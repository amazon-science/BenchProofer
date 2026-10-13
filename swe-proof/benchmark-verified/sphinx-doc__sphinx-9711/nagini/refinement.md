# refinement.md — sphinx-doc__sphinx-9711

The operation-by-operation correspondence between `model.py`'s implementation
(the `verify_requirement` impl region and the deep `version_gt` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The requirement-decision site — `verify_needs_extensions` (`sphinx/extension.py:54`)

Gold hunk (the per-extension decision; module import of `Version`/`InvalidVersion`
added at the top):
```
- if extension.version == 'unknown version' or reqversion > extension.version:
-     raise VersionRequirementError(...)
+ fulfilled = True
+ if extension.version == 'unknown version':
+     fulfilled = False
+ else:
+     try:
+         if Version(reqversion) > Version(extension.version):
+             fulfilled = False
+     except InvalidVersion:
+         if reqversion > extension.version:
+             fulfilled = False
+ if not fulfilled:
+     raise VersionRequirementError(...)
```

| # | model.py impl op (`verify_requirement`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `reqversion: List[int]`, `extversion: List[int]` | the `reqversion` dict value and `extension.version` string | R | dotted release string ↔ `List[int]` of integer release segments (mapping.md §2). |
| A2 | `ext_known: bool` | `extension.version == 'unknown version'` (first disjunct) | R | the loaded version's *presence* is the only thing this branch reads of it; abstracted to a boolean (mapping.md §2). |
| A3 | `fulfilled = True` | `fulfilled = True` | I | identical control-flow seed. |
| A4 | `if not ext_known: fulfilled = False` | `if extension.version == 'unknown version': fulfilled = False` | R | same branch, refined predicate (A2). |
| A5 | `else: if version_gt(ToSeq(reqversion), ToSeq(extversion)): fulfilled = False` | `else: try: if Version(reqversion) > Version(extension.version): fulfilled = False except InvalidVersion: …` | A-reference | the changed comparison is modelled **deeply**: `version_gt` (the spelled-out segment-wise integer compare in the `pure` region) IS the release-number ordering. There is no consumed comparator axiom — the proof never depends on one. The deep model is validated **== the real callee** out of band: G-AX (axiom_check.py) runs `packaging.version.Version` on boundary+fuzz and asserts `version_gt == (Version(..) > Version(..))`. On the modelled domain (valid dotted release numbers — the F2P/issue inputs) `Version()` never raises, so the `except InvalidVersion` textual fallback is never taken and the modelled path is exactly the executed path (mapping.md §3.1). |
| A6 | `if not fulfilled: raise RequirementUnfulfilled()` | `if not fulfilled: raise VersionRequirementError(__(...))` | R | `RequirementUnfulfilled` ↔ `VersionRequirementError`; a builtin/real exception in an `Exsures` crashes Nagini (mapping.md §2). The F2P test asserts only that the build aborts with *a* `VersionRequirementError`; the message content is observationally irrelevant. |
| A7 | `return True` (normal return) | falls off the end (no raise) | I | both denote "the requirement is fulfilled, the build proceeds"; the model reports it as a `True` return so the postcondition can pin the normal-return case. |

The discriminating content of the change — comparing `3.9` vs `3.10` as
RELEASE NUMBERS (`[3,9] < [3,10]`, so `version_gt` is False, requirement
fulfilled) rather than as TEXT (`"3.9" > "3.10"`, so the requirement is wrongly
rejected) — lives in `version_gt`'s segment-wise integer comparison (model) ⇔
`Version(reqversion) > Version(extension.version)` (real). The pre-patch
decision compared the version *strings* textually; `model_prepatch.py`
reproduces that (a lexicographic code-point comparison inside the impl region)
and **fails** the `Exsures` clause
`(ext_known is False or version_gt(ToSeq(reqversion), ToSeq(extversion)) is True)`
— i.e. it raises on `req=3.9, ext=3.10` where the release-number ordering says
the loaded version is adequate. That is exactly the spec sensing the change
(G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the version comparison — is modelled **deeply** (the spelled-out
segment-wise integer comparison `version_gt`/`version_gt_from`/`seg`, consumed
in `verify_requirement`, step A5, an **A-reference**), not hidden behind an
axiom about the operation under change: there is **no consumed comparator
axiom**. The real comparator `packaging.version.Version` appears only as the
**A-reference** that G-AX validates the deep model against. There are no
A-consumed axioms in this bundle.

## C. verify(model) ⇒ resolved

`verify_requirement` verifies only if its normal-return/raise decision is driven
EXACTLY by `ext_known` and the release-number ordering `version_gt` (the
postcondition pins the normal-return case to `ext_known is True ∧
version_gt(req,ext) is False`, and the `Exsures` pins the raise case to the
complement). By R (release string ↔ `List[int]` segments, `VersionRequirementError`
↔ `RequirementUnfulfilled`, the `'unknown version'`↔`ext_known` abstraction) the
verified decision equals the gold patch's `fulfilled` decision on the tested
inputs; by G-AX the deep model `version_gt` equals the real
`Version(..) > Version(..)` (A-reference) on the valid-release domain those
inputs inhabit. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and the audited deep-model
reference — and the gold patch resolves (G-RESOLVE). The single trust point is
PLAN §1.1's refinement fidelity (this document, G-EQ) plus the A-reference
soundness G-AX checks; there are no consumed axioms.
