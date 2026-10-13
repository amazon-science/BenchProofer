# mapping.md — sympy__sympy-13372

Model ↔ repo symbol binding, type abstraction, and callee provenance.
All file:line references are at `base_commit`
`30379ea6e225e37833a764ac2da7b7fadf5fe374`.

Repo file under change: `sympy/core/evalf.py`.

## 1. Changed function under specification

| model symbol | repo symbol | repo location (base_commit) |
|---|---|---|
| `numericComplexResult (realPart imagPart : Part) (prec : Int)` | the `except KeyError:` fallback body of `evalf` that splits `x` into real/imaginary components and assembles the result tuple `r = re, im, reprec, imprec` | `sympy/core/evalf.py:1284` (`def evalf`), fallback block lines `1295`–`1312` |

The repo code at that block (base_commit):

```python
xe = x._eval_evalf(prec)
re, im = xe.as_real_imag()                 # line 1295
if re.has(re_) or im.has(im_):
    raise NotImplementedError              # 1297
if re == 0:                                # 1298  -> exact-zero real component
    re = None
    reprec = None
elif re.is_number:                         # 1301  -> numeric real component
    re = re._to_mpmath(prec, allow_ints=False)._mpf_
    reprec = prec                          # 1303
# <<< base_commit: NO else branch — reprec left UNBOUND if re is non-numeric >>>
if im == 0:                                # 1304  -> exact-zero imaginary component
    im = None
    imprec = None
elif im.is_number:                         # 1307  -> numeric imaginary component
    im = im._to_mpmath(prec, allow_ints=False)._mpf_
    imprec = prec                          # 1309
# <<< base_commit: NO else branch — imprec left UNBOUND if im is non-numeric >>>
r = re, im, reprec, imprec                 # 1310  -> UnboundLocalError when unbound
```

`numericComplexResult` models the body executed once the `KeyError` fallback is
entered and `x._eval_evalf(prec).as_real_imag()` has produced the two components:
it receives the two components (`realPart`, `imagPart`) and the target precision
`prec`, and returns the assembled result record — or signals that no numeric
result is available. The outer machinery (`evalf_table[x.func]` dispatch, the
`KeyError`/`AttributeError` `try`/`except`, the `subs`/`verbose`/`chop`/`strict`
post-processing) is control context that selects/uses this block; it is not part
of the modeled data-flow and is not modeled.

## 2. Type abstraction (the Lean↔Python bijection)

A component (`re` or `im`, a sympy `Expr`) is consulted through exactly two
unchanged sympy observations before the modeled step assembles the result:

  * its **classification** — is it an exact zero (`expr == 0`), a concrete
    numeric quantity (`expr.is_number`), or neither;
  * for a numeric component, its **converted value**
    (`expr._to_mpmath(prec, allow_ints=False)._mpf_`).

These two observations are abstracted into the `Part` carrier. The proof relies
only on the classification being a three-way disjoint tag and the converted
value being some fixed handle — never on a concrete numeric value — so the exact
mpf payload is irrelevant to the modeled control flow.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a sympy component `Expr` (`re` / `im`) | `Part` | `(status, value)`: `status` = its classification, `value` = its converted-value handle (used only when `status = numeric`) |
| `expr == 0` (exact-zero test) | `status = PartStatus.exactZero` | the `if re == 0` / `if im == 0` branch |
| `expr.is_number` (numeric test) | `status = PartStatus.numeric` | the `elif re.is_number` / `elif im.is_number` branch |
| neither (still symbolic) | `status = PartStatus.nonNumeric` | the missing-`else` case the fix adds |
| `expr._to_mpmath(prec, allow_ints=False)._mpf_` | `value : Int` (opaque handle) | the converted numeric payload; modeled as an abstract `Int` (value never inspected by the spec) |
| target working precision `prec` | `prec : Int` | identity |
| `r = (re, im, reprec, imprec)` result tuple | `EvalResult` record | `re ↔ realValue`, `im ↔ imagValue` (`None ↔ none`), `reprec ↔ realPrec`, `imprec ↔ imagPrec` |
| `raise NotImplementedError` (the fix's new `else`) | `out = none` | signalling "no numeric result available"; the `except`-chain at `evalf` lines 1399/1406 catches it as the fall-back-to-ordinary-evalf path |

`Char`/string indexing is not used (this is a control-flow, not a per-codepoint,
change). The carrier is the abstract `Part`/`EvalResult` record because the
operation is the assembly/short-circuit logic over the unchanged classification,
not arithmetic over a concrete value domain.

## 3. Callee provenance (axioms region)

There are **no consumed axioms** and **no A-reference deep model**. The two
sympy observations folded into `Part` (`== 0`, `is_number`, and `_to_mpmath`)
are UNCHANGED by the fix — the fix adds only the two missing `else` clauses; it
does not touch how a component is classified or converted. They are abstracted
as read-only inputs (the `Part` carrier), not re-derived and not pinned to any
value, so there is **nothing to validate against a real callee**: no
`axiom_check.py`, and `meta.json gates.G-AX.status = "skip"`.

The single behaviour the fix introduces — "a non-numeric component ⇒ signal no
numeric result instead of fabricating/crashing" — is modeled DEEPLY by `evalSpec`
and the `do` block (the missing-`else` ⇒ `none` branch), with the same
control/data flow as `patch.diff`. It is not hidden behind an axiom.

## 4. Why the bug is an `UnboundLocalError` and how the model expresses it

At base_commit, when a component is neither an exact zero nor `is_number` (e.g.
`re` is still a symbolic expression such as `Max(0, y)`), neither the `if` nor
the `elif` branch runs, so the local `reprec` (resp. `imprec`) is never bound.
The next statement `r = re, im, reprec, imprec` then references the unbound local
→ `UnboundLocalError: local variable 'reprec' referenced before assignment`
(the traceback in the issue). The gold fix adds `else: raise NotImplementedError`
to each ladder, so a non-numeric component cleanly raises the same
`NotImplementedError` the function already raises elsewhere — caught by the
caller's fall-back-to-ordinary-evalf path.

Lean cannot host a literally-unbound local. The pre-patch skeleton
(`Solution_prepatch.lean`) expresses the defect faithfully as **never branching
on the non-numeric case at all**: it unconditionally assembles the result record
(treating every non-exact-zero component as if it were numeric, i.e. fabricating
a value+precision for a non-numeric component — the model of "reprec/imprec used
when they were never set"). It never yields `none`. That violates the frozen
discriminating postcondition `(re non-numeric ∨ im non-numeric) → out = none`,
so `prove_correct` fails (G-DIFF): the buggy skeleton cannot be shown equal to
`evalSpec`, which returns `none` exactly on the non-numeric case.

## 5. G-CONF fuzz seed

`conf_skip = true`. The modeled step assembles the result from an ABSTRACT
classification produced by sympy's symbolic engine on arbitrary `Expr` trees;
there is no database-free numeric R/I shadow reconstructable from the abstract
`Part` carrier (status tag + value handle). The impl region is the deep model of
the changed control flow, with no transliterable arithmetic R/I op. No fuzz
seed; `conformance_check.py` is a `status=skip` stub. Soundness rests on
G-VERIFY + G-DIFF + G-RESOLVE + G-EQ. (sympy-13480 precedent.)
