import os, tempfile, pytest

@pytest.fixture()
def client(tmp_path):

    os.environ["GACHA_DB"] = str(tmp_path / "test.db")
    from app import database
    database.DB_PATH = os.environ["GACHA_DB"]
    database.init_db()
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as c:  
        yield c