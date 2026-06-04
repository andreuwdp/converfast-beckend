from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
from utils.files import save_upload, generate_output_path, file_response
from services.document_service import pdf_to_word, word_to_pdf, excel_to_pdf, pptx_to_pdf
import zipfile
from pathlib import Path

router = APIRouter()


def _check_pdf(filename: str):
    if not filename or not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Carica un file PDF valido (.pdf).")


@router.post("/pdf-to-word")
async def api_pdf_to_word(file: UploadFile = File(...)):
    """Converte PDF in DOCX."""
    _check_pdf(file.filename)
    input_path = await save_upload(file)
    output_path = generate_output_path("docx")
    try:
        pdf_to_word(input_path, output_path)
        return file_response(output_path, file.filename, "docx")
    finally:
        if input_path.exists(): input_path.unlink()


@router.post("/word-to-pdf")
async def api_word_to_pdf(file: UploadFile = File(...)):
    """Converte DOCX/DOC in PDF."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nessun file caricato.")
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in {"doc", "docx", "odt", "rtf", "txt"}:
        raise HTTPException(status_code=400, detail=f"Formato non supportato: .{ext}")
    input_path = await save_upload(file)
    output_path = generate_output_path("pdf")
    try:
        word_to_pdf(input_path, output_path)
        return file_response(output_path, file.filename, "pdf")
    finally:
        if input_path.exists(): input_path.unlink()


@router.post("/excel-to-pdf")
async def api_excel_to_pdf(file: UploadFile = File(...)):
    """Converte XLSX/XLS in PDF."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nessun file caricato.")
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in {"xls", "xlsx", "ods", "csv"}:
        raise HTTPException(status_code=400, detail=f"Formato non supportato: .{ext}")
    input_path = await save_upload(file)
    output_path = generate_output_path("pdf")
    try:
        excel_to_pdf(input_path, output_path)
        return file_response(output_path, file.filename, "pdf")
    finally:
        if input_path.exists(): input_path.unlink()


@router.post("/pptx-to-pdf")
async def api_pptx_to_pdf(file: UploadFile = File(...)):
    """Converte PPTX/PPT in PDF."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="Nessun file caricato.")
    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in {"ppt", "pptx", "odp"}:
        raise HTTPException(status_code=400, detail=f"Formato non supportato: .{ext}")
    input_path = await save_upload(file)
    output_path = generate_output_path("pdf")
    try:
        pptx_to_pdf(input_path, output_path)
        return file_response(output_path, file.filename, "pdf")
    finally:
        if input_path.exists(): input_path.unlink()


@router.post("/compress-pdf")
async def api_compress_pdf(file: UploadFile = File(...)):
    """
    Comprime un PDF usando PyMuPDF.
    Riduce qualità immagini e rimuove dati inutili.
    """
    _check_pdf(file.filename)
    input_path = await save_upload(file)
    output_path = generate_output_path("pdf")
    try:
        import fitz
        doc = fitz.open(str(input_path))
        # Salva con compressione garbage collection e deflate
        doc.save(
            str(output_path),
            garbage=4,
            deflate=True,
            deflate_images=True,
            deflate_fonts=True,
            clean=True
        )
        doc.close()
        orig = input_path.stat().st_size
        comp = output_path.stat().st_size
        saved = round((1 - comp/orig)*100, 1)
        response = file_response(output_path, file.filename, "pdf")
        response.headers["X-Original-Size"]   = str(orig)
        response.headers["X-Compressed-Size"] = str(comp)
        response.headers["X-Saved-Percent"]   = str(max(0, saved))
        return response
    except ImportError:
        raise HTTPException(status_code=500, detail="PyMuPDF non installato.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore compressione PDF: {str(e)}")
    finally:
        if input_path.exists(): input_path.unlink()


@router.post("/merge-pdf")
async def api_merge_pdf(
    file: UploadFile = File(...),
    file2: UploadFile = File(None),
    file3: UploadFile = File(None),
):
    """
    Unisce 1-3 file PDF in uno solo.
    Carica file, file2, file3 come form fields.
    """
    _check_pdf(file.filename)
    paths = []
    for f in [file, file2, file3]:
        if f and f.filename:
            paths.append(await save_upload(f))
    output_path = generate_output_path("pdf")
    try:
        import fitz
        merged = fitz.open()
        for p in paths:
            doc = fitz.open(str(p))
            merged.insert_pdf(doc)
            doc.close()
        merged.save(str(output_path), garbage=3, deflate=True)
        merged.close()
        return file_response(output_path, file.filename, "pdf")
    except ImportError:
        raise HTTPException(status_code=500, detail="PyMuPDF non installato.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore unione PDF: {str(e)}")
    finally:
        for p in paths:
            if p.exists(): p.unlink()


@router.post("/split-pdf")
async def api_split_pdf(
    file: UploadFile = File(...),
    pages: str = Form("all"),
):
    """
    Divide un PDF.
    pages: 'all' (ogni pagina in file separato) oppure '1,3,5' o '2-5'
    Ritorna ZIP con i file risultanti.
    """
    _check_pdf(file.filename)
    input_path = await save_upload(file)
    output_dir = input_path.parent / f"split_{input_path.stem}"
    output_dir.mkdir(exist_ok=True)
    zip_path = generate_output_path("zip")

    try:
        import fitz
        doc = fitz.open(str(input_path))
        total = len(doc)

        # Parsing selezione pagine
        if pages.strip().lower() == "all":
            page_list = list(range(total))
        else:
            page_list = []
            for part in pages.split(","):
                part = part.strip()
                if "-" in part:
                    a, b = part.split("-")
                    page_list += list(range(int(a)-1, min(int(b), total)))
                elif part.isdigit():
                    idx = int(part) - 1
                    if 0 <= idx < total:
                        page_list.append(idx)

        if not page_list:
            raise HTTPException(status_code=400, detail="Nessuna pagina valida selezionata.")

        # Crea un PDF per ogni pagina selezionata
        out_files = []
        for i, pg in enumerate(page_list):
            new_doc = fitz.open()
            new_doc.insert_pdf(doc, from_page=pg, to_page=pg)
            out_file = output_dir / f"pagina_{pg+1}.pdf"
            new_doc.save(str(out_file))
            new_doc.close()
            out_files.append(out_file)
        doc.close()

        # Crea ZIP
        with zipfile.ZipFile(str(zip_path), "w", zipfile.ZIP_DEFLATED) as zf:
            for f in out_files:
                zf.write(str(f), f.name)

        stem = Path(file.filename).stem
        return FileResponse(
            path=str(zip_path),
            filename=f"{stem}_pagine.zip",
            media_type="application/zip"
        )

    except HTTPException:
        raise
    except ImportError:
        raise HTTPException(status_code=500, detail="PyMuPDF non installato.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Errore divisione PDF: {str(e)}")
    finally:
        if input_path.exists(): input_path.unlink()
        if output_dir.exists():
            import shutil
            shutil.rmtree(str(output_dir), ignore_errors=True)
