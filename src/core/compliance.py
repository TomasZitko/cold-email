"""
Compliance Module
=================
GDPR, unsubscribe management, and bounce handling.
"""

from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
import time
from datetime import datetime

from src.utils.logger import SystemLogger
from src.utils.helpers import FileHelper


class ComplianceManager:
    """
    Manage compliance: unsubscribe, GDPR, bounces.
    """

    def __init__(self, config: Dict):
        """Initialize compliance manager."""
        self.config = config
        self.logger = SystemLogger.get_logger(__name__, config.get('logging'))

        # File paths
        compliance_config = config.get('compliance', {})
        paths = config.get('paths', {}).get('compliance', {})

        self.unsubscribe_file = paths.get('unsubscribe', 'data/compliance/unsubscribe_list.json')
        self.bounce_file = paths.get('bounces', 'data/compliance/bounce_blacklist.json')
        self.spam_file = paths.get('spam', 'data/compliance/spam_complaints.json')

        # Load data
        self.unsubscribe_list = FileHelper.load_json(self.unsubscribe_file, {})
        self.bounce_blacklist = FileHelper.load_json(self.bounce_file, {})
        self.spam_complaints = FileHelper.load_json(self.spam_file, {})

        self.logger.info("Compliance Manager initialized")

    def add_unsubscribe(self, email: str, lead_id: Optional[str] = None, reason: str = "user_request"):
        """Add email to unsubscribe list."""
        self.unsubscribe_list[email] = {
            'lead_id': lead_id,
            'reason': reason,
            'timestamp': time.time(),
            'date': datetime.now().isoformat()
        }

        FileHelper.save_json(self.unsubscribe_file, self.unsubscribe_list)
        self.logger.info(f"Added {email} to unsubscribe list")

    def is_unsubscribed(self, email: str) -> bool:
        """Check if email is unsubscribed."""
        return email in self.unsubscribe_list

    def add_bounce(self, email: str, reason: str = "bounce"):
        """Add email to bounce blacklist."""
        if email not in self.bounce_blacklist:
            self.bounce_blacklist[email] = {
                'count': 0,
                'first_bounce': time.time(),
                'reasons': []
            }

        self.bounce_blacklist[email]['count'] += 1
        self.bounce_blacklist[email]['last_bounce'] = time.time()
        self.bounce_blacklist[email]['reasons'].append({
            'reason': reason,
            'timestamp': time.time()
        })

        FileHelper.save_json(self.bounce_file, self.bounce_blacklist)
        self.logger.warning(f"Bounce recorded for {email} (count: {self.bounce_blacklist[email]['count']})")

    def is_bounced(self, email: str, max_bounces: int = 2) -> bool:
        """Check if email has bounced too many times."""
        if email not in self.bounce_blacklist:
            return False

        return self.bounce_blacklist[email]['count'] >= max_bounces

    def add_spam_complaint(self, email: str):
        """Add spam complaint."""
        self.spam_complaints[email] = {
            'timestamp': time.time(),
            'date': datetime.now().isoformat()
        }

        FileHelper.save_json(self.spam_file, self.spam_complaints)
        self.logger.warning(f"Spam complaint recorded for {email}")

        # Auto-add to unsubscribe if enabled
        if self.config.get('compliance', {}).get('spam', {}).get('auto_blacklist', True):
            self.add_unsubscribe(email, reason="spam_complaint")

    def is_spam_complained(self, email: str) -> bool:
        """Check if email has spam complaint."""
        return email in self.spam_complaints

    def can_email(self, email: str) -> Tuple[bool, str]:
        """
        Check if we can send email to this address.

        Returns:
            (can_send, reason)
        """
        if self.is_unsubscribed(email):
            return False, "Unsubscribed"

        if self.is_spam_complained(email):
            return False, "Spam complaint"

        if self.is_bounced(email):
            return False, "Too many bounces"

        return True, "OK"

    def export_data(self, output_dir: str) -> Dict[str, str]:
        """Export all compliance data (GDPR data export)."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        files = {}

        # Unsubscribes
        unsub_file = output_path / "unsubscribe_list.json"
        FileHelper.save_json(str(unsub_file), self.unsubscribe_list)
        files['unsubscribe'] = str(unsub_file)

        # Bounces
        bounce_file = output_path / "bounce_blacklist.json"
        FileHelper.save_json(str(bounce_file), self.bounce_blacklist)
        files['bounces'] = str(bounce_file)

        # Spam complaints
        spam_file = output_path / "spam_complaints.json"
        FileHelper.save_json(str(spam_file), self.spam_complaints)
        files['spam'] = str(spam_file)

        self.logger.info(f"Exported compliance data to {output_dir}")

        return files

    def get_statistics(self) -> Dict:
        """Get compliance statistics."""
        return {
            'unsubscribed_count': len(self.unsubscribe_list),
            'bounced_count': len(self.bounce_blacklist),
            'spam_complaints_count': len(self.spam_complaints),
            'total_blocked': len(set(list(self.unsubscribe_list.keys()) +
                                    list(self.bounce_blacklist.keys()) +
                                    list(self.spam_complaints.keys())))
        }
