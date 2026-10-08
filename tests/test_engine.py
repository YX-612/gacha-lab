import random
from app.engine import GachaPool

RATES = {"6": 0.02, "5": 0.10, "4": 0.88}

def make(seed=42):
    return GachaPool(RATES, pity=60, rng=random.Random(seed))

def test_ten_pulls_shape():
    out, _ = make().pull_many(10)
    assert len(out) == 10
    assert all(r in RATES for r in out)

def test_pity_counts_up_when_no_six():
    # 把六星概率调成 0：普通抽永远抽不出六星，计数必然一路涨
    p = GachaPool({"6": 0.0, "5": 0.10, "4": 0.90}, pity=60, rng=random.Random(7))
    _, pity = p.pull_many(5)
    assert pity == 5

def test_hard_pity_triggers_and_resets():
    p = GachaPool({"6": 0.0, "5": 0.10, "4": 0.90}, pity=60, rng=random.Random(7))
    out, pity = p.pull_many(1, pity_start=59)   # 第 60 抽：硬保底
    assert out[0] == "6" and pity == 0