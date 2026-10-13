# mapping.md — django__django-11820

Binds every `model.py` symbol to its repository counterpart at
`base_commit = c2678e49759e5c4c329bff0eeca2886267005d21`, states the type
abstraction, and gives the provenance of each modelled callee (source + the
behaviour the function encodes).

Repo file under change: `django/db/models/base.py`. The changed function is the
inner per-name walk of `Model._check_ordering` (the `for part in
field.split(LOOKUP_SEP)` loop, lines 1706-1723 at `base_commit`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `check_related_path(path, root)` | the inner loop of `Model._check_ordering` that walks one related ordering path — `django/db/models/base.py:1706-1723` | the modelled changed function: does walking one related path produce a `models.E015` validation error |
| `walk_err(path, model, fld_model, fld_name)` | the deep model of that loop's net effect (the post-fix semantics) | pure spec: the per-name fold producing the error verdict |
| `resolve_kind(model, name)` *(graph fn — A-reference)* | `Options.get_field(name)` + `Field.is_relation` — `django/db/models/options.py:get_field`, `django/db/models/fields/__init__.py:is_relation` | unchanged name-resolution: 0 if `get_field` raises `FieldDoesNotExist`, 1 if the found field `is_relation`, else 2 |
| `relation_target(model, name)` *(graph fn — A-reference)* | `fld.get_path_info()[-1].to_opts.model` — `django/db/models/base.py:1713` | unchanged related-model lookup: the model a relation field points at |
| `pk_kind(model)` *(graph fn — A-reference)* | `Options.pk` + `.is_relation` — `django/db/models/options.py:pk` | unchanged primary-key lookup: the `pk` alias resolves to `_meta.pk`; 1 if that field is a relation (e.g. a parent link), else 2 |
| `pk_target(model)` *(graph fn — A-reference)* | `_meta.pk.get_path_info()[-1].to_opts.model` | unchanged: model a relational pk points at |
| `transform_present(field_model, field_name, name)` *(graph fn — A-reference)* | `fld.get_transform(name) is not None` — `django/db/models/base.py:1715` | unchanged transform lookup: whether the last found field admits the trailing name as a registered lookup/transform |

The pre-fix repo behaviour the change replaces (audited in refinement.md, not
referenced from the consumer spec view): the inner loop called
`_cls._meta.get_field(part)` for every part (so the `pk` alias raised
`FieldDoesNotExist`) and never reset `_cls` after a non-relation field (so a
name following a non-relation field was re-resolved against the *same* model).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a related ordering path `str` (`"a__b__c"`), already split on `LOOKUP_SEP` into a `list[str]` of name parts | `path: List[int]` of name identifiers; spec over `PSeq[int]` via `ToSeq` | each distinct field-name string ↔ a distinct integer id; the literal alias string `'pk'` ↔ the reserved id `0`; `parts[k]` ↔ `path[k]`; `len(parts)` ↔ `len(path)` |
| a model class `_cls` | `int` model identifier | each model ↔ a distinct non-negative id; the running `_cls` value `None` ↔ the reserved model id `-1` (`None._meta` raises `AttributeError`, the same effect as "resolves to nothing") |
| the last field object `fld` | a `(fld_model: int, fld_name: int)` pair | `fld is None` ↔ `fld_name == -1`; otherwise the field is identified by the model it was found on and its name id (its `get_transform` behaviour is keyed on that pair) |
| the per-path verdict: `errors.append(E015)` was reached at least once for this path | `bool` (`Result()` / `walk_err`) | `True` ↔ the path contributes a `models.E015` error; `False` ↔ the path is a legitimate ordering target |

`str` indexing/iteration is banned in Nagini, so name parts are integer ids and
the path is carried as `List[int]` / `PSeq[int]`. The outer `_check_ordering`
loop over the related-field list and the (unchanged) error-message formatting
are not modelled — they are observationally the identity over the per-path
boolean the F2P/P2P tests assert (each test uses a single ordering path and
asserts the exact `[Error(...E015...)]` vs `[]` list).

## 3. Callee provenance (the graph functions — A-reference, checked by G-AX)

The five `@ContractOnly` functions in the axioms region model the **unchanged**
name-resolution machinery as *referentially transparent* functions over integer
ids. The proof does NOT consume any value-level `Ensures` from them beyond the
return-range facts (`resolve_kind ∈ {0,1,2}`, `pk_kind ∈ {1,2}`, targets ≥ 0,
`transform_present` a bool) needed for branch totality. They are the **graph
data** the deep fold `walk_err` ranges over; the *changed behaviour* — the `pk`
alias resolution and the "no model to continue from after a non-relation field"
reset — is modelled DEEPLY in `walk_err` / `check_related_path`, not behind any
of these functions. Hence they are **A-reference**: G-AX validates the deep
model against the real callees end-to-end, it does not consume a value axiom.

**Soundness check (G-AX):** `axiom_check.py` builds real Django model graphs for
the two F2P scenarios, four P2P-shaped scenarios, and three adversarial
scenarios, then (a) observes that the range facts hold when each function is
backed by the real callee (`Options.get_field`/`is_relation`/`Options.pk`/
`Field.get_path_info`/`Field.get_transform`), and (b) folds the deep model
`walk_err` over each related path using those real callees and asserts the
verdict EQUALS the real `Model._check_ordering` E015 verdict for that path. It
imports only `django` (the framework whose `_check_ordering` the gold patch
edits) and the standard library; exit 0 iff every observation matches.

Flag/configuration dependencies: none. The pk alias is the literal string
`'pk'` (Django hard-codes the `pk` alias, `django/db/models/options.py`); no
optional keyword arguments gate the modelled behaviour.

## 4. Conformance check (G-CONF)

`conformance_check.py` runs the contract-stripped impl region (shadow), with
the five graph functions backed by the real repo callees over an integer-id
bridge, against the real patched per-path E015 verdict of
`Model._check_ordering` on >= 1e5 inputs (curated boundary paths + fuzz over
six concrete scenario graphs). Pinned fuzz seed: **11820** (the instance
number).

## 5. Termination obligation

`check_related_path` carries `Requires(MustTerminate(2))`: the real inner walk
is a bounded `for part in field.split(LOOKUP_SEP)` loop over the finitely many
parts of one ordering path — it always completes and delivers its per-path
verdict to `_check_ordering` (which the checks framework then surfaces as the
`[Error(...E015...)]` vs `[]` list the tests assert). Nagini verifies partial
correctness by default, so without this obligation a diverging implementation
would satisfy the value postcondition vacuously while never producing the
verdict the real function always produces. The loop discharges the obligation
with the strictly decreasing measure `n - i`.
