# Grafana Query Documentation for Freqtrade Metrics

This document provides instructions on how to query the Freqtrade metrics in Grafana.

## Available Metrics

The following metrics are exposed by the task manager:

- `rsi_condition_1h`
- `stoch_condition_1h`
- `cloud_condition_1h`
- `line_condition_1h`
- `macd_condition_1h`
- `adx_condition_1h`
- `bb_condition_1h`
- `rsi_condition`
- `stoch_condition`
- `cloud_condition`
- `line_condition`
- `macd_condition`
- `adx_condition`
- `bb_condition`

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

- **RSI Condition 1h:** `freqtrade_rsi_condition_1h_BTC_USDT_USDT`
- **MACD Condition:** `freqtrade_macd_condition_BTC_USDT_USDT`

**PAXG/USDT:USDT**

- **Cloud Condition 1h:** `freqtrade_cloud_condition_1h_PAXG_USDT_USDT`
- **BB Condition:** `freqtrade_bb_condition_PAXG_USDT_USDT`

You can use these query names in Grafana to create panels and visualize the data from the Freqtrade metrics.
