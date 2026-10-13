# mapping.md — django__django-15732

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = ce69e34bd646558bb44ea92cecfd98b345a0b3e0`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each helper call.

Repo file under change: `django/db/backends/base/schema.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `chooseTarget (names) (uniqueSel) (allowMultiple) (canonical)` | the constraint-selection logic inside `BaseDatabaseSchemaEditor._delete_composed_index` — `django/db/backends/base/schema.py:559` (selection + raise body lines 565–582 post-patch) | the modeled changed function: decide the single constraint identifier to act on |
| `names : List String` | `constraint_names` — the result list of `self._constraint_names(model, columns, exclude=…, **constraint_kwargs)` (`schema.py:565-570`) | the candidate identifiers discovered for the target columns (opaque method input) |
| `uniqueSel : Bool` | `constraint_kwargs.get("unique") is True` (`schema.py:573` post-patch) | whether selection is by uniqueness (True for the unique_together-delete caller) |
| `allowMultiple : Bool` | `self.connection.features.allows_multiple_constraints_on_same_fields` (`schema.py:575`) | whether the backend permits several constraints on the same fields |
| `canonical : String` | `default_name = str(self._unique_constraint_name(model._meta.db_table, columns, quote=False))` (`schema.py:577-579`) | the identifier the unique_together naming scheme assigns to these columns (opaque method input) |
| `out : Option String` | `constraint_names[0]` when `len(constraint_names) == 1`, else the `ValueError` path (`schema.py:580-590`) | the single target to act on, or "no unique target" (the raise) |

The pre-patch repo behaviour the change replaces (refinement audit only): the
selection had no narrowing step — `constraint_names` flowed straight into the
`len(...) != 1` check (`schema.py:580` pre-patch), so a column carrying both a
standalone unique constraint and a unique_together constraint yielded two
candidates and raised `ValueError`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `constraint_names` (a Python `list[str]`) | `names : List String` | element-wise `str` ↔ `String`; `len(l)` ↔ `l.length`; order preserved; empty list ↔ `[]` |
| a constraint identifier (`str`) | `String` | identity on character content |
| `constraint_kwargs.get("unique") is True` (`bool`) | `uniqueSel : Bool` | `True ↔ true`, anything else ↔ `false` |
| `features.allows_multiple_constraints_on_same_fields` (`bool`) | `allowMultiple : Bool` | `True ↔ true`, `False ↔ false` |
| `default_name` (`str`) | `canonical : String` | identity on character content |
| `constraint_names[0]` / the `ValueError` raise | `Option String` | `some n` ↔ "act on `n`" (`len==1`); `none` ↔ "wrong number ⇒ raise" |

Membership `canonical ∈ names` (Lean) ↔ `default_name in constraint_names`
(Python) — Python's `in` on a list is element equality, the same as Lean
`List.Mem` over `String`. `narrowed`'s replacement `[canonical]` (Lean) ↔ the
gold `constraint_names = [default_name]` (Python).

## 3. Callee provenance (helper calls — taken as opaque inputs, NOT axiomatized)

The changed function `_delete_composed_index` calls three helpers; the change
does NOT modify any of them, and the new behaviour does not depend on any
property of their outputs beyond their *values*, which are passed in as the
method's parameters. There is therefore **no consumed axiom and no A-reference
deep model** — the contract holds for every possible helper output.

- `_constraint_names(model, columns, exclude, **constraint_kwargs)` →
  `names`. `schema.py:1037` (def). Unchanged. Returns the list of matching
  constraint identifiers; modeled as the opaque `names` parameter.
- `_unique_constraint_name(table, columns, quote=False)` → `canonical`. This
  helper is *introduced* by the gold patch (`schema.py:1606-1616`) by extracting
  the pre-existing `IndexName(table, columns, "_uniq", create_unique_name)`
  naming expression out of `_create_unique_sql`. Its `quote=False` value is the
  unquoted canonical unique_together name for the columns — a pure function of
  `(table, columns)`. Modeled as the opaque `canonical` parameter. (Its
  extraction is a pure refactor whose behaviour-bearing use is here; see
  refinement.md §B.)
- `allows_multiple_constraints_on_same_fields` — a backend feature flag
  (`django/db/backends/base/features.py:296`, default `True`; `False` on Oracle).
  Modeled as the opaque `allowMultiple` parameter; the F2P test is guarded by
  `@skipUnlessDBFeature("allows_multiple_constraints_on_same_fields")`, i.e. it
  runs with `allowMultiple = true`. Recorded here per SPEC_GUIDE §3 flag-dep.

Because every helper result is consumed only as a value (no behavioural
contract is assumed), **`axiom_check.py` (G-AX) is vacuous** and exits 0 after
asserting there are no axioms/A-references to validate (meta.json records the
empty axiom set).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15732`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`narrowed`/`selectedTarget` (all R/I-tagged ops) to Python and compares against
the gold `_delete_composed_index` selection logic over the same fuzzed
`(names, uniqueSel, allowMultiple, canonical)` tuples. There are no A-tagged
callees in the impl region, so the shadow is pure R/I (conf_skip = false).
