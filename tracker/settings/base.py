import os

BOT_NAME = "tracker"

SPIDER_MODULES = ["tracker.spiders"]
NEWSPIDER_MODULE = "tracker.spiders"

USER_AGENT = "Outlier Media Development Tracker (https://outliermedia.org/)"

ROBOTSTXT_OBEY = False

COOKIES_ENABLED = False

DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

PLAYWRIGHT_LAUNCH_OPTIONS = {"headless": False}

ITEM_PIPELINES = {
    "tracker.pipelines.TrackerPipeline": 300,
}

AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = float(os.getenv("AUTOTHROTTLE_START_DELAY", 1.0))
AUTOTHROTTLE_MAX_DELAY = float(os.getenv("AUTOTHROTTLE_MAX_DELAY", 30.0))
AUTOTHROTTLE_TARGET_CONCURRENCY = float(
    os.getenv("AUTOTHROTTLE_TARGET_CONCURRENCY", 1.0)
)

EXTENSIONS = {
    "scrapy.extensions.closespider.CloseSpider": None,
}

CLOSESPIDER_ERRORCOUNT = 5

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"
