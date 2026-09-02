#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import yfinance as yf
import time
import os
import re
import sys
from IPython.display import clear_output
import gspread
import argparse

    
# # Load Arguments

GENERATE_MARKDOWN = True
GENERATE_HTML = True
REPORT_PATH = '../TradingAssistWebapp/pages/'
GSHEET_CREDS = "c:/users/pbara/Documents/Python/secrets/sheets-pandas-reader-193e91a08e8e.json"

def parse_args():
    parser = argparse.ArgumentParser(description="Reporting options")

    parser.add_argument(
        "-M", "--Markdown",
        type=int,
        help="Set to 1 to print 'Markdown'"
    )

    parser.add_argument(
        "-H", "--HTML",
        type=int,
        help="Set to 1 to print 'HTML'"
    )
    
    parser.add_argument(
        "-r", "--Report_path",
        type=str,
        help="Path to save a reports"
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
    'ETH': {'SYM':'ETH-USD', 'ADJ': 0},
    'ETH.i': {'SYM':'ETH-USD', 'ADJ': 0}
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
    
    # Replace with your actual Google Sheet ID
    # (Found in the URL: https://docs.google.com/spreadsheets/d/SHEET_ID/edit)
    SHEET_ID = "1HJ9h7UEtUQCXNA58UkZyPsHogJWBAcB1lNWt9nOPMR4"
    
    # Specify the tab name (optional, defaults to the first sheet)
    SHEET_NAME = "Trades"

    # Option 1: Simple way to read a shared google sheet with the view as is
    '''
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
    # Load into DataFrame
    df = pd.read_csv(url)
    '''
    
    # Option 2: Requires google account service credentials to read the full sheet regardless of the filters applied in the browser
    gc = gspread.service_account(filename=GSHEET_CREDS)
    sh = gc.open_by_key(SHEET_ID)
    worksheet = sh.worksheet(SHEET_NAME)
    df = pd.DataFrame(worksheet.get_all_records())

    # Keep open trades only
    df = df[df.Closed=='No'].copy()
    
    # Fill numberic columns' NA with 0 and cast numeric columns from str to float type
    cols = ['Open Price', 'Close Price', 'Commission','Risk ($)', 'Balance at Open', 'PnL']
    df[cols] = df[cols].fillna('0')
    for c in cols:
        df[c] = df[c].apply(lambda x: float(re.sub(r"\(", "-", re.sub(r"[,\)]", "", str(x))))) # Replace '(' with '-' and remove ')', ',' from the numbers to cast them to float
    df.head()

    # # Get Point Values
    # 2. Specify the tab name (optional, defaults to the first sheet)
    SHEET_NAME = 'Symbols'

    # Pick an options:
    '''
    OPTION 1: Read 'Symbols directly from shared url
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
    point_val_df = pd.read_csv(url, header=None, names=['Symbol', 'Point Value'])
    '''

    # OPTION 2: Read 'Symbols' sheet using using Google authentication - gspread
    point_val_df = pd.DataFrame(sh.worksheet(SHEET_NAME).get_all_records(head=0))
    all_values = sh.worksheet(SHEET_NAME).get_all_values()
    point_val_df = pd.DataFrame(all_values, columns=['Symbol', 'Point Value'])
    point_val_df['Point Value'] = point_val_df['Point Value'].astype(float)
    
    
    # # Get Prices
    price_df = pd.DataFrame(df['Symbol']).drop_duplicates()
    price_df['Current Price'] = price_df.Symbol.apply(lambda x : get_live_price(x, yfinance_sym_dic))
    price_df
    
    
    # # Append Price to trades DF    
    df = pd.merge(df, price_df, on='Symbol', how='left')
    df = pd.merge(df, point_val_df, on='Symbol', how='left')
    df['Point Value'] = df['Point Value'].fillna(1)
    df['PnL'] = (df['Volume'] * (df['Current Price']-df['Open Price']) * df['Point Value']).round(2)
    df
    
    
    # # Group by account and symbol to report
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
    if GENERATE_MARKDOWN:
        page_nm = 'acct_lvl_stats.md'
        with open(os.path.join(REPORT_PATH, page_nm), 'w') as f:  # Save to a file
            f.write(df.groupby('Account').agg({'PnL': sum}).to_markdown())
            
        page_nm = 'sym_lvl_stats.md'
        with open(os.path.join(REPORT_PATH, page_nm), 'w') as f:
            f.write(df.groupby('Symbol').agg({'Volume': sum, 'PnL': sum}).to_markdown())
        
        page_nm = 'sym_acct_lvl_stats.md'
        with open(os.path.join(REPORT_PATH, page_nm), 'w') as f:
            f.write(df.groupby(['Symbol','Account'], as_index=False).agg({'Volume': sum, 'PnL': sum}).to_markdown())
        
        page_nm = 'acct_sym_lvl_stats.md'
        with open(os.path.join(REPORT_PATH, page_nm), 'w') as f:
            f.write(df.groupby(['Account','Symbol'], as_index=False).agg({'Volume': sum, 'PnL': sum}).to_markdown())


    # # Generate HTML tables
    if GENERATE_HTML:
        # Create HTML with DataTables library (sortable, searchable, paginated)
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>DataFrame Table</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <style>
                body {{
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .container {{
                    max-width: 900px;
                    background-color: white;
                    padding: 30px;
                    border-radius: 8px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                }}
                h1 {{
                    margin-bottom: 30px;
                    color: #333;
                }}
                table {{
                    font-size: 14px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Data Report</h1>
                #DataFrameHtml
            </div>
        </body>
        </html>
        """
        page_nm = 'acct_lvl_stats.html'
        with open(os.path.join(REPORT_PATH, page_nm), 'w') as f:  # Save to a file
            t = df.groupby('Account').agg({'PnL': sum})
            f.write(html_content.replace('#DataFrameHtml', t.to_html(border=0, justify='left',  table_id='dataTable', classes='table table-striped table-hover')))
            
        page_nm = 'sym_lvl_stats.html'
        with open(os.path.join(REPORT_PATH, page_nm), 'w') as f:
            t = df.groupby('Symbol').agg({'Volume': sum, 'PnL': sum})
            f.write(html_content.replace('#DataFrameHtml', t.to_html(border=0, justify='left',  table_id='dataTable', classes='table table-striped table-hover')))
        
        page_nm = 'sym_acct_lvl_stats.html'
        with open(os.path.join(REPORT_PATH, page_nm), 'w') as f:
            t = df.groupby(['Symbol','Account']).agg({'Volume': sum, 'PnL': sum})
            f.write(html_content.replace('#DataFrameHtml', t.to_html(border=0, justify='left',  table_id='dataTable', classes='table table-striped table-hover')))
        
        page_nm = 'acct_sym_lvl_stats.html'
        with open(os.path.join(REPORT_PATH, page_nm), 'w') as f:
            t = df.groupby(['Account','Symbol']).agg({'Volume': sum, 'PnL': sum})
            f.write(html_content.replace('#DataFrameHtml', t.to_html(border=0, justify='left',  table_id='dataTable', classes='table table-striped table-hover')))
    return None
            
if __name__ == "__main__":
    args = parse_args()

    # Handle Markdown flag
    if args.Markdown == 1:
        GENERATE_MARKDOWNS = True

    # Handle HTML flag
    if args.HTML == 1:
        GENERATE_HTML = True

    # Handle Markdown_path flag and print the new path if any
    if args.Report_path:
        REPORT_PATH = args.Markdown_path

    if GENERATE_MARKDOWNS:
        print(f"Markdowns will be saved to:", REPORT_PATH)

    if GENERATE_HTML:
        print(f"HTML files will be saved to:", REPORT_PATH)

    while True:
        myfunc()
        time.sleep(2)