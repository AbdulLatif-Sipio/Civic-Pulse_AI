"""
CivicPulse AI • CleanCity Copilot — Cloud Entrypoint
Self-contained Streamlit runner with automated background FastAPI backend.
Compatible with Streamlit Community Cloud (share.streamlit.io) and Hugging Face Spaces (Streamlit SDK).
"""

import os
import sys
import time
import socket
import threading
import logging

# Ensure root workspace and frontend modules are in sys.path
ROOT_DIR = os.path.abspath(os.path.dirname(__file__))
FRONTEND_DIR = os.path.join(ROOT_DIR, "cleancity-frontend", "cleancity-frontend")
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
if FRONTEND_DIR not in sys.path:
    sys.path.insert(0, FRONTEND_DIR)

logger = logging.getLogger("civicpulse_launcher")
logging.basicConfig(level=logging.INFO)

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0

def start_backend_daemon():
    """Starts master_backend FastAPI in a background daemon thread if not already running."""
    if is_port_in_use(8000):
        logger.info("[CivicPulse] Backend already running on port 8000.")
        return

    logger.info("[CivicPulse] Auto-starting FastAPI master backend on port 8000...")
    import uvicorn
    try:
        import master_backend
        server = threading.Thread(
            target=uvicorn.run,
            args=(master_backend.app,),
            kwargs={
                "host": "127.0.0.1",
                "port": 8000,
                "log_level": "warning",
            },
            daemon=True,
        )
        server.start()
        
        # Give the backend up to 6 seconds to bind and initialize DB
        for _ in range(30):
            if is_port_in_use(8000):
                logger.info("[CivicPulse] FastAPI master backend is ONLINE on port 8000.")
                break
            time.sleep(0.2)
    except Exception as e:
        logger.error(f"[CivicPulse] Failed to launch backend daemon: {e}")

# Launch backend in background before Streamlit script executes
start_backend_daemon()

# Change working directory so Streamlit relative asset paths resolve cleanly
os.chdir(FRONTEND_DIR)

# Load the main citizen portal application
main_app_path = os.path.join(FRONTEND_DIR, "app.py")
with open(main_app_path, "r", encoding="utf-8") as f:
    code = f.read()

# Execute app.py in global context
exec(compile(code, main_app_path, "exec"), globals())
