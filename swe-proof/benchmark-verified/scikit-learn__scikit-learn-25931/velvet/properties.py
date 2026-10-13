"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-25931 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region and, where a case legitimately re-proves, the
``prove_correct`` tactic body is changed — both elided from the consumer spec
view, so ``markers.same_spec`` holds and every ``prove_correct`` obligation
survives with a byte-identical statement). ``expect:"verify"`` passes iff (in
scope AND the file elaborates with every obligation closed); ``expect:"reject"``
passes iff (in scope AND it does NOT verify AND the case's refutation ``witness``
holds of the rival while FAILING on the frozen solution).

DEFENDED SURFACE — three contracted methods, IN THE FILE'S DECLARATION ORDER
(which is part of the frozen spec region and is load-bearing, see below), a
CALL-SITE ADMISSIBILITY wall built from three opaque screen properties, three
opaque matrix TYPES, FOUR opaque NUMERICAL carrier types (a produced score
sequence, a requested point, ONE SCORE of such a sequence, and the OFFSET a
fitting tail records), three opaque numerical callees and one recorded constant:

  screenHandle (presented : Presented) : Bool               -- declared 1st
    require screenAdvises presented = false  -- (P1) a matrix the screen has
                                             --      nothing to advise about
    ensures accepted = if screenRefuses presented then false else true
                                             -- (C1) the screen's VERDICT, and
                                             --      nothing besides: the method
                                             --      reports whether the matrix
                                             --      was accepted or turned away.
                                             --      It computes no score and it
                                             --      hands back no DATA, so no
                                             --      text can obtain a prepared
                                             --      matrix out of it (see the
                                             --      FOURTH lesson below).
  scorePublic (handle : CallerHandle) : Option (List Score) -- declared 2nd
    require screenAdvises (presentCaller handle) = false    -- (P1) as above
    require scorableAsGiven (preparedOf handle) = true      -- (P2) the matrix the
                                             --      screen hands back for it is
                                             --      one the scorer can consume as
                                             --      it stands (a DOMAIN FENCE, see
                                             --      below: a screen accepts some
                                             --      matrices the scorer refuses)
    ensures result = if screenRefuses (presentCaller handle) then none
                     else some (scoreValues
                                  (anomalyScores (preparedOf handle)))
                                             -- (C1) the verdict governs what is
                                             --      SERVED: nothing for a handle
                                             --      the screen refuses, and
                                             --      otherwise the per-sample
                                             --      scores of the prepared form
                                             --      of that handle's own numbers,
                                             --      whatever labelling the handle
                                             --      does or does not present
  fitComputeOffset (samples : Prepared) (q : Point) : Offset -- declared 3rd (LAST)
    require scorableAsGiven samples = true   -- (P1) consumable by the scorer
                                             --      exactly as it stands
    require hasSamples samples = true        -- (P2) at least one sample
    ensures offset = percentileAt (anomalyScores samples) q -- (C1) order statistic

  THREE OF THESE REQUIRES ARE DOMAIN FENCES, not screening claims: the two on the
  last method and the second on the entry point. Each excludes a region where the
  repository reports nothing at all -- an arrangement or a width the scorer
  refuses; a matrix holding no samples, and so no numbers to take an order
  statistic of -- and each is measured in axiom_check.py together with the control
  that it excludes no more than that. They give a rival extra hypotheses and no
  extra licence: every reject case below is refuted at a matrix the fences admit.

  THE ENTRY POINT'S FENCE IS THE ONE ADDED LAST, and it is there because a screen's
  ACCEPTANCE does not settle what the scorer can consume. A handle in the newer
  sparse container is accepted by the public screen -- which hands back a prepared
  matrix of the same numbers, compressed by row, in the working precision -- and
  the scorer then refuses that matrix, as does the public entry point itself
  (measured, base commit: axiom_check.py ``check_sparse_container_fence``, with the
  dense matrix and the older sparse containers of the same numbers all consumed and
  all served as the control, and with ``fit`` refusing the newer container outright
  so no offset tail holds one). Without the fence the served-value clause promised
  scores over a region where the repository raises instead of serving any; with it,
  the clause is unconditional exactly where scores exist -- and in particular over
  every arrangement the graded scoring surface uses. It is a restriction on the
  argument and not on the result, so it is not a value an implementation may drop.

  A THIRD FENCE USED TO STAND HERE AND IS A TYPE NOW, which is the FIFTH MEASURED
  LESSON of this bundle. The percentile point carried ``require 0 ≤ q ∧ q ≤ 100``,
  because the order-statistic callee refuses a point outside the range a percentage
  occupies (measured — axiom_check.py ``check_percentile_point_fences``). A judge's
  audit refuted that arrangement four ways with a single move: a precondition
  fences the argument the METHOD IS CALLED WITH, while the total reference
  ``percentileAt`` may be NAMED at any term of its argument type ANYWHERE INSIDE A
  BODY — including in a value-neutral position the postcondition cannot see, e.g.
  ``let probe := percentileAt scores 1000; if probe == probe then … else …``, and
  the same probe inside ``scorePublic``. Those rivals VERIFIED while their faithful
  counterparts raise from the order-statistic callee and resolve nothing (measured
  in the official image on the sharpest of them: F2P 0/1, and 4 of 21 P2P failing).
  The repair has the same shape as the fourth lesson's: both numerical arguments
  became OPAQUE CARRIER TYPES (``Scores``, ``Point``) with a one-way reading
  ``scoreValues : Scores → List Score``, so a point or a sequence the callee refuses
  is now INEXPRESSIBLE rather than merely un-called-with. Measured against the
  frozen file as it now stands, every rival of that family fails to elaborate:
  ``percentileAt scores 1000`` (and the same probe inside ``scorePublic``) gives
  ``failed to synthesize OfNat Point 1000``, ``percentileAt scores (q + 100.5)``
  gives ``failed to synthesize HAdd Point Float Point``, and ``percentileAt ([] :
  List Rat) q`` gives ``Application type mismatch: The argument [] has type List
  Rat but is expected to have type Scores in the application percentileAt []``.
  A precondition could not have delivered any of those.

  THE SIXTH MEASURED LESSON IS THAT SAME SHAPE ONE STEP FURTHER IN: THE READING'S
  ELEMENTS ARE CARRIERS TOO. ``scoreValues`` used to hand back a sequence of plain
  numbers (``Scores → List Rat``). But READING a produced sequence is itself PARTIAL
  in the POSITION read: asked for the score at a position the sequence does not
  have, the repository reports nothing and refuses the read, and it refuses it even
  where the value read is then cancelled away, because the refusal happens at the
  READ (measured — axiom_check.py ``check_score_index_fences``: a position far past
  the end, the length itself, and the mirror position before the start, over four
  sequence lengths, on the screen-free sequence and on the public entry point's own
  served one; 140 observations). A sequence of PLAIN NUMBERS admits an UNGUARDED
  read at any position, since such a read needs only a default element to fall back
  on where the position is absent — so a rival could name a score in a region where
  the repository derives none, and name it in a value-neutral position, which is
  exactly where no postcondition can see it. A judge's audit refuted the previous
  arrangement four ways with that one move: ``let probe := nums[1000]!`` in the
  offset tail (cancelled into the offset, and as a two-way branch on the value
  read), the same read at ``nums[nums.length]!``, and the same probe inside
  ``scorePublic``. All four VERIFIED, and their faithful counterparts were run in
  the official image: the three on the offset tail fail the graded test and 4 of the
  21 P2P tests, and the one on the public entry point fails 13 of the 21. The repair
  is the fifth lesson's, applied to the ELEMENT type — ``scoreValues : Scores → List
  Score`` over an opaque ``Score`` — so an unguarded read has no default to fall back
  on and no term of the element type can be written down at all. Measured against
  the frozen file as it now stands, every rival of that family fails to elaborate
  with ``failed to synthesize Inhabited Score`` (and, where it branched on the value
  read, ``failed to synthesize Decidable``), while the reads the repository DOES
  serve stay expressible and still verify: the guarded read that reports the ABSENCE
  of a position (``nums[0]?``) and the sequence's length both verify (measured, exit
  0). The carrier costs the logic nothing — no clause here does arithmetic on a
  single score, the order statistic takes the SEQUENCE, and the served-value clause
  is an equality of sequences, which is why ``public-serves-empty-scores`` below
  still attacks it with ``return some []``.

  THE SEVENTH MEASURED LESSON IS THE SAME SHAPE ONE STEP FURTHER OUT: THE VALUE THE
  TAIL REPORTS IS A CARRIER TOO, BECAUSE ARITHMETIC IS TOTAL IN THE REFERENCE
  LANGUAGE AND PARTIAL IN THE REPOSITORY. The offset used to be a plain rational
  (``percentileAt : Scores → Point → Rat``, ``fitComputeOffset … : Rat``). Rational
  division is TOTAL there — ``x / 0`` is the rational 0, and ``(x - x)⁻¹`` is 0 —
  while the repository derives NO number for either: as a plain real it refuses the
  division outright (``ZeroDivisionError``) and in the working precision its scorer
  produces it reports a non-finite value with a ``RuntimeWarning``, and cancelling
  the quotient away does not avoid it because the divergence happens AT THE
  ARITHMETIC (measured — axiom_check.py ``check_offset_arithmetic_fences`` legs (b)
  and (c)). An independent audit of the previous arrangement refuted it with exactly
  that: rivals that returned the right order statistic while ALSO forming ``off / 0``
  in a discarded position verified, and the counterpart patch of the sharpest of them
  was run in the official image — the graded test passes and FOUR of the P2P scoring
  and prediction tests fail (``test_iforest_works``, ``test_score_samples``,
  ``test_iforest_chunks_works1``, ``test_iforest_chunks_works2``), consistently over
  three attempts, so it resolves nothing. No postcondition can fence that shape: the
  quotient is DISCARDED, so no clause about the reported value can see it, and a
  restriction on a parameter fences an argument rather than the arithmetic a body
  writes. The repair is the fifth lesson's again, on the RESULT type: the reported
  offset is the opaque carrier ``Offset``, whose only terms are ``percentileAt
  (anomalyScores samples) q`` and ``defaultOffset``, the constant the requestless
  fitting path records (-0.5 on every model measured, and never the order statistic a
  requested contamination level determines — same leg, (a)). Measured against the
  frozen file as it now stands, every rival of that family fails to elaborate
  — ``failed to synthesize HDiv Offset ℕ`` for the quotient by a written zero,
  ``failed to synthesize HSub Offset Offset`` for the quotient by its own difference
  and for the reciprocal of that difference, ``failed to synthesize Neg Offset`` for
  the negation, and ``Application type mismatch: The argument off has type Rat but is
  expected to have type Offset`` for an aggregate or a rational literal — while what
  the repository does derive stays expressible and still verifies (the order
  statistic itself, exit 0; the guarded read; the sequence's length).
  TWO REJECT CASES WERE RETIRED BY THIS MOVE and are recorded in the accounting
  below: ``fit-aggregates-scores`` (the sequence's length as the offset) and
  ``fit-negates-offset`` (the orientation position) are both INEXPRESSIBLE now, and
  ``fit-forge-offset-value`` — the only offset a text can write that the tail must
  not report — is what remains on that clause, at the grounded constant instead of a
  rational literal.

  WHAT THIS CARRIER DOES NOT FENCE, AND WHY THAT IS NOT A HOLE. A number the text
  derives with arithmetic the repository leaves undefined, and then DISCARDS, still
  elaborates, and nothing in a spec can prevent it. FOUR ROUTES to that shape were
  measured against the shipped file, each exit 0, and the residual is exactly as wide
  as they are: written constants alone (``let junk := (1 : Rat) / 0`` — also exit 0
  before this carrier existed, so the carrier neither opened nor closed it); a
  screening verdict, through the branch of the Boolean the file does expose (``let b
  := (if screenAdvises (presentPrepared samples) then (1 : Rat) else 0)`` then ``let
  junk := b / (b - b)``); the produced sequence's LENGTH as a rational (``let n :=
  (nums.length : Rat)`` then ``let junk := n / (n - n)``); and that same length in
  ``Nat``, divided by zero (``let junk := nums.length / 0``), where the division is
  the reference language's truncating one. No clause and no type here reaches any of
  them: the numbers are the reference language's own, and every Boolean and every
  length the file exposes is a route to one. None is a refutation, and the reason is
  the R-ARITH reading rule (mapping.md §2.2, published with the spec): with the
  offset a carrier there is no number left in the file that models a repository
  quantity, so an arithmetic term is a CONSTANT of the reference language and reads
  back as the number it evaluates to, not as an operation the repository performs.
  The rule is grounded, not asserted, in BOTH directions: the reference language's
  rational arithmetic is exact where the repository's on these numbers is not (same
  leg, (e)), and its division is total and its ``Nat`` subtraction truncating where
  the repository's are neither (``(1 : Rat) / 0``, ``(0 : Rat)⁻¹``, ``(1 : Int) / 0``
  and ``(5 : Nat) / 0`` are each ``0`` and ``(3 : Nat) - 5`` is ``0``, measured as
  ``example``\ s that verify, while the repository raises for the first and reports
  ``-2`` for the last). An operator-by-operator reading of arithmetic is therefore
  unfaithful in both directions and cannot be the intended one. Under the value
  reading a discarded number is dead text, and the values the tail can REPORT are
  exactly the two the repository has.

