# python/lib/trade_simulator.py
import json
import time
import numpy as np
# from scipy import stats # Not used
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
import logging # Import logging

from lib.market_data import MarketDataProcessor, OrderBook # Relative import
from lib.almgren_chriss import AlmgrenChrissModel, AlmgrenChrissParams # Relative import

logger = logging.getLogger(__name__) # Get logger

@dataclass
class SimulationParams:
    exchange: str
    asset: str # e.g., BTC-USDT
    order_type: str
    quantity: float # in USD
    volatility: float # User input, e.g., 0.02 (2% daily) or an annualized figure
    fee_tier: str

@dataclass
class SimulationResults:
    expected_slippage_pct: float # Renamed for clarity
    expected_fees_usd: float   # Renamed for clarity
    expected_market_impact_pct: float # Renamed for clarity
    net_cost_usd: float        # Renamed for clarity
    maker_taker_proportion: float
    internal_latency_ms: float # Renamed for clarity
    last_price_usd: float      # Renamed for clarity
    spread_bps: float
    order_book_depth_usd: float # Renamed for clarity (e.g. total value in top N levels)
    # Add new fields if needed
    realized_volatility_short_term: Optional[float] = None # From market data processor
    market_data_timestamp: Optional[str] = None


class TradeSimulator:
    def __init__(self, market_data_processor: MarketDataProcessor):
        self.market_data_processor = market_data_processor
        self.fee_tiers = { # (maker_fee_rate, taker_fee_rate)
            "VIP0": (0.0008, 0.0010),
            "VIP1": (0.0007, 0.0009),
            "VIP2": (0.0005, 0.0008),
            "VIP3": (0.0003, 0.0006),
            "VIP4": (0.0001, 0.0004),
        }
        # Mock "trained" coefficients for slippage and maker/taker models
        # These would typically be loaded from a file or database in a real system
        self.slippage_model_coeffs = {
            "intercept": 0.00005,  # Base slippage % (0.005%)
            "quantity_usd_coef": 1e-9, # Slippage per USD of quantity
            "volatility_coef": 0.3,   # Multiplier for input volatility
            "spread_bps_coef": 0.00002 # Slippage per bps of spread
        }
        self.maker_taker_logistic_coeffs = {
            "intercept": 1.0,
            "volatility_coef": -15.0, # Higher vol -> lower maker proportion
            "quantity_depth_ratio_coef": -5.0 # Higher ratio (bigger order rel. to depth) -> lower maker
        }
        
    def _get_live_market_data(self, asset_symbol: str) -> Dict[str, Any]:
        """
        Fetches live market data for the asset.
        OKX WebSocket uses symbols like "BTC-USDT-SWAP".
        The input asset might be "BTC-USDT". We need to map this.
        For simplicity, assume asset_symbol is already the correct instId for OKX.
        """
        # Simple mapping for common assets to their SWAP counterparts if needed for WebSocket
        # This depends on what the WebSocket endpoint expects and provides.
        # The current WS endpoint is for BTC-USDT-SWAP.
        # If params.asset is "BTC-USDT", we should try fetching "BTC-USDT-SWAP"
        # from the market_data_processor if that's what it stores.

        # The current market_data_processor is hardcoded to BTC-USDT-SWAP.
        # If asset_symbol is different, we won't get live data from *this* processor.
        
        # Let's assume the input asset_symbol can be directly used if it matches,
        # or we attempt a common mapping.
        # For OKX, spot might be "BTC-USDT", perpetual swap is "BTC-USDT-SWAP".
        # The provided WS is for SWAP.
        
        # For now, if the processor is connected to BTC-USDT-SWAP and asset_symbol is BTC-USDT,
        # we will try to fetch BTC-USDT-SWAP.
        # This logic needs to be robust based on how symbols are handled.
        
        effective_symbol = asset_symbol
        if asset_symbol == "BTC-USDT":
             effective_symbol = "BTC-USDT-SWAP"
        elif asset_symbol == "ETH-USDT":
             effective_symbol = "ETH-USDT-SWAP"

        order_book: Optional[OrderBook] = self.market_data_processor.get_latest_order_book(effective_symbol)
        
        live_data = {
            "last_price_usd": 0.0,
            "spread_bps": 0.0, # Default to 0
            "order_book_depth_usd": 0.0,
            "realized_volatility_short_term": None,
            "market_data_timestamp": None,
            "is_data_live": False
        }

        if order_book: # Check if order_book object exists first
            logger.info(f"Live market data for {effective_symbol}: Found order book.")
            # Log individual components for spread_bps calculation
            raw_asks = order_book.asks[:3] # Log top 3 asks
            raw_bids = order_book.bids[:3] # Log top 3 bids
            mid_p = order_book.mid_price
            spread_val = order_book.spread
            spread_bps_val = order_book.spread_bps

            logger.info(f"OrderBook Details for {effective_symbol}:")
            logger.info(f"  Top Asks: {[(a.price, a.quantity) for a in raw_asks]}")
            logger.info(f"  Top Bids: {[(b.price, b.quantity) for b in raw_bids]}")
            logger.info(f"  Calculated Mid Price: {mid_p}")
            logger.info(f"  Calculated Spread: {spread_val}")
            logger.info(f"  Calculated Spread BPS: {spread_bps_val}")

            if mid_p > 0: # Ensure mid_price is positive before using it
                live_data["last_price_usd"] = mid_p
                live_data["spread_bps"] = spread_bps_val # Use the calculated spread_bps
                live_data["order_book_depth_usd"] = order_book.total_depth_usd(N_levels=10)
                live_data["market_data_timestamp"] = order_book.timestamp
                live_data["is_data_live"] = True
                if spread_bps_val <= 0:
                    logger.warning(f"Spread BPS for {effective_symbol} is {spread_bps_val}, which will result in '—' in UI.")
            else:
                logger.warning(f"Mid price for {effective_symbol} is {mid_p}. Using fallback values for some live data.")
                # Potentially set spread_bps to a specific error indicator or keep 0 if mid_price is bad
                # Fallback values for other fields (as you had before)
                if asset_symbol.startswith("BTC"):
                    live_data["last_price_usd"] = 60000.0 # Fallback if mid_p was bad
                    # live_data["spread_bps"] = 1.5 # Example fallback spread_bps
                    live_data["order_book_depth_usd"] = 2000000
                # ... other fallbacks ...
                live_data["market_data_timestamp"] = order_book.timestamp # Still use timestamp if book object exists

        else:
            logger.warning(f"No live order book data for {effective_symbol}. Using full fallback values.")
            # Full fallback as before
            if asset_symbol.startswith("BTC"):
                live_data["last_price_usd"] = 60000.0
                live_data["spread_bps"] = 1.5 # Fallback spread_bps
                live_data["order_book_depth_usd"] = 2000000
            # ... other fallbacks ...
        
        logger.info(f"Final live_data being returned for {asset_symbol}: {live_data}")
        return live_data

    def calculate_fees_usd(self, params: SimulationParams, maker_taker_prop: float) -> float:
        maker_fee_rate, taker_fee_rate = self.fee_tiers.get(params.fee_tier, self.fee_tiers["VIP0"])
        
        if params.order_type.lower() == "market":
            return params.quantity * taker_fee_rate
        
        # For limit orders (not used here but for completeness)
        # effective_fee_rate = (maker_taker_prop * maker_fee_rate) + \
        #                      ((1 - maker_taker_prop) * taker_fee_rate)
        # return params.quantity * effective_fee_rate
        return params.quantity * taker_fee_rate # Default to taker for market


    def predict_slippage_pct(self, params: SimulationParams, live_market_data: Dict) -> float:
        c = self.slippage_model_coeffs
        
        # Use input volatility (e.g., daily or annualized user provides)
        # If live_market_data['realized_volatility_short_term'] is available and relevant,
        # you might blend it or use it. For now, stick to user input vol.
        input_vol = params.volatility

        slippage = (
            c["intercept"] +
            (c["quantity_usd_coef"] * params.quantity) +
            (c["volatility_coef"] * input_vol) +
            (c["spread_bps_coef"] * live_market_data.get("spread_bps", 0.0))
        )
        return max(0.0, slippage) # Ensure non-negative

    def calculate_market_impact_pct(self, params: SimulationParams, live_market_data: Dict) -> float:
        current_price = live_market_data.get("last_price_usd", 1.0)
        if current_price == 0:
            logger.warning("Current price is 0, cannot calculate quantity in base asset for AC model. Market impact might be inaccurate.")
            # Fallback or decide how to handle; for now, proceed cautiously
            # A very small placeholder price could be used, or return a high default impact.
            # Let's make quantity_base_asset 0 if price is 0 to signal an issue to AC model.
            quantity_base_asset = 0.0
        else:
            quantity_base_asset = params.quantity / current_price # params.quantity is in USD

        # Simplified estimates for ADV and Market Cap (as before)
        if params.asset.startswith("BTC"):
            avg_daily_volume_base = 50000
            market_cap_usd = 1.2e12
        elif params.asset.startswith("ETH"):
            avg_daily_volume_base = 700000
            market_cap_usd = 350e9
        else:
            avg_daily_volume_base = 1000000
            market_cap_usd = 10e9
        
        annualized_volatility = params.volatility
        if 0 < annualized_volatility < 0.1: # Heuristic for daily vol input
             annualized_volatility = params.volatility * np.sqrt(252)
        elif annualized_volatility <=0:
            logger.warning(f"Input volatility {params.volatility} is not positive. Using a small default for AC.")
            annualized_volatility = 0.2 # Default 20% annualized if input is invalid

        ac_params_input = {
            "volatility": annualized_volatility,
            "quantity": quantity_base_asset,
            "avg_daily_volume": avg_daily_volume_base,
            "market_cap": market_cap_usd,
            "time_horizon_days": 1.0 / (24 * 60 * 2) # Example: execute over 1 hour of a day
        }
        
        try:
            estimated_ac_params: AlmgrenChrissParams = AlmgrenChrissModel.estimate_parameters(
                volatility=ac_params_input["volatility"],
                quantity=ac_params_input["quantity"],
                avg_daily_volume=ac_params_input["avg_daily_volume"],
                market_cap=ac_params_input["market_cap"],
                T_days=ac_params_input["time_horizon_days"]
            )
            
            # If quantity_base_asset ended up being 0 or very small, AC might misbehave or give 0 impact.
            if estimated_ac_params.X <= 1e-9: # If quantity is effectively zero
                logger.info("Quantity for AC model is near zero. Market impact calculated as 0.")
                return 0.0

            model = AlmgrenChrissModel(estimated_ac_params)
            risk_aversion_lambda = 1.0e-7 # Adjusted, might need tuning
            result = model.compute_optimal_trajectory(risk_aversion=risk_aversion_lambda)
            
            # result.expected_cost IS THE ABSOLUTE DOLLAR SHORTFALL FROM AC MODEL
            absolute_dollar_cost_from_ac = result.expected_cost
            
            # params.quantity IS THE TOTAL INITIAL USD VALUE OF THE ORDER
            if params.quantity > 0: # Avoid division by zero
                market_impact_percentage = (absolute_dollar_cost_from_ac / params.quantity) * 100.0
            else:
                market_impact_percentage = 0.0
            
            # The AC model's result.market_impact was (cost / X_base_qty) * 100, which is not what we want here.
            # We use our own calculation above.
            logger.info(f"AC calculation: abs_cost={absolute_dollar_cost_from_ac:.4f}, order_value_usd={params.quantity:.2f}, impact_pct={market_impact_percentage:.4f}%")
            return max(0.0, market_impact_percentage) # Ensure non-negative

        except Exception as e:
            logger.error(f"Almgren-Chriss calculation failed: {e}", exc_info=True)
            # Fallback to simplified model if AC fails
            # This fallback might need to be more robust or provide a clearer error impact.
            gamma_fallback = 0.1
            normalized_quantity_fallback = quantity_base_asset / (avg_daily_volume_base if avg_daily_volume_base > 0 else 1)
            # Ensure params.volatility is reasonable here if it's used directly
            vol_for_fallback = params.volatility if params.volatility > 0 else 0.02 
            market_impact_pct_fallback = gamma_fallback * vol_for_fallback * (normalized_quantity_fallback ** 0.6) * 100.0
            logger.warning(f"Falling back to simplified market impact: {market_impact_pct_fallback:.4f}%")
            return max(0.0, market_impact_pct_fallback)


    def predict_maker_taker_proportion(self, params: SimulationParams, live_market_data: Dict) -> float:
        """Predicts MAKER proportion (0 to 1). Taker is 1 - maker_proportion."""
        if params.order_type.lower() == "market":
            return 0.0  # Market orders are always takers

        # For limit orders (currently not primary focus but model is here)
        c = self.maker_taker_logistic_coeffs
        
        order_book_depth_usd = live_market_data.get("order_book_depth_usd", 1.0)
        if order_book_depth_usd == 0: order_book_depth_usd = 1.0 # Avoid division by zero
        
        quantity_depth_ratio = params.quantity / order_book_depth_usd
        
        # Logistic function input
        x = (
            c["intercept"] +
            (c["volatility_coef"] * params.volatility) +
            (c["quantity_depth_ratio_coef"] * quantity_depth_ratio)
        )
        maker_proportion = 1 / (1 + np.exp(-x)) # Sigmoid
        return np.clip(maker_proportion, 0.0, 1.0)

    def simulate_trade(self, params_dict: Dict[str, Any]) -> Dict[str, Any]:
        sim_start_time = time.time()
        
        params = SimulationParams(
            exchange=params_dict.get("exchange", "OKX"),
            asset=params_dict.get("asset", "BTC-USDT"), # This is what UI sends, e.g. "BTC-USDT"
            order_type=params_dict.get("orderType", "market"),
            quantity=float(params_dict.get("quantity", 100)),
            volatility=float(params_dict.get("volatility", 0.02)),
            fee_tier=params_dict.get("feeTier", "VIP0")
        )
        
        # Get live market data (price, spread, depth)
        # The asset here needs to be mapped to the actual instrument ID from WebSocket if different.
        # e.g., if UI sends "BTC-USDT", but WS uses "BTC-USDT-SWAP"
        live_market_data = self._get_live_market_data(params.asset)
        maker_taker_prop = self.predict_maker_taker_proportion(params, live_market_data)
        expected_fees_usd = self.calculate_fees_usd(params, maker_taker_prop)
        expected_slippage_pct = self.predict_slippage_pct(params, live_market_data)
        expected_market_impact_pct = self.calculate_market_impact_pct(params, live_market_data)
        
        slippage_cost_usd = params.quantity * (expected_slippage_pct / 100.0)
        market_impact_cost_usd = params.quantity * (expected_market_impact_pct / 100.0)
        net_cost_usd = slippage_cost_usd + expected_fees_usd + market_impact_cost_usd

        data_proc_latency_stats = self.market_data_processor.get_data_processing_latency_stats()
        sim_end_time = time.time()
        simulation_logic_time_ms = (sim_end_time - sim_start_time) * 1000

        return {
            "expectedSlippage": expected_slippage_pct,
            "expectedFees": expected_fees_usd,
            "expectedMarketImpact": expected_market_impact_pct,
            "netCost": net_cost_usd,
            "makerTakerProportion": maker_taker_prop,
            # Use average from stats for "internalLatency" as per original UI field
            "internalLatency": data_proc_latency_stats.get("avg_ms", 0.0), 
            "lastPrice": live_market_data["last_price_usd"],
            "spreadBps": live_market_data["spread_bps"],
            "orderBookDepth": live_market_data["order_book_depth_usd"],
            "marketDataTimestamp": live_market_data.get("market_data_timestamp"),
            "simulationExecutionTimeMs": simulation_logic_time_ms, # Time for this function
            "marketDataProcessingLatencyStats": data_proc_latency_stats # New detailed stats
        }


# Example usage - not run when imported
# if __name__ == "__main__":
#     # This example would require a running MarketDataProcessor instance
#     class MockMarketDataProcessor:
#         def get_latest_order_book(self, symbol): return None
#         def get_average_processing_time(self): return 10.0
#         def get_historical_volatility(self, symbol, window): return 0.001

#     mock_mdp = MockMarketDataProcessor()
#     simulator = TradeSimulator(market_data_processor=mock_mdp)
    
#     params = {
#         "exchange": "OKX", "asset": "BTC-USDT", "orderType": "market",
#         "quantity": "1000", "volatility": "0.05", "feeTier": "VIP1"
#     }
#     results = simulator.simulate_trade(params)
#     logger.info(json.dumps(results, indent=2))