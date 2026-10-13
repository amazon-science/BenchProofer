# refinement.md — django__django-12774

The operation-by-operation correspondence between `model.py`'s implementation
(the `should_reject` impl region, the deep `permits_alone` / `any_permits`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (the proof uses an axiom's `Ensures`),
**A-reference** (a deep model validated == the real callee by axiom_check.py /
G-AX, NOT consumed), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The guard site — `QuerySet.in_bulk()` (`django/db/models/query.py:685`)

Gold hunk:
```
-        if field_name != 'pk' and not self.model._meta.get_field(field_name).unique:
+        opts = self.model._meta
+        unique_fields = [
+            constraint.fields[0]
+            for constraint in opts.total_unique_constraints
+            if len(constraint.fields) == 1
+        ]
+        if (
+            field_name != 'pk' and
+            not opts.get_field(field_name).unique and
+            field_name not in unique_fields
+        ):
             raise ValueError("in_bulk()'s field_name must be a unique field but %r isn't." % field_name)
```

| # | model.py impl op (`should_reject`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `field_name: int`; `field_name == PK` early return False | `field_name != 'pk'` (the guard's first conjunct; the pk short-circuit) | R | field name `str` ↔ `int` identity; `'pk'` / `opts.pk.name` ↔ `PK` (mapping.md §2). `field_name == PK ⇒ accept` ⇔ `field_name == 'pk' ⇒ the conjunction is False ⇒ no raise`. |
| A2 | param `field_unique: bool`; `field_unique` early return False | `not opts.get_field(field_name).unique` (the guard's second conjunct) | A-reference | `opts.get_field(field_name).unique` is the UNCHANGED individual-unique flag, passed in as data; `axiom_check.py` reads the REAL callee when forming each observation (mapping.md §3.2). `field_unique ⇒ accept` ⇔ `not unique` is False ⇒ no raise. |
| A3 | `guarantees: List[Tuple[bool, PSeq[int]]]`; the loop building `found = any_permits(guarantees, 0, field_name)` via `permits_alone(g) = g[0] and len(g[1])==1 and g[1][0]==field_name` | `unique_fields = [c.fields[0] for c in opts.total_unique_constraints if len(c.fields)==1]` then `field_name not in unique_fields` (the guard's NEW third conjunct) | A-reference | the changed operation is modeled **deeply**: `permits_alone` / `any_permits` (pure region) ARE the single-field-unconditional extraction + membership test. There is no consumed axiom. The deep model is validated == the real `total_unique_constraints` filter + single-field extraction by G-AX (axiom_check.py; mapping.md §3.1). A `UniqueConstraint` ↔ `(condition is None, fields)`; `total_unique_constraints` already keeps only `condition is None`, so `g[0]` is True for every supplied element — the model still carries the flag so it is 1:1 with the patch and would correctly reject a conditional element. `len(c.fields)==1`/`c.fields[0]` ↔ `len(g[1])==1`/`g[1][0]` (R). |
| A4 | `should_reject` returns the boolean `field_name != PK and not field_unique and not any_permits(...)` | the `if (...)` test whose True branch executes `raise ValueError(...)` | I | the modeled object is the guard *decision*; the `raise` is the identical control-flow consequence of the decision being True. The error message and the subsequent `in_bulk` body are unchanged by the patch and irrelevant to the decision. |

The discriminating content of the change is the NEW third conjunct
`field_name not in unique_fields` (A3). The pre-patch guard lacked it entirely:
a non-`pk`, non-`unique` field was ALWAYS rejected. `model_prepatch.py`
reproduces that (`return field_name != PK and not field_unique`, ignoring
`guarantees`) and **fails** the postcondition
`Result() == (field_name != PK and not field_unique and not any_permits(...))`
whenever some guarantee permits the field — exactly the F2P
`test_in_bulk_meta_constraint` case (`year` is the sole field of an
unconditional constraint). This is the spec sensing the change (G-DIFF).

## B. The discriminators the spec pins (verify ⇒ correct)

The postcondition pins the decision exactly, so no wrong impl of the modeled
behaviour can satisfy it:

- **F2P (accept):** a single-field unconditional guarantee (`year`) ⇒
  `any_permits` True ⇒ `not Result()` (clause `Implies(any_permits(...), not
  Result())`). The prepatch rejects ⇒ fails.
- **P2P (still reject) — partial constraint:** a constraint with `condition is
  not None` has `g[0] == False` ⇒ `permits_alone` False ⇒ does not flip the
  decision (`ean` stays rejected). Mirrors `total_unique_constraints` excluding
  conditional constraints.
- **P2P (still reject) — composite constraint:** a constraint with
  `len(fields) > 1` has `len(g[1]) != 1` ⇒ `permits_alone` False (`brand`,
  `name` stay rejected). Mirrors `if len(constraint.fields) == 1`.
- **P2P (accept) — unique=True:** `field_unique` ⇒ early-return accept
  (`test_in_bulk_non_unique_field` / the existing unique-field path).
- **pk:** `field_name == PK` ⇒ accept (`in_bulk(field_name='pk')` default).
- **Delivery (total correctness):** the precondition carries a termination
  obligation (`MustTerminate`), and the impl's scan loop discharges it with
  the strictly decreasing measure `len(guarantees) - i`. Without it Nagini
  proves only partial correctness, so an implementation that never returns on
  the non-pk / non-unique path (unbounded self-recursion or a frozen loop)
  would satisfy the value postcondition vacuously while its refined
  counterpart diverges instead of delivering the decision. The obligation
  excludes exactly that class: a self-call or non-decreasing loop now fails
  the obligation-leak check.

G-AX (axiom_check.py) confirms each of these against the REAL Django
`total_unique_constraints` + `get_field().unique` derivation.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — adding `field_name not in unique_fields` derived from the
single-field total unique constraints — is modeled **deeply** (`permits_alone` /
`any_permits`, A3, an **A-reference**), not hidden behind an axiom about the
function under change. There is **no consumed `@ContractOnly` axiom**: the
unchanged callees (`total_unique_constraints`, `get_field().unique`) are
A-references whose real behaviour G-AX validates the deep model against.

## D. verify(model) ⇒ resolved

`should_reject` verifies only if it TERMINATES (the precondition's
`MustTerminate` obligation must be fully consumed, so a diverging impl cannot
verify vacuously) and its result equals
`field_name != PK and not field_unique and not any_permits(guarantees, 0,
field_name)` (the exact post-patch guard) — in particular it must consult the
declared guarantees (A3), which the prepatch does not. By R (field-name `str` ↔
`int`, `'pk'` ↔ `PK`, `UniqueConstraint` ↔ `(condition is None, fields)`) the
verified decision equals the gold guard `field_name != 'pk' and not
opts.get_field(field_name).unique and field_name not in unique_fields`; by G-AX
the deep model `any_permits` equals the real `total_unique_constraints` +
single-field extraction (A-reference) and `field_unique` is the real
`get_field().unique` (A-reference). Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and audited
callees — and the gold patch resolves (G-RESOLVE). The trust points are exactly
the two of PLAN §1.1: axiom/callee soundness (G-AX, here the A-reference checks)
and refinement fidelity (this document, G-EQ).
