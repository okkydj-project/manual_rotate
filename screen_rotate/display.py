"""High-level display control: discover monitors, apply rotation."""

import glob
import os
import subprocess
import time
from typing import Optional

from .dbus import DisplayConfigDBus
from .monitor import (
    PhysicalMonitor,
    LogicalMonitor,
    parse_physical_monitor,
    parse_logical_monitor,
    ROTATION_NORMAL,
    ROTATION_90,
    ROTATION_180,
    ROTATION_270,
)

_POWER_SCHEMA = "org.gnome.settings-daemon.plugins.power"


def _find_backlight_path():
    """Find the sysfs backlight path."""
    matches = glob.glob("/sys/class/backlight/*")
    return matches[0] if matches else None


def _read_sysfs_brightness():
    """Read actual hardware brightness from sysfs. Returns integer value."""
    path = _find_backlight_path()
    if path is None:
        return 0
    try:
        with open(os.path.join(path, "actual_brightness")) as f:
            val = int(f.read().strip())
        if val > 0:
            return val
    except (OSError, ValueError):
        pass
    try:
        with open(os.path.join(path, "brightness")) as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return 0


class DisplayController:
    """Manages display configuration via Mutter D-Bus."""

    def __init__(self):
        self._dbus = DisplayConfigDBus()
        self.serial: int = 0
        self.physical_monitors: list[PhysicalMonitor] = []
        self.logical_monitors: list[LogicalMonitor] = []
        self.properties: dict = {}

    def discover(self):
        """Re-read the current state from D-Bus."""
        state = self._dbus.get_current_state()
        self.serial = int(state[0])
        self.physical_monitors = [parse_physical_monitor(m) for m in state[1]]
        self.logical_monitors = [parse_logical_monitor(lm) for lm in state[2]]
        self.properties = dict(state[3])

    def get_builtin_monitor(self) -> Optional[PhysicalMonitor]:
        """Return the built-in (internal) physical monitor, or the first one."""
        for m in self.physical_monitors:
            if m.is_builtin:
                return m
        return self.physical_monitors[0] if self.physical_monitors else None

    def get_builtin_logical_monitor(self) -> Optional[LogicalMonitor]:
        """Return the logical monitor that contains the built-in display."""
        builtin = self.get_builtin_monitor()
        if builtin is None:
            return None
        for lm in self.logical_monitors:
            if builtin.connector in lm.monitor_connectors:
                return lm
        return self.logical_monitors[0] if self.logical_monitors else None

    def get_current_rotation(self) -> int:
        """Return the current rotation of the built-in display."""
        lm = self.get_builtin_logical_monitor()
        return lm.rotation if lm else ROTATION_NORMAL

    def get_current_scale(self) -> float:
        """Return the current scale of the built-in display."""
        lm = self.get_builtin_logical_monitor()
        return lm.scale if lm else 1.0

    def get_active_mode(self) -> Optional[str]:
        """Return the active mode ID of the built-in display."""
        bm = self.get_builtin_monitor()
        if bm and bm.active_mode:
            return bm.active_mode.mode_id
        return None

    def get_active_resolution(self) -> str:
        """Return a human-readable resolution string."""
        bm = self.get_builtin_monitor()
        if bm and bm.active_mode:
            return f"{bm.active_mode.width}x{bm.active_mode.height}"
        return "Unknown"

    def apply_rotation(self, rotation: int):
        """Apply a rotation to the built-in display.

        Args:
            rotation: One of ROTATION_NORMAL, ROTATION_90, ROTATION_180, ROTATION_270.

        Raises:
            Exception: If D-Bus call fails.
        """
        self.discover()

        builtin = self.get_builtin_monitor()
        lm = self.get_builtin_logical_monitor()
        if builtin is None or lm is None:
            raise RuntimeError("No built-in display found")

        mode_id = self.get_active_mode()
        if mode_id is None:
            raise RuntimeError("No active mode found")

        saved_brightness = _read_sysfs_brightness()

        ambient_was_enabled = self._disable_ambient()

        try:
            monitors = [(builtin.connector, mode_id, {})]

            logical_monitor = (
                lm.x,
                lm.y,
                lm.scale,
                rotation,
                lm.primary,
                monitors,
            )

            self._dbus.apply_monitors_config(
                self.serial,
                1,
                [logical_monitor],
            )

            if saved_brightness > 0:
                self._dbus.set_backlight(builtin.connector, saved_brightness)

                time.sleep(0.2)
                actual = _read_sysfs_brightness()
                if abs(actual - saved_brightness) > 10:
                    self._dbus.set_backlight(builtin.connector, saved_brightness)
        finally:
            if ambient_was_enabled:
                self._restore_ambient()

    @staticmethod
    def _get_ambient_state():
        """Check if ambient light sensor is enabled."""
        try:
            result = subprocess.run(
                ["gsettings", "get", _POWER_SCHEMA, "ambient-enabled"],
                capture_output=True, text=True, check=False,
            )
            return result.stdout.strip().lower() == "true"
        except Exception:
            return False

    @staticmethod
    def _disable_ambient():
        """Disable ambient light sensor. Returns True if it was enabled."""
        was_enabled = DisplayController._get_ambient_state()
        if was_enabled:
            subprocess.run(
                ["gsettings", "set", _POWER_SCHEMA, "ambient-enabled", "false"],
                check=False,
            )
            time.sleep(0.1)
        return was_enabled

    @staticmethod
    def _restore_ambient():
        """Re-enable ambient light sensor."""
        subprocess.run(
            ["gsettings", "set", _POWER_SCHEMA, "ambient-enabled", "true"],
            check=False,
        )
