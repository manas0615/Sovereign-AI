import os
import shutil
import tempfile
import subprocess
from typing import List, BinaryIO
from sovereign.core.knowledge.parser import DocumentParser, OCRRequiredError
from sovereign.core.knowledge.models import Document, DocumentBlock

class OCRDependencyError(Exception):
    """Raised when the underlying OCR engine is missing."""
    pass

def _find_tesseract() -> str:
    """Find tesseract executable on system or fallback paths."""
    cmd = os.environ.get("TESSERACT_CMD")
    if cmd and os.path.isfile(cmd):
        return cmd
    which = shutil.which("tesseract")
    if which:
        return which
    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return "tesseract"

class OCRParser(DocumentParser):
    def __init__(self):
        self._tesseract_cmd = _find_tesseract()

    def parse(self, document: Document, file_stream: BinaryIO) -> List[DocumentBlock]:
        tess = self._tesseract_cmd
        try:
            subprocess.run([tess, "--version"], capture_output=True, check=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            raise OCRDependencyError(f"Tesseract OCR is not installed or not found at '{tess}'.")

        blocks = []
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(file_stream.read())
            tmp_path = tmp.name

        try:
            result = subprocess.run([tess, tmp_path, "stdout"], capture_output=True, text=True)

            if result.returncode != 0:
                raise ValueError(f"Tesseract failed: {result.stderr}")
            
            text = result.stdout.strip()
            if text:
                blocks.append(DocumentBlock(
                    document_id=document.document_id,
                    page_number=document.metadata.get("page_number", 1) if document.metadata else 1,
                    sequence=0,
                    text=text,
                    block_type="paragraph"
                ))
        finally:
            os.remove(tmp_path)
            
        return blocks
