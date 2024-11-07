from datetime import datetime

import pytest
from scrapy.http import HtmlResponse

from tracker.spiders.medc_programs import MedcProgramsSpider

pytest.mark.usefixtures("betamax_session")


@pytest.fixture
def parsed(betamax_session):
    url = "https://www.michiganbusiness.org/reports-data/michigan-community-revitalization-program-projects/"  # noqa
    betamax_res = betamax_session.get(url)
    res = HtmlResponse(url, body=betamax_res.content)
    spider = MedcProgramsSpider()
    return [item for item in spider.parse_table(res)]


def test_count(parsed):
    assert len(parsed) == 9


def test_dt(parsed):
    assert parsed[0].date == datetime(2024, 10, 22).date()


def test_content(parsed):
    assert (
        parsed[0].content
        == "Approval Date: Oct 22, 2024\nLocation: Detroit\nProject Investment: Up to $153.28 million\nProjected Jobs: 80\nProjected Award Amount: Up to $1.50 million"  # noqa
    )
