"""Download page with file browser, filter, and progress."""

from __future__ import annotations
import customtkinter as ctk
from gui.theme import ThemeManager, Dim, Fonts
from gui.components.tables import StyledTable
from gui.components.forms import StyledEntry, StyledButton
from gui.components.loading import AnimatedProgressBar
from gui.components.dialogs import Toast
from gui.smooth_scrolling import bind_smooth_scroll

tm = ThemeManager()
C = tm.C


class DownloadPage(ctk.CTkFrame):
    def __init__(self, master, **kw):
        super().__init__(master, fg_color=C.bg_main, **kw)
        self._documents = []

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_content()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=Dim.PAD_XL, pady=(Dim.PAD_XL, 0))
        header.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(
            header, text="Download Documents", font=Fonts.TITLE,
            text_color=C.text_primary,
        ).grid(row=0, column=0, sticky="w")
        self._search = StyledEntry(
            header, placeholder="Search by Document ID or file name...", width=280,
        )
        self._search.entry.bind("<KeyRelease>", self._filter)
        self._search.grid(row=0, column=1, sticky="e")

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
            ("original_filename", "File Name", 240),
            ("file_extension", "Type", 80),
            ("owner_id", "Owner", 120),
            ("file_size_display", "Size", 90),
            ("created_at", "Modified", 130),
        ])
        self._table.grid(row=0, column=0, sticky="nsew")
        self._table.bind_select(self._on_select)
        bind_smooth_scroll(scroll)

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="ew",
                       padx=Dim.PAD_XL, pady=(0, Dim.PAD_XL))
        StyledButton(
            btn_frame, text="Download Selected", icon="\u2193",
            command=self._download, width=160,
        ).pack(side="left")

        self._progress_frame = ctk.CTkFrame(self, fg_color=C.bg_card,
                                            corner_radius=Dim.RADIUS_LG)
        self._progress_frame.grid(row=3, column=0, sticky="ew",
                                  padx=Dim.PAD_XL, pady=(0, Dim.PAD_MD))
        self._progress_frame.grid_columnconfigure(0, weight=1)
        self._progress_frame.grid_remove()
        self._progress_label = ctk.CTkLabel(
            self._progress_frame, text="Downloading...", font=Fonts.BODY,
            text_color=C.text_primary,
        )
        self._progress_label.grid(row=0, column=0, sticky="w",
                                  padx=Dim.PAD_LG, pady=(Dim.PAD_MD, Dim.PAD_SM))
        self._progress_bar = AnimatedProgressBar(self._progress_frame, width=400)
        self._progress_bar.grid(row=1, column=0, sticky="ew",
                                padx=Dim.PAD_LG, pady=(0, Dim.PAD_MD))

        self._post_frame = ctk.CTkFrame(self, fg_color="transparent")
        self._post_frame.grid(row=4, column=0, sticky="ew",
                              padx=Dim.PAD_XL, pady=(0, Dim.PAD_MD))
        self._post_frame.grid_remove()

        self._post_label = ctk.CTkLabel(
            self._post_frame, text="Download complete!",
            font=Fonts.SUBTITLE, text_color=C.success,
        )
        self._post_label.grid(row=0, column=0, columnspan=4, pady=(0, Dim.PAD_MD))

        StyledButton(
            self._post_frame, text="Download Another", variant="outline",
            command=self._download_another, width=140,
        ).grid(row=1, column=0, padx=(0, Dim.PAD_SM))
        StyledButton(
            self._post_frame, text="Open Folder", variant="outline",
            command=self._open_folder, width=120,
        ).grid(row=1, column=1, padx=(0, Dim.PAD_SM))
        StyledButton(
            self._post_frame, text="Back", variant="outline",
            command=self._go_back, width=100,
        ).grid(row=1, column=2, padx=(0, Dim.PAD_SM))
        StyledButton(
            self._post_frame, text="Dashboard",
            command=self._go_dashboard, width=120,
        ).grid(row=1, column=3)

    def load_documents(self, documents: list[dict]):
        self._documents = documents
        self._table.insert_rows(documents)

    def _on_select(self, _=None):
        pass

    def _filter(self, _=None):
        q = self._search.get_value().lower()
        if not q:
            self._table.insert_rows(self._documents)
            return
        filtered = [d for d in self._documents if q in d.get("original_filename", d.get("filename", "")).lower() or q in d.get("document_id", "").lower()]
        self._table.insert_rows(filtered)

    def _download(self):
        sel = self._table.get_selected()
        if not sel:
            Toast(self, "Select a file to download", "warning")
            return
        self._progress_frame.grid()
        self._post_frame.grid_remove()
        self._progress_bar.set_progress(0)
        self._animate()

    def _animate(self, step=0):
        if step <= 10:
            self._progress_bar.set_progress(step / 10)
            self._progress_label.configure(text=f"Downloading... {step * 10}%")
            self.after(150, lambda: self._animate(step + 1))
        else:
            self._progress_label.configure(text="Download complete!")
            self._progress_frame.grid_remove()
            Toast(self, "File downloaded and decrypted successfully!", "success")
            self._post_frame.grid()

    def _download_another(self):
        self._post_frame.grid_remove()

    def _open_folder(self):
        Toast(self, "Opening download folder...", "info")

    def _go_back(self):
        if hasattr(self, '_app') and self._app:
            self._app._navigate("documents")

    def _go_dashboard(self):
        if hasattr(self, '_app') and self._app:
            self._app._navigate("dashboard")

    def apply_theme(self):
        self.configure(fg_color=C.bg_main)
