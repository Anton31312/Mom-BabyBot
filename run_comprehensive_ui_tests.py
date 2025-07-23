#!/usr/bin/env python
"""
Script to run comprehensive UI tests for the application.

This script:
1. Runs UI tests across different browsers and screen sizes
2. Generates screenshots for visual comparison
3. Checks for accessibility issues
4. Generates a comprehensive report
"""

import os
import sys
import time
import json
import argparse
import subprocess
from datetime import datetime
from pathlib import Path

# Check if required packages are installed
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    import axe_selenium_python
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", 
                          "selenium", "webdriver-manager", "axe-selenium-python"])
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.webdriver.firefox.options import Options as FirefoxOptions
    import axe_selenium_python

# Import webdriver managers
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager

# Set paths
BASE_DIR = Path(__file__).resolve().parent
REPORTS_DIR = BASE_DIR / "test_reports" / "ui"
SCREENSHOTS_DIR = REPORTS_DIR / "screenshots"
ACCESSIBILITY_DIR = REPORTS_DIR / "accessibility"

# Create directories if they don't exist
REPORTS_DIR.mkdir(parents=True, exist_ok=True)
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
ACCESSIBILITY_DIR.mkdir(parents=True, exist_ok=True)

# Test configuration
BROWSERS = ["chrome", "firefox"]
SCREEN_SIZES = {
    "mobile": (375, 667),      # iPhone 8
    "tablet": (768, 1024),     # iPad
    "desktop": (1366, 768),    # Laptop
    "large": (1920, 1080)      # Desktop
}

# URLs to test
URLS = [
    "/",
    "/pregnancy/",
    "/child-development/",
    "/nutrition/",
    "/tools/contraction-counter/",
    "/tools/kick-counter/",
    "/tools/sleep-timer/",
    "/tools/feeding-tracker/",
    "/tools/child-profiles/",
    "/tools/vaccine-calendar/",
    "/documentation/"
]

def setup_driver(browser, headless=True):
    """Set up WebDriver for the specified browser."""
    if browser == "chrome":
        options = ChromeOptions()
        if headless:
            options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    elif browser == "firefox":
        options = FirefoxOptions()
        if headless:
            options.add_argument("--headless")
        driver = webdriver.Firefox(executable_path=GeckoDriverManager().install(), options=options)
    else:
        raise ValueError(f"Unsupported browser: {browser}")
    
    return driver

def take_screenshot(driver, url, browser, size):
    """Take a screenshot of the specified URL."""
    filename = f"{browser}_{size}_{url.replace('/', '_')}.png"
    if filename.endswith("_.png"):
        filename = filename.replace("_.png", "index.png")
    
    screenshot_path = SCREENSHOTS_DIR / filename
    driver.save_screenshot(str(screenshot_path))
    return screenshot_path

def run_accessibility_test(driver, url, browser, size):
    """Run accessibility test using axe-core."""
    axe = axe_selenium_python.Axe(driver)
    axe.inject()
    results = axe.run()
    
    filename = f"{browser}_{size}_{url.replace('/', '_')}_a11y.json"
    if filename.endswith("__a11y.json"):
        filename = filename.replace("__a11y.json", "index_a11y.json")
    
    report_path = ACCESSIBILITY_DIR / filename
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    
    return results

def test_url(driver, base_url, url_path, browser, size):
    """Test a specific URL with the given browser and screen size."""
    full_url = f"{base_url}{url_path}"
    
    try:
        driver.get(full_url)
        time.sleep(2)  # Wait for page to load
        
        # Take screenshot
        screenshot_path = take_screenshot(driver, url_path, browser, size)
        
        # Run accessibility test
        a11y_results = run_accessibility_test(driver, url_path, browser, size)
        
        violations_count = len(a11y_results["violations"])
        
        return {
            "url": full_url,
            "browser": browser,
            "size": size,
            "screenshot": str(screenshot_path),
            "accessibility": {
                "violations": violations_count,
                "report": str(ACCESSIBILITY_DIR / f"{browser}_{size}_{url_path.replace('/', '_')}_a11y.json")
            },
            "status": "success"
        }
    except Exception as e:
        return {
            "url": full_url,
            "browser": browser,
            "size": size,
            "error": str(e),
            "status": "error"
        }

