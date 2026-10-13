# mapping.md — sphinx-doc__sphinx-8265

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = b428cd2404675475a5c3dc2a2b0790ba57676202`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance. There are **no axioms and no A-references** in this bundle:
every callee the modeled renderers invoke is itself a renderer of a
sub-expression, and each unchanged such sub-expression is carried as a
pre-rendered `Expr.atom` leaf (an I-op). Consequently there is no
`axiom_check.py` (G-AX has nothing to check) and `conf_skip = false`.

Repo file under change: `sphinx/pycode/ast.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `renderGroup (elts : List Expr)` | `_UnparseVisitor.visit_Tuple` — `sphinx/pycode/ast.py:171` | modeled changed function #1 (render a parenthesised group of expressions) |
| `renderIndex (value idx : Expr)` | `_UnparseVisitor.visit_Subscript` — `sphinx/pycode/ast.py:168` | modeled changed function #2 (render an indexing expression) |
| `render : Expr → List Char` | `_UnparseVisitor.visit` dispatch over the modeled node shapes — `sphinx/pycode/ast.py:74` | pure spec: render an expression to source text; deep model of the renderer restricted to the touched shapes |
| `joinComma` | `", ".join(...)` (used throughout the visitor) | pure spec: comma-join already-rendered pieces |
| `isUnpack` | `isinstance(elt, ast.Starred)` (the `is_simple_tuple` guard, post-patch) | pure spec: is an element an unpacking element |
| `Expr.atom` | any node rendered by an **unchanged** `visit_*` method (`Name`, `Constant`, `Attribute`, operators, `Call`, `List`, `Set`, …) | a sub-expression already rendered to text by an unchanged renderer |
| `Expr.unpack` | `ast.Starred` | an unpacking element `*e` |
| `Expr.group` | `ast.Tuple` | a (possibly empty) parenthesised group of expressions |
| `Expr.index` | `ast.Subscript` (`value` ↔ `node.value`, `idx` ↔ `node.slice`) | an indexing expression `value[idx]` |

The two methods correspond to the two gold hunks; `visit_Tuple` and
`visit_Subscript` are mutually reachable through `visit`, so both live in the
single `render` recursion and are pinned by one `Expr` carrier.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a rendered source string | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `str` concat ↔ `List` `++`; `", ".join` ↔ `joinComma` |
| a Python `ast` expression node | `Expr` | structural: `ast.Tuple(elts)` ↔ `Expr.group (elts.map ·)`; `ast.Subscript(value, slice)` ↔ `Expr.index value slice`; `ast.Starred(v)` ↔ `Expr.unpack v`; **any other node** ↔ `Expr.atom t`, where `t` is the text that node's unchanged `visit_*` renders to (G-CONF lowers `atom t` by parsing `t` back to its real node and lets the real visitor render it — the identity, since `t` is already that node's rendering) |
| `node.elts` (a tuple's elements) | the `List Expr` argument of `group` | `len(node.elts)` ↔ `elts.length`; `node.elts == []` ↔ `elts.isEmpty` |
| `bool(value.elts)` (non-empty) | `!elts.isEmpty` | Python truthiness of a list ↔ list non-emptiness |
| `any(isinstance(e, ast.Starred) ...)` | `elts.any isUnpack` | element-wise Starred test |

`List Char`/`String` indexing in Lean is total and sound. The recursion in
`render` mirrors the visitor's recursive `self.visit(e)` calls; G-CONF's
`to_ast` reverses the bijection so the real visitor renders the same tree.

### Domain restriction (observable behaviour)

At `base_commit` the visitor has **no `visit_Starred` method**, so rendering any
`ast.Starred` node raises `NotImplementedError` — in BOTH branches of the
patched `visit_Subscript`. The patch's `not any(isinstance(elt, ast.Starred) …)`
clause is therefore defensive and **unobservable**: a tuple slice containing a
starred element raises regardless. `Expr.unpack` / `isUnpack` are kept in the
model only to mirror that clause faithfully (refinement.md, directive 3); G-CONF
does not generate Starred nodes because they lie outside the renderable domain.

### Eval-environment note (Python 3.9)

The SWE-Bench eval image runs **Python 3.9** (harness spec for sphinx 3.3),
where the `ast.Index` class still exists (deprecated) but — since the 3.9
"simplified subscription AST" change — the parser no longer produces it:
`ast.Subscript.slice` is the expression directly. The patch's
`elif isinstance(node.slice, ast.Index) and is_simple_tuple(node.slice.value)`
branch is therefore **dead code** in the eval environment; only the
`is_simple_tuple(node.slice)` branch (slice is itself a tuple) and the `else`
branch execute. (Even if an `Index`-wrapped node were constructed by hand, the
elif performs the identical flattening, so the observable output would be the
same.) The model encodes exactly the two reachable branches. This was
confirmed empirically in-container (the patched visitor renders `Tuple[int, int]`
→ `Tuple[int, int]`, `x[(a, b)]` → `x[a, b]`, `(1, 2, 3)` → `(1, 2, 3)`).

## 3. Callee provenance

None. Every node the modeled renderers descend into is either one of the three
modeled shapes (`group`/`index`/`unpack`, rendered deeply by `render`) or an
unchanged sub-expression carried as `Expr.atom` (an I-op, rendered by reproducing
its text). There is no unchanged imperative/pure callee whose behaviour is
assumed, hence no `axiom`, no `:|`-stub, and no A-reference. `axiom_check.py` is
intentionally absent (G-AX → skip: "no axioms in bundle").

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`8265`** so the
consumer-side verdict is reproducible. The R/I shadow transliterates `render`/
`joinComma`/`isUnpack` to Python; the oracle is the patched real
`sphinx.pycode.ast._UnparseVisitor` (`apply_gold=True`). Over 10⁵ fuzzed
expression trees plus the boundary set ({`(1,2,3)`, `()`, `(1)`, `Tuple[int,int]`,
`x[a]`, `x[a,b]`, `x[()]`, `x[(a)]`, `a[b][c]`}) the two agree with zero
disagreements.
