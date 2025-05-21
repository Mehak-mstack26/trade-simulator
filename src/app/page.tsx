// "use client"

// import type React from "react" // Keep if you use React.FC or similar types, otherwise optional
// import { useState, useEffect } from "react"
// import { toast } from "sonner"
// import { Card } from "@/components/ui/card"
// import { Button } from "@/components/ui/button"
// import { Input } from "@/components/ui/input"
// import { Label } from "@/components/ui/label"
// import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
// import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
// // Ensure simulateTrade is correctly imported from your actions file
// // If your actions.ts exports simulateTrade, the path below is an example
// // import { simulateTrade } from "./actions"; // Assuming actions.ts is in the same directory
// // If actions.ts is in src/app/actions.ts and page.tsx is in src/app/page.tsx:
// import { simulateTrade } from "@/app/actions" // This should be correct if actions.ts is in src/app/
// import { Loader2, ArrowRight } from 'lucide-react'

// // Available trading pairs
// const TRADING_PAIRS = ["BTC-USDT", "ETH-USDT", "SOL-USDT", "XRP-USDT", "BNB-USDT"]

// interface SimulationResultData {
//   expectedSlippage: number;
//   expectedFees: number;
//   expectedMarketImpact: number;
//   netCost: number;
//   makerTakerProportion: number;
//   internalLatency: number;
//   lastPrice: number;
//   spreadBps: number;
//   orderBookDepth: number;
//   marketDataTimestamp: string | null;
//   simulationExecutionTimeMs: number;
//   // Add any other fields returned by your backend
//   [key: string]: any; // Allow for other potential fields
// }

// export default function Home() {
//   const [isUIDisplayingConnected, setIsUIDisplayingConnected] = useState(false) // For UI WebSocket simulation
//   const [isLoading, setIsLoading] = useState(false)
//   const [tickCount, setTickCount] = useState(0) // For UI WebSocket simulation
//   const [lastUpdate, setLastUpdate] = useState("") // For UI WebSocket simulation

//   const [formData, setFormData] = useState({
//     exchange: "OKX",
//     asset: "BTC-USDT",
//     orderType: "market",
//     quantity: "100",
//     volatility: "0.02", // Example: 2% daily volatility
//     feeTier: "VIP1",
//   })

//   const [results, setResults] = useState<SimulationResultData>({
//     expectedSlippage: 0,
//     expectedFees: 0,
//     expectedMarketImpact: 0,
//     netCost: 0,
//     makerTakerProportion: 0,
//     internalLatency: 0,
//     lastPrice: 0,
//     spreadBps: 0,
//     orderBookDepth: 0,
//     marketDataTimestamp: null,
//     simulationExecutionTimeMs: 0,
//   })

//   // This useEffect simulates a frontend WebSocket connection for UI purposes (tick counter, status).
//   // The actual market data connection is handled by the Python backend.
//   useEffect(() => {
//     let intervalId: NodeJS.Timeout | undefined;

//     // Simulate connection attempt
//     const timer = setTimeout(() => {
//       setIsUIDisplayingConnected(true);
//       toast("UI WebSocket Simulation", {
//         description: "Frontend UI simulating market data stream connection.",
//       });

//       // Simulate receiving ticks for UI display
//       intervalId = setInterval(() => {
//         setTickCount((prev) => prev + 1);
//         setLastUpdate(new Date().toLocaleTimeString()); // More readable format
//       }, 2000); // Slower interval for UI ticks
//     }, 1500);

//     return () => {
//       clearTimeout(timer);
//       if (intervalId) {
//         clearInterval(intervalId);
//       }
//     };
//   }, []);

//   const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
//     const { name, value } = e.target;
//     setFormData((prev) => ({ ...prev, [name]: value }));
//   };

//   const handleSelectChange = (name: string, value: string) => {
//     setFormData((prev) => ({ ...prev, [name]: value }));
//   };

