#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import yfinance as yf
import time
import os
import re
from IPython.display import clear_output


# In[2]:


#ADJ is the amount in dollars to make up for the price diff bw/ yfinance api and broker data
yfinance_sym_dic = { 
    'MNQ': {'SYM':'MNQ=F', 'ADJ': 0},
    'NQ': {'SYM':'NQ=F', 'ADJ': 0},
    'US100': {'SYM':'MNQ=F', 'ADJ': -53.18},
    'GC': {'SYM':'GC=F', 'ADJ': 0},
    'MGX': {'SYM':'MGC=F', 'ADJ': 0},
    'SI': {'SYM':'SI=F', 'ADJ': 0},
    'SIL': {'SYM':'SIL=F', 'ADJ': 0},
    'XAUUSD': {'SYM':'GC=F', 'ADJ': 0},
    'AGXUSD': {'SYM':'SI=F', 'ADJ': 0},
    'BZ': {'SYM':'BZ=F', 'ADJ': 0}, # Brent Crude Futures
    'CL': {'SYM':'CL=F', 'ADJ': 0}, # WTI Crude Futures
    'BTC': {'SYM':'BTC-USD', 'ADJ': 0},
    'ETH': {'SYM':'ETH-USD', 'ADJ': 0}
}


def get_live_price(ticker_symbol: str, yfinance_map: dict)-> float:
    # Initialize the Ticker object 
    if ticker_symbol in yfinance_map.keys():
        ticker = yf.Ticker(yfinance_map[ticker_symbol]['SYM'])
        # .fast_info provides the most recent 'last_price'
        # This is faster than fetching the full .info dictionary
        current_price = ticker.fast_info['last_price'] + yfinance_map[ticker_symbol]['ADJ']
    else:
        ticker = yf.Ticker(ticker_symbol)
        current_price = ticker.fast_info['last_price']
        
    return current_price



def myfunc()->None:
    # # Read the trades worksheet

    # In[3]:
    
    
    # 1. Replace with your actual Google Sheet ID
    # (Found in the URL: https://docs.google.com/spreadsheets/d/SHEET_ID/edit)
    SHEET_ID = "1HJ9h7UEtUQCXNA58UkZyPsHogJWBAcB1lNWt9nOPMR4"
    
    # 2. Specify the tab name (optional, defaults to the first sheet)
    SHEET_NAME = 'Trades'
    
    # 3. Construct the export URL
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"

    # 4. Load into DataFrame
    df = pd.read_csv(url)
    
    # Cast numeric columns from str to float type
    cols = ['Open Price', 'Close Price', 'Commission']
    for c in cols:
        df[c] = df[c].apply(lambda x: float(re.sub(r"\(", "-", re.sub(r"[,\)]", "", x))))
    df.head()
    
    
    # # Get Point Values
    
    # In[4]:
    
    
    # 2. Specify the tab name (optional, defaults to the first sheet)
    SHEET_NAME = 'Symbols'
    
    # 3. Construct the export URL
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
    
    # 4. Load into DataFrame
    point_val_df = pd.read_csv(url, header=None, names=['Symbol', 'Point Value'])
    point_val_df.head()
    
    
    # # Get Prices
    
    # In[5]:
    
    
    price_df = pd.DataFrame(df['Symbol']).drop_duplicates()
    price_df['Current Price'] = price_df.Symbol.apply(lambda x : get_live_price(x, yfinance_sym_dic))
    price_df
    
    
    # # Append Price to trades DF
    
    # In[6]:
    
    
    df = pd.merge(df, price_df, on='Symbol', how='left')
    df = pd.merge(df, point_val_df, on='Symbol', how='left')
    df['Point Value'] = df['Point Value'].fillna(1)
    df['PnL'] = (df['Volume'] * (df['Current Price']-df['Open Price']) * df['Point Value']).round(2)
    df
    
    
    # # Group by account and symbol to report
    
    # In[7]:
    
    out = df.groupby(['Symbol','Account']).agg({'PnL': sum})
    os.system('cls')
    print(out)

while True:
    myfunc()
    time.sleep(2)