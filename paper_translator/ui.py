from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from .config import AppConfig, ConfigStore
from .server import ConnectorServer
from .translator import TranslationError, TranslationResult, Translator
from .windows import GlobalHotkey, TrayIcon, cursor_position, send_copy_shortcut


BG = "#F4F6F9"
CARD = "#FFFFFF"
TEXT = "#182230"
MUTED = "#667085"
BORDER = "#E4E7EC"
ACCENT = "#4F6EF7"
ACCENT_HOVER = "#405DE1"
SUCCESS = "#12B76A"
DANGER = "#D92D20"
ERROR_BG = "#FEF3F2"
ERROR_TEXT = "#B42318"
TRANSPARENT = "#010203"
FONT = "Microsoft YaHei UI"
RESULT_DEFAULT_WIDTH = 520
RESULT_DEFAULT_HEIGHT = 300
RESULT_MIN_WIDTH = 420
RESULT_MIN_HEIGHT = 240


def constrained_result_size(
    start_width: int,
    start_height: int,
    delta_x: int,
    delta_y: int,
    max_width: int,
    max_height: int,
) -> tuple[int, int]:
    width_limit = max(RESULT_MIN_WIDTH, max_width)
    height_limit = max(RESULT_MIN_HEIGHT, max_height)
    width = min(max(RESULT_MIN_WIDTH, start_width + delta_x), width_limit)
    height = min(max(RESULT_MIN_HEIGHT, start_height + delta_y), height_limit)
    return width, height


