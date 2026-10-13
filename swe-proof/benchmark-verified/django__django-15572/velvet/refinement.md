# refinement.md — django__django-15572

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the two `do` blocks `collectConfiguredDirs` / `collectLoaderDirs`, plus the
deep folds `collectConfigured` / `collectLoader`) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (opaque callee —
**A-consumed** where the structure consumes the opaque term, **A-reference**
where a deep model is validated == the real callee by G-AX), or **I** (identical
concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. Site #1 — directly-configured directories (`autoreload.py:20`)

Gold hunk:
```
-        items.update(cwd / to_path(dir) for dir in backend.engine.dirs)
+        items.update(cwd / to_path(dir) for dir in backend.engine.dirs if dir)
```

| # | Solution.lean impl op (`collectConfiguredDirs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `entries : List (List Char)` | `backend.engine.dirs` | R | a list of `str`/`Path` directory entries ↔ `List (List Char)` (mapping.md §2). |
| A2 | `if keepConfigured e` = `decide (e ≠ [])` | the added `if dir` guard | **I** | the discriminating change, modeled DEEPLY: Python truthiness of a directory entry ↔ non-emptiness (mapping.md §2). This is the operation the patch adds. |
| A3 | `[normalizePath e]` for a kept entry | `cwd / to_path(dir)` | **A-consumed** | unchanged per-entry normaliser, opaque free function (mapping.md §3.1). G-CONF runs the same stand-in both sides; nothing asserted ⇒ no G-AX. |
| A4 | `(if … then [normalizePath e] else []) ++ result`, backward `while` fold | the generator expression accumulated by `items.update(...)` | **I** + R | the fold is the per-entry filtered expansion in order (concrete, transliterated by G-CONF); `items.update` into a `set` is R (the list carrier captures membership; dedup/order is set-level, not patched — mapping.md §2). |

## B. Site #2 — loader-supplied directories (`autoreload.py:25-29`)

Gold hunk:
```
             items.update(
                 cwd / to_path(directory)
                 for directory in loader.get_dirs()
-                if not is_django_path(directory)
+                if directory and not is_django_path(directory)
             )
```

| # | Solution.lean impl op (`collectLoaderDirs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | param `entries : List (List Char)` | `loader.get_dirs()` | R | list of `str`/`Path` entries ↔ `List (List Char)`. |
| B2 | `keepLoader e` = `decide (e ≠ []) && (!isFrameworkOwned e)` | `if directory and not is_django_path(directory)` | **I** + **A-consumed** | the added `directory and` is the discriminating change, modeled DEEPLY as `decide (e ≠ [])` (I); `is_django_path(...)` is the unchanged opaque predicate `isFrameworkOwned` (A-consumed, mapping.md §3.2). Emptiness is conjoined FIRST/independently, matching `directory and not …`. |
| B3 | `[normalizePath e]` for a kept entry | `cwd / to_path(directory)` | **A-consumed** | same unchanged normaliser as A3. |
| B4 | filtered backward `while` fold ++ `items.update` | the generator expression | **I** + R | as A4. |

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one behaviour that genuinely *changed* — the
emptiness filter at both sites — is modeled **deeply** (`keepConfigured` /
`keepLoader` and the spelled-out folds `collectConfigured`/`collectLoader`,
tagged I), NOT hidden behind an axiom about a changed callee. The two
A-consumed callees (`normalizePath`, `isFrameworkOwned`) are UNCHANGED by the
patch and are opaque free functions with no asserted contract, so:
- there is **no consumed `_prop` axiom** (nothing asserted) and **no A-reference
  deep model** (the changed thing is the filter, not these callees);
- **G-AX is a skip** — there is nothing to validate against the real callee
  (cf. django__django-12276). An opaque callee with no `ensures` cannot mask a
  wrong impl, because the spec still forces the emptiness-filter structure
  regardless of the callees' values.

## D. Prepatch fails on the discriminating clause (G-DIFF)

`Solution_prepatch.lean` (byte-identical spec) drops the emptiness test at BOTH
sites: site #1 normalises every entry unconditionally; site #2 drops only
framework-owned entries. Against the identical frozen spec each loop leaves the
unsolved goal that an empty entry's contribution `[normalizePath e]` must equal
`(if keep… then [normalizePath e] else [])` — which fails precisely when the
entry is empty (`keep… = false`). This is exactly the
`entries = [] :: es → out = collect… es` clause, and the regression the issue
describes: an empty `DIRS` entry is normalised to the project root and watched,
so `template_changed()` always matches. (Confirmed: prepatch verification fails
at both `collectConfigured` and `collectLoader` loop invariants.)

## E. verify(Solution) ⇒ resolved

Each method verifies only if its output equals the exact per-entry filtered
expansion (A2/B2). By R (`str ↔ List Char`, truthiness ↔ non-emptiness, the
`set` membership carrier) the verified collections equal the patched generator
expressions on the tested inputs; by G-CONF the R/I filter agrees with
`patch.diff`'s behaviour on ≥10⁵ input lists across both sites (seed=15572),
with the opaque callees cancelled on both sides. The F2P test
`test_template_dirs_ignore_empty_path` (DIRS=`[""]` ⇒ `get_template_directories()
== set()`) is exactly the `entries = [""] ⇒ out = []` instance the second
postcondition pins. Therefore an impl satisfying this spec, refined by the map
above, is the gold patch up to type refinement and unchanged opaque callees —
and the gold patch resolves (G-RESOLVE). Trust points: the type bijection
(mapping.md §2) and refinement fidelity (this doc, G-EQ + G-CONF); no axiom
soundness surface (the callees are opaque/free, G-AX skip).

## F. Termination is part of the contract (total correctness)

Both methods are verified under **total correctness**
(`set_option loom.semantics.termination "total"`, `open TotalCorrectness`),
with `decreasing i` on each loop. The real `get_template_directories()`
always terminates (finite generator expressions over finite lists), so a
verified impl must terminate too: a while-loop that never decrements its
index (returning the right value only "after" a divergent loop) does NOT
verify — under total semantics the loop obligations include strict decrease
of the measure, which such an impl cannot discharge. This closes the
partial-correctness loophole where non-terminating impls were admitted
vacuously.
