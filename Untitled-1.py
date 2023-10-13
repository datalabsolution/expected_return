import datetime
import math
import pandas as pd
import streamlit as st
import yfinance as yf
from polygon import RESTClient
import matplotlib.pyplot as plt
import matplotlib.dates as mdates



# Function to check if a date is the third Friday of the month
def is_third_friday(date):
    return date.weekday() == 4 and 15 <= date.day <= 21

# Initialize
today = datetime.date.today()
client = RESTClient("AI73Oy1KnUYUfHAKsOJLxSmVz9dWFC95")
option_num = 20

# Streamlit UI
st.title('Expected Move')
stock_code = st.sidebar.text_input("Enter the stock code:", value="AAPL")
option_num = st.sidebar.slider("Select the number of expiry dates:", 1, 30, 10)
ticker = yf.Ticker(stock_code)
option_dates = ticker.options

# Use the closest 10 expiry dates
closest_ten_dates = option_dates[:option_num]
current_price = round(yf.download(stock_code, period='1d')['Adj Close'].values[-1], 2)

table_data = []

# Loop through each option date
for option_date in closest_ten_dates:
    option_date_bw = datetime.datetime.strptime(option_date, '%Y-%m-%d').date()
    days_between = (option_date_bw - today).days + 1

    # Check if the date is the third Friday of the month
    is_third_fri = is_third_friday(option_date_bw)

    # Get option chain
    opt = ticker.option_chain(option_date)
    closest_strike_index = (abs(opt.calls["strike"] - current_price)).idxmin()
    closest_strike = opt.calls["strike"].iloc[closest_strike_index]

    try:
        option_call = opt.calls.query(f'strike == {closest_strike}')['contractSymbol'].values[0]
        option_put = opt.puts.query(f'strike == {closest_strike}')['contractSymbol'].values[0]
        IV_call = client.get_snapshot_option(underlying_asset=stock_code.upper(), option_contract=f"O:{option_call}")
        IV_put = client.get_snapshot_option(underlying_asset=stock_code.upper(), option_contract=f"O:{option_put}")
        mean_iv = (IV_call.implied_volatility + IV_put.implied_volatility) / 2

        # Append data to table_data list
        expected_move = current_price * mean_iv * math.sqrt(days_between / 365)
        expected_return_lower = current_price - expected_move
        expected_return_upper = current_price + expected_move
        display_date = option_date + "m" if is_third_fri else option_date
        table_data.append([
            display_date, days_between, closest_strike, mean_iv,
            round(expected_return_upper, 2), current_price,
            round(expected_return_lower, 2), round(expected_move, 2)
        ])
    except Exception as e:
        st.write(f"{option_date} no IV data")
        continue

# Create DataFrame and display table
df_columns = ['Expiry Date', 'Days', 'Strike', 'Mean_IV', 'Upper', 'Current', 'Lower', 'Expected Move']
df = pd.DataFrame(table_data, columns=df_columns)
df = round(df, 3)
st.table(df)

plt.figure(figsize=(12, 6))
plt.plot(df['Expiry Date'], df['Upper'], label='Upper', marker='o')
plt.plot(df['Expiry Date'], df['Lower'], label='Lower', marker='x')
plt.axhline(y=current_price, color='r', linestyle='-', label=f'Current Price: {current_price}')
plt.xlabel('Expiry Date')
plt.ylabel('Price')
plt.title('Upper and Lower Price Ranges by Expiry Date')
plt.legend()
plt.grid(True)

# Rotate x-axis labels and adjust font size
plt.xticks(rotation=45, fontsize=10)

# Display the plot in Streamlit
st.pyplot(plt)
