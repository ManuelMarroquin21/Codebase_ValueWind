import pandas as pd 
from scipy.stats import weibull_min
import numpy as np

class Fatigue_Analysis:
    """
    Handles fatigue analysis and damage calculation, including Weibull distribution fitting
    and weighted sums of damage using surrogate model responses.
    """

    def __init__(self, wind_farm_data):
        """
        Initialize the Fatigue Analysis class.

        Parameters
        ----------
        wind_farm_data : dict
            Wind farm input data containing parameters and settings.
        """
        self.wind_farm_data = wind_farm_data
 
    def get_fatigue_damage(self, turbine):
        """
        Analyzes fatigue for each sensor with fatigue analysis enabled and logs damage
        for the most recent entry in response_log.

        Parameters
        ----------
        turbine : object
            Turbine instance containing response_log to store damage calculations.
        """
        response_sensors = self.wind_farm_data['WF'].get('WF_ResponseSensors', {})

        # Only calculate for the most recent entry
        if not turbine.response_log.empty:
            latest_index = turbine.response_log.index[-1]
            latest_response = turbine.response_log.at[latest_index, 'response']

            for sensor_name in turbine.sensor_names:
                sensor_data = response_sensors.get(sensor_name)
                if sensor_data and sensor_data.get('flag_fatigueAnalysis', False):
                    # Calculate sensor damage for the latest timestep
                    sensor_damage = self.calculate_damage(latest_response, sensor_name)
                    # Log the calculated damage in the most recent entry
                    turbine.response_log.at[latest_index, 'fatigue_damage'] = sensor_damage
                    break  # Stop once we find and calculate for the first valid sensor

    def calculate_damage(self, response, sensor):
        """
        Calculate fatigue damage for a given sensor's response at the current timestep.

        Parameters
        ----------
        response : dict
            Dictionary of responses at the current timestep.
        sensor : str
            Sensor name to calculate fatigue damage for.

        Returns
        -------
        dict
            Calculated damage for the specified sensor, split into mean and standard deviation components.
        """
        m_W = self.wind_farm_data['WF']['WF_ResponseSensors'][sensor].get('m_W')
        sensor_mean = f"{sensor}_mean"
        sensor_std = f"{sensor}_std"

        if sensor_mean in response and sensor_std in response:
            response_mean = response[sensor_mean]
            response_std = response[sensor_std]

            # Calculate damage for mean and std components individually
            damage_mean = (response_mean ** m_W) * 3600 if isinstance(response_mean, (int, float)) else 0
            damage_std = (response_std ** m_W) * 3600 if isinstance(response_std, (int, float)) else 0

            return {
                'damage_mean': damage_mean,
                'damage_std': damage_std
            }
        else:
            return {'damage_mean': None, 'damage_std': None}  # Default to zero if values are not present

    def calculate_weighted_response(self, wind_speed_bins, weibull_pdf, TIreq, Preq, interp_type, surrogate_query): 
        """
        Calculate the weighted response using the Weibull PDF and the surrogate model.

        Parameters
        ----------
        wind_speed_bins : array-like
            Wind speed bins for which the Weibull PDF is calculated.
        weibull_pdf : array-like
            The Weibull PDF values corresponding to the wind speed bins.
        TIreq : float
            Turbulence intensity requirement.
        Preq : float
            Power requirement.
        interp_type : str
            Type of interpolation to be used in the surrogate model query.
        surrogate_query : TurbineSurrogateQuery instance
            The surrogate model query instance used to retrieve response data.

        Returns
        -------
        total_weighted_response : dict
            Dictionary containing the weighted responses for different keys (e.g., Power, etc.).
        """
        total_weighted_response = {}

        for idx, wind_speed in enumerate(wind_speed_bins):
            wind_farm_response = surrogate_query.get_points_from_surrogate_spline(
                wind_speed, TIreq, Preq, interp_type, self.wind_farm_data
            )

            if isinstance(wind_farm_response, dict):
                for key, value in wind_farm_response.items():
                    if key not in total_weighted_response:
                        total_weighted_response[key] = 0

                    if 'Power' in key:
                        total_weighted_response[key] += weibull_pdf[idx] * value
                    else:
                        total_weighted_response[key] += weibull_pdf[idx] * (value ** self.m_W) * 3600

        return total_weighted_response