//   const handleSimulate = async () => {
//     setIsLoading(true);
//     try {
//       // Ensure formData values are numbers where appropriate for the backend if not already strings
//       const paramsToSend = {
//         ...formData,
//         quantity: formData.quantity, // Already string, backend parses to float
//         volatility: formData.volatility, // Already string, backend parses to float
//       };
//       const result = await simulateTrade(paramsToSend);
//       // Ensure all fields from backend are mapped, provide defaults if some are missing
//       setResults({
//         expectedSlippage: result.expectedSlippage ?? 0,
//         expectedFees: result.expectedFees ?? 0,
//         expectedMarketImpact: result.expectedMarketImpact ?? 0,
//         netCost: result.netCost ?? 0,
//         makerTakerProportion: result.makerTakerProportion ?? 0,
//         internalLatency: result.internalLatency ?? 0, // This is backend's per-tick processing time
//         lastPrice: result.lastPrice ?? 0,
//         spreadBps: result.spreadBps ?? 0,
//         orderBookDepth: result.orderBookDepth ?? 0,
//         marketDataTimestamp: result.marketDataTimestamp ?? null,
//         simulationExecutionTimeMs: result.simulationExecutionTimeMs ?? 0,
//       });
//       toast("Simulation Complete", {
//         description: "Trade simulation results updated.",
//       });
//     } catch (error) {
//       console.error("Simulation error:", error);
//       const errorMessage = error instanceof Error ? error.message : "Failed to run trade simulation";
//       toast("Simulation Error", {
//         description: errorMessage,
//         style: { backgroundColor: 'red', color: 'white' },
//       });
//     } finally {
//       setIsLoading(false);
//     }
//   };

//   return (
//     <main className="container mx-auto py-8 px-4">
//       <h1 className="text-3xl font-bold mb-8 text-center">Cryptocurrency Trade Simulator</h1>

//       <div className="flex flex-col lg:flex-row gap-6">
//         {/* Left Panel - Input Parameters */}
//         <Card className="p-6 flex-1">
//           <h2 className="text-xl font-semibold mb-4">Input Parameters</h2>

//           <div className="space-y-4">
//             <div>
//               <Label htmlFor="exchange">Exchange</Label>
//               <Select
//                 value={formData.exchange}
//                 onValueChange={(value) => handleSelectChange("exchange", value)}
//                 disabled
//               >
//                 <SelectTrigger>
//                   <SelectValue placeholder="Select Exchange" />
//                 </SelectTrigger>
//                 <SelectContent>
//                   <SelectItem value="OKX">OKX</SelectItem>
//                 </SelectContent>
//               </Select>
//             </div>

//             <div>
//               <Label htmlFor="asset">Spot Asset</Label>
//               <Select value={formData.asset} onValueChange={(value) => handleSelectChange("asset", value)}>
//                 <SelectTrigger>
//                   <SelectValue placeholder="Select Asset" />
//                 </SelectTrigger>
//                 <SelectContent>
//                   {TRADING_PAIRS.map((pair) => (
//                     <SelectItem key={pair} value={pair}>
//                       {pair}
//                     </SelectItem>
//                   ))}
//                 </SelectContent>
//               </Select>
//             </div>

//             <div>
//               <Label htmlFor="orderType">Order Type</Label>
//               <Select
//                 value={formData.orderType}
//                 onValueChange={(value) => handleSelectChange("orderType", value)}
//                 disabled
//               >
//                 <SelectTrigger>
//                   <SelectValue placeholder="Select Order Type" />
//                 </SelectTrigger>
//                 <SelectContent>
//                   <SelectItem value="market">Market</SelectItem>
//                 </SelectContent>
//               </Select>
//             </div>

//             <div>
//               <Label htmlFor="quantity">Quantity (USD)</Label>
//               <Input
//                 id="quantity"
//                 name="quantity"
//                 type="number"
//                 value={formData.quantity}
//                 onChange={handleInputChange}
//                 min="1"
//                 step="any"
//               />
//             </div>

