# mapping.md — django__django-14771

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 4884a87e022056eda10534c13d74e49b8cdda632`, states the type
abstraction, and gives the provenance of the one A-reference (an unchanged
runtime primitive the deep model is validated against by G-AX).

Repo file under change: `django/utils/autoreload.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `child_arguments(prefix, is_reference_impl, opt_keys, opt_is_flag, opt_vals, package_reported, launch_package, argv, script_exists)` | `get_child_arguments()` — `django/utils/autoreload.py:213` (body lines 219-248) | the modeled changed function: builds the reloader child-process argument vector |
| `prefix: PSeq[PSeq[int]]` | `[sys.executable] + ['-W%s' % o for o in sys.warnoptions]` — `django/utils/autoreload.py:222` | the fixed leading arguments (interpreter path + warning options) every branch prepends, built before the new forwarding step; unchanged by the patch |
| `is_reference_impl: bool` | `sys.implementation.name == 'cpython'` — post-patch `autoreload.py:223` | whether the running interpreter is the reference C implementation; the guard the new forwarding step is gated on |
| `opt_keys: PSeq[PSeq[int]]` | the keys of `sys._xoptions` (a dict), in iteration order — post-patch `autoreload.py:226` (`for key, value in sys._xoptions.items()`) | the supplied implementation-option NAMES |
| `opt_is_flag: PSeq[bool]` | the per-option predicate `value is True` — post-patch `autoreload.py:225` | true iff the option's value is the present-with-no-value sentinel `True` |
| `opt_vals: PSeq[PSeq[int]]` | the values of `sys._xoptions`, in iteration order (meaningful only where `opt_is_flag` is false) — post-patch `autoreload.py:226` | the supplied implementation-option VALUES |
| `package_reported: bool` | `getattr(__main__, '__spec__', None) is not None` — `autoreload.py:226` (pre/post-patch identical) | whether a launch package was reported (module launch) |
| `launch_package: PSeq[int]` | the module name selected from `__main__.__spec__` (`spec.parent` or `spec.name`) — `autoreload.py:227-232` | the package re-invoked on a module launch; unchanged by this patch |
| `argv: PSeq[PSeq[int]]` | `sys.argv` — `autoreload.py:220` (`Path(sys.argv[0])`), 233/247 | the process argument vector; `argv[0]` the script, `argv[1:]` the program arguments |
| `script_exists: bool` | `py_script.exists()` i.e. `Path(sys.argv[0]).exists()` — `autoreload.py:234` | whether the entry script path exists on disk (gate for the Windows fallbacks) |
| `dash_x()` | the option flag `'-X'` in the f-strings `f'-X{key}'` / `f'-X{key}={value}'` (`autoreload.py:225`) | pure spec: the implementation-option flag token as code points (`PSeq(45,88)`) |
| `eq()` | the `'='` in `f'-X{key}={value}'` (`autoreload.py:225`) | pure spec: the name/value separator (`PSeq(61)`) |
| `dash_m()` | the literal `'-m'` (`autoreload.py:232`) | pure spec: the module-execution flag token as code points (`PSeq(45,109)`); unchanged |
| `option_token(key, is_flag, val)` *(deep model — A-reference)* | one element produced by the generator `f'-X{key}' if value is True else f'-X{key}={value}'` (`autoreload.py:225`) | pure spec: the single token forwarded for one option |
| `option_tokens(keys, flags, vals)` *(deep model — A-reference)* | `args.extend(<generator over sys._xoptions.items()>)` — `autoreload.py:224-227` | pure spec: the whole forwarded-option token list; validated against the real `sys._xoptions` / `sys.implementation.name` semantics by axiom_check.py (G-AX), NOT consumed as an axiom |
| `is_module_launch(package_reported, launch_package)` | the unchanged module-launch predicate at `autoreload.py:226-232` | pure spec: a module launch is detected iff a non-empty launch package is reported; unchanged by this patch |

