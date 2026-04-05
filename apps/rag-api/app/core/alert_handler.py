"""
Smart alerting with rule-based analysis engine.

Not every ERROR deserves an email. This module classifies errors into four
categories and handles each differently:

  alert     — Critical: send email immediately (e.g. auth failure, service down)
  burst     — Important: only alert when the same error repeats N times within
              a time window, indicating a persistent issue rather than a blip
  suppress  — Known non-critical: silently ignore (e.g. warmup, expected 404s)
  digest    — Default: accumulate and send a periodic summary email

Rules are evaluated top-to-bottom; the first match wins.  Unmatched errors
fall through to the "digest" bucket.
"""

from __future__ import annotations

import hashlib
import logging
import re
import smtplib
import socket
import threading
import time
import traceback
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape
from typing import Literal

from app.core.config import (
    ALERT_APP_NAME,
    ALERT_CONTEXT_LINES,
    ALERT_COOLDOWN_SECONDS,
    ALERT_DIGEST_INTERVAL,
    ALERT_FROM_EMAIL,
    ALERT_SMTP_HOST,
    ALERT_SMTP_PASSWORD,
    ALERT_SMTP_PORT,
    ALERT_SMTP_USE_TLS,
    ALERT_SMTP_USER,
    ALERT_TO_EMAILS,
)

_internal_logger = logging.getLogger("alert_handler")

# ── Rule definitions ─────────────────────────────────────────────────────

Action = Literal["alert", "burst", "suppress", "digest"]


@dataclass
class AlertRule:
    """A single classification rule.

    Fields:
        name:            Human-readable label shown in emails / logs.
        pattern:         Regex matched against "{logger_name}: {message}".
        action:          What to do when matched.
        burst_threshold: (burst only) How many occurrences within burst_window
                         before firing an alert.
        burst_window:    (burst only) Sliding window in seconds.
    """
    name: str
    pattern: str
    action: Action = "digest"
    burst_threshold: int = 3
    burst_window: int = 300
    _compiled: re.Pattern | None = field(default=None, repr=False, init=False)

    def matches(self, text: str) -> bool:
        if self._compiled is None:
            self._compiled = re.compile(self.pattern, re.IGNORECASE)
        return self._compiled.search(text) is not None


# ── Default rules (evaluated top-to-bottom, first match wins) ────────────

DEFAULT_RULES: list[AlertRule] = [
    # ─── alert: always send immediately ──────────────────────────────
    AlertRule(
        name="auth_failure",
        pattern=r"(invalid.*api.?key|authentication|unauthorized|403|401)",
        action="alert",
    ),
    AlertRule(
        name="service_unreachable",
        pattern=r"(connection\s*refused|dns.*fail|service.unavailable|503|502)",
        action="alert",
    ),
    AlertRule(
        name="agent_crash",
        pattern=r"Error while generating streamed response",
        action="alert",
    ),
    AlertRule(
        name="out_of_memory",
        pattern=r"(MemoryError|out of memory|OOM|Cannot allocate)",
        action="alert",
    ),

    # ─── burst: only alert on repeated failures ──────────────────────
    AlertRule(
        name="search_persistent_failure",
        pattern=r"Vector Store Search failed after retries",
        action="burst",
        burst_threshold=3,
        burst_window=300,
    ),
    AlertRule(
        name="session_persistent_failure",
        pattern=r"Failed to create ChatKit session",
        action="burst",
        burst_threshold=3,
        burst_window=300,
    ),
    AlertRule(
        name="openai_rate_limit",
        pattern=r"(rate.?limit|429|too many requests)",
        action="burst",
        burst_threshold=5,
        burst_window=60,
    ),
    AlertRule(
        name="timeout_errors",
        pattern=r"(timed?\s*out|timeout|deadline exceeded)",
        action="burst",
        burst_threshold=5,
        burst_window=120,
    ),

    # ─── suppress: never alert ───────────────────────────────────────
    AlertRule(
        name="warmup_failure",
        pattern=r"Startup warmup failed",
        action="suppress",
    ),
    AlertRule(
        name="thread_not_found",
        pattern=r"(Thread|Item).*not found",
        action="suppress",
    ),
    AlertRule(
        name="alert_self_failure",
        pattern=r"Failed to send alert email",
        action="suppress",
    ),
    AlertRule(
        name="attachment_not_impl",
        pattern=r"NotImplementedError",
        action="suppress",
    ),
]