//             <div>
//               <Label htmlFor="volatility">Volatility (e.g., 0.02 for 2%)</Label>
//               <Input
//                 id="volatility"
//                 name="volatility"
//                 type="number"
//                 value={formData.volatility}
//                 onChange={handleInputChange}
//                 min="0.0001" // Allow smaller volatility
//                 max="2"    // Allow up to 200%
//                 step="0.0001"
//               />
//             </div>

//             <div>
//               <Label htmlFor="feeTier">Fee Tier</Label>
//               <Select value={formData.feeTier} onValueChange={(value) => handleSelectChange("feeTier", value)}>
//                 <SelectTrigger>
//                   <SelectValue placeholder="Select Fee Tier" />
//                 </SelectTrigger>
//                 <SelectContent>
//                   <SelectItem value="VIP0">VIP0 (Standard)</SelectItem>
//                   <SelectItem value="VIP1">VIP1</SelectItem>
//                   <SelectItem value="VIP2">VIP2</SelectItem>
//                   <SelectItem value="VIP3">VIP3</SelectItem>
//                   <SelectItem value="VIP4">VIP4</SelectItem>
//                 </SelectContent>
//               </Select>
//             </div>

//             <Button onClick={handleSimulate} className="w-full mt-4" disabled={isLoading}>
//               {isLoading ? (
//                 <>
//                   <Loader2 className="mr-2 h-4 w-4 animate-spin" />
//                   Simulating...
//                 </>
//               ) : (
//                 <>
//                   Run Simulation
//                   <ArrowRight className="ml-2 h-4 w-4" />
//                 </>
//               )}
//             </Button>
//           </div>
//         </Card>

//         {/* Right Panel - Output Parameters */}
//         <Card className="p-6 flex-1">
//           <h2 className="text-xl font-semibold mb-4">Output Parameters</h2>
//           <Tabs defaultValue="results" className="w-full">
//             <TabsList className="grid w-full grid-cols-2">
//               <TabsTrigger value="results">Simulation Results</TabsTrigger>
//               <TabsTrigger value="market">Market Snapshot</TabsTrigger>
//             </TabsList>

//             <TabsContent value="results" className="space-y-4 pt-4">
//               <div className="grid grid-cols-2 gap-x-4 gap-y-3"> {/* Adjusted gap */}
//                 <div>
//                   <Label className="text-sm text-muted-foreground">Expected Slippage</Label>
//                   <p className="text-lg font-medium">{results.expectedSlippage.toFixed(4)}%</p>
//                 </div>
//                 <div>
//                   <Label className="text-sm text-muted-foreground">Expected Fees</Label>
//                   <p className="text-lg font-medium">${results.expectedFees.toFixed(2)}</p>
//                 </div>
//                 <div>
//                   <Label className="text-sm text-muted-foreground">Market Impact</Label>
//                   <p className="text-lg font-medium">{results.expectedMarketImpact.toFixed(4)}%</p>
//                 </div>
//                 <div>
//                   <Label className="text-sm text-muted-foreground">Net Cost</Label>
//                   <p className="text-lg font-medium">${results.netCost.toFixed(2)}</p>
//                 </div>
//                 <div>
//                   <Label className="text-sm text-muted-foreground">Maker/Taker Proportion</Label>
//                   <p className="text-lg font-medium">{results.makerTakerProportion.toFixed(2)}</p>
//                 </div>
//                 <div>
//                   <Label className="text-sm text-muted-foreground">WS Tick Latency (Avg)</Label>
//                   <p className="text-lg font-medium">{results.internalLatency.toFixed(2)} ms</p>
//                 </div>
//                 <div>
//                   <Label className="text-sm text-muted-foreground">Simulation Exec. Time</Label>
//                   <p className="text-lg font-medium">
//                     {results.simulationExecutionTimeMs ? results.simulationExecutionTimeMs.toFixed(2) : "0.00"} ms
//                   </p>
//                 </div>
//               </div>
//             </TabsContent>

