"""Verify the frozen static research snapshot without rerunning the experiments."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = Path(__file__).with_name("STATIC_FREEZE.json")


def check_files(root, expected):
    issues = []
    for name, digest in expected.items():
        path = root / name
        if not path.is_file():
            issues.append(f"missing: {name}")
        elif hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            issues.append(f"modified: {name}")
    return issues


def main():
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected = manifest["files"]
    issues = check_files(ROOT, expected)
    if issues:
        raise SystemExit("\n".join(issues))
    print(f"Verified {len(expected)} frozen static research files.")


if __name__ == "__main__":
    main()
