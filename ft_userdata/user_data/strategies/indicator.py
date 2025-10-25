# pragma pylint: disable=missing-docstring, invalid-name, pointless-string-statement
# flake8: noqa: F401
# isort: skip_file
# --- Do not remove these imports ---
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from pandas import DataFrame
from typing import Optional, Union

from freqtrade.strategy import (
    IStrategy,
    Trade,
    Order,
    PairLocks,
    informative,  # @informative decorator
    # Hyperopt Parameters
    BooleanParameter,
    CategoricalParameter,
    DecimalParameter,
    IntParameter,
    RealParameter,
    # timeframe helpers
    timeframe_to_minutes,
    timeframe_to_next_date,
    timeframe_to_prev_date,
    # Strategy helper functions
    merge_informative_pair,
    stoploss_from_absolute,
    stoploss_from_open,
)

# --------------------------------
# Add your lib to import here
import talib.abstract as ta
from technical import qtpylib


# This class is a sample. Feel free to customize it.
class indicator(IStrategy):
    """
    This is a sample strategy to inspire you.
    More information in https://www.freqtrade.io/en/latest/strategy-customization/

    You can:
        :return: a Dataframe with all mandatory indicators for the strategies
    - Rename the class name (Do not forget to update class_name)
    - Add any methods you want to build your strategy
    - Add any lib you need to build your strategy

    You must keep:
    - the lib in the section "Do not remove these libs"
    - the methods: populate_indicators, populate_entry_trend, populate_exit_trend
    You should keep:
    - timeframe, minimal_roi, stoploss, trailing_*
    """

    # Strategy interface version - allow new iterations of the strategy interface.
    # Check the documentation or the Sample strategy to get the latest version.
    INTERFACE_VERSION = 3

    # Can this strategy go short?
    can_short: bool = False

    # Minimal ROI designed for the strategy.
    # This attribute will be overridden if the config file contains "minimal_roi".
    minimal_roi = {
        # "120": 0.0,  # exit after 120 minutes at break even
        "60": 0.01,
        "30": 0.02,
        "0": 0.04,
    }

    # Optimal stoploss designed for the strategy.
    # This attribute will be overridden if the config file contains "stoploss".
    stoploss = -0.10

    # Trailing stoploss
    trailing_stop = False
    # trailing_only_offset_is_reached = False
    # trailing_stop_positive = 0.01
    # trailing_stop_positive_offset = 0.0  # Disabled / not configured

    # Optimal timeframe for the strategy.
    timeframe = "15m"
    informative_timeframe = '1h'

    # Run "populate_indicators()" only for new candle.
    process_only_new_candles = True

    # These values can be overridden in the config.
    use_exit_signal = True
    exit_profit_only = False
    ignore_roi_if_entry_signal = False

    # Number of candles the strategy requires before producing valid signals
    startup_candle_count: int = 200

    # Optional order type mapping.
    order_types = {
        "entry": "limit",
        "exit": "limit",
        "stoploss": "market",
        "stoploss_on_exchange": False,
    }

    def informative_pairs(self):
        """
        Define additional, informative pair/interval combinations to be cached from the exchange.
        These pair/interval combinations are non-tradeable, unless they are part
        of the whitelist as well.
        For more information, please consult the documentation
        :return: List of tuples in the format (pair, interval)
            Sample: return [("PAXG/USDT", "5m"),
                            ("BTC/USDT", "15m"),
                            ]
        """
        pairs = self.dp.current_whitelist()
        informative_pairs = [(pair, self.informative_timeframe) for pair in pairs]
        return informative_pairs

