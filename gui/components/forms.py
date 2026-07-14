"""Form inputs, buttons, password fields, dropdowns, text areas."""

from __future__ import annotations
from typing import Callable
import customtkinter as ctk
from gui.theme import ThemeManager, Dim, Fonts

tm = ThemeManager()
C = tm.C


class StyledEntry(ctk.CTkFrame):
    def __init__(self, master, label: str = "", placeholder: str = "",
                 show: str = "", width: int = 0, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        if label:
            ctk.CTkLabel(
                self, text=label, font=Fonts.SMALL_BOLD,
                text_color=C.text_secondary, anchor="w",
            ).pack(fill="x", pady=(0, 4))
        entry_width = width if width > 0 else 0
        self.entry = ctk.CTkEntry(
            self, placeholder_text=placeholder, font=Fonts.BODY,
            fg_color=C.bg_input, border_color=C.border,
            text_color=C.text_primary, placeholder_text_color=C.text_dim,
            corner_radius=Dim.RADIUS, height=36, width=entry_width, show=show,
        )
        self.entry.pack(fill="x")

    def get_value(self) -> str:
        return self.entry.get().strip()

    def set_value(self, v: str):
        self.entry.delete(0, "end")
        self.entry.insert(0, v)

    def clear(self):
        self.entry.delete(0, "end")

    def focus(self):
        self.entry.focus_set()

    def apply_theme(self):
        self.entry.configure(fg_color=C.bg_input, border_color=C.border,
                             text_color=C.text_primary)


class PasswordEntry(ctk.CTkFrame):
    def __init__(self, master, label: str = "Password", width: int = 0, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        if label:
            ctk.CTkLabel(
                self, text=label, font=Fonts.SMALL_BOLD,
                text_color=C.text_secondary, anchor="w",
            ).pack(fill="x", pady=(0, 4))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x")
        row.grid_columnconfigure(0, weight=1)

        entry_width = width - 44 if width > 44 else 0
        self.entry = ctk.CTkEntry(
            row, placeholder_text="Enter password", font=Fonts.BODY,
            fg_color=C.bg_input, border_color=C.border,
            text_color=C.text_primary, placeholder_text_color=C.text_dim,
            corner_radius=Dim.RADIUS, height=36, width=entry_width, show="\u2022",
        )
        self.entry.grid(row=0, column=0, sticky="ew")

        self._showing = False
        self._toggle = ctk.CTkButton(
            row, text="\u25C9", font=(Fonts.F, 14), width=36, height=36,
            fg_color=C.bg_input, hover_color=C.bg_sidebar_hover,
            text_color=C.text_secondary, corner_radius=Dim.RADIUS_SM,
            command=self._do_toggle,
        )
        self._toggle.grid(row=0, column=1, padx=(4, 0))

    def _do_toggle(self):
        self._showing = not self._showing
        self.entry.configure(show="" if self._showing else "\u2022")
        self._toggle.configure(text="\u25CB" if self._showing else "\u25C9")

    def get_value(self) -> str:
        return self.entry.get().strip()

    def clear(self):
        self.entry.delete(0, "end")

    def focus(self):
        self.entry.focus_set()

    def apply_theme(self):
        self.entry.configure(fg_color=C.bg_input, border_color=C.border,
                             text_color=C.text_primary)
        self._toggle.configure(fg_color=C.bg_input, hover_color=C.bg_sidebar_hover)


class StyledComboBox(ctk.CTkFrame):
    def __init__(self, master, label: str = "", values: list[str] = None,
                 width: int = 0, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        if not values:
            values = []
        if label:
            ctk.CTkLabel(
                self, text=label, font=Fonts.SMALL_BOLD,
                text_color=C.text_secondary, anchor="w",
            ).pack(fill="x", pady=(0, 4))
        self.combo = ctk.CTkComboBox(
            self, values=values, font=Fonts.BODY,
            fg_color=C.bg_input, border_color=C.border,
            button_color=C.primary, button_hover_color=C.primary_hover,
            dropdown_fg_color=C.bg_card, dropdown_hover_color=C.bg_card_hover,
            text_color=C.text_primary, corner_radius=Dim.RADIUS,
            height=36, width=width if width > 0 else 0, state="readonly",
        )
        self.combo.pack(fill="x")
        if values:
            self.combo.set(values[0])

    def get_value(self) -> str:
        return self.combo.get()

    def set_value(self, v: str):
        self.combo.set(v)


class StyledButton(ctk.CTkButton):

    @staticmethod
    def _get_variants() -> dict[str, tuple[str, str, str]]:
        c = ThemeManager().C
        return {
            "primary": (c.primary, c.primary_hover, c.text_on_primary),
            "success": (c.success, c.success_hover, c.text_on_primary),
            "danger": (c.danger, c.danger_hover, c.text_on_primary),
            "warning": (c.warning, c.warning_hover, c.text_on_primary),
            "outline": ("transparent", c.bg_sidebar_hover, c.primary),
        }

    def __init__(self, master, text: str = "Button", variant: str = "primary",
                 command: Callable | None = None, width: int = 130,
                 height: int = 36, icon: str = "", **kw):
        colors = self._get_variants().get(variant, self._get_variants()["primary"])
        fg, hover, tc = colors
        bd = 1 if variant == "outline" else 0

        # Let caller kwargs override variant defaults
        fg = kw.pop("fg_color", fg)
        hover = kw.pop("hover_color", hover)
        tc = kw.pop("text_color", tc)

        display_text = f"{icon}  {text}" if icon else text

        super().__init__(
            master, text=display_text, font=Fonts.BODY_BOLD,
            fg_color=fg, hover_color=hover, text_color=tc,
            corner_radius=Dim.RADIUS_SM, height=height, width=width,
            border_width=bd, border_color=C.primary,
            command=command, **kw,
        )


class StyledText(ctk.CTkFrame):
    def __init__(self, master, label: str = "", height: int = 100,
                 width: int = 0, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        if label:
            ctk.CTkLabel(
                self, text=label, font=Fonts.SMALL_BOLD,
                text_color=C.text_secondary, anchor="w",
            ).pack(fill="x", pady=(0, 4))
        self.textbox = ctk.CTkTextbox(
            self, font=Fonts.BODY, fg_color=C.bg_input,
            text_color=C.text_primary, corner_radius=Dim.RADIUS,
            height=height, width=width if width > 0 else 0,
            border_color=C.border, border_width=1,
        )
        self.textbox.pack(fill="x")

    def get_value(self) -> str:
        return self.textbox.get("1.0", "end-1c").strip()

    def set_value(self, v: str):
        self.textbox.delete("1.0", "end")
        self.textbox.insert("1.0", v)

    def clear(self):
        self.textbox.delete("1.0", "end")
