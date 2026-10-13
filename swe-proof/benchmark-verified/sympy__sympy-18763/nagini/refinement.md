# refinement.md — sympy__sympy-18763

The operation-by-operation correspondence between `model.py`'s implementation
(the `format_restriction` impl region plus the deep `assembled` layout model in
the `pure` region) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A-consumed** (proof uses an axiom's `Ensures`),
**A-reference** (a deep model validated == a real callee by G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The single change site — `LatexPrinter._print_Subs` (`sympy/printing/latex.py:706-707`)

Gold hunk:
```
-        return r'\left. %s \right|_{\substack{ %s }}' % (latex_expr,
+        return r'\left. \left(%s\right) \right|_{\substack{ %s }}' % (latex_expr,
                                                          latex_subs)
```

The change inserts a matched scaling delimiter pair `\left(` … `\right)`
*directly around* the first substituted fragment (`latex_expr`); the surrounding
layout and the second substituted fragment (`latex_subs`) are unchanged.

| # | model.py impl op (`format_restriction`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `body: List[int]` | the `latex_expr` `%s` substituent (`latex_expr = self._print(expr)`, line 701) | R | `str` ↔ `List[int]` code points (mapping.md §2); `latex_expr` is an already-rendered fragment, taken as the opaque read-only input `body`. |
| A2 | parameter `cond: List[int]` | the `latex_subs` `%s` substituent (`latex_subs = r'\\ '.join(...)`, lines 704-705) | R | `str` ↔ `List[int]`; `latex_subs` is taken as the opaque read-only input `cond`. The `'\\ '.join(...)` that builds it is UNCHANGED by the patch, so its result is just the input fragment. |
| A3 | `result + [92,108,101,102,116,46,32]` (`open_layout`) | the literal `r'\left. '` prefix of the template | I + R | identical concrete byte sequence; `str` literal ↔ code-point list (mapping.md §2). |
| A4 | `result + [92,108,101,102,116,40]` (`open_delim`) emitted **directly before** the body copy | the `\left(` literal ADDED **directly before** `%s` (the discriminating insertion) | I + R | identical concrete byte sequence, in the same position relative to the body fragment. This is the load-bearing op of the change. |
| A5 | the loop `result.append(body[i])` over `body` | the `%s` substitution of `latex_expr` | R | printf `%s` ↔ verbatim copy of the fragment's code points; the loop reproduces `latex_expr` element-for-element. |
| A6 | `result + [92,114,105,103,104,116,41]` (`close_delim`) emitted **directly after** the body copy | the `\right)` literal ADDED **directly after** `%s` | I + R | identical concrete byte sequence, in the same position relative to the body fragment. The other half of the discriminating insertion. |
| A7 | `result + [32,92,114,105,103,104,116,124,95,123,92,115,117,98,115,116,97,99,107,123,32]` (`mid_layout`) | the literal `r' \right|_{\substack{ '` between the two `%s` | I + R | identical concrete byte sequence; `str` literal ↔ code-point list. |
| A8 | the loop `result.append(cond[j])` over `cond` | the `%s` substitution of `latex_subs` | R | printf `%s` ↔ verbatim copy of the fragment's code points. |
| A9 | `result + [32,125,125]` (`tail`) | the literal `r' }}'` suffix of the template | I + R | identical concrete byte sequence. |
| A10 | `return result` (a `List[int]`) | `return <the assembled str>` | R | the function returns the assembled string; `str` ↔ `List[int]`. The `_print_Subs` result is consumed by the printer purely as character content (the F2P test compares the rendered string equality), so the refinement is observation-preserving. |

The discriminating content of the change — the body fragment is enclosed in its
own matched `\left(` … `\right)` pair — lives in steps **A4** and **A6**
(`open_delim` directly before, `close_delim` directly after the body copy),
captured in the spec by `ToSeq(Result()) == assembled(ToSeq(body), ToSeq(cond))`
together with the structural `take`/`drop` clauses pinning the delimiter pair's
positions. The pre-patch template omits exactly this pair;
`model_prepatch.py` reproduces that (it copies `body` straight after
`open_layout` with no `open_delim`/`close_delim`) and **fails** the
postcondition `ToSeq(Result()) == assembled(ToSeq(body), ToSeq(cond))` — which
is exactly the spec sensing the change (G-DIFF; observed failure at
`model_prepatch.py:96`).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I (no axioms at all). The one operation that genuinely
*changed* — inserting the matched delimiter pair around the body fragment — is
modeled **deeply** as the spelled-out code-point segments `open_delim` /
`close_delim` emitted in their exact positions in the `assembled` layout and the
verified impl loop. There is **no consumed axiom** and **no A-reference deep
model**: the function under change is a pure string-template assembly of two
already-rendered fragments, so there is no unchanged opaque callee whose
behaviour the proof needs (mapping.md §3). Consequently there is no
`axiom_check.py`.

## C. verify(model) ⇒ resolved

`format_restriction` verifies only if its output equals the exact assembled
layout with the body bracketed by its matched delimiter pair (`assembled`, steps
A3–A9) — i.e. only if both `open_delim` (A4) and `close_delim` (A6) are present
in the right positions. By R (`str` ↔ `List[int]`, printf `%s` ↔ verbatim
fragment copy, `str` literals ↔ code-point lists) the verified assembly equals
the gold template
`r'\left. \left(%s\right) \right|_{\substack{ %s }}' % (latex_expr, latex_subs)`
element-for-element on every fragment input. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement — and
the gold patch resolves (G-RESOLVE). The only trust point is refinement fidelity
(this document, G-EQ); there is no axiom-soundness trust point because there are
no axioms.
