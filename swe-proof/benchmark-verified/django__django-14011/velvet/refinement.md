# refinement.md — django__django-14011

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `installPreferred` and `releaseAll` `do` blocks and the `releasedSeq` deep
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement; state the bijection), **A-consumed** (proof uses an axiom's
`ensures`), **A-reference** (deep model validated == real callee by G-AX), or
**I** (identical concrete op). EVERY step is R, A, or I — no kind-3
(inexpressible changed op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the A legs and this narrative are audited by **G-EQ** / **G-AX**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## Site A.1 — install preferred connections (`process_request_thread`)

Gold hunk (`django/core/servers/basehttp.py`, post-patch):
```python
def process_request_thread(self, request, client_address):
    if self.connections_override:
        for alias, conn in self.connections_override.items():
            connections[alias] = conn
    super().process_request_thread(request, client_address)
```

Modeled by `installPreferred (preferred registry : List (String × Int))`.

| # | Solution.lean impl op (`installPreferred`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `preferred : List (String × Int)` | `self.connections_override` (a dict `alias↦conn`) | R | dict ↔ assoc-list, conn ↔ `id(conn)` (mapping.md §2). The method *consuming* this param is the model of the constructor accepting/storing `connections_override=`. |
| A2 | param `registry : List (String × Int)` | the live `django.db.connections` registry the worker sees before install | R | `ConnectionHandler` ↔ assoc-list with first-match lookup (mapping.md §2). |
| A3 | backward `while` loop prepending each `preferred[i-1]` onto `registry`, result `= preferred ++ registry` | `for alias, conn in self.connections_override.items(): connections[alias] = conn` | I + A-reference | the install loop is transliterated concretely (the `++`/cons fold ops are **I**, refuted by G-CONF); the claim that the override-precedence merge equals the real `__setitem__`/`__getitem__` post-state is the **A-reference** G-AX validates (mapping.md §3.1). No consumed axiom. |
| A4 | `ensures out = preferred ++ registry` (override precedence); `ensures ∀ p ∈ preferred, p ∈ out` | the net effect: every overridden alias now resolves to the parent's conn; others unchanged | I | the discriminating postcondition; pins that the worker resolves overridden aliases to the supplied connections rather than fresh ones (mapping.md §5). |
| A5 | `super().process_request_thread(...)` (the actual request handling) | same call | (refinement frame) | unchanged framework dispatch; not a data op — it is the I-leg sequencing (mapping.md §0). The model omits it as it carries no observable data-carrier postcondition. |

Discriminating content: with the install reverted, `out = registry` (worker
keeps its own bindings ⇒ for in-memory sqlite, a *fresh empty DB*).
`Solution_prepatch.lean` reproduces that and **fails** on
`out = preferred ++ registry` and `out.length = preferred.length +
registry.length` and `∀ p ∈ preferred, p ∈ out` (G-DIFF), matching the real
DB-visibility F2P failures.

## Site A.2 — release all connections (`close_request` / `_close_connections`)

Gold hunk (`django/core/servers/basehttp.py`, post-patch):
```python
def _close_connections(self):
    connections.close_all()

def close_request(self, request):
    self._close_connections()
    super().close_request(request)
```

Modeled by `releaseAll (handles : List Bool)`.

| # | Solution.lean impl op (`releaseAll`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | param `handles : List Bool` (each conn's open/closed state) | the live registry `connections` at request end | R | registry ↔ `List Bool` of `(conn.connection is not None)` (mapping.md §2). |
| B2 | backward `while` loop emitting `false` for each handle, result `= releasedSeq handles` | `connections.close_all()` (iterates, calls `conn.close()` on each) | I + A-reference | the release fold is transliterated concretely (**I**, refuted by G-CONF); the claim that "after `close_all`, every connection is closed" == `releasedSeq` is the **A-reference** G-AX validates (mapping.md §3.2). No consumed axiom. |
| B3 | `ensures ∀ b ∈ out, b = false`; `ensures out = releasedSeq handles` | net effect: no connection left open after the request | I | the discriminating postcondition; pins universal release so teardown sees no still-held connection (the #22414 fix). |
| B4 | `super().close_request(request)` (socket teardown) | same call | (refinement frame) | unchanged framework dispatch; the I-leg sequencing, no data-carrier postcondition (mapping.md §0). |

Discriminating content: with release reverted, `out = handles` (states
unchanged). `Solution_prepatch_2.lean` reproduces that (base has no
`close_request` override) and **fails** on `∀ b ∈ out, b = false` and
`out = releasedSeq handles` (G-DIFF).

## C. Site B — `django_test_skips` (no modeled method; not kind-3)

Gold hunk (`django/db/backends/sqlite3/features.py`): one test-name string added
to the `django_test_skips` dict. This is a **declarative test-skip datum**, not
a computation over any input carrier: it changes only *which* tests the eval
harness runs, and the test it skips
(`...LiveServerTestCloseConnectionTest.test_closes_connections`) is **not** in
FAIL_TO_PASS. It therefore carries no behavior expressible as a grounded
postcondition and is intentionally not modeled as a `method` (modeling it would
be vacuous — SPEC_GUIDE §0.4/§0.8). It is reproduced verbatim in `patch.diff` so
the harness resolves (G-RESOLVE). This is NOT a kind-3 "inexpressible changed
op": it is a data-free configuration edit, not an algorithm we hide behind an
axiom.

## D. No kind-3 steps

Every modeled step is R, A-reference, or I. The two operations that genuinely
*changed behavior* — installing override connections and releasing all
connections — are modeled **deeply and concretely** (the spelled-out `++`/cons
merge and the `releasedSeq` release fold), not hidden behind an axiom about the
function under change. The only A-tags are **A-reference** deep models of
**unchanged** callees (`ConnectionHandler.__setitem__`/`__getitem__` and
`close_all`), validated == the real callee by G-AX. There are **no consumed
axioms**.

## E. verify(Solution) ⇒ resolved

`installPreferred` verifies only if its output is the override-precedence merge
`preferred ++ registry` (A3/A4); `releaseAll` verifies only if every handle ends
released (B2/B3). By R (`ConnectionHandler` ↔ assoc-list/`List Bool`, conn ↔
`id`/`Bool` state) these equal, respectively, the real post-install registry
(every overridden alias resolves to the supplied conn) and the real post-`close_all`
registry (every conn closed). By G-AX the deep models equal the real unchanged
callees (A-reference); by G-CONF the R/I transliteration agrees with patch.diff
behaviour on ≥10⁵ inputs. Therefore a model satisfying this spec, refined by the
map above and combined with the verbatim Site-B skip datum, is the gold patch up
to type refinement and audited callees — and the gold patch resolves
(G-RESOLVE). Trust points: refinement fidelity (this doc, G-EQ + G-CONF) and
A-reference soundness (G-AX). There are no consumed axioms to trust.
