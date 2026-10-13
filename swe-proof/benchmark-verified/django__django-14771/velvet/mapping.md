# mapping.md — django__django-14771

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 4884a87e022056eda10534c13d74e49b8cdda632`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance. There are **no axioms** in this bundle (the changed region
calls no library function whose behaviour the proof must assume); every step is
**R** (type refinement) or **I** (identical concrete op).

Repo file under change: `django/utils/autoreload.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `relaunchArgv (executable warnopts isCpython xopts argv)` | `get_child_arguments()` — `django/utils/autoreload.py:213` (the `args = [...] + [...]` block, line 222, and the `__spec__`/`else` argv tail) | the modeled changed function: builds the argument vector used to relaunch the interpreter under the reloader |
| `relaunchArgvSpec` *(pure, deep model)* | the same argument-vector construction, post-patch (lines 222 and the inserted `if sys.implementation.name == 'cpython': args.extend(...)` block, lines 223–227) | pure spec: the full argument vector, given the five inputs |
| `warnFlag (o : List Char)` *(pure)* | the pre-existing `'-W%s' % o for o in sys.warnoptions` comprehension (`autoreload.py:222`) | per-warning-option serialization (`-W` + option), unchanged by the patch |
| `xFlag (kv : List Char × XVal)` *(pure)* | the inserted `f'-X{key}' if value is True else f'-X{key}={value}'` generator (`autoreload.py:225–226`) | per-X-option serialization (`-Xkey` / `-Xkey=value`) |
| `XVal` (`bare` / `eq value`) *(pure)* | the value of a `sys._xoptions` entry: `True` (bare `-X` switch) vs. a string (`-X` with a value) | the two shapes a runtime X-option value takes |

The inputs of `relaunchArgv` correspond to these reads in `get_child_arguments`:

| model parameter | repo expression | repo line @ base_commit | added by patch? |
|---|---|---|---|
| `executable` | `sys.executable` | autoreload.py:222 (`[sys.executable]`) | no — pre-existing, unchanged |
| `warnopts` | `sys.warnoptions` | autoreload.py:222 (`['-W%s' % o for o in sys.warnoptions]`) | no — pre-existing, unchanged |
| `isCpython` | `sys.implementation.name == 'cpython'` | added at autoreload.py:223 | **yes** |
| `xopts` | `sys._xoptions.items()` | added at autoreload.py:226 | **yes** |
| `argv` | `sys.argv[1:]` / `sys.argv` (the trailing program args added in the `__spec__`/`else` branches) | autoreload.py:233, 235, 247 | no — pre-existing, unchanged |

The terms `-X` options, the `cpython` implementation, and `sys._xoptions` are
quoted verbatim in the public `problem_statement` (title + body + the
`https://docs.python.org/3/library/sys.html#sys._xoptions` reference), so naming
the *behaviour* in those terms is not leakage; the patched file/function names
(`autoreload` / `get_child_arguments`) are NOT named in the spec view.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a command-line argument `str` (`sys.executable`, an element of `sys.argv`, a produced `-W…`/`-X…` flag) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `str` concat (`%`, `f''`, `+`) ↔ `List` `++`; empty `str` ↔ `[]` |
| the argument vector (`args` list / the function's return list) | `List (List Char)` | order-preserving list of argument strings; `list + list` ↔ `++`; `list.extend(gen)` ↔ `++ (… .map …)` |
| `sys.warnoptions` (a `list[str]`) | `warnopts : List (List Char)` | element-wise `str ↔ List Char`; order preserved |
| `sys.implementation.name == 'cpython'` (a `bool`) | `isCpython : Bool` | `True ↔ true`, `False ↔ false` |
| `sys._xoptions` (an insertion-ordered `dict[str, True|str]`) | `xopts : List (List Char × XVal)` | the dict's `.items()` in iteration order ↔ the list of `(key.toList, XVal)` pairs, order preserved; a value of `True` ↔ `XVal.bare`; a value that is a `str v` ↔ `XVal.eq v.toList` |
| `f'-X{key}' if value is True else f'-X{key}={value}'` | `xFlag` | `value is True` ↔ `XVal.bare` (⇒ `-X` ++ key); else `-X` ++ key ++ `=` ++ value ↔ `XVal.eq value` |
| `'-W%s' % o` | `warnFlag o` | `-W` ++ option text |

### `sys._xoptions` value-shape note (used by G-CONF / model fidelity)

CPython's `sys._xoptions` maps each `-X` option name to `True` when the option
was given with no `=value` (a bare `-Xname`), and to the value string otherwise
(`-Xname=value` → `'value'`). The `XVal` carrier models exactly these two cases;
`xFlag` reproduces the patch's `value is True` test (note: identity, `is True`,
not truthiness — a value of the string `"True"` is keyed, not bare, and G-CONF
exercises this).

## 3. Callee provenance

**None consumed.** The changed region calls no library function whose result the
proof must assume: the construction is a closed function of the five inputs (a
list comprehension over `warnoptions`, an implementation-name equality test, a
generator over `_xoptions.items()`, and list concatenation — all transliterated
I/R ops). `Path(sys.argv[0])`, `getattr(__main__, '__spec__', None)`,
`py_script.exists()`, and `subprocess.run` are unchanged by the patch and are not
part of the X-option-forwarding behaviour the F2P test (`test_xoptions`) observes
(that test mocks `sys.argv`, `sys.warnoptions`, and `sys._xoptions` and inspects
the returned argument list directly). Hence there is **no `axiom`, no deep-model
A-reference, and no `axiom_check.py`** (G-AX = skip). All refinement legs are R/I,
fully covered by G-CONF.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14771`** so the
consumer-side verdict is reproducible. The ORACLE runs the **real patched**
`get_child_arguments()` in-container (mocking `sys.argv`, `sys.warnoptions`,
`sys._xoptions`, `sys.executable`, `sys.implementation.name`, and
`__main__.__spec__` exactly as `tests/utils_tests/test_autoreload.py`'s
`TestChildArguments` does) and captures the returned argument list. The SHADOW
transliterates `relaunchArgvSpec` (R/I ops) to Python over the real `str` type.
They must agree on every fuzzed configuration.
