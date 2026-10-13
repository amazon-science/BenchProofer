# mapping.md — django__django-13837

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 415f50298f97fb17f841a9df38d995ccf347dfcc`, states the type
abstraction, and gives the provenance of the one A-reference (an unchanged
runtime/library primitive the deep model is validated against by G-AX).

Repo file under change: `django/utils/autoreload.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `child_arguments(prefix, launch_package, argv, script_exists)` | `get_child_arguments()` — `django/utils/autoreload.py:213` (body lines 219-246) | the modeled changed function: builds the reloader child process's argument vector |
| `launch_package: Optional[List[int]]` | the launch-package name, i.e. `__main__.__spec__.parent` when `__main__.__spec__ is not None`, else absent — `django/utils/autoreload.py:222-225` (post-patch `__main__.__spec__`/`.parent`) | the package a module-launch (`python -m PKG`) reports; `None` ↔ not a module launch |
| `argv: List[List[int]]` | `sys.argv` — `django/utils/autoreload.py:221` (`Path(sys.argv[0])`), 226/227/245 | the process argument vector; `argv[0]` the script, `argv[1:]` the program arguments |
| `prefix: List[List[int]]` | `[sys.executable] + ['-W%s' % o for o in sys.warnoptions]` — `django/utils/autoreload.py:223` | the fixed leading arguments (interpreter + warning options) every branch prepends |
| `script_exists: bool` | `Path(sys.argv[0]).exists()` — `django/utils/autoreload.py:228` | whether the entry script path exists on disk (gate for the Windows fallbacks) |
| `dash_m()` | the literal `'-m'` (`django/utils/autoreload.py:226`) | pure spec: the module-execution flag token as code points |
| `is_module_launch(launch_package)` *(deep model — A-reference)* | the predicate `__main__.__spec__ is not None and __main__.__spec__.parent` — `django/utils/autoreload.py:224` | pure spec: a module launch is detected iff a non-empty launch package is reported; validated against the real `__main__.__spec__` semantics by axiom_check.py (G-AX), NOT consumed as an axiom |

The pre-patch repo behaviour the change corrects (for the refinement audit, not
referenced from the consumer spec view): at `autoreload.py:219-227` the entry
point detected a module launch only by `py_script == Path(django.__main__.__file__)`
— i.e. only when the script path equalled Django's own `__main__.py` — and then
emitted the *literal* package name `'django'` (`args += ['-m', 'django']`). A
module launched as `python -m PKG` for any `PKG` other than `django` did not
match that path equality and fell through to the final `else: args += sys.argv`
branch, losing the `-m PKG` form entirely.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (package names, argv elements, the `'-m'` flag) | `List[int]` of Unicode code points | `s[k]` ↔ `text[k] == ord(s[k])`; `len(s)` ↔ `len(text)`; an empty `str` ↔ `[]`; equality of `str` ↔ `PSeq` equality via `ToSeq` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `list` of `str` (`sys.argv`, the built args, the prefix) | `List[List[int]]` of code-point lists | element `argv[i]` ↔ a `List[int]`; `list` concatenation `+` ↔ `PSeq` `+`; `argv[1:]` ↔ `ToSeq(argv).drop(1)` |
| `list[str]` value inside a specification | `PSeq[PSeq[int]]` | `ToSeq(list_of_lists)` materializes each element via the element type's `ToSeq` |
| `__main__.__spec__` (only its `.parent`, and its `None`-ness, observed) | `launch_package: Optional[List[int]]` | `__spec__ is None` ↔ `launch_package is None`; `__spec__.parent` ↔ the code points of `launch_package` (a directory/zip launch gives parent `""` ↔ `launch_package == []`) |
| `Path(sys.argv[0]).exists()` | `script_exists: bool` | a pure boolean observation; the model carries it as a parameter |

`str` indexing/iteration is banned in Nagini, so every string carrier is
`List[int]`; the argument vector is `List[List[int]]`; the specification is
phrased over `PSeq[int]` / `PSeq[PSeq[int]]` via `ToSeq`. The Windows-specific
`.exe`/`-script.py` fallbacks (`autoreload.py:231-243`) are UNCHANGED by the
patch; the model represents that whole branch abstractly by the single
`script_exists` guard and a sentinel result, since neither the issue nor the
F2P test exercises it (it is PASS_TO_PASS and identical pre/post patch).

## 3. The decisive predicate / deep-model reference (A-reference, checked by G-AX)

### 3.1 `is_module_launch` deep model ↔ `__main__.__spec__` semantics

**Reference:** the runtime/import-system rule the patch relies on, per the
CPython documentation
(https://docs.python.org/3/reference/import.html#main-spec):

> `__main__.__spec__` is set (not `None`) **iff** Python was launched with `-m`
> or with the name of a directory / zipfile / `sys.path` entry. In the `-m PKG`
> case `__main__.__spec__.parent` is `PKG`; in the directory/zipfile case the
> parent is the empty string `""`.

Hence "Python was started with `-m PKG`" holds **iff**
`__main__.__spec__ is not None and __main__.__spec__.parent` is a non-empty
string equal to `PKG`. The patch's branch guard `__main__.__spec__ is not None
and __main__.__spec__.parent` is exactly this predicate, and the emitted package
is exactly `__main__.__spec__.parent`. The change is therefore modeled **deeply**:
`is_module_launch(launch_package) == (launch_package is not None and
len(launch_package) > 0)` and the emitted module name is `launch_package`
itself — there is **no consumed axiom** standing in for the changed branch. The
deep model is validated against the real runtime semantics out-of-band by
axiom_check.py (G-AX), which constructs real `ModuleSpec` objects (the very
objects `__main__.__spec__` is) for the `-m PKG`, directory-launch, and
script-launch cases and asserts the predicate + emitted-name agree.

**Soundness check (G-AX):** `axiom_check.py` builds real
`importlib.machinery.ModuleSpec` instances (and the genuine `None` spec for a
plain `python script.py` launch) for representative launch shapes — `-m pkg`,
`-m pkg.sub`, `-m django`, a bare directory/zip launch (parent `""`), and the
no-spec script launch — and asserts that `__spec__ is not None and
__spec__.parent` and the resulting child argument vector match the model. It
imports only the standard library (`importlib.machinery`); nothing
repo-specific. Exit 0 iff sound.

There are **no consumed `@ContractOnly` axioms** in this bundle: the only
unchanged-callee-shaped construct is the `__main__.__spec__`/`.parent` access,
which IS the changed predicate and is therefore modeled deeply (A-reference),
not consumed.
