#!/usr/bin/env python3
"""Selector visual de ventanas con la estética de Rofi."""

import json
import os
import re
import sys

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gdk, Gio, GLib, Gtk, GtkLayerShell


CSS = b"""
* {
    font-family: 'JetBrainsMono Nerd Font';
    font-size: 11pt;
    color: #abb2bf;
}
window { background-color: transparent; }
#panel {
    background-color: rgba(35, 39, 46, 0.97);
    border: 2px solid #3e4452;
    border-radius: 16px;
    padding: 16px;
}
.window-cell {
    background-color: transparent;
    border: 2px solid transparent;
    border-radius: 10px;
    padding: 14px;
    min-width: 96px;
    min-height: 96px;
}
.window-cell.selected {
    background-color: #2c313a;
    border-color: #61afef;
}
"""


def normalized(value):
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


class AltTabWindow(Gtk.Window):
    def __init__(self, state_file, ready_file):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.state_file = state_file
        self.ready_file = ready_file
        self.last_state = None
        self.cells = []
        self.app_icons = self.build_icon_index()

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.set_decorated(False)
        self.set_app_paintable(True)
        self.set_position(Gtk.WindowPosition.CENTER)
        visual = self.get_screen().get_rgba_visual()
        if visual:
            self.set_visual(visual)

        if GtkLayerShell.is_supported():
            GtkLayerShell.init_for_window(self)
            GtkLayerShell.set_namespace(self, "rofi-alt-tab")
            GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
            GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.NONE)

        self.panel = Gtk.Grid(column_spacing=7, row_spacing=7)
        self.panel.set_name("panel")
        self.add(self.panel)
        self.connect("destroy", Gtk.main_quit)
        self.connect("map-event", self.on_map)

        if not self.refresh(force=True):
            GLib.idle_add(Gtk.main_quit)
            return
        self.show_all()
        GLib.timeout_add(30, self.refresh)

    def on_map(self, *_):
        # Dar tiempo a que el compositor presente el primer frame. El
        # controlador cambiará el foco justo después de esta confirmación.
        GLib.timeout_add(25, self.mark_ready)
        return False

    def mark_ready(self):
        try:
            with open(self.ready_file, "w", encoding="utf-8") as handle:
                handle.write("ready\n")
        except OSError:
            pass
        return False

    @staticmethod
    def build_icon_index():
        index = {}
        for app in Gio.AppInfo.get_all():
            icon = app.get_icon()
            if icon is None:
                continue
            values = [app.get_id(), app.get_executable(), app.get_name()]
            if isinstance(app, Gio.DesktopAppInfo):
                values.extend([
                    app.get_string("StartupWMClass"),
                    app.get_string("X-GNOME-WMClass"),
                ])
            for value in values:
                key = normalized((value or "").removesuffix(".desktop"))
                if key:
                    index.setdefault(key, icon)
        return index

    def icon_for(self, window):
        values = [window.get("class", ""), window.get("initialClass", "")]
        keys = [normalized(value.removesuffix(".desktop")) for value in values]
        for key in keys:
            if key in self.app_icons:
                return self.app_icons[key]
        for key in keys:
            if not key:
                continue
            for app_key, icon in self.app_icons.items():
                if app_key.endswith(key) or key.endswith(app_key):
                    return icon
        return Gio.ThemedIcon.new("application-x-executable")

    def rebuild(self, windows):
        for child in self.panel.get_children():
            self.panel.remove(child)
        self.cells = []

        columns = min(5, max(1, len(windows)))
        for position, window in enumerate(windows):
            cell = Gtk.EventBox()
            cell.get_style_context().add_class("window-cell")
            image = Gtk.Image.new_from_gicon(self.icon_for(window), Gtk.IconSize.DIALOG)
            image.set_pixel_size(96)
            cell.add(image)
            self.panel.attach(cell, position % columns, position // columns, 1, 1)
            self.cells.append(cell)
        self.panel.show_all()

    def refresh(self, force=False):
        try:
            with open(self.state_file, encoding="utf-8") as handle:
                state = json.load(handle)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            self.destroy()
            return False

        signature = json.dumps(state, ensure_ascii=False, sort_keys=True)
        if not force and signature == self.last_state:
            return True
        old_windows = self.last_state and json.loads(self.last_state).get("windows")
        windows = state.get("windows", [])
        if force or old_windows != windows:
            self.rebuild(windows)

        selected = state.get("index", 0)
        for position, cell in enumerate(self.cells):
            context = cell.get_style_context()
            if position == selected:
                context.add_class("selected")
            else:
                context.remove_class("selected")
        self.last_state = signature
        return True


def main():
    if len(sys.argv) != 3 or not os.path.isfile(sys.argv[1]):
        return 1
    AltTabWindow(sys.argv[1], sys.argv[2])
    Gtk.main()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
