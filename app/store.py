from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock

from app.models.dataset import AnalysisResult, NormalizedDataset


@dataclass
class SessionRecord:
    id: str
    path: Path
    filename: str
    dataset: NormalizedDataset | None = None
    analysis: AnalysisResult | None = None
    sheets: list[str] = field(default_factory=list)


class SessionStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._items: dict[str, SessionRecord] = {}

    def put(self, record: SessionRecord) -> None:
        with self._lock:
            self._items[record.id] = record

    def get(self, session_id: str) -> SessionRecord | None:
        with self._lock:
            return self._items.get(session_id)

    def update(self, record: SessionRecord) -> None:
        self.put(record)


store = SessionStore()
