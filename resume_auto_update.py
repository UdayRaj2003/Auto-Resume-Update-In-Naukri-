import argparse
import os
import re
import sys
import tempfile
import json 
import logging
import socket
import time
import ctypes
from ctypes import wintypes
from functools import wraps
from pathlib import Path
from datetime import datetime

import requests
from dotenv import load_dotenv

from src.client.naukri_client import NaukriLoginClient


load_dotenv(override=True)

DOWNLOAD_TIMEOUT = int(
    os.getenv("DOWNLOAD_TIMEOUT", "60")
)

RETRY_COUNT = int(
    os.getenv("RETRY_COUNT", "3")
)

LOG_RETENTION_DAYS = int(
    os.getenv("LOG_RETENTION_DAYS", "30")
)

username = os.getenv("USERNAME")
password = os.getenv("PASSWORD")

drive_url = os.getenv("GOOGLE_DRIVE_URL")


BASE_DIR = Path(__file__).resolve().parent

LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

STATUS_FILE = BASE_DIR / "status.json"

TODAY = datetime.now().strftime("%Y-%m-%d")

LOG_FILE = LOG_DIR / f"{TODAY}.log"

ERROR_LOG = LOG_DIR / "errors.log"



logger = logging.getLogger("ResumeUpdater")
logger.setLevel(logging.INFO)
logger.propagate = False
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(message)s"
)

fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
fh.setFormatter(formatter)

if not logger.handlers:
    logger.addHandler(fh)



error_logger = logging.getLogger("ResumeErrors")
error_logger.setLevel(logging.ERROR)
error_logger.propagate = False
efh = logging.FileHandler(ERROR_LOG, encoding="utf-8")
efh.setFormatter(formatter)

if not error_logger.handlers:
    error_logger.addHandler(efh)
# ==========================================================
# Helpers
# ==========================================================
def internet_available():

    try:

        socket.create_connection(("8.8.8.8", 53), timeout=5)

        return True

    except OSError:

        return False

def is_workstation_locked():
    """
    Returns True if Windows workstation is locked.
    Returns False if user session is unlocked.
    """

    user32 = ctypes.WinDLL("user32", use_last_error=True)

    UOI_NAME = 2

    hDesktop = user32.OpenInputDesktop(
        0,
        False,
        0x0001
    )

    if not hDesktop:
        # Unable to open input desktop
        # Usually means workstation is locked
        return True

    needed = wintypes.DWORD()

    user32.GetUserObjectInformationW(
        hDesktop,
        UOI_NAME,
        None,
        0,
        ctypes.byref(needed)
    )

    buffer = ctypes.create_unicode_buffer(
        needed.value
    )

    user32.GetUserObjectInformationW(
        hDesktop,
        UOI_NAME,
        buffer,
        needed,
        ctypes.byref(needed)
    )

    user32.CloseDesktop(hDesktop)

    return buffer.value.lower() != "default"


