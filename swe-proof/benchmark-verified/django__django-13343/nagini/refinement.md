# refinement.md — django__django-13343

The operation-by-operation correspondence between `model.py`'s implementation
(the `configure` and `describe_store` impl regions) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — **A-consumed** where the proof uses an axiom's `Ensures`, **A-reference**
where a deep model is validated == real semantics by axiom_check.py / G-AX), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

This is a **two-site** change. The sites share no call edge; they communicate
through the field's recorded state (`_storage_callable`). Each site is modeled
as its own contracted function, and each has its own verification-failing
prepatch (G-DIFF needs one per independently-observable fixed behaviour).

## A. The configuration site — `FileField.__init__` (`files.py:230-237`)

Gold hunk:
```
         self.storage = storage or default_storage
         if callable(self.storage):
+            # Hold a reference to the callable for deconstruct().
+            self._storage_callable = self.storage
             self.storage = self.storage()
             if not isinstance(self.storage, Storage):
                 raise TypeError(...)
```

| # | model.py impl op (`configure`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `field.store = given` | `self.storage = storage or default_storage` | R + I | a storage object ↔ its identity `int` (mapping.md §2); `given != default_store_id()` models the truthy supplied value (`storage or default_storage == storage`). |
| A2 | `if given_is_producer:` | `if callable(self.storage):` | R | `callable(self.storage)` ↔ the boolean `given_is_producer` (mapping.md §2). |
| A3 | `field.has_producer = True; field.producer_id = given` | `self._storage_callable = self.storage` | R + I | recording the original callable ⇔ setting the bool `has_producer` and storing the callable's identity `producer_id == given` (the callable's id, captured BEFORE the call replaces `self.storage`). |
| A4 | `field.store = evaluated` | `self.storage = self.storage()` | A-reference | evaluating the producer yields a concrete store; modeled as a distinct id `evaluated` (the precondition `evaluated != given` is the producer-evaluation-yields-a-distinct-object fact, validated against the real test producers by axiom_check.py — mapping.md §3.1). The order matters and is preserved: `producer_id` captures the callable's identity, then `store` becomes the evaluation. |
| A5 | `else: field.has_producer = False` | (the `isinstance` check / no `_storage_callable` set) | R | when not a producer, no callable is recorded (`getattr(..., default)` will later fall through to `self.storage`). The spec pins this with the frame clause `Implies(not given_is_producer, producer_id == Old(producer_id))`: the gold hunk writes `_storage_callable` ONLY inside the `if callable(...)` branch, so on the non-producer branch the recorded-producer slot is untouched — an impl that scribbled on it would correspond to writing a spurious `_storage_callable` for a concrete store, which the real deconstruct would then emit (breaking the concrete-store round-trip). The `isinstance`/`TypeError` guard is an unchanged validation orthogonal to the tested deconstruction behaviour and is not modeled. |

## B. The description site — `FileField.deconstruct` (`files.py:281-282`)

Gold hunk:
```
         if self.storage is not default_storage:
-            kwargs['storage'] = self.storage
+            kwargs['storage'] = getattr(self, '_storage_callable', self.storage)
         return name, path, args, kwargs
```

| # | model.py impl op (`describe_store`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `if field.store == default_store_id(): return None` | `if self.storage is not default_storage:` (guarding whether `kwargs['storage']` is set) | R + A-reference | identity test against the default singleton ↔ `store == default_store_id()` (id 0); `Result() is None` ⇔ the `storage` key is absent (mapping.md §2, §3.2). |
| B2 | `if field.has_producer: return field.producer_id` | `getattr(self, '_storage_callable', self.storage)` — the `_storage_callable` branch | R + I | `getattr` returns `_storage_callable` when present ⇔ return the recorded `producer_id` when `has_producer`. This is the discriminating fix: the ORIGINAL producer, not the evaluated store. |
| B3 | `return field.store` | `getattr(self, '_storage_callable', self.storage)` — the default branch | R + I | `getattr` falls back to `self.storage` when `_storage_callable` is absent ⇔ return the live `store` when not `has_producer`. |

## C. The discriminating change and the two prepatches

The tested behaviour is the round-trip `describe_store(configure(producer))`
returning the **original producer**, never the concrete store it evaluated to —
exactly `assertIs(deconstruct()['storage'], callable_storage)` (F2P
`test_deconstruction`). It is sensed by the conjunction of two model clauses,
each broken by one prepatch:

- **`model_prepatch.py` (site B, the deconstruct bug):** `describe_store`
  returns `field.store` unconditionally (gold pre-image `kwargs['storage'] =
  self.storage`). With a recorded producer, `store == evaluated != producer_id`
  (preconditions), so it **fails** `describe_store`'s postcondition
  `Result() == field.producer_id`. This is the literal bug the issue reports.
- **`model_prepatch_2.py` (site A, the __init__ bug):** `configure` never
  records the producer (`has_producer` stays `False`), the gold pre-image where
  `__init__` evaluates the callable but stores no `_storage_callable`. It
  **fails** `configure`'s postcondition `field.has_producer == given_is_producer`.
  Without this recording, even a correct deconstruct (B2) could not recover the
  producer — so both hunks are necessary and each is independently witnessed.

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The two genuinely-changed
operations — recording the original producer at configuration, and emitting it
(not the evaluation) at description — are modeled **deeply** as field-state and
identity logic; there is no consumed axiom about either changed operation. The
two A-references (producer evaluation yields a distinct object; identity
comparison against the default singleton) concern UNCHANGED Python semantics the
new code relies on, and are validated against real semantics by axiom_check.py
(G-AX). No `@ContractOnly` axiom is shipped (no dead axiom).

## E. verify(model) ⇒ resolved

`configure` verifies only if it records the producer exactly when one is
supplied (A3, `has_producer == given_is_producer`, `producer_id == given`),
records NOTHING in the producer slot otherwise (A5,
`producer_id == Old(producer_id)` on the non-producer branch — closing the
dead-state hole where a same-spec impl could scribble a spurious producer
record for a concrete store), and adopts the evaluation as the live store (A4). `describe_store` verifies only if,
for a non-default store, it returns the recorded producer when one exists (B2)
and the live store otherwise (B3), and suppresses the key for the default store
(B1). By R (storage object ↔ identity int; `callable`/`getattr`/`is`-comparison
correspondences) and the two G-AX-validated A-references, the verified pair is
the gold patch up to type refinement on the tested inputs. The gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
A-reference soundness (G-AX) and refinement fidelity (this document, G-EQ).
