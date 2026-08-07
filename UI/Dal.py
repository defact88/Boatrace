# -*- coding: utf-8 -*-
# DAL (Data Access Layer) for BoatRaceDB  ── 高速化改修版
# 変更点:
#   1. fetch_one / fetch_all が共有コネクションを使い、毎回open/closeしない
#   2. 初回接続時に読み取り性能向上のPRAGMAを設定
#   3. 書き込み系(transaction)は従来通り独立コネクション＋バックアップ
#   4. 既存のAPIシグネチャは一切変えていない（呼び出し側の修正不要）

from __future__ import annotations
import os, re, sqlite3
from contextlib import contextmanager
from datetime   import datetime
from pathlib    import Path
from typing     import Iterable, Iterator, Optional, Sequence, Any

DB_PATH    = r"C:\boatrace\boatrace.db"
BACKUP_DIR = Path(r"C:\boatrace\BACKUP\DB\DAL")

WRITE_HEAD = re.compile(
    r"^(?:INSERT|UPDATE|DELETE|REPLACE|CREATE|ALTER|DROP|VACUUM|ATTACH)\b", re.I
)

# ------------------------------------------------------------------ #
#  共有読み取りコネクション（プロセス起動時に一度だけ接続）
# ------------------------------------------------------------------ #
_shared_conn: Optional[sqlite3.Connection] = None

def _get_shared_conn() -> sqlite3.Connection:
    """
    読み取り専用のシングルトン接続を返す。
    初回呼び出し時のみ sqlite3.connect() し、以後は使い回す。
    書き込みには使わない（transaction() が別接続を開く）。
    """
    global _shared_conn
    if _shared_conn is None:
        _shared_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _shared_conn.row_factory = sqlite3.Row
        # --- 読み取り性能チューニング ---
        _shared_conn.execute("PRAGMA foreign_keys  = ON")
        _shared_conn.execute("PRAGMA journal_mode  = WAL")      # 書き込みと読み取りが競合しない
        _shared_conn.execute("PRAGMA synchronous   = NORMAL")   # WALなら安全に落とせる
        _shared_conn.execute("PRAGMA cache_size    = -32000")   # 32 MB ページキャッシュ
        _shared_conn.execute("PRAGMA temp_store    = MEMORY")   # 中間テーブルをメモリに
        _shared_conn.execute("PRAGMA mmap_size     = 268435456")# 256 MB メモリマップ読み
    return _shared_conn

def close_shared():
    """アプリ終了時に明示的に呼ぶ（必須ではないが後片付け用）"""
    global _shared_conn
    if _shared_conn is not None:
        _shared_conn.close()
        _shared_conn = None

# ------------------------------------------------------------------ #
#  書き込み用コネクション（従来通り毎回open/close）
# ------------------------------------------------------------------ #
def _connect(db_path: str = DB_PATH) -> sqlite3.Connection:
    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    return c

@contextmanager
def connection(db_path: str = DB_PATH) -> Iterator[sqlite3.Connection]:
    c = _connect(db_path)
    try:
        yield c
    finally:
        c.close()

@contextmanager
def transaction(db_path: str = DB_PATH) -> Iterator[sqlite3.Connection]:
    with connection(db_path) as c:
        c.execute("BEGIN IMMEDIATE;")
        _ensure_backup_dir()
        _auto_backup(db_path)
        try:
            yield c
            c.commit()
        except Exception:
            c.rollback()
            raise

# ------------------------------------------------------------------ #
#  読み取りAPI  ── 共有接続を使う
# ------------------------------------------------------------------ #
def fetch_one(sql: str, params: Sequence[Any] = (), *,
              conn: Optional[sqlite3.Connection] = None):
    """
    conn が渡された場合はそれを使う（書き込みトランザクション内からの呼び出し用）。
    渡されない場合は共有接続を使い、open/closeのオーバーヘッドをゼロにする。
    """
    c = conn if conn is not None else _get_shared_conn()
    return c.execute(sql, params).fetchone()

def fetch_all(sql: str, params: Sequence[Any] = (), *,
              conn: Optional[sqlite3.Connection] = None):
    c = conn if conn is not None else _get_shared_conn()
    return c.execute(sql, params).fetchall()

# ------------------------------------------------------------------ #
#  書き込みAPI  ── 従来通り
# ------------------------------------------------------------------ #
def execute(sql: str, params: Sequence[Any] = (), *,
            conn: Optional[sqlite3.Connection] = None) -> int:
    if conn is not None:
        return conn.execute(sql, params).rowcount
    with transaction() as c:
        return c.execute(sql, params).rowcount

def executemany(sql: str, seq_params: Iterable[Sequence[Any]], *,
                conn: Optional[sqlite3.Connection] = None) -> int:
    if conn is not None:
        return conn.executemany(sql, seq_params).rowcount
    with transaction() as c:
        return c.executemany(sql, seq_params).rowcount

def executescript(script: str, *, conn: Optional[sqlite3.Connection] = None) -> None:
    if conn is not None:
        conn.executescript(script)
        return
    with transaction() as c:
        c.executescript(script)

# ------------------------------------------------------------------ #
#  バックアップ
# ------------------------------------------------------------------ #
def _ensure_backup_dir():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

def _auto_backup(db_path: str):
    src = Path(db_path)
    if not src.exists():
        return
    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = BACKUP_DIR / f"boatrace_{ts}.db"
    with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
        fdst.write(fsrc.read())

# ------------------------------------------------------------------ #
#  convenience API（変更なし）
# ------------------------------------------------------------------ #
def list_tables() -> list[str]:
    rows = fetch_all("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return [r[0] for r in rows]

def list_columns(table: str) -> list[tuple[str, str]]:
    rows = fetch_all(f"PRAGMA table_info({table})")
    return [(r[1], r[2]) for r in rows]

def vacuum(*, conn: Optional[sqlite3.Connection] = None):
    executescript("VACUUM;", conn=conn)

def safe_sql(sql: str, params: Sequence[Any] = ()):
    head = sql.lstrip()[:16].upper()
    if WRITE_HEAD.match(head):
        return execute(sql, params)
    return fetch_all(sql, params)

if __name__ == "__main__":
    print("DB:", DB_PATH)
    print("tables:", ", ".join(list_tables()))
