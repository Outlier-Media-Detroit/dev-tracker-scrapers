import re
from datetime import datetime
from io import BytesIO
from typing import List, Optional

import requests
import scrapy
import sentry_sdk
from pdfminer.high_level import extract_pages, extract_text
from pdfminer.layout import LAParams
from scrapy.http import Response
from scrapy.selector import Selector

from tracker.items import TrackerEvent, TrackerLocation
from tracker.utils import PIN_PATTERN, clean_spaces, parse_addresses


# TODO: Kales, Odd Fellows,
class BrownfieldSpider(scrapy.Spider):
    name = "brownfield"
    allowed_domains = ["www.degc.org"]
    start_urls = ["https://www.degc.org/dbra/"]
    USER_AGENT = (
        "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0"
    )
    plan_address_map = {}

    def parse(self, response: Response):
        for section in response.css("[role=tabpanel]")[1:]:
            for document_link in section.css("a"):
                document_title = " ".join(document_link.css("*::text").extract())
                if "AGENDA" in document_title.upper():
                    yield scrapy.Request(
                        response.urljoin(document_link.xpath("@href").extract_first()),
                        self.parse_agenda_pdf,
                        meta={
                            "document_title": document_title,
                        },
                    )

    def load_plans(self, response: Response):
        plan_link_map = {}
        in_plans = False
        for line in response.css(".wixui-tabs__container p"):
            label_text = " ".join(line.css("*::text").extract())
            if not in_plans:
                if "PLANS UNDER CONSIDERATION" in label_text.upper():
                    in_plans = True
                    continue
            for plan_link in line.css("a"):
                plan_title = self.get_plan_name(
                    " ".join(plan_link.css("*::text").extract())
                )
                plan_link_map[plan_title] = self.get_plan_url(response, plan_link)

        for plan_name, plan_url in plan_link_map.items():
            res = requests.get(
                plan_url, allow_redirects=True, headers={"User-Agent": self.USER_AGENT}
            )
            pdf_str = self.parse_plan_pdf(plan_url, res.content)
            self.plan_address_map[plan_name.upper().strip()] = [
                clean_spaces(a) for a in parse_addresses(pdf_str)
            ] + self.parse_pins(pdf_str)

    def parse_pins(self, body_text: str) -> List[str]:
        pin_results = re.findall(PIN_PATTERN, body_text)
        pins = []
        for result in pin_results:
            # Remove accidental suffixes of streets like ...00WOODWARD
            pin = re.sub(r"[A-Z]{2,}$", "", result)
            if not any(c in pin for c in [".", "-"]):
                pins.append(f"{pin.zfill(8)}.")
            else:
                pins.append(pin)
        return list(set(pins))

    def get_plan_url(self, response: Response, link: Selector) -> str:
        plan_url = response.urljoin(link.xpath("@href").extract_first())
        # Handle dropbox links by changing param to force PDF download
        if ("dropbox" in plan_url) and ("dl=0" in plan_url):
            plan_url = plan_url.replace("dl=0", "dl=1")
        return plan_url

    def get_plan_name(self, plan_text: str) -> str:
        return (
            re.sub(r"\s+", " ", plan_text.upper())
            .strip()
            .replace(" BROWNFIELD PLAN", "")
            .split(" REDEVELOPMENT PROJECT ")[0]
            .split(" TRANSFORMATIONAL ")[0]
        )

    def parse_agenda_pdf(self, response: Response):
        agenda_text = self.parse_pdf(response.body)
        split_items = agenda_text.split("PROJECTS")[1].split("OTHER")[0].split("\n\n")
        agenda_numbers = [
            agenda_num
            for agenda_num in split_items
            if re.search(r"^[IVXLCDM]+\.", agenda_num.strip())
        ]
        agenda_project_items = [
            agenda_item for agenda_item in split_items if ":" in agenda_item
        ]
        for idx, agenda_item in enumerate(agenda_project_items):
            date_str = response.meta["document_title"].split(" – ")[1]
            dt = datetime.strptime(date_str, "%B %d, %Y")
            item_id = None
            if len(agenda_numbers) > idx:
                item_id = agenda_numbers[idx]
            yield TrackerEvent(
                id=self.parse_agenda_id(
                    response.meta["document_title"], dt, agenda_item, item_id
                ),
                source="brownfield",
                source_title=response.meta["document_title"],
                date=dt.date(),
                url=response.url,
                content=re.sub(r"\s+", " ", agenda_item).strip(),
                locations=self.parse_agenda_item_locations(agenda_item),
            )

    def parse_agenda_id(
        self,
        title: str,
        dt: datetime,
        agenda_item: str,
        item_id: Optional[str] = None,
    ) -> str:
        if not item_id:
            item_id = agenda_item.split(".")[0].lower().strip()
        slug_title = re.sub(r"[^a-z0-9 ]", "", title.lower()).replace(" ", "_")
        return f"brownfield/{dt.strftime('%Y/%m/%d')}/{slug_title}/{item_id}"

    def parse_agenda_item_locations(self, agenda_item: str) -> List[TrackerLocation]:
        if re.search(r"^[IVXLCDM]+\.", agenda_item):
            agenda_item = re.split(r"[IVXLCDM]+\.", agenda_item)[1]
        project_str = agenda_item.upper().split(":")[0].split("BROWNFIELD")[0].strip()
        # TODO: How to handle "Former Fisher Body Redevelopment" showing up for "Former
        # Fisher Body Plant"
        locations = [
            TrackerLocation(address=address)
            for address in self.plan_address_map.get(project_str, [])
        ]
        for address in parse_addresses(agenda_item):
            locations.append(
                TrackerLocation(
                    address=re.split(r"Brownfield", address, flags=re.IGNORECASE)[0]
                )
            )
        return locations

    def parse_plan_pdf(self, plan_url: str, pdf_bytes: bytes) -> str:
        pages = extract_pages(BytesIO(pdf_bytes))
        page_results = []

        # Only pull pages that have PINs on them to check for addresses
        for page_num, _ in enumerate(pages):
            try:
                page_text = extract_text(
                    BytesIO(pdf_bytes),
                    page_numbers=[page_num],
                    laparams=LAParams(line_margin=0.1),
                )
                if re.search(PIN_PATTERN, page_text):
                    page_results.append(page_text)
            except Exception as e:
                with sentry_sdk.push_scope() as scope:
                    scope.set_extra("url", plan_url)
                    sentry_sdk.capture_exception(e)
        return "\n".join(page_results)

    def parse_pdf(self, pdf_bytes: bytes) -> str:
        return extract_text(BytesIO(pdf_bytes), laparams=LAParams(line_margin=0.5))
