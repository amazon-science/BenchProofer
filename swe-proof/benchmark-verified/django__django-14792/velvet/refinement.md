# refinement.md — django__django-14792

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `resolveZoneLabel` `do` block) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — A-consumed /
A-reference), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The selection site — `_get_timezone_name()` (`django/utils/timezone.py:74`)

Gold hunk:
```
- return str(timezone)
+ return timezone.tzname(None) or str(timezone)
```

`x or y` in Python evaluates to `x` when `x` is truthy, else `y`. Here `x =
timezone.tzname(None)` (a `str` or `None`) and `y = str(timezone)` (always a
`str`). A `str` is truthy iff non-empty; `None` is falsy. So the result is the
short label when it is present **and** non-empty, otherwise the full label.

| # | Solution.lean impl op (`resolveZoneLabel`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `shortLabel : Option (List Char)` | `timezone.tzname(None)` subexpression | R | `tz.tzname(None)` ↔ `shortLabel` (mapping.md §2): `None ↔ none`, `str s ↔ some s.toList`, `'' ↔ some []`. The `tzinfo` object is presented as its two observable labels (mapping.md §1). |
| A2 | parameter `fullLabel : List Char` | `str(timezone)` subexpression | R | `str(tz)` ↔ `fullLabel` (mapping.md §2), `str ↔ List Char`. |
| A3 | `match shortLabel with \| none => return fullLabel` | the `or` falls through to `str(timezone)` when `tzname(None)` is `None` | R + I | `None` is falsy → `or` yields the right operand; model: `none` branch returns `fullLabel`. |
| A4 | `\| some s => if s ≠ [] then s else fullLabel` | the `or`: yield `tzname(None)` if truthy (non-empty str), else `str(timezone)` | R + I | non-empty `str` is truthy → `or` yields the left operand (`s`); empty `str ''` is falsy → yields the right (`fullLabel`). `s ≠ []` ↔ Python string truthiness (mapping.md §2). |
| A5 | `return out` (`List Char`) | `return ...` (`str`) | R | `str ↔ List Char`; `_get_timezone_name`'s caller compares the rendered text. |

The whole `or`-selection is the changed operation; it is modeled **concretely**
(the `match` + `if`), so every step is R/I — there is no callee whose contract
the proof consumes (mapping.md §3: zero axioms).

Discriminating content of the change — when the short label (`tzname(None)`) is
present, non-empty, and **differs** from the full label (`str()`), the result
must be the short label, not the full one. This lives in clause
`ensures (∀ s, shortLabel = some s → s ≠ [] → out = s)` (model) ⇔ the truthy
branch of `tzname(None) or str(timezone)` (real). The pre-patch returned
`str(timezone)` unconditionally; `Solution_prepatch.lean` reproduces that
(`return fullLabel`) and **fails** that exact clause (G-DIFF) — the goal left
unsolved is `⊢ ∀ s, shortLabel = some s → s ≠ [] → fullLabel = s`.

## B. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the
`x or y` selection between two labels — is modeled **concretely** (the `match`
on `shortLabel` and the emptiness test `s ≠ []`), not hidden behind an axiom.
There are no consumed axioms and no deep-model references; G-AX has nothing to
check (it skips). The two label-producing callees (`tzname`, `str`) are the
observation functions of the input bijection (mapping.md §2), not axioms.

## C. verify(Solution) ⇒ resolved

`resolveZoneLabel` verifies only if its output is the short label whenever that
label is present and non-empty (A4), and the full label when the short is absent
(A3) or empty (A4). By R (`tzname(None) ↔ shortLabel`, `str() ↔ fullLabel`,
Python string truthiness ↔ `s ≠ []`) the verified selection equals
`timezone.tzname(None) or str(timezone)` on the tested `tzinfo` inputs; by G-CONF
the R/I transliteration of the selection agrees with `patch.diff`'s behaviour on
≥10⁵ inputs (the real `tzname`/`str` observations bridged via mapping.md §2).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The sole
trust point is refinement fidelity (this doc, G-EQ + G-CONF); there are no axioms
to trust (G-AX skip).
