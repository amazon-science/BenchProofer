# refinement.md — sphinx-doc__sphinx-9602

Operation-by-operation correspondence between `Solution.lean`'s impl region
(`implementation_literalTypeNodes` plus the deep models `expandLiteral` / `wrap`
/ `valSeq` / `reprVal`) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement; state the bijection), **A-reference** (deep model
validated == the real callee — by G-AX for the unchanged sub-callees, by G-CONF
for the changed whole function), or **I** (identical concrete op). No row is a
consumed axiom; there is no `axioms` content (the callees are modeled deeply).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4); the A-reference sub-callees by **G-AX** (`axiom_check.py`); the narrative by
**G-EQ**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The change — `_parse_annotation` (`sphinx/domains/python.py`)

The gold patch has three hunks. They implement **two independently-observable
new behaviours** on a parametrised type whose arguments are constant values, and
hunk 2's head test additionally **preserves** the existing behaviour on every
other head — a third observable, and the one a head-blind model cannot see:

```
# hunk 1 — ast.Constant branch (python.py:126):
-    return [nodes.Text(node.value)]
+    return [nodes.Text(repr(node.value))]

# hunk 2 — ast.Subscript branch (python.py:150-154): after building the
#          bracketed result, wrap each inner Text in a `literal` node when the
#          head is Literal / typing.Literal:
+    if result[0] in ('Literal', 'typing.Literal'):
+        for i, subnode in enumerate(result[1:], start=1):
+            if isinstance(subnode, nodes.Text):
+                result[i] = nodes.literal('', '', subnode)

# hunk 3 — top-level rewrite loop (python.py:182-188): a `literal`-wrapped node
#          is unwrapped to its inner Text (so it stays plain text), and only
#          *unwrapped* Text nodes become cross-references:
-        if isinstance(node, nodes.Text) and node.strip():
+        if isinstance(node, nodes.literal):
+            result[i] = node[0]
+        elif isinstance(node, nodes.Text) and node.strip():
             result[i] = type_to_xref(str(node), env)
```

Net behaviour modeled: for `head[v1, v2, …]` with `head` ANY dotted Python type
name, the head becomes a cross-reference and the brackets/commas are
punctuation; the class of each ARGUMENT node is selected by the head. Under
`head ∈ {Literal, typing.Literal}` each constant value `vi` is **plain inline
text** showing `repr(vi)` — never a cross-reference; under every other dotted
head the argument node is a **cross-reference** as it has always been, since
hunk 2's guard is false there and hunk 3's `elif` leg runs.
`expandLiteral` (via `argNodeCtor`) is exactly this, on BOTH sides of the guard.