THE MATRICES ARE OBJECTS AND NOT SEQUENCES OF NUMBERS, AND THAT IS A CORRECTION
RATHER THAN A PREFERENCE. An earlier revision of this spec carried the matrices as
their CONTENTS (``List Rat``) and applied the screen properties to that. It is
unsound, and the counterexample is inside this bundle's own G-AX fixture: two
matrices holding bit-identical numbers disagree about the labelling advisory (one
presents the recorded labelling, one presents none), about the refusal (the same
numbers arranged as another width are turned away) and about readability (the same
numbers compressed cannot be read as they stand) — all three measured,
axiom_check.py ``check_object_properties``. A property of the contents would have
had to answer twice for one argument, so the four legs of that fixture were
jointly unsatisfiable on the old carrier: the spec was describing something that
cannot exist. The repair is the three opaque object types above, with two
non-invertible presentations into ``Presented``; the screen properties are
properties of the OBJECT. The two NUMERICAL arguments became carrier types as
well, for the related measured reason recorded under the FIFTH lesson above —
their callee is partial in both, and only an argument type fences every naming
site — with ``scoreValues`` as the one-way reading of a produced score sequence,
and the SIXTH lesson then carried that reading's own ELEMENTS the same way and for
the same measured kind of reason, and the SEVENTH the value the tail REPORTS, whose
arithmetic is total in the reference language and partial in the repository.

THERE IS NO SCREENING TALLY ANYWHERE IN THIS SPEC, AND THE HISTORY IS MEASURED.
Earlier revisions modeled the screen as a ``mut checks : Nat`` counter, pinned by
``ensures checks = checksOld + 1`` on the entry point that screens and
``ensures checks = checksOld`` on the paths that must not. Both pins were refuted
through the same gap: a tally is a FREELY-WRITTEN value, so a postcondition over
it pins its FINAL VALUE and never whether the screening call was EXECUTED. The
whole family verified — discard the returned tally, advance-then-restore
(``let saved := checks; checks := checks + 1; …; checks := saved``),
arithmetic-cancel, double-screen — while every faithful counterpart re-screened
the already-prepared matrix and left the reported advisory in place.

Two further defects of the tally revision were measured and are also closed here:

  * THE VALUE CLAUSE WAS CONDITIONED ON THE LABELLING. The screening entry point
    used to carry ``require carriesLabels samples = true`` — a matrix still
    presenting the labelling recorded at fit time — so its value clause said
    NOTHING about the ordinary unlabelled handle, which is what most of the graded
    scoring surface uses. A one-line rival serving ``if carriesLabels samples then
    anomalyScores samples else []`` verified while breaking every unlabelled
    caller. A labelling governs the ADVISORY and the refusal of a DISAGREEING
    labelling — never a score value (measured: axiom_check.py leg (iv), where the
    unlabelled handle of a labelled model's own numbers is scored to bit-identical
    values). So the value leg is unconditional in the labelling, and the labelling
    appears only in ``screenAdvises`` (the argument restriction) and in
    ``screenRefuses`` (a labelling that disagrees).
  * STATEMENT ORDER WAS LICENSED AWAY. With the screen modeled as a tally, the
    order of "advance the tally" against "bind the scores" was declared
    unobservable, and this battery shipped that shape as a POSITIVE control
    (``pos-public-order-swap``). It is the reading that lets an impl serve numbers
    derived from a matrix the screen has not yet accepted. The verdict is now an
    OBLIGATION rather than prose: both ``accepted`` and ``result`` are functions of
    ``screenRefuses``, so a value the verdict does not sanction is rejected by the
    verifier. The shape that positive used to bless is therefore in the REJECT lane
    below with a witness (``public-ignores-refusal``, ``screen-ignores-refusal``),
    and the positive control for those methods is a reshape in which the verdict
    still selects what comes out.

THE THIRD MEASURED LESSON — HOW OFTEN A SCORER IS INVOKED IS NOT WITNESSABLE BY
ANY POSTCONDITION HERE, AND THE FAMILY IS CLOSED BY DECLARATION ORDER PLUS THE
HANDLE TYPE, NOT BY A CLAUSE. This is why the method order and the argument TYPES
above are load-bearing, and it is the reason this revision separates the SCREEN
from the SCORING.

An audit of the previous revision routed the offset derivation through a
scorer-invoking method under a guard on that method's own precondition:

    if screenAdvises samples then
      <derive the offset from the value reference>
    else
      let _r ← scorePublic samples          -- previous revision: a scoring method
      <derive the offset from the value reference>

The rival VERIFIED, and its faithful counterpart put the heavy chunked scorer to
work a SECOND time, which two P2P tests detect by asserting the exact chunk-row
call count. Four facts of this carrier were measured while diagnosing it:

  * a precondition is NOT an unguardable wall. Whatever the precondition mentions,
    an implementation may branch on it and make the call in the branch where it
    holds: the plain form ``if p then … else <call>`` discharges ``p = false`` for
    a ``Bool``-valued ``p``, and for a ``Prop``-valued one
    ``if @decide P (Classical.propDecidable _) then … else <call>`` does the same
    (measured: exit 0 for both; the dependent-``if`` and ``open Classical in``
    spellings are rejected by WPGen, which is a parser accident and not a wall);
  * so a precondition restricts WHICH ARGUMENTS a call may be made with, and it
    cannot restrict HOW OFTEN a reachable method is called;
  * an invocation count is not a value any postcondition here can see, a tally
    that would count it is advance-then-restore forgeable (above), and Velvet has
    no cost, fuel, or ghost-history facility;
  * the only barriers that survive are therefore DECLARATION SCOPE, ARGUMENT
    TYPES, and the total-correctness termination obligation.

The frozen spec closes the family with all three, and the closure is structural
rather than prose:

  * ONE SCORER-INVOKING METHOD, AND IT IS TYPED ON A HANDLE NOBODY CAN FORM.
    ``scorePublic`` is the only method that invokes a scorer, and its argument is
    a ``CallerHandle`` — an opaque axiom TYPE with no constructor, no
    ``Inhabited``/``Nonempty`` instance, and no term anywhere in the file. The
    fitting tail holds a ``Prepared``, and a prepared matrix cannot be read back as
    a caller handle: presentation to a screen (``presentCaller``,
    ``presentPrepared``) runs the other way and neither map is invertible, which is
    the modeling counterpart of the plain fact that the tail no longer holds the
    caller's labelled matrix. Measured against the frozen file, every route to that
    method from the offset tail fails to elaborate: ``scorePublic
    Classical.arbitrary`` and ``scorePublic (Classical.choice …)`` fail with an
    application type mismatch, ``scorePublic default`` with ``failed to synthesize
    Inhabited CallerHandle``, ``scorePublic ⟨⟩`` with ``Invalid ⟨…⟩ notation``.
    The ``sorry``-fabricated handle is not a route either: the project's single
    verifier entry point exits 3 on ``declaration uses 'sorry'``, so such a file
    is not a verifying rival at all (measured, exit 3), quite apart from having no
    repository text to be refined into.
  * DECLARATION ORDER AS SCOPE. ``fitComputeOffset`` is declared LAST, so no
    later method can route through it either; a rival that self-calls it is
    rejected by the total-correctness termination obligation (measured: ``fail to
    show termination for``). And ``scorePublic``, the one scoring method, is
    declared BEFORE it, so ``scorePublic`` cannot reach the offset tail: the two
    scoring-relevant methods are mutually unreachable, which is what makes "one
    scorer invocation per public call" structural. Declaration order lives in the
    frozen spec region, so no same-spec rival can reorder the file.
  * THE R-VALUE RULE (stated normatively in the frozen axiom comment and
    mapping.md §2) — ``anomalyScores samples``, ``scoreValues scores`` and
    ``percentileAt scores q``
    denote VALUES, not actions, and carry no repetition content: an impl naming
    such a value at several places reads back into the SAME repository text as one
    naming it once (the callee produces the value, a name is bound to it, and each
    occurrence uses that binding). So on the offset path the screen-free scores
    are reached as a value reference, and a duplicated reference is not a distinct
    behaviour to be rejected — it is the same behaviour spelled twice.

