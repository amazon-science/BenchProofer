# refinement.md — matplotlib__matplotlib-26208

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `inheritSharedConvA` / `inheritSharedConvB` `do` blocks) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement; state the
bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(deep model validated == real callee by G-AX), or **I** (identical concrete op).
EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The x-sharing companion site — `twinx()` (`lib/matplotlib/axes/_base.py:4441`)

Gold hunk (added line):
```
+        ax2.xaxis.units = self.xaxis.units
         return ax2
```

| # | Solution.lean impl op (`inheritSharedConvA`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `source : ConvSetting` | `self.xaxis.units` (the source axis's setting) | R | `Axis.units` value ↔ `Option Int` (mapping.md §2): `None ↔ none`, a present object ↔ `some id(obj)`. |
| A2 | `let out := source` (deep value copy) | `ax2.xaxis.units = self.xaxis.units` | I | the changed op is a plain reference copy of the source setting onto the companion axis; modeled deeply as a value copy. Identical concrete op (no callee, no abstraction beyond the R type bijection). Transliterated and refuted by G-CONF. |
| A3 | `return out` (`ConvSetting`) | the companion `ax2`'s `xaxis.units` after `twinx` returns | R | the returned value is the companion axis's setting; observed by the F2P test via `ax2.xaxis.units is ax1.xaxis.units` (object identity ↔ value equality of the identity tag) and `is not None` (↔ `isPresent`). |

Discriminating content of the change — the companion axis carries the *same*
present setting as the source rather than the freshly-initialised absent default
— lives in `out = source`. The pre-patch companion axis kept its construction
default `None` (`Axis.__init__`: `self.units = None`); `Solution_prepatch_1.lean`
reproduces that (`out := none`) and **fails** `out = source` whenever the source
carries a present setting (G-DIFF).

## B. The y-sharing companion site — `twiny()` (`lib/matplotlib/axes/_base.py:4470`)

Gold hunk (added line):
```
+        ax2.yaxis.units = self.yaxis.units
         return ax2
```

| # | Solution.lean impl op (`inheritSharedConvB`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `source : ConvSetting` | `self.yaxis.units` | R | same bijection as A1 (mapping.md §2). |
| B2 | `let out := source` (deep value copy) | `ax2.yaxis.units = self.yaxis.units` | I | identical to A2 at the second, independently-observed site. |
| B3 | `return out` | companion `ax2`'s `yaxis.units` after `twiny` returns | R | same as A3, on the y coordinate. |

`Solution_prepatch_2.lean` reproduces the pre-patch absent default at this site
(`out := none`) and **fails** `out = source` (G-DIFF). The two sites are modeled
and exercised independently because the F2P test is parametrised over `twin ∈
{x, y}` and asserts each coordinate on its own.

## C. No kind-3 (inexpressible-changed-op) steps; no consumed axioms

Every step is R or I. The only operation that genuinely *changed* — carrying the
source axis's conversion setting onto the companion axis — is modeled **deeply**
(the value copy `out = source`, steps A2/B2), not hidden behind an axiom about
the function under change. There is **no consumed axiom** and **no A-reference
deep model of an unchanged callee** (`axiom_check.py` asserts the inventory is
empty; G-AX is vacuous). The fidelity of the deep model to the real patched code
is audited by G-CONF against the REAL patched `twinx`/`twiny`.

## D. verify(Solution) ⇒ resolved

`inheritSharedConvA`/`inheritSharedConvB` verify only if the companion axis's
setting equals the source's (`out = source`, hence `isPresent out = isPresent
source`). By the R bijection (`Axis.units ↔ Option Int`, object identity ↔
identity-tag equality), the verified copy equals `ax2.<axis>.units =
self.<axis>.units` on every input. The sole FAIL_TO_PASS test
(`test_twin_units[x]` / `[y]`) asserts exactly: after plotting along the shared
coordinate so the source axis carries a present setting, the companion axis
(a) carries a present setting (`units is not None` ↔ `isPresent out`, true
because `isPresent source` holds once a quantity is plotted) and (b) carries the
*same* setting object (`ax2.<axis>.units is ax1.<axis>.units` ↔ `out = source`).
Both are pinned by the spec. By G-CONF the R/I transliteration agrees with
`patch.diff`'s behaviour on ≥10⁵ inputs. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to the type refinement — and the
gold patch resolves (G-RESOLVE). The single trust point is refinement fidelity
(this doc, G-EQ + G-CONF); there are no axioms to trust (G-AX vacuous).
