# RELAXED_LEAKAGE — astropy__astropy-13398 (lean)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

Policy: `prompts/lean/spec_guide.md` directive 6 — "**Exception —
relaxed-leakage:** for a proven `problem_statement ↔ gold` mismatch where a
faithful spec MUST name the discriminator, keep the instance with the leak
allowed". The gate honors it mechanically (`src/swebench_unified/gates/leak.py`)
through the `relaxed_leakage` meta flag plus this file, **even when the lexical
screen passes** — which is this bundle's situation: G-LEAK's lexical screen
reports "spec view clean", and the leak is semantic.

## The mismatch (problem_statement ↔ gold)

The public `problem_statement` (5323 chars) is a feature request for *direct*
ITRS ↔ AltAz/HADec transforms, with an inlined code sketch. Token scan,
re-measured here from `instance.json`:

| token | hits in problem_statement |
|---|---|
| `refraction` | **1**, and it is the disclaimer: *"I have yet to add refraction, but I can do so if it is deemed important to do so"* |
| `pressure`, `refco`, `erfa`, `atioq`, `atoiq` | 0 |
| `SELMIN`, `CELMIN`, `0.05`, `1e-6` | 0 |
| `add_refraction`, `remove_refraction`, `altaz_to_hadec` | 0 |
| `Newton`, `renorm` | 0 |

The inlined sketch has no refraction, no `pressure` test, and no AltAz→HADec
cross-rotation; it splits two ways on `isinstance(observed_frame, AltAz)`.

The gold edit does not stop there. Measured (not read off a stamp): the diff of
the `impl` regions of `Solution_prepatch.lean` against `Solution.lean` is
*exactly* the refraction path — the `pressure > 0` arm with `toApparent` and the
hour-angle cross-rotation in the forward leg, and the mirrored `toGeometric`
block in the inverse leg. So the graded delta of this cell **is** the facet the
`problem_statement` disclaims. A spec that says nothing about that facet does
not distinguish the pre-patch implementation from the gold one, and G-DIFF —
which requires `Solution_prepatch.lean` to FAIL — cannot pass. Naming the
discriminator is forced by the bundle's own construction, not chosen.

## Why the closed form, and not an abstract refraction step — measured

Three steps, each measured rather than argued.

**1. The carrier must be `Float`, not `ℝ`.** The prior G-EQ/G-PANEL-1 failure on
this cell was a same-spec rival that adds and subtracts `1e300` around an
Earth-scale vector. Over `ℝ` that rewrite is `ring`-provably the identity, and
`correct_*` is a predicate on the implementation's VALUE alone, so **no
postcondition over `ℝ` can reject it**: the rival verifies and its patch fails 3
of 4 FAIL_TO_PASS tests (`test_itrs_topo_to_altaz_with_refraction`,
`test_itrs_topo_to_hadec_with_refraction`, `test_itrs_straight_overhead`) plus 5
of 68 PASS_TO_PASS. Over `Float` the same rewrite collapses the vector to
exactly `0.0` and nothing closes the proof. `properties.py` pins that shape as
the reject case `forward-cancels-huge-offset`, and the two shapes the most
recent audit added on top of it are re-checked against this spec here:
`fatk_11` (the same cancellation in the INVERSE leg) and `fatk_12` (the
cancellation applied to the A coefficient VALUE) are both `same_spec = True` and
both exit 1, failing at `ring_nf made no progress on goal` — `Float` carries no
`CommRing` instance, so the rival cannot even state its lemma.

**2. Refraction cannot be axiomatized.** `spec_guide` directive 7 is explicit:
"NEVER axiomatize the function under spec or the operation the patch changes"
(`prompts/lean/spec_guide.md:70`), and refraction IS the operation the patch
adds. The reason is measured in this cell's own audit record: an attack that
keeps the Lean implementation intact and corrupts only the coefficient produced
Δel errors of **232663 mas at alt=10°, 41237 mas at 45°, 7273 mas at 80°**
against the tests' **0.1 mas** tolerance, and its patch was recorded NOT
RESOLVED (F2P 2/4 fail, P2P 0 fail). An opaque `refract` axiom admits exactly
that class of patch: the Lean side is unchanged, so it still verifies, while the
Python body it maps to is free to be wrong. Abstracting refraction therefore
reopens the SPEC-TOO-WEAK hole this repair closed.

