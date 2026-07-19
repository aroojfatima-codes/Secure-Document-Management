"""Dialogs, modals, and toast notification system."""

from __future__ import annotations
from typing import Callable
import customtkinter as ctk
from gui.theme import ThemeManager, Fonts

tm = ThemeManager()
C = tm.C


class BaseDialog(ctk.CTkToplevel):
    def __init__(self, master, title: str, message: str, accent: str = "",
                 button_text: str = "OK", button_variant: str = "primary",
                 on_close: Callable | None = None):
        super().__init__(master)
        if not accent:
            accent = C.primary
        self.title(title)
        self.configure(fg_color=C.bg_modal)
        self.resizable(False, False)
        try:
            self.transient(master)
            self.grab_set()
        except Exception:
            pass
        self._on_close = on_close

        w, h = 420, 240
        x = self.winfo_screenwidth() // 2 - w // 2
        y = self.winfo_screenheight() // 2 - h // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        ctk.CTkFrame(self, height=4, fg_color=accent, corner_radius=0).pack(fill="x")

        icon_map = {C.success: "\u2714", C.danger: "\u2718", C.warning: "\u26A0"}
        ctk.CTkLabel(
            self, text=icon_map.get(accent, "\u2139"),
            font=(Fonts.F, 32), text_color=accent,
        ).pack(pady=(20, 6))

        ctk.CTkLabel(
            self, text=title, font=Fonts.SUBTITLE,
            text_color=C.text_primary,
        ).pack(pady=(0, 6))

        ctk.CTkLabel(
            self, text=message, font=Fonts.BODY,
            text_color=C.text_secondary, wraplength=360,
        ).pack(padx=24, pady=(0, 16))

        from gui.components.forms import StyledButton
        StyledButton(self, text=button_text, variant=button_variant,
                     command=self._close, width=120).pack(pady=(0, 18))
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _close(self):
        try:
            self.grab_release()
        except Exception:
            pass
        if self._on_close:
            try:
                self._on_close()
            except Exception:
                pass
        self.destroy()


class SuccessDialog(BaseDialog):
    def __init__(self, master, message: str, title: str = "Success", **kw):
        super().__init__(master, title, message, accent=C.success,
                         button_variant="success", **kw)


class ErrorDialog(BaseDialog):
    def __init__(self, master, message: str, title: str = "Error", **kw):
        super().__init__(master, title, message, accent=C.danger,
                         button_variant="danger", **kw)


class WarningDialog(BaseDialog):
    def __init__(self, master, message: str, title: str = "Warning", **kw):
        super().__init__(master, title, message, accent=C.warning,
                         button_variant="warning", **kw)


class ConfirmDialog(ctk.CTkToplevel):
    def __init__(self, master, message: str, title: str = "Confirm",
                 on_yes: Callable | None = None, on_no: Callable | None = None):
        super().__init__(master)
        self.title(title)
        self.configure(fg_color=C.bg_modal)
        self.resizable(False, False)
        try:
            self.transient(master)
            self.grab_set()
        except Exception:
            pass
        self._on_yes = on_yes
        self._on_no = on_no

        w, h = 400, 210
        x = self.winfo_screenwidth() // 2 - w // 2
        y = self.winfo_screenheight() // 2 - h // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        ctk.CTkFrame(self, height=4, fg_color=C.warning, corner_radius=0).pack(fill="x")
        ctk.CTkLabel(self, text="\u26A0", font=(Fonts.F, 28),
                     text_color=C.warning).pack(pady=(16, 4))
        ctk.CTkLabel(self, text=title, font=Fonts.SUBTITLE,
                     text_color=C.text_primary).pack(pady=(0, 4))
        ctk.CTkLabel(self, text=message, font=Fonts.BODY,
                     text_color=C.text_secondary, wraplength=340).pack(padx=20, pady=(0, 14))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(pady=(0, 16))
        from gui.components.forms import StyledButton
        StyledButton(btn_frame, text="Cancel", variant="outline",
                     command=self._no, width=100).pack(side="left", padx=(0, 8))
        StyledButton(btn_frame, text="Confirm", variant="danger",
                     command=self._yes, width=100).pack(side="left")
        self.protocol("WM_DELETE_WINDOW", self._no)

    def _yes(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
        if self._on_yes:
            try:
                self._on_yes()
            except Exception:
                pass

    def _no(self):
        try:
            self.grab_release()
        except Exception:
            pass
        self.destroy()
        if self._on_no:
            try:
                self._on_no()
            except Exception:
                pass


class Toast(ctk.CTkToplevel):
    """Non-blocking toast that auto-dismisses with slide animation."""

    def __init__(self, master, message: str, toast_type: str = "success",
                 duration: int = 3000):
        try:
            super().__init__(master)
            self.overrideredirect(True)
            self.configure(fg_color=C.bg_card, border_width=1,
                           border_color=C.border_light)

            color_map = {
                "success": (C.success, "\u2714"),
                "error": (C.danger, "\u2718"),
                "warning": (C.warning, "\u26A0"),
                "info": (C.info, "\u2139"),
            }
            accent, icon_t = color_map.get(toast_type, color_map["info"])

            ctk.CTkFrame(self, width=4, fg_color=accent, corner_radius=0).pack(
                side="left", fill="y")
            ctk.CTkLabel(self, text=icon_t, font=Fonts.ICON,
                         text_color=accent, width=30).pack(side="left", padx=(6, 2))
            ctk.CTkLabel(
                self, text=message, font=Fonts.BODY,
                text_color=C.text_primary, wraplength=280,
            ).pack(side="left", padx=(0, 14), pady=10)

            self.update_idletasks()
            sw = self.winfo_screenwidth()
            w = self.winfo_width()
            start_x = sw + 10
            end_x = sw - w - 20
            y = 20
            self.geometry(f"+{start_x}+{y}")
            self._slide_in(start_x, end_x, y, 0, 8)
            self.after(duration, lambda: self._slide_out(end_x, start_x, y))
        except Exception:
            pass

    def _slide_in(self, start_x, end_x, y, step, total):
        def run():
            try:
                p = min((step + 1) / total, 1.0)
                eased = 1 - (1 - p) ** 3
                x = int(start_x + (end_x - start_x) * eased)
                self.geometry(f"+{x}+{y}")
                if step + 1 < total:
                    self.after(18, lambda: self._slide_in(start_x, end_x, y, step + 1, total))
            except Exception:
                pass
        self.after(18, run)

    def _slide_out(self, start_x, end_x, y, step=0, total=8):
        def run():
            try:
                p = min((step + 1) / total, 1.0)
                eased = p ** 3
                x = int(start_x + (end_x - start_x) * eased)
                self.geometry(f"+{x}+{y}")
                if step + 1 < total:
                    self.after(18, lambda: self._slide_out(start_x, end_x, y, step + 1, total))
                else:
                    self.destroy()
            except Exception:
                pass
        self.after(18, run)
