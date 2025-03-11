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
        df.index = pd.date_range(start="2015-01-01 00:00", periods=len(df), freq='h')
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
            cashflow = reference_price - self.strike_price
            
            if self.one_sided:
                # One-sided CfD:
                # If the market price is higher than the strike price, the operator keeps the market price (no state payment).
                # If the market price is lower than the strike price, the state pays the operator (cashflow is positive).
                cashflow = cashflow.clip(lower=0)  # Only the state pays when market < strike, otherwise operator keeps market price.
            else:
                # Two-sided CfD:
                # If the market price is higher than the strike price, the operator pays the state (cashflow is negative).
                # If the market price is lower than the strike price, the state pays the operator (cashflow is positive).
                cashflow = cashflow  # Cashflow is negative when market > strike (operator pays state), positive when market < strike (state pays operator).
            
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
        # Aggregates cashflows based on the selected payment frequency.
        cashflow = self.aggregate_payments()

        plt.figure(figsize=(12, 6))

        if self.scheme_type == "FiT":
            # For FiT, the cashflow is simply the strike price
            plt.axhline(y=self.strike_price, color='red', linestyle='--', label=f'Strike Price (FiT) - {self.strike_price} EUR/MWh')
            plt.fill_between(cashflow.index, 0, self.strike_price, color='orange', alpha=0.5, label=f'Fixed Payment (FiT) - {self.strike_price} EUR/MWh')
        
        elif self.scheme_type == "FiP":
            # For FiP, the cashflow is market price + premium
            cashflow = self.calculate_cashflow()
            plt.plot(cashflow.index, cashflow, label=f"FiP Cashflow (Market Price + {self.premium} EUR Premium)", color='purple')
            plt.axhline(y=0, color='black', linestyle='--', label='Zero Line (FiP)')
        
        elif self.scheme_type == "CfD":
            # For CfD, we have a dynamic cashflow based on the difference to the strike price
            plt.axhline(y=self.strike_price, color='red', linestyle='--', label=f'Strike Price (CfD) - {self.strike_price} EUR/MWh')
            
            # Highlight positive and negative cashflows (operator or government payments)
            plt.fill_between(cashflow.index, self.strike_price, cashflow + self.strike_price, 
                            where=(cashflow < 0), color='green', alpha=0.5, label='Gov. Payment to Operator (EUR/MWh)')
            plt.fill_between(cashflow.index, self.strike_price, cashflow + self.strike_price, 
                            where=(cashflow > 0), color='orange', alpha=0.5, label='Operator Payment to Gov. (EUR/MWh)')
        
        else:
            raise ValueError("Invalid scheme type")
        
        plt.xlabel('Time')
        plt.ylabel('Price (EUR/MWh)')
        plt.title(f'{self.scheme_type} Cashflows (EUR/MWh)')
        plt.legend()
        plt.grid()
        plt.show()
