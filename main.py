import backtrader as bt
import pandas as pd
from pathlib import Path
from typing import Dict

from parth.strategies import MultiAssetStrategy
from parth.utils.dataloader import DataLoader, YFDataloader as yfd


def write_parameters(**kwargs):
    # Default Parameters
    parameters = {
        # Halftrend
        'HT_RES' : 60,
        'AMPLITUDE' : 2,
        'CHANNELDEVIATION' : 2,

        # ST Grab
        'ST_GRAB_RES' : 60,
        'ST_GRAB_PERIOD' : 34,

        # HTF EMAs
        'EMA_RES' : 240,
        'EMA_LENGTH_1' : 21,
        'EMA_LENGTH_2' : 50,
        'EMA_LENGTH_3' : 200,

        # ATR Trailing Stop
        'NATR_RES' : 60 ,
        'NATRPERIOD' : 5,
        'NATRMULTIP' : 3.5,

        # Hull Suite
        'HULL_RES' : 240,
        'HULL_SRC' : 'Close',
        'HULL_MODESWITCH' : 'HMA',
        'HULL_LENGTH' : 55,
        }
    
    # Update with passed keyword arguments
    parameters.update(**kwargs)

    # Generate parameters dataframe
    path_params = Path('data/params/params.csv')

    df_params = pd.DataFrame(parameters, index=[0])
    df_params.to_csv(path_params, index=False)


def write_hyperparameters(**kwargs):
    # Default Hyperparameters
    hyperparameters = {
        'SYMBOLS' : ['AAPL'],
        'GENERAL_TIMEFRAME' : 60, 

        # Risk Management
        'DEFAULT_RISK_PERCENT' : 1, 
        'MAXIMUM_CAPITAL_EXPOSURE' :  11.5, 
        'MINIMUM_TRADE_COUNT' : 10, 
        'MINIMUM_WINS_COUNT' : 3, 
        }
    
    # Update with passed keyword arguments
    hyperparameters.update(**kwargs)

    if not hyperparameters['SYMBOLS']:
        hyperparameters.update(SYMBOLS=['AAPL'])
        

    # Generate hyperparameters dataframe
    path_hparams = Path('data/params/hparams.csv')

    df_hparams = pd.DataFrame(hyperparameters)
    df_hparams.to_csv(path_hparams, index=False)


def runstrat(dataloader : DataLoader, params : Dict, hparams : Dict = None):

    # Assert All Parameters/Hyperparameters are available
    list_parameters = [
        'HT_RES', 
        'AMPLITUDE', 
        'CHANNELDEVIATION', 
        'ST_GRAB_RES', 
        'ST_GRAB_PERIOD', 
        'EMA_RES', 
        'EMA_LENGTH_1', 
        'EMA_LENGTH_2', 
        'EMA_LENGTH_3', 
        'NATR_RES', 
        'NATRPERIOD', 
        'NATRMULTIP', 
        'HULL_RES', 
        'HULL_SRC', 
        'HULL_MODESWITCH', 
        'HULL_LENGTH', 
    ]

    # Some missing parameters.
    for param_name in list_parameters:
        param = params.get(param_name, None)
        
        if param is None:
            return ValueError(f'Missing Parameter. `{param_name}`')

    # # Some missing parameters.
    # if not set(list_parameters).issubset(params.keys()):
    #     missing_params = set(list_parameters) - set(params.keys())
    #     raise ValueError(f"Missing Parameters [{' ,'.join(missing_params)}")   

    # Default Hyperparameters
    hyperparameters = {
        'SYMBOLS' : ['AAPL'],
        'GENERAL_TIMEFRAME' : 60, 

        # Risk Management
        'CAPITAL' : 100000.0,
        'DEFAULT_RISK_PERCENT' : 1, 
        'MAXIMUM_CAPITAL_EXPOSURE' :  11.5, 
        'MINIMUM_TRADE_COUNT' : 10, 
        'MINIMUM_WINS_COUNT' : 3, 
        }
    
    # Update with passed hyperparameters
    if hparams:
        hyperparameters.update(hparams) 

    # Create Backtrader Engine
    cerebro = bt.Cerebro(stdstats=False)
    cerebro.broker.setcash(hyperparameters.get('CAPITAL'))

    # Fetch Dataloader data, if not present
    if not dataloader.has_data:
        dataloader.load_data()

    GENERAL_TIMEFRAME = hyperparameters.get('GENERAL_TIMEFRAME')

    # Load Data into Engine
    _datas = dataloader.dataframes
    _symbols = list(_datas.keys())

    for key, value in _datas.items():
        cerebro.adddata(value, name=key) # Original Data

        # Resample Data for Each Indicator
        # Default to 1, if value is less than general timeframe
        compression_ht = max(int(params.get('HT_RES')/GENERAL_TIMEFRAME), 1)
        compression_ats = max(int(params.get('NATR_RES')/GENERAL_TIMEFRAME), 1)
        compression_st = max(int(params.get('ST_GRAB_RES')/GENERAL_TIMEFRAME), 1)
        compression_ema = max(int(params.get('EMA_RES')/GENERAL_TIMEFRAME), 1)
        compression_hull = max(int(params.get('HULL_RES')/GENERAL_TIMEFRAME), 1)

        data_ht=cerebro.resampledata(value, timeframe=bt.TimeFrame.Minutes, compression=compression_ht, name=f'{key}-halftrend')
        data_ats=cerebro.resampledata(value, timeframe=bt.TimeFrame.Minutes, compression=compression_ats, name=f'{key}-ats')
        data_stgrab=cerebro.resampledata(value, timeframe=bt.TimeFrame.Minutes, compression=compression_st, name=f'{key}-stgrab')
        data_ema=cerebro.resampledata(value, timeframe=bt.TimeFrame.Minutes, compression=compression_ema, name=f'{key}-htfema')
        data_hull=cerebro.resampledata(value, timeframe=bt.TimeFrame.Minutes, compression=compression_hull, name=f'{key}-hull')

        # Hide Plots for the Data
        data_ht.plotinfo.plot = False
        data_ats.plotinfo.plot = False
        data_stgrab.plotinfo.plot = False
        data_ema.plotinfo.plot = False
        data_hull.plotinfo.plot = False
 
    # Add the strategy
    cerebro.addstrategy(MultiAssetStrategy, symbol_list=_symbols, parameters=params, hyperparameters=hyperparameters)

    # Run the strategy
    cerebro.run()

    # cerebro.plot(iplot=False, volume=False, style='candle', numfigs=len(_symbols)* 2)
    # print(cerebro.broker.getvalue())
    return cerebro


if __name__ == '__main__':
    # runstrat(['AAPL', 'MSFT', 'GOOG', 'AMZN', 'NVDA', 'META', 'TSLA', 'UNH', 'V',
    #      'XOM', 'LLY', 'JNJ', 'JPM', 'WMT', 'MA', 'AVGO', 'PG', 'ORCL', 'HD', 'CVX'])
    # runstrat(['AAPL', 'TSLA', 'GOOG', 'MSFT', 'META'])

    # write_hyperparameters()
    # write_parameters()

    dataloader = yfd(['MSFT'], '1d')

    # Fetch the Hyperparameters
    hparams = pd.read_csv(Path('data/params/hparams.csv'))
    params = pd.read_csv(Path('data/params/params.csv'))
    hparams = hparams.iloc[0]
    params = params.iloc[0]

    params.to_dict()


    cerebro = runstrat(dataloader=dataloader, params=params)
    # print('Balance: ', cerebro.broker.getvalue())