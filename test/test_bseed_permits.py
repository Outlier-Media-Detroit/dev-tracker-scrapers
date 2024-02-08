import pytest
from freezegun import freeze_time
from scrapy.http import Response
from tracker.spiders.bseed_permits import BseedPermitsSpider

pytest.mark.usefixtures("betamax_session")


@pytest.fixture
def freeze():
    with freeze_time("2024-02-04"):
        yield


@pytest.fixture
def parsed(betamax_session, freeze):
    url = "https://services2.arcgis.com/qvkbeam7Wirps6zC/arcgis/rest/services/building_permits_2023/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"  # noqa
    betamax_res = betamax_session.get(url)
    res = Response(url, body=betamax_res.content)
    spider = BseedPermitsSpider()
    return [item for item in spider.parse(res)]


def test_count(parsed):
    assert len(parsed) == 6
