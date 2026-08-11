# OCR Local Windows Setup Guide

To run scanned PDF OCR features in your local Windows environment (outside of Docker), you need to install the following binary dependencies and add them to your path.

## 1. Install Poppler (for pdf2image)
1. Download the latest Poppler binary package for Windows (e.g., from [poppler-windows](https://github.com/oschwartz10612/poppler-windows/releases) or conda).
2. Extract the downloaded folder to a location on your computer (e.g., `C:\Program Files\poppler`).
3. Add the `bin` folder (e.g., `C:\Program Files\poppler\Library\bin` or `C:\Program Files\poppler\bin`) to your Windows User or System Environment Variables **PATH**.

## 2. Install Tesseract (for pytesseract)
1. Download the Windows installer for Tesseract OCR from [UB-Mannheim Tesseract](https://github.com/UB-Mannheim/tesseract/wiki).
2. Run the installer. By default, it installs to `C:\Program Files\Tesseract-OCR`.
3. Add `C:\Program Files\Tesseract-OCR` to your Environment Variables **PATH**.
4. (Optional) Define the `TESSDATA_PREFIX` environment variable pointing to the `tessdata` subfolder (e.g., `C:\Program Files\Tesseract-OCR\tessdata`) if pytesseract cannot find the language files.

## Troubleshooting
If you encounter `TesseractNotFoundError` or `pdf2image` exceptions:
- **Server crash avoidance:** The backend dynamically checks for these binaries and handles missing dependencies gracefully, reporting the issue via the Intake chat rather than crashing.
- **Verify PATH:** Restart your terminal/VS Code/IDE after adding variables to PATH so they are inherited.
- **Direct Path configuration:** If you cannot modify path, you can set the `tesseract_cmd` path directly in code/configuration if needed.