def populate_indicators(self, dataframe: DataFrame, metadata: dict) -> DataFrame:
        """
        Adds requested TA indicators to the given DataFrame.
        :param dataframe: Dataframe with data from the exchange
        :param metadata: Additional information, like the currently traded pair
        :return: Dataframe with all mandatory indicators for the strategies
        """

        # --- 1h Informative Timeframe Indicators ---
        informative_1h = self.dp.get_pair_dataframe(pair=metadata['pair'], timeframe=self.informative_timeframe)

        # Condition 1: RSI vs. 21 EMA on 1h
        informative_1h["rsi"] = ta.RSI(informative_1h)
        informative_1h['rsi_ema'] = ta.EMA(informative_1h['rsi'], timeperiod=21)
        informative_1h['rsi_condition'] = np.where(informative_1h['rsi'] > informative_1h['rsi_ema'], 1,  # Buy
                                                   np.where(informative_1h['rsi'] < informative_1h['rsi_ema'], -1, 0))  # Sell, Equal

        # Condition 2: Stochastic Oscillator (length 21) on 1h
        stoch_fast_1h = ta.STOCHF(informative_1h, fastk_period=21)
        informative_1h["fastk"] = stoch_fast_1h["fastk"]
        informative_1h["fastd"] = stoch_fast_1h["fastd"]
        informative_1h['stoch_condition'] = np.where(informative_1h['fastk'] > informative_1h['fastd'], 1,  # Buy
                                                     np.where(informative_1h['fastk'] < informative_1h['fastd'], -1, 0))  # Sell, Equal

        # Conditions 3 & 4: Ichimoku Cloud on 1h
        tenkan_high = informative_1h['high'].rolling(window=9).max()
        tenkan_low = informative_1h['low'].rolling(window=9).min()
        informative_1h['tenkan'] = (tenkan_high + tenkan_low) / 2

        kijun_high = informative_1h['high'].rolling(window=26).max()
        kijun_low = informative_1h['low'].rolling(window=26).min()
        informative_1h['kijun'] = (kijun_high + kijun_low) / 2

        informative_1h['senkou_a'] = ((informative_1h['tenkan'] + informative_1h['kijun']) / 2).shift(periods=26)
        senkou_high = informative_1h['high'].rolling(window=52).max()
        senkou_low = informative_1h['low'].rolling(window=52).min()
        informative_1h['senkou_b'] = ((senkou_high + senkou_low) / 2).shift(periods=26)

        cloud_top = informative_1h[['senkou_a', 'senkou_b']].max(axis=1)
        cloud_bottom = informative_1h[['senkou_a', 'senkou_b']].min(axis=1)
        informative_1h['cloud_condition'] = np.where(informative_1h['close'] > cloud_top, 1,  # Buy
                                                     np.where(informative_1h['close'] < cloud_bottom, -1, 0))  # Sell, Equal/Inside

        informative_1h['line_condition'] = np.where(informative_1h['tenkan'] > informative_1h['kijun'], 1,  # Buy
                                                    np.where(informative_1h['tenkan'] < informative_1h['kijun'], -1, 0))  # Sell, Equal

        # Merge 1h indicators into the main 15m dataframe
        dataframe = merge_informative_pair(dataframe, informative_1h, self.timeframe, self.informative_timeframe, ffill=True)

        # --- 15m Main Timeframe Indicators ---
        # Condition 1: RSI vs. 21 EMA on 15m
        dataframe["rsi"] = ta.RSI(dataframe)
        dataframe['rsi_ema'] = ta.EMA(dataframe['rsi'], timeperiod=21)
        dataframe['rsi_condition'] = np.where(dataframe['rsi'] > dataframe['rsi_ema'], 1,  # Buy
                                              np.where(dataframe['rsi'] < dataframe['rsi_ema'], -1, 0))  # Sell, Equal

        # Condition 2: Stochastic Oscillator (length 21) on 15m
        stoch_fast = ta.STOCHF(dataframe, fastk_period=21)
        dataframe["fastk"] = stoch_fast["fastk"]
        dataframe["fastd"] = stoch_fast["fastd"]
        dataframe['stoch_condition'] = np.where(dataframe['fastk'] > dataframe['fastd'], 1,  # Buy
                                                np.where(dataframe['fastk'] < dataframe['fastd'], -1, 0))  # Sell, Equal

        # Conditions 3 & 4: Ichimoku Cloud on 15m
        tenkan_high = dataframe['high'].rolling(window=9).max()
        tenkan_low = dataframe['low'].rolling(window=9).min()
        dataframe['tenkan'] = (tenkan_high + tenkan_low) / 2

        kijun_high = dataframe['high'].rolling(window=26).max()
        kijun_low = dataframe['low'].rolling(window=26).min()
        dataframe['kijun'] = (kijun_high + kijun_low) / 2

        dataframe['senkou_a'] = ((dataframe['tenkan'] + dataframe['kijun']) / 2).shift(periods=26)
        senkou_high = dataframe['high'].rolling(window=52).max()
        senkou_low = dataframe['low'].rolling(window=52).min()
        dataframe['senkou_b'] = ((senkou_high + senkou_low) / 2).shift(periods=26)

        cloud_top = dataframe[['senkou_a', 'senkou_b']].max(axis=1)
        cloud_bottom = dataframe[['senkou_a', 'senkou_b']].min(axis=1)
        dataframe['cloud_condition'] = np.where(dataframe['close'] > cloud_top, 1,  # Buy
                                                np.where(dataframe['close'] < cloud_bottom, -1, 0))  # Sell, Equal/Inside

        dataframe['line_condition'] = np.where(dataframe['tenkan'] > dataframe['kijun'], 1,  # Buy
                                               np.where(dataframe['tenkan'] < dataframe['kijun'], -1, 0))  # Sell, Equal

        return dataframe
