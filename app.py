import time
import pandas as pd
import streamlit as st

import datetime
from pathlib import Path
from main import write_hyperparameters, write_parameters, runstrat
from parth.utils.dataloader import YFDataloader


# Path to Hyperparameters and Parametersclear
path_params = Path('data/params/params.csv')
path_hparams = Path('data/params/hparams.csv')

# Parameters/Hyperparameters Dataframes 
df_params = pd.read_csv(path_params)
df_hparams = pd.read_csv(path_hparams)

# Options for Indicator/Strategy Settings
options_sources = ['Open', 'High', 'Low', 'Close']
options_symbols =  ['AAPL', 'MSFT', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA', 'UNH', 'V',
   'XOM', 'LLY', 'JNJ', 'JPM', 'WMT', 'MA', 'AVGO', 'PG', 'ORCL', 'HD', 'CVX',
   'MRK', 'KO', 'PEP', 'ABBV', 'COST', 'BAC', 'CRM', 'PFE', 'MCD', 'CSCO', 'TMO',
   'ACN', 'ADBE', 'AMD', 'ABT', 'NFLX', 'LIN', 'DHR', 'CMCSA', 'NKE', 'DIS',
   'TXN', 'VZ', 'WFC', 'NEE', 'UPS', 'PM', 'MS', 'BMY'
]
options_symbols.sort()
options_resolutions = {
   "1m" : 1, 
   "5m" : 5, 
   "15m" : 15, 
   "30m" : 30, 
   "1h" : 60, 
   "4h" : 240, 
   "1d" : 1440, 
   "1wk" : 7 * 1440,
}
list_resolutions = list(options_resolutions.keys())


# Define the tabs for the app
tab_settings, tab_chart, tab_dataframe, tab_logs = \
   st.tabs([
      ":wrench: Settings", 
      ":chart_with_upwards_trend: Charts/Visualizations", 
      ":bar_chart: Dataframe", 
      ":calendar: Logs"])


