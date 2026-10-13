# refinement.md — django__django-13401

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `fieldEq`, `fieldLt`, `fieldHash` `do` blocks and the pure models
`keyOf`/`ownerLt`/`fieldLtSpec`) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement; bijection in mapping.md §2), **A-consumed** (the
proof uses the opaque callee's contract), **A-reference** (a deep model
validated == its real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the A legs and this narrative are audited by **G-EQ**. Claim: any impl verifying
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE). Three independently
fixed behaviours ⟹ three `Solution_prepatch_*.lean`, one per method (G-DIFF).

## A. Equality — `Field.__eq__` (`__init__.py:516`)

Gold hunk:
```
-            return self.creation_counter == other.creation_counter
+            return (
+                self.creation_counter == other.creation_counter and
+                getattr(self, 'model', None) == getattr(other, 'model', None)
+            )
```

| # | Solution.lean impl op (`fieldEq`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `a b : FieldRec` | `self`, `other` (`isinstance` `Field`) | R | `Field` ↔ `FieldRec` (mapping.md §2). The `isinstance`/`NotImplemented` guard is outside the modeled `Field`-only domain (mapping.md §2), unchanged by the patch. |
| A2 | `decide (a.counter = b.counter)` | `self.creation_counter == other.creation_counter` | I | identical concrete int comparison; `int` ↔ `Int` (R). |
| A3 | `decide (a.owner = b.owner)` | `getattr(self,'model',None) == getattr(other,'model',None)` | R + I | the model-equality test; `model` identity ↔ `owner : Option (String×String)` (mapping.md §2). `Option` equality (`none=none`, `some p = some q ↔ p=q`) ↔ the `getattr(...,None)` comparison: both unattached (`None==None`) or same model identity. |
| A4 | `&&` of A2,A3 returned | `... and ...` returned | I | short-circuit boolean conjunction; observationally `&&`. |

Pre-patch `Solution_prepatch_eq.lean` drops A3 (`return decide (a.counter =
b.counter)` only) and **fails** `out = (… && …)` — the exact bug
(`self.creation_counter == other.creation_counter` alone), so equal-counter
cross-model fields wrongly compared equal.

## B. Strict order — `Field.__lt__` (`__init__.py:522`)

Gold hunk replaces `return self.creation_counter < other.creation_counter` with
the decision tree: counter-differs-or-both-unattached ⟹ compare counters; else
attachment-differs ⟹ unattached first; else compare `(app_label, model_name)`
tuples.

| # | Solution.lean impl op (`fieldLt` / `fieldLtSpec`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `a.counter ≠ b.counter ∨ (a.owner=none ∧ b.owner=none)` → `decide (a.counter < b.counter)` | `if (self.creation_counter != other.creation_counter or not hasattr(self,'model') and not hasattr(other,'model')): return self.creation_counter < other.creation_counter` | R + I | identical guard + comparison; `hasattr(...,'model')` ↔ `owner.isSome`, so `not hasattr ∧ not hasattr` ↔ `owner=none ∧ owner=none` (R). Python `and` binds tighter than `or`, matching the Lean parenthesization. |
| B2 | `a.owner.isSome ≠ b.owner.isSome` → `decide (a.owner = none)` | `elif hasattr(self,'model') != hasattr(other,'model'): return not hasattr(self,'model')` | R + I | exactly-one-attached ⟹ the unattached one is `<` ("no-model fields first"); `not hasattr(self,'model')` ↔ `a.owner = none` (R). |
| B3 | `match a.owner,b.owner with some pa, some pb => ownerLt pa pb` | `else: return ((self.model._meta.app_label, self.model._meta.model_name) < (other...app_label, other...model_name))` | R + I | both attached, equal counters ⟹ lexicographic tuple `<`; `ownerLt` IS Python tuple `<` on `(str,str)` (mapping.md §2, §3.2). The `_ , _ => false` arm is unreachable under the B1/B2 guards (both `isSome`). |

Pre-patch `Solution_prepatch_lt.lean` is `return decide (a.counter < b.counter)`
(counter only) and **fails** `out = fieldLtSpec a b` on the B3 tie-break — the
exact bug.

## C. Digest — `Field.__hash__` (`__init__.py:528`)

Gold hunk:
```
-        return hash(self.creation_counter)
+        return hash((
+            self.creation_counter,
+            self.model._meta.app_label if hasattr(self, 'model') else None,
+            self.model._meta.model_name if hasattr(self, 'model') else None,
+        ))
```

| # | Solution.lean construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | `keyOf a = {counter, scopeName := owner.map (·.1), entityName := owner.map (·.2)}` | the tuple `(creation_counter, app_label if hasattr else None, model_name if hasattr else None)` | R + I | the key construction; `owner.map (·.1)` ↔ `app_label if hasattr(self,'model') else None` and likewise `.2`/`model_name` (R; `Option.map` ↔ the conditional). |
| C2 | `pyHash (keyOf a)` | `hash((...))` | A-consumed | `pyHash` is the opaque contract on the unchanged builtin `hash`; the proof consumes only `out = pyHash (keyOf a)` (digest is a function of the key). G-AX confirms the real `hash` is a function of the key AND that keys differing in model identity have unequal digests on the F2P inputs (mapping.md §3.1). |

Pre-patch `Solution_prepatch_hash.lean` digests `{counter, scopeName:=none,
entityName:=none}` (ordinal only) and **fails** `out = pyHash (keyOf a)` whenever
`a.owner ≠ none` — the exact bug (`hash(self.creation_counter)`), so cross-model
fields collided in sets.

## D. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The changed comparison/order logic is modeled
**directly** (`fieldLtSpec`, the `&&`, the `keyOf` tuple) — concrete I ops over
the R-refined carrier — not hidden behind an axiom about a function under change.
The only A leg is the **unchanged** builtin `hash` (C2, `pyHash`), an A-consumed
contract, not the operation the patch changes.

## E. verify(Solution) ⇒ resolved

`fieldEq` verifies only if `out` equals counter-equality AND owner-equality (A2,
A3); `fieldLt` only if `out = fieldLtSpec` (the full B1–B3 tree); `fieldHash`
only if `out = pyHash (keyOf a)` (the full key C1). By R (`Field ↔ FieldRec`,
`model` identity ↔ `owner`, `hasattr` ↔ `isSome`, tuple `<` ↔ `ownerLt`) the
three verified methods equal the gold `__eq__`/`__lt__`/`__hash__` on the tested
inputs; by G-AX the real `hash` meets the `pyHash` contract (C2) and the
model-distinguishing property the F2P test needs; by G-CONF the R/I shadow of
`fieldEq`/`fieldLt` agrees with `patch.diff` behaviour on ≥10⁵ inputs. Therefore
a model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the one audited builtin — and the gold patch resolves
(G-RESOLVE). Trust points are exactly the two of plan §1.1: callee soundness
(G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
