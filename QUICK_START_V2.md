# 🚀 Quick Start Guide - Lead Filter V2

## Installation (First Time Only)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Verify installation
python -c "from selenium import webdriver; print('✅ Selenium OK')"
python -c "import yaml; print('✅ PyYAML OK')"
python -c "import tqdm; print('✅ tqdm OK')"
```

## Running the Filter

### Method 1: Interactive Menu (Recommended)

```bash
python main.py
```

Then select:
- **Option 2** - Filter Leads V2 (CSV-based, advanced scoring)

When prompted, enter your CSV file path or press Enter to use the sample file.

### Method 2: Direct Command Line

```bash
# With default config
python bots/filter_leads_v2.py data/your_leads.csv

# With custom config
python bots/filter_leads_v2.py data/your_leads.csv --config custom_config.yaml
```

### Method 3: Test with Sample Data

```bash
# Run with included sample data
python bots/filter_leads_v2.py data/sample_input.csv
```

## Expected Output

After processing, check the `data/` folder:

```
data/
├── HIGH_PRIORITY_LEADS.csv      ← Start here! (Score 70-100)
├── MEDIUM_PRIORITY_LEADS.csv    ← Follow-up (Score 40-69)
├── LOW_PRIORITY_LEADS.csv       ← Low priority (Score 0-39)
├── REJECTED_LEADS.csv           ← Auto-rejected with reasons
└── STATISTICS_REPORT.txt        ← Full analytics report
```

## CSV Input Format

Your CSV file needs these columns (any order):

```csv
company_name,email,phone,website,address,industry,registration_date,employees
"Kavárna Coffee","info@coffee.cz","+420 777 123 456","","Praha 1","kavárna","2024-03-15",5
"Old Restaurant","tony@pizza.cz","+420 555 444 333","oldsite.com","Brno","restaurace","2010-05-20",15
```

See [`data/sample_input.csv`](data/sample_input.csv) for a complete example.

## Understanding the Scores

### GOLDEN LEADS (70-100 points)
- **NEW businesses (0-12 months) + NO website + Customer-facing**
  - Example: New cafe opened 3 months ago, active on Instagram, no website
  - Score: 25 (age) + 20 (industry) + 10 (social) + 5 (size) = **60-80 pts**

- **Established businesses + OLD/BAD website + Customer-facing**
  - Example: 10-year restaurant with outdated 2010 website, no mobile, no SSL
  - Score: 15 (age) + 40 (bad website) + 20 (industry) + 5 (size) = **80 pts**

### GOOD LEADS (40-69 points)
- NEW businesses with old websites
- Mid-age businesses (1-5 years) with no website
- Professional services with outdated websites

### LOW PRIORITY (0-39 points)
- Businesses with modern websites (they don't need help)
- Very old businesses with no website (don't want one)
- B2B-only industries

### AUTO-REJECTED
- Government entities (úřad, ministerstvo, etc.)
- Holding companies
- Pure B2B (velkoobchod, výroba, sklad)
- No contact info

## Quick Customization

Edit `config.yaml` to adjust:

```yaml
# Change scoring thresholds
scoring:
  high_priority_min: 70    # Lower to 60 for more HIGH leads

# Add your industry keywords
industry:
  customer_facing:
    keywords:
      - your_keyword_here

# Speed up processing
performance:
  threading:
    max_workers: 100       # Increase from 50
```

## Troubleshooting

### "File not found"
```bash
# Make sure you're in the project directory
cd c:\Users\tomas_48vauln\Documents\Projects\bots\cold-email
```

### "Module not found"
```bash
pip install -r requirements.txt --upgrade
```

### "Selenium error"
```bash
pip install selenium webdriver-manager --upgrade
```

### "Processing is slow"
Disable AI analysis in `config.yaml`:
```yaml
ai:
  screenshot:
    enabled: false    # Much faster, but less accurate
```

## Next Steps

1. **Test with sample data:**
   ```bash
   python bots/filter_leads_v2.py data/sample_input.csv
   ```

2. **Review output:**
   - Open `data/HIGH_PRIORITY_LEADS.csv`
   - Read `data/STATISTICS_REPORT.txt`

3. **Customize config:**
   - Add your industry keywords to `config.yaml`
   - Adjust scoring thresholds

4. **Process your real data:**
   ```bash
   python bots/filter_leads_v2.py data/your_real_leads.csv
   ```

5. **Generate emails for HIGH priority leads:**
   ```bash
   python main.py
   # Select option 3 (Generate Emails)
   ```

## Performance Tips

**For 100k+ leads:**

1. Disable AI analysis:
   ```yaml
   ai:
     screenshot:
       enabled: false
   ```

2. Increase workers:
   ```yaml
   performance:
     threading:
       max_workers: 100
   ```

3. Enable caching:
   ```yaml
   performance:
     cache:
       enabled: true
   ```

4. Run on a powerful machine (multi-core CPU recommended)

Expected speed: **~300-500 leads/minute** (without AI)

## 🎯 Ready to Use!

You're all set! The system will:
- ✅ Clean and deduplicate your data
- ✅ Analyze websites for quality issues
- ✅ Detect social media presence
- ✅ Score each lead 0-100
- ✅ Auto-reject bad leads
- ✅ Generate 4 prioritized CSV files
- ✅ Create a statistics report

**Start with the sample data to see it in action!**

```bash
python bots/filter_leads_v2.py data/sample_input.csv
```

For full documentation, see [README_V2.md](README_V2.md)
