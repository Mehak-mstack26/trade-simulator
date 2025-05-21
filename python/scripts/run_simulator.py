#!/usr/bin/env python3
"""
Trade simulator CLI tool.
This script provides a command-line interface for running trade simulations.
"""

import argparse
import json
import sys
import os
import time

# Add lib directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), "../lib"))

from trade_simulator import TradeSimulator

def main():
    parser = argparse.ArgumentParser(description="Trade Simulator CLI")
    
    # Required parameters
    parser.add_argument("--exchange", type=str, default="OKX",
                        help="Exchange (default: OKX)")
    parser.add_argument("--asset", type=str, default="BTC-USDT",
                        help="Trading pair (default: BTC-USDT)")
    parser.add_argument("--order-type", type=str, default="market",
                        choices=["market", "limit"],
                        help="Order type (default: market)")
    parser.add_argument("--quantity", type=float, default=100.0,
                        help="Order quantity in USD (default: 100.0)")
    parser.add_argument("--volatility", type=float, default=0.02,
                        help="Market volatility (default: 0.02)")
    parser.add_argument("--fee-tier", type=str, default="VIP0",
                        choices=["VIP0", "VIP1", "VIP2", "VIP3", "VIP4"],
                        help="Fee tier (default: VIP0)")
    
    # Output format
    parser.add_argument("--format", type=str, default="human",
                        choices=["human", "json"],
                        help="Output format (default: human)")
    
    args = parser.parse_args()
    
    # Create simulator
    simulator = TradeSimulator()
    
    # Prepare parameters
    params = {
        "exchange": args.exchange,
        "asset": args.asset,
        "orderType": args.order_type,
        "quantity": str(args.quantity),
        "volatility": str(args.volatility),
        "feeTier": args.fee_tier
    }
    
    # Print input parameters
    if args.format == "human":
        print("=== Trade Simulation Parameters ===")
        print(f"Exchange:   {args.exchange}")
        print(f"Asset:      {args.asset}")
        print(f"Order Type: {args.order_type}")
        print(f"Quantity:   ${args.quantity:.2f}")
        print(f"Volatility: {args.volatility:.4f}")
        print(f"Fee Tier:   {args.fee_tier}")
        print()
        print("Running simulation...")
    
    # Run simulation
    start_time = time.time()
    results = simulator.simulate_trade(params)
    end_time = time.time()
    
    # Print results
    if args.format == "human":
        print("\n=== Simulation Results ===")
        print(f"Expected Slippage:       {results['expectedSlippage']:.4f}%")
        print(f"Expected Fees:           ${results['expectedFees']:.2f}")
        print(f"Expected Market Impact:  {results['expectedMarketImpact']:.4f}%")
        print(f"Net Cost:                ${results['netCost']:.2f}")
        print(f"Maker/Taker Proportion:  {results['makerTakerProportion']:.2f}")
        print(f"Internal Latency:        {results['internalLatency']:.2f} ms")
        print(f"Last Price:              ${results['lastPrice']:.2f}")
        print(f"Spread (bps):            {results['spreadBps']:.2f}")
        print(f"Order Book Depth:        ${results['orderBookDepth']:.2f}")
        print(f"\nSimulation completed in {(end_time - start_time) * 1000:.2f} ms")
    else:
        # JSON format
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()
