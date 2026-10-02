#!/usr/bin/env python3
"""Panel de ajustes rápidos One Dark Pro Darker para Waybar."""

import json
import importlib.util
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading
import time

os.environ["GDK_BACKEND"] = "wayland"

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk, GtkLayerShell


SCRIPT_DIR = Path(__file__).resolve().parent
RUNTIME_DIR = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
PID_FILE = RUNTIME_DIR / f"waybar-quick-settings-{os.getuid()}.pid"

CSS = b"""
* { font-family: "JetBrainsMono Nerd Font", monospace; font-size: 13px; }
window { background: transparent; }
.panel {
  background: rgba(35, 39, 46, 0.98);
  border: 1px solid #3e4452;
  border-radius: 18px;
  padding: 16px;
  color: #abb2bf;
}
.header { margin-bottom: 7px; }
.title { color: #d7dae0; font-size: 16px; font-weight: 700; }
.subtitle { color: #5c6370; font-size: 11px; }
.close {
  color: #abb2bf; background: #2c313a; border: 0; border-radius: 10px;
  min-width: 30px; min-height: 30px; padding: 0;
}
.close:hover { color: #23272e; background: #e06c75; }
.tile {
  color: #abb2bf; background: #1e2227; border: 1px solid #3e4452;
  border-radius: 13px; padding: 11px 12px; min-height: 54px;
}
.tile:hover { color: #d7dae0; background: #2c313a; border-color: #61afef; }
.tile-icon { font-size: 18px; min-width: 25px; }
.tile-title { color: #d7dae0; font-weight: 700; }
.tile-detail { color: #7f848e; font-size: 10px; }
.blue .tile-icon { color: #61afef; }
.purple .tile-icon { color: #c678dd; }
.green .tile-icon { color: #98c379; }
.yellow .tile-icon { color: #e5c07b; }
.tile.updating { box-shadow: inset 0 0 0 1px #61afef; }
.tile.power-performance .tile-icon,
.tile.power-performance .tile-detail { color: #e06c75; }
.tile.power-performance:hover {
  background-color: rgba(224, 108, 117, 0.18); border-color: #e06c75;
}
.tile.power-balanced .tile-icon,
.tile.power-balanced .tile-detail { color: #e5c07b; }
.tile.power-balanced:hover {
  background-color: rgba(229, 192, 123, 0.16); border-color: #e5c07b;
}
.tile.power-saver .tile-icon,
.tile.power-saver .tile-detail { color: #98c379; }
.tile.power-saver:hover {
  background-color: rgba(152, 195, 121, 0.16); border-color: #98c379;
}
.section-title { color: #5c6370; font-size: 10px; font-weight: 700; margin-top: 7px; }
.status-row {
  color: #abb2bf; background: #1e2227; border-radius: 10px;
  padding: 8px 11px;
}
.status-icon { color: #56b6c2; font-size: 15px; min-width: 25px; }
.status-muted { color: #7f848e; font-size: 11px; }
.round-action {
  color: #abb2bf; background: #1e2227; border: 1px solid #3e4452;
  border-radius: 11px; padding: 8px 11px;
}
.round-action:hover { color: #23272e; background: #61afef; border-color: #61afef; }
.danger:hover { background: #e06c75; border-color: #e06c75; }
.submenu-header {
  border-bottom: 1px solid #3e4452; margin-bottom: 2px; padding-bottom: 10px;
}
.submenu-back {
  color: #61afef; background: #2c313a; border: 0; border-radius: 10px;
  min-width: 30px; min-height: 30px; padding: 0;
}
.submenu-back:hover { color: #1e2227; background: #61afef; }
.submenu-title { color: #d7dae0; font-size: 15px; font-weight: 700; }
.submenu-caption { color: #5c6370; font-size: 10px; }
.submenu-scroll { background: transparent; border: 0; }
.submenu-list { background: transparent; }
.submenu-item {
  color: #abb2bf; background: transparent; border: 0; border-radius: 9px;
  box-shadow: none; min-height: 34px; padding: 5px 10px;
}
.submenu-item:hover { color: #d7dae0; background-color: #2c313a; }
.submenu-item.loading { color: #61afef; background-color: #2c313a; }
.submenu-item:disabled { color: #5c6370; opacity: 1; }
.submenu-marker { color: #98c379; min-width: 18px; }
.submenu-wifi-icon { color: #61afef; font-size: 16px; min-width: 22px; }
.submenu-arrow { color: #5c6370; }
.submenu-separator { background-color: #3e4452; margin: 5px 9px; min-height: 1px; }
.submenu-message { color: #7f848e; padding: 22px 12px; }
.submenu-error { color: #e06c75; padding: 4px 12px 12px; }
.submenu-fallback {
  color: #abb2bf; background: #1e2227; border: 1px solid #3e4452;
  border-radius: 9px; padding: 8px 10px;
}
.submenu-fallback:hover { color: #d7dae0; border-color: #61afef; }
scrollbar slider {
  background-color: #61afef; border-radius: 5px; min-width: 5px;
}
"""


def output(command):
    try:
        return subprocess.run(
            command, text=True, capture_output=True, timeout=3, check=False
        ).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def script_status(name):
    raw = output([str(SCRIPT_DIR / name)])
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {"text": "No disponible", "tooltip": "", "class": "disabled"}


