# mapping.md — django__django-11206

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 571ab44e8a8936014c22e7eebe4948d9611fd7ce`, states the type
abstraction (the correspondence G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each callee.

Repo file under change: `django/utils/numberformat.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `formatDecimal (number : DecVal) (decimalPos : Option Nat)` | `format(number, decimal_sep, decimal_pos=None, …)` — `django/utils/numberformat.py:7` (changed region: the `Decimal` branch beginning `django/utils/numberformat.py:29`) | the modeled changed function, restricted to the `isinstance(number, Decimal)` path that the change touches |
| `DecVal` *(carrier — two facets of the input)* | the input object `number : Decimal` itself, observed through exactly the two things the operation reads it by: `Fraction(number)` and the unchanged display tail applied to that very object (see §2) | the carrier |
| `DecVal.amount` | `Fraction(number)` — the exact amount the input denotes; the value the comparison `abs(number) < cutoff` is taken on | carrier facet: the only facet the guard reads |
| `DecVal.render` | `lambda dp: <the unchanged display tail>(number, '.', dp, grouping, thousand_sep, force_grouping)` — the display string **this very object** produces at a requested position count (§3.1) | carrier facet: the display behaviour that travels with the value |
| `renderDecimal (d : DecVal) (dp : Option Nat)` | that facet applied: the unchanged display tail run on whichever value the operation hands it | pure spec: "display this value" |
| `zeroRender` *(opaque — A-reference)* | the same unchanged display tail applied to `Decimal('0')`: `lambda dp: <tail>(Decimal('0'), '.', dp, …)` | opaque free constant; the display behaviour of the one value the normalization produces. Validated `== the real tail on Decimal('0')` by axiom_check.py (G-AX), NOT consumed as a property |
| `plainZero` | the literal `Decimal('0')` on the right of `number = Decimal('0')` (`numberformat.py:36` post-patch) | pure spec: the value the normalization produces — its amount is `0` and its display behaviour is `zeroRender` |
| `clampSmall (d : DecVal) (dp : Option Nat)` *(deep model — the changed op)* | the inserted normalization block `django/utils/numberformat.py:30-36` (post-patch): `cutoff = Decimal('0.' + '1'.rjust(decimal_pos,'0')); if abs(number) < cutoff: number = Decimal('0')` | pure spec: the value-normalization the change adds, INCLUDING which value the normalized case produces and that the other case is the input itself |
| `ratAbs (n : Rat)` | the magnitude `abs(number)` compares on | pure spec: exact magnitude on `Rat` |
| `workingDigits` | `decimal.getcontext().prec` — `28` in the ambient context this code runs under | pure spec: the number of significant digits the environment keeps when it materializes a magnitude |
| `resolution (p : Nat)` | the `cutoff` value `Decimal('0.' + '1'.rjust(decimal_pos,'0'))` (`numberformat.py:33` post-patch) | pure spec: the literal threshold the changed block writes down |
| `guardCutoff (p : Nat)` | no single expression — the threshold the comparison `abs(number) < cutoff` **effectively** applies to the exact magnitude, once `abs()`'s context rounding is accounted for (§2, derivation) | pure spec: the resolution lowered by half a unit in the last significant digit kept |
| `belowResolution (d : DecVal) (dp : Option Nat)` | the guard `decimal_pos is not None and abs(number) < cutoff` (`numberformat.py:31,34` post-patch) | pure spec: the normalization condition |
| `leastExponentMagnitude` | `-decimal.getcontext().Etiny()` = `-(Emin - prec + 1)` = `1000026` in the ambient context this code runs under | pre-condition region: the magnitude of the smallest exponent the environment can place a digit at |
| `positionsInExponentRange (dp : Option Nat)` | no repo expression — the requested-position-count side of the domain of the correspondence (§2), namely that the exponent `guardCutoff dp` needs, `-(max dp 1 + workingDigits)`, is one the environment can represent | pre-condition region: the `require` clause of `formatDecimal` |

The repo symbol `cutoff` (`numberformat.py:33`) and the literal construction
`'1'.rjust(decimal_pos, '0')` are the pre-image of `resolution`; they live only
in the refinement audit, not in the consumer spec view.

