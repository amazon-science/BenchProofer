# mapping.md — sympy__sympy-14248

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 9986b38181cdd556a3f3411e553864f11912244e`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each callee.

Repo files under change: `sympy/printing/str.py`, `sympy/printing/latex.py`,
`sympy/printing/pretty/pretty.py`.

## 0. Scope of the model (what `Solution.lean` pins, and why it suffices)

The gold patch fixes one behaviour across several printers: a sum of matrix
expressions must render a negated summand as a *subtraction* (`a - b`) instead
of an addition of a negative (`a + (-1)*b` / `a + -b`). The behaviour-carrying
operation is the **sign-folding join** of the already-rendered term strings of
a `MatAdd`.

`Solution.lean` models that join (`StrPrinter._print_MatAdd`, the body changed
by the str.py hunk) **deeply** as `joinSignedMatrixTerms`. This single modeled
function is the load-bearing one for the differential because:

* `sympy.printing.codeprinter.CodePrinter` subclasses `StrPrinter`
  (`codeprinter.py:38`) and does **not** override `_print_MatAdd`. So the
  patched `str.py._print_MatAdd` is the exact method exercised by the ccode,
  fcode, jscode, julia, octave and rcode F2P tests (7 of the 8 changed test
  files reduce to this one method).
* `latex.py._print_MatAdd` (post-patch, `latex.py:1480`) uses a **byte-identical
  algorithm** over its own term strings (`self._print(t)`); only the per-term
  renderer differs, and that renderer is the unchanged input bridge. The model
  therefore captures the latex behaviour up to the per-term renderer (R-bridge).

Two sites are deliberately **not** modeled (documented, not hidden):

* `_print_MatMul` (str.py + latex.py): pulls a leading negative numeric
  coefficient out as a `-` prefix. This is a *separate* behaviour with its own
  branch; it is rendered by the same `latex`/`str` F2P assertions but is an
  independent algorithm. Modeling MatAdd already discriminates the headline bug
  (`A - A*B - B`), so the bundle scopes to MatAdd for a clean, faithful spec
  rather than a weaker spec spanning two algorithms. The MatMul hunk ships in
  `patch.diff` (gold verbatim) so G-RESOLVE still exercises it.
* `pretty.py._print_MatAdd`: same behaviour rendered onto a 2-D `prettyForm`
  canvas (`stringPict`), a drawing primitive Velvet's value fragment does not
  model. Its content (fold a leading-negative term into a `' '` gap rather than
  a `' + '` gap) is the SAME sign decision the modeled str join makes; the
  canvas is the only difference. Out of `Solution.lean` scope; in `patch.diff`.

The frozen spec is strong enough that the pre-patch `_print_MatAdd`
(`' + '.join(terms)`) fails it on the discriminating input (a term carrying a
leading `-`), which is exactly the F2P-observed bug — see refinement.md §D and
`Solution_prepatch.lean`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `joinSignedMatrixTerms (terms : List (List Char))` | `StrPrinter._print_MatAdd(self, expr)` — `sympy/printing/str.py:313` (post-patch body `str.py:321-334`) | the modeled changed function (matrix-sum sign-folding join) |
| `joinSignedTerms (ts : List (List Char))` *(deep model — pure)* | the post-patch join body of `_print_MatAdd` (`str.py:321-334`) | pure spec: rendering of a non-empty term-string sequence |
| `joinTail` / `tailPiece` / `termSign` / `termBody` *(pure)* | the per-term `if t.startswith('-')` sign split + `l.extend([sign, t])` + final `' '.join` of `_print_MatAdd` | pure spec helpers: one non-leading term's contribution |
| input element `t : List Char` | `self.parenthesize(arg, precedence(expr))` for `arg in expr.args` — `str.py:29`, `precedence` `str.py` import | unchanged callee producing each rendered term string (R-bridge input) |

The pre-patch repo symbol the change removes (refinement audit only, not in the
consumer spec view): the one-liner `' + '.join([self.parenthesize(arg,
precedence(expr)) for arg in expr.args])` (`str.py:314-315` @ base_commit).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| one rendered term string `t` (a Python `str`) | `List Char` | `t` ↔ `t.toList`; `t.startswith('-')` ↔ `t.head? = some '-'`; `t[1:]` ↔ `t.drop 1`; `str` concat ↔ `List` `++`; `' '.join` ↔ interspersing `' '` |
| the sequence of term strings `[parenthesize(a, …) for a in expr.args]` | `List (List Char)` | element-wise as above; `len(expr.args)` ↔ `terms.length`; sympy guarantees a `MatAdd` has `≥ 2` args, so `terms ≠ []` (the method `require`) always holds |
| `self.parenthesize(arg, precedence(expr))` | the input element (identity bridge) | the per-term renderer is **unchanged** by the patch; both the shadow and the oracle in G-CONF call the SAME real `parenthesize`, so it is the shared input, not modeled. Its output is a plain `str`. |
| a leading minus glyph `'-'` (U+002D) | Lean `Char` `'-'` | `Char.ofNat 45` ↔ `'-'`; the sole character the algorithm branches on |

No Velvet `mut`-frame concern: `terms` is read-only and is NOT declared `mut`
(directive 5); the only `mut` locals (`result`, `i`) are genuine accumulators.

## 3. Callee provenance — NO axioms, NO A-references (kind-A is empty)

This bundle axiomatizes **nothing**. The changed string operation is modeled
**deeply** by `joinSignedTerms`/`joinTail`/`tailPiece` in the `pure` region (the
`axioms` region of `Solution.lean` is empty). The one callee the real method
uses, `StrPrinter.parenthesize`, is **unchanged** by the patch and supplies the
input term strings identically to both sides of the G-CONF differential, so it
is the R-bridge input (§2), not a contract requiring an axiom (SPEC_GUIDE §0.7:
never axiomatize what you can share as input; never ship a dead axiom).

**Soundness witness (G-AX):** because there is no axiom to falsify, `axiom_check.py`
instead executes the REAL patched `StrPrinter._print_MatAdd` on the issue/F2P
boundary inputs plus 20 000 randomized matrix sums and asserts the deep model
`joinSignedTerms` (its `shadow_join` transliteration) equals it on every input —
backing the "no axioms" claim with execution. Imports only stdlib + the repo's
own (patched) sympy. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14248`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `joinSignedTerms`/`joinTail`/`tailPiece`/`termSign`/`termBody`
(all R/I-tagged ops) to Python and feeds both the shadow and the oracle the
identical real `parenthesize` term strings (the shared R-bridge input). There
are no A-tagged callees in the impl region, so `conf_skip=false` and the shadow
is pure R/I.
