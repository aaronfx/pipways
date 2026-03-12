def calculate_metrics(df):

    trades = len(df)

    wins = df[df["profit"] > 0]
    losses = df[df["profit"] <= 0]

    win_rate = round(len(wins) / trades * 100, 2)

    gross_profit = wins["profit"].sum()
    gross_loss = abs(losses["profit"].sum())

    profit_factor = round(gross_profit / gross_loss, 2) if gross_loss else 0

    avg_win = wins["profit"].mean() if len(wins) else 0
    avg_loss = abs(losses["profit"].mean()) if len(losses) else 0

    risk_reward = round(avg_win / avg_loss, 2) if avg_loss else 0

    expectancy = round(
        (win_rate / 100 * avg_win) - ((1 - win_rate / 100) * avg_loss),
        2
    )

    return {
        "trades": trades,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "risk_reward": risk_reward,
        "expectancy": expectancy
    }
