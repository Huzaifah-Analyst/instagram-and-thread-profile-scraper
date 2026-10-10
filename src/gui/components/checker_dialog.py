"""Manage isolated checker sessions with optional in-memory account import."""

from pathlib import Path
from tkinter import filedialog
from typing import Callable

import customtkinter as ctk

from src.core.checkers import Checker, CheckerStore
from src.core.credentials import AccountCredential, read_accounts
from src.core.session import SESSION_CONNECTED, check_session
from src.gui import theme


class CheckerDialog(ctk.CTkToplevel):
    """Let operators select slots and open their official IG/Threads login tabs."""

    def __init__(
        self, master: ctk.CTk, store: CheckerStore,
        on_login: Callable[[Checker], None], on_saved: Callable[[], None],
        on_import: Callable[[list[AccountCredential], list[Checker]], None] | None = None,
    ) -> None:
        """Build a compact account manager showing saved-login presence only."""
        super().__init__(master)
        self.title("Checker accounts")
        self.geometry("800x480")
        self.transient(master)
        self.store = store
        self.on_login = on_login
        self.on_saved = on_saved
        self.on_import = on_import
        self.slots = store.load()
        self.variables: list[ctk.BooleanVar] = []
        ctk.CTkLabel(
            self, text="Choose checkers for this batch", font=theme.FONT_H1
        ).pack(pady=(16, 6))
        ctk.CTkLabel(
            self, text="Each checker needs Instagram AND Threads login in its own browser.\n"
                       "Saved logins are verified live when you press Start. One worker per checker.",
        ).pack(pady=(0, 12))
        for slot in self.slots:
            row = ctk.CTkFrame(self)
            row.pack(fill="x", padx=18, pady=3)
            enabled = ctk.BooleanVar(value=slot.enabled)
            self.variables.append(enabled)
            label = slot.checker_id.replace("_", " ").title()
            if slot.username:
                label += f" (@{slot.username})"
            ctk.CTkCheckBox(row, text=label, variable=enabled).pack(
                side="left", padx=10, pady=8
            )
            state, _ = check_session(slot.profile_dir)
            ctk.CTkLabel(row, text="IG cookie saved" if state == SESSION_CONNECTED else "Login needed").pack(side="left")
            ctk.CTkButton(
                row, text="Login IG + Threads", width=155,
                command=lambda chosen=slot: self._login(chosen),
            ).pack(side="right", padx=10)
        self.message = ctk.CTkLabel(self, text="", text_color=theme.STATUS_WARN)
        self.message.pack(pady=4)
        if on_import is not None:
            ctk.CTkButton(self, text="Import accounts & auto-login", command=self._import).pack(pady=4)
            ctk.CTkLabel(self, text="UTF-8 file: username|password|2FA secret (up to 5 accounts)").pack()
        ctk.CTkButton(self, text="Save selection", command=self._save).pack(pady=8)

    def _import(self) -> None:
        """Validate the entire file before binding sessions or starting browsers."""
        filename = filedialog.askopenfilename(
            parent=self, title="Import checker accounts", filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if not filename or self.on_import is None:
            return
        try:
            accounts = read_accounts(Path(filename))
            checkers = self.store.bind_accounts([account.username for account in accounts])
        except ValueError as exc:
            self.message.configure(text=str(exc))
            return
        except OSError:
            self.message.configure(text="Could not save checker settings. Check folder permissions.")
            return
        self.on_saved()
        self.destroy()
        self.on_import(accounts, checkers)

    def _login(self, checker: Checker) -> None:
        """Save choices before opening login and release the dialog's focus."""
        self.variables[self.slots.index(checker)].set(True)
        if self._persist():
            self.destroy()
            self.on_login(checker)

    def _persist(self) -> bool:
        """Persist selected slot IDs with an actionable validation message."""
        try:
            self.store.save([
                slot.checker_id for slot, variable in zip(self.slots, self.variables)
                if variable.get()
            ])
        except (OSError, ValueError) as exc:
            self.message.configure(text=str(exc))
            return False
        self.on_saved()
        return True

    def _save(self) -> None:
        """Close the manager only after its configuration is saved."""
        if self._persist():
            self.destroy()
