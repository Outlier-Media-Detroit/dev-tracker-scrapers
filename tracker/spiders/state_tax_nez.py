import re
from collections import defaultdict
from datetime import date, datetime
from io import BytesIO
from typing import List, Mapping, Tuple

import scrapy
from pdfminer.high_level import extract_text
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage

from tracker.items import TrackerEvent

COL_PREFIXES = [
    "APPL.",
    "CERT.",
    "NAME",
    "LOCAL",
    "COUNTY",
    "INVESTMENT",
    "EFFECTIVE",
    "EXPIRES",
    "REASON",
]


class StateTaxNezSpider(scrapy.Spider):
    name = "state_tax_nez"
    allowed_domains = ["www.michigan.gov"]
    start_urls = [
        "https://www.michigan.gov/treasury/local/stc/state-tax-commission-meeting-schedules"  # noqa
    ]
    user_agent = (
        "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0"
    )

    def parse(self, response):
        for schedule_url in response.css("#pagebody li a::attr(href)").extract()[:2]:
            yield scrapy.Request(
                response.urljoin(schedule_url), callback=self.parse_schedule_page
            )

    def parse_schedule_page(self, response):
        for row in response.css("#pagebody tr:not(:first-child)"):
            agenda_url = row.css("a::attr(href)").extract_first()
            if agenda_url is None:
                continue
            date_obj = datetime.strptime(
                " ".join(row.css("td:first-child *::text").extract())
                .split(" (")[0]
                .strip(),
                "%A, %B %d, %Y",
            ).date()
            yield scrapy.Request(
                response.urljoin(agenda_url),
                callback=self.parse_agenda,
                meta={"agenda_date": date_obj},
            )

    def parse_agenda(self, response):
        fp = BytesIO(response.body)
        for p in PDFPage.get_pages(fp):
            for a in p.annots or []:
                annot = a.resolve()
                uri = annot.get("A", {}).get("URI", b"").decode().lower()
                if uri and ".pdf" in uri:
                    yield scrapy.Request(
                        response.urljoin(uri),
                        callback=self.parse_agenda_detail,
                        meta={"agenda_date": response.meta["agenda_date"]},
                    )

    def parse_agenda_detail(self, response):
        agenda_text = extract_text(
            BytesIO(response.body),
            laparams=LAParams(char_margin=0.25),
        )
        for event in self.parse_events(
            agenda_text, response.url, response.meta["agenda_date"]
        ):
            yield event

    def parse_events(
        self, response_text: str, response_url: str, agenda_date: date
    ) -> List[Mapping]:
        chunks = [c.strip() for c in re.split(r"\n\n+", response_text)]
        columns = []
        items = []
        col_start_idx = -1

        description = None
        action_dict = None
        for idx, chunk in enumerate(chunks):
            if "AGENDA FOR" in chunk:
                col_start_idx = idx + 2
                continue
            if re.match(r"^\d+$", chunk):
                continue
            # TODO: Artificial stop, hacky
            if chunk.startswith("CHARITABLE"):
                if description is not None:
                    items.extend(
                        self.process_group_events(
                            description, action_dict, response_url, agenda_date
                        )
                    )
                columns = []
                description = None
                action_dict = None
                continue

            if chunk.startswith("NEIGHBORHOOD ENTERPRISE ZONE"):
                if description is not None:
                    items.extend(
                        self.process_group_events(
                            description,
                            action_dict,
                            response_url,
                            agenda_date,
                        )
                    )
                columns = []
                description = chunk
                action_dict = defaultdict(list)
                continue
            in_col_group = len(columns) > 0 and idx < (col_start_idx + len(columns))
            if action_dict is not None and (
                any(chunk.startswith(prefix) for prefix in COL_PREFIXES) or in_col_group
            ):
                group_title = columns[idx - col_start_idx] if in_col_group else ""
                group_items = [c.strip() for c in chunk.split("\n")]
                title, group = self.parse_group(group_items, group_title=group_title)
                if title not in action_dict:
                    columns.append(title)

                action_dict[title].extend(group)

        return items

    def parse_group(
        self, group: List[str], group_title: str = ""
    ) -> Tuple[str, List[str]]:
        data_idx = 0 if group_title != "" else 1
        if (
            group[0] == "APPL."
            or group[0].startswith("EXPIRES")
            or group[0].startswith("EFFECTIVE")
        ):
            data_idx = 2
        title = " ".join(group[:data_idx]) or group_title
        return title, group[data_idx:]

    def process_group_events(
        self,
        description: str,
        action_dict: Mapping,
        response_url: str,
        response_date: date,
    ) -> List[Mapping]:
        items = []
        id_key = [key for key in action_dict.keys() if "NO." in key][0]
        for idx in range(len(action_dict[id_key])):
            if (
                idx >= len(action_dict["LOCAL UNIT"])
                or "Detroit" not in action_dict["LOCAL UNIT"][idx]
            ):
                continue
            id_val = action_dict[id_key][idx].split(" ")[0]
            action_text = self.get_action_from_description(description)
            action_item = {}
            for key in action_dict.keys():
                if idx < len(action_dict[key]):
                    action_item[key] = action_dict[key][idx]

            items.append(
                TrackerEvent(
                    id=f"state_tax_nez/{response_date.strftime('%Y/%m/%d')}/{id_val}",
                    source="state_tax_nez",
                    source_title=f"NEZ {action_text}: {id_val}",
                    date=response_date,
                    url=response_url,
                    content="\n".join(f"{k}: {v}" for k, v in action_item.items()),
                )
            )
        return items

    def get_action_from_description(self, description: str) -> str:
        desc = re.sub(r"\s+", " ", description).strip().upper()
        # Parse whether extension, initial
        if "PRELIMINARY APPROVAL" in desc:
            return "Preliminary approval"
        if "EXTENSION ACKNOWLEDGEMENT" in desc:
            return "Extension"
        if "REMOVE CERTIFICATES FROM ABEYANCE" in desc:
            return "Approval"
        if "TRANSFER APPLICATIONS FOR APPROVAL" in desc:
            return "Transfer approval"
