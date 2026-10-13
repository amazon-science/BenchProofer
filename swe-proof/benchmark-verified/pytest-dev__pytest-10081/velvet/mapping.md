# mapping.md — pytest-dev__pytest-10081

Symbol binding, type bijection, callee provenance, and the pinned G-CONF fuzz
seed. All file:line references are at `base_commit`
`da9a2b584eb7a6c7e924b2621ed0ddaeca0a7bea`.

## 1. The changed function (modeled)

| model symbol | repo symbol | repo location @ base_commit | carrier |
|---|---|---|---|
| `shouldDeferCleanup` | the decision, inside `TestCaseFunction.runtest`, whether to postpone the post-test cleanup step when the interactive debugger option is active | `src/_pytest/unittest.py:301` (method); decision at `:319`; patched at `:316–321` | three `Bool` inputs → `Bool` |

The only behaviour the patch changes is the boolean predicate that gates the
postponement of the cleanup step (`runtest`, the `else` branch of the
async check). Everything else in `runtest` (async dispatch, the
`setattr`/`delattr` of the bound method, calling the test) is unchanged and
orthogonal to the gated decision; it is not modeled. mapping.md §3 records why
those are R-identity.

## 2. Type bijection (used by G-CONF)

| repo reality | Lean model |
|---|---|
| `self.config.getoption("usepdb")` — truthiness of the `--pdb` option | `debuggerActive : Bool` |
| `_is_skipped(self.obj)` — the unit (test method) carries the skip marker | `unitSkipped : Bool` |
| `_is_skipped(self.parent.obj)` — the enclosing group (test class) carries the skip marker | `groupSkipped : Bool` |
| postponement happens (real `self._explicit_tearDown` is set; the bound cleanup is replaced by a no-op and deferred) | `out = true` |
| postponement does NOT happen (cleanup runs in its normal place / is skipped by the framework) | `out = false` |

`bool ↔ Bool` is identity. The three inputs are the *results* of the unchanged
callees `config.getoption` and `_is_skipped`, taken as boolean carriers (§3).

## 3. Callee provenance and why there are no axioms

The decision calls exactly two unchanged callees, both consumed only for their
boolean result:

- **`_is_skipped(obj)`** — `src/_pytest/unittest.py:412`:
  ```python
  def _is_skipped(obj) -> bool:
      return bool(getattr(obj, "__unittest_skip__", False))
  ```
  Pure, unchanged by the patch. The patch adds a *second call site*
  (`_is_skipped(self.parent.obj)`) but does not alter the function. Its result
  is modeled as the `Bool` input `unitSkipped` / `groupSkipped` — an
  **R-identity** refinement (`bool(getattr(...)) ↔ Bool`), not an axiom. G-CONF
  routes the inputs through the *real* `_is_skipped` over objects carrying
  varied marker attribute values, refuting the R leg.
- **`self.config.getoption("usepdb")`** — returns the truthiness of the `--pdb`
  command-line option; unchanged. Modeled as the `Bool` input `debuggerActive`
  — R-identity.
- **`assert isinstance(self.parent, UnitTestCase)`** (`:318`, added by the
  patch) is a type assertion with no behavioural effect (the parent of a
  `TestCaseFunction` is always a `UnitTestCase`, `:183`, `:60`); it is not
  modeled. R-identity (no observable).

`self.parent.obj` resolves to the enclosing class object via the standard
collector parent chain (`TestCaseFunction.parent` is the `UnitTestCase`,
`:183`/`:200`; `UnitTestCase.obj` is the test class). Taking
`_is_skipped(self.parent.obj)` as `groupSkipped` is the load-bearing new input.

Because both callees are consumed purely for their boolean value and modeled as
R-identity inputs, there is **no consumed axiom and no `:|` stub**. G-AX is
therefore not applicable (no `axiom_check.py`); G-CONF carries the full R/I
burden against the real `_is_skipped`.

## 4. G-CONF fuzz seed

Pinned seed: **`10081`**. `N_FUZZ = 100_000` plus the full 2³ = 8 boundary
cross-product of `(debuggerActive, unitSkipped, groupSkipped)` and a sweep of
real marker attribute encodings (`True`, `1`, truthy/falsy objects, missing
attribute) for the `_is_skipped` R-leg.
