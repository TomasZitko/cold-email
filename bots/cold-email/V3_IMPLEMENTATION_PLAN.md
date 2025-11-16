# V3 Implementation Status & Plan

## Current Status: V2 Code with V3 Config

The codebase currently has:
- **V3 config file**: `config_v3_webdesign.yaml` (READY - defines all V3 scoring logic)
- **V2 code**: `bots/filter_leads_v2.py` (NEEDS UPDATE - still using V2 scoring)

## Key Findings

### What Works
1. ✅ Website scraping (SSL, mobile-friendly, responsive CSS, Flash detection)
2. ✅ Social media detection (Instagram, Facebook activity)
3. ✅ Basic industry categorization
4. ✅ Company size scoring
5. ✅ Copyright year detection
6. ✅ Website analysis caching

### What's Missing (Critical for V3)

#### 1. **Website Age Detection** ❌ NOT IMPLEMENTED
**V3 Requirement**: Detect website age for redesign probability scoring
**Needs**:
- WHOIS domain registration lookup
- Archive.org (Wayback Machine) last major change detection
- Return: `website_age_years` (float)

**Impact**: Without this, redesign probability scoring (30 points) cannot work

**Implementation Required**:
```python
def get_website_age(self, domain: str) -> Dict:
    """
    Get website age from WHOIS and archive.org
    Returns: {
        'domain_age_years': float,
        'last_redesign_years': float,
        'registration_date': str
    }
    """
    # Use python-whois library
    # Fallback to archive.org API
```

---

#### 2. **Business Status Detection** ❌ NOT IMPLEMENTED
**V3 Requirement**: Check if business is open/closed (page 123-160 in V3_UPGRADE_GUIDE.md)
**Needs**:
- Google Business Profile API integration
- Google Maps scraping (look for "Permanently closed" label)
- Website keyword detection ("permanently closed", "out of business", etc.)

**Impact**: Wastes time on dead businesses

**Implementation Required**:
```python
def check_business_status(self, company_name: str, website: str) -> str:
    """
    Check if business is operational
    Returns: 'open', 'closed', 'temporarily_closed', 'unknown'
    """
    # 1. Check Google Business Profile API
    # 2. Scrape Google Maps for closure label
    # 3. Check website for closure keywords
    # 4. Must fail 3 consecutive checks before marking closed
```

---

#### 3. **Redesign Probability Scoring** ❌ NOT IMPLEMENTED
**V3 Requirement**: Core V3 feature (30 points max)
**Current Code**: Uses `_score_business_age()` (V2 logic - 25 points)
**Should Be**: `_score_redesign_probability()` (V3 logic - 30 points)

**Scoring Logic**:
- 3-5 year old websites: 30 points (PERFECT redesign timing)
- 5-7 year old: 25 points (overdue)
- 0-2 year old: 0 points (recently redesigned - SKIP)
- **Bonus points**:
  - DIY template sites (Wix, Weebly, Squarespace): +12pts
  - Old copyright (≤2020): +8pts
  - Flash/deprecated tech: +10pts
  - Not mobile-friendly: +8pts

**Implementation Required**:
```python
def _score_redesign_probability(self, website_age: float, business_age: float,
                                website_analysis: Dict) -> int:
    """
    Score redesign probability (30 points max)
    Uses website age OR business age as proxy
    Adds bonus for DIY templates, old copyright, deprecated tech
    """
    # Implement V3 redesign_probability config logic
```

---

#### 4. **9-Tier Industry System** ❌ NOT IMPLEMENTED
**V3 Requirement**: Replace 4-tier with 9-tier system (pages 44-67 in V3_UPGRADE_GUIDE.md)
**Current Code**: Uses 4 tiers (customer_facing, professional_services, local_services, b2b_other)
**Should Be**: 9 tiers with dramatically different weights

| Current V2 | V2 Points | V3 Tier | V3 Points | Change |
|------------|-----------|---------|-----------|--------|
| Professional services | 15 | Tier 1 (Legal, Financial, Medical) | 30 | +15 (100% increase) |
| Customer-facing | 20 | Tier 9 (Cafes, Bars) | 5 | -15 (75% decrease) |

**Key Change**: Legal/Financial/Medical go from 15pts → 30pts (highest priority)

**Implementation Required**:
```python
def _score_industry_tier(self, lead: Dict) -> Tuple[int, str, str, str]:
    """
    Score industry using 9-tier system (30 points max)
    Returns: (points, tier_name, avg_project_value, conversion_probability)
    """
    # Check all 9 tiers from config_v3_webdesign.yaml
    # Return tier metadata for reporting
```

---

