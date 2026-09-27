import uvicorn
import webbrowser
import threading
import time
import sys
import os

# Ensure UTF-8 output encoding on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

def open_browser():
    time.sleep(1.2)
    print("Opening STATIX PRO in your browser at http://localhost:8000 ...")
    webbrowser.open("http://localhost:8000")

if __name__ == "__main__":
    # Ensure current directory is in sys.path
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    if curr_dir not in sys.path:
        sys.path.insert(0, curr_dir)

    # Launch browser after slight delay
    threading.Thread(target=open_browser, daemon=True).start()

    from backend.modules.network import get_local_ip
    local_ip = get_local_ip()

    print("==================================================================")
    print("   STATIX PRO - Civil Engineering Statics Suite (Beer & Johnston) ")
    print(f"   💻 Desktop Access URL: http://localhost:8000                 ")
    print(f"   📱 Android Access URL: http://{local_ip}:8000               ")
    print("==================================================================")

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, log_level="info")
