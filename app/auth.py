from __future__ import annotations

import base64
import hmac


def auth_enabled(username: str | None, password: str | None) -> bool:
    return bool(username and password)


def authorised_basic_header(
    header: str | None, username: str | None, password: str | None
) -> bool:
    if not auth_enabled(username, password):
        return True
    if not header or not header.startswith("Basic "):
        return False
    try:
        decoded = base64.b64decode(header[6:], validate=True).decode("utf-8")
        supplied_user, supplied_password = decoded.split(":", 1)
    except (ValueError, UnicodeDecodeError):
        return False
    return hmac.compare_digest(supplied_user, username or "") and hmac.compare_digest(
        supplied_password, password or ""
    )
