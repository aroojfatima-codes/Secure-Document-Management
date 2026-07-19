"""Cross-platform smooth scrolling utilities for CustomTkinter.

Handles mousewheel bindings for Windows (MouseWheel), macOS (Shift+MouseWheel),
and Linux (Button-4/5) on CTkScrollableFrame and any scrollable container.
"""

from __future__ import annotations

import sys
import customtkinter as ctk


def bind_smooth_scroll(widget: ctk.CTkBaseClass) -> None:
    """Bind cross-platform mousewheel scrolling to a widget."""
    try:
        if sys.platform == "linux":
            widget.bind("<Button-4>", _on_linux_scroll_up, add="+")
            widget.bind("<Button-5>", _on_linux_scroll_down, add="+")
        else:
            widget.bind("<MouseWheel>", _on_windows_mac_scroll, add="+")

        widget.bind("<Map>", lambda e: _bind_children(widget), add="+")
        _bind_children(widget)
    except Exception:
        pass


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


def _scroll_widget(scrollable: ctk.CTkScrollableFrame, delta: int) -> None:
    """Scroll a CTkScrollableFrame using its internal canvas."""
    try:
        scrollable._parent_canvas.yview_scroll(int(delta), "units")
    except AttributeError:
        try:
            scrollable._parent_frame.yview_scroll(int(delta), "units")
        except AttributeError:
            pass
    except Exception:
        pass


def _on_windows_mac_scroll(event) -> str:
    """Handle mousewheel on Windows and macOS."""
    try:
        scrollable = _find_scrollable_ancestor(event.widget)
        if scrollable is not None:
            delta = event.delta
            if sys.platform == "darwin":
                _scroll_widget(scrollable, -1 * delta / 3)
            else:
                _scroll_widget(scrollable, -1 * delta / 120)
    except Exception:
        pass
    return "break"


def _on_linux_scroll_up(event) -> str:
    """Handle Button-4 (scroll up) on Linux."""
    try:
        scrollable = _find_scrollable_ancestor(event.widget)
        if scrollable is not None:
            _scroll_widget(scrollable, -3)
    except Exception:
        pass
    return "break"


def _on_linux_scroll_down(event) -> str:
    """Handle Button-5 (scroll down) on Linux."""
    try:
        scrollable = _find_scrollable_ancestor(event.widget)
        if scrollable is not None:
            _scroll_widget(scrollable, 3)
    except Exception:
        pass
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
    """Rebind scroll events after content changes."""
    parent = content_frame
    while parent is not None:
        try:
            parent = parent.master
        except Exception:
            return
        if isinstance(parent, ctk.CTkScrollableFrame):
            bind_smooth_scroll(parent)
            return