with tab_settings:

   column_left, column_right = st.columns([.8 ,.1])
   column_left.header("STRATEGY SETTINGS")
   button_run_settings = column_right.button('Run', type='primary') # Use to commit settings to file


   # GENERAL SETTINGS
   st.subheader("General Settings", divider='rainbow')

   input_symbols = st.multiselect(label='Symbols/Tickers', 
                                 options=options_symbols,
                                 key='SYMBOLS') # SYMBOLS
   
   input_timeframe = st.selectbox(label='General Timeframe', 
                                 options=list_resolutions, 
                                 index=4,
                                 key='GENERAL_TIMEFRAME') # GENERAL_TIMEFRAME = 60
   
   # Backtest Range
   column_left, column_right = st.columns(2)   
   input_start_date = column_left.date_input(label="Backtest Start Date", 
                                    min_value=datetime.date(2000, 1, 1),
                                    value=datetime.date(2017, 1, 1),
                                    key='START_DATE').strftime("%Y-%m-%d")
   
   input_end_date = column_right.date_input(label="End Date", 
                                    min_value=datetime.date(2000, 1, 1),
                                    value=datetime.date(2023, 12, 31),
                                    key='END_DATE').strftime("%Y-%m-%d")

   # Get available timeframes for indicator
   index_res_selected = list_resolutions.index(input_timeframe)
   allowed_resolutions = list_resolutions[index_res_selected : ]


   # INDICATOR PARAMETERS
   st.subheader("Indicator Parameters", divider='rainbow')


   # Halftrend
   st.text('HALFTREND')

   column_left, column_mid, column_right = st.columns(3) 

   input_ht_res = column_left.selectbox(label='Timeframe', 
                                        options=allowed_resolutions, 
                                        index=0,
                                        key='HT_RES') # HT_RES = 60
   
   input_amplitude = column_mid.number_input(label='Amplitude',
                                             min_value=2,
                                             value=2,
                                             key='AMPLITUDE')   # AMPLITUDE = 2

   input_channel_dev = column_right.number_input(label='Channel Deviation',
                                             min_value=0,
                                             value=2,
                                             key='CHANNELDEVIATION') # CHANNELDEVIATION = 2


   # ST Grab
   st.divider()
   st.text('ST GRAB')

   column_left, column_mid, column_right = st.columns(3) 
   input_st_res = column_left.selectbox(label='Timeframe', 
                                        options=allowed_resolutions, 
                                        index=0,
                                        key='ST_GRAB_RES') # ST_GRAB_RES = 60
   
   input_st_period = column_mid.number_input(label='Period',
                                             min_value=2,
                                             value=2,
                                             key='ST_GRAB_PERIOD') # ST_GRAB_PERIOD = 34


   # HTF EMAs
   st.divider()
   st.text('HTF EMAS')

   input_ema_res = st.selectbox(label='Timeframe', 
                                        options=allowed_resolutions, 
                                        index=0,
                                        key='EMA_RES') # EMA_RES = 240
   
   column_left, column_mid, column_right = st.columns(3) 
   input_ema_length_1 = column_left.number_input(label='EMA Period 1',
                                             min_value=2,
                                             value=21,
                                             key='EMA_LENGTH_1') # EMA_LENGTH_1 = 21
      
   input_ema_length_2 = column_mid.number_input(label='EMA Period 2',
                                             min_value=2,
                                             value=50,
                                             key='EMA_LENGTH_2') # EMA_LENGTH_2 = 50
   
   input_ema_length_3 = column_right.number_input(label='EMA Period 3',
                                             min_value=2,
                                             value=200,
                                             key='EMA_LENGTH_3') # EMA_LENGTH_3 = 200


   # ATR Trailing Stop
   st.divider()
   st.text('ATR TRAILING STOP')

   column_left, column_mid, column_right = st.columns(3)  

   input_natr_res = column_left.selectbox(label='Timeframe', 
                                        options=allowed_resolutions, 
                                        index=0,
                                        key='NATR_RES') # NATR_RES = 60
   
   input_natr_period = column_mid.number_input(label='ATR Period',
                                             min_value=2,
                                             value=5,
                                             key='NATRPERIOD') # NATRPERIOD = 5
   
   input_natr_multiplier = column_right.number_input(label='ATR Multiplier',
                                             min_value=0.1,
                                             value=3.5,
                                             key='NATRMULTIP') # NATRMULTIP = 3.5


   # Hull Suite
   st.divider()
   st.text('HULL SUITE')

   input_hull_res = st.selectbox(label='Timeframe', 
                                        options=allowed_resolutions, 
                                        index=0,
                                        key='HULL_RES') # HULL_RES = 240
   
   column_left, column_mid, column_right = st.columns(3)  

   input_hull_src = column_left.selectbox(label='Source', 
                                        options=options_sources, 
                                        index=3,
                                        key='HULL_SRC') # HULL_SRC = 'Close'
   
   input_hull_mode = column_mid.selectbox(label='Mode',
                                          options=['HMA', 'EHMA', 'THMA'],
                                          index=0,
                                          key='HULL_MODESWITCH') # HULL_MODESWITCH = 'HMA'
   
   input_hull_length = column_right.number_input(label='Period',
                                             min_value=2,
                                             value=55,
                                             key='HULL_LENGTH') # HULL_LENGTH = 55


   #  Risk Management
   st.subheader("Risk Management | Kelly's Criterion Settings", divider='rainbow')

   column_left, column_right = st.columns(2)
   
   input_default_risk_percent = column_left.number_input(label="Default Risk Percentage",
                  min_value=0.01, max_value=100.,
                  value=1.,
                  help='\
                     This is the default percentage of the capital to be risked on each trade \
                     before the Kelly\'s percentage calculations is been implemented. \
                     It can take values within 0.01 and 100.'
                  ) # DEFAULT_RISK_PERCENT = 1

   input_max_capital_exposure = column_left.number_input(label="Maximum Capital Exposure",
                  min_value=1., max_value=100.,
                  value=11.5,
                  help='\
                     This is the maximum percentage of the capital exposure at a given time. \
                     It can take values within 0.01 and 100.'
                  ) # MAXIMUM_CAPITAL_EXPOSURE = 11.5
      
   input_min_trade_count = column_right.number_input(label="Minimum Trade Count",
                  min_value=10,
                  value=10,
                  help='\
                     This is the minimum number of trades to be closed before Kelly\'s Percentage \
                     is calculatead and implemented for position sizing. \
                     Defualt value is 10 trades.'
                  ) # MINIMUM_TRADE_COUNT = 10

   input_min_win_count = column_right.number_input(label="Minimum Win Count",
                  min_value=1,
                  value=3,
                  help='\
                     This is the minimum number of winning trades to be closed before Kelly\'s Percentage \
                     is calculatead and implemented for position sizing. \
                     Defualt value is 10 trades.'
                  ) # MINIMUM_WINS_COUNT = 3
   

