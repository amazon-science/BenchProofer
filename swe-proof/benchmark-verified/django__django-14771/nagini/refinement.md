# refinement.md — django__django-14771

The operation-by-operation correspondence between `model.py`'s implementation
(the `child_arguments` impl region, plus the deep fold `option_tokens` /
`option_token` and the pure tokens in the `pure` region) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — split into **A-consumed**, the proof uses the axiom's `Ensures`, and
**A-reference**, a deep model validated == the real callee/runtime by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed step — the `-X` forwarding in `get_child_arguments()` (`django/utils/autoreload.py:213`)

Gold hunk (inserted between the warning-options line and the `__spec__` branch):
```
     args = [sys.executable] + ['-W%s' % o for o in sys.warnoptions]
+    if sys.implementation.name == 'cpython':
+        args.extend(
+            f'-X{key}' if value is True else f'-X{key}={value}'
+            for key, value in sys._xoptions.items()
+        )
     # __spec__ is set when the server was started with the `-m` option,
```

| # | model.py impl op (`child_arguments`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `prefix: PSeq[PSeq[int]]` | `args = [sys.executable] + ['-W%s' % o for o in sys.warnoptions]` (the leading arguments built before the new step) | R | `list[str]` ↔ `PSeq[PSeq[int]]`; `str` ↔ `PSeq[int]` code points (mapping.md §2). The prefix is unchanged by the patch and read-only here (an immutable pure-sequence value). |
| A2 | guard `is_reference_impl` | `if sys.implementation.name == 'cpython':` | R + A-reference | the boolean observation `sys.implementation.name == 'cpython'` ↔ the parameter `is_reference_impl`. G-AX confirms the running reference interpreter reports `'cpython'`. |
| A3 | parameters `opt_keys`, `opt_is_flag`, `opt_vals` (index-aligned) | `for key, value in sys._xoptions.items()` | R + A-reference | `sys._xoptions` (a `dict`) iterated by `.items()` ↔ the three index-aligned sequences: i-th key ↔ `opt_keys[i]`, `value is True` ↔ `opt_is_flag[i]`, `value` ↔ `opt_vals[i]`; iteration order ↔ sequence order (mapping.md §2). |
| A4 | per-option token `option_token(opt_keys[i], opt_is_flag[i], opt_vals[i])` = `dash_x()+key` if `is_flag` else `dash_x()+key+eq()+val` | `f'-X{key}' if value is True else f'-X{key}={value}'` | A-reference | the changed forwarding is modeled **deeply**: the f-string `f'-X{key}'` ↔ `dash_x() + key` and `f'-X{key}={value}'` ↔ `dash_x() + key + eq() + val`; the selector `value is True` ↔ `is_flag`. There is **no consumed axiom**; the deep model is validated == the real generator out-of-band by axiom_check.py (G-AX). `'-X'` ↔ `PSeq(45,88)` (I on content), `'='` ↔ `PSeq(61)` (I on content). |
| A5 | accumulate `options = option_tokens(opt_keys, opt_is_flag, opt_vals)` when `is_reference_impl`, else the empty sequence; `leading = prefix + options` | `args.extend(<generator>)` under the `if sys.implementation.name == 'cpython':` guard | R + A-reference | `args.extend(gen)` appends the per-option tokens in order ↔ `prefix + option_tokens(...)`; the guard makes the option list empty on a non-reference interpreter ↔ the `if`-guard skipping the `extend`. The impl loop builds `option_tokens` by the front-recursive fold (one unfold per option). |
| A6 | module-launch result `leading + PSeq(dash_m(), launch_package) + argv.drop(1)` | `args += ['-m', name]; args += sys.argv[1:]` | R + I | UNCHANGED branch: the module flag `'-m'` ↔ `dash_m()`, the re-invoked package ↔ `launch_package`, `sys.argv[1:]` ↔ `argv.drop(1)`; `list +` ↔ `PSeq +`. The forwarded options now precede this, exactly as in the gold (`args` already carries them). |
| A7 | `elif not script_exists: return windows_recovery()` | `elif not py_script.exists(): <Windows .exe / -script.py recovery>` | R + I (abstracted) | `Path(sys.argv[0]).exists()` ↔ `script_exists`; the whole Windows recovery body is UNCHANGED by the patch, represented abstractly by the sentinel. Not the modeled behaviour; PASS_TO_PASS and identical pre/post patch. |
| A8 | `else: return leading + argv` | `else: args += sys.argv` | R + I | the final fall-through is unchanged: leading args (now incl. forwarded options) then the whole argument vector. This is the branch the F2P `test_xoptions` exercises. `list +` ↔ `PSeq +`. |

The discriminating content of the change — forwarding the recorded
implementation options as `-Xname` / `-Xname=value` tokens inserted into the
leading arguments on the reference interpreter — lives in steps A4/A5
(`option_tokens` consumed in `child_arguments`, gated on `is_reference_impl`).
The pre-patch built the leading arguments WITHOUT any such forwarding;
`model_prepatch.py` reproduces that (`options` is always the empty sequence) and
**fails** the postcondition clauses (A) and (B), which require the forwarded
tokens to appear (`prefix + option_tokens(...) + ...`) whenever
`is_reference_impl` and at least one option is supplied — exactly the spec
sensing the change (G-DIFF). It is reported failing on clause (A); clause (B)
(the branch `test_xoptions` exercises) fails identically.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — forwarding the `-X` implementation options under the cpython guard —
is modeled **deeply** (`option_token` / `option_tokens` over
`opt_keys`/`opt_is_flag`/`opt_vals`, gated on `is_reference_impl`, steps
A2–A5), not hidden behind an axiom about the runtime. There is **no consumed
`@ContractOnly` axiom** in this bundle: the only unchanged-runtime-shaped
constructs — `sys._xoptions`, `value is True`, `sys.implementation.name` — ARE
the changed forwarding and so are **A-references** that G-AX validates the deep
model against, never consumed axioms.

## C. verify(model) ⇒ resolved

`child_arguments` verifies only if, on the reference interpreter, the leading
arguments are followed by exactly the per-option tokens — `-Xname` for a
flag-only option, `-Xname=value` for a name=value option — in supplied order
(A4/A5), before the rest of the command line in every reconstruction shape
(A6/A8), and the empty list otherwise. By R (`str` ↔ `PSeq[int]`, `list[str]` ↔
`PSeq[PSeq[int]]`, `sys.argv[1:]` ↔ `argv.drop(1)`, `dict.items()` ↔ the
index-aligned sequences) the verified reconstruction equals the gold post-patch
`get_child_arguments()` on the tested shapes; by G-AX the deep fold
`option_tokens` equals the real `sys._xoptions` forwarding generator and the
guard matches `sys.implementation.name == 'cpython'` (A-reference). Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the audited runtime reference — and the gold patch resolves
(G-RESOLVE: the F2P `test_xoptions` now sees `[sys.executable, '-Xutf8',
'-Xa=b', __file__, 'runserver']` for `sys._xoptions == {'utf8': True,
'a': 'b'}`; the P2P tests that mock `sys._xoptions == {}` still see no `-X`
tokens). The trust points are exactly the two of PLAN §1.1: A-reference
soundness (G-AX) and refinement fidelity (this document, G-EQ).
