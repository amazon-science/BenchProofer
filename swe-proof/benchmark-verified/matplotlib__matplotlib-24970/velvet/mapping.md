# mapping.md — matplotlib__matplotlib-24970

Binds every `Solution.lean` symbol to its repository counterpart, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance + executable-soundness obligation of the axiomatized callee.

REFERENCE TREE for every claim below: `base_commit =
a3011dfd1aaa2487cce8aa7369475533133ef777` **with `patch.diff` applied** — the
tree whose behaviour the spec must describe. Line numbers are given at
`base_commit` (where `patch.diff` moves a line, both positions are named).

Repo file under change: `lib/matplotlib/colors.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolveSlots (paletteSize : Nat) (cells : List Cell)` | the index-resolution block of `Colormap.__call__` — `lib/matplotlib/colors.py:683` (def), body lines `715`–`738` | the modeled changed function: maps each input element to the lookup-table slot that addresses its colour, and hands on the integer container holding those slots |
| `paletteSize` | `self.N` — `lib/matplotlib/colors.py:669` (`self.N = int(N)`) | number of ordinary palette entries; the lookup table has `N + 3` rows |
| `underSlot paletteSize = paletteSize` | `self._i_under = self.N` — `colors.py:673` | reserved slot for inputs below the range |
| `overSlot paletteSize = paletteSize + 1` | `self._i_over = self.N + 1` — `colors.py:674` | reserved slot for inputs above the range |
| `invalidSlot paletteSize = paletteSize + 2` | `self._i_bad = self.N + 2` — `colors.py:675` | reserved slot for invalid (no-value) inputs |
| `Cell` (`inPalette k`/`belowRange`/`aboveRange`/`invalid`) | the *class* of one element of `xa` as the three reserved-marker stores see it — i.e. after the upstream value examination (`colors.py:709`–`726`) AND after the index cast (§2.1) | one already-classified input element. The syntax is WIDER than the classification's image (`inPalette k` is well-formed for every `k`, §2.1 produces only `k ≤ N-1`), and the denotation is faithful on all of it — §2.4 |
| `slotOf` / `slotSeq` *(deep model)* | the per-element resolved-slot VALUES of the assignment block `colors.py:728`–`732`, **in that order** | the per-element slot, and the slot sequence of a whole row (values only). The guard on `inPalette k` is the FIRST store's predicate `xa > self.N - 1`, which also holds of the reserved marker values — §2.4 |
| `IndexRow` *(opaque type)* | the integer **container** the resolved indices live in: the `numpy.ndarray` bound to `xa` when `lut.take(xa, …)` (`colors.py:738`) reads it | the result object of the modeled function. A container is values **plus** the integer width they are stored in, so it is NOT the bare tuple of values; kept abstract for the reason in §2.2 |
| `slotsOf : IndexRow → List Nat` *(opaque read)* | reading the per-element indices out of that array (`xa.tolist()`; equivalently what `lut.take` addresses rows with) | the only observation the model makes of a container. UNCHANGED read, invoked by both twins |
| `rowOf : List Nat → IndexRow` *(axiom)* | the ordinary array construction over index values already in hand — `np.array(values)`, or the input's own array left as it came in | the container an implementation can obtain WITHOUT carrying out any reserved-marker assignment. Records no assignment provenance |
| `slotsOf_rowOf` *(axiom)* | `np.array(values).tolist() == values` | readback of a BUILT container; §3.3 |
| `assignReserved(cells, paletteSize, admitsNegative, carrier)` *(opaque callee — A-consumed)* | the UNCHANGED per-element reserved-marker assignment: the three sequential stores `xa[xa>self.N-1]=_i_over` / `xa[xa<0]=_i_under` / `xa[mask_bad]=_i_bad` (`colors.py:730`–`732`), carried out on the integer container `xa` and yielding that same container for `lut.take` (`colors.py:738`) to read | callee: performs the array reserved-marker assignment and PRODUCES the container it wrote into; well-defined only on a container in which every one of the three selection steps is live — one that admits every reserved index it writes AND represents values below zero (§2.3) |
| `carrier` (the `Nat` argument of `assignReserved`) | the count of NON-NEGATIVE values the container's dtype represents — `int(np.iinfo(xa.dtype).max) + 1` (it admits `0 .. carrier-1`) | how far UP the container reaches; what the three reserved-marker writes need |
| `admitsNegative` (the `Bool` argument of `assignReserved`) | whether the container's dtype represents values below zero at all — `int(np.iinfo(xa.dtype).min) < 0`, i.e. `True` for `int8/16/32/64` and `False` for `uint8/16/32/64` | whether the container reaches BELOW zero; what the below-range selection `xa[xa < 0]` needs to select anything (§2.3) |
| `markersAdmitted(row, paletteSize)` *(opaque predicate on a CONTAINER)* | the capability that the reserved-marker assignment COMPLETED on THIS container (its stores were in-range for the container's integer width) — there is no repo identifier for it; it abstracts the "assignment carried out without an out-of-range scalar conversion" effect | unforgeable capability granted only by a well-defined `assignReserved` — one whose BOTH container obligations hold — and only for the container that assignment produced; required of the result of `resolveSlots` |

The reserved-slot indices come from `Colormap.__init__` (`colors.py:673–675`):
`self._i_under = self.N`, `self._i_over = self.N + 1`, `self._i_bad = self.N + 2`;
and the lookup table has `self.N + 3` rows, so rows `N`, `N+1`, `N+2` are valid
and distinct. `self.N ≥ 0` (`int(N)`, default 256).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4) uses to translate values between the Lean value
domain and the repo types. A wrong entry surfaces as a spurious G-CONF
disagreement.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the input array `X` / `xa` (`np.ndarray`, any numeric dtype) | `cells : List Cell` | the row of input elements ↔ a `List Cell`; `xa.shape[0]`/element count ↔ `cells.length`; element order ↔ list order. Each element is first **classified** (§2.1), and only its class is observable to the slot-assignment step under test. |
| one element of `xa` | one `Cell` | by §2.1 below |
| `self.N` (the palette size, a non-negative int) | `paletteSize : Nat` | `self.N` ↔ `paletteSize`; `self.N ≥ 0` always (`int(N)`), so `Nat` is exact |
| the resolved index **array** `xa` after `colors.py:732` — the object `lut.take(xa, …)` (`colors.py:738`) reads | `out : IndexRow` | the array object ↔ the abstract container; §2.2 says why the carrier is abstract rather than a list |
| the per-element index values readable out of that array (`xa.tolist()`) | `slotsOf out : List Nat` | the assigned slot of each element ↔ the `Nat` at the same position; `lut.take` reads colour `lut[(slotsOf out)[i]]` |
| the NON-NEGATIVE extent of the container the reserved markers are stored into — how far up its dtype reaches | the `carrier : Nat` argument of `assignReserved` (`carrier` admits `0 .. carrier-1`) | `carrier = int(np.iinfo(dtype).max) + 1`: `uint m`-bit ↔ `2**m`, `int m`-bit ↔ `2**(m-1)`. The signed-`int` container the reference produces ↔ a `carrier` larger than every written index (`≥ N+3`), chosen in the impl as `paletteSize + 3`. This extent alone does NOT determine the container — see the next row |
| whether that container represents values BELOW zero | the `admitsNegative : Bool` argument of `assignReserved` | `admitsNegative = (int(np.iinfo(dtype).min) < 0)`: `True` for every signed dtype, `False` for every unsigned one. INDEPENDENT of `carrier`: a `uint16` container (`carrier = 65536`, `admitsNegative = False`) and an `int64` one (`carrier = 2**63`, `admitsNegative = True`) both admit every reserved index, and the below-range selection is live only in the second (§2.3) |
| `with np.errstate(invalid="ignore"): xa = xa.astype(int)` — at `base_commit` `colors.py:727`, INSIDE the `kind == "f"` branch; in the reference tree it stands alone and unconditional immediately before the stores | the carrier-width choice `carrier = paletteSize + 3` at the `assignReserved` call site | the cast yields a container admitting every reserved index `≤ N+2` whatever the input dtype was; modeled by calling the assignment with a carrier whose admitted range exceeds every written index |
| `lut.take(xa, mode='clip')` (`colors.py:738`) | the palette read, downstream of `resolveSlots`; folded into the result it consumes | `mode='clip'` clamps each index into `0 .. len(lut)-1 = N+2`; every resolved slot already lies in that range |

