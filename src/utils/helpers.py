"""
Helper utilities for common operations.
"""

import hashlib
import json
import time
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, List


class FileHelper:
    """File operation helpers."""

    @staticmethod
    def ensure_dir(path: str) -> Path:
        """Ensure directory exists, create if not."""
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    @staticmethod
    def load_json(filepath: str, default: Any = None) -> Any:
        """Load JSON file, return default if not found."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return default if default is not None else {}

    @staticmethod
    def save_json(filepath: str, data: Any, indent: int = 2) -> bool:
        """Save data to JSON file."""
        try:
            # Ensure directory exists
            Path(filepath).parent.mkdir(parents=True, exist_ok=True)

            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=indent, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving JSON to {filepath}: {e}")
            return False

    @staticmethod
    def file_age_days(filepath: str) -> Optional[float]:
        """Get file age in days."""
        try:
            file_path = Path(filepath)
            if not file_path.exists():
                return None

            mtime = file_path.stat().st_mtime
            age_seconds = time.time() - mtime
            return age_seconds / 86400  # Convert to days
        except Exception:
            return None


class IDGenerator:
    """Generate unique IDs for leads, emails, etc."""

    @staticmethod
    def generate_lead_id(email: str, company_name: str) -> str:
        """Generate unique lead ID from email and company name."""
        combined = f"{email}:{company_name}".lower()
        return hashlib.md5(combined.encode()).hexdigest()[:12]

    @staticmethod
    def generate_short_id(length: int = 8) -> str:
        """Generate short random ID."""
        chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
        return ''.join(random.choices(chars, k=length))

    @staticmethod
    def generate_unsubscribe_token(lead_id: str) -> str:
        """Generate secure unsubscribe token."""
        timestamp = str(int(time.time()))
        combined = f"{lead_id}:{timestamp}"
        return hashlib.sha256(combined.encode()).hexdigest()[:16]


class DateHelper:
    """Date and time helpers."""

    @staticmethod
    def parse_date(date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object."""
        if not date_str:
            return None

        # Common date formats
        formats = [
            '%Y-%m-%d',
            '%d.%m.%Y',
            '%d/%m/%Y',
            '%Y/%m/%d',
            '%d-%m-%Y'
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue

        return None

    @staticmethod
    def months_since(date_str: str) -> Optional[int]:
        """Calculate months since a date string."""
        parsed_date = DateHelper.parse_date(date_str)
        if not parsed_date:
            return None

        now = datetime.now()
        months = (now.year - parsed_date.year) * 12 + (now.month - parsed_date.month)
        return max(0, months)

    @staticmethod
    def format_date(dt: datetime, format_str: str = '%Y-%m-%d') -> str:
        """Format datetime to string."""
        return dt.strftime(format_str)

    @staticmethod
    def is_business_hours() -> bool:
        """Check if current time is business hours (9 AM - 5 PM, Mon-Fri)."""
        now = datetime.now()

        # Check if weekday (0 = Monday, 6 = Sunday)
        if now.weekday() >= 5:
            return False

        # Check if between 9 AM and 5 PM
        return 9 <= now.hour < 17


class RateLimiter:
    """Simple rate limiter for API calls and email sending."""

    def __init__(self, calls_per_hour: int = 30):
        self.calls_per_hour = calls_per_hour
        self.min_delay = 3600 / calls_per_hour  # Minimum delay in seconds
        self.last_call = 0

    def wait(self, randomize: bool = True, randomize_range: int = 60):
        """Wait appropriate time before next call."""
        now = time.time()
        elapsed = now - self.last_call

        # Calculate required wait time
        wait_time = self.min_delay - elapsed

        # Add random variation if requested
        if randomize and wait_time > 0:
            variation = random.uniform(-randomize_range, randomize_range)
            wait_time = max(0, wait_time + variation)

        if wait_time > 0:
            time.sleep(wait_time)

        self.last_call = time.time()

    def can_proceed(self) -> bool:
        """Check if enough time has passed since last call."""
        now = time.time()
        elapsed = now - self.last_call
        return elapsed >= self.min_delay


class TextHelper:
    """Text processing helpers."""

    @staticmethod
    def truncate(text: str, max_length: int = 100, suffix: str = '...') -> str:
        """Truncate text to max length."""
        if not text or len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix

    @staticmethod
    def clean_whitespace(text: str) -> str:
        """Clean excess whitespace from text."""
        if not text:
            return ''
        return ' '.join(text.split())

    @staticmethod
    def extract_keywords(text: str, keywords_list: List[str]) -> List[str]:
        """Extract matching keywords from text."""
        if not text:
            return []

        text_lower = text.lower()
        found = []

        for keyword in keywords_list:
            if keyword.lower() in text_lower:
                found.append(keyword)

        return found

    @staticmethod
    def contains_any(text: str, keywords: List[str]) -> bool:
        """Check if text contains any of the keywords."""
        if not text or not keywords:
            return False

        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)

    @staticmethod
    def similarity_score(text1: str, text2: str) -> float:
        """Simple similarity score between two texts (0-1)."""
        if not text1 or not text2:
            return 0.0

        # Convert to sets of words
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())

        # Calculate Jaccard similarity
        intersection = words1.intersection(words2)
        union = words1.union(words2)

        if not union:
            return 0.0

        return len(intersection) / len(union)
