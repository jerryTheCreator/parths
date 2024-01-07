import math
import backtrader as bt
import backtrader.indicators as btind
from typing import Dict

from .utils.tv_functions import na, nz, ternary

class StGrab(bt.Indicator):
    lines = ('ema_high', 'ema_low')
    params = ( 
        ('period', 34),
    )
    plotinfo = {
        'plot' : True,
        'subplot' : False,
        'plotname' : 'stgrab',
        'plotabove' : False, 
        'plotyticks' : []
    }
    plotlines = dict(
        ema_high=dict(marker='', markersize=0.0, color='black', ls='none',),
        ema_low=dict(marker='', markersize=0.0, color='black', ls='none',),
    )
    
    def __init__(self, params : Dict):
        # Update Parameters
        self.params.period = params.get('ST_GRAB_PERIOD')

        self.lines.ema_high = btind.EMA(self.data.high, period=self.params.period)
        self.lines.ema_low = btind.EMA(self.data.low, period=self.params.period)


class HtfEma(bt.Indicator):
    lines = ('ema_1', 'ema_2', 'ema_3')
    params = ( 
        ('period_1', 21),
        ('period_2', 50),
        ('period_3', 200),
    )
    plotinfo = {
        'plot' : False,
        'subplot' : False,
        'plotname' : 'htf_ema',
        'plotabove' : False, 
        'plotyticks' : []
    }
    plotlines = dict(
        ema_1=dict(marker='', markersize=0.0, color='black', ls='none',),
        ema_2=dict(marker='', markersize=0.0, color='black', ls='none',),
        ema_3=dict(marker='', markersize=0.0, color='black', ls='none',),
    )

    def __init__(self, params : Dict):
        # Update Parameters
        self.params.period_1 = params.get('EMA_LENGTH_1')
        self.params.period_2 = params.get('EMA_LENGTH_2')
        self.params.period_3 = params.get('EMA_LENGTH_3')

        self.lines.ema_1 = btind.EMA(self.data.close, period=self.params.period_1)
        self.lines.ema_2 = btind.EMA(self.data.close, period=self.params.period_2)
        self.lines.ema_3 = btind.EMA(self.data.close, period=self.params.period_3)
     

class HullSuite(bt.Indicator):
    lines = ('mhull', 'hull', 'shull')
    params = ( 
        ('source', 'close'), 
        ('mode', 'hma'),
        ('length', 55),
    )
    plotinfo = {
        'plot' : False,
        'subplot' : False,
        'plotname' : 'hull_suite',
        'plotabove' : False, 
        'plotyticks' : []
    }
    plotlines = dict(
        mhull=dict(marker='', markersize=0.0, color='black', ls='none',),
        hull=dict(marker='', markersize=0.0, color='black', ls='none',),
        shull=dict(marker='', markersize=0.0, color='black', ls='none',),
    )
    
    def __init__(self, params : Dict):
        # Update Parameters
        self.params.source = params.get('HULL_SRC').lower()
        self.params.mode = params.get('HULL_MODESWITCH').lower()
        self.params.length = params.get('HULL_LENGTH')
        
        source = self.data.open if self.params.source == 'open' else \
                self.data.high if self.params.source == 'high' else \
                self.data.low if self.params.source == 'low' else \
                    self.data.close
        thma_len = int(self.params.length / 2)

        hma = btind.HMA(source, period=self.params.length)
        ehma = btind.EMA((2 * btind.EMA(period=int(self.params.length / 2))) - btind.EMA(period=int(self.params.length)), period=math.floor(math.sqrt(self.params.length)))
        thma = btind.WMA(btind.WMA(source, period=int(thma_len / 3)) * 3 - btind.WMA(source, period=int(thma_len / 2)) - btind.WMA(source, period=thma_len), period=thma_len)

        self.lines.mhull = ehma if self.params.mode == 'ehma' else thma if self.params.mode == 'thma' else hma
    
    def next(self):
        self.lines.hull[0] = self.lines.mhull[0]
        self.lines.shull[0] = self.lines.mhull[-2]
   

