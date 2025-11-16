# Cold Email Pro - Production-Ready Outreach System 🚀

**A professional, production-ready cold email system for web design agencies.**

Built for **real results**: Filter 20,000+ leads, generate personalized demos, and send emails that actually get replies - without getting blacklisted.

---

## 🎯 What This System Does

### 1. **Intelligent Lead Filtering** 📊
- Process CSV/XLSX files with thousands of leads
- Smart niche detection (restaurant, hotel, cafe, salon, etc.)
- Multi-factor scoring (0-100)
- Automatic tier classification (Tier 1/2/3 or reject)
- Filters out government entities, large corps, and bad data

### 2. **Dynamic Website Generation** 🌐
- **ONE index.html** handles all demos (no file explosion!)
- Personalized for each lead via URL parameters
- Responsive, modern templates
- Niche-specific color schemes
- Ready to deploy on Cloudflare Pages, GitHub Pages, or any hosting

### 3. **Smart Email Orchestration** 📧
- **Tiered sending strategy**:
  - Tier 1: Personalized demo + high-touch
  - Tier 2: Mockup + portfolio
  - Tier 3: Portfolio only
- **Warm-up schedule** (20/day → 200/day over weeks)
- **Rate limiting** to avoid spam filters
- **GDPR-compliant** unsubscribe system
- Bounce and spam complaint handling

### 4. **Production-Ready Features** ✅
- Multi-threaded processing
- Caching system (7-day TTL)
- Resume capability
- Comprehensive logging
- Error handling
- Statistics and reporting

---

## 🏗️ Architecture

```
cold-email/
├── src/
│   ├── core/
│   │   ├── lead_processor.py        # Lead filtering + niche detection
│   │   ├── website_generator.py     # Dynamic demo generation
│   │   ├── email_orchestrator.py    # Smart sending + warm-up
│   │   └── compliance.py            # GDPR + unsubscribe
│   ├── utils/
│   │   ├── logger.py                # Centralized logging
│   │   ├── validators.py            # Email/URL/phone validation
│   │   └── helpers.py               # Common utilities
│   ├── templates/                   # Website templates (HTML)
│   └── email_templates/             # Email templates (TXT)
├── config/
│   └── production.yaml              # Main configuration
├── data/
│   ├── leads/                       # Input and processed leads
│   ├── generated_sites/             # Demo websites
│   ├── emails/                      # Email queue and logs
│   └── compliance/                  # Unsubscribe/bounce lists
├── logs/                            # System logs
├── cold_email_pro.py                # Main CLI interface
├── requirements.txt                 # Dependencies
└── .env                             # Environment variables (SMTP, etc.)
```

---

## 🚀 Quick Start

### 1. Installation

```bash
# Clone/navigate to the repository
cd cold-email

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env with your SMTP credentials
nano .env
```

### 2. Configure SMTP Settings

Edit `.env`:

```env
SMTP_HOST=smtp.your-provider.com
SMTP_PORT=587
SMTP_USER=info@tomaszitko.cz
SMTP_PASSWORD=your_password_here
```

**Recommended SMTP Providers:**
- **SendGrid**: $15/month (40k emails, great deliverability)
- **Mailgun**: Pay-as-you-go
- **Amazon SES**: Cheapest, but harder setup
- **Your domain's SMTP**: Free, but start with warm-up!

### 3. Prepare Your Leads File

Create a CSV/XLSX file with these columns:

| Column | Required | Description |
|--------|----------|-------------|
| `company_name` | ✅ Yes | Company name |
| `email` | No | Email address |
| `phone` | No | Phone number |
| `website` | No | Website URL |
| `industry` | No | Industry/category |
| `address` | No | Full address |
| `registration_date` | No | Company founded date |
| `employees` | No | Number of employees |

**Example:**

```csv
company_name,email,phone,website,industry,address,employees
Kavárna U Tří Koček,info@utrikocek.cz,+420 777 123 456,,kavárna,"Hlavní 25, Praha",5
Restaurant Mario,mario@restaurant.cz,+420 555 444 333,mario-restaurant.cz,restaurace,,12
```

### 4. Process Leads

```bash
# Process your leads file
python cold_email_pro.py process --input your_leads.csv
```

This will create:
- `data/leads/processed/TIER1_LEADS.csv` - Top 5% (score 85+)
- `data/leads/processed/TIER2_LEADS.csv` - Top 20% (score 70-84)
- `data/leads/processed/TIER3_LEADS.csv` - Potential (score 60-69)
- `data/leads/processed/REJECTED_LEADS.csv` - Auto-rejected
- `data/leads/processed/STATISTICS.txt` - Detailed report

### 5. Generate Demo Websites (Optional - for Tier 1 leads)

```bash
# Generate demos for your best leads
python cold_email_pro.py generate-sites --input data/leads/processed/TIER1_LEADS.csv
```

