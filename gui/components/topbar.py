"""Top navigation bar with search, theme toggle, user info, logout, and breadcrumbs."""

from __future__ import annotations
from typing import Callable
import customtkinter as ctk
from gui.theme import ThemeManager, Dim, Fonts

tm = ThemeManager()
C = tm.C


class TopBar(ctk.CTkFrame):
    """Horizontal top bar spanning the content area."""

    def __init__(self, master, height: int = Dim.TOPBAR_H, **kw):
        kw.pop("height", None)
        kw.pop("fg_color", None)
        kw.pop("corner_radius", None)
        super().__init__(master, height=height, fg_color=C.bg_topbar,
                         corner_radius=0, **kw)
        self.pack_propagate(False)

        self._left = ctk.CTkFrame(self, fg_color="transparent")
        self._left.pack(side="left", fill="y", padx=(Dim.PAD_LG, 0))

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
            text_color=C.text_primary, placeholder_text_color=C.text_dim,
            corner_radius=Dim.RADIUS,
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

        self._logout_btn = ctk.CTkButton(
            self._right, text="\u2192  Logout", font=Fonts.SMALL_BOLD,
            fg_color="transparent", hover_color=C.danger_subtle,
            text_color=C.danger, corner_radius=Dim.RADIUS_SM,
            height=30, width=90, command=self._on_logout_click,
        )

        self._on_theme_change_cb: Callable | None = None
        self._on_logout_cb: Callable | None = None
        self._on_search_cb: Callable | None = None
        self._logged_in = False

    def set_breadcrumb(self, text: str):
        self._breadcrumb.configure(text=text)

    def set_user(self, username: str, role: str = ""):
        display = f"{username}"
        if role:
            display = f"{username}  ({role})"
        self._user_label.configure(text=display)

    def set_theme_change_callback(self, cb: Callable):
        self._on_theme_change_cb = cb

    def set_logout_callback(self, cb: Callable):
        self._on_logout_cb = cb

    def set_search_callback(self, cb: Callable):
        self._on_search_cb = cb
        self._search_entry.bind("<Return>", lambda e: self._on_search_submit())

    def _on_search_submit(self):
        query = self._search_var.get().strip()
        if self._on_search_cb and query:
            self._on_search_cb(query)

    def set_logged_in(self, logged_in: bool):
        self._logged_in = logged_in
        if logged_in:
            self._logout_btn.pack(side="left", padx=(12, 0))
        else:
            self._logout_btn.pack_forget()
            self._user_label.configure(text="User")
            self._search_var.set("")

    def _toggle_theme(self):
        try:
            new_mode = tm.toggle()
            self._theme_btn.configure(text="\u2600" if new_mode == "dark" else "\u263E")
            if self._on_theme_change_cb:
                self._on_theme_change_cb(new_mode)
        except Exception:
            pass

    def _on_logout_click(self):
        if self._on_logout_cb:
            try:
                self._on_logout_cb()
            except Exception:
                pass

    def apply_theme(self):
        self.configure(fg_color=C.bg_topbar)
        self._breadcrumb.configure(text_color=C.text_primary)
        self._search_entry.configure(
            fg_color=C.bg_input, border_color=C.border, text_color=C.text_primary,
            placeholder_text_color=C.text_dim)
        self._theme_btn.configure(
            fg_color="transparent", hover_color=C.bg_sidebar_hover,
            text_color=C.text_secondary)
        self._avatar.configure(fg_color=C.primary)
        self._user_label.configure(text_color=C.text_primary)
        self._logout_btn.configure(
            fg_color="transparent", hover_color=C.danger_subtle,
            text_color=C.danger)
