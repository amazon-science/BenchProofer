# mapping.md — sympy__sympy-15349

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 768da1c6f6ec907524b8ebbf6bf818c92b56101b`, states the type
abstraction, and records what the bundle's seven `@ContractOnly` declarations are
(the constructors of the carrier) and what they assume (nothing). It also states
the rule that governs the translation of an expression the model has NO sort for
(§2, R-1sort) — the one place where this document, and not the machine, is what
carries `verify ⇒ correct`.

Repo file under change: `sympy/algebras/quaternion.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `rotation_matrix(a,b,c,d,s)` | the `if not v:` branch of `Quaternion.to_rotation_matrix` — `sympy/algebras/quaternion.py:489` (block `526`–`539`) | the modeled changed function: the 3×3 rotation block |
| `rotation_matrix_affine(a,b,c,d,s,x,y,z)` | the `else:` branch of the same method — `sympy/algebras/quaternion.py:541`–`551` | the 4×4 affine embedding (reuses the changed entry inside `m13`) |
| `Scalar` (class) | the type of `q.a`, `q.b`, `q.c`, `q.d`, `s` and every matrix entry: SymPy `Expr` | the carrier: one expression of this computation (§2) |
| `zero()` (contract-only) | `Integer(0)` | carrier constructor: the exact literal `0` the source writes (trailing affine row) |
| `one()` (contract-only) | `Integer(1)` | carrier constructor: the exact literal `1` the source writes (`1 - 2*s*(...)`, affine corner) |
| `two()` (contract-only) | `Integer(2)` | carrier constructor: the exact literal `2` the source writes (`2*s*(...)`) |
| `add(u,v)` (contract-only) | `u + v` on `Expr` | carrier constructor |
| `sub(u,v)` (contract-only) | `u - v` on `Expr` | carrier constructor |
| `mul(u,v)` (contract-only) | `u * v` on `Expr` | carrier constructor |
| `sq(u)` (contract-only) | `u ** 2` on `Expr` | carrier constructor |
| `two_s` (pure) | the shared factor `2*s` — `quaternion.py:527` ff. | pure spec: the factor every off-diagonal entry carries |
| `diag0/diag1/diag2` (pure) | `m00`, `m11`, `m22` — `quaternion.py:526,531,536` | pure spec: the three diagonal entries, `1 − 2s(c²+d²)` etc. |
| `off_bc_minus/off_bc_plus` (pure) | `m01`, `m10` — `quaternion.py:527,530` | pure spec: the `2s(bc ∓ da)` off-diagonals |
| `off_bd_plus/off_bd_minus` (pure) | `m02`, `m20` — `quaternion.py:528,534` | pure spec: the `2s(bd ± ca)` off-diagonals |
| `off_cd_minus` (pure) | `m12` — `quaternion.py:532` | pure spec: the third-column second-row entry `2s(cd − ba)` (the corrected sign) |
| `off_cd_plus` (pure) | `m21` — `quaternion.py:535` | pure spec: the second-column third-row entry `2s(cd + ba)` |
| `translation` (pure) | `m03/m13/m23` — `quaternion.py:544,545,546` | pure spec: `p_i − x·m_i0 − y·m_i1 − z·m_i2`, in the source's own left association |

The single repo edit is on the `m12` line (`quaternion.py:532`):
the pre-patch source computes `2*s*(q.c*q.d + q.b*q.a)`; the corrected source
computes `2*s*(q.c*q.d - q.b*q.a)`. In the model this is exactly the difference
between `off_cd_plus` (the prepatch term) and `off_cd_minus` (the required term)
at result index 5 (3×3) / 6 (4×4 upper-left block), and inside `translation` at
index 7.

## 2. Type abstraction (R-refinements)

