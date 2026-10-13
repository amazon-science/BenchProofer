# mapping.md — django__django-12774

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 67f9d076cfc1858b94f9ed6d1a5ce2327dcc8d0d`, states the type
abstraction, and gives the provenance of every callee the deep model is
validated against (G-AX / axiom_check.py).

Repo file under change: `django/db/models/query.py` (the single hunk in the
gold patch).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `should_reject(field_name, field_unique, guarantees)` | the field-name acceptability guard of `QuerySet.in_bulk(self, id_list=None, *, field_name='pk')` — `django/db/models/query.py:685` (the guard expression at body lines 692-693, the patched hunk) | the modeled changed decision: should `in_bulk` reject `field_name` with `ValueError("in_bulk()'s field_name must be a unique field ...")`? |
| `PK` (== 0) | the string `'pk'` and the model's primary-key field name (`self.model._meta.pk.name`); `in_bulk`'s default `field_name='pk'` | the distinguished primary-key identity that the guard always accepts |
| `field_unique` (bool param) | `opts.get_field(field_name).unique` — `Options.get_field` at `django/db/models/options.py:554`, `Field.unique` attribute | whether the looked-up field is individually unique; an UNCHANGED callee, passed in as data |
| `guarantees: List[Tuple[bool, PSeq[int]]]` | `opts.total_unique_constraints` — `Options.total_unique_constraints` at `django/db/models/options.py:832` (a `@cached_property`); each element a `UniqueConstraint` | the model's declared total (unconditional) uniqueness constraints; an UNCHANGED property, modeled as a value list |
| `g[0]` (a guarantee's `unconditional` flag) | `constraint.condition is None` — `UniqueConstraint.condition` set at `django/db/models/constraints.py:79` | True iff the constraint applies to every row (carries no condition). NOTE: `total_unique_constraints` ALREADY filters to `condition is None`, so every element passed in is unconditional; the flag is carried explicitly to keep the model 1:1 with the patch and to let the model also represent (and reject) any conditional element. |
| `g[1]` (a guarantee's `names`) | `constraint.fields` (a tuple of field-name strings) — `UniqueConstraint.fields` set at `django/db/models/constraints.py:78` | the field names the constraint ranges over |
| `permits_alone(g, field_name)` | the patch's per-constraint filter `len(constraint.fields) == 1` combined with `constraint.fields[0]` and the `field_name not in unique_fields` membership | pure spec: does this guarantee make `field_name` acceptable on its own (single-field + unconditional + that field == `field_name`)? |
| `any_permits(guarantees, 0, field_name)` | the patch's `field_name not in unique_fields`, where `unique_fields = [c.fields[0] for c in opts.total_unique_constraints if len(c.fields) == 1]` | pure spec: is `field_name` the sole field of SOME total unique constraint? |

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| field-name `str` (e.g. `'year'`, `'pk'`, `'brand'`) | `int` identity | distinct field names ↔ distinct integers; only *equality* of names is used by the guard (`field_name != 'pk'`, `field_name not in unique_fields`, `constraint.fields[0] == field_name`), so any injective name→int encoding is faithful. `'pk'` and the model's pk field name both map to the distinguished identity `PK`. |
| `'pk'` literal / pk default / `opts.pk.name` | `PK` (== 0) | the guard's primary-key short-circuit `field_name != 'pk'` ↔ `field_name == PK`; a pk lookup never reaches `get_field` (short-circuit), mirrored by the model's first early return. |
| `UniqueConstraint` object | `Tuple[bool, PSeq[int]]` = `(condition is None, [ord-ids of fields])` | only the two touched attributes (`condition`, `fields`) participate in the guard; reduced to an immutable value pair (no object-field heap permissions needed). `len(constraint.fields)` ↔ `len(g[1])`; `constraint.fields[0]` ↔ `g[1][0]`. |
| `opts.total_unique_constraints` (a `list`) | `List[Tuple[bool, PSeq[int]]]` (read-only, `Acc(list_pred(...), 1/2)`) | the property is read, never mutated; modeled at fractional permission per directive 5. |
| `opts.get_field(field_name).unique` (bool) | the `field_unique: bool` parameter | the field's individual-unique flag, an unchanged callee value; passed in (the guard reads it, does not compute it). |
| raising `ValueError(...)` | `should_reject` returns `True` | the decision is the modeled object; the actual `raise` is the I-identical control-flow consequence in `patch.diff` (refinement.md A4). The model returns the boolean the `if (...)` evaluates to. |

`str` indexing/iteration is banned in Nagini; field-name identity is the only
operation, so field names are modeled as `int` identities and the constraint's
field list as `PSeq[int]`.

## 3. Callee provenance (validated by G-AX / axiom_check.py)

There are **no consumed `@ContractOnly` axioms** in this bundle: the substance of
the change — deriving the single-field total-unique fields and testing
membership — is modeled DEEPLY (`permits_alone` + the front-recursive fold
`any_permits` + the `should_reject` decision). The unchanged callees the patch
uses are validated as **A-references** (the deep model is checked == reality):

### 3.1 `any_permits` / `permits_alone` deep model ↔ `total_unique_constraints` + the patch's `unique_fields` derivation (A-reference)
**Callees (all UNCHANGED by the patch):**
- `Options.total_unique_constraints` (`django/db/models/options.py:832`):
  ```python
  @cached_property
  def total_unique_constraints(self):
      return [
          constraint
          for constraint in self.constraints
          if isinstance(constraint, UniqueConstraint) and constraint.condition is None
      ]
  ```
  i.e. the `UniqueConstraint`s whose `condition is None` (the unconditional /
  "total" ones — they hold for every row, unlike conditional/partial ones).
- The patch's single-field extraction `unique_fields = [c.fields[0] for c in
  opts.total_unique_constraints if len(c.fields) == 1]`.
- `UniqueConstraint.fields` / `UniqueConstraint.condition`
  (`django/db/models/constraints.py:78-79`).

The deep model encodes a guarantee as `(condition is None, fields)` and defines
`permits_alone(g, f) = g[0] and len(g[1]) == 1 and g[1][0] == f`, with
`any_permits` the existential fold. This is exactly
`f in [c.fields[0] for c in total_unique_constraints if len(c.fields) == 1]`
restricted to the unconditional constraints. `axiom_check.py` (G-AX) constructs
real Django models with single-field-unconditional, conditional (partial),
multi-field, and `unique=True` configurations and asserts the deep model's
`should_reject` equals the real guard on every field. Exit 0 iff sound.

### 3.2 `field_unique` ↔ `Field.unique` via `Options.get_field` (A-reference)
**Callee (UNCHANGED):** `Options.get_field(field_name)`
(`django/db/models/options.py:554`) returns the `Field`; `.unique` is its
individual-unique flag. The model takes this boolean as a parameter rather than
recomputing it; `axiom_check.py` reads the REAL `opts.get_field(fn).unique` when
forming each observation, so the A-reference check exercises the real callee.

**Flag/configuration dependency:** the patch and the model are sound for the
`condition is None` ⇔ unconditional semantics of `UniqueConstraint`. G-AX fuzzes
both the conditional (`condition=Q(...)`) and unconditional cases plus
single-field vs. multi-field, which is exactly the configuration space the F2P /
P2P tests cover (`test_in_bulk_meta_constraint`,
`test_in_bulk_non_unique_meta_constaint`, `test_in_bulk_non_unique_field`).
