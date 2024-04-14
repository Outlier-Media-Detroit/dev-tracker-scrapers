import hashlib
import re
from datetime import datetime
from io import BytesIO
from typing import List

import scrapy
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
from scrapy.http import Response

from tracker.items import TrackerEvent, TrackerLocation
from tracker.utils import PIN_PATTERN, clean_spaces, parse_addresses


class PlanningCommissionSpider(scrapy.Spider):
    name = "planning_commission"
    allowed_domains = ["detroitmi.gov"]
    start_urls = [
        "https://detroitmi.gov/documents?name=&field_department_target_id_1=%22CPC+Agendas%22&field_description_value=",  # noqa
        # "https://detroitmi.gov/documents?name=&field_department_target_id_1=%22CPC+Minutes%22&field_description_value=",  # noqa
    ]

    def parse(self, response: Response):
        for doc_link in response.css("#block-detroitmi-content ul a"):
            doc_title = doc_link.xpath("./text()").extract_first()
            # callback = (
            #     self.parse_minutes
            #     if "minutes" in doc_title.lower()
            #     else self.parse_agenda
            # )
            yield scrapy.Request(
                response.urljoin(doc_link.xpath("@href").extract_first()),
                self.parse_document_page,
                meta={
                    "parse_callback": self.parse_agenda,
                    "doc_title": doc_title,
                },
            )

    def parse_document_page(self, response: Response):
        doc_url = response.css("#block-detroitmi-content a::attr(href)").extract_first()
        yield scrapy.Request(
            response.urljoin(doc_url),
            response.meta["parse_callback"],
            meta={"doc_title": response.meta["doc_title"]},
        )

    def parse_agenda(self, response: Response):
        agenda_text = extract_text(
            BytesIO(response.body), laparams=LAParams(line_margin=0.5)
        )
        agenda_text = agenda_text.split("AGENDA", 1)[1]
        dt = self.parse_agenda_dt(response.meta["doc_title"])

        for section in self.parse_agenda_sections(agenda_text):
            if section.strip() in ["Public Comment"]:
                continue
            h = hashlib.new("sha256")
            h.update(section.encode())
            yield TrackerEvent(
                id=f"planning_commission/{dt.strftime('%Y/%m/%d')}/agenda/{h.hexdigest()}",  # noqa
                source="planning_commission",
                source_title="Agenda",
                date=dt.date(),
                url=response.url,
                content=section,
                locations=self.parse_agenda_locations(section),
            )

    def parse_agenda_sections(self, content: str) -> List[str]:
        sections = []
        include_section = False
        IGNORE_PATTERNS = [
            r"^[IVXLCDM]+\.",
            r"^[A-Z]\.$",
            r"^\d+ mins$",
        ]
        for section in re.split("\n{2,}", content):
            clean_section = section.strip()
            if re.search(r"^[IVXLCDM]+\.\s+Adjournment", clean_section) or re.search(
                r"^Adjournment", clean_section
            ):
                return sections

            if re.search(r"^[IVXLCDM]+\.\s+Public Hearings", clean_section):
                include_section = True
            elif include_section and not any(
                re.search(pattern, clean_section) for pattern in IGNORE_PATTERNS
            ):
                sections.append(section.strip())

        return sections

    def parse_agenda_dt(self, date_str: str) -> datetime:
        return datetime.strptime(date_str.split(" ")[0], "%m/%d/%Y")

    def parse_agenda_locations(self, content: str) -> List[TrackerLocation]:
        locations = []
        for address in parse_addresses(content):
            locations.append(TrackerLocation(address=clean_spaces(address)))
        for pin in re.findall(PIN_PATTERN, content):
            locations.append(TrackerLocation(pin=pin))
        return locations
