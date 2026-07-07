# AGENTS.md — Screen Rotate Project Memory

## Project Overview

A PySide6 desktop app for Ubuntu 26.04 Wayland that rotates the built-in display
via the `org.gnome.Mutter.DisplayConfig` D-Bus API.

**Working directory:** `/home/oq-dj/Desktop/opencode_space/manual_rotate/`
**Package:** `screen_rotate/`
**Run:** `./run.sh` (or `python3 -m screen_rotate.main`)

---

## What Works

- **Rotation itself:** All 4 rotations work (Landscape, Portrait Left/Right, Upside Down).
- **D-Bus API:** `GetCurrentState` / `ApplyMonitorsConfig` work correctly.
- **Monitor discovery:** Built-in display (`eDP-1`) found dynamically, no hardcoded values.
- **GUI:** PySide6 resizable window, QToolButton-based orientation selector, status display, active button highlight.
- **Desktop launcher:** Fixed — `~/.local/bin/screen-rotate` now sets `PYTHONPATH`.

---

## Historical Bug: Brightness Dims on Rotation (FIXED)

### Root cause

GNOME's **ambient light sensor** (`ambient-enabled=true`) was fighting `SetBacklight`
calls. After `ApplyMonitorsConfig`, the ambient sensor would override our brightness
restore, causing the screen to settle at whatever level the sensor wanted instead of
the saved level.

Additionally: D-Bus backlight value and sysfs can diverge, so the D-Bus backlight
value is not a reliable source of truth — we must read actual hardware brightness
from sysfs.

### Fix (implemented)

1. **Read sysfs brightness** (`actual_brightness`) — the true hardware value
2. **Disable ambient light sensor** via `gsettings` before rotation
3. **Retry SetBacklight** (2 attempts × 0.3s) — reduced from 8, works now that ambient is off
4. **Verify with sysfs** after restore (1 check with 0.2s delay)
5. **Re-enable ambient sensor** in `finally` block (always restored even on errors)
6. **Sysfs fallback:** when `actual_brightness` returns 0 (screen in low-power state), fall back to `brightness`

### Key files changed

- `display.py`: Ambient disable/restore, sysfs-based save, minimal verification
- `dbus.py`: Retry-based `set_backlight` (always calls `SetBacklight`, never trusts D-Bus current value)

---

## Historical Bug: UI Freeze During Rotation (FIXED)

### Root cause

`apply_rotation()` ran entirely on the GUI thread — blocking D-Bus calls +
`time.sleep()` loops (~6.2s) froze the Qt event loop completely.

### Fix (implemented)

Rotation now runs on a **QThread** (`RotationWorker`) so the main Qt event loop
stays free. The GUI disables all orientation buttons during rotation and shows
"Rotating..." in the status bar. When the worker emits `done`, the UI refreshes
and buttons re-enable.

**Timing optimizations applied:**
| Before | After | Change |
|--------|-------|--------|
| `set_backlight` retries: 8 × 0.4s | 2 × 0.3s | 3.2s → 0.6s |
| Verification loop: 3 × 0.5s | 1 × 0.2s | 1.5s → 0.2s |
| Ambient disable sleep: 0.3s | 0.1s | 0.3s → 0.1s |
| **Total rotation time:** ~6.2s | **~1.0s** | **84% reduction** |

### Key files changed

- `gui.py`: Added `RotationWorker(QThread)` class, `_busy` flag, async flow

---

## GUI Layout Overhaul (DONE)

- **Button widget:** QPushButton → **QToolButton** (`ToolButtonTextUnderIcon` — icon above text)
- **Grid layout:** Diamond (3×3, 5 empty cells) → **Top→2col→Bottom** with `colSpan`
- **Info section:** 4 labels stacked → **2×2 grid** (half the height)
- **Window:** Removed `setFixedSize`, now resizable with `setMinimumSize(480, 520)`
- **Button sizing:** `QSizePolicy.Expanding` both directions, min 100×80
- **Zero overlap** verified at 400×400, 600×580, 800×600, 1200×800

---

## D-Bus backlight details

- **Backlight property:** `(serial, [{connector, active, min, max, value}])`
- **SetBacklight:** `(serial, connector, value)` — requires FRESH serial
- **ChangeBacklight:** `(serial, output_index, value)` — deprecated, returns new value
- **sysfs path:** `/sys/class/backlight/intel_backlight/`
- **actual_brightness:** 10–1060 range
- Writing sysfs requires root (permission denied for user)

### GNOME settings that affect brightness

```
org.gnome.settings-daemon.plugins.power idle-dim true
org.gnome.settings-daemon.plugins.power idle-brightness 30
```

### Other D-Bus services on the system

- `org.gnome.Shell.Brightness` — has `SetDimming(bool)` and `SetAutoBrightnessTarget(double)` but NO SetBrightness
- `org.gnome.SettingsDaemon.Power` — NOT running (ServiceUnknown)
- `org.gnome.Mutter.IdleMonitor` — available
- `org.gnome.Mutter.DisplayConfig` — our main interface

---

## Files

```
screen_rotate/
├── main.py          # Entry point, PySide6 QApplication
├── gui.py           # QMainWindow + RotationWorker (QThread) + QToolButton layout
├── display.py       # DisplayController — discover, apply rotation, brightness save/restore, ambient control
├── monitor.py       # Dataclasses, rotation constants, D-Bus state parsers
├── dbus.py          # DisplayConfigDBus — low-level D-Bus wrapper, retry-based set_backlight
├── __init__.py
└── icons/           # SVG icons for each rotation + app icon

install.sh           # Installs to ~/.local/share/screen-rotate/, creates launcher
uninstall.sh         # Removes installed files
run.sh               # Quick launcher
requirements.txt     # PySide6, dbus-python
README.md
instruction.md       # Original requirements
```

---

## How to test

```bash
cd /home/oq-dj/Desktop/opencode_space/manual_rotate
./run.sh

# Or test rotation from CLI:
python3 -c "
from screen_rotate.display import DisplayController
ctrl = DisplayController()
ctrl.apply_rotation(1)  # 90 degrees
"
```

---

## What to try next

1. **Test edge cases:** very low brightness, night light mode, external monitors
2. **Improve GUI feedback** during rotation (spinner, dim overlay, etc.)
3. **Add keyboard shortcuts** for quick rotation
4. **Auto-detect tablet mode** and suggest portrait rotation

---

## Environment

- Ubuntu 26.04 LTS, GNOME 50, Wayland
- Python 3.14, PySide6, dbus-python
- sysfs backlight: `/sys/class/backlight/intel_backlight/` (min=10, max=1060)
- Connector: `eDP-1` (CMN built-in display)
