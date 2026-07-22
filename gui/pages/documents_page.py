"""Documents page with grid+table toggle, search, context menu, sort."""

from __future__ import annotations
import customtkinter as ctk
from tkinter import Menu
from gui.theme import ThemeManager, Dim, Fonts
from gui.components.tables import StyledTable
from gui.components.forms import StyledEntry
from gui.components.dialogs import ConfirmDialog, Toast
from gui.smooth_scrolling import bind_smooth_scroll

tm = ThemeManager()
C = tm.C

def _file_colors() -> dict[str, str]:
    c = C
    return {
        "pdf": c.danger, "doc": c.info, "docx": c.info,
        "png": c.warning, "jpg": c.warning, "jpeg": c.warning,
        "txt": c.primary, "csv": c.success, "xlsx": c.success,
    }


class DocumentsPage(ctk.CTkFrame):
    def __init__(self, master, on_refresh=None, user: dict | None = None, **kw):
        kw.pop("fg_color", None)
        super().__init__(master, fg_color=C.bg_main, **kw)
        self._on_refresh = on_refresh
        self._view_mode = "grid"
        self._all_documents = []
        self._documents = []
        self._app = None
        self._user = user or {}
        self._role = self._user.get("role", "viewer").lower()
        self._can_upload = self._role in ("admin", "editor")
        self._can_share = self._role in ("admin", "editor")
        self._can_delete = self._role in ("admin", "editor")

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_content()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=Dim.PAD_XL, pady=(Dim.PAD_XL, 0))
        header.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            header, text="Document Library", font=Fonts.TITLE,
            text_color=C.text_primary,
        ).grid(row=0, column=0, sticky="w")

        controls = ctk.CTkFrame(header, fg_color="transparent")
        controls.grid(row=0, column=1, sticky="e")

        self._search = StyledEntry(
            controls, placeholder="Search documents...", width=200,
        )
        self._search.entry.bind("<KeyRelease>", self._filter_docs)
        self._search.pack(side="left", padx=(0, Dim.PAD_SM))

        self._grid_btn = ctk.CTkButton(
            controls, text="\u25A6", width=32, height=32, font=Fonts.ICON,
            fg_color=C.bg_card, hover_color=C.bg_sidebar_hover,
            text_color=C.primary, corner_radius=Dim.RADIUS_SM,
            command=lambda: self._set_view("grid"),
        )
        self._grid_btn.pack(side="left", padx=2)

        self._table_btn = ctk.CTkButton(
            controls, text="\u2630", width=32, height=32, font=Fonts.ICON,
            fg_color=C.bg_input, hover_color=C.bg_sidebar_hover,
            text_color=C.text_secondary, corner_radius=Dim.RADIUS_SM,
            command=lambda: self._set_view("table"),
        )
        self._table_btn.pack(side="left", padx=2)

    def _set_view(self, mode: str):
        self._view_mode = mode
        self._grid_btn.configure(
            fg_color=C.primary if mode == "grid" else C.bg_card,
            text_color=C.text_on_primary if mode == "grid" else C.primary,
        )
        self._table_btn.configure(
            fg_color=C.primary if mode == "table" else C.bg_input,
            text_color=C.text_on_primary if mode == "table" else C.text_secondary,
        )
        self._render_documents()

    def _build_content(self):
        self._content = ctk.CTkFrame(self, fg_color="transparent")
        self._content.grid(row=1, column=0, sticky="nsew",
                           padx=Dim.PAD_XL, pady=Dim.PAD_MD)
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(0, weight=1)

        self._table_view = StyledTable(self._content, columns=[
            ("document_id", "Document ID", 110),
            ("original_filename", "File Name", 220),
            ("file_extension", "Type", 80),
            ("owner_id", "Owner", 120),
            ("file_size_display", "Size", 90),
            ("created_at", "Modified", 130),
            ("status", "Status", 100),
        ])
        self._table_view.bind_select(self._on_table_select)
        self._table_view.tree.bind("<Button-3>", self._on_right_click)

        self._grid_frame = ctk.CTkScrollableFrame(
            self._content, fg_color="transparent",
            scrollbar_button_color=C.scrollbar,
            scrollbar_button_hover_color=C.scrollbar_hover,
        )
        bind_smooth_scroll(self._grid_frame)

        self._context_menu = None

    def load_documents(self, documents: list[dict]):
        self._all_documents = documents
        self._documents = documents
        self._render_documents()

    def _render_documents(self):
        self._table_view.grid_forget()
        self._grid_frame.grid_forget()

        if self._view_mode == "table":
            self._table_view.grid(row=0, column=0, sticky="nsew")
            self._table_view.insert_rows(self._documents)
        else:
            self._grid_frame.grid(row=0, column=0, sticky="nsew")
            for w in self._grid_frame.winfo_children():
                w.destroy()
            cols = 3
            for i, doc in enumerate(self._documents):
                card = self._make_file_card(self._grid_frame, doc)
                card.grid(row=i // cols, column=i % cols,
                          padx=Dim.PAD_SM, pady=Dim.PAD_SM, sticky="ew")
                self._grid_frame.grid_columnconfigure(i % cols, weight=1)

    def _make_file_card(self, parent, doc: dict) -> ctk.CTkFrame:
        name = doc.get("original_filename", doc.get("filename", "file.txt"))
        ext = name.rsplit(".", 1)[-1].lower() if "." in name else "txt"
        color = _file_colors().get(ext, C.text_dim)
        size = doc.get("file_size_display", doc.get("size", "Unknown"))
        modified = doc.get("created_at", doc.get("modified_at", ""))
        doc_id = doc.get("document_id", "")

        card = ctk.CTkFrame(
            parent, fg_color=C.bg_card, corner_radius=Dim.RADIUS,
            border_width=1, border_color=C.border,
            height=100, cursor="hand2",
        )
        card.pack_propagate(False)
        card.bind("<Button-3>", lambda e, d=doc: self._show_context_menu(e, d))
        card.bind("<Button-1>", lambda e, d=doc: self._on_select(d))
        card.bind("<Enter>", lambda e: card.configure(border_color=C.primary))
        card.bind("<Leave>", lambda e: card.configure(border_color=C.border))

        ctk.CTkLabel(
            card, text=f"\u25C9 .{ext}", font=Fonts.ICON,
            text_color=color, width=40,
        ).pack(side="left", padx=(Dim.PAD_MD, Dim.PAD_SM))

        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, pady=Dim.PAD_MD)
        ctk.CTkLabel(
            info, text=f"{doc_id}  \u2022  {name}", font=Fonts.BODY_BOLD, text_color=C.text_primary,
            anchor="w",
        ).pack(fill="x")
        ctk.CTkLabel(
            info, text=f"{size}  \u2022  {modified}", font=Fonts.TINY,
            text_color=C.text_dim, anchor="w",
        ).pack(fill="x")

        actions = ctk.CTkFrame(card, fg_color="transparent", width=80)
        actions.pack(side="right", padx=Dim.PAD_SM)
        if self._can_share:
            ctk.CTkButton(
                actions, text="\uD83D\uDD17", width=28, height=28, font=Fonts.ICON,
                fg_color=C.bg_input, hover_color=C.success,
                text_color=C.text_secondary, corner_radius=Dim.RADIUS_SM,
                command=lambda d=doc: self._on_share(d),
            ).pack(pady=2)
        ctk.CTkButton(
            actions, text="\u2191", width=28, height=28, font=Fonts.ICON,
            fg_color=C.bg_input, hover_color=C.primary,
            text_color=C.text_secondary, corner_radius=Dim.RADIUS_SM,
            command=lambda d=doc: self._on_download(d),
        ).pack(pady=2)
        return card

    def _on_select(self, doc: dict):
        if hasattr(self, '_app') and self._app:
            try:
                doc_id = doc.get("document_id", "")
                page = self._app._create_page("document_detail")
                if page:
                    self._app._page_cache["document_detail"] = page
                    page.refresh(doc_id)
                    self._app._show_cached_page("document_detail")
            except Exception:
                pass

    def _on_download(self, doc: dict):
        if hasattr(self, '_app') and self._app:
            try:
                self._app._navigate("download")
            except Exception:
                Toast(self, f"Downloading {doc.get('original_filename', doc.get('filename', 'file'))}...", "info")
        else:
            Toast(self, f"Downloading {doc.get('original_filename', doc.get('filename', 'file'))}...", "info")

    def _on_share(self, doc: dict):
        if hasattr(self, '_app') and self._app:
            try:
                self._app._navigate("share")
            except Exception:
                pass

    def _on_table_select(self, _=None):
        pass

    def _on_right_click(self, event):
        sel = self._table_view.get_selected()
        if sel:
            self._show_context_menu(event, sel)

    def _show_context_menu(self, event, doc: dict):
        if self._context_menu:
            self._context_menu.destroy()
        self._context_menu = Menu(
            self, tearoff=0, bg=C.bg_card, fg=C.text_primary,
            activebackground=C.primary, activeforeground=C.text_on_primary,
            font=Fonts.BODY, borderwidth=1, relief="flat",
        )
        self._context_menu.add_command(
            label="Open", command=lambda: self._on_select(doc))
        self._context_menu.add_command(
            label="Download", command=lambda: self._on_download(doc))
        if self._can_share:
            self._context_menu.add_separator()
            self._context_menu.add_command(
                label="Share", command=lambda d=doc: self._on_share(d))
        if self._can_delete:
            self._context_menu.add_separator()
            self._context_menu.add_command(
                label="Delete",
                command=lambda: ConfirmDialog(
                    self, f"Delete '{doc.get('original_filename', doc.get('filename', 'file'))}'?",
                    on_yes=lambda d=doc: self._do_delete(d),
                ))
        try:
            self._context_menu.tk_popup(event.x_root, event.y_root)
        except Exception:
            pass

    def _navigate_to(self, page_name: str):
        if hasattr(self, '_app') and self._app:
            try:
                self._app._navigate(page_name)
            except Exception:
                pass

    def _filter_docs(self, _=None):
        q = self._search.get_value().lower()
        if not q:
            self._documents = self._all_documents
            self._render_documents()
            return
        filtered = [d for d in self._all_documents if q in d.get("original_filename", d.get("filename", "")).lower() or q in d.get("document_id", "").lower()]
        self._documents = filtered
        self._render_documents()

    def _do_delete(self, doc: dict):
        if hasattr(self, '_app') and self._app and hasattr(self._app, 'controller') and self._app.controller:
            try:
                result = self._app.controller["document"].delete_document(doc.get("document_id", ""))
                if result and result.get("success"):
                    Toast(self, "File deleted successfully", "success")
                    if self._on_refresh:
                        self._on_refresh()
                else:
                    error_msg = result.get("error", "Delete failed") if result else "Delete failed"
                    Toast(self, error_msg, "error")
            except Exception as e:
                Toast(self, f"Delete failed: {e}", "error")
        else:
            Toast(self, "Delete unavailable — no backend connected", "error")

    def apply_theme(self):
        self.configure(fg_color=C.bg_main)
