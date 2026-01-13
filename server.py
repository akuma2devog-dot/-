from http.server import BaseHTTPRequestHandler, HTTPServer
from config import PORT

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_server():
    HTTPServer(("0.0.0.0", PORT), HealthHandler).serve_forever()
