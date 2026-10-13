# mapping.md — django__django-12774

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 67f9d076cfc1858b94f9ed6d1a5ce2327dcc8d0d`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each callee. This bundle has **no consumed axioms and no
deep-model reference to a foreign library callee** (G-AX is skip — see §3).

Repo file under change: `django/db/models/query.py` (the `in_bulk` validation
guard, body lines 689–700 post-patch).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `validateLookupField (fieldName) (fieldUnique) (constraints)` | the lookup-field validation guard of `QuerySet.in_bulk` — `django/db/models/query.py:684` (guard at body lines 688–691 pre-patch) | the modeled changed function: the decision whether the requested lookup field is rejected |
| `singleColumnFields (constraints : List (List String))` | the `unique_fields` list comprehension introduced by the patch (`query.py:692–696` post-patch) | pure spec: the field names that a *single-column* total uniqueness guarantee covers; the per-element expansion of the guarantee list |
| `inBulkValidate` (pure decision) | the boolean guard `field_name != 'pk' and not …unique and field_name not in unique_fields` → `raise ValueError` (post-patch) vs fall through | pure spec: the validation outcome (reject vs accept) |
| `fieldUnique : Bool` *(free input — owed no contract)* | `opts.get_field(field_name).unique` — `query.py:690`; `Field.unique` (`django/db/models/fields/__init__.py`) | unchanged callee; whether the requested field is *individually* declared unique. Modeled as a FREE Bool: the spec holds for every value of it, so it is strictly weaker than any concrete test (directive 7) — no axiom. |
| `constraints : List (List String)` *(free input)* | `opts.total_unique_constraints` — `django/db/models/options.py:832` (a list of `UniqueConstraint`; each `.fields` is the tuple of covered field names) | unchanged callee, computed pre-patch; the changed code only *consumes* its result. Modeled as a free input (the list of each constraint's `.fields`); no contract needed (directive 7). Provenance + behaviour confirmed by G-CONF against the real `total_unique_constraints`. |

The patched code computes `opts = self.model._meta` then iterates
`opts.total_unique_constraints`; `_meta` and `total_unique_constraints` are
**unchanged** (the property already existed at base_commit — see §3). The patch
adds only the `unique_fields` comprehension and the third `and` conjunct.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `field_name : str` | `String` | identity on character content; equality `field_name == 'pk'` ↔ `fieldName == "pk"` |
| the primary-key alias `'pk'` | the literal `"pk"` | the default `field_name` and the one value exempt from the guard; a pre-existing sentinel, not introduced by the patch |
| `opts.get_field(field_name).unique : bool` | `fieldUnique : Bool` | identity; the field's individual-uniqueness flag |
| `opts.total_unique_constraints : list[UniqueConstraint]` | `constraints : List (List String)` | each `UniqueConstraint` ↔ its `.fields` tuple (a list of field-name `str`); `len(c.fields)` ↔ `(c).length`; `c.fields[0]` ↔ the head of a singleton |
| `unique_fields : list[str]` | `singleColumnFields constraints : List String` | `str` list ↔ `List String`; `field_name not in unique_fields` ↔ `!(singleColumnFields constraints).contains fieldName` |
| `raise ValueError("…must be a unique field…")` | `Except.error ValidationErr.fieldNotUnique` | the one rejection outcome the guard distinguishes; reaching the body past the guard ↔ `Except.ok ()` |

`total_unique_constraints` returns only `UniqueConstraint`s with
`condition is None` (the "total" filter); conditional/partial constraints are
already excluded by that unchanged property, so they never appear in
`constraints`. Multi-column constraints DO appear but are filtered to
non-contributing by the `len(c.fields) == 1` test inside the comprehension —
modeled by `singleColumnFields` (only singletons contribute their sole field).

## 3. Callee provenance

### 3.1 `total_unique_constraints` (unchanged — free input, no axiom)
`Options.total_unique_constraints` (`django/db/models/options.py:832`) existed
at base_commit:
```python
@cached_property
def total_unique_constraints(self):
    return [
        constraint for constraint in self.constraints
        if isinstance(constraint, UniqueConstraint) and constraint.condition is None
    ]
```
The patch does not change it; it only reads its result. Modeled as the free
input `constraints`. No contract is asserted on it, so it is owed no axiom
(directive 7); its real behaviour (multi-column and conditional constraints) is
exercised by G-CONF, which builds real models and reads the real property.

### 3.2 `get_field(field_name).unique` (unchanged — free Bool, no axiom)
`Field.unique` is the field's individual-uniqueness flag, unchanged by the
patch. Modeled as the free Bool `fieldUnique`; the spec holds for both values,
so no contract is needed.

### 3.3 No consumed axiom, no deep-model reference
The behaviour this bundle pins — the validation *decision*, including the new
single-column-constraint allowance — is modeled DEEPLY in the `pure` region
(`singleColumnFields`, `inBulkValidate`). There is no module-level `axiom` and
no A-reference to a foreign library callee. **G-AX is therefore `skip`** (no
`axiom_check.py`); a stub `axiom_check.py` exits with `status=skip` for the
orchestrator. Soundness of the R/I model is audited by **G-CONF** against the
real patched guard.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`12774`** so the
consumer-side verdict is reproducible. The shadow transliterates
`singleColumnFields`/`inBulkValidate` (R/I-tagged ops) to Python; there are no
A-tagged callees in the impl region. The oracle builds real Django models with
`UniqueConstraint`s (single-column, multi-column, conditional) and calls the
real patched `in_bulk` validation, observing reject (`ValueError`) vs accept on
the DB-free legs (`id_list=[]` short-circuits to `{}` after the guard; an
invalid field raises before any DB access).
