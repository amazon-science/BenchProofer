# refinement.md — django__django-13837

The operation-by-operation correspondence between `model.py`'s implementation
(the `child_arguments` impl region, plus the deep predicate `is_module_launch`
and the pure tokens in the `pure` region) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed**, the proof uses the axiom's `Ensures`, and **A-reference**,
a deep model validated == the real callee/runtime by axiom_check.py / G-AX), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed branch — `get_child_arguments()` (`django/utils/autoreload.py:213`)

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
+    # see https://docs.python.org/3/reference/import.html#main-spec
+    if __main__.__spec__ is not None and __main__.__spec__.parent:
+        args += ['-m', __main__.__spec__.parent]
         args += sys.argv[1:]
     elif not py_script.exists():
         ...
```

| # | model.py impl op (`child_arguments`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `prefix: PSeq[PSeq[int]]` | `args = [sys.executable] + ['-W%s' % o for o in sys.warnoptions]` (the fixed leading arguments built before the branch) | R | `list[str]` ↔ `PSeq[PSeq[int]]`; `str` ↔ `PSeq[int]` code points (mapping.md §2). The prefix is unchanged by the patch and is read-only here (an immutable pure-sequence value). |
| A2 | parameters `package_reported: bool`, `launch_package: PSeq[int]` | the runtime values `__main__.__spec__ is not None` and `__main__.__spec__.parent` | R + A-reference | `__spec__ is not None` ↔ `package_reported`; `__spec__.parent` (a `str`) ↔ `launch_package` (a `PSeq[int]`). The mapping of `__main__.__spec__`/`.parent` to (reported?, parent-name) is validated == the real runtime by G-AX (mapping.md §3.1). |
| A3 | branch guard `is_module_launch(package_reported, launch_package)` i.e. `package_reported and len(launch_package) > 0` | `if __main__.__spec__ is not None and __main__.__spec__.parent:` | A-reference | the changed launch-detection predicate is modeled **deeply**: `is_module_launch` (the spelled-out `pure` predicate) IS `__spec__ is not None and (a non-empty parent string)`. A non-empty `str` is truthy, so `... and __main__.__spec__.parent` ⇔ `package_reported and len(launch_package) > 0`. There is **no consumed axiom**; the deep model is validated == the real runtime predicate out-of-band by axiom_check.py (G-AX): for genuine `ModuleSpec`s of `-m PACKAGE`, a directory launch (parent `""`), and a script launch (spec `None`), the runtime predicate and `is_module_launch` agree. |
| A4 | module-launch result `prefix + PSeq(dash_m(), launch_package) + argv.drop(1)` | `args += ['-m', __main__.__spec__.parent]; args += sys.argv[1:]` | R + A-reference | the emitted module flag `'-m'` ↔ `dash_m()` (`PSeq(45,109)`, I on content); the emitted package is `launch_package` itself ↔ `__main__.__spec__.parent` itself — grounded in the input, **not** any fixed literal; `sys.argv[1:]` ↔ `argv.drop(1)`. `+` (list concat) ↔ `PSeq` `+`. G-AX confirms the emitted package equals the launched package's `ModuleSpec.parent`. |
| A5 | `elif not script_exists: return windows_recovery()` | `elif not py_script.exists(): <Windows .exe / -script.py recovery>` | R + I (abstracted) | `Path(sys.argv[0]).exists()` ↔ `script_exists`; the whole Windows recovery body is UNCHANGED by the patch (identical pre/post), so it is represented abstractly by the sentinel `windows_recovery()`. It is not the modeled behaviour; it is PASS_TO_PASS and identical on both sides of the diff. |
| A6 | `else: return prefix + argv` | `else: args += sys.argv` | R + I | the final fall-through is unchanged: leading args then the whole argument vector. `list + list` ↔ `PSeq + PSeq`. |

The discriminating content of the change — recognising **any** `-m PACKAGE`
launch (not only `-m django`) and re-emitting **that** package — lives in
step A3/A4: `is_module_launch` is true for every non-empty launched package, and
the result emits `launch_package` itself. The pre-patch recognised a module
launch only when `py_script == Path(django.__main__.__file__)`, i.e. only when
the launched package was exactly `'django'`, and emitted the literal `'django'`;
`model_prepatch.py` reproduces that (the guard `... and launch_package ==
PSeq('django') ` + the literal `PSeq('django')`) and **fails** the postcondition
clause (A) `Result() == prefix + PSeq(dash_m(), launch_package) + argv.drop(1)`
for a non-django module launch (where it instead returns `prefix + argv` via the
`else` branch) — exactly the spec sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the module-launch detection and the package it re-invokes — is
modeled **deeply** (`is_module_launch` over `package_reported`/`launch_package`,
and the direct re-emission of `launch_package`, steps A3/A4), not hidden behind
an axiom about the runtime. There is **no consumed `@ContractOnly` axiom** in
this bundle: the only unchanged-callee-shaped construct, the
`__main__.__spec__`/`.parent` access, IS the changed predicate and so is an
**A-reference** that G-AX validates the deep model against, never a consumed
axiom.

## C. verify(model) ⇒ resolved

`child_arguments` verifies only if, on a module launch (`is_module_launch`
true), its result equals `prefix + ['-m', launch_package] + argv.drop(1)` with
the **launched package itself** (A4), and only if the non-module branches return
the unchanged forms (A5/A6). By R (`str` ↔ `PSeq[int]`, `list[str]` ↔
`PSeq[PSeq[int]]`, `sys.argv[1:]` ↔ `argv.drop(1)`) the verified reconstruction
equals the gold post-patch `get_child_arguments()` on the tested launch shapes;
by G-AX the deep predicate `is_module_launch` and the emitted package equal the
real `__main__.__spec__`/`.parent` runtime semantics (A-reference). Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the audited runtime reference — and the gold patch resolves
(G-RESOLVE: the F2P `test_run_as_non_django_module` now sees `['-m',
'utils_tests.test_module', ...]`, and the P2P `test_run_as_module` still sees
`['-m', 'django', ...]`). The trust points are exactly the two of PLAN §1.1:
A-reference soundness (G-AX) and refinement fidelity (this document, G-EQ).
