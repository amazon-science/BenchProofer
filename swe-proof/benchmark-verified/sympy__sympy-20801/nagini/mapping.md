# mapping.md — sympy__sympy-20801

Binds every `model.py` symbol to its repository counterpart at
`base_commit = e11d3fed782146eebbffdc9ced0364b223b84b6c`, states the type
abstraction, and records the provenance of the (single) modeled function.

Repo file under change: `sympy/core/numbers.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `float_equals(self_is_zero, kind, other_truthy, numeric_eq)` | `Float.__eq__(self, other)` — `sympy/core/numbers.py:1383` | the modeled changed function (equality of an exact floating value against an already-sympified operand) |
| `is_truth_value(kind)` | `isinstance(other, Boolean)` — `numbers.py:1391` (post-patch) | pure predicate: operand is a symbolic logical truth value |
| `is_irrational_const(kind)` | `other.is_NumberSymbol and other.is_irrational` — `numbers.py:1393-1395` | pure predicate: operand is an irrational named constant |
| `is_numeric_kind(kind)` | the four numeric branches `other.is_NumberSymbol(rational) / is_Float / is_Rational / is_Number` — `numbers.py:1393-1410` | pure predicate: operand defers to a kind-proper numeric-equality decision |
| `is_other_kind(kind)` | the fall-through past all numeric/boolean branches (`if not self: return not other`; else `return False`) — `numbers.py:1411-1412` (post-patch) | pure predicate: operand is neither a number nor a truth value — the only case the zero short circuit governs |
| `Requires(MustTerminate(1))` | the whole `Float.__eq__` body: a bounded, loop-free dispatch that returns a verdict on every in-domain operand (no loop, no recursion) | total-correctness obligation: forbids diverging implementations that would satisfy the value postconditions vacuously (Nagini's default is partial correctness); the real method discharges it trivially |

The pre-patch code the change relocates (for the refinement audit, not
referenced from the consumer spec view): the two lines

```python
if not self:
    return not other
```

which at `base_commit` sit at `numbers.py:1389-1390` — i.e. BEFORE the
`isinstance(other, Boolean)` test — and which the gold patch deletes from there
and re-inserts at `numbers.py:1411` (after all the boolean/number branches).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection / justification |
|---|---|---|
| `self`, a `Float` | `self_is_zero: bool` | the only facet of `self` the dispatch reads (other than the numeric value used by the numeric branches) is its Python truth value `not self`, which for a `Float` is `True` iff the mantissa is zero. `self_is_zero == (not self)`. |
| `other`, an already-sympified SymPy object | `kind: int` ∈ {0..6} | classification by the exact `isinstance`/`is_*` facets the dispatch tests, in dispatch order: 0 = `isinstance(other, Boolean)`; 1 = `other.is_NumberSymbol and other.is_irrational`; 2 = `other.is_NumberSymbol and not other.is_irrational`; 3 = `other.is_Float`; 4 = `other.is_Rational`; 5 = `other.is_Number` (none of the prior); 6 = none of the above. |
| `not other` (Python negation of the operand) | `other_truthy: bool`, with `not other` modeled as `not other_truthy` | `other_truthy == bool(other)`; e.g. `bool(S.false) == False`, so `not S.false == True`. |
| the kind-proper numeric-equality sub-result | `numeric_eq: bool` | for kinds 2 and 4 it is `bool(other.__eq__(self))` (delegation); for kind 3 it is `self._mpf_ == other._mpf_`; for kind 5 it is `bool(mlib.mpf_eq(self._mpf_, other._as_mpf_val(self._prec)))`. All three are UNCHANGED sub-decisions; the model carries the (kind-appropriate) result opaquely as one boolean. |
| `bool` returned by `__eq__` | `bool` returned by `float_equals` | identity. The `NotImplemented` path (raised `SympifyError` in the unchanged try/except preamble, `numbers.py:1385-1388`) is outside the modeled domain — it precedes and is untouched by the relocated block, and no F2P/P2P operand triggers it. |

The model's `kind == 2` branch corresponds to a real dispatch branch
(`other.is_NumberSymbol` true, `other.is_irrational` falsy →
`return other.__eq__(self)`). It IS reachable: `Catalan` and `EulerGamma` are
`NumberSymbol`s whose irrationality is unproven, so `is_irrational is None`
(falsy), which routes them through this branch (confirmed in the pinned eval
container: `Catalan.is_irrational is None`, `EulerGamma.is_irrational is None`).
pi, E and GoldenRatio have `is_irrational is True` and take the kind-1 branch.
The kind-2 verdict is the delegated equality `other.__eq__(self)` — an unchanged
sub-decision the model carries opaquely as `numeric_eq` — so this branch is
behaviour-neutral, and axiom_check.py exercises it (Catalan, EulerGamma in the
operand battery) to confirm the model's kind-2 verdict matches the real code.

## 3. Callees / axioms

**None consumed.** The change is a pure relocation of a control-flow block
within `Float.__eq__`; it calls no library callee that Nagini cannot express.
The numeric sub-decisions (`other.__eq__(self)`, the mpf compares) are UNCHANGED
sub-results carried opaquely as the boolean `numeric_eq` (a type refinement, R —
not an axiomatized callee whose `Ensures` the proof consumes). There is thus no
`@ContractOnly` axiom (the `axioms` region is empty) and no A-consumed row.

**Deep-model reference (A-reference, checked by G-AX / axiom_check.py).** The
dispatch itself is modeled DEEPLY (`float_equals` spells out every case). It is
validated equal to the real `Float.__eq__` out-of-band: `axiom_check.py`
classifies a battery of representative operands into the model's kind code,
feeds `float_equals` the same facets the real code reads, and asserts the model
verdict equals the real `self == other`. It exercises all reachable kinds
{0,1,2,3,4,5,6} over 7 floats × 23 operands (161 pairs), and witnesses the four
issue assertions. It imports only `sympy` (the repository under test) and the
standard library. It models the POST-PATCH function, so it must run with the
gold patch applied (apply_gold=True): at base_commit it correctly fails on the
buggy code. Soundness pinned at the post-patch repository (Python 3.x;
sympy 1.8), the configuration the harness evaluates.

## 4. Behavioural provenance of the pinned property

The issue (`problem_statement`) reports that a zero floating value compared with
the symbolic boolean `false` returns the wrong verdict in one comparison order:
`S(0.0) == S.false` yields `True`, while `S.false == S(0.0)`, `S(0) == S.false`
and `S.false == S(0)` all yield `False`. The desired behaviour, stated by the
issue, is that `S(0.0) == S.false` also be `False` — i.e. a floating value is
never equal to a symbolic boolean, regardless of order or of the float being
zero.

In the model this is exactly the postcondition
`Implies(is_truth_value(kind), Result() == False)`, which holds independent of
`self_is_zero` and `other_truthy`. It is the clause `model_prepatch.py` violates
(the zero short circuit `return not other_truthy` precedes the truth-value
case, so for `other == S.false` it returns `not False == True`).

## G-CONF

Differential conformance (`conformance_check.py`): the contract-stripped
`# impl-start`/`# impl-end` region of `model.py` (plus the four `@Pure` helpers,
both copied VERBATIM — verified byte-identical to the regions above) diffed
against the REAL gold-patched `sympy.core.numbers.Float.__eq__`
(`sympy/core/numbers.py:1383`, §1), which is CALLED, never reimplemented.
`_assert_patched()` inspects the loaded source and refuses to report a verdict
unless `if not self:` sits AFTER the `isinstance(other, Boolean)` test, so a
green run cannot come from unpatched code.

