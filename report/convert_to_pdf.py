#!/usr/bin/env python3
"""Convert markdown to PDF with styling and images."""
import markdown
from weasyprint import HTML, CSS
from pathlib import Path
import re

# Read markdown
md_path = Path("FINAL_REPORT.md")
md_content = md_path.read_text()

# Fix image paths to be absolute
reports_dir = md_path.parent.absolute()
md_content = re.sub(
    r'!\[([^\]]*)\]\(([^)]+\.png)\)',
    lambda m: f'![{m.group(1)}](file://{reports_dir}/{m.group(2)})',
    md_content
)

# Convert to HTML
html_content = markdown.markdown(
    md_content,
    extensions=['tables', 'fenced_code', 'codehilite']
)

# Add CSS styling
styled_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 40px auto;
            padding: 0 20px;
            color: #333;
        }}
        h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #34495e; border-bottom: 2px solid #95a5a6; padding-bottom: 8px; margin-top: 30px; }}
        h3 {{ color: #7f8c8d; margin-top: 20px; }}
        code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-family: monospace; }}
        pre {{ background: #f4f4f4; padding: 15px; border-radius: 5px; overflow-x: auto; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background: #3498db; color: white; }}
        tr:nth-child(even) {{ background: #f9f9f9; }}
        blockquote {{ border-left: 4px solid #3498db; padding-left: 20px; margin: 20px 0; color: #555; }}
        img {{ max-width: 100%; height: auto; margin: 20px 0; border: 1px solid #ddd; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""

# Generate PDF
pdf_path = Path("Final Report.pdf")
HTML(string=styled_html).write_pdf(pdf_path)

print(f"✅ PDF generated: {pdf_path}")
print(f"   Size: {pdf_path.stat().st_size / 1024:.1f} KB")
