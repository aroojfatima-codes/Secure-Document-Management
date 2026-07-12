"""Advanced theme engine supporting dark/light modes.

Centralizes all colours, fonts, dimensions, and theme-switching logic.
Every GUI module imports from here for consistent styling.
"""

from __future__ import annotations

import customtkinter as ctk
from typing import Any


class _ThemeColors:
    """Proxy that always resolves colours from the current theme mode.

    Unlike a snapshot, this object looks up colours at access time so
    module-level ``C = ThemeManager().C`` keeps working after a theme switch.
    """

    _instance: "_ThemeColors | None" = None

    def __new__(cls) -> "_ThemeColors":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __getattr__(self, name: str) -> str:
        tm = ThemeManager()
        palette = _DARK_PALETTE if tm._mode == "dark" else _LIGHT_PALETTE
        try:
            return palette[name]
        except KeyError:
            raise AttributeError(f"Colour '{name}' not found in theme")


_DARK_PALETTE = {
    "bg_root": "#0B1120",
    "bg_main": "#0F172A",
    "bg_sidebar": "#111827",
    "bg_sidebar_hover": "#1E293B",
    "bg_card": "#1E293B",
    "bg_card_hover": "#263548",
    "bg_input": "#1E293B",
    "bg_input_focus": "#263548",
    "bg_topbar": "#111827",
    "bg_modal": "#0F172A",
    "bg_tooltip": "#334155",
    "bg_code": "#1E293B",
    "bg_selected": "#1E3A5F",
    "bg_card_translucent": "#1E293B",

    "accent_blue": "#3B82F6",
    "accent_purple": "#8B5CF6",

    "primary": "#3B82F6",
    "primary_hover": "#2563EB",
    "primary_light": "#60A5FA",
    "primary_dark": "#1D4ED8",
    "primary_subtle": "#1D4ED8",

    "success": "#22C55E",
    "success_hover": "#16A34A",
    "success_subtle": "#052E16",

    "warning": "#F59E0B",
    "warning_hover": "#D97706",
    "warning_subtle": "#451A03",

    "danger": "#EF4444",
    "danger_hover": "#DC2626",
    "danger_subtle": "#450A0A",

    "info": "#06B6D4",
    "info_hover": "#0891B2",

    "text_primary": "#F8FAFC",
    "text_secondary": "#94A3B8",
    "text_dim": "#64748B",
    "text_on_primary": "#FFFFFF",
    "text_link": "#60A5FA",

    "border": "#1E293B",
    "border_light": "#334155",
    "border_focus": "#3B82F6",
    "divider": "#1E293B",

    "scrollbar": "#334155",
    "scrollbar_hover": "#475569",

    "sidebar_active": "#3B82F6",
    "sidebar_active_text": "#FFFFFF",
    "sidebar_text": "#94A3B8",

    "shadow": "#000000",
    "overlay": "#000000",

    "chart_1": "#3B82F6",
    "chart_2": "#22C55E",
    "chart_3": "#F59E0B",
    "chart_4": "#EF4444",
    "chart_5": "#8B5CF6",
    "chart_6": "#EC4899",

    "glass_bg": "#1E293B",
    "glass_border": "#334155",
}

