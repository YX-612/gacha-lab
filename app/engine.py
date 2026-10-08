import random

class GachaPool:
    """硬保底：第 pity 抽必出六星，其余按公示概率。rng 可注入——测试能定种子。"""
    def __init__(self, rates: dict, pity: int, rng=random):
        self.rates, self.pity, self.rng = rates, pity, rng

    def _roll(self, pity_now: int) -> str:
        if pity_now >= self.pity - 1:
            return "6"
        x = self.rng.random()
        acc = 0.0
        for rarity, p in sorted(self.rates.items(), key=lambda kv: -float(kv[0])):
            acc += p
            if x < acc:
                return rarity
        return "3"

    def pull_many(self, count: int, pity_start: int = 0):
        """返回 (每抽稀有度列表, 结束时保底计数)。抽到六星计数归零。"""
        out, pity = [], pity_start
        for _ in range(count):
            r = self._roll(pity)
            out.append(r)
            pity = 0 if r == "6" else pity + 1
        return out, pity