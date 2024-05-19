from scrapy import Spider

from .api import DetroitAddressAPI
from .items import TrackerEvent, TrackerLocation


class TrackerPipeline:
    def process_item(self, item: TrackerEvent, spider: Spider) -> TrackerEvent:
        clean_locations = []
        for location in item.locations:
            loc = self.clean_location(location)
            # Make sure PIN isn't already included
            if loc and not (
                loc.pin
                and len(loc.pin) > 0
                and any(cl.pin == loc.pin for cl in clean_locations)
            ):
                clean_locations.append(loc)
        item.locations = clean_locations
        return item

    def clean_location(self, location: TrackerLocation) -> TrackerLocation:
        cleaned_loc = None
        if location.pin:
            cleaned_loc = DetroitAddressAPI.get_location_from_pin(location.pin)
        # Try address if exists and PIN doesn't return a response
        if location.address and not cleaned_loc:
            cleaned_loc = DetroitAddressAPI.get_location_from_address(location.address)
        # Ignore odd matchesfor invalid locations
        if cleaned_loc and (".0000" in cleaned_loc.address or cleaned_loc.lon > 0):
            return
        # Only include location if API matches
        return cleaned_loc
