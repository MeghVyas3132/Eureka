import io

import pdfplumber

from ingestion.parsers.base_parser import BaseParser


class PDFParser(BaseParser):
    MIN_COLUMNS = 2

    def parse(self, file_bytes: bytes) -> list[dict]:
        rows: list[dict] = []

        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        if not table or len(table) < 2:
                            continue

                        raw_header = table[0]
                        if not raw_header or len(raw_header) < self.MIN_COLUMNS:
                            continue

                        header = [self.normalise_key(str(h or "")) for h in raw_header]
                        if all(h == "" for h in header):
                            continue

                        for row in table[1:]:
                            if row is None:
                                continue
                            padded = list(row) + [""] * (len(header) - len(row))
                            row_dict = {
                                header[i]: str(padded[i]).strip() if padded[i] is not None else ""
                                for i in range(len(header))
                            }
                            if all(v == "" for v in row_dict.values()):
                                continue
                            rows.append(row_dict)

                        if rows:
                            break

                    if rows:
                        break
        except Exception as exc:
            raise ValueError(f"Could not extract table from PDF: {exc}") from exc

        if not rows:
            raise ValueError(
                "No data table found in PDF. Ensure the PDF contains a table with a header row. "
                "Scanned/image PDFs are not supported."
            )

        return rows
