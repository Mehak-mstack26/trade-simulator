#!/usr/bin/env python3
"""
WebSocket client for connecting to OKX market data stream.
This script connects to the WebSocket endpoint and prints the received data.
"""

import asyncio
import json
import websockets
import argparse
import time
from datetime import datetime

async def connect_websocket(url, verbose=False):
    """Connect to WebSocket and process incoming data"""
    try:
        async with websockets.connect(url) as websocket:
            print(f"Connected to {url}")
            print("Receiving market data...")
            
            tick_count = 0
            start_time = time.time()
            
            while True:
                # Receive message
                message = await websocket.recv()
                data = json.loads(message)
                
                tick_count += 1
                current_time = time.time()
                elapsed = current_time - start_time
                
                # Print summary every second in non-verbose mode
                if not verbose and elapsed >= 1:
                    tps = tick_count / elapsed
                    print(f"Received {tick_count} ticks ({tps:.2f} ticks/sec)")
                    tick_count = 0
                    start_time = current_time
                
                # Print full data in verbose mode
                if verbose:
                    timestamp = data.get("timestamp", "")
                    exchange = data.get("exchange", "")
                    symbol = data.get("symbol", "")
                    
                    # Get top of book
                    asks = data.get("asks", [])
                    bids = data.get("bids", [])
                    
                    best_ask = asks[0] if asks else ["N/A", "N/A"]
                    best_bid = bids[0] if bids else ["N/A", "N/A"]
                    
                    print(f"[{timestamp}] {exchange} {symbol}")
                    print(f"  Best Ask: {best_ask[0]} ({best_ask[1]})")
                    print(f"  Best Bid: {best_bid[0]} ({best_bid[1]})")
                    print(f"  Book Depth: {len(asks)} asks, {len(bids)} bids")
                    print()
    except Exception as e:
        print(f"WebSocket error: {e}")
        # Implement reconnection logic here

def main():
    parser = argparse.ArgumentParser(description="WebSocket client for OKX market data")
    parser.add_argument("--url", type=str, 
                        default="wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP",
                        help="WebSocket URL")
    parser.add_argument("--verbose", action="store_true", 
                        help="Print detailed market data")
    
    args = parser.parse_args()
    
    print("Starting WebSocket client...")
    print(f"Connecting to: {args.url}")
    print(f"Verbose mode: {'enabled' if args.verbose else 'disabled'}")
    print()
    
    try:
        asyncio.run(connect_websocket(args.url, args.verbose))
    except KeyboardInterrupt:
        print("\nClient stopped by user")

if __name__ == "__main__":
    main()
