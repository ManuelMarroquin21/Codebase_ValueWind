import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import numpy_financial as npf  # Import numpy_financial for IRR calculation
from MarketEnvironment import MarketEnv

class Valuation:
    def __init__(self, market_env, capacity_mw, lifetime_years, discount_rate):
        self.market_env = market_env  # Instance of MarketEnv
        self.capacity_mw = capacity_mw  # Installed capacity in MW
        self.lifetime_years = lifetime_years  # Project lifetime in years
        self.discount_rate = discount_rate  # Discount rate for NPV calculations

        # Example cost values for offshore wind in Denmark (adjust as needed)
        self.capex = 3000000 * capacity_mw  # 3M EUR per MW (example CAPEX cost)
        self.opex_annual = 70000 * capacity_mw  # 70k EUR per MW per year (example OPEX cost)
    
    def calculate_revenue(self):
        cashflow = self.market_env.aggregate_payments()
        revenue = cashflow * self.capacity_mw  # Scale revenue by capacity
        return revenue
    
    def calculate_npv(self):
        revenue = self.calculate_revenue().resample('YE').sum()  # Update 'Y' -> 'YE'
        
        npv = -self.capex  # Initial investment
        
        for year in range(1, self.lifetime_years + 1):
            if year - 1 < len(revenue):  # Ensure index is within bounds
                yearly_revenue = revenue.iloc[year - 1] - self.opex_annual
                npv += yearly_revenue / ((1 + self.discount_rate) ** year)
        
        return npv
    
    def calculate_irr(self):
        revenue = self.calculate_revenue().resample('YE').sum()  # Update 'Y' -> 'YE'
        
        # Check if the revenue is valid and not empty
        if revenue.isnull().all() or revenue.empty:
            print("Error: Revenue data is empty or contains only NaNs.")
            return np.nan  # Return NaN if revenue is not valid
        
        cashflows = [-self.capex]
        for year in range(1, self.lifetime_years + 1):
            if year - 1 < len(revenue):  # Ensure index is within bounds
                yearly_revenue = revenue.iloc[year - 1] - self.opex_annual
                cashflows.append(yearly_revenue)
        
        # Check if cashflows contains any NaN values
        if any(np.isnan(cashflows)):
            print("Error: Cashflows contain NaN values.")
            return np.nan  # Return NaN if there are NaN values in cashflows
        
        # Calculate IRR
        irr = npf.irr(cashflows)
        
        if np.isnan(irr):
            print("Error: IRR could not be calculated.")
        return irr
    
    def plot_revenue(self):
        revenue = self.calculate_revenue().resample('YE').sum()  # Update 'Y' -> 'YE'
        
        plt.figure(figsize=(10, 5))
        plt.bar(revenue.index.year, revenue, color='blue', alpha=0.7, label='Annual Revenue')
        plt.axhline(y=self.opex_annual, color='red', linestyle='--', label='Annual OPEX')
        plt.xlabel('Year')
        plt.ylabel('Revenue (EUR)')
        plt.title('Annual Revenue from Support Scheme')
        plt.legend()
        plt.grid()
        plt.show()
