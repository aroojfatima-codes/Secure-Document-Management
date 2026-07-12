"""Card widgets — stat cards, info cards, action cards, page headers."""

from __future__ import annotations
from typing import Callable
import customtkinter as ctk
from gui.theme import ThemeManager, Dim, Fonts

tm = ThemeManager()
C = tm.C


class StatCard(ctk.CTkFrame):
    """Dashboard stat card with icon, large value, and subtitle."""

    def __init__(self, master, title: str, value: str, icon: str = "",
                 accent: str = "", **kw):
        super().__init__(master, fg_color=C.bg_card,
                         corner_radius=Dim.RADIUS_LG, **kw)
        if not accent:
            accent = C.primary
        self._accent = accent

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=Dim.PAD_MD, pady=(Dim.PAD_MD, 0))

        self._icon_circle = ctk.CTkLabel(
            top, text=icon, font=Fonts.ICON_LG, text_color=accent,
            width=38, height=38, corner_radius=19,
            fg_color=C.bg_input,
        )
        self._icon_circle.pack(side="left")

        self._value = ctk.CTkLabel(
            self, text=value, font=Fonts.TITLE_LG,
            text_color=C.text_primary, anchor="w",
        )
        self._value.pack(fill="x", padx=Dim.PAD_MD, pady=(8, 0))

        self._title = ctk.CTkLabel(
            self, text=title, font=Fonts.SMALL,
            text_color=C.text_secondary, anchor="w",
        )
        self._title.pack(fill="x", padx=Dim.PAD_MD, pady=(0, Dim.PAD_MD))

    def update_value(self, v: str):
        self._value.configure(text=v)

    def apply_theme(self):
        self.configure(fg_color=C.bg_card)
        self._icon_circle.configure(fg_color=C.bg_input, text_color=self._accent)
        self._value.configure(text_color=C.text_primary)
        self._title.configure(text_color=C.text_secondary)


class InfoCard(ctk.CTkFrame):
    """Card with a title header and scrollable content area."""

    def __init__(self, master, title: str = "", **kw):
        super().__init__(master, fg_color=C.bg_card,
                         corner_radius=Dim.RADIUS_LG, **kw)
        if title:
            hdr = ctk.CTkFrame(self, fg_color="transparent")
            hdr.pack(fill="x", padx=Dim.PAD_MD, pady=(Dim.PAD_MD, Dim.PAD_SM))
            ctk.CTkLabel(
                hdr, text=title, font=Fonts.SUBTITLE,
                text_color=C.text_primary, anchor="w",
            ).pack(side="left")

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True,
                          padx=Dim.PAD_MD, pady=(0, Dim.PAD_MD))

    def add_row(self, label: str, value: str):
        row = ctk.CTkFrame(self.content, fg_color="transparent", height=28)
        row.pack(fill="x", pady=1)
        row.pack_propagate(False)
        ctk.CTkLabel(
            row, text=label, font=Fonts.SMALL,
            text_color=C.text_secondary, width=130, anchor="w",
        ).pack(side="left", padx=(0, 8))
        ctk.CTkLabel(
            row, text=str(value), font=Fonts.BODY,
            text_color=C.text_primary, anchor="w",
        ).pack(side="left", fill="x", expand=True)

    def apply_theme(self):
        self.configure(fg_color=C.bg_card)


class ActionCard(ctk.CTkFrame):
    """Clickable action card for dashboard quick actions."""

    def __init__(self, master, title: str, icon: str, description: str = "",
                 accent: str = "", command: Callable | None = None, **kw):
        super().__init__(master, fg_color=C.bg_card,
                         corner_radius=Dim.RADIUS_LG, height=90,
                         cursor="hand2", **kw)
        self.pack_propagate(False)
        self._cmd = command
        if not accent:
            accent = C.primary

        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", fill="y", padx=(Dim.PAD_MD, 0), pady=Dim.PAD_MD)

        ctk.CTkLabel(
            left, text=icon, font=Fonts.ICON_LG,
            text_color=accent, width=36, height=36,
            corner_radius=18, fg_color=C.bg_input,
        ).pack()

        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="left", fill="y", padx=(Dim.PAD_SM, Dim.PAD_MD),
                   pady=Dim.PAD_MD, expand=True)

        ctk.CTkLabel(
            right, text=title, font=Fonts.BODY_BOLD,
            text_color=C.text_primary, anchor="w",
        ).pack(anchor="w")
        if description:
            ctk.CTkLabel(
                right, text=description, font=Fonts.TINY,
                text_color=C.text_dim, anchor="w",
            ).pack(anchor="w")

        for w in (self, left, right):
            w.bind("<Button-1>", lambda e: self._cmd and self._cmd())
            w.bind("<Enter>", self._enter)
            w.bind("<Leave>", self._leave)

    def _enter(self, _=None):
        self.configure(fg_color=C.bg_card_hover)

    def _leave(self, _=None):
        self.configure(fg_color=C.bg_card)

    def apply_theme(self):
        self.configure(fg_color=C.bg_card)


class PageHeader(ctk.CTkFrame):
    """Page title with optional subtitle and action buttons."""

    def __init__(self, master, title: str, subtitle: str = "",
                 actions: list[tuple[str, Callable]] | None = None, **kw):
        super().__init__(master, fg_color="transparent", height=52, **kw)
        self.pack_propagate(False)

        left = ctk.CTkFrame(self, fg_color="transparent")
        left.pack(side="left", fill="y")

        self._title = ctk.CTkLabel(
            left, text=title, font=Fonts.TITLE_SM,
            text_color=C.text_primary,
        )
        self._title.pack(side="left", padx=(0, 12))

        if subtitle:
            self._sub = ctk.CTkLabel(
                left, text=subtitle, font=Fonts.SMALL,
                text_color=C.text_secondary,
            )
            self._sub.pack(side="left")

        if actions:
            right = ctk.CTkFrame(self, fg_color="transparent")
            right.pack(side="right", fill="y")
            for label, cmd in actions:
                ctk.CTkButton(
                    right, text=label, font=Fonts.SMALL_BOLD,
                    fg_color=C.primary, hover_color=C.primary_hover,
                    text_color=C.text_on_primary,
                    corner_radius=Dim.RADIUS_SM, height=32,
                    command=cmd,
                ).pack(side="right", padx=(6, 0))

    def apply_theme(self):
        self._title.configure(text_color=C.text_primary)
