import pytest
from freezegun import freeze_time
from scrapy.http import HtmlResponse

from tracker.items import TrackerLocation
from tracker.spiders.bseed_special import BseedSpecialSpider

pytest.mark.usefixtures("betamax_session")


@pytest.fixture
def freeze():
    with freeze_time("2024-04-16"):
        yield


@pytest.fixture
def parsed(betamax_session, freeze):
    url = "https://detroitmi.gov/events/special-land-use-hearings-0"
    betamax_res = betamax_session.get(url)
    res = HtmlResponse(url, body=betamax_res.content)
    spider = BseedSpecialSpider()
    return [item for item in spider.parse(res)]


def test_count(parsed):
    assert len(parsed) == 3


def test_id(parsed):
    assert parsed[0].id == "bseed_special/2024/04/17/SLU2023-00240"


def test_locations(parsed):
    assert parsed[0].locations == [
        TrackerLocation(address="7214 W Vernor Hwy"),
        TrackerLocation(pin="18001417."),
    ]
