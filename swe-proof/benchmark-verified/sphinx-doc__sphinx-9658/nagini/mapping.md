# mapping.md — sphinx-doc__sphinx-9658

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 232dbe41c5250eb7d559d40438c4743483e95f15`, states the type
abstraction, and gives the provenance of the deep-model reference (the real
callee chain validated by axiom_check.py / G-AX).

Repo file under change: `sphinx/ext/autodoc/mock.py`.
Repo file consuming the changed attributes (unchanged): `sphinx/util/typing.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `subclass_short_name(name)` | `_make_subclass(name, module, ...)` — `sphinx/ext/autodoc/mock.py:72` (the `attrs` dict, line 74-77) | modeled changed site: the placeholder subclass records its own short identifier (its attribute `name`). The gold patch adds `'__name__': name` to `attrs`. |
| `placeholder_display_name(short_name)` | `_MockObject.__init__` — `sphinx/ext/autodoc/mock.py:42` (body line 43) | modeled changed site: the placeholder's display identifier (`__qualname__`) is set from its short identifier (`__name__`). The gold patch changes `self.__qualname__ = ''` to `self.__qualname__ = self.__name__`. The `_MockObject.__name__ = ''` default (line 28-29, gold hunk 1) makes the attribute always exist. |
| `qualified_reference(name, module)` | the renderer reading `__module__` + `__qualname__` to compose a cross-reference — `sphinx/util/typing.py` `_restify_py37` line 194-198 (`':py:class:`%s.%s`' % (cls.__module__, cls.__qualname__)`), the **F2P bug-path** (`test_restify_mock`) | the end-to-end observable: the fully-qualified reference is `module` + `.` + display identifier. Unchanged consuming code. The dangling-dot symptom is observable through `restify` only; `stringify` (`_stringify_py37`, `test_stringify_mock`, P2P) yields the same value via a different code path (the falsy placeholder short-circuits to `repr()`==`__display_name__`==`module.name`) and is invariant across the two commits, so it is not a discriminator. |
| `render_qualified(module, display)` *(pure, deep model — A-reference)* | the dotted join `':py:class:`%s.%s`' % (cls.__module__, cls.__qualname__)` in `_restify_py37` (`sphinx/util/typing.py:198`) | pure spec: the renderer's `module + '.' + display` join. Spelled out structurally; validated against the real `restify` (the F2P bug-path) by axiom_check.py (G-AX), NOT consumed as an axiom. The same value also equals the real `stringify` output (pinned by axiom_check.py as a P2P value equality, not as a discriminator). |

The pre-patch repo state the change repairs (for the refinement audit, not
referenced from the consumer spec view): `_MockObject.__init__` hard-set
`self.__qualname__ = ''` (`mock.py:43`), and `_make_subclass` recorded no
`__name__` in `attrs` (`mock.py:74-77`), so a placeholder reached by attribute
`name` had an empty display identifier and the renderer produced a dangling
`<module>.` with the trailing component dropped (issue: "Bases: `torch.nn.`"
instead of "Bases: `torch.nn.Module`").

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the attribute `name`, the `module` path, `__qualname__`, the rendered reference) | `List[int]` of Unicode code points | `s[k]` ↔ `list[k] == ord(s[k])`; `len(s)` ↔ `len(list)`; `str` concatenation `a + b` ↔ list `+`; `'.'` ↔ `[46]`; empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| the placeholder object's attribute store (`__name__`, `__qualname__`, `__module__`) | the three `List[int]` carriers threaded through `subclass_short_name` → `placeholder_display_name` → `qualified_reference` | each attribute is the corresponding code-point list; setting an attribute ↔ returning/binding the list |
| the `restify`/`stringify` reST decoration (`:py:class:`...``) | omitted (constant wrapper) | the F2P tests compare the inner `module.qualname` text; the `:py:class:` wrapper is a constant prefix/suffix the change does not touch. axiom_check.py checks the full real `restify`/`stringify` output including the wrapper. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

