# mapping.md — scikit-learn__scikit-learn-10844

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 97523985b39ecde369d83352d7c3baf403b60a22`, states the
Lean↔Python type abstraction (the bijection G-CONF / G-AX use), and records
callee provenance.

Repo file under change: `sklearn/metrics/cluster/supervised.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `fowlkesCoeffSquared (width : Nat) (agree spreadA spreadB : Word width)` | the trailing computation of `fowlkes_mallows_score` (`sklearn/metrics/cluster/supervised.py:787`, body lines 852-859) | the modeled changed function — the routine that combines the three aggregates into the returned similarity score |
| `agree`   | `tk = np.dot(c.data, c.data) - n_samples` (line 856) | count of co-grouped element pairs (true positives `tk`), held in a machine register; `agree.toExact` is its value promoted to exact arithmetic |
| `spreadA` | `pk = np.sum(np.asarray(c.sum(axis=0)).ravel() ** 2) - n_samples` (line 857) | sum-of-squares aggregate of one partition's marginal group sizes, in a register; `spreadA.toExact` is its promotion |
| `spreadB` | `qk = np.sum(np.asarray(c.sum(axis=1)).ravel() ** 2) - n_samples` (line 858) | sum-of-squares aggregate of the other partition's marginal group sizes, in a register; `spreadB.toExact` is its promotion |
| `out : Option (RatPlan × Rat)` | the whole of line 859's returned expression: its VALUE (squared — the root is peeled, see §3) together with the COMBINATION the expression performs to reach it | the two observables of the changed line |
| the `Rat` component `v` | the value returned by the score expression on line 859, squared | the representable squared similarity coefficient |
| the `RatPlan` component `p` | the SHAPE of line 859's expression: which integer quantities it materialises from the aggregates, where it takes its ratios, and whether it decides the no-agreement case ahead of them. Gold line 859 is `np.sqrt(tk / pk) * np.sqrt(tk / qk) if tk != 0. else 0.` ⇒ `.zeroThen (.read .agree) (.mul (.ratio (.read .agree) (.read .spreadA)) (.ratio (.read .agree) (.read .spreadB)))` — the `if tk != 0.` guard is part of the expression's shape, and `.zeroThen` is that guard. The pre-patch line 859 is `tk / np.sqrt(pk * qk)` ⇒ `.ratio (.mul (.read .agree) (.read .agree)) (.mul (.read .spreadA) (.read .spreadB))` (squared, so `tk` is materialised twice on the numerator side exactly as `pk*qk` is on the denominator side). | the combination plan (see §2, machine-word row) |
| the tie conjunct `p.value width agree.toExact spreadA.toExact spreadB.toExact = some v` | that line 859's returned NUMBER is the number line 859's EXPRESSION computes — the value and the shape are two views of one expression, not two independent facts about the line | binds the two observables, so the returned plan is the routine's arithmetic and not an annotation beside it (§2, the total-division row; refinement.md step 5b) |
| `Aggregate.agree / .spreadA / .spreadB` | the three names `tk`, `pk`, `qk` that line 859 may read | a plan's read alphabet: line 859 reads no other quantity |
| `Word width` / `Word.toExact` | the fixed-width integer register an aggregate is held in / reading that register's content out into arbitrary-precision arithmetic — what Python's own `int` gives once a scalar leaves the array (`int(pk)`, or an `object`-dtype view of it). **`.toExact` is not a dtype selection.** Selecting a wider dtype re-registers the aggregate at a wider fixed width (a `Word 64` where the platform default may have been narrower) and leaves it in a register, where multiplication still wraps; the promotion is the step off the register carrier altogether, after which no width bounds anything | the aggregates' CARRIER, and the exit from it |
| `instMulWord` (`Word.mul`, via `truncW`) | multiplying two such registers with the machine's own fixed-width multiply — `np.int64 * np.int64`, which wraps silently on overflow | the register carrier's only arithmetic; this is the operation `pk * qk` performs on line 859 pre-patch |
| `truncW width x` | writing exact integer `x` into a `width`-bit two's-complement register (the silent wraparound) | the wrap itself, so it can be named in the model |

