"""
Script to programmatically generate a sample PDF resume for testing.
Uses reportlab library.
"""

import sys
from pathlib import Path

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
except ImportError:
    print("reportlab library not installed. Install requirements first.")
    sys.exit(1)


def generate_pdf(output_path: Path) -> None:
    doc = SimpleDocTemplate(str(output_path), pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom Styles
    name_style = ParagraphStyle(
        'NameStyle',
        parent=styles['Heading1'],
        fontSize=24,
        leading=28,
        spaceAfter=6
    )
    contact_style = ParagraphStyle(
        'ContactStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=12
    )
    heading_style = ParagraphStyle(
        'HeadingStyle',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        spaceBefore=10,
        spaceAfter=6
    )
    body_style = ParagraphStyle(
        'BodyStyle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=6
    )

    story = []
    
    # Header
    story.append(Paragraph("John Doe", name_style))
    story.append(Paragraph("john.doe@email.com | +91-9876543210 | Hyderabad, Telangana, India<br/>linkedin.com/in/johndoe | github.com/johndoe", contact_style))
    story.append(Spacer(1, 10))

    # Summary
    story.append(Paragraph("Professional Summary", heading_style))
    story.append(Paragraph("Full Stack Engineer at Microsoft with 4.5+ years of experience building high-throughput pipelines, API services, and modern responsive frontends. Experienced in React and Python.", body_style))
    story.append(Spacer(1, 10))

    # Experience
    story.append(Paragraph("Work Experience", heading_style))
    story.append(Paragraph("<b>Microsoft India - Software Engineer II</b> (06/2022 - Present)", body_style))
    story.append(Paragraph("Building scalable backend pipelines and reactive UI features. Managed cross-functional integration of candidate matching engines.", body_style))
    story.append(Spacer(1, 5))
    story.append(Paragraph("<b>Startup X - Software Engineer</b> (05/2020 - 05/2022)", body_style))
    story.append(Paragraph("Developed full stack features using Django and React. Optimized SQL queries to improve response times by 30%.", body_style))
    story.append(Spacer(1, 10))

    # Education
    story.append(Paragraph("Education", heading_style))
    story.append(Paragraph("<b>IIT Hyderabad</b> - B.Tech in Computer Science (2022)", body_style))
    story.append(Spacer(1, 10))

    # Skills
    story.append(Paragraph("Skills", heading_style))
    story.append(Paragraph("React, React.js, Python, Docker, Django, PostgreSQL, Kubernetes, AWS", body_style))

    doc.build(story)
    print(f"Generated PDF resume at: {output_path}")


if __name__ == "__main__":
    out = Path(__file__).parent / "resume_john_doe.pdf"
    generate_pdf(out)
