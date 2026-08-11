import pytest
import io
import asyncio
import pypdf
from unittest.mock import patch, MagicMock
from app.utils.file_parser import (
    extract_text_from_file,
    ParsedFileResult,
    MAX_OCR_PAGES,
)

def has_ocr_binaries() -> bool:
    """Helper to check if poppler and tesseract are installed on the running environment."""
    import shutil
    has_tesseract = shutil.which("tesseract") is not None
    
    # Check poppler by checking if pdftoppm is in PATH (required by pdf2image)
    has_poppler = shutil.which("pdftoppm") is not None
    return has_tesseract and has_poppler

# --- Mocked Unit Tests ---

@pytest.mark.anyio
async def test_extract_text_native_pdf_high_density():
    # Mock pypdf reader to return a high density text
    dummy_text = "This is a high density page with lots of actual native text extracted by pdf reader. " * 10
    
    # 500 characters on 1 page is density 500 >= 100
    mock_page = MagicMock()
    mock_page.extract_text.return_value = dummy_text
    
    with patch("pypdf.PdfReader") as MockReader:
        mock_instance = MockReader.return_value
        mock_instance.pages = [mock_page]
        
        # Call file_parser
        res = await extract_text_from_file("spec.pdf", b"dummy pdf bytes")
        
        assert res.method == "native"
        assert dummy_text in res.text
        assert res.error_detail is None

@pytest.mark.anyio
async def test_extract_text_ocr_fallback_on_low_density():
    # Mock page text to be very short (e.g. watermark or page number) -> density 5 < 100
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Page 1"
    
    # Mock pdf2image & pytesseract
    mock_images = [MagicMock()]
    mock_ocr_text = "Successfully extracted OCR text from image"
    
    with patch("pypdf.PdfReader") as MockReader, \
         patch("pdf2image.convert_from_bytes") as mock_convert, \
         patch("pytesseract.image_to_string") as mock_tesseract:
         
        mock_instance = MockReader.return_value
        mock_instance.pages = [mock_page]
        mock_convert.return_value = mock_images
        mock_tesseract.return_value = mock_ocr_text
        
        res = await extract_text_from_file("scanned_spec.pdf", b"dummy pdf bytes")
        
        assert res.method == "ocr"
        assert res.text == mock_ocr_text
        assert res.error_detail is None
        mock_convert.assert_called_once_with(b"dummy pdf bytes", dpi=150, timeout=30)
        mock_tesseract.assert_called_once_with(mock_images[0], timeout=10)

@pytest.mark.anyio
async def test_extract_text_ocr_limit_pages():
    # Mock pypdf reader to return empty text, but with too many pages
    mock_page = MagicMock()
    mock_page.extract_text.return_value = ""
    
    with patch("pypdf.PdfReader") as MockReader:
        mock_instance = MockReader.return_value
        mock_instance.pages = [mock_page] * (MAX_OCR_PAGES + 1)
        
        with pytest.raises(ValueError) as excinfo:
            await extract_text_from_file("huge_scanned.pdf", b"dummy pdf bytes")
            
        assert "exceeds the maximum limits for OCR" in str(excinfo.value)

@pytest.mark.anyio
async def test_extract_text_ocr_timeout_or_failure():
    # Trigger low density native text
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Page 1"
    
    # Mock convert_from_bytes to raise a poppler error
    with patch("pypdf.PdfReader") as MockReader, \
         patch("pdf2image.convert_from_bytes") as mock_convert:
         
        mock_instance = MockReader.return_value
        mock_instance.pages = [mock_page]
        mock_convert.side_effect = Exception("Poppler process died unexpectedly")
        
        res = await extract_text_from_file("scanned.pdf", b"dummy pdf bytes")
        
        assert res.method == "failed"
        assert "Poppler PDF conversion failed" in res.error_detail
        assert res.text == ""

@pytest.mark.anyio
async def test_extract_text_txt_native():
    file_content = b"Simple plain text file contents"
    res = await extract_text_from_file("notes.txt", file_content)
    assert res.method == "native"
    assert res.text == "Simple plain text file contents"

# --- Gated Integration Test ---

@pytest.mark.skipif(not has_ocr_binaries(), reason="OCR system binaries (tesseract, poppler) are not installed")
@pytest.mark.anyio
async def test_ocr_real_execution():
    # This integration test runs ONLY if both tesseract and poppler are installed.
    # We will generate a minimal PDF with no native text (empty page).
    # Since it's blank, OCR should run and return empty text, resulting in a failed method or empty text.
    # Note: Generating a real PDF requires a tool, or we can use a small 1x1 image/PDF bytes structure.
    # Let's write a simple blank PDF structure using bytes:
    # A minimal valid PDF structure containing a single page.
    blank_pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj <</Type/Catalog/Pages 2 0 R>> endobj\n"
        b"2 0 obj <</Type/Pages/Kids[3 0 R]/Count 1>> endobj\n"
        b"3 0 obj <</Type/Page/Parent 2 0 R/MediaBox[0 0 100 100]>> endobj\n"
        b"xref\n"
        b"0 4\n"
        b"0000000000 65535 f\n"
        b"0000000009 00000 n\n"
        b"0000000052 00000 n\n"
        b"0000000101 00000 n\n"
        b"trailer <</Size 4/Root 1 0 R>>\n"
        b"startxref\n"
        b"178\n"
        b"%%EOF"
    )
    res = await extract_text_from_file("blank.pdf", blank_pdf)
    # The blank pdf will fall back to OCR. OCR will execute, but find no text.
    # So it should either return method='failed' or method='ocr' with blank text.
    assert res.method in ("ocr", "failed")
