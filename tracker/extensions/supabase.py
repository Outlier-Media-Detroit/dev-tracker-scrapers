from dataclasses import asdict

from scrapy import signals
from scrapy.crawler import Crawler
from supabase import create_client
from supabase.client import Client
from ..items import TrackerEvent, TrackerLocation
from ..api import DetroitAddressAPI


class SupabaseExporterExtension:
    def __init__(self, url: str, key: str, table: str):
        self.scraped_items = []
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
        self.table.upsert(self.scraped_items).execute()

    def add_item(self, item: TrackerEvent):
        locations = [asdict(self.clean_location(loc)) for loc in item.locations]
        item_dict = asdict(item)
        item_dict["date"] = item_dict["date"].strftime("%Y-%m-%d")
        item_dict.pop("locations")

        item_dict["data"] = {"locations": locations}
        self.scraped_items.append(item_dict)

    def clean_location(self, location: TrackerLocation) -> TrackerLocation:
        """TODO: Put this in a separate extension"""
        if location.pin:
            cleaned_loc = DetroitAddressAPI.get_location_from_pin(location.pin)
        elif location.address:
            cleaned_loc = DetroitAddressAPI.get_location_from_address(location.address)
        # Default to existing location if a response wasn't found
        return cleaned_loc or location
