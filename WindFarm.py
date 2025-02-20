import pandas as pd
from Turbine import Turbine
from Fatigue_Analysis import Fatigue_Analysis
from FarmSurrogate import FarmSurrogateQuery
from File_Handling import load_yaml, process_duration_fields
from scipy.stats import weibull_min
import numpy as np
from WF_Controller import WF_Controller

class WindFarm:
    """
    Represents a wind farm in the simulation environment. Manages turbine data, layout,
    and accesses environmental parameters from MetEnvironment.
    
    Parameters
    ----------
    env : ValueWindEnv
        The main simulation environment, providing access to MetEnvironment.
    """
    def __init__(self, env):
        self.env = env  # Access to the main simulation environment
        self.wind_farm_data = load_windfarmData(self.env.config)

        self.wf_controller = WF_Controller(self.env)

        # Initialize Wind Farm Farm Surrogate
        self.wf_surrogate_query = FarmSurrogateQuery(self.env.metEnv, self.wind_farm_data)
        
        # Load and initialize turbines through Turbine class
        self.turbines = Turbine.initialize_turbines(self.env)

        # Initialize Fatigue Analysis class for the wind farm
                # this should be optional, depending on a flag in the config file
        self.fatigue_analysis = Fatigue_Analysis(self.wind_farm_data)

        # Set start and end times from wind_farm_data for the 'WF' identifier
        self.start_time = self.env.config.WF_OperationsStart_h
        self.end_time = self.env.config.WF_OperationsEnd_h
        
        # check if this should live here or in the turbine class
        self.response_log_reference = {turbine.name: pd.DataFrame(columns=['simulation_time', 'response'])
                                       for turbine in self.turbines.values()}
        

    def start(self):
        """Starts the wind farm simulation process."""
        self.env.process(self.run_hourly())
        # self.response_log_reference = self.get_WindFarmResponse_Reference() # this needs to be fixed. Currently it is referencing the turbine level response

    def run_hourly(self):
        """
        A generator function that triggers the wind farm response calculation every hour
        within the specified operational time window.
        """
        while True:
            if self.start_time <= self.env.now <= self.end_time:
                self.get_WindFarmResponse_timestep()
                #if turbine_surrogate
                #self.get_TurbineResponse()
            yield self.env.timeout(1)

    def get_WindFarmResponse_timestep(self):
        """
        Returns the wind farm response for the current simulation step.
        """
        # get the control output for this timestep, this is a dummy implementation
        #WF_Controller.compute_turbine_setpoints()
        control_output = self.wf_controller.get_turbine_setpoints()
        response = self.wf_surrogate_query.get_windFarm_response_timestep(control_output)
        # write response to turbine level
        for i, (turbine_name, turbine) in enumerate(self.turbines.items()):
            turbine_response = {}
            turbine_response[f"{'Power'}_{'mean'}"] = response.Power.sel(wt=i) #  This only works if turbines are initialized in the same order as defined in the surrogate model, could be improved
            new_entry = pd.DataFrame({
            'simulation_time': [self.env.now],
            'response': [turbine_response],
            'fatigue_damage': [None]  # Initialize with None, to be updated later
        })
            turbine.response_log = pd.concat([turbine.response_log, new_entry], ignore_index=True)

            # write flow conditions to turbine level
            inflow_conditions = {}
            inflow_conditions[f"{'ws_ambient'}"] = response.WS_eff.sel(wt=i) # same
            inflow_conditions[f"{'ti_ambient'}"] = response.TI_eff.sel(wt=i) # same
            new_entry = pd.DataFrame({
                'simulation_time': [self.env.now],
                'flow_conditions': [inflow_conditions]
            })
            turbine.ambient_inflow = pd.concat(
                [turbine.ambient_inflow, new_entry],
                ignore_index=True
            )

    def get_turbine_response(self):
        for turbine in self.turbines.values():
            turbine.get_turbine_response()
        return None

    # this is calling pywake for all WS and Wind direction
    def get_WindFarmResponse_global(self):

        # get the control ouptut 
        control_output = self.get_ControlOutput()
        

        # get the reponse of the farm surrogate
        response = self.wf_surrogate_query.get_windFarm_response(control_output)
        return None

    # the fatique analyis is done on turbine level from here
    # turbine object is passed to the function
    def get_FatigueAnalysis(self):    
        for turbine in self.turbines.values():
            self.fatigue_analysis.get_fatigue_analysis(turbine)
        return None

         

    # this needs to be checked
    def get_WindFarmResponse_Reference(self):
        """
        Calculates and logs the wind farm reference response based on Weibull distribution fitting.

        Returns
        -------
        dict of pd.DataFrame
            The wind farm reference response logs, each entry keyed by turbine name.
        """
        TIreq = 10  # Placeholder for turbulence intensity in %
        Preq = 11   # Rated power in MW
        interp_type = 'linear'  # Example interpolation type

        if self.wind_farm_data['WF']['WF_Response_Reference']['flag_fitWB']:
            shape_param, loc, scale_param = self.env.metEnv.fit_weibull_distribution()

            wind_speed_bins = np.linspace(4, 24, 11)
            weibull_pdf = weibull_min.pdf(wind_speed_bins, shape_param, loc, scale_param)
            weibull_pdf = weibull_pdf / np.sum(weibull_pdf)

            for turbine in self.turbines.values():
                turbine.get_turbine_reference_response(
                    self.fatigue_analysis, wind_speed_bins, weibull_pdf, TIreq, Preq, interp_type
                )
        return None


def load_windfarmData(config):
    """
    Loads wind farm input parameters from the configuration file.

    Returns
    -------
    dict
        Dictionary with wind farm parameters.
    """
    wind_farm_data = {}

    if hasattr(config, 'WindFarm_inputFiles'):
        for identifier, file_name in config.WindFarm_inputFiles.items():
            wind_farm_data[identifier] = load_yaml(config.valuewind_inputFolder, file_name)
            wind_farm_data[identifier] = process_duration_fields(wind_farm_data[identifier])

    return wind_farm_data