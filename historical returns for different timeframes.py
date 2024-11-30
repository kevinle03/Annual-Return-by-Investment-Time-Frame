import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import numpy_financial as npf
from collections import defaultdict

# Define the ticker symbol
ticker_symbol = "^GSPC"  # S&P 500 Index

# Get historical data
start_date = "1928-01-01"
end_date = "2024-01-01"
monthly_contribution = 1000

# Download daily data
daily_data = yf.download(ticker_symbol, start=start_date, end=end_date, interval="1d")

# Check if data was downloaded
if daily_data.empty:
    raise ValueError("No data downloaded. Please check the ticker symbol and date range.")

# Resample to monthly data using month-end frequency
monthly_historical_data = daily_data.resample('ME').last()

# Ensure the data is sorted by date
monthly_historical_data.sort_index(inplace=True)

# Check if 'Adj Close' is available; if not, fallback to 'Close'
price_column = 'Adj Close' if 'Adj Close' in monthly_historical_data.columns else 'Close'

# Initialize a dictionary to store results
results = defaultdict(lambda: {
    "positive_irr_count": 0,
    "total_periods": 0,
    "best_start_year": None,
    "best_irr": float('-inf'),
    "min_irr": float('inf'),
    "max_irr": float('-inf'),
    "sum_irr": 0.0
})

# Define the range for time_frame_years
min_years = 1
max_years = 40

for time_frame_years in range(min_years, max_years + 1):
    print(f"\nAnalyzing Time Frame: {time_frame_years} Year(s)")
    
    # Initialize a dictionary to track IRRs for each start_year
    irr_dict = {}
    
    # Calculate the last possible start_year to ensure data availability
    last_start_year = 2024 - time_frame_years
    
    for start_year in range(1928, last_start_year + 1):
        # Define the start and end dates for the period
        period_start = f"{start_year}-01-31"
        period_end = f"{start_year + time_frame_years - 1}-12-31"

        # Select the data for the period
        historical_data = monthly_historical_data.loc[period_start : period_end]

        # Check if we have enough data
        expected_length = time_frame_years * 12
        if len(historical_data) < expected_length:
            print(f"  Not enough data for period {start_year} to {start_year + time_frame_years - 1}")
            continue

        # Drop any rows with missing data
        historical_data = historical_data.dropna()

        # Investing scenario
        shares = 0.0  # Initialize as float
        total_contributions = 0.0
        portfolio_value = []

        # Loop through each row in the historical data
        for index, row in historical_data.iterrows():
            # Use Adjusted Close price to buy shares
            buy_price = row[price_column]

            # Ensure buy_price is a scalar
            if isinstance(buy_price, pd.Series):
                buy_price = buy_price.item()
            elif pd.isna(buy_price):
                print(f"    NaN price encountered on {index}. Skipping this month.")
                # Append current portfolio value without adding new shares
                current_portfolio_value = shares * row[price_column]
                # Ensure current_portfolio_value is scalar
                if isinstance(current_portfolio_value, pd.Series):
                    current_portfolio_value = current_portfolio_value.item()
                portfolio_value.append(float(current_portfolio_value))
                continue

            # Convert buy_price to float
            try:
                buy_price = float(buy_price)
            except ValueError:
                print(f"    Non-numeric price encountered on {index}. Skipping this month.")
                # Append current portfolio value without adding new shares
                current_portfolio_value = shares * row[price_column]
                if isinstance(current_portfolio_value, pd.Series):
                    current_portfolio_value = current_portfolio_value.item()
                portfolio_value.append(float(current_portfolio_value))
                continue

            if buy_price == 0:
                print(f"    Zero price encountered on {index}. Skipping this month.")
                # Append current portfolio value without adding new shares
                current_portfolio_value = shares * row[price_column]
                if isinstance(current_portfolio_value, pd.Series):
                    current_portfolio_value = current_portfolio_value.item()
                portfolio_value.append(float(current_portfolio_value))
                continue

            # Calculate the number of shares to buy this month
            shares_to_buy = monthly_contribution / buy_price
            shares += shares_to_buy
            total_contributions += monthly_contribution

            # Calculate current portfolio value
            current_price = row[price_column]
            if isinstance(current_price, pd.Series):
                current_price = current_price.item()
            elif pd.isna(current_price):
                print(f"    NaN current price encountered on {index}. Using last known price.")
                # Use last known price if current price is NaN
                current_price = portfolio_value[-1] / shares if portfolio_value else 0.0

            current_portfolio_value = shares * current_price
            portfolio_value.append(float(current_portfolio_value))

        # Create cash flows
        # Each month's contribution is a cash outflow (-monthly_contribution)
        # The final portfolio value is a cash inflow (+portfolio_value[-1])
        cash_flows = [-monthly_contribution] * len(historical_data)

        # Ensure portfolio_value has at least one value
        if portfolio_value:
            # Add the final portfolio value to the last cash flow
            cash_flows[-1] += portfolio_value[-1]
        else:
            print(f"    No portfolio value calculated for period {start_year} to {start_year + time_frame_years - 1}")
            continue

        # Verify that all elements in cash_flows are numeric
        try:
            # Convert cash_flows to float
            cash_flows = [float(cf) for cf in cash_flows]
        except (ValueError, TypeError) as e:
            print(f"    Non-numeric cash flow encountered for period {start_year} to {start_year + time_frame_years - 1}: {e}")
            continue

        # Calculate IRR using numpy_financial
        try:
            irr = npf.irr(cash_flows)
        except Exception as e:
            print(f"    IRR calculation failed for period {start_year} to {start_year + time_frame_years - 1}: {e}")
            continue

        # Handle cases where IRR calculation fails
        if irr is not None and not pd.isna(irr):
            # Annualize IRR (since cash flows are monthly)
            annualized_return = (1 + irr) ** 12 - 1
            irr_dict[start_year] = annualized_return
            # Track positive IRR counts
            if annualized_return > 0:
                results[time_frame_years]["positive_irr_count"] += 1
            results[time_frame_years]["total_periods"] += 1

            # Update min, max, and sum IRRs
            if annualized_return < results[time_frame_years]["min_irr"]:
                results[time_frame_years]["min_irr"] = annualized_return
            if annualized_return > results[time_frame_years]["max_irr"]:
                results[time_frame_years]["max_irr"] = annualized_return
            results[time_frame_years]["sum_irr"] += annualized_return

            # Track the best start year for this time_frame_years
            if annualized_return > results[time_frame_years]["best_irr"]:
                results[time_frame_years]["best_irr"] = annualized_return
                results[time_frame_years]["best_start_year"] = start_year

            print(
                f"    Period {start_year} to {start_year + time_frame_years - 1}: IRR = {annualized_return * 100:.2f}%"
            )
        else:
            print(f"    IRR calculation returned NaN for period {start_year} to {start_year + time_frame_years - 1}")

    # After iterating through all start_years for the current time_frame_years
    positive_count = results[time_frame_years]["positive_irr_count"]
    total = results[time_frame_years]["total_periods"]
    best_year = results[time_frame_years]["best_start_year"]
    best_irr = results[time_frame_years]["best_irr"]
    min_irr = results[time_frame_years]["min_irr"]
    max_irr = results[time_frame_years]["max_irr"]
    sum_irr = results[time_frame_years]["sum_irr"]

    if total > 0:
        success_rate = (positive_count / total) * 100
        average_irr = sum_irr / total
        print(f"  Success Rate: {positive_count}/{total} periods ({success_rate:.2f}%)")
        print(f"  Lowest IRR: {min_irr * 100:.2f}%")
        print(f"  Highest IRR: {max_irr * 100:.2f}%")
        print(f"  Average IRR: {average_irr * 100:.2f}%")
        if best_year is not None:
            print(f"  Best Start Year: {best_year} with IRR = {best_irr * 100:.2f}%")
    else:
        print("  No valid periods analyzed for this time frame.")

