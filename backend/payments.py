import stripe
import os
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, insert, update
from pydantic import BaseModel
from datetime import datetime

from .database import database, subscriptions, users
from .security import get_current_user

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

router = APIRouter(prefix="/payments", tags=["payments"])

class CreateSubscriptionRequest(BaseModel):
    price_id: str
    tier: str

@router.post("/create-subscription")
async def create_subscription(
    request: CreateSubscriptionRequest,
    current_user: dict = Depends(get_current_user)
):
    query = select(subscriptions).where(subscriptions.c.user_id == current_user["id"])
    existing = await database.fetch_one(query)

    try:
        if existing and existing["stripe_customer_id"]:
            customer_id = existing["stripe_customer_id"]
        else:
            customer = stripe.Customer.create(
                email=current_user["email"],
                metadata={"user_id": current_user["id"]}
            )
            customer_id = customer.id

            if existing:
                query = update(subscriptions).where(
                    subscriptions.c.user_id == current_user["id"]
                ).values(stripe_customer_id=customer_id)
            else:
                query = insert(subscriptions).values(
                    user_id=current_user["id"],
                    stripe_customer_id=customer_id,
                    tier="free"
                )
            await database.execute(query)

        subscription = stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": request.price_id}],
            payment_behavior="default_incomplete",
            expand=["latest_invoice.payment_intent"],
        )

        return {
            "subscription_id": subscription.id,
            "client_secret": subscription.latest_invoice.payment_intent.client_secret
        }

    except stripe.error.StripeError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "invoice.payment_succeeded":
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]

        query = update(subscriptions).where(
            subscriptions.c.stripe_customer_id == customer_id
        ).values(
            status="active",
            stripe_subscription_id=subscription["id"],
            current_period_end=datetime.fromtimestamp(subscription["current_period_end"])
        )
        await database.execute(query)

    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        customer_id = subscription["customer"]

        query = update(subscriptions).where(
            subscriptions.c.stripe_customer_id == customer_id
        ).values(status="cancelled", tier="free")
        await database.execute(query)

    return {"status": "success"}

async def require_subscription(tier: str):
    async def checker(current_user: dict = Depends(get_current_user)):
        query = select(subscriptions).where(subscriptions.c.user_id == current_user["id"])
        sub = await database.fetch_one(query)

        if not sub or sub["tier"] not in [tier, "vip"] or sub["status"] != "active":
            raise HTTPException(status_code=403, detail=f"{tier} subscription required")
        return current_user
    return checker
