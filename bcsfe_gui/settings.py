"""GUI settings. They are stored apart from BCSFE's own config, which is never changed."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

GUI_DIR = Path(__file__).resolve().parent.parent
LOCALES_DIR = GUI_DIR / "locales"
SETTINGS_PATH = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "BCSFE_GUI" / "settings.json"

# "en": English interface and BCSFE's configured locale (English by default).
# "es": Spanish interface and the Spanish BCSFE translation in locales/es.
LANGUAGES = {"en": "English", "es": "Español"}
DEFAULTS: dict[str, Any] = {"language": "en"}


def load() -> dict[str, Any]:
    data = dict(DEFAULTS)
    try:
        stored = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        if isinstance(stored, dict):
            data.update({k: v for k, v in stored.items() if k in DEFAULTS})
    except (OSError, ValueError):
        pass
    if data["language"] not in LANGUAGES:
        data["language"] = DEFAULTS["language"]
    return data


def save(data: dict[str, Any]) -> None:
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


current = load()


def install_locale() -> None:
    """Lets BCSFE find the Spanish translation shipped with the GUI and use it
    whenever the GUI language is Spanish."""
    from bcsfe import core
    from bcsfe.core.locale_handler import LocalManager

    original_folder = LocalManager.get_locale_folder

    def get_locale_folder(locale: str) -> "core.Path":
        if locale == "es" and (LOCALES_DIR / "es").is_dir():
            return core.Path(str(LOCALES_DIR / "es"))
        return original_folder(locale)

    LocalManager.get_locale_folder = staticmethod(get_locale_folder)  # type: ignore[method-assign]

    original_init = core.CoreData.init_data

    def init_data(self: Any) -> None:
        original_init(self)
        apply_language(self)

    core.CoreData.init_data = init_data  # type: ignore[method-assign]


def apply_language(core_data: Any = None) -> None:
    from bcsfe import core
    from bcsfe.core.locale_handler import LocalManager

    target = core_data if core_data is not None else core.core_data
    if current["language"] == "es" and (LOCALES_DIR / "es").is_dir():
        target.local_manager = LocalManager("es")
    else:
        target.local_manager = LocalManager()


def set_language(language: str) -> None:
    if language not in LANGUAGES:
        raise ValueError(language)
    current["language"] = language
    save(current)
    apply_language()
