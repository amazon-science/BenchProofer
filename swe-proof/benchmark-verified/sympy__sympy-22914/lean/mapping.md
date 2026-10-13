# mapping.md — symbol binding & type bijection (sympy__sympy-22914)

## Modeled function
- **Lean** `implementation_printApp : String → List String → String → String`
- **Python** the per-node emission decision of
  `CodePrinter._print_Function` (`sympy/printing/codeprinter.py:415-441 @
  c4e836cdf7`), driven by the `known_functions` mapping that the printer
  assembles from the module-level name→built-in table in
  `sympy/printing/pycode.py:19-21 @ c4e836cdf7`.

### What the change is
`_print_Function` decides how to render a function application
`f(a₁,…,aₙ)`. Its FIRST arm fires when the function's class name is a key of
`self.known_functions`: it emits `mapped_name(printed_args)` (via
`_print_known_func` → `'{name}({args})'.format(name=_module_format(known),
args=', '.join(...))`). When the name is NOT a key of that table, the node is
emitted by the LATER arms instead (a rewrite to `Piecewise`, per-class
printers, or the not-supported fall-through) — those later arms are unchanged
by the patch.

The patch adds two rows to the plain name→built-in table in `pycode.py`:
the minimum operation ↦ `min` and the maximum operation ↦ `max` (alongside the
pre-existing absolute-value ↦ `abs` row). After the patch, those two class
names are keys of the table, so the built-in dispatch arm fires for them and
renders `min(args)` / `max(args)`. Before the patch the arm does not fire for
them, and rendering is left to the later, unchanged arms.

**Empirically confirmed at base_commit** (printer on the worktree):
`Min(x,y)` pre-patch → `((x) if (x <= y) else (y))` (the Piecewise-rewrite arm);
post-patch (gold applied) → `min(x, y)`. `Max(x,y,z)` → `max(x, y, z)`.
`Abs(x)` → `abs(x)` both pre- and post-patch. A genuinely unknown name `Foo` →
the not-supported fall-through `Foo(x, y)` both pre- and post-patch.

### Modeled slice (inputs + observable) — TOTAL, no domain restriction
- **Observable** = the source text the printer emits for one
  function-application node, as `String`.
- `name : String` — the application head/class name (`expr.func.__name__`).
- `args : List String` — the already-printed argument strings
  (`[parenthesize(a,0) for a in expr.args]`); per-argument printing is
  unchanged by the patch and abstracted into the inputs.
- `fallback : String` — the source text the UNCHANGED surrounding printing
  machinery emits for this node when its head is none of the three
  builtin-mapped heads modeled here (`_known_functions_math` routing,
  the `_rewriteable_functions` Piecewise rewrite, per-class `_print_<cls>`
  printers, the not-supported fall-through — all untouched by the gold hunk).
  That machinery is pre-existing, unchanged infrastructure whose OUTPUT is
  supplied to the modeled per-node decision as a read-only input. The fourth
  spec conjunct pins the routine to return it verbatim for every non-mapped
  head — the no-change half of the contract. The spec is therefore total:
  EVERY name's emission is pinned, either to a built-in call or to `fallback`.

## Type bijection (used by G-CONF)
| Python | Lean | notes |
|---|---|---|
| function class name `expr.func.__name__` (`str`) | `name : String` | dispatch key |
| printed argument strings `[parenthesize(a,0) …]` (`list[str]`) | `args : List String` | arg printing unchanged by patch |
| unchanged machinery's emission for a non-mapped head (`str`) | `fallback : String` | the machinery itself is NOT modeled — its OUTPUT is the input |
| arm fires: `name in known_functions` | the `if name = …` ladder matching | post-patch: true for the min/max ops and the pre-existing abs |
| arm output `'{m}({args})'.format(...)`, `m=_module_format(v)=v` | `renderCall v args = v ++ "(" ++ … ++ ")"` | plain-table value has no module prefix → `_module_format` identity |
| `', '.join(printed_args)` | `String.intercalate ", " args` | identical separator/join |
| arm does NOT fire (`name not in known_functions`) | result = `fallback` | the node keeps the unchanged machinery's emission, verbatim |

## Callee provenance
- No UNCHANGED callee is consumed as an axiom. The dispatch test, the
  name→built-in mapping, and the `', '.join` + format are all modeled DEEPLY
  (spelled out: the `if` ladder + `renderCall`). These are pure Lean, not
  axiomatized. The `axioms` region is empty.
- The argument-printing recursion (`self._print(arg)`) and the non-mapped
  emission machinery are unchanged by the patch and abstracted into the
  read-only inputs `args` / `fallback` — not modeled, not axiomatized.

## Flag dependency
None. The patch is purely additive (two new table rows); the dispatch is an
unconditional membership test on the name key.

## G-CONF fuzz seed
Pinned seed: **22914**. ≥10^5 fuzzed expression inputs: real `Min`/`Max`/`Abs`
nodes (2–5 args, nesting, integer args) exercising the built-in-call legs, and
real non-mapped heads (`sin`, `exp`, `gamma`, undefined `f`, `Piecewise`, …)
exercising the fallback pass-through. The oracle is the REAL post-patch
printer `PythonCodePrinter().doprint(expr)` (gold applied). The shadow is the
transliterated `implementation_printApp`, fed the printer's own
`parenthesize(arg, 0)` outputs as `args` and a pristine same-class printer's
`doprint(expr)` as `fallback` on non-mapped heads (a poison sentinel on mapped
heads, so a shadow that leaks `fallback` where the built-in call is required
diverges).
