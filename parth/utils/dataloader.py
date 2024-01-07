import pandas as pd
import logging

import backtrader as bt

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Union, List, Dict

from dateutil.parser import parse
import yfinance as yf


class DataLoader(ABC):
    # CLASS CONSTANT ATTRIBUTES
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    OHLC_COLUMNS = [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]
    RESOLUTIONS = ["1m", "5m", "15m", "30m", "1h", "4h", "1d", "1wk", "1mo"]
    TIMEFRAMES = {
        "1m" : bt.TimeFrame.Minutes, 
        "5m" : bt.TimeFrame.Minutes, 
        "15m" : bt.TimeFrame.Minutes, 
        "30m" : bt.TimeFrame.Minutes, 
        "1h" : bt.TimeFrame.Minutes, 
        "4h" : bt.TimeFrame.Minutes, 
        "1d" : bt.TimeFrame.Days, 
        "1w" : bt.TimeFrame.Weeks, 
        "1M" : bt.TimeFrame.Months, 
    }
    COMPRESSIONS = {
        "1m" : 1, 
        "5m" : 5, 
        "15m" : 15, 
        "30m" : 30, 
        "1h" : 60, 
        "4h" : 240, 
        "1d" : 1, 
        "1w" : 1, 
        "1M" : 1, 
    } 
    DATA_ARGS = {
        'open' : 0,
        'high' : 1,
        'low' : 2, 
        'close' : 3,
        'volume' : 4,
        'openinterest' : -1, 
        'timeframe' : None,
        'compression' : None,
    }


    def __init__(
        self, 
        symbol: Union[str, List[str]], 
        resolution: str, 
        **period_kwargs
    ) -> None:
        
        # Confirm required arguments passed
        assert symbol and resolution, '`symbol` and `resolution` arguments are required.'

        # Set the symbol, resolution and date range for the object
        self.symbols : List[str] = self._set_symbol(symbol)
        self.resolution = self._set_resolution(resolution)
        self.start_date, self.end_date = self._set_data_range(period_kwargs)

        # OHLC DataFrames
        self._raw_dataframes : Dict[str, pd.DataFrame] = {}
        self.__dataframes : Dict[str, pd.DataFrame]= {}


    @property  # Read Only Getter for self.dataframe
    def dataframes(self):
        return self.__dataframes


    def load_data(self):
        """
        This runs the process of fetching, parsing data, and storing it to self.data_frame.
        """
        try:
            # Download (fetch) the data; Assign Raw Data self.raw_data
            self._raw_dataframes = self._fetch_data()

            # Parse Each Downloaded Data
            parsed = {ticker : self._parse_data(self._raw_dataframes[ticker])
                      for ticker in self._raw_dataframes.keys()}

            # Assign Parsed Data to self.dataframes
            self.__dataframes = parsed

            # Clear raw downloaded data
            if self.has_data:
                self._raw_dataframes = None

            return self.__dataframes

        except Exception as e:
            logging.error(f"Error Loading Data: {e}")
            raise e


    @abstractmethod
    def _fetch_data(self) -> Dict[str, pd.DataFrame]:
        # Must be over-ridden, to populate the symbol dataframe
        return {}


    def _parse_data(self, data: pd.DataFrame) -> pd.DataFrame:
        '''
        Parse downloaded data into standard format for backtrader.
        '''
        columns = ['open', 'high', 'low', 'close', 'volume']
        dataframe = data.copy()
        dataframe.columns = dataframe.columns.str.lower()
        
        # Make sure the dataframe is not empty, and contains all necessary columns
        if dataframe.empty:
            logging.warning('Passed Data does not contain any data at all.')
            return None

        if not set(columns).issubset(dataframe.columns):
            logging.warning('Passed Data does not contain all the necessary columns.')
            return None
        
        try: 
            # Reorder columns into the desired format
            dataframe = dataframe[columns]
            bt_data = bt.feeds.PandasData(dataname=dataframe, **self.DATA_ARGS)

        except Exception as e:
            logging.error(f"Error parsing data: {e}")
            raise e
        
        return bt_data


    def _set_symbol(self, symbol: Union[str, List[str]]):
        
        if isinstance(symbol, str):
            return [symbol.upper()]
        
        elif isinstance(symbol, list):
            return [str_.upper() for str_ in symbol]
        
        else:
            error_message = f"Unsupported data type for symbol: {type(symbol)}"
            logging.warning(error_message)
            raise TypeError(error_message)


    def _set_resolution(self, resolution: str) -> str:
        resolutions = self.RESOLUTIONS
        default_resolution = "1d"

        # Default resolution to '1d' if the passed resolution is not recognized
        if resolution not in resolutions:
            warning_msg = f'Unsupported resolution: "{resolution}" is not recognized. Defaulting to "{default_resolution}".'
            logging.warning(warning_msg)

            resolution = default_resolution

        # Update the DATA_ARGS
        self.DATA_ARGS.update(
            timeframe=self.TIMEFRAMES[resolution], 
            compression=self.COMPRESSIONS[resolution]
        )

        # Return the resolution
        return resolution
          

    def _set_data_range(self, period_kwargs: dict = {}) -> tuple:
        """
        Set the data range based on the given period arguments, start date, and end date.

        Args:
            period_args (dict): Dictionary containing period information along with start_date and end_date.

        Returns:
            tuple: A tuple containing formatted start and end dates.
        """

        # Check if both start_date and end_date are provided in period_args
        if "start_date" in period_kwargs and "end_date" in period_kwargs:
            start_date = parse(period_kwargs["start_date"])
            end_date = parse(period_kwargs["end_date"])
        else:

            # Default start_date and end_date
            _default_start = '2010-01-01' \
                if (self.resolution in ['1d', '1w', '1M']) \
                    else '2023-08-01' 

            start_date = period_kwargs.get("start_date", _default_start)
            end_date = period_kwargs.get("end_date")

            # Check if start_date and end_date are valid datetime objects, otherwise use default values.
            if not isinstance(start_date, datetime):
                start_date = (
                    parse(start_date) if start_date else datetime.now() - timedelta(days=30)
                )

            if not isinstance(end_date, datetime):
                end_date = parse(end_date) if end_date else datetime.now()


            # Check for periods, instead of dates
            duration = {
                "seconds": period_kwargs.get("seconds", 0),
                "minutes": period_kwargs.get("minutes", 0),
                "hours": period_kwargs.get("hours", 0),
                "days": period_kwargs.get("days", 0),
                "weeks": period_kwargs.get("weeks", 0),
                "months": period_kwargs.get("months", 0),
                "years": period_kwargs.get("years", 0),
            }

            # Checks if the default duration has been updated by the passed period arguments
            if any(value > 0 for value in duration.values()):
                end_date = datetime.now()
                start_date = end_date - relativedelta(**duration) # Get the start date using timedelta and the specified duration / period

        return start_date.strftime("%Y-%m-%d"), end_date.strftime("%Y-%m-%d")

    @property
    def has_data(self):
        return self.dataframes


class YFDataloader(DataLoader):
    def __init__(
        self, symbol: str, resolution: str, **period_args
    ) -> None:
        super().__init__(symbol, resolution, **period_args)


    def _fetch_data(self) -> Dict[str, pd.DataFrame]:
        try:
            _data_dict = {}

            # Loop Through all symbols in the symbols list
            for symbol in self.symbols:
                data = yf.download(
                    symbol,
                    start=self.start_date,
                    end=self.end_date,
                    interval=self.resolution,
                )

                data.index = pd.to_datetime(data.index)

                if data.empty:
                    error_message = (
                        "WARNING: Fetch Data Unsuccesful. Object Dataframe did not recieve any data."
                        + " Ensure the symbol(s) are valid, and the start/end dates are allowed for that resolution."
                    )
                    logging.warning(error_message)
                    continue

                _data_dict[symbol] = data

        except Exception as e:
            logging.warning(f"Fetch Data Unsuccesful: {e}")
            raise e
        
        # Return dictionary of downloaded datas
        return _data_dict


if __name__ == "__main__":

    aapl = YFDataloader('aapl', '1d')
    aapl.load_data()

    print(aapl.dataframes)

    pass
