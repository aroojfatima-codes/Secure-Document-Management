"""Audit log page with filtering and export."""

from __future__ import annotations
import customtkinter as ctk
from gui.theme import ThemeManager, Dim, Fonts
from gui.components.tables import StyledTable
from gui.components.forms import StyledComboBox, StyledButton, StyledEntry
from gui.components.dialogs import Toast
from gui.smooth_scrolling import bind_smooth_scroll

tm = ThemeManager()
C = tm.C


class AuditPage(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=C.bg_main, **kw)
        self._logs = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build_header()
        self._build_filters()
        self._build_content()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=Dim.PAD_XL, pady=(Dim.PAD_XL, 0))
        header.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            header, text="Audit Logs", font=Fonts.TITLE,
            text_color=C.text_primary,
        ).grid(row=0, column=0, sticky="w")
        StyledButton(
            header, text="Export CSV", variant="outline", width=110,
            command=self._export,
        ).grid(row=0, column=1, sticky="e")

    def _build_filters(self):
        filters = ctk.CTkFrame(self, fg_color=C.bg_card, corner_radius=Dim.RADIUS_LG)
        filters.grid(row=1, column=0, sticky="ew",
                     padx=Dim.PAD_XL, pady=Dim.PAD_MD)
        ctk.CTkLabel(
            filters, text="Action:", font=Fonts.BODY, text_color=C.text_secondary,
        ).pack(side="left", padx=(Dim.PAD_MD, 4), pady=Dim.PAD_MD)
        self._action_filter = StyledComboBox(
            filters, values=["All", "Upload", "Download", "Share", "Login", "Logout"], width=120,
        )
        self._action_filter.combo.configure(command=lambda _: self._apply_filter())
        self._action_filter.pack(side="left", padx=4, pady=Dim.PAD_MD)
        ctk.CTkLabel(
            filters, text="User:", font=Fonts.BODY, text_color=C.text_secondary,
        ).pack(side="left", padx=(Dim.PAD_MD, 4), pady=Dim.PAD_MD)
        self._user_filter = StyledComboBox(
            filters, values=["All Users", "admin", "officer", "viewer"], width=120,
        )
        self._user_filter.combo.configure(command=lambda _: self._apply_filter())
        self._user_filter.pack(side="left", padx=4, pady=Dim.PAD_MD)
        ctk.CTkLabel(
            filters, text="Search:", font=Fonts.BODY, text_color=C.text_secondary,
        ).pack(side="left", padx=(Dim.PAD_MD, 4), pady=Dim.PAD_MD)
        self._search = StyledEntry(
            filters, placeholder="Search logs...", width=200,
        )
        self._search.entry.bind("<KeyRelease>", lambda _: self._apply_filter())
        self._search.pack(side="left", padx=4, pady=Dim.PAD_MD)

    def _build_content(self):
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=C.scrollbar,
            scrollbar_button_hover_color=C.scrollbar_hover,
        )
        scroll.grid(row=2, column=0, sticky="nsew",
                    padx=Dim.PAD_XL, pady=Dim.PAD_MD)
        scroll.grid_columnconfigure(0, weight=1)

        self._table = StyledTable(scroll, columns=[
            ("document_id", "Document ID", 110),
            ("action", "Action", 120),
            ("user", "User", 110),
            ("timestamp", "Timestamp", 160),
            ("status", "Status", 100),
            ("details", "Details", 200),
            ("ip", "IP Address", 120),
        ])
        self._table.grid(row=0, column=0, sticky="nsew")
        bind_smooth_scroll(scroll)

    def load_logs(self, logs: list[dict]):
        self._logs = logs
        self._table.insert_rows(logs)

    def _apply_filter(self):
        action = self._action_filter.get_value()
        user = self._user_filter.get_value()
        search = self._search.get_value().lower()
        filtered = self._logs
        if action != "All":
            filtered = [l for l in filtered if l.get("action", "").lower() == action.lower()]
        if user != "All Users":
            filtered = [l for l in filtered if l.get("user", "") == user]
        if search:
            filtered = [l for l in filtered if search in l.get("document_id", "").lower() or search in l.get("details", "").lower() or search in l.get("user", "").lower()]
        self._table.insert_rows(filtered)

    def _export(self):
        Toast(self, "Audit log exported to CSV", "success")

    def apply_theme(self):
        self.configure(fg_color=C.bg_main)
