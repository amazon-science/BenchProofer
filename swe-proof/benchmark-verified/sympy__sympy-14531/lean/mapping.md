# mapping.md — sympy__sympy-14531

## Symbol binding (file:line @ base_commit 205da797006360fc629110937e39a19c9561313e)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_printRelational` / `problem_spec_printRelational` | `StrPrinter._print_Relational` (charmap branch) | `sympy/printing/str.py:619` (return line `633`) |
| `implementation_printLimit` / `problem_spec_printLimit` | `StrPrinter._print_Limit` | `sympy/printing/str.py:216` (return lines `219`,`221`) |
| `render : Settings → Expr → String` | the printer's own NESTED subexpression renderer `self._print(sub)` at the active settings — a fresh `StrPrinter(settings)` whose `_print_level` is pre-bumped to the container's frame (NOT the top-level `sstr(sub, **settings)`; see "Rendering context" below) | `sympy/printing/printer.py` `Printer._print` (recursion depth `_print_level`); `sstr` at `str.py:807` |

The gold patch touches MANY `_print_*` methods (AppliedPredicate, ExprCondPair,
Lambda, Limit, MatrixElement, Normal, Permutation, PermutationGroup, PolyRing,
FracField, Relational, Uniform), but they all share ONE behavior: each replaced a
bare `%s`/`str()` interpolation of a subexpression (which renders at the DEFAULT
settings) with `self._print(...)` (which renders at the printer's ACTIVE
settings). Two representatives are modeled — the two exercised by the
FAIL_TO_PASS tests:
  * `_print_Relational` — `test_python_relational`, `test_Rational`
    (`sstr(Eq(x, Rational(2,3)), sympy_integers=True) == "Eq(x, S(2)/3)"`);
  * `_print_Limit` — `test_Rational`
    (`sstr(Limit(x, x, Rational(7,2)), sympy_integers=True) == "Limit(x, x, S(7)/2)"`).
Both fixed routines collapse to the same skeleton, so the two triples capture the
single behavioral change the issue describes.

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Lean | Python |
|---|---|
| `Settings : Type` (abstract) | the full rendering profile: the StrPrinter settings dict (discriminating key `sympy_integers : bool`) TOGETHER WITH the rendering context (nested-in-a-container vs bare top-level; see "Rendering context") |
| `Expr : Type` (abstract) | a sympy `Expr` (subexpression) |
| `render : Settings → Expr → String` | `nested_print(s, e)` — a fresh `StrPrinter(s)` with `_print_level` pre-bumped to the container's frame, then `._print(e)`; == the real `self._print(e)` as invoked from inside `_print_Relational` / `_print_Limit` |
| `settings : Settings` | the ACTIVE profile: the settings dict passed to the top-level `sstr(...)`, in the NESTED context |
| `defaultSettings : Settings` (impl/proof region only) | the default/bare profile a `%s`/`str(sub)` interpolation uses: default options `{}` in the TOP-LEVEL context (a bare `str()` starts a fresh printer at `_print_level` 0) |
| `relName : String` | `charmap[expr.rel_op]` ∈ {"Eq","Ne",…} |
| `lhs rhs : Expr` | `expr.lhs`, `expr.rhs` |
| `dirIsDefault : Bool` | `str(dir) == "+"` |
| `e z z0 dir : Expr` | `expr.args` of the `Limit` (`e, z, z0, dir`) |
| `result : String` | the rendered string |

`Settings` and `Expr` are abstract Lean type variables; `render` is universally
quantified, so the spec/impl are parametric over EVERY renderer. The only modeled
behavior is which profile (`settings` vs `defaultSettings`) is handed to `render`
for the nested subexpressions. The fix passes the ACTIVE `settings`; the prepatch
passes the constant `defaultSettings`.

## Rendering context (why `render` is NOT top-level `sstr`)

`Printer._print` tracks a recursion depth `_print_level`
(`sympy/printing/printer.py:246`), and `StrPrinter._print_Float` with the default
`full_prec="auto"` strips trailing zeros exactly when `_print_level > 1`
(`str.py:611`): nested `self._print(Float(1.5))` gives `'1.5'` while top-level
`sstr(Float(1.5))` gives `'1.50000000000000'`. So the real subexpression renderer
inside a container depends on the options dict AND the nested context. The
abstract Lean `Settings` denotes that whole profile (options + context); both the
gold `self._print(...)` and the prepatch bare `str(...)` are instances of the SAME
`render` at different profiles — active-options/nested vs default-options/
top-level — so the model is unchanged in shape and the G-CONF shadow binds
`render settings ·` to a `_print_level`-pre-bumped `StrPrinter(settings)._print`,
byte-for-byte the container's nested call.

## Callee provenance + flag deps

- `render` (the subexpression renderer) is the UNCHANGED `Printer._print`
  dispatch. It is NOT axiomatized: it is left universally quantified, so it is an
  A-reference recorded only to document the G-CONF binding to the real callee.
- Flag dependency: the observable difference between active and default profile is
  governed by the `sympy_integers` setting in `_print_Rational`
  (`str.py:571`: `S(%s)/%s` when `sympy_integers` else `%s/%s`). G-CONF fuzzes
  `sympy_integers ∈ {True, False}` and uses rational-bearing subexpressions so the
  active-vs-default distinction is observable.

## Pinned G-CONF fuzz seed

`random.Random(14531)`, N = 100_000 (`conformance_check.py`).
