# refinement.md — django__django-12774

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `validateLookupField` `do` block, plus the deep `singleColumnKeys` /
`lookupFieldDecision` models in the `pure` region) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement; state the bijection),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (deep model
validated == real callee by G-AX), or **I** (identical concrete op). EVERY step
is R, A, or I.

This bundle has **no consumed axioms and no A-reference**: every unchanged
callee is modeled as a FREE input owed no contract (directive 7), and the
changed behaviour is modeled deeply as pure R/I content. The R/I legs are
mechanically refuted by **G-CONF** (`conformance_check.py`, §4.1); the narrative
is audited by **G-EQ**. **G-AX is `skip`** (no axioms — see mapping.md §3.3).

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The lookup-field validation guard — `QuerySet.in_bulk` (`django/db/models/query.py:684`)

Gold hunk (body lines 688–700 post-patch):
```python
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

| # | Solution.lean impl op (`validateLookupField`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `fieldName : String` | `field_name: str` arg | R | `str` ↔ `String` (mapping.md §2). G-CONF passes the same field-name strings to both sides. |
| A2 | param `fieldUnique : Bool` (free input) | `opts.get_field(field_name).unique` | R + free | `Field.unique` flag is unchanged by the patch; modeled as a free Bool owed no contract (directive 7). G-CONF supplies the real `.unique` value to the shadow and lets the oracle compute its own. |
| A3 | param `constraints : List (List String)` (free input) | `opts.total_unique_constraints` (each `.fields`) | R + free | unchanged callee (mapping.md §3.1). `UniqueConstraint` ↔ its `.fields` list; modeled as a free input. G-CONF reads the real property. |
| A4 | `uniqueFields := singleColumnKeys constraints`, computed by the backward `while` fold over `soleColumn` | the `unique_fields` list comprehension (`constraint.fields[0] for … if len(constraint.fields) == 1`) | I | concrete, transliterated by G-CONF. `soleColumn g = [g[0]!]` iff `g.length = 1` else `[]` ⇔ the comprehension's `if len(c.fields)==1` filter + `c.fields[0]` projection. The backward fold computes exactly the left-to-right concatenation `singleColumnKeys`. |
| A5 | `if (fieldName != "pk") && (!fieldUnique) && (!uniqueFields.contains fieldName) then Except.error … else Except.ok ()` | the three-conjunct `if (…)` → `raise ValueError` else fall through | I + R | identical boolean structure. `raise ValueError("…unique field…")` ↔ `Except.error .fieldNotUnique`; falling past the guard ↔ `Except.ok ()` (mapping.md §2). The `field_name not in unique_fields` conjunct ⇔ `!uniqueFields.contains fieldName`. |

Discriminating content of the change — a field that is the **sole column of a
single-column total uniqueness guarantee** must be ACCEPTED — lives in the third
conjunct `!(singleColumnKeys constraints).contains fieldName` (model) ⇔
`field_name not in unique_fields` (real). The pre-patch guard had only the first
two conjuncts; `Solution_prepatch.lean` reproduces that two-conjunct guard and
**fails** the postcondition on exactly the goal `fieldName ∉ singleColumnKeys
constraints` (it reaches the rejection branch for a constraint-covered field it
cannot discharge) — i.e. G-DIFF sees the bug precisely where the F2P test
`test_in_bulk_meta_constraint` exercises it.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — adding the
single-column-constraint allowance to the validation guard — is modeled
**deeply** (`singleColumnKeys`/`soleColumn` in the `pure` region and the
verified fold), not hidden behind an axiom about the function under change.
There is no consumed `inBulk` axiom and no A-reference.

## C. Free inputs are weaker than any callee (directive 7)

`fieldUnique` and `constraints` are unconstrained method parameters. The
postcondition `out = lookupFieldDecision fieldName fieldUnique constraints`
holds for EVERY value of both, so the spec assumes nothing about
`get_field(...).unique` or `total_unique_constraints` beyond what the decision
itself computes from them — strictly weaker than any concrete contract. G-CONF
confirms the real callees produce values within this modeled domain (a `str`
flag and a list of field-name lists).

## D. verify(Solution) ⇒ resolved

`validateLookupField` verifies only if its outcome equals
`lookupFieldDecision`, i.e. it rejects exactly when the key is neither `"pk"`,
nor individually unique, nor a single-column-constraint key — the third conjunct
(A5) being the whole of the behavioural change. By R (`str ↔ String`,
`UniqueConstraint ↔ .fields`, `ValueError ↔ Except.error`) the verified decision
equals the patched guard's reject/accept behaviour on every input; by G-CONF the
R/I transliteration of the fold + guard agrees with `patch.diff`'s behaviour
over ≥10⁵ inputs built from real Django models with single-column, multi-column,
and conditional `UniqueConstraint`s. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). Trust points: refinement fidelity (this doc, G-EQ +
G-CONF). There is no axiom trust point (G-AX skip).
