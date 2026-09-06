"""Tk text with offline formula images and lossless clipboard contents."""
from __future__ import annotations

import tkinter as tk
from concurrent.futures import ThreadPoolExecutor

from PIL import Image, ImageTk

from .formulas import Segment, render_formula, split_formulas


class MathText(tk.Text):
    def __init__(self, master: tk.Widget, **kwargs: object) -> None:
        super().__init__(master, **kwargs)
        self.source = ""
        self._generation = 0
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="formula-render")
        self._future = None
        self._images: list[tuple[str, Image.Image, ImageTk.PhotoImage]] = []
        self._image_sources: dict[str, str] = {}
        self._resize_job: str | None = None
        self.tag_configure("formula_block", justify="center", spacing1=8, spacing3=8)
        self.bind("<Configure>", self._schedule_resize, add=True)
        self.bind("<<Copy>>", self._copy_selection)
        self.bind("<Destroy>", self._shutdown, add=True)

    def set_content(self, text: str, *, math: bool = True) -> None:
        self.source = text
        self._generation += 1
        generation = self._generation
        if self._future:
            self._future.cancel()
        self._images.clear()
        self._image_sources.clear()
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.insert("1.0", text)
        self.configure(state="disabled")
        parts = split_formulas(text) if math else []
        if not any(part.latex for part in parts):
            return
        size = max(14, round(11 * float(self.tk.call("tk", "scaling"))))
        self._future = self._executor.submit(self._render, parts, size)
        future = self._future

        def finish() -> None:
            if not self.winfo_exists() or generation != self._generation:
                return
            if not future.done():
                self.after(40, finish)
                return
            self._insert_rendered(parts, future.result())

        self.after(40, finish)

    @staticmethod
    def _render(parts: list[Segment], size: int) -> list[Image.Image | None]:
        return [render_formula(part.latex, part.display, size) if part.latex else None
                for part in parts]

    def _insert_rendered(self, parts: list[Segment], images: list[Image.Image | None]) -> None:
        position = self.yview()[0]
        self.configure(state="normal")
        self.delete("1.0", "end")
        for index, (part, original) in enumerate(zip(parts, images)):
            if original is None:
                self.insert("end", part.raw)
                continue
            if part.display and self.index("end-1c").split(".")[1] != "0":
                self.insert("end", "\n")
            start = self.index("end-1c")
            photo = self._photo(original)
            name = self.image_create("end", image=photo, align="center", padx=2)
            self._images.append((name, original, photo))
            self._image_sources[name] = part.raw
            if part.display:
                if index + 1 == len(parts) or not parts[index + 1].raw.startswith("\n"):
                    self.insert("end", "\n")
                self.tag_add("formula_block", start, "end-1c")
        self.configure(state="disabled")
        self.yview_moveto(position)

    def _photo(self, original: Image.Image) -> ImageTk.PhotoImage:
        width = max(40, self.winfo_width() - 16)
        if original.width > width:
            original = original.resize(
                (width, max(1, round(original.height * width / original.width))),
                Image.Resampling.LANCZOS,
            )
        return ImageTk.PhotoImage(original, master=self)

    def _schedule_resize(self, _event: tk.Event) -> None:
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(100, self._resize_images)

    def _resize_images(self) -> None:
        self._resize_job = None
        for index, (name, original, _photo) in enumerate(self._images):
            photo = self._photo(original)
            self.image_configure(name, image=photo)
            self._images[index] = (name, original, photo)

    def selection_source(self) -> str:
        if not self.tag_ranges("sel"):
            return ""
        return "".join(self._image_sources.get(value, "") if kind == "image" else value
                       for kind, value, _index in self.dump("sel.first", "sel.last", text=True, image=True))

    def _copy_selection(self, _event: tk.Event) -> str:
        value = self.selection_source()
        if value:
            self.clipboard_clear()
            self.clipboard_append(value)
        return "break"

    def _shutdown(self, event: tk.Event) -> None:
        if event.widget is self:
            self._generation += 1
            self._executor.shutdown(wait=False, cancel_futures=True)
