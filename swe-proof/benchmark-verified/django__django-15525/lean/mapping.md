# mapping.md — symbol binding & type bijection

## Modeled function

| Lean | Python | file:line @ base_commit |
|---|---|---|
| `implementation_resolveRecord` / `problem_spec_resolveRecord` / `correct_resolveRecord` | `build_instance(Model, data, db)` | `django/core/serializers/base.py:325-347` |

base_commit: `fbacaa58ffc5a62456ee68b90efa13957f761ce4`

The edited hunk is lines 336-344: before the fix the not-yet-saved object's
identifying key is derived without first establishing the target database on the
object's state; the fix sets `obj._state.db = db` before calling
`obj.natural_key()` so that any related-record lookups performed while deriving
the key resolve against the target database `db` rather than the default.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Lean | Python |
|---|---|
| `Store` (`String`) | database alias `db` (a `str`, e.g. `"default"`, `"other"`) |
| `Payload` (`List String`) | `data` field dict's descriptive (non-pk) fields, order-stable |
| `Key` (`List String`) | the tuple returned by `Model(**data).natural_key()` |
| `Data.id : Option Int` | `data.get(Model._meta.pk.attname)` (`None` ⇒ `none`) |
| `Data.payload` | descriptive fields of `data` |
| `Record.payload` / `Record.store` | the built `obj`'s field data / `obj._state.db` |
| `defaultStore = "default"` | `DEFAULT_DB_ALIAS = "default"` (the state a fresh instance carries) |
| `Except Failure Data` | the operation's outcome: a record, or the exception raised when the key derivation could not be run on the instance it was given |
| `Failure.keyDerivationUnavailable` | `AttributeError: '<Model>' object has no attribute 'natural_key'` (no such step) **or** `<Related>.DoesNotExist` from `natural_key()` following a reference on an instance whose `_state.db` does not hold the referenced row (step present, cannot resolve here) |

## Callee provenance (opaque signatures only — `_prop` axioms, if any, added by proof agent)

| Lean callee | real callee | provenance |
|---|---|---|
| `derive : KeyDerivation` (`Record → Except Failure Key`) — an ARGUMENT of the operation, not a global constant | `obj.natural_key()` (resolves with `obj._state.db`; absent on models that define no `natural_key`) | `base.py:341` (post-fix `obj.natural_key()`); model method, store-dependent AND partial |
| `lookupByKey : Store → Key → Option Int` | `default_manager.db_manager(db).get_by_natural_key(*natural_key)` → `.pk`, `Model.DoesNotExist` ⇒ none | `base.py:342-345` |
| `coerceId : Int → Int` | `Model._meta.pk.to_python(...)` | `base.py:343` |

**Flag dependency:** `hasKey` models the model-side half of the guard
`pk is None and hasattr(default_manager, "get_by_natural_key") and hasattr(Model, "natural_key")`
— i.e. `hasattr(default_manager, "get_by_natural_key") and hasattr(Model, "natural_key")` —
while `data.id = none` models `pk is None`.
`derive` is store-dependent ONLY because `natural_key()` may follow a
ForeignKey whose related object is fetched from the object's `_state.db` — which
is also why it can fail outright on an instance carrying the wrong alias. G-CONF
fuzzes both store-sensitive and store-insensitive key derivations (a per-case
`key_home`: the store the referenced row lives in, or None for a key that follows
no reference).

**Definedness correspondence (what `derivationAvailability` binds to).**
`obj.natural_key()` can fail to hand back a key in TWO ways, and both are
definedness facts about where the step may be run:

* the model may not offer the step at all. The same two `hasattr` checks that
  make resolving *useful* are what make the call *callable*: on a model without
  that method it raises `AttributeError`.
* the step may not resolve on the instance it is given. `natural_key()` may
  follow a reference, which is resolved against the instance's `_state.db`; when
  the referenced row lives only in the target database, calling it on an instance
  still carrying the default alias raises `DoesNotExist`. This is not a
  hypothetical: it is the regression scenario, measured directly on the F2P's
  model shape (default-store call raises `Person.DoesNotExist`; target-store call
  returns `('The Lord of the Rings', 'J.R.R. Tolkien')`).

