# refinement.md — django__django-14915

The operation-by-operation correspondence between `model.py`'s implementation
(the `ChoiceValue.membership_identity` impl region and the `value_identity`
axiom) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses the axiom's contract, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The change site — adding `__hash__` (`django/forms/models.py:1161`)

Gold hunk (added to `class ModelChoiceIteratorValue`):
```
     def __str__(self):
         return str(self.value)

+    def __hash__(self):
+        return hash(self.value)
+
     def __eq__(self, other):
         ...
```

| # | model.py impl op (`ChoiceValue.membership_identity`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | receiver `self: ChoiceValue` with fields `value: int`, `instance: int` | `self` of `ModelChoiceIteratorValue` with attrs `value`, `instance` | R | the wrapper class refined to its two touched fields; `value` ↔ `int` key, `instance` ↔ opaque `int` object-identity (mapping.md §2). |
| A2 | `self.value` | `self.value` | I | the same field read; the wrapped stored value. |
| A3 | `value_identity(self.value)` | `hash(self.value)` | A-consumed | the new method defers to the unchanged stdlib `hash` on the bare value. `value_identity` is the weakest sufficient contract: a fixed pure (deterministic) function of its argument (mapping.md §3.1). The proof consumes it to discharge `Result() == value_identity(self.value)`. G-AX runs the real `hash` against it (determinism + the F2P non-collision). |
| A4 | `return value_identity(self.value)` | `return hash(self.value)` | I | the result of the callee is returned unchanged; the method body is a single return of the value's identity. |
| A5 | `Requires(MustTerminate(1))` (spec obligation, no impl op) | the gold body is a single bounded expression — it terminates on every input | I | total-correctness leg: Nagini defaults to partial correctness, under which a diverging impl (`while True: pass`) verifies vacuously yet its faithful patch (a hanging `__hash__`) does not resolve. The obligation pins the gold's actual termination behaviour; the straight-line gold body discharges it trivially. |

The discriminating content of the change — the wrapper's membership identity is
the identity of its **wrapped value** (so it is independent of the derived
object `instance`) — lives in the postcondition `Result() ==
value_identity(self.value)`. The pre-patch class defined `__eq__` without
`__hash__`, so its membership identity was governed by the object/instance, not
by `value` (mapping.md §1); `model_prepatch.py` reproduces that
(`return value_identity(self.instance)`) and **fails** the postcondition
`Result() == value_identity(self.value)` — exactly the spec sensing the change
(G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The only operation the change *adds* —
hashing the wrapped value — is a call into the **unchanged** stdlib `hash`
primitive, modeled by the `value_identity` **A-consumed** axiom (an unchanged
callee the new code invokes, not the operation under change being hidden behind
an axiom). The "operation under change" is the *method definition itself*
(`__hash__`), which is modeled directly and verified, not axiomatized. There is
no deep-model A-reference here: the change is a one-line delegation to a stdlib
primitive, so the primitive is a consumed axiom (its determinism is what the
postcondition rests on), and the F2P non-collision among distinct values is a
property of that primitive on the specific test inputs, checked by G-AX.

## C. verify(model) ⇒ resolved

`ChoiceValue.membership_identity` verifies only if it TERMINATES (A5 — the
`MustTerminate(1)` obligation rules out the vacuous divergence class: under
bare partial correctness an infinite loop satisfies every value postcondition
on its unreachable exit, yet a hanging `__hash__` never passes the F2P test)
and its result equals `value_identity(self.value)` (A3/A4) — a function of
`value` alone, never of `instance` (which is held read-only at
`Acc(..., 1/2)` and forbidden from the result, directive 5). By R (`ChoiceValue` ↔ `ModelChoiceIteratorValue`,
`value`/`instance` field bijection) and A-consumed (`value_identity` ↔ `hash`)
the verified method equals `return hash(self.value)` on the tested inputs — the
gold patch's `__hash__` verbatim. By G-AX the real `hash` is deterministic
(equal values ⇒ equal identity, so a wrapper agrees with the bare value and
with another wrapper of the same value — F2P assertion 1) and does not collide
on the distinct auto-increment pks the F2P test uses (F2P assertion 2).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the one audited callee — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom
soundness (G-AX) and refinement fidelity (this document, G-EQ).