def run_tests(base_url, headless=True):
    """Run UI tests for all combinations of browsers and screen sizes."""
    results = []
    
    for browser in BROWSERS:
        for size_name, (width, height) in SCREEN_SIZES.items():
            print(f"Testing with {browser} at {size_name} size ({width}x{height})...")
            
            driver = setup_driver(browser, headless)
            driver.set_window_size(width, height)
            
            for url in URLS:
                print(f"  Testing URL: {url}")
                result = test_url(driver, base_url, url, browser, size_name)
                results.append(result)
                
                if result["status"] == "error":
                    print(f"    Error: {result['error']}")
                else:
                    violations = result["accessibility"]["violations"]
                    print(f"    Success! Accessibility violations: {violations}")
            
            driver.quit()
    
    return results

def generate_report(results):
    """Generate a comprehensive HTML report."""
    report_path = REPORTS_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    
    # Count statistics
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["status"] == "success")
    failed_tests = total_tests - successful_tests
    
    total_violations = sum(r["accessibility"]["violations"] for r in results if r["status"] == "success")
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>UI Test Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 0; padding: 20px; }}
            h1, h2, h3 {{ color: #333; }}
            .summary {{ background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
            .success {{ color: green; }}
            .error {{ color: red; }}
            table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            .screenshot {{ max-width: 300px; border: 1px solid #ddd; }}
        </style>
    </head>
    <body>
        <h1>UI Test Report</h1>
        <div class="summary">
            <h2>Summary</h2>
            <p>Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p>Total Tests: {total_tests}</p>
            <p>Successful Tests: <span class="success">{successful_tests}</span></p>
            <p>Failed Tests: <span class="error">{failed_tests}</span></p>
            <p>Total Accessibility Violations: <span class="error">{total_violations}</span></p>
        </div>
        
        <h2>Test Results</h2>
        <table>
            <tr>
                <th>URL</th>
                <th>Browser</th>
                <th>Size</th>
                <th>Status</th>
                <th>Accessibility Violations</th>
                <th>Screenshot</th>
            </tr>
    """
    
    for result in results:
        html += f"""
            <tr>
                <td>{result["url"]}</td>
                <td>{result["browser"]}</td>
                <td>{result["size"]}</td>
                <td class="{'success' if result['status'] == 'success' else 'error'}">{result["status"]}</td>
                <td>{result["accessibility"]["violations"] if result["status"] == "success" else "N/A"}</td>
                <td>
                    {f'<img src="{os.path.relpath(result["screenshot"], REPORTS_DIR)}" class="screenshot" />' if result["status"] == "success" else "N/A"}
                </td>
            </tr>
        """
    
    html += """
        </table>
    </body>
    </html>
    """
    
    with open(report_path, "w") as f:
        f.write(html)
    
    return report_path

def main():
    """Main function to run UI tests."""
    parser = argparse.ArgumentParser(description="Run comprehensive UI tests")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Base URL for testing")
    parser.add_argument("--no-headless", action="store_true", help="Run browsers in non-headless mode")
    args = parser.parse_args()
    
    print(f"Starting UI tests against {args.base_url}...")
    print(f"Headless mode: {not args.no_headless}")
    
    results = run_tests(args.base_url, headless=not args.no_headless)
    report_path = generate_report(results)
    
    print(f"\nUI testing complete!")
    print(f"Report generated: {report_path}")
    
    # Count statistics
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["status"] == "success")
    failed_tests = total_tests - successful_tests
    
    total_violations = sum(r["accessibility"]["violations"] for r in results if r["status"] == "success")
    
    print(f"Total Tests: {total_tests}")
    print(f"Successful Tests: {successful_tests}")
    print(f"Failed Tests: {failed_tests}")
    print(f"Total Accessibility Violations: {total_violations}")
    
    # Return non-zero exit code if there were failures
    return 1 if failed_tests > 0 else 0

if __name__ == "__main__":
    sys.exit(main())