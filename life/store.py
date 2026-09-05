"""Banco local de eventos da vida (SQLite).

Um evento e qualquer coisa que aconteceu ou vai acontecer e que veio de
alguma fonte conectada: um email, um compromisso, um voo barato, uma
cobranca. Toda fonte nova grava aqui, no mesmo formato.
"""
import json
import os
import sqlite3
from datetime import datetime

from life.config import BRT, DB_PATH, ensure_home

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id           INTEGER PRIMARY KEY,
    source       TEXT NOT NULL,   -- gmail, gcalendar, flights, ...
    external_id  TEXT NOT NULL,   -- id na fonte, garante idempotencia
    ts           TEXT NOT NULL,   -- quando o evento acontece/aconteceu (ISO)
    kind         TEXT NOT NULL,   -- acao | dinheiro | compromisso | info | ruido
    title        TEXT NOT NULL,
    who          TEXT,            -- remetente, organizador
    amount_brl   REAL,
    link         TEXT,
    raw          TEXT,            -- json com o que a fonte devolveu
    collected_at TEXT NOT NULL,
    UNIQUE(source, external_id)
);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
CREATE INDEX IF NOT EXISTS idx_events_kind ON events(kind);
CREATE INDEX IF NOT EXISTS idx_events_collected ON events(collected_at);
"""


def connect():
    ensure_home()
    first_time = not DB_PATH.exists()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    if first_time:
        # O banco tem seu email dentro. Ninguem alem de voce le.
        os.chmod(DB_PATH, 0o600)
    return conn


def now_iso():
    return datetime.now(BRT).isoformat(timespec="seconds")


def save_events(conn, events, collected_at=None):
    """Grava eventos e devolve os que sao novos (nunca vistos antes)."""
    collected_at = collected_at or now_iso()
    novos = []
    for ev in events:
        cur = conn.execute(
            """INSERT OR IGNORE INTO events
               (source, external_id, ts, kind, title, who, amount_brl, link, raw, collected_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                ev["source"],
                str(ev["external_id"]),
                ev["ts"],
                ev.get("kind", "info"),
                ev.get("title", "(sem titulo)"),
                ev.get("who"),
                ev.get("amount_brl"),
                ev.get("link"),
                json.dumps(ev.get("raw", {}), ensure_ascii=False),
                collected_at,
            ),
        )
        if cur.rowcount:
            novos.append(ev)
    conn.commit()
    return novos


def count_by_kind(conn, since_iso):
    rows = conn.execute(
        "SELECT kind, COUNT(*) AS n FROM events WHERE collected_at >= ? GROUP BY kind",
        (since_iso,),
    ).fetchall()
    return {r["kind"]: r["n"] for r in rows}
