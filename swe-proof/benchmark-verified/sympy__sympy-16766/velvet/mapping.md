# mapping.md — sympy__sympy-16766

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = b8fe457a02cc24b3470ff678d0099c350b7fef43`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of the (zero) consumed axioms.

Repo file under change: `sympy/printing/pycode.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `renderAccess (base : List Char) (indices : List (List Char))` | `PythonCodePrinter._print_Indexed(self, expr)` — added by the patch at `sympy/printing/pycode.py:360` (immediately after `_print_Not`, line 356) | the modeled changed function: the new element-access rendering handler |
| `accessRender base indices` | the body `"{}[{}]".format(str(base), ", ".join([self._print(ind) for ind in index]))` (post-patch `pycode.py:360-363`) | pure spec: the assembled access string |
| `joinComma` | `", ".join([...])` over the rendered subscripts (`pycode.py:363` post-patch) | pure spec: comma-separated join of the rendered subscript fragments |

The components `renderAccess` consumes — `base` (the carrier's text) and each
element of `indices` (a subscript's rendered text) — correspond to
`str(expr.args[0])` and `self._print(ind)` for `ind in expr.args[1:]`. These are
the outputs of **unchanged** rendering helpers (`Symbol.__str__` /
`StrPrinter`-routed `Printer._print`); the patch does not touch them. They are
therefore part of the input carrier (R), not axiomatized callees — G-CONF feeds
the shadow the SAME real-helper outputs the oracle uses (see §3).

The pre-patch repo behaviour the change fixes (refinement audit only, not in the
consumer spec view): with no `_print_Indexed` handler, an `Indexed` expression
dispatches to `CodePrinter._print_not_supported` (`codeprinter.py:490`), which
adds the node to `self._not_supported` and returns `emptyPrinter(expr)`; at
`doprint` time (`codeprinter.py:103-107`) that set causes a `# Not supported in
<lang>:` / `# Indexed` comment block to be prepended to the emitted code. The
post-patch handler renders the access directly, with no such annotation.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| a rendered code fragment (`str`): `str(base)`, each `self._print(ind)`, and the returned access string | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `str` concat ↔ `List` `++`; empty `str` ↔ `[]`; the literal `"["`, `"]"`, `", "` ↔ their `.toList` |
| the ordered subscript fragments `[self._print(ind) for ind in expr.args[1:]]` | `indices : List (List Char)` | the i-th rendered subscript string ↔ the i-th element of `indices`; list length + order preserved |
| `"{}[{}]".format(a, b)` | `a ++ "[".toList ++ b ++ "]".toList` | Python `str.format` with the fixed template `"{}[{}]"` is exactly the two-bracket concatenation |
| `", ".join(frags)` | `joinComma frags` | string join with separator `", "` ↔ `joinComma` (no leading/trailing separator; `[]`↦`""`, `[x]`↦`x`) |

Lean `String`/`List Char` indexing is total and sound; the carrier is
`List Char` because the operation is character-level string assembly. The
modeled function is deterministic and total on its inputs; there is no exception
path (the patch never raises).

## 3. Callee provenance (kind-A) — none consumed

There are **no consumed axioms** (`axioms` region empty) and **no A-reference
deep models** of a changed callee. The only callees the patch invokes —
`str(base)` and `self._print(ind)` — are **unchanged** by the patch and their
outputs are treated as the input carrier (R), per §1/§2. The behaviour under
specification (assembling the bracketed, comma-separated access string and
emitting it as ordinary *supported* code) is modeled **deeply** by `joinComma` /
`accessRender`; nothing is borrowed from an opaque oracle. Hence
`axiom_check.py` is a stub with `status="skip"` (no axioms), and the impl region
is **all R/I** (not all-A), so G-CONF produces a real (non-skip) verdict.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16766`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `joinComma`/`accessRender` (R/I-tagged ops) to Python and feeds
them the real `str(base)` / `self._print(ind)` outputs (the unchanged-helper
components, mapping.md §1/§2); the oracle is the real patched `_print_Indexed`.
There are no A-tagged callees to leave as real-callee calls.
