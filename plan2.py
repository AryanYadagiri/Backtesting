import numpy as np
import talib as talib
import pandas_ta as ta
import yfinance as yf
from backtesting import Strategy, Backtest

dogecoin = yf.Ticker("TATASTEEL.NS")
data = dogecoin.history(period="10y", interval="1d")
st = ta.supertrend(high=data["High"],low=data["Low"],close=data["Close"],length=12,multiplier=3)
data["Supertrend"] = st["SUPERT_12_3"]
data["Supertrend_Signal"] = st["SUPERTd_12_3"]

class MyStrategy(Strategy):
    lookback = 10

    def get_supertrend(self):
        st = self.data.Supertrend
        return st
    
    def init(self):
        self.dema = self.I(talib.DEMA, self.data.Close, 200, name="dema")
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, 14, name="atr")
        self.adx = self.I(talib.ADX, self.data.High, self.data.Low, self.data.Close, 14, name="adx")

        self.supertrend = self.I(self.get_supertrend, name="supertrend")
    
    def cal_slope(self):
        if len(self.dema) < self.lookback:
            return 0  # or handle appropriately
        y = self.dema[-self.lookback:]
        x = np.arange(len(y))
        slope, _ = np.polyfit(x, y, 1)
        return slope
    
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
        if len(self.data) < 200:
            return
        exit = self.data.Supertrend_Signal[-2]
        if self.position:
            if self.position.is_long:
                if exit == -1:
                    self.position.close()
                    return
            # elif self.position.is_short:
            #     if exit == 1:
            #         self.position.close()
            #         return
            return

        close = self.data.Close[-1]
        prev_high = self.data.High[-2]
        prev_low = self.data.Low[-2]
        slope = self.cal_slope()
        adx = self.adx[-1]
        prev_atr = self.atr[-2]
        prev_dema = self.dema[-2]
        signal = self.data.Supertrend_Signal[-2]
        pre_signal = self.data.Supertrend_Signal[-3]

        if slope > 0 and prev_low > prev_dema and signal == 1:
            sl = prev_low - prev_atr
            risk = close - sl
            units = self.calculate_position_size(close, sl, close)
            if risk <= 0 or units is None:
                return
            # tp = close + (risk * 2)
            if not (sl < close):
                return
            self.buy(sl=sl, size=units)
            return
        
        if slope < 0 and prev_high < prev_dema and signal == -1:
            sl = prev_high + prev_atr
            risk = sl - close
            units = self.calculate_position_size(sl, close, close)

            if risk <= 0 or units is None:
                return
            if sl <= close:
                return

            self.sell(size=units, sl=sl)

bt = Backtest(data, MyStrategy, cash=10000, commission=0.0005)
stats = bt.run()
print(stats)  
bt.plot()