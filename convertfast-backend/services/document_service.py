from pathlib import Path
from fastapi import HTTPException
import subprocess
import os

def pdf_to_word(input_path: Path, output_path: Path) -> Path:
    """
    Converte PDF in DOCX usando pdf2docx.
    Mantiene testo, tabelle e formattazione base.
    """
    try:
        from pdf2docx import Converter
        cv = Converter(str(input_path))
        cv.convert(str(output_path), start=0, end=None)
        cv.close()
        return output_path
    except ImportError:
        raise HTTPException(status_code=500, detail="pdf2docx non installato.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore conversione PDF→Word: {str(e)}")


def _docx_to_html(input_path: Path) -> str:
    """
    Converte DOCX in HTML usando python-docx.
    Estrae testo, paragrafi, tabelle e stili base.
    """
    from docx import Document
    from docx.shared import Pt, RGBColor
    import html

    doc = Document(str(input_path))
    lines = []

    lines.append("""<!DOCTYPE html><html><head><meta charset="UTF-8">
    <style>
      body { font-family: Arial, sans-serif; font-size: 12pt; margin: 2cm; line-height: 1.5; color: #000; }
      h1 { font-size: 18pt; font-weight: bold; margin: 12pt 0 6pt; }
      h2 { font-size: 16pt; font-weight: bold; margin: 10pt 0 5pt; }
      h3 { font-size: 14pt; font-weight: bold; margin: 8pt 0 4pt; }
      p  { margin: 6pt 0; }
      table { border-collapse: collapse; width: 100%; margin: 10pt 0; }
      td, th { border: 1px solid #ccc; padding: 6pt 8pt; }
      th { background: #f0f0f0; font-weight: bold; }
      .bold { font-weight: bold; }
      .italic { font-style: italic; }
      .underline { text-decoration: underline; }
    </style></head><body>""")

    for para in doc.paragraphs:
        text = html.escape(para.text)
        if not text.strip():
            lines.append("<p>&nbsp;</p>")
            continue
        style = para.style.name.lower()
        if 'heading 1' in style:
            lines.append(f"<h1>{text}</h1>")
        elif 'heading 2' in style:
            lines.append(f"<h2>{text}</h2>")
        elif 'heading 3' in style:
            lines.append(f"<h3>{text}</h3>")
        else:
            # Applica stili inline
            parts = []
            for run in para.runs:
                r = html.escape(run.text)
                if run.bold:   r = f"<strong>{r}</strong>"
                if run.italic: r = f"<em>{r}</em>"
                if run.underline: r = f"<u>{r}</u>"
                parts.append(r)
            content = ''.join(parts) if parts else text
            align = para.alignment
            style_attr = ''
            if align and align.name == 'CENTER': style_attr = ' style="text-align:center"'
            elif align and align.name == 'RIGHT': style_attr = ' style="text-align:right"'
            lines.append(f"<p{style_attr}>{content}</p>")

    # Tabelle
    for table in doc.tables:
        lines.append("<table>")
        for i, row in enumerate(table.rows):
            lines.append("<tr>")
            for cell in row.cells:
                tag = "th" if i == 0 else "td"
                lines.append(f"<{tag}>{html.escape(cell.text)}</{tag}>")
            lines.append("</tr>")
        lines.append("</table>")

    lines.append("</body></html>")
    return "\n".join(lines)


def _xlsx_to_html(input_path: Path) -> str:
    """Converte XLSX in HTML usando openpyxl."""
    try:
        import openpyxl
        import html as html_mod
        wb = openpyxl.load_workbook(str(input_path), data_only=True)
        ws = wb.active
        lines = ["""<!DOCTYPE html><html><head><meta charset="UTF-8">
        <style>body{font-family:Arial,sans-serif;font-size:11pt;margin:1.5cm;}
        table{border-collapse:collapse;width:100%;}
        td,th{border:1px solid #ccc;padding:5pt 8pt;font-size:10pt;}
        th{background:#e8e8e8;font-weight:bold;}</style></head><body><table>"""]
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            tag = "th" if i == 0 else "td"
            lines.append("<tr>" + "".join(f"<{tag}>{html_mod.escape(str(c or ''))}</{tag}>" for c in row) + "</tr>")
        lines.append("</table></body></html>")
        return "\n".join(lines)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore lettura Excel: {str(e)}")


