import pandas as pd
from TurbineSurrogate import TurbineSurrogateQuery
from Fatigue_Analysis import Fatigue_Analysis
from File_Handling import load_yaml, process_duration_fields

class Turbine:
    """
    Represents a wind turbine with its essential information.
    
    Parameters
    ----------
    name : str
        The name or identifier of the turbine.
    latitude : float
        The latitude position of the turbine.
    longitude : float
        The longitude position of the turbine.
    env : ValueWindEnv
        The simulation environment instance providing access to configuration and current simulation time.
    """
    def __init__(self, name, latitude, longitude, env, wind_farm_data):
        """
        Initialize a Turbine instance with essential properties and setup.
        
        Parameters
        ----------
        name : str
            Name of the turbine.
        latitude : float
            Latitude of the turbine.
        longitude : float
            Longitude of the turbine.
        env : ValueWindEnv
            The simulation environment.
        wind_farm_data : dict
            The wind farm data including response sensors.
        """
        self.name = name
        self.latitude = latitude
        self.longitude = longitude
        self.env = env
        self.surrogate_query = TurbineSurrogateQuery(wind_farm_data)

        wf_data = wind_farm_data.get('WF', {})
        response_sensors = wf_data.get('WF_ResponseSensors', [])
        self.sensor_names = []
        for sensor in response_sensors:
            if isinstance(sensor, str):
                self.sensor_names.append(sensor)
            elif isinstance(sensor, dict):
                self.sensor_names.extend(sensor.keys())

        self.response_log = pd.DataFrame(columns=['simulation_time', 'response', 'fatigue_damage'])
        self.response_log_reference = pd.DataFrame(columns=['simulation_time', 'reference_response'])
        # Initialize turbine flow log
        self.ambient_inflow = pd.DataFrame(columns=['simulation_time', 'flow_conditions'])
                              

    @classmethod
    def initialize_turbines(cls, env):
        """
        Initializes the turbines in the wind farm based on the turbine data.
        
        Parameters
        ----------
        env : ValueWindEnv
            The simulation environment instance that provides access to configurations.
        wind_farm_data : dict
            Wind farm data containing configuration details.
        
        Returns
        -------
        dict
            A dictionary where the keys are turbine names and the values are Turbine objects.
        """
        wind_turbine_data = load_windturbineData(env.config)
        turbine_data = cls.load_turbine_data(wind_turbine_data)
        turbines = {}
        for _, row in turbine_data.iterrows():
            name = row['Turbine']
            latitude = row['Latitude']
            longitude = row['Longitude']
            turbines[name] = cls(name, latitude, longitude, env, wind_turbine_data)
        return turbines

    @staticmethod
    def load_turbine_data(wind_turbine_data):
        """
        Loads wind turbine data from a CSV file specified in the configuration.

        Parameters
        ----------
        wind_turbine_data : dict
            Wind farm data containing configuration details.

        Returns
        -------
        pd.DataFrame
            DataFrame containing the wind turbine data.
        """
        folder = wind_turbine_data['WT']['WT_inputFolder']
        filename = wind_turbine_data['WT']['WT_inputFiles']['Layout']
        filepath = f"{folder}/{filename}"
        turbine_data = pd.read_csv(filepath, delimiter=';')
        return turbine_data

    def get_turbine_response(self, Preq, interp_type):
        """
        Returns and logs the turbine response using the surrogate model.

        Parameters
        ----------
        Vreq : float
            Wind speed request.
        TIreq : float
            Turbulence intensity request.
        Preq : float
            Power request.
        interp_type : str
            Interpolation type for the response.
        
        Returns
        -------
        dict
            Response from the surrogate model for the turbine.
        """
#############
        Preq = control_output['Preq']
        interp_type = 'linear'

        # Fetch turbine response from all turbines in the farm
        turbine_responses = {}
        for turbine in self.turbines.values():
            # Extract flow conditions for the current simulation time
            flow_conditions = self.windFarm_flow[turbine.name]
            current_flow = flow_conditions[flow_conditions['simulation_time'] == self.env.now]
            
            # Check if Vreq and TIreq are available for the current timestamp
            if not current_flow.empty:
                Vreq = current_flow.iloc[0]['flow_conditions'].get('Vreq')
                TIreq = current_flow.iloc[0]['flow_conditions'].get('TIreq')
                
                # Verify that both Vreq and TIreq are not None
                if Vreq is None or TIreq is None:
                    raise ValueError(f"Missing Vreq or TIreq data for turbine '{turbine.name}' at timestamp {self.env.now}")
            else:
                # Raise an error if data is completely missing for the current time
                raise ValueError(f"Missing flow data for turbine '{turbine.name}' at timestamp {self.env.now}")

            # Calculate the response for the turbine based on Vreq, TIreq, Preq, and interp_type
            turbine.get_turbine_response(Vreq, TIreq, Preq, interp_type)

            # call damage calculation from here?
            turbine.get_fatigue_damage()


        ########
        response = self.surrogate_query.get_points_from_surrogate_spline(
            Vreq, TIreq, Preq, self.sensor_names, interp_type
        )
        new_entry = pd.DataFrame({
            'simulation_time': [self.env.now],
            'response': [response],
            'fatigue_damage': [None]  # Initialize with None, to be updated later
        })
        self.response_log = pd.concat([self.response_log, new_entry], ignore_index=True)
        return response

    def get_fatigue_damage(self, fatigue_analysis):
        """
        Calculates and logs fatigue damage for the turbine.

        Parameters
        ----------
        fatigue_analysis : Fatigue_Analysis
            Fatigue analysis tool to calculate fatigue damage.
        """
        fatigue_damage = fatigue_analysis.get_fatigue_damage(self)
        
        # Update the 'fatigue_damage' for the most recent response entry
        if not self.response_log.empty:
            self.response_log.loc[self.response_log.index[-1], 'fatigue_damage'] = fatigue_damage

    def get_turbine_reference_response(self, fatigue_analysis, wind_speed_bins, weibull_pdf, TIreq, Preq, interp_type):
        """
        Logs the reference response for the turbine based on the Weibull distribution.

        Parameters
        ----------
        fatigue_analysis : Fatigue_Analysis
            Fatigue analysis tool for calculating the weighted response.
        wind_speed_bins : array-like
            Wind speed bins for the Weibull distribution.
        weibull_pdf : array-like
            Weibull PDF values corresponding to the wind speed bins.
        TIreq : float
            Turbulence intensity request.
        Preq : float
            Power request.
        interp_type : str
            Interpolation type for the response.
        """
        total_weighted_response = fatigue_analysis.calculate_weighted_response(
            wind_speed_bins, weibull_pdf, TIreq, Preq, interp_type, self.surrogate_query
        )
        new_reference_entry = pd.DataFrame({
            'simulation_time': [self.env.now],
            'reference_response': [total_weighted_response]
        })
        self.response_log_reference = pd.concat([self.response_log_reference, new_reference_entry], ignore_index=True)



def load_windturbineData(config):
    """
    Loads wind farm input parameters from the configuration file.

    Returns
    -------
    dict
        Dictionary with wind farm parameters.
    """
    wind_turbine_data = {}

    if hasattr(config, 'WindFarm_inputFiles'):
        for identifier, file_name in config.WindTurbine_inputFiles.items():
            wind_turbine_data[identifier] = load_yaml(config.valuewind_inputFolder, file_name)
            wind_turbine_data[identifier] = process_duration_fields(wind_turbine_data[identifier])

    return wind_turbine_data