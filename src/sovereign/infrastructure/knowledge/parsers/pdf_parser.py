"""PDF parser supporting digital text extraction and scanned-page OCR fallback."""

import io
import os
import sys
import tempfile
import subprocess
from typing import List, BinaryIO, Optional
import pypdf

from sovereign.core.knowledge.parser import DocumentParser, OCRRequiredError
from sovereign.core.knowledge.models import Document, DocumentBlock


def _render_pdf_page_native(pdf_path: str, page_index: int, scale: int = 3) -> bytes:
    """Render a single PDF page to PNG bytes using Windows WinRT runtime API."""
    full_pdf_path = os.path.abspath(pdf_path).replace("'", "''")
    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp_out:
        tmp_out_path = tmp_out.name.replace("'", "''")

    ps_code = f"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Runtime.WindowsRuntime

$asTaskGeneric = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {{ 
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.IsGenericMethod 
}} | Select-Object -First 1

$asTaskAction = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {{
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and -not $_.IsGenericMethod
}} | Select-Object -First 1

function Await-Task($op, $t) {{
    $m = $asTaskGeneric.MakeGenericMethod($t)
    $task = $m.Invoke($null, @($op))
    $task.Wait()
    return $task.Result
}}

function Await-Action($op) {{
    $task = $asTaskAction.Invoke($null, @($op))
    $task.Wait()
}}

[Windows.Data.Pdf.PdfDocument, Windows.Data.Pdf, ContentType = WindowsRuntime] | Out-Null
[Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime] | Out-Null
[Windows.Storage.FileAccessMode, Windows.Storage, ContentType = WindowsRuntime] | Out-Null
[Windows.Data.Pdf.PdfPageRenderOptions, Windows.Data.Pdf, ContentType = WindowsRuntime] | Out-Null

$pdfPath = [System.IO.Path]::GetFullPath('{full_pdf_path}')
$outPath = [System.IO.Path]::GetFullPath('{tmp_out_path}')

$storageFileOp = [Windows.Storage.StorageFile]::GetFileFromPathAsync($pdfPath)
$storageFile = Await-Task $storageFileOp ([Windows.Storage.StorageFile])

$docOp = [Windows.Data.Pdf.PdfDocument]::LoadFromFileAsync($storageFile)
$doc = Await-Task $docOp ([Windows.Data.Pdf.PdfDocument])

if ({page_index} -ge $doc.PageCount) {{
    throw "Page index {page_index} out of range (total pages: $($doc.PageCount))"
}}

$page = $doc.GetPage([uint32]{page_index})

$destDir = [System.IO.Path]::GetDirectoryName($outPath)
$destName = [System.IO.Path]::GetFileName($outPath)

$folderOp = [Windows.Storage.StorageFolder]::GetFolderFromPathAsync($destDir)
$folder = Await-Task $folderOp ([Windows.Storage.StorageFolder])

$createdFileOp = $folder.CreateFileAsync($destName, [Windows.Storage.CreationCollisionOption]::ReplaceExisting)
$destFile = Await-Task $createdFileOp ([Windows.Storage.StorageFile])

$streamOp = $destFile.OpenAsync([Windows.Storage.FileAccessMode]::ReadWrite)
$stream = Await-Task $streamOp ([Windows.Storage.Streams.IRandomAccessStream])

$options = New-Object Windows.Data.Pdf.PdfPageRenderOptions
$options.DestinationWidth = [uint32]($page.Size.Width * {scale})
$options.DestinationHeight = [uint32]($page.Size.Height * {scale})

$renderOp = $page.RenderToStreamAsync($stream, $options)
Await-Action $renderOp

$stream.Dispose()
$page.Dispose()
"""
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", ps_code],
            capture_output=True,
            text=True,
            timeout=30
        )
        if proc.returncode != 0:
            raise RuntimeError(f"Native PDF rasterization failed: {proc.stderr}")
        with open(tmp_out_path, "rb") as f:
            return f.read()
    finally:
        if os.path.exists(tmp_out_path):
            try:
                os.remove(tmp_out_path)
            except OSError:
                pass


class PDFParser(DocumentParser):
    
    def __init__(self, ocr_parser: Optional[DocumentParser] = None):
        self._ocr_parser = ocr_parser

    def parse(self, document: Document, file_stream: BinaryIO) -> List[DocumentBlock]:
        pdf_bytes = file_stream.read()
        try:
            reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        except Exception as e:
            raise ValueError(f"Failed to read PDF: {e}")
            
        blocks: List[DocumentBlock] = []
        sequence = 0
        total_pages = len(reader.pages)
        
        if total_pages == 0:
            return blocks

        # Temporary PDF file for native rasterization if needed
        tmp_pdf_path = None
        
        try:
            for i, page in enumerate(reader.pages):
                page_number = i + 1
                text = page.extract_text()
                
                # Check if page contains meaningful digital text
                has_meaningful_text = bool(text and len(text.strip()) >= 50)
                
                if has_meaningful_text:
                    paragraphs = text.strip().split('\n\n')
                    for p in paragraphs:
                        clean_p = p.strip()
                        if clean_p:
                            block = DocumentBlock(
                                document_id=document.document_id,
                                page_number=page_number,
                                section=None,
                                block_type="paragraph",
                                sequence=sequence,
                                text=clean_p
                            )
                            blocks.append(block)
                            sequence += 1
                else:
                    # Page is scanned or image-only
                    if self._ocr_parser is None:
                        raise OCRRequiredError(
                            f"PDF {document.filename} appears to be an image-only or scanned PDF. OCR is required."
                        )
                    
                    # Attempt native page rasterization first
                    raster_bytes = None
                    try:
                        if tmp_pdf_path is None:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_pdf:
                                tmp_pdf.write(pdf_bytes)
                                tmp_pdf_path = tmp_pdf.name
                        raster_bytes = _render_pdf_page_native(tmp_pdf_path, i, scale=3)
                    except Exception:
                        raster_bytes = None

                    if raster_bytes:
                        meta = document.metadata.copy() if document.metadata else {}
                        meta["page_number"] = page_number
                        img_doc = Document(
                            document_id=document.document_id,
                            filename=f"{document.filename}_page_{page_number}.png",
                            source_path=document.source_path,
                            document_type="image",
                            file_size=len(raster_bytes),
                            content_hash=document.content_hash,
                            metadata=meta
                        )
                        ocr_blocks = self._ocr_parser.parse(img_doc, io.BytesIO(raster_bytes))
                        for block in ocr_blocks:
                            block.sequence = sequence
                            blocks.append(block)
                            sequence += 1
                    else:
                        # Fallback: extract images embedded directly in page
                        page_images = getattr(page, "images", [])
                        if page_images:
                            for img in page_images:
                                img_stream = io.BytesIO(img.data)
                                meta = document.metadata.copy() if document.metadata else {}
                                meta["page_number"] = page_number
                                img_doc = Document(
                                    document_id=document.document_id,
                                    filename=f"{document.filename}_page_{page_number}_{img.name}",
                                    source_path=document.source_path,
                                    document_type="image",
                                    file_size=len(img.data),
                                    content_hash=document.content_hash,
                                    metadata=meta
                                )
                                ocr_blocks = self._ocr_parser.parse(img_doc, img_stream)
                                for block in ocr_blocks:
                                    block.sequence = sequence
                                    blocks.append(block)
                                    sequence += 1
        finally:
            if tmp_pdf_path and os.path.exists(tmp_pdf_path):
                try:
                    os.remove(tmp_pdf_path)
                except OSError:
                    pass

        return blocks

