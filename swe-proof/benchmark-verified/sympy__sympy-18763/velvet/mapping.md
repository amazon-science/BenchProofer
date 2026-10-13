# mapping.md — sympy__sympy-18763

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 70381f282f2d9d039da860e391fe51649df2779d`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
provenance of the abstracted-as-input rendered fragments.

Repo file under change: `sympy/printing/latex.py`.
`spec_provenance: cold` — derived from `problem_statement` + gold `patch` + the
real source at `base_commit` only.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `renderSubsNotation (body subsList : List Char)` | `LatexPrinter._print_Subs(self, subs)` — `sympy/printing/latex.py:699` (the `return` assembly at line 706) | the modeled changed function: assembles the LaTeX string for an evaluated-at-a-point (substitution) expression |
| `subsNotationLatex (body subsList : List Char)` | the post-patch `return` template at `sympy/printing/latex.py:706` | pure spec: the exact character sequence the assembled LaTeX must be (deep model of the changed string op) |
| `body` (input `List Char`) | `latex_expr = self._print(expr)` — `latex.py:701` | the rendered LaTeX of the inner expression; an UNCHANGED upstream computation, abstracted as a free input |
| `subsList` (input `List Char`) | `latex_subs = r'\\ '.join(...)` — `latex.py:704-705` | the rendered LaTeX of the `var=point` assignment list; an UNCHANGED upstream computation, abstracted as a free input |

The gold patch (`latex.py:706`) changes ONLY the return template — it wraps the
rendered body in `\left( ... \right)`. The preamble lines 700-705 (`subs.args`
unpacking, the `self._print` calls, the `\\ `.join) are unchanged context; their
results enter the model as the free inputs `body` and `subsList`. They assert no
contract on those callees, so they are neither A-consumed nor A-reference — they
are inputs (there is nothing for G-AX to validate; no `axiom_check.py`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a LaTeX string (`latex_expr`, `latex_subs`, and `_print_Subs`'s return) | `List Char` | `s` (Python `str`) ↔ `s.toList`-shaped `List Char`; `str` concatenation (`%`-format / `+`) ↔ `List` `++`; the literal template pieces ↔ the corresponding `String.toList` literals; empty `str` ↔ `[]` |
| a single character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; total/exact on the printable LaTeX alphabet involved |

`body` and `subsList` are read-only inputs — NOT declared `mut`; the routine
computes one fresh `List Char` and mutates nothing (directive 5: no `mut`
params, so no frame obligation arises).

## 3. Callee provenance

There are **no axioms and no deep-model references** in this bundle. The single
changed operation — the `return`-template string assembly — is modeled
**deeply and concretely**: `subsNotationLatex` (pure region) spells out the exact
character sequence, and the `do` block reproduces it by literal `++`
concatenation (an **I** op). The unchanged upstream renderers (`self._print`,
the `\\ `.join) are not modeled; their outputs are the free inputs `body` /
`subsList` (§1). Hence `meta.json` has empty `axioms` / `deep_model_references`,
no `axiom_check.py`, and **G-AX skips** (gates.py `gate_ax`).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`18763`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`subsNotationLatex` (the I-tagged concatenation) to Python and recomputes the
unchanged preamble fragments (`body`, `subsList`) with the **real** repo
`LatexPrinter` (the abstracted-as-input legs run the real callee), then diffs the
assembled string against the real patched `_print_Subs` over ≥10⁵ fuzzed `Subs`
objects. Exit 0 iff zero disagreements.
