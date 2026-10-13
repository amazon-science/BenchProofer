# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""End-to-end route tests (no live Bedrock; agent disabled)."""
import re

import pytest
from conftest import FULL_BM, FULL_IID, IID, require_mirror
from backend import settings

# disable the live agent for route tests (set on the module, not env: settings
# may already be imported by another test module)
settings.AGENT_ENABLED = False

from starlette.testclient import TestClient  # noqa: E402
from backend.app import app  # noqa: E402

# every board route is /{benchmark}/{backend}/... — these tests drive the Pro row
P = "/pro"

# a chooser cell: a LINK wrapped around a bare count. A count rendered as text,
# or an anchor with anything else inside it, deliberately does not match.
_CELL = re.compile(r'<a href="(/[^"]+)"[^>]*class="bk-cell[^"]*"[^>]*>'
                   r'\s*<span class="bk-count">(\d+)</span></a>', re.S)


def _cell_hrefs(hrefs, bm, bk):
    """A cell either keeps the instance (same row: /i/<iid>) or links to the
    row's index; both are a working cell for that backend."""
    return [h for h in hrefs if h == f"/{bm}/{bk}/" or h.startswith(f"/{bm}/{bk}/i/")]


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def test_root_is_the_overview_page(client):
    """`/` is a page, not a redirect into a cell.

    It is the front page of the published site (and the file a static publish
    serves as its index), so it has to be readable by someone who has never seen
    the corpus, and it has to lead into the boards rather than replace them.
    """
    r = client.get("/", follow_redirects=False)
    assert r.status_code == 200, "the overview must render, not redirect"
    t = r.text
    assert settings.SITE_TITLE in t and settings.SITE_TAGLINE in t
    # a way in: the default cell, plus one link per benchmark row
    assert f'href="/{settings.DEFAULT_BENCHMARK}/{settings.DEFAULT_BACKEND}/"' in t
    for bm in settings.BENCHMARKS:
        assert settings.benchmark_label(bm) in t, f"{bm} is missing from the overview"


def test_overview_figures_are_measured_not_written(client):
    """Every figure on the front page comes from the corpus being served, so the
    overview cannot disagree with the board it links to.

    A figure hardcoded in the template is the failure this catches: it reads as a
    claim about the release long after the corpus has moved. Each per-backend
    count is therefore compared against `green_counts` (the same function the
    header chooser drills into) AND required to link to the board it counts.
    """
    from backend import data
    t = client.get("/").text
    for bm in settings.BENCHMARKS:
        gc = data.green_counts(bm)
        for b in settings.BACKENDS:
            assert re.search(r'href="/%s/%s/\?flagged=green"[^>]*>\s*%d\s*</a>'
                             % (bm, b, gc[b]), t, re.S), \
                f"{bm}/{b}: the overview does not report {gc[b]} linked to its board"
        n = data.instance_counts(bm)
        assert f'class="num">{n}<' in t, f"{bm}: instance count {n} missing"
        # bundles present, not instances x backends: a lane may cover a subset of
        # the row, and multiplying would publish bundles that do not exist
        assert f'class="num">{sum(data.bundle_counts(bm).values())}<' in t


def test_the_overview_classifies_every_gate(client):
    """`GATE_FAMILIES` is the front page's taxonomy of the gate suite, so it must
    partition `GATE_ORDER`: a newly registered gate that nobody classified would
    vanish from the only page explaining what the suite is for, and a stale key
    would advertise a gate that no longer runs."""
    from backend import data
    listed = [g for _name, _why, keys in data.GATE_FAMILIES for g in keys]
    assert len(listed) == len(set(listed)), "a gate is classified in two families"
    assert set(listed) == set(data.GATE_ORDER), (
        f"unclassified: {sorted(set(data.GATE_ORDER) - set(listed))}; "
        f"stale: {sorted(set(listed) - set(data.GATE_ORDER))}")
    t = client.get("/").text
    for g in data.GATE_ORDER:
        assert g in t, f"{g} is not named on the overview"
        # the same wording the boards hover, rather than a second description
        assert data.GATE_DEFS[g][:40] in t, f"{g}: definition not carried over"


