#!/bin/bash
# ──────────────────────────────────────────
#  GitPulse — Portable USB Launcher (Linux/MSYS2)
#  No installation required. No admin needed.
# ──────────────────────────────────────────

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
export GHM_CONFIG="$SCRIPT_DIR/config"

# Find Python
if [ -x "$SCRIPT_DIR/python/bin/python3" ]; then
    PYTHON="$SCRIPT_DIR/python/bin/python3"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
elif command -v python &>/dev/null; then
    PYTHON="python"
else
    echo ""
    echo "  ERROR: Python not found."
    echo "  Install Python 3.8+ or place a portable Python in $SCRIPT_DIR/python/"
    echo ""
    exit 1
fi

echo ""
echo "  GitPulse — Portable Mode"
echo "  Config: $GHM_CONFIG"
echo ""

# Check for requests
$PYTHON -c "import requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "  Installing requests..."
    $PYTHON -m pip install --user requests --quiet 2>/dev/null || \
    $PYTHON -m pip install requests --break-system-packages --quiet 2>/dev/null
fi

# CLI or Web mode
if [ "$1" = "--web" ]; then
    $PYTHON "$SCRIPT_DIR/gitpulse.py" --web
else
    $PYTHON "$SCRIPT_DIR/gitpulse.py"
fi
