# mapping.md — astropy__astropy-14369

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = fa4e8d1cd279acf9b24560813c8652494ccd5922`, states the type
abstraction, and gives the provenance of the deep-model reference (the
A-reference validated by G-AX).

Repo file under change: `astropy/units/format/cds.py` (plus the regenerated
LALR parse table `astropy/units/format/cds_parsetab.py`).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reduceDivisionChain (n)` | the CDS division-chain reduction: rule `division_of_units` + action `p_division_of_units` — `astropy/units/format/cds.py:181-190` (rule string, body) | the modeled changed behaviour: the exponent each operand of a `u/u/.../u` chain receives |
| `chainPower (i)` *(deep model — A-reference)* | the post-patch left-grouped reduction `combined_units DIVISION unit_expression`, `p[0] = p[1] / p[3]` — `astropy/units/format/cds.py:184` (post-patch) | pure spec: exponent of operand `i` in a left-grouped division chain (+1 for the head, -1 for the rest); validated `==` the real patched parser by axiom_check.py (G-AX), NOT a consumed axiom |
| `expVec (n)` / `expVecFrom b m` | the per-operand exponent vector the parsed composite unit denotes | the assembled deep model: `expVec n` = `[chainPower 0, …, chainPower (n-1)]` |

Pre-patch repo construct the change replaces (for the refinement audit, not
referenced from the consumer spec view): the right-recursive alternative
`unit_expression DIVISION combined_units` (`cds.py` pre-patch), under which `p[3]`
is the recursively parsed remainder of the chain — division nesting to the right,
alternating the operand signs.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a chain of `UnitBase` operands `u(0)/u(1)/.../u(n-1)` parsed by the CDS grammar | a count `n : Nat` of operand positions | only operand *position* (not identity) determines the exponent the grouping assigns; position `i` ↔ the i-th `unit_expression` leaf, left to right |
| the parsed composite `UnitBase` (a product of `base**power` factors) | `List Int` of integer exponents, one per operand position (`expVec n`) | `(expVec n)[i]` ↔ the integer power of operand `u(i)` in the parsed unit; the F2P tests compare exactly these powers (e.g. `km/s/Mpc == u.km/u.s/u.Mpc`) |
| `UnitBase.__truediv__` / `__pow__(-1)` (the `p[1] / p[3]` and `p[2] ** -1` actions) | integer exponent arithmetic (negate on division) | division of units adds the exponent vectors with the divisor negated; on a chain of *distinct* operands this reduces to per-position ±1, which is what the tests and the issue exercise |

Rich `UnitBase` objects and `str` parsing are outside the modeled fragment, so
the carrier is `Nat` (operand count) → `List Int` (exponent vector).

Scope note: the model pins the **exponent-vector** behaviour (the observable in
the issue and in F2P `test_cds_grammar[strings4]`, `[strings6]`). The same single
grammar-rule change also flips one parser-acceptance decision (`km/s.Mpc-1`
becomes a syntax error, F2P `test_cds_grammar_fail[km/s.Mpc-1]`); that LALR-table
acceptance effect is not modeled deeply (it is a property of the generated parse
table, not of the exponent algebra) and is carried by `patch.diff` == gold
(G-RESOLVE). The deep model captures the primary observable the issue describes.

## 3. Deep-model reference provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `chainPower` deep model ↔ the real patched CDS parser (A-reference)

**Callee:** the post-patch `astropy.units.Unit(<chain>, format='cds')` parser,
built from the corrected grammar
`division_of_units : combined_units DIVISION unit_expression` with action
`p[0] = p[1] / p[3]` (`astropy/units/format/cds.py:181-190`, post-patch; LALR
table `cds_parsetab.py`). The changed reduction is modelled **deeply** by the
pure function `chainPower` (Solution.lean pure region); there is **no consumed
axiom**.

Left grouping `(((u0/u1)/u2)/.../u(n-1))` means the head keeps power +1 and each
subsequent operand is divided in exactly once, receiving power -1 — independent
of its depth. This is precisely `chainPower i = +1 if i==0 else -1`.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL patched parser on:
the F2P/issue chains (`km/s/Mpc`, `J/m/s/kpc`, `s`, `km/s`, `J/s/kpc`); ALL
distinct-operand chains of length 1..5 over a 5-unit alphabet (every operand
position observed directly, no masking); and 4000 randomised fuzz chains of
length 1..8 over a 12-unit pool. For each chain it extracts the parsed unit's
exponent **per operand position** and asserts it equals `chainPower` at every
index (the index-level equivalence the model decides — SPEC_GUIDE directive 7,
no double-mask). It imports only the standard library and `astropy.units` (the
very package the patch edits). Docs / standard the behaviour follows: the CDS
"Standards for Astronomical Catalogues 2.0"
(http://vizier.u-strasbg.fr/doc/catstd-3.2.htx), under which composite SI units
such as `10+3J/m/s/kpc2` denote `J·m^-1·s^-1·kpc2^-1`.
