# refinement.md — sympy__sympy-15349

The operation-by-operation correspondence between `model.py`'s implementation
(the `rotation_matrix` and `rotation_matrix_affine` impl regions) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed** / **A-reference**), or
**I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

There are seven `@ContractOnly` declarations in this bundle, and they are the
CONSTRUCTORS of the carrier. They **assert nothing**: no `Ensures`, no algebraic
law, no ordering, no numeric content (`meta.json axioms`, all seven with an empty
`assumes`). So there is **no A-consumed step and no axiom trust point** — a
declaration with no postcondition supplies a proof with nothing to lean on.
What the map below does rely on are R-legs and A-reference facts about the real
callee, and each of those is confirmed against it in `axiom_check.py` /
`conformance_check.py`.

## A0. The carrier: the EXPRESSIONS of the computation

The components, the common scale and the matrix entries are not modelled as
numbers. They are modelled as what they are in the repository — **expressions** —
and the model carries that directly: `Scalar` is an opaque type, its only
inhabitants are the ones the seven constructors build, and those seven
constructors name everything this computation does with its inputs.

| constructor | repository counterpart | |
|---|---|---|
| `zero()` | `Integer(0)` (the literal `0` of the trailing affine row) | R-ops |
| `one()` | `Integer(1)` (the literal `1` of `1 - 2*s*(...)` and the affine corner) | R-ops |
| `two()` | `Integer(2)` (the literal `2` of `2*s*(...)`) | R-ops |
| `add(u, v)` | `u + v` on `Expr` | R-ops |
| `sub(u, v)` | `u - v` on `Expr` | R-ops |
| `mul(u, v)` | `u * v` on `Expr` | R-ops |
| `sq(u)` | `u ** 2` on `Expr` | R-ops |

The three constants are **nullary**, and that is the whole of their content: the
source writes exactly three integer literals, so three nullary constants name them
exactly, and the model's interface then mentions no sort but `Scalar`. `Scalar` is
therefore not merely the carrier of the entries but the ONLY sort this behaviour
computes with — no number is an argument, an operand or a result anywhere in it.
See A0-1sort.

So a modelled term denotes the expression built by the same sequence of
operations on the same operands, and

    model term at index k   =   the expression the source builds for entry k

with nothing in between. Each `Ensures` mirrors one source line. Six
consequences are used throughout.

* **(R-ops)** each of the seven constructors has exactly one counterpart above,
  and the counterpart is total and exact: applying it to the counterparts of the
  operands builds the counterpart of the term. Exhibited on symbolic operands in
  `axiom_check.py` (`check_constructor_bridge`).
* **(R-cong)** the ONLY identification this carrier proves is congruence — the
  same constructor applied to the same operands is the same scalar — and
  congruence holds of the repository's expressions: combining the same parts the
  same way twice builds the same expression. This is the leg that makes a proof
  carried out over the carrier transfer, and it is checked symbolically in
  `axiom_check.py` (`check_congruence_and_strictness`, R-cong).
* **(R-finer)** the converse leg, and the one that fixes the DIRECTION of the
  refinement. The repository's equality on expressions identifies strictly MORE
  than the carrier's sameness does: it flattens and orders sums and products and
  collapses a repeated factor to a power, so `mul(c, c)` and `sq(c)`, or
  `mul(b, c)` and `mul(c, b)`, are distinct scalars that the repository calls
  equal. The carrier therefore only ever distinguishes where the repository does
  not, and the model is the STRICTER of the two — never the laxer. A spec clause
  the source satisfies is a clause the carrier's sameness also satisfies where it
  matters (the source's entries are built by the very constructor sequence the
  clause names, checked as an identity of expression trees below), while a
  realisation the carrier admits cannot be one the repository separates.
  Exhibited in `axiom_check.py` (R-finer).
