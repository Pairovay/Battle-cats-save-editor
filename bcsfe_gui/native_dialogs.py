"""Native open/save file dialogs.

On Windows the common dialogs (GetOpenFileNameW / GetSaveFileNameW) are used
through ctypes: they work from any thread and stay above the editor window.
Other systems fall back to tkinter."""

from __future__ import annotations

import os
import sys
from typing import Sequence

from .i18n import t

FileTypes = Sequence[tuple[str, str]]


def _build_filter(filetypes: FileTypes | None, initialfile: str) -> str:
    types: list[tuple[str, str]] = []
    for desc, pattern in filetypes or []:
        types.append((desc, pattern))
    if not types and initialfile.lower().endswith(".json"):
        types.append((t("json_files"), "*.json"))
    types.append((t("all_files"), "*.*"))
    return "".join(f"{desc}\0{pattern}\0" for desc, pattern in types) + "\0"


if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    class OPENFILENAMEW(ctypes.Structure):
        _fields_ = [
            ("lStructSize", wintypes.DWORD),
            ("hwndOwner", wintypes.HWND),
            ("hInstance", wintypes.HINSTANCE),
            ("lpstrFilter", wintypes.LPCWSTR),
            ("lpstrCustomFilter", wintypes.LPWSTR),
            ("nMaxCustFilter", wintypes.DWORD),
            ("nFilterIndex", wintypes.DWORD),
            ("lpstrFile", wintypes.LPWSTR),
            ("nMaxFile", wintypes.DWORD),
            ("lpstrFileTitle", wintypes.LPWSTR),
            ("nMaxFileTitle", wintypes.DWORD),
            ("lpstrInitialDir", wintypes.LPCWSTR),
            ("lpstrTitle", wintypes.LPCWSTR),
            ("Flags", wintypes.DWORD),
            ("nFileOffset", wintypes.WORD),
            ("nFileExtension", wintypes.WORD),
            ("lpstrDefExt", wintypes.LPCWSTR),
            ("lCustData", wintypes.LPARAM),
            ("lpfnHook", ctypes.c_void_p),
            ("lpTemplateName", wintypes.LPCWSTR),
            ("pvReserved", ctypes.c_void_p),
            ("dwReserved", wintypes.DWORD),
            ("FlagsEx", wintypes.DWORD),
        ]

    OFN_OVERWRITEPROMPT = 0x00000002
    OFN_NOCHANGEDIR = 0x00000008
    OFN_PATHMUSTEXIST = 0x00000800
    OFN_FILEMUSTEXIST = 0x00001000
    OFN_EXPLORER = 0x00080000

    _comdlg32 = ctypes.WinDLL("comdlg32")
    _user32 = ctypes.WinDLL("user32")
    _ole32 = ctypes.WinDLL("ole32")
    _comdlg32.GetOpenFileNameW.argtypes = [ctypes.POINTER(OPENFILENAMEW)]
    _comdlg32.GetSaveFileNameW.argtypes = [ctypes.POINTER(OPENFILENAMEW)]
    _user32.GetForegroundWindow.restype = wintypes.HWND

    def _wide_buffer(text: str):
        # The filter contains embedded '\0' characters, which ctypes does not
        # accept in a plain str.
        raw = text.encode("utf-16-le") + b"\0\0"
        buf = (ctypes.c_wchar * (len(raw) // 2))()
        ctypes.memmove(buf, raw, len(raw))
        return buf

    def _run(save: bool, title: str, initialdir: str, initialfile: str, filetypes: FileTypes | None) -> str | None:
        # The Explorer-style dialog needs COM in single-threaded mode on this thread.
        _ole32.CoInitializeEx(None, 0x2)
        buf = ctypes.create_unicode_buffer(initialfile or "", 4096)
        flt = _wide_buffer(_build_filter(filetypes, initialfile or ""))
        ofn = OPENFILENAMEW()
        ofn.lStructSize = ctypes.sizeof(OPENFILENAMEW)
        ofn.hwndOwner = _user32.GetForegroundWindow()
        ofn.lpstrFilter = ctypes.cast(flt, wintypes.LPCWSTR)
        ofn.nFilterIndex = 1
        ofn.lpstrFile = ctypes.cast(buf, wintypes.LPWSTR)
        ofn.nMaxFile = len(buf)
        ofn.lpstrInitialDir = initialdir if initialdir and os.path.isdir(initialdir) else None
        ofn.lpstrTitle = title or None
        if save:
            ofn.Flags = OFN_EXPLORER | OFN_NOCHANGEDIR | OFN_PATHMUSTEXIST | OFN_OVERWRITEPROMPT
            ok = _comdlg32.GetSaveFileNameW(ctypes.byref(ofn))
        else:
            ofn.Flags = OFN_EXPLORER | OFN_NOCHANGEDIR | OFN_PATHMUSTEXIST | OFN_FILEMUSTEXIST
            ok = _comdlg32.GetOpenFileNameW(ctypes.byref(ofn))
        if not ok:
            return None
        return buf.value or None

    def message_box(title: str, text: str, error: bool = True) -> None:
        _user32.MessageBoxW(None, text, title, 0x10 if error else 0x40)

else:  # pragma: no cover - only used outside Windows

    def _run(save: bool, title: str, initialdir: str, initialfile: str, filetypes: FileTypes | None) -> str | None:
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", 1)
        types = list(filetypes or []) + [(t("all_files"), "*")]
        try:
            if save:
                res = filedialog.asksaveasfilename(parent=root, title=title, initialdir=initialdir, initialfile=initialfile, filetypes=types)
            else:
                res = filedialog.askopenfilename(parent=root, title=title, initialdir=initialdir, initialfile=initialfile, filetypes=types)
        finally:
            root.destroy()
        return res or None

    def message_box(title: str, text: str, error: bool = True) -> None:
        print(f"{title}: {text}", file=sys.stderr)


def open_file(title: str, initialdir: str = "", initialfile: str = "", filetypes: FileTypes | None = None) -> str | None:
    return _run(False, title, initialdir, initialfile, filetypes)


def save_file(title: str, initialdir: str = "", initialfile: str = "", filetypes: FileTypes | None = None) -> str | None:
    return _run(True, title, initialdir, initialfile, filetypes)
