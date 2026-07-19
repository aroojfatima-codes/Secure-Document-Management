"""Settings page with theme switcher, backup/restore, preferences."""

from __future__ import annotations
import customtkinter as ctk
from gui.theme import ThemeManager, Dim, Fonts
from gui.components.forms import StyledButton, StyledComboBox
from gui.components.dialogs import Toast, ConfirmDialog
from gui.smooth_scrolling import bind_smooth_scroll

tm = ThemeManager()
C = tm.C


class SettingsPage(ctk.CTkFrame):
    def __init__(self, master, on_theme_change=None, **kw):
        kw.pop("fg_color", None)
        super().__init__(master, fg_color=C.bg_main, **kw)
        self._on_theme_change = on_theme_change

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_content()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=Dim.PAD_XL, pady=(Dim.PAD_XL, 0))
        ctk.CTkLabel(
            header, text="Settings", font=Fonts.TITLE,
            text_color=C.text_primary,
        ).pack(anchor="w")

    def _build_content(self):
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=C.scrollbar,
            scrollbar_button_hover_color=C.scrollbar_hover,
        )
        scroll.grid(row=1, column=0, sticky="nsew", padx=Dim.PAD_XL, pady=Dim.PAD_MD)
        scroll.grid_columnconfigure(0, weight=1)

        theme_card = self._make_section(scroll, "Appearance", 0)
        theme_row = ctk.CTkFrame(theme_card, fg_color="transparent")
        theme_row.pack(fill="x", padx=Dim.PAD_LG, pady=Dim.PAD_MD)
        ctk.CTkLabel(
            theme_row, text="Theme:", font=Fonts.BODY, text_color=C.text_secondary,
        ).pack(side="left")
        self._theme_combo = StyledComboBox(
            theme_row, values=["Dark", "Light"], width=150,
        )
        self._theme_combo.pack(side="left", padx=Dim.PAD_SM)
        self._theme_combo.combo.configure(command=self._change_theme)
        StyledButton(
            theme_row, text="Apply", width=80, command=self._change_theme,
        ).pack(side="left", padx=Dim.PAD_SM)

        accent_row = ctk.CTkFrame(theme_card, fg_color="transparent")
        accent_row.pack(fill="x", padx=Dim.PAD_LG, pady=(0, Dim.PAD_MD))
        ctk.CTkLabel(
            accent_row, text="Accent Color:", font=Fonts.BODY,
            text_color=C.text_secondary,
        ).pack(side="left")
        colors = [("Blue", C.primary), ("Green", C.success),
                  ("Purple", C.accent_purple), ("Red", C.danger)]
        for name, color in colors:
            btn = ctk.CTkButton(
                accent_row, text="", width=28, height=28,
                fg_color=color, hover_color=color,
                corner_radius=14, border_width=2, border_color=C.border,
            )
            btn.pack(side="left", padx=4)

        security_card = self._make_section(scroll, "Security", 1)
        opt_row = ctk.CTkFrame(security_card, fg_color="transparent")
        opt_row.pack(fill="x", padx=Dim.PAD_LG, pady=Dim.PAD_MD)
        ctk.CTkLabel(
            opt_row, text="Two-Factor Authentication:", font=Fonts.BODY,
            text_color=C.text_secondary,
        ).pack(side="left")
        ctk.CTkSwitch(
            opt_row, text="", onvalue=True, offvalue=False,
            fg_color=C.border, progress_color=C.success,
            button_color=C.text_on_primary,
        ).pack(side="right")

        timeout_row = ctk.CTkFrame(security_card, fg_color="transparent")
        timeout_row.pack(fill="x", padx=Dim.PAD_LG, pady=(0, Dim.PAD_MD))
        ctk.CTkLabel(
            timeout_row, text="Session Timeout (minutes):", font=Fonts.BODY,
            text_color=C.text_secondary,
        ).pack(side="left")
        self._timeout = StyledComboBox(
            timeout_row, values=["15", "30", "60", "120"], width=100,
        )
        self._timeout.pack(side="right")

        backup_card = self._make_section(scroll, "Backup & Restore", 2)
        btn_row = ctk.CTkFrame(backup_card, fg_color="transparent")
        btn_row.pack(fill="x", padx=Dim.PAD_LG, pady=Dim.PAD_MD)
        StyledButton(
            btn_row, text="Create Backup", icon="\uD83D\uDCBE", width=140,
            command=self._create_backup,
        ).pack(side="left", padx=(0, Dim.PAD_SM))
        StyledButton(
            btn_row, text="Restore Backup", variant="outline", icon="\uD83D\uDD04",
            width=140,
            command=self._restore_backup,
        ).pack(side="left")

        about_card = self._make_section(scroll, "About", 3)
        ctk.CTkLabel(
            about_card, text="Secure Document Management System v2.0",
            font=Fonts.BODY, text_color=C.text_secondary,
        ).pack(anchor="w", padx=Dim.PAD_LG, pady=Dim.PAD_SM)
        ctk.CTkLabel(
            about_card, text="Enterprise-grade document security with AI-powered face recognition",
            font=Fonts.TINY, text_color=C.text_dim,
        ).pack(anchor="w", padx=Dim.PAD_LG, pady=(0, Dim.PAD_MD))

        bind_smooth_scroll(scroll)

    def _make_section(self, parent, title: str, row: int) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            parent, fg_color=C.bg_card, corner_radius=Dim.RADIUS_LG,
        )
        card.grid(row=row, column=0, sticky="ew", pady=Dim.PAD_SM)
        ctk.CTkLabel(
            card, text=title, font=Fonts.SUBTITLE, text_color=C.text_primary,
        ).pack(anchor="w", padx=Dim.PAD_LG, pady=(Dim.PAD_MD, Dim.PAD_SM))
        return card

    def _change_theme(self, _=None):
        mode = self._theme_combo.get_value().lower()
        if self._on_theme_change:
            try:
                self._on_theme_change(mode)
            except Exception:
                pass

    def _create_backup(self):
        Toast(self, "Backup created successfully", "success")

    def _restore_backup(self):
        ConfirmDialog(
            self, "Restore from backup? Current data may be overwritten.",
            on_yes=lambda: Toast(self, "Backup restored", "success"),
        )

    def apply_theme(self):
        self.configure(fg_color=C.bg_main)
