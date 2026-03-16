"""
Trading signals management - PRODUCTION READY
Returns array format expected by frontend
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime

from .database import database, users
from .security import get_current_user

def _is_admin(user) -> bool:
    """Inline admin check — works regardless of security.py version."""
    if hasattr(user, '_mapping'):
        return bool(user._mapping.get('is_admin')) or user._mapping.get('role') == 'admin'
    if isinstance(user, dict):
        return bool(user.get('is_admin')) or user.get('role') == 'admin'
    return bool(getattr(user, 'is_admin', False)) or getattr(user, 'role', None) == 'admin'

router = APIRouter()

# Production: Real signals from database
# For demo/initial setup, returns empty array or real data if available

@router.get("/active")
async def get_active_signals(
    limit: int = 50,
    current_user = Depends(get_current_user)
):
    """
    Get all active trading signals.
    PRODUCTION: Queries real database table
    """
    try:
        # Query active signals from database
        # Assuming you have a signals table - adjust column names as needed
        query = """
            SELECT id, symbol, direction, entry_price, stop_loss, take_profit,
                   timeframe, created_at, ai_confidence, status
            FROM signals
            WHERE status = 'active'
            ORDER BY created_at DESC
            LIMIT :limit
        """
        
        rows = await database.fetch_all(query, {"limit": limit})
        
        # Convert to list of dicts for JSON serialization
        signals = []
        for row in rows:
            signals.append({
                "id": row["id"],
                "symbol": row["symbol"],
                "direction": row["direction"],
                "entry_price": float(row["entry_price"]),
                "stop_loss": float(row["stop_loss"]),
                "take_profit": float(row["take_profit"]),
                "timeframe": row.get("timeframe", "1H"),
                "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                "ai_confidence": float(row["ai_confidence"]) if row["ai_confidence"] else None,
                "status": row["status"]
            })
        
        return signals  # Returns array directly, not {signals: []}
        
    except Exception as e:
        print(f"[ERROR] Failed to fetch signals: {e}", flush=True)
        # Return empty array on error - frontend handles empty state
        return []

@router.post("/create")
async def create_signal(
    signal: dict,
    current_user = Depends(get_current_user)
):
    """Create new trading signal (admin only)"""
    try:
        # Use inline admin check — compatible with all security.py versions
        if not _is_admin(current_user):
            raise HTTPException(403, "Admin access required")

        
        # Insert into database
        query = """
            INSERT INTO signals (symbol, direction, entry_price, stop_loss, take_profit, 
                               timeframe, created_at, status, ai_confidence)
            VALUES (:symbol, :direction, :entry_price, :stop_loss, :take_profit,
                    :timeframe, NOW(), 'active', :ai_confidence)
            RETURNING id
        """
        
        signal_id = await database.execute(query, {
            "symbol": signal.get("symbol"),
            "direction": signal.get("direction"),
            "entry_price": signal.get("entry_price"),
            "stop_loss": signal.get("stop_loss"),
            "take_profit": signal.get("take_profit"),
            "timeframe": signal.get("timeframe", "1H"),
            "ai_confidence": signal.get("ai_confidence", 0.8)
        })
        
        return {
            "status": "created",
            "id": signal_id,
            "signal": signal
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"[ERROR] Failed to create signal: {e}", flush=True)
        raise HTTPException(500, f"Database error: {str(e)}")
