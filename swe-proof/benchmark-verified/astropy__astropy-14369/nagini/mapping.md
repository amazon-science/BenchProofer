# mapping.md — astropy__astropy-14369

Binds every `model.py` symbol to its repository counterpart at
`base_commit = fa4e8d1cd279acf9b24560813c8652494ccd5922`, states the type
abstraction, and gives the provenance of the deep-model reference (the A-reference
validated by G-AX).

Repo file under change: `astropy/units/format/cds.py` (plus the regenerated
LALR parse table `astropy/units/format/cds_parsetab.py`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reduce_division_chain(powers, leading)` | the CDS division-chain reduction: rule `division_of_units` + action `p_division_of_units` — `astropy/units/format/cds.py:182-190` (rule string lines 183-185, body lines 187-190) — **both** productions: `DIVISION unit_expression` (body line 188-189, `p[0] = p[2] ** -1`) and the chain production (body line 190, `p[0] = p[1] / p[3]`) | the modeled changed behaviour: the exponent each operand of a `u/u/.../u` chain receives, with or without a leading `/` |
| `chain_power(i, power, leading)` *(deep model — A-reference)* | the post-patch left-grouped reduction `combined_units DIVISION unit_expression`, `p[0] = p[1] / p[3]` — `astropy/units/format/cds.py:185,190` (post-patch) — together with the leading-`/` base case `DIVISION unit_expression`, `p[0] = p[2] ** -1` (`cds.py:184,188-189`, unchanged by the patch) | pure spec: exponent of the operand at position `i` whose OWN intrinsic exponent is `power`, in a left-grouped division chain: it keeps `power` iff `i == 0` and the chain does not open with `/`, and receives `-power` otherwise; validated `==` the real patched parser by axiom_check.py (G-AX), NOT a consumed axiom |

Note on the operand granularity: one `unit_expression` leaf may itself carry a
numeric power (`unit_with_power : UNIT numeric_power`, `p[0] = p[1] ** p[2]` —
`cds.py:230-236`), so `kpc2` is ONE operand of intrinsic exponent 2, not two
operands. The model carries that intrinsic exponent per position (`powers[i]`)
rather than assuming it is 1, which is why the exponent it predicts for the
issue's `10+3J/m/s/kpc2` is `kpc^-2` and not `kpc^-1`.

Pre-patch repo construct the change replaces (for the refinement audit, not
referenced from the consumer spec view): the right-recursive alternative
`unit_expression DIVISION combined_units` (`cds.py:185` pre-patch), under which
`p[3]` is the recursively parsed remainder of the chain — division nesting to
the right, alternating the operand signs.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a chain of `unit_expression` operands `u(0)/u(1)/.../u(n-1)` parsed by the CDS grammar, each operand being a base raised to its own numeric power | `powers: List[int]` — the i-th element is the INTRINSIC exponent of the i-th `unit_expression` leaf, left to right | operand *position* together with that operand's own intrinsic exponent determines the exponent the grouping assigns; operand *identity* (which base it is) does not, so it is not carried |
| whether the chain opens with the division operator (`division_of_units : DIVISION unit_expression` heads the parse) | `leading: bool` | `leading` is `True` exactly when the surface begins with `/`; that production negates its operand (`p[2] ** -1`), so there is no positive head |
| the parsed composite `UnitBase` (a product of `base**power` factors) | `List[int]` of integer exponents, one per operand position | `Result()[i]` ↔ the integer power operand `u(i)` contributes to the parsed unit. When several positions share a base the parser reports their SUM for that base, and the vector determines it; on all-distinct-base chains each position is read off directly. The F2P tests compare exactly these powers (e.g. `km/s/Mpc == u.km/u.s/u.Mpc`, `10+3J/m/s/kpc2 == 1e3*u.W/(u.m*u.kpc**2)`) |
| `UnitBase.__truediv__` / `__pow__(-1)` (the `p[1] / p[3]` and `p[2] ** -1` actions) | integer exponent arithmetic (negate on division) | division of units adds the exponent vectors with the divisor negated; under LEFT grouping every operand after the head is divided in exactly once, so its own exponent is negated exactly once — per position `+powers[i]` for a non-leading head, `-powers[i]` otherwise. This is stated over the FULL admitted domain: operands may repeat a base, may carry any intrinsic exponent, and the chain may open with `/`. |

Rich `UnitBase` objects and `str` parsing are banned/inexpressible in Nagini, so
the carrier is `List[int]`; the specification is phrased over `PSeq[int]` via
`ToSeq`.

Scope note: the model pins the **exponent-vector** behaviour (the observable in
the issue and in F2P `test_cds_grammar[strings4]`, `[strings6]`) over the whole
domain its precondition admits — operands at any intrinsic exponent, bases free
to repeat, and the leading-`/` form all included, each exercised by G-AX and
G-CONF. The same single grammar-rule change also flips one parser-acceptance
decision (`km/s.Mpc-1` becomes a syntax error, F2P
`test_cds_grammar_fail[km/s.Mpc-1]`); that LALR-table acceptance effect is not
modeled deeply (it is a property of the generated parse table, not of the
exponent algebra) and is carried by `patch.diff` == gold (G-RESOLVE). The deep
model captures the primary observable the issue describes.

Note on well-definedness of the abstraction: the carrier includes `leading`
precisely so the map to the real callee is a FUNCTION. Without it a single model
point (arity 1, leaf `s`) would have two real realizations — `s` → `[+1]` and
`/s` → `[-1]` — and no single prediction could match both. With `leading` in the
carrier those are two distinct model points, each with one real image.

## 3. Deep-model reference provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `chain_power` deep model ↔ the real patched CDS parser (A-reference)

**Callee:** the post-patch `astropy.units.Unit(<chain>, format='cds')` parser,
built from the corrected grammar
`division_of_units : combined_units DIVISION unit_expression` with action
`p[0] = p[1] / p[3]` (`astropy/units/format/cds.py:182-190`, post-patch; LALR
table `cds_parsetab.py`). The changed reduction is modelled **deeply** by the
`@Pure` function `chain_power` (model.py pure region); there is **no consumed
`@ContractOnly` axiom**.

Left grouping `(((u0/u1)/u2)/.../u(n-1))` means the head keeps its own exponent
and each subsequent operand is divided in exactly once, so its own exponent is
negated exactly once — independent of its depth. When the chain instead opens
with `/`, the `DIVISION unit_expression` base case (`p[0] = p[2] ** -1`) negates
the first operand too, so there is no positive head. This is precisely
`chain_power(i, power, leading) = power if (i == 0 and not leading) else -power`.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL patched parser on:
the F2P/issue chains, including the powered-operand (`J/m/s/kpc2`, `m2/s`,
`km/s2`, `km/s/Mpc2`, `kpc-2/s`, `m10/s`) and leading-operator (`/s`, `/km/s`,
`/km/s/Mpc`) forms; ALL distinct-base chains of length 1..4 over a 5-operand
alphabet of POWERED operands, with and without the leading operator (every
operand position observed directly, no masking); ALL repeated-base chains of
length 1..4 over a 3-operand alphabet that reuses bases at different intrinsic
exponents, under the per-base summing bridge; and 4000 randomised fuzz chains
of length 1..8 over a 12-base × 7-exponent operand pool with both leading
settings and bases free to repeat. For each chain it extracts the parsed unit's
exponent **per operand position** (or, when bases repeat, per base against the
model's positional sum) and asserts it equals `chain_power` at every index (the
index-level equivalence the model decides — SPEC_GUIDE directive 7, no
double-mask). Verified in the official instance image with the gold patch
applied: **4663 chains, 0 mismatches, exit 0**; run against the *pre-patch*
parser in the same image it correctly FAILS (first mismatch `km/s/Mpc` got
`[1,-1,1]` want `[1,-1,-1]`), so the check discriminates rather than merely
passing. It imports only the standard library and `astropy.units` (the very
package the patch edits). Docs / standard the behaviour follows: the CDS
"Standards for Astronomical Catalogues 2.0"
(http://vizier.u-strasbg.fr/doc/catstd-3.2.htx), under which composite SI units
such as `10+3J/m/s/kpc2` denote `J·m^-1·s^-1·kpc^-2` — the trailing operand's
own exponent 2 is preserved under the division, which is exactly what the F2P
expectation `u.Unit(1e3*u.W/(u.m*u.kpc**2))` asserts.
