# mapping.md — sympy__sympy-12419

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 479939f8c65c8c2908bbedc959549a257a7c0b0b`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge the Lean carrier ↔ the
library objects), and records callee provenance and the pinned fuzz seed.

`spec_provenance: cold` — the spec was derived only from `problem_statement`,
the gold `patch`, and the repo source at `base_commit`.

Repo file under change: `sympy/matrices/expressions/matexpr.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `identityEntry (i j : Idx) (eq : Option Bool) (kd : Option Bool)` | `Identity._entry(self, i, j)` — `sympy/matrices/expressions/matexpr.py:478-484` (post-patch) | the modeled changed function: selects the element value of the diagonal-of-units operator at a symbolic position |
| `Idx` (`pure`) | a symbolic matrix index `i`/`j` (`sympify`'d argument of `_entry`, a `Symbol`/`Expr`/`Integer`) | opaque position carrier; whether two positions coincide is decided by the verdict, not by inspecting the atom |
| `MatEntry` (`pure`) | the fragment of `sympy` value-builders `_entry` returns: `S.One`, `S.Zero`, and an unevaluated `KroneckerDelta(i, j)` | honest symbolic-value carrier (no opaque answer node) |
| `MatEntry.coincide a b` ↔ an UNEVALUATED `KroneckerDelta(a, b)` *(A-reference)* | `sympy.functions.special.tensor_functions.KroneckerDelta` (unchanged callee, imported by the patch) | the symbolic coincidence indicator, denoted only where the indicator's own rules settle neither outcome |
| `eq : Option Bool` ↔ three-valued `Eq(i, j)` verdict *(A-reference input)* | `sympy.core.relational.Eq` then the `is S.true` / `is S.false` test (`matexpr.py:479-483` post-patch) | the three-valued comparison verdict that drives the OUTER branch |
| `kd : Option Bool` ↔ three-valued verdict of `KroneckerDelta(i, j)`'s OWN self-evaluation *(A-reference input)* | `KroneckerDelta.eval` — `sympy/functions/special/tensor_functions.py:136-175` | the indicator's own verdict, which drives the INNER selection once the comparison declines. It is an INDEPENDENT verdict: `KroneckerDelta.eval` applies `diff.is_zero`/`fuzzy_not` (lines 158-162) and the below_fermi/above_fermi rules (lines 164-169), which are strictly broader than `Eq`'s, so it can settle a pair `Eq` leaves unsettled |
| `coincideValue (i j : Idx) (kd : Option Bool)` (`pure`) | the value `KroneckerDelta(i, j)` denotes: `S.One` / `S.Zero` / an unevaluated `KroneckerDelta` | the indicator's own three-way collapse, modeled deeply |
| `entryFor (i j : Idx) (eq : Option Bool) (kd : Option Bool)` (`pure`, deep model — **A-reference**) | the post-patch body of `Identity._entry` (`matexpr.py:478-484`) composed with the value its `KroneckerDelta(i, j)` return denotes | pure spec: the per-verdict element value; its equality to the real `_entry` is validated by `conformance_check.py` (G-CONF) |

The pre-patch repo fact the change overturns (refinement audit only, NOT in the
consumer spec view): pre-patch `_entry` tested `if i == j` — Python structural
(two-valued) equality — and returned `S.One`/`S.Zero`, so an UNDETERMINED
comparison of two distinct symbolic indices fell into the `else` and collapsed to
`S.Zero` (`matexpr.py:478-482` pre-patch). That is the bug: the symbolic entry
`In[i, j]` evaluated to `0`, and a double summation over the square range summed
zeros to `0` instead of recovering `n`.

The unchanged dispatch that makes `_entry` observable is
`MatrixExpr.__getitem__` (`matexpr.py:230-243`): for a 2-tuple key it calls
`self._entry(sympify(i), sympify(j))` when `valid_index(i, j) != False`. For a
symbolic size `n`, `valid_index` (`matexpr.py:223-228`) holds (the bound checks
are undetermined, hence `!= False`), so `In[i, j]` reaches `_entry`. The patch
does **not** touch this dispatch; it only changes the value `_entry` returns.

## 2. Type abstraction (R-refinements) — the Lean↔library bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean carrier and the library objects.

| repo reality | Lean carrier | bijection |
|---|---|---|
| three-valued result of `Eq(i, j)` evaluated by `is S.true` / `is S.false` | `eq : Option Bool` | `S.true ↔ some true`, `S.false ↔ some false`, an unevaluated `Eq(...)` (neither) `↔ none`. Total, exact. (`Eq` is the unchanged comparison primitive.) |
| a symbolic index operand `i`/`j` (`Symbol`/`Expr`/`Integer`) | `Idx` | opaque atom; only its identity is observed (it appears inside the coincidence indicator). G-CONF binds it to a real index. |
| `S.One` | `MatEntry.unit` | the multiplicative unit |
| `S.Zero` | `MatEntry.null` | the additive zero |
| an UNEVALUATED `KroneckerDelta(i, j)` | `MatEntry.coincide i j` | the symbolic coincidence indicator (a single constructor over the two operands), used ONLY where the indicator itself declines to collapse |
| the three-valued value of `KroneckerDelta(i, j)` (`S.One` / `S.Zero` / unevaluated) | `kd : Option Bool` (`some true` / `some false` / `none`) | the indicator's OWN verdict. Total, exact. Checked by `kdval` in G-AX/G-CONF |

`MatEntry` is a finite value inductive because the modeled operation is
*symbolic-value selection*; each constructor maps 1:1 to a library value-builder.
The operands `i, j` are abstract, so the result on the doubly-unsettled case is
*parameterised by the actual operands* (the §0.8 grounding: the postcondition is
dischargeable only by emitting the coincidence indicator over `i, j`, not by
echoing an opaque constant).

Note that `MatEntry.coincide i j` corresponds to an UNEVALUATED indicator, which
is why the second verdict `kd` is needed to say WHEN that carrier value is the
right one: the same library call `KroneckerDelta(i, j)` denotes `S.One`, `S.Zero`,
or the unevaluated node depending on its own rules, and only the last of those
three is `MatEntry.coincide i j`.

## 3. Callee provenance

### 3.1 `entryFor` deep model ↔ `Identity._entry` value (A-reference)
The changed operation — selecting the element value from the comparison verdict,
deferring to the coincidence indicator when that verdict does not settle the pair
— is modeled **deeply** by `entryFor`/`coincideValue` in the `pure` region; there
is **no consumed axiom**. The two value-builders it composes are **unchanged** by
the patch:

- `KroneckerDelta(i, j)` (`sympy/functions/special/tensor_functions.py`) — the
  symbolic coincidence indicator. The patch only newly *imports* and *returns*
  it; the function itself is unchanged. Its semantics: `KroneckerDelta(p, q)`
  evaluates to `1` when it can settle the pair as coincident, to `0` when it can
  settle it as distinct, and stays an unevaluated `KroneckerDelta` (a nonzero
  symbolic object that a summation can reduce) only when its own rules settle
  neither.

  IMPORTANT, and the reason the model carries a SECOND verdict input: the
  indicator's rules are strictly BROADER than `Eq`'s, so its verdict is NOT a
  function of the comparison's. `KroneckerDelta.eval`
  (`tensor_functions.py:136-175`) first tests `diff.is_zero` /
  `fuzzy_not(diff.is_zero)` (lines 158-162) and then the below_fermi/above_fermi
  assumption rules (lines 164-169). Hence there are pairs for which `Eq(p, q)` is
  unevaluated (verdict `none`) yet `KroneckerDelta(p, q)` is `S.Zero` — witness
  `p = Symbol('p', below_fermi=True)`, `q = Symbol('q', above_fermi=True)`, for
  which the real post-patch `Identity(n)._entry(p, q)` is `0` (measured
  in-container at `base_commit` with the gold patch applied). A model predicting a
  nonzero symbolic value on every `none` comparison would be UNFAITHFUL on that
  class. The model therefore defers a `none` comparison to the indicator's own
  three-valued verdict (`coincideValue`) instead of assuming the indicator
  declines as well.
- `Eq` (`sympy/core/relational.py`) — the symbolic-equality constructor whose
  `is S.true` / `is S.false` test yields the three-valued verdict. Unchanged.

G-CONF (`conformance_check.py`) validates that the deep model `entryFor`,
transliterated through the §2 bijection, equals the real library value
`Identity(n)[i, j]` (post-patch) under the library's structural equality — the
end-to-end A-reference check. Axiomatising `_entry` itself is forbidden (§0.7,
it is the function under change).

### 3.2 Component-callee soundness (G-AX, `axiom_check.py`)
`axiom_check.py` validates the two unchanged A-reference callees (and both of the
three-valued bridges the model reads them through) in isolation
against real sympy (no double-masking — each is checked at the level the model
claims it):

- the three-valued verdict: for fuzzed index pairs, `Eq(a, b)` lands in exactly
  one of `{S.true, S.false, unevaluated}` and the `threeval` bridge is total and
  exact (matches the `is S.true`/`is S.false` test the patch performs);
- the coincidence indicator's OWN verdict: the `kdval` bridge over real
  `KroneckerDelta(a, b)` is total and exact (`S.One` → `some true`, `S.Zero` →
  `some false`, unevaluated → `none`), and where that verdict is `none` the value
  is an unevaluated `KroneckerDelta` that is **not** `S.Zero` — i.e. exactly the
  doubly-unsettled value the spec pins (`entryFor_unsettled_ne_null`). G-AX also
  witnesses the POPULATED cross-class (`Eq` unsettled, indicator settles distinct)
  so the broader-rules fact above is measured, not assumed.

Imports only sympy (ships in the testbed). Exit 0 iff every obligation holds.

## 4. Fuzz seed (G-CONF / G-AX)

`conformance_check.py` and `axiom_check.py` pin **`SEED = 12419`**, and G-CONF
runs `N_FUZZ = 100_000` index-pair configurations so the verdict is
reproducible (plan §4.1, §11.3). The R/I shadow transliterates
`entryFor`/`coincideValue` (`unit`/`null`/`coincide` ↔ `S.One`/`S.Zero`/an
unevaluated `KroneckerDelta`) and reads BOTH verdicts from the real unchanged
callees (A-tagged → run real callee): `Eq(a, b)` through `threeval` and
`KroneckerDelta(a, b)` through `kdval`. Oracle = the real patched
`Identity(n)[a, b]`. The fuzz pool includes below_fermi/above_fermi symbols so the
populated `eq = none, kd = some false` class is exercised rather than assumed
empty.

## 5. F2P discriminator

`FAIL_TO_PASS = ["test_Identity"]` (the new asserts: `In[i, j] != 0`;
`Sum(In[i, j], (i, 0, n-1), (j, 0, n-1)).subs(n, 3).doit() == 3`; and the nested
form). At base, `In[i, j]` evaluates to `0` for distinct symbolic `i, j`, so
`In[i, j] != 0` is **False** (assert fails) and the double sum is `0`. Post-patch
the undetermined verdict returns `KroneckerDelta(i, j)` — a nonzero symbolic
object the summation reduces to the count of coincident positions, `n` (→ `3`
under `subs(n, 3)`). The pre-change skeleton models the bug by returning
`MatEntry.null` whenever the comparison is not definitely-equal, which fails
`out = entryFor i j eq kd`, `eq = none → out = coincideValue i j kd` and
`eq = none → kd = none → out ≠ MatEntry.null` (G-DIFF). Confirmed in-container: with the gold
patch applied, the constructor-bijection shadow `== Identity(n)[a,b]` over the
fuzzed pairs (0 disagreements); at base it diverges on every undetermined pair.
A `Piecewise((1, Eq(i,j)), (0, True))` alternative (the hint's first candidate)
is **rejected** by the spec — it does not equal `coincide i j` and, in the real
library, the *nested* double sum does NOT reduce to `n` (it leaves
`Piecewise((3, Eq(i,0)), …) + …`); only the coincidence-indicator form passes the
F2P assert, so the spec pins the discriminating value, not a weaker one.

The spec also rejects the strictly-too-strong neighbour that an earlier revision
of this bundle modeled: returning an ALWAYS-unevaluated indicator on every `none`
comparison, i.e. ignoring the indicator's own verdict. That is unfaithful on the
populated below_fermi/above_fermi class (§3.1), where the real `_entry` returns
`S.Zero`; the battery ships it as `weak-ignores-indicator-verdict` and it is
rejected by the `eq = none → kd = some false → out = MatEntry.null` clause.
