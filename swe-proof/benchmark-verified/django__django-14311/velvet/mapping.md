# mapping.md — django__django-14311

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 5a8e8f80bb82a867eab7e4d9d099f21d0a976d22`, states the type
abstraction (the Lean↔Python bijection G-CONF uses to bridge values), and gives
the provenance of each callee.

Repo file under change: `django/utils/autoreload.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `relaunchCommand (leadingArgs …) (moduleName) (parentPackage) (trailingArgs)` | `get_child_arguments()` — `django/utils/autoreload.py:213` (the `__spec__`-present branch, body lines 226-228) | the modeled changed function (interpreter relaunch argv builder) |
| `moduleToReexec (moduleName) (parentPackage)` | the dotted name chosen for `-m` — the changed expression at `django/utils/autoreload.py:227` (pre-patch) / lines 226-231 (post-patch) | pure spec: which dotted module name the `-m` relaunch is given |

The modeled slice is exactly the `if getattr(__main__, '__spec__', None) …`
branch that emits `['-m', <name>] + sys.argv[1:]`. The other branches of
`get_child_arguments` (the `not py_script.exists()` Windows `.exe`/`-script.py`
fallbacks and the final `args += sys.argv` plain-script case) are **unchanged by
the patch** and outside the modeled slice; the F2P test exercises only the
`__spec__`-present `-m` branch (see §3).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as a spurious G-CONF
disagreement.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `__main__.__spec__.name` (the entry module's reported dotted name, a `str`) | `moduleName : String` | Python `str` ↔ Lean `String`, character-for-character; the empty `str` ↔ `""` |
| `__main__.__spec__.parent` (the parent package's dotted name, a `str`; `''` when there is no parent package) | `parentPackage : String` | Python `str` ↔ Lean `String`; the falsy empty `str` `''` ↔ `""` (the `spec.parent` truthiness test ↔ `parentPackage ≠ ""`) |
| `args` prefix already built = `[sys.executable] + ['-W%s' % o for o in sys.warnoptions]` (a `list[str-like]`) | `leadingArgs : List String` | Python `list` ↔ Lean `List`; element-wise `str` ↔ `String`. Reproduced verbatim; never inspected. |
| `sys.argv[1:]` (the trailing program arguments, a `list[str]`) | `trailingArgs : List String` | Python `list[str]` ↔ Lean `List String`, element-wise; appended verbatim |
| `args += ['-m', name]` then `args += sys.argv[1:]` | `leadingArgs ++ ["-m", name] ++ trailingArgs` | Python list `+=` (append/extend) ↔ Lean `++`; the literal `'-m'` ↔ `"-m"` |
| `name == '__main__'` | `moduleName == "__main__"` | `str` equality ↔ `String` `==` (`BEq`) |
| `name.endswith('.__main__')` | `moduleName.endsWith ".__main__"` | Python `str.endswith(suffix)` (single string arg) ↔ Lean `String.endsWith`; a whole-suffix match, both true exactly when the trailing characters equal `.__main__` |
| `name = spec.parent` / `name = spec.name` selection, `args += ['-m', name]` | `moduleToReexec moduleName parentPackage` chosen element | the patched `if/else` choosing `spec.parent` vs `spec.name` ↔ `moduleToReexec` |

Note `Path(sys.argv[0])` / `py_script` is computed in the function but is **only
read in the other (non-`__spec__`) branches**; in the modeled `-m` branch it is
irrelevant to the output, so it has no Lean carrier.

## 3. Callee provenance (kind-A)

**None.** Every operation in the modeled slice is a primitive on values already
in hand:

- `spec.name == '__main__'` / `spec.name.endswith('.__main__')` — `str`
  equality and a `str.endswith` literal-suffix test, both **modeled concretely**
  (`==` and `String.endsWith`), not axiomatized.
- `spec.parent` truthiness — a non-empty-`str` test, modeled as
  `parentPackage ≠ ""`.
- `args += ['-m', name]`, `args += sys.argv[1:]` — list concatenation, modeled
  as `++`.

There is **no unchanged foreign callee** whose contract the proof consumes and
**nothing deep-modeled against a real callee**, so there is no axiom and no
A-reference. `axiom_check.py` is therefore omitted and `meta.json` records
`G-AX: skip` (mirrors the no-axiom exemplar django__django-11490). The function
under change (`get_child_arguments` / the `-m` name choice) is itself modeled
directly and is **never** axiomatized (directive 7).

`__main__.__spec__` attribute access is the runtime plumbing that *delivers*
`moduleName`/`parentPackage` to the function; it is the input-acquisition path
(bridged by the §2 bijection: `__spec__.name`↔`moduleName`,
`__spec__.parent`↔`parentPackage`), not a computational callee, so it is not a
modeled op and not an axiom.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14311`** so the
consumer-side verdict is reproducible. The shadow it builds transliterates
`moduleToReexec` (pure R/I op) and the argv assembly to Python and diffs against
the real patched `get_child_arguments` branch behaviour (a faithfully extracted
`name`-selection oracle) over the fuzzed `(moduleName, parentPackage,
leadingArgs, trailingArgs)` space. There are no A-tagged ops, so the shadow is
pure R/I.
