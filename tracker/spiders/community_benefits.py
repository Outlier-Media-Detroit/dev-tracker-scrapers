from datetime import datetime, timedelta
from urllib.parse import urlencode

import scrapy
from scrapy.http import Response

from tracker.items import TrackerEvent


class CommunityBenefitsSpider(scrapy.Spider):
    name = "community_benefits"
    allowed_domains = ["detroitmi.gov"]

    def start_requests(self):
        start_date = datetime.now() - timedelta(days=365)
        req_params = {
            "field_start_value": start_date.strftime("%Y-%m-%d"),
            "term_node_tid_depth": "86",
            "term_node_tid_depth_1": "All",
            "term_node_tid_depth_2": "All",
        }
        yield scrapy.Request(
            f"https://detroitmi.gov/Calendar-and-Events?{urlencode(req_params)}",
            self.parse_events,
        )

    def parse_events(self, response: Response):
        INCLUDE_STRINGS = ["Benefit", "CBO"]
        for event in response.css(".view-content .article-title a"):
            event_title = event.xpath("string()").extract_first()
            # Assign list of title strings for events that should be included
            if any(s in event_title for s in INCLUDE_STRINGS):
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
        url_subpath = response.url.split("/")[-1]

        yield TrackerEvent(
            id=f"community_benefits/{event_dt.strftime('%Y/%m/%d')}/{url_subpath}",
            source="community_benefits",
            source_title=event_title,
            date=event_dt.date(),
            url=response.url,
            content=" ".join(response.css("article.description *::text").extract()),
            locations=[],
        )
