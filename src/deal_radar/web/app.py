from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .. import db
from ..proposal import write_proposal
from ..scoring import score_demand
from ..sources.rss import import_rss

WEB_DIR = Path(__file__).resolve().parent


@asynccontextmanager
async def lifespan(_app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="deal-radar", lifespan=lifespan)
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")


@app.get("/")
def index(request: Request, imported: int | None = None, error: str | None = None):
    demands = db.list_demands_with_scores()
    return templates.TemplateResponse(
        request,
        "index.html",
        {"demands": demands, "imported": imported, "error": error},
    )


@app.post("/demands")
def create_demand(
    title: str = Form(...),
    description: str = Form(...),
    url: str = Form(""),
    budget: str = Form(""),
):
    db.add_demand(
        source="manual",
        title=title.strip(),
        description=description.strip(),
        url=url.strip() or None,
        budget=budget.strip() or None,
    )
    return RedirectResponse("/", status_code=303)


@app.get("/demands/{demand_id}")
def demand_detail(request: Request, demand_id: int, error: str | None = None):
    demand = db.get_demand(demand_id)
    if not demand:
        raise HTTPException(status_code=404, detail="需求不存在")
    proposals = db.get_proposals(demand_id)
    return templates.TemplateResponse(
        request,
        "demand.html",
        {"demand": demand, "proposals": proposals, "error": error},
    )


@app.post("/demands/{demand_id}/score")
def score(demand_id: int):
    demand = db.get_demand(demand_id)
    if not demand:
        raise HTTPException(status_code=404, detail="需求不存在")
    try:
        result = score_demand(demand)
    except Exception as exc:  # noqa: BLE001 - 展示给用户
        return RedirectResponse(
            f"/demands/{demand_id}?error={quote(str(exc)[:300])}", status_code=303
        )
    db.upsert_score(demand_id, result["score"], result["reason"], result["risk"])
    return RedirectResponse(f"/demands/{demand_id}", status_code=303)


@app.post("/demands/{demand_id}/proposal")
def proposal(demand_id: int):
    demand = db.get_demand(demand_id)
    if not demand:
        raise HTTPException(status_code=404, detail="需求不存在")
    try:
        content = write_proposal(demand)
    except Exception as exc:  # noqa: BLE001
        return RedirectResponse(
            f"/demands/{demand_id}?error={quote(str(exc)[:300])}", status_code=303
        )
    db.add_proposal(demand_id, content)
    return RedirectResponse(f"/demands/{demand_id}", status_code=303)


@app.post("/proposals/{proposal_id}/status")
def proposal_status(proposal_id: int, status: str = Form(...)):
    db.update_proposal_status(proposal_id, status)
    return RedirectResponse("/", status_code=303)


@app.post("/import/rss")
def import_rss_route(url: str = Form(...)):
    try:
        added = import_rss(url.strip())
    except Exception as exc:  # noqa: BLE001
        return RedirectResponse(f"/?error={quote(str(exc)[:300])}", status_code=303)
    return RedirectResponse(f"/?imported={added}", status_code=303)
