# Review site (`viz/`)

A read-only review UI for the constructed bundles, covering the whole
**benchmark x backend matrix** from one server. `/` is an overview of the corpora
and the gate suite, every figure on it measured from the corpus being served;
the bundles themselves are under `/{benchmark}/{backend}/...`, and the header
chooser is a matrix with one row per
benchmark and one cell per backend, each showing that cell's fully-green count,
plus a totals column holding the row's instance count. Every number in it is a
drill-down link: a backend cell opens that cell's board, the total opens the
row's whole (unfiltered) instance list.
Switching *backend* keeps you on the same instance (ids are shared across
backends within a benchmark); switching *benchmark* goes to that row's index,
because the benchmarks have disjoint instance sets. Model naming (`model.py` vs
`Solution.lean`), highlighting, and labels adapt per backend; comments live in one
database tagged by `(benchmark, backend)`.

It exists because a bundle is an argument and the gates only decide the parts that
are mechanical. Whether a spec is *faithful* to the real callee, or whether it
*discloses* the fix, is a judgment a person has to be able to make quickly over
hundreds of instances, which means reading the spec, the real code at
`base_commit`, and the gate notes side by side. This is that reading surface. It
never modifies a dataset (`benchmark-*/`, `repos*/`); the only writable state is
the comments database at `viz/data/review.sqlite` (untracked).

Every loader takes the benchmark key as its first argument
(`data.summary_table(bm, bk)`, `paths.bench_root(bm)`), so no module-level state
decides which dataset a request reads. The two axes come from different places.
The **columns** are the backends of `swebench_unified.backends.registry`, which is
the authoritative list: the site adds only the presentation of them
(`BACKEND_LABELS` and `_BACKEND_MODEL`, which hold the pre-patch stem, extension
and fence language, in `viz/backend/settings.py`), and splits them into the matrix and the
set-apart boxes by whether the release gate covers them. The **rows** are the
`BENCHMARK_DEFS` entries in the same file (bundle root, mirror root, label), each
with a pair of directory variables overriding it, and `VIZ_BENCHMARKS` selects
which of them to serve.

## What it shows (per instance)

- The issue (`problem_statement`), with `hints_text` clearly marked *not
  solver-visible*.
- The gold **patch with surrounding context**, an **expand-full-file** button
  (with a **✕ collapse** to close it again), and a **browse-the-repo-at-base_commit**
  file tree (open any file at that commit to trace callees, tests and context,
  and close it with ✕ collapse), so a reviewer can check a spec against the real code
  rather than trusting the patch hunk in isolation.
- The **formal model** vs the **pre-patch twin** (the same spec with the bug)
  shown as a **highlighted diff**. The spec regions are byte-identical by
  construction, so the diff isolates exactly the implementation change that fixes
  the bug.
