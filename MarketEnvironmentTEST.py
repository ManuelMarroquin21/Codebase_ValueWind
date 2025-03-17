from MarketEnvironment import MarketEnv

# Define the path to the market price file and the strike price
market_price_file = "C:\\Users\\Unai\\Codebase_ValueWind\\Inputs\\DayAheadPrices.csv"
strike_price = 25  # Example strike price, adjust as needed

# Create an instance of MarketEnv with default CfD settings
market_env = MarketEnv(
    market_price_file=market_price_file,
    strike_price=strike_price,
    scheme_type="CfD",  # Default scheme is CfD
    premium=8,
    one_sided=False,  # Two-sided CfD
    reference_period="monthly",  # "hourly", "daily", "monthly", "yearly"
    payment_frequency="monthly"  # "hourly", "daily", "monthly", "yearly"
)

# Plot the CfD cashflow
market_env.plot_cashflow()