from scrapy import Spider
from scrapy.crawler import Crawler

from .items import TrackerEvent


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
        return item