THE FOURTH MEASURED LESSON, AND IT IS WHY A SCREEN'S DATA IS A CALLER-SIDE VALUE
IN THIS SPEC. An earlier revision had the screening method hand back the prepared
matrix, pinned through an A-reference of type ``Presented → Prepared``. A judge's
audit refuted it seven different ways with a single move: a total pure reference
has no call site, so it carries no call-site obligation, and the offset tail could
simply NAME the screen's own output for the matrix it already holds and never
invoke the screening method at all. The faithful counterpart of naming it re-runs
the input preparation on data the caller never supplied — reported advisory
included — and its materialized patch failed the graded test in the official image
(measured: FAIL_TO_PASS 0/1 on the feature-name test, PASS_TO_PASS 21/21). The
lesson generalizes past this cell: an operation whose repository image carries an
AMBIENT EFFECT must not be modeled as a total function over an argument type the
defective context can form, because naming a value discharges nothing.

So the screen's output is now a reference of type ``CallerHandle → Prepared``
(``preparedOf``): a value only a text holding the CALLER'S handle can name, which
in this file is the public entry point — the one place a caller's matrix is
screened at all. The screening method's result is a VERDICT. And there is
deliberately no ``Presented → Prepared`` anywhere in the file, so a text holding
prepared data cannot obtain a re-prepared form of it by any route. Measured
against the frozen file as it now stands, every route the audit used fails to
elaborate rather than verifying:

  * ``preparedOf (presentPrepared samples)`` — ``Application type mismatch: The
    argument presentPrepared samples has type Presented but is expected to have
    type CallerHandle``;
  * ``preparedOf Classical.arbitrary`` — ``Application type mismatch``;
  * ``preparedOf default`` — ``failed to synthesize Inhabited CallerHandle``;
  * ``preparedOf (Classical.choice …)`` — the unprovable side goal ``⊢ Nonempty
    CallerHandle``.

WHAT REMAINS ADMISSIBLE ON THE OFFSET PATH IS HARMLESS, AND IT IS SHIPPED AS A
POSITIVE CONTROL RATHER THAN HIDDEN. The guarded shape above still verifies
against the frozen file with the SCREEN (which computes no score) in the branch:
an implementation that can prove, before screening, that the screen has nothing
to advise about the data it holds may screen it again. Its faithful
counterpart re-runs the input preparation only where no report can be drawn, so
it draws no report and runs no scorer a second time (the screening method computes
no score, and it hands back no data for anything to be derived from). Measured in
the official image: the counterpart resolves — F2P passes and all 21 P2P pass,
chunk-count assertions included. That is ``pos-fit-\
provably-silent-rescreen`` below. The re-screen the issue is about — the
UNCONDITIONAL one, which reports a labelling discrepancy about data the caller
never supplied — is rejected at the call site (measured: exit 1 on
``⊢ screenAdvises (presentPrepared samples) = false``) and is
``Solution_prepatch.lean``'s impl verbatim.

Consequently NO reject case below attacks invocation multiplicity: such a rival
either fails to elaborate (no handle term / non-terminating), in which case it is
not a spec weakness, or it is a duplicated value reference, which R-VALUE reads
back as the same text, or it is the provably-silent re-screen, which is correct
and is defended positively.

THE CARRIER AND WHY THE WITNESS ROUTE IS THE HOARE TRIPLE, NOT THE TESTER.
The postconditions reference the opaque
``anomalyScores``/``scoreValues``/``percentileAt``, the
opaque screen properties and the opaque carrier types, so the tester route
(``extract_program_for`` + ``derive_tester_for`` + ``decide``) is UNAVAILABLE:
extraction cannot compile a program whose result depends on a callee with no
executable code, and ``decide`` gets stuck on the opaque term (confirmed during
authoring: ``fitComputeOffsetExec ... depends on declaration 'anomalyScores',
which has no executable code``). So every reject witness refutes the method's
partial-correctness Hoare triple DIRECTLY at an arbitrary matrix of the relevant
type — ``¬ triple True (method args) (fun out => <clause>)`` — peeled through
``wp_pure``, checked in a file whose ``prove_correct`` blocks have been stripped
so no frozen tactic script can mask the verdict.