def test_comments_are_off_unless_a_deployment_opts_in(client, monkeypatch):
    """Comments are the site's only writable surface, so they are opt-in.

    With the flag off, no page may LINK to a comment route and no route may
    accept a write: a static publish (GitHub Pages, an object store) runs no
    process, so a form left on the page would post into nothing. The suite runs
    with the feature on (see conftest), which is why this measures the default
    rather than the other way round.
    """
    monkeypatch.setattr(settings, "COMMENTS_ENABLED", False)
    assert client.get("/comments").status_code == 404
    for page in ("/", f"{P}/nagini/", f"{P}/nagini/i/{IID}"):
        t = client.get(page).text
        assert 'href="/comments"' not in t, f"{page}: links to a route that 404s"
        assert f"/i/{IID}/comment" not in t, f"{page}: renders a form that 403s"
        assert "open-comments" not in t, f"{page}: offers a comments filter"
    r = client.post(f"{P}/nagini/i/{IID}/comment",
                    data={"author": "rev", "body": "hi"}, follow_redirects=False)
    assert r.status_code == 403
    r = client.post(f"{P}/nagini/comment/1/status",
                    data={"status": "resolved", "who": "rev"}, follow_redirects=False)
    assert r.status_code == 403


def test_index(client):
    r = client.get(f"{P}/nagini/")
    assert r.status_code == 200 and IID in r.text


def test_unknown_cell_404(client):
    # route-level pattern constraint -> 422 (or 404); never a 200
    assert client.get(f"{P}/coq/").status_code in (404, 422)
    assert client.get(f"{P}/coq/i/{IID}").status_code in (404, 422)
    # unknown BENCHMARK likewise
    assert client.get("/humaneval/nagini/").status_code in (404, 422)
    assert client.get(f"/humaneval/nagini/i/{IID}").status_code in (404, 422)


