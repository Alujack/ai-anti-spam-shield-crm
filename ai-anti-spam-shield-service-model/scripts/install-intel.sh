#!/bin/bash
#
# Install Phishing Intelligence Engine Dependencies
# Phase 3: Domain Intelligence, SSL Analysis, Screenshot Capture
#

set -e

echo "========================================"
echo "Phishing Intelligence Engine Installer"
echo "========================================"
echo ""

# Check if running in virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Warning: Not running in a virtual environment"
    echo "Consider activating your venv first: source venv/bin/activate"
    echo ""
fi

echo "[1/3] Installing Python packages..."
pip install python-whois dnspython aiohttp playwright Pillow

echo ""
echo "[2/3] Installing Playwright browsers..."
echo "This may take a few minutes on first run..."
playwright install chromium

echo ""
echo "[3/3] Verifying installation..."

python3 -c "
import whois
import dns.resolver
import aiohttp
from playwright.async_api import async_playwright
from PIL import Image
print('All packages imported successfully!')
"

echo ""
echo "========================================"
echo "Installation complete!"
echo "========================================"
echo ""
echo "New endpoints available:"
echo "  POST /analyze-url-deep   - Deep URL analysis with all components"
echo "  GET  /intel/domain/{d}   - Domain intelligence lookup"
echo "  POST /intel/screenshot   - Screenshot capture and analysis"
echo "  POST /intel/risk-score   - Manual risk score calculation"
echo "  GET  /intel-health       - Health check for intel engine"
echo ""
echo "Start the server with:"
echo "  cd app && uvicorn main:app --reload"
echo ""
