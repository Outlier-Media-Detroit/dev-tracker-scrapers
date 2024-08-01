from datetime import datetime

import pytest
from freezegun import freeze_time
from scrapy.http import Response

from tracker.items import TrackerLocation
from tracker.spiders.medc_incentives import MedcIncentivesSpider

pytest.mark.usefixtures("betamax_session")


@pytest.fixture
def freeze():
    with freeze_time("2024-08-01"):
        yield


@pytest.fixture
def parsed(betamax_session, freeze):
    url = "https://gisp.mcgi.state.mi.us/arcgis/rest/services/MEDC/Incentives/MapServer/0/query?f=json&where=1=1%20AND%20County%20=%20163&outFields=*&outSR=4326"  # noqa
    betamax_res = betamax_session.get(url)
    res = Response(url, body=betamax_res.content)
    spider = MedcIncentivesSpider()
    return [item for item in spider.parse(res)]


def test_count(parsed):
    assert len(parsed) == 226


def test_dt(parsed):
    assert parsed[0].date == datetime(2020, 4, 15).date()


def test_location(parsed):
    assert parsed[0].locations[0] == TrackerLocation(
        pin=None,
        address="655 W. Willis Detroit, MI 48201",
        lon=-83.06659999999994,
        lat=42.34920000000005,
    )
