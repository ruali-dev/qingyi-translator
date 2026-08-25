from __future__ import annotations

import ctypes
import queue
import threading
from ctypes import wintypes

import win32api
import win32con
import win32gui


WM_HOTKEY = 0x0312
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
VK_T = 0x54
HOTKEY_ID = 0x5A71


def send_copy_shortcut() -> None:
    user32 = ctypes.windll.user32
    key_up = 0x0002
    user32.keybd_event(win32con.VK_CONTROL, 0, 0, 0)
    user32.keybd_event(ord("C"), 0, 0, 0)
    user32.keybd_event(ord("C"), 0, key_up, 0)
    user32.keybd_event(win32con.VK_CONTROL, 0, key_up, 0)


def cursor_position() -> tuple[int, int]:
    point = wintypes.POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(point))
    return point.x, point.y


class GlobalHotkey:
    def __init__(self, actions: queue.Queue[str]) -> None:
        self.actions = actions
        self.thread: threading.Thread | None = None
        self.thread_id: int | None = None

    def start(self) -> None:
        self.thread = threading.Thread(target=self._run, name="global-hotkey", daemon=True)
        self.thread.start()

    def stop(self) -> None:
        if self.thread_id:
            ctypes.windll.user32.PostThreadMessageW(self.thread_id, win32con.WM_QUIT, 0, 0)

    def _run(self) -> None:
        self.thread_id = win32api.GetCurrentThreadId()
        user32 = ctypes.windll.user32
        if not user32.RegisterHotKey(None, HOTKEY_ID, MOD_CONTROL | MOD_SHIFT, VK_T):
            self.actions.put("hotkey_error")
            return
        message = wintypes.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
                if message.message == WM_HOTKEY and message.wParam == HOTKEY_ID:
                    self.actions.put("translate_selection")
        finally:
            user32.UnregisterHotKey(None, HOTKEY_ID)


class TrayIcon:
    WM_TRAY = win32con.WM_USER + 20
    CMD_SETTINGS = 1001
    CMD_EXIT = 1002

    def __init__(self, actions: queue.Queue[str]) -> None:
        self.actions = actions
        self.thread = threading.Thread(target=self._run, name="tray-icon", daemon=True)
        self.hwnd: int | None = None

    def start(self) -> None:
        self.thread.start()

    def stop(self) -> None:
        if self.hwnd:
            win32gui.PostMessage(self.hwnd, win32con.WM_CLOSE, 0, 0)

    def _run(self) -> None:
        class_name = "PaperTranslatorTrayWindow"
        message_map = {
            self.WM_TRAY: self._on_tray,
            win32con.WM_COMMAND: self._on_command,
            win32con.WM_DESTROY: self._on_destroy,
        }
        window_class = win32gui.WNDCLASS()
        window_class.hInstance = win32api.GetModuleHandle(None)
        window_class.lpszClassName = class_name
        window_class.lpfnWndProc = message_map
        try:
            win32gui.RegisterClass(window_class)
        except win32gui.error:
            pass
        self.hwnd = win32gui.CreateWindow(
            class_name, class_name, 0, 0, 0, 0, 0, 0, 0, window_class.hInstance, None
        )
        icon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        try:
            win32gui.Shell_NotifyIcon(
                win32gui.NIM_ADD,
                (self.hwnd, 0, win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP,
                 self.WM_TRAY, icon, "轻译 · Qingyi"),
            )
        except win32gui.error:
            self.actions.put("tray_error")
            win32gui.DestroyWindow(self.hwnd)
            return
        win32gui.PumpMessages()

    def _on_tray(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        if lparam == win32con.WM_LBUTTONUP:
            self.actions.put("show_settings")
        elif lparam == win32con.WM_RBUTTONUP:
            menu = win32gui.CreatePopupMenu()
            win32gui.AppendMenu(menu, win32con.MF_STRING, self.CMD_SETTINGS, "设置")
            win32gui.AppendMenu(menu, win32con.MF_SEPARATOR, 0, "")
            win32gui.AppendMenu(menu, win32con.MF_STRING, self.CMD_EXIT, "退出")
            x, y = win32gui.GetCursorPos()
            win32gui.SetForegroundWindow(hwnd)
            win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN, x, y, 0, hwnd, None)
            win32gui.DestroyMenu(menu)
        return 0

    def _on_command(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        command = win32api.LOWORD(wparam)
        if command == self.CMD_SETTINGS:
            self.actions.put("show_settings")
        elif command == self.CMD_EXIT:
            self.actions.put("exit")
        return 0

    def _on_destroy(self, hwnd: int, msg: int, wparam: int, lparam: int) -> int:
        try:
            win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, (hwnd, 0))
        except win32gui.error:
            pass
        finally:
            win32gui.PostQuitMessage(0)
        return 0
