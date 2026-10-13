# refinement.md — sympy__sympy-16597

The operation-by-operation correspondence between `model.py`'s implementation
(the deep theory model `consistent_theory` and the THIRTY-ONE deducers — five
bounded seeds `deduce_even` / `deduce_odd` / `deduce_integer` /
`deduce_rational` / `deduce_irrational`, one unbounded seed `deduce_infinite`,
four unknown-frontier seeds `deduce_not_rational` / `deduce_not_irrational` /
`deduce_not_even` / `deduce_not_odd`, three defining-condition seeds
`deduce_real_nonrational_bounded` / `deduce_real_transcendental` /
`deduce_integer_nonodd`, two one-sided seeds
`deduce_integer_nonnegative` / `deduce_integer_nonpositive`, one bounded
algebraic seed `deduce_algebraic_bounded`, four sign-frontier seeds
`deduce_not_nonnegative` / `deduce_real_not_nonnegative` /
`deduce_real_not_positive` / `deduce_real_not_negative`, one origin seed
`deduce_nonnegative_nonpositive`, two whole-number-class seeds `deduce_prime` /
`deduce_noncomposite_positive_even`, and one punctured-line seed
`deduce_nonzero`) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A-consumed** (the proof uses an axiom's `Ensures`),
**A-reference** (a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, deduces the same fact tables as the gold patch on the tested seeds, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

There is **no consumed `@ContractOnly` axiom**: the changed behaviour — the
set-containment rule theory — is modelled DEEPLY (`consistent_theory`), so the
real rule engine is an **A-reference** (validated by G-AX), not an axiom.

## A. The rule theory — `_assume_rules` (`sympy/core/assumptions.py:163-201`)

Gold hunk (the behavioural delta):
```
- 'rational       ->  real'
+ 'rational       ->  real & finite'
- 'algebraic      ->  complex'
+ 'algebraic      ->  complex & finite'
- 'transcendental ==  complex & !algebraic'
+ 'transcendental ==  complex & !algebraic & finite'
- 'irrational     ==  real & !rational'
+ 'irrational     ==  real & !rational & finite'
```
(the `ask_generated.py` hunk is the mechanically-recompiled CNF/dict mirror of
the same rules; `make_known_facts` regenerates it — it carries no independent
behaviour.)

| # | model.py impl op | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `KB` record of `Optional[bool]` fields, one per fact | the `StdFactKB`/`FactKB` dict of `is_<fact>` → True/False/None for a quantity | R | a fact value is `True`/`False`/`None` ↔ `Optional[bool]`; one dict entry ↔ one field (mapping.md §2). |
| A2 | `consistent_theory(k)` — the conjunction of the containment implications incl. the new `rational/algebraic/irrational/transcendental -> finite` edges and their contrapositives, plus the pre-existing engine edges `real -> complex`, the `!odd` direction of `even == integer & !odd` (`even -> !odd`), and the reverse exclusion of `noninteger == real & !integer` (`integer -> !noninteger`) | the post-edit `_assume_rules` rule set compiled by `FactRules`, whose closure `deduce_all_facts` makes every one of these implications hold in each fact table it produces | A-reference | the changed string of rules is modelled **deeply** as the closure predicate; there is no consumed axiom. The clause list is a SOUND-BUT-NOT-COMPLETE reading of the closure — it states implications the real closure satisfies, not the whole of it — which is why §B does not rest on it alone (see the per-seed obligation, A3/A3b). The contrapositives (`!finite -> !rational…`, `!rational -> !integer`, `!integer -> !even/!odd/!prime/!composite`) are exactly what `deduce_alpha_implications` adds (`facts.py:116`). The `real -> complex` (`assumptions.py:169`), `even -> !odd` / `odd -> !even` (`even == integer & !odd`, `assumptions.py:176`), `algebraic -> !transcendental`, `finite -> !infinite` and `integer -> !noninteger` (reverse of `noninteger == real & !integer`) edges are pre-existing engine facts the F2P tests reach (`oo.is_complex`, `Symbol(even=True).is_odd`, integer/noninteger consistency); they over-cover the caller-reachable facts. The theory further carries the pre-existing SIGN, ORIENTATION, SELF-ADJOINTNESS and WHOLE-NUMBER-CLASS rules of the same block — `real -> hermitian` (`:170`), `imaginary -> antihermitian` (`:172`), `imaginary -> !real` (`:196`), `negative/positive == nonpositive/nonnegative & nonzero` (`:181-182`), `zero == nonnegative & nonpositive` (`:183`), `nonpositive/nonnegative == real & !positive/!negative` (`:185-186`), `zero -> even & finite` (`:188`), `prime -> integer & positive` (`:190`), `composite -> integer & positive & !prime` (`:191`) and the beta rule `!composite -> !positive \| !even \| prime` (`:192`), plus `nonzero == real & !zero` (`:200`) — all of which the hidden battery observes (`test_I`, `test_symbol_zero`, `test_Mul_is_prime_composite`, `test_composite`, `test_symbol_imaginary`). G-AX validates all seventy-three clauses of `consistent_theory` hold in the real engine on 1235 observations at the property level (sixty before the fifth correction added the thirteen punctured-real-line clauses, A3j). |
| A3 | the FIVE bounded-seed deducers — `deduce_even`, `deduce_odd`, `deduce_integer`, `deduce_rational`, `deduce_irrational` — each seeding one positive membership and assigning along the edges its closure fires, each returning a record with `finite=True` and `consistent_theory(Result())` | the engine’s forward-chaining closure of each of those five seeds under the edited rules, each deducing `is_finite=True` | R + A-reference | each `self._tell(key,value)` for a fired implication edge ↔ one field assignment (mapping.md §2). What discriminates is NOT which edge the model walks but the resolved STATUS each closure reaches: every one of the five seeds resolves boundedness, and the five have pairwise-different Unknown sets (`rational=True` leaves `integer`/parity Unknown; `integer=True` leaves parity Unknown; `irrational=True` leaves `algebraic` Unknown), so each seed's boundedness obligation must be met on a record where the others' antecedents are Unknown. Measured on the real patched engine, field for field, in `axiom_check.py`'s `SEED_RECORDS`. |
| A3b | the FOUR frontier deducers — `deduce_not_rational`, `deduce_not_irrational`, `deduce_not_even`, `deduce_not_odd` — each seeding one NEGATIVE membership and returning a record whose `finite is None` | the engine’s closure of `Symbol(rational=False)` / `(irrational=False)` / `(even=False)` / `(odd=False)`, each leaving `is_finite` unresolved | R + A-reference | the obligation from the other side: boundedness must resolve on the five positive seeds and must NOT resolve on these four, so it cannot be satisfied by an over-strong theory that bounds everything. `rational=False` additionally propagates to `!integer` and thence `!even/!odd/!prime/!composite` and nothing further; the other three propagate to nothing. Measured, not reasoned (`SEED_RECORDS`). |
| A3c | the THREE defining-condition deducers — `deduce_real_nonrational_bounded`, `deduce_real_transcendental`, `deduce_integer_nonodd` — each seeding the statuses one equivalence needs on its right-hand side and returning a record in which the membership that equivalence defines is RESOLVED (`irrational=True`, `irrational=True`, `even=True` respectively) | the engine's closure of `Symbol(real=True, rational=False, finite=True)`, `Symbol(real=True, transcendental=True)` and `Symbol(integer=True, odd=False)` under the edited rules, each deducing the defined membership because `irrational == real & !rational & finite` and `even == integer & !odd` are EQUIVALENCES (`==`), which `FactRules` compiles in both directions, not one-way `->` edges | R + A-reference | this is the leg the forward-only clause list of A2 cannot supply on its own. The five bounded and four frontier seeds all assert a plain membership or non-membership, so none of them ever hands the closure a complete right-hand side of an equivalence with the left-hand side outstanding; the reverse direction is therefore vacuous on all nine records. These three make it observable. `deduce_real_transcendental` additionally COMPOSES the two obligations: transcendence must resolve boundedness (the edited edge) and that resolved boundedness must then satisfy the irrationality equivalence, so a theory that fires the new boundedness edge but keeps irrationality one-way is rejected here. Measured on the real patched engine, field for field, in `axiom_check.py`'s `SEED_RECORDS`; every pinned field is invariant across a 74-member pool of alternative rule sets that all pass the hidden battery, so no incidental choice is pinned. |
| A4 | `deduce_infinite` impl: seed `infinite=True, real=True`, then `real->complex`, `infinite->!finite`, `!finite->!{rational,algebraic,irrational,transcendental}`, `!rational->!integer`, `!integer->!{even,odd,prime,composite}`, `real&!integer->noninteger`, returning a record with those values, all four sign statuses left Unknown, and `consistent_theory(Result())` | the engine’s closure of the SIGN-FREE unbounded real seed `Symbol('x', infinite=True, real=True)` under the edited rules, deducing `is_complex=True`, `is_integer/is_even/…=False`, `is_noninteger=True`, and leaving `is_positive/is_negative/is_nonpositive/is_nonnegative` None | R + A-reference | the new edges make `!finite` (from `infinite`) propagate to `!rational` etc. (contrapositives of A2). `complex=True` is the pre-existing `real->complex` deduction. Each propagated `self._tell` ↔ one field assignment. The reference is the bare seed, NOT `S.Infinity`: the two concrete unbounded quantities are that seed plus a declared direction, agreeing on every membership and disagreeing on sign, so unboundedness itself decides no sign region. `Ensures(Result().positive is None)` and its three companions state that, and G-AX measures it on the real engine (`u.is_positive is None`, …) alongside `oo.is_positive is True` / `(-oo).is_negative is True`. |
| A3d | the TWO one-sided deducers — `deduce_integer_nonnegative`, `deduce_integer_nonpositive` — each seeding wholeness plus one bound by zero, resolving boundedness through wholeness, pinning the weak bound its seed states and the opposite strict sign to False, leaving the seeded side's strict sign Unknown, and (for the nonpositive seed) `prime`/`composite` False | the engine’s closure of `Symbol('x', integer=True, nonnegative=True)` and `Symbol('x', integer=True, nonpositive=True)` | R + A-reference | these put the sign region and the memberships in ONE record, so a theory may not answer memberships while abstaining on sign, nor conflate a weak bound with a strict sign: zero satisfies both seeds, so the strict sign on the seeded side must stay Unknown while the opposite strict sign resolves to False. `prime`/`composite` resolve to False on the nonpositive seed only, since primality demands strict positivity. Measured field for field, sign statuses included, in `axiom_check.py`'s `SEED_RECORDS`. |
| A3e | `deduce_algebraic_bounded` — seed `algebraic=True` AND `finite=True`, then `algebraic -> complex`, `algebraic -> !transcendental`, `finite -> !infinite`, everything else left Unknown | the engine's closure of `Symbol('x', algebraic=True, finite=True)` | R + A-reference | the containment `algebraic -> complex` (`assumptions.py:168`) is VACUOUS on every one of the fifteen earlier seeds, because each record that is algebraic there is also real and `real -> complex` forces complexity independently. This seed leaves realness Unknown, so the containment is the only route to complexity; the rival rule set that drops the `complex` conjunct reproduces all fifteen earlier records and fails `test_symbol_noncommutative` (measured). Boundedness is SEEDED rather than deduced here, per A5. Measured field for field in `SEED_RECORDS`. |
| A3f | the FOUR sign-frontier deducers — `deduce_not_nonnegative`, `deduce_real_not_nonnegative`, `deduce_real_not_positive`, `deduce_real_not_negative` — each seeding the REFUSAL of a sign region and returning the record its closure reaches (`!nonnegative` alone denies `positive`, `prime`, `composite` and nothing else; with realness added the sign resolves fully to strictly negative; the two remaining seeds each resolve the weak region their equivalence defines) | the engine's closure of `Symbol('x', nonnegative=False)`, `Symbol('x', real=True, nonnegative=False)`, `Symbol('x', real=True, positive=False)`, `Symbol('x', real=True, negative=False)` under `positive == nonnegative & nonzero` (`:182`), `nonnegative == real & !negative` (`:186`), `nonpositive == real & !positive` (`:185`) and the contrapositives `FactRules` derives | R + A-reference | none of the fifteen earlier seeds ever refuses a strict sign or a weak region, so the reverse direction of the two weak-region equivalences and the contrapositive of the strict-sign equivalences were unobservable. Four surveyed rule sets that delete or weaken them reproduce every earlier pinned record and fail `test_symbol_falsenonnegative`, `test_symbol_falsepositive_real`, `test_neg_symbol_nonpositive`, `test_I` (measured, resolved=FALSE). Note the first seed pins realness to Unknown: refusing a region says nothing about the real line, which is what makes the DROP-CONJ rival that removes `real` from the weak-region equivalences visible. Measured field for field in `SEED_RECORDS`. |
| A3g | `deduce_nonnegative_nonpositive` — seed both bounds by zero, then deny both strict signs, recognise the origin, and assign the entire whole-number cascade (`even`, `integer`, `rational`, `real`, `algebraic`, `finite`, `complex`, `hermitian`, `!odd`, `!noninteger`, `!irrational`, `!transcendental`, `!infinite`, `!prime`, `!composite`) | the engine's closure of `Symbol('x', nonnegative=True, nonpositive=True)` under `zero == nonnegative & nonpositive` (`:183`) followed by `zero -> even & finite` (`:188`) | R + A-reference | the origin is the one point both weak regions share, and it is the ONLY seed at which `zero -> even & finite` fires; no earlier seed carries both bounds, so a rule set that deletes that rule (or just its `even` conjunct) reproduced every earlier record and failed `test_symbol_zero` / `test_Mul_is_algebraic` / `test_special_is_rational` (measured, resolved=FALSE). Measured field for field in `SEED_RECORDS`. |
| A3h | the TWO whole-number-class deducers — `deduce_prime` (seed `prime=True`, resolving wholeness, strict positivity, `!composite` and the full bounded cascade, parity left Unknown) and `deduce_noncomposite_positive_even` (seed `composite=False, positive=True, even=True`, resolving `prime=True`) | the engine's closure of `Symbol('x', prime=True)` and `Symbol('x', composite=False, positive=True, even=True)` under `prime -> integer & positive` (`:190`), `composite -> integer & positive & !prime` (`:191`) and the beta rule `!composite -> !positive \| !even \| prime` (`:192`) | R + A-reference | the two classes appear in the earlier seeds only as consequences (`prime is None` / `prime is False`), never as an antecedent, so their mutual exclusion and the recognition of the smaller class from its defining conditions were unobservable. The rival that drops `!prime` from the composite rule reproduces every earlier record and fails `test_Mul_is_prime_composite`; the rival that deletes the beta rule fails `test_composite` (measured, both resolved=FALSE). The second seed is the beta rule's reverse direction: its other two disjuncts are denied by the seed, so primality must resolve. Parity stays Unknown on the prime seed because both parities occur among the primes. Measured field for field in `SEED_RECORDS`. |
| A3i | `deduce_nonzero` — seed the record's non-zero status, then `real`, `complex`, `!imaginary`, `hermitian`, everything else Unknown (the seed that takes the `nonzero` field as its hypothesis; since the fifth correction every deducer PINS that field, see A3j) | the engine's closure of `Symbol('x', nonzero=True)` under `nonzero == real & !zero` (`assumptions.py:200`) | R + A-reference | the non-zero status is the punctured REAL line, not merely "distinct from zero", and no earlier seed states it, so the `real` conjunct of that equivalence was unobservable. Two surveyed rule sets (deleting the rule, and dropping its `real` conjunct) reproduce every earlier pinned record, verify against the fifteen-seed spec, and fail `test_symbol_imaginary` / `test_symbol_zero` / `test_symbol_falsenonnegative` (measured, resolved=FALSE) — they were the last two uncovered holes of the survey. Measured field for field in `SEED_RECORDS`, whose record for this seed is the only twenty-two-field one. |
| A3j | the NON-ZERO COLUMN (fifth correction, 2026-08-16): `consistent_theory` takes `Requires(Acc(k.nonzero, 1 / 8))` and carries the thirteen clauses of the punctured real line — `nonzero -> real`, `!real -> !nonzero`, `positive -> nonzero`, `negative -> nonzero`, `nonpositive & nonnegative -> !nonzero`, `!nonzero & real -> even`, `!nonzero & real -> nonnegative`, `!nonzero & real -> nonpositive`, `nonzero & nonpositive -> negative`, `nonzero & nonnegative -> positive`, `odd -> nonzero`, `irrational -> nonzero`, `real & !finite -> nonzero` — and EVERY one of the thirty-one deducers now pins `Result().nonzero` to the trit the real engine resolves for its own seed (9 True, 1 False on the origin seed, 14 None; `Ensures(Acc(Result().nonzero))` 24x) | the engine's closure under `nonzero == real & !zero` (`assumptions.py:200`), `positive == nonnegative & nonzero` / `negative == nonpositive & nonzero` (`:181-182`), `zero == nonnegative & nonpositive` (`:183`), `zero -> even & finite` (`:188`), `odd == integer & !even` + `irrational == real & !rational & finite` + `infinite -> !finite` as `FactRules` compiles them in both directions | R + A-reference | `nonzero` was a field of the record that only ONE deducer's postcondition mentioned and that `consistent_theory` held no permission to, so on the other thirty seeds it was a FREE cell: any trit verified. Four rivals differing from gold in that cell alone were machine-witnessed to verify against the fourth-correction spec (claiming it off parity, claiming it at the origin, denying it on a strictly positive whole number, and adding it on the real-transcendental seed). All thirteen clauses were probed to hold on 7741 real-engine observations (numeric singletons plus every satisfiable single, pair and triple of the 21 seed facts), and each per-seed value was read off the modelled reference AND re-read identically with the modelled change absent, so the column depends only on rules `patch.diff` does not touch and cannot over-fit any correct alternative. Measured field for field in `SEED_RECORDS` via `SEED_NONZERO` (G-AX). |
| A3k | the REGION AWAY FROM THE REAL LINE (sixth correction, 2026-08-16): six new seeds instantiate the closure where the quantity does NOT lie on the real line, has unbounded absolute value, or is only assumed to multiply order-independently — a non-zero multiple of the imaginary unit (`imaginary=True`); the same bounded by transcendence (`imaginary=True, transcendental=True`); unbounded absolute value alone (`finite=False`); the punctured line read backwards (`integer=False, nonzero=False`); the denial of one adjointness orientation (`antihermitian=False`); and both order-of-multiplication seeds (`commutative=True` / `False`) — each pinning all twenty-two fields; and `consistent_theory` gains twenty clauses that are non-vacuous only there: `!real -> {!integer, !rational, !irrational, !noninteger, !nonzero}`, `imaginary -> {!nonzero, !irrational, !rational, !integer, !noninteger}`, `!nonzero & !integer -> !real`, `!finite -> {!integer, !even, !odd, !prime, !composite}` and `!complex -> {!real, !imaginary, !algebraic, !transcendental}` | the engine's closure under `imaginary -> !real` (`assumptions.py:189`), `nonzero == real & !zero` (`:200`), `noninteger == real & !integer` (`:199`), `irrational == real & !rational & finite` (`:191`), `rational -> real & finite` / `algebraic -> complex & finite` / `transcendental == complex & !algebraic & finite` (`:166,168,179`), `zero -> even & finite` (`:188`), `prime -> integer & positive` (`:185`) and `complex -> commutative` (`:172`) as `FactRules` compiles them in both directions | R + A-reference | Before this correction EVERY record the spec observed had realness True (16 seeds) or Unknown (8) — resolved False on NONE, and no record had the imaginary orientation, unbounded absolute value or a denied order-independence. So every relation the theory states about NOT lying on the real line, about unboundedness, and about order-of-multiplication was VACUOUS on the whole observable, and a rule theory free to get them wrong verified: a 447-variant machine survey of spec-conformant rule sets found 33 that reproduced every pin of the fifth-correction spec yet did NOT resolve the hidden suite (breaking `test_issue_4149`, `test_Mul_is_infinite`, `test_issue_6631`, `test_Mul_is_prime_composite`, `test_nan` and `test_symbol_noncommutative`; one broke 27 P2P tests). Against the six new seeds all 33 violate a pin (measured: 33/33, survivors 0). The `imaginary & transcendental` seed is the one record on which the modelled boundedness relation is observable with realness DENIED, so the second prepatch obligation is non-vacuous off the line as well as on it. All twenty clauses were probed to hold on 11324 real-engine observations (numeric singletons plus every satisfiable single, pair and triple of the 24 seed facts) with three deliberately-too-strong controls violating 648/696/696 times, so the probe discriminates; and every per-seed value was read off the modelled reference AND re-read identically with the modelled change absent for the two order-of-multiplication seeds, whose records are patch-invariant. Measured field for field in `SEED_RECORDS` (G-AX, 1389 observations); the rival rule set of the recorded G-EQ attack now FAILS `axiom_check.py` at `deduce_imaginary`. |
| A5 | boundedness is NOT pinned for the seeds `algebraic=True` and `transcendental=True` anywhere in the spec | the gold rules do bound both | (deliberate under-specification) | two independently harness-verified resolving alternatives leave one or the other of those two Unknown (a rule set that bounds via `rational`/`irrational` without the `algebraic` conjunct, and one without the `transcendental` conjunct, each measured resolved=TRUE with a failure set identical to gold on the whole `test_assumptions.py`). Pinning either would reject a correct implementation, so the spec states only the statuses the hidden tests actually observe. |

## B. The discriminating clause and the prepatch

The behavioural change is observable in **two directions** — forwards
(memberships now force boundedness) and backwards (unboundedness now excludes
those memberships) — so there are two `model_prepatch` variants, each reverting
the impls of one direction to the pre-patch propagation (the old rule set has no
`* -> finite` edges):

- `model_prepatch.py` reverts all FIVE bounded-seed deducers: each stops before
  boundedness and leaves `finite` (and the `!infinite` that depends on it)
  Unknown. Each of the five **fails** its own `Ensures(Result().finite is True)`
  as well as `consistent_theory(Result())`. (G-DIFF, forward direction.)
- `model_prepatch_2.py` reverts `deduce_infinite`: `infinite -> !finite` fires
  but `!finite` propagates to nothing (old rules), so `rational/integer/even/…`
  stay `None`. It **fails** `consistent_theory(Result())` (the spec requires
  `finite=F -> rational=F`, hence the cascade) — and the F2P clauses
  `Result().rational is False`, `Result().integer is False`, etc. (G-DIFF,
  backward direction.)

**The closure postcondition alone is NOT sufficient, and this is the substance of
the 2026-08-15 repair.** `consistent_theory` is a predicate on ONE record, so a
clause like `rational=T -> finite=T` is satisfied **vacuously** on any record
where boundedness happens to be resolved for a different reason. A knowledge base
that bounds only the parity classes reproduces the even-seed record and the
unbounded-seed record EXACTLY — all 14 trits, `consistent_theory` included —
while leaving `Symbol(odd=True).is_finite`, `Symbol(integer=True).is_finite` and
`Symbol(rational=True).is_finite` Unknown. Such a rival verified against the
earlier two-seed spec and its faithful patch was harness-run to resolved=FALSE.
Instantiating the closure at two seeds cannot see WHICH memberships force
boundedness, which is exactly the patch's delta.

The obligation that IS sufficient is per-seed and two-sided: the closure is
instantiated at thirty-one seeds, and each deducer’s postconditions pin the trit of
EVERY `KB` field (True / False / None) to the real engine’s deduced value for
THAT seed. The five positive-membership seeds each carry
`Ensures(Result().finite is True)` on a record where the other four antecedents
are Unknown, so no one of them can be discharged vacuously through another; the
four negative-membership seeds each carry `Ensures(Result().finite is None)`, so
the obligation cannot be met by a theory that resolves boundedness everywhere.
Together the thirty-one records leave no field of the observable free —
literally every one of the record’s twenty-two fields on every one of the
thirty-one seeds, since the fifth correction (A3j) closed the last free cell: a
spec-admitted record IS the real engine’s record on each of the thirty-one seeds
(`axiom_check.py` `SEED_RECORDS` asserts thirty of them field-for-field
against the real patched engine, G-AX, sign statuses included for the one-sided
seeds and for all nine seeds of the fourth correction, and the non-zero column
merged in from `SEED_NONZERO`; the unbounded seed is checked separately, its
non-zero status included). The shared spec (`consistent_theory` and all
thirty-one deducers’ pre/post) is byte-identical across model.py and both prepatch
files (verified with `same_spec`: only `impl` regions differ).

**Sign neutrality of the unbounded seed (2026-08-15, third correction).** The
fifteen-seed obligation as first written pinned every field of fourteen seeds
but left four free on the unbounded one, and nothing else in the spec reaches a
sign region on a record whose boundedness is False. So a record that read a
direction off unboundedness — `positive=True, nonnegative=True, negative=False,
nonpositive=False`, or only `nonnegative=True, negative=False` — satisfied the
whole spec and VERIFIED (three such rivals measured
`CANDIDATE-COUNTEREXAMPLE: shares spec AND verifies`). Those are not correct
alternatives: the rule sets they refine to (`infinite -> positive`,
`infinite -> nonnegative`) contradict the oppositely-unbounded quantity's own
declared direction, so `FactRules` raises `InconsistentAssumptions` during
`import sympy` and the entire battery errors. The real engine leaves all four
Unknown for the bare seed (measured), so `Ensures(Result().positive is None)`
and its three companions are faithful, and the three rivals now fail to
verify.

**Clause-level instantiation (2026-08-16, fourth correction).** The three
corrections above each closed one vacuity; the general statement is that a
clause of `consistent_theory` constrains a record only where the status it
decides is not settled for another reason, so every clause group needs a seed on
which it is the sole route. Nine groups had none: the algebraic containment (A3e),
the two weak sign regions and their defining conditions (A3f), the origin (A3g),
the exclusion between the two whole-number classes and the recognition of the
smaller one (A3h), and the punctured real line (A3i). Machine-witnessed over 107
rival rule sets, each written into `_assume_rules`, compiled, and graded against
the whole hidden battery in-container: 29 do not yield a working library at all,
49 violate a record the fifteen-seed spec already pinned, **13 reproduce all
fifteen pinned records and are resolved=FALSE**, and 16 reproduce them and are
resolved=TRUE. All 13 violate one of the nine new records; the 16 resolving
rivals violate none of them (every field of all nine new records takes the same
value across those 16, so no new pin can reject a correct alternative). Two of
the 13 — the rule sets that delete `nonzero == real & !zero` or drop its `real`
conjunct — were confirmed to VERIFY against the fifteen-seed spec, which is the
`verify ⇏ resolved` witness this correction removes.

**The free cell (2026-08-16, fifth correction).** The fourth correction closed
every clause GROUP that no pinned record witnessed; it did not ask whether every
FIELD of the record was pinned on every seed. One was not. `nonzero` was
mentioned by exactly one deducer's postconditions — `deduce_nonzero`, the seed
that takes it as its hypothesis — and `consistent_theory` held no permission to
it at all (no `Acc(k.nonzero, 1/8)` in its `Requires`), so no clause of the
closure predicate could refer to it either. On the other thirty seeds it
was therefore a FREE cell of the record: an implementation could hand back True,
False or Unknown for it and verify. Four rivals differing from gold in that one
cell were machine-witnessed to verify against the fourth-correction spec —
reading it off parity (`even -> nonzero`), asserting it at the origin, denying it
on a strictly positive whole number, and asserting it on the real-transcendental
seed. The last is the shape the recorded G-EQ finding used: a `CANDIDATE` whose
faithful rule set adds `transcendental -> nonzero`, which through
`nonzero == real & !zero` also makes every transcendental real and so fails
`test_issue_4149` in PASS_TO_PASS (74 P2P, 1 failing) while passing all three
F2P. The repair is A3j: the field is pinned in all thirty-one postconditions at
the engine's value, and `consistent_theory` takes the permission and states the
thirteen clauses of the punctured real line. After it, that rival's added line is
part of gold on the seed it targeted (so the shape is no longer a same-spec
difference at all) and every other value of the column is rejected by an exact
pin or by a clause: the four rivals above now fail to verify (measured; two by
the pin, two by `consistent_theory`), and the reject lane `nz-*` in
`properties.py` witnesses all four shapes with `pos-real-transcendental-nonzero-first`
/ `pos-origin-nonzero-first` as the over-fitting guard (both verify, measured).

**Why this does not over-fit.** The obligation is EXTENSIONAL — it states the
resolved status of each seed’s closure, never which rule produced it. Rule sets
that reach the same records by different edges (a direct `even -> finite`
plus `odd -> finite` plus `integer -> rational & finite`; a standalone
`irrational -> finite`) reproduce every pinned record and were harness-run to
resolved=TRUE;
they remain admitted, and rivals encoding them verify. Conversely every rule set
measured in this repair that reproduced every pinned record passed FAIL_TO_PASS,
and every FAIL_TO_PASS-failing rule set violated at least one pinned record (~30
candidate rule sets across five batches, the last of which swept the sign
edges: `infinite -> positive` and `infinite -> nonnegative` each break the
import, and both violate the unbounded seed's four sign Unknowns). And per A5, the two seeds whose
boundedness genuinely differs across correct alternatives (`algebraic=True`,
`transcendental=True`) are pinned nowhere.

### B.1 Completion — the deduction is TOTAL (`Requires(MustTerminate(_))`)

Every clause in §A/§B constrains the VALUES of a record that was handed back;
none of them says a record is handed back at all. Nagini proves PARTIAL
correctness by default, so a deducer whose body never reaches its `return`
satisfies `consistent_theory(Result())` and all 14 pinned trits **vacuously**.
That admits an implementation whose refined image is a fact closure that
re-enters itself, leaving every assumption query pending; the F2P tests then
raise `RecursionError` instead of observing the trit, so it does not resolve.
This was machine-witnessed (2026-08-14 spec repair: two same-spec rivals,
`return deduce_even()` and `return deduce_infinite()`, verified under the
pre-repair spec and their faithful patches were harness-run to resolved=FALSE).

The property the real callee HAS, and which those rivals lack, is completion:
`FactKB.deduce_all_facts` (`sympy/core/facts.py:501-537`) consumes a finite
`facts` work-list — `while facts:` with `facts = []` rebuilt each round only
from beta rules whose triggers newly fired, and `_tell` (`facts.py:484-496`)
returning False once a key already holds its value, so no fact is re-announced
— hence the closure drains and RETURNS for every seed. `StdFactKB.__init__`
(`sympy/core/assumptions.py:208-223`) calls it exactly once and does not
re-enter itself. So the deduction terminates and the queried status is always
available, which is precisely why `Symbol('x', even=True).is_finite` evaluates
to `True` rather than hanging.

Modelled as `Requires(MustTerminate(2))` in each deducer’s pre-conditions (and
`MustTerminate(1)` on the record constructor, whose level must sit strictly
below its callers’). This is behaviour, not an implementation detail: it fixes
no iteration order, no propagation sequence, and no step count. Both positive
controls (the reverse-order deducers) still verify, so it does not over-fit;
the three `diverge-*` G-PBT reject cases are its falsification lane.

## C. No kind-3 (unexpressible-changed-op) steps

Every step is R or A-reference. The one operation that genuinely *changed* —
the rule theory (the `* -> finite` containments) — is modelled **deeply** as
`consistent_theory` and the propagation in the deducers, not hidden behind an
axiom about the engine. The real engine (`FactKB.deduce_all_facts` over the
edited `_assume_rules`) appears only as the **A-reference** G-AX validates the
deep model against. There is no consumed `@ContractOnly` axiom (no dead axiom).

## D. verify(model) ⇒ resolved

All thirty-one deducers verify only if they COMPLETE (§B.1 — so a record is
actually handed back, matching the real closure's drained work-list) AND each
returns the real engine's full record for its own seed: closed under
`consistent_theory` (A2) and matching every pinned trit (all 22 fields on every
one of the thirty-one seeds; A3, A3b, A3c, A3d, A3e–A3j, A4). That forces boundedness to
resolve on each of the five positive-membership seeds SEPARATELY — including the
`rational` seed where wholeness is Unknown and the `irrational` seed which the
exclusion places outside the rationals, so no one of them can borrow another's
verdict — while leaving it Unknown on the four negative-membership seeds and
False, with the whole membership cascade, on the unbounded seed. Those are
exactly the statuses the hidden tests observe across the seed families.
Every other clause group of the theory is likewise forced on a seed where
nothing else settles it (A3e–A3j), so a verifying record cannot drop a
containment, an exclusion, a weak-region equivalence, the origin rule or any of
the thirteen punctured-real-line rules either, and no field of any seed's record
is left for it to choose (A3j).
By R (trit ↔ `Optional[bool]`, dict ↔ record, `deduce_all_facts` closure ↔
straight-line propagation) the verified deducers compute the same fact tables the
real engine computes under the edited `_assume_rules` on all thirty-one seeds. By
G-AX the deep theory `consistent_theory` holds in the real post-patch engine and
all thirty recorded seeds' records are the real engine's (and both prepatch
variants fail in the pre-patch engine), so the
model’s obligations ARE the gold rule set’s closure on the tested seeds. The gold
patch (which edits exactly those rules) resolves (G-RESOLVE). Rule-level
adversarial sweep: of 107 candidate rule sets, every one that reproduces all
thirty-one records was harness-run to resolved=TRUE, and every resolved=FALSE
one violates a pinned record (§B, fourth correction). The trust points are the two of PLAN §1.1: A-reference
soundness (G-AX) and refinement fidelity (this document, G-EQ).

## E. Leakage disposition — relaxed, and why

This instance is a `problem_statement` ↔ gold MISMATCH: the public statement asks
only that an `even` quantity be known bounded, while the gold edit adds the
boundedness conjunct to four other classes and lets `even` inherit it
transitively. Re-measured at `base_commit` + the frozen `test_patch`: adding
`'even -> finite'`, adding `'integer -> finite'`, or adding the exact
`hints_text` suggestion `'rational -> real & finite'` alone each leaves all three
FAIL_TO_PASS tests failing (the last stops at `oo.is_algebraic is False`), while
the gold patch passes all three. So a spec strong enough to reject those three
impls must name all four boundedness-forcing classes and the two-directional
closure — vocabulary that is 0x in the `problem_statement`. The bundle therefore
ships `RELAXED_LEAKAGE.md` with `meta.json relaxed_leakage = true`; G-LEAK
records `relaxed`. Only no-leakage relaxes: `verify ⟹ correct` is untouched, and
§B / §D above are the argument that it holds.
