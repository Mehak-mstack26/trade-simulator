import asyncio
import json
import time
import websockets
import numpy as np
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

@dataclass
class OrderBookLevel:
    price: float
    quantity: float

@dataclass
class OrderBook:
    timestamp: str  # Millisecond epoch string
    exchange: str
    symbol: str
    asks: List[OrderBookLevel]
    bids: List[OrderBookLevel]
    
    @property
    def mid_price(self) -> float:
        if not self.asks or not self.bids:
            # logger.debug(f"Calculating mid_price for {self.symbol}: Asks or bids list is empty.") # Too verbose for normal ops
            return 0.0
        try:
            # Ensure prices are floats, can happen if source data is inconsistent
            ask_price = float(self.asks[0].price)
            bid_price = float(self.bids[0].price)
            return (ask_price + bid_price) / 2
        except (TypeError, ValueError, IndexError) as e:
            logger.error(f"Error calculating mid_price for {self.symbol}: {e}. Asks: {self.asks[:1]}, Bids: {self.bids[:1]}")
            return 0.0
    
    @property
    def spread(self) -> float:
        if not self.asks or not self.bids:
            return 0.0
        try:
            ask_price = float(self.asks[0].price)
            bid_price = float(self.bids[0].price)
            return ask_price - bid_price
        except (TypeError, ValueError, IndexError) as e:
            logger.error(f"Error calculating spread for {self.symbol}: {e}. Asks: {self.asks[:1]}, Bids: {self.bids[:1]}")
            return 0.0
    
    @property
    def spread_bps(self) -> float:
        current_mid_price = self.mid_price
        if current_mid_price == 0:
            return 0.0 # Avoid division by zero; if mid_price is 0, spread_bps is undefined or infinite
        current_spread = abs(self.spread)  # Use absolute value of spread
        return (current_spread / current_mid_price) * 10000
    
    def depth_at_level(self, level_pct: float) -> Tuple[float, float]: # Not currently used, but potentially useful
        if not self.asks or not self.bids: return 0.0, 0.0
        mid = self.mid_price
        if mid == 0: return 0.0, 0.0
        level_diff_abs = mid * level_pct
        ask_depth = sum(float(l.quantity) for l in self.asks if float(l.price) <= mid + level_diff_abs)
        bid_depth = sum(float(l.quantity) for l in self.bids if float(l.price) >= mid - level_diff_abs)
        return ask_depth, bid_depth
    
    def total_depth_usd(self, N_levels: int = 10) -> float:
        if not self.asks and not self.bids: return 0.0
        # Optimization: Ensure N_levels does not exceed available levels to prevent summing empty lists often
        ask_value = sum(float(l.price) * float(l.quantity) for l in self.asks[:N_levels])
        bid_value = sum(float(l.price) * float(l.quantity) for l in self.bids[:N_levels])
        return ask_value + bid_value