This creates:
- `data/generated_sites/index.html` - Single HTML file for all demos
- `data/generated_sites/demos.json` - Lead data

**Deploy to Cloudflare Pages** (recommended):

1. Create a Cloudflare Pages project
2. Upload `index.html` and `demos.json`
3. Set custom domain (e.g., `demo.tomaszitko.cz`)
4. Test: `https://demo.tomaszitko.cz/?lead=abc123`

**Alternative**: Upload to GitHub Pages, Netlify, or any static host.

### 6. Send Emails

**IMPORTANT: Start with Tier 3 (low-effort) to warm up your domain!**

```bash
# DRY RUN FIRST (test without sending)
python cold_email_pro.py send --input data/leads/processed/TIER3_LEADS.csv --dry-run

# Production send (portfolio only, no demos)
python cold_email_pro.py send --input data/leads/processed/TIER3_LEADS.csv

# For Tier 1 (with personalized demos)
python cold_email_pro.py send \
  --input data/leads/processed/TIER1_LEADS.csv \
  --demo-url https://demo.tomaszitko.cz/
```

The system will:
1. Check daily warm-up limits
2. Filter out unsubscribed/bounced emails
3. Apply tier-specific daily limits
4. Rate limit to avoid spam triggers
5. Log all sent emails

### 7. Monitor Progress

```bash
# View statistics
python cold_email_pro.py stats
```

---

## 📋 Warm-Up Schedule

**CRITICAL**: Never send too many emails at once! This system enforces warm-up:

| Days Active | Emails/Day | Purpose |
|-------------|------------|---------|
| Day 1-7 | 20 | Establish sender reputation |
| Day 8-14 | 50 | Gradual increase |
| Day 15-21 | 100 | Moderate volume |
| Day 22+ | 200 | Full capacity |

**Tier-specific limits** (additional):
- **Tier 1** (personalized): 10/day (high effort)
- **Tier 2** (mockup): 30/day
- **Tier 3** (portfolio): 60/day

---

## 🎨 Customization

### Edit Email Templates

Templates are in `src/email_templates/`:
- `tier1_personalized_demo.txt` - For leads with demos
- `tier2_mockup_portfolio.txt` - For good leads
- `tier3_portfolio.txt` - For potential leads

Use Jinja2 variables:
- `{{ company_name }}` - Company name
- `{{ industry }}` - Industry
- `{{ location }}` - Extracted city/region
- `{{ demo_url }}` - Demo URL (Tier 1 only)
- `{{ your_name }}` - Your name
- `{{ your_email }}` - Your email
- `{{ unsubscribe_url }}` - Unsubscribe link

### Adjust Scoring Thresholds

Edit `config/production.yaml`:

```yaml
lead_processing:
  tiers:
    tier1_min: 85  # Top 5% - Personalized demo
    tier2_min: 70  # Top 20% - Mockup + portfolio
    tier3_min: 60  # Top 50% - Portfolio only
```

### Add Custom Niches

Edit `config/production.yaml`:

```yaml
niches:
  detection:
    yoga_studio:
      keywords: [yoga, jóga, studio, wellness]
      template: fitness
      priority_multiplier: 1.1
```

---

## 📊 Understanding the Scoring System

Leads are scored 0-100 based on:

### 1. Business Health (35 points)
- Employee count (3-20 = sweet spot)
- Has valid contact info
- Has physical address

### 2. Redesign Opportunity (30 points)
- **No website**: 30 points (GOLDEN)
- **Has website**: 15 points (opportunity for redesign)

### 3. Industry Fit (25 points)
- **High-value**: Restaurant, hotel, cafe, salon (25 pts)
- **Medium-value**: Fitness, retail, professional (18 pts)
- **Default**: Other industries (10 pts)

### 4. Timing Signals (10 points)
- New business (<2 years): 10 points
- Established business (2-5 years): 5 points

**Niche multipliers** are then applied (e.g., restaurants × 1.2).

---

## 🛡️ Compliance & GDPR

### Unsubscribe Handling

Every email includes an unsubscribe link. The system automatically:
- Tracks unsubscribe requests
- Blocks future emails to unsubscribed addresses
- Exports data for GDPR compliance

### Bounce Management

Automatically tracks:
- Hard bounces (invalid email)
- Soft bounces (temporary failure)
- Spam complaints

After 2 bounces, email is automatically blacklisted.

### Data Export (GDPR)

```bash
# Export all compliance data
python cold_email_pro.py export-compliance
```

---

## 🔥 Real-World Usage Examples

### Example 1: First Campaign (20k Leads)

