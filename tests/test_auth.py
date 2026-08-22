import base64

from app.auth import authorised_basic_header


def basic(user: str, password: str) -> str:
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return f"Basic {token}"


def test_auth_disabled_when_credentials_not_set():
    assert authorised_basic_header(None, None, None)


def test_auth_rejects_wrong_credentials_and_accepts_right_ones():
    assert not authorised_basic_header(None, "liam", "secret")
    assert not authorised_basic_header(basic("liam", "wrong"), "liam", "secret")
    assert authorised_basic_header(basic("liam", "secret"), "liam", "secret")