**3. Given 1 and 2, the postcondition is a float64 equality with the real
callee, so every sub-expression is pinned bit-for-bit.** The question the
leakage finding raises is whether the *individual* pieces — the two clamp
constants, their values, the Newton denominator — are each necessary. Measured
inside the task image with the gold patch applied
(`leakmeas.py` → `leakmeas.log`; pyerfa 2.0.0.3), 10 elevations from 0.5° to
89.9999999°, against the real `add_refraction` / `remove_refraction`:

*Control.* The spec's transcription reproduces the real callee **exactly** —
`|diff| = 0` at all 10 elevations, in both legs. So the differences below are
differences from the real function, not from a model of it.

| piece elided from the spec | max difference from the real value | elevations where it bites |
|---|---|---|
| `sinAltFloor = 0.05` (sel unclamped) | 2.12e+04 m / 437.9 arcsec | 3/10 (0.5°, 2°, 2.8624°) |
| `cosAltFloor = 1e-6` (cel unclamped) | 1.86e-09 m | 2/10 (89.99999°, 89.9999999°) |
| Newton denominator | 1230 m / 25.37 arcsec | 10/10 |
| `B tan²z` term | 1.82e+04 m / 375 arcsec | 8/10 |
| small-angle cos → exact `cos` | 1.39e-07 m | 6/10 |
| final renormalisation | 1053 m | 10/10 |
| inverse leg: clamp `cel` too (symmetrise the legs) | 2.22e-03 m | 2/10 |
| inverse leg: use the forward Newton form | 1229 m / 25.36 arcsec | 10/10 |

Every row is non-zero, so every elided spec is **unfaithful** — it demands a
value the patched library does not produce. That is the G-PANEL-2
(spec-too-strong) defect class, and it is the *other* failure this cell was just
repaired for, so it is not a hypothetical cost.

The biting inputs are reachable through the public API, not artefacts: asking
for `AltAz(alt=0.5°, …, pressure=1000 hPa)` and transforming through ITRS makes
the forward leg see `sin(el) = 0.0056547301` (below 0.05, clamp bites), `alt=2°`
gives `0.031828226`, and `alt=89.9999999°` gives `cos(el) = 1.7458153e-09`
(below 1e-6, clamp bites).

## Which pieces the tests need, and which only faithfulness needs

Being precise about this matters, because the two justifications are not equally
strong. Measured over the **200 directions the FAIL_TO_PASS test itself
samples** (`leakmeas2.py` → `leakmeas2.log`; the exact configuration of
`test_itrs_topo_to_altaz_with_refraction`: `golden_spiral_grid(200)` over the
whole sphere, equatorial site, J2000, 1000 hPa, rh 0.5, tolerance 0.1 mas on
alt/az and 10 cm on distance):

- **102 of the 200 directions have `sin(el) < 0.05`** (minimum −0.991798), so
  the `sinAltFloor` regime is squarely inside the graded test. Eliding the clamp
  moves the altitude by up to **1.377e+06 mas** on those directions.
- Eliding the Newton denominator: **2.279e+04 mas**, 200/200 directions changed.
- Eliding the `B tan²z` term: **3.619e+05 mas**, 200/200 changed.
- Eliding the renormalisation: direction barely moves (1.8e-07 mas) but the
  vector moves by up to 1.9e+11 m, i.e. it is the *distance* assertion
  (10 cm tolerance) that it breaks; 188/200 changed.
- `cosAltFloor = 1e-6`: **0 of 200** directions reach `cos(el) < 1e-6`
  (minimum 0.0807442), so this clamp is **not** exercised by the test.
