import pandas as pd
import random
import numpy as np
from File_Handling import load_yaml, process_duration_fields

class CAPEX:
    def __init__(self, env):
        self.env = env  # Access to the environment
        self.capex_data, self.material_data = load_capex_data(self.env.config)
        self.events = self.extract_event_schedule()
        # Initialize a list to store cost records for creating a DataFrame
        self.cost_records = []

    def extract_event_schedule(self):
        events = []
        for file_key, capex_file_data in self.capex_data.items():
            if 'cost_categories' in capex_file_data:
                for category in capex_file_data['cost_categories']:
                    for subcategory in category['subcategories']:
                        project_time = subcategory.get('project_time_h')
                        if project_time is not None:
                            events.append((project_time, f"{subcategory['name']}_event"))
            else:
                print(f"Warning: 'cost_categories' key not found in '{file_key}' of the CAPEX data files.")
        return events

    def start(self):
        self.total_cost = 0  # Reset total cost for each simulation run
        for timing, event_name in self.events:
            self.env.process(self.schedule_event(timing, event_name))

    def schedule_event(self, timing, event_name):
        yield self.env.timeout(timing)
        # Execute the capital cost calculation when the event is triggered
        self.calculate_capital_cost(event_name, timing)

    def calculate_capital_cost(self, event_name, timing):
        event_cost = 0

        for file_key, capex_file_data in self.capex_data.items():
            if 'cost_categories' not in capex_file_data:
                print(f"Warning: 'cost_categories' key not found in '{file_key}' of the CAPEX data files.")
                continue

            for category in capex_file_data['cost_categories']:
                category_name = category['name']

                for subcategory in category['subcategories']:
                    subcategory_name = subcategory['name']

                    if f"{subcategory['name']}_event" == event_name:
                        for item in subcategory['subsubcategories']:
                            item_cost = item.get('fixed_cost', 0)
                            subsubcategory_name = item.get('name')
                            subsubcategory_total = item_cost

                            if item.get('flag_material_cost', False):
                                materials = item.get('material', [])
                                if isinstance(materials, dict):  # Single material
                                    materials = [materials]

                                for material in materials:
                                    material_cost = self.calculate_material_cost(material, subcategory)
                                    material_cost_total = (
                                        material.get('mass', 0) * material_cost * material.get('CF', 1)
                                    )
                                    subsubcategory_total += material_cost_total

                            # Append a record for the current subsubcategory, including timing
                            self.cost_records.append({
                                "event_name": event_name,
                                "category_name": category_name,
                                "subcategory_name": subcategory_name,
                                "subsubcategory_name": subsubcategory_name,
                                "cost": subsubcategory_total,
                                "timing": timing  # Store timing for DCF calculation
                            })
                            event_cost += subsubcategory_total

        self.total_cost += event_cost
        print(f"Total capital cost for {event_name}: {event_cost}")

    def calculate_material_cost(self, material, subcategory):
        material_name = material.get('name')
        material_cost = 0
        if material_name:
            for material_file_data in self.material_data.values():
                material_info = next(
                    (m for m in material_file_data.get('Commodity', []) if m['name'] == material_name),
                    None
                )
                if material_info:
                    parameters = material_info['Parameters']
                    material_cost = parameters['material_cost']
                    flag_gbm = parameters['flag_GBM']
                    mu = parameters.get('mu', 0)
                    sigma = parameters.get('sigma', 0)
                    flag_jump_diff = parameters['flag_JumpDif']
                    lambda_jump = parameters.get('lambda_jump', 0)
                    sigma_jump = parameters.get('sigma_jump', 0)

                    timing = subcategory.get('project_time_h', 1)/8760  # Convert to years
                    if flag_gbm:
                        material_cost = geometric_brownian_motion(material_cost, mu, sigma, timing)
                    elif flag_jump_diff:
                        material_cost = jump_diffusion(
                            material_cost, mu, sigma, timing, lambda_jump, sigma_jump
                        )
                    break
        return material_cost

    def get_cost_dataframe(self):
        """Converts the cost records list to a DataFrame for further analysis."""
        return pd.DataFrame(self.cost_records)




def load_capex_data(config):
    """
    Loads CAPEX and Material input parameters from configuration files, 
    converting any nested duration parameters to hours.

    Parameters
    ----------
    config : Configuration
        The configuration object containing paths to CAPEX and Material input files.

    Returns
    -------
    tuple
        Two dictionaries containing CAPEX data and Material data, respectively.
    """
    capex_data = {}
    material_data = {}

    # Load CAPEX input files
    if hasattr(config, 'Capex_inputFiles'):
        for identifier, file_name in config.Capex_inputFiles.items():
            capex_data[identifier] = load_yaml(config.valuewind_inputFolder, file_name)
            capex_data[identifier] = process_duration_fields(capex_data[identifier])  # Process for duration fields

        print("Loaded CAPEX data structure:", capex_data)

    # Load Material input files
    if hasattr(config, 'Material_inputFiles'):
        for identifier, file_name in config.Material_inputFiles.items():
            material_data[identifier] = load_yaml(config.valuewind_inputFolder, file_name)
            material_data[identifier] = process_duration_fields(material_data[identifier])  # Process for duration fields

        print("Loaded Material data structure:", material_data)

    return capex_data, material_data


def geometric_brownian_motion(S0, mu, sigma, T):
    """Calculate a random realization of Geometric Brownian Motion."""
    W = np.random.normal(0, np.sqrt(T))  # Brownian motion component
    return S0 * np.exp((mu - 0.5 * sigma**2) * T + sigma * W)

def jump_diffusion(S0, mu, sigma, T, lambda_jump, sigma_jump):
    """Calculate a random realization of Jump Diffusion process."""
    # Basic GBM component
    S_t = geometric_brownian_motion(S0, mu, sigma, T)
    # Number of jumps in the time interval
    num_jumps = np.random.poisson(lambda_jump * T)
    # Apply jump diffusion adjustments
    for _ in range(num_jumps):
        jump_size = np.random.normal(0, sigma_jump)
        S_t *= np.exp(jump_size)
    return S_t