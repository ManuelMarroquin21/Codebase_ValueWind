import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import numpy_financial as npf  # Add this import at the top of the file

class Valuation:
    def __init__(self, market_env, capacity_mw, lifetime_years, discount_rate, capacity_factor=0.5):
        """
        Initialize the Valuation class.

        :param market_env: MarketEnv object containing market data and cashflows.
        :param capacity_mw: Installed capacity of the project in MW.
        :param lifetime_years: Lifetime of the project in years.
        :param discount_rate: Discount rate for NPV calculation.
        :param capacity_factor: Capacity factor of the project (default is 1.0, i.e., 100%).
        """
        self.market_env = market_env
        self.capacity_mw = capacity_mw
        self.lifetime_years = lifetime_years
        self.discount_rate = discount_rate
        self.capacity_factor = capacity_factor  # Capacity factor as a fraction (e.g., 0.9 for 90%)

        # Example CAPEX and OPEX for offshore wind in Denmark
        self.capex = 3_000_000 * capacity_mw  # €3M per MW installed
        self.opex_annual = 50_000 * capacity_mw  # €50K per MW annually

    def calculate_revenue(self):
        """
        Calculate the revenue based on market cashflows and project capacity.

        :return: DataFrame containing the revenue over time.
        """
        # Get cashflows from the market environment
        cashflow = self.market_env.aggregate_payments().fillna(0)

        # Debugging: Print the structure of the cashflow object
        print("Cashflow structure:")
        print(cashflow.head())

        # If cashflow is a Series, use it directly
        if isinstance(cashflow, pd.Series):
            revenue = cashflow * self.capacity_mw * self.capacity_factor
        # If cashflow is a DataFrame, use the appropriate column
        elif isinstance(cashflow, pd.DataFrame):
            if 'Cashflow' in cashflow.columns:
                revenue = cashflow['Cashflow'] * self.capacity_mw * self.capacity_factor
            else:
                raise KeyError("The 'Cashflow' column is missing in the aggregate_payments output.")
        else:
            raise TypeError("Unexpected type for cashflow. Expected Series or DataFrame.")

        return revenue.to_frame(name="Revenue")

    def calculate_npv(self):
        """
        Calculate the Net Present Value (NPV) of the project.

        :return: NPV value as a float.
        """
        revenue = self.calculate_revenue().resample('YE').sum()

        # Ensure enough years of data
        if len(revenue) < self.lifetime_years:
            raise ValueError(f"Revenue data has {len(revenue)} years, but lifetime is {self.lifetime_years} years")

        npv = -self.capex
        for year in range(min(self.lifetime_years, len(revenue))):
            annual_revenue = revenue.iloc[year]["Revenue"]
            npv += (annual_revenue - self.opex_annual) / (1 + self.discount_rate) ** (year + 1)

        return npv

    def calculate_irr(self):
        """
        Calculate the Internal Rate of Return (IRR) of the project.

        :return: IRR value as a float or None if calculation fails.
        """
        revenue = self.calculate_revenue().resample('YE').sum()
        cashflows = [-self.capex] + [
            (revenue.iloc[year]["Revenue"] - self.opex_annual) for year in range(len(revenue))
        ]

        try:
            irr = npf.irr(cashflows)
            if np.isnan(irr):
                raise ValueError("IRR calculation failed due to invalid cashflows.")
        except Exception as e:
            print("Error: IRR could not be calculated.", e)
            irr = None  # Return None if IRR calculation fails

        return irr

    def plot_revenue(self):
        """
        Plot the revenue over time.

        :return: None
        """
        revenue = self.calculate_revenue()
        plt.figure(figsize=(12, 6))
        plt.plot(revenue, label="Revenue (€)")
        plt.xlabel("Date")
        plt.ylabel("Revenue (€)")
        plt.title("Project Revenue Over Time")
        plt.legend()
        plt.grid()
        plt.show()