```bash
# Step 1: Process leads
python cold_email_pro.py process --input raw_leads_20k.csv

# Results:
# - Tier 1: 1,000 leads (5%)
# - Tier 2: 3,000 leads (15%)
# - Tier 3: 6,000 leads (30%)
# - Rejected: 10,000 leads (50%)

# Step 2: Generate demos for Tier 1
python cold_email_pro.py generate-sites --input data/leads/processed/TIER1_LEADS.csv

# Step 3: Upload to Cloudflare Pages
# (Upload index.html + demos.json)

# Step 4: Start with Tier 3 (warm-up)
python cold_email_pro.py send --input data/leads/processed/TIER3_LEADS.csv

# Day 1-7: 20 emails/day from Tier 3
# Day 8-14: 50 emails/day from Tier 3 + Tier 2
# Day 15+: Start Tier 1 with demos
```

### Example 2: Weekly Maintenance

```bash
# Monday: Process new leads
python cold_email_pro.py process --input weekly_leads.csv

# Tuesday-Friday: Send emails
python cold_email_pro.py send --input data/leads/processed/TIER2_LEADS.csv

# Friday: Check stats
python cold_email_pro.py stats
```

---

## 🐛 Troubleshooting

### "SMTP authentication failed"

Check `.env` file:
- Correct SMTP host
- Correct username
- Correct password
- Correct port (587 for TLS, 465 for SSL)

### "Daily limit reached"

Normal! The system enforces warm-up. Wait until tomorrow or adjust limits in `config/production.yaml`:

```yaml
email:
  sending:
    warmup:
      enabled: false  # Disable warm-up (NOT recommended)
```

### "Emails going to spam"

Common causes:
1. **Not warmed up**: Follow the warm-up schedule
2. **No SPF/DKIM**: Configure DNS records for your sending domain
3. **Generic content**: Personalize more (use Tier 1 strategy)
4. **High volume too fast**: Slow down

### "No leads in Tier 1"

Your leads might not score high enough. Lower the threshold:

```yaml
lead_processing:
  tiers:
    tier1_min: 75  # Lower from 85
```

---

## 📈 Expected Results

Based on typical web design cold email campaigns:

| Tier | Leads | Open Rate | Reply Rate | Conversion |
|------|-------|-----------|------------|------------|
| Tier 1 (Demo) | 1,000 | 40-50% | 5-10% | 1-2% |
| Tier 2 (Mockup) | 3,000 | 30-40% | 2-5% | 0.5-1% |
| Tier 3 (Portfolio) | 6,000 | 20-30% | 1-2% | 0.1-0.3% |

**To get 10 clients from 20k leads:**
- Tier 1: ~10-20 clients (1-2%)
- Tier 2: ~15-30 clients (0.5-1%)
- Tier 3: ~6-18 clients (0.1-0.3%)

**Total expected: 31-68 clients** (with proper execution)

---

## 🚨 Important Notes

### DO:
✅ Start with Tier 3 to warm up
✅ Follow the warm-up schedule
✅ Personalize email templates
✅ Test with --dry-run first
✅ Monitor spam complaints
✅ Reply to interested leads FAST

### DON'T:
❌ Send 1000 emails on day 1 (blacklist)
❌ Use generic templates (spam folder)
❌ Ignore unsubscribes (legal issues)
❌ Skip SPF/DKIM setup (deliverability)
❌ Email the same lead twice (annoying)

---

## 🔧 Advanced Configuration

### Custom Rate Limiting

```yaml
email:
  sending:
    rate_limit:
      emails_per_hour: 20  # Lower for more caution
      delay_between_emails_seconds: 180  # 3 minutes
      randomize_delay: true
```

### Disable Caching

```yaml
performance:
  cache:
    enabled: false
```

### Increase Processing Speed

```yaml
performance:
  threading:
    max_workers: 50  # Increase for faster processing
```

---

## 📞 Support & Questions

For issues or questions:
1. Check this README
2. Review `logs/system.log` for errors
3. Check `config/production.yaml` for settings
4. Review `data/leads/processed/STATISTICS.txt` for insights

---

## 📝 License

Internal tool for web design agencies. Use responsibly and comply with local email marketing laws (GDPR, CAN-SPAM, etc.).

---

## 🙏 Credits

Built by **Tomáš Žitko** for professional cold email outreach.

**Tech stack:**
- Python 3.8+
- pandas (data processing)
- Jinja2 (templating)
- PyYAML (configuration)
- Beautiful single-page website architecture

---

## 🎯 Final Tips for Success

1. **Quality > Quantity**: 1,000 perfect leads > 20,000 garbage leads
2. **Personalization matters**: Tier 1 with demos gets 10x better results
3. **Warm up properly**: Don't rush, it takes 3-4 weeks to scale
4. **Reply fast**: When someone replies, respond within hours
5. **A/B test**: Try different email templates and track results
6. **Clean your list**: Remove bounces and unsubscribes regularly
7. **Follow up**: Send 2-3 follow-ups to non-responders (1 week apart)

**Good luck landing those 10 clients!** 🚀
