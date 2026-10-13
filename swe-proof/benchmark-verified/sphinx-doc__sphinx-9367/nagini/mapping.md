# mapping.md — sphinx-doc__sphinx-9367

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 6918e69600810a4664e53653d6ff0290c3c4a788`, states the type
abstraction, and records callee provenance.

Repo file under change: `sphinx/pycode/ast.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `render_tuple(elts)` | `_UnparseVisitor.visit_Tuple(self, node)` — `sphinx/pycode/ast.py:215` | the modeled changed function (tuple AST node → source-like text) |
| input `elts: List[PSeq[int]]` | `node.elts` (the tuple's element AST nodes) **after** each is rendered by `self.visit(e)` | the carrier: the already-rendered text of each member |
| `render_seq(s)` / `join_sep(s)` / `sep()` / `empty_seq()` | the assembly expression of `visit_Tuple` (the parentheses, the `", ".join(...)`, and the post-patch single-element trailing comma) | pure spec: the deep model of the assembly under change |

The element rendering `self.visit(e)` (`ast.py:81`, `_UnparseVisitor.visit`,
the inherited `ast.NodeVisitor.visit` dispatch) is **unchanged** by the patch
and is therefore taken as the input carrier, NOT modeled or axiomatized: each
element's rendering is a given code-point sequence `elts[k]`. The gold hunk
touches only the surrounding assembly, so this abstraction is faithful (see
refinement.md §B).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (each `self.visit(e)` result, and the `visit_Tuple` return) | `PSeq[int]` of Unicode code points | `s[k]` ↔ code point; `str` concatenation ↔ `PSeq` `+`; an empty `str` ↔ `empty_seq()` |
| `node.elts` (a `List` of element AST nodes) | `List[PSeq[int]]` — the parallel list of their renderings | `len(node.elts)` ↔ `len(elts)`; `node.elts[k]` rendered ↔ `elts[k]` |
| `", ".join(self.visit(e) for e in node.elts)` | `join_sep(ToSeq(elts))` | the separator-joined concatenation of the member renderings, `, ` (U+002C U+0020) between adjacent members |
| string literals `"("`, `")"`, `","`, `", "`, `"()"` | `PSeq(40)`, `PSeq(41)`, `PSeq(44)`, `PSeq(44, 32)`, `PSeq(40, 41)` | code points: `(`=40, `)`=41, `,`=44, ` `=32 |
| `"(%s,)" % self.visit(node.elts[0])` (post-patch single-element form) | `PSeq(40) + elts[0] + PSeq(44, 41)` | `(` + member + `,)` |

`str` indexing/iteration is banned in Nagini, so the carrier is `PSeq[int]`
throughout; the member-rendering list is `List[PSeq[int]]`, viewed in the spec
as `PSeq[PSeq[int]]` via `ToSeq`.

**Termination (total correctness):** the real assembly always answers —
parenthesizing and `", ".join`-ing finitely many member renderings is a
bounded computation. The spec carries `Requires(MustTerminate(2))` on
`render_tuple` (consumed in the multi-branch loop by
`Invariant(MustTerminate(i))`). Nagini is a partial-correctness verifier by
default, so without the obligation a diverging implementation would satisfy
every `Ensures` vacuously while sharing the spec.

## 3. Callee provenance

There are **no axioms** in this bundle (the `axioms` region is empty) and **no
A-reference deep-model-vs-real-callee checks**, hence **no `axiom_check.py`**.
Reason: the single operation the patch changes — the tuple **assembly** — is
modeled **deeply** by the pure functions `join_sep` / `render_seq` (concrete
spec definitions, not contracts about an external callee). The only callee
`visit_Tuple` invokes, `self.visit(e)`, is **unchanged** by the patch and is
abstracted as the **input** `elts[k]` (each member's already-computed
rendering), so there is nothing to validate against a real callee. The
abstraction is sound because the gold hunk is confined to the parenthesize/join
assembly and never touches `self.visit`.

`render_seq` is a complete closed-form definition over `PSeq[PSeq[int]]`; it is
not a stand-in for any library function. Its correctness as the desired
behaviour is witnessed directly by the F2P/P2P tests via `patch.diff`
(G-RESOLVE), not by an out-of-band executable check.

## G-CONF (differential conformance)

`conformance_check.py` refutes the R/I refinement leg by executing both sides:

* **Shadow** — the `# impl-start` / `# impl-end` region of `model.py` copied
  **verbatim** (`shadow_render_tuple`), with only the contract calls
  (`Requires`/`Ensures`/`Invariant`/`Assert`) and the `# invariants-start`/`-end`
  markers deleted; the `@Pure` helpers it calls (`empty_seq`, `sep`) copied
  minus contracts. `join_sep` / `render_seq` are deliberately **not** copied:
  they occur only in the postcondition, so importing them would compare the spec
  with itself instead of the impl with the repo. `PSeq` is realized as an
  immutable tuple shim exposing exactly `PSeq(*items)` / `take` / `drop` / `+` /
  `len` / `[]` / `==`, and `ToSeq(list)` materializes one. No `@ContractOnly`
  callee and no axiom exists in this bundle (§3), so nothing is assumed.
* **Oracle** — the REAL patched `_UnparseVisitor.visit_Tuple`
  (`sphinx/pycode/ast.py:215`, §1), **called** (not transliterated) on a live
  `_UnparseVisitor("")`; the gate applies `patch.diff` to /testbed first. The
  member renderings fed to the shadow come from the same unchanged
  `visitor.visit(e)` the oracle's own assembly consumes (§1, refinement.md §B).
* **Type bridge** (§2, inverted) — member renderings are generated as concrete
  `str`; shadow side `str → PSeq[int]` via `ord` per character (list →
  `List[PSeq[int]]`), result `PSeq[int] → str` via `chr`. Oracle side, two
  independent realizations: (a) **synthetic** `ast.Name(id=s)` members, since
  the unchanged `visit_Name` returns `node.id` verbatim — this reaches the
  *full* abstract domain, including member renderings that are empty or contain
  `,`, `, `, `(`, `)`, or non-ASCII code points, which no parseable tuple source
  can produce; (b) **parsed** real Python source through the genuine recursive
  renderer (nested tuples recurse into the patched `visit_Tuple`).
* **Input domain** — `Requires` is only `Acc(list_pred(elts), 1/2)` plus
  `MustTerminate(2)`, so every finite list of finite code-point sequences is
  admissible and nothing is excluded. All three impl branches are taken
  (`n == 0`, `n == 1` — the F2P `(1,)` shape, and the `else` loop with both its
  `i == n` and its `i < n` iterations).
* **Inputs / seed** — 100000 inputs total: **7381 exhaustive** (every member-
  rendering list of length 0..4 over the 9-symbol adversarial alphabet
  `'' | 'x' | '1' | 'a, b' | ',' | '(' | ')' | '(1,)' | 'é'` — a complete
  decision over that alphabet, stronger than sampling it), 14 boundary/F2P
  parsed sources, then seeded fuzz over both arms. **Pinned seed: `SEED = 9367`.**
* **Verdict** — exit 0 iff zero disagreements; recorded `G-CONF=pass`, 0
  disagreements. Negative control: pointing the same script at the *pre-patch*
  `visit_Tuple` refutes immediately on the single-member case
  (`shadow='(,)'` vs `oracle='()'`), so the check is capable of failing on
  exactly the behaviour under specification.
