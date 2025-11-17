# 🔧 COMPLETE SETUP GUIDE - Virtual Environment

This guide walks you through setting up a **clean, isolated Python environment** for the Professional Salesman system.

---

## 🎯 Why Use Virtual Environment?

**Benefits:**
- ✅ Isolates project dependencies from system Python
- ✅ Prevents version conflicts with other projects
- ✅ Easy to replicate on different machines
- ✅ Clean uninstall (just delete `venv` folder)
- ✅ Professional best practice

**Without venv:** Dependencies install globally, can conflict with other projects
**With venv:** Each project has its own isolated Python + dependencies

---

## 🚀 Quick Setup (Recommended)

### **Linux / macOS**

```bash
# Clone the repository
git clone https://github.com/TomasZitko/cold-email.git
cd cold-email
git checkout claude/sales-outreach-automation-01LfnikqhS4pCVFfwpk7G1yd
cd bots/cold-email

# Run automated setup
chmod +x setup.sh
./setup.sh

# Setup will:
# - Create virtual environment
# - Install all dependencies
# - Create .env file
# - Set up data directory

# Edit your credentials
nano .env

# Start using the system!
python main.py
```

### **Windows**

```batch
REM Clone the repository
git clone https://github.com/TomasZitko/cold-email.git
cd cold-email
git checkout claude/sales-outreach-automation-01LfnikqhS4pCVFfwpk7G1yd
cd bots\cold-email

REM Run automated setup
setup.bat

REM Edit your credentials
notepad .env

REM Start using the system!
python main.py
```

---

## 🔧 Manual Setup (Step by Step)

### **Step 1: Clone Repository**

```bash
git clone https://github.com/TomasZitko/cold-email.git
cd cold-email
git checkout claude/sales-outreach-automation-01LfnikqhS4pCVFfwpk7G1yd
cd bots/cold-email
```

### **Step 2: Create Virtual Environment**

**Linux / macOS:**
```bash
python3 -m venv venv
```

**Windows:**
```batch
python -m venv venv
```

This creates a `venv` folder containing isolated Python installation.

### **Step 3: Activate Virtual Environment**

**Linux / macOS:**
```bash
source venv/bin/activate
```

**Windows (Command Prompt):**
```batch
venv\Scripts\activate.bat
```

**Windows (PowerShell):**
```powershell
venv\Scripts\Activate.ps1
```

**You'll see `(venv)` prefix in terminal when active.**

### **Step 4: Upgrade pip**

```bash
pip install --upgrade pip
```

### **Step 5: Install Dependencies**

```bash
pip install -r requirements.txt
```

This installs all required packages:
- pandas (data processing)
- requests (HTTP requests)
- beautifulsoup4 (HTML parsing)
- selenium (browser automation)
- openai (GPT-4 API)
- python-dotenv (environment variables)
- notion-client (Notion integration)
- And more...

### **Step 6: Configure Environment**

```bash
# Copy template
cp .env.example .env

# Edit with your credentials
nano .env  # or vim, or any text editor
```

**Required settings:**
```env
OPENAI_API_KEY=sk-your-actual-key
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=your-app-password
IMAP_USER=your.email@gmail.com
IMAP_PASSWORD=your-app-password
SENDER_NAME=Your Name
SENDER_COMPANY=Your Company
```

### **Step 7: Verify Setup**

```bash
# Check Python is from venv
which python  # Should show: .../venv/bin/python

# Check packages installed
pip list

# Try importing key packages
python -c "import pandas, openai, requests; print('✅ All imports successful')"
```

### **Step 8: Run the System**

```bash
python main.py
```

---

## 🔄 Daily Usage

### **Activate venv (every time you work on project):**

**Linux / macOS:**
```bash
cd /path/to/cold-email/bots/cold-email
source venv/bin/activate
```

**Windows:**
```batch
cd C:\path\to\cold-email\bots\cold-email
venv\Scripts\activate
```

### **Deactivate venv (when done):**

```bash
deactivate
```

### **Check if venv is active:**

```bash
# Should show (venv) prefix
echo $PS1  # Linux/macOS

# Or check Python location
which python  # Should be inside venv folder
```

---

## 📦 Managing Dependencies

### **Add new package:**

