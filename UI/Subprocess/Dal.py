# -*- coding: utf-8 -*-
# DAL (Data Access Layer) for BoatRaceDB  ── 高速化改修版

from __future__ import annotations
import os, re, sqlite3
from contextlib import contextmanager
from datetime   import datetime
from pathlib    import Path
from typing     import Iterable, Iterator, Optional, Sequence, Any
#---------------------------------------

DB_PATH    = r"C:\boatrace\boatrace.db"
BACKUP_DIR = Path(r"C:\boatrace\BACKUP\DB\DAL")
WRITE_HEAD = re.compile(
                 r"^(?:INSERT|UPDATE|DELETE|REPLACE|CREATE|ALTER|DROP|VACUUM|ATTACH)\b", re.I )

_shared_conn:Optional[sqlite3.Connection] = None

#---------------------------------------
def _get_shared_conn() -> sqlite3.Connection:

    global _shared_conn
    if _shared_conn is None:
        _shared_conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _shared_conn.row_factory = sqlite3.Row

        _shared_conn.execute("PRAGMA foreign_keys  = ON")
        _shared_conn.execute("PRAGMA journal_mode  = WAL")
        _shared_conn.execute("PRAGMA synchronous   = NORMAL")
        _shared_conn.execute("PRAGMA cache_size    = -32000")
        _shared_conn.execute("PRAGMA temp_store    = MEMORY")
        _shared_conn.execute("PRAGMA mmap_size     = 268435456")

    return _shared_conn
#---------------------------------------
def close_shared():

    global _shared_conn
    if _shared_conn is not None:
        _shared_conn.close()
        _shared_conn = None
#---------------------------------------
def _connect(db_path:str = DB_PATH) -> sqlite3.Connection:

    c             = sqlite3.connect(db_path, timeout=30.0)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")

    return c
#---------------------------------------
@contextmanager
def connection(db_path:str= DB_PATH) -> Iterator[sqlite3.Connection]:

    c = _connect(db_path)
    try:
        yield c
    finally:
        c.close()
#---------------------------------------
@contextmanager
def transaction(db_path:str = DB_PATH) -> Iterator[sqlite3.Connection]:

    with connection(db_path) as c:
        c.execute("BEGIN IMMEDIATE;")
        #_auto_backup(db_path)
        try:
            yield c
            c.commit()
        except Exception:
            c.rollback()
            raise
#---------------------------------------
def fetch_one(sql:str, params:Sequence[Any] = (), *, conn:Optional[sqlite3.Connection]=None):

    c = conn if conn is not None else _get_shared_conn()

    return c.execute(sql, params).fetchone()
#---------------------------------------
def fetch_all(sql:str, params:Sequence[Any] = (), *, conn:Optional[sqlite3.Connection]=None):

    c = conn if conn is not None else _get_shared_conn()

    return c.execute(sql, params).fetchall()
#---------------------------------------
def execute(sql:str, params:Sequence[Any] = (), *, conn:Optional[sqlite3.Connection]=None):

    if conn is not None:
        return conn.execute(sql, params).rowcount
    with transaction() as c:
        return c.execute(sql, params).rowcount
#---------------------------------------
def executemany(sql:str, seq_params:Iterable[Sequence[Any]], *, conn:Optional[sqlite3.Connection]=None):

    if conn is not None:
        return conn.executemany(sql, seq_params).rowcount
    with transaction() as c:
        return c.executemany(sql, seq_params).rowcount
#---------------------------------------
def executescript(script:str, *, conn:Optional[sqlite3.Connection]=None) -> None:

    if conn is not None:
        conn.executescript(script)
        return
    with transaction() as c:
        c.executescript(script)

#---------------------------------------
def _auto_backup(db_path: str):

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    src = Path(db_path)
    if not src.exists():
        return
    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    dst = BACKUP_DIR / f"boatrace_{ts}.db"
    with open(src, "rb") as fsrc, open(dst, "wb") as fdst:
        fdst.write(fsrc.read())

#---------------------------------------
def list_tables() -> list[str]:

    rows = fetch_all( """
                      SELECT name
                        FROM sqlite_master
                       WHERE type='table'
                    ORDER BY name
                       """)

    return [r[0] for r in rows]
#---------------------------------------
def list_columns(table:str) -> list[tuple[str, str]]:

    rows = fetch_all(f"PRAGMA table_info({table})")

    return [(r[1], r[2]) for r in rows]
#---------------------------------------
def vacuum(*, conn: Optional[sqlite3.Connection] = None):

    executescript("VACUUM;", conn=conn)
#---------------------------------------
def safe_sql(sql:str, params:Sequence[Any] = ()):

    head = sql.lstrip()[:16].upper()
    if WRITE_HEAD.match(head):
        return execute(sql, params)
    return fetch_all(sql, params)
#---------------------------------------
if __name__ == "__main__":
    print("DB:", DB_PATH)
    print("tables:", ", ".join(list_tables()))