### 2.1 Element classification `Cell` (an R-refinement of the examination + cast)

Classification is not changed by `patch.diff`; what the patch changes is WHERE
the index cast sits, and the cast is upstream of the three stores that read the
class. In the reference tree the sequence is:

1. the unchanged upstream examination (`colors.py:709`–`726`): the bad-mask
   (`np.ma` / `np.isnan`), and — for a float input only — the scaling
   `xa *= self.N`, the clamp `xa[xa<0] = -1`, `xa[xa==N] = N-1`, and
   `np.clip(xa, -1, N, out=xa)`;
2. the index cast `xa = xa.astype(int)`, unconditional (at `base_commit` this
   line is `colors.py:727`, reached only when `xa.dtype.kind == "f"`);
3. the three reserved-marker stores (`colors.py:730`–`732`).

The class of an element is therefore taken on its value **as the stores see it**,
i.e. AFTER the cast, and that is what the table below says:

| element as the reserved-marker stores see it | `Cell` |
|---|---|
| recorded in `mask_bad` (a NaN / masked element), whatever its numeric value | `invalid` |
| otherwise, post-cast value `v` with `0 ≤ v ≤ N-1` | `inPalette v` |
| otherwise, post-cast value `v < 0` | `belowRange` |
| otherwise, post-cast value `v > N-1` | `aboveRange` |

