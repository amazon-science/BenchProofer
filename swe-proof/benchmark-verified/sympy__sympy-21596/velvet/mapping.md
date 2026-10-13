# mapping.md — sympy__sympy-21596

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 110997fe18b9f7d5ba7d22f624d156a29bf40759`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of every modeled callee.

Repo file under change: `sympy/sets/handlers/intersection.py`
(the `@dispatch(ImageSet, Set)` overload of `intersection_sets(self, other)`,
the `if other == S.Reals:` branch — body lines 279–322 @ base_commit, 279–327
after the change).

`spec_provenance: cold` — the spec was derived from the `problem_statement`, the
gold `patch`, and the real source at `base_commit` only.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line) | role |
|---|---|---|
| `restrictToRealValues (domain, imaginaryPart, denominators, valueOf)` | the `other == S.Reals` branch of `intersection_sets` — `intersection.py:279–327` (changed lines 284–294, 323–324, 326) | the modeled changed function: assembles the index set whose image is the real intersection, and hands back the assembly. It speaks for the two outcomes of settling the imaginary part that REACH the assembly (§2.4); the two that return before any changed line do not belong to the modeled surface |
| `domain : Set Int` | `base_set` on entry to the branch (`self.base_sets[0]` — read at line 231: `S.Integers`, `S.Naturals0`, …) | the index domain the family ranges over. It reaches the answer as the nullary ATOM `IndexReport.given`, i.e. as the object handed in ITSELF; the `Set Int` value is used only by `reported`, to read a description back as indices |
| `imaginaryPart : ImaginaryPart` | the OUTCOME of settling `im = expand_complex(...)` (line 303) in the chain at lines 309–318: `if im.is_zero:` … `else:` | what the branch has been told about the imaginary part, in the two shapes that reach the assembly (§2.4). `.zeroThroughout` ↔ `im.is_zero` is True (lines 309–313, whose body is `pass`); `.factors gs` ↔ the `else` leg, where the numerator's factor list `Mul.make_args(numer(im))` is handed over (line 324). The shape is READ OFF `im` before any index set is built, never chosen by the answer |
| `ImaginaryPart.factors gs` — its payload `gs` | `Mul.make_args(numer(im))` — line 324, the factor list of the imaginary part's numerator (`numer` imported at line 8, `im = expand_complex(...)` line 303) | the factors resolved ONE AT A TIME by `_solution_union` (line 288 loop); the value is real at `n` iff one of them vanishes. Each list member is the factor ITSELF — an identity-bearing handle — and NOT the values it takes, because line 293 puts the factor into the object the caller sees (§2.3) |
| `keptToReal` *(pure spec)* | lines 309–313 vs 323–324: `pass` (no `&=` at all) vs `base_set &= _solution_union(Mul.make_args(numer(im)), n)` | the keep leg AS ASSEMBLED for each shape: the atom `given` where the imaginary part is settled zero throughout (nothing stands over `base_set`, because the branch performs no keep step), `meet given (zerosOfAny gs)` where the factors were handed over |
| `realIndices` *(pure spec)* | the membership of `base_set` as it reaches line 326 | the same two shapes read as plain index sets: the whole domain where the imaginary part is settled zero (every member of the family is already real), the domain intersected with the listed factors' zero indices otherwise |
| `denominators : List Factor` | `denoms(f)` — line 326, the denominators of the family expression `f = self.lamda.expr` (line 296) | the factors resolved one at a time by the same helper; their vanishing makes the value undefined. Same carrier, for the same reason: the ONE helper both legs call is the one that embeds a factor (§2.3) |
| `valueOf : Factor → Int → Option Rat` | `i.subs(n, k)` — the value a factor takes at an index, as `solve_linear`/`Eq` read it | the value READING, a separate input. `valueOf g k = some q` iff `g.subs(n,k)` is the Rational `q`, `none` iff it is no rational value (`zoo`, `nan`). A function OF a factor, so the values are a consequence of the factor and never determine one (§2.3) |
| `out : IndexReport` | the `base_set` object at line 327, as BUILT by lines 323–326 | the assembled index-set description handed to `imageset` |
| `IndexReport` *(deep model — A-reference)* | the SymPy set-expression tree gold constructs: `Union` of `FiniteSet`/`ConditionSet` nodes (lines 291, 293, 294) combined by `&` (323) and `-` (326), inside the set algebra those operators live in (`Union`, `Complement`, `S.EmptySet`) | pure spec: HOW an index set is put together, not merely which indices it holds |
| `IndexReport.given` | `base_set` itself, the left operand of line 323 | the ATOM: the index domain as handed in, with no node between it and the `&=` |
| `IndexReport.noIndices` / `.either` / `.otherIndices` | `S.EmptySet` / `Union(a, b)` / `Complement(S.Integers, a)` — the rest of the set algebra `&=` and `-=` live in, available to any implementation of this branch | pure spec: the OTHER descriptions of a collection of indices that the same callees can build. Present so that a re-described domain is EXPRESSIBLE and then excluded by name (§2.2), not unrepresentable |
| `vanishingSet valueOf g` *(deep model — A-reference)* | the one-factor node `_solution_union` emits for a factor `i`: `FiniteSet(xis)` when `solve_linear(i, 0, [sym])` returns `x == sym` (lines 289–291), else `ConditionSet(sym, Eq(i, 0))` (line 293) | pure spec: the indices at which one factor vanishes |
| `anyVanishes valueOf gs` *(deep model — A-reference)* | `_solution_union(exprs, sym)` as a whole — `Union(*sols)` over the per-factor nodes (line 294) | pure spec: the indices at which any LISTED factor vanishes |
| `.meet` | `base_set &= …` — line 323 | keep the domain down to the real-making indices |
| `.apart` | `base_set -= …` — line 326 | take that apart from the undefined indices |
| `reported` *(deep model — A-reference)* | `Set.contains` / `in` on the constructed object — the membership semantics of the SymPy set algebra (`Union`, `&`, `-`, `FiniteSet`, `ConditionSet`) | pure spec: reading a description back as a plain set of indices |

The pre-patch logic the change replaces (refinement audit only; elided from the
consumer spec view): the imaginary-part leg
`x, xis = zip(*[solve_linear(i, 0) for i in Mul.make_args(im) …]); base_set -=
FiniteSet(xis)` (lines 306–311 @ base_commit — a `-=` where the desired behaviour
keeps, and one `FiniteSet` of a tuple rather than a per-factor union), and the
denominator loop `for i in denoms(f): … solve_linear(i, 0) for i in
Mul.make_args(im) …` (lines 312–321 @ base_commit — the inner comprehension
re-ranges over the imaginary part's factors instead of the denominator `i`).
`Solution_prepatch.lean` is the first leg (no keep), `Solution_prepatch_2.lean`
the second (the denominator leg never removes anything).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4) and G-AX use to translate values between the Lean
value domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `base_set` on entry — a SymPy index `Set` over the integers (`S.Integers`, `S.Naturals0`, …) | `domain : Set Int`, and the atom `IndexReport.given` | a symbolic integer set `B` ↔ `{n | B.contains(n) is True}`; `k ∈ B` ↔ `k ∈ domain`. The OBJECT `B` itself ↔ the atom `given`, which is what the assembly clause pins; the `Set Int` reading is what `reported` uses. The two are deliberately NOT the same carrier: `Set Int` is extensional and the object is not (§2.2). |
| the outcome of `im.is_zero` at line 309 — `True` (the `pass` leg) or "neither True nor False, and `ifree == {n}`" (the `else` leg) | the constructor of `imaginaryPart : ImaginaryPart` — `.zeroThroughout` / `.factors gs` | outcome ↔ constructor. The correspondence is on the OUTCOME, not on the indices it leads to: `im.is_zero is True` ↔ `.zeroThroughout` even though the branch then keeps every index of `base_set`, and a `.factors gs` whose factors vanish everywhere is NOT that outcome (§2.4). The two remaining outcomes (`im.is_zero is False` → `return S.EmptySet` at 314–315, `ifree != {n}` → `return None` at 316–317) return before any changed line and have NO carrier here. |
| a factor of `numer(im)` (`Mul.make_args`, line 324), a rational function of the lambda variable `n`, as an OBJECT | one element of the `gs` payload of `ImaginaryPart.factors` | factor `i` ↔ the handle for `i`. The correspondence is on the factor's IDENTITY, and it is INJECTIVE in the direction that matters: distinct SymPy factors are distinct handles, so no two factors of the model are conflated. The LIST is ordered as `Mul.make_args` yields it, and its LENGTH is observable (§3.1). Modeling `numer(im)` rather than `im` matches line 324: a zero of `im` is a zero of its numerator, and the denominator is handled by its own leg. |
| an element of `denoms(f)` (line 326), as an OBJECT | one element of `denominators : List Factor` | `d` ↔ the handle for `d`, same correspondence. |
| `i.subs(n, k)` — the VALUE a factor takes at an index | `valueOf : Factor → Int → Option Rat` applied to that factor's handle and `k` | `valueOf g k = some q` iff `g.subs(n,k)` is the Rational `q`, and `= none` iff it is no rational value at all. TOTAL and EXACT **on values**: the factor `n + 1/2` reads as `1/2` at `k = 0` (neither `0` nor an integer), and `1/n - 1` reads as `none` at `k = 0` (`zoo`), so no index is silently truncated into a root or out of one. It is NOT injective and is not claimed to be: `n**2 - n/2 - 1/2` and `(n-1)*(2*n+1)/2` are measured value-identical over the probed integers and are different objects by `srepr`, which is exactly why the value reading is a SEPARATE input from the factor rather than the factor's carrier (§2.3). |
| the object `_solution_union(exprs, sym)` RETURNS (line 294) | `IndexReport.zerosOfAny gs` | a `Union` of one node per element of `exprs`, in order ↔ `zerosOfAny` of the corresponding factor list. The correspondence is per-factor: `exprs` of length 2 ↔ a two-element `gs`, and NOT a one-element `gs` whose factor is their product (§3.1). |
| `base_set &= S` (line 323) | `.meet a b` | `&=` ↔ `meet` on the description; on membership `k ∈ (B & S)` ↔ `k ∈ reported a ∩ reported b` |
| `base_set -= S` (line 326) | `.apart a b` | `-=` ↔ `apart`; on membership `k ∈ (B - S)` ↔ `k ∈ reported a \ reported b` |
| `Union(a, b)` / `Complement(S.Integers, a)` / `S.EmptySet` — the operations the same set algebra offers | `.either a b` / `.otherIndices a` / `.noIndices` | the reshapes an implementation of this branch could build out of the identical callees; on membership `∪` / complement / `∅`. They are modeled so that the assembly clause can EXCLUDE them by name (§2.2) |
| `k in <the constructed set>` | `k ∈ reported domain valueOf out` | the membership semantics of the whole assembled object, read over the index domain the assembly was built from |
| `imageset(lam, base_set)` (line 327) | (omitted — unchanged frame) | the image step is byte-identical pre/post-change and merely carries the assembled index set forward, so it is outside the modeled change (directive 5). It is also STRUCTURE-PRESERVING: `imageset` of a `FiniteSet` is a `FiniteSet` of images and `imageset` of a `ConditionSet` is an `ImageSet` over it, which is why the index-set assembly, not just its membership, is what the caller ends up reporting. |

### 2.1 Why the carrier is the ASSEMBLY and not only the membership

An index-set carrier that records only WHICH indices survive is strictly weaker
than the repo behaviour, and the gap is caller-visible. The failing test compares
returned objects, e.g. `FiniteSet(-1, 1)` for the issue's own family. "The
integers at which `(n - 1)(n + 1)` vanishes" holds exactly the indices `-1` and
`1`, so a membership-only post-image cannot distinguish it — yet the real callees
turn that description into `ConditionSet(n, Eq((n-1)*(n+1), 0), Integers)`, which
is a different object from `FiniteSet(-1, 1)` and fails the comparison. The
mechanism is line 288–293: `_solution_union` loops over the factors it is GIVEN
and `solve_linear` names an index only for a factor it can solve, so the shape of
the answer depends on the factor LIST, not on the set of indices that list picks
out. `IndexReport` is therefore the carrier, with `reported` retaining the
membership reading as a second, weaker obligation.

Clause-by-clause justification of the assembly post-image against the patched
source:

| clause fragment | justified by |
|---|---|
| innermost node is the ATOM `given` | `base_set` is bound at line 231 (`self.base_sets[0]`) and reaches line 323's `&=` unmodified — nothing between the two rebinds or re-describes it, so the left operand of the `&=` is that object itself |
| `keptToReal (.factors gs)` = `meet given (zerosOfAny gs)` | line 323–324, inside the `else` leg of the `im.is_zero` chain: `base_set &= _solution_union(Mul.make_args(numer(im)), n)` |
| `keptToReal .zeroThroughout` = the bare atom `given`, with NO node over it | lines 309–313: `if im.is_zero:` … `pass`. The keep step is SKIPPED, so `base_set` reaches line 326 exactly as it was bound at line 231 — not narrowed by a collection that happens to exclude nothing, but not narrowed at all (§2.4) |
| the keep leg depends on the SHAPE and nothing else | the `if`/`elif`/`else` chain at 309–318 dispatches on `im` alone, before any set is built; no branch inspects `base_set` or the denominators to decide whether to keep |
| `zerosOfAny` = one contribution per listed factor | lines 288–294: `for i in exprs: … sols.append(…)`, `Union(*sols)` |
| outer node `apart … (zerosOfAny denominators)`, under BOTH shapes | line 326: `base_set -= _solution_union(denoms(f), n)` — OUTSIDE the `if`/`elif`/`else` chain (dedented to the chain's own indentation), so it runs on the `pass` leg as well as on the `else` leg. This is the changed line the settled-zero shape reaches, and it is why that shape is inside the modeled surface rather than out of scope |
| the two lists are NOT interchangeable | 324 supplies the imaginary numerator's factors to the `&=`, 326 the denominators to the `-=` |
| keep before remove (`apart` outermost) | 323 executes before 326, and only the `-=` result reaches line 327 |
| the factor lists are passed through unchanged | 324 and 326 hand `Mul.make_args(numer(im))` and `denoms(f)` straight to the helper, which iterates them in order (line 288) |

### 2.2 Why the domain leaf is an ATOM and the algebra is CLOSED

Clause (1) is an equation between DESCRIPTIONS, so what it can distinguish is
bounded by what a description can distinguish — and that made an earlier
`given (s : Set Int)` leaf strictly weaker than it looked. `Set Int` is
EXTENSIONAL: two sets with the same members are the same value, so
`given ((domain ∩ Z) ∪ (domain \ Z)) = given domain` was a THEOREM, and an
implementation that narrowed `base_set` by a condition excluding no index
satisfied the assembly clause verbatim. The SymPy objects it corresponds to are
NOT extensional — they are compared by `==`/`srepr` — so that same
implementation hands line 323 an `Intersection`/`Union` over a `Complement` where
gold hands it `S.Integers`, and line 327 reports a different object. Measured on
the family whose imaginary part does not split into linear factors: masking the
domain with "the indices that either do or do not make some listed factor vanish"
answers
`Union(ImageSet(Lambda(x, x/2), Complement(ConditionSet(n, Eq(n**2 - n/2 - 1/2, 0), Integers), …)), Intersection(…))`
where the failing test asserts
`ImageSet(Lambda(x, x/2), ConditionSet(n, Eq(n**2 - n/2 - 1/2, 0), Integers))`,
with identical membership at every probed integer — harness verdict on that
shape: FAIL_TO_PASS 0/1, PASS_TO_PASS 46/46.

Two changes make the Lean carrier as fine as the repo's on this axis:

1. **`given` is nullary.** It denotes `base_set` itself. No description of the
   same indices can be substituted for it, because a description of the same
   indices is not that constructor.
2. **The algebra is CLOSED over the operations the branch's own callees offer**
   (`noIndices` ↔ `S.EmptySet`, `either` ↔ `Union`, `otherIndices` ↔
   `Complement`, next to `zerosOfAny`/`meet`/`apart`). The masked, split,
   complemented and enlarged-then-cut-back assemblies are therefore EXPRESSIBLE,
   and the clause excludes them by naming the single assembly asked for — rather
   than being silent about assemblies the model cannot write down, which would
   leave the spec weaker than it reads.

Direction of the residual strictness. Being finer than the caller-visible object
on some axis can only make the clause reject a rival, never admit one. Two such
axes are known and recorded rather than weakened away:

* **Argument ORDER inside a leg.** `zerosOfAny` carries an ordered `List` while
  `Union` canonicalizes its arguments, so two factor lists differing only in
  order describe one SymPy object and two `IndexReport`s. The pinned clause is
  still TRUE of the real code (lines 323–324 and 326 pass their lists through
  untouched, in the order the callees produced them), so nothing faithful is
  excluded; a permuting implementation is refused conservatively.
* **Caller-invisible REGROUPING.** Pinning one assembly refuses regroupings that
  would resolve; the measured ones are listed in refinement.md §B.2 and in
  `properties.py` under "SPEC-STRENGTH PROBES … NOT shipped", precisely so the
  over-strict direction is visible.

### 2.3 Why a factor is an OBJECT and its values are a separate reading

§2.2 closed this hole for the domain leaf. It is the SAME hole one level down, on
a collection's members, and it was left open.

Clause (1) is an equation between DESCRIPTIONS, so what it can distinguish is
bounded by what a `zerosOfAny` payload can distinguish — and an earlier
`zerosOfAny (gs : List (Int → Option Rat))` payload carried a factor as the
FUNCTION giving its value at each index. A function is EXTENSIONAL, so any
re-presentation of a factor taking the same value at every index WAS the same
payload member: on that carrier

    gs.map (fun g k => if g k = some 0 then some 0 else g k) = gs

is a THEOREM (`funext`, then `by_cases` on `g k = some 0`), and an implementation
that handed a leg's list to the helper re-presented factor by factor satisfied the
assembly clause VERBATIM.

The repo objects are not extensional. A factor is an expression compared by
`==`/`srepr`; MANY distinct expressions take the same value at every index
(measured: `n**2 - n/2 - 1/2`, `(n-1)*(2*n+1)/2` and `n**2 - n/2 - 1/2 + 0` are
value-identical over the probed integers and three different objects by `srepr`);
and line 293 puts the factor ITSELF into the node it builds
(`ConditionSet(sym, Eq(i, 0))`), which line 327 carries into the object the caller
reports. So a re-presenting implementation answers a different object with
identical membership. Measured on the family whose imaginary part does not split
into linear factors: it answers

`ImageSet(Lambda(x, x/2), ConditionSet(n, Eq((n - 1)*(2*n + 1)/2, 0), Integers))`

where the failing test asserts

`ImageSet(Lambda(x, x/2), ConditionSet(n, Eq(n**2 - n/2 - 1/2, 0), Integers))`,

with identical membership at every probed integer — harness verdict on that shape:
FAIL_TO_PASS 0/1, PASS_TO_PASS 46/46.

Two changes make the Lean carrier as fine as the repo's on this axis, mirroring
§2.2:

1. **A factor is `Factor`, an identity-bearing handle.** It denotes the factor
   handed in. Its values are not part of it, so a factor of equal value everywhere
   is a DIFFERENT factor, and — since the handle exposes nothing but its identity
   — no `Factor` can be manufactured out of the values any factor takes. Only the
   factors handed in can appear in an answer.
2. **The value reading is a SEPARATE input, `valueOf : Factor → Int → Option Rat`.**
   Clause (2) keeps its full extensional strength (the surviving indices are still
   pinned exactly) while clause (1) pins the factors themselves. Because `valueOf`
   is a function OF a factor, the values are a consequence of the factor and never
   determine one.

Applied to BOTH lists, not just the imaginary part's: lines 323–326 resolve the two
collections through the ONE helper at 284–294, and line 293 fires for either of
them, so an obligation on the keep leg alone would be asymmetric against the
shared helper and its faithfulness would rest on which families the suite happens
to assert. `properties.py` ships `weak-represents-a-factor` (measured not to
resolve) and `weak-represents-a-denominator` (shipped on that symmetry; the
asserted families do not happen to observe denominator syntax) for the two legs.

Direction of the residual strictness, recorded rather than weakened away. Pinning
member identity refuses a re-presented member regardless of which branch the
callees take for it, and on the line-291 branch the emitted node carries no syntax
at all (measured: `n - 1`, `2*n - 2`, `1 - n` and `n/3 - 1/3` all build the same
object, `FiniteSet(1)`), so a counterpart that re-presented only SOLVABLE factors
would resolve and is refused conservatively. That is the price of stating the
obligation on the members rather than on the callees' internal case split: the
alternative would make the spec's strength depend on a split the caller cannot
see, and would leave the hole open on every family whose factors the callees
cannot solve. Being finer than the caller-visible object can only make the clause
reject a rival, never admit one.

### 2.4 Why the imaginary part is a TWO-SHAPE INPUT and not a factor list

The branch settles the imaginary part BEFORE it builds any index set, and the
outcome of that settling decides whether a keep step happens at all. The patched
source, read at `base_commit + patch` (lines 309–327, quoted as it stands):

```python
        if im.is_zero:
            # allow re-evaluation
            # of self in this case to make
            # the result canonical
            pass
        elif im.is_zero is False:
            return S.EmptySet
        elif ifree != {n}:
            return None
        else:
            ...
            base_set &= _solution_union(
                Mul.make_args(numer(im)), n)
        base_set -= _solution_union(denoms(f), n)
        return imageset(lam, base_set)
