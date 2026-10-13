# refinement.md — django__django-14311

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `relaunchCommand` `do` block and the pure `moduleToReexec` decision) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the narrative is audited by **G-EQ**. Claim: any impl verifying against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves. `patch.diff` is the gold patch
**verbatim** (G-RESOLVE).

## A. The relaunch-name site — `get_child_arguments()` (`django/utils/autoreload.py:226-228`)

Gold hunk (the `__spec__`-present branch):
```
-    if getattr(__main__, '__spec__', None) is not None and __main__.__spec__.parent:
-        args += ['-m', __main__.__spec__.parent]
+    if getattr(__main__, '__spec__', None) is not None:
+        spec = __main__.__spec__
+        if (spec.name == '__main__' or spec.name.endswith('.__main__')) and spec.parent:
+            name = spec.parent
+        else:
+            name = spec.name
+        args += ['-m', name]
         args += sys.argv[1:]
```

| # | Solution.lean impl op (`relaunchCommand`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `moduleName : String` | `__main__.__spec__.name` (a `str`) | R | `str` ↔ `String` (mapping.md §2). Acquired via `__spec__` attribute access, the input-delivery path, not a modeled callee. |
| A2 | param `parentPackage : String` | `__main__.__spec__.parent` (a `str`, `''` if none) | R | `str` ↔ `String`; the `spec.parent` truthiness test ↔ `parentPackage ≠ ""` (mapping.md §2). |
| A3 | param `leadingArgs : List String` | the already-built `args = [sys.executable] + ['-W…' …]` prefix | R | `list` ↔ `List`, element-wise `str` ↔ `String`; reproduced verbatim, never inspected (mapping.md §2). |
| A4 | param `trailingArgs : List String` | `sys.argv[1:]` | R | `list[str]` ↔ `List String`, element-wise (mapping.md §2). |
| A5 | `moduleName == "__main__"` | `spec.name == '__main__'` | I | `str`/`String` equality, identical concrete op. |
| A6 | `moduleName.endsWith ".__main__"` | `spec.name.endswith('.__main__')` | I | literal whole-suffix test; `String.endsWith` ↔ single-arg `str.endswith` (mapping.md §2). |
| A7 | `… && parentPackage ≠ ""` | `… and spec.parent` | I + R | boolean `and`; the non-empty-`str` truthiness ↔ `≠ ""` (R, mapping.md §2). |
| A8 | `if (…) then parentPackage else moduleName` (= `moduleToReexec moduleName parentPackage`) | the `if/else` choosing `name = spec.parent` vs `name = spec.name` | I | identical branch selecting the dotted name. |
| A9 | `cmdline := leadingArgs ++ ["-m", name]` then `++ trailingArgs` | `args += ['-m', name]` then `args += sys.argv[1:]` | I | list concatenation; `'-m'` literal ↔ `"-m"`; order preserved. |

Discriminating content of the change — a genuine deeper dotted module
(`spec.name` like `foo.bar.baz`, NOT a package-entry name, with a non-empty
parent `foo.bar`) is relaunched under its OWN name `foo.bar.baz`, not collapsed
to the parent `foo.bar`. This lives in `moduleToReexec`'s `else` branch
(`moduleName`) guarded by the package-entry test. The pre-patch always used the
parent whenever one existed; `Solution_prepatch.lean` reproduces that
(`if parentPackage ≠ "" then parentPackage else moduleName`) and **fails**
`cmdline = … moduleToReexec moduleName parentPackage …` (G-DIFF) precisely on
this input class — exactly what the F2P
`test_run_as_non_django_module_non_package` observes (`-m
utils_tests.test_module.main_module`, not `-m utils_tests.test_module`).

## B. No second site

The patch touches only the single `__spec__`-present branch of one function;
there is no independently-fixed behavior, so there is one `Solution.lean` method
and one prepatch.

## C. No axioms, no kind-3 (inexpressible-changed-op) steps

Every step is R or I. There is **no consumed axiom and no A-reference**: every
op in the modeled slice is a primitive on values already in hand (`str`
equality, `str.endswith` literal-suffix, non-empty test, list `++`), modeled
concretely. The function under change is modeled directly and is never
axiomatized (directive 7). The one operation that genuinely *changed* — the
choice of dotted name for `-m` — is modeled deeply by `moduleToReexec`
(spelled out, step A8), not hidden behind an axiom.

## D. verify(Solution) ⇒ resolved

`relaunchCommand` verifies only if its output equals
`leadingArgs ++ ["-m", moduleToReexec moduleName parentPackage] ++ trailingArgs`
— i.e. the `-m` name is the parent package exactly when the entry module is a
package entry point (`__main__` / `*.__main__`) with a parent, and otherwise the
module's own dotted name (A5-A9). By R (`str ↔ String`, `list ↔ List`, the
`spec.parent` truthiness ↔ `≠ ""`) the verified builder equals the patched
`get_child_arguments` `-m` branch on the bridged inputs; by G-CONF the R/I
transliteration agrees with `patch.diff`'s behaviour on ≥10⁵ fuzzed inputs.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). There are
no axioms, so the only trust point is refinement fidelity (this doc, G-EQ +
G-CONF).
