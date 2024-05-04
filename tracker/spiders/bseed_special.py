import re
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import urlencode

import scrapy
from scrapy.http import Response

from tracker.items import TrackerEvent, TrackerLocation
from tracker.utils import clean_spaces, parse_addresses, PIN_PATTERN


class BseedSpecialSpider(scrapy.Spider):
    name = "bseed_special"
    allowed_domains = ["detroitmi.gov"]

    def start_requests(self):
        start_date = datetime.now() - timedelta(days=365)
        req_params = {
            "field_start_value": start_date.strftime("%Y-%m-%d"),
            "term_node_tid_depth": "36",
            "term_node_tid_depth_1": "All",
            "term_node_tid_depth_2": "All",
        }
        yield scrapy.Request(
            f"https://detroitmi.gov/Calendar-and-Events?{urlencode(req_params)}",
            self.parse_events,
        )

    def parse_events(self, response: Response):
        IGNORE_STRINGS = ["Land Based Projects"]
        for event in response.css(".view-content .article-title a"):
            event_title = event.xpath("string()").extract_first()
            # Assign list of title strings for events that should be ignored
            if any(s in event_title for s in IGNORE_STRINGS):
                continue
            yield scrapy.Request(
                response.urljoin(event.xpath("@href").extract_first()), self.parse
            )

        for next_link in response.css("a[title='Go to next page']"):
            yield scrapy.Request(
                response.urljoin(next_link.xpath("@href").extract_first()),
                self.parse_events,
            )

    def parse(self, response: Response):
        event_title = " ".join(response.css("h1.title *::text").extract()).strip()
        event_time = response.css(".event-node time").xpath("@datetime").extract_first()
        if event_time is None:
            return
        event_dt = datetime.strptime(event_time.split("T")[0].strip(), "%Y-%m-%d")

        for row in response.css("article.description p"):
            row_text = clean_spaces(" ".join(row.css("*::text").extract()))
            # Only handling clean PIN items
            if "PIN:" not in row_text:
                continue
            row_chunks = row.css("*::text").extract()
            case_id = self.parse_case_id(row_chunks)

            yield TrackerEvent(
                id=f"bseed_special/{event_dt.strftime('%Y/%m/%d')}/{case_id}",
                source="bseed_special",
                source_title=event_title,
                date=event_dt.date(),
                url=response.url,
                content=row_text,
                locations=self.parse_locations(row_chunks),
            )

    def parse_case_id(self, row_chunks: List[str]) -> Optional[str]:
        clean_chunks = [chunk.strip() for chunk in row_chunks if chunk.strip()]
        for idx, chunk in enumerate(clean_chunks):
            # Get the first element following "Case:"
            if "Case" in chunk:
                return clean_chunks[idx + 1]
        return "x"

    def parse_locations(self, row_chunks: List[str]) -> List[TrackerLocation]:
        locations = []
        location_str = [r for r in row_chunks if "PIN:" in r][0]
        for address in parse_addresses(location_str):
            locations.append(TrackerLocation(address=address))
        for pin in re.findall(PIN_PATTERN, location_str):
            locations.append(TrackerLocation(pin=pin))
        return locations
