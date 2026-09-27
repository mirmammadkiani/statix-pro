import webview
import threading
import time
import socket
import sys
import os
import uvicorn

# Ensure UTF-8 output encoding on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def is_port_in_use(port: int = 8000) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def start_backend():
    # Make sure app path is in sys.path
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    if curr_dir not in sys.path:
        sys.path.insert(0, curr_dir)

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, log_level="warning")

if __name__ == "__main__":
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    if curr_dir not in sys.path:
        sys.path.insert(0, curr_dir)

    # Start backend in background if not already active
    if not is_port_in_use(8000):
        t = threading.Thread(target=start_backend, daemon=True)
        t.start()
        time.sleep(1.2)

    # Create native standalone desktop window
    window = webview.create_window(
        title="STATIX PRO | سامانه تحلیل استاتیک مهندسی عمران",
        url="http://localhost:8000",
        width=1320,
        height=880,
        min_size=(960, 640),
        background_color="#0a0e17"
    )

    webview.start()
