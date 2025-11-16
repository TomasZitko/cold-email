"""
Validation utilities for emails, URLs, and data.
"""

import re
from typing import Optional
from urllib.parse import urlparse


class Validators:
    """Collection of validation functions."""

    # Regex patterns
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    CZECH_PHONE_PATTERN = re.compile(r'^(\+420|00420)?\s?[0-9]{9}$')
    URL_PATTERN = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE
    )

    @staticmethod
    def is_valid_email(email: str) -> bool:
        """Check if email address is valid."""
        if not email or not isinstance(email, str):
            return False
        return bool(Validators.EMAIL_PATTERN.match(email.strip()))

    @staticmethod
    def is_valid_phone(phone: str, country: str = 'CZ') -> bool:
        """Check if phone number is valid."""
        if not phone or not isinstance(phone, str):
            return False

        phone = phone.strip().replace(' ', '').replace('-', '')

        if country == 'CZ':
            return bool(Validators.CZECH_PHONE_PATTERN.match(phone))

        # Generic check for other countries
        return len(phone) >= 9 and phone.replace('+', '').isdigit()

    @staticmethod
    def is_valid_url(url: str) -> bool:
        """Check if URL is valid."""
        if not url or not isinstance(url, str):
            return False

        url = url.strip()

        # Add https:// if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        return bool(Validators.URL_PATTERN.match(url))

    @staticmethod
    def normalize_url(url: str) -> Optional[str]:
        """Normalize URL to standard format."""
        if not url:
            return None

        url = url.strip()

        # Add https:// if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url

        # Parse and validate
        try:
            parsed = urlparse(url)
            if not parsed.netloc:
                return None

            # Reconstruct URL
            return f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        except Exception:
            return None

    @staticmethod
    def normalize_phone(phone: str, country: str = 'CZ') -> Optional[str]:
        """Normalize phone number to standard format."""
        if not phone:
            return None

        phone = phone.strip().replace(' ', '').replace('-', '')

        if country == 'CZ':
            # Remove country code if present
            phone = phone.replace('+420', '').replace('00420', '')

            # Check if valid 9-digit number
            if len(phone) == 9 and phone.isdigit():
                return f"+420 {phone[:3]} {phone[3:6]} {phone[6:]}"

        return phone

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe file system use."""
        if not filename:
            return "unnamed"

        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '', filename)

        # Replace spaces with underscores
        filename = filename.replace(' ', '_')

        # Limit length
        if len(filename) > 200:
            filename = filename[:200]

        return filename or "unnamed"

    @staticmethod
    def extract_domain(url: str) -> Optional[str]:
        """Extract domain from URL."""
        if not url:
            return None

        normalized = Validators.normalize_url(url)
        if not normalized:
            return None

        try:
            parsed = urlparse(normalized)
            return parsed.netloc
        except Exception:
            return None

    @staticmethod
    def is_government_entity(company_name: str, keywords: list = None) -> bool:
        """Check if company is a government entity."""
        if not company_name:
            return False

        if keywords is None:
            keywords = [
                'ministerstvo', 'úřad', 'státní', 'municipality',
                'municipality', 'obec', 'město', 'kraj',
                'government', 'veřejná správa'
            ]

        company_lower = company_name.lower()
        return any(keyword in company_lower for keyword in keywords)

    @staticmethod
    def extract_company_type(company_name: str) -> Optional[str]:
        """Extract Czech company type from name."""
        if not company_name:
            return None

        types = {
            's.r.o.': 'LLC',
            'a.s.': 'Joint-Stock',
            'OSVČ': 'Sole Proprietor',
            'v.o.s.': 'General Partnership',
            'k.s.': 'Limited Partnership',
            'družstvo': 'Cooperative'
        }

        company_lower = company_name.lower()

        for abbr, full_name in types.items():
            if abbr.lower() in company_lower:
                return full_name

        return None
