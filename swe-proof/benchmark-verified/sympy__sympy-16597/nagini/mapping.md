# mapping.md — sympy__sympy-16597

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 6fd65310fa3167b9626c38a5487e171ca407d988`, states the type
abstraction, and gives the provenance of the deep-model reference (the rule
engine) the deep model is validated against.

Leakage disposition: **relaxed** — see `RELAXED_LEAKAGE.md` (`problem_statement`
↔ gold mismatch; a faithful spec must name the boundedness-forcing classes).

Repo files under change: `sympy/core/assumptions.py` (the rule source),
`sympy/assumptions/ask_generated.py` + the runtime engine `sympy/core/facts.py`
(`FactRules.deduce_all_facts`, the forward-chaining closure these rules compile
into).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `KB` (record of `Optional[bool]` properties) | the `StdFactKB` / `FactKB` knowledge base populated for a `Basic` object (`sympy/core/assumptions.py:208` `StdFactKB`; `sympy/core/facts.py:473` `FactKB(dict)`); each field ↔ one `is_<fact>` entry | a deduced three-valued fact table for one quantity |
| `consistent_theory(k)` *(deep model — A-reference)* | the set of implication rules `_assume_rules = FactRules([...])` (`sympy/core/assumptions.py:163-201`) AFTER the gold edit, as realized by the forward-chaining closure `FactKB.deduce_all_facts` (`sympy/core/facts.py:501-537`) | pure spec: the record is closed under the (edited) containment relations |
| `deduce_even()` | the deduction performed when a `Symbol('x', even=True)` is queried — `make_property`/`_ask` driving `deduce_all_facts` from the seed `even=True` (`sympy/core/assumptions.py:238-310`) | the closure of the seed `even=True` |
| `deduce_odd()` | the same engine driven from `Symbol('x', odd=True)` | the closure of the seed `odd=True` |
| `deduce_integer()` | the same engine driven from `Symbol('x', integer=True)` | the closure of the seed `integer=True` |
| `deduce_rational()` | the same engine driven from `Symbol('x', rational=True)` | the closure of the seed `rational=True` |
| `deduce_irrational()` | the same engine driven from `Symbol('x', irrational=True)` | the closure of the seed `irrational=True` |
| `deduce_infinite()` | the same engine driven from the SIGN-FREE unbounded real seed `Symbol('x', infinite=True, real=True)`. The two concrete unbounded quantities `S.Infinity` / `S.NegativeInfinity` (`sympy/core/numbers.py`) are this seed plus a declared direction; they agree with it on every membership and differ from each other on sign, which is why the seed itself resolves no sign region (§3.1, third correction) | the closure of an unbounded real seed, direction not assumed |
| `deduce_integer_nonnegative()` | the same engine driven from `Symbol('x', integer=True, nonnegative=True)` | the closure of a whole number bounded below by zero |
| `deduce_integer_nonpositive()` | the same engine driven from `Symbol('x', integer=True, nonpositive=True)` | the closure of a whole number bounded above by zero |
| `deduce_not_rational()` | the same engine driven from `Symbol('x', rational=False)` | the closure of a non-membership seed |
| `deduce_not_irrational()` | the same engine driven from `Symbol('x', irrational=False)` | the closure of a non-membership seed |
| `deduce_not_even()` | the same engine driven from `Symbol('x', even=False)` | the closure of a denied-parity seed |
| `deduce_not_odd()` | the same engine driven from `Symbol('x', odd=False)` | the closure of a denied-parity seed |
| `deduce_real_nonrational_bounded()` | the same engine driven from `Symbol('x', real=True, rational=False, finite=True)` | the closure of a seed meeting irrationality's defining conditions |
| `deduce_real_transcendental()` | the same engine driven from `Symbol('x', real=True, transcendental=True)` | the closure of a real transcendental: bounded, hence meeting the irrationality condition |
| `deduce_integer_nonodd()` | the same engine driven from `Symbol('x', integer=True, odd=False)` | the closure of a seed meeting evenness's defining conditions |
| `deduce_algebraic_bounded()` | the same engine driven from `Symbol('x', algebraic=True, finite=True)` | the closure of a bounded algebraic seed — the containment `algebraic -> complex` (`assumptions.py:168`) observed on a record whose realness is Unknown |
| `deduce_not_nonnegative()` | the same engine driven from `Symbol('x', nonnegative=False)` | the closure of a refused weak sign region: `positive == nonnegative & nonzero` (`assumptions.py:182`) denies strict positivity, and `prime`/`composite -> positive` (`:190-191`) deny both classes |
| `deduce_real_not_nonnegative()` | the same engine driven from `Symbol('x', real=True, nonnegative=False)` | the closure of a real quantity refused the region bounded below by zero — `nonnegative == real & !negative` (`:186`) run backwards makes it strictly negative |
| `deduce_real_not_positive()` | the same engine driven from `Symbol('x', real=True, positive=False)` | the closure of the defining condition of `nonpositive == real & !positive` (`assumptions.py:185`) |
| `deduce_real_not_negative()` | the same engine driven from `Symbol('x', real=True, negative=False)` | the closure of the defining condition of `nonnegative == real & !negative` (`assumptions.py:186`) |
| `deduce_nonnegative_nonpositive()` | the same engine driven from `Symbol('x', nonnegative=True, nonpositive=True)` | the closure of the origin: `zero == nonnegative & nonpositive` (`:183`) followed by `zero -> even & finite` (`:188`) |
| `deduce_prime()` | the same engine driven from `Symbol('x', prime=True)` | the closure of a prime seed: `prime -> integer & positive` (`:190`) plus the exclusion carried by `composite -> integer & positive & !prime` (`:191`) |
| `deduce_noncomposite_positive_even()` | the same engine driven from `Symbol('x', composite=False, positive=True, even=True)` | the closure of the beta rule at `assumptions.py:192` (a non-composite quantity is non-positive, or odd, or prime) with its other two disjuncts denied by the seed |
| `deduce_nonzero()` | the same engine driven from `Symbol('x', nonzero=True)` | the closure of `nonzero == real & !zero` (`assumptions.py:200`): the punctured real line |

The thirty-one deducers are thirty-one instantiations of the SAME callee
(`StdFactKB.__init__` → `FactKB.deduce_all_facts`) at thirty-one different
seeds. They exist because `consistent_theory` is a predicate on ONE record: a
clause `rational=T -> finite=T` is vacuous on any record where boundedness is
resolved for another reason, so instantiating the closure at one seed does not
observe WHICH memberships force boundedness. The same argument applies to every
other clause of the theory — `algebraic=T -> complex=T` says nothing on a record
whose realness already forced complexity, and `real=T & positive=F ->
nonpositive=T` says nothing on a record that never refuses a strict sign — so
each clause group needs a seed on which the status it decides is otherwise free.
See §3.1.

The gold patch changes the **rule data**, not the engine: it adds `finite` to
the consequents of `rational`, `algebraic`, `transcendental`, `irrational`
(`assumptions.py` hunk) and regenerates the compiled CNF / dict mirrors
(`ask_generated.py` hunk). The runtime closure (`facts.py`) is unchanged; it
simply now propagates the new edges. (The patch also touches `power.py`,
`tree.py`, `indexed.py` — see §3.)

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a fact value `True` / `False` / `None` (the three-valued result of `is_<fact>`) | `Optional[bool]` field (`True` / `False` / `None`) | identity: `obj.is_<fact>` ↔ `k.<fact>` |
| the `StdFactKB` dict keyed by fact name | a `KB` record with one field per relevant fact | `kb[fact]` ↔ `getattr(k, fact)`; only the facts the witnessed queries touch are carried |
| `FactKB.deduce_all_facts` forward-chaining fixpoint (`facts.py:501`) | a straight-line propagation following the rule edges, one assignment per fired implication | each `self._tell(key, value)` for an implication edge ↔ one `k.<consequent> = <value>` assignment; the closure’s *result* (a fact table closed under the rules) is what both sides produce, captured by `consistent_theory` |
| the seed assumption set passed to `StdFactKB(facts)` | the initial field assignment(s) in each deducer’s impl (`k.even = True`, etc.) | identity on the seeded facts |

The whole-string / object machinery is irrelevant here: the only observable is
the trit fact table, which is modelled field-for-field.

## 3. Deep-model reference provenance (kind-A-reference — checked by G-AX)

### 3.1 `consistent_theory` + deducers ↔ the edited rule engine (A-reference)
**Reference:** the forward-chaining closure of `_assume_rules` after the gold
edit. The changed behaviour (the rule set) is modelled **deeply** as the closure
predicate `consistent_theory` (the spelled-out containment theory) and the
thirty-one straight-line deducers, one per instantiated seed; there is **no
`@ContractOnly` axiom** the proof consumes.

The gold edit (`sympy/core/assumptions.py:163-201`) is, line-for-line:
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
plus the pre-existing edges (`integer -> rational`, `real -> complex`
(`assumptions.py:169`), `even/odd -> integer`, `even == integer & !odd`
(`assumptions.py:176`, the `!odd` direction `even -> !odd`),
`prime/composite -> integer`, `zero -> even & finite`, `infinite -> !finite`,
`noninteger == real & !integer` (both the forward `real & !integer -> noninteger`
and the reverse exclusion `integer -> !noninteger`)). The engine derives every
**contrapositive** automatically (`facts.py:deduce_alpha_implications` adds
`(Not(j), Not(i))` for each `i -> j`, `facts.py:116`), which is why
`consistent_theory` carries the contrapositive clauses `!rational -> !integer`,
`!finite -> !{rational, algebraic, irrational, transcendental}`,
`!integer -> !{even, odd, prime, composite}`. The `transcendental`/`irrational`
`==` rules contribute the forward `T -> finite` edge used here. The model carries
the membership consequences the F2P/P2P queries actually reach — including the
pre-existing `real -> complex`, `even -> !odd` and `integer -> !noninteger`
facts, which over-cover the caller-reachable facts; over-covering a reachable
fact is sound, and each is exactly what the real engine deduces (G-AX validated).

The theory also carries the SIGN, ORIENTATION, SELF-ADJOINTNESS and
WHOLE-NUMBER-CLASS clauses, all of them pre-existing rules of the same
`_assume_rules` block (`assumptions.py:163-201`, verbatim):
```
'real           ->  hermitian'          'imaginary      ->  antihermitian'
'imaginary      ->  !real'              'nonzero        ==  real & !zero'
'negative       ==  nonpositive & nonzero'
'positive       ==  nonnegative & nonzero'
'zero           ==  nonnegative & nonpositive'
'nonpositive    ==  real & !positive'
'nonnegative    ==  real & !negative'
'zero           ->  even & finite'
'prime          ->  integer & positive'
'composite      ->  integer & positive & !prime'
'!composite     ->  !positive | !even | prime'
```
`FactRules` compiles each `==` in both directions and adds every
contrapositive, which is where the model's clauses `positive=T -> real=T`,
`real=F -> nonpositive=F`, `real=T & positive=F -> nonpositive=T`,
`nonpositive=T & nonnegative=T -> positive=F`, `prime=T -> positive=T`,
`hermitian=F -> real=F` and their companions come from. These are behaviour the
hidden battery observes directly (`test_I`, `test_symbol_real`,
`test_symbol_zero`, `test_symbol_falsepositive_real`,
`test_Mul_is_prime_composite`, `test_composite`), and the nine seeds added on
2026-08-16 are what make them observable one antecedent at a time (§3.1, fourth
correction).

**Soundness check (G-AX):** `axiom_check.py` imports the REAL `sympy` package
(the patched library) and:
  * asserts the F2P-witnessed queries directly and non-skipped — `Symbol('e',
    even=True).is_finite is True` (deduce_even) and `S.Infinity` /
    `S.NegativeInfinity` resolving is_finite / is_rational / is_integer /
    is_even / is_odd / is_algebraic / is_transcendental / is_irrational /
    is_composite to False and is_noninteger to True (deduce_infinite);
  * asserts the complete record of ALL THIRTY seeds carried in
    `SEED_RECORDS` (the thirty-one instantiated seeds less the unbounded ones,
    which is asserted separately just above), so the per-seed obligation is
    checked against
    the real engine and not only inside Nagini: the five bounded seeds each
    resolve is_finite to True and the four frontier seeds each leave it None.
    Run against a rule set that bounds the parity seed alone, this check fails
    at `PER-SEED FAIL (deduce_odd)`; run against the pre-patch engine it fails
    at the even seed. For the two one-sided seeds the asserted table includes
    the four sign statuses, so the model's sign pins are measured too; for
    the nine seeds added on 2026-08-16 the asserted record is the FULL
    twenty-one-field table, sign, orientation and self-adjointness included; and
    for EVERY seed the asserted record now also carries the non-zero status,
    merged in from `SEED_NONZERO` (nine True, one False on the origin seed,
    fourteen Unknown), so all twenty-two fields are measured on all thirty-one
    seeds. Run against a rule set that reads the non-zero status off parity this
    check fails at `PER-SEED FAIL (deduce_even)`;
  * asserts SIGN NEUTRALITY of the unbounded seed: the two concrete unbounded
    quantities carry opposite signs (`oo.is_positive is True`,
    `(-oo).is_negative is True`), and `Symbol('u', infinite=True, real=True)`
    leaves all four of is_positive / is_negative / is_nonpositive /
    is_nonnegative None. Run against a rule set that derives a sign or a
    one-sided bound from unboundedness this check fails — in fact such a rule
    set makes `S.NegativeInfinity` raise `InconsistentAssumptions` at import,
    so the library does not load at all;
  * reads the relevant `is_*` properties of a wide family of seeds (every
    single relevant assumption and every consistent pair, plus the numeric
    singletons `oo, -oo, 0, 1, 1/2, pi, E, I`) into a trit record and asserts
    that record satisfies **every clause of `consistent_theory`** at the
    property level (no value-membership proxy, no double mask — each implication
    `A -> B` is checked as `A in deduced ⇒ B in deduced`). All seventy-three
    clauses of `consistent_theory` are checked — including the thirteen
    punctured-real-line clauses added on 2026-08-16 (`nonzero -> real`,
    `!real -> !nonzero`, the two strict signs, both bounds by zero at once, the
    three consequences of denying it on the real line, the two strict signs it
    gives back with a weak bound, and odd parity / irrationality / unboundedness
    on the real line) — and the trit record read for each seed
    carries all twenty-two properties the model names. 1235 observations,
    exit 0 iff the real engine’s deduced facts are closed under the modelled
    theory (measured 2026-08-16: `G-AX OK: … validated against the REAL sympy
    assumptions engine on 1235 observations`). Run against the *pre-patch* engine the same check fails immediately
    on `even=True -> is_finite True` (it returns None), confirming the check is
    bound to the actual change.

The model carries the facts and clauses the witnessed deductions need plus the
adjacent caller-reachable facts (`real -> complex`, `even -> !odd`,
`integer -> !noninteger`) that pin the trits the F2P/P2P queries observe; every
clause is a sound consequence of (hence implied by) the real engine’s full
closure, so the A-reference is sound (over-covering reachable facts never
admits a non-resolving impl).

**Completion:** each deducer additionally demands `MustTerminate`, i.e. the
deduction always delivers its record. This is a property of the real callee:
`deduce_all_facts` (`facts.py:501-537`) drains a finite work-list (`while
facts:`, rebuilt only from newly-fired beta triggers, with `_tell`
(`facts.py:484-496`) returning False on an already-held key so nothing is
re-announced) and returns; `StdFactKB.__init__` (`assumptions.py:208-223`)
invokes it once without re-entry. Hence every `is_<fact>` query the F2P tests
make is answered rather than left pending. See refinement.md §B.1.

**Full-table pinning, per seed:** each deducer’s postconditions pin the trit of
EVERY `KB` field to the real engine’s deduced value for THAT seed — including
the Unknown fields (`prime is None` / `composite is None` for the even seed,
since parity does not decide primality) and the excluded memberships.
`axiom_check.py` asserts the complete record for thirty of the
thirty-one seeds against the real engine (`SEED_RECORDS`) — with the sign
statuses added for the two one-sided seeds, the full twenty-one-field
table for the nine seeds added on 2026-08-16, the non-zero status merged in for
every seed from `SEED_NONZERO`, and the unbounded seed checked
separately — so a spec-admitted record IS the real engine’s record on each of
them. Since 2026-08-16 this is literal for every field: `nonzero` used to be
mentioned by one deducer's postconditions only, and `consistent_theory` held no
permission to it, leaving it a FREE cell on the other thirty seeds that any
trit satisfied.

**Why ten seeds and not two (2026-08-15).** An earlier revision instantiated the
closure at two seeds (`even=True` and the unbounded real) and this section
claimed "no field of the observable is left under-constrained". That claim was
false, and the correction is the substance of this revision. The `is_finite`
observable ranges over eleven seed families; a knowledge base can reproduce the
even-seed and unbounded-seed records EXACTLY — every one of the 14 trits,
`consistent_theory` included — while leaving `Symbol(odd=True).is_finite`,
`Symbol(integer=True).is_finite` and `Symbol(rational=True).is_finite` Unknown.
Such a rival verified against the two-seed spec and its faithful patch was
harness-run to resolved=FALSE. The reason is structural: `consistent_theory` is
a per-record predicate, so `Implies(k.rational is True, k.finite is True)` is
satisfied VACUOUSLY on the even record — there `rational` and `finite` are both
True whichever relation forced them, and the record cannot express WHICH one
did. The fix is to make each boundedness antecedent observable on its own
record, with the others Unknown, which is what the five bounded-seed deducers
do. The four frontier deducers pin `finite is None` and bound the obligation
from the other side, so it cannot be met by resolving boundedness everywhere.

**Why the equivalences need their reverse direction (2026-08-15, second
correction).** The ten-seed revision above closed the per-antecedent boundedness
hole but left a second one. `consistent_theory` carried only FORWARD implications
and contrapositives, so for the relations the engine states as equivalences
(`irrational == real & !rational & finite`, `even == integer & !odd`) the
reverse direction — meeting the defining conditions MAKES a quantity a member —
was unobservable. Structurally: all ten seeds asserted either a plain membership
or a plain non-membership, and on such a record the reverse direction of an
equivalence is never exercised, because no seed hands the record the full
right-hand side of one while leaving its left-hand side to be deduced. A rival
theory that keeps every containment and contrapositive but propagates the
irrationality relation one way only reproduces all ten pinned records EXACTLY
and still fails the hidden behaviour: `Symbol(real=True, rational=False,
finite=True).is_irrational` and `Symbol('t', real=True,
transcendental=True).is_irrational` come back Unknown instead of True. The three
defining-condition seeds make that reverse direction observable, and the two new
clauses of `consistent_theory` state it. The `real=True, transcendental=True`
seed is the one that ties the two holes together: transcendence must resolve
boundedness AND the resolved boundedness must then feed the irrationality
equivalence, so a record that does the first without the second is rejected.

**Why the unbounded seed pins SIGN NEUTRALITY (2026-08-15, third correction).**
The fifteen-seed revision pinned every property of fourteen seeds but left four
of them free on the unbounded seed: `positive`, `negative`, `nonpositive` and
`nonnegative` were unstated there, and nothing else in the spec reaches them on
a record whose realness is seeded and whose boundedness is False. A rival record
that reads a direction off unboundedness alone — `positive = True, nonnegative =
True, negative = False, nonpositive = False`, or only the weaker one-sided
`nonnegative = True, negative = False` — therefore satisfied every clause and
VERIFIED (measured: three such rivals returned `CANDIDATE-COUNTEREXAMPLE:
shares spec AND verifies` before this correction). It is not a correct
alternative: the corresponding rule set (`infinite -> positive`, or
`infinite -> nonnegative`) makes `S.NegativeInfinity`'s own declared direction
contradict the derived one, so `FactRules` raises `InconsistentAssumptions`
while `sympy` is being imported and the whole hidden battery errors out. The
real engine resolves no sign region for the bare seed (measured:
`Symbol('u', infinite=True, real=True).is_positive is None`, and likewise for
the other three), because the two concrete unbounded quantities agree on every
membership and disagree on sign — each carries its direction as a separate
declared assumption. The unbounded seed now pins those four Unknowns, and the
three rivals are rejected. Note this is a claim about the SEED, not about
`oo`: `S.Infinity.is_positive` is True, but it is true by assumption and not by
deduction from unboundedness, which is exactly the distinction the seed-level
obligation has to preserve.

**Why thirty-one seeds and not fifteen (2026-08-16, fourth correction; the
count grew again at the sixth).** The
three corrections above each closed one vacuity and left the general case open:
a clause of `consistent_theory` constrains a record only where the status it
decides is not already settled for another reason, so EVERY clause group needs a
seed of its own. With the closure instantiated at the fifteen membership seeds
alone, nine clause groups were never witnessed: the containment of the algebraic
numbers in the complex quantities (every algebraic record among the fifteen is
also real, and realness forces complexity independently), the two weak sign
regions and their defining conditions (no seed refuses a strict sign), the
origin (no seed carries both bounds by zero), the exclusion between the two
distinguished whole-number classes and the recognition of the smaller one from
its defining conditions (no seed is prime, or non-composite-positive-even), and
the punctured real line (no seed is definitely non-zero). Machine-witnessed over
a survey of 107 rival rule sets, each written into `assumptions.py`, compiled,
and graded against the whole hidden battery in-container: 29 do not yield a
working library at all (the rule set makes `import sympy` fail), 49 violate a
record the fifteen-seed spec already pinned, **13 reproduce all fifteen pinned
records and are resolved=FALSE** — e.g. dropping the realness conjunct of
`nonzero == real & !zero` (fails `test_symbol_imaginary`), dropping `!prime`
from the composite rule (fails `test_Mul_is_prime_composite`), deleting
`zero == nonnegative & nonpositive` (fails `test_symbol_falsenonnegative`) — and
the remaining 16 reproduce every pinned record and are resolved=TRUE. The nine
seeds added here pin exactly the records that separate those 13: re-running the
same survey against the thirty-one-seed spec, all 13 violate a new pin, the 16
resolving rivals stay admitted, and no rival is both admitted and
resolved=FALSE.

**Extensional, not intensional (over-fitting guard).** The obligation states the
resolved STATUS of each seed's closure, never which rule produced it. This is
required for soundness in the other direction: an algebraic-only boundedness
edge is a genuinely correct alternative fix (harness-verified resolved=TRUE) and
is extensionally identical to gold on every probed seed, so it remains admitted.
For the same reason boundedness for the BARE seeds `algebraic=True` and
`transcendental=True` is NOT pinned anywhere: two further harness-resolving
variants leave one or the other Unknown, so a clause pinning them would reject a
correct implementation. The three defining-condition seeds were chosen under the
same discipline. Over a surveyed pool of 74 rule sets that each reproduce the ten
pinned records and pass the whole hidden battery, every field pinned for
`real=True, rational=False, finite=True`, for `real=True, transcendental=True`
and for `integer=True, odd=False` takes the SAME value in all 74; fields that
dissented anywhere are left free. Concretely: `Symbol(algebraic=True).is_finite`
dissents (3 of 74), bare `Symbol(transcendental=True).is_complex` dissents (1 of
74), and `Symbol(integer=True, even=False).is_odd` dissents (1 of 74) — so none
of those is pinned, and the mirror seed `integer=True, even=False` is not used at
all. Adding realness to the transcendental seed is what makes its record
invariant, which is why the pinned seed is `real=True, transcendental=True`
rather than `transcendental=True` alone.

The nine seeds of the fourth correction were chosen under the same discipline,
measured against the 16 rule sets that reproduce every pinned record and pass
the whole hidden battery: every one of the twenty-one fields of each new seed's
record (twenty-two for the punctured-line seed) takes the SAME value in all 16,
so no new pin can reject a correct alternative. Candidate seeds whose records
were NOT invariant were dropped rather than weakened: a bare `imaginary=True`
seed was rejected because `Symbol(imaginary=True).is_complex` moves under an
admitted rival (the rule set without `imaginary -> complex` passes the whole
battery), and for the same reason the seeds `transcendental=True, finite=True`,
`positive=False` alone, `complex=False` and `algebraic=False, finite=True` are
not used. This is also why the containment seed is `algebraic=True, finite=True`
rather than `algebraic=True`: per A5 the boundedness of a bare algebraic
quantity differs across correct alternatives, so boundedness is handed over as
an assumption instead of being pinned as a deduction.

**Why twenty-two fields and not twenty-one (2026-08-16, fifth correction).** The
fourth correction gave every clause GROUP a seed; it did not give every FIELD a
pin. `nonzero` was mentioned by the postconditions of exactly one deducer —
`deduce_nonzero`, whose hypothesis it is — and `consistent_theory` did not even
hold a permission to it, so no clause of the closure predicate could speak about
it. On the other thirty seeds it was a free cell: True, False and Unknown
all verified. Four rivals differing from gold in that cell alone were measured to
verify against the fourth-correction spec (`even -> nonzero`, the origin claiming
it, a strictly positive whole number denying it, and the real-transcendental seed
claiming it — the last is the shape of the recorded `verify ⇏ resolved` witness,
whose faithful rule set `transcendental -> nonzero` also makes every
transcendental real through `nonzero == real & !zero` and so fails
`test_issue_4149`). The column is now pinned on all thirty-one seeds and
`consistent_theory` carries the thirteen punctured-real-line clauses. Both
directions of the over-fitting guard were measured before the pins were written:
each of the thirty-one per-seed values was read off the modelled reference
(`base_commit` + `patch.diff`) AND re-read identically with the modelled change
absent, so the column turns only on rules the gold hunk does not touch and cannot
separate gold from any correct alternative to it; and all thirteen clauses were
probed over 7741 real-engine observations (the numeric singletons plus every
satisfiable single, pair and triple of the twenty-one seed facts) with no
violation. The reject lane in `properties.py` (`nz-even-claim-nonzero`,
`nz-origin-claim-nonzero`, `nz-prime-deny-nonzero`, `nz-odd-drop-nonzero`,
`nz-real-transcendental-drop-nonzero`) witnesses all four shapes, and
`pos-real-transcendental-nonzero-first` / `pos-origin-nonzero-first` are the
order-insensitivity controls; measured, the five reject and the two verify.

## 4. Other gold hunks not modelled (faithfulness note)

The gold patch also edits `sympy/core/power.py` (`_eval_is_rational` early-exit
for `integer**integer`), `sympy/printing/tree.py` (adds `finite`/`infinite`
lines to a docstring example), and `sympy/tensor/indexed.py` (`Idx` accepts
`±oo` bounds). None of these are exercised by the FAIL_TO_PASS tests
(`test_infinity`, `test_neg_infinity`, `test_other_symbol`); they are
performance / cosmetic / unrelated-domain changes shipped in the same commit.
`patch.diff` is the **gold patch verbatim** (it applies at base_commit and
resolves the harness, G-RESOLVE), so these hunks ship intact; the verified model
faithfully captures the **tested** behaviour (the assumption-rule containment
theory the F2P tests observe).