class PaperTranslatorApp:
    def __init__(self, root: tk.Tk, icon_path: Path | None = None) -> None:
        self.root = root
        self.root.title("轻译 · 论文划词翻译")
        self.root.geometry("620x570")
        self.root.minsize(580, 540)
        self.root.configure(bg=BG)
        self.root.protocol("WM_DELETE_WINDOW", self.hide_settings)

        self.store = ConfigStore()
        self.config = self.store.load()
        self.actions: queue.Queue[str] = queue.Queue()
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.hotkey = GlobalHotkey(self.actions)
        self.tray = TrayIcon(self.actions, icon_path)
        self.server: ConnectorServer | None = None
        self.result_window: tk.Toplevel | None = None
        self.result_canvas: tk.Canvas | None = None
        self.result_shadow: int | None = None
        self.result_card: int | None = None
        self.result_body_item: int | None = None
        self.result_resize_grip: tk.Canvas | None = None
        self.result_text: tk.Text | None = None
        self.result_model: tk.Label | None = None
        self.result_source: tk.Label | None = None
        self.result_mark: tk.Canvas | None = None
        self.result_mark_bg: int | None = None
        self.result_mark_text: int | None = None
        self.copy_button: tk.Button | None = None
        self.status_var = tk.StringVar(value="准备就绪")
        self.api_key_visible = False
        self._drag_origin: tuple[int, int] | None = None
        self._resize_origin: tuple[int, int, int, int] | None = None
        self._loading_generation = 0
        self._result_mode = "success"

        self._apply_theme()
        self._build_settings()
        self._center_settings()
        self.hotkey.start()
        self.tray.start()
        self._restart_server()
        self.root.after(160, self._poll)

        if self.config.api_key or self.config.base_url.startswith("http://127.0.0.1"):
            self.root.after(240, self.hide_settings)

    def _apply_theme(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "Accent.TButton", background=ACCENT, foreground="white", borderwidth=0,
            focusthickness=0, padding=(18, 10), font=(FONT, 10, "bold")
        )
        style.map("Accent.TButton", background=[("active", ACCENT_HOVER)])
        style.configure(
            "Quiet.TButton", background=CARD, foreground=TEXT, bordercolor=BORDER,
            lightcolor=BORDER, darkcolor=BORDER, padding=(16, 9), font=(FONT, 10)
        )
        style.map("Quiet.TButton", background=[("active", "#F8FAFC")])

    def _build_settings(self) -> None:
        outer = tk.Frame(self.root, bg=BG, padx=34, pady=28)
        outer.pack(fill="both", expand=True)
        header = tk.Frame(outer, bg=BG)
        header.pack(fill="x", pady=(0, 22))
        logo = tk.Canvas(header, width=46, height=46, bg=BG, highlightthickness=0)
        logo.pack(side="left", padx=(0, 13))
        self._rounded_rect(logo, 1, 1, 45, 45, 13, fill=ACCENT)
        logo.create_line(13, 14, 33, 14, fill="white", width=3, capstyle=tk.ROUND)
        logo.create_line(13, 22, 28, 22, fill="white", width=3, capstyle=tk.ROUND)
        logo.create_line(13, 30, 22, 30, fill="white", width=3, capstyle=tk.ROUND)
        logo.create_line(
            26, 30, 31, 35, 39, 24, fill="#D7F9E4", width=3,
            capstyle=tk.ROUND, joinstyle=tk.ROUND
        )
        heading = tk.Frame(header, bg=BG)
        heading.pack(side="left", fill="x", expand=True)
        tk.Label(heading, text="轻译", bg=BG, fg=TEXT, font=(FONT, 19, "bold")).pack(anchor="w")
        tk.Label(
            heading, text="选中论文文字，右键即可翻译", bg=BG, fg=MUTED, font=(FONT, 9)
        ).pack(anchor="w", pady=(2, 0))
        tk.Label(
            header, text="  本机运行  ", bg="#EAFBF3", fg="#087443",
            font=(FONT, 9), padx=6, pady=5
        ).pack(side="right")

        card = tk.Frame(
            outer, bg=CARD, padx=24, pady=22, highlightbackground=BORDER, highlightthickness=1
        )
        card.pack(fill="both", expand=True)
        tk.Label(card, text="模型设置", bg=CARD, fg=TEXT, font=(FONT, 12, "bold")).pack(anchor="w")
        tk.Label(
            card, text="支持所有 OpenAI 兼容的 Chat Completions 接口",
            bg=CARD, fg=MUTED, font=(FONT, 9)
        ).pack(anchor="w", pady=(4, 16))

        self.base_url = tk.StringVar(value=self.config.base_url)
        self.api_key = tk.StringVar(value=self.config.api_key)
        self.model = tk.StringVar(value=self.config.model)
        self.target_language = tk.StringVar(value=self.config.target_language)
        self._field(card, "API 地址", self.base_url)
        self.api_key_entry = self._field(
            card, "API Key", self.api_key, secret=True, trailing="显示", command=self._toggle_key
        )
        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x")
        left = tk.Frame(row, bg=CARD)
        left.pack(side="left", fill="x", expand=True, padx=(0, 8))
        right = tk.Frame(row, bg=CARD)
        right.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self._field(left, "模型", self.model, compact=True)
        self._field(right, "目标语言", self.target_language, compact=True)

        footer = tk.Frame(outer, bg=BG)
        footer.pack(fill="x", pady=(18, 0))
        self.status_dot = tk.Label(footer, text="●", bg=BG, fg=SUCCESS, font=(FONT, 9))
        self.status_dot.pack(side="left")
        tk.Label(footer, textvariable=self.status_var, bg=BG, fg=MUTED, font=(FONT, 9)).pack(
            side="left", padx=(6, 0)
        )
        ttk.Button(footer, text="测试连接", style="Quiet.TButton", command=self.test_connection).pack(
            side="right", padx=(10, 0)
        )
        ttk.Button(
            footer, text="保存并在后台运行", style="Accent.TButton", command=self.save_and_hide
        ).pack(side="right")

    def _field(
        self, parent: tk.Widget, label: str, variable: tk.StringVar, *,
        secret: bool = False, trailing: str = "", command: object | None = None,
        compact: bool = False,
    ) -> tk.Entry:
        block = tk.Frame(parent, bg=CARD)
        block.pack(fill="x", pady=(0, 14 if not compact else 0))
        tk.Label(block, text=label, bg=CARD, fg="#344054", font=(FONT, 9, "bold")).pack(
            anchor="w", pady=(0, 6)
        )
        shell = tk.Frame(block, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        shell.pack(fill="x")
        entry = tk.Entry(
            shell, textvariable=variable, show="●" if secret else "", relief="flat", bd=0,
            bg=CARD, fg=TEXT, insertbackground=TEXT, font=("Segoe UI", 10)
        )
        entry.pack(side="left", fill="x", expand=True, padx=12, pady=10)
        if trailing:
            tk.Button(
                shell, text=trailing, command=command, relief="flat", bd=0, bg=CARD,
                activebackground=CARD, fg=ACCENT, activeforeground=ACCENT_HOVER,
                cursor="hand2", font=(FONT, 9), padx=10
            ).pack(side="right", fill="y")
        return entry

    def _toggle_key(self) -> None:
        self.api_key_visible = not self.api_key_visible
        self.api_key_entry.configure(show="" if self.api_key_visible else "●")

    def _center_settings(self) -> None:
        self.root.update_idletasks()
        width, height = 620, 570
        x = max(0, (self.root.winfo_screenwidth() - width) // 2)
        y = max(0, (self.root.winfo_screenheight() - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def current_config(self) -> AppConfig:
        return AppConfig(
            base_url=self.base_url.get().strip(), api_key=self.api_key.get().strip(),
            model=self.model.get().strip(), target_language=self.target_language.get().strip(),
            timeout_seconds=self.config.timeout_seconds, port=self.config.port
        )

    def save_and_hide(self) -> None:
        try:
            self.config = self.current_config()
            self.store.save(self.config)
            self._restart_server()
        except (OSError, ValueError) as exc:
            self._set_status(str(exc), error=True)
            return
        self._set_status("配置已保存，右键翻译已就绪")
        self.root.after(350, self.hide_settings)

    def test_connection(self) -> None:
        try:
            config = self.current_config()
            config.validate()
        except ValueError as exc:
            self._set_status(str(exc), error=True)
            return
        self._set_status("正在连接模型…", pending=True)
        self._translate_async("Translate this sentence into Chinese.", config, test=True)

    def translate_selection(self) -> None:
        send_copy_shortcut()
        self.root.after(220, self._read_selection)

    def _read_selection(self) -> None:
        try:
            text = self.root.clipboard_get().strip()
        except tk.TclError:
            text = ""
        if not text:
            self._show_error("没有读取到选中的文字")
            return
        self._show_loading(text)
        self._translate_async(text, self.config)

    def _translate_async(self, text: str, config: AppConfig | None = None, test: bool = False) -> None:
        def worker() -> None:
            try:
                result = Translator(config or self.config).translate(text)
                self.events.put(("test_ok" if test else "translation", result))
            except TranslationError as exc:
                self.events.put(("test_error" if test else "translation_error", str(exc)))
        threading.Thread(target=worker, name="llm-request", daemon=True).start()

    def _create_result_window(self) -> None:
        window = tk.Toplevel(self.root)
        window.overrideredirect(True)
        window.configure(bg=TRANSPARENT)
        window.attributes("-topmost", True)
        try:
            window.wm_attributes("-transparentcolor", TRANSPARENT)
        except tk.TclError:
            window.configure(bg=CARD)
        window.geometry(f"{RESULT_DEFAULT_WIDTH}x{RESULT_DEFAULT_HEIGHT}")
        window.minsize(RESULT_MIN_WIDTH, RESULT_MIN_HEIGHT)
        window.bind("<Escape>", lambda _event: window.withdraw())
        canvas = tk.Canvas(window, bg=TRANSPARENT, highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        shadow = self._rounded_rect(canvas, 9, 12, 511, 292, 22, fill="#D8DEE9")
        card = self._rounded_rect(canvas, 5, 5, 507, 287, 22, fill=CARD, outline=BORDER)
        body = tk.Frame(canvas, bg=CARD)
        body_item = canvas.create_window(
            25, 22, anchor="nw", window=body, width=462, height=244
        )

        top = tk.Frame(body, bg=CARD, cursor="fleur")
        top.pack(fill="x")
        mark = tk.Canvas(top, width=30, height=30, bg=CARD, highlightthickness=0)
        mark.pack(side="left", padx=(0, 9))
        self.result_mark = mark
        self.result_mark_bg = self._rounded_rect(mark, 1, 1, 29, 29, 9, fill="#EEF1FF")
        self.result_mark_text = mark.create_text(
            15, 15, text="译", fill=ACCENT, font=(FONT, 11, "bold")
        )
        title = tk.Label(
            top, text="论文翻译", bg=CARD, fg=TEXT, font=(FONT, 11, "bold")
        )
        title.pack(side="left")
        self.result_model = tk.Label(
            top, text="", bg="#F2F4F7", fg=MUTED, font=("Segoe UI", 8), padx=8, pady=3
        )
        self.result_model.pack(side="left", padx=(10, 0))
        tk.Button(
            top, text="×", command=window.withdraw, relief="flat", bd=0, bg=CARD,
            activebackground="#F2F4F7", fg=MUTED, font=("Segoe UI", 15),
            cursor="hand2", width=2
        ).pack(side="right")
        tk.Frame(body, height=1, bg="#F0F1F3").pack(fill="x", pady=(12, 8))
        bottom = tk.Frame(body, bg=CARD)
        bottom.pack(side="bottom", fill="x", pady=(10, 0))
        self.result_source = tk.Label(
            bottom, text="", bg=CARD, fg="#98A2B3", font=(FONT, 8), anchor="w"
        )
        self._text_button(bottom, "设置", self.show_settings).pack(side="right", padx=(8, 0))
        self.copy_button = self._text_button(bottom, "复制译文", self._copy_result, accent=True)
        self.copy_button.pack(side="right")
        self.result_source.pack(side="left", fill="x", expand=True)
        text_shell = tk.Frame(body, bg=CARD)
        text_shell.pack(fill="both", expand=True)
        text_widget = tk.Text(
            text_shell, wrap="word", relief="flat", bd=0, bg=CARD, fg=TEXT,
            insertbackground=TEXT, selectbackground="#DCE4FF", selectforeground=TEXT,
            font=(FONT, 11), padx=2, pady=4, spacing1=2, spacing3=4, cursor="arrow"
        )
        scrollbar = ttk.Scrollbar(text_shell, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        text_widget.pack(side="left", fill="both", expand=True)
        self.result_window = window
        self.result_canvas = canvas
        self.result_shadow = shadow
        self.result_card = card
        self.result_body_item = body_item
        self.result_text = text_widget

        grip = tk.Canvas(
            window, width=20, height=20, bg=CARD, highlightthickness=0,
            cursor="size_nw_se"
        )
        for offset in (0, 5, 10):
            grip.create_line(
                18 - offset, 18, 18, 18 - offset,
                fill="#98A2B3", width=1, capstyle=tk.ROUND
            )
        grip.place(relx=1, rely=1, anchor="se", x=-14, y=-14)
        grip.bind("<ButtonPress-1>", self._begin_resize)
        grip.bind("<B1-Motion>", self._resize_result)
        grip.bind("<ButtonRelease-1>", self._end_resize)
        self.result_resize_grip = grip

        self._bind_drag_handle(top, mark, title, self.result_model)
        window.bind("<Configure>", self._layout_result_window)
        window.update_idletasks()
        self._layout_result_window()

    def _text_button(self, parent: tk.Widget, text: str, command: object, *, accent: bool = False) -> tk.Button:
        return tk.Button(
            parent, text=text, command=command, relief="flat", bd=0,
            bg=ACCENT if accent else "#F2F4F7",
            activebackground=ACCENT_HOVER if accent else "#E9ECF0",
            fg="white" if accent else "#475467", activeforeground="white" if accent else TEXT,
            font=(FONT, 9, "bold" if accent else "normal"), padx=13, pady=6, cursor="hand2"
        )

    def _bind_drag_handle(self, *widgets: tk.Widget) -> None:
        for widget in widgets:
            widget.configure(cursor="fleur")
            widget.bind("<ButtonPress-1>", self._begin_drag)
            widget.bind("<B1-Motion>", self._drag_result)
            widget.bind("<ButtonRelease-1>", self._end_drag)

    def _layout_result_window(self, event: tk.Event | None = None) -> None:
        if event is not None and event.widget is not self.result_window:
            return
        if not (
            self.result_window and self.result_canvas and self.result_shadow
            and self.result_card and self.result_body_item
        ):
            return
        width = max(RESULT_MIN_WIDTH, self.result_window.winfo_width())
        height = max(RESULT_MIN_HEIGHT, self.result_window.winfo_height())
        self.result_canvas.coords(
            self.result_shadow, *self._rounded_rect_points(9, 12, width - 9, height - 8, 22)
        )
        self.result_canvas.coords(
            self.result_card, *self._rounded_rect_points(5, 5, width - 13, height - 13, 22)
        )
        self.result_canvas.itemconfigure(
            self.result_body_item, width=width - 58, height=height - 56
        )

    def _begin_resize(self, event: tk.Event) -> str:
        if self.result_window:
            self._resize_origin = (
                event.x_root,
                event.y_root,
                self.result_window.winfo_width(),
                self.result_window.winfo_height(),
            )
        return "break"

    def _resize_result(self, event: tk.Event) -> str:
        if self.result_window and self._resize_origin:
            start_x, start_y, start_width, start_height = self._resize_origin
            max_width = self.result_window.winfo_screenwidth() - self.result_window.winfo_x() - 8
            max_height = self.result_window.winfo_screenheight() - self.result_window.winfo_y() - 8
            width, height = constrained_result_size(
                start_width,
                start_height,
                event.x_root - start_x,
                event.y_root - start_y,
                max_width,
                max_height,
            )
            self.result_window.geometry(f"{width}x{height}")
        return "break"

    def _end_resize(self, _event: tk.Event) -> str:
        self._resize_origin = None
        return "break"

    def _show_loading(self, source: str) -> None:
        self._loading_generation += 1
        generation = self._loading_generation
        self._show_result("", source, mode="loading")
        self._animate_loading(generation, 0)

    def _animate_loading(self, generation: int, frame: int) -> None:
        if (
            generation != self._loading_generation
            or self._result_mode != "loading"
            or not self.result_window
            or not self.result_window.winfo_exists()
            or self.result_window.state() == "withdrawn"
            or not self.result_text
        ):
            return
        dots = ("●  ·  ·", "·  ●  ·", "·  ·  ●", "·  ●  ·")[frame % 4]
        messages = ("正在理解句意", "正在对齐学术术语", "正在组织自然译文")
        message = messages[(frame // 4) % len(messages)]
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.tag_configure(
            "loading_title", font=(FONT, 12, "bold"), foreground=TEXT, spacing3=14
        )
        self.result_text.tag_configure(
            "loading_dots", font=("Segoe UI", 12, "bold"), foreground=ACCENT, spacing3=12
        )
        self.result_text.tag_configure("loading_hint", font=(FONT, 9), foreground=MUTED)
        self.result_text.insert("end", "正在翻译\n", "loading_title")
        self.result_text.insert("end", f"{dots}\n", "loading_dots")
        self.result_text.insert("end", message, "loading_hint")
        self.result_text.configure(state="disabled")
        self.result_window.after(220, lambda: self._animate_loading(generation, frame + 1))

    def _show_result(
        self, translation: str, source: str = "", model: str = "", *, mode: str = "success"
    ) -> None:
        was_visible = bool(
            self.result_window
            and self.result_window.winfo_exists()
            and self.result_window.state() != "withdrawn"
        )
        if not self.result_window or not self.result_window.winfo_exists():
            self._create_result_window()
        assert self.result_window and self.result_text and self.result_model and self.result_source
        self._result_mode = mode
        if mode != "loading":
            self._loading_generation += 1
        self._apply_result_mode(mode, model)
        self.result_text.configure(state="normal")
        self.result_text.delete("1.0", "end")
        self.result_text.insert("1.0", translation)
        self.result_text.configure(state="disabled")
        preview = " ".join(source.split())[:42]
        if mode == "error":
            self.result_source.configure(text="请检查 API 地址、Key 和模型设置", fg=ERROR_TEXT)
        else:
            self.result_source.configure(text=f"原文  {preview}" if preview else "", fg="#98A2B3")
        if not was_visible:
            x, y = cursor_position()
            screen_w = self.result_window.winfo_screenwidth()
            screen_h = self.result_window.winfo_screenheight()
            width = max(RESULT_MIN_WIDTH, self.result_window.winfo_width())
            height = max(RESULT_MIN_HEIGHT, self.result_window.winfo_height())
            pos_x = min(max(8, x + 18), max(8, screen_w - width - 8))
            pos_y = min(max(8, y + 18), max(8, screen_h - height - 8))
            self.result_window.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
            self.result_window.attributes("-alpha", 0.0)
            self.result_window.deiconify()
            self._fade_in(0.0)
        self.result_window.lift()

    def _apply_result_mode(self, mode: str, model: str) -> None:
        assert (
            self.result_mark and self.result_mark_bg and self.result_mark_text
            and self.result_model and self.result_text and self.copy_button
        )
        if mode == "error":
            self.result_mark.itemconfigure(self.result_mark_bg, fill=ERROR_BG)
            self.result_mark.itemconfigure(self.result_mark_text, text="!", fill=DANGER)
            self.result_model.configure(text="翻译失败", bg=ERROR_BG, fg=ERROR_TEXT)
            self.result_text.configure(fg=ERROR_TEXT)
            self.copy_button.configure(
                state="normal", text="复制详情", bg=DANGER, activebackground=ERROR_TEXT,
                fg="white", activeforeground="white"
            )
        elif mode == "loading":
            self.result_mark.itemconfigure(self.result_mark_bg, fill="#EEF1FF")
            self.result_mark.itemconfigure(self.result_mark_text, text="译", fill=ACCENT)
            self.result_model.configure(text="处理中", bg="#EEF1FF", fg=ACCENT)
            self.result_text.configure(fg=MUTED)
            self.copy_button.configure(
                state="disabled", text="请稍候", bg="#F2F4F7", disabledforeground="#98A2B3"
            )
        else:
            self.result_mark.itemconfigure(self.result_mark_bg, fill="#EEF1FF")
            self.result_mark.itemconfigure(self.result_mark_text, text="译", fill=ACCENT)
            self.result_model.configure(text=model or "LLM", bg="#F2F4F7", fg=MUTED)
            self.result_text.configure(fg=TEXT)
            self.copy_button.configure(
                state="normal", text="复制译文", bg=ACCENT, activebackground=ACCENT_HOVER,
                fg="white", activeforeground="white"
            )

    def _fade_in(self, alpha: float) -> None:
        if not self.result_window or not self.result_window.winfo_exists():
            return
        alpha = min(1.0, alpha + 0.18)
        self.result_window.attributes("-alpha", alpha)
        if alpha < 1.0:
            self.result_window.after(16, lambda: self._fade_in(alpha))

    def _begin_drag(self, event: tk.Event) -> str:
        if self.result_window:
            self._drag_origin = (
                event.x_root - self.result_window.winfo_x(),
                event.y_root - self.result_window.winfo_y()
            )
        return "break"

    def _drag_result(self, event: tk.Event) -> str:
        if self.result_window and self._drag_origin:
            x = event.x_root - self._drag_origin[0]
            y = event.y_root - self._drag_origin[1]
            self.result_window.geometry(f"+{x}+{y}")
        return "break"

    def _end_drag(self, _event: tk.Event) -> str:
        self._drag_origin = None
        return "break"

    def _copy_result(self) -> None:
        if not self.result_text:
            return
        value = self.result_text.get("1.0", "end-1c")
        self.root.clipboard_clear()
        self.root.clipboard_append(value)
        if self.result_source:
            self.result_source.configure(text="已复制到剪贴板")

    def _show_error(self, message: str) -> None:
        self._show_result(f"翻译失败\n\n{message}", mode="error")

    def _set_status(self, message: str, *, error: bool = False, pending: bool = False) -> None:
        self.status_var.set(message)
        self.status_dot.configure(fg=DANGER if error else ("#F79009" if pending else SUCCESS))

    def show_settings(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def hide_settings(self) -> None:
        self.root.withdraw()

    def _restart_server(self) -> None:
        if self.server:
            self.server.stop()
        try:
            self.server = ConnectorServer(
                "127.0.0.1", self.config.port,
                lambda text: Translator(self.config).translate(text), self.events
            )
            self.server.start()
            self._set_status("右键翻译服务已就绪")
        except OSError as exc:
            self.server = None
            self._set_status(f"本地连接器未启动：{exc}", error=True)

    def _poll(self) -> None:
        try:
            while True:
                action = self.actions.get_nowait()
                if action == "translate_selection":
                    self.translate_selection()
                elif action == "show_settings":
                    self.show_settings()
                elif action == "hotkey_error":
                    self._set_status("备用快捷键 Ctrl+Shift+T 已被占用", error=True)
                elif action == "tray_error":
                    self._set_status("系统托盘初始化失败，请保持设置窗口打开", error=True)
                    self.show_settings()
                elif action == "exit":
                    self.close()
                    return
        except queue.Empty:
            pass
        try:
            while True:
                event, payload = self.events.get_nowait()
                if event == "translation_started":
                    self._show_loading(str(payload))
                elif event == "translation":
                    result = payload
                    assert isinstance(result, TranslationResult)
                    self._show_result(result.translation, result.source, result.model)
                elif event == "translation_error":
                    self._show_error(str(payload))
                elif event == "test_ok":
                    self._set_status("连接成功，当前模型可以正常翻译")
                elif event == "test_error":
                    self._set_status(f"连接失败：{payload}", error=True)
        except queue.Empty:
            pass
        self.root.after(160, self._poll)

    @staticmethod
    def _rounded_rect_points(
        x1: int, y1: int, x2: int, y2: int, radius: int
    ) -> list[int]:
        return [
            x1 + radius, y1, x2 - radius, y1, x2, y1, x2, y1 + radius,
            x2, y2 - radius, x2, y2, x2 - radius, y2, x1 + radius, y2,
            x1, y2, x1, y2 - radius, x1, y1 + radius, x1, y1,
        ]

    @staticmethod
    def _rounded_rect(
        canvas: tk.Canvas, x1: int, y1: int, x2: int, y2: int, radius: int, **kwargs: object
    ) -> int:
        points = PaperTranslatorApp._rounded_rect_points(x1, y1, x2, y2, radius)
        return canvas.create_polygon(points, smooth=True, splinesteps=24, **kwargs)

    def close(self) -> None:
        self.hotkey.stop()
        self.tray.stop()
        if self.server:
            self.server.stop()
        self.root.destroy()
