#!/usr/bin/env python3
"""Check package completeness and active version metadata."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads((ROOT / "MANIFEST_V7.json").read_text(encoding="utf-8"))
    version = manifest["version"]
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    assert f"version: {version}" in skill.split("---", 2)[1]
    for name in ("STYLE_PROFILES_V7.json", "VECTOR_COMPONENT_CATALOG_V7.json"):
        assert json.loads((ROOT / "profiles" / name).read_text(encoding="utf-8"))["version"] == version
    missing = [rel for paths in manifest["files"].values()
               for rel in ([paths] if isinstance(paths, str) else paths)
               if not (ROOT / rel).is_file()]
    assert not missing, f"Missing manifest files: {missing}"
    assert manifest["baseline_status"] != "stable"
    print(f"PASS manifest {version}: all declared files present")


if __name__ == "__main__":
    main()
