"""Search page with instant filter and advanced options."""

from __future__ import annotations
import customtkinter as ctk
from gui.theme import ThemeManager, Dim, Fonts
from gui.components.forms import StyledEntry, StyledComboBox, StyledButton
from gui.components.tables import StyledTable
from gui.components.dialogs import Toast

tm = ThemeManager()
C = tm.C


class SearchPage(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=C.bg_main, **kw)
        self._all_docs = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build_header()
        self._build_filters()
        self._build_results()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=Dim.PAD_XL, pady=(Dim.PAD_XL, 0))
        ctk.CTkLabel(
            header, text="Search Documents", font=Fonts.TITLE,
            text_color=C.text_primary,
        ).pack(anchor="w")

    def _build_filters(self):
        filters = ctk.CTkFrame(self, fg_color=C.bg_card, corner_radius=Dim.RADIUS_LG)
        filters.grid(row=1, column=0, sticky="ew",
                     padx=Dim.PAD_XL, pady=Dim.PAD_MD)
        filters.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            filters, text="\uD83D\uDD0D", font=Fonts.ICON, text_color=C.text_dim,
        ).grid(row=0, column=0, padx=(Dim.PAD_MD, 0), pady=Dim.PAD_MD)

        self._query = StyledEntry(
            filters, placeholder="Type to search instantly...",
            width=400,
        )
        self._query.entry.bind("<KeyRelease>", self._do_search)
        self._query.grid(row=0, column=1, sticky="ew", pady=Dim.PAD_MD)

        self._type_filter = StyledComboBox(
            filters, values=["All Types", "PDF", "Word", "Image", "Text"], width=130,
        )
        self._type_filter.combo.configure(command=lambda _: self._do_search())
        self._type_filter.grid(row=0, column=2, padx=Dim.PAD_SM, pady=Dim.PAD_MD)

        self._owner_filter = StyledComboBox(
            filters, values=["All Owners", "Me", "Others"], width=130,
        )
        self._owner_filter.combo.configure(command=lambda _: self._do_search())
        self._owner_filter.grid(row=0, column=3, padx=(0, Dim.PAD_MD), pady=Dim.PAD_MD)

        StyledButton(
            filters, text="Search", icon="\uD83D\uDD0D", width=90,
            command=self._do_search,
        ).grid(row=0, column=4, padx=(0, Dim.PAD_MD), pady=Dim.PAD_MD)

    def _build_results(self):
        self._results_label = ctk.CTkLabel(
            self, text="Start typing to search...", font=Fonts.BODY,
            text_color=C.text_secondary, anchor="w",
        )
        self._results_label.grid(row=2, column=0, sticky="w",
                                 padx=Dim.PAD_XL, pady=(Dim.PAD_SM, 0))

        self._table = StyledTable(self, columns=[
            ("name", "File Name", 240),
            ("type", "Type", 80),
            ("owner", "Owner", 120),
            ("size", "Size", 90),
            ("modified", "Modified", 130),
        ])
        self._table.grid(row=3, column=0, sticky="nsew",
                         padx=Dim.PAD_XL, pady=Dim.PAD_MD)

    def load_documents(self, docs: list[dict]):
        self._all_docs = docs

    def _do_search(self, _=None):
        q = self._query.get_value().lower()
        if not q:
            self._table.clear()
            self._results_label.configure(text="Start typing to search...")
            return
        results = [d for d in self._all_docs if q in d.get("filename", "").lower()]
        self._table.insert_rows(results)
        self._results_label.configure(text=f"{len(results)} result(s) found")
