# mapping.md — pytest-dev__pytest-7236

Binds every `model.py` symbol to its repository counterpart at
`base_commit = c98bc4cd3d687fe9b392d8eecd905627191d4f06`, states the type
abstraction, and gives the provenance of the deeply-modelled helper.

Repo file under change: `src/_pytest/unittest.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `decide_teardown(item)` | the post-mortem teardown-recording branch in `TestCaseFunction.runtest` — `src/_pytest/unittest.py:223-225` | the modeled changed function (whether to record the test case's teardown routine for explicit later invocation under `--pdb`) |
| `skip_marker_set(skip_marker)` *(deep model — A-reference)* | `_is_skipped(obj)` — `src/_pytest/unittest.py:305-307` (introduced by the patch); `bool(getattr(obj, "__unittest_skip__", False))` | pure spec: whether the skip marker counts as set |
| `TestCaseItem.postmortem_mode` | `self.config.getoption("usepdb")` — `unittest.py:223` | the `--pdb` post-mortem mode flag |
| `TestCaseItem.skip_marker` | the value read by `getattr(self.obj, "__unittest_skip__", False)` (the `__unittest_skip__` attribute on `self.obj`) | the skip marker value under the default-absent lookup |
| `TestCaseItem.teardown_recorded` | the effect of `self._explicit_tearDown = self._testcase.tearDown` (recording the teardown for explicit later invocation in `teardown()`) — `unittest.py:224` set, `unittest.py:123-126` consumed | the recorded-for-later flag (the observable that governs whether `tearDown` is eventually run) |

The pre-patch repo behaviour the change fixes (for the refinement audit, not
referenced from the consumer spec view): `runtest` (`unittest.py:208-233`)
unconditionally executed the recording branch whenever `usepdb` was truthy
(`if self.config.getoption("usepdb"):`), so for a skipped test `teardown()`
later invoked the recorded `_explicit_tearDown` (the test's `tearDown`).

Other change sites in the same patch, behaviour-identical refactors
(`getattr(..., "__unittest_skip__", ...)` inlined → `_is_skipped(...)`),
covered by the same deep model `skip_marker_set` (refinement.md §B):
- `collect` — `unittest.py:44` (`skipped = getattr(cls, "__unittest_skip__", False)` → `_is_skipped(cls)`).
- `_make_xunit_fixture.fixture` — `unittest.py:92` (`if getattr(self, "__unittest_skip__", None):` → `if _is_skipped(self):`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.config.getoption("usepdb")` (truthy config value) | `bool` `usepdb` | the option is consumed only for its truthiness in the `and`; modelled as a `bool`. |
| `getattr(obj, "__unittest_skip__", False)` value | `int` `skip_marker` | `0` ↔ attribute absent OR present-but-falsy; non-zero ↔ attribute present with a truthy value. `bool(getattr(...))` ↔ `skip_marker != 0`. This is the value space `_is_skipped` reduces with `bool(...)`. |
| `self._explicit_tearDown = self._testcase.tearDown` (recording the routine) and its later invocation in `teardown()` | `bool` `teardown_recorded` | `teardown_recorded == True` ↔ the teardown routine is recorded for explicit later invocation (so `teardown()` runs it); `False` ↔ not recorded (so it is not run). The `setattr(..., "tearDown", lambda: None)` neutralising the immediate teardown rides along with the recording and is not separately observable. |

`runtest` reads `usepdb` and the marker (read-only) and records the teardown
routine; `decide_teardown` mirrors this with `Acc(..., 1/2)` on the read-only
mode flag and marker and full permission on the mutated `teardown_recorded`.

## 3. Deep-model provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `skip_marker_set` deep model ↔ `_is_skipped` / `bool(getattr(...))` (A-reference)
**Callee:** the helper the patch introduces,
`_is_skipped(obj) = bool(getattr(obj, "__unittest_skip__", False))`
(`src/_pytest/unittest.py:305-307`). The skip decision is modelled **deeply**
by the `@Pure` function `skip_marker_set(skip_marker) = (skip_marker != 0)` in the
`pure` region; there is **no `skip_marker_set` axiom** the proof consumes. The deep
model is validated equal to the real helper out-of-band by axiom_check.py
(G-AX).

`getattr(obj, "__unittest_skip__", False)` returns the attribute's value if the
object carries it, else `False`; `bool(...)` then reduces to truthiness. So
`_is_skipped(obj)` is `True` exactly when the marker is present with a truthy
value. `@unittest.skip(...)` (CPython `unittest`) sets `__unittest_skip__ = True`
on the wrapped method/class; `@pytest.mark.skip` does not set it (the F2P
`[@pytest.mark.skip]` variant is skipped by pytest's own machinery before the
unittest path, so its teardown is not recorded either — and it is a PASS_TO_PASS
that the conjunction preserves). The integer carrier captures the full truthiness
space (absent/falsy → 0, truthy → non-zero), matching `bool(...)`. Source:
CPython `Lib/unittest/case.py` (`skip()` sets `test_item.__unittest_skip__ =
True`); Python `getattr`/`bool` semantics. Docs:
https://docs.python.org/3/library/unittest.html#unittest.skip.

**Soundness check (G-AX):** `axiom_check.py` builds objects spanning the marker
space — attribute absent; present and `False`/`0`/`""`/`None`/empty (falsy);
present and `True`/non-zero-int/non-empty (truthy) — runs the real
`bool(getattr(obj, "__unittest_skip__", False))` on each, and asserts it equals
the deep model `skip_marker_set(marker)` under the carrier bijection (falsy ↔ 0,
truthy ↔ non-zero). It also reconstructs the full `runtest` decision
`usepdb and not _is_skipped(obj)` over the `usepdb × marker` grid and asserts it
equals `decide_teardown`'s postcondition. Exit 0 iff sound. It imports only the
standard library; nothing repo-specific (the helper is a one-line
`bool(getattr(...))` reproduced from source).
