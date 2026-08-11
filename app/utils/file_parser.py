import io
import asyncio
from dataclasses import dataclass
import pypdf

# Maximum page cap for scanned OCR to prevent memory exhaust
MAX_OCR_PAGES = 15

@dataclass
class ParsedFileResult:
    text: str
    method: str  # "native" | "ocr" | "failed"
    error_detail: str = None

def extract_text_from_pdf_native(file_bytes: bytes) -> str:
    """Extract native text from PDF bytes."""
    pdf_file = io.BytesIO(file_bytes)
    reader = pypdf.PdfReader(pdf_file)
    text_content = []
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text_content.append(page_text)
    return "\n".join(text_content)

def perform_ocr(file_bytes: bytes) -> str:
    """Synchronous CPU-bound OCR logic."""
    # Import pdf2image and pytesseract dynamically to prevent import crashes
    # on machines without local installations unless OCR is actually triggered.
    try:
        from pdf2image import convert_from_bytes
        import pytesseract
    except ImportError as e:
        raise RuntimeError(
            "OCR dependencies missing. Please install 'pytesseract' and 'pdf2image' "
            "and check docs/ocr_setup.md."
        ) from e

    # Render PDF pages to images (150 DPI limit, timeout 30s)
    try:
        images = convert_from_bytes(file_bytes, dpi=150, timeout=30)
    except Exception as e:
        raise RuntimeError(f"Poppler PDF conversion failed: {str(e)}") from e

    if len(images) > MAX_OCR_PAGES:
        raise ValueError(
            f"Scanned PDF exceeds the maximum limits for OCR processing (Max: {MAX_OCR_PAGES} pages, got {len(images)} pages)."
        )

    text_content = []
    for i, img in enumerate(images):
        try:
            # OCR each page with a 10 second timeout
            page_text = pytesseract.image_to_string(img, timeout=10)
            if page_text:
                text_content.append(page_text)
        except pytesseract.TesseractError as e:
            raise RuntimeError(f"Tesseract OCR failed on page {i+1}: {str(e)}") from e
        except Exception as e:
            raise RuntimeError(f"OCR execution timed out or failed on page {i+1}: {str(e)}") from e

    return "\n".join(text_content)

async def extract_text_from_file(filename: str, file_bytes: bytes) -> ParsedFileResult:
    """Extract text from pdf or text files, falling back to OCR if needed.
    
    This function is async-safe and runs blocking OCR calls in separate threads.
    """
    if filename.lower().endswith(".pdf"):
        # 1. First extract using native pypdf
        try:
            native_text = extract_text_from_pdf_native(file_bytes)
        except Exception:
            native_text = ""
        
        # Determine density
        try:
            pdf_file = io.BytesIO(file_bytes)
            reader = pypdf.PdfReader(pdf_file)
            total_pages = len(reader.pages)
        except Exception:
            total_pages = 0
            
        char_density = len(native_text) / total_pages if total_pages > 0 else 0
        
        # Density threshold: at least 100 characters per page on average for native text
        if total_pages > 0 and char_density >= 100:
            return ParsedFileResult(text=native_text, method="native")
            
        # 2. Scanned PDF fallback: run OCR in a thread pool
        if total_pages > MAX_OCR_PAGES:
            raise ValueError(
                f"Scanned PDF exceeds the maximum limits for OCR processing (Max: {MAX_OCR_PAGES} pages, got {total_pages} pages)."
            )
            
        try:
            ocr_text = await asyncio.to_thread(perform_ocr, file_bytes)
            if not ocr_text.strip():
                return ParsedFileResult(
                    text="", 
                    method="failed", 
                    error_detail="OCR executed but found no extractable text in the images."
                )
            return ParsedFileResult(text=ocr_text, method="ocr")
        except Exception as e:
            # Graceful degradation: return method="failed" and let the caller decide
            return ParsedFileResult(text="", method="failed", error_detail=str(e))
            
    # Try reading as text
    try:
        text = file_bytes.decode("utf-8")
        return ParsedFileResult(text=text, method="native")
    except UnicodeDecodeError:
        try:
            text = file_bytes.decode("latin-1")
            return ParsedFileResult(text=text, method="native")
        except UnicodeDecodeError:
            raise ValueError("Unsupported binary file type. Please upload PDF or text files.")