Type bridge = §2 inverted: real operands are constructed first, then classified
into `kind` 0..6 by exactly the `isinstance`/`is_*` facets the dispatch tests
(so `Requires(0 <= kind <= 6)` holds by construction), with
`self_is_zero = (not self)`, `other_truthy = bool(other)`, and `numeric_eq`
obtained by CALLING the repo's own unchanged sub-decisions (`other.__eq__(self)`
for kinds 2/4, the `_mpf_` tuple compare for kind 3,
`mlib.mpf_eq(self._mpf_, other._as_mpf_val(self._prec))` for kind 5).

* **Pinned seed: 20801.**
* **Inputs: 100 000** Requires-satisfying observations against the real function
  (540 exhaustive boundary matrix = 12 Floats × 45 operands, plus 99 460 seeded
  fuzz), covering all seven kinds and all eight impl branches.
* The modeled abstract domain is FINITE (2 × 7 × 2 × 2 = **56** points) and is
  enumerated **exhaustively**. Only **24** are realizable by a real
  `(Float, operand)` pair — the facets are not independent, since kinds 0/1/6
  always carry `numeric_eq` False — so at all 56 points the shadow is *also*
  audited against the five `Ensures` clauses. Without that audit a shadow
  returning `numeric_eq` in the kind-0 branch would pass the differential leg
  vacuously.
* The run FAILS if any impl branch or kind went unexercised, or if the
  discriminating witnesses are missing: kind 0 + `self_is_zero` + falsy operand
  (`S(0.0) == S.false`, the F2P shape), kind 6 + `self_is_zero` + falsy operand
  (`Float(0.0) == Tuple()` is really True — the relocated block's only surviving
  effect), and both `numeric_eq` values on kinds 3 and 4.

Negative controls (run out-of-band, not shipped): the prepatch shadow (zero
short circuit hoisted to the front) fails on `S(0.0) == S.false`; running
against the UNPATCHED repo with the source guard disabled fails the same way;
a shadow whose kind-0 branch returns `numeric_eq` fails the abstract Ensures
audit; a shadow negating the zero fall-through fails; and a generator with the
falsy kind-6 operands removed fails the witness obligation instead of reporting
green.
