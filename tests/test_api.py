import pytest

BODY = {"uid": "t1", "pool_id": "standard", "count": 10}

def test_pull_ten(client):
    r = client.post("/api/pull", json=BODY)
    assert r.status_code == 200
    assert len(r.json()["results"]) == 10

@pytest.mark.parametrize("count", [0, -1, 11, 100, "十"])
def test_pull_bad_count(client, count):
    r = client.post("/api/pull", json={**BODY, "count": count})
    assert r.status_code == 422

def test_pull_unknown_pool(client):
    r = client.post("/api/pull", json={**BODY, "pool_id": "nope"})
    assert r.status_code == 404

def test_stats_consistency(client):
    for _ in range(10):
        client.post("/api/pull", json=BODY)
    s = client.get("/api/stats/t1").json()
    assert s["total"] == 100
    assert 0 <= s["six_star"] <= 100
    assert s["actual_rate"] is None or 0 <= s["actual_rate"] <= 1

def test_history_pagination(client):
    client.post("/api/pull", json=BODY)
    h1 = client.get("/api/history/t1?limit=5").json()
    h2 = client.get("/api/history/t1?skip=5&limit=5").json()
    h3 = client.get("/api/history/t1?skip=10&limit=5").json()
    assert h1["total"] == 10
    assert len(h1["items"]) == 5 and len(h2["items"]) == 5
    assert h3["items"] == []
    ids = [it["id"] for it in h1["items"]] + [it["id"] for it in h2["items"]]
    assert sorted(ids) == list(range(1, 11))