# refinement.md — django__django-16560

The operation-by-operation correspondence between `model.py`'s implementations
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement —
same operation, refined carrier type), **A** (axiomatized callee — split into
**A-consumed**, the proof uses the axiom's `Ensures`, and **A-reference**, a
deep model validated == the real callee by `axiom_check.py` / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the maps below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

The patch makes ONE uniform change — threading an optional `violation_error_code`
classifier — across four observable surfaces of every constraint class
(`BaseConstraint`/`CheckConstraint`/`UniqueConstraint` in
`django/db/models/constraints.py`, `ExclusionConstraint` in
`django/contrib/postgres/constraints.py`). The four surfaces are modelled as
four contracted functions; each has its own verification-failing prepatch
(G-DIFF), one per independently-observable fixed behaviour.

## Site 1 — Configuration (`configured_code` ↔ `__init__`)

Gold hunks (`constraints.py:21,25,33-34`, mirrored in every subclass `__init__`
forwarding `violation_error_code` to `super().__init__`):
```
+    violation_error_code = None
-    def __init__(self, *args, name=None, violation_error_message=None):
+    def __init__(self, *args, name=None, violation_error_code=None, violation_error_message=None):
+        if violation_error_code is not None:
+            self.violation_error_code = violation_error_code
```

| # | model.py impl op (`configured_code`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1a | param `code: Optional[int]` | `violation_error_code=None` kwarg | R | `str`/`None` ↔ `Optional[int]` token (mapping.md §2). |
| 1b | `return code` so `Result() is code` | `if … is not None: self.violation_error_code = …`, else the class default `None` | R + I | both retain the classifier verbatim and default to the neutral `None` marker. For the token domain the guard-then-class-default is observationally `self.violation_error_code = violation_error_code` (the absent input is `None`, which the class default already supplies). |

Prepatch `model_prepatch_2.py`: returns `None` regardless (the pre-patch
constructor with no classifier parameter) → fails `Result() is code`. The F2P
`test_custom_violation_code_message` asserts the configured classifier is
retained.

## Site 2 — Violation reporting (`validate_rule` / `surfaced_violation_code` ↔ `validate`)

Gold hunks (`constraints.py:115,388,403`; `postgres/constraints.py:207,212`):
```
- raise ValidationError(self.get_violation_error_message())
+ raise ValidationError(self.get_violation_error_message(), code=self.violation_error_code)
```

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| 2a | `violated: bool` input | the underlying check `queryset.exists()` / `Q(check).check(...)` / `(condition & Exists(...)).check(...)` verdict | R | the unchanged check is abstracted by its boolean verdict (mapping.md §2); not an axiom — the patch leaves it untouched. |
| 2b | `if violated: raise ValidationFailure()` else return (`validate_rule`) | `if <check>: raise ValidationError(…)` else fall through | I | identical control flow: raise on a reported violation, return otherwise. `ValidationFailure` ↔ `ValidationError` (mapping.md §2). |
| 2c | `surfaced_violation_code(rule_code, True)` returns `rule_code` (`Ensures(Result() is rule_code)`) | the `code=self.violation_error_code` argument of the raised `ValidationError` | R + I | the surfaced failure carries EXACTLY the rule's classifier. `ValidationError`'s `code` store-verbatim semantics (`core/exceptions.py:175`) make the raised error's `.code` equal the argument (mapping.md §3, G-AX-checked); `surfaced_violation_code` pins that argument to `rule_code`. The message argument is irrelevant to the classifier flow (dropped, R). |

Prepatch `model_prepatch.py`: `surfaced_violation_code` returns `None` (the
pre-patch `ValidationError(msg)` with no `code` argument) → fails
`Result() is rule_code` whenever the rule carries a classifier. This is the
exact behaviour the F2P `test_validate_custom_error` /
`test_validate_conditon_custom_error` assert (`cm.exception.code == "…"`).

## Site 3 — Identity (`constraints_equal` ↔ `__eq__`)

Gold hunks (`constraints.py:137,323`; `postgres/constraints.py:152`):
```
  and self.violation_error_message == other.violation_error_message
+ and self.violation_error_code == other.violation_error_code
```

| # | model.py impl op (`constraints_equal`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 3a | `a_key == b_key` | the pre-existing conjunction comparing name/fields/check/… | R | `*_key` abstracts "every other equality facet" (mapping.md §2); unchanged by the patch. |
| 3b | `and a_code is b_code` | `and self.violation_error_code == other.violation_error_code` | R | the *added* conjunct: classifier identity. `is` on the token ↔ `==` on the classifier string (interned tokens; identity ⇔ equality for the token domain). |

Prepatch `model_prepatch_3.py`: drops the classifier conjunct
(`return a_key == b_key`, the pre-patch `__eq__`) → fails
`Result() == (a_key == b_key and a_code is b_code)` when the rules differ only in
classifier — exactly the F2P `test_eq` `assertNotEqual`.

## Site 4 — Reconstruction (`keyword_bundle_names_code` ↔ `deconstruct`)

Gold hunk (`constraints.py:84-85`):
```
+ if self.violation_error_code is not None:
+     kwargs["violation_error_code"] = self.violation_error_code
```

| # | model.py impl op (`keyword_bundle_names_code`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 4a | `return rule_code is not None` | the conditional `if self.violation_error_code is not None: kwargs[…] = …` | R + I | the observable the F2P `test_deconstruction` asserts is membership of the `violation_error_code` key in the kwargs, i.e. exactly the boolean `code is not None` (mapping.md §2). The stored value, when present, is the classifier verbatim. |

Prepatch `model_prepatch_4.py`: `return False` (the pre-patch `deconstruct`,
which never emits the key) → fails `Result() == (rule_code is not None)` when a
classifier is present.

## Textual representation — not separately contracted (same predicate as Site 4)

Each class's textual representation adds a ` violation_error_code=%r` segment iff
`self.violation_error_code is not None` — the *string-rendered* projection of the
identical `code is not None` predicate verified at Site 4. Nagini bans building
arbitrary-value strings, and the tested observable is the same
present-iff-non-None gating. It is therefore covered by Site 4's verified
predicate and validated end-to-end by G-RESOLVE; no kind-3 step is hidden.

## No kind-3 (unexpressible-changed-op) steps; no consumed axioms

Every step above is R or I over the `Optional[int]` token domain. There is **no
`@ContractOnly` axiom** the proof consumes and **no A-reference deep model**: the
only abstracted callee (the underlying violation check) is reduced to a boolean
verdict (the patch does not change it), and the framework error's
store-verbatim `code` semantics — the one library fact the refinement leans on —
is validated against the real `ValidationError` (and the real patched constraint
classes) by `axiom_check.py` / G-AX (mapping.md §3), not consumed as an axiom.

## verify(model) ⇒ resolved

Each contracted function verifies only if it reproduces its gold surface: the
configuration retains the classifier (Site 1), the surfaced failure carries
exactly the rule's classifier (Site 2), equality includes the classifier
(Site 3), and reconstruction names it iff present (Site 4). By R (the
`Optional[int]` token bijection, the boolean-verdict abstraction of the
unchanged check, the `ValidationFailure`↔`ValidationError` raise map +
`surfaced_violation_code`'s value pin) each verified function equals its gold
hunk on the tested inputs; G-AX confirms the framework `code` value-flow the
refinement assumes. Therefore a model satisfying this spec, refined by the maps
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE).
