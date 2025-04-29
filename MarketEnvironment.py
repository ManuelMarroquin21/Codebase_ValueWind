import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

class MarketEnv:
    def __init__(self, market_price_file, strike_price, scheme_type, premium, one_sided, reference_period, payment_frequency, inflation_rate, capacity_mw):
        self.market_price_file = market_price_file
        self.strike_price = strike_price
        self.scheme_type = scheme_type
        self.premium = premium
        self.one_sided = one_sided
        self.reference_period = reference_period
        self.payment_frequency = payment_frequency
        self.inflation_rate = inflation_rate
        self.capacity_mw = capacity_mw  # Store capacity as an attribute
        self.market_prices = self.load_market_prices()

    def load_market_prices(self):
        # Load the CSV data for reference
        df = pd.read_csv(self.market_price_file, skiprows=4)
        df = df.iloc[:, 5]  # Assuming this is the correct column for market prices

        # Store the raw market data for reference
        self.raw_market_data = pd.Series(
            data=df.values,
            index=pd.date_range(start="2015-01-01 00:00", periods=len(df), freq='h'),
            name="Raw Market Price"
        )

        # Generate the working period index (2025–2050)
        start_date = pd.Timestamp("2025-01-01 00:00")
        end_date = pd.Timestamp("2050-12-31 23:00")
        working_index = pd.date_range(start=start_date, end=end_date, freq='h')

        # Initialize market_prices with NaN for the working period
        market_prices = pd.Series(index=working_index, data=None, name="Market Price")

        return market_prices

    def forecast_market_prices(self, known_share, target_share, known_year=2021, target_year=2030, start_year=2025, end_year=2050):
        # Calculate the market value adjustment factor (MVF) series
        mvf_series = self.calculate_market_value_adjustment(known_share, target_share, known_year, target_year, end_year)

        # Filter the raw market data for Q4 2024 to calculate the base price
        q4_2024 = self.raw_market_data["2024-10-01":"2024-12-31"]
        if q4_2024.empty:
            raise ValueError("Market prices for Q4 2024 are missing. Ensure the input data includes this period.")
        base_price = q4_2024.mean()

        # Generate hourly dates for the forecast period
        forecast_dates = pd.date_range(start=f"{start_year}-01-01", end=f"{end_year}-12-31 23:00", freq='h')

        # Align MVF series with the forecast dates
        mvf_series = mvf_series.reindex(forecast_dates, method='ffill')

        # Calculate forecasted prices for the forecast period
        years_since_2024 = (forecast_dates - pd.Timestamp("2024-01-01")).days / 365.25
        inflated_prices = base_price * ((1 + self.inflation_rate) ** years_since_2024)
        adjusted_prices = inflated_prices * mvf_series.values

        # Assign the forecasted prices to the market_prices attribute
        self.market_prices = pd.Series(adjusted_prices, index=forecast_dates, name="Forecasted Price")

        print("Forecasted Prices:")
        print(self.market_prices.head())
        print(self.market_prices.tail())

    def get_reference_price(self):
        if self.reference_period == "daily":
            return self.market_prices.resample('d').mean().reindex(self.market_prices.index, method='ffill')
        elif self.reference_period == "monthly":
            return self.market_prices.resample('ME').mean().reindex(self.market_prices.index, method='ffill')
        elif self.reference_period == "yearly":
            return self.market_prices.resample('YE').mean().reindex(self.market_prices.index, method='ffill')
        else:
            return self.market_prices

    def calculate_cashflow(self):
        reference_price = self.get_reference_price()
        reference_price = reference_price["2025-01-01":"2050-12-31"]
        index = reference_price.index

        if self.scheme_type == "FiT":
            return pd.Series(self.strike_price, index=index)
        elif self.scheme_type == "FiP":
            return reference_price + self.premium
        elif self.scheme_type == "CfD":
            if self.one_sided:
                return self.strike_price - reference_price.clip(upper=self.strike_price)
            else:
                return self.strike_price - reference_price
        elif self.scheme_type == "Market":
            return reference_price
        else:
            raise ValueError("Invalid scheme type")

    def aggregate_payments(self):
        """
        Calculate the cashflows based on the forecasted prices and CfD scheme.

        :return: A pandas Series containing the cashflows over time.
        """
        # Ensure forecasted prices are available
        if self.market_prices is None:
            raise ValueError("Market prices have not been forecasted. Please call forecast_market_prices first.")

        # Calculate the difference between the strike price and forecasted prices
        cashflow = self.strike_price - self.market_prices

        # Apply one-sided CfD logic if applicable
        if self.one_sided:
            cashflow = cashflow.clip(lower=0)  # Payments only when the strike price is higher

        # Multiply by capacity to get total cashflows
        cashflow *= self.capacity_mw

        print("Calculated Cashflows:")
        print(cashflow.head())
        print(cashflow.tail())

        return cashflow

    def calculate_market_value_adjustment(self, known_share, target_share, known_year=2021, target_year=2030, end_year=2050):
        mvf_known = max(-0.3 * known_share + 1, 0.7)
        mvf_target = max(-0.3 * target_share + 1, 0.7)

        years = list(range(known_year, end_year + 1))
        mvf_values = []

        for year in years:
            if year <= known_year:
                mvf = mvf_known
            elif year >= target_year:
                slope = (mvf_target - mvf_known) / (target_year - known_year)
                mvf = mvf_known + slope * (year - known_year)
                mvf = max(mvf, 0.7)
            else:
                slope = (mvf_target - mvf_known) / (target_year - known_year)
                mvf = mvf_known + slope * (year - known_year)
            mvf_values.append(mvf)

        return pd.Series(mvf_values, index=pd.date_range(f"{known_year}-01-01", f"{end_year}-12-31", freq="YE"))

    def plot_cashflow(self):
        cashflow = self.aggregate_payments()
        cashflow = cashflow["2025":"2050"]

        print("Aggregate Payments:")
        print(cashflow.head())
        print(cashflow.tail())

        plt.figure(figsize=(12, 6))
        plt.bar(cashflow.index.year, cashflow.values, color='skyblue', label='Cashflow')
        plt.axhline(y=0, color='black', linewidth=1)
        plt.xlabel('Year')
        plt.ylabel(f'Cashflow ({"EUR/MWh" if self.payment_frequency == "hourly" else "EUR"})')
        plt.title(f'{self.scheme_type} Cashflows (2025-2050)')
        plt.grid(axis='y')
        plt.xticks(ticks=range(2025, 2051))
        plt.legend()
        plt.tight_layout()
        plt.show()