The whole abstraction is one choice: **the model's carrier is the EXPRESSIONS of
this computation**, presented as an opaque type `Scalar` with seven constructors
and nothing else. The constructors are `@Pure @ContractOnly` with no `Ensures`,
so they assume no algebraic law, no ordering and no numeric content; a scalar IS
the term that builds it, two scalars are the same one exactly when they are built
the same way out of the same parts, and no other identification between terms
holds or is refutable. The repository's scalars are `Expr` — expression trees —
and its `==` is an equality of expressions, so this is the faithful reading and
not an approximation of one. Everything below is an instance of that one bridge.

| repo reality | model carrier | bijection |
|---|---|---|
| quaternion components `q.a, q.b, q.c, q.d` (SymPy `Expr`) | scalars `a, b, c, d` | component access `q.a` ↔ `a`, etc. No precondition restricts them, so each ranges over every expression the behaviour is realised at: indeterminates, rationals, trigonometric values of the angle. |
| `s = q.norm()**-2` (the common scale) | scalar `s` | the identity on expressions: the modelled scale IS the expression the source computes, passed as-is with no rescaling (`1/30` for `Quaternion(1,2,3,4)`, `1` for the symbolic unit witness). `norm` is NOT axiomatized — the patch does not change it, and all the refinement needs is that `s` is the expression `q.norm()**-2`, which both `conformance_check.py` and `axiom_check.py` obtain from that very call (`norm` applies `trigsimp` to the sum of squares, so the realised scale of a trigonometric quaternion is the exact scalar 1). |
| `Integer(0)`, `Integer(1)`, `Integer(2)`, `+`, `-`, `*`, `** 2` on `Expr` | `zero()`, `one()`, `two()`, `add`, `sub`, `mul`, `sq` | **(R-ops)** one counterpart per constructor, total and exact: applying the counterpart to the counterparts of the operands builds the counterpart of the term. Exhibited on symbolic operands in `axiom_check.py`. |
| `Matrix([[...],[...],[...]])` (SymPy 3×3 / 4×4 matrix) | `List[Scalar]` row-major (length 9 / 16) | **(R-layout)** `Matrix[i, j]` ↔ `Result()[i*ncols + j]`, with **no factor in between**; `Matrix` equality ↔ element-wise list equality. The F2P test compares two `Matrix` objects for exact equality, i.e. every entry equal — the row-major list pins exactly that. |
| the translation point `v = (x, y, z)` | scalars `x, y, z` | tuple unpacking `(x, y, z) = v` ↔ the three params; the source line `m_i3 = p_i − x·m_i0 − y·m_i1 − z·m_i2` is mirrored clause for clause, in the source's association. |
| `Expr.__eq__` (structural equality of expression trees) | sameness of scalars, written `is` | **(R-cong / R-finer)** the carrier proves exactly congruence, and congruence holds of the repository's expressions (building the same term twice out of the same parts yields the same expression). Conversely the repository identifies strictly MORE than the carrier does — it flattens and orders sums and products and collapses a repeated factor to a power, so `mul(c,c)`/`sq(c)` and `mul(b,c)`/`mul(c,b)` are distinct scalars it calls equal. The carrier is therefore the FINER relation and the model the stricter of the two, never the laxer. Both directions are exhibited in `axiom_check.py`. |

**Operation vocabulary of the bridge (R-vocab).** The seven constructors are the
whole vocabulary. There is no division, no remainder, no rounding and no order on
`Scalar`: `//` on `Scalar` is a type error and `<` on `Scalar` is a type error, so
a realisation reaching for one of them does not translate at all rather than
merely failing a clause. And the relations Python makes writable on any value —
`==`, `!=`, `is`, `is not` — are UNDECIDED here between differently-built terms,
in both directions: neither provable nor refutable. So a realisation that decides
an entry on such a relation has to satisfy the entry clauses on BOTH sides of it.

