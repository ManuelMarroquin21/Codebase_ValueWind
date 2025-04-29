from MarketEnvironment import MarketEnv
from Valuation import Valuation

# Define market price file and strike price
market_price_file = "C:\\Users\\Unai\\Codebase_ValueWind\\Inputs\\DayAheadPrices.csv"
strike_price = 40  # Example strike price, adjust as needed

# Define project valuation parameters
capacity_mw = 500  # Example capacity in MW
lifetime_years = 25  # Project lifetime in years
discount_rate = 0.07  # 7% discount rate
capacity_factor = 0.9  # 90% capacity factor

# Create an instance of MarketEnv with default CfD settings
market_env = MarketEnv(
    market_price_file=market_price_file,
    strike_price=strike_price,
    scheme_type="CfD",  # Can be "CfD", "FiT", or "FiP"
    premium=8,
    one_sided=True,  # One-sided CfD
    reference_period="monthly",  # "hourly", "daily", "monthly", "yearly"
    payment_frequency="yearly",  # "hourly", "daily", "monthly", "yearly"
    inflation_rate=0.02,  # Example inflation rate of 2%
    capacity_mw=capacity_mw  # Pass capacity to MarketEnv
)

# Forecast market prices from 2025–2050
market_env.forecast_market_prices(
    known_share=0.2084,
    target_share=0.4866,
    known_year=2021,
    target_year=2030,
    start_year=2025,
    end_year=2050
)

# Create an instance of Valuation
valuation = Valuation(
    market_env=market_env,
    capacity_mw=capacity_mw,
    lifetime_years=lifetime_years,
    discount_rate=discount_rate,
    capacity_factor=capacity_factor
)

# Calculate and print NPV and IRR
try:
    npv = valuation.calculate_npv()
    print(f"Net Present Value (NPV): €{npv:,.2f}")
except ValueError as e:
    print("Error calculating NPV:", e)

irr = valuation.calculate_irr()
if irr is not None:
    print(f"Internal Rate of Return (IRR): {irr:.2%}")
else:
    print("IRR calculation failed.")

# Plot revenue over the project lifetime
valuation.plot_revenue()
