"""
Lead Filtering System V3 - BALANCED & CONTEXT-AWARE
====================================================

Philosophy: Give them a chance! Context over strict rules.

Key Changes from V2:
- NO website ≠ bad lead (Vemsi cafe example)
- Small cafes ≠ bad lead (can afford €2k-€5k)
- DIY websites = PERFECT leads (dimsumspot.cz)
- Professional design intent = lower priority (bondcafe.cz)
- NO expensive APIs (free scraping only)

Auto-Reject ONLY:
- Government entities
- Recently redesigned (modern, <2 years)
- Permanently closed (verified)
- Large corporations (50+ employees)
"""

import os
import sys
import time
import json
import re
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from tqdm import tqdm

# Load environment variables
load_dotenv()


class LeadFilterBalancedV3:
    """
    Balanced V3 Lead Filtering - Context-aware, non-strict scoring.

    Scoring breakdown (100 points):
    - Business Health: 35 points (reviews, social, employees, location)
    - Redesign Opportunity: 30 points (website quality or absence)
    - Industry Fit: 25 points (5 tiers, all get chances)
    - Timing Signals: 10 points (recent changes, growth)
    """

    def __init__(self, config_path: str = 'config.yaml'):
        """Initialize the filter with configuration."""
        print(">> Initializing Balanced V3 Lead Filter...")

        # Load configuration
        self.config = self._load_config(config_path)

        # Setup logging
        self._setup_logging()

        # Initialize cache
        self.cache = {}
        self.statistics = defaultdict(int)
        self.rejection_reasons = Counter()

        # Load cache
        if self.config.get('performance', {}).get('cache', {}).get('enabled'):
            self._load_cache()

        self.logger.info("[OK] Initialization complete")

    def _load_config(self, config_path: str) -> Dict:
        """Load YAML configuration file."""
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            self.logger.warning(f"[WARN] Config file not found: {config_path}, using defaults")
            return self._get_default_config()
        except Exception as e:
            self.logger.error(f"[ERROR] Config load failed: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Return default configuration."""
        return {
            'scoring': {
                'high_priority_min': 70,
                'medium_priority_min': 50,
            },
            'website': {
                'timeout_seconds': 10,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            'performance': {
                'cache': {
                    'enabled': True,
                    'cache_file': 'data/cache_v3.json',
                    'ttl_days': 30
                },
                'max_workers': 10
            }
        }

    def _setup_logging(self):
        """Setup logging configuration."""
        log_dir = Path('logs')
        log_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S',
            handlers=[
                logging.FileHandler(log_dir / 'filter_leads_v3.log', encoding='utf-8')
            ]
        )

        self.logger = logging.getLogger(__name__)

    def _load_cache(self):
        """Load analysis cache from disk."""
        cache_file = self.config['performance']['cache']['cache_file']

        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    self.cache = json.load(f)
                self.logger.info(f"[CACHE] Loaded {len(self.cache)} cached analyses")
            except Exception as e:
                self.logger.error(f"[ERROR] Cache load failed: {e}")

    def _save_cache(self):
        """Save analysis cache to disk."""
        if not self.config.get('performance', {}).get('cache', {}).get('enabled'):
            return

        cache_file = self.config['performance']['cache']['cache_file']
        Path(cache_file).parent.mkdir(parents=True, exist_ok=True)

        # Remove old cache entries
        ttl_days = self.config['performance']['cache'].get('ttl_days', 30)
        cutoff_time = (datetime.now() - timedelta(days=ttl_days)).timestamp()

        self.cache = {
            k: v for k, v in self.cache.items()
            if v.get('timestamp', 0) > cutoff_time
        }

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2)
            self.logger.info(f"[CACHE] Cache saved ({len(self.cache)} entries)")
        except Exception as e:
            self.logger.error(f"[ERROR] Cache save failed: {e}")

    # ========================================================================
    # SCORING METHODS - BALANCED V3
    # ========================================================================

    def calculate_score(self, lead: Dict) -> Tuple[int, Dict, str]:
        """
        Calculate balanced V3 score for a lead.

        Returns:
            (total_score, breakdown, priority_signal)
        """
        breakdown = {}
        signals = []

        # 1. Business Health Score (35 points max)
        health_score, health_signals = self._score_business_health(lead)
        breakdown['business_health'] = health_score
        signals.extend(health_signals)

        # 2. Website Redesign Opportunity (30 points max)
        redesign_score, redesign_signals = self._score_redesign_opportunity(lead)
        breakdown['redesign_opportunity'] = redesign_score
        signals.extend(redesign_signals)

        # 3. Industry Fit (25 points max)
        industry_score, industry_signals = self._score_industry_fit(lead)
        breakdown['industry_fit'] = industry_score
        signals.extend(industry_signals)

        # 4. Timing Signals (10 points max)
        timing_score, timing_signals = self._score_timing_signals(lead)
        breakdown['timing'] = timing_score
        signals.extend(timing_signals)

        total_score = sum([health_score, redesign_score, industry_score, timing_score])
        priority_signal = " | ".join(signals) if signals else "Standard prospect"

        return total_score, breakdown, priority_signal

    def _score_business_health(self, lead: Dict) -> Tuple[int, List[str]]:
        """
        Score business health (35 points max).
        Healthy businesses can afford websites, regardless of industry.
        """
        score = 0
        signals = []

        # Active Business Signals (20 points)
        google_reviews = lead.get('google_reviews_count', 0)
        if google_reviews >= 10:
            score += 10
            signals.append(f"{google_reviews} reviews")
        elif google_reviews >= 5:
            score += 5

        # Check for recent reviews (within 3 months)
        # This would require scraping Google Business, placeholder for now
        recent_reviews = lead.get('recent_reviews', False)
        if recent_reviews:
            score += 5
            signals.append("Recent activity")

        # Social media activity
        social_active = lead.get('social_media_active', False)
        if social_active:
            score += 5
            signals.append("Active social media")

        # Phone verified
        if lead.get('phone_verified', False):
            score += 3

        # Physical location (not home address)
        if lead.get('physical_location', False):
            score += 2

        # Revenue Signals (15 points)
        employees = lead.get('employees', 0)
        if 5 <= employees <= 20:
            score += 10
            signals.append(f"{employees} employees (ideal size)")
        elif 20 < employees <= 50:
            score += 8
        elif 3 <= employees <= 5:
            score += 7
        elif 1 <= employees <= 2:
            score += 3
            signals.append("Small team (lower budget)")
        elif employees > 50:
            score += 2
            signals.append("Large company (harder to reach)")

        # Multiple locations bonus
        locations = lead.get('locations_count', 1)
        if locations > 1:
            score += 5
            signals.append(f"{locations} locations")

        return min(score, 35), signals

    def _score_redesign_opportunity(self, lead: Dict) -> Tuple[int, List[str]]:
        """
        Score website redesign opportunity (30 points max).

        Context matters:
        - NO website + active business = 30pts (Vemsi cafe)
        - DIY website = 25-30pts (dimsumspot.cz)
        - Professional intent site = 5-10pts (bondcafe.cz)
        - Modern site = -10pts (reject)
        """
        website_url = lead.get('website', '')

        # Handle NaN/float values
        if pd.isna(website_url) or not isinstance(website_url, str):
            website_url = ''
        else:
            website_url = website_url.strip()

        signals = []

        # Scenario A: NO Website
        if not website_url or website_url.lower() in ['n/a', 'none', '']:
            # Check business health context
            reviews = lead.get('google_reviews_count', 0)
            social_active = lead.get('social_media_active', False)
            business_age_years = lead.get('business_age_years', 0)

            if reviews >= 10 or social_active:
                signals.append("NO WEBSITE + Active business = GOLDEN!")
                return 30, signals
            elif business_age_years >= 5:
                signals.append("No website, established business (may not want one)")
                return 15, signals
            elif business_age_years < 0.5:  # Less than 6 months
                signals.append("Too new, no website yet")
                return 10, signals
            else:
                signals.append("No website")
                return 20, signals

        # Scenario B: HAS Website - Analyze it
        website_analysis = self._analyze_website(website_url)

        # Check if recently redesigned (AUTO-REJECT)
        if website_analysis.get('modern_penalty', False):
            signals.append("RECENTLY REDESIGNED - SKIP")
            return -10, signals

        # Check if professional design intent (LOW PRIORITY)
        if website_analysis.get('professional_intent', False):
            signals.append("Already invested in professional design")
            return 7, signals

        # DIY/Outdated Website (PERFECT LEADS!)
        score = 0

        if website_analysis.get('diy_builder'):
            score += 15
            signals.append(f"DIY builder: {website_analysis['diy_builder']}")

        copyright_year = website_analysis.get('copyright_year')
        if copyright_year and copyright_year <= 2020:
            score += 10
            signals.append(f"Old copyright: {copyright_year}")

        if not website_analysis.get('has_ssl', True):
            score += 8
            signals.append("No HTTPS")

        if not website_analysis.get('mobile_friendly', True):
            score += 8
            signals.append("Not mobile-friendly")

        if website_analysis.get('deprecated_tech', False):
            score += 10
            signals.append("Uses Flash/deprecated tech")

        if website_analysis.get('broken_links', 0) > 0:
            score += 5
            signals.append(f"{website_analysis['broken_links']} broken links")

        if website_analysis.get('slow_load', False):
            score += 5
            signals.append("Slow load time")

        if score > 0:
            signals.append("DIY/outdated website - PERFECT!")

        return min(score, 30), signals

    def _score_industry_fit(self, lead: Dict) -> Tuple[int, List[str]]:
        """
        Score industry fit (25 points max).
        Simplified 5-tier system - all get chances!
        """
        industry_text = str(lead.get('industry', '')).lower()
        company_name = str(lead.get('company_name', '')).lower()
        combined_text = f"{industry_text} {company_name}"

        signals = []

        # Tier 1: High Budget B2B (25 points)
        tier1_keywords = ['legal', 'law', 'advokát', 'accounting', 'financial', 'audit',
                          'medical', 'dental', 'clinic', 'lékař']
        if any(kw in combined_text for kw in tier1_keywords):
            signals.append("Tier 1: High budget B2B (€8k-€15k)")
            return 25, signals

        # Tier 2: Medium Budget B2B (20 points)
        tier2_keywords = ['architecture', 'engineering', 'insurance', 'consulting',
                          'realit', 'nemovitost']
        if any(kw in combined_text for kw in tier2_keywords):
            signals.append("Tier 2: Medium budget B2B (€5k-€10k)")
            return 20, signals

        # Tier 3: Customer-Facing Services (18 points)
        tier3_keywords = ['restaurant', 'hotel', 'gym', 'fitness', 'salon', 'spa',
                          'wedding', 'event', 'beauty', 'wellness']
        if any(kw in combined_text for kw in tier3_keywords):
            signals.append("Tier 3: Customer-facing (€3k-€8k)")
            return 18, signals

        # Tier 4: Retail & Trades (15 points)
        tier4_keywords = ['retail', 'store', 'shop', 'plumbing', 'hvac', 'electric',
                          'auto', 'repair', 'obchod']
        if any(kw in combined_text for kw in tier4_keywords):
            signals.append("Tier 4: Retail/Trades (€2k-€5k)")
            return 15, signals

        # Tier 5: Small Local (10 points) - includes cafes!
        tier5_keywords = ['cafe', 'coffee', 'bar', 'pub', 'bistro', 'kavárna',
                          'food truck', 'artisan', 'freelancer']
        if any(kw in combined_text for kw in tier5_keywords):
            signals.append("Tier 5: Small local (€1k-€3k, high conversion!)")
            return 10, signals

        # Default: Give them a chance
        signals.append("General business (€2k-€5k)")
        return 12, signals

    def _score_timing_signals(self, lead: Dict) -> Tuple[int, List[str]]:
        """
        Score timing signals (10 points max).
        Recent changes = good timing.
        """
        score = 0
        signals = []

        business_age_years = lead.get('business_age_years', 0)

        # Business opened 3-5 years ago (likely still on original site)
        if 3 <= business_age_years <= 5:
            score += 8
            signals.append(f"{business_age_years:.1f} years old (redesign cycle)")

        # New location or expansion
        if lead.get('new_location_recent', False):
            score += 5
            signals.append("New location opened")

        # Rebranding detected
        if lead.get('rebranding_detected', False):
            score += 10
            signals.append("REBRANDING DETECTED - PERFECT TIMING!")

        # Hiring (growing business)
        if lead.get('hiring_recent', False):
            score += 5
            signals.append("Recently hiring")

        # Warning signals
        if lead.get('temporarily_closed', False):
            signals.append("WARNING: Temporarily closed")
            score -= 5

        return min(score, 10), signals

    def _analyze_website(self, url: str) -> Dict:
        """
        Analyze website for redesign opportunity.
        FREE scraping only, no expensive APIs.
        """
        if not url.startswith('http'):
            url = 'https://' + url

        analysis = {
            'has_ssl': url.startswith('https://'),
            'mobile_friendly': False,
            'diy_builder': None,
            'copyright_year': None,
            'professional_intent': False,
            'modern_penalty': False,
            'deprecated_tech': False,
            'broken_links': 0,
            'slow_load': False
        }

        try:
            # Time the request
            start_time = time.time()

            user_agent = self.config.get('website', {}).get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            timeout = self.config.get('website', {}).get('timeout_seconds', 10)

            response = requests.get(
                url,
                timeout=timeout,
                headers={'User-Agent': user_agent},
                allow_redirects=True
            )

            load_time = time.time() - start_time
            analysis['slow_load'] = load_time > 5  # 5 seconds threshold

            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            html_lower = response.text.lower()

            # Check mobile-friendly
            viewport = soup.find('meta', attrs={'name': 'viewport'})
            analysis['mobile_friendly'] = viewport is not None

            # Detect DIY builders
            diy_indicators = {
                'wix.com': 'Wix',
                'weebly.com': 'Weebly',
                'wordpress.com': 'WordPress.com',
                'squarespace.com': 'Squarespace',
                'webnode.cz': 'Webnode',
                'carrd.co': 'Carrd'
            }

            for indicator, name in diy_indicators.items():
                if indicator in url or indicator in html_lower:
                    analysis['diy_builder'] = name
                    break

            # Check copyright year
            footer = soup.find('footer') or soup.find(id='footer') or soup.find(class_='footer')
            if footer:
                footer_text = footer.get_text()
                years = re.findall(r'\b(20\d{2})\b', footer_text)
                if years:
                    analysis['copyright_year'] = max(int(y) for y in years)

            # Check for professional design intent (like bondcafe.cz)
            professional_indicators = [
                '<video', 'data-aos', 'gsap', 'animation', 'parallax',
                'custom-navigation', 'hero-section', 'brand-colors'
            ]
            professional_count = sum(1 for ind in professional_indicators if ind in html_lower)
            analysis['professional_intent'] = professional_count >= 3

            # Check for modern penalty (recently redesigned)
            modern_indicators = [
                analysis['has_ssl'],
                analysis['mobile_friendly'],
                '@media' in html_lower,  # Responsive CSS
                load_time < 3,  # Fast load
                analysis.get('copyright_year', 0) >= 2023
            ]
            analysis['modern_penalty'] = sum(modern_indicators) >= 4

            # Check for deprecated tech
            analysis['deprecated_tech'] = '.swf' in html_lower or 'flash' in html_lower

            # Sample check for broken images
            images = soup.find_all('img', src=True)[:5]
            for img in images:
                img_src = img['src']
                if img_src.startswith('http') and not self._check_resource(img_src):
                    analysis['broken_links'] += 1

        except Exception as e:
            self.logger.error(f"[ERROR] Website analysis failed for {url}: {e}")

        return analysis

    def _check_resource(self, url: str) -> bool:
        """Check if a resource URL is accessible."""
        try:
            response = requests.head(url, timeout=3)
            return response.status_code < 400
        except:
            return False

    # ========================================================================
    # AUTO-REJECT LOGIC
    # ========================================================================

    def should_auto_reject(self, lead: Dict) -> Tuple[bool, Optional[str]]:
        """
        Check if lead should be auto-rejected.
        ONLY reject for clear reasons!
        """
        company_name = str(lead.get('company_name', '')).lower()
        industry = str(lead.get('industry', '')).lower()

        # 1. Government entities
        gov_keywords = ['ministry', 'municipality', 'government', 'město', 'obec',
                        'úřad', 'ministerstvo', 'krajský']
        if any(kw in company_name or kw in industry for kw in gov_keywords):
            return True, "Government entity"

        # 2. Large corporations (50+ employees)
        if lead.get('employees', 0) > 50:
            return True, "Large corporation (50+ employees)"

        # 3. Permanently closed (must be verified!)
        if lead.get('permanently_closed', False):
            return True, "Permanently closed"

        # 4. Recently redesigned (from website analysis)
        # This is checked in scoring, not here

        return False, None

    # ========================================================================
    # DATA ENRICHMENT
    # ========================================================================

    def enrich_lead(self, lead: Dict) -> Dict:
        """
        Enrich lead with calculated/derived fields.
        Handles missing data gracefully.
        """
        enriched = lead.copy()

        # Calculate business age from registration_date
        if 'registration_date' in lead and lead['registration_date']:
            try:
                reg_date = pd.to_datetime(lead['registration_date'])
                age_years = (pd.Timestamp.now() - reg_date).days / 365.25
                enriched['business_age_years'] = age_years
            except:
                enriched['business_age_years'] = 0
        else:
            enriched['business_age_years'] = 0

        # Set defaults for fields that need scraping (we'll add scraping later)
        enriched.setdefault('google_reviews_count', 0)
        enriched.setdefault('recent_reviews', False)
        enriched.setdefault('social_media_active', False)
        enriched.setdefault('phone_verified', bool(lead.get('phone')))
        enriched.setdefault('physical_location', bool(lead.get('address')))
        enriched.setdefault('locations_count', 1)
        enriched.setdefault('new_location_recent', False)
        enriched.setdefault('rebranding_detected', False)
        enriched.setdefault('hiring_recent', False)
        enriched.setdefault('temporarily_closed', False)
        enriched.setdefault('permanently_closed', False)

        return enriched

    # ========================================================================
    # MAIN PROCESSING
    # ========================================================================

    def process_lead(self, lead: Dict) -> Dict:
        """Process a single lead and return enriched data."""
        try:
            # Enrich lead with calculated fields
            lead = self.enrich_lead(lead)

            # Check for auto-reject
            should_reject, reject_reason = self.should_auto_reject(lead)

            if should_reject:
                self.rejection_reasons[reject_reason] += 1
                return {
                    **lead,
                    'score': 0,
                    'priority': 'REJECTED',
                    'rejection_reason': reject_reason,
                    'breakdown': {},
                    'signals': ''
                }

            # Calculate score
            score, breakdown, signals = self.calculate_score(lead)

            # Determine priority
            high_min = self.config.get('scoring', {}).get('high_priority_min', 70)
            medium_min = self.config.get('scoring', {}).get('medium_priority_min', 50)

            if score >= high_min:
                priority = 'HIGH'
                self.statistics['high_priority'] += 1
            elif score >= medium_min:
                priority = 'MEDIUM'
                self.statistics['medium_priority'] += 1
            elif score >= 30:
                priority = 'LOW'
                self.statistics['low_priority'] += 1
            else:
                priority = 'REJECTED'
                self.statistics['rejected'] += 1
                self.rejection_reasons['Score too low'] += 1

            return {
                **lead,
                'score': score,
                'priority': priority,
                'breakdown': breakdown,
                'signals': signals,
                'rejection_reason': '' if priority != 'REJECTED' else 'Score too low'
            }

        except Exception as e:
            self.logger.error(f"[ERROR] Failed to process lead: {e}")
            return {
                **lead,
                'score': 0,
                'priority': 'ERROR',
                'error': str(e)
            }

    def run(self, input_file: str):
        """Main entry point - process leads from input file."""
        try:
            print(f"\n>> Loading leads from {input_file}...")

            # Load input file
            if input_file.endswith('.csv'):
                df = pd.read_csv(input_file)
            elif input_file.endswith('.xlsx'):
                df = pd.read_excel(input_file)
            else:
                raise ValueError(f"Unsupported file format: {input_file}")

            print(f">> Loaded {len(df)} leads")

            # Convert to list of dicts
            leads = df.to_dict('records')

            # Process leads (with threading)
            max_workers = self.config.get('performance', {}).get('max_workers', 5)
            print(f"\n>> Processing leads with {max_workers} workers...")

            results = []
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                futures = {executor.submit(self.process_lead, lead): lead for lead in leads}

                for future in tqdm(as_completed(futures), total=len(leads), desc="Processing leads"):
                    result = future.result()
                    results.append(result)

            # Convert to DataFrame
            results_df = pd.DataFrame(results)

            # Sort by score (descending)
            results_df = results_df.sort_values('score', ascending=False)

            # Save outputs
            output_dir = Path('data/output')
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

            # Save full results
            results_df.to_csv(output_dir / f'leads_v3_balanced_{timestamp}.csv', index=False)

            # Save priority tiers
            for priority in ['HIGH', 'MEDIUM', 'LOW']:
                tier_df = results_df[results_df['priority'] == priority]
                if len(tier_df) > 0:
                    tier_df.to_csv(output_dir / f'leads_{priority.lower()}_{timestamp}.csv', index=False)

            # Save rejected
            rejected_df = results_df[results_df['priority'] == 'REJECTED']
            if len(rejected_df) > 0:
                rejected_df.to_csv(output_dir / f'leads_rejected_{timestamp}.csv', index=False)

            # Save cache
            self._save_cache()

            self.logger.info("[DONE] Processing complete!")

            # Print summary
            print("\n" + "=" * 80)
            print("PROCESSING SUMMARY - BALANCED V3")
            print("=" * 80)
            print(f"[OK] Total processed: {len(results_df)}")
            print(f"  - High priority:   {self.statistics['high_priority']}")
            print(f"  - Medium priority: {self.statistics['medium_priority']}")
            print(f"  - Low priority:    {self.statistics['low_priority']}")
            print(f"  - Rejected:        {self.statistics['rejected']}")
            print("=" * 80)

            if self.rejection_reasons:
                print("\nREJECTION REASONS:")
                for reason, count in self.rejection_reasons.most_common():
                    print(f"  - {reason}: {count}")
                print("=" * 80)

            # Top 10 leads
            print("\nTOP 10 LEADS:")
            top_10 = results_df.head(10)
            for idx, lead in top_10.iterrows():
                print(f"\n{lead.get('company_name', 'Unknown')}: {lead['score']}/100 ({lead['priority']})")
                print(f"  {lead.get('signals', '')}")
            print("=" * 80)

        except Exception as e:
            self.logger.error(f"[ERROR] Processing failed: {e}", exc_info=True)
            raise


# ============================================================================
# CLI INTERFACE
# ============================================================================

def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Lead Filtering System V3 - Balanced & Context-Aware"
    )
    parser.add_argument(
        'input_file',
        help="Path to CSV or Excel file with leads"
    )
    parser.add_argument(
        '--config',
        default='config.yaml',
        help="Path to configuration file (default: config.yaml)"
    )

    args = parser.parse_args()

    # Create and run filter
    filter_system = LeadFilterBalancedV3(config_path=args.config)
    filter_system.run(args.input_file)


if __name__ == '__main__':
    main()
