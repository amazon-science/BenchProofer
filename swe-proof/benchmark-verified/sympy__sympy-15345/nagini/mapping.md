# mapping.md — sympy__sympy-15345

Binds every model.py symbol to its repo counterpart at `base_commit`
`9ef28fba5b4d6d0168237c9c005a550e6dc27d81`, records the type abstraction, and
documents callee provenance.

## 1. Modeled function

| model.py | repo symbol | repo location (base_commit) | role |
|---|---|---|---|
| `print_lattice_call(name, operands)` | `MCodePrinter._print_Function` (the method `_print_MinMaxBase` is bound to, post-fix) | `sympy/printing/mathematica.py:96-102` | the rendering of a recognised function application to Mathematica surface syntax. The gold patch routes the lattice operators (`Max`/`Min`, i.e. `MinMaxBase` instances) into this method (`_print_MinMaxBase = _print_Function`, line 105 after patch) AND registers their recognised names in `known_functions` (lines 34-35 after patch), so the method takes the `expr.func.__name__ in self.known_functions` branch and emits `"%s[%s]" % (mfunc, self.stringify(expr.args, ", "))`. |

The observable change is the application delimiter: pre-fix the operators were
unrecognised and printed by the inherited generic printer
(`StrPrinter._print_Function`, `sympy/printing/str.py:160-161`) as
`name + "(" + stringify(args, ", ") + ")"` — ROUND parentheses, invalid in the
target surface language; post-fix they print as
`name + "[" + stringify(args, ", ") + "]"` — SQUARE brackets.

## 2. Type abstraction

| repo reality | model as | justification |
|---|---|---|
| a rendered string (`str`) | `PSeq[int]` of Unicode code points | Nagini bans `str` indexing (SPEC_GUIDE §2). `'['→91`, `']'→93`, `','→44`, `' '→32`, `'('→40`, `')'→41`. |
| `expr.args` (a tuple of SymPy sub-expressions) and their per-arg rendered strings `[self.parenthesize(item, 0) ... ]` produced by `stringify` | `operands: PSeq[PSeq[int]]`, the sequence of operands' already-rendered surface forms | the recursive rendering of each operand (`self.parenthesize`/`self._print`) is UNCHANGED machinery; only the outer assembly (name + brackets + ", "-join) changed. The model takes each operand's rendered form as a given `PSeq[int]` and assembles them. The operand ORDER is `expr.args`' order, fixed by SymPy's argument canonicalisation upstream of the printer (`MinMaxBase.__new__` / `_argset` / `ordered`, `sympy/functions/elementary/miscellaneous.py:340-371`) — identical pre/post fix — so the model is faithful to NOT reorder. |
| `mfunc` = the recognised name (`"Max"` / `"Min"`) from `known_functions` | `name: PSeq[int]` | the recognised Mathematica name; for `Max`/`Min` it is identical to `expr.func.__name__`. Taken as a given `PSeq[int]`. |
| `self.stringify(args, ", ")` (`sympy/printing/str.py:35-36`) = `", ".join(parenthesize(a,0) for a in args)` | `joined(operands)` (front-recursive ", "-join, model.py pure region) | a separator-join with separator `", "` and no trailing separator; modeled deeply (§3). |

**Termination (total correctness):** the real printer always answers —
assembling a function application's surface text from finitely many operand
fragments is a bounded computation (`", ".join` over a finite list plus the
`"%s[%s]"` format). The spec carries `Requires(MustTerminate(2))` on
`print_lattice_call` (consumed in the impl loop by
`Invariant(MustTerminate(i))`). Nagini is a partial-correctness verifier by
default, so without the obligation a diverging implementation would satisfy
every `Ensures` vacuously while sharing the spec.

## 3. Callee provenance

No `@ContractOnly` axiom is consumed. The only library helper the changed
assembly calls is `stringify` (`StrPrinter.stringify`,
`sympy/printing/str.py:35-36`), which is a plain `sep.join([...])`. Its
join-with-separator semantics are modeled DEEPLY by `joined` (the front-
recursive fold in the pure region) — an **A-reference**: `joined` is validated
== the real `", ".join` semantics by `axiom_check.py` (G-AX), not assumed via a
contract.

`stringify` evidence (`sympy/printing/str.py`):
```
35  def stringify(self, args, sep, level=0):
36      return sep.join([self.parenthesize(item, level) for item in args])
```
With `sep == ", "`, `stringify(args, ", ")` is exactly `", ".join(rendered_args)`:
the operands concatenated left-to-right with one `", "` between adjacent pairs
and no trailing separator — which is `joined(operands)`.

The bracket wrapping `"%s[%s]" % (mfunc, ...)` (`sympy/printing/mathematica.py:101`,
unchanged by the patch but now reached for the lattice operators) supplies the
`'['`/`']'` delimiters; `rendered(name, operands)` models that wrapping deeply.
