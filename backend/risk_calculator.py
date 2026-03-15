"""
Position sizing and risk calculation tools.
FIXED: Returns all fields expected by frontend.
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from .security import get_current_user

router = APIRouter()

class RiskCalculationRequest(BaseModel):
    account_balance: float
    risk_percent: float
    entry_price: float
    stop_loss: float
    take_profit: Optional[float] = None
    symbol: Optional[str] = "EURUSD"

@router.post("/calculate")
async def calculate_risk(
    request: RiskCalculationRequest,
    current_user = Depends(get_current_user)
):
    """
    Calculate position size based on risk parameters.
    FIXED: Returns complete fields matching frontend expectations.
    """
    try:
        account_balance = request.account_balance
        risk_percent = request.risk_percent
        entry_price = request.entry_price
        stop_loss = request.stop_loss
        take_profit = request.take_profit or 0

        # Validate inputs
        if account_balance <= 0:
            raise HTTPException(400, "Account balance must be positive")
        if risk_percent <= 0 or risk_percent > 100:
            raise HTTPException(400, "Risk percent must be between 0 and 100")
        if entry_price <= 0:
            raise HTTPException(400, "Entry price must be positive")
        if stop_loss <= 0:
            raise HTTPException(400, "Stop loss must be positive")
        if entry_price == stop_loss:
            raise HTTPException(400, "Entry price cannot equal stop loss")

        # Calculate risk metrics
        risk_amount = account_balance * (risk_percent / 100)
        price_risk = abs(entry_price - stop_loss)

        # For forex: 1 lot = 100,000 units, pip value varies
        # Standard calculation for forex
        position_size = risk_amount / price_risk

        # Convert to standard lot sizes
        # Standard lot = 1.0, Mini = 0.1, Micro = 0.01
        if position_size >= 1:
            position_size_rounded = round(position_size, 2)
        else:
            position_size_rounded = round(position_size, 2)

        # Ensure minimum lot size (0.01)
        if position_size_rounded < 0.01:
            position_size_rounded = 0.01

        # Calculate units (1 lot = 100,000 units for standard forex)
        units = int(position_size * 100000)

        # Calculate max loss in currency
        max_loss = price_risk * position_size

        # Calculate risk:reward ratio
        if take_profit and take_profit > 0:
            reward = abs(take_profit - entry_price)
            risk_reward_ratio = safe_div(reward, price_risk, 0)
        else:
            risk_reward_ratio = 0

        # Determine recommendation
        recommendation = "valid"
        warnings = []

        if risk_percent > 2:
            recommendation = "high_risk"
            warnings.append("Risking more than 2% per trade is dangerous")

        if risk_reward_ratio > 0 and risk_reward_ratio < 1.5:
            recommendation = "poor_risk_reward"
            warnings.append("Risk/Reward ratio should be at least 1:1.5")
        elif risk_reward_ratio >= 2:
            pass  # Good R:R

        if position_size_rounded < 0.01:
            recommendation = "below_minimum_lot"
            warnings.append("Position size below broker minimum (0.01 lots)")

        return {
            "position_size": position_size_rounded,
            "units": units,
            "risk_amount": round(risk_amount, 2),
            "risk_percent": risk_percent,
            "max_loss": round(max_loss, 2),
            "risk_reward_ratio": round(risk_reward_ratio, 2),
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "take_profit": take_profit,
            "price_risk": round(price_risk, 5),
            "recommendation": recommendation,
            "warnings": warnings,
            "is_valid": len(warnings) == 0 or recommendation == "valid"
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Calculation error: {str(e)}")

def safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    return numerator / denominator if denominator != 0 else default

@router.get("/history")
async def get_risk_history(
    limit: int = 10,
    current_user = Depends(get_current_user)
):
    """Get recent risk calculations for the user."""
    # This is a placeholder - in production, store calculations in database
    return []
