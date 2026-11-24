import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from .config import settings

SCHEMA = """
CREATE TABLE IF NOT EXISTS demands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source TEXT NOT NULL DEFAULT 'manual',
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    url TEXT,
    budget TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(source, url)
);

CREATE TABLE IF NOT EXISTS scores (
    demand_id INTEGER PRIMARY KEY REFERENCES demands(id) ON DELETE CASCADE,
    score INTEGER NOT NULL,
    reason TEXT,
    risk TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    demand_id INTEGER NOT NULL REFERENCES demands(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def add_demand(source: str, title: str, description: str, url: str | None = None,
               budget: str | None = None) -> int | None:
    """插入需求，重复的 (source, url) 返回 None。"""
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT OR IGNORE INTO demands (source, title, description, url, budget) "
            "VALUES (?, ?, ?, ?, ?)",
            (source, title, description, url, budget),
        )
        return cur.lastrowid if cur.rowcount else None


def list_demands_with_scores(limit: int = 200) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT d.id, d.source, d.title, d.description, d.url, d.budget, d.created_at,
                   s.score, s.reason, s.risk,
                   (SELECT COUNT(*) FROM proposals p WHERE p.demand_id = d.id) AS proposal_count
            FROM demands d
            LEFT JOIN scores s ON s.demand_id = d.id
            ORDER BY COALESCE(s.score, -1) DESC, d.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_demand(demand_id: int) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            """
            SELECT d.*, s.score, s.reason, s.risk
            FROM demands d
            LEFT JOIN scores s ON s.demand_id = d.id
            WHERE d.id = ?
            """,
            (demand_id,),
        ).fetchone()
    return dict(row) if row else None


def upsert_score(demand_id: int, score: int, reason: str, risk: str) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO scores (demand_id, score, reason, risk, updated_at)
            VALUES (?, ?, ?, ?, datetime('now'))
            ON CONFLICT(demand_id) DO UPDATE SET
                score = excluded.score,
                reason = excluded.reason,
                risk = excluded.risk,
                updated_at = datetime('now')
            """,
            (demand_id, score, reason, risk),
        )


def add_proposal(demand_id: int, content: str) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO proposals (demand_id, content) VALUES (?, ?)", (demand_id, content)
        )
        return cur.lastrowid


def get_proposals(demand_id: int) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM proposals WHERE demand_id = ? ORDER BY id DESC", (demand_id,)
        ).fetchall()
    return [dict(r) for r in rows]


def update_proposal_status(proposal_id: int, status: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE proposals SET status = ? WHERE id = ?", (status, proposal_id))
