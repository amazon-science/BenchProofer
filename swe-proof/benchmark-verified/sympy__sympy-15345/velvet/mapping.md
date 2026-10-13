# mapping.md — sympy__sympy-15345

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 9ef28fba5b4d6d0168237c9c005a550e6dc27d81`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee/dispatch provenance. `spec_provenance: "cold"` (meta.json): the spec was
derived from the problem statement, the gold patch, and the repo source only.

Repo file under change: `sympy/printing/mathematica.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `renderNode (head args : List Char) (kind : NodeKind)` | the body of `MCodePrinter._print_Function` (`sympy/printing/mathematica.py:99`, post-patch reused for the extremum node class) together with the node-class → print-method dispatch in `Printer._print` (`sympy/printing/printer.py`) | the modeled changed behaviour: which delimiter pair surrounds a node's rendered argument text |
| `NodeKind.functionApp` | a node whose class resolves dispatch to `_print_Function` — a named-function application rendered `Head[args]` | node kind |
| `NodeKind.extremum` | a `Max`/`Min` node (class `MinMaxBase`, `sympy/functions/elementary/miscellaneous.py`) — the node the patch reroutes to the function-application rendering | node kind |
| `NodeKind.plainExpr` | any node with no dedicated `_print_*` in `MCodePrinter`, rendered by the inherited generic fallback `StrPrinter._print_<...>`/`_print_Function`-style fallback as `Head(args)` | node kind |
| `render (head args : List Char) (kind : NodeKind)` *(deep model)* | the delimiter-selection behaviour the dispatch realises: `_print_Function`'s `"%s[%s]"` template (square brackets) vs the generic round-parenthesis form for un-dispatched nodes | pure spec: the rendered source text for one node |

Pre-patch repo facts the change removes/adds (refinement audit only, not in the
consumer spec view):
- `known_functions` (`mathematica.py:11-33`) gains `"Max"`/`"Min"` entries —
  behaviourally inert (the head name they map to equals the fallthrough head
  name `expr.func.__name__`; verified empirically, refinement.md §B).
- `MCodePrinter` gains `_print_MinMaxBase = _print_Function`
  (`mathematica.py` post-patch) — the load-bearing change: it makes the
  `MinMaxBase` node class dispatch to the bracketed function-application
  renderer instead of falling through to the parenthesised generic printer.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

The table G-CONF (§4.1) uses to translate values between the Lean value domain
and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the rendered source `str` returned for a node, and its `head` / joined-argument substrings | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `str` concat ↔ `List` `++`; one ASCII char ↔ `Char.ofNat (ord ch)` |
| the node's head name (`expr.func.__name__`) | `head : List Char` | identity on the character content; an INPUT to `renderNode` (unchanged by the patch) |
| the node's arguments rendered and comma-joined (`self.stringify(expr.args, ", ")`) | `args : List Char` | identity on the character content; an INPUT to `renderNode`. The argument order/text is produced by the same `stringify` before and after the patch, so it is held fixed on both sides of G-CONF (the patch does not touch it). |
| the node's class identity, reduced to the only distinction the rendering reacts to | `kind : NodeKind` | a `MinMaxBase` node ↔ `.extremum`; a node dispatching to `_print_Function` ↔ `.functionApp`; an un-dispatched node ↔ `.plainExpr` |
| `'['`/`']'` vs `'('`/`')'` delimiter pair | the literal `['[']`/`[']']` vs `['(']`/`[')']` in `render` | identity |

Note (arg order): `Max(x, 2)` renders its args as `2, x` both pre- and
post-patch (SymPy's `MinMaxBase` canonical-orders its arguments at construction,
independent of the printer). The patch changes ONLY the surrounding delimiter
pair, not the argument text; the model treats `args` as a fixed input, matching
that fact.

## 3. Dispatch / callee provenance (no axioms — G-AX skipped)

There is **no axiomatized callee** and **no A-reference deep model of an outside
callee**. `render` models the printer's delimiter-selection dispatch DEEPLY over
the finite `NodeKind` space; the comma-joining of arguments (`stringify`) is an
unchanged helper whose output is consumed as the `args` input, owed no contract.

Consequently `axiom_check.py` is omitted and `meta.json gates.G-AX.status =
"skip"` (the astropy__astropy-13236 no-axiom dispatch precedent).

**Empirical confirmation of the load-bearing change (cold, from the repo +
container):** with the dict-only half of the patch applied (the `"Max"`/`"Min"`
`known_functions` entries) and the dispatch alias withheld, `Max(x,y,z)` still
renders `Max(x, y, z)` (parens) — the dict change is inert. With the dispatch
alias `_print_MinMaxBase = _print_Function` applied alone, `Max(x,y,z)` renders
`Max[x, y, z]` (brackets) — the alias is sufficient. So the modeled behaviour is
the node-kind → delimiter dispatch, and the extremum kind moving from the paren
branch to the bracket branch is the whole observable fix.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15345`** so the
consumer-side verdict (§11.3) is reproducible. It drives the patched real
`mathematica_code` on concrete nodes of each `NodeKind`, recovers the
(head, joined-args, delimiter-pair) observable, and diffs the modeled
`render`'s delimiter choice against it; the unchanged argument text is read off
the real render and held fixed on both sides, isolating the R/I dispatch leg.
