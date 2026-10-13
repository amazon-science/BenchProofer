# mapping.md — pytest-dev__pytest-8399

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 6e7dc8bac831cd8cf7a53b08efa366bd84f0c0fe`, states the type
abstraction, and gives the provenance of the one A-reference deep model (the
fixture-listing visibility rule).

Repo files under change: `src/_pytest/python.py`, `src/_pytest/unittest.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `generated_fixture_name(label)` | the `name=f"..._fixture_{...}"` keyword of each auto-generated xunit/unittest fixture — `src/_pytest/unittest.py:147` (`_make_xunit_fixture`); `src/_pytest/python.py:531` (`_inject_setup_module_fixture`), `:560` (`_inject_setup_function_fixture`), `:812` (`_inject_setup_class_fixture`), `:841` (`_inject_setup_method_fixture`) | the modeled changed behaviour: how the generated fixture name is formed (the patch prepends `_` to every one of these five name f-strings) |
| `listed(name, verbose)` *(deep model — A-reference)* | the fixture-listing visibility rule — `src/_pytest/python.py:1511` (`_showfixtures_main`, reached by `pytest --fixtures`) and `:1429` (`_show_fixtures_per_test`) | unchanged framework logic: a fixture is omitted at default verbosity exactly when its name begins with `_`; modeled deeply, validated `listed == real rule` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `begins_private(name)` | the predicate `argname[0] == "_"` / `argname.startswith("_")` inside that rule (`python.py:1511`, `:1429`) | pure spec: a name begins with the privacy marker |
| `PRIVACY_MARKER` | the literal `"_"` (the leading char the fix adds; the char tested by the listing rule) | pure spec: code point U+005F = 95 |

The five gold name f-strings at base_commit (the descriptive labels, before the
fix prepends `_`):

| site | base_commit name f-string |
|---|---|
| `unittest.py:147` | `f"unittest_{setup_name}_fixture_{obj.__qualname__}"` |
| `python.py:531` | `f"xunit_setup_module_fixture_{self.obj.__name__}"` |
| `python.py:560` | `f"xunit_setup_function_fixture_{self.obj.__name__}"` |
| `python.py:812` | `f"xunit_setup_class_fixture_{self.obj.__qualname__}"` |
| `python.py:841` | `f"xunit_setup_method_fixture_{self.obj.__qualname__}"` |

Each is the abstract `label` of the model: a non-empty descriptive string whose
first character is an ordinary letter (`u` or `x`), never `_`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the generated fixture name `str` (the f-string value) | `List[int]` of Unicode code points | `s[k]` ↔ `name[k] == ord(s[k])`; `len(s)` ↔ `len(name)`; `str` concatenation ↔ list `+`; the prepended `"_"` ↔ `[95]` |
| a name `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| the descriptive label `f"unittest_{setup}_fixture_{qualname}"` etc. | `label: List[int]` (an input, non-empty, first code point ≠ 95) | the framework computes this from the hook name + the object's qualname; the model treats it as an opaque descriptive label — the fix touches only the leading marker, not the label content |
| the verbosity level `config.getvalue("verbose")` (an `int`) | `verbose: int` | identical; the rule branches on `verbose > 0` vs `verbose <= 0` |
| `argname[0] == "_"` / `argname.startswith("_")` on a non-empty name | `name[0] == 95` on `len(name) > 0` | identical predicate on code points |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

### Termination obligation (total correctness)

`generated_fixture_name` carries `Requires(MustTerminate(len(label) + 2))`: the
real name construction is a single f-string evaluation that always returns the
name to the `@pytest.fixture(name=...)` decorator during collection — it never
diverges. Under Nagini's default partial-correctness semantics an
implementation that computes the right name and then loops forever would
satisfy every `Ensures` vacuously while never registering the fixture (so the
`--fixtures` F2P would never pass); the obligation rejects any such
implementation. The measure `len(label) + 2` bounds the one pass over the
finite label plus constant work; the impl loop discharges it with the strictly
decreasing invariant `MustTerminate(len(label) - i + 1)`.

## 3. Deep-model reference (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `listed` deep model ↔ the fixture-listing visibility rule
**Reference (unchanged framework logic):** the `--fixtures` listing applies, at
`src/_pytest/python.py:1511` (`_showfixtures_main`):

```python
if verbose <= 0 and argname[0] == "_":
    continue          # fixture omitted from the listing
```

and equivalently at `src/_pytest/python.py:1429` (`_show_fixtures_per_test`):

```python
if verbose <= 0 and argname.startswith("_"):
    return            # fixture omitted
```

So a fixture is **omitted at the default verbosity** (`verbose <= 0`) exactly
when its name's first character is `_`, and **always shown** at a raised
verbosity (`verbose > 0`). The patch does not change this rule — it is modeled
**deeply** by the pure predicate `listed` (and `begins_private`); there is **no
`@ContractOnly` axiom** the proof consumes. The deep model is validated equal to
both real rule expressions out-of-band by axiom_check.py (G-AX) over 17 boundary
+ 20000 fuzz names at five verbosity levels, plus the end-to-end fix effect
(prepending `_` flips the real filter from shown→omitted at default verbosity,
shown at verbose) over 8 real labels + 20000 fuzz labels. Both `--fixtures`
display functions index `argname[0]`, so they require a non-empty name; the
model carries `len(label) > 0` as a precondition (the labels are non-empty
f-strings).

This A-reference depends on no flags. The discriminating behaviour the F2P test
observes — the generated fixture is absent under `pytest --fixtures` (no
"no docstring available" line) but present under `pytest --fixtures -v` — is
precisely `not listed(name, 0)` and `listed(name, 1)`, which hold iff the
generated name begins with `_`. There is no consumed axiom and no stdlib callee:
the only repo logic referenced is framework-internal and unchanged, validated by
G-AX.
