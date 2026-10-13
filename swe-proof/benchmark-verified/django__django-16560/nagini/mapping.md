# mapping.md — django__django-16560

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 51c9bb7cd16081133af4f0ab6d06572660309730`, states the type
abstraction, and gives the provenance of the one library value-flow the
refinement relies on.

Repo files under change:
`django/db/models/constraints.py` (BaseConstraint / CheckConstraint /
UniqueConstraint) and `django/contrib/postgres/constraints.py`
(ExclusionConstraint). All four constraint classes receive the *same* uniform
change: an optional `violation_error_code` classifier threaded through
configuration, violation reporting, equality, reconstruction, and the textual
representation.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| the classifier token (`code` / `rule_code` / `*_code` params) | `self.violation_error_code` (new attr; class default `None` post-patch at `constraints.py:21`) | the optional violation classifier |
| the opaque payload (`*_key` params) | the rule's discriminating non-classifier facets (e.g. `name`/`fields`/`check`/`expressions`) | abstract stand-in for "everything else equality compares" |
| `ValidationFailure` (user exception, fieldless) | `django.core.exceptions.ValidationError` (`django/core/exceptions.py:133`) | the validation error a rule raises on a detected violation |
| `configured_code(code)` | the configuration storing the classifier — `BaseConstraint.__init__` (+ each subclass forwarding `violation_error_code` to `super().__init__`): `constraints.py:21,25,33-34,85-91,157-216`; `postgres/constraints.py:26-63` | (1) the classifier is retained / defaults to the neutral marker |
| `surfaced_violation_code(rule_code, violated)` | the classifier on the error built at the violation site — `ValidationError(..., code=self.violation_error_code)` in `validate()`: `constraints.py:115,388,403`; `postgres/constraints.py:207,212` (post-patch) | (2) the surfaced failure carries exactly the rule's classifier |
| `validate_rule(rule_code, violated)` | the raise-on-violation control flow of `CheckConstraint.validate` / `UniqueConstraint.validate` / `ExclusionConstraint.validate` (`constraints.py:111-117,385-405`; `postgres/constraints.py:205-212`) | (2) raise iff the underlying check reports a violation |
| `constraints_equal(a_key, a_code, b_key, b_code)` | `__eq__` (`constraints.py:132-139,313-325`; `postgres/constraints.py:143-154`) | (3) equality includes the classifier |
| `keyword_bundle_names_code(rule_code)` | `BaseConstraint.deconstruct` (the new `if self.violation_error_code is not None: kwargs[...] = ...` at `constraints.py:84-85` post-patch) | (4) reconstruction keywords name the classifier iff present |

The textual-representation change (each class appends a
` violation_error_code=%r` segment iff `self.violation_error_code is not None`)
is the *string-rendered* projection of the very same `code is not None`
predicate that `keyword_bundle_names_code` models; it is not separately
contracted (it is pure presentation over the same boolean, and Nagini bans
building arbitrary-value strings). Its tested behaviour is the same
present/absent gating verified by `keyword_bundle_names_code` and validated
end-to-end by G-RESOLVE.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `violation_error_code: str` or `None` | `Optional[int]` | `None` ↔ `None` (the neutral "no classifier" marker); each distinct `str` classifier ↔ a distinct non-null `int` token. The only observables the tests make of the code are identity comparisons (`==`/`is`, present/absent), never its characters — so an opaque token domain is faithful. `is` on the `Optional[int]` token mirrors `==` on the (interned) classifier string in the tests. |
| the underlying violation check (`queryset.exists()`, `Q(check).check(...)`, `(condition & Exists(...)).check(...)`) | `violated: bool` input | an unchanged callee whose only relevant observable is its boolean verdict; abstracted as the boolean directly (no axiom — the patch does not change it). |
| `ValidationError(message, code=X)` | `ValidationFailure()` raised + `surfaced_violation_code` returning `X` | builtin exceptions crash Nagini's `Exsures`; the user-defined `ValidationFailure` is the raise marker, and the classifier the error carries is pinned functionally by `surfaced_violation_code` (whose `Ensures(Result() is rule_code)` is the discriminating fact). The `message` is irrelevant to the classifier flow and is dropped. |
| the rule's non-classifier payload (`name`, `fields`, `check`, …) | `*_key: int` | a single opaque int per rule standing for "every other equality facet"; the tested `__eq__` change is solely the *addition* of the classifier term to a conjunction that already compares the rest. |
| keyword bundle `kwargs` from `deconstruct` | `bool` (classifier present?) | the patch's only change to `deconstruct` is the conditional insertion `if self.violation_error_code is not None: kwargs["violation_error_code"] = ...`; the observable the F2P test asserts is exactly membership of that key, i.e. the boolean `code is not None`. |

`str` indexing/iteration is banned in Nagini; since no test inspects classifier
*characters* (only presence and identity), the `Optional[int]` token domain is
the faithful carrier — no `List[int]` is needed.

## 3. Callee provenance (the one library value-flow the refinement relies on)

There is **no `@ContractOnly` axiom** consumed by the proof and **no A-reference
deep model**. The single library fact the refinement leans on is the
**store-verbatim semantics of the framework validation error's `code`**:

  `ValidationError(message, code=X).code is X`, and
  `ValidationError(message).code is None`.

**Source:** `django/core/exceptions.py`, `ValidationError.__init__`
(`def __init__(self, message, code=None, params=None)`), the scalar branch
`self.code = code` (line 175). The constructor stores `code` verbatim with no
transformation; the default `code=None`. This is unchanged by the patch.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL
`django.core.exceptions.ValidationError` and the REAL patched constraint classes
in-container and asserts (1) configuration retains/defaults the classifier,
(2) the error built at the violation site carries exactly the rule's classifier
(and `ValidationError(code=X).code is X`, default `None`), (3) the classifier
participates in `__eq__`, and (4) `deconstruct` names the classifier iff
present. It imports only the standard library plus the repo under test. Exit 0
iff sound. (On the pre-patch tree the configuration/eq/deconstruct checks fail,
confirming the check exercises the changed behaviour, not a vacuity.)
