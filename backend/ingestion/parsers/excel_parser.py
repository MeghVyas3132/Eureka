import io

import pandas as pd

from ingestion.parsers.base_parser import BaseParser


class ExcelParser(BaseParser):
    def parse(self, file_bytes: bytes) -> list[dict]:
        try:
            df = pd.read_excel(io.BytesIO(file_bytes), engine="openpyxl", sheet_name=0, dtype=str)
        except Exception:
            try:
                df = pd.read_excel(io.BytesIO(file_bytes), engine="xlrd", sheet_name=0, dtype=str)
            except Exception as exc:
                raise ValueError(f"Could not parse Excel file: {exc}") from exc

        df = df.dropna(how="all")
        df = df.fillna("")

        rows: list[dict] = []
        for _, row in df.iterrows():
            normalised = self.normalise_row(row.to_dict())
            if not normalised or all(v == "" for v in normalised.values()):
                continue
            rows.append(normalised)

        return rows
