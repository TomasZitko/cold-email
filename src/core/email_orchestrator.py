"""
Smart Email Orchestrator
========================
Intelligent email sending with:
- Tiered strategy (personalized demo vs portfolio)
- Warm-up schedule
- Rate limiting
- Deliverability optimization
- Batch management
"""

import os
import smtplib
import time
import json
from email.message import EmailMessage
from email.utils import formataddr
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
from jinja2 import Template

from src.utils.logger import SystemLogger
from src.utils.helpers import FileHelper, RateLimiter, DateHelper, IDGenerator
from src.utils.validators import Validators


class EmailOrchestrator:
    """
    Intelligent email orchestration with warm-up and tiered sending.
    """

    def __init__(self, config: Dict):
        """Initialize email orchestrator."""
        self.config = config
        self.logger = SystemLogger.get_logger(__name__, config.get('logging'))

        # SMTP settings
        self.smtp_config = config.get('email', {}).get('smtp', {})
        self.sending_config = config.get('email', {}).get('sending', {})

        # Load email templates
        self.templates = {}
        self._load_templates()

        # Rate limiter
        emails_per_hour = self.sending_config.get('rate_limit', {}).get('emails_per_hour', 30)
        self.rate_limiter = RateLimiter(calls_per_hour=emails_per_hour)

        # Statistics
        self.stats = {
            'emails_sent': 0,
            'emails_failed': 0,
            'tier_breakdown': {'tier1': 0, 'tier2': 0, 'tier3': 0}
        }

        # Sent log
        self.sent_log_file = config.get('paths', {}).get('output', {}).get('emails_sent', 'data/emails/sent/sent_log.json')
        self.sent_log = self._load_sent_log()

        self.logger.info("Email Orchestrator initialized")

    def _load_templates(self):
        """Load email templates."""
        templates_path = Path(self.config.get('email', {}).get('templates', {}).get('base_path', 'src/email_templates/'))

        if not templates_path.exists():
            self.logger.warning(f"Email templates path not found: {templates_path}")
            return

        template_files = {
            'tier1': self.config.get('email', {}).get('templates', {}).get('tier1', 'tier1_personalized_demo.txt'),
            'tier2': self.config.get('email', {}).get('templates', {}).get('tier2', 'tier2_mockup_portfolio.txt'),
            'tier3': self.config.get('email', {}).get('templates', {}).get('tier3', 'tier3_portfolio.txt'),
        }

        for tier, filename in template_files.items():
            filepath = templates_path / filename
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    self.templates[tier] = f.read()
                    self.logger.info(f"Loaded {tier} template")
            else:
                self.logger.warning(f"Template not found: {filepath}")

    def _load_sent_log(self) -> Dict:
        """Load log of sent emails."""
        return FileHelper.load_json(self.sent_log_file, {})

    def _save_sent_log(self):
        """Save sent email log."""
        FileHelper.save_json(self.sent_log_file, self.sent_log)

    def can_send_today(self) -> Tuple[bool, int, str]:
        """
        Check if we can send emails today based on warm-up schedule.

        Returns:
            (can_send, limit, reason)
        """
        # Count emails sent today
        today = datetime.now().strftime('%Y-%m-%d')
        today_count = sum(1 for log in self.sent_log.values()
                         if log.get('sent_date', '').startswith(today))

        # Check warm-up schedule
        warmup_config = self.sending_config.get('warmup', {})
        if not warmup_config.get('enabled', True):
            return True, 999999, "Warm-up disabled"

        # Calculate days since first email
        if not self.sent_log:
            days_active = 1
        else:
            first_sent = min(log.get('sent_timestamp', time.time())
                           for log in self.sent_log.values())
            days_active = max(1, int((time.time() - first_sent) / 86400))

        # Determine daily limit based on warm-up schedule
        schedule = warmup_config.get('schedule', {})
        if days_active <= 7:
            daily_limit = schedule.get('day_1_7', 20)
        elif days_active <= 14:
            daily_limit = schedule.get('day_8_14', 50)
        elif days_active <= 21:
            daily_limit = schedule.get('day_15_21', 100)
        else:
            daily_limit = schedule.get('day_22_plus', 200)

        can_send = today_count < daily_limit
        reason = f"Day {days_active} of warm-up: {today_count}/{daily_limit} sent today"

        return can_send, daily_limit - today_count, reason

    def send_batch(self, leads: List[Dict], demo_base_url: Optional[str] = None) -> Dict:
        """
        Send emails to a batch of leads with intelligent tiering.

        Args:
            leads: List of lead dictionaries (with tier, score, etc.)
            demo_base_url: Base URL for demo websites (e.g., "https://tomaszitko.cz/demo/")

        Returns:
            Statistics dict
        """
        self.logger.info(f"Sending emails to {len(leads)} leads...")

        # Check if we can send
        can_send, remaining, reason = self.can_send_today()
        self.logger.info(f"Daily limit check: {reason}")

        if not can_send:
            self.logger.warning("Daily limit reached. Skipping batch.")
            return {
                'sent': 0,
                'failed': 0,
                'skipped': len(leads),
                'reason': 'Daily limit reached'
            }

        # Filter leads by tier limits
        leads_to_send = self._filter_by_tier_limits(leads)

        # Limit to remaining daily quota
        if len(leads_to_send) > remaining:
            self.logger.info(f"Limiting batch to {remaining} emails (daily quota)")
            leads_to_send = leads_to_send[:remaining]

        # Send emails
        sent = 0
        failed = 0

        for lead in leads_to_send:
            try:
                # Wait for rate limit
                self.rate_limiter.wait(
                    randomize=self.sending_config.get('rate_limit', {}).get('randomize_delay', True),
                    randomize_range=self.sending_config.get('rate_limit', {}).get('randomize_range_seconds', 60)
                )

                # Send email
                success = self._send_single_email(lead, demo_base_url)

                if success:
                    sent += 1
                    self.stats['emails_sent'] += 1
                    self.stats['tier_breakdown'][lead.get('tier', 'tier3')] += 1

                    # Log sent email
                    self._log_sent_email(lead)
                else:
                    failed += 1
                    self.stats['emails_failed'] += 1

            except Exception as e:
                self.logger.error(f"Error sending to {lead.get('email')}: {e}")
                failed += 1
                self.stats['emails_failed'] += 1

        # Save sent log
        self._save_sent_log()

        self.logger.info(f"Batch complete: {sent} sent, {failed} failed")

        return {
            'sent': sent,
            'failed': failed,
            'skipped': len(leads) - len(leads_to_send)
        }

    def _filter_by_tier_limits(self, leads: List[Dict]) -> List[Dict]:
        """Filter leads by tier daily limits."""
        batches_config = self.sending_config.get('batches', {})

        tier_limits = {
            'tier1': batches_config.get('tier1_daily_limit', 10),
            'tier2': batches_config.get('tier2_daily_limit', 30),
            'tier3': batches_config.get('tier3_daily_limit', 60)
        }

        # Count sent today by tier
        today = datetime.now().strftime('%Y-%m-%d')
        sent_today = {'tier1': 0, 'tier2': 0, 'tier3': 0}

        for log in self.sent_log.values():
            if log.get('sent_date', '').startswith(today):
                tier = log.get('tier', 'tier3')
                sent_today[tier] += 1

        # Filter leads
        filtered = []

        for lead in leads:
            tier = lead.get('tier', 'tier3')
            if sent_today.get(tier, 0) < tier_limits.get(tier, 0):
                filtered.append(lead)
                sent_today[tier] += 1

        return filtered

    def _send_single_email(self, lead: Dict, demo_base_url: Optional[str]) -> bool:
        """Send email to a single lead."""
        email = lead.get('email')
        if not email or not Validators.is_valid_email(email):
            self.logger.warning(f"Invalid email for {lead.get('company_name')}: {email}")
            return False

        # Check if already sent
        lead_id = lead.get('lead_id', IDGenerator.generate_lead_id(email, lead.get('company_name', '')))
        if lead_id in self.sent_log:
            self.logger.info(f"Email already sent to {email}, skipping")
            return False

        # Generate email content
        tier = lead.get('tier', 'tier3')
        subject, body = self._generate_email_content(lead, demo_base_url)

        if not subject or not body:
            self.logger.error(f"Failed to generate email content for {email}")
            return False

        # Create email message
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = formataddr((
            self.smtp_config.get('from_name', 'Tomáš Žitko'),
            self.smtp_config.get('from_email', 'info@tomaszitko.cz')
        ))
        msg['To'] = email
        msg.set_content(body, charset='utf-8')

        # Add unsubscribe header
        unsubscribe_url = self._generate_unsubscribe_url(lead_id)
        msg['List-Unsubscribe'] = f"<{unsubscribe_url}>"

        # Send via SMTP
        try:
            with smtplib.SMTP(
                self.smtp_config.get('host'),
                self.smtp_config.get('port', 587)
            ) as server:
                if self.smtp_config.get('use_tls', True):
                    server.starttls()

                server.login(
                    self.smtp_config.get('username'),
                    self.smtp_config.get('password')
                )

                server.send_message(msg)

            self.logger.info(f"✓ Email sent to {email} ({tier})")
            return True

        except Exception as e:
            self.logger.error(f"SMTP error sending to {email}: {e}")
            return False

    def _generate_email_content(self, lead: Dict, demo_base_url: Optional[str]) -> Tuple[str, str]:
        """Generate personalized email content."""
        tier = lead.get('tier', 'tier3')

        # Get template
        template_text = self.templates.get(tier)
        if not template_text:
            self.logger.error(f"No template found for {tier}")
            return "", ""

        # Parse template (format: SUBJECT: xxx\n\nBODY: xxx)
        parts = template_text.split('\n\n', 1)
        if len(parts) != 2:
            self.logger.error(f"Invalid template format for {tier}")
            return "", ""

        subject_line = parts[0].replace('SUBJECT:', '').strip()
        body_template = parts[1].replace('BODY:', '').strip()

        # Personalization variables
        variables = {
            'company_name': lead.get('company_name', 'Vážený zákazníku'),
            'industry': lead.get('industry', 'byznys'),
            'niche': lead.get('niche', 'default'),
            'location': self._extract_location(lead.get('address', '')),
            'your_name': self.smtp_config.get('from_name', 'Tomáš Žitko'),
            'your_email': self.smtp_config.get('from_email', 'info@tomaszitko.cz'),
            'demo_url': '',
            'unsubscribe_url': self._generate_unsubscribe_url(lead.get('lead_id', ''))
        }

        # Add demo URL for tier1 and tier2
        if tier in ['tier1', 'tier2'] and demo_base_url:
            lead_id = lead.get('lead_id', IDGenerator.generate_lead_id(
                lead.get('email', ''),
                lead.get('company_name', '')
            ))
            variables['demo_url'] = f"{demo_base_url}?lead={lead_id}"

        # Render template
        try:
            subject_template = Template(subject_line)
            body_template_obj = Template(body_template)

            subject = subject_template.render(**variables)
            body = body_template_obj.render(**variables)

            return subject, body

        except Exception as e:
            self.logger.error(f"Template rendering error: {e}")
            return "", ""

    def _extract_location(self, address: str) -> str:
        """Extract location from address."""
        if not address:
            return "České republice"

        parts = address.split(',')
        if len(parts) >= 2:
            location = parts[-1].strip()
            location = ' '.join([part for part in location.split() if not part[0].isdigit()])
            return location.strip() if location else "České republice"

        return "České republice"

    def _generate_unsubscribe_url(self, lead_id: str) -> str:
        """Generate unsubscribe URL."""
        token = IDGenerator.generate_unsubscribe_token(lead_id)
        base_url = self.config.get('compliance', {}).get('unsubscribe', {}).get('link_format', '')
        if base_url:
            return base_url.replace('{lead_id}', lead_id).replace('{token}', token)
        return f"https://tomaszitko.cz/unsubscribe?id={lead_id}"

    def _log_sent_email(self, lead: Dict):
        """Log sent email."""
        lead_id = lead.get('lead_id', IDGenerator.generate_lead_id(
            lead.get('email', ''),
            lead.get('company_name', '')
        ))

        self.sent_log[lead_id] = {
            'email': lead.get('email'),
            'company_name': lead.get('company_name'),
            'tier': lead.get('tier'),
            'sent_timestamp': time.time(),
            'sent_date': datetime.now().isoformat()
        }

    def get_statistics(self) -> Dict:
        """Get sending statistics."""
        return self.stats.copy()
