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



from fastapi import Query

@app.get("/api/history/{uid}")
def history(uid: str, pool_id: str = "standard",
            skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
            db=Depends(get_db)):
    rows = db.execute(
        """SELECT id, rarity, pity_at_pull, created_at FROM pulls
           WHERE uid=? AND pool_id=? ORDER BY id DESC LIMIT ? OFFSET ?""",
        (uid, pool_id, limit, skip)).fetchall()
    total = db.execute(
        "SELECT COUNT(*) AS c FROM pulls WHERE uid=? AND pool_id=?",
        (uid, pool_id)).fetchone()["c"]
    return {"total": total, "items": [dict(r) for r in rows]}


@app.get("/api/stats/{uid}")
def stats(uid: str, pool_id: str = "standard", db=Depends(get_db)):
    total = db.execute("SELECT COUNT(*) AS c FROM pulls WHERE uid=? AND pool_id=?",
                       (uid, pool_id)).fetchone()["c"]
    six = db.execute("SELECT COUNT(*) AS c FROM pulls WHERE uid=? AND pool_id=? AND rarity='6'",
                     (uid, pool_id)).fetchone()["c"]
    pity = pity_from_history(db, uid, pool_id)
    claimed = POOLS[pool_id]["rates"]["6"]
    return {
        "uid": uid, "pool_id": pool_id, "total": total, "six_star": six,
        "actual_rate": round(six / total, 4) if total else None,
        "claimed_rate": claimed,
        "deviation": round(six / total - claimed, 4) if total else None,
        "pity_now": pity,
    }


import random as _r
import matplotlib
matplotlib.use("Agg")            # 无显示器环境也能画
import matplotlib.pyplot as plt

@app.post("/api/simulate")
def simulate(pool_id: str = "standard",
             n: int = Query(100_000, ge=100, le=1_000_000),
             seed: int | None = None):
    cfg = POOLS[pool_id]
    pool = GachaPool(cfg["rates"], cfg["pity"], rng=_r.Random(seed))
    gaps, gap = [], 0
    for _ in range(n):
        r, _p = pool.pull_many(1, gap)
        if r[0] == "6":
            gaps.append(gap + 1); gap = 0
        else:
            gap += 1
    expected = sum(gaps) / len(gaps)
    # 直方图
    plt.figure(figsize=(8, 4.5))
    plt.hist(gaps, bins=range(0, cfg["pity"] + 2), color="#2437ff", edgecolor="white")
    plt.axvline(expected, color="#ffd802", lw=2, label=f"expected {expected:.1f}")
    plt.xlabel("六星间隔抽数"); plt.legend()
    import os; os.makedirs("reports", exist_ok=True)
    plt.savefig("reports/gap_hist.png", dpi=150, bbox_inches="tight"); plt.close()
    return {
        "n": n, "six_star_count": len(gaps),
        "expected_pulls_per_six": round(expected, 2),
        "max_gap": max(gaps), "claimed_rate": cfg["rates"]["6"],
        "actual_rate": round(len(gaps) / n, 4),
        "chart": "reports/gap_hist.png",
    }

# 前端演示页：静态兜底路由必须挂在所有 API 路由之后
from fastapi.staticfiles import StaticFiles  # noqa: E402
app.mount("/", StaticFiles(directory="static", html=True), name="static")
