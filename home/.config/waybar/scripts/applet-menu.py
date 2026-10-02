#!/usr/bin/env python3
"""Show nm-applet or Blueman actions in a compact, centred Wayland window."""

import argparse
import fcntl
import os
from pathlib import Path
import socket
import subprocess
import sys
import time

# Never fall back to XWayland: the old GTK popup could remain mapped there.
os.environ['GDK_BACKEND'] = 'wayland'

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
gi.require_version('GtkLayerShell', '0.1')
from gi.repository import Gdk, Gio, GLib, Gtk, GtkLayerShell


WATCHER = 'org.kde.StatusNotifierWatcher'
ITEM = 'org.kde.StatusNotifierItem'
PROPERTIES = 'org.freedesktop.DBus.Properties'
DBUSMENU = 'com.canonical.dbusmenu'
MENU_PROPERTIES = [
    'label', 'type', 'enabled', 'visible', 'toggle-type', 'toggle-state',
    'icon-name', 'children-display',
]
TITLES = {'network': 'Redes', 'vpn': 'VPN', 'bluetooth': 'Bluetooth'}
APPLET_LOCALE = {
    'LANG': 'es_ES.UTF-8',
    'LC_ALL': 'es_ES.UTF-8',
    'LANGUAGE': 'es_ES:es',
}
HYPR_CLOSE_EVENTS = {
    b'workspace', b'workspacev2', b'focusedmon', b'focusedmonv2',
    b'activespecial',
}

CSS = b'''
* {
  font-family: "JetBrainsMono Nerd Font", monospace;
  font-size: 13px;
}
window#applet-menu { background: transparent; }
.menu-card {
  background-color: rgba(35, 39, 46, 0.98);
  border: 1px solid #3e4452;
  border-radius: 14px;
  color: #abb2bf;
  padding: 8px;
}
.menu-header {
  border-bottom: 1px solid #3e4452;
  padding: 3px 2px 9px 2px;
}
.menu-title { color: #61afef; font-weight: 700; font-size: 14px; }
.menu-back {
  background: transparent;
  border: 0;
  box-shadow: none;
  color: #c678dd;
  min-height: 26px;
  min-width: 28px;
  padding: 2px 7px;
}
.menu-back:hover {
  background-color: #2c313a;
  color: #d7dae0;
}
.menu-item {
  background: transparent;
  border: 0;
  border-radius: 7px;
  box-shadow: none;
  color: #abb2bf;
  min-height: 30px;
  padding: 3px 9px;
}
.menu-item:hover { background-color: #2c313a; color: #61afef; }
.menu-item:disabled { color: #5c6370; opacity: 1; }
.menu-item label { padding: 0; }
.menu-separator {
  background-color: #3e4452;
  min-height: 1px;
  margin: 5px 8px;
}
scrollbar slider {
  background-color: #61afef;
  border-radius: 5px;
  min-width: 5px;
}
'''


def call(bus, destination, path, interface, method, arguments=None, timeout=2500):
    """Make a synchronous session D-Bus call and unpack its result."""
    result = bus.call_sync(
        destination, path, interface, method, arguments, None,
        Gio.DBusCallFlags.NONE, timeout, None,
    )
    return result.unpack() if result is not None else ()


def find_menu(bus, wanted):
    """Return the unique bus name and menu path exported by an applet."""
    items = call(
        bus, WATCHER, '/StatusNotifierWatcher', PROPERTIES, 'Get',
        GLib.Variant('(ss)', (WATCHER, 'RegisteredStatusNotifierItems')),
    )[0]
    for address in items:
        destination, separator, path = address.partition('/')
        path = '/' + path if separator else '/StatusNotifierItem'
        try:
            properties = call(
                bus, destination, path, PROPERTIES, 'GetAll',
                GLib.Variant('(s)', (ITEM,)),
            )[0]
        except GLib.Error:
            continue
        if properties.get('Id') == wanted and properties.get('Menu') not in (None, '/'):
            return destination, properties['Menu']
    return None


