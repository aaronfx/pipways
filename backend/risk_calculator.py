"""
Position sizing and risk calculation tools.
"""
from fastapi import APIRouter, Depends
from backend.security import get_current_user

router = APIRouter()

@router.post("/calculate")
async def calculate_risk(
    account_balance: float,
    risk_percent: float,
    entry_price: float,
    stop_loss: float,
    current_user = Depends(get_current_user)
):
    """Calculate position size based on risk parameters."""
    risk_amount = account_balance * (risk_percent / 100)
    price_risk = abs(entry_price - stop_loss)

    if price_risk == 0:
        return {"error": "Invalid stop loss"}

    position_size = risk_amount / price_risk
    return {
        "position_size": round(position_size, 2),
        "risk_amount": risk_amount,
        "risk_percent": risk_percent
    }