* **(R-layout)** `Matrix[i, j]` ↔ `Result()[i*ncols + j]` (`ncols` = 3 resp. 4),
  with no factor in between; `Matrix` equality ↔ element-wise list equality. The
  `Matrix(...)` constructor stores the entries it is given and is row-major
  (A-reference; `axiom_check.py`).
* **(R-vocab)** the seven constructors are the WHOLE vocabulary of the carrier.
  There is no division, no remainder, no rounding and no order on `Scalar`: an
  operation of that kind is not merely refutable here, it cannot be written down
  — a realisation reaching for one does not translate (measured: `//` on
  `Scalar` is a type error, `<` on `Scalar` is a type error). And the relations
  that ARE writable in Python on any value — `==`, `!=`, `is`, `is not` — are
  UNDECIDED between differently-built terms on this carrier, in both directions.
  A realisation that decides an entry on such a relation must therefore satisfy
  the entry clauses on BOTH sides of it. This is the leg the two earlier carriers
  failed, and A0-note records how.

  The relations are not the whole of what Python lets a realisation branch on,
  and the rest of it has to be covered here explicitly rather than left to that
  enumeration. Any value in Python also has a TRUTH VALUE, obtained without
  naming an operation at all, and the repository DECIDES it: its scalars are
  `Expr`, `Expr` defines `__bool__`, and the counterpart R-ops assigns to
  `zero()` is `Integer(0)`, which that method makes falsy, while an ordinary
  object reference is truthy. A carrier that left the truth value of a scalar
  decided would therefore have branched-on truthiness dead in the proof and live
  in the repository on every input — the guarded-branch family again, at the
  load-bearing entry. So `Scalar` DECLARES `__bool__` and assumes nothing about
  it, exactly as the seven constructors assume nothing: no scalar is provably
  true, none is provably false, and a realisation deciding an entry on the truth
  value of a scalar carries the entry clauses on BOTH sides of that decision,
  just as for `==` and `is`. Measured: the rival that overwrites the
  load-bearing entry behind `if not zero():` is REFUTED at `Result()[5]` and
  `Result()[6]`, and the branch is LIVE rather than merely unentered (the same
  rival with `Assert(False)` first inside it is refuted too), so the rejection is
  not vacuous. `properties.py` carries the family as
  `rej-truthiness-guard-3x3`, `rej-truthiness-guard-argument` and
  `rej-truthiness-guard-built-term`.

  What is left over is REFLECTION rather than computation — `type(u) is type(v)`,
  `str(u)`, `hash(u)`, `id(u)`. `type` is not a constructor and a type object is
  not a scalar, so no such expression has a counterpart on this carrier, and the
  verifier's reading of it is not Python's (it models `type(u)` as a fresh
  object, so `type(u) is type(u)` is provably FALSE here and True there). That
  puts it in the number-sort position rather than the relation position: it is
  governed by R-1sort's translate-by-MEANING rule (mapping.md), which is the only
  thing that can govern it, since a branch the verifier proves dead admits no
  refuting postcondition at all.
* **(R-1sort)** `Scalar` is the whole carrier and the only sort the modelled
  behaviour computes with. Whole numbers occur in the model only as POSITIONS in
  the result and as its LENGTH — the shape of the matrix, fixed at nine and
  sixteen — and no arithmetic is performed on those. Both impl regions are
  straight-line constructor cascades with no number-valued arithmetic in them at
  all, machine-checked in `conformance_check.py` (`check_no_number_sort`: no `//`,
  no `%`, no real literal, no `int(`/`float(` in either region). A0-1sort states
  the rule this fixes for translating an expression the model has no sort for.

**A0-note (why the carrier is neither ℤ nor a field).** The carrier is the
substance of this model rather than a technicality, because two earlier choices
of it each admitted a realisation that verifies and does not resolve, for two
different reasons.

