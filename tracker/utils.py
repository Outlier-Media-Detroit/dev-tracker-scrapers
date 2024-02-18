import re
from typing import List

import requests

from tracker.items import TrackerLocation

ADDRESS_PATTERN = r"((\b\d+(?=(,| and | or )))|(\b\d+(\s+[A-Z]\w*\.?)+))"


def clean_spaces(input_str: str) -> str:
    if not input_str:
        return ""
    return re.sub(r"\s+", " ", input_str).strip()


def parse_addresses(input_str: str) -> List[str]:
    matches = re.findall(ADDRESS_PATTERN, input_str)
    addresses = []
    chunks = []
    for match in matches:
        if match[1]:
            chunks.append(match[0])
        else:
            street_name = " ".join(match[0].split(" ")[1:])
            for addr_num in chunks:
                addresses.append(f"{addr_num} {street_name}")
            addresses.append(match[0])
            chunks = []
    return addresses


# TODO: Throttle this, run at end only for addresses without PINs
def get_pin(address: str) -> TrackerLocation:
    location = TrackerLocation(None, address)
    res = requests.get(
        "https://opengis.detroitmi.gov/opengis/rest/services/Geocoders/CompositeGeocoder/GeocodeServer/findAddressCandidates",  # noqa
        params={
            "SingleLine": address,
            "outSR": 4326,
            "outFields": "*",
            "f": "pjson",
            "Street": "",
            "City": "",
            "ZIP": "",
            "category": "",
            "maxLocations": "",
            "searchExtent": "",
            "location": "",
            "distance": "",
            "magicKey": "",
        },
    )
    data = res.json()
    candidates = [
        c
        for c in sorted(data["candidates"], key=lambda c: c["score"], reverse=True)
        if c["attributes"].get("Loc_name") != "StreetCenterli"
    ]

    # TODO: Should this return location directly?
    if len(candidates) > 0:
        location.address = candidates[0].get("ShortLabel")
        location.pin = candidates[0].get("attributes", {}).get("parcel_id")
    return location
