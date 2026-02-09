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
import logging

logger = logging.getLogger(__name__)

def get_static_assets_dir() -> str:
    """
    Return the absolute filesystem path to the application's static/assets directory.

    Order of resolution:
    1. If running inside a Flask app context, use current_app.static_folder + '/assets'.
    2. Otherwise, fallback to '<module_dir>/static/assets' relative to this utils.py file.

    This centralizes the single source of truth for static asset lookup. Do not depend on CWD.
    """
    try:
        # local import to avoid hard dependency at module import time
        from flask import current_app
        # current_app.static_folder is absolute path to the static folder
        static_folder = getattr(current_app, "static_folder", None)
        if static_folder:
            path = os.path.join(static_folder, "assets")
            return path
    except Exception:
        # not in a Flask app context, fallback
        pass

    # fallback: module-relative path -> ../static/assets
    module_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(module_dir, "static", "assets")
    return path

# --- Asset helpers ---------------------------------------------------------
def normalize_asset_key(s: str) -> str:
    """
    Normalize asset keys for comparison: lowercase, replace spaces with underscore,
    remove non-alphanumeric/underscore characters, collapse multiple underscores.
    """
    if not s:
        return ""
    # Lowercase
    out = s.lower()
    # Replace spaces and hyphens with underscore
    out = out.replace(" ", "_").replace("-", "_")
    # Keep only alphanumerics and underscores
    out = "".join(c if (c.isalnum() or c == "_") else "_" for c in out)
    # Collapse multiple underscores
    while "__" in out:
        out = out.replace("__", "_")
    return out.strip("_")

def get_asset_image_path(base_name: str, assets_dir: str = None):
    """
    Given a base_name like "MidwestLogo_1" or "MidwestFooter",
    return the first matching file path under assets_dir with extension priority:
    .png, .jpg, .jpeg, .pdf (case-insensitive). If missing, return None and log.

    If assets_dir is None, resolve via get_static_assets_dir() so callers never need to compute paths.
    """
    if not base_name:
        return None

    # resolve canonical assets dir if not provided
    if not assets_dir:
        assets_dir = get_static_assets_dir()

    desired = normalize_asset_key(base_name)
    exts = [".png", ".jpg", ".jpeg", ".pdf"]

    try:
        files = os.listdir(assets_dir)
    except FileNotFoundError:
        logger.warning("Assets directory does not exist: %s", assets_dir)
        return None
    except Exception:
        logger.exception("Failed listing assets directory: %s", assets_dir)
        return None

    candidates = []
    for fname in files:
        name, ext = os.path.splitext(fname)
        ext = ext.lower()
        if ext not in exts:
            continue
        norm = normalize_asset_key(name)
        if norm == desired:
            # prefer earlier extension in exts order
            candidates.append((exts.index(ext), os.path.join(assets_dir, fname)))
    if not candidates:
        logger.warning("Asset not found for base '%s' in %s", base_name, assets_dir)
        return None
    # sort by extension priority and return the best candidate
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]

def compute_image_display_height(image_path: str, target_width: float) -> float:
    """
    Compute the image height (points) when scaled to target_width preserving aspect ratio.
    Returns 0 if the image_path is missing or unreadable.
    """
    if not image_path or not os.path.exists(image_path):
        return 0
    try:
        img = ImageReader(image_path)
        iw, ih = img.getSize()
        if iw == 0:
            return 0
        scale = float(target_width) / float(iw)
        return float(ih) * scale
    except Exception:
        logger.exception("Failed to compute image display height for %s", image_path)
        return 0

# --- Image helpers ---------------------------------------------------------
def create_scaled_image(image_path, target_width, max_height=650):
    """
    Return an RLImage scaled to target_width while preserving aspect ratio.
    If image can't be read, return a Paragraph placeholder.
    """
    try:
        image_reader = ImageReader(image_path)
    except Exception:
        logger.warning("create_scaled_image: image not found or unreadable: %s", image_path)
        return Paragraph("Image not available", getSampleStyleSheet()["Normal"])

    orig_width, orig_height = image_reader.getSize()
    aspect_ratio = orig_height / orig_width
    target_height = target_width * aspect_ratio

    if target_height > max_height:
        target_height = max_height
        target_width = target_height / aspect_ratio

    return RLImage(image_path, width=target_width, height=target_height)

def draw_image_on_canvas(canvas, image_path, x, y, width=None, keep_aspect=True, anchor_top=False):
    """
    Draw raster image on canvas.
    - If anchor_top is False: y is bottom coordinate (ReportLab default).
    - If anchor_top is True: y is top coordinate; image will be drawn so its top edge = y.
    Returns drawn height (points) or 0 if skipped.
    PDF images are skipped (log a warning).
    """
    if not image_path or not os.path.exists(image_path):
        logger.debug("draw_image_on_canvas: image missing: %s", image_path)
        return 0
    _, ext = os.path.splitext(image_path)
    ext = ext.lower()
    if ext == ".pdf":
        logger.warning("PDF asset rendering not implemented: %s (skipping)", image_path)
        return 0
    try:
        img = ImageReader(image_path)
        iw, ih = img.getSize()
        if iw == 0:
            return 0
        if width:
            scale = width / float(iw)
            draw_w = width
            draw_h = float(ih) * scale
        else:
            draw_w = iw
            draw_h = ih

        if anchor_top:
            # y is top coordinate; compute bottom-left y
            bottom_y = y - draw_h
        else:
            bottom_y = y

        # ReportLab's drawImage expects bottom-left coordinates
        canvas.drawImage(image_path, x, bottom_y, width=draw_w, height=draw_h, preserveAspectRatio=keep_aspect, mask='auto')
        return draw_h
    except Exception as ex:
        logger.exception("Failed to draw image %s: %s", image_path, ex)
        return 0

