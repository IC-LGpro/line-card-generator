from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import os
from datetime import datetime
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import KeepTogether

from utils import create_scaled_image, build_table_content, make_footer, del_downloaded_logos

# Function creates the company logo table (the first element on the pdf)
def create_cologo_table(logo_path):
   # Add Company logo
    if os.path.exists(logo_path):
        company_logo = create_scaled_image(logo_path, target_width=4 * inch)
        logo_table = Table([[company_logo]], colWidths=[6.5 * inch])
        logo_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
    return logo_table

def create_header_with_product_image(logo_path, region):
    elements = []

    # Load company logo
    cologo = create_scaled_image(logo_path, target_width=3 * inch)

    # Create title
    current_year = datetime.now().year
    title_text = f"{current_year} Line Card"
    title_style = ParagraphStyle(
        name="TitleStyle",
        fontSize=24,
        leading=22,
        alignment=2,  # Right-align
        fontName="Helvetica-Bold"
    )
    title = Paragraph(title_text, title_style)

    # Top row: logo and title
    top_table = Table([[cologo, title]], colWidths=[3.25 * inch, 3.25 * inch])
    top_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    elements.append(top_table)

    # Bottom row: products image
    product_image_path = f"assets/{region}_products_image.jpg"
    if os.path.exists(product_image_path):
        product_image = create_scaled_image(product_image_path, target_width=8.5 * inch)
        product_table = Table([[product_image]], colWidths=[6.5 * inch])
        product_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(product_table)
    else:
        elements.append(Paragraph("Product image not found", getSampleStyleSheet()["Normal"]))

    return elements

# Primary function to generate the PDF
def generate_pdf(airtable_records, output_path, logo_path, region, include_products_image):
    # 1. Prepare PDF
    doc = SimpleDocTemplate(output_path, pagesize=letter, topMargin=36, bottomMargin=48, leftMargin=36, rightMargin=36)
    elements = [] # will be used to store the elmenets of the PDF
    downloaded_logos = [] # List to keep track of temporarily downloaded logos from the Airtable records

    # 2. Add Company logo & title
    if include_products_image=="yes":
        header_elements = create_header_with_product_image(logo_path, region)
        elements.append(KeepTogether(header_elements))
        elements.append(Spacer(1, 15))
    else:
        logo = create_scaled_image(logo_path, target_width=4 * inch)
        logo_table = Table([[logo]], colWidths=[6.5 * inch])
        logo_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        elements.append(logo_table)
        elements.append(Spacer(1, 10))

        current_year = datetime.now().year
        title_text = f"{current_year} Line Card"
        title_style = ParagraphStyle(
            name="TitleStyle",
            fontSize=24,
            leading=22,
            alignment=1,  # Center-align
            spaceAfter=12,
            fontName="Helvetica-Bold"
        )
        title_paragraph = Paragraph(title_text, title_style)
        elements.append(title_paragraph)
        elements.append(Spacer(1, 15))
        
    # 4. Add the table content
    tables, downloaded_logos = build_table_content(airtable_records, downloaded_logos)
    elements.extend(tables)

    # 5. Build PDF w/ footer
    doc.build(elements, onFirstPage=make_footer(region), onLaterPages=make_footer(region))
    print("PDF with aligned containers created successfully.")

    # 6. Clean up downloaded logo files
    del_downloaded_logos(downloaded_logos)
