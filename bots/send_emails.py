# bots/send_emails.py
import os
import json
import smtplib
import time
import random
import pandas as pd
from datetime import datetime, timedelta
from email.message import EmailMessage
from dotenv import load_dotenv
from typing import Dict, List, Optional
import logging

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/email_sending.log'),
        logging.StreamHandler()
    ]
)

class EmailSender:
    """
    Professional email sending system with spam avoidance and smart scheduling.

    Features:
    - Randomized send times (look human, not bot)
    - Rate limiting (daily limits, hourly limits)
    - Smart scheduling (optimal send times)
    - Priority-based sending (high-priority leads first)
    - Warm-up mode (gradually increase volume)
    - Resume capability
    - Spam detection avoidance
    """

    def __init__(
        self,
        emails_file='data/emails-to-send.json',
        leads_file='data/qualified-leads.csv',
        log_file='data/sent_log.txt',
        queue_file='data/send_queue.json'
    ):
        self.emails_file = emails_file
        self.leads_file = leads_file
        self.log_file = log_file
        self.queue_file = queue_file

        # SMTP credentials from .env
        self.EMAIL_SERVER = os.getenv('SMTP_HOST')
        self.EMAIL_PORT = int(os.getenv('SMTP_PORT', 587))
        self.EMAIL_USER = os.getenv('SMTP_USER')
        self.EMAIL_PASS = os.getenv('SMTP_PASSWORD')

        # Spam avoidance settings (configurable via .env)
        self.DAILY_LIMIT = int(os.getenv('DAILY_EMAIL_LIMIT', 50))  # Max emails per day
        self.HOURLY_LIMIT = int(os.getenv('HOURLY_EMAIL_LIMIT', 10))  # Max emails per hour
        self.MIN_DELAY = int(os.getenv('MIN_DELAY_SECONDS', 60))  # Min delay between emails (60s)
        self.MAX_DELAY = int(os.getenv('MAX_DELAY_SECONDS', 300))  # Max delay between emails (5min)
        self.WARM_UP_MODE = os.getenv('WARM_UP_MODE', 'false').lower() == 'true'
        self.WARM_UP_DAILY_INCREASE = int(os.getenv('WARM_UP_DAILY_INCREASE', 5))  # Increase by 5 each day

        # Best times to send (9AM-5PM on weekdays)
        self.SEND_HOURS_START = int(os.getenv('SEND_HOURS_START', 9))
        self.SEND_HOURS_END = int(os.getenv('SEND_HOURS_END', 17))
        self.SEND_WEEKDAYS_ONLY = os.getenv('SEND_WEEKDAYS_ONLY', 'true').lower() == 'true'

    def _is_sending_allowed_now(self) -> bool:
        """Check if current time is within allowed sending hours"""
        now = datetime.now()

        # Check weekday restriction
        if self.SEND_WEEKDAYS_ONLY and now.weekday() >= 5:  # 5=Saturday, 6=Sunday
            logging.info("⏸️  Not sending - Weekend (weekdays only mode enabled)")
            return False

        # Check hour restriction
        if not (self.SEND_HOURS_START <= now.hour < self.SEND_HOURS_END):
            logging.info(f"⏸️  Not sending - Outside allowed hours ({self.SEND_HOURS_START}:00-{self.SEND_HOURS_END}:00)")
            return False

        return True

    def _get_random_delay(self) -> int:
        """Generate a random delay between emails to look human"""
        # Randomize delay with normal distribution (looks more human)
        delay = random.gauss(
            (self.MIN_DELAY + self.MAX_DELAY) / 2,  # mean
            (self.MAX_DELAY - self.MIN_DELAY) / 6   # std dev
        )
        # Clamp to min/max
        delay = max(self.MIN_DELAY, min(self.MAX_DELAY, delay))
        return int(delay)

    def _get_todays_send_count(self) -> int:
        """Count how many emails were sent today"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            today = datetime.now().date()
            count = 0
            for line in lines:
                try:
                    # Extract date from log line (format: "Day Mon DD HH:MM:SS YYYY: ...")
                    log_date_str = ' '.join(line.split(':')[0].split()[:5])
                    log_date = datetime.strptime(log_date_str, "%a %b %d %H:%M:%S %Y").date()
                    if log_date == today:
                        count += 1
                except:
                    continue

            return count
        except FileNotFoundError:
            return 0

    def _get_hours_send_count(self, hours=1) -> int:
        """Count emails sent in the last N hours"""
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            cutoff_time = datetime.now() - timedelta(hours=hours)
            count = 0

            for line in lines:
                try:
                    log_date_str = ' '.join(line.split(':')[0].split()[:5])
                    log_date = datetime.strptime(log_date_str, "%a %b %d %H:%M:%S %Y")
                    if log_date >= cutoff_time:
                        count += 1
                except:
                    continue

            return count
        except FileNotFoundError:
            return 0

    def _calculate_warm_up_limit(self) -> int:
        """Calculate daily limit for warm-up mode"""
        if not self.WARM_UP_MODE:
            return self.DAILY_LIMIT

        # Count total days of sending
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            unique_dates = set()
            for line in lines:
                try:
                    log_date_str = ' '.join(line.split(':')[0].split()[:5])
                    log_date = datetime.strptime(log_date_str, "%a %b %d %H:%M:%S %Y").date()
                    unique_dates.add(log_date)
                except:
                    continue

            days_sending = len(unique_dates)
            warm_up_limit = min(10 + (days_sending * self.WARM_UP_DAILY_INCREASE), self.DAILY_LIMIT)
            logging.info(f"📈 Warm-up mode: Day {days_sending+1}, limit = {warm_up_limit} emails")
            return warm_up_limit
        except FileNotFoundError:
            logging.info(f"📈 Warm-up mode: Day 1, limit = 10 emails")
            return 10  # Start with 10 emails on day 1

    def _sort_emails_by_priority(self, emails: List[Dict]) -> List[Dict]:
        """Sort emails by priority (HIGH first, then MEDIUM, then LOW)"""
        priority_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2}

        def get_priority_value(email):
            priority = email.get('priority', 'MEDIUM')
            return priority_order.get(priority, 1)

        return sorted(emails, key=get_priority_value)

    def _add_personalization_footer(self, body: str, company_name: str) -> str:
        """Add subtle personalization to avoid spam filters"""
        # Add a subtle footer that makes each email unique
        footer = f"\n\n---\nEmail prepared specifically for {company_name}"
        return body + footer

    def _create_queue(self, emails: List[Dict]) -> List[Dict]:
        """Create a send queue with scheduled times"""
        queue = []
        now = datetime.now()

        # Start scheduling from next available slot
        current_time = now

        for email in emails:
            # Find next available sending slot
            while not self._is_sending_allowed_now_for_time(current_time):
                current_time += timedelta(hours=1)

            # Add random delay
            delay = self._get_random_delay()
            current_time += timedelta(seconds=delay)

            queue_item = email.copy()
            queue_item['scheduled_time'] = current_time.isoformat()
            queue.append(queue_item)

        return queue

    def _is_sending_allowed_now_for_time(self, check_time: datetime) -> bool:
        """Check if a specific time is within allowed sending hours"""
        if self.SEND_WEEKDAYS_ONLY and check_time.weekday() >= 5:
            return False

        if not (self.SEND_HOURS_START <= check_time.hour < self.SEND_HOURS_END):
            return False

        return True

    def _save_queue(self, queue: List[Dict]):
        """Save send queue to file"""
        with open(self.queue_file, 'w', encoding='utf-8') as f:
            json.dump(queue, f, indent=4, ensure_ascii=False)

    def _load_queue(self) -> List[Dict]:
        """Load send queue from file"""
        try:
            with open(self.queue_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def run(self, batch_mode=False, resume=False):
        """
        Main method to execute email sending with smart scheduling.

        Args:
            batch_mode (bool): If True, send all emails in queue immediately (respect rate limits)
            resume (bool): If True, resume from existing queue
        """
        print("\n" + "="*60)
        print("🚀 PROFESSIONAL EMAIL SENDER - SPAM-SAFE MODE")
        print("="*60 + "\n")

        # Validate SMTP credentials
        if not all([self.EMAIL_SERVER, self.EMAIL_USER, self.EMAIL_PASS]):
            logging.error("❌ Email credentials not set in .env file")
            return

        # Load or create queue
        if resume:
            queue = self._load_queue()
            if not queue:
                logging.info("No existing queue found. Starting fresh.")
                resume = False

        if not resume:
            # Load emails to send
            try:
                with open(self.emails_file, 'r', encoding='utf-8') as f:
                    emails_to_send = json.load(f)
                if not emails_to_send:
                    logging.info("🤷 No emails to send.")
                    return
            except (FileNotFoundError, json.JSONDecodeError):
                logging.error(f"❌ No valid emails found in '{self.emails_file}'")
                return

            # Sort by priority
            emails_to_send = self._sort_emails_by_priority(emails_to_send)
            logging.info(f"📊 Loaded {len(emails_to_send)} emails (sorted by priority)")

            # Create scheduled queue
            queue = self._create_queue(emails_to_send)
            self._save_queue(queue)
            logging.info(f"📅 Created send queue with {len(queue)} emails")

        # Load leads CSV for status updates
        try:
            df = pd.read_csv(self.leads_file)
        except FileNotFoundError:
            logging.error(f"❌ Leads file '{self.leads_file}' not found")
            return

        # Check rate limits
        todays_count = self._get_todays_send_count()
        daily_limit = self._calculate_warm_up_limit()

        logging.info(f"📊 Today's stats: {todays_count}/{daily_limit} emails sent")

        if todays_count >= daily_limit:
            logging.warning(f"⚠️  Daily limit reached ({daily_limit}). No more emails will be sent today.")
            return

        # Connect to SMTP and send
        successful_sends = 0
        failed_sends = 0
        skipped = 0

        try:
            with smtplib.SMTP(self.EMAIL_SERVER, self.EMAIL_PORT) as server:
                server.set_debuglevel(0)
                server.starttls()
                server.login(self.EMAIL_USER, self.EMAIL_PASS)
                logging.info(f"✅ Connected to SMTP: {self.EMAIL_SERVER}")

                for idx, email_data in enumerate(queue, 1):
                    # Check daily limit
                    current_count = self._get_todays_send_count()
                    if current_count >= daily_limit:
                        logging.warning(f"⛔ Daily limit reached ({daily_limit}). Stopping.")
                        break

                    # Check hourly limit
                    hourly_count = self._get_hours_send_count(1)
                    if hourly_count >= self.HOURLY_LIMIT:
                        logging.warning(f"⏸️  Hourly limit reached ({self.HOURLY_LIMIT}). Pausing for 30 minutes...")
                        time.sleep(1800)  # 30 minute pause

                    # Check if it's a good time to send
                    if not batch_mode and not self._is_sending_allowed_now():
                        logging.info(f"⏸️  Outside sending hours. Stopping for now. Resume later with --resume flag.")
                        break

                    # Validate email data
                    if not all(key in email_data for key in ['to_email', 'subject', 'body']):
                        logging.warning(f"⚠️  Invalid email data, skipping: {email_data.get('company_name', 'Unknown')}")
                        skipped += 1
                        continue

                    company_name = email_data.get('company_name', 'Unknown')
                    priority = email_data.get('priority', 'MEDIUM')

                    print(f"\n[{idx}/{len(queue)}] 📧 Sending to: {company_name} (Priority: {priority})")
                    print(f"   To: {email_data['to_email']}")
                    print(f"   Subject: {email_data['subject']}")

                    # Create email message
                    msg = EmailMessage()
                    msg['Subject'] = email_data['subject']
                    msg['From'] = self.EMAIL_USER
                    msg['To'] = email_data['to_email']

                    # Add personalization footer
                    body_with_footer = self._add_personalization_footer(
                        email_data['body'],
                        company_name
                    )
                    msg.set_content(body_with_footer, charset='utf-8')

                    try:
                        server.send_message(msg)
                        logging.info(f"✅ Sent to {email_data['to_email']}")

                        # Update lead status
                        if 'website_url' in email_data:
                            df.loc[df['website_url'] == email_data['website_url'], 'status'] = 'email_sent'

                        # Log the send
                        with open(self.log_file, 'a', encoding='utf-8') as log:
                            log.write(f"{time.ctime()}: {email_data['to_email']} | {company_name} | {email_data.get('website_url', 'N/A')}\n")

                        successful_sends += 1

                        # Remove from queue
                        queue.pop(0)
                        self._save_queue(queue)

                        # Randomized delay (human-like behavior)
                        if idx < len(queue):  # Don't delay after last email
                            delay = self._get_random_delay()
                            print(f"   ⏳ Waiting {delay}s before next email (randomized for spam avoidance)...")
                            time.sleep(delay)

                    except smtplib.SMTPException as e:
                        logging.error(f"❌ Failed to send to {email_data['to_email']}: {e}")
                        failed_sends += 1

        except smtplib.SMTPAuthenticationError:
            logging.error("❌ SMTP Authentication failed. Check credentials in .env")
            return
        except Exception as e:
            logging.error(f"❌ Unexpected error: {e}")
            return

        # Save updated lead statuses
        if successful_sends > 0:
            df.to_csv(self.leads_file, index=False)
            logging.info(f"💾 Updated {successful_sends} lead statuses")

        # Summary
        print("\n" + "="*60)
        print("📊 SENDING SUMMARY")
        print("="*60)
        print(f"✅ Successful: {successful_sends}")
        print(f"❌ Failed: {failed_sends}")
        print(f"⏭️  Skipped: {skipped}")
        print(f"📋 Remaining in queue: {len(queue)}")
        print(f"📊 Today's total: {self._get_todays_send_count()}/{daily_limit}")
        print("="*60 + "\n")

        if len(queue) > 0:
            print(f"💡 TIP: Run with --resume flag to continue sending remaining {len(queue)} emails")


if __name__ == "__main__":
    import sys

    sender = EmailSender()

    # Check for flags
    batch_mode = '--batch' in sys.argv
    resume = '--resume' in sys.argv

    if '--help' in sys.argv:
        print("""
Professional Email Sender - Usage:

python send_emails.py              # Normal mode (respect time windows)
python send_emails.py --batch      # Batch mode (send all immediately, respect rate limits)
python send_emails.py --resume     # Resume from previous queue
python send_emails.py --help       # Show this help

Environment variables (.env):
- DAILY_EMAIL_LIMIT=50            # Max emails per day
- HOURLY_EMAIL_LIMIT=10           # Max emails per hour
- MIN_DELAY_SECONDS=60            # Min delay between emails
- MAX_DELAY_SECONDS=300           # Max delay between emails
- WARM_UP_MODE=false              # Gradually increase daily volume
- SEND_HOURS_START=9              # Start sending at 9 AM
- SEND_HOURS_END=17               # Stop sending at 5 PM
- SEND_WEEKDAYS_ONLY=true         # Only send Mon-Fri
        """)
    else:
        sender.run(batch_mode=batch_mode, resume=resume)
