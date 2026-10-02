#!/usr/bin/env python3

import locale
import os
import subprocess
import sys
import time
from pathlib import Path

MODE = Path(sys.argv[0]).name.removeprefix("applications-")
CACHE_DIR = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache")) / "rofi-applications"
CACHE_MAX_AGE = 300

CATEGORY_RULES = {
    "all": set(),
    "internet": {
        "Network", "WebBrowser", "Email", "Chat", "InstantMessaging",
        "FileTransfer", "RemoteAccess", "P2P",
    },
    "multimedia": {
        "AudioVideo", "Audio", "Video", "Player", "Recorder", "Music",
        "AudioVideoEditing", "Mixer", "TV",
    },
    "development": {
        "Development", "IDE", "GUIDesigner", "WebDevelopment",
        "RevisionControl", "Debugger", "Building", "Database",
    },
    "security": {"Security", "NetworkSecurity", "SystemSecurity"},
    "office": {
        "Office", "WordProcessor", "Spreadsheet", "Presentation",
        "Calendar", "ContactManagement",
    },
    "graphics": {
        "Graphics", "Photography", "RasterGraphics", "VectorGraphics",
        "Scanning", "Publishing",
    },
    "system": {
        "System", "Settings", "DesktopSettings", "HardwareSettings",
        "FileManager", "TerminalEmulator", "Filesystem", "Monitor",
        "Printing",
    },
    "utilities": {
        "Utility", "TextEditor", "Calculator", "Archiving", "Compression",
        "FileTools", "Documentation", "Viewer",
    },
}

MODE_TITLES = {
    "all": "󰀻  Todas",
    "internet": "󰖟  Internet",
    "multimedia": "󰝚  Multimedia",
    "development": "󰅩  Desarrollo",
    "security": "󰒃  Seguridad",
    "office": "󰈙  Oficina",
    "graphics": "󰏘  Gráficos",
    "system": "󰒓  Sistema",
    "utilities": "  Utilidades",
}


def clean(value: str | None) -> str:
    return (value or "").replace("\0", " ").replace("\x1f", " ").replace("\n", " ").strip()


def application_dirs() -> list[Path]:
    data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    data_dirs = os.environ.get("XDG_DATA_DIRS", "/usr/local/share:/usr/share").split(":")
    candidates = [data_home / "applications"]
    candidates.extend(Path(item) / "applications" for item in data_dirs if item)
    candidates.extend((
        Path.home() / ".local/share/flatpak/exports/share/applications",
        Path("/var/lib/flatpak/exports/share/applications"),
    ))
    return list(dict.fromkeys(candidates))


def categories_for(app) -> set[str]:
    return {item.strip() for item in (app.get_categories() or "").split(";") if item.strip()}


def is_security(categories: set[str]) -> bool:
    return bool(categories & CATEGORY_RULES["security"]) or any(
        item.startswith("X-BlackArch-") for item in categories
    )


def belongs(app, mode: str) -> bool:
    if mode == "all":
        return True

    categories = categories_for(app)
    if mode == "security":
        return is_security(categories)

    if mode == "internet" and is_security(categories):
        return False

    return bool(categories & CATEGORY_RULES.get(mode, set()))


def icon_name(app, Gio) -> str:
    icon = app.get_icon()
    if icon is None:
        return "application-x-executable"
    if isinstance(icon, Gio.ThemedIcon):
        names = icon.get_names()
        if names:
            return clean(names[0])
    if isinstance(icon, Gio.FileIcon):
        path = icon.get_file().get_path()
        if path and Path(path).is_file():
            return clean(path)
        return "application-x-executable"
    return clean(icon.to_string()) or "application-x-executable"


def launch(desktop_id: str) -> None:
    desktop_file = next(
        (directory / desktop_id for directory in application_dirs()
         if (directory / desktop_id).is_file()),
        None,
    )
    command = (["gio", "launch", str(desktop_file)] if desktop_file
               else ["gtk-launch", desktop_id])
    environment = {
        key: value for key, value in os.environ.items()
        if not key.startswith("ROFI_")
    }

    try:
        subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True,
            env=environment,
        )
    except Exception as error:
        print(f"No se pudo abrir {desktop_id}: {error}", file=sys.stderr)


def render_apps(mode: str) -> bytes:
    import gi

    gi.require_version("Gio", "2.0")
    gi.require_version("GioUnix", "2.0")
    from gi.repository import Gio, GioUnix

    locale.setlocale(locale.LC_ALL, "")
    apps = [
        app for app in GioUnix.DesktopAppInfo.get_all()
        if app.should_show() and belongs(app, mode)
    ]
    apps.sort(key=lambda app: locale.strxfrm(clean(app.get_display_name()).casefold()))

    rows = [
        f"\0prompt\x1f{MODE_TITLES.get(mode, 'Aplicaciones')}\n".encode("utf-8"),
        f"\0message\x1f{len(apps)} aplicaciones · escribe para buscar\n".encode("utf-8"),
        b"\0no-custom\x1ftrue\n",
    ]

    for app in apps:
        name = clean(app.get_display_name())
        desktop_id = clean(app.get_id())
        description = clean(app.get_description())
        executable = clean(app.get_executable())
        meta = clean(f"{description} {executable}")
        row = (
            f"{name}\0"
            f"icon\x1f{icon_name(app, Gio)}\x1f"
            f"info\x1f{desktop_id}\x1f"
            f"meta\x1f{meta}\n"
        )
        rows.append(row.encode("utf-8"))
    return b"".join(rows)


def cache_path(mode: str) -> Path:
    return CACHE_DIR / f"{mode}.rows"


def cache_is_stale(path: Path) -> bool:
    try:
        cache_mtime = path.stat().st_mtime_ns
        if time.time() - path.stat().st_mtime > CACHE_MAX_AGE:
            return True
        return any(directory.stat().st_mtime_ns > cache_mtime
                   for directory in application_dirs() if directory.is_dir())
    except OSError:
        return True


def refresh_cache(mode: str) -> bytes:
    content = render_apps(mode)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    destination = cache_path(mode)
    temporary = CACHE_DIR / f".{mode}.{os.getpid()}.tmp"
    temporary.write_bytes(content)
    os.replace(temporary, destination)
    return content


def refresh_in_background(mode: str) -> None:
    environment = {
        key: value for key, value in os.environ.items()
        if not key.startswith("ROFI_")
    }
    try:
        subprocess.Popen(
            [str(Path(__file__).resolve()), "--refresh", mode],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True,
            env=environment,
        )
    except OSError:
        pass


def list_apps(mode: str) -> None:
    path = cache_path(mode)
    try:
        content = path.read_bytes()
    except OSError:
        content = refresh_cache(mode)
    else:
        if cache_is_stale(path):
            refresh_in_background(mode)
    sys.stdout.buffer.write(content)


if len(sys.argv) == 2 and sys.argv[1] == "--refresh-stale":
    for cache_mode in MODE_TITLES:
        destination = cache_path(cache_mode)
        if not destination.exists() or cache_is_stale(destination):
            refresh_cache(cache_mode)
elif len(sys.argv) == 3 and sys.argv[1] == "--refresh":
    refresh_cache(sys.argv[2])
elif os.environ.get("ROFI_RETV", "0") == "1" and os.environ.get("ROFI_INFO"):
    launch(os.environ["ROFI_INFO"])
else:
    list_apps(MODE)
