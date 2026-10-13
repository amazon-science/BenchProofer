# refinement.md — operation correspondence

Modeled function: `implementation_resolveRecord` ↔ `build_instance(Model, data, db)`.

| # | Lean impl op | patch.diff / repo op | tag | note |
|---|---|---|---|---|
| 1 | `if data.id = none ∧ hasKey = true` | `if pk is None and hasattr(default_manager, "get_by_natural_key") and hasattr(Model, "natural_key")` | R | `Option`-none ↔ `pk is None`; `hasKey` ↔ the two `hasattr` guards (mapping.md) |
| 2 | `let mut obj : Record := { payload := data.payload, store := defaultStore }` | `obj = Model(**data)` (fresh instance carries default `_state.db`) | R | a freshly assembled record starts on the default store |
| 3 | `obj := { obj with store := store }` | `obj._state.db = db` | I | **the fix**: establish the target store on the record before key derivation |
| 4 | `let key ← derive obj` | `natural_key = obj.natural_key()` | A-consumed | key derivation reads `obj._state.db`; PARTIAL callee, store-dependent (mapping.md). The `←` is load-bearing: it is where "no key came back" propagates — whether because the model has no such step or because the step could not resolve on the record it was handed |
| 5 | `match lookupByKey store key with \| some raw => ... \| none => return data` | `try: data[pk] = ...get_by_natural_key(*natural_key).pk except Model.DoesNotExist: pass` | A-consumed | found ⇒ set id; not-found ⇒ leave id (the `except ... pass`) |
| 6 | `some (coerceId raw)` | `Model._meta.pk.to_python(... .pk)` | A-consumed | coerce raw id to pk type |
| 7 | `return data` (outer / fallthrough) | `return Model(**data)` | R | the assembled record with (possibly) updated id |

Every step is R, A, or I. No changed op is left inexpressible.

**The fix is op #3 (tag I).** The pre-patch impl omits it, so it derives the key
from a record still on the default store (step 4 reads `obj.store`); the
post-patch impl derives from the record established on `store`. Clause (C2) of
the spec pins the key to `derive { payload := data.payload, store := store }`,
so the prepatch fails verification whenever the target store differs from the
default — exactly the multi-database bug. `Solution_prepatch.lean` is that
omission and nothing else, and it fails to elaborate on precisely that mismatch.

## Op #4 is PARTIAL, and that is an obligation, not a detail

Step #4 is not a total function of the record. It fails to hand back a key in two
distinct situations, and BOTH are properties of the real callee:

* the model may offer no such step. `hasattr(Model, "natural_key")` is false, the
  call raises `AttributeError`, and there is no key to come back with.
* the step may not resolve on the record it is handed. `natural_key()` follows
  the record's references against the alias the record carries, so on an instance
  still on the default store a reference to a row that lives only in the target
  store raises `DoesNotExist`. Measured directly on the F2P's model shape: the
  default-store call raises `Person.DoesNotExist`, the target-store call returns
  the key. This is the same fact the bug is about, seen from the definedness side
  rather than the "wrong key" side.

Op #1's guard therefore has TWO roles in the patched code, and op #3 has a second
role of its own; the correspondence has to carry all of them:

* the guard decides whether resolving an identifier is *useful* (the record has
  no pk yet), and
