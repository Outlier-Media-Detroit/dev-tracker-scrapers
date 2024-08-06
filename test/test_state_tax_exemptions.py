from datetime import datetime

import pytest
from freezegun import freeze_time
from scrapy.http import Request, Response

from tracker.items import TrackerLocation
from tracker.spiders.state_tax_exemptions import StateTaxExemptionsSpider

from .utils import load_fixture_bytes


@pytest.fixture
def freeze():
    with freeze_time("2024-08-05"):
        yield


@pytest.fixture
def parsed(freeze):
    url = "https://www.michigan.gov/taxes/-/media/Project/Websites/treasury/BLGSS/PSD/Property-Tax-OPRA-Certs/2022/OPRA_11152022_New.pdf?rev=6f2baf3277bf4a8ea250666295e4e3d5&hash=DC8CD7EDCBCE22DD31C715E7F801AFFE"  # noqa
    res = Response(
        url,
        body=load_fixture_bytes("state_tax_exemptions.pdf"),
        request=Request(
            url, meta={"action": "Certificates", "date": datetime(2022, 12, 20).date()}
        ),
    )
    spider = StateTaxExemptionsSpider()
    return [item for item in spider.parse_certificate_results(res)]


def test_count(parsed):
    assert len(parsed) == 3


def test_id(parsed):
    assert (
        parsed[0].id
        == "state_tax_exemptions/certificates/2022/12/20/682972d243a8c174df599849f1d8a08e1588cc0b8da2a55e32f49da3640d9329"  # noqa
    )


def test_content(parsed):
    assert (
        parsed[0].content
        == "The State Tax Commission, at their November 15, 2022 meeting, considered and approved your application for an obsolete property rehabilitation project, in accordance with Public Act 146 of 2000, as amended. Enclosed is certificate number 3-22-0030, issued to 1732 Bethune Lofts, LLC for the project located at 1732 Bethune Avenue, City of Detroit, Wayne County.\nA party aggrieved by the issuance, refusal to issue, revocation, transfer or modification of this exemption certificate may appeal a final decision of the State Tax Commission by filing a petition with the Michigan Tax Tribunal within 35 days. MCL 205.735a (6). More information on how to file a petition with the Michigan Tax Tribunal can be found at www.mich.gov/taxtrib or by calling (517) 335-9760."  # noqa
    )


def test_locations(parsed):
    assert sorted(parsed[0].locations, key=lambda loc: loc.address)[
        0
    ] == TrackerLocation(address="0030 Bethune Lofts")
