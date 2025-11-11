#!/usr/bin/env python3
"""
UPS Shipment Void Automation
=============================

This script automates the process of voiding UPS shipments that have only label-created status.

WORKFLOW:
1. Read tracking numbers from ups_label_only_filter.py output CSV
2. Map tracking numbers to login credentials using account number mapping:
   - Extract account_number from carrier_carrier_invoice_original_flat_ups table
   - Map using: industry_index_login.account_number = RIGHT(carrier_invoice.account_number, 6)
   - Query peerdb.industry_index_logins table for username/password
3. Automate browser to:
   - Log in to UPS website using retrieved credentials
   - Navigate to Billing menu
   - Click "View and Pay Bills" to access Billing Center

Usage:
    poetry run python src/ups_shipment_void_automation.py --csv <path_to_csv>

Configuration:
    Set in .env file:
    - UPS_WEB_LOGIN_URL: UPS login page URL
    - CLICKHOUSE_HOST: ClickHouse host for carrier invoice data
    - CLICKHOUSE_PORT: ClickHouse port
    - CLICKHOUSE_USERNAME: ClickHouse username
    - CLICKHOUSE_PASSWORD: ClickHouse password
    - CLICKHOUSE_DATABASE: ClickHouse database name
    - PEERDB_DUCKDB_PATH: Path to PeerDB DuckDB file with login credentials
    - OUTPUT_DIR: Output directory for screenshots and logs

Input:
    - CSV file from ups_label_only_filter.py with columns:
      tracking_number, account_number, status_description, status_code, status_type, date_processed

Output:
    - Screenshots of automation process
    - Log file with automation results
    - CSV file with void operation results

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import argparse
import csv
import glob
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import duckdb
from dotenv import load_dotenv
from playwright.sync_api import Browser, BrowserContext, Page
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
UPS_WEB_LOGIN_URL = os.getenv("UPS_WEB_LOGIN_URL", "https://www.ups.com/lasso/login")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "data/output")
PEERDB_DUCKDB_PATH = os.getenv(
    "PEERDB_DUCKDB_PATH", "peerdb_industry_index_logins.duckdb"
)
PEERDB_TABLE_NAME = "peerdb_data.industry_index_logins"

# Browser configuration
DEFAULT_TIMEOUT = 30000  # 30 seconds in milliseconds
DEFAULT_NAVIGATION_TIMEOUT = 60000  # 60 seconds for page loads

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)


def find_latest_ups_label_only_csv(output_dir: str = OUTPUT_DIR) -> Optional[str]:
    """
    Find the latest ups_label_only_tracking_range_*.csv file in the output directory

    Args:
        output_dir: Directory to search for CSV files

    Returns:
        Path to the latest CSV file, or None if not found
    """
    try:
        # Pattern to match ups_label_only_filter.py output files
        pattern = os.path.join(output_dir, "ups_label_only_tracking_range_*.csv")
        csv_files = glob.glob(pattern)

        if not csv_files:
            logger.error(
                f"❌ No ups_label_only_tracking_range_*.csv files found in {output_dir}"
            )
            logger.info(
                "💡 Run ups_label_only_filter.py first to generate tracking data"
            )
            return None

        # Sort by modification time (most recent first)
        latest_file = max(csv_files, key=os.path.getmtime)

        # Get file modification time for logging
        mod_time = datetime.fromtimestamp(os.path.getmtime(latest_file))
        logger.info(f"📁 Found latest CSV file: {latest_file}")
        logger.info(f"   Last modified: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")

        return latest_file

    except Exception as e:
        logger.error(f"❌ Error finding latest CSV file: {e}")
        return None


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
        if not os.path.exists(csv_path):
            logger.error(f"❌ CSV file not found: {csv_path}")
            return []

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                tracking_data.append(
                    {
                        "tracking_number": row["tracking_number"],
                        "account_number": row["account_number"],
                        "status_description": row.get("status_description", ""),
                        "status_code": row.get("status_code", ""),
                        "status_type": row.get("status_type", ""),
                    }
                )

        logger.info(
            f"✅ Loaded {len(tracking_data)} tracking numbers from CSV: {csv_path}"
        )

        if tracking_data:
            logger.info(f"📋 Sample tracking numbers:")
            for item in tracking_data[:3]:
                logger.info(
                    f"   📦 {item['tracking_number']} (Account: {item['account_number']})"
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

    Args:
        duckdb_path: Path to the PeerDB DuckDB file

    Returns:
        Dictionary mapping account_number (last 6 digits) to credentials:
        {
            "123456": {
                "username": "user@example.com",
                "password": "password123",
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
                    "status_description": item.get("status_description", ""),
                    "status_code": item.get("status_code", ""),
                    "status_type": item.get("status_type", ""),
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


class UPSVoidAutomation:
    """
    Automated UPS shipment void handler using Playwright browser automation

    This class manages the complete workflow for voiding UPS shipments:
    - Browser initialization and configuration
    - Navigation to login page
    - Credential entry and form submission
    - Navigation to Billing Center
    - Error handling and recovery
    - Screenshot capture for debugging
    """

    def __init__(
        self,
        headless: bool = True,
        output_dir: str = OUTPUT_DIR,
    ):
        """
        Initialize the UPS void automation

        Args:
            headless: Run browser in headless mode (default: True)
            output_dir: Directory for screenshots and logs
        """
        self.headless = headless
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Playwright objects (initialized in context manager)
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

        logger.info(f"🚀 UPS Void Automation initialized")
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

    def login(
        self, username: str, password: str, save_screenshots: bool = True
    ) -> Dict[str, Any]:
        """
        Perform login to UPS website

        Args:
            username: UPS username
            password: UPS password
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

            # STEP 1: Enter username
            logger.info("📝 Step 1: Entering username...")

            username_field = self.page.wait_for_selector(
                'input[name="username"]', timeout=10000
            )
            if not username_field:
                raise Exception("Could not find username input field")

            logger.info(f"✅ Found username field")
            username_field.fill(username)
            logger.info(f"   Username entered: {username[:10]}...")

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
            password_field.fill(password)
            logger.info("   Password entered: ********")

            if save_screenshots:
                result["screenshot"] = self.save_screenshot("04_password_entered")

            # Find and click submit button
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
                result["screenshot"] = self.save_screenshot("05_after_submit")

            # Check if login was successful
            current_url = self.page.url
            result["url"] = current_url

            # Login success indicators
            success_indicators = [
                "myups" in current_url.lower(),
                "dashboard" in current_url.lower(),
                "account" in current_url.lower(),
                current_url != UPS_WEB_LOGIN_URL,
            ]

            if any(success_indicators):
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

    def navigate_to_billing_center(
        self, save_screenshots: bool = True
    ) -> Dict[str, Any]:
        """
        Navigate to Billing Center after successful login

        After login, directly navigate to https://billing.ups.com/home

        Args:
            save_screenshots: Whether to save screenshots during navigation

        Returns:
            Dictionary containing navigation result with keys:
            - success: bool indicating if navigation was successful
            - message: str describing the result
            - url: str of final URL
            - screenshot: str path to screenshot (if saved)
        """
        result = {
            "success": False,
            "message": "",
            "url": "",
            "screenshot": "",
        }

        try:
            logger.info("💳 Navigating to Billing Center...")

            # Wait for page to be ready after login
            self.page.wait_for_load_state("domcontentloaded", timeout=10000)

            if save_screenshots:
                result["screenshot"] = self.save_screenshot("06_home_page")

            # Navigate directly to Billing Center
            logger.info("🌐 Navigating directly to: https://billing.ups.com/home")
            self.page.goto(
                "https://billing.ups.com/home",
                wait_until="domcontentloaded",
                timeout=30000,
            )

            # Wait for billing center page to load
            logger.info("⏳ Waiting for Billing Center page to load...")
            self.page.wait_for_load_state("networkidle", timeout=30000)

            if save_screenshots:
                result["screenshot"] = self.save_screenshot("08_billing_center_page")

            current_url = self.page.url
            result["url"] = current_url
            logger.info(f"✅ Billing Center page loaded! URL: {current_url}")

            # Keep browser open for 7 seconds to view the page
            logger.info("⏸️ Keeping browser open for 7 seconds...")
            self.page.wait_for_timeout(7000)

            # Check for success indicators
            success_indicators = [
                "billing" in current_url.lower(),
                "bill" in current_url.lower(),
            ]

            # Also check page content
            try:
                page_text = self.page.inner_text("body")
                content_indicators = [
                    "billing center" in page_text.lower(),
                    "view and pay bills" in page_text.lower(),
                    "billing" in page_text.lower(),
                ]
                success_indicators.extend(content_indicators)
            except:
                pass

            if any(success_indicators):
                result["success"] = True
                result["message"] = "Successfully navigated to Billing Center"
                logger.info(f"✅ Billing Center page loaded! URL: {current_url}")
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

    def search_tracking_number(
        self,
        tracking_number: str,
        save_screenshots: bool = True,
        submit_dispute: bool = False,
    ) -> Dict[str, Any]:
        """
        Search for a tracking number in the Billing Center

        Steps:
        1. Click on "Reporting & Search"
        2. Select "Tracking Number Detail" category
        3. Enter the tracking number

        Args:
            tracking_number: The tracking number to search for
            save_screenshots: Whether to save screenshots during search

        Returns:
            Dictionary containing search result with keys:
            - success: bool indicating if search was successful
            - message: str describing the result
            - screenshot: str path to screenshot (if saved)
        """
        result = {
            "success": False,
            "message": "",
            "screenshot": "",
        }

        try:
            logger.info(f"🔍 Searching for tracking number: {tracking_number}")

            # STEP 1: Click on "Reporting & Search"
            logger.info("🖱️ Step 1: Looking for 'Reporting & Search' section...")

            reporting_selectors = [
                'a:has-text("Reporting & Search")',
                'button:has-text("Reporting & Search")',
                'a:has-text("Reporting")',
                '[href*="reporting"]',
                'nav a:has-text("Reporting")',
            ]

            reporting_link = None
            for selector in reporting_selectors:
                try:
                    reporting_link = self.page.wait_for_selector(selector, timeout=5000)
                    if reporting_link and reporting_link.is_visible():
                        logger.info(
                            f"✅ Found 'Reporting & Search' section: {selector}"
                        )
                        break
                except:
                    continue

            if not reporting_link:
                raise Exception("Could not find 'Reporting & Search' section")

            # Click on Reporting & Search
            logger.info("🖱️ Clicking 'Reporting & Search'...")
            reporting_link.click()
            self.page.wait_for_timeout(2000)

            if save_screenshots:
                result["screenshot"] = self.save_screenshot(
                    "09_reporting_search_clicked"
                )

            # STEP 2: Select "Tracking Number Detail" radio button
            logger.info(
                "📋 Step 2: Looking for 'Tracking Number Detail' radio button..."
            )

            tracking_detail_selectors = [
                'input[type="radio"][value*="tracking"]',
                'input[type="radio"] + label:has-text("Tracking Number Detail")',
                'label:has-text("Tracking Number Detail")',
                "text=Tracking Number Detail",
            ]

            tracking_detail_radio = None
            for selector in tracking_detail_selectors:
                try:
                    tracking_detail_radio = self.page.wait_for_selector(
                        selector, timeout=5000
                    )
                    if tracking_detail_radio and tracking_detail_radio.is_visible():
                        logger.info(
                            f"✅ Found 'Tracking Number Detail' radio button: {selector}"
                        )
                        break
                except:
                    continue

            if not tracking_detail_radio:
                raise Exception("Could not find 'Tracking Number Detail' radio button")

            # Click on Tracking Number Detail radio button
            logger.info("🖱️ Clicking 'Tracking Number Detail' radio button...")
            tracking_detail_radio.click()
            self.page.wait_for_timeout(1000)

            if save_screenshots:
                result["screenshot"] = self.save_screenshot(
                    "10_tracking_detail_selected"
                )

            # STEP 3: Enter tracking number in the Tracking Number field
            logger.info("📝 Step 3: Looking for Tracking Number input field...")

            # Based on the screenshot, there's a dedicated "Tracking Number" field
            tracking_number_selectors = [
                'input[placeholder*="Tracking Number"]',
                'input[name*="trackingNumber"]',
                'input[id*="trackingNumber"]',
                'input[name*="tracking"]',
                'input[placeholder*="tracking"]',
                # Look for the input field near the "Tracking Number" label
                'label:has-text("Tracking Number") + input',
                'label:has-text("Tracking Number") ~ input',
            ]

            tracking_number_input = None
            for selector in tracking_number_selectors:
                try:
                    tracking_number_input = self.page.wait_for_selector(
                        selector, timeout=5000
                    )
                    if tracking_number_input and tracking_number_input.is_visible():
                        logger.info(f"✅ Found Tracking Number input: {selector}")
                        break
                except:
                    continue

            if not tracking_number_input:
                raise Exception("Could not find Tracking Number input field")

            # Enter tracking number in the Tracking Number field
            logger.info(
                f"📝 Entering tracking number in Tracking Number field: {tracking_number}"
            )
            tracking_number_input.fill(tracking_number)
            self.page.wait_for_timeout(1000)

            if save_screenshots:
                result["screenshot"] = self.save_screenshot(
                    "11_tracking_number_entered"
                )

            logger.info(f"✅ Successfully entered tracking number: {tracking_number}")

            # STEP 4: Click Submit button
            logger.info("🖱️ Step 4: Looking for Submit button...")

            submit_selectors = [
                'button:has-text("Submit")',
                'input[type="submit"]',
                'button[type="submit"]',
                'a:has-text("Submit")',
            ]

            submit_button = None
            for selector in submit_selectors:
                try:
                    submit_button = self.page.wait_for_selector(selector, timeout=5000)
                    if submit_button and submit_button.is_visible():
                        logger.info(f"✅ Found Submit button: {selector}")
                        break
                except:
                    continue

            if not submit_button:
                raise Exception("Could not find Submit button")

            # Click Submit button
            logger.info("🖱️ Clicking Submit button...")
            submit_button.click()

            # Wait for results to load
            logger.info("⏳ Waiting for search results to load...")
            self.page.wait_for_timeout(3000)

            if save_screenshots:
                result["screenshot"] = self.save_screenshot("12_search_results")

            # STEP 5: Click the invoice number link in the results table (opens new tab)
            logger.info(
                "🖱️ Step 5: Looking for Invoice Number hyperlink in results table..."
            )

            # Wait for the search results table to be visible
            self.page.wait_for_selector("table", timeout=10000)
            logger.info("✅ Search results table is visible")

            # Wait for the table to fully render
            self.page.wait_for_timeout(3000)

            # Click the Invoice Number cell (3rd column, index 2) using Playwright
            logger.info("🔍 Looking for Invoice Number cell to click...")

            # Get current number of pages before clicking
            current_pages = len(self.page.context.pages)
            logger.info(f"📊 Current number of pages/tabs: {current_pages}")

            # Find and click the Invoice Number cell using Playwright selector
            try:
                # The Invoice Number is in the 3rd column (td:nth-child(3))
                invoice_cell = self.page.locator(
                    "table tbody tr:first-child td:nth-child(3)"
                )
                invoice_text = invoice_cell.text_content()
                logger.info(f"✅ Found Invoice Number cell: {invoice_text}")
                logger.info("🖱️ Clicking Invoice Number cell...")

                # Click the cell
                invoice_cell.click()

                click_result = {"success": True, "text": invoice_text}
            except Exception as e:
                logger.error(f"❌ Failed to find/click Invoice Number cell: {str(e)}")
                click_result = {"success": False, "error": str(e)}

            logger.info(f"🔍 Click result: {click_result}")

            if not click_result.get("success"):
                raise Exception(
                    f"Could not find or click Invoice Number link: {click_result.get('error')}"
                )

            logger.info(f"✅ Clicked Invoice Number link: {click_result.get('text')}")
            logger.info("🖱️ Waiting for new tab to open...")

            # Wait a bit for potential new tab to open
            self.page.wait_for_timeout(3000)

            # Check if a new tab was opened
            new_pages = len(self.page.context.pages)
            logger.info(f"📊 Number of pages/tabs after click: {new_pages}")

            if new_pages > current_pages:
                # A new tab was opened, switch to it
                logger.info("✅ New tab detected, switching to it...")
                new_page = self.page.context.pages[-1]  # Get the last (newest) page
                self.page = new_page
                logger.info(f"✅ Switched to new tab: {new_page.url}")

                # Wait for the new page to load
                logger.info("⏳ Waiting for invoice details page to load in new tab...")
                self.page.wait_for_load_state("domcontentloaded", timeout=10000)
            else:
                # No new tab, the page navigated in the same tab
                logger.info("ℹ️ No new tab opened, page navigated in same tab")
                logger.info("⏳ Waiting for invoice details page to load...")
                self.page.wait_for_load_state("domcontentloaded", timeout=10000)

            if save_screenshots:
                result["screenshot"] = self.save_screenshot("13_invoice_details")

            logger.info(
                f"✅ Successfully navigated to invoice details for tracking number: {tracking_number}"
            )
            logger.info(f"📄 Invoice details page URL: {self.page.url}")

            # Keep browser open for 7 seconds to observe the invoice details page
            logger.info("⏸️ Keeping browser open for 7 seconds...")
            self.page.wait_for_timeout(7000)
            logger.info(f"✅ Invoice details page loaded! URL: {self.page.url}")

            # Step 6: Search for tracking number in the "Search Table" field
            logger.info(
                f"🔍 Step 6: Searching for tracking number in Search Table: {tracking_number}"
            )
            try:
                # Look for the "Search Table" input field
                logger.info("📝 Looking for 'Search Table' input field...")
                search_table_input = self.page.locator(
                    'input[placeholder*="Search"], input[type="search"], input[aria-label*="Search"]'
                ).first

                if search_table_input.is_visible(timeout=5000):
                    logger.info("✅ Found 'Search Table' input field")

                    # Clear any existing text and enter the tracking number
                    logger.info(f"📝 Entering tracking number: {tracking_number}")
                    search_table_input.click()
                    search_table_input.fill("")  # Clear first
                    search_table_input.fill(tracking_number)

                    if save_screenshots:
                        self.save_screenshot("14_search_table_entered")

                    logger.info(
                        f"✅ Successfully entered tracking number in Search Table: {tracking_number}"
                    )

                    # Wait a moment for the table to filter
                    logger.info("⏳ Waiting for table to filter results...")
                    self.page.wait_for_timeout(2000)

                    if save_screenshots:
                        self.save_screenshot("15_search_table_filtered")

                    logger.info("✅ Table filtered successfully")

                    # Step 7: Click the three-dot menu in the Action column
                    logger.info(
                        "🖱️ Step 7: Looking for three-dot menu in Action column..."
                    )
                    try:
                        # Look for the three-dot button (vertical ellipsis) in the Action column
                        # The button is in the last column of the filtered table row
                        three_dot_button = self.page.locator(
                            "table tbody tr button, table tbody tr td:last-child button"
                        ).first

                        if three_dot_button.is_visible(timeout=5000):
                            logger.info(
                                "✅ Found three-dot menu button in Action column"
                            )
                            logger.info("🖱️ Clicking three-dot menu...")
                            three_dot_button.click()

                            # Wait for menu to appear
                            self.page.wait_for_timeout(1000)

                            if save_screenshots:
                                self.save_screenshot("16_three_dot_menu_opened")

                            logger.info("✅ Three-dot menu opened")

                            # Step 8: Click "Dispute" option
                            logger.info("🖱️ Step 8: Looking for 'Dispute' option...")
                            dispute_option = self.page.locator('text="Dispute"').first

                            if dispute_option.is_visible(timeout=5000):
                                logger.info("✅ Found 'Dispute' option")
                                logger.info("🖱️ Clicking 'Dispute'...")
                                dispute_option.click()

                                # Wait for dispute dialog to appear
                                self.page.wait_for_timeout(2000)

                                if save_screenshots:
                                    self.save_screenshot("17_dispute_clicked")

                                logger.info("✅ Successfully clicked 'Dispute' option")

                                # Step 9: Select "Void Credits" from Reason dropdown
                                logger.info("🖱️ Step 9: Looking for Reason dropdown...")
                                try:
                                    # Look for the Dispute modal dialog first
                                    dispute_modal = self.page.locator(
                                        '[role="dialog"][aria-label="Dispute"], #disputes-modal'
                                    ).first

                                    if dispute_modal.is_visible(timeout=5000):
                                        logger.info("✅ Found Dispute modal")

                                        # Look for the dropdown INSIDE the modal
                                        reason_dropdown = dispute_modal.locator(
                                            "select"
                                        ).first

                                        if reason_dropdown.is_visible(timeout=5000):
                                            logger.info("✅ Found Reason dropdown")
                                            logger.info(
                                                "🖱️ Selecting 'Void Credits' from dropdown..."
                                            )

                                            # Use select_option to choose "Void Credits"
                                            reason_dropdown.select_option(
                                                label="Void Credits"
                                            )

                                            # Wait for selection to register
                                            self.page.wait_for_timeout(1000)

                                            if save_screenshots:
                                                self.save_screenshot(
                                                    "18_void_credits_selected"
                                                )

                                            logger.info(
                                                "✅ Successfully selected 'Void Credits'"
                                            )

                                            # Step 9.5: Select "Package" from Dispute Level dropdown
                                            logger.info(
                                                "🖱️ Step 9.5: Looking for Dispute Level dropdown..."
                                            )
                                            # Look for the second select element (Dispute Level)
                                            dispute_level_dropdown = (
                                                dispute_modal.locator("select").nth(1)
                                            )

                                            if dispute_level_dropdown.is_visible(
                                                timeout=5000
                                            ):
                                                logger.info(
                                                    "✅ Found Dispute Level dropdown"
                                                )
                                                logger.info(
                                                    "🖱️ Selecting 'Package' from Dispute Level dropdown..."
                                                )

                                                # Use select_option to choose "Package"
                                                dispute_level_dropdown.select_option(
                                                    label="Package"
                                                )

                                                # Wait for selection to register
                                                self.page.wait_for_timeout(1000)

                                                if save_screenshots:
                                                    self.save_screenshot(
                                                        "18b_package_level_selected"
                                                    )

                                                logger.info(
                                                    "✅ Successfully selected 'Package' for Dispute Level"
                                                )
                                            else:
                                                logger.warning(
                                                    "⚠️ Dispute Level dropdown not found"
                                                )
                                                if save_screenshots:
                                                    self.save_screenshot(
                                                        "error_dispute_level_not_found"
                                                    )

                                            # Step 10: Submit or keep form open based on parameter
                                            if submit_dispute:
                                                logger.info(
                                                    "🖱️ Step 10: Looking for Submit button..."
                                                )
                                                submit_button = dispute_modal.locator(
                                                    'button:has-text("Submit")'
                                                ).first

                                                if submit_button.is_visible(
                                                    timeout=5000
                                                ):
                                                    logger.info(
                                                        "✅ Found Submit button"
                                                    )
                                                    logger.info(
                                                        "🖱️ Clicking Submit button..."
                                                    )
                                                    submit_button.click()

                                                    # Wait for submission to process
                                                    self.page.wait_for_timeout(3000)

                                                    if save_screenshots:
                                                        self.save_screenshot(
                                                            "19_dispute_submitted"
                                                        )

                                                    logger.info(
                                                        "✅ Successfully submitted dispute with Void Credits"
                                                    )
                                                else:
                                                    logger.warning(
                                                        "⚠️ Submit button not found"
                                                    )
                                                    if save_screenshots:
                                                        self.save_screenshot(
                                                            "error_submit_not_found"
                                                        )
                                            else:
                                                logger.info(
                                                    "⏸️ Step 10: Dispute form filled, keeping browser open..."
                                                )
                                                logger.info(
                                                    "✅ Successfully filled dispute form with Void Credits and Package level"
                                                )

                                                # Keep browser open for 10 seconds to review
                                                logger.info(
                                                    "⏸️ Keeping browser open for 10 seconds to review..."
                                                )
                                                self.page.wait_for_timeout(10000)

                                                if save_screenshots:
                                                    self.save_screenshot(
                                                        "19_dispute_form_ready"
                                                    )

                                                logger.info(
                                                    "✅ Dispute form ready (NOT submitted)"
                                                )
                                        else:
                                            logger.warning(
                                                "⚠️ Reason dropdown not found"
                                            )
                                            if save_screenshots:
                                                self.save_screenshot(
                                                    "error_reason_dropdown_not_found"
                                                )
                                    else:
                                        logger.warning("⚠️ Dispute modal not found")
                                        if save_screenshots:
                                            self.save_screenshot(
                                                "error_dispute_modal_not_found"
                                            )

                                except Exception as e:
                                    logger.error(
                                        f"❌ Failed to select Void Credits or submit: {str(e)}"
                                    )
                                    if save_screenshots:
                                        self.save_screenshot(
                                            "error_void_credits_submit"
                                        )

                            else:
                                logger.warning("⚠️ 'Dispute' option not found in menu")
                                logger.info("⏭️ Skipping to next tracking number...")
                                if save_screenshots:
                                    self.save_screenshot("error_dispute_not_found")
                        else:
                            logger.warning("⚠️ Three-dot menu button not found")
                            if save_screenshots:
                                self.save_screenshot("error_three_dot_not_found")

                    except Exception as e:
                        logger.error(
                            f"❌ Failed to click three-dot menu or Dispute: {str(e)}"
                        )
                        if save_screenshots:
                            self.save_screenshot("error_three_dot_dispute")

                else:
                    logger.warning("⚠️ Search Table input field not found")

            except Exception as e:
                logger.error(f"❌ Failed to search in Search Table: {str(e)}")
                if save_screenshots:
                    self.save_screenshot("error_search_table")

            result["success"] = True
            result["message"] = (
                f"Successfully searched for tracking number: {tracking_number}"
            )

        except Exception as e:
            result["message"] = f"Search failed: {str(e)}"
            logger.error(f"❌ {result['message']}")
            if save_screenshots:
                result["screenshot"] = self.save_screenshot("error_search_exception")

        return result