## 2. Type abstraction (R-refinements) — the Lean↔Python correspondence

This is the table G-CONF (§4) and G-AX use to translate values between the Lean
value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

**The carrier holds the input's DISPLAY BEHAVIOUR, not a description of the
input.** The operation does two things and only two: it compares the input's
magnitude against a threshold, and it hands a value on to a display step it does
not change. So the input must be carried by (a) its exact amount and (b) what it
displays as — and (b) cannot be reconstructed from any description of the value,
because the display step is `'{:f}'.format(number)`, which dispatches on
`type(number).__format__`. A `Decimal` **subclass** that formats itself
differently is such an input, and one of this instance's own failing rows uses
exactly that shape (`tests/utils_tests/test_numberformat.py::TestNumberFormat::
test_decimal_subclass`, whose `EuroDecimal.__format__` prefixes `'€ '`). A
carrier holding only a description — the amount, or the written triple
`as_tuple()` — therefore identifies inputs the repository distinguishes, and any
implementation that round-trips the input through such a description satisfies a
spec stated over it while changing the real output. `DecVal` carries the display
behaviour as a facet, which makes the pass-through case of `clampSmall` a claim
about the input **itself**.

| repo reality | Lean carrier | correspondence |
|---|---|---|
| `number : Decimal` (or any subclass) — a finite decimal input | `DecVal` (`amount : Rat`, `render : Option Nat → List Char`) | `amount := Fraction(number)`; `render := lambda dp: tail(number, '.', dp, grouping, thousand_sep, force_grouping)` where `tail` is the unchanged display step (§3.1). This is **not** claimed to be a bijection and does not need to be: it is the pair of observables the operation reads, and the spec's obligation is stated entirely in terms of them. What IS claimed, and measured by axiom_check.py, is that the pair is (i) **sufficient** — the real post-change output is a function of exactly these two facets of the input plus `decimal_pos` — and (ii) **necessary in both components** — there are real input pairs agreeing on `amount` (three of them agreeing on `as_tuple()` as well) whose `render` differs, so neither facet can be dropped nor derived from the other. Non-finite inputs (`NaN`/`Infinity`) are outside the modeled path — the branch is entered only for finite `Decimal`s and G-CONF/G-AX restrict to those. |
| the exact amount `number` denotes | `d.amount` | `Fraction(number)` (exact; `Fraction` accepts a `Decimal` losslessly). The normalization DECISION observes `number` only through the **order-only** comparison `abs(number) < cutoff`, which is exact over `Rat` (DECISIONS.md: model order-only float/decimal fixes with `Rat`, never `Float`/`Real`). |
| `decimal_pos : int \| None` | `Option Nat` | `None` ↔ `none`; a non-negative `int p` ↔ `some p`. (The repo only ever passes a non-negative `decimal_pos`; G-CONF fuzzes `{None,0,1,2,3,8}`.) |
| `cutoff = Decimal('0.' + '1'.rjust(p,'0'))` | `resolution p = 1 / 10 ^ (max p 1)` | for `p ≥ 1`, `'0.' + '1'.rjust(p,'0')` is `0.<p-1 zeros>1` = `10^-p`; for `p = 0`, `'1'.rjust(0,'0') = '1'` so `cutoff = Decimal('0.1') = 10^-1`. Hence `cutoff = 10^-max(p,1) = resolution p` exactly (checked in axiom_check.py for `p` in `0..50`). |
| `decimal.getcontext().prec` (28), `ROUND_HALF_EVEN` | `workingDigits = 28` | the ambient arithmetic context. axiom_check.py and conformance_check.py both **assert** `prec == 28`, `rounding == ROUND_HALF_EVEN` and that `Overflow` is trapped before running any probe, so a bundle evaluated under a different context fails loudly instead of silently drifting. |
| `decimal.getcontext().Etiny()` (`= Emin - prec + 1 = -1000026`) | `leastExponentMagnitude = 1000026` (as a magnitude) | the smallest exponent the ambient context can place a digit at: results needing a smaller one are materialized on the coarser subnormal grid instead. Both container probes **assert** `-Etiny() == leastExponentMagnitude` before running, for the same reason as the row above. This is the one context quantity the `guardCutoff` derivation needs beyond `prec`, and it is what the `require` clause of `formatDecimal` is stated in terms of. |
| `abs(number) < cutoff` — the guard as the interpreter executes it | `ratAbs d.amount < guardCutoff p` | **the derivation, which is the whole reason `guardCutoff ≠ resolution`.** `abs()` on a `Decimal` is a **context operation**: it returns the magnitude *materialized at `prec` significant digits with `ROUND_HALF_EVEN`*, and only that materialized value is compared. Write `c = resolution p = 10^-m`, `m = max(p,1)`. Magnitudes in `[c/10, c)` have their 28-significant-digit grid spaced `c·10^-28` apart, so materialization maps every `x ≥ c − c·10^-28/2 = c(1 − 5·10^-29)` **up to `c`**, and at the boundary itself the tie resolves upward because the two candidates are `9.99…9×10^-(m+1)` (last kept digit `9`, odd) and `1.00…0×10^-m` (last kept digit `0`, even). Hence `abs(number) < cutoff` ⟺ `\|n\| < c(1 − 5·10^-29)` = `c − c/(2·10^28)` = `guardCutoff p`, with the comparison STRICT and the boundary magnitude NOT normalized. Comparing the exact magnitude against `resolution p` instead would be a different predicate on the whole half-ulp window `[guardCutoff p, resolution p)` — magnitudes with more significant digits than the ambient precision, which is precisely where the exact and materialized readings part. axiom_check.py checks the equivalence executably: 2670 probes built in exact integer units of `10^-(29+m)` around the threshold (the tuple constructor `Decimal((sign, digits, exponent))` is the only exact way to build them — `scaleb`, `*` and `-` all round to `prec` and would collapse a 29-digit probe onto the threshold it is meant to bracket), on both signs, for `p ∈ {0,1,2,3,8}`. |
| `Decimal('0')` (the normalization's result) | `plainZero = { amount := 0, render := zeroRender }` | amount `0`, display behaviour `zeroRender`. This entry is load-bearing and not a formality: a value denoting zero with any **other** display behaviour — e.g. `Decimal('0E-303')`, which is what `number * 0` yields for the F2P input, and which the unchanged tail routes to its `abs(exponent) + len(digits) > 200` branch — is a **different** `DecVal` and displays differently, so the spec pins this one specifically. |
| the formatted return `str` | `List Char` | the display string of `format`; `renderDecimal`'s codomain. G-CONF compares the displayed strings character-for-character. |

**Domain of the correspondence.** The `render` facet is only defined where the
real tail runs, and the guard's equivalence above is only claimed where the
ambient context can materialize both the magnitude and the threshold. Three
exclusions, all measured rather than assumed:

* non-finite inputs (`NaN`, `sNaN`, `±Infinity`) never reach the modeled branch;
* magnitudes above the context's `Emax` (999999), for which `abs(number)` raises
  a trapped `decimal.Overflow` rather than returning a value. axiom_check.py
  probes the boundary from both sides (building the probes with the exact tuple
  constructor, since `Decimal(9).scaleb(Emax + 1)` itself signals) and records
  where it lies; G-CONF skips draws outside the domain and reports the count.
* **requested position counts whose threshold the context cannot place**, which
  is the one exclusion the spec view carries as an obligation rather than a
  convention: the `require positionsInExponentRange decimalPos` clause of
  `formatDecimal`, i.e. `max p 1 + workingDigits ≤ leastExponentMagnitude`, so
  `p ≤ 999998`.

  *Why it is needed.* The `guardCutoff` derivation above places the effective
  threshold half a unit in the 28th significant digit below `10^-m`, i.e. at the
  exponent `-(m + 28)`. That grid exists only while `m + 28 ≤ -Etiny = 1000026`.
  Past it the spacing available below `10^-m` is the coarser subnormal one, every
  magnitude in the half-ulp window materializes **up onto** `cutoff` instead of
  onto the grid point below it, and the equivalence fails in *both* directions —
  which is why this is a restriction of the domain and not a slackening of the
  threshold. Just past the bound the model normalizes what the repository keeps
  (`p = 999999`, magnitude `(10^29 − 6)·10^-1000028`: modeled `True`, real
  `False`). Far past it the direction reverses: the literal `cutoff` is built
  from a string and so is exact at any exponent, while `abs(number)` is a context
  operation and collapses to `0`, so the repository normalizes an input the model
  keeps (`p = 1000027`, `Decimal('1E-1000027')`: modeled `False`, real `True`).
  Those are exactly the two witnesses this bound answers.

  *Why it bounds only `decimalPos`.* The restriction is on the requested position
  count alone — there is **no** bound on the input. For any admitted `p` the
  window sits at an exponent `≥ Etiny`, so an input magnitude at or below `Etiny`
  is simply far below the window and both readings agree on it.
  `check_input_magnitude_unbounded` measures that on 150 subnormal /
  below-`Etiny` magnitudes (including `10^29 − 5` units at `Etiny`, `Etiny − 1`,
  `Etiny − 40` and `Emin`, both signs) across admitted position counts
  `{0, 1, 3, 8, 999998}`: 0 disagreements.

  *Where the boundary is measured.* `check_position_range_boundary` in
  axiom_check.py asserts the clause admits `999998` and rejects `999999`, then
  checks the modeled and real guards agree on threshold-straddling probes at
  `p ∈ {999996, 999997, 999998}` (27 probes, 0 disagreements — non-vacuously: the
  families bracket `guardCutoff p`, so both sides return a mix of verdicts) and
  that they disagree at `p ∈ {999999, 1000027}` (3 and 6 probes respectively).
  G-CONF additionally draws the largest admitted count `p = 999998`
  end-to-end — including a `Decimal` subclass and magnitudes straddling
  `guardCutoff 999998` — so the bound is exercised from inside by the
  differential check too, and rejects out-of-range counts in `in_scope`.

  Note the asymmetry with the `Emax` exclusion: an out-of-range `decimal_pos`
  does not raise, so nothing in the environment marks it. That is why it is
  stated as a `require` in the spec view instead of being left to a convention
  about which calls occur. What it costs the consumer is bounded and checkable:
  at `base_commit` the only in-repo call site that reaches this branch with a
  non-`None` position count is `django/contrib/admin/utils.py:394`
  (`formats.number_format(value, field.decimal_places)` for a `DecimalField`) —
  `defaultfilters.floatformat` passes a **string**, not a `Decimal`
  (`defaultfilters.py:162-163`), so it takes the `str` path — and the clause
  admits every position count up to 999998. The clause also constrains only
  `decimalPos`, never the input, so it cannot be discharged by knowing anything
  about the value under formatting.

The normalization's only observable is **which value reaches the display step** —
the plain zero value when below the threshold, the input itself (display
behaviour included) otherwise. The display step is unchanged, so the change's
entire observable effect is captured by `clampSmall`.

**What the correspondence deliberately does NOT pin, and why that is faithful.**
The postcondition applies the `render` facet of the value `clampSmall` selects;
it never reads that value's `amount`. So the `amount` component of the
*normalized* value is unobservable — an implementation writing
`{ amount := 1, render := zeroRender }` in place of `plainZero` satisfies the
spec, and G-MUT reports exactly that mutant as a survivor. This is not a gap in
the correspondence, for two independent reasons. (i) It is unobservable in the
repository too: the output is the string the display step returns, the display
step is applied to an *object*, and once which object it receives is fixed the
string is fixed — the amount is not a further degree of freedom the real code
reads. (ii) The perturbation is not realizable: in Python the two facets are
facets of one object, so there is no `Decimal` whose amount is `1` and which
displays the way `Decimal('0')` does. The pair `(amount, render)` is the *image*
of an object under two observations, not an independently-inhabited product, and
a Lean value outside that image has no counterpart to refine to. What the spec
must pin — and does — is which of the two realizable values the display step
receives; that is precisely `clampSmall`, and the two uniqueness rivals that
mis-select it (`reject-value-rebuilt-not-input` on the pass-through branch,
`reject-zero-loses-plain-form` on the normalized one) are both refused.

## 3. Callee provenance

### 3.1 `render` / `zeroRender` ↔ the unchanged `format` tail (A-reference)
**Callee:** the part of `django.utils.numberformat.format` that the change does
**not** touch — everything from the `# Format values with more than 200 digits`
comment (`numberformat.py:29`, post-change line offset +8) through the final
`return sign + int_part + dec_part`. The changed function delegates to it
unchanged after the normalization.

It is modeled as a **facet of the carried value** rather than as a free function
of a description of the value, and the one display behaviour the operation
introduces itself — that of `Decimal('0')` — is the `opaque` free constant
`zeroRender`. The proof consumes **no property** of either: `render` appears
identically on both sides of the postcondition `out = renderDecimal (clampSmall
…) …`, so the spec pins only *which value* is displayed. This is an
**A-reference**, not a consumed axiom. G-AX validates it by reconstructing the
pre-change tail in-container (strip the normalization block from the installed
patched source) and checking

```
patched_format(number, dp) == renderDecimal(clampSmall(carrier(number), dp), dp)
```

on boundary + fuzz inputs, where `carrier(number) = DecVal(Fraction(number),
lambda dp: tail(number, dp))` and `plain_zero = carrier(Decimal('0'))`.

**Realizability of the facet type `Option Nat → List Char`.** A facet of this
type can stand for the unchanged tail only if that tail really is a function of
the input object and the requested position count alone. It is: the tail reads
`number` via `number.as_tuple()` (the `abs(exponent) + len(digits) > 200` test)
and via `'{:f}'.format(number)`, and both are determined by the object. Note this
is *weaker* than requiring the tail to be a function of `as_tuple()`, and that
gap is the repair: `'{:f}'.format` dispatches on the object's TYPE, so two
objects with equal `as_tuple()` can display differently. axiom_check.py measures
exactly this — it exhibits pairs with equal `amount` whose displayed strings
differ, three of them with equal `as_tuple()` as well, which is what rules out
every description-only carrier. (The other `format` arguments — `decimal_sep`,
`grouping`, `thousand_sep`, `force_grouping`, `use_l10n` — are constant across
the twin and are held fixed by both probes; they are parameters of the *display
step*, not observables of the changed op, and the postcondition quantifies over
neither.)

There is **no consumed axiom**: the only property the proof uses is the
definitional equality `clampSmall d dp = (if belowResolution d dp then plainZero
else d)`, which is the deeply-modeled changed op itself, not an external
contract.

### 3.2 Why the display step is not re-derived
Its behaviour (scientific-notation cutoff for >200-digit values, `'{:f}'`
expansion, decimal split/pad, digit grouping, sign) is **unchanged** by this
issue and is exercised identically pre- and post-change. Re-deriving it would be
modeling an unchanged operation; per SPEC_GUIDE §3 it is abstracted, and its
equivalence across the twin is the A-reference G-AX checks. The single behaviour
the F2P rows observe — a sub-threshold `Decimal` displaying as `0.000…` instead
of in scientific notation, and a `Decimal` **subclass** keeping its own display
when it is not normalized — is produced entirely by handing the otherwise
unchanged step either the **plain zero value** or **the input itself**, which is
why §2 pins the display behaviour of both and not merely the amounts.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11206`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`clampSmall`/`belowResolution`/`guardCutoff`/`resolution` (the R/I-tagged changed
op) to Python — taking the decision from the `amount` facet alone, as an exact
`Fraction` comparison and never a `Decimal` operation — and leaves the A-tagged
`render`/`zeroRender` facets as the **real unchanged repo display step**,
reconstructed in-container by stripping the normalization block from the
installed (patched) `format`. So the shadow is exactly "select which value the
unchanged step receives, then run it": either the input object itself or
`Decimal('0')`. It diffs that shadow against the patched `format` (the oracle)
over ≥10⁵ fuzzed `(number, decimal_pos, grouping, thousand_sep,
force_grouping)` tuples, whose `number` draws include `Decimal` **subclass**
instances and magnitudes with more significant digits than the ambient precision
placed at the materialization boundary — the two families on which a shadow that
rebuilt the value it passes on, or that compared the exact magnitude against
`resolution p`, would disagree here.
