"""Screenshot-inspired independent checkboxes for target fields."""

from collections.abc import Callable

import customtkinter as ctk

from src.core.check_plan import CHECK_LABELS, CHECK_NAMES, checks_for_mode
from src.gui import theme


class CheckSelection(ctk.CTkFrame):
    """Let operators combine status, country and joined-date checks."""

    def __init__(
        self, master: ctk.CTkBaseClass, on_changed: Callable[[], None],
    ) -> None:
        """Build field cards and a shortcut controlling both Alive checks."""
        super().__init__(master, fg_color=theme.BG_ELEVATED)
        self.grid_columnconfigure((0, 1), weight=1)
        self.on_changed = on_changed
        self.variables = {
            name: ctk.BooleanVar(value=True) for name in CHECK_NAMES
        }
        self.checkboxes: dict[str, ctk.CTkCheckBox] = {}
        self.both_var = ctk.BooleanVar(value=True)
        self.both_button = ctk.CTkCheckBox(
            self, text="IG + Threads Alive", variable=self.both_var,
            command=self._both_changed, font=theme.FONT_CAPTION,
        )
        self.both_button.grid(
            row=0, column=0, columnspan=2, sticky="w", padx=10, pady=8,
        )
        for index, (name, label) in enumerate(CHECK_LABELS):
            card = ctk.CTkFrame(self, fg_color=theme.BG_SURFACE)
            card.grid(
                row=1 + index // 2, column=index % 2,
                sticky="nsew", padx=4, pady=4,
            )
            control = ctk.CTkCheckBox(
                card, text="", width=26, variable=self.variables[name],
                command=self._changed,
            )
            control.pack(side="left", padx=(6, 0), pady=8)
            caption = ctk.CTkLabel(
                card, text=label, wraplength=95, justify="left",
                font=theme.FONT_CAPTION,
            )
            caption.pack(side="left", padx=4)
            caption.bind(
                "<Button-1>",
                lambda _event, checkbox=control: checkbox.toggle(),
            )
            self.checkboxes[name] = control
        self.note = ctk.CTkLabel(
            self, text="Preset selected. Tick any mix for custom checks.",
            wraplength=260, font=theme.FONT_CAPTION,
        )
        self.note.grid(row=4, column=0, columnspan=2, padx=6, pady=6)

    @property
    def selection(self) -> tuple[str, ...]:
        """Return selected field identifiers in a stable order."""
        return tuple(name for name, var in self.variables.items() if var.get())

    def set_preset(self, mode: str) -> None:
        """Mirror a legacy preset without emitting a custom-selection event."""
        checks = checks_for_mode(mode)
        for name, variable in self.variables.items():
            variable.set(name in checks)
        self._sync_both()
        self.note.configure(
            text="Preset selected. Tick any mix for custom checks.",
        )

    def set_enabled(self, enabled: bool) -> None:
        """Freeze the complete selection during setup and active runs."""
        for control in (*self.checkboxes.values(), self.both_button):
            control.configure(state="normal" if enabled else "disabled")

    def _sync_both(self) -> None:
        """Keep the Alive shortcut checked only when both flags are checked."""
        self.both_var.set(all(
            self.variables[name].get()
            for name in ("ig_alive", "threads_alive")
        ))

    def _both_changed(self) -> None:
        """Toggle both Alive flags without touching country/date choices."""
        for name in ("ig_alive", "threads_alive"):
            self.variables[name].set(self.both_var.get())
        self._changed()

    def _changed(self) -> None:
        """Explain custom scope and notify the owning panel."""
        self._sync_both()
        count = len(self.selection)
        self.note.configure(
            text=f"Custom: {count} checks. Select Output sets export fields.",
        )
        self.on_changed()
