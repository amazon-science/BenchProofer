# refinement.md — django__django-14771

Maps every op in `implementation_reloaderArgv` to its `patch.diff` / base-source
counterpart in `get_child_arguments` (`django/utils/autoreload.py`). Tags: **R**
type refinement, **A-consumed** proof uses an axiom property, **A-reference** deep
model validated == real callee (G-AX), **I** identical concrete op.

The modeled scenario is the common relaunch path (`__spec__` is `None`, the
script exists), so `get_child_arguments` returns `args` after `args += sys.argv`.
This is the path exercised by the F2P test `test_xoptions` and the warn/argv
PASS_TO_PASS tests.

| # | Lean op (`implementation_reloaderArgv`) | Python counterpart | tag | note |
|---|------------------------------------------|--------------------|-----|------|
| 1 | `let mut args := [executable]` | `args = [sys.executable] + …` (the `[sys.executable]` head) | R | `sys.executable : str ↔ executable : String`, identity |
| 2 | `for o in warnoptions do args := args ++ [warnArg o]` | `… + ['-W%s' % o for o in sys.warnoptions]` | R+I | list comprehension ↔ accumulator `for`; `'-W%s' % o ↔ "-W" ++ o` (I, helper `warnArg`) |
| 3 | `if isCpython then …` | `if sys.implementation.name == 'cpython':` | R | `name=='cpython' ↔ isCpython=true` |
| 4 | `for kv in xoptions do args := args ++ [xoptArg kv]` | `args.extend(f'-X{key}' if value is True else f'-X{key}={value}' for key, value in sys._xoptions.items())` | R+I | `dict.items()` insertion order ↔ `List (String × XVal)` order; `value is True ↔ XVal.flag`, RHS string `↔ XVal.val v`; `f'-X{key}' ↔ "-X"++key`, `f'-X{key}={value}' ↔ "-X"++key++"="++v` (I, helper `xoptArg`) |
| 5 | `args := args ++ argv` | `else: args += sys.argv` (modeled path) | R | `sys.argv : list[str] ↔ argv : List String`, element-wise identity |
| 6 | `return args` | `return args` | I | identity |

No op is changed-but-inexpressible: every op is total Lean string concatenation /
list append over the input lists. There is NO opaque repo callee consumed and NO
deep-model A-reference axiomatized — the inserted code uses only Python string
formatting and dict iteration, both modeled deeply. Hence the axioms region is
empty and `axiom_check.py` (G-AX) is a skip stub.

The behavior-changing region is ops 3–4 (the CPython-gated `-X` forwarding). The
prepatch impl omits ops 3–4 entirely (it drops the interpreter `-X` options) —
exactly the bug in the issue (e.g. `-Xutf8` lost across a reload). The spec forces
the `-X` tokens to appear when `isCpython = true`, so the carried gold proof is
unclosable against the prepatch impl (G-DIFF).

The impl region has genuine R/I content (executable head, warn tokens, `-X`
tokens, argv tail) ⇒ `conf_skip = false`; `conformance_check.py` differential-tests
the R/I shadow against the gold patch behavior over ≥10⁵ fuzzed inputs.
