"""
Script to programmatically generate the professional One-Page Technical Abstract PDF.
Saves document as Candidate_Data_Transformer_Abstract.pdf.
Uses reportlab layout blocks to build a high-density, senior-engineer-quality review sheet.
"""

from pathlib import Path
import sys

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
except ImportError:
    print("reportlab library not installed. Cannot generate abstract PDF.")
    sys.exit(1)


def generate_abstract_pdf(output_path: Path) -> None:
    # Set tight margins (0.4 inch) to fit all information cleanly on a single page
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=30,
        rightMargin=30,
        topMargin=25,
        bottomMargin=25
    )
    
    styles = getSampleStyleSheet()
    
    # Custom tight styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1A365D'), # Deep Navy
        spaceAfter=2
    )
    subtitle_style = ParagraphStyle(
        'DocSub',
        parent=styles['Normal'],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#4A5568'), # Slate Gray
        spaceAfter=10
    )
    section_title_style = ParagraphStyle(
        'SecTitle',
        parent=styles['Heading2'],
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#2B6CB0'), # Royal Blue
        spaceBefore=6,
        spaceAfter=3
    )
    body_style = ParagraphStyle(
        'Body',
        parent=styles['Normal'],
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor('#2D3748')
    )
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=body_style,
        leftIndent=10,
        firstLineIndent=-5,
        spaceAfter=2
    )

    story = []
    
    # Header Section
    story.append(Paragraph("TECHNICAL ABSTRACT: MULTI-SOURCE CANDIDATE DATA TRANSFORMER", title_style))
    story.append(Paragraph("System Architecture & Design Review | Candidate: Engineering Intern | Target: Eightfold AI Senior Reviewers", subtitle_style))
    
    # Horizontal rule
    hr_table = Table([[""]], colWidths=[550], rowHeights=[1.5])
    hr_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#2B6CB0')),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(hr_table)
    story.append(Spacer(1, 6))

    # Column/Grid setup using a borderless ReportLab Table
    col_width = 265
    gutter_width = 20
    
    # Left Column Content
    left_flow = []
    left_flow.append(Paragraph("1. System Architecture & Pipeline", section_title_style))
    left_flow.append(Paragraph(
        "The system implements a decoupled, linear data ingestion pipeline separating parsing, mapping, normalization, conflict resolution, score evaluation, and custom projection layer. Underpinned by clean design architecture, modules strictly fulfill the <b>Single Responsibility Principle (SRP)</b> to ensure scalability on production workloads.",
        body_style
    ))
    left_flow.append(Spacer(1, 4))
    
    left_flow.append(Paragraph("2. Heterogeneous Parsers", section_title_style))
    left_flow.append(Paragraph(
        "• <b>CSV/JSON</b>: Read structured headers mapping variations (e.g. designation -> headline) into canonical keys.<br/>"
        "• <b>PDF/TXT</b>: Utilizes <i>pdfplumber</i> for layout-preserved extraction (falling back to <i>pypdf</i> if corrupt) and runs optimized regex filters for structured fields.",
        body_style
    ))
    left_flow.append(Spacer(1, 4))

    left_flow.append(Paragraph("3. Value Normalization Engine", section_title_style))
    left_flow.append(Paragraph(
        "• <b>Phones</b>: Cleans digits and standardizes to E.164 (e.g. +919876543210).<br/>"
        "• <b>Dates</b>: Parses multiple formats (Jan 2024, 01/24, 2024) to ISO YYYY-MM.<br/>"
        "• <b>Skills</b>: Maps lowercase tech aliases (ReactJS, React.js) to canonical labels (React).<br/>"
        "• <b>Countries</b>: Standardizes names and codes to ISO-3166-1 alpha-2.",
        body_style
    ))
    left_flow.append(Spacer(1, 4))

    left_flow.append(Paragraph("4. Confidence Scoring Model", section_title_style))
    left_flow.append(Paragraph(
        "We introduce a multi-factor confidence model. Base confidences depend on ingestion reliability (Structured = 0.85; Unstructured = 0.65).<br/>"
        "• <b>Consensus Boost</b>: Field confidence gets +0.10 for each matching value detected across sources.<br/>"
        "• <b>Normalization Penalty</b>: Formats failing validation (e.g. malformed phone) are penalized by -0.15.<br/>"
        "• <b>Overall Confidence</b>: Weighted average of all resolved fields.",
        body_style
    ))

    # Right Column Content
    right_flow = []
    right_flow.append(Paragraph("5. Merge & Conflict Resolution Policies", section_title_style))
    right_flow.append(Paragraph(
        "Data merging is resolved deterministically by candidate keys (e.g. normalized email/phone). Conflict resolution rules ensure integrity:<br/>"
        "• <b>Contact Details</b>: <i>CSV > Resume</i>. Structured database exports are prioritized.<br/>"
        "• <b>Work Experience</b>: <i>Resume > CSV</i>. Text summaries from resume offer superior descriptive depth.<br/>"
        "• <b>Experience Deduplication</b>: Jobs at the same company and title are aligned, merging start/end dates and selecting the longest string for summaries.",
        body_style
    ))
    right_flow.append(Spacer(1, 4))

    right_flow.append(Paragraph("6. Configurable Projection Layer", section_title_style))
    right_flow.append(Paragraph(
        "Provides runtime customization without changing Python code. Supports:<br/>"
        "• Field Renaming & Subsetting (using dot and array-index notation like <i>emails[0]</i>).<br/>"
        "• Dynamic toggles for metadata (confidence scores, provenance histories).<br/>"
        "• Missing value policies: <i>null</i>, <i>omit</i> (removes key), or <i>error</i> (raises validation exception).",
        body_style
    ))
    right_flow.append(Spacer(1, 4))

    right_flow.append(Paragraph("7. Edge Case Management & Safety", section_title_style))
    right_flow.append(Paragraph(
        "• <b>Corrupt PDF</b>: Recovers by falling back to pypdf; errors are caught and logged, returning empty files gracefully rather than crashing.<br/>"
        "• <b>Empty Fields</b>: Missing attributes map to null values; never 'invent' data.<br/>"
        "• <b>JSON Schema</b>: Built-in validation blocks malformed canonical or projection configs.",
        body_style
    ))
    right_flow.append(Spacer(1, 4))

    right_flow.append(Paragraph("8. Key Architectural Trade-offs", section_title_style))
    right_flow.append(Paragraph(
        "• <b>Regex vs. LLM</b>: Text parsing uses pre-compiled regex and heuristics. While LLMs offer higher accuracy for edge layouts, regex parsers run in milliseconds, require no network calls, and guarantee 100% deterministic results, critical for bulk indexing.",
        body_style
    ))

    # Combine columns into a single row table
    grid_table = Table([[left_flow, right_flow]], colWidths=[col_width, col_width], spaceBefore=5)
    grid_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    
    # Introduce gutter by splitting the columns
    grid_table_with_gutter = Table([[left_flow, "", right_flow]], colWidths=[col_width, gutter_width, col_width])
    grid_table_with_gutter.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))

    story.append(grid_table_with_gutter)
    
    # Build Document
    doc.build(story)
    print(f"One-Page Technical Abstract PDF successfully generated at: {output_path}")


if __name__ == "__main__":
    out_pdf = Path(__file__).parent / "Candidate_Data_Transformer_Abstract.pdf"
    generate_abstract_pdf(out_pdf)