def start_applet(wanted):
    command = ['nm-applet', '--indicator'] if wanted == 'nm-applet' else ['blueman-applet']
    running = subprocess.run(
        ['pgrep', '-u', str(os.getuid()), '-x', command[0]],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False,
    ).returncode == 0
    if not running:
        environment = os.environ.copy()
        environment.update(APPLET_LOCALE)
        subprocess.Popen(
            command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, start_new_session=True, env=environment,
        )


def wait_for_menu(bus, wanted):
    endpoint = find_menu(bus, wanted)
    if endpoint is not None:
        return endpoint
    start_applet(wanted)
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        time.sleep(0.15)
        endpoint = find_menu(bus, wanted)
        if endpoint is not None:
            return endpoint
    raise RuntimeError('El applet no ha publicado su menú en la sesión.')


def menu_layout(bus, destination, path, item_id, depth=1):
    """Refresh one menu node and return its current D-Bus layout."""
    call(
        bus, destination, path, DBUSMENU, 'AboutToShow',
        GLib.Variant('(i)', (item_id,)),
    )
    return call(
        bus, destination, path, DBUSMENU, 'GetLayout',
        GLib.Variant('(iias)', (item_id, depth, MENU_PROPERTIES)),
    )[1]


def plain_label(label):
    """Remove GTK mnemonic underscores while preserving escaped underscores."""
    output = []
    index = 0
    while index < len(label):
        if label[index] == '_' and index + 1 < len(label):
            if label[index + 1] == '_':
                output.append('_')
                index += 2
                continue
            index += 1
            continue
        output.append(label[index])
        index += 1
    return ''.join(output)


def translated_label(label):
    """Translate the few Bluetooth profile strings left untranslated upstream."""
    label = plain_label(label)
    replacements = (
        ('Audio Profiles for ', 'Perfiles de audio para '),
        ('High Fidelity Playback', 'Reproducción de alta fidelidad'),
        ('A2DP Sink', 'receptor A2DP'),
        ('Headset Head Unit', 'Unidad de auriculares'),
        ('codec ', 'códec '),
    )
    for source, target in replacements:
        label = label.replace(source, target)
    return label


def visible_children(layout):
    return [child for child in layout[2] if child[1].get('visible', True)]


def display_children(layout):
    """Remove empty rows and separators left orphaned by dynamic sections."""
    output = []
    for child in visible_children(layout):
        _item_id, properties, descendants = child
        is_separator = properties.get('type') == 'separator'
        if is_separator:
            if not output or output[-1][1].get('type') == 'separator':
                continue
            output.append(child)
            continue
        is_empty = not any((
            properties.get('label', '').strip(),
            properties.get('icon-name'),
            properties.get('toggle-type'),
            properties.get('children-display') == 'submenu',
            descendants,
        ))
        if not is_empty:
            output.append(child)
    if output and output[-1][1].get('type') == 'separator':
        output.pop()
    return output


def layout_signature(layout):
    """Describe visible menu content without volatile D-Bus item IDs."""
    _item_id, properties, children = layout
    own_properties = tuple(sorted(
        (key, repr(value)) for key, value in properties.items()
        if key in MENU_PROPERTIES
    ))
    return own_properties, tuple(
        layout_signature(child) for child in children
        if child[1].get('visible', True)
    )


