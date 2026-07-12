"""Loading spinner, progress bar, status badge, and tooltip."""

from __future__ import annotations
import customtkinter as ctk
from gui.theme import ThemeManager, Dim, Fonts

tm = ThemeManager()
C = tm.C


class LoadingSpinner(ctk.CTkFrame):
    def __init__(self, master, message: str = "Loading...", **kw):
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
        frames = ["\u25CC", "\u25CD", "\u25CE", "\u25CF"]
        self._idx = (self._idx + 1) % len(frames)
        self._spinner.configure(text=frames[self._idx])
        self.after(180, self._animate)


class StatusBadge(ctk.CTkFrame):
    def __init__(self, master, text: str, color: str = "", **kw):
        if not color:
            color = C.primary
        super().__init__(master, fg_color=color, corner_radius=10,
                         height=22, **kw)
        self.pack_propagate(False)
        self._label = ctk.CTkLabel(
            self, text=text, font=Fonts.TINY_BOLD,
            text_color=C.text_on_primary,
        )
        self._label.pack(padx=8, expand=True)

    def set_text(self, t: str):
        self._label.configure(text=t)

    def set_color(self, c: str):
        self.configure(fg_color=c)


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

    def _hide(self, _=None):
        if self._tip:
            self._tip.destroy()
            self._tip = None


class AnimatedProgressBar(ctk.CTkFrame):
    """Animated horizontal progress bar."""

    def __init__(self, master, width: int = 300, height: int = 8, **kw):
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
            self._bar.place(relx=0, rely=0, relwidth=self._current, relheight=1)

    def _animate(self):
        diff = self._target - self._current
        if abs(diff) < 0.01:
            self._current = self._target
            self._bar.place(relx=0, rely=0, relwidth=self._current, relheight=1)
            return
        self._current += diff * 0.2
        self._bar.place(relx=0, rely=0, relwidth=max(0.01, self._current), relheight=1)
        self.after(16, self._animate)
