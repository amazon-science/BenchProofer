# mapping.md — django__django-16938

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 1136aa5005f0ae70fea12796b7e37d6f027b9263`, states the type
abstraction, and gives the provenance of each modeled callee (source + the exact
behaviour the model encodes).

Repo files under change (two identical hunks, one per serializer backend):
* `django/core/serializers/python.py` — `Serializer.handle_m2m_field`, nested
  `queryset_iterator` (body line 82 @ base_commit).
* `django/core/serializers/xml_serializer.py` — `Serializer.handle_m2m_field`,
  nested `queryset_iterator` (body line 158 @ base_commit).

Both hunks are byte-identical edits of the same nested helper; they are modeled
by the single function `build_pk_iterator` (the per-function marker regions are
module-level singletons, so one modeled function stands for the two identical
sites; see refinement.md §A/§B).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `build_pk_iterator(base, pk)` | the nested `queryset_iterator(obj, field)` in `handle_m2m_field` — `python.py:81-82` and `xml_serializer.py:157-158` | the modeled changed function: build the by-reference (pk-only) iterator for a related m2m collection |
| `Fetch(restricted, requested, members, listed, excluding)` | the related-collection `QuerySet` (`getattr(obj, field.name)` — the m2m `RelatedManager`'s queryset) and its `query` state | minimal class: only the touched query facets |
| `Fetch.restricted` | `isinstance(qs.query.select_related, dict)` (`django/db/models/sql/query.py:213,2264-2272`; the compiler reads it as `restricted = isinstance(self.query.select_related, dict)`, `compiler.py:1184`) | whether a *specific* set of adjacent records is requested for eager co-selection |
| `Fetch.requested` | the keys of the `query.select_related` dict (the requested adjacent-record fields) | the named adjacent-record fields |
| `Fetch.members` | the primary keys of the collection members the fetch addresses (the real m2m membership of the owning row) | which records are referenced |
| `Fetch.listed` / `Fetch.excluding` | the projection **as the query state holds it**: the `query.deferred_loading` pair `(field_names, defer)` (`django/db/models/sql/query.py:2311-2358`) — `listed` is the explicitly listed field codes, `excluding` says the list is the codes to leave OUT | the projection, in its own representation; an EMPTY `listed` imposes no restriction (every code loads) |
| `clear_specific_request(q)` | `QuerySet.select_related()` called with **no arguments** (`django/db/models/query.py:1546-1568`; `else: obj.query.select_related = True`) | resets the eager-co-selection request to its unrestricted default (`select_related` becomes the bool `True`, i.e. NOT a dict) |
| `only_pk(q, pk)` | `QuerySet.only("pk")` (`django/db/models/query.py:1728-1747` → `query.add_immediate_loading(("pk",))`) | narrows the projection to the single primary-key field |
| `ill_formed(restricted, requested, listed, excluding, pk)` (with the helper `dropped(listed, excluding, pk, f)`) | the evaluation-time descend check `select_related_descend` (`django/db/models/query_utils.py:315-351`), specifically its raise branch (lines 341-350): `restricted and select_mask and field.name in requested and field not in select_mask → raise FieldError(... "cannot be both deferred and traversed using select_related ...")` | the deep model of the unchanged check that decides whether the fetch errors |

The pre-patch repo behaviour the change targets (for the refinement audit, not
referenced from the consumer spec view): a related m2m manager whose custom
`get_queryset()` bakes in `select_related("<adjacent>")` makes
`query.select_related` a dict; the pre-patch chain `getattr(...).only("pk")`
then narrows the projection to drop that adjacent record, so at evaluation
`select_related_descend` raises `FieldError` (`"Field <Model>.<adjacent> cannot
be both deferred and traversed using select_related at the same time."`). This
is the regression reported in the issue.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| related-collection `QuerySet` + its `query` | `Fetch` (a 5-field class) | only the touched facets are carried; QuerySet methods return new clones (`_chain()`), so each op is modeled as producing a NEW `Fetch` (faithful to the immutable-clone chaining) |
| `query.select_related` being a `dict` vs a `bool` | `Fetch.restricted: bool` | `restricted == isinstance(query.select_related, dict)` — the exact flag the compiler computes (`compiler.py:1184`) |
| keys of the `select_related` dict (requested adjacent-record fields) | `Fetch.requested: PSet[int]` | each requested field name ↔ a distinct field code (int); set membership ↔ `name in requested` |
| `query.deferred_loading == (field_names, defer)` | `Fetch.listed: PSet[int]` + `Fetch.excluding: bool` | each listed field name ↔ a field code; `excluding == defer`. The projection is carried in the representation the query state ITSELF uses, NOT collapsed to an effective column set. This is load-bearing: `Query.add_immediate_loading` (`sql/query.py:2336-2358`) branches on `defer`, so a defer-mode and an only-mode query with the same effective columns react differently to a later narrowing. A collapsed `loaded` encoding maps a plain base and a `defer(pk)` base to the SAME abstract state while the real code distinguishes them, so it cannot be a faithful bridge. |
| the effective column set the projection loads (`query.get_select_mask()`; empty ⇒ no restriction ⇒ all columns) | derived, via the model's own `dropped` predicate: `{f : not dropped(listed, excluding, pk, f)}` | the *meaning* of the projection, checked separately from its representation (G-CONF diffs both) |
| the m2m membership of the owning row | `Fetch.members: PSet[int]` | each member primary key ↔ itself |
| the primary-key field "pk" | the int `pk` (a field code) | `"pk"` ↔ `pk`; the pk is never dropped by a projection (`dropped` returns False for it), matching `_get_defer_select_mask`/`_get_only_select_mask` which both unconditionally seed `select_mask[opts.pk]` (`sql/query.py:729-796`) |
| `.iterator()` (terminal of the chain) | omitted (identity) | `iterator()` only changes the fetch *strategy*, not the well-formedness facets the issue concerns; the FieldError is raised during SQL setup, which `iterator()` does not alter |
| `getattr(obj, field.name)` (the accessor that yields the base collection) | the `base: Fetch` argument | the accessor is refined to its result state; its possible baked-in `select_related` request is exactly the arbitrary `base.restricted`/`base.requested` the precondition admits |

