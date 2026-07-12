"""Login page with glassmorphism card and animated background."""

from __future__ import annotations
import math
import customtkinter as ctk
from gui.theme import ThemeManager, Dim, Fonts
from gui.components.forms import StyledEntry, PasswordEntry, StyledButton
from gui.components.dialogs import Toast

tm = ThemeManager()
C = tm.C


class LoginPage(ctk.CTkFrame):
    def __init__(self, master, on_login=None, on_switch_register=None, on_face_login=None, **kw):
        super().__init__(master, fg_color=C.bg_main, **kw)
        self._on_login = on_login
        self._on_switch_register = on_switch_register
        self._on_face_login = on_face_login

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        center = ctk.CTkFrame(self, fg_color="transparent")
        center.grid(row=0, column=0)
        center.grid_columnconfigure(0, weight=1)

        self._build_bg_animation(center)
        card = self._build_card(center)
        card.grid(row=0, column=0, padx=Dim.PAD_XL, pady=Dim.PAD_XL)

    # ------------------------------------------------------------------
    # Animated background
    # ------------------------------------------------------------------
    def _build_bg_animation(self, parent):
        bg = ctk.CTkFrame(parent, fg_color=C.bg_main)
        bg.place(relx=0, rely=0, relwidth=1, relheight=1)
        bg.lower()
        self._bg_canvas = ctk.CTkCanvas(
            bg, bg=C.bg_main, highlightthickness=0, width=900, height=700,
        )
        self._bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        # (start_x, start_y, speed_x, speed_y) per orb
        self._orbs = [
            {"x": 120, "y": 100, "vx": 0.7, "vy": 0.4, "r": 60},
            {"x": 700, "y": 500, "vx": -0.5, "vy": 0.6, "r": 80},
            {"x": 400, "y": 200, "vx": 0.3, "vy": -0.55, "r": 100},
        ]
        self._tick = 0
        self._animate_bg()

    def _animate_bg(self):
        canvas_w = max(self._bg_canvas.winfo_width(), 900)
        canvas_h = max(self._bg_canvas.winfo_height(), 700)

        for orb in self._orbs:
            orb["x"] += orb["vx"]
            orb["y"] += orb["vy"]

            if orb["x"] - orb["r"] < 0 or orb["x"] + orb["r"] > canvas_w:
                orb["vx"] = -orb["vx"]
                orb["x"] = max(orb["r"], min(orb["x"], canvas_w - orb["r"]))
            if orb["y"] - orb["r"] < 0 or orb["y"] + orb["r"] > canvas_h:
                orb["vy"] = -orb["vy"]
                orb["y"] = max(orb["r"], min(orb["y"], canvas_h - orb["r"]))

        self._tick += 1
        self._draw_orbs()
        self.after(50, self._animate_bg)

    def _draw_orbs(self):
        self._bg_canvas.delete("all")
        colors = [C.primary_dark, C.accent_blue, C.accent_purple]
        for i, orb in enumerate(self._orbs):
            x, y, r = orb["x"], orb["y"], orb["r"]
            pulse = r + 5 * math.sin(self._tick * 0.08 + i * 2)
            self._bg_canvas.create_oval(
                x - pulse, y - pulse, x + pulse, y + pulse,
                fill=colors[i % len(colors)], outline="", width=0,
            )

    # ------------------------------------------------------------------
    # Card
    # ------------------------------------------------------------------
    def _build_card(self, parent) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            parent, fg_color=C.bg_card_translucent, corner_radius=Dim.RADIUS_XL,
            border_width=1, border_color=C.border_light,
            width=400, height=620,
        )
        card.pack_propagate(False)

        ctk.CTkLabel(
            card, text="\uD83D\uDD12", font=(Fonts.F, 40),
            text_color=C.primary,
        ).pack(pady=(Dim.PAD_XL, Dim.PAD_SM))

        ctk.CTkLabel(
            card, text="Secure Document Manager",
            font=Fonts.TITLE, text_color=C.text_primary,
        ).pack(pady=(0, 4))

        ctk.CTkLabel(
            card, text="Sign in to your account",
            font=Fonts.BODY, text_color=C.text_secondary,
        ).pack(pady=(0, Dim.PAD_LG))

        self._username = StyledEntry(
            card, label="Username", placeholder="Enter your username", width=320,
        )
        self._username.pack(padx=Dim.PAD_LG, pady=(0, Dim.PAD_MD))

        self._password = PasswordEntry(card, label="Password", width=320)
        self._password.pack(padx=Dim.PAD_LG, pady=(0, Dim.PAD_MD))

        remember_frame = ctk.CTkFrame(card, fg_color="transparent")
        remember_frame.pack(fill="x", padx=Dim.PAD_LG, pady=(0, Dim.PAD_MD))
        self._remember = ctk.CTkCheckBox(
            remember_frame, text="Remember me", font=Fonts.SMALL,
            text_color=C.text_secondary, fg_color=C.primary,
            hover_color=C.primary_hover, border_color=C.border,
            checkmark_color=C.text_on_primary,
        )
        self._remember.pack(side="left")
        ctk.CTkButton(
            remember_frame, text="Forgot password?", font=Fonts.SMALL_BOLD,
            fg_color="transparent", hover_color=C.bg_sidebar_hover,
            text_color=C.primary, command=self._forgot,
        ).pack(side="right")

        StyledButton(
            card, text="Sign In", width=320, height=40,
            command=self._do_login,
        ).pack(padx=Dim.PAD_LG, pady=(0, Dim.PAD_MD))

        self._error_label = ctk.CTkLabel(
            card, text="", font=Fonts.TINY,
            text_color=C.danger, wraplength=300,
        )
        self._error_label.pack(padx=Dim.PAD_LG, pady=(0, Dim.PAD_SM))

        divider = ctk.CTkFrame(card, fg_color=C.border_light, height=1)
        divider.pack(fill="x", padx=Dim.PAD_LG, pady=(Dim.PAD_MD, Dim.PAD_MD))

        ctk.CTkLabel(
            card, text="or continue with", font=Fonts.SMALL,
            text_color=C.text_secondary,
        ).pack(pady=(0, Dim.PAD_MD))

        StyledButton(
            card, text="Login with Face Recognition", width=320, height=40,
            fg_color=C.accent_purple, hover_color=C.accent_purple,
            command=self._on_face_login_click,
        ).pack(padx=Dim.PAD_LG, pady=(0, Dim.PAD_MD))

        bottom = ctk.CTkFrame(card, fg_color="transparent")
        bottom.pack(side="bottom", pady=Dim.PAD_LG)
        ctk.CTkLabel(
            bottom, text="Don't have an account?", font=Fonts.BODY,
            text_color=C.text_secondary,
        ).pack(side="left")
        ctk.CTkButton(
            bottom, text="Register", font=Fonts.BODY_BOLD,
            fg_color="transparent", hover_color=C.bg_sidebar_hover,
            text_color=C.primary, command=self._switch,
        ).pack(side="left", padx=(4, 0))

        return card

    # ------------------------------------------------------------------
    # Callbacks
    # ------------------------------------------------------------------
    def _do_login(self):
        u = self._username.get_value()
        p = self._password.get_value()
        if not u or not p:
            self._error_label.configure(text="Please enter username and password")
            return
        self._error_label.configure(text="")
        if self._on_login:
            self._on_login(u, p)

    def _on_face_login_click(self):
        if self._on_face_login:
            self._on_face_login()

    def _switch(self):
        if self._on_switch_register:
            self._on_switch_register()

    def _forgot(self):
        Toast(self, "Contact admin to reset password.", "info")

    def apply_theme(self):
        self.configure(fg_color=C.bg_main)
        for w in self.winfo_children():
            if hasattr(w, "configure"):
                try:
                    w.configure(fg_color=C.bg_main)
                except Exception:
                    pass
