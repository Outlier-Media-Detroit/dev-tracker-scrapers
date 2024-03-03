from io import StringIO

import sentry_sdk
from scrapy import Spider, signals
from sentry_sdk import Client as SentryClient
from twisted.python.failure import Failure


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
