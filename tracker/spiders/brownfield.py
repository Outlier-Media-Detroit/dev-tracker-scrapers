import re
from datetime import datetime
from io import BytesIO, StringIO
from typing import List

import requests
import scrapy
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams
from scrapy.http import Response
from scrapy.selector import Selector

from tracker.items import TrackerEvent, TrackerLocation
from tracker.utils import parse_addresses


# TODO: Kales, Odd Fellows,
class BrownfieldSpider(scrapy.Spider):
    name = "brownfield"
    allowed_domains = ["www.degc.org"]
    start_urls = ["https://www.degc.org/dbra/"]
    USER_AGENT = (
        "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0"
    )
    plan_pin_map = {}

    def parse(self, response: Response):
        # TODO:
        # self.load_plans(response)
        for document_link in response.css("div.et_pb_tab_2 a"):
            document_title = document_link.xpath("./text()").extract_first()
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
        for group in response.css(".accordion-block .accordion-row"):
            label_text = " ".join(group.css(".accordion-label *::text").extract())
            if "PLANS UNDER CONSIDERATION" not in label_text.upper():
                continue
            for plan_link in group.css("a"):
                plan_title = self.get_plan_name(
                    plan_link.xpath("./text()").extract_first()
                )
                plan_link_map[plan_title] = self.get_plan_url(response, plan_link)

        for plan_name, plan_url in plan_link_map.items():
            print(plan_url)
            res = requests.get(
                plan_url, allow_redirects=True, headers={"User-Agent": self.USER_AGENT}
            )
            pdf_str = self.parse_pdf(res.content)
            print(plan_name)
            self.plan_pin_map[plan_name] = self.parse_pins(pdf_str)
            print(self.plan_pin_map[plan_name])

    def parse_pins(self, body_text: str) -> List[str]:
        pin_results = re.findall(r"\d{7,8}[.-]?[\dA-Z]*", body_text)
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
        agenda_project_items = [
            agenda_item
            for agenda_item in re.split(
                r"\n(?=[IVXLCDM]+\.)",
                agenda_text.split("PROJECTS")[1].split("OTHER")[0],
            )
            if ":" in agenda_item
        ]
        for agenda_item in agenda_project_items:
            date_str = response.meta["document_title"].split(" – ")[1]
            dt = datetime.strptime(date_str, "%B %d, %Y")
            yield TrackerEvent(
                id=self.parse_agenda_id(
                    response.meta["document_title"], dt, agenda_item
                ),
                source="brownfield",
                date=dt.date(),
                url=response.url,
                content=re.sub(r"\s+", " ", agenda_item).strip(),
                locations=self.parse_agenda_item_locations(agenda_item),
            )

    def parse_agenda_id(self, title: str, dt: datetime, agenda_item: str) -> str:
        item_id = agenda_item.split(".")[0].lower().strip()
        slug_title = re.sub(r"[^a-z0-9 ]", "", title.lower()).replace(" ", "_")
        return f"brownfield/{dt.strftime('%Y/%m/%d')}/{slug_title}/{item_id}"

    def parse_agenda_item_locations(self, agenda_item: str) -> List[TrackerLocation]:
        project_str = re.split(r"[IVXLCDM]+\.", agenda_item)[1].split(":")[0].strip()
        # TODO: How to handle "Former Fisher Body Redevelopment" showing up for "Former
        # Fisher Body Plant"
        locations = self.plan_pin_map.get(project_str.upper().strip(), [])
        for address in parse_addresses(agenda_item):
            print(address)
            locations.append(
                TrackerLocation(
                    address=re.split(r"Brownfield", address, flags=re.IGNORECASE)[0]
                )
            )
        return locations

    def parse_minutes_pdf(
        self, title: str, response_bytes: bytes
    ) -> List[TrackerEvent]:
        """TODO: Parse semi-structured, beginning of groups"""
        # Some project names are addresses, not included in plans
        # TODO: Remove double spaces, but not double newlines to start
        pass

    def parse_pdf(self, pdf_bytes: bytes) -> str:
        out_str = StringIO()
        extract_text_to_fp(
            BytesIO(pdf_bytes), out_str, laparams=LAParams(line_margin=0.1)
        )
        return out_str.getvalue()
