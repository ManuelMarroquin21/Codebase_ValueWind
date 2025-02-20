from File_Handling import load_yaml, process_duration_fields

class MarketEnv:

    def __init__(self,env):
        self.env = env
        self.marketInput = load_marketInput(self.env.config)


    # all functions defining the market behaviour functions should be defined here
    def get_market_condition(self):
        

        return None



def load_marketInput(config):
    """
    Loads wind farm input parameters from the configuration file.

    Returns
    -------
    dict
        Dictionary with wind farm parameters.
    """
    marketInput = {}

    if hasattr(config, 'Market_inputFiles'):
        for identifier, file_name in config.Market_inputFiles.items():
            marketInput[identifier] = load_yaml(config.valuewind_inputFolder, file_name)
            marketInput[identifier] = process_duration_fields(marketInput[identifier])

    return marketInput
