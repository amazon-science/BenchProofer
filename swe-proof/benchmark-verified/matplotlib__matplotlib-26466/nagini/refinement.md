# refinement.md — matplotlib__matplotlib-26466

The operation-by-operation correspondence between `model.py`'s implementation
(the two construction-site functions `retain_pair_a` and
`retain_pair_b`) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A-consumed** / **A-reference** (axiomatized
callee — none here), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. Site #1 — `OffsetFrom.__init__` (`lib/matplotlib/text.py:1392`)

Gold hunk:
```
-        self._ref_coord = ref_coord
+        x, y = ref_coord  # Make copy when ref_coord is an array (and check the shape).
+        self._ref_coord = x, y
```

| # | model.py impl op (`retain_pair_a`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `pair: List[Slot]`, `len(pair) == 2` | `ref_coord` (a 2-component coordinate; tuple/list/array) | R | a 2-element coordinate container ↔ a length-2 `List[Slot]`, entry *i* being the storage LOCATION holding component *i* (mapping.md §2). `len == 2` ↔ the implicit "exactly two components" the unpacking `x, y = ref_coord` requires (and which the comment notes also "checks the shape"). |
| A2 | `given0 = pair[0]`; `x = given0.value`; `given1 = pair[1]`; `y = given1.value` | `x, y = ref_coord` | R | tuple-unpacking ↔ reading the component value OUT of each of the two locations. Identical data flow; only the carrier is refined. Reading `.value` is the modelled counterpart of the unpacking actually producing a value (for an ndarray, a fresh scalar object) rather than a further reference into the caller's buffer (mapping.md §2). |
| A3 | `kept0 = Slot(x)`; `kept1 = Slot(y)`; `retained = [kept0, kept1]`; `return retained` (fresh `List` at full `list_pred`, each element a fresh location at full `Acc(.value)`) | `self._ref_coord = x, y` (a fresh 2-tuple bound from the unpacked locals) | R + I | building a fresh ordered pair from the two read components ↔ allocating two fresh locations and the result list over them. The freshly-built `(x, y)` tuple is a NEW object whose two slots are the tuple's OWN — decoupled from `ref_coord` at both levels; the model's fresh `Result()` at full container permission with full permission to each `Result()[i].value` is that same two-level decoupling (R-OWN below). Returning the value that the repo assigns to `self._ref_coord` is the I correspondence (model `Result()` ↔ stored attribute). |
| R-OPQ | component values modelled as opaque, uninterpreted `object`s, pinned by IDENTITY (`Result()[i] is pair[i]`) | `float` components, stored untransformed by the pass-through `x, y = …; … = x, y` | R | the gold reads the two components and re-stores them with NO transformation; the identity pin is the strongest expressible form of that pass-through. An earlier `int` carrier admitted transforms that are the identity over ints but lossy over the repo's real floats — the G-EQ audit exploited exactly this with `x // 1, y // 1` (verifies over int; its real patch truncates the F2P's `(.5, .5)` and does not resolve). On the opaque carrier no arithmetic on the components is expressible and only carrying the SAME objects through satisfies `is`, so every transform rival is rejected (mapping.md §2). |

## B. Site #2 — `_AnnotationBase.__init__` (`lib/matplotlib/text.py:1459`)

Gold hunk:
```
-        self.xy = xy
+        x, y = xy  # Make copy when xy is an array (and check the shape).
+        self.xy = x, y
```

| # | model.py impl op (`retain_pair_b`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `pair: List[Slot]`, `len(pair) == 2` | `xy` (a 2-component point) | R | identical to A1. |
| B2 | `given0 = pair[0]`; `x = given0.value`; `given1 = pair[1]`; `y = given1.value` | `x, y = xy` | R | identical to A2. |
| B3 | `kept0 = Slot(x)`; `kept1 = Slot(y)`; `retained = [kept0, kept1]`; `return retained` | `self.xy = x, y` | R + I | identical to A3. |

## C. The ownership / no-aliasing correspondence (R-OWN, the heart)

The single behaviour the patch changes at both sites is **share → read out**:
pre-patch stores something that still reads the caller's storage
(`self._ref_coord = ref_coord` / `self.xy = xy`); post-patch reads each component
OUT of that storage and stores those (`x, y = …; self._… = x, y`).

