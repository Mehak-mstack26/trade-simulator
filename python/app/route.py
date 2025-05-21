# python/app/route.py
import json
import sys
import os
import asyncio
import threading # For running websocket in background
import logging # Import logging
import time
from typing import Dict, Any

# --- Corrected sys.path.append for robust import from 'lib' ---
# Get the absolute path of the 'app' directory (where this file is)
app_dir = os.path.abspath(os.path.dirname(__file__))
# Go up one level to the 'python' directory
python_dir = os.path.dirname(app_dir)
# Construct the path to the 'lib' directory which is a sibling to 'app'
lib_dir = os.path.join(python_dir, "lib")
# Add 'lib' directory to sys.path if not already there
if lib_dir not in sys.path:
    sys.path.insert(0, lib_dir) # Insert at the beginning to prioritize it

# Now imports from 'lib' should work
from trade_simulator import TradeSimulator
from market_data import MarketDataProcessor # <<<< ------ CORRECTED IMPORT HERE

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Global instances ---
# Initialize MarketDataProcessor globally
DEFAULT_WEBSOCKET_URL = "wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP"
market_data_processor = MarketDataProcessor(DEFAULT_WEBSOCKET_URL)

# Initialize simulator, passing the market data processor
simulator = TradeSimulator(market_data_processor)


# --- Background task for WebSocket ---
def run_websocket_client():
    logger.info(f"Starting WebSocket client for {market_data_processor.websocket_url} in a background thread.")
    # Create a new event loop for the thread if Python < 3.7 or if needed
    # For Python 3.7+ asyncio.run should handle this, but explicit loop can be more robust in threads
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(market_data_processor.connect_websocket())
    finally:
        loop.close()

# Start WebSocket client in a separate thread when the app initializes
websocket_thread = threading.Thread(target=run_websocket_client, daemon=True)
websocket_thread.start()


def POST(request):
    request_start_time = time.perf_counter()
    try:
        # Parse request body
        body = json.loads(request.body)
        logger.info(f"Received simulation request: {body}")
        
        # Validate required parameters
        required_params = ["exchange", "asset", "orderType", "quantity", "volatility", "feeTier"]
        for param in required_params:
            if param not in body:
                logger.error(f"Missing required parameter: {param}")
                return {
                    "status": 400,
                    "body": json.dumps({"error": f"Missing required parameter: {param}"})
                }
        
        # Simulate trade
        results = simulator.simulate_trade(body)
        logger.info(f"Simulation successful for asset {body.get('asset')}")
        
        request_end_time = time.perf_counter() 
        backend_processing_time_ms = (request_end_time - request_start_time) * 1000
        logger.info(f"Backend POST request processing time: {backend_processing_time_ms:.2f} ms")
        results["backendRequestProcessingTimeMs"] = backend_processing_time_ms 

        return {"status": 200, "body": json.dumps(results)}
    except Exception as e:
        logger.error(f"Error during simulation: {str(e)}", exc_info=True)
        request_end_time = time.perf_counter() 
        backend_processing_time_ms = (request_end_time - request_start_time) * 1000
        logger.info(f"Backend POST request processing time (with error): {backend_processing_time_ms:.2f} ms")
        return {"status": 500, "body": json.dumps({"error": str(e)})}
    