The same has to hold of the one remaining thing Python lets a realisation ask of
any value without naming an operation at all: its TRUTH VALUE. This is not a
relation between two terms, so the sentence above does not reach it, and it
matters more than the relations do, because the two languages disagree about it
at a term the map names outright. The repository's scalars are `Expr`, and `Expr`
defines `__bool__`; the counterpart R-ops assigns to `zero()` is `Integer(0)`,
which that method makes FALSY, and a plain object reference is truthy. So a
realisation deciding an entry on the truth value of a scalar would, if the model
left that truth value decided, have its guarded branch dead in the proof and live
in the repository on every input — the guarded-branch hole, at the load-bearing
entry, and reachable without writing any operation the vocabulary above excludes.
`Scalar` therefore DECLARES `__bool__` and asserts nothing about it, exactly as
the seven constructors assert nothing: no scalar is provably true and none is
provably false, the truth value of a scalar is undecided in both directions, and
a realisation that decides an entry on it carries the entry clauses on BOTH sides
of that decision, just as for `==` and `is`. `properties.py` carries the family as
reject cases (`rej-truthiness-guard-3x3`, `rej-truthiness-guard-argument`,
`rej-truthiness-guard-built-term`), and the branch is measured LIVE rather than
merely unentered: the rival with `Assert(False)` first inside the guarded branch
is REFUTED, so the rejection is not vacuous.

What remains outside the model's reach, and is governed by R-1sort's rule below
rather than by any clause, is REFLECTION on a value rather than computation with
it — `type(u) is type(v)`, `str(u)`, `hash(u)`, `id(u)`. `type` is not one of the
seven constructors and a type object is not a scalar, so such an expression has
no counterpart under this map at all; and the verifier's reading of it is not
Python's (it models `type(u)` as a fresh object, making even `type(u) is type(u)`
provably FALSE, where Python makes it True). An expression of that kind is
therefore in the same position as `7 // -2`: it lies outside the one sort this
behaviour computes with, its image is the VALUE the verifier proves it has, and a
realisation transcribing its characters into the repository is not that
expression's image but the image of a different expression the proof never saw.
No clause can close it — a branch the verifier proves dead is dead, so there is
nothing for a postcondition to refute — which is precisely why it is stated here,
as a rule of the map, and not attempted as a postcondition.

**Sort vocabulary of the bridge (R-1sort), and the rule for an expression with no
counterpart.** `Scalar` is not merely the carrier of the entries, it is the ONLY
sort this behaviour computes with. The three constants are nullary and the other
four take scalars and return a scalar, so no number is ever an argument, an
operand or a result anywhere in the model; the model's own impl regions are
straight-line constructor cascades containing no number-valued arithmetic at all
(machine-checked: `conformance_check.py check_no_number_sort` refuses `//`, `%`, a
real literal, `int(` and `float(` in either region). Whole numbers appear only as
positions in the result list and as its length — the SHAPE of the matrix, fixed at
nine and sixteen — and no arithmetic is performed on those either.

Whole numbers are nevertheless a sort the model's LANGUAGE has, so a realisation
can compute with them even though the modelled behaviour does not. The map is what
says what such a computation means, and it has to, because the two languages do
not agree about it:

