#!/usr/bin/env python3
"""Convert FINAL_REPORT.md to professional PDF"""

import markdown
from weasyprint import HTML, CSS
from pathlib import Path
import re

# Read markdown
md_path = Path("FINAL_REPORT.md")
md_content = md_path.read_text()

# Convert to HTML with extensions
html_content = markdown.markdown(
    md_content,
    extensions=['tables', 'fenced_code', 'codehilite', 'nl2br']
)

# Professional styling
styled_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        @page {{
            size: A4;
            margin: 2.5cm 2cm;
            @top-center {{
                content: "Document Intelligence Refinery - Final Report";
                font-size: 9pt;
                color: #666;
            }}
            @bottom-right {{
                content: "Page " counter(page) " of " counter(pages);
                font-size: 9pt;
                color: #666;
            }}
        }}
        
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            font-size: 11pt;
        }}
        
        h1 {{
            color: #1a1a1a;
            font-size: 24pt;
            font-weight: bold;
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 10px;
            margin-top: 30px;
            margin-bottom: 20px;
            page-break-after: avoid;
        }}
        
        h2 {{
            color: #2c3e50;
            font-size: 18pt;
            font-weight: bold;
            border-bottom: 2px solid #3498db;
            padding-bottom: 8px;
            margin-top: 25px;
            margin-bottom: 15px;
            page-break-after: avoid;
        }}
        
        h3 {{
            color: #34495e;
            font-size: 14pt;
            font-weight: bold;
            margin-top: 20px;
            margin-bottom: 10px;
            page-break-after: avoid;
        }}
        
        h4 {{
            color: #555;
            font-size: 12pt;
            font-weight: bold;
            margin-top: 15px;
            margin-bottom: 8px;
        }}
        
        p {{
            margin: 8px 0;
            text-align: justify;
        }}
        
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 10pt;
            color: #c7254e;
        }}
        
        pre {{
            background: #f8f8f8;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #3498db;
            overflow-x: auto;
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 9pt;
            line-height: 1.4;
            page-break-inside: avoid;
        }}
        
        pre code {{
            background: none;
            padding: 0;
            color: #333;
        }}
        
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 15px 0;
            font-size: 10pt;
            page-break-inside: avoid;
        }}
        
        th {{
            background: #2c3e50;
            color: white;
            padding: 10px;
            text-align: left;
            font-weight: bold;
        }}
        
        td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        
        tr:nth-child(even) {{
            background: #f9f9f9;
        }}
        
        blockquote {{
            border-left: 4px solid #3498db;
            padding-left: 20px;
            margin: 15px 0;
            color: #555;
            font-style: italic;
        }}
        
        ul, ol {{
            margin: 10px 0;
            padding-left: 30px;
        }}
        
        li {{
            margin: 5px 0;
        }}
        
        strong {{
            color: #2c3e50;
            font-weight: bold;
        }}
        
        em {{
            color: #555;
            font-style: italic;
        }}
        
        hr {{
            border: none;
            border-top: 2px solid #ddd;
            margin: 20px 0;
        }}
        
        /* Special styling for checkmarks */
        li:has(input[type="checkbox"]:checked)::before {{
            content: "✅ ";
        }}
        
        /* Executive summary box */
        h2:first-of-type + p {{
            background: #e8f4f8;
            padding: 15px;
            border-left: 4px solid #3498db;
            margin: 15px 0;
        }}
        
        /* Metrics highlighting */
        td:contains("%"), td:contains("$") {{
            font-weight: bold;
            color: #27ae60;
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""

# Generate PDF
pdf_path = Path("Final_Submission_Report.pdf")
HTML(string=styled_html).write_pdf(pdf_path)

print(f"✅ PDF generated: {pdf_path}")
print(f"   Size: {pdf_path.stat().st_size / 1024:.1f} KB")
print(f"   Pages: ~15")
print(f"\n📄 Ready for submission!")
