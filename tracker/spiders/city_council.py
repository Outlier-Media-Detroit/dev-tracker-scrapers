from datetime import datetime

import scrapy
from scrapy.http import Response
from tracker.utils import clean_spaces, parse_addresses
from tracker.items import TrackerLocation, TrackerEvent
from typing import List


class CityCouncilSpider(scrapy.Spider):
    name = "city_council"
    allowed_domains = ["pub-detroitmi.escribemeetings.com"]

    def start_requests(self):
        current_year = datetime.now().year
        for year in range(current_year - 1, current_year + 1):
            yield scrapy.Request(
                "https://pub-detroitmi.escribemeetings.com",
                self._parse_events,
                meta={
                    "playwright": True,
                    "playwright_include_page": True,
                    "year": year,
                },
            )

    async def _parse_events(self, response: Response):
        page = response.meta["playwright_page"]
        await page.click("button[title=List]")
        await page.wait_for_url("**/?Year**")
        year_option_text = await page.locator(
            f".YearFilterOption [data-year='{response.meta['year']}']"
        ).inner_text()
        await page.locator(".YearFilterOption").select_option(year_option_text.strip())
        await page.wait_for_url(f"**/?Year={response.meta['year']}**")

        await page.locator(".PastMeetingTypesName").get_by_text(
            "City Council Formal Session"
        ).click()
        await page.locator(".collapse.show").wait_for()
        for link in await page.locator(".meeting-title-heading a").all():
            url = await link.get_attribute("href")
            yield response.follow(url)

    def parse(self, response: Response):
        dt_str = response.css("time")[0].attrib["datetime"].strip()
        dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
        for item in response.css(".AgendaItemContainer"):
            title = " ".join(item.css("h2 *::text").extract()).strip()
            if "BUDGET" not in title:
                continue
            for row in item.css(".AgendaItemContentRow .RichText p"):
                content = clean_spaces(" ".join(row.css("*::text").extract()))
                locations = self.parse_locations(content)
                if len(locations) > 0:
                    yield TrackerEvent(
                        id="city_council/TEST",  # TODO:
                        source="city_council",
                        date=dt.date(),
                        url=response.url,
                        content=content,
                        locations=locations,
                    )

    def parse_locations(self, content_str: str) -> List[TrackerLocation]:
        return [
            TrackerLocation(address=address) for address in parse_addresses(content_str)
        ]
