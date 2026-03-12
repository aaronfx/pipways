@router.post("/analyze-performance")
async def analyze_performance(
    file: UploadFile = File(...),
    current_user: Optional[dict] = Depends(get_current_user_optional)
):

    import pandas as pd
    import io

    try:

        contents = await file.read()

        # CSV
        if file.filename.endswith(".csv"):

            df = pd.read_csv(io.BytesIO(contents))

        # Excel
        elif file.filename.endswith(".xlsx"):

            df = pd.read_excel(io.BytesIO(contents))

        else:

            raise HTTPException(
                status_code=400,
                detail="Unsupported file type"
            )

        # normalize column names
        df.columns = [c.lower() for c in df.columns]

        if "profit" not in df.columns:

            raise HTTPException(
                status_code=400,
                detail="Profit column not detected"
            )

        trades = len(df)

        wins = df[df["profit"] > 0]
        losses = df[df["profit"] <= 0]

        win_rate = round(len(wins) / trades * 100, 2)

        gross_profit = wins["profit"].sum()
        gross_loss = abs(losses["profit"].sum())

        profit_factor = round(gross_profit / gross_loss, 2) if gross_loss else 0

        avg_win = wins["profit"].mean() if len(wins) else 0
        avg_loss = abs(losses["profit"].mean()) if len(losses) else 0

        rr = round(avg_win / avg_loss, 2) if avg_loss else 0

        summary = f"""
Trades: {trades}
Win Rate: {win_rate}%
Profit Factor: {profit_factor}
Risk Reward: {rr}
"""

        prompt = f"""
You are a professional trading coach.

Analyze this trading performance:

{summary}

Return structured response:

Performance Summary
Key Issues
Strengths
Improvement Plan
Recommended Courses
Mentor Advice
"""

        ai_text = await call_openrouter(
            [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        )

        return {

            "summary": summary,
            "analysis": ai_text,

            "metrics": {
                "trades": trades,
                "win_rate": win_rate,
                "profit_factor": profit_factor,
                "risk_reward": rr
            }

        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
