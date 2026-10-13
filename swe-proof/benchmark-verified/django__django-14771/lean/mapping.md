# mapping.md — django__django-14771

## Symbol binding (file:line @ base_commit 4884a87e022056eda10534c13d74e49b8cdda632)

- Modeled function: `get_child_arguments`
  — `django/utils/autoreload.py:213-248` @ base_commit.
  Returns the argument vector used to relaunch the interpreter under the
  development auto-reloader.
- Patched region: `django/utils/autoreload.py:222` prefix construction; the gold
  patch inserts lines after `args = [sys.executable] + ['-W%s' % o ...]`
  (between old line 222 and the `__spec__` comment block at old 223).

## Modeled scenario

The F2P test `test_xoptions` and the PASS_TO_PASS warn/argv tests exercise the
common `runserver` path: `__main__.__spec__` is `None` and `Path(sys.argv[0])`
exists, so control reaches the final `else: args += sys.argv`. The fix is
inserted *before* any branch (it builds the `args` prefix), so this path is a
faithful, representative skeleton of the changed control flow. The
`__spec__`/`-m` branch and the Windows exe-fallback branches are unchanged
alternative paths not in scope of the modeled behavior (they are unaffected by
the fix; with empty `_xoptions` they are byte-identical pre/post patch — which
is exactly why their tests are PASS_TO_PASS).

## Lean ↔ Python type bijection (used by G-CONF)

| Python (in `get_child_arguments`)         | Lean model                         | bijection |
|-------------------------------------------|------------------------------------|-----------|
| `sys.executable : str`                    | `executable : String`              | identity (R) |
| `sys.warnoptions : list[str]`             | `warnoptions : List String`        | element-wise identity (R) |
| `sys.implementation.name == 'cpython'`    | `isCpython : Bool`                 | `True ↔ name=='cpython'`, else `False` (R) |
| `sys._xoptions : dict[str, str\|True]`    | `xoptions : List (String × XVal)`  | insertion-ordered items; value `True ↦ XVal.flag`, value `s:str ↦ XVal.val s` (R) |
| `sys.argv : list[str]`                    | `argv : List String`               | element-wise identity (R) |
| `'-W%s' % o`                              | `"-W" ++ o`                        | identity (I) |
| `f'-X{key}'` when `value is True`         | `xoptArg key XVal.flag = "-X"++key`| identity (I) |
| `f'-X{key}={value}'` otherwise            | `xoptArg key (XVal.val v)`         | identity (I) |
| `args` (return, list[str])                | `result : List String`             | element-wise identity (R) |

`sys._xoptions` value domain: CPython stores `True` for a bare `-Xfoo` and the
RHS string for `-Xfoo=bar`. `XVal.flag` / `XVal.val s` is the exact bijection.

## Callee provenance + flag deps

- No UNCHANGED pure callee is consumed: the inserted code uses only Python
  string formatting (`f'-X{...}'`) and dict iteration, both modeled deeply as
  total Lean string concatenation over the input list. Hence NO `opaque` callee
  and NO `_prop` axiom (axioms region empty; G-AX = skip).
- Flag dependency: the `-X` forwarding is gated on `isCpython`
  (`sys.implementation.name == 'cpython'`); G-CONF fuzzes both truth values.

## G-CONF fuzz seed

Pinned seed: `14771`.
