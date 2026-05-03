from abc import ABC, abstractmethod


class BaseParser(ABC):
    """
    All parsers return a list of dicts.
    Column names are normalised: lowercased, stripped, spaces replaced with underscores.
    Values are raw strings; validation happens in the validator layer.
    """

    @abstractmethod
    def parse(self, file_bytes: bytes) -> list[dict]:
        """
        Parse file bytes into a list of row dicts.
        Each dict has string keys and raw string values.
        Never raises on bad data unless the file is unreadable.
        """
        raise NotImplementedError

    @staticmethod
    def normalise_key(key: str) -> str:
        return (
            key.strip()
            .lower()
            .replace(" ", "_")
            .replace("-", "_")
            .replace("/", "_")
        )

    @staticmethod
    def normalise_row(row: dict) -> dict:
        return {
            BaseParser.normalise_key(str(k)): str(v).strip() if v is not None else ""
            for k, v in row.items()
            if k is not None
        }
