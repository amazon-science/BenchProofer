# refinement.md — sphinx-doc__sphinx-9367

Maps every operation in `implementation_renderTuple` to its `patch.diff`
counterpart in `_UnparseVisitor.visit_Tuple` (sphinx/pycode/ast.py:215 @
base_commit). Tags: **R** type-refinement, **A-consumed** proof uses a callee
axiom, **A-reference** op left as the real repo callee in G-CONF (not
axiomatized), **I** identical concrete op.

## Patch (post-patch `visit_Tuple`)
```python
def visit_Tuple(self, node: ast.Tuple) -> str:
    if len(node.elts) == 0:
        return "()"
    elif len(node.elts) == 1:
        return "(%s,)" % self.visit(node.elts[0])
    else:
        return "(" + ", ".join(self.visit(e) for e in node.elts) + ")"
```

The changed behavior is the addition of the `len(node.elts) == 1` branch, which
wraps the single rendered component with a TRAILING comma (`"(%s,)"`) instead of
letting it fall into the join branch (which would render `"(e)"` — a
parenthesized expression, not a one-element tuple). The empty and ≥2 branches are
unchanged in behavior.

## Modeling decision
The observable behavior of `visit_Tuple` is the returned source-text string, a
pure function of the rendered text of the tuple's components and their count. Each
component is rendered by the recursive `self.visit(e)`, which is UNCHANGED by the
patch. So the model takes the input to be `elts : List String` — the ordered,
already-rendered component strings — and pins how those pieces are wrapped/joined
by arity. The per-component renderer is absorbed into the input, so the spec holds
for EVERY component renderer and pins only the wrap/join logic — which is exactly
the modeled change.

## Operation correspondence
| # | Lean op (`implementation_renderTuple`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `if elts.length == 0 then return "()"` | `if len(node.elts) == 0: return "()"` | I | empty-tuple branch, `elts.length : Nat ↔ len(node.elts) : int`. |
| 2 | `else if elts.length == 1 then return "(" ++ elts.headI ++ ",)"` | `elif len(node.elts) == 1: return "(%s,)" % self.visit(node.elts[0])` | R | the FIXED branch: single rendered component `elts.headI ↔ self.visit(node.elts[0])` wrapped with a trailing comma. `String ↔ str`. |
| 3 | `else return "(" ++ String.intercalate ", " elts ++ ")"` | `else: return "(" + ", ".join(self.visit(e) for e in node.elts) + ")"` | R | ≥2-component branch: `String.intercalate ", " elts ↔ ", ".join(self.visit(e) for e in node.elts)`. |
| 4 | (input) `elts : List String` | `[self.visit(e) for e in node.elts]` | A-reference | the per-component recursive render `self.visit` is unchanged; left as the real visitor in G-CONF (NOT axiomatized, NOT deep-modeled — absorbed into the input). |

## R/I legs ⇒ G-CONF
Ops 1 (I), 2 and 3 (R) are the R/I content (the wrap/join logic). Op 4 is the
A-reference: G-CONF leaves the per-component visit as the REAL recursive visitor
(it does NOT substitute an axiom model) — that is how the wrap/join legs are
isolated and tested. `conf_skip = false`: the impl region has genuine R/I content
(the arity-dependent wrapping is the fixed behavior), so `conformance_check.py`
differential-tests the shadow (arity branch over already-rendered components) vs
the patched `unparse`'s output over ≥10^5 fuzzed tuple expressions.

## No A-consumed row
The proof consumes no property of the per-component renderer (it is absorbed into
the input `elts`), so `meta.json axioms = []`. Op 4 is recorded as an A-reference
solely to document the G-CONF binding to the real callee; there is no
`opaque`/`axiom` declaration in `Solution.lean` and `axiom_check.py` is a skip
stub.

## F2P alignment
`test_unparse[(1,)-(1,)]` parses `"(1,)"` and expects `unparse` to return `"(1,)"`.
Pre-patch the single component fell into the join branch and rendered `"(1)"`; the
discriminating clause of `problem_spec_renderTuple` (single component ⇒
`"(" ++ e ++ ",)"`) pins the trailing comma, and the prepatch impl (two-way split,
single component → `"(1)"`) CANNOT satisfy it — it fails on exactly the
`[e]` clause (`"(e)" ≠ "(e,)"`). The PASS_TO_PASS cases `()` (empty) and
`(1, 2, 3)` (≥2) are pinned by the unchanged branches. `patch.diff` (gold
verbatim) makes the harness resolve.
