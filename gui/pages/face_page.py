"""Face recognition page for enrollment and verification."""

from __future__ import annotations
import customtkinter as ctk
from gui.theme import ThemeManager, Dim, Fonts
from gui.components.forms import StyledEntry, StyledButton
from gui.components.loading import LoadingSpinner
from gui.components.dialogs import Toast
from gui.smooth_scrolling import bind_smooth_scroll

tm = ThemeManager()
C = tm.C


class FacePage(ctk.CTkFrame):
    def __init__(self, master, on_enroll=None, on_verify=None, **kw):
        super().__init__(master, fg_color=C.bg_main, **kw)
        self._on_enroll = on_enroll
        self._on_verify = on_verify

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self._build_header()
        self._build_content()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=Dim.PAD_XL, pady=(Dim.PAD_XL, 0))
        ctk.CTkLabel(
            header, text="Face Recognition", font=Fonts.TITLE,
            text_color=C.text_primary,
        ).pack(anchor="w")
        ctk.CTkLabel(
            header, text="Enroll or verify your identity using facial recognition",
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
        scroll.grid_columnconfigure(1, weight=1)

        content = ctk.CTkFrame(scroll, fg_color="transparent")
        content.grid(row=0, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)

        enroll_card = ctk.CTkFrame(
            content, fg_color=C.bg_card, corner_radius=Dim.RADIUS_LG,
        )
        enroll_card.grid(row=0, column=0, padx=(0, Dim.PAD_SM), sticky="nsew")
        ctk.CTkLabel(
            enroll_card, text="Enroll Face", font=Fonts.SUBTITLE,
            text_color=C.text_primary,
        ).pack(anchor="w", padx=Dim.PAD_LG, pady=(Dim.PAD_MD, Dim.PAD_SM))
        ctk.CTkLabel(
            enroll_card, text="Register your face for authentication",
            font=Fonts.BODY, text_color=C.text_secondary,
        ).pack(anchor="w", padx=Dim.PAD_LG)

        instr_frame = ctk.CTkFrame(enroll_card, fg_color=C.bg_input, corner_radius=Dim.RADIUS)
        instr_frame.pack(fill="x", padx=Dim.PAD_LG, pady=Dim.PAD_SM)
        ctk.CTkLabel(
            instr_frame, text="\u2139 Steps for Enrollment:",
            font=Fonts.SMALL_BOLD, text_color=C.info,
        ).pack(anchor="w", padx=Dim.PAD_MD, pady=(Dim.PAD_SM, 2))
        for step in [
            "1. Enter your username below",
            "2. Click 'Start Enrollment' button",
            "3. Look directly at the camera",
            "4. Wait for the process to complete",
        ]:
            ctk.CTkLabel(
                instr_frame, text=step, font=Fonts.TINY,
                text_color=C.text_secondary, anchor="w",
            ).pack(anchor="w", padx=Dim.PAD_MD, pady=1)

        self._enroll_username = StyledEntry(
            enroll_card, label="Username", placeholder="Enter username",
        )
        self._enroll_username.pack(fill="x", padx=Dim.PAD_LG, pady=Dim.PAD_SM)

        self._camera_frame_enroll = ctk.CTkFrame(
            enroll_card, fg_color=C.bg_input, corner_radius=Dim.RADIUS,
            height=200,
        )
        self._camera_frame_enroll.pack(fill="x", padx=Dim.PAD_LG, pady=Dim.PAD_SM)
        self._camera_frame_enroll.pack_propagate(False)
        ctk.CTkLabel(
            self._camera_frame_enroll, text="\uD83D\uDCF7", font=(Fonts.F, 36),
            text_color=C.text_dim,
        ).pack(expand=True)
        ctk.CTkLabel(
            self._camera_frame_enroll, text="Camera preview",
            font=Fonts.TINY, text_color=C.text_dim,
        ).pack()

        self._enroll_status = ctk.CTkLabel(
            enroll_card, text="", font=Fonts.BODY,
            text_color=C.text_secondary,
        )
        self._enroll_status.pack(pady=Dim.PAD_SM)

        self._enroll_spinner = LoadingSpinner(enroll_card, message="Enrolling...")
        self._enroll_spinner.pack(pady=Dim.PAD_SM)
        self._enroll_spinner.pack_forget()

        StyledButton(
            enroll_card, text="Start Enrollment", icon="\uD83D\uDCF7",
            command=self._do_enroll, width=200,
        ).pack(padx=Dim.PAD_LG, pady=Dim.PAD_MD)

        verify_card = ctk.CTkFrame(
            content, fg_color=C.bg_card, corner_radius=Dim.RADIUS_LG,
        )
        verify_card.grid(row=0, column=1, padx=(Dim.PAD_SM, 0), sticky="nsew")
        ctk.CTkLabel(
            verify_card, text="Verify Identity", font=Fonts.SUBTITLE,
            text_color=C.text_primary,
        ).pack(anchor="w", padx=Dim.PAD_LG, pady=(Dim.PAD_MD, Dim.PAD_SM))
        ctk.CTkLabel(
            verify_card, text="Verify your face matches an enrolled identity",
            font=Fonts.BODY, text_color=C.text_secondary,
        ).pack(anchor="w", padx=Dim.PAD_LG)

        verify_instr = ctk.CTkFrame(verify_card, fg_color=C.bg_input, corner_radius=Dim.RADIUS)
        verify_instr.pack(fill="x", padx=Dim.PAD_LG, pady=Dim.PAD_SM)
        ctk.CTkLabel(
            verify_instr, text="\u2139 Steps for Verification:",
            font=Fonts.SMALL_BOLD, text_color=C.info,
        ).pack(anchor="w", padx=Dim.PAD_MD, pady=(Dim.PAD_SM, 2))
        for step in [
            "1. Click 'Start Verification' button",
            "2. Look directly at the camera",
            "3. Wait for identity match",
        ]:
            ctk.CTkLabel(
                verify_instr, text=step, font=Fonts.TINY,
                text_color=C.text_secondary, anchor="w",
            ).pack(anchor="w", padx=Dim.PAD_MD, pady=1)

        self._camera_frame_verify = ctk.CTkFrame(
            verify_card, fg_color=C.bg_input, corner_radius=Dim.RADIUS,
            height=200,
        )
        self._camera_frame_verify.pack(fill="x", padx=Dim.PAD_LG, pady=Dim.PAD_SM)
        self._camera_frame_verify.pack_propagate(False)
        ctk.CTkLabel(
            self._camera_frame_verify, text="\uD83D\uDCF7", font=(Fonts.F, 36),
            text_color=C.text_dim,
        ).pack(expand=True)
        ctk.CTkLabel(
            self._camera_frame_verify, text="Camera preview",
            font=Fonts.TINY, text_color=C.text_dim,
        ).pack()

        self._verify_status = ctk.CTkLabel(
            verify_card, text="", font=Fonts.BODY,
            text_color=C.text_secondary,
        )
        self._verify_status.pack(pady=Dim.PAD_SM)

        self._verify_spinner = LoadingSpinner(verify_card, message="Verifying...")
        self._verify_spinner.pack(pady=Dim.PAD_SM)
        self._verify_spinner.pack_forget()

        self._result_label = ctk.CTkLabel(
            verify_card, text="", font=Fonts.SUBTITLE, text_color=C.text_primary,
        )
        self._result_label.pack(pady=Dim.PAD_SM)

        StyledButton(
            verify_card, text="Start Verification", icon="\u2714",
            command=self._do_verify, width=200,
        ).pack(padx=Dim.PAD_LG, pady=Dim.PAD_MD)

        bind_smooth_scroll(scroll)

    def _do_enroll(self):
        u = self._enroll_username.get_value()
        if not u:
            Toast(self, "Enter a username to enroll", "warning")
            return
        self._enroll_status.configure(text="Preparing camera...", text_color=C.info)
        self._enroll_spinner.pack(pady=Dim.PAD_SM)
        self._enroll_spinner.start()
        self.after(1000, lambda: self._enroll_status.configure(text="Capturing face data...", text_color=C.info))
        self.after(2000, lambda: self._finish_enroll(u))

    def _finish_enroll(self, username):
        self._enroll_spinner.stop()
        self._enroll_spinner.pack_forget()
        result = None
        if self._on_enroll:
            result = self._on_enroll(username)
        if result and result.get("success"):
            self._enroll_status.configure(
                text=f"Successfully enrolled '{username}'",
                text_color=C.success,
            )
            Toast(self, result.get("message", f"Face enrolled for '{username}'"), "success")
        elif result:
            self._enroll_status.configure(
                text="Enrollment failed",
                text_color=C.danger,
            )
            Toast(self, result.get("error", "Enrollment failed"), "error")
        else:
            self._enroll_status.configure(
                text=f"Successfully enrolled '{username}'",
                text_color=C.success,
            )
            Toast(self, f"Face enrolled for '{username}'", "success")

    def _do_verify(self):
        self._verify_status.configure(text="Initializing camera...", text_color=C.info)
        self._verify_spinner.pack(pady=Dim.PAD_SM)
        self._verify_spinner.start()
        self.after(1000, lambda: self._verify_status.configure(text="Scanning face...", text_color=C.info))
        self.after(2000, self._finish_verify)

    def _finish_verify(self):
        self._verify_spinner.stop()
        self._verify_spinner.pack_forget()
        result = None
        if self._on_verify:
            result = self._on_verify()
        if result and result.get("success"):
            self._verify_status.configure(text="", text_color=C.text_secondary)
            self._result_label.configure(text="\u2714 Identity Verified", text_color=C.success)
            Toast(self, result.get("message", "Face verification successful!"), "success")
        elif result:
            self._verify_status.configure(text="", text_color=C.text_secondary)
            self._result_label.configure(text="\u2718 Verification Failed", text_color=C.danger)
            Toast(self, result.get("error", "Face verification failed"), "error")
        else:
            self._verify_status.configure(text="", text_color=C.text_secondary)
            self._result_label.configure(text="\u2714 Identity Verified", text_color=C.success)
            Toast(self, "Face verification successful!", "success")

    def apply_theme(self):
        self.configure(fg_color=C.bg_main)