def test_chooser_is_a_full_benchmark_x_backend_matrix(client):
    """The header chooser is a table-shaped matrix: backend names head the
    COLUMNS, benchmarks label the ROWS (in BENCHMARK_DEFS order), a totals column
    carries each row's instance count, and every cell is that cell's green count
    linking to that cell's board.

    Three failure modes, all reported as "only a total column, and the total is
    not clickable":
      * the payload: green_counts() is a {backend: n} breakdown, not one flat
        number;
      * the render: every number is an anchor -- a backend count to its own
        board, a total to the row's whole instance list. A count rendered as a
        bare <span> is dead text and fails here;
      * the layout: the matrix is a clipping flex item, so a shrinkable box or a
        zero-floor grid track lets the header hide the per-backend columns and
        leave the totals column alone on screen.

    Driven off the settings lists rather than a hard-coded set, so a backend
    added without a chooser cell fails here instead of vanishing from the header.
    """
    from backend import data
    formal = [b for b in settings.BACKENDS if b in settings.FORMAL_BACKENDS]
    extra = [b for b in settings.BACKENDS if b not in settings.FORMAL_BACKENDS]
    assert set(formal) >= {"nagini", "velvet", "lean"}

    # ---- payload: a per-backend breakdown, not a flat total
    for bm in settings.BENCHMARKS:
        gc = data.green_counts(bm)
        assert isinstance(gc, dict), f"{bm}: green_counts must be a breakdown"
        for b in formal:
            assert b in gc, f"{bm}: breakdown lost the {b} column"
            assert isinstance(gc[b], int) and gc[b] >= 0
        n = data.instance_counts(bm)
        assert isinstance(n, int) and n >= max(gc[b] for b in formal)

    for page in (f"{P}/nagini/", f"{P}/nagini/i/{IID}", "/comments"):
        t = client.get(page).text
        # ---- shape: one header row of backend names above both benchmark rows,
        # and one single-column box per backend without a verifier, set apart
        assert t.count('class="bk-colhead') == len(formal) + 1 + len(extra), \
            f"{page}: expected a colhead per formal backend + totals + each extra"
        assert t.count('bk-extra') == len(extra), \
            f"{page}: expected one set-apart box per backend with no verifier"
        assert t.index('bk-colhead') < t.index('bk-rowlab'), \
            f"{page}: backend column headers must precede the benchmark rows"
        # row order. Located by the CELL class: the column heads sit above both
        # rows and link into the CURRENT row, so a bare path search finds the head
        # first and says nothing about row order.
        rows = [re.search(r'<a href="/%s/nagini/"[^>]*class="bk-cell' % bm, t)
                for bm in settings.BENCHMARKS]
        assert all(rows), f"{page}: a benchmark row has no nagini cell"
        starts = [m.start() for m in rows]
        assert starts == sorted(starts), \
            f"{page}: rows must render in {list(settings.BENCHMARKS)} order"

        # ---- render: every count in the matrix is inside an anchor
        matrix = re.search(r'<nav class="bk-matrix"[^>]*>(.*?)</nav>', t, re.S)
        assert matrix, f"{page}: the chooser matrix did not render"
        block = matrix.group(1)
        counted = re.findall(
            r'<(a|span)\b[^>]*class="bk-(?:cell|total)[^"]*"[^>]*>(.*?)</\1>',
            block, re.S)
        assert counted, f"{page}: no counts found in the chooser"
        for tag, inner in counted:
            assert tag == "a", f"{page}: count {inner.strip()!r} is not a link"

        # ---- every configured backend has a linked cell showing ITS count, both
        # in the matrix (the formal ones) and anywhere on the page (all of them,
        # so an extra box that lost its cells fails too)
        for scope, html, want in (("matrix", block, formal),
                                  ("page", t, settings.BACKENDS)):
            cells = dict(_CELL.findall(html))
            for bm in settings.BENCHMARKS:
                gc = data.green_counts(bm)
                for b in want:
                    hrefs = _cell_hrefs(cells, bm, b)
                    assert hrefs, f"{page}: {bm}/{b} has no linked cell in the {scope}"
                    for h in hrefs:
                        assert cells[h] == str(gc[b]), \
                            f"{page}: {bm}/{b} shows {cells[h]}, expected {gc[b]}"

        # ---- the totals column: the row's instance count, drilling into that
        # row's whole list on a real backend
        for bm in settings.BENCHMARKS:
            n = data.instance_counts(bm)
            assert f'{n} instances">{n}<' in t, f"{page}: missing total {n} for {bm}"
            m = re.search(r'<a href="(/%s/[a-z]+/)"[^>]*class="bk-total[^"]*"'
                          r'[^>]*>\s*%d\s*</a>' % (bm, n), block)
            assert m, f"{page}: the {bm} total ({n}) is not a drill-down link"
            assert m.group(1).split("/")[2] in settings.BACKENDS

        # the backend tracks reserve their content width (no bare 1fr track)
        assert "repeat(%d, minmax(" % len(formal) in t, \
            f"{page}: backend columns can be squeezed to nothing"

    # ---- layout: the table cannot be shrunk/clipped out of the header
    css = client.get("/static/app.css").text
    matrix_rule = re.search(r"header\.top nav\.bk-matrix\{([^}]*)\}", css)
    assert matrix_rule, ".bk-matrix rule missing"
    body = matrix_rule.group(1)
    assert "flex:0 0 auto" in body or "flex-shrink:0" in body, \
        "the chooser must not shrink: overflow:hidden lets it clip its columns"
    assert "min-width:min-content" in body
    top = re.search(r"header\.top\{([^}]*)\}", css)
    assert top and "flex-wrap:wrap" in top.group(1), \
        "the header must wrap rather than squeeze the chooser"


