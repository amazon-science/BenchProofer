# refinement.md — matplotlib__matplotlib-13989

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `buildHistOptionsM` `do` block and the deep `buildHistOptions` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** / **A-reference** (axiom legs — none here), or **I** (identical
concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); there are no A legs (no axioms), so G-AX is not applicable. Claim: any
impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The option-mapping assembly — `Axes.hist` (`lib/matplotlib/axes/_axes.py:6654–6689`)

Gold hunk (the patch changes the density-entry write from a whole-dict
**replacement** to an in-place **add**):
```
         density = bool(density) or bool(normed)
         if density and not stacked:
-            hist_kwargs = dict(density=density)   # REPLACES dict -> drops any 'range' entry
+            hist_kwargs['density'] = density       # ADDS the entry -> keeps 'range'
```
Effect: the explicit data-bounds entry (`hist_kwargs['range'] = bin_range`, set
earlier for a single-dataset call) is no longer wiped when the density entry is
recorded, so `np.histogram` still honours the requested bounds and the returned
bin edges span them.

| # | Solution.lean impl op (`buildHistOptionsM`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `boundsOpt : Option (Float × Float)` | the `'range'` entry of `hist_kwargs` as it stands at the density write (present iff set at `:6685`) | R | `'range' in d` ↔ `some _`, payload carried opaquely (mapping.md §2). |
| A2 | params `density`, `accumulate : Bool` | locals `density` (`:6688`) and `stacked` (the `not stacked` guard) | R | `True ↔ true`, `False ↔ false` (mapping.md §2). |
| A3 | `let base := { boundsOpt := boundsOpt, densityOpt := none }` | the mapping before the density write: it already carries the `'range'` entry (`:6685`) and no `'density'` entry | I | identical: the carrier entering the density write is exactly the bounds entry plus no density entry. |
| A4 | `if density && !accumulate then { base with densityOpt := some density }` | (post-image) `if density and not stacked: hist_kwargs['density'] = density` | I | **the behavioural change**: `{ base with densityOpt := … }` is the record analogue of an in-place key add — it keeps `base.boundsOpt` and only writes the density field. The pre-image `hist_kwargs = dict(density=density)` instead REBINDS the carrier, dropping the bounds entry; the prepatch models that as `{ boundsOpt := none, densityOpt := … }`. |
| A5 | `else base` | the `density and not stacked` guard being false → `hist_kwargs` left unchanged | I | identical: no density entry written; the mapping is unchanged. |
| A6 | result `out : HistOptions` returned | the `hist_kwargs` mapping passed to `np.histogram(..., **hist_kwargs)` (`:6698`) | R | `HistOptions` ↔ the dict's `'range'`/`'density'` entries (mapping.md §2). The unchanged `np.histogram` then honours a present `'range'` entry — the F2P oracle (G-RESOLVE). |

No A (axiom) steps; no kind-3 (changed inexpressible) steps. The assembly is a
pure dict construction with one conditional key write, modeled deeply and tagged
**R/I**.

Discriminating content of the change — recording the density choice must
**preserve** the already-determined bounds entry instead of discarding it —
lives in the impl op A4 (`{ base with densityOpt := … }`, keeping
`base.boundsOpt`) ⇔ `hist_kwargs['density'] = density` (the real in-place add).
The pre-patch `hist_kwargs = dict(density=density)` discards the bounds entry;
`Solution_prepatch.lean` reproduces that (`{ boundsOpt := none, densityOpt := …
}`) and **fails** the frozen spec's `out.boundsOpt = boundsOpt` clause (and the
`out = buildHistOptions …` clause) — G-DIFF. The failure is precisely
`none = boundsOpt` unprovable in the `density = true, accumulate = false` case.

## B. verify(Solution) ⇒ resolved

`buildHistOptionsM` verifies only if its result equals `buildHistOptions
boundsOpt density accumulate` AND the three discriminating clauses hold:
`out.boundsOpt = boundsOpt` (bounds entry ALWAYS preserved),
`(density ∧ ¬accumulate) → out.densityOpt = some density`, and
`¬(density ∧ ¬accumulate) → out.densityOpt = none`. By R (the `HistOptions` ↔
`hist_kwargs`-entries bijection, mapping.md §2) the verified assembly equals the
patched assembly block of `Axes.hist` on the modeled inputs. The F2P test pins
exactly this: a single-dataset density call with explicit bounds
(`boundsOpt = some (0,1), density = true, accumulate = false`) must keep the
bounds entry, so `np.histogram` returns edges with `bins[0] == 0`,
`bins[-1] == 1`. The pre-patch dropped the bounds entry → edges spanned the
data range instead (the reported `[0.0033…, 0.933…]`).

By G-CONF the R/I transliteration of `buildHistOptions` agrees with `patch.diff`'s
behaviour over the full finite control space plus fuzz. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). There are no axiom trust
points (no axioms); the only trust point is refinement fidelity (this doc,
G-EQ + G-CONF).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely changed — whether recording
the density choice replaces or extends the option mapping — is modeled **deeply**
(the `{ base with densityOpt := … }` record update, A4, which structurally
preserves `boundsOpt`), not hidden behind an axiom about the function under
change. There are no consumed axioms and no A-reference deep models of outside
callees. `np.histogram` (the unchanged downstream consumer) is the G-RESOLVE
oracle, not a modeled callee.