def _pptx_to_html(input_path: Path) -> str:
    """Converte PPTX in HTML usando python-pptx."""
    try:
        from pptx import Presentation
        import html as html_mod
        prs = Presentation(str(input_path))
        lines = ["""<!DOCTYPE html><html><head><meta charset="UTF-8">
        <style>body{font-family:Arial,sans-serif;margin:1cm;}
        .slide{page-break-after:always;border:1px solid #ddd;padding:20pt;margin-bottom:20pt;min-height:400pt;}
        h2{font-size:20pt;margin-bottom:10pt;}p{font-size:12pt;margin:4pt 0;}</style></head><body>"""]
        for i, slide in enumerate(prs.slides, 1):
            lines.append(f'<div class="slide"><p style="color:#999;font-size:9pt">Slide {i}</p>')
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    text = html_mod.escape(shape.text.strip())
                    if shape.shape_type == 13: continue
                    lines.append(f"<p>{text}</p>")
            lines.append("</div>")
        lines.append("</body></html>")
        return "\n".join(lines)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore lettura PowerPoint: {str(e)}")


def _html_to_pdf(html_content: str, output_path: Path) -> Path:
    """Converte HTML in PDF usando WeasyPrint (puro Python, no LibreOffice)."""
    try:
        from weasyprint import HTML, CSS
        HTML(string=html_content).write_pdf(
            str(output_path),
            stylesheets=[CSS(string="@page { margin: 2cm; size: A4; }")]
        )
        return output_path
    except ImportError:
        raise HTTPException(status_code=500, detail="WeasyPrint non installato.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore generazione PDF: {str(e)}")


def word_to_pdf(input_path: Path, output_path: Path) -> Path:
    """
    Converte DOCX/DOC in PDF usando python-docx + WeasyPrint.
    Nessuna dipendenza da LibreOffice — funziona con 512MB RAM.
    """
    try:
        ext = input_path.suffix.lower()
        if ext in ('.doc', '.docx', '.odt', '.rtf'):
            html_content = _docx_to_html(input_path)
        else:
            # Testo semplice
            text = input_path.read_text(encoding='utf-8', errors='replace')
            import html as html_mod
            html_content = f"<html><body><pre>{html_mod.escape(text)}</pre></body></html>"
        return _html_to_pdf(html_content, output_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore conversione Word→PDF: {str(e)}")


def excel_to_pdf(input_path: Path, output_path: Path) -> Path:
    """Converte XLSX/XLS in PDF usando openpyxl + WeasyPrint."""
    try:
        html_content = _xlsx_to_html(input_path)
        return _html_to_pdf(html_content, output_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore conversione Excel→PDF: {str(e)}")


def pptx_to_pdf(input_path: Path, output_path: Path) -> Path:
    """Converte PPTX in PDF usando python-pptx + WeasyPrint."""
    try:
        html_content = _pptx_to_html(input_path)
        return _html_to_pdf(html_content, output_path)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore conversione PPTX→PDF: {str(e)}")


def pdf_to_images(input_path: Path, output_dir: Path, fmt: str = "jpg", dpi: int = 150) -> list:
    """
    Converte ogni pagina PDF in immagine.
    Usa PyMuPDF (fitz) se disponibile, altrimenti pdf2image.
    """
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(str(input_path))
        paths = []
        for i, page in enumerate(doc):
            mat = fitz.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat)
            out = output_dir / f"page_{i+1}.{fmt}"
            if fmt.lower() in ("jpg", "jpeg"):
                pix.save(str(out), "jpeg")
            else:
                pix.save(str(out))
            paths.append(out)
        doc.close()
        return paths
    except ImportError:
        raise HTTPException(
            status_code=500,
            detail="PyMuPDF non installato. Esegui: pip install PyMuPDF"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore PDF→Immagini: {str(e)}")
