import io
import pytest
from fastapi.testclient import TestClient

from app import main, schemas

client = TestClient(main.app)

FAKES = {
    schemas.KnowledgeReport: schemas.KnowledgeReport(
        answer="a", key_points=["k"], standards_referenced=[], related_topics=[]
    ),
    schemas.CrackReport: schemas.CrackReport(
        crack_detected=True, crack_type="hairline", severity="low", confidence=0.8,
        probable_causes=["shrinkage"], recommended_actions=["monitor"], urgency="routine",
        disclaimer="Consult an engineer.",
    ),
}


@pytest.fixture(autouse=True)
def fake_llm(monkeypatch):
    monkeypatch.setattr(main, "ask_json", lambda s, p, cls, imgs=None: FAKES[cls])


def test_health():
    assert client.get("/api/health").status_code == 200


def test_knowledge():
    r = client.post("/api/knowledge", data={"question": "What is M25 concrete?"})
    assert r.status_code == 200 and r.json()["answer"] == "a"


def test_crack_requires_image():
    assert client.post("/api/cracks", data={"location": "wall"}).status_code == 422


def test_crack_ok_and_bad_mime():
    ok = client.post("/api/cracks", files={"file": ("w.png", io.BytesIO(b"x"), "image/png")})
    assert ok.status_code == 200 and ok.json()["severity"] == "low"
    bad = client.post("/api/cracks", files={"file": ("w.txt", io.BytesIO(b"x"), "text/plain")})
    assert bad.status_code == 415


def test_safety_needs_input():
    assert client.post("/api/safety", data={}).status_code == 400
