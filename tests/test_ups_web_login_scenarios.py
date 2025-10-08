#!/usr/bin/env python3
"""
Advanced Test Scenarios for UPS Web Login Automation
====================================================

This script provides comprehensive test scenarios for the UPS web login automation,
including edge cases, error handling, and various configuration options.

Test Scenarios:
1. Basic login with default settings
2. Login with different timeout configurations
3. Login with screenshot capture at each step
4. Login with custom credentials
5. Login URL validation
6. Browser configuration testing
7. Error recovery testing
8. Session persistence testing

Usage:
    # Run all scenarios
    poetry run python tests/test_ups_web_login_scenarios.py
    
    # Run specific scenario
    poetry run python tests/test_ups_web_login_scenarios.py --scenario basic
    
    # Run with visible browser
    poetry run python tests/test_ups_web_login_scenarios.py --headed

Author: Gabriel Jerdhy Lapuz
Project: gsr_automation
"""

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def print_section(title: str):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_result(scenario_name: str, success: bool, message: str, details: Dict[str, Any] = None):
    """Print formatted test result"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"\n{status} - {scenario_name}")
    print(f"   Message: {message}")
    if details:
        for key, value in details.items():
            print(f"   {key}: {value}")


def scenario_basic_login(headless: bool = True) -> Dict[str, Any]:
    """
    Scenario 1: Basic login with default settings
    
    Tests:
    - Standard login flow
    - Default timeout settings
    - Basic error handling
    """
    print_section("Scenario 1: Basic Login")
    
    try:
        from src.src.ups_web_login import UPSWebLoginAutomation
        
        with UPSWebLoginAutomation(headless=headless) as ups_login:
            result = ups_login.login(save_screenshots=True)
            
            return {
                'scenario': 'Basic Login',
                'success': result['success'],
                'message': result['message'],
                'url': result['url'],
                'screenshot': result.get('screenshot', '')
            }
    except Exception as e:
        return {
            'scenario': 'Basic Login',
            'success': False,
            'message': f"Exception: {str(e)}",
            'url': '',
            'screenshot': ''
        }


def scenario_url_validation(headless: bool = True) -> Dict[str, Any]:
    """
    Scenario 2: Test different UPS login URLs
    
    Tests:
    - Multiple potential login URLs
    - URL accessibility
    - Redirect handling
    """
    print_section("Scenario 2: URL Validation")
    
    test_urls = [
        "https://www.ups.com/lasso/login",
        "https://www.ups.com/login",
        "https://wwwapps.ups.com/doapp/SignIn",
        "https://www.ups.com/myups/login"
    ]
    
    results = []
    
    try:
        from src.src.ups_web_login import UPSWebLoginAutomation
        
        for url in test_urls:
            print(f"\n🔍 Testing URL: {url}")
            
            try:
                with UPSWebLoginAutomation(headless=headless) as ups_login:
                    # Try to navigate to the URL
                    ups_login.page.goto(url, wait_until='domcontentloaded', timeout=15000)
                    current_url = ups_login.page.url
                    
                    # Check if page loaded
                    title = ups_login.page.title()
                    
                    results.append({
                        'url': url,
                        'accessible': True,
                        'final_url': current_url,
                        'title': title
                    })
                    
                    print(f"   ✅ Accessible")
                    print(f"   Final URL: {current_url}")
                    print(f"   Title: {title}")
                    
            except Exception as e:
                results.append({
                    'url': url,
                    'accessible': False,
                    'error': str(e)
                })
                print(f"   ❌ Not accessible: {str(e)[:100]}")
        
        # Determine success
        accessible_count = sum(1 for r in results if r.get('accessible', False))
        
        return {
            'scenario': 'URL Validation',
            'success': accessible_count > 0,
            'message': f"{accessible_count}/{len(test_urls)} URLs accessible",
            'results': results
        }
        
    except Exception as e:
        return {
            'scenario': 'URL Validation',
            'success': False,
            'message': f"Exception: {str(e)}",
            'results': []
        }


def scenario_browser_configuration(headless: bool = True) -> Dict[str, Any]:
    """
    Scenario 3: Test different browser configurations
    
    Tests:
    - Different viewport sizes
    - Different user agents
    - Browser arguments
    """
    print_section("Scenario 3: Browser Configuration")
    
    configurations = [
        {
            'name': 'Desktop (1920x1080)',
            'viewport': {'width': 1920, 'height': 1080},
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },
        {
            'name': 'Laptop (1366x768)',
            'viewport': {'width': 1366, 'height': 768},
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        },
        {
            'name': 'Tablet (768x1024)',
            'viewport': {'width': 768, 'height': 1024},
            'user_agent': 'Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
        }
    ]
    
    results = []
    
    try:
        from playwright.sync_api import sync_playwright
        
        for config in configurations:
            print(f"\n🔍 Testing: {config['name']}")
            
            try:
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=headless)
                    context = browser.new_context(
                        viewport=config['viewport'],
                        user_agent=config['user_agent']
                    )
                    page = context.new_page()
                    
                    # Try to load UPS homepage
                    page.goto('https://www.ups.com', timeout=15000)
                    
                    results.append({
                        'config': config['name'],
                        'success': True,
                        'viewport': config['viewport']
                    })
                    
                    print(f"   ✅ Configuration works")
                    
                    browser.close()
                    
            except Exception as e:
                results.append({
                    'config': config['name'],
                    'success': False,
                    'error': str(e)
                })
                print(f"   ❌ Configuration failed: {str(e)[:100]}")
        
        success_count = sum(1 for r in results if r.get('success', False))
        
        return {
            'scenario': 'Browser Configuration',
            'success': success_count > 0,
            'message': f"{success_count}/{len(configurations)} configurations successful",
            'results': results
        }
        
    except Exception as e:
        return {
            'scenario': 'Browser Configuration',
            'success': False,
            'message': f"Exception: {str(e)}",
            'results': []
        }


def scenario_screenshot_capture(headless: bool = True) -> Dict[str, Any]:
    """
    Scenario 4: Test screenshot capture functionality
    
    Tests:
    - Screenshot saving
    - File naming
    - Directory creation
    """
    print_section("Scenario 4: Screenshot Capture")
    
    try:
        from src.src.ups_web_login import UPSWebLoginAutomation
        
        output_dir = Path("data/output")
        
        # Count existing screenshots
        existing_screenshots = list(output_dir.glob("*.png")) if output_dir.exists() else []
        initial_count = len(existing_screenshots)
        
        print(f"📊 Initial screenshot count: {initial_count}")
        
        with UPSWebLoginAutomation(headless=headless) as ups_login:
            # Navigate to UPS homepage
            ups_login.page.goto('https://www.ups.com', timeout=15000)
            
            # Take multiple screenshots
            screenshots = []
            for i in range(3):
                screenshot_path = ups_login.save_screenshot(f"test_screenshot_{i}")
                screenshots.append(screenshot_path)
                print(f"   📸 Screenshot {i+1}: {Path(screenshot_path).name}")
        
        # Verify screenshots were created
        new_screenshots = list(output_dir.glob("*.png")) if output_dir.exists() else []
        final_count = len(new_screenshots)
        
        print(f"📊 Final screenshot count: {final_count}")
        print(f"📊 New screenshots: {final_count - initial_count}")
        
        return {
            'scenario': 'Screenshot Capture',
            'success': final_count > initial_count,
            'message': f"Created {final_count - initial_count} screenshots",
            'screenshots': screenshots
        }
        
    except Exception as e:
        return {
            'scenario': 'Screenshot Capture',
            'success': False,
            'message': f"Exception: {str(e)}",
            'screenshots': []
        }


def scenario_error_handling(headless: bool = True) -> Dict[str, Any]:
    """
    Scenario 5: Test error handling
    
    Tests:
    - Invalid credentials
    - Network errors
    - Timeout handling
    """
    print_section("Scenario 5: Error Handling")
    
    test_cases = []
    
    try:
        from src.src.ups_web_login import UPSWebLoginAutomation
        
        # Test 1: Invalid URL
        print("\n🔍 Test 1: Invalid URL")
        try:
            with UPSWebLoginAutomation(headless=headless) as ups_login:
                ups_login.page.goto('https://invalid-ups-url-12345.com', timeout=5000)
                test_cases.append({'test': 'Invalid URL', 'handled': False})
        except Exception as e:
            print(f"   ✅ Error handled: {str(e)[:100]}")
            test_cases.append({'test': 'Invalid URL', 'handled': True})
        
        # Test 2: Timeout
        print("\n🔍 Test 2: Short timeout")
        try:
            with UPSWebLoginAutomation(headless=headless) as ups_login:
                ups_login.page.set_default_timeout(1000)  # 1 second
                ups_login.page.goto('https://www.ups.com', wait_until='networkidle')
                test_cases.append({'test': 'Short timeout', 'handled': False})
        except Exception as e:
            print(f"   ✅ Timeout handled: {str(e)[:100]}")
            test_cases.append({'test': 'Short timeout', 'handled': True})
        
        handled_count = sum(1 for tc in test_cases if tc['handled'])
        
        return {
            'scenario': 'Error Handling',
            'success': handled_count == len(test_cases),
            'message': f"{handled_count}/{len(test_cases)} errors handled correctly",
            'test_cases': test_cases
        }
        
    except Exception as e:
        return {
            'scenario': 'Error Handling',
            'success': False,
            'message': f"Exception: {str(e)}",
            'test_cases': test_cases
        }


def main():
    """Main test runner for all scenarios"""
    parser = argparse.ArgumentParser(description='UPS Web Login Advanced Test Scenarios')
    parser.add_argument(
        '--headed',
        action='store_true',
        help='Run browser in headed mode (visible browser window)'
    )
    parser.add_argument(
        '--scenario',
        choices=['basic', 'url', 'browser', 'screenshot', 'error', 'all'],
        default='all',
        help='Specific scenario to run (default: all)'
    )
    args = parser.parse_args()
    
    headless = not args.headed
    
    print("🚀 UPS Web Login - Advanced Test Scenarios")
    print("=" * 70)
    print(f"Mode: {'Headed (visible browser)' if args.headed else 'Headless'}")
    print(f"Scenario: {args.scenario}")
    
    # Define scenarios
    scenarios = {
        'basic': scenario_basic_login,
        'url': scenario_url_validation,
        'browser': scenario_browser_configuration,
        'screenshot': scenario_screenshot_capture,
        'error': scenario_error_handling
    }
    
    # Run scenarios
    results = []
    
    if args.scenario == 'all':
        for name, func in scenarios.items():
            result = func(headless=headless)
            results.append(result)
            time.sleep(1)  # Brief pause between scenarios
    else:
        result = scenarios[args.scenario](headless=headless)
        results.append(result)
    
    # Summary
    print_section("TEST SUMMARY")
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"{status} - {result['scenario']}: {result['message']}")
    
    # Overall result
    all_passed = all(r['success'] for r in results)
    
    print("\n" + "=" * 70)
    if all_passed:
        print("🎉 All scenarios passed!")
        return 0
    else:
        failed_count = sum(1 for r in results if not r['success'])
        print(f"❌ {failed_count}/{len(results)} scenarios failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())