- The **equivalence** argument (`refinement.md` / `mapping.md` /
  `axiom_check.py`), the **13 gate** badges (**hover/focus any badge for its
  definition and this instance's recorded note**), and the **audit verdicts** from
  `meta.json` (the G-EQ detail plus each G-PANEL role's verdict and notes).
- **G-PBT property-based falsification**: the adversarial battery
  (`properties.py`) and its per-case result (`pbt_result.json`): a verdict pill
  plus a table of every spec-lane and axiom-lane case (kind / expect / outcome).
- **Metadata**: modeled functions, axioms, deep refs, the test sets.
- Every instance in the row is listed, including blocked / parked / never-built,
  with a construction-status column (ok / blocked / timeout / missing) and a
  **fully-green** pill. Index filters: fully-green / non-green / ok / blocked /
  timeout.
- **Comments & flags** (Markdown, sanitized), **off by default**: flag a weak
  spec / imprecise axiom / leakage / faithfulness issue; **reply to any comment to
  any depth** (full multi-round threads); mark resolved or reopen. There is no
  admin role, so any reviewer can moderate, and a site-wide `/comments` page lists
  every thread. It is the only part of the site that writes, so a published copy
  cannot serve it; `VIZ_COMMENTS_ENABLED=1` turns the form, the threads and
  `/comments` on for a reviewing deployment.
- **Ask an agent** (read-only, **multi-turn**): a tool-use loop that can read the
  bundle, the repo at `base_commit`, the verdict, and the metadata, with the
  conversation preserved across turns. Every tool is read-only and path-guarded to
  the benchmark's bundle and mirror roots; the agent cannot write anything.
  It is **off by default**, because it is the one feature that reaches off the
  machine: with it off a sidebar footnote says so and names `VIZ_AGENT_ENABLED=1`,
  which enables it and calls Bedrock on the host's own credentials.

## Install (Python only)

```bash
pip install -e ".[viz]"        # from the repo root; see the viz extra in pyproject.toml
```

No npm or system packages. htmx and the Pygments stylesheet are not shipped:
`bash scripts/fetch_vendor.sh viz` puts them in `viz/static/vendor/` (see below). The agent feature uses your provider's ambient credentials.

### Prerequisite: the repo mirrors

The bundle roots (`benchmark-verified/`, `benchmark-pro/`) are in the repository,
but the **source mirrors** the site reads `base_commit` from are not: `repos/` and
`repos-pro/` are untracked, so a fresh clone has neither. Without them the site
still serves every page, and the browse-the-repo tree, the expand-full-file button
and the patch's surrounding context degrade to an error line. Build them once:

```bash
python scripts/setup_repos.py                                    # -> repos/     (Verified)
SBU_BENCHMARK=swe_bench_pro_python SBU_REPOS_ROOT="$PWD/repos-pro" \
  python scripts/setup_repos.py                                  # -> repos-pro/ (Pro)
```

If you already have clones elsewhere, point `VIZ_VERIFIED_REPOS` / `VIZ_REPOS_DIR`
at them instead of copying. The mirrors are a test input as well as a serving one:
the tests that read a real commit out of one (`test_app.py::test_repo_browse`, and
`file_at_base` / `tree_at_base` / `mirror_for` in `test_data_layer.py`) skip with
that message when no mirror is present, so a fresh checkout is green before the
download and those properties are simply unmeasured until it happens.

### Point it at your own corpus

Nothing about the site is specific to the two shipped rows. To serve one corpus of
your own, give it a bundle root and (optionally) a mirror root, and name the row:

```bash
VIZ_BENCHMARKS=pro VIZ_BENCHMARK_DIR=/path/to/your/bundles \
  VIZ_REPOS_DIR=/path/to/your/clones bash viz/serve.sh
```

`VIZ_BENCHMARKS` is what makes the chooser one row instead of two, so an
unpopulated row never appears as a line of zeros. The bundle root needs the layout
the loaders expect, which is what the construction pipeline writes:
`<root>/<instance_id>/` holding the immutable inputs (`instance.json`,
`patch.diff`) and `<root>/<instance_id>/<backend>/` holding that backend's
`meta.json`, `verdict.md` and model files.

### Serve a corpus ALONGSIDE the shipped rows

Reusing a shipped row's variables replaces that row. To add a row instead, declare
it in a JSON file and name it in `VIZ_BENCHMARK_SPEC` -- the review-site half of
the construction side's `SBU_BENCHMARK_SPEC`, so a third benchmark is a file on
both sides rather than an edit here:

```bash
cat > /tmp/live-row.json <<'JSON'
{"key": "live", "dir": "/path/to/benchmark-live", "repos": "/path/to/repos-live",
 "label": "SWE-bench-Live"}
JSON
VIZ_BENCHMARK_SPEC=/tmp/live-row.json bash viz/serve.sh   # -> /live/nagini/...
```

`key` becomes the URL prefix and the comments-DB benchmark column, so reusing a
built-in key is refused rather than silently attaching that corpus's review
history to the new row. One file may hold a list (or `{"benchmarks": [...]}`), and
`VIZ_BENCHMARK_SPEC` takes several paths separated by `:`.

### Vendored third-party assets

The release redistributes no third-party code, so these two files are fetched,
not shipped: `bash scripts/fetch_vendor.sh viz` (from the repo root) downloads
htmx at its pin and checks it against a pinned sha256, and generates the
stylesheet with the installed Pygments. The site serves them unmodified from
`viz/static/vendor/`, which git ignores:

| file | version | upstream | license |
|---|---|---|---|
| `htmx.min.js` | 2.0.4, from `unpkg.com/htmx.org@2.0.4/dist/htmx.min.js` | [htmx](https://htmx.org) | 0BSD (Zero-Clause BSD) |
| `pygments.css` | generated by whichever Pygments the `viz` extra installed (developed against 2.20.0) | [Pygments](https://pygments.org) | BSD-2-Clause |

The stylesheet is the `default` style's HTML class definitions,
`HtmlFormatter(style="default").get_style_defs(".highlight")`, so rerun the script
rather than hand-editing it.

## Run

```bash
bash viz/serve.sh              # binds 127.0.0.1:9000 ONLY (override with VIZ_PORT)
```

It refuses to bind a non-loopback interface unless `VIZ_ALLOW_PUBLIC=1`. That
default is the point: the site renders unpublished artifacts and accepts comments
with no authentication of its own, so it is written to be reachable only by
someone who already has shell access to the host. `serve.sh` does not depend on
an activated environment, so it can be launched from any shell; point
`VIZ_PYTHON` at the interpreter holding the `viz` extra if it is not the one on
`PATH`.

To read it from another machine, forward the port over SSH rather than binding a
public interface:

```bash
HOST=user@your-host bash viz/connect.sh   # ssh -N -L 8080:127.0.0.1:9000
# open http://localhost:8080
```

`HOST` is any destination `ssh` accepts, so a jump through a bastion belongs in
your `~/.ssh/config` as a `ProxyJump` on that alias.

## Settings (env)

| var | default | meaning |
|---|---|---|
| `VIZ_PORT` | 9000 | port to serve on (loopback) |
| `VIZ_HOST` | 127.0.0.1 | bind addr (anything else needs `VIZ_ALLOW_PUBLIC=1`) |
| `VIZ_PYTHON` | python on `PATH` | interpreter that has the `viz` extra |
| `VIZ_COMMENTS_ENABLED` | 0 | enable the comment form and `/comments` (the only writable surface; a published static copy has no server to write with) |
| `VIZ_AGENT_ENABLED` | 0 | enable the ask-an-agent feature (needs Bedrock credentials on the host) |
| `VIZ_BEDROCK_MODEL` / `VIZ_BEDROCK_REGION` | see `settings.py` | model id and region for the agent |
| `VIZ_AGENT_RATE_PER_MIN` | 30 | per-minute cap on agent calls |
| `VIZ_MAINTAINERS` | `maintainer` | comma-separated comment authors whose threads get the maintainer accent |
| `VIZ_BENCHMARKS` | every `BENCHMARK_DEFS` key | comma-separated subset of the rows to serve |
| `VIZ_BENCHMARK_SPEC` | unset | `:`-separated JSON files declaring EXTRA rows (`key` / `dir` / `repos` / `label`) |
| `VIZ_BENCHMARK` / `VIZ_BACKEND` | `verified` / `nagini` | the matrix cell the overview page and the header's fallback links point at |
| `VIZ_BENCHMARK_DIR` / `VIZ_REPOS_DIR` | `benchmark-pro` / `repos-pro` | the Pro row's bundle and mirror roots |
| `VIZ_VERIFIED_DIR` / `VIZ_VERIFIED_REPOS` | `benchmark-verified` / `repos` | the Verified row's bundle and mirror roots |

## Move the comments through git

`viz/data/review.sqlite` is operational state and is untracked, so review history
travels as a committed JSON file and comes back out of it:

```bash
python viz/export_comments.py        # DB   -> viz/review_comments.json, then commit it
python viz/export_comments.py --load # JSON -> DB, for a reader who just cloned
```

The load ADDS: a comment already in the database is left alone (identity is
benchmark + backend + instance + author + timestamp, since the `id` in a snapshot
is the exporting database's), so it is safe on a database that already carries
local review, and running it twice changes nothing.

## Tests

```bash
pip install -e ".[viz,dev]"                   # the route tests need httpx (dev extra)
python -m pytest viz/tests -q                 # data layer, routes, comments, agent tools
VIZ_LIVE_AGENT=1 python -m pytest viz/tests/test_agent_tools.py::test_live_agent  # one live call
```

Both run from the repo root; `python -m pytest tests/` does not reach `viz/tests`.

The second line is the only test that reaches a model; the rest run offline.
Serving the site needs `.[viz]` alone; `starlette`'s `TestClient` is what pulls
in `httpx`, so it is a test-time dependency rather than a runtime one.

## Layout

```
viz/backend/   app.py · data.py · repo.py · patchview.py · render.py
               comments.py · agent.py · settings.py · paths.py
viz/templates/ base · index · instance · comments · _macros · _threads · _file · _tree · _answer
viz/static/    app.css · vendor/{htmx.min.js, pygments.css} (fetched, untracked)
viz/data/      review.sqlite (untracked)
viz/tests/     test_data_layer · test_app · test_backends · test_agent_tools · test_render
viz/serve.sh   viz/connect.sh   viz/export_comments.py
```

One note for anyone touching the fully-green pill: it is not computed here. Both it
and the release gate call `swebench_unified.greenness`, so a badge cannot disagree
with which cells `scripts/green_check.py` accepts. The criterion behind that
predicate is stated once in prose, in section 8 of
[../docs/architecture.md](../docs/architecture.md).
