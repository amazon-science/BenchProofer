# refinement.md — sympy__sympy-19637

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `markerPresent` `do` block plus the pure `markerFlag`) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement; state the
bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(deep model validated == real callee by G-AX), or **I** (identical concrete
op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The marker-presence flag step — `kernS` (`sympy/core/sympify.py:516`)

Gold hunk:
```
-        hit = kern in s
+            hit = kern in s
+        else:
+            hit = False
```
(The added indentation moves `hit = kern in s` from the outer `if '(' in s`
level into the inner `if ' ' in s:` branch; the new `else: hit = False` makes
the step total.)

| # | Solution.lean impl op (`markerPresent`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `s : List Char` | the local working string `s` at the flag step | R | `str` ↔ `List Char` (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`; the marker is the space code point. |
| A2 | `if s.contains ' ' then Except.ok true` | `if ' ' in s:` … `hit = kern in s` | I + R | concrete membership. By mapping.md §3 the gold's `kern in s` (post-replace) equals `' ' in s` on the working string, because `kern` is chosen ABSENT from `s` and then substituted for every space. The success leg `Except.ok true` ↔ `hit = True` (R: `bool` ↔ `Except.ok Bool`). |
| A3 | `else Except.ok false` | `else: hit = False` | I + R | the no-marker path now yields a flag (`False`) rather than reading an unestablished value. `Except.ok false` ↔ `hit = False`. This is the totality the gold adds. |
| A4 | result `out = Except.ok (markerFlag s)`, `markerFlag s = s.contains ' '` | the flag `hit` after the step | R | the success leg carries the flag; `markerFlag` is the total membership value the two branches jointly compute. The failure leg `Except.error` is NEVER produced by Solution.lean — pinning the step total. |

Discriminating content of the change — the step must be **total** (always
`Except.ok`), never surfacing a failure on the no-marker path. This lives in the
`else Except.ok false` branch (A3) ⇔ the gold's added `else: hit = False`. The
pre-patch read the flag from an unestablished value on that path
(`UnboundLocalError`); `Solution_prepatch.lean` reproduces that by producing
`Except.error MarkerError.markerUnavailable` on the no-marker path and **fails**
`out = Except.ok (markerFlag s)` (G-DIFF) on exactly the `' ' ∉ s` case.

**Termination semantics.** The file uses `loom.semantics.termination "total"`
(total correctness). The real flag step is a straight-line membership test plus
branch — the gold's `if ' ' in s: … hit = kern in s; else: hit = False` always
terminates and yields a value (the `while kern in s` kern-selection loop
terminates on every finite string), and the F2P test observes the returned
result. Total correctness is therefore the faithful semantics. Partial
correctness would admit a same-spec implementation that diverges (an infinite
loop vacuously satisfies every `ensures`) — a wrong impl the tests would fail —
so it would leave the spec too weak.

## B. No axioms

There is no `axioms`-region content beyond the `MarkerError` failure-shape
inductive (a type used only to express the error leg; carries no `ensures` and
no callee claim). The only callee-like operation is the **concrete**
per-code-point membership `s.contains ' '`, modeled directly (tag I), not behind
an axiom. Hence this bundle ships **no `axiom_check.py` and runs no G-AX**: there
is no callee contract to validate against a real callee. The `while kern in s`
random-kern selection of the real code is observationally irrelevant to the flag
(mapping.md §3) and is not modeled — it neither changes the flag nor is changed
by the patch.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — making the flag
step total / error-free on the no-marker path — is modeled **directly** as the
two-branch membership returning the success leg in both cases (A2/A3). There is
no consumed axiom about the function under change.

## D. verify(Solution) ⇒ resolved

`markerPresent` verifies only if its output is `Except.ok (markerFlag s)` for
every `s` — i.e. it ALWAYS succeeds (never the error leg) and the flag equals
`s.contains ' '` (A2–A4). By R (`str ↔ List Char`, marker ↔ space code point,
`bool ↔ Except.ok Bool`) and the marker identity (mapping.md §3) the verified
step equals the gold's total flag step `if ' ' in s: … hit = kern in s; else:
hit = False` on the working string. By G-CONF the R/I transliteration of the
branch agrees with `patch.diff`'s behaviour on ≥10⁵ working strings (including
the F2P input `"(2*x)/(x-1)"`, which has no space after the transforms and so
takes the else/total path the bug crashed on). Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement — and
the gold patch resolves (G-RESOLVE). The single trust point is refinement
fidelity (this doc, G-EQ + G-CONF); there are no axioms (no G-AX leg).
