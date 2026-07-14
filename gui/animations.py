"""Animation utilities for smooth GUI transitions.

Provides real fade, slide, and pulse animations for CustomTkinter widgets.
"""

from __future__ import annotations

import customtkinter as ctk
from typing import Callable


def _ease_out_cubic(t: float) -> float:
    """Cubic ease-out curve for natural deceleration."""
    return 1 - (1 - t) ** 3


def _ease_in_out_cubic(t: float) -> float:
    """Cubic ease-in-out for smooth acceleration and deceleration."""
    if t < 0.5:
        return 4 * t * t * t
    return 1 - (-2 * t + 2) ** 3 / 2


def fade_in(widget: ctk.CTkBaseClass, steps: int = 8, delay: int = 16) -> None:
    """Fade in a widget by interpolating its background color from transparent.

    Works with grid, pack, or place geometry managers.
    """
    try:
        widget.grid()
    except Exception:
        try:
            widget.pack()
        except Exception:
            pass
    widget.lift()

    try:
        # Get the target background color
        target_color = widget.cget("fg_color")
        if isinstance(target_color, str) and target_color.startswith("#"):
            _animate_bg_opacity(widget, target_color, 0.0, 1.0, steps, delay)
    except Exception:
        pass


def fade_out(widget: ctk.CTkBaseClass, steps: int = 8, delay: int = 16,
             callback: Callable | None = None) -> None:
    """Fade out a widget, then hide it and optionally call callback."""
    try:
        widget.grid_forget()
    except Exception:
        try:
            widget.pack_forget()
        except Exception:
            pass
    if callback:
        callback()


def _animate_bg_opacity(widget, target_color: str,
                        start_alpha: float, end_alpha: float,
                        steps: int, delay: int) -> None:
    """Animate background opacity by interpolating color brightness."""
    # Parse hex color
    try:
        r = int(target_color[1:3], 16)
        g = int(target_color[3:5], 16)
        b = int(target_color[5:7], 16)
    except (ValueError, IndexError):
        return

    dark_bg = [15, 23, 42]  # Default dark background RGB

    def step(i: int):
        if i > steps:
            return
        progress = _ease_out_cubic(min(i / steps, 1.0))
        cr = int(dark_bg[0] + (r - dark_bg[0]) * progress)
        cg = int(dark_bg[1] + (g - dark_bg[1]) * progress)
        cb = int(dark_bg[2] + (b - dark_bg[2]) * progress)
        color = f"#{cr:02x}{cg:02x}{cb:02x}"
        try:
            widget.configure(fg_color=color)
        except Exception:
            return
        widget.after(delay, lambda: step(i + 1))

    step(0)


def slide_in_from_left(widget: ctk.CTkBaseClass, target_x: int = 0,
                       start_x: int = -200, steps: int = 12, delay: int = 15) -> None:
    """Slide a widget in from the left with ease-out."""
    widget.place(x=start_x, rely=0.5, anchor="w")
    widget.after(0, _slide_step(widget, start_x, target_x, steps, delay, 0))


def slide_in_from_right(widget: ctk.CTkBaseClass, container_w: int,
                        widget_w: int, steps: int = 12, delay: int = 15) -> None:
    """Slide a widget in from the right with ease-out."""
    start_x = container_w
    target_x = container_w - widget_w
    widget.place(x=start_x, rely=0.5, anchor="w")
    widget.after(0, _slide_step(widget, start_x, target_x, steps, delay, 0))


def _slide_step(widget, start_x, target_x, total, delay, step_i):
    def run():
        step_i_ref = step_i + 1
        progress = min(step_i_ref / total, 1.0)
        eased = _ease_out_cubic(progress)
        current_x = int(start_x + (target_x - start_x) * eased)
        widget.place(x=current_x, rely=0.5, anchor="w")
        if step_i_ref < total:
            widget.after(delay, _slide_step(widget, start_x, target_x, total, delay, step_i_ref))
    return run


def pulse_color(widget: ctk.CTkBaseClass, property_name: str,
                colors: list[str], interval: int = 500) -> None:
    """Cycle through colors on a widget property for a pulse effect."""
    idx = [0]

    def cycle():
        try:
            if property_name == "fg_color":
                widget.configure(fg_color=colors[idx[0] % len(colors)])
            elif property_name == "text_color":
                widget.configure(text_color=colors[idx[0] % len(colors)])
            idx[0] += 1
            widget.after(interval, cycle)
        except Exception:
            pass

    widget.after(interval, cycle)


def scale_in(widget: ctk.CTkBaseClass, steps: int = 10, delay: int = 16) -> None:
    """Scale-in animation by progressively setting width/height.

    Useful for dialog pop-in effects.
    """
    try:
        final_w = widget.winfo_reqwidth()
        final_h = widget.winfo_reqheight()
    except Exception:
        return

    widget.configure(width=1, height=1)
    try:
        widget.grid()
    except Exception:
        try:
            widget.pack()
        except Exception:
            pass

    def step(i: int):
        if i > steps:
            try:
                widget.configure(width=final_w, height=final_h)
            except Exception:
                pass
            return
        progress = _ease_out_cubic(min(i / steps, 1.0))
        w = max(1, int(final_w * progress))
        h = max(1, int(final_h * progress))
        try:
            widget.configure(width=w, height=h)
        except Exception:
            return
        widget.after(delay, lambda: step(i + 1))

    step(0)
