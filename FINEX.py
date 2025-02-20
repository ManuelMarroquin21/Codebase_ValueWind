import pandas as pd
import numpy as np
from File_Handling import load_yaml, process_duration_fields

class FINEX:
    def __init__(self, env, capex):
        self.env = env  # Access to the environment for scheduling
        self.capex = capex  # Access to CAPEX instance for cost data
        self.finex_data = load_finex_data(self.env.config)
        self.discount_rate = self.get_interest_rate()
        self.cost_records = []

    def get_interest_rate(self):
        """Extracts and returns the interest rate as a decimal from the finex_data."""
        for identifier, data in self.finex_data.items():
            for item in data.get("FINEX", []):
                if item.get("name") == "Debt":
                    interest_rate = item["Parameters"].get("interest_rate", 0)
                    # Convert interest rate from percentage to decimal format
                    return interest_rate / 100
        print("Warning: 'Debt' interest rate not found in any FINEX data file; using default of 0%")
        return 0

    def discount_cost(self):
        """Calculates discounted cost for each record in the CAPEX cost breakdown and returns a DataFrame."""
        # Retrieve the cost breakdown DataFrame from CAPEX
        cost_df = self.capex.get_cost_dataframe()

        # Ensure 'timing' is numeric for discount calculation
        cost_df['timing'] = pd.to_numeric(cost_df['timing'], errors='coerce')

        # Calculate the discounted cost for each record based on the timing field
        cost_df['discounted_cost'] = cost_df.apply(
            lambda row: row['cost'] / ((1 + self.discount_rate) ** row['timing']) if pd.notnull(row['timing']) else row['cost'],
            axis=1
        )
        self.cost_records = cost_df

    def get_cost_dataframe(self):
        """Converts the cost records list to a DataFrame for further analysis."""
        return self.cost_records


def load_finex_data(config):
    """
    Loads FINEX input parameters from configuration files, 
    converting any duration parameters to hours.

    Parameters
    ----------
    config : Configuration
        The configuration object containing paths to FINEX input files.

    Returns
    -------
    dict
        Dictionary containing FINEX data, with duration parameters converted to hours where applicable.
    """
    finex_data = {}

    # Load FINEX input files
    if hasattr(config, 'Finex_inputFiles'):
        for identifier, file_name in config.Finex_inputFiles.items():
            finex_data[identifier] = load_yaml(config.valuewind_inputFolder, file_name)
            finex_data[identifier] = process_duration_fields(finex_data[identifier])  # Process for duration fields
        print("Loaded Finex data structure:", finex_data)

    return finex_data

