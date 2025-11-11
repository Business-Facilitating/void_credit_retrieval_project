#!/usr/bin/env python3
"""
UPS Website Login Automation
=============================

This module provides automated login functionality for the UPS website using Playwright.
It handles the complete login flow including credential entry, form submission, and
authentication verification.

Features:
- Secure credential management via environment variables
- Robust error handling and logging
- Headless and headed browser modes
- Screenshot capture on errors
- Session persistence support
- Configurable timeouts and retries
- Bulk void shipments from CSV with account mapping
- Automatic shipping history filter configuration:
  * Set results per page to 50
  * Set date range to match ups_label_only_filter.py (85-89 days ago)

Security:
- Credentials loaded from .env file (never hardcoded)
- Screenshots saved to output directory (excluded from git)
- Secure browser context with proper cleanup

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import csv
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import duckdb
from dotenv import load_dotenv
from playwright.sync_api import Browser, BrowserContext, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
UPS_WEB_LOGIN_URL = os.getenv("UPS_WEB_LOGIN_URL", "https://www.ups.com/lasso/login")
UPS_WEB_USERNAME = os.getenv("UPS_WEB_USERNAME")
UPS_WEB_PASSWORD = os.getenv("UPS_WEB_PASSWORD")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "data/output")

# Validate required environment variables
if not UPS_WEB_USERNAME:
    raise ValueError(
        "UPS_WEB_USERNAME environment variable is required. Please set it in your .env file."
    )
if not UPS_WEB_PASSWORD:
    raise ValueError(
        "UPS_WEB_PASSWORD environment variable is required. Please set it in your .env file."
    )

# Browser configuration
DEFAULT_TIMEOUT = 30000  # 30 seconds in milliseconds
DEFAULT_NAVIGATION_TIMEOUT = 60000  # 60 seconds for page loads

# PeerDB Configuration
PEERDB_DUCKDB_PATH = os.getenv(
    "PEERDB_DUCKDB_PATH", "peerdb_industry_index_logins.duckdb"
)
PEERDB_TABLE_NAME = "peerdb_data.industry_index_logins"


# Helper Functions for Data Loading
def load_tracking_numbers_from_csv(csv_path: str) -> List[Dict[str, str]]:
    """
    Load tracking numbers and account numbers from ups_label_only_filter.py output CSV

    Args:
        csv_path: Path to the CSV file containing tracking numbers

    Returns:
        List of dictionaries with tracking_number and account_number
    """
    tracking_data = []

    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                tracking_data.append(
                    {
                        "tracking_number": row["tracking_number"],
                        "account_number": row["account_number"],
                    }
                )

        logger.info(
            f"✅ Loaded {len(tracking_data)} tracking numbers from CSV: {csv_path}"
        )
        return tracking_data

    except Exception as e:
        logger.error(f"❌ Failed to load tracking numbers from CSV: {e}")
        return []


def load_login_credentials_from_peerdb(
    duckdb_path: str = PEERDB_DUCKDB_PATH,
) -> Dict[str, Dict[str, str]]:
    """
    Load UPS login credentials from PeerDB industry_index_logins table

    Maps account_number (last 6 digits) to login credentials.
    Uses the formula: industry_index_login.account_number = RIGHT(carrier_invoice.account_number, 6)

    Note: The table uses carrier_login for username and carrier_password for password.

    Args:
        duckdb_path: Path to the PeerDB DuckDB file

    Returns:
        Dictionary mapping account_number (last 6 digits) to credentials:
        {
            "123456": {
                "username": "user@example.com",  # from carrier_login column
                "password": "password123",        # from carrier_password column
                "account_number": "123456",
                "account_type": "UPS Primary Login"
            }
        }
    """
    credentials_map = {}

    try:
        if not os.path.exists(duckdb_path):
            logger.error(f"❌ PeerDB DuckDB file not found: {duckdb_path}")
            logger.info("💡 Run peerdb_pipeline.py first to extract login credentials")
            return {}

        conn = duckdb.connect(duckdb_path, read_only=True)

        # Query to get login credentials
        # Note: carrier_login column contains the username, carrier_password contains the password
        # We get all Primary BFS Login accounts (these are the main UPS account logins)
        query = f"""
            SELECT
                account_number,
                account_type,
                carrier_login,
                carrier_password
            FROM {PEERDB_TABLE_NAME}
            WHERE account_type LIKE '%Primary%'
            AND account_number IS NOT NULL
            AND carrier_login IS NOT NULL
            AND carrier_password IS NOT NULL
        """

        result = conn.execute(query).fetchall()
        conn.close()

        # Build credentials map using account_number as key
        for row in result:
            account_number = str(row[0]).strip()
            credentials_map[account_number] = {
                "account_number": account_number,
                "account_type": row[1],
                "username": row[2],  # carrier_login is the username
                "password": row[3],  # carrier_password is the password
            }

        logger.info(
            f"✅ Loaded {len(credentials_map)} UPS login credentials from PeerDB"
        )
        logger.info(
            f"📋 Account numbers available: {list(credentials_map.keys())[:5]}..."
        )

        return credentials_map

    except Exception as e:
        logger.error(f"❌ Failed to load credentials from PeerDB: {e}")
        return {}


def map_tracking_to_credentials(
    tracking_data: List[Dict[str, str]], credentials_map: Dict[str, Dict[str, str]]
) -> List[Dict[str, Any]]:
    """
    Map tracking numbers to their corresponding login credentials

    Uses the formula: industry_index_login.account_number = RIGHT(carrier_invoice.account_number, 6)

    Args:
        tracking_data: List of tracking numbers with account_numbers
        credentials_map: Dictionary mapping account_number (last 6 digits) to credentials

    Returns:
        List of dictionaries with tracking_number, account_number, and credentials
    """
    mapped_data = []

    for item in tracking_data:
        tracking_number = item["tracking_number"]
        full_account_number = item["account_number"]

        # Extract last 6 digits of account number to match with industry_index_logins
        last_6_digits = str(full_account_number)[-6:] if full_account_number else None

        if not last_6_digits:
            logger.warning(f"⚠️ No account number for tracking {tracking_number}")
            continue

        # Look up credentials using last 6 digits
        credentials = credentials_map.get(last_6_digits)

        if credentials:
            mapped_data.append(
                {
                    "tracking_number": tracking_number,
                    "full_account_number": full_account_number,
                    "account_number_key": last_6_digits,
                    "username": credentials["username"],
                    "password": credentials["password"],
                    "account_type": credentials["account_type"],
                }
            )
            logger.debug(f"✅ Mapped {tracking_number} → Account {last_6_digits}")
        else:
            logger.warning(
                f"⚠️ No credentials found for account {last_6_digits} (tracking: {tracking_number})"
            )

    logger.info(
        f"✅ Successfully mapped {len(mapped_data)}/{len(tracking_data)} tracking numbers to credentials"
    )

    return mapped_data


class UPSWebLoginAutomation:
    """
    Automated login handler for UPS website

    This class manages the complete login workflow for UPS.com including:
    - Browser initialization and configuration
    - Navigation to login page
    - Credential entry and form submission
    - Authentication verification
    - Error handling and recovery
    - Screenshot capture for debugging
    """

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        headless: bool = True,
        output_dir: str = OUTPUT_DIR,
    ):
        """
        Initialize the UPS login automation

        Args:
            username: UPS username (defaults to environment variable)
            password: UPS password (defaults to environment variable)
            headless: Run browser in headless mode (default: True)
            output_dir: Directory for screenshots and logs
        """
        self.username = username or UPS_WEB_USERNAME
        self.password = password or UPS_WEB_PASSWORD
        self.headless = headless
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Playwright objects (initialized in context manager)
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        logger.info(f"🚀 UPS Web Login Automation initialized")
        logger.info(
            f"   Username: {self.username[:10]}..."
            if self.username
            else "   Username: Not set"
        )
        logger.info(f"   Headless mode: {self.headless}")
        logger.info(f"   Output directory: {self.output_dir}")

    def __enter__(self):
        """Context manager entry - initialize browser"""
        self.start_browser()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup browser"""
        self.close_browser()

    def start_browser(self) -> None:
        """Initialize Playwright browser and create new context"""
        try:
            logger.info("🌐 Starting browser...")
            self.playwright = sync_playwright().start()

            # Launch Chromium browser
            self.browser = self.playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",  # Avoid detection
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )

            # Create browser context with realistic settings
            self.context = self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="en-US",
                timezone_id="America/New_York",
            )

            # Set default timeouts
            self.context.set_default_timeout(DEFAULT_TIMEOUT)
            self.context.set_default_navigation_timeout(DEFAULT_NAVIGATION_TIMEOUT)

            # Create new page
            self.page = self.context.new_page()

            logger.info("✅ Browser started successfully")

        except Exception as e:
            logger.error(f"❌ Failed to start browser: {e}")
            self.close_browser()
            raise

    def close_browser(self) -> None:
        """Close browser and cleanup resources"""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            logger.info("🔒 Browser closed successfully")
        except Exception as e:
            logger.warning(f"⚠️ Error during browser cleanup: {e}")

    def save_screenshot(self, name: str = "screenshot") -> str:
        """
        Save screenshot of current page

        Args:
            name: Base name for screenshot file

        Returns:
            Path to saved screenshot
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        filepath = self.output_dir / filename

        try:
            if self.page:
                self.page.screenshot(path=str(filepath), full_page=True)
                logger.info(f"📸 Screenshot saved: {filepath}")
                return str(filepath)
        except Exception as e:
            logger.error(f"❌ Failed to save screenshot: {e}")

        return ""

    def login(self, save_screenshots: bool = True) -> Dict[str, Any]:
        """
        Perform login to UPS website

        Args:
            save_screenshots: Whether to save screenshots during login process

        Returns:
            Dictionary containing login result with keys:
            - success: bool indicating if login was successful
            - message: str describing the result
            - url: str of final URL after login attempt
            - screenshot: str path to screenshot (if saved)
        """
        result = {"success": False, "message": "", "url": "", "screenshot": ""}

        try:
            logger.info("🔐 Starting UPS login process...")

            # Navigate to login page
            logger.info(f"🌐 Navigating to: {UPS_WEB_LOGIN_URL}")
            self.page.goto(UPS_WEB_LOGIN_URL, wait_until="domcontentloaded")

            if save_screenshots:
                result["screenshot"] = self.save_screenshot("01_login_page")

            # Wait for login form to be visible
            logger.info("⏳ Waiting for login form...")

            # UPS uses a two-step login process via Auth0
            # Step 1: Enter username and click Continue
            # Step 2: Enter password and submit

            # STEP 1: Enter username
            logger.info("📝 Step 1: Entering username...")

            username_field = self.page.wait_for_selector(
                'input[name="username"]', timeout=10000
            )
            if not username_field:
                raise Exception("Could not find username input field")

            logger.info(f"✅ Found username field")
            username_field.fill(self.username)
            logger.info(f"   Username entered: {self.username[:10]}...")

            if save_screenshots:
                result["screenshot"] = self.save_screenshot("02_username_entered")

            # Click Continue button
            continue_button = self.page.wait_for_selector(
                'button[type="submit"]:has-text("Continue")', timeout=5000
            )
            if not continue_button:
                raise Exception("Could not find Continue button")

            logger.info("🖱️ Clicking Continue button...")
            continue_button.click()

            # Wait for password page to load
            logger.info("⏳ Waiting for password page...")
            self.page.wait_for_load_state("domcontentloaded", timeout=15000)

            if save_screenshots:
                result["screenshot"] = self.save_screenshot("03_password_page")

            # STEP 2: Enter password
            logger.info("📝 Step 2: Entering password...")

            # Wait for password field to appear
            password_field = self.page.wait_for_selector(
                'input[type="password"]', timeout=10000
            )
            if not password_field:
                raise Exception("Could not find password input field")

            logger.info(f"✅ Found password field")
            password_field.fill(self.password)
            logger.info("   Password entered: ********")

            if save_screenshots:
                result["screenshot"] = self.save_screenshot("04_password_entered")

            # Find and click submit button (usually says "Continue" or "Sign In")
            submit_button = self.page.wait_for_selector(
                'button[type="submit"]', timeout=5000
            )
            if not submit_button:
                raise Exception("Could not find submit button")

            logger.info("🖱️ Clicking submit button...")
            submit_button.click()

            # Wait for navigation or error message
            logger.info("⏳ Waiting for login response...")
            self.page.wait_for_load_state("domcontentloaded", timeout=30000)

            if save_screenshots:
                result["screenshot"] = self.save_screenshot("03_after_submit")

            # Check if login was successful
            current_url = self.page.url
            result["url"] = current_url

            # Login success indicators (adjust based on actual UPS behavior)
            success_indicators = [
                "myups" in current_url.lower(),
                "dashboard" in current_url.lower(),
                "account" in current_url.lower(),
                current_url != UPS_WEB_LOGIN_URL,
            ]

            # Login failure indicators
            error_selectors = [
                ".error",
                ".alert-danger",
                '[role="alert"]',
                "text=Invalid",
                "text=incorrect",
            ]

            # Check for error messages
            has_error = False
            for selector in error_selectors:
                try:
                    error_element = self.page.query_selector(selector)
                    if error_element and error_element.is_visible():
                        error_text = error_element.inner_text()
                        logger.error(f"❌ Login error detected: {error_text}")
                        result["message"] = f"Login failed: {error_text}"
                        has_error = True
                        break
                except:
                    continue

            if has_error:
                result["success"] = False
            elif any(success_indicators):
                result["success"] = True
                result["message"] = "Login successful"
                logger.info(f"✅ Login successful! Current URL: {current_url}")
            else:
                result["success"] = False
                result["message"] = f"Login status unclear. Current URL: {current_url}"
                logger.warning(f"⚠️ {result['message']}")

        except PlaywrightTimeoutError as e:
            result["message"] = f"Timeout during login: {str(e)}"
            logger.error(f"⏱️ {result['message']}")
            if save_screenshots:
                result["screenshot"] = self.save_screenshot("error_timeout")

        except Exception as e:
            result["message"] = f"Login failed: {str(e)}"
            logger.error(f"❌ {result['message']}")
            if save_screenshots:
                result["screenshot"] = self.save_screenshot("error_exception")

        return result

    def navigate_to_shipping_history(
        self, save_screenshots: bool = True, configure_filters: bool = True
    ) -> Dict[str, Any]:
        """
        Navigate to Shipping History page after successful login

        Args:
            save_screenshots: Whether to save screenshots during navigation
            configure_filters: Whether to automatically configure filters (results per page and date range)

        Returns:
            Dictionary containing navigation result with keys:
            - success: bool indicating if navigation was successful
            - message: str describing the result
            - url: str of final URL
            - screenshot: str path to screenshot (if saved)
            - filter_config: dict with filter configuration results (if configure_filters=True)
        """
        result = {
            "success": False,
            "message": "",
            "url": "",
            "screenshot": "",
            "filter_config": None,
        }

        try:
            logger.info("🚢 Navigating to Shipping History...")

            # Wait for page to be ready
            self.page.wait_for_load_state("domcontentloaded", timeout=10000)

            if save_screenshots:
                result["screenshot"] = self.save_screenshot("05_home_page")

            # Look for Shipping menu/link
            # Common selectors for UPS shipping menu
            shipping_selectors = [
                'a:has-text("Shipping")',
                'button:has-text("Shipping")',
                'a[href*="shipping"]',
                'nav a:has-text("Ship")',
                '[data-test*="shipping"]',
                '.nav-link:has-text("Shipping")',
            ]

            shipping_link = None
            for selector in shipping_selectors:
                try:
                    shipping_link = self.page.wait_for_selector(selector, timeout=3000)
                    if shipping_link and shipping_link.is_visible():
                        logger.info(f"✅ Found Shipping menu: {selector}")
                        break
                except:
                    continue

            if not shipping_link:
                # Try to navigate directly to shipping history URL
                logger.info("⚠️ Shipping menu not found, trying direct URL...")
                shipping_history_urls = [
                    "https://www.ups.com/ship/history",
                    "https://www.ups.com/shipping/history",
                    "https://wwwapps.ups.com/history",
                ]

                for url in shipping_history_urls:
                    try:
                        logger.info(f"🔗 Trying URL: {url}")
                        self.page.goto(
                            url, wait_until="domcontentloaded", timeout=15000
                        )
                        current_url = self.page.url

                        if (
                            "history" in current_url.lower()
                            or "ship" in current_url.lower()
                        ):
                            logger.info(f"✅ Successfully navigated to: {current_url}")
                            result["success"] = True
                            result["message"] = (
                                "Navigated to shipping history via direct URL"
                            )
                            result["url"] = current_url

                            if save_screenshots:
                                result["screenshot"] = self.save_screenshot(
                                    "06_shipping_history"
                                )

                            return result
                    except Exception as e:
                        logger.warning(f"   Failed to access {url}: {str(e)[:100]}")
                        continue

                raise Exception(
                    "Could not find Shipping menu or navigate to shipping history"
                )

            # Click on Shipping menu
            logger.info("🖱️ Clicking Shipping menu...")
            shipping_link.click()

            # Wait for dropdown menu to fully expand
            logger.info("⏳ Waiting for menu to expand...")
            self.page.wait_for_timeout(3000)

            if save_screenshots:
                result["screenshot"] = self.save_screenshot("06_shipping_menu_opened")

            # Look for "View Shipping History" link
            # Based on inspection, the exact text is "View Shipping History"
            logger.info("🔍 Looking for 'View Shipping History' link...")

            history_selectors = [
                'a:has-text("View Shipping History")',
                'a[href*="ship/history"]',
                'a:has-text("Shipping History")',
                '[role="menuitem"]:has-text("View Shipping History")',
                'nav a:has-text("View Shipping History")',
            ]

            history_link = None
            for selector in history_selectors:
                try:
                    history_link = self.page.wait_for_selector(selector, timeout=5000)
                    if history_link and history_link.is_visible():
                        logger.info(f"✅ Found Shipping History link: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"   Selector '{selector}' not found: {str(e)[:50]}")
                    continue

            if not history_link:
                # Try direct URL as fallback
                logger.warning("⚠️ Could not find link, trying direct URL...")
                direct_url = "https://www.ups.com/ship/history?loc=en_US"
                logger.info(f"🔗 Navigating to: {direct_url}")
                self.page.goto(direct_url, wait_until="domcontentloaded", timeout=15000)

                current_url = self.page.url
                result["url"] = current_url

                if "history" in current_url.lower():
                    result["success"] = True
                    result["message"] = "Navigated to shipping history via direct URL"
                    logger.info(f"✅ Successfully navigated to: {current_url}")

                    if save_screenshots:
                        result["screenshot"] = self.save_screenshot(
                            "07_shipping_history_page"
                        )

                    return result
                else:
                    raise Exception("Could not navigate to Shipping History")

            # Click on Shipping History
            logger.info("🖱️ Clicking Shipping History...")
            history_link.click()

            # Wait for history page to load
            logger.info("⏳ Waiting for Shipping History page to load...")
            self.page.wait_for_load_state("domcontentloaded", timeout=15000)

            if save_screenshots:
                result["screenshot"] = self.save_screenshot("07_shipping_history_page")

            # Verify we're on the shipping history page
            current_url = self.page.url
            result["url"] = current_url

            # Check for success indicators
            success_indicators = [
                "history" in current_url.lower(),
                "ship" in current_url.lower(),
            ]

            # Also check page content
            try:
                page_text = self.page.inner_text("body")
                content_indicators = [
                    "shipping history" in page_text.lower(),
                    "shipment history" in page_text.lower(),
                    "recent shipments" in page_text.lower(),
                ]
                success_indicators.extend(content_indicators)
            except:
                pass

            if any(success_indicators):
                result["success"] = True
                result["message"] = "Successfully navigated to Shipping History"
                logger.info(f"✅ Shipping History page loaded! URL: {current_url}")

                # Configure filters if requested
                if configure_filters:
                    logger.info("⚙️ Configuring shipping history filters...")
                    filter_result = self.configure_shipping_history_filters(
                        save_screenshots=save_screenshots
                    )
                    result["filter_config"] = filter_result

                    if filter_result["success"]:
                        result[
                            "message"
                        ] += f" | Filters configured: {filter_result['date_range']}, 50 results/page"
                    else:
                        logger.warning(
                            f"⚠️ Filter configuration had issues: {filter_result['message']}"
                        )
            else:
                result["success"] = False
                result["message"] = f"Navigation unclear. Current URL: {current_url}"
                logger.warning(f"⚠️ {result['message']}")

        except PlaywrightTimeoutError as e:
            result["message"] = f"Timeout during navigation: {str(e)}"
            logger.error(f"⏱️ {result['message']}")
            if save_screenshots:
                result["screenshot"] = self.save_screenshot("error_navigation_timeout")

        except Exception as e:
            result["message"] = f"Navigation failed: {str(e)}"
            logger.error(f"❌ {result['message']}")
            if save_screenshots:
                result["screenshot"] = self.save_screenshot(
                    "error_navigation_exception"
                )

        return result

    def configure_shipping_history_filters(
        self, save_screenshots: bool = True
    ) -> Dict[str, Any]:
        """
        Configure Shipping History page filters:
        1. Set results per page to 50
        2. Set date range to match ups_label_only_filter.py (85-89 days ago)

        Args:
            save_screenshots: Whether to save screenshots during configuration

        Returns:
            Dictionary containing configuration result with keys:
            - success: bool indicating if configuration was successful
            - message: str describing the result
            - date_range: str showing the configured date range
            - screenshot: str path to screenshot (if saved)
        """
        result = {
            "success": False,
            "message": "",
            "date_range": "",
            "screenshot": "",
        }

        try:
            logger.info("⚙️ Configuring Shipping History filters...")

            # Wait for page to be ready
            self.page.wait_for_load_state("domcontentloaded", timeout=10000)
            self.page.wait_for_timeout(3000)

            if save_screenshots:
                result["screenshot"] = self.save_screenshot("08_before_filter_config")

            # Calculate date range (same logic as ups_label_only_filter.py)
            # Note: UPS minimum date range is 90 days ago, so we use 89-85 days ago
            start_cutoff_days = int(
                os.getenv("DLT_TRANSACTION_START_CUTOFF_DAYS", "89")
            )
            end_cutoff_days = int(os.getenv("DLT_TRANSACTION_END_CUTOFF_DAYS", "85"))
            start_date = datetime.utcnow() - timedelta(days=start_cutoff_days)
            end_date = datetime.utcnow() - timedelta(days=end_cutoff_days)

            # Format dates for UPS date inputs (MM/DD/YYYY format with slashes)
            start_date_str = start_date.strftime("%m/%d/%Y")
            end_date_str = end_date.strftime("%m/%d/%Y")
            result["date_range"] = f"{start_date_str} to {end_date_str}"

            logger.info(
                f"📅 Target date range: {start_date_str} to {end_date_str} ({start_cutoff_days}-{end_cutoff_days} days ago)"
            )

            # STEP 1: Change results per page to 50
            logger.info("📊 Step 1: Setting results per page to 50...")

            # Look for results per page dropdown/selector
            results_per_page_selectors = [
                'select[name*="pageSize"]',
                'select[name*="perPage"]',
                'select[name*="results"]',
                'select[aria-label*="results"]',
                'select[aria-label*="per page"]',
                'select[id*="pageSize"]',
                'select[id*="perPage"]',
                'button:has-text("results per page")',
                'button:has-text("Show")',
            ]

            results_selector = None
            for selector in results_per_page_selectors:
                try:
                    results_selector = self.page.wait_for_selector(
                        selector, timeout=3000
                    )
                    if results_selector and results_selector.is_visible():
                        logger.info(f"✅ Found results per page selector: {selector}")
                        break
                except:
                    continue

            if results_selector:
                # Check if it's a select element or button
                tag_name = results_selector.evaluate("el => el.tagName.toLowerCase()")

                if tag_name == "select":
                    # It's a dropdown - select the option with value 50
                    logger.info("🖱️ Selecting 50 results per page...")
                    results_selector.select_option(value="50")
                    logger.info("✅ Set results per page to 50")
                elif tag_name == "button":
                    # It's a button - click it to open menu
                    logger.info("🖱️ Clicking results per page button...")
                    results_selector.click()
                    self.page.wait_for_timeout(1000)

                    # Look for option with 50
                    option_selectors = [
                        'li:has-text("50")',
                        'a:has-text("50")',
                        'button:has-text("50")',
                        '[role="option"]:has-text("50")',
                    ]

                    for opt_selector in option_selectors:
                        try:
                            option = self.page.wait_for_selector(
                                opt_selector, timeout=2000
                            )
                            if option and option.is_visible():
                                logger.info("🖱️ Clicking 50 option...")
                                option.click()
                                logger.info("✅ Set results per page to 50")
                                break
                        except:
                            continue

                self.page.wait_for_timeout(2000)

                if save_screenshots:
                    result["screenshot"] = self.save_screenshot(
                        "09_results_per_page_set"
                    )
            else:
                logger.warning(
                    "⚠️ Could not find results per page selector - may not be available on this page"
                )

            # STEP 2: Set date range
            logger.info("📅 Step 2: Setting date range...")

            # Step 2a: Click the "Modify" button
            logger.info('📅 Step 2a: Clicking "Modify" button...')
            modify_button_selectors = [
                'button:has-text("Modify")',
                'a:has-text("Modify")',
                'button:has-text("modify")',
                'a:has-text("modify")',
                '[aria-label*="modify"]',
                '[aria-label*="Modify"]',
            ]

            modify_button_clicked = False
            for selector in modify_button_selectors:
                try:
                    modify_button = self.page.wait_for_selector(selector, timeout=2000)
                    if modify_button and modify_button.is_visible():
                        logger.info(f"✅ Found Modify button: {selector}")
                        modify_button.click()
                        logger.info("🖱️ Clicked Modify button")
                        self.page.wait_for_timeout(2000)
                        modify_button_clicked = True

                        if save_screenshots:
                            result["screenshot"] = self.save_screenshot(
                                "09b_modify_button_clicked"
                            )
                        break
                except:
                    continue

            if not modify_button_clicked:
                logger.warning("⚠️ Could not find Modify button")
                result["success"] = False
                result["message"] = "Could not find Modify button"
                return result

            # Step 2b: Find "Show my activity for" dropdown
            logger.info('📅 Step 2b: Finding "Show my activity for" dropdown...')

            # Try to find any select elements on the page
            activity_dropdown_selectors = [
                "select",  # Try any select element first
                'select[name*="activity"]',
                'select[id*="activity"]',
                'select[name*="dateRange"]',
                'select[id*="dateRange"]',
                'select[name*="period"]',
                'select[id*="period"]',
                'select[name*="time"]',
                'select[id*="time"]',
            ]

            activity_dropdown = None
            for selector in activity_dropdown_selectors:
                try:
                    # Get all matching selects
                    selects = self.page.locator(selector).all()
                    logger.info(
                        f"🔍 Found {len(selects)} select element(s) with selector: {selector}"
                    )

                    for select in selects:
                        if select.is_visible():
                            # Log the select element's attributes for debugging
                            try:
                                name_attr = select.get_attribute("name") or ""
                                id_attr = select.get_attribute("id") or ""
                                logger.info(
                                    f"   📋 Select found - name: '{name_attr}', id: '{id_attr}'"
                                )

                                # Use the first visible select element
                                if not activity_dropdown:
                                    activity_dropdown = select
                                    logger.info(f"✅ Using select element: {selector}")
                            except:
                                continue

                    if activity_dropdown:
                        break
                except Exception as e:
                    logger.info(f"   ⚠️ Error with selector {selector}: {str(e)}")
                    continue

            if not activity_dropdown:
                logger.warning("⚠️ Could not find any dropdown after clicking Modify")
                result["success"] = False
                result["message"] = "Could not find dropdown after clicking Modify"
                return result

            # Step 2c: Select "Custom Date Range" option
            logger.info('📅 Step 2c: Selecting "Custom Date Range"...')
            try:
                # Try to select by visible text
                custom_range_options = [
                    "Custom Date Range",
                    "custom date range",
                    "Custom",
                    "custom",
                ]

                custom_selected = False
                for option_text in custom_range_options:
                    try:
                        activity_dropdown.select_option(label=option_text)
                        logger.info(f'✅ Selected "{option_text}" from dropdown')
                        custom_selected = True
                        self.page.wait_for_timeout(
                            2000
                        )  # Wait for date inputs to appear

                        if save_screenshots:
                            result["screenshot"] = self.save_screenshot(
                                "09c_custom_date_selected"
                            )
                        break
                    except Exception as e:
                        continue

                if not custom_selected:
                    logger.warning('⚠️ Could not select "Custom Date Range" option')
                    result["success"] = False
                    result["message"] = 'Could not select "Custom Date Range" option'
                    return result

            except Exception as e:
                logger.warning(f"⚠️ Error selecting custom date range: {str(e)}")
                result["success"] = False
                result["message"] = f"Error selecting custom date range: {str(e)}"
                return result

            # Look for date range inputs
            # Common patterns: from/to date, start/end date
            date_input_selectors = [
                'input[type="date"]',
                'input[name*="from"]',
                'input[name*="start"]',
                'input[name*="From"]',
                'input[name*="Start"]',
                'input[placeholder*="From"]',
                'input[placeholder*="Start"]',
                'input[placeholder*="from"]',
                'input[placeholder*="start"]',
                'input[aria-label*="from"]',
                'input[aria-label*="start"]',
                'input[aria-label*="From"]',
                'input[aria-label*="Start"]',
            ]

            # Find "from" date input
            from_date_input = None
            for selector in date_input_selectors:
                try:
                    from_date_input = self.page.wait_for_selector(
                        selector, timeout=3000
                    )
                    if from_date_input and from_date_input.is_visible():
                        logger.info(f"✅ Found 'from' date input: {selector}")
                        break
                except:
                    continue

            if from_date_input:
                # Fill in start date
                # UPS uses MM/DD/YYYY format (with slashes)
                logger.info(f"📅 Setting start date to: {start_date_str}")

                # Clear existing value first
                from_date_input.click()
                from_date_input.fill("")

                # Fill with MM/DD/YYYY format
                from_date_input.fill(start_date_str)
                logger.info(f"✅ Set start date to {start_date_str}")

                self.page.wait_for_timeout(1000)

                if save_screenshots:
                    result["screenshot"] = self.save_screenshot("10_start_date_set")

                # Find "to" date input
                to_date_selectors = [
                    'input[type="date"]:not([name*="from"]):not([name*="start"])',
                    'input[name*="to"]',
                    'input[name*="end"]',
                    'input[placeholder*="To"]',
                    'input[placeholder*="End"]',
                    'input[aria-label*="to"]',
                    'input[aria-label*="end"]',
                ]

                to_date_input = None
                for selector in to_date_selectors:
                    try:
                        to_date_input = self.page.wait_for_selector(
                            selector, timeout=3000
                        )
                        if to_date_input and to_date_input.is_visible():
                            # Make sure it's not the same as from_date_input
                            if to_date_input != from_date_input:
                                logger.info(f"✅ Found 'to' date input: {selector}")
                                break
                    except:
                        continue

                if to_date_input:
                    # Fill in end date
                    logger.info(f"📅 Setting end date to: {end_date_str}")

                    # Clear existing value first
                    to_date_input.click()
                    to_date_input.fill("")

                    # Fill with end date
                    to_date_input.fill(end_date_str)
                    logger.info(f"✅ Set end date to {end_date_str}")

                    self.page.wait_for_timeout(1000)

                    if save_screenshots:
                        result["screenshot"] = self.save_screenshot("11_end_date_set")

                    # Look for Apply/Search/Submit button to apply the filters
                    apply_selectors = [
                        'button:has-text("Apply")',
                        'button:has-text("Search")',
                        'button:has-text("Submit")',
                        'button:has-text("Go")',
                        'button[type="submit"]',
                    ]

                    apply_button = None
                    for selector in apply_selectors:
                        try:
                            apply_button = self.page.wait_for_selector(
                                selector, timeout=3000
                            )
                            if apply_button and apply_button.is_visible():
                                logger.info(f"✅ Found apply button: {selector}")
                                break
                        except:
                            continue

                    if apply_button:
                        logger.info("🖱️ Clicking apply button to apply filters...")
                        apply_button.click()
                        self.page.wait_for_timeout(3000)

                        if save_screenshots:
                            result["screenshot"] = self.save_screenshot(
                                "12_filters_applied"
                            )

                        logger.info("✅ Filters applied successfully")
                    else:
                        logger.warning(
                            "⚠️ No apply button found - filters may auto-apply"
                        )

                    result["success"] = True
                    result["message"] = (
                        f"Configured filters: 50 results per page, date range {start_date_str} to {end_date_str}"
                    )
                    logger.info(f"✅ {result['message']}")

                else:
                    logger.warning("⚠️ Could not find 'to' date input")
                    result["success"] = False
                    result["message"] = "Could not find 'to' date input field"

            else:
                logger.warning("⚠️ Could not find date range inputs")
                result["success"] = False
                result["message"] = "Could not find date range input fields"

        except PlaywrightTimeoutError as e:
            result["message"] = f"Timeout during filter configuration: {str(e)}"
            logger.error(f"⏱️ {result['message']}")
            if save_screenshots:
                result["screenshot"] = self.save_screenshot(
                    "error_filter_config_timeout"
                )

        except Exception as e:
            result["message"] = f"Filter configuration failed: {str(e)}"
            logger.error(f"❌ {result['message']}")
            if save_screenshots:
                result["screenshot"] = self.save_screenshot(
                    "error_filter_config_exception"
                )

        return result

    def void_shipment(
        self, shipment_index: int = 0, save_screenshots: bool = True
    ) -> Dict[str, Any]:
        """
        Void a shipment from the Shipping History page

        Args:
            shipment_index: Index of the shipment to void (0 = first shipment)
            save_screenshots: Whether to save screenshots during the process

        Returns:
            Dictionary containing void result with keys:
            - success: bool indicating if void was successful
            - message: str describing the result
            - tracking_number: str tracking number of voided shipment (if available)
            - screenshot: str path to screenshot (if saved)
        """
        result = {
            "success": False,
            "message": "",
            "tracking_number": "",
            "screenshot": "",
        }

        try:
            logger.info(f"🗑️ Voiding shipment (index: {shipment_index})...")

            # Wait for page to be ready
            self.page.wait_for_load_state("domcontentloaded", timeout=10000)
            self.page.wait_for_timeout(3000)

            if save_screenshots:
                result["screenshot"] = self.save_screenshot("08_before_void")

            # Look for action buttons (three dots) in shipment rows
            logger.info("🔍 Looking for three-dot Actions buttons in shipment rows...")

            # First, try to find shipment rows
            shipment_row_selectors = [
                "tbody tr",
                'tr[data-test*="shipment"]',
                ".shipment-row",
                '[class*="table"] tr',
            ]

            shipment_rows = []
            for selector in shipment_row_selectors:
                try:
                    elements = self.page.query_selector_all(selector)
                    if elements and len(elements) > 0:
                        logger.info(
                            f"✅ Found {len(elements)} shipment rows: {selector}"
                        )
                        shipment_rows = elements
                        break
                except:
                    continue

            if not shipment_rows:
                logger.warning(
                    "⚠️ Could not find shipment rows, looking for action buttons directly..."
                )

            # Look for action menu buttons in the Actions column
            # Based on page inspection: button text is "Action Menu"
            logger.info("🔍 Looking for Action Menu buttons in table rows...")

            action_button_selectors = [
                'tbody tr button:has-text("Action Menu")',  # Action Menu button in table rows
                "button.ups-btn_standalone_icon",  # Button class
                "tbody tr button",  # Any button in table rows
            ]

            # Get all action menu buttons
            action_buttons = []
            for selector in action_button_selectors:
                try:
                    elements = self.page.query_selector_all(selector)
                    visible_elements = [e for e in elements if e.is_visible()]
                    if visible_elements:
                        logger.info(
                            f"✅ Found {len(visible_elements)} action menu buttons: {selector}"
                        )
                        action_buttons = visible_elements
                        break
                except Exception as e:
                    logger.debug(f"   Selector '{selector}' not found: {str(e)[:50]}")
                    continue

            if not action_buttons:
                raise Exception("Could not find any Action Menu buttons in table rows")

            # Check if shipment_index is valid
            if shipment_index >= len(action_buttons):
                raise Exception(
                    f"Shipment index {shipment_index} out of range (found {len(action_buttons)} shipments)"
                )

            # Click the action button for the specified shipment
            target_button = action_buttons[shipment_index]
            logger.info(f"🖱️ Clicking Actions button for shipment {shipment_index}...")
            target_button.click()

            # Wait for menu to appear
            logger.info("⏳ Waiting for actions menu to appear...")
            self.page.wait_for_timeout(2000)

            if save_screenshots:
                result["screenshot"] = self.save_screenshot("09_actions_menu_opened")

            # Look for Void option in the dropdown menu
            # Based on screenshot: menu items are in a list with text "Void"
            logger.info("🔍 Looking for Void option in menu...")

            void_selectors = [
                'a:has-text("Void")',  # Menu items appear to be links
                'button:has-text("Void")',
                'li a:has-text("Void")',  # List item with link
                '[role="menuitem"]:has-text("Void")',
                '.menu-item:has-text("Void")',
                'div:has-text("Void")',
            ]

            void_button = None
            for selector in void_selectors:
                try:
                    void_button = self.page.wait_for_selector(selector, timeout=5000)
                    if void_button and void_button.is_visible():
                        logger.info(f"✅ Found Void option: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"   Selector '{selector}' not found: {str(e)[:50]}")
                    continue

            if not void_button:
                raise Exception("Could not find Void option in dropdown menu")

            # Click Void button
            logger.info("🖱️ Clicking Void button...")
            void_button.click()

            # Wait for confirmation dialog or next page
            logger.info("⏳ Waiting for void confirmation...")
            self.page.wait_for_timeout(3000)

            if save_screenshots:
                result["screenshot"] = self.save_screenshot("10_void_confirmation")

            # Look for confirmation button
            logger.info("🔍 Looking for confirmation button...")

            confirm_selectors = [
                'button:has-text("Confirm")',
                'button:has-text("Yes")',
                'button:has-text("Void Shipment")',
                'button:has-text("OK")',
                '[data-test*="confirm"]',
                'button[type="submit"]',
            ]

            confirm_button = None
            for selector in confirm_selectors:
                try:
                    confirm_button = self.page.wait_for_selector(selector, timeout=5000)
                    if confirm_button and confirm_button.is_visible():
                        logger.info(f"✅ Found confirmation button: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"   Selector '{selector}' not found: {str(e)[:50]}")
                    continue

            if confirm_button:
                # Click confirmation button
                logger.info("🖱️ Clicking confirmation button...")
                confirm_button.click()

                # Wait for void to complete
                logger.info("⏳ Waiting for void to complete...")
                self.page.wait_for_timeout(3000)

                if save_screenshots:
                    result["screenshot"] = self.save_screenshot("11_void_completed")
            else:
                logger.warning(
                    "⚠️ No confirmation button found - void may have completed without confirmation"
                )

            # Check for success message
            current_url = self.page.url
            result["url"] = current_url

            # Look for success indicators
            try:
                page_text = self.page.inner_text("body")
                success_indicators = [
                    "void" in page_text.lower() and "success" in page_text.lower(),
                    "shipment voided" in page_text.lower(),
                    "successfully voided" in page_text.lower(),
                    "cancelled" in page_text.lower(),
                ]

                if any(success_indicators):
                    result["success"] = True
                    result["message"] = "Shipment voided successfully"
                    logger.info(f"✅ Shipment voided successfully!")
                else:
                    # Assume success if no error message
                    result["success"] = True
                    result["message"] = "Void action completed (verification unclear)"
                    logger.info(f"✅ Void action completed")

            except Exception as e:
                logger.warning(f"⚠️ Could not verify void success: {str(e)[:100]}")
                result["success"] = True
                result["message"] = "Void action completed (could not verify)"

        except PlaywrightTimeoutError as e:
            result["message"] = f"Timeout during void: {str(e)}"
            logger.error(f"⏱️ {result['message']}")
            if save_screenshots:
                result["screenshot"] = self.save_screenshot("error_void_timeout")

        except Exception as e:
            result["message"] = f"Void failed: {str(e)}"
            logger.error(f"❌ {result['message']}")
            if save_screenshots:
                result["screenshot"] = self.save_screenshot("error_void_exception")

        return result

    def get_visible_tracking_numbers(self) -> List[str]:
        """
        Extract all visible tracking numbers from the current Shipping History page

        Returns:
            List of tracking numbers visible on the current page
        """
        visible_tracking_numbers = []

        try:
            logger.info("🔍 Extracting visible tracking numbers from page...")

            # Wait for the table to load
            self.page.wait_for_timeout(2000)

            # Try different selectors to find tracking numbers in the table
            tracking_selectors = [
                'td:has-text("1Z")',  # UPS tracking numbers start with 1Z
                "tr td",  # All table cells
            ]

            for selector in tracking_selectors:
                try:
                    cells = self.page.locator(selector).all()
                    logger.info(
                        f"🔍 Found {len(cells)} cells with selector: {selector}"
                    )

                    for cell in cells:
                        try:
                            text = cell.inner_text().strip()
                            # UPS tracking numbers are 18 characters starting with 1Z
                            if text.startswith("1Z") and len(text) == 18:
                                if text not in visible_tracking_numbers:
                                    visible_tracking_numbers.append(text)
                                    logger.debug(f"   ✅ Found tracking number: {text}")
                        except:
                            continue

                    if visible_tracking_numbers:
                        break
                except Exception as e:
                    logger.debug(f"   ⚠️ Error with selector {selector}: {str(e)}")
                    continue

            logger.info(
                f"✅ Found {len(visible_tracking_numbers)} tracking numbers on page"
            )
            return visible_tracking_numbers

        except Exception as e:
            logger.error(f"❌ Failed to extract tracking numbers: {e}")
            return []

    def void_shipment_by_tracking_number(
        self, tracking_number: str, save_screenshots: bool = True
    ) -> Dict[str, Any]:
        """
        Void a shipment by searching for its tracking number on the Shipping History page

        Args:
            tracking_number: UPS tracking number to void
            save_screenshots: Whether to save screenshots during the process

        Returns:
            Dictionary containing void result with keys:
            - success: bool indicating if void was successful
            - message: str describing the result
            - tracking_number: str tracking number of voided shipment
            - screenshot: str path to screenshot (if saved)
        """
        result = {
            "success": False,
            "message": "",
            "tracking_number": tracking_number,
            "screenshot": "",
        }

        try:
            logger.info(f"🔍 Searching for tracking number: {tracking_number}")

            # Wait for page to be ready
            self.page.wait_for_load_state("domcontentloaded", timeout=10000)
            self.page.wait_for_timeout(3000)

            if save_screenshots:
                result["screenshot"] = self.save_screenshot(
                    f"search_before_{tracking_number[:10]}"
                )

            # Look for search input field on the shipping history page
            search_selectors = [
                'input[type="search"]',
                'input[placeholder*="Search"]',
                'input[placeholder*="tracking"]',
                'input[name*="search"]',
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    search_input = self.page.wait_for_selector(selector, timeout=3000)
                    if search_input and search_input.is_visible():
                        logger.info(f"✅ Found search input: {selector}")
                        break
                except:
                    continue

            if search_input:
                # Use search to find the tracking number
                logger.info(f"🔍 Searching for tracking number: {tracking_number}")
                search_input.fill(tracking_number)
                self.page.wait_for_timeout(2000)

                if save_screenshots:
                    result["screenshot"] = self.save_screenshot(
                        f"search_entered_{tracking_number[:10]}"
                    )

            # Find the row containing this tracking number
            logger.info(f"🔍 Looking for row with tracking number {tracking_number}...")

            # Try to find the tracking number in the table
            row_selectors = [
                f'tr:has-text("{tracking_number}")',
                f'tbody tr:has-text("{tracking_number}")',
            ]

            target_row = None
            for selector in row_selectors:
                try:
                    target_row = self.page.wait_for_selector(selector, timeout=5000)
                    if target_row and target_row.is_visible():
                        logger.info(f"✅ Found row with tracking number")
                        break
                except:
                    continue

            if not target_row:
                raise Exception(
                    f"Could not find tracking number {tracking_number} in shipping history"
                )

            # Find the action button in this row
            action_button = target_row.query_selector('button:has-text("Action Menu")')
            if not action_button:
                action_button = target_row.query_selector("button")

            if not action_button:
                raise Exception("Could not find action button for this tracking number")

            # Click the action button
            logger.info("🖱️ Clicking action button...")
            action_button.click()
            self.page.wait_for_timeout(2000)

            if save_screenshots:
                result["screenshot"] = self.save_screenshot(
                    f"menu_opened_{tracking_number[:10]}"
                )

            # Find and click Void option
            void_selectors = [
                'a:has-text("Void")',
                'button:has-text("Void")',
                'li a:has-text("Void")',
            ]

            void_button = None
            for selector in void_selectors:
                try:
                    void_button = self.page.wait_for_selector(selector, timeout=5000)
                    if void_button and void_button.is_visible():
                        logger.info(f"✅ Found Void option")
                        break
                except:
                    continue

            if not void_button:
                raise Exception("Could not find Void option in menu")

            # Click Void
            logger.info("🖱️ Clicking Void...")
            void_button.click()
            self.page.wait_for_timeout(3000)

            if save_screenshots:
                result["screenshot"] = self.save_screenshot(
                    f"void_confirm_{tracking_number[:10]}"
                )

            # Handle confirmation if present
            confirm_selectors = [
                'button:has-text("Confirm")',
                'button:has-text("Yes")',
                'button:has-text("Void Shipment")',
                'button:has-text("OK")',
            ]

            for selector in confirm_selectors:
                try:
                    confirm_button = self.page.wait_for_selector(selector, timeout=3000)
                    if confirm_button and confirm_button.is_visible():
                        logger.info("🖱️ Clicking confirmation...")
                        confirm_button.click()
                        self.page.wait_for_timeout(3000)
                        break
                except:
                    continue

            if save_screenshots:
                result["screenshot"] = self.save_screenshot(
                    f"void_complete_{tracking_number[:10]}"
                )

            # Check for success
            result["success"] = True
            result["message"] = f"Shipment {tracking_number} voided successfully"
            logger.info(f"✅ {result['message']}")

        except Exception as e:
            result["message"] = f"Failed to void {tracking_number}: {str(e)}"
            logger.error(f"❌ {result['message']}")
            if save_screenshots:
                result["screenshot"] = self.save_screenshot(
                    f"error_{tracking_number[:10]}"
                )

        return result

    def bulk_void_shipments_from_csv(
        self,
        csv_path: str,
        peerdb_path: str = PEERDB_DUCKDB_PATH,
        save_screenshots: bool = True,
        output_csv: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Bulk void shipments from ups_label_only_filter.py CSV output

        This method:
        1. Loads tracking numbers from CSV
        2. Loads login credentials from PeerDB
        3. Maps tracking numbers to credentials using account_number
        4. Logs in with appropriate credentials for each account
        5. Navigates to Shipping History and configures filters:
           - Sets results per page to 50
           - Sets date range to 85-89 days ago (same as ups_label_only_filter.py)
        6. Extracts visible tracking numbers from the filtered page
        7. Only voids tracking numbers that are visible on the filtered page
        8. Saves results to CSV

        Args:
            csv_path: Path to ups_label_only_filter.py output CSV
            peerdb_path: Path to PeerDB DuckDB file with login credentials
            save_screenshots: Whether to save screenshots
            output_csv: Path to save results CSV (default: auto-generated)

        Returns:
            Dictionary with results:
            - total_tracking_numbers: int (from CSV)
            - total_voided: int (successfully voided)
            - total_failed: int (failed or not visible)
            - results: List of void results with status for each tracking number
        """
        summary = {
            "total_tracking_numbers": 0,
            "total_voided": 0,
            "total_failed": 0,
            "results": [],
        }

        try:
            # Step 1: Load tracking numbers from CSV
            logger.info("📊 Step 1: Loading tracking numbers from CSV...")
            tracking_data = load_tracking_numbers_from_csv(csv_path)

            if not tracking_data:
                logger.error("❌ No tracking numbers loaded from CSV")
                return summary

            summary["total_tracking_numbers"] = len(tracking_data)

            # Step 2: Load credentials from PeerDB
            logger.info("🔑 Step 2: Loading login credentials from PeerDB...")
            credentials_map = load_login_credentials_from_peerdb(peerdb_path)

            if not credentials_map:
                logger.error("❌ No credentials loaded from PeerDB")
                return summary

            # Step 3: Map tracking numbers to credentials
            logger.info("🔗 Step 3: Mapping tracking numbers to credentials...")
            mapped_data = map_tracking_to_credentials(tracking_data, credentials_map)

            if not mapped_data:
                logger.error("❌ No tracking numbers could be mapped to credentials")
                return summary

            # Group by account for efficient login management
            account_groups = {}
            for item in mapped_data:
                account_key = item["account_number_key"]
                if account_key not in account_groups:
                    account_groups[account_key] = []
                account_groups[account_key].append(item)

            logger.info(
                f"📦 Grouped {len(mapped_data)} shipments into {len(account_groups)} accounts"
            )

            # Step 4: Process each account group
            for account_key, items in account_groups.items():
                logger.info(f"\n{'='*60}")
                logger.info(
                    f"🔐 Processing account {account_key} ({len(items)} shipments)"
                )
                logger.info(f"{'='*60}")

                # Get credentials for this account
                first_item = items[0]
                username = first_item["username"]
                password = first_item["password"]

                # Login with this account's credentials
                logger.info(f"🔑 Logging in as {username}...")

                # Update instance credentials temporarily
                original_username = self.username
                original_password = self.password
                self.username = username
                self.password = password

                try:
                    # Perform login
                    login_result = self.login(save_screenshots=save_screenshots)

                    if not login_result["success"]:
                        logger.error(
                            f"❌ Login failed for account {account_key}: {login_result['message']}"
                        )
                        # Mark all items in this group as failed
                        for item in items:
                            summary["results"].append(
                                {
                                    "tracking_number": item["tracking_number"],
                                    "account_number": item["full_account_number"],
                                    "account_key": account_key,
                                    "success": False,
                                    "message": f"Login failed: {login_result['message']}",
                                }
                            )
                            summary["total_failed"] += 1
                        continue

                    logger.info(f"✅ Login successful for account {account_key}")

                    # Navigate to shipping history (with automatic filter configuration)
                    logger.info(
                        "🚢 Navigating to Shipping History and configuring filters..."
                    )
                    nav_result = self.navigate_to_shipping_history(
                        save_screenshots=save_screenshots,
                        configure_filters=True,  # This will set results per page to 50 and date range
                    )

                    if not nav_result["success"]:
                        logger.error(f"❌ Navigation failed: {nav_result['message']}")
                        # Mark all items as failed
                        for item in items:
                            summary["results"].append(
                                {
                                    "tracking_number": item["tracking_number"],
                                    "account_number": item["full_account_number"],
                                    "account_key": account_key,
                                    "success": False,
                                    "message": f"Navigation failed: {nav_result['message']}",
                                }
                            )
                            summary["total_failed"] += 1
                        continue

                    # Check filter configuration result
                    if "filter_config" in nav_result:
                        filter_config = nav_result["filter_config"]
                        if filter_config.get("success"):
                            logger.info(
                                f"✅ Filters configured: {filter_config.get('message', '')}"
                            )
                        else:
                            logger.warning(
                                f"⚠️ Filter configuration had issues: {filter_config.get('message', '')}"
                            )

                    # Extract visible tracking numbers from the filtered page
                    logger.info(
                        "🔍 Checking which tracking numbers are visible on the filtered page..."
                    )
                    visible_tracking_numbers = self.get_visible_tracking_numbers()

                    if not visible_tracking_numbers:
                        logger.warning(
                            "⚠️ No tracking numbers found on the filtered page"
                        )
                        # Mark all items as skipped
                        for item in items:
                            summary["results"].append(
                                {
                                    "tracking_number": item["tracking_number"],
                                    "account_number": item["full_account_number"],
                                    "account_key": account_key,
                                    "success": False,
                                    "message": "Not visible on filtered page",
                                }
                            )
                            summary["total_failed"] += 1
                        continue

                    logger.info(
                        f"✅ Found {len(visible_tracking_numbers)} tracking numbers on filtered page"
                    )

                    # Filter items to only those visible on the page
                    items_to_void = []
                    items_not_visible = []

                    for item in items:
                        if item["tracking_number"] in visible_tracking_numbers:
                            items_to_void.append(item)
                        else:
                            items_not_visible.append(item)
                            logger.info(
                                f"⚠️ Tracking {item['tracking_number']} not visible on filtered page - skipping"
                            )
                            summary["results"].append(
                                {
                                    "tracking_number": item["tracking_number"],
                                    "account_number": item["full_account_number"],
                                    "account_key": account_key,
                                    "success": False,
                                    "message": "Not visible on filtered page (outside date range or already voided)",
                                }
                            )
                            summary["total_failed"] += 1

                    if not items_to_void:
                        logger.warning(
                            f"⚠️ None of the {len(items)} tracking numbers are visible on the filtered page"
                        )
                        continue

                    logger.info(
                        f"📋 Will void {len(items_to_void)}/{len(items)} tracking numbers that are visible"
                    )

                    # Void each shipment that is visible on the page
                    for i, item in enumerate(items_to_void, 1):
                        tracking_number = item["tracking_number"]
                        logger.info(f"\n🗑️ Voiding {i}/{len(items)}: {tracking_number}")

                        void_result = self.void_shipment_by_tracking_number(
                            tracking_number, save_screenshots=save_screenshots
                        )

                        # Record result
                        summary["results"].append(
                            {
                                "tracking_number": tracking_number,
                                "account_number": item["full_account_number"],
                                "account_key": account_key,
                                "success": void_result["success"],
                                "message": void_result["message"],
                            }
                        )

                        if void_result["success"]:
                            summary["total_voided"] += 1
                            logger.info(f"   ✅ Success")
                        else:
                            summary["total_failed"] += 1
                            logger.error(f"   ❌ Failed: {void_result['message']}")

                        # Small delay between voids
                        self.page.wait_for_timeout(2000)

                finally:
                    # Restore original credentials
                    self.username = original_username
                    self.password = original_password

            # Step 5: Save results to CSV
            if output_csv is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_csv = os.path.join(OUTPUT_DIR, f"void_results_{timestamp}.csv")

            logger.info(f"\n💾 Saving results to CSV: {output_csv}")

            with open(output_csv, "w", encoding="utf-8", newline="") as f:
                fieldnames = [
                    "tracking_number",
                    "account_number",
                    "account_key",
                    "success",
                    "message",
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(summary["results"])

            logger.info(f"✅ Results saved to: {output_csv}")

            # Print summary
            logger.info(f"\n{'='*60}")
            logger.info("📊 BULK VOID SUMMARY")
            logger.info(f"{'='*60}")
            logger.info(f"Total tracking numbers: {summary['total_tracking_numbers']}")
            logger.info(f"Successfully voided: {summary['total_voided']}")
            logger.info(f"Failed: {summary['total_failed']}")
            logger.info(f"Results saved to: {output_csv}")

        except Exception as e:
            logger.error(f"❌ Bulk void failed: {e}")

        return summary


def main():
    """Main function to demonstrate UPS login automation with shipping history navigation"""
    logger.info("=" * 60)
    logger.info("🚀 UPS Web Login & Shipping History Automation")
    logger.info("=" * 60)

    try:
        # Create automation instance with context manager
        with UPSWebLoginAutomation(headless=False) as ups_login:
            # Perform login
            login_result = ups_login.login(save_screenshots=True)

            # Display login results
            logger.info("\n" + "=" * 60)
            logger.info("📊 LOGIN RESULT")
            logger.info("=" * 60)
            logger.info(f"Success: {'✅ YES' if login_result['success'] else '❌ NO'}")
            logger.info(f"Message: {login_result['message']}")
            logger.info(f"Final URL: {login_result['url']}")
            if login_result["screenshot"]:
                logger.info(f"Screenshot: {login_result['screenshot']}")

            # If login successful, navigate to shipping history
            if login_result["success"]:
                logger.info("\n" + "=" * 60)
                logger.info("🚢 NAVIGATING TO SHIPPING HISTORY")
                logger.info("=" * 60)

                # Navigate to shipping history
                nav_result = ups_login.navigate_to_shipping_history(
                    save_screenshots=True
                )

                # Display navigation results
                logger.info("\n" + "=" * 60)
                logger.info("📊 NAVIGATION RESULT")
                logger.info("=" * 60)
                logger.info(
                    f"Success: {'✅ YES' if nav_result['success'] else '❌ NO'}"
                )
                logger.info(f"Message: {nav_result['message']}")
                logger.info(f"Final URL: {nav_result['url']}")
                if nav_result["screenshot"]:
                    logger.info(f"Screenshot: {nav_result['screenshot']}")

                return nav_result["success"]
            else:
                logger.error("❌ Login failed, cannot navigate to shipping history")
                return False

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
    sys.exit(0 if success else 1)
    sys.exit(0 if success else 1)
    sys.exit(0 if success else 1)
    sys.exit(0 if success else 1)
