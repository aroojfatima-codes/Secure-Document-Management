"""Canvas-drawn charts for dashboard analytics."""

from __future__ import annotations
import customtkinter as ctk
from gui.theme import ThemeManager, Dim, Fonts

tm = ThemeManager()
C = tm.C


class DonutChart(ctk.CTkFrame):
    """Simple donut/pie chart drawn on a Canvas."""

    def __init__(self, master, size: int = 160, **kw):
        super().__init__(master, fg_color=C.bg_card,
                         corner_radius=Dim.RADIUS_LG, **kw)
        self._size = size
        self._canvas = ctk.CTkCanvas(
            self, width=size, height=size,
            bg=C.bg_card, highlightthickness=0,
        )
        self._canvas.pack(pady=Dim.PAD_MD)
        self._legend = ctk.CTkFrame(self, fg_color="transparent")
        self._legend.pack(fill="x", padx=Dim.PAD_SM, pady=(0, Dim.PAD_MD))

    def draw(self, segments: list[tuple[str, float, str]]):
        """Draw donut chart. segments = [(label, value, color), ...]"""
        self._canvas.delete("all")
        for w in self._legend.winfo_children():
            w.destroy()

        total = sum(s[1] for s in segments)
        if total == 0:
            return

        cx, cy, r = self._size // 2, self._size // 2, self._size // 2 - 10
        inner_r = r * 0.55
        start = -90

        for label, value, color in segments:
            extent = (value / total) * 360
            self._canvas.create_arc(
                cx - r, cy - r, cx + r, cy + r,
                start=start, extent=extent,
                fill=color, outline=C.bg_card, width=2, style="pieslice",
            )
            start += extent

        self._canvas.create_oval(
            cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r,
            fill=C.bg_card, outline=C.bg_card, width=2,
        )

        self._canvas.create_text(
            cx, cy - 8, text=str(int(total)), font=Fonts.TITLE_SM,
            fill=C.text_primary,
        )
        self._canvas.create_text(
            cx, cy + 10, text="Total", font=Fonts.TINY,
            fill=C.text_secondary,
        )

        for label, value, color in segments:
            row = ctk.CTkFrame(self._legend, fg_color="transparent", height=18)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)
            ctk.CTkLabel(
                row, text="\u25CF", font=Fonts.TINY,
                text_color=color, width=16,
            ).pack(side="left", padx=(4, 2))
            ctk.CTkLabel(
                row, text=label, font=Fonts.TINY,
                text_color=C.text_secondary,
            ).pack(side="left")
            pct = f"{(value / total * 100):.0f}%" if total else "0%"
            ctk.CTkLabel(
                row, text=pct, font=Fonts.TINY_BOLD,
                text_color=C.text_primary,
            ).pack(side="right", padx=(4, 8))


class BarChart(ctk.CTkFrame):
    """Simple horizontal bar chart."""

    def __init__(self, master, width: int = 280, bar_height: int = 20, **kw):
        super().__init__(master, fg_color=C.bg_card,
                         corner_radius=Dim.RADIUS_LG, **kw)
        self._chart_width = width
        self._bar_height = bar_height
        self._canvas = ctk.CTkCanvas(
            self, width=width, height=10, bg=C.bg_card, highlightthickness=0,
        )
        self._canvas.pack(fill="x", padx=Dim.PAD_MD, pady=Dim.PAD_MD)

    def draw(self, data: list[tuple[str, float, str]]):
        """Draw horizontal bars. data = [(label, value, color), ...]"""
        self._canvas.delete("all")
        if not data:
            return
        max_val = max(d[1] for d in data) or 1
        bar_w = self._chart_width - 80
        y = 8

        for label, value, color in data:
            self._canvas.create_text(
                4, y + self._bar_height // 2, text=label,
                font=Fonts.TINY, fill=C.text_secondary, anchor="w",
            )
            bar_len = (value / max_val) * bar_w if max_val else 0
            x0, y0, x1, y1 = 70, y, 70 + bar_len, y + self._bar_height
            self._canvas.create_rectangle(
                x0, y0, x1, y1, fill=color, outline="", width=0,
            )
            self._canvas.create_text(
                x1 + 6, y + self._bar_height // 2,
                text=str(int(value)), font=Fonts.TINY,
                fill=C.text_secondary, anchor="w",
            )
            y += self._bar_height + 12

        self._canvas.configure(height=y + 4)


class MiniSparkline(ctk.CTkFrame):
    """Tiny sparkline chart for stat cards."""

    def __init__(self, master, width: int = 80, height: int = 28, **kw):
        super().__init__(master, fg_color="transparent", **kw)
        self._w = width
        self._h = height
        self._canvas = ctk.CTkCanvas(
            self, width=width, height=height,
            bg=C.bg_card, highlightthickness=0,
        )
        self._canvas.pack()

    def draw(self, values: list[float], color: str = ""):
        self._canvas.delete("all")
        if not color:
            color = C.primary
        if len(values) < 2:
            return
        max_v = max(values) or 1
        min_v = min(values)
        rng = max_v - min_v or 1
        points = []
        dx = self._w / (len(values) - 1)
        for i, v in enumerate(values):
            x = i * dx
            y = self._h - ((v - min_v) / rng) * (self._h - 4) - 2
            points.extend([x, y])
        if len(points) >= 4:
            self._canvas.create_line(
                points, fill=color, width=2, smooth=True,
            )
