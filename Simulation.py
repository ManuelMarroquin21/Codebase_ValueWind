from pathlib import Path
from attrs import define, field
from typing import Union
import pandas as pd
import matplotlib.pyplot as plt

from File_Handling import load_yaml, process_duration_fields
from File_Handling import calculate_duration_in_hours
from Data_classes import FromDictMixin
from ValueWindEnv import ValueWindEnv
from WindFarm import WindFarm

@define(auto_attribs=True)
class Simulation:
    """The primary API to interact with the simulation methodologies."""

    library_path: Path
    config: 'Configuration'  # Keep 'Configuration' as a string for forward reference
    env: ValueWindEnv = field(init=False)
    results_collector: 'ResultsCollector' = field(init=False)  # Results collector instance
    all_results_df: pd.DataFrame = field(init=False)

    def __attrs_post_init__(self) -> None:
        """Post-initialization hook to finalize setup."""
        self._setup_simulation()
        # Initialize ResultsCollector with env, which already contains windFarm
        self.results_collector = ResultsCollector(env=self.env)

    @classmethod
    def from_config(cls, library_path: Union[str, Path], config: Union[str, Path, dict, 'Configuration']):
        """Creates a ``Simulation`` object from a configuration file or dictionary."""
        library_path = Path(library_path)
        if isinstance(config, (str, Path)):
            config_path = library_path / config
            config = load_yaml(config_path.parent, config_path.name)
            config = process_duration_fields(config)

        if isinstance(config, dict):
            config = Configuration.from_dict(config)
        if not isinstance(config, Configuration):
            raise TypeError("``config`` must be a dictionary or ``Configuration`` object!")
        return cls(library_path=library_path, config=config)

    def _setup_simulation(self):
        """Initializes the simulation objects based on the config."""
        self.env = ValueWindEnv(self.config)

    def run(self, until: Union[int, float, None] = None):
        """Run the simulation."""
        self.env.run_simulation(until=until)
        # Collect results after simulation
        self.results_collector.collect_capex_results()
        self.results_collector.collect_finex_results()

    def run_monte_carlo(self, num_runs: int, until: Union[int, float, None] = None):
        """Run multiple Monte Carlo realizations of the simulation."""
        all_results = []
        
        for i in range(num_runs):
            print(f"Running simulation {i+1} / {num_runs}")
            self.run(until=until)  # Run a single simulation
            run_results = self.results_collector.capex_df  # Collect CAPEX results
            all_results.append(run_results.to_dict())  # Collect CAPEX results as dict
            
            # Optionally reset the environment if required for the next run
            # self._setup_simulation()
        
        self.all_results_df = pd.DataFrame(all_results)  # Store all results in a DataFrame for analysis
        print("Monte Carlo simulation completed.")


