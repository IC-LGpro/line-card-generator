# Imports
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
  pdf_type = input("Enter the PDF type (state or regional): ").strip().lower()
  
  if pdf_type == 'regional':
    # Filter by region
    region = input("Enter the region (East, Midwest, North Central, Pacific Northwest, Rockies, Southwest, West): ").strip().lower()
    include_products_image = input("Include images? (yes/no): ").strip().lower() #Option to include product images in the PDF
    # Gets airtable records and sorts them into groups of parents and children companies w/ logos, and descriptions 
    airtable_records = fetch_airtable_records(region)
    generate_pdf(airtable_records, logo_path=f"assets/{region}Logo.jpg", output_path="output/line_card.pdf", region=region, include_products_image=include_products_image)
    print("PDF generated successfully at 'output/line_card.pdf'.")

  elif pdf_type == 'state':
    # Filter by state
    region = input("Enter the region (East, Midwest, North Central, Pacific Northwest, Rockies, Southwest, West): ").strip().lower()
    available_states = REGION_STATE_MAP.get(region, [])
    state = input(f"Enter a state ({', '.join(available_states)}): ").strip().lower()
    airtable_records = fetch_airtable_records(region, state=state)
    generate_pdf_state(airtable_records, logo_path=f"assets/{region}Logo.jpg", output_path="output/line_card.pdf", region=region, state=state)
    print("State PDF generated successfully at 'output/line_card.pdf'.")


if __name__ == "__main__":
  main()