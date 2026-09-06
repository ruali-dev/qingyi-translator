import time
import tkinter as tk

import pytest

from paper_translator.formulas import render_formula, split_formulas
from paper_translator.math_text import MathText
from paper_translator.translator import normalize_selection, Translator
from paper_translator.config import AppConfig


@pytest.mark.parametrize("source,latex,display", [
    (r"$x$", "x", False),
    (r"$1$", "1", False),
    (r"$x_i^2$", "x_i^2", False),
    (r"\(\alpha + \beta\)", r"\alpha + \beta", False),
    (r"$$\frac{a}{b}$$", r"\frac{a}{b}", True),
    (r"\[\sum_{i=1}^n i\]", r"\sum_{i=1}^n i", True),
    (r"\begin{align}a&=b\\c&=d\end{align}", r"\begin{align}a&=b\\c&=d\end{align}", True),
])
def test_recognize_delimiters(source, latex, display):
    parts = split_formulas("前文" + source + "后文")
    assert len(parts) == 3
    assert parts[1].latex == latex
    assert parts[1].display == display
    assert "".join(part.raw for part in parts) == "前文" + source + "后文"


@pytest.mark.parametrize("source", [
    r"Price $5 and $10, escaped \$20; [1]", r"`$x$`",
    "```latex\n$x$\n```", r"Unclosed \(x", r"Unclosed $x", "plain 中文",
])
def test_prose_code_and_incomplete_math_stay_literal(source):
    parts = split_formulas(source)
    assert not any(part.latex for part in parts)
    assert "".join(part.raw for part in parts) == source


def test_normalize_preserves_math_line_breaks_and_subtraction():
    math = "\\[a-\nb + \\text{two  words}\\]"
    assert normalize_selection("A transla-\ntion\n" + math + "\nworks.") == "A translation " + math + " works."


@pytest.mark.parametrize("latex", [
    r"E=mc^2", r"\frac{-b\pm\sqrt{b^2-4ac}}{2a}",
    r"\sum_{i=1}^{n} x_i", r"\int_0^\infty e^{-x}\,dx",
    r"\begin{pmatrix}a&b\\c&d\end{pmatrix}",
    r"f(x)=\begin{cases}x^2&x>0\\0&x\leq0\end{cases}",
    r"\begin{aligned}a&=b+c\\d&=e\end{aligned}",
    r"\begin{equation}a=b\end{equation}",
])
def test_real_offline_renderer(latex):
    image = render_formula(latex, True, 20)
    assert image is not None
    assert image.width > 5 and image.height > 5
    assert image.getbbox() is not None


def test_invalid_formula_falls_back():
    assert render_formula(r"\frac{", True, 20) is None
    assert render_formula("x" * 4001, True, 20) is None


def test_prompt_preserves_latex():
    prompt = Translator(AppConfig())._payload("source")["messages"][0]["content"]
    assert "LaTeX" in prompt and r"\(" in prompt and r"\[" in prompt


def wait_for_images(root, widget):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        root.update()
        if widget.image_names():
            return
        time.sleep(0.02)
    pytest.fail("Formula did not render in Tk")


def test_tk_render_copy_resize_and_replacement():
    root = tk.Tk()
    root.geometry("520x300")
    widget = MathText(root)
    widget.pack(fill="both", expand=True)
    try:
        source = r"结果：\(\frac{a}{b}\)，矩阵\[\begin{pmatrix}a&b\\c&d\end{pmatrix}\]完成。"
        widget.set_content(source)
        wait_for_images(root, widget)
        assert len(widget.image_names()) == 2
        assert widget.source == source
        widget.tag_add("sel", "1.0", "end-1c")
        copied = widget.selection_source()
        assert r"\(\frac{a}{b}\)" in copied
        assert r"\begin{pmatrix}a&b\\c&d\end{pmatrix}" in copied
        root.geometry("300x240")
        root.update()
        widget._resize_images()
        assert all(photo.width() <= widget.winfo_width() for _, _, photo in widget._images)
        widget.set_content(r"\[\int_0^1 x\,dx\]")
        widget.set_content("请求失败", math=False)
        root.update()
        assert not widget.image_names()
        assert widget.get("1.0", "end-1c") == "请求失败"
        widget.set_content(r"正确 $x$，无效 \[\frac{\]")
        wait_for_images(root, widget)
        assert len(widget.image_names()) == 1
        assert r"\[\frac{\]" in widget.get("1.0", "end-1c")
    finally:
        root.destroy()
