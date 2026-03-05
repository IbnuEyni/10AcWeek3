#!/usr/bin/env python3
"""Create a native digital PDF for testing"""

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

def create_native_pdf():
    filename = "data/test_native_digital.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    story = []
    styles = getSampleStyleSheet()
    
    # Title
    story.append(Paragraph("Financial Report 2024", styles['Title']))
    story.append(Spacer(1, 12))
    
    # Some text
    story.append(Paragraph("Executive Summary", styles['Heading2']))
    story.append(Paragraph(
        "This is a native digital PDF created for testing document extraction. "
        "It contains structured text, tables, and proper formatting that should be "
        "easily extractable without OCR.", 
        styles['Normal']
    ))
    story.append(Spacer(1, 12))
    
    # Table 1
    story.append(Paragraph("Revenue Breakdown", styles['Heading2']))
    data1 = [
        ['Quarter', 'Revenue', 'Expenses', 'Profit'],
        ['Q1', '$100,000', '$60,000', '$40,000'],
        ['Q2', '$120,000', '$65,000', '$55,000'],
        ['Q3', '$150,000', '$70,000', '$80,000'],
        ['Q4', '$180,000', '$75,000', '$105,000'],
    ]
    table1 = Table(data1)
    table1.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table1)
    story.append(Spacer(1, 12))
    
    # More text
    story.append(Paragraph("Analysis", styles['Heading2']))
    story.append(Paragraph(
        "The company showed strong growth throughout the year with consistent "
        "quarter-over-quarter improvements. Revenue increased by 80% from Q1 to Q4, "
        "while maintaining healthy profit margins.",
        styles['Normal']
    ))
    story.append(Spacer(1, 12))
    
    # Table 2
    story.append(Paragraph("Department Expenses", styles['Heading2']))
    data2 = [
        ['Department', 'Budget', 'Actual', 'Variance'],
        ['Engineering', '$50,000', '$48,000', '-$2,000'],
        ['Marketing', '$30,000', '$32,000', '+$2,000'],
        ['Sales', '$40,000', '$38,000', '-$2,000'],
        ['Operations', '$20,000', '$19,000', '-$1,000'],
    ]
    table2 = Table(data2)
    table2.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table2)
    
    doc.build(story)
    print(f"✓ Created native digital PDF: {filename}")

if __name__ == "__main__":
    create_native_pdf()
