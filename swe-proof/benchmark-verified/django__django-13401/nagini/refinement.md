# refinement.md — django__django-13401

The operation-by-operation correspondence between `model.py`'s implementation
(the `attr_eq` / `attr_lt` / `attr_hash_key` impl regions and the deep `eq_ref` /
`lt_ref` / `hash_ref` / `same_owner` / `lex_lt` models) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A-consumed** (proof
uses an axiom's `Ensures`), **A-reference** (a deep model is validated == the
real callee by axiom_check.py / G-AX, NOT consumed), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at `base_commit`
and is the real correctness oracle, G-RESOLVE). It is a multi-site change: three
methods of `Field` (`__eq__`, `__lt__`, `__hash__`) are independently fixed, so
there are three contracted+implemented functions and three independently failing
prepatch variants (one per fixed behavior).

This change calls NO library/utility the patch leaves unchanged that needs
axiomatization: the three operations are spelled out over the field values. The
native callees they DO use — `getattr`-equality, native tuple comparison, the
builtin `hash` — are **A-reference**s the deep models are validated against, not
consumed `@ContractOnly` axioms. There is therefore no `axioms` region content
and **no kind-3 (inexpressible-changed-op) step**.

## A. `__eq__` site — `Field.__eq__` (`django/db/models/fields/__init__.py:516`)

Gold hunk:
```
-            return self.creation_counter == other.creation_counter
+            return (
+                self.creation_counter == other.creation_counter and
+                getattr(self, 'model', None) == getattr(other, 'model', None)
+            )
```

| # | model.py impl op (`attr_eq`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `self_, other: Attr` | `self, other` (`Field`) | R | `Field` ↔ `Attr` with only the touched fields (mapping.md §1,2). The `isinstance(other, Field)` guard / `NotImplemented` branch is the unchanged dispatch wrapper, omitted from the modeled core (it is identical pre/post-patch and exercised by the P2P `test_field_ordering`). |
| A2 | `self_.rank == other.rank` | `self.creation_counter == other.creation_counter` | R+I | int equality; `rank` ↔ `creation_counter`. |
| A3 | `same_owner(self_, other)` | `getattr(self,'model',None) == getattr(other,'model',None)` | A-reference | owner-identity equality modeled deeply (`same_owner`): both ownerless, or both own an equal `(app_label, model_name)` pair. Validated == native `getattr`-equality by axiom_check.py §A-reference 1. |
| A4 | `Result() == eq_ref(self_, other)` | the returned boolean | I | the postcondition pins the result to the deep reference `eq_ref == (rank== ∧ same_owner)`, the exact post-patch boolean. |

## B. `__lt__` site — `Field.__lt__` (`django/db/models/fields/__init__.py:522`)

Gold hunk (the `creation_counter`-only return replaced by the three-branch
order). Model `attr_lt` mirrors it branch-for-branch:

| # | model.py impl op (`attr_lt`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `if self_.rank != other.rank or (not self_.owned and not other.owned): return self_.rank < other.rank` | `if self.creation_counter != other.creation_counter or not hasattr(self,'model') and not hasattr(other,'model'): return self.creation_counter < other.creation_counter` | R+I | rank↔creation_counter, owned↔hasattr(model); identical boolean structure and int comparison. |
| B2 | `elif self_.owned != other.owned: return not self_.owned` | `elif hasattr(self,'model') != hasattr(other,'model'): return not hasattr(self,'model')` | R+I | owned↔hasattr(model); identical (no-owner field ordered first). |
| B3 | `else: return lex_lt(self_.okey, other.okey)` | `else: return ((self.model._meta.app_label, self.model._meta.model_name) < (other...))` | A-reference + R | the native tuple comparison of the `(app_label, model_name)` pairs is modeled as lexicographic order on the flattened `okey` (label ++ [0] ++ name). The NUL separator preserves tuple order; axiom_check.py §A-reference 2 asserts `lex_lt` on flattened keys == native tuple order, and `lt_ref` == the whole native `__lt__`. |
| B4 | `Result() == lt_ref(self_, other)` | the returned boolean | I | postcondition pins the result to the deep reference `lt_ref`, the exact post-patch order. |

## C. `__hash__` site — `Field.__hash__` (`django/db/models/fields/__init__.py:528`)

Gold hunk:
```
-        return hash(self.creation_counter)
+        return hash((
+            self.creation_counter,
+            self.model._meta.app_label if hasattr(self, 'model') else None,
+            self.model._meta.model_name if hasattr(self, 'model') else None,
+        ))
```

| # | model.py impl op (`attr_hash_key`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | build the KEY `PSeq(rank, 1) + okey` (owned) / `PSeq(rank, 0)` (ownerless) | build the tuple `(creation_counter, app_label_or_None, model_name_or_None)` | A-reference + R | the changed operation is the KEY: it now carries the owner identity, not the rank alone. Modeled deeply so two attributes differing in owner produce distinct keys. `hash_ref` distinct ⇔ gold key tuple distinct (axiom_check.py §A-reference 3). |
| C2 | `Result() == hash_ref(self_)` | `hash(<that tuple>)` | A-reference | the builtin `hash` is the unchanged callee. The model returns the key; axiom_check.py validates that on EQUAL-rank distinct keys the builtin `hash` separates them (the de-dup property the issue targets), explicitly NOT claiming universal hash injectivity (the `-1`/`-2` quirk affects only distinct ranks). |

## D. Independent prepatch witnesses (G-DIFF)

Each fixed behavior is sensed independently by a same-spec prepatch whose impl
reverts exactly one method to the pre-patch `creation_counter`-only form:

| variant | reverted impl | fails on |
|---|---|---|
| `model_prepatch_eq.py` | `attr_eq → return self_.rank == other.rank` | `Result() == eq_ref(self_, other)` (same rank, different owner ⇒ gold False, prepatch True) |
| `model_prepatch_lt.py` | `attr_lt → return self_.rank < other.rank` | `Result() == lt_ref(self_, other)` (equal rank, owners differ ⇒ gold uses the tie-break, prepatch returns False) |
| `model_prepatch_hash.py` | `attr_hash_key → return PSeq(self_.rank)` | `Result() == hash_ref(self_)` (key drops the owner) |
| `model_prepatch.py` | all three reverted (the true pre-image) | all three postconditions |

## E. verify(model) ⇒ resolved

`attr_eq` / `attr_lt` / `attr_hash_key` verify only if their results equal the
deep references `eq_ref` / `lt_ref` / `hash_ref` — which encode exactly the
post-patch `__eq__` / `__lt__` / `__hash__` decisions (A-reference, validated ==
the native `getattr`/tuple/`hash` semantics by G-AX). By R (Field↔Attr,
creation_counter↔rank, model-identity↔(app_label,model_name) pair, str↔code
points) the verified operations are the gold patch's operations on the tested
inputs. The F2P test (`Field instances from abstract models are not equal.`)
asserts the three abstract-inherited fields compare unequal, sort by model name,
and hash apart — exactly what `eq_ref`/`lt_ref`/`hash_ref` deliver and the
prepatches violate; the P2P `test_field_ordering` (bare, ownerless, distinct
ranks) is preserved by branch B1 (the creation_counter-first ordering). The
shipped gold patch resolves (G-RESOLVE). Trust points are the two of PLAN §1.1:
A-reference soundness (G-AX) and refinement fidelity (this document, G-EQ).
