import requests
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.platypus import Image as RLImage
from reportlab.lib.units import inch
from reportlab.lib.utils import ImageReader
import os
from datetime import datetime
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import KeepTogether

#Function to create a true-to-scaled images for the PDF
def create_scaled_image(image_path, target_width):
    from reportlab.lib.utils import ImageReader
    image_reader = ImageReader(image_path)
    orig_width, orig_height = image_reader.getSize()
    aspect_ratio = orig_height / orig_width
    target_height = target_width * aspect_ratio
    return RLImage(image_path, width=target_width, height=target_height
)


def build_footer(region, styleN):
    icon_path = "assets/regionalIcon.jpg"
    icon = create_scaled_image(icon_path, target_width=0.5 * inch)
    website = "www.lawlessgroup.com"

    # Default values
    contact_info_1 = ""
    contact_info_2 = ""
    columns = []
    col_widths = []

    if region in ["West", "Pacific Northwest"]:
        contact_info_1 = (
            "TEAMWEST@LAWLESSGROUP.COM<br/>"
            "4451 Eucalyptus Ave. #330<br/>"
            "Chino, CA 91710<br/>"
            "909-606-9111"
        )
        columns = [icon, Paragraph(contact_info_1, styleN), Paragraph(website, styleN)]
        col_widths = [0.7 * inch, 4.8 * inch, 1.0 * inch]

    elif region == "Soutwest":
        contact_info_1 = (
            "TEAMSOUTH@LAWLESSGROUP.COM<br/>"
            "11625 Columbia Center Drive, Ste. 100<br/>"
            "Dallas, TX 75299<br/>"
            "972-247-8871"
        )
        contact_info_2 = (
            "TEAMSOUTH@LAWLESSGROUP.COM<br/>"
            "13323 S. Gessner Road, Ste.100<br/>"
            "Missouri City, TX 77489<br/>"
            "281-491-0351"
        )
        columns = [
            icon,
            Paragraph(contact_info_1, styleN),
            Paragraph(contact_info_2, styleN),
            Paragraph(website, styleN)
        ]
        col_widths = [0.7 * inch, 2.8 * inch, 2.8 * inch, 1.2 * inch]

    elif region == "Rockies":
        contact_info_1 = (
            "18146 Easy 84th Ave<br/>"
            "Commerce City, CO 80022<br/>"
            "719-315-7780"
        )
        contact_info_2 = (
            "3812 W. California Ave<br/>"
            "Salt Lake City, UT 84104<br/>"
            "801-301-8327"
        )
        columns = [
            icon,
            Paragraph(contact_info_1, styleN),
            Paragraph(contact_info_2, styleN),
            Paragraph(website, styleN)
        ]
        col_widths = [0.7 * inch, 2.8 * inch, 2.8 * inch, 1.2 * inch]

    elif region == "East":
        contact_info_1 = (
            "2590 Ocoee Apopka Road, Suite 100<br/>"
            "Apopka, FL 32703<br/>"
            "407-831-6676"
        )
        columns = [icon, Paragraph(contact_info_1, styleN), Paragraph(website, styleN)]
        col_widths = [0.7 * inch, 4.8 * inch, 1.0 * inch]

    elif region == "Midwest":
        contact_info_1 = (
            "55 W. Army Trail Road, Suite 102<br/>"
            "Glendale Heights, IL 60108<br/>"
            "630-931-5636"
        )
        columns = [icon, Paragraph(contact_info_1, styleN), Paragraph(website, styleN)]
        col_widths = [0.7 * inch, 4.8 * inch, 1.0 * inch]

    elif region == "North Central":
        contact_info_1 = (
            "3225 Harvester Rd.<br/>"
            "Kansas City, KS 66115<br/>"
            "816-472-5033"
        )
        columns = [icon, Paragraph(contact_info_1, styleN), Paragraph(website, styleN)]
        col_widths = [0.7 * inch, 4.8 * inch, 1.0 * inch]

    else:
        contact_info_1 = (
            "info@lawlessgroup.com<br/>"
            "123 Main St<br/>"
            "Anywhere, USA<br/>"
            "000-000-0000"
        )
        columns = [icon, Paragraph(contact_info_1, styleN), Paragraph(website, styleN)]
        col_widths = [0.7 * inch, 4.8 * inch, 1.0 * inch]

    footer_table = Table([columns], colWidths=col_widths)
    footer_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (-1, 0), (-1, 0), "RIGHT"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))

    return footer_table

def make_footer(region):
    def add_footer(canvas, doc):
        styles = getSampleStyleSheet()
        styleN = styles["Normal"]

        # You can dynamically determine the region here if needed
        footer = build_footer(region=region, styleN=styleN)

        # Wrap and draw the footer at the bottom of the page
        w, h = footer.wrap(doc.width, doc.bottomMargin)
        footer.drawOn(canvas, doc.leftMargin, 20)
    return add_footer


# Primary  function to generate the PDF
def generate_pdf(airtable_records, output_path, logo_path, region):
    # Prepare PDF
    doc = SimpleDocTemplate(output_path, pagesize=letter, topMargin=36, bottomMargin=9, leftMargin=9, rightMargin=18)
    elements = []
    downloaded_logos = []

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
        elements.append(logo_table)
        elements.append(Spacer(1, 30))

    #Add a title
    current_year = datetime.now().year
    title_text = f"{current_year} Line Card"

    title_style = ParagraphStyle(
        name="TitleStyle",
        fontSize=24,
        leading=22,
        alignment=2, # 0 = left, 1 = center, 2 = right
        spaceAfter=12,
        fontName="Helvetica-Bold"
    )
    title_paragraph = Paragraph(title_text, title_style)
    elements.append(title_paragraph)
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
            parent_logo = create_scaled_image(logo_filename, target_width=1.4 * inch)
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
                child_logo = create_scaled_image(logo_filename, target_width=0.7 * inch)
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
            ("VALIGN", (0, 0), (-1, -1), "CENTER"),
            #("LEFTPADDING", (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.grey),
        ]))

        
        elements.append(KeepTogether([table, Spacer(1, 12)]))

    
    elements.append(Spacer(1,81))
    # Build PDF
    doc.build(elements, onFirstPage=make_footer(region), onLaterPages=make_footer(region))
    print("PDF with aligned containers created successfully.")

    # Clean up downloaded logo files
    for logo_filename in downloaded_logos:
        if os.path.exists(logo_filename):
            os.remove(logo_filename)
