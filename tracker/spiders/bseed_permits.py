import json
from datetime import datetime
from typing import Mapping

import scrapy
from scrapy.http import Response

from tracker.items import TrackerEvent, TrackerLocation


class BseedPermitsSpider(scrapy.Spider):
    name = "bseed_permits"
    start_urls = [
        "https://services2.arcgis.com/qvkbeam7Wirps6zC/arcgis/rest/services/building_permits_2023/FeatureServer/0/query?outFields=*&where=1%3D1&f=geojson"  # noqa
    ]

    def parse(self, response: Response):
        res = json.loads(response.body)
        for feature in res["features"]:
            rec = feature["properties"]
            if not self._should_include(rec):
                continue
            location = TrackerLocation(pin=rec["parcel_id"])
            dt = datetime.fromtimestamp(rec["issued_date"] / 1000)
            yield TrackerEvent(
                id=f"bseed_permits/{rec['record_id']}",
                source="bseed_permits",
                date=dt.date(),
                url="",
                content="",  # TODO:,
                locations=[location],
            )

    def _should_include(self, rec: Mapping) -> bool:
        return rec.get("contractor_est_cost") and rec["contractor_est_cost"] > 200_000
