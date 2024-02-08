import pytest
from freezegun import freeze_time

pytest.mark.usefixtures("betamax_session")


@pytest.fixture
def freeze():
    with freeze_time("2024-02-04"):
        yield
