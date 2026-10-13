# refinement.md — sphinx-doc__sphinx-9367

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`renderSequence` `do` block + the pure `renderTuple` model) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement; state the bijection),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (deep model
validated == real callee by G-AX), or **I** (identical concrete op). EVERY step
is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`, §4);
the narrative is audited by **G-EQ**. Claim: any impl verifying against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The render site — `_UnparseVisitor.visit_Tuple` (`sphinx/pycode/ast.py:215`)

Gold hunk:
```
-        if node.elts:
-            return "(" + ", ".join(self.visit(e) for e in node.elts) + ")"
-        else:
+        if len(node.elts) == 0:
             return "()"
+        elif len(node.elts) == 1:
+            return "(%s,)" % self.visit(node.elts[0])
+        else:
+            return "(" + ", ".join(self.visit(e) for e in node.elts) + ")"
```

| # | Solution.lean impl op (`renderSequence`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `elts : List (List Char)` | `[self.visit(e) for e in node.elts]` (the rendered text of each `node.elts` member) | R | `list[str]` ↔ `List (List Char)`, element-wise `str` ↔ `List Char` (mapping.md §2). The unchanged recursive `self.visit` is abstracted as the opaque input — no callee contract (mapping.md §3). G-CONF bridges by rendering the patched `visit_Tuple` over members whose images we control. |
| A2 | `match elts with \| [] => …` ⇔ `len(node.elts) == 0` | `if len(node.elts) == 0: return "()"` | R + I | empty-list case `[]` ↔ `len == 0` (mapping.md §2: `len(elts)` ↔ `elts.length`). Result `"()".toList` ↔ the literal `"()"` (I). |
| A3 | `\| [e] => "(".toList ++ e ++ ",)".toList` ⇔ `len == 1` | `elif len(node.elts) == 1: return "(%s,)" % self.visit(node.elts[0])` | R + I | one-member case `[e]` ↔ `len == 1`; `"(" ++ e ++ ",)"` ↔ `"(%s,)" % m` where `m` is the single member's rendered text (mapping.md §2: `++` ↔ `str` concat/`%`). This is the **trailing-comma** behavior the change introduces — the discriminating clause. |
| A4 | `\| _ => "(".toList ++ List.intercalate ", ".toList elts ++ ")".toList` ⇔ `len ≥ 2` | `else: return "(" + ", ".join(self.visit(e) for e in node.elts) + ")"` | R + I | many-member case (`a :: b :: rest`, i.e. `len ≥ 2`) ↔ the `else`; `"(" ++ intercalate ", " elts ++ ")"` ↔ `"(" + ", ".join(parts) + ")"` (mapping.md §2: `intercalate SEP` ↔ `SEP.join`, valid for ≥ 1 part — here ≥ 2). Carried over **unchanged** from the pre-patch code. |
| A5 | `return result` (`List Char`) | the returned `str` | R | the rendered `str` ↔ `List Char` (mapping.md §2). |

Discriminating content of the change — a one-member sequence renders **`(m,)`**,
not `(m)` — lives in `renderTuple [e] = "(".toList ++ e ++ ",)".toList` (model)
⇔ the new `elif len(node.elts) == 1: return "(%s,)" % …` branch (real). The
pre-patch code had no one-member case (the non-empty branch always joined inside
bare parens, yielding `(m)`); `Solution_prepatch.lean` reproduces that and
**fails** `out = renderTuple elts` exactly on the one-member case (G-DIFF).

## B. No second site

`visit_Tuple` is the only function the patch changes, and it has one
independently-observable fixed behavior (the one-member rendering). The 0-member
and ≥2-member branches are behaviour-preserving (identical to pre-patch under
refinement), so there is a single prepatch.

## C. No kind-A (axiom) and no kind-3 (inexpressible-changed-op) steps

Every step is R or I. The changed operation — the member-count-dependent
wrapping/joining of already-rendered text — is modeled **deeply and concretely**
(`renderTuple`, the spelled-out `match`); nothing is hidden behind an axiom.
There is no unchanged callee whose contract the proof consumes: the only
sub-computation, `self.visit(e)`, is treated as opaque input (mapping.md §3), so
there is no A-consumed axiom and no A-reference deep model. `axiom_check.py`
(G-AX) is therefore a documented no-op (exit 0).

## D. verify(Solution) ⇒ resolved

`renderSequence` verifies only if its output equals `renderTuple elts` — i.e.
`()` for an empty sequence, `(m,)` for one member (A3, the trailing comma), and
`(m₁, m₂, …)` for two or more (A4). By R (`list[str] ↔ List (List Char)`, `str`
concat/`%`/`join` ↔ `++`/`intercalate`) the verified renderer equals the patched
`visit_Tuple` on every input; by G-CONF the R/I transliteration of the impl
agrees with `patch.diff`'s behaviour on ≥10⁵ inputs (including the F2P cases
`()`, `(1,)`, `(1, 2, 3)`). There are no axioms or deep-model references, so the
only trust point of plan §1.1 in play is refinement fidelity (this doc, G-EQ +
G-CONF); axiom soundness (G-AX) is vacuous. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement — and
the gold patch resolves (G-RESOLVE).
