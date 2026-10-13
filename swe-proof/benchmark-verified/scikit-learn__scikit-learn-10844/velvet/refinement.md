# refinement.md — scikit-learn__scikit-learn-10844

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `fowlkesCoeffSquared` `do` block) and `patch.diff` (the gold patch). Each
step is tagged **R** (type refinement; state the bijection), **A-consumed**
(proof uses an axiom's `ensures`), **A-reference** (a deep model validated ==
the real callee by G-AX), or **I** (identical concrete op). Every step is R, A,
or I; no kind-3 (changed-inexpressible) op.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`);
the numeric callee reference is audited by **G-AX** (`axiom_check.py`); the
narrative by **G-EQ**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## The fix — `fowlkes_mallows_score` (`sklearn/metrics/cluster/supervised.py:787`)

Gold hunks:
```
- c = contingency_matrix(labels_true, labels_pred, sparse=True)
+ c = contingency_matrix(labels_true, labels_pred,
+                        sparse=True).astype(np.int64)
  tk = np.dot(c.data, c.data) - n_samples
  pk = np.sum(np.asarray(c.sum(axis=0)).ravel() ** 2) - n_samples
  qk = np.sum(np.asarray(c.sum(axis=1)).ravel() ** 2) - n_samples
- return tk / np.sqrt(pk * qk) if tk != 0. else 0.
+ return np.sqrt(tk / pk) * np.sqrt(tk / qk) if tk != 0. else 0.
```

The two hunks fix ONE behavior — the int-overflow that turns the score into
`nan`. Hunk (a) `.astype(np.int64)` makes the aggregates exact wide integers;
hunk (b) reassociates the arithmetic so the overflowing product `pk * qk` is
never formed (it divides first, multiplying two in-range ratios).

The impl region returns TWO observables, and the map covers both: the VALUE the
patched expression computes, and the PLAN — a first-class description of WHICH
combination of the aggregates line 859 performs (mapping.md §1, §2). The second
observable exists because the first cannot see the bug: over exact arithmetic
`tk/sqrt(pk*qk)` and `sqrt(tk/pk)*sqrt(tk/qk)` denote the same number, so no
clause about the returned number alone distinguishes the pre-patch line from the
patched one. What distinguishes them is the intermediate `pk*qk` that only one of
them materialises, and materialisation is a property of the expression, so it is
the expression that has to be returned.

| # | Solution.lean impl op (`fowlkesCoeffSquared`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | params `(width : Nat) (agree spreadA spreadB : Word width)`, read through `.toExact` | `tk`, `pk`, `qk` as they sit in the contingency matrix's integer dtype (lines 854-858) | R | fixed-width integer scalars ↔ `Word width` register contents, with `.toExact` the promotion into arbitrary precision (mapping.md §2). The `inWord` requires say the register holds the aggregate, so `.toExact` is the mathematical integer on every admissible input; what the carrier retains is that the aggregates' own multiplication wraps. Modelling them as unbounded `Int` would erase precisely the machine fact this fix is about — see the carrier note in the discriminating-clause section. G-CONF recomputes `(tk,pk,qk)` from real label arrays through lines 854-858; G-AX executes the register carrier against real `np.int64` multiplication. |
| 2 | `let p : RatPlan := .zeroThen (.read .agree) (.mul (.ratio (.read .agree) (.read .spreadA)) (.ratio (.read .agree) (.read .spreadB)))` | the SHAPE of patched line 859, `np.sqrt(tk / pk) * np.sqrt(tk / qk) if tk != 0. else 0.` | R | structural refinement of an expression, not of a value: `.read k` ↔ the occurrence of aggregate `k`; `.ratio` ↔ the `/` at that position; `RatPlan.mul` ↔ the `*` between the two roots (squared: `(sqrt x * sqrt y)^2 = x*y`, so the outer multiply survives squaring in place — mapping.md §3); `.zeroThen (.read .agree) …` ↔ the `if tk != 0. else 0.` guard, which is part of the expression and not a wrapper around it — it answers `0` on a triple whose agreement count vanishes *without evaluating the quotients*, which is what the real line does. The plan is exactly the gold expression's tree with the two roots peeled: the guard, then two `tk/·` ratios multiplied. No integer product node, because gold line 859 materialises no integer product. |
| 3 | `let ra := (agree.toExact:Rat) / spreadA.toExact` | `tk / pk` (inside patched line 859) | I | identical concrete op: integer/integer exact ratio. `Rat` division transliterates to the real `tk/pk` (a float ratio that does not overflow — `tk,pk ≤ n^2 < 2^63`). Note the operands are the PROMOTED values: this step has left the fixed-width carrier, which is what makes it safe. |
| 4 | `let rb := (agree.toExact:Rat) / spreadB.toExact` | `tk / qk` | I | as #3. |
| 5 | `let v := if agree.toExact = 0 then 0 else ra * rb` | `... * ... if tk != 0. else 0.` | I + R | the multiply of the two ratios is the I op; the `tk != 0.` short-circuit ↔ `agree = 0 → v = 0` (R, mapping.md §2). The returned `v` is the SQUARED score (mapping.md §3); the model carries the square so the unchanged `np.sqrt` is peeled. |
| 5a | any `Int`- or `Rat`-valued step the impl region performs on `.toExact` values (here #3-#5; in a candidate rival, e.g. `spreadA.toExact * spreadB.toExact`) | arbitrary-precision arithmetic on scalars taken OUT of the array — `int(pk) * int(qk)`, `tk / pk` — never an op on the array's own integer dtype | R | mapping.md §2, the promoted-operand row. This is the leg that decides how a candidate routine is refined, so it is stated as its own step: `.toExact` is the exit from the register, and exact `Int`/`Rat` arithmetic has no width, so its counterpart must have none either. Refining a promoted-operand step into a fixed-width op would attribute wrapping to `Int`, which does not wrap, and would identify the pre-patch routine with a routine the model separates from it. The fixed-width multiply of two aggregates is a DIFFERENT model op (`instMulWord`, row below), and that is the one the pre-patch line performs. |
| 5b | the returned pair under the tie conjunct `p.value width agree.toExact spreadA.toExact spreadB.toExact = some v` | the SHORT-CIRCUIT of patched line 859 (`… if tk != 0. else 0.`) — as an operation of the expression, not a wrapper around it | R | this is the leg that decides how a candidate routine's VALUE expression is refined, so it is stated as its own step. `Rat` division is TOTAL (`x / 0 = 0`), so on an admissible triple whose spread vanishes an unconditional product of quotients denotes the required `0`: the number is right, and no clause about the number can say whether the quotients were formed. The PLAN says: `.zeroThen` answers before dividing, an unguarded plan yields nothing there. The tie makes the returned number the returned plan's number at this call's own width and aggregates, so a routine satisfying this spec HAS decided the degenerate case ahead of its quotients and its repo counterpart keeps the `if tk != 0.` guard. Refining an unconditional value expression into an unguarded repo expression attributes to the routine a step its own plan denies, and produces `nan` where the routine returns `0`: G-AX (`check_degenerate_short_circuit`) executes both shapes of the real callee arithmetic at the admissible aggregates `(0, 0, 30)` and G-CONF counts the real label arrays where it happens. |
| 6 | `return some (p, v)` | line 859 `return`s the (finite) score computed by that expression | R | `some (p, v)` ↔ the function returns a finite representable score reached by combination `p`; `none` ↔ it returns no number (`nan`). (mapping.md §2.) |
| — | the SQUARED value `agree^2/(spreadA*spreadB)` vs `(np.sqrt(tk/pk)*np.sqrt(tk/qk))^2` | the outer `np.sqrt` (unchanged callee) | A-reference | the single positive square root is peeled by squaring: `score = sqrt(v)`. The model pins `v = tk^2/(pk*qk)`; G-AX validates `(np.sqrt(tk/pk)*np.sqrt(tk/qk))^2 == tk^2/(pk*qk)` on the REAL numpy. NOT a consumed axiom — the relation is a squaring identity (mapping.md §3, directive 7). |
| — | `truncW` / `instMulWord` (the register carrier) vs the machine's own fixed-width integer multiply | `pk * qk` as line 859 computes it pre-patch, on fixed-width operands | A-reference | the pure region models an aggregate as register contents whose multiplication truncates back into the register. G-AX (`check_register_reference`) executes that model against REAL `np.int64` multiplication on ~20k pairs spanning the signed range and requires exact agreement, plus non-vacuity of the wrap and in-range exactness. At the F2P witness the register product of the two spreads wraps NEGATIVE, which is the same event that makes the real pre-patch `np.sqrt(pk*qk)` a `nan`. |
| — | `inWord` / `IntPlan.value` / `RatPlan.value` (the pure region) vs a fixed-width integer register | the machine arithmetic lines 854-859 run on | A-reference | the pure region models "an integer step has a value only while it fits the word". G-AX transliterates it and executes it at width 64 against the real `np.int64`: at the F2P aggregates real `pk*qk` wraps and `np.sqrt` gives `nan` at exactly the input where the product-first plan has no value, while the returned plan and the patched formula are both fine (mapping.md §3). So the model's partiality is the machine's failure. |

## The discriminating clause (what the bug violates)

The behavior the F2P test `test_int_overflow_mutual_info_fowlkes_mallows_score`
demands is `assert_all_finite(fowlkes_mallows_score(x, y))` — the score must be
a **finite representable number**, not `nan`.

Mathematically `tk / sqrt(pk*qk)` and `sqrt(tk/pk) * sqrt(tk/qk)` are equal over
the reals — a theorem, not a limitation of this encoding. It has a consequence
that decides the shape of the whole spec, and the consequence has to be stated
precisely, because a slightly-too-strong reading of it is what a previous revision
of this document got wrong:

**Over an EXACT-INTEGER carrier, no clause about the returned number can separate
the two routines** — and that is a defect of the carrier, not a fact about the
routines. If the aggregates are unbounded `Int`, then `spreadA * spreadB > 0`
follows from the sign requires by a theorem, the overflow that IS this bug is
unrepresentable, and the two associations are pointwise-equal FUNCTIONS. Any
postcondition of the form "the result equals `f(agree, spreadA, spreadB)`" is then
satisfied by both, and no strengthening of the value clause can help: a rival that
divides by `spreadA * spreadB` is *provably* the shipped routine. A spec that
tried to separate them by value on that carrier would have to smuggle in a
hand-written range test, and then the discriminator is the smuggled test rather
than anything the spec forces.

So the model is given the machine fact instead of being asked to work around its
absence. The aggregates arrive as REGISTER CONTENTS (`Word width`), whose own
multiplication (`instMulWord`) truncates back into the register; `.toExact` is a
promotion off that carrier. On this carrier `(spreadA * spreadB).toExact < 0` is
SATISFIABLE — it holds at the F2P witness — so the value clause is no longer
blind: a routine that assembles its answer through a register product of two
aggregates returns a different number than the coefficient exactly where that
product outgrows the register, and the existing `0 ≤ v` and exact-value conjuncts
reach that behaviour on their own, with no test smuggled in and no clause naming
any rival. Both observables therefore discriminate:

* **the VALUE**, because the carrier makes the wrap representable;
* **the PLAN**, because materialisation is a property of the expression.

Two carriers means two multiplications, and a candidate routine is refined by
which of them its text uses (mapping.md §2, promoted-operand row; step 5a above).
This is the whole content of the correspondence for this instance, so it is worth
stating as a pair of measured facts about the shipped spec rather than as advice:

* a routine that forms `spreadA * spreadB` on the REGISTERS and divides into that
  register's content **does not verify** — the content is `truncW width (·*·)`,
  which the exact-value conjunct cannot equal wherever the product leaves the
  word (this is `Solution_prepatch.lean`, and it is the reject case
  `prepatch-product-first-plan`). Its repo counterpart is the pre-patch line;
* a routine that promotes both spreads and forms `spreadA.toExact *
  spreadB.toExact` **does verify** — and it must, because that is a different
  routine: an `Int` product has no width, so its repo counterpart multiplies
  scalars read out of the array (`int(pk) * int(qk)`), is finite at the failing
  scale, and returns the same coefficient the gold line returns. Refining such a
  step into an op on the array's integer dtype would be the correspondence error
  the two-carrier model exists to prevent: it would report a routine as the
  pre-patch line on the strength of a multiplication the model says is exact.

So the spec separates the routines by CARRIER, not by evaluation order alone:
what it forbids is reaching the coefficient through a fixed-width product of
aggregates, by either observable, and what it permits is any assembly that
divides first or promotes first.

The plan clause is the last postcondition conjunct:

```
∀ (w : Nat) (a b c : Int), 2 ≤ w → 0 ≤ a → a ≤ b → a ≤ c →
  inWord w a → inWord w b → inWord w c →
  p.value w a b c
    = some (if a = 0 then 0 else (a : Rat) * a / ((b : Rat) * c))
