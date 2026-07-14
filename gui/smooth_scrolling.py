"""Cross-platform smooth scrolling utilities for CustomTkinter.

Handles mousewheel bindings for Windows (MouseWheel), macOS (Shift+MouseWheel),
and Linux (Button-4/5) on CTkScrollableFrame and any scrollable container.
"""

from __future__ import annotations

import sys
import customtkinter as ctk


def bind_smooth_scroll(widget: ctk.CTkBaseClass) -> None:
    """Bind cross-platform mousewheel scrolling to a widget.

    Call this after building content inside a CTkScrollableFrame so the
    mousewheel works regardless of which child widget has focus.

    On Windows  : <MouseWheel>  (delta ±120)
    On macOS    : <Shift-MouseWheel>
    On Linux    : <Button-4> / <Button-5>
    """
    if sys.platform == "linux":
        widget.bind("<Button-4>", _on_linux_scroll_up, add="+")
        widget.bind("<Button-5>", _on_linux_scroll_down, add="+")
    else:
        widget.bind("<MouseWheel>", _on_windows_mac_scroll, add="+")
        # macOS trackpad sends MouseWheel with very small delta values
        # so the same handler works for both platforms.

    # Also bind to all current and future children
    widget.bind("<Map>", lambda e: _bind_children(widget), add="+")
    _bind_children(widget)


def _bind_children(widget: ctk.CTkBaseClass) -> None:
    """Recursively bind scroll events to all child widgets."""
    try:
        for child in widget.winfo_children():
            if sys.platform == "linux":
                child.bind("<Button-4>", _on_linux_scroll_up, add="+")
                child.bind("<Button-5>", _on_linux_scroll_down, add="+")
            else:
                child.bind("<MouseWheel>", _on_windows_mac_scroll, add="+")
            _bind_children(child)
    except Exception:
        pass


def _on_windows_mac_scroll(event) -> str:
    """Handle mousewheel on Windows and macOS."""
    # Find the nearest CTkScrollableFrame ancestor
    scrollable = _find_scrollable_ancestor(event.widget)
    if scrollable is not None:
        # Windows: delta is typically ±120 per notch
        # macOS: delta can be smaller for trackpad
        delta = event.delta
        if sys.platform == "darwin":
            # macOS: delta is in pixels, typically ±1 to ±10
            scrollable._parent_frame.yview_scroll(int(-1 * delta / 3), "units")
        else:
            # Windows: delta is in multiples of 120
            scrollable._parent_frame.yview_scroll(int(-1 * delta / 120), "units")
    return "break"


def _on_linux_scroll_up(event) -> str:
    """Handle Button-4 (scroll up) on Linux."""
    scrollable = _find_scrollable_ancestor(event.widget)
    if scrollable is not None:
        scrollable._parent_frame.yview_scroll(-3, "units")
    return "break"


def _on_linux_scroll_down(event) -> str:
    """Handle Button-5 (scroll down) on Linux."""
    scrollable = _find_scrollable_ancestor(event.widget)
    if scrollable is not None:
        scrollable._parent_frame.yview_scroll(3, "units")
    return "break"


def _find_scrollable_ancestor(widget) -> ctk.CTkScrollableFrame | None:
    """Walk up the widget tree to find the nearest CTkScrollableFrame."""
    current = widget
    while current is not None:
        if isinstance(current, ctk.CTkScrollableFrame):
            return current
        try:
            current = current.master
        except Exception:
            break
    return None


def rebind_scroll(content_frame: ctk.CTkFrame) -> None:
    """Rebind scroll events after content changes.

    Call this after dynamically adding/removing children from a
    CTkScrollableFrame to ensure new widgets get scroll bindings.
    """
    # Find the parent scrollable frame
    parent = content_frame
    while parent is not None:
        try:
            parent = parent.master
        except Exception:
            return
        if isinstance(parent, ctk.CTkScrollableFrame):
            bind_smooth_scroll(parent)
            return