def process_shipments(
    mapped_data: List[Dict[str, Any]],
    headless: bool = True,
    save_screenshots: bool = True,
    submit_dispute: bool = False,
) -> List[Dict[str, Any]]:
    """
    Process shipments by logging in with credentials and navigating to Billing Center

    Args:
        mapped_data: List of tracking numbers with credentials
        headless: Run browser in headless mode
        save_screenshots: Save screenshots during automation
        submit_dispute: Submit the dispute form (default: False)

    Returns:
        List of results for each shipment processed
    """
    results = []

    # Group tracking numbers by account (username)
    accounts = {}
    for item in mapped_data:
        username = item["username"]
        if username not in accounts:
            accounts[username] = {
                "username": username,
                "password": item["password"],
                "account_number": item["account_number_key"],
                "tracking_numbers": [],
            }
        accounts[username]["tracking_numbers"].append(item)

    logger.info(
        f"📊 Processing {len(mapped_data)} tracking numbers across {len(accounts)} accounts"
    )

    # Process each account
    for idx, (username, account_data) in enumerate(accounts.items(), 1):
        logger.info(f"\n{'='*60}")
        logger.info(f"🔄 Processing Account {idx}/{len(accounts)}")
        logger.info(f"   Username: {username[:20]}...")
        logger.info(f"   Account: {account_data['account_number']}")
        logger.info(f"   Tracking numbers: {len(account_data['tracking_numbers'])}")
        logger.info(f"{'='*60}")

        try:
            with UPSVoidAutomation(headless=headless) as automation:
                # Login
                login_result = automation.login(
                    username=account_data["username"],
                    password=account_data["password"],
                    save_screenshots=save_screenshots,
                )

                if not login_result["success"]:
                    logger.error(
                        f"❌ Login failed for account {account_data['account_number']}"
                    )
                    for tracking_item in account_data["tracking_numbers"]:
                        results.append(
                            {
                                "tracking_number": tracking_item["tracking_number"],
                                "account_number": tracking_item["full_account_number"],
                                "username": username,
                                "login_success": False,
                                "billing_center_success": False,
                                "error": login_result["message"],
                            }
                        )
                    continue

                logger.info(
                    f"✅ Login successful for account {account_data['account_number']}"
                )

                # Navigate to Billing Center
                billing_result = automation.navigate_to_billing_center(
                    save_screenshots=save_screenshots
                )

                if billing_result["success"]:
                    logger.info(f"✅ Successfully navigated to Billing Center")
                else:
                    logger.warning(
                        f"⚠️ Failed to navigate to Billing Center: {billing_result['message']}"
                    )

                # Search for each tracking number in this account
                for tracking_item in account_data["tracking_numbers"]:
                    search_result = {"success": False, "message": ""}

                    if billing_result["success"]:
                        # Search for this tracking number
                        search_result = automation.search_tracking_number(
                            tracking_number=tracking_item["tracking_number"],
                            save_screenshots=save_screenshots,
                            submit_dispute=submit_dispute,
                        )

                        if search_result["success"]:
                            logger.info(
                                f"✅ Successfully searched for tracking number: {tracking_item['tracking_number']}"
                            )
                        else:
                            logger.warning(
                                f"⚠️ Failed to search for tracking number: {search_result['message']}"
                            )

                    # Record results for this tracking number
                    results.append(
                        {
                            "tracking_number": tracking_item["tracking_number"],
                            "account_number": tracking_item["full_account_number"],
                            "username": username,
                            "login_success": login_result["success"],
                            "billing_center_success": billing_result["success"],
                            "billing_center_url": billing_result.get("url", ""),
                            "search_success": search_result["success"],
                            "error": (
                                search_result.get("message", "")
                                if not search_result["success"]
                                else (
                                    billing_result.get("message", "")
                                    if not billing_result["success"]
                                    else ""
                                )
                            ),
                        }
                    )

        except Exception as e:
            logger.error(
                f"❌ Error processing account {account_data['account_number']}: {e}"
            )
            for tracking_item in account_data["tracking_numbers"]:
                results.append(
                    {
                        "tracking_number": tracking_item["tracking_number"],
                        "account_number": tracking_item["full_account_number"],
                        "username": username,
                        "login_success": False,
                        "billing_center_success": False,
                        "error": str(e),
                    }
                )

    return results


