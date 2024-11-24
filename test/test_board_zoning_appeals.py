import pytest
from freezegun import freeze_time
from scrapy.http import HtmlResponse

from tracker.items import TrackerLocation
from tracker.spiders.board_zoning_appeals import BoardZoningAppealsSpider

pytest.mark.usefixtures("betamax_session")


@pytest.fixture
def freeze():
    with freeze_time("2024-11-24"):
        yield


@pytest.fixture
def parsed(betamax_session, freeze):
    url = "https://detroitmi.gov/events/board-zoning-appeals-docket-44"
    betamax_res = betamax_session.get(url)
    res = HtmlResponse(url, body=betamax_res.content)
    spider = BoardZoningAppealsSpider()
    return [item for item in spider.parse(res)]


def test_count(parsed):
    assert len(parsed) == 1


def test_id(parsed):
    assert (
        parsed[0].id == "board_zoning_appeals/2024/09/23/board-zoning-appeals-docket-44"
    )


def test_locations(parsed):
    assert sorted(parsed[0].locations, key=lambda loc: loc.address) == [
        TrackerLocation(address="14439 Wade"),
        TrackerLocation(address="469 Brainard"),
        TrackerLocation(address="637 Leicester Court"),
        TrackerLocation(address="643 Leicester Court"),
        TrackerLocation(address="649 Leicester Court"),
        TrackerLocation(address="9301 Oakland"),
    ]
