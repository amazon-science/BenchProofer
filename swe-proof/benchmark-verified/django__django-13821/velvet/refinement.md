# refinement.md — django__django-13821

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the method `verifyVersion`, plus the pure `lexLt` / `requiredVersion` /
`errorMessage` / `checkSpec` models) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement; state the bijection), **A-consumed** /
**A-reference** (none in this bundle), or **I** (identical concrete op). EVERY
step is R or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The version-guard function

Gold hunk:
```
 def check_sqlite_version():
-    if Database.sqlite_version_info < (3, 8, 3):
-        raise ImproperlyConfigured('SQLite 3.8.3 or later is required (found %s).' % Database.sqlite_version)
+    if Database.sqlite_version_info < (3, 9, 0):
+        raise ImproperlyConfigured(
+            'SQLite 3.9.0 or later is required (found %s).' % Database.sqlite_version
+        )
```

| # | Solution.lean impl op (`verifyVersion`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `info : List Nat` | the module global `Database.sqlite_version_info` (a tuple of ints) the guard reads | R | the runtime version-info tuple ↔ `List Nat` (mapping.md §2). G-CONF bridges via `tuple(info)`. The function takes no Python argument — it reads this global; the spec lifts it to a parameter so the behaviour is a total function of its inputs. |
| A2 | param `versionStr : List Char` | the module global `Database.sqlite_version` (a string) interpolated into the message | R | the runtime version string ↔ `List Char` (mapping.md §2); G-CONF bridges via `"".join` / per-char identity. Lifted to a parameter for the same reason as A1. |
| A3 | `tooOld := lexLt info [3, 9, 0]` | `Database.sqlite_version_info < (3, 9, 0)` | I | Python tuple `<` IS the lexicographic strict order `lexLt` models (component-by-component, prefix-below-extension). The literal threshold `[3, 9, 0]` ↔ `(3, 9, 0)` is the **post-patch** minimum — the single value the change raises (from `(3, 8, 3)`). G-CONF transliterates `lexLt` to `tuple(info) < (3, 9, 0)`. |
| A4 | `if tooOld then Except.error (errorMessage versionStr) else Except.ok ()` | `if ...: raise ImproperlyConfigured('SQLite 3.9.0 or later is required (found %s).' % version)` else falls through (returns `None`) | I | the `Except (List Char) Unit` outcome ↔ (raise `ImproperlyConfigured` with that message | no raise) (mapping.md §2). `errorMessage versionStr` IS the `%`-interpolated post-patch diagnostic, modeled deeply as concrete `List Char` concatenation; G-CONF compares the rendered message string verbatim. |

## B. The discriminating content — what the spec senses

The change raises the minimum supported version from `(3, 8, 3)` to `(3, 9, 0)`
(and re-words the diagnostic to name `3.9.0`). The frozen spec pins the outcome
to `checkSpec info versionStr` with `requiredVersion = [3, 9, 0]` and
`errorMessage` naming `3.9.0`. `Solution_prepatch.lean` reproduces the pre-patch
skeleton (threshold `[3, 8, 3]`, message naming `3.8.3`) and **fails**
verification on exactly the clause `out = checkSpec info versionStr` (G-DIFF,
confirmed unsolved goal `ensures_1: out = checkSpec info versionStr`).

The two states diverge precisely on the version tuples that sort in the half-open
interval `[(3,8,3), (3,9,0))` — e.g. the F2P test's `(3, 8, 11, 1)`: the pre-patch
guard does **not** raise (it is `≥ (3,8,3)`) and, where both raise, emits the
`3.8.3` message; the post-patch guard raises with the `3.9.0` message. That is
exactly what `test_check_sqlite_version` observes (it asserts the
`ImproperlyConfigured` message `'SQLite 3.9.0 or later is required (found
3.8.11.1).'` for version `(3, 8, 11, 1)`).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operations that genuinely changed — the comparison
threshold and the diagnostic text — are modeled **deeply** (the `lexLt` order
against the `requiredVersion = [3, 9, 0]` literal, A3; the spelled-out
`errorMessage` concatenation, A4), not hidden behind an axiom about a function
under change. There are **no consumed axioms and no A-references**: the function
under spec (`check_sqlite_version`) calls no unchanged repo callee whose
behaviour the proof relies on — tuple `<` and `%`-formatting are language
primitives, modeled as concrete I-ops and refuted directly by G-CONF. Nothing
requires G-AX validation; `axiom_check.py` is absent and G-AX skips.

## D. verify(Solution) ⇒ resolved

`verifyVersion` verifies only if its outcome equals the exact modeled decision
`checkSpec info versionStr` — raise with the `3.9.0` diagnostic iff the version
sorts below `[3, 9, 0]`, else succeed (A3/A4). By R (the `List Nat` /
`List Char` / `Except` bijections, mapping.md §2) the verified guard equals the
gold-patched `check_sqlite_version` on every (version-info, version-string) the
runtime can present. By G-CONF the R/I transliteration agrees with the patched
`base.py` guard on ≥10⁵ checks (seed 13821, 0 disagreements), including every
boundary across both thresholds and the F2P `(3, 8, 11, 1)`. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The sole trust point is
refinement fidelity (this doc, G-EQ + G-CONF); there are no axioms (G-AX skips).
