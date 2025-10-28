# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these imports ---
import numpy as np
import pandas as pd
from pandas import DataFrame

from freqtrade.strategy import IStrategy, merge_informative_pair
import talib.abstract as ta


class level_one(IStrategy):
    INTERFACE_VERSION = 3
    can_short: bool = False

    minimal_roi = {"60": 0.01, "30": 0.02, "0": 0.04}
    stoploss = -0.10
    trailing_stop = False

    timeframe = "15m"
    informative_timeframe = '1h'
    process_only_new_candles = True
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    startup_candle_count: int = 200

    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    def informative_pairs(self):
        return []

    def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:

        # --- Main Timeframe Indicators ---
        dataframe["rsi"] = ta.RSI(dataframe)
        dataframe['rsi_ema'] = ta.EMA(dataframe['rsi'], timeperiod=21)

        stoch = ta.STOCHF(dataframe, fastk_period=21)
        dataframe["fastk"] = stoch["fastk"]
        dataframe["fastd"] = stoch["fastd"]
        dataframe['stoch_condition'] = np.where(
            dataframe['fastk'] > dataframe['fastd'], 1,
            np.where(dataframe['fastk'] < dataframe['fastd'], -1, 0)
        )

        # Ichimoku
        tenkan_high = dataframe['high'].rolling(9).max()
        tenkan_low = dataframe['low'].rolling(9).min()
        dataframe['tenkan'] = (tenkan_high + tenkan_low) / 2

        kijun_high = dataframe['high'].rolling(26).max()
        kijun_low = dataframe['low'].rolling(26).min()
        dataframe['kijun'] = (kijun_high + kijun_low) / 2


        # MACD
        macd_df = ta.MACD(dataframe, fastperiod=12, slowperiod=26, signalperiod=9)
        dataframe['macd'] = macd_df['macd']
        dataframe['macdsignal'] = macd_df['macdsignal']
        dataframe['macd_condition'] = np.where(
            dataframe['macd'] > dataframe['macdsignal'], 1,
            np.where(dataframe['macd'] < dataframe['macdsignal'], -1, 0)
        )

        # ADX
        dataframe['adx'] = ta.ADX(dataframe, timeperiod=14)
        dataframe['plus_di'] = ta.PLUS_DI(dataframe, timeperiod=14)
        dataframe['minus_di'] = ta.MINUS_DI(dataframe, timeperiod=14)
        dataframe['adx_condition'] = np.where(
            (dataframe['adx'] > 25) & (dataframe['plus_di'] > dataframe['minus_di']), 1,
            np.where((dataframe['adx'] > 25) & (dataframe['plus_di'] < dataframe['minus_di']), -1, 0)
        )

        # Drop rows with NaN from merge/shift
        dataframe.dropna(inplace=True)

        return dataframe

    def populate_entry_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['enter_long'] = 0
        return dataframe

    def populate_exit_trend(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        dataframe['exit_long'] = 0
        return dataframe