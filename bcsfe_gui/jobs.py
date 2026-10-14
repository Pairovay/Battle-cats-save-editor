"""Runs BCSFE features on a separate thread, one at a time."""

from __future__ import annotations

import itertools
import threading
import time
import traceback
from typing import Any, Callable

from .bridge import Bridge, JobCancelled
from .i18n import t


class BusyError(Exception):
    pass


class Job:
    def __init__(self, job_id: int, title: str, kind: str, log_start: int) -> None:
        self.id = job_id
        self.title = title
        self.kind = kind
        self.status = "running"
        self.error: str | None = None
        self.log_start = log_start
        self.started = time.time()
        self.finished: float | None = None
        self.result: Any = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "kind": self.kind,
            "status": self.status,
            "error": self.error,
            "log_start": self.log_start,
            "elapsed": round((self.finished or time.time()) - self.started, 1),
        }


class JobRunner:
    def __init__(self, bridge: Bridge) -> None:
        self.bridge = bridge
        self.lock = threading.Lock()
        self.current: Job | None = None
        self._ids = itertools.count(1)

    def busy(self) -> bool:
        return self.current is not None and self.current.status == "running"

    def start(self, title: str, func: Callable[[], Any], kind: str = "feature") -> Job:
        with self.lock:
            if self.busy():
                raise BusyError(t("busy"))
            self.bridge.log.flush_partial()
            self.bridge.reset_for_job()
            job = Job(next(self._ids), title, kind, self.bridge.log.next_index)
            thread = threading.Thread(target=self._run, args=(job, func), name=f"bcsfe-job-{job.id}", daemon=True)
            self.bridge.job_thread = thread
            self.current = job
            thread.start()
            return job

    def _run(self, job: Job, func: Callable[[], Any]) -> None:
        try:
            job.result = func()
            job.status = "done"
        except SystemExit:
            job.status = "done"
        except JobCancelled:
            self.bridge.log.write_segments([[t("task_stopped"), "w"]])
            job.status = "cancelled"
        except Exception as exc:  # noqa: BLE001 - shown to the user
            tb = traceback.format_exc()
            self.bridge.log.write_segments([["Error: " + (str(exc) or exc.__class__.__name__), "e"]])
            for line in tb.rstrip().splitlines():
                self.bridge.log.write_segments([[line, "trace"]])
            job.error = str(exc) or exc.__class__.__name__
            job.status = "error"
        finally:
            self.bridge.log.flush_partial()
            job.finished = time.time()
            self.bridge.job_thread = None
            self.bridge.auto_answers = []
