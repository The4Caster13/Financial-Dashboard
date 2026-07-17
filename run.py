"""Entry point — `python run.py`. Kept separate from app.py so a future desktop
shell can `from app import server` and drive the same Flask app without also
re-running this file's __main__ block."""
from app import app
from config import DEBUG, HOST, PORT

if __name__ == "__main__":
    # threaded=True lets the auto-refresh Interval on one page keep firing
    # without blocking other requests (e.g. switching pages, other browser tabs).
    app.run(host=HOST, port=PORT, debug=DEBUG, threaded=True)
