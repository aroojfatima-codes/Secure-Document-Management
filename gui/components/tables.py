"""Styled Treeview table with sorting, selection, and scrollbar."""

from __future__ import annotations
from typing import Any
import customtkinter as ctk
from tkinter import ttk
from gui.theme import ThemeManager, Dim, Fonts

tm = ThemeManager()
C = tm.C


class StyledTable(ctk.CTkFrame):
    def __init__(self, master, columns: list[tuple[str, str, int]], **kw):
        kw.pop("fg_color", None)
        kw.pop("corner_radius", None)
        super().__init__(master, fg_color=C.bg_card,
                         corner_radius=Dim.RADIUS_LG, **kw)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("SDMS.Treeview",
                        background=C.bg_card, foreground=C.text_primary,
                        fieldbackground=C.bg_card, borderwidth=0,
                        font=Fonts.BODY, rowheight=34)
        style.configure("SDMS.Treeview.Heading",
                        background=C.bg_input, foreground=C.text_secondary,
                        font=Fonts.SMALL_BOLD, borderwidth=0, relief="flat")
        style.map("SDMS.Treeview",
                  background=[("selected", C.primary_dark)],
                  foreground=[("selected", C.text_on_primary)])
        style.layout("SDMS.Treeview", [("treearea", {"sticky": "nsew"})])

        tree_frame = ctk.CTkFrame(self, fg_color="transparent")
        tree_frame.pack(fill="both", expand=True, padx=3, pady=3)

        self._col_ids = [c[0] for c in columns]
        self.tree = ttk.Treeview(
            tree_frame, columns=self._col_ids, show="headings",
            style="SDMS.Treeview", selectmode="browse",
        )

        self._sort_reverse: dict[str, bool] = {}
        for col_id, heading, width in columns:
            self.tree.heading(
                col_id, text=heading, anchor="w",
                command=lambda c=col_id: self._sort_column(c),
            )
            self.tree.column(col_id, width=width, minwidth=40, anchor="w")

        scrollbar = ctk.CTkScrollbar(
            tree_frame, orientation="vertical", command=self.tree.yview,
            fg_color=C.bg_card, button_color=C.scrollbar,
            button_hover_color=C.scrollbar_hover, width=8,
        )
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self._data: list[dict[str, Any]] = []

    def _sort_column(self, col_id: str):
        reverse = self._sort_reverse.get(col_id, False)
        items = [(self.tree.set(child, col_id), child) for child in self.tree.get_children("")]
        items.sort(key=lambda t: t[0], reverse=reverse)
        for index, (val, child) in enumerate(items):
            self.tree.move(child, "", index)
        self._sort_reverse[col_id] = not reverse

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._data.clear()

    def insert_rows(self, rows: list[dict[str, Any]]):
        self.clear()
        for row_data in rows:
            values = [row_data.get(cid, "") for cid in self._col_ids]
            self.tree.insert("", "end", values=values)
            self._data.append(row_data)

    def get_selected(self) -> dict[str, Any] | None:
        sel = self.tree.selection()
        if not sel:
            return None
        idx = self.tree.index(sel[0])
        if 0 <= idx < len(self._data):
            return self._data[idx]
        return None

    def bind_select(self, callback):
        self.tree.bind("<<TreeviewSelect>>", callback)

    def get_row_count(self) -> int:
        return len(self.tree.get_children())
