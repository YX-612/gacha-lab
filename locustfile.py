from locust import HttpUser, task, between


class PullUser(HttpUser):
    host = "http://127.0.0.1:8000"
    wait_time = between(0, 0.05)

    @task(3)
    def pull(self):
        self.client.post("/api/pull",
                         json={"uid": "load", "pool_id": "standard", "count": 1})

    @task(1)
    def stats(self):
        self.client.get("/api/stats/load")
