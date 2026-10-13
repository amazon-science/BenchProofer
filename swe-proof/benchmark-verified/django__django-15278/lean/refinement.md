# refinement.md — django__django-15278

Maps every operation in `implementation_requiresTableRebuild` to its
`patch.diff` counterpart. Tags: **R** (type refinement), **A-consumed** (proof
uses an axiom's property), **A-reference** (deep model validated == real callee
by G-AX), **I** (identical concrete op). Every step is R, A, or I.

## Modeled function: `requiresTableRebuild` (the `add_field` routing decision)

Post-patch repo code (`patch.diff`), the routing decision at the head of
`DatabaseSchemaEditor.add_field`:

```python
if (
    field.primary_key or field.unique or
    not field.null or self.effective_default(field) is not None
):
    self._remake_table(model, create_field=field)
else:
    super().add_field(model, field)
```

Lean impl (`implementation_requiresTableRebuild`):

```lean
def implementation_requiresTableRebuild (c : ColumnProps) : Bool := Id.run do
  if c.isPrimaryKey || c.isUnique || !c.allowsNull || c.hasStoredDefault then
    return true
  return false
```

| # | Lean op | patch.diff / real-code counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `c.isPrimaryKey` | `field.primary_key` | **R** | boolean field ↔ field attribute; identity bijection (mapping.md). |
| 2 | `c.isUnique` | `field.unique` | **R** | boolean field ↔ field attribute; identity bijection. `OneToOneField` forces this `True`. |
| 3 | `!c.allowsNull` | `not field.null` | **R** | boolean negation of the nullability attribute; `!` ↔ Python `not`. |
| 4 | `c.hasStoredDefault` | `self.effective_default(field) is not None` | **R** | the whole `is not None` test is abstracted into one boolean observation; `effective_default`'s computation is unchanged by the patch and not the modeled decision, so it is carried as input, not recomputed. |
| 5 | `... || ... || ... || ...` | `... or ... or ... or ...` | **I** | the four-way disjunction; `||` ↔ Python short-circuit `or` (no side effects in either operand at this point, so truth value is identical). **This is the fixed decision**: the two leading disjuncts `isPrimaryKey \|\| isUnique` correspond exactly to the `field.primary_key or field.unique` the patch prepends. |
| 6 | `if ... then return true; return false` | `if (...): _remake_table(...) else: super().add_field(...)` | **I** (deep model of the changed branch) | the boolean result IS the branch selector: `true` ⇔ reconstruct (`_remake_table`), `false` ⇔ plain in-place add (`super().add_field`). The downstream branch bodies are unchanged by the patch and abstracted away (mapping.md output bijection); only which branch is taken is the observable change. |

All impl-region ops are **R/I** — there is NO A-tagged (axiom) content, so the
impl is NOT all-A-tagged: `conf_skip = false`, and `conformance_check.py`
mechanically differential-tests the R/I shadow against an in-process replica of
the post-patch decision.

## Soundness check (verify ⟹ correct)

- `problem_spec_requiresTableRebuild c result := result = (c.isPrimaryKey ||
  c.isUnique || !c.allowsNull || c.hasStoredDefault)` pins the result EXACTLY
  (full boolean equality to an input-grounded expression) — directive 5 (frame):
  the output is fully determined by the four column properties; no component is
  unconstrained, and there is no ungrounded oracle (directive 8) — the
  postcondition is dischargeable only by actually computing the disjunction over
  the input's properties. Each of the four disjuncts is an independent forcing
  condition, so no wrong impl that drops one (e.g. the prepatch, which drops
  `isPrimaryKey || isUnique`) can satisfy the spec.
- The prepatch impl reproduces the pre-patch decision `!c.allowsNull ||
  c.hasStoredDefault` (omitting the two leading disjuncts). It violates the spec
  on the discriminating clause `isUnique = true, allowsNull = true, isPrimaryKey
  = false, hasStoredDefault = false`: the impl returns `false`, the spec requires
  `true`. (Symmetrically for `isPrimaryKey = true` alone.) Its carried gold proof
  cannot close (G-DIFF/G-PANEL).
- This discriminating case is precisely what the FAIL_TO_PASS test
  `test_add_field_o2o_nullable` exercises: a `OneToOneField(Note, CASCADE,
  null=True)` — `unique=True` (forced by `OneToOneField`), `null=True`, not a
  primary key, no stored default. Pre-patch the decision is `false` so the plain
  in-place column addition is attempted and fails ("Cannot add a UNIQUE
  column"); post-patch the decision is `true` so the table is reconstructed and
  the column is materialized.
- G-CONF confirms the R/I shadow == the in-process replica of the patched
  decision over all 16 exhaustive 4-bit assignments plus ≥1e5 fuzzed
  boolean 4-tuples (zero disagreements).