def retry(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        last = None

        for i in range(RETRY_COUNT):

            try:
                return func(*args, **kwargs)

            except Exception as e:

                last = e

                logger.warning(
                    f"Retry {i+1}/{RETRY_COUNT}: {e}"
                )

                time.sleep(min(2 ** i, 10))

        raise last

    return wrapper

    
    



def save_status(status, msg=""):

    data = {

        "last_run": datetime.now().isoformat(),
        "status": status,
        "message": msg

    }

    with open(
        STATUS_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            indent=4
        )

def cleanup_logs():

    LOG_DIR.mkdir(exist_ok=True)

    cutoff = time.time() - (
        LOG_RETENTION_DAYS * 86400
    )

    for file in LOG_DIR.glob("*.log"):

        if file.name=="errors.log":
            continue

        if file.stat().st_mtime < cutoff:
            file.unlink()



def error(msg):
    print(f"\n❌ {msg}")

    try:
        logger.error(msg)
    except:
        pass

    sys.exit(1)


def success(msg):
    print(f"✅ {msg}")

    try:
        logger.info(msg)
    except:
        pass


    # ==========================================================
    # Google Drive
    # ==========================================================
@retry
def download_resume(share_url: str, resume_name: str) -> str:

    print("\n📥 Downloading latest resume from Google Drive...")

    match = re.search(r"/d/([A-Za-z0-9_-]+)", share_url)

    if not match:
        error("Invalid GOOGLE_DRIVE_URL")

    file_id = match.group(1)

    download_url = (
        f"https://drive.google.com/uc?export=download&id={file_id}"
    )

    response = requests.get(
        download_url,
        timeout=DOWNLOAD_TIMEOUT
    )

    response.raise_for_status()

    if not response.content.startswith(b"%PDF"):
        error(
            "Downloaded file is not a valid PDF.\n"
            "Make sure Google Drive file is shared as:\n"
            "'Anyone with the link → Viewer'"
        )

    today = datetime.now().strftime("%Y-%m-%d")

    filename = f"{resume_name}_{today}.pdf"

    filepath = os.path.join(
        tempfile.gettempdir(),
        filename
    )

    with open(filepath, "wb") as f:
        f.write(response.content)

    success(f"Downloaded: {filename}")

    return filepath

@retry
def login_client(client):
    return client.login()

@retry
def upload_resume(client,path):
    return client.update_resume(path)
# ==========================================================
# Main
# ==========================================================

def main():

    start = time.time()
    cleanup_logs()
    parser = argparse.ArgumentParser(
        description="NopeRi Resume Auto Updater"
    )

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show full traceback"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("           NopeRi Resume Auto Updater")
    print("=" * 60)


    if not internet_available():
        error("No Internet Connection")

    resume_name = os.getenv(
        "RESUME_NAME",
        "Resume"
    )
    if not username:
        error("USERNAME missing in .env")

    if not password:
        error("PASSWORD missing in .env")

    if not drive_url:
        error("GOOGLE_DRIVE_URL missing in .env")

    success("Environment loaded")

    pdf_path = None

    try:

        # --------------------------------------
        # Download Resume
        # --------------------------------------

        pdf_path = download_resume(
            drive_url,
            resume_name
        )

        # --------------------------------------
        # Login
        # --------------------------------------

        print("\n🔐 Logging into Naukri...")

        client = NaukriLoginClient(
            username,
            password
        )

        login_client(client)

        success("Login successful")

        # --------------------------------------
        # Upload Resume
        # --------------------------------------

        print("\n📤 Uploading latest resume...")

        result = upload_resume(client,pdf_path)

        success("Resume updated successfully")
        logger.info(
            f"Uploaded Resume : {os.path.basename(pdf_path)}"
        )
        save_status(
            "SUCCESS",
            "Resume Updated Successfully"
            )

        print("\nResult")
        print("-" * 60)
        print(result)
        logger.info(f"API Response : {result}")

    except Exception as e:

        import traceback
        
        error_logger.error(
            traceback.format_exc()
        )
        logger.error(str(e))

        save_status(
            "FAILED",
            str(e)
        )

        if args.debug:
            raise

        error(str(e))



    finally:

        if pdf_path and os.path.exists(pdf_path):

            try:

                os.remove(pdf_path)
                success("Temporary resume deleted")

            except Exception:
                pass

        execution = time.time() - start

        logger.info(
            f"Execution Time: {execution:.2f}s"
        )
        logger.info("-" * 80)
        logger.info("")

        print(
            f"\nExecution Time : {execution:.2f} sec"
        )

        print("\n🎉 Finished")
        
        # --------------------------------------
        # Auto Sleep
        # --------------------------------------

        AUTO_SLEEP = os.getenv(
            "AUTO_SLEEP",
            "false"
        ).lower() == "true"

        AUTO_SLEEP_DELAY = int(
            os.getenv(
                "AUTO_SLEEP_DELAY",
                "300"
            )
        )

        if AUTO_SLEEP:

            logger.info(
                f"Waiting {AUTO_SLEEP_DELAY} seconds before checking workstation..."
            )

            time.sleep(AUTO_SLEEP_DELAY)

            if is_workstation_locked():

                logger.info(
                    "Workstation is locked. Going to Sleep..."
                )

                ctypes.windll.PowrProf.SetSuspendState(
                    False,
                    False,
                    False
                )

            else:

                logger.info(
                    "Workstation is unlocked. Sleep skipped."
                )
        

if __name__ == "__main__":
    main()