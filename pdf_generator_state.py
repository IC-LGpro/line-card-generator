from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import os
from reportlab.platypus import KeepTogether

from utils import create_scaled_image, build_table_content, make_footer, del_downloaded_logos, cleanup_output_folder

def create_state_header(state, logo_path):
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        name="StateTitleStyle",
        fontSize=24,
        leading=28,
        alignment=1,  # Centered
        fontName="Helvetica-Bold",
        spaceAfter=20
    )
    current_year = datetime.now().year
    title_text = f"{current_year} Line Card - {state.title()}"

    header_elements = []

    # Add logo if it exists
    if os.path.exists(logo_path):
        logo = create_scaled_image(logo_path, target_width=4 * inch)
        logo_table = Table([[logo]], colWidths=[6.5 * inch])
        logo_table.setStyle(TableStyle([
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ]))
        header_elements.append(logo_table)
        header_elements.append(Spacer(1, 10))

    # Add title
    header_elements.append(Paragraph(title_text, title_style))
    header_elements.append(Spacer(1, 20))

    return header_elements

def generate_pdf_state(airtable_records, output_path, logo_path, region, state):
    doc = SimpleDocTemplate(output_path, pagesize=letter, topMargin=36, bottomMargin=48, leftMargin=36, rightMargin=36)
    elements = []
    downloaded_logos = []

    # Header with logo and state title
    header_elements = create_state_header(state, logo_path)
    elements.append(KeepTogether(header_elements))

    # Table content
    tables, downloaded_logos = build_table_content(airtable_records, downloaded_logos)
    elements.extend(tables)

    # Footer
    doc.build(elements, onFirstPage=make_footer(region), onLaterPages=make_footer(region))

    # Cleanup
    del_downloaded_logos(downloaded_logos)
    cleanup_output_folder()
    
