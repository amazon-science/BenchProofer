# refinement.md — django__django-11206

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`formatDecimal` `do` block, the deep
`clampSmall`/`belowResolution`/`guardCutoff`/`resolution` model over the `DecVal`
carrier, and the two display facets `render`/`zeroRender`) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (abstracted
callee — **A-consumed** where the proof uses the axiom's `ensures`,
**A-reference** where a deep/opaque model is validated == the real callee by
G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
A legs and this narrative are audited by **G-EQ**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The normalization site — `format()` Decimal branch (`django/utils/numberformat.py:29-36`)

Gold hunk (inserted at the top of the `isinstance(number, Decimal)` branch):
```
+        if decimal_pos is not None:
+            cutoff = Decimal('0.' + '1'.rjust(decimal_pos, '0'))
+            if abs(number) < cutoff:
+                number = Decimal('0')
```

| # | Solution.lean impl op (`formatDecimal`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `number : DecVal` (`amount : Rat`, `render : Option Nat → List Char`) | `number` (a `Decimal`, or any subclass) on the `isinstance(number, Decimal)` path | R | the input is carried by the **two facets the changed operation reads it through**: `amount := Fraction(number)` (the exact amount, which the comparison is taken on) and `render := lambda dp: tail(number, '.', dp, …)` (what **this very object** displays as under the unchanged tail). Not claimed to be a bijection and it does not need to be — what is claimed, and measured by axiom_check.py, is that the pair is *sufficient* (the post-change output is a function of these two facets plus `decimal_pos`) and *necessary in both components* (real input pairs agree on `amount`, three of them on `as_tuple()` too, yet display differently). §A0 is the reason the second facet cannot be replaced by any description of the input. mapping.md §2. |
| A2 | parameter `decimalPos : Option Nat`, restricted by `require positionsInExponentRange decimalPos` | `decimal_pos` (`int \| None`) | R | `None` ↔ `none`, non-negative `int p` ↔ `some p` (mapping.md §2). The `require` clause is the requested-position-count half of the **domain of the correspondence**: `max p 1 + workingDigits ≤ leastExponentMagnitude` (`p ≤ 999998`, where `leastExponentMagnitude = -getcontext().Etiny() = 1000026`). It is a bound on the *position count only* — never on the input — and §A0(iii) is the measurement that says why the R-legs A3/A4 need it and that it is exactly tight. |
| A3 | `belowResolution number decimalPos` (`none ⇒ false`; `some p ⇒ ratAbs number.amount < guardCutoff p`) | `decimal_pos is not None and abs(number) < cutoff` | R + I | the normalization guard. `decimal_pos is not None` ↔ the `match dp` arm. `abs(number) < cutoff` ↔ `ratAbs number.amount < guardCutoff p`: the decision reads the input **only** through the `amount` facet — an order-only comparison, hence exact over `Rat` (DECISIONS.md) — but the threshold it effectively applies is *not* `resolution p`. `abs()` is a **context operation**: it materializes the magnitude at `prec = 28` significant digits under `ROUND_HALF_EVEN` and compares only that, so every magnitude at or above `resolution p − resolution p / (2·10^28)` is lifted onto `cutoff` and fails the strict `<`. `guardCutoff p` is exactly that lowered threshold; the tie at the boundary resolves upward because the two 28-digit candidates are `9.99…9` (last kept digit odd) and `1.00…0` (even). Derivation and the 2670 executable boundary probes: mapping.md §2. The lowered threshold lives at exponent `-(max p 1 + workingDigits)`, which is what A2's `require` clause keeps representable (§A0(iii)). Concrete comparison ops are **I**; the type bridge is **R**. |
| A4 | `if belowResolution … then num := { amount := 0, render := zeroRender }` (so the value fed onward is `clampSmall number decimalPos`, whose small-case result is `plainZero`) | `if abs(number) < cutoff: number = Decimal('0')` | R + I | the deeply-modeled changed assignment: replace the value by the **plain zero value** — amount `0` *and* the display behaviour of `Decimal('0')` — exactly when the guard holds, and leave it as **the input itself** otherwise. `Decimal('0') ↔ plainZero` (**R**, mapping.md §2); the replace-under-the-guard operation itself is **I**. Both facets of both branches are load-bearing, not incidental — §A0. This is the single op the patch adds. |
| A5 | `return renderDecimal num decimalPos` | the unchanged remainder of `format` displaying the (possibly normalized) `number` | A-reference | the display tail is **unchanged** by the patch. It is modeled as a *facet of the carried value* (`renderDecimal d dp = d.render dp`), with the one display behaviour the change introduces itself — that of `Decimal('0')` — as the `opaque` free constant `zeroRender`. `render` appears identically on both sides of the postcondition, so the spec pins only *which value* is displayed and consumes **no property** of the tail (mapping.md §3.1). G-AX validates the A-reference by reconstructing the pre-patch tail in-container and checking `patched_format(number, dp) == renderDecimal (clampSmall (carrier number) dp) dp` with `carrier n = DecVal(Fraction(n), lambda dp: tail(n, dp))` and `plainZero = carrier(Decimal('0'))`. |

### A0. Why the carrier holds display BEHAVIOUR, and why the threshold is lowered (the R-legs A3 and A4 rest on)

Two things about the real code are observable in the output and are what the
model has to reach. Both are measured, not asserted.

**(i) The display tail dispatches on the input's TYPE, so no description of the
value is enough.** The unchanged tail reads `number` twice: `number.as_tuple()`
(for the `abs(exponent) + len(digits) > 200` branch) and `'{:f}'.format(number)`,
which goes through `type(number).__format__`. A `Decimal` **subclass** that
formats itself differently therefore displays differently from the plain
`Decimal` of the same amount *and the same `as_tuple()`*. This instance's own
suite contains exactly such an input:
`tests/utils_tests/test_numberformat.py::TestNumberFormat::test_decimal_subclass`
builds a `EuroDecimal` whose `__format__` prefixes `'€ '` and asserts
`nformat(price, ',') == '€ 1,23'`.

Consequences:

* a carrier holding only a *description* of the input — the amount, or the
  written triple `as_tuple()` — identifies inputs the repository distinguishes.
  Over such a carrier the A5 A-reference is not even well-typed as a function of
  the input, and worse, an implementation that **round-trips the input through
  its own description** before handing it on is provably the identity by
  structure eta, so a spec stated over that carrier *admits* it. Its faithful
  real counterpart, `number = Decimal(number.as_tuple())` inserted ahead of the
  gold block, keeps every amount and destroys the subclass. Measured under the
  resolve harness: **resolved=False, FAIL_TO_PASS 1/2, PASS_TO_PASS 4/4** — the
  row the change targets now passes and `test_decimal_subclass` fails with
  `AssertionError: '1,23' != '€ 1,23'`. That is a
  verify-does-not-imply-resolve break, and it is *unreachable* by any rival on a
  description-only carrier, because the rival's argument and the spec's are the
  same point there. It is also the sharpest break available on this instance:
  it breaks a row the gold patch leaves untouched, so it shows up with the
  targeted row green (see §B).
* **the result of A4 is equally load-bearing.** `Decimal('0')` and
  `Decimal('0E-303')` both denote zero and display as `'0.000'` and
  `'0.000e-303'` at three requested positions, because the second stays on the
  `>200`-digit branch. So "replace the value by something denoting zero" is
  strictly weaker than the gold op. Measured: normalizing by `number = number * 0`
  (decimal multiplication keeps the sign and adds the exponents, so the zero is
  written at the input's own place) **fails** `test_decimal_numbers` on the very
  row the change targets — `'0.000000…0001234'` at `decimal_pos=3` must display
  `'0.000'` and gets `'0.000e-303'`. Measured under the resolve harness:
  **resolved=False, FAIL_TO_PASS 0/2, PASS_TO_PASS 4/4** (see §B for why the
  recorded count is 0/2 rather than 1/2).

`DecVal` carries the display behaviour as a facet, which makes A4's
pass-through branch a claim about the input **itself** and its normalized branch
a claim about the plain zero **specifically**. axiom_check.py measures the
necessity of the facet directly, as equal-amount input pairs whose displayed
strings differ (three of them with equal `as_tuple()` as well), and
properties.py ships the two corresponding uniqueness rivals
(`reject-value-rebuilt-not-input`, `reject-zero-loses-plain-form`) — both
refused by this spec and admitted by a description-only one.

**(ii) The guard compares a materialized magnitude, not the exact one.**
`cutoff` equals `resolution p = 10^-max(p,1)` exactly (mapping.md §2), but
`abs(number) < cutoff` is not `|n| < cutoff` on the exact amount: `abs()` returns
the magnitude rounded to the ambient 28 significant digits first. On the half-ulp
window `[guardCutoff p, resolution p)` the two readings part — exactly the
magnitudes carrying more significant digits than the ambient precision. Modeling
the guard as an exact comparison against `resolution p` would therefore be a
*different* predicate, and `belowResolution` uses `guardCutoff p` for that
reason. The corresponding uniqueness rival is
`reject-threshold-exact-compare`; unlike the two above it costs **zero** suite
failures (measured under the resolve harness with `number.copy_abs() < cutoff`,
the exact-comparison spelling, in place of `abs(number) < cutoff`:
**resolved=True, FAIL_TO_PASS 2/2, PASS_TO_PASS 4/4**), because no suite row
lands in the window. It is shipped
on uniqueness grounds only and `properties.py` says so; the *faithfulness* claim
it protects is the one G-CONF and G-AX exercise, both of which draw inputs
placed on the materialization boundary.

**(iii) That derivation has a domain, and A2's `require` clause is exactly it.**
The lowered threshold of (ii) is half a unit in the 28th significant digit below
`10^-m` (`m = max p 1`), i.e. a value at exponent `-(m + 28)`. The ambient
context can only place a digit down to `Etiny = Emin - prec + 1 = -1000026`, so
the grid the derivation reasons on exists exactly while
`m + 28 ≤ 1000026`, i.e. `p ≤ 999998`. That inequality *is*
`positionsInExponentRange decimalPos`, with
`leastExponentMagnitude = -getcontext().Etiny() = 1000026`.

Past the bound the equivalence fails, and in **both** directions — which is why
this is a restriction of the domain and not a re-tuning of the threshold:

* `p = 999999`, magnitude `(10^29 − 6)·10^-1000028`: the model normalizes
  (`ratAbs amount < guardCutoff p`) and the repository does **not**, because the
  grid point below `cutoff` is no longer available and `abs()` materializes the
  magnitude straight up onto `cutoff`;
* `p = 1000027`, input `Decimal('1E-1000027')`: now the repository normalizes and
  the model does **not** — `cutoff` is built by `Decimal(<str>)` and so is exact
  at any exponent, while `abs(number)` is a context operation and collapses to
  `0`.

Both are measured, in `check_position_range_boundary` (axiom_check.py): the
clause admits `999998` and rejects `999999`; the modeled and real guards agree on
27 threshold-straddling probes at `p ∈ {999996, 999997, 999998}` — non-vacuously,
since each family brackets `guardCutoff p` and both sides return a mix of
verdicts — and disagree on 3 probes at `p = 999999` and 6 at `p = 1000027`.
G-CONF additionally draws the largest admitted count end-to-end.

Two properties of the clause matter for reading it as a domain restriction rather
than a convenient hypothesis:

* **it constrains the position count only, never the input.** No input magnitude
  is excluded, and none needs to be: for an admitted `p` the half-ulp window sits
  at an exponent `≥ Etiny`, so a subnormal or below-`Etiny` input magnitude is
  simply far below the window and both readings agree.
  `check_input_magnitude_unbounded` measures that on 150 such magnitudes across
  admitted counts `{0, 1, 3, 8, 999998}`: 0 disagreements. So the clause is
  discharged by the *caller's* choice of `decimal_pos` alone and carries no
  information about the value being formatted — in particular no implementation
  can consume it to decide anything about `number`;
* **it excludes nothing this instance grades.** Every `decimal_pos` appearing in
  the FAIL_TO_PASS and PASS_TO_PASS rows is in `{None, 0, 1, 2, 3, 8}`
  (`tests/utils_tests/test_numberformat.py`), and the repository's only call site
  that reaches this branch with a non-`None` count passes a `DecimalField`'s
  `decimal_places` (mapping.md §2). So the bound removes no behaviour the
  resolve argument of §D rests on.

A precondition is also the one edit that can buy verification with a premise
rather than earn it, so properties.py fences this clause from all three sides and
each side is a separate G-PBT case, all three measured with real builds:
`admiss-precond-satisfiable` (the clause is available in region, admits `none`,
`some 0`, `some 3` and every count up to `some 999998`, and FAILS at
`some 999999` — so it is neither tightened past the graded rows nor collapsed to
`True`; five negative controls, one per conjunct, all fail),
`pos-domain-restricted` (an implementation correct inside the clause and
deliberately wrong outside it still verifies, which is what "the obligation says
nothing out of range" means operationally — so the clause is a genuine domain
restriction and not a hidden extra premise), and
`reject-invented-domain-bound` (an implementation may NOT draw a tighter cut-off
of its own inside the admitted range: the rival stops normalizing from a
requested count of 3 upward and is refused, and its faithful real patch —
the gold block guarded by `decimal_pos <= 2` — is measured resolved=False,
FAIL_TO_PASS 0/2, PASS_TO_PASS 4/4). The five soundness positives whose proof
script is byte-identical to the frozen one all still verify with the clause in
place, so it costs no correct implementation its proof.

## B. No second change site, and how to read this instance's FAIL_TO_PASS list
The patch is a single additive block in one function. `test_decimal_subclass`
(also listed FAIL_TO_PASS) **passes both pre- and post-patch**: it calls
`nformat(price, ',')` with `decimal_pos=None`, so the inserted block — guarded by
`decimal_pos is not None` — cannot change its behaviour. Measured directly in a
worktree at `base_commit` with the instance's test file applied: pre-patch,
`test_decimal_numbers` fails (`'1.234e-300' != '0.000'`) and
`test_decimal_subclass` passes.

Why it is nevertheless in FAIL_TO_PASS, and why that matters for reading every
`refinement` note in properties.py: `test_decimal_numbers` fails inside a
`subTest`, which emits its diagnostics *without* terminating the runner's
verbose status line, so the next test's status is appended to the same line —

```
test_decimal_numbers (…TestNumberFormat) ... test_decimal_subclass (…TestNumberFormat) ... ok
```

— and the harness's per-test status parse cannot attribute that `ok`. So
whenever `test_decimal_numbers` fails, `test_decimal_subclass` is *recorded* as
failing too. Measured: a semantically no-op patch (pre-patch behaviour) records
FAIL_TO_PASS **0/2**, PASS_TO_PASS 4/4. Consequences used throughout this
bundle: a rival that breaks only the targeted row records 0/2 (not 1/2), and a
recorded 1/2 means something strictly stronger — the targeted row is green and a
row the gold patch never touches has been broken. §A0(i)'s rival is the only one
measured here that does that, which is exactly why it is the load-bearing
uniqueness case.

There is no independently-fixed second behaviour, hence a single
`Solution_prepatch.lean`.

Discriminating content of the change — a `Decimal` whose materialized magnitude
is below `10^-max(decimal_pos,1)` is displayed as `0.000…` rather than passed
through to the scientific-notation path — lives in
`clampSmall number decimalPos = plainZero` (model) ⇔ `number = Decimal('0')`
under the guard (real). The pre-patch `format` never normalizes;
`Solution_prepatch.lean` reproduces that (hands `number` straight to
`renderDecimal`) and **fails**
`out = renderDecimal (clampSmall number decimalPos) decimalPos`
on exactly the below-threshold clause (G-DIFF), leaving the residual goal
`renderDecimal number decimalPos = renderDecimal (if belowResolution number decimalPos = true then { amount := 0, render := zeroRender } else number) decimalPos`.

## C. No kind-3 (inexpressible-changed-op) steps
Every step is R, A, or I. The one operation that genuinely *changed* — the
below-threshold normalization — is modeled **deeply** (the spelled-out
`clampSmall`/`belowResolution`/`guardCutoff`/`resolution`/`plainZero`, steps
A3–A4, R + I), not hidden behind an axiom about the function under change. Note
that its **result** is modeled deeply too (the plain zero value, display
behaviour included, not an existential "some zero"), and that its **guard** is
modeled at the threshold the interpreter actually applies rather than the one the
source writes down; §A0 shows both are required for faithfulness. The only
abstracted callee, the display tail (step A5), is **unchanged** by the patch and
is an A-reference: it is carried as a facet of the value, its zero case is the
`opaque` `zeroRender`, and the proof consumes **no** property of either. There is
no consumed axiom.

## D. verify(Solution) ⇒ resolved
`formatDecimal` verifies only if its returned value is `renderDecimal` applied to
`clampSmall number decimalPos` (A3–A5) — for **every** input and every requested
position count the `require` clause admits, which is every count up to 999998 and
therefore every count this instance's rows use (§A0(iii)): the display step
receives the **plain zero value** exactly when the materialized magnitude is
below the threshold and **the input itself**, display behaviour included,
otherwise. By R
(`Decimal ↔ DecVal` on the two facets the operation reads,
`Decimal('0') ↔ plainZero`, `int|None ↔ Option Nat`, `cutoff = resolution`,
`abs(number) < cutoff ⟺ ratAbs amount < guardCutoff`) this is the gold patch's
`number = Decimal('0') if abs(number) < cutoff else number` feeding the unchanged
tail. By G-AX the facets equal the real unchanged tail over this carrier
(A-reference, together with the sufficiency and both-component necessity
measurements); by G-CONF the R/I transliteration of the normalization composed
with the real pre-patch tail agrees with the patched `format` on ≥10⁵ inputs
whose draws include `Decimal` subclass instances and magnitudes on the
materialization boundary. The two steps an earlier description-only carrier left
unpinned — *whether the pass-through value is the input or a reconstruction of
it*, and *which* value denoting zero reaches the tail — are pinned by A1/A4 and
probed by both container gates and by shipped uniqueness rivals whose faithful
patches are measured not to resolve. So a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement and the audited unchanged
tail — and the gold patch resolves (G-RESOLVE). Trust points are exactly the two
of plan §1.1: A-reference soundness (G-AX) and refinement fidelity (this doc,
G-EQ + G-CONF).
