# refinement.md — sympy__sympy-22456

The operation-by-operation correspondence between `model.py`'s implementation
(the `rebuild_from_args` impl region and the deep model of the reconstruction)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses an axiom's `Ensures`), **A-reference** (a deep
model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The fix

The gold patch makes the atomic string token `String` satisfy the universal
`Basic` argument-invariance `expr.func(*expr.args) == expr`. `String` holds its
defining `text` in `not_in_args`, so `String.args == ()`. Pre-fix `String`
inherited `Basic.func` (returns the class), so `func(*args)` was `String()`,
which fails in `Token.__new__` because the `text` slot is neither supplied
positionally nor defaulted. The fix overrides `func` to return a nullary
callable yielding the same object (and `kwargs()` to return `{}`), so
`func(*args)` returns the original token unchanged.

Gold hunks (`sympy/codegen/ast.py`):
```
- class String(Token):
+ class String(Atom, Token):
  ...
+     def kwargs(self, exclude = (), apply = None):
+         return {}
+
+     #to be removed when Atom is given a suitable func
+     @property
+     def func(self):
+         return lambda: self
```
(plus the enabling `from sympy.core.expr import Expr, Atom` import and a removed
blank line — neither carries behaviour the F2P test observes.)

## Operation correspondence — `rebuild_from_args` ↔ `String.func(*String.args)`

| # | model.py impl op (`rebuild_from_args`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameter `s: Atomic` with field `text: List[int]` | the `String` instance `st` with attribute `text: str` | R | the rich `String` token is modelled by its single defining facet `text`; `str` ↔ `List[int]` of code points (mapping.md §2). Token equality (`Token.__eq__`: same class + all slots equal) reduces, for the single-slot `String`, to text equality — modelled as `PSeq[int]` equality. |
| 2 | `arg_count(s) == 0` (pure helper, fixed at 0) | `len(st.args) == 0` — `String.args == ()` because `text` is `not_in_args`, so `Basic.__new__` receives no positional args | R | the positional-argument list is modelled by its length; for this atomic token it is empty. The reconstruction therefore consumes zero positional elements (mapping.md §1). |
| 3 | the result is a token carrying EXACTLY the original text (`ToSeq(Result().text) == ToSeq(s.text)`), produced by the text-preserving rebuild loop | `st.func(*st.args)` post-fix = `(lambda: self)()` = `st` | A-reference | the changed reconstruction operation is modelled **deeply**: the impl loop copies the original `text` element-for-element into the rebuilt token, mirroring the fact that the new `func` returns the SAME object (which trivially carries the original text), independent of the empty argument list. There is **no consumed axiom** — the proof depends on no `@ContractOnly`. Instead the deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs the real `String.func(*String.args)` and asserts it equals the original token (full token equality), with `rebuilt.text == st.text`, on F2P + boundary + 20000 fuzz texts. |
| 4 | `return Atomic(rebuilt_text)` (a fresh token, full permission) | the returned reconstructed token | R | object construction of the modelled token; the F2P test compares the rebuilt token to the original by `==`, which is text equality for `String` (step 1). |

The pre-existing `kwargs`-invariance (`func(**kwargs()) == self`) holds both
before and after the fix, so it is not the discriminating behaviour; it is
checked for completeness by axiom_check.py but the F2P discriminator is the
**args**-invariance (the new `assert st.func(*st.args) == st`).

## The differential (G-DIFF)

The discriminating content of the change lives in step 3: the reconstruction
must reproduce the original text WITHOUT reading it from the empty positional
argument list. `model_prepatch.py` keeps the spec byte-identical and reproduces
the pre-fix reconstruction — a generic positional rebuild that can only source
the text from `args` (length `arg_count(s) == 0`), so it produces an EMPTY text
and **fails** the postcondition `ToSeq(Result().text) == ToSeq(s.text)` for any
non-empty text. This is exactly the spec sensing the change: pre-fix
`String.func(*String.args)` cannot recover the excluded `text` slot (the real
code raises `TypeError: No value for 'text' given`; the model captures the
loss of the text payload, which is the same broken invariance). G-AX confirms
the pre-fix raise vs the post-fix identity directly on the real `String`.

## No kind-3 (unexpressible-changed-op) steps

Every step above is R or A-reference. The one operation that genuinely
*changed* — the atomic token's self-reconstruction from its arguments — is
modelled **deeply** (the spelled-out text-preserving rebuild in
`rebuild_from_args`, an **A-reference**), not hidden behind an axiom about the
function under change. There is **no A-consumed axiom**: the proof consumes no
`@ContractOnly` contract. `Basic.func`, `Basic.args`, and `Token.__new__` are
SymPy core/codegen code reproduced faithfully in the skeleton, not axiomatized.

## verify(model) ⇒ resolved

`rebuild_from_args` verifies only if its result carries exactly the original
text (step 3) — i.e. only if the reconstruction satisfies argument invariance
even on non-empty text. By R (str ↔ List[int]; token equality ↔ text equality;
`args` ↔ its length) the verified reconstruction equals
`st.func(*st.args) == st` on the tested inputs; by G-AX the deep model equals
the real `String.func(*String.args)` (A-reference) post-fix. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited deep model — and the gold patch resolves
(G-RESOLVE). The single trust point is refinement fidelity (this document,
G-EQ) plus the executable A-reference soundness check (G-AX); there is no axiom
trust point because no axiom is consumed.
