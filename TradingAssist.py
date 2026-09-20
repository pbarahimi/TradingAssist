#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import time
import os
import sys
import argparse
from IPython.display import clear_output
import re
from urllib.parse import quote

sys.path.append('./src')
# from GSheetImporter import GSheetImporter
from pullprice import yfinance_sym_dic, get_live_price

# # Load Arguments
PRINT = True
GENERATE_MARKDOWN = False
GENERATE_HTML = False
REPORT_PATH = '../TradingAssistWebapp/pages/'
# GSHEET_CREDS = "c:/users/pbara/Documents/Python/secrets/sheets-pandas-reader-193e91a08e8e.json"
# GSHEET_CREDS = '/home/pbarahimi/.credentials/gsheets.json'

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
        "-P", "--Print",
        type=int,
        help="Set to 0 to switch off print to stdout"
    )

    parser.add_argument(
        "-r", "--Report_path",
        type=str,
        help="Path to save a reports"
    )

    args = parser.parse_args()
    return args

def myfunc()->None:
    # # Read the trades worksheet

    # Replace with your actual Google Sheet ID
    # (Found in the URL: https://docs.google.com/spreadsheets/d/SHEET_ID/edit)
    SHEET_ID = "1HJ9h7UEtUQCXNA58UkZyPsHogJWBAcB1lNWt9nOPMR4"

    # Specify the tab name (optional, defaults to the first sheet)
    SHEET_NAME = "TradesCopy"
    sql_query = "SELECT * WHERE P=0" # Query to only pull open trades
    encoded_query = quote(sql_query)
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}&tq={encoded_query}"
    num_cols = ['Open Price', 'Close Price', 'Commission','Risk ($)', 'Balance at Open', 'PnL']

    # Load into DataFrame read directly from the url
    df = pd.read_csv(url)
    df[num_cols] = df[num_cols].fillna('0')
    for c in num_cols:
        df[c] = df[c].apply(lambda x: float(re.sub(r"\(", "-", re.sub(r"[,\)]", "", str(x))))) # Replace '(' with '-' and remove ')', ',' from the numbers to cast them to float
    # gsheet = GSheetImporter(sheet_id=SHEET_ID, sheet_name=SHEET_NAME, credentials_path=GSHEET_CREDS)
    # gsheet.get_dataframe()
    # gsheet.to_num(num_cols)

    # Keep open trades
    #df = gsheet.df[gsheet.df['Is Closed']==0].copy()
    #df = df[df['Is Closed']==0].copy()

    # # Get Point Values
    # Specify the tab name (optional, defaults to the first sheet)
    SHEET_NAME = 'Symbols'
    
    # Pulling directly from shared url to avoid using google service account quota
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={SHEET_NAME}"
    point_val_df = pd.read_csv(url, header=None, names=['Symbol', 'Point Value'])

    # # Get Prices
    price_df = pd.DataFrame(df['Symbol']).drop_duplicates()
    price_df['Current Price'] = price_df.Symbol.apply(lambda x : get_live_price(x, yfinance_sym_dic))

    # # Append Price to trades DF    
    df = pd.merge(df, price_df, on='Symbol', how='left')
    df = pd.merge(df, point_val_df, on='Symbol', how='left')
    df['Point Value'] = df['Point Value'].fillna(1)
    df['PnL'] = (df['Volume'] * (df['Current Price']-df['Open Price']) * df['Point Value']).round(2)

    if PRINT:
        # # Group by account and symbol to report
        if sys.platform == "win32":
            os.system('cls')
        else:
            os.system('clear')

        print(df.groupby(['Account','Symbol']).agg({'Volume': sum, 'PnL': sum}))
        print('\n', 50 * '-', '\n')
        print(df.groupby('Account').agg({'PnL': sum}))
        print('\n', 50 * '-', '\n')
        print(df.groupby(['Symbol','Account']).agg({'Volume': sum, 'PnL': sum}))
        print('\n', 50 * '-', '\n')
        print(df.groupby('Symbol').agg({'Volume': sum, 'PnL': sum}))

    # # Generate Markdowns
    if GENERATE_MARKDOWN:
        '''
        page_nm = 'acct_lvl_stats.md'
        with open(os.path.join(REPORT_PATH, page_nm), 'w') as f:  # Save to a file
            f.write(df.groupby('Account').agg({'PnL': sum}).to_markdown())

        page_nm = 'sym_lvl_stats.md'
        with open(os.path.join(REPORT_PATH, page_nm), 'w') as f:
            f.write(df.groupby('Symbol').agg({'Volume': sum, 'PnL': sum}).to_markdown())

        page_nm = 'sym_acct_lvl_stats.md'
        with open(os.path.join(REPORT_PATH, page_nm), 'w') as f:
            f.write(df.groupby(['Symbol','Account'], as_index=False).agg({'Volume': sum, 'PnL': sum}).to_markdown())
        '''
        page_nm = 'acct_sym_lvl_stats.md'
        with open(os.path.join(REPORT_PATH, page_nm), 'w') as f:
            f.write(df.groupby(['Account','Symbol'], as_index=False).agg({'Volume': sum, 'PnL': sum}).to_markdown())


    # # Generate HTML tables
    if GENERATE_HTML:
        '''
        page_nm = 'acct_lvl_stats.html'
        with open(os.path.join(REPORT_PATH, page_nm), 'w') as f:  # Save to a file
            t = df.groupby('Account').agg({'PnL': sum})
            f.write(t.to_html(border=0, justify='left',  table_id='dataTable', classes='table table-striped table-hover'))
 
        page_nm = 'sym_lvl_stats.html'
        with open(os.path.join(REPORT_PATH, page_nm), 'w') as f:
            t = df.groupby('Symbol').agg({'Volume': sum, 'PnL': sum})
            f.write(t.to_html(border=0, justify='left',  table_id='dataTable', classes='table table-striped table-hover'))

        page_nm = 'sym_acct_lvl_stats.html'
        with open(os.path.join(REPORT_PATH, page_nm), 'w') as f:
            t = df.groupby(['Symbol','Account']).agg({'Volume': sum, 'PnL': sum})
            f.write(t.to_html(border=0, justify='left',  table_id='dataTable', classes='table table-striped table-hover'))
        '''
        page_nm = 'acct_sym_lvl_stats.html'
        with open(os.path.join(REPORT_PATH, page_nm), 'w') as f:
            t = df.groupby(['Account','Symbol']).agg({'Volume': sum, 'PnL': sum})
            f.write(t.to_html(border=0, justify='left',  table_id='dataTable', classes='table table-striped table-hover'))

    return None

if __name__ == "__main__":
    args = parse_args()

    # Handle Markdown flag
    if args.Markdown == 1:
        GENERATE_MARKDOWN = True

    # Handle HTML flag
    if args.HTML == 1:
        GENERATE_HTML = True

    # Handle print to stdout flag
    if args.Print == 0:
        PRINT = False

    # Handle Report_path argument - update reports location
    if args.Report_path:
        REPORT_PATH = args.Markdown_path

    if GENERATE_MARKDOWN:
        print(f"Markdowns will be saved to:", REPORT_PATH)

    if GENERATE_HTML:
        print(f"HTML files will be saved to:", REPORT_PATH)

    while True:
        try:
            myfunc()
        except Exception as e:
            print(f'An error occured: {e}')
        time.sleep(1)
