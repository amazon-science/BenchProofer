# refinement.md — django__django-10880

The operation-by-operation correspondence between `model.py`'s implementation
(`render_fragment` impl region + the deep `fragment`/`modifier` model in the
`pure` region) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement), **A** (axiomatized callee — **A-consumed** if the proof uses
its `Ensures`, **A-reference** if a deep model is validated == the real callee
by axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The single changed line — the set-reducing function's render

Gold hunk (`django/db/models/aggregates.py`, body of `as_sql`):
```
- extra_context['distinct'] = 'DISTINCT' if self.distinct else ''
+ extra_context['distinct'] = 'DISTINCT ' if self.distinct else ''
```
The rendered SQL fragment is produced one step later by the inherited
`Func.as_sql` via the printf template
`'%(function)s(%(distinct)s%(expressions)s)'`
(`django/db/models/expressions.py:621-622`, `return template % data`). So the
observable string is the concatenation
`function + "(" + distinct + expressions + ")"`, where `distinct` is the value
set on the line above. The fix changes that value from `'DISTINCT'` (no trailing
space) to `'DISTINCT '` (trailing space).

| # | model.py impl op (`render_fragment`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | params `function, operands: List[int]` | the `%(function)s` and `%(expressions)s` template values (`str`) | R | `str` ↔ `List[int]` of code points (mapping.md §2). `operands` abstracts the already-compiled `%(expressions)s` text (e.g. `CASE WHEN ...`). |
| A2 | param `distinct: bool` | `self.distinct` (a bool) | I | identical concrete boolean carrier. |
| A3 | `modifier(distinct)` = `kw_distinct() + PSeq(sep())` when `distinct`, else empty | `extra_context['distinct'] = 'DISTINCT ' if self.distinct else ''` | A-reference | the changed value IS the modeled `modifier`: `'DISTINCT '` ↔ `kw_distinct()+space` (8 keyword code points then U+0020), `''` ↔ the empty sequence. The trailing space is the whole fix and lives in `PSeq(sep())`. Modelled deeply (no consumed axiom). |
| A4 | `fragment(...) = function + open_paren() + modifier(distinct) + operands + close_paren()` and the building loops in the impl | `template % data` with `template='%(function)s(%(distinct)s%(expressions)s)'` (`Func.as_sql`, expressions.py:621-622) | A-reference | the percent-substitution of the repo template is exactly this concatenation: `%(function)s` → function, literal `(`, `%(distinct)s` → modifier, `%(expressions)s` → operands, literal `)`. axiom_check.py (G-AX) runs the REAL `template % data` and asserts `fragment == template % data` on boundary + 20000 fuzz inputs in both modes. |
| A5 | `result.append(41)` (closing `)`) and the wrapping `(` literal | the literal parentheses in the template | I | identical literal code points. |

The discriminating content of the change — the separator after `DISTINCT` —
lives in `modifier(True) == kw_distinct() + PSeq(sep())` (model) ⇔ the trailing
space of `'DISTINCT '` (real). The pre-patch `'DISTINCT'` omitted it;
`model_prepatch.py` reproduces that (drops the `result.append(32)`) and **fails**
the operands-loop invariant
`ToSeq(result) == function + "(" + modifier(distinct) + operands.take(k)`
(because `modifier(True)` carries the separator the buggy impl never appended) —
which is exactly the spec sensing the change (G-DIFF). Equivalently the
postconditions `Result()[len(function)+1+len(kw_distinct())] == sep()` and the
keyword-slice clause fail.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the rendered modifier value and its placement in the template — is
modelled **deeply** (the spelled-out `modifier`/`fragment` concatenation and the
verified building loops), not hidden behind an axiom about the function under
change. There is **no consumed `@ContractOnly` axiom**: the `axioms` region is
empty. The only out-of-band trust point is the A-reference of A3/A4, which G-AX
validates against the real percent-template substitution.

## C. verify(model) ⇒ resolved

`render_fragment` verifies only if its output equals
`function + "(" + modifier(distinct) + operands + ")"` with
`modifier(True) == DISTINCT + space` (A3/A4) — so when `distinct` is requested
the keyword is necessarily separated from the operands by a space (the explicit
separation postconditions). By R (`str` ↔ `List[int]`, A1) and by G-AX (the deep
model equals the real template substitution with `'DISTINCT '`, A-reference), a
verified `render_fragment` equals the SQL fragment the gold-patched
`Func.as_sql` produces. The gold patch makes the harness `resolved`
(the F2P query `Count(Case(When(...)), distinct=True)` then renders the valid
`COUNT(DISTINCT CASE WHEN ...)` instead of the invalid `COUNT(DISTINCTCASE
WHEN ...)`). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited template render — and
the gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: reference-callee soundness (G-AX) and refinement fidelity (this
document, G-EQ).
