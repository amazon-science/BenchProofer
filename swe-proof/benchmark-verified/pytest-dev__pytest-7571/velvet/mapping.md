# mapping.md — pytest-dev__pytest-7571

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 422685d0bdc110547535036c1ff398b5e1c44145`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
callee provenance / flag dependencies.

Repo file under change: `src/_pytest/logging.py` (class `LogCaptureFixture`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `initStep (lvl0 : Int)` | `LogCaptureFixture.__init__(self, item)` — `src/_pytest/logging.py:344` | the modeled changed function (fixture construction: the level-restore bookkeeping it initializes) |
| `setLevelStep (st) (lvl)` | `LogCaptureFixture.set_level(self, level, logger=None)` — `src/_pytest/logging.py:421` | the modeled changed function (setting the capture level during a test) |
| `restoreStep (st)` | `LogCaptureFixture._finalize(self)` — `src/_pytest/logging.py:351` | the modeled changed function (end-of-test cleanup that restores levels) |
| `runLifecycle (lvl0) (lvl)` | the composite `__init__` → `set_level` → `_finalize` lifecycle the F2P test exercises (`testing/logging/test_fixture.py::test_change_level_undos_handler_level`) | the composite behavior the fix is about: the handler capture level after a set-then-teardown cycle |
| `FixtureState.level` | `self.handler.level` (the `LogCaptureHandler`'s logging level, `LogCaptureHandler(logging.StreamHandler).level`) | the capture level currently in effect |
| `FixtureState.savedLevel` | `self._initial_handler_level` (`Optional[int]`) — the attribute the fix introduces (`logging.py:348` post-patch) | the handler level recorded for reinstatement at teardown; `None` until `set_level` runs |
| `initState` / `setLevelState` / `restoreState` | pure deep models of the three storage code-paths (see §3) | deep models, NOT axiomatized callees |

The post-patch repo symbol the fix introduces (refinement audit only): the
`self._initial_handler_level` attribute, initialized to `None` at
`logging.py:348`, assigned `self.handler.level` at `logging.py:440`, and read
back under an `is not None` guard at `logging.py:357–358`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

The table G-CONF (§4) uses to translate values between the Lean value domain and
the Python repo types. A wrong entry surfaces as spurious G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.handler.level` (a logging level) | `FixtureState.level : Int` | a Python logging level is a non-negative `int`; modeled as `Int` (the fuzz domain is the same finite-int range — mapping note below). Identity on values. |
| `self._initial_handler_level : Optional[int]` | `FixtureState.savedLevel : Option Int` | `None` ↔ `none`; an `int v` ↔ `some v`. The guard `if self._initial_handler_level is not None` ↔ the `match … | some v => … | none => …` in `restoreState`. |
| the `level` argument of `set_level` | the `lvl : Int` parameter of `setLevelStep` | `set_level` accepts `Union[int, str]`; the F2P test passes only `int` levels (41, 43), and `logging` normalizes a level to the int that `self.handler.level` then reports. Modeled as `Int`. (flag note below.) |
| the handler level at fixture creation | `lvl0 : Int` parameter of `initStep` | a freshly-created `LogCaptureHandler` has `level == 0` (`logging.Handler` default `NOTSET`); the F2P test asserts `caplog.handler.level == 0` on entry. `lvl0` is that ambient level; the test exercises `lvl0 = 0`, the model is general over `lvl0 : Int`. |

Modeling note — **`level` normalization / `Union[int,str]`.** `set_level`'s
`level` may be a string name; the real code calls `logging.getLevelName`-style
normalization indirectly via `setLevel`, and `self.handler.level` always reads
back an `int`. The F2P test (and this model) use integer levels only, where
`self.handler.level == level`. String levels are out of scope for the modeled
property (they do not change the save/restore data-flow this fix is about); the
G-CONF shadow fuzzes integer levels, matching the F2P regime.

Modeling note — **second-set-within-a-test.** `set_level` records
`self._initial_handler_level = self.handler.level` on **every** call (it is a
plain assignment, NOT a `setdefault`). So a second `set_level` in the same test
overwrites the saved value with the level the first set established — teardown
then restores to *that*, not to the original ambient level. `setLevelState`
reproduces this exactly (`savedLevel := some st.level`, unconditional
overwrite), distinguishing it from the sibling `_initial_logger_levels`
dictionary which uses `setdefault`. G-CONF fuzzes multi-set sequences to pin
this.

## 3. Callee provenance (deep models — NOT axioms)

This fix changes no foreign callee; it rewires the fixture's own retained-level
data-flow (`self.handler.setLevel(...)` / `self.handler.level` are the touched
handler ops, and `self._initial_handler_level` is a plain instance attribute).
Accordingly there are **no consumed axioms and no deep-model references to a
foreign callee** (`axioms` region is empty; `meta.json axioms = []`,
`deep_model_references = []`). `initState`, `setLevelState`, and `restoreState`
are *deep models of the three code paths the patch edits*, not of unchanged
callees:

- `initState` models `__init__`'s added line `self._initial_handler_level = None`
  (`logging.py:348` post-patch): a fresh fixture records nothing to reinstate
  (`savedLevel := none`), in effect at the ambient handler level.
- `setLevelState` models `set_level`'s added line
  `self._initial_handler_level = self.handler.level` *before*
  `self.handler.setLevel(level)` (`logging.py:440–441` post-patch): record the
  level currently in effect, then move to the requested level.
- `restoreState` models `_finalize`'s added guard
  `if self._initial_handler_level is not None: self.handler.setLevel(self._initial_handler_level)`
  (`logging.py:357–358` post-patch): reinstate the recorded level on the `some`
  branch; leave the fixture untouched on the `none` branch (no level was set).

Because these model the **changed** operations, they are exercised end-to-end by
G-CONF against the patched real `LogCaptureFixture` (§4 below), not by an axiom
check. There is no `axiom_check.py` in this bundle (G-AX skips: no axioms).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`7571`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds is the
transliteration of `initState`/`setLevelState`/`restoreState`/`runLifecycle`
(all R/I-tagged ops, no A-tagged callee in the computed output) to Python over
the real `LogCaptureFixture`: it constructs a real fixture against a dummy item,
drives `set_level(...)` (one or more times) and then `_finalize()`, and reads
`fixture.handler.level`, comparing against the shadow's
`restoreState ∘ setLevelState* ∘ initState`. Inputs span: the ambient level
(no set → `_finalize` is a no-op), a single set, and randomized multi-set
sequences (pinning the unconditional-overwrite save semantics).
