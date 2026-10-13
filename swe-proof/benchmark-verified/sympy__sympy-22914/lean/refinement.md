# refinement.md — operation correspondence (sympy__sympy-22914)

Maps every op in `implementation_printApp` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

## The change
The patch adds two rows to the printer's plain name→built-in table
(`_known_functions` in `sympy/printing/pycode.py`):
```python
 _known_functions = {
     'Abs': 'abs',
+    'Min': 'min',
+    'Max': 'max',
 }
```
This table feeds `self.known_functions`, whose membership is the gate of the
FIRST arm of `CodePrinter._print_Function`:
```python
if expr.func.__name__ in self.known_functions:        # dispatch test
    cond_func = self.known_functions[expr.func.__name__]   # 'min' / 'max' (str)
    func = cond_func                                  # str branch
    return func(*[parenthesize(a,0) for a in expr.args])   # via _print_known_func:
    #   '{name}({args})'.format(name=_module_format(func), args=', '.join(...))
# else: arm does not fire -> later, patch-unchanged arms
#       (Piecewise rewrite / per-class printers / not-supported)
```
Adding the two rows makes this arm fire for the min/max operations, rendering
`min(args)` / `max(args)`; before the patch the arm did not fire for them
(empirically the min/max ops were rendered by a later Piecewise-rewrite arm).
For every head other than the two newly-mapped operations, the emission is
byte-identical pre- and post-patch (the gold hunk touches nothing else); that
unchanged emission enters the model as the read-only input `fallback`, and the
spec's fourth conjunct pins the routine to return it VERBATIM — the
no-regression half of the contract.

The modeled observable is the printer's per-node emission, as `String`.

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `if name = "Min" then renderCall "min" args` | new row `'Min': 'min'` ⟹ arm fires with mapped name `min` | R | string class-name `expr.func.__name__` ↔ `name : String`; printed-args `list[str]` ↔ `args : List String`; `', '.join` + format ↔ `renderCall`. The added table row is what makes this arm fire. |
| 2 | `else if name = "Max" then renderCall "max" args` | new row `'Max': 'max'` ⟹ arm fires with mapped name `max` | R | same bijection as row 1 for the maximum operation |
| 3 | `else if name = "Abs" then renderCall "abs" args` | the PRE-EXISTING `'Abs' → 'abs'` row firing | I | unchanged behavior, modeled for fidelity/regression (the pre-patch twin keeps exactly this) |
| 4 | `renderCall fn args = fn ++ "(" ++ String.intercalate ", " args ++ ")"` | `_print_known_func`: `'{name}({args})'.format(name=_module_format(known), args=', '.join(printed_args))` | I | identical formatting; `_module_format` is the identity on an unqualified plain-table value, so `name == known` |
| 5 | `else fallback` | any other head emitted by the unchanged machinery — byte-identical pre/post patch | I | the no-change pass-through; the emission the unchanged machinery produces enters as the read-only input `fallback` and is returned verbatim |

No A-consumed rows: the proof discharges the rendered string directly from the
inputs (`name`, `args`, `fallback`); no UNCHANGED callee property is assumed.
No A-reference rows: the dispatch decision and formatting are spelled out, not
delegated to a real callee. No changed-inexpressible op. The `axioms` region is
empty and `axiom_check.py` is a skip stub.

## Prepatch (the bug)
`Solution_prepatch.lean` models the actual pre-patch behaviour: the
built-in-equivalent table does NOT yet contain the min/max operations — only
the pre-existing absolute-value row — so a min/max application falls through
and keeps the surrounding machinery's emission (`fallback`). This corresponds
to the absence of the two table rows. It has no faithful R/I row producing
`renderCall "min"/"max" …` for those names — exactly the G-DIFF signal: for
`name = "Min"` the spec demands `renderCall "min" args`, but the impl returns
the universally quantified `fallback`, which cannot be proved equal to it (and
in the real repo the Piecewise text indeed differs).

## Why the spec is TIGHT (total, no domain restriction)
The four spec conjuncts cover EVERY head: the three mapped heads are pinned to
their built-in-call emissions, and every other head is pinned to `fallback` —
the unchanged machinery's output supplied as a read-only input. No output is
left unconstrained, so a verifying impl cannot smuggle in behavior the gold
patch does not have (e.g. mapping some other function to a built-in, emitting
an upper-case call name, or garbling non-mapped emissions): any such impl
violates one of the four conjuncts. The only degrees of freedom a verifying
impl has are representational (branch order, how it assembles the pinned
strings), which are behaviorally invisible.

## Discriminating clause
Rows 1–2 are the discriminator: the frozen `problem_spec_printApp` demands
`result = renderCall "min" args` when `name = "Min"` (and likewise `max`). The
prepatch impl yields `fallback`, so its `correct_*` cannot close (over all
quantified `fallback`). The post-patch impl produces exactly those values, so
the spec is dischargeable only by the patched behaviour.

## verify(Solution) ⇒ resolved
`implementation_printApp` verifies only if, for `name = "Min"`,
`result = renderCall "min" args`; for `name = "Max"`,
`result = renderCall "max" args`; for `name = "Abs"`,
`result = renderCall "abs" args`; and for EVERY other name,
`result = fallback` — the unchanged machinery's emission, i.e. the node prints
exactly as before the patch. By R (head name, rendered operands, fallback text
`str ↔ String`) and I (call assembly transliterated verbatim; pass-through
identity), the verified routine equals the patched `_print_Function`'s
emission on ALL nodes: built-in calls on the mapped heads, byte-identical
unchanged output elsewhere; by G-CONF the R/I transliteration agrees with the
patched `PythonCodePrinter().doprint` on ≥10⁵ inputs spanning both mapped and
non-mapped heads. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement, and the gold patch resolves.
