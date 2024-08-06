import hashlib
import re
from datetime import datetime
from io import BytesIO
from typing import List

import scrapy
from pdfminer.high_level import extract_pages, extract_text

from tracker.items import TrackerEvent, TrackerLocation
from tracker.utils import clean_spaces, parse_addresses


class StateTaxExemptionsSpider(scrapy.Spider):
    name = "state_tax_exemptions"
    allowed_domains = ["www.michigan.gov"]
    start_urls = ["https://www.michigan.gov/taxes/property/exemptions"]
    user_agent = (
        "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0"
    )

    def parse(self, response):
        for link in response.css(".component-content a.view-link"):
            title = link.xpath("string()").extract_first()
            url = link.xpath("@href").extract_first()
            yield response.follow(
                url, self.parse_exemption_page, meta={"exemption": title}
            )

    def parse_exemption_page(self, response):
        for link in response.css("#content li a"):
            title = re.sub(
                r"\s+", " ", link.xpath("string()").extract_first() or ""
            ).strip()
            if title.upper() != "CERTIFICATE ACTIVITY":
                continue
            yield response.follow(
                link.xpath("@href").extract_first(),
                self.parse_certificate_activity,
                meta=response.meta,
            )

    def parse_certificate_activity(self, response):
        for link in response.css(".component-content table:first-of-type a"):
            title = re.sub(
                r"\s+", " ", link.xpath("string()").extract_first() or ""
            ).strip()
            action = title.split(" ")[0]
            date_obj = None
            date_match = re.search(r"\(.*\)", title)
            if date_match:
                try:
                    date_obj = datetime.strptime(
                        date_match.group(), "(%m/%d/%y)"
                    ).date()
                except ValueError:
                    date_obj = datetime.strptime(
                        date_match.group(), "(%m/%d/%Y)"
                    ).date()
            if date_obj is None or date_obj.year < 2020:
                continue
            yield response.follow(
                link.xpath("@href").extract_first(),
                self.parse_certificate_results,
                meta={**response.meta, "date": date_obj, "action": action},
            )

    def parse_certificate_results(self, response):
        pages = extract_pages(BytesIO(response.body))

        for page_num, _ in enumerate(pages):
            page_text = extract_text(
                BytesIO(response.body),
                page_numbers=[page_num],
            )

            if (
                ("Certificate No." in page_text)
                or ("FAQs" in page_text)
                or ("DETROIT" not in page_text.upper())
            ):
                continue

            h = hashlib.new("sha256")
            h.update(page_text.encode())

            yield TrackerEvent(
                id=f"state_tax_exemptions/{response.meta['action'].lower()}/{response.meta['date'].strftime('%Y/%m/%d')}/{h.hexdigest()}",  # noqa
                source="state_tax_exemptions",
                source_title=self.parse_owner(page_text),
                date=response.meta["date"],
                url=response.url,
                content=self.parse_content(page_text),
                locations=self.parse_locations(page_text),
            )

    def parse_owner(self, content: str) -> str:
        # Pull from recipient block
        split_blocks = content.split("\n\n")
        for idx, block in enumerate(split_blocks):
            if block.strip().startswith("Dear"):
                return split_blocks[idx - 1].split("\n")[1].strip()
        return ""

    def parse_content(self, content: str) -> str:
        output_lines = []
        for block in content.split("\n\n"):
            clean_block = clean_spaces(block)
            if ("State Tax Commission" in block) and (
                "Executive Director" not in block
            ):
                output_lines.append(clean_block)
        return "\n".join(output_lines)

    def parse_locations(self, content: str) -> List[TrackerLocation]:
        locations = []
        for address in parse_addresses(clean_spaces(content)):
            locations.append(TrackerLocation(address=address))
        return locations
