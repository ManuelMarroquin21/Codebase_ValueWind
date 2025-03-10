import pandas as pd
import matplotlib.pyplot as plt
from File_Handling import load_yaml, process_duration_fields

class MarketEnv:
    def __init__(self, env):
        self.env = env
        self.marketInput = self.load_market_input(self.env.config)
        self.market_prices = self.load_market_prices()

    def load_market_input(self, config):
        """
        Loads market-related input parameters from the configuration file.
        """
        market_input = {}
        if hasattr(config, 'Market_inputFiles'):
            for identifier, file_name in config.Market_inputFiles.items():
                market_input[identifier] = load_yaml(config.valuewind_inputFolder, file_name)
                market_input[identifier] = process_duration_fields(market_input[identifier])
        return market_input

    def load_market_prices(self):
    
    #Loads historical market price data from the specified Market.yaml file.
        market_prices = {}
        if 'market_prices' in self.marketInput:
            for key, file_name in self.marketInput['market_prices'].items():
                file_path = f"{self.marketInput['MA_inputFolder']}/{file_name}"
                market_prices[key] = pd.read_csv(file_path, index_col=0, parse_dates=True)
        return market_prices

    def calculate_revenue(self, scheme_type, strike_price, wind_generation, **kwargs):
        """
        Calculates revenue for the wind farm based on the chosen support scheme.
        """
        market_price = self.market_prices.get(kwargs.get('market_price_type', 'day_ahead'))
        if market_price is None:
            raise ValueError("Market price data not available")
        
        if scheme_type == 'FIT':
            return self.calculate_fit(strike_price, wind_generation, **kwargs)
        elif scheme_type == 'FIP':
            return self.calculate_fip(strike_price, wind_generation, market_price, **kwargs)
        elif scheme_type == 'CfD':
            return self.calculate_cfd(strike_price, wind_generation, market_price, **kwargs)
        else:
            raise ValueError("Invalid scheme type")

    def calculate_fit(self, fixed_price, wind_generation, **kwargs):
        return wind_generation * fixed_price

    def calculate_fip(self, premium, wind_generation, market_price, **kwargs):
        sliding_premium = kwargs.get('sliding_premium', False)
        cap = kwargs.get('cap', None)
        floor = kwargs.get('floor', None)
        
        if sliding_premium:
            revenue = wind_generation * (premium + (market_price - premium).clip(lower=0))
        else:
            revenue = wind_generation * (market_price + premium)
        
        if cap:
            revenue = revenue.clip(upper=cap)
        if floor:
            revenue = revenue.clip(lower=floor)
        
        return revenue

    def calculate_cfd(self, strike_price, wind_generation, market_price, **kwargs):
        two_sided = kwargs.get('two_sided', True)
        cap = kwargs.get('cap', None)
        floor = kwargs.get('floor', None)
        
        difference = strike_price - market_price
        
        if two_sided:
            revenue = wind_generation * difference
        else:
            revenue = wind_generation * difference.clip(lower=0)
        
        if cap:
            revenue = revenue.clip(upper=cap)
        if floor:
            revenue = revenue.clip(lower=floor)
        
        return revenue

    def plot_revenues(self, scheme_type, strike_price, wind_generation, **kwargs):
        market_price = self.market_prices.get(kwargs.get('market_price_type', 'day_ahead'))
        revenue = self.calculate_revenue(scheme_type, strike_price, wind_generation, **kwargs)
        
        plt.figure(figsize=(12, 6))
        plt.plot(market_price.index, market_price, label='Market Price', linestyle='dashed')
        plt.plot(market_price.index, revenue, label=f'{scheme_type} Revenue')
        
        if scheme_type in ['FIT', 'CfD']:
            plt.axhline(y=strike_price, color='r', linestyle='--', label='Strike Price')
        
        plt.xlabel('Time')
        plt.ylabel('Price / Revenue')
        plt.title(f'{scheme_type} Revenue vs Market Price')
        plt.legend()
        plt.grid()
        plt.show()
