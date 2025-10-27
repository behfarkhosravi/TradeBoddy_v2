# Grafana Query Documentation for Freqtrade Metrics

This document provides instructions on how to query the Freqtrade metrics in Grafana.

## Available Metrics

The following metrics are exposed by the task manager:

- `enter_long`
- `enter_short`
- `exit_long`
- `exit_short`
- `rsi`
- `sma`
- `ema`
- `macd`
- `macdsignal`
- `macdhist`
- `bollinger_top`
- `bollinger_mid`
- `bollinger_bottom`
- `volume`

## Querying in Grafana

To query a metric in Grafana, you can use the following format:

```
freqtrade_<metric_name>_<pair>
```

Where:

- `<metric_name>` is one of the metrics listed above.
- `<pair>` is the trading pair, with `/` and `:` replaced by `_`.

### Examples

Here are some examples for the pairs `BTC/USDT:USDT` and `PAXG/USDT:USDT`:

**BTC/USDT:USDT**

- **RSI:** `freqtrade_rsi_BTC_USDT_USDT`
- **SMA:** `freqtrade_sma_BTC_USDT_USDT`
- **MACD:** `freqtrade_macd_BTC_USDT_USDT`

**PAXG/USDT:USDT**

- **RSI:** `freqtrade_rsi_PAXG_USDT_USDT`
- **Volume:** `freqtrade_volume_PAXG_USDT_USDT`
- **Bollinger Top:** `freqtrade_bollinger_top_PAXG_USDT_USDT`

You can use these query names in Grafana to create panels and visualize the data from the Freqtrade metrics.
