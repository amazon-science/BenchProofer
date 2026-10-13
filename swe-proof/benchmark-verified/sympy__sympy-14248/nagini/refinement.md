# refinement.md — sympy__sympy-14248

The operation-by-operation correspondence between `model.py`'s implementation
(the deep folds `matadd` / `matmul` and the verified loops `render_sum` /
`render_product`) and `patch.diff` (the gold patch).  Each step is tagged
**R** (type refinement), **A** (axiomatized callee — none here, split would be
**A-consumed** / **A-reference**), or **I** (identical concrete operation).

`patch.diff` is the **gold patch verbatim** (it applies cleanly at
`base_commit` and is the real correctness oracle, G-RESOLVE).  It edits three
printer files (`str.py`, `latex.py`, `pretty/pretty.py`).  These implement
**three** distinct rendering behaviours, NOT two:

  - a spaced-binary-minus matrix-sum join (`str`/`latex` `_print_MatAdd`),
    modelled by `matadd` / `render_sum` (§A);
  - a negative-leading-coefficient matrix-product sign (`str`/`latex`
    `_print_MatMul`), modelled by `matmul` / `render_product` (§B);
  - a single-space matrix-sum join that keeps the minus attached to the term
    (`pretty` `_print_MatAdd`), a GENUINELY DIFFERENT algorithm from the first,
    modelled by its own deep fold `matadd_space` / `render_sum_space` (§A2).

Each site that is its own algorithm is modelled deeply with its own postcondition
and its own pre-patch discriminator (`model_prepatch.py`, `model_prepatch_2.py`,
`model_prepatch_3.py`).  Sites that share a byte-identical hunk with a modelled
site (only `latex._print_MatAdd` ↔ `str._print_MatAdd`) are R-refinements of the
shared fold and need no separate model (§C).

The claim: any implementation that verifies against this frozen spec, refined
per the maps below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.

There are **no axioms**: all three changed behaviours are modelled **deeply**
(the output sequence is spelled out as a front-recursive fold over the abstract
child-render sequence).  The per-child rendering is an INPUT (R), so nothing
opaque is consumed and there is no G-AX obligation.

## A. The sum-rendering site — `_print_MatAdd` (`sympy/printing/str.py:314`)

Gold hunk:
```
-        return ' + '.join([self.parenthesize(arg, precedence(expr))
-            for arg in expr.args])
+        terms = [self.parenthesize(arg, precedence(expr))
+             for arg in expr.args]
+        l = []
+        for t in terms:
+            if t.startswith('-'):
+                sign = "-"; t = t[1:]
+            else:
+                sign = "+"
+            l.extend([sign, t])
+        sign = l.pop(0)
+        if sign == '+':
+            sign = ""
+        return sign + ' '.join(l)
```

| # | model.py impl op (`render_sum` / its pure spec) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `terms: List[PSeq[int]]` | `terms = [self.parenthesize(arg, precedence(expr)) for arg in expr.args]` | R | the list of already-rendered term strings ↔ `List[PSeq[int]]` of code points (mapping.md §2). The per-term render `self.parenthesize(...)` is the input, not modeled. |
| A2 | `is_neg(t) == (len(t) > 0 and t[0] == 45)` | `t.startswith('-')` | R | leading-minus test on a `str` ↔ on a code-point `PSeq` (45 = `'-'`). |
| A3 | `body(t) == t.drop(1)` when negative, else `t` | `t = t[1:]` when negative | R | `str` slice-off-first ↔ `PSeq.drop(1)`. |
| A4 | for a non-leading term: `contrib(t) == sep_minus()+body(t)` if `is_neg` else `sep_plus()+body(t)` | `sign = "-"/"+"`, `l.extend([sign, t])`, later `' '.join(l)` joins `sign` and `t` with a single space, i.e. `' - '+t[1:]` or `' + '+t` between successive terms | R + I | the gold builds the alternating `[sign, term]` list and `' '.join`s it; under the code-point refinement that is exactly `' - '`/`' + '` prefixing each non-leading term's body. `sep_minus()=PSeq(32,45,32)`, `sep_plus()=PSeq(32,43,32)`. |
| A5 | leading term: `lead(t) == PSeq(45)+body(t)` if `is_neg` else `body(t)`; assembled as `matadd = lead(terms[0]) + add_tail(terms,1)` | `sign = l.pop(0); if sign=='+': sign=""; return sign + ' '.join(l)` | R + I | popping the first `sign` and blanking it when `'+'` is exactly "first term carries no infix separator; a leading-minus first term keeps its `-`". The fold `add_tail` is the `' '.join` of the remaining `[sign, t]` pairs. |

