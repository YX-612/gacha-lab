from pydantic import BaseModel, Field

class PullRequest(BaseModel):
    uid: str = Field(min_length=1, max_length=32, examples=["amiya"])
    pool_id: str = Field(examples=["standard"])
    count: int = Field(ge=1, le=10, description="单抽=1，十连=10")

class PullResult(BaseModel):
    uid: str
    pool_id: str
    results: list[str]      # 每抽稀有度，如 ["4","5","4",...]
    pity_now: int           # 抽完后的保底进度