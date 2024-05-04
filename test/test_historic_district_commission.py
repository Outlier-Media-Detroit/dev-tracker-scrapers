import pytest
from freezegun import freeze_time
from scrapy.http import HtmlResponse

from tracker.items import TrackerLocation
from tracker.spiders.historic_district_commission import (
    HistoricDistrictCommissionSpider,
)

pytest.mark.usefixtures("betamax_session")


@pytest.fixture
def freeze():
    with freeze_time("2024-05-04"):
        yield


@pytest.fixture
def parsed(betamax_session, freeze):
    url = "https://detroitmi.gov/government/mayors-office/bridging-neighborhoods-program/property-listings/3769-3777-3783-sturtevant-03132024"  # noqa
    betamax_res = betamax_session.get(url)
    res = HtmlResponse(url, body=betamax_res.content)
    spider = HistoricDistrictCommissionSpider()
    return [item for item in spider.parse(res)]


def test_locations(parsed):
    assert sorted(parsed[0].locations, key=lambda loc: loc.address) == [
        TrackerLocation(address="3769 Sturtevant"),
        TrackerLocation(address="3777 Sturtevant"),
        TrackerLocation(address="3783 Sturtevant"),
    ]


def test_content(parsed):
    assert (
        parsed[0].content
        == "ALSO KNOWN AS (AKA) HISTORIC DISTRICT Russel Woods-Sullivan NEIGHBORHOOD Russell Woods-Sullivan YEAR CONSTRUCTED Ca. 1920 ELEMENTS OF DESIGN COUNCIL DISTRICT 7 APPLICATION NUMBER PROJECT SCOPE Erect new garage, alter existing garage, install driveways"  # noqa
    )