The discriminating content — a term whose render starts with `-` must use a
binary minus (` - ` + stripped body), and the first term carries no `+` — lives
in `contrib` / `lead`.  The pre-patch `' + '.join(terms)` joins every term with
`' + '` and strips no sign; `model_prepatch.py` reproduces that (loop body
`sep_plus()+t`, bare first term) and **fails** the invariant
`ToSeq(result) == add_tail(ToSeq(terms), i)` — the spec sensing the change
(G-DIFF).  F2P witness: `str(A - A*B - B)` has terms `["-B","-A*B","A"]`; gold →
`"-B - A*B + A"`, pre-patch → `"-B + -A*B + A"`.

## A2. The single-space sum-rendering site — pretty `_print_MatAdd` (`sympy/printing/pretty/pretty.py:821`)

This is a **distinct algorithm** from §A — not an R-refinement of `matadd`.  The
gold builds the sum left-to-right: the first term is emitted in full; for a
**structurally negative** non-leading term — `S(item.args[0]).is_negative`, a
test on the expression tree, NOT on the rendered text — it appends a single
space and then the term **in full** (nothing stripped), and for any other
non-leading term it appends `' + '` then the term.  So a structurally-negative
non-leading term is separated by `' '` and emitted whole, whereas §A separates
a text-leading-`-` term by `' - '` and strips the `-`.  The structural test can
disagree with the rendered text (e.g. `y*B` with `Symbol('y', negative=True)`:
`S(y).is_negative` is True but the picture `y⋅B` has no leading `-`), so the
fact is carried as its own boolean input `negs[k]` (mapping.md §2.2) — the same
input-refinement discipline as `neg` in §B.  It is modelled by its own deep
fold (`matadd_space` / `render_sum_space`), with `contrib_space(t, n)` carrying
the single-space contribution keyed on `n`.

Gold hunk:
```
-        return self._print_seq(expr.args, None, None, ' + ')
+        s = None
+        for item in expr.args:
+            pform = self._print(item)
+            if s is None:
+                s = pform     # First element
+            else:
+                if S(item.args[0]).is_negative:
+                    s = prettyForm(*stringPict.next(s, ' '))
+                    pform = self._print(item)
+                else:
+                    s = prettyForm(*stringPict.next(s, ' + '))
+                s = prettyForm(*stringPict.next(s, pform))
+        return s
```

| # | model.py impl op (`render_sum_space` / its pure spec) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A2.1 | parameter `terms: List[PSeq[int]]` | `pform = self._print(item)` over `expr.args` | R | the per-item rendered picture (single-line on the F2P cases) ↔ `List[PSeq[int]]` of code points; the per-item render is the input, not modelled. |
| A2.2 | parameter `negs: List[bool]`, `negs[k]` paired with `terms[k]` (`Requires(len(negs)==len(terms))`) | `S(item.args[0]).is_negative` | R | the truthiness of the structural negativity test on item k's leading argument, carried as a boolean input — the same input-refinement as `neg` in §B2.  NOT derivable from the rendered text: `S(y).is_negative` can be True while the picture `y⋅B` has no leading `'-'` (mapping.md §2.2); the earlier `is_neg(t)` abstraction was unfaithful (G-PANEL-2 counterexample `-A + y*B`). |
| A2.3 | non-leading term: `contrib_space(t, n) == sep_space()+t` if `n` else `sep_plus()+t` | neg branch: `stringPict.next(s,' ')` then `stringPict.next(s, pform)` (full item, nothing stripped); else `stringPict.next(s,' + ')` then `stringPict.next(s, pform)` | R + I | the single-space-then-full-term vs `' + '`-then-term horizontal concatenation, decided by the structural fact `n`. `sep_space()=PSeq(32)`, `sep_plus()=PSeq(32,43,32)`. Crucially the term is NOT stripped (no `body`) and the decision is `n`, unlike §A. |
| A2.4 | leading term: `terms[0]` (emitted in full); assembled as `matadd_space = terms[0] + add_tail_space(terms, negs, 1)` | `if s is None: s = pform` (first element, full) | R + I | first term carries no infix separator and keeps its own sign. The fold `add_tail_space` is the left-to-right horizontal concatenation of the remaining contributions. |

