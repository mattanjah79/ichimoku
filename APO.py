import pandas as pd
from pandas_datareader import data
import yfinance as yf
import matplotlib.pyplot as plt
import plotly.graph_objs as go
import statistics as stats
import math as math

# Fetch daily data for 4 years
symbol = "^N225"
start_date = '2022-01-01'
end_date = '2022-11-18'

df = yf.download(symbol, start_date, end_date)

SMA_NUM_PERIODS = 40

# VAR and CONS for EMA Calculation
NUM_PERIODS_FAST = 10 # Static time period parameter for the fast EMA
K_FAST = 2 / (NUM_PERIODS_FAST + 1) # Static smoothing factor parameter for fast EMA
ema_fast = 0
ema_fast_values = [] # Hold fast EMA values for visualisation purposes

NUM_PERIODS_SLOW = 40 # Static time period parameter for slow EMA
K_SLOW = 2 / (NUM_PERIODS_SLOW + 1) # Static smoothing factor parameter for slow EMA
ema_slow = 0
ema_slow_values = [] # Hold slow EMA values for visualisation purposes

apo_values = [] # track computed absolute price oscillator value signals

orders = [] # Container for tracking buy/sell order, +1 for buy order, -1 for sell order, 0 for no-action
positions = [] # Container for tracking positions, positive for long positions, negative for short positions, 0 for flat/no position
pnls = [] # Container for tracking total_pnls, this is the sum of closed_pnl i.e. pnls already locked in and open_pnl i.e. pnls for open-position marked to market price

last_buy_price = 0 # Price at which last buy trade was made, used to prevent over-trading at/around the same price
last_sell_price = 0 # Price at which last sell trade was made, used to prevent over-trading at/around the same price
position = 0  # Current position of the trading strategy
buy_sum_price_qty = 0  # Summation of products of buy_trade_price and buy_trade_qty for every buy Trade made since last time being flat
buy_sum_qty = 0 # Summation of buy_trade_qty for every buy Trade made since last time being flat
sell_sum_price_qty = 0 # Summation of products of sell_trade_price and sell_trade_qty for every sell Trade made since last time being flat
sell_sum_qty = 0 # Summation of sell_trade_qty for every sell Trade made since last time being flat
open_pnl = 0 # Open/Unrealized PnL marked to market
close_pnl = 0 # Closed/Realized PnL so far

# Constants that define strategy behavior/thresholds
APO_VALUE_FOR_BUY_ENTRY = -10
APO_VALUE_FOR_SELL_ENTRY = 10
MIN_PRICE_MOVE_FROM_LAST_TRADE = 10
MIN_PROFIT_TO_CLOSE = 10
NUM_SHARES_PER_TRADE = 1

close = df['Close']
price_history = []

for close_price in close:
    price_history.append(close_price)
    if len(price_history) > SMA_NUM_PERIODS:
        del (price_history[0])
    sma = stats.mean(price_history)
    variance = 0
    for hist_price in price_history:
        variance = variance + ((hist_price - sma) ** 2)

    stdev = math.sqrt(variance / len(price_history))
    stdev_factor = stdev/20000
    if stdev_factor == 0:
        stdev_factor = 1



    if (ema_fast == 0):
        ema_fast = close_price
        ema_slow = close_price
    else:
        ema_fast = ((close_price - ema_fast) * (K_FAST*stdev_factor)) + ema_fast
        ema_slow = ((close_price - ema_slow) * (K_SLOW*stdev_factor)) + ema_slow

    ema_fast_values.append(ema_fast)
    ema_slow_values.append(ema_slow)

    apo = ema_fast - ema_slow
    apo_values.append(apo)

    if ((apo > (APO_VALUE_FOR_SELL_ENTRY*stdev_factor) and abs(close_price - last_sell_price) > (MIN_PRICE_MOVE_FROM_LAST_TRADE*stdev_factor))
        or (position > 0 and (apo >=0 or open_pnl > (MIN_PROFIT_TO_CLOSE/stdev_factor)))):
        orders.append(-1)
        last_sell_price = close_price
        position -= NUM_SHARES_PER_TRADE
        sell_sum_price_qty += (close_price*NUM_SHARES_PER_TRADE)
        sell_sum_qty += NUM_SHARES_PER_TRADE
        print("Sell ", NUM_SHARES_PER_TRADE, " @ ", close_price, "Position: ", position)

    elif ((apo < (APO_VALUE_FOR_BUY_ENTRY*stdev_factor) and abs(close_price - last_buy_price) > (MIN_PRICE_MOVE_FROM_LAST_TRADE*stdev_factor))
        or (position < 0 and (apo <= 0 or open_pnl > (MIN_PROFIT_TO_CLOSE/stdev_factor)))):
        orders.append(+1)
        last_buy_price = close_price
        position += NUM_SHARES_PER_TRADE
        buy_sum_price_qty += (close_price*NUM_SHARES_PER_TRADE)
        buy_sum_qty += NUM_SHARES_PER_TRADE
        print("Buy ", NUM_SHARES_PER_TRADE, " @ ", close_price, "Position: ", position)

    else:
        orders.append(0)
    positions.append(position)

    open_pnl = 0
    if position > 0:
        if sell_sum_qty > 0:
            open_pnl = abs(sell_sum_qty) * ((sell_sum_price_qty/sell_sum_qty) - (buy_sum_price_qty/buy_sum_qty))
        open_pnl += abs(sell_sum_qty - position) * (close_price - (buy_sum_price_qty - close_price))
    elif position < 0:
        if buy_sum_qty > 0:
            open_pnl = abs(buy_sum_qty) * ((sell_sum_price_qty/sell_sum_qty) - (buy_sum_price_qty/buy_sum_qty))
        open_pnl += abs(buy_sum_qty - position) * (sell_sum_price_qty/(sell_sum_qty - close_price))
    else:
        close_pnl += (sell_sum_price_qty - buy_sum_price_qty)
        buy_sum_price_qty = 0
        buy_sum_qty = 0
        sell_sum_price_qty = 0
        sell_sum_qty = 0
        last_buy_price = 0
        last_sell_price = 0

    print("OpenPnL: ", open_pnl, "ClosedPnL: ", close_pnl)
    pnls.append(close_pnl + open_pnl)


