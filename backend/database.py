"""
Database module for Pipways
Compatible with existing auth.py imports
"""

import os
import asyncpg
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging
import json

logger = logging.getLogger(__name__)

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
                if params:
                    keys = list(params.keys())
                    values = [params[k] for k in keys]
                    for i, key in enumerate(keys):
                        query = query.replace(f":{key}", f"${i+1}")
                    row = await conn.fetchrow(query, *values)
                else:
                    row = await conn.fetchrow(query)
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
                if params:
                    keys = list(params.keys())
                    values = [params[k] for k in keys]
                    for i, key in enumerate(keys):
                        query = query.replace(f":{key}", f"${i+1}")
                    rows = await conn.fetch(query, *values)
                else:
                    rows = await conn.fetch(query)
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
                if params:
                    keys = list(params.keys())
                    values = [params[k] for k in keys]
                    for i, key in enumerate(keys):
                        query = query.replace(f":{key}", f"${i+1}")
                    await conn.execute(query, *values)
                else:
                    await conn.execute(query)
            except Exception as e:
                logger.error(f"[database] Execute error: {e}")
                raise

    async def run_migrations(self):
        """Run database migrations"""
        async with self.pool.acquire() as conn:
            # Users table for auth compatibility
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
            
            # Signals table
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
                    created_at TIMESTAMP DEFAULT NOW(),
                    expires_at TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT NOW()
                )
            """)
            
            # Add missing columns
            await conn.execute("ALTER TABLE signals ADD COLUMN IF NOT EXISTS candles TEXT")
            await conn.execute("ALTER TABLE signals ADD COLUMN IF NOT EXISTS pattern_name VARCHAR(50)")
            await conn.execute("ALTER TABLE signals ADD COLUMN IF NOT EXISTS breakout_point TEXT")
            logger.info("[database] ✅ Migrations complete")

    async def create_signal(self, signal_data: Dict) -> Dict:
        """Create a new signal"""
        query = """
            INSERT INTO signals (
                symbol, direction, entry, target, stop, entry_price, take_profit, stop_loss,
                confidence, ai_confidence, asset_type, country, pattern, timeframe,
                pattern_points, candles, breakout_point, is_pattern_idea, pattern_name,
                status, is_published, expires_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19, $20, $21, $22)
            RETURNING *
        """
        
        params = {
            "symbol": signal_data["symbol"],
            "direction": signal_data["direction"],
            "entry": signal_data["entry"],
            "target": signal_data["target"],
            "stop": signal_data["stop"],
            "entry_price": signal_data.get("entry_price", 0),
            "take_profit": signal_data.get("take_profit", 0),
            "stop_loss": signal_data.get("stop_loss", 0),
            "confidence": signal_data.get("confidence", 70),
            "ai_confidence": signal_data.get("ai_confidence", 70),
            "asset_type": signal_data.get("asset_type", "forex"),
            "country": signal_data.get("country", "all"),
            "pattern": signal_data.get("pattern", "BREAKOUT"),
            "timeframe": signal_data.get("timeframe", "M5"),
            "pattern_points": signal_data.get("pattern_points"),
            "candles": signal_data.get("candles"),
            "breakout_point": signal_data.get("breakout_point"),
            "is_pattern_idea": signal_data.get("is_pattern_idea", True),
            "pattern_name": signal_data.get("pattern_name", "Breakout"),
            "status": signal_data.get("status", "active"),
            "is_published": signal_data.get("is_published", True),
            "expires_at": signal_data.get("expires_at", datetime.utcnow())
        }
        
        return await self.fetch_one(query, params)

    async def get_active_signals(self, limit: int = 50) -> List[Dict]:
        """Get active signals"""
        query = """
            SELECT * FROM signals 
            WHERE status = 'active' 
            AND (expires_at IS NULL OR expires_at > NOW())
            ORDER BY created_at DESC 
            LIMIT $1
        """
        rows = await self.fetch_all(query, {"limit": limit})
        
        # Parse JSON fields
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
        """Get signal by ID"""
        query = "SELECT * FROM signals WHERE id = $1"
        row = await self.fetch_one(query, {"id": signal_id})
        
        if row:
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
        """Expire old signals"""
        query = """
            UPDATE signals 
            SET status = 'expired' 
            WHERE status = 'active' 
            AND expires_at < NOW()
            RETURNING id
        """
        rows = await self.fetch_all(query)
        return len(rows) if rows else 0

    # User methods for auth compatibility
    async def create_user(self, email: str, password_hash: str, name: Optional[str] = None) -> Dict:
        query = """
            INSERT INTO users (email, password_hash, name)
            VALUES ($1, $2, $3)
            RETURNING id, email, name, role, is_active, created_at
        """
        return await self.fetch_one(query, {"email": email, "hash": password_hash, "name": name})

    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        query = "SELECT * FROM users WHERE email = $1 AND is_active = TRUE"
        return await self.fetch_one(query, {"email": email})

    async def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        query = "SELECT id, email, name, role, is_active, created_at FROM users WHERE id = $1"
        return await self.fetch_one(query, {"id": user_id})


# CRITICAL EXPORTS for auth.py compatibility

# 1. Singleton instance
database = Database(DATABASE_URL)

# 2. get_database function
def get_database():
    """Return database singleton instance"""
    return database

# 3. LEGACY: users table reference (for auth.py compatibility)
# This is a stub that provides the table interface auth.py expects
class UsersTable:
    """Stub for legacy auth.py compatibility"""
    def __init__(self, db):
        self.db = db
    
    async def select(self, *args, **kwargs):
        """Legacy compatibility"""
        return self
    
    async def where(self, **kwargs):
        """Legacy compatibility"""
        return []
    
    async def first(self):
        """Legacy compatibility"""
        return None

users = UsersTable(database)

# 4. LEGACY: get_available_columns function (for auth.py compatibility)
def get_available_columns(table_name: str) -> List[str]:
    """Return available columns for a table (legacy compatibility)"""
    columns = {
        'users': ['id', 'email', 'password_hash', 'name', 'role', 'is_active', 'created_at', 'updated_at'],
        'signals': ['id', 'symbol', 'direction', 'entry', 'target', 'stop', 'pattern_name', 'candles', 'created_at']
    }
    return columns.get(table_name, [])

# Legacy init functions
async def init_db():
    await database.connect()

async def close_db():
    await database.disconnect()
