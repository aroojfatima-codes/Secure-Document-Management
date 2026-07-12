"""Document detail page — full metadata view for a single document."""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

import customtkinter as ctk

from gui.components.cards import InfoCard, PageHeader
from gui.components.forms import StyledButton
from gui.components.dialogs import Toast
from gui.theme import ThemeManager, Dim, Fonts

if TYPE_CHECKING:
    from gui.app import App

tm = ThemeManager()
C = tm.C


class DocumentDetailPage(ctk.CTkFrame):
    """Show detailed metadata for a single document."""

    def __init__(self, master, app: "App | None" = None, **kwargs) -> None:
        super().__init__(master, fg_color=C.bg_main, **kwargs)
        self._app = app
        self._doc_id: str = ""

        header = PageHeader(
            self,
            title="Document Details",
            actions=[("Back to Documents", lambda: self._app._navigate("documents"))],
        )
        header.pack(fill="x", padx=Dim.PAD_XL, pady=(Dim.PAD_XL, 0))

        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=C.scrollbar,
            scrollbar_button_hover_color=C.scrollbar_hover,
        )
        self._scroll.pack(fill="both", expand=True, padx=Dim.PAD_XL, pady=Dim.PAD_MD)

    def refresh(self, document_id: str = "") -> None:
        if document_id:
            self._doc_id = document_id

        for w in self._scroll.winfo_children():
            w.destroy()

        ctrl = self._app.controller
        if not ctrl:
            Toast(self, "No controller available", "error")
            return

        try:
            result = ctrl["document"].get_document_detail(self._doc_id)
        except Exception as exc:
            Toast(self, f"Failed to load document: {exc}", "error")
            return

        if not result or not result.get("success"):
            Toast(self, "Failed to load document.", "error")
            return

        doc = result.get("document", result)

        card = InfoCard(self._scroll, title="Document Information")
        card.pack(fill="x", pady=(0, Dim.PAD_MD))

        fields = [
            ("Document ID", doc.get("document_id", "")),
            ("Filename", doc.get("original_filename", "")),
            ("MIME Type", doc.get("mime_type", "")),
            ("File Size", f"{doc.get('file_size', 0):,} bytes"),
            ("SHA-256 Hash", doc.get("sha256_hash", "")),
            ("Owner ID", doc.get("owner_id", "")),
            ("Status", doc.get("status", "")),
            ("Shared With", f"{doc.get('shared_with_count', 0)} user(s)"),
            ("Created", str(doc.get("created_at", ""))[:19]),
            ("Updated", str(doc.get("updated_at", ""))[:19]),
        ]

        for label, value in fields:
            card.add_row(label, value)

        actions = ctk.CTkFrame(self._scroll, fg_color="transparent")
        actions.pack(fill="x", pady=(0, Dim.PAD_MD))

        StyledButton(
            actions, text="Download", variant="primary", command=self._download, width=130,
        ).pack(side="left", padx=(0, 8))

        StyledButton(
            actions, text="Share", variant="success", command=self._share, width=130,
        ).pack(side="left")

    def _download(self) -> None:
        self._app._navigate("download")

    def _share(self) -> None:
        self._app._navigate("share")

    def apply_theme(self):
        self.configure(fg_color=C.bg_main)