- small-angle cos → exact `cos`: 172/200 directions change, but by at most
  **3.75e-06 mas** — inside the 0.1 mas tolerance, so this is **not** exercised
  by the test either.

So four of the six pieces are load-bearing for *resolution* with margins of
10⁵–10⁶ against the tolerance, and two (`cosAltFloor`, the small-angle cosine)
are load-bearing only for *faithfulness* — they change the float64 value on
reachable inputs while staying inside the test tolerance. Those two are retained
because the postcondition is an equality, not because a test forces them. A spec
that dropped them would pass G-EQ and fail G-PANEL-2. There is no third option
available: with `Float` fixed by step 1 and deep modelling fixed by step 2, the
postcondition either equals the real computation or does not.

The control for this second measurement is weaker than for the first and is
recorded as such: over the test's own grid the transcription agrees with the
real callee to **9.16e-08 mas** in altitude, with a 0.0469 m Cartesian residual
on vectors up to 1.5e+14 m long (≈3e-16 relative). That residual is the
accumulation order of the rotation product in the comparison harness
(`np.einsum` versus `erfa.rxp`), not the refraction step; the bit-exact control
is the per-vector table above, where the difference is exactly 0.

## Two items are NOT gold-only — a measured correction

The leakage finding lists `refa`/`refb` and the `A·tan z + B·tan³ z` model form
among the leaked material. Both are reachable from the solver's own tree at the
base commit, measured in the image:

- `refa`, `refb` and `erfa.refco` are **existing repo vocabulary**:
  `astropy/coordinates/erfa_astrom.py` lines 59, 67, 74, 161, 342 already bind
  `refa, refb = erfa.refco(...)` before the patch.
- `erfa.refco.__doc__` in the installed pyerfa states *"Determine the constants
  A and B in the atmospheric refraction model dZ = A tan Z + B tan^3 Z"* and
  names its returns `refa`, `refb`. The model form is the dependency's public
  documentation.

They are renamed anyway (below). What is genuinely gold-only, re-confirmed by
`git grep` at `base_commit` 6500928dc0e57be8f06d1162eacc3ba5e2eff692 inside the
image, is the clamp-constant names and the helper names: `SELMIN`, `CELMIN`,
`add_refraction`, `remove_refraction`, `altaz_to_hadec_mat` — **0 hits each**.
Nor are they reachable upstream: the names originate in ERFA's `atioq.c`, the
repo vendors no erfa at that commit (`git ls-tree` of `cextern/` is cfitsio,
expat, wcslib and two trim scripts), and the installed pyerfa 2.0.0.3 exposes no
such symbol (`[n for n in dir(erfa) if "MIN" in n]` is empty). So the name+value
pairing was edit-localization a solver could not obtain from either the
statement or the repo, which is why the renames below are not cosmetic.

Every measurement in this file was re-run at that same `base_commit` checkout
with `patch.diff` applied, and reproduced the numbers above byte-for-byte
(`leakmeas_base.log` versus `leakmeas.log`: identical).

## What WAS done to the spec view (de-narration that costs no adequacy)

1. **Every gold-only identifier is gone.** `SELMIN`→`sinAltFloor`,
   `CELMIN`→`cosAltFloor`, `addRefraction`→`toApparent`,
   `removeRefraction`→`toGeometric`, `altazToHadecMat`→`poleTiltMat`,
   `toAltazMat`→`altazMat`, `toHadecMat`→`hadecMat`, `refCoef`→`bendCoefs`,
   `refa`/`refb`→`coefA`/`coefB`. None of the new names is a case-variant or
   substring of a patched repo symbol, so the edit-localization pointer — the
   sharpest part of the finding — is removed outright, not merely re-cased.
2. **The prose that restated the closed form is gone.** The `toApparent` and
   `toGeometric` docstrings no longer transcribe `Δel`, no longer name
   "Newton–Raphson", and no longer point at the ERFA reference routine; they
   state the abstract behavior and name the equations below as the definition of
   record. The two floor docstrings no longer paraphrase the gold's own comment,
   and the `bendCoefs` axiom docstring no longer quotes the model form.