`str` field names are never indexed in the model (Nagini bans `str` indexing);
field identities are abstracted to distinct integer codes and sets thereof.

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

There is **no consumed `@ContractOnly` axiom**: every operation the build chains
is modeled DEEPLY as a state transition or predicate over the touched facets.
The deep models stand for these unchanged Django callees and are validated equal
to them out-of-band by `axiom_check.py` (G-AX):

### 3.1 `clear_specific_request` ↔ `QuerySet.select_related()` (no args)
`django/db/models/query.py:1546-1568`. With no positional fields the `else`
branch runs: `obj.query.select_related = True`. Because `True` is a bool (not a
dict), the compiler's `restricted = isinstance(self.query.select_related, dict)`
becomes `False`. The deep model encodes exactly this: `Result().restricted ==
False`, projection unchanged. (Note: the literal `None` argument also clears, to
`False`; the patch uses the no-arg form, which sets `True`. Both yield a non-dict
`select_related`, hence `restricted == False` — the only facet that matters.)

### 3.2 `only_pk` ↔ `QuerySet.only("pk")`
`django/db/models/query.py:1728-1747` → `query.add_immediate_loading(("pk",))`,
whose body is (`sql/query.py:2336-2358`):
```python
existing, defer = self.deferred_loading
field_names = set(field_names)            # {"pk"} -> {<pk name>}
if defer:
    self.deferred_loading = field_names.difference(existing), False
else:
    self.deferred_loading = frozenset(field_names), False
```
So the result is ALWAYS a keep list (`defer` becomes `False`, i.e. the model's
`Result().excluding == False`), and the listed set is the named field MINUS what
was already on an incoming leave-out list. Two cases, both modeled:
* incoming projection is not a leave-out list carrying the pk ⇒ the list is
  exactly `{pk}` (`Result().listed == PSet(pk)`);
* incoming projection IS a leave-out list already carrying the pk ⇒ the
  difference is EMPTY, so `deferred_loading` becomes `(set(), False)`; an empty
  list imposes no restriction, hence `get_select_mask() == {}` and every column
  loads (`len(Result().listed) == 0`).
The eager-co-selection request is left untouched. The deep model's case split on
`q.excluding and pk in q.listed` is exactly this `difference` branch.