class AtrTrailStop(bt.Indicator):
    lines = ('xATRTrailingStop', 'pos', 'xATR', 'cond_ats_long', 'cond_ats_short', 'test')
    params = ( 
        ('period', 5), 
        ('multiplier', 3.5),
    )
    plotinfo = {
        'plot' : True,
        'subplot' : False,
        'plotname' : 'ATR_TS',
        'plotabove' : False, 
        'plotyticks' : []
    }
    plotlines = dict(
        xATRTrailingStop=dict(marker='', markersize=0.0, color='black', ls='none',),
        pos=dict(marker='', markersize=0.0, color='black', ls='none',),
        xATR=dict(marker='', markersize=0.0, color='black', ls='none',),
        cond_ats_long=dict(marker='', markersize=0.0, color='black', ls='none',),
        cond_ats_short=dict(marker='', markersize=0.0, color='black', ls='none',),
        test=dict(marker='', markersize=0.0, color='black', ls='none',),
    )
    def __init__(self, params: Dict):
        # Update Parameters
        self.params.period = params.get('NATRPERIOD')
        self.params.multiplier = params.get('NATRMULTIP')

        self.lines.xATR = btind.ATR(self.data, period=self.params.period)
        self.lines.xATRTrailingStop = bt.LineNum(float('nan'))
        self.lines.pos = bt.LineNum(float('nan'))

    def next(self):
        bar = self.data
        nLoss = self.params.multiplier * self.lines.xATR[0]
        self.lines.xATRTrailingStop[0] = float('nan')
        self.lines.pos[0] = float('nan')

        iff_1 = ternary(bar.close[0] > nz(self.lines.xATRTrailingStop[-1], 0), 
                        bar.close[0] - nLoss, 
                        bar.close[0] + nLoss)
        
        iff_2 = ternary((bar.close[0] < nz(self.lines.xATRTrailingStop[-1], 0)) and (bar.close[-1] < nz(self.lines.xATRTrailingStop[-1], 0)), 
                        min(nz(self.lines.xATRTrailingStop[-1]), bar.close[0] + nLoss), 
                        iff_1)

        self.lines.xATRTrailingStop[0] = ternary((bar.close[0] > nz(self.lines.xATRTrailingStop[-1], 0)) and (bar.close[-1] > nz(self.lines.xATRTrailingStop[-1], 0)), 
                                                 max(nz(self.lines.xATRTrailingStop[-1]), bar.close[0] - nLoss), 
                                                 iff_2)

        iff_3 = ternary((bar.close[-1] > nz(self.lines.xATRTrailingStop[-1], 0)) and (bar.close[0] < nz(self.lines.xATRTrailingStop[-1], 0)), 
                        -1, 
                        nz(self.lines.pos[-1], 0))

        self.lines.pos[0] = ternary((bar.close[-1] < nz(self.lines.xATRTrailingStop[-1], 0)) and (bar.close[0] > nz(self.lines.xATRTrailingStop[-1], 0)), 
                                    1, 
                                    iff_3)

        self.lines.cond_ats_long[0] = bar.close[0] > self.lines.xATRTrailingStop[0] # self.lines.pos[0] == 1
        self.lines.cond_ats_short[0] = bar.close[0] < self.lines.xATRTrailingStop[0] # self.lines.pos[0] == -1

        self.lines.test[0] = ternary(self.lines.cond_ats_long[0], 1, -1)