The discriminating content — a structurally-negative non-leading term joined
by a single space and kept whole, the decision keyed on `negs[k]` — lives in
`contrib_space` / `matadd_space`.  The pre-patch
`_print_seq(expr.args, None, None, ' + ')` joins every term with `' + '` and
consults no negativity fact; `model_prepatch_3.py` reproduces that (loop body
`sep_plus()+t`) and **fails** the invariant
`ToSeq(result) == add_tail_space(ToSeq(terms), ToSeq(negs), i)` (G-DIFF).
F2P witness: `pretty(A*B*C - A*B - B*C)` has terms `["-A*B","-B*C","A*B*C"]`
with `negs=[True,True,False]`; gold → `"-A*B -B*C + A*B*C"` (the F2P-required
value), §A's str discipline → `"-A*B - B*C + A*B*C"` (extra space, **fails**
the assertion), pre-patch → `"-A*B + -B*C + A*B*C"`.  Beyond the F2P, the
structural/text divergence witness: `pretty(-A + y*B)` with
`Symbol('y', negative=True)` has terms `["-A","y⋅B"]`, `negs=[True,True]`
(`S(y).is_negative` is True though `y⋅B` has no leading `-`); gold →
`"-A y⋅B"`, a rendered-text-decided rival → `"-A + y⋅B"` — rejected by G-PBT
`weak-space-text-negativity`.

## B. The product-leading-sign site — `_print_MatMul` (`sympy/printing/str.py:306`)

Gold hunk:
```
-        return '*'.join([self.parenthesize(arg, precedence(expr))
+        c, m = expr.as_coeff_mmul()
+        if c.is_number and c < 0:
+            expr = _keep_coeff(-c, m)
+            sign = "-"
+        else:
+            sign = ""
+        return sign + '*'.join([self.parenthesize(arg, precedence(expr))
             for arg in expr.args])
```

| # | model.py impl op (`render_product` / its pure spec) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `factors: List[PSeq[int]]` | `[self.parenthesize(arg, precedence(expr)) for arg in expr.args]` over the (coefficient-normalised) `expr` | R | the rendered factor strings of the product `_keep_coeff(-c, m)` when negative, else of `expr` (mapping.md §2). |
| B2 | parameter `neg: bool` | `c, m = expr.as_coeff_mmul(); c.is_number and c < 0` | R | the boolean "negative numeric leading coefficient"; an input refinement of the structural test on the expression tree (mapping.md §2.1). |
| B3 | `joinstar(factors) == factors[0] + mul_tail(factors,1)`, each tail factor prefixed by `star()=PSeq(42)` | `'*'.join([...])` | R + I | `str` join-on-`'*'` ↔ the `*`-prefixed front-recursive fold over the factor sequence. |
| B4 | `matmul = PSeq(45)+joinstar(factors)` if `neg` else `joinstar(factors)`; impl prepends `[45]` iff `neg` | `sign + '*'.join([...])` with `sign = "-"` iff negative-numeric-coeff | R + I | the single leading `'-'` (45) iff `neg`. Coefficient folding (`_keep_coeff(-c, m)`, which drops a unit coefficient) is absorbed into the `factors` input (mapping.md §2.1). |

`model_prepatch_2.py` reverts B4 (drops the `neg` leading minus, matching the
pre-patch `'*'.join(...)` with no `sign`) and **fails** the postcondition
`ToSeq(Result()) == matmul(ToSeq(factors), neg)` (G-DIFF).  F2P witness:
`pretty(-A*B*C)` → `"-A*B*C"` (gold) vs the un-signed product (pre-patch);
`latex(-A) → r"-A"`.

## C. Cross-file site disposition (per-site equivalence, not a blanket "same behaviour")

