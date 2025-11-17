# bots/analyze_responses.py
import os
import imaplib
import email
import pandas as pd
import json
from datetime import datetime, timedelta
from dotenv import load_dotenv
from notion_client import Client
from typing import Dict, List, Optional, Tuple
from collections import Counter
import re

load_dotenv()

class ResponseAnalyzer:
    """
    Professional response tracking and analytics system.

    Features:
    - Response classification (positive, negative, neutral, question)
    - Detailed statistics and conversion tracking
    - Response rate calculations
    - Export to JSON/CSV
    - Notion integration (optional)
    - Command-line reporting
    """

    def __init__(
        self,
        qualified_leads_files=None,  # Can accept list of files or single file
        responses_file='data/responses.json',
        sent_log_file='data/sent_log.txt'
    ):
        # Default to checking all priority lead files
        if qualified_leads_files is None:
            qualified_leads_files = [
                'data/HIGH_PRIORITY_LEADS.csv',
                'data/MEDIUM_PRIORITY_LEADS.csv',
                'data/LOW_PRIORITY_LEADS.csv'
            ]
        elif isinstance(qualified_leads_files, str):
            qualified_leads_files = [qualified_leads_files]

        self.leads_files = qualified_leads_files
        self.responses_file = responses_file
        self.sent_log_file = sent_log_file

        # Load leads from all files
        all_leads_dfs = []
        for leads_file in qualified_leads_files:
            try:
                df = pd.read_csv(leads_file)
                all_leads_dfs.append(df)
            except FileNotFoundError:
                continue

        if all_leads_dfs:
            self.leads_df = pd.concat(all_leads_dfs, ignore_index=True)
            print(f"✅ Loaded {len(self.leads_df)} total leads from {len(all_leads_dfs)} file(s)")
        else:
            print(f"⚠️  Warning: No leads files found.")
            self.leads_df = pd.DataFrame()

        # Store the first file for saving updates (we'll update all files later if needed)
        self.leads_file = qualified_leads_files[0] if qualified_leads_files else 'data/leads.csv'

        # Notion integration (optional)
        self.notion = None
        if os.getenv('NOTION_API_KEY') and os.getenv('NOTION_DATABASE_ID'):
            self.notion = Client(auth=os.getenv('NOTION_API_KEY'))
            self.database_id = os.getenv('NOTION_DATABASE_ID')

        # IMAP configuration
        self.imap_config = {
            'host': os.getenv('IMAP_HOST'),
            'user': os.getenv('IMAP_USER'),
            'password': os.getenv('IMAP_PASSWORD')
        }

        # Response classification keywords (Czech)
        self.positive_keywords = [
            'mám zájem', 'zajímá mě', 'pošlete', 'send', 'ano', 'yes',
            'zní to dobře', 'sounds good', 'call', 'meeting', 'schůzka',
            'kdy máte čas', 'when', 'rád bych', 'chci vědět víc',
            'více informací', 'more info', 'ukažte mi', 'show me',
            'domluvme si', 'let\'s schedule', 'můžeme se sejít'
        ]

        self.negative_keywords = [
            'ne děkuji', 'no thanks', 'not interested', 'nemám zájem',
            'unsubscribe', 'odhlásit', 'stop', 'spam', 'nepište',
            'don\'t contact', 'remove me', 'už ne', 'not now'
        ]

        self.question_keywords = [
            'kolik', 'how much', 'cena', 'price', 'pricing', 'co', 'what',
            'jak', 'how', 'kdy', 'when', 'kde', 'where', 'proč', 'why',
            'můžete', 'can you', 'would you', 'could you'
        ]

        # Load existing responses
        self.responses = self._load_responses()

    def _load_responses(self) -> List[Dict]:
        """Load existing responses from file"""
        try:
            with open(self.responses_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_responses(self):
        """Save responses to file"""
        with open(self.responses_file, 'w', encoding='utf-8') as f:
            json.dump(self.responses, f, indent=4, ensure_ascii=False)

    def _classify_response(self, text: str) -> Tuple[str, float]:
        """
        Classify response sentiment and calculate confidence score

        Returns:
            (classification, confidence) where classification is one of:
            'positive', 'negative', 'question', 'neutral'
        """
        text_lower = text.lower()

        # Count keyword matches
        positive_matches = sum(1 for kw in self.positive_keywords if kw in text_lower)
        negative_matches = sum(1 for kw in self.negative_keywords if kw in text_lower)
        question_matches = sum(1 for kw in self.question_keywords if kw in text_lower)

        # Check for question marks
        if '?' in text:
            question_matches += 1

        # Determine classification
        max_matches = max(positive_matches, negative_matches, question_matches)

        if max_matches == 0:
            return 'neutral', 0.3

        if positive_matches == max_matches:
            confidence = min(0.5 + (positive_matches * 0.15), 1.0)
            return 'positive', confidence
        elif negative_matches == max_matches:
            confidence = min(0.5 + (negative_matches * 0.15), 1.0)
            return 'negative', confidence
        else:
            confidence = min(0.5 + (question_matches * 0.10), 0.9)
            return 'question', confidence

    def check_inbox(self, mark_as_read=False):
        """Check inbox for responses and classify them"""
        print("\n" + "="*60)
        print("📬 CHECKING EMAIL RESPONSES")
        print("="*60 + "\n")

        if not all(self.imap_config.values()):
            print("❌ IMAP configuration missing in .env file")
            return

        try:
            mail = imaplib.IMAP4_SSL(self.imap_config['host'])
            mail.login(self.imap_config['user'], self.imap_config['password'])
            mail.select('inbox')

            # Search for unseen emails
            status, messages = mail.search(None, 'UNSEEN')
            if status != 'OK':
                print("ℹ️  No new messages found.")
                mail.logout()
                return

            message_ids = messages[0].split()
            if not message_ids:
                print("ℹ️  No new messages found.")
                mail.logout()
                return

            print(f"📧 Found {len(message_ids)} unread emails. Analyzing...\n")

            new_responses = 0
            for num in message_ids:
                status, data = mail.fetch(num, '(RFC822)')
                if status != 'OK':
                    continue

                msg = email.message_from_bytes(data[0][1])
                from_address = email.utils.parseaddr(msg['From'])[1]

                # Check if sender is one of our leads (use 'email' column from filter_leads_v2.py)
                email_col = 'email' if 'email' in self.leads_df.columns else 'contact_email'
                if self.leads_df.empty or from_address not in self.leads_df[email_col].values:
                    continue

                # Get lead info
                lead_info = self.leads_df[self.leads_df[email_col] == from_address].iloc[0]

                # Extract email content
                subject = msg.get('subject', '')
                body = self._extract_email_body(msg)

                # Classify response
                full_text = f"{subject} {body}"
                classification, confidence = self._classify_response(full_text)

                # Create response record (use correct column names from filter_leads_v2.py)
                response_data = {
                    'timestamp': datetime.now().isoformat(),
                    'from_email': from_address,
                    'company_name': lead_info.get('company_name', 'Unknown'),  # Changed from 'name'
                    'website_url': lead_info.get('website', ''),  # Changed from 'website_url'
                    'subject': subject,
                    'body_preview': body[:200] + '...' if len(body) > 200 else body,
                    'classification': classification,
                    'confidence': confidence,
                    'priority': lead_info.get('priority', 'Medium').upper(),  # Normalize to uppercase
                    'score': lead_info.get('score', 0)
                }

                # Check if we already have this response
                if not any(r['from_email'] == from_address for r in self.responses):
                    self.responses.append(response_data)
                    new_responses += 1

                    # Print response details
                    emoji = {
                        'positive': '🟢',
                        'negative': '🔴',
                        'question': '🟡',
                        'neutral': '⚪'
                    }.get(classification, '⚪')

                    print(f"{emoji} {classification.upper()} (confidence: {confidence:.0%})")
                    print(f"   From: {lead_info.get('name', 'Unknown')}")
                    print(f"   Email: {from_address}")
                    print(f"   Subject: {subject}")
                    print(f"   Preview: {body[:100]}...")
                    print()

                    # Add to Notion if positive
                    if classification == 'positive' and self.notion:
                        self._add_to_notion(lead_info, response_data)

                    # Update lead status
                    self._update_lead_status(from_address, classification)

                # Mark as read if requested
                if mark_as_read:
                    mail.store(num, '+FLAGS', '\\Seen')

            # Save responses
            if new_responses > 0:
                self._save_responses()
                print(f"✅ Saved {new_responses} new responses")

            mail.logout()

        except Exception as e:
            print(f"❌ Error checking inbox: {e}")

    def _extract_email_body(self, msg) -> str:
        """Extract plain text body from email message"""
        body = ""
        try:
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == 'text/plain':
                        body = part.get_payload(decode=True).decode(errors='ignore')
                        break
            else:
                body = msg.get_payload(decode=True).decode(errors='ignore')
        except:
            body = ""
        return body

    def _update_lead_status(self, email: str, classification: str):
        """Update lead status in CSV based on response classification"""
        status_map = {
            'positive': 'replied_positive',
            'negative': 'replied_negative',
            'question': 'replied_question',
            'neutral': 'replied_neutral'
        }

        if not self.leads_df.empty:
            # Use correct email column name
            email_col = 'email' if 'email' in self.leads_df.columns else 'contact_email'

            # Add status column if it doesn't exist
            if 'status' not in self.leads_df.columns:
                self.leads_df['status'] = 'email_sent'

            self.leads_df.loc[self.leads_df[email_col] == email, 'status'] = status_map.get(classification, 'replied')
            self.leads_df.to_csv(self.leads_file, index=False)

    def _add_to_notion(self, lead_info: pd.Series, response_data: Dict):
        """Add positive response to Notion"""
        if not self.notion:
            return

        try:
            # Use correct column names from filter_leads_v2.py
            website = lead_info.get('website', '')
            email_val = lead_info.get('email', lead_info.get('contact_email', ''))

            self.notion.pages.create(
                parent={"database_id": self.database_id},
                properties={
                    "Name": {"title": [{"text": {"content": lead_info.get('company_name', 'Unknown')}}]},
                    "Website": {"url": website if website else "https://example.com"},  # Notion requires valid URL
                    "Email": {"email": email_val if email_val else "placeholder@example.com"},  # Notion requires valid email
                    "Status": {"select": {"name": "Positive Reply"}},
                    "Confidence": {"number": response_data['confidence']},
                    "Response": {"rich_text": [{"text": {"content": response_data['body_preview']}}]}
                }
            )
            print(f"   ✅ Added to Notion")
        except Exception as e:
            print(f"   ⚠️  Notion error: {e}")

    def generate_report(self, days=30) -> Dict:
        """Generate comprehensive analytics report"""
        print("\n" + "="*60)
        print("📊 EMAIL CAMPAIGN ANALYTICS REPORT")
        print("="*60 + "\n")

        # Calculate date range
        cutoff_date = datetime.now() - timedelta(days=days)

        # Get sent emails count
        total_sent = self._count_sent_emails(cutoff_date)

        # Filter responses by date
        recent_responses = [
            r for r in self.responses
            if datetime.fromisoformat(r['timestamp']) >= cutoff_date
        ]

        # Classification breakdown
        classifications = Counter(r['classification'] for r in recent_responses)

        # Calculate rates
        total_responses = len(recent_responses)
        response_rate = (total_responses / total_sent * 100) if total_sent > 0 else 0

        positive_count = classifications.get('positive', 0)
        positive_rate = (positive_count / total_sent * 100) if total_sent > 0 else 0

        # Priority breakdown
        priority_breakdown = Counter(r['priority'] for r in recent_responses)

        # Print report
        print(f"📅 Period: Last {days} days")
        print(f"📤 Total Emails Sent: {total_sent}")
        print(f"📥 Total Responses: {total_responses}")
        print(f"📈 Response Rate: {response_rate:.2f}%")
        print()

        print("🎯 RESPONSE BREAKDOWN:")
        print(f"   🟢 Positive: {classifications.get('positive', 0)} ({positive_rate:.2f}% conversion rate)")
        print(f"   🟡 Questions: {classifications.get('question', 0)}")
        print(f"   ⚪ Neutral: {classifications.get('neutral', 0)}")
        print(f"   🔴 Negative: {classifications.get('negative', 0)}")
        print()

        print("📊 BY LEAD PRIORITY:")
        print(f"   HIGH: {priority_breakdown.get('HIGH', 0)} responses")
        print(f"   MEDIUM: {priority_breakdown.get('MEDIUM', 0)} responses")
        print(f"   LOW: {priority_breakdown.get('LOW', 0)} responses")
        print()

        # Positive responses details
        if positive_count > 0:
            print("🟢 POSITIVE RESPONSES:")
            positive_responses = [r for r in recent_responses if r['classification'] == 'positive']
            for resp in positive_responses:
                print(f"   • {resp['company_name']} ({resp['from_email']})")
                print(f"     Subject: {resp['subject']}")
                print(f"     Confidence: {resp['confidence']:.0%}")
                print()

        print("="*60)

        return {
            'period_days': days,
            'total_sent': total_sent,
            'total_responses': total_responses,
            'response_rate': response_rate,
            'positive_rate': positive_rate,
            'classifications': dict(classifications),
            'priority_breakdown': dict(priority_breakdown)
        }

    def _count_sent_emails(self, cutoff_date: datetime) -> int:
        """Count emails sent since cutoff date"""
        try:
            with open(self.sent_log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            count = 0
            for line in lines:
                try:
                    log_date_str = ' '.join(line.split(':')[0].split()[:5])
                    log_date = datetime.strptime(log_date_str, "%a %b %d %H:%M:%S %Y")
                    if log_date >= cutoff_date:
                        count += 1
                except:
                    continue

            return count
        except FileNotFoundError:
            return 0

    def list_responses(self, classification_filter: Optional[str] = None):
        """List all responses, optionally filtered by classification"""
        print("\n" + "="*60)
        print("📋 RESPONSE LIST")
        if classification_filter:
            print(f"Filter: {classification_filter.upper()}")
        print("="*60 + "\n")

        responses = self.responses
        if classification_filter:
            responses = [r for r in responses if r['classification'] == classification_filter.lower()]

        if not responses:
            print("No responses found.")
            return

        for idx, resp in enumerate(responses, 1):
            emoji = {
                'positive': '🟢',
                'negative': '🔴',
                'question': '🟡',
                'neutral': '⚪'
            }.get(resp['classification'], '⚪')

            print(f"{idx}. {emoji} {resp['company_name']}")
            print(f"   Email: {resp['from_email']}")
            print(f"   Date: {resp['timestamp'][:10]}")
            print(f"   Subject: {resp['subject']}")
            print(f"   Classification: {resp['classification']} ({resp['confidence']:.0%} confidence)")
            print(f"   Preview: {resp['body_preview'][:100]}...")
            print()

    def export_responses(self, filename='data/responses_export.csv'):
        """Export responses to CSV"""
        if not self.responses:
            print("No responses to export.")
            return

        df = pd.DataFrame(self.responses)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"✅ Exported {len(self.responses)} responses to {filename}")


if __name__ == "__main__":
    import sys

    analyzer = ResponseAnalyzer()

    if '--help' in sys.argv:
        print("""
Response Analyzer - Usage:

python analyze_responses.py              # Check inbox for new responses
python analyze_responses.py --report     # Generate analytics report
python analyze_responses.py --list       # List all responses
python analyze_responses.py --positive   # List only positive responses
python analyze_responses.py --export     # Export responses to CSV
python analyze_responses.py --help       # Show this help
        """)
    elif '--report' in sys.argv:
        days = int(sys.argv[sys.argv.index('--report') + 1]) if len(sys.argv) > sys.argv.index('--report') + 1 else 30
        analyzer.generate_report(days=days)
    elif '--list' in sys.argv:
        analyzer.list_responses()
    elif '--positive' in sys.argv:
        analyzer.list_responses(classification_filter='positive')
    elif '--export' in sys.argv:
        analyzer.export_responses()
    else:
        analyzer.check_inbox(mark_as_read=False)
