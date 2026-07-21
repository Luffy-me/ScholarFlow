"""Pipeline stage failures with structured context."""

from __future__ import annotations


class PipelineStageError(RuntimeError):
    def __init__(self, stage: str, message: str) -> None:
        self.stage = stage
        self.message = message
        super().__init__(f"[{stage}] {message}")
