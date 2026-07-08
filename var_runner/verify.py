"""Post-push verification: byte-for-byte comparison of local vs re-fetched remote.

Web-editor commits can fail silently (observed repeatedly in the qrc-shot-wall
incident log), so every push is verified by re-fetching the raw file with a
cache-busted URL and comparing bytes. No trust without re-fetch.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass


@dataclass
class VerifyResult:
    ok: bool
    local_sha256: str
    remote_sha256: str
    first_diff_offset: int | None = None
    detail: str = ""

    def __bool__(self) -> bool:  # allows `if verify_bytes(...):`
        return self.ok


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_bytes(local: bytes, remote: bytes) -> VerifyResult:
    """Compare local and remote content byte-for-byte."""
    lsha, rsha = sha256_hex(local), sha256_hex(remote)
    if lsha == rsha:
        return VerifyResult(True, lsha, rsha, None, "identical")
    offset = next(
        (i for i, (a, b) in enumerate(zip(local, remote)) if a != b),
        min(len(local), len(remote)),
    )
    return VerifyResult(
        False, lsha, rsha, offset,
        f"mismatch at byte {offset}: local {len(local)}B vs remote {len(remote)}B",
    )


def normalize_newlines(data: bytes) -> bytes:
    """CRLF/CR -> LF. Use ONLY for diagnosis, never to declare verification passed."""
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
