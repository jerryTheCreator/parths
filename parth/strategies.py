import backtrader as bt

from collections import deque
from typing import Dict

from .indicators import AtrTrailStop, Halftrend, HtfEma, HullSuite, StGrab
from .utils.tv_functions import na


class MultiAssetStrategy(bt.Strategy):
    lines = ('sl',)

    params = (
        ('parameters',  dict()),
        ('hyperparameters', dict()),
        ('symbol_list', []),
    )

    def __init__(self):
        # Group Data by Symbol; Each symbols have 6 datas (different timeframes for the different indicators)
        self.data_groups = dict()
        for index, symbol in enumerate(self.params.symbol_list):
            tf_subdata = []
            for sub_index in range(6):
                data_index = (index * 6) + sub_index
                tf_subdata.append(self.datas[data_index])

            self.data_groups[symbol] = tf_subdata

        # Generate and Store The Symbol Data (Variables, Indicators) for each symbols
        self.indicator_groups = dict() # Stores Indicators for each symbol
        self.orders = dict() # Stores the order instances for each symbol
        self.exit_orders = dict()
        self.trades = dict() # Stores the trade instances for each symbol
        self.trade_counts = dict()

        for symbol, data_group in self.data_groups.items():
            _dict : Dict[str, bt.Indicator] = dict()
            
            _dict['data_0'] = data_group[0] # Original candlestick datas
            
            # Indicators
            _dict['halftrend'] = Halftrend(data_group[1], self.params.parameters)
            _dict['ats'] = AtrTrailStop(data_group[2], self.params.parameters)
            _dict['stgrab'] = StGrab(data_group[3], self.params.parameters)
            _dict['htfema'] = HtfEma(data_group[4], self.params.parameters)
            _dict['hull_suite'] = HullSuite(data_group[5], self.params.parameters)

            # Variables
            _dict['pend_long'] = False
            _dict['window_cond_hull'] : deque = deque([], maxlen=500)
            _dict['window_cond_touch_line'] = deque([False, False], maxlen=2)
            _dict['sl'] = bt.LineNum(float('nan'))

            self.indicator_groups[symbol] = _dict
            self.orders[symbol] : bt.Order = None
            self.exit_orders[symbol] : bt.Order = None
            self.trades[symbol] : bt.Trade = None
            self.trade_counts[symbol] = 0

        # General attributes for Kelly's Criterion position sizing
        self._count_trades = 0
        self._count_wins = 0
        self._count_losses = 0
        self._avg_win = 0
        self._avg_loss = 0


    def log(self, _text, dt=None):
        dt = dt or self.datas[0].datetime.datetime(0)
        print(f'{dt.strftime("%Y-%m-%d %H:%M:%S")} : {_text}') 


    def next(self):
        # Iterate through the symbols
        for symbol, data in self.indicator_groups.items():
            bar = data['data_0'] # Fetch Bar Data
            stgrab, htfema, hull_suite, halftrend, ats = data['stgrab'], data['htfema'], data['hull_suite'], data['halftrend'], data['ats'] # Fetch Indicator Data
            
            # region ----- CONDITIONS
            # St Grab
            cond_above_st = bar.close[0] > stgrab.lines.ema_high[0]
            # cond_below_st = bar.close[0] < stgrab.lines.ema_low[0] # UNUSED

            # HTF EMAs
            cond_ema_long = (htfema.lines.ema_1[0] > htfema.lines.ema_2[0]) and (htfema.lines.ema_2[0] > htfema.lines.ema_3[0])

            # Hull Suite
            _hull_long = hull_suite.lines.hull[0] > hull_suite.lines.shull[0]
            data['window_cond_hull'].appendleft(_hull_long)
            cond_hull_long = any(data['window_cond_hull'])

            # Halftrend
            cond_ht_long = (not na(halftrend.lines.arrowUp[0])) and (halftrend.lines.trend[0] == 0) and (halftrend.lines.trend[-1] == 1)
            cond_ht_short = (not na(halftrend.lines.arrowDown[0])) and (halftrend.lines.trend[0] == 1) and (halftrend.lines.trend[-1] == 0)

            # ATR Trailing Stop
            # cond_ats_long = ats.lines.cond_ats_long[0] # UNUSED
            cond_ats_short = ats.lines.cond_ats_short[0]
            sl_line = ats.lines.xATRTrailingStop[0]
            
            cond_touch_line = (bar.high[0] >= sl_line) and (bar.low[0] <= sl_line)
            data['window_cond_touch_line'].append(cond_touch_line)

            if (data['window_cond_touch_line'][0]) and (not data['window_cond_touch_line'][1]):
                data['sl'][0] = sl_line - ((.45/100) * sl_line)
            else:
                data['sl'][0] = data['sl'][-1]
            # endregion

            # region ----- ENTRY
            condition_cancel = (cond_ht_short or cond_ats_short or (not cond_hull_long) or (not cond_ema_long))

            if (not data['pend_long']) and (cond_ht_long and cond_above_st) and (not condition_cancel): # and (not self.trades[symbol]) and (not condition_cancel) : # Halftrend Long Signal, while Price Above Halftrend, and Halftrend above ST_GRaB
                data['pend_long'] = True
                
                order_size = self.sizer_percent(bar.high[0]) # Calculate the order size
                self.orders[symbol] = self.buy(data=bar, exectype=bt.Order.Stop, price=bar.high[0], size=order_size)
                # self.log(f'{symbol} | buy-stop order sent : Price :({bar.high[0]}).')

            if data['pend_long'] and (self.trades[symbol] is None):
                # Cancel Pending Orders
                if condition_cancel:
                    # Cancel Buy Sequence If:
                    # - Short Signal from Halftrend
                    # - Current Price is below the ATR Line
                    # - No Buy Signal from Hull Suite in the last 500 bars
                    # - 4-hour EMA not in the right order, and MAPD is not within 4 and -4
                    data['pend_long'] = False

                    self.cancel(self.orders[symbol])
                    # self.log(f'<--- {symbol} | cancel buy-stop order sent.')     
                    # print('------ Reason: {}'.format(ternary(cond_ht_short, 'cond_ht_short', 
                    #                                   ternary(cond_ats_short, 'cond_ats_short', 
                    #                                           ternary(not cond_hull_long, 'not cond_hull_long', 
                    #                                                   ternary(not cond_ema_long, 'not cond_ema_long', 'Unknown'))))))   
            
            # endregion

            # region ----- EXIT
            elif (self.trades[symbol] is not None):
                data['pend_long'] = False
                
                # Set/Update SL:
                if self.exit_orders[symbol]: 
                    self.cancel(self.exit_orders[symbol])
                    self.exit_orders[symbol] = None  # clear the reference
                
                if cond_ats_short:
                    self.close(data=bar)
                    # self.log(f'<--- {symbol} | close buy signal sent : price below atr line --->')

                else:
                    # Set SL to the updated sl value
                    self.exit_orders[symbol] = self.close(data=bar, price=data['sl'][0], exectype=bt.Order.Stop) 
                    # self.log(f'<--- {symbol} | exit buy order sent/updated : trailing stop triggered --->')
            
            # endregion   


    # def notify_order(self, order):
    #     if order.status in [order.Submitted, order.Accepted]:
    #         return  # do nothing if order is still being processed

    #     if order.status in [order.Completed]:
    #         if order.isbuy():
    #             print('BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
    #                   (order.executed.price,
    #                    order.executed.value,
    #                    order.executed.comm))

    #             self.bar_executed = len(self)  # when was trade executed

    #         else:  # Sell
    #             print('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' %
    #                   (order.executed.price,
    #                    order.executed.value,
    #                    order.executed.comm))
    #             self.log('Exit Order triggered')

    #     elif order.status in [order.Canceled, order.Margin, order.Rejected]:
    #         print('Order Canceled/Margin/Rejected')

    #     self.order = None  # write down that there is no order pending


    def notify_trade(self, trade):
        symbol = trade.getdataname()

        if trade.justopened and trade.size > 0:
            self.orders[symbol] = None
            self.trades[symbol] = trade
            self.log(f'{symbol} | TRADE EXECUTED at {trade.price: .2f}, Order Size : {trade.size}')    
        
        if trade.isclosed or trade.size < 0:
            # Update Counters
            self._update_counters(trade)
            
            self.orders[symbol] = None
            self.trades[symbol] = None
            self.trade_counts[symbol] += 1
            self.log(f'TRADE CLOSED at {trade.price: .2f}')


    def stop(self):
        print('<<<<<----- SUMMARY ----->>>>>')
        print('Trades Completed : ', sum(list(self.trade_counts.values())))
        for symbol, count in self.trade_counts.items():
            print(symbol, ': ', count)

        
    def sizer_percent(self, price): 
        risk_percentage = self._kelly_percent()

        risk_amount = self.broker.get_cash() * risk_percentage
        position_size = risk_amount / price
        return position_size
    

    def _kelly_percent(self):
        '''
        Calculate the percentage of the maximum exposure to risk per trade, using Kelly's Criterion Percentage formula

        `Kelly % = W – [(1-W)/R]`

        Where,

        W = Winning probability
            The winning probability is defined as the total number of winning trades divided over the total number of trades

        R = Win/Loss ratio.
            The win/loss ratio is the average gain of winning trades divided over average loss of the negative trades.

        '''

        MINIMUM_TRADE_COUNT = self.params.hyperparameters.get('MINIMUM_TRADE_COUNT')
        DEFAULT_RISK_PERCENT = self.params.hyperparameters.get('DEFAULT_RISK_PERCENT')
        MAXIMUM_CAPITAL_EXPOSURE = self.params.hyperparameters.get('MAXIMUM_CAPITAL_EXPOSURE')

        # If total closed trades is less than 10, or 
        # Use the default fraction percentage 
        if self._count_trades < MINIMUM_TRADE_COUNT:
            return DEFAULT_RISK_PERCENT * .01
        
        W = self._count_wins / self._count_losses
        R = self._avg_win / self._avg_loss

        kellys = round(W - ((1 - W) / R), 2)

        return kellys * MAXIMUM_CAPITAL_EXPOSURE * 0.01


    def _update_counters(self, trade : bt.Trade):
        pnl = trade.pnl
        
        # Increment the Trade Count
        self._count_trades += 1
        
        # If in Profit
        if pnl > 0:
            self._count_wins += 1 
            self._avg_win = (((self._count_wins - 1) * self._avg_win) + pnl) / self._count_wins

        # If in Loss
        elif pnl < 0:
            self._count_losses += 1 
            self._avg_loss = (((self._count_losses - 1) * self._avg_loss) + abs(pnl)) / self._count_losses