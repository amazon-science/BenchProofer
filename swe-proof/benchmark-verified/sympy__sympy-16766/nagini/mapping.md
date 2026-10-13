# mapping.md — sympy__sympy-16766

Binds every `model.py` symbol to its repository counterpart at
`base_commit = b8fe457a02cc24b3470ff678d0099c350b7fef43`, states the type
abstraction, and records callee provenance.

Repo file under change: `sympy/printing/pycode.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `print_indexed(name, index_renderings)` | `PythonCodePrinter._print_Indexed(self, expr)` — added at `sympy/printing/pycode.py:360` (immediately after `_print_Not`, body lines 360-363 post-patch) | the modeled changed function: the Python-source renderer for an element-access (`Indexed`) expression |
| `name` (param) | `str(base)` where `base = expr.args[0]` (`sympy/printing/pycode.py:361` post-patch) — the carrier's textual name produced by the unchanged `str()`/`_sympystr` of `IndexedBase` (`sympy/tensor/indexed.py:517`) | unchanged callee output, taken as input carrier |
| `index_renderings` (param) | `[self._print(ind) for ind in index]` where `index = expr.args[1:]` (`sympy/printing/pycode.py:362-363` post-patch) — each index expression rendered by the unchanged dispatcher `self._print` (`sympy/printing/printer.py`) | unchanged callee outputs, taken as input carrier |
| `join_sep(s)` *(deep model)* | `", ".join([...])` (`sympy/printing/pycode.py:363` post-patch) | pure spec: separator-joined concatenation of the index renderings |
| `render_indexed(name, idx)` *(deep model)* | `"{}[{}]".format(str(base), ", ".join([...]))` (`sympy/printing/pycode.py:363` post-patch) | pure spec: the full `name[idx0, idx1, ...]` assembly under change |
| `sep()` | the join separator literal `", "` | pure spec: separator as code points `PSeq(44, 32)` |

The pre-patch repo state the change repairs (for the refinement audit, not
referenced from the consumer spec view): `PythonCodePrinter` has **no**
`_print_Indexed` method, so `CodePrinter._print` dispatches an `Indexed` node to
`_print_not_supported` (`sympy/printing/codeprinter.py:490-492`), which records
the node in `self._not_supported` and returns `self.emptyPrinter(expr)`; in
`doprint` (`codeprinter.py:65,105-118`) the recorded unsupported nodes cause a
leading comment block — `"  # Not supported in Python:\n  # Indexed\n"` — to be
prepended to the emitted source. The pre-patch output of the renderer is
therefore the bare rendering preceded by that fixed annotation prefix.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (`str(base)` carrier name, each `self._print(ind)` index rendering, and the `_print_Indexed` return) | `List[int]` / `PSeq[int]` of Unicode code points | `s[k]` ↔ `ord(s[k])`; `len(s)` ↔ `len`; `str` `+`/`%`/`.format` concatenation ↔ `PSeq` `+`; an empty `str` ↔ `empty_seq()` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the `List[int]` as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| the index-rendering list `[self._print(ind) for ind in index]` | `List[PSeq[int]]` (pure view `PSeq[PSeq[int]]`) | each `self._print(ind)` ↔ one `PSeq[int]`; the list ↔ `PSeq[PSeq[int]]` via `ToSeq` |
| `", ".join(parts)` | `join_sep(ToSeq(parts))` | separator `, ` between adjacent members, none at the ends |
| the literals `"["`, `"]"` | `PSeq(91)`, `PSeq(93)` | `ord('[')==91`, `ord(']')==93` |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]` /
`PSeq[int]` throughout.

`expr.args[0]` is the carrier (an `IndexedBase`); `expr.args[1:]` are the index
expressions; `Indexed.__new__` (`sympy/tensor/indexed.py:140-159`) raises
`IndexException` if constructed with no index, so an `Indexed` always has at
least one index — modeled by the precondition `len(index_renderings) >= 1`.

## 3. Callee provenance (kind-A)

There are **no axioms** in this bundle (the `axioms` region is empty) and there
is **no A-reference deep model of an external callee**. Both callees the new
renderer invokes — `str(base)` (the carrier name) and `self._print(ind)` (the
per-index dispatcher) — are **unchanged** by the gold patch, so their outputs
are taken as the **input carriers** `name: List[int]` and
`index_renderings: List[PSeq[int]]`, not modeled deeply and not axiomatized.
The pure functions `join_sep` / `render_indexed` are closed-form specification
definitions of the assembly under change (the `, `-join and the `name[...]`
bracketing), not contracts about an external callee. Consequently
`axiom_check.py` is **absent** — there is nothing to execute in-container
against a real callee (G-AX has no obligation here).
