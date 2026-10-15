"""Local RFC 6238 authenticator codes; the seed never leaves this process."""

import base64
import hashlib
import hmac
import struct
import time

from src.core.credentials import normalize_secret


def totp_code(secret: str, timestamp: float | None = None, digits: int = 6) -> str:
    """Generate SHA-1 TOTP for a 30-second step; support RFC eight-digit tests."""
    if digits not in (6, 8):
        raise ValueError("TOTP digits must be six or eight.")
    key = normalize_secret(secret)
    key_bytes = base64.b32decode(key + "=" * (-len(key) % 8))
    current = time.time() if timestamp is None else timestamp
    if current < 0:
        raise ValueError("TOTP time must not precede the Unix epoch.")
    digest = hmac.new(key_bytes, struct.pack(">Q", int(current // 30)), hashlib.sha1).digest()
    offset = digest[-1] & 15
    number = int.from_bytes(digest[offset:offset + 4], "big") & 0x7fffffff
    return str(number % (10 ** digits)).zfill(digits)
