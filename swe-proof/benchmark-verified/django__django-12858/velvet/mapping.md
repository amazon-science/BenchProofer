# mapping.md — django__django-12858

Symbol binding, the Lean↔Python type bijection (used by G-CONF), callee
provenance, and the pinned G-CONF fuzz seed. Spec provenance: **cold** (derived
only from `problem_statement`, the gold `patch`, and the repo source at
`base_commit`).

Repo file under change: `django/db/models/base.py`.

## 1. The modeled function

| Lean | Python | location @ base_commit |
|---|---|---|
| `checkOrderingRef` | the per-reference body of the `for field in related_fields:` loop inside `Model._check_ordering` | `django/db/models/base.py:1709` (method `_check_ordering`); inner walk at `:1735-1758` |

`_check_ordering` validates every entry of `Meta.ordering`. The patch touches
ONLY the `except (FieldDoesNotExist, AttributeError):` branch of the inner walk
that resolves a single **related** ordering reference (one that contains the
`__` lookup separator) part-by-part across the schema graph and decides whether
to raise `models.E015` for it. `checkOrderingRef` models that inner walk: given
the chain of parts of ONE reference and the schema accessors, it returns whether
the reference is judged invalid (an E015-style report is raised for it).

The surrounding scaffolding of `_check_ordering` (splitting `ordering` into
related vs non-related entries, stripping `-`, the `'?'` filter, the later
`fields - valid_fields` non-related check, building the `checks.Error` object,
the `pk` set-comprehension filter on NON-related fields) is **unchanged** by the
patch and is out of scope; only the related-reference walk's invalidity decision
changes.

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
| `hasTransform : Field → Part → Bool` | `fld.get_transform(part) is not None` (a registered transform of the last resolved field) |
| `hasLookup : Field → Part → Bool` | `fld.get_lookup(part) is not None` (a registered lookup of the last resolved field) — **the accessor newly consulted by the fix** |
| `parts.foldl stepWalk (initState cls0)` | the `for part in field.split(LOOKUP_SEP):` loop, threading `(_cls, fld, raised?)` |

The walk's four accessors are taken as **FREE INPUTS** (no axioms): the spec
makes no behavioural claim about how a schema resolves a name, what a model's
identity field is, or which transforms/lookups are registered — it holds for
EVERY schema. The decision under spec is purely *how those accessors are threaded
across the chain of parts*, which is what the patch changes.

## 3. Callee provenance (all UNCHANGED by the patch — hence free inputs, no G-AX)

| accessor | real callee | unchanged? |
|---|---|---|
| `lookup` | `Options.get_field` (`django/db/models/options.py`) | yes — same call both pre/post-patch |
| `aliasField` | `Options.pk` (the model's primary key field) | yes — same call both pre/post-patch |
| `hasTransform` | `Field.get_transform` (`django/db/models/query_utils.RegisterLookupMixin`) | yes — same call both pre/post-patch |
| `hasLookup` | `Field.get_lookup` (`django/db/models/query_utils.RegisterLookupMixin`) | yes — pre-existing accessor; the patch only *starts consulting* it in the except-branch |
| relation descent | `fld.get_path_info()[-1].to_opts.model` | yes — unchanged |

None of these callees is changed by the patch. `get_lookup` is a pre-existing
method (a sibling of `get_transform` on the same registry mixin); the patch does
not change `get_lookup`, it only adds a *call* to it inside the invalidity
decision. So none is axiomatized; they are abstracted into the free inputs above.
There is therefore nothing for G-AX to check against a real callee
(`axiom_check.py` reports `status=skip`). The patch's content is entirely in the
control flow that threads them — modeled deeply and differential-tested by
G-CONF (§4).

## 4. The single fixed behavior (one failing prepatch)

The gold patch makes one control-flow correction to the except-branch invalidity
decision: a part that fails to resolve (`get_field` raised) is exempt from E015
if it is a registered **transform** of the last resolved field **OR** a
registered **lookup** of it — previously only a transform exempted it. In the
model, `flagOnUnresolved` clears the flag when `hasTransform f p || hasLookup f p`
(post-patch), vs `hasTransform f p` alone (pre-patch).

`Solution_prepatch.lean` inlines the buggy except-branch decision (clears only on
`hasTransform`, with NO `hasLookup` escape). For a part that is a registered
lookup-but-not-transform of the last field, the inlined step wrongly flags the
reference, while the frozen spec's `stepWalk` (via `flagOnUnresolved`, which also
clears on `hasLookup`) does not. The loop-body invariant
`st = (parts.take …).foldl stepWalk (initState cls0)` then becomes unprovable →
`prove_correct` fails (G-DIFF). Models the F2P
`test_ordering_pointing_to_lookup_not_transform` (`test__isnull` must NOT raise
E015; `isnull` is a registered lookup, not a transform).

One `Solution_prepatch.lean` because the patch fixes exactly one independently
observable behavior (SPEC_GUIDE §3 / G-DIFF).

## 5. G-CONF fuzz seed

`SEED = 12858`, `N_FUZZ = 100_000` (pinned, deterministic). The differential
test runs the R/I shadow of the `stepWalk` fold against an ORACLE that
transliterates the **gold-patched** walk verbatim, over random synthetic schemas
+ part chains (boundary chains first, incl. the F2P `test__isnull` scenario).
See `conformance_check.py`.