### 3.3 `ill_formed` ↔ `select_related_descend` (the raise branch)
`django/db/models/query_utils.py:341-350`:
```python
if (restricted and select_mask and field.name in requested
        and field not in select_mask):
    raise FieldError(... "cannot be both deferred and traversed using "
                     "select_related at the same time.")
```
i.e. the fetch errors exactly when restricted (a specific set is requested) AND
some requested field is excluded by the projection (in `requested`, not in the
select_mask). The deep model
`ill_formed(restricted, requested, listed, excluding, pk) == restricted and
len(listed) > 0 and ∃ f ∈ requested with dropped(listed, excluding, pk, f)`
encodes precisely that: the `len(listed) > 0` conjunct is the real
`select_mask`-non-empty conjunct (an empty `deferred_loading` set yields an empty
mask, `get_select_mask` returning `{}` at `sql/query.py:798-812`), and `dropped`
is `field not in select_mask` computed in the query state's own representation —
a listed code is dropped iff the list is a leave-out list, an unlisted code is
dropped iff the list is a keep list, and the pk is never dropped (both mask
builders unconditionally seed `select_mask[opts.pk]`, `sql/query.py:731,777`).
When `restricted` is False (the post-`select_related()` state), the branch cannot
fire — well-formed regardless of the projection. (`select_related_descend`
also returns False without raising for nullable FKs in unrestricted mode,
`query_utils.py:339`; that only reduces the descend set and never raises, so it
does not affect the ill-formedness facet.)

**Guard conjuncts, all three modeled (no over-approximation).** The real guard
is a three-way conjunction (`restricted and select_mask and field.name in
requested and field not in select_mask`) and the deep model carries all of it:
`restricted` ↔ `restricted`, `select_mask` non-empty ↔ `len(listed) > 0`, and
`field.name in requested and field not in select_mask` ↔ `f in requested and
dropped(...)`. An earlier revision dropped the non-emptiness conjunct and
justified it as a sound over-approximation on the grounds that the empty-mask
region was unreachable; that reasoning was wrong on exactly the `defer(pk)` base,
where `only("pk")` DOES produce an empty mask (§3.2). Modeling the conjunct
directly removes the need for the argument: `model_ill_formed ⟺ real_raises`, and
G-CONF confirms the biconditional on the full enumerated space with 0
disagreements.

