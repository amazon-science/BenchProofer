# refinement.md — django__django-12965

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `directDeleteEligible` `do` block plus the deep `withTarget` model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A-consumed**
(proof uses an axiom's `ensures`), **A-reference** (a deep model validated ==
the real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The single-alias decision — `SQLDeleteCompiler.single_alias` (`compiler.py:1408`)

Gold hunk:
```
 @cached_property
 def single_alias(self):
+    # Ensure base table is in aliases.
+    self.query.get_initial_alias()
     return sum(self.query.alias_refcount[t] > 0 for t in self.query.alias_map) == 1
```

| # | Solution.lean impl op (`directDeleteEligible`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `refcount : List Nat` | the implicit `self.query` reference-count state `[self.query.alias_refcount[t] for t in self.query.alias_map]` | R | the Lean↔Python carrier bijection (mapping.md §2): `alias_map` order ↔ list order, base table ↔ head, empty `alias_map` ↔ `[]`. |
| A2 | `tableRefs := withTarget tableRefs` (head incremented; `headD 0` makes the empty state yield `[1]`) | `self.query.get_initial_alias()` (the **added** line) | A-reference + I | the added call is to the **unchanged** callee `get_initial_alias`; its single side effect on the refcount state is modeled deeply by `withTarget` (mapping.md §3.1), validated `== get_initial_alias` by G-AX. The assignment op itself is **I** (concrete, transliterated by G-CONF). |
| A3 | `return liveCount tableRefs.tail == 0` | `return sum(self.query.alias_refcount[t] > 0 for t in self.query.alias_map) == 1` | I | `liveCount` counts entries `≠ 0` ⇔ `sum(bool > 0)` counts truthy refcounts. The count is taken AFTER A2, and A2 always leaves the head ≥ 1 while touching no other entry, so the Python total is exactly `1 + liveCount tail`; hence `sum(...) == 1` ⇔ `liveCount tail == 0` pointwise. Transliterated and differential-tested by G-CONF (100,016 real `Query` states, 0 disagreements). |

The mut-frame postcondition `ensures tableRefs = withTarget tableRefsOld` (directive
5) pins the *exact* post-state: the operation mutates the refcount vector by
exactly one `withTarget` and nothing else — matching the lone `get_initial_alias()`
side effect. An impl that mutated the state differently (or not at all) fails
this clause.

Discriminating content of the change lives in `A2`. The pre-patch code omits
`get_initial_alias()` and asks whether the recorded state holds exactly one live
table, so on a full-table delete (`tableRefs = []`, empty `alias_map`) it counts
`liveCount [] = 0 ≠ 1` and falls into the subquery path; under the spec the tail
of `[]` is empty, no non-targeted table is live, and the deletion is a direct
`DELETE FROM table`. `Solution_prepatch.lean` reproduces the omission (no
`withTarget` call, and the whole-vector `== 1` test) and **fails** both
`direct ↔ liveCount tableRefsOld.tail = 0` and the mut-frame clause
`tableRefs = withTarget tableRefsOld` (G-DIFF). This is
exactly the F2P observation: `test_fast_delete_all` asserts the full delete
issues one query with no `SELECT` subquery.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely changed — inserting
the base-table-registration call before the count — is modeled with the deep
`withTarget` reference (A-reference, A2) and a concrete count (I, A3); there is no
axiom about the function under change (`single_alias` itself is never
axiomatized). The only deep-model callee, `withTarget`, is an **unchanged** repo
method (`get_initial_alias`), G-AX-validated.

## C. verify(Solution) ⇒ resolved

`directDeleteEligible` verifies only if (i) it leaves the refcount state at exactly
`withTarget tableRefsOld` (mut frame = the lone real side effect) and (ii) its
boolean equals `liveCount tableRefsOld.tail = 0` — i.e. the delete is confined to
the table it targets. By the A2 head-invariant this is pointwise the patched
`sum(...) == 1`. By R (the `List Nat` ↔
`alias_refcount`/`alias_map` bijection) and G-AX (`withTarget` == the real
`get_initial_alias` side effect), the verified decision equals the patched
`single_alias` on every real `Query` state; by G-CONF the R/I transliteration
agrees with `patch.diff`'s behaviour over fuzzed alias states including the
empty-`alias_map` full-delete case. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the
audited callee — and the gold patch resolves (G-RESOLVE). Trust points are
exactly the two of plan §1.1: deep-model soundness (G-AX) and refinement
fidelity (this doc, G-EQ + G-CONF).
