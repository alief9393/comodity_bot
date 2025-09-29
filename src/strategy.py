import pandas as pd
from scipy.signal import find_peaks
import config 

class TradingStrategy:
    def __init__(self):
        """
        Initializes the strategy with parameters from the config file.
        """
        self.ema_period = config.EMA_PERIOD
        self.rsi_period = config.RSI_PERIOD
        self.rsi_oversold = config.RSI_OVERSOLD_LEVEL
        self.swing_lookback = config.SWING_LOOKBACK_CANDLES

    def calculate_indicators(self, df_h4, df_h1):
        """
        Calculates all necessary indicators and adds them to the dataframes.
        """
        df_h4[f'EMA_{self.ema_period}'] = df_h4['close'].ewm(span=self.ema_period, adjust=False).mean()

        delta = df_h1['close'].diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        avg_gain = gain.rolling(window=self.rsi_period).mean()
        avg_loss = loss.rolling(window=self.rsi_period).mean()
        rs = avg_gain / avg_loss
        df_h1[f'RSI_{self.rsi_period}'] = 100 - (100 / (1 + rs))
        
        return df_h4, df_h1

    def _find_swing_points(self, data):
        """
        Private helper function to find swing points. (Copied from notebook 03)
        """
        swing_highs_indices, _ = find_peaks(data['high'], distance=self.swing_lookback)
        swing_lows_indices, _ = find_peaks(-data['low'], distance=self.swing_lookback)

        if len(swing_lows_indices) < 2 or len(swing_highs_indices) == 0:
            return None, None

        last_swing_high_time = data.index[swing_highs_indices[-1]]
        last_swing_low_time = data.index[swing_lows_indices[-1]]

        if last_swing_low_time < last_swing_high_time:
            return last_swing_low_time, last_swing_high_time
        else:
            prev_swing_low_time = data.index[swing_lows_indices[-2]]
            relevant_highs = swing_highs_indices[data.index[swing_highs_indices] > prev_swing_low_time]
            if len(relevant_highs) > 0:
                first_relevant_high_time = data.index[relevant_highs[0]]
                return prev_swing_low_time, first_relevant_high_time
        return None, None

    def check_for_signal(self, df_h4, df_h1):
        """
        The main "brain" function to check all conditions for a buy signal.
        """
        print("\n--- Starting New Signal Check ---")
        
        last_h4 = df_h4.iloc[-1]
        is_uptrend = last_h4['close'] > last_h4[f'EMA_{self.ema_period}']
        
        if not is_uptrend:
            print(f"Condition 1 FAILED: H4 Close ({last_h4['close']:.3f}) is not above EMA ({last_h4[f'EMA_{self.ema_period}']:.3f}).")
            return None

        print("Condition 1 PASSED: H4 trend is up.")

        last_low_time, last_high_time = self._find_swing_points(df_h4)
        
        if not (last_low_time and last_high_time):
            print("Condition 2 FAILED: Could not identify a valid swing structure.")
            return None

        swing_low_price = df_h4.loc[last_low_time]['low']
        swing_high_price = df_h4.loc[last_high_time]['high']
        price_range = swing_high_price - swing_low_price

        fibo_382 = swing_high_price - (price_range * 0.382)
        fibo_618 = swing_high_price - (price_range * 0.618)

        is_in_zone = fibo_618 <= last_h4['close'] <= fibo_382

        if not is_in_zone:
            print(f"Condition 2 FAILED: Price ({last_h4['close']:.3f}) is not in the Golden Zone ({fibo_618:.3f} - {fibo_382:.3f}).")
            return None
        
        print(f"Condition 2 PASSED: Price is in the Golden Zone.")

        last_h1 = df_h1.iloc[-1]
        prev_h1 = df_h1.iloc[-2]
        rsi_col = f'RSI_{self.rsi_period}'
        
        rsi_crossed_up = prev_h1[rsi_col] < self.rsi_oversold and last_h1[rsi_col] >= self.rsi_oversold
        
        if not rsi_crossed_up:
            print(f"Condition 3 FAILED: H1 RSI ({last_h1[rsi_col]:.2f}) did not just cross above {self.rsi_oversold}.")
            return None
        
        print(f"Condition 3 PASSED: H1 RSI crossed up through {self.rsi_oversold}.")

        print("\n*** ALL CONDITIONS MET! ***")
        
        stop_loss = swing_low_price
        take_profit = swing_high_price + (price_range * 0.618)

        signal_details = {
            'symbol': config.SYMBOL,
            'entry_price': last_h1['close'],
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'reason': 'EMA Trend + Fibo Retracement + RSI Crossover'
        }
        
        return signal_details