def test_chooser_renders_all_backends_without_the_formal_split(client):
    """The chooser must not depend on the formal/extra split BEING THERE: if that
    pair of template globals is unavailable, the matrix still renders one column
    per configured backend. Guards the collapse where an absent list silently
    became a zero-column grid, leaving only the totals and nothing clickable."""
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    from backend.app import templates
    # a SEPARATE environment: overlay() shares the parent's globals dict by
    # reference and per-template globals merely chain onto it, so neither can
    # actually hide a name from the app's own env. It escapes like the app's.
    src_dir = templates.env.loader.searchpath[0]
    env = Environment(loader=FileSystemLoader(src_dir),
                      autoescape=select_autoescape(["html", "xml"]))
    env.globals.update({k: v for k, v in templates.env.globals.items()
                        if k not in ("formal_backends", "extra_backends")})
    env.filters.update(templates.env.filters)
    t = env.get_template("base.html").render(bm="pro", bk="nagini", request=None)
    # match on the repeat() COUNT, not the track syntax, so this keeps biting
    # if the track function changes again
    assert "repeat(0," not in t, "chooser collapsed to a zero-column grid"
    linked = set(re.findall(r'<a href="(/[^"]+/)"[^>]*class="bk-cell', t))
    for bm in settings.BENCHMARKS:
        for b in settings.BACKENDS:
            assert f"/{bm}/{b}/" in linked, f"{bm}/{b} lost its cell without the split"
    # the totals column alone is exactly the regression, not an acceptable render
    assert len(linked) == len(settings.BENCHMARKS) * len(settings.BACKENDS)


def test_backend_counts_open_the_board_they_count_from_an_instance_page(client):
    """A count in the chooser opens the BOARD it counts -- including from an
    instance page, which is the only place the two targets differ.

    The number under a backend is that cell's fully-green count, so its drill-down
    is that cell's instance list, NOT the same-instance switch that the column
    head carries: routing a count through that switch makes the number under the
    active backend a link to the URL the reader is already on, and every other
    number in the row a link to a sibling instance page rather than to a board.
    From a board route the two targets coincide, so this measures from
    /{bm}/{bk}/i/{iid} and compares each href to the page's own URL.
    """
    from urllib.parse import urljoin
    page = f"{P}/nagini/i/{IID}"
    here = urljoin("http://viz.test", page)
    t = client.get(page).text
    cells = [h for h, _n in _CELL.findall(t)]
    boards = {f"/{bm}/{b}/" for bm in settings.BENCHMARKS for b in settings.BACKENDS}
    assert len(cells) == len(boards), \
        f"expected one count per cell, got {len(cells)}: {cells}"
    for href in cells:
        assert href in boards, f"count links to {href}, which is not a board"
        assert urljoin(here, href) != here, \
            f"count links back to the page it is rendered on: {href}"
    assert set(cells) == boards, f"missing board links: {sorted(boards - set(cells))}"


def test_backend_toggle_keeps_instance_within_row(client):
    """Switching backend keeps the instance; switching benchmark row does NOT
    (the two benchmarks have disjoint instance sets). The instance travels on the
    column HEAD -- the backend name -- and not on the count beside it, which is a
    cell-level number and owes its click to that cell's board (above)."""
    t = client.get(f"{P}/nagini/i/{IID}").text
    for b in ("velvet", "lean"):
        assert re.search(r'<a href="/pro/%s/i/%s"[^>]*class="bk-colhead' % (b, IID), t), \
            f"the {b} column head must carry the instance"
    # the verified row links to its index, never to a Pro instance id
    assert f'/verified/nagini/i/{IID}' not in t
    assert 'href="/verified/nagini/"' in t


def test_every_formal_backend_serves_an_instance(client):
    """One instance, one page per backend, each naming ITS OWN model artifact --
    the naming is what tells the cells of one instance apart."""
    for b in settings.FORMAL_BACKENDS:
        r = client.get(f"{P}/{b}/i/{IID}")
        assert r.status_code == 200, f"{b} instance page failed"
        mine = settings.model_file(b)
        assert mine in r.text, f"{b}: page does not name {mine}"
        for other in settings.BACKENDS:
            theirs = settings.model_file(other)
            assert theirs == mine or theirs not in r.text, \
                f"{b}: page names {other}'s {theirs}"


