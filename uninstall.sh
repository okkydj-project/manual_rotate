#!/bin/bash
# Screen Rotate - Uninstaller

set -e

APP_NAME="screen-rotate"
INSTALL_DIR="$HOME/.local/share/screen-rotate"
BIN_DIR="$HOME/.local/bin"
LAUNCHER_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons"

echo "=== Screen Rotate Uninstaller ==="
echo ""

# Remove application files
echo "Removing application files..."
rm -rf "$INSTALL_DIR"
rm -f "$BIN_DIR/$APP_NAME"
rm -f "$LAUNCHER_DIR/$APP_NAME.desktop"
rm -f "$ICON_DIR/$APP_NAME.svg"

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$LAUNCHER_DIR" 2>/dev/null || true
fi

echo ""
echo "=== Uninstall Complete ==="
echo ""
echo "Screen Rotate has been removed."
echo "PySide6 and dbus-python were not removed (other apps may need them)."