Two consequences worth stating, because a model that classifies on the PRE-cast
value gets them wrong:

* **Truncation.** For a float input the cast truncates toward zero, so
  `0.914 * 6 = 5.49` classifies as the in-range index `5`, not `aboveRange`.
* **Wrapping.** The cast targets the platform `int` (a signed 64-bit integer), so
  an unsigned element that does not fit it wraps to a NEGATIVE value: a
  `uint64` element `≥ 2**63` classifies as `belowRange` and resolves to
  `underSlot`, even though its magnitude is far ABOVE the palette. Measured on
  the reference tree at `N = 6`: `2**63 - 1 → overSlot 7` (fits, still above the
  palette) while `2**63 → underSlot 6`, `2**63 + 1 → underSlot 6`,
  `2**64 - 1 → underSlot 6`. The threshold is exactly the signed maximum, which
  is what makes the post-cast reading the faithful one. `conformance_check.py`
  fuzzes `uint64` and the unclamped dtype extremes so this region is reachable,
  and `axiom_check.check_post_cast_classification` pins it against real numpy
  with the pre-cast reading as the negative control.

`invalid` takes precedence over both range classes because `xa[mask_bad] = _i_bad`
is the LAST of the three stores and overwrites whatever the range stores wrote at
that position.

The stores run in this exact order (`colors.py:728`–`732`): `over → _i_over
(N+1)`, `under → _i_under (N)`, `bad → _i_bad (N+2)`, modeled by `slotOf`.

The order is NOT irrelevant to the resolved value, and §2.4 is the binding that
says so. It matters in one direction: an element's slot is decided by the FIRST
store whose predicate selects it, and the first store's predicate
`xa > self.N - 1` holds of the three reserved marker values themselves. The table
above is faithful because it reads each element's class on the value the stores
see (post-cast) — an element whose post-cast value is `> N-1` is `aboveRange`, and
that is the class the first store acts on. §2.4 states what this forces about the
syntactically wider `inPalette k`.

### 2.2 Why the result carrier is a CONTAINER and not its index values

The behaviour the F2P observes is NOT the resolved slot *value*. Those values are
byte-identical in both trees: each class resolves to the same slot either way.
The slot-assignment block (`colors.py:730–732`) writes the three reserved marker
scalars `_i_over=N+1`, `_i_under=N`, `_i_bad=N+2` into `xa`, and numpy evaluates
the scalar RHS conversion on EVERY call **regardless of whether the mask selects
any element** — so a narrow `xa` is reported even for an EMPTY or wholly-in-range
input. The discriminating behaviour is whether the container the markers are
written into ADMITS them, **independently of the input contents**: the
completing-assignment effect, modeled as the unforgeable `markersAdmitted`
capability that the gated callee grants ONLY under `paletteSize + 3 ≤ carrier`.