**Termination.** The real counterparts are straight-line attribute stores and
a bounded string join — they always return. The model pins this with
`Requires(MustTerminate(2))` on the two identifier helpers and
`Requires(MustTerminate(3))` on the composed render site (room to call the
helpers), with every loop carrying a strictly decreasing
`Invariant(MustTerminate(len(...) - i))` measure. This rules out
implementations that would satisfy the value clauses vacuously by never
returning (Nagini alone proves only partial correctness).

## 3. Deep-model reference (kind A-reference — checked by G-AX / axiom_check.py)

### 3.1 `subclass_short_name` / `placeholder_display_name` / `render_qualified` ↔ the real placeholder + renderer

**Callees (post-patch, all in the installed sphinx package):**
`sphinx.ext.autodoc.mock._make_subclass` / `_MockObject.__init__` (build the
placeholder) and `sphinx.util.typing.restify` / `stringify` (render it). There
is **no consumed `@ContractOnly` axiom** in this bundle: the changed behaviour
is modelled deeply and validated equal to the real chain out-of-band by G-AX.

The patched behaviour, from the gold source:

```python
class _MockObject:
    __display_name__ = '_MockObject'
    __name__ = ''                                 # gold hunk 1 (default)
    ...
    def __init__(self, *args, **kwargs):
        self.__qualname__ = self.__name__         # gold hunk 2 (was '')

def _make_subclass(name, module, ...):
    attrs = {'__module__': module,
             '__display_name__': module + '.' + name,
             '__name__': name,                     # gold hunk 3
             ...}
    return type(name, (superclass,), attrs)
```

A placeholder reached by attribute `name` under module path `module`
(`module.__getattr__(name)` → `_make_subclass(name, module)()`) therefore has
`__name__ == name` and, after `__init__`, `__qualname__ == name`. The F2P
renderer `restify` reads `__qualname__` directly and composes
`':py:class:`%s.%s`' % (obj.__module__, obj.__qualname__)` = `module + '.' +
name` (patched) — vs the dangling `module + '.'` at base_commit where
`__qualname__ == ''`. This inner `module.name` is exactly what
`render_qualified(module, name)` and the three modeled functions compute.

`stringify` reaches the SAME inner value `module.name` but by a different code
path: the placeholder is falsy (`__len__()==0`), so `stringify` short-circuits
at its `not annotation` guard to `repr(obj)` == `__display_name__` ==
`module + '.' + name` (set unconditionally in `_make_subclass`'s `attrs`); it
never reads `__qualname__` and so is already correct at base_commit. That is why
`test_stringify_mock` is PASS_TO_PASS (invariant across the two commits) and only
`test_restify_mock` is FAIL_TO_PASS.

**Soundness check (G-AX):** `axiom_check.py` builds the REAL placeholder via
`sphinx.ext.autodoc.mock.mock([...])` + attribute access (the F2P input
`unknown.secret.Class` plus 200+ randomized identifier chains), reads the real
`__module__` / `__qualname__`, runs the real `restify` / `stringify`, and
asserts: (a) the placeholder's display identifier equals the attribute name on
the patched code (empty on base_commit); (b) on the patched code the real
`restify` reference equals `:py:class:`module.name`` and never ends in a dangling
dot, while on base_commit the real `restify` reference DOES dangle
(`...endswith(".`")`); (c) the real `stringify` value equals `module.name` on
BOTH commits (pinned as a P2P value equality, NOT a discriminator). It is a
**pre/post discriminator keyed on `restify`** (the F2P bug-path): it inspects the
installed `__init__` / `_make_subclass` source to decide whether the propagation
fix is present, asserting the dangling-dot `restify` reference on the base_commit
code and the repaired reference on the patched code. Confirmed rc=0 in-container
on BOTH testbeds (base_commit `fix_present=False`; gold `fix_present=True`; 204
cases each, 0 violations). The model's decision is the propagated (patched) one.
Imports: standard library + the installed sphinx package (the very package the
gold patch edits). Docs/source: the gold patch hunks above.