```bash
# Activate venv first
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Install package
pip install package-name

# Update requirements.txt
pip freeze > requirements.txt
```

### **Update all packages:**

```bash
pip install --upgrade -r requirements.txt
```

### **List installed packages:**

```bash
pip list
```

---

## 🗑️ Uninstall / Clean Up

### **Remove virtual environment:**

```bash
# Deactivate first
deactivate

# Delete venv folder
rm -rf venv  # Linux/macOS
# or
rmdir /s venv  # Windows
```

### **Start fresh:**

```bash
# Remove old venv
rm -rf venv

# Create new one
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## 🐛 Troubleshooting

### **Problem: `python3: command not found`**

**Solution:**
```bash
# Try just 'python' instead
python --version

# If that works, use 'python' everywhere instead of 'python3'
python -m venv venv
```

### **Problem: `venv/bin/activate: Permission denied`**

**Solution:**
```bash
chmod +x venv/bin/activate
source venv/bin/activate
```

### **Problem: PowerShell execution policy error**

**Solution:**
```powershell
# Run as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then activate
venv\Scripts\Activate.ps1
```

### **Problem: `pip install` fails with SSL error**

**Solution:**
```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Or use --trusted-host
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org -r requirements.txt
```

### **Problem: Can't find openai/pandas after install**

**Solution:**
```bash
# Make sure venv is activated
source venv/bin/activate

# Check Python location
which python  # Should be in venv folder

# If not, recreate venv
deactivate
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **Problem: `ModuleNotFoundError` when running**

**Solution:**
```bash
# Activate venv first!
source venv/bin/activate

# Then run
python main.py
```

---

## 🎓 VS Code Integration

### **Setup VS Code to use venv:**

1. Open project in VS Code:
   ```bash
   code /path/to/cold-email/bots/cold-email
   ```

2. Open Command Palette (Ctrl+Shift+P / Cmd+Shift+P)

3. Type: "Python: Select Interpreter"

4. Choose the interpreter from `venv` folder:
   - Linux/macOS: `./venv/bin/python`
   - Windows: `.\venv\Scripts\python.exe`

5. VS Code will now use venv automatically!

---

## 📝 .gitignore (Already configured)

The `venv/` folder should NOT be committed to git:

```gitignore
# Virtual environment
venv/
env/
ENV/
```

This is already set up - you'll share `requirements.txt` instead of the actual packages.

---

## 🔒 Security Best Practices

### **Never commit sensitive files:**

```gitignore
# Already in .gitignore
.env
*.env
data/*.csv
data/*.json
data/*.txt
```

### **Use environment variables:**

```python
# Good ✅
api_key = os.getenv('OPENAI_API_KEY')

# Bad ❌
api_key = 'sk-1234567890abcdef'  # Never hardcode!
```

---

## 🚀 Deployment / Production

### **Share project with team:**

```bash
# They clone repo
git clone https://github.com/TomasZitko/cold-email.git

# They create their own venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# They create their own .env
cp .env.example .env
# Edit with their credentials
```

### **Update requirements.txt after adding packages:**

```bash
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Updated dependencies"
git push
```

---

## ✅ Verification Checklist

After setup, verify everything works:

- [ ] Virtual environment created (`venv/` folder exists)
- [ ] Venv is activated (`(venv)` shows in terminal)
- [ ] Dependencies installed (`pip list` shows pandas, openai, etc.)
- [ ] `.env` file exists with your credentials
- [ ] `data/` directory exists
- [ ] `data/email-templates.txt` exists
- [ ] Can import packages: `python -c "import pandas, openai"`
- [ ] Can run main: `python main.py`

---

## 🎯 Quick Reference

| Command | Linux/macOS | Windows |
|---------|-------------|---------|
| Create venv | `python3 -m venv venv` | `python -m venv venv` |
| Activate venv | `source venv/bin/activate` | `venv\Scripts\activate` |
| Deactivate venv | `deactivate` | `deactivate` |
| Install deps | `pip install -r requirements.txt` | `pip install -r requirements.txt` |
| Check Python | `which python` | `where python` |
| List packages | `pip list` | `pip list` |

---

**You're now ready to use the Professional Salesman system with a clean, isolated environment! 🎉**

Need help? Check the main README or open an issue on GitHub.
