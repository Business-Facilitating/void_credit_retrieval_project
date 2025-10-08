# UPS Web Login - Quick Start Guide

Get started with UPS web automation in 5 minutes!

## ⚡ Quick Setup (5 Steps)

### Step 1: Install Playwright

```bash
poetry add playwright
```

### Step 2: Install Browser

```bash
poetry run playwright install chromium
```

### Step 3: Add Credentials to .env

Open your `.env` file and add:

```env
# UPS Web Login Configuration
UPS_WEB_LOGIN_URL=https://www.ups.com/lasso/login
UPS_WEB_USERNAME=spinlgx
UPS_WEB_PASSWORD=PdeqbzsZm$3&&n
```

**⚠️ Security Note**: These credentials are for testing. Never commit your `.env` file!

### Step 4: Test the Setup

```bash
poetry run python tests/test_ups_web_login.py --skip-login
```

This will verify:
- ✅ Environment variables are set
- ✅ Playwright is installed
- ✅ Browser is available

### Step 5: Run the Login Automation

**Option A: Headless mode (no visible browser)**
```bash
poetry run python src/src/ups_web_login.py
```

**Option B: Headed mode (see the browser)**
```bash
poetry run python tests/test_ups_web_login.py --headed
```

## 🎯 What Happens?

The automation will:
1. 🌐 Open the UPS login page
2. 📝 Fill in your username and password
3. 🖱️ Click the submit button
4. ✅ Verify successful login
5. 📸 Save screenshots to `data/output/`

## 📊 Expected Output

```
🚀 UPS Web Login Automation
============================================================
🚀 UPS Web Login Automation initialized
   Username: spinlgx...
   Headless mode: True
   Output directory: data/output
🌐 Starting browser...
✅ Browser started successfully
🔐 Starting UPS login process...
🌐 Navigating to: https://www.ups.com/lasso/login
⏳ Waiting for login form...
✅ Found username field: input[name="username"]
✅ Found password field: input[name="password"]
📝 Entering credentials...
   Username entered: spinlgx...
   Password entered: ********
📸 Screenshot saved: data/output/02_credentials_entered_20250101_120000.png
✅ Found submit button: button[type="submit"]
🖱️ Clicking submit button...
⏳ Waiting for login response...
📸 Screenshot saved: data/output/03_after_submit_20250101_120001.png
✅ Login successful! Current URL: https://www.ups.com/myups/...
🔒 Browser closed successfully

============================================================
📊 LOGIN RESULT
============================================================
Success: ✅ YES
Message: Login successful
Final URL: https://www.ups.com/myups/dashboard
Screenshot: data/output/03_after_submit_20250101_120001.png
```

## 🐛 Troubleshooting

### Error: "Playwright not installed"

```bash
poetry add playwright
poetry run playwright install chromium
```

### Error: "UPS_WEB_USERNAME environment variable is required"

1. Make sure `.env` file exists in project root
2. Add the credentials:
   ```env
   UPS_WEB_USERNAME=spinlgx
   UPS_WEB_PASSWORD=PdeqbzsZm$3&&n
   ```

### Error: "Executable doesn't exist"

```bash
poetry run playwright install chromium
```

### Login fails but no error

1. Run in headed mode to see what's happening:
   ```bash
   poetry run python tests/test_ups_web_login.py --headed
   ```
2. Check screenshots in `data/output/`
3. Verify credentials are correct

## 🔄 Next Steps

After successful login, you can:

1. **Extend the automation** - Add more actions after login
2. **Extract data** - Scrape tracking information
3. **Automate workflows** - Create end-to-end automation
4. **Schedule tasks** - Run automation on a schedule

See [README_UPS_Web_Login.md](README_UPS_Web_Login.md) for advanced usage.

## 📝 Code Example

```python
from src.src.ups_web_login import UPSWebLoginAutomation

# Simple usage
with UPSWebLoginAutomation(headless=True) as ups_login:
    result = ups_login.login(save_screenshots=True)
    
    if result['success']:
        print("✅ Logged in successfully!")
        # Do more automation here...
    else:
        print(f"❌ Login failed: {result['message']}")
```

## 🔒 Security Reminders

- ✅ Credentials are in `.env` (gitignored)
- ✅ Never commit `.env` file
- ✅ Screenshots may contain sensitive data
- ✅ `data/output/` is gitignored

## 📞 Need Help?

1. Check [README_UPS_Web_Login.md](README_UPS_Web_Login.md) for detailed docs
2. Review test output and screenshots
3. Run tests with `--headed` flag to see browser

