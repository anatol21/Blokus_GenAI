#!/usr/bin/env bash
set -euo pipefail

python3 -m venv .venv
. .venv/bin/activate
python - <<'PY'
import site
from pathlib import Path

root = Path.cwd()
src = root / "src"
site_packages = Path(site.getsitepackages()[0])
pth_path = site_packages / "blokus_focus_pokus_local.pth"
pth_path.write_text(f"{src}\n", encoding="utf-8")
print(f"Wrote {pth_path}")
PY

python -m pip install -e '.[test]'