* **Not ℤ.** The entries of this matrix are in general not integers — `2/3` for
  the `(1,2)` entry of `Quaternion(1, 2, 3, 4)`, and `-sin(x)` at the symbolic
  X-rotation witness, which has no integer part to take. On a carrier of
  integers the ℤ-specific total operations `//` and `%` are available and
  expressions such as `(3*k)//3` and `k - k % 1` are identities at every
  integer, so a realisation using one of them satisfies every entry equation and
  verifies while denoting a rounding step the repository does not perform.
  Separately, `0 < s < 1` — which is precisely the ordinary case, the scale being
  a reciprocal — has no integer solution, so a realisation may branch on it and
  do as it likes on the branch reality actually takes. `properties.py` carries
  `rej-truncate-3x3`, which on the present carrier does not translate at all.
* **Not a field either, and this is the point.** Moving to an ordered field of
  characteristic zero removes `//` and `%` and makes the scale condition
  satisfiable, but it ADDS two things the repository's scalars do not have: a
  semantic equality and a decidable order. Over any field the condition
  `(a + d)*(a + d) != a*a + 2*a*d + d*d` is unsatisfiable, so a realisation that
  decides an entry on it verifies with the guarded branch unreachable — while the
  repository's equality on expressions is an equality of EXPRESSIONS, under which
  those two sides are distinct, so the guarded branch is the one the real code
  takes on every input, at every entry. The same holds of any polynomial
  identity — `(a+d)*(a-d)` against `a*a - d*d`, `(a²+d²)²` against
  `a⁴+2a²d²+d⁴` — and of the order relation, which is not decidable on the
  repository's scalars at all. No strengthening of the entry equations reaches
  such a realisation, because it violates none of them: the carrier is what has
  to change. No carrier of VALUES can close this family, since the family is
  generated by equations that are true of values and false of expressions.
* **Hence expressions.** On the present carrier those two sides are distinct
  terms, no identification between them is provable and no separation between
  them is provable either, both branches are reachable, and the entry clause is
  refuted on the guarded one. The rivals are carried in `properties.py`
  (`rej-identity-guard-3x3`, `rej-identity-guard-m01`, `rej-order-guard-3x3`,
  `rej-identity-guard-affine-m03`), and `axiom_check.py` exhibits the fact they
  rest on: pairs of differently-built expressions that agree at every number and
  are distinct in the repository, with the guard condition evaluating to `True`
  there.

**A0-1sort (the one-sort rule, and the meaning of a numeric expression).** The
model's LANGUAGE has whole numbers and reals even though the modelled behaviour
has no sort for them, so a realisation can compute with them. What such a
computation MEANS under this map has to be stated, because the model's language
and the repository's language do not agree about it:

