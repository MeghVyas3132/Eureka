import csv
import io

import chardet

from ingestion.parsers.base_parser import BaseParser


class CSVParser(BaseParser):
    def parse(self, file_bytes: bytes) -> list[dict]:
        detected = chardet.detect(file_bytes)
        encoding = detected.get("encoding") or "utf-8"

        try:
            text = file_bytes.decode(encoding, errors="replace")
        except Exception:
            text = file_bytes.decode("utf-8", errors="replace")

        text = text.lstrip("\ufeff")

        reader = csv.DictReader(io.StringIO(text))
        rows: list[dict] = []
        for row in reader:
            normalised = self.normalise_row(row)
            if not normalised or all(v == "" for v in normalised.values()):
                continue
            rows.append(normalised)

        return rows
