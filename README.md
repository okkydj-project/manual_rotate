# Screen Rotate

A lightweight native desktop application for manually rotating the display on Ubuntu 26.04 with GNOME 50 and Wayland.

Replaces the broken GNOME auto-rotation feature with a reliable manual solution.

## Requirements

- Ubuntu 26.04 LTS
- GNOME 50
- Wayland
- Python 3.10+
- PySide6
- dbus-python

## Installation

### Quick Install

```bash
chmod +x install.sh
./install.sh
```

### Manual Install

```bash
pip3 install --user PySide6 dbus-python
python3 -m screen_rotate.main
```

### From apt (if available)

```bash
sudo apt install python3-pyside6.qtcore python3-pyside6.qtgui python3-pyside6.qtwidgets python3-dbus
```

## Usage

1. Launch from Activities menu: search for "Screen Rotate"
2. Or run from terminal: `screen-rotate`
3. Click one of four rotation buttons:
   - **Landscape** - Normal orientation (0°)
   - **Portrait Left** - Rotated 90° counter-clockwise
   - **Portrait Right** - Rotated 90° clockwise
   - **Upside Down** - Rotated 180°

The current display info (monitor name, resolution, scale, orientation) is shown at the top.

## Architecture

```
screen_rotate/
├── main.py          # Entry point
├── gui.py           # PySide6 GUI
├── display.py       # High-level display control
├── monitor.py       # Monitor discovery and data models
├── dbus.py          # D-Bus wrapper for Mutter DisplayConfig
└── icons/           # SVG icons for rotation buttons
```

### D-Bus Interface

Uses the official `org.gnome.Mutter.DisplayConfig` D-Bus API:

- `GetCurrentState` - Reads current monitor configuration
- `ApplyMonitorsConfig` - Applies rotation changes

No xrandr, wlr-randr, swaymsg, or X11 APIs are used.

## How It Works

1. On startup, reads the current display state via D-Bus
2. Discovers the built-in display dynamically (no hardcoded connector names)
3. Shows current resolution, scale, and orientation
4. When a rotation button is clicked, applies the new configuration via `ApplyMonitorsConfig`
5. The active orientation button is highlighted and disabled to prevent redundant clicks

## Error Handling

- If the display configuration changes while the app is open, click a button to rediscover
- If Mutter rejects a rotation request, a clear error message is displayed
- The application does not crash on errors

## Uninstallation

```bash
chmod +x uninstall.sh
./uninstall.sh
```

This removes:
- Application files from `~/.local/share/screen-rotate/`
- Launcher from `~/.local/share/applications/`
- Icon from `~/.local/share/icons/`
- Binary from `~/.local/bin/screen-rotate`

Python packages (PySide6, dbus-python) are not removed as other applications may depend on them.

## Troubleshooting

### "No built-in display detected"

The application looks for a monitor with `is-builtin=true` property. If your internal display is not detected, check:

```bash
busctl introspect org.gnome.Mutter.DisplayConfig /org/gnome/Mutter/DisplayConfig
```

### "ApplyMonitorsConfig not allowed"

Some systems may restrict display configuration changes. Check the `ApplyMonitorsConfigAllowed` property.

### Rotation doesn't apply

Ensure you are running under Wayland, not X11. Check with:

```bash
echo $XDG_SESSION_TYPE
```

## Known Limitations

- Only rotates the primary/built-in display
- External monitors are discovered but not rotated
- Scale and resolution are preserved from current settings
- Requires Wayland (does not work on X11)

## License

MIT
