import re
from typing import Set

ADDRESS_PATTERN = r"((\b\d+(?=(,| & | and | or )))|(\b\d+(\s+[0-9A-Z]\w*\.?)+))"
PIN_PATTERN = r"\d{7,8}[.-]?[\dA-Z]*"


def clean_spaces(input_str: str) -> str:
    if not input_str:
        return ""
    return re.sub(r"\s+", " ", input_str).strip()


def parse_addresses(input_str: str) -> Set[str]:
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
    return set([a.replace(".", "") for a in addresses])
