# refinement.md — sympy__sympy-21612

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `bracketDenomFactors` `do` block, the deep `renderDenomFactors` model, and
the `DenomFactor` observations) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement; state the bijection), **A-reference** (a deep
model / observation validated == the real callee by G-AX), or **I** (identical
concrete op). EVERY step is R, A, or I; no kind-3 (changed inexpressible op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference legs and this narrative are audited by **G-EQ** and
**G-AX**. Claim: any impl verifying against this frozen spec, refined per the
map below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The bracketing site — `StrPrinter._print_Mul` (`sympy/printing/str.py:249`)

Gold hunk (the one edited line, `str.py:335-336`):
```
- if (len(item.args[0].args) != 1 and isinstance(item.base, Mul)):
+ if (len(item.args[0].args) != 1 and isinstance(item.base, (Mul, Pow))):
```
This is the gate that decides whether a reciprocal denominator factor
`item = Pow(base, -1)` is added to `pow_paren` — i.e. whether it RAISES a
protective-bracket request. The patch widens the inner-shape condition from "is a
product" (`Mul`) to "is a product OR a power" (`(Mul, Pow)`).

The gate is only half of the site. The request is SATISFIED later, at
`str.py:354-356`:
```python
for item in pow_paren:
    if item.base in b:
        b_str[b.index(item.base)] = "(%s)" % b_str[b.index(item.base)]
```
`b.index` is a first-occurrence VALUE lookup, and the loop re-reads `b_str` each
iteration, so a request is applied at the position its inner expression is FOUND
at and applications accumulate. The modeled function is therefore the whole
`b`→`b_str` step, not a per-slot predicate; see mapping.md §0.

| # | Solution.lean impl op (`bracketDenomFactors`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `slots : List DenomFactor` | the denominator list `b`, in order — ALL of it: the `item.base` entries (`str.py:342`), the `apow(item)` entries (344) and the `Rational(item.q)` entries (349) | R | each entry of `b` ↔ one `DenomFactor`; list order preserved (mapping.md §2). Modelling all of `b`, not only the reciprocal entries, is required because a request's `b.index` lookup ranges over the whole list and non-reciprocal slots occupy positions in it. |
| A2 | `DenomFactor.rendered` | `self.parenthesize(b[k], prec, strict=False)` = `b_str[k]` before any request (`str.py:351`) | R + A-reference | the slot value's standard rendered text; an UNCHANGED sub-render callee, taken as a given observed value. G-CONF leaves it as the REAL `self.parenthesize`; G-AX reads it from the real object and (on unchanged-behaviour inputs) checks the deep model reproduces the real loaded string. |
| A3 | `DenomFactor.shape` ∈ {product, power, simple} | `type(b[k])`: `Mul` / `Pow` / other | R + A-reference | faithful 3-way classification of the inner top-level type; `Mul`/`Pow` are disjoint (mapping.md §2). Observed from the real object; G-AX validates `item.base is item.args[0]` and the shape/components readings. |
| A4 | `DenomFactor.components` | `len(b[k].args)`; for a reciprocal slot this is `len(item.args[0].args)`, the quantity read at `str.py:335` | R | top-level component count of the inner expression (mapping.md §2). |
| A5 | `DenomFactor.isReciprocal` | whether the slot was pushed from the `item.exp is S.NegativeOne` branch (`str.py:342`) rather than from `apow(item)` (344) or `Rational(item.q)` (349) | R + A-reference | only slots from that branch are ever appended to `pow_paren`, so only they can raise a request. This models the BRANCH the changed gate sits inside — unchanged by the patch. |
| A6 | `DenomFactor.innerKey`, with `innerKey i = innerKey j` ⟺ the slot values are `==` | the `==`-equality that `item.base in b` and `b.index(item.base)` use (`str.py:355`) | R + A-reference | `list.index` / `in` compare with `==`, so the lookup depends on the slot values only through their `==`-equivalence classes; `innerKey` is a faithful code for those classes. G-AX asserts the correspondence pairwise over every pair of real slots. |
| A7 | `needsBrackets f = f.isReciprocal && (f.components != 1) && shapeIsCompound f.shape` | the patched gate `len(item.args[0].args) != 1 and isinstance(item.base, (Mul, Pow))`, inside the `item.exp is S.NegativeOne` branch | I (the modeled change) | `components != 1` ⇔ `len(...args) != 1`; `shapeIsCompound shape` (`product ∨ power`) ⇔ `isinstance(item.base, (Mul, Pow))`; `isReciprocal` ⇔ the enclosing branch. This conjunction IS the changed line plus its context. The `power` disjunct is the patch's widening. G-CONF checks the full assembled string. |
| A8 | `firstSlotWithKey f.innerKey all` | `b.index(item.base)` — first-occurrence value lookup; `slots.length` (past the end) ⟺ `item.base not in b`, where the real guard skips the request and `wrapAt` past the end is a no-op | I | UNCHANGED by the patch, and the reason equal-inner slots co-target. Grounded in the real base-commit function by G-AX (obligation 2 over duplicate-inner quotients). |
| A9 | `bracketTargets all slots` | `[b.index(item.base) for item in pow_paren]`, in slot order (`pow_paren` is appended to during the `args` loop) | I | one request per raising slot, resolved to positions; order-preserving. |
| A10 | `applyWraps` / `wrapAt` / `wrapText` — `renderDenomFactors slots = applyWraps (slotTexts slots) (bracketTargets slots slots)` | the `for item in pow_paren:` loop at `str.py:354-356` mutating `b_str` in place | I | the requests are satisfied one after another against the text produced so far, so two requests naming the same position wrap that text twice: `"(%s)"` ↔ `"(".toList ++ … ++ ")".toList`, in-place mutation of `b_str[i]` ↔ `wrapAt … i`, the loop ↔ the left fold. |
| A11 | the `while` fold over `targets` building `result = applyWraps texts (targets.take k)` | the `for item in pow_paren` loop itself | I | concrete, transliterated by G-CONF (the proven forward-fold pattern, plan §5.4); `applyWraps_take_step` is the loop's single body obligation. |

Discriminating content of the change — a reciprocal whose inner expression is a
**power** with ≠1 component (e.g. `Pow(y,-1)`, rendering `1/y`) now raises a
request, so `q/(1/y)` not the wrong `q/1/y` — lives in `shapeIsCompound
DenomShape.power = true` (model) ⇔ `isinstance(item.base, Pow)` (real). The
pre-patch gate admitted only `product` inners; `Solution_prepatch.lean` reproduces
that (its request list filters on `f.shape == DenomShape.product`) and **fails**
`out = renderDenomFactors slots` on a `power`-shaped slot (G-DIFF).

## B. Modeled altitude — the main arm of `_print_Mul`

`_print_Mul` has TWO arms (`str.py:258`). The FIRST arm handles special
unevaluated forms (a leading `One`, any `Number` in `args[1:]`, or an
integer-base/integer-exp `Pow` factor) and is **not touched by the patch**. The
edited gate lives only in the MAIN (second) arm, which is where the F2P input
`Mul(x, Pow(1/y,-1))` and the preserved #14160 case both route.
`bracketDenomFactors` models the main arm's whole `b`→`b_str` denominator-slot
rendering; `conformance_check.py` and `axiom_check.py` therefore restrict to
main-arm inputs (the first arm is common to both legs, unchanged, and out of the
modeled altitude; G-CONF logs the skip).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
the request gate's inner-shape test — is modeled **directly** (`needsBrackets`
over the `DenomShape` classification, step A7), not hidden behind an opaque axiom
about the function under change: there is **no consumed axiom**. `DenomFactor` is
a `structure` of observations (A-reference, G-AX-validated against the real
loaded `_print_Mul`), not a load-bearing contract — the proof of
`bracketDenomFactors` is purely structural over whatever `DenomFactor` values it
receives.

