# mapping.md — symbol binding & type bijection (django__django-15732)

## Modeled function
- **Lean** `implementation_selectUniqueToDrop : List String → Bool → Bool → String → Except Unit String`
- **Python** the constraint-selection decision inside
  `BaseDatabaseSchemaEditor._delete_composed_index`
  (`django/db/backends/base/schema.py:559` @ base_commit `ce69e34`), specifically
  the post-patch block at lines 565–588 of the patched file:

  ```python
  constraint_names = self._constraint_names(model, columns,
      exclude=meta_constraint_names | meta_index_names, **constraint_kwargs)
  if (constraint_kwargs.get("unique") is True
          and constraint_names
          and self.connection.features.allows_multiple_constraints_on_same_fields):
      default_name = str(self._unique_constraint_name(model._meta.db_table, columns, quote=False))
      if default_name in constraint_names:
          constraint_names = [default_name]
  if len(constraint_names) != 1:
      raise ValueError("Found wrong number (%s) of constraints for %s(%s)" % ...)
  self.execute(self._delete_constraint_sql(sql, model, constraint_names[0]))
  ```

The observable behavior the F2P tests demand is exactly this decision: given the
candidate constraint identifiers discovered for the target columns, decide which
single identifier to drop, or signal "wrong number of constraints". The patch
adds a narrowing step so a duplicate uniqueness constraint over the same columns
no longer forces the error.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `constraint_names` (`list[str]`, output of `self._constraint_names(...)`) | `candidates : List String` | the discovered constraint identifiers, order preserved |
| `constraint_kwargs.get("unique") is True` | `isUnique : Bool` | whether the deletion targets a UNIQUE constraint (`alter_unique_together` passes `{"unique": True, ...}`) |
| `self.connection.features.allows_multiple_constraints_on_same_fields` | `allowsMultiple : Bool` | backend capability flag |
| `str(self._unique_constraint_name(db_table, columns, quote=False))` | `defaultName : String` | the canonical, unquoted identifier the schema generator assigns to a composite-uniqueness constraint over these columns |
| `raise ValueError(...)` (wrong-number-of-constraints) | `Except.error ()` | the operation cannot decide |
| `self._delete_constraint_sql(sql, model, constraint_names[0])` reaching a single name | `Except.ok n` | the single identifier selected for deletion; we model the selection, not the SQL-string rendering (an I-tagged downstream wrapper) |

## Callee provenance
- `self._constraint_names(...)` — UNCHANGED by the patch. Its **output** is the
  free input `candidates`; we do NOT model the name-discovery itself and do NOT
  axiomatize it (no property of it is consumed: the spec is quantified over all
  possible outputs). It introspects the DB introspection layer; modeling it is
  out of scope and unnecessary for the graded behavior.
- `self._unique_constraint_name(table, columns, quote=False)` — INTRODUCED by the
  patch (a refactor of the previously-inline `IndexName(table, columns, "_uniq",
  create_unique_name)`). It deterministically produces the canonical constraint
  identifier; its **output** is the free input `defaultName`. We model the
  *decision that uses it*, not the identifier-rendering algorithm (string
  hashing of column names is incidental to the graded behavior and is an I/R
  wrapper). No property of it is consumed by the proof.
- `self._delete_constraint_sql(...)` / `self.execute(...)` — UNCHANGED downstream
  rendering + side effect; identity wrappers on the selected identifier, not
  modeled (I-tagged).

No UNCHANGED callee is consumed as an axiom; the axioms region is empty. The
spec is universally quantified over `candidates` / `defaultName` / both flags, so
correctness holds for every value any real helper could return — there is nothing
to axiomatize.

## Flag dependency
The narrowing branch fires only when `isUnique = True` AND `allowsMultiple =
True` AND `candidates` is nonempty AND `defaultName ∈ candidates`. The F2P tests
are gated `@skipUnlessDBFeature("allows_multiple_constraints_on_same_fields")`,
i.e. they exercise `allowsMultiple = True`; `alter_unique_together` always passes
`unique=True` on the delete path, i.e. `isUnique = True`. G-CONF fuzzes all four
inputs (both flags over {True,False}) so every branch is covered.

## G-CONF fuzz seed
Pinned seed: **15732**. ≥10^5 fuzzed inputs over candidate lists drawn from a
small identifier alphabet (so `defaultName ∈ candidates` is hit frequently),
list lengths 0–4, and both flags ranging over {True, False}.