| closed expression | this model's language, as the verifier reads it | the repository's language |
|---|---|---|
| `7 // -2` | `-3` (division truncates toward zero) | `-4` (floor) |
| `7 % -2` | `1` (sign of the dividend) | `-1` (sign of the divisor) |
| `0.1 + 0.2 == 0.3` | true (the verifier's reals are exact) | false (binary approximation) |

Both halves are measured rather than asserted: the repository's readings in
`conformance_check.py` (`check_no_number_sort`), the verifier's in the model
itself — a realisation guarding a load-bearing entry on `7 // -2 == -3` is
REFUTED, which is only possible if the verifier proves that guard true.

The rule, stated in full in `mapping.md` §2 (R-1sort), is that **a refinement
preserves MEANING, not text**: the image of a model expression is the repository
expression denoting what the model expression denotes — for a carrier term the
R-ops counterpart, term for term, and for a closed numeric expression the VALUE
the verifier proves it has. Transcribing the characters `7 // -2` into the
repository is therefore not that expression's image, since those characters denote
something else there; and a branch the proof discharged as unreachable is
unreachable in the realisation, because a guard on a closed expression has the
same truth value on both sides of the map once the expression is mapped by
meaning.

This is where the document, not the machine, carries `verify ⇒ correct`, and it is
worth being plain about why no clause could carry it instead. The rival the rule
answers is the gold cascade wrapped in `if 7 // -2 == -4: <pre-change entry>`.
Under the verifier's semantics that guard is FALSE, so the rival's impl region and
the gold impl region are the SAME computation in every state any specification
quantifies over — so a specification the gold impl satisfies is one that rival
satisfies, no matter what the specification says. The construction is available
against every specification of every behaviour in any language whose closed
arithmetic the verifier decides; it is a fact about the two languages, not about
this behaviour, and there is no clause it violates for a stronger clause to catch.
What it violates is the refinement, by mapping a model expression denoting `-3` to
a repository expression denoting `-4`. `properties.py` deliberately carries no
reject case of this family, and the comment above `rej-identity-guard-3x3` records
the reason: one direction verifies (so it cannot honestly be listed as rejected,
and no model closes it), and the other direction is refuted but WOULD resolve, so
booking its rejection as a win would credit this spec with strength it lacks.

## A. The changed method — `Quaternion.to_rotation_matrix` (`sympy/algebras/quaternion.py:489`)

Gold hunk (the single edited line, `quaternion.py:532`):
```
- m12 = 2*s*(q.c*q.d + q.b*q.a)
+ m12 = 2*s*(q.c*q.d - q.b*q.a)
```

### A.1 the 3×3 branch (`if not v:` → `model.rotation_matrix`)

| # | model.py impl op | patch.diff / source op | tag | justification |
|---|---|---|---|---|
| A1 | params `a, b, c, d: Scalar` | `q.a, q.b, q.c, q.d` (SymPy `Expr`) | R | A0: the model's scalars ARE the repository's expressions, component for component. No precondition restricts them, so each ranges over every expression the behaviour is realised at — indeterminates and trigonometric values of the angle included. |
| A2 | param `s: Scalar` | `s = q.norm()**-2` | R | the identity on expressions: the modelled scale IS the expression the source computes, with no reciprocal or rescaling in between. The patch does not touch the scale and `norm` is NOT axiomatized: what the refinement needs of it is only that the realised `s` is the expression `q.norm()**-2`, and both `conformance_check.py` and `axiom_check.py` obtain it from that very call rather than re-deriving it (`norm` applies `trigsimp`, so the realised scale of a trigonometric quaternion is the exact scalar 1). |
| A3 | `m00 = sub(one(), mul(mul(two(), s), add(sq(c), sq(d))))` | `m00 = 1 - 2*s*(q.c**2 + q.d**2)` | R | the same term under R-ops, constructor for operation and in the same association. |
| A4 | `m01 = mul(mul(two(), s), sub(mul(b, c), mul(d, a)))` | `m01 = 2*s*(q.b*q.c - q.d*q.a)` | R | as A3. |
| A5 | `m02 = mul(mul(two(), s), add(mul(b, d), mul(c, a)))` | `m02 = 2*s*(q.b*q.d + q.c*q.a)` | R | as A3. |
| A6 | `m10 = mul(mul(two(), s), add(mul(b, c), mul(d, a)))` | `m10 = 2*s*(q.b*q.c + q.d*q.a)` | R | as A3. |
| A7 | `m11 = sub(one(), mul(mul(two(), s), add(sq(b), sq(d))))` | `m11 = 1 - 2*s*(q.b**2 + q.d**2)` | R | as A3. |
| **A8** | `m12 = mul(mul(two(), s), sub(mul(c, d), mul(b, a)))` | `m12 = 2*s*(q.c*q.d - q.b*q.a)` (the **patched** line) | R | **the corrected line**, mirrored term for term. The spec pins `Result()[5] is off_cd_minus = 2s(cd − ba)`, which under R-ops holds only of the source entry `2*s*(q.c*q.d - q.b*q.a)`. |
| A9 | `m20 = mul(mul(two(), s), sub(mul(b, d), mul(c, a)))` | `m20 = 2*s*(q.b*q.d - q.c*q.a)` | R | as A3. |
| A10 | `m21 = mul(mul(two(), s), add(mul(c, d), mul(b, a)))` | `m21 = 2*s*(q.c*q.d + q.b*q.a)` | R | as A3; note this entry keeps the `+ b·a` sign — the two `(cd)` off-diagonals are opposite. |
| A11 | `m22 = sub(one(), mul(mul(two(), s), add(sq(b), sq(c))))` | `m22 = 1 - 2*s*(q.b**2 + q.c**2)` | R | as A3. |
| A12 | `result = [m00,…,m22]` (row-major) | `Matrix([[m00,m01,m02],[m10,m11,m12],[m20,m21,m22]])` | R | R-layout; `axiom_check.py` checks `Matrix[i,j]` against the model term on rational, integral and fully symbolic quaternions, and on the symbolic ones as an identity of expression TREES (`srepr`). |

Note on `q.c**2` versus `mul(c, c)`: the model writes `sq(c)`, whose counterpart
is `c ** 2` — the operation the source actually performs. `mul(c, c)` is a
DIFFERENT scalar here (the repository identifies the two; R-finer), so the map
does not have to pretend they are the same one, and the impl mirrors the source's
choice of operation rather than an equivalent of it.

### A.2 the 4×4 branch (`else:` → `model.rotation_matrix_affine`)

| # | model.py impl op | source op | tag | justification |
|---|---|---|---|---|
| B1–B11 | the same nine core entries `m00…m22` | `quaternion.py:526–536` (shared block) | R | identical to A3–A12; the SAME `m12` line is reused, so the corrected sign also flows here. |
| **B12** | `m13 = sub(sub(sub(y, mul(x, m10)), mul(y, m11)), mul(z, m12))` (with `m12` as A8) | `m13 = y - x*m10 - y*m11 - z*m12` (`quaternion.py:545`) | R | the identical line under R-ops, in the source's own left association. Inherits the corrected `m12`, and the spec pins `Result()[7]` to that term via `translation(y, …, off_cd_minus(…))`. |
| B13 | `m03`, `m23`, `m30..m32 = zero()`, `m33 = one()` | `m03/m23/m30..m33` (`quaternion.py:544,546,547,548`) | R | as B12 for the two other translation entries; the source's trailing row is `(0,0,0,1)`, and `zero()`/`one()` name the integer literals it writes. |
| B14 | `result = [m00,…,m33]` (4×4 row-major) | `Matrix([[…],[…],[…],[…]])` | R | as A12, length 16. |

## B. Why two contracted functions / one prepatch

The gold edit is a single source line (`m12`) consumed by BOTH return branches
of the one method. `model.py` mirrors the two branches as two contracted
functions sharing the identical entry terms; `model_prepatch.py` reverts the
`m12` impl in BOTH (the single pre-change expression, `2s(cd + ba)`), so it
FAILS on the discriminating clause in each: `Result()[5] is off_cd_minus(...)`
(3×3) and `Result()[6] is off_cd_minus(...)` (4×4 upper-left block). One prepatch
covers the one independently-changed behaviour (the `m12` sign), observed at two
sites. (G-DIFF.)

## C. No kind-3 (unexpressible-changed-op) steps

The operation that changed — the sign of the `(b·a)` term in the third-column
second-row entry — is a difference of two products, modeled **deeply and
exactly**: `off_cd_minus(a,b,c,d,s)` unfolds to `mul(two_s(s), sub(mul(c, d),
mul(b, a)))`, the verbatim impl term, whose counterpart under R-ops is the
verbatim source expression. It is neither axiomatized nor abstracted; the seven
`@ContractOnly` constructors are the carrier itself and assert nothing, so
nothing about the changed operation is assumed. Nothing is hand-waved.

Nor is any step of it number-valued: the whole cascade is constructor
applications on the arguments, which is what makes A0-1sort's rule apply to the
impl regions vacuously — there is no numeric expression in either of them for the
rule to have to translate (checked in `conformance_check.py`).

## D. verify(model) ⇒ resolved

`rotation_matrix` / `rotation_matrix_affine` verify only if the call REACHES its
return (the method-level `Requires(MustTerminate(2))` / `(6)` obligation — under
Nagini's partial-correctness reading of `Ensures`, delivery is a separate
obligation, and the real method is a straight-line cascade with no loop and no
recursion, `quaternion.py:524-551`, so claiming it is faithful) and if every
delivered entry IS the term the clause names — in particular
`Result()[5]` / `Result()[6]` is `2s(cd − ba)` (the corrected sign) and
`Result()[7]` carries that term into `m13`.

Those clauses are claims at the arguments the source realises, not at a disjoint
set of them: there is no precondition on any argument, so each ranges over every
expression, and by A2 the fifth ranges over the scale expression `q.norm()**-2`
itself — `1/30` at `Quaternion(1, 2, 3, 4)`, `1` at the symbolic unit witness. So
an implementation that verifies has been checked on the very arguments the F2P
test drives.

It has also been checked to compute them with operations that mean something
there. By R-vocab the carrier vocabulary a realisation can use is the seven
constructors,
each of which has an exact counterpart (R-ops), so a verifying implementation
cannot be one that satisfies the clauses while denoting an operation the source
does not have — the rounding family does not translate. And by R-vocab again a
realisation cannot satisfy the clauses only where they are vacuous, on either of
the two things it can branch on WITHIN the carrier: a relation between scalars is
undecided between differently-built terms, and the truth value of a scalar is
undecided as well (`Scalar.__bool__` is declared and assumes nothing), so both
sides of any such guard carry the full obligation. Truthiness has to be named
here alongside the relations rather than folded into them: it is not a relation,
the repository decides it, and it decides it the other way at the term R-ops maps
`zero()` to — so an enumeration of relations alone would leave exactly this
family open at the load-bearing entry. That is the leg the field carrier lacked,
and it is what rules out the whole family of realisations that are correct exactly
where the repository's expressions never go. What it does NOT cover is reflection
on a scalar (`type`, `str`, `hash`, `id`), which names no carrier operation and
has no counterpart; that is left to the R-1sort rule in the next sentence, which
is the only instrument that reaches it, a verifier-dead branch having no clause to
refute it. And by R-1sort
together with A0-1sort, a realisation that steps outside the carrier into the
number sort the modelled behaviour does not have is translated by MEANING and not
by text: what it computes there denotes, in the repository, the value the verifier
proved it denotes, so a branch dead in the proof is dead in the realisation and
the entries delivered are the ones every clause was checked against.

Finally, by R-cong every identification the proof used is congruence, which holds
of the repository's expressions, and by R-finer the repository identifies more
than the carrier does — so the proof transfers and the model is the stricter of
the two, never the laxer. Together with R-layout (`Matrix(...)` ↔ row-major
value-preserving list) the verified entries are therefore the entries the gold
method builds on the tested inputs; `conformance_check.py` measures exactly that
against the real callee, and on symbolic quaternions as an identity of expression
trees. The F2P test compares the resulting `Matrix` for exact equality; the gold
method (= the verified skeleton under R) produces exactly that matrix, and the
pre-patch method produces the `+b·a` entry the spec rejects. Hence a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE).

There are no axiom trust points: the seven `@ContractOnly` constructors carry no
postcondition, so a proof can lean on nothing they say. The trust points are
refinement fidelity (this document, G-EQ) and the A-reference facts — the
value-preservation and row-major layout of the `Matrix` constructor, the realised
value of the common scale, the constructor bridge, and congruence and coarseness
of the repository's equality — all confirmed against the real callee in
`axiom_check.py` and `conformance_check.py`.
