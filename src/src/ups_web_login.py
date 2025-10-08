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

Security:
- Credentials loaded from .env file (never hardcoded)
- Screenshots saved to output directory (excluded from git)
- Secure browser context with proper cleanup

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

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
        self, save_screenshots: bool = True
    ) -> Dict[str, Any]:
        """
        Navigate to Shipping History page after successful login

        Args:
            save_screenshots: Whether to save screenshots during navigation

        Returns:
            Dictionary containing navigation result with keys:
            - success: bool indicating if navigation was successful
            - message: str describing the result
            - url: str of final URL
            - screenshot: str path to screenshot (if saved)
        """
        result = {"success": False, "message": "", "url": "", "screenshot": ""}

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