### C.0 Why ownership must be modelled PER COMPONENT, not per container

The obligation is stated at **two carrier levels**, because at one level it is
unsound. `pair` is a length-2 `List[Slot]` in which entry *i* is the storage
LOCATION holding component *i*, and `Slot.value` is the component value there
(mapping.md §2).

An earlier version of this spec modelled only the container (`List[object]`, one
permission level) and claimed that "the retained container is a distinct object"
captured the fix. **It does not, and the G-EQ audit refuted it.** On a plain
`List` the two predicates

  (i) the retained container is a distinct Python object, and
  (ii) the retained components are decoupled from the caller's storage

coincide, so a container-only spec looks adequate. On the repo's real carrier —
a **mutable `ndarray`** — they come apart: `ref_coord[0:2]` is a distinct
ndarray OBJECT that is a **view** still addressing the caller's buffer
(`view.base is ref_coord`), so `of_xy[:] = 1` is observable through it. The
audit's counterexample was exactly that: it satisfied every container-level
clause and every identity pin, verified, and its faithful real patch left the
F2P failing (1/1 F2P fail, 100/100 P2P pass — a `verify`-but-not-`resolve`
break). Object-distinctness certifies the wrong thing; **decoupling of storage**
is the property, and it is per component.

So the location is promoted to a modelled entity, which makes the patch's delta
observable where the container-only carrier had modelled it away. Note the
recursion terminates here: a `Slot` has no slicing/viewing primitive, so there
is no "sub-view of a location" to escape into. (A nested
`List[List[object]]` carrier does NOT work for the same reason the flat one does
not — `a[0:1]` is still an aliasing view one level down.)

### C.1 The clauses

- The input container is required and ensured at `Acc(list_pred(pair), 1/2)` —
  the caller keeps half the permission, i.e. continues to own and may mutate it
  after the call (directive 5).
- **Each input component LOCATION** is required and ensured at
  `Acc(pair[i].value, 1/2)` — the caller goes on owning that location and may
  overwrite it IN PLACE after the call. This is the direct mirror of the test
  mutating `of_xy[:] = 1` / `an_xy[:] = 2` after `annotate`/`OffsetFrom` returns:
  the mutation writes the caller's component cells, not the container binding.
