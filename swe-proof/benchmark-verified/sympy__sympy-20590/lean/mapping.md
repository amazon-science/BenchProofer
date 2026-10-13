# mapping.md — symbol binding & type bijection (sympy__sympy-20590)

## Instance summary
A printing-support mixin class that sits in the ancestry of the core expression
base class did not pin its instance memory layout (it declared no fixed
attribute set). Because one ancestor layer left the layout unpinned, instances of
downstream concrete types regained a per-instance attribute dictionary, so they
became freely mutable (an arbitrary attribute could be set) — a regression from
the intended immutable instances. The fix makes that mixin layer pin its layout
with an empty fixed-attribute set, so every ancestor layer pins its layout and
instances no longer carry a per-instance attribute dictionary.

## Modeled function (the changed behavior under spec)
The behavior is CPython's instance-layout determination for a type: an instance
carries a per-instance attribute dictionary **iff at least one ancestor layer
(excluding the universal base) fails to declare an empty fixed-attribute set**.
The fix is the single ancestor layer that now pins its layout.

| Lean | Python | file:line @ base_commit |
|---|---|---|
| `implementation_immutableInstances` / `problem_spec_immutableInstances` / `correct_immutableInstances` | the printing-support mixin's class-body slot declaration that determines whether downstream instances carry a per-instance attribute dictionary | `sympy/core/_print_helpers.py:8` (the mixin class body, where the gold patch inserts the empty fixed-attribute declaration at line 20) |

Anchor of the observable: the concrete downstream type whose instances the issue
reports as mutable is constructed at `sympy/core/symbol.py:182` (its ancestry is
`sympy/core/expr.py:3855 → :17`, `sympy/core/basic.py:28`, the mixin at
`sympy/core/_print_helpers.py:8`, and `sympy/core/evalf.py:1379`). Every layer
other than the mixin already pins its layout (`expr.py:40`, `expr.py:3865`,
`basic.py:72`, `evalf.py:1382`, `symbol.py:203`); only the mixin lacked it.

## Type bijection (used by G-CONF / G-AX)
| Python reality | Lean model |
|---|---|
| an ancestor class (excluding `object`) in a type's linearized ancestry (MRO) | `Layer` (a one-field structure) |
| the class declares `__slots__` with no `'__dict__'` entry (pins its instance layout) | `Layer.pinsLayout = true` |
| the class declares no `__slots__` (or includes `'__dict__'`) | `Layer.pinsLayout = false` |
| the ancestry layers other than the fixed mixin | `otherLayers : List Layer` (the impl's input) |
| `hasattr(instance, '__dict__')` (instance carries an attribute dict, i.e. is mutable) | `ancestryAddsDict layers = true` |
| instance is immutable (no per-instance attribute dict) | `result = true` |

Bridge for G-CONF: a fuzzed `otherLayers : List Bool` is realized in CPython by
dynamically building a chain of classes, each declaring `__slots__ = ()` iff its
flag is `true`, plus the fixed mixin (always `__slots__ = ()`), then observing
`hasattr(instance, '__dict__')`. The Lean prediction is `all otherLayers pin`.

## Callee provenance / flag deps
No UNCHANGED callee is invoked by the modeled behavior — the layout rule is a
pure fold over the ancestry and is modeled deeply. No `opaque` callee, no
consumed axiom (G-AX = skip). No flag dependency.

## G-CONF fuzz seed
`conf_seed = 20590` (pinned).
