"""Shared documents page showing files shared with/by the user."""

from __future__ import annotations
import customtkinter as ctk
from gui.theme import ThemeManager, Dim, Fonts
from gui.components.tables import StyledTable
from gui.components.forms import StyledButton, StyledComboBox, StyledEntry
from gui.components.dialogs import Toast, ConfirmDialog, SuccessDialog, ErrorDialog
from gui.smooth_scrolling import bind_smooth_scroll

tm = ThemeManager()
C = tm.C


class SharedPage(ctk.CTkFrame):
    def __init__(self, master, controller=None, user: dict | None = None, **kw):
        kw.pop("fg_color", None)
        super().__init__(master, fg_color=C.bg_main, **kw)
        self._controller = controller
        self._shared = []
        self._app = None
        self._user = user or {}
        self._role = self._user.get("role", "viewer").lower()
        self._can_revoke = self._role in ("admin", "editor")

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
            header, values=["All", "Shared With Me"], width=180,
        )
        self._filter.combo.configure(command=self._apply_filter)
        self._filter.grid(row=0, column=1, sticky="e", padx=(0, Dim.PAD_SM))
        self._search = StyledEntry(
            header, placeholder="Search by Document ID or file name...", width=250,
        )
        self._search.entry.bind("<KeyRelease>", self._search_docs)
        self._search.grid(row=0, column=2, sticky="e", padx=(0, Dim.PAD_SM))
        StyledButton(
            header, text="Refresh", variant="outline", width=90,
            command=self._refresh,
        ).grid(row=0, column=3, sticky="e")

    def _build_content(self):
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=C.scrollbar,
            scrollbar_button_hover_color=C.scrollbar_hover,
        )
        scroll.grid(row=1, column=0, sticky="nsew",
                    padx=Dim.PAD_XL, pady=Dim.PAD_MD)
        scroll.grid_columnconfigure(0, weight=1)

        self._table = StyledTable(scroll, columns=[
            ("document_id", "Document ID", 110),
            ("original_filename", "File Name", 200),
            ("owner_id", "Owner", 120),
            ("file_size_display", "Size", 100),
            ("mime_type", "Type", 100),
            ("created_at", "Date Shared", 150),
        ])
        self._table.grid(row=0, column=0, sticky="nsew")
        bind_smooth_scroll(scroll)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew",
                       padx=Dim.PAD_XL, pady=(0, Dim.PAD_XL))
        if self._can_revoke:
            StyledButton(
                btn_frame, text="Revoke Access", variant="danger",
                command=self._revoke, width=140,
            ).pack(side="left")

    def load_documents(self, docs: list[dict]):
        self._shared = docs
        self._table.insert_rows(docs)

    def _apply_filter(self, _=None):
        mode = self._filter.get_value()
        if mode == "All":
            self._table.insert_rows(self._shared)
        elif mode == "Shared With Me":
            self._table.insert_rows([s for s in self._shared if s.get("direction") == "to_me"])
        else:
            self._table.insert_rows([s for s in self._shared if s.get("direction") == "by_me"])

    def _search_docs(self, _=None):
        q = self._search.get_value().lower()
        if not q:
            self._table.insert_rows(self._shared)
            return
        filtered = [s for s in self._shared if q in s.get("document_id", "").lower() or q in s.get("original_filename", "").lower()]
        self._table.insert_rows(filtered)

    def _refresh(self):
        if self._controller:
            try:
                result = self._controller["document"].list_shared_with_me(1, 50)
                if result and result.get("success"):
                    docs = result.get("documents", [])
                    for d in docs:
                        d["direction"] = "to_me"
                    self._shared = docs
                    self._table.insert_rows(self._shared)
                    Toast(self, "Shared documents refreshed", "info")
                else:
                    Toast(self, "Failed to refresh shared documents", "error")
            except Exception as exc:
                Toast(self, f"Refresh error: {exc}", "error")
        else:
            self._table.insert_rows(self._shared)
            Toast(self, "Shared documents refreshed", "info")

    def _revoke(self):
        sel = self._table.get_selected()
        if not sel:
            Toast(self, "Select a share entry to revoke", "warning")
            return
        doc_id = sel.get("document_id", "")
        doc_name = sel.get("original_filename", "file")
        owner_id = sel.get("owner_id", "")

        if not self._controller:
            Toast(self, "No controller available", "error")
            return

        def do_revoke():
            try:
                result = self._controller["document"].revoke_share(doc_id, owner_id)
                if result and result.get("success"):
                    SuccessDialog(
                        self,
                        message=f"Access revoked for '{doc_name}'.",
                        title="Access Revoked",
                    )
                    self._refresh()
                else:
                    error_msg = result.get("error", "Revoke failed") if result else "Revoke failed"
                    ErrorDialog(self, message=str(error_msg), title="Revoke Failed")
            except Exception as exc:
                ErrorDialog(self, message=f"Revoke error: {exc}", title="Revoke Error")

        ConfirmDialog(
            self,
            f"Revoke access for '{doc_name}'?",
            on_yes=do_revoke,
        )

    def apply_theme(self):
        self.configure(fg_color=C.bg_main)