The head guard of hunk 2 is therefore a **changed control-flow operation whose
false branch is load-bearing**: it is what keeps `List[None]`'s and `int |
None`'s constants on the cross-reference path, which the graded P2P rows
`tests/test_domain_py.py::test_parse_annotation` (the `List[None]` case) and
`::test_pyfunction_with_union_type_operator` read. Both branches are modeled
(row 1 below), so neither can be satisfied vacuously.

| # | Solution.lean impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `head : List Char` with the domain hypothesis `okHead head` (any dotted Python type name) | the head string of the subscript, `result[0]` | R | `str ↔ List Char` (mapping §2). The domain is the whole shape a parametrised head has, so BOTH sides of the guard in row 1b are inside it. |
| 1b | `argNodeCtor head` (= `DocNode.text` iff `isLitHead head`, else `DocNode.xref`) — the head-selected argument node constructor | the `result[0] in ('Literal', 'typing.Literal')` guard of hunk 2, together with hunk 3's `if isinstance(node, nodes.literal) … elif isinstance(node, nodes.Text)` dispatch | I (a changed control-flow op, modeled on BOTH branches) | the guard is a concrete two-way test on the head string; its TRUE branch wraps each inner Text so hunk 3 unwraps it to plain text, its FALSE branch leaves the Text unwrapped so hunk 3's `elif` sends it to `type_to_xref`. Both legs are written out in the postcondition, so a model that ignores the head satisfies neither. Refuted mechanically by G-CONF, whose head pool straddles the guard (§4). |
| 2 | `values : List LitVal` | the `ast.Constant` arguments of the subscript | R | each `ast.Constant.value` (`bool`/`int`/`str`) ↔ a `LitVal` (mapping §2). The list is unrestricted, including empty (row 2b), because the postcondition carries no non-emptiness hypothesis. |
| 2b | `valSeq _ _ [] = [punct "(", punct ")"]` — the zero-argument spelling's region | the `elif isinstance(node, ast.Tuple)` branch's `else` leg, which appends `desc_sig_punctuation('', '(')` and `desc_sig_punctuation('', ')')` for a slice whose `elts` is empty (the source `head[()]`) | I | concrete and unchanged by the patch; transliterated by G-CONF, whose boundary rows include the empty argument list under both an ordinary head and the enumeration head. The pair is PUNCTUATION, so hunk 2's guard (which rewrites `nodes.Text` children only) cannot reach it — hence the region does not depend on the head, which is why `valSeq`'s empty arm ignores `mk`. |
| 3 | `wrap head inner` = `xref head :: punct "[" :: (inner ++ [punct "]"])` | the subscript branch building `result = unparse(head) ++ ['['] ++ inner ++ [']']`, then the top-level loop turning the head Text into `type_to_xref(head)` | I + A-reference | bracket/comma/head structure is concrete (I), transliterated by G-CONF; that the head Text becomes a `pending_xref` targeting `head` is the unchanged-callee `type_to_xref` carrier check (A-reference, G-AX §3.2). |
| 4 | `valSeq (argNodeCtor head) reprVal values` — one `argNodeCtor head (reprVal v)` per value, `punct ", "` between | hunks 1+2+3 together: each value Text shows `repr(value)` (hunk 1); under the enumeration head it is wrapped in a `literal` (hunk 2) and unwrapped back to plain Text (hunk 3's `if` leg), and under any other head it is left unwrapped and becomes a cross-reference (hunk 3's `elif` leg) | I + A-reference | the per-value emission and `", "` separators are concrete (I), and so is the head-selected node class (row 1b). The two A-references: (a) `reprVal == repr` on the modeled domain (G-AX §3.1); (b) which node class each argument ends up carrying — validated by the whole-function G-CONF equivalence (§3.3) with the change applied, over a head pool that covers both branches. |
| 5 | `result = expandLiteral head values` (`List DocNode`) | the returned `List[Node]` of `_parse_annotation` | R | `result` IS the emitted child sequence, class + text (mapping §2). The F2P `test_parse_annotation_Literal` asserts exactly this node-class+text sequence. |

## Discriminators — what the spec pins that the pre-image violates

Three independently-observable behaviours are pinned — two the change
introduces and one it PRESERVES. The shipped prepatch encodes the primary
introduced one; G-MUT exercises the second structurally; the preserved one is
pinned by the head-selected argument class and is what the P2P rows read:

- **Value-as-text vs value-as-xref** (hunks 2+3). `Solution_prepatch.lean`
  routes the values through `DocNode.xref` (the pre-image path where every
  non-blank Text became a cross-reference). The frozen postcondition `result =
  expandLiteral head values` demands `DocNode.text` for the values, so
  `correct_literalTypeNodes` FAILS. This is the nitpick of the issue:
  `Literal[True]` must not become a `py:class` reference.
- **`repr` vs raw value** (hunk 1). Rendering a string value bare (no quotes),
  the pre-image `nodes.Text(node.value)`, contradicts `reprVal` (single-quoted
  for strings), so the proof would FAIL on a string argument. This is what the
  F2P test's `'abc'` row observes (`"'abc'"`, with quotes); G-MUT kills the
  corresponding impl mutant.
- **PRESERVED: the zero-argument spelling** (the `ast.Tuple` empty leg, which
  the patch does not touch). The postcondition holds for EVERY argument list, so
  `values = []` is pinned to `wrap head [punct "(", punct ")"]` — a five-node
  sequence. An impl free there may abbreviate `Tuple[()]` to a lone reference,
  which the graded P2P row `tests/test_domain_py.py::test_parse_annotation`
  reads child-by-child, so such a refinement does not resolve even though the
  enumeration behaviour it was aimed at is untouched. `properties.py`'s r15 is
  that rival, and it is rejected.
- **PRESERVED: argument-as-xref under every other head** (hunk 2's false
  branch + hunk 3's `elif`). The postcondition holds for every `okHead head`,
  and `argNodeCtor` is `DocNode.xref` off the enumeration head, so an impl that
  renders the arguments the same way regardless of the head FAILS — it must read
  the head to decide. This is the facet a head-blind model leaves free: it is
  unobservable at the enumeration head alone, yet it is exactly what
  `tests/test_domain_py.py::test_parse_annotation` (`List[None]` → a
  cross-reference `None`) and `::test_pyfunction_with_union_type_operator`
  (`int | None` → a cross-reference `None`) assert, so a spec silent about it
  admits a model whose refinement regresses those rows while still resolving the
  F2P row. `properties.py`'s r11/r12/r13 are the three ways to get this wrong
  (selection dropped, too broad, too narrow) and all three are rejected.

## No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operations that genuinely *changed* —
constant rendering via `repr`, the head test, and the argument-node routing on
BOTH of its branches — are modeled **deeply** (`reprVal`, `argNodeCtor`,
`expandLiteral`), not hidden behind an axiom about the function under change and
not demoted to a domain hypothesis. There is no consumed axiom.

The head test specifically is a *changed control-flow op*, and a changed
control-flow op is only an I row when both of its branches are written into the
postcondition (row 1b). Encoding such a guard as a precondition hypothesis
instead would leave its false branch unconstrained, which is not a refinement of
the guard but a deletion of half of it.

## verify(Solution) ⇒ resolved

`correct_literalTypeNodes` holds only if the impl's output equals `expandLiteral
head values` for EVERY dotted head AND EVERY argument list: the head
cross-reference, the bracket/comma punctuation, and one node per value showing
`reprVal v` whose class is the one the head selects (steps 1b, 4) — plain text
under the enumeration head, a cross-reference under any other — with the
zero-argument spelling's parenthesis pair in place of the argument nodes when
there are none (step 2b). By R (`str ↔ List Char`, `LitVal ↔
ast.Constant`, node carriers) the verified sequence equals the changed
`_parse_annotation`'s output on both kinds of annotation; by G-AX the
sub-callees are sound (`reprVal == repr`, head `type_to_xref` carrier); by
G-CONF the whole deep model agrees node-for-node with the real changed callee on
≥10⁵ inputs spanning both sides of the head test, so neither branch is
validated at the other's expense. Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement and validated callees — and the gold patch
resolves (G-RESOLVE). Trust points: deep-model faithfulness (G-AX + G-CONF) and
refinement fidelity (this doc, G-EQ).
