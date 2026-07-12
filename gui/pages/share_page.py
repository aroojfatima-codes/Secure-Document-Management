"""Share page for sharing documents with other users."""

from __future__ import annotations
import customtkinter as ctk
from gui.theme import ThemeManager, Dim, Fonts
from gui.components.forms import StyledEntry, StyledComboBox, StyledButton
from gui.components.dialogs import Toast

tm = ThemeManager()
C = tm.C


class SharePage(ctk.CTkFrame):
    def __init__(self, master, on_share=None, **kw):
        super().__init__(master, fg_color=C.bg_main, **kw)
        self._on_share = on_share

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_content()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=Dim.PAD_XL, pady=(Dim.PAD_XL, 0))
        ctk.CTkLabel(
            header, text="Share Documents", font=Fonts.TITLE,
            text_color=C.text_primary,
        ).pack(anchor="w")
        ctk.CTkLabel(
            header, text="Share files securely with team members",
            font=Fonts.BODY, text_color=C.text_secondary,
        ).pack(anchor="w", pady=(2, 0))

    def _build_content(self):
        card = ctk.CTkFrame(
            self, fg_color=C.bg_card, corner_radius=Dim.RADIUS_LG,
            width=500,
        )
        card.grid(row=1, column=0, sticky="nw", padx=Dim.PAD_XL, pady=Dim.PAD_MD)
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            card, text="Document:", font=Fonts.BODY, text_color=C.text_secondary,
        ).grid(row=0, column=0, sticky="w", padx=Dim.PAD_LG, pady=Dim.PAD_MD)
        self._doc = StyledComboBox(
            card, values=["doc_v2.pdf", "report.docx", "photo.png"], width=300,
        )
        self._doc.grid(row=0, column=1, sticky="w", padx=Dim.PAD_SM, pady=Dim.PAD_MD)

        ctk.CTkLabel(
            card, text="Share with:", font=Fonts.BODY, text_color=C.text_secondary,
        ).grid(row=1, column=0, sticky="w", padx=Dim.PAD_LG, pady=Dim.PAD_MD)
        self._user = StyledEntry(card, placeholder="Username", width=300)
        self._user.grid(row=1, column=1, sticky="w", padx=Dim.PAD_SM, pady=Dim.PAD_MD)

        ctk.CTkLabel(
            card, text="Permission:", font=Fonts.BODY, text_color=C.text_secondary,
        ).grid(row=2, column=0, sticky="w", padx=Dim.PAD_LG, pady=Dim.PAD_MD)
        self._perm = StyledComboBox(
            card, values=["View Only", "Download", "Edit"], width=300,
        )
        self._perm.grid(row=2, column=1, sticky="w", padx=Dim.PAD_SM, pady=Dim.PAD_MD)

        ctk.CTkLabel(
            card, text="Note (optional):", font=Fonts.BODY, text_color=C.text_secondary,
        ).grid(row=3, column=0, sticky="nw", padx=Dim.PAD_LG, pady=Dim.PAD_MD)
        self._note = ctk.CTkTextbox(
            card, height=60, width=300, fg_color=C.bg_input,
            text_color=C.text_primary, font=Fonts.BODY,
            corner_radius=Dim.RADIUS,
        )
        self._note.grid(row=3, column=1, sticky="w", padx=Dim.PAD_SM, pady=Dim.PAD_MD)

        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.grid(row=4, column=0, columnspan=2, pady=Dim.PAD_LG)
        StyledButton(
            btn_frame, text="Share Document", icon="\uD83D\uDD17",
            command=self._do_share, width=160,
        ).pack()

    def _do_share(self):
        doc = self._doc.get_value()
        user = self._user.get_value()
        if not user:
            Toast(self, "Please enter a username", "warning")
            return
        Toast(self, f"Shared '{doc}' with {user}", "success")
        self._user.clear()
