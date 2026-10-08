import os, sqlite3

DB_PATH = os.environ.get("GACHA_DB", "data/gacha.db")

def init_db():
    """建表 + 开 WAL。启动时调用一次。"""
    os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")   # 压测并发写不加这个会疯狂 locked
    conn.execute("""CREATE TABLE IF NOT EXISTS pulls(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        uid TEXT NOT NULL,
        pool_id TEXT NOT NULL,
        rarity TEXT NOT NULL,
        pity_at_pull INTEGER,
        created_at TEXT DEFAULT (datetime('now','localtime')))""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_uid ON pulls(uid)")
    conn.commit(); conn.close()

def get_db():
    """FastAPI 依赖：每请求一个连接，用完即关。"""
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()