import json
from datetime import datetime

import scrapy

from tracker.items import TrackerEvent, TrackerLocation


class MedcIncentivesSpider(scrapy.Spider):
    name = "medc_incentives"
    allowed_domains = ["gisp.mcgi.state.mi.us"]
    start_urls = [
        "https://gisp.mcgi.state.mi.us/arcgis/rest/services/MEDC/Incentives/MapServer/0/query?f=json&where=1=1%20AND%20County%20=%20163&outFields=*&outSR=4326"  # noqa
    ]

    def parse(self, response):
        res = json.loads(response.body)
        for feature in res["features"]:
            rec = feature["attributes"]
            if not rec.get("ProjectCity", "").upper() == "DETROIT":
                continue
            dt = datetime.fromtimestamp(rec["Project_Close_Date"] / 1000)
            yield TrackerEvent(
                id=f"medc_incentives/{rec['ProjID']}",
                source="medc_incentives",
                source_title=rec["Project_Name"],
                date=dt.date(),
                url="https://maps.michiganbusiness.org/",
                content=rec["Project_Highlight"],
                locations=[
                    TrackerLocation(
                        address=f"{rec['ProjectAddress']} Detroit, MI {rec['ProjectZipCode']}",  # noqa
                        lon=feature["geometry"]["x"],
                        lat=feature["geometry"]["y"],
                    )
                ],
            )
