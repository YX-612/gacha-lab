# gacha-lab · 抽卡系统测试实验室

> 自建带 60 抽硬保底的抽卡引擎，转身当它的测试：用蒙特卡洛自证概率口径，用 pytest 守住边界，用 Locust 摸清瓶颈。

![tests](https://img.shields.io/badge/pytest-12%20passed-brightgreen) ![coverage](https://img.shields.io/badge/coverage-97%25-blue)

在线演示：<!-- render 部署后填入，如 https://gacha-lab-xxxx.onrender.com/docs -->（免费实例休眠，首访约 30–60s）

## 它做什么

- **抽卡引擎** `app/engine.py`：公示概率（6★ 2% / 5★ 10% / 4★ 88%）+ 60 抽硬保底，随机源可注入（单测可定种子、结果可复现）
- **REST API** `app/main.py`：`POST /api/pull`、`GET /api/history/{uid}`、`GET /api/stats/{uid}`、`GET /api/pools`、`POST /api/simulate`
- **概率自证**：1 万抽实测综合概率 2.92%，与保底模型理论值 1/E[轮长] ≈ 2.85% 吻合——公示的 2% 是基础概率，硬保底将其抬升，两层口径实测分离
- **接口自动化**：pytest 12 例全绿（参数化边界 / 404 / 翻页不重不漏 / 保底三件套），覆盖率 97%
- **专项压测**：Locust 阶梯加压 100→300→600→1000 并发，QPS / p95 与瓶颈分析见压测报告

## 30 秒上手

```bash
git clone https://github.com/YX-612/gacha-lab && cd gacha-lab
pip install -r requirements.txt
uvicorn app.main:app --reload     # 打开 http://127.0.0.1:8000/docs
```

## 证据链

- `reports/gap_hist.png` — 六星间隔分布直方图（蒙特卡洛）
- `reports/偏差表.md` — 1 万 / 10 万 / 100 万次实测 vs 理论
- `reports/压测报告.md` — 并发 / QPS / p95 与瓶颈分析
- `htmlcov/index.html` — pytest-cov 覆盖率报告（本地 `python -m pytest --cov=app --cov-report=html` 生成）

## 设计取舍

- **保底进度不落库**：从抽卡流水实时推导——可审计、可重放，杜绝配置与状态漂移
- **随机源可注入**：引擎接受 rng 参数，测试用固定种子复现保底边界
- **SQLite + WAL**：单机演示足够；压测定位瓶颈后，扩展路径为批量插入 / 多 worker / 换 Postgres
