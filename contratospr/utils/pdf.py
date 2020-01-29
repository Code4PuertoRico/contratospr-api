import subprocess


def pdf_to_png(file, page=1):
    process = subprocess.Popen(
        ["pdftoppm", "-png", "-f", f"{page}", "-l", f"{page}", "-"],
        stdin=file,
        stdout=subprocess.PIPE,
    )

    return process


def get_pdf_pages(file):
    process = subprocess.Popen(["pdfinfo", "-"], stdin=file, stdout=subprocess.PIPE)

    output, _ = process.communicate()

    pages = 0

    for line in output.splitlines():
        if b"Pages" in line:
            pages = int(line.split(b":", 1)[1].strip())
            break

    return pages


def tesseract(file):
    process = subprocess.Popen(
        ["tesseract", "-", "-", "quiet"], stdin=file, stdout=subprocess.PIPE
    )

    output, _ = process.communicate()

    return output


def pdf_to_text(file):
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
            pages.append({"number": number, "text": text})

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
                pages.append({"number": page_number, "text": text})

    return pages
