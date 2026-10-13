# refinement.md — django__django-15561

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `decideSchemaAlteration` `do` block and the `schemaAlterationNeeded` pure
spec) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement; state the bijection), **A-consumed** (proof uses an axiom's
`ensures`), **A-reference** (deep model validated == real callee by G-AX), or
**I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. There are no A
legs in this bundle. Claim: any impl verifying against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The decision site — `_field_should_be_altered()` (`django/db/backends/base/schema.py:1372`)

Gold change: the literal `non_database_attrs` list is replaced by
`old_field.non_db_attrs` / `new_field.non_db_attrs`, and the new class attribute
`Field.non_db_attrs` (`django/db/models/fields/__init__.py:143`) adds `"choices"`
to that set. The net behaviour: a difference confined to `choices` (and the
other listed presentation attributes) no longer makes the two reconstructed
`(path, args, kwargs)` identities differ, so no column rewrite is generated.

| # | Solution.lean impl op (`decideSchemaAlteration`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `a b : FieldDef` | `old_field`, `new_field` args of `_field_should_be_altered` | R | `Field` ↔ `FieldDef` via the projection (mapping.md §2): `quote_name(field.column)`, the stripped `deconstruct()` identity, and the `choices` kwarg. Both read-only — no `mut` (directive 5). |
| A2 | `a.quotedColumn`, `b.quotedColumn` | `self.quote_name(old_field.column)`, `self.quote_name(new_field.column)` | R | the quoted column name; `quote_name` is the unchanged callee, run live by G-CONF. `String` ↔ `str`. |
| A3 | `a.schemaIdentity`, `b.schemaIdentity` | `(old_path, old_args, old_kwargs)` / `(new_path, new_args, new_kwargs)` after `kwargs.pop(attr)` for every `attr in field.non_db_attrs` | R | the schema-relevant reconstruction. `non_db_attrs` minus `choices` is the unchanged `non_database_attrs` set; mapping.md §2.1 strips exactly that set, splitting `choices` out separately. `deconstruct()` is the unchanged callee, run live by G-CONF. |
| A4 | `decide (a.quotedColumn ≠ b.quotedColumn) || decide (a.schemaIdentity ≠ b.schemaIdentity)` | `self.quote_name(old.column) != self.quote_name(new.column) or (old_path, old_args, old_kwargs) != (new_path, new_args, new_kwargs)` | I | the decision disjunction, identical under the projection. Post-patch `non_db_attrs` includes `choices`, so a `choices`-only difference leaves both reconstructions equal ⇒ the disjunction is `False`. The model encodes the same end-state by never consulting `FieldDef.choices`. |
| A5 | returned `Bool` | the returned `bool` | R | `true`/`false` ↔ `True`/`False`. |

Discriminating content of the change — a difference confined to `choices` must
yield `False` (no rewrite) — lives in `schemaAlterationNeeded` **not** consulting
`a.choices`/`b.choices`. The pre-patch behaviour treated `choices` as part of the
reconstructed identity (it was absent from `non_database_attrs`), so a
`choices`-only difference made the identities differ and returned `True`;
`Solution_prepatch.lean` reproduces that by adding the
`decide (a.choices ≠ b.choices)` disjunct and **fails** `out =
schemaAlterationNeeded a b` exactly when `a` and `b` differ only in `choices`
(G-DIFF). G-CONF independently confirms: run against the pre-patch (unpatched)
oracle, the shadow disagrees on precisely the `choices`-only diffs.

## B. The `non_db_attrs` definition site — `Field.non_db_attrs` (`django/db/models/fields/__init__.py:143`)

The second gold hunk adds the `non_db_attrs` class attribute (the old literal
list, plus `"choices"`). It is not a separately-observable behaviour: its sole
effect is to feed the attribute set the decision site (A) strips. It is modeled
implicitly by the strip set in mapping.md §2.1 (the unchanged attributes) plus
the decision's omission of `choices` (A4). No separate `method` or prepatch:
its behavioural content is entirely the A-site decision, and a prepatch must
keep the spec byte-identical (G-DIFF).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely changed — excluding `choices`
from the rewrite decision — is modeled **directly** in the `pure` region
(`schemaAlterationNeeded` ignores `FieldDef.choices`), not hidden behind an
axiom about the function under change. There are no consumed axioms and no
deep-model references: the only callees (`deconstruct`, `quote_name`) are
**unchanged** and run live by G-CONF.

## D. verify(Solution) ⇒ resolved

`decideSchemaAlteration` verifies only if its output equals
`schemaAlterationNeeded a b` (A4), i.e. the decision that ignores `choices`. By R
(`Field ↔ FieldDef` via the unchanged `deconstruct`/`quote_name` projection, the
`Bool ↔ bool` identity) the verified decision equals the patched
`_field_should_be_altered(old, new)` on the tested field pairs; by G-CONF the R/I
projection of the decision agrees with `patch.diff`'s behaviour on 100 012 inputs
(0 disagreements) and disagrees with the pre-patch behaviour exactly on the
`choices`-only diffs (the bug). Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE). Trust point is the single one of plan §1.1 that applies
here: refinement fidelity (this doc, G-EQ + G-CONF); there are no axioms, so the
axiom-soundness trust point (G-AX) is vacuous.
