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


def test_content(parsed):
    assert (
        parsed[0].content
        == "9:00 AM Case: SLU2024-00031 Address: 8045 & 8035 Linwood Ave. and 2619 Montgomery St. (PIN: 10007710.001, 10007710.002L, & 10001474.001) Proposed Use: Establish a Concert Café in a 1,267 square foot unit of an existing 4,895 square foot building and develop a 2,107 square foot Outdoor Seating/Patio Area behind the proposed cafe in a B4 (General Business) Zoning District."  # noqa
    )
    assert (
        parsed[1].content
        == "9:30 AM Case: SLU2024-00091 Address: 15411 & 15435 E. Warren Ave. (PIN: 21002804-5 & 21002806-9) Proposed Use: Establish the uses of Brewpub, microbrewery, small distillery, and small winery and Specially designated distributors (SDD) and Specially designated merchants (SDM) establishment in an existing 2,612 square foot building in a B4 (General Business) Zoning District."  # noqa
    )


def test_locations(parsed):
    assert parsed[0].locations == [
        TrackerLocation(address="7214 W Vernor Hwy"),
        TrackerLocation(pin="18001417."),
    ]
