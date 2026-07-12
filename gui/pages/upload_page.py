"""Upload page with drag-drop zone, file selector, and progress."""

from __future__ import annotations
import customtkinter as ctk
from gui.theme import ThemeManager, Dim, Fonts
from gui.components.forms import StyledButton, StyledEntry, StyledComboBox, StyledText
from gui.components.loading import AnimatedProgressBar
from gui.components.dialogs import Toast

tm = ThemeManager()
C = tm.C


class UploadPage(ctk.CTkFrame):
    def __init__(self, master, on_upload=None, **kw):
        super().__init__(master, fg_color=C.bg_main, **kw)
        self._on_upload = on_upload
        self._selected_path = ""

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_content()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=Dim.PAD_XL, pady=(Dim.PAD_XL, 0))
        ctk.CTkLabel(
            header, text="Upload Document", font=Fonts.TITLE,
            text_color=C.text_primary,
        ).pack(anchor="w")
        ctk.CTkLabel(
            header, text="Securely upload and encrypt your files",
            font=Fonts.BODY, text_color=C.text_secondary,
        ).pack(anchor="w", pady=(2, 0))

    def _build_content(self):
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=C.scrollbar,
            scrollbar_button_hover_color=C.scrollbar_hover,
        )
        scroll.grid(row=1, column=0, sticky="nsew", padx=Dim.PAD_XL, pady=Dim.PAD_MD)
        scroll.grid_columnconfigure(0, weight=1)

        drop_zone = ctk.CTkFrame(
            scroll, fg_color=C.bg_input, corner_radius=Dim.RADIUS_LG,
            border_width=2, border_color=C.border,
            height=180, cursor="hand2",
        )
        drop_zone.grid(row=0, column=0, sticky="ew", pady=(0, Dim.PAD_LG))
        drop_zone.pack_propagate(False)
        drop_zone.bind("<Button-1>", lambda e: self._browse())

        ctk.CTkLabel(
            drop_zone, text="\u2B06\uFE0F", font=(Fonts.F, 32),
            text_color=C.text_dim,
        ).pack(pady=(Dim.PAD_LG, Dim.PAD_SM))
        self._drop_label = ctk.CTkLabel(
            drop_zone, text="Click to browse or drag file here",
            font=Fonts.BODY, text_color=C.text_secondary,
        )
        self._drop_label.pack()
        ctk.CTkLabel(
            drop_zone, text="Supports PDF, DOCX, TXT, images, and more",
            font=Fonts.TINY, text_color=C.text_dim,
        ).pack(pady=(2, 0))

        info_frame = ctk.CTkFrame(scroll, fg_color=C.bg_card, corner_radius=Dim.RADIUS_LG)
        info_frame.grid(row=1, column=0, sticky="ew", pady=(0, Dim.PAD_LG))
        info_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            info_frame, text="File Details", font=Fonts.SUBTITLE,
            text_color=C.text_primary,
        ).grid(row=0, column=0, columnspan=2, sticky="w",
               padx=Dim.PAD_LG, pady=(Dim.PAD_MD, Dim.PAD_SM))

        self._filename_label = ctk.CTkLabel(
            info_frame, text="No file selected", font=Fonts.BODY,
            text_color=C.text_dim, anchor="w",
        )
        self._filename_label.grid(row=1, column=0, columnspan=2,
                                  sticky="w", padx=Dim.PAD_LG)

        ctk.CTkLabel(
            info_frame, text="Title:", font=Fonts.BODY, text_color=C.text_secondary,
        ).grid(row=2, column=0, sticky="w", padx=Dim.PAD_LG, pady=Dim.PAD_SM)
        self._title = StyledEntry(info_frame, width=300)
        self._title.grid(row=2, column=1, sticky="w", padx=Dim.PAD_SM, pady=Dim.PAD_SM)

        ctk.CTkLabel(
            info_frame, text="Category:", font=Fonts.BODY, text_color=C.text_secondary,
        ).grid(row=3, column=0, sticky="w", padx=Dim.PAD_LG, pady=Dim.PAD_SM)
        self._category = StyledComboBox(
            info_frame, values=["General", "Finance", "Legal", "HR", "Technical"], width=300,
        )
        self._category.grid(row=3, column=1, sticky="w", padx=Dim.PAD_SM, pady=Dim.PAD_SM)

        ctk.CTkLabel(
            info_frame, text="Description:", font=Fonts.BODY,
            text_color=C.text_secondary,
        ).grid(row=4, column=0, sticky="nw", padx=Dim.PAD_LG, pady=Dim.PAD_SM)
        self._description = StyledText(info_frame, height=60, width=300)
        self._description.grid(row=4, column=1, sticky="w", padx=Dim.PAD_SM, pady=Dim.PAD_SM)

        self._progress_frame = ctk.CTkFrame(scroll, fg_color=C.bg_card, corner_radius=Dim.RADIUS_LG)
        self._progress_frame.grid(row=2, column=0, sticky="ew", pady=(0, Dim.PAD_LG))
        self._progress_frame.grid_columnconfigure(0, weight=1)
        self._progress_frame.grid_remove()

        self._progress_label = ctk.CTkLabel(
            self._progress_frame, text="Uploading...", font=Fonts.BODY,
            text_color=C.text_primary,
        )
        self._progress_label.grid(row=0, column=0, sticky="w",
                                  padx=Dim.PAD_LG, pady=(Dim.PAD_MD, Dim.PAD_SM))
        self._progress_bar = AnimatedProgressBar(self._progress_frame, width=400)
        self._progress_bar.grid(row=1, column=0, sticky="ew",
                                padx=Dim.PAD_LG, pady=(0, Dim.PAD_MD))

        btn_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        btn_frame.grid(row=3, column=0, sticky="ew")
        StyledButton(
            btn_frame, text="Upload & Encrypt", icon="\u2B06\uFE0F",
            command=self._do_upload, width=160,
        ).pack(side="left", padx=(0, Dim.PAD_SM))
        StyledButton(
            btn_frame, text="Clear", variant="outline",
            command=self._clear, width=100,
        ).pack(side="left")

    def _browse(self):
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(
            title="Select File",
            filetypes=[
                ("All Supported", "*.pdf *.docx *.doc *.txt *.csv *.xlsx *.png *.jpg *.jpeg"),
                ("PDF", "*.pdf"), ("Word", "*.docx *.doc"), ("Text", "*.txt"),
                ("Images", "*.png *.jpg *.jpeg"), ("All files", "*.*"),
            ],
        )
        root.destroy()
        if path:
            self._selected_path = path
            import os
            fname = os.path.basename(path)
            size = os.path.getsize(path)
            size_str = f"{size / 1024:.1f} KB" if size < 1048576 else f"{size / 1048576:.1f} MB"
            self._filename_label.configure(
                text=f"{fname} ({size_str})", text_color=C.text_primary)
            self._title.set_value(fname.rsplit(".", 1)[0])

    def _do_upload(self):
        if not self._selected_path:
            Toast(self, "Please select a file first", "warning")
            return
        self._progress_frame.grid()
        self._progress_bar.set_progress(0)
        self._animate_upload()

    def _animate_upload(self, step=0):
        if step <= 10:
            self._progress_bar.set_progress(step / 10)
            self._progress_label.configure(text=f"Uploading... {step * 10}%")
            self.after(200, lambda: self._animate_upload(step + 1))
        else:
            self._progress_label.configure(text="Upload complete!")
            Toast(self, "File uploaded and encrypted successfully!", "success")
            self.after(1500, lambda: self._progress_frame.grid_remove())

    def _clear(self):
        self._selected_path = ""
        self._filename_label.configure(text="No file selected", text_color=C.text_dim)
        self._title.clear()
        self._description.clear()
