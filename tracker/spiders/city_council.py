import re
from datetime import datetime
from typing import List

import scrapy
from scrapy.http import Response

from tracker.items import TrackerEvent, TrackerLocation
from tracker.utils import clean_spaces, parse_addresses


class CityCouncilSpider(scrapy.Spider):
    name = "city_council"
    allowed_domains = ["pub-detroitmi.escribemeetings.com"]

    def start_requests(self):
        current_year = datetime.now().year
        for year in range(current_year, current_year + 2):
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
        for link in await page.locator(
            ".collapse .MeetingTypeContainer .itemResources a.link"
        ).all():
            url = await link.get_attribute("href")
            # Applies to both agendas and minutes
            if "Agenda=" in url:
                yield response.follow(url, meta={"source": "Detroit City Council"})

        planning_committee = "Planning and Economic Development Standing Committee"
        await page.locator(".PastMeetingTypesName").get_by_text(
            planning_committee
        ).click()
        await page.wait_for_selector(
            f'.collapse.show [meetingtype="{planning_committee}"]', state="visible"
        )
        for link in await page.locator(
            ".collapse .MeetingTypeContainer .itemResources a.link"
        ).all():
            url = await link.get_attribute("href")
            if "Agenda=" in url:
                yield response.follow(
                    url,
                    meta={
                        "source": "Detroit City Council Planning and Economic Development Committee"  # noqa
                    },
                )

    def parse(self, response: Response):
        body_slug = self._get_meeting_body_slug(response)
        dt = self._get_datetime(response)
        source_title = (
            response.css("title::text").extract_first().split(" - ")[0].strip()
        )
        for item in response.css(".AgendaItemContainer"):
            title = " ".join(item.css("h2 *::text").extract()).strip()
            if "Formal Session" in source_title and not any(
                w in title for w in ["BUDGET", "PLANNING"]
            ):
                continue
            for agenda_item in item.css(".AgendaItem"):
                agenda_num = " ".join(
                    agenda_item.css(".AgendaItemCounter *::text").extract()
                ).strip()
                if not agenda_num:
                    continue
                for row in agenda_item.css(".AgendaItemDescription p"):
                    content = clean_spaces(" ".join(row.css("*::text").extract()))
                    locations = self.parse_locations(content)
                    if len(locations) > 0 or "PILOT" in content:
                        yield TrackerEvent(
                            id=f"city_council/{dt.strftime('%Y/%m/%d')}/{body_slug}/{agenda_num}",  # noqa
                            source=response.meta["source"],
                            source_title=source_title,
                            date=dt.date(),
                            url=response.url,
                            content=content,
                            locations=locations,
                        )

    def parse_locations(self, content_str: str) -> List[TrackerLocation]:
        locations = []
        for address in parse_addresses(content_str):
            if not any(
                w in address.upper()
                for w in [
                    "LLC",
                    "ASSOCIATION",
                    "OFFICER",
                    "DETROIT CITY",
                    "FINANCIAL",
                    "BUDGET",
                    "EXEMPTION",
                    "APPLICATION",
                    "AGREEMENT",
                ]
            ):
                locations.append(TrackerLocation(address=address))
        return locations

    def _get_meeting_body_slug(self, response: Response) -> str:
        title = response.css("title::text").extract_first().strip()
        body_title = title.split("-")[0].strip()
        return re.sub(r"[^\d\w ]", "", body_title).lower().replace(" ", "_")

    def _get_datetime(self, response: Response) -> datetime:
        dt_str = response.css("time")[0].attrib["datetime"].strip()
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M")
