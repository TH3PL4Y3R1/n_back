from __future__ import annotations

"""SQLite persistence layer for the N-back task.

Schema
------
  sessions  — one row per task run (mirrors the old .meta.json sidecar)
  trials    — one row per trial   (mirrors the old per-session CSV columns)

ON DELETE CASCADE on trials.session_id means aborting the task only needs to
delete the session row; all its trials are removed automatically.
"""

import json
import sqlite3
from typing import Dict, List

DB_FILENAME = "nback.db"

# ---------------------------------------------------------------------------
# DDL
# ---------------------------------------------------------------------------

_CREATE_SESSIONS = """
CREATE TABLE IF NOT EXISTS sessions (
    session_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    participant_id        TEXT    NOT NULL,
    session_ts            TEXT    NOT NULL,
    n_back                INTEGER,
    blocks                INTEGER,
    trials_per_block      INTEGER,
    practice_trials       INTEGER,
    practice_target_rate  REAL,
    practice_has_lures    INTEGER,
    target_rate           REAL,
    lure_nminus1_rate     REAL,
    lure_nplus1_rate      REAL,
    max_consec_targets    INTEGER,
    seed                  INTEGER,
    letters               TEXT,
    psychopy_version      TEXT,
    display_refresh_hz    REAL,
    window_fullscreen     INTEGER,
    screen_index          INTEGER,
    soa_ms                INTEGER,
    fixed_iti_ms          INTEGER,
    kb_backend            TEXT,
    created_at            TEXT    DEFAULT (datetime('now'))
);
"""

_CREATE_TRIALS = """
CREATE TABLE IF NOT EXISTS trials (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id        INTEGER NOT NULL
                          REFERENCES sessions(session_id) ON DELETE CASCADE,
    participant_id    TEXT,
    session_ts        TEXT,
    block_idx         INTEGER,
    trial_idx         INTEGER,
    n_back            INTEGER,
    stimulus          TEXT,
    is_target         INTEGER,
    lure_type         TEXT,
    iti_ms            INTEGER,
    stim_onset_time   REAL,
    response_key      TEXT,
    rt_ms             REAL,
    correct           INTEGER,
    marker_code_stim  INTEGER,
    marker_code_resp  INTEGER
);
"""

_CREATE_TRIALS_INDEX = """
CREATE INDEX IF NOT EXISTS idx_trials_session ON trials(session_id);
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_db(path: str) -> sqlite3.Connection:
    """Open (or create) the SQLite database and ensure schema is up to date.

    - WAL journal mode: crash-safe and better concurrent read performance.
    - Foreign-key enforcement enabled so ON DELETE CASCADE works.
    """
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.executescript(_CREATE_SESSIONS + _CREATE_TRIALS + _CREATE_TRIALS_INDEX)
    conn.commit()
    return conn


def insert_session(conn: sqlite3.Connection, meta: Dict) -> int:
    """Insert a session row from a metadata dict.

    Accepts the same dict produced by main() for the old .meta.json sidecar.
    Returns the new session_id (autoincrement integer).
    """
    letters_json = json.dumps(meta.get("letters", []))
    cur = conn.execute(
        """
        INSERT INTO sessions (
            participant_id, session_ts, n_back, blocks, trials_per_block,
            practice_trials, practice_target_rate, practice_has_lures,
            target_rate, lure_nminus1_rate, lure_nplus1_rate,
            max_consec_targets, seed, letters, psychopy_version,
            display_refresh_hz, window_fullscreen, screen_index,
            soa_ms, fixed_iti_ms, kb_backend
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        (
            meta.get("participant_id"),
            meta.get("session_timestamp"),
            meta.get("n_back"),
            meta.get("blocks"),
            meta.get("trials_per_block"),
            meta.get("practice_trials"),
            meta.get("practice_target_rate"),
            int(bool(meta.get("practice_has_lures"))),
            meta.get("target_rate"),
            meta.get("lure_nminus1_rate"),
            meta.get("lure_nplus1_rate"),
            meta.get("max_consec_targets"),
            meta.get("seed"),
            letters_json,
            meta.get("psychopy_version"),
            meta.get("display_refresh_hz"),
            int(bool(meta.get("window_fullscreen"))),
            meta.get("screen_index"),
            meta.get("soa_ms"),
            meta.get("fixed_iti_ms"),
            meta.get("kb_backend"),
        ),
    )
    conn.commit()
    return cur.lastrowid  # type: ignore[return-value]


def insert_trials(conn: sqlite3.Connection, session_id: int, rows: List[Dict]) -> None:
    """Bulk-insert trial rows for a completed block.

    Each dict in *rows* matches the trial fieldnames used in run_block().
    The caller is responsible for calling conn.commit() after this function
    (allows batching multiple operations before committing).
    """
    if not rows:
        return

    def _float_or_none(v: object) -> object:
        try:
            return float(v)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None

    def _int_or_none(v: object) -> object:
        try:
            return int(v)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            return None

    conn.executemany(
        """
        INSERT INTO trials (
            session_id, participant_id, session_ts,
            block_idx, trial_idx, n_back, stimulus, is_target, lure_type,
            iti_ms, stim_onset_time, response_key, rt_ms, correct,
            marker_code_stim, marker_code_resp
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        [
            (
                session_id,
                r.get("participant_id"),
                r.get("session_timestamp"),
                r.get("block_idx"),
                r.get("trial_idx"),
                r.get("n_back"),
                r.get("stimulus"),
                r.get("is_target"),
                r.get("lure_type"),
                r.get("iti_ms"),
                _float_or_none(r.get("stim_onset_time") or None),
                r.get("response_key") or None,
                _float_or_none(r.get("rt_ms") or None),
                r.get("correct"),
                _int_or_none(r.get("marker_code_stim") or None),
                _int_or_none(r.get("marker_code_resp") or None),
            )
            for r in rows
        ],
    )


def delete_session(conn: sqlite3.Connection, session_id: int) -> None:
    """Delete a session and all its trials (via ON DELETE CASCADE).

    Used when the participant aborts mid-task with ESC.
    The caller must call conn.commit() after this to make it durable.
    """
    if not session_id:
        return
    conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
