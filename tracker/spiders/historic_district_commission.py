import re
from datetime import datetime, timedelta
from urllib.parse import urlencode

import scrapy
from scrapy.http import Response

from tracker.items import TrackerEvent, TrackerLocation
from tracker.utils import clean_spaces, parse_addresses


class HistoricDistrictCommissionSpider(scrapy.Spider):
    name = "historic_district_commission"

    def start_requests(self):
        start_date = datetime.now() - timedelta(days=365)
        req_params = {
            "field_start_value": start_date.strftime("%Y-%m-%d"),
            "term_node_tid_depth": "86",
            "term_node_tid_depth_1": "1636",
            "term_node_tid_depth_2": "All",
        }
        yield scrapy.Request(
            f"https://detroitmi.gov/Calendar-and-Events?{urlencode(req_params)}",
            self.parse_events,
        )

    def parse_events(self, response: Response):
        for event in response.css(".view-content .article-title a"):
            yield scrapy.Request(
                response.urljoin(event.xpath("@href").extract_first()), self.parse_event
            )

        for next_link in response.css("a[title='Go to next page']"):
            yield scrapy.Request(
                response.urljoin(next_link.xpath("@href").extract_first()),
                self.parse_events,
            )

    def parse_event(self, response: Response):
        for property_link in response.css("article.property a"):
            yield scrapy.Request(
                response.urljoin(property_link.xpath("@href").extract_first()),
                self.parse,
            )

    def parse(self, response: Response):
        event_title = " ".join(response.css("h1.title *::text").extract()).strip()
        addr_str = event_title.split(" (")[0]
        date_str = re.search(r"\d\d?/\d\d?/\d\d(\d\d)?", event_title).group()
        try:
            dt = datetime.strptime(date_str, "%m/%d/%Y")
        except ValueError:
            dt = datetime.strptime(date_str, "%m/%d/%y")

        yield TrackerEvent(
            id=f"historic_district_commission/{dt.strftime('%Y/%m/%d')}/{response.url.split('/')[-1]}",  # noqa
            source="historic_district_commission",
            source_title="Historic District Commission",
            date=dt.date(),
            url=response.url,
            content=clean_spaces(
                " ".join(response.css(".property-overview *::text").extract())
            ),
            locations=[
                TrackerLocation(address=address)
                for address in parse_addresses(addr_str)
            ],
        )
