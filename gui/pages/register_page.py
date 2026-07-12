"""Registration page with multi-field form, password strength meter."""

from __future__ import annotations
import customtkinter as ctk
from gui.theme import ThemeManager, Dim, Fonts
from gui.components.forms import StyledEntry, PasswordEntry, StyledComboBox, StyledButton
from gui.components.dialogs import Toast

tm = ThemeManager()
C = tm.C


class RegisterPage(ctk.CTkFrame):
    def __init__(self, master, on_register=None, on_switch_login=None, **kw):
        super().__init__(master, fg_color=C.bg_main, **kw)
        self._on_register = on_register
        self._on_switch_login = on_switch_login

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        center = ctk.CTkFrame(self, fg_color="transparent")
        center.grid(row=0, column=0)

        card = ctk.CTkFrame(
            center, fg_color=C.bg_card_translucent, corner_radius=Dim.RADIUS_XL,
            border_width=1, border_color=C.border_light,
            width=440, height=620,
        )
        card.pack_propagate(False)
        card.grid(row=0, column=0, padx=Dim.PAD_XL, pady=Dim.PAD_XL)

        ctk.CTkLabel(
            card, text="Create Account", font=Fonts.TITLE,
            text_color=C.text_primary,
        ).pack(pady=(Dim.PAD_XL, Dim.PAD_SM))
        ctk.CTkLabel(
            card, text="Fill in your details to register",
            font=Fonts.BODY, text_color=C.text_secondary,
        ).pack(pady=(0, Dim.PAD_LG))

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.pack(fill="x", padx=Dim.PAD_LG)

        self._username = StyledEntry(form, label="Username", placeholder="Choose a username", width=350)
        self._username.pack(fill="x", pady=(0, Dim.PAD_SM))

        self._fullname = StyledEntry(form, label="Full Name", placeholder="Your full name", width=350)
        self._fullname.pack(fill="x", pady=(0, Dim.PAD_SM))

        self._email = StyledEntry(form, label="Email", placeholder="you@example.com", width=350)
        self._email.pack(fill="x", pady=(0, Dim.PAD_SM))

        self._role = StyledComboBox(form, label="Role",
                                    values=["admin", "officer", "viewer"], width=350)
        self._role.pack(fill="x", pady=(0, Dim.PAD_SM))

        self._password = PasswordEntry(form, label="Password", width=350)
        self._password.pack(fill="x", pady=(0, Dim.PAD_SM))

        self._strength_frame = ctk.CTkFrame(form, fg_color="transparent", height=6)
        self._strength_frame.pack(fill="x", pady=(0, Dim.PAD_SM))
        self._strength_frame.pack_propagate(False)
        self._strength_bar = ctk.CTkFrame(self._strength_frame, fg_color=C.danger, height=4)
        self._strength_bar.place(relx=0, rely=0, relwidth=0, relheight=1)
        self._strength_label = ctk.CTkLabel(
            form, text="", font=Fonts.TINY, text_color=C.text_dim,
        )
        self._strength_label.pack(anchor="w")
        self._password.entry.bind("<KeyRelease>", self._check_strength)

        self._confirm = PasswordEntry(form, label="Confirm Password", width=350)
        self._confirm.pack(fill="x", pady=(0, Dim.PAD_SM))

        self._terms = ctk.CTkCheckBox(
            form, text="I agree to the Terms of Service",
            font=Fonts.SMALL, text_color=C.text_secondary,
            fg_color=C.primary, hover_color=C.primary_hover,
            border_color=C.border, checkmark_color=C.text_on_primary,
        )
        self._terms.pack(anchor="w", pady=(0, Dim.PAD_MD))

        StyledButton(
            card, text="Register", width=350, height=40,
            command=self._do_register,
        ).pack(padx=Dim.PAD_LG, pady=(0, Dim.PAD_SM))

        self._error_label = ctk.CTkLabel(
            card, text="", font=Fonts.TINY, text_color=C.danger, wraplength=330,
        )
        self._error_label.pack(padx=Dim.PAD_LG, pady=(0, Dim.PAD_SM))

        bottom = ctk.CTkFrame(card, fg_color="transparent")
        bottom.pack(side="bottom", pady=Dim.PAD_LG)
        ctk.CTkLabel(bottom, text="Already have an account?", font=Fonts.BODY,
                     text_color=C.text_secondary).pack(side="left")
        ctk.CTkButton(
            bottom, text="Sign In", font=Fonts.BODY_BOLD, fg_color="transparent",
            hover_color=C.bg_sidebar_hover, text_color=C.primary,
            command=self._switch,
        ).pack(side="left", padx=(4, 0))

    def _check_strength(self, _=None):
        pw = self._password.get_value()
        score = 0
        if len(pw) >= 8:
            score += 1
        if any(c.isupper() for c in pw):
            score += 1
        if any(c.isdigit() for c in pw):
            score += 1
        if any(not c.isalnum() for c in pw):
            score += 1

        levels = {0: (0, C.danger, "Very Weak"), 1: (0.25, C.danger, "Weak"),
                  2: (0.5, C.warning, "Fair"), 3: (0.75, C.info, "Strong"),
                  4: (1.0, C.success, "Very Strong")}
        width, color, text = levels.get(score, (0, C.danger, "Very Weak"))
        self._strength_bar.place(relx=0, rely=0, relwidth=width, relheight=1)
        self._strength_bar.configure(fg_color=color)
        self._strength_label.configure(text=text, text_color=color)

    def _do_register(self):
        u = self._username.get_value()
        f = self._fullname.get_value()
        e = self._email.get_value()
        r = self._role.get_value()
        p = self._password.get_value()
        c = self._confirm.get_value()

        if not all([u, f, e, p]):
            self._error_label.configure(text="All fields are required")
            return
        if p != c:
            self._error_label.configure(text="Passwords do not match")
            return
        if not self._terms.get():
            self._error_label.configure(text="You must agree to the terms")
            return
        self._error_label.configure(text="")
        if self._on_register:
            self._on_register(u, f, e, r, p)

    def _switch(self):
        if self._on_switch_login:
            self._on_switch_login()
