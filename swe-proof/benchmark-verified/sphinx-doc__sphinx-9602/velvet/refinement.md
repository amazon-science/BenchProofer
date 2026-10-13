# refinement.md — sphinx-doc__sphinx-9602

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `literalTypeNodes` `do` block plus the deep models `expandLiteral` /
`wrap` / `valSeq` / `reprVal`) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement; state the bijection), **A-reference** (deep model
validated == the real callee — by G-AX for the unchanged sub-callees, by G-CONF
for the changed whole function), or **I** (identical concrete op). No row is a
consumed `axiom`; there is no `axioms` content (the callees are modeled deeply).
A *changed op Velvet cannot express* is FORBIDDEN here.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference sub-callees by **G-AX** (`axiom_check.py`); the narrative
by **G-EQ**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The change — `_parse_annotation` (`sphinx/domains/python.py`)

The gold patch has three hunks, implementing **two independently-observable
behaviours** on a parametrised type whose arguments are constant values:

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

Net behaviour modeled: for `head[v1, v2, …]` with `head ∈ {Literal,
typing.Literal}`, the head becomes a cross-reference, the brackets/commas are
punctuation, and each constant value `vi` is rendered as **plain inline text**
showing `repr(vi)` — never a cross-reference. `expandLiteral` is exactly this.

| # | Solution.lean impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | `head : List Char`, the two `require head = …` literals | the `result[0] in ('Literal', 'typing.Literal')` guard | R | `str ↔ List Char` (mapping §2). The modeled domain is exactly the guard's true-branch. |
| 2 | `values : List LitVal` | the `ast.Constant` arguments of the subscript | R | each `ast.Constant.value` (`bool`/`int`/`str`) ↔ a `LitVal` (mapping §2). |
| 3 | `wrap head inner` = `xref head :: punct "[" :: (inner ++ [punct "]"])` | the subscript branch building `result = unparse(head) ++ ['['] ++ inner ++ [']']`, then the top-level loop turning the head Text into `type_to_xref(head)` | I + A-reference | bracket/comma/head structure is concrete (I), transliterated by G-CONF; that the head Text becomes a `pending_xref` targeting `head` is the unchanged-callee `type_to_xref` carrier check (A-reference, G-AX §3.2). |
| 4 | `valSeq DocNode.text reprVal values` — one `DocNode.text (reprVal v)` per value, `punct ", "` between | hunks 1+2+3 together: each value Text shows `repr(value)` (hunk 1), is wrapped in a `literal` (hunk 2) and unwrapped back to plain Text — NOT a cross-reference (hunk 3) | I + A-reference | the per-value emission and `", "` separators are concrete (I). The two A-references: (a) `reprVal == repr` on the modeled domain (G-AX §3.1); (b) the value nodes stay PLAIN TEXT (the `literal`-unwrap path), so `DocNode.text` not `DocNode.xref` — validated by the whole-function G-CONF equivalence (§3.3) with the patch applied. |
| 5 | `out = expandLiteral head values` returned (`List DocNode`) | the returned `List[Node]` of `_parse_annotation` | R | `out` IS the emitted child sequence, class + text (mapping §2). The F2P `test_parse_annotation_Literal` asserts exactly this node-class+text sequence. |

## Discriminators — what the spec pins that the bugs violate

Two independently-observable fixed behaviours, two failing prepatches:

- **Value-as-text vs value-as-xref** (hunks 2+3). `Solution_prepatch_2.lean`
  routes the values through `DocNode.xref` (the pre-patch path where every
  non-blank Text became a cross-reference). The frozen postcondition `out =
  expandLiteral head values` demands `DocNode.text` for the values, so
  `prove_correct` FAILS. This is the nitpick bug of the issue: `Literal[True]`
  must not become a `py:class` reference.
- **`repr` vs raw value** (hunk 1). `Solution_prepatch.lean` renders a string
  value bare (no quotes), the pre-patch `nodes.Text(node.value)`. The
  postcondition demands `reprVal` (single-quoted for strings), so `prove_correct`
  FAILS on a string argument. This is what the F2P test's `'abc'` row observes
  (`"'abc'"`, with quotes).

## No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operations that genuinely *changed* —
constant rendering via `repr` and the literal-value text routing — are modeled
**deeply** (`reprVal`, `expandLiteral` with `DocNode.text` values), not hidden
behind an axiom about the function under change. There is no consumed axiom.

## verify(Solution) ⇒ resolved

`literalTypeNodes` verifies only if its output equals `expandLiteral head
values`: the head cross-reference, the bracket/comma punctuation, and one PLAIN
TEXT node per value showing `reprVal v` (step 4). By R (`str ↔ List Char`,
`LitVal ↔ ast.Constant`, node carriers) the verified sequence equals the patched
`_parse_annotation`'s output on the tested `Literal[...]` annotations; by G-AX
the sub-callees are sound (`reprVal == repr`, head `type_to_xref` carrier); by
G-CONF the whole deep model agrees node-for-node with the patched real callee on
≥10⁵ inputs. Therefore a model satisfying this spec, refined by the map above, is
the gold patch up to type refinement and validated callees — and the gold patch
resolves (G-RESOLVE). Trust points: deep-model faithfulness (G-AX + G-CONF) and
refinement fidelity (this doc, G-EQ).
