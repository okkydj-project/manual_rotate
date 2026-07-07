"""PySide6 GUI for Screen Rotate."""

import os
import time

from PySide6.QtCore import Qt, QSize, Signal, QThread
from PySide6.QtGui import QIcon, QFont
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QLabel,
    QToolButton,
    QGroupBox,
    QGridLayout,
    QFrame,
    QSizePolicy,
)

from .display import DisplayController, _read_sysfs_brightness
from .monitor import (
    ROTATION_NORMAL,
    ROTATION_90,
    ROTATION_180,
    ROTATION_270,
    ROTATION_LABELS,
)

_ICONS_DIR = os.path.join(os.path.dirname(__file__), "icons")

_ORIENTATIONS = [
    (ROTATION_NORMAL, "landscape", "Landscape", "Normal"),
    (ROTATION_90, "portrait-left", "Portrait Left", "90\u00b0 CCW"),
    (ROTATION_180, "landscape-upside-down", "Upside Down", "180\u00b0"),
    (ROTATION_270, "portrait-right", "Portrait Right", "90\u00b0 CW"),
]

_GRID_POS = {
    ROTATION_NORMAL: (0, 0, 1, 2),
    ROTATION_90:     (1, 0, 1, 1),
    ROTATION_270:    (1, 1, 1, 1),
    ROTATION_180:    (2, 0, 1, 2),
}

_BASE_STYLE = (
    "QToolButton {"
    "  border: 2px solid #ccc;"
    "  border-radius: 8px;"
    "  font-size: 13px;"
    "}"
    "QToolButton:hover {"
    "  border-color: #3584e4;"
    "  background: #f0f7ff;"
    "}"
)

_ACTIVE_STYLE = (
    "QToolButton {"
    "  border: 2px solid #3584e4;"
    "  border-radius: 8px;"
    "  font-size: 13px;"
    "  background: #e8f4fd;"
    "  font-weight: bold;"
    "}"
    "QToolButton:hover {"
    "  border-color: #3584e4;"
    "  background: #e8f4fd;"
    "}"
)


def _icon_path(name):
    return os.path.join(_ICONS_DIR, f"{name}.svg")


class RotationWorker(QThread):
    """Runs display rotation off the main thread so the UI stays responsive."""

    done = Signal(bool, str, dict)

    def __init__(self, rotation):
        super().__init__()
        self._rotation = rotation

    def run(self):
        timing = {}
        t_start = time.time()

        try:
            ctrl = DisplayController()
            t_alloc = time.time()

            ctrl.discover()
            t_discover = time.time()

            builtin = ctrl.get_builtin_monitor()
            lm = ctrl.get_builtin_logical_monitor()
            if builtin is None or lm is None:
                self.done.emit(False, "No built-in display found", timing)
                return

            mode_id = ctrl.get_active_mode()
            if mode_id is None:
                self.done.emit(False, "No active mode found", timing)
                return

            saved_brightness = _read_sysfs_brightness()
            t_info = time.time()

            ambient_was = ctrl._disable_ambient()
            t_ambient_off = time.time()

            monitors = [(builtin.connector, mode_id, {})]
            logical = (
                lm.x, lm.y, lm.scale, self._rotation, lm.primary, monitors,
            )

            ctrl._dbus.apply_monitors_config(ctrl.serial, 1, [logical])
            t_apply = time.time()

            if saved_brightness > 0:
                ctrl._dbus.set_backlight(builtin.connector, saved_brightness)

                time.sleep(0.2)
                actual = _read_sysfs_brightness()
                if abs(actual - saved_brightness) > 10:
                    ctrl._dbus.set_backlight(builtin.connector, saved_brightness)
            t_brightness = time.time()

            if ambient_was:
                ctrl._restore_ambient()
            t_done = time.time()

            timing = {
                "alloc":       int((t_alloc       - t_start)     * 1000),
                "discover":    int((t_discover    - t_alloc)     * 1000),
                "info_gather": int((t_info        - t_discover)  * 1000),
                "ambient_off": int((t_ambient_off - t_info)      * 1000),
                "apply_config":int((t_apply       - t_ambient_off) * 1000),
                "backlight":   int((t_brightness  - t_apply)     * 1000),
                "ambient_on":  int((t_done        - t_brightness)* 1000),
                "total":       int((t_done        - t_start)     * 1000),
            }

            self.done.emit(True, "", timing)

        except Exception as e:
            t_err = time.time()
            timing["total"] = int((t_err - t_start) * 1000)
            self.done.emit(False, str(e), timing)


class ScreenRotateWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._controller = DisplayController()
        self._buttons = {}
        self._busy = False
        self._worker = None
        self._init_ui()
        self._refresh_status()

    def _init_ui(self):
        self.setWindowTitle("Screen Rotate")
        self.setMinimumSize(480, 520)
        self.resize(600, 580)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        info_group = QGroupBox("Current Display")
        info_layout = QGridLayout(info_group)
        info_layout.setSpacing(6)

        self._label_monitor = QLabel()
        self._label_monitor.setFont(QFont("sans-serif", 10))
        info_layout.addWidget(self._label_monitor, 0, 0)

        self._label_scale = QLabel()
        self._label_scale.setFont(QFont("sans-serif", 10))
        info_layout.addWidget(self._label_scale, 0, 1)

        self._label_resolution = QLabel()
        self._label_resolution.setFont(QFont("sans-serif", 10))
        info_layout.addWidget(self._label_resolution, 1, 0)

        self._label_orientation = QLabel()
        self._label_orientation.setFont(QFont("sans-serif", 10, QFont.Weight.Bold))
        info_layout.addWidget(self._label_orientation, 1, 1)

        info_layout.setColumnStretch(0, 1)
        info_layout.setColumnStretch(1, 1)

        layout.addWidget(info_group)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        orient_group = QGroupBox("Rotate Display")
        orient_layout = QGridLayout(orient_group)
        orient_layout.setSpacing(12)
        orient_layout.setContentsMargins(12, 12, 12, 12)

        for col in range(2):
            orient_layout.setColumnStretch(col, 1)
        for row in range(3):
            orient_layout.setRowStretch(row, 1)

        for rot, icon_name, label, subtitle in _ORIENTATIONS:
            row, col, row_span, col_span = _GRID_POS[rot]

            btn = QToolButton()
            btn.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
            btn.setIcon(QIcon(_icon_path(icon_name)))
            btn.setIconSize(QSize(48, 48))
            btn.setText(f"{label}\n{subtitle}")
            btn.setFont(QFont("sans-serif", 11))
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            btn.setMinimumSize(100, 80)
            btn.setStyleSheet(_BASE_STYLE)
            btn.clicked.connect(lambda checked=False, r=rot: self._on_rotate(r))

            orient_layout.addWidget(btn, row, col, row_span, col_span)
            self._buttons[rot] = btn

        layout.addWidget(orient_group, 1)

        self._status_label = QLabel()
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setFont(QFont("sans-serif", 9))
        layout.addWidget(self._status_label)

    def _refresh_status(self):
        try:
            self._controller.discover()
        except Exception as e:
            self._status_label.setText(f"Error: {e}")
            return

        bm = self._controller.get_builtin_monitor()
        lm = self._controller.get_builtin_logical_monitor()

        if bm is None:
            self._label_monitor.setText("Monitor: Not found")
            self._status_label.setText("No built-in display detected")
            return

        self._label_monitor.setText(f"Monitor: {bm.display_name} ({bm.connector})")

        mode = bm.active_mode
        if mode:
            self._label_resolution.setText(
                f"Resolution: {mode.width}x{mode.height} @ {mode.refresh_rate:.1f} Hz"
            )
        else:
            self._label_resolution.setText("Resolution: Unknown")

        self._label_scale.setText(f"Scale: {self._controller.get_current_scale():.2f}")

        current_rot = self._controller.get_current_rotation()
        self._label_orientation.setText(
            f"Orientation: {ROTATION_LABELS.get(current_rot, 'Unknown')}"
        )

        for rot, btn in self._buttons.items():
            if rot == current_rot:
                btn.setEnabled(False)
                btn.setStyleSheet(_ACTIVE_STYLE)
            else:
                btn.setEnabled(True)
                btn.setStyleSheet(_BASE_STYLE)

        self._status_label.setText("")

    def _on_rotate(self, rotation):
        if self._busy:
            return
        self._busy = True

        for btn in self._buttons.values():
            btn.setEnabled(False)

        self._status_label.setText("Rotating\u2026")
        self._status_label.setStyleSheet("color: #3584e4;")

        self._worker = RotationWorker(rotation)
        self._worker.done.connect(self._on_rotation_done)
        self._worker.start()

    def _on_rotation_done(self, success, error, timing):
        self._busy = False
        self._worker = None

        self._print_timing(timing)

        if success:
            self._refresh_status()
            self._status_label.setText("Rotation applied successfully")
            self._status_label.setStyleSheet("color: #2ec27e;")
        else:
            self._status_label.setText(f"Error: {error}")
            self._status_label.setStyleSheet("color: #e01b24;")
            self._refresh_status()

    @staticmethod
    def _print_timing(timing):
        if not timing:
            return
        lines = ["--- Rotation timing (ms) ---"]
        ordered = ["alloc", "discover", "info_gather", "ambient_off",
                   "apply_config", "backlight", "ambient_on", "total"]
        for key in ordered:
            if key in timing:
                label = key.replace("_", " ").title()
                lines.append(f"  {label:18s}: {timing[key]:>5d}")
        lines.append("-----------------------------")
        print("\n".join(lines))
