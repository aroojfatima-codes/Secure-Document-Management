"""Loading spinner, progress bar, status badge, and tooltip."""

from __future__ import annotations
import customtkinter as ctk
from gui.theme import ThemeManager, Fonts

tm = ThemeManager()
C = tm.C


class LoadingSpinner(ctk.CTkFrame):
    def __init__(self, master, message: str = "Loading...", **kw):
        kw.pop("fg_color", None)
        super().__init__(master, fg_color=C.bg_main, **kw)
        self._running = False
        self._idx = 0

        self._spinner = ctk.CTkLabel(
            self, text="\u25CC", font=(Fonts.F, 28),
            text_color=C.primary,
        )
        self._spinner.pack(pady=(0, 8))
        self._label = ctk.CTkLabel(
            self, text=message, font=Fonts.SUBTITLE,
            text_color=C.text_primary,
        )
        self._label.pack()

    def start(self):
        self._running = True
        self._animate()

    def stop(self):
        self._running = False

    def _animate(self):
        if not self._running:
            return
        try:
            frames = ["\u25CC", "\u25CD", "\u25CE", "\u25CF"]
            self._idx = (self._idx + 1) % len(frames)
            self._spinner.configure(text=frames[self._idx])
            self.after(180, self._animate)
        except Exception:
            self._running = False


class StatusBadge(ctk.CTkFrame):
    def __init__(self, master, text: str, color: str = "", height: int = 22, **kw):
        if not color:
            color = C.primary
        kw.pop("height", None)
        kw.pop("fg_color", None)
        kw.pop("corner_radius", None)
        super().__init__(master, fg_color=color, corner_radius=10,
                         height=height, **kw)
        self.pack_propagate(False)
        self._label = ctk.CTkLabel(
            self, text=text, font=Fonts.TINY_BOLD,
            text_color=C.text_on_primary,
        )
        self._label.pack(padx=8, expand=True)

    def set_text(self, t: str):
        try:
            self._label.configure(text=t)
        except Exception:
            pass

    def set_color(self, c: str):
        try:
            self.configure(fg_color=c)
        except Exception:
            pass


class ToolTip:
    """Hover tooltip for any widget."""

    def __init__(self, widget, text: str):
        self._widget = widget
        self._text = text
        self._tip = None
        widget.bind("<Enter>", self._show, add="+")
        widget.bind("<Leave>", self._hide, add="+")

    def _show(self, _=None):
        if self._tip:
            return
        try:
            x = self._widget.winfo_rootx() + 20
            y = self._widget.winfo_rooty() + self._widget.winfo_height() + 6
            self._tip = ctk.CTkToplevel(self._widget)
            self._tip.overrideredirect(True)
            self._tip.configure(fg_color=C.bg_tooltip)
            ctk.CTkLabel(
                self._tip, text=self._text, font=Fonts.TINY,
                text_color=C.text_primary, padx=8, pady=4,
            ).pack()
            self._tip.geometry(f"+{x}+{y}")
        except Exception:
            self._tip = None

    def _hide(self, _=None):
        if self._tip:
            try:
                self._tip.destroy()
            except Exception:
                pass
            self._tip = None


class AnimatedProgressBar(ctk.CTkFrame):
    """Animated horizontal progress bar."""

    def __init__(self, master, width: int = 300, height: int = 8, **kw):
        kw.pop("width", None)
        kw.pop("height", None)
        kw.pop("fg_color", None)
        kw.pop("corner_radius", None)
        super().__init__(master, fg_color=C.bg_input, corner_radius=height // 2,
                         width=width, height=height, **kw)
        self.pack_propagate(False)
        self._bar = ctk.CTkFrame(
            self, fg_color=C.primary, corner_radius=height // 2,
        )
        self._bar.place(relx=0, rely=0, relwidth=0, relheight=1)
        self._target = 0.0
        self._current = 0.0

    def set_progress(self, value: float, animate: bool = True):
        self._target = max(0.0, min(1.0, value))
        if animate:
            self._animate()
        else:
            self._current = self._target
            try:
                self._bar.place(relx=0, rely=0, relwidth=self._current, relheight=1)
            except Exception:
                pass

    def _animate(self):
        try:
            diff = self._target - self._current
            if abs(diff) < 0.01:
                self._current = self._target
                self._bar.place(relx=0, rely=0, relwidth=self._current, relheight=1)
                return
            self._current += diff * 0.2
            self._bar.place(relx=0, rely=0, relwidth=max(0.01, self._current), relheight=1)
            self.after(16, self._animate)
        except Exception:
            pass
