
import httpx
import json
import base64
from typing import Optional
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.api_key = settings.OPENROUTER_API_KEY
        self.model = settings.OPENROUTER_MODEL
        self.vision_model = settings.OPENROUTER_VISION_MODEL
        self.base_url = "https://openrouter.ai/api/v1"

    async def analyze_performance(self, trades: list, account_balance: Optional[float] = None) -> dict:
        """Analyze trading performance using AI"""
        if not self.api_key:
            raise ValueError("AI service not configured")

        prompt = f"""
        Analyze these trading statistics and provide professional feedback:

        Trades: {json.dumps(trades)}
        Account Balance: {account_balance or 'N/A'}

        Provide analysis in JSON format with these keys:
        - summary (overall assessment)
        - strengths (array of 3 strengths)
        - weaknesses (array of 3 areas to improve)
        - risk_assessment (rating 1-10)
        - recommendations (array of 3 actionable tips)
        - win_rate_analysis
        - psychology_feedback
        """

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://pipways.com",
                    "X-Title": "Pipways AI Analysis"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "You are a professional trading analyst. Provide detailed, actionable feedback."},
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": 1500,
                    "temperature": 0.7
                }
            )

            if response.status_code != 200:
                raise Exception(f"AI service error: {response.text}")

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Try to parse JSON, fallback to raw text
            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                return json.loads(content.strip())
            except:
                return {"raw_analysis": content, "structured": False}

    async def analyze_chart(self, image_bytes: bytes, pair: str, timeframe: str, additional_info: str = "") -> dict:
        """Analyze chart image using vision model"""
        if not self.api_key:
            raise ValueError("AI service not configured")

        image_base64 = base64.b64encode(image_bytes).decode()

        prompt = f"""Analyze this {pair} {timeframe} chart. {additional_info}

        Provide analysis in JSON format:
        - signal (BUY, SELL, or NEUTRAL)
        - confidence (0-100)
        - entry_zone (price level)
        - stop_loss (price level)
        - take_profit (array of price levels)
        - risk_reward (ratio like "1:2")
        - summary (brief explanation)
        - market_structure (trend description)
        - key_levels (support/resistance)
        """

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://pipways.com",
                    "X-Title": "Pipways Chart Analysis"
                },
                json={
                    "model": self.vision_model,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}}
                            ]
                        }
                    ],
                    "max_tokens": 1500
                }
            )

            if response.status_code != 200:
                raise Exception(f"AI service error: {response.text}")

            result = response.json()
            content = result["choices"][0]["message"]["content"]

            # Try to parse JSON
            try:
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]
                analysis = json.loads(content.strip())
                return {
                    "analysis": analysis,
                    "formatted": self._format_chart_analysis(analysis),
                    "raw": content
                }
            except:
                return {
                    "analysis": {"raw": content},
                    "formatted": content,
                    "raw": content
                }

    async def chat(self, message: str, context: str = "trading") -> str:
        """AI Mentor chat"""
        if not self.api_key:
            raise ValueError("AI service not configured")

        contexts = {
            "trading": "You are a professional trading mentor with 20+ years experience.",
            "psychology": "You are a trading psychology expert helping with emotional control and discipline.",
            "risk_management": "You are a risk management specialist focusing on capital preservation.",
            "technical_analysis": "You are a technical analysis expert.",
            "strategy": "You are a trading strategy developer."
        }

        system_prompt = contexts.get(context, contexts["trading"])

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://pipways.com",
                    "X-Title": "Pipways AI Mentor"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": message}
                    ],
                    "max_tokens": 800,
                    "temperature": 0.7
                }
            )

            if response.status_code != 200:
                raise Exception(f"AI service error: {response.text}")

            result = response.json()
            return result["choices"][0]["message"]["content"]

    def _format_chart_analysis(self, data: dict) -> str:
        """Format chart analysis into readable text"""
        signal = data.get('signal', 'UNKNOWN')
        emoji = "🟢" if "BUY" in signal.upper() else "🔴" if "SELL" in signal.upper() else "⚪"

        return f"""
{emoji} SIGNAL: {signal}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📈 Entry: {data.get('entry_zone', 'N/A')}
🛑 Stop Loss: {data.get('stop_loss', 'N/A')}
🎯 Take Profits: {', '.join(data.get('take_profit', []))}
⚖️ Risk/Reward: {data.get('risk_reward', 'N/A')}
🎲 Confidence: {data.get('confidence', 'N/A')}%

📝 Summary:
{data.get('summary', 'No summary available')}

🏗️ Structure: {data.get('market_structure', 'N/A')}
"""

ai_service = AIService()