def test_verified_row_serves_its_own_instances(client):
    """The verified board reads benchmark-verified/, and a Pro id 404s there."""
    from backend import data
    vids = data.all_instance_ids("verified")
    assert vids, "no verified instances found"
    r = client.get("/verified/nagini/")
    assert r.status_code == 200 and vids[0] in r.text
    assert client.get(f"/verified/nagini/i/{vids[0]}").status_code == 200
    # cross-row leakage: a Pro instance must not resolve on the verified board
    assert client.get(f"/verified/nagini/i/{IID}").status_code == 404
    # ...and vice versa
    assert client.get(f"{P}/nagini/i/{vids[0]}").status_code == 404


def test_index_filters(client):
    assert client.get(f"{P}/nagini/?flagged=relaxed").status_code == 200
    assert client.get(f"{P}/nagini/?repo_filter=ansible/ansible").status_code == 200
    assert client.get(f"{P}/nagini/?flagged=green").status_code == 200
    assert client.get(f"{P}/nagini/?flagged=blocked").status_code == 200
    assert client.get(f"{P}/nagini/?q=0ea40e09").status_code == 200


def test_instance_page_sections(client):
    t = client.get(f"{P}/nagini/i/{IID}").text
    for s in ["problem statement", "Equivalent real patch", "Browse repository",
              "model &amp; equivalence", "Audit verdicts", "Metadata", "Comments"]:
        assert s in t, f"missing section: {s}"


def test_the_model_card_names_the_backend_it_is_showing(client):
    """The heading names the backend whose model the card shows. Jinja renders an
    unknown name as empty rather than raising, so a heading that reads
    " model & equivalence" is a passing template with a missing global. Checked
    per backend, since the point of the heading is telling the cells apart."""
    for bk in settings.BACKENDS:
        t = client.get(f"{P}/{bk}/i/{IID}").text
        label = settings.BACKEND_LABELS[bk]
        assert f"{label} model &amp; equivalence" in t, bk


def test_instance_404(client):
    assert client.get(f"{P}/nagini/i/not__real-9999").status_code == 404


def test_repo_browse(client):
    require_mirror("pro", IID)
    assert "Ansible" in client.get(f"{P}/nagini/i/{IID}/file?path=README.md").text
    assert "lib" in client.get(f"{P}/nagini/i/{IID}/tree").text
    assert "ansible" in client.get(f"{P}/nagini/i/{IID}/tree?subdir=lib").text


def test_repo_browse_guard(client):
    assert client.get(f"{P}/nagini/i/{IID}/file?path=../../../etc/passwd").status_code == 404


def test_comment_lifecycle(client):
    # post
    r = client.post(f"{P}/nagini/i/{IID}/comment",
                    data={"author": "rev1", "body": "Spec looks weak on empty.",
                          "flag": "weak-spec"},
                    follow_redirects=False)
    assert r.status_code == 303
    assert "rev1" in client.get(f"{P}/nagini/i/{IID}").text
    assert "rev1" in client.get("/comments").text
    # resolve (any collaborator can)
    client.post(f"{P}/nagini/comment/1/status",
                data={"status": "resolved", "who": "rev2", "back": "/comments"},
                follow_redirects=False)
    assert "resolved by rev2" in client.get("/comments").text
    # reply
    client.post(f"{P}/nagini/i/{IID}/comment",
                data={"author": "rev2", "body": "Fixed, thanks.", "parent_id": "1"},
                follow_redirects=False)
    assert "Fixed, thanks." in client.get(f"{P}/nagini/i/{IID}").text


