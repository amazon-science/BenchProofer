# refinement.md — django__django-13837

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`buildChildArgs` `do` block and the `childArgsSpec` / `baseArgs` deep models) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement; state
the bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference**
(deep model validated == real callee by G-AX), or **I** (identical concrete op).
EVERY step is R, A, or I. There are **no A steps** in this bundle: the routine
assembles its result purely from values it is handed; no unchanged callee's
behavior is assumed.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviorally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The changed function — `get_child_arguments()` (`django/utils/autoreload.py:213`)

Gold hunk:
```
-    import django.__main__
-    django_main_path = Path(django.__main__.__file__)
+    import __main__
     py_script = Path(sys.argv[0])
     args = [sys.executable] + ['-W%s' % o for o in sys.warnoptions]
-    if py_script == django_main_path:
-        # The server was started with `python -m django runserver`.
-        args += ['-m', 'django']
+    # __spec__ is set when the server was started with the `-m` option,
+    if __main__.__spec__ is not None and __main__.__spec__.parent:
+        args += ['-m', __main__.__spec__.parent]
         args += sys.argv[1:]
     elif not py_script.exists():
         ... exe_entrypoint / script_entrypoint / RuntimeError ...
     else:
         args += sys.argv
     return args
```

| # | Solution.lean impl op (`buildChildArgs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `interp : List Char` | `sys.executable` | R | interpreter path `str` ↔ `List Char` (mapping.md §2). Passed through into `baseArgs`. |
| A2 | `warnOpts : List (List Char)`; `baseArgs = interp :: warnFlags warnOpts`, `warnFlags (o::os) = ("-W"++o) :: …` | `args = [sys.executable] + ['-W%s' % o for o in sys.warnoptions]` | R + I | `warnFlags` models the comprehension **deeply**: it prefixes `-W` to each raw option `o` (`'-W%s' % o`), preserving order; `baseArgs` conses `interp`. G-CONF builds `['-W%s'%o for o in warnoptions]` (mapping.md §2). |
| A3 | `entry : EntryDesc` (`notModule` / `pathEntry` / `moduleEntry pkg`) | `__main__.__spec__` and `__main__.__spec__.parent` | R | the program-entry descriptor. `__spec__ is None` ↔ `notModule`; `__spec__` present with empty `.parent` ↔ `pathEntry`; `__spec__` present with non-empty `.parent == pkg` ↔ `moduleEntry pkg` (mapping.md §2, §3). |
| A4 | `modPkg := match entry with .moduleEntry pkg => some pkg \| _ => none` | `__main__.__spec__ is not None and __main__.__spec__.parent` | I | the module-start test: a non-empty descriptor package yields `some pkg`, otherwise `none`. This is the **single behavioral pivot** of the change (see §B). |
| A5 | `some pkg => prefixArgs ++ (["-m", pkg] ++ userArgs)` where `userArgs := argv.drop 1` | `args += ['-m', __main__.__spec__.parent]; args += sys.argv[1:]` | R + I | the module-execution re-launch names the *detected* package `pkg`, not a literal, then appends the arguments after argv[0]. `argv.drop 1` ↔ `sys.argv[1:]`; `"-m"` literal ↔ `'-m'`. |
| A6 | `none => match probe with .exists => prefixArgs ++ argv` | `else: args += sys.argv` | R + I | not a module and script exists: append the full argument vector. `argv` ↔ `sys.argv`. |
| A7 | `.exeEntry => exePath :: userArgs` | `if exe_entrypoint.exists(): return [str(exe_entrypoint), *sys.argv[1:]]` | R + I | the native-executable-suffix fallback. `exePath` ↔ `str(py_script.with_suffix('.exe'))` (mapping.md §2). |
| A8 | `.scriptEntry => prefixArgs ++ ([scriptPath] ++ userArgs)` | `if script_entrypoint.exists(): return [*args, str(script_entrypoint), *sys.argv[1:]]` | R + I | the generated-launcher-script fallback. `scriptPath` ↔ `str(py_script.with_name('%s-script.py' % py_script.name))`. |
| A9 | `.missing => Except.error .scriptMissing` | `raise RuntimeError('Script %s does not exist.' % py_script)` | R | the invalid-invocation failure. The `Except.error` carrier ↔ the raised `RuntimeError`; G-CONF maps both to the `ERROR` sentinel (mapping.md §2). |

## B. The discriminating change and the prepatch

The pre-patch detected a module start by comparing the invoking script path to
the framework's *own* program entry (`py_script == django_main_path`), and on a
hit emitted the **literal** built-in package name (`args += ['-m', 'django']`).
The fix instead consults the documented top-level entry descriptor: a module
start is recognized iff the descriptor's package is non-empty, and the re-launch
names *that* package.

`Solution_prepatch.lean` reproduces the old behavior: `modPkg` is `some pkg`
**only** when `pkg` equals the built-in package (`if pkg = "django" then some pkg
else none`), so a program started as a *different* module (`moduleEntry pkg`,
`pkg ≠ "django"`) is not recognized and falls through to the script-path branch.
It **fails** `out = childArgsSpec ...` on exactly the `moduleEntry pkg` case with
`pkg ≠ "django"` (G-DIFF) — which is precisely the F2P scenario
`test_run_as_non_django_module` (`pkg = "utils_tests.test_module"`).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that changed — the module-start detection and
the package it names — is modeled **directly** (the `match entry` + `modPkg`
dispatch and the `["-m", pkg]` emission), not hidden behind an axiom. There are
**no axioms** (consumed or reference) in this bundle: the function reads runtime
state (`sys.executable`, `sys.warnoptions`, `sys.argv`, `__main__.__spec__`) and
probes the filesystem, all of which are read-only **inputs** the harness controls
(the F2P test mocks every one of them) — they are R-refinements of the input
carrier, not callees whose behavior the proof assumes. Hence `axiom_check.py` is
absent and G-AX is skipped (meta.json `gates.G-AX.status = "skip"`).

## D. verify(Solution) ⇒ resolved

`buildChildArgs` verifies only if its output equals `childArgsSpec` on every
combination of entry descriptor and script probe — in particular the module
branch must name the *detected* package `pkg` (A4, A5), not a literal. By R
(`str ↔ List Char`, the entry-descriptor and probe bijections, the `RuntimeError`
↔ `Except.error` mapping) the verified result equals the patched
`get_child_arguments` under the denoted runtime state; by G-CONF the R/I
transliteration agrees with `patch.diff`'s behavior on ≥10⁵ inputs spanning every
entry × probe combination plus the exact F2P scenario. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The sole trust point is
refinement fidelity (this doc, G-EQ + G-CONF); there is no axiom-soundness trust
point because there are no axioms.