3. **Provably code-only.** Mechanically back-substituting the nine renames makes
   `Solution.lean` byte-identical to the pre-edit file **apart from those five
   docstrings**, and the other six artifacts back-substitute byte-identically
   with no residue at all. Re-verified after the edit: `Solution.lean` exit 0,
   `Solution_prepatch.lean` still fails (exit 3, `sorry`), and the whole
   `properties.py` battery reproduces its previous exits exactly — 4 positives
   exit 0, 15 rivals exit 1, 15 witness-vs-rival exit 0, 15 witness-vs-gold
   exit 1, 15 gate consistency probes exit 1, 15 stronger binder probes exit 1,
   15 flipped-claim forgeries on the rival exit 1, 14/15 on gold exit 0 (the one
   documented script-shape artefact unchanged). No clause was weakened to buy
   de-narration.

This does **not** eliminate the leak: the `pure` region still determines the
refraction arithmetic, as steps 1–3 above show it must. That residue is what the
recorded relaxation covers.

## Core soundness (relaxation criteria 1–2)

All eleven mechanical gates are green on the artifacts this file accompanies —
ten record `pass` (G-VERIFY, G-DIFF, G-GOLD, G-MUT, G-PBT, G-INTEGRITY,
G-HYGIENE, G-RESOLVE, G-CONF, G-AX) and G-LEAK records `relaxed`, which
`scripts/green_check.py` treats as green alongside `pass` and `skip`. The same
eleven passed with G-LEAK at `pass` on the immediately preceding revision of
these artifacts, which differed from this one only in the identifier names and
the five docstrings described below. Detail worth naming: G-PBT — 19 spec cases behaved as
expected (4 positives + 15 rejected rivals); G-MUT — 20/20 mutants killed;
G-CONF — 100000 draws against the real callees in-container, 0 disagreements;
G-DIFF — the pre-patch implementation still fails the spec, so the spec still
sees the bug.

Criterion 1 (core sound) and criterion 2 (the leak is genuinely unavoidable,
measured above) hold; this file plus the `relaxed_leakage` meta flag supply
criterion 3 (in-bundle documentation).

## Second facet: the (site, epoch) carry — measured separately

The leakage role that re-derived this bundle after the rename campaign accepted
the refraction argument above and then measured a SECOND leaking facet that the
argument does not reach: the carry. It is dispositioned here on its own
measurements. The refraction unavoidability claim is NOT extended to it, because
it does not apply — as that role correctly measured.

**What the spec view hands over.** `carryTo` is declared over both endpoint pairs
(vector, source site, source epoch, target site, target epoch); the forward
postcondition puts it behind `siteDiffers … || epochDiffers …`; the inverse
postcondition applies it unconditionally; and its docstring says it is the
identity when the pairs agree and otherwise routes through an inertial frame,
"which also shifts stellar aberration".

**The public statement argues the opposite design.** Re-measured from
`instance.json`: *"One feature of this approach is that it treats the ITRS
position as time invariant. It makes no sense to be doing an ITRS->ITRS transform
for differing `obstimes` between the input and output frame, so the `obstime` of
the output frame is simply adopted."* Token counts in `problem_statement`:
`np.any` 0, `transform_to(ITRS` 0, `EarthLocationAttribute` 0, `location !=` 0,
`identity` 0; against `obstime` 3, `location` 3, `ITRS->ITRS` 3, `aberration` 1.
The topic is raised and the mechanism is argued *against*; the inlined sketch
ends `return itrs_frame.realize_frame(rep)` with no guard anywhere. So the
carry's presence and its shape are not derivable from the statement.

**Not needed for G-DIFF — recorded as accepted, not disputed.** The role measured
`NOCARRY_GOLD.lean` (the spec with every carry symbol deleted, refraction
retained) at exit 0, with a cross-control at exit 1 against the refraction-free
pre-patch implementation. That measurement stands: the refraction clause alone
makes the pre-patch implementation fail, so nothing about G-DIFF forces the
carry.