```

Four outcomes, and exactly TWO of them reach an assembly:

| outcome | what the branch does | modeled as |
|---|---|---|
| `im.is_zero` is True | NOTHING is kept: the leg's body is `pass`, so `base_set` reaches line 326 as bound. Every member of the family is already real, so there is nothing to narrow BY — no factor of `im` is resolved and `Mul.make_args(numer(im))` is never formed | `imaginaryPart = .zeroThroughout`, keep leg `given` |
| `im.is_zero` is neither True nor False, and `ifree == {n}` | the numerator's factors are handed over and the domain is kept down to their zeros (323–324) | `imaginaryPart = .factors gs`, keep leg `meet given (zerosOfAny gs)` |
| `im.is_zero` is False | `return S.EmptySet` at 314–315 — before line 323 and before line 326, i.e. before EVERY changed line | out of scope (unchanged frame, directive 5); the modeled surface does not speak for it |
| `ifree != {n}` | `return None` at 316–317 — likewise before every changed line | out of scope, same reason |

The settled-zero outcome is NOT out of scope: it falls through to line 326, which
IS a changed line, so the modeled surface has to say what the answer is there —
and what it is, is the domain taken apart from the denominators' zeros, with no
keep node at all.

Why the shape is an INPUT with two constructors rather than a factor list:

* the two outcomes call for DIFFERENT ASSEMBLIES, not merely for different
  indices. A factor-list carrier can only express "settled zero" as some list,
  and every candidate is a different assembly from the one the branch performs:
  the empty list gives `meet given (zerosOfAny [])`, whose indices are EMPTY
  where the branch keeps the whole domain; a list of factors vanishing everywhere
  gives `meet given (…)`, which holds the right indices but stands a keep node
  over `base_set` where the branch stands none. Both are shipped as rejected
  rivals (`weak-ignores-the-settled-shape`, `weak-keeps-when-settled-zero`).
* standing a keep node there is caller-VISIBLE, not merely cosmetic. The `&=`
  re-evaluates `base_set`, which is exactly what the leg's own comment says it is
  avoiding ("allow re-evaluation of self in this case to make the result
  canonical" — read as the deliberate intent of the `pass`). Measured on the
  family `imageset(Lambda(n, n/2), Intersection(S.Integers, Interval(0, 5),
  evaluate=False))`, whose `im.is_zero` is True and whose keep collection would be
  `UniversalSet()`: the branch answers `FiniteSet(0, 1/2, 1, 3/2, 2, 5/2)` and a
  counterpart that narrows anyway answers `ImageSet(Lambda(n, n/2),
  Range(0, 6, 1))` — the same six members, a different object. Both halves of that
  are checked mechanically: G-CONF's *narrow-anyway* control (§4) IS that rival,
  run against the gold-patched function on this very family, and G-AX's Fact 8
  (§3.1) pins the callee premise (the node is `S.UniversalSet`, it contains every
  probed index, and `B` vs `B & UniversalSet` are `srepr`-different for a
  non-canonical `B`). (Measured on a constructed family of that shape; the failing
  test's asserted families do NOT cover it — all seven reach the `else` leg.)
* the shape is read off `im` alone, before any set exists, so it is an INPUT: the
  answer never chooses it, and no rival can recover it from the indices it would
  produce, because the two constructors are distinct regardless of the values
  `valueOf` gives (a `.factors gs` whose factors vanish at every index is still
  not `.zeroThroughout`).

`Solution_prepatch.lean` — the twin whose keep leg is absent — is therefore
exactly what the branch does on the settled-zero shape, and it fails to verify
only where the imaginary part arrives AS FACTORS. That is the discrimination the
spec has to carry: not "is there a keep leg" but "which shape calls for one".

## 3. Callee provenance (deep-model references — checked by G-AX)

### 3.1 `vanishingSet` / `anyVanishes` / `IndexReport` / `reported` ↔ the real set algebra (A-reference)

**Callees (all UNCHANGED at base_commit; the change only re-arranges how they are
combined):**
- `sympy.solvers.solvers.solve_linear(expr, 0, [n])` — returns `(n, sol)` for a
  factor linear in `n`, and `(numer, denom)` otherwise. Gold turns the first into
  `FiniteSet(sol)` and the second into `ConditionSet(n, Eq(expr, 0))`; in both
  cases the node denotes the indices at which the factor vanishes —
  `vanishingSet`.
- `sympy.simplify.radsimp.numer` (imported line 8) with `Mul.make_args` — splits
  the imaginary part into the factor list carried by `ImaginaryPart.factors gs`
  — reached only on the `else` leg (line 324), which is why the settled-zero
  shape carries no list at all (§2.4).
- `sympy.solvers.solvers.denoms(f)` — the denominators of the family expression,
  the list `denominators`.
- `Union`, `FiniteSet`, `ConditionSet`, `&`, `-`, `imageset` — the set algebra
  realizing `zerosOfAny` / `meet` / `apart` and their membership reading.

**Soundness check (G-AX):** `axiom_check.py` runs the real `solve_linear`,
`numer`, `denoms` and the SymPy set operations and asserts, for the issue's own
factors and for fuzzed linear/affine factors, both legs of the model:

1. *membership* — for each integer `k`, `k ∈ _solution_union([g₁ … gₘ], n)` iff
   some `gⱼ.subs(n,k) == 0` (so `anyVanishes` denotes what the helper builds), and
   `k ∈ (B & Z) - S` iff `k ∈ B ∧ k ∈ Z ∧ k ∉ S` (so `reported` denotes the
   membership of a `meet`/`apart` assembly);
2. *assembly* — the object is a FUNCTION of the factor list and not only of the
   index set it denotes: `_solution_union` on a two-factor list and on the
   one-element list holding their product denote the same indices but are
   DIFFERENT objects by `srepr` (the first names the indices, the second does
   not), which is what `IndexReport` distinguishing `zerosOfAny [g₁, g₂]` from
   `zerosOfAny [g₁*g₂]` records; and the construction is deterministic
   (`srepr`-stable across repeated builds), so pinning one assembly is not
   pinning an implementation accident;
3. *member identity* — the object depends on each listed factor's own IDENTITY and
   not only on the values that factor takes: for two expressions that are
   value-identical at every probed index and different objects by `srepr`,
   `_solution_union` on the one-element list of each builds DIFFERENT objects,
   because line 293 embeds the factor itself. That is what makes `Factor` an
   identity-bearing handle with `valueOf` a separate reading (§2.3) rather than a
   value function, and it is checked on BOTH the imaginary-part and the
   denominator list, since one helper serves both legs.
4. *a keep node excludes nothing and is still observable* — the fact behind
   `keptToReal .zeroThroughout = given` (§2.4). On the settled-zero shape a
   counterpart that keeps anyway hands the callees `Mul.make_args(numer(0))`,
   whose node is `S.UniversalSet`; G-AX asserts that node is exactly
   `S.UniversalSet`, that it contains every probed index (so the rival keeps the
   same indices as the branch), and that `B` and `B & UniversalSet` are
   nonetheless DIFFERENT objects by `srepr` where `B` is not already canonical —
   measured on `Intersection(S.Integers, Interval(0, 5), evaluate=False)`, the
   shape the leg's own comment is protecting. On an already-canonical `B` the two
   coincide, and that direction is recorded rather than asserted (2 of the 3
   probed pairs).

stdlib + sympy (the repo under test) only. Exit 0 iff sound.

No **consumed** axiom: the proof uses no `axiom`'s `ensures`. `Factor`,
`vanishingSet`, `anyVanishes`, `IndexReport` and `reported` are spelled-out deep models
(A-reference), validated against the real callees by G-AX (refinement.md §A).

## 4. G-CONF fuzz seed (pinned for deterministic eval)

`conformance_check.py` seeds its `random.Random` with **`21596`**. The R/I shadow
it builds transliterates the impl region — assemble `given domain`, `meet` with
the per-factor zero collection of the imaginary numerator's factors ONLY on the
shape that reaches line 323 (on the `if im.is_zero: … pass` leg it keeps nothing,
just as the branch does not), then `apart` the per-factor zero collection of the
denominators — to Python over the **real**
SymPy callees (`solve_linear`, `numer`, `denoms` are run for real: they are the
unchanged A-reference callees, out of the R/I leg), and diffs the result against
the gold-patched `imageset(...).intersect(S.Reals)` on fuzzed integer-indexed
families, on BOTH legs of the carrier:

* *membership* — for fuzzed query integers, `k ∈ shadow` vs `k ∈ gold`;
* *structure* — `srepr(shadow) == srepr(gold)`, the leg that the failing test
  itself compares and that a membership-only shadow cannot check.

The imaginary-part leg and the denominator leg are exercised separately (families
without / with `n`-dependent denominators), and **three** negative controls run
alongside, one per axis on which a membership-equivalent rival can differ. Each
must agree with gold on membership everywhere and disagree on `srepr`; if the
first two ever failed to discriminate, the structural leg would be decoration on
that axis and the gate fails.

* *collapse* — the factor list replaced by a single product factor. Probes the
  list's **length/grouping**.
* *re-present* — each member replaced by a different expression of equal value at
  every probed index. Probes each member's **identity** — the axis a value-only
  carrier leaves free, and therefore the one §2.3 is about. The collapse control
  cannot see it: re-presenting keeps the list's length, its order, and every
  index the answer picks out.
* *narrow-anyway* — on the settled-zero shape, keep the domain down to the zero
  collection regardless (the previous, unconditional model). Probes the **shape**
  the keep leg is allowed to depend on, i.e. §2.4. The node the real callees
  build for an identically zero numerator excludes no index, so the rival keeps
  exactly the same ones; where the domain is not already canonical the `&`
  re-evaluates it and the object differs. Where it IS already canonical the rival
  is genuinely invisible, so this control's requirement is **≥1 family with
  bite**, not "0 mute" — asserting no-mute would be asserting something false
  about a canonical domain.

The generator emits some factors `solve_linear` cannot solve (an occasional
expanded quadratic), because a list of purely linear factors lands on the
naked-index branch where a factor's identity is genuinely unobservable and the
member-identity control would have nothing to exhibit. Family 4 of the seven
asserted families has exactly that shape, so it is in-distribution.

Measured at the pinned seed (in-container, gold applied, exit 0): 74428 membership
compares over 4009 families, `srepr` equal on all 409 settled families, collapse
control discriminating on all 115 eligible families, re-present control
discriminating on all 267 eligible families, 0 mute on either; and on the 2
settled-zero families the shape-aware shadow matches gold exactly while the
narrow-anyway rival differs on 1 of them (the unevaluated-domain one — measured
`ImageSet(Lambda(n, n/2), Range(0, 6, 1))` against gold's
`FiniteSet(0, 1/2, 1, 3/2, 2, 5/2)`, same six members) and is invisible on the
other.

Families whose `imageset` frame is **not injective** on the probed indices (in the
limit, a constant real part) are skipped by the *membership* leg only, and the
count is reported. The reason is well-posedness, not convenience: that leg asks
the shadow which *index* survived and asks gold whether the *value* at that index
is in the reported set, and those coincide only when distinct surviving indices
carry distinct values. The predicate is decided from the family alone, before
either side is consulted, so it cannot filter on who won — and the *structural*
leg still compares those families in full, on the whole assembled object.
