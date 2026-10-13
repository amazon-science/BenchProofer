# mapping.md — sphinx-doc__sphinx-8475

## Symbol binding (file:line @ base_commit 3ea1ec84cc610f7a9f4f6b354e264565254923ff)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_probeUri` / `problem_spec_probeUri` | the HEAD-probe → GET-fallback block inside `CheckExternalLinksBuilder.check_uri` | `sphinx/builders/linkcheck.py:166-179` |
| `retryWithFull` (pure helper) | the `except (HTTPError, TooManyRedirects):` retry decision (post-patch) | `sphinx/builders/linkcheck.py:174` |
| `ReqOutcome` (pure type) | the observable result/exception classes of a `requests` call: a usable response, `requests.exceptions.HTTPError`, `requests.exceptions.TooManyRedirects`, any other exception | `sphinx/builders/linkcheck.py:20`, `requests.exceptions` |

The modeled fragment is the non-anchor probe path of `check_uri`: a HEAD request
is attempted first, and on a *retryable* failure the check retries with a GET
request, reporting that request's outcome. This is the only behavior the gold
patch changes and the only behavior the FAIL_TO_PASS test
(`test_TooManyRedirects_on_HEAD`) observes.

### What the modeled fragment does (base_commit)

```python
else:
    try:
        # try a HEAD request first, which should be easier on
        # the server and the network
        response = requests.head(req_url, allow_redirects=True,
                                 config=self.app.config, auth=auth_info, **kwargs)
        response.raise_for_status()
    except HTTPError:                       # base_commit: only HTTPError
        # retry with GET request if that fails, some servers
        # don't like HEAD requests.
        response = requests.get(req_url, stream=True, config=self.app.config,
                                auth=auth_info, **kwargs)
        response.raise_for_status()
```

- `requests.head(...)` followed by `raise_for_status()` is the lightweight probe.
  Its outcome is one of: success (no exception), `HTTPError` (an error status),
  `TooManyRedirects` (the server kept redirecting — `allow_redirects=True` and the
  redirect cap was exceeded), or any other exception (connection/TLS/etc.).
- At base_commit, ONLY `HTTPError` triggers the GET fallback. A `TooManyRedirects`
  raised by the HEAD probe escapes this inner `try` and propagates to the outer
  handler, where it is classified `broken` — the bug the issue reports (an
  infinite-redirect-on-HEAD server makes the link be reported broken even though a
  GET would succeed).
- Post-patch, the `except` clause is `(HTTPError, TooManyRedirects)`, so a redirect
  loop on the HEAD probe also falls back to GET. The fallback GET's own outcome is
  what survives (it may itself succeed, raise `HTTPError`, etc.).

The surrounding control flow downstream of this block (the outer `except
HTTPError` status-code classification, the `redirected`/`working` decision on
`response.url`) is UNCHANGED by the patch and is driven entirely by the surviving
`response`; we therefore model the fragment as the function that selects which
probe's outcome survives. Both the lightweight outcome and the fallback outcome
are INPUTS to this function (they are determined by the network), so neither is an
axiomatized callee — see "Callee provenance".

## Lean ↔ Python type bijection (used by G-CONF and G-AX)

| Python | Lean | bijection |
|---|---|---|
| outcome of a single `requests.{head,get}(...)` + `raise_for_status()` | `ReqOutcome` | `ok` ↔ no exception (a usable response); `statusError` ↔ `requests.exceptions.HTTPError`; `redirectLoop` ↔ `requests.exceptions.TooManyRedirects`; `otherFailure` ↔ any other exception (connection error, TLS error, the anchor-not-found `Exception`, …). |
| the HEAD probe outcome | `light : ReqOutcome` | the outcome of `requests.head(...)` + `raise_for_status()`. |
| the GET fallback outcome | `full : ReqOutcome` | the outcome of `requests.get(...)` + `raise_for_status()` performed in the `except` body. |
| `except (HTTPError, TooManyRedirects):` (post-patch) — does this exception trigger the GET retry? | `retryWithFull light : Bool` | `true` iff `light ∈ {statusError, redirectLoop}`; `false` otherwise (success or any other exception type, which is NOT caught by this clause and propagates). |
| the `response` variable that survives the block and is read downstream | `result : ReqOutcome` | `full` when the HEAD outcome is caught by the retry clause; `light` otherwise. |

Note: when `light` is `otherFailure` (not caught) or `ok`, no GET is performed and
`result = light`. The model carries `full` as a separate input regardless; it is
only *selected* when `retryWithFull light = true`, matching the Python (the GET is
only executed inside the `except` body), so the value of `full` is immaterial in
the non-retry case — exactly as `problem_spec_probeUri` states.

## Callee provenance + flag dependencies

- **`light`, `full` — INPUTS, not callees.** The two `requests` calls produce the
  network outcomes; they are environmental inputs to the decision, modeled as the
  function's arguments. There is no unchanged pure callee to axiomatize: the patch
  changes the *control-flow decision* (which exception types retry), not a callee.
  Hence the `axioms` region declares no `opaque`/`axiom` (no `_prop` consumed).
- **`retryWithFull` — the changed decision, modeled deeply (R/I).** This is the
  operation the patch edits (`except HTTPError` → `except (HTTPError,
  TooManyRedirects)`). Modeled structurally by case analysis on `ReqOutcome` —
  NEVER axiomatized (SPEC_GUIDE §3). G-CONF differential-tests it.
- **Flag dependencies.** The probe path modeled here is the `else` branch of `if
  anchor and self.app.config.linkcheck_anchors`. The anchor branch (which issues a
  GET directly and never uses the HEAD→GET fallback) is a separate path and is not
  the behavior under spec; the patch does not touch it. `allow_redirects=True` on
  the HEAD request is what makes `TooManyRedirects` reachable on the probe (a
  redirect loop). No other configuration flag affects the retry decision.

## G-CONF fuzz seed

Pinned LCG seed: **8475** (see `conformance_check.py` `SEED`). Corpus: all
`(light, full)` pairs over the 4×4 `ReqOutcome` enum exhaustively, plus ≥1e5
fuzzed pairs, diffed against an in-process replica of the post-patch retry
decision (`except (HTTPError, TooManyRedirects)`). G-AX is a skip stub (no
consumed axiom; the only deep model `retryWithFull` is a pure control-flow
decision over the bijected outcome enum, exercised exhaustively by G-CONF).
