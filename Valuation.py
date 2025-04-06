import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class Valuation:
    def __init__(self, market_env, capacity_mw, lifetime_years, discount_rate):
        self.market_env = market_env
        self.capacity_mw = capacity_mw
        self.lifetime_years = lifetime_years
        self.discount_rate = discount_rate

        # Example CAPEX and OPEX for offshore wind in Denmark
        self.capex = 3_000_000 * capacity_mw  # €3M per MW installed
        self.opex_annual = 50_000 * capacity_mw  # €50K per MW annually

    def calculate_revenue(self):
        cashflow = self.market_env.aggregate_payments().fillna(0)  # Fix NaN issue
        revenue = cashflow["Cashflow"] * self.capacity_mw
        return revenue.to_frame()

    def calculate_npv(self):
        revenue = self.calculate_revenue().resample('YE').sum()

        # Ensure enough years of data
        if len(revenue) < self.lifetime_years:
            raise ValueError(f"Revenue data has {len(revenue)} years, but lifetime is {self.lifetime_years} years")

        npv = -self.capex
        for year in range(min(self.lifetime_years, len(revenue))):
            if year - 1 < len(revenue):
                npv += (revenue.iloc[year - 1] - self.opex_annual) / (1 + self.discount_rate) ** year


        return npv

    def calculate_irr(self):
        revenue = self.calculate_revenue().resample('YE').sum()
        cashflows = [-self.capex] + [(revenue.iloc[year]["Cashflow"] - self.opex_annual) for year in range(len(revenue))]

        try:
            irr = np.irr(cashflows)
            if np.isnan(irr):
                raise ValueError("IRR calculation failed due to invalid cashflows.")
        except Exception as e:
            print("Error: IRR could not be calculated.", e)
            irr = None  # Return None if IRR calculation fails

        return irr

    def plot_revenue(self):
        revenue = self.calculate_revenue()
        plt.figure(figsize=(12, 6))
        plt.plot(revenue, label="Revenue (€)")
        plt.xlabel("Date")
        plt.ylabel("Revenue (€)")
        plt.title("Project Revenue Over Time")
        plt.legend()
        plt.grid()
        plt.show()
