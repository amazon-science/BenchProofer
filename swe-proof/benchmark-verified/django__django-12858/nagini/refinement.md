# refinement.md — django__django-12858

The operation-by-operation correspondence between `model.py`'s implementation
(the `select_reported_paths` impl region and the deep `flag_path` decision) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses an axiom's `Ensures`), **A-reference** (a deep
model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The reporting decision — `Model._check_ordering` (`django/db/models/base.py:1750`)

Gold hunk (inside `except (FieldDoesNotExist, AttributeError):`):
```
- if fld is None or fld.get_transform(part) is None:
+ if fld is None or (
+     fld.get_transform(part) is None and fld.get_lookup(part) is None
+ ):
      errors.append(checks.Error("'ordering' refers to the nonexistent field, "
                                 "related field, or lookup '%s'." % field,
                                 obj=cls, id='models.E015'))
```

| # | model.py impl op (`select_reported_paths`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | inputs `reached_field, is_value_op, is_compare_op: List[int]` (0/1), index-aligned, one entry per examined path | the per-path state in the `for field in related_fields:` loop: for each path, `fld is not None`, `fld.get_transform(part) is not None`, `fld.get_lookup(part) is not None` at the trailing segment | R | the dotted path collection ↔ aligned index `k`; each truthiness test ↔ a 0/1 (mapping.md §2). |
| A2 | `flag_path(reached_field[i], is_value_op[i], is_compare_op[i]) == (reached_field[i]==0 or (is_value_op[i]==0 and is_compare_op[i]==0))` | the new guard itself: `errors.append(...)` runs iff `fld is None or (fld.get_transform(part) is None and fld.get_lookup(part) is None)` is true. | I + A-reference | the boolean algebra is **identical** (I): append (report) iff `fld is None ∨ (t is None ∧ l is None)`, with `fld is None ↔ reached_field==0`, `t is None ↔ is_value_op==0`, `l is None ↔ is_compare_op==0`. The two registry-query truthiness tests (`get_transform`/`get_lookup` non-None) that supply `is_value_op`/`is_compare_op` are **A-reference**: their real semantics are validated == the model booleans by axiom_check.py (G-AX, mapping.md §3.1/§3.2), not consumed as `@ContractOnly` Ensures. |
| A3 | append `1` (report) / `0` (accept) to `errors`, one per path, in order | `errors.append(checks.Error(... id='models.E015'))` runs (or not) once per offending path | R | the `models.E015` error object content per path is constant up to the interpolated path string, which the F2P test does not inspect; the observable is presence/absence, carried by 0/1 (mapping.md §2). The accumulation order/length mirrors the real loop. |

The discriminating content of the change — a trailing segment that is a
registered comparison operator (`get_lookup(part)` non-None) but NOT a
value-producing operator (`get_transform(part)` None), with a field reached,
must be ACCEPTED rather than reported — lives in the `and is_compare_op == 0`
conjunct of `flag_path`'s second disjunct (model) ⇔ the `and
fld.get_lookup(part) is None` clause the gold patch ADDS to the `(... )`
sub-condition (real). The pre-patch predicate omits that clause (it reports iff
`fld is None or get_transform(part) is None`); `model_prepatch.py` reproduces
the omission (its impl tests only `reached_field[i] == 0 or is_value_op[i] ==
0`) and **fails** the loop-invariant/postcondition clause `Result()[k] ==
flag_path(reached_field[k], is_value_op[k], is_compare_op[k])` on any path with
`reached_field=1, is_value_op=0, is_compare_op=1` (the prepatch wrongly reports
it, flag 1, where the spec requires flag 0) — exactly the F2P scenario
`ordering = ('test__isnull',)` where `isnull` is a `Lookup` registered on
`CharField` but not a `Transform` (G-DIFF).

## B. No consumed axioms

There is **no `@ContractOnly` axiom** in this bundle. The two callees the real
predicate consults — `Field.get_transform` and `Field.get_lookup` — supply the
two boolean inputs to a decision that is modelled **deeply** (`flag_path` and
the verified loop ARE the post-patch predicate's boolean algebra). They are
therefore **A-reference** (validated == the real callees by axiom_check.py /
G-AX over the full truth table and via real registered/unregistered operators),
NOT axioms the proof's `Ensures` consume. The decision logic itself contains the
changed clause and is verified directly.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, I, or A-reference. The one operation that genuinely
*changed* — widening the "report invalid" predicate to also accept a registered
comparison operator — is modelled **deeply** (the `is_compare_op == 0` conjunct
of `flag_path`, consumed in `select_reported_paths`), not hidden behind an axiom
about the function under change. The two registry queries are unchanged callees
whose only role is to produce the two booleans; they appear solely as the
A-references G-AX validates the deep model against.

## D. verify(model) ⇒ resolved

`select_reported_paths` verifies only if every output flag equals the exact
post-patch decision `flag_path` (A2/A3), i.e. it reports a path iff no field was
reached OR the trailing segment is neither a value-producing nor a comparison
operator (equivalently: accepts iff a field was reached AND the segment is at
least one operator kind). By R (path ↔ aligned index; object/`None` tests ↔ 0/1; the constant
`models.E015` error ↔ a report flag) the verified decision equals the gold
predicate `fld is None or (get_transform is None and get_lookup is None)` on the
examined paths; by G-AX the booleans `is_value_op`/`is_compare_op` equal the real
`get_transform`/`get_lookup` non-None tests (A-reference) and `flag_path` equals
the real predicate over the full truth table. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement and
audited callees — and the gold patch resolves (G-RESOLVE). The trust points are
exactly the two of PLAN §1.1: callee/predicate soundness (G-AX) and refinement
fidelity (this document, G-EQ).
