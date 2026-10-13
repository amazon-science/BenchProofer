# refinement.md — sympy__sympy-15345

Operation-by-operation correspondence between `model.py`'s implementation (the
`print_lattice_call` impl region + the deep `joined`/`rendered` pure models) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `Ensures`), **A-reference** (a deep model
validated == the real callee by `axiom_check.py` / G-AX, NOT consumed), or
**I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The gold patch

```
# hunk 1 — sympy/printing/mathematica.py, known_functions table
+    "Max": [(lambda *x: True, "Max")],
+    "Min": [(lambda *x: True, "Min")],

# hunk 2 — MCodePrinter body
+    _print_MinMaxBase = _print_Function
```

Together these make a `MinMaxBase` node (`Max`/`Min`) dispatch to
`_print_Function` AND be a recognised name in `known_functions`, so
`_print_Function` takes its recognised-function branch and returns
`"%s[%s]" % (mfunc, self.stringify(expr.args, ", "))` — the recognised name,
then a `[`...`]`-delimited, `", "`-joined operand list.

## B. Operation correspondence

| # | model.py impl op (`print_lattice_call` / pure models) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `name: PSeq[int]` | `mfunc` (the recognised name from `known_functions`, e.g. `"Max"`/`"Min"`) | R | `str` ↔ `PSeq[int]` code points (mapping.md §2). |
| B2 | `operands: PSeq[PSeq[int]]` | `expr.args`, each rendered by `self.parenthesize(item, 0)` inside `self.stringify` | R | each operand's already-rendered surface form is a `PSeq[int]`; the operand sequence is `PSeq[PSeq[int]]`. The per-operand rendering is UNCHANGED machinery taken as given; order = `expr.args` order, fixed upstream and identical pre/post (mapping.md §2). |
| B3 | `joined(operands)` (front-recursive ", "-join, no trailing separator) | `self.stringify(expr.args, ", ")` = `", ".join([parenthesize(a,0) for a in args])` (`sympy/printing/str.py:35-36`) | A-reference | the separator-join is modeled DEEPLY (`joined` in the pure region) — there is no consumed `stringify` axiom. The deep model is validated == the real `", ".join` semantics by `axiom_check.py` (G-AX): for any operand list, `joined == ", ".join`. |
| B4 | `name + PSeq(lbracket()) + body + PSeq(rbracket())` (i.e. `rendered(name, operands)`), with `lbracket()==91 ('[')`, `rbracket()==93 (']')` | `"%s[%s]" % (mfunc, ...)` (`sympy/printing/mathematica.py:101`) | I | concatenation `name + '[' + body + ']'` ↔ the `%`-format `"%s[%s]"`; the literal bracket characters `'['`/`']'` are identical concrete code points. |
| B5 | the loop building `body` back-to-front, one `joined` unfold per step | (no explicit loop — `str.join` performs the same fold internally) | A-reference | the loop computes exactly `joined(operands)`, the body asserts equal to it via the postcondition `Result() == rendered(...)`; its equality to the real `", ".join` is the B3 G-AX check. |

## C. The discriminating clause (G-DIFF)

The change's observable content is the application delimiter: **square brackets
`[`...`]` (post) vs round parentheses `(`...`)` (pre)**. In the model this lives
in `rendered(name, operands) = name + PSeq(91) + joined + PSeq(93)`, pinned by
the postcondition `Ensures(Result() == rendered(name, operands))` and by
`Ensures(Result()[len(name)] == lbracket())` /
`Ensures(Result()[len(Result())-1] == rbracket())`.

`model_prepatch.py` reproduces the pre-fix behaviour: the operators are
unrecognised and fall to the generic reduction-printer
(`StrPrinter._print_Function`), which wraps the SAME `", "`-joined body in ROUND
parentheses — `name + PSeq(40) + body + PSeq(41)`. It keeps the spec
byte-identical and **fails** the postcondition `Result() == rendered(...)`
(`'(' = 40 ≠ '[' = 91`), which is exactly the spec sensing the change (G-DIFF).

## D. No kind-3 (unexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely changed —
emitting the recognised name with SQUARE-bracket application syntax instead of
the generic round-paren form — is modeled DEEPLY (the `rendered`/`joined`
assembly spelled out and verified, steps B3-B5), not hidden behind an axiom
about the changed printer method. There is **no consumed `@ContractOnly`
axiom**; the only library helper invoked by the changed assembly, `stringify`'s
`", ".join`, appears only as the **A-reference** that G-AX validates `joined`
against.

## D2. Termination obligation (total correctness)

Nagini is a partial-correctness verifier by default: a non-terminating
implementation (bare self-recursion, an endless loop) satisfies every
`Ensures` vacuously while sharing the spec byte-for-byte — a wrong
implementation the spec would otherwise admit (the G-PANEL-1 auditor
demonstrated exactly this class). The real printer always answers: assembling
a function application's surface text from finitely many operand fragments is
a bounded computation. The spec therefore carries
`Requires(MustTerminate(2))` on `print_lattice_call` (consumed in the impl
loop by `Invariant(MustTerminate(i))`, with `i` the strictly decreasing,
bounded-below measure). With termination required and the full functional
postcondition `Result() == rendered(name, operands)`, any verifying same-spec
implementation must terminate and return exactly the pinned text — the spec is
functionally complete on its domain.

## E. verify(model) ⇒ resolved

`print_lattice_call` verifies only if its output equals
`rendered(name, operands)` — the recognised name, then `'['`, then the
`", "`-joined operands in order, then `']'`. By R (str ↔ PSeq, operands taken
as given in `expr.args` order) and I (the bracket-format) the verified output
equals `"%s[%s]" % (mfunc, self.stringify(expr.args, ", "))` for the lattice
operators, which is exactly what the gold patch makes `_print_Function` produce
once `Max`/`Min` are routed in via `_print_MinMaxBase = _print_Function` and
registered in `known_functions`. By G-AX the deep `joined` model equals the real
`", ".join` (A-reference). Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and the audited deep model —
and the gold patch resolves (G-RESOLVE: `mcode(Max(x,2)) == "Max[2, x]"`,
`mcode(Max(x,y,z)*Min(y,z)) == "Max[x, y, z]*Min[y, z]"`, the F2P `test_Function`
assertion). The single trust point is refinement fidelity (this document, G-EQ)
plus the one A-reference G-AX check.
