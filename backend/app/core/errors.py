from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class UpstreamAPIError(Exception):
    status_code: int
    code: str | None
    message: str

    def to_dict(self) -> dict:
        return {
            "status": "error",
            "code": self.code,
            "message": self.message,
        }
