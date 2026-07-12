"""Animation utilities for smooth GUI transitions."""

from __future__ import annotations

import customtkinter as ctk
from typing import Callable


def fade_in(widget: ctk.CTkBaseClass, steps: int = 10, delay: int = 20) -> None:
    """Show a grid-managed widget (CTK has no alpha, so this is instant)."""
    try:
        widget.grid()
    except Exception:
        widget.pack()
    widget.lift()


def fade_out(widget: ctk.CTkBaseClass, steps: int = 10, delay: int = 20,
             callback: Callable | None = None) -> None:
    """Hide a grid-managed widget, then optionally call callback."""
    try:
        widget.grid_forget()
    except Exception:
        widget.pack_forget()
    if callback:
        callback()


def slide_in_from_left(widget: ctk.CTkBaseClass, target_x: int = 0,
                       start_x: int = -200, steps: int = 12, delay: int = 15) -> None:
    """Slide a widget in from the left."""
    widget.place(x=start_x, rely=0.5, anchor="w")
    widget.after(0, _slide_step(widget, start_x, target_x, steps, delay, 0))


def slide_in_from_right(widget: ctk.CTkBaseClass, container_w: int,
                        widget_w: int, steps: int = 12, delay: int = 15) -> None:
    """Slide a widget in from the right."""
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


def _ease_out_cubic(t: float) -> float:
    return 1 - (1 - t) ** 3


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
