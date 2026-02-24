from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image, Spacer, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
import os
from datetime import datetime
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import KeepTogether
import logging
from reportlab.lib import colors

from utils import create_scaled_image, build_table_content, make_page_decorator, del_downloaded_logos, cleanup_output_folder, get_asset_image_path, compute_image_display_height

logger = logging.getLogger(__name__)

# Top/bottom padding constants (tweak as needed)
TOP_PADDING_AFTER_HEADER_FIRST_PAGE = 14   # points between header bottom and first content on page 1
TOP_PADDING_AFTER_HEADER_LATER_PAGES = 10  # points for pages 2+
BOTTOM_PADDING_ABOVE_FOOTER = 6            # small padding above footer

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

    # Use later-page header height + explicit later padding for the document top margin
    later_reserved_top = header2_h + TOP_PADDING_AFTER_HEADER_LATER_PAGES
    reserved_bottom = footer_h + BOTTOM_PADDING_ABOVE_FOOTER

    # Compute first-page-only spacer so page 1 content sits under header1 + first-page padding
    first_page_total_needed = header1_h + TOP_PADDING_AFTER_HEADER_FIRST_PAGE
    first_page_extra = max(0, first_page_total_needed - later_reserved_top)

    doc = SimpleDocTemplate(output_path, pagesize=letter, topMargin=later_reserved_top, bottomMargin=reserved_bottom, leftMargin=left_margin, rightMargin=right_margin)
    elements = []  # will be used to store the elements of the PDF
    downloaded_logos = []  # List to keep track of temporarily downloaded logos from the Airtable records

    # Insert a first-page-only spacer so page 1 content sits below header_1 area (no double-counting)
    if first_page_extra > 0:
        elements.append(Spacer(1, first_page_extra))

    # Add the table content (no additional top spacer here)
    tables, downloaded_logos = build_table_content(airtable_records, downloaded_logos)
    elements.extend(tables)

    # --- East-only appended asset (insert before footer, after all tables) ---
    # Tweakable side padding (points)
    EAST_ASSET_SIDE_PADDING = 12

    if region and region.strip().lower() == "east":
        asset_base = "Lawless_East_asset"
        asset_path = get_asset_image_path(asset_base)
        if asset_path:
            try:
                # Compute drawable width aligned to content frame (content-aligned)
                drawable_width = PAGE_WIDTH - left_margin - right_margin - (2 * EAST_ASSET_SIDE_PADDING)
                if drawable_width <= 0:
                    logger.warning("Drawable width computed non-positive for east asset; skipping asset insertion.")
                else:
                    # create_scaled_image preserves aspect ratio
                    east_img = create_scaled_image(asset_path, target_width=drawable_width)
                    # small spacer then the image, so it sits above footer on last page
                    elements.append(Spacer(1, 12))
                    elements.append(east_img)
                    elements.append(Spacer(1, 8))
            except Exception:
                logger.exception("Failed to append East region asset %s to PDF", asset_path)
        else:
            logger.warning("East region asset '%s' not found in static assets; skipping.", asset_base)
    
    # Final disclaimer appended to every PDF (last content element before footer)
    try:
        disclaimer_style = ParagraphStyle("DisclaimerStyle", parent=getSampleStyleSheet()["Normal"], textColor=colors.red)
        elements.append(Spacer(1, 8))
        elements.append(Paragraph("Disclaimer: Every manufacturer is not in every state.", disclaimer_style))
    except Exception:
        logger.exception("Failed to append disclaimer paragraph to PDF")

    # Page decorator handles header/footer drawing; pass region and optional state (None here)
    page_decorator = make_page_decorator(region, state_name=None)

    # Build PDF with page decorator applied to both first and later pages
    doc.build(elements, onFirstPage=page_decorator, onLaterPages=page_decorator)

    # Clean up downloaded logo files
    del_downloaded_logos(downloaded_logos)
    cleanup_output_folder()
