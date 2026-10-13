# refinement.md — sympy__sympy-22080

The operation-by-operation correspondence between `model.py`'s implementation
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses an
axiom's `Ensures`, and **A-reference**, where a deep model is validated == the
real callee by axiom_check.py / G-AX), or **I** (identical concrete operation).
The claim: *any implementation that verifies against this frozen spec, refined
per the map below, is behaviourally equal to the gold patch on the tested
inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE). The gold touches two files / two sites.

## Total-correctness obligations (applies throughout)

Each contracted function carries `Requires(MustTerminate(n))` (the composite at
measure 2 so it may invoke the two standalone functions at measure 1). Nagini
is a partial-correctness verifier by default, so without these obligations an
implementation that diverges before answering would satisfy every value
postcondition vacuously while its faithful real patch hangs the printer. The
real operations always return, so the obligation is faithful, not a
strengthening beyond reality.

## Carrier refinement (applies throughout)

All "binding strengths" (precedence values) are modelled as Python `int`. In the
real code they are entries of the `PRECEDENCE` dict (ints: Add=40, Mul=50,
Pow=60, Func=70) and one derived threshold `0.5*(PRECEDENCE["Pow"] +
PRECEDENCE["Mul"])` which is the Python `float` `55.0`. The model uses the
integer midpoint `(60 + 50)//2 == 55`.

| repo reality | model carrier | bijection |
|---|---|---|
| `PRECEDENCE["Add"/"Mul"/"Pow"/"Func"]` (int) | `level_additive/level_multiplicative/level_power/level_function()` | identical integer constants 40/50/60/70 |
| `0.5*(PRECEDENCE["Pow"]+PRECEDENCE["Mul"])` = `55.0` (float) | `leading_minus_cutoff()` = `(level_power()+level_multiplicative())//2` = `55` (int) | **R**: exact. `Pow+Mul = 110` is even, so the integer midpoint equals the float midpoint, and the only use of the value is the comparison `precedence(item) <(=) threshold` against integer-valued precedences — every comparison outcome is identical under `float 55.0` and `int 55`. The tested behaviour is precision-independent, so an integer carrier is faithful (no `--float-encoding` needed). |
| `precedence(item)` (the dispatcher) | the operand's integer strength passed as `factor_strength` / read off the constant pure fns | **R**: the dispatcher returns the relevant `PRECEDENCE`/`PRECEDENCE_VALUES` entry; the model names that entry directly. |

## A. The precedence site — `precedence.py` `PRECEDENCE_VALUES`

Gold hunk (`sympy/printing/precedence.py`, in the `PRECEDENCE_VALUES` dict):
```
     "MatrixSolve": PRECEDENCE["Mul"],
+    "Mod": PRECEDENCE["Mul"],
     "TensAdd": PRECEDENCE["Add"],
```

| # | model.py op (`remainder_operand_level`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `return level_multiplicative()` | the new dict entry `"Mod": PRECEDENCE["Mul"]` makes `precedence(Mod(...))` return `PRECEDENCE["Mul"]` | A-reference | the changed value IS modelled deeply (the model states `Result()==level_multiplicative()`); G-AX (axiom_check.py) runs the real `precedence(Mod(x,y))` and asserts it equals `PRECEDENCE["Mul"]` (== `level_multiplicative()`). Pre-patch there is no `"Mod"` entry, so the dispatcher walks the MRO to `Function` and returns `PRECEDENCE["Func"]` (70); `model_prepatch_2.py` reproduces that (`level_function()`) and FAILS the postcondition `Result()==level_multiplicative()`. |

## B. The single-factor leading-minus site — `codeprinter.py` `_print_Mul`

Gold hunk (`sympy/printing/codeprinter.py`):
```
-        a_str = [self.parenthesize(x, prec) for x in a]
+        if len(a) == 1 and sign == "-":
+            ...                       # comment: unary minus binds between Mul and Pow
+            a_str = [self.parenthesize(a[0], 0.5*(PRECEDENCE["Pow"]+PRECEDENCE["Mul"]))]
+        else:
+            a_str = [self.parenthesize(x, prec) for x in a]
```
plus the import `from sympy.printing.precedence import precedence, PRECEDENCE`.

The model abstracts the `len(a)==1 and sign=="-"` branch: `negated_single_operand_enclosed(operand_level)` is exactly the wrap/bare decision the printer makes for that single factor `a[0]`. (The `else` branch and the multi-factor / non-negative cases are unchanged by the patch and are not modelled — they are outside the changed behaviour.)

| # | model.py op (`negated_single_operand_enclosed`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | the level chosen is `leading_minus_cutoff()`, pinned `level_multiplicative() < · < level_power()` | `0.5*(PRECEDENCE["Pow"]+PRECEDENCE["Mul"])` | A-reference + R | the threshold is modelled deeply as the integer midpoint; G-AX asserts the real float threshold `55.0` is strictly between Mul and Pow and equals the model midpoint (carrier R above). |
| B2 | `encloses(operand_level, level, False)` | `self.parenthesize(a[0], level)` with default `strict=False` | A-reference | `parenthesize(item, level, strict=False)` returns the wrapped form iff `precedence(item) < level or precedence(item) <= level`, i.e. `precedence(item) <= level`; `encloses(s, t, False)` is exactly that predicate. The deep model of `parenthesize` is validated == the real `parenthesize` output structurally (presence of wrapping parens) by G-AX on one operand per strength class (remainder 50, product 50, power 60, function 70). |
| B3 | `operand_level` is the operand's own re-binding level (parameter) | `precedence(a[0])` | R | the dispatcher's value for the single factor; G-AX reads the real `precedence(item)` for each tested operand and feeds the same value into the model decision (no double-mask — the wrap decision is asserted at the structural paren-presence level, not via a value proxy). |

