"""Shared documents page showing files shared with/by the user."""

from __future__ import annotations
import customtkinter as ctk
from gui.theme import ThemeManager, Dim, Fonts
from gui.components.tables import StyledTable
from gui.components.forms import StyledButton, StyledComboBox
from gui.components.dialogs import Toast

tm = ThemeManager()
C = tm.C


class SharedPage(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=C.bg_main, **kw)
        self._shared = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_content()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=Dim.PAD_XL, pady=(Dim.PAD_XL, 0))
        header.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            header, text="Shared Documents", font=Fonts.TITLE,
            text_color=C.text_primary,
        ).grid(row=0, column=0, sticky="w")
        self._filter = StyledComboBox(
            header, values=["All", "Shared With Me", "Shared By Me"], width=180,
        )
        self._filter.combo.configure(command=self._apply_filter)
        self._filter.grid(row=0, column=1, sticky="e")

    def _build_content(self):
        self._table = StyledTable(self, columns=[
            ("name", "File Name", 200),
            ("shared_by", "Shared By", 120),
            ("shared_with", "Shared With", 120),
            ("permission", "Permission", 100),
            ("date", "Date Shared", 120),
        ])
        self._table.grid(row=1, column=0, sticky="nsew",
                         padx=Dim.PAD_XL, pady=Dim.PAD_MD)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew",
                       padx=Dim.PAD_XL, pady=(0, Dim.PAD_XL))
        StyledButton(
            btn_frame, text="Revoke Access", variant="danger",
            command=self._revoke, width=140,
        ).pack(side="left")

    def load_shared(self, shared: list[dict]):
        self._shared = shared
        self._table.insert_rows(shared)

    def _apply_filter(self, _=None):
        mode = self._filter.get_value()
        if mode == "All":
            self._table.insert_rows(self._shared)
        elif mode == "Shared With Me":
            self._table.insert_rows([s for s in self._shared if s.get("direction") == "to_me"])
        else:
            self._table.insert_rows([s for s in self._shared if s.get("direction") == "by_me"])

    def _revoke(self):
        sel = self._table.get_selected()
        if not sel:
            Toast(self, "Select a share entry to revoke", "warning")
            return
        Toast(self, f"Revoked access for {sel.get('filename', 'file')}", "success")
