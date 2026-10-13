# mapping.md — pytest-dev__pytest-8399

## Symbol binding (file:line @ base_commit 6e7dc8bac831cd8cf7a53b08efa366bd84f0c0fe)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_generatedFixtureName` / `problem_spec_generatedFixtureName` / `correct_generatedFixtureName` | the `name=` keyword expression that names the synthesized setup–teardown fixture in `_make_xunit_fixture` | `src/_pytest/unittest.py:147` (the `name=f"…"` of the `@pytest.fixture(…)` decorator) |
| `descriptiveName` (pure helper) | the f-string template `f"unittest_{setup_name}_fixture_{obj.__qualname__}"` minus the patch's leading private marker | `src/_pytest/unittest.py:147` |
| `setupName : List Char` | `setup_name` (the setup-hook attribute name, e.g. `"setUpClass"`) | `_make_xunit_fixture` parameter, `unittest.py:124` |
| `qualname : List Char` | `obj.__qualname__` (the owning test-class's qualified name) | `unittest.py:147` |

## What the function does

`_make_xunit_fixture(obj, setup_name, teardown_name, …)` synthesizes a pytest
fixture that runs a unittest/xunit-style setup–teardown pair, and gives it a
unique name via the `@pytest.fixture(name=…)` keyword. At `base_commit` that name
is

```python
name=f"unittest_{setup_name}_fixture_{obj.__qualname__}"
```

so for `setUpClass` of class `MyTestCase` the fixture is named
`unittest_setUpClass_fixture_MyTestCase`.

### Consumer-side visibility (UNCHANGED by the patch — context, not modeled op)

`pytest --fixtures` lists fixtures via `write_fixture` /
`_showfixtures_main` in `src/_pytest/python.py`. Both hide a fixture at the
default verbosity exactly when its name begins with an underscore:

```python
# src/_pytest/python.py:1429
if verbose <= 0 and argname.startswith("_"):
    return
# src/_pytest/python.py:1511
if verbose <= 0 and argname[0] == "_":
    continue
```

A synthesized fixture has no docstring, so when it IS shown it prints
`no docstring available`. Since the generated names did NOT begin with `_`, they
leaked into the default `--fixtures` listing (the bug). The fix prepends `_` to
the generated name, making it private so it is hidden unless `-v` is passed. This
visibility rule is the consumer; it is unchanged by the patch and therefore is
context only — the modeled op is the name construction itself.

### The fix

The gold patch prepends a single `_` to the generated name at five sites — four
in `src/_pytest/python.py` (`xunit_setup_{module,function,class,method}_fixture_…`)
and one in `src/_pytest/unittest.py` (`unittest_{setup_name}_fixture_…`). All five
are the identical transformation `name → "_" + name`. The FAIL_TO_PASS test
`testing/test_unittest.py::test_fixtures_setup_setUpClass_issue8394` exercises the
`unittest.py` site (`setUpClass`), which is the one modeled here; the other four
are the same edit and are covered by G-CONF over arbitrary template/qualname
inputs.

## Lean modeling

The name is a pure per-code-point string built from the fixed template and the
two string inputs, so it is modeled as `List Char` (SPEC_GUIDE §2: per-code-point
string op → `List Char`, total/sound indexing). `descriptiveName setupName
qualname = "unittest_" ++ setupName ++ "_fixture_" ++ qualname` is the bare
(pre-fix) descriptive name; the post-fix name is `'_' :: descriptiveName …`. The
impl is the `Id.run do` skeleton appending the marker, the template head,
`setupName`, the template tail, and `qualname` in order — a line-for-line
skeleton of building the f-string with the leading `_`.

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `setup_name : str` | `setupName : List Char` | code-point list (identity over ASCII identifier chars) |
| `obj.__qualname__ : str` | `qualname : List Char` | code-point list |
| the resulting `name=` string | `result : List Char` | code-point list; `"".join` ↔ `List Char` |
| the f-string template literals `"unittest_"`, `"_fixture_"`, leading `"_"` | the corresponding `"…".toList` literals | identity |

## Callee provenance + flag dependencies

- **No consumed callee axiom and no A-reference.** The name is built entirely from
  literal string template parts and the two `List Char` inputs by concatenation;
  there is no unchanged repo callee in the modeled op. The `axioms` region is
  empty and **G-AX skips**.
- **No flag dependency.** The name expression is evaluated unconditionally inside
  the `@pytest.fixture(…)` decorator; it does not depend on scope/autouse/verbose.
  The consumer-side `verbose <= 0` visibility check is unchanged context, not part
  of the modeled op.

## G-CONF fuzz seed

Pinned LCG seed: **8399** (see `conformance_check.py` `SEED`). Corpus: random
`(setupName, qualname)` pairs over identifier-like character sets (letters,
digits, `_`, `.`, mixed case), including empty strings and long names, ≥1e5
inputs. The R/I shadow of `implementation_generatedFixtureName` is diffed against
an in-process replica of the POST-PATCH f-string `"_" + f"unittest_{setup_name}_
fixture_{obj.__qualname__}"`. Hand-picked edge cases: empty `setupName`/`qualname`,
the F2P scenario (`setupName="setUpClass"`, `qualname="MyTestCase"`), and a
qualname containing a dot (nested class).
