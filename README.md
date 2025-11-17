# 🚀 Professional Sales Automation System

A complete cold email system that acts like a professional salesman - using proven sales frameworks, smart spam avoidance, and response tracking.

---

## ⚡ Quick Start

### **1. Clone Repository**

```bash
git clone https://github.com/TomasZitko/cold-email.git
cd cold-email
git checkout claude/sales-outreach-automation-01LfnikqhS4pCVFfwpk7G1yd
```

### **2. Run Automated Setup**

**Linux / macOS:**
```bash
./setup.sh
```

**Windows:**
```batch
setup.bat
```

This automatically:
- ✅ Creates virtual environment
- ✅ Installs all dependencies
- ✅ Sets up data directory
- ✅ Creates .env file

### **3. Configure Credentials**

Edit `.env` file with your API keys:

```bash
nano .env  # or notepad .env on Windows
```

**Required:**
```env
OPENAI_API_KEY=sk-your-actual-key
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=your-app-password
IMAP_USER=your.email@gmail.com
IMAP_PASSWORD=your-app-password
SENDER_NAME=Your Name
SENDER_COMPANY=Your Company
```

### **4. Run the System**

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Run
python main.py
```

---

## 📂 Project Structure

```
cold-email/
├── bots/                    # Bot Python scripts
│   ├── filter_leads_v2.py  # Lead filtering (0-100 scoring)
│   ├── generate_emails.py  # Email generation with AI
│   ├── send_emails.py      # Spam-safe email sending
│   └── analyze_responses.py # Response tracking
├── data/                    # Data files
│   └── email-templates.txt # 20+ proven templates
├── main.py                  # Main entry point
├── setup.sh                 # Linux/macOS setup
├── setup.bat                # Windows setup
├── .env.example             # Configuration template
├── requirements.txt         # Dependencies
├── config.yaml              # Lead filtering config
├── README_PROFESSIONAL_SALESMAN.md  # Full docs
└── SETUP_GUIDE.md           # Detailed setup guide
```

---

## 🎯 Features

- ✅ **Smart Lead Filtering** - 0-100 scoring system
- ✅ **20+ Sales Templates** - PAS, AIDA, Before-After-Bridge frameworks
- ✅ **AI Email Generation** - GPT-4 personalization
- ✅ **Spam Avoidance** - Randomized timing, rate limiting, warm-up mode
- ✅ **Response Tracking** - Auto-classify positive/negative/question
- ✅ **Analytics** - Conversion rates, response tracking, reports

---

## 📖 Documentation

- **[README_PROFESSIONAL_SALESMAN.md](README_PROFESSIONAL_SALESMAN.md)** - Complete system documentation
- **[SETUP_GUIDE.md](SETUP_GUIDE.md)** - Virtual environment setup guide
- **[QUICK_START_V2.md](QUICK_START_V2.md)** - Quick start guide
- **[README_V2.md](README_V2.md)** - Lead filtering documentation

---

## 🔧 Requirements

- Python 3.8+
- OpenAI API key
- SMTP email account (Gmail recommended)
- IMAP access for response tracking

---

## 💡 Typical Workflow

```bash
# 1. Filter leads (sorts into HIGH/MEDIUM/LOW/REJECTED)
python main.py  # Option 2

# 2. Generate personalized emails
python main.py  # Option 3

# 3. Send emails (spam-safe)
python main.py  # Option 4

# 4. Track responses
python main.py  # Option 5

# OR: Run everything
python main.py  # Option 6
```

---

## 🆘 Support

- **Full Documentation:** [README_PROFESSIONAL_SALESMAN.md](README_PROFESSIONAL_SALESMAN.md)
- **Setup Issues:** [SETUP_GUIDE.md](SETUP_GUIDE.md)
- **GitHub Issues:** [Report a bug](https://github.com/TomasZitko/cold-email/issues)

---

## ⚖️ License

This project is for legitimate business outreach only. You are responsible for compliance with CAN-SPAM Act, GDPR, and local regulations.

---

**Ready to close more deals? Clone and run setup! 🔥**
