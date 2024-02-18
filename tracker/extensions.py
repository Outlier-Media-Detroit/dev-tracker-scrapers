from dataclasses import asdict
from io import StringIO

import sentry_sdk
from scrapy import Spider, signals
from scrapy.crawler import Crawler
from sentry_sdk import Client as SentryClient
from supabase import create_client
from supabase.client import Client
from twisted.python.failure import Failure

from .items import TrackerEvent


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

    # TODO: Need to look up PINs for addresses
    def add_item(self, item: TrackerEvent):
        item_dict = asdict(item)
        item_dict["date"] = item_dict["date"].strftime("%Y-%m-%d")
        item_dict["data"] = {"locations": item_dict.pop("locations")}
        self.scraped_items.append(item_dict)


class SentryErrors:
    def __init__(self, dsn):
        self.client: SentryClient = sentry_sdk.init(dsn=dsn)

    @classmethod
    def from_crawler(cls, crawler):
        extension = cls(dsn=crawler.settings.get("SENTRY_DSN"))
        crawler.signals.connect(extension.spider_error, signal=signals.spider_error)
        return extension

    def spider_error(self, failure: Failure, response, spider: Spider):
        traceback = StringIO()
        failure.printTraceback(file=traceback)
        self.client.capture_message(
            message="[{}] {}".format(spider.name, repr(failure.value))
        )
