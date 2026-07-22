"""Audit log page with filtering and export."""

from __future__ import annotations
import csv
import os
import customtkinter as ctk
from tkinter import filedialog
from gui.theme import ThemeManager, Dim, Fonts
from gui.components.tables import StyledTable
from gui.components.forms import StyledComboBox, StyledButton, StyledEntry
from gui.components.dialogs import Toast
from gui.smooth_scrolling import bind_smooth_scroll

tm = ThemeManager()
C = tm.C


class AuditPage(ctk.CTkFrame):
    def __init__(self, master, **kw):
        kw.pop("fg_color", None)
        super().__init__(master, fg_color=C.bg_main, **kw)
        self._logs = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_content()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=Dim.PAD_XL, pady=(Dim.PAD_XL, 0))
        header.grid_columnconfigure(2, weight=1)
        ctk.CTkLabel(
            header, text="Audit Logs", font=Fonts.TITLE,
            text_color=C.text_primary,
        ).grid(row=0, column=0, sticky="w")

        filters = ctk.CTkFrame(header, fg_color="transparent")
        filters.grid(row=0, column=1, sticky="e", padx=(Dim.PAD_MD, 0))

        self._action_filter = StyledComboBox(
            filters, values=["All", "UPLOAD", "DOWNLOAD", "DELETE", "SHARE", "LOGIN", "FACE_LOGIN"],
            width=140,
        )
        self._action_filter.pack(side="left", padx=(0, Dim.PAD_SM))

        self._user_filter = StyledEntry(
            filters, placeholder="Filter by user...", width=140,
        )
        self._user_filter.pack(side="left", padx=(0, Dim.PAD_SM))

        self._search = StyledEntry(
            filters, placeholder="Search logs...", width=160,
        )
        self._search.pack(side="left", padx=(0, Dim.PAD_SM))
        self._search.entry.bind("<KeyRelease>", lambda e: self._apply_filter())

        StyledButton(
            header, text="Apply", variant="outline", width=70,
            command=self._apply_filter,
        ).grid(row=0, column=3, padx=(Dim.PAD_SM, 0))

        StyledButton(
            header, text="Export CSV", variant="outline", width=110,
            command=self._export,
        ).grid(row=0, column=4, padx=(Dim.PAD_SM, 0))



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
            filtered = [e for e in filtered if e.get("action", "").lower() == action.lower()]
        if user != "All Users":
            filtered = [e for e in filtered if e.get("user", "") == user]
        if search:
            filtered = [e for e in filtered if search in e.get("document_id", "").lower() or search in e.get("details", "").lower() or search in e.get("user", "").lower()]
        self._table.insert_rows(filtered)

    def _export(self):
        try:
            if not self._logs:
                Toast(self, "No logs to export", "warning")
                return
            path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                initialfile="audit_logs.csv",
            )
            if not path:
                return
            with open(path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "document_id", "action", "user", "timestamp",
                    "status", "details", "ip"
                ])
                writer.writeheader()
                for log in self._logs:
                    writer.writerow({k: log.get(k, "") for k in [
                        "document_id", "action", "user", "timestamp",
                        "status", "details", "ip"
                    ]})
            Toast(self, f"Audit log exported to {os.path.basename(path)}", "success")
        except Exception as e:
            Toast(self, f"Export failed: {e}", "error")

    def apply_theme(self):
        self.configure(fg_color=C.bg_main)
