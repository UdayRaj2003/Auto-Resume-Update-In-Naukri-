# ----------------------------------------------------------------------------------
# run_all.py
#
# Single entry point to run the full NopeRi daily pipeline:
#   1. apply_agent.py        — search, filter, and apply to matching jobs
#   2. resume_auto_update.py — download latest resume from Google Drive and upload
#
# Usage:
#   python run_all.py                  # auto-uses .venv if present
#   .venv\Scripts\python run_all.py    # explicit venv invocation
#   python run_all.py --debug          # forwarded to resume_auto_update.py
#
# Both scripts always run — a failure in one does not skip the other.
# If not already inside .venv, this script re-launches itself with it.
# ----------------------------------------------------------------------------------

import os
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
VENV_DIR = BASE_DIR / ".venv"
VENV_PYTHON = (
    VENV_DIR / "Scripts" / "python.exe"
    if os.name == "nt"
    else VENV_DIR / "bin" / "python"
)

PIPELINE = [
    ("Job Apply Agent", BASE_DIR / "apply_agent.py"),
    ("Resume Auto Updater", BASE_DIR / "resume_auto_update.py"),
]


def resolve_python() -> Path:
    if VENV_PYTHON.is_file():
        return VENV_PYTHON
    return Path(sys.executable)


def ensure_venv() -> None:
    """Re-launch this script with .venv Python when available."""
    target = resolve_python()
    current = Path(sys.executable).resolve()
    if target.resolve() == current:
        return

    print(f"Switching to venv Python: {target}")
    result = subprocess.run(
        [str(target), str(Path(__file__).resolve()), *sys.argv[1:]],
        cwd=BASE_DIR,
    )
    sys.exit(result.returncode)


PYTHON = resolve_python()


def pipeline_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONUNBUFFERED", "1")
    return env


def run_script(label: str, script: Path, extra_args: list[str]) -> int:
    print("\n" + "=" * 60)
    print(f"  Starting: {label}")
    print(f"  Script  : {script.name}")
    print("=" * 60 + "\n")

    start = time.time()
    result = subprocess.run(
        [str(PYTHON), str(script), *extra_args],
        cwd=BASE_DIR,
        env=pipeline_env(),
    )
    elapsed = time.time() - start

    status = "OK" if result.returncode == 0 else f"FAILED (exit {result.returncode})"
    print(f"\n{label} finished in {elapsed:.1f}s — {status}\n")
    return result.returncode


def main() -> int:
    extra_args = sys.argv[1:]

    print("=" * 60)
    print("           NopeRi — Full Pipeline")
    print("=" * 60)
    print("  Order: job apply → resume update")
    print(f"  Python: {PYTHON}")
    print("=" * 60)

    pipeline_start = time.time()
    results: list[tuple[str, int | None]] = []

    for label, script in PIPELINE:
        if not script.is_file():
            print(f"❌ Missing script: {script}")
            results.append((label, None))
            continue

        args = extra_args if script.name == "resume_auto_update.py" else []
        code = run_script(label, script, args)
        results.append((label, code))

    total = time.time() - pipeline_start
    print("=" * 60)
    print("  Pipeline summary")
    print("-" * 60)
    for label, code in results:
        if code is None:
            status = "SKIPPED (script missing)"
        elif code == 0:
            status = "OK"
        else:
            status = f"FAILED (exit {code})"
        print(f"  {label}: {status}")
    print("-" * 60)
    print(f"  Total time: {total:.1f}s")
    print("=" * 60)

    failed = any(code not in (0, None) for _, code in results)
    missing = any(code is None for _, code in results)
    return 1 if failed or missing else 0


if __name__ == "__main__":
    ensure_venv()
    sys.exit(main())