//             <TabsContent value="market" className="space-y-4 pt-4">
//               <div className="grid grid-cols-2 gap-x-4 gap-y-3"> {/* Adjusted gap */}
//                 <div>
//                   <Label className="text-sm text-muted-foreground">UI Connection Status</Label>
//                   <p className={`text-lg font-medium ${isUIDisplayingConnected ? "text-green-500" : "text-red-500"}`}>
//                     {isUIDisplayingConnected ? "Connected" : "Disconnected"}
//                   </p>
//                 </div>
//                 <div>
//                   <Label className="text-sm text-muted-foreground">UI Ticks Received</Label>
//                   <p className="text-lg font-medium">{tickCount}</p>
//                 </div>
//                 <div>
//                   <Label className="text-sm text-muted-foreground">Last Price (from Sim)</Label>
//                   <p className="text-lg font-medium">${results.lastPrice > 0 ? results.lastPrice.toFixed(2) : "—"}</p>
//                 </div>
//                 <div>
//                   <Label className="text-sm text-muted-foreground">Spread (bps) (from Sim)</Label>
//                   <p className="text-lg font-medium">{results.spreadBps !== null && results.spreadBps !== undefined ? 
//     results.spreadBps.toFixed(2) : "—"}</p>
//                 </div>
//                 <div>
//                   <Label className="text-sm text-muted-foreground">Order Book Depth (from Sim)</Label>
//                   <p className="text-lg font-medium">
//                     ${results.orderBookDepth > 0 ? results.orderBookDepth.toFixed(2) : "—"}
//                   </p>
//                 </div>
//                  <div>
//                   <Label className="text-sm text-muted-foreground">Market Data Timestamp (Sim)</Label>
//                   <p className="text-xs font-medium"> {/* Smaller font for timestamp */}
//                     {results.marketDataTimestamp ? new Date(parseInt(results.marketDataTimestamp)).toLocaleString() : "N/A"}
//                   </p>
//                 </div>
//                 <div>
//                   <Label className="text-sm text-muted-foreground">UI Last Update</Label>
//                   <p className="text-lg font-medium">{lastUpdate || "—"}</p>
//                 </div>
//               </div>
//             </TabsContent>
//           </Tabs>
//         </Card>
//       </div>

//       <div className="mt-8">
//         <Card className="p-6">
//           <h2 className="text-xl font-semibold mb-4">System Information</h2>
//           <div className="grid grid-cols-1 md:grid-cols-2 gap-4"> {/* Changed to 2 cols for sys info */}
//             <div>
//               <Label className="text-muted-foreground">Backend WebSocket Endpoint</Label>
//               <p className="text-sm font-mono break-all">
//                 wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP
//               </p>
//             </div>
//             <div>
//               <Label className="text-muted-foreground">UI Simulated Connection</Label>
//               <p className={`font-medium ${isUIDisplayingConnected ? "text-green-500" : "text-red-500"}`}>
//                 {isUIDisplayingConnected ? "Connected" : "Connecting..."}
//               </p>
//             </div>
//           </div>
//         </Card>
//       </div>
//     </main>
//   )
// }


"use client"

import React, { useState, useEffect, useRef, useCallback } from "react" // Added useRef, useCallback
import { toast } from "sonner"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Switch } from "@/components/ui/switch" // Import Switch
import { simulateTrade } from "@/app/actions"
import { Loader2, ArrowRight, RefreshCwIcon } from 'lucide-react' // Added RefreshCwIcon

// Available trading pairs
const TRADING_PAIRS = ["BTC-USDT", "ETH-USDT", "SOL-USDT", "XRP-USDT", "BNB-USDT"]
const AUTO_REFRESH_INTERVAL_MS = 5000; // Refresh every 5 seconds

