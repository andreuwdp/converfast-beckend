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


def word_to_pdf(input_path: Path, output_path: Path) -> Path:
    """
    Converte DOCX in PDF usando LibreOffice headless.
    Richiede LibreOffice installato sul server.
    """
    output_dir = output_path.parent
    try:
        result = subprocess.run(
            [
                "libreoffice", "--headless", "--convert-to", "pdf",
                "--outdir", str(output_dir), str(input_path)
            ],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            raise Exception(result.stderr)

        # LibreOffice genera il file con lo stesso stem dell'input
        generated = output_dir / (input_path.stem + ".pdf")
        if generated.exists() and generated != output_path:
            generated.rename(output_path)

        return output_path

    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="LibreOffice non trovato. Installalo sul server: apt-get install libreoffice"
        )
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Conversione timeout. File troppo grande.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore conversione Word→PDF: {str(e)}")


def excel_to_pdf(input_path: Path, output_path: Path) -> Path:
    """Converte XLSX/XLS in PDF usando LibreOffice."""
    return word_to_pdf(input_path, output_path)  # stessa logica


def pptx_to_pdf(input_path: Path, output_path: Path) -> Path:
    """Converte PPTX in PDF usando LibreOffice."""
    return word_to_pdf(input_path, output_path)


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
