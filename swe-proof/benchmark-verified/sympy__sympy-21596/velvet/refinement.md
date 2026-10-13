# refinement.md — sympy__sympy-21596

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`restrictToRealValues` `do` block) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement; state the bijection), **A-consumed** (proof uses
the axiom's `ensures`), **A-reference** (deep model validated == real callee by
G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
A-reference legs + this narrative are audited by **G-AX** and **G-EQ**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The change site — the `other == S.Reals` branch of `intersection_sets(self, other)`

The change rearranges how the index set `base_set` is restricted before the final
`imageset`, and it introduces a helper that resolves a factor list one factor at a
time. Before, the imaginary-part leg *subtracted* an exclusion set built as a
`FiniteSet` of a **tuple** (which excludes nothing), and the denominator loop
iterated the wrong expression. After (`intersection.py`, all line numbers in the
patched file):

```
      8: from sympy.simplify.radsimp import numer
284-294: def _solution_union(exprs, sym):
             sols = []
             for i in exprs:                                  # ONE node per factor
                 x, xis = solve_linear(i, 0, [sym])
                 if x == sym:
                     sols.append(FiniteSet(xis))              # the index, NAMED
                 else:
                     sols.append(ConditionSet(sym, Eq(i, 0)))  # unresolved condition
             return Union(*sols)
309-313:     if im.is_zero:
                 # allow re-evaluation of self in this case to make
                 # the result canonical
                 pass                                         # NOTHING is kept
314-315:     elif im.is_zero is False:
                 return S.EmptySet                            # before every changed line
316-317:     elif ifree != {n}:
                 return None                                  # before every changed line
318-324:     else:
                 base_set &= _solution_union(Mul.make_args(numer(im)), n)   # keep the zeros of im
    326: base_set -= _solution_union(denoms(f), n)            # dedented: runs on the
                                                              # `pass` leg TOO
    327: return imageset(lam, base_set)
```

The four-way settling chain (309–318) is CONTEXT — the patch does not touch it; the
hunk's own header (`@@ -303,22 +316,14 @@`) opens on `elif ifree != {n}:` as an
unchanged line. What the patch changes is the `else` leg's body (a subtraction that
removed nothing becomes the `&=` keep at 323–324) and the denominator removal
(the old per-denominator loop, which re-ranged over `Mul.make_args(im)`, becomes
line 326).

That context nevertheless decides which changed line runs, which is why the spec
has to carry it:

* the keep step at 323–324 is CONDITIONAL — it happens on the `else` leg only, and
  on the `if im.is_zero:` leg the body is `pass`, so `base_set` is not narrowed at
  all;
* line 326 is at the chain's own indentation, so the changed removal runs on BOTH
  legs that fall through;
* only two of the four outcomes fall through. The other two `return` before every
  changed line and are an unchanged frame (directive 5).

The two that fall through are the two shapes of the `ImaginaryPart` input
(mapping.md §2.4). A model with one unconditional keep step cannot state what the
patched code does on the first of them, which is the defect this revision fixes
(§B.2, "A second correction").

## The carrier: the ASSEMBLY, not only the surviving indices

The observable this instance is judged on is the OBJECT line 327 hands back, and
the failing test compares objects (`FiniteSet(-1, 1)`, `ImageSet(Lambda(x, x/2),
ConditionSet(n, Eq(n**2 - n/2 - 1/2, 0), Integers))`, `S.EmptySet`, …). Line
288's loop makes that object a function of the factor LIST it is given: a factor
`solve_linear` can solve contributes a NAMED index (`FiniteSet`, line 291), one it
cannot contributes an unresolved condition (`ConditionSet`, line 293). Two factor
lists picking out the same indices therefore produce DIFFERENT objects — for the
issue's own family, `[n-1, n+1]` gives `FiniteSet(-1, 1)` and the single factor
`(n-1)*(n+1)` gives `ConditionSet(n, Eq((n-1)*(n+1), 0), Integers)` — and only the
first passes the test. An index-set-only post-image cannot see that difference, so
`Solution.lean` models the answer as an `IndexReport`: `given` / `zerosOfAny` /
`meet` / `apart`, mirroring branch entry, line 294, line 323 and line 326, with
`reported` retaining the membership reading as a second, weaker `ensures`.

