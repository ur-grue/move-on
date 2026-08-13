from __future__ import annotations

import calendar
import hashlib
import json
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field

HASH_FIELDS = (
    "source_file",
    "sha256",
    "extracted_at",
    "message_count",
    "conversation_count",
    "tool_version",
    "output_sha256",
)


class Message(BaseModel):
    role: str
    content: str


class Metadata(BaseModel):
    source: str
    conversation_id: str
    conversation_title: str = ""
    created_at: str = ""
    updated_at: str = ""


class Conversation(BaseModel):
    format_version: str = "1"
    messages: list[Message]
    metadata: Metadata


class ManifestRun(BaseModel):
    source_file: str
    sha256: str
    extracted_at: str
    message_count: int
    conversation_count: int
    tool_version: str
    output_sha256: str | None = None
    previous_run_hash: str = ""

    def hash_fields(self) -> str:
        """Serialize the fixed-field subset for hash chain computation."""
        data = {field: getattr(self, field) for field in HASH_FIELDS}
        canonical = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ErasureStatus(str, Enum):
    PENDING = "pending"
    SENT = "sent"
    OVERDUE = "overdue"
    COMPLAINT_FILED = "complaint_filed"


def calculate_deadline(sent_date: date) -> date:
    """Calculate GDPR Art. 12(3) deadline: receipt + 1 calendar month."""
    month = sent_date.month
    year = sent_date.year
    if month == 12:
        month = 1
        year += 1
    else:
        month += 1
    last_day = calendar.monthrange(year, month)[1]
    day = min(sent_date.day, last_day)
    return date(year, month, day)


class ProviderManifest(BaseModel):
    runs: list[ManifestRun] = Field(default_factory=list)
    active_run: int = 0
    chain_broken: bool = False
    erasure_status: ErasureStatus = ErasureStatus.PENDING
    erasure_sent_at: str | None = None
    erasure_deadline: str | None = None


class Manifest(BaseModel):
    version: str = "1"
    providers: dict[str, ProviderManifest] = Field(default_factory=dict)

    def add_run(self, provider: str, run: ManifestRun) -> None:
        if provider not in self.providers:
            self.providers[provider] = ProviderManifest()
        pm = self.providers[provider]

        if pm.runs:
            previous = pm.runs[-1]
            run.previous_run_hash = previous.hash_fields()

        pm.runs.append(run)
        pm.active_run = len(pm.runs) - 1

    def verify_chain(self, provider: str) -> list[int]:
        """Return indices of runs where the hash chain is broken."""
        pm = self.providers.get(provider)
        if pm is None or len(pm.runs) < 2:
            return []

        broken = []
        for i in range(1, len(pm.runs)):
            expected = pm.runs[i - 1].hash_fields()
            actual = pm.runs[i].previous_run_hash
            if actual != expected:
                broken.append(i)
        return broken

    def provider_names(self) -> list[str]:
        return sorted(self.providers.keys())

    def latest_run(self, provider: str) -> ManifestRun | None:
        pm = self.providers.get(provider)
        if pm is None or not pm.runs:
            return None
        return pm.runs[pm.active_run]


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")
