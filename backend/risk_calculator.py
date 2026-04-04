"""
Position sizing and risk calculation tools.

Changes from original:
  - FIXED: Correct lot size formula: risk_amount / (stop_pips * pip_value_per_lot)
           Old broken formula risk_amount / price_risk gave 20,000 lots instead of 0.20.
  - ADDED: INSTRUMENT_CONFIG — pip size and value per lot for forex, JPY, gold, silver, oil, indices.
  - FIXED: /calculate no longer requires auth — public calculator works without a token.
           If a token IS present the calculation is saved to history automatically.
  - ADDED: get_optional_user() — returns user if authenticated, None if not, never raises 401.
  - ADDED: risk_calculations table migration runs once at startup.
  - FIXED: /history now queries the DB instead of returning [].
  - FIXED: is_valid = recommendation == "valid" (was: len(warnings)==0 or rec=="valid").
  - ADDED: stop_pips and pip_value_per_lot in response so frontend can show them.
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from typing import Optional
from .security import get_current_user
from .database import database

router = APIRouter()

# ── Instrument configurations ─────────────────────────────────────────────────
# pip_size      : price movement of 1 pip for this instrument
# pip_value     : USD P&L per 1 standard lot per 1 pip movement
# contract_size : units per 1 standard lot
INSTRUMENT_CONFIG = {
    'forex':   {'pip_size': 0.0001, 'pip_value': 10.0,  'contract_size': 100000, 'label': 'Forex (EUR/USD, GBP/USD, AUD/USD…)'},
    'jpy':     {'pip_size': 0.01,   'pip_value': 10.0,  'contract_size': 100000, 'label': 'JPY Pairs (USD/JPY, EUR/JPY, GBP/JPY…)'},
    'gold':    {'pip_size': 0.01,   'pip_value': 1.0,   'contract_size': 100,    'label': 'Gold (XAU/USD)'},
    'silver':  {'pip_size': 0.001,  'pip_value': 50.0,  'contract_size': 5000,   'label': 'Silver (XAG/USD)'},
    'oil':     {'pip_size': 0.01,   'pip_value': 10.0,  'contract_size': 1000,   'label': 'Oil (WTI / BRENT)'},
    'indices': {'pip_size': 1.0,    'pip_value': 1.0,   'contract_size': 1,      'label': 'Indices (S&P500, NAS100, US30…)'},
}

# ── Risk calculations table migration ─────────────────────────────────────────
_RISK_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS risk_calculations (
    id               SERIAL PRIMARY KEY,
    user_id          INTEGER NOT NULL,
    account_balance  FLOAT   NOT NULL,
    risk_percent     FLOAT   NOT NULL,
    entry_price      FLOAT   NOT NULL,
    stop_loss        FLOAT   NOT NULL,
    take_profit      FLOAT   DEFAULT 0,
    instrument_type  VARCHAR(20) DEFAULT 'forex',
    symbol           VARCHAR(20) DEFAULT '',
    position_size    FLOAT   NOT NULL,
    risk_reward_ratio FLOAT  DEFAULT 0,
    calculated_at    TIMESTAMP DEFAULT NOW()
)
"""

_risk_table_ready = False

async def _ensure_risk_table():
    global _risk_table_ready
    if _risk_table_ready:
        return
    try:
        await database.execute(_RISK_TABLE_SQL)
        _risk_table_ready = True
    except Exception:
        pass  # Table may already exist or DB not yet ready


# ── Optional auth helper ──────────────────────────────────────────────────────
async def get_optional_user(request: Request):
    """
    Returns the authenticated user if a valid Bearer token is present.
    Returns None silently if no token or token is invalid.
    Never raises 401 — safe to use on public endpoints.
    """
    try:
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return None
        token = auth[7:]
        from jose import jwt, JWTError
        from .database import SECRET_KEY, ALGORITHM, users
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get('sub')
        if not email:
            return None
        query = users.select().where(users.c.email == email)
        return await database.fetch_one(query)
    except Exception:
        return None


# ── Request / response models ─────────────────────────────────────────────────
class RiskCalculationRequest(BaseModel):
    account_balance: float
    risk_percent: float
    entry_price: float
    stop_loss: float
    take_profit: Optional[float] = None
    instrument_type: Optional[str] = 'forex'
    symbol: Optional[str] = 'EURUSD'


