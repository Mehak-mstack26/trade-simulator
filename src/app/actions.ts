// src/app/actions.ts
'use server' // If using Next.js App Router server actions

// Define the expected structure of parameters from the frontend
interface SimulateTradeParams {
  exchange: string;
  asset: string;
  orderType: string;
  quantity: string; // Keep as string, Python backend will parse
  volatility: string; // Keep as string, Python backend will parse
  feeTier: string;
}

// Define the expected structure of the successful response from the backend
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
}

export async function simulateTrade(params: SimulateTradeParams): Promise<SimulationResultData> {
  const backendUrl = 'http://localhost:5001/api/simulate'; // Ensure this matches your Flask server
  console.log("Frontend: Sending simulation request to backend:", params);

  try {
    const response = await fetch(backendUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params), // Send the parameters as a JSON string
    });

    const responseData = await response.json(); // Always try to parse JSON

    if (!response.ok) {
      console.error("Frontend: Backend returned an error:", responseData);
      // The backend already structures its error in { "error": "message" }
      throw new Error(responseData.error || `HTTP error! status: ${response.status}`);
    }

    console.log("Frontend: Received simulation results from backend:", responseData);
    return responseData as SimulationResultData;

  } catch (error) {
    console.error("Frontend: Error during simulateTrade fetch:", error);
    if (error instanceof Error) {
        throw error; // Re-throw the original error if it's already an Error instance
    }
    throw new Error("Network error or failed to connect to the simulation backend.");
  }
}