"""Strict account-file import; secrets stay in memory and out of repr/errors."""

import base64
import binascii
import csv
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class AccountCredential:
    """One authorized account's login data, never serialized by the app."""

    username: str
    password: str = field(repr=False)
    totp_secret: str = field(repr=False)


def normalize_secret(value: str) -> str:
    """Validate a Base32 authenticator seed without echoing invalid input."""
    secret = "".join(value.split()).upper().rstrip("=")
    if not re.fullmatch(r"[A-Z2-7]{16,128}", secret):
        raise ValueError("2FA must be a Base32 authenticator secret, not an OTP.")
    try:
        decoded = base64.b32decode(secret + "=" * (-len(secret) % 8))
    except (binascii.Error, ValueError):
        raise ValueError("Invalid Base32 authenticator secret.") from None
    if len(decoded) < 10:
        raise ValueError("Authenticator secret is too short.")
    return secret


def parse_accounts(text: str) -> list[AccountCredential]:
    """Read up to five unique username|password|2FA rows, all or nothing."""
    result: list[AccountCredential] = []
    seen: set[str] = set()
    for number, line in enumerate(text.lstrip("\ufeff").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            fields = next(csv.reader([line], delimiter="|", strict=True))
        except csv.Error:
            raise ValueError(f"Line {number}: malformed pipe-separated row.") from None
        if len(fields) != 3:
            raise ValueError(f"Line {number}: expected username|password|2FA secret.")
        if (not result and fields[0].strip().casefold() == "username"
                and fields[1].strip().casefold() == "password"
                and fields[2].strip().casefold() in {"2fa", "2fa_secret", "totp_secret"}):
            continue
        username, password, raw_secret = fields
        username = username.strip().lstrip("@").lower()
        if not re.fullmatch(r"[a-z0-9_.]{1,30}", username):
            raise ValueError(f"Line {number}: invalid Instagram username.")
        if not password or any(ord(char) < 32 for char in password):
            raise ValueError(f"Line {number}: password is empty or contains control characters.")
        if username in seen:
            raise ValueError(f"Line {number}: duplicate account.")
        try:
            secret = normalize_secret(raw_secret)
        except ValueError:
            raise ValueError(f"Line {number}: invalid authenticator secret.") from None
        seen.add(username)
        result.append(AccountCredential(username, password, secret))
        if len(result) > 5:
            raise ValueError("Import at most five accounts per file.")
    if not result:
        raise ValueError("The account file contains no account rows.")
    return result


def read_accounts(path: Path) -> list[AccountCredential]:
    """Read a small UTF-8 account file, with sanitized file/encoding errors."""
    try:
        if path.stat().st_size > 64 * 1024:
            raise ValueError("Account file exceeds 64 KB.")
        return parse_accounts(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError):
        raise ValueError("Cannot read the account file as UTF-8 text.") from None
