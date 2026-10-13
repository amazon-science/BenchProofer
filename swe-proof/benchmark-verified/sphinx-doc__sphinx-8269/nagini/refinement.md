# refinement.md — sphinx-doc__sphinx-8269

The operation-by-operation correspondence between `model.py`'s implementation
(the `classify_fragment_link` impl region plus the live `raise_on_error_status`
axiom) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses the axiom's `Ensures`/`Exsures`, and **A-reference**, where a deep
model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

The patch edits the fragment-checking branch of the nested `check_uri()` in
`sphinx/builders/linkcheck.py`. Gold hunk:

```
                     # Read the whole document and see if #anchor exists
                     response = requests.get(req_url, stream=True, config=self.app.config,
                                             auth=auth_info, **kwargs)
+                    response.raise_for_status()
                     found = check_anchor(response, unquote(anchor))

                     if not found:
```

## A. The fragment-checking branch — `check_uri()` fragment slice (`linkcheck.py:165-172` + dispatch `:186-199`)

| # | model.py impl op (`classify_fragment_link`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `status: int` | `response.status_code` of the `requests.get(...)` response | R | the HTTP status as an `int` (mapping.md §2). The status carries the entire transport outcome the dispatch needs. |
| A2 | `found = fragment_present` (the scanner verdict, read first) | `found = check_anchor(response, unquote(anchor))` | R | `check_anchor`'s `bool` verdict refined to the branch-selector bit `fragment_present` (mapping.md §3.2). UNCHANGED by the patch. Modelling it as evaluated up front is observationally identical: it has no side effect the slice depends on, and post-patch it runs after the gate — the gate decides the outcome before `found` is consulted either way. |
| A3 | `raise_on_error_status(status)` — the ADDED status gate, called BEFORE acting on `found` | `response.raise_for_status()` — **the one added line** | A-consumed | `raise_on_error_status` is the weakest contract on `Response.raise_for_status` the spec needs: it raises `TransportError` exactly on a status in `[400, 600)` and returns normally otherwise (mapping.md §3.1). The proof consumes its `Ensures`/`Exsures` to discharge the postconditions. G-AX confirms it against the real `raise_for_status` (boundary + fuzz). THIS is the changed operation — but the change is *adding a call to an unchanged callee*, so it is an A-consumed axiom about that callee, not a deep model of a changed function. |
| A4 | `if not found: raise FragmentAbsent()` | `if not found: raise Exception(__("Anchor '%s' not found") % anchor)` | R + I | the fragment-absent raise (`Exception` ↔ `FragmentAbsent`, R: user-defined exception stands in for the builtin; mapping.md §2). Identical control flow: reached only when the gate did NOT raise (non-error status) and the fragment is absent. |
| A5 | `except TransportError:` dispatch — `401 → (WORKING, NONE)`, `503 → (IGNORED, TRANSPORT)`, else `→ (FAILED, TRANSPORT)` | `except HTTPError as err:` — `err.response.status_code == 401 → ('working', ' - unauthorized', 0)`, `== 503 → ('ignored', str(err), 0)`, else `→ ('broken', str(err), 0)` | R + I | the shared error-status dispatch (UNCHANGED by the patch). `HTTPError ↔ TransportError` (R); the 401/503/else branching on `status` is the identical concrete decision (the real code reads `err.response.status_code`, the model reads `status` — the same value, mapping.md §2). The model status-class `FAILED` (code 1) refines the repo's `'broken'` string. The tuple `(class, info)` refines to `(status-class, datum-kind)`: `' - unauthorized'`→`DATUM_NONE` on the 401 working path, `str(err)`→`DATUM_TRANSPORT` on the 503/else paths. |
| A6 | `except FragmentAbsent: return (FAILED, FRAGMENT_ABSENT)` | the broad `except Exception as err:` → `'broken', str(err), 0` (with the non-SSL branch) | R + I | the fragment-absent → `FAILED` (repo `'broken'`) path. `str(err)` here is the `Anchor not found` message, refined to `DATUM_FRAGMENT_ABSENT` (mapping.md §2). The SSL-ignored sub-case of `except Exception` is outside the modelled slice (no fragment F2P link is an SSL error). |
| A7 | fall-through `return (WORKING, NONE)` | the success path below the `try` (`response.url...` redirect check → `'working', '', 0` on the no-redirect F2P case) | R + I | reached only when neither the gate nor the fragment raise fired (non-error status AND fragment present). The redirect sub-classification (`'redirected'`) is orthogonal to this change and not exercised by the F2P test (localhost, no redirect); modelled as the working outcome. |
| A8 | `Requires(MustTerminate(2))` on `classify_fragment_link` (and `Requires(MustTerminate(1))` consumed on the axiomatized gate) — the total-correctness obligation | the real fragment branch is a bounded, straight-line computation: `requests.get` returns (or raises, outside the slice), `raise_for_status` is two range checks + return/raise, `check_anchor` is a bounded scan of the fetched document, and each dispatch arm is a single `return` — `check_uri` always DELIVERS its `(status, info, code)` verdict to the worker thread | R | termination is a real, observable property of the modelled slice: a checker that never returns would hang the linkcheck worker and the F2P test would never see its output line. Nagini is a partial-correctness verifier by default, so without the obligation an impl that diverges before returning (`while True: pass`) satisfies every value postcondition vacuously while resolving nothing — the exact spec-admits-wrong-impl hole the G-PANEL-1 audit exploited (atk_4). The obligation adds NO value constraint (every `(status, fragment_present)` input remains admissible) and does not over-constrain the impl shape (the flat-dispatch positive control still verifies); it only forces every loop/callee on the path to the return to carry a decreasing measure, which the loop-free real slice trivially does. |

