# refinement.md — matplotlib__matplotlib-24970

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`resolveSlots` `do` block, the deep `slotOf`/`slotSeq` value model, the abstract
index container `IndexRow` read through `slotsOf`, and the axiomatized callee
`assignReserved` with its `markersAdmitted` capability) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement; state
the bijection), **A-consumed** (proof uses the callee axiom's `ensures` — both
the result and the capability), **A-reference** (deep model validated == real
callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
axiomatized callee contract, the built-container readback, and the classification
the two are stated over are validated against real numpy by **G-AX**
(`axiom_check.py`); the narrative is audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## 0. What the F2P test actually observes (the discriminator)

The sole F2P test is `test_index_dtype[uint8]`:
`assert_array_equal(cm(np.uint8(0)), cm(0))`, run under matplotlib's pytest
config (warnings promoted to errors). The data value is **0**, unmasked, default
`N = 256`. The *colour value* of `cm(np.uint8(0))` is **identical** pre- and
post-patch (slot 0) — the resolved slot VALUES are byte-for-byte equal in both
trees. The test fails pre-patch NOT on a value difference but because the
reserved-marker assignment statements
(`xa[xa>N-1]=_i_over`, `xa[xa<0]=_i_under`, `xa[mask_bad]=_i_bad`) convert the
reserved-index scalars (`N+1=257`, `N=256`, `N+2=258`) into `xa`'s narrow uint8
container, which numpy evaluates **regardless of whether any element matches the
mask** (here none does) — an out-of-bound integer conversion that the test
config promotes to a failure. The gold fix casts `xa` to a signed `int` (a wide
container that admits every reserved index) BEFORE those stores, so the
conversion is in-range and the operation completes.

The discriminator is therefore a **completing-assignment effect** — whether the
reserved-marker stores are carried out on a carrier that admits the indices they
write — present on the F2P input even though the resolved slot VALUES are
unchanged. There is no value-level discriminator on the F2P input. The effect is
modeled as an unforgeable capability `markersAdmitted out paletteSize`, granted
ONLY by an admitting reserved-marker assignment and held ONLY by the container
that assignment produced (A3′).

The cast the fix hoists does two things at once, and the P2P suite observes the
second one. `xa.astype(int)` targets the platform **signed** `int`, so the
container it produces both admits every reserved index AND represents values below
zero. The second property is what keeps `xa[xa<0] = self._i_under`
(`colors.py:731`) alive: in a container that reaches high enough for the markers
but not below zero, that selection matches nothing and every below-range element
keeps the `overSlot` the preceding store wrote — a VALUE divergence on all
below-range inputs, which is what the out-of-range PASS_TO_PASS cases
(`test_get_under_over_bad`, `test_colormap_invalid`, `test_BoundaryNorm`, the
`test_colormap_reversing` family) observe. So the container has two extents and
the spec has to require both (mapping.md §2.3, A4/A5).

## A. The index-resolution site — `Colormap.__call__` (`lib/matplotlib/colors.py:683`)

The gold hunk (`colors.py:715–731`) moves the index cast `xa = xa.astype(int)`
out of the `if xa.dtype.kind == "f":` branch so it runs **unconditionally** (for
integer dtypes as well as floats), under `np.errstate(invalid="ignore")`, BEFORE
the three reserved-marker writes. The observable consequence: the carrier that
holds each resolved slot is always wide enough (a signed `int` array) to admit
the reserved markers `N`, `N+1`, `N+2`, regardless of the input dtype.

| # | Solution.lean impl op (`resolveSlots`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `paletteSize : Nat`, `cells : List Cell` | `self.N` and the input array `X`/`xa` of `__call__` | R | `self.N` ↔ `paletteSize` (`int(N) ≥ 0`, so `Nat` exact); the row of input elements ↔ `List Cell`, each element abstracted to its post-classification class (mapping.md §2, §2.1). G-CONF bridges via the `classify` shadow. |
| A2 | (no node) the classification producing each `Cell` | the bad-mask, the float scale `xa *= self.N` and the clamps `xa[xa<0]=-1`, `xa[xa==N]=N-1`, `np.clip(xa,-1,N)` (`colors.py:709–726`), followed by the index cast — so the class is the one the three stores see, taken on the POST-cast value | R | the classification rule is unchanged by the patch; what the patch moves is the cast, and the cast sits upstream of the stores that read the class, so the faithful reading is the post-cast one (mapping.md §2.1). The four classes `inPalette k / belowRange / aboveRange / invalid` are exactly the four kinds reaching the reserved-marker block, `invalid` last-write-wins. Includes the wrapping region: an unsigned element that does not fit the signed carrier classifies as `belowRange`. Bridged by G-CONF's `classify` shadow and pinned against real numpy by `axiom_check.check_post_cast_classification`. The IMAGE of this classification is narrower than the `Cell` syntax — it produces `inPalette k` only for `k ≤ N-1` — and `cells` is an INPUT the modeled function does not constrain, so the denotation A3 gives has to be faithful on the WHOLE syntax and not merely on the image (mapping.md §2.4). G-CONF fuzzes forward through `classify`, so it reaches the image only; the out-of-image region is pinned by `axiom_check.check_selection_order_dominance` and by the two row-rewrite rivals in `properties.py`. |
| A3 | the READ of the produced container: `slotsOf out = slotSeq paletteSize cells` (`inPalette k ↦ k` while `k < N`, else `↦ overSlot`; `belowRange ↦ N`, `aboveRange ↦ N+1`, `invalid ↦ N+2`) | reading the per-element indices out of the array `colors.py:728–732` wrote, which is what `lut.take(xa, mode='clip')` (`colors.py:738`) addresses rows with | I | concrete, transliterated by G-CONF. The three reserved classes land in their own distinct trailing slots; an ordinary index keeps its value only while that value is strictly inside the palette, because the three stores are three SELECTIONS in a fixed order and the FIRST of them, `xa[xa > self.N - 1]`, also selects an element carrying one of the reserved marker values — first selection wins, so such an element resolves to `overSlot` (mapping.md §2.4, measured by `axiom_check.check_selection_order_dominance`). The ORDERING is therefore load-bearing for the resolved value, and the guard on `slotOf (.inPalette k)` is exactly where it enters. The index VALUES are unchanged by the patch (identical in both trees), which is why they cannot be the discriminator; what the spec adds is that these values must be read out of the container the assignment produced (A5), not out of one the impl built. |
| A3′ | the result type `out : IndexRow`, observed only through `slotsOf` | the `numpy.ndarray` bound to `xa` when `lut.take(xa, …)` reads it (`colors.py:738`) | R | a container is index values **plus** the integer dtype they are stored in — described here by TWO independent extents, how far it reaches up (`carrier`) and whether it reaches below zero (`admitsNegative`, mapping.md §2.3); two arrays can read back the same indices in different widths and only one of them admitted the reserved markers, so the modeled result is the abstract container and not its value list (mapping.md §2.2). `rowOf` (build an array from values in hand) is kept apart from `assignReserved` (carry out the assignment) for the same reason; the separation is the executable content of `axiom_check.check_provenance_not_readable`. |
| A4 | `admitsNegative := true` and `carrier := paletteSize + 3` passed to `assignReserved` | `with np.errstate(...): xa = xa.astype(int)` — the cast moved out of the float branch so it runs for ALL dtypes BEFORE the reserved-marker writes | R | the cast target is the platform **signed** `int`, and the assignment needs BOTH of its properties, because it selects on BOTH ends of the container: it admits every reserved index (`int` represents any value `≤ N+2`) — modeled by `carrier = paletteSize + 3`, which admits `0 .. paletteSize+2` — and it represents values below zero, so the below-range selection `xa[xa<0]` (`colors.py:731`) is live — modeled by `admitsNegative = true`. The two extents are independent: an unsigned container of any width admits every reserved index while making that selection dead (mapping.md §2.3, measured). The cast itself is unchanged numpy `astype`; the refinement is the choice of both extents. What these two obligations do NOT claim is worth stating, because an earlier revision of this row over-claimed it: they do not single out the platform signed `int`. A narrower admitting container (`int16` at `N = 256`) satisfies both and agrees with the platform `int` on the entire float-valued path, since the upstream clamp bounds every float-derived value inside `-1 .. N`; it separates only on integer-dtype input, and that separation is a RE-CLASSIFICATION (it changes `cells`, A2) rather than a change in the container the assignment runs in, so it is upstream of the modeled function. The obligations are exactly the two selection boundaries and nothing more — measured, `axiom_check.check_carrier_refinement_scope`. |
| A5 | `out <- assignReserved cells paletteSize admitsNegative carrier` (the gated callee), which PRODUCES a container and grants `markersAdmitted out paletteSize` for that container | the unchanged per-element reserved-marker assignment `xa[xa>N-1]=_i_over`; `xa[xa<0]=_i_under`; `xa[mask_bad]=_i_bad` (`colors.py:730–732`), whose result is the array `lut.take(xa, mode='clip')` then reads (`colors.py:738`) | A-consumed | the unchanged array operation (the three sequential conditional stores, same constants). The proof CONSUMES this callee's contract: the container it produced reads back `slotSeq …` AND carries the `markersAdmitted` capability — but the contract applies ONLY when every one of the three selection steps is live in the container: `paletteSize+3 ≤ carrier` (the reserved-index writes are in range — exactly the legality of the store) AND `admitsNegative = true` (the below-range selection selects something at all, without which the readback claim would itself be false — mapping.md §2.3). The capability is granted for the container the assignment WROTE INTO and for no other, which is what makes it untransferable to a value-equal array. Validated == the real numpy operation by G-AX (mapping.md §3, axiom_check.py). |

### A.diff — how the spec sees the change (G-DIFF)

The discriminating content of the change — the reserved-marker assignment **must
be carried out on a container in which every one of its three selection steps is
live**: one that admits every reserved index up to `N + 2` AND represents values
below zero — lives in the interaction of A4 and A5: `resolveSlots` may only call
`assignReserved` (and so obtain the `markersAdmitted` capability its
postcondition requires) once it has established BOTH `paletteSize + 3 ≤ carrier`
and `admitsNegative = true` (A4). The gold patch establishes both at once by
casting to the platform signed `int`. `Solution.lean` calls
`assignReserved cells paletteSize true (paletteSize + 3)`: both obligations hold,
the capability is granted, the postcondition `markersAdmitted out paletteSize` is
discharged, and it verifies.

`Solution_prepatch.lean` models the pre-patch container by calling
`assignReserved cells paletteSize false paletteSize` — the container the element
arrived in, for an integer-dtype input the widening never touches: unsigned, with
a non-negative extent of only `paletteSize`. NEITHER obligation holds
(`false = true` and `paletteSize + 3 ≤ paletteSize` are both unprovable), so the
capability is never granted, the postcondition cannot be discharged, and
verification **fails** — on exactly the input-independent container legality the
fix changes. Measured failure goal: `false = true` (the first obligation the
verifier reaches). Both obligations are independent of `cells`, so the failure is
present on EVERY input (empty / all-in-range included), matching the warning the
F2P actually discriminates.

The width obligation alone would not be enough, and this is measured rather than
argued. The same call at an enormous UNSIGNED width —
`assignReserved cells paletteSize false (max 65536 (paletteSize + 3))`, the
transliteration of a `uint16` container — discharges `paletteSize + 3 ≤ carrier`
by `Nat.le_max_right`, is not a launder and not a fabrication (it hands on exactly
the container the gated call produced), and its faithful counterpart passes the
F2P while breaking 172 of 253 PASS_TO_PASS tests, because the below-range store is
dead in it. Under the two-extent contract it is REJECTED at exit 1 with the sole
residual verification condition `false = true`, while the SAME width with the
signedness restored (`true (max 65536 (paletteSize + 3))`) still verifies at exit
0 — so the obligation added is about the below-range selection being live, not
about the width. The gate is semantic rather than syntactic: a computed
`decide (1 < 0)` in that argument is rejected on `decide (1 < 0) = true` and a
computed `decide (0 < 1)` verifies.

The capability is unforgeable and untransferable. `markersAdmitted` is `opaque`,
so an impl cannot fabricate it: an impl that builds the value-correct container
itself instead of routing through the gated call fails at the unprovable
`markersAdmitted (rowOf (slotSeq paletteSize cells)) paletteSize` (measured, and
shipped as `properties.py`'s `reject-fabricate-value-correct`). And because it is
a predicate on the CONTAINER rather than on the index values, it does not travel
across a value-equal rebuild: an impl that carries out the admitting assignment
and then hands on a container it built from the resolved values — either spelled
out (`rowOf (slotSeq paletteSize cells)`) or read back out of the produced
container (`rowOf (slotsOf r)`) — is rejected on that same goal, measured with the
value clauses discharged by hand so the outcome cannot be a tactic artefact
(`properties.py`, accounting block "FAMILY 2: THE LAUNDER"). That rebuild is the
behaviour under repair: in the repository the container an implementation has in
hand without carrying out the assignment is the input's own narrow array. This
closes the prior framings' defects: the discriminator is neither a hand-picked
returned constant nor a predicate over index values, but a property of the
container an admitting assignment produced.

## B. No kind-3 (unexpressible-changed-op) steps

Every step is R, I, or A-consumed. The one operation that genuinely *changed* —
casting to a signed `int` container before the reserved-marker writes — is
captured by the combination of the two-extent container refinement (A4) and the
callee's two-part legality precondition (A5: the assignment is well-defined, and
grants its capability, only on a container that admits every reserved index AND
represents values below zero). The assignment itself
(`assignReserved`) is an UNCHANGED numpy operation invoked by both twins; it is
**A-consumed** (the proof uses its contract — both the produced container's
readback and the capability) and validated against the real numpy operation by
G-AX. The other two assumptions are about UNCHANGED operations as well: `slotsOf`
is the read the palette lookup performs and `slotsOf_rowOf` is the readback of the
ordinary array construction (mapping.md §3.3, `axiom_check.check_container_readback`).
There is no axiom about the function under change, and no kind-3 step.

## C. verify(Solution) ⇒ resolved

`resolveSlots` verifies only if the container it hands on holds the unforgeable
`markersAdmitted out paletteSize` capability. That capability is obtainable ONLY
from `assignReserved`, whose contract grants it ONLY under BOTH
`paletteSize + 3 ≤ carrier` — a container that admits every reserved index it
writes — and `admitsNegative = true` — a container in which the below-range
selection is live — and grants it ONLY for the container that call produced. So a
verifying impl must hand on the container an assignment wrote into that was live
in both directions: it can neither hand on one a narrow assignment produced, nor
one an unsigned assignment produced at any width, nor substitute a container of
its own carrying the same index values, even though the values are identical in
every case. The gold patch establishes both obligations at once by casting to a
signed `int` for ALL dtypes before the writes (A4); by R (`self.N ↔ paletteSize`,
element ↔ `Cell`, the resolved index array ↔ `out` with `slotsOf out` its index
values, the container's non-negative extent ↔ `carrier` and its signedness ↔
`admitsNegative`) and by
G-AX (the assignment's slot result == `slotSeq` over the row; `paletteSize + 3 ≤
carrier` coincides EXACTLY with the real "no out-of-bound conversion" legality;
and `admitsNegative = true` coincides EXACTLY with the produced container reading
back `slotSeq` on rows containing a below-range element, with every unsigned dtype
as the negative control), the verified resolver equals the gold patch's integer
pipeline on the tested inputs AND performs the reserved-marker stores only on a
container in which all three of them are live (the operation completes and the
below-range elements reach their own marker).

One more leg is needed before "equals the gold patch's integer pipeline" follows,
and it is about the ROW rather than the container. `cells` is an INPUT the modeled
function does not constrain, so an implementation may hand the assignment a row of
its own choosing; C1 sees that row only through `slotSeq paletteSize`. The
denotation therefore has to make `slotSeq`'s fibres coincide EXACTLY with the
identifications the repository itself makes: two classes may share a resolved slot
only when the three selections really do resolve them alike. Under the current
`slotOf` that holds — an ordinary index at or above `paletteSize` shares
`overSlot` with `aboveRange`, which is what the first selection actually does, and
no ordinary index reaches `underSlot` or `invalidSlot` at all
(`slotOf_inPalette_ne_underSlot`, `slotOf_inPalette_ne_invalidSlot`). So a rewrite
of the row that C1 cannot see is one the repository cannot see either, and a rewrite
the repository can see is rejected.

This is the second claim a previous revision got wrong, and both corrections are
recorded because the earlier text is what the audits falsified. The revision before
this one asserted in A3 that "each class lands in its own distinct slot" and that
"the Python assignment ordering is irrelevant to the resolved value of a class".
Both are false of the frozen text: the ordering is precisely what decides an
ordinary index carrying a reserved marker value, and under the identity reading
`.belowRange` and `.inPalette N` (likewise `.invalid` and `.inPalette (N+2)`) landed
in the SAME slot. Two implementations exploiting that collision verified while
diverging from the gold pipeline on every below-range, resp. invalid, input
(measured: F2P 1/1 pass, P2P 81 pass / 172 fail and 82 / 171). The missing
observable was the resolved slot of an ordinary index, made observable in Python by
`xa[xa > self.N - 1] = self._i_over` running FIRST with a predicate that also holds
of the marker values it stores; the guard in `slotOf` is what now excludes those
implementations, and the exclusion is measured (`properties.py`,
"FAMILY 3: THE ROW REWRITE THROUGH THE GATED CALL") together with the benign third
rewrite that must keep verifying.

The earlier revision before that described the
container by its non-negative extent alone, so "equals the gold patch's integer
pipeline" did not follow from verification: an unsigned container of sufficient
width satisfied every obligation and diverged from the gold pipeline on every
below-range input (measured: F2P 1/1 pass, P2P 81 pass / 172 fail). The missing
observable was the container's signedness, made observable in Python by
`xa[xa<0] = self._i_under` being a predicate on negative values; the second
obligation of A5 is what now excludes it, and the exclusion is measured in A.diff
rather than argued. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
one audited A-consumed callee — and the gold patch resolves (G-RESOLVE). The two
trust points are axiom soundness (G-AX: the `assignReserved` contract, including
its weakest-sufficient legality precondition, over-approximates the real numpy
operation) and refinement fidelity (this document + G-CONF, G-EQ).