@define(auto_attribs=True)
class ResultsCollector:
    """Class to collect and analyze results from CAPEX, FINEX, and MetEnvironment (wind data)."""
    
    env: 'ValueWindEnv'  # Environment containing CAPEX, FINEX, and MetEnvironment instances
    capex_df: pd.DataFrame = field(init=False)  # DataFrame for CAPEX results
    finex_df: pd.DataFrame = field(init=False)  # DataFrame for FINEX discounted results
    wind_speed_series: pd.Series = field(init=False)  # Series for wind speed time series

    def __attrs_post_init__(self):
        # Initialize the CAPEX and FINEX data frames and wind data series after instantiation
        self.collect_capex_results()
        self.collect_finex_results()
        self.collect_wind_data()

    def collect_capex_results(self):
        """Collects CAPEX cost data into a DataFrame."""
        self.capex_df = self.env.capex.get_cost_dataframe()
        print("CAPEX results collected.")

    def collect_finex_results(self):
        """Collects FINEX discounted costs into a DataFrame."""
        self.finex_df = self.env.finex.get_cost_dataframe()
        print("FINEX discounted results collected.")

    def collect_wind_data(self):
        """Collects wind speed data from MetEnvironment into a time series."""
        self.wind_speed_series = self.env.metEnv.wind_speed_series
        if not self.wind_speed_series.empty:
            print("Wind speed data collected.")
        else:
            print("Wind speed data is not available.")

    def plot_total_costs(self):
        """Plots total costs from CAPEX and FINEX."""
        if self.capex_df is not None and self.finex_df is not None:
            total_cost = self.capex_df['cost'].sum()
            total_discounted_cost = self.finex_df['discounted_cost'].sum()

            plt.figure(figsize=(8, 5))
            plt.bar(['Total Cost', 'Total Discounted Cost'], [total_cost, total_discounted_cost])
            plt.title('Total Costs: CAPEX vs Discounted FINEX')
            plt.ylabel('Cost')
            plt.show()
        else:
            print("CAPEX or FINEX data not available for plotting.")

    def plot_wind_time_series(self):
        """Plots the wind speed time series."""
        if not self.wind_speed_series.empty:
            plt.figure(figsize=(10, 6))
            self.wind_speed_series.plot()
            plt.title("Wind Speed Time Series")
            plt.xlabel("Time")
            plt.ylabel("Wind Speed (m/s)")
            plt.show()
        else:
            print("Wind speed data is not available for plotting.")

    def plot_windFarm_response(self):
        """Plots the wind farm response time series from the individual Turbines in the WindFarm instance."""
        for turbine in self.env.windFarm.turbines.values():
            if not turbine.response_log.empty:
                #convert to dataframe
                response_df = pd.json_normalize(turbine.response_log['response'])
                plot_df = pd.concat([turbine.response_log['simulation_time'], response_df], axis=1)

                plt.figure(figsize=(12, 6))
                for col in plot_df.columns[1:]:
                    plt.plot(plot_df['simulation_time'], plot_df[col], label=col)
                plt.title(f"{turbine.name} Response Time Series")
                plt.xlabel("Time")
                plt.ylabel("Response")
                plt.legend()
                plt.show()
            else:
                print(f"No response data available for turbine {turbine.name}.")

    def plot_WF_layout(self):
        """Creates a plot of the wind farm layout, displaying the positions of all turbines."""
        # Access turbine data from the WindFarm instance in the environment
        turbines = self.env.windFarm.turbines

        # Extract latitude and longitude from each Turbine instance
        latitudes = [turbine.latitude for turbine in turbines.values()]
        longitudes = [turbine.longitude for turbine in turbines.values()]
        turbine_names = [turbine.name for turbine in turbines.values()]

        # Plot the layout
        plt.figure(figsize=(10, 8))
        plt.scatter(longitudes, latitudes, marker='o', color='blue', label='Turbine')
        
        # Annotate each turbine point with its name
        for name, x, y in zip(turbine_names, longitudes, latitudes):
            plt.text(x, y, name, fontsize=9, ha='right')

        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.title("Wind Farm Layout")
        plt.legend()
        plt.grid(True)
        plt.show()


@define(auto_attribs=True)
class Configuration(FromDictMixin):
    """Configuration for the Simulation."""

    name: str
    valuewind_inputFolder: str
    Finex_inputFiles: str
    Capex_inputFiles: dict[str, str]
    MetEnv_inputFiles: dict[str, str]
    Material_inputFiles: dict[str, str]
    WindFarm_inputFiles: dict[str, str]
    WindTurbine_inputFiles: dict[str, str]
    Valuation_inputFiles: dict[str, str]
    Market_inputFiles: dict[str, str]
    Project_Duration: dict[str, Union[int, str]]
    Project_StartDate: str
    WF_OperationsStart: dict[str, Union[int, str]]
    WF_OperationsEnd_h: int 
    WF_OperationsEnd: dict[str, Union[int, str]]
    WF_OperationsStart_h: int 
    TimeStep: int
    Project_Duration_h: int 

    #def __attrs_post_init__(self):
    #    """Calculate and set the project duration in hours after initialization."""
    #    self.Project_Duration_h = calculate_duration_in_hours(
    #        self.Project_Duration.get("value"),
    #        self.Project_Duration.get("unit")
    #    )