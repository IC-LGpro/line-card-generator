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

# Function to create a true-to-scaled images for the PDF
def create_scaled_image(image_path, target_width):
    from reportlab.lib.utils import ImageReader
    image_reader = ImageReader(image_path)
    orig_width, orig_height = image_reader.getSize()
    aspect_ratio = orig_height / orig_width
    target_height = target_width * aspect_ratio
    return RLImage(image_path, width=target_width, height=target_height
)

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

# Builds the table content for the PDF
def build_table_content(airtable_records, downloaded_logos):

    # Styles for wrapping
    styles = getSampleStyleSheet()
    styleN = styles["Normal"]
    tables = []

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
                child_logo = create_scaled_image(logo_filename, target_width=0.6 * inch)
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
        table = Table([row], colWidths=[2.0*inch, 5.0*inch])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "CENTER"),
            ("LEFTPADDING", (0, 0), (0, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.grey),
        ]))
        tables.append(KeepTogether([table, Spacer(1, 12)]))

    return tables, downloaded_logos


    # Function to build the content within the footer called by add_footer

# Function to build the footer content
def build_footer(region):
    icon_path = "assets/regionalIcon.jpg"
    icon = create_scaled_image(icon_path, target_width=0.5 * inch)
    website = "<b>www.lawlessgroup.com</b>"

    # Define styles for the footer
    website_style = ParagraphStyle(
        name="WebsiteStyle",
        fontSize=11,
        alignment=1,  # 2 = right-align
        wordWrap='CJK',  # Left-to-right, avoids breaking words
        spaceShrinkage=0.05,
        allowWindows=1,
        allowOrphans=1  # Slightly compresses spaces to fit more
    )

    address_style = ParagraphStyle(
        name="FooterAddressStyle",
        fontSize=9,  # Smaller font size
        leading=10,  # Line spacing
        alignment=1,  # Centered (use 0 for left-aligned)
        spaceAfter=2
    )

    # Default values
    contact_info_1 = ""
    contact_info_2 = ""
    columns = []
    col_widths = []

    # Determine footer content based on region
    if region in ["West", "Pacific Northwest"]:
        contact_info_1 = (
            "TEAMWEST@LAWLESSGROUP.COM<br/>"
            "4451 Eucalyptus Ave. #330<br/>"
            "Chino, CA 91710<br/>"
            "909-606-9111"
        )
        columns = [icon, Paragraph(contact_info_1, address_style), Paragraph(website, website_style)]
        col_widths = [0.7 * inch, 4.8 * inch, 2 * inch]

    elif region == "Southwest":
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
            Paragraph(contact_info_1, address_style),
            Paragraph(contact_info_2, address_style),
            Paragraph(website, website_style)
        ]
        col_widths = [0.7 * inch, 2.4 * inch, 2.4 * inch, 1.9 * inch]

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
            Paragraph(contact_info_1, address_style),
            Paragraph(contact_info_2, address_style),
            Paragraph(website, website_style)
        ]
        col_widths = [0.7 * inch, 2.4 * inch, 2.4 * inch, 1.9 * inch]

    elif region == "East":
        contact_info_1 = (
            "2590 Ocoee Apopka Road, Suite 100<br/>"
            "Apopka, FL 32703<br/>"
            "407-831-6676"
        )
        columns = [icon, Paragraph(contact_info_1, address_style), Paragraph(website, website_style)]
        col_widths = [0.7 * inch, 4.8 * inch, 2.0 * inch]

    elif region == "Midwest":
        contact_info_1 = (
            "55 W. Army Trail Road, Suite 102<br/>"
            "Glendale Heights, IL 60108<br/>"
            "630-931-5636"
        )
        columns = [icon, Paragraph(contact_info_1, address_style), Paragraph(website, website_style)]
        col_widths = [0.7 * inch, 4.8 * inch, 2.0 * inch]

    elif region == "North Central":
        contact_info_1 = (
            "3225 Harvester Rd.<br/>"
            "Kansas City, KS 66115<br/>"
            "816-472-5033"
        )
        columns = [icon, Paragraph(contact_info_1, address_style), Paragraph(website, website_style)]
        col_widths = [0.7 * inch, 4.8 * inch, 2.0 * inch]

    # Defalt footer layout 
    footer_table = Table([columns], colWidths=col_widths)
    footer_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (-1, 0), (-1, 0), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4), 
        ("LEFTPADDING", (0, 0), (0, 0), 4), # Left adding for the footer icon
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))

    return footer_table

# Function to draw add footer content to the PDF and call the build_footer function
def make_footer(region):
    # This function will be called to add the footer to each page
    def add_footer(canvas, doc):
        styles = getSampleStyleSheet()
        styleN = styles["Normal"]

        # You can dynamically determine the region here if needed
        footer = build_footer(region=region)

        # Wrap and draw the footer at the bottom of the page
        w, h = footer.wrap(doc.width, doc.bottomMargin)
        footer.drawOn(canvas, doc.leftMargin, 20)
    return add_footer

# Function to delete downloaded logo files after PDF generation
def del_downloaded_logos(downloaded_logos):
    for logo_filename in downloaded_logos:
        if os.path.exists(logo_filename):
            os.remove(logo_filename)

# Primary function to generate the PDF
def generate_pdf(airtable_records, output_path, logo_path, region):
    # 1. Prepare PDF
    doc = SimpleDocTemplate(output_path, pagesize=letter, topMargin=36, bottomMargin=48, leftMargin=36, rightMargin=36)
    elements = [] # will be used to store the elmenets of the PDF
    downloaded_logos = [] # List to keep track of temporarily downloaded logos from the Airtable records

    # 2. Add Company logo
    logo_table = create_cologo_table(logo_path)
    elements.append(logo_table)
    elements.append(Spacer(1, 30))

    # 3. Add a title
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

    # 4. Add the table content
    tables, downloaded_logos = build_table_content(airtable_records, downloaded_logos)
    elements.extend(tables)

    # 5. Build PDF w/ footer
    doc.build(elements, onFirstPage=make_footer(region), onLaterPages=make_footer(region))
    print("PDF with aligned containers created successfully.")

    # 6. Clean up downloaded logo files
    del_downloaded_logos(downloaded_logos)
