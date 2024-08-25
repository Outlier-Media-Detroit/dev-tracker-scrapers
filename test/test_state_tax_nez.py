from datetime import datetime

import pytest
from scrapy.http import Request, Response

from tracker.spiders.state_tax_nez import StateTaxNezSpider

from .utils import load_fixture_bytes


@pytest.fixture
def parsed():
    url = "https://www.michigan.gov/treasury/-/media/Project/Websites/treasury/STC/Meetings/2024/August-20-2024--Exemptions-Agendadocx.pdf"  # noqa
    res = Response(
        url,
        body=load_fixture_bytes("state_tax_nez.pdf"),
        request=Request(url, meta={"agenda_date": datetime(2024, 8, 20).date()}),
    )
    spider = StateTaxNezSpider()
    return [item for item in spider.parse_agenda_detail(res)]


def test_count(parsed):
    assert len(parsed) == 127


def test_id(parsed):
    assert parsed[0].id == "state_tax_nez/2024/08/20/NEZ-2024-039"


def test_source_title(parsed):
    assert parsed[0].source_title == "NEZ Preliminary approval: NEZ-2024-039"
    assert parsed[-1].source_title == "NEZ Transfer approval: N2019-016"


def test_content(parsed):
    assert (
        parsed[0].content
        == "APPL. NO.: NEZ-2024-039\nNAME: Torian Detroit, LLC\nLOCAL UNIT: City of Detroit\nCOUNTY: Wayne\nAPPL. TYPE: 1\nINVESTMENT: $150,000\nEXPIRES ON XX/XX/XXXX: 08/20/2027"  # noqa
    )
