# UPS Web Login Automation

Automated login functionality for the UPS website using Playwright browser automation.

## 📋 Overview

This module provides secure, automated login to the UPS website (https://www.ups.com). It uses Playwright for browser automation, offering a robust and modern approach to web interaction.

## 🔐 Security Features

- **Environment Variable Storage**: Credentials stored securely in `.env` file
- **No Hardcoded Credentials**: All sensitive data loaded from environment
- **Git Protection**: `.env` file automatically excluded from version control
- **Screenshot Privacy**: Screenshots saved to `data/output/` (excluded from git)

## 🚀 Quick Start

### 1. Install Playwright

Add Playwright to the project dependencies:

```bash
poetry add playwright
```

Install the Chromium browser:

```bash
poetry run playwright install chromium
```

### 2. Configure Credentials

Add your UPS web login credentials to your `.env` file:

```env
# UPS Web Login Configuration
UPS_WEB_LOGIN_URL=https://www.ups.com/lasso/login
UPS_WEB_USERNAME=your_ups_username
UPS_WEB_PASSWORD=your_ups_password
```

**⚠️ Important**: 
- These are your UPS.com website credentials (not API credentials)
- Never commit your `.env` file to version control
- The `.env` file is already in `.gitignore`

### 3. Run the Login Automation

**Headless mode (no visible browser):**
```bash
poetry run python src/src/ups_web_login.py
```

**Headed mode (visible browser for debugging):**
```bash
# Modify the script to set headless=False in the main() function
# Or use the test script with --headed flag
poetry run python tests/test_ups_web_login.py --headed
```

## 🧪 Testing

### Run All Tests

```bash
poetry run python tests/test_ups_web_login.py
```

### Test Options

```bash
# Run with visible browser
poetry run python tests/test_ups_web_login.py --headed

# Skip actual login (only test environment and installation)
poetry run python tests/test_ups_web_login.py --skip-login
```

### Test Coverage

The test suite validates:
1. ✅ Environment variables are properly configured
2. ✅ Playwright is installed and browsers are available
3. ✅ Login automation executes successfully
4. ✅ Screenshots are captured correctly
5. ✅ Error handling works as expected

## 📖 Usage Examples

### Basic Usage

```python
from src.src.ups_web_login import UPSWebLoginAutomation

# Use context manager for automatic cleanup
with UPSWebLoginAutomation(headless=True) as ups_login:
    result = ups_login.login(save_screenshots=True)
    
    if result['success']:
        print(f"✅ Login successful!")
        print(f"Current URL: {result['url']}")
    else:
        print(f"❌ Login failed: {result['message']}")
```

### Custom Configuration

```python
from src.src.ups_web_login import UPSWebLoginAutomation

# Custom credentials and settings
with UPSWebLoginAutomation(
    username="custom_username",
    password="custom_password",
    headless=False,  # Show browser
    output_dir="custom/output/path"
) as ups_login:
    result = ups_login.login(save_screenshots=True)
```

### Manual Browser Control

```python
from src.src.ups_web_login import UPSWebLoginAutomation

# Initialize without context manager for manual control
ups_login = UPSWebLoginAutomation(headless=False)

try:
    ups_login.start_browser()
    result = ups_login.login(save_screenshots=True)
    
    # Do additional automation after login
    if result['success']:
        # Access the page object for further automation
        page = ups_login.page
        # ... perform additional actions ...
        
finally:
    ups_login.close_browser()
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `UPS_WEB_USERNAME` | ✅ Yes | - | UPS website username |
| `UPS_WEB_PASSWORD` | ✅ Yes | - | UPS website password |
| `UPS_WEB_LOGIN_URL` | No | `https://www.ups.com/lasso/login` | UPS login page URL |
| `OUTPUT_DIR` | No | `data/output` | Directory for screenshots |

### Browser Settings

The automation uses the following browser configuration:
- **Browser**: Chromium (Chrome-based)
- **Viewport**: 1920x1080
- **User Agent**: Modern Chrome on Windows
- **Locale**: en-US
- **Timezone**: America/New_York
- **Default Timeout**: 30 seconds
- **Navigation Timeout**: 60 seconds

## 📊 Return Values

The `login()` method returns a dictionary with:

```python
{
    'success': bool,        # True if login succeeded
    'message': str,         # Description of result
    'url': str,            # Final URL after login attempt
    'screenshot': str      # Path to screenshot (if saved)
}
```

## 🐛 Troubleshooting

### Playwright Not Installed

**Error**: `ModuleNotFoundError: No module named 'playwright'`

**Solution**:
```bash
poetry add playwright
poetry run playwright install chromium
```

### Missing Environment Variables

**Error**: `ValueError: UPS_WEB_USERNAME environment variable is required`

**Solution**:
1. Ensure `.env` file exists in project root
2. Add the required credentials:
   ```env
   UPS_WEB_USERNAME=your_username
   UPS_WEB_PASSWORD=your_password
   ```

### Browser Not Found

**Error**: `Executable doesn't exist at ...`

**Solution**:
```bash
poetry run playwright install chromium
```

### Login Fails

**Possible causes**:
1. **Incorrect credentials**: Verify username/password in `.env`
2. **Page structure changed**: UPS may have updated their login page
3. **CAPTCHA or 2FA**: UPS may require additional verification
4. **Network issues**: Check internet connection

**Debugging steps**:
1. Run in headed mode to see what's happening:
   ```bash
   poetry run python tests/test_ups_web_login.py --headed
   ```
2. Check screenshots in `data/output/` directory
3. Review error messages in console output

### Timeout Errors

**Error**: `TimeoutError: Timeout 30000ms exceeded`

**Solution**:
- Slow internet connection: Increase timeout in code
- Page loading issues: Check UPS website status
- Selector issues: Page structure may have changed

## 🔒 Security Best Practices

1. **Never commit credentials**
   - Always use `.env` file for credentials
   - Verify `.env` is in `.gitignore`
   - Never hardcode credentials in scripts

2. **Protect screenshots**
   - Screenshots may contain sensitive information
   - `data/output/` is excluded from git
   - Review screenshots before sharing

3. **Secure your `.env` file**
   - Set appropriate file permissions (Unix: `chmod 600 .env`)
   - Don't share your `.env` file
   - Rotate credentials regularly

4. **Use environment-specific credentials**
   - Use different credentials for testing vs production
   - Consider using `.env.local` for local development

## 📁 File Structure

```
gsr_automation/
├── src/src/
│   └── ups_web_login.py          # Main automation module
├── tests/
│   └── test_ups_web_login.py     # Test suite
├── docs/
│   └── README_UPS_Web_Login.md   # This documentation
├── data/output/                   # Screenshots and logs (gitignored)
├── .env.example                   # Template with UPS_WEB_* variables
└── .env                          # Your actual credentials (gitignored)
```

## 🚧 Limitations

1. **CAPTCHA**: Cannot bypass CAPTCHA challenges automatically
2. **2FA**: Two-factor authentication requires manual intervention
3. **Session Management**: Sessions expire based on UPS policies
4. **Rate Limiting**: UPS may rate-limit automated logins
5. **Page Changes**: UPS website updates may break selectors

## 🔄 Next Steps

After successful login, you can extend the automation to:

1. **Navigate to specific pages**
   ```python
   if result['success']:
       ups_login.page.goto('https://www.ups.com/tracking')
   ```

2. **Extract data**
   ```python
   # Get tracking information
   tracking_data = ups_login.page.query_selector('.tracking-info').inner_text()
   ```

3. **Perform actions**
   ```python
   # Click buttons, fill forms, etc.
   ups_login.page.click('button#submit')
   ```

4. **Save session state**
   ```python
   # Save cookies for later use
   cookies = ups_login.context.cookies()
   ```

## 📞 Support

For issues or questions:
1. Check this documentation
2. Review test output and screenshots
3. Check Playwright documentation: https://playwright.dev/python/
4. Review project's main README.md for general setup

## 📝 Notes

- This automation is for legitimate business use only
- Respect UPS Terms of Service
- Use responsibly and ethically
- Consider API alternatives when available (see `ups_api.py`)

