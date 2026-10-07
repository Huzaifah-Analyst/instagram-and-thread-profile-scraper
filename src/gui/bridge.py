"""Thread-safe bridge between ``MultiWorkerScraper`` and the Tk main loop (TSK-204).

The scraper runs on a background thread. Its progress callbacks only put
events on a ``queue.Queue``; the GUI drains that queue with ``poll()`` from a
``root.after()`` timer, so widgets are only ever touched on the Tk thread.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional, Protocol, Union

logger = logging.getLogger(__name__)


class RunState(str, Enum):
    """Lifecycle of a checking run as seen by the GUI."""

    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"


@dataclass
class ProgressEvent:
    """One account finished."""

    done: int
    total: int
    record: dict


@dataclass
class FinishedEvent:
    """The run ended (normally, by ``stop()``, or by a session block)."""

    records: list[dict]
    stop_reason: Optional[str]
    elapsed: float


@dataclass
class ErrorEvent:
    """The run crashed; ``message`` is shown to the user."""

    message: str


BridgeEvent = Union[ProgressEvent, FinishedEvent, ErrorEvent]


class ScraperLike(Protocol):
    """The subset of ``MultiWorkerScraper`` the bridge relies on."""

    stop_reason: Optional[str]

    def run(self, usernames: list[str]) -> list[dict]: ...
    def pause(self) -> None: ...
    def resume(self) -> None: ...
    def stop(self, reason: str = ...) -> None: ...


ScraperFactory = Callable[[str, Callable[[int, int, dict], None]], ScraperLike]


@dataclass
class _Run:
    """Per-run bookkeeping."""

    scraper: ScraperLike
    thread: threading.Thread
    started: float = field(default_factory=time.monotonic)


class ScraperBridge:
    """Starts, pauses and stops scraper runs and relays their events."""

    def __init__(self, scraper_factory: ScraperFactory) -> None:
        """Creates the bridge.

        Args:
            scraper_factory: ``(mode, progress_callback) -> scraper``. Called once
                per run, so every run gets a fresh single-use scraper.
        """
        self._factory = scraper_factory
        self._events: "queue.Queue[BridgeEvent]" = queue.Queue()
        self._state = RunState.IDLE
        self._run: Optional[_Run] = None

    @property
    def state(self) -> RunState:
        """Current run state (updated on the GUI thread by ``poll()``)."""
        return self._state

    @property
    def elapsed(self) -> float:
        """Seconds since the current run started (0 when idle)."""
        return time.monotonic() - self._run.started if self._run else 0.0

    def start(self, usernames: list[str], mode: str) -> None:
        """Launches a run on a background thread.

        Raises:
            RuntimeError: If a run is already active.
            ValueError: If ``usernames`` is empty.
        """
        if self._state is not RunState.IDLE:
            raise RuntimeError("A run is already in progress")
        if not usernames:
            raise ValueError("No usernames to check")

        scraper = self._factory(mode, self._on_progress)
        thread = threading.Thread(target=self._worker, args=(scraper, list(usernames)),
                                  name="scraper-run", daemon=True)
        self._run = _Run(scraper=scraper, thread=thread)
        self._state = RunState.RUNNING
        thread.start()

    def pause(self) -> None:
        """Pauses a running scrape before each worker's next account."""
        if self._state is RunState.RUNNING and self._run:
            self._run.scraper.pause()
            self._state = RunState.PAUSED

    def resume(self) -> None:
        """Resumes a paused scrape."""
        if self._state is RunState.PAUSED and self._run:
            self._run.scraper.resume()
            self._state = RunState.RUNNING

    def stop(self) -> None:
        """Asks the scraper to stop; a ``FinishedEvent`` follows shortly."""
        if self._state in (RunState.RUNNING, RunState.PAUSED) and self._run:
            self._run.scraper.stop("Stopped by user")
            self._state = RunState.STOPPING

    def poll(self, max_events: int = 500) -> list[BridgeEvent]:
        """Drains pending events. Call from the GUI thread only.

        Returns:
            Events in arrival order; the state returns to ``IDLE`` once a
            ``FinishedEvent`` or ``ErrorEvent`` has been delivered.
        """
        events: list[BridgeEvent] = []
        while len(events) < max_events:
            try:
                event = self._events.get_nowait()
            except queue.Empty:
                break
            events.append(event)
            if isinstance(event, (FinishedEvent, ErrorEvent)):
                self._state = RunState.IDLE
                self._run = None
        return events

    def join(self, timeout: Optional[float] = None) -> None:
        """Waits for the background thread (used by tests and on app close)."""
        if self._run:
            self._run.thread.join(timeout)

    def _on_progress(self, done: int, total: int, record: dict) -> None:
        """Scraper callback; runs on the scraper thread, so it only enqueues."""
        self._events.put(ProgressEvent(done, total, record))

    def _worker(self, scraper: ScraperLike, usernames: list[str]) -> None:
        """Background thread body."""
        started = time.monotonic()
        try:
            records = scraper.run(usernames)
        except Exception as exc:  # noqa: BLE001 - thread boundary: must report, not die silently
            logger.exception("Scraper run failed")
            self._events.put(ErrorEvent(_friendly_error(exc)))
            return
        self._events.put(FinishedEvent(records, scraper.stop_reason, time.monotonic() - started))


def _friendly_error(exc: Exception) -> str:
    """Turns common setup failures into an actionable message."""
    text = str(exc)
    if "Executable doesn't exist" in text:
        return "Chromium is not installed. Run: python -m playwright install chromium"
    if "ProcessSingleton" in text or "user data directory is already in use" in text:
        return "The browser profile is in use. Close the setup/login browser window and try again."
    return f"Run failed: {text.splitlines()[0] if text else type(exc).__name__}"