def save_results_to_csv(
    results: List[Dict[str, Any]], output_dir: str = OUTPUT_DIR
) -> str:
    """
    Save automation results to CSV file

    Args:
        results: List of result dictionaries
        output_dir: Output directory for CSV file

    Returns:
        Path to saved CSV file
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"ups_void_automation_results_{timestamp}.csv"
    filepath = os.path.join(output_dir, filename)

    try:
        with open(filepath, "w", encoding="utf-8", newline="") as f:
            if results:
                fieldnames = results[0].keys()
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(results)

        logger.info(f"💾 Results saved to: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"❌ Failed to save results to CSV: {e}")
        return ""


def print_summary(results: List[Dict[str, Any]]):
    """Print summary of automation results"""
    logger.info("\n" + "=" * 60)
    logger.info("📊 UPS VOID AUTOMATION SUMMARY")
    logger.info("=" * 60)

    total = len(results)
    login_success = sum(1 for r in results if r.get("login_success", False))
    billing_success = sum(1 for r in results if r.get("billing_center_success", False))
    errors = sum(1 for r in results if r.get("error", ""))

    logger.info(f"📦 Total tracking numbers: {total}")
    logger.info(f"✅ Successful logins: {login_success}")
    logger.info(f"💳 Reached Billing Center: {billing_success}")
    logger.info(f"❌ Errors: {errors}")

    if total > 0:
        success_rate = (billing_success / total) * 100
        logger.info(f"📈 Success rate: {success_rate:.1f}%")


def main():
    """Main function to run the UPS void automation"""
    parser = argparse.ArgumentParser(
        description="UPS Shipment Void Automation - Navigate to Billing Center for label-only shipments"
    )
    parser.add_argument(
        "--csv",
        type=str,
        required=False,
        help="Path to CSV file from ups_label_only_filter.py (default: auto-detect latest file)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=True,
        help="Run browser in headless mode (default: True)",
    )
    parser.add_argument(
        "--headed",
        action="store_true",
        help="Run browser in headed mode (visible browser)",
    )
    parser.add_argument(
        "--no-screenshots", action="store_true", help="Disable screenshot capture"
    )
    parser.add_argument(
        "--submit",
        action="store_true",
        help="Submit the dispute form (default: False, form will be filled but not submitted)",
    )

    args = parser.parse_args()

    # Determine headless mode
    headless = not args.headed if args.headed else args.headless
    save_screenshots = not args.no_screenshots
    submit_dispute = args.submit

    logger.info("=" * 60)
    logger.info("🚀 UPS SHIPMENT VOID AUTOMATION")
    logger.info("=" * 60)

    # Determine which CSV file to use
    csv_path = args.csv
    if not csv_path:
        logger.info("🔍 No CSV file specified, searching for latest file...")
        csv_path = find_latest_ups_label_only_csv()
        if not csv_path:
            logger.error("❌ Could not find CSV file. Exiting.")
            return 1
    else:
        logger.info(f"📁 Using specified CSV file: {csv_path}")

    logger.info(f"📁 Input CSV: {csv_path}")
    logger.info(f"🌐 Headless mode: {headless}")
    logger.info(f"📸 Screenshots: {save_screenshots}")
    logger.info("=" * 60)

    # Step 1: Load tracking numbers from CSV
    logger.info("\n📊 Step 1: Loading tracking numbers from CSV...")
    tracking_data = load_tracking_numbers_from_csv(csv_path)

    if not tracking_data:
        logger.error("❌ No tracking numbers found. Exiting.")
        return 1

    # Step 2: Load login credentials from PeerDB
    logger.info("\n🔑 Step 2: Loading login credentials from PeerDB...")
    credentials_map = load_login_credentials_from_peerdb()

    if not credentials_map:
        logger.error("❌ No credentials found. Exiting.")
        return 1

    # Step 3: Map tracking numbers to credentials
    logger.info("\n🔗 Step 3: Mapping tracking numbers to credentials...")
    mapped_data = map_tracking_to_credentials(tracking_data, credentials_map)

    if not mapped_data:
        logger.error("❌ No tracking numbers could be mapped to credentials. Exiting.")
        return 1

    # Step 4: Process shipments
    logger.info("\n🔄 Step 4: Processing shipments...")
    results = process_shipments(
        mapped_data,
        headless=headless,
        save_screenshots=save_screenshots,
        submit_dispute=submit_dispute,
    )

    # Step 5: Save results
    logger.info("\n💾 Step 5: Saving results...")
    csv_path = save_results_to_csv(results)

    # Print summary
    print_summary(results)

    logger.info(f"\n📁 Results saved to: {csv_path}")
    logger.info("\n✅ UPS Void Automation completed!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
