#!/bin/bash
# AI Anti-Spam Shield Mobile - Startup Script
# This script sets up the correct Xcode environment (Xcode 26)

export DEVELOPER_DIR=/Applications/Xcode26.app/Contents/Developer

echo "=========================================="
echo "  AI Anti-Spam Shield Mobile"
echo "  Using Xcode 26"
echo "=========================================="
echo ""
echo "DEVELOPER_DIR set to: $DEVELOPER_DIR"
echo ""
echo "You can now run:"
echo "  flutter run"
echo "  flutter build ios"
echo "  open ios/Runner.xcworkspace"
echo ""

# Start a new shell with the environment set
exec $SHELL