**A5 version pin.** The three-arm dispatch (401/503/else) is the ENTIRE
`except HTTPError` handler at this instance's `base_commit`
(`1e2ccd8f0eca…`, Sphinx 3.3.0, 2020-10-03): the repo has no `429` branch, no
`limit_rate`, and no `'rate-limited'` status — `git grep -E
'limit_rate|rate-limited|next_check|DEFAULT_DELAY' -- sphinx/` at that commit
returns nothing (verify in the worktree; do not rely on memory of later
Sphinx). A 429 response falls into the `else` arm: `('broken', str(err), 0)` =
the model's `(FAILED, DATUM_TRANSPORT)`. The linkcheck rate-limiting feature
was introduced in Sphinx 3.4 (Dec 2020) and post-dates this instance; at this
commit `linkcheck.py:200-211` is the redirect handling.

The discriminating content of the change: pre-patch the fragment branch reached
`check_anchor` and the `Anchor not found` raise **without** ever calling
`raise_for_status`, so an error-status response with the fragment absent (the
F2P scenario: a localhost server returning 500) was reported as
`broken` with the `Anchor 'anchor' not found` datum. Post-patch the added
`raise_for_status()` raises `HTTPError` first, so the shared `except HTTPError`
dispatch reports `broken` with the `500 Server Error: ...` transport datum —
exactly the F2P assertion.

`model_prepatch.py` reproduces the pre-patch skeleton (the status gate
`raise_on_error_status(status)` is **removed** from the fragment branch, so the
`except TransportError` dispatch is unreachable) and **fails** verification: the
verifier reports `Postcondition ... Implies((status == 401), (Result() ==
(WORKING(), DATUM_NONE()))) might not hold` — for `status == 401` with
`fragment_present == False`, the pre-patch returns `(FAILED,
FRAGMENT_ABSENT)` instead of the required `(WORKING, NONE)`, because the
401 special-case lived only inside the now-unreachable `HTTPError` handler.
The same failure underlies clauses (2), (3), and (5) (503, the general
error-status → transport datum, and the no-fragment-absent-datum invariant);
Nagini reports the first. That is exactly the spec sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The operation that genuinely *changed* — adding
`response.raise_for_status()` to the fragment branch — is modelled as the
explicit `raise_on_error_status(status)` call (A3), an **A-consumed** axiom about
the **unchanged** `Response.raise_for_status` callee the new line invokes. There
is no deep model of a changed function and therefore no **A-reference**: the
changed delta is a new *call site* to an existing routine, which is exactly what
an A-consumed axiom captures. The axiom's `Ensures`/`Exsures` are consumed by
`classify_fragment_link`'s postconditions (clauses 3 and 5 are dischargeable
only because the gate raises on `[400,600)` before the fragment scan). No dead
axiom — but note the precise mechanism: removing the axiom's `Exsures` does
NOT make the gold proof fail; it makes the error-status obligations hold
*vacuously* (with no declared exceptional postcondition the verifier treats
the call as non-raising, and the normal-completion `Ensures(status < 400 or
status >= 600)` then renders the post-call state infeasible on any error
status — empirically, the gold impl with the `Exsures` deleted still
verifies, and so does a deliberately wrong 500→IGNORED dispatch). The
`Exsures` is consumed the other way around: it is what makes the `except
TransportError` handler REACHABLE and its 401/503/else dispatch actually
constrained by clauses (1)–(3)/(5). With the `Exsures` present (the frozen
spec), wrong-dispatch implementations fail verification (G-PBT's
`partial-drop-401`/`partial-drop-503`/`wrong-error-datum` cases and the
audit's boundary/control-flow attacks are rejected exactly because of it), so
the axiom's exceptional clause is the load-bearing source of the spec's
discriminating power over the error-status arm.

## C. verify(model) ⇒ resolved

`classify_fragment_link` verifies only if (a) on an error status it dispatches
EXACTLY as the shared `HTTPError` handler does — 401→working, 503→ignored,
else→broken-with-transport-datum (A5), reachable only because the gate raises
first (A3) — (b) on a non-error status it defers to the fragment verdict
(A4, A7), and (c) it actually TERMINATES and returns that classification
(A8: the `MustTerminate` obligation closes the vacuous-divergence hole — an
impl that spins forever satisfies the value clauses only vacuously and its
faithful real patch hangs the checker thread, failing the F2P test by
timeout). By R (`status_code` ↔ `status`, `check_anchor` verdict ↔
`fragment_present`, `HTTPError` ↔ `TransportError`, `Exception` ↔
`FragmentAbsent`, the `(status, info, code)` tuple ↔ `(class, datum)`) the
verified slice equals the gold `check_uri` fragment branch with the added
`response.raise_for_status()`; by G-AX the real `Response.raise_for_status`
meets the `raise_on_error_status` axiom (A-consumed). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the one audited callee — and the gold patch resolves
(G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom soundness
(G-AX) and refinement fidelity (this document, G-EQ).
