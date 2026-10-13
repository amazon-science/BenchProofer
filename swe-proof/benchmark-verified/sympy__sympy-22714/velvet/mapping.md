# mapping.md — sympy__sympy-22714

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 3ff4717b6aef6086e78f01cdfa06f64ae23aed7e`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo file under change: `sympy/geometry/point.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `imaginaryCoordCheck (coords : List Coord)` | the admissibility test inside `Point.__new__` — `sympy/geometry/point.py:153` (the `if any(...)` guard that raises `ValueError('Imaginary coordinates are not permitted.')`) | the modeled changed decision: does the constructor reject the coordinate list as imaginary? |
| `Coord` *(structure)* | one element `a` of the `coords` tuple inside `Point.__new__` | the per-coordinate observations the guard consults, abstracted (§2) |
| `coordImaginary (c : Coord)` | the per-element predicate of the `any(... for a in coords)` generator | pure spec: does one coordinate count as imaginary for the guard? |
| `anyImaginary (cs : List Coord)` | the `any(...)` aggregation over `coords` | pure spec: does ANY coordinate count as imaginary (the disjunction the `if` tests)? |

There is **no axiomatized callee** and **no A-reference deep model of an outside
callee**: the changed decision is a pure per-element predicate over the
coordinate list, modeled DEEPLY in the `pure` region. The functions the per-element
predicate consults on the Python side (the numeric-ness query and the
imaginary-part assessment) are not separately modeled — their *results* on each
coordinate are the abstracted observations `Coord` carries (§2), and G-CONF
recomputes those results from the **real** SymPy expressions, so no contract is
owed to them.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the `coords` tuple (a sequence of SymPy expressions) | `List Coord` | `coords` ↔ `coords.toList`-shaped `List Coord`; `len(coords)` ↔ `cs.length`; element order preserved (`any` is order-insensitive, but the carrier keeps order) |
| one coordinate expression `a` | `Coord` | abstracted to the three observations below |
| `bool(a.is_number)` — is the coordinate a concrete number? | `Coord.numeric : Bool` | `a.is_number` is `True` for concrete numbers, `False`/`None` for symbolic expressions; coerced with `bool(...)` |
| `a.is_number and im(a).is_zero is False` — the coordinate's imaginary part is **rigorously** determined to be nonzero | `Coord.imagNonzero : Bool` | `im(a).is_zero` is SymPy's three-valued zero test (`True`=provably zero, `False`=provably nonzero, `None`=indeterminate); the observation is the strict `is False`, i.e. provably-nonzero. **This is the only imaginary observation the modeled (post-change) decision reads.** |
| `bool(im(a))` — a coarse truth-value of the imaginary-part object | `Coord.imagPresent : Bool` | the plain truthiness of the imaginary-part expression: it is truthy whenever that expression is not the literal zero object. **Independent of `imagNonzero`:** when expression evaluation is suppressed the imaginary part of a real number is carried as an unsimplified expression that is truthy even though it is provably zero. This observation is NOT consulted by the modeled decision; it is carried so the pre-patch skeleton (`Solution_prepatch.lean`) can reproduce the historical decision rule, which `Solution.lean`'s frozen spec then refutes (G-DIFF). |

`coordImaginary c := c.numeric && c.imagNonzero` is the modeled per-element
predicate; `anyImaginary` is its disjunction over the list. The constructor
raises `ValueError('Imaginary coordinates are not permitted.')` **iff**
`anyImaginary coords = true`; otherwise construction proceeds. `imaginaryCoordCheck`
returns that boolean (the directly-changed decision), not the downstream raise.

## 3. Callee provenance (kind-A)

**None.** This bundle has no `axiom` and no A-reference deep model. The changed
operation is a self-contained per-element predicate over the coordinate list
(§1, §2), modeled deeply. The two SymPy queries the predicate uses
(`a.is_number` and the three-valued `im(a).is_zero`) are UNCHANGED by the patch
and are consulted only to produce the per-coordinate observations
`Coord.numeric` / `Coord.imagNonzero`; G-CONF computes those observations from
the real SymPy expressions (`a.is_number`, `im(a).is_zero`) at base_commit, so
their behaviour is exercised against reality rather than axiomatized. Hence
`axiom_check.py` is absent (G-AX skips: "no axioms in bundle").

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`22714`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow transliterates
`coordImaginary`/`anyImaginary` to Python (`any(c.numeric and c.imagNonzero ...)`);
the oracle is the patched per-element guard
`any(a.is_number and im(a).is_zero is False for a in coords)` evaluated over the
**real** SymPy expressions (the post-image of `point.py:153`, transliterated
verbatim), plus a set of end-to-end `Point(*coords)` boundary checks (including
the `evaluate(False)` regression case) that assert the abstraction predicts the
real constructor's raise / no-raise outcome.