def test_comments_are_scoped_per_benchmark(client):
    """The same backend on the other benchmark row is a DIFFERENT board: its
    threads must not bleed across, and its ids are its own."""
    from backend import comments, data
    vid = data.all_instance_ids("verified")[0]
    cid = comments.add_comment("verified", "nagini", vid, "rev1", "verified-row thread")
    # visible on the verified board, absent from the Pro board
    assert "verified-row thread" in client.get(f"/verified/nagini/i/{vid}").text
    assert "verified-row thread" not in client.get(f"{P}/nagini/i/{IID}").text
    # the shared panel shows both, tagged, and filters by benchmark
    panel = client.get("/comments").text
    assert "verified-row thread" in panel
    assert "verified-row thread" in client.get("/comments?benchmark=verified").text
    assert "verified-row thread" not in client.get("/comments?benchmark=pro").text
    # resolving via the WRONG benchmark row must fail
    r = client.post(f"{P}/nagini/comment/{cid}/status",
                    data={"status": "resolved", "who": "rev1"}, follow_redirects=False)
    assert r.status_code == 400
    r = client.post(f"/verified/nagini/comment/{cid}/status",
                    data={"status": "resolved", "who": "rev1"}, follow_redirects=False)
    assert r.status_code == 303


def test_agent_disabled_403(client):
    r = client.post(f"{P}/nagini/i/{IID}/ask", data={"question": "hi"})
    assert r.status_code == 403


def test_markdown_sanitized(client):
    # a comment with a script tag must be neutralized in render
    client.post(f"{P}/nagini/i/{IID}/comment",
                data={"author": "attacker", "body": "hi <script>alert(1)</script> **bold**"},
                follow_redirects=False)
    t = client.get(f"{P}/nagini/i/{IID}").text
    assert "<script>alert(1)</script>" not in t
    assert "<strong>bold</strong>" in t


def test_multiround_nested_replies(client):
    """Reply-to-a-reply (multiple rounds) must persist and render as a chain."""
    from backend import comments
    root = comments.add_comment("pro", "nagini", IID, "rev1", "Is the empty case pinned?",
                                flag="weak-spec")
    r1 = comments.add_comment("pro", "nagini", IID, "rev2", "Yes — see clause 2.", parent_id=root)
    r2 = comments.add_comment("pro", "nagini", IID, "rev1", "Got it, what about len 1?",
                              parent_id=r1)  # reply to a reply
    comments.add_comment("pro", "nagini", IID, "rev2", "Also covered.", parent_id=r2)
    threads = comments.threads_for("pro", "nagini", IID)
    # find our root and walk the chain depth
    node = next(t for t in threads if t["id"] == root)
    depths = []
    def walk(n):
        depths.append(n["depth"])
        for ch in n["replies"]:
            walk(ch)
    walk(node)
    assert max(depths) >= 3, f"expected a >=3-deep reply chain, got depths {depths}"
    page = client.get(f"{P}/nagini/i/{IID}").text
    for body in ["Is the empty case pinned?", "see clause 2", "what about len 1", "Also covered"]:
        assert body in page


def test_gate_definitions_present(client):
    """Every gate's definition is rendered (hover popover) on the instance page."""
    from backend import data
    t = client.get(f"{P}/nagini/i/{IID}").text
    assert "gate-pop" in t  # the hover popover container
    # G-PBT is a gate and has a definition
    assert "G-PBT" in t
    assert "property-based falsification" in t.lower()
    for g in data.GATE_ORDER:
        assert g in data.GATE_DEFS, f"no definition for {g}"


def test_overview_gate_chips_deliver_the_definition_they_promise(client):
    """Each gate chip on the overview anchors a popover carrying its definition.

    The chips are styled `cursor:help`, so the cursor promises a definition. It
    used to live in `title`, which the browser draws slowly, unstyled, and not at
    all on touch, so the promise read as a dead control. Asserted per chip rather
    than per page: a chip that keeps the cursor and loses the popover fails here.
    """
    import re
    from backend import data
    t = client.get("/").text
    chips = {}
    for block in t.split('class="gkey"')[1:]:      # one block per chip
        m = re.search(r"<code>(G-[A-Z]+)</code>", block)
        assert m, "a chip renders no gate key"
        chips[m.group(1)] = block
    assert set(chips) == set(data.GATE_ORDER), f"chips: {sorted(chips)}"
    for g, block in chips.items():
        assert "gate-pop" in block, f"{g} chip anchors no popover"
        assert data.GATE_DEFS[g][:40] in block, \
            f"{g}: definition is not in the chip's popover"
    css = client.get("/static/app.css").text
    # the anchor is the wrapper, not the <code>: an absolutely positioned popover
    # needs a positioned ancestor, and the cursor belongs on the same element
    assert re.search(r"\.gkey\{[^}]*position:relative", css)
    assert re.search(r"\.gkey\{[^}]*cursor:help", css)
    assert re.search(r"\.gkey:hover \.gate-pop[^{]*\{[^}]*display:block", css)


