#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/src"

if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi
# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --upgrade pip
pip install -r ../requirements-build.txt
python -c "import os; [os.makedirs(d, exist_ok=True) for d in ('logs', 'media', 'static')]"

pyinstaller --clean --noconfirm bulk_emailer.spec

echo "Build complete: $ROOT/src/dist/bulk_emailer"
