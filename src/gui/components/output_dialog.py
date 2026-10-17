"""Modal column selector with a private draft until OK is pressed."""

from collections.abc import Callable

import customtkinter as ctk

from src.core.output_settings import DEFAULT_NAMES, OUTPUT_NAMES, normalize_selection
from src.core.export_selection import EXPORT_PRESETS, export_preset


class OutputDialog(ctk.CTkToplevel):
    """Choose clipboard and file columns without changing scraping scope."""

    def __init__(self, master: ctk.CTkBaseClass, names: tuple[str, ...],
                 on_apply: Callable[[tuple[str, ...]], bool],
                 checks: tuple[str, ...] | None = None) -> None:
        """Build a scrollable popup that fits smaller desktop displays."""
        super().__init__(master)
        self.title("Select Output")
        self.geometry("480x570")
        self.minsize(400, 400)
        self.transient(master)
        self.on_apply = on_apply
        self.checks = checks
        self.variables = {name: ctk.BooleanVar(value=name in names) for name in OUTPUT_NAMES}
        self.variables["Username"].set(True)
        self.checkboxes: dict[str, ctk.CTkCheckBox] = {}
        ctk.CTkLabel(self, text="Choose columns for copy and export").pack(pady=(12, 6))
        self.preset_var = ctk.StringVar(value="Custom columns")
        self.preset_menu = ctk.CTkOptionMenu(
            self, values=list(EXPORT_PRESETS), variable=self.preset_var,
            command=self.apply_preset,
        )
        self.preset_menu.pack(fill="x", padx=12, pady=(0, 6))
        body = ctk.CTkScrollableFrame(self)
        body.pack(fill="both", expand=True, padx=12)
        for name, variable in self.variables.items():
            checkbox = ctk.CTkCheckBox(body, text=name, variable=variable,
                                      state="disabled" if name == "Username" else "normal")
            checkbox.pack(anchor="w", padx=12, pady=5)
            self.checkboxes[name] = checkbox
        ctk.CTkLabel(
            self, text="The same selection applies to clipboard, CSV and Excel.",
        ).pack(pady=6)
        tools = ctk.CTkFrame(self, fg_color="transparent")
        tools.pack(fill="x", padx=12, pady=6)
        ctk.CTkButton(tools, text="Select all", command=self.select_all).pack(side="left")
        ctk.CTkButton(tools, text="Reset to default", command=self.reset).pack(side="right")
        buttons = ctk.CTkFrame(self, fg_color="transparent")
        buttons.pack(fill="x", padx=12, pady=(6, 12))
        self.ok_button = ctk.CTkButton(buttons, text="OK", command=self.apply)
        self.ok_button.pack(side="right")
        ctk.CTkButton(buttons, text="Cancel", command=self.destroy).pack(side="left")
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.after(50, self._make_modal)

    def _make_modal(self) -> None:
        """Take the grab once Tk has mapped the window."""
        self.lift()
        self.grab_set()

    def select_all(self) -> None:
        """Select every supported output column in the draft."""
        for variable in self.variables.values():
            variable.set(True)

    def apply_preset(self, preset: str) -> None:
        """Change only this dialog's draft until the operator presses OK."""
        if preset == "Custom columns":
            return
        names = export_preset(preset, self.checks)
        for name, variable in self.variables.items():
            variable.set(name in names)

    def reset(self) -> None:
        """Restore the six default columns in the draft."""
        for name, variable in self.variables.items():
            variable.set(name in DEFAULT_NAMES)

    def apply(self) -> None:
        """Apply only after preferences have been saved successfully."""
        names = normalize_selection(tuple(name for name, var in self.variables.items() if var.get()))
        if self.on_apply(names):
            self.destroy()
