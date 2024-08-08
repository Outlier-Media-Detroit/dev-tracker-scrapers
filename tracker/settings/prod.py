import os

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

from .base import *  # noqa

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE = os.getenv("SUPABASE_TABLE", "tracker_events")

EXTENSIONS = {
    "tracker.extensions.SentryErrors": 10,
    "tracker.extensions.SupabaseExporterExtension": 100,
    "scrapy.extensions.closespider.CloseSpider": None,
}

SENTRY_DSN = os.getenv("SENTRY_DSN")

if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[LoggingIntegration(level=None, event_level="ERROR")],
        traces_sample_rate=1.0,
    )

PLAYWRIGHT_LAUNCH_OPTIONS = {"headless": True}
