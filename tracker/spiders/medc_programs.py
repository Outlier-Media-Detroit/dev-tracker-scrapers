import re
from datetime import datetime

import scrapy

from tracker.items import TrackerEvent


class MedcProgramsSpider(scrapy.Spider):
    name = "medc_programs"
    allowed_domains = ["www.michiganbusiness.org"]
    start_urls = [
        "https://www.michiganbusiness.org/reports-data/brownfield-tax-increment-financing-projects/",  # noqa
        "https://www.michiganbusiness.org/reports-data/strategic-site-readiness-program/",  # noqa
        "https://www.michiganbusiness.org/reports-data/michigan-community-revitalization-program-projects/",  # noqa
        "https://www.michiganbusiness.org/reports-data/michigan-loan-portfolio/",
        "https://www.michiganbusiness.org/reports-data/michigan-community-cdbg-program-projects/",  # noqa
        "https://www.michiganbusiness.org/reports-data/michigan-business-development-program-projects/",  # noqa
    ]

    def parse(self, response):
        yield from self.parse_table(response)

        next_link = response.css("a[aria-label='Next Page']")
        if len(next_link) > 0:
            yield response.follow(next_link[0].xpath("@href").extract_first())

    def parse_table(self, response):
        source = self.parse_source(response.url)
        for item in response.css("main .bg-light .col-12"):
            title = " ".join(item.css("p::text").extract()).strip()
            date_str = ""
            dt = None
            content_dict = {}
            for row in item.css("tr"):
                label = row.css("th::text").extract_first().strip()
                value = row.css("td::text").extract_first()
                if value:
                    value = value.strip()
                else:
                    value = ""
                content_dict[label] = value
                if "Date" in label:
                    dt = datetime.strptime(value, "%b %d, %Y").date()
                    date_str = dt.strftime("%Y/%m/%d")

            if not any(
                ("Detroit" in value) or ("Wayne" in value)
                for value in content_dict.values()
            ):
                continue

            yield TrackerEvent(
                id=f"medc_programs/{self.slugify(source)}/{date_str}/{self.slugify(title)}",  # noqa
                source=source,
                source_title=title,
                date=dt,
                url=response.url,
                content="\n".join(f"{k} {v}" for k, v in content_dict.items()),
                locations=[],
            )

    def parse_source(self, url: str) -> str:
        if "brownfield" in url:
            return "Brownfield Tax Increment Financing"
        if "strategic" in url:
            return "Strategic Site Readiness Program"
        if "revitalization" in url:
            return "Community Revitalization Program"
        if "loan-portfolio" in url:
            return "MBDP and MCRP Loan Portfolio"
        if "cdbg" in url:
            return "Community Development Block Grants"
        if "business-development" in url:
            return "Business Development Program"
        return "MEDC"

    def slugify(self, value: str) -> str:
        return re.sub(r"[^a-z0-9 ]", "", value.lower()).replace(" ", "_")
