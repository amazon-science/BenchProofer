# refinement.md — django__django-14915

Correspondence between `Solution.lean`'s `choiceValueHash` impl and
`patch.diff`. The gold patch ADDS a `__hash__` method to
`class ModelChoiceIteratorValue`, body `return hash(self.value)`. `patch.diff` is
the gold verbatim (applies at base_commit, resolves — G-RESOLVE).

## A. The added method — `ModelChoiceIteratorValue.__hash__`

Gold hunk: an addition into `class ModelChoiceIteratorValue` between `__str__`
and `__eq__`:
```
+    def __hash__(self):
+        return hash(self.value)
+
```
Net effect: the wrapper becomes HASHABLE, with a hash determined by its wrapped
value. Before the patch, defining `__eq__` without `__hash__` caused Python to
set `__hash__ = None` automatically, so the object was UNHASHABLE (using it as a
dict key / set member / `in` a dict raised `TypeError: unhashable type`).

| # | Solution.lean impl op (`choiceValueHash`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `value : Int` | `self.value` (the wrapped value) | R | the wrapped value (a pk integer in the F2P test) ↔ Lean `Int` (mapping.md §2). |
| A2 | `valueHash value` | `hash(self.value)` | **A-consumed** | unchanged library hashing of the wrapped value, modeled as an OPAQUE free function with NO asserted concrete value. The proof/structure consumes it as an opaque term; its concrete output is salt-/implementation-dependent, so G-AX has nothing to check (mapping.md §3). |
| A3 | `return valueHash value` (post-image `h = valueHash value`) | `return hash(self.value)` | **I** | identical concrete op — the discriminating behavior the fix introduces: the wrapper's hash IS the hash of its wrapped value (a deterministic function of `value`). |

No kind-3 (changed inexpressible) op. The impl region is all-A-tagged (the
single op is the opaque value hash); the discriminating change — that the hash
is *determined by* the value — is the structural post-image `h = valueHash
value` and is what the spec pins.

### Discriminating behavior (the "I")
The behavior the fix establishes is: **the wrapper's hash is a function of its
wrapped value** — equal values produce equal hashes, and the object is hashable.
This is exactly what makes the F2P test pass:
`hash(value_1) == hash(ModelChoiceIteratorValue(self.c1.pk, None))` (same `value`
⇒ same hash, regardless of the companion `instance`) and
`hash(value_1) != hash(value_2)` (different `value` ⇒ different hash, when the
underlying value hashes differ). The spec `h = valueHash value` captures both:
the result depends on `value` and on nothing else.

## B. verify(Solution) ⇒ resolved

`choiceValueHash` verifies only if `h = valueHash value` (A2-A3). By R (the type
bijection, mapping.md §2) the verified result equals the patched
`hash(self.value)` on the real wrapper. Because the result is a function of
`value` alone, two wrappers with the same `value` necessarily hash equal (F2P
first assertion) and the object is hashable (F2P prerequisite — no `TypeError`),
while different underlying values give the (distinct, when `hash` distinguishes
them) value hashes (F2P second assertion).

## C. Prepatch fails on the discriminating clause (G-DIFF)

`Solution_prepatch.lean` (byte-identical spec) returns the constant `0` — the
pre-image of the bug, where the wrapper exposed NO value-determined hash (Python
auto-set `__hash__ = None`, making the object unhashable / its hash not a
function of the value). Against the identical spec this leaves the unsolved goal

```
0 = valueHash value
```

which fails whenever `valueHash value ≠ 0` — i.e. for essentially every wrapped
value. This is precisely the missing "hash is determined by the wrapped value"
contract: the bug the issue describes (`TypeError: unhashable type:
'ModelChoiceIteratorValue'`, and the absence of a value-consistent hash).
Verified: `lean_verify` on the prepatch exits non-zero with exactly
`⊢ 0 = valueHash value`.

## D. Trust surface

Only the type bijection (mapping.md §2) and the OPAQUE value hash (A2). The
opaque callee asserts nothing about its concrete value, so it cannot mask a wrong
impl: the spec still forces the result to be `valueHash value` (the hash
determined by the wrapped value) regardless of which integers `hash()` produces.
The impl region is all-A-tagged, so there is no R/I leg to differential-test and
no DB-free cross-language shadow of `hash()` (salt-dependent) — G-CONF is
skipped (`conf_skip=true`, status=skip stub). No axiom_check needed (G-AX skip —
nothing asserted about the hash's value to validate). Soundness rests on
G-VERIFY + G-DIFF + G-RESOLVE.
