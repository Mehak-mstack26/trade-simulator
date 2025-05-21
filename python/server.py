import json
import sys
import os
import asyncio
import threading
import logging
from typing import Dict, Any

# --- REMOVE or COMMENT OUT THIS lib_dir path manipulation ---
# app_dir = os.path.abspath(os.path.dirname(__file__))
# python_dir = os.path.dirname(app_dir)
# lib_dir = os.path.join(python_dir, "lib")
# if lib_dir not in sys.path:
#     sys.path.insert(0, lib_dir)
# --- END REMOVAL ---

# Now imports from 'lib' should work if 'python' directory is on sys.path
from lib.trade_simulator import TradeSimulator  # Changed to absolute package import
from lib.market_data import MarketDataProcessor # Changed to absolute package import

# --- Logging Setup ---
# (Keep your logging setup as is)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
server_logger = logging.getLogger(__name__)

server_logger.debug(f"Attempting to run server.py from: {os.getcwd()}")
server_logger.debug(f"Current sys.path: {sys.path}")

try:
    server_logger.info("Attempting to import 'app' package...")
    import app # Just try to import the package first
    server_logger.info("Successfully imported 'app' package.")
    
    server_logger.info("Attempting to import 'app.route' module...")
    import app.route # Then try to import the module
    server_logger.info("Successfully imported 'app.route' module.")

    server_logger.info("Attempting to import POST from app.route...")
    from app.route import POST as simulate_trade_handler
    from app.route import logger as route_logger
    server_logger.info("Successfully imported POST and logger from app.route.")

except ImportError as e:
    server_logger.error(f"ImportError occurred: {e}", exc_info=True)
    sys.exit(1)
except Exception as e:
    server_logger.error(f"An unexpected error occurred during import: {e}", exc_info=True)
    sys.exit(1)

# If imports succeed, then proceed with Flask app
from flask import Flask, request, jsonify
import json # Make sure json is imported here as well

app_flask = Flask(__name__) # Renamed to avoid conflict if 'app' was imported as a module

@app_flask.route("/api/simulate", methods=["POST"])
def handle_simulate_route():
    route_logger.info(f"--- Received request on /api/simulate from {request.remote_addr} ---") # Log incoming request
    class MockFrameworkRequest:
        def __init__(self, body_bytes):
            self.body = body_bytes
    try:
        raw_body = request.data
        route_logger.debug(f"Raw request body: {raw_body[:500]}") # Log first 500 bytes of body

        framework_request_obj = MockFrameworkRequest(raw_body)
        response_dict_from_handler = simulate_trade_handler(framework_request_obj)
        
        route_logger.info(f"--- Simulation handler finished. Preparing response. Status: {response_dict_from_handler['status']} ---")
        route_logger.debug(f"Response body from handler: {response_dict_from_handler['body']}")

        response_body_content = json.loads(response_dict_from_handler["body"])
        
        flask_response = jsonify(response_body_content)
        route_logger.info(f"--- Sending response to client. Status: {response_dict_from_handler['status']} ---")
        return flask_response, response_dict_from_handler["status"]

    except json.JSONDecodeError as e:
        route_logger.error(f"JSONDecodeError in handle_simulate_route: {e}. Request data: {request.data[:200]}")
        return jsonify({"error": "Invalid JSON in request body"}), 400
    except Exception as e:
        route_logger.error(f"Unexpected error in handle_simulate_route: {e}", exc_info=True)
        return jsonify({"error": "An internal server error occurred"}), 500


if __name__ == "__main__":
    route_logger.info("Starting Flask backend server (from server.py)...")
    app_flask.run(debug=True, host="0.0.0.0", port=5001, use_reloader=False)