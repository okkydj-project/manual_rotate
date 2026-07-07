"""D-Bus interface to org.gnome.Mutter.DisplayConfig."""

import time

import dbus


_BUS_NAME = "org.gnome.Mutter.DisplayConfig"
_OBJECT_PATH = "/org/gnome/Mutter/DisplayConfig"
_INTERFACE = "org.gnome.Mutter.DisplayConfig"


class DisplayConfigDBus:
    """Low-level D-Bus wrapper for Mutter DisplayConfig."""

    def __init__(self):
        bus = dbus.SessionBus()
        self._proxy = bus.get_object(_BUS_NAME, _OBJECT_PATH)
        self._iface = dbus.Interface(self._proxy, _INTERFACE)
        self._props = dbus.Interface(self._proxy, "org.freedesktop.DBus.Properties")

    def get_current_state(self):
        """Return (serial, physical_monitors, logical_monitors, properties)."""
        return self._iface.GetCurrentState()

    def apply_monitors_config(self, serial, method, logical_monitors, properties=None):
        """Apply a new monitor configuration.

        Args:
            serial: Serial from GetCurrentState.
            method: 0=verify, 1=temporary, 2=persistent.
            logical_monitors: List of (x, y, scale, rotation, primary, monitors).
            properties: Dict of global properties.
        """
        if properties is None:
            properties = {}
        self._iface.ApplyMonitorsConfig(
            serial, method, logical_monitors, properties
        )

    def is_apply_allowed(self):
        """Check if ApplyMonitorsConfig is permitted."""
        return bool(self._props.Get(_INTERFACE, "ApplyMonitorsConfigAllowed"))

    def get_backlight(self, connector):
        """Return the current backlight value for the given connector.

        Args:
            connector: The connector name (e.g. 'eDP-1').

        Returns:
            (serial, min, max, value) or None if not found.
        """
        raw = self._props.Get(_INTERFACE, "Backlight")
        serial = int(raw[0])
        for entry in raw[1]:
            if str(entry.get("connector", "")) == connector:
                return serial, int(entry["min"]), int(entry["max"]), int(entry["value"])
        return None

    def get_backlight_serial(self):
        """Return just the current backlight serial number."""
        raw = self._props.Get(_INTERFACE, "Backlight")
        return int(raw[0])

    def set_backlight(self, connector, value):
        """Force-set the backlight value with retry logic.

        Always calls SetBacklight (does not trust current D-Bus value
        since it can diverge from hardware sysfs). Retries until all
        attempts exhausted.

        Args:
            connector: The connector name (e.g. 'eDP-1').
            value: The backlight value to set.
        """
        target = int(value)

        for attempt in range(2):
            time.sleep(0.3)

            bl = self.get_backlight(connector)
            if bl is None:
                continue

            try:
                self._iface.SetBacklight(bl[0], connector, target)
            except dbus.DBusException:
                continue

    def change_backlight(self, serial, output_index, value):
        """Call ChangeBacklight (deprecated) as fallback.

        Args:
            serial: Fresh backlight serial.
            output_index: Index of the output in the physical monitors list.
            value: Target backlight value.

        Returns:
            The new backlight value returned by Mutter.
        """
        return self._iface.ChangeBacklight(serial, output_index, int(value))
