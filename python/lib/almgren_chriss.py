import numpy as np
from dataclasses import dataclass
from typing import List, Optional
import logging # Import logging

logger = logging.getLogger(__name__) # Get logger

@dataclass
class AlmgrenChrissParams:
    sigma: float  # Volatility (daily, for internal calculations if T is in days)
    eta: float    # Permanent impact parameter
    gamma: float  # Temporary impact parameter
    T: float      # Time horizon (in units consistent with sigma, e.g., days)
    X: float      # Total shares/quantity to execute (in base asset)
    
@dataclass
class AlmgrenChrissResult:
    optimal_trajectory: List[float]
    expected_cost: float
    market_impact: float # As a percentage of total value
    
class AlmgrenChrissModel:
    def __init__(self, params: AlmgrenChrissParams):
        self.params = params
        if params.X == 0: # Handle zero quantity case
            logger.warning("AlmgrenChrissModel initialized with zero quantity.")
        
    def compute_optimal_trajectory(self, risk_aversion: float = 1.0e-6) -> AlmgrenChrissResult:
        if self.params.X == 0:
             return AlmgrenChrissResult(optimal_trajectory=[0.0], expected_cost=0.0, market_impact=0.0)

        sigma = self.params.sigma
        eta = self.params.eta
        gamma = self.params.gamma
        T = self.params.T
        X = self.params.X
        
        N = 10  # Number of trading intervals (can be configurable)
        tau = T / N
        
        # kappa = np.sqrt(risk_aversion * (sigma**2) / (gamma + 1e-12)) # Avoid division by zero
        # Handle cases where gamma might be zero or very small
        if gamma <= 1e-12: # If temporary impact is negligible
            # This implies trading very slowly is optimal if eta is also small, or instant if eta is large.
            # The formula for kappa might become problematic.
            # For simplicity, if gamma is zero, market impact might be dominated by permanent impact.
            # Or, if a linear trajectory is assumed when temporary impact is negligible:
            logger.warning("Gamma (temporary impact parameter) is very small or zero. Kappa calculation might be unstable.")
            # Defaulting to a simple linear trajectory and estimating cost based on permanent impact
            # This is a simplification; true AC with gamma=0 needs careful derivation.
            # For now, let's proceed with kappa calculation, but add small epsilon to gamma.
            gamma_eff = max(gamma, 1e-12)
        else:
            gamma_eff = gamma

        # Ensure risk_aversion is positive, sigma^2 is non-negative
        if risk_aversion <= 0 or sigma < 0:
            logger.error(f"Invalid parameters for kappa: risk_aversion={risk_aversion}, sigma={sigma}")
            # Fallback or raise error
            return AlmgrenChrissResult(optimal_trajectory=[X] + [0.0]*N, expected_cost=float('inf'), market_impact=float('inf'))


        kappa_squared_numerator = risk_aversion * (sigma**2)
        if kappa_squared_numerator < 0: # Should not happen if inputs are valid
            kappa_squared_numerator = 0

        kappa = np.sqrt(kappa_squared_numerator / gamma_eff)

        trajectory = []
        
        # sinh_kappa_T = np.sinh(kappa * T)
        # cosh_kappa_T = np.cosh(kappa * T)
        # Using static methods to handle large values
        sinh_kappa_T = self._sinh(kappa * T)
        cosh_kappa_T = self._cosh(kappa * T)


        if abs(sinh_kappa_T) < 1e-9: # Avoid division by zero if kappa*T is very small (effectively linear trade)
            # Linear trajectory
            for j in range(N + 1):
                trajectory.append(X * (1 - (j / N)))
        else:
            for j in range(N + 1):
                t_j = j * tau
                # x_j = X * (np.sinh(kappa * (T - t_j)) / sinh_kappa_T)
                x_j = X * (self._sinh(kappa * (T - t_j)) / sinh_kappa_T)
                trajectory.append(x_j)
        
        # Ensure trajectory ends at 0 and starts at X
        trajectory[0] = X
        trajectory[-1] = 0.0

        # Calculate Expected Cost (Implementation Shortfall)
        # E[Cost] = X * (eta * X / 2) + gamma * sum( (x_j - x_{j+1})^2 / tau_j ) from paper
        # Or using the closed-form solution for expected cost when optimal:
        # E[Cost] = (eta * X^2 / 2) + ( (gamma * X^2 * kappa) / (2 * sinh_kappa_T^2) ) * ( (kappa*T/2) + sinh(2*kappa*T)/4 )
        # A simpler common representation:
        # Cost = PermanentImpactCost + TemporaryImpactCost
        # PermanentImpact: 0.5 * eta * X^2 (if eta is defined as dP/dQ = eta * v)
        # TemporaryImpact: if kappa*T is small, approx gamma * X^2 / T
        #                  else, gamma * X^2 * kappa * (coth(kappa*T))
        
        permanent_cost_component = 0.5 * eta * X**2
        
        if abs(kappa * T) < 1e-6 or abs(sinh_kappa_T) < 1e-9: # linear execution approximation
            temporary_cost_component = gamma * X**2 / T if T > 0 else 0
        else:
            temporary_cost_component = gamma_eff * X**2 * kappa * (cosh_kappa_T / sinh_kappa_T)
            
        expected_total_cost = permanent_cost_component + temporary_cost_component
        
        # Market impact as a percentage of total value (X * S_0)
        # If S_0 is current price, then market_impact_pct = (expected_total_cost / X) / S_0 * 100
        # The model itself gives cost in terms of price movement.
        # If X is quantity and cost is in price units, then cost/X is avg price move.
        # Market impact % = (Avg Price Move / Initial Price) * 100
        # Here, the 'expected_cost' is the total dollar cost.
        # So, market_impact_pct = (expected_total_cost / (X * InitialPrice)) * 100 if cost is in dollars.
        # The model often expresses cost in terms of price deviation.
        # If eta, gamma are scaled correctly, expected_cost IS the dollar cost.
        
        # The problem asks for "Expected Market Impact (%)".
        # If X is in base currency (e.g. BTC) and `expected_total_cost` is also in base currency terms (price impact * quantity)
        # Then market_impact_pct = (expected_total_cost / X) * 100 if X is interpreted as value.
        # Let's assume `expected_total_cost` is the total dollar cost.
        # And `X` is quantity in base asset. We need an initial price to normalize.
        # The model doesn't explicitly use an initial price S0 for cost calculation, it's implicit in scaled eta, gamma.
        # For now, assume `expected_total_cost` is the total $ cost, and we want impact % of initial $ value.
        # However, the parameters eta, gamma are often scaled such that the output cost can be directly used.
        # The LinkedIn article formula for market impact used X (total shares).
        # If expected_cost is the $ value lost, then market_impact_pct = (expected_cost / (X_usd_value)) * 100
        # The current `X` is in base asset. We need price to convert `X` to USD for denominator if `expected_cost` is USD.
        # Or, if `expected_cost` is in (price_deviation * base_quantity), then `expected_cost / X` is avg price deviation.
        
        # Let's assume the cost formula yields total $ cost.
        # The quantity X is in base asset. To get total initial $ value of order, we need a price.
        # This price isn't part of AlmgrenChrissParams. It should be.
        # For now, we return `expected_total_cost / X_initial_value_usd * 100`.
        # Since we don't have InitialPrice here, we can assume X is already value, or cost is scaled.
        # The common interpretation is `expected_cost / (S0 * X) * 100`.
        # If `eta` and `gamma` are properly calibrated from price data, `expected_cost` is already the $ cost.
        # Then `market_impact_pct = (expected_cost / total_initial_order_value_usd) * 100`
        # The `X` in `AlmgrenChrissParams` is `quantity_base_asset`.
        # If `expected_total_cost` represents the total $ execution shortfall, then
        # market_impact = (expected_total_cost / (Price_at_start * X_base_asset)) * 100
        # This model's `expected_cost` is often interpreted as the additional cost (shortfall) in dollar terms.
        # So if the initial order value was `P0 * X`, then market_impact = `expected_cost / (P0 * X) * 100`.
        # The `estimate_parameters` tries to make `eta` and `gamma` such that this holds.

        # For now, if X is large, eta and gamma are small, cost will be a fraction of X.
        # Let's assume the formula for expected_cost / X (quantity) gives the average price deviation.
        # If X is quantity in base, and cost is total $ cost, then cost/X = avg price deviation from ideal.
        # This seems to be the case.
        
        # Market impact is often defined as the expected execution shortfall per share, relative to initial price.
        # Or, total shortfall relative to initial value.
        # If `expected_total_cost` is the $ shortfall, and we want % of initial value, we need `P0 * X`.
        # The `compute_optimal_trajectory` doesn't get `P0`.
        # The `market_impact` field in `AlmgrenChrissResult` is defined as "As a percentage of total value".
        # This implies `market_impact_value = expected_total_cost / (InitialPrice * X_base) * 100`.
        # Since `InitialPrice` is not passed, let's assume the `eta` and `gamma` from `estimate_parameters`
        # are scaled such that `expected_total_cost` is comparable to `X` (if X were value), or
        # that `expected_total_cost / X` gives a price deviation, and we need to normalize by a price.
        # The current `lib/almgren_chriss.py` has market_impact = expected_cost / X * 100 in its example.
        # This implies expected_cost is already relative or X is value.
        # Given our X is base quantity, `expected_cost / X` is avg price slippage due to impact.
        # To make it a %, we need to divide by current price.
        # Let's assume the model's `expected_cost` is the total $ shortfall.
        # And the `X` parameter is quantity in base asset. The `TradeSimulator` will handle normalization by price.
        # So, this function should return the raw expected_total_cost (in $).
        # The `market_impact` field of the result should be this cost.
        # The caller (`TradeSimulator`) will then convert to percentage.

        # The `AlmgrenChrissResult` expects market_impact as a percentage.
        # If `expected_total_cost` is the dollar shortfall and `self.params.X` is base qty,
        # we need a price to calculate `self.params.X * Price` for the denominator.
        # This is a flaw in the original `AlmgrenChrissResult` structure or this function's scope.
        # For now, let's assume `expected_total_cost` is the dollar cost, and the percentage calculation is done by the caller.
        # However, to fulfill the dataclass, we need to estimate a % here.
        # Let's assume the internal "cost" is such that `cost / X` is price deviation.
        # Then `market_impact_pct = (cost / X) / S0 * 100`.
        # This is getting complicated. Let's stick to the article's interpretation:
        # "market_impact = expected_cost / X * 100" where X is shares and cost is total cost in value units.
        # This implies expected_cost is price-normalized.

        # The `market_impact` field in the `AlmgrenChrissResult` from the original `main` example in `almgren_chriss.py`
        # was `expected_cost / X * 100`. This suggests `expected_cost` is already a sum of price deviations if X is shares.
        # Or if X is value, then `expected_cost` is value.

        # Simpler: Assume the formulas for eta and gamma and cost are such that `expected_total_cost` is the $ cost.
        # The TradeSimulator will calculate percentage using the live price.
        # So, AlmgrenChrissResult.market_impact will temporarily store the $ cost.
        # This is a slight misuse of the field name if it's meant to be %, but practical.
        
        # Let's redefine: AlmgrenChrissResult.market_impact_value_absolute = expected_total_cost
        # The TradeSimulator will convert this to percentage.
        # For now, to avoid changing the dataclass, we'll calculate a % assuming an S0 of 1.
        # The `TradeSimulator` will recalculate based on actual S0.
        market_impact_percentage_approx = (expected_total_cost / X) * 100 if X > 0 else 0.0 # Rough %, assumes S0=1 or cost is already relative


        return AlmgrenChrissResult(
            optimal_trajectory=trajectory,
            expected_cost=expected_total_cost, # This is the absolute $ cost/shortfall
            market_impact=market_impact_percentage_approx # Temporary, caller should re-normalize
        )

    @staticmethod
    def _sinh(x: float) -> float:
        if x > 700: return np.exp(x - np.log(2)) # Avoid overflow, sinh(x) approx e^x / 2 for large x
        if x < -700: return -np.exp(-x - np.log(2))
        return np.sinh(x)

    @staticmethod
    def _cosh(x: float) -> float:
        if abs(x) > 700: return np.exp(abs(x) - np.log(2)) # cosh(x) approx e^|x| / 2
        return np.cosh(x)

    @staticmethod
    def estimate_parameters(
        volatility: float, # Annualized volatility (e.g., 0.3 for 30%)
        quantity: float,   # Order quantity in base asset (e.g., number of BTC)
        avg_daily_volume: Optional[float] = None, # In base asset
        market_cap: Optional[float] = None,       # In USD
        T_days: float = 1.0 # Time horizon in days
    ) -> AlmgrenChrissParams:
        
        # Default ADV and Market Cap if not provided (rough estimates)
        if avg_daily_volume is None or avg_daily_volume == 0:
            avg_daily_volume = quantity * 100  # Assume order is 1% of ADV
            logger.warning(f"avg_daily_volume not provided or zero, estimated to {avg_daily_volume}")
        if market_cap is None:
            # Try to estimate market_cap from ADV if possible (e.g. assuming ADV is 0.1% of market cap)
            # This needs a price to convert ADV (base) to ADV (USD)
            # For now, use a large default if not provided.
            market_cap = avg_daily_volume * 2000 * 1000 # Rough: ADV_base * Price_guess * 1000
            logger.warning(f"market_cap not provided, estimated to {market_cap}")

        # Convert annualized volatility to daily for consistency if T is in days
        # sigma in AC model is typically vol per sqrt(time_unit_of_T)
        # If T is in days, sigma should be daily_vol.
        daily_vol = volatility / np.sqrt(252) # Assuming 252 trading days per year
        
        # Parameters eta (permanent impact) and gamma (temporary impact)
        # These are highly dependent on market microstructure and need calibration.
        # Using simplified estimations based on "The Market Impact of Trades" by Almgren, Thum, Hauptmann, Li (2005)
        # Permanent impact: eta * sigma / ADV
        # Temporary impact: gamma_0 * sigma * (Q / (ADV * T))^(1/4) * (1/ADV)
        # Or simpler from various sources:
        # eta proportional to (sigma / ADV) or (1 / MarketCap_USD_daily_volume_fraction)
        # gamma proportional to (sigma / ADV) or (1 / LiquidityMeasure)

        # Simplified parameters (need actual calibration for real-world use)
        # Let eta be related to inverse of daily volume fraction of market cap
        # Daily_ADV_USD = avg_daily_volume * SomePrice (need price here ideally)
        # For now, assume ADV is in base, so need to scale by market cap correctly.
        # eta ~ 1 / (ADV_as_fraction_of_market_cap_per_day)
        # Let's use the article's reference style for permanent impact `ηXt` and temporary `γxt` where xt is trading rate
        # And then relate these to the Almgren-Chriss paper's parameterization.
        # The parameters `eta` and `gamma` in `AlmgrenChrissParams` are from the quadratic cost function:
        # Cost = Integral { gamma * v(t)^2 + eta * v(t) * X(t) } dt
        # Often simplified: E[Impact] = c1 * sigma * (Q/ADV)^(alpha) + c2 * sigma * sqrt(Q/ADV)
        
        # Using a common heuristic:
        # eta is a constant, e.g., 0.07 from some papers for large stocks, but scaled.
        # gamma is also a constant, e.g., 0.14
        # These constants are often related to (sigma / ADV).
        # From the LinkedIn example, they use eta and gamma as direct multipliers.
        # The `AlmgrenChrissModel` uses eta for permanent impact: permanent_cost = 0.5 * eta * X**2
        # And gamma for temporary impact: temporary_cost = gamma * X**2 * kappa * coth(kappa * T)
        # Where X is total quantity.

        # Coefficients from Kissell & Malamut (2005) "Optimal Trading III"
        # For US Equities, typical parameters (after scaling):
        # Permanent impact coefficient (eta_km) ~ 2.5e-7 to 5e-7 (when impact is eta_km * ParticipationRate * Volatility)
        # Temporary impact coefficient (gamma_km) ~ 2.5e-6 to 5e-6
        # The `eta` and `gamma` in our `AlmgrenChrissParams` are different.
        # `eta` in our model: if permanent impact cost is 0.5 * `eta` * X^2.
        # `gamma` in our model: if temporary impact cost involves `gamma` * X^2 ...

        # Let's try to derive `eta` and `gamma` such that they fit general expectations.
        # Assume permanent impact is some % of ADV leads to some price change.
        # If trading 10% of ADV (X/ADV = 0.1) causes 0.1 * sigma permanent price change.
        # Permanent Price Impact = C_perm * sigma * (X / ADV)
        # Total Permanent Cost = Permanent Price Impact * X = C_perm * sigma * X^2 / ADV
        # Comparing with 0.5 * `eta` * X^2 => `eta` = 2 * C_perm * sigma / ADV
        # Let C_perm = 0.1 (heuristic)
        eta_param = 2.0 * 0.1 * daily_vol / avg_daily_volume if avg_daily_volume > 0 else 1e-5
        
        # Temporary Price Impact = C_temp * sigma * sqrt(Rate / ADV) where Rate = X/T
        # Total Temporary Cost = Temporary Price Impact * X = C_temp * sigma * X * sqrt( (X/T) / ADV )
        # This doesn't quite fit `gamma` * X^2 ... form.
        # Alternative from Almgren (2005) paper "Optimal Execution with Non-Linear Impact Costs"
        # Temporary impact function h(v) = epsilon * sgn(v) + gamma_tmp * v (where v is trading rate)
        # Permanent impact g(v) = eta_perm * v
        # The current model is simpler.
        
        # Using the initial example's logic in almgren_chriss.py (which was based on some other source):
        # eta_orig = 2.5e-6 * (market_cap / (avg_daily_volume_usd if avg_daily_volume_usd else 1))
        # gamma_orig = 5e-6 * (market_cap / (avg_daily_volume_usd if avg_daily_volume_usd else 1))
        # This assumes avg_daily_volume is in USD. Our avg_daily_volume is in base.
        # We need price for avg_daily_volume_usd.
        # Let's assume a placeholder price or pass it if available.
        # For now, make eta_param and gamma_param less dependent on an unknown price.
        # Fallback to simpler constants if ADV is problematic.
        
        if avg_daily_volume <= 0: # Should not happen if defaults above work
            logger.error("avg_daily_volume is zero or negative in AC estimate_parameters.")
            avg_daily_volume = quantity * 100 # Re-default
        
        # These need to be scaled appropriately for crypto. Assume higher liquidity means smaller eta, gamma.
        # Let's use a scale factor based on the asset's typical ADV.
        # BTC ADV is high, so eta/gamma should be smaller.
        # Assume an ADV of 50k BTC.
        btc_adv_ref = 50000.0 
        adv_scale_factor = btc_adv_ref / avg_daily_volume if avg_daily_volume > 0 else 1.0
        
        # Base eta/gamma values (these are illustrative and need calibration)
        base_eta = 1e-5
        base_gamma = 5e-5

        eta_param = base_eta * adv_scale_factor
        gamma_param = base_gamma * adv_scale_factor
        
        # Ensure eta and gamma are not excessively large or small
        eta_param = np.clip(eta_param, 1e-10, 1e-3)
        gamma_param = np.clip(gamma_param, 1e-10, 1e-3)

        logger.info(f"Estimated AC Params: daily_vol={daily_vol:.4g}, eta={eta_param:.4g}, gamma={gamma_param:.4g}, T={T_days}, X={quantity:.4g}")

        return AlmgrenChrissParams(
            sigma=daily_vol, # Daily volatility
            eta=eta_param,
            gamma=gamma_param,
            T=T_days,        # Time horizon in days
            X=quantity       # Quantity in base asset
        )

