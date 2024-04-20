from scrapy import Spider
from scrapy.crawler import Crawler

from .api import DetroitAddressAPI
from .items import TrackerEvent, TrackerLocation


# TODO: implement pipeline loading previous development lookup strings
# Base on https://github.com/City-Bureau/city-scrapers-core/blob/main/city_scrapers_core/pipelines/diff.py  # noqa
class TrackerPipeline:
    def __init__(self, crawler: Crawler):
        self.crawler = crawler
        self.client = None

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        pipeline = cls(crawler)
        # TODO: This should be a key-value storage of strings to find and the fields to
        # apply to items matching them
        if crawler.spider:
            crawler.spider._projects = {}
        return pipeline

    def process_item(self, item: TrackerEvent, spider: Spider) -> TrackerEvent:
        clean_locations = []
        for location in item.locations:
            loc = self.clean_location(location)
            if loc:
                clean_locations.append(loc)
        item.locations = clean_locations
        return item

    def clean_location(self, location: TrackerLocation) -> TrackerLocation:
        cleaned_loc = None
        if location.pin:
            cleaned_loc = DetroitAddressAPI.get_location_from_pin(location.pin)
        # Try address if exists and PIN doesn't return a response
        if location.address and not cleaned_loc:
            cleaned_loc = DetroitAddressAPI.get_location_from_address(location.address)
        # Only include location if API matches
        return cleaned_loc
