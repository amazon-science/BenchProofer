# mapping.md — django__django-11820

Symbol binding, the Lean↔Python type bijection (used by G-CONF), callee
provenance, and the pinned G-CONF fuzz seed. Spec provenance: **cold** (derived
only from `problem_statement`, the gold `patch`, and the repo source at
`base_commit`).

## 1. The modeled function

| Lean | Python | location @ base_commit |
|---|---|---|
| `checkOrderingRef` | the per-reference body of the `for field in related_fields:` loop inside `Model._check_ordering` | `django/db/models/base.py:1660` (method), inner walk at `:1705-1721` |

`_check_ordering` validates every entry of `Meta.ordering`. The patch touches
ONLY the inner walk that resolves a single **related** ordering reference (one
that contains the `__` lookup separator) part-by-part across the schema graph
and decides whether to raise `models.E015` for it. `checkOrderingRef` models
that inner walk: given the chain of parts of ONE reference and the schema
accessors, it returns whether the reference is judged invalid (an E015-style
report is raised for it).

The surrounding scaffolding of `_check_ordering` (splitting `ordering` into
related vs non-related entries, stripping `-`, the `'?'` filter, the later
`fields - valid_fields` non-related check, building the `checks.Error` object,
the `pk` set-comprehension filter on NON-related fields) is **unchanged** by the
patch and is out of scope; only the related-reference walk changes.

## 2. The type bijection (Lean ↔ Python), used by G-CONF

| Lean | Python (real repo type) |
|---|---|
| `Model = Nat` | a model class / `Options` (`_cls`); only identity matters, modeled as an opaque id |
| `Field` = `{ isRel : Bool, relModel : Model }` | a resolved `Field`; `isRel ↔ fld.is_relation`; `relModel ↔ fld.get_path_info()[-1].to_opts.model` (the model the relation descends into) |
| `Part` = `{ name : Nat, isAlias : Bool }` | one `part` of `field.split(LOOKUP_SEP)`; `isAlias ↔ (part == 'pk')` |
| `Option Model` (`cur`) | `_cls` (a model) or `None` (off the model graph) |
| `Option Field` (`last`) | `fld` (a resolved field) or `None` (the `fld = None` seed) |
| `Bool` (`flag`) | "a `checks.Error(... id='models.E015')` was appended for this reference" |
| `lookup : Model → Part → Option Field` | `_cls._meta.get_field(part)`: `some f` if it resolves, `none` if it raises `FieldDoesNotExist` |
| `aliasField : Model → Field` | `_cls._meta.pk` (the identity field of the model) |
| `hasTransform : Field → Part → Bool` | `fld.get_transform(part) is not None` (a registered lookup/transform of the last resolved field) |
| `parts.foldl stepWalk (initState cls0)` | the `for part in field.split(LOOKUP_SEP):` loop, threading `(_cls, fld, raised?)` |

The walk's three accessors are taken as **FREE INPUTS** (no axioms): the spec
makes no behavioural claim about how a schema resolves a name, what a model's
identity field is, or which transforms are registered — it holds for EVERY
schema. The decision under spec is purely *how those accessors are threaded
across the chain of parts*, which is what the patch changes.

## 3. Callee provenance (all UNCHANGED by the patch — hence free inputs, no G-AX)

| accessor | real callee | unchanged? |
|---|---|---|
| `lookup` | `Options.get_field` (`django/db/models/options.py`) | yes — same call both pre/post-patch |
| `aliasField` | `Options.pk` (the model's primary key field) | yes — only *whether it is consulted* changes |
| `hasTransform` | `Field.get_transform` (`django/db/models/lookups.py` registry) | yes — same call both pre/post-patch |
| relation descent | `fld.get_path_info()[-1].to_opts.model` | yes — only *when* it is taken changes |

None of these callees is changed by the patch, so none is axiomatized; they are
abstracted into the free inputs above. There is therefore nothing for G-AX to
check against a real callee (`axiom_check.py` reports `status=skip`). The patch's
content is entirely in the control flow that threads them — modeled deeply and
differential-tested by G-CONF (§4).

## 4. The two fixed behaviors (each gets a failing prepatch)

The gold patch makes two independent control-flow corrections to the walk:

1. **pk alias** — a part equal to `'pk'` is resolved via `_cls._meta.pk` instead
   of `_cls._meta.get_field('pk')` (which raises, because `pk` is an alias not a
   real field). `Solution_prepatch_1.lean` drops the alias branch (always uses
   `lookup`), so the alias part wrongly fails to resolve → flagged → fails the
   frozen `stepWalk` invariant. Models the F2P
   `test_ordering_pointing_to_related_model_pk` (`parent__pk` must NOT raise).
2. **non-relation terminates the descent** — after resolving a NON-relation
   field, `_cls` is set to `None`, so a FOLLOWING part has no model to resolve
   against and the reference is flagged. `Solution_prepatch_2.lean` leaves `_cls`
   at the current model after a non-relation field (the pre-patch behavior: the
   `if fld.is_relation:` block simply fell through), so a following part
   spuriously resolves against the same model → not flagged → fails the frozen
   `stepWalk` invariant. Models the F2P
   `test_ordering_pointing_multiple_times_to_model_fields`
   (`parent__field1__field2` MUST raise).

Two `Solution_prepatch_*` files because the two are independently observable
fixed behaviors (SPEC_GUIDE §3 / G-DIFF).

## 5. G-CONF fuzz seed

`SEED = 11820`, `N_FUZZ = 100_000` (pinned, deterministic). The differential
test runs the R/I shadow of the `stepWalk` fold against an ORACLE that
transliterates the **gold-patched** walk verbatim, over random synthetic schemas
+ part chains (boundary chains first). See `conformance_check.py`.
