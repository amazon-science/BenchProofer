# refinement.md — django__django-13406

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`assignQuery` `do` block) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement; state the bijection), **A-consumed** (proof uses an
axiom's `ensures`), **A-reference** (deep model validated == real callee by
G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The setter site — `QuerySet.query` setter (`django/db/models/query.py:210`)

Gold hunk:
```
     @query.setter
     def query(self, value):
+        if value.values_select:
+            self._iterable_class = ValuesIterable
         self._query = value
```

| # | Solution.lean impl op (`assignQuery`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `incoming : Query`, observed via `projectsColumns incoming` | `value` arg; `value.values_select` (a tuple) | R | rich `Query` → `structure Query {projection : List String}`; `projectsColumns incoming = !incoming.projection.isEmpty` ↔ `bool(value.values_select)` (mapping.md §2). G-CONF bridges via real `value.values_select`. |
| A2 | `shaper := if projectsColumns incoming then Shaper.namedValues else shaper` | `if value.values_select: self._iterable_class = ValuesIterable` | I | identical control + data flow: the single-armed conditional writes the named-values shaper exactly when the projection is non-empty, else leaves the field unchanged. `Shaper.namedValues` ↔ `ValuesIterable` (mapping.md §2). The `else shaper` arm is the Lean rendering of "the `if` did not fire, so `_iterable_class` is untouched" — the unchanged frame (directive 5). |
| A3 | `storedQuery := incoming` | `self._query = value` | I | identity install; `storedQuery` ↔ `self._query`. Unconditional, both sides. |
| A4 | `return ()` (Unit) | (setter returns `None`) | R | a Python setter has no return value; the modeled method returns `Unit`. The observable effect is the two field post-states, pinned by the `ensures` clauses. |

Discriminating content of the change — `_iterable_class` MUST become the
named-values shaper when (and only when) the incoming carrier projects columns —
lives in `shaperAfter incoming prior = if projectsColumns incoming then
Shaper.namedValues else prior` (model) ⇔ the `if value.values_select:
self._iterable_class = ValuesIterable` step (real). The pre-patch setter omitted
this step entirely, so `_iterable_class` kept its prior value (`ModelIterable`
for a freshly constructed container); `Solution_prepatch.lean` reproduces that
(impl is `storedQuery := incoming; return ()`, no shaper write) and **fails**
the clause `shaper = shaperAfter incoming shaperOld` on exactly the projecting
case — the unsolved goal is `projectsColumns incoming = true → shaperOld =
Shaper.namedValues`, which is the bug (G-DIFF).

## B. The `mut`-frame discipline (directive 5)

`storedQuery` and `shaper` are the two genuinely-written fields, declared `mut`.

- `storedQuery` is pinned exactly to the supplied carrier (`ensures storedQuery
  = incoming`) — A3.
- `shaper`'s post-state is pinned exactly per the reconciliation rule (`ensures
  shaper = shaperAfter incoming shaperOld`). The PRESERVED frame (the
  no-projection case) is stated against the **entry value** `shaperOld`, not left
  unconstrained — closing the Lean analogue of the full-permission hole: a wrong
  impl that silently overwrote `shaper` in the no-projection case would violate
  `shaper = shaperOld`.
- `incoming` is NOT `mut`: the setter reads `value.values_select` and never
  mutates the carrier (directive 5 — a read-only input must not be `mut`).

## C. No axioms, no kind-3 (inexpressible-changed-op) steps

Every step is R or I. There is **no consumed axiom** and **no A-reference deep
model of a foreign callee**: the changed function reads one attribute of its
argument and writes two of its own fields, calling nothing whose contract the
proof must consume (mapping.md §3). Hence `axioms` region is empty,
`deep_model_references` is empty, and G-AX is skipped. The one operation that
genuinely *changed* — adding the conditional shaper reconciliation — is modeled
**directly** as the `if`-assignment (A2), an **I** op transliterated by G-CONF,
not hidden behind an axiom about the function under change.

## D. verify(Solution) ⇒ resolved

`assignQuery` verifies only if (A2) `shaper` equals `shaperAfter incoming
shaperOld` — i.e. becomes the named-values shaper exactly when the carrier
projects columns and is otherwise the prior shaper — and (A3) `storedQuery`
equals `incoming`. By R (`Query ↔ values_select`, `Shaper ↔ _iterable_class`
classes, `Unit ↔ None`) the verified method equals the patched setter's effect on
the tested carriers; by G-CONF the R/I transliteration of the `if`-assignment
agrees with `patch.diff`'s real behaviour (real `value.values_select`, real
`reloaded.query = value` setter, real `reloaded._iterable_class`) on ≥10⁵ inputs.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The only
trust point is refinement fidelity (this doc, G-EQ + G-CONF); there are no axioms
(G-AX skipped).