with tab_chart:
   st.header('VISUALIZATIONS', anchor='Charts')

   # When Run Button is Pressed
   # Update Parameters and Hyperparameters
   if button_run_settings:
      if not input_symbols:
         error_no_symbols = 'No tickers/symbols selected for backtest. Please select at least one symbols from the list.'
         st.error(error_no_symbols)
         exit()
         
      
      st.toast('View backtest performance on the `Chart/Visualizations` tab.')
      
      parameters = df_params.iloc[0].to_dict()
      hyperparameters = df_hparams.iloc[0].to_dict()

      # Update Parameters
      parameters.update(
         # Halftrend
         HT_RES = options_resolutions[input_ht_res],
         AMPLITUDE = input_amplitude,
         CHANNELDEVIATION = input_channel_dev,

         # ST Grab
         ST_GRAB_RES = options_resolutions[input_st_res],
         ST_GRAB_PERIOD = input_st_period,

         # HTF EMAs
         EMA_RES = options_resolutions[input_ema_res],
         EMA_LENGTH_1 = input_ema_length_1,
         EMA_LENGTH_2 = input_ema_length_2,
         EMA_LENGTH_3 = input_ema_length_3,

         # ATR Trailing Stop
         NATR_RES =  options_resolutions[input_natr_res],
         NATRPERIOD = input_natr_period,
         NATRMULTIP = input_natr_multiplier,

         # Hull Suite
         HULL_RES = options_resolutions[input_hull_res],
         HULL_SRC = input_hull_src,
         HULL_MODESWITCH = input_hull_mode,
         HULL_LENGTH = input_hull_length,
      )

      # Update Hyperparameters
      hyperparameters.update(
         SYMBOLS = input_symbols,
         GENERAL_TIMEFRAME = options_resolutions[input_timeframe], 

         DEFAULT_RISK_PERCENT = input_default_risk_percent, 
         MAXIMUM_CAPITAL_EXPOSURE =  input_max_capital_exposure, 
         MINIMUM_TRADE_COUNT = input_min_trade_count, 
         MINIMUM_WINS_COUNT = input_min_win_count, 
      )

      # Write Settings to the CSV files
      write_parameters(**parameters)
      write_hyperparameters(**hyperparameters)

      # Use Spinner while running strategies
      cerebro = None
      with st.spinner('Strategy is running. Hold on to your horses...'):
         try:
            dataloader = YFDataloader(symbol=input_symbols, 
                                    resolution=input_timeframe,
                                    start_date = input_start_date,
                                    end_date=input_end_date)
            cerebro = runstrat(dataloader=dataloader, params=parameters, hparams=hyperparameters)
         except Exception as e:
            st.error('Some error occured : ', e)
            exit()

      if not dataloader.has_data:
         st.error('Could not fetch data')
         exit()

      st.success('Done!')

      progress_text = "Creating plots..."
      progress_bar = st.progress(0, text=progress_text)

      for percent_complete in range(100):
         time.sleep(0.01)
         progress_bar.progress(percent_complete + 1, text=progress_text)
      time.sleep(1)
      progress_bar.empty()

      st.write(F"FINAL BALANCE : {cerebro.broker.getvalue()}")

with tab_dataframe:
   st.header("DATA")


with tab_logs:
   st.header("LOGS")

