# mapping.md — sympy__sympy-13615

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 50d8a102f0735da8e165a0369bbb994c7d0592a6`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the one opaque callee.

Repo file under change: `sympy/sets/sets.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `complementFinite (elems : List Int)` | `Set._complement(self, other)` — `sympy/sets/sets.py:188`; the modeled branch `elif isinstance(other, FiniteSet):` at `sets.py:218–220` | the modeled changed function: the relative complement of a finite operand `other` against the ambient set `self` |
| `contains` *(opaque — unchanged callee)* | `self.contains(el)` — `Set.contains`, `sympy/sets/sets.py:291` (returns `S.true` / `S.false` / a symbolic `Contains` object) | the ambient set's membership oracle, consulted once per element; UNCHANGED by the patch |
| `Trit` (`inside` / `outside` / `unknown`) | the three observable outcomes of `self.contains(el)`: `S.true`, `S.false`, and "neither" (a symbolic `Contains`, i.e. `contains not in [True, False]`) | three-valued membership verdict |
| `definiteOut` (pure) | the elements that become definite members — post-patch `sifted[False]` routed into `FiniteSet(*(sifted[False]))` (`sets.py` gold hunk) | pure spec: the definite members of the complement |
| `symbolicUnknown` (pure) | the elements retained symbolically — post-patch `sifted[None]` routed into the unevaluated `Complement(FiniteSet(*(sifted[None])), self, evaluate=False)` | pure spec: the undetermined elements held for symbolic handling |
| `Partition { definite, symbolic }` | the two non-dropped element groups the post-patch `Union(FiniteSet(*sifted[False]), Complement(FiniteSet(*sifted[None]), self, …))` is built from | the two-part result the gold assembles |

The element class NOT represented in `Partition` is `sifted[True]` — the
elements `self.contains` decides ARE in the ambient set; the gold drops them
("ignore those that are contained in self"), exactly as `Trit.inside` appears in
neither `definiteOut` nor `symbolicUnknown`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `other` — a `FiniteSet` of distinct sympy elements (`other.args`, iterated by `for el in other`) | `elems : List Int` | each sympy element ↔ a distinct `Int` handle (an opaque token; only its membership verdict is observed, never its value). `len(other.args)` ↔ `elems.length`. Order is the iteration order of `other`. |
| `self.contains(el) ∈ [True, False] / else` | `Trit` (`inside` / `outside` / `unknown`) | `S.true` ↔ `Trit.inside`; `S.false` ↔ `Trit.outside`; a symbolic `Contains` (`contains not in [True, False]`) ↔ `Trit.unknown`. This IS the gold's `ternary_sift`: `contains if contains in [True, False] else None`. |
| `sift(other, ternary_sift)[False]` (a `list`, order-preserving) | `definiteOut elems` | the order-preserving sublist of `elems` whose verdict is `outside`; `FiniteSet(*xs)` is order-/dup-insensitive, so list order is observationally free here, but the model preserves it for a faithful R leg |
| `sift(other, ternary_sift)[None]` (a `list`) | `symbolicUnknown elems` | the order-preserving sublist of `elems` whose verdict is `unknown` |
| `sift(other, ternary_sift)[True]` (dropped) | (absent from `Partition`) | the `inside`-verdict elements; not retained in either field |

`Int` is used as an opaque element-handle carrier only: the spec NEVER does
arithmetic on it; the sole operation on an element is `contains el`. This matches
the repo, where `el` is an arbitrary sympy `Expr` and the only thing read off it
is `self.contains(el)`.

## 3. Callee provenance — the opaque membership oracle (checked by G-AX)

### 3.1 `contains` ↔ `Set.contains` (opaque, unchanged callee)
**Callee:** `Set.contains(self, other)` (`sympy/sets/sets.py:291`). For a fixed
ambient set `self` it is a deterministic map from an element to one of three
observable verdicts:

```python
def contains(self, other):
    other = sympify(other, strict=True)
    ret = sympify(self._contains(other))   # may be S.true, S.false, or None
    if ret is None:
        ret = Contains(other, self, evaluate=False)   # a symbolic, un-booleable object
    return ret
```

`ret` is `S.true` / `S.false` when membership is decidable, and otherwise a
symbolic `Contains` instance (which is `not in [True, False]`). The gold's
`ternary_sift` reads exactly this trichotomy:
`contains if contains in [True, False] else None`.

`contains` is modeled **`opaque`, not `axiom`**: it asserts no value contract,
only determinism (a fixed element handle has a single fixed verdict). This is the
weakest sufficient contract (SPEC_GUIDE directive 7) — it cannot over-claim a
verdict, a value, or a raise behavior — and it keeps the symbol computable inside
the `do` block. The membership oracle is UNCHANGED by the patch (the patch only
re-routes elements *based on* its verdict), so there is no changed operation
hidden behind it; there is no A-reference deep model and no value `ensures` to
validate.

**Soundness check (G-AX):** because `contains` carries no value contract, G-AX
has no axiom `ensures` to refute. `axiom_check.py` instead (a) asserts the bundle
declares no value-bearing axioms / no A-references (so a future edit that smuggles
one in without a check is caught), and (b) exercises the REAL `Set.contains` /
`ternary_sift` trichotomy in-container — over decided-inside (e.g. a number in an
`Interval`), decided-outside (a number outside it), and undetermined (a free
`Symbol`) cases, plus fuzz — confirming every observation lands in exactly one of
`{True, False, None}`, i.e. that the `Trit` carrier is total and the
`ternary_sift` partition mapping.md §2 claims is faithful. Imports only sympy +
stdlib. Exit 0 iff sound.

### 3.2 Flag/configuration dependencies
None. `Set.contains` takes no flags; its verdict depends only on `self` and the
element. G-AX fuzzes a representative ambient set (`Interval`) plus the symbolic
case; the trichotomy is configuration-independent.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13615`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`definiteOut`/`symbolicUnknown` (the R/I-tagged selections) to Python and bridges
the `Trit` verdict via the real `self.contains(el) in [True, False] else None`
trichotomy (the opaque callee left as the real `Set.contains`), diffing the
two-part result against the gold `patch.diff` behaviour (`sifted[False]` and
`sifted[None]`).
