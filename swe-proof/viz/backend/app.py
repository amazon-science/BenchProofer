# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""FastAPI app for the SWE-Proof artifact site (read-only, plus opt-in comments).

`/` is the overview page and every other route is a drill-down from it, so the
site can be read by someone who has never seen the corpus. ONE site serves the
whole BENCHMARK x BACKEND matrix; `settings.BENCHMARKS` and
`settings.BACKENDS` are the authoritative lists. Every route is prefixed
/{bm}/{bk}/... and a 2-row header chooser switches cells: moving between
backends keeps the same instance (ids are shared across backends within a
benchmark), while switching benchmark rows goes to that row's index (the two
benchmarks have disjoint instance sets). `viz/serve.sh` binds 127.0.0.1 only;
an SSH tunnel is the access perimeter. Server-rendered Jinja UI (htmx for
in-page fragments). The dataset and repo mirrors are read-only; the only writes
are to the comments SQLite DB.
"""
from __future__ import annotations

import datetime as _dt
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Form, Path as FPath, Request
from fastapi.responses import (HTMLResponse, JSONResponse, PlainTextResponse,
                               RedirectResponse)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from . import comments, data, patchview, render, repo, settings
from . import agent as agent_mod

VIZ_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(VIZ_DIR / "templates"))


def _static_version() -> str:
    """Short fingerprint of app.css mtime — appended as ?v= so browsers refetch
    the stylesheet whenever it changes (no stale cache after a deploy)."""
    try:
        return str(int((VIZ_DIR / "static" / "app.css").stat().st_mtime))
    except OSError:
        return "0"


# expose helpers + the static-asset version to every template
templates.env.filters["md"] = render.md
templates.env.filters["hl"] = render.highlight_code
templates.env.globals["static_v"] = _static_version()
templates.env.globals["site_title"] = settings.SITE_TITLE
templates.env.globals["backends"] = settings.BACKENDS
templates.env.globals["formal_backends"] = settings.FORMAL_BACKENDS
templates.env.globals["extra_backends"] = settings.EXTRA_BACKENDS
templates.env.globals["backend_labels"] = settings.BACKEND_LABELS
templates.env.globals["benchmarks"] = settings.BENCHMARKS
templates.env.globals["benchmark_label"] = settings.benchmark_label
# the cell a header link falls back to on a page that names no cell (/comments),
# so no template hardcodes a benchmark or backend key
templates.env.globals["default_benchmark"] = settings.DEFAULT_BENCHMARK
templates.env.globals["default_backend"] = settings.DEFAULT_BACKEND
templates.env.globals["maintainers"] = settings.MAINTAINERS
# callables, not values: the corpus can change while the site is serving, so
# these are recomputed per render (behind data.py's TTL cache)
templates.env.globals["green_counts"] = data.green_counts
templates.env.globals["instance_counts"] = data.instance_counts


def _ts(epoch: float | None) -> str:
    if not epoch:
        return ""
    return _dt.datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M")


templates.env.filters["ts"] = _ts


def _short_id(iid: str) -> str:
    """Pro ids are instance_<org>__<proj>-<sha40>-v<sha40> — abbreviate the shas."""
    s = iid[len("instance_"):] if iid.startswith("instance_") else iid
    parts = s.split("-")
    out = []
    for part in parts:
        if len(part) == 40 and all(c in "0123456789abcdef" for c in part):
            out.append(part[:8])
        elif len(part) == 41 and part.startswith("v") and \
                all(c in "0123456789abcdef" for c in part[1:]):
            out.append("v" + part[1:9])
        else:
            out.append(part)
    return "-".join(out)


templates.env.filters["short_id"] = _short_id


def _sha(value, n: int = 10) -> str:
    """The first n characters of a commit id, from a row that may not carry one.

    `{{ row.base_commit[:10] }}` is a slice, and Jinja compiles a slice to a plain
    subscript rather than to `environment.getitem`, so it does NOT degrade to
    Undefined: a row with no `base_commit` raised UndefinedError and the instance
    page answered HTTP 500 instead of rendering the rest of the record. Every row
    in the corpus has one today, which is why only a partially-written or
    hand-edited instance.json reaches this.
    """
    return str(value or "")[:n]


templates.env.filters["sha"] = _sha


def _as_list(value) -> list:
    """A meta.json field the page counts or iterates over, as a list.

    Both `|length` and `{% for %}` raise TypeError on a scalar -- they do not
    degrade to Undefined the way an attribute lookup does -- so a record whose
    `axioms` is a number used to answer HTTP 500 on that cell's page. data.py
    guards the same three fields for the board with `_seq`; this is the template's
    half of it. A missing field is Undefined, which is not a list either, so it
    counts as 0 exactly as before.
    """
    return value if isinstance(value, list) else []


templates.env.filters["as_list"] = _as_list


# The pin below compiles every template this list matches, so it selects by
# extension rather than "every file under templates/": an editor's swap or backup
# file is not a template, and compiling it would turn a stray byte into a failure
# to boot. `_pinned_template_names` is also what the test reads, so the two can
# never disagree about the set.
_TEMPLATE_EXTS = ("html",)


def _pinned_template_names(t: Jinja2Templates) -> list[str]:
    return t.env.list_templates(extensions=_TEMPLATE_EXTS)


def _pin_templates(t: Jinja2Templates) -> Jinja2Templates:
    """Bind the template set to the code that is running, and compile it now.

    Jinja re-reads a template whenever its mtime moves (`auto_reload` defaults
    on), but nothing re-imports this module: the server is ONE long-lived
    process, so every filter stays whatever it was at startup. Without pinning
    the two halves drift, and editing a template to call a filter signature the
    running code does not have yet returns HTTP 500 on that page -- with the
    test suite green, because on disk the pair IS consistent. So a restart is
    what deploys, as it already is for this module and for `app.css`'s
    cache-buster.

    Compiling every template here rather than lazily on first request is the
    other half, and the reason `auto_reload = False` alone is not enough: Jinja
    loads a template when it is first rendered, so a page not yet visited would
    still be read from disk after the edit. It also turns a syntax error in any
    template into a failure to boot rather than a 500 on the one page that uses
    it.
    """
    t.env.auto_reload = False
    for name in _pinned_template_names(t):
        t.env.get_template(name)
    return t


_pin_templates(templates)


def RedirectResponse_to(url: str):
    """303 redirect so a POST becomes a GET (PRG pattern)."""
    return RedirectResponse(url=url, status_code=303)


def TR(name: str, ctx: dict):
    """TemplateResponse with the Starlette>=1.x signature (request first).

    `comments_enabled` is injected here rather than registered as a template
    global, for two reasons: it is read at RENDER time, so a deployment (or a
    test) that flips `settings.COMMENTS_ENABLED` after import is honoured; and it
    reaches every template including `base.html`, so no page can render a
    comment link the routes would refuse.
    """
    ctx.setdefault("comments_enabled", settings.COMMENTS_ENABLED)
    return templates.TemplateResponse(ctx["request"], name, ctx)


# route-level constraints: /{bm}/{bk}/ only matches real benchmark/backend keys,
# so reserved single-segment paths (/comments, /healthz, /static, future ones)
# can never be shadowed by the dynamic routes.
_BK = FPath(pattern=r"^(?:%s)$" % "|".join(settings.BACKENDS))
_BM = FPath(pattern=r"^(?:%s)$" % "|".join(settings.BENCHMARKS))


@asynccontextmanager
async def _lifespan(app):
    # creating the DB is the first write a served corpus would see, so it waits
    # for the feature to be on: a read-only deployment leaves no file behind
    if settings.COMMENTS_ENABLED:
        comments.init_db()
    yield


app = FastAPI(title=settings.SITE_TITLE, lifespan=_lifespan)
app.mount("/static", StaticFiles(directory=str(VIZ_DIR / "static")), name="static")


# ---------------------------------------------------------------- overview
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    """The site's front page: what the corpus claims, and how to read it.

    Every number on it is measured from the corpus being served rather than
    written into the template, so a page that says "500 instances" is reporting
    what is on disk. `corpus_rows` is one row per benchmark, and the per-backend
    figures are the same `green_counts` the header chooser drills into, so the
    overview cannot disagree with the boards it links to.
    """
    rows = []
    for bm in settings.BENCHMARKS:
        gc, bc = data.green_counts(bm), data.bundle_counts(bm)
        rows.append({"key": bm, "label": settings.benchmark_label(bm),
                     "instances": data.instance_counts(bm), "green": gc,
                     "bundles": sum(bc.values()),
                     "green_total": sum(gc.values())})
    return TR("home.html", {
        "request": request, "corpus_rows": rows,
        "tagline": settings.SITE_TAGLINE,
        "gate_families": data.GATE_FAMILIES, "gate_defs": data.GATE_DEFS,
        "default_cell": f"/{settings.DEFAULT_BENCHMARK}/{settings.DEFAULT_BACKEND}/",
    })


@app.get("/{bm}/{bk}/", response_class=HTMLResponse)
def index(request: Request, bm: str = _BM, bk: str = _BK, repo_filter: str = "",
          gate: str = "", q: str = "", flagged: str = ""):
    # copy: summary_table() is cached/shared across requests — never mutate it
    rows = [dict(r) for r in data.summary_table(bm, bk)]
    cc = comments.counts_by_instance(bm, bk) if settings.COMMENTS_ENABLED else {}
    for r in rows:
        r["comments"] = cc.get(r["instance_id"], {"total": 0, "open": 0, "resolved": 0})
    repos = sorted({r["repo"] for r in rows})
    if repo_filter:
        rows = [r for r in rows if r["repo"] == repo_filter]
    if q:
        ql = q.lower()
        rows = [r for r in rows if ql in r["instance_id"].lower()]
    if flagged == "relaxed":
        rows = [r for r in rows if r["relaxed_leakage"]]
    elif flagged == "axioms":
        rows = [r for r in rows if r["n_axioms"] > 0]
    elif flagged == "open-comments":
        rows = [r for r in rows if r["comments"]["open"] > 0]
    elif flagged == "green":
        rows = [r for r in rows if r["green"]]
    elif flagged == "not-green":
        rows = [r for r in rows if not r["green"]]
    # "unreadable" is the row `data._unreadable_row` substitutes for a record no
    # loader could read. Like "missing" it has no entry in the board's select --
    # both are normally absent from the whole corpus -- but ?flagged=unreadable is
    # then the query that answers "did construction leave anything unreadable".
    elif flagged in ("failing", "pending", "blocked", "timeout", "missing",
                     "unreadable"):
        rows = [r for r in rows if r["status"] == flagged]
    return TR("index.html", {
        "request": request, "bm": bm, "bk": bk, "rows": rows, "repos": repos,
        "repo_filter": repo_filter, "q": q, "flagged": flagged,
        "gate_order": data.GATE_ORDER, "gate_defs": data.GATE_DEFS,
        "total": len(data.all_instance_ids(bm)),
    })


# ---------------------------------------------------------------- instance page
@app.get("/{bm}/{bk}/i/{instance_id}", response_class=HTMLResponse)
def instance_page(request: Request, instance_id: str, bm: str = _BM, bk: str = _BK):
    row = data.dataset_row(bm, instance_id)
    if not row:
        return PlainTextResponse("unknown instance", status_code=404)
    m = data.meta(bm, bk, instance_id)
    g = data.gates(bm, bk, instance_id)
    n_f2p, n_p2p = _count_tests(row.get("FAIL_TO_PASS")), _count_tests(row.get("PASS_TO_PASS"))
    diff = data.read_bundle_file(bm, bk, instance_id, "patch.diff") or ""
    patch_files = patchview.parse(diff)
    bundle = data.bundle_present_files(bm, bk, instance_id)
    # render bundle code files (skip the .md ones — those render as markdown inline)
    code_blocks = []
    for name, label, lang in bundle:
        if name.endswith(".md"):
            continue
        src = data.read_bundle_file(bm, bk, instance_id, name)
        if src is not None:
            code_blocks.append({"name": name, "label": label, "lang": lang, "src": src})
    md_blocks = []
    for name, label, lang in bundle:
        if not name.endswith(".md"):
            continue
        src = data.read_bundle_file(bm, bk, instance_id, name)
        if src:
            md_blocks.append({"name": name, "label": label, "src": src})
    return TR("instance.html", {
        "request": request, "bm": bm, "bk": bk, "iid": instance_id, "row": row,
        "meta": m, "gates": g,
        "gate_order": data.GATE_ORDER, "gate_defs": data.GATE_DEFS,
        "patch_files": patch_files,
        "patch_stats": patchview.stats(diff), "code_blocks": code_blocks,
        "md_blocks": md_blocks, "audit_notes": data.audit_notes(bm, bk, instance_id),
        "verdict": data.verdict_md(bm, bk, instance_id),
        "result": data.result(bm, bk, instance_id), "green": data.is_green(g),
        "failing": data.failing_gates(g),
        "changed_files": repo.changed_files(bm, bk, instance_id),
        "threads": (comments.threads_for(bm, bk, instance_id)
                    if settings.COMMENTS_ENABLED else []),
        "flags": comments.FLAGS,
        "agent_enabled": settings.AGENT_ENABLED,
        "prepatch_models": data.list_prepatch(bm, bk, instance_id),
        "prepatch_diffs": data.prepatch_diffs(bm, bk, instance_id),
        "pbt": data.pbt_result(bm, bk, instance_id),
        "model_file": settings.model_file(bk),
        "prepatch_file": settings.prepatch_file(bk),
        "n_f2p": n_f2p, "n_p2p": n_p2p,
    })


def _count_tests(field) -> int:
    """FAIL_TO_PASS / PASS_TO_PASS may be a list or a JSON-encoded string."""
    import json as _json
    if field is None:
        return 0
    if isinstance(field, list):
        return len(field)
    try:
        v = _json.loads(field)
        return len(v) if isinstance(v, list) else 0
    except (ValueError, TypeError):
        return 0


# ---------------------------------------------------------------- repo browse (htmx fragments)
@app.get("/{bm}/{bk}/i/{instance_id}/file", response_class=HTMLResponse)
def repo_file(request: Request, instance_id: str, path: str, lang: str = "",
              bm: str = _BM, bk: str = _BK):
    content = repo.file_at_base(bm, instance_id, path)
    if content is None:
        return PlainTextResponse("file not found at base_commit", status_code=404)
    lang = lang or _lang_for(path)
    return TR("_file.html", {
        "request": request, "bm": bm, "bk": bk, "path": path, "src": content,
        "lang": lang, "iid": instance_id, "nlines": content.count("\n") + 1,
    })


@app.get("/{bm}/{bk}/i/{instance_id}/tree", response_class=HTMLResponse)
def repo_tree(request: Request, instance_id: str, subdir: str = "",
              bm: str = _BM, bk: str = _BK):
    entries = repo.tree_at_base(bm, instance_id, subdir)
    if entries is None:
        return PlainTextResponse("tree not found", status_code=404)
    parent = "/".join(subdir.strip("/").split("/")[:-1]) if subdir.strip("/") else None
    return TR("_tree.html", {
        "request": request, "bm": bm, "bk": bk, "iid": instance_id,
        "subdir": subdir.strip("/"), "entries": entries, "parent": parent,
    })


def _lang_for(path: str) -> str:
    ext = path.rsplit(".", 1)[-1].lower() if "." in path else ""
    return {"py": "python", "md": "markdown", "rst": "rst", "txt": "text",
            "js": "javascript", "json": "json", "cfg": "ini", "toml": "toml",
            "html": "html", "css": "css", "c": "c", "h": "c"}.get(ext, "text")


# ---------------------------------------------------------------- comments
_COMMENTS_OFF = ("comments are off (they are opt-in, because they are the only "
                 "part of this site that writes): set VIZ_COMMENTS_ENABLED=1 on "
                 "a deployment whose SQLite file survives a restart")


@app.post("/{bm}/{bk}/i/{instance_id}/comment")
def post_comment(instance_id: str, bm: str = _BM, bk: str = _BK, author: str = Form(""),
                 body: str = Form(""), flag: str = Form(""), parent_id: str = Form("")):
    if not settings.COMMENTS_ENABLED:
        return JSONResponse({"error": _COMMENTS_OFF}, status_code=403)
    if not data.dataset_row(bm, instance_id):
        return JSONResponse({"error": "unknown instance"}, status_code=404)
    pid = int(parent_id) if parent_id.strip().isdigit() else None
    try:
        comments.add_comment(bm, bk, instance_id, author, body, parent_id=pid, flag=flag)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    return RedirectResponse_to(f"/{bm}/{bk}/i/{instance_id}#comments")


@app.post("/{bm}/{bk}/comment/{comment_id}/status")
def toggle_status(comment_id: int, bm: str = _BM, bk: str = _BK, status: str = Form(...),
                  who: str = Form(""), back: str = Form("/comments")):
    if not settings.COMMENTS_ENABLED:
        return JSONResponse({"error": _COMMENTS_OFF}, status_code=403)
    try:
        comments.set_status(bm, bk, comment_id, status, who)
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)
    return RedirectResponse_to(back)


# ---------------------------------------------------------------- shared comments panel
@app.get("/comments", response_class=HTMLResponse)
def comments_panel(request: Request, status: str = "", flag: str = "",
                   backend: str = "", benchmark: str = ""):
    if not settings.COMMENTS_ENABLED:
        return PlainTextResponse(_COMMENTS_OFF, status_code=404)
    threads = comments.all_threads(status=status or None, flag=flag or None,
                                   backend=backend or None,
                                   benchmark=benchmark or None)
    # attach instance repo for display (rows carry their own benchmark key).
    # An unrecognized benchmark is shown as-is, NOT coerced to the default —
    # guessing would misattribute the thread to the wrong dataset.
    for t in threads:
        if t["benchmark"] in settings.BENCHMARKS:
            r = data.dataset_row(t["benchmark"], t["instance_id"]) or {}
            t["repo"] = r.get("repo", "")
        else:
            t["repo"] = ""
            t["unknown_benchmark"] = True
    return TR("comments.html", {
        "request": request, "threads": threads, "status": status, "flag": flag,
        "backend_filter": backend, "benchmark_filter": benchmark,
        "flags": comments.FLAGS,
    })


# ---------------------------------------------------------------- ask-an-agent
def _agent_error(e: BaseException) -> str:
    """Why the agent could not answer, in terms the reader can act on.

    Turning the feature on is not sufficient: it calls Bedrock with whatever
    credentials the host has, so the likely failure is environmental (boto3 not
    installed, no credentials, the model not enabled for this account/region)
    rather than anything about the bundle being reviewed. A bare exception class
    would read as a bug in the site.
    """
    name, txt = type(e).__name__, str(e)
    where = f"{settings.BEDROCK_MODEL} in {settings.BEDROCK_REGION}"
    if isinstance(e, ImportError):
        return f'ask-an-agent needs boto3: pip install -e ".[viz]" ({name})'
    if name in ("NoCredentialsError", "NoRegionError", "ProfileNotFound",
                "CredentialRetrievalError", "TokenRetrievalError",
                "ExpiredTokenException", "UnrecognizedClientException"):
        return f"no usable credentials for Bedrock ({where}) — {name}: {txt}"
    if name in ("AccessDeniedException", "ResourceNotFoundException",
                "ValidationException", "EndpointConnectionError"):
        return (f"Bedrock refused the call — check {where} is enabled for these "
                f"credentials ({name}: {txt})")
    return f"agent error: {name}: {txt}"


@app.post("/{bm}/{bk}/i/{instance_id}/ask")
def ask_agent(request: Request, instance_id: str, bm: str = _BM, bk: str = _BK,
              question: str = Form(...), convo_id: str = Form("")):
    if not settings.AGENT_ENABLED:
        return JSONResponse({"error": "ask-an-agent is off (it is opt-in): set "
                                      "VIZ_AGENT_ENABLED=1 and give the host "
                                      "Bedrock credentials"}, status_code=403)
    if not data.dataset_row(bm, instance_id):
        return JSONResponse({"error": "unknown instance"}, status_code=404)
    cid = int(convo_id) if convo_id.strip().isdigit() else None
    try:
        result = agent_mod.ask(bm, bk, instance_id, question, convo_id=cid)
    except agent_mod.RateLimited:
        return JSONResponse({"error": "rate limited — wait a moment"}, status_code=429)
    except Exception as e:  # noqa: BLE001
        return JSONResponse({"error": _agent_error(e)}, status_code=500)
    return TR("_answer.html", {
        "request": request, "bm": bm, "bk": bk, "iid": instance_id,
        "transcript": result["transcript"], "convo_id": result["convo_id"],
    })


@app.get("/healthz", response_class=PlainTextResponse)
def healthz():
    return "ok"