# --- Page decorators for header/footer ------------------------------------
def make_page_decorator(region_name: str, state_name: str = None, assets_dir: str = None):
    """
    Return a single function to be passed to doc.build for onFirstPage and onLaterPages.
    Behavior:
     - Header image base: "{RegionName}Logo_1" for page 1, "{RegionName}Logo_2" for later pages.
     - Footer image base: "{RegionName}Footer" for all pages.
     - If state_name provided, draw centered state_name text under the header (only on page 1).
    The decorator will log missing assets and never raise.
    """
    if not assets_dir:
        assets_dir = get_static_assets_dir()

    def add_header_footer(canvas, doc):
        try:
            page_width, page_height = doc.pagesize
            left = doc.leftMargin
            # content_width still available for content calculations
            content_width = page_width - doc.leftMargin - doc.rightMargin

            # determine header variant
            page_num = canvas.getPageNumber()
            header_variant = 1 if page_num == 1 else 2
            header_base = f"{region_name}Logo_{header_variant}"
            header_path = get_asset_image_path(header_base, assets_dir=assets_dir)

            header_height = 0
            if header_path:
                # draw header top-aligned to page top and spanning full page width (not constrained by margins)
                header_height = draw_image_on_canvas(canvas, header_path, 0, page_height, width=page_width, anchor_top=True)
                if header_height == 0:
                    header_height = int(0.9 * inch)
            else:
                header_height = int(0.9 * inch)
                logger.warning("Missing header asset for region=%s variant=%s", region_name, header_variant)

            # If state_name is present, draw it centered under the header with configurable padding only on page 1
            if state_name and page_num == 1:
                # Increased top padding above State Name (affects page 1 only)
                state_padding_top = 28  # points (increased from 12)
                state_font_size = 20
                # place baseline of text below header by padding; text_y is baseline
                text_y = page_height - header_height - state_padding_top
                canvas.setFont("Helvetica-Bold", state_font_size)
                canvas.setFillColorRGB(0, 0, 0)
                canvas.drawCentredString(page_width / 2.0, text_y, state_name.title())

            # Footer: use {RegionName}Footer on every page (draw full page width, bottom-aligned)
            footer_base = f"{region_name}Footer"
            footer_path = get_asset_image_path(footer_base, assets_dir=assets_dir)
            if footer_path:
                # draw footer bottom-aligned at y=0 spanning full page width
                draw_image_on_canvas(canvas, footer_path, 0, 0, width=page_width, anchor_top=False)
            else:
                # fallback: draw a rule line across content area
                canvas.setStrokeColorRGB(0.5, 0.5, 0.5)
                canvas.setLineWidth(0.5)
                canvas.line(left, 30, left + content_width, 30)
                logger.warning("Missing footer asset for region=%s", region_name)
        except Exception:
            logger.exception("Error in page decorator for region=%s state=%s", region_name, state_name)
    return add_header_footer

# --- Existing table-building that downloads logos from Airtable -----------
def build_table_content(airtable_records, downloaded_logos):
    styles = getSampleStyleSheet()
    styleN = styles["Normal"]
    tables = []

    # Base directory for temporary logos under static assets
    base_temp_dir = os.path.join(get_static_assets_dir(), "temp_logos")
    os.makedirs(base_temp_dir, exist_ok=True)

    for parent_name, group in airtable_records.items():
        parent = group["parent"]
        children = group["children"]

        # sanitize parent_name for filenames
        safe_parent = "".join(c if (c.isalnum() or c in (' ', '_', '-')) else '_' for c in (parent_name or "unknown"))
        safe_parent = safe_parent.replace(' ', '_')

        parent_logo_info = parent.get("Logos", []) if parent else []
        if parent_logo_info:
            try:
                logo_url = parent_logo_info[0].get("url")
                logo_filename = os.path.join(base_temp_dir, f"logo_{safe_parent}.png")
                resp = requests.get(logo_url, timeout=30)
                if resp.status_code == 200:
                    with open(logo_filename, "wb") as f:
                        f.write(resp.content)
                    downloaded_logos.append(logo_filename)
                    parent_logo = create_scaled_image(logo_filename, target_width=1.4 * inch)
                else:
                    logger.warning("Failed to download parent logo %s: status %s", logo_url, resp.status_code)
                    parent_logo = Paragraph("No Logo", styleN)
            except Exception as ex:
                logger.exception("Error downloading parent logo for %s: %s", parent_name, ex)
                parent_logo = Paragraph("No Logo", styleN)
        else:
            parent_logo = Paragraph("No Logo", styleN)

        child_logos = []
        for i, child in enumerate(children):
            child_logo_info = child.get("Logos", [])
            if child_logo_info:
                try:
                    logo_url = child_logo_info[0].get("url")
                    logo_filename = os.path.join(base_temp_dir, f"child_logo_{safe_parent}_{i}.png")
                    resp = requests.get(logo_url, timeout=30)
                    if resp.status_code == 200:
                        with open(logo_filename, "wb") as f:
                            f.write(resp.content)
                        downloaded_logos.append(logo_filename)
                        child_logo = create_scaled_image(logo_filename, target_width=0.6 * inch)
                        child_logos.append(child_logo)
                    else:
                        logger.warning("Failed to download child logo %s: status %s", logo_url, resp.status_code)
                except Exception as ex:
                    logger.exception("Error downloading child logo for %s child %d: %s", parent_name, i, ex)

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
