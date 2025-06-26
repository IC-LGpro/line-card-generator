# This program contains the main logic for generating PDF line cards based on user input.
# It allows users to generate either regional or state-specific line cards by fetching records from Airtable
# and generating PDFs with the relevant information.
#  Imports
from airtable_utils import fetch_airtable_records
from pdf_generator import generate_pdf
from pdf_generator_state import generate_pdf_state

def main():

  REGION_STATE_MAP = {
    "midwest": ["illinois", "indiana", "michigan", "wisconsin"],
    "west": ["california", "nevada", "arizona", "hawaii", "new mexico", "hawaii"],
    "east": ["florida", "georgia","alabama","tennessee", "kentucky", "north carolina", "south carolina", "virginia", 
             "new york", "massachusetts", "connecticut", "ohio", "pennsylvania", "new jersey", "maryland", "delaware", 
             "rhode island", "maine", "new hampshire", "vermont", "west virginia"],
    "southwest": ["texas", "arkansas", "oklahoma", "louisiana", "mississippi"],
    "north central": ["minnesota", "north dakota","south dakota", "iowa", "nebraska", "kansas", "missouri"],
    "pacific northwest": ["oregon", "washington", "alaska"],
    "rockies": ["colorado", "utah", "montana", "wyoming", "idaho"]
}
  
  # Reverse the REGION_STATE_MAP to map states to regions
  STATE_TO_REGION_MAP = {
    state: region
    for region, states in REGION_STATE_MAP.items()
    for state in states
    }
  
  pdf_type = input("Enter the PDF type (state or regional): ").strip().lower()
  
  if pdf_type == 'regional':
    # Filter by region
    region = input("Enter the region (East, Midwest, North Central, Pacific Northwest, Rockies, Southwest, West): ").strip().lower()
    include_products_image = input("Would you like to include product images? (yes/no): ").strip().lower() #Option to include product images in the PDF
    # Gets airtable records and sorts them into groups of parents and children companies w/ logos, and descriptions 
    airtable_records = fetch_airtable_records(region)
    generate_pdf(airtable_records, 
                 logo_path=f"assets/{region}Logo.jpg", 
                 output_path=f"output/line_card.pdf", 
                 region=region, 
                 include_products_image=include_products_image)
  elif pdf_type == 'state':
    state = input("Enter a state: ").strip().lower()
    region = STATE_TO_REGION_MAP.get(state)

    if not region:
        print("Invalid state selection.")
        return

    airtable_records = fetch_airtable_records(region, state=state)
    generate_pdf_state(
        airtable_records,
        logo_path=f"assets/{region}Logo.jpg",
        output_path=f"output/line_card.pdf",
        region=region,
        state=state
    )


'''if __name__ == "__main__":
  main()'''