# refinement.md — sphinx-doc__sphinx-7462

Operation-by-operation correspondence between `Solution.lean`'s impl regions (the
`renderSequenceTokens` and `renderSequenceText` `do` blocks + the pure `seqTokens`
/ `seqText` models) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement; state the bijection), **A-consumed** (proof uses an axiom's
`ensures`), **A-reference** (deep model validated == real callee by G-AX), or
**I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`, §4);
the narrative is audited by **G-EQ**. Claim: any impl verifying against this
frozen spec, refined per the maps below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE). It touches two files,
each adding an empty-sequence special case to that file's `ast.Tuple` rendering
branch.

## A. Site #1 — display tokens (`sphinx/domains/python.py`, `_parse_annotation.unparse`, line 116)

Gold hunk:
```
         elif isinstance(node, ast.Tuple):
-            result = []
-            for elem in node.elts:
-                result.extend(unparse(elem))
-                result.append(addnodes.desc_sig_punctuation('', ', '))
-            result.pop()
+            if node.elts:
+                result = []
+                for elem in node.elts:
+                    result.extend(unparse(elem))
+                    result.append(addnodes.desc_sig_punctuation('', ', '))
+                result.pop()
+            else:
+                result = [addnodes.desc_sig_punctuation('', '('),
+                          addnodes.desc_sig_punctuation('', ')')]
             return result
```

| # | Solution.lean impl op (`renderSequenceTokens`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `elts : List (List (List Char))` | the per-member node lists `unparse(elem)` for `elem in node.elts` | R | `list[list[Node]]` ↔ `List (List (List Char))`: a `Node` ↔ its `astext()` `List Char`, a member's `List[Node]` ↔ `List (List Char)`, the member list ↔ the outer `List` (mapping.md §2.1). The unchanged recursive `unparse(elem)` is the opaque input — no callee contract (mapping.md §3). |
| A2 | `match elts with \| [] => ["(".toList, ")".toList]` | `else: result = [desc_sig_punctuation('', '('), desc_sig_punctuation('', ')')]` (the `node.elts` falsy branch) | R + I | empty member list `[]` ↔ `not node.elts` (mapping.md §2.1: `len(node.elts) == 0` ↔ `elts = []`). The two tokens `"(".toList`, `")".toList` ↔ the two `desc_sig_punctuation` nodes `'('`, `')'` (mapping.md §2.1, §2.3). This is the **empty-tuple** behavior the change introduces — the discriminating clause. |
| A3 | `\| _ => List.intercalate [", ".toList] elts` | the `if node.elts:` loop: `extend(unparse(elem))` + `append(', ')` per member, then `result.pop()` | R + I | the non-empty loop builds `m₀ ++ SEP ++ m₁ ++ SEP ++ … ++ mₖ ++ SEP` and then drops the final `SEP` (`result.pop()`) — i.e. members interspersed with one `', '` separator between adjacent members, none at the ends. That is exactly `List.intercalate [", ".toList] elts` for a non-empty list (separator between adjacent elements; mapping.md §2.1). The separator `[", "].toList`-as-a-single-token ↔ `desc_sig_punctuation('', ', ')`. Carried over **unchanged** from the pre-patch code. |
| A4 | `return result` (`List (List Char)`) | `return result` (`List[Node]`) | R | the node list ↔ `List (List Char)`, cardinality-preserving (mapping.md §2.1). |

Discriminating content — an empty sequence renders as the **two punctuation
tokens `(` `)`**, not as the empty list — lives in
`seqTokens [] = ["(".toList, ")".toList]` (model) ⇔ the new `else` branch (real).
The pre-patch loop had no empty case: with `node.elts` empty it appended nothing
and then `result.pop()` raised `IndexError` (the reported bug); modeled as the
empty-list result (no tokens). `Solution_prepatch.lean` reproduces the
no-empty-case skeleton (`List.intercalate [", "] elts`, which is `[]` on the
empty input) and **fails** `out = seqTokens elts` exactly on the empty case
(G-DIFF).

## B. Site #2 — source text (`sphinx/pycode/ast.py`, `unparse`, line 116)

Gold hunk:
```
     elif isinstance(node, ast.Tuple):
