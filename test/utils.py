import os

FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures")


def load_fixture_bytes(fixture: str) -> bytes:
    with open(os.path.join(FIXTURE_DIR, fixture), "rb") as f:
        return f.read()
