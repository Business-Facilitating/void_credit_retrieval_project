#!/usr/bin/env python3
"""
UPS Web Login Automation - Headless Mode for Linux/Cloud Deployment

This version is optimized for headless environments like Google Cloud VMs.
It uses advanced anti-detection techniques to work in headless mode.

Note: This may not work as reliably as headed mode due to UPS anti-bot measures.
For production, consider using Xvfb (virtual display) instead.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.src.ups_web_login import UPSWebLoginAutomation
from playwright.sync_api import sync_playwright
import logging

logger = logging.getLogger(__name__)


class UPSWebLoginHeadless(UPSWebLoginAutomation):
    """
    Extended version with headless mode optimizations for Linux deployment
    """
    
    def __init__(self, headless: bool = True, output_dir: str = "data/output"):
        """
        Initialize UPS Web Login Automation for headless mode
        
        Args:
            headless: Whether to run in headless mode (default: True for Linux)
            output_dir: Directory to save screenshots and outputs
        """
        # Force headless mode for cloud deployment
        super().__init__(headless=headless, output_dir=output_dir)
    
    def _start_browser(self):
        """
        Start browser with enhanced anti-detection for headless mode
        """
        logger.info("🌐 Starting browser (headless mode with anti-detection)...")
        
        self.playwright = sync_playwright().start()
        
        # Enhanced browser arguments for headless mode
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--disable-setuid-sandbox',
            '--no-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-gpu',
            '--window-size=1920,1080',
        ]
        
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=browser_args
        )
        
        # Create context with realistic settings
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['geolocation'],
            geolocation={'latitude': 40.7128, 'longitude': -74.0060},  # New York
            color_scheme='light',
            extra_http_headers={
                'Accept-Language': 'en-US,en;q=0.9',
            }
        )
        
        # Add anti-detection scripts
        self.context.add_init_script("""
            // Override the navigator.webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // Override the navigator.plugins property
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
            
            // Override the navigator.languages property
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en']
            });
            
            // Add chrome property
            window.chrome = {
                runtime: {}
            };
            
            // Override permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        self.page = self.context.new_page()
        
        # Set default timeouts
        self.page.set_default_timeout(self.default_timeout)
        self.page.set_default_navigation_timeout(self.navigation_timeout)
        
        logger.info("✅ Browser started successfully (headless mode)")


def main():
    """Main function for headless deployment"""
    logger.info("=" * 60)
    logger.info("🚀 UPS Web Login Automation (Headless Mode)")
    logger.info("=" * 60)
    logger.info("⚠️ Note: Headless mode may not work due to UPS anti-bot measures")
    logger.info("   Consider using Xvfb for better reliability")
    logger.info("=" * 60)
    
    try:
        # Try headless mode first
        with UPSWebLoginHeadless(headless=True) as ups_login:
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
                
                nav_result = ups_login.navigate_to_shipping_history(save_screenshots=True)
                
                logger.info("\n" + "=" * 60)
                logger.info("📊 NAVIGATION RESULT")
                logger.info("=" * 60)
                logger.info(f"Success: {'✅ YES' if nav_result['success'] else '❌ NO'}")
                logger.info(f"Message: {nav_result['message']}")
                logger.info(f"Final URL: {nav_result['url']}")
                if nav_result["screenshot"]:
                    logger.info(f"Screenshot: {nav_result['screenshot']}")
                
                return nav_result["success"]
            else:
                logger.error("❌ Login failed")
                return False
    
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

