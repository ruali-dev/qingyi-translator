from __future__ import annotations

import ctypes
import sys
import tkinter as tk

from .ui import PaperTranslatorApp


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("论文划词翻译器当前只支持 Windows")
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass
    root = tk.Tk()
    PaperTranslatorApp(root)
    root.mainloop()

