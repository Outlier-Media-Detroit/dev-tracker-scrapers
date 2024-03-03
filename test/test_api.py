import pytest  # noqa

from tracker.items import TrackerLocation
from tracker.api import DetroitAddressAPI


def test_get_location_address_valid():
    location = DetroitAddressAPI._get_location_from_address(
        {
            "candidates": [
                {
                    "attributes": {
                        "ShortLabel": "1 Woodward Ave",
                        "parcel_id": "02001910-5",
                        "X": -83.045475,
                        "Y": 42.32890800000001,
                    }
                }
            ]
        }
    )
    assert location == TrackerLocation(
        "02001910-5", "1 Woodward Ave", -83.045475, 42.32890800000001
    )


def test_get_location_address_empty():
    location = DetroitAddressAPI._get_location_from_address({"candidates": []})
    assert location is None


def test_get_location_pin_valid():
    location = DetroitAddressAPI._get_location_from_pin(
        {
            "features": [
                {
                    "properties": {
                        "parcel_number": "02001910-5",
                        "address": "1 WOODWARD AVE",
                    },
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [-83.045829, 42.3290542],
                                [-83.0454114, 42.3292309],
                                [-83.0450385999999, 42.3287569],
                                [-83.0454539, 42.3285772],
                                [-83.045829, 42.3290542],
                            ]
                        ],
                    },
                }
            ],
        }
    )
    assert location == TrackerLocation(
        "02001910-5", "1 WOODWARD AVE", -83.04543343924747, 42.32890470268001
    )


def test_get_location_pin_empty():
    location = DetroitAddressAPI._get_location_from_pin({"features": []})
    assert location is None
