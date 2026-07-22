"""Modern animated sidebar with expand/collapse, hover effects, and active glow."""

from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from gui.theme import Dim, Fonts, ThemeManager

tm = ThemeManager()
C = tm.C


class SidebarItem(ctk.CTkFrame):
    """Single sidebar navigation item with icon, label, and hover/active states."""

    def __init__(self, master, icon_text: str, label: str,
                 command: Callable | None = None, height: int = 40, **kw):
        kw.pop("height", None)
        kw.pop("fg_color", None)
        kw.pop("corner_radius", None)
        super().__init__(master, fg_color="transparent", corner_radius=Dim.RADIUS,
                         height=height, cursor="hand2", **kw)
        self.pack_propagate(False)
        self._cmd = command
        self._label_text = label
        self._active = False
        self._expanded = True
        self._danger = False

        self._icon = ctk.CTkLabel(
            self, text=icon_text, font=Fonts.ICON,
            text_color=C.sidebar_text, width=28, anchor="w",
        )
        self._icon.pack(side="left", padx=(14, 6))

        self._text = ctk.CTkLabel(
            self, text=label, font=Fonts.BODY,
            text_color=C.sidebar_text, anchor="w",
        )
        self._text.pack(side="left", fill="x", expand=True, padx=(0, 12))

        for w in (self, self._icon, self._text):
            w.bind("<Button-1>", self._click)
            w.bind("<Enter>", self._enter)
            w.bind("<Leave>", self._leave)

    def _click(self, _=None):
        if self._cmd:
            try:
                self._cmd()
            except Exception:
                pass

    def _enter(self, _=None):
        if not self._active:
            if self._danger:
                self.configure(fg_color=C.danger_subtle)
                self._icon.configure(text_color=C.danger)
                self._text.configure(text_color=C.danger)
            else:
                self.configure(fg_color=C.bg_sidebar_hover)
                self._icon.configure(text_color=C.text_primary)
                self._text.configure(text_color=C.text_primary)

    def _leave(self, _=None):
        if not self._active:
            if self._danger:
                self.configure(fg_color="transparent")
                self._icon.configure(text_color=C.danger)
                self._text.configure(text_color=C.danger)
            else:
                self.configure(fg_color="transparent")
                self._icon.configure(text_color=C.sidebar_text)
                self._text.configure(text_color=C.sidebar_text)

    def set_active(self, active: bool):
        self._active = active
        if active:
            self.configure(fg_color=C.sidebar_active)
            self._icon.configure(text_color=C.sidebar_active_text)
            self._text.configure(text_color=C.sidebar_active_text)
        else:
            self.configure(fg_color="transparent")
            if self._danger:
                self._icon.configure(text_color=C.danger)
                self._text.configure(text_color=C.danger)
            else:
                self._icon.configure(text_color=C.sidebar_text)
                self._text.configure(text_color=C.sidebar_text)

    def set_expanded(self, expanded: bool):
        self._expanded = expanded
        if expanded:
            self._text.pack(side="left", fill="x", expand=True, padx=(0, 12))
        else:
            self._text.pack_forget()

    def set_danger_style(self):
        self._danger = True
        self._icon.configure(text_color=C.danger)
        self._text.configure(text_color=C.danger)