# ── Helpers ──────────────────────────────────────────────────────────────


def _fingerprint(record: logging.LogRecord) -> str:
    parts = [record.name, record.getMessage()[:256]]
    if record.exc_info and record.exc_info[0]:
        parts.append(record.exc_info[0].__name__)
    raw = "|".join(parts)
    return hashlib.md5(raw.encode(), usedforsecurity=False).hexdigest()[:12]


def _match_text(record: logging.LogRecord) -> str:
    """Build the string that rules are matched against."""
    text = f"{record.name}: {record.getMessage()}"
    if record.exc_info and record.exc_info[0]:
        text += f" [{record.exc_info[0].__name__}]"
    return text


# ── Email building ───────────────────────────────────────────────────────

_LEVEL_COLORS = {
    "CRITICAL": "#d32f2f",
    "ERROR": "#e53935",
    "WARNING": "#ff9800",
}

_ACTION_LABELS = {
    "alert": "CRITICAL",
    "burst": "PERSISTENT",
    "digest": "DIGEST",
}


def _build_single_email(
    record: logging.LogRecord,
    context_lines: list[str],
    rule: AlertRule | None,
    burst_info: str = "",
) -> MIMEMultipart:
    level = record.levelname
    color = _LEVEL_COLORS.get(level, "#333")
    ts = datetime.fromtimestamp(record.created, tz=timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )
    hostname = socket.gethostname()
    rule_name = rule.name if rule else "unclassified"
    action_label = _ACTION_LABELS.get(rule.action if rule else "digest", "DIGEST")

    tb_html = ""
    if record.exc_info and record.exc_info[1]:
        tb_text = "".join(traceback.format_exception(*record.exc_info))
        tb_html = f"""
        <h3 style="color:#333;margin:18px 0 8px">Stack Trace</h3>
        <pre style="background:#1e1e1e;color:#d4d4d4;padding:14px;border-radius:6px;
                    font-size:13px;overflow-x:auto;line-height:1.5">{escape(tb_text)}</pre>
        """

    ctx_html = ""
    if context_lines:
        ctx_text = "\n".join(context_lines[-ALERT_CONTEXT_LINES:])
        ctx_html = f"""
        <h3 style="color:#333;margin:18px 0 8px">Recent Log Context ({len(context_lines)} lines)</h3>
        <pre style="background:#f5f5f5;color:#333;padding:14px;border-radius:6px;
                    font-size:12px;overflow-x:auto;line-height:1.4;max-height:600px;
                    overflow-y:auto">{escape(ctx_text)}</pre>
        """

    burst_html = ""
    if burst_info:
        burst_html = (
            f'<p style="background:#ff9800;color:#fff;padding:8px 14px;border-radius:6px;'
            f'font-size:13px">{escape(burst_info)}</p>'
        )

    html = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
                max-width:800px;margin:0 auto;padding:20px">
        <div style="background:{color};color:#fff;padding:16px 20px;border-radius:8px 8px 0 0">
            <h2 style="margin:0;font-size:18px">
                [{action_label}] {ALERT_APP_NAME}
                <span style="background:rgba(255,255,255,0.2);padding:2px 8px;
                             border-radius:10px;font-size:12px;margin-left:8px">
                    {escape(rule_name)}
                </span>
            </h2>
            <p style="margin:6px 0 0;opacity:0.9;font-size:13px">
                {ts} · {hostname} · {escape(record.name)}
            </p>
        </div>
        <div style="border:1px solid #e0e0e0;border-top:none;padding:20px;
                    border-radius:0 0 8px 8px;background:#fff">
            {burst_html}
            <h3 style="color:#333;margin:0 0 8px">Error Message</h3>
            <pre style="background:#fff3e0;color:#e65100;padding:14px;border-radius:6px;
                        font-size:14px;white-space:pre-wrap;word-break:break-word;
                        line-height:1.5">{escape(record.getMessage())}</pre>
            {tb_html}
            {ctx_html}
            <hr style="border:none;border-top:1px solid #eee;margin:20px 0">
            <p style="color:#999;font-size:11px;margin:0">
                Logger: {escape(record.name)} ·
                File: {escape(record.pathname)}:{record.lineno} ·
                Function: {escape(record.funcName or '')}
            </p>
        </div>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[{action_label}] {ALERT_APP_NAME} — {record.getMessage()[:100]}"
    msg["From"] = ALERT_FROM_EMAIL
    msg["To"] = ", ".join(ALERT_TO_EMAILS)

    plain = (
        f"[{action_label}] {ALERT_APP_NAME}  (rule: {rule_name})\n"
        f"Time: {ts}\nHost: {hostname}\nLogger: {record.name}\n\n"
        f"Message:\n{record.getMessage()}\n"
    )
    if burst_info:
        plain += f"\n{burst_info}\n"
    if record.exc_info and record.exc_info[1]:
        plain += f"\nTraceback:\n{''.join(traceback.format_exception(*record.exc_info))}\n"
    if context_lines:
        plain += "\nRecent Log Context:\n" + "\n".join(context_lines[-ALERT_CONTEXT_LINES:])

    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    return msg


