# refinement.md — sympy__sympy-14531

Every operation in each `implementation_<name>` mapped to its `patch.diff`
counterpart. Tags: **R** (type refinement), **A-consumed** (proof uses an axiom's
property), **A-reference** (deep model validated == real callee by G-AX/G-CONF),
**I** (identical concrete op).

## `implementation_printRelational` ↔ `_print_Relational` (charmap branch, str.py:633)

Gold (post-patch) line:
```python
return '%s(%s, %s)' % (charmap[expr.rel_op], self._print(expr.lhs), self._print(expr.rhs))
```
Pre-patch line:
```python
return '%s(%s, %s)' % (charmap[expr.rel_op], expr.lhs, expr.rhs)
```

| Lean op | patch.diff op | tag |
|---|---|---|
| `render settings lhs` | `self._print(expr.lhs)` — render lhs at the ACTIVE profile (active options, NESTED context: the call runs inside the container's `_print` frame at `_print_level >= 2`) | **A-reference** (renderer universally quantified; binding to the real nested `self._print` checked by G-CONF via a `_print_level`-pre-bumped shadow printer) |
| `render settings rhs` | `self._print(expr.rhs)` — render rhs at the ACTIVE profile | **A-reference** |
| `relName ++ "(" ++ … ++ ", " ++ … ++ ")"` | `'%s(%s, %s)' % (charmap[expr.rel_op], …, …)` — string template splice | **I** |

The prepatch's `render defaultSettings lhs/rhs` corresponds to the bare
`expr.lhs` / `expr.rhs` `%s`-interpolation, i.e. `str(sub)` at the DEFAULT
profile — default options AND top-level rendering context (a bare `str()` starts
a fresh printer at `_print_level` 0; see mapping.md "Rendering context").

## `implementation_printLimit` ↔ `_print_Limit` (str.py:219,221)

Gold (post-patch):
```python
if str(dir) == "+":
    return "Limit(%s, %s, %s)" % tuple(map(self._print, (e, z, z0)))
else:
    return "Limit(%s, %s, %s, dir='%s')" % tuple(map(self._print, (e, z, z0, dir)))
```
Pre-patch:
```python
if str(dir) == "+":
    return "Limit(%s, %s, %s)" % (e, z, z0)
else:
    return "Limit(%s, %s, %s, dir='%s')" % (e, z, z0, dir)
```

| Lean op | patch.diff op | tag |
|---|---|---|
| `if dirIsDefault then … else …` | `if str(dir) == "+":` — default-direction branch select | **R** (`dirIsDefault : Bool` ↔ `str(dir) == "+"`) |
| `render settings e/z/z0` | `map(self._print, (e, z, z0))` — render each at the ACTIVE profile | **A-reference** |
| `render settings dir` (else branch) | `self._print(dir)` from `map(self._print, (e, z, z0, dir))` | **A-reference** |
| `"Limit(" ++ … ++ ")"` / `… ++ ", dir='" ++ … ++ "')"` | the two `"Limit(...)"`/`"Limit(..., dir='%s')"` templates | **I** |

The prepatch's `render defaultSettings …` corresponds to the bare `(e, z, z0)` /
`(e, z, z0, dir)` `%s`-interpolation (`str(sub)` at DEFAULT settings).

## Notes
- No op is changed-inexpressible. The single behavioral change — render nested
  subexpressions at the printer's ACTIVE profile instead of the default — is
  modeled directly as which profile argument is passed to `render`. The
  "profile" (`Settings`) covers both the options dict AND the rendering context
  (nested vs top-level `_print_level`); see mapping.md "Rendering context".
- No consumed axiom: `render` is universally quantified, so the proof uses no
  property of it (the spec holds for every renderer). `axiom_check.py` is a skip
  stub. The R/I content (profile selection + branch + template splice) is
  differential-tested by `conformance_check.py` (G-CONF, `conf_skip=false`).