**Occurrence correspondence (which Lean text models a CALL).** `natural_key()`
is an effect: it raises, and the raise escapes whether or not the returned value
is used. The Lean carrier is pure and total, so a term whose value is dropped is
zeta-erased and denotes nothing. The binding is therefore part of the mapping,
not incidental syntax:

| repo text | Lean text |
|---|---|
| `natural_key = obj.natural_key()` (or any call whose exception can escape) | `let k ← derive r` — the step is BOUND, so "no key came back" propagates |
| a call whose failure cannot escape (`try: obj.natural_key() except Exception: pass`; or capture the outcome and re-raise it only where the bound form would have) | `let _ := derive r` — a dropped value, zeta-erased; the impl is the same function as one that never mentions it |

Consequence, recorded because two audits turned on it: an alternative
implementation that writes an extra derivation as a dropped value is
DEFINITIONALLY gold (`example : implP = implG := rfl` closes), so no
specification can reject it while admitting gold, and a materialized diff that
lets that dropped call raise is not a transcription of it. Both faithful
transcriptions resolve (F2P 1/1, P2P 53/53, measured); see refinement.md for the
table and `properties.py` for the six paired cases that pin both sides.

So the Lean side does not model the derivation as a total function; it takes it
as an argument and assumes exactly

    derivationAvailability data store hasKey derive :=
      (hasKey = true  → ∃ key,
          derive { payload := data.payload, store := store } = Except.ok key) ∧
      (hasKey = false → ∀ r, derive r = Except.error Failure.keyDerivationUnavailable)

i.e. `hasKey = hasattr(...) and hasattr(...)` read as a definedness condition,
AND "only on the record assembled for the target store" — nothing whatever is
assumed about the step on any other record. Postcondition clause (C0) is stated
over it; see `refinement.md` for why that clause is what pins op #4 inside op
#1's guard *and* onto op #2/#3's record, and `properties.py` for the four rivals
it refutes.

Soundness notes on this binding, recorded rather than glossed:

* `hasKey` is a single Bool where the repo has two independent `hasattr` checks,
  so the mixed states (manager method present, model method absent, and vice
  versa) are OVER-APPROXIMATED: `hasKey = false` covers all three "not both
  present" cases. That is sound in the safety direction for (C0) — the spec
  forbids running the derivation in a state where the real code may raise, which
  is a superset of the states where it certainly raises — and it never weakens
  (C2), which speaks only about `hasKey = true`, where both checks hold and the
  real call is defined. The one thing the model cannot express is a state where
  `Model.natural_key` exists but the manager method does not: the real code would
  skip the block yet `obj.natural_key()` would be callable. An implementation is
  not required to be correct there beyond the frame clauses, and it is not
  required to raise either — (C0) only forbids failing.
* `derivationAvailability` assumes a key comes back only for the record assembled
  on the target store — never for a record on any other alias, and never for a
  record with any other payload. The store dimension is exact (that is the
  regression, measured above). The payload dimension is an UNDER-approximation:
  the repo would in fact resolve the key for other field data on the target
  store, and the spec declines to assume it. That direction is the safe one — a
  hypothesis that assumes less makes the obligation HARDER, so it can only reject
  implementations, never admit a wrong one — and its cost is bounded and
  measured: gold, the prepatch twin, all five positive controls (including
  `pos-control-double-derive`, which runs the step twice) and the admissibility
  instance all discharge it, because the record a correct implementation derives
  from is the one assembled from `data` on `store`. What it buys is that the
  implementation has no way to *forge* a key at a point where the real call
  raises, which is what both audit rivals did.
* The two real failures (`AttributeError`, `DoesNotExist`) collapse onto the
  single `Failure` value this carrier has. Nothing is lost: with one constructor
  no implementation can discriminate them, and clause (C0) forbids either
  escaping, so the collapse cannot license a rival. It does mean the spec cannot
  say WHICH failure a wrong implementation would have produced, only that it
  produced one.

## G-CONF fuzz seed

`conf_seed = 20240630` (pinned).
