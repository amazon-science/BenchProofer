# mapping.md — matplotlib__matplotlib-26342

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 2aee6ccd7c7e1f8d282c1e7579f4ee546b838542`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance + flag dependencies.

Repo file under change: `lib/matplotlib/collections.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `setPaths (mut coll : PathContainer) (newPaths)` | the path-replacement request handler on the drawable-path container base class `Collection` — `lib/matplotlib/collections.py:209` (`def set_paths`, body filled in post-patch at lines 210–211) | the modeled changed function |
| `PathContainer.paths` | `self._paths` — the stored collection of drawable paths (`lib/matplotlib/collections.py:170` init, `:210` post-patch write) | what a paths query returns |
| `PathContainer.stale` | `self.stale` — the redraw-needed flag (`lib/matplotlib/collections.py:211` post-patch write) | whether the container must be redrawn before next render |
| `getPaths coll` | `Collection.get_paths(self)` → `return self._paths` (`lib/matplotlib/collections.py:206`) | the unchanged paths query, used only to express "stored == supplied" |
| `out : Except Unit Unit` | the success/refusal outcome of the request — `Except.ok ()` ↔ normal return (`None`), `Except.error ()` ↔ a refusal (`raise NotImplementedError`) | the observable that distinguishes the fix from the pre-patch refusal |

The pre-patch repo reality the change fixes (refinement audit only, not in the
consumer spec view): the base `Collection.set_paths` (`collections.py:209`)
was `raise NotImplementedError` — it refused every path-replacement request.
The gold patch fills that body in with `self._paths = paths; self.stale = True`
(mirroring what `PathCollection.set_paths`, `collections.py:1005`, already did),
and removes the now-redundant override on `PathCollection`. `ContourSet`
(`lib/matplotlib/contour.py:706`) subclasses `Collection`, so it inherits the
newly-working `set_paths`; the F2P test exercises `ContourSet.set_paths`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo objects. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `Collection` instance, restricted to path-replacement-relevant state | `PathContainer` | a container `c` ↔ `⟨c.get_paths(), c.stale⟩`. The non-path state of `c` (offsets, transforms, sizes, styling) is invariant under a path-replacement request and is omitted from the carrier. |
| `self._paths` (the stored collection, whatever object) | `PathContainer.paths : List Int` | the supplied collection is stored **wholesale by object identity** — `set_paths` neither inspects nor reshapes its elements. `List Int` is the order-faithful carrier of opaque path identities; G-CONF compares by Python object identity (`get_paths() is supplied`), so the element type is immaterial. |
| `self.stale` (redraw-needed flag) | `PathContainer.stale : Bool` | `True` ↔ `true`, `False` ↔ `false`. |
| outcome of `set_paths` | `out : Except Unit Unit` | a normal return (`None`) ↔ `Except.ok ()`; a refusal (`raise NotImplementedError`) ↔ `Except.error ()`. The fix is exactly the transition error → ok. |
| supplied paths argument | `newPaths : List Int` (read-only, not `mut`) | the `paths` positional argument; stored, never mutated by the op. |
| a path-replacement request `c.set_paths(p)` | running `setPaths` once on the corresponding `coll` with `newPaths = p` | calling `set_paths` once ↔ running `setPaths` once. |

There is no `str`/`List Char` modeling here: the changed behavior is a leaf
state mutation + outcome (refuse → complete), not a string transformation. The
carrier is the minimal observable state a single path-replacement request can
read or affect.

## 3. Callee provenance

### 3.1 No consumed axioms, no A-references (G-AX skips)
The modeled operation is spelled out **directly** over the observable carrier:
`setPaths` *is* "store the supplied collection and mark stale, completing
normally", which is exactly the gold body `self._paths = paths; self.stale =
True` under the §2 bijection. There is therefore:

* **no `axiom` consumed by the proof** (`meta.json` declares zero consumed
  axioms); the proof discharges by `loom_solve` + `simp [getPaths]`;
* **no A-reference deep model of an *unchanged* callee**, and so **no
  `axiom_check.py`** — G-AX correctly skips. Per SPEC_GUIDE §0.7 the function
  the patch changes (`set_paths`) is NEVER axiomatized nor declared an
  A-reference; doing so would (wrongly) demand its *base-commit* behavior match
  the patched model, but at `base_commit` `set_paths` still `raise
  NotImplementedError`. Its fidelity to the gold body is instead enforced by
  **G-CONF** (R/I shadow vs the *patched* `Collection.set_paths`), **G-GOLD**,
  and **G-RESOLVE**. The only callee named in the spec, `get_paths`
  (`collections.py:206`), is the trivial accessor `return self._paths`; it is
  unchanged, modeled by the Lean-side `getPaths` def (not an axiom), and used
  only to phrase the postcondition `getPaths coll = newPaths` (equivalent to
  `coll.paths = newPaths`).

### 3.2 Flag / branch dependency
None. `set_paths` is unconditional — it always stores and always marks stale,
on every container and every supplied collection. There is no boolean guard and
no flag-dependent second behavior. G-CONF therefore fuzzes only the SHAPE of the
supplied collection (length, repeated assignment), not a configuration flag.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`26342`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
the `setPaths` `do` block to Python (store supplied wholesale, set stale True,
return ok) and compares its observable (outcome, the stored object by identity,
and the post `stale` flag) against the real patched `Collection.set_paths`
invoked on a freshly built container, over ≥10⁵ fuzzed supplied collections.