#### 5. **Business Maturity Scoring** ❌ PARTIALLY IMPLEMENTED
**V3 Requirement**: Replace "business age" with "business maturity" (revenue proxies)
**Current Code**: `_score_company_size()` gives 5 points max
**Should Be**: `_score_business_maturity()` gives 20 points max

**New Scoring Logic**:
- **Employee-based revenue proxy**:
  - 10-50 employees: 10pts (estimated $100k-$500k revenue)
  - 5-9 employees: 7pts (estimated $50k-$100k revenue)
- **Multi-location bonus**:
  - 2 locations: +5pts
  - 3-5 locations: +8pts
- **Online presence paradox**:
  - Active social + NO website: +10pts (GOLDEN)
  - Active social + BAD website: +7pts (ready for upgrade)
  - Google Reviews 20+: +4pts

**Implementation Required**:
```python
def _score_business_maturity(self, lead: Dict, website_analysis: Dict,
                             social_media: Dict) -> int:
    """
    Score business maturity (20 points max)
    Includes: revenue proxy, multi-location, online presence
    """
    # Implement V3 business_maturity config logic
```

---

#### 6. **DIY Template Detection** ⚠️ PARTIALLY IMPLEMENTED
**Current Code**: Detects Wix, Weebly in URL
**V3 Requirement**: Detect AND give +12 bonus points to redesign score

**Templates to Detect**:
- wix.com, weebly.com, wordpress.com (NOT .org)
- squarespace.com, webnode.cz, carrd.co
- Look in: HTML source, meta tags, CSS classes, JavaScript libraries

**Implementation Required**:
```python
def _detect_diy_template(self, url: str, html: str) -> Optional[str]:
    """
    Detect DIY website builder
    Returns: 'wix', 'weebly', 'squarespace', 'wordpress_com', etc. or None
    """
    # Check URL, meta tags, HTML comments, CSS classes
```

---

#### 7. **Modern Website Penalty** ❌ NOT IMPLEMENTED
**V3 Requirement**: If ALL modern indicators present, apply -10pts penalty

**Modern Indicators**:
- Has SSL (HTTPS)
- Mobile-friendly (viewport meta tag)
- Responsive CSS (media queries)
- Fast load time (<3 seconds)
- Current copyright (2023+)
- Domain age <2 years

**Signal**: "Recently redesigned - SKIP"

**Implementation Required**:
```python
def _check_modern_website_penalty(self, analysis: Dict, website_age: float) -> int:
    """
    Check if website is too modern (recently redesigned)
    Returns: -10 if all modern indicators present, else 0
    """
```

---

#### 8. **Enhanced Output Columns** ❌ NOT IMPLEMENTED
**V3 Requirement**: Add strategic columns for sales team (pages 187-208 in V3_UPGRADE_GUIDE.md)

**New Columns to Add**:
- `conversion_probability` - "10-15%" (from industry tier)
- `avg_project_value` - "$12,000" (from industry tier)
- `industry_tier` - "Tier 1 - Premium B2B"
- `redesign_probability` - 30 (out of 30)
- `business_maturity_score` - 18 (out of 20)
- `website_age_years` - 4.5
- `business_age_years` - 5
- `estimated_revenue` - "$100k-$500k" (from employee count)
- `google_reviews_count` - 47 (NEW scraping needed)
- `business_status` - "Open" (from status detection)

---

## V2 vs V3 Scoring Comparison

### V2 Current Scoring (100 points total):
```
Website Quality:  40 points (HIGH weight on website issues)
Business Age:     25 points (generic age scoring)
Industry Fit:     20 points (4-tier system)
Social Media:     10 points (bonus for active + no website)
Company Size:      5 points (employee count)
```

### V3 Target Scoring (100 points total):
```
Redesign Probability:  30 points (NEW - timing is everything)
Industry Tier:         30 points (9-tier, B2B focus)
Business Maturity:     20 points (revenue proxy, multi-location)
Website Issues:        15 points (reduced weight)
Engagement Signals:     5 points (reviews, social, activity)
```

**Key Philosophy Change**:
- **V2**: "Find bad websites" (any business with issues)
- **V3**: "Find profitable clients at the right time" (high-budget, ready to buy)

---

## Priority Implementation Order

### Phase 1: Core V3 Scoring (CRITICAL)
1. **Implement `_score_industry_tier()`** - 9-tier system
   - Config already exists in `config_v3_webdesign.yaml`
   - Replace `_score_industry_fit()`
   - Estimated: 2-3 hours

2. **Implement `_score_redesign_probability()`** - NEW scoring method
   - Config already exists
   - Replace `_score_business_age()`
   - Estimated: 3-4 hours (includes website age detection)

3. **Implement `_score_business_maturity()`** - Replaces company size
   - Config already exists
   - Replace `_score_company_size()`
   - Estimated: 2-3 hours