Every clause of this spec is OPAQUE-VALUED (there is no transparent tally left),
so every witness CONDITIONS on the sub-domain where the rival is wrong:

  * for the VERDICT legs the hypothesis fixes the opaque verdict at the probed
    matrix (``screenRefuses pr = true``, or ``= false``), which is what selects the
    branch the rival gets wrong;
  * for the VALUE legs the hypothesis says only that the two terms the rival
    confuses differ at the probed input (e.g. ``percentileAt (anomalyScores pf) p
    ≠ 0``);
  * every matrix binder — and, since the fifth lesson, the POINT binder too — is
    UNIVERSALLY QUANTIFIED: none of these types has a concrete term, so a witness
    takes an arbitrary matrix (``pr : Presented``, ``pd : Prepared``,
    ``hd : CallerHandle``) at an arbitrary requested point (``p : Point``) and
    conditions on the sub-domain where the rival is wrong. That is strictly
    stronger than probing one point, and it is the carrier's doing rather than a
    choice;
  * ``public-keys-on-advisory`` carries two hypotheses, deliberately: one is the
    method's OWN precondition instantiated at the probed handle
    (``screenAdvises (presentCaller ha_hd) = false``, i.e. the witness attacks
    INSIDE the modeled domain rather than outside it), the other is the sub-domain
    where the rival is wrong. They are about different terms and are jointly
    satisfiable (the axioms are unconstrained — verified by the gate's consistency
    probe); no witness ever carries two hypotheses about the same term.
    ``public-serves-empty-scores`` likewise carries a branch-selecting hypothesis
    and a value-difference one, about different terms.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling's mandatory
    frame-mutation rival overwrote a read-only input carrying only a half
    permission (``Acc(X_raw.has_labels, 1/2)``) and was rejected by the
    permission system. Velvet is referentially transparent: there is no heap, no
    aliasing, and no fractional permission. There is no ``mut`` binder at all in
    this revision, and ``samples``/``q``/``handle`` are immutable value
    parameters. No read-only input can be overwritten, so no discriminating
    witness could exist. Omitted because the class collapses on this carrier, not
    because it was hard; no substitute fabricated.

  * CONTROL-FLOW-EFFECT / SIDE-EFFECT ON SHARED STATE — the heart of this
    surface. The nagini sibling modeled the advisory as a side effect on shared
    estimator state (``fit_advisories``) and the offset provenance as unforgeable
    tokens. Here the advisory is an AMBIENT effect with no returned value, so it
    is carried as the screening method's argument restriction (which an impl
    cannot drop) rather than as a threaded output (which it could); and the
    refusal, which the caller does observe, is carried as the handed-back result.
    The control-flow rivals are therefore the lanes below: rivals that consult the
    wrong predicate or no predicate at all (``screen-ignores-refusal``,
    ``screen-refuses-everything``, ``public-ignores-refusal``,
    ``public-keys-on-advisory``, ``public-refuses-everything``), and — on the
    offset path — the re-screening family, which is rejected at the CALL SITE and
    is therefore not postcondition-witnessable (see the note above the reject
    lane).

  * UNGROUNDED-ORACLE ECHO — N/A in the wrong direction here. Every leg is
    opaque, so no rival can be refuted by computing the answer; each is refuted by
    conditioning on the sub-domain where it is wrong (above).

  * DIVERGENCE / NON-TERMINATION — NOTHING TO SHIP, and the reason is the
    TERMINATION OBLIGATION, not vacuity of the class and not a spec hole. Two
    earlier readings of this lane were both wrong and are corrected here by real
    builds against the frozen file as it now stands.

    The frozen ``Solution.lean`` carries ``set_option
    loom.semantics.termination "total"``. Under TOTAL correctness the verifier
    discharges a termination obligation, so a diverging rival is REJECTED rather
    than vacuously accepted. Measured (audit, real builds against this bundle):

      - the corpus divergence probe (a ``while True do pure ()`` prefix spliced
        into every impl region, each proof reduced to a bare ``loom_solve``) —
        exit 1, ``error: Decreasing annotations are required in total
        correctness semantics``;
      - the same prefix in fitComputeOffset's region alone — exit 1, same error;
      - a self-recursive rival — exit 1, ``error: fail to show termination for``;
      - the sharper shape, a loop that CARRIES a measure the verifier cannot show
        decreasing (``let mut q : Nat := 1; while q > 0 / invariant 0 ≤ q /
        done_with q = 0 / decreasing q do q := q``), exit 1 with the residual goal
        ``⊢ q < q`` under ``case «decreasing_1: q»``. This one is decisive: the
        refusal is the measure's OWN descent obligation, so it cannot be
        dismissed as merely the missing-annotation linter.

    So the class is NOT a ``partial`` hole, and there is no cohort in which it
    would be one. All 500 velvet bundles read ``total`` and open
    ``TotalCorrectness``; none reads ``partial``. The option and the ``open``
    also cannot drift apart, since the ``set_option`` elaborator itself runs
    ``openScope `TotalCorrectness``.

    Nothing is shippable as a reject case even so, and this is the part that is a
    carrier fact rather than a choice. A reject case needs a witness that
    ELABORATES against the rival, and the rival's own module does not elaborate:
    the termination obligation fails inside the method itself, so the witness
    file built from it dies on ``Decreasing annotations are required`` before the
    witness's ``example`` is ever reached (measured: exit 1 on the rival side,
    which the gate reads as ``witness-unproven``). The rejection is real and is
    already delivered by the verifier for every diverging impl of this spec —
    there is simply no separate manifest case that can carry it. Recorded as a
    demonstrated carrier limit on the WITNESS PROTOCOL, not as a known spec hole.

  * AXIOM lane — DROPPED. ``anomalyScores``/``percentileAt`` are G-AX-validated
    A-reference deep-model callees, and the matrix types, the object properties
    and the three screen properties are grounded by axiom_check.py as well; the
    sibling's four axiom probes are exactly what G-AX discharges for this bundle.
    The gate ignores ``AXIOM_TESTS`` regardless.

BINDER / CLAUSE COVERAGE. Every one of the three obligations is DEFENDED (a
soundness positive) and ATTACKED (a reject rival), and EVERY top-level clause is
attacked at more than one position:

  * ``screenHandle``'s conditional clause is attacked at BOTH branches — the
    refused one (``screen-ignores-refusal``: report as accepted a matrix the
    verdict turns away) and the accepted one (``screen-refuses-everything``:
    report every matrix turned away);
  * ``scorePublic``'s conditional clause at FOUR positions — the refused branch
    (``public-ignores-refusal``), the served branch
    (``public-refuses-everything``), the PREDICATE consulted
    (``public-keys-on-advisory``: branch on the advisory instead of the refusal),
    and the served VALUE (``public-serves-empty-scores``);
  * ``fitComputeOffset``'s single offset clause at the one position a text can
    still write wrong — the whole VALUE, reported as the constant the OTHER fitting
    path records instead of the order statistic the requested level determines
    (``fit-forge-offset-value``). Since the SEVENTH lesson that is not a narrowed
    attack surface but the whole of it: the reported offset is a carrier whose only
    two terms are the required order statistic and that constant, so the FUNCTION
    taken of the produced score sequence, the ORIENTATION of the result and the
    dependence on the REQUESTED POINT are pinned by the argument type rather than
    by a rival, and every shape that used to attack them fails to elaborate
    (measured, quoted below).

WHAT IS NOT ATTACKED, AND WHY IT IS A CARRIER FACT RATHER THAN AN OMISSION: there
is no separate reject case for the DATA a screen produces, because the screening
method produces none — that is the point of the fourth lesson above. The prepared
matrix a screen makes of a caller's handle is pinned where it is observable, in
``scorePublic``'s served value (``anomalyScores (preparedOf handle)``), and THAT
position is attacked (``public-serves-empty-scores``). A rival that served the
scores of a DIFFERENT prepared matrix cannot be shipped because it cannot be
written: ``preparedOf`` is the only producer of a prepared matrix in the file and
it takes the handle the method was given, so there is no second term to name.
Naming it twice is the same value twice (R-VALUE), and re-preparing an
already-prepared matrix changes neither the numbers nor the scores in the
repository (measured — axiom_check.py ``check_handle_properties`` leg (b)), so
there is no faithful counterpart at that position that fails to resolve.

The reject witnesses quantify EVERY binder of the offset clause universally —
since the fifth lesson neither the matrices nor the requested point has a concrete
term — and they move the compared VALUES instead: the constant the requestless
fitting path records, an empty served sequence, and the opposite branch of each
verdict. So the battery attests the spec's dependence on each input AT AN ARBITRARY
input rather than at one point of it, which is the stronger statement.

ONE VALUE-LEG RIVAL REMAINS ON fitComputeOffset, AND THE OTHER FOUR WERE RETIRED
BY CARRIER LESSONS RATHER THAN DROPPED — they can no longer be WRITTEN, so they are
not shippable cases, and their content is carried by the argument and result TYPES
instead. That precedent is the foreign prepared matrix recorded above, and a
retirement is strictly stronger than a witnessed rejection: a rejected rival is one
the spec refutes on a real build, while these cannot be spelled at all. Each
measured against the frozen file as it now stands:

  * ``fit-forge-offset-value`` (SHIPPED) reports ``defaultOffset`` — the constant a
    fit that requests no contamination level records — instead of the order
    statistic the requested level determines. It is the only offset a text can
    write down besides the required one, so it is simultaneously the rival that
    pins the offset's dependence on the SCORES, on the FUNCTION taken of them and
    on the REQUESTED POINT: a text that disregards any of the three has nothing
    else to fall back on.
  * ``fit-uses-foreign-scores`` (retired by the FIFTH lesson) took the order
    statistic of a foreign sequence (``let scores := ([] : List Rat)``) and now
    gives ``Application type mismatch: The argument scores has type List Rat but is
    expected to have type Scores in the application percentileAt scores`` —
    ``anomalyScores samples`` is the only ``Scores`` term this tail can name.
  * ``fit-ignores-requested-point`` (retired by the FIFTH lesson) took the order
    statistic at a written point (``percentileAt scores 0``) and now gives
    ``failed to synthesize OfNat Point 0`` — ``q`` is the only ``Point`` term in
    scope.
  * ``fit-aggregates-scores`` (retired by the SEVENTH lesson) read the method's own
    produced sequence through ``scoreValues`` and reported HOW MANY scores it holds
    (``let off := (scores.length : Rat)``). With the reported offset a carrier that
    no longer elaborates: ``Application type mismatch: The argument off has type
    Rat but is expected to have type Offset in the application pure off``. The same
    message retires a written rational offset in that position.
  * ``fit-negates-offset`` (retired by the SEVENTH lesson) kept the right sequence
    and the right point and inverted the ORIENTATION of the result
    (``let off := -(percentileAt scores q)``); it now gives ``failed to synthesize
    Neg Offset``. The threshold sign error it stood for is inexpressible, which is
    the same reason the quotient family is: an offset carrier has no arithmetic on
    it at all (``failed to synthesize HDiv Offset ℕ``, ``failed to synthesize HSub
    Offset Offset``).

THE UNCONDITIONAL RE-SCREEN IS REJECTED BUT NOT WITNESSABLE, and that is a
protocol limit rather than a spec hole. The shape — the pre-patch's, literally —
presents the already-prepared matrix back to the screen:

    let rescreened ← screenHandle (presentPrepared samples)
    let scores := anomalyScores samples
    let off := percentileAt scores q
    return off

It is REJECTED (measured, real build against the spec as it now stands, exit 1) on
the CALL-SITE obligation ``⊢ screenAdvises (presentPrepared samples) = false``,
underivable from the offset tail's context (``scorableAsGiven samples = true``,
``hasSamples samples = true``, and every screen property
opaque); presenting some
other matrix does not help, since there is no other matrix term to present and the
goal would be equally underivable at it. But a
reject case must additionally carry a ``witness`` that refutes the rival while
FAILING on the frozen solution, and the only witness route on this carrier refutes
the method's POSTCONDITION triple. This rival's postcondition is SATISFIED — the
offset value is identical, screening being value-neutral on the numbers
(mapping.md §3.1), which is the whole reason the defect was silent — so no
postcondition witness can separate it from gold (measured: witness-unproven), and
shipping one would ship a broken case. The value-neutrality is measured, not
assumed: the same numbers screened again score bit-identically
(``check_handle_properties`` leg (b), ``check_value_equality``). The shape is
instead pinned where it is
actually decided: it is ``Solution_prepatch.lean``'s impl verbatim, and G-DIFF
requires it to FAIL on exactly that goal.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-25931"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each verified unique inside Solution.lean at load, and
# ---- each lying ENTIRELY inside the impl region / proof body it means to edit).
_SCREEN_IMPL = (
    "    -- Consult the verdict: report the matrix turned away, or report it accepted.\n"
    "    if screenRefuses presented then\n"
    "      return false\n"
    "    else\n"
    "      return true"
)
_PUB_IMPL = (
    "    -- Fresh handle: screen it first, and serve the scores of what that screen\n"
    "    -- prepared only where it accepted the handle.\n"
    "    let accepted ← screenHandle (presentCaller handle)\n"
    "    if accepted then\n"
    "      return some (scoreValues (anomalyScores (preparedOf handle)))\n"
    "    else\n"
    "      return none"
)
_FIT_IMPL = (
    "    -- The data is already prepared: take its screen-free scores and read off the\n"
    "    -- requested order statistic. Nothing here screens the matrix again.\n"
    "    let scores := anomalyScores samples\n"
    "    let off := percentileAt scores q\n"
    "    return off"
)
_SCREEN_PROOF = "prove_correct screenHandle by\n  loom_solve"
_PUB_PROOF = "prove_correct scorePublic by\n  loom_solve"
_FIT_PROOF = "prove_correct fitComputeOffset by\n  loom_solve"

for _a in (_SCREEN_IMPL, _PUB_IMPL, _FIT_IMPL,
           _SCREEN_PROOF, _PUB_PROOF, _FIT_PROOF):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a[:40]!r}"


# ---- witness builder. Reaches the FROZEN method obligation directly through the
# ---- partial-correctness Hoare triple (the opaque carrier kills the tester
# ---- path — see the module docstring). `head` declares the example's
# ---- conditioning binders; `reduce` is the simp set that peels the triple
# ---- (`wp_pure`, plus a branch hypothesis where the RIVAL's own control flow has
# ---- to be resolved before its result is in view); `refute` is the tactic body
# ---- after that. Checked in a file whose `prove_correct` blocks are stripped, so
# ---- no tactic script can interfere.
#
# EVERY MATRIX BINDER IS UNIVERSALLY QUANTIFIED, and that is forced by the carrier
# rather than chosen. The three matrix carriers are opaque TYPES with no
# constructor (see the docstring: they have to be, because every property a screen
# decides is a property of the matrix as an OBJECT and not of the numbers it
# holds), so there is no concrete matrix term to probe at. A witness therefore
# takes an arbitrary matrix and conditions on the sub-domain where the rival is
# wrong — a strictly stronger statement than one at a point. The binders that ARE
# concrete are still moved: `q` across `0` and `1`, and the score sequences the
# value legs compare.
#
# WHY `simp only [...]` AND NOT `unfold`, AND WHY IT IS LOAD-BEARING. The gate's
# second build reads "the witness FAILED against the frozen solution" as "the
# frozen solution satisfies the spec here", and that inference only holds if the
# gold-side build actually EVALUATED the claim. `unfold f g` is an error when `g`
# does not occur in the goal — and the methods gold and a rival call are exactly
# what a control-flow rival changes, so a witness that names the RIVAL's callee
# in an `unfold` breaks the gold build on a missing occurrence rather than on a
# refutation. Measured on this bundle (audit, real builds): a then-shipped
# `unfold fitComputeOffset scorePublic` witness failed on gold with
#   error: Tactic `unfold` failed to unfold `scorePublic` in ¬{True}...
# — gold does not call it — and a FORGERY asserting a value violated by gold AND
# by the rival, referencing no spec clause, cleared both halves under that same
# shape: rival exit 0, gold exit 1, recorded as a refutation. So the exit code
# carried no information, exactly the defect class pbt_witness screens on the
# rival side.
#
# `simp only` tolerates a rewrite rule with no occurrence (it warns), so the SAME
# witness text reduces on BOTH sides and both builds ask the same question. Under
# the repaired shape gold's failure is a semantic one with the reduced `wp` term
# in view — either `unsolved goals ... ⊢ False` (verdict legs) or a type mismatch
# exhibiting the REFLEXIVE equation that simp derived because gold satisfies the
# clause (value legs) — and a forgery ELABORATES against gold (exit 0) => the gate
# records `witness-vacuous` and rejects it. The unfold list is the union of every
# method on the call path of gold AND of the rival, so it is side-independent by
# construction: gold's `scorePublic` DELEGATES to `screenHandle`, so both names are
# in the list for every witness on that method, and a rival that drops the
# delegation reduces under the same text.
def _triple_witness(head, call, clause, unfold, refute, reduce="wp_pure"):
    rules = ", ".join(unfold.split())
    return (
        f"example {head}:\n"
        f"    ¬ (triple (l := Prop) True\n"
        f"    ({call})\n"
        f"    (fun out => {clause})) := by\n"
        f"  simp only [triple, {rules}]\n"
        f"  intro hh\n"
        f"  have hc := hh trivial\n"
        f"  simp [{reduce}] at hc\n"
        f"{refute}"
    )


# The verdict-leg refutation body: fixing the opaque verdict at the probed matrix
# selects the branch the frozen clause demands, and the rival's result contradicts
# it outright — `simp` closes the goal.
_VERDICT_REFUTE_R = "  simp [hs] at hc\n"

# The value-leg refutation body: `simp` reduces the goal to the equality the rival
# produces; discharge it against the conditioning hypothesis `h`.
_VALUE_REFUTE = "  exact h hc.symm\n"

# The served-value refutation body on `scorePublic`: fix the verdict so the served
# branch is the one in view, strip the `some`, then contradict. The extra
# `wp_pure` in the reduce set is measured: where a rival's result differs from the
# frozen one INSIDE the option (both sides `some`), the contradiction is one level
# down, so the `wp` of the returned `pure` has to be reduced before the two
# sequences can be compared; without it the rival build leaves an unreduced `wp`
# standing and the goal `⊢ False` unsolved.
_PUB_VALUE_REFUTE = (
    "  simp [hs, wp_pure] at hc\n"
    "  exact h hc\n"
)

_SCREEN_CLAUSE = "out = if screenRefuses {x} then false else true"
_PUB_CLAUSE = (
    "out = if screenRefuses (presentCaller hd) then none "
    "else some (scoreValues (anomalyScores (preparedOf hd)))"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — Structurally different but CORRECT impls
    # that MUST verify; else the spec is SPEC-TOO-STRONG on the impl's shape.
    # Each keeps its `prove_correct` obligation byte-identical and reshapes only
    # the executable surface; the frozen `loom_solve` still closes (verified
    # during authoring, exit 0). None adds a helper lemma, axiom, or assumption.
    # =====================================================================
    {
        "id": "pos-screen-single-expression",
        "kind": "soundness",
        "expect": "verify",
        # screenHandle: fold the two-branch statement form into ONE expression in
        # which the verdict selects what is reported. Same function of the
        # verdict, so the clause still holds on the whole domain.
        "module": _swap(
            _BASE, _SCREEN_IMPL,
            "    -- One expression: the verdict selects what is reported.\n"
            "    return (if screenRefuses presented then false else true)"),
        "rationale": "DEFENDS screenHandle. Folding the two-branch form into a "
                     "single conditional expression leaves the reported verdict the "
                     "SAME function of the screen's own — not accepted for a matrix "
                     "the screen refuses, accepted otherwise — so a correct reshape "
                     "must verify, else SPEC-TOO-STRONG on the branching shape. Note "
                     "what this does NOT bless: the verdict is still consulted before "
                     "anything is reported. Frozen `loom_solve` retained.",
    },
    {
        "id": "pos-public-inline-verdict",
        "kind": "soundness",
        "expect": "verify",
        # scorePublic: consult the verdict directly instead of delegating to the
        # screen method. Same served result on the whole domain.
        "module": _swap(
            _BASE, _PUB_IMPL,
            "    -- Consult the verdict here rather than through the screen method;\n"
            "    -- the served result is the same function of it.\n"
            "    if screenRefuses (presentCaller handle) then\n"
            "      return none\n"
            "    else\n"
            "      return some (scoreValues (anomalyScores (preparedOf handle)))"),
        "rationale": "DEFENDS scorePublic. An entry point that consults the "
                     "screen's verdict itself, instead of delegating to the "
                     "screening method and branching on the verdict it reports, serves the "
                     "SAME function of that verdict — nothing for a refused handle, "
                     "the per-sample scores of what the screen prepares from that "
                     "handle otherwise. A correct reshape must verify, else "
                     "SPEC-TOO-STRONG on which of the two spellings of the screen an "
                     "impl uses. Frozen `loom_solve` retained.",
    },
    {
        "id": "pos-fit-inline-percentile",
        "kind": "soundness",
        "expect": "verify",
        # fitComputeOffset: inline the order-statistic step into the return
        # (drop the `let off :=` binding). Same data flow: derive from the
        # prepared matrix (no re-screen), then return the order statistic.
        "module": _swap(
            _BASE, _FIT_IMPL,
            "    -- The data is already prepared: take its screen-free scores, then return\n"
            "    -- the requested order statistic of them directly.\n"
            "    let scores := anomalyScores samples\n"
            "    return percentileAt scores q"),
        "rationale": "DEFENDS fitComputeOffset. Inlining the order-statistic step "
                     "into the `return` (dropping the intermediate `let off`) "
                     "keeps the same data flow — derive from the matrix the earlier "
                     "screen prepared, then return `percentileAt scores q` — so the "
                     "obligation still holds; a correct reshape must verify, else "
                     "SPEC-TOO-STRONG. Frozen `loom_solve` retained.",
    },
    {
        "id": "pos-fit-provably-silent-rescreen",
        "kind": "soundness",
        "expect": "verify",
        # THE HONEST LICENSE, SHIPPED AS A CONTROL RATHER THAN LEFT IMPLICIT. The
        # offset tail may present its prepared matrix to the screen again in the
        # branch where it can PROVE the screen has nothing to advise about it. That
        # re-screen draws no report and computes no score — its image re-runs the
        # input preparation, which does not move the numbers; the screening method
        # invokes no scorer, and the
        # scorer-invoking method is unreachable from here (no handle term exists).
        # This case pins that the spec rejects the UNCONDITIONAL re-screen without
        # also rejecting a redundant-but-silent preparation step, which would be
        # SPEC-TOO-STRONG. Measured in the official image: the faithful counterpart
        # resolves (F2P passes; all 21 P2P pass, chunk-count assertions included).
        "module": _swap(
            _BASE, _FIT_IMPL,
            "    -- Screen the data again only where it is provable that no report can\n"
            "    -- be drawn about it; the screen computes no score either way.\n"
            "    if screenAdvises (presentPrepared samples) then\n"
            "      return percentileAt (anomalyScores samples) q\n"
            "    else\n"
            "      let _accepted ← screenHandle (presentPrepared samples)\n"
            "      return percentileAt (anomalyScores samples) q"),
        "rationale": "DEFENDS fitComputeOffset against being SPEC-TOO-STRONG on "
                     "the screening restriction. The rival does present its data to "
                     "the screen a second time — but only inside the branch where "
                     "the screen's advisory provably does not arise, which is the "
                     "call-site obligation the frozen screen carries. Its faithful "
                     "counterpart re-runs input preparation exactly where no report "
                     "can be drawn, so it reports nothing, leaves the numbers "
                     "untouched, and puts no scorer to work a second time (the "
                     "screening method computes no score, and the scorer-invoking "
                     "method takes a caller handle, which this tail cannot form). "
                     "It must verify: a spec that rejected it would forbid a "
                     "redundant preparation step that no consumer can observe, "
                     "rather than the unconditional re-screen the issue is about — "
                     "and that one is still rejected (Solution_prepatch.lean, exit "
                     "1 on `⊢ screenAdvises (presentPrepared samples) = false`). "
                     "Frozen `loom_solve` retained.",
    },

    # =====================================================================
    # ADMISSIBILITY — the methods carry `require` clauses (the call-site wall
    # described in the module docstring), so the nagini precondition-admission probe
    # applies in its own right. It is NOT dischargeable from inside Lean, and that is
    # by construction rather than an omission: the screen properties are OPAQUE
    # axioms over OPAQUE matrix types, so no matrix satisfies them derivably — which
    # is exactly what makes the wall unfabricable by a rival. Joint satisfiability
    # holds in the MODEL (all references are unconstrained, so an interpretation with
    # any combination of truth values at a given matrix exists; this is the gate's
    # axiom-consistency probe), and non-vacuity is attested EMPIRICALLY by the
    # surface below instead: if a precondition were contradictory, the obligation
    # would be vacuous and every `expect:"reject"` rival here would verify. They do
    # not — all seven reject.
    #
    # The analogue on a TOTAL carrier is additionally the one the task lane names:
    # the obligation being UNSATISFIABLE at exactly an F2P-shaped input. That is what
    # the three cases below test directly — each discharges the frozen post-image at
    # an ARBITRARY matrix of the relevant carrier (the strongest form available, the
    # types having no concrete term) as a `have`, BY EVALUATION, before closing the
    # frozen obligation verbatim. Two of the three are conditional clauses, and a
    # conditional clause is exactly the shape that can be quietly unsatisfiable in
    # one branch, so both branches are discharged.
    # =====================================================================
    {
        "id": "admiss-screen-posimage-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _SCREEN_PROOF,
            "prove_correct screenHandle by\n"
            "  have admiss_posimage : ∀ (pr : Presented),\n"
            "      triple (l := Prop) True\n"
            "      (screenHandle pr)\n"
            "      (fun out =>\n"
            "        out = if screenRefuses pr then false else true) := by\n"
            "    intro pr\n"
            "    simp only [triple, screenHandle]\n"
            "    intro _\n"
            "    split <;> simp [wp_pure]\n"
            "  loom_solve"),
        "rationale": "ADMISSIBILITY on a total carrier: screenHandle's CONDITIONAL "
                     "post-image is SATISFIABLE at an ARBITRARY presented matrix in "
                     "BOTH branches of the opaque verdict — reported not accepted "
                     "where the screen refuses, reported accepted otherwise. "
                     "The `have` claims the frozen clause verbatim, universally "
                     "quantified over the matrix (the carrier has no concrete term by "
                     "construction — see the docstring), and discharges it by "
                     "EVALUATION after splitting the verdict (`split <;> simp "
                     "[wp_pure]`), assuming nothing. If either branch were "
                     "unsatisfiable the modeled screen would be degenerate — the "
                     "total-carrier analogue of PRECOND-TOO-STRONG. The impl region "
                     "is byte-identical to the frozen one and the frozen obligation "
                     "is closed verbatim by the untouched `loom_solve`, so the case "
                     "adds an obligation and weakens none.",
    },
    {
        "id": "admiss-public-posimage-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        # The `have` states scorePublic's CONDITIONAL post-image at an ARBITRARY
        # handle and discharges it in BOTH branches of the opaque verdict, by
        # evaluation, assuming nothing.
        "module": _swap(
            _BASE, _PUB_PROOF,
            "prove_correct scorePublic by\n"
            "  have admiss_posimage : ∀ (hd : CallerHandle),\n"
            "      triple (l := Prop) True\n"
            "      (scorePublic hd)\n"
            "      (fun out =>\n"
            "        out = if screenRefuses (presentCaller hd) then none\n"
            "              else some (scoreValues\n"
            "                           (anomalyScores (preparedOf hd)))) := by\n"
            "    intro hd\n"
            "    simp only [triple, scorePublic, screenHandle]\n"
            "    intro _\n"
            "    split <;> simp [wp_pure]\n"
            "  loom_solve"),
        "rationale": "ADMISSIBILITY on a total carrier, for the clause the graded "
                     "scoring surface lives on: scorePublic's post-image is "
                     "SATISFIABLE at an ARBITRARY caller handle in BOTH branches of "
                     "the screen's verdict — nothing served where the screen "
                     "refuses, the per-sample scores of what the screen prepares "
                     "otherwise. The `have` claims the frozen clause verbatim, "
                     "universally quantified over the handle, and discharges it by "
                     "EVALUATION after splitting the verdict, assuming nothing. If "
                     "either branch were unsatisfiable the modeled entry point would "
                     "be degenerate exactly where the graded scoring surface is. The "
                     "impl region is byte-identical to the frozen one and the frozen "
                     "obligation is closed verbatim by the untouched `loom_solve`.",
    },
    {
        "id": "admiss-fit-posimage-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        # The `have` states the obligation's post-image at an ARBITRARY prepared
        # matrix and an ARBITRARY requested point (neither carrier has a concrete
        # term — fifth lesson), and closes it by `simp [wp_pure]`, i.e. by
        # evaluating the method rather than by assuming anything. If the post-image
        # were unsatisfiable there (the total-carrier analogue of
        # PRECOND-TOO-STRONG) this `have` would not close.
        "module": _swap(
            _BASE, _FIT_PROOF,
            "prove_correct fitComputeOffset by\n"
            "  have admiss_posimage : ∀ (pd : Prepared) (pt : Point),\n"
            "      triple (l := Prop) True\n"
            "      (fitComputeOffset pd pt)\n"
            "      (fun out =>\n"
            "        out = percentileAt (anomalyScores pd) pt) := by\n"
            "    intro pd pt\n"
            "    simp only [triple, fitComputeOffset]\n"
            "    intro _\n"
            "    simp [wp_pure]\n"
            "  loom_solve"),
        "rationale": "ADMISSIBILITY on a total carrier: fitComputeOffset's "
                     "post-image is SATISFIABLE at an ARBITRARY prepared matrix at an "
                     "ARBITRARY requested point. The `have` claims exactly "
                     "the frozen obligation's clause there — the offset is the order "
                     "statistic of that matrix's scores — and discharges it BY "
                     "EVALUATION (`simp [wp_pure]` on the reduced method), assuming "
                     "nothing. Both binders are universal because neither carrier "
                     "has a concrete term (fifth lesson), so this is the strongest "
                     "form the carrier admits. If the clause were unsatisfiable at an "
                     "input of the "
                     "failing fit's shape, the modeled behaviour would be degenerate "
                     "at precisely the point the issue is about and no impl could "
                     "satisfy it there — the total-carrier analogue of "
                     "PRECOND-TOO-STRONG. The impl region is byte-identical to the "
                     "frozen one and the frozen obligation is closed verbatim by the "
                     "untouched `loom_solve`, so the case adds an obligation and "
                     "weakens none. No new declaration, no axiom, no assumption.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected. Each keeps the frozen proof (which its reshape leaves with
    # an unsolved goal — but the rejection is ATTRIBUTED to the spec by the
    # machine-checked Hoare-triple witness, not by the stale proof failing), and
    # carries (a) the refinement argument that its faithful real counterpart would
    # NOT resolve the F2P and (b) a witness conditioned on the sub-domain where it
    # is wrong.
    #
    # The unconditional re-screen (the pre-patch shape) is NOT here: it is rejected
    # at the CALL SITE, where no postcondition witness can reach it. See the last
    # block of the module docstring, and G-DIFF on Solution_prepatch.lean.
    # =====================================================================
    {
        "id": "screen-ignores-refusal",
        "kind": "uniqueness",
        "expect": "reject",
        # Report every matrix accepted whatever the verdict: the impl never
        # consults `screenRefuses`, so a matrix the screen refuses is reported
        # usable and passed along.
        "module": _swap(_BASE, _SCREEN_IMPL, "    return true"),
        "refinement": "a screen that reports every matrix accepted without consulting "
                      "the verdict lets unusable data through: a matrix whose width "
                      "disagrees with the width recorded at fit time, one holding "
                      "no samples, one holding a magnitude the working precision "
                      "cannot represent, or one presenting a labelling that "
                      "disagrees with the recorded one all proceed to be scored "
                      "instead of being turned away. The graded surface asserts the "
                      "opposite for exactly those inputs (a caller scoring a matrix "
                      "of the wrong width must be told so), and the numbers a "
                      "scorer would produce from such data are not meaningful — it "
                      "would NOT resolve.",
        "rationale": "REJECT from screenHandle's clause `accepted = if "
                     "screenRefuses presented then false else true`: the rival "
                     "reports acceptance on the whole domain, which differs from the "
                     "required value on every matrix the screen refuses. If it "
                     "verified => SPEC-TOO-WEAK, and in precisely the way an earlier "
                     "revision of this battery blessed as a positive control "
                     "(statement order declared unobservable, so a caller could be "
                     "answered without the verdict). The verdict "
                     "leg is opaque, so the witness takes an arbitrary presented "
                     "matrix and CONDITIONS on the sub-domain where the rival is "
                     "wrong (`screenRefuses pr = true`).",
        "witness": _triple_witness(
            "(pr : Presented) (hs : screenRefuses pr = true) ",
            "screenHandle pr", _SCREEN_CLAUSE.format(x="pr"),
            "screenHandle", _VERDICT_REFUTE_R),
    },
    {
        "id": "screen-refuses-everything",
        "kind": "uniqueness",
        "expect": "reject",
        # The opposite polarity: refuse everything. Right on the refused branch,
        # wrong on every matrix the screen accepts.
        "module": _swap(_BASE, _SCREEN_IMPL, "    return false"),
        "refinement": "a screen that reports every matrix turned away stops all "
                      "scoring: the "
                      "public entry point serves nothing, the fitting tail has no "
                      "prepared data to derive a threshold from, and every scoring, "
                      "prediction and threshold consumer fails outright — it would "
                      "NOT resolve.",
        "rationale": "REJECT from screenHandle's clause: the rival reports `false` "
                     "on the whole domain, which differs from the required value on "
                     "every matrix the screen ACCEPTS. This is the opposite polarity "
                     "from `screen-ignores-refusal`, so between them both branches "
                     "of the conditional clause are pinned; a spec leaving either "
                     "branch unpinned would be SPEC-TOO-WEAK. The verdict leg is "
                     "opaque, so the witness takes an arbitrary presented matrix and "
                     "CONDITIONS on the sub-domain where the rival is wrong "
                     "(`screenRefuses pw = false`, the opposite verdict from the "
                     "previous case, at a differently-named binder).",
        "witness": _triple_witness(
            "(pw : Presented) (hs : screenRefuses pw = false) ",
            "screenHandle pw", _SCREEN_CLAUSE.format(x="pw"),
            "screenHandle", _VERDICT_REFUTE_R),
    },
    {
        "id": "public-ignores-refusal",
        "kind": "uniqueness",
        "expect": "reject",
        # THE INVERSION OF THE WITHDRAWN POSITIVE. Serve the scores regardless of
        # the screen's verdict: the impl neither screens nor consults
        # `screenRefuses`, so numbers derived from a handle the screen refuses are
        # handed to the caller as if they were meaningful.
        "module": _swap(
            _BASE, _PUB_IMPL,
            "    return some (scoreValues (anomalyScores (preparedOf handle)))"),
        "refinement": "a counterpart that hands back scores for every handle, "
                      "without consulting the screen, serves numbers derived from "
                      "a handle the screen refuses — one whose width disagrees "
                      "with the width recorded at fit time, one holding no "
                      "samples, one holding a magnitude the working precision "
                      "cannot represent, or one presenting a labelling that "
                      "disagrees with the recorded one. The graded scoring surface "
                      "asserts the opposite for exactly those handles: a caller "
                      "that scores a matrix of the wrong width must be told the "
                      "handle is unusable, not served a score for it. It would NOT "
                      "resolve.",
        "rationale": "REJECT from scorePublic's clause `result = if screenRefuses "
                     "(presentCaller handle) then none else some (scoreValues "
                     "(anomalyScores (preparedOf handle)))`: the rival serves "
                     "scores on the whole domain, which differs from the required "
                     "value on every handle the screen refuses. If it verified => "
                     "SPEC-TOO-WEAK, and in precisely the way an earlier revision of "
                     "this battery blessed as a positive control (statement order "
                     "declared unobservable, so a value could be served without the "
                     "verdict). The verdict leg is opaque and the handle type has no "
                     "concrete term, so the witness quantifies over an arbitrary "
                     "handle and CONDITIONS on the sub-domain where the rival is "
                     "wrong (`screenRefuses (presentCaller hd) = true`).",
        "witness": _triple_witness(
            "(hd : CallerHandle) (hs : screenRefuses (presentCaller hd) = true) ",
            "scorePublic hd", _PUB_CLAUSE,
            "scorePublic screenHandle", _VERDICT_REFUTE_R),
    },
    {
        "id": "public-refuses-everything",
        "kind": "uniqueness",
        "expect": "reject",
        # The opposite polarity: serve NOTHING, whatever the verdict. Passes the
        # refused branch, wrong on every handle the screen accepts.
        "module": _swap(_BASE, _PUB_IMPL, "    return none"),
        "refinement": "a counterpart whose public scoring entry point reports "
                      "every handle unusable never scores anything: every scoring, "
                      "prediction and threshold consumer of the public path gets "
                      "nothing back, so the graded scoring surface fails outright "
                      "— it would NOT resolve.",
        "rationale": "REJECT from scorePublic's clause: the rival returns `none` "
                     "on the whole domain, which differs from the required value "
                     "on every handle the screen ACCEPTS. This is the opposite "
                     "polarity from `public-ignores-refusal`, so between them both "
                     "branches of the conditional clause are pinned; a spec that "
                     "left either branch unpinned would be SPEC-TOO-WEAK. The "
                     "witness quantifies over an arbitrary handle and CONDITIONS on "
                     "the sub-domain where the rival is wrong (`screenRefuses "
                     "(presentCaller hf) = false`), the opposite verdict from the "
                     "previous case.",
        "witness": _triple_witness(
            "(hf : CallerHandle) (hs : screenRefuses (presentCaller hf) = false) ",
            "scorePublic hf",
            "out = if screenRefuses (presentCaller hf) then none "
            "else some (scoreValues (anomalyScores (preparedOf hf)))",
            "scorePublic screenHandle", _VERDICT_REFUTE_R),
    },
    {
        "id": "public-keys-on-advisory",
        "kind": "uniqueness",
        "expect": "reject",
        # CONTROL FLOW ON THE WRONG PREDICATE. The impl does consult the screen —
        # but the ADVISORY rather than the REFUSAL: it withholds scores where the
        # screen merely reports a labelling discrepancy, and serves them where the
        # screen refuses the handle outright. It is the rival that would survive a
        # spec conflating the two observables into one property.
        "module": _swap(
            _BASE, _PUB_IMPL,
            "    if screenAdvises (presentCaller handle) then\n"
            "      return none\n"
            "    else\n"
            "      return some (scoreValues (anomalyScores (preparedOf handle)))"),
        "refinement": "a counterpart that withholds scores whenever the screen has "
                      "something to ADVISE about the handle's labelling, and serves "
                      "them whenever the screen REFUSES the handle, has the two "
                      "observables exactly backwards: a caller whose matrix is "
                      "merely unlabelled would be refused service it is entitled "
                      "to (the advisory is a report, not a refusal — measured, "
                      "axiom_check.py leg (iv)), while a caller whose matrix has "
                      "the wrong width would be served a score instead of being "
                      "told the handle is unusable. Both directions regress graded "
                      "behaviour — it would NOT resolve.",
        "rationale": "REJECT from scorePublic's clause: inside the modeled domain "
                     "(`screenAdvises (presentCaller handle) = false`) the rival "
                     "takes its else branch and serves the scores "
                     "unconditionally, so it is wrong on every handle the screen "
                     "refuses. If it verified => SPEC-TOO-WEAK, in the specific "
                     "way that matters here: the spec would not distinguish the "
                     "ADVISORY from the REFUSAL, and the two are separate "
                     "repository observables (a report versus a raise). Two "
                     "conditioning hypotheses, about DIFFERENT terms: `screenAdvises "
                     "(presentCaller ha_hd) = false` is this method's own "
                     "precondition instantiated, so the attack lands INSIDE the "
                     "modeled domain, and `screenRefuses (presentCaller ha_hd) = "
                     "true` is the sub-domain where the rival is wrong.",
        "witness": _triple_witness(
            "(ha_hd : CallerHandle) "
            "(ha : screenAdvises (presentCaller ha_hd) = false) "
            "(hs : screenRefuses (presentCaller ha_hd) = true) ",
            "scorePublic ha_hd",
            "out = if screenRefuses (presentCaller ha_hd) then none "
            "else some (scoreValues (anomalyScores (preparedOf ha_hd)))",
            "scorePublic screenHandle", _VERDICT_REFUTE_R,
            reduce="wp_pure, ha"),
    },
    {
        "id": "public-serves-empty-scores",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE LEG on the public path: screen correctly, then serve an EMPTY score
        # sequence instead of the scores of what the screen prepared. Right on the
        # refused branch; wrong on the served branch wherever the real scores are
        # not empty.
        "module": _swap(
            _BASE, _PUB_IMPL,
            "    let accepted ← screenHandle (presentCaller handle)\n"
            "    if accepted then\n"
            "      return some []\n"
            "    else\n"
            "      return none"),
        "refinement": "a public scoring entry point that screens correctly but "
                      "hands back an empty score sequence returns one score per "
                      "sample for no sample at all: every consumer of the public "
                      "path — scoring, prediction, threshold comparison — gets "
                      "nothing to work with where it expects one value per row, so "
                      "the graded scoring surface fails outright. It would NOT "
                      "resolve.",
        "rationale": "REJECT from scorePublic's clause on its SERVED branch: the "
                     "rival serves `some []`, which differs from `some (scoreValues "
                     "(anomalyScores (preparedOf handle)))` "
                     "wherever the real score sequence is non-empty, while the "
                     "refused branch still holds. If it verified => SPEC-TOO-WEAK "
                     "(the public path's scoring VALUE unpinned, with only its "
                     "verdict pinned). Two conditioning hypotheses about different "
                     "terms: `screenRefuses (presentCaller hv) = false` puts the "
                     "served branch in view, and `scoreValues (anomalyScores "
                     "(preparedOf hv)) ≠ []` is the sub-domain where the rival is "
                     "wrong.",
        "witness": _triple_witness(
            "(hv : CallerHandle) (hs : screenRefuses (presentCaller hv) = false) "
            "(h : scoreValues (anomalyScores (preparedOf hv)) ≠ []) ",
            "scorePublic hv",
            "out = if screenRefuses (presentCaller hv) then none "
            "else some (scoreValues (anomalyScores (preparedOf hv)))",
            "scorePublic screenHandle", _PUB_VALUE_REFUTE),
    },
    {
        "id": "fit-forge-offset-value",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE / THE OTHER FITTING PATH'S CONSTANT. Route through the prepared
        # matrix exactly as gold does (so no re-screen is even attempted) but record
        # the offset a fit that requests NO contamination level records, instead of
        # the order statistic the requested level determines. Since the seventh
        # lesson this is THE ONLY offset a text can write down besides the required
        # one, so it is simultaneously the case that pins the offset's dependence on
        # the SCORES, on the FUNCTION taken of them and on the REQUESTED POINT: a
        # rival that disregards any of the three can only fall back on this constant
        # (measured: an aggregate or a rational literal in this position gives
        # `Application type mismatch: The argument off has type Rat but is expected
        # to have type Offset`, and a negation gives `failed to synthesize Neg
        # Offset`). It replaces the retired `fit-aggregates-scores` and
        # `fit-negates-offset`, whose positions are now inexpressible rather than
        # merely wrong.
        "module": _swap(
            _BASE, _FIT_IMPL,
            "    -- The data is already prepared: take its screen-free scores, then report\n"
            "    -- the offset a fit that requests no contamination level records.\n"
            "    let scores := anomalyScores samples\n"
            "    let off := defaultOffset\n"
            "    return off"),
        "refinement": "a counterpart that records the constant the requestless "
                      "fitting path records (-0.5, measured — axiom_check.py "
                      "`check_offset_arithmetic_fences` leg (a)) instead of the order "
                      "statistic of the training matrix's anomaly scores at the point "
                      "the requested contamination level determines ignores the "
                      "caller's configuration and the fitted model together: every "
                      "model gets the same threshold whatever data it was fitted on "
                      "and whatever fraction the caller asked to be treated as "
                      "anomalous, so the requested fraction of the training data no "
                      "longer falls outside the boundary. The recorded offset is "
                      "measurably not that constant on every model measured (same "
                      "leg), and the P2P prediction/decision consumers that depend on "
                      "the requested contamination observe wrong labels — it would "
                      "NOT resolve.",
        "rationale": "REJECT from fitComputeOffset's value clause `offset = "
                     "percentileAt (anomalyScores samples) q`: the rival returns "
                     "`defaultOffset`, the one other term of the offset carrier, "
                     "which differs from the required value wherever the order "
                     "statistic at the requested point is not that constant — which "
                     "is everywhere the repository was measured. The value leg is "
                     "opaque, so the witness takes an arbitrary prepared matrix and "
                     "CONDITIONS on that sub-domain (`percentileAt (anomalyScores pf) "
                     "p ≠ defaultOffset`) — exactly where the rival is wrong. If it "
                     "verified => SPEC-TOO-WEAK (the offset's derivation from the "
                     "SCORES, the function taken of them, and its dependence on the "
                     "requested point all unpinned at once, since after the seventh "
                     "lesson no other rival on this clause can be written). Probed at "
                     "an ARBITRARY requested point rather than at one: the point "
                     "carrier has no concrete term (fifth lesson), so the witness "
                     "quantifies over it, which is the stronger claim.",
        "witness": _triple_witness(
            "(pf : Prepared) (p : Point) "
            "(h : percentileAt (anomalyScores pf) p ≠ defaultOffset) ",
            "fitComputeOffset pf p",
            "out = percentileAt (anomalyScores pf) p",
            "fitComputeOffset", _VALUE_REFUTE),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 10 SPEC cases (8
# uniqueness rivals + 1 soundness positive + 1 admissibility) all attached to a
# SINGLE nagini function `fit_offset` whose contract bundles: a side-effect
# advisory tally (`fit_advisories`), two unforgeable provenance @Predicate tokens
# (`offset_from_unvalidated_scoring`, `prepared_input`/`raw_fit_input`), a
# read-only fractional-permission input (`Acc(X_raw.has_labels, 1/2)`), and a
# biconditional linking `offset_set` to `calibration_requested`.
#
# This velvet bundle NARROWS to the purely functional core the change actually
# turns on — WHICH path the offset derivation uses, and hence whether the
# already-prepared data is screened a SECOND time — modeled across three methods
# (the screen, the public scoring entry point, the fit tail). The nagini
# side-effect tally, the token clauses and the biconditional collapse onto two
# observables of the screen: its ADVISORY, which is ambient and has no returned
# value, so it is carried as the screening method's argument restriction (an impl
# cannot drop a call-site obligation), and its REFUSAL, which the caller does
# observe, so it is carried as the reported result. A screening COUNTER was
# tried for this and measured defeatable in both directions; see the module
# docstring.
#
#   nagini case                          -> here                              disp
#   ---------------------------------------------------------------------------
#   3. validating-path-prepatch-bug      -> Solution_prepatch.lean (G-DIFF)   MOVED
#      (route via validating scorer;        (present the prepared matrix back to the
#       fit_advisories == 1)                 screen; rejected at the CALL SITE,
#                                            `⊢ screenAdvises (presentPrepared
#                                            samples) = false`. Not
#                                            shippable as a manifest case: with the
#                                            offset value unchanged by screening, the
#                                            rival's postcondition is SATISFIED, so no
#                                            postcondition witness can refute it —
#                                            see the docstring. Not dropped: it is
#                                            the prepatch's impl verbatim.)
#   2. control-flow-unconditional-scorer -> public-ignores-refusal            RE-AIMED
#      (scorer invoked unconditionally)      (scores served without consulting the
#                                            screen's verdict — the shape an earlier
#                                            revision blessed as a positive control)
#   4. skip-scorer-no-offset             -> public-refuses-everything         RE-AIMED
#      (no offset produced)                  (nothing served, whatever the verdict)
#   5. forge-offset-token                -> fit-forge-offset-value            RE-AIMED
#      (offset_set true w/o scoring token)   (offset from the WRONG quantity;
#                                             opaque value leg, conditioned)
#   6. raw-matrix-out-of-domain          -> fit-forge-offset-value            SUBSUMED
#   7. fabricated-matrix-wrong-data      -> the SCORE-SEQUENCE argument TYPE  STRUCTURAL
#      (score a fabricated matrix, not       (it was ported as fit-uses-foreign-scores
#       fit's own prepared input)             and retired by the FIFTH lesson: the
#                                            score sequence is a carrier type whose
#                                            only term in this tail is `anomalyScores
#                                            samples`, so a foreign sequence no longer
#                                            elaborates — measured, `Application type
#                                            mismatch ... expected to have type
#                                            Scores`. The provenance content is
#                                            carried by the argument type, and since
#                                            the SEVENTH lesson the FUNCTION taken of
#                                            the method's own sequence is carried by
#                                            the RESULT type the same way — an
#                                            aggregate of the scores no longer
#                                            elaborates either.)
#   8. skip-record-fit-labels            -> (fitted_with_labels not modeled)  OMITTED
#   1. frame-mutation-write-readonly     -> (referentially transparent)       OMITTED
#   9. pos-control-record-labels-last    -> pos-fit-inline-percentile         PORTED
#  10. admissibility-public-scorer       -> admiss-public-posimage-nondegenerate  PORTED
#
# ADDED (11) — coverage of the surface this bundle DOES model that the nagini
# single-function framing did not expose as separate cases:
#   * pos-screen-single-expression, pos-public-inline-verdict — defend the screen
#     and the public entry point's obligations (nagini modeled the scorers as
#     callees with contracts, not as separately-contracted functions).
#   * pos-fit-provably-silent-rescreen — defends the boundary of the screening
#     restriction from the other side: the redundant-but-provably-silent re-screen
#     must remain admissible, or the spec would be SPEC-TOO-STRONG on a step no
#     consumer can observe. It has no nagini counterpart because the nagini tally
#     counted screens outright, so it could not express "a screen that draws no
#     report".
#   * public-keys-on-advisory — the rival that consults the screen but keys on the
#     ADVISORY instead of the REFUSAL. No nagini counterpart: the nagini contract
#     had only one screening observable (the advisory tally); this bundle separates
#     the two, and this case is what makes the separation load-bearing.
#   * screen-ignores-refusal, screen-refuses-everything — attack the screen's own
#     clause at both branches of its verdict, which the nagini framing folded into
#     the scorer's contract. (The screen hands back NO matrix to attack: its
#     prepared output is the caller-side value the public entry point's served
#     clause names, and THAT position is attacked by public-serves-empty-scores.
#     See the fourth lesson in the module docstring for the measured reason the
#     output moved to the caller's side.)
#   * public-serves-empty-scores — attacks the served VALUE of the scoring
#     obligation.
#   * fit-aggregates-scores, fit-negates-offset — velvet-only obligations with no
#     nagini counterpart (the nagini contract abstracted the offset VALUE away
#     entirely: it carried provenance tokens, not the order statistic), RETIRED by
#     the SEVENTH lesson. The FUNCTION taken of the score sequence and the
#     ORIENTATION of the result are carried by the offset carrier now — neither
#     shape elaborates — and what remains shippable on that clause is
#     fit-forge-offset-value at the grounded constant. See the seventh lesson in
#     the module docstring for the measured reason, and the retirement list above
#     for the exact messages.
#   * admiss-screen-posimage-nondegenerate, admiss-fit-posimage-nondegenerate —
#     the total-carrier admissibility probes for the other two obligations; the
#     nagini sibling carried one, on the public scorer.
#
# OMITTED (2), with reasons:
#   * frame-mutation-write-readonly — VACUOUS. Velvet is referentially
#     transparent: no heap, no aliasing, no fractional permission. This revision
#     has no `mut` binder at all; `samples`/`q`/`handle` are immutable value
#     parameters. There is no read-only input to overwrite, so no discriminating
#     witness could exist. Not fabricated.
#   * skip-record-fit-labels — the fit-time label-recording observable
#     (`fitted_with_labels == Old(X_raw.has_labels)`) is a separate estimator
#     state field the nagini contract carried but this bundle does NOT model: the
#     velvet carrier models only the offset-derivation tail, the screen and the
#     public scoring entry point (mapping.md §1). No counterpart clause exists to
#     attack, so there is no rival to build here — a genuine carrier-narrowing
#     omission, not a dropped-because-hard case.
#
# The two Implies-clauses and the biconditional of the nagini spec have no
# separate velvet counterpart: the offset-set/calibration linkage is not part of
# this bundle's modeled surface (the fit tail here is entered already on the
# non-default-contamination path — mapping.md §1). Their discriminating content
# (the offset is derived from the prepared matrix, without re-screening it in a
# way the caller can observe) is carried by the call-site wall (G-DIFF, on the
# prepatch's route through the screen) and by fit-forge-offset-value (value), so
# nothing the sibling tested on this behaviour is dropped silently.
#
# WITNESS ROUTE. The tester route (`derive_tester_for` + `decide`) is UNAVAILABLE
# because every clause references an opaque reference (`anomalyScores`,
# `percentileAt`, a screen property, or the handle type): extraction cannot compile
# a program depending on a code-free callee, and `decide` stalls on the opaque term
# (confirmed during authoring). Every witness instead refutes the method's
# partial-correctness Hoare triple directly, conditioned on the sub-domain where
# the rival is wrong. Each witness was built against the rival (elaborates) and
# against the frozen solution (fails), and each conditioning hypothesis was
# checked jointly satisfiable. The triple is peeled with `simp only`, never
# `unfold`, for the measured reason documented at `_triple_witness`: `unfold`
# errors on a callee absent from the goal, which on a control-flow rival is
# precisely the gold-vs-rival difference, and it let a forged witness clear both
# halves.
#
# The gold-side failure signatures were established as REFUTATIONS rather than
# tactic mismatches by the forgery experiment, not by reading the error text:
#
#   * VERDICT-LEG witnesses fail on gold with `unsolved goals hd : CallerHandle
#     hs : screenRefuses (presentCaller hd) = true hh : True ≤ wp (do let accepted
#     ← if screenRefuses (presentCaller hd) = true then pure false else pure true
#     if accepted = true then pure (some (anomalyScores (preparedOf hd))) else
#     pure none) fun out => out = if screenRefuses (presentCaller hd) = true then
#     none else some (anomalyScores (preparedOf hd)) hc : wp (pure none …` — gold's
#     served result IS the one the frozen clause demands under the conditioning
#     hypothesis, so `False` is genuinely unprovable. Proved informative by
#     FLIPPING THE CONDITIONING HYPOTHESIS: the same witness with the opposite
#     verdict refutes gold's counterpart branch instead (the pair
#     screen-ignores-refusal / screen-refuses-everything is exactly that flip, and
#     each half is a recorded refutation of its own rival), so gold's exit code
#     tracks the claim rather than the tactic shape.
#   * VALUE-LEG witnesses fail on gold with a message that LOOKS syntactic and is
#     not: `simp` PROVES the clause on gold, so the reduced hypothesis collapses to
#     `True` and the refutation step has nothing to contradict — measured on the
#     current bytes as `Application type mismatch: The argument hc has type True
#     but is expected to have type anomalyScores (preparedOf hv) = [] in the
#     application h hc` (served-value leg) and `Invalid field `symm`:
#     The environment does not contain `True.symm` hc has type True` (offset value
#     legs). On the RIVAL the same probe reduces to the concrete false equation and
#     the refutation closes. That pair is the refutation. The shape was
#     additionally checked non-forgeable in the other direction: a witness
#     asserting the rival is CORRECT at an agreement point breaks the RIVAL build
#     (exit 1 => `witness-unproven`), so it cannot be smuggled through.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; the gate ignores this list.
# The sibling's four axiom probes (mismatch_advisory/prepare soundness, scorer +
# token soundness, offset provenance, prepared-scorer containment) are the
# obligations axiom_check.py / G-AX already discharge for this bundle
# (`anomalyScores == -_compute_chunked_score_samples`, `percentileAt ==
# np.percentile`, the object properties, and the grounding of the three screen
# properties: the advisory is drawn exactly on a labelling MISMATCH IN PRESENCE,
# the refusal exactly on a labelling that DISAGREES or on a shape/precision the
# screen rejects, and the advisory does not change the scores).
AXIOM_TESTS = []
