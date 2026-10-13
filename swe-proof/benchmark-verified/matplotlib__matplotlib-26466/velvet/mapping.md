# mapping.md — matplotlib__matplotlib-26466

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 3dd06a46750d174f821df5377996f493f1af4ebb`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of the modeled sites. Repo file under change:
`lib/matplotlib/text.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `captureCoordA (coords : Array Int)` | `OffsetFrom.__init__(self, artist, ref_coord, unit)` — `lib/matplotlib/text.py:1373` (body line 1392, `self._ref_coord = ref_coord`) | modeled changed function: the coordinate-retaining constructor, site 1 |
| `captureCoordB (coords : Array Int)` | `_AnnotationBase.__init__(self, xy, xycoords, annotation_clip)` — `lib/matplotlib/text.py:1454` (body line 1459, `self.xy = xy`) | modeled changed function: the coordinate-retaining constructor, site 2 |
| `StoredCoord` / `observe` | (no single repo symbol — a deep model of the retention behaviour) | pure spec: how a retained pair behaves when its source container is later mutated (`snapshot` = copied/detached, `reference` = aliased) |

The pre-patch repo behaviour the change removes (refinement audit only, not in
the consumer spec view): both constructors stored the input object itself
(`self._ref_coord = ref_coord` / `self.xy = xy`), so a later in-place mutation
of a mutable input (a numpy array) was observable through the stored attribute.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| a 2-component coordinate (`ref_coord` / `xy`: a `(float, float)` tuple or a length-2 array) | `Array Int` with `size = 2` | `(p, q)` ↔ `#[p, q]`; component 0 ↔ `coords[0]!`, component 1 ↔ `coords[1]!`; `len == 2` ↔ `coords.size = 2` |
| a single coordinate component value | Lean `Int` | identity on the value. **The modeled operation is pure component *copy/identity*** — neither arithmetic nor ordering is performed on the components (the fix only unpacks-and-restores them), so an exact integer carrier is faithful and avoids spurious float concerns (SPEC_GUIDE float rule N/A: no precision-sensitive op). G-CONF feeds integer-valued arrays, which numpy stores exactly. |
| the stored attribute pair (`self._ref_coord` / `self.xy`), read back after the source is mutated | `StoredCoord` + `observe out a b` (with `(a, b)` = the source's later contents) | `snapshot x y` ↔ a detached stored pair (gold/patched); `reference` ↔ the input object retained by alias (pre-patch). `observe` ↔ reading the attribute after mutating the source array to `(a, b)`. |

The copy fix is **order-and-value-preserving on the components**: the patched
code is `x, y = ref_coord; self._ref_coord = x, y` — same two values, same
order, just detached from the source container. So `Int` components with exact
equality fully capture the observable contract.

## 3. Site provenance (the modeled changes — checked by G-CONF, not G-AX)

### 3.1 `captureCoordA` ↔ `OffsetFrom.__init__`
**Repo:** `lib/matplotlib/text.py:1373`. Pre-patch body stores
`self._ref_coord = ref_coord` (the input object, aliased). Post-patch:
`x, y = ref_coord; self._ref_coord = x, y` (a fresh tuple of the two
components — detached). G-CONF constructs the REAL patched `OffsetFrom` from a
numpy array, mutates the array, and reads `of._ref_coord`; it must equal the
capture-time pair (the `snapshot` semantics). The `artist` argument is supplied
as an `IdentityTransform` (a valid `Transform`); `__init__` only stores
`ref_coord`, so the artist kind does not affect the modeled behaviour.

### 3.2 `captureCoordB` ↔ `_AnnotationBase.__init__`
**Repo:** `lib/matplotlib/text.py:1454`. Pre-patch stores `self.xy = xy`
(aliased); post-patch `x, y = xy; self.xy = x, y` (detached). G-CONF constructs
a REAL patched `Annotation` (concrete subclass of `_AnnotationBase`) with
`xy = <numpy array>`, mutates the array, reads `an.xy`; must equal the
capture-time pair.

### 3.3 `OffsetFrom._get_scale` inline — **not modeled** (behaviour-preserving)
The gold patch also deletes `OffsetFrom._get_scale(self, renderer)` and inlines
it into `OffsetFrom.__call__` as `scale = 1 if self._unit == "pixels" else
renderer.points_to_pixels(1)`. This is a pure extract-method-inverse refactor:
`_get_scale` returns `1.` for `"pixels"` and `renderer.points_to_pixels(1.)`
otherwise, called from exactly one site, and the inlined expression computes the
identical value. No observable behaviour changes; the F2P test does not
discriminate it. It is therefore intentionally omitted from `Solution.lean`
(refinement.md §C). No axiom, no method, no G-AX obligation.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`26466`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `captureCoordA`/`captureCoordB` (both pure R/I — there are no
A-tagged callees in either impl region, so `conf_skip = false`) to Python's
`snapshot` semantics, and runs the REAL patched constructors as the oracle
(mutate-source-then-read).

## 5. Axioms — none

This bundle declares zero consumed axioms and zero A-reference deep models of an
unchanged callee. The only modeled behaviour is the *changed* constructors'
copy-on-capture, validated by G-CONF against the real patched code, not by an
axiom (refinement.md §C; `axiom_check.py` asserts the inventory is empty).