`imageset` (line 327) is structure-preserving on this data — the image of a
`FiniteSet` is a `FiniteSet` of images, the image of a `ConditionSet` is an
`ImageSet` over it — so the assembly is what the caller ends up reporting.

The same argument reaches one level further down, into a `zerosOfAny` payload's
MEMBERS, and that is the second place the carrier has to be as fine as the repo's.
Line 293 embeds the factor `i` ITSELF in the node it builds, so the object depends
on each listed factor's identity and not merely on the indices that factor picks
out: `n**2 - n/2 - 1/2` and `(n-1)*(2*n+1)/2` are value-identical over the probed
integers and different objects by `srepr`, and they build different
`ConditionSet`s. A factor is therefore modeled as an identity-bearing `Factor`
handle, with the value reading supplied as a separate input
`valueOf : Factor → Int → Option Rat` — so clause (2) keeps its full extensional
strength on the surviving indices while clause (1) pins the factors themselves.
Both lists carry it, because the one helper at 284–294 resolves both legs
(mapping.md §2.3).

| # | Solution.lean impl op (`restrictToRealValues`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameter `domain : Set Int` | `base_set` on branch entry | R | symbolic integer index set ↔ membership predicate `λ n, n ∈ B` (mapping.md §2). |
| 2 | parameter `imaginaryPart : ImaginaryPart` | the settled outcome of `im.is_zero` — the chain at 309–318 — together with `Mul.make_args(numer(im))` on the `else` leg, line 324 | R | TWO shapes, because two of the four outcomes reach an assembly. `.zeroThroughout` ↔ the `if im.is_zero:` leg (309–313), whose body is `pass` (313): no factor of `im` is resolved and `Mul.make_args(numer(im))` is never formed, so that shape carries NO list. `.factors gs` ↔ the `else` leg (318–324), whose `gs` is `Mul.make_args(numer(im))`. Each factor `i` ↔ its own identity-bearing handle; the list's ORDER, LENGTH **and each MEMBER'S IDENTITY** are part of the carrier because line 288 emits one node per element and line 293 embeds that element (mapping.md §2.3). Modeling `numer(im)` (not `im`) matches line 324: a zero of `im` is a zero of its numerator, and the denominator has its own leg. The other two outcomes — `return S.EmptySet` (314–315) and `return None` (316–317) — return BEFORE every changed line, so they are an unchanged frame (directive 5) and the carrier deliberately gives them no shape (mapping.md §2.4). |
| 3 | parameter `denominators : List Factor` | `denoms(f)` — line 326 | R | each denominator `d` ↔ its own handle, same carrier — the same helper resolves both legs, so line 293 fires for either list. |
| 3a | parameter `valueOf : Factor → Int → Option Rat` | `i.subs(n, k)` — how `solve_linear`/`Eq` read a factor's value | R | `valueOf g k = some q` iff `g.subs(n,k)` is the Rational `q`, `none` iff it is no rational value (`zoo`, `nan`). TOTAL and EXACT on values; NOT injective, and deliberately not the factor's carrier (mapping.md §2.3). |
| 4 | `.given` (the accumulator's initial value) | `base_set` as the left operand of line 323 | I | the domain enters the assembly unmodified, as the ATOM (mapping.md §2.2). |
| 5 | `.zerosOfAny gs` | `_solution_union(exprs, sym)` — lines 284–294 | A-reference | the deep model of the helper: one contribution per LISTED factor, collected (`Union`, line 294), each factor's contribution denoting its zero set (`FiniteSet(xis)` line 291 / `ConditionSet` line 293). G-AX validates THREE legs against the real callees: the membership (`k ∈ _solution_union([g₁…gₘ], n)` iff some `gⱼ` vanishes at `k`), the per-factor structure (a two-factor list and the one-element list of their product denote the same indices but are different objects by `srepr`), and each member's IDENTITY (two value-identical, `srepr`-different factors build different objects, because line 293 embeds the factor itself). |
| 6 | `acc := match imaginaryPart with \| .zeroThroughout => acc \| .factors gs => .meet acc (.zerosOfAny gs)` | the whole `if im.is_zero: … pass … else: base_set &= _solution_union(Mul.make_args(numer(im)), n)` chain — lines 309–324 | A-reference + I | the **changed** op, and the SHAPE decides whether it happens at all. On `.factors`, `meet` is the `&=` (**I** on membership: `k ∈ (B & S)` ↔ `k ∈ B ∧ k ∈ S`); that its right operand is the per-factor collection of the IMAGINARY numerator's factors, THOSE FACTORS AND NOT OTHERS OF EQUAL VALUE, is the discriminating content. On `.zeroThroughout` the leg's body is `pass` (309–313), so `acc` is left as the ATOM `given` and NO node is built over it: `base_set` reaches line 326 exactly as bound. Standing a keep node there instead — even one whose collection excludes no index — is a caller-VISIBLE difference, measured `FiniteSet(0, 1/2, 1, 3/2, 2, 5/2)` vs `ImageSet(Lambda(n, n/2), Range(0, 6, 1))` on a constructed family of that shape (mapping.md §2.4), and is shipped as the reject case `weak-keeps-when-settled-zero`. Keeping (`&=`) rather than removing, on the leg that keeps, is the first of the two behaviours the change alters. |
| 7 | `acc := .apart acc (.zerosOfAny denominators)` | `base_set -= _solution_union(denoms(f), n)` — line 326 | A-reference + I | `apart` is the `-=` (**I** on membership); its right operand is the per-factor collection of `denoms(f)` — the denominator list itself, those denominators and not others of equal value, which is the second behaviour the change alters (the earlier loop resolved the imaginary part's factors inside the denominator loop). Applied AFTER step 6, matching 323 → 326, and applied UNCONDITIONALLY: line 326 sits at the `if`/`elif`/`else` chain's own indentation, outside it, so it runs on the `pass` leg as well — which is why this step is outside the `match` of step 6. |
| 8 | `return acc` | `return imageset(lam, base_set)` — line 327 | R | the `imageset(lam, ·)` wrapper is unchanged pre/post-change and structure-preserving on this data; the assembled index set is what it maps (mapping.md §2, directive 5: an unchanged surrounding frame, carried through). |
| 9 | `ensures reported domain valueOf out = realIndices domain valueOf imaginaryPart \ anyVanishes valueOf denominators` | the membership of the object at line 327's argument | A-reference + I | the membership consequence of steps 4–7, with the post-image following the shape exactly as step 6 does: `realIndices` is `domain` on `.zeroThroughout` (every member is already real, nothing is dropped) and `domain ∩ anyVanishes valueOf gs` on `.factors gs`; the leg `conformance_check.py` probes point-by-point. It is implied by the assembly clause, so it adds no constraint — it is retained because it is the leg with a direct point-by-point mechanical check. |

## A. The two independently-changed behaviours (G-DIFF)

`test_imageset_intersect_real` exercises both legs, and they are independently
observable, so there are two failing prepatch twins (one per behaviour). Each
keeps the spec byte-identical (`same_spec`) and changes only the impl region.

- **Keep leg** (`Solution_prepatch.lean`): before the change the imaginary-part
  leg subtracted a `FiniteSet` of a tuple (lines 306–311 @ base_commit), which
  removes nothing — modeled as the keep step being absent on BOTH shapes. The
  twin's assembly is `apart (given domain) (zerosOfAny denominators)` whatever
  the imaginary part's shape, which fails the assembly clause (the `meet` node is
  missing) and the membership clause (non-real indices survive) on the `.factors`
  shape. Note that on `.zeroThroughout` the twin is RIGHT — that is what the
  patched branch itself does there — so the twin's failure is located exactly on
  the shape the change speaks for, and the verifier reports it as the
  `.factors`-shape case only. Discriminated by the family `n + (n-1)(n+1)i` over
  ℤ, where the twin keeps every integer and the test asserts `FiniteSet(-1, 1)`.
- **Apart leg** (`Solution_prepatch_2.lean`): before the change the denominator
  loop's inner comprehension re-ranged over `Mul.make_args(im)` instead of the
  denominator `i` (lines 312–321 @ base_commit), so denominator zeros were left
  in — modeled as the `apart` node being absent. The twin's assembly is the keep
  leg alone, `keptToReal imaginaryPart` — the atom `given` on `.zeroThroughout`
  and `meet (given domain) (zerosOfAny gs)` on `.factors gs` — where the clause
  requires an `apart` node at the top on BOTH shapes, line 326 being outside the
  chain. It therefore fails on both (verified: residual `⊢ False` in the
  `.zeroThroughout` case and in the `.factors` case). Discriminated by the
  families with `n`-dependent denominators (`n/(n-6)+…`, `n/(n²-9)+…`), where a
  pole survives.

## B. No kind-3 (inexpressible-changed-op) steps, and nothing deferred that the test observes

Every step is R, A-reference, or I; there is **no consumed axiom**. The operation
that genuinely changed — which collection is kept, which is removed, and that each
is resolved factor by factor — is modeled DIRECTLY (steps 5–7), including the
structure-determining data (the two factor lists, their roles, their order and
their per-element resolution). What is left to the unchanged callees is only their
INTERNAL canonicalization: which normal form `solve_linear` returns, how `Union`
flattens, how `FiniteSet` orders its elements. That residue is (a) unchanged by
the patch, (b) a function of the assembly the spec pins, and (c) validated
against the real callees by G-AX — including that it is DETERMINISTIC (`srepr`
stable across rebuilds), so pinning one assembly does not pin an accident of a
particular run.

This is a deliberate strengthening over the earlier version of this document,
which claimed the skeleton "need not" reproduce the canonicalization tower and
pinned only membership. That claim was too weak for exactly the reason §"The
carrier" gives: an implementation that produced one `ConditionSet` over the whole
imaginary part has the right membership on every input, satisfies a
membership-only post-image, and still fails the test. Measured: a harness run on
that shape records FAIL_TO_PASS 0/1 with PASS_TO_PASS 46/46.

### B.1 Measured refinement evidence

Every candidate assembly was replayed through the REAL callees (`solve_linear`,
`numer`, `denoms`, `Union`, `FiniteSet`, `ConditionSet`, `&`, `-`, `imageset`) on
all seven families the failing test asserts, and compared with the objects it
asserts. The frozen assembly matches **7/7** — which also validates the
measurement harness. Rival assemblies (families numbered in the test's assertion
order):

| assembly | fails family | example |
|---|---|---|
| drop the keep leg | 1,2,3,4,5,6,7 | `Integers` vs `FiniteSet(-1, 1)` |
| drop the apart leg | 5,6,7 | `FiniteSet(1/2, zoo)` vs `FiniteSet(1/2)` |
| collapse the factor list | 1,2,3,5,6,7 | `ConditionSet(n, Eq((n-1)*(n+1), 0), Integers)` vs `FiniteSet(-1, 1)` |
| merge the two lists into the keep leg | 7 | a non-empty `ImageSet` over a `Complement` vs `S.EmptySet` |
| swap the two lists' roles | 1,2,3,4,5,6,7 | `EmptySet` vs `FiniteSet(-1, 1)` |
| ignore the domain (start from all integers) | 3 | `FiniteSet(-1, 1)` vs `FiniteSet(1)` on the `S.Naturals0`-indexed family |
| skip the keep leg when the factor list is a singleton | 4 | `ImageSet(Lambda(n, n/2), Integers)` vs `ImageSet(Lambda(x, x/2), ConditionSet(n, Eq(n**2 - n/2 - 1/2, 0), Integers))` |
| echo the surviving indices by de Morgan | 1,2,3,4,5,6,7 | `Complement(Integers, Complement(Integers, FiniteSet(-1, 1)))` vs `FiniteSet(-1, 1)` |
| mask the domain leaf with a condition excluding nothing | 4 | a `Union` of an `ImageSet` over a `Complement` and an `Intersection`, vs `ImageSet(Lambda(x, x/2), ConditionSet(n, Eq(n**2 - n/2 - 1/2, 0), Integers))` |
| split the domain leaf and union the halves back | 4 | the same shape |
| re-present each keep-leg member as another factor of equal value everywhere | 4 | `ImageSet(Lambda(x, x/2), ConditionSet(n, Eq((n - 1)*(2*n + 1)/2, 0), Integers))` vs `ImageSet(Lambda(x, x/2), ConditionSet(n, Eq(n**2 - n/2 - 1/2, 0), Integers))` — identical membership at every probed integer; harness verdict FAIL_TO_PASS 0/1, PASS_TO_PASS 46/46 |

All eleven are rejected by the spec (`properties.py`, machine-checked with
discriminating witnesses), and each one's faithful counterpart would NOT resolve.
All eleven are stated on the `.factors gs` shape, which is the shape the seven
asserted families reach.

Three further reject cases live on the SHAPE SPLIT, and they are shipped on a
measured OBJECT divergence rather than on a measured resolve failure, because the
asserted families never reach the settled-zero leg (all seven have an unsettled
`im`; that is why the previous, unconditional model resolved):

| rival | what it does | evidence |
|---|---|---|
| `weak-keeps-when-settled-zero` | narrows the domain on `.zeroThroughout` too, by a collection excluding nothing | replayed on `imageset(Lambda(n, n/2), Intersection(S.Integers, Interval(0, 5), evaluate=False))`, whose keep collection is `UniversalSet()`: `ImageSet(Lambda(n, n/2), Range(0, 6, 1))` vs the branch's `FiniteSet(0, 1/2, 1, 3/2, 2, 5/2)` — same six members, different object |
| `weak-ignores-the-settled-shape` | uses `meet given (zerosOfAny [])` for the settled-zero shape — an empty list contributes nothing, so the indices are EMPTY | wrong on membership, not merely on the object: it drops every index where the branch keeps them all |
| `weak-swaps-the-two-shapes` | builds the keep node on `.zeroThroughout` and none on `.factors gs` | the `.factors` half is exactly the keep-leg twin, the row "drop the keep leg" above, which fails all seven families |

One further reject case, `weak-represents-a-denominator`, re-presents each member
of the APART leg's list and is shipped on the SYMMETRY of the shared helper rather
than on a measured resolve failure: the asserted families do not happen to observe
denominator syntax (measured — the only `n`-dependent denominator reaching line
293 belongs to the family asserting `S.EmptySet`, and a constant denominator's node
IS `S.EmptySet`), so the replay matches 7/7. An obligation on the keep leg alone
would nonetheless be asymmetric against the one helper that serves both legs, and
its faithfulness would rest on which families the suite asserts, so the obligation
is stated symmetrically and this case is labeled for what it is.

### B.2 Where the assembly clause is CONSERVATIVE

Pinning one assembly also refuses some reshapes that would resolve. Measured
(each replayed through the real callees on all seven asserted families):

* `meet given (apart (zerosOfAny gs) (zerosOfAny denominators))` on the
  `.factors gs` shape — the
  same three pieces regrouped. Rejected by the spec, but it matches all seven
  asserted objects, so its counterpart WOULD resolve.
* `zerosOfAny (gs ++ [<a factor vanishing nowhere>])` — an appended
  factor that never vanishes. Rejected by the spec; also matches all seven.
* `apart given noIndices` as the leaf, then the normal assembly — the real set
  algebra simplifies `X - EmptySet` to `X`, so this matches all seven too.
* re-presenting only the factors the callees CAN solve. On the line-291 branch the
  emitted node is the naked index and carries no syntax (measured: `n - 1`,
  `2*n - 2`, `1 - n` and `n/3 - 1/3` all build `FiniteSet(1)`), so such a
  counterpart matches all seven. Clause (1) refuses it anyway, because the member
  obligation is stated on the members and not on the callees' internal case split
  — see mapping.md §2.3 for why that is the right side to err on.

These are over-strict rejections, not detections of wrong implementations, and
they are recorded rather than shipped as reject cases (`properties.py`,
"SPEC-STRENGTH PROBES ... NOT shipped"): claiming they would fail the harness
would be false.

**Direction of the residual risk — corrected.** An earlier version of this
document asserted the risk was "SPEC-TOO-STRONG on caller-invisible regroupings,
never SPEC-TOO-WEAK". That was refuted by executed resolves: on the then-carrier a
factor was a value FUNCTION, so a value-preserving re-presentation of a leg's
members was provably the identity, and same-spec, verifying implementations of that
shape were run through the official harness and did NOT resolve (FAIL_TO_PASS 0/1,
PASS_TO_PASS 46/46). The claim was false because the carrier modeled a factor by
its values while the repo's observable carries the factor itself (mapping.md §2.3).
The carrier now distinguishes factors by identity and the two member-identity
reject cases pin it. What can honestly be said is narrower: the assembly clause
pins the ATOM, the two lists with their length, order and members, and the two
roles; the axes on which it is finer than the caller-visible object are ENUMERATED
above and each is a direction that can only refuse a rival, never admit one; and no
further axis on which a value-preserving or membership-preserving reshape stays
invisible to clause (1) is known. That is a bounded statement about what has been
probed, not a proof that none exists.

**A second correction — the SETTLED-ZERO shape was modeled wrongly.** An earlier
version of this document (and of the spec) carried the imaginary part as a single
factor list and made the keep step UNCONDITIONAL: `acc := .meet acc (.zerosOfAny
imFactors)`, with no shape to split on. Re-read against the patched source, that
is not what the branch does. The patched code reaches the changed lines through a
four-way settling of `im` (the chain at 309–318, itself unchanged context), and on
the leg where `im.is_zero` holds the body is `pass`: the
`&=` at 323–324 does not run, and `base_set` reaches line 326 exactly as bound at
231. The leg's own comment says why — "allow re-evaluation of self in this case to
make the result canonical" — so skipping the keep is the point of the leg, not an
optimization. The unconditional model was therefore UNFAITHFUL on that leg: it
required a `meet` node the branch does not build, and required it in a way no
faithful implementation of the settled-zero path could satisfy. Measured on a
constructed family of that shape, `imageset(Lambda(n, n/2),
Intersection(S.Integers, Interval(0, 5), evaluate=False))` — whose `im.is_zero` is
True and whose keep collection would be `UniversalSet()` — the branch answers
`FiniteSet(0, 1/2, 1, 3/2, 2, 5/2)` and a counterpart that narrows anyway answers
`ImageSet(Lambda(n, n/2), Range(0, 6, 1))`: same six members, different object.
The carrier now splits on the shape (`ImaginaryPart`), the keep step is under that
split, and the two failure directions it opens are shipped as reject cases
(`weak-keeps-when-settled-zero`, `weak-ignores-the-settled-shape`,
`weak-swaps-the-two-shapes`). Honest scope of the measurement: the divergence
above is an OBJECT divergence on a family constructed to have that shape, not a
recorded FAIL_TO_PASS flip — the seven families the failing test asserts all reach
the `else` leg, which is why the unfaithful model resolved and still passed
G-RESOLVE. What is corrected is the model's fidelity on a changed line the suite
does not exercise, and the two out-of-scope outcomes (`return S.EmptySet`,
`return None`) are recorded as unchanged frame rather than given a carrier
(mapping.md §2.4).

Both halves of that correction are now MECHANICAL, not narrative:

* `conformance_check.py`'s shadow follows the shape (it keeps nothing where
  `im.is_zero`), two settled-zero families are in its boundary list, and a third
  negative control — *narrow-anyway* — is the rejected model itself. Measured
  in-container with the gold patch applied, exit 0: the shape-aware shadow matches
  gold on `srepr` for both settled-zero families, and the narrow-anyway rival
  keeps the same indices and builds a DIFFERENT object on the one whose domain is
  not already canonical. On the canonical one it is invisible, which is why that
  control requires ≥1 family with bite rather than 0 mutes.