```

— the returned plan must denote the coefficient at EVERY machine word width that
holds the three aggregates, and on ALL aggregate triples that width holds, not
just the ones of the call at hand. This admits exactly the plans that materialise
no integer product AND decide the no-agreement case before they divide:

* **(soundness)** the shipped plan satisfies it — every integer step is a bare
  `.read`, so no step can leave the word, and each `.ratio` yields an exact
  quotient; the two quotients multiply to `a*a/(b*c)`, and on a triple whose
  agreement count vanishes the `.zeroThen` guard answers `0` before either
  quotient is formed. This is discharged in the `prove_correct` body, and
  independently checked against the real machine by G-AX at width 64 and at
  widths 3..16.
* **(strength, materialisation)** any plan containing an `IntPlan.mul` violates
  it. Fix a width `w ≥ 2` and take `a = b = c = m = 2^(w-1) - 1 ≥ 1`, all in the
  word and satisfying the ordering hypotheses. Every integer product a plan can
  form from these is at least `m*m > m`, outside the word, so `IntPlan.value` is
  `none`, so `RatPlan.value` is `none ≠ some _`. There is no width at which a
  product-forming plan escapes, which is why the clause is quantified over `w`
  instead of instantiated at 64. (Instantiating it at 64 would also name the
  dtype hunk (a) selects; quantifying keeps the artifact silent about the
  width — mapping.md §2.)
* **(strength, the degenerate triple)** the quantified domain contains
  `(a, b, c) = (0, 0, 0)` — admissible, and a real clustering (mapping.md,
  admissible-input frame) — where the clause demands `some 0`. A plan that forms
  its quotients unconditionally yields `none` there, so the short-circuit is
  forced by the clause and is not a stylistic choice: `.zeroThen` must guard on
  the AGREEMENT count specifically, since guarding on a spread instead leaves
  `(0, b, 0)` with `b ≠ 0` unanswered.

### Reading a candidate routine — which observable carries its arithmetic

The postcondition returns a PAIR, and its two components are tied by a clause and
not by a reading:

```
p.value width agree.toExact spreadA.toExact spreadB.toExact = some v
```

The number a routine returns is the number its own returned plan yields, at the
width and the aggregates of the call. Three consequences fix how a candidate
implementation of this spec is refined into repo text. Each is stated because each
has been a live source of correspondence error on this cell.

1. **The value expression is not a routine's arithmetic; its plan is.** `Rat`
   division is total, so on an admissible triple whose spread vanishes an
   unconditional `ra * rb` denotes the same rational as a guarded one. Two impls
   differing only in that guard return the SAME PAIR everywhere on the admissible
   domain — machine-checked as an identity of the two returned pairs, not assumed
   (the identity record below) — and Lean is extensional, so NO postcondition can
   separate them. They are therefore one routine, not two, and its arithmetic is
   the one its plan describes: with the short-circuit, because `.zeroThen` is in
   the plan. Its repo counterpart keeps `if tk != 0. else 0.`; dropping the guard
   yields `nan` at that triple (G-AX) where the routine returns `0`, so an
   unguarded refinement refines nothing that satisfies this spec.
2. **Promotion off the register is legitimate; arithmetic left in the register is
   not.** A step on `.toExact` values has left the carrier and its counterpart is
   arbitrary-precision arithmetic on scalars out of the array (step 5a, mapping.md
   §2). A refinement of such a step must perform the promotion too — `int(pk) *
   int(qk)`, not `pk * qk` on the array dtype — and a plan may not materialise an
   aggregate product at all, at any width.
3. **Sameness of the returned pair is sameness of routine.** The plan and the
   value are the whole result. Implementations that agree on both across the
   admissible domain are the routine their common plan describes, and differences
   confined to intermediate expressions the exact carrier cannot observe are not
   differences in the routine being refined.

**Identity record (measured, not argued).** Two rivals of the shipped impl are
identities of the RETURNED PAIR on the admissible domain: (a) gold's plan and
ratios with the zero test dropped from the value expression, and (b) gold's plan
with the value reached through the promoted exact product `spreadA.toExact *
spreadB.toExact`, also without the zero test. Both return the same plan term and
the same rational as the shipped impl at every admissible triple — checked in
Lean as an equality of the two returned pairs during authoring, and re-executed
on every G-AX run over the transliterated model
(`check_degenerate_short_circuit`, the value-slot sweep: all three value shapes
agree on every triple drawn, including the degenerate ones). So no clause about
either observable can reject them — which is why the accept lane of
`properties.py` carries them as positive controls
(`pos-control-unconditional-value-arithmetic`,
`pos-control-promoted-product-value`) rather than the reject lane, and why the
obligation that governs them is the tie plus rule 1 above: their faithful repo
counterpart is the GUARDED, promoted expression, which is the gold line. The
control in the other direction was measured too: the register-product route and
the product-first plan are separated by the spec on both observables, and
`Solution_prepatch.lean` fails on them.

`Solution_prepatch.lean` reproduces the pre-patch line 859 as what it is: it forms
the product of the two spreads IN THEIR REGISTERS and divides by that content, and
it reports the corresponding product-first plan, with NO hand-written range check
anywhere in its `do` block. It **fails to verify** (G-DIFF), and now for two
independent reasons, one per observable: its plan has no value at the widths where
the materialised product leaves the word (e.g. width 4 with `(a,b,c) = (1,7,7)`,
where the denominator product 49 does not fit), and its value is not the
coefficient at the magnitudes where the register product wraps — where the wrap
goes negative it is not even nonnegative, so it fails `0 ≤ v` as well. The byte-identical spec view is
enforced by `same_spec`; the plan choice lives entirely inside the prepatch's
`impl` `do` block.

## No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operation that genuinely changed — the
re-association that avoids the overflowing product — is modeled DIRECTLY twice
over: as the divide-first computation in the `do` block (steps 3-5, all I) and as
the returned plan whose nodes are the nodes of gold line 859 (step 2, R). Its
representability consequence is pinned by the plan clause (step 2 + the
discriminating-clause section) and by the `some`/`none` post-state (step 6, R).
The unchanged `np.sqrt` is the only callee and is handled by squaring
(A-reference), not by a consumed axiom. There is no module-level `axiom`.

## verify(Solution) ⇒ resolved

`fowlkesCoeffSquared` verifies only if, for every admissible input, it returns
`some (p, v)` where `v` is `agree^2/(spreadA*spreadB)` (or `0` when `agree = 0`),
`p` is a combination of the aggregates that denotes that coefficient at every
machine word width holding them — hence, by the strength argument above, a
combination that materialises no product of aggregates and decides the
no-agreement case before it divides — AND `v` is the number `p` itself yields at
this call's width (the tie), so the combination `p` describes is the one the
routine performed and not a claim beside it. Because the aggregates are
carried in registers whose multiplication wraps, the value requirement is itself
discriminating: it forces a routine to reach the coefficient either by dividing
before it multiplies or by promoting off the register carrier first, and rules out
assembling it through a register product of aggregates; and the tie forbids the
remaining loophole, a routine whose plan short-circuits while its refinement
divides unconditionally — under the tie that refinement is unfaithful, and the
real callee returns no number where the routine returns `0` (G-AX
`check_degenerate_short_circuit`, G-CONF's vanishing-spread count). That is the
patched line 859 and not the pre-patch one, which is refuted on both
observables. By R
(register carrier ↔ fixed-width scalars, `.toExact` ↔ the exit from the register,
promoted-operand arithmetic ↔ arbitrary-precision arithmetic on scalars out of
the array (step 5a), square↔root,
`some`↔finite, plan↔expression shape) the verified routine is the patched divide-first score; by G-AX the squared
model equals the real patched formula, the plan semantics agree with real
`np.int64` behaviour, the modelled register multiply IS real `np.int64`
multiplication (checked pair-by-pair, with the wrap shown reachable), and both the
product-first plan and the register route fail exactly where the real pre-patch is
`nan`; by G-CONF both observables agree with `patch.diff`'s
behaviour on ≥10^5 inputs plus the overflow witness. Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement —
and the gold patch resolves (G-RESOLVE). The trust points are exactly: refinement
fidelity (this doc, G-EQ + G-CONF), the square-root reference soundness, and the
fidelity of the machine-word model — both the partial plan semantics and the
wrapping register carrier (all G-AX). There are no consumed axioms.
