import layoffs_tracker as lt

EVENTS = [
    {"event_id": 1, "company": "Acme", "state": "CA", "workers": 120, "announced_date": "2026-03-01",
     "status": "confirmed", "source_types": ["warn", "news"]},
    {"event_id": 2, "company": "Acme", "state": "TX", "workers": 80, "announced_date": "2026-02-01",
     "status": "confirmed", "source_types": ["warn"]},
    {"event_id": 3, "company": "Beta", "state": "CA", "workers": None, "announced_date": "2026-01-15",
     "status": "confirmed", "source_types": ["sec"]},
]


class FakeClient:
    def __init__(self):
        self.calls = []

    def layoffs_events(self, **params):
        self.calls.append(params)
        o = params["offset"]
        return {"total": len(EVENTS), "rows": EVENTS[o:o + params["limit"]]}

    def layoffs_companies(self, **params):
        self.calls.append(params)
        return {"rows": [{"company": "Acme", "workers": 200, "events": 2}]}


def test_by_company():
    ranked = lt.by_company(EVENTS)
    assert ranked[0] == {"company": "Acme", "events": 2, "workers": 200, "states": "CA, TX"}
    assert ranked[1]["workers"] == 0


def test_paging_and_csv(tmp_path, monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(lt, "DataPorium", lambda: fake)
    monkeypatch.setattr(lt, "PAGE", 2)
    assert lt.main(["--state", "CA", "--out", str(tmp_path)]) == 0
    lines = (tmp_path / "layoffs.csv").read_text().splitlines()
    assert len(lines) == 4 and "warn; news" in lines[1]
    assert fake.calls[0]["status"] == "confirmed" and fake.calls[0]["state"] == "CA"
    assert [c["offset"] for c in fake.calls] == [0, 2]


def test_top(tmp_path, monkeypatch):
    fake = FakeClient()
    monkeypatch.setattr(lt, "DataPorium", lambda: fake)
    assert lt.main(["--top", "--days", "365", "--status", "all", "--out", str(tmp_path)]) == 0
    assert fake.calls[0]["days"] == 365 and fake.calls[0]["status"] is None
    assert (tmp_path / "top_companies.csv").exists()
