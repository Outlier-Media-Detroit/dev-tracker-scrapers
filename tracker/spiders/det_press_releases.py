import hashlib
import re
from datetime import datetime, timedelta
from typing import List
from urllib.parse import urlencode

import scrapy
from scrapy.http import Response

from tracker.items import TrackerEvent, TrackerLocation
from tracker.utils import PIN_PATTERN, parse_addresses


class DetPressReleasesSpider(scrapy.Spider):
    name = "det_press_releases"
    allowed_domains = ["detroitmi.gov"]

    def start_requests(self):
        start_date = datetime.now() - timedelta(days=365)
        req_params = {
            "field_start_value": start_date.strftime("%Y-%m-%d"),
            "term_node_tid_depth": "All",
            "term_node_tid_depth_1": "301",
            "term_node_tid_depth_2": "All",
        }
        yield scrapy.Request(
            f"https://detroitmi.gov/news?{urlencode(req_params)}",
            self.parse_events,
        )

    def parse_events(self, response: Response):
        for event in response.css(".view-content .article-title a"):
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
        event_time = response.css(".news-node time").xpath("@datetime").extract_first()
        if event_time is None:
            return
        event_dt = datetime.strptime(event_time.split("T")[0].strip(), "%Y-%m-%d")

        content = " ".join(response.css("article.description *::text").extract())
        locations = self.parse_locations(content)
        if len(locations) > 0:
            h = hashlib.new("sha256")
            h.update(content.encode())
            yield TrackerEvent(
                id=f"det_press_releases/{event_dt.strftime('%Y/%m/%d')}/{h.hexdigest()}",  # noqa
                source="Detroit Press Releases",
                source_title=event_title,
                date=event_dt.date(),
                url=response.url,
                content="",
                locations=locations,
            )

    def parse_locations(self, content: str) -> List[TrackerLocation]:
        locations = []
        for address in parse_addresses(content):
            locations.append(TrackerLocation(address=address))
        for pin in re.findall(PIN_PATTERN, content):
            locations.append(TrackerLocation(pin=pin))
        return locations
