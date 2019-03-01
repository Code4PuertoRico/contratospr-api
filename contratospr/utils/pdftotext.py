import subprocess


def pdf_to_text(file):
    process = subprocess.Popen(
        ["pdftotext", "-", "-"], stdin=file, stdout=subprocess.PIPE
    )

    output, _ = process.communicate()

    return output
