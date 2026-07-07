# Screen Rotate GUI for Ubuntu (Wayland)

## Objective

Create a lightweight native desktop application that allows the user to manually rotate the internal display on Ubuntu 26.04 running GNOME 50 and Wayland.

The application is intended to replace the broken GNOME auto-rotation feature with a reliable manual solution.

The user should never need to use the terminal after installation.

---

# Requirements

## Platform

* Ubuntu 26.04 LTS
* GNOME 50
* Wayland
* Python 3
* PySide6 (preferred) or GTK4
* Official Mutter DisplayConfig D-Bus API only

Do NOT use:

* xrandr
* wlr-randr
* swaymsg
* X11 APIs

---

# Development Process

Before writing production code:

1. Inspect the live `org.gnome.Mutter.DisplayConfig` interface.
2. Discover all connected monitors dynamically.
3. Determine the current monitor configuration.
4. Verify that rotation is supported.
5. Build the implementation from the discovered API rather than hardcoded values.

Pause after discovery and present a plan before implementing.

---

# User Interface

Create a clean native desktop application.

Show:

* Current monitor
* Current orientation
* Current resolution
* Current scaling

Provide four large buttons:

* Landscape
* Portrait Left
* Portrait Right
* Landscape Upside Down

Each button should include an icon and descriptive label.

Rotating the display should require only one click.

---

# Behaviour

* Detect the current orientation when the application starts.
* Highlight the active orientation.
* Disable the button for the current orientation.
* Apply changes immediately.
* Show a success or error message if the operation succeeds or fails.

---

# Monitor Handling

Automatically discover the active internal display.

Do not hardcode:

* eDP-1
* connector names
* monitor IDs
* logical monitor IDs

Support future monitor changes by rediscovering the display configuration each time the application starts.

---

# Architecture

Organize the project into modules:

screen_rotate/

├── main.py
├── gui.py
├── display.py
├── dbus.py
├── monitor.py
├── icons/
├── resources/
├── README.md
├── install.sh
├── uninstall.sh
├── requirements.txt
└── screen-rotate.desktop

---

# Installation

Provide an install script that:

* Installs Python dependencies.
* Creates a launcher in `~/.local/share/applications`.
* Copies icons.
* Makes the application searchable from the GNOME Activities menu.
* Optionally allows the user to pin it to Favorites.

---

# User Experience

The application should:

* Launch in under one second.
* Require no terminal.
* Feel like a native Ubuntu utility.
* Follow GNOME Human Interface Guidelines where practical.

---

# Error Handling

If the display configuration changes while the application is open:

* Rediscover the monitor.
* Continue functioning without requiring a restart.

If Mutter rejects a rotation request:

* Display a clear error message.
* Do not crash.

---

# Documentation

Generate a comprehensive README covering:

* Installation
* Usage
* Architecture
* Troubleshooting
* Known limitations
* How to uninstall

---

# Deliverables

Provide:

* Complete source code
* Install script
* Uninstall script
* Desktop launcher
* Application icon
* README
* Requirements file

The final application should behave like a native Ubuntu desktop utility that lets the user rotate the display with a single click.