That effect is a property of the CONTAINER, so the modeled result has to be one.
Two arrays can read back the same indices in different integer widths — in this
very function, the resolved values of the input's own narrow array and of the
cast wide array coincide — and only one of them admitted the markers. A result
type of `List Nat` cannot tell them apart: index values are the only thing such a
result carries, so a capability stated over them transfers to any value-equal
list, and an implementation that carries out the admitting assignment and then
hands on an array it BUILT from the index values satisfies the same
postconditions as one that hands on the array the assignment wrote into. That
implementation is precisely the behaviour under repair (the palette read receives
the narrow container), so the model keeps `IndexRow` opaque and observes it only
through `slotsOf`. `rowOf` (build from values) and `assignReserved` (carry out
the assignment, and grant the capability for the container it produced) are kept
apart for the same reason: building a container is available to any
implementation and says nothing about any assignment having completed.

### 2.3 Why SIGNEDNESS is a second, independent observable of the container

The three reserved-marker stores are not one operation but three *selections*,
and they do not all select on the same end of the container:

```python
xa[xa > self.N - 1] = self._i_over      # colors.py:730  — selects ABOVE the palette
xa[xa < 0]          = self._i_under     # colors.py:731  — selects BELOW zero
xa[mask_bad]        = self._i_bad       # colors.py:732  — selects on the bad mask
```

`colors.py:731` is a predicate on NEGATIVE values. In a container whose dtype
represents nothing below zero, `xa < 0` is false at every position, so that store
selects NOTHING — and because it runs SECOND, every element that should have
resolved to `underSlot` keeps the `overSlot` that `colors.py:730` already wrote
there (a below-range element is, in an unsigned container, a large positive one,
so `colors.py:730` does select it). The readback of the produced container is then
`overSlot` where `slotSeq` says `underSlot`.

That divergence is invisible to the container's non-negative extent. Measured on
real numpy at `N = 256` with `X = [-inf, -1, 0, nan, .7, 2, inf]`:

| container | readback |
|---|---|
| signed `int` (the reference tree's cast target) | `[256 256 0 258 179 257 257]` |
| `uint16` (`carrier = 65536`, admits every reserved index) | `[257 257 0 258 179 257 257]` |

Both containers admit every reserved index the assignment writes, so both satisfy
`paletteSize + 3 ≤ carrier`; they differ only in whether they reach below zero,
and they resolve the three below-range elements differently. So `carrier` and
`admitsNegative` are independent observables and the model has to carry both:
`assignReserved` takes both, and its contract requires both
(`admitsNegative = true` and `paletteSize + 3 ≤ carrier`). The first is required
for the SOUNDNESS of the contract's readback claim, not for convenience: on an
unsigned container the claim `slotsOf r = slotSeq paletteSize cells` is false, as
the table shows.

The reference tree makes both properties hold in one step — `xa.astype(int)`
targets the platform signed `int`, which both reaches below zero and admits every
reserved index — which is why a one-extent model could describe the reference
correctly while still admitting a rival the reference is not.

**What an admitting carrier refines to, and what it does not.** The two
obligations constrain the container the ASSIGNMENT runs in, and NOTHING else. They
do not single out the platform signed `int`, and an earlier revision of this
section over-claimed that they do. A narrower signed dtype can satisfy both:
`int16` at `N = 256` has `carrier = 32768 ≥ 259` and represents values below zero,
and it agrees with the platform `int` on the ENTIRE float-valued path, because the
upstream clamp and `np.clip(xa, -1, N, out=xa)` (`colors.py:709`–`726`) leave every
float-derived value inside `-1 .. N`. So the obligations are exactly the two
selection boundaries — the point at which the below-range selection becomes live,
and the point at which the largest reserved marker first fits — and the model
claims no more than that.

Where a narrower container does separate is on integer-dtype input, whose values
the float path's clamp never touches: at `N = 256`, `int16` resolves
`[100000, 40000, 32768]` to `[256, 256, 256]` (each value wraps NEGATIVE in that
width, so the below-range selection takes it) where the platform `int` gives
`[257, 257, 257]`. That divergence is a RE-CLASSIFICATION — it changes the input
`cells` (§2.1), not the container the assignment runs in — so it is upstream of
the modeled function and outside what these two obligations can or should say.
`axiom_check.check_carrier_refinement_scope` measures both halves: the agreement
on the float path and the separation on the integer path.

**Why the earlier framings failed.** (i) An earlier `slotOf … % paletteSize`
"fold" model asserted a slot-VALUE distinction that never occurs — a
counterfactual. (ii)–(iii) Later framings returned an explicit `out.capacity`
constant; the discriminator was a value the impl returns by fiat, so an impl
performing NO widening but returning a large `capacity` verified while still
leaving the markers unrepresentable. (iv) The framing before this one made
`markersAdmitted` a predicate on the resolved index VALUES (`out : List Nat`):
unforgeable, but transferable by value equality, which is the launder described
above. (v) The framing before THIS one described a container by the single `Nat`
`carrier`, i.e. by its non-negative extent alone: sound for the reference, but it
let an unsigned container of any sufficient width discharge the whole
precondition, and in such a container the below-range selection is dead (§2.3).
The current model closes all five: the capability is granted only by the gated
`assignReserved`, whose TWO-part precondition `admitsNegative = true` and
`paletteSize + 3 ≤ carrier` — one obligation per selection end — is discharged at
the call site, and it is held by the CONTAINER that call produced.

### 2.4 SELECTION ORDER — what an ordinary index resolves to, and why `slotOf` guards it

`Cell` is a WIDER syntax than the image of the classification. `inPalette k` is
well-formed for every `k : Nat`, while §2.1 only ever produces `inPalette v` with
`0 ≤ v ≤ N-1`. The denotation `slotOf` must therefore be faithful on the WHOLE
syntax, not merely on that image, and for a concrete reason rather than a stylistic
one: the classified row is an INPUT of the modeled function (`cells`), so an
implementation is free to hand the reserved-marker assignment a row containing
elements outside the image, and whatever the model says such an element resolves to
is a claim about the repository that has to be true.

The three stores are three SELECTIONS over one container, run in a fixed order:

```python
xa[xa > self.N - 1] = self._i_over      # colors.py:730  — FIRST
xa[xa < 0]          = self._i_under     # colors.py:731
xa[mask_bad]        = self._i_bad       # colors.py:732
```

The first predicate is `xa > self.N - 1`, and it holds of the three reserved
marker VALUES `N`, `N+1`, `N+2` exactly as it holds of any other out-of-range-high
index. So an element arriving at this block with an index `≥ N` does NOT keep that
index: the first selection takes it and stores `_i_over = N+1` over it, and no
later selection takes it back (`xa < 0` is false of a non-negative index, and it is
in `mask_bad` only if it was invalid to begin with, which is a different class).
First selection wins. Hence the binding

```lean
slotOf paletteSize (.inPalette k) = if k < paletteSize then k else overSlot paletteSize
```

— an ordinary index keeps the value it carries only while that value is strictly
inside the palette, and outside it describes exactly what `aboveRange` describes.

Two consequences the spec depends on:

* **`underSlot` and `invalidSlot` are reachable from their own class and from
  nowhere else.** No index value resolves to either: below `N` an index resolves to
  itself, and at or above `N` the first selection sends it to `overSlot`. That is
  what makes the resolved-slot sequence informative about WHICH end an element came
  from, and it is stated in `Solution.lean` as `slotOf_inPalette_ne_underSlot` /
  `slotOf_inPalette_ne_invalidSlot`.
* **The resolution is injective on classes, so the row cannot be re-spelled.** An
  earlier revision read `.inPalette k ↦ k` for every `k`, which made `.belowRange`
  and `.inPalette N` resolve to the same slot (likewise `.invalid` and
  `.inPalette (N+2)`). Because `cells` is unconstrained, an implementation could
  then rewrite the row along that collision before the gated call and satisfy every
  clause of the specification while its repository counterpart changed observable
  colours — measured on the official harness at PASS_TO_PASS 81 pass / 172 fail
  (below-range rewrite) and 82 / 171 (invalid rewrite).

**Why the wider syntax is KEPT rather than excluded by a precondition.** A
precondition `k < paletteSize` on every element, or a postcondition demanding the
row be handed on unrewritten, would also reject a CORRECT implementation: the third
rewrite of the same shape, `.aboveRange ↦ .inPalette (overSlot paletteSize)`,
resolves 253/253 on the official harness, precisely because the selection that
would take the rewritten element is the one that runs first. The repository
identifies those two situations, so the model must identify them too. Excluding the
out-of-image syntax would make the specification stronger than the behaviour it
describes; giving that syntax its true denotation does not.

**Soundness check (G-AX).** `axiom_check.check_selection_order_dominance`
reproduces the cast and the three stores in numpy alone and asserts, for
`N ∈ {1, 6, 256}` and indices sweeping `{0, 1, N-1, N, N+1, N+2, N+7, 2N}`, that
the shipped reading of `slotOf` matches the real per-element slots while the
identity reading DISAGREES (at `N = 256` the input `[256, 257, 258]` resolves to
`[257, 257, 257]`, not to itself). `axiom_check.check_row_rewrite_divergence_witness`
measures the end-to-end consequence at `N = 256` on
`X = [-inf, -1, 0, nan, .7, 2, inf]`: the reference resolves
`[256, 256, 0, 258, 179, 257, 257]`; the below-range rewrite gives
`[257, 257, 0, 258, 179, 257, 257]` and the invalid rewrite
`[256, 256, 0, 257, 179, 257, 257]` (both DIVERGE), while the `aboveRange` rewrite
AGREES — the three measurements that pin this section from both sides.

## 3. Axiom provenance + soundness

`assignReserved` is the only axiomatized **callee**, and it is **A-consumed** (the
proof of `resolveSlots` uses its contract — the produced container's readback AND
the `markersAdmitted` capability). It models the UNCHANGED numpy reserved-marker
assignment; it is NOT the function under change. `markersAdmitted` and `slotsOf`
are `opaque`, so no implementation can fabricate a capability or redefine the
read; `rowOf` is an `axiom` (a total function into an opaque type) with one
readback fact, §3.3.

`#print axioms resolveSlots_correct = [assignReserved_contract, propext, rowOf,
Classical.choice, Quot.sound]` — no `sorryAx`. The two bundle-specific
assumptions are `assignReserved_contract` (§3.1–3.2) and `slotsOf_rowOf` (§3.3;
it does not appear in the list because the frozen impl does not build a
container — the reject lane of `properties.py` does). Both are validated against
real numpy by `axiom_check.py` (G-AX), which imports only the standard library +
`numpy` and exits 0 iff sound.

### 3.1 LEGALITY PRECONDITION — `paletteSize + 3 ≤ carrier`
The largest reserved index written is `N+2`; an integer container admits it iff
its representable maximum is `≥ N+2`, i.e. (for a container admitting
`0..carrier-1`) `carrier-1 ≥ N+2`, i.e. `carrier ≥ N+3`. This is exactly the
condition under which the reserved-marker stores complete WITHOUT an out-of-range
scalar conversion — i.e. without numpy's out-of-bound-integer warning, which
matplotlib's pytest configuration promotes to the F2P failure. The conversion is
evaluated regardless of whether any element matches the mask, so it is reported
even for the unmasked value-0 F2P input.

`axiom_check.check_legality_precondition` asserts, against real numpy, that
across `uint8/uint16/uint32/uint64/int8/int16/int32/int64` and `N` sweeping the
threshold: the reserved-marker store on the F2P-shaped input (value 0, unmasked)
emits the out-of-bound report **iff** the largest reserved index does NOT fit the
container — i.e. "no report" coincides EXACTLY with `paletteSize + 3 ≤ carrier`.
So the precondition is neither too strong (no admitting width is excluded) nor
too weak (every excluded width really reports). `axiom_check.check_f2p_witness`
pins the exact F2P case: uint8, `N=256` (`carrier 256 < 259`) reports on the
marker store while a widened container does not, values unchanged (slot 0).

### 3.2 RESULT — the container produced, its readback, and the capability
On a well-defined assignment the produced container reads back
`slotSeq paletteSize cells` (each element's slot is `slotOf` of its class) and
carries `markersAdmitted … paletteSize`. The readback half is the unchanged
per-element resolution, refuted by G-CONF (§4) against the real patched
`Colormap.__call__` (slot recovered from output RGBA) on ≥10⁵ inputs. The
capability half is checked by G-CONF's carrier-legality leg (the marker writes
are legal on the real reference tree, with the pre-patch tree as the negative
control) and by `axiom_check` §3.1.

Note what the contract does NOT say: it pins the readback of the container it
PRODUCED, and nothing about any other container that happens to read back the
same indices. That asymmetry is the point of §2.2.

### 3.3 BUILT CONTAINER — `slotsOf (rowOf vs) = vs`, and nothing else
`rowOf` is the ordinary array construction over index values already in hand, and
the single fact in scope about it is that reading it back yields those values:
`np.array(values).tolist() == values`. Building a container is available to any
implementation and carries out no assignment, so it grants no capability.

**Soundness check (G-AX):** `axiom_check.check_container_readback` builds arrays
of index values across integer dtypes and asserts the readback is exact.
`axiom_check.check_provenance_not_readable` is the load-bearing half: it exhibits
two containers with IDENTICAL readback values — one narrow (the input's own
`uint8` array), one wide (the same values after the cast) — whose marker-store
legality DIFFERS, so the readback values do not determine the capability and
`markersAdmitted` cannot soundly be stated over them. That is the executable form
of §2.2.

### 3.4 POST-CAST CLASSIFICATION — §2.1's faithfulness
`axiom_check.check_post_cast_classification` reproduces, in numpy alone, the cast
followed by the three stores, and asserts that the resulting per-element slots
equal `slotOf` of the class taken on the POST-cast value, across integer dtypes
including `uint64` at and around `2**63`. The PRE-cast reading is run as a
negative control and must DISAGREE there (it reports `overSlot` where the stores
produce `underSlot`), so the check is load-bearing rather than decorative.

### 3.5 SELECTION ORDER — §2.4's faithfulness
`axiom_check.check_selection_order_dominance` and
`axiom_check.check_row_rewrite_divergence_witness` validate the guard on
`slotOf (.inPalette k)`: the first is a per-element sweep with the identity reading
as the negative control, the second an end-to-end row measurement showing that the
two collisions the earlier reading permitted really change resolved slots while the
one identification it keeps really does not. Measurements are quoted in §2.4.
`axiom_check.check_carrier_refinement_scope` bounds what §2.3's two obligations
claim (agreement of a narrower admitting container on the float path, separation
only on integer input).

## 4. G-CONF fuzz seed (pinned for deterministic eval)

`conformance_check.py` seeds its `random.Random` with **`24970`** so the
consumer-side verdict is reproducible. It builds the R/I shadow of the
`resolveSlots` slot values in Python (the classification of §2.1 — including the
unconditional index cast — then the `slotOf`/`slotSeq` ops, R/I-tagged), bridges
`Cell`↔element and `slotsOf out`↔resolved-index-array via §2, and
differential-tests it against the reference behaviour — the real
`Colormap.__call__` index resolution at `base_commit` with `patch.diff` applied —
over the boundary cases (the `uint8`/`int`/`float16`/`float` F2P matrix, empty
arrays, out-of-range / NaN elements, the per-dtype integer EXTREMES for
`uint8/uint16/uint32/uint64/int8/int16/int32/int64`, and the `uint64` signed
threshold `2**63 - 2 … 2**64 - 1`) plus ≥10⁵ fuzzed rows whose integer values are
drawn from each dtype's own full range rather than a clamped window. It
additionally runs the discriminating marker-write carrier-legality leg (the
precondition the `markersAdmitted` capability abstracts) on the real reference
tree (N=256 viridis, empty uint8 input emits no out-of-bound report ⇒ the
container admits the markers), with the pre-patch tree as the negative control.