The gold edits `str.py`, `latex.py`, and `pretty/pretty.py`.  Each site is
disposed of by EITHER (a) a byte-identical hunk to an already-modelled site
(then it is a pure R-refinement of the same fold) OR (b) its own deep model +
pre-patch discriminator.  No site relies on a prose-only "realises the same
behaviour" claim across a genuinely-different algorithm.

- **`latex._print_MatAdd`** — disposition (a), R of `matadd` (§A).  Its gold
  hunk is the **byte-for-byte identical** sign-aware-join loop as
  `str._print_MatAdd` (same `if t.startswith('-'): sign="-"; t=t[1:]` … `sign +
  ' '.join(l)`), only the per-term render differs (latex vs str), which is the
  input.  No separate model needed.
- **`latex._print_MatMul`** — disposition (a), R of `matmul` (§B).  It pulls a
  negative numeric leading coefficient out as a leading `'-'`
  (`if expr.args[0].is_Number and expr.args[0]<0: ... return '-' + ' '.join(...)`):
  the leading-`-` decision and assembly are the same `matmul` shape; the
  inter-factor separator (`' '` vs `'*'`) is part of the rendered-factor input
  framing, not a different sign algorithm.  Modelled by `render_product`/`matmul`.
- **`pretty._print_MatAdd`** — disposition (b), its OWN deep model `matadd_space`
  / `render_sum_space` (§A2).  This is a GENUINELY DIFFERENT algorithm from
  `str._print_MatAdd`: a STRUCTURALLY-negative non-leading term
  (`S(item.args[0]).is_negative`, carried as the input `negs[k]`) is joined by
  a single space and kept WHOLE, whereas the str/latex loop tests the rendered
  text for a leading `-`, joins by `' - '`, and STRIPS the minus.  On the F2P
  input `["-A*B","-B*C","A*B*C"]` (negs `[True,True,False]`) the two disagree
  (`"-A*B -B*C + A*B*C"` vs `"-A*B - B*C + A*B*C"`), and the decision sources
  disagree on e.g. `-A + y*B` with `Symbol('y', negative=True)` (`"-A y⋅B"` vs
  `"-A + y⋅B"`); only the structural single-space form satisfies
  `test_pretty.py::test_MatrixSymbol_printing` and matches the gold callee.  It
  is NOT an R-refinement of `matadd`; modelling it as one would be a kind-3
  step disguised as R.  Its pre-patch discriminator is `model_prepatch_3.py`.

No site is a *changed operation Nagini cannot express*: every step above is R, I,
or a deep model.  The three changed operations — spaced-binary-minus sum join,
product leading-sign, and single-space sum join — are each modelled deeply (no
axiom hides them), so there is no kind-3 step and no A-consumed/A-reference row.

## D. verify(model) ⇒ resolved

`render_sum` verifies only if its output equals the spaced-binary-minus join
`matadd` (§A), `render_sum_space` only if it equals the single-space join
`matadd_space(terms, negs)` (§A2), and `render_product` only if it equals
`matmul` with the leading sign (§B).  These three postconditions pin all three
tested behaviours distinctly — in particular `render_sum_space` forces the
single-space, term-kept-whole discipline decided by the STRUCTURAL fact
`negs[k]`, so a str-style (` - `, minus-stripped) refinement of the pretty site
does NOT verify (it fails `matadd_space`; reproduced by `model_prepatch_3.py`
and G-PBT `weak-space-as-str-discipline`), and a rendered-text-decided rival
(`contrib_space(t, is_neg(t))`) does NOT verify either (G-PBT
`weak-space-text-negativity`; this was the panel's P1/faithfulness
counterexample against the earlier revision).  By the R-refinements (rendered
child `str` ↔ `PSeq[int]`; the child render and the structural negativity /
coefficient tests as boolean inputs) the verified
assemblers equal the gold `_print_MatAdd` / `_print_MatMul` bodies on the
rendered-child inputs the F2P tests exercise; the only cross-file R-claims left
are the byte-identical `latex._print_MatAdd` and the same-shape
`latex._print_MatMul` (§C), each disposed of explicitly.  Therefore a model
satisfying this spec, refined by the maps above, is the gold patch up to type
refinement on every tested site — and the gold patch resolves (G-RESOLVE).  The
single trust point is refinement fidelity (this document, G-EQ); there is no
axiom trust point (no `@ContractOnly`, no G-AX).
