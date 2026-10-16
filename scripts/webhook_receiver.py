"""Small standard-library HTTP receiver for training notifications."""

from http.server import BaseHTTPRequestHandler, HTTPServer
import json


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        try:
            payload = json.loads(self.rfile.read(length))
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_error(400, "Expected a JSON webhook payload")
            return
        print(json.dumps(payload, indent=2), flush=True)
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"received"}')


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 5001), WebhookHandler).serve_forever()