**Soundness check (G-AX), `axiom_check.py`:** configures Django standalone,
defines a model with a custom manager whose `get_queryset()` bakes in
`select_related("master")` (the issue's reproducer), and runs the REAL ORM:
- PRE-PATCH chain `Tag.objects.all().only("pk")` → `query.select_related` is a
  dict (restricted), and `compiler.pre_sql_setup()` raises `FieldError`
  (ill_formed True). This is the model_prepatch discriminator.
- POST-PATCH chain `Tag.objects.all().select_related().only("pk")` →
  `query.select_related` is NOT a dict (restricted False), `pre_sql_setup()`
  succeeds (not ill_formed), and the compiled `select` is exactly the pk column
  (`loaded == {pk}` — no adjacent `master` column).
- a non-restricted base (`select_related(None)`) is well-formed under both
  chains (reset is a no-op on the observable outcome).
Exit 0 iff every observation matches the deep model. Verified to pass against
the base_commit Django source. Imports stdlib + Django (the repo under test).

## G-CONF (differential conformance — `conformance_check.py`)

**Pinned seed: `SEED = 16938`.** Inputs checked: **100000** (`N_TARGET`), of
which the first **7813** are the *exhaustive* enumeration of the finite modeled
input space (13 named boundary cases + all 7800 domain points); the remainder is
seeded fuzz over the SAME space. Because the space is finite and fully
enumerated, this is strictly stronger than 1e5 samples over a subspace.

**Shadow.** `build_pk_iterator`, `clear_specific_request`, `only_pk` and the
`@Pure` helpers `dropped` and `ill_formed` are copied VERBATIM from `model.py`'s
`# impl-start` / `# impl-end` and `# pure-start` / `# pure-end` regions, with only
the contract calls (`Requires`/`Ensures`) removed. `PSet` is supplied by a shim
(construction, `in`, `==`, `len`, set difference `-`); `Exists(int, ...)` is
evaluated over the finite universe of field codes, faithful because `requested` is
always a subset of it. There is no `@ContractOnly` callee to stub (§3).

**Oracle — the real patched function, CALLED not transliterated.** The modeled
symbol is the nested closure `queryset_iterator` (§1: `python.py:81-82` and
`xml_serializer.py:157-158`). Being a local, it cannot be imported by name, so
it is driven end-to-end through the REAL
`django.core.serializers.serialize(backend, [obj])` over a real sqlite ORM, and
the queryset it builds is captured at the UNCHANGED boundary immediately below
it — the terminal `QuerySet.iterator` of the patched chain. The real
`select_related()`, `only("pk")`, `add_immediate_loading`, `get_select_mask` and
`select_related_descend`/`pre_sql_setup` all execute unmodified; no Django
behaviour is reimplemented. Both patched hunks are exercised
(`backend="python"` and `backend="xml"`).

**Input domain (finite).** Base states are realized in the REAL direction, by a
custom default manager on the related model whose `get_queryset()` bakes in the
state (the issue's own reproducer shape), then abstracted with `alpha`:
10 `select_related` configs (absent / no-arg / `None` / every non-empty subset of
the 3 FKs) x 65 projection configs (absent / `only` / `defer` over every subset
of the 5 concrete fields) x 6 owning rows of differing m2m membership (including
EMPTY and SINGLETON) x 2 patched sites = 7800. The model's `Requires` constrains
only permissions (`Acc`), so every generated state satisfies it.

**Clauses diffed** (each against a real observable, not a reimplementation):
`well_formedness` (`ill_formed` vs whether the real `pre_sql_setup()` raises
`FieldError`), `restricted`, `listed` + `excluding` (vs the real
`query.deferred_loading` pair — the projection in its own representation),
`loaded` (the effective column set the model's `dropped` predicate implies, vs the
real `get_select_mask()`, cross-checked against the compiled SQL select list),
`members`, and `member_set` (vs the m2m pk list the real serializer emitted).
Diffing the projection BOTH as representation and as meaning means neither a
right-columns/wrong-mode nor a right-mode/wrong-columns answer can pass.

### Recorded verdict: **G-CONF = pass** — 0 disagreements / 100000 inputs

Every diffed clause agrees with the real patched chain on all 7813 exhaustive
cases and the seeded fuzz on top: `well_formedness`, `restricted`,
`listed`/`excluding`, the effective `loaded` set, `members`, and `member_set`.
The informational `requested_keyset_mismatches` statistic is also **0**.

**The `defer(pk)` family, and a corrected earlier verdict.** A previous run of
this gate recorded **fail, 24301/100000, class `loaded`**, reporting that
`only("pk")` on a base whose manager defers the pk column yields an empty select
mask (all columns loaded) rather than `{pk}`. The *observation about Django is
correct* and is confirmed here against the real patched serializer:

| | value |
|---|---|
| real built `deferred_loading` | `(set(), False)` |
| real built `get_select_mask()` | `{}` (no restriction ⇒ all fields loaded) |
| real compiled SQL | `SELECT tag.id, tag.name, tag.master_id, …` |

What that run mis-attributed was the *cause*. It concluded the divergence was
"bridge-independent" — that a plain base and a `defer(pk)` base share one abstract
state, so no abstraction of this signature could be faithful. That conclusion held
only for the collapsed one-field `loaded` encoding that revision of the type
bridge used. Reading the projection the way the query state itself holds it, as
the `deferred_loading` pair `(listed, excluding)` (§2), keeps the two bases
DISTINCT — a plain base is `(∅, defer=True)`, a `defer(pk)` base is
`({pk}, defer=True)` — and `only_pk`'s case split on `q.excluding and pk in
q.listed` then reproduces the real `field_names.difference(existing)` branch
exactly (§3.2). The information the model needed was destroyed by the bridge, not
absent from the model's signature. The fault was in the type bridge (and in a
shadow that had gone stale against `model.py`'s current 5-field `Fetch`), not in
the artifact; the model's claim about the real behaviour was right.

**Falsifiability (negative control).** Run WITHOUT the gold patch, the same script
over the same 100000 inputs reports **69870 disagreements**, dominated by
`well_formedness+restricted` (52894) — the real pre-patch `FieldError` on the F2P
reproducer shape, which the patched model predicts away. Neither the generator,
the pinned seed, the input count, nor any boundary witness (including the three
`defer` witnesses that expose this family) was narrowed or removed.

**Modeling note.** `build_pk_iterator`'s `requested` facet is diffed too and now
agrees everywhere: the real `select_related()` replaces the dict with `True`,
discarding the keys, and `clear_specific_request` models the same discard
(`q.requested - q.requested`). The clause's stated purpose (refinement.md §C.1 —
the build addresses the same members the accessor yields) is additionally checked
directly against `members` and against the m2m pk list the real serializer emits.
