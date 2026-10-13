# refinement.md — sympy__sympy-16766

The operation-by-operation correspondence between `model.py`'s implementation
(the `print_indexed` impl region and the deep `render_indexed` / `join_sep`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A-consumed** (proof uses an axiom's `Ensures`), **A-reference**
(a deep model validated == a real callee by G-AX), or **I** (identical concrete
operation). The claim: *any implementation that verifies against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on
the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The assembly site — `PythonCodePrinter._print_Indexed` (added at `sympy/printing/pycode.py:360`)

Gold hunk:
```
+    def _print_Indexed(self, expr):
+        base = expr.args[0]
+        index = expr.args[1:]
+        return "{}[{}]".format(str(base), ", ".join([self._print(ind) for ind in index]))
```

| # | model.py impl op (`print_indexed`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `name: List[int]` | `str(base)` where `base = expr.args[0]` | R | the carrier name `str` ↔ `List[int]` code points (mapping.md §2); `str()`/`_sympystr` of the carrier is unchanged ⇒ taken as the input carrier (§B). |
| A2 | parameter `index_renderings: List[PSeq[int]]` | `[self._print(ind) for ind in index]` where `index = expr.args[1:]` | R | each index AST node ↔ its `str` rendering ↔ `PSeq[int]`; the dispatcher `self._print` is unchanged ⇒ the index renderings are taken as the input carrier (§B). |
| A3 | `n = len(index_renderings)`, precondition `n >= 1` | the slice `expr.args[1:]` (always non-empty for an `Indexed`) | I/R | index count; an `Indexed` always carries ≥1 index (`Indexed.__new__` raises otherwise — mapping.md §2). |
| A4 | `else`/loop building `joined == join_sep(idx)` | `", ".join([self._print(ind) for ind in index])` | R | `", ".join(renderings)` ↔ `join_sep(ToSeq(index_renderings))` (the separator-joined concatenation, `, ` between adjacent members, modeled deeply in the `pure` region); the loop is a faithful materialization of the join, invariant `joined == join_sep(idx.drop(i))`. |
| A5 | `return nm + PSeq(91) + joined + PSeq(93)` | `"{}[{}]".format(str(base), <join>)` | R | `"{}[{}]".format(name, body)` ↔ `name` + `[` + `body` + `]` = `nm + PSeq(91) + joined + PSeq(93)`; `"["`=`PSeq(91)`, `"]"`=`PSeq(93)` (mapping.md §2). This is the assembly under change. |

The discriminating content of the change is that an element-access expression
is rendered **at all** as the clean `name[idx0, idx1, ...]` string — with the
`, `-joined indices inside `[ ]` and **no surrounding annotation**. Pre-patch,
`PythonCodePrinter` had no `_print_Indexed`, so the node fell through to the
generic unsupported-node fallback (`codeprinter.py:490-492`), and `doprint`
prepended a fixed `"  # Not supported in Python:\n  # Indexed\n"` comment block
to the emitted source. `model_prepatch.py` reproduces that fallback (it prepends
the fixed annotation prefix to the same clean body) and **fails** the
postcondition `Result() == render_indexed(ToSeq(name), ToSeq(index_renderings))`
exactly because of the nonempty leading prefix — the spec sensing the change
(G-DIFF). The multi-index `, ` separator (the F2P observes `p[0, 1]`) is pinned
by `join_sep` / clause A4.

## B. The element-rendering callees — `str(base)` and `self._print(ind)` (unchanged)

`_print_Indexed` calls `str(base)` to render the carrier name and
`self._print(ind)` to render each index. The gold patch does **not** touch
either callee (`str`/`_sympystr` of `IndexedBase`, nor the `_print` dispatcher
nor any per-node `_print_*`); only the new assembly is added. The carrier name
and the index renderings are therefore taken as the **input carriers**
`name: List[int]` and `index_renderings: List[PSeq[int]]` — NOT modeled deeply
and NOT axiomatized. There is consequently **no A-consumed axiom** and **no
A-reference deep model of a real callee** in this bundle (the `axioms` region is
empty, and `axiom_check.py` is absent — see mapping.md §3). The pure functions
`join_sep` and `render_indexed` are closed-form spec definitions of the assembly
under change, not contracts about an external callee.

## C. No kind-3 (unexpressible-changed-op) steps

Every step in §A is R or I. The one operation that genuinely changed — adding
the renderer that assembles `name[idx0, idx1, ...]` from the carrier name and
the `, `-joined index renderings — is modeled **deeply** (`render_indexed` /
`join_sep` in the `pure` region, consumed by `print_indexed`'s postcondition),
not hidden behind any axiom. No step is a changed-but-inexpressible operation.

## D. verify(model) ⇒ resolved

`print_indexed` verifies only if its output equals
`render_indexed(ToSeq(name), ToSeq(index_renderings))` exactly (A4–A5), which
pins the rendering to `name` + `[` + (`, `-joined index renderings) + `]`, with
no surrounding text. By R (str ↔ List[int]/PSeq[int]; the literal `[`/`]` ↔
code-point bijection; `", ".join` ↔ `join_sep`; `"{}[{}]".format` ↔ the
concatenation) the verified assembly equals `_print_Indexed`'s post-patch return
on every input, with the carrier name and index renderings (from the unchanged
`str`/`self._print`, §B) passed through identically. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE: F2P `test_PythonCodePrinter`
asserts `prntr.doprint(p[0, 1]) == 'p[0, 1]'`, which holds post-patch and fails
pre-patch where the unsupported-node annotation is prepended; the P2P printer
tests are unaffected by the additive method). The sole trust point is
refinement fidelity (this document, G-EQ); there are no axioms to audit.
