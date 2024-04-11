import pytest
from freezegun import freeze_time
from scrapy.http import Response, Request

from tracker.items import TrackerLocation
from tracker.spiders.planning_commission import PlanningCommissionSpider

from .utils import load_fixture_bytes

pytest.mark.usefixtures("betamax_session")


@pytest.fixture
def freeze():
    with freeze_time("2024-02-04"):
        yield


@pytest.fixture
def parsed(freeze):
    url = "https://detroitmi.gov/sites/detroitmi.localhost/files/2024-02/2%201%202024%20CPC%20Agenda.pdf"  # noqa
    res = Response(
        url,
        body=load_fixture_bytes("planning_commission_agenda.pdf"),
        request=Request(url, meta={"doc_title": "2/1/2024 Agenda"}),
    )
    spider = PlanningCommissionSpider()
    return [item for item in spider.parse_agenda(res)]


def test_count(parsed):
    assert len(parsed) == 4


def test_locations(parsed):
    assert sorted(parsed[2].locations, key=lambda loc: loc.address) == [
        TrackerLocation(address="2075 Vermont Street"),
        TrackerLocation(address="2081 Vermont Street"),
        TrackerLocation(address="2087 Vermont Street"),
        TrackerLocation(address="2099 Vermont Street"),
    ]