- The retained container is ensured at full `Acc(list_pred(Result()))` — owned
  by the new instance. Jointly with the caller's 1/2 share this is satisfiable
  **only if `Result()` is a distinct object** from the input: an alias would
  demand `1/2 (caller) + 1 (instance) = 3/2 > 1` total permission to one object.
  Hence `model_prepatch.py` (site #1 → `return pair`) and `model_prepatch_2.py`
  (site #2 → `return pair`) each FAIL on `insufficient permission to access
  list_pred(Result())` — the spec sensing the share (G-DIFF), one failing variant
  per independently-fixed site.
- **Each retained component LOCATION** is ensured at full
  `Acc(Result()[i].value)` — the retained pair's component *i* lives in storage
  the constructed object owns outright. Jointly with the caller's retained
  `Acc(pair[i].value, 1/2)` this is satisfiable **only if the retained location
  is not the caller's location** *i*. This is the clause the container-level
  spec lacked, and it is what rejects the audit's counterexample class: a
  genuinely fresh container filled with the caller's own component locations
  satisfies every container clause and both identity pins, yet is rejected here
  (`3/2 > 1` on that location). It also rejects, with no distinctness
  precondition and hence no narrowing of the modelled domain, the degenerate
  case where the retained pair's two components are ONE location (the two full
  permissions coincide, so the retained pair could not hold two independent
  components).

Together: the retained pair owns its container AND both locations its components
live in, so none of the storage it reads back from is storage the caller can
still write; and the caller kept all of its own. That conjunction, not
object-distinctness, is what the F2P observes. The gold `x, y = ref_coord`
performs exactly the read-out that establishes it (for an ndarray the unpacking
yields fresh scalar objects; the stored tuple's slots are the tuple's own), while
the pre-patch assignment and every share-the-caller's-storage arrangement do not.

The identity clauses `Result()[i].value is pair[i].value`, `len(Result()) == 2`
pin that the retained pair carries the right two components in order and
UNTRANSFORMED (so both a "fresh but wrong/empty pair" cheat and a "fresh but
transformed components" cheat, R-OPQ, are rejected), grounded entirely in the
input (directive 8) — no oracle. The permission clauses and the identity clauses
are independently load-bearing: the swap/duplicate rivals are fully owned at both
levels and fail only the pins, while the share-storage rivals satisfy both pins
and fail only the permissions (properties.py records one reject case per class).

### Totality (R-TERM)

Both contracts carry `Requires(MustTerminate(2))`: the construction-time
retention is a bounded, loop-free step in the repo (`x, y = …; self._… = x, y`
— no loop, no recursion), so it must terminate. This is a total-correctness
obligation, not merely partial correctness. Without it, an implementation that
diverges (e.g. inserts an unconditional `while True:` loop before the
retention) satisfies every value and permission postcondition **vacuously**
under Nagini's partial-correctness default — the G-EQ audit built exactly that
counterexample: it verified against the old spec, but its faithful real patch
hangs every `OffsetFrom(...)`/`annotate(...)` constructor call, the F2P suite
times out (300 s guillotine), and the patch does NOT resolve. With
`MustTerminate(2)` the diverging body cannot discharge the caller's
termination obligation (obligation-leak check), so that rival is rejected
(properties.py cases `weak-diverge-no-terminate-a/-b`). The gold-faithful
loop-free impl discharges the obligation trivially.

## D. The other gold hunk — `_get_scale` inlining (not modelled)

| # | repo change | tag | justification |
|---|---|---|---|
| I-REFACTOR | delete `OffsetFrom._get_scale(renderer)` (`text.py:1410-1415`) and inline it into `OffsetFrom.__call__` as `scale = 1 if self._unit == "pixels" else renderer.points_to_pixels(1)` (rewrite of `text.py:1447-1450`) | I (behaviour-preserving refactor) | `_get_scale` returned `1.` for `"pixels"` else `renderer.points_to_pixels(1.)`; the inlined expression computes the identical value (`1` vs `1.` and `points_to_pixels(1)` vs `points_to_pixels(1.)` are numerically equal). It changes no observable output and is not what the F2P test detects (the test checks the copy behaviour, not the scale). Therefore it is not modelled; it carries no verification obligation. Included verbatim in `patch.diff` only because it is part of the gold commit. |

## E. No kind-3 (unexpressible-changed-op) steps; no axioms

Every modelled step above is R or I. The changed operation — reading each
component out of the caller's storage instead of retaining something that still
reads it — is expressed **directly** in Nagini (read the value out of each of the
two input locations, build a fresh length-2 list over two fresh locations, return
it with full permission to the container and to each retained location, while
keeping the input container and both input locations read-only), so there is no
`@ContractOnly` axiom and no A-reference deep model. `axiom_check.py` therefore
has nothing to validate against a real callee and trivially exits 0.

## F. verify(model) ⇒ resolved

Each function verifies only if it terminates (R-TERM) and returns a length-2 pair
that is fully owned AT BOTH LEVELS — a distinct container, and two distinct
locations neither of which the caller still holds a share of (C, C.0) — carrying
the input's two components in order, untransformed (C, R-OPQ). By R (2-element
container ↔ `List[Slot]`, component storage cell ↔ `Slot`, `float` component ↔
opaque object under identity pass-through, unpacking ↔ reading `.value` out of
each location, fresh tuple with its own slots ↔ fresh list of fresh locations at
full permission) the verified functions equal the gold hunks' stored values and
their decoupling-from-caller's-storage property at both sites. Crucially the
converse direction now holds too, which it did not under the container-only
carrier: an implementation that verifies cannot retain anything that still reads
the caller's component storage, so the F2P's post-construction in-place overwrite
cannot move what it stored. The gold patch additionally
performs the behaviour-preserving `_get_scale` inline (D), which does not change
the resolved verdict. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement on the bug-fix hunks — and the
gold patch resolves (G-RESOLVE). There are no axioms, so the only trust point of
PLAN §1.1 in play is refinement fidelity (this document, G-EQ).