def test_gate_popover_hidden_by_default(client):
    """The definition popover must be HIDDEN by default and only shown on hover/
    focus — never dumped inline in the badge. Also: the stylesheet link is
    version-stamped so a CSS change is never served stale from cache."""
    import re
    # the css link carries ?v=<mtime> (cache-bust)
    page = client.get(f"{P}/nagini/i/{IID}").text
    assert re.search(r'/static/app\.css\?v=\d+', page), "app.css link must be versioned"
    css = client.get("/static/app.css").text
    m = re.search(r"\.gate-pop\{([^}]*)\}", css)
    assert m, ".gate-pop rule missing"
    default = m.group(1)
    # hidden via display:none (and belt-and-suspenders visibility/opacity)
    assert "display:none" in default and "visibility:hidden" in default
    # revealed only under :hover / :focus
    assert re.search(r"\.gate:hover \.gate-pop[^{]*\{[^}]*display:block", css)
    # no rule reveals the popover ITSELF without hover/focus
    for sel, body in re.findall(r"([^{}]+)\{([^}]*)\}", css):
        s = sel.strip()
        if (re.search(r"\.gate-pop\s*$", s) or re.search(r"\.gate-pop[:,]", s)) \
                and ":hover" not in s and ":focus" not in s:
            assert "display:block" not in body and "visibility:visible" not in body, \
                f"stray rule reveals popover without hover: {s}"


def test_pbt_absent_ok(client):
    """A bundle may have no battery to render — the card simply doesn't render.

    The cell is resolved off the corpus rather than pinned: batteries keep
    landing, so an id pinned for this property stops having it.
    """
    from backend import data
    iid = next((i for i in data.all_instance_ids("pro")
                if data.pbt_result("pro", "nagini", i) is None), None)
    assert iid, "no pro/nagini cell is without a battery"
    assert client.get(f"{P}/nagini/i/{iid}").status_code == 200


def test_prepatch_diff(client):
    """model_prepatch -> model diff is computed and rendered (impl differs, spec same)."""
    from backend import data
    diffs = data.prepatch_diffs(FULL_BM, "nagini", FULL_IID)
    assert diffs, "expected at least one prepatch diff"
    assert any(ln["tag"] in ("add", "del") for d in diffs for ln in d["lines"])
    t = client.get(f"/{FULL_BM}/nagini/i/{FULL_IID}").text
    assert "spec identical" in t  # the model-diff header


def test_repo_file_fragment_has_collapse(client):
    """The expand-full-file fragment includes a collapse control."""
    require_mirror("pro", IID)
    frag = client.get(f"{P}/nagini/i/{IID}/file?path=README.md").text
    assert "collapse" in frag.lower()


def test_status_toggle_scoped_to_backend(client):
    """A thread raised on one board cannot be resolved via another board's route."""
    from backend import comments
    cid = comments.add_comment("pro", "velvet", IID, "rev1", "velvet-only thread")
    r = client.post(f"{P}/nagini/comment/{cid}/status",
                    data={"status": "resolved", "who": "rev1"}, follow_redirects=False)
    assert r.status_code == 400  # wrong board
    r = client.post(f"{P}/velvet/comment/{cid}/status",
                    data={"status": "resolved", "who": "rev1"}, follow_redirects=False)
    assert r.status_code == 303  # right board