The discriminating content of this hunk: a single negated factor of
multiplication-level strength (50) must be wrapped because the unary-minus
threshold (55) exceeds 50. Pre-patch the level was `prec` = `precedence(expr)`,
which for a negative-coefficient `Mul` collapses to `PRECEDENCE["Add"]` (40) via
`precedence_Mul`/`_coeff_isneg`; `model_prepatch.py` reproduces that
(`encloses(operand_level, level_additive(), False)`) and FAILS the postcondition
`Result()==encloses(operand_level, leading_minus_cutoff(), False)` (and the
"level <= Mul ⇒ enclosed" consequence) — exactly the spec sensing the change
(G-DIFF, confirmed: model_prepatch.py fails at this postcondition).

## C. The composite illustration — `negated_remainder_is_enclosed`

`negated_remainder_is_enclosed()` is a *worked instance* that composes both
modelled obligations on the negated remainder operand `-Mod(x,y)`: its impl
`negated_single_operand_enclosed(remainder_operand_level())` calls both modelled
functions (under spec, not as axioms — §3 of SPEC_GUIDE) and its result is the
concrete `True` consequence the `-(x % y)` F2P observation demands.

**Discrimination note (corrected per panel DEFECT 2).** This composite is NOT
the locus of differential sensing, and its `Ensures(Result()==True)` is not
load-bearing. Because Nagini forbids calling a non-`@Pure` (contracted) function
inside an `Ensures`, the composite's postcondition cannot be strengthened to
`Result()==negated_single_operand_enclosed(remainder_operand_level())` (that
triggers `purity.violated`); a strengthening to a pure mirror would add nothing,
since a bare `return True` already satisfies it. So the composite is kept as an
illustration and the discrimination lives entirely in the two STANDALONE
functions, each carrying its own discriminating postcondition:

  * `remainder_operand_level` — `Ensures(Result()==level_multiplicative())`;
    `model_prepatch_2.py` (remainder level reverted to Func=70) FAILS **at this
    function's own postcondition** (confirmed: error at `remainder_operand_level`).
  * `negated_single_operand_enclosed` — `Ensures(Result()==encloses(operand_
    level, leading_minus_cutoff(), False))` plus the `<=Mul ⇒ enclosed`
    consequence; `model_prepatch.py` (cut-off reverted to Add=40) FAILS **at this
    function's own postcondition** (confirmed: error at
    `negated_single_operand_enclosed`).

Each prepatch variant is sensed by the standalone function it reverts, not by
the composite. Both variants exist because the gold fixes two independent sites
and each must be sensed independently (G-DIFF).

| # | model.py op | patch.diff op | tag | justification |
|---|---|---|---|---|
| C1 | `s = remainder_operand_level()` | `precedence(Mod(x,y))` | A-reference | site A (discriminated by `remainder_operand_level`'s own postcondition) |
| C2 | `negated_single_operand_enclosed(s)` | the `_print_Mul` single-factor branch on `a[0]==Mod(x,y)` | A-reference | site B (discriminated by `negated_single_operand_enclosed`'s own postcondition) |
| C3 | `Ensures(Result()==True)` | the F2P observation `pycode(-Mod(x,y)) == '-(x % y)'` | I | the concrete `True` consequence the F2P test demands; illustrative, not the discriminator (see note above) |

## D. No kind-3 (unexpressible-changed-op) steps

Every step is R, A-reference, or I. The two operations that genuinely *changed*
— the remainder node's precedence value and the single-factor leading-minus
parenthesization threshold — are modelled **deeply** (spelled-out integer
constants and the `encloses`/`leading_minus_cutoff` predicate), NOT hidden behind
an axiom about the function under change. There is **no consumed `@ContractOnly`
axiom** (the `axioms` region is empty); both deep models are **A-references**
that G-AX validates against the real `precedence` table and real `parenthesize`
predicate. No A-consumed rows exist.

## E. verify(model) ⇒ resolved

`remainder_operand_level` verifies only if it returns the Mul strength (site
A); `negated_single_operand_enclosed` verifies only if it wraps exactly the
operands whose strength is at most the unary-minus threshold strictly above Mul
(site B); `negated_remainder_is_enclosed` verifies only if both hold so a negated
remainder operand is wrapped. By the carrier R (int ↔ PRECEDENCE entries; int
midpoint ↔ float `55.0`, exact) and G-AX (the real `precedence(Mod)` == Mul and
the real `parenthesize` wraps iff `precedence(item) <= 55.0`), the verified model
is the gold patch up to type refinement and audited callees. The gold patch
resolves (G-RESOLVE). Trust points are exactly PLAN §1.1: axiom/callee soundness
(G-AX, two A-references) and refinement fidelity (this document, G-EQ).