**Nor is it needed for any graded assertion — measured here.** In the task image
at `base_commit` 6500928dc0 with `patch.diff` applied and the harness's own
`pip install -e ".[test]"` step run (`carrymeas.log`, `cirs_topo_calls.log`):

| the F2P tests' own frame pairs | site differs | epoch differs | guard |
|---|---|---|---|
| `ITRS(location=loc)` → `AltAz(J2000, loc)` | no | no | no-op |
| `ITRS(location=loc)` → `AltAz(J2000, loc, 1000 hPa)` | no | no | no-op |
| `ITRS(location=loc)` → `HADec(J2000, loc)` | no | no | no-op |
| `ITRS(location=loc)` → `HADec(J2000, loc, 1000 hPa)` | no | no | no-op |
| `ITRS(J2010, home)` → `AltAz(J2010, home)` | no | no | no-op |
| `ITRS(J2010, home)` → `HADec(J2010, home)` | no | no | no-op |

`ITRS(location=loc)` takes `DEFAULT_OBSTIME`, which is `Time('J2000', scale=tt)`
— the same object the tests' `obstime='J2000'` parses to (measured: the epoch
comparison is False, not merely close), so the guard is dead on every graded
input. On the same six pairs the trailing inverse carry is bit-exactly the
identity: `max |carry(x) − x| = 0 m`, `np.array_equal` true. And
`test_cirs_itrs_topo`, the F2P test whose subject IS the carry semantics, calls
the two functions under spec **zero** times — its own assertions pass while the
call counters read `itrs_to_observed=0 observed_to_itrs=0`, against a control of
`1/1` for one explicit ITRS↔AltAz round trip. That test grades `ITRS.location`
and the CIRS↔ITRS transforms, which this spec models opaquely and does not
implement. So no graded assertion can distinguish the carry from its absence, and
the facet belongs to the class this file already separates: faithfulness-bearing,
not test-bearing, exactly like `cosAltFloor` and the small-angle cosine.

**What denying it costs — measured on the same run.** The differing-pair inputs
are reachable by passing two ordinary frames, and the real carry moves the answer
by:

| input pair | max effect of the carry |
|---|---|
| epoch J2010 → J2011, same site | 2.97e+08 m |
| site home → other site, same epoch | 2.33e+06 m |
| site and epoch both differ | 2.99e+08 m |
| site home → geocentre | 5.00e+06 m |
| forward leg, gold body vs a carry-less body (epoch differs) | 2.98e+08 m |
| forward leg, gold body vs a carry-less body (site differs) | 2.03e+06 m |
| forward leg, HADec + refraction, site differs | 2.03e+06 m |

A spec asserting the un-carried value on those inputs is unfaithful by those
margins. This is not hypothetical for this cell: the faithfulness defect it was
repaired for was precisely a wrong carry *shape* — the earlier 3-argument reading
over-constrained `observed_to_itrs` and disagreed with the patched library by
5.46613e+06 m across 21 configurations.

**The two leak-free alternatives, and the price of each.** Both are real; neither
is free, and neither is dismissed here.

1. *Delete the carry from the spec view.* The `opaque` declaration lives in the
   spec view, so the implementation could not use it either, and the modelled
   functions would stop being the patched functions on every input in the table
   above — converting a leakage finding into the faithfulness class of finding
   this cell was repaired for.
2. *Narrow the modelled domain to the same-pair case* under a hypothesis, and
   drop the carry from the postconditions. G-DIFF still passes (the role measured
   it) and no graded assertion is lost (measured above); the price is that the
   equality then says nothing about the inputs in the table — the spec's silence,
   rather than its content, carries them.

What this file dispositions is the revision on disk: the carry is named, in the
shape the patched library actually computes, with the divergence table as the
reason.

