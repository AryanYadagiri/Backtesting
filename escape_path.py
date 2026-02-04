import numpy as np
import talib as talib
import yfinance as yf
from backtesting import Strategy, Backtest

dogecoin = yf.Ticker("DOGE-USD")
data = dogecoin.history(period="1y", interval="1h")

class MyStrategy(Strategy):
    lookback = 20
    def init(self):
        self.rsi = self.I(talib.RSI, self.data.Close, 40, name="rsi_40")
        self.sma = self.I(talib.SMA, self.data.Close, 40, name="sma_40")
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, 14)
    
    def sma_slope(self):
        if len(self.sma) < self.lookback:
            return 0  # or handle appropriately
        y = self.sma[-self.lookback:]
        x = np.arange(len(y))
        slope, _ = np.polyfit(x, y, 1)
        return slope
    
    def calculate_position_size(self, entry_price, stop_loss_price):
        account_value = self.equity
        risk_amount = account_value * 0.01

        risk_per_unit = entry_price - stop_loss_price
        if risk_per_unit <= 0:
            return None

        raw_units = risk_amount / risk_per_unit

        max_units_by_cash = self.equity / entry_price
        units = int(min(raw_units, max_units_by_cash))

        if units < 1:
            return None

        return units

    def next(self): 
        if len(self.data) < 40:
            return

        close = self.data.Close[-1]
        open_ = self.data.Open[-1] # Use open_ to avoid shadowing the built-in open()
        high = self.data.High[-1]
        low = self.data.Low[-1]
        sma = self.sma[-1]
        rsi = self.rsi[-1]
        atr = self.atr[-1]
        prev_high = self.data.High[-2]
        prev_low = self.data.Low[-2]
        prev_sma = self.sma[-2]
        slope = self.sma_slope()

        # if slope > 0 and sma <= high and sma >= low and rsi >= 50 and rsi <= 70:
        if slope > 0 and  prev_low <= prev_sma <= prev_high and rsi > 55:
            # sl_chatgpt = close - 1.5 * atr
            sl = low - atr
            risk = close - sl
            units = self.calculate_position_size(close, sl)
            if risk <= 0 or units is None:
                return
            # tp_chatgpt = close + 3.0 * atr
            tp = close + (risk * 2)
            self.buy(sl=sl, tp=tp, size=units)

bt = Backtest(data, MyStrategy, cash=10000, commission=0.005)
stats = bt.run()
print(stats)  
bt.plot()