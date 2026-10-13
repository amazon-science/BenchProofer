# refinement.md — matplotlib__matplotlib-26342

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`setPaths` `do` block) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement; state the bijection), **A-consumed** (proof uses this
axiom's `ensures`), **A-reference** (a deep model validated == the real callee by
G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The path-replacement site — `Collection.set_paths` (`lib/matplotlib/collections.py`)

Gold hunk (the refused body is filled in):
```
     def set_paths(self, paths):
-        raise NotImplementedError
+        self._paths = paths
+        self.stale = True
```
plus the removal of the now-redundant `PathCollection.set_paths` override (which
had the identical body) — see §B.

| # | Solution.lean impl op (`setPaths`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `mut coll : PathContainer` | the `self` (a `Collection` instance) of `set_paths(self, paths)` | R | a `Collection` `c`, restricted to path-replacement-relevant state, ↔ `⟨c.get_paths(), c.stale⟩` (mapping.md §2). Non-path state (offsets, transforms, sizes, styling) is invariant under the op and omitted from the carrier. |
| A2 | parameter `newPaths : List Int` (read-only, not `mut`) | the `paths` positional argument | R | the supplied collection ↔ `List Int` of opaque path identities; stored wholesale by object identity, never inspected or mutated (mapping.md §2). Not `mut`: the op never alters the supplied collection (directive 5). |
| A3 | `coll := { coll with paths := newPaths, stale := true }` | `self._paths = paths` ; `self.stale = True` | R + I | two concrete field assignments. `coll.paths := newPaths` ↔ `self._paths = paths` (store wholesale); `coll.stale := true` ↔ `self.stale = True`. G-CONF transliterates both directly and compares the stored object by identity. |
| A4 | `return Except.ok ()` | implicit normal return (`None`); body no longer raises | R | the **outcome** is the heart of the fix: the request now COMPLETES (`Except.ok ()` ↔ normal `None` return) rather than refusing (`Except.error ()` ↔ `raise NotImplementedError`). G-CONF checks the oracle never raises; G-AX checks the real callee completes normally. |

Postcondition frame: the touched aspects are pinned exactly — `coll.paths =
newPaths` and `coll.stale = true` (A3), `out = Except.ok ()` (A4) — and
`getPaths coll = newPaths` restates the storage observable through the unchanged
query (directive 5 `mut`-frame: no fragment of the mutated post-state is left
unconstrained).

Discriminating content of the change — a path-replacement request now SUCCEEDS,
stores exactly the supplied collection, and marks a redraw — lives in the four
postconditions. The pre-patch reality the change fixes: the base
`Collection.set_paths` was `raise NotImplementedError`, so any container that did
not override it (notably `ContourSet`, which subclasses `Collection`) refused the
request outright. `Solution_prepatch.lean` reproduces that (`return Except.error
()`, no mutation) and **fails** all four clauses (G-DIFF; confirmed: the unsolved
goals are exactly `Except.error () = Except.ok ()`, `collOld.paths = newPaths`,
`getPaths collOld = newPaths`, and `collOld.stale = true`).

## B. The redundant-override removal — `PathCollection.set_paths`

The gold patch also DELETES `PathCollection.set_paths` (`collections.py:1005`),
whose body was byte-identical to the one now installed on the base
`Collection`. This is a pure refactor with NO observable behavioral change:
`PathCollection` continues to expose a `set_paths` with the same body, now
inherited rather than overridden. It introduces no second independently-observable
fixed behavior, so it needs no separate `Solution_prepatch_<k>.lean`. It is not
modeled (it would be the identical `setPaths` method), and it is not a callee the
spec invokes.

## C. No consumed axioms, no A-references, no kind-3 steps

Every step is R or I (A1–A4). The single operation that genuinely *changed* —
the body of `set_paths`, from a refusal to a store-and-refresh — is modeled
**directly** over the observable carrier (the two field assignments + the ok
outcome), not hidden behind an axiom about, or a deep-model reference to, the
function under change. Per SPEC_GUIDE §0.7 the function the patch changes is
NEVER axiomatized nor declared an A-reference: its soundness is enforced by
G-CONF (which runs against the *patched* repo), G-GOLD, and G-RESOLVE, not by
G-AX. There is therefore:

* **no `axiom` consumed by the proof** (`meta.json` declares zero consumed
  axioms); the proof discharges by `loom_solve` + `simp [getPaths]` over the
  spelled-out body.
* **no A-reference** — and so **no `axiom_check.py`**; G-AX correctly *skips*
  (there is no UNCHANGED callee whose internal behavior the proof assumes). The
  only callee named in the spec, the accessor `get_paths`
  (`collections.py:206`, `return self._paths`), is unchanged and trivial — it is
  the identity on `coll.paths`, modeled by the Lean-side `getPaths` def, not an
  axiomatized callee. The changed op's fidelity to the gold body is checked by
  G-CONF (R/I shadow vs the patched `Collection.set_paths` over ≥10⁵ inputs),
  G-GOLD, and G-RESOLVE.

## D. verify(Solution) ⇒ resolved

`setPaths` verifies only if its output completes (`Except.ok ()`, A4), stores
exactly the supplied collection (`coll.paths = newPaths`, A3), and marks the
container stale (`coll.stale = true`, A3), with the supplied collection left
read-only (A2). By R (`Collection` ↔ `PathContainer`, `self._paths` ↔
`coll.paths`, `self.stale` ↔ `coll.stale`, normal return ↔ `Except.ok ()`) the
verified method equals the gold body `self._paths = paths; self.stale = True`
on every container and supplied collection; by G-CONF the R/I transliteration
(store wholesale, mark stale, complete normally) agrees with `patch.diff`'s
behaviour — the real patched `Collection.set_paths` — over ≥10⁵ fuzzed inputs,
and a gold-faithful impl verifies (G-GOLD).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). The F2P
test (`test_contour_set_paths`) replaces a `ContourSet`'s paths with another's
via `cs_test.set_paths(cs_ref.get_paths())` and asserts the figures then render
identically — which requires precisely that `set_paths` stores the supplied
paths and marks a redraw, the observable the verified spec guarantees.
