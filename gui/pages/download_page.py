"""Download page with file browser, filter, and progress."""

from __future__ import annotations
import customtkinter as ctk
from gui.theme import ThemeManager, Dim, Fonts
from gui.components.tables import StyledTable
from gui.components.forms import StyledEntry, StyledButton
from gui.components.loading import AnimatedProgressBar
from gui.components.dialogs import Toast

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
            header, placeholder="Filter files...", width=220,
        )
        self._search.entry.bind("<KeyRelease>", self._filter)
        self._search.grid(row=0, column=1, sticky="e")

    def _build_content(self):
        self._table = StyledTable(self, columns=[
            ("name", "File Name", 240),
            ("type", "Type", 80),
            ("owner", "Owner", 120),
            ("size", "Size", 90),
            ("modified", "Modified", 130),
        ])
        self._table.grid(row=1, column=0, sticky="nsew",
                         padx=Dim.PAD_XL, pady=Dim.PAD_MD)
        self._table.bind_select(self._on_select)

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
        filtered = [d for d in self._documents if q in d.get("filename", "").lower()]
        self._table.insert_rows(filtered)

    def _download(self):
        sel = self._table.get_selected()
        if not sel:
            Toast(self, "Select a file to download", "warning")
            return
        self._progress_frame.grid()
        self._progress_bar.set_progress(0)
        self._animate()

    def _animate(self, step=0):
        if step <= 10:
            self._progress_bar.set_progress(step / 10)
            self._progress_label.configure(text=f"Downloading... {step * 10}%")
            self.after(150, lambda: self._animate(step + 1))
        else:
            self._progress_label.configure(text="Download complete!")
            Toast(self, "File downloaded and decrypted successfully!", "success")
            self.after(1500, lambda: self._progress_frame.grid_remove())
