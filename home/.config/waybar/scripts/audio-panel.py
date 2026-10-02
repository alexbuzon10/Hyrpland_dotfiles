#!/usr/bin/env python3
"""Panel de audio One Dark Pro Darker para Waybar."""

import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import threading

os.environ["GDK_BACKEND"] = "wayland"

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Gdk", "3.0")
gi.require_version("GtkLayerShell", "0.1")
from gi.repository import Gdk, GdkPixbuf, GLib, Gtk, GtkLayerShell


SCRIPT_DIR = Path(__file__).resolve().parent
WAYBAR_DIR = SCRIPT_DIR.parent
ASSETS_DIR = WAYBAR_DIR / "assets"
RUNTIME_DIR = Path(os.environ.get("XDG_RUNTIME_DIR", "/tmp"))
PID_FILE = RUNTIME_DIR / f"waybar-audio-panel-{os.getuid()}.pid"
BOOST_FILE = WAYBAR_DIR / "audio-boost"

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
.header { margin-bottom: 5px; }
.title { color: #d7dae0; font-size: 16px; font-weight: 700; }
.subtitle { color: #5c6370; font-size: 11px; }
.close {
  color: #abb2bf; background: #2c313a; border: 0; border-radius: 10px;
  min-width: 30px; min-height: 30px; padding: 0;
}
.close:hover { color: #23272e; background: #e06c75; }
.section {
  background: #1e2227;
  border: 1px solid #3e4452;
  border-radius: 13px;
  padding: 12px;
}
.section-title { color: #d7dae0; font-weight: 700; }
.section-icon { color: #61afef; font-size: 17px; min-width: 24px; }
.input .section-icon { color: #c678dd; }
.device-label { color: #7f848e; font-size: 10px; }
combobox button {
  color: #d7dae0; background: #282c34; border: 1px solid #3e4452;
  border-radius: 9px; padding: 6px 9px;
}
combobox button:hover { border-color: #61afef; background: #2c313a; }
combobox window menu { background: #23272e; border: 1px solid #3e4452; }
combobox menuitem { color: #abb2bf; padding: 7px 10px; }
combobox menuitem:hover { color: #d7dae0; background: #2c313a; }
.volume-icon { color: #abb2bf; font-size: 17px; min-width: 24px; }
.percent { color: #d7dae0; font-weight: 700; min-width: 46px; }
.mute {
  color: #abb2bf; background: #282c34; border: 1px solid #3e4452;
  border-radius: 9px; min-width: 34px; min-height: 30px; padding: 0;
}
.mute:hover { border-color: #61afef; color: #61afef; }
.mute.active { color: #e06c75; border-color: #e06c75; }
scale { padding: 0; }
scale trough {
  min-height: 5px; border-radius: 999px; background: #3e4452;
}
scale highlight { min-height: 5px; border-radius: 999px; background: #61afef; }
.input scale highlight { background: #c678dd; }
scale slider {
  min-width: 12px; min-height: 12px; margin: -5px;
  border-radius: 50%; background: #d7dae0; border: 0;
}
.boosted scale highlight { background: #d19a66; }
.boosted scale slider { background: #d19a66; }
.boost-row {
  color: #abb2bf; background: #1e2227; border-radius: 10px;
  padding: 8px 10px;
}
.boost-title { color: #d7dae0; }
.boost-detail { color: #7f848e; font-size: 10px; }
switch { background: #3e4452; border-radius: 999px; }
switch:checked { background: #d19a66; }
switch slider { background: #d7dae0; border-radius: 50%; }
.advanced-audio {
  color: #abb2bf; background: #1e2227; border: 1px solid #3e4452;
  border-radius: 12px; padding: 9px 12px; box-shadow: none;
}
.advanced-audio:hover {
  color: #d7dae0; background: #2c313a; border-color: #61afef;
}
.advanced-icon { color: #61afef; font-size: 17px; min-width: 25px; }
.advanced-title { color: #d7dae0; font-weight: 700; }
.advanced-detail { color: #7f848e; font-size: 10px; }
.advanced-arrow { color: #5c6370; font-size: 16px; }
.empty { color: #7f848e; padding: 8px; }
"""


def command_output(command):
    environment = os.environ.copy()
    environment["LC_ALL"] = "C"
    try:
        return subprocess.run(
            command, text=True, encoding="utf-8", errors="replace",
            capture_output=True, timeout=4, check=False, env=environment,
        ).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def pactl_json(*arguments):
    raw = command_output(["pactl", "-f", "json", *arguments])
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {} if arguments and arguments[-1] == "info" else []


def volume_percent(device):
    channels = device.get("volume", {})
    values = []
    for channel in channels.values():
        raw = str(channel.get("value_percent", "0%")).rstrip("%")
        try:
            values.append(float(raw))
        except ValueError:
            pass
    return round(sum(values) / len(values)) if values else 0


def device_label(device):
    properties = device.get("properties") or {}
    candidates = (
        device.get("description"),
        properties.get("device.description"),
        properties.get("device.alias"),
        properties.get("node.description"),
    )
    for candidate in candidates:
        if candidate and candidate != "(null)":
            return str(candidate)
    name = str(device.get("name", "Dispositivo"))
    return name.rsplit(".", 1)[-1].replace("-", " ").replace("_", " ").title()


def audio_snapshot():
    info = pactl_json("info")
    sinks = pactl_json("list", "sinks")
    sources = [
        source for source in pactl_json("list", "sources")
        if not source.get("monitor_source")
        and not str(source.get("name", "")).endswith(".monitor")
    ]
    return {
        "default_sink": info.get("default_sink_name", ""),
        "default_source": info.get("default_source_name", ""),
        "sinks": sinks,
        "sources": sources,
    }


def run_detached(command):
    try:
        subprocess.Popen(
            command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, close_fds=True, start_new_session=True,
        )
    except OSError:
        pass


class AudioPanel(Gtk.Window):
    def __init__(self, persistent=False):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.persistent = persistent
        self.destroyed = False
        self.internal_update = False
        self.refreshing = False
        self.refresh_timeout = 0
        self.snapshot = {"sinks": [], "sources": []}
        self.device_signatures = {"sink": None, "source": None}
        self.dragging = {"sink": False, "source": False}
        self.volume_timeouts = {"sink": 0, "source": 0}
        self.feedback_timeout = 0
        self.subscribe_process = None
        self.boost_enabled = self.read_boost_state()

        self.set_decorated(False)
        self.set_app_paintable(True)
        self.connect("destroy", self.on_destroy)
        self.connect("key-press-event", self.on_key)

        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.EXCLUSIVE)
        GtkLayerShell.set_namespace(self, "waybar-audio-panel")
        for edge in (GtkLayerShell.Edge.TOP, GtkLayerShell.Edge.RIGHT,
                     GtkLayerShell.Edge.BOTTOM, GtkLayerShell.Edge.LEFT):
            GtkLayerShell.set_anchor(self, edge, True)
        GtkLayerShell.set_exclusive_zone(self, -1)

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
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

        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=9)
        panel.set_size_request(430, -1)
        panel.get_style_context().add_class("panel")
        guard.add(panel)
        self.build_header(panel)
        self.sink_widgets = self.build_section(panel, "sink")
        self.source_widgets = self.build_section(panel, "source")
        self.build_pavucontrol_action(panel)

        self.begin_refresh()
        self.start_subscription()

    def build_header(self, panel):
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header.get_style_context().add_class("header")
        titles = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        title = Gtk.Label(label="Audio", xalign=0)
        title.get_style_context().add_class("title")
        subtitle = Gtk.Label(label="Dispositivos y niveles", xalign=0)
        subtitle.get_style_context().add_class("subtitle")
        titles.pack_start(title, False, False, 0)
        titles.pack_start(subtitle, False, False, 0)
        header.pack_start(titles, True, True, 0)
        close = Gtk.Button(label="󰅖")
        close.get_style_context().add_class("close")
        close.connect("clicked", lambda *_: self.close_panel())
        header.pack_end(close, False, False, 0)
        panel.pack_start(header, False, False, 0)

    def build_section(self, panel, kind):
        is_sink = kind == "sink"
        section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=9)
        section.get_style_context().add_class("section")
        section.get_style_context().add_class("output" if is_sink else "input")

        heading = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        icon = Gtk.Label(label="󰕾" if is_sink else "󰍬")
        icon.get_style_context().add_class("section-icon")
        title = Gtk.Label(label="Salida" if is_sink else "Entrada", xalign=0)
        title.get_style_context().add_class("section-title")
        heading.pack_start(icon, False, False, 0)
        heading.pack_start(title, True, True, 0)
        section.pack_start(heading, False, False, 0)

        device_caption = Gtk.Label(label="DISPOSITIVO", xalign=0)
        device_caption.get_style_context().add_class("device-label")
        section.pack_start(device_caption, False, False, 0)
        combo = Gtk.ComboBoxText()
        combo.set_hexpand(True)
        combo.connect("changed", self.on_device_changed, kind)
        section.pack_start(combo, False, False, 0)

        volume_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=9)
        volume_icon = Gtk.Label(label="󰕾" if is_sink else "󰍬")
        volume_icon.get_style_context().add_class("volume-icon")
        scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 150 if is_sink and self.boost_enabled else 100, 1
        )
        scale.set_draw_value(False)
        scale.set_hexpand(True)
        scale.set_increments(1, 5)
        scale.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.BUTTON_RELEASE_MASK)
        scale.connect("button-press-event", self.on_scale_press, kind)
        scale.connect("button-release-event", self.on_scale_release, kind)
        scale.connect("value-changed", self.on_volume_changed, kind)
        percent = Gtk.Label(label="0 %")
        percent.get_style_context().add_class("percent")
        mute = Gtk.Button(label="󰖁" if is_sink else "󰍭")
        mute.get_style_context().add_class("mute")
        mute.set_tooltip_text("Silenciar" if is_sink else "Silenciar micrófono")
        mute.connect("clicked", self.on_mute_clicked, kind)
        volume_row.pack_start(volume_icon, False, False, 0)
        volume_row.pack_start(scale, True, True, 0)
        volume_row.pack_start(percent, False, False, 0)
        volume_row.pack_start(mute, False, False, 0)
        section.pack_start(volume_row, False, False, 0)
        if is_sink:
            self.build_boost_row(section)
        panel.pack_start(section, False, False, 0)
        return {
            "section": section, "combo": combo, "scale": scale,
            "percent": percent, "mute": mute,
        }

    def build_boost_row(self, panel):
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        row.get_style_context().add_class("boost-row")
        labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        title = Gtk.Label(label="Volumen ampliado", xalign=0)
        title.get_style_context().add_class("boost-title")
        detail = Gtk.Label(label="Permitir hasta 150 % también en la barra", xalign=0)
        detail.get_style_context().add_class("boost-detail")
        labels.pack_start(title, False, False, 0)
        labels.pack_start(detail, False, False, 0)
        self.boost_switch = Gtk.Switch()
        self.boost_switch.set_valign(Gtk.Align.CENTER)
        self.boost_switch.set_active(self.boost_enabled)
        self.boost_switch.connect("notify::active", self.on_boost_changed)
        row.pack_start(labels, True, True, 0)
        row.pack_end(self.boost_switch, False, False, 0)
        panel.pack_start(row, False, False, 0)

    def build_pavucontrol_action(self, panel):
        button = Gtk.Button()
        button.set_tooltip_text("Abrir el mezclador de volumen avanzado")
        button.get_style_context().add_class("advanced-audio")
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=9)
        icon = Gtk.Image.new_from_pixbuf(
            GdkPixbuf.Pixbuf.new_from_file_at_scale(
                str(ASSETS_DIR / "audio-mixer.svg"), 18, 18, True,
            )
        )
        icon.set_size_request(25, 18)
        icon.get_style_context().add_class("advanced-icon")
        labels = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        title = Gtk.Label(label="Abrir mezclador de volumen", xalign=0)
        title.get_style_context().add_class("advanced-title")
        detail = Gtk.Label(
            label="Aplicaciones y dispositivos avanzados", xalign=0,
        )
        detail.get_style_context().add_class("advanced-detail")
        labels.pack_start(title, False, False, 0)
        labels.pack_start(detail, False, False, 0)
        arrow = Gtk.Label(label="↗")
        arrow.get_style_context().add_class("advanced-arrow")
        row.pack_start(icon, False, False, 0)
        row.pack_start(labels, True, True, 0)
        row.pack_end(arrow, False, False, 0)
        button.add(row)
        button.connect("clicked", self.open_pavucontrol)
        panel.pack_start(button, False, False, 0)

    def open_pavucontrol(self, *_args):
        self.close_panel()
        run_detached(["pavucontrol"])

    def read_boost_state(self):
        try:
            return BOOST_FILE.read_text().strip() == "1"
        except OSError:
            return False

    def write_boost_state(self, enabled):
        try:
            BOOST_FILE.write_text("1\n" if enabled else "0\n")
        except OSError:
            pass

    def on_boost_changed(self, switch, _property):
        if self.internal_update:
            return
        self.boost_enabled = switch.get_active()
        self.write_boost_state(self.boost_enabled)
        maximum = 150 if self.boost_enabled else 100
        scale = self.sink_widgets["scale"]
        scale.set_range(0, maximum)
        if self.boost_enabled:
            self.sink_widgets["section"].get_style_context().add_class("boosted")
        else:
            self.sink_widgets["section"].get_style_context().remove_class("boosted")
            if scale.get_value() > 100:
                scale.set_value(100)

    def on_scale_press(self, _scale, _event, kind):
        self.dragging[kind] = True
        return False

    def on_scale_release(self, _scale, _event, kind):
        self.dragging[kind] = False
        self.schedule_refresh(180)
        return False

    def on_volume_changed(self, scale, kind):
        widgets = self.sink_widgets if kind == "sink" else self.source_widgets
        value = round(scale.get_value())
        widgets["percent"].set_text(f"{value} %")
        if kind == "sink":
            context = widgets["section"].get_style_context()
            if value > 100:
                context.add_class("boosted")
            elif not self.boost_enabled:
                context.remove_class("boosted")
        if self.internal_update:
            return
        timeout = self.volume_timeouts[kind]
        if timeout:
            GLib.source_remove(timeout)
        self.volume_timeouts[kind] = GLib.timeout_add(
            55, self.apply_volume, kind, value
        )

    def apply_volume(self, kind, value):
        self.volume_timeouts[kind] = 0
        widgets = self.sink_widgets if kind == "sink" else self.source_widgets
        name = widgets["combo"].get_active_id()
        if name:
            target = "sink" if kind == "sink" else "source"
            run_detached(["pactl", f"set-{target}-volume", name, f"{value}%"])
            run_detached(["pactl", f"set-{target}-mute", name, "0"])
            if kind == "sink":
                self.schedule_feedback(name)
        return False

    def schedule_feedback(self, device):
        if self.feedback_timeout:
            GLib.source_remove(self.feedback_timeout)
        self.feedback_timeout = GLib.timeout_add(
            180, self.play_feedback, device
        )

    def play_feedback(self, device):
        self.feedback_timeout = 0
        run_detached([
            str(SCRIPT_DIR / "play-volume-feedback.sh"),
            "--device", device,
        ])
        return False

    def on_mute_clicked(self, _button, kind):
        widgets = self.sink_widgets if kind == "sink" else self.source_widgets
        name = widgets["combo"].get_active_id()
        if name:
            target = "sink" if kind == "sink" else "source"
            run_detached(["pactl", f"set-{target}-mute", name, "toggle"])
            self.schedule_refresh(160)

    def on_device_changed(self, combo, kind):
        if self.internal_update:
            return
        name = combo.get_active_id()
        if not name:
            return
        threading.Thread(
            target=self.set_default_device, args=(kind, name), daemon=True
        ).start()
        self.update_controls(kind, name)

    def set_default_device(self, kind, name):
        if kind == "sink":
            subprocess.run(["pactl", "set-default-sink", name], check=False)
            streams = command_output(["pactl", "list", "short", "sink-inputs"])
            for line in streams.splitlines():
                stream_id = line.split("\t", 1)[0].strip()
                if stream_id.isdigit():
                    subprocess.run(
                        ["pactl", "move-sink-input", stream_id, name], check=False
                    )
        else:
            subprocess.run(["pactl", "set-default-source", name], check=False)
            streams = command_output(["pactl", "list", "short", "source-outputs"])
            for line in streams.splitlines():
                stream_id = line.split("\t", 1)[0].strip()
                if stream_id.isdigit():
                    subprocess.run(
                        ["pactl", "move-source-output", stream_id, name], check=False
                    )
        GLib.idle_add(self.schedule_refresh, 180)

    def widgets_for(self, kind):
        return self.sink_widgets if kind == "sink" else self.source_widgets

    def devices_for(self, kind):
        return self.snapshot.get("sinks" if kind == "sink" else "sources", [])

    def update_controls(self, kind, selected_name):
        if self.dragging[kind]:
            return
        widgets = self.widgets_for(kind)
        device = next(
            (item for item in self.devices_for(kind) if item.get("name") == selected_name),
            None,
        )
        if device is None:
            return
        value = volume_percent(device)
        muted = bool(device.get("mute"))
        self.internal_update = True
        if kind == "sink" and value > 100 and not self.boost_enabled:
            self.boost_enabled = True
            self.boost_switch.set_active(True)
            widgets["scale"].set_range(0, 150)
            self.write_boost_state(True)
        widgets["scale"].set_value(value)
        widgets["percent"].set_text(f"{value} %")
        widgets["mute"].get_style_context().remove_class("active")
        if muted:
            widgets["mute"].get_style_context().add_class("active")
        widgets["mute"].set_label(
            ("󰖁" if muted else "󰕾") if kind == "sink"
            else ("󰍭" if muted else "󰍬")
        )
        self.internal_update = False

    def apply_snapshot(self, snapshot):
        self.refreshing = False
        if self.destroyed:
            return False
        self.snapshot = snapshot
        for kind, default_key in (("sink", "default_sink"), ("source", "default_source")):
            devices = self.devices_for(kind)
            signature = tuple((item.get("name"), device_label(item)) for item in devices)
            widgets = self.widgets_for(kind)
            combo = widgets["combo"]
            selected = snapshot.get(default_key, "")
            if signature != self.device_signatures[kind]:
                self.internal_update = True
                combo.remove_all()
                for item in devices:
                    combo.append(str(item.get("name", "")), device_label(item))
                self.device_signatures[kind] = signature
                self.internal_update = False
            if selected and combo.get_active_id() != selected:
                self.internal_update = True
                combo.set_active_id(selected)
                self.internal_update = False
            if not combo.get_active_id() and devices:
                self.internal_update = True
                combo.set_active(0)
                self.internal_update = False
            combo.set_sensitive(bool(devices))
            self.update_controls(kind, combo.get_active_id())
        return False

    def begin_refresh(self):
        if self.refreshing or self.destroyed:
            return False
        self.refreshing = True

        def worker():
            snapshot = audio_snapshot()
            GLib.idle_add(self.apply_snapshot, snapshot)

        threading.Thread(target=worker, daemon=True).start()
        return False

    def schedule_refresh(self, delay=120):
        if self.destroyed:
            return False
        if self.refresh_timeout:
            GLib.source_remove(self.refresh_timeout)
        self.refresh_timeout = GLib.timeout_add(delay, self.run_scheduled_refresh)
        return False

    def run_scheduled_refresh(self):
        self.refresh_timeout = 0
        if self.get_visible():
            self.begin_refresh()
        return False

    def start_subscription(self):
        def worker():
            try:
                self.subscribe_process = subprocess.Popen(
                    ["pactl", "subscribe"], text=True, encoding="utf-8",
                    errors="replace", stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                )
                for event in self.subscribe_process.stdout:
                    if self.destroyed:
                        break
                    if "sink" in event or "source" in event or "server" in event:
                        GLib.idle_add(self.schedule_refresh, 120)
            except OSError:
                pass

        threading.Thread(target=worker, daemon=True).start()

    def close_panel(self):
        if self.persistent:
            self.hide()
            GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.NONE)
        else:
            self.destroy()

    def toggle_panel(self):
        if self.get_visible():
            self.close_panel()
        else:
            GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.EXCLUSIVE)
            self.show_all()
            self.present()
            self.begin_refresh()
        return False

    def on_key(self, _window, event):
        if event.keyval == Gdk.KEY_Escape:
            self.close_panel()
            return True
        return False

    def on_destroy(self, *_args):
        self.destroyed = True
        if self.refresh_timeout:
            GLib.source_remove(self.refresh_timeout)
        for timeout in self.volume_timeouts.values():
            if timeout:
                GLib.source_remove(timeout)
        if self.feedback_timeout:
            GLib.source_remove(self.feedback_timeout)
        if self.subscribe_process and self.subscribe_process.poll() is None:
            self.subscribe_process.terminate()
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
    window = AudioPanel(persistent=daemon_mode)
    window.show_all()
    if daemon_mode and not show_initially:
        window.hide()
        GtkLayerShell.set_keyboard_mode(window, GtkLayerShell.KeyboardMode.NONE)
    signal.signal(signal.SIGUSR1, lambda *_: GLib.idle_add(window.toggle_panel))
    signal.signal(signal.SIGTERM, lambda *_: GLib.idle_add(window.destroy))
    Gtk.main()
