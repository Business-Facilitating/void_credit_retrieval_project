# UPS Web Login - Quick Reference

## ⚡ Installation

```bash
poetry add playwright
poetry run playwright install chromium
```

## 🔐 Configuration (.env file)

```env
UPS_WEB_USERNAME=spinlgx
UPS_WEB_PASSWORD=PdeqbzsZm$3&&n
```

## 🚀 Run Commands

```bash
# Run automation (headless)
poetry run python src/src/ups_web_login.py

# Test with visible browser
poetry run python tests/test_ups_web_login.py --headed

# Test prerequisites only
poetry run python tests/test_ups_web_login.py --skip-login
```

## 💻 Code Examples

### Basic Usage
```python
from src.src.ups_web_login import UPSWebLoginAutomation

with UPSWebLoginAutomation(headless=True) as ups_login:
    result = ups_login.login(save_screenshots=True)
    if result['success']:
        print("✅ Success!")
```

### Custom Config
```python
with UPSWebLoginAutomation(
    username="custom_user",
    password="custom_pass",
    headless=False
) as ups_login:
    result = ups_login.login()
```

### Extend After Login
```python
with UPSWebLoginAutomation() as ups_login:
    result = ups_login.login()
    if result['success']:
        # Access page object
        page = ups_login.page
        page.goto('https://www.ups.com/tracking')
        # More automation...
```

## 📊 Return Value

```python
{
    'success': bool,      # Login succeeded?
    'message': str,       # Result description
    'url': str,          # Final URL
    'screenshot': str    # Screenshot path
}
```

## 🐛 Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError: playwright` | `poetry add playwright` |
| `Executable doesn't exist` | `poetry run playwright install chromium` |
| `UPS_WEB_USERNAME required` | Add to `.env` file |
| Login fails | Run with `--headed` to debug |

## 📁 File Locations

- **Main Module**: `src/src/ups_web_login.py`
- **Tests**: `tests/test_ups_web_login.py`
- **Screenshots**: `data/output/`
- **Config**: `.env` (root directory)

## 📖 Documentation

- [Complete Guide](README_UPS_Web_Login.md)
- [Quick Start](UPS_WEB_LOGIN_QUICKSTART.md)
- [Implementation](UPS_WEB_LOGIN_IMPLEMENTATION.md)

## 🔒 Security Checklist

- ✅ Credentials in `.env` (not in code)
- ✅ `.env` in `.gitignore`
- ✅ `data/output/` in `.gitignore`
- ✅ Never commit `.env` file

## 🎯 Quick Test

```bash
# 1. Install
poetry add playwright
poetry run playwright install chromium

# 2. Configure .env
echo "UPS_WEB_USERNAME=spinlgx" >> .env
echo "UPS_WEB_PASSWORD=PdeqbzsZm\$3&&n" >> .env

# 3. Test
poetry run python tests/test_ups_web_login.py --headed
```

## 💡 Tips

- Use `headless=False` for debugging
- Check screenshots in `data/output/`
- Use `--headed` flag in tests to see browser
- Screenshots saved automatically on errors
- Context manager handles cleanup automatically

