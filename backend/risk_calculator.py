from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from sqlalchemy import insert, select, desc, func
from datetime import datetime

from .database import database, risk_calculations, signals
from .security import get_current_user, get_current_admin

router = APIRouter(prefix="/risk", tags=["risk_calculator"])

class RiskCalculationRequest(BaseModel):
    account_balance: float = Field(..., gt=0)
    risk_percent: float = Field(..., gt=0, le=5)
    entry_price: float
    stop_loss: float
    take_profit: float
    signal_id: Optional[int] = None

class RiskCalculationResponse(BaseModel):
    position_size: float
    max_loss: float
    risk_reward_ratio: float
    units: float
    pip_value: float
    recommendation: str

@router.post("/calculate", response_model=RiskCalculationResponse)
async def calculate_risk(
    data: RiskCalculationRequest,
    current_user: Optional[dict] = Depends(get_current_user)
):
    risk_amount = data.account_balance * (data.risk_percent / 100)
    sl_distance = abs(data.entry_price - data.stop_loss)

    if sl_distance == 0:
        raise HTTPException(status_code=400, detail="Entry and Stop Loss cannot be same")

    pip_value_per_lot = 10
    pips_at_risk = sl_distance / 0.0001
    position_size = risk_amount / (pips_at_risk * pip_value_per_lot)

    tp_distance = abs(data.take_profit - data.entry_price)
    risk_reward_ratio = tp_distance / sl_distance

    recommendation = "valid"
    if risk_reward_ratio < 1.5:
        recommendation = "poor_risk_reward"
    elif data.risk_percent > 2:
        recommendation = "high_risk"
    elif position_size < 0.01:
        recommendation = "below_minimum_lot"

    if current_user:
        query = insert(risk_calculations).values(
            user_id=current_user["id"],
            signal_id=data.signal_id,
            account_balance=data.account_balance,
            risk_percent=data.risk_percent,
            entry_price=data.entry_price,
            stop_loss=data.stop_loss,
            position_size=position_size,
            max_loss=risk_amount,
            risk_reward_ratio=risk_reward_ratio,
            calculated_at=datetime.utcnow()
        )
        await database.execute(query)

    return RiskCalculationResponse(
        position_size=round(position_size, 2),
        max_loss=round(risk_amount, 2),
        risk_reward_ratio=round(risk_reward_ratio, 2),
        units=round(position_size * 100000, 0),
        pip_value=round(pip_value_per_lot * position_size, 2),
        recommendation=recommendation
    )

@router.get("/history")
async def get_calculation_history(
    limit: int = 50,
    current_user: dict = Depends(get_current_user)
):
    query = select(risk_calculations).where(
        risk_calculations.c.user_id == current_user["id"]
    ).order_by(desc(risk_calculations.c.calculated_at)).limit(limit)

    results = await database.fetch_all(query)
    return [dict(r) for r in results]
