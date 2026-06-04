from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from utils.files import save_upload, generate_output_path, file_response
from services.document_service import pdf_to_word, word_to_pdf, excel_to_pdf, pptx_to_pdf

router = APIRouter()


@router.post("/pdf-to-word")
async def api_pdf_to_word(file: UploadFile = File(...)):
    """
    Converte PDF in DOCX (Word).
    Mantiene testo, tabelle e formattazione.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Carica un file PDF valido.")

    input_path = await save_upload(file)
    output_path = generate_output_path("docx")

    try:
        pdf_to_word(input_path, output_path)
        return file_response(output_path, file.filename, "docx")
    finally:
        if input_path.exists():
            input_path.unlink()


@router.post("/word-to-pdf")
async def api_word_to_pdf(file: UploadFile = File(...)):
    """
    Converte DOCX/DOC in PDF usando LibreOffice.
    """
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
        if input_path.exists():
            input_path.unlink()


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
        if input_path.exists():
            input_path.unlink()


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
        if input_path.exists():
            input_path.unlink()
