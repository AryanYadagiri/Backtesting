import numpy as np
import talib as talib
import pandas_ta as ta
import yfinance as yf
from backtesting import Strategy, Backtest

dogecoin = yf.Ticker("ITC.NS")
data = dogecoin.history(period="1mo", interval="5m")


class MyStrategy(Strategy):
    lookback = 10

    def get_supertrend(self):
        st = self.data.Supertrend
        return st
    
    def init(self):
        self.ema = self.I(talib.EMA, self.data.Close, 20, name="ema")
        self.atr = self.I(talib.ATR, self.data.High, self.data.Low, self.data.Close, 14, name="atr")
        self.stoch_k, self.stoch_d = self.I(
        talib.STOCHRSI,
        self.data.Close,
        14,  # timeperiod
        14,  # fastk_period
        3,   # fastd_period
        0    # fastd_matype (SMA)
        )
        print(self.stoch_d)
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
        if len(self.data) < 25 or len(self.stoch_d) < 5:
            return

        close = self.data.Close[-1]
        ema = self.ema[-1]

        # === EXIT: mean reversion to EMA ===
        if self.position:
            if self.position.is_long and close >= ema:
                self.position.close()
            elif self.position.is_short and close <= ema:
                self.position.close()
            return

        prev_high = self.data.High[-2]
        prev_low = self.data.Low[-2]
        prev_atr = self.atr[-2]

        d4 = self.stoch_d[-4]
        d3 = self.stoch_d[-3]
        d2 = self.stoch_d[-2]

        # === LONG: oversold mean reversion ===
        if d4 < 20 and d3 < 20 and d2 < 20 and close < ema:
            sl = prev_low - (prev_atr * 1.5)
            units = self.calculate_position_size(close, sl, close)
            if units:
                self.buy(size=units, sl=sl)

        # === SHORT: overbought mean reversion ===
        elif d4 > 80 and d3 > 80 and d2 > 80 and close > ema:
            sl = prev_high + (prev_atr * 1.5)
            units = self.calculate_position_size(sl, close, close)
            if units:
                self.sell(size=units, sl=sl)

            if len(self.data) < 25:
                return
            high = self.data.High[-1]
            low = self.data.Low[-1]
            ema = self.ema[-1]
            if self.position:
                if self.position.is_long:
                    if ema <= high or ema >= low:
                        self.position.close()
                        return
                elif self.position.is_short:
                    if ema <= high or ema >= low:
                        self.position.close()
                        return
                return

            close = self.data.Close[-1]
            prev_high = self.data.High[-2]
            prev_low = self.data.Low[-2]
            check_stochrsi = self.stoch_d[-4]
            signal_stochrsi = self.stoch_d[-3]
            prev_stochrsi = self.stoch_d[-2]
            prev_atr = self.atr[-2]

            if signal_stochrsi < 20 and prev_stochrsi < 20 and high < ema:
                sl = prev_low - (prev_atr * 2)
                risk = close - sl
                units = self.calculate_position_size(close, sl, close)
                if risk <= 0 or units is None:
                    return
                # tp = close + (risk * 2)
                if not (sl < close):
                    return
                self.buy(sl=sl, size=units)
                return
            
            if signal_stochrsi > 80 and prev_stochrsi > 80 and low > ema:
                sl = prev_high + (prev_atr * 2)
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