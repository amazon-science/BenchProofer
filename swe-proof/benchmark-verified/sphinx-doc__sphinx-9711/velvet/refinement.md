# refinement.md — sphinx-doc__sphinx-9711

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`anyRequirementUnmet` `do` block, the deep `verGt`/`unmet`/`anyUnmet` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement), **A**
(axiomatized callee — **A-consumed** where the proof uses an axiom's `ensures`,
**A-reference** where a deep model is validated == the real callee by G-AX), or
**I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The comparison site — `verify_needs_extensions()` (`sphinx/extension.py:54`)

Gold hunk (semantics):
```
-        if extension.version == 'unknown version' or reqversion > extension.version:
+        fulfilled = True
+        if extension.version == 'unknown version':
+            fulfilled = False
+        else:
+            try:
+                if Version(reqversion) > Version(extension.version):
+                    fulfilled = False
+            except InvalidVersion:
+                if reqversion > extension.version:
+                    fulfilled = False
+
+        if not fulfilled:
             raise VersionRequirementError(...)
```
(plus `from packaging.version import InvalidVersion, Version` at the import head.)

| # | Solution.lean impl op (`anyRequirementUnmet`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `reqs : List Requirement` | the `for extname, reqversion in config.needs_extensions.items()` items, paired with `app.extensions.get(extname)` | R | dict-of-requirements ↔ `List Requirement` (mapping.md §2); order-insensitive because the observable is the disjunction. |
| A2 | the backward `while` loop folding `acc := unmet r \|\| acc`, result `acc = anyUnmet reqs` | the `for` loop that, across iterations, raises iff some item is unmet | I | the loop is the concrete disjunctive scan; G-CONF transliterates it. The model returns the boolean; the real function turns `true` into `raise VersionRequirementError` (R, A4). |
| A3 | `unmet r` = `if !isPresent then false else if !isKnown then true else verGt required present` | the per-iteration test: absent ⇒ `continue` (skip, warn); `unknown version` ⇒ unmet; else `Version(reqversion) > Version(extension.version)` | A-reference + I | the `isPresent`/`isKnown` guards are concrete (I), transliterated by G-CONF; the version comparison `verGt` is the **deep model** of `Version(reqversion) > Version(extension.version)` (A-reference, validated == real `packaging.Version` compare by G-AX, mapping.md §3.1). No consumed axiom. |
| A4 | result `raised : Bool` | `if not fulfilled: raise VersionRequirementError(...)` | R | mapping.md §2: the function raises iff the scan finds an unmet requirement; G-CONF observes "real patched function raised?" against the shadow boolean. |

Discriminating content of the change — the version comparison is **numeric**, not
**textual**: `verGt "3.9" "3.10" = false` (model) ⇔ `Version("3.9") >
Version("3.10")` is `False` (real), whereas the **pre-patch** textual
`"3.9" > "3.10"` is `True`. `Solution_prepatch.lean` reproduces the textual
comparison (`decide (r.required > r.present)` on the raw `List Char`) and
therefore **fails** `raised = anyUnmet reqs` (G-DIFF) — its loop body cannot
discharge the invariant when the textual and numeric verdicts disagree (e.g. on
`required "3.9"`, `present "3.10"`). This is exactly the F2P
`test_needs_extensions` "needs_extensions fulfilled" case (`'3.9'` required,
`'3.10'` loaded).

## B. The domain restriction — `try/except InvalidVersion`

The gold patch wraps the numeric comparison in `try … except InvalidVersion:`
and falls back to the textual `reqversion > extension.version` when a version
string is not PEP 440-parseable. The spec models the **numeric** branch only and
pins its domain with `require reqs.all reqWellFormed` (`numericVer`: every dotted
component a non-empty digit run). On that domain `Version(...)` never raises
`InvalidVersion`, so the fallback branch is unreachable — G-AX asserts this
(`Version()` does not raise inside `numericVer`). The fallback is out of the
modeled scope by construction, not hidden: it is a behaviour the issue does not
exercise (the bug and the F2P test are entirely within numeric versions), and
modeling it would not strengthen `verify ⇒ resolved`. No kind-3 step: the changed
op is fully expressed on its modeled domain.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — the
version comparison from textual to numeric — is modeled **deeply** (the
spelled-out `verGt`/`relGt`/`parseComp`/`splitDots`, step A3, an A-reference + I),
not hidden behind an axiom about the function under change: there is no consumed
axiom. The deep model's fidelity to the real `packaging.Version` comparator is
the single A-reference, G-AX-validated.

## D. verify(Solution) ⇒ resolved

`anyRequirementUnmet` verifies only if its output equals `anyUnmet reqs`, i.e.
the disjunction of the per-requirement test where the version comparison is the
exact numeric `verGt` with `verGt "3.9" "3.10" = false` (A3). By R
(dict ↔ `List Requirement`, raise ⇔ boolean, mapping.md §2) the verified scan
equals the patched `verify_needs_extensions`'s raise decision on the modeled
numeric-version inputs; by G-AX the deep model `verGt` equals the real
`packaging.Version` comparison (A-reference); by G-CONF the R/I transliteration
of the fold agrees with `patch.diff`'s observable (raises ⇔ unmet) on ≥10⁵
inputs. Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement and the audited callee — and the gold patch
resolves (G-RESOLVE). Trust points are exactly the two of plan §1.1: A-reference
soundness (G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
