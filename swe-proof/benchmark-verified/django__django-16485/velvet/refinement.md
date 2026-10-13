# refinement.md — django__django-16485

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `numericDisplay` `do` block) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — A-consumed /
A-reference), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The guard site — `floatformat()` (`django/template/defaultfilters.py:171`)

Gold hunk:
```
-    if not m and p < 0:
+    if not m and p <= 0:
         return mark_safe(
             formats.number_format(
                 "%d" % (int(d)), 0, use_l10n=use_l10n, force_grouping=force_grouping,
             )
         )
```
Net effect: a whole-number value with a requested fractional-digit count of
**zero** now takes the integer-rendering branch instead of falling through to
the fractional-rendering branch (which computes `prec = 0` and raises
`ValueError`). Only the guard changes; both branch bodies are byte-identical.

| # | Solution.lean impl op (`numericDisplay`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `isWhole : Bool` | `not m` (`m = int(d) - d`, line 167) | R | Python bool `int(d) == d` ↔ Lean `Bool` (mapping.md §2). `isWhole` true ⇔ the value is a whole number. |
| A2 | param `p : Int` | `p = int(arg)` (line 162) | R | Python `int` ↔ Lean `Int` (mapping.md §2); identity, sign-preserving. |
| A3 | param `intView : List Char` | the integer-branch return `mark_safe(number_format("%d" % int(d), 0, …))` (lines 172–179) | R | UNCHANGED branch body, taken as a read-only pre-computed input; its `SafeString` content ↔ `List Char` (mapping.md §2). Not an axiom — nothing asserted about its value (LESSONS abstracted-input-not-axiom). |
| A4 | param `fracView : List Char` | the fractional-branch return `mark_safe(number_format(number, abs(p), …))` (lines 199–206, tail from 181) | R | UNCHANGED branch body, read-only pre-computed input; content ↔ `List Char`. Not an axiom. |
| A5 | `if isWhole = true ∧ p ≤ 0 then return intView else return fracView` | `if not m and p <= 0:` dispatch (selecting the integer branch vs the fractional tail) | **I** | the discriminating change is modeled **deeply**: the guard `not m and p <= 0` ⇔ `isWhole = true ∧ p ≤ 0`, the branch selection ⇔ the `if`/fall-through. The `<= 0` (not `< 0`) is the exact behaviour the fix introduces. G-CONF transliterates this concrete selection. |

Discriminating content of the change — the guard admits `p == 0` for whole
values (`p <= 0` not `p < 0`) — lives in `p ≤ 0` (model) ⇔ `p <= 0` (real). The
pre-patch guard used `p < 0`, routing whole values at `p == 0` into the
fractional branch (the crash); `Solution_prepatch.lean` reproduces that with
`p < 0` and **fails** `out = (if isWhole = true ∧ p ≤ 0 then intView else
fracView)` (G-DIFF) at exactly `isWhole = true ∧ p = 0`.

## B. No axioms

There are no axiomatized callees. The two renderings the routine chooses between
(`intView`, `fracView`) are UNCHANGED sub-results of the surrounding code,
modeled as plain read-only inputs (A3/A4, tagged R). Nothing is asserted about
their value, so they cannot mask a wrong impl: the spec forces the branch
SELECTION structure (`isWhole && p ≤ 0`) regardless of what the two renderings
are. There is no callee contract for G-AX to validate, and the one changed op
(the dispatch guard) is the function-under-change's own guard, which directive 7
forbids axiomatizing — it is modeled deeply (I) instead. The bundle therefore
ships no `axiom_check.py`; `gate_ax` returns **skip** (the canonical no-axiom
path). The branch-boundary fidelity and branch-stability facts a witness would
assert are exactly what G-CONF establishes mechanically on the patched tree
(§4 / conformance_check.py, 100019 inputs, 0 disagreements).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the dispatch
guard — is modeled **deeply** (the spelled-out `if isWhole = true ∧ p ≤ 0`,
step A5, an I op), not hidden behind an axiom about the function under change.
The branch bodies are unchanged and abstracted as inputs (R), which is sound
because the patch does not touch them.

## D. verify(Solution) ⇒ resolved

`numericDisplay` verifies only if its output equals
`if isWhole = true ∧ p ≤ 0 then intView else fracView` (A5). By R (the bool/int
bijections and the `SafeString`-content identity, mapping.md §2) the verified
selection equals the patched guard's branch choice on the real
`floatformat` inputs. The F2P test `test_zero_values` adds
`floatformat("0.00", 0) == "0"` and `floatformat(Decimal("0.00"), 0) == "0"`:
both are whole values (`isWhole = true`) with `p = 0`, so the spec forces the
integer rendering (`intView`, which renders `"0"`), exactly what the patch
produces — and the pre-patch fractional branch crashed. The PASS_TO_PASS cases
(`p > 0`, non-whole values, `p < 0` wholes) are all covered identically by both
guards, so the selection is unchanged there.

By G-CONF the R/I transliteration of the selection agrees with the real patched
`floatformat`'s branch choice on ≥10⁵ inputs; by G-RESOLVE the gold patch
resolves. Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement — and the gold patch resolves. The only
trust point is refinement fidelity (this doc, G-EQ + G-CONF); there are no
axioms and no A-references, so G-AX is a skip (no contract to check).
