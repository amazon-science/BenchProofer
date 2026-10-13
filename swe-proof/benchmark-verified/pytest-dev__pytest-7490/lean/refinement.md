# refinement.md — pytest-dev__pytest-7490

Maps every operation in `implementation_resolveExpectedFailure` to its
`patch.diff` counterpart. The independently-observable fixed behavior is the
post-body refresh of the effective xfail annotation added to the test-call
hookwrapper in `src/_pytest/skipping.py` (see mapping.md). Tags: **R**
type-refinement, **A-consumed** proof uses a callee axiom, **A-reference**
deep-modeled changed op validated == real callee, **I** identical concrete op.

## Patch (post-patch, the governing fragment)
```python
# src/_pytest/skipping.py — pytest_runtest_call, AFTER yield (added by the patch)
    yield

    # The test run may have added an xfail mark dynamically.
    xfailed = item._store.get(xfailed_key, None)   # `before`
    if xfailed is None:
        item._store[xfailed_key] = xfailed = evaluate_xfail_marks(item)   # `after`
```
The net effect on the stored annotation: `store[xfailed_key]` becomes the
pre-existing value when that value is not `None`, otherwise the freshly
re-evaluated annotation. `pytest_runtest_makereport` later reads exactly this
stored value to decide xfail-vs-fail.

## Operation correspondence
| # | Lean op (`implementation_resolveExpectedFailure`) | patch.diff / governed op | tag | note |
|---|---|---|---|---|
| 1 | `let mut xfailed := before` | `xfailed = item._store.get(xfailed_key, None)` | R | `item._store.get(xfailed_key, None) : Optional[Xfail] ↔ before : Option ExpectedFailure`; `None ↔ none`, `Xfail(...) ↔ some ⟨reason,run,strict⟩`. |
| 2 | `if xfailed.isNone then xfailed := after` | `if xfailed is None: item._store[xfailed_key] = xfailed = evaluate_xfail_marks(item)` | R | `value is None ↔ Option.isNone`; the re-evaluated `evaluate_xfail_marks(item)` is `after`. Selection only; the patch does not change `evaluate_xfail_marks`. |
| 3 | `return xfailed` | the value left in `item._store[xfailed_key]`, read later by `pytest_runtest_makereport` | I | identical: the resolved annotation is what reporting consults. |

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference).
Therefore `meta.json axioms = []`, `deep_model_references = []`, and
`axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow (`before if before is not None else after`) against the real
patched store-refresh logic over ≥10^5 fuzzed `(before, after)` annotation
states. `conf_skip = false`.

## Prepatch = the real bug
`Solution_prepatch.lean` omits op #2 entirely — its impl is `let mut xfailed :=
before; return xfailed`, the literal pre-patch behavior where the test-call
hookwrapper never refreshes the annotation after the body runs. With `before =
none` (no marker present before the body) and `after = some ⟨…⟩` (a marker
added during the body) it returns `none`, but the spec's no-earlier-annotation
clause demands `result = after = some ⟨…⟩`. The carried gold proof fails to
typecheck on exactly that discriminating clause (`before = none → result =
after`) — precisely the behavior the FAIL_TO_PASS tests
`test_dynamic_xfail_set_during_runtest_failed` and
`…_passed_strict` assert (a dynamically-added xfail mark must be honored by the
report). The spec is byte-identical between the two files (only the impl body
differs).

## patch.diff == gold
`patch.diff` is the gold patch verbatim. It applies at `base_commit` and the
harness resolves. Beyond the modeled post-body refresh, the patch also inlines
the `runxfail` guard in `pytest_runtest_setup` and the pre-`yield` block of
`pytest_runtest_call` and simplifies the `skipped_by_mark_key` assignment; these
are behavior-preserving restructures (I) that do not affect the modeled refresh
the FAIL_TO_PASS tests exercise.
