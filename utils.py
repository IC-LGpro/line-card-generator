#This file contains utility functions for generating PDF line cards, including image handling, table creation, and footer generation.
# It also includes functions for cleaning up temporary files and managing the output folder.
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Table, TableStyle, Paragraph, Spacer, Image as RLImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import os
import requests
import time

def create_scaled_image(image_path, target_width, max_height=650):
    image_reader = ImageReader(image_path)
    orig_width, orig_height = image_reader.getSize()
    aspect_ratio = orig_height / orig_width
    target_height = target_width * aspect_ratio

    if target_height > max_height:
        target_height = max_height
        target_width = target_height / aspect_ratio

    return RLImage(image_path, width=target_width, height=target_height)

def build_table_content(airtable_records, downloaded_logos):
    styles = getSampleStyleSheet()
    styleN = styles["Normal"]
    tables = []

    for parent_name, group in airtable_records.items():
        parent = group["parent"]
        children = group["children"]

        parent_logo_info = parent.get("Logos", []) if parent else []
        if parent_logo_info:
            logo_url = parent_logo_info[0]["url"]
            logo_filename = f"assets/temp_logos/logo_{parent_name.replace(' ', '_')}.png"
            response = requests.get(logo_url)
            with open(logo_filename, "wb") as f:
                f.write(response.content)
            downloaded_logos.append(logo_filename)
            parent_logo = create_scaled_image(logo_filename, target_width=1.4 * inch)
        else:
            parent_logo = Paragraph("No Logo", styleN)

        child_logos = []
        for i, child in enumerate(children):
            child_logo_info = child.get("Logos", [])
            if child_logo_info:
                logo_url = child_logo_info[0]["url"]
                logo_filename = f"assets/temp_logos/child_logo_{parent_name.replace(' ', '_')}_{i}.png"
                response = requests.get(logo_url)
                with open(logo_filename, "wb") as f:
                    f.write(response.content)
                downloaded_logos.append(logo_filename)
                child_logo = create_scaled_image(logo_filename, target_width=0.6 * inch)
                child_logos.append(child_logo)

        description = parent.get("Description", "No description available.") if parent else "No description available."
        description_paragraph = Paragraph(description, styleN)

        right_column_content = []
        if child_logos:
            child_logo_table = Table([child_logos])
            child_logo_table.setStyle(TableStyle([
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]))
            right_column_content.append(child_logo_table)
            right_column_content.append(Spacer(1, 4))

        right_column_content.append(description_paragraph)

        row = [parent_logo, right_column_content]
        table = Table([row], colWidths=[2.0 * inch, 5.0 * inch])
        table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "CENTER"),
            ("LEFTPADDING", (0, 0), (0, 0), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
            ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.grey),
        ]))
        tables.append(table)
        tables.append(Spacer(1, 12))

    return tables, downloaded_logos

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
    if region in ["west", "pacific northwest"]:
        contact_info_1 = (
            "TEAMWEST@LAWLESSGROUP.COM<br/>"
            "4451 Eucalyptus Ave. #330<br/>"
            "Chino, CA 91710<br/>"
            "909-606-9111"
        )
        columns = [icon, Paragraph(contact_info_1, address_style), Paragraph(website, website_style)]
        col_widths = [0.7 * inch, 4.8 * inch, 2 * inch]

    elif region == "southwest":
        contact_info_1 = (
            "11625 Columbia Center Drive, Ste. 100<br/>"
            "Dallas, TX 75299<br/>"
            "P: 972-247-8871<br/>"
            "F: 972-620-1147"

        )
        contact_info_2 = (
            "13323 S. Gessner Road, Ste.100<br/>"
            "Missouri City, TX 77489<br/>"
            "P: 281-491-0351<br/>"
            "F: 281-491-0367"
        )
        columns = [
            icon,
            Paragraph(contact_info_1, address_style),
            Paragraph(contact_info_2, address_style),
            Paragraph(website, website_style)
        ]
        col_widths = [0.7 * inch, 2.4 * inch, 2.4 * inch, 1.9 * inch]

    elif region == "rockies":
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

    elif region == "east":
        contact_info_1 = (
            "TEAMEAST@LAWLESSGROUP.COM<br/>"
            "2590 Ocoee Apopka Road, Suite 100<br/>"
            "Apopka, FL 32703<br/>"
            "407-831-6676"
        )
        columns = [icon, Paragraph(contact_info_1, address_style), Paragraph(website, website_style)]
        col_widths = [0.7 * inch, 4.8 * inch, 2.0 * inch]

    elif region == "midwest":
        contact_info_1 = (
            "Mike.Fisher@lawlessgroup.com | Tim.Weber@lawlessgroup.com<br/>"
            "55 W. Army Trail Road, Suite 102<br/>"
            "Glendale Heights, IL 60108<br/>"
            "630-931-5636"
        )
        columns = [icon, Paragraph(contact_info_1, address_style), Paragraph(website, website_style)]
        col_widths = [0.7 * inch, 4.8 * inch, 2.0 * inch]

    elif region == "north central":
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

def make_footer(region):

    # This function will be called to add the footer to each page
    def add_footer(canvas, doc):

        # You can dynamically determine the region here if needed
        footer = build_footer(region)

        # Wrap and draw the footer at the bottom of the page
        w, h = footer.wrap(doc.width, doc.bottomMargin)
        footer.drawOn(canvas, doc.leftMargin, 20)
    return add_footer

def del_downloaded_logos(downloaded_logos):
    for logo_filename in downloaded_logos:
        if os.path.exists(logo_filename):
            os.remove(logo_filename)

def cleanup_output_folder(folder="output", max_age_seconds=60):
    now = time.time()
    if not os.path.exists(folder):
        return  # Skip if folder doesn't exist
    for filename in os.listdir(folder):
        filepath = os.path.join(folder, filename)
        if os.path.isfile(filepath):
            file_age = now - os.path.getmtime(filepath)
            if file_age > max_age_seconds:
                os.remove(filepath)
                print(f"Deleted {filepath}")
