"""Check the final mobile snapshot and the existing static freeze read-only."""
import json
from pathlib import Path

from ble_crowd.verify_freeze import ROOT, MANIFEST as STATIC, check_files

MANIFEST = Path(__file__).resolve().parents[1] / "MOBILE_FREEZE.json"


def main():
    static = json.loads(STATIC.read_text(encoding="utf-8"))["files"]
    mobile = json.loads(MANIFEST.read_text(encoding="utf-8"))["files"]
    issues = check_files(ROOT, static) + check_files(ROOT, mobile)
    if issues:
        raise SystemExit("\n".join(issues))
    print(f"Verified {len(mobile)} mobile snapshot files and {len(static)} static snapshot files.")


if __name__ == "__main__":
    main()
