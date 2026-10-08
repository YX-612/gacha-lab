# seed_10k.py — 灌 1 万抽演示数据（一次性脚本）
import httpx

with httpx.Client(timeout=30) as c:
    for i in range(1000):          # 1000 轮 × 10 连 = 1 万抽
        r = c.post("http://127.0.0.1:8000/api/pull",
                   json={"uid": "tester", "pool_id": "standard", "count": 10})
        r.raise_for_status()
        if (i + 1) % 100 == 0:
            print(f"{(i + 1) * 10} 抽完成")
print("灌完了，浏览器开 http://127.0.0.1:8000/api/stats/tester")