def test_reply_cannot_cross_backends(client):
    """A reply's parent must live on the same (backend, instance)."""
    from backend import comments
    import pytest as _pytest
    root = comments.add_comment("pro", "lean", IID, "a", "lean thread")
    with _pytest.raises(ValueError):
        comments.add_comment("pro", "nagini", IID, "b", "cross-board reply", parent_id=root)
    # ...and not across benchmark rows either
    with _pytest.raises(ValueError):
        comments.add_comment("verified", "lean", IID, "b", "cross-row reply", parent_id=root)


def test_reserved_paths_not_shadowed(client):
    """/comments and /healthz must never be eaten by the /{bk}/ route."""
    assert client.get("/comments").status_code == 200
    assert client.get("/healthz").text == "ok"
    assert client.get("/not-a-benchmark/nagini/").status_code in (404, 422)
    # a single-segment path can never reach the 2-segment board route
    assert client.get("/nagini/").status_code in (404, 422)


# ------------------------------------------------------------------ code/template coherence
#
# What these two pin is the one thing a green suite cannot see. `serve.sh` runs ONE
# process, so the filters are whatever they were at startup, while Jinja re-reads a
# template as soon as its mtime moves. A template edit that calls a filter keyword
# the loaded code does not have is then a 500 on every page that renders it -- and
# on disk the pair is consistent, so every test here passes throughout.

def test_the_running_server_renders_the_templates_it_imported():
    """A server must not read half of an edit. Pinned, the template set is the one
    that was on disk when this module was imported -- the same instant as the
    filters it calls and as `static_v` -- so a template can never call a filter
    signature the running code does not have.

    Both halves matter. `auto_reload` off stops a rendered page from being
    re-read, and compiling every template at import stops a page that has not
    been visited yet from being read fresh (and therefore late) the first time
    someone clicks it -- which is exactly the click that broke.
    """
    from backend.app import templates
    env = templates.env
    assert env.auto_reload is False, "a live template edit can outrun the code"
    from backend.app import _pinned_template_names
    on_disk = set(_pinned_template_names(templates))
    # every page this site serves comes from one of these, so an empty set would
    # make the rest of this test pass by testing nothing
    assert {"base.html", "index.html", "instance.html"} <= on_disk, sorted(on_disk)
    compiled = {key[1] for key in env.cache}
    missing = on_disk - compiled
    assert not missing, f"read from disk on first request, not at import: {sorted(missing)}"


def test_a_template_edit_cannot_outrun_the_code_that_renders_it(tmp_path):
    """The mechanism, end to end: an edit that needs a filter keyword the loaded
    code does not have must not reach a running server.

    `shout` here stands in for `md`: the edited template calls it with a keyword,
    exactly as `instance.html` calls `md(fold_prose=...)`, and the filter object in
    the environment is the old one-argument version, exactly as an older process
    holds an older `render.md`. Unpinned that is a TypeError, i.e. a 500. Pinned,
    both renders are the template the server started with. The second template is
    also checked to be a real trap, so this cannot pass by rendering something
    harmless.
    """
    from fastapi.templating import Jinja2Templates
    from backend.app import _pin_templates
    from jinja2 import Environment, FileSystemLoader, select_autoescape
    import os
    import time

    tpl = tmp_path / "page.html"
    tpl.write_text("{{ x | shout }}")
    t = Jinja2Templates(directory=str(tmp_path))
    t.env.filters["shout"] = lambda s: s.upper()      # the OLD signature, no kwargs
    _pin_templates(t)

    assert t.env.get_template("page.html").render(x="a") == "A"

    # the edit: a new call the loaded filter cannot serve
    tpl.write_text("{{ x | shout(loud=True) }}")
    os.utime(tpl, (time.time() + 10, time.time() + 10))   # unambiguously newer

    # it really is a trap -- an env that DOES re-read raises the site's TypeError
    fresh = Environment(loader=FileSystemLoader(str(tmp_path)),
                        autoescape=select_autoescape(["html", "xml"]))
    fresh.filters["shout"] = t.env.filters["shout"]
    with pytest.raises(TypeError, match="unexpected keyword argument 'loud'"):
        fresh.get_template("page.html").render(x="a")

    # ...and the pinned env is untouched by it
    assert t.env.get_template("page.html").render(x="a") == "A"
