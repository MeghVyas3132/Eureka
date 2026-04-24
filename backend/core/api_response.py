from typing import Any


def success_response(data: Any, message: str) -> dict[str, Any]:
    return {
        "data": data,
        "message": message,
    }


def error_payload(error: str, detail: Any) -> dict[str, Any]:
    return {
        "error": error,
        "detail": detail,
    }
