# Imports
from airtable_utils import fetch_airtable_records
from pdf_generator import generate_pdf

def main():
  # Filter by region
  region = input("Enter the region (East, Midwest, North Central, Pacific Northwest, Rockies, Southwest, West): ").strip().lower()
  include_products_image = input("Include images? (yes/no): ").strip().lower() #Option to include product images in the PDF

  # Gets airtable records and sorts them into groups of parents and children companies w/ logos, and descriptions 
  airtable_records = fetch_airtable_records(region)
  #print(f"Number of records: {len(airtable_records)}")

  generate_pdf(airtable_records, logo_path=f"assets/{region}Logo.jpg", output_path="output/line_card.pdf", region=region, include_products_image=include_products_image == 'yes')
  print("PDF generated successfully at 'output/line_card.pdf'.")

if __name__ == "__main__":
  main()