The request-RESOLUTION rule (A8–A10) is likewise modeled directly rather than
abstracted away. It is unchanged by the patch, but it is not separable from the
change: the gate's decision is only observable through it, and it is what makes
the produced text depend on the OTHER slots rather than on the raising slot alone.
A model that satisfied each request at its own slot would be internally
consistent and would agree with the real function on every input whose
denominator slots hold distinct inner expressions — and would diverge on the
equal-inner class, e.g. predicting `x/(((y*z))*((y*z)))` where the real patched
printer produces `x/((((y*z)))*(y*z))`. That divergence is not hypothetical; it is
why the resolution rule is spelled out here and why both G-CONF and G-AX are
constructed to be able to see it (mapping.md §3.1, §4).

## D. verify(Solution) ⇒ resolved

`bracketDenomFactors` verifies only if its output equals the exact denominator
rendering `renderDenomFactors slots` — which raises a request for a
`power`-shaped reciprocal slot with ≠1 component (A7) and satisfies every request
at the position its inner expression is found at, cumulatively (A8–A10). By R
(entry of `b` ↔ `DenomFactor`, `str`↔`List Char`, `type`↔`shape`,
`len(args)`↔`components`, the `exp==-1` branch ↔ `isReciprocal`, the `==`-classes
of slot values ↔ `innerKey`) the verified rendering equals the patched function's
`b_str` on the modeled main-arm inputs.

By G-AX the observation pipeline is sound (`item.base is item.args[0]`,
shape/components/rendered/isReciprocal read from the real slot, and `innerKey`
equality checked pairwise against real `==`), and the modeled
`renderDenomFactors`, assembled through `_print_Mul`'s unchanged scaffold, equals
the string the REAL loaded base-commit `_print_Mul` produces on every generated
quotient the patch does not re-bracket — including quotients whose slots hold
EQUAL inner expressions, which is what grounds the unchanged resolution rule in
the real function (the patch does not touch `str.py:354-356`, so base is
authoritative there). Both trigger and resolution are shown non-vacuous.

By G-CONF the R/I transliteration of the whole pure surface, embedded in
`_print_Mul`'s unchanged scaffold and NOT reusing the real `pow_paren` / `b.index`
block, agrees with `patch.diff`'s actual PATCHED `_print_Mul` on ≥10⁵ inputs
drawn from a family heavy on duplicate inner expressions and non-reciprocal slots
(this is where the modeled *changed* gate is validated against the patched
function — G-AX may not, per SPEC_GUIDE §0.7, since it runs unpatched).

Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and audited observations — on the equal-inner class as
well as on the distinct-inner one — and the gold patch resolves the F2P `test_Mul`
(`str(Mul(x, Pow(1/y,-1))) == 'x/(1/y)'`) while preserving the PASS_TO_PASS cases
incl. #14160 (G-RESOLVE). Trust points are exactly the two of plan §1.1:
observation soundness (G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