class Sidebar(ctk.CTkFrame):
    """Animated expandable sidebar with branding and navigation."""

    def __init__(self, master, width: int = 0, on_navigate: Callable = None,
                 on_toggle: Callable = None, on_logout: Callable = None,
                 on_login: Callable = None, on_register: Callable = None, **kw):
        if not width:
            width = Dim.SIDEBAR_W
        kw.pop("width", None)
        kw.pop("fg_color", None)
        kw.pop("corner_radius", None)
        super().__init__(master, width=width, fg_color=C.bg_sidebar,
                         corner_radius=0, **kw)
        self.pack_propagate(False)
        self._on_navigate = on_navigate
        self._on_toggle = on_toggle
        self._on_logout = on_logout
        self._on_login = on_login
        self._on_register = on_register
        self._items: list[SidebarItem] = []
        self._nav_labels: list[ctk.CTkLabel] = []
        self._active_idx = -1
        self._expanded = True
        self._target_w = width
        self._animating = False

        self._build_brand()
        self._sep = ctk.CTkFrame(self, height=1, fg_color=C.border)
        self._sep.pack(fill="x", padx=14, pady=(2, 6))

        self._nav = ctk.CTkFrame(self, fg_color="transparent")
        self._nav.pack(fill="both", expand=True)

        self._bottom = ctk.CTkFrame(self, fg_color="transparent")
        self._bottom.pack(fill="x", side="bottom", pady=(0, 12))

    def _build_brand(self):
        hdr = ctk.CTkFrame(self, fg_color="transparent", height=52)
        hdr.pack(fill="x", pady=(14, 4))
        hdr.pack_propagate(False)

        self._brand_icon = ctk.CTkLabel(
            hdr, text="\u25C8", font=(Fonts.F, 22, "bold"),
            text_color=C.primary, width=30,
        )
        self._brand_icon.pack(side="left", padx=(16, 8))

        self._brand_text_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        self._brand_text_frame.pack(side="left", fill="y")

        self._brand_title = ctk.CTkLabel(
            self._brand_text_frame, text="SDMS", font=Fonts.SUBTITLE,
            text_color=C.text_primary, anchor="w",
        )
        self._brand_title.pack(anchor="w")

        self._brand_sub = ctk.CTkLabel(
            self._brand_text_frame, text="Secure Documents", font=Fonts.TINY,
            text_color=C.text_dim, anchor="w",
        )
        self._brand_sub.pack(anchor="w")

    def add_item(self, icon: str, label: str,
                 command: Callable | None = None) -> None:
        item = SidebarItem(self._nav, icon_text=icon, label=label, command=command)
        item.pack(fill="x", padx=8, pady=1)
        self._items.append(item)

    def add_separator(self):
        ctk.CTkFrame(self._nav, height=1, fg_color=C.border).pack(
            fill="x", padx=14, pady=8)

    def add_label(self, text: str):
        lbl = ctk.CTkLabel(
            self._nav, text=text.upper(), font=Fonts.TINY_BOLD,
            text_color=C.text_dim, anchor="w",
        )
        lbl.pack(fill="x", padx=22, pady=(10, 3))
        self._nav_labels.append(lbl)

    def clear(self):
        for item in self._items:
            try:
                item.destroy()
            except Exception:
                pass
        self._items.clear()
        self._active_idx = -1
        for w in self._nav.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass
        for w in self._bottom.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

    def set_active(self, idx: int):
        if 0 <= self._active_idx < len(self._items):
            self._items[self._active_idx].set_active(False)
        self._active_idx = idx
        if 0 <= idx < len(self._items):
            self._items[idx].set_active(True)

    def animate_width(self, target: int):
        self._target_w = target
        self._expanded = (target > Dim.SIDEBAR_COLLAPSED_W)
        if not self._animating:
            self._animating = True
            self._animate_width_step()

    def _animate_width_step(self):
        try:
            current = self.winfo_width()
            target = self._target_w
            if current < 1:
                current = Dim.SIDEBAR_W
            if abs(current - target) < 4:
                self.configure(width=target)
                self._expanded = (target > Dim.SIDEBAR_COLLAPSED_W)
                for item in self._items:
                    item.set_expanded(self._expanded)
                if self._expanded:
                    try:
                        self._brand_text_frame.pack(side="left", fill="y")
                    except Exception:
                        pass
                    try:
                        self._brand_icon.pack(side="left", padx=(16, 8))
                    except Exception:
                        pass
                else:
                    try:
                        self._brand_text_frame.pack_forget()
                    except Exception:
                        pass
                    try:
                        self._brand_icon.pack(side="left", padx=(10, 4))
                    except Exception:
                        pass
                self._animating = False
                return
            diff = target - current
            step = max(1, int(diff * 0.25))
            new_w = current + step if diff > 0 else current - step
            self.configure(width=new_w)
            self.after(16, self._animate_width_step)
        except Exception:
            self._animating = False
            try:
                self.configure(width=self._target_w)
            except Exception:
                pass

    def build_auth_menu(self, user: dict):
        self.clear()
        self._nav_labels = []
        nav = self._on_navigate
        role = user.get("role", "").lower()

        self.add_label("Overview")
        self.add_item("\u2302", "Dashboard", lambda: nav("dashboard") if nav else None)

        if role in ("admin", "editor"):
            self.add_item("\u2B06", "Upload", lambda: nav("upload") if nav else None)

        self.add_item("\u25A3", "Documents", lambda: nav("documents") if nav else None)
        self.add_item("\u26B2", "Search", lambda: nav("search") if nav else None)

        if role in ("admin", "editor"):
            self.add_item("\uD83D\uDD17", "Share Documents", lambda: nav("share") if nav else None)

        self.add_item("\u267B", "Shared Documents", lambda: nav("shared") if nav else None)

        if role == "admin":
            self.add_separator()
            self.add_label("Administration")
            self.add_item("\u2611", "Audit Logs", lambda: nav("audit") if nav else None)

        self.add_separator()
        self.add_label("Account")
        self.add_item("\uD83D\uDCF7", "Face Recognition", lambda: nav("face") if nav else None)

        if role == "admin":
            self.add_item("\u2699", "Settings", lambda: nav("settings") if nav else None)

        self.add_item("\uD83D\uDC64", "Profile", lambda: nav("profile") if nav else None)

        logout_item = SidebarItem(
            self._bottom, icon_text="\u2192", label="Logout",
            command=self._on_logout if self._on_logout else None,
        )
        logout_item.set_danger_style()
        logout_item.pack(fill="x", padx=8, pady=1)

    def build_unauth_menu(self):
        self.clear()
        self._nav_labels = []
        self.add_label("Access")
        self.add_item("\u25B6", "Login", lambda: self._on_login() if self._on_login else None)
        self.add_item("\u2795", "Register", lambda: self._on_register() if self._on_register else None)
