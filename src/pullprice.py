#ADJ is the amount in dollars to make up for the price diff bw/ yfinance api and broker data
yfinance_sym_dic = { 
    'MNQ': {'SYM':'MNQ=F', 'ADJ': 0},
    'NQ': {'SYM':'NQ=F', 'ADJ': 0},
    'MES': {'SYM':'MES=F', 'ADJ': 0},
    'ES': {'SYM':'ES=F', 'ADJ': 0},
    'US100': {'SYM':'MNQ=F', 'ADJ': -53.18},
    'GC': {'SYM':'GC=F', 'ADJ': 0},
    'MGC': {'SYM':'MGC=F', 'ADJ': 0},
    'SI': {'SYM':'SI=F', 'ADJ': 0},
    'SIL': {'SYM':'SIL=F', 'ADJ': 0},
    'XAUUSD': {'SYM':'GC=F', 'ADJ': 0},
    'AGXUSD': {'SYM':'SI=F', 'ADJ': 0},
    'BZ': {'SYM':'BZ=F', 'ADJ': 0}, # Brent Crude Futures
    'CL': {'SYM':'CL=F', 'ADJ': 0}, # WTI Crude Futures
    'MCL': {'SYM':'MCL=F', 'ADJ': 0}, # WTI Micro Crude Futures
    'UKOIL': {'SYM':'BZ=F', 'ADJ': 0}, # Brent Crude Futures
    'ADA': {'SYM':'ADA-USD', 'ADJ': 0},
    'BTC': {'SYM':'BTC-USD', 'ADJ': 0},
    'ETH': {'SYM':'ETH-USD', 'ADJ': 0},
    'ETH.i': {'SYM':'ETH-USD', 'ADJ': 0}
}


def get_live_price(ticker_symbol: str, yfinance_map: dict)-> float:
    import yfinance as yf

    # Initialize the Ticker object 
    try:
        if ticker_symbol in yfinance_map.keys():
            ticker = yf.Ticker(yfinance_map[ticker_symbol]['SYM'])
            # .fast_info provides the most recent 'last_price'
            # This is faster than fetching the full .info dictionary
            current_price = ticker.fast_info['last_price'] + yfinance_map[ticker_symbol]['ADJ']
        else:
            ticker = yf.Ticker(ticker_symbol)
            current_price = ticker.fast_info['last_price']
    except KeyError:
        print(f'No price data found, symbol may be delisted: {ticker_symbol}')
        current_price = None
        
    return current_price
