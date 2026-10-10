"""Five independent named checker profiles; configuration contains no secrets."""

import json
import logging
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Checker:
    """One isolated browser profile and its operator-selected enabled state."""

    checker_id: str
    profile_dir: Path
    enabled: bool = False
    username: str | None = None


def checker_slots(primary: Path) -> list[Checker]:
    """Reuse the existing session as checker 1; allocate four separate profiles."""
    return [Checker(
        f"checker_{index}", primary if index == 1 else primary.parent / "checker_profiles" / f"checker_{index}",
        enabled=index == 1,
    ) for index in range(1, 6)]


class CheckerStore:
    """Persist selections and usernames only; never store passwords or 2FA seeds."""

    def __init__(self, primary: Path) -> None:
        """Locate settings beside the primary profile, outside bundled resources."""
        self.primary = primary
        self.path = primary.parent / "checkers.json"

    def load(self) -> list[Checker]:
        """Read enabled slot IDs and fail visibly on invalid configuration."""
        slots = checker_slots(self.primary)
        if not self.path.exists():
            return slots
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        enabled = raw.get("enabled") if isinstance(raw, dict) else None
        known = {slot.checker_id for slot in slots}
        if (not isinstance(enabled, list) or not enabled
                or any(not isinstance(item, str) or item not in known for item in enabled)
                or len(set(enabled)) != len(enabled)):
            raise ValueError("Invalid checkers.json: select valid checker slots in Setup.")
        identities = raw.get("identities", {})
        if (not isinstance(identities, dict)
                or any(key not in known or not isinstance(value, str)
                       or not re.fullmatch(r"[a-z0-9_.]{1,30}", value)
                       for key, value in identities.items())
                or len(set(identities.values())) != len(identities)):
            raise ValueError("Invalid checker account bindings in checkers.json.")
        result = []
        for slot in slots:
            username = identities.get(slot.checker_id)
            profile = slot.profile_dir
            if username:
                digest = hashlib.sha256(username.encode("utf-8")).hexdigest()[:24]
                profile = self.primary.parent / "checker_profiles" / f"imported_{digest}"
            result.append(Checker(slot.checker_id, profile, slot.checker_id in enabled, username))
        return result

    def save(self, enabled: list[str]) -> None:
        """Atomically save validated slot selection without touching login state."""
        identities = {slot.checker_id: slot.username for slot in self.load() if slot.username}
        self._write(enabled, identities)

    def bind_accounts(self, usernames: list[str]) -> list[Checker]:
        """Bind slots to stable imported profiles without overwriting older sessions."""
        if (not 1 <= len(usernames) <= 5 or len(set(usernames)) != len(usernames)
                or any(not re.fullmatch(r"[a-z0-9_.]{1,30}", value) for value in usernames)):
            raise ValueError("Import one to five distinct valid account usernames.")
        identities = {f"checker_{i}": name for i, name in enumerate(usernames, 1)}
        self._write(list(identities), identities)
        return [slot for slot in self.load() if slot.enabled]

    def _write(self, enabled: list[str], identities: dict[str, str]) -> None:
        """Write only selected IDs and account names, never passwords or seeds."""
        known = {slot.checker_id for slot in checker_slots(self.primary)}
        if not enabled or len(set(enabled)) != len(enabled) or not set(enabled) <= known:
            raise ValueError("Select at least one distinct checker.")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps({"enabled": enabled, "identities": identities}, indent=2), encoding="utf-8")
        temporary.replace(self.path)
