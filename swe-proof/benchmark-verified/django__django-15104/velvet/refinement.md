# refinement.md — django__django-15104

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`fieldDefsIgnoringRelationTargets` `do` block and the deep `viewAll`/`fieldView`/
`dropTarget` model) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement; state the bijection), **A-consumed** / **A-reference** (none in
this bundle), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The changed routine — `only_relation_agnostic_fields` (`autodetector.py:89`)

Gold hunk:
```
 if field.remote_field and field.remote_field.model:
-    del deconstruction[2]['to']
+    deconstruction[2].pop('to', None)
```

| # | Solution.lean impl op (`fieldDefsIgnoringRelationTargets`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `fields : List FieldDef` | `fields` mapping iterated via `sorted(fields.items())` | R | dict-of-fields ↔ name-ordered `List FieldDef` (mapping.md §2); `sorted` is an unchanged callee modeled as input order (free). G-CONF feeds the same fields to both sides. |
| A2 | `f.relational` consulted in `fieldView` | `if field.remote_field and field.remote_field.model:` | R | the relational truthiness ↔ free `Bool` (mapping.md §2/§3). Independent of the patch. |
| A3 | `f.kwargs` carried as the binding set | `deconstruction = self.deep_deconstruct(field)`, component `[2]` | R | unchanged `deep_deconstruct` kwargs ↔ free `List (String × Int)` (mapping.md §3). The value tokens are opaque and never inspected. |
| A4 | `dropTarget f.kwargs` for a relational field (`fieldView`) — keep every binding whose name ≠ `"to"`, **never failing** | `deconstruction[2].pop('to', None)` | I | the changed op, modeled **deeply**: `pop(k, None)` removes key `k` when present and is a total no-op otherwise — exactly `filter (·.1 ≠ "to")`. Total (raises nothing) for every kwargs set, with or without `"to"`. This is the whole behavioural content of the fix. |
| A5 | result is `Except.ok (viewAll fields)` — the per-field views, **always** `ok` | the method returns `fields_def` normally (never raising) | I | the routine completes for every input; `Except.ok` carries the assembled list. mapping.md §2 (raising ↔ `Except`). |

### Discriminating content of the change
`del deconstruction[2]['to']` raises `KeyError` when a relational field's kwargs
lack `"to"` (the hardcoded-`to` custom FK of the issue); `pop('to', None)` does
not. The model pins this two ways, both load-bearing:
1. **never raises** — `out = Except.ok (...)` (`Except.error ()` is unreachable
   for the gold skeleton; the pre-patch skeleton produces `Except.error ()` on a
   relational field missing `"to"` and so **fails verify**, G-DIFF);
2. **target elided** — `viewAll` uses `dropTarget` on relational fields.

`Solution_prepatch.lean` reproduces the unconditional-removal-with-failure
behaviour: on a relational field whose kwargs lack `"to"` it yields
`Except.error ()`, which violates `out = Except.ok (viewAll fields)`. It fails on
exactly the clause the fix repairs (confirmed: the rewrite goal is
`(if i_2 then Except.error () else Except.ok result_1) = Except.ok (viewAll fields)`).

## B. No axioms (A-consumed / A-reference: none)

The three callees the routine consults — `deep_deconstruct`, the
`remote_field`/`model` relational test, and `sorted` — are **unchanged** by the
patch and modeled as FREE inputs whose every value the spec tolerates (directive
7; mapping.md §3). The spec relies on no library callee's behavior, so there is
no consumed axiom and no deep-model reference. `axiom_check.py` is omitted
(G-AX skips). The only thing modeled deeply is the *changed* op itself (`pop`,
step A4) — an **I** transliteration, not an axiom about the function under change.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — dropping the
`'to'` binding from `del` (raises-if-absent) to `pop(..., None)` (total) — is
modeled **deeply** by `dropTarget` plus the `Except.ok` totality of the result
(steps A4/A5), not hidden behind an axiom.

## D. verify(Solution) ⇒ resolved

`fieldDefsIgnoringRelationTargets` verifies only if its output is
`Except.ok (viewAll fields)` for **every** input — i.e. it never raises (A5) and
elides the relation target of relational fields (A4). By R (mapping.md §2:
dict↔list, relational↔Bool, kwargs↔assoc-list, `pop`↔`filter`) the verified
routine equals the gold-patched `only_relation_agnostic_fields` on the inputs the
F2P test and issue exercise — in particular the hardcoded-`to` custom-FK field,
where the gold patch completes (the create migration is detected) and the
pre-patch raised `KeyError`. G-CONF differential-tests the R/I shadow against the
REAL gold-patched routine over ≥10⁵ fuzzed field collections (including that
shape), 0 disagreements. Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). Trust points: refinement fidelity (this doc, G-EQ + G-CONF); there
are no axioms to trust.
