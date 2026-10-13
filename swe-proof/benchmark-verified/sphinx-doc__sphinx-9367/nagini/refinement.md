# refinement.md — sphinx-doc__sphinx-9367

The operation-by-operation correspondence between `model.py`'s implementation
(the `render_tuple` impl region and the deep `render_seq` / `join_sep` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `Ensures`), **A-reference** (a deep model
validated == a real callee by G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The assembly site — `_UnparseVisitor.visit_Tuple` (`sphinx/pycode/ast.py:215`)

Gold hunk:
```
 def visit_Tuple(self, node: ast.Tuple) -> str:
-    if node.elts:
-        return "(" + ", ".join(self.visit(e) for e in node.elts) + ")"
-    else:
+    if len(node.elts) == 0:
         return "()"
+    elif len(node.elts) == 1:
+        return "(%s,)" % self.visit(node.elts[0])
+    else:
+        return "(" + ", ".join(self.visit(e) for e in node.elts) + ")"
```

| # | model.py impl op (`render_tuple`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `elts: List[PSeq[int]]` (the member renderings) | `node.elts`, each rendered by `self.visit(e)` | R | element AST nodes ↔ their `str` renderings ↔ `PSeq[int]` code-point sequences (mapping.md §1, §2); the rendering callee `self.visit` is unchanged ⇒ taken as the input carrier (§B). |
| A2 | `n = len(elts)` | `len(node.elts)` | I/R | sequence length; same operation, refined carrier (`List[PSeq[int]]` vs `List[AST]`). |
| A3 | `if n == 0: return PSeq(40, 41)` | `if len(node.elts) == 0: return "()"` | R | `"()"` ↔ `PSeq(40, 41)` (mapping.md §2). |
| A4 | `elif n == 1: return PSeq(40) + es[0] + PSeq(44, 41)` | `elif len(node.elts) == 1: return "(%s,)" % self.visit(node.elts[0])` | R | `"(%s,)" % e0` ↔ `(` + `e0` + `,)` = `PSeq(40) + es[0] + PSeq(44, 41)`; `"("`=`PSeq(40)`, `",)"`=`PSeq(44, 41)` (mapping.md §2). **This is the single behavioural change**: the trailing comma after the lone member. |
| A5 | `else:` branch: backward loop building `joined == join_sep(es)`, then `return PSeq(40) + joined + PSeq(41)` | `else: return "(" + ", ".join(self.visit(e) for e in node.elts) + ")"` | R | `", ".join(renderings)` ↔ `join_sep(ToSeq(elts))` (the separator-joined concatenation, `, ` between adjacent members, modeled deeply in the `pure` region); `"("`+join+`")"` ↔ `PSeq(40) + joined + PSeq(41)` (mapping.md §2). The loop is a faithful materialization of the join: invariant `joined == join_sep(es.drop(i))`. |

The discriminating content of the change — a one-member sequence renders as
`(e0,)` (with the trailing comma) rather than `(e0)` — lives in clause A4 of
the impl and in the `render_seq` `len(s) == 1` branch of the spec
(`PSeq(40) + s[0] + PSeq(44, 41)`). The pre-patch code rendered every non-empty
sequence with the join branch, so a one-member sequence collapsed to `(e0)`
with no comma; `model_prepatch.py` reproduces that (the single `else` join
branch covers `n == 1`) and **fails** the postcondition
`Result() == render_seq(ToSeq(elts))` exactly on the one-member case — the spec
sensing the change (G-DIFF).

## B. The element-rendering callee — `self.visit(e)` (unchanged)

`visit_Tuple` calls `self.visit(e)` to render each member. The gold patch does
NOT touch `self.visit` (nor any per-node `visit_*`); only the surrounding
assembly changes. The member renderings are therefore taken as the **input
carrier** `elts: List[PSeq[int]]` — NOT modeled deeply and NOT axiomatized.
There is consequently **no A-consumed axiom** and **no A-reference deep model
of a real callee** in this bundle (the `axioms` region is empty, and
`axiom_check.py` is absent — see mapping.md §3). The pure functions `join_sep`
and `render_seq` are closed-form spec definitions of the assembly under change,
not contracts about an external callee.

## B2. Termination obligation (total correctness)

Nagini is a partial-correctness verifier by default: an implementation with no
reachable normal exit (an endless loop before the `return`) satisfies every
`Ensures` — including the exact output pin — vacuously while sharing the spec
byte-for-byte. That is a wrong implementation the spec would otherwise admit
(the audit's P1 witness). The real `visit_Tuple` always answers: assembling a
finite tuple literal from finitely many member renderings is a bounded
computation (`", ".join` over a finite list plus concatenations). The spec
therefore carries `Requires(MustTerminate(2))` on `render_tuple` (consumed in
the multi-branch loop by `Invariant(MustTerminate(i))`, with `i` the strictly
decreasing, bounded-below measure). With termination required and the full
functional postcondition `Result() == render_seq(ToSeq(elts))`, any verifying
same-spec implementation must terminate and return exactly the pinned text —
the spec is functionally complete on its domain (properties.py `w-diverge`
pins the rejection).

## C. No kind-3 (unexpressible-changed-op) steps

Every step in §A is R or I. The one operation that genuinely changed — the
parenthesize/join assembly with its new single-member trailing-comma form — is
modeled **deeply** (`render_seq` / `join_sep` in the `pure` region, consumed by
`render_tuple`'s postcondition), not hidden behind any axiom. No step is a
changed-but-inexpressible operation.

## D. verify(model) ⇒ resolved

`render_tuple` verifies only if it TERMINATES on every input (§B2,
`Requires(MustTerminate(2))`) and its output equals `render_seq(ToSeq(elts))`
exactly (A3–A5), which pins the empty form `()`, the single-member form
`(e0,)`, and the multi-member separator-joined form. By R (str ↔ PSeq[int],
the literal-string ↔ code-point bijection, `", ".join` ↔ `join_sep`) the
verified assembly equals `visit_Tuple`'s post-patch return on every input, with
the member renderings (from the unchanged `self.visit`, §B) passed through
identically. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE: F2P `test_unparse[(1,)-(1,)]` passes, and the empty/multi
P2P cases `()`/`(1, 2, 3)`/`(1, 2)` continue to pass). The sole trust point is
refinement fidelity (this document, G-EQ); there are no axioms to audit.
