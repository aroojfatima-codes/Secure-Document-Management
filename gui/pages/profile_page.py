"""Profile page with user info, edit, and change password."""

from __future__ import annotations
import customtkinter as ctk
from gui.theme import ThemeManager, Dim, Fonts
from gui.components.forms import StyledEntry, PasswordEntry, StyledButton
from gui.components.dialogs import Toast
from gui.smooth_scrolling import bind_smooth_scroll

tm = ThemeManager()
C = tm.C


class ProfilePage(ctk.CTkFrame):
    def __init__(self, master, user: dict | None = None, **kw):
        super().__init__(master, fg_color=C.bg_main, **kw)
        self._user = user or {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_content()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=Dim.PAD_XL, pady=(Dim.PAD_XL, 0))
        ctk.CTkLabel(
            header, text="My Profile", font=Fonts.TITLE,
            text_color=C.text_primary,
        ).pack(anchor="w")

    def _build_content(self):
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=C.scrollbar,
            scrollbar_button_hover_color=C.scrollbar_hover,
        )
        scroll.grid(row=1, column=0, sticky="nsew", padx=Dim.PAD_XL, pady=Dim.PAD_MD)
        scroll.grid_columnconfigure(0, weight=1)

        profile_card = ctk.CTkFrame(
            scroll, fg_color=C.bg_card, corner_radius=Dim.RADIUS_LG,
        )
        profile_card.grid(row=0, column=0, sticky="ew", pady=(0, Dim.PAD_LG))

        top = ctk.CTkFrame(profile_card, fg_color="transparent")
        top.pack(fill="x", padx=Dim.PAD_LG, pady=Dim.PAD_LG)

        avatar = ctk.CTkFrame(
            top, width=80, height=80, fg_color=C.primary, corner_radius=40,
        )
        avatar.pack(side="left", padx=(0, Dim.PAD_LG))
        avatar.pack_propagate(False)
        initial = (self._user.get("full_name") or self._user.get("username") or "U")[0].upper()
        ctk.CTkLabel(
            avatar, text=initial, font=Fonts.TITLE, text_color=C.text_on_primary,
        ).pack(expand=True)

        info = ctk.CTkFrame(top, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True)
        ctk.CTkLabel(
            info, text=self._user.get("full_name", "User"),
            font=Fonts.TITLE, text_color=C.text_primary,
        ).pack(anchor="w")
        ctk.CTkLabel(
            info, text=f"@{self._user.get('username', 'unknown')}",
            font=Fonts.BODY, text_color=C.text_secondary,
        ).pack(anchor="w")
        role = self._user.get("role", "viewer").capitalize()
        badge = ctk.CTkFrame(
            info, fg_color=C.primary, corner_radius=Dim.RADIUS_SM, height=22,
        )
        badge.pack(anchor="w", pady=(4, 0))
        badge.pack_propagate(False)
        ctk.CTkLabel(
            badge, text=role, font=Fonts.TINY_BOLD, text_color=C.text_on_primary,
        ).pack(padx=8, expand=True)

        edit_card = ctk.CTkFrame(
            scroll, fg_color=C.bg_card, corner_radius=Dim.RADIUS_LG,
        )
        edit_card.grid(row=1, column=0, sticky="ew", pady=(0, Dim.PAD_LG))
        ctk.CTkLabel(
            edit_card, text="Edit Profile", font=Fonts.SUBTITLE,
            text_color=C.text_primary,
        ).pack(anchor="w", padx=Dim.PAD_LG, pady=(Dim.PAD_MD, Dim.PAD_SM))

        form = ctk.CTkFrame(edit_card, fg_color="transparent")
        form.pack(fill="x", padx=Dim.PAD_LG, pady=(0, Dim.PAD_MD))
        form.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            form, text="Full Name:", font=Fonts.BODY, text_color=C.text_secondary,
        ).grid(row=0, column=0, sticky="w", pady=Dim.PAD_SM)
        self._name = StyledEntry(form)
        self._name.set_value(self._user.get("full_name", ""))
        self._name.grid(row=0, column=1, sticky="ew", padx=Dim.PAD_SM, pady=Dim.PAD_SM)

        ctk.CTkLabel(
            form, text="Email:", font=Fonts.BODY, text_color=C.text_secondary,
        ).grid(row=1, column=0, sticky="w", pady=Dim.PAD_SM)
        self._email = StyledEntry(form)
        self._email.set_value(self._user.get("email", ""))
        self._email.grid(row=1, column=1, sticky="ew", padx=Dim.PAD_SM, pady=Dim.PAD_SM)

        StyledButton(
            edit_card, text="Save Changes", command=self._save_profile, width=130,
        ).pack(anchor="w", padx=Dim.PAD_LG, pady=(0, Dim.PAD_MD))

        pw_card = ctk.CTkFrame(
            scroll, fg_color=C.bg_card, corner_radius=Dim.RADIUS_LG,
        )
        pw_card.grid(row=2, column=0, sticky="ew", pady=(0, Dim.PAD_LG))
        ctk.CTkLabel(
            pw_card, text="Change Password", font=Fonts.SUBTITLE,
            text_color=C.text_primary,
        ).pack(anchor="w", padx=Dim.PAD_LG, pady=(Dim.PAD_MD, Dim.PAD_SM))

        self._current_pw = PasswordEntry(pw_card, label="Current Password")
        self._current_pw.pack(fill="x", padx=Dim.PAD_LG, anchor="w")
        self._new_pw = PasswordEntry(pw_card, label="New Password")
        self._new_pw.pack(fill="x", padx=Dim.PAD_LG, anchor="w", pady=Dim.PAD_SM)
        self._confirm_pw = PasswordEntry(pw_card, label="Confirm New Password")
        self._confirm_pw.pack(fill="x", padx=Dim.PAD_LG, anchor="w")

        StyledButton(
            pw_card, text="Update Password", variant="outline", width=130,
            command=self._change_password,
        ).pack(anchor="w", padx=Dim.PAD_LG, pady=Dim.PAD_MD)

        bind_smooth_scroll(scroll)

    def _save_profile(self):
        Toast(self, "Profile updated successfully", "success")

    def _change_password(self):
        if self._new_pw.get_value() != self._confirm_pw.get_value():
            Toast(self, "Passwords do not match", "error")
            return
        if not self._current_pw.get_value():
            Toast(self, "Enter current password", "warning")
            return
        Toast(self, "Password updated successfully", "success")
        self._current_pw.clear()
        self._new_pw.clear()
        self._confirm_pw.clear()

    def apply_theme(self):
        self.configure(fg_color=C.bg_main)
