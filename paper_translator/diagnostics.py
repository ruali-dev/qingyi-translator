"""Offline release check using the same result window as normal translations."""
from __future__ import annotations

import json
import time
import tkinter as tk
from pathlib import Path

from PIL import ImageGrab

from . import __version__
from .ui import PaperTranslatorApp


def check_rendering(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    root = tk.Tk()
    root.withdraw()
    app = PaperTranslatorApp.__new__(PaperTranslatorApp)
    app.root = root
    app.result_window = None
    app._loading_generation = 0
    sample = (
        r"正态分布的密度为 \(p(x)=\frac{1}{\sqrt{2\pi\sigma^2}}"
        r"e^{-\frac{(x-\mu)^2}{2\sigma^2}}\)，其积分满足：" "\n"
        r"\[\int_{-\infty}^{\infty}p(x)\,dx=1\]" "\n"
        r"矩阵与损失函数：\[A=\begin{pmatrix}a&b\\c&d\end{pmatrix},"
        r"\quad L=\sum_{i=1}^{n}(y_i-\hat y_i)^2\]" "\n"
        r"分段函数：\[f(x)=\begin{cases}x^2&x>0\\0&x\leq0\end{cases}\]"
    )
    try:
        app._show_result(sample, "Offline rendering check", "v" + __version__)
        window, widget = app.result_window, app.result_text
        assert window is not None and widget is not None
        window.geometry("740x600+100+100")
        deadline = time.monotonic() + 20
        while time.monotonic() < deadline:
            root.update()
            if len(widget.image_names()) == 4:
                break
            time.sleep(0.02)
        assert len(widget.image_names()) == 4, "Bundled formula rendering failed"
        assert widget.source == sample, "Full copy lost source"
        widget.tag_add("sel", "1.0", "end-1c")
        assert r"\begin{pmatrix}" in widget.selection_source(), "Selection lost formula"
        widget.tag_remove("sel", "1.0", "end")
        root.update()
        ImageGrab.grab(window=window.winfo_id()).save(output / "formulas.png")
        window.geometry("420x300+100+100")
        root.update()
        widget._resize_images()
        assert all(photo.width() <= widget.winfo_width() for _, _, photo in widget._images)
        (output / "result.json").write_text(json.dumps({
            "version": __version__, "formula_count": len(widget.image_names()),
            "copy": "passed", "resize": "passed", "offline": True,
        }, indent=2), encoding="utf-8")
    finally:
        root.destroy()
