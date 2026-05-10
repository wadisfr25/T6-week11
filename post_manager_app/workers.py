from __future__ import annotations

import traceback

from PySide6.QtCore import QObject, QRunnable, Signal

from post_manager_app.api import ApiError, perform_request


class WorkerSignals(QObject):
    started = Signal(str)
    finished = Signal(str, object)
    failed = Signal(str, str, int, object)


class ApiWorker(QRunnable):
    def __init__(self, operation_name: str, method: str, endpoint: str = "", payload: dict | None = None):
        super().__init__()
        self.operation_name = operation_name
        self.method = method
        self.endpoint = endpoint
        self.payload = payload
        self.signals = WorkerSignals()

    def run(self) -> None:
        self.signals.started.emit(self.operation_name)
        try:
            result = perform_request(self.method, self.endpoint, self.payload)
            self.signals.finished.emit(self.operation_name, result)
        except ApiError as error:
            self.signals.failed.emit(
                self.operation_name,
                error.message,
                error.status_code or 0,
                error.errors,
            )
        except Exception:
            self.signals.failed.emit(
                self.operation_name,
                "Terjadi error tidak terduga.\n" + traceback.format_exc(limit=1),
                0,
                {},
            )
