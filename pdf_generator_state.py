from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import os
from reportlab.platypus import KeepTogether

from utils import create_scaled_image, build_table_content, make_page_decorator, del_downloaded_logos, cleanup_output_folder, get_asset_image_path, compute_image_display_height

def generate_pdf_state(airtable_records, output_path, region, state):
    """
    Generate a state-specific PDF using the region's header/footer assets.
    Draw a centered state name under the header on page 1 only.
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

    # State label typography and padding
    state_font_size = 20  # larger, prominent
    # Increased top padding so the State Name on page 1 is visually separated from the header
    state_padding_top = 28
    state_padding_bottom = 12
    state_text_height = state_font_size  # approximate baseline-to-top measure

    # Reserve space for later pages (use later-page header height) so pages 2+ don't get extra gap
    later_reserved_top = header2_h + 8  # small padding under later-page header
    reserved_bottom = footer_h + 6

    # Compute first-page-only spacer needed so page 1 content sits under header1 + state label
    first_page_total_needed = header1_h + state_padding_top + state_text_height + state_padding_bottom
    first_page_extra = max(0, first_page_total_needed - later_reserved_top)

    doc = SimpleDocTemplate(output_path, pagesize=letter, topMargin=later_reserved_top, bottomMargin=reserved_bottom, leftMargin=left_margin, rightMargin=right_margin)
    elements = []
    downloaded_logos = []

    # Insert a first-page-only spacer so the content on page 1 sits below header_1 + state label area
    if first_page_extra > 0:
        elements.append(Spacer(1, first_page_extra))

    # Add a small spacer so story doesn't immediately butt up to reserved area
    elements.append(Spacer(1, 8))

    # Table content
    tables, downloaded_logos = build_table_content(airtable_records, downloaded_logos)
    elements.extend(tables)

    # Page decorator will draw header (Logo_1 on page1, Logo_2 on others) and footer using the region.
    # Provide state_name so decorator draws the centered state under the header on page 1 only.
    page_decorator = make_page_decorator(region, state_name=state.title())

    doc.build(elements, onFirstPage=page_decorator, onLaterPages=page_decorator)

    # Cleanup
    del_downloaded_logos(downloaded_logos)
    cleanup_output_folder()