# Optional: Summarize the results
print("\nSummary of IRR Statistics for Each Time Frame:")
summary_data = []
for tf_years in range(min_years, max_years + 1):
    best_year = results[tf_years]["best_start_year"]
    best_irr = results[tf_years]["best_irr"]
    min_irr = results[tf_years]["min_irr"]
    max_irr = results[tf_years]["max_irr"]
    sum_irr = results[tf_years]["sum_irr"]
    total = results[tf_years]["total_periods"]
    if total > 0:
        average_irr = sum_irr / total
        summary_data.append({
            "Time Frame (Years)": tf_years,
            "Best Start Year": best_year,
            "Best IRR (%)": best_irr * 100,
            "Lowest IRR (%)": min_irr * 100,
            "Highest IRR (%)": max_irr * 100,
            "Average IRR (%)": average_irr * 100
        })
    else:
        summary_data.append({
            "Time Frame (Years)": tf_years,
            "Best Start Year": None,
            "Best IRR (%)": None,
            "Lowest IRR (%)": None,
            "Highest IRR (%)": None,
            "Average IRR (%)": None
        })

summary_df = pd.DataFrame(summary_data)
print(summary_df)

# Optional: Plot the summary
plt.figure(figsize=(14, 8))
plt.plot(summary_df["Time Frame (Years)"], summary_df["Best IRR (%)"], marker='o', label='Best IRR')
plt.plot(summary_df["Time Frame (Years)"], summary_df["Lowest IRR (%)"], marker='x', label='Lowest IRR')
plt.plot(summary_df["Time Frame (Years)"], summary_df["Highest IRR (%)"], marker='^', label='Highest IRR')
plt.plot(summary_df["Time Frame (Years)"], summary_df["Average IRR (%)"], marker='s', label='Average IRR')
plt.title("IRR Statistics by Investment Time Frame")
plt.xlabel("Investment Time Frame (Years)")
plt.ylabel("IRR (%)")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()
