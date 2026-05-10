from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass


API_BASE_URL = "https://api.pahrul.my.id/api/posts"
REQUEST_TIMEOUT_SECONDS = 15


class ApiError(Exception):
    def __init__(self, message: str, status_code: int | None = None, errors: dict | None = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.errors = errors or {}


@dataclass
class ApiResponse:
    payload: object
    status_code: int


def parse_json_bytes(raw_bytes: bytes) -> object:
    if not raw_bytes:
        return {}
    return json.loads(raw_bytes.decode("utf-8"))


def normalize_error_message(payload: object, fallback: str) -> tuple[str, dict]:
    if not isinstance(payload, dict):
        return fallback, {}

    message = payload.get("message") or payload.get("error") or fallback
    errors = payload.get("errors")
    if not isinstance(errors, dict):
        errors = {}

    detail_messages: list[str] = []
    for value in errors.values():
        if isinstance(value, list):
            detail_messages.extend(str(item) for item in value)
        elif value:
            detail_messages.append(str(value))

    if detail_messages:
        message = f"{message}\n" + "\n".join(detail_messages)

    return message, errors


def extract_data(payload: object) -> object:
    if isinstance(payload, dict) and "data" in payload:
        return payload["data"]
    return payload


def perform_request(method: str, endpoint: str = "", payload: dict | None = None) -> ApiResponse:
    url = API_BASE_URL if not endpoint else f"{API_BASE_URL}/{endpoint}"
    body = None
    headers = {"Accept": "application/json"}

    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url=url, data=body, headers=headers, method=method)

    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            response_payload = parse_json_bytes(response.read())
            return ApiResponse(payload=response_payload, status_code=response.status)
    except urllib.error.HTTPError as error:
        error_payload = parse_json_bytes(error.read())
        message, errors = normalize_error_message(error_payload, f"HTTP {error.code} error")
        raise ApiError(message=message, status_code=error.code, errors=errors) from error
    except urllib.error.URLError as error:
        reason_text = str(getattr(error, "reason", error))
        lowered = reason_text.lower()
        if "timed out" in lowered:
            raise ApiError("Request timeout. Coba lagi beberapa saat.") from error
        raise ApiError(f"Gagal terhubung ke server: {reason_text}") from error
    except TimeoutError as error:
        raise ApiError("Request timeout. Coba lagi beberapa saat.") from error