class AppletMenuWindow(Gtk.Window):
    """A compact layer-shell window backed by the applet's real D-Bus menu."""

    def __init__(self, bus, destination, path, menu_kind, title, root_id):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)
        self.bus = bus
        self.destination = destination
        self.menu_path = path
        self.menu_kind = menu_kind
        self.root_id = root_id
        self.history = []
        self.hypr_socket = None
        self.hypr_watch_id = 0
        self.hypr_buffer = b''
        self.focus_relax_id = 0
        self.menu_signal_ids = []
        self.refresh_id = 0
        self.poll_id = 0
        self.scroll_restore_id = 0
        self.last_layout_signature = None
        self.destroying = False

        self.set_name('applet-menu')
        self.set_title(title)
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_accept_focus(True)
        self.set_skip_taskbar_hint(True)
        self.set_default_size(390, -1)
        self.connect('destroy', self.on_destroy)
        self.connect('key-press-event', self.on_key_press)
        self.connect('map-event', self.on_map)

        GtkLayerShell.init_for_window(self)
        GtkLayerShell.set_layer(self, GtkLayerShell.Layer.OVERLAY)
        # Force focus on opening so Escape and keyboard navigation work.
        GtkLayerShell.set_keyboard_mode(self, GtkLayerShell.KeyboardMode.EXCLUSIVE)
        if hasattr(GtkLayerShell, 'set_namespace'):
            GtkLayerShell.set_namespace(self, 'waybar-applet-menu')
        for edge in (
            GtkLayerShell.Edge.TOP,
            GtkLayerShell.Edge.RIGHT,
            GtkLayerShell.Edge.BOTTOM,
            GtkLayerShell.Edge.LEFT,
        ):
            GtkLayerShell.set_anchor(self, edge, True)
        # Cover reserved panels too, matching the grab area of a native popup.
        GtkLayerShell.set_exclusive_zone(self, -1)
        display = Gdk.Display.get_default()
        pointer = display.get_default_seat().get_pointer()
        _screen, pointer_x, pointer_y = pointer.get_position()
        monitor = display.get_monitor_at_point(pointer_x, pointer_y)
        if monitor is not None:
            GtkLayerShell.set_monitor(self, monitor)

        provider = Gtk.CssProvider()
        provider.load_from_data(CSS)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(), provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
        )

        self.backdrop = Gtk.EventBox()
        self.backdrop.set_visible_window(False)
        self.backdrop.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.backdrop.connect('button-press-event', self.on_backdrop_click)
        self.card_guard = Gtk.EventBox()
        self.card_guard.set_visible_window(False)
        self.card_guard.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.card_guard.connect('button-press-event', lambda *_args: True)
        self.card_guard.set_halign(Gtk.Align.CENTER)
        self.card_guard.set_valign(Gtk.Align.CENTER)
        self.backdrop.add(self.card_guard)
        self.add(self.backdrop)

        self.card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.card.set_size_request(390, -1)
        self.card.get_style_context().add_class('menu-card')
        self.card_guard.add(self.card)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        header.get_style_context().add_class('menu-header')
        self.back = Gtk.Button(label='‹')
        self.back.set_tooltip_text('Volver')
        self.back.get_style_context().add_class('menu-back')
        self.back.connect('clicked', self.go_back)
        header.pack_start(self.back, False, False, 0)
        self.heading = Gtk.Label(label=title, xalign=0)
        self.heading.set_hexpand(True)
        self.heading.get_style_context().add_class('menu-title')
        header.pack_start(self.heading, True, True, 0)
        self.card.pack_start(header, False, False, 0)

        self.page_serial = 0
        self.stack = Gtk.Stack()
        self.stack.set_homogeneous(False)
        self.stack.set_interpolate_size(True)
        self.stack.set_transition_duration(190)
        self.card.pack_start(self.stack, True, True, 0)
        self.scroll, self.items = self.create_page_widgets()
        self.stack.add_named(self.scroll, self.next_page_name())
        self.show_page(root_id, title, remember=False)
        self.watch_menu_updates()
        # Some Blueman backends do not emit a menu signal for every device
        # transition.  Poll the exported menu as a reliable fallback, but only
        # redraw when its visible content has actually changed.
        self.poll_id = GLib.timeout_add(750, self.poll_menu_state)

    def on_key_press(self, _window, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
            return True
        if event.keyval in (Gdk.KEY_Left, Gdk.KEY_BackSpace) and self.history:
            self.go_back()
            return True
        return False

    def on_backdrop_click(self, _widget, event):
        """Close on the outer input region; the card guard stops inner clicks."""
        self.destroy()
        return True

    def on_map(self, *_args):
        self.watch_hyprland_events()
        # EXCLUSIVE guarantees initial focus, but keeping it would prevent
        # Hyprland workspace dispatches.  ON_DEMAND retains the acquired focus
        # while returning shortcut control to the compositor.
        self.focus_relax_id = GLib.timeout_add(120, self.relax_keyboard_mode)
        return False

    def relax_keyboard_mode(self):
        self.focus_relax_id = 0
        GtkLayerShell.set_keyboard_mode(
            self, GtkLayerShell.KeyboardMode.ON_DEMAND,
        )
        return False

    def on_destroy(self, *_args):
        self.destroying = True
        if self.refresh_id:
            GLib.source_remove(self.refresh_id)
            self.refresh_id = 0
        if self.poll_id:
            GLib.source_remove(self.poll_id)
            self.poll_id = 0
        if self.scroll_restore_id:
            GLib.source_remove(self.scroll_restore_id)
            self.scroll_restore_id = 0
        for subscription_id in self.menu_signal_ids:
            self.bus.signal_unsubscribe(subscription_id)
        self.menu_signal_ids.clear()
        if self.focus_relax_id:
            GLib.source_remove(self.focus_relax_id)
            self.focus_relax_id = 0
        if self.hypr_watch_id:
            GLib.source_remove(self.hypr_watch_id)
            self.hypr_watch_id = 0
        if self.hypr_socket is not None:
            self.hypr_socket.close()
            self.hypr_socket = None
        if Gtk.main_level():
            Gtk.main_quit()

    def watch_hyprland_events(self):
        if self.hypr_socket is not None:
            return
        signature = os.environ.get('HYPRLAND_INSTANCE_SIGNATURE')
        runtime = os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}')
        if not signature:
            return
        candidates = (
            Path(runtime) / 'hypr' / signature / '.socket2.sock',
            Path('/tmp/hypr') / signature / '.socket2.sock',
        )
        path = next((candidate for candidate in candidates if candidate.exists()), None)
        if path is None:
            return
        try:
            self.hypr_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.hypr_socket.connect(str(path))
            self.hypr_socket.setblocking(False)
            self.hypr_watch_id = GLib.io_add_watch(
                self.hypr_socket.fileno(),
                GLib.IO_IN | GLib.IO_HUP | GLib.IO_ERR,
                self.on_hyprland_event,
            )
        except OSError:
            if self.hypr_socket is not None:
                self.hypr_socket.close()
            self.hypr_socket = None

    def on_hyprland_event(self, _source, condition):
        if condition & (GLib.IO_HUP | GLib.IO_ERR):
            self.hypr_watch_id = 0
            return False
        try:
            chunk = self.hypr_socket.recv(8192)
        except BlockingIOError:
            return True
        if not chunk:
            self.hypr_watch_id = 0
            return False
        self.hypr_buffer += chunk
        lines = self.hypr_buffer.split(b'\n')
        self.hypr_buffer = lines.pop()
        for line in lines:
            event_name = line.partition(b'>>')[0]
            if event_name in HYPR_CLOSE_EVENTS:
                self.hypr_watch_id = 0
                # Drop the exclusive keyboard grab before destruction.  If the
                # layer is destroyed while it still owns that grab, Hyprland can
                # restore its previous focus and jump back to the old workspace.
                GtkLayerShell.set_keyboard_mode(
                    self, GtkLayerShell.KeyboardMode.NONE,
                )
                GLib.timeout_add(50, self.close_after_workspace_change)
                return False
        return True

    def close_after_workspace_change(self):
        self.destroy()
        return False

    def next_page_name(self):
        self.page_serial += 1
        return f'menu-page-{self.page_serial}'

    def create_page_widgets(self):
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_max_content_height(620)
        scroll.set_propagate_natural_height(True)
        items = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        scroll.add(items)
        return scroll, items

    def watch_menu_updates(self):
        """Refresh the open page when its applet changes the D-Bus menu."""
        signal_names = ['LayoutUpdated']
        if self.menu_kind != 'bluetooth':
            signal_names.append('ItemsPropertiesUpdated')
        for signal_name in signal_names:
            subscription_id = self.bus.signal_subscribe(
                self.destination,
                DBUSMENU,
                signal_name,
                self.menu_path,
                None,
                Gio.DBusSignalFlags.NONE,
                self.on_menu_update,
            )
            self.menu_signal_ids.append(subscription_id)

    def on_menu_update(
        self, _connection, _sender, _path, _interface, _signal,
        _parameters, _user_data,
    ):
        if self.destroying or self.refresh_id:
            return
        # Applets often emit several related changes in one burst.
        self.refresh_id = GLib.timeout_add(120, self.refresh_visible_page)

    def refresh_visible_page(self):
        self.refresh_id = 0
        if self.destroying:
            return False
        self.sync_visible_page()
        return False

    def poll_menu_state(self):
        if self.destroying:
            self.poll_id = 0
            return False
        self.sync_visible_page()
        return True

    def sync_visible_page(self):
        """Fetch current applet data and redraw only when content changed."""
        title = self.heading.get_text()
        try:
            layout = self.current_page_layout()
            if layout_signature(layout) != self.last_layout_signature:
                self.current_id = layout[0]
                self.render_page(layout, title)
        except (GLib.Error, RuntimeError):
            # A device can disappear while its submenu is open.  Return to a
            # valid root instead of leaving a stale or empty page on screen.
            self.history.clear()
            try:
                self.root_id = choose_root(
                    self.bus, self.destination, self.menu_path, self.menu_kind,
                )
                self.show_page(
                    self.root_id, TITLES[self.menu_kind], remember=False,
                )
            except (GLib.Error, RuntimeError):
                pass

    def go_back(self, *_args):
        if self.history:
            item_id, title = self.history.pop()
            self.show_page(
                item_id, title, remember=False, transition='backward',
            )

    def show_page(self, item_id, title, remember=True, transition=None):
        if remember:
            self.history.append((self.current_id, self.heading.get_text()))
            transition = transition or 'forward'
        self.current_id = item_id
        layout = menu_layout(
            self.bus, self.destination, self.menu_path, item_id, depth=1,
        )
        self.render_page(layout, title, transition=transition)

    def render_page(self, layout, title, transition=None):
        """Redraw one fetched layout while preserving keyboard selection."""
        if transition is not None:
            previous_scroll = self.scroll
            # Keep at most the outgoing and incoming page in the stack.
            for page in self.stack.get_children():
                if page is not previous_scroll:
                    self.stack.remove(page)
            self.scroll, self.items = self.create_page_widgets()
            self.stack.add_named(self.scroll, self.next_page_name())
            stack_transition = (
                Gtk.StackTransitionType.SLIDE_RIGHT
                if transition == 'backward'
                else Gtk.StackTransitionType.SLIDE_LEFT
            )
            self.stack.set_transition_type(stack_transition)
        self.last_layout_signature = layout_signature(layout)
        scroll_value = self.scroll.get_vadjustment().get_value()
        focused_key = None
        focused = self.get_focus()
        for child in self.items.get_children():
            if child is focused or (focused is not None and child.is_ancestor(focused)):
                focused_key = getattr(child, 'menu_item_key', None)
                break
        self.heading.set_text(translated_label(title))
        self.back.set_visible(bool(self.history))
        for child in self.items.get_children():
            child.destroy()
        children = display_children(layout)
        if not children:
            empty = Gtk.Label(label='No hay opciones disponibles', xalign=0)
            empty.set_margin_start(10)
            empty.set_margin_end(10)
            empty.set_margin_top(10)
            empty.set_margin_bottom(10)
            self.items.pack_start(empty, False, False, 0)
        for child in children:
            self.add_item(child)
        self.scroll.show_all()
        self.back.set_visible(bool(self.history))
        if transition is not None:
            self.stack.set_visible_child(self.scroll)
        buttons = [
            child for child in self.items.get_children()
            if isinstance(child, Gtk.Button) and child.get_sensitive()
        ]
        target = next((
            button for button in buttons
            if getattr(button, 'menu_item_key', None) == focused_key
        ), None)
        if target is not None:
            target.grab_focus()
        if scroll_value:
            if self.scroll_restore_id:
                GLib.source_remove(self.scroll_restore_id)
            self.scroll_restore_id = GLib.idle_add(
                self.restore_scroll_position, scroll_value,
            )

    def restore_scroll_position(self, value):
        self.scroll_restore_id = 0
        if self.destroying:
            return False
        adjustment = self.scroll.get_vadjustment()
        maximum = max(
            adjustment.get_lower(),
            adjustment.get_upper() - adjustment.get_page_size(),
        )
        adjustment.set_value(min(value, maximum))
        return False

    def add_item(self, item):
        item_id, properties, children = item
        if properties.get('type') == 'separator':
            separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            separator.get_style_context().add_class('menu-separator')
            self.items.pack_start(separator, False, False, 0)
            return

        source_label = properties.get('label', '')
        label_text = translated_label(source_label)
        has_submenu = properties.get('children-display') == 'submenu' or bool(children)
        toggle_type = properties.get('toggle-type')
        toggle_state = properties.get('toggle-state', 0)

        button = Gtk.Button()
        button.menu_item_key = (source_label, has_submenu)
        button.set_relief(Gtk.ReliefStyle.NONE)
        button.set_sensitive(properties.get('enabled', True))
        button.get_style_context().add_class('menu-item')
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=9)

        icon_name = properties.get('icon-name')
        if icon_name:
            row.pack_start(
                Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.MENU),
                False, False, 0,
            )
        elif toggle_type:
            if toggle_state == 1:
                marker = '●' if toggle_type == 'radio' else '✓'
            else:
                marker = ' '
            mark = Gtk.Label(label=marker)
            mark.set_size_request(16, -1)
            row.pack_start(mark, False, False, 0)

        label = Gtk.Label(label=label_text, xalign=0)
        label.set_line_wrap(True)
        label.set_hexpand(True)
        row.pack_start(label, True, True, 0)
        if has_submenu:
            row.pack_end(Gtk.Label(label='›'), False, False, 0)
            button.connect('clicked', self.open_submenu, source_label, item_id)
        else:
            button.connect('clicked', self.activate_item, source_label, item_id)
        button.add(row)
        self.items.pack_start(button, False, False, 0)

    def resolve_item(self, source_label, fallback_id, require_submenu):
        """Resolve a possibly renewed nm-applet item against its latest layout."""
        layout = self.current_page_layout()
        fallback = None
        for child in visible_children(layout):
            item_id, properties, descendants = child
            if item_id == fallback_id:
                fallback = child
            has_submenu = (
                properties.get('children-display') == 'submenu'
                or bool(descendants)
            )
            if properties.get('label', '') == source_label and has_submenu == require_submenu:
                return child
        if fallback is not None:
            return fallback
        raise RuntimeError(f'La opción «{translated_label(source_label)}» ya no está disponible.')

    def current_page_layout(self):
        """Return one current menu snapshot, replacing stale submenu IDs."""
        if self.current_id == 0:
            return menu_layout(
                self.bus, self.destination, self.menu_path, 0, depth=1,
            )
        root = menu_layout(
            self.bus, self.destination, self.menu_path, 0, depth=2,
        )
        heading = self.heading.get_text().casefold()
        for child in visible_children(root):
            properties = child[1]
            is_submenu = (
                properties.get('children-display') == 'submenu'
                or bool(child[2])
            )
            if not is_submenu:
                continue
            label = translated_label(properties.get('label', '')).casefold()
            same_page = label == heading
            direct_vpn = self.menu_kind == 'vpn' and 'vpn' in label
            if same_page or direct_vpn:
                self.current_id = child[0]
                self.root_id = child[0] if direct_vpn else self.root_id
                return child
        return menu_layout(
            self.bus, self.destination, self.menu_path, self.current_id, depth=1,
        )

    def open_submenu(self, _button, source_label, fallback_id):
        try:
            item_id, properties, _children = self.resolve_item(
                source_label, fallback_id, require_submenu=True,
            )
            self.show_page(
                item_id, translated_label(properties.get('label', source_label)),
            )
        except (GLib.Error, RuntimeError) as exc:
            self.report_click_error(source_label, exc)

    def activate_item(self, _button, source_label, fallback_id):
        try:
            item_id, _properties, _children = self.resolve_item(
                source_label, fallback_id, require_submenu=False,
            )
            self.activate(item_id, source_label, fallback_id)
        except (GLib.Error, RuntimeError) as exc:
            self.report_click_error(source_label, exc)

    def report_click_error(self, source_label, error):
        label = translated_label(source_label)
        message = f'{label}: {error}'
        print('Menú del applet:', message, file=sys.stderr)
        subprocess.Popen(
            ['notify-send', '-a', 'Waybar', 'La opción no pudo ejecutarse', message],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, start_new_session=True,
        )

    def activate(self, item_id, source_label, fallback_id):
        # Some applet actions keep their D-Bus method open while a secondary
        # dialog is running. Unmap this surface before dispatching the action.
        self.hide()
        display = Gdk.Display.get_default()
        if display is not None:
            display.flush()
        try:
            try:
                self.send_event(item_id, 'clicked')
            except GLib.Error as exc:
                stale_id = (
                    'id supplied' in str(exc).casefold()
                    or 'does not refer to a menu item' in str(exc).casefold()
                )
                if not stale_id:
                    raise
                fresh_id, _properties, _children = self.resolve_item(
                    source_label, fallback_id, require_submenu=False,
                )
                self.send_event(fresh_id, 'clicked')
        finally:
            self.destroy()

    def send_event(self, item_id, event_name):
        timestamp = int(time.monotonic() * 1000) & 0xffffffff
        call(
            self.bus, self.destination, self.menu_path, DBUSMENU, 'Event',
            GLib.Variant(
                '(isvu)',
                (item_id, event_name, GLib.Variant('i', 0), timestamp),
            ),
        )


