import pymupdf


def load_pdf(file_bytes: bytes) -> str:
    document = pymupdf.open(
        stream=file_bytes,
        filetype="pdf",
    )

    pages: list[str] = []

    for page in document:
        text = page.get_text().strip()

        if text:
            pages.append(text)

    document.close()

    return "\n\n".join(pages)