# mapping.md — pytest-dev__pytest-8399

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 6e7dc8bac831cd8cf7a53b08efa366bd84f0c0fe`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
provenance. There are **no axioms** in this bundle (the generated identifier is
built purely from a given descriptive label; no external callee is consulted),
so there is no `axiom_check.py` and G-AX auto-skips.

Repo files under change: `src/_pytest/unittest.py`, `src/_pytest/python.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `privatizeName (base : List Char)` | the fixture-name construction `name=f"unittest_{setup_name}_fixture_{obj.__qualname__}"` inside `_make_xunit_fixture` — `src/_pytest/unittest.py:147` | the modeled changed operation: produce the generated helper's lookup identifier; the gold prepends a leading `_` |

The same textual operation occurs at four further sites in
`src/_pytest/python.py` (the xunit-style equivalents). They are **not** modeled
separately because they are byte-for-byte the *identical* operation
(`name = "_" + base`) and the F2P-graded behavior is exercised at the
`unittest.py` site (see §3). They are recorded for the refinement audit only:

- `src/_pytest/python.py:530` — `name=f"xunit_setup_module_fixture_{self.obj.__name__}"`
- `src/_pytest/python.py:559` — `name=f"xunit_setup_function_fixture_{self.obj.__name__}"`
- `src/_pytest/python.py:811` — `name=f"xunit_setup_class_fixture_{self.obj.__qualname__}"`
- `src/_pytest/python.py:840` — `name=f"xunit_setup_method_fixture_{self.obj.__qualname__}"`

### Unchanged downstream consumer (the *reason* the prefix matters — not modeled)
`_pytest.python._showfixtures_main` / `write_fixture` (`python.py:1429`,
`python.py:1511`) skip any fixture whose registered name begins with `_` unless
verbosity > 0:

```python
if verbose <= 0 and argname.startswith("_"):
    return            # hidden from the default `--fixtures` listing
```

This routine is **unchanged** by the patch; it is the existing privatization
convention the fix relies on. The modeled operation's postcondition
(`out.head? = some '_'`) is exactly the property this consumer keys on.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the generated-name string (the `name=...` f-string value, and its `base` body) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; `str` concat ↔ `List` `++`; the single literal char `'_'` ↔ Lean `'_'`; a one-char prefix `"_" + s` ↔ `'_' :: l` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |

`base` (the descriptive label, e.g. `unittest_setUpClass_fixture_Tests`) is the
pre-patch generated name; the modeled operation maps it to `'_' :: base`. The
carrier is `List Char` because the operation is a per-code-point string build
(a single front cons), and Lean `List Char` indexing/`head?` is total and sound.

## 3. F2P provenance & call-site configurations

The graded behavior `testing/test_unittest.py::test_fixtures_setup_setUpClass_issue8394`
runs `pytest --fixtures` on a `unittest.TestCase` defining `setUpClass`, and
asserts the generated `setUpClass` fixture is hidden by default
(`no_fnmatch_line("*no docstring available*")`) yet shown under `-v`. That
fixture's name is produced by `_make_xunit_fixture(... "setUpClass" ...)` — the
exact callee `privatizeName` models. The two real invocations of the callee are:

| `setup_name` | `teardown_name` | `cleanup_name` | `scope` | `pass_self` | base label `base` |
|---|---|---|---|---|---|
| `setUpClass` | `tearDownClass` | `doClassCleanups` | `class` | `False` | `unittest_setUpClass_fixture_{qualname}` |
| `setup_method` | `teardown_method` | `None` | `function` | `True` | `unittest_setup_method_fixture_{qualname}` |

G-CONF fuzzes both configurations and many `__qualname__` values, reading the
registered lookup name off the generated fixture
(`fixture._pytestfixturefunction.name`) — the identifier the listing keys on.

No flag dependency affects the name construction itself: the `name=` keyword is
passed unconditionally, so G-CONF does not need a flag matrix for the callee.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`8399`** so the
consumer-side verdict is reproducible. The shadow transliterates `privatizeName`
(the sole R/I op, `'_' :: base` → `"_" + base`) to Python; the oracle is the
patched `_pytest.unittest._make_xunit_fixture` (gold patch applied in-container).
There are no A-tagged callees to leave as real, so the comparison is pure R/I.
