from typing import Optional

import requests
from shapely.geometry import shape

from .items import TrackerLocation


class DetroitAddressAPI:
    ADDRESS_ENDPOINT = "https://opengis.detroitmi.gov/opengis/rest/services/Geocoders/CompositeGeocoder/GeocodeServer/findAddressCandidates"  # noqa
    PIN_ENDPOINT = "https://services2.arcgis.com/qvkbeam7Wirps6zC/arcgis/rest/services/Parcels_Current/FeatureServer/0/query"  # noqa

    @staticmethod
    def get_location_from_address(address: str) -> Optional[TrackerLocation]:
        try:
            res = requests.get(
                DetroitAddressAPI.ADDRESS_ENDPOINT,
                params={
                    "SingleLine": address,
                    "outFields": "*",
                    "outSR": 4326,
                    "f": "pjson",
                },
            )
            data = res.json()
        except Exception:
            return

        return DetroitAddressAPI._get_location_from_address(data)

    @staticmethod
    def get_location_from_pin(pin: str) -> Optional[TrackerLocation]:
        try:
            res = requests.get(
                DetroitAddressAPI.PIN_ENDPOINT,
                params={
                    "where": f"parcel_number='{pin}'",
                    "outFields": "*",
                    "outSR": 4326,
                    "f": "geojson",
                },
            )
            data = res.json()
        except Exception:
            return

        return DetroitAddressAPI._get_location_from_pin(data)

    @staticmethod
    def _get_location_from_address(data: dict) -> Optional[TrackerLocation]:
        if len(data["candidates"]) == 0:
            return

        candidate = data["candidates"][0]["attributes"]
        return TrackerLocation(
            candidate["parcel_id"],
            candidate["ShortLabel"],
            candidate["X"],
            candidate["Y"],
        )

    @staticmethod
    def _get_location_from_pin(data: dict) -> Optional[TrackerLocation]:
        if len(data["features"]) == 0:
            return

        feature = data["features"][0]["properties"]
        centroid = shape(data["features"][0]["geometry"]).centroid
        return TrackerLocation(
            feature["parcel_number"], feature["address"], centroid.x, centroid.y
        )