@dataclass
class _DigestEntry:
    rule_name: str
    message: str
    logger_name: str
    count: int = 1
    first_seen: float = 0.0
    last_seen: float = 0.0


def _build_digest_email(entries: list[_DigestEntry]) -> MIMEMultipart:
    ts = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    hostname = socket.gethostname()
    total = sum(e.count for e in entries)

    rows_html = ""
    for e in sorted(entries, key=lambda x: -x.count):
        first = datetime.fromtimestamp(e.first_seen, tz=timezone.utc).strftime("%H:%M:%S")
        last = datetime.fromtimestamp(e.last_seen, tz=timezone.utc).strftime("%H:%M:%S")
        rows_html += f"""
        <tr>
            <td style="padding:8px;border-bottom:1px solid #eee;font-size:12px;
                       font-family:monospace;color:#6a1b9a">{escape(e.rule_name)}</td>
            <td style="padding:8px;border-bottom:1px solid #eee;font-size:13px;
                       text-align:center;font-weight:bold">{e.count}</td>
            <td style="padding:8px;border-bottom:1px solid #eee;font-size:12px;
                       color:#666">{first} – {last}</td>
            <td style="padding:8px;border-bottom:1px solid #eee;font-size:12px;
                       max-width:400px;overflow:hidden;text-overflow:ellipsis;
                       white-space:nowrap">{escape(e.message[:120])}</td>
        </tr>
        """

    html = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
                max-width:800px;margin:0 auto;padding:20px">
        <div style="background:#5c6bc0;color:#fff;padding:16px 20px;border-radius:8px 8px 0 0">
            <h2 style="margin:0;font-size:18px">
                [DIGEST] {ALERT_APP_NAME} — {total} errors in the last period
            </h2>
            <p style="margin:6px 0 0;opacity:0.9;font-size:13px">{ts} · {hostname}</p>
        </div>
        <div style="border:1px solid #e0e0e0;border-top:none;padding:20px;
                    border-radius:0 0 8px 8px;background:#fff">
            <p style="color:#666;font-size:13px;margin:0 0 12px">
                These errors were below the immediate-alert threshold.
                Review and investigate if any pattern is concerning.
            </p>
            <table style="width:100%;border-collapse:collapse">
                <thead>
                    <tr style="background:#f5f5f5">
                        <th style="padding:8px;text-align:left;font-size:12px">Rule</th>
                        <th style="padding:8px;text-align:center;font-size:12px">Count</th>
                        <th style="padding:8px;text-align:left;font-size:12px">Time Range</th>
                        <th style="padding:8px;text-align:left;font-size:12px">Sample Message</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        </div>
    </div>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = (
        f"[DIGEST] {ALERT_APP_NAME} — {total} errors "
        f"({len(entries)} types) in the last period"
    )
    msg["From"] = ALERT_FROM_EMAIL
    msg["To"] = ", ".join(ALERT_TO_EMAILS)

    plain_rows = "\n".join(
        f"  [{e.rule_name}] ×{e.count}  {e.message[:100]}"
        for e in sorted(entries, key=lambda x: -x.count)
    )
    plain = (
        f"[DIGEST] {ALERT_APP_NAME}\n"
        f"Time: {ts}\nHost: {hostname}\n"
        f"Total errors: {total} ({len(entries)} types)\n\n{plain_rows}\n"
    )
    msg.attach(MIMEText(plain, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))
    return msg


