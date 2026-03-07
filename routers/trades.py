from fastapi import APIRouter, Form, Depends, HTTPException
from typing import Optional
from auth import get_current_user
from database import get_db

router = APIRouter()

@router.get("/")
async def get_trades(current_user: str = Depends(get_current_user), conn=Depends(get_db)):
    """Get all trades for current user"""
    try:
        user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
        trades = await conn.fetch(
            "SELECT * FROM trades WHERE user_id = $1 ORDER BY created_at DESC",
            user["id"]
        )
        return [dict(t) for t in trades]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch trades: {str(e)}")

@router.post("/")
async def create_trade(
    pair: str = Form(...),
    direction: str = Form(...),
    pips: float = Form(...),
    grade: str = Form(...),
    entry_price: Optional[float] = Form(None),
    exit_price: Optional[float] = Form(None),
    current_user: str = Depends(get_current_user),
    conn=Depends(get_db)
):
    """Create new trade entry"""
    try:
        user = await conn.fetchrow("SELECT id FROM users WHERE email = $1", current_user)
        trade_id = await conn.fetchval("""
            INSERT INTO trades (user_id, pair, direction, entry_price, exit_price, pips, grade)
            VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id
        """, user["id"], pair.upper(), direction, entry_price, exit_price, pips, grade)

        return {"id": trade_id, "message": "Trade saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save trade: {str(e)}")
