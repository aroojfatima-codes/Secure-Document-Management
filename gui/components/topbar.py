"""Top navigation bar with search, theme toggle, user info, and breadcrumbs."""

from __future__ import annotations
from typing import Callable
import customtkinter as ctk
from gui.theme import ThemeManager, Dim, Fonts

tm = ThemeManager()
C = tm.C


class TopBar(ctk.CTkFrame):
    """Horizontal top bar spanning the content area."""

    def __init__(self, master, **kw):
        super().__init__(master, height=Dim.TOPBAR_H, fg_color=C.bg_topbar,
                         corner_radius=0, **kw)
        self.pack_propagate(False)

        self._left = ctk.CTkFrame(self, fg_color="transparent")
        self._left.pack(side="left", fill="y", padx=(Dim.PAD_LG, 0))

        self._toggle_btn = ctk.CTkButton(
            self._left, text="\u2630", font=Fonts.ICON, width=32, height=32,
            fg_color="transparent", hover_color=C.bg_sidebar_hover,
            text_color=C.text_secondary, command=self._on_toggle,
        )
        self._toggle_btn.pack(side="left", padx=(0, 8))

        self._breadcrumb = ctk.CTkLabel(
            self._left, text="", font=Fonts.BODY_BOLD,
            text_color=C.text_primary, anchor="w",
        )
        self._breadcrumb.pack(side="left", padx=(4, 0))

        self._right = ctk.CTkFrame(self, fg_color="transparent")
        self._right.pack(side="right", fill="y", padx=(0, Dim.PAD_LG))

        self._search_var = ctk.StringVar()
        self._search_entry = ctk.CTkEntry(
            self._right, textvariable=self._search_var,
            placeholder_text="Quick search...",
            font=Fonts.BODY, fg_color=C.bg_input, border_color=C.border,
            text_color=C.text_primary, corner_radius=Dim.RADIUS,
            width=200, height=30,
        )
        self._search_entry.pack(side="left", padx=(0, 12), pady=9)

        self._theme_btn = ctk.CTkButton(
            self._right, text="\u263E", font=Fonts.ICON, width=32, height=32,
            fg_color="transparent", hover_color=C.bg_sidebar_hover,
            text_color=C.text_secondary, command=self._toggle_theme,
        )
        self._theme_btn.pack(side="left", padx=(0, 8))

        self._user_frame = ctk.CTkFrame(self._right, fg_color="transparent")
        self._user_frame.pack(side="left")

        self._avatar = ctk.CTkLabel(
            self._user_frame, text="\u263A", font=Fonts.ICON,
            text_color=C.text_on_primary, width=30, height=30,
            corner_radius=15, fg_color=C.primary,
        )
        self._avatar.pack(side="left", padx=(0, 6))

        self._user_label = ctk.CTkLabel(
            self._user_frame, text="User", font=Fonts.SMALL_BOLD,
            text_color=C.text_primary,
        )
        self._user_label.pack(side="left")

        self._on_toggle_cb: Callable | None = None
        self._on_theme_change_cb: Callable | None = None

    def set_breadcrumb(self, text: str):
        self._breadcrumb.configure(text=text)

    def set_user(self, username: str, role: str = ""):
        display = f"{username}"
        if role:
            display = f"{username}  ({role})"
        self._user_label.configure(text=display)

    def set_toggle_callback(self, cb: Callable):
        self._on_toggle_cb = cb

    def set_theme_change_callback(self, cb: Callable):
        self._on_theme_change_cb = cb

    def _on_toggle(self):
        if self._on_toggle_cb:
            self._on_toggle_cb()

    def _toggle_theme(self):
        new_mode = tm.toggle()
        self._theme_btn.configure(text="\u2600" if new_mode == "dark" else "\u263E")
        if self._on_theme_change_cb:
            self._on_theme_change_cb(new_mode)

    def apply_theme(self):
        self.configure(fg_color=C.bg_topbar)
        self._breadcrumb.configure(text_color=C.text_primary)
        self._search_entry.configure(
            fg_color=C.bg_input, border_color=C.border, text_color=C.text_primary)
        self._theme_btn.configure(
            fg_color="transparent", hover_color=C.bg_sidebar_hover,
            text_color=C.text_secondary)
        self._avatar.configure(fg_color=C.primary)
        self._user_label.configure(text_color=C.text_primary)
