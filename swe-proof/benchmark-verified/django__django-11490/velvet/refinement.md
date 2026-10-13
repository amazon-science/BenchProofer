# refinement.md — django__django-11490

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`applyProjection` `do` block) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement; state the bijection), **A-consumed** (proof uses
an axiom's `ensures`), **A-reference** (deep model validated == real callee by
G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The push-down site — `get_combinator_sql` (`django/db/models/sql/compiler.py:426–433`)

Gold hunk:
```
                 if not compiler.query.values_select and self.query.values_select:
+                    compiler.query = compiler.query.clone()
                     compiler.query.set_values((
                         *self.query.extra_select,
                         *self.query.values_select,
                         *self.query.annotation_select,
                     ))
```

| # | Solution.lean impl op (`applyProjection`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `persistent : Carrier` | `compiler.query`, read at the guard | R | the sub-query `Query` → the five observations this step touches (`columns`, `sideSelected`, `auxSelected`, `auxAvailable`, `ownFields`); `persistent.columns.isEmpty` ↔ `not compiler.query.values_select`. Full bijection in mapping.md §2. |
| A2 | params `requested`, `projected : List String` | `self.query.values_select` (guard) and `(*extra_select, *values_select, *annotation_select)` (`compiler.py:430–432`) | R | two INDEPENDENT observations of the outer query: the guard reads the first, the recording the second. |
| A3 | `let mut working := persistent` | `compiler.query = compiler.query.clone()` | I | take a private working copy. In Lean a fresh binding to an immutable value IS a clone (no aliasing); `persistent` is untouched by later writes to `working`. |
| A4 | `if shouldProject persistent requested then ... working := recordOnto persistent projected` | `if not compiler.query.values_select and self.query.values_select: compiler.query.set_values((...))` | I | identical guarded data flow. `recordOnto` transliterates `set_values`' SEVEN observable steps — the empty-`fields` leg, the no-extra/no-annotations shortcut, the `if extra_select` / `elif annotation_select` / `else` three-way sort (the `elif` being the side-output PRECEDENCE), and the two mask writes plus `values_select` landing together. Step-by-step table in mapping.md §2. |
| A5 | `return working` | the carrier `compiler.as_sql()` then reads to build the fragment | R | `working`'s three selection records ↔ the `values_select` / `extra_select` / `annotation_select` the fragment is compiled from. |
| A6 | `ensures persistent = persistentOld` | the **effect of the `clone()`**: `set_values` mutates the copy, NOT the shared `Query` in `combined_queries` | I (frame) | the whole point of the gold one-liner. Pins all five observations, so a rival that records onto the shared carrier and restores only some of them is caught. |
| A7 | `require shouldProject persistent requested = true → answerable persistent projected = true` | `add_fields(field_names, True)` (`query.py:2062` → `1788–1824`) raises `FieldError` for a name it cannot resolve | R (domain) | bounds the claim to the sub-domain where the real callee is TOTAL. `answerable` = `ownFields ∪ sideSelected ∪ auxSelected`, measured to be exactly the non-raising set (481 admissible inputs across 15 carrier shapes, 0 admitted-but-raising, 0 value divergences, 0 excluded-but-succeeding modulo relation-traversal names). |
| A8 | `ensures shouldProject ... = false → recorded = recordedOld` and `... = true → recorded = true` | `set_values` is called strictly INSIDE the guard | I (accounting) | whether the recording act occurs is observable beyond the column list (`set_values` also clears deferred loading and rewrites both masks), so it is pinned; how MANY times is left free. |

Discriminating content of the change — the **shared carrier must survive the
operation unchanged** so a second evaluation can project a different column list
— lives in `ensures persistent = persistentOld` (model) ⇔ the inserted
`compiler.query = compiler.query.clone()` that diverts `set_values` away from the
shared object (real). The pre-patch code mutates the shared carrier directly;
`Solution_prepatch.lean` reproduces that (impl is
`persistent := recordOnto persistent projected; return persistent`, no clone) and **fails** the frame clause on exactly the
push-down case — the unsolved goal is
`(if shouldProject persistentOld requested then recordOnto persistentOld projected
else persistentOld) = persistentOld`, i.e. the projection leaking back into the shared carrier (G-DIFF).

## B. The `mut`-frame discipline (directive 5)

This bundle IS a directive-5 instance: the bug is an unframed write to a shared
read-only-by-contract carrier.

- `persistent` is declared `mut` (the long-standing code reaches for the shared
  carrier as the thing to reconcile), but its post-state is pinned **exactly to
  its entry value**: `ensures persistent = persistentOld`. This closes the Lean
  analogue of the full-permission hole — an impl that wrote the projection back
  onto `persistent` (the pre-patch bug) violates the frame. The push-down result
  is delivered through the SEPARATE return carrier `working`, never by mutating
  the shared input.
- `requested` and `projected` are NOT `mut`: the operation reads the outer
  request's own column list and its pushed-down projection and never alters
  either (directive 5 — a read-only input must not be `mut`).
- `working`'s post-state is pinned exactly by `ensures working = workingCarrier
  persistentOld requested projected` — note it is computed against `persistentOld`, the
  carrier's entry columns, so the spec ties the projection result to the carrier
  state observed BEFORE any write, leaving no room for an impl to observe a
  self-inflicted mutation.

## C. No axioms, no kind-3 (inexpressible-changed-op) steps

Every step is R or I. There is **no consumed axiom** and **no A-reference deep
model of a foreign callee**: the changed operation reads two emptiness
observations and writes a working carrier, calling nothing whose contract the
proof must consume (mapping.md §3). `Query.clone()` and `Query.set_values()` are
modeled directly — `clone()` as Lean value-copy (A3), `set_values` as installing
the column list (A4) — not hidden behind axioms about the function under change.
Hence the `axioms` region is empty, `deep_model_references` is empty, and G-AX is
skipped. The one operation that genuinely *changed* — inserting the clone so the
shared carrier is left intact — is modeled **directly** as the working-copy +
frame discipline (A3 + A6), an **I** leg transliterated by G-CONF.

## D. verify(Solution) ⇒ resolved

`applyProjection` verifies only if (A6) `persistent = persistentOld` — the shared
carrier is returned exactly as received — and (A4/A5) `working = workingCarrier
persistentOld requested projected` — the working carrier carries the projection sorted across its three
selection records exactly when the push-down applies, else the carrier exactly
as it stands. By R (sub-query `Query` ↔ the five-field `Carrier` of
mapping.md §2, outer projection tuple ↔ `List String`, the carrier read by
`as_sql` ↔ `working`) the verified method
equals the patched block's effect on the tested compound queries; by G-CONF the
R/I transliteration of the working-copy + frame discipline agrees with
`patch.diff`'s real behaviour (real compound `QuerySet`, real repeated
`values_list(...)` evaluation over the shared combined sub-queries, real patched
`get_combinator_sql`) on ≥10⁵ inputs. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). The only trust point is refinement fidelity (this
doc, G-EQ + G-CONF); there are no axioms (G-AX skipped).
