"""Transient confirmation banner (TSK-302).

The toast is ``place()``-d over the window, so it never shifts the layout or
takes focus, and it removes itself after ``duration_ms``.
"""

from __future__ import annotations

from typing import Optional

import customtkinter as ctk

from src.gui import theme

TOAST_DURATION_MS = 2500

_LEVELS = {
    "success": ("#064E3B", "#34D399", theme.STATUS_ACTIVE),
    "error": ("#7F1D1D", "#F87171", theme.STATUS_BANNED),
}


def show_toast(master: ctk.CTkBaseClass, text: str, level: str = "success",
               duration_ms: int = TOAST_DURATION_MS) -> ctk.CTkFrame:
    """Shows a banner near the bottom of ``master``'s window.

    A newer toast on the same window replaces the previous one.

    Args:
        master: Any widget; the toast is placed on its top-level window.
        text: Message to show.
        level: ``success`` (green) or ``error`` (red).
        duration_ms: How long the banner stays visible.

    Returns:
        The toast frame (tests use it to check visibility).
    """
    window = master.winfo_toplevel()
    previous: Optional[ctk.CTkFrame] = getattr(window, "_active_toast", None)
    if previous is not None and previous.winfo_exists():
        previous.destroy()

    background, foreground, border = _LEVELS.get(level, _LEVELS["success"])
    toast = ctk.CTkFrame(window, fg_color=background, border_color=border, border_width=1, corner_radius=8)
    ctk.CTkLabel(toast, text=text, text_color=foreground, font=theme.FONT_BODY).pack(padx=18, pady=10)
    toast.place(relx=0.5, rely=1.0, y=-120, anchor="s")
    toast.lift()
    window._active_toast = toast  # type: ignore[attr-defined]
    toast.after(duration_ms, lambda: toast.winfo_exists() and toast.destroy())
    return toast
