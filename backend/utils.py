"""
Utility Functions
"""
import os
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

def format_datetime(dt: Optional[datetime]) -> Optional[str]:
    """Format datetime to ISO string"""
    if dt is None:
        return None
    return dt.isoformat()

def parse_datetime(date_str: str) -> Optional[datetime]:
    """Parse ISO datetime string"""
    try:
        return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except:
        return None

def generate_slug(text: str) -> str:
    """Generate URL-friendly slug"""
    import re
    slug = re.sub(r'[^\w\s-]', '', text.lower())
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

def get_env_or_default(key: str, default: str) -> str:
    """Get environment variable or default value"""
    return os.getenv(key, default)