**Prose versus shape.** Two clauses of the `carryTo` docstring are consumed by no
proof — "identity when the two pairs agree" and "which also shifts stellar
aberration". Both theorems close by `split_ifs <;> rfl` and `carryTo` is opaque,
so nothing in the development uses either property (G-AX probes them against the
real routine instead). They are de-narration candidates and are recorded as such.
What de-narration cannot do is settle the facet: what the role measured is the
SHAPE — which leg is guarded, which is unconditional, and the two-pair dependence
— and the shape is what the divergence table forces.

## Scope of the relaxation: which facet is dispositioned

This section records what the relaxation does and does not cover, as a statement
of scope. It draws no conclusion about any verdict; the facts above and the gate
record are the whole of what this file offers.

**The facets covered.** Two, each on its own measurements, and the second does
NOT inherit the first's argument.

1. *Atmospheric correction.* The `pure` region of the spec view exposes the step
   the `problem_statement` disclaims — that it exists, where it sits
   (`pressure > 0`, plus the hour-angle cross-rotation, and the forward/inverse
   asymmetry), and its closed form including both floor constants and their
   values. That disposition rests on the token scan, the impl-region diff
   identifying the graded delta, the eight-row divergence table with a bit-exact
   control, the 102-of-200 coverage count on the test's own grid, and the
   re-checked rival exits.
2. *The (site, epoch) carry.* The spec view exposes the guarded-forward /
   unconditional-inverse asymmetry and the two-pair dependence, against a
   statement that argues for a time-invariant reading. That disposition rests on
   the section above it: the guard is a no-op on all six graded frame pairs, the
   trailing carry is bit-exactly the identity there, the F2P test whose subject is
   the carry never calls the functions under spec (0 calls against a 1/1
   control) — and yet the carry moves the answer by 2.0e+06 to 3.0e+08 m on
   differing-pair inputs that ordinary calls reach. It is
   faithfulness-bearing and not test-bearing, and the two leak-free alternatives
   are priced rather than dismissed.

**What is outside them.** Nothing here speaks to any further leaking line — a
spec-view identifier colliding with some other patched repo symbol, or narration
of a bug→fix mechanism elsewhere, is untouched by this disposition and is not
argued for above.

**What would break it.** Two things, both checkable. First, core soundness: the
gate record in the section above. Second, the unavoidability claim, which is
refuted by exhibiting a spec that (a) rejects the `1e300` cancellation family in
both legs and on coefficient values, (b) rejects a patch whose Python
refraction body is wrong while its Lean implementation is untouched, and (c)
agrees with the real `add_refraction`/`remove_refraction` at float64 on the
input classes in the divergence table. No such spec is claimed to be impossible
in principle; what is measured is that dropping any single piece breaks (c), and
that abstracting the step breaks (b) with a recorded NOT-RESOLVED margin. For the
carry facet the refutation is narrower and cheaper: exhibit a carry-free spec that
still agrees with the patched library on the differing-pair rows of its table, or
show that those rows are unreachable through ordinary calls. Neither is claimed
impossible; what is measured is the size of the disagreement.

**On re-checking.** The measurements are reproducible rather than asserted:
`leakmeas.py`, `leakmeas2.py` and `carrymeas.py` re-run in the task image against
the real callees, and `count_calls.py` plus a plain-python replay of
`test_cirs_itrs_topo` re-derive the call counts; the token scan re-runs from
`instance.json`; the gold-only token counts
re-run as `git grep` at the image's base checkout; the rival exits re-run
through `scripts/lean_verify.sh`; and G-CONF re-plays the model against the real
callees on every gate run. A reader who reaches a different number than the
tables record has found something this file gets wrong.

Per `src/swebench_unified/gates/_audit.py`, leakage relaxation is a G-LEAK
concept: there is no "relaxed" status at the panel layer, and nothing downstream
re-applies the relaxation to a panel-layer verdict. That is a fact about the
pipeline's wiring, noted so a reader knows this file's flag does not propagate.