interface SimulationResultData {
  expectedSlippage: number;
  expectedFees: number;
  expectedMarketImpact: number;
  netCost: number;
  makerTakerProportion: number;
  internalLatency: number;
  lastPrice: number;
  spreadBps: number;
  orderBookDepth: number;
  marketDataTimestamp: string | null;
  simulationExecutionTimeMs: number;
  backendRequestProcessingTimeMs?: number; 
  marketDataProcessingLatencyStats?: {
    avg_ms: number;
    min_ms: number;
    max_ms: number;
    p95_ms: number;
    count: number;
    std_dev_ms: number;
  };
  [key: string]: any;
}

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [isAutoRefreshing, setIsAutoRefreshing] = useState(false); // For subtle loading state during auto-refresh

  const [formData, setFormData] = useState({
    exchange: "OKX",
    asset: "BTC-USDT",
    orderType: "market",
    quantity: "100",
    volatility: "0.02",
    feeTier: "VIP1",
  });

  const [results, setResults] = useState<SimulationResultData>({
    expectedSlippage: 0, expectedFees: 0, expectedMarketImpact: 0, netCost: 0,
    makerTakerProportion: 0, internalLatency: 0, lastPrice: 0, spreadBps: 0,
    orderBookDepth: 0, marketDataTimestamp: null, simulationExecutionTimeMs: 0,
    backendRequestProcessingTimeMs: 0,
    marketDataProcessingLatencyStats: { avg_ms: 0, min_ms: 0, max_ms: 0, p95_ms: 0, count: 0, std_dev_ms: 0 }
  });

  // New states for auto-refresh and backend status
  const [autoRefreshEnabled, setAutoRefreshEnabled] = useState(false);
  const autoRefreshIntervalId = useRef<NodeJS.Timeout | null>(null);
  const [isBackendConnected, setIsBackendConnected] = useState(true); // Assume connected until a failure
  const [uiActivityCounter, setUiActivityCounter] = useState(0);
  const [lastAutoRefreshTime, setLastAutoRefreshTime] = useState<string | null>(null);
  const [lastJsProcessingTime, setLastJsProcessingTime] = useState<number | null>(null); // For UI update latency measurement

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSelectChange = (name: string, value: string) => {
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const performSimulation = useCallback(async (isAuto: boolean = false) => {
    const jsProcessingStartTime = performance.now(); 
    if (!isAuto) {
      setIsLoading(true);
    } else {
      setIsAutoRefreshing(true); // Indicate background activity
    }

    try {
      const paramsToSend = { ...formData };
      const result = await simulateTrade(paramsToSend);
      setResults({
        expectedSlippage: result.expectedSlippage ?? 0,
        expectedFees: result.expectedFees ?? 0,
        expectedMarketImpact: result.expectedMarketImpact ?? 0,
        netCost: result.netCost ?? 0,
        makerTakerProportion: result.makerTakerProportion ?? 0,
        internalLatency: result.internalLatency ?? 0,
        lastPrice: result.lastPrice ?? 0,
        spreadBps: result.spreadBps ?? 0,
        orderBookDepth: result.orderBookDepth ?? 0,
        marketDataTimestamp: result.marketDataTimestamp ?? null,
        simulationExecutionTimeMs: result.simulationExecutionTimeMs ?? 0,
        backendRequestProcessingTimeMs: result.backendRequestProcessingTimeMs, // Added
        marketDataProcessingLatencyStats: result.marketDataProcessingLatencyStats // Added
      });

      if (!isBackendConnected) setIsBackendConnected(true); // Connection restored

      if (!isAuto) {
        toast("Simulation Complete", { description: "Trade simulation results updated." });
      } else {
        setUiActivityCounter(prev => prev + 1);
        setLastAutoRefreshTime(new Date().toLocaleTimeString());
      }
    } catch (error) {
      console.error(`Simulation error during ${isAuto ? "auto-refresh" : "manual run"}:`, error);
      const errorMessage = error instanceof Error ? error.message : "Failed to run trade simulation";
      
      if (isBackendConnected) setIsBackendConnected(false);

      if (isAuto) {
        setAutoRefreshEnabled(false); // Stop auto-refresh on error
        toast.error(`Auto-refresh failed: ${errorMessage}. Stopped.`, { duration: 5000 });
      } else {
        toast("Simulation Error", {
          description: errorMessage,
          style: { backgroundColor: 'red', color: 'white' },
        });
      }
    } finally {
      if (!isAuto) {
        setIsLoading(false);
      }
      setIsAutoRefreshing(false);
      const jsProcessingEndTime = performance.now();
      const duration = jsProcessingEndTime - jsProcessingStartTime;
      setLastJsProcessingTime(duration);
      console.log(`Frontend JS + API call for simulation: ${duration.toFixed(2)} ms`);
    }
  }, [formData, isBackendConnected]); // Dependencies for useCallback

  const handleManualSimulate = () => {
    performSimulation(false);
  };

  const handleAutoRefreshToggle = (checked: boolean) => {
    setAutoRefreshEnabled(checked);
    if (checked) {
      setUiActivityCounter(0); // Reset counter when enabling
      setLastAutoRefreshTime(null);
    }
  };

  // Effect to manage auto-refresh interval
  useEffect(() => {
    if (autoRefreshIntervalId.current) {
      clearInterval(autoRefreshIntervalId.current);
      autoRefreshIntervalId.current = null;
    }

    if (autoRefreshEnabled) {
      // Perform an initial simulation immediately when auto-refresh is turned on
      // if results are stale or not yet loaded.
      if (results.lastPrice === 0 || uiActivityCounter === 0) {
         performSimulation(true);
      }

      autoRefreshIntervalId.current = setInterval(() => {
        performSimulation(true);
      }, AUTO_REFRESH_INTERVAL_MS);
    }

    return () => {
      if (autoRefreshIntervalId.current) {
        clearInterval(autoRefreshIntervalId.current);
      }
    };
  }, [autoRefreshEnabled, formData, performSimulation, results.lastPrice, uiActivityCounter]); // Added performSimulation and others to dependencies


  // Initial simulation run on component mount if desired, or rely on user/auto-refresh
   useEffect(() => {
    // Optional: Run simulation once on load if you want initial data without user interaction
    // performSimulation(false); 
    // For now, let's not auto-run on mount, user can click or enable auto-refresh.
  }, [performSimulation]); // Empty dependency array means it runs once, if performSimulation is stable

  return (
    <main className="container mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold mb-8 text-center">Cryptocurrency Trade Simulator</h1>

      <div className="flex flex-col lg:flex-row gap-6">
        {/* Left Panel - Input Parameters */}
        <Card className="p-6 flex-1">
          <h2 className="text-xl font-semibold mb-4">Input Parameters</h2>
          <div className="space-y-4">
            {/* Exchange, Asset, Order Type, Quantity, Volatility, Fee Tier Inputs... (same as before) */}
             <div>
              <Label htmlFor="exchange">Exchange</Label>
              <Select
                value={formData.exchange}
                onValueChange={(value) => handleSelectChange("exchange", value)}
                disabled
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select Exchange" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="OKX">OKX</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="asset">Spot Asset</Label>
              <Select value={formData.asset} onValueChange={(value) => handleSelectChange("asset", value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select Asset" />
                </SelectTrigger>
                <SelectContent>
                  {TRADING_PAIRS.map((pair) => (
                    <SelectItem key={pair} value={pair}>
                      {pair}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="orderType">Order Type</Label>
              <Select
                value={formData.orderType}
                onValueChange={(value) => handleSelectChange("orderType", value)}
                disabled
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select Order Type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="market">Market</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <Label htmlFor="quantity">Quantity (USD)</Label>
              <Input
                id="quantity"
                name="quantity"
                type="number"
                value={formData.quantity}
                onChange={handleInputChange}
                min="1"
                step="any"
              />
            </div>

            <div>
              <Label htmlFor="volatility">Volatility (e.g., 0.02 for 2%)</Label>
              <Input
                id="volatility"
                name="volatility"
                type="number"
                value={formData.volatility}
                onChange={handleInputChange}
                min="0.0001"
                max="2"
                step="0.0001"
              />
            </div>

            <div>
              <Label htmlFor="feeTier">Fee Tier</Label>
              <Select value={formData.feeTier} onValueChange={(value) => handleSelectChange("feeTier", value)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select Fee Tier" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="VIP0">VIP0 (Standard)</SelectItem>
                  <SelectItem value="VIP1">VIP1</SelectItem>
                  <SelectItem value="VIP2">VIP2</SelectItem>
                  <SelectItem value="VIP3">VIP3</SelectItem>
                  <SelectItem value="VIP4">VIP4</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center space-x-2 mt-4">
              <Switch
                id="auto-refresh"
                checked={autoRefreshEnabled}
                onCheckedChange={handleAutoRefreshToggle}
              />
              <Label htmlFor="auto-refresh">Auto-refresh results every {AUTO_REFRESH_INTERVAL_MS/1000}s</Label>
              {isAutoRefreshing && <RefreshCwIcon className="h-4 w-4 animate-spin text-muted-foreground" />}
            </div>

            <Button onClick={handleManualSimulate} className="w-full mt-2" disabled={isLoading || autoRefreshEnabled}>
              {isLoading ? (
                <><Loader2 className="mr-2 h-4 w-4 animate-spin" />Simulating...</>
              ) : (
                <><ArrowRight className="mr-2 h-4 w-4" />Run Simulation</>
              )}
            </Button>
            {autoRefreshEnabled && (
                 <p className="text-xs text-muted-foreground text-center">Manual simulation disabled during auto-refresh.</p>
            )}
          </div>
        </Card>

        {/* Right Panel - Output Parameters */}
        <Card className="p-6 flex-1">
          <h2 className="text-xl font-semibold mb-4">Output Parameters</h2>
          <Tabs defaultValue="results" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="results">Simulation Results</TabsTrigger>
              <TabsTrigger value="market">Market Snapshot</TabsTrigger>
            </TabsList>

            <TabsContent value="results" className="space-y-4 pt-4">
              <div className="grid grid-cols-2 gap-x-4 gap-y-3">
                {/* Results fields (same as before) */}
                <div>
                  <Label className="text-sm text-muted-foreground">Expected Slippage</Label>
                  <p className="text-lg font-medium">{results.expectedSlippage.toFixed(4)}%</p>
                </div>
                <div>
                  <Label className="text-sm text-muted-foreground">Expected Fees</Label>
                  <p className="text-lg font-medium">${results.expectedFees.toFixed(2)}</p>
                </div>
                <div>
                  <Label className="text-sm text-muted-foreground">Market Impact</Label>
                  <p className="text-lg font-medium">{results.expectedMarketImpact.toFixed(4)}%</p>
                </div>
                <div>
                  <Label className="text-sm text-muted-foreground">Net Cost</Label>
                  <p className="text-lg font-medium">${results.netCost.toFixed(2)}</p>
                </div>
                <div>
                  <Label className="text-sm text-muted-foreground">Maker/Taker Proportion</Label>
                  <p className="text-lg font-medium">{results.makerTakerProportion.toFixed(2)}</p>
                </div>
                <div>
                  <Label className="text-sm text-muted-foreground">WS Tick Latency (Avg)</Label>
                  <p className="text-lg font-medium">{results.internalLatency.toFixed(2)} ms</p>
                </div>
                <div>
                  <Label className="text-sm text-muted-foreground">Simulation Exec. Time</Label>
                  <p className="text-lg font-medium">
                    {results.simulationExecutionTimeMs ? results.simulationExecutionTimeMs.toFixed(2) : "0.00"} ms
                  </p>
                </div>
              </div>
            </TabsContent>

            <TabsContent value="market" className="space-y-3 pt-4">
              <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                <div><Label className="text-sm text-muted-foreground">Backend Connection</Label><p className={`text-lg font-medium ${isBackendConnected ? "text-green-500" : "text-red-500"}`}>{isBackendConnected ? "Connected" : "Error"}</p></div>
                <div><Label className="text-sm text-muted-foreground">Auto-Refreshes Done</Label><p className="text-lg font-medium">{autoRefreshEnabled ? uiActivityCounter : "N/A"}</p></div>
                <div><Label className="text-sm text-muted-foreground">Last Auto-Refresh Time</Label><p className="text-lg font-medium">{autoRefreshEnabled && lastAutoRefreshTime ? lastAutoRefreshTime : "N/A"}</p></div>
                <div><Label className="text-sm text-muted-foreground">Last Price</Label><p className="text-lg font-medium">${results.lastPrice > 0 ? results.lastPrice.toFixed(2) : "—"}</p></div>
                <div><Label className="text-sm text-muted-foreground">Spread (bps)</Label><p className="text-lg font-medium">{results.spreadBps != null ? results.spreadBps.toFixed(2) : "—"}</p></div>
                <div><Label className="text-sm text-muted-foreground">Order Book Depth</Label><p className="text-lg font-medium">${results.orderBookDepth > 0 ? results.orderBookDepth.toFixed(2) : "—"}</p></div>
                <div><Label className="text-sm text-muted-foreground">Market Data Timestamp</Label><p className="text-xs font-medium">{results.marketDataTimestamp ? new Date(parseInt(results.marketDataTimestamp)).toLocaleString() : "N/A"}</p></div>
                <hr className="col-span-2 my-1" />
                <div><Label className="text-sm text-muted-foreground">BE Tick Latency (Avg)</Label><p className="text-lg font-medium">{results.internalLatency.toFixed(2)} ms</p></div>
                <div><Label className="text-sm text-muted-foreground">BE Sim Exec. Time</Label><p className="text-lg font-medium">{results.simulationExecutionTimeMs ? results.simulationExecutionTimeMs.toFixed(2) : "0.00"} ms</p></div>
                <div><Label className="text-sm text-muted-foreground">BE Request Time</Label><p className="text-lg font-medium">{results.backendRequestProcessingTimeMs ? results.backendRequestProcessingTimeMs.toFixed(2) : "N/A"} ms</p></div>
                <div>
                  <Label className="text-sm text-muted-foreground">FE JS + API Time</Label>
                  <p className="text-lg font-medium">{lastJsProcessingTime ? lastJsProcessingTime.toFixed(2) + " ms" : "N/A"}</p>
                </div>
                {results.marketDataProcessingLatencyStats && (
                  <>
                    <div className="col-span-2 mt-1">
                      <Label className="text-sm text-muted-foreground">BE Market Data Tick Processing Stats (ms):</Label>
                      <p className="text-xs">
                        Avg: {results.marketDataProcessingLatencyStats.avg_ms.toFixed(2)}, 
                        Min: {results.marketDataProcessingLatencyStats.min_ms.toFixed(2)}, 
                        Max: {results.marketDataProcessingLatencyStats.max_ms.toFixed(2)}, 
                        P95: {results.marketDataProcessingLatencyStats.p95_ms.toFixed(2)}, 
                        StdDev: {results.marketDataProcessingLatencyStats.std_dev_ms.toFixed(2)}
                        ({results.marketDataProcessingLatencyStats.count} ticks)
                      </p>
                    </div>
                  </>
                )}
              </div>
            </TabsContent>
          </Tabs>
        </Card>
      </div>

      <div className="mt-8">
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">System Information</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <Label className="text-muted-foreground">Backend WebSocket Endpoint</Label>
              <p className="text-sm font-mono break-all">
                wss://ws.gomarket-cpp.goquant.io/ws/l2-orderbook/okx/BTC-USDT-SWAP
              </p>
            </div>
            <div>
              <Label className="text-muted-foreground">Backend HTTP API Endpoint</Label>
              <p className="text-sm font-mono break-all">
                http://localhost:5001/api/simulate
              </p>
            </div>
          </div>
        </Card>
      </div>
    </main>
  )
}