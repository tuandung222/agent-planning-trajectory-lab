#!/usr/bin/env python3
"""
Trajectory tracing utilities for planning-agent runs.

The tracer writes one JSON object per line (JSONL), designed for:
- offline analysis
- supervised fine-tuning dataset curation
- reward-model / preference data preparation
"""

from __future__ import annotations

import json
import os
import uuid
import hashlib
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_CURRENT_TRACER: ContextVar["TrajectoryTracer | None"] = ContextVar(
    "current_trajectory_tracer",
    default=None
)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _safe_preview(value: Any, max_len: int = 1200) -> str:
    text = str(value)
    if len(text) <= max_len:
        return text
    return text[:max_len] + "...<truncated>"


def _bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off"}


@dataclass
class TrajectoryTracer:
    """Collects and persists trajectory events for one run."""

    topic: str
    provider: str
    model: str
    enabled: bool = True
    output_dir: Path = field(default_factory=lambda: Path("trajectories"))
    run_id: str = field(default_factory=lambda: f"run_{uuid.uuid4().hex[:12]}")

    def __post_init__(self) -> None:
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.output_dir / f"{self.run_id}.jsonl"
        self.summary_path = self.output_dir / f"{self.run_id}.summary.json"

        self._event_count = 0
        self._tool_call_count = 0
        self._tool_error_count = 0

        if self.enabled:
            self.log_event(
                "run_started",
                topic=self.topic,
                provider=self.provider,
                model=self.model,
            )

    def log_event(self, event_type: str, **payload: Any) -> None:
        """Append one event line to JSONL."""
        if not self.enabled:
            return

        self._event_count += 1
        event = {
            "ts_utc": _utc_now_iso(),
            "run_id": self.run_id,
            "idx": self._event_count,
            "event_type": event_type,
            "payload": payload,
        }
        with self.file_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=True) + "\n")

    def log_phase(self, phase: str, status: str, **payload: Any) -> None:
        self.log_event("phase", phase=phase, status=status, **payload)

    def log_tool_call(self, tool: str, **kwargs: Any) -> None:
        self._tool_call_count += 1
        self.log_event("tool_call", tool=tool, kwargs=kwargs)

    def log_tool_result(
        self,
        tool: str,
        ok: bool,
        latency_ms: int,
        result_preview: str,
    ) -> None:
        if not ok:
            self._tool_error_count += 1
        self.log_event(
            "tool_result",
            tool=tool,
            ok=ok,
            latency_ms=latency_ms,
            result_preview=_safe_preview(result_preview),
        )

    def log_message_snapshot(self, role: str, text: str) -> None:
        self.log_event(
            "message_snapshot",
            role=role,
            text_preview=_safe_preview(text),
            text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
        )

    def complete(self, status: str, report_text: str | None = None, error: str | None = None) -> None:
        """Finalize trajectory and write summary JSON."""
        self.log_event("run_completed", status=status, error=error)

        report_sha = None
        report_len = None
        if report_text is not None:
            report_len = len(report_text)
            report_sha = hashlib.sha256(report_text.encode("utf-8")).hexdigest()
            self.log_event(
                "final_report",
                report_len=report_len,
                report_sha256=report_sha,
                report_preview=_safe_preview(report_text),
            )

        summary = {
            "run_id": self.run_id,
            "topic": self.topic,
            "provider": self.provider,
            "model": self.model,
            "status": status,
            "event_count": self._event_count,
            "tool_call_count": self._tool_call_count,
            "tool_error_count": self._tool_error_count,
            "jsonl_path": str(self.file_path),
            "report_len": report_len,
            "report_sha256": report_sha,
            "error": error,
        }
        with self.summary_path.open("w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=True)


def build_tracer_from_env(topic: str, provider: str, model: str) -> TrajectoryTracer:
    enabled = _bool_env("TRACE_TRAJECTORY", True)
    output_dir = Path(os.getenv("TRACE_DIR", "trajectories"))
    return TrajectoryTracer(
        topic=topic,
        provider=provider,
        model=model,
        enabled=enabled,
        output_dir=output_dir,
    )


def get_current_tracer() -> TrajectoryTracer | None:
    return _CURRENT_TRACER.get()


@contextmanager
def tracing_context(tracer: TrajectoryTracer | None):
    token = _CURRENT_TRACER.set(tracer)
    try:
        yield
    finally:
        _CURRENT_TRACER.reset(token)
