
import os
import time
import requests
import logging
from prometheus_client import start_http_server, Gauge

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
FREQTRADE_API_URL = os.getenv('FREQTRADE_API_URL', 'http://freqtrade:8080')
FREQTRADE_USERNAME = os.getenv('FREQTRADE_USERNAME')
FREQTRADE_PASSWORD = os.getenv('FREQTRADE_PASSWORD')
PROMETHEUS_PORT = int(os.getenv('PROMETHEUS_PORT', 8001))

# --- Prometheus Metrics ---
# Create a dictionary to hold gauges for each condition for each pair
METRICS = {}
CONDITIONS = [
    'enter_long', 'enter_short', 'exit_long', 'exit_short',
    'rsi', 'sma', 'ema', 'macd', 'macdsignal', 'macdhist',
    'bollinger_top', 'bollinger_mid', 'bollinger_bottom', 'volume'
]

# --- State ---
last_candle_timestamp = {}
jwt_token = None
refresh_token = None
token_expiration = 0

def get_jwt_token():
    """Authenticate with Freqtrade API and get a JWT token."""
    global jwt_token, refresh_token, token_expiration
    # If token exists and is not expiring soon (e.g., in the next minute)
    if jwt_token and token_expiration > time.time() + 60:
        return jwt_token

    if refresh_token:
        token = refresh_jwt_token()
        if token:
            return token

    try:
        response = requests.post(
            f"{FREQTRADE_API_URL}/api/v1/token/login",
            auth=(FREQTRADE_USERNAME, FREQTRADE_PASSWORD)
        )
        response.raise_for_status()
        token_data = response.json()
        jwt_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        # Freqtrade tokens usually expire in 15 minutes (900 seconds)
        token_expiration = time.time() + 840  # 14 minutes
        return jwt_token
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to get JWT token: {e}")
        return None

def refresh_jwt_token():
    """Refresh the JWT token using the refresh token."""
    global jwt_token, token_expiration
    try:
        headers = {'Authorization': f'Bearer {refresh_token}'}
        response = requests.post(
            f"{FREQTRADE_API_URL}/api/v1/token/refresh",
            headers=headers
        )
        response.raise_for_status()
        token_data = response.json()
        jwt_token = token_data.get('access_token')
        token_expiration = time.time() + 840  # 14 minutes
        return jwt_token
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to refresh JWT token: {e}")
        return None

def fetch_pair_history(token, pair, timeframe='5m', strategy='level_one'):
    """Fetch analyzed pair history from Freqtrade."""
    try:
        headers = {'Authorization': f'Bearer {token}'}
        params = {
            'pair': pair,
            'timeframe': timeframe,
            'strategy': strategy
        }
        response = requests.get(
            f"{FREQTRADE_API_URL}/api/v1/pair_history",
            headers=headers,
            params=params
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to fetch pair history for {pair}: {e}")
        return None

def wait_for_freqtrade():
    """Wait for the Freqtrade API to be available."""
    while True:
        try:
            response = requests.get(f"{FREQTRADE_API_URL}/api/v1/ping")
            if response.status_code == 200:
                logging.info("Freqtrade API is available.")
                break
        except requests.exceptions.RequestException as e:
            logging.warning(f"Freqtrade API not yet available: {e}. Retrying in 10 seconds...")
        time.sleep(10)


def update_metrics():
    """Fetch data and update Prometheus metrics."""
    token = get_jwt_token()
    if not token:
        return

    # Get pairs from environment variable, split by comma
    pairs_str = os.getenv('FREQTRADE_PAIRS', 'BTC/USDT:USDT,PAXG/USDT:USDT')
    pairs = [pair.strip() for pair in pairs_str.split(',')]

    for pair in pairs:
        data = fetch_pair_history(token, pair)
        if not data or 'data' not in data or not data['data']:
            logging.warning(f"No data received for pair {pair}")
            continue

        # Get the last candle
        last_candle = data['data'][-1]
        timestamp = last_candle[0] # Assuming the first element is the timestamp

        # Check if this is a new candle
        if last_candle_timestamp.get(pair) == timestamp:
            logging.info(f"No new candle for {pair}. Skipping.")
            continue

        last_candle_timestamp[pair] = timestamp
        logging.info(f"New candle for {pair} at {timestamp}. Updating metrics.")

        # Create metrics if they don't exist for this pair
        safe_pair_name = pair.replace('/', '_').replace(':', '_')
        if safe_pair_name not in METRICS:
            METRICS[safe_pair_name] = {
                cond: Gauge(f'freqtrade_{cond}_{safe_pair_name}', f'Value of {cond} for {pair}')
                for cond in CONDITIONS
            }

        # Update metrics with the values from the last candle
        headers = data.get('columns', [])
        for i, header in enumerate(headers):
            if header in METRICS[safe_pair_name]:
                try:
                    value = float(last_candle[i])
                    METRICS[safe_pair_name][header].set(value)
                    logging.info(f"Set {header} for {pair} to {value}")
                except (ValueError, TypeError):
                    logging.warning(f"Could not convert value for {header} to float. Skipping.")


if __name__ == '__main__':
    logging.info(f"Starting Prometheus server on port {PROMETHEUS_PORT}")
    start_http_server(PROMETHEUS_PORT)

    wait_for_freqtrade()

    logging.info("Task manager started. Waiting for the first run.")

    while True:
        update_metrics()
        logging.info("Run complete. Waiting for 60 seconds.")
        time.sleep(60)
