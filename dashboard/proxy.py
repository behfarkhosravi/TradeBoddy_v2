import http.server
import socketserver
import requests
import json
import base64
import os

PORT = 8000
API_URL = 'http://127.0.0.1:8080'
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../ft_userdata/user_data/config.json'))

# Load credentials from config.json
with open(CONFIG_PATH, 'r') as f:
    config = json.load(f)
    username = config['api_server']['username']
    password = config['api_server']['password']

# Encode credentials for Basic Authentication
credentials = base64.b64encode(f'{username}:{password}'.encode('utf-8')).decode('utf-8')

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith('/api/'):
            url = f'{API_URL}{self.path}'
            try:
                headers = dict(self.headers)
                headers['Authorization'] = f'Basic {credentials}'

                response = requests.get(url, headers=headers)
                self.send_response(response.status_code)
                for key, value in response.headers.items():
                    self.send_header(key, value)
                self.end_headers()
                self.wfile.write(response.content)
            except requests.exceptions.RequestException as e:
                self.send_error(500, f'Error forwarding request: {e}')
        else:
            return http.server.SimpleHTTPRequestHandler.do_GET(self)


# Change directory to the dashboard's location
os.chdir(os.path.join(os.path.dirname(__file__)))

with socketserver.TCPServer(('', PORT), ProxyHandler) as httpd:
    print('serving at port', PORT)
    httpd.serve_forever()
