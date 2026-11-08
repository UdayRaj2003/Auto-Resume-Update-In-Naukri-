"""
login_browser.py — Semi-automated one-click browser login helper for Naukri.

Launches a visible Chrome window, pre-fills your username and password,
and automatically extracts the 'nauk_at' session cookie to save it directly
into .env as NAUKRI_AUTH_TOKEN.
"""

import os
import time
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(ENV_PATH, override=True)

USERNAME = os.getenv("USERNAME", "")
PASSWORD = os.getenv("PASSWORD", "")

LOGIN_URL = "https://www.naukri.com/nlogin/login"


def update_env_token(token: str) -> None:
    """Write or update NAUKRI_AUTH_TOKEN in the .env file and current os.environ."""
    os.environ["NAUKRI_AUTH_TOKEN"] = token
    lines = []
    found = False

    if ENV_PATH.exists():
        with open(ENV_PATH, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("NAUKRI_AUTH_TOKEN="):
                    lines.append(f"NAUKRI_AUTH_TOKEN={token}\n")
                    found = True
                else:
                    lines.append(line)

    if not found:
        if lines and not lines[-1].endswith("\n"):
            lines.append("\n")
        lines.append(f"NAUKRI_AUTH_TOKEN={token}\n")

    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)


def run_login():
    print("=" * 60)
    print("        Naukri Automated Browser Login & Token Sync")
    print("=" * 60)

    if not USERNAME or not PASSWORD:
        print("[ERROR] USERNAME and PASSWORD must be set in .env")
        return False

    print("\n[1/3] Launching Chrome...")
    options = webdriver.ChromeOptions()
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(options=options)

    try:
        print(f"[2/3] Opening {LOGIN_URL}...")
        driver.get(LOGIN_URL)

        # Pre-fill username and password
        wait = WebDriverWait(driver, 10)
        try:
            u_input = wait.until(EC.presence_of_element_located((By.ID, "usernameField")))
            p_input = driver.find_element(By.ID, "passwordField")
            u_input.clear()
            u_input.send_keys(USERNAME)
            p_input.clear()
            p_input.send_keys(PASSWORD)

            # Click login button
            submit_btn = driver.find_element(By.XPATH, "//button[@type='submit' and contains(., 'Login')]")
            submit_btn.click()
            print("[INFO] Credentials entered and Login clicked.")
        except Exception as e:
            print(f"[NOTE] Automatic form fill skipped: {e}")

        print("\n[3/3] Waiting for login to complete...")
        print(">>> If a CAPTCHA or OTP appears, please complete it in the Chrome window. <<<")

        # Poll cookies until 'nauk_at' appears
        start_time = time.time()
        timeout = 180  # 3 minutes

        while time.time() - start_time < timeout:
            try:
                cookies = driver.get_cookies()
            except Exception:
                print("\n[NOTE] Chrome window was closed before login completed.")
                return False
            for c in cookies:
                if c.get("name") == "nauk_at" and c.get("value"):
                    token = c["value"]
                    update_env_token(token)
                    print(f"\n[SUCCESS] Captured 'nauk_at' session token ({len(token)} chars)!")
                    print(f"[SUCCESS] Saved NAUKRI_AUTH_TOKEN to: {ENV_PATH}")
                    return True
            time.sleep(1)

        print("\n[ERROR] Timed out waiting for login after 3 minutes.")
        return False

    finally:
        try:
            driver.quit()
        except Exception:
            pass


if __name__ == "__main__":
    success = run_login()
    exit(0 if success else 1)

