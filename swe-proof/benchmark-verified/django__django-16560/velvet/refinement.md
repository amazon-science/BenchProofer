# refinement.md — django__django-16560

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the five `do` blocks and their `pure` post-images) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement; state the bijection),
**A-consumed** / **A-reference** (axiom legs — none in this bundle), or **I**
(identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1) against the real gold-patched constraint objects; the narrative is audited
by **G-EQ**. Claim: any impl verifying against this frozen spec, refined per the
maps below, is behaviourally equal to the gold patch on the tested observables,
so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

The feature adds an optional `violation_error_code` and surfaces it in five
independent projections of a constraint. Each projection is one method; each has
its own failing prepatch (G-DIFF needs one per independently-observable fixed
behaviour). `ErrCode = Option (List Char)` ↔ `str | None` throughout (mapping.md
§2).

## A. Store — `recordErrorCode` ↔ `BaseConstraint.__init__`

Gold hunk (`django/db/models/constraints.py`):
```
+        if violation_error_code is not None:
+            self.violation_error_code = violation_error_code
```
(with the class attribute default `violation_error_code = None`).

| # | Solution.lean impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `supplied : ErrCode` | the new `violation_error_code=None` kwarg | R | `str\|None ↔ Option (List Char)` (mapping.md §2). |
| A2 | `out := supplied` when `supplied ≠ none`, else `none` | the store guarded by `is not None` over the `None` class default | I | observationally `self.violation_error_code == supplied if supplied is not None else None`; the guard is redundant with the `None` default but kept faithful. `recordedCode supplied = supplied`. |

Prepatch_1 reverts to the base_commit state (no attribute tracked ⇒ always
`none`) and **fails** `out = recordedCode supplied`.

## B. Serialize — `serializeWithCode` ↔ `BaseConstraint.deconstruct`

Gold hunk:
```
+        if self.violation_error_code is not None:
+            kwargs["violation_error_code"] = self.violation_error_code
```

| # | Solution.lean impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | param `base : List (String × List Char)` | the pre-existing `kwargs` dict (`name`, optional `violation_error_message`) | R | dict ↔ ordered assoc list (mapping.md §2); a free input (unchanged content). |
| B2 | `some c => base ++ [("violation_error_code", c)]`; `none => base` | the guarded `kwargs[...] = ...` | I + R | adding the entry iff a code is set ↔ the `is not None` guard; the appended pair is the bijection of the str key/value. `withCodeKwarg`. |

Prepatch_2 never appends the entry and **fails** `out = withCodeKwarg base code`.

## C. Equality — `constraintsEqual` ↔ `CheckConstraint.__eq__` / `UniqueConstraint.__eq__`

Gold hunk (both subclasses, same shape):
```
+                and self.violation_error_code == other.violation_error_code
                 and self.violation_error_message == other.violation_error_message
```

| # | Solution.lean impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | param `otherEqual : Bool` | the conjunction of all OTHER `__eq__` clauses (name, check/fields, condition, message, …) | R | a free input (unchanged conjuncts) ↔ their truth value. |
| C2 | `otherEqual && (codeA == codeB)` | ANDing the new `self.violation_error_code == other.violation_error_code` conjunct | I | `==` on `Option (List Char)` ↔ Python `==` on `str\|None`; conjunction is faithful. `constraintEq`. |

Prepatch_3 drops the code conjunct (`out := otherEqual`) and **fails**
`out = constraintEq otherEqual codeA codeB` (discriminated when
`otherEqual = true` and `codeA ≠ codeB`).

## D. Text form — `renderConstraint` ↔ `CheckConstraint.__repr__` / `UniqueConstraint.__repr__`

Gold hunk (both subclasses, same shape):
```
+            (
+                ""
+                if self.violation_error_code is None
+                else " violation_error_code=%r" % self.violation_error_code
+            ),
```
appended into the `repr` format string.

| # | Solution.lean impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| D1 | param `base : List Char` | the rest of the `repr` string (class, fields, name, …) | R | a free input (unchanged rendering) ↔ its character content. |
| D2 | param `shown : List Char` | `%r % self.violation_error_code` | R | the standard value formatter's rendering of the code, an unchanged formatting step; `shown ↔ (%r % code)` (mapping.md §2). |
| D3 | `some _ => base ++ " violation_error_code=".toList ++ shown`; `none => base` | the `"" if None else " violation_error_code=%r" % code` fragment | I + R | appending the fixed-key fragment + `shown` iff a code is set ↔ the conditional expression. `renderedWithCode`. |

Prepatch_4 never appends the fragment (`out := base`) and **fails**
`out = renderedWithCode base code shown`.

## E. Validate report — `validateWithCode` ↔ `*.validate`

Gold hunks (CheckConstraint and the message-reporting Unique/Exclusion branches):
```
-                raise ValidationError(self.get_violation_error_message())
+                raise ValidationError(
+                    self.get_violation_error_message(), code=self.violation_error_code
+                )
```

| # | Solution.lean impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| E1 | param `isValid : Bool` | the unchanged validity predicate (`Q(self.check).check(...)`, `queryset.exists()`) | R | a free input (unchanged DB-backed test) ↔ its boolean. |
| E2 | `if isValid then Except.ok () else Except.error code` | accept silently, else `raise ValidationError(msg, code=self.violation_error_code)` | I + R | acceptance ↔ no raise (`Except.ok ()`); a reported violation carrying the code ↔ `Except.error code`; observable is `exc.code` (mapping.md §2). `checkResult`. |

Prepatch_5 reports the violation with `Except.error none` (no code, the
base_commit behaviour) and **fails** `isValid = false → out = Except.error code`
(discriminated whenever `code ≠ none`).

### Scope note (the deliberately-uncovered fields branch)
The gold patch leaves the `UniqueConstraint` *fields* branch raising
`instance.unique_error_message(...)` with its own `code="unique_together"`,
unchanged (PASS_TO_PASS `test_validate` asserts `cm.exception.code ==
"unique_together"` even when a custom code is set). This bundle models only the
**message-reporting** branch — the one the patch changes and the F2P tests
`test_validate_custom_error` / `test_validate_conditon_custom_error` exercise. The
spec makes NO claim that every violation carries the custom code, so it does not
contradict the unchanged fields branch (directive 4 / 3 — skeleton-faithful, not
over-claiming).

## F. No kind-3 (inexpressible-changed-op) steps; no axioms

Every step is R or I. There is no operation that genuinely changed yet is
inexpressible: the whole change is data-plumbing of an optional value, modeled
deeply. There is **no consumed axiom and no A-reference**; every unchanged
sub-computation is a free input (mapping.md §1.1, §3), so G-AX has nothing to
check and skips.

## G. verify(Solution) ⇒ resolved

Each method verifies only if its output equals the exact post-image
(`recordedCode` / `withCodeKwarg` / `constraintEq` / `renderedWithCode` /
`checkResult`). By the R bijection (`str\|None ↔ Option (List Char)`, dict ↔
assoc list, `repr` ↔ `List Char`, `ValidationError(code)` ↔ `Except`), each
verified projection equals the corresponding gold-patched observable; G-CONF
refutes any R/I divergence over ≥10⁵ inputs against the real patched objects.
Therefore a model satisfying this spec, refined by the maps above, is the gold
patch up to type refinement on the five tested behaviours — and the gold patch
resolves (G-RESOLVE). The one trust point of plan §1.1 left is refinement
fidelity (this doc, G-EQ + G-CONF); there are no axioms to trust.
