from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


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


class ProviderManifest(BaseModel):
    runs: list[ManifestRun] = Field(default_factory=list)
    active_run: int = 0


class Manifest(BaseModel):
    version: str = "1"
    providers: dict[str, ProviderManifest] = Field(default_factory=dict)

    def add_run(self, provider: str, run: ManifestRun) -> None:
        if provider not in self.providers:
            self.providers[provider] = ProviderManifest()
        pm = self.providers[provider]
        pm.runs.append(run)
        pm.active_run = len(pm.runs) - 1

    def provider_names(self) -> list[str]:
        return sorted(self.providers.keys())

    def latest_run(self, provider: str) -> ManifestRun | None:
        pm = self.providers.get(provider)
        if pm is None or not pm.runs:
            return None
        return pm.runs[pm.active_run]


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")
