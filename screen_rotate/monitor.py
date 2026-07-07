"""Monitor discovery and representation."""

from dataclasses import dataclass, field
from typing import Optional

import dbus


ROTATION_NORMAL = 0
ROTATION_90 = 1
ROTATION_180 = 2
ROTATION_270 = 3

ROTATION_LABELS = {
    ROTATION_NORMAL: "Landscape",
    ROTATION_90: "Portrait Left",
    ROTATION_180: "Landscape Upside Down",
    ROTATION_270: "Portrait Right",
}


@dataclass
class Mode:
    mode_id: str
    width: int
    height: int
    refresh_rate: float
    supported_scales: list = field(default_factory=list)
    is_current: bool = False
    is_preferred: bool = False


@dataclass
class PhysicalMonitor:
    connector: str
    vendor: str
    product: str
    serial: str
    display_name: str
    is_builtin: bool
    modes: list = field(default_factory=list)
    active_mode: Optional[Mode] = None


@dataclass
class LogicalMonitor:
    x: int
    y: int
    scale: float
    rotation: int
    primary: bool
    monitor_connectors: list = field(default_factory=list)


def parse_physical_monitor(raw):
    """Parse a physical monitor tuple from D-Bus GetCurrentState."""
    ident = raw[0]
    modes_raw = raw[1]
    props = dict(raw[2])

    connector, vendor, product, serial = str(ident[0]), str(ident[1]), str(ident[2]), str(ident[3])

    modes = []
    active_mode = None
    for m in modes_raw:
        mode = Mode(
            mode_id=str(m[0]),
            width=int(m[1]),
            height=int(m[2]),
            refresh_rate=float(m[3]),
            supported_scales=[float(s) for s in m[5]],
            is_current=bool(m[6].get("is-current", False)),
            is_preferred=bool(m[6].get("is-preferred", False)),
        )
        modes.append(mode)
        if mode.is_current:
            active_mode = mode

    return PhysicalMonitor(
        connector=connector,
        vendor=vendor,
        product=product,
        serial=serial,
        display_name=str(props.get("display-name", "")),
        is_builtin=bool(props.get("is-builtin", False)),
        modes=modes,
        active_mode=active_mode,
    )


def parse_logical_monitor(raw):
    """Parse a logical monitor tuple from D-Bus GetCurrentState."""
    x = int(raw[0])
    y = int(raw[1])
    scale = float(raw[2])
    rotation = int(raw[3])
    primary = bool(raw[4])
    monitor_connectors = [str(mc[0]) for mc in raw[5]]

    return LogicalMonitor(
        x=x,
        y=y,
        scale=scale,
        rotation=rotation,
        primary=primary,
        monitor_connectors=monitor_connectors,
    )
