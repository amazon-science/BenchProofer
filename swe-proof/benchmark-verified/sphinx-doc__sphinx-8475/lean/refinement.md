# refinement.md — sphinx-doc__sphinx-8475

Maps every operation in `implementation_probeUri` to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX), **I**
(identical concrete op). Every step is R, A, or I.

## Modeled function: `probeUri` (HEAD-probe → GET-fallback block of `check_uri`)

Post-patch repo code (`patch.diff`, `sphinx/builders/linkcheck.py:166-179`):
```python
try:
    # try a HEAD request first, which should be easier on the server/network
    response = requests.head(req_url, allow_redirects=True,
                             config=self.app.config, auth=auth_info, **kwargs)
    response.raise_for_status()
except (HTTPError, TooManyRedirects):       # patch: added TooManyRedirects
    # retry with GET request if that fails, some servers don't like HEAD requests.
    response = requests.get(req_url, stream=True, config=self.app.config,
                            auth=auth_info, **kwargs)
    response.raise_for_status()
# `response` flows downstream unchanged
```

Lean impl (`implementation_probeUri`):
```lean
def implementation_probeUri (light full : ReqOutcome) : ReqOutcome :=
  Id.run do
    let mut response := light
    if retryWithFull light then
      response := full
    return response
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `light : ReqOutcome` | outcome of `requests.head(...)` + `raise_for_status()` | **R** | the lightweight-probe result class ↔ the `ReqOutcome` enum (mapping.md bijection: `ok`/`statusError`/`redirectLoop`/`otherFailure`). An environmental input, not a callee. |
| 2 | `full : ReqOutcome` | outcome of `requests.get(...)` + `raise_for_status()` in the `except` body | **R** | the fallback-request result class ↔ `ReqOutcome`. Same bijection. An environmental input; only *read* when the retry fires, matching that the GET only executes inside the `except` body. |
| 3 | result `: ReqOutcome` | the `response` variable that survives the `try/except` and flows downstream | **R** | the surviving response ↔ `ReqOutcome`. The downstream classification (`raise_for_status`/status-code handling, `redirected`/`working`) is UNCHANGED by the patch and is a pure function of this surviving outcome, so modeling which outcome survives captures the full observable effect of the edited block. |
| 4 | `let mut response := light` | `response = requests.head(...); response.raise_for_status()` establishes `response` as the HEAD outcome before the `except` | **I** | initial value of the surviving response is the lightweight outcome. |
| 5 | `if retryWithFull light then response := full` | `except (HTTPError, TooManyRedirects): response = requests.get(...); response.raise_for_status()` | **I** (deep model of the changed op) | **the fixed operation.** `retryWithFull light` is `true` iff `light ∈ {statusError, redirectLoop}` — exactly the post-patch `except (HTTPError, TooManyRedirects)` clause (`HTTPError` ↔ `statusError`, `TooManyRedirects` ↔ `redirectLoop`). This is the line the patch edits (`except HTTPError` → `except (HTTPError, TooManyRedirects)`); modeled deeply, never axiomatized (SPEC_GUIDE §3). On retry the surviving response becomes the GET outcome `full`. G-CONF differential-tests it. |
| 6 | `return response` | `response` flows out of the block | **I** | the surviving outcome (`full` if retried, else `light`). |

The impl region contains **R/I ops only** and NO consumed axiom, so
`conf_skip = false`: `conformance_check.py` differential-tests the R/I retry leg
against an in-process replica of the post-patch `except (HTTPError,
TooManyRedirects)` decision.

## Soundness check (verify ⟹ correct)

- `problem_spec_probeUri light full result` pins the outcome EXACTLY for every
  `(light, full)` pair: `result = if retryWithFull light then full else light`.
  Directive 5 (frame): the result is fully determined — there is no unconstrained
  output component. Directive 8: the postcondition is grounded in the inputs via
  the structural decision `retryWithFull` over the bijected outcome enum, not an
  opaque oracle; the result must be *produced by* selecting one of the two input
  outcomes according to the modeled retry decision.
- The prepatch impl retries only on `statusError` (its selector is `match light
  with | statusError => true | _ => false`, i.e. base_commit `except HTTPError`).
  It violates the spec on the discriminating clause: `light = redirectLoop`,
  `full = ok`, where `retryWithFull light = true` so the spec requires `result =
  full = ok`, but the prepatch does not retry and returns `result = light =
  redirectLoop`. Its carried gold proof cannot close (G-DIFF/G-PANEL).
- This discriminating case is exactly the FAIL_TO_PASS test
  `test_TooManyRedirects_on_HEAD`: the HEAD handler returns an infinite 302
  redirect to itself, so the HEAD probe raises `TooManyRedirects`
  (`redirectLoop`), while the GET handler returns `200 OK` (`full = ok`).
  Post-patch the retry fires and the link is reported `working` (`info=""`);
  base_commit propagated the `TooManyRedirects` to the outer handler and reported
  the link `broken`.
- The PASS_TO_PASS tests `test_follows_redirects_on_HEAD` /
  `test_follows_redirects_on_GET` exercise *finite* redirects (no loop), where the
  HEAD probe succeeds (`light = ok`, `retryWithFull = false`, no retry) — preserved
  identically by both impls. `test_raises_for_invalid_status` exercises
  `light = statusError` (retry fires in both impls). The retry behavior on those
  outcomes is unchanged, matching the spec.

## Why no axiom

The patch changes a control-flow *decision*, not a callee. The two network
outcomes are inputs (`light`, `full`); the decision (`retryWithFull`) is modeled
deeply as a total function over the 4-constructor `ReqOutcome` enum. There is no
unchanged pure callee whose property the proof must consume, so the `axioms`
region is empty and `axiom_check.py` is a skip stub (G-AX = skip). G-CONF is the
primary and exhaustive differential for the modeled decision.
