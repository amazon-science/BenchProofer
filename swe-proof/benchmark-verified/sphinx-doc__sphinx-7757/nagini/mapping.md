# mapping.md — sphinx-doc__sphinx-7757

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 212fd67b9f0b4fae6a7c3501fdf1a9a5b2801329`, states the type
abstraction, and gives the provenance of the one axiomatized callee.

Repo file under change: `sphinx/util/inspect.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `resolve_positional_defaults(positionals, posonly, provided)` | the parameter-construction loops of `signature_from_str(signature)` — `sphinx/util/inspect.py:514` (body lines 519-537: the `posonlyargs` loop and the `args.args` loop that compute each parameter's `default`) | the modeled changed function: how supplied defaults are aligned across the positional parameters and attached to each `Parameter` |
| `render(value_code)` *(axiom — A-consumed)* | `sphinx.pycode.ast.unparse` (imported as `ast_unparse`), `sphinx/pycode/ast.py:61` — applied to a default AST node, e.g. `ast_unparse(args.defaults[...])` (`inspect.py:531`) | unchanged **partial** callee: renders one default-value AST node to its source string; the patch does not change it. Defined only on its `renderable` domain (raises `NotImplementedError` otherwise) |
| `renderable(value_code)` *(axiom — domain predicate)* | the domain of definedness of `sphinx.pycode.ast.unparse` — the node kinds `_UnparseVisitor` implements (`sphinx/pycode/ast.py`, the `visit_*` methods); its complement raises `NotImplementedError` | abstract predicate naming the inputs `render` may be applied to; guards every `render` call so the contract never claims a return value off-domain |
| `resolved_default(p, n, m, provided)` *(deep model)* | the per-position default decision: `Parameter.empty` vs `ast_unparse(defaults[...])` after the left-pad `for _ in range(len(defaults), positionals): defaults.insert(0, Parameter.empty)` (`inspect.py:519-537`, post-patch) | pure spec of the aligned default for one positional parameter |
| `first_default_pos(n, m)` | `positionals - len(args.defaults)` — equivalently the number of leading `Parameter.empty` slots the left-pad inserts (`inspect.py:530`, post-patch) | pure spec: index of the first defaulted positional parameter |
| `EMPTY()` | `inspect.Parameter.empty` — the unique sentinel meaning "this parameter has no default" | pure spec: the no-default sentinel |

The pre-patch repo code the change replaces (for the refinement audit, not
referenced from the consumer spec view): the `posonlyargs` loop at
`inspect.py:523-527` constructs each positional-only `Parameter` with **no
`default=` argument** (so the default is always `Parameter.empty`), and the
`args.args` loop at `inspect.py:529-537` computes alignment as
`len(args.args) - i <= len(args.defaults)` with
`ast_unparse(args.defaults[-len(args.args) + i])` — i.e. it indexes
`args.defaults` relative to the **ordinary-parameter count alone**, ignoring
that positional-only parameters also consume entries of the single combined
`args.defaults` list.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `ast.arguments` parameter lists: `args.posonlyargs ++ args.args` (the positional parameters, positional-only prefix then positional-or-keyword) | two integers: `positionals = len(posonlyargs) + len(args)` (= `n`) and `posonly = len(posonlyargs)` (= the length of the positional-only prefix) | a parameter is identified by its 0-based index `p` over the combined positional list; `p < posonly` ⇔ positional-only, `posonly <= p < positionals` ⇔ positional-or-keyword. Only the *count* and the prefix boundary matter for the alignment bug; names/annotations are irrelevant to it. |
| `args.defaults` — a single list of default-value AST nodes that, by Python's grammar, binds to the **trailing** positional parameters | `provided: List[int]` of value codes, `m = len(provided)` ≤ `positionals` | element `provided[j]` ↔ the `j`-th supplied default node, in source order; a supplied default node is a distinct non-sentinel code (`!= EMPTY()`). Its rendered source string is `render(provided[j])`. |
| `ast_unparse(node)` — render a default node to its source string | `render(value_code)`: a deterministic total map returning a non-sentinel code | the *value* of a rendered default is opaque to the alignment; what the spec pins is WHICH positions get `EMPTY` vs a rendered default, plus that a rendered default is never `Parameter.empty`. |
| `Parameter.empty` (the no-default sentinel) | `EMPTY()` = `-1` | a unique value distinct from every rendered-default code (`render(...) != EMPTY()`). |
| `Parameter(name, kind, default=..., annotation=...)` objects | the returned `List[int]` of resolved defaults, one per positional parameter in order | `Result()[p]` is `EMPTY()` ⇔ the real `Parameter` at index `p` has `default is Parameter.empty`; otherwise `Result()[p] == render(provided[p-(n-m)])` ⇔ the real `Parameter`'s `default == ast_unparse(defaults[p])`. Names, annotations, `kind`, and the non-positional parameters (`*args`, kwonly, `**kwargs`) are unchanged by the patch and omitted. |

`str` indexing/AST traversal is banned in Nagini; the carrier is therefore the
two positional counts plus the `List[int]` of default value codes, with the
specification carried over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `render` ↔ `sphinx.pycode.ast.unparse` (A-consumed) — a PARTIAL callee
**Callee:** `sphinx.pycode.ast.unparse(node)` (`sphinx/pycode/ast.py:61`, the
`_UnparseVisitor` dispatch). The patch does **not** change it; the changed
function merely calls it on whichever default node alignment selects.

**The callee is PARTIAL.** At the pinned `base_commit` (sphinx 3.1.0, py 3.9)
`_UnparseVisitor` implements `visit_*` for only a fixed set of node kinds
(Constant, Name, Attribute, Tuple/List/Dict/Set, BinOp/BoolOp/UnaryOp,
Subscript/Index, Call, Lambda, …) and **raises `NotImplementedError`** on any
other grammar-valid default expression (empirically: `IfExp` `a=1 if x else 2`,
`Compare` `a=x==y`, `JoinedStr` `a=f'{x}'`, `Slice` `a=z[1:2]`, dict-unpacking
`a={**w}`, `ListComp`, `Yield`, …). It is therefore **not total** on all
default nodes. Modelling it as a total never-raising function would be an
**over-claim of totality** (SPEC_GUIDE directive 7's #1 soundness defect).

**Domain restriction.** The model names the renderer's domain of definedness
with the abstract predicate `renderable(value_code)` and applies `render` ONLY
to value codes satisfying it: `render` carries `Requires(renderable(value_code))`,
and `resolve_positional_defaults` / `resolved_default` require every supplied
default value code to be `renderable`. So the contract never asserts a return
value on inputs the real callee does not handle. The only property the proof
then consumes, ON THAT DOMAIN, is that a rendered default is **never** the
`Parameter.empty` sentinel (`render(...) != EMPTY()`) — so a position the model
marks "has a default" really carries a source string — together with
referential transparency. This is the **weakest** contract sufficient: it says
nothing about the concrete rendered string, only that, on the renderer's
domain, it is a non-sentinel value, which is all the alignment correctness
needs. (Faithfulness note: this domain restriction does not weaken the bundle's
guarantee — the alignment bug is a position-selection effect independent of
which default expressions are renderable; the F2P/P2P signatures all use
renderable literal defaults, and the prepatch twin still fails on alignment.)

**Soundness check (G-AX):** `axiom_check.py` runs the REAL post-patch
`signature_from_str` on 3900 signatures (an exhaustive small enumeration of
`k` positional-only + `r` ordinary positional parameters with every contiguous
trailing default block, plus 4000 randomized fuzz signatures, plus the headline
`(a, b=0, /, c=1)` case) and asserts position-by-position that the real
`Parameter.default` is `Parameter.empty` exactly where the deep alignment model
predicts `EMPTY` and a non-empty source string exactly otherwise. For the
render axiom it validates BOTH directions of the partial callee: (i) ON the
domain it runs the REAL `ast.unparse` on renderable default expressions and
confirms a non-empty source string (never `Parameter.empty`), deterministic;
and (ii) OFF the domain it confirms the renderer RAISES on unsupported
grammar-valid expressions (so `renderable` is non-vacuous and the axiom never
claims a return value there). Exit 0 iff sound — confirmed RC=0 in the pinned
eval container (gold applied). It imports only the standard library plus the
`sphinx` package under test (the very module the patch lives in).

## 4. The behavioural change the spec pins

Python's grammar attaches the `defaults` list to the **trailing** positional
parameters, counted across positional-only and positional-or-keyword
parameters **together**. The desired behaviour: positional parameter `p` carries
a default iff `p >= positionals - m`. The pre-patch repo code (a) never attached
any default to positional-only parameters and (b) aligned ordinary-parameter
defaults against the ordinary-parameter count alone — so a defaulted
positional-only parameter such as `b` in `(a, b=0, /, c=1)` lost its default.
The spec senses exactly this through `ToSeq(Result())[p] == resolved_default(p,
…)` and the positional-only-not-exempt clause `ToSeq(Result())[p] != EMPTY()`
for a positional-only `p` inside the trailing default block (model_prepatch.py
fails on it).
