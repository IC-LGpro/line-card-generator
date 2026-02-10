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

# Ensure output and temp folders exist (helps avoid 404s when serving generated PDFs)
os.makedirs("output", exist_ok=True)

# Ensure static/assets and static/assets/temp_logos exist (use app.static_folder for robust absolute paths)
static_assets_dir = os.path.join(app.static_folder, "assets")
static_temp_logos = os.path.join(static_assets_dir, "temp_logos")
os.makedirs(static_assets_dir, exist_ok=True)
os.makedirs(static_temp_logos, exist_ok=True)

# Maps for region and state
REGION_STATE_MAP = {
    "midwest": ["illinois", "indiana", "michigan", "wisconsin"],
    "west": ["california", "nevada", "hawaii", "new mexico"],
    "east": ["florida", "georgia", "alabama", "tennessee", "kentucky", "north carolina", "south carolina", "virginia",
             "new york", "massachusetts", "connecticut", "ohio", "pennsylvania", "new jersey", "maryland", "delaware",
             "rhode island", "maine", "new hampshire", "vermont", "west virginia"],
    "southwest": ["texas", "arkansas", "oklahoma", "louisiana", "mississippi", "arizona", "tennessee"],
    "north central": ["minnesota", "north dakota", "south dakota", "iowa", "nebraska", "kansas", "missouri"],
    "pacific northwest": ["oregon", "washington", "alaska"],
    "rockies": ["colorado", "utah", "montana", "wyoming", "idaho"]
}

STATE_TO_REGION_MAP = {
    state: region
    for region, states in REGION_STATE_MAP.items()
    for state in states
}

@app.before_request
def log_request():
    try:
        logging.info("Incoming request: %s %s from %s", request.method, request.path, request.remote_addr)
        # Log small payloads for diagnostics
        data = request.get_data(as_text=True)
        if data:
            logging.info("Payload: %s", data[:200])
    except Exception:
        logging.exception("Error while logging request")

@app.route("/", methods=["GET"])
def index():
    return render_template("input_form.html")

@app.route("/generate-pdf/regional", methods=["POST", "GET", "OPTIONS"])
def generate_regional_pdf():
    # If a non-POST reached this endpoint, return a JSON explanation (helps debugging when JS isn't running)
    if request.method != "POST":
        return jsonify({"error": "Method not allowed. This endpoint expects a POST with JSON body."}), 405

    try:
        data = request.get_json(silent=True) or {}
        region = (data.get("region", "") or "").lower()

        if region not in REGION_STATE_MAP:
            return jsonify({"error": "Invalid region name."}), 400

        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"{region}_Linecard_{timestamp}.pdf"
        output_path = os.path.join("output", filename)

        airtable_records = fetch_airtable_records(region)
        logging.info("Regional PDF request for region=%s returned %d grouped records", region, len(airtable_records or {}))
        if not airtable_records:
            return jsonify({"error": "No records found for region"}), 404

        # generate_pdf now uses assets for header/footer; product-image option removed
        generate_pdf(
            airtable_records,
            output_path=output_path,
            region=region
        )

        # Return a web-accessible URL path (not the filesystem path)
        url_path = f"/output/{filename}"

        return jsonify({
            "message": f"{region.title()} Line Card PDF generated successfully.",
            "path": url_path,
            "url": url_path,
            "filename": filename
        })
    except Exception as e:
        logging.error("Error generating regional PDF: %s", traceback.format_exc())
        return jsonify({"error": "Server error generating PDF", "detail": str(e)}), 500

@app.route("/generate-pdf/state", methods=["POST", "GET", "OPTIONS"])
def generate_state_pdf():
    if request.method != "POST":
        return jsonify({"error": "Method not allowed. This endpoint expects a POST with JSON body."}), 405

    try:
        data = request.get_json(silent=True) or {}
        # Normalize underscores from the client (e.g. new_york -> new york)
        state = (data.get("state", "") or "").lower().replace("_", " ").strip()
        region = STATE_TO_REGION_MAP.get(state)

        if not region:
            return jsonify({"error": "Invalid state name."}), 400

        timestamp = datetime.now().strftime("%Y%m%d")
        filename = f"{state.replace(' ', '_')}_Linecard_{timestamp}.pdf"
        output_path = os.path.join("output", filename)

        airtable_records = fetch_airtable_records(region, state=state)
        logging.info("State PDF request for state=%s region=%s returned %d grouped records", state, region, len(airtable_records or {}))
        if not airtable_records:
            return jsonify({"error": "No records found for state"}), 404

        # generate_pdf_state now accepts region + state and uses assets for header/footer and state label
        generate_pdf_state(
            airtable_records,
            output_path=output_path,
            region=region,
            state=state
        )

        url_path = f"/output/{filename}"

        return jsonify({
            "message": f"{state.title()} Line Card PDF generated successfully.",
            "path": url_path,
            "url": url_path,
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
