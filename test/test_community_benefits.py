import pytest
from freezegun import freeze_time
from scrapy.http import HtmlResponse

from tracker.spiders.community_benefits import CommunityBenefitsSpider

pytest.mark.usefixtures("betamax_session")


@pytest.fixture
def freeze():
    with freeze_time("2024-04-24"):
        yield


@pytest.fixture
def parsed(betamax_session, freeze):
    url = "https://detroitmi.gov/events/hotel-water-square-cbo-meeting-1-9-2024"
    betamax_res = betamax_session.get(url)
    res = HtmlResponse(url, body=betamax_res.content)
    spider = CommunityBenefitsSpider()
    return [item for item in spider.parse(res)]


def test_count(parsed):
    assert len(parsed) == 1


def test_id(parsed):
    assert (
        parsed[0].id
        == "community_benefits/2024/01/09/hotel-water-square-cbo-meeting-1-9-2024"
    )


def test_locations(parsed):
    assert parsed[0].locations == []
