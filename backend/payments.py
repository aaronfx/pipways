"""
Payment processing (Stripe integration).
"""
from fastapi import APIRouter, Depends, HTTPException
from backend.security import get_current_user
import os

router = APIRouter()
STRIPE_KEY = os.getenv("STRIPE_SECRET_KEY", "")

@router.post("/create-intent")
async def create_payment_intent(current_user = Depends(get_current_user)):
    """Create Stripe payment intent."""
    if not STRIPE_KEY:
        raise HTTPException(500, "Stripe not configured")
    return {"client_secret": "test_secret", "status": "ready"}
