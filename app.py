# Uses Flask to create a web application for generating line card PDFs based on region or state.
from flask import Flask, render_template, request, jsonify, send_from_directory
from datetime import datetime
import os
import logging
import traceback

from airtable_utils import fetch_airtable_records
from pdf_generator import generate_pdf
from pdf_generator_state import generate_pdf_state

logging.basicConfig(level=logging.INFO)

app = Flask(__name__, static_url_path='/static', static_folder='static')

# Ensure output folder exists (helps avoid 404s when serving generated PDFs)
os.makedirs("output", exist_ok=True)

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

@app.route("/", methods=["GET"])
def index():
    return render_template("input_form.html")

@app.route("/generate-pdf/regional", methods=["POST"])
def generate_regional_pdf():
    try:
        data = request.get_json()
        region = (data.get("region", "") or "").lower()
        include_images = data.get("include_products_image", False)

        if region not in REGION_STATE_MAP:
            return jsonify({"error": "Invalid region name."}), 400

        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"{region}_Linecard_{timestamp}.pdf"
        output_path = os.path.join("output", filename)

        airtable_records = fetch_airtable_records(region)
        generate_pdf(
            airtable_records,
            logo_path=f"assets/{region}Logo.jpg",
            output_path=output_path,
            region=region,
            include_products_image="yes" if include_images else "no"
        )

        return jsonify({
            "message": f"{region.title()} Line Card PDF generated successfully.",
            "path": output_path,
            "filename": filename
        })
    except Exception as e:
        logging.error("Error generating regional PDF: %s", traceback.format_exc())
        return jsonify({"error": "Server error generating PDF", "detail": str(e)}), 500

@app.route("/generate-pdf/state", methods=["POST"])
def generate_state_pdf():
    try:
        data = request.get_json()
        # Normalize underscores from the client (e.g. new_york -> new york)
        state = (data.get("state", "") or "").lower().replace("_", " ").strip()
        region = STATE_TO_REGION_MAP.get(state)

        if not region:
            return jsonify({"error": "Invalid state name."}), 400

        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"{state.replace(' ', '_')}_Linecard_{timestamp}.pdf"
        output_path = os.path.join("output", filename)

        airtable_records = fetch_airtable_records(region, state=state)
        generate_pdf_state(
            airtable_records,
            logo_path=f"assets/{region}Logo.jpg",
            output_path=output_path,
            region=region,
            state=state
        )

        return jsonify({
            "message": f"{state.title()} Line Card PDF generated successfully.",
            "path": output_path,
            "filename": filename
        })
    except Exception as e:
        logging.error("Error generating state PDF: %s", traceback.format_exc())
        return jsonify({"error": "Server error generating PDF", "detail": str(e)}), 500

@app.route("/output/<path:filename>")
def serve_output(filename):
    return send_from_directory("output", filename)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=False)