# ── Background email sender ─────────────────────────────────────────────


def _send_email_sync(mime_msg: MIMEMultipart) -> None:
    try:
        if ALERT_SMTP_USE_TLS:
            server = smtplib.SMTP(ALERT_SMTP_HOST, ALERT_SMTP_PORT, timeout=30)
            server.starttls()
        else:
            server = smtplib.SMTP(ALERT_SMTP_HOST, ALERT_SMTP_PORT, timeout=30)

        if ALERT_SMTP_USER and ALERT_SMTP_PASSWORD:
            server.login(ALERT_SMTP_USER, ALERT_SMTP_PASSWORD)

        server.sendmail(ALERT_FROM_EMAIL, ALERT_TO_EMAILS, mime_msg.as_string())
        server.quit()
    except Exception:
        _internal_logger.warning("Failed to send alert email", exc_info=True)


def _send_in_background(mime_msg: MIMEMultipart) -> None:
    threading.Thread(target=_send_email_sync, args=(mime_msg,), daemon=True).start()


# ── Smart Alert Handler ──────────────────────────────────────────────────


class SmartAlertHandler(logging.Handler):
    """Logging handler with rule-based analysis.

    Processing pipeline for every log record:

    1. Buffer the formatted line (all levels) for context.
    2. If level < configured alert level → stop.
    3. Match against rules top-to-bottom.
    4. Depending on matched action:
       - alert:    check cooldown → send immediately
       - burst:    track in sliding window → send when threshold crossed
       - suppress: discard silently
       - digest:   accumulate for periodic summary
       (no match → treated as "digest")
    5. Periodic timer flushes the digest bucket via email.
    """

    def __init__(
        self,
        level: int = logging.ERROR,
        rules: list[AlertRule] | None = None,
    ) -> None:
        super().__init__(level)
        self._rules = rules if rules is not None else list(DEFAULT_RULES)
        self._context_buffer: deque[str] = deque(maxlen=ALERT_CONTEXT_LINES)

        # alert cooldown: fingerprint → last-sent monotonic time
        self._cooldown_map: dict[str, float] = {}

        # burst tracking: fingerprint → list of monotonic timestamps
        self._burst_windows: dict[str, deque[float]] = {}

        # digest accumulator: fingerprint → DigestEntry
        self._digest_bucket: dict[str, _DigestEntry] = {}

        self._lock = threading.Lock()
        self._formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

        self._digest_timer: threading.Timer | None = None
        self._start_digest_timer()

    # ── Rule matching ────────────────────────────────────────────────

    def _classify(self, record: logging.LogRecord) -> tuple[AlertRule | None, Action]:
        text = _match_text(record)
        for rule in self._rules:
            if rule.matches(text):
                return rule, rule.action
        return None, "digest"

    # ── Core emit ────────────────────────────────────────────────────

    def emit(self, record: logging.LogRecord) -> None:
        try:
            formatted = self._formatter.format(record)

            with self._lock:
                self._context_buffer.append(formatted)

            if record.levelno < self.level:
                return

            rule, action = self._classify(record)

            if action == "suppress":
                return

            if action == "alert":
                self._handle_alert(record, rule)
            elif action == "burst":
                self._handle_burst(record, rule)
            else:
                self._handle_digest(record, rule)

        except Exception:
            self.handleError(record)

    # ── Action: alert (immediate, with cooldown) ─────────────────────

    def _handle_alert(
        self, record: logging.LogRecord, rule: AlertRule | None,
    ) -> None:
        fp = _fingerprint(record)
        now = time.monotonic()

        with self._lock:
            last_sent = self._cooldown_map.get(fp, 0)
            if now - last_sent < ALERT_COOLDOWN_SECONDS:
                return
            self._cooldown_map[fp] = now
            context_snapshot = list(self._context_buffer)
            self._cleanup_cooldown(now)

        email = _build_single_email(record, context_snapshot, rule)
        _send_in_background(email)

    # ── Action: burst (sliding window threshold) ─────────────────────

    def _handle_burst(
        self, record: logging.LogRecord, rule: AlertRule | None,
    ) -> None:
        fp = _fingerprint(record)
        now = time.monotonic()
        threshold = rule.burst_threshold if rule else 3
        window = rule.burst_window if rule else 300

        with self._lock:
            if fp not in self._burst_windows:
                self._burst_windows[fp] = deque()
            timestamps = self._burst_windows[fp]
            timestamps.append(now)

            # Trim timestamps outside the window
            cutoff = now - window
            while timestamps and timestamps[0] < cutoff:
                timestamps.popleft()

            count = len(timestamps)

            if count < threshold:
                return

            # Threshold crossed — check cooldown before sending
            last_sent = self._cooldown_map.get(fp, 0)
            if now - last_sent < ALERT_COOLDOWN_SECONDS:
                return
            self._cooldown_map[fp] = now
            timestamps.clear()
            context_snapshot = list(self._context_buffer)

        burst_info = (
            f"Burst detected: {count} occurrences in the last {window}s "
            f"(threshold: {threshold})"
        )
        email = _build_single_email(record, context_snapshot, rule, burst_info)
        _send_in_background(email)

    # ── Action: digest (accumulate for periodic summary) ─────────────

    def _handle_digest(
        self, record: logging.LogRecord, rule: AlertRule | None,
    ) -> None:
        fp = _fingerprint(record)
        now = record.created

        with self._lock:
            if fp in self._digest_bucket:
                entry = self._digest_bucket[fp]
                entry.count += 1
                entry.last_seen = now
            else:
                self._digest_bucket[fp] = _DigestEntry(
                    rule_name=rule.name if rule else "unclassified",
                    message=record.getMessage(),
                    logger_name=record.name,
                    count=1,
                    first_seen=now,
                    last_seen=now,
                )

    # ── Digest timer ─────────────────────────────────────────────────

    def _start_digest_timer(self) -> None:
        self._digest_timer = threading.Timer(
            ALERT_DIGEST_INTERVAL, self._flush_digest,
        )
        self._digest_timer.daemon = True
        self._digest_timer.start()

    def _flush_digest(self) -> None:
        with self._lock:
            entries = list(self._digest_bucket.values())
            self._digest_bucket.clear()

        if entries:
            email = _build_digest_email(entries)
            _send_in_background(email)

        self._start_digest_timer()

    # ── Cleanup ──────────────────────────────────────────────────────

    def _cleanup_cooldown(self, now: float) -> None:
        expired = [
            fp for fp, ts in self._cooldown_map.items()
            if now - ts > ALERT_COOLDOWN_SECONDS * 2
        ]
        for fp in expired:
            self._cooldown_map.pop(fp, None)

    def close(self) -> None:
        if self._digest_timer:
            self._digest_timer.cancel()
        super().close()
