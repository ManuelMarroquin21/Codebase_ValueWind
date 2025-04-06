import pandas as pd
import matplotlib.pyplot as plt

class MarketEnv:
    def __init__(self, market_price_file, strike_price, scheme_type="CfD", premium=0, one_sided=True, reference_period="hourly", payment_frequency="hourly"):
        # Initialize the Market Environment with given parameters
        self.market_price_file = market_price_file
        self.strike_price = strike_price
        self.scheme_type = scheme_type  # "CfD", "FiT", "FiP", "Market"
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
        df.index = pd.date_range(start="2015-01-01 00:00", periods=len(df), freq='h')
        df.name = "Market Price"
        return df
    
    def get_reference_price(self):
        # Calculates the reference price based on the selected reference period.
        if self.reference_period == "daily":
            return self.market_prices.resample('d').mean().reindex(self.market_prices.index, method='ffill')
        elif self.reference_period == "monthly":
            return self.market_prices.resample('ME').mean().reindex(self.market_prices.index, method='ffill')
        elif self.reference_period == "yearly":
            return self.market_prices.resample('y').mean().reindex(self.market_prices.index, method='ffill')
        else:  # Default to hourly
            return self.market_prices
    
    def calculate_cashflow(self):
        # Calculates cashflow based on the selected scheme type and configuration.
        reference_price = self.get_reference_price()
        
        if self.scheme_type == "FiT":
            return pd.Series(self.strike_price, index=self.market_prices.index)  # Fixed revenue per MWh as a time series
        elif self.scheme_type == "FiP":
            return reference_price + self.premium  # Market price + premium
        elif self.scheme_type == "CfD":
            if self.one_sided:
                # One-sided CfD: Operator receives market price if it's above the strike price, otherwise receives the strike price.
                return self.strike_price - reference_price.clip(upper=self.strike_price)
            else:
                # Two-sided CfD: Operator receives strike price, paying or receiving the difference.
                return self.strike_price - reference_price
        elif self.scheme_type == "Market":
            return reference_price  # Operator simply receives the market price
        else:
            raise ValueError("Invalid scheme type")
    
    def aggregate_payments(self):
        # Aggregates cashflows based on the selected payment frequency.
        cashflow = self.calculate_cashflow()
        
        if self.payment_frequency == "daily":
            return cashflow.resample('d').sum()
        elif self.payment_frequency == "monthly":
            return cashflow.resample('ME').sum()
        elif self.payment_frequency == "yearly":
            return cashflow.resample('y').sum()
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
        plt.ylabel(f'Cashflow ({"EUR/MWh" if self.payment_frequency == "hourly" else "EUR"})')
        plt.title(f'{self.scheme_type} Cashflows')
        plt.legend()
        plt.grid()
        plt.show()

# Example usage:
# market_env = MarketEnv("C:\\Users\\Unai\\Codebase_ValueWind\\Inputs\\DayAheadPrices.csv", strike_price=50, scheme_type="CfD", one_sided=False, reference_period="monthly", payment_frequency="yearly")
# market_env.plot_cashflow()
