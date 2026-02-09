from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import os
from datetime import datetime
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import KeepTogether

from utils import create_scaled_image, build_table_content, make_page_decorator, del_downloaded_logos, cleanup_output_folder, get_asset_image_path, compute_image_display_height

# Primary function to generate the PDF (region-level)
def generate_pdf(airtable_records, output_path, region, state=None):
    """
    airtable_records: grouped dict
    output_path: filesystem path to write PDF
    region: region name (string)
    state: optional (kept for compatibility)
    """

    # Page and content margins
    PAGE_WIDTH, PAGE_HEIGHT = letter
    left_margin = 36
    right_margin = 36
    content_width = PAGE_WIDTH - left_margin - right_margin

    # Resolve header/footer asset paths and compute heights scaled to full page width
    header1_path = get_asset_image_path(f"{region}Logo_1")
    header2_path = get_asset_image_path(f"{region}Logo_2")
    footer_path = get_asset_image_path(f"{region}Footer")

    header1_h = compute_image_display_height(header1_path, PAGE_WIDTH) or (0.9 * inch)
    header2_h = compute_image_display_height(header2_path, PAGE_WIDTH) or (0.9 * inch)
    footer_h = compute_image_display_height(footer_path, PAGE_WIDTH) or (0.5 * inch)

    # Reserve space for later pages (use later-page header height) so pages 2+ don't get extra gap
    later_reserved_top = header2_h + 8  # small padding under later-page header
    reserved_bottom = footer_h + 6  # small padding above footer

    # Compute first-page-only extra spacer to account for larger first-page header (if any)
    first_page_extra = max(0, (header1_h - header2_h) + 8)  # add small padding

    doc = SimpleDocTemplate(output_path, pagesize=letter, topMargin=later_reserved_top, bottomMargin=reserved_bottom, leftMargin=left_margin, rightMargin=right_margin)
    elements = []  # will be used to store the elements of the PDF
    downloaded_logos = []  # List to keep track of temporarily downloaded logos from the Airtable records

    # Insert a first-page-only spacer so page 1 content aligns under the taller header_1
    if first_page_extra > 0:
        elements.append(Spacer(1, first_page_extra))

    # Add a small spacer so story doesn't immediately butt up to reserved area
    elements.append(Spacer(1, 12))

    # Add the table content
    tables, downloaded_logos = build_table_content(airtable_records, downloaded_logos)
    elements.extend(tables)

    # Page decorator handles header/footer drawing; pass region and optional state (None here)
    page_decorator = make_page_decorator(region, state_name=None)

    # Build PDF with page decorator applied to both first and later pages
    doc.build(elements, onFirstPage=page_decorator, onLaterPages=page_decorator)

    # Clean up downloaded logo files
    del_downloaded_logos(downloaded_logos)
    cleanup_output_folder()
