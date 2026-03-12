from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import insert, select
from pydantic import BaseModel
from datetime import datetime
import os
import aiohttp

from .database import database, ai_screening_logs, signals
from .security import get_current_admin
from .ai_services import generate_content

router = APIRouter(prefix="/ai/screening", tags=["ai_screening"])

ALPHA_VANTAGE_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

async def get_market_sentiment(asset: str):
    if not ALPHA_VANTAGE_KEY:
        return {"sentiment": "neutral", "score": 50}

    url = f"https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={asset}&apikey={ALPHA_VANTAGE_KEY}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            data = await response.json()
            return {
                "sentiment": data.get("feed", [{}])[0].get("overall_sentiment_label", "neutral"),
                "score": float(data.get("feed", [{}])[0].get("overall_sentiment_score", 0)) * 100
            }

async def get_volatility_index():
    return {"vix": 15.5, "condition": "low"}

@router.post("/screen-signal/{signal_id}")
async def screen_signal(
    signal_id: int,
    current_user: dict = Depends(get_current_admin)
):
    query = select(signals).where(signals.c.id == signal_id)
    signal = await database.fetch_one(query)

    if not signal:
        raise HTTPException(status_code=404, detail="Signal not found")

    sentiment_data = await get_market_sentiment(signal["asset"])
    volatility = await get_volatility_index()

    prompt = f"""
    Analyze this trading signal:
    Asset: {signal["asset"]}
    Direction: {signal["direction"]}
    Entry: {signal["entry_price"]}
    SL: {signal["stop_loss"]} ({abs(signal["entry_price"] - signal["stop_loss"])/0.0001} pips)
    TP: {signal["take_profit"]} (R:R = {abs(signal["take_profit"] - signal["entry_price"]) / abs(signal["entry_price"] - signal["stop_loss"]):.2f})

    Market:
    - Sentiment: {sentiment_data["sentiment"]} ({sentiment_data["score"]:.0f}/100)
    - Volatility: {volatility["condition"]}

    Return: 1. RECOMMENDATION: (APPROVE/REJECT/CAUTION) 2. REASONING:
    """

    analysis = await generate_content(prompt)

    lines = analysis.split("\n")
    recommendation = "caution"
    reasoning = analysis

    for line in lines:
        if "RECOMMENDATION:" in line:
            if "APPROVE" in line:
                recommendation = "approve"
            elif "REJECT" in line:
                recommendation = "reject"
        if "REASONING:" in line:
            reasoning = line.split("REASONING:")[1].strip()

    query = insert(ai_screening_logs).values(
        signal_id=signal_id,
        market_condition=volatility["condition"],
        news_sentiment=sentiment_data["sentiment"],
        volatility_score=sentiment_data["score"],
        ai_recommendation=recommendation,
        reasoning=reasoning,
        screened_at=datetime.utcnow()
    )
    await database.execute(query)

    return {
        "signal_id": signal_id,
        "recommendation": recommendation,
        "reasoning": reasoning,
        "market_sentiment": sentiment_data["sentiment"],
        "volatility": volatility["condition"]
    }

@router.get("/history/{signal_id}")
async def get_screening_history(signal_id: int):
    query = select(ai_screening_logs).where(
        ai_screening_logs.c.signal_id == signal_id
    ).order_by(ai_screening_logs.c.screened_at.desc())

    results = await database.fetch_all(query)
    return [dict(r) for r in results]
