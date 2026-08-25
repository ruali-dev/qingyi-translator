from __future__ import annotations

import ctypes
import sys
import tkinter as tk
from pathlib import Path

from .ui import PaperTranslatorApp


def resource_path(*parts: str) -> Path:
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return bundle_root.joinpath(*parts)


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("论文划词翻译器当前只支持 Windows")
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass
    root = tk.Tk()
    icon_path = resource_path("assets", "icon", "qingyi.ico")
    if icon_path.exists():
        try:
            root.iconbitmap(default=str(icon_path))
        except tk.TclError:
            pass
    PaperTranslatorApp(root, icon_path)
    root.mainloop()
