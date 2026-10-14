"""Entry point: prepares BCSFE, starts the local server and opens the window."""

from __future__ import annotations

import argparse
import os
import secrets
import shutil
import subprocess
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path

from . import APP_TITLE, native_dialogs
from .i18n import t

GUI_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = GUI_DIR / "web"


def _bcsfe_source_dirs() -> list[Path]:
    """BCSFE copies next to this folder, preferred over the pip-installed one
    (the GUI is tested with BCSFE 3.6.0)."""
    return [
        GUI_DIR.parent / "BCSFE-Python-main" / "BCSFE-Python-main" / "src",
        GUI_DIR.parent / "BCSFE-Python-main" / "src",
        GUI_DIR / "BCSFE-Python" / "src",
    ]


def import_bcsfe() -> None:
    for src in _bcsfe_source_dirs():
        if (src / "bcsfe" / "__init__.py").is_file():
            sys.path.insert(0, str(src))
            break
    # bcsfe.cli.color runs os.system("color") on import; without a console that
    # would flash a black window, so it is skipped.
    real_system = os.system
    os.system = lambda cmd: 0 if cmd == "color" else real_system(cmd)  # type: ignore[assignment]
    try:
        import bcsfe  # noqa: F401
        from bcsfe import cli, core  # noqa: F401
    finally:
        os.system = real_system  # type: ignore[assignment]


def init_bcsfe(data_dir: str | None) -> None:
    """The same start-up steps as the ``bcsfe`` console program."""
    from importlib import resources

    from bcsfe import __app_name__, __version__, copy_to_data_dir, core

    from . import settings

    settings.install_locale()
    if data_dir:
        core.set_data_dir_path(core.Path(data_dir))

    version_path = core.Path.get_data_folder().add("version.txt")
    current = version_path.read().to_str().strip() if version_path.exists() else None
    if current != __version__:
        files = resources.files(__app_name__).joinpath("files")
        copy_to_data_dir(files, files)
        version_path.write(core.Data(__version__))

    core.core_data.init_data()
    try:
        core.SaveFile.get_temp_path().remove()
    except Exception:
        pass
    try:
        core.GameDataGetter.delete_old_versions(5)
    except Exception:
        pass


def find_browser() -> str | None:
    candidates: list[Path] = []
    for env in ("ProgramFiles(x86)", "ProgramFiles", "LOCALAPPDATA"):
        base = os.environ.get(env)
        if base:
            candidates.append(Path(base) / "Microsoft" / "Edge" / "Application" / "msedge.exe")
    for env in ("ProgramFiles", "ProgramFiles(x86)", "LOCALAPPDATA"):
        base = os.environ.get(env)
        if base:
            candidates.append(Path(base) / "Google" / "Chrome" / "Application" / "chrome.exe")
    for c in candidates:
        if c.is_file():
            return str(c)
    for name in ("msedge", "chrome", "google-chrome", "chromium", "chromium-browser"):
        found = shutil.which(name)
        if found:
            return found
    return None


def open_window(url: str) -> subprocess.Popen | None:
    """Opens the interface in its own window (Edge/Chrome app mode)."""
    browser = find_browser()
    if browser is None:
        webbrowser.open(url)
        return None
    profile = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "BCSFE_GUI" / "browser_profile"
    profile.mkdir(parents=True, exist_ok=True)
    args = [
        browser,
        f"--app={url}",
        f"--user-data-dir={profile}",
        "--no-first-run",
        "--no-default-browser-check",
        "--disable-sync",
        "--hide-crash-restore-bubble",
        "--disable-features=Translate,msEdgeSidebarV2,msUndersideButton",
        "--window-size=1400,900",
    ]
    flags = 0x08000000 if sys.platform == "win32" else 0  # CREATE_NO_WINDOW
    return subprocess.Popen(args, creationflags=flags)


def watch(app: "AppState", proc: subprocess.Popen | None, url: str) -> None:  # noqa: F821
    """Stops the server once the window is closed."""
    started = time.time()
    exited_at: float | None = None
    fallback_opened = False
    while not app.shutdown_event.is_set():
        time.sleep(1)
        now = time.time()
        if not app.page_seen and not fallback_opened and now - started > 15:
            # The window never loaded the editor (e.g. a stuck browser process
            # holds the same profile), so open it in the default browser.
            fallback_opened = True
            webbrowser.open(url)
            app.last_seen = now
        if proc is not None and exited_at is None and proc.poll() is not None:
            exited_at = now
        if app.bye_at is not None and now - app.bye_at > 4 and now - app.last_seen > 4:
            # The page said it was closing and did not come back (not a reload).
            app.shutdown_event.set()
        elif exited_at is not None and exited_at - started > 8 and now - app.last_seen > 4:
            # The window's browser process ended: the window was closed.
            app.shutdown_event.set()
        elif (proc is None or exited_at is not None) and now - app.last_seen > 120:
            # No browser process of our own (the browser was already open):
            # wait until the page stops polling.
            app.shutdown_event.set()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=APP_TITLE)
    parser.add_argument("--data-dir", help="BCSFE data folder (default: Documents\\bcsfe)")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--no-window", action="store_true", help="do not open the window, print the URL instead")
    args = parser.parse_args(argv)

    try:
        import_bcsfe()
    except ImportError as exc:
        native_dialogs.message_box(APP_TITLE, t("bcsfe_missing", error=exc))
        return 1

    try:
        init_bcsfe(args.data_dir)
        from . import bridge as bridge_mod

        bridge_mod.install()
        from .server import AppState, create_server
        from .session import session

        token = secrets.token_urlsafe(24)
        app = AppState(WEB_DIR, token, session)
        server = create_server(app, args.port)
    except Exception:
        native_dialogs.message_box(APP_TITLE, t("startup_error", trace=traceback.format_exc()))
        return 1

    url = f"http://127.0.0.1:{app.port}/?t={token}"
    threading.Thread(target=server.serve_forever, name="http", daemon=True).start()

    if args.no_window:
        # Headless mode (testing): only stops with Ctrl+C or /api/quit.
        if sys.__stdout__ is not None:
            print(url, file=sys.__stdout__, flush=True)
    else:
        proc = open_window(url)
        threading.Thread(target=watch, args=(app, proc, url), name="watch", daemon=True).start()

    try:
        app.shutdown_event.wait()
    except KeyboardInterrupt:
        pass
    server.shutdown()
    return 0
