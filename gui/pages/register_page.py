"""Registration page with multi-field form, password strength meter."""

from __future__ import annotations
import customtkinter as ctk
from gui.theme import ThemeManager, Dim, Fonts
from gui.components.forms import StyledEntry, PasswordEntry, StyledComboBox, StyledButton
from gui.components.dialogs import Toast
from gui.smooth_scrolling import bind_smooth_scroll

tm = ThemeManager()
C = tm.C


class RegisterPage(ctk.CTkFrame):
    def __init__(self, master, on_register=None, on_switch_login=None, **kw):
        super().__init__(master, fg_color=C.bg_main, **kw)
        self._on_register = on_register
        self._on_switch_login = on_switch_login

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=C.scrollbar,
            scrollbar_button_hover_color=C.scrollbar_hover,
        )
        scroll.grid(row=0, column=0, sticky="nsew", padx=Dim.PAD_XL, pady=Dim.PAD_MD)
        scroll.grid_columnconfigure(0, weight=1)
        scroll.grid_rowconfigure(0, weight=1)

        center = ctk.CTkFrame(scroll, fg_color="transparent")
        center.grid(row=0, column=0)
        center.grid_columnconfigure(0, weight=1)

        card = ctk.CTkFrame(
            center, fg_color=C.bg_card_translucent, corner_radius=Dim.RADIUS_XL,
            border_width=1, border_color=C.border_light,
        )
        card.grid(row=0, column=0, padx=Dim.PAD_XL, pady=Dim.PAD_XL, sticky="nsew")
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card, text="Create Account", font=Fonts.TITLE,
            text_color=C.text_primary,
        ).grid(row=0, column=0, pady=(Dim.PAD_XL, Dim.PAD_SM))
        ctk.CTkLabel(
            card, text="Fill in your details to register",
            font=Fonts.BODY, text_color=C.text_secondary,
        ).grid(row=1, column=0, pady=(0, Dim.PAD_LG))

        form = ctk.CTkFrame(card, fg_color="transparent")
        form.grid(row=2, column=0, sticky="ew", padx=Dim.PAD_XL)
        form.grid_columnconfigure(0, weight=1)

        self._username = StyledEntry(form, label="Username", placeholder="Choose a username")
        self._username.grid(row=0, column=0, sticky="ew", pady=(0, Dim.PAD_SM))

        self._fullname = StyledEntry(form, label="Full Name", placeholder="Your full name")
        self._fullname.grid(row=1, column=0, sticky="ew", pady=(0, Dim.PAD_SM))

        self._email = StyledEntry(form, label="Email", placeholder="you@example.com")
        self._email.grid(row=2, column=0, sticky="ew", pady=(0, Dim.PAD_SM))

        self._role = StyledComboBox(form, label="Role",
                                    values=["admin", "editor", "viewer"])
        self._role.grid(row=3, column=0, sticky="ew", pady=(0, Dim.PAD_SM))

        self._password = PasswordEntry(form, label="Password")
        self._password.grid(row=4, column=0, sticky="ew", pady=(0, Dim.PAD_SM))

        self._strength_frame = ctk.CTkFrame(form, fg_color="transparent", height=6)
        self._strength_frame.grid(row=5, column=0, sticky="ew", pady=(0, Dim.PAD_SM))
        self._strength_frame.pack_propagate(False)
        self._strength_bar = ctk.CTkFrame(self._strength_frame, fg_color=C.danger, height=4)
        self._strength_bar.place(relx=0, rely=0, relwidth=0, relheight=1)
        self._strength_label = ctk.CTkLabel(
            form, text="", font=Fonts.TINY, text_color=C.text_dim,
        )
        self._strength_label.grid(row=6, column=0, sticky="w")
        self._password.entry.bind("<KeyRelease>", self._check_strength)

        self._confirm = PasswordEntry(form, label="Confirm Password")
        self._confirm.grid(row=7, column=0, sticky="ew", pady=(0, Dim.PAD_SM))

        self._terms = ctk.CTkCheckBox(
            form, text="I agree to the Terms of Service",
            font=Fonts.SMALL, text_color=C.text_secondary,
            fg_color=C.primary, hover_color=C.primary_hover,
            border_color=C.border, checkmark_color=C.text_on_primary,
        )
        self._terms.grid(row=8, column=0, sticky="w", pady=(0, Dim.PAD_MD))

        StyledButton(
            card, text="Register", height=40,
            command=self._do_register,
        ).grid(row=3, column=0, sticky="ew", padx=Dim.PAD_XL, pady=(0, Dim.PAD_SM))

        self._error_label = ctk.CTkLabel(
            card, text="", font=Fonts.TINY, text_color=C.danger, wraplength=330,
        )
        self._error_label.grid(row=4, column=0, sticky="ew", padx=Dim.PAD_XL, pady=(0, Dim.PAD_SM))

        bottom = ctk.CTkFrame(card, fg_color="transparent")
        bottom.grid(row=5, column=0, pady=Dim.PAD_LG)
        ctk.CTkLabel(bottom, text="Already have an account?", font=Fonts.BODY,
                     text_color=C.text_secondary).pack(side="left")
        ctk.CTkButton(
            bottom, text="Sign In", font=Fonts.BODY_BOLD, fg_color="transparent",
            hover_color=C.bg_sidebar_hover, text_color=C.primary,
            command=self._switch,
        ).pack(side="left", padx=(4, 0))

        bind_smooth_scroll(scroll)

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

    def apply_theme(self):
        self.configure(fg_color=C.bg_main)
