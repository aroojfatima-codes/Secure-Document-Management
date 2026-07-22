"""Document detail page — full metadata view for a single document."""

from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter as ctk

from gui.components.cards import InfoCard, PageHeader
from gui.components.forms import StyledButton
from gui.components.dialogs import Toast
from gui.theme import ThemeManager, Dim, Fonts
from gui.smooth_scrolling import bind_smooth_scroll

if TYPE_CHECKING:
    from gui.app import App

tm = ThemeManager()
C = tm.C


class DocumentDetailPage(ctk.CTkFrame):
    """Show detailed metadata for a single document."""

    def __init__(self, master, app: "App | None" = None, user: dict | None = None, **kwargs) -> None:
        kwargs.pop("fg_color", None)
        super().__init__(master, fg_color=C.bg_main, **kwargs)
        self._app = app
        self._user = user or {}
        self._role = self._user.get("role", "viewer").lower()
        self._can_share = self._role in ("admin", "editor")
        self._can_download = True
        self._doc_id: str = ""

        header = PageHeader(
            self,
            title="Document Details",
            actions=[("Back to Documents", self._go_back)],
        )
        header.pack(fill="x", padx=Dim.PAD_XL, pady=(Dim.PAD_XL, 0))

        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=C.scrollbar,
            scrollbar_button_hover_color=C.scrollbar_hover,
        )
        self._scroll.pack(fill="both", expand=True, padx=Dim.PAD_XL, pady=Dim.PAD_MD)
        bind_smooth_scroll(self._scroll)

        # Show a placeholder if no document is loaded yet
        ctk.CTkLabel(
            self._scroll, text="Select a document to view its details",
            font=Fonts.BODY, text_color=C.text_secondary,
        ).pack(pady=Dim.PAD_XL)

    def _go_back(self):
        if self._app:
            try:
                self._app._navigate("documents")
            except Exception:
                pass

    def refresh(self, document_id: str = "") -> None:
        if document_id:
            self._doc_id = document_id

        for w in self._scroll.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

        ctrl = None
        if self._app:
            ctrl = self._app.controller
        if not ctrl:
            # Show placeholder when no controller
            ctk.CTkLabel(
                self._scroll, text="No controller available",
                font=Fonts.BODY, text_color=C.danger,
            ).pack(pady=Dim.PAD_XL)
            return

        try:
            result = ctrl["document"].get_document_detail(self._doc_id)
        except Exception as exc:
            Toast(self, f"Failed to load document: {exc}", "error")
            ctk.CTkLabel(
                self._scroll, text=f"Error: {exc}",
                font=Fonts.BODY, text_color=C.danger,
            ).pack(pady=Dim.PAD_XL)
            return

        if not result or not result.get("success"):
            Toast(self, "Failed to load document.", "error")
            ctk.CTkLabel(
                self._scroll, text="Document not found",
                font=Fonts.BODY, text_color=C.text_secondary,
            ).pack(pady=Dim.PAD_XL)
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

        if self._can_share:
            StyledButton(
                actions, text="Share", variant="success", command=self._share, width=130,
            ).pack(side="left", padx=(0, 8))

        StyledButton(
            actions, text="Back to Documents", variant="outline",
            command=self._go_back, width=160,
        ).pack(side="left", padx=(0, 8))

        StyledButton(
            actions, text="Dashboard",
            command=self._go_dashboard, width=120,
        ).pack(side="right")

    def _download(self) -> None:
        if self._app:
            try:
                self._app._navigate("download")
            except Exception:
                pass

    def _share(self) -> None:
        if self._app:
            try:
                self._app._navigate("share")
            except Exception:
                pass

    def _go_dashboard(self) -> None:
        if self._app:
            try:
                self._app._navigate("dashboard")
            except Exception:
                pass

    def apply_theme(self):
        self.configure(fg_color=C.bg_main)
