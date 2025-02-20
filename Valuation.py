from File_Handling import load_yaml, process_duration_fields

class Valuation: 

    def __init__(self,env):
        self.env = env
        self.valuationInput = load_valuationInput(self.env.config)


    # all valuation functions should be defined here
    def valuation(self):
        

        return None






def load_valuationInput(config):
    """
    Loads wind farm input parameters from the configuration file.

    Returns
    -------
    dict
        Dictionary with wind farm parameters.
    """
    valuationInput = {}

    if hasattr(config, 'Valuation_inputFiles'):
        for identifier, file_name in config.Valuation_inputFiles.items():
            valuationInput[identifier] = load_yaml(config.valuewind_inputFolder, file_name)
            valuationInput[identifier] = process_duration_fields(valuationInput[identifier])

    return valuationInput
