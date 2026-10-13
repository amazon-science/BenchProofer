# refinement.md — sympy__sympy-15976

Maps every operation of `implementation_symbolMarkup` (Solution.lean impl region)
to its `patch.diff` (gold) counterpart. Tags: **R** = type-only refinement,
**I** = identical concrete op, **A-consumed** = proof uses a callee axiom,
**A-reference** = deep model validated == real callee by G-AX.

The gold patch rewrites the body of `_print_Symbol` (presentation printer) so the
returned node `x` *is* the scripted element (or the bare name `mi`) directly,
rather than always wrapping it inside a freshly allocated `<mi>`; and it moves the
`mathvariant="bold"` `setAttribute` to AFTER `x` is chosen.

| # | impl op (Solution.lean) | patch.diff (gold) counterpart | tag |
|---|---|---|---|
| 1 | `mname := MathNode.elem "mi" [] [MathNode.text name]` | `mname = createElement('mi'); mname.appendChild(createTextNode(name))` | R (minidom node ↔ `MathNode.elem`/`text`; type bijection in mapping.md) |
| 2 | `if supers.length == 0 then if subs.length == 0 then mname` | `if len(supers)==0: if len(subs)==0: x = mname` | I (case split + assignment) |
| 3 | `else MathNode.elem "msub" [] [mname, joinPieces subs]` | `else: x = createElement('msub'); x.appendChild(mname); x.appendChild(join(subs))` | R (two `appendChild` ↔ children list `[mname, join subs]`) |
| 4 | `else if subs.length == 0 then MathNode.elem "msup" [] [mname, joinPieces supers]` | `else: if len(subs)==0: x = createElement('msup'); x.appendChild(mname); x.appendChild(join(supers))` | R (as #3) |
| 5 | `else MathNode.elem "msubsup" [] [mname, joinPieces subs, joinPieces supers]` | `else: x = createElement('msubsup'); appendChild(mname); appendChild(join(subs)); appendChild(join(supers))` | R (three children, subs before supers — matches gold order) |
| 6 | `joinPieces` (single → `mi`; many → `mrow` of `mi`s with `mo " "` separators) | the local `join(items)` closure (unchanged by the patch) | R (deep model of unchanged helper; structure preserved) |
| 7 | `if style == "bold" then x := x.setAttr "mathvariant" "bold"` | `# Set bold font?` `if style == 'bold': x.setAttribute('mathvariant', 'bold')` | I (post-assembly attribute set on chosen `x`) |
| 8 | `return x` | `return x` | I |

Every op is R or I. There is **no A-consumed and no A-reference**: the markup
assembly and the `join` helper are modeled deeply; the minidom constructors are
modeled directly by `MathNode`. Hence `axiom_check.py` is a skip stub and
`meta.json conf_skip = false` (the impl region is R/I, mechanically refuted by
`conformance_check.py` over 1.2e5 fuzzed inputs + 10 F2P edge cases).

## Pre-patch divergence (G-DIFF)
The pre-patch impl allocates an outer `<mi>` element, sets the bold attribute on
it up front, and appends the scripted element (or the bare name text) as its
CHILD. For any scripted symbol this yields `<mi><msub>…</msub></mi>` instead of
the bare `<msub>…</msub>`, so the top-level `nodeName` is `'mi'` not `'msub'` —
exactly what `test_presentation_symbol` (F2P) rejects. The carried gold proof
(`rfl`) cannot close against the buggy impl, so `Solution_prepatch.lean` fails
G-VERIFY.
