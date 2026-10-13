# mapping.md — matplotlib__matplotlib-26466

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 3dd06a46750d174f821df5377996f493f1af4ebb`, states the type
abstraction, and (there are no axioms) records the callee provenance relevant
to the modelled behaviour.

Repo file under change: `lib/matplotlib/text.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `retain_pair_a(pair)` | `OffsetFrom.__init__` — `lib/matplotlib/text.py:1373` (body line 1392: `self._ref_coord = ref_coord`) | modelled changed construction site #1: retain the supplied (x, y) pair on the instance |
| `retain_pair_b(pair)` | `_AnnotationBase.__init__` — `lib/matplotlib/text.py:1454` (body line 1459: `self.xy = xy`) | modelled changed construction site #2: retain the supplied (x, y) pair on the instance |

The model.py symbols are deliberately site-neutral (`retain_pair_a` /
`retain_pair_b`, parameter `pair`): one of the two repo sites it models
(`OffsetFrom`, the reference-coordinate constructor) is disclosed only in the
instance's non-solver-visible `hints_text`, not in the public
`problem_statement`, so the spec view must NOT name it or echo its repo
identifiers (`OffsetFrom`, `ref_coord`, "reference coordinate"). This mapping
file is provenance (not part of the consumer spec view) and so cites the real
repo symbols for faithfulness.

The two functions return the value that, in the repo, is assigned to the
instance attribute (`self._ref_coord` resp. `self.xy`). The model isolates the
single behaviour the patch changes — *what gets stored* — from the surrounding
constructor bookkeeping (`set_unit`, `xycoords`, `set_annotation_clip`,
`_draggable`), which the patch does not touch.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the `(x, y)` reference coordinate / annotation point (a 2-tuple, list, or **mutable numpy array** of two numeric components) | `List[Slot]` of length 2 | `coord[0] ↔ pair[0]`, `coord[1] ↔ pair[1]`; a 2-element mutable container ↔ a length-2 `List` of storage locations. |
| the **storage cell** each component lives in (an ndarray buffer element, a list element cell, a tuple slot) | `Slot`, one modelled entity per location; `Slot.value` is the component value stored there | The caller's later in-place mutation of an array (`of_xy[:] = 1`) ↔ writing `pair[i].value` after the function returns. This level exists because it is where the tested behaviour lives, see the note below. |
| each numeric component (`float`) | opaque, uninterpreted `object` (a `Slot.value`) | **Pass-through-exact (R-OPQ).** The modelled operation reads the two components out of their locations and re-stores them **without any transformation** (the gold's `x, y = coord; … = x, y` merely rebinds); the tested behaviour is (a) whether the stored pair stays fixed when the caller later mutates the input container and (b) that the stored components are the very values supplied. An opaque carrier with **identity** pins (`Result()[i].value is pair[i].value`) captures exactly that: no arithmetic on the components is even expressible, so a value-lossy transform (e.g. the audit's `x // 1, y // 1` floor-truncation, identity over ints but lossy on real floats like the F2P's `(.5, .5)`) cannot verify. This closes the transform hole the earlier `int` carrier left open (over ints, `x // 1 == x`, so a floor-dividing rival verified while its real patch did not resolve). |
| the instance attribute holding the stored pair (`self._ref_coord` / `self.xy`) | the function's `Result()`: full `list_pred` permission (container owned by the new instance) **and** full `Acc(Result()[i].value)` for each *i* (each retained component's location owned by it) | storing a pair that reads none of the caller's storage ↔ `Result()` freshly allocated at full permission over two locations held at full permission; storing the caller's own container ↔ `Result() is input`; storing anything that still reads the caller's cells (a whole- or per-component **view** of the input) ↔ `Result()[i].value` being the caller's location *i*. All of the latter are forbidden — each would need >1 total permission to something the caller kept a share of (refinement.md §C). |

`numpy`-array iteration/indexing and `str` are banned in Nagini; the carrier is
`List[Slot]` throughout. Aliasing/ownership is carried by Nagini's fractional
permissions at both levels (`list_pred` on the container, `Acc(.value)` on each
location), which is exactly the property the bug violates.

**Why the storage cell is a modelled level and not abstracted away.** On a plain
`List` carrier, "the retained container is a distinct object" and "the retained
components are decoupled from the caller's storage" are the same predicate. On
the repo's real carrier they are not: `ref_coord[0:2]` is a distinct ndarray
object that is a **view** still addressing the caller's buffer, so
`of_xy[:] = 1` is observable through it, and the same is true of a per-component
`ref_coord[0:1]`. A container-only model therefore models the patch's delta away
— and the G-EQ audit exploited precisely that (its rival satisfied every
container clause and both identity pins, verified, and its faithful patch left
the F2P failing). Promoting the location to `Slot` makes the delta observable per
component, and terminates the escape: a `Slot` has no slicing primitive, so there
is no sub-view of a location to hide in.

On identity vs. equality for the components: in the repo the unpacking
`x, y = ref_coord` binds x/y to the objects (or, for a numpy array, fresh
scalar objects carrying the exact values) read from the container, and the
patch stores those bindings untransformed. The model's `is` pin asserts
"the stored location i carries exactly what was read out of input location i,
with no transformation applied in between" — the strongest expressible form of
the gold's pass-through, and the discriminator the hidden F2P actually relies on
(it renders at the exact supplied coordinates).

The pins constrain the *component values*; the two permission levels constrain
*where those values live*, and they are independently load-bearing. A rival that
swaps, drops, or transforms components fails a pin while owning everything; a
rival that reproduces both components exactly but reads them back out of the
caller's cells satisfies both pins and fails the location permissions. Neither
family alone would be caught by the other's clauses, and only the two together
imply what the F2P observes.

Both contracts additionally require `MustTerminate(2)` (totality): the repo
operation is a bounded, loop-free constructor step (`x, y = …; self._… = x, y`)
that always returns, so a faithful model must terminate too. Under Nagini's
partial-correctness default, omitting this let a divergent (`while True`)
implementation verify vacuously while its real patch hangs every constructor
call and fails the hidden tests by timeout (the G-EQ audit's counterexample);
`MustTerminate` closes that hole (refinement.md §C, R-TERM).

## 3. Callee provenance

There are **no `@ContractOnly` axioms** in this bundle (the `axioms` and `pure`
regions are empty) and **no deep-model A-references**. The changed operation is
expressed directly with native Nagini constructs (read two components of the
input, build a fresh length-2 list, return it under full permission). Nothing
repo-specific or stdlib is invoked by the modelled operation, so `axiom_check.py`
has no callee to validate; it documents this and exits 0 (see the file).

For completeness, the gold patch's other hunk — the deletion of the private
`OffsetFrom._get_scale(renderer)` helper and the inlining of its body into
`OffsetFrom.__call__` as `scale = 1 if self._unit == "pixels" else
renderer.points_to_pixels(1)` — is a pure, behaviour-preserving refactor
(`lib/matplotlib/text.py:1410-1415` removed; `:1447-1450` rewritten). It changes
no observable behaviour and is not part of the bug fix the F2P test detects; it
is therefore not modelled (refinement.md row I-REFACTOR).
