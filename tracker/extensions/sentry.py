from io import StringIO

import sentry_sdk
from scrapy import Spider, signals
from sentry_sdk import capture_message
from sentry_sdk.integrations.logging import LoggingIntegration
from twisted.python.failure import Failure


class SentryErrors:
    def __init__(self, dsn):
        sentry_sdk.init(
            dsn=dsn,
            integrations=[LoggingIntegration(level=None, event_level="ERROR")],
            traces_sample_rate=1.0,
        )

    @classmethod
    def from_crawler(cls, crawler):
        extension = cls(dsn=crawler.settings.get("SENTRY_DSN"))
        crawler.signals.connect(extension.spider_error, signal=signals.spider_error)
        return extension

    def spider_error(self, failure: Failure, response, spider: Spider):
        traceback = StringIO()
        failure.printTraceback(file=traceback)
        capture_message(message="[{}] {}".format(spider.name, repr(failure.value)))
