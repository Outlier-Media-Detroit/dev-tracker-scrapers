import pytest
from freezegun import freeze_time
from scrapy.http import HtmlResponse

from tracker.items import TrackerLocation
from tracker.spiders.det_press_releases import DetPressReleasesSpider

pytest.mark.usefixtures("betamax_session")


@pytest.fixture
def freeze():
    with freeze_time("2025-02-04"):
        yield


@pytest.fixture
def parsed(betamax_session, freeze):
    url = "https://detroitmi.gov/news/mayor-duggan-state-local-leaders-celebrate-groundbreaking-brand-new-18m-affordable-housing-project"  # noqa
    betamax_res = betamax_session.get(url)
    res = HtmlResponse(url, body=betamax_res.content)
    spider = DetPressReleasesSpider()
    return [item for item in spider.parse(res)]


def test_count(parsed):
    assert len(parsed) == 1


def test_id(parsed):
    assert (
        parsed[0].id
        == "det_press_releases/2023/12/11/b94efe8447e955b19301e69e1bc5f09aec64035b5d81a00fd098dc1d1bf6f808"  # noqa
    )


def test_locations(parsed):
    assert parsed[0].locations == [
        TrackerLocation(address="5800 Michigan Avenue The"),
    ]