_LIGHT_PALETTE = {
    "bg_root": "#F1F5F9",
    "bg_main": "#F8FAFC",
    "bg_sidebar": "#FFFFFF",
    "bg_sidebar_hover": "#F1F5F9",
    "bg_card": "#FFFFFF",
    "bg_card_hover": "#F8FAFC",
    "bg_input": "#F1F5F9",
    "bg_input_focus": "#FFFFFF",
    "bg_topbar": "#FFFFFF",
    "bg_modal": "#FFFFFF",
    "bg_tooltip": "#1E293B",
    "bg_code": "#F1F5F9",
    "bg_selected": "#EFF6FF",
    "bg_card_translucent": "#FFFFFF",

    "accent_blue": "#3B82F6",
    "accent_purple": "#8B5CF6",

    "primary": "#3B82F6",
    "primary_hover": "#2563EB",
    "primary_light": "#60A5FA",
    "primary_dark": "#1D4ED8",
    "primary_subtle": "#1D4ED8",

    "success": "#22C55E",
    "success_hover": "#16A34A",
    "success_subtle": "#F0FDF4",

    "warning": "#F59E0B",
    "warning_hover": "#D97706",
    "warning_subtle": "#FFFBEB",

    "danger": "#EF4444",
    "danger_hover": "#DC2626",
    "danger_subtle": "#FEF2F2",

    "info": "#06B6D4",
    "info_hover": "#0891B2",

    "text_primary": "#0F172A",
    "text_secondary": "#475569",
    "text_dim": "#94A3B8",
    "text_on_primary": "#FFFFFF",
    "text_link": "#3B82F6",

    "border": "#E2E8F0",
    "border_light": "#CBD5E1",
    "border_focus": "#3B82F6",
    "divider": "#E2E8F0",

    "scrollbar": "#CBD5E1",
    "scrollbar_hover": "#94A3B8",

    "sidebar_active": "#3B82F6",
    "sidebar_active_text": "#FFFFFF",
    "sidebar_text": "#475569",

    "shadow": "#00000020",
    "overlay": "#1E293B",

    "chart_1": "#3B82F6",
    "chart_2": "#22C55E",
    "chart_3": "#F59E0B",
    "chart_4": "#EF4444",
    "chart_5": "#8B5CF6",
    "chart_6": "#EC4899",

    "glass_bg": "#F8FAFC",
    "glass_border": "#E2E8F0",
}


class Fonts:
    """Named font tuples used across all widgets."""
    F = "Segoe UI"
    TITLE_XL = (F, 28, "bold")
    TITLE_LG = (F, 22, "bold")
    TITLE = (F, 20, "bold")
    TITLE_MD = (F, 18, "bold")
    TITLE_SM = (F, 15, "bold")
    SUBTITLE = (F, 13, "bold")
    BODY = (F, 12)
    BODY_BOLD = (F, 12, "bold")
    SMALL = (F, 11)
    SMALL_BOLD = (F, 11, "bold")
    TINY = (F, 10)
    TINY_BOLD = (F, 10, "bold")
    MONO = ("Consolas", 11)
    MONO_SM = ("Consolas", 10)
    ICON = (F, 16)
    ICON_LG = (F, 20)
    ICON_SM = (F, 13)


class Dim:
    """Layout dimension constants."""
    SIDEBAR_W = 220
    SIDEBAR_COLLAPSED_W = 60
    TOPBAR_H = 48
    RADIUS_SM = 6
    RADIUS = 8
    RADIUS_LG = 12
    RADIUS_XL = 16
    PAD_XS = 4
    PAD_SM = 8
    PAD_MD = 12
    PAD_LG = 18
    PAD_XL = 24
    PAD_XXL = 32
    MIN_W = 1080
    MIN_H = 640
    ANIM_FAST = 80
    ANIM_NORMAL = 150
    ANIM_SLOW = 300


class ThemeManager:
    """Singleton that manages the active theme and notifies observers."""

    _instance: "ThemeManager | None" = None

    def __new__(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._mode = "dark"
            cls._instance._observers: list = []
        return cls._instance

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def C(self) -> _ThemeColors:
        """Shorthand for the current colour palette.

        Returns a singleton proxy that always resolves colours for the
        active theme mode, so callers never hold stale colour references.
        """
        return _ThemeColors()

    def toggle(self) -> str:
        self._mode = "light" if self._mode == "dark" else "dark"
        ctk.set_appearance_mode("dark" if self._mode == "dark" else "light")
        for fn in self._observers:
            fn(self._mode)
        return self._mode

    def set_mode(self, mode: str) -> None:
        if mode != self._mode:
            self._mode = mode
            ctk.set_appearance_mode("dark" if mode == "dark" else "light")
            for fn in self._observers:
                fn(self._mode)

    def on_change(self, callback) -> None:
        self._observers.append(callback)

    def get_color(self, name: str) -> str:
        palette = _DARK_PALETTE if self._mode == "dark" else _LIGHT_PALETTE
        return palette.get(name, "#FFFFFF")


def apply_theme(mode: str = "dark") -> None:
    """Initialize CustomTkinter theme."""
    ctk.set_appearance_mode("dark" if mode == "dark" else "light")
    ctk.set_default_color_theme("blue")
    tm = ThemeManager()
    tm.set_mode(mode)
