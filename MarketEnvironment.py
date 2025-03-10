import pandas as pd
import matplotlib.pyplot as plt

class MarketEnv:
    def __init__(self, market_price_file, strike_price, scheme_type="CfD", premium=0, one_sided=True, reference_period="hourly", payment_frequency="hourly"):
        # Initialize the Market Environment with given parameters
        self.market_price_file = market_price_file
        self.strike_price = strike_price
        self.scheme_type = scheme_type  # "CfD", "FiT", "FiP"
        self.premium = premium  # Only for FiP
        self.one_sided = one_sided  # Only for CfD
        self.reference_period = reference_period  # "hourly", "daily", "monthly", "yearly"
        self.payment_frequency = payment_frequency  # "hourly", "daily", "monthly", "yearly"
        self.market_prices = self.load_market_prices()
    
    def load_market_prices(self):
        # Loads the market prices from the CSV file, selecting only the relevant column (DK1 bidding zone).
        # Assumes that relevant data starts at row 5 (index 4 in Python, since it's zero-based).
        df = pd.read_csv(self.market_price_file, skiprows=4)  # Skip first 4 rows
        df = df.iloc[:87672, 5]  # Select DK1 column and correct row range
        df.index = pd.date_range(start="2015-01-01 00:00", periods=len(df), freq='H')
        df.name = "Market Price"
        return df
    
    def get_reference_price(self):
        # Calculates the reference price based on the selected reference period.
        if self.reference_period == "daily":
            return self.market_prices.resample('D').mean().reindex(self.market_prices.index, method='ffill')
        elif self.reference_period == "monthly":
            return self.market_prices.resample('M').mean().reindex(self.market_prices.index, method='ffill')
        elif self.reference_period == "yearly":
            return self.market_prices.resample('Y').mean().reindex(self.market_prices.index, method='ffill')
        else:  # Default to hourly
            return self.market_prices
    
    def calculate_cashflow(self):
        # Calculates cashflow based on the selected scheme type and configuration.
        reference_price = self.get_reference_price()
        
        if self.scheme_type == "FiT":
            return self.strike_price  # Fixed revenue per MWh
        elif self.scheme_type == "FiP":
            return reference_price + self.premium  # Market price + premium
        elif self.scheme_type == "CfD":
            cashflow =  reference_price - self.strike_price
            if self.one_sided:
                cashflow = cashflow.clip(lower=0)  # Operator keeps extra revenue if market price > strike
            return cashflow
        else:
            raise ValueError("Invalid scheme type")
    
    def aggregate_payments(self):
        # Aggregates cashflows based on the selected payment frequency.
        cashflow = self.calculate_cashflow()
        
        if self.payment_frequency == "daily":
            return cashflow.resample('D').sum()
        elif self.payment_frequency == "monthly":
            return cashflow.resample('M').sum()
        elif self.payment_frequency == "yearly":
            return cashflow.resample('Y').sum()
        else:  # Default to hourly
            return cashflow
    
    def plot_cashflow(self):
        # Plots the strike price and highlights CfD cashflows without showing the market price line.
        cashflow = self.aggregate_payments()
        
        plt.figure(figsize=(12, 6))
        plt.axhline(y=self.strike_price, color='red', linestyle='--', label='Strike Price')
        
        # Highlight positive (operator pays government) and negative (government pays operator) cashflows
        plt.fill_between(cashflow.index, self.strike_price, cashflow + self.strike_price, 
                         where=(cashflow < 0), color='green', alpha=0.5, label='Gov. Payment to Operator')
        plt.fill_between(cashflow.index, self.strike_price, cashflow + self.strike_price, 
                         where=(cashflow > 0), color='orange', alpha=0.5, label='Operator Payment to Gov.')
        
        plt.xlabel('Time')
        plt.ylabel('Price')
        plt.title(f'{self.scheme_type} Cashflows')
        plt.legend()
        plt.grid()
        plt.show()