class Halftrend(bt.Indicator):
    lines = ('atr', 'trend', 'nextTrend', 'maxLowPrice', 'minHighPrice', 'up', 'down', 'ht', 'highPrice', 'lowPrice', 'highma', 'lowma', 'arrowUp', 'arrowDown', 'atrHigh', 'atrLow')
    params = ( 
        ('amplitude', 2), 
        ('deviation', 2),
    )
    plotinfo = {
        'plot' : True,
        'subplot' : False,
        'plotname' : 'halftrend',
        'plotabove' : True, 
        'plotmargin' : 0.1
    }
    plotlines = dict(
        ht=dict(marker='', markersize=0.0, color='purple', ls='--',),
        atr=dict(marker='', markersize=0.0, color='black', ls='none',),
        trend=dict(marker='', markersize=0.0, color='black', ls='none',),
        nextTrend=dict(marker='', markersize=0.0, color='black', ls='none',),
        maxLowPrice=dict(marker='', markersize=0.0, color='black', ls='none',),
        minHighPrice=dict(marker='', markersize=0.0, color='black', ls='none',),
        up=dict(marker='', markersize=0.0, color='black', ls='none',),
        down=dict(marker='', markersize=0.0, color='black', ls='none',),
        highPrice=dict(marker='', markersize=0.0, color='black', ls='none',),
        lowPrice=dict(marker='', markersize=0.0, color='black', ls='none',),
        highma=dict(marker='', markersize=0.0, color='black', ls='none',),
        lowma=dict(marker='', markersize=0.0, color='black', ls='none',),
        arrowUp=dict(marker='', markersize=0.0, color='black', ls='none',),
        arrowDown=dict(marker='', markersize=0.0, color='black', ls='none',),
        atrHigh=dict(marker='', markersize=0.0, color='black', ls='none',),
        atrLow=dict(marker='', markersize=0.0, color='black', ls='none',),
    )

    def __init__(self, params : Dict):
        # Update Parameters
        self.params.amplitude = params.get('AMPLITUDE')
        self.params.deviation = params.get('CHANNELDEVIATION')
        
        self.lines.atr = btind.ATR(self.data, period=100) / 2
    
        self.lines.highPrice = btind.Highest(self.data.high, period=self.params.amplitude)
        self.lines.lowPrice = btind.Lowest(self.data.low, period=self.params.amplitude)
        self.lines.highma = btind.SMA(self.data.high, period=self.params.amplitude)
        self.lines.lowma = btind.SMA(self.data.low, period=self.params.amplitude)

        self.lines.arrowUp =  bt.LineNum(float('nan'))
        self.lines.arrowDown = bt.LineNum(float('nan'))

    def start(self):
        self.lines.arrowUp[0] =  math.nan
        self.lines.arrowDown[0] = math.nan

        self.lines.trend[0] = 0
        self.lines.nextTrend[0] = 0
        self.lines.up[0] = 0
        self.lines.down[0] = 0
        self.lines.maxLowPrice[0] = nz(self.data.low[0], self.data.low[-1])
        self.lines.minHighPrice[0] = nz(self.data.high[0], self.data.high[-1])
        
    def next(self):
        dev = self.params.deviation * self.lines.atr[0]
        atrHigh = 0.0
        atrLow = 0.0

        self.lines.arrowUp[0] =  math.nan
        self.lines.arrowDown[0] = math.nan

        self.lines.trend[0] = self.lines.trend[-1]
        self.lines.nextTrend[0] = self.lines.nextTrend[-1]
        self.lines.up[0] = self.lines.up[-1]
        self.lines.down[0] = self.lines.down[-1]
        self.lines.maxLowPrice[0] = self.lines.maxLowPrice[-1]
        self.lines.minHighPrice[0] = self.lines.minHighPrice[-1]

        if self.lines.nextTrend[0] == 1:
            self.lines.maxLowPrice[0] = max(self.lines.lowPrice[0], self.lines.maxLowPrice[0])

            if self.lines.highma[0] < self.lines.maxLowPrice[0] and self.data.close[0] < nz(self.data.low[-1], self.data.low[0]):
                self.lines.trend[0] = 1
                self.lines.nextTrend[0] = 0
                self.lines.minHighPrice[0] = self.lines.highPrice[0]
        else:
            self.lines.minHighPrice[0] = min(self.lines.highPrice[0], self.lines.minHighPrice[0])
            if self.lines.lowma[0] > self.lines.minHighPrice[0] and self.data.close[0] > nz(self.data.high[-1], self.data.high[0]):
                self.lines.trend[0] = 0
                self.lines.nextTrend[0] = 1
                self.lines.maxLowPrice[0] = self.lines.lowPrice[0]

        if self.lines.trend[0] == 0:
            if not na(self.lines.trend[-1]) and self.lines.trend[-1] != 0:
                self.lines.up[0] = ternary(na(self.lines.down[-1]), self.lines.down[0], self.lines.down[-1])
                self.lines.arrowUp[0] = self.lines.up[0] - self.lines.atr[0]
            else:
                self.lines.up[0] = ternary(na(self.lines.up[-1]) , self.lines.maxLowPrice[0] , max(self.lines.maxLowPrice[0], self.lines.up[-1]))
            atrHigh = self.lines.up[0] + dev
            atrLow = self.lines.up[0] - dev
        else:
            if not na(self.lines.trend[-1]) and self.lines.trend[-1] != 1:
                self.lines.down[0] = ternary(na(self.lines.up[-1]), self.lines.up[0], self.lines.up[-1])
                self.lines.arrowDown[0] = self.lines.down[0] + self.lines.atr[0]
            else:
                self.lines.down[0] = ternary( na(self.lines.down[-1]), self.lines.minHighPrice[0], min(self.lines.minHighPrice[0], self.lines.down[-1]))
            atrHigh = self.lines.down[0] + dev
            atrLow = self.lines.down[0] - dev

        self.lines.ht[0] = ternary(self.lines.trend[0] == 0, self.lines.up[0], self.lines.down[0])
        self.lines.atrHigh[0] = atrHigh
        self.lines.atrLow[0] = atrLow