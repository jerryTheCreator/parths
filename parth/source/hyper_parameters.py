# STRATEGY HYPER-PARAMETERS

# SYMBOLS = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA', 'UNH', 'V',
#     'XOM', 'LLY', 'JNJ', 'JPM', 'WMT', 'MA', 'AVGO', 'PG', 'ORCL', 'HD', 'CVX',
#     'MRK', 'KO', 'PEP', 'ABBV', 'COST', 'BAC', 'CRM', 'PFE', 'MCD', 'CSCO', 'TMO',
#     'ACN', 'ADBE', 'AMD', 'ABT', 'NFLX', 'LIN', 'DHR', 'CMCSA', 'NKE', 'DIS',
#     'TXN', 'VZ', 'WFC', 'NEE', 'UPS', 'PM', 'MS', 'BMY']

# SYMBOLS = ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA', 'UNH', 'V']

SYMBOLS = ['TSLA'] # , 'AAPL']
GENERAL_TIMEFRAME = 60

# Risk Management
TRADE_INFO_FILENAME = 'trade_info.parquet'
DEFAULT_RISK_PERCENT = 1
MAXIMUM_CAPITAL_EXPOSURE = 10 # 11.5
MINIMUM_TRADE_COUNT = 10
MINIMUM_WINS_COUNT = 3

# Indicator Timeframes
HT_RES = 60
NATR_RES = 60 
ST_GRAB_RES = 60
EMA_RES = 240
HULL_RES = 240


