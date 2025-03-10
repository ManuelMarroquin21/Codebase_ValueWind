from MarketEnvironment import MarketEnv

# Define the path to the market price file and the strike price
market_price_file = "C:\\Users\\Unai\\Codebase_ValueWind\\Inputs\\DayAheadPrices.csv"
strike_price = 13.8  # Example strike price, adjust as needed

# Create an instance of MarketEnv with default CfD settings
market_env = MarketEnv(
    market_price_file=market_price_file,
    strike_price=strike_price,
    scheme_type="FiP",  # Default scheme is CfD
    premium=5,
    one_sided=False,  # Two-sided CfD
    reference_period="daily",  # Default hourly comparison
    payment_frequency="monthly"  # Default hourly payments
)

# Plot the CfD cashflow
market_env.plot_cashflow()