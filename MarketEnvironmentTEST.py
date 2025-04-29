from MarketEnvironment import MarketEnv

# Define path to the market price file and strike price
market_price_file = "C:\\Users\\Unai\\Codebase_ValueWind\\Inputs\\DayAheadPrices.csv"
strike_price = 80  # Adjust as needed

# Create MarketEnv instance with two-sided CfD settings
market_env = MarketEnv(
    market_price_file=market_price_file,
    strike_price=strike_price,
    scheme_type="CfD",
    premium=8,
    one_sided=False,
    reference_period="monthly",     # Options: "hourly", "daily", "monthly", "yearly"
    payment_frequency="monthly",     # Options: "hourly", "daily", "monthly", "yearly"
    inflation_rate=0.01,
    capacity_mw=500  # Example capacity in MW
)

# Forecast market prices from 2025–2050 using MVF adjustment
market_env.forecast_market_prices(
    known_share=0.2084,
    target_share=0.4866,
    known_year=2021,
    target_year=2030,
    start_year=2025,
    end_year=2050
)

# Plot forecasted cashflows
market_env.plot_cashflow()

# Print forecasted market prices (optional)
print("Forecasted Market Prices (2025–2050):")
print(market_env.market_prices.head())
print(market_env.market_prices.tail())