The pre-patch repo behaviour the change corrects (for the refinement audit, not
referenced from the consumer spec view): at `autoreload.py:222` the leading
arguments were `[sys.executable] + ['-W%s' % o for o in sys.warnoptions]` and
the implementation options carried on the original command line were **never
forwarded** to the child — there was no `sys._xoptions` step at all between the
warning-options line and the `__spec__` branch.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (option names/values, argv elements, the `'-X'`/`'-m'`/`'='` literals) | `List[int]` of Unicode code points (specs over `PSeq[int]`) | `s[k]` ↔ `ord(s[k])`; `len(s)` ↔ `len`; empty `str` ↔ empty seq; `str` `+`/equality ↔ `PSeq` `+`/equality |
| `list` of `str` (`sys.argv`, the built `args`, the prefix, the forwarded tokens) | `List[List[int]]` / `PSeq[PSeq[int]]` | element `args[i]` ↔ a code-point seq; `list` `+`/`extend` ↔ `PSeq` `+`; `sys.argv[1:]` ↔ `argv.drop(1)` |
| `sys._xoptions` (a `dict` iterated by `.items()`) | three index-aligned pure sequences `opt_keys`, `opt_is_flag`, `opt_vals` of equal length | the i-th `.items()` pair `(key, value)` ↔ (`opt_keys[i]`, value); `value is True` ↔ `opt_is_flag[i]`; `value` (when not the sentinel) ↔ `opt_vals[i]`. Iteration order is the dict's insertion order, preserved as the sequence order (the F2P relies on `{'utf8': True, 'a': 'b'}` → `['-Xutf8', '-Xa=b']`). |
| the f-string `f'-X{key}'` | `dash_x() + key` | string interpolation of a flag-only option ↔ seq concatenation |
| the f-string `f'-X{key}={value}'` | `dash_x() + key + eq() + val` | string interpolation of a name=value option ↔ seq concatenation |
| `value is True` | `is_flag: bool` | identity-test against the boolean `True` sentinel; a present-with-no-value `-X` option has value `True` in `sys._xoptions` |
| `sys.implementation.name == 'cpython'` | `is_reference_impl: bool` | a pure boolean observation carried as a parameter |
| `Path(sys.argv[0]).exists()` | `script_exists: bool` | a pure boolean observation carried as a parameter |

`str` indexing/iteration is banned in Nagini, so every string carrier is
`List[int]` and the argument vector / option lists are `PSeq[PSeq[int]]`; the
specification is phrased via `ToSeq`. The Windows-specific `.exe`/`-script.py`
fallbacks (`autoreload.py:234-245`) are UNCHANGED by the patch; the model
represents that whole branch abstractly by the single `script_exists` guard and
a sentinel result, since neither the issue nor the F2P test exercises it (it is
PASS_TO_PASS and identical pre/post patch). The module-launch package selection
(`spec.parent`/`spec.name`) is likewise unchanged by THIS patch and is carried
abstractly by `launch_package`.

## 3. The decisive forwarding / deep-model reference (A-reference, checked by G-AX)

### 3.1 `option_tokens` deep model ↔ the `sys._xoptions` forwarding rule

**Reference:** the CPython runtime semantics the patch relies on, per the
documentation (https://docs.python.org/3/library/sys.html#sys._xoptions):

> `sys._xoptions` is a dictionary of the various implementation-specific flags
> passed through the `-X` command-line option. An option given as `-Xname` has
> the value `True`; an option given as `-Xname=value` has the string `value`.
> `sys.implementation.name` is `'cpython'` on the reference interpreter.

Hence the child command line for the reference interpreter must re-supply each
recorded option as a single token: `-Xname` when the recorded value is the
boolean `True` (the option was given with no value), and `-Xname=value`
otherwise; on any other interpreter `sys._xoptions` is not re-forwarded (the
empty list). This is exactly what `option_tokens` / `option_token` encode:
`option_token(key, is_flag, val) == dash_x()+key` if `is_flag` else
`dash_x()+key+eq()+val`, folded over the option list in order, gated on
`is_reference_impl`. The change is therefore modeled **deeply**; there is **no
consumed axiom** standing in for the forwarding rule.

**Soundness check (G-AX):** `axiom_check.py` drives the REAL transformation —
the generator `f'-X{key}' if value is True else f'-X{key}={value}'` over real
`dict` objects exactly as `sys._xoptions.items()` is iterated, gated on
`sys.implementation.name == 'cpython'` — on boundary inputs (empty options, a
single flag, a single name=value, the F2P `{'utf8': True, 'a': 'b'}`, values
that look like `True`, integer-ish/odd values, the present-vs-False distinction)
plus randomized fuzz, and asserts every produced token list equals the model's
`option_tokens`. It also confirms the `value is True` identity-test (only the
boolean `True` sentinel, not a truthy string `'True'`, yields the flag form) and
that the running interpreter reports `sys.implementation.name == 'cpython'`. It
imports only the standard library (`sys`); nothing repo-specific. Exit 0 iff
sound.

There are **no consumed `@ContractOnly` axioms** in this bundle: the only
unchanged-runtime-shaped constructs are the `sys._xoptions` / `value is True` /
`sys.implementation.name` accesses, which ARE the changed forwarding and so are
modeled deeply (A-reference), never consumed.
