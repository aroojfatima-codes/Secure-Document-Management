"""Share page for sharing documents with other users."""

from __future__ import annotations
import customtkinter as ctk
from gui.theme import ThemeManager, Dim, Fonts
from gui.components.forms import StyledEntry, StyledComboBox, StyledButton
from gui.components.tables import StyledTable
from gui.components.dialogs import Toast, SuccessDialog
from gui.smooth_scrolling import bind_smooth_scroll

tm = ThemeManager()
C = tm.C


class SharePage(ctk.CTkFrame):
    def __init__(self, master, on_share=None, **kw):
        kw.pop("fg_color", None)
        super().__init__(master, fg_color=C.bg_main, **kw)
        self._on_share = on_share
        self._documents = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)
        self._build_header()
        self._build_content()
        self._build_results()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=Dim.PAD_XL, pady=(Dim.PAD_XL, 0))
        ctk.CTkLabel(
            header, text="Share Documents", font=Fonts.TITLE,
            text_color=C.text_primary,
        ).pack(anchor="w")
        ctk.CTkLabel(
            header, text="Select a document from the table below and share it securely",
            font=Fonts.BODY, text_color=C.text_secondary,
        ).pack(anchor="w", pady=(2, 0))

    def _build_content(self):
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=C.scrollbar,
            scrollbar_button_hover_color=C.scrollbar_hover,
        )
        scroll.grid(row=1, column=0, sticky="ew", padx=Dim.PAD_XL, pady=Dim.PAD_MD)
        scroll.grid_columnconfigure(0, weight=1)

        self._table = StyledTable(scroll, columns=[
            ("document_id", "Document ID", 110),
            ("original_filename", "File Name", 220),
            ("owner_id", "Owner", 120),
            ("file_size_display", "Size", 90),
            ("status", "Status", 100),
        ])
        self._table.grid(row=0, column=0, sticky="nsew")
        bind_smooth_scroll(scroll)

        card = ctk.CTkFrame(
            self, fg_color=C.bg_card, corner_radius=Dim.RADIUS_LG,
        )
        card.grid(row=2, column=0, sticky="ew",
                  padx=Dim.PAD_XL, pady=Dim.PAD_MD)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card, text="Share with:", font=Fonts.BODY, text_color=C.text_secondary,
        ).grid(row=0, column=0, sticky="w", padx=Dim.PAD_LG, pady=Dim.PAD_MD)
        self._user = StyledEntry(card, placeholder="Enter username")
        self._user.grid(row=0, column=1, sticky="ew", padx=Dim.PAD_SM, pady=Dim.PAD_MD)

        ctk.CTkLabel(
            card, text="Permission:", font=Fonts.BODY, text_color=C.text_secondary,
        ).grid(row=1, column=0, sticky="w", padx=Dim.PAD_LG, pady=Dim.PAD_MD)
        self._perm = StyledComboBox(
            card, values=["View Only", "Download", "Edit"],
        )
        self._perm.grid(row=1, column=1, sticky="ew", padx=Dim.PAD_SM, pady=Dim.PAD_MD)

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=2, column=0, columnspan=2, pady=Dim.PAD_MD)
        StyledButton(
            btn_frame, text="Share Document", icon="\uD83D\uDD17",
            command=self._do_share, width=160,
        ).pack(side="left", padx=(0, Dim.PAD_SM))
        StyledButton(
            btn_frame, text="Share Another", variant="outline",
            command=self._share_another, width=130,
        ).pack(side="left", padx=(0, Dim.PAD_SM))
        StyledButton(
            btn_frame, text="View Shared Documents", variant="outline",
            command=self._view_shared, width=160,
        ).pack(side="left", padx=(0, Dim.PAD_SM))
        StyledButton(
            btn_frame, text="Dashboard",
            command=self._go_dashboard, width=120,
        ).pack(side="right")

    def _build_results(self):
        self._results_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._results_frame.grid(row=3, column=0, sticky="ew",
                                 padx=Dim.PAD_XL, pady=(0, Dim.PAD_MD))
        self._results_frame.grid_remove()

    def load_documents(self, docs: list[dict]):
        self._documents = docs
        self._table.insert_rows(docs)

    def _do_share(self):
        sel = self._table.get_selected()
        user = self._user.get_value()
        if not sel:
            Toast(self, "Please select a document from the table", "warning")
            return
        if not user:
            Toast(self, "Please enter a username", "warning")
            return
        doc_id = sel.get("document_id", "")
        doc_name = sel.get("original_filename", "file")
        SuccessDialog(
            self,
            message=f"Document '{doc_name}' ({doc_id}) shared with '{user}' successfully.",
            title="Document Shared",
        )
        self._user.clear()

    def _share_another(self):
        self._user.clear()

    def _view_shared(self):
        if hasattr(self, '_app') and self._app:
            try:
                self._app._navigate("shared")
            except Exception:
                pass

    def _go_dashboard(self):
        if hasattr(self, '_app') and self._app:
            try:
                self._app._navigate("dashboard")
            except Exception:
                pass

    def apply_theme(self):
        self.configure(fg_color=C.bg_main)
