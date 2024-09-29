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
                source="Detroit BSEED Permits",
                source_title="",
                date=dt.date(),
                url="",
                content=self.get_content(rec),
                locations=[location],
            )

    def get_content(self, rec: Mapping) -> str:
        contractor_est_cost = rec.get("contractor_est_cost")
        if contractor_est_cost:
            contractor_est_cost = f"{float(contractor_est_cost):,.2f}"
        else:
            contractor_est_cost = "N/A"

        return "\n".join(
            [
                f"Date Issued: {datetime.fromtimestamp(rec['issued_date'] / 1000).strftime('%B %e, %Y')}",  # noqa
                f"Building Legal Use: {rec.get('current_legal_use') or 'N/A'}",
                f"Proposed Use: {rec.get('proposed_use') or 'N/A'}",
                f"Permit Type: {rec.get('permit_type') or 'N/A'}",
                f"Description of Work: {rec.get('description_of_work') or 'N/A'}",
                f"Contractor Estimated Cost: {contractor_est_cost}",
                f"Stories: {rec.get('stories') or 'N/A'}",
                f"Zoning Code: {rec.get('zoning_district') or 'N/A'}",
                f"Type of Construction: {rec.get('type_of_construction') or 'N/A'}",
            ]
        )

    def _should_include(self, rec: Mapping) -> bool:
        return (
            rec.get("permit_type")
            in ["New", "Add Additional Occupancy/Use", "Change of Occupancy/Use"]
            or rec.get("change_in_units") == "Yes"
        )