# ── Routes ────────────────────────────────────────────────────────────────────
@router.post("/calculate")
async def calculate_risk(
    request: RiskCalculationRequest,
    current_user=Depends(get_optional_user),
):
    """
    Calculate position size. Authentication is optional.
    The public risk calculator page works without a token.
    When a valid token is present the result is saved to the user's history.
    """
    await _ensure_risk_table()

    try:
        account_balance  = request.account_balance
        risk_percent     = request.risk_percent
        entry_price      = request.entry_price
        stop_loss        = request.stop_loss
        take_profit      = request.take_profit or 0
        instrument_type  = (request.instrument_type or 'forex').lower()

        # ── Input validation ─────────────────────────────────────────────
        if account_balance <= 0:
            raise HTTPException(400, "Account balance must be positive")
        if risk_percent <= 0 or risk_percent > 100:
            raise HTTPException(400, "Risk percent must be between 0 and 100")
        if entry_price <= 0:
            raise HTTPException(400, "Entry price must be positive")
        if stop_loss <= 0:
            raise HTTPException(400, "Stop loss must be positive")
        if entry_price == stop_loss:
            raise HTTPException(400, "Entry price cannot equal stop loss")

        config = INSTRUMENT_CONFIG.get(instrument_type, INSTRUMENT_CONFIG['forex'])
        pip_size         = config['pip_size']
        pip_value_per_lot = config['pip_value']
        contract_size    = config['contract_size']

        # ── Core calculations ─────────────────────────────────────────────
        risk_amount = account_balance * (risk_percent / 100)
        price_risk  = abs(entry_price - stop_loss)
        stop_pips   = price_risk / pip_size

        # FIXED: correct position sizing formula.
        # Old: risk_amount / price_risk  → 20,000 lots for a typical EUR/USD trade.
        # New: risk_amount / (stop_pips × pip_value_per_lot) → 0.20 lots ✓
        raw_position   = risk_amount / (stop_pips * pip_value_per_lot)
        position_size  = max(0.01, round(raw_position, 2))

        units    = int(position_size * contract_size)
        max_loss = stop_pips * pip_value_per_lot * position_size

        # ── Risk:Reward ───────────────────────────────────────────────────
        risk_reward_ratio = 0.0
        if take_profit and take_profit > 0:
            reward_pips = abs(take_profit - entry_price) / pip_size
            risk_reward_ratio = _safe_div(reward_pips, stop_pips)

        # ── Recommendations ───────────────────────────────────────────────
        recommendation = "valid"
        warnings = []

        if risk_percent > 2:
            recommendation = "high_risk"
            warnings.append("Risking more than 2% per trade is dangerous for your account")

        if 0 < risk_reward_ratio < 1.5:
            if recommendation == "valid":
                recommendation = "poor_risk_reward"
            warnings.append("Risk:Reward below 1:1.5 — consider a better take profit level")

        if raw_position < 0.01:
            if recommendation == "valid":
                recommendation = "below_minimum_lot"
            warnings.append("Position size is below the broker minimum of 0.01 lots")

        result = {
            "position_size":     position_size,
            "units":             units,
            "risk_amount":       round(risk_amount, 2),
            "risk_percent":      risk_percent,
            "max_loss":          round(max_loss, 2),
            "risk_reward_ratio": round(risk_reward_ratio, 2),
            "stop_pips":         round(stop_pips, 1),
            "pip_value_per_lot": pip_value_per_lot,
            "entry_price":       entry_price,
            "stop_loss":         stop_loss,
            "take_profit":       take_profit,
            "price_risk":        round(price_risk, 5),
            "instrument_type":   instrument_type,
            "symbol":            request.symbol or 'EURUSD',
            "recommendation":    recommendation,
            "warnings":          warnings,
            # FIXED: was `len(warnings) == 0 or recommendation == "valid"` (or → True whenever rec is valid
            # regardless of warnings). Simplified to the single source of truth.
            "is_valid":          recommendation == "valid",
        }

        # ── Persist if authenticated ──────────────────────────────────────
        if current_user:
            try:
                from .security import get_user_id
                user_id = get_user_id(current_user)
                if user_id:
                    await database.execute(
                        """
                        INSERT INTO risk_calculations
                          (user_id, account_balance, risk_percent, entry_price, stop_loss,
                           take_profit, instrument_type, symbol, position_size, risk_reward_ratio)
                        VALUES
                          (:user_id, :balance, :risk, :entry, :sl,
                           :tp, :instr, :sym, :pos, :rr)
                        """,
                        {
                            'user_id': user_id,
                            'balance': account_balance,
                            'risk':    risk_percent,
                            'entry':   entry_price,
                            'sl':      stop_loss,
                            'tp':      take_profit or 0,
                            'instr':   instrument_type,
                            'sym':     request.symbol or '',
                            'pos':     position_size,
                            'rr':      round(risk_reward_ratio, 2),
                        }
                    )
            except Exception:
                pass  # History save is non-fatal

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Calculation error: {str(e)}")


@router.get("/history")
async def get_risk_history(
    limit: int = 10,
    current_user=Depends(get_current_user),
):
    """Return recent risk calculations for the authenticated user."""
    await _ensure_risk_table()
    try:
        from .security import get_user_id
        user_id = get_user_id(current_user)
        rows = await database.fetch_all(
            """
            SELECT position_size, risk_percent, risk_reward_ratio,
                   instrument_type, symbol, calculated_at, account_balance
            FROM   risk_calculations
            WHERE  user_id = :user_id
            ORDER  BY calculated_at DESC
            LIMIT  :limit
            """,
            {'user_id': user_id, 'limit': limit},
        )
        return [dict(r) for r in rows]
    except Exception:
        return []


def _safe_div(numerator: float, denominator: float, default: float = 0.0) -> float:
    return numerator / denominator if denominator != 0 else default