No module-level `axiom` and no separate `pure` helper for the arithmetic: the
squared coefficient is one closed arithmetic expression in the three integer
aggregates. The pure region declares only the plan syntax (`Aggregate`,
`IntPlan`, `RatPlan` — including `.zeroThen`, the node for answering a
degenerate triple without evaluating the rest of the combination), its
machine-word semantics (`inWord`, `IntPlan.value`, `RatPlan.value`), and the
register carrier the aggregates arrive on (`Word`, `truncW`, `instMulWord`) —
the vocabulary in which "which combination line 859 performs, and on what
carrier" is stated.

The pre-patch repo expression the change removes (refinement audit only, not in
the consumer spec view): `return tk / np.sqrt(pk * qk) if tk != 0. else 0.`
(line 859) — and the pre-patch contingency dtype (line 855, `sparse=True`
without `.astype(np.int64)`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the repo's numeric types.

| repo reality | Lean carrier | bijection / justification |
|---|---|---|
| `tk`, `pk`, `qk` — fixed-width integer scalars in the contingency matrix's dtype (lines 854-858) | `Word width` (`agree`, `spreadA`, `spreadB`), with `.toExact` the promotion | **the aggregates are modelled as REGISTER CONTENTS, not as unbounded integers.** Each `require inWord width ·.toExact` says the register holds the value, so within range `.toExact` IS the mathematical integer and nothing admissible is distorted. What the register carrier adds is that the aggregates' own multiplication (`instMulWord`) wraps, so a routine that multiplies two aggregates *in their registers* obtains a different quantity than one that promotes first. **This is the modelling decision the whole cell turns on, and modelling the aggregates as unbounded `Int` instead would be unsound for this bug**: over unbounded `Int` with both spreads positive, `spreadA * spreadB` is positive by a theorem, the overflow that IS the defect is unrepresentable, and the pre-patch and patched combinations become pointwise-equal functions that no postcondition can separate. G-AX (`check_register_reference`) executes the model's register multiply against real `np.int64` multiplication on ~20k pairs, including the F2P product, and asserts the wrap is reachable. |
| an arithmetic step whose OPERANDS have already left the array — `int(pk) * int(qk)`, `tk / pk` on scalars read out of it | exact `Int` / `Rat` arithmetic on `.toExact` values (unbounded, total) | **the direction of this row is what the cell turns on, and it is the row a rival routine is refined through.** A step whose operands are `.toExact` values is a step taken *after* the aggregates leave their registers, so its repo counterpart is arbitrary-precision arithmetic on scalars taken out of the array (`int(pk) * int(qk)`, exact at every magnitude), and **not** `pk * qk` on the array's own dtype. Reading it the other way round is unsound in the strong sense: `Int` multiplication does not wrap, so identifying it with a fixed-width multiply would give the model's `Int` a property `Int` does not have, and would collapse two routines the model keeps apart. The fixed-width multiply of two aggregates has its own carrier here (`instMulWord`, §1) exactly so the two are different objects. The consequence for any candidate routine is direct: a routine whose model text forms `spreadA.toExact * spreadB.toExact` has promoted both aggregates and multiplied in arbitrary precision — its repo counterpart is finite at every magnitude and is *not* the pre-patch line; the pre-patch line multiplies IN the register (`spreadA * spreadB : Word width`, whose content is `truncW width (·*·)`), and a routine that assembles its answer from that content is refuted by the exact-value conjunct wherever the product leaves the word. |
| the squared coefficient `(tk / np.sqrt(pk*qk))^2 = tk^2 / (pk*qk)` | `Rat` (exact) | the score is a ratio of integers; its SQUARE is the exact rational `agree^2 / (spreadA*spreadB)`. `Rat` is exact and computable (Velvet methods must compile — `Real` is noncomputable), so the squared coefficient is modeled exactly. Modeling the square (not the score itself) lets the single `np.sqrt` be peeled (§3) without an axiom. |
| `np.sqrt(·)` of a nonnegative argument | identity-after-squaring (omitted from the carrier) | the outer square root is order-preserving and value-determining on `≥ 0`: `score = sqrt(squared)`, so pinning the squared value pins the score. It is the SAME primitive in both patch and pre-patch (unchanged), so it carries no behavioral distinction; see §3. |
| `... if tk != 0. else 0.` short-circuit | the `agree = 0 → v = 0` clause of the postcondition, and `RatPlan.zeroThen (.read .agree) …` in the returned plan | the Python guard returns `0.` when `tk == 0`; the model returns `v = 0` (whose root is `0`) on `agree = 0`. The guard is also part of the expression's SHAPE, so it appears in the plan as well: `.zeroThen g q` answers `0` on a triple where the integer step `g` vanishes *without evaluating `q`*, which is what a routine that tests `tk` before dividing does. It is load-bearing rather than decoration, because a spread may vanish (see the admissible-input frame): a plan that forms its quotients unconditionally has no value on such a triple, so `.zeroThen` on the agreement count is forced by the plan clause and not merely permitted. |
| a real division whose divisor is `0` — no number comes out (`nan`), and the guarded line never performs it | `Rat` division, which is TOTAL: `x / 0 = 0` | **the one place the model's carrier is more forgiving than the machine, and the reason the tie conjunct exists.** On an admissible triple whose spread vanishes the real unguarded expression produces no number, while the exact rational quotient reports `0` — the required value. So an unconditional product of quotients and a guarded one denote the SAME rational everywhere admissible, and no clause about the returned number can distinguish them (G-AX runs that identity as a sweep). The distinction is carried by the PLAN (`.zeroThen` yields `0`, an unguarded plan yields nothing) and made binding by the tie: the returned number is the returned plan's number, so a routine satisfying this spec decided the no-agreement case before dividing, and its repo counterpart keeps the `if tk != 0.` guard. G-AX (`check_degenerate_short_circuit`) executes both shapes of the real callee arithmetic at the aggregates `(0, 0, 30)`: finite `0` with the guard, non-finite without it. |
| overflow / non-finite result (`nan`) | `Option (RatPlan × Rat) = none` | a `nan` float (a non-representable score) corresponds to `none`; a finite representable score to `some (p, v)`. `assert_all_finite` (the F2P test) observes exactly `some …` vs `none`. |
| a fixed-width two's-complement integer register (`np.int64` here, `w = 64`) | `inWord w x := -(2^(w-1)) ≤ x ∧ x ≤ 2^(w-1) - 1` | the integers such a register holds. **The width is a universally quantified variable of the postcondition, never the literal 64** — see the note below. |
| materialising an integer product in such a register (`pk * qk` in the pre-patch line 859, which wraps) | `IntPlan.value w … (.mul p q) = none` when `¬ inWord w (x*y)` | the model's ONE partiality. Real int64 multiplication wraps silently; the model refuses to give the step a value instead. Both make the enclosing expression not denote the mathematical coefficient, and G-AX executes the two side by side on the F2P aggregates (real `np.int64` `pk*qk` wraps negative ⇒ `np.sqrt` ⇒ `nan`; the product-first plan has no value) to show the model's partiality is that machine failure and not an artifact. |
| dividing one register by another (`tk / pk`, `tk / qk` in gold line 859) | `RatPlan.value w … (.ratio n d) = some ((x:Rat)/(y:Rat))` for `y ≠ 0` | total once both integer steps have a value: a quotient of two in-register integers is a magnitude ≤ the numerator, so no ratio step can leave the representable band. This is why gold's association survives where the pre-patch's does not. |

#### Why the width is quantified and not fixed at 64
The abstraction the model needs is "line 859 must not materialise a product of
the aggregates". Instantiated at one width that reads as "must not materialise a
product **that exceeds this width**", which is a fact about magnitudes on the
call at hand rather than about the expression. Quantifying over every width `w`
that holds the three aggregates turns it into a fact about the expression: for
ANY width, taking all three aggregates equal to the largest value the word holds
(`m = 2^(w-1) - 1`, `m ≥ 1`) makes every product a plan could materialise at
least `m^2 > m`, outside the word — so a plan yields the coefficient at every
width iff it materialises no product at all. `axiom_check.py` executes that
argument at widths 3..16. Fixed-width variants of the clause are strictly weaker
than the shipped one; the shipped one names no width, so it also cannot leak
which dtype hunk (a) selected.

### Admissible-input frame
`require 2 ≤ width`, `require inWord width agree.toExact`, `inWord width
spreadA.toExact`, `inWord width spreadB.toExact`, `require agree.toExact ≤
spreadA.toExact`, `agree.toExact ≤ spreadB.toExact`, `require 0 ≤
agree.toExact`, `0 ≤ spreadA.toExact`, `0 ≤ spreadB.toExact` — nine requires.

The three `inWord` requires say only that each register HOLDS its aggregate —
they bound the inputs, and deliberately **not** their product. The F2P-scale
witness `(tk, pk, qk) = (3003497866, 5152663196, 3294371982)` satisfies every one
of the nine requires at width 64 (each aggregate is far inside the word, and
`tk ≤ pk`, `tk ≤ qk`), while `pk * qk` is not in the word; so the very input on
which the pre-patch overflows is admissible, and the precondition excludes
nothing the gold patch changed.

Justification of the sign and ordering requires: `agree ≥ 0` is a count of
co-grouped pairs (`tk = Σ_ij c_ij² - n ≥ 0`). `spreadA`, `spreadB` are sums of
squares of marginal group sizes minus `n_samples`, hence `≥ 0` likewise. The two
ordering requires are the marginal inequality `tk ≤ pk`, `tk ≤ qk`: expanding a
marginal square, `Σ_j (Σ_i c_ij)² ≥ Σ_j Σ_i c_ij²`, because every cross term is
a product of nonnegative counts — so subtracting the same `n_samples` from both
preserves it. They are facts about the real aggregates, not conveniences: they
are what makes the coefficient lie in the unit interval.

**A vanishing spread is admitted, not excluded** (`0 ≤`, not `0 <`): a partition
that spreads every element into its own group has `Σ (group size)² = n`, so its
aggregate is exactly `0`, and by the ordering requires the agreement count is
then `0` too. This is an ordinary clustering, not a pathology, and it is the
input on which forming a quotient against that spread yields no number at all —
which is why the routine has to DECIDE the no-agreement case on the agreement
count before it divides, and why the plan carries `.zeroThen`. The `agree = 0`
case is the Python `tk != 0.` short-circuit branch, and that branch is the one
that answers on a degenerate partition.

## 3. Callee provenance — the single square root (no consumed axiom)

**Callee:** `numpy.sqrt`, applied once to a nonnegative argument. In the patched
expression it appears twice (`np.sqrt(tk/pk) * np.sqrt(tk/qk)`); in the pre-patch
once (`np.sqrt(pk*qk)`). It is **unchanged** by the fix.

It is **not** modeled by a consumed axiom. The routine returns the SQUARED
coefficient `v`, and the score is `sqrt(v)`. Because `sqrt` on a nonnegative
real is the unique nonnegative number whose square is the argument, pinning `v`
exactly (the postcondition) pins the score exactly; the relation `score^2 = v`
is a squaring identity, not a borrowed contract. Hence no `axiom` is consumed and
there is no dead axiom (directive 7, no over-claiming).

**What G-AX checks instead (the deep-model references the two observables rest
on):** `axiom_check.py` runs the REAL `numpy` and the transliterated pure region.

* **A-reference (the squaring)** — `(np.sqrt(tk/pk) * np.sqrt(tk/qk))^2` equals
  the model's `tk^2/(pk*qk)` numerically on 9 boundary + 20000 fuzz aggregate
  triples, so the modeled square is the patched score's square.
* **P-reference (the plan semantics)** — `IntPlan.value` / `RatPlan.value` are
  transliterated to Python (`Fraction`, exact) and executed at width 64, the
  dtype hunk (a) selects. On the same triples the RETURNED plan has a value and
  that value is the exact coefficient (so the plan clause is TRUE of the real
  patched line 859), while the product-first plan is valueless on 19998 of the
  20000 (so the clause is not vacuous).
* **Faithfulness of the discriminator** — at the F2P-scale aggregates
  `(tk, pk, qk) = (3003497866, 5152663196, 3294371982)`, `pk*qk` exceeds
  `np.iinfo(np.int64).max`; the REAL pre-patch `tk/np.sqrt(pk*qk)` on `np.int64`
  operands is `nan` while the patched formula is finite, and at exactly that
  input the product-first plan has no value while the returned plan does. The
  model's partiality IS the machine's failure.
* **S-reference (the short-circuit)** — `check_degenerate_short_circuit` takes the admissible degenerate triple `(0, 0, 30)` (every element of one partition in a group of its own) and runs the REAL patched arithmetic both ways: with the `tk != 0.` test it returns a finite `0`, and with the test dropped it returns a non-finite value — in both refinement shapes (divide first; promote the spreads to an exact product first). The plan semantics splits them the same way (the returned plan yields `0`, the bare combine step has no value). The NEGATIVE CONTROL runs alongside: the model's total rational arithmetic reports the same number for the guarded expression and for both unguarded shapes, there and across a sweep of admissible triples, so the returned number provably cannot carry the short-circuit and the tie clause is doing work the value clause cannot.
* **Width-universality** — at widths 3..16, `m = 2^(w-1)-1`: `m*m` leaves the
  word, the product-first plan is valueless on aggregates the word holds, and the
  returned plan still yields the exact coefficient `1`.
* **R-reference (the register carrier)** — `check_register_reference` executes the
  model's `truncW` / `instMulWord` against REAL `np.int64` multiplication on 14
  boundary pairs plus 20000 random pairs drawn from the full signed range, and
  requires exact agreement on every one, in range and out. It further asserts
  NON-VACUITY (the wrap must actually fire on that corpus, or the carrier's
  distinction would be decoration) and in-range FAITHFULNESS (where the exact
  product fits the register, the register holds exactly it — so the carrier
  distorts nothing admissible). `check_register_discriminates` then shows the
  carrier bites at the F2P witness: the register product of the two spreads wraps
  NEGATIVE there, so a routine combining through it divides by a negative
  quantity and cannot return a nonnegative coefficient.

stdlib + numpy only; exit 0 iff every obligation holds.

## 4. G-CONF fuzz seed (pinned for deterministic eval)

`conformance_check.py` seeds its `random.Random` with **`10844`** so the
consumer-side verdict is reproducible. It shadows BOTH observables of the impl
region on the same fuzzed inputs — ≥10^5 fuzzed label arrays plus the F2P-scale
overflow witness, with the three aggregates recomputed from each label pair
exactly as lines 854-858 do:

1. **the value** — the impl's divide-first computation transliterated to Python
   over the real `int`/`float` carrier, diffed against the patched
   `fowlkes_mallows_score` behaviour (square the returned score);
2. **the plan** — the plan the impl returns, evaluated by the transliterated
   fixed-width semantics at width 64. It must HAVE a value on every input the
   oracle accepts and that value must be the oracle's squared score; the
   product-first plan is evaluated alongside and the inputs where IT is valueless
   are counted, with a FAIL if the count is zero (a fuzz that never reaches the
   overflow regime carries no evidence about the clause that separates the two
   routines);
3. **the register carrier** — the value a routine gets by combining through the
   REGISTER product of the two spreads is computed alongside on the same real
   label data, and the inputs where it parts company from the exact coefficient
   are counted, with a FAIL if that count is zero. Same reasoning as leg 2: a fuzz
   that never reaches the wrapping regime carries no evidence about the carrier
   distinction the value clause rests on;
4. **the tie** — the returned number and the returned plan's number are compared
   as exact rationals with NO tolerance, because that is how the spec states the
   conjunct. A tie that held only to within a tolerance would not be it.

The admissible domain includes a VANISHING SPREAD, so those inputs are compared
rather than skipped: the fully-split label arrays reach the routine as `(0, 0, s)`,
the oracle returns `0` there, and the combine step run unconditionally has no
value at all — the returned plan's `.zeroThen` step is the only reason a number
comes out. The run counts those inputs and FAILS if it never reaches one, on the
same reasoning as legs 2 and 3.
