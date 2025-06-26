# app.py
# This FastAPI application serves a form for generating PDF line cards based on regions or states.
# It allows users to select a region or state, fetches records from Airtable, and generates PDFs with the relevant information.
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from fastapi.staticfiles import StaticFiles
from datetime import datetime

from airtable_utils import fetch_airtable_records
from pdf_generator import generate_pdf
from pdf_generator_state import generate_pdf_state

from fastapi.responses import HTMLResponse

app = FastAPI()

@app.get("/", response_class=HTMLResponse)
def serve_form():
    with open("input_form.html", "r") as f:
        return f.read()
    
# Mount the output directory to serve static files
app.mount("/output", StaticFiles(directory="output"), name="output")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Maps for region and state
REGION_STATE_MAP = {
    "midwest": ["illinois", "indiana", "michigan", "wisconsin"],
    "west": ["california", "nevada", "arizona", "hawaii", "new mexico", "hawaii"],
    "east": ["florida", "georgia", "alabama", "tennessee", "kentucky", "north carolina", "south carolina", "virginia",
             "new york", "massachusetts", "connecticut", "ohio", "pennsylvania", "new jersey", "maryland", "delaware",
             "rhode island", "maine", "new hampshire", "vermont", "west virginia"],
    "southwest": ["texas", "arkansas", "oklahoma", "louisiana", "mississippi"],
    "north central": ["minnesota", "north dakota", "south dakota", "iowa", "nebraska", "kansas", "missouri"],
    "pacific northwest": ["oregon", "washington", "alaska"],
    "rockies": ["colorado", "utah", "montana", "wyoming", "idaho"]
}

STATE_TO_REGION_MAP = {
    state: region
    for region, states in REGION_STATE_MAP.items()
    for state in states
}

# Request models
class RegionalPDFRequest(BaseModel):
    region: str
    include_products_image: Optional[bool] = False
class StatePDFRequest(BaseModel):
    state: str

@app.post("/generate-pdf/regional")
def generate_regional_pdf(request: RegionalPDFRequest):
    region = request.region.lower()
    if region not in REGION_STATE_MAP:
        raise HTTPException(status_code=400, detail="Invalid region name.")
    
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"{region}_Linecard_{timestamp}.pdf"

    airtable_records = fetch_airtable_records(region)
    generate_pdf(
        airtable_records,
        logo_path=f"assets/{region}Logo.jpg",
        output_path = f"output/{filename}",
        region=region,
        include_products_image="yes" if request.include_products_image else "no"
    )
    return {
    "message": f"{region.title()} Line Card PDF generated successfully.",
    "path": f"output/{filename}",
    "filename": filename
    }


@app.post("/generate-pdf/state")
def generate_state_pdf(request: StatePDFRequest):
    state = request.state.lower()
    region = STATE_TO_REGION_MAP.get(state)
    if not region:
        raise HTTPException(status_code=400, detail="Invalid state name.")
    
    timestamp = datetime.now().strftime("%Y%m%d")
    filename = f"{state}_Linecard_{timestamp}.pdf"

    airtable_records = fetch_airtable_records(region, state=state)
    generate_pdf_state(
        airtable_records,
        logo_path=f"assets/{region}Logo.jpg",
        output_path = f"output/{filename}",
        region=region,
        state=state
    )
    return {
    "message": f"{state.title()} Line Card PDF generated successfully.",
    "path": f"output/{filename}",
    "filename": filename
    }



# To run the FastAPI app, use the command:
# uvicorn app:app --reload