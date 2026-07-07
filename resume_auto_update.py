import argparse
import os
import re
import sys
import tempfile
from datetime import datetime

import requests
from dotenv import load_dotenv

from src.client.naukri_client import NaukriLoginClient


# ==========================================================
# Helpers
# ==========================================================

def error(msg):
    print(f"\n❌ {msg}")
    sys.exit(1)


def success(msg):
    print(f"✅ {msg}")


# ==========================================================
# Google Drive
# ==========================================================

def download_resume(share_url: str, resume_name: str) -> str:
    """
    Accepts a normal Google Drive share link like:

    https://drive.google.com/file/d/FILE_ID/view?usp=sharing

    Downloads the PDF and saves it as:

    Uday_Resume_2026-07-07.pdf
    """

    print("\n📥 Downloading latest resume from Google Drive...")

    match = re.search(r"/d/([A-Za-z0-9_-]+)", share_url)

    if not match:
        error("Invalid GOOGLE_DRIVE_URL")

    file_id = match.group(1)

    download_url = (
        f"https://drive.google.com/uc?export=download&id={file_id}"
    )

    response = requests.get(download_url, timeout=60)
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
        filename,
    )

    with open(filepath, "wb") as f:
        f.write(response.content)

    success(f"Downloaded: {filename}")

    return filepath


# ==========================================================
# Main
# ==========================================================

def main():

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

    load_dotenv(override=True)

    username = os.getenv("USERNAME")
    password = os.getenv("PASSWORD")

    drive_url = os.getenv("GOOGLE_DRIVE_URL")

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

        client.login()

        success("Login successful")

        # --------------------------------------
        # Upload Resume
        # --------------------------------------

        print("\n📤 Uploading latest resume...")

        result = client.update_resume(pdf_path)

        success("Resume updated successfully")

        print("\nResult")
        print("-" * 60)
        print(result)

    except Exception as e:

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

    print("\n🎉 Finished")


if __name__ == "__main__":
    main()