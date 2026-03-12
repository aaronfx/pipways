import os
from typing import Dict, Any, Optional
import openai
from fastapi import HTTPException

openai.api_key = os.getenv("OPENAI_API_KEY")

async def analyze_trading_data(data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        if not openai.api_key:
            return {
                "analysis": "AI analysis unavailable - no API key configured",
                "recommendations": [],
                "risk_assessment": "unknown"
            }

        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional trading analyst. Analyze the provided trading data and give structured insights."
                },
                {
                    "role": "user",
                    "content": f"Analyze this trading data: {data}"
                }
            ],
            temperature=0.7,
            max_tokens=500
        )

        analysis = response.choices[0].message.content
        return {
            "analysis": analysis,
            "recommendations": extract_recommendations(analysis),
            "risk_assessment": extract_risk_level(analysis)
        }
    except Exception as e:
        return {
            "analysis": f"Analysis error: {str(e)}",
            "recommendations": [],
            "risk_assessment": "error"
        }

def extract_recommendations(analysis_text: str) -> list:
    recommendations = []
    lines = analysis_text.split("
")
    for line in lines:
        if any(keyword in line.lower() for keyword in ["recommend", "suggest", "advice", "consider"]):
            recommendations.append(line.strip())
    return recommendations[:5]

def extract_risk_level(analysis_text: str) -> str:
    text_lower = analysis_text.lower()
    if "high risk" in text_lower or "high" in text_lower:
        return "high"
    elif "low risk" in text_lower or "low" in text_lower:
        return "low"
    elif "medium risk" in text_lower or "medium" in text_lower:
        return "medium"
    return "unknown"

async def generate_content(prompt: str, content_type: str = "general") -> str:
    try:
        if not openai.api_key:
            return "AI content generation unavailable - no API key configured"

        system_prompts = {
            "blog": "You are a professional financial blogger. Write engaging, informative content about trading and investing.",
            "course": "You are an expert trading instructor. Create educational content that is clear and actionable.",
            "seo": "You are an SEO expert. Generate optimized meta titles and descriptions.",
            "general": "You are a helpful trading assistant."
        }

        response = await openai.ChatCompletion.acreate(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": system_prompts.get(content_type, system_prompts["general"])
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.7,
            max_tokens=1000
        )

        return response.choices[0].message.content
    except Exception as e:
        return f"Content generation error: {str(e)}"
