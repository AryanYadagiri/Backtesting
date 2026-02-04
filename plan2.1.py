import talib as talib
import pandas_ta as ta
import yfinance as yf
from backtesting import Strategy, Backtest

dogecoin = yf.Ticker("RELIANCE.NS")
data = dogecoin.history(period="10y", interval="1d")
st1 = ta.supertrend(high=data["High"],low=data["Low"],close=data["Close"],length=10,multiplier=1)
st2 = ta.supertrend(high=data["High"],low=data["Low"],close=data["Close"],length=11,multiplier=2)
st3 = ta.supertrend(high=data["High"],low=data["Low"],close=data["Close"],length=12,multiplier=3)
# print(st1)
# print(st2)
# print(st3)
data["Supertrend1"] = st1["SUPERT_10_1"]
data["Supertrend2"] = st2["SUPERT_11_2"]
data["Supertrend3"] = st3["SUPERT_12_3"]
data["Supertrend_Signal1"] = st1["SUPERTd_10_1"]
data["Supertrend_Signal2"] = st2["SUPERTd_11_2"]
data["Supertrend_Signal3"] = st3["SUPERTd_12_3"]

class MyStrategy(Strategy):

    def get_supertrend1(self):
        st = self.data.Supertrend1
        return st

    def get_supertrend2(self):
        st = self.data.Supertrend2
        return st

    def get_supertrend3(self):
        st = self.data.Supertrend3
        return st

    def init(self):
        self.supertrend1 = self.I(self.get_supertrend1, name="supertrend1")
        self.supertrend2 = self.I(self.get_supertrend2, name="supertrend2")
        self.supertrend3 = self.I(self.get_supertrend3, name="supertrend3")
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, 14, name="atr")
    
    def calculate_position_size(self, a, b, entry_price):
        risk_amount = self.equity * 0.01

        risk_per_unit = a - b
        if risk_per_unit <= 0:
            return None

        raw_units = risk_amount / risk_per_unit

        max_units_by_cash = self.equity / entry_price
        units = int(min(raw_units, max_units_by_cash))

        if units < 1:
            return None

        return units

    def next(self): 
        if len(self.data) < 12:
            return
        close = self.data.Close[-1]
        prev_low = self.data.Low[-2]
        prev_atr = self.atr[-2]
        # exit1 = self.data.Supertrend_Signal1[-2]
        exit2 = self.data.Supertrend_Signal2[-2]
        exit3 = self.data.Supertrend_Signal3[-2]

        if self.position:
            if self.position.is_long:
                # if exit1 == -1 or exit2 == -1 or exit3 == -1:
                if exit2 == -1 or exit3 == -1:
                    self.position.close()
                    return
                elif self.position.pl_pct == 5:
                    sl = prev_low - prev_atr
                    risk = close - sl
                    units = self.calculate_position_size(close, sl, close)
                    if risk <= 0 or units is None:
                        return
                    if not (sl < close):
                        return
                    self.buy(size=0.20, sl=sl)
                    return
                elif self.position.pl_pct == 10:
                     sl = prev_low - prev_atr
                     risk = close - sl
                     units = self.calculate_position_size(close, sl, close)
                     if risk <= 0 or units is None:
                         return
                     if not (sl < close):
                         return
                     self.buy(size=0.20, sl=sl) 
                     return    
            return

       
        signal1 = self.data.Supertrend_Signal1[-2]
        signal2 = self.data.Supertrend_Signal2[-2]
        signal3 = self.data.Supertrend_Signal3[-2]
        

        if signal1 == 1 and signal2 == 1 and signal3 == 1:
            sl = prev_low - prev_atr
            risk = close - sl
            units = self.calculate_position_size(close, sl, close)
            if risk <= 0 or units is None:
                return
            if not (sl < close):
                return
            # tp = close + (risk * 2)
            self.buy(sl=sl, size=units)
            return

bt = Backtest(data, MyStrategy, cash=10000, commission=0.0005)
stats = bt.run()
print(stats)  
bt.plot()