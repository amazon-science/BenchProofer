# refinement.md — sympy__sympy-13091

Operation-by-operation correspondence between `Solution.lean`'s impl regions (the
`directEquality` / `equalityCompare` / `inequalityCompare` `do` blocks and the
deep `eqResult` / `resolveEq` / `neResult` models) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A-consumed** /
**A-reference** (axiom legs — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); there are no A legs (no axioms), so G-AX is not applicable. Claim: any
impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. `__eq__`'s verdict — behaviour A (`directEquality`)

Gold hunk (`sympy/core/basic.py`, replicated at `numbers.py:1261/1722/3342`):
```
-                return False    # sympy != other
+                return NotImplemented
```
Effect: when `__eq__` cannot interpret its operand (`_sympify` rejected it), it
returns the `NotImplemented` sentinel — declining to decide — instead of deciding
`False`. This lets the `==` operator delegate to the operand's reflected `__eq__`.

| # | Solution.lean impl op (`directEquality`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `operand : Operand` | the value `other` after the type/`_sympify` checks in `__eq__` | R | `other` ↔ `Operand` (mapping.md §2). |
| A2 | `| .foreign => .undecided` | (post-image) `return NotImplemented` | I | **the behavioural change**: an uninterpretable operand yields the delegation sentinel, not `False`. Pre-image returned `False` (`.isFalse`). |
| A3 | `| .matchingEqual => .isTrue` | `return self._hashable_content() == other._hashable_content()` (when equal) | I | unchanged: an interpretable, equal operand decides `True`. |
| A4 | `| .matchingUnequal => .isFalse` | `return False` (type mismatch) / `_hashable_content` mismatch | I | unchanged: an interpretable but differing operand decides `False`. This `return False` (the `type(self) != type(other)` arm, `basic.py:319`) is NOT the changed line and is preserved. |

## B. `==` operator dispatch — unchanged mechanism (`equalityCompare`)

| # | Solution.lean impl op (`equalityCompare`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `let selfV ← directEquality operand` | `self.__eq__(other)` | I | the left operand's verdict (callee-under-spec: `directEquality_correct` discharges it). |
| B2 | `resolveEq selfV reflectedV` | the CPython `==` rich-comparison dispatch (datamodel: try `self.__eq__`, on `NotImplemented` try reflected `other.__eq__`, else identity ⇒ `False`) | R | the unchanged language mechanism, modeled deeply. `reflectedV` is the foreign object's own outcome — a free input. Not edited by the patch; present so behaviour A's effect (delegation) is observable. |

## C. `__ne__`'s negation — behaviour B (`inequalityCompare`)

Gold hunk (`sympy/core/basic.py:332`, replicated at every `__ne__` site):
```
-        return not self.__eq__(other)
+        return not self == other
```
Effect: inequality negates the `==` OPERATOR'S resolved decision (which delegates
on the sentinel) instead of negating the raw `__eq__` method result. Negating the
raw result is wrong because `not NotImplemented` is `False` in Python — so a
delegated-then-resolved-unequal pair would wrongly report `!=` as `False`.

| # | Solution.lean impl op (`inequalityCompare`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | `let selfV ← directEquality operand` | the `self == other` operator's consultation of `self.__eq__` | I | callee-under-spec. |
| C2 | `let eq := resolveEq selfV reflectedV` | (post-image) `self == other` — the operator, honouring delegation | R | **the behavioural change**: `__ne__` routes through the `==` operator (`resolveEq`), not the raw method. Pre-image was `not self.__eq__(other)` — negating `selfV` directly, where `.undecided` would negate to `false`. |
| C3 | `return !eq` | `return not (self == other)` | I | the negation itself, unchanged. |

No A (axiom) steps; no kind-3 (changed-inexpressible) steps. The two changed
behaviours are modeled **deeply** (`eqResult` for A, `resolveEq`+`neResult` for B),
not hidden behind an axiom about the function under change.

## D. verify(Solution) ⇒ resolved

`directEquality` verifies only if `operand = .foreign → out = .undecided` (A2 —
the F2P behaviour). `inequalityCompare` verifies only if
`(operand = .foreign ∧ reflectedV = .undecided) → out = true` and
`(operand = .foreign ∧ reflectedV = .isTrue) → out = false` (C2 — delegation
honoured before negation). By R (mapping.md §2) these equal the patched
`__eq__`/`__ne__` behaviour.

The two F2P tests pin exactly this:
- `test_equality` (in `test_basic.py`): a foreign `Foo()` gives `b != foo`,
  `foo != b`, `not b == foo`, `not foo == b` (both `__eq__` decline ⇒ identity
  fallback `False`; A2 + B2 + C2); and `Bar` (which returns `True` for any
  `Basic`) gives `b == bar` AND `bar == b` symmetrically — reachable only because
  `Basic.__eq__` returns `NotImplemented` so `b == bar` delegates to `Bar.__eq__`
  (A2 + B2 with `reflectedV = .isTrue`).
- `test_comparisons_with_unknown_type` (in `test_numbers.py`): the identical
  behaviour for `Integer`/`Float`/`Rational` (and `oo`/`nan` for which `Bar`
  itself returns `False`), plus the `raises(TypeError, ...)` rows for the ordering
  operators — which the modeled functions do not touch (out of scope, unchanged).

By G-CONF the R/I transliteration of `eqResult`/`resolveEq`/`neResult` agrees with
`patch.diff`'s behaviour over the full 9-combination input space plus fuzz.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). There are
no axiom trust points; the only trust point is refinement fidelity (this doc,
G-EQ + G-CONF).

## E. The two prepatch variants (G-DIFF)

- `Solution_prepatch.lean` — behaviour **A** reverted: `directEquality .foreign =
  .isFalse` (the pre-patch `return False`). Fails the frozen
  `operand = .foreign → out = .undecided` clause. This is the bug `test_equality`'s
  `Bar` case catches (`bar == b` would be `False`, asymmetric).
- `Solution_prepatch_ne.lean` — behaviour **B** reverted: `inequalityCompare`
  negates the raw verdict (`.undecided ↦ false`) instead of the operator-resolved
  decision (the pre-patch `not self.__eq__(other)`). Fails the frozen
  `(operand = .foreign ∧ reflectedV = .undecided) → out = true` clause. This is
  the bug the `b != foo` / `foo != b` assertions catch.

Two independently-observable fixed behaviours ⇒ two prepatch files (SPEC_GUIDE
§1.1).
