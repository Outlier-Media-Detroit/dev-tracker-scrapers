from io import StringIO

import sentry_sdk
from scrapy import signals
from supabase import create_client


class SupabaseExporterExtension:
    def __init__(self, url, key, table):
        self.scraped_items = []
        self.client = create_client(url, key)
        self.table = self.client.table(table)

    @classmethod
    def from_crawler(cls, crawler):
        extension = cls(
            crawler.settings.get("SUPABASE_URL"),
            crawler.settings.get("SUPABASE_KEY"),
            crawler.settings.get("SUPABASE_TABLE"),
        )
        crawler.signals.connect(extension.add_item, signal=signals.item_scraped)
        crawler.signals.connect(extension.spider_closed, signal=signals.spider_closed)

        return extension

    def spider_closed(self):
        self.table.upsert([self.scraped_items])

    def add_item(self, item):
        self.scraped_items.append(item)


class SentryErrors:
    def __init__(self, dsn):
        self.client = sentry_sdk.init(dsn=dsn)

    @classmethod
    def from_crawler(cls, crawler):
        extension = cls(dsn=crawler.settings.get("SENTRY_DSN"))
        crawler.signals.connect(extension.spider_error, signal=signals.spider_error)

    def spider_error(self, failure, response, spider):
        traceback = StringIO()
        failure.printTraceback(file=traceback)
        self.client.capture_message(
            message="[{}] {}".format(spider.name, repr(failure.value))
        )
