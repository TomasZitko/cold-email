# Quick Start Guide - Test in 5 Minutes ⚡

## Step 1: Install Dependencies (2 min)

```bash
cd /home/user/cold-email
pip install -r requirements.txt
```

## Step 2: Setup SMTP (1 min)

```bash
# Copy example environment file
cp .env.example .env

# Edit with your SMTP credentials
nano .env
```

**Add your SMTP details:**
```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=info@tomaszitko.cz
SMTP_PASSWORD=your_password_here
```

## Step 3: Test with Sample Data (2 min)

```bash
# Process sample leads
python cold_email_pro.py process --input sample_leads.csv

# Check results
ls -lh data/leads/processed/

# View statistics
cat data/leads/processed/STATISTICS.txt
```

**Expected output:**
```
Total Processed: 10
Tier 1 (Premium):  2-3 leads
Tier 2 (Good):     3-4 leads
Tier 3 (Potential): 2-3 leads
Rejected:          2-3 leads
```

## Step 4: Generate Demo Websites (1 min)

```bash
# Generate demos for Tier 1 leads
python cold_email_pro.py generate-sites --input data/leads/processed/TIER1_LEADS.csv

# Check generated files
ls -lh data/generated_sites/
```

You should see:
- `index.html` - Single page for all demos
- `demos.json` - Lead data

## Step 5: Test Email Sending (DRY RUN)

```bash
# Test without actually sending
python cold_email_pro.py send \
  --input data/leads/processed/TIER3_LEADS.csv \
  --dry-run
```

**This will NOT send emails**, just show you what would happen.

---

## Next Steps

### Deploy Demo Website

**Option A: Upload to your hosting**
1. Upload `data/generated_sites/index.html` and `demos.json`
2. Access via `https://your-domain.com/demo/?lead=LEAD_ID`

**Option B: Cloudflare Pages (recommended)**
1. Create Cloudflare Pages project
2. Upload files
3. Set custom domain: `demo.tomaszitko.cz`

### Send Real Emails

```bash
# Start with Tier 3 (low-effort, warm-up)
python cold_email_pro.py send --input data/leads/processed/TIER3_LEADS.csv

# After 1 week, move to Tier 2
python cold_email_pro.py send --input data/leads/processed/TIER2_LEADS.csv

# After 2 weeks, send Tier 1 with demos
python cold_email_pro.py send \
  --input data/leads/processed/TIER1_LEADS.csv \
  --demo-url https://demo.tomaszitko.cz/
```

---

## Troubleshooting

### "ModuleNotFoundError"
```bash
pip install -r requirements.txt
```

### "SMTP authentication failed"
Check your `.env` file - make sure credentials are correct.

### "No leads in Tier 1"
Normal with sample data. With real 20k leads, you'll get ~1,000 Tier 1 leads.

---

## What the Sample Data Shows

The `sample_leads.csv` demonstrates the filtering logic:

1. **Kavárna U Tří Koček** - ✅ HIGH SCORE (new cafe, no website, has contact)
2. **Restaurant Mario** - ✅ HIGH SCORE (old website, established business)
3. **Salon Bella** - ✅ GOOD SCORE (new salon, no website)
4. **Hotel Paradise** - ⚠️ MEDIUM SCORE (large company, 45 employees)
5. **Fitness Studio Max** - ✅ GOOD SCORE (recent, no website)
6. **Bistro Corner** - ✅ GOOD SCORE (old website, good size)
7. **Café Relax** - ⚠️ MEDIUM SCORE (has website, no contact)
8. **Advokátní kancelář** - ✅ MEDIUM SCORE (professional services)
9. **Ministerstvo financí** - ❌ REJECTED (government entity)
10. **Malý Salon** - ⚠️ LOW SCORE (too small, only 2 employees)

---

## Ready for Production?

1. ✅ Test with sample data
2. ✅ Configure SMTP
3. ✅ Test dry-run
4. ✅ Deploy demo website
5. ✅ Process your real 20k leads
6. ✅ Start sending (follow warm-up!)

**Questions? Check README.md for full documentation.**
