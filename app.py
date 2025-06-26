# app.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
from fastapi.staticfiles import StaticFiles

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
    
    airtable_records = fetch_airtable_records(region)
    generate_pdf(
        airtable_records,
        logo_path=f"assets/{region}Logo.jpg",
        output_path="output/line_card.pdf",
        region=region,
        include_products_image="yes" if request.include_products_image else "no"
    )
    return {"message": f"{region.title()} Line Card PDF generated successfully.", "path": "output/line_card.pdf"}

@app.post("/generate-pdf/state")
def generate_state_pdf(request: StatePDFRequest):
    state = request.state.lower()
    region = STATE_TO_REGION_MAP.get(state)
    if not region:
        raise HTTPException(status_code=400, detail="Invalid state name.")
    
    airtable_records = fetch_airtable_records(region, state=state)
    generate_pdf_state(
        airtable_records,
        logo_path=f"assets/{region}Logo.jpg",
        output_path="output/line_card.pdf",
        region=region,
        state=state
    )
    return {"message": f"{state.title()} Line Card PDF generated successfully.", "path": "output/line_card.pdf"}
