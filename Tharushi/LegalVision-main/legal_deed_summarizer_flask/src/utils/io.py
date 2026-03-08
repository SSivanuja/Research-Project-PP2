import os
from io import BytesIO

import pdfplumber
from docx import Document
from PIL import Image
import pytesseract


def read_uploaded_file(file_storage) -> str:
    """
    Universal reader for:
    - txt
    - pdf
    - docx
    - png/jpg/jpeg
    - scanned pdf (OCR fallback)
    """

    filename = getattr(file_storage, "filename", "") or ""
    ext = os.path.splitext(filename.lower())[1]

    # Read raw bytes
    data = file_storage.read()

    # ========================
    # TXT
    # ========================
    if ext == ".txt":
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data.decode("latin-1", errors="ignore")

    # ========================
    # PDF
    # ========================
    if ext == ".pdf":
        text = ""
        with pdfplumber.open(BytesIO(data)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"

        # If no text extracted → likely scanned PDF → use OCR
        if not text.strip():
            text = ocr_pdf(BytesIO(data))

        return text.strip()

    # ========================
    # DOCX
    # ========================
    if ext == ".docx":
        doc = Document(BytesIO(data))
        return "\n".join([p.text for p in doc.paragraphs])

    # ========================
    # IMAGE (OCR)
    # ========================
    if ext in [".png", ".jpg", ".jpeg"]:
        image = Image.open(BytesIO(data))
        return pytesseract.image_to_string(image)

    raise ValueError(
        "Unsupported file format. Allowed: .txt, .pdf, .docx, .png, .jpg, .jpeg"
    )


def ocr_pdf(file_like) -> str:
    """
    OCR fallback for scanned PDFs
    """
    text = ""
    with pdfplumber.open(file_like) as pdf:
        for page in pdf.pages:
            image = page.to_image(resolution=300).original
            text += pytesseract.image_to_string(image) + "\n"
    return text