import requests
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import Image as RLImage
from reportlab.lib.units import inch
import os

def generate_pdf(airtable_records, output_path, logo_path):
    # Prepare PDF
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    elements = []
    downloaded_logos = []

    # Add Company logo
    if os.path.exists(logo_path):
        elements.append(Image(logo_path, width=300, height=150))
        elements.append(Spacer(1, 30))

    # Styles for wrapping
    styles = getSampleStyleSheet()
    styleN = styles["Normal"]

    # Build content
    for parent_name, group in airtable_records.items():
        parent = group["parent"]
        children = group["children"]

        # --- Parent Logo ---
        parent_logo_info = parent.get("Logos", []) if parent else []
        if parent_logo_info:
            logo_url = parent_logo_info[0]["url"]
            logo_filename = f"temp_logos/logo_{parent_name.replace(' ', '_')}.png"
            response = requests.get(logo_url)
            with open(logo_filename, "wb") as f:
                f.write(response.content)
            downloaded_logos.append(logo_filename)
            parent_logo = RLImage(logo_filename, width=1.8*inch, height=0.8*inch)
        else:
            parent_logo = Paragraph("No Logo", styleN)

        # --- Child Logos (if any) ---
        child_logos = []
        for i, child in enumerate(children):
            child_logo_info = child.get("Logos", [])
            if child_logo_info:
                logo_url = child_logo_info[0]["url"]
                logo_filename = f"temp_logos/child_logo_{parent_name.replace(' ', '_')}_{i}.png"
                response = requests.get(logo_url)
                with open(logo_filename, "wb") as f:
                    f.write(response.content)
                downloaded_logos.append(logo_filename)
                child_logo = RLImage(logo_filename, width=0.9*inch, height=0.4*inch)
                child_logos.append(child_logo)

        # --- Description ---
        if parent:
            description = parent.get("Description", "No description available.")
        else:
            description = "No description available."
        description_paragraph = Paragraph(description, styleN)


        # Combine child logos and description vertically
        right_column_content = []

        if child_logos:
            child_logo_table = Table([child_logos])
            child_logo_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),]))
            right_column_content.append(child_logo_table)
            right_column_content.append(Spacer(1, 4))

        # Add description after child logos (or directly if no children)
        right_column_content.append(description_paragraph)


        # Create a row with parent logo and right column
        row = [parent_logo, right_column_content]
        table = Table([row], colWidths=[2.2*inch, 4.8*inch])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.grey),
        ]))

        elements.append(table)
        elements.append(Spacer(1, 12))

    # Build PDF
    doc.build(elements)
    print("PDF with aligned containers created successfully.")

    # Clean up downloaded logo files
    for logo_filename in downloaded_logos:
        if os.path.exists(logo_filename):
            os.remove(logo_filename)
