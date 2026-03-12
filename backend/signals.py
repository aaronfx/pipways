from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, insert, update, delete, desc
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address

from .database import database, signals, users
from .security import get_current_user, get_current_admin
from .notifications import notify_new_signal

router = APIRouter(prefix="/signals", tags=["signals"])
limiter = Limiter(key_func=get_remote_address)

class SignalCreate(BaseModel):
    title: str
    description: str
    asset: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float

class SignalUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    result: Optional[str] = None

class SignalResponse(BaseModel):
    id: int
    title: str
    description: str
    asset: str
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    status: str
    result: str
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

@router.get("/", response_model=List[SignalResponse])
@limiter.limit("30/minute")
async def get_signals(
    request: Request,
    status: Optional[str] = Query(None),
    asset: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    query = select(signals).order_by(desc(signals.c.created_at))

    if status:
        query = query.where(signals.c.status == status)
    if asset:
        query = query.where(signals.c.asset == asset)

    query = query.limit(limit).offset(offset)
    results = await database.fetch_all(query)
    return [dict(row) for row in results]

@router.get("/{signal_id}", response_model=SignalResponse)
async def get_signal(signal_id: int):
    query = select(signals).where(signals.c.id == signal_id)
    result = await database.fetch_one(query)
    if not result:
        raise HTTPException(status_code=404, detail="Signal not found")
    return dict(result)

@router.post("/", response_model=SignalResponse)
async def create_signal(
    signal_data: SignalCreate,
    current_user: dict = Depends(get_current_admin)
):
    query = insert(signals).values(
        title=signal_data.title,
        description=signal_data.description,
        asset=signal_data.asset,
        direction=signal_data.direction,
        entry_price=signal_data.entry_price,
        stop_loss=signal_data.stop_loss,
        take_profit=signal_data.take_profit,
        status="ACTIVE",
        result="PENDING",
        created_by=current_user["id"],
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    signal_id = await database.execute(query)

    # Notify subscribers
    signal = await database.fetch_one(select(signals).where(signals.c.id == signal_id))
    await notify_new_signal(dict(signal))

    return dict(signal)

@router.put("/{signal_id}", response_model=SignalResponse)
async def update_signal(
    signal_id: int,
    signal_update: SignalUpdate,
    current_user: dict = Depends(get_current_admin)
):
    query = select(signals).where(signals.c.id == signal_id)
    existing = await database.fetch_one(query)
    if not existing:
        raise HTTPException(status_code=404, detail="Signal not found")

    update_data = signal_update.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()

    query = update(signals).where(signals.c.id == signal_id).values(**update_data)
    await database.execute(query)

    query = select(signals).where(signals.c.id == signal_id)
    result = await database.fetch_one(query)
    return dict(result)

@router.delete("/{signal_id}")
async def delete_signal(
    signal_id: int,
    current_user: dict = Depends(get_current_admin)
):
    query = delete(signals).where(signals.c.id == signal_id)
    result = await database.execute(query)
    if result == 0:
        raise HTTPException(status_code=404, detail="Signal not found")
    return {"message": "Signal deleted successfully"}
