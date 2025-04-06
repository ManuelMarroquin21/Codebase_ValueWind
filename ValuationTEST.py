from MarketEnvironment import MarketEnv
from ProjectValuation import Valuation

# Define market price file and strike price
market_price_file = "C:\\Users\\Unai\\Codebase_ValueWind\\Inputs\\DayAheadPrices.csv"
strike_price = 40  # Example strike price, adjust as needed

# Create an instance of MarketEnv with default CfD settings
market_env = MarketEnv(
    market_price_file=market_price_file,
    strike_price=strike_price,
    scheme_type="CfD",  # Can be "CfD", "FiT", or "FiP"
    premium=8,
    one_sided=True,  # One-sided CfD
    reference_period="monthly",  # "hourly", "daily", "monthly", "yearly"
    payment_frequency="yearly"  # "hourly", "daily", "monthly", "yearly"
)

# Define project valuation parameters
capacity_mw = 500  # Example capacity in MW
lifetime_years = 25  # Project lifetime in years
discount_rate = 0.07  # 7% discount rate

# Create an instance of Valuation
valuation = Valuation(market_env, capacity_mw, lifetime_years, discount_rate)

# Calculate and print NPV and IRR
try:
    npv = valuation.calculate_npv()
    print("NPV:", npv)
except ValueError as e:
    print("Error calculating NPV:", e)

irr = valuation.calculate_irr()
if irr is not None:
    print("IRR:", irr)
else:
    print("IRR calculation failed.")

# Plot revenue over the project lifetime
valuation.plot_revenue()
