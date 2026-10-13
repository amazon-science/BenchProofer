# mapping.md — django__django-13590

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 755dbf39fcdc491fe9b588358303e259c7750be4`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `django/db/models/sql/query.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolve_sequence(value, field_named)` | the `isinstance(value, (list, tuple))` branch of `Query.resolve_lookup_value(self, value, can_reuse, allow_joins)` — `django/db/models/sql/query.py:1072` (the list/tuple branch at lines 1077-1083) | the only modeled changed function: resolve each sub-value and rebuild a container of the same kind via a convention-matching (non-raising) construction |
| `value: List[int]` | `value` (a `list`/`tuple`/`namedtuple` of sub-values) in the branch | the input sequence of sub-values |
| `field_named: bool` | `hasattr(type_, '_make')` — whether `type(value)` is a `namedtuple` | which container-builder convention `type(value)` requires to construct without raising |
| `resolve_one(sub_value)` *(axiom — A-consumed)* | the recursive `self.resolve_lookup_value(sub_value, can_reuse, allow_joins)` call applied to one element — `query.py:1078-1080` | unchanged per-element resolution; for a non-expression sub-value it bottoms out in the `return value` pass-through (`query.py:1083`) |
| `resolved_seq(s)` | the element-wise application of the recursive resolve over the whole sequence (the generator `(self.resolve_lookup_value(sub_value, …) for sub_value in value)`) — `query.py:1078-1081` | pure spec: the resolved-element sequence |
| `build_container(elems, field_named, spread)` *(axiom — A-consumed)* | the UNCHANGED container *constructor* invoked as `type_(values)` (single iterable) / `type_(*values)` (spread) — `query.py` | unchanged callee: a well-formed (non-raising) construction is reachable only when the convention matches the kind; on success it grants the `well_formed_container` token |
| `well_formed_container(contents, field_named)` *(axiom — A-consumed; abstract capability token)* | the IDENTITY of a constructor-produced, well-formed container — the result of the `return type_(...)`/`type_(*...)` call | unchanged callee output: the reconstruction's only producer of the rebuilt container is the constructor call; the token captures "this container came through a non-raising construction for this kind", so the construction cannot be bypassed |

The pre-patch repo construction the change replaces (for the refinement audit,
not referenced from the consumer spec view): `return type(value)(<generator>)`
(`query.py:1080` pre-patch) — a single iterable passed to the container kind's
constructor, which for a `namedtuple` kind with ≥2 fields supplies only one
positional argument to a constructor expecting one-per-field and **raises
TypeError**.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a `list`/`tuple`/`namedtuple` of opaque sub-values | `List[int]` of sub-value identities | the k-th sub-value ↔ `value[k]`; `len(value)` ↔ the element count; container order ↔ list order. The tested behaviour observes only WHICH sub-values end up in the rebuilt container and IN WHAT ORDER (the F2P filters on `EmployeeRange(minimum=51, maximum=100)` and checks the resulting queryset), so an opaque-identity carrier is faithful. The carrier is a *materialized, re-iterable* list (not a single-use generator). |
| `type(value)` and `hasattr(type_, '_make')` | the boolean `field_named` | `field_named == True` ↔ `type(value)` is a `namedtuple` (has `_make`); `field_named == False` ↔ a plain `list`/`tuple` kind. |
| `type_(values)` (single iterable) vs `type_(*values)` (spread) | the `spread` argument of `build_container` and the precondition `field_named == spread` | `spread == False` ↔ pass the single iterable `type_(values)`; `spread == True` ↔ spread one-per-field `type_(*values)`. The precondition `field_named == spread` encodes "a well-formed (non-raising) construction needs the matching convention": a field-named kind needs the spread; a plain kind needs the single iterable. |
| the constructor RAISES vs SUCCEEDS (a control-flow effect, invisible to the `List[int]` value abstraction) | the `well_formed_container(contents, field_named)` capability token granted only under `field_named == spread` | a non-raising construction ↔ the builder grants the token; a would-raise construction ↔ the precondition `field_named == spread` is violated, the call is forbidden, no token. |
| the rebuilt container | `List[int]` `Result()` | element-for-element, in order. |

`str` is not involved; sub-values are carried as opaque `int` identities, so no
`str`-indexing concern arises.

## 3. Why the discriminator must be modeled as a control-flow effect (the soundness fix)

The behaviour that the F2P test discriminates is **whether the field-named
constructor RAISES**: pre-patch `EmployeeRange(<generator>)` raises `TypeError:
__new__() missing 1 required positional argument: 'maximum'`; post-patch
`EmployeeRange(*values)` succeeds. The *contents* the rebuilt container would hold
are identical either way, so a value-level postcondition cannot separate them
(batch03 G-EQ break). The raise/succeed effect is therefore lifted into the
contract of the function under change via the unforgeable `well_formed_container`
capability token (see refinement.md §B): the token is granted only by a
non-raising (`field_named == spread`) construction and is required by
`resolve_sequence`'s postcondition, so a verifying impl must perform the
convention-matching construction for a field-named kind.

This is the same idiom as the `combined_collection` token in
`tasks/pydata__xarray-4094/` (a "raises vs returns" change captured by a
capability the unchanged callee grants only on success). It is a capability, NOT
an answer-key oracle (SPEC_GUIDE §0.8): the token carries no value an impl can
echo back; it can only be obtained by going through the (effect-producing)
construction.

## 4. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 4.1 `resolve_one` ↔ recursive per-element resolution (A-consumed)
**Callee:** `Query.resolve_lookup_value(self, sub_value, can_reuse, allow_joins)`
applied to a single element (`django/db/models/sql/query.py:1078-1080`). It is
UNCHANGED by this patch (only the *reconstruction* around the generator changes).
The model consumes only that per-element resolution is a **deterministic pure
function of the sub-value** — `resolve_one` carries no `Ensures` beyond purity;
the proof relies on nothing more than "the same sub-value resolves to the same
value", which lets `resolved_seq` be a well-defined function over the input. For a
non-expression sub-value (no `resolve_expression` attribute) the recursion bottoms
out in the final `return value` (`query.py:1083`), i.e. the identity. The axiom is
the **weakest** contract the proof needs (purity/determinism); it never pins an
exact value and is not the operation under change.

### 4.2 `build_container` + `well_formed_container` ↔ the unchanged container constructor (A-consumed)
**Callee:** the Python container **constructor** of the container kind —
`type_(values)` and `type_(*values)` for `type_ ∈ {list, tuple, namedtuple}`. The
patch does **not** change the constructor; it changes only HOW the constructor is
**called** (the `spread` choice), which lives in `resolve_sequence`'s impl. So the
constructor is an *unchanged callee*, axiomatized as kind A — exactly as
`tasks/pydata__xarray-4094/` axiomatizes the unchanged `Dataset` constructor.

The contract `build_container` encodes:
* `Requires(field_named == spread)` — a well-formed (non-raising) construction is
  reachable only under the matching convention. A field-named kind handed the
  single un-spread iterable (`field_named == True, spread == False`) raises and so
  cannot well-form; the precondition forbids that call.
* On a well-formed construction it `Ensures` the result holds exactly the elements,
  in order (`len(Result()) == len(elems)`, `ToSeq(Result()) == Old(ToSeq(elems))`),
  AND grants `well_formed_container(ToSeq(Result()), field_named)` — the abstract
  capability token (`@ContractOnly @Predicate`, no body) that nothing else can
  fabricate (Nagini cannot `Fold` an abstract predicate).

The token's soundness is precisely that a *token-granting (well-formed)*
construction is reachable only under the matching convention — established by the
real-constructor observations below.

**Soundness check (G-AX, validated IN-CONTAINER, rc=0):** `axiom_check.py` runs
the real constructions on boundary element lists (incl. the F2P 2-field case
`[51, 100]`, empty, singletons, and longer lists) plus 20 000 randomized fuzz
lists, asserting:
* a plain kind (`list`/`tuple`) built from a single iterable WELL-FORMS holding
  exactly the elements (`list(tuple(iterable)) == [elements]`);
* a `namedtuple` kind built by spreading one-per-field (`cls(*values)`) WELL-FORMS
  holding exactly the elements (this is the gold's `type_(*values)`);
* a `namedtuple` kind handed the single un-spread iterable does NOT well-form: for
  ≥2 fields it raises `TypeError` (the issue's exact error); for 1 field it bundles
  the whole iterable into field 0 (contents differ from the elements).
It also checks `resolve_one` determinism/identity on boundary + scalar fuzz. It
imports only `collections.namedtuple` from the standard library (the same
construction the gold patch uses); nothing repo-specific. Exit 0 iff sound;
confirmed rc=0 in the pinned eval image
`swebench/sweb.eval.x86_64.django_1776_django-13590`.

## 5. Conformance check (G-CONF)

`conformance_check.py` runs the contract-stripped impl region of
`resolve_sequence` (shadow) against the real patched
`Query.resolve_lookup_value` (oracle) on the whole sequence, with the
@ContractOnly callees bridged to their real counterparts (`resolve_one` ->
the per-element recursive resolution; `build_container` -> the real
constructor of the input's kind under the convention `spread` denotes).
Inputs: 29 boundary sequences + 100000 fuzz sequences over list / tuple /
namedtuple kinds (field counts 1..6) with scalar, expression-bearing, and
nested sub-values. **Pinned fuzz seed: 13590.**
