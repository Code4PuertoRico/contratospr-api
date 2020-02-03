import subprocess
from structlog import get_logger

logger = get_logger(__name__)


def pdf_to_png(file, page=1):
    logger.info("Extracting png from pdf...", page=page)

    process = subprocess.Popen(
        ["pdftoppm", "-png", "-f", f"{page}", "-l", f"{page}", "-"],
        stdin=file,
        stdout=subprocess.PIPE,
    )

    return process


def get_pdf_pages(file):
    logger.info("Extracting pages with pdfinfo...")
    process = subprocess.Popen(["pdfinfo", "-"], stdin=file, stdout=subprocess.PIPE)

    output, _ = process.communicate()

    pages = 0

    for line in output.splitlines():
        if b"Pages" in line:
            pages = int(line.split(b":", 1)[1].strip())
            break

    return pages


def tesseract(file):
    logger.info("Extracting with tesseract...")
    process = subprocess.Popen(
        ["tesseract", "-", "-", "quiet"], stdin=file, stdout=subprocess.PIPE
    )

    output, _ = process.communicate()

    return output


def pdf_to_text(file):
    logger.info("Extracting with pdftotext...")
    process = subprocess.Popen(
        ["pdftotext", "-", "-"], stdin=file, stdout=subprocess.PIPE
    )

    output, _ = process.communicate()

    return output


def extract_pdf_text_by_pages(file):
    pages = []
    output = pdf_to_text(file)

    for number, page in enumerate(output.split(b"\f"), start=1):
        text = page.strip().decode("utf-8")

        if text:
            logger.info(
                "Successfully extracted text", number=number, method="pdftotext"
            )
            pages.append({"number": number, "text": text})
        else:
            logger.info("Failure to extract text", number=number, method="pdftotext")

    if not pages:
        file.seek(0)
        pages_number = get_pdf_pages(file)

        for i in range(pages_number):
            page_number = i + 1
            file.seek(0)
            png_file = pdf_to_png(file, page=page_number)
            page = tesseract(png_file.stdout)
            text = page.strip().decode("utf-8")

            if text:
                logger.info(
                    "Successfully extracted text", number=number, method="tesseract"
                )
                pages.append({"number": page_number, "text": text})
            else:
                logger.info(
                    "Failure to extract text", number=number, method="tesseract"
                )

    return pages