* it decides whether step #4 is *defined at all* (`hasattr(Model,
  "natural_key")`), while
* op #3 decides whether step #4 can *resolve* — it is what makes the record one
  the step is defined on.

The spec carries those roles as follows. The derivation step is handed to the
operation as an argument (`derive : KeyDerivation`, i.e.
`Record → Except Failure Key`) rather than being a global total function, so the
implementation has no way to obtain a key except by running that step and no way
to forge its availability. `derivationAvailability data store hasKey derive` —
the frozen obligation's only hypothesis — says a key comes back under `hasKey`
**for the record assembled on `store`**, and that nothing at all comes back when
`hasKey` is false; about the step on any OTHER record it says nothing, so an
implementation may not assume a key from one. Clause **(C0)** of the
postcondition (`∃ res, result = Except.ok res`: assembling a record always yields
a record) is then the obligation that op #4 is run only where op #1's guard says
it exists and only on the record ops #2–#3 assemble. Gold discharges (C0) because
its single run of #4 sits inside #1 and on that record; an implementation that
runs #4 anywhere else, or on anything else, has no key to show and cannot produce
a record at all.

This is what closes two holes successive audits found, both of which VERIFIED
against the spec as it stood and neither of which resolves the instance:

1. a rival that hoists ops #2–#4 above op #1 — a refactor that changes no
   observable on the guarded path — resolves the target F2P and then breaks every
   unrelated path that loads data for a model with no `natural_key` (measured:
   FAIL_TO_PASS 1/1, PASS_TO_PASS 27/53, 26 regressions). Clause (C0) over the
   `hasKey` half of availability rejects it.
2. a rival that keeps ops #1–#5 exactly as gold has them and merely runs step #4
   one EXTRA time on the record before op #3 establishes its store, discarding
   that result (`obj = Model(**data); obj.natural_key(); obj._state.db = db;
   natural_key = obj.natural_key()`). Nothing about the key it uses changes, so it
   reads as a redundant probe — but the discarded call raises, and the exception
   escapes: measured PASS_TO_PASS 53/53 with FAIL_TO_PASS 0/1, i.e. it breaks the
   very test the fix exists for. The mirror-image shape, re-deriving on a freshly
   assembled default-store record AFTER the correct derivation, measures the same.
   Restricting availability to the target-store record is what rejects both.

The cost of the second repair is bounded and measured: gold, the prepatch twin,
all five positive controls and the admissibility instance in `properties.py` still
discharge the obligation, because a correct implementation derives from the record
assembled from `data` on `store`. In particular `pos-control-double-derive` runs
step #4 twice on that record and verifies, so the obligation is not a rule about
how MANY times the step may be run — it is a rule about what it may be run on.

## What counts as RUNNING op #4 (the refinement rule for an effectful callee)

Op #4 is the only step in this correspondence whose *occurrence* — not just its
value — is observable in the repo, because `obj.natural_key()` can raise. The
Lean side is pure and total, so the correspondence has to say explicitly which
Lean text models an occurrence:

> A call to `obj.natural_key()` whose failure can escape is modelled by BINDING
> the derivation step (`let k ← derive r`), and only by that. A Lean term
> `let _ := derive r` whose value is dropped is zeta-erased: it denotes nothing,
> and an implementation carrying it is the same function — up to `rfl` — as the
> implementation without it. So the faithful transcription of a dropped value is
> a call whose failure cannot escape (`try: obj.natural_key() except
> Exception: pass`, or capture the outcome now and re-raise it only where the
> bound version would have propagated it).

That rule is forced by the carrier, not chosen for convenience, and it is
measured rather than argued. With the frozen spec regions in scope, all three of
the shapes successive audits proposed — the hoist written as a value, and the two
extra probes written as dropped values — are DEFINITIONALLY the frozen
implementation:

    example : implH = implG := rfl   -- prelude evaluated above the guard
    example : implP = implG := rfl   -- dropped probe before the store is set
    example : implQ = implG := rfl   -- dropped probe after the correct derivation

all closing under `scripts/lean_verify.sh` (exit 0). No obligation can reject one
of those and still admit gold, so a rival of that shape is never a spec-too-weak
finding; it is an unfaithful transcription, and the harness measures a program
the Lean side does not denote. The faithful transcriptions resolve, measured on
fresh harness runs:

| shape | materialized as | measured |
|---|---|---|
| hoist as a value | evaluate the step up front, capture the outcome, re-raise inside the guard | F2P 1/1, P2P 53/53 — RESOLVED |
| dropped probe | `try: obj.natural_key() except Exception: pass` before `obj._state.db = db` | F2P 1/1, P2P 53/53 — RESOLVED |
| hoist as an effect (bound) | unconditional `natural_key()` above the guard | F2P 1/1, P2P 27/53 — 26 regressions |
| probe as an effect (bound) | extra `natural_key()` whose exception escapes | F2P 0/1, P2P 53/53 |

The bottom two rows are what the spec must reject, and does: `(C0)` over
store-relative availability rejects both bound shapes (`rej-derive-outside-guard`,
`rej-probe-before-store`, `rej-probe-after-store` in `properties.py`). The top two
rows are what it must admit, and does: the same three edits with the derivation
DROPPED instead of bound ship as positive controls
(`pos-control-discarded-hoist`, `-discarded-probe-before`,
`-discarded-probe-after`), each carrying an `_isGold` step that closes
`implementation_resolveRecord d s hk dv = <the frozen body>` by `rfl` alone — so
G-PBT itself checks the gold-hood claim instead of taking it on trust. The spec
view states the rule where the callee is introduced (`KeyDerivation`).

The key-derivation and lookup callees (#4–#6) are A-consumed: the proof consumes
their behavior rather than computing it. For #5 and #6 that consumption is pure
term-identity — the same opaque constants appear in the spec and in the impl, and
the proof only case-splits on #5's result. For #4 it is the
`derivationAvailability` hypothesis, which is a THEOREM HYPOTHESIS discharged by
whoever instantiates the obligation, not an `axiom` declaration. So this bundle
declares no `axiom <callee>_prop` and G-AX has no consumed-axiom
over-approximation to validate against the repo callee (see `axiom_check.py`);
what G-CONF validates instead is that both properties the spec leans on — #4's
store-dependence and its partiality — are the real callee's, by driving the R/I
skeleton and the transcribed patch over both.