4. **Update `_score_website_quality()` → `_score_website_issues()`**
   - Reduce from 40pts to 15pts max
   - Add modern website penalty
   - Estimated: 1-2 hours

5. **Implement `_score_engagement_signals()`** - NEW scoring method
   - Google Reviews scraping
   - Social media activity
   - Estimated: 2-3 hours

### Phase 2: Website Age Detection (CRITICAL for Redesign Scoring)
6. **Implement `get_website_age()`**
   - WHOIS lookup using `python-whois` library
   - Archive.org API fallback
   - Cache results (TTL: 30 days)
   - Estimated: 4-5 hours

### Phase 3: Business Status Detection (HIGH PRIORITY)
7. **Implement `check_business_status()`**
   - Google Maps scraping (Selenium)
   - Website keyword detection
   - Auto-reject permanently closed businesses
   - Estimated: 3-4 hours

### Phase 4: Enhanced Features (MEDIUM PRIORITY)
8. **DIY Template Detection Enhancement**
   - Better detection logic
   - +12 bonus points for redesign score
   - Estimated: 1-2 hours

9. **Multi-location Detection**
   - Scrape Google Maps for multiple locations
   - +5 to +8 bonus points
   - Estimated: 2-3 hours

10. **Google Reviews Scraping**
    - Count reviews from Google Business Profile
    - +4 bonus points for 20+ reviews
    - Estimated: 2-3 hours

### Phase 5: Enhanced Output & Reporting (LOW PRIORITY)
11. **Add V3 Output Columns**
    - All new metadata columns
    - Update CSV output format
    - Estimated: 1-2 hours

12. **Update Statistics Report**
    - Pipeline value calculation (COUNT × AVG_PROJECT_VALUE)
    - Conversion probability by tier
    - Estimated: 1-2 hours

---

## Estimated Total Implementation Time

| Phase | Tasks | Hours | Priority |
|-------|-------|-------|----------|
| Phase 1: Core V3 Scoring | 5 tasks | 10-15 hours | CRITICAL |
| Phase 2: Website Age | 1 task | 4-5 hours | CRITICAL |
| Phase 3: Business Status | 1 task | 3-4 hours | HIGH |
| Phase 4: Enhanced Features | 3 tasks | 5-7 hours | MEDIUM |
| Phase 5: Output & Reporting | 2 tasks | 2-4 hours | LOW |
| **TOTAL** | **12 tasks** | **24-35 hours** | |

---

## Quick Start: Minimum Viable V3

To get V3 working with minimal changes (focus on highest impact):

1. ✅ **Fix Unicode issues** (DONE)
2. **Implement 9-tier industry scoring** (2-3 hours)
   - Highest impact: Legal firms go from 15pts → 30pts
3. **Add basic website age detection** (4-5 hours)
   - Just WHOIS, skip archive.org for now
4. **Implement redesign probability scoring** (2-3 hours)
   - Use website age + DIY detection + old copyright
5. **Test with sample data** (1 hour)

**Total: 9-12 hours for Minimum Viable V3**

---

## Testing Plan

### Test Data Needed
Create test cases representing all 9 tiers:
1. Law firm (Tier 1) - 4 years old, outdated website → expect HIGH score
2. Cafe (Tier 9) - 6 months old, no website → expect LOW score
3. Real estate (Tier 2) - 5 years old, Wix site → expect HIGH score
4. E-commerce (Tier 4) - 2 years old, modern site → expect MEDIUM score

### Success Criteria
- Law firm (Tier 1, 4 years old, bad site) scores 80-90 points
- Cafe (Tier 9, new, no site) scores 10-20 points
- High priority leads have 10-15% conversion probability
- Medium priority leads have 5-10% conversion probability

---

## Current State Summary

**Status**: The codebase has V3 config but V2 code. Running the script works but uses V2 scoring logic.

**To Use V3 Config Now**: The config is there, but scoring methods need to be rewritten to use it.

**Recommendation**: Implement Phase 1 (Core V3 Scoring) first to see 5X conversion rate improvement as promised in V3 upgrade guide.

---

## Questions to Answer Before Implementation

1. **Do you have access to Google Business Profile API?**
   - If NO: Use Google Maps scraping (slower but free)

2. **Do you want to implement WHOIS lookup?**
   - Requires `python-whois` library
   - Alternative: Just use business age as proxy

3. **Should we keep V2 code and create V3 as separate file?**
   - Option A: Update `filter_leads_v2.py` in place (breaking change)
   - Option B: Create `filter_leads_v3.py` (both versions available)

4. **What's the priority?**
   - Speed (minimum viable V3 in 9-12 hours)
   - Completeness (full V3 in 24-35 hours)

---

**Ready to start implementation when you give the go-ahead!**
