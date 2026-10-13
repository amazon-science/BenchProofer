# refinement.md — sphinx-doc__sphinx-7462

The operation-by-operation correspondence between `model.py`'s implementation
(the `tuple_tokens` and `tuple_text` impl regions and the deep `join_tokens` /
`join_comma` models) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — split into **A-consumed**,
where the proof uses an axiom's `Ensures`, and **A-reference**, where a deep
model is validated == the real callee by axiom_check.py / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE). There are **no consumed `@ContractOnly`
axioms**: every step is R, A-reference, or I.

## A. Site A — token surface (`sphinx/domains/python.py`, `unparse` Tuple branch)

Gold hunk:
```
- result = []
- for elem in node.elts:
-     result.extend(unparse(elem))
-     result.append(addnodes.desc_sig_punctuation('', ', '))
- result.pop()
+ if node.elts:
+     result = []
+     for elem in node.elts:
+         result.extend(unparse(elem))
+         result.append(addnodes.desc_sig_punctuation('', ', '))
+     result.pop()
+ else:
+     result = [addnodes.desc_sig_punctuation('', '('),
+               addnodes.desc_sig_punctuation('', ')')]
  return result
```

| # | model.py impl op (`tuple_tokens`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `elts: PSeq[PSeq[int]]` | `node.elts` (the parsed member nodes, each already rendered by `unparse(elem)`) | R | member list ↔ `PSeq[PSeq[int]]`; each member's token text ↔ `PSeq[int]` (mapping.md §2). |
| A2 | guard `if len(elts) > 0:` | `if node.elts:` | I | non-emptiness test; `len(elts) > 0` ↔ truthiness of the member list. |
| A3 | `result = join_tokens(elts)` (the members with a single ', ' separator token between them, no trailing separator) | the loop `for elem in node.elts: result.extend(unparse(elem)); result.append(desc_sig_punctuation('', ', ')); result.pop()` | A-reference | the unchanged non-empty assembly is modeled **deeply** by `join_tokens` (front-recursive fold, separator `sep_token()` == `PSeq(44, 32)`). No consumed axiom — the proof never depends on one. G-AX validates `join_tokens == the real loop` on boundary + fuzz (mapping.md §3.1). |
| A4 | `else: result = PSeq(open_paren(), close_paren())` (two tokens `'('`, `')'`) | `else: result = [desc_sig_punctuation('', '('), desc_sig_punctuation('', ')')]` | I (under R) | the empty-group rendering; `open_paren()`/`close_paren()` == the token texts `'('`/`')'` (mapping.md §2). This is the discriminating fix at site A. |
| A5 | `return result` | `return result` | I | |

The discriminating content of the change at site A — an empty group renders as
`['(', ')']` rather than executing `result.pop()` on an empty list (the
`IndexError` crash) — lives in clause `Ensures(Implies(len(elts) == 0, Result()
== PSeq(open_paren(), close_paren())))`. `model_prepatch.py` reproduces the
pre-patch unconditional assembly (`return join_tokens(elts)`, whose empty image
is the empty token sequence, the abstract form of the crashing `pop()`), and
**fails** exactly this clause (G-DIFF).

## B. Site B — text surface (`sphinx/pycode/ast.py`, `unparse` Tuple branch)

Gold hunk:
```
- return ", ".join(unparse(e) for e in node.elts)
+ if node.elts:
+     return ", ".join(unparse(e) for e in node.elts)
+ else:
+     return "()"
```

| # | model.py impl op (`tuple_text`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `elts: PSeq[PSeq[int]]` | `node.elts` (each member already rendered by `unparse(e)` into a `str`) | R | member list ↔ `PSeq[PSeq[int]]`; member text ↔ `PSeq[int]` (mapping.md §2). |
| B2 | guard `if len(elts) > 0:` | `if node.elts:` | I | non-emptiness test. |
| B3 | `result = join_comma(elts)` | `", ".join(unparse(e) for e in node.elts)` | A-reference | the unchanged non-empty join is modeled **deeply** by `join_comma` (front-recursive fold, separator `sep_token()` == `PSeq(44, 32)`). G-AX validates `join_comma == ', '.join` on boundary + fuzz (mapping.md §3.2). |
| B4 | `else: result = PSeq(40, 41)` (the two characters `'('`, `')'`) | `else: return "()"` | I (under R) | the empty-group rendering; `PSeq(40, 41)` == the code points of `"()"` (mapping.md §2). This is the discriminating fix at site B. |
| B5 | `return result` | `return ...` | I | |

The discriminating content at site B — an empty group renders as `"()"` rather
than the empty join `""` — lives in clause `Ensures(Implies(len(elts) == 0,
Result() == PSeq(40, 41)))`. `model_prepatch_2.py` reproduces the pre-patch
unconditional `return join_comma(elts)` (empty image `""`) and **fails** exactly
this clause (G-DIFF).

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The two operations that genuinely
*changed* — the empty-group renderings at each site — are spelled out
**concretely** (`PSeq(open_paren(), close_paren())` / `PSeq(40, 41)`), not
hidden behind an axiom. The unchanged member-assembly operations are modeled
**deeply** (`join_tokens`, `join_comma`, the front-recursive folds in the `pure`
region) and validated against their real callees by G-AX (A-reference), never
consumed as axioms. There is **no consumed `@ContractOnly` axiom** in this
bundle. Each member's own rendering (`unparse(elem)` / `unparse(e)`) is an
unchanged upstream computation taken as an already-rendered input, so it is not
modeled or axiomatized.

## D. verify(model) ⇒ resolved

`tuple_tokens` verifies only if its output is the two-token `'(' ')'` rendering
on the empty group (A4) and the separator-token interleaving on a non-empty
group (A3); `tuple_text` verifies only if its output is `"()"` on the empty
group (B4) and the comma-and-space join otherwise (B3). By R (member list ↔
`PSeq[PSeq[int]]`, token/char text ↔ `PSeq[int]`) the verified renderings equal
the gold branches; by G-AX the deep models `join_tokens` / `join_comma` equal
the real loop / `', '.join` on the unchanged non-empty case (A-reference), and
the real callees crash / return `""` on the empty group, exactly the defect the
gold guards. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and audited deep models — and the gold
patch resolves (G-RESOLVE). The one trust point is refinement fidelity (this
document, G-EQ) plus deep-model soundness (axiom_check.py, G-AX); there are no
consumed-axiom trust points.
