# mapping.md — pytest-dev__pytest-7236

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = c98bc4cd3d687fe9b392d8eecd905627191d4f06`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance and flag dependencies.

Repo file under change: `src/_pytest/unittest.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `markedSkipped (skipMarked : Bool)` | `_is_skipped(obj)` — `src/_pytest/unittest.py` (helper ADDED by the patch at the end of the module) | modeled changed function: reports whether the object bears the skip mark |
| `teardownPostponed (asyncTest, debuggerActive, skipMarked)` | the teardown-deferral decision inside `TestCaseFunction.runtest` — `src/_pytest/unittest.py:207` (the `if self.config.getoption("usepdb") ...:` guard, body line 224) | modeled changed function: whether this test's teardown is deferred |

Both are on the fix list. `teardownPostponed` calls `markedSkipped` as a
sub-method (callee-under-spec, SPEC_GUIDE §3): `prove_correct` generates
`markedSkipped_correct`, which the caller's proof applies directly — better than
an axiom, and the reason there is **no consumed axiom** in this bundle.

The pre-patch repo expression the change replaces (refinement audit only, not in
the consumer spec view): the bare guard `if self.config.getoption("usepdb"):`
(`unittest.py:220` pre-patch), which became
`if self.config.getoption("usepdb") and not _is_skipped(self.obj):`.

The two other gold hunks (`collect`, `_make_xunit_fixture`) replace
`getattr(cls, "__unittest_skip__", False)` / `getattr(self, "__unittest_skip__",
None)` by `_is_skipped(...)`. These are **truthiness-identical refactors** that
route the SAME skip-mark read through the new helper; they change no observable
behavior (see refinement.md §C) and are not independently modeled.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `bool(getattr(obj, "__unittest_skip__", False))` — the skip-mark flag of `obj` | `skipMarked : Bool` | Python truthiness of the attribute ↔ Lean `Bool`; `True`↔`true`, `False`/absent↔`false`. `_is_skipped` returns exactly `bool(...)`. |
| `is_async_function(self.obj)` — whether the test method is `async` | `asyncTest : Bool` | the `if is_async_function(self.obj):` branch in `runtest`; `True`↔`true`. The async branch never reaches the deferral guard, so `asyncTest = true ⇒ postpone = false`. |
| `self.config.getoption("usepdb")` — whether `--pdb` is active | `debuggerActive : Bool` | the option's boolean value ↔ Lean `Bool`; `--pdb` given ↔ `true`. |
| `_is_skipped(self.obj)` evaluated at the guard | `skipMarked : Bool` | the same skip-mark read as `markedSkipped`'s input; bridges `_is_skipped(self.obj)`. |
| teardown deferral effect (`self._explicit_tearDown = self._testcase.tearDown` + stubbing `tearDown` to a no-op, later invoked by `teardown()`) | `postpone : Bool` | `postpone = true` ↔ the deferral branch taken (real `tearDown` postponed, then run later); `postpone = false` ↔ deferral skipped, so the stubbed no-op `tearDown` stands and the real `tearDown` never runs for a skipped test. This is what the F2P test observes via `tracked == []`. |

There are no string/collection carriers; the changed behavior is pure boolean
dataflow. Lean has no aliasing; all three inputs are read-only (not `mut`).

## 3. Callee provenance & flag dependencies

- `markedSkipped` ↔ `_is_skipped`: `_is_skipped(obj)` is `bool(getattr(obj,
  "__unittest_skip__", False))`. It is a NEW function the patch adds and is on
  the fix list, so it is modeled as a sub-method (callee-under-spec), NOT
  axiomatized. Its only behavior is to surface the skip-mark boolean, which is
  `markedSkipped`'s identity spec.
- `teardownPostponed` ↔ `runtest` deferral: the guard sits inside the
  `else` of `if is_async_function(self.obj):`, so the deferral is reachable only
  for non-async tests — captured by the `!asyncTest` conjunct. The `--pdb`
  dependency is the `debuggerActive` conjunct; the new skip exclusion is the
  `!skipMarked` conjunct (`and not _is_skipped(self.obj)`).
- No unchanged imperative/pure callee is consumed: there is no axiom and no
  `axiom_check.py`. G-AX is `skip` (meta.json).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`7236`** so the
consumer-side verdict is reproducible. Both modeled methods' impl regions are
pure R/I (closed boolean expressions; the `markedSkipped` sub-call is an I op
transliterated inline as the identity on `skipMarked`), so the entire impl is in
G-CONF scope and tested exhaustively over the boolean cube plus seeded fuzz.
