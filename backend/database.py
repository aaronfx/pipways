"""
Database module for Pipways
Handles PostgreSQL connections, migrations, and all CRUD operations
"""

import os
import asyncpg
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.environ.get("DATABASE_URL") or os.environ.get("RAILWAY_DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

class Database:
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        """Initialize connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=1,
                max_size=10,
                command_timeout=60
            )
            logger.info("[database] ✅ Connected to PostgreSQL")
            await self.run_migrations()
        except Exception as e:
            logger.exception(f"[database] ❌ Connection failed: {e}")
            raise

    async def disconnect(self):
        """Close pool"""
        if self.pool:
            await self.pool.close()
            logger.info("[database] Disconnected")

    async def fetch_one(self, query: str, params: Optional[dict] = None) -> Optional[Dict]:
        """Fetch single row"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        async with self.pool.acquire() as conn:
            try:
                row = await conn.fetchrow(query, *(params.values() if params else []))
                return dict(row) if row else None
            except Exception as e:
                logger.error(f"[database] Query error: {e}")
                raise

    async def fetch_all(self, query: str, params: Optional[dict] = None) -> List[Dict]:
        """Fetch multiple rows"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(query, *(params.values() if params else []))
                return [dict(row) for row in rows]
            except Exception as e:
                logger.error(f"[database] Query error: {e}")
                raise

    async def execute(self, query: str, params: Optional[dict] = None) -> None:
        """Execute statement"""
        if not self.pool:
            raise RuntimeError("Database not connected")
        
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(query, *(params.values() if params else []))
            except Exception as e:
                logger.error(f"[database] Execute error: {e}")
                raise

    async def run_migrations(self):
        """Run database migrations"""
        async with self.pool.acquire() as conn:
            # Create tables if not exist
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    name VARCHAR(100),
                    role VARCHAR(20) DEFAULT 'user',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS predictions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    symbol VARCHAR(20) NOT NULL,
                    direction VARCHAR(10) NOT NULL,
                    entry_price DECIMAL,
                    target_price DECIMAL,
                    stop_loss DECIMAL,
                    confidence INTEGER,
                    timeframe VARCHAR(10),
                    status VARCHAR(20) DEFAULT 'pending',
                    result VARCHAR(20),
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    prediction_id INTEGER REFERENCES predictions(id),
                    symbol VARCHAR(20) NOT NULL,
                    direction VARCHAR(10) NOT NULL,
                    entry_price DECIMAL NOT NULL,
                    exit_price DECIMAL,
                    quantity DECIMAL,
                    pnl DECIMAL,
                    status VARCHAR(20) DEFAULT 'open',
                    opened_at TIMESTAMP DEFAULT NOW(),
                    closed_at TIMESTAMP
                )
            """)
            
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS signals (
                    id SERIAL PRIMARY KEY,
                    symbol VARCHAR(20) NOT NULL,
                    direction VARCHAR(10) NOT NULL,
                    entry VARCHAR(20) NOT NULL,
                    target VARCHAR(20) NOT NULL,
                    stop VARCHAR(20) NOT NULL,
                    entry_price DECIMAL,
                    take_profit DECIMAL,
                    stop_loss DECIMAL,
                    confidence INTEGER DEFAULT 70,
                    ai_confidence INTEGER DEFAULT 70,
                    asset_type VARCHAR(20) DEFAULT 'forex',
                    country VARCHAR(50) DEFAULT 'all',
                    pattern VARCHAR(50) DEFAULT 'BREAKOUT',
                    timeframe VARCHAR(10) DEFAULT 'M5',
                    pattern_points TEXT,
                    candles TEXT,
                    breakout_point TEXT,
                    is_pattern_idea BOOLEAN DEFAULT FALSE,
                    pattern_name VARCHAR(50),
                    status VARCHAR(20) DEFAULT 'active',
                    is_published BOOLEAN DEFAULT TRUE,
                    bias_d1 VARCHAR(10),
                    bias_h4 VARCHAR(10),
                    bos_m5 VARCHAR(10),
                    created_at TIMESTAMP DEFAULT NOW(),
                    expires_at TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Migration: add candles column if not exists
            try:
                await conn.execute("ALTER TABLE signals ADD COLUMN IF NOT EXISTS candles TEXT")
                await conn.execute("ALTER TABLE signals ADD COLUMN IF NOT EXISTS pattern_name VARCHAR(50)")
                await conn.execute("ALTER TABLE signals ADD COLUMN IF NOT EXISTS breakout_point TEXT")
                logger.info("[database] ✅ Migration complete")
            except Exception as e:
                logger.warning(f"[database] Migration warning (may already exist): {e}")

    # User management
    async def create_user(self, email: str, password_hash: str, name: Optional[str] = None) -> Dict:
        query = """
            INSERT INTO users (email, password_hash, name)
            VALUES ($1, $2, $3)
            RETURNING id, email, name, role, is_active, created_at
        """
        row = await self.fetch_one(query, {"email": email, "hash": password_hash, "name": name})
        return row

    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        query = "SELECT * FROM users WHERE email = $1 AND is_active = TRUE"
        return await self.fetch_one(query, {"email": email})

    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        query = "SELECT id, email, name, role, is_active, created_at FROM users WHERE id = $1"
        return await self.fetch_one(query, {"id": user_id})

    # Predictions
    async def create_prediction(self, user_id: int, symbol: str, direction: str, 
                                entry_price: float, target_price: float, 
                                stop_loss: float, confidence: int, timeframe: str) -> Dict:
        query = """
            INSERT INTO predictions (user_id, symbol, direction, entry_price, target_price, stop_loss, confidence, timeframe)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            RETURNING *
        """
        params = {
            "user_id": user_id, "symbol": symbol, "direction": direction,
            "entry": entry_price, "target": target_price, "stop": stop_loss,
            "confidence": confidence, "timeframe": timeframe
        }
        return await self.fetch_one(query, params)

    async def get_user_predictions(self, user_id: int, limit: int = 50) -> List[Dict]:
        query = """
            SELECT * FROM predictions 
            WHERE user_id = $1 
            ORDER BY created_at DESC 
            LIMIT $2
        """
        return await self.fetch_all(query, {"user_id": user_id, "limit": limit})

    # Trades
    async def create_trade(self, user_id: int, prediction_id: Optional[int], 
                         symbol: str, direction: str, entry_price: float,
                         quantity: float) -> Dict:
        query = """
            INSERT INTO trades (user_id, prediction_id, symbol, direction, entry_price, quantity)
            VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING *
        """
        params = {
            "user_id": user_id, "prediction_id": prediction_id,
            "symbol": symbol, "direction": direction,
            "entry": entry_price, "qty": quantity
        }
        return await self.fetch_one(query, params)

    async def get_user_trades(self, user_id: int, limit: int = 50) -> List[Dict]:
        query = """
            SELECT * FROM trades 
            WHERE user_id = $1 
            ORDER BY opened_at DESC 
            LIMIT $2
        """
        return await self.fetch_all(query, {"user_id": user_id, "limit": limit})

    async def close_trade(self, trade_id: int, exit_price: float, pnl: float) -> Optional[Dict]:
        query = """
            UPDATE trades 
            SET exit_price = $1, pnl = $2, status = 'closed', closed_at = NOW()
            WHERE id = $3
            RETURNING *
        """
        return await self.fetch_one(query, {"exit": exit_price, "pnl": pnl, "id": trade_id})

    # Signals
    async def create_signal(self, signal_data: Dict) -> Dict:
        query = """
            INSERT INTO signals (
                symbol, direction, entry, target, stop, entry_price, take_profit, stop_loss,
                confidence, ai_confidence, asset_type, country, pattern, timeframe,
                pattern_points, candles, breakout_point, is_pattern_idea, pattern_name,
                status, is_published, expires_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22)
            RETURNING *
        """
        
        import json
        params = {
            "symbol": signal_data["symbol"],
            "direction": signal_data["direction"].upper(),
            "entry": signal_data["entry"],
            "target": signal_data["target"],
            "stop": signal_data["stop"],
            "entry_price": float(signal_data.get("entry_price", 0) or signal_data["entry"]),
            "take_profit": float(signal_data.get("take_profit", 0) or signal_data["target"]),
            "stop_loss": float(signal_data.get("stop_loss", 0) or signal_data["stop"]),
            "confidence": int(signal_data.get("confidence", 70)),
            "ai_confidence": int(signal_data.get("ai_confidence", signal_data.get("confidence", 70))),
            "asset_type": signal_data.get("asset_type", "forex"),
            "country": signal_data.get("country", "all"),
            "pattern": signal_data.get("pattern", "BREAKOUT"),
            "timeframe": signal_data.get("timeframe", "M5"),
            "pattern_points": json.dumps(signal_data.get("pattern_points", [])) if signal_data.get("pattern_points") else None,
            "candles": json.dumps(signal_data.get("candles", [])) if signal_data.get("candles") else None,
            "breakout_point": json.dumps(signal_data.get("breakout_point")) if signal_data.get("breakout_point") else None,
            "is_pattern_idea": signal_data.get("is_pattern_idea", True),
            "pattern_name": signal_data.get("pattern_name", "Breakout"),
            "status": "active",
            "is_published": True,
            "expires_at": signal_data.get("expires_at", datetime.utcnow())
        }
        
        return await self.fetch_one(query, params)

    async def get_active_signals(self, limit: int = 50) -> List[Dict]:
        query = """
            SELECT * FROM signals 
            WHERE status = 'active' 
            AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY created_at DESC 
            LIMIT $1
        """
        rows = await self.fetch_all(query, {"limit": limit})
        
        import json
        for row in rows:
            if row.get("pattern_points"):
                try:
                    row["pattern_points"] = json.loads(row["pattern_points"])
                except:
                    row["pattern_points"] = None
            if row.get("candles"):
                try:
                    row["candles"] = json.loads(row["candles"])
                except:
                    row["candles"] = None
            if row.get("breakout_point"):
                try:
                    row["breakout_point"] = json.loads(row["breakout_point"])
                except:
                    row["breakout_point"] = None
                    
        return rows

    async def get_signal_by_id(self, signal_id: int) -> Optional[Dict]:
        query = "SELECT * FROM signals WHERE id = $1"
        row = await self.fetch_one(query, {"id": signal_id})
        
        if row:
            import json
            if row.get("pattern_points"):
                try:
                    row["pattern_points"] = json.loads(row["pattern_points"])
                except:
                    row["pattern_points"] = None
            if row.get("candles"):
                try:
                    row["candles"] = json.loads(row["candles"])
                except:
                    row["candles"] = None
                    
        return row

    async def expire_old_signals(self) -> int:
        query = """
            UPDATE signals 
            SET status = 'expired' 
            WHERE status = 'active' 
            AND expires_at < NOW()
            RETURNING id
        """
        rows = await self.fetch_all(query)
        return len(rows) if rows else 0


# Global singleton instance
database = Database(DATABASE_URL)

# Convenience function for importing
def get_database():
    """Return database singleton instance"""
    return database

# Legacy support
async def init_db():
    """Initialize database connection"""
    await database.connect()

async def close_db():
    """Close database connection"""
    await database.disconnect()