def clean_text(value):
    return " ".join(str(value).replace("\n", " ").split())


def without_leading_icon(value):
    """Remove a Nerd Font prefix when the row already supplies an icon."""
    text = clean_text(value)
    prefix, separator, remainder = text.partition(" ")
    if separator and any(ord(character) >= 0xE000 for character in prefix):
        return remainder
    return text


def network_status():
    raw = output([
        "env", "LC_ALL=C", "nmcli", "-t", "--escape", "no", "-f",
        "DEVICE,TYPE,STATE,CONNECTION", "device",
    ])
    for line in raw.splitlines():
        parts = line.split(":", 3)
        if len(parts) != 4 or parts[2] != "connected":
            continue
        device, connection_type, _state, connection = parts
        if connection_type == "ethernet":
            return "󰈀", connection
        if connection_type != "wifi":
            continue

        signal = 0
        wifi = output([
            "env", "LC_ALL=C", "nmcli", "-t", "--escape", "no", "-f",
            "IN-USE,SIGNAL,SSID",
            "device", "wifi", "list", "ifname", device,
        ])
        for access_point in wifi.splitlines():
            fields = access_point.split(":", 2)
            if len(fields) == 3 and fields[0].casefold() in ("*", "yes", "sí"):
                try:
                    signal = max(0, min(100, int(fields[1])))
                except ValueError:
                    signal = 0
                if fields[2]:
                    connection = fields[2]
                break

        icons = ("󰤯", "󰤟", "󰤢", "󰤥", "󰤨")
        icon = icons[min(signal // 20, len(icons) - 1)]
        detail = f"{connection} · {signal}%" if signal else connection
        return icon, detail
    return "󰤭", "Sin conexión"


def wifi_signal_levels():
    """Return the strongest current signal for each visible SSID."""
    raw = output([
        "env", "LC_ALL=C", "nmcli", "-t", "--escape", "no", "-f",
        "SIGNAL,SSID", "device", "wifi", "list", "--rescan", "no",
    ])
    levels = {}
    for line in raw.splitlines():
        signal_text, separator, ssid = line.partition(":")
        if not separator or not ssid:
            continue
        try:
            signal = max(0, min(100, int(signal_text)))
        except ValueError:
            continue
        levels[ssid] = max(signal, levels.get(ssid, 0))
    return levels


def wifi_signal_icon(signal):
    icons = ("󰤯", "󰤟", "󰤢", "󰤥", "󰤨")
    return icons[min(max(signal, 0) // 20, len(icons) - 1)]


POWER_PROFILES = ["balanced", "power-saver", "performance"]
POWER_NAMES = {
    "performance": "Rendimiento",
    "balanced": "Equilibrado",
    "power-saver": "Ahorro",
}
POWER_ICONS = {
    "performance": "󰓅",
    "balanced": "󰾅",
    "power-saver": "󰌪",
}


def power_profile():
    profile = output(["powerprofilesctl", "get"])
    return (
        profile,
        POWER_ICONS.get(profile, "󰾅"),
        POWER_NAMES.get(profile, "Predeterminado"),
    )


_APPLET_BACKEND = None


def applet_backend():
    """Load the proven nm-applet/Blueman D-Bus adapter on first use."""
    global _APPLET_BACKEND
    if _APPLET_BACKEND is None:
        path = SCRIPT_DIR / "applet-menu.py"
        spec = importlib.util.spec_from_file_location("waybar_applet_backend", path)
        if spec is None or spec.loader is None:
            raise RuntimeError("No se pudo cargar el backend de conectividad.")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _APPLET_BACKEND = module
    return _APPLET_BACKEND


class EmbeddedAppletMenu(Gtk.Box):
    """NetworkManager/Blueman menu rendered inside Quick Settings."""

    TITLES = {
        "network": ("󰤨", "Redes", "Wi-Fi y conexiones"),
        "vpn": ("󰌷", "VPN", "Túneles y perfiles"),
        "bluetooth": ("󰂯", "Bluetooth", "Dispositivos cercanos"),
    }
    EXTERNAL_ACTIONS = (
        "información de la conexión",
        "editar las conexiones",
        "configurar vpn",
        "conectar con una red inalámbrica oculta",
        "crear una red inalámbrica nueva",
        "enviar archivos al dispositivo",
        "perfiles de audio y entrada",
        "dispositivos",
        "adaptadores",
        "servicios locales",
        "complementos",
        "ayuda",
    )

    def __init__(self, host, kind):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.host = host
        self.kind = kind
        self.backend = None
        self.bus = None
        self.destination = None
        self.menu_path = None
        self.root_id = 0
        self.current_id = 0
        self.current_title = self.TITLES[kind][1]
        self.history = []
        self.refreshing = False
        self.disposed = False
        self.poll_id = 0
        self.last_signature = None
        self.page_serial = 0
        self.wifi_signals = {}
        self.set_size_request(410, -1)
        self.get_style_context().add_class("panel")
        self.connect("destroy", self.on_destroy)

        self.build_header()
        self.page_stack = Gtk.Stack()
        self.page_stack.set_homogeneous(False)
        self.page_stack.set_interpolate_size(True)
        self.page_stack.set_transition_duration(190)
        self.scroll, self.items = self.create_page_widgets()
        self.page_stack.add_named(self.scroll, self.next_page_name())
        self.pack_start(self.page_stack, True, True, 0)
        self.show_message("Cargando opciones…")
        self.load_initial()

    def next_page_name(self):
        self.page_serial += 1
        return f"connectivity-page-{self.page_serial}"

    def create_page_widgets(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_max_content_height(560)
        scroll.set_propagate_natural_height(True)
        scroll.get_style_context().add_class("submenu-scroll")
        items = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        items.get_style_context().add_class("submenu-list")
        scroll.add(items)
        return scroll, items

    def build_header(self):
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=9)
        header.get_style_context().add_class("submenu-header")
        back = Gtk.Button(label="󰁍")
        back.set_tooltip_text("Volver")
        back.get_style_context().add_class("submenu-back")
        back.connect("clicked", self.go_back)
        header.pack_start(back, False, False, 0)

        icon, title, caption = self.TITLES[self.kind]
        glyph = Gtk.Label(label=icon)
        glyph.get_style_context().add_class("tile-icon")
        header.pack_start(glyph, False, False, 0)
        labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.heading = Gtk.Label(label=title, xalign=0)
        self.heading.get_style_context().add_class("submenu-title")
        subtitle = Gtk.Label(label=caption, xalign=0)
        subtitle.get_style_context().add_class("submenu-caption")
        labels.pack_start(self.heading, False, False, 0)
        labels.pack_start(subtitle, False, False, 0)
        header.pack_start(labels, True, True, 0)

        close = Gtk.Button(label="󰅖")
        close.get_style_context().add_class("close")
        close.connect("clicked", lambda *_: self.host.close_panel())
        header.pack_end(close, False, False, 0)
        self.pack_start(header, False, False, 0)

    def clear_items(self):
        for child in self.items.get_children():
            child.destroy()

    def show_message(self, text, error=None):
        self.clear_items()
        message = Gtk.Label(label=text, xalign=0)
        message.set_line_wrap(True)
        message.get_style_context().add_class("submenu-message")
        self.items.pack_start(message, False, False, 0)
        if error:
            detail = Gtk.Label(label=clean_text(error), xalign=0)
            detail.set_line_wrap(True)
            detail.get_style_context().add_class("submenu-error")
            self.items.pack_start(detail, False, False, 0)
            actions = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
            retry = Gtk.Button(label="󰑐  Reintentar")
            retry.get_style_context().add_class("submenu-fallback")
            retry.connect("clicked", lambda *_: self.load_initial())
            classic = Gtk.Button(label="Abrir menú clásico")
            classic.get_style_context().add_class("submenu-fallback")
            classic.connect("clicked", lambda *_: self.host.open_classic_applet(self.kind))
            actions.pack_start(retry, True, True, 0)
            actions.pack_start(classic, True, True, 0)
            self.items.pack_start(actions, False, False, 0)
        self.items.show_all()

    def load_initial(self):
        if self.refreshing or self.disposed:
            return
        self.refreshing = True
        self.show_message("Cargando opciones…")

        def worker():
            try:
                backend = applet_backend()
                bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
                wanted = "blueman" if self.kind == "bluetooth" else "nm-applet"
                destination, path = backend.wait_for_menu(bus, wanted)
                root_id = backend.choose_root(bus, destination, path, self.kind)
                layout = backend.menu_layout(bus, destination, path, root_id, depth=1)
                return backend, bus, destination, path, root_id, layout, None
            except Exception as error:  # D-Bus and applet failures share the fallback UI.
                return None, None, None, None, 0, None, str(error)

        self.host.run_panel_action(worker, self.apply_initial)

    def apply_initial(self, result):
        self.refreshing = False
        if self.disposed:
            return False
        backend, bus, destination, path, root_id, layout, error = result
        if error:
            self.show_message("No se pudo cargar este menú.", error)
            return False
        self.backend = backend
        self.bus = bus
        self.destination = destination
        self.menu_path = path
        self.root_id = root_id
        self.current_id = root_id
        self.history.clear()
        self.render(layout, self.TITLES[self.kind][1])
        if not self.poll_id:
            self.poll_id = GLib.timeout_add(1000, self.poll_current_page)
        return False

    def render(self, layout, title, transition=None, wifi_signals=None):
        if self.disposed:
            return
        if transition is not None:
            previous_scroll = self.scroll
            self.scroll, self.items = self.create_page_widgets()
            self.page_stack.add_named(self.scroll, self.next_page_name())
            self.page_stack.set_transition_type(
                Gtk.StackTransitionType.SLIDE_RIGHT
                if transition == "backward"
                else Gtk.StackTransitionType.SLIDE_LEFT
            )
            self.scroll.show_all()
            self.page_stack.set_visible_child(self.scroll)

            def remove_previous():
                if previous_scroll.get_parent() is self.page_stack:
                    self.page_stack.remove(previous_scroll)
                previous_scroll.destroy()
                return False

            GLib.timeout_add(210, remove_previous)
        self.current_id = layout[0]
        self.current_title = title
        if wifi_signals is not None:
            self.wifi_signals = wifi_signals
        elif not self.is_wifi_page(title):
            self.wifi_signals = {}
        self.heading.set_text(self.backend.translated_label(title))
        self.last_signature = self.backend.layout_signature(layout)
        self.clear_items()
        children = self.backend.display_children(layout)
        if not children:
            self.show_message("No hay opciones disponibles")
            return
        for item in children:
            self.add_item(item)
        self.items.show_all()

    @staticmethod
    def is_wifi_page(title):
        return "redes disponibles" in title.casefold()

    @classmethod
    def opens_external_window(cls, label):
        normalized = label.casefold().strip()
        return any(fragment in normalized for fragment in cls.EXTERNAL_ACTIONS)

    @staticmethod
    def is_htb_profile(label):
        normalized = label.casefold().replace("-", "_").replace(" ", "_")
        return any(marker in normalized for marker in (
            "htb", "hack_the_box", "hackthebox", "machines_",
            "starting_point", "starting_points",
        ))

    @staticmethod
    def row_svg_icon(filename):
        image = Gtk.Image()
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            str(SCRIPT_DIR.parent / "assets" / filename), 18, 18, True,
        )
        image.set_from_pixbuf(pixbuf)
        image.set_size_request(22, 18)
        return image

    def add_item(self, item):
        item_id, properties, children = item
        if properties.get("type") == "separator":
            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            separator.get_style_context().add_class("submenu-separator")
            self.items.pack_start(separator, False, False, 0)
            return

        source_label = properties.get("label", "")
        label_text = self.backend.translated_label(source_label)
        has_submenu = properties.get("children-display") == "submenu" or bool(children)
        toggle_type = properties.get("toggle-type")
        toggle_state = properties.get("toggle-state", 0)
        button = Gtk.Button()
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.set_sensitive(properties.get("enabled", True))
        button.get_style_context().add_class("submenu-item")
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=9)

        icon_name = properties.get("icon-name")
        signal = self.wifi_signals.get(label_text) if self.is_wifi_page(self.current_title) else None
        vpn_icon = None
        if self.kind == "vpn" and not self.opens_external_window(label_text):
            vpn_icon = "htb-vpn.svg" if self.is_htb_profile(label_text) else "vpn.svg"
        elif label_text.casefold() == "conexiones vpn":
            vpn_icon = "vpn.svg"
        if signal is not None:
            icon = Gtk.Label(label=wifi_signal_icon(signal))
            icon.set_tooltip_text(f"Señal: {signal}%")
            icon.get_style_context().add_class("submenu-wifi-icon")
            row.pack_start(icon, False, False, 0)
        elif vpn_icon:
            row.pack_start(self.row_svg_icon(vpn_icon), False, False, 0)
        elif icon_name:
            icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU)
            icon.set_size_request(18, 18)
            row.pack_start(icon, False, False, 0)
        elif toggle_type:
            if toggle_type == "radio":
                marker_text = "●" if toggle_state == 1 else "○"
            else:
                marker_text = "✓" if toggle_state == 1 else " "
            marker = Gtk.Label(label=marker_text)
            marker.get_style_context().add_class("submenu-marker")
            row.pack_start(marker, False, False, 0)

        label = Gtk.Label(label=label_text, xalign=0)
        label.set_line_wrap(True)
        label.set_hexpand(True)
        row.pack_start(label, True, True, 0)
        if vpn_icon and toggle_type and toggle_state == 1:
            active = Gtk.Label(label="✓")
            active.get_style_context().add_class("submenu-marker")
            row.pack_end(active, False, False, 0)
        if has_submenu:
            indicator = Gtk.Stack()
            indicator.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
            indicator.set_transition_duration(100)
            arrow = Gtk.Label(label="›")
            arrow.get_style_context().add_class("submenu-arrow")
            spinner = Gtk.Spinner()
            indicator.add_named(arrow, "arrow")
            indicator.add_named(spinner, "loading")
            indicator.set_visible_child_name("arrow")
            row.pack_end(indicator, False, False, 0)
            button.submenu_indicator = indicator
            button.submenu_spinner = spinner
            button.connect(
                "clicked", self.open_submenu,
                item_id, label_text, source_label,
            )
        else:
            button.connect(
                "clicked", self.activate_item,
                item_id, label_text, source_label,
            )
        button.add(row)
        self.items.pack_start(button, False, False, 0)

    @staticmethod
    def set_submenu_loading(button, loading):
        if button is None:
            return
        context = button.get_style_context()
        if loading:
            context.add_class("loading")
            button.submenu_spinner.start()
            button.submenu_indicator.set_visible_child_name("loading")
        else:
            context.remove_class("loading")
            button.submenu_spinner.stop()
            button.submenu_indicator.set_visible_child_name("arrow")

    def open_submenu(self, button, item_id, title, source_label):
        self.load_page(
            item_id,
            title,
            remember=True,
            transition="forward",
            source_label=source_label,
            loading_button=button,
        )

    def load_page(
        self, item_id, title, remember=False, transition=None,
        source_label=None, loading_button=None,
    ):
        if self.refreshing or self.disposed:
            return
        self.refreshing = True
        previous = (self.current_id, self.current_title)
        parent_id = self.current_id
        self.set_submenu_loading(loading_button, True)

        def worker():
            last_error = None
            layout = None
            resolved_id = item_id
            for attempt in range(4):
                try:
                    if source_label is not None:
                        parent = self.backend.menu_layout(
                            self.bus, self.destination, self.menu_path,
                            parent_id, depth=1,
                        )
                        fallback = None
                        resolved = None
                        for child in self.backend.visible_children(parent):
                            child_id, properties, descendants = child
                            has_submenu = (
                                properties.get("children-display") == "submenu"
                                or bool(descendants)
                            )
                            if child_id == item_id:
                                fallback = child_id
                            if (properties.get("label", "") == source_label
                                    and has_submenu):
                                resolved = child_id
                                break
                        resolved_id = resolved if resolved is not None else fallback
                        if resolved_id is None:
                            raise RuntimeError(
                                f"«{title}» todavía no está disponible."
                            )
                    layout = self.backend.menu_layout(
                        self.bus, self.destination, self.menu_path,
                        resolved_id, depth=1,
                    )
                    # AboutToShow can publish the children just after the first
                    # GetLayout. Give dynamic applets a short settling window.
                    if self.backend.display_children(layout) or attempt == 3:
                        signals = (
                            wifi_signal_levels() if self.is_wifi_page(title) else {}
                        )
                        return layout, signals, None
                except Exception as error:
                    last_error = error
                time.sleep(0.10 * (attempt + 1))
            return None, {}, str(last_error or "El submenú no terminó de cargar.")

        def apply_page(result):
            self.refreshing = False
            if self.disposed:
                return False
            self.set_submenu_loading(loading_button, False)
            layout, signals, error = result
            if error:
                subprocess.Popen(
                    ["notify-send", "-a", "Waybar", "Submenú no disponible",
                     clean_text(error)],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                return False
            if remember:
                self.history.append(previous)
            self.render(layout, title, transition=transition, wifi_signals=signals)
            return False

        self.host.run_panel_action(worker, apply_page)

    def go_back(self, *_args):
        if self.history:
            item_id, title = self.history.pop()
            self.load_page(item_id, title, transition="backward")
        else:
            self.host.show_main_panel()

    def activate_item(self, button, item_id, label_text, source_label):
        if self.refreshing or self.disposed:
            return
        self.refreshing = True
        current_id = self.current_id
        current_title = self.current_title
        close_after_activation = self.opens_external_window(label_text)
        button.get_style_context().add_class("loading")

        def resolve_action_id():
            """Resolve the current D-Bus ID from the stable source label."""
            parent = self.backend.menu_layout(
                self.bus, self.destination, self.menu_path,
                current_id, depth=1,
            )
            fallback = None
            for child in self.backend.visible_children(parent):
                child_id, properties, descendants = child
                has_submenu = (
                    properties.get("children-display") == "submenu"
                    or bool(descendants)
                )
                if child_id == item_id and not has_submenu:
                    fallback = child_id
                if (properties.get("label", "") == source_label
                        and not has_submenu):
                    return child_id
            if fallback is not None:
                return fallback
            raise RuntimeError(f"«{label_text}» ya no está disponible.")

        def send_event(resolved_id):
            timestamp = int(time.monotonic() * 1000) & 0xffffffff
            self.backend.call(
                self.bus, self.destination, self.menu_path,
                self.backend.DBUSMENU, "Event",
                GLib.Variant(
                    "(isvu)",
                    (resolved_id, "clicked", GLib.Variant("i", 0), timestamp),
                ),
            )

        def worker():
            panel_hidden = False
            try:
                resolved_id = resolve_action_id()
                if close_after_activation:
                    hidden = threading.Event()

                    def hide_panel():
                        if not self.disposed:
                            self.host.hide()
                        hidden.set()
                        return False

                    GLib.idle_add(hide_panel)
                    panel_hidden = hidden.wait(0.75)
                try:
                    send_event(resolved_id)
                except Exception as first_error:
                    message = str(first_error).casefold()
                    stale_id = any(marker in message for marker in (
                        "id supplied", "does not refer", "menu item",
                        "invalid id", "unknown id",
                    ))
                    if not stale_id:
                        raise
                    # The applet rebuilt its menu between resolve and Event.
                    send_event(resolve_action_id())
                if close_after_activation:
                    return None, {}, None, panel_hidden
                time.sleep(0.25)
                layout = self.backend.menu_layout(
                    self.bus, self.destination, self.menu_path, current_id, depth=1,
                )
                signals = (
                    wifi_signal_levels()
                    if self.is_wifi_page(current_title) else {}
                )
                return layout, signals, None, panel_hidden
            except Exception as error:
                return None, {}, str(error), panel_hidden

        def applied(result):
            self.refreshing = False
            if self.disposed:
                return False
            button.get_style_context().remove_class("loading")
            layout, signals, error, panel_hidden = result
            if close_after_activation:
                if panel_hidden:
                    self.host.show_main_panel()
                if error:
                    subprocess.Popen(
                        ["notify-send", "-a", "Waybar",
                         "No se pudo abrir la opción", clean_text(error)],
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True,
                    )
                return False
            if layout is not None and current_id == self.current_id:
                self.render(layout, current_title, wifi_signals=signals)
            elif error:
                self.show_message("No se pudo ejecutar la opción.", error)
            self.host.load_statuses()
            return False

        self.host.run_panel_action(worker, applied)

    def poll_current_page(self):
        if self.disposed:
            self.poll_id = 0
            return False
        if self.refreshing or not self.host.get_visible():
            return True
        self.refreshing = True
        current_id = self.current_id
        current_title = self.current_title

        def worker():
            try:
                layout = self.backend.menu_layout(
                    self.bus, self.destination, self.menu_path, current_id, depth=1,
                )
                signals = (
                    wifi_signal_levels() if self.is_wifi_page(current_title) else {}
                )
                return layout, signals, None
            except Exception as error:
                return None, {}, str(error)

        def applied(result):
            self.refreshing = False
            if self.disposed:
                return False
            layout, signals, _error = result
            if (layout is not None and current_id == self.current_id
                    and (self.backend.layout_signature(layout) != self.last_signature
                         or signals != self.wifi_signals)):
                self.render(layout, self.current_title, wifi_signals=signals)
                self.host.load_statuses()
            return False

        self.host.run_panel_action(worker, applied)
        return True

    def dispose(self):
        self.disposed = True
        if self.poll_id:
            GLib.source_remove(self.poll_id)
            self.poll_id = 0

    def on_destroy(self, *_args):
        self.dispose()


class QuickSettings(Gtk.Window):
    def __init__(self, persistent=False):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.persistent = persistent
        self.destroyed = False
        self.network_refreshing = False
        self.power_changing = False
        self.set_decorated(False)
        self.set_app_paintable(True)
        self.connect("destroy", self.on_destroy)
        self.connect("key-press-event", self.on_key)

        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.EXCLUSIVE)
        GtkLayerShell.set_namespace(self, "waybar-quick-settings")
        for edge in (GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.RIGHT,
                     GtkLayerShell.Edge.BOTTOM, GtkLayerShell.Edge.LEFT):
            GtkLayerShell.set_anchor(self, edge, True)
        GtkLayerShell.set_exclusive_zone(self, -1)

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        backdrop = Gtk.EventBox()
        backdrop.set_visible_window(False)
        backdrop.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        backdrop.connect("button-press-event", lambda *_: self.close_panel())
        self.add(backdrop)

        guard = Gtk.EventBox()
        guard.set_visible_window(False)
        guard.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        guard.connect("button-press-event", lambda *_: True)
        guard.set_halign(Gtk.Align.END)
        guard.set_valign(Gtk.Align.START)
        guard.set_margin_top(54)
        guard.set_margin_end(8)
        backdrop.add(guard)

        self.panel_stack = Gtk.Stack()
        self.panel_stack.set_homogeneous(False)
        self.panel_stack.set_interpolate_size(True)
        self.panel_stack.set_transition_duration(180)
        guard.add(self.panel_stack)
        self.main_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=9)
        self.main_panel.set_size_request(410, -1)
        self.main_panel.get_style_context().add_class("panel")
        self.panel_stack.add_named(self.main_panel, "main")
        self.internal_page = None
        self.build_header(self.main_panel)
        self.build_tiles(self.main_panel)
        self.build_status(self.main_panel)
        self.build_actions(self.main_panel)
        self.load_statuses()

    def build_header(self, panel):
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header.get_style_context().add_class("header")
        titles = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        title = Gtk.Label(label="Ajustes rápidos", xalign=0)
        title.get_style_context().add_class("title")
        subtitle = Gtk.Label(label="Sistema y conectividad", xalign=0)
        subtitle.get_style_context().add_class("subtitle")
        titles.pack_start(title, False, False, 0)
        titles.pack_start(subtitle, False, False, 0)
        header.pack_start(titles, True, True, 0)
        close = Gtk.Button(label="󰅖")
        close.get_style_context().add_class("close")
        close.connect("clicked", lambda *_: self.close_panel())
        header.pack_end(close, False, False, 0)
        panel.pack_start(header, False, False, 0)

    def tile(self, icon, title, detail, color, callback, svg=None):
        button = Gtk.Button()
        button.set_hexpand(True)
        button.set_vexpand(True)
        button.get_style_context().add_class("tile")
        button.get_style_context().add_class(color)
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=9)
        if svg:
            glyph = Gtk.Image()
            self.set_svg(glyph, svg)
        else:
            glyph = Gtk.Label(label=icon)
        glyph.set_valign(Gtk.Align.CENTER)
        glyph.get_style_context().add_class("tile-icon")
        row.pack_start(glyph, False, False, 0)
        labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        labels.set_valign(Gtk.Align.CENTER)
        heading = Gtk.Label(label=title, xalign=0)
        heading.get_style_context().add_class("tile-title")
        info = Gtk.Label(label=detail, xalign=0)
        info.set_ellipsize(3)
        info.get_style_context().add_class("tile-detail")
        labels.pack_start(heading, False, False, 0)
        labels.pack_start(info, False, False, 0)
        row.pack_start(labels, True, True, 0)
        button.add(row)
        button.status_icon = glyph
        button.status_detail = info
        button.connect("clicked", callback)
        return button

    def set_svg(self, image, name):
        width = 25 if name == "vpn-mixed.svg" else 18
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            str(SCRIPT_DIR.parent / "assets" / name), width, 18, True,
        )
        image.set_from_pixbuf(pixbuf)
        image.set_size_request(25, 18)

    def build_tiles(self, panel):
        grid = Gtk.Grid(column_spacing=8, row_spacing=8)
        grid.set_column_homogeneous(True)
        grid.set_row_homogeneous(True)
        self.network_tile = self.tile(
            "󰤯", "Red", "Comprobando…", "blue",
            lambda *_: self.open_applet("network"),
        )
        grid.attach(self.network_tile, 0, 0, 1, 1)
        self.bluetooth_tile = self.tile(
            "󰂯", "Bluetooth", "Comprobando…", "purple",
            lambda *_: self.open_applet("bluetooth"),
        )
        grid.attach(self.bluetooth_tile, 1, 0, 1, 1)
        self.vpn_tile = self.tile(
            "", "VPN", "Comprobando…", "green",
            lambda *_: self.open_applet("vpn"),
            svg="vpn.svg",
        )
        grid.attach(self.vpn_tile, 0, 1, 1, 1)
        self.power_profile_name = "balanced"
        self.power_tile = self.tile(
            "󰾅", "Energía", "Comprobando…", "power-balanced",
            lambda *_: self.cycle_power(self.power_profile_name),
        )
        grid.attach(self.power_tile, 1, 1, 1, 1)
        panel.pack_start(grid, False, False, 0)
        GLib.timeout_add_seconds(3, self.refresh_visible_statuses)

    def apply_network(self, result):
        self.network_refreshing = False
        if self.destroyed:
            return False
        icon, detail = result
        self.network_tile.status_icon.set_text(icon)
        self.network_tile.status_detail.set_text(detail)
        return False

    def start_network_refresh(self):
        if (not self.network_refreshing and not self.destroyed
                and (not self.persistent or self.get_visible())):
            self.network_refreshing = True
            self.run_async(network_status, self.apply_network)
        return GLib.SOURCE_CONTINUE

    def refresh_visible_statuses(self):
        if not self.destroyed and (not self.persistent or self.get_visible()):
            self.load_statuses()
        return GLib.SOURCE_CONTINUE

    def build_status(self, panel):
        label = Gtk.Label(label="INFORMACIÓN", xalign=0)
        label.get_style_context().add_class("section-title")
        panel.pack_start(label, False, False, 0)
        self.private_ip_row = self.status_row(panel, "󰩟", "IP privada", "Comprobando…")

    def status_row(self, panel, icon, title, detail):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        row.get_style_context().add_class("status-row")
        glyph = Gtk.Label(label=icon)
        glyph.get_style_context().add_class("status-icon")
        name = Gtk.Label(label=title, xalign=0)
        name.set_hexpand(True)
        value = Gtk.Label(label=detail, xalign=1)
        value.get_style_context().add_class("status-muted")
        row.pack_start(glyph, False, False, 0)
        row.pack_start(name, True, True, 0)
        row.pack_end(value, False, False, 0)
        panel.pack_start(row, False, False, 0)
        row.status_detail = value
        return row

    def run_async(self, worker, callback):
        def task():
            result = worker()
            GLib.idle_add(callback, result)

        threading.Thread(target=task, daemon=True).start()

    def run_panel_action(self, worker, callback):
        """Run an in-panel update without changing the panel visibility."""
        if not self.destroyed:
            self.run_async(worker, callback)

    def load_statuses(self):
        self.start_network_refresh()
        self.run_async(lambda: script_status("bluetooth-status.sh"), self.apply_bluetooth)
        self.run_async(lambda: script_status("htb-vpn.sh"), self.apply_vpn)
        self.run_async(power_profile, self.apply_power)
        self.run_async(lambda: script_status("private-ip.sh"), self.apply_private_ip)

    def apply_bluetooth(self, status):
        if not self.destroyed:
            self.bluetooth_tile.status_icon.set_text(clean_text(status.get("text", "󰂯")))
            self.bluetooth_tile.status_detail.set_text(clean_text(status.get("tooltip", "No disponible")))
        return False

    def apply_vpn(self, status):
        if not self.destroyed:
            status_class = clean_text(status.get("class", ""))
            if status_class == "connecting-htb":
                icon = "htb-vpn-connecting.svg"
            elif status_class == "connecting-other":
                icon = "vpn-connecting.svg"
            elif status_class == "htb":
                icon = "htb-vpn.svg"
            elif status_class == "mixed":
                icon = "vpn-mixed.svg"
            else:
                icon = "vpn.svg"
            self.set_svg(self.vpn_tile.status_icon, icon)
            detail = clean_text(status.get("text", "")) or "Desconectada"
            self.vpn_tile.status_detail.set_text(detail)
        return False

    def apply_power(self, status):
        if not self.destroyed and not self.power_changing:
            self.update_power_display(status)
        return False

    def update_power_display(self, status):
        profile, icon, name = status
        self.power_profile_name = profile
        self.power_tile.status_icon.set_text(icon)
        self.power_tile.status_detail.set_text(name)
        style = self.power_tile.get_style_context()
        for state_class in (
            "power-performance", "power-balanced", "power-saver"
        ):
            style.remove_class(state_class)
        style.add_class({
            "performance": "power-performance",
            "balanced": "power-balanced",
            "power-saver": "power-saver",
        }.get(profile, "power-balanced"))

    def finish_power_change(self, status):
        self.power_changing = False
        self.power_tile.get_style_context().remove_class("updating")
        if not self.destroyed:
            self.update_power_display(status)
        return False

    def apply_private_ip(self, status):
        if not self.destroyed:
            self.private_ip_row.status_detail.set_text(
                without_leading_icon(status.get("text", "Sin IP"))
            )
        return False

    def build_actions(self, panel):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        actions = (
            ("󰓃  Audio", [str(SCRIPT_DIR / "audio-panel-toggle.sh")], False),
            ("󰍜  Archivos", ["thunar"], False),
            ("󰌾  Bloquear", ["hyprlock"], False),
            ("󰐥", ["wlogout", "-n", "-b", "3", "-c", "20", "-r", "20",
                     "-L", "340", "-R", "340", "-T", "250", "-B", "250"], True),
        )
        for text, command, danger in actions:
            button = Gtk.Button(label=text)
            button.get_style_context().add_class("round-action")
            if danger:
                button.get_style_context().add_class("danger")
            button.connect("clicked", lambda _b, cmd=command: self.spawn_external(cmd))
            row.pack_start(button, True, True, 0)
        panel.pack_start(row, False, False, 0)

    def open_applet(self, kind):
        if self.internal_page is not None:
            self.panel_stack.remove(self.internal_page)
            self.internal_page.destroy()
        self.internal_page = EmbeddedAppletMenu(self, kind)
        self.panel_stack.add_named(self.internal_page, "connectivity")
        self.panel_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT)
        self.internal_page.show_all()
        self.panel_stack.set_visible_child(self.internal_page)

    def show_main_panel(self):
        page = self.internal_page
        self.panel_stack.set_transition_type(Gtk.StackTransitionType.SLIDE_RIGHT)
        self.panel_stack.set_visible_child(self.main_panel)
        self.internal_page = None
        if page is not None:
            page.dispose()

            def remove_page():
                if page.get_parent() is self.panel_stack:
                    self.panel_stack.remove(page)
                page.destroy()
                return False

            GLib.timeout_add(190, remove_page)
        self.load_statuses()

    def open_classic_applet(self, kind):
        self.spawn_external([str(SCRIPT_DIR / "applet-menu.py"), kind])

    def spawn_external(self, command):
        """Launch a separate interface; external interfaces replace this panel."""
        self.close_panel()
        try:
            subprocess.Popen(
                command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, close_fds=True, start_new_session=True,
            )
        except OSError:
            pass

    def cycle_power(self, current):
        if self.power_changing:
            return

        next_profile = (
            POWER_PROFILES[(POWER_PROFILES.index(current) + 1) % len(POWER_PROFILES)]
            if current in POWER_PROFILES else "balanced"
        )
        self.power_changing = True
        self.power_tile.get_style_context().add_class("updating")
        self.update_power_display((
            next_profile,
            POWER_ICONS[next_profile],
            POWER_NAMES[next_profile],
        ))

        def change_profile():
            try:
                subprocess.run(
                    ["powerprofilesctl", "set", next_profile],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                    check=False,
                )
            except (OSError, subprocess.TimeoutExpired):
                pass
            return power_profile()

        # Regla del panel: una acción interna actualiza en vivo y nunca lo cierra.
        self.run_panel_action(change_profile, self.finish_power_change)

    def close_panel(self):
        if self.internal_page is not None:
            self.show_main_panel()
        if self.persistent:
            self.hide()
        else:
            self.destroy()

    def toggle_panel(self):
        if self.get_visible():
            self.close_panel()
        else:
            self.show_all()
            self.panel_stack.set_visible_child(self.main_panel)
            self.load_statuses()
            self.present()
        return False

    def on_key(self, _window, event):
        if event.keyval == Gdk.KEY_Escape:
            if self.internal_page is not None:
                self.internal_page.go_back()
            else:
                self.close_panel()
            return True
        return False

    def on_destroy(self, *_args):
        self.destroyed = True
        try:
            if PID_FILE.exists() and PID_FILE.read_text().strip() == str(os.getpid()):
                PID_FILE.unlink()
        except OSError:
            pass
        Gtk.main_quit()


def running_instance():
    try:
        pid = int(PID_FILE.read_text().strip())
        os.kill(pid, 0)
        return pid
    except (OSError, ValueError):
        try:
            PID_FILE.unlink()
        except OSError:
            pass
        return None


if __name__ == "__main__":
    daemon_mode = "--daemon" in sys.argv
    show_initially = "--show" in sys.argv
    existing_pid = running_instance()
    if existing_pid is not None:
        if not daemon_mode:
            os.kill(existing_pid, signal.SIGUSR1)
        sys.exit(0)
    PID_FILE.write_text(str(os.getpid()))
    window = QuickSettings(persistent=daemon_mode)
    window.show_all()
    if daemon_mode and not show_initially:
        window.hide()
    signal.signal(signal.SIGUSR1, lambda *_: GLib.idle_add(window.toggle_panel))
    signal.signal(signal.SIGTERM, lambda *_: GLib.idle_add(window.destroy))
    Gtk.main()
