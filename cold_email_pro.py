#!/usr/bin/env python3
"""
Cold Email Outreach System - Production Ready
==============================================
Professional lead filtering, website generation, and email outreach.

Author: Tomáš Žitko
Version: 2.0.0
"""

import sys
import os
from pathlib import Path
import argparse
import yaml
from typing import Dict

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.core.lead_processor import LeadProcessor
from src.core.website_generator import WebsiteGenerator
from src.core.email_orchestrator import EmailOrchestrator
from src.core.compliance import ComplianceManager
from src.utils.logger import SystemLogger
from src.utils.helpers import FileHelper


class ColdEmailPro:
    """
    Main application class.
    """

    def __init__(self, config_path: str = 'config/production.yaml'):
        """Initialize the application."""
        self.config = self._load_config(config_path)
        self.logger = SystemLogger.get_logger('ColdEmailPro', self.config.get('logging'))

        # Initialize components
        self.lead_processor = LeadProcessor(self.config)
        self.website_generator = WebsiteGenerator(self.config)
        self.email_orchestrator = EmailOrchestrator(self.config)
        self.compliance = ComplianceManager(self.config)

        self.logger.info("=" * 60)
        self.logger.info("Cold Email Pro - Production System Initialized")
        self.logger.info("=" * 60)

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            # Load environment variables for sensitive data
            smtp_config = config.get('email', {}).get('smtp', {})
            smtp_config['host'] = os.getenv('SMTP_HOST', smtp_config.get('host', ''))
            smtp_config['username'] = os.getenv('SMTP_USER', smtp_config.get('username', ''))
            smtp_config['password'] = os.getenv('SMTP_PASSWORD', smtp_config.get('password', ''))

            return config

        except FileNotFoundError:
            print(f"❌ Config file not found: {config_path}")
            sys.exit(1)
        except yaml.YAMLError as e:
            print(f"❌ Error parsing config file: {e}")
            sys.exit(1)

    def process_leads(self, input_file: str, output_dir: str = 'data/leads/processed/'):
        """
        Process leads from CSV/XLSX file.

        Args:
            input_file: Path to input CSV/XLSX file
            output_dir: Directory to save processed leads
        """
        self.logger.info(f"📊 Processing leads from: {input_file}")

        # Process leads
        results = self.lead_processor.process_file(input_file)

        if not results:
            self.logger.error("No results from lead processing")
            return

        # Export results
        files = self.lead_processor.export_results(results, output_dir)

        # Print statistics
        stats = self.lead_processor.get_statistics()
        self.logger.info("\n" + "=" * 60)
        self.logger.info("PROCESSING COMPLETE")
        self.logger.info("=" * 60)
        self.logger.info(f"Total Processed: {stats['total_processed']}")
        self.logger.info(f"Tier 1 (Premium):  {stats['tier1_count']} leads")
        self.logger.info(f"Tier 2 (Good):     {stats['tier2_count']} leads")
        self.logger.info(f"Tier 3 (Potential):{stats['tier3_count']} leads")
        self.logger.info(f"Rejected:          {stats['rejected_count']} leads")
        self.logger.info("=" * 60)

        return results

    def generate_websites(self, leads_file: str, output_dir: str = 'data/generated_sites/'):
        """
        Generate demo websites for leads.

        Args:
            leads_file: Path to CSV file with leads (typically TIER1_LEADS.csv or TIER2_LEADS.csv)
            output_dir: Directory to save generated files
        """
        self.logger.info(f"🌐 Generating demo websites from: {leads_file}")

        # Load leads
        import pandas as pd
        df = pd.read_csv(leads_file)
        leads = df.to_dict('records')

        self.logger.info(f"Generating demos for {len(leads)} leads...")

        # Generate demo files
        files = self.website_generator.generate_all(leads, output_dir)

        self.logger.info("\n" + "=" * 60)
        self.logger.info("WEBSITE GENERATION COMPLETE")
        self.logger.info("=" * 60)
        for file_type, filepath in files.items():
            self.logger.info(f"{file_type}: {filepath}")
        self.logger.info("=" * 60)
        self.logger.info("\n📋 Next steps:")
        self.logger.info("1. Upload these files to your web hosting")
        self.logger.info("2. Point demos to: https://tomaszitko.cz/demo/")
        self.logger.info("3. Test with: https://tomaszitko.cz/demo/?lead=YOUR_LEAD_ID")
        self.logger.info("=" * 60)

        return files

    def send_emails(self, leads_file: str, demo_url: str = None, dry_run: bool = False):
        """
        Send emails to leads.

        Args:
            leads_file: Path to CSV file with leads
            demo_url: Base URL for demo websites (e.g., "https://tomaszitko.cz/demo/")
            dry_run: If True, don't actually send emails (test mode)
        """
        if dry_run:
            self.logger.info("🧪 DRY RUN MODE - No emails will be sent")

        self.logger.info(f"📧 Sending emails from: {leads_file}")

        # Load leads
        import pandas as pd
        df = pd.read_csv(leads_file)
        leads = df.to_dict('records')

        # Filter by compliance
        filtered_leads = []
        for lead in leads:
            email = lead.get('email')
            if not email:
                continue

            can_send, reason = self.compliance.can_email(email)
            if not can_send:
                self.logger.info(f"Skipping {email}: {reason}")
                continue

            filtered_leads.append(lead)

        self.logger.info(f"After compliance filtering: {len(filtered_leads)} leads")

        if dry_run:
            self.logger.info("\n📊 DRY RUN SUMMARY:")
            self.logger.info(f"Would send to {len(filtered_leads)} leads")
            return

        # Check warm-up limits
        can_send, remaining, reason = self.email_orchestrator.can_send_today()
        self.logger.info(f"Daily limit: {reason}")

        if not can_send:
            self.logger.warning("❌ Daily limit reached. Try again tomorrow.")
            return

        # Confirm sending
        print("\n" + "=" * 60)
        print("⚠️  PRODUCTION EMAIL SENDING")
        print("=" * 60)
        print(f"Leads to email: {len(filtered_leads)}")
        print(f"Daily limit remaining: {remaining}")
        print(f"Demo URL: {demo_url or 'None (portfolio only)'}")
        print("=" * 60)
        confirm = input("Continue? (yes/no): ").strip().lower()

        if confirm != 'yes':
            self.logger.info("Cancelled by user")
            return

        # Send emails
        result = self.email_orchestrator.send_batch(filtered_leads, demo_url)

        self.logger.info("\n" + "=" * 60)
        self.logger.info("EMAIL SENDING COMPLETE")
        self.logger.info("=" * 60)
        self.logger.info(f"Sent:    {result['sent']}")
        self.logger.info(f"Failed:  {result['failed']}")
        self.logger.info(f"Skipped: {result['skipped']}")
        self.logger.info("=" * 60)

    def show_statistics(self):
        """Show system statistics."""
        print("\n" + "=" * 60)
        print("SYSTEM STATISTICS")
        print("=" * 60)

        # Lead processing stats
        lead_stats = self.lead_processor.get_statistics()
        print("\n📊 Lead Processing:")
        print(f"  Total Processed: {lead_stats['total_processed']}")
        print(f"  Tier 1: {lead_stats['tier1_count']}")
        print(f"  Tier 2: {lead_stats['tier2_count']}")
        print(f"  Tier 3: {lead_stats['tier3_count']}")
        print(f"  Rejected: {lead_stats['rejected_count']}")

        # Email stats
        email_stats = self.email_orchestrator.get_statistics()
        print("\n📧 Email Sending:")
        print(f"  Total Sent: {email_stats['emails_sent']}")
        print(f"  Failed: {email_stats['emails_failed']}")
        print(f"  By Tier:")
        for tier, count in email_stats['tier_breakdown'].items():
            print(f"    {tier}: {count}")

        # Compliance stats
        compliance_stats = self.compliance.get_statistics()
        print("\n🛡️  Compliance:")
        print(f"  Unsubscribed: {compliance_stats['unsubscribed_count']}")
        print(f"  Bounced: {compliance_stats['bounced_count']}")
        print(f"  Spam Complaints: {compliance_stats['spam_complaints_count']}")
        print(f"  Total Blocked: {compliance_stats['total_blocked']}")

        print("=" * 60 + "\n")


