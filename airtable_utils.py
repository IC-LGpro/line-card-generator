# airtable_utils.py
# This file contains utility functions for fetching records from Airtable.
# It includes functions to handle pagination, filtering by region and state, and grouping records by parent
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def fetch_airtable_records(region, state=None):
    """
    Fetch all records from the Airtable table with pagination.
    Returns a dictionary grouped by parent company.
    Raises exceptions with helpful messages on failure.
    """
    url = "https://api.airtable.com/v0/appDsGXHk2qjpghDU/tblSsgAiKeTkRTTxn"
    pat = os.getenv("AIRTABLE_PAT")  # Personal access token ID with read and write access
    if not pat:
        raise RuntimeError("Missing AIRTABLE_PAT environment variable")

    headers = {"Authorization": f"Bearer {pat}"}

    all_records = []
    params = {}

    # pagination loop
    while True:
        resp = requests.get(url, headers=headers, params=params, timeout=30)
        if resp.status_code != 200:
            # bubble up helpful error
            raise RuntimeError(f"Airtable API returned status {resp.status_code}: {resp.text}")
        data = resp.json()
        all_records.extend(data.get("records", []))

        offset = data.get("offset")
        if offset:
            params["offset"] = offset
        else:
            break

    # Filter records by region
    filtered = [r["fields"] for r in all_records if any(region.lower() == reg.lower() for reg in r["fields"].get("Region", []))]

    # If filtering by state to further narrow down
    if state:
        def normalize_manufacturer_states(val):
            if isinstance(val, list):
                return [s.strip().lower() for s in val]
            elif isinstance(val, str):
                return [s.strip().lower() for s in val.split(",")]
            else:
                return []

        filtered = [
            r for r in filtered
            if state.lower() in normalize_manufacturer_states(r.get("Manufacturer States", ""))
        ]

    # Group by parent company
    grouped = {}

    for record in filtered:
        name = record.get("Manufacturer Names", "Unknown Manufacturer")
        parent = record.get("Parent", name)

        if parent not in grouped:
            grouped[parent] = {
                "parent": None,
                "children": []}
        if name == parent:
            grouped[parent]["parent"] = record
        else:
            grouped[parent]["children"].append(record)

    return dict(sorted(grouped.items(), key=lambda x: x[0].lower()))