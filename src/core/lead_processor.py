"""
Enhanced Lead Processor with Niche Detection
=============================================
Production-ready lead filtering, scoring, and organization.

Features:
- Smart niche detection (restaurant, hotel, cafe, salon, etc.)
- Multi-factor scoring (0-100)
- Tiered classification (Tier 1/2/3 or reject)
- Data cleaning and deduplication
- Automatic enrichment
- Batch processing with caching
"""

import pandas as pd
import re
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from src.utils.logger import SystemLogger
from src.utils.validators import Validators
from src.utils.helpers import FileHelper, IDGenerator, DateHelper, TextHelper


class LeadProcessor:
    """
    Enhanced lead processor with intelligent niche detection and scoring.
    """

    def __init__(self, config: Dict):
        """Initialize the lead processor."""
        self.config = config
        self.logger = SystemLogger.get_logger(__name__, config.get('logging'))

        # Statistics
        self.stats = {
            'total_processed': 0,
            'tier1_count': 0,
            'tier2_count': 0,
            'tier3_count': 0,
            'rejected_count': 0,
            'niche_distribution': Counter(),
            'rejection_reasons': Counter()
        }

        # Cache
        self.cache = {}
        self._load_cache()

        self.logger.info("Lead Processor initialized")

    def _load_cache(self):
        """Load cached scores and analysis."""
        cache_file = self.config.get('paths', {}).get('cache', {}).get('lead_scores')
        if cache_file:
            self.cache = FileHelper.load_json(cache_file, {})
            self.logger.info(f"Loaded {len(self.cache)} cached lead scores")

    def _save_cache(self):
        """Save cache to disk."""
        cache_file = self.config.get('paths', {}).get('cache', {}).get('lead_scores')
        if cache_file:
            FileHelper.save_json(cache_file, self.cache)
            self.logger.info(f"Saved {len(self.cache)} lead scores to cache")

    def process_file(self, filepath: str) -> Dict[str, pd.DataFrame]:
        """
        Process leads from CSV/XLSX file.

        Returns:
            Dict with keys: 'tier1', 'tier2', 'tier3', 'rejected'
        """
        self.logger.info(f"Processing file: {filepath}")

        # Load file
        df = self._load_file(filepath)
        if df is None or df.empty:
            self.logger.error("No data loaded from file")
            return {}

        # Clean and validate
        df = self._clean_data(df)

        # Deduplicate
        df = self._deduplicate(df)

        self.logger.info(f"Processing {len(df)} leads...")

        # Process each lead
        results = []

        # Use threading for parallel processing
        max_workers = self.config.get('lead_processing', {}).get('max_workers', 20)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_lead = {
                executor.submit(self._process_single_lead, row): idx
                for idx, row in df.iterrows()
            }

            # Process results with progress bar
            for future in tqdm(as_completed(future_to_lead), total=len(df), desc="Processing leads"):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as e:
                    self.logger.error(f"Error processing lead: {e}")

        # Convert to DataFrame
        results_df = pd.DataFrame(results)

        # Split into tiers
        output = self._split_by_tier(results_df)

        # Update statistics
        self._update_stats(output)

        # Save cache
        self._save_cache()

        self.logger.info(f"Processing complete: Tier1={self.stats['tier1_count']}, "
                        f"Tier2={self.stats['tier2_count']}, Tier3={self.stats['tier3_count']}, "
                        f"Rejected={self.stats['rejected_count']}")

        return output

    def _load_file(self, filepath: str) -> Optional[pd.DataFrame]:
        """Load CSV or XLSX file."""
        path = Path(filepath)

        if not path.exists():
            self.logger.error(f"File not found: {filepath}")
            return None

        try:
            if path.suffix.lower() == '.csv':
                df = pd.read_csv(filepath, encoding='utf-8')
            elif path.suffix.lower() in ['.xlsx', '.xls']:
                df = pd.read_excel(filepath)
            else:
                self.logger.error(f"Unsupported file type: {path.suffix}")
                return None

            self.logger.info(f"Loaded {len(df)} rows from {filepath}")
            return df

        except Exception as e:
            self.logger.error(f"Error loading file: {e}")
            return None

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and normalize data."""
        self.logger.info("Cleaning data...")

        # Rename columns to standard names (handle various formats)
        column_mapping = {
            'company': 'company_name',
            'name': 'company_name',
            'business_name': 'company_name',
            'e-mail': 'email',
            'mail': 'email',
            'email_address': 'email',
            'telephone': 'phone',
            'tel': 'phone',
            'mobile': 'phone',
            'web': 'website',
            'url': 'website',
            'site': 'website',
            'category': 'industry',
            'type': 'industry',
            'business_type': 'industry',
            'founded': 'registration_date',
            'established': 'registration_date',
            'staff': 'employees',
            'employee_count': 'employees',
        }

        # Apply column mapping (case-insensitive)
        df.columns = df.columns.str.strip().str.lower()
        df.rename(columns=column_mapping, inplace=True)

        # Normalize URLs
        if 'website' in df.columns:
            df['website'] = df['website'].apply(lambda x: Validators.normalize_url(str(x)) if pd.notna(x) else None)

        # Normalize phones
        if 'phone' in df.columns:
            df['phone'] = df['phone'].apply(lambda x: Validators.normalize_phone(str(x)) if pd.notna(x) else None)

        # Clean text fields
        text_columns = ['company_name', 'industry', 'address']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].apply(lambda x: TextHelper.clean_whitespace(str(x)) if pd.notna(x) else None)

        # Convert employees to int
        if 'employees' in df.columns:
            df['employees'] = pd.to_numeric(df['employees'], errors='coerce').fillna(0).astype(int)

        self.logger.info(f"Data cleaned. Columns: {list(df.columns)}")
        return df

    def _deduplicate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate leads."""
        before = len(df)

        # Deduplicate by company name + email
        df = df.drop_duplicates(subset=['company_name'], keep='first')

        after = len(df)
        removed = before - after

        if removed > 0:
            self.logger.info(f"Removed {removed} duplicate leads")

        return df

    def _process_single_lead(self, row: pd.Series) -> Optional[Dict]:
        """Process a single lead."""
        try:
            # Extract basic info
            company_name = row.get('company_name', '')
            email = row.get('email', '')
            phone = row.get('phone', '')
            website = row.get('website', '')
            industry = row.get('industry', '')
            address = row.get('address', '')
            employees = row.get('employees', 0)
            registration_date = row.get('registration_date', '')

            # Generate lead ID
            lead_id = IDGenerator.generate_lead_id(
                email or company_name,
                company_name
            )

            # Check cache
            if lead_id in self.cache:
                cached = self.cache[lead_id].copy()
                cached['from_cache'] = True
                return cached

            # Auto-reject checks
            reject_reason = self._should_reject(row)
            if reject_reason:
                result = {
                    'lead_id': lead_id,
                    'company_name': company_name,
                    'email': email,
                    'phone': phone,
                    'website': website,
                    'industry': industry,
                    'address': address,
                    'employees': employees,
                    'tier': 'rejected',
                    'score': 0,
                    'rejection_reason': reject_reason,
                    'niche': None
                }
                self.cache[lead_id] = result
                return result

            # Detect niche
            niche = self._detect_niche(company_name, industry, website)

            # Calculate score
            score_data = self._calculate_score(row, niche)

            # Determine tier
            tier = self._determine_tier(score_data['total_score'])

            # Build result
            result = {
                'lead_id': lead_id,
                'company_name': company_name,
                'email': email,
                'phone': phone,
                'website': website,
                'industry': industry,
                'address': address,
                'employees': employees,
                'niche': niche,
                'tier': tier,
                'score': score_data['total_score'],
                'score_breakdown': score_data['breakdown'],
                'notes': score_data.get('notes', ''),
                'from_cache': False
            }

            # Cache result
            self.cache[lead_id] = result

            return result

        except Exception as e:
            self.logger.error(f"Error processing lead: {e}")
            return None

    def _should_reject(self, row: pd.Series) -> Optional[str]:
        """
        Check if lead should be auto-rejected.

        Returns rejection reason or None.
        """
        company_name = str(row.get('company_name', ''))
        employees = row.get('employees', 0)
        website = str(row.get('website', ''))

        # No contact info
        email = row.get('email', '')
        phone = row.get('phone', '')
        if not email and not phone and not website:
            return "No contact information"

        # Government entity
        if Validators.is_government_entity(company_name):
            return "Government entity"

        # Large corporation (50+ employees)
        if employees >= 50:
            return "Large corporation (likely has in-house team)"

        # Check for B2B-only keywords
        b2b_keywords = self.config.get('auto_reject', {}).get('b2b_only', {}).get('keywords', [])
        if TextHelper.contains_any(company_name, b2b_keywords):
            return "B2B-only industry"

        return None

    def _detect_niche(self, company_name: str, industry: str, website: str) -> str:
        """Detect business niche from available data."""
        # Combine all text for analysis
        text = f"{company_name} {industry}".lower()

        # Check against niche keywords
        niches_config = self.config.get('niches', {}).get('detection', {})

        for niche_name, niche_data in niches_config.items():
            keywords = niche_data.get('keywords', [])
            if TextHelper.contains_any(text, keywords):
                return niche_name

        return 'default'

    def _calculate_score(self, row: pd.Series, niche: str) -> Dict:
        """
        Calculate lead score (0-100).

        Scoring factors:
        - Business health (35 points)
        - Redesign opportunity (30 points)
        - Industry fit (25 points)
        - Timing signals (10 points)
        """
        score = 0
        breakdown = {}
        notes = []

        # 1. Business Health (35 points)
        health_score = self._score_business_health(row)
        score += health_score
        breakdown['business_health'] = health_score

        # 2. Redesign Opportunity (30 points)
        redesign_score = self._score_redesign_opportunity(row)
        score += redesign_score
        breakdown['redesign_opportunity'] = redesign_score

        # 3. Industry Fit (25 points)
        industry_score = self._score_industry_fit(niche)
        score += industry_score
        breakdown['industry_fit'] = industry_score

        # 4. Timing Signals (10 points)
        timing_score = self._score_timing(row)
        score += timing_score
        breakdown['timing'] = timing_score

        # Apply niche multiplier
        niches_config = self.config.get('niches', {}).get('detection', {})
        multiplier = niches_config.get(niche, {}).get('priority_multiplier', 1.0)
        score = min(100, int(score * multiplier))

        # Generate notes
        if score >= 85:
            notes.append("EXCELLENT LEAD - Personalized demo recommended")
        elif score >= 70:
            notes.append("GOOD LEAD - Mockup + portfolio recommended")
        elif score >= 60:
            notes.append("POTENTIAL LEAD - Portfolio email recommended")

        if not row.get('website'):
            notes.append("No website - great opportunity")

        return {
            'total_score': score,
            'breakdown': breakdown,
            'notes': ' | '.join(notes)
        }

    def _score_business_health(self, row: pd.Series) -> int:
        """Score business health (0-35 points)."""
        score = 0

        # Employee count
        employees = row.get('employees', 0)
        if 3 <= employees <= 20:
            score += 15  # Sweet spot
        elif 21 <= employees <= 50:
            score += 10
        elif employees > 0:
            score += 5

        # Has contact info
        if row.get('email'):
            score += 10
        if row.get('phone'):
            score += 5

        # Has address (local business)
        if row.get('address'):
            score += 5

        return min(35, score)

    def _score_redesign_opportunity(self, row: pd.Series) -> int:
        """Score redesign opportunity (0-30 points)."""
        website = row.get('website')

        # No website = opportunity
        if not website:
            return 30

        # Old website = opportunity (would need website analysis here)
        # For now, assume any existing website is moderate opportunity
        return 15

    def _score_industry_fit(self, niche: str) -> int:
        """Score industry fit based on niche (0-25 points)."""
        # High-value niches
        high_value = ['restaurant', 'hotel', 'cafe', 'salon']
        if niche in high_value:
            return 25

        # Medium-value niches
        medium_value = ['fitness', 'retail', 'professional']
        if niche in medium_value:
            return 18

        # Default
        return 10

    def _score_timing(self, row: pd.Series) -> int:
        """Score timing signals (0-10 points)."""
        score = 0

        # New business (< 2 years)
        registration_date = row.get('registration_date', '')
        if registration_date:
            months = DateHelper.months_since(str(registration_date))
            if months and months <= 24:
                score += 10
            elif months and months <= 60:
                score += 5

        return min(10, score)

    def _determine_tier(self, score: int) -> str:
        """Determine tier based on score."""
        thresholds = self.config.get('lead_processing', {}).get('tiers', {})

        tier1_min = thresholds.get('tier1_min', 85)
        tier2_min = thresholds.get('tier2_min', 70)
        tier3_min = thresholds.get('tier3_min', 60)

        if score >= tier1_min:
            return 'tier1'
        elif score >= tier2_min:
            return 'tier2'
        elif score >= tier3_min:
            return 'tier3'
        else:
            return 'rejected'

    def _split_by_tier(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """Split results into tiers."""
        return {
            'tier1': df[df['tier'] == 'tier1'].copy(),
            'tier2': df[df['tier'] == 'tier2'].copy(),
            'tier3': df[df['tier'] == 'tier3'].copy(),
            'rejected': df[df['tier'] == 'rejected'].copy()
        }

    def _update_stats(self, output: Dict[str, pd.DataFrame]):
        """Update processing statistics."""
        self.stats['tier1_count'] = len(output.get('tier1', []))
        self.stats['tier2_count'] = len(output.get('tier2', []))
        self.stats['tier3_count'] = len(output.get('tier3', []))
        self.stats['rejected_count'] = len(output.get('rejected', []))

        self.stats['total_processed'] = (
            self.stats['tier1_count'] +
            self.stats['tier2_count'] +
            self.stats['tier3_count'] +
            self.stats['rejected_count']
        )

        # Niche distribution
        for tier_name, tier_df in output.items():
            if tier_name != 'rejected' and not tier_df.empty:
                for niche in tier_df['niche']:
                    self.stats['niche_distribution'][niche] += 1

        # Rejection reasons
        rejected_df = output.get('rejected', pd.DataFrame())
        if not rejected_df.empty and 'rejection_reason' in rejected_df.columns:
            for reason in rejected_df['rejection_reason']:
                self.stats['rejection_reasons'][reason] += 1

    def get_statistics(self) -> Dict:
        """Get processing statistics."""
        return self.stats.copy()

    def export_results(self, output: Dict[str, pd.DataFrame], output_dir: str):
        """Export results to CSV files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        files_created = []

        for tier_name, tier_df in output.items():
            if tier_df.empty:
                continue

            filename = output_path / f"{tier_name.upper()}_LEADS.csv"
            tier_df.to_csv(filename, index=False, encoding='utf-8-sig')
            files_created.append(str(filename))

            self.logger.info(f"Exported {len(tier_df)} {tier_name} leads to {filename}")

        # Export statistics
        stats_file = output_path / "STATISTICS.txt"
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write("LEAD PROCESSING STATISTICS\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Total Processed: {self.stats['total_processed']}\n")
            f.write(f"Tier 1 (Premium): {self.stats['tier1_count']}\n")
            f.write(f"Tier 2 (Good): {self.stats['tier2_count']}\n")
            f.write(f"Tier 3 (Potential): {self.stats['tier3_count']}\n")
            f.write(f"Rejected: {self.stats['rejected_count']}\n\n")

            f.write("Niche Distribution:\n")
            for niche, count in self.stats['niche_distribution'].most_common():
                f.write(f"  {niche}: {count}\n")

            f.write("\nRejection Reasons:\n")
            for reason, count in self.stats['rejection_reasons'].most_common():
                f.write(f"  {reason}: {count}\n")

        files_created.append(str(stats_file))

        return files_created