| closed expression | this model's language, as the verifier reads it | the repository's language | measured |
|---|---|---|---|
| `7 // -2` | `-3` (division truncates toward zero) | `-4` (floor) | verifier: a realisation guarding on `7 // -2 == -3` is REFUTED at the load-bearing entry, one guarding on `== -4` verifies with the branch dead. repository: `conformance_check.py`. |
| `7 % -2` | `1` (sign of the dividend) | `-1` (sign of the divisor) | as above |
| `0.1 + 0.2 == 0.3` | true (the verifier's reals are exact) | false (binary approximation) | `conformance_check.py` |

So a closed numeric expression is not a shared piece of text with one value. It
has a value in this model, decided by the verifier's semantics — that is the
semantics the proof was carried out under, and the only sense in which the model
means anything at all — and a possibly different value in the repository. The
refinement rule follows, and it is the rule this document exists to state:

> **A refinement preserves MEANING, not text.** The image of an expression under
> this map is the repository expression that DENOTES WHAT THE MODEL EXPRESSION
> DENOTES. For a term of the carrier that is the R-ops counterpart, term for term.
> For a closed numeric expression — which has no counterpart, the modelled
> behaviour having no number sort — it is the VALUE the verifier proves it has:
> `7 // -2` translates to `-3`, `0.1 + 0.2 == 0.3` to `True`. Transcribing the
> characters `7 // -2` into the repository is NOT that expression's image, because
> those characters denote `-4` there; it is the image of a different model
> expression, one the proof never saw.
>
> **A refinement also preserves REACHABILITY.** A branch the proof discharged as
> unreachable is unreachable in the realisation. Under the rule above this is a
> consequence rather than an extra demand: a guard on a closed expression has the
> same truth value on both sides of the map once the expression is mapped by
> meaning, so a branch dead in the proof is dead in the realisation, and the
> realisation computes the entries the live branch computes — which are the ones
> every clause was checked against.

Two things are worth being explicit about, because this is a place where the
document rather than the machine is load-bearing.

*Why the rule is the right one and not a convenience.* The rival this rule answers
is a realisation whose impl region is the gold cascade wrapped in
`if 7 // -2 == -4: <pre-change entry>`. Under the verifier's semantics that guard
is FALSE, so the rival's impl and the gold impl are the SAME computation — not
merely equivalent, identical in every state the proof quantifies over. A model the
gold impl satisfies is therefore a model that rival satisfies, whatever the model
says: the construction is available against every specification of every behaviour
in any language whose closed arithmetic the verifier decides. Treating it as a
weakness of THIS behaviour's specification would be a category error, and treating
it as one to be repaired by strengthening a clause is not possible even in
principle — there is no clause it violates. What it is instead is a REFINEMENT
that does not preserve meaning: it maps a model expression denoting `-3` to a
repository expression denoting `-4`, and the rule above rules that out by name.

*What is left to the reader of this map.* The machine re-derives that a rival is a
same-spec model, that it verifies, and that a supplied realisation resolves. The
faithfulness of the realisation to the model — that it is the model's image under
THIS map — is the auditor's judgment, and the rule above is the standard it is
judged against. `properties.py` carries no reject case of this family, and the
comment above `rej-identity-guard-3x3` says why: one direction verifies (so it
cannot be listed as rejected, and no model closes it), and the other direction is
refuted but WOULD resolve, so recording its rejection as a win would credit this
specification with strength it does not have.

That is the substantive content of the carrier choice, and it is worth stating
what it replaces, because two earlier carriers each admitted a realisation that
verifies and does not resolve.

* A carrier of **integers** fails twice over. ℤ carries the ℤ-specific total
  operations `//` and `%`, and expressions such as `(3*k)//3` and `k - k % 1` are
  identities at every integer — so a realisation using them satisfies every entry
  equation and verifies, while what they denote is TRUNCATION, which is not an
  operation on the repository's scalars at all (the entries here are in general
  not integers: `2/3` at `Quaternion(1,2,3,4)`, `-sin(x)` at the symbolic
  witness, which has no integer part to take). And over ℤ a condition on the
  scale is vacuous: `0 < s < 1`, precisely the ordinary case for a reciprocal,
  has no integer solution, so a realisation may branch on it and do as it likes
  on the branch reality takes.
* A carrier of **field or real values** repairs both of those and introduces a
  third, worse one. It removes `//` and `%` and makes the scale condition
  satisfiable, but it supplies a SEMANTIC equality and a DECIDABLE ORDER that the
  repository's scalars do not have. Over any field the condition
  `(a + d)*(a + d) != a*a + 2*a*d + d*d` is unsatisfiable — so a realisation
  deciding an entry on it verifies with the guarded branch unreachable — while
  `Expr.__eq__` compares expression TREES, under which the two sides are
  distinct, so that same guarded branch is the one the real code takes on every
  input. Any polynomial identity generates another instance, and the order
  relation supplies a family of its own, being undecidable on the repository's
  scalars. No strengthening of the entry equations reaches such a realisation
  because it violates none of them, and no carrier of VALUES closes the family at
  all, since the family is generated by equations that hold of values and fail of
  expressions.
