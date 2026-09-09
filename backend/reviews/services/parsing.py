"""Extract raw text from an uploaded contract file.

Kept deliberately small and format-specific rather than one clever
do-everything function, so a new format is one new branch, not a rewrite.
"""
import io

from docx import Document
from pypdf import PdfReader


class UnsupportedFileType(Exception):
    pass


class UnreadableFile(Exception):
    pass


def extract_text(filename: str, raw_bytes: bytes) -> str:
    ext = (filename.rsplit(".", 1)[-1] if "." in filename else "").lower()

    if ext == "txt":
        try:
            return raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return raw_bytes.decode("latin-1")

    if ext == "docx":
        try:
            doc = Document(io.BytesIO(raw_bytes))
        except Exception as exc:
            raise UnreadableFile(
                "Couldn't open this .docx file — it may be corrupted or password-protected."
            ) from exc
        return "\n".join(p.text for p in doc.paragraphs)

    if ext == "pdf":
        try:
            reader = PdfReader(io.BytesIO(raw_bytes))
            if reader.is_encrypted:
                raise UnreadableFile("This PDF is password-protected. Remove the password and re-upload.")
            pages = [page.extract_text() or "" for page in reader.pages]
        except UnreadableFile:
            raise
        except Exception as exc:
            raise UnreadableFile(
                "Couldn't extract text from this PDF — it may be a scanned image without a "
                "text layer. Try exporting/re-saving it as text-based PDF, or upload as .txt/.docx."
            ) from exc
        text = "\n".join(pages)
        if not text.strip():
            raise UnreadableFile(
                "No extractable text found in this PDF — it looks like a scanned image "
                "without OCR. Try a text-based PDF, .docx, or .txt instead."
            )
        return text

    raise UnsupportedFileType(f"Unsupported file type '.{ext}'. Upload a .txt, .docx, or .pdf file.")
