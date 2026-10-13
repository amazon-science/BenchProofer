# mapping.md — matplotlib__matplotlib-26466

## Instance
- repo: matplotlib/matplotlib
- base_commit: 3dd06a46750d174f821df5377996f493f1af4ebb
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
Two constructors each store a 2D coordinate that is handed in through a mutable
container (a numpy array, in the repo). At base_commit each stores the container
*by reference*:

- `OffsetFrom.__init__` (lib/matplotlib/text.py:1392 @ base_commit):
  `self._ref_coord = ref_coord`
- `_AnnotationBase.__init__` (lib/matplotlib/text.py:1459 @ base_commit):
  `self.xy = xy`

Because the container is shared with the caller and `numpy` arrays are mutable,
a later in-place edit of the caller's array (`xy_0[1] = 3`, or `of_xy[:] = 1` in
the F2P test) silently changes the coordinate already stored on the object — the
symptom in the issue (the arrow/annotation position moves after the call).

The gold patch unpacks the two components and re-stores them as a fresh tuple, so
the stored coordinate is a by-value snapshot taken at construction time and is
decoupled from any later mutation of the source:

```python
# OffsetFrom.__init__
-        self._ref_coord = ref_coord
+        x, y = ref_coord  # Make copy when ref_coord is an array (and check the shape).
+        self._ref_coord = x, y
# _AnnotationBase.__init__
-        self.xy = xy
+        x, y = xy  # Make copy when xy is an array (and check the shape).
+        self.xy = x, y
```

Unpacking `x, y = arr` reads the two scalar elements out of the array into Python
ints/floats; the subsequent tuple `(x, y)` holds those scalar copies, so it no
longer aliases the caller's array.

The same patch also inlines `OffsetFrom._get_scale` into `OffsetFrom.__call__`
(`sc = self._get_scale(renderer)` → `scale = 1 if self._unit == "pixels" else
renderer.points_to_pixels(1)`). That edit is a behaviour-neutral refactor of an
already-correct branch (the returned scale is identical for both `unit` values);
it is NOT the fix and is not modeled. Only the two copy-on-store sites are
modeled, one triple each.

## Modeled behaviour (per site)
The *retention* is modeled directly, so the reference-vs-value distinction lives
in the model rather than being asserted away. A capture produces a `StoredCoord`
— either `snapshot x y` (detached from the source) or `reference` (still bound to
the source) — and reading it back is `observe`:

- `initial : Rat × Rat` — the coordinate value present in the caller's source
  container at the moment the object is constructed (the value `x, y` is read
  from).
- `out : StoredCoord` — the coordinate the object retains after construction.
- `observe out later` — reading the retained coordinate back when the source
  container's CURRENT contents are `later : Rat × Rat` (the caller may have edited
  it in place in between). `observe (snapshot x y) later = (x, y)` (detached);
  `observe reference later = later` (aliased).

Post-patch contract (both sites identical):
`∀ later, observe out later = initial` — reading the retained coordinate back
under EVERY possible later state of the source yields the construction-time
value. Only `snapshot initial.1 initial.2` satisfies this; a `reference` leaks
`later`. This is the bug→fix delta made observable: the universally-quantified
`later` frames the retained pair to the capture-time components for every future
state of the source, which only the copy (`snapshot`) behaviour achieves.
Pre-patch (the bug): the impl returns `reference`, so `observe reference later =
later ≠ initial` in general — the contract fails (G-DIFF).

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_freezeOffsetOrigin` / `problem_spec_freezeOffsetOrigin` / `correct_freezeOffsetOrigin` | `OffsetFrom.__init__` storing `self._ref_coord` (lib/matplotlib/text.py:1373-1393; bug at 1392) |
| `implementation_freezeAnchorPoint` / `problem_spec_freezeAnchorPoint` / `correct_freezeAnchorPoint` | `_AnnotationBase.__init__` storing `self.xy` (lib/matplotlib/text.py:1455-1462; bug at 1459) |

## Type bijection (Lean ↔ Python)
| Lean | Python |
|---|---|
| `Rat × Rat` | a 2D coordinate `(float, float)` — exact rationals stand in for the float components, which are only stored and read back verbatim (no arithmetic on them is modeled) |
| `initial` | the `(arr[0], arr[1])` values at construction time |
| `later` | the `(arr[0], arr[1])` values at the later read time (post-mutation) |
| `StoredCoord.snapshot x y` | the fixed store — a fresh tuple `self.attr = (x, y)` that no longer aliases the source array |
| `StoredCoord.reference` | the buggy store — `self.attr = arr`, the live reference to the caller's array |
| `observe out later` | reading `obj._ref_coord` / `obj.xy` back after the source array has been mutated to `later` |

The "mutable container + later mutation" of numpy arrays is modeled by the
`StoredCoord` retention plus the universally-quantified `later` in `observe`: Lean
values are immutable, so aliasing is made observable by asking, for EVERY possible
later state of the source, what a read of the retained coordinate returns. A
`snapshot` read ignores `later` (the fixed by-value store); a `reference` read
returns it (the by-reference bug).

## Callee provenance / flag deps
None. The capture consumes no unchanged outside callee, so the `axioms` region is
empty and **G-AX skips**. There is no flag dependence (both `OffsetFrom` units and
all `xycoords` go through the same store).

## G-CONF fuzz seed
Pinned seed: **26466** (also recorded in meta.json `verifier_pins.conf_seed`).