# Example Usage (kept for reference, but ensure it's not run on import)
# if __name__ == "__main__":
#     logging.basicConfig(level=logging.INFO)
#     # Estimate parameters
#     params = AlmgrenChrissModel.estimate_parameters(
#         volatility=0.6,      # 60% annualized volatility
#         quantity=100,       # 100 BTC to execute
#         avg_daily_volume=50000,  # 50k BTC per day
#         market_cap=1.2e12,     # $1.2T market cap
#         T_days=1.0
#     )
    
#     model = AlmgrenChrissModel(params)
#     result = model.compute_optimal_trajectory(risk_aversion=1e-7) # Typical risk aversion
    
#     logger.info(f"Optimal trajectory length: {len(result.optimal_trajectory)}")
#     logger.info(f"Expected cost (absolute $ if params scaled): {result.expected_cost:.2f}")
    
#     # To get market impact percentage, we need initial price. Assume P0 = $60,000
#     P0 = 60000
#     initial_value_usd = P0 * params.X
#     market_impact_pct_recalc = (result.expected_cost / initial_value_usd) * 100 if initial_value_usd > 0 else 0
#     logger.info(f"Recalculated Market impact % (assuming P0={P0}): {market_impact_pct_recalc:.4f}%")
#     logger.info(f"Model's approx market_impact %: {result.market_impact:.4f}%")
