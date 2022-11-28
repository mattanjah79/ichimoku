import pandas as pd
import datetime
import numpy as np
import yfinance as yf
import plotly.graph_objs as go

# IMPORT DATA
start = pd.to_datetime('2020-02-04')
end = pd.to_datetime('2022-11-20')

df = yf.download('^N225', start, end)
#print(df)


# ICHIMOKU APPLICATION
index = pd.date_range(end, periods=26, freq='D')
columns = df.columns

dfna = pd.DataFrame(index=index, columns=columns)

df = pd.concat([df,dfna])



# --- tenkan sen --- #
# --- conversion line (9-period high + 9 period low) / 2 --- #
nine_period_high = df['High'].rolling(window=9).max()
nine_period_low = df['Low'].rolling(window=9).min()
df['tenkan_sen'] = (nine_period_high + nine_period_low)/2

# --- kijun sen --- #
# --- base line (26-period high + 26 period low) / 2 --- #
twosix_period_high = df['High'].rolling(window=26).max()
twosix_period_low = df['Low'].rolling(window=26).min()
df['kijun_sen'] = (twosix_period_high + twosix_period_low)/2

# --- senkou span A --- #
# --- leading span A (cl + bl) / 2 --- #
df['senkou_span_a'] = ((df['tenkan_sen'] + df['kijun_sen'])/2).shift(26)

# --- senkou span B --- #
# --- leading span B (52-period high + 52 period low) / 2 --- #
fivetwo_period_high = df['High'].rolling(window=52).max()
fivetwo_period_low = df['Low'].rolling(window=52).min()
df['senkou_span_b'] = ((fivetwo_period_high + fivetwo_period_low)/2).shift(26)

# --- chikou span --- #
# --- lagging span - close plotted 26 periods in the past --- #
df['chikou_span'] = df['Close'].shift(-26)

# ALGO VIZ

# declare figure
fig = go.Figure()

# set up traces
fig.add_trace(go.Candlestick(x=df.index,
                             open=df['Open'],
                             high=df['High'],
                             low=df['Low'],
                             close=df['Close'], name='market data'))
fig.add_trace(go.Scatter(x=df.index, y=df['tenkan_sen'], line=dict(color='red', width=.8), name='tenkan sen'))
fig.add_trace(go.Scatter(x=df.index, y=df['kijun_sen'], line=dict(color='blue', width=.8), name='kijun sen'))
fig.add_trace(go.Scatter(x=df.index, y=df['senkou_span_a'], line=dict(color='green', width=.8), name='senkou span a'))
fig.add_trace(go.Scatter(x=df.index, y=df['senkou_span_b'], line=dict(color='pink', width=.8), name='senkou span b')) #fill='tonexty', fillcolor='salmon', opacity=.01
fig.add_trace(go.Scatter(x=df.index, y=df['chikou_span'], line=dict(color='skyblue', width=.8), name='chikou span'))

# show
#fig.show()


# fig write
#fig.write_html('/Users/Mate/Desktop/xtb/fig_html/ichimoku.html')


# BACKTESTING


# SIGNALS
    # LINES
#print(df)


    # PRICE TO LINE

    # CHIKOU SPAN