class MarketDataProcessor:
    def __init__(self, websocket_url: str):
        self.websocket_url = websocket_url
        self.order_books: Dict[str, OrderBook] = {} # Data Structure: Dict for O(1) avg access by symbol
        # Historical data for L2 can be memory intensive. Capped for memory optimization.
        self.historical_data: Dict[str, List[OrderBook]] = {} 
        self.processing_times: List[float] = [] # Latency Benchmark: stores individual tick processing times
        self.max_historical_L2_ticks = 100 # Memory Optimization: Cap for L2 history per symbol
        self.max_processing_times_entries = 1000 # Memory Optimization: Cap for latency metrics storage
        self.is_connected: bool = False # Network: Track WebSocket connection status

    async def connect_websocket(self):
        # Network Optimization: Loop for reconnections on disconnect
        while True:
            try:
                # Network Optimization: Ping/pong helps maintain connection and detect dead ones faster.
                async with websockets.connect(
                    self.websocket_url,
                    ping_interval=15, 
                    ping_timeout=30   
                ) as websocket:
                    logger.info(f"Successfully connected to WebSocket: {self.websocket_url}")
                    self.is_connected = True
                    while True:
                        processing_start_time = time.perf_counter() # Latency Benchmark: High-precision timer
                        message_raw = await websocket.recv()
                        
                        try:
                            data = json.loads(message_raw) # Network: Standard JSON parsing
                        except json.JSONDecodeError:
                            logger.error(f"Failed to decode JSON from WebSocket message: {message_raw[:200]}")
                            continue # Skip malformed message

                        parsed_symbol = data.get("symbol")
                        if not parsed_symbol:
                            # logger.warning(f"Received message without 'symbol' field: {data.get('event')}") # Example: might be pong/info
                            continue
                            
                        order_book = self._parse_order_book(data)
                        if order_book:
                            self.order_books[parsed_symbol] = order_book # Thread-safety: dict assignment is atomic
                            
                            # Memory Optimization: Capped historical data storage
                            if parsed_symbol not in self.historical_data:
                                self.historical_data[parsed_symbol] = []
                            self.historical_data[parsed_symbol].append(order_book)
                            if len(self.historical_data[parsed_symbol]) > self.max_historical_L2_ticks:
                                self.historical_data[parsed_symbol].pop(0)
                        
                        processing_end_time = time.perf_counter()
                        # Latency Benchmark: Data processing latency for this tick in ms
                        tick_processing_time_ms = (processing_end_time - processing_start_time) * 1000 
                        self.processing_times_ms.append(tick_processing_time_ms) # Store in ms
                        # Memory Optimization: Capped list for processing times
                        if len(self.processing_times_ms) > self.max_processing_times_entries:
                            self.processing_times_ms.pop(0)

            except websockets.exceptions.ConnectionClosed as e:
                logger.error(f"WebSocket connection to {self.websocket_url} closed: {e}. Reconnecting in 5s...")
            except ConnectionRefusedError:
                logger.error(f"Connection to {self.websocket_url} refused. VPN/server down? Retrying in 10s...")
            except Exception as e: # Catch other potential websocket errors (e.g. timeout, handshake failures)
                logger.error(f"WebSocket error with {self.websocket_url}: {e}. Reconnecting in 5s...", exc_info=False) # exc_info=True for full trace
            finally:
                self.is_connected = False # Ensure status is updated on any disconnection/error
                await asyncio.sleep(5) # Wait before trying to reconnect

    def _parse_order_book(self, data: Dict) -> Optional[OrderBook]:
        asks_raw = data.get("asks", [])
        bids_raw = data.get("bids", [])
        timestamp_str = data.get("timestamp") # Expected "YYYY-MM-DDTHH:MM:SSZ" from goquant.io proxy
        symbol = data.get("symbol")
        exchange = data.get("exchange", "OKX") # Default if not present

        if not all([isinstance(asks_raw, list), isinstance(bids_raw, list), timestamp_str, symbol]):
            logger.error(f"Missing critical fields or invalid format in order book data for {symbol}: {data.get('event')}")
            return None

        try:
            # Data Structure: OrderBookLevel stores price/qty. Parsing to float here.
            asks = [OrderBookLevel(float(price), float(qty)) for price, qty in asks_raw if price and qty]
            bids = [OrderBookLevel(float(price), float(qty)) for price, qty in bids_raw if price and qty]
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing order book levels for {symbol}: {e}. Asks raw: {asks_raw[:2]}, Bids raw: {bids_raw[:2]}")
            return None
        
        # Data Integrity: Ensure book is sorted (provider should do this, but verify/enforce)
        asks.sort(key=lambda x: x.price) 
        bids.sort(key=lambda x: x.price, reverse=True)
        
        try:
            # Timestamp conversion: Python 3.7+ datetime.fromisoformat or strptime can handle 'Z'
            # The goquant proxy seems to provide "YYYY-MM-DDTHH:MM:SSZ"
            # If it contains fractional seconds like "YYYY-MM-DDTHH:MM:SS.fffZ", adjust format string
            # For "YYYY-MM-DDTHH:MM:SSZ":
            if '.' in timestamp_str: # Handles "YYYY-MM-DDTHH:MM:SS.fffZ"
                 dt_object = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
            else: # Handles "YYYY-MM-DDTHH:MM:SSZ"
                 dt_object = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
            ms_epoch_timestamp = str(int(dt_object.timestamp() * 1000))
        except ValueError as e:
            logger.error(f"Could not parse timestamp string '{timestamp_str}' for {symbol}: {e}. Using current time as fallback.")
            ms_epoch_timestamp = str(int(time.time() * 1000)) # Fallback, less accurate

        return OrderBook(
            timestamp=ms_epoch_timestamp, # Store as ms epoch string
            exchange=exchange,
            symbol=symbol,
            asks=asks,
            bids=bids
        )
    
    def get_latest_order_book(self, symbol: str) -> Optional[OrderBook]:
        # Thread-safety: dict.get() is atomic
        return self.order_books.get(symbol)
    
    def get_average_processing_time(self) -> float:
        # Latency Benchmark: Provides average data processing latency.
        # Thread-safety: list read operations (len, sum) are safe if appends/pops are atomic (which they are).
        if not self.processing_times: return 0.0
        return sum(self.processing_times) / len(self.processing_times)
    
    def get_data_processing_latency_stats(self) -> Dict[str]:
        if not self.processing_times_ms:
            return {
                "avg_ms": 0.0, "min_ms": 0.0, "max_ms": 0.0, 
                "p95_ms": 0.0, "count": 0, "std_dev_ms": 0.0
            }
        
        times_np = np.array(self.processing_times_ms)
        stats = {
            "avg_ms": float(np.mean(times_np)),
            "min_ms": float(np.min(times_np)),
            "max_ms": float(np.max(times_np)),
            "p95_ms": float(np.percentile(times_np, 95)) if len(times_np) > 1 else float(times_np[0] if len(times_np) == 1 else 0),
            "count": len(times_np),
            "std_dev_ms": float(np.std(times_np)) if len(times_np) > 1 else 0.0
        }
        return stats
    
    def get_historical_volatility(self, symbol: str, window: int = 100) -> float:
        """Calculate historical volatility from mid prices (simple realization).
        Note: This is a very short-term realized volatility. Annualization needs care.
        """
        if symbol not in self.historical_data or len(self.historical_data[symbol]) < window + 1:
            return 0.0 # Not enough data
            
        # Use last N ticks from historical data for this symbol
        relevant_books = self.historical_data[symbol][-(window + 1):]
        mid_prices = [ob.mid_price for ob in relevant_books if ob.mid_price > 0]

        if len(mid_prices) < 2: # Need at least 2 prices for a return
            return 0.0

        log_returns = np.diff(np.log(mid_prices))
        
        if len(log_returns) > 1: # Need at least 2 returns for std dev
            # This standard deviation is per-tick interval.
            # To annualize: std_dev_tick * sqrt(ticks_per_year)
            # Ticks_per_year is hard to estimate accurately without consistent tick intervals.
            # For now, return the raw standard deviation of log returns as a measure of short-term price fluctuation.
            return np.std(log_returns) 
        return 0.0

# Example usage - not run when imported
# async def main_test():
#     processor = MarketDataProcessor("wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP")
#     # In a real app, connect_websocket runs in a background thread.
#     # For a standalone test, you can run it directly:
#     await processor.connect_websocket() 

# if __name__ == "__main__":
#     logging.basicConfig(level=logging.DEBUG) # Use DEBUG for more verbose logs during testing
#     asyncio.run(main_test())