def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(
        description='Cold Email Pro - Production-Ready Outreach System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process leads
  python cold_email_pro.py process --input leads.csv

  # Generate demo websites
  python cold_email_pro.py generate-sites --input data/leads/processed/TIER1_LEADS.csv

  # Send emails (dry run)
  python cold_email_pro.py send --input data/leads/processed/TIER1_LEADS.csv --dry-run

  # Send emails (production)
  python cold_email_pro.py send --input data/leads/processed/TIER1_LEADS.csv --demo-url https://tomaszitko.cz/demo/

  # Show statistics
  python cold_email_pro.py stats
        """
    )

    parser.add_argument('--config', default='config/production.yaml',
                       help='Path to config file (default: config/production.yaml)')

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Process leads command
    process_parser = subparsers.add_parser('process', help='Process leads from CSV/XLSX file')
    process_parser.add_argument('--input', required=True, help='Input CSV/XLSX file')
    process_parser.add_argument('--output', default='data/leads/processed/', help='Output directory')

    # Generate websites command
    generate_parser = subparsers.add_parser('generate-sites', help='Generate demo websites')
    generate_parser.add_argument('--input', required=True, help='Input CSV file with leads')
    generate_parser.add_argument('--output', default='data/generated_sites/', help='Output directory')

    # Send emails command
    send_parser = subparsers.add_parser('send', help='Send emails to leads')
    send_parser.add_argument('--input', required=True, help='Input CSV file with leads')
    send_parser.add_argument('--demo-url', help='Base URL for demo websites')
    send_parser.add_argument('--dry-run', action='store_true', help='Test mode (don\'t send emails)')

    # Statistics command
    stats_parser = subparsers.add_parser('stats', help='Show system statistics')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Initialize app
    app = ColdEmailPro(config_path=args.config)

    # Execute command
    if args.command == 'process':
        app.process_leads(args.input, args.output)

    elif args.command == 'generate-sites':
        app.generate_websites(args.input, args.output)

    elif args.command == 'send':
        app.send_emails(args.input, args.demo_url, args.dry_run)

    elif args.command == 'stats':
        app.show_statistics()


if __name__ == '__main__':
    main()
