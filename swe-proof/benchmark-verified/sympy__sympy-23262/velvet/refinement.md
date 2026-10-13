# refinement.md — sympy__sympy-23262

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`renderSequence` `do` block plus the deep `renderSeq`/`joinComma` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (deep model
validated == an UNCHANGED real callee by G-AX), or **I** (identical concrete
op). **This bundle has NO A-consumed and NO A-reference steps:** every step is
R or I. The one operation the patch actually *changes* — the delimiter pair and
the join-and-wrap — is the function under spec itself, modeled deeply and
concretely (`renderSeq`/`joinComma`); per SPEC_GUIDE §0.7 the changed function
must NOT be axiomatized or A-referenced, so it carries no G-AX obligation and
the bundle ships no `axiom_check.py` (G-AX = skip).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1, run against the gold-patched tree); this narrative is audited by **G-EQ**.
Claim: any impl verifying against this frozen spec, refined per the map below,
is behaviorally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (byte-identical; G-RESOLVE).

## A. The render site — the iterable branch of the changed function

Gold hunk (`sympy/utilities/lambdify.py:957-964`):

```
     elif iterable(arg):
         if isinstance(arg, list):
-            left, right = "[]"
+            left, right = "[", "]"
         elif isinstance(arg, tuple):
-            left, right = "()"
+            left, right = "(", ",)"
         else:
             raise NotImplementedError("unhandled type: %s, %s" % (type(arg), arg))
         return left +', '.join(_recursive_to_string(doprint, e) for e in arg) + right
```

| # | Solution.lean impl op (`renderSequence`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `elems : List (List Char)` | `[ _recursive_to_string(doprint, e) for e in arg ]` — the ordered element texts | R | each rendered element text ↔ a `List Char`, positionally (mapping.md §2). The element-rendering recursion is UNCHANGED by the patch; in G-CONF the same `doprint`/recursion runs on both sides (R identity bridge), so it carries no obligation. |
| A2 | parameter `isList : Bool` | `isinstance(arg, list)` vs `isinstance(arg, tuple)` | R | `True` ↔ `isList = true` (bracket kind), `False` ↔ `isList = false` (paren kind), mapping.md §2. The unreachable `else: raise` arm is out of the modeled domain (only `list`/`tuple` reach here). |
| A3 | delimiter selection `openD := if isList then "[" else "("`; `closeD := if isList then "]" else ",)"` | `left, right = "[", "]"` / `left, right = "(", ",)"` | I | the literal delimiter pair per kind. The tuple closer is `,)` — a comma BEFORE the closing parenthesis. This is exactly the changed assignment (the pre-patch `left, right = "()"` split the 2-char string into `(` and `)`, dropping the comma). |
| A4 | body `joinComma elems` | `', '.join(... for e in arg)` | I | comma-space separator strictly between adjacent element texts; mapping.md §2. `joinComma` front-recursion = `', '.join`. |
| A5 | result `openD ++ joinComma elems ++ closeD` | `left + body + right` | I | the changed render step is modeled **deeply and concretely**: `renderSeq`/`joinComma` (pure region) and the straight-line `do` block ARE the join-and-wrap. The concat ops (`++`) are **I** (concrete, transliterated by G-CONF). Because this is the function the patch changes, it is NOT axiomatized or A-referenced (§0.7); its equality to the gold-patched `_recursive_to_string` iterable branch is validated by **G-CONF** over ≥10⁵ inputs on the patched tree, not by G-AX. mapping.md §3.1. |

Discriminating content of the change — a parenthesized sequence closes with `,)`
not `)`, so a one-element tuple renders `'(t0,)'` (a tuple) not `'(t0)'` (a bare
value) — lives in `renderSeq false elems = "(".toList ++ joinComma elems ++
",)".toList` (model) ⇔ `left, right = "(", ",)"` (real). The pre-patch
`left, right = "()"` made the closer the bare `)`; `Solution_prepatch.lean`
reproduces that (`closeD := if isList then "]".toList else ")".toList`) and
**fails** `out = renderSeq isList elems` on the clause `closeD = ",)" .toList`
for the `isList = false` branch (G-DIFF). The list branch is behaviourally
unchanged (`"[]"` and `"[", "]"` both yield `[`/`]`), so the prepatch's list
case is left agreeing with the spec — the failure is localized to the tuple
closer, the actual fix.

## B. One prepatch suffices (G-DIFF)

There is a single independently-observable fixed behaviour: the tuple closing
delimiter. The list-delimiter edit in the same hunk (`"[]"` → `"[", "]"`) is a
pure refactor with NO behavioural effect — both forms unpack to `left='['`,
`right=']'` — so it produces no separate testable behaviour and needs no separate
prepatch. The F2P assertion (`lambdify([], (1,))() == (1,)`) bottoms out entirely
in the tuple-closer change. Hence one `Solution_prepatch.lean`, failing on the
tuple branch, covers the fix.

## C. No kind-3 (inexpressible-changed-op) steps; no axioms

Every step is R or I. The one operation that genuinely *changed* — the delimiter
pair (specifically the tuple closer) and the join-and-wrap — is modeled
**deeply and concretely** (the spelled-out `renderSeq`/`joinComma`, steps A3–A5),
not hidden behind an axiom about the function under change. Per SPEC_GUIDE §0.7
the changed function must NOT be axiomatized or A-referenced: an A-reference is a
deep model of an *unchanged* callee validated == the real callee by G-AX, but the
real callee here at `base_commit` is the *pre-patch* code (which renders a
one-element tuple as `'(1)'`), so any A-reference asserting `renderSeq == real`
would be structurally impossible (G-AX runs on the unpatched tree). There are
therefore **no A-consumed and no A-reference** steps and the bundle ships **no
`axiom_check.py`** (G-AX = skip). The per-element texts and the join are composed
for real on both sides of G-CONF, and nothing about how an element renders is
assumed by the proof; the proof consumes only the structural unfold of
`renderSeq`/`joinComma`.

## D. verify(Solution) ⇒ resolved

`renderSequence` verifies only if its output equals the exact join-and-wrap
`renderSeq isList elems` — comma-space join (A4), bracket pair for a list, and
crucially the `,)` closer for a tuple (A3, A5). By R (rendered text ↔ `List Char`,
kind ↔ `isList`, element-list ↔ `elems`) the verified result equals the real
`left + ', '.join(...) + right` on the tested inputs; by G-CONF the R/I
transliteration of the join-and-wrap agrees with `patch.diff`'s behaviour
(sharing the unchanged leaf renderer) on ≥10⁵ nested inputs run against the
gold-patched tree. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The single trust point is refinement fidelity (this doc + G-CONF);
there is no consumed-axiom and no A-reference trust point (G-AX = skip, no
unchanged callee to check).
