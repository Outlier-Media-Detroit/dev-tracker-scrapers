import re
from io import BytesIO, StringIO
from typing import List

import requests
import scrapy
from pdfminer.high_level import extract_text_to_fp
from pdfminer.layout import LAParams


# Visit all links on starter page before going deeper
# https://www.reddit.com/r/webscraping/comments/ptum2u/scrapy_is_processing_links_from_next_page_before/
class BrownfieldSpider(scrapy.Spider):
    name = "brownfield"
    allowed_domains = ["www.degc.org"]
    start_urls = ["https://www.degc.org/dbra/"]
    USER_AGENT = (
        "Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0"
    )

    # def parse(self, response):
    #     pass

    # def load_plans(self, response):
    def parse(self, response):
        # TODO: There are documents with each active plan, potentially only work on
        # active plans, load the PINs related to them, then store a mapping rather than
        # a pipeline?
        plan_dict = {}
        for group in response.css(".accordion-block .accordion-row"):
            label_text = " ".join(group.css(".accordion-label *::text").extract())
            if "PLANS UNDER CONSIDERATION" not in label_text.upper():
                continue
            for plan_link in group.css("a"):
                plan_title = (
                    plan_link.xpath("./text()")
                    .extract_first()
                    .replace(" BROWNFIELD PLAN", "")
                    .strip()
                )
                plan_dict[plan_title] = response.urljoin(
                    plan_link.xpath("@href").extract_first()
                )
        for plan_name, plan_url in plan_dict.items():
            # TODO:
            print(plan_url)
            res = requests.get(plan_url, headers={"User-Agent": self.USER_AGENT})
            pdf_str = self.parse_pdf(res.content)
            print(plan_name)
            print(self.parse_pins(pdf_str))

    def parse_pdf(self, response_bytes: bytes) -> str:
        lp = LAParams(line_margin=0.1)
        out_str = StringIO()
        extract_text_to_fp(BytesIO(response_bytes), out_str, laparams=lp)
        return out_str.getvalue()

    def parse_pins(self, body_text: str) -> List[str]:
        pin_results = re.findall(r"\d{7,8}[.-]?[\dA-Z]*", body_text)
        pins = []
        for result in pin_results:
            if not any(c in result for c in [".", "-"]):
                pins.append(f"{result.zfill(8)}.")
            else:
                pins.append(result)
        return list(set(pins))