* On the **expression** carrier the two sides of every such condition are
  distinct terms, no identification and no separation between them is provable,
  both branches are reachable, and the entry clause is refuted on the guarded
  one. `properties.py` carries all three families as reject cases
  (`rej-truncate-3x3` for the rounding family — inexpressible here;
  `rej-identity-guard-3x3`, `rej-identity-guard-m01`,
  `rej-identity-guard-affine-m03` for the polynomial-identity family;
  `rej-order-guard-3x3` for the relational family — inexpressible here), and
  `axiom_check.py` exhibits the underlying fact: pairs of differently-built
  expressions that agree at every number, distinct in the repository, with the
  guard condition evaluating to `True` there.

`q.b**2` is written `sq(b)` in the model, whose counterpart is `b ** 2` — the
operation the source performs — and not `mul(b, b)`, which is a different scalar
here. SymPy `2*s*(...)` ↔ model `mul(mul(two(), s), ...)` and `1 - 2*s*(...)` ↔
`sub(one(), mul(mul(two(), s), ...))`; the association is the source's
throughout, so the impl regions mirror `quaternion.py:526-548` line for line.

## 3. Axioms

Seven, and they are the CONSTRUCTORS of the carrier: `zero`, `one`, `two`, `add`,
`sub`, `mul`, `sq` (`meta.json axioms`, each with an empty `assumes`). They are
`@Pure @ContractOnly` with a docstring and NO `Ensures`, so they contribute **no
axiom trust point**: there is nothing they state for a proof to lean on and
nothing a rival could satisfy vacuously. Their only role is to make the carrier
opaque — which is exactly what removes the operations and the decided relations
that earlier carriers smuggled in (§2, R-vocab).

The three constants are NULLARY, which is the whole of their content: `lit(k)`
taking a whole number would make the model's declared interface mention a second
sort, and the model would then be about two sorts of value while the behaviour is
about one. The source writes exactly three integer literals (`0`, `1`, `2`), so
three nullary constants name them exactly and nothing is lost (`axiom_check.py`
exhibits each against `Integer(0)`, `Integer(1)`, `Integer(2)`).

Consequently there is no G-AX axiom obligation to fuzz, and `AXIOM_TESTS` in
`properties.py` is empty by design. What `axiom_check.py` validates instead are
the **A-reference** facts the refinement rests on, each against the REAL callee
in the instance image:

* **R-ops** — each constructor's counterpart, exhibited on symbolic operands.
* **R-layout** — `Matrix[i,j]` equals the supplied entry and the constructor is
  row-major and value-preserving, on rational, integral and fully symbolic
  quaternions, for both the 3×3 and the 4×4 shape.
* **R-formula** — every entry the real `to_rotation_matrix` produces IS the
  corresponding model term under the bridge, at the realised scale `1/norm²`; on
  symbolic quaternions this is checked as an identity of expression TREES
  (`srepr`), the strongest form of the claim, and the issue's own witness
  `Quaternion(cos(x/2), sin(x/2), 0, 0)` yields the textbook X-rotation matrix.
* **R-cong** — congruence holds of the repository's expressions.
* **R-finer** — the repository's equality is coarser than the carrier's sameness
  (so the model is the stricter of the two), together with the carrier-forcing
  witness: differently-built expressions that agree at every number are distinct
  there, and the guard condition built from them evaluates to `True`.
* **R-1sort** — `conformance_check.py` confirms that neither impl region contains
  number-valued arithmetic, and records the repository language's readings of the
  closed expressions the table above turns on.

The unchanged callee `norm` is not axiomatized because the patch does not change
it; what the refinement uses about it is only the R-fact that the realised scale
is the expression `q.norm()**-2`, which both out-of-band checks take from the
real call rather than re-deriving.
