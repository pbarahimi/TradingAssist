#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pandas as pd
import yfinance as yf
import time
import os
import sys
import re
import sys
from IPython.display import clear_output
import warnings
import argparse
from datetime import datetime

    
# # Load Arguments

GENERATE_MARKDOWNS = False
MARKDOWN_PATH = '../TradingAssistWebapp/pages/'

def parse_args():
    parser = argparse.ArgumentParser(description="Markdown utility options")

    parser.add_argument(
        "-m", "--Markdown",
        type=int,
        help="Set to 1 to print 'Markdown'"
    )

    parser.add_argument(
        "-mp", "--Markdown_path",
        type=str,
        help="Path to save a markdown file"
    )

    args = parser.parse_args()
    return args

# In[2]:


#ADJ is the amount in dollars to make up for the price diff bw/ yfinance api and broker data
yfinance_sym_dic = { 
    'MNQ': {'SYM':'MNQ=F', 'ADJ': 0},
    'NQ': {'SYM':'NQ=F', 'ADJ': 0},
    'MES': {'SYM':'MES=F', 'ADJ': 0},
    'ES': {'SYM':'ES=F', 'ADJ': 0},
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
    
    # 5. Keep open trades only
    df = df[df.Closed=='No'].copy()
    
    # Fill numberic columns' NA with 0 and cast numeric columns from str to float type
    cols = ['Open Price', 'Close Price', 'Commission','Risk ($)', 'Balance at Open', 'PnL']
    df[cols] = df[cols].fillna('0')
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
    
    if sys.platform == "win32":
        os.system('cls')
    else:
        os.system('clear')
        
    print(df.groupby('Account').agg({'PnL': sum}))
    print('\n', 50 * '-', '\n')
    print(df.groupby('Symbol').agg({'Volume': sum, 'PnL': sum}))
    print('\n', 50 * '-', '\n')
    print(df.groupby(['Symbol','Account']).agg({'Volume': sum, 'PnL': sum}))
    print('\n', 50 * '-', '\n')
    print(df.groupby(['Account','Symbol']).agg({'Volume': sum, 'PnL': sum}))
    
    # # Generate Markdowns
    if GENERATE_MARKDOWNS:
        page_nm = 'acct_lvl_stats.md'
        with open(os.path.join(MARKDOWN_PATH, page_nm), 'w') as f:  # Save to a file
            f.write(df.groupby('Account').agg({'PnL': sum}).to_markdown())
            
        page_nm = 'sym_lvl_stats.md'
        with open(os.path.join(MARKDOWN_PATH, page_nm), 'w') as f:
            f.write(df.groupby('Symbol').agg({'Volume': sum, 'PnL': sum}).to_markdown())
        
        page_nm = 'sym_acct_lvl_stats.md'
        with open(os.path.join(MARKDOWN_PATH, page_nm), 'w') as f:
            f.write(df.groupby(['Symbol','Account']).agg({'Volume': sum, 'PnL': sum}).to_markdown())
        
        page_nm = 'acct_sym_lvl_stats.md'
        with open(os.path.join(MARKDOWN_PATH, page_nm), 'w') as f:
            f.write(df.groupby(['Account','Symbol']).agg({'Volume': sum, 'PnL': sum}).to_markdown())
        
    return None
            
if __name__ == "__main__":
    args = parse_args()

    # Handle Markdown flag
    if args.Markdown == 1:
        GENERATE_MARKDOWNS = True

    # Handle Markdown_path flag and print the new path if any
    if args.Markdown_path:
        MARKDOWN_PATH = args.Markdown_path

    if GENERATE_MARKDOWNS:
        print(f"Markdowns will be saved to:", MARKDOWN_PATH)

    while True:
        try:
            myfunc()
        except Exception:
            print(f'Error - {datetime.now().strftime("%m/%d/%Y %H:%M:%S")}.')
        time.sleep(2)