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
    Returns a list of records.
    """
    # Airtable API Setup using the Marketing Base/Line-Card-Item Table

    url = "https://api.airtable.com/v0/appDsGXHk2qjpghDU/tblSsgAiKeTkRTTxn"
    pat = os.getenv("AIRTABLE_PAT")  # Personal access token ID with read and write access
    headers = {"Authorization": f"Bearer {pat}"}  # "Authorization: Bearer YOUR_TOKEN"

    all_records = [] # List to hold all records
    params = {}     # Parameters for pagination

    # Gets all records with pagination
    # Airtable API returns a maximum of 100 records per request, so we need to  
    # loop through the pages until we get all records
    while True:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        all_records.extend(data.get("records", []))

        # Check if there's another page
        offset = data.get("offset")
        if offset:
            params["offset"] = offset
        else:
            break

    # Filter records by region
    filtered = [r["fields"] for r in all_records if any(region.lower() == reg.lower() for reg in r["fields"].get("Region", []))]

    # If filtering by state to further narrow down
    if state:
        filtered = [
            r for r in filtered
            if state.lower() in([s.strip().lower() for s in r.get("Manufacturer States", [])] 
                                if isinstance(r.get("Manufacturer States", ""), list)
                                else [s.strip().lower() for s in r.get("Manufacturer States", "").split(",")]
                )
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
        
    """Now all Comapnies should be in a dictionary with parent companies' records as keys and their children's records as values."""
    return dict(sorted(grouped.items(), key=lambda x: x[0].lower()))