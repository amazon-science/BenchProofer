# refinement.md — django__django-15315

The operation-by-operation correspondence between `model.py`'s implementation
(the `located_value` impl region) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A-consumed** (the proof uses this axiom's
contract), **A-reference** (a deep model validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The hash site — `Field.__hash__` (`django/db/models/fields/__init__.py:544`)

Gold hunk:
```
 def __hash__(self):
-    return hash((
-        self.creation_counter,
-        self.model._meta.app_label if hasattr(self, 'model') else None,
-        self.model._meta.model_name if hasattr(self, 'model') else None,
-    ))
+    return hash(self.creation_counter)
```

| # | model.py impl op (`located_value`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `self: Descriptor` with field `self.order` | `self` (a `Field`) with attribute `self.creation_counter` | R | `Field` ↔ `Descriptor`; `creation_counter` (int) ↔ `order` (int), identity (mapping.md §1, §2). |
| A2 | `hash_int(self.order)` | `hash(self.creation_counter)` | A-consumed + R | `hash` on a single int is the unchanged primitive, axiomatized as `hash_int` (the proof consumes only its determinism, which `@Pure` grants); the argument is the int field under R. The post-fix body hashes the creation-order identity alone (mapping.md §3.1). |
| A3 | `return hash_int(self.order)` | `return hash(self.creation_counter)` | I | identical `return` of the hashed value. |

The fields `has_owner`, `owner_label`, `owner_name` appear in the modeled
`Descriptor` (and in the spec's permission footprint) but the **gold impl never
reads them** — exactly mirroring the gold body, which after the fix references
neither `hasattr(self, 'model')` nor `self.model._meta.*`. Their presence in
the spec lets the postcondition `Result() == hash_int(self.order)` assert the
located-value is a function of `order` ALONE: independent of the attachment
flag and of both owner-derived attributes. That independence IS the
stability-under-attachment guarantee the issue and the F2P test demand.

**Existence-conditioned permissions (attribute-error faithfulness).** The
owner-derived attributes exist in the real program only once the field is
attached (`self.model` is set by `contribute_to_class`); reading
`self.model._meta.*` on an UNattached field raises `AttributeError`, and the
F2P test hashes an unattached field first — so a `__hash__` that reads the
owner attributes unconditionally does NOT resolve even if it returns
`hash(self.creation_counter)` (empirically confirmed: the audited attack
`_shadow = self.model._meta.app_label; return hash(self.creation_counter)`
errors the F2P test with `AttributeError: 'IntegerField' object has no
attribute 'model'`). The spec pins this: permission on `owner_label` /
`owner_name` is granted only under `Implies(self.has_owner, ...)`, so a
verifying implementation can read an owner attribute only after establishing
attachment — the model analogue of the `hasattr(self, 'model')` guard. A
guarded read followed by the order-only return remains admitted (its faithful
real patch resolves), so the spec is not over-tightened.

**Total correctness (termination obligation).** The spec carries
`Requires(MustTerminate(2))` on `located_value` (and `MustTerminate(1)` on the
`Descriptor` constructor so an obligated caller can construct descriptors).
Under partial correctness alone, a diverging implementation — an infinite loop
in place of the return — verifies vacuously (every value postcondition holds on
the unreachable exit), yet its faithful real counterpart is a `__hash__` that
never returns, which hangs every hash-container lookup and the F2P test, so it
does NOT resolve. The obligation closes that class: every loop must supply a
decreasing termination measure. The gold body is a single straight-line
delegation to the hashing primitive and discharges the obligation trivially, so
the obligation is faithful (the real method terminates), not over-tightened —
confirmed by the positive controls, which all still verify.

## B. The discriminating clause (G-DIFF)

The pre-fix body hashed the 3-tuple `(creation_counter, app_label_or_None,
model_name_or_None)`, whose last two slots become non-`None` once the field is
attached to a model — so the located-value CHANGES across attachment.
`model_prepatch.py` reproduces this faithfully under the shared (byte-identical)
spec: on the `has_owner` branch it returns
`hash_int(self.order + self.owner_label + self.owner_name)` — a value that folds
in the owner-derived attributes, exactly as the real 3-tuple hash does. It
**fails** the postcondition `Result() == hash_int(self.order)` on that branch
(verifier: `model_prepatch.py:77 — Assertion (Result() == hash_int(self.order))
might not hold`), which is precisely the spec sensing the bug the F2P test
`test_hash_immutability` catches.

(The prepatch expresses the owner-dependence using only the shared `hash_int`
axiom rather than a second tuple-hash axiom, so the spec — including the axioms
region — stays byte-identical to `model.py` as G-DIFF requires. The essential
property under test, "the located-value depends on the owner-attachment state,"
is preserved: any owner-derived term inside `hash_int` breaks the order-only
postcondition.)

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The operation that genuinely *changed*
— hashing only the creation-order identity instead of a model-dependent tuple —
is expressed directly: the modeled `located_value` hashes `self.order` alone and
the postcondition pins the result to `hash_int(self.order)`, independent of the
owner fields. The single consumed axiom, `hash_int` (**A-consumed**, site A),
covers the **unchanged** hashing primitive the new code invokes; it is NOT the
operation under change. axiom_check.py also validates the A-reference oracle
(that `hash(creation_order)` is invariant under attachment while the pre-fix
tuple-hash is not), tying the deep model to the real builtin (G-AX).

## D. verify(model) ⇒ resolved

`located_value` verifies only if its result equals `hash_int(self.order)` — a
function of the creation-order identity alone, with no dependence on the
attachment flag or owner-derived attributes (A2). By R (`Field` ↔ `Descriptor`,
`creation_counter` ↔ `order`, identity on `int`) the verified function equals
`hash(self.creation_counter)` on every field, which is the gold body verbatim.
By G-AX the axiom `hash_int` over-approximates the real builtin `hash` on an int
(determinism), and the deep oracle (`hash(creation_order)` stable under
attachment) holds. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and the audited callee — and the
gold patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN
§1.1: axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
