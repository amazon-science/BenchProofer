# refinement.md — sympy__sympy-24213

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`combineAddends` `do` block, the deep `checkStep`/`checkAddends` model, and
`sumFactors`) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses an axiom's
`ensures`, **A-reference** where a deep model is validated == the real callee by
G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
A legs and this narrative are audited by **G-EQ**. Claim: any impl verifying
against this frozen spec, refined per the map below, is behaviourally equal to the
gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The Add-branch dimension test — `_collect_factor_and_dimension` (`sympy/physics/units/unitsystem.py:178`)

Gold hunk:
```
-                if dim != addend_dim:
+                if not self.get_dimension_system().equivalent_dims(dim, addend_dim):
```

| # | Solution.lean impl op (`combineAddends`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `first : Addend`, `rest : List Addend` | the collected `(factor, dim)` of `args[0]` (`:174`) and the loop over `args[1:]` (`:175`), each addend's `(addend_factor, addend_dim)` from the recursive call (`:176-177`) | R | the recursive sub-collection is UNCHANGED; its results are read-only inputs (mapping.md §1, §2). `args[1:]` ↔ `rest`. |
| A2 | `first.factor : Int`, `a.factor : Int`; `factor := factor + a.factor` over the loop, then total `first.factor + sumFactors rest` | `factor += addend_factor` accumulated from `factor, dim = collect(args[0])` (`:174`, `:183`) | R + I | scale factor modeled order-only as `Int` (mapping.md §2); the accumulation `+=` is the concrete `sumFactors` fold. The F2P test observes only whether an error is raised, so the factor carrier need only respect `+`. |
| A3 | `checkStep first.dim.deps a rest'` per addend — the reduction attempted on BOTH sides first (`refDeps.isNone || a.dim.deps.isNone` ⇒ `unreducible`), then signature equality ⇒ defer / `disagreeing` — folded by `checkAddends first.dim.deps rest` | `self.get_dimension_system().equivalent_dims(dim, addend_dim)` (`:178` post-patch), guarding the loop | A-reference + I | the changed comparison is modeled **deeply**: `checkStep`/`deps`-equality (pure region) IS the dimensional-equivalence test. No consumed `equivalentDims` axiom. `equivalent_dims` REDUCES both arguments before comparing (`dimensions.py:429-430`) and that reduction is partial, so the model has a leg for each of its THREE outcomes, in the callee's own order: reduce-then-compare means an absent signature on either side preempts any verdict (`unreducible`), both present and unequal is a verdict of "not equivalent" (`disagreeing`), both present and equal certifies. The fold ops (`==`, `||`, the loop) are **I** (concrete, transliterated by G-CONF); the equality of the three-leg `deps`-comparison to the real `equivalent_dims` — including that a both-signatures-present pair RETURNS rather than raising — is the **A-reference** G-AX validates (mapping.md §3.1). Because the real branch evaluates the guard per addend inside `for addend in expr.args[1:]` and leaves the loop at the first addend it cannot carry through, `checkStep` is leftmost-failure: the deciding addend is the leftmost non-certified one and the outcome is the manner in which IT failed. |
| A4a | `return Combined.reported factor first.dim` | all equivalent: fall through to `return factor, dim` (`:184`) | R | `reported f d` ↔ the returned `(factor, dim)`. |
| A4b | `return Combined.disagreement` | some addend compared and found not equivalent: the branch reports a dimensional disagreement (`:179-182`) | R | a REQUIRED, distinguished observation. What a caller is handed here is specifically the claim that the addends' dimensions were compared and disagree, and the repository's own consistency checks grade sums by receiving exactly this report by CLASS — five such assertions sit in the P2P set. So this outcome may not be answered with the A4c one. |
| A4c | `return Combined.noSignature` | a dimension in play has no signature, so the reduction inside the guard fails before any comparison and the combination is abandoned (`dimensions.py:383-395`) | R | a DIFFERENT observation from A4b: no verdict about dimensional agreement was ever produced. Deliberately ASYMMETRIC with A4b — the spec fixes only that no value is reported here and that it is not reported as a disagreement, leaving the particular manner of the abandonment free, because nothing in the graded behaviour observes it (mapping.md §2.2 records the four-way measurement establishing exactly that asymmetry: reporting a disagreement instead of A4c fails a graded consistency test, while varying A4c's manner alone fails nothing). Pinning a manner here would be true of gold and false of correct alternatives. |
| A4d | which of A4b / A4c holds when a sum reaches BOTH | the `for` walk over `args[1:]` evaluates the guard per addend and leaves at the first addend it cannot carry through (`:175-182`) | I | not free: measured on the patched tree, two sums with dimensionally identical addends differing only in WHERE the signature-less one falls give different outcomes, so the ordering is observable. `checkStep`'s front recursion is that order (G-CONF pins both probes and fails if they ever agree). |

Discriminating content of the change — surface inequality (`dim != addend_dim`)
→ dimensional-equivalence (`equivalent_dims`) — lives in the spec invariant
`chk = checkAddends first.dim.deps (rest.drop i)` ⇔ the `equivalent_dims` guard
(real). The pre-patch compared surface expression identity;
`Solution_prepatch.lean` reproduces that (`a.dim.surf == first.dim.surf`) and
**fails** the invariant `chk = checkAddends first.dim.deps ...` (G-DIFF), because
`surf`-equality is not `deps`-equality (two surface-distinct dimensions can share a
signature), and because a surface test reduces nothing and so can never reach the
signature-less outcome at all.

The surface-distinct-but-equivalent class the discriminator rests on has TWO
independent sources under the mapping.md §2.1 bijection, and both are ordinary
user input:
1. **different base decompositions** of the same signature — the issue's
   `velocity` vs `acceleration*time`, `force` vs `mass*acceleration`;
2. **different numeric TYPES or `Float` precisions in an exponent** — SymPy numbers
   compare equal across type while hashing differently, so `Dimension(length**2)`
   and `Dimension(length**2.0)` are surface-distinct (structural `Dimension.__eq__`
   keeps a nested number's type) yet `equivalent_dims` accepts them (dict `==`
   compares the powers with SymPy `==`, and `Integer(2) == Float(2.0)`). Reached by
   `meter**2 + meter**2.0`, with the `Float` exponent flowing out of the UNCHANGED
   `Pow` branch (`unitsystem.py:167-172`).
Source 2 is what a `hash`/`frozenset` key over the dependency dict silently loses:
such a key is strictly FINER than the dict `==` the real callee performs, so it
would report `none`/`ValueError` where the patched repo returns a result. Both
sources are now covered by G-AX's boundary pairs and G-CONF's term pool.

There is a THIRD class the change is observable on, and it runs the other way —
post-patch reports NO value where pre-patch returned one. `equivalent_dims`
reduces both arguments before comparing, and that reduction is partial
(`dimensions.py:383-395`), whereas the pre-patch surface test `dim != addend_dim`
reduced nothing and so could never fail that way. With `b1`, `b2` of dimension
`Dimension(length+time)` (an `Add`-named dimension, unreducible) and scale factors
1 and 2, measured at `base_commit` and `base_commit + patch.diff`:

| input | pre-patch | post-patch |
|---|---|---|
| `b1 + b2` | `(3, Dimension(Dimension(length, L) + Dimension(time, T)))` | `TypeError` — no value |
| `b1 + l1`, `l1 + b1` | `ValueError` — no value | `TypeError` — no value |

So this class is INSIDE the modeled behaviour, not outside it: the first row is a
genuine patch delta. `Dim.deps` is therefore `Option Int` and `checkStep` attempts
the reduction on both sides before comparing, which sends every row above to a
value-less outcome.

Note what the second row shows, and what an earlier revision of this doc got
wrong. Both `b1 + l1` rows report no value, pre- AND post-patch — but they report
DIFFERENT things, and one of the two is graded. That is why A4b and A4c are
separate outcomes rather than one value-less inhabitant: with a single one, the
choice between them was free, and an implementation answering every abandoned
combination with the disagreement report satisfied the whole contract while being
observably different from the real routine on a graded test. The earlier
justification here — that the exception TYPE is not observable because the F2P
test only asserts a value comes back — was refuted by the P2P half of the graded
set, which asserts the disagreement report BY CLASS five times over. The
correctness claim of this bundle is over BOTH halves, so `Combined` carries three
outcomes.

`properties.py` holds the reject witnesses for each way of getting this wrong
while agreeing with gold everywhere else: `rival-missing-signature-wildcard`
(reports no value even where a signature exists),
`rival-collapse-to-disagreement` and `rival-collapse-to-nosignature` (the two
outcome-identity collapses), and `rival-priority-inverted` (right multiset of
failures, wrong deciding addend). The frozen spec must reject all four.

## B. No second change site

The gold patch is a single one-line hunk; there is no independently-observable
second fixed behavior, so a single `Solution_prepatch.lean` suffices (G-DIFF).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — the
dimension comparison — is modeled **deeply** (the spelled-out `checkAddends` fold
over `checkStep`, step A3, an A-reference + I), not hidden behind an axiom about the
function under change: there is no consumed `equivalentDims` axiom. The only kind-A
content is the A-reference deep model of the UNCHANGED callee `equivalent_dims`,
validated by G-AX.

## D. verify(Solution) ⇒ resolved

`combineAddends` verifies only if its `chk` accumulator equals `checkAddends
first.dim.deps rest` (A3) and, for EACH of the three values that fold can take,
the result is the matching one of A4a/A4b/A4c — the three implication `ensures`
pin the legs separately, so no leg can be answered with another leg's outcome and
no two of them can be collapsed. By R (`args[1:] ↔ rest`, factor order model, the
outcome correspondence A4a–A4d) the verified combination equals the patched Add
branch on the tested inputs, on both halves of the graded set: the reported-value
leg (F2P) and the disagreement-report leg (P2P consistency). By G-AX the deep
model `deps`-equality equals the real `equivalent_dims`, and a both-signatures-
present pair returns rather than raising (A-reference). By G-CONF the R/I
transliteration of the fold agrees with `patch.diff`'s behaviour, graded three
ways, on ≥10⁵ inputs including the ordering probes of A4d. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
the audited callee — and the gold patch resolves (G-RESOLVE). Trust points are
exactly the two of plan §1.1: deep-model soundness (G-AX) and refinement fidelity
(this doc, G-EQ + G-CONF).
