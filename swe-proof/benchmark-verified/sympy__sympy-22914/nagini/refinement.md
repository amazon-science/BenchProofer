# refinement.md — sympy__sympy-22914

The operation-by-operation correspondence between `model.py`'s implementation
(the `print_function_call` impl region and the deep model `is_supported` /
`target_name` / `call_render`) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed** where
the proof uses an axiom's `Ensures`, **A-reference** where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The change site — the supported-function table

Gold hunk (`sympy/printing/pycode.py:19-21`):
```
 _known_functions = {
     'Abs': 'abs',
+    'Min': 'min',
+    'Max': 'max',
 }
```

Adding these two keys makes `'Min'`/`'Max'` members of every Python-code
printer's `known_functions` table (built from `_known_functions ∪ {math.*}` at
`pycode.py:80`). The function-application dispatch `_print_Function`
(`codeprinter.py:415`) then takes its **known** branch for `Min`/`Max`,
rendering `<target>(<comma-joined args>)` = `min(...)` / `max(...)`, instead of
falling through to the `_rewriteable_functions` Piecewise rewrite.

| # | model.py impl op (`print_function_call`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `name_code: int` | `expr.func.__name__` keyed into `known_functions` | R | the identity `str` key abstracted to an integer name code; the only facets read are table membership + value (mapping.md §2). |
| A2 | parameter `joined_args: List[int]` | `self.stringify(expr.args, ", ")` / `', '.join(self._print(a) ...)` | R | already-rendered comma-joined argument text as a code-point list; an UNCHANGED sub-computation (identical for the pre-existing `Abs`), carried opaquely (mapping.md §2). |
| A2b | parameter `fallback: List[int]` (read-only, `Acc(...,1/2)`) | the text the non-call paths of `_print_Function` emit for an unsupported identity (`_print_not_supported`, `codeprinter.py:560`, OR the `_rewriteable_functions` Piecewise rewrite, `codeprinter.py:433-436`) | R | the unchanged surrounding machinery's output for this node, carried opaquely as one pre-rendered sequence; the spec pins the unsupported result to it EXACTLY (`ToSeq(Result()) == ToSeq(fallback)`), so nothing but the supported-call emission may change (mapping.md §1). |
| A3 | the dispatch `if name_code ∈ {0,1,2}: render call else return the fallback text unaltered`, with `is_supported`/`target_name` giving membership and target | the `if expr.func.__name__ in self.known_functions:` branch of `_print_Function`, now matching `Min`/`Max` because the gold edit added them | A-reference | the changed operation (extending the supported table so `Min`→`min`, `Max`→`max`) is modeled **deeply**: `is_supported`/`target_name` (the `pure` region) ARE the post-patch table membership/value, and the impl renders the call exactly for them. There is **no consumed table axiom** — the proof never depends on a `@ContractOnly`. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs the real `PythonCodePrinter` and asserts `doprint(Min/Max/Abs(...)) == call_render(...)` (mapping.md §3.1). |
| A4 | `result = nm + [40] + joined_args + [41]` | `"%s(%s)" % (func, self.stringify(expr.args, ", "))` (`codeprinter.py:427`) / `'{name}({args})'.format(...)` (`pycode.py:65`) | R + I | string concatenation/format ↔ list `+`; `(`→40, `)`→41 (I); `func`→`target_name`, args→`joined_args` (R). |
| A5 | `out = empty + fallback; return out` (unsupported branch) | the unchanged non-call machinery's return value passed through `_print_Function` unaltered | I | identity on the carried fallback text (a fresh list copy, value-equal by `ToSeq`); the unsupported path performs NO computation of its own — exactly the gold patch, which touches only the table. |

The discriminating content of the change — `Min`/`Max` becoming supported
call-rendered functions with targets `min`/`max` — lives in
`is_supported(1)==is_supported(2)==True` with `target_name(1)==PSeq(109,105,110)`
(`min`) and `target_name(2)==PSeq(109,97,120)` (`max`) (model) ⇔ the two added
table entries (real). The pre-patch table had neither key, so `Min`/`Max` fell
through to the rewriteable-Piecewise branch; `model_prepatch.py` reproduces that
(only name code 0/`Abs` rendered as a call, `Min`/`Max` return the unchanged
machinery's `fallback` text) and **fails** the postcondition
`Implies(is_supported(name_code), ToSeq(Result()) ==
call_render(name_code, ToSeq(joined_args)))` — exactly the spec sensing the
change (G-DIFF). The verifier reports the failure on that clause at
`model_prepatch.py:110`.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — extending the printer's supported-function table — is modeled
**deeply** (`is_supported`/`target_name` consumed by `print_function_call`,
step A3, an **A-reference**), not hidden behind an axiom about the function
under change. The axioms region is **empty**; there is no consumed
`@ContractOnly`.

## C. verify(model) ⇒ resolved

`print_function_call` verifies only if, for every supported name code (in
particular the minimum/maximum selection codes), its output equals the call
rendering `target_name ++ "(" ++ joined_args ++ ")"` (A3/A4), and only if an
unsupported identity is emitted EXACTLY as the unchanged surrounding machinery
emits it (`ToSeq(Result()) == ToSeq(fallback)`, A2b/A5) — so no divergent
unsupported-path behaviour is admitted. By R (str ↔ List[int], the unchanged
`joined_args` and `fallback` sub-computations, `(`/`)` literals) the verified
renderer equals the real `_print_Function` on the tested inputs;
by G-AX the deep model `is_supported`/`target_name`/`call_render` equals the
real `PythonCodePrinter` rendering of `Min`/`Max`/`Abs` (the A-reference).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited deep model — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom/
deep-model soundness (G-AX) and refinement fidelity (this document, G-EQ).
