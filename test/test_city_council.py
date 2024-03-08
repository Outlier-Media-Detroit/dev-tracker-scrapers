import pytest
from freezegun import freeze_time
from scrapy.http import HtmlResponse

from tracker.items import TrackerLocation
from tracker.spiders.city_council import CityCouncilSpider

pytest.mark.usefixtures("betamax_session")


@pytest.fixture
def freeze():
    with freeze_time("2024-02-04"):
        yield


@pytest.fixture
def parsed(betamax_session, freeze):
    url = "https://pub-detroitmi.escribemeetings.com/Meeting.aspx?Id=78f778d5-f60e-4f58-b4b5-c52373ee5a39&Agenda=Agenda&lang=English"  # noqa
    betamax_res = betamax_session.get(url)
    res = HtmlResponse(url, body=betamax_res.content)
    spider = CityCouncilSpider()
    return [item for item in spider.parse(res)]


def test_count(parsed):
    assert len(parsed) == 3


def test_locations(parsed):
    assert parsed[0].locations == [TrackerLocation(address="629 West Willis")]
