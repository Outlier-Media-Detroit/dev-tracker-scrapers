from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass
class TrackerLocation:
    pin: Optional[str] = None
    address: Optional[str] = None


@dataclass
class TrackerEvent:
    id: Optional[str]
    source: str
    date: date
    url: str
    content: str
    locations: List[TrackerLocation] = field(default_factory=list)
