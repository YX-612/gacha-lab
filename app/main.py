from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import init_db
from app.pools import POOLS

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()          # 启动时建表（测试换 GACHA_DB 后再启动，就建到临时库）
    yield

app = FastAPI(
    title="gacha-lab API",
    version="1.0.0",
    description="抽卡系统测试实验室：自建带保底的抽卡引擎，转身当它的测试。",
    lifespan=lifespan,
)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/api/pools")
def list_pools():
    return list(POOLS.values())


from fastapi import Depends, HTTPException
from app.database import get_db
from app.schemas import PullRequest, PullResult
from app.engine import GachaPool

def pity_from_history(db, uid: str, pool_id: str) -> int:
    """距上次六星的抽数 = 当前保底进度（从流水推导，随时可审计）"""
    row = db.execute(
        """SELECT COUNT(*) AS c FROM pulls WHERE uid=? AND pool_id=? AND id >
           (SELECT COALESCE(MAX(id), 0) FROM pulls
            WHERE uid=? AND pool_id=? AND rarity='6')""",
        (uid, pool_id, uid, pool_id)).fetchone()
    return row["c"]

@app.post("/api/pull", response_model=PullResult)
def pull(req: PullRequest, db=Depends(get_db)):
    cfg = POOLS.get(req.pool_id)
    if cfg is None:
        raise HTTPException(status_code=404, detail=f"卡池不存在: {req.pool_id}")
    pity_start = pity_from_history(db, req.uid, req.pool_id)
    results, pity_end = GachaPool(cfg["rates"], cfg["pity"]).pull_many(req.count, pity_start)
    db.executemany(
        "INSERT INTO pulls(uid, pool_id, rarity, pity_at_pull) VALUES (?,?,?,?)",
        [(req.uid, req.pool_id, r, pity_start + i) for i, r in enumerate(results)])
    db.commit()
    return PullResult(uid=req.uid, pool_id=req.pool_id, results=results, pity_now=pity_end)