def choose_root(bus, destination, path, selected):
    """Return the page root, opening nm-applet directly at VPN when requested."""
    if selected != 'vpn':
        return 0
    root = menu_layout(bus, destination, path, 0, depth=1)
    for child in visible_children(root):
        if 'vpn' in translated_label(child[1].get('label', '')).casefold():
            return child[0]
    raise RuntimeError('nm-applet no ofrece un submenú VPN en este momento.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('menu', choices=('network', 'vpn', 'bluetooth'))
    parser.add_argument(
        '--check', action='store_true',
        help='Comprueba el menú por D-Bus sin abrir una ventana.',
    )
    args = parser.parse_args()

    bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
    wanted = 'blueman' if args.menu == 'bluetooth' else 'nm-applet'
    destination, path = wait_for_menu(bus, wanted)
    root_id = choose_root(bus, destination, path, args.menu)
    layout = menu_layout(bus, destination, path, root_id, depth=1)
    count = len(visible_children(layout))
    if args.check:
        print(f'{args.menu}: menú disponible; {count} entradas')
        return

    if not os.environ.get('WAYLAND_DISPLAY'):
        raise RuntimeError('No se encontró una sesión Wayland activa.')
    runtime = Path(os.environ.get('XDG_RUNTIME_DIR', f'/run/user/{os.getuid()}'))
    lock = os.open(
        runtime / 'waybar-applet-menu.lock',
        os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600,
    )
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        os.close(lock)
        return

    if not Gtk.init_check()[0]:
        os.close(lock)
        raise RuntimeError('No se pudo crear la ventana Wayland del menú.')
    window = AppletMenuWindow(
        bus, destination, path, args.menu, TITLES[args.menu], root_id,
    )
    window.show_all()
    window.back.set_visible(False)
    window.present()
    for child in window.items.get_children():
        if isinstance(child, Gtk.Button) and child.get_sensitive():
            child.grab_focus()
            break
    Gtk.main()
    os.close(lock)


if __name__ == '__main__':
    try:
        main()
    except (GLib.Error, RuntimeError, OSError) as exc:
        message = str(exc)
        print('Menú del applet:', message, file=sys.stderr)
        subprocess.run(
            ['notify-send', '-a', 'Waybar', 'No se pudo abrir el menú', message],
            check=False,
        )
        sys.exit(1)
