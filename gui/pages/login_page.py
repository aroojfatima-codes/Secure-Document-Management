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
        kw.pop("fg_color", None)
        super().__init__(master, fg_color=C.bg_main, **kw)
        self._on_login = on_login
        self._on_switch_register = on_switch_register
        self._on_face_login = on_face_login

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        center = ctk.CTkFrame(self, fg_color="transparent")
        center.grid(row=0, column=0, sticky="nsew")
        center.grid_columnconfigure(0, weight=1)
        center.grid_rowconfigure(0, weight=1)

        self._build_bg_animation(center)

        card = self._build_card(center)
        card.grid(row=0, column=0, padx=Dim.PAD_XL, pady=Dim.PAD_XL)

    def _build_bg_animation(self, parent):
        bg = ctk.CTkFrame(parent, fg_color=C.bg_main)
        bg.place(relx=0, rely=0, relwidth=1, relheight=1)
        bg.lower()
        self._bg_canvas = ctk.CTkCanvas(
            bg, bg=C.bg_main, highlightthickness=0,
        )
        self._bg_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)

        self._orbs = [
            {"x": 120, "y": 100, "vx": 0.7, "vy": 0.4, "r": 60},
            {"x": 700, "y": 500, "vx": -0.5, "vy": 0.6, "r": 80},
            {"x": 400, "y": 200, "vx": 0.3, "vy": -0.55, "r": 100},
        ]
        self._tick = 0
        self._animating = True
        self._animate_bg()

    def _animate_bg(self):
        if not self._animating:
            return
        try:
            canvas_w = max(self._bg_canvas.winfo_width(), 400)
            canvas_h = max(self._bg_canvas.winfo_height(), 400)

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
        except Exception:
            self._animating = False

    def _draw_orbs(self):
        try:
            self._bg_canvas.delete("all")
            colors = [C.primary_dark, C.accent_blue, C.accent_purple]
            for i, orb in enumerate(self._orbs):
                x, y, r = orb["x"], orb["y"], orb["r"]
                pulse = r + 5 * math.sin(self._tick * 0.08 + i * 2)
                self._bg_canvas.create_oval(
                    x - pulse, y - pulse, x + pulse, y + pulse,
                    fill=colors[i % len(colors)], outline="", width=0,
                )
        except Exception:
            pass

    def _build_card(self, parent) -> ctk.CTkFrame:
        card = ctk.CTkFrame(
            parent, fg_color=C.bg_card_translucent, corner_radius=Dim.RADIUS_XL,
            border_width=1, border_color=C.border_light,
        )
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card, text="\uD83D\uDD12", font=(Fonts.F, 40),
            text_color=C.primary,
        ).grid(row=0, column=0, pady=(Dim.PAD_XL, Dim.PAD_SM))

        ctk.CTkLabel(
            card, text="Secure Document Manager",
            font=Fonts.TITLE, text_color=C.text_primary,
        ).grid(row=1, column=0, pady=(0, 4))

        ctk.CTkLabel(
            card, text="Sign in to your account",
            font=Fonts.BODY, text_color=C.text_secondary,
        ).grid(row=2, column=0, pady=(0, Dim.PAD_LG))

        form_frame = ctk.CTkFrame(card, fg_color="transparent")
        form_frame.grid(row=3, column=0, sticky="ew", padx=Dim.PAD_XL)
        form_frame.grid_columnconfigure(0, weight=1)

        self._username = StyledEntry(
            form_frame, label="Username", placeholder="Enter your username",
        )
        self._username.grid(row=0, column=0, sticky="ew", pady=(0, Dim.PAD_MD))

        self._password = PasswordEntry(form_frame, label="Password")
        self._password.grid(row=1, column=0, sticky="ew", pady=(0, Dim.PAD_MD))

        remember_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        remember_frame.grid(row=2, column=0, sticky="ew", pady=(0, Dim.PAD_MD))
        remember_frame.grid_columnconfigure(0, weight=1)
        self._remember = ctk.CTkCheckBox(
            remember_frame, text="Remember me", font=Fonts.SMALL,
            text_color=C.text_secondary, fg_color=C.primary,
            hover_color=C.primary_hover, border_color=C.border,
            checkmark_color=C.text_on_primary,
        )
        self._remember.grid(row=0, column=0, sticky="w")
        ctk.CTkButton(
            remember_frame, text="Forgot password?", font=Fonts.SMALL_BOLD,
            fg_color="transparent", hover_color=C.bg_sidebar_hover,
            text_color=C.primary, command=self._forgot,
        ).grid(row=0, column=1, sticky="e")

        StyledButton(
            form_frame, text="Sign In", height=40,
            command=self._do_login,
        ).grid(row=3, column=0, sticky="ew", pady=(0, Dim.PAD_MD))

        self._error_label = ctk.CTkLabel(
            form_frame, text="", font=Fonts.TINY,
            text_color=C.danger, wraplength=300,
        )
        self._error_label.grid(row=4, column=0, sticky="ew", pady=(0, Dim.PAD_SM))

        divider = ctk.CTkFrame(card, fg_color=C.border_light, height=1)
        divider.grid(row=4, column=0, sticky="ew", padx=Dim.PAD_XL, pady=(Dim.PAD_MD, Dim.PAD_MD))

        ctk.CTkLabel(
            card, text="or continue with", font=Fonts.SMALL,
            text_color=C.text_secondary,
        ).grid(row=5, column=0, pady=(0, Dim.PAD_MD))

        StyledButton(
            card, text="Login with Face Recognition", height=40,
            fg_color=C.accent_purple, hover_color=C.primary_dark,
            command=self._on_face_login_click,
        ).grid(row=6, column=0, sticky="ew", padx=Dim.PAD_XL, pady=(0, Dim.PAD_MD))

        bottom = ctk.CTkFrame(card, fg_color="transparent")
        bottom.grid(row=7, column=0, pady=Dim.PAD_LG)
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

    def _do_login(self):
        u = self._username.get_value()
        p = self._password.get_value()
        if not u or not p:
            self._error_label.configure(text="Please enter username and password")
            return
        self._error_label.configure(text="")
        if self._on_login:
            try:
                self._on_login(u, p)
            except Exception as e:
                Toast(self, f"Login error: {e}", "error")

    def _on_face_login_click(self):
        if self._on_face_login:
            try:
                self._on_face_login()
            except Exception as e:
                Toast(self, f"Face login error: {e}", "error")

    def _switch(self):
        if self._on_switch_register:
            try:
                self._on_switch_register()
            except Exception:
                pass

    def _forgot(self):
        Toast(self, "Contact admin to reset password.", "info")

    def destroy(self):
        self._animating = False
        super().destroy()

    def apply_theme(self):
        self.configure(fg_color=C.bg_main)
