from datetime import datetime

import scrapy


class CityCouncilSpider(scrapy.Spider):
    name = "city_council"
    allowed_domains = ["pub-detroitmi.escribemeetings.com"]

    def start_requests(self):
        current_year = datetime.now().year
        for year in range(current_year - 1, current_year + 1):
            yield scrapy.Request(
                f"https://pub-detroitmi.escribemeetings.com?Year={year}&Expanded=City Council Formal Session",  # noqa
                self.parse,
            )

    def parse(self, response):
        pass