-        return ", ".join(unparse(e) for e in node.elts)
+        if node.elts:
+            return ", ".join(unparse(e) for e in node.elts)
+        else:
+            return "()"
```

| # | Solution.lean impl op (`renderSequenceText`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `elts : List (List Char)` | the per-member strings `unparse(e)` for `e in node.elts` | R | `list[str]` ↔ `List (List Char)`, element-wise `str` ↔ `List Char` (mapping.md §2.2). Unchanged recursive `unparse(e)` is the opaque input — no callee contract (mapping.md §3). |
| B2 | `match elts with \| [] => "()".toList` | `else: return "()"` (the `node.elts` falsy branch) | R + I | empty member list `[]` ↔ `not node.elts`; `"()".toList` ↔ the literal `"()"` (mapping.md §2.2). This is the **empty-tuple** behavior the change introduces — the discriminating clause. |
| B3 | `\| _ => List.intercalate ", ".toList elts` | `if node.elts: return ", ".join(unparse(e) for e in node.elts)` | R + I | the non-empty case joins members with the two-character separator `", "`, none at the ends ↔ `List.intercalate ", ".toList elts` for a non-empty list (mapping.md §2.2: `str.join` ↔ `intercalate`, valid for ≥ 1 part). Carried over **unchanged** from the pre-patch code. |
| B4 | `return result` (`List Char`) | the returned `str` | R | rendered `str` ↔ `List Char` (mapping.md §2.2). |

Discriminating content — an empty sequence renders as the empty pair **`()`**,
not the empty string — lives in `seqText [] = "()".toList` (model) ⇔ the new
`else` branch (real). The pre-patch code had no empty case: `", ".join([])`
returned `""`. `Solution_prepatch_2.lean` reproduces that
(`List.intercalate ", " elts`, which is `[]` on the empty input) and **fails**
`out = seqText elts` exactly on the empty case (G-DIFF).

## C. No kind-A (axiom) and no kind-3 (inexpressible-changed-op) steps

Every step is R or I. The changed operation in each site — the
member-count-dependent assembly of already-rendered member images — is modeled
**deeply and concretely** (`seqTokens` / `seqText`, the spelled-out `match`);
nothing is hidden behind an axiom. There is no unchanged callee whose contract
the proof consumes: the only sub-computation, the recursive render of each child,
is treated as opaque input (mapping.md §3), so there is no A-consumed axiom and no
A-reference deep model. `axiom_check.py` (G-AX) is therefore a documented no-op
(exit 0).

Both sites fix the **same conceptual omission** (an empty comma-separated
sequence had no special case) in two different renderers with two different
output domains (display nodes vs source text), so each is an independently
observable fixed behavior with its own failing prepatch (`Solution_prepatch.lean`
for site #1, `Solution_prepatch_2.lean` for site #2). The non-empty branches of
both are behaviour-preserving (identical to pre-patch under refinement).

## D. verify(Solution) ⇒ resolved

`renderSequenceTokens` verifies only if its output equals `seqTokens elts` — the
two punctuation tokens `(` `)` when empty (A2), else members interspersed with a
single `', '` separator (A3). `renderSequenceText` verifies only if its output
equals `seqText elts` — `()` when empty (B2), else `", ".join` (B3). By R
(`list[…] ↔ List (List …)`, node ↔ `astext`, `str` concat/`join` ↔
`++`/`intercalate`) each verified renderer equals its patched branch on every
input; by G-CONF the R/I transliterations agree with `patch.diff`'s behaviour on
≥10⁵ inputs each (including the F2P empty-tuple cases `Tuple[()]` and `()`). There
are no axioms or deep-model references, so the only trust point of plan §1.1 in
play is refinement fidelity (this doc, G-EQ + G-CONF); axiom soundness (G-AX) is
vacuous. Therefore a model satisfying this spec, refined by the maps above, is
the gold patch up to type refinement — and the gold patch resolves (G-RESOLVE).
