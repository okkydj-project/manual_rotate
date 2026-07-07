#!/bin/bash
# Screen Rotate - Installer for Ubuntu Wayland
# Installs the application and creates a desktop launcher.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
APP_NAME="screen-rotate"
INSTALL_DIR="$HOME/.local/share/screen-rotate"
BIN_DIR="$HOME/.local/bin"
LAUNCHER_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons"

echo "=== Screen Rotate Installer ==="
echo ""

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required but not found."
    exit 1
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install --user --quiet PySide6 dbus-python 2>/dev/null || {
    echo "Note: If pip3 install fails, try: sudo apt install python3-pyside6.qtcore python3-pyside6.qtgui python3-pyside6.qtwidgets python3-dbus"
}

# Create directories
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$LAUNCHER_DIR"
mkdir -p "$ICON_DIR"

# Copy application files
echo "Installing application files..."
cp -r "$SCRIPT_DIR/screen_rotate" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/screen_rotate/icons/screen-rotate.svg" "$ICON_DIR/"

# Create launcher script
cat > "$BIN_DIR/screen-rotate" << 'LAUNCHER'
#!/bin/bash
export PYTHONPATH="$HOME/.local/share/screen-rotate:$PYTHONPATH"
exec python3 -m screen_rotate.main "$@"
LAUNCHER
chmod +x "$BIN_DIR/screen-rotate"

# Create desktop file
cat > "$LAUNCHER_DIR/screen-rotate.desktop" << DESKTOP
[Desktop Entry]
Name=Screen Rotate
Comment=Rotate your display manually
Exec=$BIN_DIR/screen-rotate
Icon=screen-rotate
Terminal=false
Type=Application
Categories=Utility;System;
StartupNotify=true
DESKTOP

# Update desktop database
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$LAUNCHER_DIR" 2>/dev/null || true
fi

echo ""
echo "=== Installation Complete ==="
echo ""
echo "You can now:"
echo "  - Find 'Screen Rotate' in Activities"
echo "  - Run: screen-rotate"
echo "  - Pin it to Favorites from Activities"
echo ""
echo "To uninstall, run: $SCRIPT_DIR/uninstall.sh"
