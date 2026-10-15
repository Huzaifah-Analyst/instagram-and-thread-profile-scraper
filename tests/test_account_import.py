"""Account parsing, stable isolation and RFC 6238 known-answer regressions."""

import base64
from pathlib import Path

import pytest

from src.core.checkers import CheckerStore
from src.core.credentials import parse_accounts, read_accounts
from src.core.totp import totp_code

SEED = base64.b32encode(b"12345678901234567890").decode()


@pytest.mark.parametrize("timestamp,expected", [
    (59, "94287082"), (1111111109, "07081804"), (1111111111, "14050471"),
    (1234567890, "89005924"), (2000000000, "69279037"), (20000000000, "65353130"),
])
def test_rfc6238_sha1_vectors(timestamp: int, expected: str) -> None:
    """Compare against the RFC's independent SHA-1 examples, not our algorithm."""
    assert totp_code(SEED, timestamp, 8) == expected
    assert totp_code(SEED, timestamp) == expected[-6:]


def test_import_normalizes_username_and_seed_but_preserves_password() -> None:
    """BOM, optional header and grouped secrets work without trimming passwords."""
    account = parse_accounts(f'\ufeffusername|password|2fa\n@Alice|" pass|word "|{SEED.lower()}\n')[0]
    assert account.username == "alice"
    assert account.password == " pass|word "
    assert account.totp_secret == SEED
    assert account.password not in repr(account) and SEED not in repr(account)


@pytest.mark.parametrize("text", [
    "", "# no entries", "alice|sensitive-pass|123456", "alice|sensitive-pass",
    f"bad user|sensitive-pass|{SEED}", f"alice||{SEED}",
    f"alice|sensitive-pass|{SEED}\nALICE|sensitive-pass|{SEED}",
    "\n".join(f"user{i}|sensitive-pass|{SEED}" for i in range(6)),
    'alice|"sensitive-pass|bad-secret',
])
def test_invalid_imports_are_atomic_and_errors_redacted(text: str) -> None:
    """An invalid row yields no partial account list or secret-bearing message."""
    with pytest.raises(ValueError) as error:
        parse_accounts(text)
    assert "sensitive-pass" not in str(error.value)
    assert SEED not in str(error.value)


def test_file_limits_and_sanitized_missing_path(tmp_path: Path) -> None:
    """Reject missing, oversized and non-UTF8 files before any login."""
    path = tmp_path / "secret-password.txt"
    with pytest.raises(ValueError, match="Cannot read") as error:
        read_accounts(path)
    assert path.name not in str(error.value)
    path.write_bytes(b"x" * 65537)
    with pytest.raises(ValueError, match="64 KB"):
        read_accounts(path)
    path.write_bytes(b"\xff")
    with pytest.raises(ValueError, match="UTF-8"):
        read_accounts(path)


def test_import_reordering_keeps_identity_bound_sessions(tmp_path: Path) -> None:
    """Reimport/reorder never assigns another account's saved browser profile."""
    primary = tmp_path / "browser_profile"
    primary.mkdir()
    (primary / "sentinel").write_text("original session")
    store = CheckerStore(primary)
    first = {s.username: s.profile_dir for s in store.bind_accounts(["alice", "bob"])}
    second = {s.username: s.profile_dir for s in store.bind_accounts(["bob", "alice"])}
    assert first == second and len(set(first.values())) == 2
    assert primary not in first.values()
    store.save(["checker_2"])
    assert store.load()[1].username == "alice"
    assert (primary / "sentinel").read_text() == "original session"
    assert "password" not in store.path.read_text() and SEED not in store.path.read_text()
