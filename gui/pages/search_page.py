"""Search page with instant filter and advanced options."""

from __future__ import annotations
import customtkinter as ctk
from gui.theme import ThemeManager, Dim, Fonts
from gui.components.forms import StyledEntry, StyledComboBox, StyledButton
from gui.components.tables import StyledTable
from gui.components.dialogs import Toast
from gui.smooth_scrolling import bind_smooth_scroll

tm = ThemeManager()
C = tm.C


class SearchPage(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=C.bg_main, **kw)
        self._all_docs = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)
        self._build_header()
        self._build_instructions()
        self._build_search_options()
        self._build_results()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=Dim.PAD_XL, pady=(Dim.PAD_XL, 0))
        ctk.CTkLabel(
            header, text="Search Documents", font=Fonts.TITLE,
            text_color=C.text_primary,
        ).pack(anchor="w")

    def _build_instructions(self):
        instr_frame = ctk.CTkFrame(
            self, fg_color=C.bg_card, corner_radius=Dim.RADIUS_LG,
        )
        instr_frame.grid(row=1, column=0, sticky="ew",
                         padx=Dim.PAD_XL, pady=Dim.PAD_MD)
        ctk.CTkLabel(
            instr_frame, text="\u2139 How to Search",
            font=Fonts.SUBTITLE, text_color=C.info,
        ).pack(anchor="w", padx=Dim.PAD_LG, pady=(Dim.PAD_MD, Dim.PAD_SM))
        ctk.CTkLabel(
            instr_frame,
            text="Select a search option below, then enter your search term.\n"
                 "You can search by Document ID (e.g. DOC-0001), File Name, or view all documents.",
            font=Fonts.BODY, text_color=C.text_secondary, wraplength=500,
        ).pack(anchor="w", padx=Dim.PAD_LG, pady=(0, Dim.PAD_MD))

    def _build_search_options(self):
        options_frame = ctk.CTkFrame(
            self, fg_color=C.bg_card, corner_radius=Dim.RADIUS_LG,
        )
        options_frame.grid(row=2, column=0, sticky="ew",
                           padx=Dim.PAD_XL, pady=Dim.PAD_MD)
        options_frame.grid_columnconfigure(1, weight=1)

        self._search_mode = ctk.StringVar(value="filename")

        modes = [
            ("Search by Document ID", "doc_id", "Enter Document ID (e.g. DOC-0001)"),
            ("Search by File Name", "filename", "Enter file name to search..."),
            ("Show All Documents", "all", ""),
        ]

        for i, (label, value, placeholder) in enumerate(modes):
            rb = ctk.CTkRadioButton(
                options_frame, text=label, variable=self._search_mode,
                value=value, font=Fonts.BODY, text_color=C.text_primary,
                command=self._on_mode_change,
            )
            rb.grid(row=i, column=0, sticky="w",
                    padx=Dim.PAD_LG, pady=Dim.PAD_SM)

        self._search_input = StyledEntry(
            options_frame, placeholder="Enter file name to search...",
        )
        self._search_input.entry.bind("<KeyRelease>", self._do_search)
        self._search_input.grid(row=0, column=1, sticky="ew",
                                padx=Dim.PAD_SM, pady=Dim.PAD_MD)

        self._search_btn = StyledButton(
            options_frame, text="Search", icon="\uD83D\uDD0D", width=100,
            command=self._do_search,
        )
        self._search_btn.grid(row=0, column=2, padx=Dim.PAD_MD, pady=Dim.PAD_MD)

    def _on_mode_change(self):
        mode = self._search_mode.get()
        if mode == "doc_id":
            self._search_input.configure(placeholder="Enter Document ID (e.g. DOC-0001)")
            self._search_input.grid()
            self._search_btn.grid()
        elif mode == "filename":
            self._search_input.configure(placeholder="Enter file name to search...")
            self._search_input.grid()
            self._search_btn.grid()
        else:
            self._search_input.grid_remove()
            self._search_btn.grid_remove()
            self._show_all()

    def _build_results(self):
        self._results_label = ctk.CTkLabel(
            self, text="Select a search option above to begin...", font=Fonts.BODY,
            text_color=C.text_secondary, anchor="w",
        )
        self._results_label.grid(row=3, column=0, sticky="w",
                                 padx=Dim.PAD_XL, pady=(Dim.PAD_SM, 0))

        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=C.scrollbar,
            scrollbar_button_hover_color=C.scrollbar_hover,
        )
        scroll.grid(row=4, column=0, sticky="nsew",
                    padx=Dim.PAD_XL, pady=Dim.PAD_MD)
        scroll.grid_columnconfigure(0, weight=1)

        self._table = StyledTable(scroll, columns=[
            ("document_id", "Document ID", 110),
            ("original_filename", "File Name", 240),
            ("file_extension", "Type", 80),
            ("owner_id", "Owner", 120),
            ("file_size_display", "Size", 90),
            ("created_at", "Modified", 130),
        ])
        self._table.grid(row=0, column=0, sticky="nsew")
        bind_smooth_scroll(scroll)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=5, column=0, sticky="ew",
                       padx=Dim.PAD_XL, pady=(0, Dim.PAD_XL))
        StyledButton(
            btn_frame, text="Search Again", variant="outline",
            command=self._search_again, width=120,
        ).pack(side="left", padx=(0, Dim.PAD_SM))
        StyledButton(
            btn_frame, text="Clear Search", variant="outline",
            command=self._clear_search, width=120,
        ).pack(side="left", padx=(0, Dim.PAD_SM))
        StyledButton(
            btn_frame, text="Back", variant="outline",
            command=self._go_back, width=100,
        ).pack(side="left", padx=(0, Dim.PAD_SM))
        StyledButton(
            btn_frame, text="Return to Dashboard",
            command=self._go_dashboard, width=160,
        ).pack(side="right")

    def load_documents(self, docs: list[dict]):
        self._all_docs = docs

    def _do_search(self, _=None):
        mode = self._search_mode.get()
        q = self._search_input.get_value().strip()

        if mode == "all":
            self._show_all()
            return

        if not q:
            self._table.clear()
            self._results_label.configure(text="Please enter a search term...")
            return

        if mode == "doc_id":
            results = [d for d in self._all_docs if q.lower() in d.get("document_id", "").lower()]
        else:
            results = [d for d in self._all_docs if q.lower() in d.get("original_filename", "").lower()]

        self._table.insert_rows(results)
        self._results_label.configure(text=f"{len(results)} result(s) found for '{q}'")

    def _show_all(self):
        self._table.insert_rows(self._all_docs)
        self._results_label.configure(text=f"Showing all {len(self._all_docs)} document(s)")

    def _search_again(self):
        self._search_input.clear()
        self._table.clear()
        self._results_label.configure(text="Select a search option above to begin...")

    def _clear_search(self):
        self._search_input.clear()
        self._table.clear()
        self._results_label.configure(text="Select a search option above to begin...")
        self._search_mode.set("filename")
        self._on_mode_change()

    def _go_back(self):
        if hasattr(self, '_app') and self._app:
            self._app._navigate("documents")

    def _go_dashboard(self):
        if hasattr(self, '_app') and self._app:
            self._app._navigate("dashboard")

    def apply_theme(self):
        self.configure(fg_color=C.bg_main)
