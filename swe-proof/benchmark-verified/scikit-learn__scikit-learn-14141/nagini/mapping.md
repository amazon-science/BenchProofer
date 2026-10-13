# mapping.md — scikit-learn__scikit-learn-14141

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 3d997697fdd166eff428ea9fd35734b6a8ba113e`, states the type
abstraction, and gives the provenance of the one axiom.

Repo file under change: `sklearn/utils/_show_versions.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `collect_deps_versions()` | `_get_deps_info()` — `sklearn/utils/_show_versions.py:33` (roster literal at line 42, population loop at lines 58-67) | the modeled changed function (dependency-version reporter) |
| `version_of(name)` *(axiom — A-consumed)* | the per-module version observation: `mod = sys.modules[modname]` or `importlib.import_module(modname)` then `get_version(mod) == mod.__version__`, with the `ImportError` fallback `None` (`sklearn/utils/_show_versions.py:54,59-67`) | unchanged opaque callee invoked once per rostered name; its returned value is not observed by the tested behaviour |
| `name_pip()` | the roster string literal `"pip"` (`_show_versions.py:43`) | name token |
| `name_setuptools()` | `"setuptools"` (`:44`) | name token |
| `name_sklearn()` | `"sklearn"` (`:45`) | name token |
| `name_numpy()` | `"numpy"` (`:46`) | name token |
| `name_scipy()` | `"scipy"` (`:47`) | name token |
| `name_cython()` | `"Cython"` (`:48`) | name token |
| `name_pandas()` | `"pandas"` (`:49`) | name token |
| `name_matplotlib()` | `"matplotlib"` (`:50`) | name token |
| `name_parallel()` | `"joblib"` — the roster entry the gold patch adds after `"matplotlib"` (`:51` post-patch) | the parallel-execution dependency name token; the discriminating roster member |

The pre-patch roster (`deps`, lines 42-51) lists eight names and omits
`"joblib"`; the gold patch inserts `"joblib"` as the ninth entry. The population
loop `for modname in deps: deps_info[modname] = <version or None>` (lines 58-67)
is unchanged — adding the name to the roster is what makes `"joblib"` a key of
the returned dict.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| dependency module name (`str` literal in `deps`) | `int` identity token (`name_*()` constants 0..8) | distinct names ↔ distinct ints; the only relation the tested behaviour observes is name identity and which names are keys of the result. `str` indexing is banned in Nagini, and the name's spelling is never inspected — only its identity and key-presence — so an integer identity token is the faithful carrier. |
| the version string (`mod.__version__`) or `None` | `int` version marker (opaque) | the F2P/P2P tests observe only the *presence* of each name as a key, never the value; the marker is an opaque carrier for whatever `version_of` returns. |
| `deps_info` dict (`Dict[str, Optional[str]]`) | `Dict[int, int]` (name token → version marker) | `k in deps_info` ↔ `name_token in Result()`; per-key value ↔ `Result()[name_token]`. |
| `for modname in deps:` over a static 8/9-element literal | the per-name population, spelled out one assignment per roster entry | the roster has fixed, statically known membership; iterating it and unrolling it populate the same key/value pairs (refinement.md A1-A3). |
| the call COMPLETES: `_get_deps_info()` returns its dict — ordinary Python evaluation of loop-free straight-line code | `Requires(MustTerminate(2))` on `collect_deps_versions` | the real routine is bounded straight-line work (static list, dict population with per-name try/except, return), so every call terminates; the obligation pins that an implementation may not DIVERGE instead of answering. Nagini verifies partial correctness by default (no termination proof required), so without this obligation a non-terminating body (`while b: Invariant(True)`) satisfies every `Ensures` vacuously while a real `_get_deps_info` that hangs would time out the F2P — the recorded G-PANEL-1/G-EQ witness class this obligation closes (refinement.md A4). |

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `version_of` ↔ the per-module version observation (A-consumed)
**Callee:** for each rostered name the routine does (lines 58-67):
```python
if modname in sys.modules:
    mod = sys.modules[modname]
else:
    mod = importlib.import_module(modname)   # may raise ImportError
ver = get_version(mod)                       # get_version(m) == m.__version__
deps_info[modname] = ver                     # except: deps_info[modname] = None
```
`version_of(name)` models this whole observation as a total opaque function
returning an `int` version marker (the import-failure path is folded into the
marker domain — a module that cannot be imported yields its own marker value,
mirroring the `None` the `except ImportError` branch stores). The axiom's
contract is the **weakest** the proof needs: `Ensures(True)` — the proof never
relies on any property of the returned value, only on the fact that *some*
value is stored under each rostered key. The tested behaviour
(`test_get_deps_info`) checks `name in deps_info`, never the value, so no
stronger contract is warranted; a stronger one would over-claim.

**Why no raise/exception obligation:** `version_of` is total by construction —
the real routine wraps the import + version read in `try/except ImportError`
and always stores a value (the version or `None`), so from the caller's
perspective every rostered name ends up as a key carrying a value. Modeling
`version_of` as a total `int`-valued function is therefore sound: it cannot
remove a key or raise out of the population step.

**Soundness check (G-AX):** `axiom_check.py` imports the real
`sklearn.utils._show_versions._get_deps_info`, runs it, and asserts (a) every
rostered name — including `"joblib"` — is a key of the returned dict (the
`version_of`-totality property the model relies on: each rostered name becomes a
key carrying a value, never absent), and (b) the result has no key outside the
roster. It also checks the boundary where a dependency is absent (the value is
`None` but the key is still present), confirming the `version_of`-as-total
modeling. stdlib + the installed `sklearn` only; exit 0 iff sound.
