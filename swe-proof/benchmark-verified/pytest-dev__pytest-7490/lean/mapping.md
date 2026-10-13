# mapping.md — pytest-dev__pytest-7490

## Modeled function
`resolveExpectedFailure` — the most-specific-known-first resolution of the
effective expected-failure (`xfail`) annotation that the outcome-reporting path
consults. The gold patch adds a *post-body refresh* of this annotation in the
test-call hookwrapper of `src/_pytest/skipping.py`; this is the
independently-observable fixed behavior the FAIL_TO_PASS tests assert.

## Symbol binding (file:line @ base_commit 7f7a364)
| Lean symbol | Python symbol | location |
|---|---|---|
| `ExpectedFailure` | `class Xfail` (the `attr.s` result of `evaluate_xfail_marks`) | `src/_pytest/skipping.py:190-197` |
| `ExpectedFailure.reason` | `Xfail.reason : str` | `:194` |
| `ExpectedFailure.run` | `Xfail.run : bool` | `:195` |
| `ExpectedFailure.strict` | `Xfail.strict : bool` | `:196` |
| `before : Option ExpectedFailure` | `item._store.get(xfailed_key, None)` as observed at the **start** of `pytest_runtest_call` (the value the setup hook stored before the body ran) | `:249-251` (read), set at `:242` |
| `after : Option ExpectedFailure` | `evaluate_xfail_marks(item)` re-evaluated **after** the body ran (markers may have changed during the run) | post-`yield` block added by the patch, `:257+` |
| `result : Option ExpectedFailure` | the value of `item._store[xfailed_key]` once the post-body refresh completes — i.e. what `pytest_runtest_makereport` later reads at `:264` | patched `pytest_runtest_call` tail |

The `Xfail` field `raises : Optional[Tuple[Type[BaseException],...]]` is NOT
modeled: it is irrelevant to the most-specific-known-first selection the patch
governs (the selection copies the whole annotation object unchanged; the chosen
fields `reason/run/strict` are a representative reporting view, sufficient for
the discriminating behavior and the differential test). The selection is
field-agnostic, so the bijection is sound for the modeled behavior.

## Type bijection (Lean ↔ Python) — used by G-CONF
| Lean | Python |
|---|---|
| `none : Option ExpectedFailure` | `None` stored at / returned for `xfailed_key` (no xfail annotation in effect) |
| `some ⟨reason, run, strict⟩` | an `Xfail(reason=..., run=..., strict=..., raises=None)` object |
| `before` | the `xfailed_key` store value at entry to `pytest_runtest_call` |
| `after` | `evaluate_xfail_marks(item)` after the body ran |
| `result` | `xfailed_key` store value after the patched post-body refresh |

## Callee provenance + flag deps
- No unchanged callee is consumed as an axiom. The two annotation observations
  (`before`, `after`) are the *outputs* of `evaluate_xfail_marks` at two
  different moments; the patch does NOT change `evaluate_xfail_marks` itself — it
  changes *when* its result is (re)stored. The modeled operation is purely the
  store-refresh selection `store[key] = before if before is not None else after`,
  which is spelled out directly. Hence `axioms = []`,
  `deep_model_references = []`, `axiom_check.py` is a skip stub.
- Flag dependency: the patch also moves the `runxfail` guard inline (a `[NOTRUN]`
  reporting concern handled in `pytest_runtest_setup` / the pre-`yield` block of
  `pytest_runtest_call`). That guard does not affect the post-body refresh that
  the FAIL_TO_PASS tests exercise (those tests run without `--runxfail`); the
  refresh is unconditional. The modeled function is the refresh; the `runxfail`
  rewording is a behavior-preserving I-restructure (see refinement.md).

## G-CONF fuzz seed
Pinned seed: `7490` (used by `conformance_check.py`).
