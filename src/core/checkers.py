"""Five independent named checker profiles; configuration contains no secrets."""

import json
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Checker:
    """One isolated browser profile and its operator-selected enabled state."""

    checker_id: str
    profile_dir: Path
    enabled: bool = False


def checker_slots(primary: Path) -> list[Checker]:
    """Reuse the existing session as checker 1; allocate four separate profiles."""
    return [Checker(
        f"checker_{index}", primary if index == 1 else primary.parent / "checker_profiles" / f"checker_{index}",
        enabled=index == 1,
    ) for index in range(1, 6)]


class CheckerStore:
    """Persist selection only; passwords, email and 2FA stay in official login UI."""

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
        return [Checker(slot.checker_id, slot.profile_dir, slot.checker_id in enabled) for slot in slots]

    def save(self, enabled: list[str]) -> None:
        """Atomically save validated slot selection without touching login state."""
        known = {slot.checker_id for slot in checker_slots(self.primary)}
        if not enabled or len(set(enabled)) != len(enabled) or not set(enabled) <= known:
            raise ValueError("Select at least one distinct checker.")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps({"enabled": enabled}, indent=2), encoding="utf-8")
        temporary.replace(self.path)