* `axiom_check.py` Fact 8 pins the callee-level premise on the BASE-COMMIT
  callees: the node built for an identically zero numerator is exactly
  `S.UniversalSet`, it contains every probed index, and `B` vs `B & UniversalSet`
  are `srepr`-different for a non-canonical `B`. Measured in-container, exit 0, 3
  family/domain pairs probed, 1 exhibiting the difference.

So "a keep node the branch does not build is caller-visible" is a checked fact
about the real callees, not an appeal to the leg's comment.

Four positive controls in `properties.py` show the freedom a faithful
implementation actually needs — any construction ORDER, any naming of intermediate
nodes, walking or re-binding the factor lists it was handed, and building the keep
leg by calling the shape function `keptToReal` instead of writing the `match` out —
is preserved: all four verify. The third is specifically the strictness bound on
member identity: it refuses a member PUT IN PLACE OF a handed-in factor, not an
impl that copies the list. The fourth is the strictness bound on the shape split:
the spec pins WHICH assembly each shape gets, not the syntax an implementation
uses to choose between them.

## C. verify(Solution) ⇒ resolved

`restrictToRealValues` verifies only if its answer IS
`apart (keptToReal imaginaryPart) (zerosOfAny denominators)` — that is, on the
`.factors gs` shape, the domain ITSELF kept down to the per-factor zero collection
of the imaginary numerator's OWN factors, and on the `.zeroThroughout` shape the
domain ITSELF with NO keep node over it, either of those taken apart from the
per-factor zero collection of the denominators themselves — and only if the
indices that assembly picks out are
`realIndices domain valueOf imaginaryPart \ anyVanishes valueOf denominators`. By
R (mapping.md §2: index set ↔ membership for the reading and ↔ the atom for the
object, factor ↔ its own identity with `valueOf` the separate value reading, the
unchanged structure-preserving `imageset` frame, and the settled outcome of
`im.is_zero` ↔ the two shapes, mapping.md §2.4) that assembly transliterates to
exactly lines 309–326 of the patched file — the keep step under the branch that
performs it and skipped where the branch says `pass`, then the unconditional
removal at the dedented line 326 — applied in that order, to those two lists,
holding those factors. By A-reference (G-AX) `zerosOfAny` denotes what
`_solution_union` (lines 284–294) BUILDS — per factor, and per factor's identity,
not per index set — and `reported` denotes the membership of the SymPy set algebra.
By G-CONF the transliteration agrees with the gold-patched
`imageset(...).intersect(S.Reals)` on fuzzed families, on membership AND on
`srepr`, with the factor-collapse variant as a negative control that agrees on
membership and disagrees on `srepr`.

So a model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and audited callees — and the gold patch resolves (G-RESOLVE). This
is stated as the conclusion of the enumerated legs above and not as a closed proof:
an earlier version of this document asserted it flatly, and it was refuted by
executed resolves on the axis §B.2 now records (a factor's identity was invisible
to the then-carrier). The claim rests on three trust points, not two:
deep-model/callee soundness (G-AX, now including the member-identity leg),
refinement fidelity (this document, G-EQ + G-CONF), and the completeness of §B.2's
enumeration of the axes on which the carrier is coarser or finer than the
caller-visible object — the third being the one that failed before and the one a
fresh audit should attack first.
