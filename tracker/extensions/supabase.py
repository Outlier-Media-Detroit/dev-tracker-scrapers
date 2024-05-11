from dataclasses import asdict

from scrapy import signals
from scrapy.crawler import Crawler
from supabase import create_client
from supabase.client import Client

from ..items import TrackerEvent


class SupabaseExporterExtension:
    def __init__(self, url: str, key: str, table: str):
        self.scraped_items = {}
        self.client: Client = create_client(url, key)
        self.table = self.client.table(table)

    @classmethod
    def from_crawler(cls, crawler: Crawler):
        extension = cls(
            crawler.settings.get("SUPABASE_URL"),
            crawler.settings.get("SUPABASE_KEY"),
            crawler.settings.get("SUPABASE_TABLE"),
        )
        crawler.signals.connect(extension.add_item, signal=signals.item_scraped)
        crawler.signals.connect(extension.spider_closed, signal=signals.spider_closed)

        return extension

    def spider_closed(self):
        self.table.upsert(list(self.scraped_items.values())).execute()

    def add_item(self, item: TrackerEvent):
        item_dict = asdict(item)
        item_dict["date"] = item_dict["date"].strftime("%Y-%m-%d")
        locations = item_dict.pop("locations")

        item_dict["data"] = {"locations": locations}
        self.scraped_items[item_dict["id"]] = item_dict
