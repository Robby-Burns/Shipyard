import io
import pypdf

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract text from PDF bytes using pypdf."""
    pdf_file = io.BytesIO(file_bytes)
    reader = pypdf.PdfReader(pdf_file)
    text_content = []
    for i, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text:
            text_content.append(page_text)
    return "\n".join(text_content)

def extract_text_from_file(filename: str, file_bytes: bytes) -> str:
    """Extract text from pdf or text files."""
    if filename.lower().endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    
    # Try reading as text
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return file_bytes.decode("latin-1")
        except UnicodeDecodeError:
            raise ValueError("Unsupported binary file type. Please upload PDF or text files.")
