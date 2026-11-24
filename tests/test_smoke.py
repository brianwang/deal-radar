import pytest
from fastapi.testclient import TestClient

from deal_radar import db
from deal_radar.config import settings


@pytest.fixture()
def tmp_db(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "deal_radar_db", str(tmp_path / "test.db"))
    db.init_db()
    return tmp_path


def test_add_and_list(tmp_db):
    new_id = db.add_demand("manual", "做一个 RAG 知识库", "把 PDF 做成问答", None, "2-3 万")
    assert new_id is not None
    rows = db.list_demands_with_scores()
    assert len(rows) == 1
    assert rows[0]["title"] == "做一个 RAG 知识库"
    assert rows[0]["score"] is None


def test_duplicate_url_ignored(tmp_db):
    assert db.add_demand("rss", "a", "b", "http://example.com/1", None)
    assert db.add_demand("rss", "a", "b", "http://example.com/1", None) is None
    assert len(db.list_demands_with_scores()) == 1


def test_score_and_proposal_roundtrip(tmp_db):
    demand_id = db.add_demand("manual", "标题", "描述", None, None)
    db.upsert_score(demand_id, 88, "很匹配", "预算未知")
    demand = db.get_demand(demand_id)
    assert demand["score"] == 88
    assert demand["reason"] == "很匹配"

    proposal_id = db.add_proposal(demand_id, "这是一封投标信")
    assert proposal_id
    assert db.get_proposals(demand_id)[0]["status"] == "draft"
    db.update_proposal_status(proposal_id, "sent")
    assert db.get_proposals(demand_id)[0]["status"] == "sent"


def test_api_index_and_create(tmp_db):
    from deal_radar.web.app import app

    with TestClient(app) as client:
        assert client.get("/").status_code == 200
        resp = client.post(
            "/demands",
            data={"title": "测试需求", "description": "描述", "budget": "1 万", "url": ""},
            follow_redirects=False,
        )
        assert resp.status_code == 303
        detail = client.get("/demands/1")
        assert detail.status_code == 200
        assert "测试需求" in detail.text


def test_api_detail_404(tmp_db):
    from deal_radar.web.app import app

    with TestClient(app) as client:
        assert client.get("/demands/999").status_code == 404
