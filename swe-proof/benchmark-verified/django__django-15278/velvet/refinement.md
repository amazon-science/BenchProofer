# refinement.md — django__django-15278

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`requiresTableRebuild` decision) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A-consumed** / **A-reference** (axiomatized
callee), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs + this narrative are audited by **G-EQ**. `patch.diff` is the
gold patch **verbatim** (applies at base_commit, resolves — G-RESOLVE).

## A. The decision site — `SQLiteSchemaEditor.add_field` (`django/db/backends/sqlite3/schema.py:326`)

Gold hunk (the `if` condition selecting the materialization route):
```
- if not field.null or self.effective_default(field) is not None:
+ if (
+     field.primary_key or field.unique or
+     not field.null or self.effective_default(field) is not None
+ ):
      self._remake_table(model, create_field=field)
  else:
      super().add_field(model, field)
```

Net effect: the table-rebuild route (`_remake_table`) is now forced ALSO when the
new column carries a uniqueness obligation — not only when it disallows nulls or
supplies a default. In the real repo `field.unique` is the property
`self._unique or self.primary_key` (`django/db/models/fields/__init__.py:753`),
so `field.primary_key or field.unique` ≡ `field.unique`: the effective-uniqueness
observation subsumes the `primary_key` disjunct (a primary column is always
uniquely valued). The two route bodies (`_remake_table`, `super().add_field`)
are UNCHANGED; only the boolean decision changed.

| # | Solution.lean impl op (`requiresTableRebuild`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `isUnique : Bool` | `field.primary_key or field.unique` | **R** (property collapse) | `field.unique` is the property `_unique or primary_key` (mapping.md §2), hence `primary_key or unique = unique`: the two gold operands collapse to the single effective-uniqueness observation. G-CONF refutes this leg by driving the raw (`primary_key`, `_unique`) pair exhaustively and deriving `unique` by the property definition verbatim. |
| A2 | param `acceptsNull : Bool` | `field.null` | R | `bool` field flag ↔ `Bool`; the repo uses `not field.null` ↔ `!acceptsNull`. |
| A3 | param `hasServerDefault : Bool` | `self.effective_default(field) is not None` | **A-consumed** (opaque) | UNCHANGED callee `effective_default`, observed ONLY via `is not None` and modeled as a FREE boolean input with NO asserted value (mapping.md §3). Nothing is claimed about it, so G-AX has nothing to check (skip). |
| A4 | leading `isUnique` disjunct | `field.primary_key or field.unique` | **I** (post-collapse) | identical concrete op after A1 — the discriminating behavior the fix introduces, modeled deeply (a pure boolean disjunct). |
| A5 | `\|\| !acceptsNull \|\| hasServerDefault` | `or not field.null or self.effective_default(field) is not None` | **I** | identical concrete op — `or` ↔ `\|\|`, `not` ↔ `!` (mapping.md §2). |
| A6 | `out = (… \|\| … \|\| …)` returned | the `if (...)` truthiness selecting `_remake_table` vs `super().add_field` | R | `out = True` ⇔ the `if` is taken (rebuild route); `out = False` ⇔ the `else` (in-place primitive). The route bodies are unchanged, so the resolved behavior is determined entirely by this decision (mapping.md §1). |

No kind-3 (changed inexpressible) op. The one A-consumed step (A3) is the opaque
unchanged callee; the discriminating change (the `isUnique` disjunct, A4) is I —
deeply modeled and G-CONF-testable. The property collapse (A1) is an R-leg that
G-CONF differential-tests over the full raw cube.

## B. verify(Solution) ⇒ resolved

`requiresTableRebuild` verifies only if `out = isUnique || !acceptsNull ||
hasServerDefault` (A1–A6). By R (the boolean bijections + the property collapse,
mapping.md §2) the verified decision equals the patched `if` condition on every
reachable field state: `field.primary_key or field.unique` evaluates to exactly
the effective `field.unique` property value carried by `isUnique`. Because both
route bodies are unchanged, a column for which the verified decision is `True`
is rebuilt (the working route) and one for which it is `False` uses the in-place
primitive — exactly the gold patch's behavior.

The F2P test `test_add_field_o2o_nullable` adds a nullable `OneToOneField` (so
`isUnique = true` — `OneToOneField.__init__` forces `unique=True` —
`acceptsNull = true`, no default ⇒ `hasServerDefault = false`). The pre-patch
decision (`!acceptsNull || hasServerDefault` = `false || false` = `false`)
wrongly routed it to the in-place primitive, which crashes on SQLite ("Cannot
add a UNIQUE column"). The spec pins `out = true` for this input via the new
`isUnique` disjunct, forcing the rebuild route, which succeeds — the column
appears and is nullable (the test's `assertIn('note_id', ...)` and nullability
assertion).

## C. Prepatch fails on the discriminating clause (G-DIFF)

`Solution_prepatch.lean` (byte-identical spec) returns `!acceptsNull ||
hasServerDefault` — the pre-patch condition, omitting the `isUnique`
disjunct. Against the identical spec this leaves the unsolved goal

```
(!acceptsNull || hasServerDefault) = (isUnique || !acceptsNull || hasServerDefault)
```

which fails whenever `isUnique = true` while `!acceptsNull || hasServerDefault
= false` — i.e. a value-optional, default-less column that nonetheless carries
a uniqueness obligation: precisely the nullable `OneToOneField` the issue
reports.

## D. Trust surface

Only the boolean type bijections + the `Field.unique` property collapse
(mapping.md §2) and the OPAQUE unchanged callee A3. The opaque callee asserts
nothing about its value, so it cannot mask a wrong impl: the spec still forces
the full disjunction regardless of how the default is computed. G-CONF
differential-tests the R/I legs (the property collapse + the disjunction) over
the full 2⁴ raw boolean cube (`primary_key` × `_unique` × `null` ×
default-present) plus fuzz, with `hasServerDefault` ranged as a free boolean.
No axiom_check needed (G-AX skip — nothing asserted to validate). No kind-3
step.
