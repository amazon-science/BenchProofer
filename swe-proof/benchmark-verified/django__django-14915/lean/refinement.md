# refinement.md — django__django-14915

One modeled behavior: making the select-widget choice-value wrapper
(`ModelChoiceIteratorValue`) usable as a dict key / set member by giving it a
hash digest. The gold patch adds a single `__hash__` method:

```python
def __hash__(self):
    return hash(self.value)
```

## Type refinement (R)

| Python reality | Lean model | tag |
|---|---|---|
| `ModelChoiceIteratorValue` instance (`self.value`, `self.instance`) | `structure ChoiceValue { val : Int, inst : Option ModelInstance }` | R |
| `self.value` (the wrapped choice value; a model pk in practice, an `int`) | `m.val : Int` | R |
| `self.instance` (the model object the value was produced from; may be `None`) | `m.inst : Option ModelInstance` (`ModelInstance` opaque) | R |
| `hash(x)` — the builtin digest of the wrapped value | `valueHash : Int → Int` (opaque callee) | A-reference |
| object **is hashable** / a digest can be obtained | result `Option Int`: `some d` = hashable, `none` = unhashable | R |

## Operation correspondence

| # | `implementation_choiceValueHash` op | `patch.diff` op | tag |
|---|---|---|---|
| 1 | `return some (valueHash m.val)` | `def __hash__(self): return hash(self.value)`; the resulting object is hashable | R + A-reference |

* **Op #1 — R (Option carrier).** Post-patch, `__hash__` is defined, so the
  object is hashable and `hash(value)` is its digest. The `some _` wrapper is the
  type-refinement carrier for "hashable / digest obtainable". Pre-patch, the class
  defines `__eq__` without `__hash__`, so Python sets `__hash__ = None` and the
  object is **unhashable** — modeled as `none`. The discriminating clause is
  `result = some (valueHash m.val)`: the post-patch impl satisfies it, the
  pre-patch impl (`none`) cannot (`none = some _` is unprovable). This is the
  exact bug (`TypeError: unhashable type`) the F2P test `test_choice_value_hash`
  exercises.
* **Op #1 — A-reference (`valueHash`).** `hash(self.value)` calls the standard
  builtin `hash` on the wrapped value. This is an UNCHANGED callee — the patch
  does not change how a plain value is hashed; it only routes the wrapper's digest
  through it. Modeled as opaque `valueHash : Int → Int`, used identically in spec
  and impl. The proof consumes no property of it (the spec equates the result to
  `valueHash m.val` syntactically), so it is an A-reference, NOT a consumed axiom;
  `axiom_check.py` validates that the real `hash(value)` is the digest the
  post-patch `__hash__` returns. No dead `axiom` is shipped.

No `I` ops. No changed-inexpressible op.

## Frame (directive 5)

The result is pinned entirely to `m.val`; `m.inst` does not appear on the
right-hand side of `problem_spec_choiceValueHash`. This is the substantive content
of the test's first assertion — `hash(value_1) == hash(ModelChoiceIteratorValue(self.c1.pk, None))` —
that the digest depends only on the value, not on the accompanying model object.
A spec that left the digest free of `m.inst` only implicitly would permit a wrong
impl reading `m.inst`; pinning the RHS to `valueHash m.val` forbids it.

## Grounding (directive 8)

The digest is `valueHash m.val`, a function of the actual input value carrier
`m.val` — not an axiomatized answer-key the impl could echo. The second test
assertion (`hash(value_1) != hash(value_2)` for distinct pk values) is the
input-grounding witness: distinct values give distinct digests because the digest
is *produced by* applying `valueHash` to `m.val`.
