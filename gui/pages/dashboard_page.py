"""Dashboard page with stat cards, charts, activity feed, system status."""

from __future__ import annotations
import customtkinter as ctk
from gui.theme import ThemeManager, Dim, Fonts
from gui.components.cards import StatCard, ActionCard
from gui.components.charts import DonutChart, BarChart
from gui.smooth_scrolling import bind_smooth_scroll

tm = ThemeManager()
C = tm.C


class DashboardPage(ctk.CTkFrame):
    def __init__(self, master, user: dict | None = None, on_navigate=None, **kw):
        kw.pop("fg_color", None)
        super().__init__(master, fg_color=C.bg_main, **kw)
        self._user = user or {}
        self._role = self._user.get("role", "viewer").lower()
        self._can_upload = self._role in ("admin", "editor")
        self._can_share = self._role in ("admin", "editor")
        self._on_navigate = on_navigate

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._build_header()
        self._build_content()

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=Dim.PAD_XL, pady=(Dim.PAD_XL, 0))
        header.grid_columnconfigure(1, weight=1)

        welcome = self._user.get("full_name", self._user.get("username", "User"))
        ctk.CTkLabel(
            header, text=f"Welcome back, {welcome}",
            font=Fonts.TITLE, text_color=C.text_primary,
        ).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(
            header, text="Here's an overview of your document system",
            font=Fonts.BODY, text_color=C.text_secondary,
        ).grid(row=1, column=0, sticky="w", pady=(2, 0))

    def _build_content(self):
        scroll = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=C.scrollbar,
            scrollbar_button_hover_color=C.scrollbar_hover,
        )
        scroll.grid(row=1, column=0, sticky="nsew", padx=Dim.PAD_XL, pady=Dim.PAD_MD)
        scroll.grid_columnconfigure(0, weight=1)
        scroll.grid_columnconfigure(1, weight=1)

        stats_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        stats_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, Dim.PAD_LG))
        for i in range(4):
            stats_frame.grid_columnconfigure(i, weight=1)

        stat_data = [
            ("\uD83D\uDCC2", "Total Documents", "128", "+12%", C.primary),
            ("\uD83D\uDCC1", "Shared Files", "45", "+5%", C.info),
            ("\uD83D\uDEE1\uFE0F", "Active Users", "23", "+2", C.success),
            ("\u26A0\uFE0F", "Pending Reviews", "8", "-3", C.warning),
        ]
        for i, (icon, title, value, trend, color) in enumerate(stat_data):
            card = StatCard(
                stats_frame, title=f"{title} ({trend})", value=value,
                icon=icon, accent=color, width=190, height=90,
            )
            card.grid(row=0, column=i, padx=Dim.PAD_SM, sticky="ew")

        charts_row = ctk.CTkFrame(scroll, fg_color="transparent")
        charts_row.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, Dim.PAD_LG))
        charts_row.grid_columnconfigure(0, weight=1)
        charts_row.grid_columnconfigure(1, weight=1)

        pie_frame = ctk.CTkFrame(
            charts_row, fg_color=C.bg_card, corner_radius=Dim.RADIUS_LG,
        )
        pie_frame.grid(row=0, column=0, padx=(0, Dim.PAD_SM), sticky="nsew")
        ctk.CTkLabel(
            pie_frame, text="Documents by Type", font=Fonts.SUBTITLE,
            text_color=C.text_primary,
        ).pack(anchor="w", padx=Dim.PAD_MD, pady=(Dim.PAD_MD, 0))
        donut = DonutChart(pie_frame, size=160)
        donut.pack(padx=Dim.PAD_MD, pady=Dim.PAD_SM)
        donut.draw([
            ("PDF", 42, C.primary),
            ("Word", 28, C.info),
            ("Images", 18, C.warning),
            ("Other", 12, C.success),
        ])

        bar_frame = ctk.CTkFrame(
            charts_row, fg_color=C.bg_card, corner_radius=Dim.RADIUS_LG,
        )
        bar_frame.grid(row=0, column=1, padx=(Dim.PAD_SM, 0), sticky="nsew")
        ctk.CTkLabel(
            bar_frame, text="Monthly Uploads", font=Fonts.SUBTITLE,
            text_color=C.text_primary,
        ).pack(anchor="w", padx=Dim.PAD_MD, pady=(Dim.PAD_MD, 0))
        bar = BarChart(bar_frame, width=280)
        bar.pack(padx=Dim.PAD_MD, pady=Dim.PAD_SM)
        bar.draw([
            ("Jan", 15, C.primary), ("Feb", 22, C.primary),
            ("Mar", 31, C.primary), ("Apr", 18, C.primary),
            ("May", 27, C.info), ("Jun", 35, C.info),
        ])

        bottom_row = ctk.CTkFrame(scroll, fg_color="transparent")
        bottom_row.grid(row=2, column=0, columnspan=2, sticky="ew")
        bottom_row.grid_columnconfigure(0, weight=1)
        bottom_row.grid_columnconfigure(1, weight=1)

        quick_actions_frame = ctk.CTkFrame(
            bottom_row, fg_color=C.bg_card, corner_radius=Dim.RADIUS_LG,
        )
        quick_actions_frame.grid(row=0, column=0, padx=(0, Dim.PAD_SM), sticky="nsew")
        ctk.CTkLabel(
            quick_actions_frame, text="Quick Actions", font=Fonts.SUBTITLE,
            text_color=C.text_primary,
        ).pack(anchor="w", padx=Dim.PAD_MD, pady=(Dim.PAD_MD, 0))

        actions_data = []
        if self._can_upload:
            actions_data.append(("\u2B06", "Upload Document", "Encrypt & store files", C.primary, "upload"))
        actions_data.append(("\u25A3", "View Documents", "Browse your library", C.info, "documents"))
        actions_data.append(("\uD83D\uDD0D", "Search", "Find documents quickly", C.warning, "search"))
        if self._can_share:
            actions_data.append(("\uD83D\uDD17", "Share Files", "Share with team members", C.success, "share"))
        for icon, title, desc, color, page_name in actions_data:
            nav = self._on_navigate
            action = ActionCard(
                quick_actions_frame, title=title, icon=icon,
                description=desc, accent=color, height=60,
                command=lambda p=page_name: nav and nav(p),
            )
            action.pack(fill="x", padx=Dim.PAD_MD, pady=3)

        right_col = ctk.CTkFrame(bottom_row, fg_color="transparent")
        right_col.grid(row=0, column=1, padx=(Dim.PAD_SM, 0), sticky="nsew")
        right_col.grid_rowconfigure(0, weight=1)
        right_col.grid_rowconfigure(1, weight=1)
        right_col.grid_columnconfigure(0, weight=1)

        activity_frame = ctk.CTkFrame(
            right_col, fg_color=C.bg_card, corner_radius=Dim.RADIUS_LG,
        )
        activity_frame.grid(row=0, column=0, sticky="nsew", pady=(0, Dim.PAD_SM))
        ctk.CTkLabel(
            activity_frame, text="Recent Activity", font=Fonts.SUBTITLE,
            text_color=C.text_primary,
        ).pack(anchor="w", padx=Dim.PAD_MD, pady=(Dim.PAD_MD, 0))

        activity_items = [
            ("doc_v2.pdf uploaded", "2 min ago", C.primary),
            ("report.docx shared with Team", "15 min ago", C.info),
            ("photo.png downloaded", "1 hour ago", C.warning),
            ("audit log exported", "3 hours ago", C.success),
        ]
        for text, time_str, color in activity_items:
            item = ctk.CTkFrame(activity_frame, fg_color="transparent")
            item.pack(fill="x", padx=Dim.PAD_MD, pady=4)
            ctk.CTkLabel(
                item, text="\u25CF", font=Fonts.TINY, text_color=color, width=12,
            ).pack(side="left")
            ctk.CTkLabel(
                item, text=text, font=Fonts.BODY, text_color=C.text_primary,
            ).pack(side="left", padx=(4, 0))
            ctk.CTkLabel(
                item, text=time_str, font=Fonts.TINY, text_color=C.text_dim,
            ).pack(side="right")

        system_frame = ctk.CTkFrame(
            right_col, fg_color=C.bg_card, corner_radius=Dim.RADIUS_LG,
        )
        system_frame.grid(row=1, column=0, sticky="nsew")
        ctk.CTkLabel(
            system_frame, text="System Status", font=Fonts.SUBTITLE,
            text_color=C.text_primary,
        ).pack(anchor="w", padx=Dim.PAD_MD, pady=(Dim.PAD_MD, 0))

        status_items = [
            ("Database", "Online", C.success),
            ("Face Recognition", "Active", C.success),
            ("Encryption Engine", "Running", C.success),
            ("Backup Service", "Scheduled", C.info),
            ("Storage", "78% Used", C.warning),
        ]
        for label, status, color in status_items:
            item = ctk.CTkFrame(system_frame, fg_color="transparent")
            item.pack(fill="x", padx=Dim.PAD_MD, pady=4)
            ctk.CTkLabel(
                item, text=label, font=Fonts.BODY, text_color=C.text_primary,
            ).pack(side="left")
            badge = ctk.CTkFrame(
                item, fg_color=color, corner_radius=Dim.RADIUS_SM, height=22,
            )
            badge.pack(side="right")
            badge.pack_propagate(False)
            ctk.CTkLabel(
                badge, text=status, font=Fonts.TINY_BOLD,
                text_color=C.text_on_primary,
            ).pack(padx=8, expand=True)

        ctk.CTkLabel(
            system_frame, text="\u26A1 System healthy \u2014 all services operational",
            font=Fonts.TINY, text_color=C.success,
        ).pack(pady=(0, Dim.PAD_MD))

        bind_smooth_scroll(scroll)

    def apply_theme(self):
        self.configure(fg_color=C.bg_main)