df['ClosePrice'] = close
df['Fast10DaysEMA'] = ema_fast_values
df['Slow40DaysEMA'] = ema_slow_values
df['APO'] = apo_values
df['Trades'] = orders
df['Position'] = position
df['Pnl'] = pnls

df['ClosePrice'].plot(color='blue', lw=3., legend=True)
df['Fast10DaysEMA'].plot(color='y', lw=1., legend=True)
df['Slow40DaysEMA'].plot(color='m', lw=1., legend=True)

plt.plot(df.loc[df['Trades'] == 1 ].index, df['ClosePrice'][df['Trades'] == 1 ], color='r', lw=0, marker='^', markersize=7, label='buy')
plt.plot(df.loc[df['Trades'] == -1 ].index, df['ClosePrice'][df['Trades'] == -1 ], color='g', lw=0, marker='v', markersize=7, label='sell')

plt.legend()
plt.show()

df['APO'].plot(color='k', lw=3., legend=True)
plt.plot(df.loc[df['Trades'] == 1 ].index, df['APO'][ df['Trades'] == 1 ], color='r', lw=0, marker='^', markersize=7, label='buy')
plt.plot(df.loc[df['Trades'] == -1 ].index, df['APO'][ df['Trades'] == -1 ], color='g', lw=0, marker='v', markersize=7, label='sell')
plt.axhline(y=0, lw=0.5, color='k')
for i in range( APO_VALUE_FOR_BUY_ENTRY, APO_VALUE_FOR_BUY_ENTRY*5, APO_VALUE_FOR_BUY_ENTRY ):
  plt.axhline(y=i, lw=0.5, color='r')
for i in range( APO_VALUE_FOR_SELL_ENTRY, APO_VALUE_FOR_SELL_ENTRY*5, APO_VALUE_FOR_SELL_ENTRY ):
  plt.axhline(y=i, lw=0.5, color='g')
plt.legend()
plt.show()


df['Position'].plot(color='k', lw=1., legend=True)
plt.plot(df.loc[df['Position'] == 0 ].index, df['Position'][df['Position'] == 0 ], color='k', lw=0, marker='.', label='flat')
plt.plot(df.loc[df['Position'] > 0 ].index, df['Position'][df['Position'] > 0 ], color='r', lw=0, marker='+', label='long')
plt.plot(df.loc[df['Position'] < 0 ].index, df['Position'][df['Position'] < 0 ], color='g', lw=0, marker='_', label='short')
plt.axhline(y=0, lw=0.5, color='k')
for i in range( NUM_SHARES_PER_TRADE, NUM_SHARES_PER_TRADE*25, NUM_SHARES_PER_TRADE*5 ):
  plt.axhline(y=i, lw=0.5, color='r')
for i in range( -NUM_SHARES_PER_TRADE, -NUM_SHARES_PER_TRADE*25, -NUM_SHARES_PER_TRADE*5 ):
  plt.axhline(y=i, lw=0.5, color='g')
plt.legend()
plt.show()

df['Pnl'].plot(color='k', lw=1., legend=True)
plt.plot(df.loc[df['Pnl'] > 0 ].index, df['Pnl'][df['Pnl'] > 0 ], color='g', lw=0, marker='.')
plt.plot(df.loc[df['Pnl'] < 0 ].index, df['Pnl'][df['Pnl'] < 0 ], color='r', lw=0, marker='.')
plt.legend()
plt.show()
