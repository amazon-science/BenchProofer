# refinement.md — sphinx-doc__sphinx-7462

Maps every operation in each `implementation_*` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses callee axiom ·
**A-reference** deep-model validated == real callee (G-AX) · **I** identical op.

There are NO A-tagged rows: the only collaborator (the recursive per-element
renderer `unparse(elem)`) is UNCHANGED and is represented by leaving the
already-rendered elements as arbitrary inputs (`elems`), universally quantified
in both `correct_*`. The changed assembly op is modeled DEEPLY (R/I). So G-AX is
a skip stub and the R/I legs are validated by G-CONF.

## Function 1 — `unparse` ast.Tuple branch, display-token view
`sphinx/domains/python.py` · Lean `implementation_renderTupleSig`

| Lean op | patch.diff op | tag |
|---|---|---|
| `elems : List (List SigToken)` (already-rendered elements) | `node.elts` after each `unparse(elem)` (UNCHANGED recursion) | R (a `List[Node]` per element ↔ `List SigToken`; the recursion is left ∀-quantified) |
| `if elems.isEmpty then return [punct "(", punct ")"]` | `else: result = [desc_sig_punctuation('', '('), desc_sig_punctuation('', ')')]` (the NEW empty branch; in Python it is the `if node.elts: … else: …` guard) | R (`node.elts` truthiness ↔ `List.isEmpty`; `desc_sig_punctuation('', s)` ↔ `SigToken.punct s`) |
| `let mut result := []` | `result = []` | I |
| `for elem in elems do result := result ++ elem; result := result ++ [punct ", "]` | `for elem in node.elts: result.extend(unparse(elem)); result.append(desc_sig_punctuation('', ', '))` | R (`extend` ↔ `++ elem`; `append sep` ↔ `++ [punct ", "]`) |
| `return result.dropLast` | `result.pop(); return result` | R (`list.pop()` removing the last element ↔ `List.dropLast`; only reached on the non-empty branch in both) |

## Function 2 — `unparse` ast.Tuple branch, source-text view
`sphinx/pycode/ast.py` · Lean `implementation_renderTupleText`

| Lean op | patch.diff op | tag |
|---|---|---|
| `elems : List String` (already-rendered element texts) | `unparse(e) for e in node.elts` (UNCHANGED recursion) | R (per-element `str` ↔ `String`; recursion ∀-quantified) |
| `if elems.isEmpty then return "()"` | `else: return "()"` (the NEW empty branch) | R (`node.elts` truthiness ↔ `List.isEmpty`) |
| `return String.intercalate ", " elems` | `return ", ".join(unparse(e) for e in node.elts)` (the `if node.elts:` branch) | R (`", ".join` ↔ `String.intercalate ", "`) |

## Soundness note
The discriminating clause in BOTH functions is the empty-sequence case:
pre-patch, function 1 crashes (`result.pop()` on `[]`) and function 2 yields `""`
instead of `"()"`. The spec pins `assembleTupleSig [] = [punct "(", punct ")"]`
and `assembleTupleText [] = "()"`, so the prepatch impls (which omit the empty
branch) cannot satisfy the carried gold proof — exactly the F2P behavior
(`Tuple[()]` → `( )` / `()`).
