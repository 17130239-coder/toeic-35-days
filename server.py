#!/usr/bin/env python3
"""
Simple HTTP server for 35-Days Vocabulary Platform & Wayground Clone
"""
import http.server
import socketserver
import os
import sys

PORT = 3000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    # Try port or fallback
    for p in range(port, port + 10):
        try:
            with socketserver.TCPServer(("", p), Handler) as httpd:
                print(f"🚀 Server running successfully at http://localhost:{p}")
                print(f"📚 Website 1 (Vocabulary Learning App): http://localhost:{p}/")
                print(f"🎮 Website 2 (Wayground Quiz Arena):     http://localhost:{p}/wayground.html")
                httpd.serve_forever()
        except OSError:
            continue
