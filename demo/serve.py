#!/usr/bin/env python3
"""Serve widget demos. Run from repo root:  python demo/serve.py [port]
Then open: http://localhost:7777/demo/"""
import http.server
import os
import sys
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 7777
os.chdir(Path(__file__).parent.parent)
print(f"Widget demos → http://localhost:{PORT}/demo/")
http.server.test(HandlerClass=http.server.SimpleHTTPRequestHandler, port=PORT, bind="127.0.0.1")
