import http.server
import socketserver
import requests
import json
import base64
import os
import logging

# --- Setup Logging ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# --- Configuration ---
PORT = 8000
API_URL = 'http://freqtrade:8080'
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'config.json'))

# --- Load Credentials ---
try:
    with open(CONFIG_PATH, 'r') as f:
        config = json.load(f)
        username = config['api_server']['username']
        password = config['api_server']['password']

    credentials = base64.b64encode(f'{username}:{password}'.encode('utf-8')).decode('utf-8')
    logging.info("Successfully loaded API credentials.")

except FileNotFoundError:
    logging.error(f"CRITICAL: Configuration file not found at {CONFIG_PATH}. The proxy will not be able to authenticate.")
    credentials = None
except KeyError:
    logging.error("CRITICAL: 'api_server' credentials not found in the configuration file. The proxy will not be able to authenticate.")
    credentials = None


class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests: either serve static files or proxy to the API."""
        if self.path.startswith('/api/'):
            if not credentials:
                self.send_error(500, "Proxy server is not configured with API credentials.")
                return
            self.proxy_to_api()
        else:
            # Serve static files from the current directory
            super().do_GET()

    def proxy_to_api(self):
        """Forward the request to the Freqtrade API and return the response."""
        url = f'{API_URL}{self.path}'
        logging.info(f"Proxying request to: {url}")

        try:
            # Prepare headers for the forwarded request
            headers = dict(self.headers)
            headers['Authorization'] = f'Basic {credentials}'
            # It's good practice to set the Host header
            headers['Host'] = 'localhost:8080'

            response = requests.get(url, headers=headers, timeout=10) # Added a timeout
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

            # Send response back to the client
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                # Skip transferring chunked encoding header
                if key.lower() not in ['transfer-encoding', 'content-encoding']:
                    self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response.content)
            logging.info(f"Successfully forwarded request. Status code: {response.status_code}")

        except requests.exceptions.HTTPError as e:
            logging.error(f"HTTP Error from API: {e}")
            self.send_error(e.response.status_code, f"API Error: {e}")
        except requests.exceptions.RequestException as e:
            logging.error(f"Error forwarding request to API: {e}")
            self.send_error(500, f"Error connecting to the Freqtrade API: {e}")

    def log_message(self, format, *args):
        """Override to use our logger instead of stderr."""
        logging.info(f"{self.address_string()} - {args[0]} {args[1]}")


if __name__ == "__main__":
    # Change directory to the dashboard's location to serve static files correctly
    web_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(web_dir)

    with socketserver.TCPServer(('', PORT), ProxyHandler) as httpd:
        logging.info(f"Serving dashboard on http://localhost:{PORT}")
        logging.info(f"Proxying API requests to {API_URL}")
        httpd.serve_forever()
