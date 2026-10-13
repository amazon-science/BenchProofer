"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-25931 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside ``-- impl-start`` / ``-- impl-end`` — and, for the
admissibility case, inside ``-- proof-start`` / ``-- proof-end`` — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_fit`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed, no ``sorry``/``admit``/``native_decide``,
no new ``axiom``/``theorem``/``lemma``); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models one contracted procedure whose contract bundles four separate devices: a
side-effect advisory tally on shared estimator state, two unforgeable
provenance ``@Predicate`` tokens, a read-only input held at a fractional
permission, and a biconditional linking an offset-set flag to whether
calibration was requested. This Lean bundle models the purely functional core
the change turns on — the threshold-selection tail together with the description
of admissible input that fitting leaves behind, plus the traversals of the fitted
model the tail actually spends — so the nagini devices collapse onto eight
postcondition clauses (below). The adversarial ARGUMENT of
each nagini rival carries over; its mechanics are re-expressed against this
carrier, and the rivals whose distinction this carrier does not keep are DROPPED
with a reason (see the accounting block at the bottom) rather than fabricated
into something else.

DEFENDED SURFACE (one obligation, ``correct_fit``; eight independent top-level
clauses). ``implementation_fit`` returns a ``Fitting`` — the fitting tail AS THE
PROGRAM IT RUNS — so ``problem_spec_fit xOrig contaminationAuto contamination
fitting`` reads the values off it with ``fitting.result`` and the work it spends
off its structure with ``fitting.traversals``. Both readers take an
INTERPRETATION of the scoring effect — ``sc : Scoring``, i.e. what one traversal
of the fitted model turns a payload into — and the whole conjunction below is
stated under ``∀ sc : Scoring``, so nothing is claimed about any particular
scoring function and every clause is claimed for all of them. The clauses below
suppress that reader argument except where the interpretation appears in the
claim itself (C3).

The conjunction carries TWO preconditions, and they are the same shape: each
names a way the training carrier makes ``fit`` RAISE inside its first validation,
leaving no threshold and no width record, so that there is no fitted estimator
for the description to describe.

  * ``xOrig.namesInspectable = true`` — a carrier whose column labels the
    estimator cannot INSPECT (labels of mixed kinds; the label inspection raises
    rather than answering).
  * ``xOrig.contentAdmissible = true`` — a carrier whose CONTENT the
    admissibility check declines outright (no rows to describe, no columns to
    describe, or a value that is not finite).

See the two "WHERE THE DESCRIPTION IS NOT ASKED AT ALL" sections below for the
measurements and the controls. These are the only antecedents on the whole
obligation, and each is PAID FOR at the other end of the tail: the LATER carrier
gets the opposite treatment in both cases — C5's fifth leg makes an uninspectable
one a positive obligation to refuse, and C5's sixth leg does the same for one
whose content is declined. The spec pins EXACTLY:

  * (C1 no-advisory)  ``fitting.result.warned = false`` — selecting the threshold
    must not surface a feature-name-consistency diagnostic. This is the clause the
    reported defect violates and the clause the FAIL_TO_PASS test observes (it
    promotes that diagnostic to an error and fits a name-carrying table with a
    configured threshold level).
  * (C2 unconfigured) ``contaminationAuto → fitting.result.offset = -0.5`` — with
    no threshold level configured the offset is the fixed constant.
  * (C3 configured)   ``fitCompletes xOrig contaminationAuto = true →
    ¬ contaminationAuto → fitting.result.offset =
    percentile (sc (checked xOrig.values)) (100.0 * contamination)`` —
    otherwise the offset is the configured percentile of the model's anomaly
    scores OF THE TRAINING DATA at the percentage-scaled rank, and the content
    those scores are taken over is the training payload as the admissibility
    check handed it on, not the caller's own object. The first antecedent is the
    storage-form limit: see "WHERE THE DESCRIPTION STOPS" below.
  * (C4 record)       ``fitting.result.reference = {nFeatures := xOrig.nFeatures,
    hasFeatureNames := xOrig.hasFeatureNames}`` — the description of admissible
    input the fitted estimator holds is taken from the TRAINING carrier alone:
    its width and its feature-name status, on both branches and at both metadata
    values. Selecting the threshold is not allowed to re-describe it.
  * (C5 enforcement)  ``∀ z, ((z.nFeatures != xOrig.nFeatures) →
    (fitting.result.scoreLater z).refused = true) ∧
    (z.namesInspectable = true → (fitting.result.scoreLater z).warned =
    (xOrig.hasFeatureNames != z.hasFeatureNames)) ∧
    (fitting.result.scoreLater z).refAfter = fitting.result.reference ∧
    ((fitting.result.scoreLater z).refused = false →
    (fitting.result.scoreLater z).handedOn =
    {values := checked z.values, nFeatures := z.nFeatures,
    hasFeatureNames := false,
    form := Form.reshaped z.form Form.sparseByRow,
    namesInspectable := true, contentAdmissible := true}) ∧
    (z.namesInspectable = false →
    (fitting.result.scoreLater z).refused = true) ∧
    (z.contentAdmissible = false →
    (fitting.result.scoreLater z).refused = true)`` — that
    record is what the fitted estimator ENFORCES afterwards: a carrier of a
    disagreeing width is refused, a disagreeing feature-name status draws the
    diagnostic exactly wherever the status can be READ at all, handing the
    estimator a carrier never re-describes
    what it accepts, a carrier it does NOT turn away is handed to the fitted
    model in the content the admissibility check re-presents rather than in the
    caller's own presentation — and as the estimator's OWN presentation of that
    carrier, whose every field is pinned: the presented width, the presented
    storage form, no feature-name metadata of its own, and a description the
    admissibility step would itself admit (labels it will inspect, content it
    accepts) — and a carrier the estimator cannot work with at
    all — whose labels it cannot inspect, or whose content it declines — is turned
    AWAY. NOTE the refusal leg is an IMPLICATION, not a
    biconditional: agreeing widths are not claimed to be SUFFICIENT for
    acceptance here, because the real estimator has a further refusal ground
    (name identity) that this model does not carry. The converse is supplied,
    narrowly, by C6 and C7. The handed-on leg is likewise guarded by
    non-refusal, so it claims nothing about a carrier the estimator turns away.
    The FIFTH and SIXTH legs are the two additions that are not guards but
    obligations: each is what the real path does before it ever reaches the width
    comparison, and each refutes an entry point that checks the width, finds it
    agrees, and hands on a carrier the real code refuses to work with
    (``later-scoring-admits-uninspectable``,
    ``later-scoring-admits-inadmissible-content``). Note the asymmetry between
    them, which is measured rather than chosen: the warning leg IS guarded by
    inspectability and is NOT guarded by admissibility, because the real
    validation settles the naming question (``_check_feature_names``) BEFORE it
    puts the content to the admissibility check, so a content refusal does not
    suppress a name-status diagnostic that has already been raised.
  * (C6 self-admission) ``xOrig.hasFeatureNames = false →
    (fitting.result.scoreLater xOrig).refused = false`` — an estimator fitted on
    a NAMELESS carrier still admits that very carrier afterwards. Guarded by the
    metadata flag precisely because a name comparison must not be able to arise:
    were the training carrier name-bearing, the real code would compare its names
    against the recorded ones, and the model cannot see whether they agree.
  * (C7 admission)    ``∀ z, z.contentAdmissible = true →
    z.nFeatures = xOrig.nFeatures →
    (xOrig.hasFeatureNames = false ∨ z.hasFeatureNames = false) →
    z.namesInspectable = true →
    (fitting.result.scoreLater z).refused = false`` — a carrier whose content the
    admissibility check ACCEPTS, whose width is the training width and whose
    labels the estimator can inspect is
    ADMITTED, wherever a name comparison cannot arise (one side bears no names).
    The first antecedent is about ACCEPTANCE, deliberately not about the content
    being a FIXED POINT of the re-presentation (``z.values = checked z.values``):
    the check accepts content it also REWRITES, and an admission region pinned to
    the fixed point would leave every ordinary caller's carrier — every list of
    ints, every float64 frame — free to be refused. See "WHERE THE DESCRIPTION IS
    NOT ASKED AT ALL (the content-admissibility precondition)" below.
    Absent metadata is never itself a ground for refusal, in either direction.
    The disjunctive antecedent is the deliberate model limit, not slack: see
    refinement.md, "name PRESENCE, not name IDENTITY", and the
    ``pos-name-identity-refusal`` positive below, which is the machine-checked
    control showing a faithful impl that DOES refuse on name identity verifies.
    The fourth antecedent is the other side of C5's fifth leg, and the first is
    the other side of its sixth — an admission clause must not contradict a
    refusal C5 REQUIRES — and neither costs anything, because in both cases the
    refusal is required rather than left open.
  * (C8 work)         ``fitCompletes xOrig contaminationAuto = true →
    fitting.traversals = (bif contaminationAuto then []
    else [checked xOrig.values])`` — choosing the threshold is WORK and the work
    itself is pinned, not a report of it: the program traverses the fitted model
    over exactly the checked training payload, exactly once, on the configured
    branch, and NOT AT ALL on the constant branch. This is the observable
    ``test_iforest_chunks_works1/2`` count through their ``get_chunk_n_rows``
    mock, and the one two breaking implementations forged when an earlier model
    carried it as a ``Nat`` output field (verdict.md CE-1/CE-2). It carries the
    same storage-form antecedent as C3, and for the same measured reason.

WHY C4-C7 ARE PART OF THE SURFACE, NOT DECORATION. The modeled validation
step is selected by a ``reset`` flag, and that flag governs TWO separate
observables, not one: whether a consistency diagnostic is raised, AND whether the
call DESCRIBES the admissible input from the carrier it is handed or CHECKS that
carrier against the description already held. A spec that observes only the
diagnostic leaves the second consequence free, and an implementation can then
silence the diagnostic by re-describing instead of checking — honestly satisfying
C1 while destroying the width agreement the fitted estimator is supposed to
enforce from then on. C1 alone therefore does not pin the modeled behavior; C4
pins what fitting leaves on record and C5 pins that the record is enforced and
survives later use. The three ``later-scoring-*`` rivals that break that
enforcement (``-accepts-any-width``, ``-redescribes-record``,
``-silent-on-names``) and the two ``*-record`` rivals below are exactly the
implementations that satisfy C1, C2 and C3 everywhere and are still wrong.

C5's refusal leg alone is still not enough, in the other direction: an
implementation that refuses EVERY later carrier satisfies "disagreeing width ⇒
refused" vacuously, and one that treats a carrier's ABSENT metadata as
inadmissibility satisfies it too. Both are wrong, and both are real behaviours of
the class of impl that over-reads ``_check_feature_names``. C6 and C7 are the
converse obligations that reject them (``later-scoring-refuses-everything``,
``names-treated-as-inadmissibility``), stated exactly as narrowly as the real code
permits — which is why weakening the guard on them was a repair and deleting them
would not have been.

WHY THE OUTCOME CARRIES A CARRIER AND NOT ONLY FLAGS. The entry point is where a
carrier crosses from the caller's own presentation into the presentation the
fitted model operates in, and the check that licenses the crossing is separable
from the crossing itself. An entry point can therefore run its admissibility
checks IN FULL — right refusals, right diagnostic, record kept — and then hand
the model the caller's object rather than the one the check re-presented. Nothing
about the outcome's booleans or its record differs, so a contract over flags
alone cannot reach it; the outcome has to carry the VALUE that crosses. That is
what ``ScoreOutcome.handedOn`` is, and ``later-scoring-forwards-caller-payload``
is the rival it rejects — built on the real repository in the same shape (public
scorer performs the feature-name and feature-count checks, then calls the
non-validating private scorer on its raw argument) and measured there:
FAIL_TO_PASS passes, four PASS_TO_PASS bodies fail. The same reading is what
makes C3's right-hand side quantify over ``checked xOrig.values`` rather than
``xOrig.values``: what fitting scores is what its own check handed on.

AND WHY THAT CARRIER IS A WHOLE CARRIER AND NOT A PAYLOAD. What crosses is not a
naked list of numbers; it is the estimator's OWN presentation of the data, and a
presentation describes itself. Carrying only the content would leave the
description free, and an entry point can convert the content perfectly and hand
the model that content still wearing the CALLER's account of itself — its label
status, its inspectability, its admissibility — which is a second break, in the
same place, that a payload equation cannot see. So C5's fourth leg is ONE record
equation pinning all six fields, and the three that are not the content or the
width are the self-description: the presentation advertises no feature-name
metadata (the validated array is bare, whatever frame the caller wrapped it in),
its labels are ones the estimator will inspect, and its content is content the
check accepts. ``later-scoring-hands-on-caller-description`` is the rival that
leg rejects and the payload equation admitted, and the distinction is not a
modelling preference: it is measured on the real patched callee by
``axiom_check.py`` leg E, whose in-loop control is the name-bearing carrier —
where the caller's object DOES bear labels the two descriptions demonstrably
disagree, so ``hasFeatureNames := false`` is an answer the real callee could have
given otherwise (measured: 306 leg-E observations, 90 of them under a
name-bearing caller's carrier, 0 mismatches; and with that control rewritten to
assert the collapsed reading instead — the presentation's label description IS
the caller's — the same run reports 90 mismatches and exits 1, so the leg is
refutable rather than decorative). G-CONF's real-code leg
reads all six fields off the object the scoring core was ACTUALLY handed, and
its ``forward-caller-description`` mutation — content converted correctly,
description taken from the caller — is caught.

WHY C8 IS A PROGRAM PROPERTY AND NOT A FIELD. Two independently-built breaking
implementations (verdict.md CE-1/CE-2) move the chunked-scoring work — one hoists
it above the branch so the constant arm pays for a traversal it never uses, one
adds a discarded warm-up traversal — while REPORTING the count the contract asks
for. Measured against the earlier model that carried the count as a ``Nat`` field,
both are provably indistinguishable from the frozen impl
(``implementation_fit = <rival>`` closes by ``intro x c f; cases c <;> rfl``), so
NO predicate over the returned record could reject them. Deep-embedding the tail
as a ``Fitting`` program removes the field a rival could write: ``traverse`` is the
only way to reach anomaly scores, and ``Fitting.traversals`` reads the work off
the program's STRUCTURE. Both rivals are now rejected
(``traversal-hoisted-above-branch``, ``extra-discarded-traversal``), and the
machinery lives in the FROZEN ``pure`` spec region, so a variant cannot redefine
what counts as a traversal either — ``markers.same_spec`` rejects the file.

WHY NO SCORING FUNCTION IS DECLARED (SCOPE, NOT A CLAUSE). Deep-embedding the
tail is necessary and was measured NOT to be sufficient on its own. While a
top-level ``opaque scoreCore : List Float → List Float`` existed it was in scope
for the impl region, so an implementation could reach anomaly scores WITHOUT a
``traverse`` node: perform the real chunked-scoring work by applying it directly,
and build the ``traverse`` node the contract expects as well. Two independently
built breaking implementations did exactly that (verdict.md: a warm-up
``let _warm := scoreCore x.values``, once on each branch in turn), and a third
kept a decorative ``traverse`` node whose continuation discarded the scores it
yielded and recomputed them off-structure. No predicate over ``Fitting`` can
reject the first class at all: an unused ``let`` binder of a pure application is
erased by definitional equality, so such a rival IS the same Lean value as the
frozen impl (``implementation_fit = <rival>`` closes by
``intro x c f; cases c <;> rfl``) — the same impossibility the forged ``Nat``
field had.

The repair is SCOPE rather than another clause: the declaration is gone, both
readers are parameterized over an interpretation (``Scoring``), and the
obligation is universally quantified over it. No term in the file denotes "the
anomaly scores of this payload" for an implementation to apply, so the audited
counterexample no longer elaborates (measured: ``unknown identifier
'scoreCore'``) instead of verifying. ``uncounted-work-off-structure`` below is
the third rival re-expressed with what remains nameable, and C3 rejects it: the
threshold must be the configured percentile of THE SCORES THAT TRAVERSAL
YIELDED, which a continuation ignoring its argument cannot satisfy under every
interpretation.

MEASURED RESIDUAL, recorded rather than hidden. ``Scoring`` is an inhabited type
— it has to be, or ``∀ sc`` would be vacuous — so ``Classical.arbitrary
(α := Scoring)`` denotes SOME function, an implementation may apply it and
discard the result, and that file elaborates (measured). What remains is not a
weakness a clause can close but a refinement question, and the refinement rule
is the defence: a chunked-scoring pass over a payload corresponds to a
``Fitting.traverse`` node and to nothing else (mapping.md). An arbitrary
inhabitant of ``Scoring`` denotes no callee of the modeled tail, so an
implementation that materializes one and applies it has invented a Python
operation its counterpart does not perform — unmapped invention, which is
G-EQ's question and not C8's. Written down here because the alternative, a
clause asserting that the implementation "applies no arbitrary function", is
precisely the kind of assertion no control could refute.

WHERE THE DESCRIPTION STOPS (the storage-form limit on C3 and C8). The carrier
handed to fitting has a STORAGE form as well as a content, and the two are not
interchangeable to the code the patched tail runs. ``InputData.form`` carries
the form, three-valued (``Form.dense``, ``Form.sparseByRow``,
``Form.sparseByColumn``) because the scoring path is partial on the sparse LAYOUT
and not merely on sparseness, and the frozen ``pure`` region defines
``fitCompletes x auto = auto ||
(Form.reshaped x.form Form.sparseByColumn).traversable``: the runs on which
fitting reaches a result at all. C3 and C8 — the derived threshold and the
traversal record — are
asked only there. MEASURED against the real callees in the instance image, not
argued: the fit-time admissibility check admits sparse content and hands it back
sparse in the COLUMN-indexed layout (a row-indexed presentation is returned
column-indexed as well, which is what ``Form.reshaped`` says), and the
non-validating scoring path the tail then enters raises
on that form (``ValueError: X should be in csr_matrix format``) while the dense
presentation of the SAME numbers is traversed and scored, for an estimator fitted
on either form — so the refusal is about the form and not about the payload.
End to end on the patched code: a configured fit of a sparse carrier raises with
no threshold attribute set and the record of admissible input already
established; the unconfigured arm of the same carrier returns the constant; every
one of those calls succeeds on the pre-change code, so the divergence is
introduced by the change under test and is not a pre-existing property being
smuggled in. An unguarded C3/C8 would therefore assert a threshold and one
traversal for a run that does not happen — over-strength, not strength.

The limit is a NARROWING and it is bounded on three sides, each one machine- or
container-checked rather than asserted:

  * ``pos-sparse-declines-threshold`` (soundness) — the faithful counterpart at
    the boundary, which declines to invent a threshold exactly where the
    traversal is impossible, MUST verify, and does.
  * ``sparse-guard-inverted`` (uniqueness) — a rival that reads the limit as a
    general licence to skip the work, spending its traversal only where the
    description withholds its claims, is REJECTED by C8 on the dense branch.
  * ``sparse-abort-emits-diagnostic`` (uniqueness) — a rival that reads the
    withheld threshold as a withheld run, surfacing the feature-name diagnostic
    on the way out of the abort, is REJECTED by C1 at a SPARSE witness carrier.
    That is what scopes the guard to exactly two clauses: C1, C4, C5, C6 and C7
    carry no storage antecedent and are still required of the aborted run, which
    really is observed to emit no diagnostic, to leave the training carrier's
    record behind, and to enforce it afterwards.

Grounded outside Lean on the same two sides: ``axiom_check.py``'s leg S calls the
real check and the real scoring path at both widths and both storage forms,
asserting the sparse refusal AND the dense acceptance (the negative control: an
assertion the dense leg could not refute would not be grounding), and
``conformance_check.py``'s real-code leg asserts ``fitCompletes`` against the
patched estimator in BOTH directions on every draw — the tail must abort exactly
where the guard says and complete everywhere else — then, on each abort, compares
the record the aborted run established and fits the same numbers densely as a
control. The sparse UNCONFIGURED lane keeps the full obligation on both legs, and
two of that gate's mutations abuse the limit in either direction (traversing on
the sparse constant lane, and declining every sparse carrier) and are caught.
``fitCompletes`` lives in the FROZEN spec region, so a variant cannot redefine
which runs it covers either — ``markers.same_spec`` rejects the file.

WHERE THE DESCRIPTION IS NOT ASKED AT ALL (the label-inspectability precondition,
and the obligation that pays for it). Three carriers pass through this tail: the
presentation the caller hands ``fit``, the object the fit-time check hands back,
and the later carrier presented to the fitted estimator's public scoring entry
point. All three inhabit ONE Lean type, which is faithful only if every
distinction the real callees draw between them is expressible in its fields.
``hasFeatureNames`` alone is not enough: it forces every carrier into "bears
names" or "bears none", and BOTH of those are cases the estimator can ANSWER.
There is a third. MEASURED in the instance image:
``sklearn.utils.validation._get_feature_names`` RAISES ``TypeError`` for a frame
whose column labels are of MIXED kinds — some textual, some not — rather than
returning a label list or ``None``; a frame whose labels are ALL non-string is a
DIFFERENT case that answers "no names". And ``_validate_data`` reaches that
inspection before the width check, at fit time and at score time alike.

``InputData.namesInspectable`` carries the case, and the model uses it in
OPPOSITE directions at the two ends of the tail. At the fit end it is a
PRECONDITION on the whole obligation: such a fit raises inside its first
validation, leaving neither a threshold nor a width record, so there is no fitted
estimator to describe. At the scoring end it is an OBLIGATION — C5's fifth leg,
``z.namesInspectable = false → refused = true`` — because what the estimator does
with such a carrier afterwards IS observable. Only two things are guarded by it:
C5's warning leg (a name-status delta cannot be reported for a status that was
never readable) and C7's admission (an admission clause must not contradict the
refusal C5 requires). So this is not a narrowing on balance: one antecedent is
added at one end and one obligation at the other.

Bounded on three sides, each machine- or container-checked rather than asserted:

  * ``pos-uninspectable-fit-declines`` (soundness) — the faithful counterpart at
    the boundary, which leaves a refusing placeholder for a carrier it cannot
    inspect rather than inventing a threshold for it, MUST verify, and does.
  * ``later-scoring-admits-uninspectable`` (uniqueness) — the collapsed reading
    itself, an entry point that refuses on the width alone and hands on a carrier
    whose labels the real code will not work with, is REJECTED by C5's fifth leg.
  * ``names-treated-as-inadmissibility`` and ``later-scoring-refuses-everything``
    are still rejected, by C7 and C6, so the precondition did not buy a licence to
    refuse: absent metadata is still not a ground for refusal and blanket refusal
    is still wrong.

Grounded outside Lean on both sides: ``axiom_check.py``'s leg L presents mixed
labels at three widths, to the inspection itself and through the fitted
estimator's public scoring path AT THE TRAINING WIDTH (so no width check could
account for the refusal), and on every observation the homogeneously labelled
carrier of the SAME payload at the SAME width is the negative control — read and
scored. The precondition half is measured too: the fit raises, leaves no
threshold, and the homogeneously labelled control fit produces one. Any control
that stops discriminating is a hard failure of the leg, as is a leg that never
fires. ``conformance_check.py``'s real-code leg asserts the precondition against
the patched estimator in BOTH directions on every draw, asserts that such a fit
leaves neither threshold nor width record, fits the same numbers under
homogeneous labels as a per-abort control, and asserts that every uninspectable
probe is turned away BY THE LABEL INSPECTION at the training width with the
homogeneous presentation accepted there. Four of that gate's mutations abuse the
limit in either direction — dropping the precondition, over-claiming it onto
merely unlabelled carriers, admitting an uninspectable later carrier on a width
check, and reporting a name-status delta for labels never readable — and all four
are caught. Both the field and the precondition live in FROZEN spec regions, so a
variant can neither redefine the case nor drop the antecedent.

WHERE THE DESCRIPTION IS NOT ASKED AT ALL (the content-admissibility
precondition, the obligation that pays for it, and the C7 antecedent it
replaced). The label inspection is not the only partial step in front of this
tail. MEASURED in the instance image: ``sklearn.utils.validation.check_array``,
which ``_validate_data`` calls on the way in, RAISES ``ValueError`` for content
with no rows to describe, for content with no columns to describe, and for
content holding a value that is not finite — and it does so at fit time and at
score time alike. None of those three is a case ``namesInspectable`` or
``form`` can carry: each is a bare array whose labels the inspection answers
about, answering "no names", and each is dense. So this is a THIRD partiality,
independent of the other two, and ``InputData.contentAdmissible`` carries it.

The model uses the field in the SAME two opposite directions. At the fit end it
is a PRECONDITION on the whole obligation: such a fit raises inside its first
validation, leaving neither a threshold nor a width record. At the scoring end it
is an OBLIGATION — C5's sixth leg, ``z.contentAdmissible = false → refused =
true`` — because what the fitted estimator does with such a carrier IS observable.
Exactly ONE thing is guarded by it, C7's admission, and nothing else: in
particular C5's WARNING leg is deliberately NOT guarded by it, because the real
validation settles the naming question before it puts the content to the check.
So this is not a narrowing on balance either: one antecedent is added at one end
and one obligation at the other.

It also CLOSES a hole rather than trading one for another. C7's first antecedent
used to be ``z.values = checked z.values`` — the later carrier's content already
being a fixed point of the re-presentation. That was a hole, not a limit: the
check accepts content it also REWRITES (a list of ints, a float64 frame, an
integer column), so on the old reading every such carrier — the ordinary case —
sat outside C7's region and was free to be refused, and a rival that refused
exactly the carriers whose content the check would rewrite verified against the
spec while diverging from the estimator. Admission is now stated on the region
the estimator actually admits: content the check ACCEPTS, rewritten or not.
``content-rewrite-treated-as-inadmissibility`` is that rival, and it is now
REJECTED. Note the consequence for ``checked_idem``: no clause's region is pinned
to the fixed point any more, so that axiom is a measured fact about the callee
that no clause and no proof step consumes (refinement.md, "Assumed, consumed by
nothing"); it is retained because it is independently measured and because a
retained eq-attack rival replays against it.

Bounded on three sides, each machine- or container-checked rather than asserted:

  * ``pos-inadmissible-content-fit-declines`` (soundness) — the faithful
    counterpart at the boundary, which leaves a refusing placeholder for a
    carrier whose content the check declines rather than inventing a threshold
    for it, MUST verify, and does.
  * ``later-scoring-admits-inadmissible-content`` (uniqueness) — the collapsed
    reading itself, an entry point that refuses on the width and the label
    inspection but hands on content the real code declines outright, is REJECTED
    by C5's sixth leg.
  * ``content-rewrite-treated-as-inadmissibility`` (uniqueness) — the converse
    error, an entry point that treats "the check would rewrite this" as "the
    check would decline this", is REJECTED by C7 at an ordinary carrier. Together
    with ``names-treated-as-inadmissibility`` and
    ``later-scoring-refuses-everything``, still rejected by C7 and C6, that shows
    the precondition bought no licence to refuse.

Grounded outside Lean on both sides: ``axiom_check.py``'s leg D presents each of
the three declined contents at three widths, to the check itself and through the
fitted estimator's public scoring path AT THE TRAINING WIDTH (so no width check
could account for the refusal), and on every observation the ordinary content of
the SAME width is the negative control — accepted, fitted and scored; each
declined content is additionally asserted still LABEL-INSPECTABLE, which is what
makes the field irreducible to ``namesInspectable`` rather than merely distinct
from it. A leg that never fires, and a control that stops discriminating, are
both hard failures. ``conformance_check.py``'s real-code leg asserts the
precondition against the patched estimator in BOTH directions on every draw,
reads off the estimator WHICH step declined (a fit that leaves no width record
was refused by the content check, not by the width check), asserts that such a
fit leaves neither threshold nor width record, and turns every declined content
away at the TRAINING width with the ordinary content of that width accepted
there. Four of that gate's mutations abuse the limit in either direction —
dropping the precondition, over-claiming it onto content the check merely
CONVERTS, admitting an inadmissible later carrier on a width check, and treating a
re-presentation as a refusal — and all four are caught. Both the field and the
precondition live in FROZEN spec regions, so a variant can neither redefine the
case nor drop the antecedent.

BINDER STRUCTURE. Three input binders: ``xOrig`` (the data carrier, carrying
six fields: its ``values`` payload, its ``nFeatures``
width, its ``hasFeatureNames`` metadata flag, its ``form`` storage form, its
``namesInspectable`` label-inspectability and its ``contentAdmissible``
content-admissibility),
``contaminationAuto`` (branch
selector), ``contamination`` (the rank); plus the universally quantified later
carrier ``z`` inside C5, C6 and C7. All are load-bearing and all are MOVED across
the reject witnesses — counted over the shipped manifest:
``contaminationAuto`` takes both values (21 ``false`` / 10 ``true``
instantiations), ``xOrig.hasFeatureNames`` takes both values (20 ``false`` / 11
``true``), ``xOrig.nFeatures`` takes SIX distinct widths (1-6), ``xOrig.values``
TWENTY-EIGHT distinct payloads, ``contamination`` EIGHTEEN distinct levels
(0.05-0.75, and every level a witness CONFIGURES lies inside the interval the
estimator declares for that parameter), ``xOrig.form`` takes the column-indexed sparse layout as well as
the dense one (the sparse one being the C1 witness that scopes the guard above;
the soundness positive covers every form by casing on the field), and the
``z`` probes reach the row-indexed layout through the new layout rival below,
whose refutation turns on which of the two sparse layouts crosses into the fitted
model. The C5/C6/C7 witnesses instantiate ``z``
at EIGHT distinct KINDS of
carrier — a narrower nameless one, a narrower name-carrying one, one of the
training width that carries names where the record has none, one of the training
width that is nameless and whose payload is NOT already in the accepted numeric
form (the region where the handed-on leg's CONTENT half discriminates; its
SELF-DESCRIPTION half discriminates at the name-bearing probe of the third kind
instead, and its STORAGE-FORM half at the SPARSE probe of the fourth kind below,
which is why that leg is attacked three times), one of the training width that is
nameless and presented in the ROW-INDEXED SPARSE layout (the only region where
the handed-on leg's form half has content, since dense content crosses dense
whichever layout a check accepts), one of the training
width whose labels the estimator cannot inspect, one of the training width whose
content the check declines outright, and (C7) an ORDINARY nameless carrier of the
training width — content the check accepts and re-presents, which is the case the
admission clause has to cover and the one an admission region pinned to the
re-presentation's fixed point would have missed — plus, for C6, the training
carrier itself; over the battery those instantiate 44 distinct carrier literals. So
the thirty-one witnesses probe thirty-one DISTINCT input points and no binder
is held at one value across the battery. ``xOrig.namesInspectable`` and
``xOrig.contentAdmissible`` are the two
fields a reject witness cannot move: they are two of the obligation's three
preconditions, so a
witness must discharge both (all 31 do, by ``decide`` at the literal) before it can
refute anything, and their ``false`` sides are instead covered where they are
observable — on ``z`` (the C5 fifth- and sixth-leg witnesses above) and by the
``pos-uninspectable-fit-declines`` and ``pos-inadmissible-content-fit-declines``
soundness cases, whose impls branch on the field. The third precondition is not a
field at all — it is the estimator's own verdict on the configured threshold LEVEL
— and it is discharged the other way round: the level moves freely (twelve
distinct configured values), and each witness assumes the validation admits the
one it stands at, which is exactly what G-AX's parameter-domain leg measures. Its
refused side is likewise covered where the behaviour is observable, by the
``pos-declines-refused-level`` soundness case, whose impl branches on that verdict. The variation is
MEANINGFUL rather than several spellings of one point: each clause is attacked at
both values of the binder that guards it (C1 at both metadata values, on both
branches AND on both storage forms, C2 on branch-existence and branch-value, C3
on value, carrier, rank
and the interpretation of the scoring effect,
C4 on the width leg and the metadata leg, C5 on each of its seven legs and on
all three separable halves of the fourth -- and, for the seventh, on BOTH of its
lanes and in BOTH directions of the count as well as on the payload it pins, C6
and C7 on each direction of the admission obligation — and, for C7, from both
sides of the content question, a rival that refuses content the check would
merely rewrite and one that admits content the check declines — C8 on both branches — a
traversal added where the spec allows none and a second added where it allows
one — and both storage-form guards from either side, a rival that withholds the
work where the description still applies and one that withholds a claim the
description never withheld), and for the two C1 rivals that are branch-local the
agreement point was
measured — the same witness re-stated where the rival agrees with the frozen
impl FAILS against it (exit 1), which is what shows the probed point is the one
that discriminates.

THE CARRIER, AND WHY THREE WITNESS ROUTES ARE NEEDED. Clauses C1, C4, C6, C7, C8
and C5's legs other than the fourth are fully TRANSPARENT: ``warned``, the record,
the later-scoring flags and the traversal LIST are computed by the deep-modeled
validation helper and the ``Fitting`` equations out of booleans, naturals and
lists, so those rivals are refuted at plain literal inputs. C5's fourth leg is
BOTH, and that is a consequence of its pinning a whole carrier: its CONTENT
component is an equation between two applications of the opaque re-presentation
callee, so the rival that breaks it is witnessed on the conditioning route the
offset clauses use, while the three components that are the presentation's
SELF-DESCRIPTION and the one that is its STORAGE FORM are values the modeled step
computes out of booleans and a finite enumeration, so the rivals that break those
are refuted transparently — it projects the offending field off the record
equation (``congrArg InputData.hasFeatureNames``, or ``congrArg InputData.form``
for the layout rival) and settles it by ``decide``,
binding no hypothesis at all. C1's flag reduces under
``simp`` directly; the C4/C5/C6/C7 witnesses project the offending component
(``congrArg Reference.nFeatures`` / ``Reference.hasFeatureNames``, or the C5
conjunct) and settle it by ``decide`` after ``simp only`` unfolds the modeled
step; the C8 witnesses project ``List.length`` off the traversal list (a length
clash is decidable where a list of opaque ``Float`` payloads is not) — four tactic
routes were measured for these and this is the one that
discriminates (a bare ``simp`` leaves a ``do``-block residual that reduces on
neither leg, so it fails against rival AND gold and attributes nothing). The two
offset clauses are not reachable that way, for two DIFFERENT reasons, and the
distinction matters when authoring a witness. C3's right-hand side is stated over
the ``opaque`` unchanged numerical callee ``percentile``, applied to the
quantified interpretation's value — neither has a computable value at all. C2's
is a ground ``Float`` literal, which is not opaque but is still not settled by
``decide``: this carrier has no
kernel-reducible ``Decidable`` instance for ``Float`` equality, so a literal
clash as blunt as ``0.5 = -0.5`` has to be conditioned on rather than computed
(measured: four tactic routes — ``decide``, ``norm_num``, ``cases``, ``simp`` —
all fail to close it, and conditioning on the disequality lands it). C7's content region is a THIRD reason, and
the one the newest rival turns on: its refusal predicate is stated over the opaque
re-presentation callee too, so ``decide`` is stuck there exactly as it is on C3,
and the witness reaches the clause by ASCRIBING the shape the rival gives the
refusal and letting the defeq check reduce it. Either way
those nine witnesses CONDITION on the carrier: each assumes only that the two
terms it must separate differ at the probed input — exactly the sub-domain where
its rival is wrong, and a stronger claim than any single literal could make. One
carrier hypothesis per witness, about ONE term, so the hypotheses are trivially
jointly satisfiable (for C3, for C5's handed-on leg and for C7's content region
because
the callees are
unconstrained — the bundle consumes no property of ``percentile`` at all, only
idempotence of ``checked``, which a non-identity re-presentation satisfies, and
no property whatever of the interpretation, which each witness instantiates
itself; for C2 because the hypothesis is a true ground disequality). A witness
standing on the CONFIGURED lane binds one further hypothesis, and for a reason
that is about the obligation rather than about the carrier: the description is
asked only of a threshold level the estimator's parameter validation admits, so a
witness has to say which level it stands at and that the validation admits it
(``_lvl``, below). That hypothesis is about a THIRD opaque term, independent of
the other two and of every literal, so it cannot conflict with them, and it is
the one hypothesis in the battery that is measured against the real callee
directly rather than argued: G-AX's parameter-domain leg reports the real
validation's verdict at every level any witness below assumes admitted. The
gate's consistency probe confirms the lot (measured: each of the twenty-four
probes exits nonzero, i.e. ``False`` is not derivable from the hypotheses --
twenty-one witnesses carry the level hypothesis, seven of those a carrier hypothesis
as well, and three carry only a carrier hypothesis; the seven unconfigured-lane
witnesses bind nothing at all and are not probed, since with no level configured
the validation never looks at one). Every witness
below was built twice with the real toolchain — it ELABORATES against its rival
and FAILS on the frozen solution — so each is a discriminator that was SEEN to
discriminate, not an assertion that any impl would satisfy.

WHAT THE SPEC PINS UNIQUELY, AND THE FIVE PLACES IT DELIBERATELY DOES NOT
(machine-checked, exit 0, ``#print axioms`` = ``[propext, Classical.choice]`` — no
``sorryAx`` and, note, NOT ``checked_idem``):

    theorem fit_unique_mod_name_identity
        (x : InputData) (a : Bool) (c : Float) (f g : Fitting) (sc : Scoring)
        (hlvl : a = false → levelAdmitted c = true)
        (hins : x.namesInspectable = true)
        (hcon : x.contentAdmissible = true)
        (hf : problem_spec_fit x a c f) (hg : problem_spec_fit x a c g) :
        (f.result sc).warned = (g.result sc).warned
      ∧ (fitCompletes x a = true →
          (f.result sc).offset = (g.result sc).offset)
      ∧ (f.result sc).reference = (g.result sc).reference
      ∧ (fitCompletes x a = true → f.traversals sc = g.traversals sc)
      ∧ ∀ z, (z.namesInspectable = true →
               ((f.result sc).scoreLater z).warned
                 = ((g.result sc).scoreLater z).warned)
           ∧ ((f.result sc).scoreLater z).refAfter
               = ((g.result sc).scoreLater z).refAfter
           ∧ ((z.nFeatures != x.nFeatures) →
               ((f.result sc).scoreLater z).refused
                 = ((g.result sc).scoreLater z).refused)
           ∧ (z.contentAdmissible = true → z.nFeatures = x.nFeatures →
               (x.hasFeatureNames = false ∨ z.hasFeatureNames = false) →
               z.namesInspectable = true →
               ((f.result sc).scoreLater z).refused
                 = ((g.result sc).scoreLater z).refused)
           ∧ (z.namesInspectable = false →
               ((f.result sc).scoreLater z).refused = true
                 ∧ ((g.result sc).scoreLater z).refused = true)
           ∧ (z.contentAdmissible = false →
               ((f.result sc).scoreLater z).refused = true
                 ∧ ((g.result sc).scoreLater z).refused = true)
           ∧ (((f.result sc).scoreLater z).refused = false →
               ((g.result sc).scoreLater z).refused = false →
               ((f.result sc).scoreLater z).handedOn
                 = ((g.result sc).scoreLater z).handedOn)

So any two implementations that verify agree, UNDER EVERY INTERPRETATION OF THE
SCORING EFFECT, on EVERY observable the model carries — the record, and the
fitted estimator's later record behaviour and the whole PRESENTATION it hands
on — content, width, storage form and self-description — at every carrier,
unconditionally; the diagnostic at fit time
unconditionally and at scoring time for every carrier whose labels the estimator
can inspect (a name-status delta about a status the real code never managed to
read is not an observable); and the offset on both branches
together with the traversals the program spends wherever fitting runs to a result
(``fitCompletes``, the storage-form limit above, which the theorem carries as an
antecedent because the description does: on a configured sparse carrier the real
code produces neither of those two observables). On later REFUSAL they agree, and
where the estimator cannot work with the carrier at all — labels it will not
inspect, or content its check declines — they agree on the VALUE too: both refuse,
which is C5's fifth and sixth legs being obligations rather than guards. The agreement has
one gap:
a carrier that bears names presented to an estimator that holds
names. That is not
slack left by accident; it is where the real estimator decides by comparing the
NAMES THEMSELVES (``BaseEstimator._check_feature_names`` raises "The feature names
should match those that were passed during fit"), an observable this model does
not carry, so a faithful impl may legitimately refuse there. Measured, not argued,
on both sides: G-AX confirms the real callee RAISES in exactly those
configurations (``axiom_check.py``, "name-identity refusals confirmed"), G-CONF's
real-code leg confirms it against the patched estimator, and the
``pos-name-identity-refusal`` positive below is a verifying impl that DOES refuse
there — the soundness control for the guards on C6/C7.

The theorem carries the same three preconditions the description does
(``hlvl``, ``hins``, ``hcon``), which are the third, fourth and fifth places: a
configured threshold LEVEL the estimator's parameter validation refuses, a
training carrier whose labels the estimator will not inspect, and one whose
content its admissibility check declines. Two verifying impls may do anything
they like at any of the three, because the real ``fit`` raises before recording
anything — measured in both directions by G-AX's parameter-domain leg (the level)
and legs L and D (the two carrier limits) and by G-CONF's real-code leg, and
controlled by the ``pos-declines-refused-level``,
``pos-uninspectable-fit-declines`` and
``pos-inadmissible-content-fit-declines`` positives. The level precondition is
the one of the three that binds ASYMMETRICALLY: with no level configured the
validation never looks at one, so a run carrying an arbitrary level alongside the
unconfigured marker is described in full — which is why the theorem's ``hlvl`` is
an implication and not an equation, and why the auto-branch witnesses below
discharge it outright.

This is what bounds SPEC-TOO-WEAK by construction rather than by sampling rivals:
a rival that "verifies" is necessarily a reshape of the frozen impl, a
name-identity refusal, a choice of what to do on a configured sparse carrier
(where the real code aborts and the description therefore stops), a choice of
what to do at a threshold level the parameter validation refuses, or a choice of
what to do on a training carrier the label inspection turns away — and it is why
each dropped nagini rival below is justified
by an explicit machine-checked equality with the frozen impl rather than by
argument. Note what C4-C8 restore: with only C1/C2/C3 the bound holds of the
RESULT FIELDS THOSE CLAUSES NAME and says nothing about the record, its
enforcement, or the work performed, which is precisely the room the wrong
implementations used (verdict.md CE-1/CE-2 exploited the last of those).

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling's mandatory
    frame-mutation rival overwrites an input field held at a fractional
    permission and is rejected by the permission system. Lean is referentially
    transparent: no heap, no aliasing, no fractional permission, and ``xOrig``
    is an immutable value with no writable cell. No discriminating witness could
    exist, so the class collapses; no substitute probe is fabricated. (The
    observable that class was reaching for — durable estimator state that outlives
    the modeled call — IS modeled here, as C4's record and C5-C7's enforcement of
    it, and is attacked by eight rivals rather than none.)

  * DIVERGENCE / NON-TERMINATION — VACUOUS on this backend, and vacuous for the
    lean-family reason rather than the velvet one: ``implementation_fit`` is a
    total Lean ``def``, so a non-terminating rival cannot be written at all.
    DEMONSTRATED with two real builds rather than argued. There is no
    ``set_option loom.semantics.termination`` line in the frozen file, so neither
    the "total" nor the "partial" disposition of that lane applies; the carrier
    itself refuses the rival. (a) A plain ``def spin2 (c : Float) : Float :=
    spin2 c`` feeding the offset does not elaborate — ``fail to show termination
    for spin2 … failed to infer structural recursion … well-founded recursion
    cannot be used``, i.e. the diverging impl is not a writable Lean term, so
    there is nothing for a witness to refute. (b) Reaching for ``partial def``
    to get one past the elaborator does not produce a divergence case either:
    an impl whose offset is a ``partial def`` self-call DOES elaborate and IS in
    variant scope (measured: ``variant_problems`` returns ``[]``), and it is
    rejected (exit 1) — but it is not a DIVERGENCE case. Lean's logic is total:
    a ``partial def`` denotes a perfectly ordinary value (its ``Inhabited``
    default), so that rival is refuted exactly as ``forged-constant-offset`` is,
    by C3's value equation over a term the spec does not pin — the same probe
    already shipped, under a different spelling. There is therefore no impl on
    this carrier that "runs forever and satisfies every clause vacuously", which
    is the only thing a divergence rival could test. Not a known hole either: a
    hole needs an impl the fragment ADMITS that verifies vacuously, and no impl
    here verifies without being observationally the frozen one (see the
    functionality bound above).
    (This is NOT the ``loom.semantics.termination "partial"`` spec hole of
    the corpus-wide termination-semantics finding, under which a diverging impl satisfies every
    ``ensures`` vacuously — that hole needs an impl the fragment admits, and
    this straight-line total ``def`` is not one. The nagini sibling carries no
    divergence case either.)

  * UNGROUNDED-ORACLE ECHO — half applies, and is what the C3 rivals attack. C1,
    C2, C4 and C5 are grounded (booleans, naturals and a literal constant). C3
    pins the offset to a computation over the INPUT carrier's own payload, so a
    rival cannot echo an answer key — but it CAN apply the right computation to
    the wrong argument or at the wrong rank, which is exactly what the
    ``foreign-batch`` and ``rank-unscaled`` rivals do.

  * SIDE-EFFECT ON SHARED STATE / CONTROL-FLOW EFFECT — the heart of this
    surface, and the reason it has eight clauses rather than three. The nagini
    advisory tally (an undiscardable mutation of estimator state) becomes the
    value-typed ``warned`` output, and the nagini "was the non-validating path
    actually taken?" control-flow effect becomes the C1 clause: a rival that
    re-runs the consistency check has ``warned = true`` on a name-carrying fit.
    So the nagini control-flow/side-effect rival IS the
    ``second-consistency-pass`` rival below. But the modeled step's ``reset``
    flag has a SECOND state effect — it re-describes the admissible input rather
    than checking against it — and that is the effect C4 and C5 pin. A rival can
    silence the diagnostic by switching the second pass from a check to a
    re-description (``second-pass-redescribes-record``), which satisfies C1
    honestly; the state effect is what refutes it. And the effect can be moved
    without being reported at all: hoisting the chunked-scoring traversal above
    the branch, or spending a discarded warm-up traversal, are control-flow
    effects INVISIBLE to every clause over the returned values — which is why the
    tail is deep-embedded as a `Fitting` program and C8 pins the traversals off
    its structure (``traversal-hoisted-above-branch``,
    ``extra-discarded-traversal``; verdict.md CE-1/CE-2).

  * PARTIAL-DOMAIN / VALUE — APPLIES. ``forged-constant-offset``,
    ``foreign-batch-scored`` and ``rank-unscaled`` are each correct on part of
    the domain (and all three satisfy C1, C2, C4 and C5 everywhere), diverging
    only on the configured branch — the near-miss class the nagini
    provenance-token rivals occupy there.

  * AXIOM lane — DROPPED. ``percentile`` and the re-presentation callee
    ``checked`` are unchanged callees validated against the real ones by
    ``axiom_check.py`` / G-AX, which is where the nagini ``AXIOM_TESTS``
    obligations belong. This
    gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-25931"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each is unique in Solution.lean (asserted at load, so the
# manifest breaks loudly if the frozen solution ever drifts) and each lies
# ENTIRELY inside the region it is meant to edit: _I_* inside
# `-- impl-start`/`-- impl-end`, _P_INTRO inside `-- proof-start`/`-- proof-end`.
# ---------------------------------------------------------------------------
_I_VALIDATE = "  let v0 := validateInput xOrig true unrecorded Form.sparseByColumn"
_I_RECORD = (
    "  let v0 := validateInput xOrig true unrecorded Form.sparseByColumn\n"
    "  let x := v0.carrier\n"
    "  let ref := v0.refAfter")
# The program's single `traverse` node: the ONE place fitting reaches anomaly
# scores, and therefore the one place a traversal can occur. A rival that moves
# work moves this node.
_I_TRAVERSE = "    Fitting.traverse x.values fun scores =>"
_I_OFF = "      let off := percentile scores (100.0 * contamination)"
_I_RET = (
    "      Fitting.done { offset := off, warned := false, reference := ref,\n"
    "                     scoreLater := scoreEntry ref }")
_I_AUTO_RET = (
    "    Fitting.done { offset := -0.5, warned := false, reference := ref,\n"
    "                   scoreLater := scoreEntry ref }")
_I_AUTO_BRANCH = (
    "  if contaminationAuto then\n"
    "    -- 0.5 plays a special role; we take the opposite, and the constant needs no\n"
    "    -- traversal of the fitted model at all: the program is done here\n"
    + _I_AUTO_RET)
# The whole configured branch (comment banner + the traversal node and its
# continuation), and the whole two-branch tail. Used by the reshaping positives
# and by the work-shaped rivals.
_I_ELSE = (
    "  else\n"
    "    -- contamination threshold configured: derive the offset from the model's\n"
    "    -- anomaly scores of the (already-checked) training data, WITHOUT a second\n"
    "    -- admissibility pass — so no feature-name-consistency warning is emitted and\n"
    "    -- the record established from the training carrier stands. Reaching those\n"
    "    -- scores is one traversal of the fitted model and the program's only one.\n"
    + _I_TRAVERSE + "\n" + _I_OFF + "\n" + _I_RET)
_I_TAIL = _I_AUTO_BRANCH + "\n" + _I_ELSE
# The modeled public scoring entry point, whose body the C5/C6/C7 rivals replace.
_I_ENTRY_BODY = (
    "  let v := validateInput z false ref Form.sparseByRow\n"
    "  { refused := v.refused, warned := v.warned, refAfter := v.refAfter,\n"
    "    handedOn := v.carrier }")
_I_ENTRY = (
    "def scoreReport (ref : Reference) (z : InputData) : ScoreOutcome :=\n"
    + _I_ENTRY_BODY)
# The modeled entry point AS A PROGRAM: the node structure that makes what
# presenting one carrier COSTS readable off the program rather than reported in a
# field. A rival that moves score-time work moves these nodes.
_I_ENTRY_PROGRAM = (
    "def scoreEntry (ref : Reference) (z : InputData) : Scored :=\n"
    "  let r := scoreReport ref z\n"
    "  bif r.refused then Scored.done { r with returned := [] }\n"
    "    else Scored.traverse r.handedOn.values\n"
    "           (fun scores => Scored.done { r with returned := scores })")

# NOTE on what is NOT an anchor here. The traversal machinery (`Fitting`,
# `Fitting.result`, `Fitting.traversals`) lives in the frozen `pure` SPEC region,
# so no variant can touch it at all — `markers.same_spec` rejects the file. That
# is stronger than freezing a helper by anchor: the earlier model tallied
# traversals in an output FIELD threaded through an impl-region helper, and a
# rival could then report one traversal while performing two (measured: the
# work-shaped rivals below were provably indistinguishable from gold by ANY
# predicate over the returned record — `implementation_fit = <rival>` closed by
# `intro x c f; cases c <;> rfl`). Reading the traversals off the program's
# STRUCTURE removes the field a rival could write.

# The frozen proof's intro line — unique in the file — so the admissibility
# positive can prepend a ground `have` without touching the theorem STATEMENT.
_P_INTRO = "  intro xOrig contaminationAuto contamination"
# The frozen tactic body after that line, so a positive whose impl needs a
# different (still assumption-free) script can replace it. The theorem STATEMENT
# is untouched, which is what `variant_scope` requires.
_P_BODY = (
    "  -- what presenting a carrier to an estimator through the modeled entry point\n"
    "  -- reports, what it answers with, and what it costs, all read off the program\n"
    "  -- that entry point runs\n"
    "  have hout : ∀ (sc : Scoring) (ref : Reference) (z : InputData),\n"
    "      ((scoreEntry ref z).outcome sc).refused = (scoreReport ref z).refused\n"
    "      ∧ ((scoreEntry ref z).outcome sc).warned = (scoreReport ref z).warned\n"
    "      ∧ ((scoreEntry ref z).outcome sc).refAfter = (scoreReport ref z).refAfter\n"
    "      ∧ ((scoreEntry ref z).outcome sc).handedOn = (scoreReport ref z).handedOn\n"
    "      ∧ ((scoreEntry ref z).outcome sc).returned\n"
    "          = (bif (scoreReport ref z).refused then []\n"
    "             else sc (scoreReport ref z).handedOn.values)\n"
    "      ∧ (scoreEntry ref z).traversals sc\n"
    "          = (bif (scoreReport ref z).refused then []\n"
    "             else [(scoreReport ref z).handedOn.values]) := by\n"
    "    intro sc ref z\n"
    "    unfold scoreEntry\n"
    "    cases h : (scoreReport ref z).refused <;>\n"
    "      simp [Scored.outcome, Scored.traversals, h]\n"
    "  unfold problem_spec_fit implementation_fit\n"
    "  intro _hlvl hins hcon sc\n"
    "  cases contaminationAuto <;>\n"
    "    refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>\n"
    "    simp only [Bool.false_eq_true, if_false, if_true, Fitting.result,\n"
    "               Fitting.traversals, (hout sc _ _).1, (hout sc _ _).2.1,\n"
    "               (hout sc _ _).2.2.1, (hout sc _ _).2.2.2.1,\n"
    "               (hout sc _ _).2.2.2.2.2,\n"
    "               scoreReport, validateInput, unrecorded,\n"
    "               cond_true, cond_false, Bool.not_true,\n"
    "               Bool.false_and, hins, hcon] <;>\n"
    "    first\n"
    "      | rfl\n"
    "      | (intro z hc hw hn hi; simp [hi, hc, hw])\n"
    "      | (intro z; and_intros <;> intros <;>\n"
    "         first\n"
    "           | (clear hout; simp_all; done)\n"
    "           | (rw [(hout sc _ z).2.2.2.2.1]\n"
    "              simp [scoreReport, validateInput]))\n"
    "      | (intro h; first\n"
    "          | exact h.elim\n"
    "          | exact trivial\n"
    "          | exact bne_self_eq_false _\n"
    "          | exact absurd trivial h\n"
    "          | rfl\n"
    "          | (simp))")
for _a in (_I_VALIDATE, _I_RECORD, _I_TRAVERSE, _I_OFF, _I_RET, _I_AUTO_BRANCH,
           _I_AUTO_RET, _I_ELSE, _I_TAIL, _I_ENTRY_BODY, _I_ENTRY,
           _I_ENTRY_PROGRAM, _P_INTRO, _P_BODY):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"anchor drifted: {_a[:48]!r}")


# ---------------------------------------------------------------------------
# Witness scaffolds.
#
# The eight-clause spec is destructured positionally, so each scaffold names the
# conjunct it refutes and discards the rest:
#   C1 `warned`     -> `⟨hw, -, -, -, -, -, -, -⟩`
#   C2 `offset`     -> `⟨-, hclause, -, -, -, -, -, -⟩`   (unconfigured arm)
#   C3 `offset`     -> `⟨-, -, hclause, -, -, -, -, -⟩`   (configured arm)
#   C4 `reference`  -> `⟨-, -, -, href, -, -, -, -⟩`
#   C5 `scoreLater` -> `⟨-, -, -, -, hlater, -, -, -⟩`, then the conjunct within
#        (seven legs: refusal on width, diagnostic, durable record, the handed-on
#         CARRIER -- content, self-description and storage layout in one record
#         equation, so three rivals attack it -- refusal of a carrier whose labels
#         cannot be inspected, refusal of one whose content the check declines, and
#         the score-time TRAVERSAL RECORD: how many passes over the fitted model
#         presenting one carrier costs and over what payload, read off the
#         score-time program's structure rather than any field it reports)
#   C6 self-admission  -> `⟨-, -, -, -, -, hadm, -, -⟩`
#   C7 admission       -> `⟨-, -, -, -, -, -, hc7, -⟩`
#   C8 traversals      -> `⟨-, -, -, -, -, -, -, hp⟩`
#
# `_w_warned` refutes the TRANSPARENT clause C1 at literal inputs: the modeled
# validation helper's diagnostic flag reduces under `simp`, so no hypothesis is
# needed and none is stated.
#
# `_w_offset` refutes an OPAQUE value clause (C2 or C3). The clause is an
# implication, so the witness discharges its guard by `decide` and then
# contradicts the equality with a single conditioning hypothesis `h` naming the
# sub-domain where the rival is wrong. `arm` selects which implication arm to
# instantiate; `flip` orients the resulting equality against `h`.
#
# `_w_reference` / `_w_reference_width` refute C4 by PROJECTING the offending
# component of the record (its metadata status or its width) out of the clause's
# equation and deciding the resulting boolean/natural clash. The projection is
# what makes this route work: the record equation as a whole leaves a `do`-block
# residual that reduces on neither leg, so `simp` alone attributes nothing
# (measured — it fails against rival AND gold); `simp only` on the modeled step
# followed by `decide` on the projected component discriminates.
#
# `_w_later` refutes C5 by instantiating its quantifier at ONE probe carrier and
# selecting the violated conjunct. `field` names the component (`refused`,
# `warned`, `refAfter`, `inspect`) and `probe` is the carrier handed to the fitted
# estimator — a narrower one for the width components, a name-carrying one for
# the diagnostic, one whose labels the estimator cannot inspect for `inspect`
# (the fifth leg; that one probe is at the TRAINING width, so no width check can
# be what the leg is really measuring). C5's FOURTH leg (what a non-refused
# carrier is handed on) is
# not reachable that way: its two sides are applications of the OPAQUE
# re-presentation callee, so it gets its own conditioning scaffold,
# `_w_handed_on`, on the same pattern as the two offset witnesses.
# ---------------------------------------------------------------------------
# The interpretation of the scoring effect each witness instantiates the
# specification at. The spec holds for EVERY interpretation, so refuting it needs
# only ONE, and the identity is the one that keeps a witness's hypothesis about
# the smallest number of opaque terms: under it the anomaly scores of a payload
# ARE that payload, so a hypothesis that would otherwise have to name the scores
# of a payload names only `percentile`'s and `checked`'s values. Nothing in the battery depends on
# which interpretation is chosen — the choice is a witness's, not the spec's.
_SC = "(fun v => v)"


def _inp(values, n_features, has_names, form="Form.dense", inspectable="true",
         content="true"):
    return (f"{{ values := {values}, nFeatures := {n_features}, "
            f"hasFeatureNames := {has_names}, form := {form}, "
            f"namesInspectable := {inspectable}, "
            f"contentAdmissible := {content} }}")


# Every witness below discharges the obligation's THREE PRECONDITIONS before
# reaching any clause (the level one through `_lvl`, immediately below): `problem_spec_fit` claims nothing about a training carrier
# whose labels the estimator cannot inspect, and nothing about one whose content
# its admissibility check refuses, so a witness must exhibit a carrier that is
# both. The carriers `_inp` builds are inspectable and admissible, so each
# precondition is discharged by `decide` at the literal — and a witness that
# could not discharge them would be refuting a claim the spec never makes.
_PRE = "(by decide) (by decide)"


def _lvl(auto, contamination):
    """The LEVEL precondition, discharged at this witness's own literals.

    `problem_spec_fit` describes no run whose configured threshold level the
    estimator's parameter validation refuses: that validation is the first thing
    fitting does, ahead of any look at the carrier, and a level it refuses leaves
    nothing behind for any clause to describe. So a witness has to discharge it
    before it can reach a clause, and there are exactly two ways to. On the
    unconfigured lane the validation never looks at a level, so the precondition
    is discharged at the literal by `decide`. On the configured lane the verdict
    has to be ASSUMED for that witness's own level -- `levelAdmitted` is opaque,
    so nothing computes it -- exactly as a witness about the re-presentation
    callee assumes a fact about `checked`. Assumed is not unfounded: axiom_check.py's
    parameter-domain leg measures the real validation's verdict at EVERY level
    literal this battery assumes admitted, with levels outside the estimator's
    declared interval as the control that the measurement discriminates. A
    witness at a level the real validation REFUSES would be refuting a claim the
    obligation does not make, which is why no witness below stands at one.

    Returns (binder, argument): the binder, already space-prefixed, goes on the
    `example`; the argument goes into the application of the obligation.
    """
    if auto == "true":
        return "", "(fun h => absurd h (by decide))"
    return (f" (hla : levelAdmitted {contamination} = true)", "(fun _ => hla)")


# The unfolding set every witness reduces its projected component with. The two
# `Fitting` equations are what RUN the modeled program — `Fitting.result` walks it
# to the values it yields and `Fitting.traversals` reads off the payloads it
# traversed — so no witness can reach any observable without them.
_SIMP = ("implementation_fit, validateInput, scoreEntry, scoreReport,\n"
         "             unrecorded, Fitting.result, Fitting.traversals,\n"
         "             Scored.outcome, Scored.traversals, cond_true, cond_false,\n"
         "             Bool.not_false, Bool.not_true, Bool.true_and,\n"
         "             Bool.false_and")


def _w_warned(values, n_features, has_names, auto, contamination,
              form="Form.dense", layout_branch=False):
    """Refute C1, which carries NO antecedent — not the branch guard and not the
    storage-form guard C3 and C8 carry. `form` is therefore live here: a
    rival that misbehaves only on the carrier where fitting aborts is still
    refuted, at a witness presented in that storage form, which is what bounds
    the guard on C3/C8 to those two clauses.

    `layout_branch` says the rival BRANCHES on the layout the admissibility check
    hands on, so reducing its diagnostic at the literal carrier needs the two
    layout definitions unfolded as well; the other rivals never mention them and
    would only collect an unused-argument warning."""
    inp = _inp(values, n_features, has_names, form)
    lvlb, lvla = _lvl(auto, contamination)
    layout = ", Form.reshaped, Form.traversable" if layout_branch else ""
    return (
        f"example{lvlb} : ¬ problem_spec_fit {inp} {auto} {contamination}\n"
        f"    (implementation_fit {inp} {auto} {contamination}) := by\n"
        "  unfold problem_spec_fit\n"
        "  intro hsp\n"
        f"  obtain ⟨hw, -, -, -, -, -, -, -⟩ := hsp {lvla} {_PRE} {_SC}\n"
        "  simp [implementation_fit, validateInput, unrecorded,\n"
        f"        Fitting.result{layout}] at hw\n")


def _w_offset(hyp, values, n_features, has_names, auto, contamination, arm,
              flip=False, sc=_SC):
    """`sc` is the interpretation this witness instantiates the spec at. The
    identity serves for every rival whose offset is wrong as a FUNCTION OF THE
    SCORES; a rival that ignores the scores it was handed and recomputes from the
    payload AGREES with the spec under the identity and has to be separated by a
    non-identity interpretation (`uncounted-work-off-structure`).

    C3 carries TWO antecedents — the storage form on which fitting runs to a
    result (`fitCompletes`) and the branch guard — and the witness discharges both
    at its literal carrier, which is dense; C2 carries only the branch guard."""
    inp = _inp(values, n_features, has_names)
    lvlb, lvla = _lvl(auto, contamination)
    pat = {"auto": "⟨-, hclause, -, -, -, -, -, -⟩",
           "configured": "⟨-, -, hclause, -, -, -, -, -⟩"}[arm]
    guards = {"auto": "(by decide)",
              "configured": "(by decide) (by decide)"}[arm]
    return (
        f"example ({hyp}){lvlb} :\n"
        f"    ¬ problem_spec_fit {inp} {auto} {contamination}\n"
        f"      (implementation_fit {inp} {auto} {contamination}) := by\n"
        "  unfold problem_spec_fit\n"
        "  intro hsp\n"
        f"  obtain {pat} := hsp {lvla} {_PRE} {sc}\n"
        f"  have ho := hclause {guards}\n"
        "  simp [implementation_fit, validateInput, unrecorded,\n"
        "        Fitting.result] at ho\n"
        f"  exact h {'ho.symm' if flip else 'ho'}\n")


def _w_record(component, values, n_features, has_names, auto, contamination):
    """Refute C4 by projecting `component` (`nFeatures` / `hasFeatureNames`)."""
    inp = _inp(values, n_features, has_names)
    lvlb, lvla = _lvl(auto, contamination)
    return (
        f"example{lvlb} : ¬ problem_spec_fit {inp} {auto} {contamination}\n"
        f"    (implementation_fit {inp} {auto} {contamination}) := by\n"
        "  unfold problem_spec_fit\n"
        "  intro hsp\n"
        f"  obtain ⟨-, -, -, href, -, -, -, -⟩ := hsp {lvla} {_PRE} {_SC}\n"
        f"  have h2 := congrArg Reference.{component} href\n"
        f"  simp only [{_SIMP}] at h2\n"
        "  exact absurd h2 (by decide)\n")


def _w_reference(*a):
    return _w_record("hasFeatureNames", *a)


def _w_reference_width(*a):
    return _w_record("nFeatures", *a)


def _w_later(field, probe, values, n_features, has_names, auto, contamination):
    """Refute C5 at one probe carrier; `field` selects the violated conjunct.

    Four of C5's seven legs are one-directional obligations and their witnesses
    first APPLY the leg at the probe before contradicting the result: `refused`
    (a carrier of a disagreeing width MUST be turned away — the probe's width is
    chosen to disagree), `warned` (the diagnostic is pinned for a probe whose
    labels the estimator will INSPECT), `inspect` (a probe whose labels it will
    NOT inspect must be turned away — the probe is presented with that flag
    `false`) and `content` (a probe whose content the check refuses must be turned
    away — presented with THAT flag `false`). `refAfter` is an equality and is
    contradicted directly.
    """
    inp = _inp(values, n_features, has_names)
    lvlb, lvla = _lvl(auto, contamination)
    pat = {"refused": "⟨hL, -, -, -, -, -, -, -⟩",
           "warned": "⟨-, hL, -, -, -, -, -, -⟩",
           "refAfter": "⟨-, -, hL, -, -, -, -, -⟩",
           "inspect": "⟨-, -, -, -, hL, -, -, -⟩",
           "content": "⟨-, -, -, -, -, hL, -, -⟩"}[field]
    apply = ("  have hL := hL (by decide)\n"
             if field in ("refused", "warned", "inspect", "content") else "")
    return (
        f"example{lvlb} : ¬ problem_spec_fit {inp} {auto} {contamination}\n"
        f"    (implementation_fit {inp} {auto} {contamination}) := by\n"
        "  unfold problem_spec_fit\n"
        "  intro hsp\n"
        f"  obtain ⟨-, -, -, -, hlater, -, -, -⟩ := hsp {lvla} {_PRE} {_SC}\n"
        f"  obtain {pat} := hlater {probe}\n"
        + apply +
        f"  simp only [{_SIMP}] at hL\n"
        "  exact absurd hL (by decide)\n")


def _w_handed_on(hyp, values, n_features, has_names, auto, contamination,
                 probe_values):
    """Refute C5's handed-on leg: WHAT the entry point passes to the fitted model
    on a carrier it does not turn away.

    The leg is guarded by non-refusal, so the witness discharges that guard by
    `decide` at a probe of the training width and then contradicts the payload
    equality. The equality is over the OPAQUE re-presentation callee, so — like
    the two offset witnesses — it conditions on a single hypothesis naming the
    sub-domain where the rival is wrong: that re-presenting this payload is not
    the identity on it. That hypothesis is grounded rather than convenient, and
    `axiom_check.py` is where: its handed-on leg exhibits real payloads the
    admissibility check returns in a DIFFERENT content than it was given (a
    float64 column presented to a float32-typed check), and its negative control
    shows that reading the caller's own object as what gets handed on is refuted
    by the real callee rather than merely unproven.

    The leg pins the whole presentation and not only its content, so what the leg
    yields is an equation between two CARRIERS. This scaffold projects the content
    field out of it (`congrArg InputData.values`) rather than destructuring the
    record equality, which keeps the contradiction on exactly the field the
    hypothesis is about and leaves the presentation's self-description to
    `later-scoring-hands-on-caller-description`, whose rival is wrong on those
    fields and on no other.
    """
    inp = _inp(values, n_features, has_names)
    lvlb, lvla = _lvl(auto, contamination)
    probe = _inp(probe_values, n_features, "false")
    return (
        f"example ({hyp}){lvlb} :\n"
        f"    ¬ problem_spec_fit {inp} {auto} {contamination}\n"
        f"      (implementation_fit {inp} {auto} {contamination}) := by\n"
        "  unfold problem_spec_fit\n"
        "  intro hsp\n"
        f"  obtain ⟨-, -, -, -, hlater, -, -, -⟩ := hsp {lvla} {_PRE} {_SC}\n"
        f"  obtain ⟨-, -, -, hH, -, -, -, -⟩ := hlater {probe}\n"
        f"  simp only [{_SIMP}] at hH\n"
        "  exact h (congrArg InputData.values (hH (by decide))).symm\n")


def _w_handed_on_description(values, n_features, has_names, auto, contamination,
                             probe_values):
    """Refute C5's handed-on leg on the presentation's SELF-DESCRIPTION: what the
    entry point hands on describes itself as the estimator's own presentation, not
    as the caller's object.

    The companion of `_w_handed_on`, and deliberately its opposite in one respect:
    that scaffold has to condition on the opaque re-presentation callee, because
    the field it contradicts is the callee's result. This one contradicts the
    LABEL field, which no callee touches, so it is fully transparent — no
    hypothesis, and `decide` alone discharges both the non-refusal guard and the
    contradiction. Projecting one field out of the carrier equation (`congrArg`)
    is what keeps it that way: destructuring the record would drag the opaque
    content field into the goal for no gain.

    The probe therefore BEARS names and is presented at the training width to a
    fit on a nameless carrier, which is the one region where a name-bearing probe
    is admitted rather than turned away (C7's guard), so the leg's non-refusal
    guard is discharged rather than dodged.
    """
    inp = _inp(values, n_features, has_names)
    lvlb, lvla = _lvl(auto, contamination)
    probe = _inp(probe_values, n_features, "true")
    return (
        f"example{lvlb} : ¬ problem_spec_fit {inp} {auto} {contamination}\n"
        f"    (implementation_fit {inp} {auto} {contamination}) := by\n"
        "  unfold problem_spec_fit\n"
        "  intro hsp\n"
        f"  obtain ⟨-, -, -, -, hlater, -, -, -⟩ := hsp {lvla} {_PRE} {_SC}\n"
        f"  obtain ⟨-, -, -, hH, -, -, -, -⟩ := hlater {probe}\n"
        f"  simp only [{_SIMP}] at hH\n"
        "  exact absurd (congrArg InputData.hasFeatureNames (hH (by decide)))\n"
        "    (by decide)\n")


def _w_handed_on_form(values, n_features, has_names, auto, contamination,
                      probe_values, probe_form="Form.sparseByRow"):
    """Refute C5's handed-on leg on the presentation's STORAGE FORM: which of the
    estimator's two sparse layouts the crossing carrier is handed on in.

    The third scaffold on that leg, and transparent for the same reason as
    `_w_handed_on_description`: the layout field is not the opaque
    re-presentation callee's value but the check's own choice of accepted layout,
    so `decide` discharges the non-refusal guard and the contradiction alike, with
    no conditioning hypothesis. The probe is therefore presented SPARSE — a dense
    probe crosses dense whatever layout a check accepts, so it would attribute
    nothing — at the training width and nameless, so the leg's guard is discharged
    rather than dodged and no name comparison can arise. Which sparse layout the
    probe ARRIVES in is a parameter and is not what the leg turns on: a check
    hands sparse content back in the layout it accepts whichever sparse layout it
    was given, so both settings of `probe_form` discriminate, and the case below
    exercises the one where arrival and requirement already agree, so that the
    rival cannot be read as merely failing to convert.
    """
    inp = _inp(values, n_features, has_names)
    probe = _inp(probe_values, n_features, "false", form=probe_form)
    lvlb, lvla = _lvl(auto, contamination)
    return (
        f"example{lvlb} : ¬ problem_spec_fit {inp} {auto} {contamination}\n"
        f"    (implementation_fit {inp} {auto} {contamination}) := by\n"
        "  unfold problem_spec_fit\n"
        "  intro hsp\n"
        f"  obtain ⟨-, -, -, -, hlater, -, -, -⟩ := hsp {lvla} {_PRE} {_SC}\n"
        f"  obtain ⟨-, -, -, hH, -, -, -, -⟩ := hlater {probe}\n"
        f"  simp only [{_SIMP}] at hH\n"
        "  exact absurd (congrArg InputData.form (hH (by decide)))\n"
        "    (by decide)\n")


def _w_admits(values, n_features, has_names, auto, contamination):
    """Refute C6: a nameless training carrier stays admissible to its own fit.

    Instantiated by the rival that satisfies C5's one-directional `refused` leg
    VACUOUSLY by turning every carrier away. C5 alone cannot catch it — refusing
    everything satisfies a one-directional obligation — so C6 is what makes that
    weakening safe, and this scaffold is what shows C6 load-bearing. C6 is itself
    guarded (`xOrig.hasFeatureNames = false`), because a NAMED training carrier
    handed back to its own fit meets a name comparison this model cannot see; the
    witness therefore discharges that guard at a nameless carrier, by `rfl`.
    """
    inp = _inp(values, n_features, has_names)
    lvlb, lvla = _lvl(auto, contamination)
    return (
        f"example{lvlb} : ¬ problem_spec_fit {inp} {auto} {contamination}\n"
        f"    (implementation_fit {inp} {auto} {contamination}) := by\n"
        "  unfold problem_spec_fit\n"
        "  intro hsp\n"
        f"  obtain ⟨-, -, -, -, -, hadm, -, -⟩ := hsp {lvla} {_PRE} {_SC}\n"
        "  have h := hadm rfl\n"
        f"  simp only [{_SIMP}] at h\n"
        "  exact absurd h (by decide)\n")


def _w_names_not_refusal(values, n_features, has_names, auto, contamination):
    """Refute C7: absent feature-name metadata is never a ground for refusal.

    Instantiated by the rival whose extra refusal predicate is feature-name
    disagreement. That predicate vanishes at `xOrig`, so C6 cannot reach it, and
    it only refuses more than C5 obliges, so C5 cannot either. The witness
    presents a carrier of the SAME width which bears NO names, so no name
    comparison can arise — which is exactly the region C7 claims.

    The probe's payload is an ORDINARY one, not one pinned to the fixed point of
    the re-presentation callee: C7 covers content the check rewrites on the same
    terms as content it leaves as it finds it, so the region is reached without
    saying anything about what the callee returns.
    """
    inp = _inp(values, n_features, has_names)
    lvlb, lvla = _lvl(auto, contamination)
    z = ("{ values := [9.5], nFeatures := " + n_features
         + ", hasFeatureNames := false, form := Form.dense, "
         + "namesInspectable := true, contentAdmissible := true }")
    # C7's four antecedents at this probe: its content is one the check accepts
    # (`rfl`), its width is the training width (`rfl`), the disjunction "the
    # estimator holds no names OR the carrier brings none" is supplied by the
    # right-hand disjunct, and the estimator will INSPECT this carrier's labels —
    # each discharged at the literal, and none of them a claim about content the
    # check has already converted.
    return (
        f"example{lvlb} : ¬ problem_spec_fit {inp} {auto} {contamination}\n"
        f"    (implementation_fit {inp} {auto} {contamination}) := by\n"
        "  unfold problem_spec_fit\n"
        "  intro hsp\n"
        f"  obtain ⟨-, -, -, -, -, -, hc7, -⟩ := hsp {lvla} {_PRE} {_SC}\n"
        f"  have h := hc7 {z} rfl rfl (Or.inr rfl) rfl\n"
        f"  simp only [{_SIMP}] at h\n"
        "  exact absurd h (by decide)\n")


def _w_rewritten_content_admitted(hyp, values, n_features, has_names, auto,
                                  contamination, probe_values):
    """Refute C7 on its CONTENT region: content the admissibility check accepts
    and REWRITES is admitted on the same terms as content it accepts and leaves
    as it finds it.

    Instantiated by the rival whose extra refusal predicate is "the check did not
    hand this content back unchanged". That predicate is invisible to C5's
    one-directional `refused` leg (it only refuses MORE), invisible to C6 (fitting
    already re-presented the training carrier, so it is a fixed point of the
    callee there) and invisible to every clause about the fit itself. C7 is what
    states the behavior, and it can only state it if its region is NOT restricted
    to the callee's fixed points — which is why the antecedent naming those fixed
    points is not there.

    The probe's payload is an ordinary one, so the region is reached without any
    claim about the callee. The witness then conditions on ONE hypothesis, about
    that one payload: the check does not hand it back as it found it. That is the
    sub-domain where the rival is wrong, and it is grounded rather than
    convenient — `axiom_check.py`'s handed-on leg exhibits real payloads the check
    returns in a different content than it was given (a float64 column presented
    to a float32-typed check), with the already-converted control showing the
    disequality is a measured property of the callee and not an assumption about
    it.

    TACTIC ROUTE, and why it is not the one the other C7 witness uses. This
    rival's refusal predicate mentions the OPAQUE re-presentation callee, so the
    `decide` route is unavailable: the kernel cannot evaluate `checked [9.5]` and
    a `decide` would be stuck rather than deciding, which attests to nothing. The
    route here takes the clause's conclusion AT the probe and reduces it with the
    rival's own definitions, then closes on the hypothesis: the reduced claim is
    that the rival's refusal at this probe is `false`, and the hypothesis says the
    Boolean it is is `true`. Discrimination was measured on the shipped bytes:
    against the RIVAL the witness elaborates (its own proof obligation aside),
    while against the frozen solution it FAILS — gold's refusal at this probe
    reduces to the literal `false`, so the hypothesis has nothing to contradict
    and the goal is left open. The shared `simp only` set is deliberately not used
    to reduce here: it does not rewrite the branch selector the fitting program is
    chosen by, so it would leave the clause unreduced and the hypothesis
    unusable.
    """
    inp = _inp(values, n_features, has_names)
    lvlb, lvla = _lvl(auto, contamination)
    z = ("{ values := " + probe_values + ", nFeatures := " + n_features
         + ", hasFeatureNames := false, form := Form.dense, "
         + "namesInspectable := true, contentAdmissible := true }")
    # The hypothesis names the Bool-valued disequality this rival refuses on;
    # everything left of its FINAL `=` is that term (`!=` contains an `=`, so a
    # left split would truncate it).
    lhs = hyp.split(":", 1)[1].rsplit("=", 1)[0].strip()
    return (
        f"example ({hyp}){lvlb} :\n"
        f"    ¬ problem_spec_fit {inp} {auto} {contamination}\n"
        f"      (implementation_fit {inp} {auto} {contamination}) := by\n"
        "  unfold problem_spec_fit\n"
        "  intro hsp\n"
        f"  obtain ⟨-, -, -, -, -, -, hc7, -⟩ := hsp {lvla} {_PRE} {_SC}\n"
        f"  have hb := hc7 {z} rfl rfl (Or.inr rfl) rfl\n"
        "  simp [implementation_fit, validateInput, scoreEntry, scoreReport,\n"
        "        unrecorded, Fitting.result, Scored.outcome, h] at hb\n")


def _w_score_traversals(values, n_features, has_names, auto, contamination,
                        probe_names="false", probe_inspect="true",
                        probe_content="true", probe_width=None,
                        probe_values="[9.5]", hyp=None):
    """Refute C5's SEVENTH leg: how many traversals of the fitted model presenting
    ONE carrier to the fitted estimator spends, and over what.

    Instantiated by the rivals that move SCORE-TIME work rather than score-time
    values — a warm-up pass before the real one, a pass spent before the carrier
    is even judged, a pass spent on a carrier that is then turned away, or no pass
    at all on one that is accepted. Every clause over what the call REPORTS is
    blind to all of them: the report is the same value in each case. The
    traversals are read off the score-time program's STRUCTURE
    (`Scored.traversals`, in the frozen spec region), so this is the one
    refutation such a rival cannot dodge by reporting a number other than the one
    it performs — there is no field to write.

    With no `hyp`, the witness projects the LENGTH out of the leg's list equation
    and decides the resulting clash, which is the route for a rival that spends
    the wrong NUMBER of traversals; it conditions on nothing, because a length is
    a natural number `decide` can reach whatever the payloads are. `hyp` selects
    the other
    route, for a rival that spends the right number of traversals over the WRONG
    payload: there the leg's two sides are both about the OPAQUE re-presentation
    callee's value, so — like the two offset witnesses and the handed-on one — the
    witness conditions on a single hypothesis naming the sub-domain where the
    rival is wrong, and `axiom_check.py`'s handed-on leg is where that
    disequality is measured against the real callee rather than assumed.

    The probe defaults to the training width, nameless, inspectable and
    admissible — the region where the entry point accepts, so the leg's
    accepting lane is what is measured. Setting `probe_width` to a disagreeing
    width, or `probe_inspect`/`probe_content` to `false`, moves the measurement
    onto the REFUSING lane, where the leg pins no traversal at all: that is what
    refutes a rival that pays for a carrier it turns away.
    """
    inp = _inp(values, n_features, has_names)
    lvlb, lvla = _lvl(auto, contamination)
    w = n_features if probe_width is None else probe_width
    probe = _inp(probe_values, w, probe_names, inspectable=probe_inspect,
                 content=probe_content)
    if hyp:
        # right NUMBER of traversals, wrong PAYLOAD: both sides of the leg are
        # about the opaque re-presentation callee, so the witness projects the
        # traversed payload out of the list equation and contradicts `hyp`.
        header = (f"example ({hyp}){lvlb} :\n"
                  f"    ¬ problem_spec_fit {inp} {auto} {contamination}\n"
                  f"      (implementation_fit {inp} {auto} {contamination}) := by\n")
        tail = ("  have hpay := hL\n"
                "  simp [implementation_fit, validateInput, scoreEntry, scoreReport,\n"
                "        unrecorded, Fitting.result, Scored.outcome,\n"
                "        Scored.traversals] at hpay\n"
                "  exact h hpay\n")
    else:
        header = (f"example{lvlb} : ¬ problem_spec_fit {inp} {auto} {contamination}\n"
                  f"    (implementation_fit {inp} {auto} {contamination}) := by\n")
        tail = ("  have hlen := congrArg List.length hL\n"
                f"  simp only [{_SIMP}, List.length_cons, List.length_nil] at hlen\n"
                "  exact absurd hlen (by decide)\n")
    return (
        header +
        "  unfold problem_spec_fit\n"
        "  intro hsp\n"
        f"  obtain ⟨-, -, -, -, hlater, -, -, -⟩ := hsp {lvla} {_PRE} {_SC}\n"
        f"  obtain ⟨-, -, -, -, -, -, hL, -⟩ := hlater {probe}\n"
        + tail)


def _w_traversals(values, n_features, has_names, auto, contamination):
    """Refute C8: which payloads fitting traverses, and how many times.

    Instantiated by the rivals that move WORK rather than VALUES — a traversal
    hoisted above the branch, or an extra discarded one — which every clause over
    the returned values is blind to. The traversals are read off the PROGRAM's
    structure, so this is the one refutation a rival cannot dodge by reporting a
    different number than it performs.

    C8 is asked of the carriers on which fitting runs to a result, so the witness
    discharges that antecedent (`fitCompletes`, decided at its dense literal
    carrier) before projecting the length. A rival that spends its extra traversal
    on a SPARSE carrier with a configured threshold is therefore not refuted here,
    and deliberately: that run produces nothing to count (see the module header,
    "WHERE THE DESCRIPTION STOPS").
    """
    inp = _inp(values, n_features, has_names)
    lvlb, lvla = _lvl(auto, contamination)
    return (
        f"example{lvlb} : ¬ problem_spec_fit {inp} {auto} {contamination}\n"
        f"    (implementation_fit {inp} {auto} {contamination}) := by\n"
        "  unfold problem_spec_fit\n"
        "  intro hsp\n"
        f"  obtain ⟨-, -, -, -, -, -, -, hp⟩ := hsp {lvla} {_PRE} {_SC}\n"
        "  have hlen := congrArg List.length (hp (by decide))\n"
        f"  simp only [{_SIMP}, List.length_cons, List.length_nil] at hlen\n"
        "  exact absurd hlen (by decide)\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG on the impl's shape. Each keeps the
    # `theorem correct_fit` statement byte-identical AND its frozen tactic body
    # verbatim (each reshape is definitionally the frozen computation, so the
    # frozen script still closes: no proof authoring, no helper lemma, no new
    # assumption). All four verified with real builds during authoring.
    # =====================================================================
    {
        "id": "pos-derive-before-select",
        "kind": "soundness",
        "expect": "verify",
        # Statement-ORDER reshape (the direct analogue of the nagini positive,
        # which moved the state-recording statement after the scoring call):
        # derive the data-driven threshold FIRST, then select which of the two
        # thresholds to return. Still exactly one validation of the training
        # data, so still no consistency diagnostic and still the same record.
        "module": _swap(
            _BASE, _I_TAIL,
            "  -- build the threshold's DERIVATION before selecting the threshold: the\n"
            "  -- continuation that turns the model's anomaly scores of the\n"
            "  -- (already-checked) training data into the configured percentile is\n"
            "  -- written down first, and the branch then decides whether to run it.\n"
            "  -- Writing it down costs no traversal of the fitted model; only running\n"
            "  -- it does, so the work is unchanged as well as the values.\n"
            "  let derive : List Float → Fitting := fun scores =>\n"
            "    Fitting.done { offset := percentile scores (100.0 * contamination),\n"
            "                   warned := false, reference := ref,\n"
            "                   scoreLater := scoreEntry ref }\n"
            "  if contaminationAuto then\n"
            "    Fitting.done { offset := -0.5, warned := false, reference := ref,\n"
            "                   scoreLater := scoreEntry ref }\n"
            "  else\n"
            "    Fitting.traverse x.values derive"),
        "rationale": "DEFENDS correct_fit. Statement-order reshape: the "
                     "data-driven threshold is derived before the branch instead "
                     "of inside it, then the branch selects. Values are "
                     "unchanged on the whole domain — C1 still holds (still "
                     "exactly one validation of the training data, so no "
                     "consistency diagnostic), C2 still returns the constant in "
                     "the unconfigured case, C3 still returns the configured "
                     "percentile of the training scores, and C4/C5 are untouched "
                     "(the record is still the one the single reset established "
                     "and the entry point is unchanged) — so a correct reshape "
                     "MUST verify, else SPEC-TOO-STRONG on statement order. "
                     "Frozen tactic body retained verbatim; statement "
                     "byte-identical; nothing assumed. Ports the nagini "
                     "positive control (there: perform the state recording "
                     "AFTER the scoring call — the same 'reorder the statements "
                     "around the scoring step' argument).",
    },
    {
        "id": "pos-negated-branch",
        "kind": "soundness",
        "expect": "verify",
        # Control-flow reshape: test the CONFIGURED case first (negated guard)
        # and fall through to the constant, inverting the branch structure.
        "module": _swap(
            _swap(_BASE, _I_TAIL,
            "  if !contaminationAuto then\n"
            "    -- threshold level configured: one traversal of the fitted model over\n"
            "    -- the (already-checked) training data, WITHOUT a second\n"
            "    -- admissibility pass — so no consistency warning is emitted and the\n"
            "    -- record established from the training carrier stands.\n"
            "    Fitting.traverse x.values fun scores =>\n"
            "      let off := percentile scores (100.0 * contamination)\n"
            "      Fitting.done { offset := off, warned := false, reference := ref,\n"
            "                     scoreLater := scoreEntry ref }\n"
            "  else\n"
            "    -- 0.5 plays a special role; we take the opposite, and the constant\n"
            "    -- needs no traversal of the fitted model\n"
            "    Fitting.done { offset := -0.5, warned := false, reference := ref,\n"
            "                   scoreLater := scoreEntry ref }"),
            # The negated guard puts `!contaminationAuto` where the frozen impl has
            # the bare binder, so the branch selector needs one more Boolean
            # normalization step than the frozen script asks for. `variant_scope`
            # permits reproving: the theorem STATEMENT is byte-identical, the added
            # simp lemma is a library `Bool` identity, and no axiom, theorem, lemma
            # or `sorry` is introduced.
            _P_BODY,
            _P_BODY.replace(
                "               cond_true, cond_false, Bool.not_true,",
                "               cond_true, cond_false, Bool.not_false, Bool.not_true,")),
        "rationale": "DEFENDS correct_fit. Branch-structure reshape: the guard is "
                     "negated so the configured case is tested first and the "
                     "unconfigured constant is the fall-through. Identical "
                     "values, different control flow, so all eight clauses still "
                     "hold and a faithful reshape MUST verify, else "
                     "SPEC-TOO-STRONG on branch polarity. Frozen tactic body "
                     "retained verbatim; statement byte-identical; nothing "
                     "assumed.",
    },
    {
        "id": "pos-single-expression",
        "kind": "soundness",
        "expect": "verify",
        # Shape reshape: no early return at all — one return of a conditional
        # expression, with the score derivation inlined into it.
        "module": _swap(
            _BASE, _I_TAIL,
            "  -- one exit: a single conditional expression selects the whole program.\n"
            "  -- The constant arm is a finished program; the data-driven arm is one\n"
            "  -- traversal of the fitted model over the (already-checked) training\n"
            "  -- data, WITHOUT a second admissibility pass, followed by the\n"
            "  -- configured percentile of the scores it yields — so no consistency\n"
            "  -- warning is emitted and the record from the training carrier stands.\n"
            "  bif contaminationAuto then\n"
            "    Fitting.done { offset := -0.5, warned := false, reference := ref,\n"
            "                   scoreLater := scoreEntry ref }\n"
            "  else\n"
            "    Fitting.traverse x.values fun scores =>\n"
            "      Fitting.done { offset := percentile scores (100.0 * contamination),\n"
            "                     warned := false, reference := ref,\n"
            "                     scoreLater := scoreEntry ref }"),
        "rationale": "DEFENDS correct_fit. Single-exit reshape: the early return "
                     "is removed and the threshold is selected inside one "
                     "conditional expression, with the score derivation inlined. "
                     "Same value on every input, so all eight clauses still hold "
                     "and a correct reshape MUST verify, else SPEC-TOO-STRONG on "
                     "the early-return shape. Frozen tactic body retained "
                     "verbatim; statement byte-identical; nothing assumed.",
    },
    {
        "id": "pos-record-from-normalized-carrier",
        "kind": "soundness",
        "expect": "verify",
        # DEFENDS C4 against over-fitting. The record is spelled out from the
        # training carrier's own width and metadata status rather than read off
        # the validation step's output. Normalization changes only the metadata
        # flag, so the width is the same either way and the described record is
        # the same value — a correct impl that does not route the description
        # through the helper's return.
        "module": _swap(
            _BASE, _I_RECORD,
            "  let v0 := validateInput xOrig true unrecorded Form.sparseByColumn\n"
            "  let x := v0.carrier\n"
            "  -- describe the admissible input from the training carrier's own width\n"
            "  -- and metadata status, spelled out rather than read off the\n"
            "  -- validation step's own output\n"
            "  let ref : Reference :=\n"
            "    { nFeatures := x.nFeatures, hasFeatureNames := xOrig.hasFeatureNames }"),
        "rationale": "DEFENDS correct_fit, and specifically defends C4/C5 against "
                     "being read as a restatement of one particular way of "
                     "obtaining the record. This impl describes the admissible "
                     "input directly from the training carrier's fields instead "
                     "of taking the validation step's returned description; "
                     "normalization touches only the metadata flag, so the width "
                     "agrees and the described record is the SAME value on every "
                     "input. Every clause holds, so it MUST verify — else C4 "
                     "would be SPEC-TOO-STRONG on the provenance of the record "
                     "rather than on its content, which is exactly the over-fit "
                     "an added clause must avoid. ADDED with C4/C5: an added "
                     "clause needs its own soundness control, or nothing "
                     "distinguishes pinning the behavior from pinning the frozen "
                     "impl's spelling of it. Frozen tactic body retained "
                     "verbatim; statement byte-identical; nothing assumed.",
    },
    {
        "id": "pos-name-identity-refusal",
        "kind": "soundness",
        "expect": "verify",
        # THE SOUNDNESS CONTROL FOR C6/C7's GUARDS, and the reason those guards
        # are shaped the way they are. The real estimator refuses a carrier whose
        # feature NAMES disagree with the recorded ones, and this model records
        # only whether names are present, never which — so a faithful impl may
        # refuse a carrier that bears names when the record holds names, and the
        # spec must not forbid it. This impl does exactly that: it refuses
        # conservatively whenever both sides carry names. It is the real
        # post-patch behavior at the one point the model cannot resolve, so it
        # MUST verify; if it did not, C6/C7 would be OVER-STRENGTH — asserting
        # admission where the real code raises. Note what it must still respect:
        # it refuses only where a name comparison can ARISE, so C7's region
        # (either side nameless) is untouched.
        #
        # The impl needs a different tactic script — the extra disjunct does not
        # reduce under the frozen `first` alternatives — which `variant_scope`
        # permits (the theorem STATEMENT is byte-identical, the body may reprove).
        # Nothing is assumed: no new axiom, theorem, lemma or `sorry`.
        "module": _swap(
            _swap(_BASE, _I_ENTRY_BODY,
                  "  let v := validateInput z false ref Form.sparseByRow\n"
                  "  -- a name-IDENTITY comparison can arise only when the record holds\n"
                  "  -- names AND the carrier brings names of its own; where it can, the\n"
                  "  -- two may disagree and the real estimator turns the carrier away,\n"
                  "  -- so this impl refuses there conservatively.\n"
                  "  { refused := v.refused || (z.hasFeatureNames && ref.hasFeatureNames),\n"
                  "    warned := v.warned, refAfter := v.refAfter,\n"
                  "    handedOn := v.carrier }"),
            _P_BODY,
            "  -- what presenting a carrier to an estimator through the modeled entry\n"
            "  -- point reports, and what it costs, both read off the program it runs\n"
            "  have hout : ∀ (sc : Scoring) (ref : Reference) (z : InputData),\n"
            "      ((scoreEntry ref z).outcome sc).refused = (scoreReport ref z).refused\n"
            "      ∧ ((scoreEntry ref z).outcome sc).warned = (scoreReport ref z).warned\n"
            "      ∧ ((scoreEntry ref z).outcome sc).refAfter\n"
            "          = (scoreReport ref z).refAfter\n"
            "      ∧ ((scoreEntry ref z).outcome sc).handedOn\n"
            "          = (scoreReport ref z).handedOn\n"
            "      ∧ ((scoreEntry ref z).outcome sc).returned\n"
            "          = (bif (scoreReport ref z).refused then []\n"
            "             else sc (scoreReport ref z).handedOn.values)\n"
            "      ∧ (scoreEntry ref z).traversals sc\n"
            "          = (bif (scoreReport ref z).refused then []\n"
            "             else [(scoreReport ref z).handedOn.values]) := by\n"
            "    intro sc ref z\n"
            "    unfold scoreEntry\n"
            "    cases h : (scoreReport ref z).refused <;>\n"
            "      simp [Scored.outcome, Scored.traversals, h]\n"
            "  unfold problem_spec_fit implementation_fit\n"
            "  intro _hlvl hins hcon sc\n"
            "  cases contaminationAuto <;>\n"
            "    refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>\n"
            "    simp only [Bool.false_eq_true, if_false, if_true, Fitting.result,\n"
            "               Fitting.traversals, (hout sc _ _).1, (hout sc _ _).2.1,\n"
            "                 (hout sc _ _).2.2.1, (hout sc _ _).2.2.2.1,\n"
            "                 (hout sc _ _).2.2.2.2.2,\n"
            "               scoreReport, validateInput, unrecorded,\n"
            "               cond_true, cond_false, Bool.not_false, Bool.not_true,\n"
            "               Bool.true_and, Bool.false_and, hins, hcon] <;>\n"
            "    first\n"
            "      | rfl\n"
            "      | (intro z hc hw hn hi;\n"
            "         rcases hn with hn | hn <;>\n"
            "           simp [hc, hw, hn, hi])\n"
            "      | (intro z; and_intros <;> intros <;>\n"
            "         first\n"
            "           | (clear hout; simp_all; done)\n"
            "           | (rw [(hout sc _ z).2.2.2.2.1]\n"
            "              simp [scoreReport, validateInput]))\n"
            "      | (intro h; first\n"
            "          | exact h.elim\n"
            "          | exact trivial\n"
            "          | (simp [h])\n"
            "          | exact absurd trivial h\n"
            "          | rfl\n"
            "          | (simp))"),
        "rationale": "DEFENDS correct_fit against the OVER-STRENGTH reading of "
                     "C6/C7. `InputData.hasFeatureNames` carries name PRESENCE "
                     "only, so two carriers differing just in their column labels "
                     "share one image here, while the real "
                     "`BaseEstimator._check_feature_names` raises on a label "
                     "DISAGREEMENT — measured against the real post-patch code: a "
                     "fit on a frame with columns [a, b, c] then scored with "
                     "permuted names, or with [f0, f1, XX], RAISES. An admission "
                     "obligation covering named-vs-named carriers would therefore "
                     "assert `refused = false` where the real code raises, which is "
                     "why C6 is guarded by `xOrig.hasFeatureNames = false` and C7's "
                     "third antecedent is the disjunction `xOrig.hasFeatureNames = "
                     "false ∨ z.hasFeatureNames = false`. This impl is the faithful "
                     "behavior at the boundary — refuse conservatively wherever a "
                     "name comparison can arise, warn and carry on wherever it "
                     "cannot — and it MUST verify. It also fixes the weakening's "
                     "cost precisely: the impl still refuses nothing in C7's "
                     "region, so `names-treated-as-inadmissibility` (which refuses "
                     "a NAMELESS carrier) is still rejected, and "
                     "`later-scoring-refuses-everything` still fails C6. Statement "
                     "byte-identical; tactic body reproved without assuming "
                     "anything.",
    },

    {
        "id": "pos-sparse-declines-threshold",
        "kind": "soundness",
        "expect": "verify",
        # THE SOUNDNESS CONTROL FOR THE STORAGE-FORM GUARD on C3 and C8, and the
        # reason those two clauses are guarded rather than unconditional. The
        # fit-time admissibility check ADMITS a sparse carrier and hands it back
        # still sparse; the scoring path fitting itself uses performs no
        # admissibility pass of its own, so it never converts that form and cannot
        # traverse it. A sparse carrier with a configured threshold level
        # therefore produces NO threshold in the real post-patch code — it raises
        # — and this impl is the faithful counterpart at that point: it declines
        # to invent one. It MUST verify; if it did not, C3/C8 would be
        # OVER-STRENGTH, asserting a threshold and a traversal for a run that does
        # not happen. Note what it must still respect: it declines only where the
        # storage form makes the traversal impossible, so the dense region of C3
        # and C8 is untouched — which is what `sparse-guard-inverted` below is the
        # reject-lane control for.
        #
        # Like the name-identity positive it needs its own tactic script (the
        # frozen `first` alternatives do not case on the storage form), which
        # `variant_scope` permits: the theorem STATEMENT is byte-identical, no new
        # axiom/theorem/lemma, no `sorry`.
        "module": _swap(
            _swap(_BASE, _I_ELSE,
                  "  else if !(Form.reshaped xOrig.form Form.sparseByColumn).traversable then\n"
                  "    -- the check hands sparse content back sparse and the scoring path\n"
                  "    -- fitting uses cannot traverse content in that form, so this run\n"
                  "    -- reaches no threshold at all; decline to invent one\n"
                  "    Fitting.done { offset := 0.0, warned := false, reference := ref,\n"
                  "                   scoreLater := scoreEntry ref }\n"
                  + _I_ELSE),
            _P_BODY,
            "  obtain ⟨v, n, hnm, sp, ins, con⟩ := xOrig\n"
            "  -- what presenting a carrier to an estimator through the modeled entry\n"
            "  -- point reports, and what it costs, both read off the program it runs\n"
            "  have hout : ∀ (sc : Scoring) (ref : Reference) (z : InputData),\n"
            "      ((scoreEntry ref z).outcome sc).refused = (scoreReport ref z).refused\n"
            "      ∧ ((scoreEntry ref z).outcome sc).warned = (scoreReport ref z).warned\n"
            "      ∧ ((scoreEntry ref z).outcome sc).refAfter\n"
            "          = (scoreReport ref z).refAfter\n"
            "      ∧ ((scoreEntry ref z).outcome sc).handedOn\n"
            "          = (scoreReport ref z).handedOn\n"
            "      ∧ ((scoreEntry ref z).outcome sc).returned\n"
            "          = (bif (scoreReport ref z).refused then []\n"
            "             else sc (scoreReport ref z).handedOn.values)\n"
            "      ∧ (scoreEntry ref z).traversals sc\n"
            "          = (bif (scoreReport ref z).refused then []\n"
            "             else [(scoreReport ref z).handedOn.values]) := by\n"
            "    intro sc ref z\n"
            "    unfold scoreEntry\n"
            "    cases h : (scoreReport ref z).refused <;>\n"
            "      simp [Scored.outcome, Scored.traversals, h]\n"
            "  unfold problem_spec_fit implementation_fit\n"
            "  intro _hlvl hins hcon sc\n"
            "  -- the preconditions, restated on the destructured fields they are about\n"
            "  have hi0 : ins = true := hins\n"
            "  have hc0 : con = true := hcon\n"
            "  cases contaminationAuto <;> cases sp <;>\n"
            "    refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>\n"
            "    simp only [fitCompletes, Form.reshaped, Form.traversable,\n"
            "               Bool.false_eq_true, if_false, if_true,\n"
            "               Fitting.result, Fitting.traversals,\n"
            "               (hout sc _ _).1, (hout sc _ _).2.1,\n"
            "                 (hout sc _ _).2.2.1, (hout sc _ _).2.2.2.1,\n"
            "                 (hout sc _ _).2.2.2.2.2, scoreReport,\n"
            "               validateInput, unrecorded, cond_true, cond_false,\n"
            "               Bool.not_false, Bool.not_true, Bool.true_and,\n"
            "               Bool.false_and, Bool.or_false, reduceCtorEq,\n"
            "               hi0, hc0] <;>\n"
            "    first\n"
            "      | rfl\n"
            "      | (intro z hc hw hn hi; simp [hi, hc, hw])\n"
            "      | (intro z; and_intros <;> intros <;>\n"
            "         first\n"
            "           | (clear hout; simp_all; done)\n"
            "           | (rw [(hout sc _ z).2.2.2.2.1]\n"
            "              simp [scoreReport, validateInput]))\n"
            "      | (intro h; first\n"
            "          | exact h.elim\n"
            "          | exact trivial\n"
            "          | exact bne_self_eq_false _\n"
            "          | exact absurd trivial h\n"
            "          | exact absurd h (by decide)\n"
            "          | rfl\n"
            "          | (simp))"),
        "rationale": "DEFENDS correct_fit against the OVER-STRENGTH reading of C3 "
                     "and C8 on the storage form of the training carrier. "
                     "`InputData.form` is carried because the forms are "
                     "not interchangeable to the fitted model: the fit-time check "
                     "admits sparse content and returns it sparse, and the "
                     "non-validating scoring path fitting uses afterwards cannot "
                     "consume that form — measured against the real patched "
                     "callee, where a sparse carrier with a configured threshold "
                     "level raises out of the tree traversal while the dense "
                     "carrier of the same numeric content completes (axiom_check.py "
                     "leg S and its dense control; conformance_check.py's "
                     "real-code leg). A threshold obligation covering that carrier "
                     "would assert an offset and one traversal where the real code "
                     "produces neither, so C3 and C8 are asked only where fitting "
                     "runs to a result (`fitCompletes`). This impl is the faithful "
                     "behavior at that boundary — decline the threshold exactly "
                     "where the traversal is impossible, derive it everywhere else "
                     "— and it MUST verify. It also bounds the weakening's cost "
                     "precisely: it keeps the frozen configured branch verbatim "
                     "for every dense carrier, so C3's and C8's dense content is "
                     "unaffected, and it still satisfies C1, C2, C4, C5, C6 and C7 "
                     "on both storage forms. Statement byte-identical; nothing "
                     "assumed.",
    },

    {
        "id": "pos-declines-refused-level",
        "kind": "soundness",
        "expect": "verify",
        # THE SOUNDNESS CONTROL FOR THE LEVEL PRECONDITION, and the reason the
        # obligation carries one at all. `contamination` is a bare `Float` here,
        # but the real estimator DECLARES that parameter's domain and validates it
        # as the first statement of fitting, before it looks at a carrier at all:
        # a level outside the declared interval raises there, so such a run
        # reaches no threshold, no record and no traversal for any clause to
        # describe (measured on the real patched callee at levels either side of
        # the boundary, and at every level this battery assumes admitted:
        # axiom_check.py's parameter-domain leg). This impl is the faithful
        # counterpart at that point -- it declines exactly where the validation
        # refuses the level, and keeps the frozen derivation verbatim everywhere
        # else -- so it MUST verify. If it did not, the description would be
        # asserting a threshold and a traversal for a run the real code never
        # performs, which is SPEC-TOO-STRONG on the parameter domain.
        #
        # It is also what makes the precondition load-bearing rather than
        # decorative: the configured branch cannot be closed without APPLYING it
        # (`hlvl rfl`), and against a description carrying no such precondition
        # this impl is REFUTED rather than merely unprovable -- measured during
        # authoring at a level outside the declared interval, where the declining
        # branch's threshold contradicts the value the unconditioned clause pins
        # (the refutation needs only that the level is refused and that the
        # pinned value is not the declined one). Its complement is
        # `admiss-f2p-shaped-input`, whose
        # ground `have` introduces the precondition and never uses it: the
        # F2P-shaped point is therefore described unconditionally, so the
        # precondition cannot be hollowing the obligation out at the input the
        # change is about.
        #
        # Needs its own tactic script (the frozen `first` alternatives do not case
        # on the level), which `variant_scope` permits: the theorem STATEMENT is
        # byte-identical, no new axiom/theorem/lemma, no `sorry`.
        "module": _swap(
            _swap(_BASE, _I_ELSE,
                  "  else if !levelAdmitted contamination then\n"
                  "    -- the estimator validates its configured parameters BEFORE it\n"
                  "    -- looks at a carrier, so a level it refuses leaves no fitted\n"
                  "    -- model behind at all: decline instead of inventing a threshold\n"
                  "    Fitting.done { offset := 0.0, warned := false, reference := ref,\n"
                  "                   scoreLater := scoreEntry ref }\n"
                  + _I_ELSE),
            _P_BODY,
            "  -- what presenting a carrier to an estimator through the modeled entry\n"
            "  -- point reports, and what it costs, both read off the program it runs\n"
            "  have hout : ∀ (sc : Scoring) (ref : Reference) (z : InputData),\n"
            "      ((scoreEntry ref z).outcome sc).refused = (scoreReport ref z).refused\n"
            "      ∧ ((scoreEntry ref z).outcome sc).warned = (scoreReport ref z).warned\n"
            "      ∧ ((scoreEntry ref z).outcome sc).refAfter\n"
            "          = (scoreReport ref z).refAfter\n"
            "      ∧ ((scoreEntry ref z).outcome sc).handedOn\n"
            "          = (scoreReport ref z).handedOn\n"
            "      ∧ ((scoreEntry ref z).outcome sc).returned\n"
            "          = (bif (scoreReport ref z).refused then []\n"
            "             else sc (scoreReport ref z).handedOn.values)\n"
            "      ∧ (scoreEntry ref z).traversals sc\n"
            "          = (bif (scoreReport ref z).refused then []\n"
            "             else [(scoreReport ref z).handedOn.values]) := by\n"
            "    intro sc ref z\n"
            "    unfold scoreEntry\n"
            "    cases h : (scoreReport ref z).refused <;>\n"
            "      simp [Scored.outcome, Scored.traversals, h]\n"
            "  unfold problem_spec_fit implementation_fit\n"
            "  intro hlvl hins hcon sc\n"
            "  cases contaminationAuto\n"
            "  case false =>\n"
            "    -- the CONFIGURED lane, and the one place the level precondition does\n"
            "    -- work: it is what rules out the declining branch above, and without\n"
            "    -- it the goal here does not reduce at all\n"
            "    have hla : levelAdmitted contamination = true := hlvl rfl\n"
            "    refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>\n"
            "      simp only [hla, Bool.false_eq_true, if_false,\n"
            "                 Fitting.result, Fitting.traversals,\n"
            "                 (hout sc _ _).1, (hout sc _ _).2.1,\n"
            "                 (hout sc _ _).2.2.1, (hout sc _ _).2.2.2.1,\n"
            "                 (hout sc _ _).2.2.2.2.2, scoreReport,\n"
            "                 validateInput, unrecorded, cond_true, cond_false,\n"
            "                 Bool.not_false, Bool.not_true, Bool.true_and,\n"
            "                 Bool.false_and, hins, hcon] <;>\n"
            "      first\n"
            "        | rfl\n"
            "        | (intro z hc hw hn hi; simp [hi, hc, hw])\n"
            "        | (intro z; and_intros <;> intros <;>\n"
            "           first\n"
            "             | (clear hout; simp_all; done)\n"
            "             | (rw [(hout sc _ z).2.2.2.2.1]\n"
            "                simp [scoreReport, validateInput]))\n"
            "        | (intro h; first\n"
            "            | exact h.elim\n"
            "            | exact trivial\n"
            "            | exact bne_self_eq_false _\n"
            "            | exact absurd trivial h\n"
            "            | rfl\n"
            "            | (simp))\n"
            "  case true =>\n"
            "    refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>\n"
            "      simp only [if_true, Fitting.result, Fitting.traversals,\n"
            "                 (hout sc _ _).1, (hout sc _ _).2.1,\n"
            "                 (hout sc _ _).2.2.1, (hout sc _ _).2.2.2.1,\n"
            "                 (hout sc _ _).2.2.2.2.2,\n"
            "                 scoreReport, validateInput, unrecorded, cond_true,\n"
            "                 cond_false, Bool.not_false, Bool.not_true,\n"
            "                 Bool.true_and, Bool.false_and, hins, hcon] <;>\n"
            "      first\n"
            "        | rfl\n"
            "        | (intro z hc hw hn hi; simp [hi, hc, hw])\n"
            "        | (intro z; and_intros <;> intros <;>\n"
            "           first\n"
            "             | (clear hout; simp_all; done)\n"
            "             | (rw [(hout sc _ z).2.2.2.2.1]\n"
            "                simp [scoreReport, validateInput]))\n"
            "        | (intro h; first\n"
            "            | exact h.elim\n"
            "            | exact trivial\n"
            "            | exact bne_self_eq_false _\n"
            "            | exact absurd trivial h\n"
            "            | rfl\n"
            "            | (simp))"),
        "rationale": "DEFENDS correct_fit against the OVER-STRENGTH reading of the "
                     "whole description on the THRESHOLD LEVEL's domain. The level "
                     "binder is a bare `Float`, while the real estimator declares "
                     "that parameter as either the unconfigured marker or a level "
                     "in a bounded interval and validates it as the FIRST thing "
                     "fitting does -- ahead of any look at the training carrier -- "
                     "so a level it refuses ends the run there, with no threshold, "
                     "no record, no traversal and no fitted model to score with. "
                     "Measured on the real patched callee: at levels outside the "
                     "declared interval fitting raises out of parameter validation "
                     "and the estimator is left unfitted, while every level this "
                     "battery configures completes with exactly one traversal "
                     "(axiom_check.py's parameter-domain leg, with the "
                     "out-of-interval grid as its control). This impl is that "
                     "behaviour: decline where the level is refused, derive the "
                     "threshold verbatim everywhere else -- and it MUST verify, or "
                     "the description would assert an offset and a traversal for a "
                     "run that does not happen. It also shows the precondition is "
                     "load-bearing rather than decorative: its configured branch "
                     "closes only by APPLYING the precondition, and against a "
                     "description without one this same impl is REFUTED and not "
                     "merely unproven -- measured at a refused level, where the "
                     "threshold it declines to invent contradicts the one an "
                     "unconditioned clause would pin. What it must still respect is bounded "
                     "precisely: the frozen configured branch is retained for every "
                     "admitted level, so C1-C8 are untouched on the whole domain "
                     "the description covers, and `admiss-f2p-shaped-input` shows "
                     "that domain still contains the point the change is about. "
                     "Statement byte-identical; tactic body reproved without "
                     "assuming anything.",
    },

    {
        "id": "pos-uninspectable-fit-declines",
        "kind": "soundness",
        "expect": "verify",
        # THE SOUNDNESS CONTROL FOR THE OBLIGATION'S PRECONDITION, and the reason
        # the precondition is a precondition rather than a clause. Deciding
        # whether a carrier bears recordable feature names is the FIRST thing
        # fitting does with it, and that step is not total: presented with column
        # labels of mixed kinds the real code raises there instead of answering,
        # so such a fit produces no threshold, no record and no fitted estimator
        # at all. This impl is the faithful counterpart at that point — it
        # declines the entire tail, describing nothing and admitting nothing —
        # and it MUST verify; if it did not, the obligation would be asserting
        # something about a fit that does not happen. Note how narrow the licence
        # is: the impl keeps the frozen tail verbatim for every carrier the
        # estimator DOES inspect, so nothing else in the description moves, and
        # what such an estimator does with a non-inspectable carrier AFTERWARDS
        # is still required (C5's fifth leg), which is what
        # `later-scoring-admits-uninspectable` below is the reject-lane control
        # for.
        "module": _swap(
            _BASE, _I_TAIL,
            "  if !xOrig.namesInspectable then\n"
            "    -- the estimator's first act on the training carrier is to inspect its\n"
            "    -- labels for recordable names, and on labels of mixed kinds that step\n"
            "    -- raises rather than reporting a status: this fit reaches no threshold,\n"
            "    -- describes no admissible input and leaves no estimator behind.\n"
            "    -- Decline the whole tail rather than invent one.\n"
            "    Fitting.done { offset := 0.0, warned := true, reference := unrecorded,\n"
            "                   scoreLater := fun _ => Scored.done\n"
            "                     { refused := true, warned := true,\n"
            "                       refAfter := unrecorded,\n"
            "                       handedOn := { values := [], nFeatures := 0,\n"
            "                                     hasFeatureNames := false,\n"
            "                                     form := Form.dense,\n"
            "                                     namesInspectable := true,\n"
            "                                     contentAdmissible := true } } }\n"
            "  else\n"
            + "\n".join("  " + ln if ln else ln for ln in _I_TAIL.split("\n"))),
        "rationale": "DEFENDS correct_fit against the reading in which the "
                     "obligation describes a fit that never runs. The model's "
                     "`hasFeatureNames` abstracts the estimator's own label "
                     "inspection, and that inspection is PARTIAL: measured against "
                     "the real patched callee, a carrier whose column labels are of "
                     "mixed kinds makes `_get_feature_names` raise `TypeError` "
                     "instead of returning a status, at fit time and at score time "
                     "alike, whatever the estimator holds on record (axiom_check.py "
                     "leg L, with the homogeneous-label leg as its negative "
                     "control). `InputData.namesInspectable` carries exactly that "
                     "distinction and the obligation is asked only where it holds. "
                     "This impl declines the whole tail there — offset, record and "
                     "later behaviour all withheld — and MUST verify, or the "
                     "precondition would not be a precondition. It bounds the "
                     "licence precisely: the frozen tail is kept verbatim for every "
                     "carrier the estimator inspects, so C1-C8 are unaffected on "
                     "the whole domain the description covers. Statement "
                     "byte-identical; frozen tactic body retained verbatim (the "
                     "declined branch is unreachable under the precondition, which "
                     "the frozen script already has in hand); nothing assumed.",
    },

    {
        "id": "pos-inadmissible-content-fit-declines",
        "kind": "soundness",
        "expect": "verify",
        # THE SOUNDNESS CONTROL FOR THE SECOND PRECONDITION, and the reason it is
        # a precondition rather than a clause. Re-presenting the carrier's content
        # in the model's numeric form is the SECOND thing fitting does with it, and
        # that step is not total either: presented with content it does not accept
        # — content with no rows to describe, content with no columns to describe,
        # or numeric content that is not finite — the real check raises there
        # instead of returning an array, so such a fit produces no threshold, no
        # record and no fitted estimator at all. This impl is the faithful
        # counterpart at that point — it declines the entire tail, describing
        # nothing and admitting nothing — and it MUST verify; if it did not, the
        # obligation would be asserting something about a fit that does not
        # happen. Note how narrow the licence is: the impl keeps the frozen tail
        # verbatim for every carrier whose content the check DOES accept, so
        # nothing else in the description moves, and what such an estimator does
        # with an inadmissible carrier AFTERWARDS is still required (C5's sixth
        # leg), which is what `later-scoring-admits-inadmissible-content` below is
        # the reject-lane control for.
        "module": _swap(
            _BASE, _I_TAIL,
            "  if !xOrig.contentAdmissible then\n"
            "    -- having reported on the carrier's labels the estimator re-presents its\n"
            "    -- content, and on content it does not accept that step raises rather\n"
            "    -- than returning an array: this fit reaches no threshold, describes no\n"
            "    -- admissible input and leaves no estimator behind. Decline the whole\n"
            "    -- tail rather than invent one.\n"
            "    Fitting.done { offset := 0.0, warned := true, reference := unrecorded,\n"
            "                   scoreLater := fun _ => Scored.done\n"
            "                     { refused := true, warned := true,\n"
            "                       refAfter := unrecorded,\n"
            "                       handedOn := { values := [], nFeatures := 0,\n"
            "                                     hasFeatureNames := false,\n"
            "                                     form := Form.dense,\n"
            "                                     namesInspectable := true,\n"
            "                                     contentAdmissible := true } } }\n"
            "  else\n"
            + "\n".join("  " + ln if ln else ln for ln in _I_TAIL.split("\n"))),
        "rationale": "DEFENDS correct_fit against the reading in which the "
                     "obligation describes a fit that never runs, on the second of "
                     "the two steps that can end it before it starts. The "
                     "admissibility check is PARTIAL in its content argument as "
                     "well as in its labels: measured against the real patched "
                     "callee, a carrier with no rows, a carrier with no columns and "
                     "a carrier holding a non-finite value each make the fit raise "
                     "before any threshold is chosen, leaving neither the recorded "
                     "width nor the threshold attribute behind, while the "
                     "ordinary-content carrier of the same shape completes "
                     "(axiom_check.py leg D and its ordinary-content control; "
                     "conformance_check.py's real-code content lanes). "
                     "`InputData.contentAdmissible` carries exactly that "
                     "distinction, and it is not the same distinction as label "
                     "inspectability — a bare array of non-finite numbers is "
                     "perfectly inspectable and answers 'no names' — nor the same "
                     "as the storage form, which the check accepts and hands back. "
                     "This impl declines the whole tail there — offset, record and "
                     "later behaviour all withheld — and MUST verify, or the "
                     "precondition would not be a precondition. It bounds the "
                     "licence precisely: the frozen tail is kept verbatim for every "
                     "carrier whose content the check accepts, so C1-C8 are "
                     "unaffected on the whole domain the description covers. "
                     "Statement byte-identical; frozen tactic body retained "
                     "verbatim (the declined branch is unreachable under the "
                     "precondition, which the frozen script already has in hand); "
                     "nothing assumed.",
    },

    # =====================================================================
    # ADMISSIBILITY — the obligation carries exactly TWO preconditions, the
    # label-inspectability antecedent `xOrig.namesInspectable = true` and the
    # content-admissibility antecedent `xOrig.contentAdmissible = true`, so the
    # nagini precondition-admission probe DOES have a counterpart here: the
    # F2P-shaped point this case discharges the spec at is one whose preconditions
    # BOTH hold (a labelled frame with homogeneous string labels over ordinary
    # finite content — exactly what the failing test builds), so the case fails if
    # either precondition has been drawn so as to exclude the input the fix is
    # about. It covers the residual
    # admissibility risk on a total domain at the same time: that the modeled
    # behavior is UNSATISFIABLE at exactly the interesting input. The LEVEL
    # precondition is covered here too, and unconditionally: the ground `have`
    # introduces it and never applies it, so the eight conjuncts are discharged at
    # this point whatever the parameter validation says about 0.05. The spec
    # predicate is discharged by evaluation at that point (a name-carrying carrier
    # with a configured threshold level) as a ground `have`, then the frozen
    # obligation is closed verbatim. Nothing is assumed: no new
    # declaration, statement byte-identical, the `have` is a live goal inside the
    # existing tactic body. Verified with a real build during authoring.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _ground : problem_spec_fit\n"
            "      { values := [1.0], nFeatures := 3, hasFeatureNames := true,\n"
            "        form := Form.dense, namesInspectable := true,\n"
            "        contentAdmissible := true } false 0.05\n"
            "      (implementation_fit\n"
            "        { values := [1.0], nFeatures := 3, hasFeatureNames := true,\n"
            "          form := Form.dense, namesInspectable := true,\n"
            "          contentAdmissible := true } false 0.05) := by\n"
            "    -- what presenting a carrier to an estimator through the modeled entry\n"
            "    -- point reports, and what it costs, both read off the program it runs\n"
            "    have hout : ∀ (sc : Scoring) (ref : Reference) (z : InputData),\n"
            "        ((scoreEntry ref z).outcome sc).refused = (scoreReport ref z).refused\n"
            "        ∧ ((scoreEntry ref z).outcome sc).warned = (scoreReport ref z).warned\n"
            "        ∧ ((scoreEntry ref z).outcome sc).refAfter\n"
            "            = (scoreReport ref z).refAfter\n"
            "        ∧ ((scoreEntry ref z).outcome sc).handedOn\n"
            "            = (scoreReport ref z).handedOn\n"
            "        ∧ ((scoreEntry ref z).outcome sc).returned\n"
            "            = (bif (scoreReport ref z).refused then []\n"
            "               else sc (scoreReport ref z).handedOn.values)\n"
            "        ∧ (scoreEntry ref z).traversals sc\n"
            "            = (bif (scoreReport ref z).refused then []\n"
            "               else [(scoreReport ref z).handedOn.values]) := by\n"
            "      intro sc ref z\n"
            "      unfold scoreEntry\n"
            "      cases h : (scoreReport ref z).refused <;>\n"
            "        simp [Scored.outcome, Scored.traversals, h]\n"
            "    unfold problem_spec_fit implementation_fit\n"
            "    intro _hlvl hins hcon sc\n"
            "    refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>\n"
            "      simp only [Bool.false_eq_true, if_false, if_true, Fitting.result,\n"
            "                 Fitting.traversals, (hout sc _ _).1, (hout sc _ _).2.1,\n"
            "                 (hout sc _ _).2.2.1, (hout sc _ _).2.2.2.1,\n"
            "                 (hout sc _ _).2.2.2.2.2,\n"
            "                 scoreReport, validateInput,\n"
            "                 unrecorded, cond_true, cond_false, Bool.not_false,\n"
            "                 Bool.not_true, Bool.true_and, Bool.false_and] <;>\n"
            "      first\n"
            "        | rfl\n"
            "        | (intro z hc hw hn hi; simp [hi, hc, hw])\n"
            "        | (intro z; and_intros <;> intros <;>\n"
            "           first\n"
            "             | (clear hout; simp_all; done)\n"
            "             | (rw [(hout sc _ z).2.2.2.2.1]\n"
            "                simp [scoreReport, validateInput]))\n"
            "        | (intro h; first\n"
            "            | exact h.elim\n"
            "            | exact trivial\n"
            "            | exact bne_self_eq_false _\n"
            "            | exact absurd trivial h\n"
            "            | rfl\n"
            "            | (simp))\n"
            + _P_INTRO),
        "rationale": "the modeled behavior is SATISFIABLE at exactly the input "
                     "the failing test exercises — a name-carrying data carrier "
                     "of a definite width with a configured threshold level "
                     "(`hasFeatureNames := true`, `nFeatures := 3`, "
                     "`contaminationAuto := false`) — discharged by evaluation as "
                     "a ground `have`, after which the frozen obligation is "
                     "closed verbatim. All eight conjuncts are discharged there, "
                     "including C5's quantifier and its seven legs and the two "
                     "later clauses, so the "
                     "added clauses are shown "
                     "SATISFIABLE and not merely unfalsified. If this did not "
                     "verify the spec would be unsatisfiable at a normal "
                     "F2P-shaped input. It is also the PRECOND-TOO-STRONG probe: "
                     "both of the obligation's preconditions "
                     "(`namesInspectable := true`, the labels the failing test's "
                     "frame carries, and `contentAdmissible := true`, its ordinary "
                     "finite numeric content) are discharged at that point, so a "
                     "precondition drawn wide enough to exclude the input the fix "
                     "is about would fail here. The level precondition is covered "
                     "in the strongest available form: the ground `have` "
                     "INTRODUCES it and never uses it, so all eight conjuncts hold "
                     "at this point unconditionally -- the level the failing test "
                     "configures (0.05) is described whatever the parameter "
                     "validation says about it, which is what rules out the "
                     "precondition hollowing the description out at exactly the "
                     "input the change is about. Nothing "
                     "is assumed: no new declaration, statement byte-identical, "
                     "the `have` is a live goal. Re-aims the nagini "
                     "admissibility witness.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real counterpart would NOT resolve, and (b) a witness, built
    # against both files during authoring, pinning the violation at one concrete
    # input point.
    # =====================================================================

    # ---- the reported defect itself: a second consistency pass (attacks C1) ----
    {
        "id": "second-consistency-pass",
        "kind": "uniqueness",
        "expect": "reject",
        # THE PRE-PATCH BEHAVIOR. Derive the threshold by routing the
        # already-validated training data back through the VALIDATING entry
        # point, i.e. run the consistency re-check on it, and report the
        # diagnostic that re-check raises. The offset VALUE is unchanged (the
        # re-check leaves the payload alone) — the only difference is the
        # redundant re-check and its diagnostic, exactly what C1 forbids.
        "module": _swap(
            _swap(_BASE, _I_TRAVERSE,
                  "    -- attack: re-check the already-checked data (a second\n"
                  "    -- consistency pass) before traversing it, and report the\n"
                  "    -- diagnostic that re-check raises.\n"
                  "    let v2 := validateInput x false ref Form.sparseByRow\n"
                  "    Fitting.traverse v2.carrier.values fun scores =>"),
            _I_RET,
            "      Fitting.done { offset := off, warned := v2.warned,\n"
            "                     reference := v2.refAfter,\n"
            "                     scoreLater := scoreEntry v2.refAfter }"),
        "refinement": "this is the literal pre-patch behavior: the threshold "
                      "derivation runs a second consistency re-check over the "
                      "already-validated training data. On a fit whose data "
                      "carrier supplies feature-name metadata and whose threshold "
                      "level is configured, that re-check surfaces the spurious "
                      "'does not have valid feature names' diagnostic the issue "
                      "reports. The FAIL_TO_PASS test promotes that diagnostic to "
                      "an error and then fits exactly such a carrier, so a "
                      "faithful counterpart that re-checks RAISES and does NOT "
                      "resolve. If it verified => SPEC-TOO-WEAK on the one clause "
                      "the whole change exists to establish.",
        "rationale": "REJECT from C1 (`result.warned = false`): the second "
                     "consistency pass is a re-check (`reset = false`) against a "
                     "carrier whose metadata was already stripped, so its "
                     "diagnostic flag is the record's metadata status, and the "
                     "rival propagates it. At `hasFeatureNames = true` that is "
                     "`true ≠ false`. C1 is fully transparent, so the witness "
                     "needs no hypothesis: it is stated at the literal F2P-shaped "
                     "point `xOrig = {[1.0], 3, true}`, `contaminationAuto = "
                     "false`, `contamination = 0.05` — the F2P-shaped point "
                     "itself, and the metadata flag must be `true` here because "
                     "this rival AGREES with the frozen impl at "
                     "`hasFeatureNames = false` (measured: the same `_w_warned` "
                     "witness re-stated at `{[1.0], 3, false}` FAILS against this "
                     "rival, exit 1). Ports the nagini validating-path rival "
                     "(there: the advisory tally ends at 1 instead of 0).",
        "witness": _w_warned("[1.0]", "3", "true", "false", "0.05"),
    },

    # ---- silence the diagnostic by RE-DESCRIBING instead of checking (C4) ----
    {
        "id": "second-pass-redescribes-record",
        "kind": "uniqueness",
        "expect": "reject",
        # The rival that motivated C4/C5. It keeps routing the threshold through
        # the scoring path but switches that path's validation from a consistency
        # RE-CHECK to a validation that RE-DESCRIBES the admissible input from
        # the batch it is handed. A re-description raises no diagnostic, so C1 is
        # satisfied HONESTLY — nothing is discarded and the returned flag is
        # genuinely false — and C2/C3 hold because a validation leaves the
        # payload untouched. What it destroys is the record: the estimator ends
        # up describing itself from the stripped batch, so the metadata status it
        # holds is `false` where the training carrier had names.
        "module": _swap(
            _swap(_BASE, _I_TRAVERSE,
                  "    -- attack: route the traversal through a validation that\n"
                  "    -- RE-DESCRIBES the admissible input from the batch it is handed\n"
                  "    -- instead of checking that batch against the record. Such a pass\n"
                  "    -- raises no consistency diagnostic, so none is reported.\n"
                  "    let v2 := validateInput x true ref Form.sparseByRow\n"
                  "    Fitting.traverse v2.carrier.values fun scores =>"),
            _I_RET,
            "      Fitting.done { offset := off, warned := v2.warned,\n"
            "                     reference := v2.refAfter,\n"
            "                     scoreLater := scoreEntry v2.refAfter }"),
        "refinement": "a counterpart whose scoring path re-describes the "
                      "admissible input from each batch it is handed, rather than "
                      "checking that batch against what the fit established, "
                      "silences the reported diagnostic and so PASSES the "
                      "FAIL_TO_PASS test — and destroys the feature-count "
                      "agreement the fitted estimator is supposed to enforce, "
                      "because every scored batch now re-describes what the "
                      "estimator accepts. A PASS_TO_PASS test that fits a table "
                      "and then hands the fitted estimator a NARROWER batch, "
                      "expecting it to be turned away, is broken by exactly this: "
                      "the estimator re-describes itself to the narrower batch "
                      "and accepts it, so nothing is refused and the test's "
                      "expected error never arrives. Measured on the real "
                      "repository: the faithful counterpart passes the "
                      "FAIL_TO_PASS test and fails one PASS_TO_PASS test, i.e. it "
                      "does NOT resolve. This is the verify-not-resolve shape in "
                      "its purest form — it satisfies the diagnostic clause for "
                      "exactly the reason that clause was written — and it is why "
                      "the record and its enforcement have to be pinned and not "
                      "merely the diagnostic.",
        "rationale": "REJECT from C4 (`result.reference = {nFeatures := "
                     "xOrig.nFeatures, hasFeatureNames := "
                     "xOrig.hasFeatureNames}`). C1 holds HONESTLY here — a "
                     "re-describing validation returns a genuinely false "
                     "diagnostic flag, nothing is discarded — and C2/C3 hold by "
                     "congruence since validation leaves the payload untouched, "
                     "so no clause but C4 can refute it, which is precisely the "
                     "point of C4's existence. The record is transparent, so the "
                     "witness needs no hypothesis: it projects the record's "
                     "metadata status out of C4's equation and decides the "
                     "boolean clash (`false ≠ true`) at the F2P-shaped point "
                     "`xOrig = {[1.5], 4, true}`, `contaminationAuto = false`, "
                     "`contamination = 0.15`. The metadata flag must be `true` "
                     "here: at `hasFeatureNames = false` the stripped batch's "
                     "description agrees with the training carrier's and this "
                     "rival is correct.",
        "witness": _w_reference("[1.5]", "4", "true", "false", "0.15"),
    },

    # ---- re-describe the record's WIDTH from a foreign batch (C4, width leg) ----
    {
        "id": "record-width-from-foreign-batch",
        "kind": "uniqueness",
        "expect": "reject",
        # C4's OTHER leg. `second-pass-redescribes-record` re-describes from the
        # training data itself, so it moves only the metadata status and is
        # correct on the width. This rival re-describes from a batch of a
        # DIFFERENT width, so the recorded width is wrong while the metadata
        # status is right — and it emits no diagnostic and scores the correct
        # data, so C1, C2 and C3 all hold.
        "module": _swap(
            _swap(_BASE, _I_TRAVERSE,
                  "    -- attack: describe the admissible input from a batch of a\n"
                  "    -- different width than the training data, then traverse the\n"
                  "    -- training data as usual.\n"
                  "    let other : InputData :=\n"
                  "      { values := x.values, nFeatures := x.nFeatures + 1,\n"
                  "        hasFeatureNames := false, form := x.form,\n"
                  "        namesInspectable := true, contentAdmissible := true }\n"
                  "    let v2 := validateInput other true ref Form.sparseByRow\n"
                  "    Fitting.traverse x.values fun scores =>"),
            _I_RET,
            "      Fitting.done { offset := off, warned := false,\n"
            "                     reference := v2.refAfter,\n"
            "                     scoreLater := scoreEntry v2.refAfter }"),
        "refinement": "a counterpart that records a feature width other than the "
                      "one it was fitted on then enforces the wrong width from "
                      "then on: it turns away batches of the training width and "
                      "accepts batches that do not match the fitted model. Every "
                      "PASS_TO_PASS consumer that fits and then scores or "
                      "predicts on data of the same width raises instead of "
                      "returning, so it does NOT resolve. Like the other record "
                      "rival it emits no diagnostic and derives the threshold "
                      "correctly, so it would PASS the FAIL_TO_PASS test — "
                      "verify-not-resolve unless C4 pins the recorded WIDTH and "
                      "not only the recorded metadata status.",
        "rationale": "REJECT from C4, on its WIDTH component rather than its "
                     "metadata component. The sibling record rival re-describes "
                     "from the training data itself, so its recorded width is "
                     "correct and it can only be caught on the metadata leg; this "
                     "one is the reverse — the recorded metadata status is right "
                     "and the width is off by one — so C4 is shown to be enforced "
                     "on BOTH of its components rather than on one. Transparent, "
                     "so no hypothesis: the witness projects the record's width "
                     "out of C4's equation and decides the natural-number clash "
                     "at `xOrig = {[2.75], 2, false}`, `contamination = 0.35` — a "
                     "distinct width from every other witness, and the metadata "
                     "flag `false`, which pairs a bare carrier with a C4 "
                     "violation and so shows C4 is enforced independently of the "
                     "metadata flag.",
        "witness": _w_reference_width("[2.75]", "2", "false", "false", "0.35"),
    },

    # ---- the fitted estimator refuses nothing afterwards (C5, refused) ----
    {
        "id": "later-scoring-accepts-any-width",
        "kind": "uniqueness",
        "expect": "reject",
        # C5's `refused` component. The record is established correctly (C4
        # holds) and no diagnostic is emitted (C1 holds) and the threshold is
        # right (C2/C3 hold) — the estimator simply never turns a carrier away.
        # Only C5 sees it.
        "module": _swap(
            _BASE, _I_ENTRY_BODY,
            "  -- attack: the fitted estimator turns nothing away — it reports the\n"
            "  -- feature-name diagnostic but never refuses a carrier.\n"
            "  let v := validateInput z false ref Form.sparseByRow\n"
            "  { refused := false, warned := v.warned, refAfter := v.refAfter,\n"
            "    handedOn := v.carrier }"),
        "refinement": "a counterpart whose fitted estimator never refuses an "
                      "inadmissible carrier drops the feature-count agreement "
                      "entirely: handing it a batch of the wrong width no longer "
                      "raises, and the computation proceeds on data that does not "
                      "match the fitted model, so what comes back is meaningless "
                      "rather than an error. A PASS_TO_PASS test that fits and "
                      "then hands the fitted estimator a NARROWER batch, asserting "
                      "that it raises, fails outright. It emits no diagnostic "
                      "during fitting and records the right description, so it "
                      "would PASS the FAIL_TO_PASS test — verify-not-resolve "
                      "unless the spec pins that the recorded description is "
                      "ENFORCED and not merely held.",
        "rationale": "REJECT from C5's refusal leg (`(z.nFeatures != "
                     "xOrig.nFeatures) → (result.scoreLater z).refused = true`). "
                     "C1 through "
                     "C4 all hold — fitting is untouched and the record is "
                     "correct — so nothing but C5 can refute it, which is why C5 "
                     "states enforcement separately from C4's content. "
                     "Transparent, so no hypothesis: the witness instantiates "
                     "C5's quantifier at a NARROWER probe carrier "
                     "`z = {[1.25], 1, false}` against a fit at `xOrig = "
                     "{[1.25], 5, false}`, `contaminationAuto = true`, "
                     "`contamination = 0.45`, and decides the boolean clash. The "
                     "fit is on the UNCONFIGURED branch, so C5 is shown enforced "
                     "there and not only where a threshold level is configured. This is the modeled analogue of the PASS_TO_PASS "
                     "test's own shape: fit, then hand the fitted estimator a "
                     "narrower batch.",
        "witness": _w_later(
            "refused",
            "{ values := [1.25], nFeatures := 1, hasFeatureNames := false, form := Form.dense, namesInspectable := true, contentAdmissible := true }",
            "[1.25]", "5", "false", "true", "0.45"),
    },

    # ---- scoring re-describes what the estimator accepts (C5, refAfter) ----
    {
        "id": "later-scoring-redescribes-record",
        "kind": "uniqueness",
        "expect": "reject",
        # The DURABILITY leg of C5, and the modeled form of the real defect the
        # shown attack caused. Fitting is exactly right — C1..C4 all hold — but
        # the estimator's public entry point validates by RE-DESCRIBING, so each
        # carrier handed to it silently redefines what the estimator accepts and
        # is therefore never refused.
        "module": _swap(
            _BASE, _I_ENTRY_BODY,
            "  -- attack: validate the carrier handed to the fitted estimator as a\n"
            "  -- re-description, so each carrier redefines what the estimator accepts.\n"
            "  let v := validateInput z true ref Form.sparseByRow\n"
            "  { refused := v.refused, warned := v.warned, refAfter := v.refAfter,\n"
            "    handedOn := v.carrier }"),
        "refinement": "a counterpart whose public scoring path re-describes the "
                      "admissible input from every batch it is handed keeps the "
                      "description the fit established only until the first batch "
                      "arrives, after which the estimator accepts whatever it was "
                      "last shown. Nothing is ever refused and the fitted "
                      "estimator no longer holds the description its own training "
                      "data established. A PASS_TO_PASS test that fits and then "
                      "hands the fitted estimator a narrower batch, asserting it "
                      "raises, fails; this is the measured behavior of the real "
                      "counterpart of this shape (FAIL_TO_PASS passes, one "
                      "PASS_TO_PASS test fails, so it does NOT resolve). It is "
                      "the reason C5 pins the record AFTER a later call and not "
                      "only the record at the moment fitting returns.",
        "rationale": "REJECT from C5 — refuted on the `refused` component at a "
                     "narrower probe carrier, since a re-describing validation "
                     "checks nothing and so refuses nothing. C1 through C4 all "
                     "hold (fitting is byte-identical to the frozen impl), and "
                     "this rival is distinguished from "
                     "`later-scoring-accepts-any-width` in mechanism rather than "
                     "point: that one hard-codes the refusal to `false` while "
                     "keeping a checking validation, this one keeps the refusal "
                     "faithful and switches the validation to a re-description, "
                     "which also moves C5's `refAfter` component. Two distinct "
                     "wrong implementations, one clause, showing the clause is "
                     "not merely a restatement of one impl's spelling. Witnessed "
                     "at a narrower probe carrier `z = {[8.5], 1, true}` against "
                     "a fit at `xOrig = {[8.5], 3, true}`, `contaminationAuto = "
                     "false`, `contamination = 0.22` — a probe that AGREES with "
                     "the training carrier in metadata status, so the refutation "
                     "turns on the width check alone.",
        "witness": _w_later(
            "refused",
            "{ values := [8.5], nFeatures := 1, hasFeatureNames := true, form := Form.dense, namesInspectable := true, contentAdmissible := true }",
            "[8.5]", "3", "true", "false", "0.22"),
    },

    # ---- the estimator stays silent on a later name disagreement (C5, warned) ----
    {
        "id": "later-scoring-silent-on-names",
        "kind": "uniqueness",
        "expect": "reject",
        # C5's `warned` component, the leg the two width rivals cannot reach.
        # Both of those move `refused`; this one keeps the width check exactly
        # right and drops the feature-name diagnostic on later use.
        "module": _swap(
            _BASE, _I_ENTRY_BODY,
            "  -- attack: the fitted estimator checks the width but stays silent\n"
            "  -- about a feature-name disagreement.\n"
            "  let v := validateInput z false ref Form.sparseByRow\n"
            "  { refused := v.refused, warned := false, refAfter := v.refAfter,\n"
            "    handedOn := v.carrier }"),
        "refinement": "a counterpart whose fitted estimator never reports a "
                      "feature-name disagreement on later use silently accepts a "
                      "table whose columns are named differently from the training "
                      "table, or a bare array where a named table was expected, "
                      "so a caller who has permuted or renamed columns gets "
                      "silently wrong answers instead of the diagnostic that "
                      "exists to catch exactly that. The PASS_TO_PASS body that "
                      "asserts the estimator warns on a feature-name "
                      "disagreement fails. It changes nothing about fitting, so "
                      "it would PASS the FAIL_TO_PASS test — verify-not-resolve "
                      "unless C5 pins the diagnostic on later use and not only "
                      "during the fit. Note the direction: the reported issue is "
                      "that this diagnostic fires when it should not; suppressing "
                      "it wholesale is the opposite error, and a spec that "
                      "demanded silence during fitting without pinning the "
                      "diagnostic afterwards would license it.",
        "rationale": "REJECT from C5's second component (`(result.scoreLater "
                     "z).warned = (xOrig.hasFeatureNames != z.hasFeatureNames)`). "
                     "The two other C5 rivals move the `refused` component and "
                     "both keep this one faithful, so neither could be refuted "
                     "here (their probe carrier agrees in metadata status); this "
                     "rival keeps the width check exact and drops the diagnostic, "
                     "so C5 is shown enforced on its diagnostic component "
                     "independently. Transparent, so no hypothesis: witnessed at "
                     "a NAME-CARRYING probe carrier `z = {[0.5], 6, true}` of the "
                     "training width against a fit on a bare carrier `xOrig = "
                     "{[0.5], 6, false}` — the metadata disagreement that must "
                     "draw the diagnostic, at the training width so the width "
                     "check cannot be what refutes it — `contaminationAuto = "
                     "true`, `contamination = 0.65`.",
        "witness": _w_later(
            "warned",
            "{ values := [0.5], nFeatures := 6, hasFeatureNames := true, form := Form.dense, namesInspectable := true, contentAdmissible := true }",
            "[0.5]", "6", "false", "true", "0.65"),
    },

    # ---- the entry point checks, then hands on the unchecked object (C5) ----
    {
        "id": "later-scoring-forwards-caller-payload",
        "kind": "uniqueness",
        "expect": "reject",
        # C5's handed-on leg. This rival performs the admissibility check in
        # full — the right refusals, the right diagnostic, the record kept — and
        # then hands the fitted model the CALLER'S OWN object instead of the one
        # the check re-presented. Every clause over the outcome's booleans and
        # its record is satisfied exactly, which is what makes it invisible to
        # C1-C4, C6, C7 and C8: the defect is in the VALUE that crosses from the
        # entry point into the model, so the outcome has to carry that value for
        # any clause to reach it.
        "module": _swap(
            _BASE, _I_ENTRY_BODY,
            "  -- attack: check the carrier, then hand the fitted model the caller's\n"
            "  -- own object rather than the one the check re-presented. Every\n"
            "  -- diagnostic and the record are exactly right.\n"
            "  let v := validateInput z false ref Form.sparseByRow\n"
            "  { refused := v.refused, warned := v.warned, refAfter := v.refAfter,\n"
            "    handedOn := z }"),
        "refinement": "a counterpart whose public scoring entry point runs its "
                      "admissibility checks and then scores the caller's own "
                      "object — rather than the object those checks re-presented "
                      "— turns away the wrong width, emits the feature-name "
                      "diagnostic and keeps the record, all exactly as the real "
                      "estimator does, so no diagnostic and no recorded attribute "
                      "can tell it apart. What reaches the scoring path is "
                      "unconverted: a nested Python list, or a float64 frame "
                      "where the chunked scoring code requires the checked "
                      "float32 array. Measured on the real repository in exactly "
                      "this shape — the public scorer performs the feature-name "
                      "and feature-count checks and then calls the new "
                      "non-validating private scorer on its raw argument: the "
                      "FAIL_TO_PASS body PASSES (fitting is untouched and emits "
                      "no warning) and four PASS_TO_PASS bodies that score or "
                      "predict through the public path FAIL where the unconverted "
                      "object reaches array code, against a control on the same "
                      "harness where all four pass. Verify-not-resolve, and on an "
                      "observable that is not a detail: the entry point's check "
                      "has to be what FEEDS the model, not merely what precedes "
                      "it.",
        "rationale": "REJECT from C5's fourth leg (`(result.scoreLater z).refused "
                     "= false → (result.scoreLater z).handedOn = { values := "
                     "checked z.values, nFeatures := z.nFeatures, "
                     "hasFeatureNames := false, "
                     "form := Form.reshaped z.form Form.sparseByRow, "
                     "namesInspectable := true, contentAdmissible := true }`), "
                     "and ONLY from that leg — and within it from the CONTENT "
                     "field, the half a substituted payload reaches. The rival is "
                     "definitionally equal to the frozen impl in the refusal "
                     "flag, the diagnostic and the record, so C1 through C4 hold, "
                     "C6 and C7 hold (they constrain refusal alone, which is "
                     "untouched) and C8 holds (fitting's traversals are "
                     "untouched) — the leg exists because nothing else on this "
                     "surface can see which VALUE crosses the entry point. "
                     "Conditioned on ONE hypothesis about ONE term, the route the "
                     "two offset witnesses take and for the same reason: both "
                     "sides of this equation are applications of the OPAQUE "
                     "re-presentation callee, which has no computable value. The "
                     "hypothesis is that re-presenting the probe payload is not "
                     "the identity on it, and it is grounded against the real "
                     "callee by `axiom_check.py`'s handed-on leg (payloads whose "
                     "checked form differs from what was presented, plus the "
                     "negative control that the caller's own object is NOT what "
                     "the real public path hands on). Witnessed at `xOrig = "
                     "{[0.1], 1, false}`, `contaminationAuto = true`, "
                     "`contamination = 0.25` with the probe carrier `z = {[4.5], "
                     "1, false}`: the TRAINING width, so the leg's non-refusal "
                     "guard is discharged rather than dodged; NAMELESS, so no "
                     "name comparison can arise; and a payload NOT already in the "
                     "accepted numeric form, which is the only region where the "
                     "leg has content — a carrier already in that form is handed "
                     "on unchanged either way, so probing one would attribute "
                     "nothing.",
        "witness": _w_handed_on(
            "h : checked [4.5] ≠ [4.5]",
            "[0.1]", "1", "false", "true", "0.25", "[4.5]"),
    },

    # ---- the entry point re-presents the content, then describes the
    # ---- presentation as the caller's own object (C5) ----
    {
        "id": "later-scoring-hands-on-caller-description",
        "kind": "uniqueness",
        "expect": "reject",
        # C5's handed-on leg again, on the OTHER half of what that leg pins. This
        # rival re-presents the content exactly as the frozen impl does — the
        # payload equality holds — and then describes the presentation the way the
        # CALLER described its object: still advertising the caller's labels,
        # still inspectable-or-not and admissible-or-not as the caller's object
        # was. Every diagnostic, the record, the refusals and the handed-on
        # CONTENT are the frozen values, so C1-C4, C6, C7 and C8 hold exactly and
        # even the content half of C5's own leg holds; only the presentation's
        # self-description is wrong, which is why the leg has to pin the whole
        # carrier rather than its payload alone.
        "module": _swap(
            _BASE, _I_ENTRY_BODY,
            "  -- attack: re-present the content, then describe the presentation as the\n"
            "  -- caller described its object — keep its labels, and keep whether the\n"
            "  -- estimator would inspect and admit it. Content, diagnostics, refusals\n"
            "  -- and record are all exactly right.\n"
            "  let v := validateInput z false ref Form.sparseByRow\n"
            "  { refused := v.refused, warned := v.warned, refAfter := v.refAfter,\n"
            "    handedOn :=\n"
            "      { v.carrier with hasFeatureNames := z.hasFeatureNames,\n"
            "                       namesInspectable := z.namesInspectable,\n"
            "                       contentAdmissible := z.contentAdmissible } }"),
        "refinement": "a counterpart whose entry point converts the carrier and "
                      "then hands the fitted model a re-wrapped object — the "
                      "checked content put back behind the caller's own labels — "
                      "passes every check the real one does and then feeds the "
                      "scoring path something that is not the array that path "
                      "operates on. The consequence is not hypothetical: the "
                      "chunked scoring code indexes what it is handed "
                      "POSITIONALLY, and a labelled table indexes by label, so "
                      "the PASS_TO_PASS bodies that score or predict through the "
                      "public entry point break on the re-wrapped object while "
                      "fitting itself is untouched and the FAIL_TO_PASS body "
                      "still passes. It is also the shape that reintroduces the "
                      "reported defect one call later: the object the model is "
                      "handed carries names again, so an estimator that scores "
                      "through its own entry point re-raises the very "
                      "feature-name advisory this instance is about. "
                      "Verify-not-resolve, and on the half of the handed-on "
                      "observable that a payload equality cannot see.",
        "rationale": "REJECT from C5's fourth leg, and only from it — but from the "
                     "SELF-DESCRIPTION half of that leg rather than the content "
                     "half, which is what makes it the companion attack to "
                     "`later-scoring-forwards-caller-payload` and the reason the "
                     "leg pins a CARRIER rather than a payload. The rival is "
                     "definitionally equal to the frozen impl in the refusal flag, "
                     "the diagnostic, the record and the handed-on content, so "
                     "C1-C4, C6, C7 and C8 hold, and so does every field of the "
                     "leg except the three the presentation describes itself with. "
                     "Grounded against the real patched callee by `axiom_check.py` "
                     "leg E: what the estimator's admissibility step hands back "
                     "advertises NO feature-name metadata, and is itself "
                     "inspectable and admissible — measured on the same carriers "
                     "the other legs use, with the caller's own object as the "
                     "negative control on every one of the three fields (the "
                     "labelled frame that goes IN does carry names, and the "
                     "carriers legs L and D turn away are not inspectable and not "
                     "admissible, so each field is one the real callee can and does "
                     "answer differently). UNCONDITIONED: the field it contradicts "
                     "is the one no opaque callee touches, so `decide` discharges "
                     "the non-refusal guard and the contradiction alike. Witnessed "
                     "at `xOrig = {[0.35], 4, false}`, `contaminationAuto = false`, "
                     "`contamination = 0.45` with the probe carrier `z = {[6.25], "
                     "4, TRUE}`: a NAME-BEARING probe at the training width against "
                     "a nameless fit, which is exactly the region C7 admits (so "
                     "the guard is discharged rather than dodged) and the only "
                     "region where a probe's labels are both present and not a "
                     "ground for refusal.",
        "witness": _w_handed_on_description(
            "[0.35]", "4", "false", "false", "0.45", "[6.25]"),
    },

    # ---- the entry point hands the model the sparse layout its own scoring
    # ---- path refuses (C5) ----
    {
        "id": "later-scoring-hands-on-unscorable-layout",
        "kind": "uniqueness",
        "expect": "reject",
        # C5's handed-on leg a third time, on the STORAGE FORM the crossing
        # carrier is handed on in. This rival's entry point performs its
        # admissibility check in full and converts the content exactly as the
        # frozen impl does — the payload equality holds, the self-description
        # holds — but the check it performs accepts the COLUMN-indexed sparse
        # layout rather than the row-indexed one, so a sparse carrier crosses into
        # the fitted model in the layout that model's scoring path cannot
        # traverse. Every diagnostic, the record, the refusals, fitting's
        # traversals, the handed-on content and the handed-on self-description are
        # the frozen values, so C1-C4, C6, C7, C8 and six of the seven legs of C5
        # hold exactly; the defect is in the one property of the crossing value
        # the scoring path on the far side actually requires.
        "module": _swap(
            _BASE, _I_ENTRY_BODY,
            "  -- attack: check and convert the carrier exactly as the real entry point\n"
            "  -- does, but perform the check for the COLUMN-indexed sparse layout, so a\n"
            "  -- sparse carrier is handed on in the layout the fitted model's scoring\n"
            "  -- path refuses. Content, self-description, diagnostics, refusals and\n"
            "  -- record are all exactly right.\n"
            "  let v := validateInput z false ref Form.sparseByColumn\n"
            "  { refused := v.refused, warned := v.warned, refAfter := v.refAfter,\n"
            "    handedOn := v.carrier }"),
        "refinement": "a counterpart whose public scoring entry point declares the "
                      "column-indexed sparse layout as the one it accepts — "
                      "instead of the row-indexed one — converts and checks every "
                      "carrier exactly as the real estimator does: the same "
                      "refusals on a disagreeing width, the same feature-name "
                      "diagnostic, the same recorded attributes, the same numeric "
                      "content, and a genuinely converted object rather than the "
                      "caller's own. It differs from the real one in nothing but "
                      "WHICH sparse layout the converted object is handed on in. "
                      "Fitting is untouched, so the FAIL_TO_PASS body PASSES. The "
                      "non-validating scoring path the entry point forwards to "
                      "requires the row-indexed layout and raises on the "
                      "column-indexed one, so every PASS_TO_PASS body that scores "
                      "or predicts a SPARSE carrier through the public entry point "
                      "FAILS. Measured on the real repository in exactly this "
                      "shape: FAIL_TO_PASS passes 1/1 and PASS_TO_PASS is 20/21, "
                      "the sparse round-trip body failing, twice in a row and "
                      "against a control on the same harness where all 21 pass. So "
                      "it does NOT resolve. Verify-not-resolve on an observable no "
                      "clause about content, diagnostics, records or work can see: "
                      "which of the two sparse layouts crosses the entry point is "
                      "the property the scoring path turns on, and a requirement "
                      "that the crossing carrier merely still be SPARSE would leave "
                      "it entirely unsaid.",
        "rationale": "REJECT from C5's fourth leg, and only from it — from the "
                     "STORAGE FORM field of it (`form := Form.reshaped z.form "
                     "Form.sparseByRow`), the third of the three separable halves "
                     "of that leg and the companion of "
                     "`later-scoring-forwards-caller-payload` (content) and "
                     "`later-scoring-hands-on-caller-description` "
                     "(self-description). The rival is definitionally equal to the "
                     "frozen impl in the refusal flag, the diagnostic, the record, "
                     "the handed-on content and the handed-on self-description, so "
                     "C1-C4, C6, C7 and C8 hold and so does every other field of "
                     "the leg. Note what this rival is NOT: it does not fail to "
                     "convert, and it does not misdescribe what it hands on — a "
                     "clause pinning the crossing carrier's content, its labels, "
                     "its inspectability and its admissibility is satisfied by it "
                     "exactly. Nor can a coarser model reach it: with the storage "
                     "form carried as a single sparseness bit this rival is "
                     "BYTE-FOR-BYTE the frozen computation (a check that admits "
                     "sparse content and hands it back sparse is the same function "
                     "on that bit whichever layout it accepts), so no predicate "
                     "over such a model could separate the two at all — which is "
                     "why the form is three-valued and why the leg pins WHICH "
                     "layout crosses rather than only that a sparse carrier stays "
                     "sparse. Grounded against the real patched callees by "
                     "`axiom_check.py`'s layout legs: the estimator's scoring-side "
                     "admissibility step hands a sparse carrier back ROW-indexed "
                     "(and hands a dense one back dense, which is `Form.reshaped`), "
                     "its fit-side step hands the same carrier back "
                     "COLUMN-indexed — so the accepted layout is measurably a "
                     "property of the step and not of the estimator — and the "
                     "non-validating scoring path measurably consumes the "
                     "row-indexed layout and raises on the column-indexed one, "
                     "which is the negative control that makes the difference "
                     "observable rather than cosmetic. UNCONDITIONED: the field it "
                     "contradicts is the check's own choice of accepted layout and "
                     "not the opaque re-presentation callee's value, so `decide` "
                     "discharges the non-refusal guard and the contradiction alike. "
                     "Witnessed at `xOrig = {[0.75], 2, false}`, "
                     "`contaminationAuto = true`, `contamination = 0.2` with the "
                     "probe carrier `z = {[3.5], 2, false}` presented in the "
                     "ROW-INDEXED sparse layout: the TRAINING width, so the leg's "
                     "non-refusal guard is discharged rather than dodged; "
                     "NAMELESS, so no name comparison can arise; SPARSE, which is "
                     "the only region where the leg's form field has content at all "
                     "(dense content crosses dense whichever layout a check "
                     "accepts); and presented in the layout the crossing REQUIRES, "
                     "so the rival is refuted even where nothing needed converting "
                     "— it is handing on the wrong layout, not failing to reach the "
                     "right one.",
        "witness": _w_handed_on_form(
            "[0.75]", "2", "false", "true", "0.2", "[3.5]",
            probe_form="Form.sparseByRow"),
    },

    # ---- threshold never derived from the data at all (attacks C3) ----
    {
        "id": "forged-constant-offset",
        "kind": "uniqueness",
        "expect": "reject",
        # Return the UNCONFIGURED branch's constant on the configured branch too:
        # the threshold is asserted rather than derived from the training data.
        # C1, C2, C4 and C5 hold; only C3 is violated.
        "module": _swap(
            _BASE, _I_OFF,
            "      -- attack: assert the threshold instead of deriving it from the\n"
            "      -- scores the traversal yielded.\n"
            "      let off := (-0.5 : Float)"),
        "refinement": "a counterpart that hands back the unconfigured branch's "
                      "fixed constant on the configured branch never derives the "
                      "threshold from the training data at all, so the fitted "
                      "threshold is unrelated to the configured level and every "
                      "PASS_TO_PASS consumer that reads decisions/predictions off "
                      "that threshold observes the wrong cut. Note the "
                      "verify-not-resolve shape precisely: this rival emits no "
                      "diagnostic and records the right description, so it would "
                      "PASS the FAIL_TO_PASS test while breaking the threshold's "
                      "meaning — which is why C3 has to be pinned and not merely "
                      "C1.",
        "rationale": "REJECT from C3 (`¬contaminationAuto → offset = percentile "
                     "(sc (checked xOrig.values)) (100.0 * contamination)`): the "
                     "rival returns the constant `-0.5` on the configured branch. "
                     "C3's right-hand side is stated over the `opaque` callees, "
                     "so the witness CONDITIONS on the sub-domain where the rival "
                     "is wrong — that the configured percentile of the training "
                     "scores is not that constant — one hypothesis about one "
                     "term. Refuted at `xOrig = {[3.0], 1, false}`, "
                     "`contamination = 0.1`. Ports the nagini "
                     "forge-the-offset-token rival (there: claim the offset is "
                     "set without ever scoring; here the provenance token "
                     "collapses onto the value equation, which is what a "
                     "fabricated threshold violates).",
        "witness": _w_offset(
            "h : percentile (checked [3.0]) (100.0 * 0.1) ≠ -0.5",
            "[3.0]", "1", "false", "false", "0.1", "configured", flip=True),
    },

    # ---- threshold derived from the wrong data batch (attacks C3's carrier) ----
    {
        "id": "foreign-batch-scored",
        "kind": "uniqueness",
        "expect": "reject",
        # Score a locally fabricated carrier instead of this fit's own training
        # data. Structurally the right computation, applied to the wrong
        # argument: C1, C2, C4 and C5 hold, C3 is violated wherever the two
        # batches' scores differ.
        "module": _swap(
            _BASE, _I_TRAVERSE,
            "    -- attack: traverse a fabricated batch instead of this fit's own data.\n"
            "    -- The fabricated batch is admitted and traversed exactly as the\n"
            "    -- training data would be, so the only error is WHICH batch is\n"
            "    -- traversed — one traversal either way.\n"
            "    let foreign : InputData :=\n"
            "      { values := [], nFeatures := x.nFeatures,\n"
            "        hasFeatureNames := false, form := x.form,\n"
                  "        namesInspectable := true, contentAdmissible := true }\n"
            "    Fitting.traverse (checked foreign.values) fun scores =>"),
        "refinement": "a counterpart that derives the threshold from a batch "
                      "other than the data being fitted computes an order "
                      "statistic of the wrong sample entirely, so the fitted "
                      "threshold does not sit at the configured rank of the "
                      "training scores; the PASS_TO_PASS tests that assert "
                      "predictions/decision values against a correctly derived "
                      "threshold observe the wrong cut and it does NOT resolve. "
                      "Like the forged-constant rival it emits no diagnostic and "
                      "records the right description, so it would pass the "
                      "FAIL_TO_PASS test — a verify-not-resolve break if C3 did "
                      "not name the training carrier.",
        "rationale": "REJECT from C3, on its ARGUMENT rather than its shape: the "
                     "spec pins `percentile (sc (checked xOrig.values)) …` "
                     "and the rival computes `percentile (checked []) "
                     "…`. Nothing is "
                     "assumed about what a traversal yields — the witness "
                     "instantiates the quantified interpretation itself, and "
                     "conditions only on the two applications differing at the "
                     "probed input, which is the sub-domain where scoring a "
                     "foreign batch is wrong. Note the fabricated batch keeps the "
                     "training WIDTH, so C4 and C5 are untouched and only C3 can "
                     "catch it. Refuted at `xOrig = {[4.0, 5.0], 2, false}`, "
                     "`contamination = 0.2` — the only witness with a "
                     "multi-element payload at width 2, so C3's dependence on the "
                     "payload itself is exercised. Ports the nagini "
                     "fabricated-matrix rival (there: the fabricated matrix lacks "
                     "the provenance token that binds the scored batch to this "
                     "fit's own input).",
        "witness": _w_offset(
            "h : percentile (checked []) (100.0 * 0.2)\n"
            "      ≠ percentile (checked [4.0, 5.0]) (100.0 * 0.2)",
            "[4.0, 5.0]", "2", "false", "false", "0.2", "configured"),
    },

    # ---- threshold taken at the wrong rank (attacks C3's rank binder) ----
    {
        "id": "rank-unscaled",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss on the rank: take the order statistic at the raw configured
        # fraction instead of the percentage-scaled rank. Right data, right
        # computation, wrong rank — the only rival that moves the
        # `contamination` binder's role in C3.
        "module": _swap(
            _BASE, _I_OFF,
            "      -- attack: take the order statistic at the raw configured fraction\n"
            "      -- instead of the percentage-scaled rank.\n"
            "      let off := percentile scores contamination"),
        "refinement": "a counterpart that passes the configured fraction straight "
                      "to the order-statistic routine instead of the "
                      "percentage-scaled rank asks for a rank a hundredfold too "
                      "small, so the fitted threshold sits at essentially the "
                      "sample minimum regardless of the configured level; the "
                      "PASS_TO_PASS tests that pin how many training points fall "
                      "on each side of the threshold for a given configured level "
                      "then fail, so it does NOT resolve. It emits no diagnostic, "
                      "records the right description and is correct on the "
                      "unconfigured branch, so it would pass the FAIL_TO_PASS "
                      "test — again verify-not-resolve if C3 did not pin the "
                      "rank.",
        "rationale": "REJECT from C3, on its RANK argument: the spec pins the rank "
                     "`100.0 * contamination` and the rival uses `contamination`. "
                     "Both terms are opaque applications, so the witness "
                     "conditions on the two ranks yielding different order "
                     "statistics at the probed input. Refuted at `xOrig = {[6.0], "
                     "1, true}`, `contamination = 0.5` — a distinct payload and "
                     "level, and a witness carrying `hasFeatureNames = true`, "
                     "which pairs a name-carrying carrier with an offset-clause "
                     "violation and so shows C3 is enforced independently of the "
                     "metadata flag. ADDED beyond the nagini set (whose value "
                     "abstraction dropped the offset value entirely, leaving it "
                     "with no clause to attack here); it attacks a load-bearing "
                     "part of the SAME modeled spec.",
        "witness": _w_offset(
            "h : percentile (checked [6.0]) 0.5\n"
            "      ≠ percentile (checked [6.0]) (100.0 * 0.5)",
            "[6.0]", "1", "true", "false", "0.5", "configured"),
    },

    # ---- the diagnostic reported unconditionally (attacks C1 at the OTHER
    # ---- metadata point) ----
    {
        "id": "recheck-against-fixed-names",
        "kind": "uniqueness",
        "expect": "reject",
        # C1 rival at the metadata point `second-consistency-pass` cannot reach.
        # That rival compares the re-check against the record, so it is WRONG
        # only on a name-carrying carrier and correct at `hasFeatureNames =
        # false`. This one re-checks against a hard-coded "expects feature names"
        # record, so it raises the diagnostic on every configured fit —
        # including a carrier that never had feature-name metadata, where the
        # previous rival agrees with the frozen impl.
        "module": _swap(
            _swap(_BASE, _I_TRAVERSE,
                  "    -- attack: re-check against a hard-coded 'expects feature names'\n"
                  "    -- record rather than what this fit actually described.\n"
                  "    let v2 := validateInput x false\n"
                  "      { nFeatures := ref.nFeatures, hasFeatureNames := true }\n"
                  "      Form.sparseByRow\n"
                  "    Fitting.traverse v2.carrier.values fun scores =>"),
            _I_RET,
            "      Fitting.done { offset := off, warned := v2.warned,\n"
            "                     reference := ref, scoreLater := scoreEntry ref }"),
        "refinement": "a counterpart whose consistency re-check tests against a "
                      "fixed 'expects feature names' answer instead of what this "
                      "fit actually recorded surfaces the spurious feature-name "
                      "diagnostic on EVERY fit with a configured threshold level, "
                      "including the bare-numeric-carrier fits that were never "
                      "affected by the reported issue. The FAIL_TO_PASS test "
                      "promotes that diagnostic to an error, so it raises and does "
                      "NOT resolve; and it additionally breaks the "
                      "bare-numeric-carrier fits the PASS_TO_PASS body exercises, "
                      "which the reported issue never touched.",
        "rationale": "REJECT from C1 (`result.warned = false`), at the metadata "
                     "point the other C1 rival CANNOT reach. "
                     "`second-consistency-pass` compares against the record this "
                     "fit established, so at `hasFeatureNames = false` its "
                     "diagnostic flag is `false` and it AGREES with the frozen "
                     "impl there; its witness must therefore sit at "
                     "`hasFeatureNames = true`. This rival is wrong at "
                     "`hasFeatureNames = false` instead, so C1 is shown to be "
                     "enforced at BOTH values of the metadata binder rather than "
                     "only on a name-carrying carrier. Note it keeps the record "
                     "and the entry point faithful, so C4/C5 cannot catch it and "
                     "C1 is doing the work. C1 is transparent, so the witness "
                     "needs no hypothesis; refuted at `xOrig = {[7.0, 8.0], 2, "
                     "false}`, `contamination = 0.3`. ADDED by an earlier audit: "
                     "the shipped battery moved `hasFeatureNames` across "
                     "witnesses but never attacked C1 at the `false` point.",
        "witness": _w_warned("[7.0, 8.0]", "2", "false", "false", "0.3"),
    },

    # ---- the diagnostic surfaced on the UNCONFIGURED branch (attacks C1 on the
    # ---- branch the other two C1 rivals cannot reach) ----
    {
        "id": "auto-branch-diagnostic",
        "kind": "uniqueness",
        "expect": "reject",
        # Both other C1 rivals edit the CONFIGURED tail, so each is correct
        # whenever `contaminationAuto` is true and neither can be refuted on the
        # unconfigured branch. C1 is a top-level clause with no branch guard, so
        # it must hold on BOTH branches; this rival keeps the configured tail
        # exactly as frozen and reports the diagnostic on the unconfigured one.
        "module": _swap(
            _BASE, _I_AUTO_RET,
            "    -- attack: surface the consistency diagnostic on the unconfigured\n"
            "    -- branch, where no re-check is performed at all.\n"
            "    Fitting.done { offset := -0.5, warned := true, reference := ref,\n"
            "                   scoreLater := scoreEntry ref }"),
        "refinement": "a counterpart that surfaces the feature-name diagnostic "
                      "when no threshold level is configured raises on the DEFAULT "
                      "fitting path — the path the large PASS_TO_PASS body "
                      "exercises, and one the reported issue never touched. The "
                      "FAIL_TO_PASS test promotes that diagnostic to an error but "
                      "fits with a configured level, and this rival is exact on "
                      "the configured branch, so it would PASS that test while "
                      "breaking every default fit: verify-not-resolve unless C1 is "
                      "enforced on the unconfigured branch too.",
        "rationale": "REJECT from C1 (`result.warned = false`), on the BRANCH the "
                     "other two C1 rivals cannot reach. Both of those edit the "
                     "configured tail, so each is definitionally correct wherever "
                     "`contaminationAuto = true` and no witness there could refute "
                     "either (measured). C1 carries no branch guard, so it must "
                     "hold on both; this rival keeps the configured tail frozen "
                     "verbatim and breaks only the unconfigured one. C1 is "
                     "transparent, so the witness needs no hypothesis; refuted at "
                     "`xOrig = {[2.5, 3.5], 2, false}`, `contaminationAuto = "
                     "true`, `contamination = 0.6` — a distinct payload and level, "
                     "and a witness on the unconfigured branch. ADDED by an "
                     "earlier audit: clause coverage counted C1 as attacked at "
                     "both metadata points but every C1 witness sat at "
                     "`contaminationAuto = false`.",
        "witness": _w_warned("[2.5, 3.5]", "2", "false", "true", "0.6"),
    },

    # ---- the unconfigured constant with the wrong sign (attacks C2's VALUE) ----
    {
        "id": "auto-constant-sign-flipped",
        "kind": "uniqueness",
        "expect": "reject",
        # C2 rival that keeps the branch STRUCTURE and breaks only the constant.
        # `unconditional-derivation` deletes the unconfigured branch outright, so
        # it attacks whether the branch EXISTS; this attacks the constant the
        # branch returns.
        "module": _swap(
            _BASE, _I_AUTO_RET,
            "    -- attack: yield the constant with the wrong sign.\n"
            "    Fitting.done { offset := 0.5, warned := false, reference := ref,\n"
            "                   scoreLater := scoreEntry ref }"),
        "refinement": "a counterpart that selects `+0.5` where the unconfigured "
                      "branch must select its fixed negative threshold inverts the "
                      "sense of the cut: with the score convention that larger is "
                      "less abnormal, every training point lands on the opposite "
                      "side of the threshold from where it belongs, so the default "
                      "unconfigured fit labels the bulk of an ordinary sample as "
                      "abnormal. The PASS_TO_PASS body that fits at the default "
                      "setting and asserts predictions/decision values then fails, "
                      "so it does NOT resolve. It emits no diagnostic, records the "
                      "right description and is exact on the configured branch, so "
                      "it would PASS the FAIL_TO_PASS test — verify-not-resolve if "
                      "C2 pinned only the branch's existence and not its value.",
        "rationale": "REJECT from C2 (`contaminationAuto → offset = -0.5`), on its "
                     "VALUE rather than on whether the branch is reached. "
                     "`unconditional-derivation` removes the branch entirely, so "
                     "it cannot distinguish a branch that returns the WRONG "
                     "constant; this rival keeps the branch and flips the sign. "
                     "The clause's two sides are `Float` literals, which `decide` "
                     "cannot settle on this carrier (no kernel-reducible "
                     "`Decidable` instance for `Float` equality), so the witness "
                     "conditions on the literal disequality itself — one "
                     "hypothesis about one ground term, and the gate's consistency "
                     "probe confirms `False` does not follow from it. Refuted at "
                     "`xOrig = {[9.0], 1, true}`, `contaminationAuto = true`, "
                     "`contamination = 0.75` — a second witness with "
                     "`contaminationAuto = true` and a distinct payload and level. "
                     "ADDED by an earlier audit.",
        "witness": _w_offset(
            "h : (0.5 : Float) ≠ -0.5",
            "[9.0]", "1", "true", "true", "0.75", "auto"),
    },

    # ---- drop the unconfigured-branch shortcut (attacks C2) ----
    {
        "id": "unconditional-derivation",
        "kind": "uniqueness",
        "expect": "reject",
        # CONTROL-FLOW rival: remove the unconfigured branch entirely and derive
        # the threshold from the scores unconditionally. C1, C3, C4 and C5 hold;
        # C2 is violated, because the unconfigured case must return the constant.
        "module": _swap(
            _BASE, _I_TAIL,
            "  -- attack: no separate treatment of the unconfigured case — always\n"
            "  -- traverse the fitted model and derive the threshold from the scores.\n"
            "  Fitting.traverse x.values fun scores =>\n"
            "    let off := percentile scores (100.0 * contamination)\n"
            "    Fitting.done { offset := off, warned := false, reference := ref,\n"
            "                   scoreLater := scoreEntry ref }"),
        "refinement": "a counterpart that drops the unconfigured shortcut runs the "
                      "rank arithmetic on the unconfigured sentinel rather than on "
                      "a number, so fitting without a configured level raises "
                      "instead of selecting the fixed threshold; the large "
                      "PASS_TO_PASS body that fits at the default setting then "
                      "errors out, so it does NOT resolve. The two branches are "
                      "independent observables — the control-flow effect (was the "
                      "shortcut taken?) is invisible to C1, C3, C4 and C5 — so "
                      "only C2 pins it, exactly as the nagini biconditional pinned "
                      "whether the scoring path was reached.",
        "rationale": "REJECT from C2 (`contaminationAuto → offset = -0.5`): with "
                     "the branch removed the rival returns the derived percentile "
                     "on the unconfigured branch too. The witness instantiates the "
                     "unconfigured ARM at `contaminationAuto = true` — one of "
                     "three witnesses that do, and the only one attacking whether "
                     "the unconfigured branch is REACHED — and conditions on the "
                     "derived percentile differing from the fixed constant. "
                     "Refuted at `xOrig = {[2.0], 1, false}`, `contaminationAuto "
                     "= true`, `contamination = 0.25`. Ports the nagini "
                     "unconditional-scorer rival (there: calling the scorer "
                     "regardless of whether calibration was requested breaks the "
                     "biconditional).",
        "witness": _w_offset(
            "h : percentile (checked [2.0]) (100.0 * 0.25) ≠ -0.5",
            "[2.0]", "1", "false", "true", "0.25", "auto"),
    },
    # ---- the traversal hoisted above the branch (attacks C7) ----
    {
        "id": "traversal-hoisted-above-branch",
        "kind": "uniqueness",
        "expect": "reject",
        # The WORK-shaped rival, and the reason C7 exists. Derive the scores ONCE
        # up front and reuse them in whichever branch needs them. Every VALUE this
        # spec pins is untouched: the offset, the diagnostic, the record and its
        # enforcement are all identical to the frozen impl on every input, because
        # the unconfigured arm simply discards the binding. What changes is how
        # much work fitting does on the unconfigured branch — one traversal of the
        # fitted model where the frozen impl performs none.
        "module": _swap(
            _BASE, _I_TAIL,
            "  -- attack: traverse the fitted model ONCE up front, before the branch,\n"
            "  -- and reuse the scores in whichever branch needs them.\n"
            "  Fitting.traverse x.values fun scores =>\n"
            "    if contaminationAuto then\n"
            "      -- 0.5 plays a special role; we take the opposite. The scores this\n"
            "      -- arm was handed are simply discarded.\n"
            "      Fitting.done { offset := -0.5, warned := false, reference := ref,\n"
            "                     scoreLater := scoreEntry ref }\n"
            "    else\n"
            "      let off := percentile scores (100.0 * contamination)\n"
            "      Fitting.done { offset := off, warned := false, reference := ref,\n"
            "                     scoreLater := scoreEntry ref }"),
        "refinement": "a counterpart that derives the anomaly scores before "
                      "deciding whether they are needed traverses the fitted model "
                      "on a default fit that never uses them. The values it "
                      "produces are right, so it PASSES the FAIL_TO_PASS test — "
                      "and the PASS_TO_PASS bodies that pin how many times the "
                      "chunked scoring path is entered for a default fit observe "
                      "one traversal more than they expect and fail, so it does "
                      "NOT resolve. Measured on the real repository in exactly "
                      "this shape: FAIL_TO_PASS passes, four PASS_TO_PASS tests "
                      "fail. This is verify-not-resolve on an observable no "
                      "value-shaped clause can see, which is why the amount of "
                      "scoring work fitting performs is part of the contract and "
                      "not an implementation detail.",
        "rationale": "REJECT from C8 (`fitting.traversals = bif "
                     "contaminationAuto then [] else [checked xOrig.values]`). C1 "
                     "through C7 ALL hold, "
                     "and not approximately: this rival is definitionally equal to "
                     "the frozen impl in every field those clauses mention, so no "
                     "conjunct over the offset, the diagnostic, the record or its "
                     "enforcement can refute it — which is precisely the hole C8 "
                     "closes. Witnessed on the UNCONFIGURED branch, the only "
                     "branch where the two differ, at `xOrig = {[1.25], 2, "
                     "false}`, `contaminationAuto = true`, `contamination = 0.35`: "
                     "the rival reports one traversal where the clause pins none. "
                     "Note the rival cannot escape by REPORTING a different "
                     "number than it performs: the traversals are read off the "
                     "program's structure by `Fitting.traversals`, which lives in "
                     "the frozen spec region, and `traverse` is the only way to "
                     "reach anomaly scores at all — so there is no field for a "
                     "rival to write.",
        "witness": _w_traversals("[1.25]", "2", "false", "true", "0.35"),
    },

    # ---- an extra discarded traversal (attacks C8 on the CONFIGURED branch) ----
    {
        "id": "extra-discarded-traversal",
        "kind": "uniqueness",
        "expect": "reject",
        # C8's other branch. `traversal-hoisted-above-branch` moves work onto the
        # unconfigured branch and is exactly right on the configured one, so it
        # cannot show C8 enforced where a threshold level IS configured. This
        # rival keeps the unconfigured branch frozen and spends one extra
        # traversal on the configured one, discarding its result.
        "module": _swap(
            _BASE, _I_TRAVERSE,
            "    -- attack: traverse the fitted model once as a warm-up, discard the\n"
            "    -- scores it yields, then traverse it again for the threshold.\n"
            "    Fitting.traverse x.values fun _warm =>\n"
            "    Fitting.traverse x.values fun scores =>"),
        "refinement": "a counterpart that traverses the fitted model an extra time "
                      "and throws the result away computes exactly the right "
                      "threshold and emits no diagnostic, so it PASSES the "
                      "FAIL_TO_PASS test, and doubles the scoring work a "
                      "configured fit costs. The PASS_TO_PASS bodies that pin how "
                      "many times the chunked scoring path is entered for a "
                      "configured fit observe twice what they expect and fail, so "
                      "it does NOT resolve — measured on the real repository in "
                      "this shape: FAIL_TO_PASS passes, two PASS_TO_PASS tests "
                      "fail. A discarded traversal is invisible to every value in "
                      "the result, so only the traversal count can catch it.",
        "rationale": "REJECT from C8, on its CONFIGURED branch rather than its "
                     "unconfigured one. The sibling work-shaped rival hoists the "
                     "traversal and so is exact wherever a threshold level is "
                     "configured; this one is exact on the unconfigured branch and "
                     "spends two traversals where the clause pins one. Two "
                     "distinct wrong implementations refuted by one clause on its "
                     "two different branches, so C8 is not a restatement of either "
                     "rival's spelling. Like its sibling it is definitionally "
                     "equal to the frozen impl in every field C1 through C7 "
                     "mention. Witnessed at `xOrig = {[7.5], 3, true}`, "
                     "`contaminationAuto = false`, `contamination = 0.3`.",
        "witness": _w_traversals("[7.5]", "3", "true", "false", "0.3"),
    },

    # ---- work counted but not USED: a decorative traversal (attacks C3) ----
    {
        "id": "uncounted-work-off-structure",
        "kind": "uniqueness",
        "expect": "reject",
        # The audited counterexample that survives the scope repair, re-expressed
        # with what a variant can still name. It spends exactly the traversal C8
        # pins, over exactly the payload C8 names, and then IGNORES the scores that
        # traversal handed its continuation, deriving the threshold from the
        # payload itself. C8 is satisfied; the traversal is decoration.
        "module": _swap(
            _swap(_BASE, _I_TRAVERSE,
                  "    -- attack: keep the traversal node, so the work is counted\n"
                  "    -- exactly as the contract asks, and then ignore what it yields.\n"
                  "    Fitting.traverse x.values fun _scores =>"),
            _I_OFF,
            "      -- attack: derive the threshold from the payload rather than from\n"
            "      -- the scores the traversal handed us.\n"
            "      let off := percentile x.values (100.0 * contamination)"),
        "refinement": "a counterpart that enters the chunked scoring path the right "
                      "number of times over the right data and then computes the "
                      "threshold from the data instead of from the anomaly scores "
                      "that path returned puts the threshold at the configured rank "
                      "of the WRONG sample — the raw feature values rather than the "
                      "per-sample scores of the fitted trees. It emits no "
                      "diagnostic, keeps the right description, and spends the "
                      "traversals the chunking tests count, so it PASSES the "
                      "FAIL_TO_PASS test and every test that observes the traversal "
                      "count; the PASS_TO_PASS bodies that read decisions or "
                      "predictions off the threshold observe the wrong cut and it "
                      "does NOT resolve. This is the shape the audit found "
                      "surviving a work-count clause: the count can be paid in full "
                      "while the work is thrown away.",
        "rationale": "REJECT from C3, and from C3 ALONE — C1, C2, C4, C5, C6, C7 "
                     "and C8 all hold, C8 exactly (the traversal list is the "
                     "frozen one). It is the case that shows C3 binds the "
                     "threshold to THE SCORES THAT TRAVERSAL YIELDED and not "
                     "merely to a percentile of the right payload. It is also the "
                     "one witness the identity interpretation cannot refute: under "
                     "`sc = fun v => v` the scores of a payload ARE that payload, "
                     "so this rival AGREES with C3 there, and the witness "
                     "instantiates the quantified interpretation at a non-identity "
                     "one instead (`fun v => (0.0 : Float) :: v`) — which is what "
                     "quantifying over the interpretation buys that any single "
                     "scoring function would not. The hypothesis conditions only on "
                     "the two `percentile` applications differing at the probed "
                     "input. Refuted at `xOrig = {[2.5, 6.5], 2, false}`, "
                     "`contaminationAuto = false`, `contamination = 0.35`.",
        "witness": _w_offset(
            "h : percentile (checked [2.5, 6.5]) (100.0 * 0.35)\n"
            "      ≠ percentile ((0.0 : Float) :: checked [2.5, 6.5]) (100.0 * 0.35)",
            "[2.5, 6.5]", "2", "false", "false", "0.35", "configured",
            sc="(fun v => (0.0 : Float) :: v)"),
    },

    # ---- the storage-form guard read the wrong way round (attacks C8) ----
    {
        "id": "sparse-guard-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # The reject-lane control for the storage-form guard on C3/C8, and the
        # reason narrowing those clauses is not the same as dropping them. This
        # rival reads the guard as a general licence to skip the work: it spends
        # the traversal on exactly the carriers the description says nothing about
        # (sparse, configured) and takes the threshold from a constant on the
        # carriers it does describe. Everything C1, C2, C4, C5, C6 and C7 mention
        # is the frozen value; only the work and the derived threshold move, and
        # they move on the DENSE branch, where the description still applies in
        # full.
        "module": _swap(
            _BASE, _I_ELSE,
            "  else if !(Form.reshaped xOrig.form Form.sparseByColumn).traversable then\n"
            "    -- attack: read the storage-form limit as a general licence — spend the\n"
            "    -- traversal only where the description withholds its claims, and take\n"
            "    -- the threshold from a constant where it does not.\n"
            + _I_TRAVERSE + "\n" + _I_OFF + "\n" + _I_RET + "\n"
            "  else\n"
            "    Fitting.done { offset := 0.0, warned := false, reference := ref,\n"
            "                   scoreLater := scoreEntry ref }"),
        "refinement": "a counterpart that derives the threshold only from sparse "
                      "training data and hands a dense fit a constant threshold "
                      "never enters the chunked scoring path for the ordinary "
                      "dense configured fit at all. The PASS_TO_PASS bodies that "
                      "count how many times that path is entered for a configured "
                      "fit on dense data observe one entry fewer than they expect, "
                      "and the bodies that read decisions or predictions off a "
                      "correctly derived threshold observe the constant cut "
                      "instead, so it does NOT resolve — while emitting no "
                      "diagnostic and keeping the right record, so it would still "
                      "pass the FAIL_TO_PASS test. It is the wrong reading of a "
                      "domain limit rather than of a value: the limit says the "
                      "traversal is impossible on one storage form, not that it is "
                      "optional on the other.",
        "rationale": "REJECT from C8 on its DENSE branch, which is what shows the "
                     "storage-form guard on C3/C8 is a narrowing and not a hole. "
                     "The guard withholds both clauses exactly where the real "
                     "patched code produces nothing to describe (sparse carrier, "
                     "configured threshold level); this rival takes that as "
                     "permission to withhold the WORK where the clauses do apply, "
                     "and C8 refutes it at a dense carrier — the traversal list is "
                     "empty where the clause pins one traversal over the checked "
                     "training payload. Transparent, so no hypothesis: the witness "
                     "discharges C8's storage-form antecedent by `decide` at a "
                     "dense literal carrier and projects `List.length` off the "
                     "traversal list. Together with `pos-sparse-declines-threshold` "
                     "this pins the guard from both sides — an impl that declines "
                     "the threshold where the traversal is impossible verifies, and "
                     "one that declines it anywhere else does not. Refuted at "
                     "`xOrig = {[3.5, 1.5], 4, false}` (dense), "
                     "`contaminationAuto = false`, `contamination = 0.4`.",
        "witness": _w_traversals("[3.5, 1.5]", "4", "false", "false", "0.4"),
    },

    # ---- the aborted run treated as unconstrained (attacks C1) ----
    {
        "id": "sparse-abort-emits-diagnostic",
        "kind": "uniqueness",
        "expect": "reject",
        # The other reject-lane control for the storage-form guard: it bounds the
        # guard to the TWO clauses that carry it. C3 and C8 say nothing about a
        # sparse configured fit; C1, C4, C5, C6 and C7 still do, because an
        # aborted run is nevertheless observed to emit no feature-name diagnostic
        # and to leave the record it established behind. This rival reads the
        # withheld threshold as a withheld run — it declines the threshold
        # (which is allowed) and surfaces the consistency diagnostic on the way
        # out (which is not). Only `warned` moves, and only on the carrier the
        # guard is about.
        "module": _swap(
            _BASE, _I_ELSE,
            "  else if !(Form.reshaped xOrig.form Form.sparseByColumn).traversable then\n"
            "    -- attack: read the withheld threshold as a withheld run and report the\n"
            "    -- feature-name-consistency diagnostic on the way out of the abort.\n"
            "    Fitting.done { offset := 0.0, warned := true, reference := ref,\n"
            "                   scoreLater := scoreEntry ref }\n"
            + _I_ELSE),
        "refinement": "a counterpart that raises the feature-name-consistency "
                      "warning when a configured fit is handed data in the sparse "
                      "storage form emits exactly the diagnostic this change "
                      "removes, on exactly the estimator state where the reported "
                      "defect was observed. The FAIL_TO_PASS body promotes that "
                      "warning to an error, so a sparse presentation of a "
                      "name-carrying configured fit fails there, and the "
                      "PASS_TO_PASS bodies that fit sparse data under a warning "
                      "filter fail as well. The run aborting later does not make "
                      "what it did before aborting unobservable.",
        "rationale": "REJECT from C1 on the SPARSE branch, which is the control "
                     "that the storage-form guard is scoped to C3 and C8 and does "
                     "not excuse the aborted run generally. C1 carries no "
                     "antecedent at all — neither the branch guard nor "
                     "`fitCompletes` — so it is asked of every carrier including "
                     "this one, and the witness is presented in the sparse form to "
                     "show it. Transparent, so no hypothesis: `warned` reduces "
                     "under `simp` at the literal carrier. This is the third side "
                     "of the boundary that `pos-sparse-declines-threshold` "
                     "(declining the threshold there MUST verify) and "
                     "`sparse-guard-inverted` (declining the work anywhere else "
                     "must not) pin from the other two. Refuted at "
                     "`xOrig = {[3.5, 1.5], 4, false, sparse}`, "
                     "`contaminationAuto = false`, `contamination = 0.4`.",
        "witness": _w_warned("[3.5, 1.5]", "4", "false", "false", "0.4",
                             form="Form.sparseByColumn", layout_branch=True),
    },

    # ---- refuse everything, which satisfies C5 vacuously (attacks C6) ----
    {
        "id": "later-scoring-refuses-everything",
        "kind": "uniqueness",
        "expect": "reject",
        # The rival that C5's one-directional `refused` leg admits and C6 exists
        # to reject. C5 obliges the estimator to turn away a carrier of a
        # disagreeing width; it does NOT say a carrier of the agreeing width is
        # accepted, because real inadmissibility has causes this model does not
        # carry. An estimator that turns EVERYTHING away satisfies that
        # obligation vacuously while being useless.
        "module": _swap(
            _BASE, _I_ENTRY_BODY,
            "  -- attack: turn away every carrier handed to the fitted estimator,\n"
            "  -- which discharges the obligation to refuse disagreeing widths\n"
            "  -- without ever accepting anything.\n"
            "  let v := validateInput z false ref Form.sparseByRow\n"
            "  { refused := true, warned := v.warned, refAfter := v.refAfter,\n"
            "    handedOn := v.carrier }"),
        "refinement": "a counterpart whose fitted estimator rejects every batch "
                      "handed to it, including a batch identical to the one it was "
                      "fitted on, cannot be scored or predicted with at all. It "
                      "changes nothing about fitting, so it would PASS the "
                      "FAIL_TO_PASS test, and every PASS_TO_PASS body that fits "
                      "and then scores or predicts raises instead of returning. "
                      "The obligation to turn away a mismatched batch has to be "
                      "paired with the guarantee that the training batch itself "
                      "stays acceptable, or refusing everything reads as "
                      "compliance.",
        "rationale": "REJECT from C6 (`(result.scoreLater xOrig).refused = "
                     "false`), and ONLY from C6. C5's `refused` leg is stated as a "
                     "one-directional obligation — a disagreeing width MUST be "
                     "turned away — because the real estimator refuses same-width "
                     "carriers for reasons this carrier does not model, so the "
                     "converse would be too strong. That weakening is what makes "
                     "this rival possible, and C6 is what closes it: the training "
                     "carrier must remain admissible to the estimator fitted on "
                     "it. C1 through C5, C7 and C8 all hold (its handed-on leg "
                     "vacuously: this rival refuses everything). Witnessed at `xOrig = "
                     "{[2.5], 4, false}`, `contaminationAuto = false`, "
                     "`contamination = 0.4`.",
        "witness": _w_admits("[2.5]", "4", "false", "false", "0.4"),
    },
    {
        "id": "names-treated-as-inadmissibility",
        "kind": "uniqueness",
        "expect": "reject",
        # The rival that survives BOTH C5's one-directional `refused` leg and
        # C6's single-point admissibility guarantee. It turns away any carrier
        # whose feature-name status disagrees with the record. That predicate is
        # FALSE at the training carrier itself, so C6 cannot see it, and it only
        # ever refuses MORE than C5 obliges, so C5 cannot see it either. It is
        # nevertheless wrong: a naming disagreement is a matter for the warning,
        # never a ground for turning a carrier away.
        "module": _swap(
            _BASE, _I_ENTRY_BODY,
            "  -- attack: escalate a feature-name disagreement from a warning\n"
            "  -- into a refusal. Vanishes at the training carrier, so a\n"
            "  -- single-point admissibility guarantee is blind to it.\n"
            "  let v := validateInput z false ref Form.sparseByRow\n"
            "  { refused := v.refused || (ref.hasFeatureNames != z.hasFeatureNames),\n"
            "    warned := v.warned, refAfter := v.refAfter,\n"
            "    handedOn := v.carrier }"),
        "refinement": "a counterpart that raises instead of scoring whenever the "
                      "batch's feature-name status differs from the fitted "
                      "estimator's would still emit the warning the fix is about, "
                      "so it could pass the FAIL_TO_PASS body, but every "
                      "PASS_TO_PASS body that fits on a labelled table and then "
                      "scores a bare numeric array — or fits on an array and "
                      "scores a labelled table — raises instead of returning a "
                      "score. The real estimator warns in exactly those cases and "
                      "carries on.",
        "rationale": "REJECT from C7 (a carrier whose content the check accepts, "
                     "at the training width, is admitted), and ONLY from C7. "
                     "C5's `refused` leg is one-directional, so refusing MORE is "
                     "invisible to it; C6 pins admissibility only at `xOrig`, "
                     "where this rival's extra refusal predicate is false by "
                     "construction. C7 is what states the behavior: feature-name "
                     "metadata is never itself a ground for refusal. C1-C6 and C8 "
                     "all hold. Witnessed at `xOrig = {[1.0], 2, true}`, "
                     "`contaminationAuto = false`, `contamination = 0.3`, with a "
                     "same-width unlabelled carrier.",
        "witness": _w_names_not_refusal("[1.0]", "2", "true", "false", "0.3"),
    },
    {
        "id": "content-rewrite-treated-as-inadmissibility",
        "kind": "uniqueness",
        "expect": "reject",
        # THE RIVAL THAT SURVIVES EVERY OTHER CLAUSE by refusing exactly the
        # carriers the description used to say nothing about. Its extra refusal
        # predicate is "the admissibility check did not hand this content back as
        # it found it". That predicate is FALSE at the training carrier — fitting
        # already re-presented it, so it is a fixed point of the callee there — so
        # C6 cannot see it; it only ever refuses MORE than C5's one-directional
        # `refused` leg obliges, so C5 cannot see it; and it changes nothing about
        # the fit, so C1-C4 and C8 cannot see it. C7 is the only clause that can,
        # and it can only do so because its region covers content the check
        # REWRITES as well as content it leaves alone. This case is why the
        # fixed-point antecedent C7 used to carry is not there: with it, this rival
        # verified.
        "module": _swap(
            _BASE, _I_ENTRY_BODY,
            "  -- attack: escalate 'the check had to convert this content' from a\n"
            "  -- conversion into a refusal. Vanishes at the training carrier, whose\n"
            "  -- content fitting already re-presented, so a single-point admissibility\n"
            "  -- guarantee is blind to it.\n"
            "  let v := validateInput z false ref Form.sparseByRow\n"
            "  { refused := v.refused || (z.values != checked z.values),\n"
            "    warned := v.warned, refAfter := v.refAfter,\n"
            "    handedOn := v.carrier }"),
        "refinement": "a counterpart that turns away every carrier whose content "
                      "the admissibility check has to convert refuses exactly what "
                      "the check exists to accept: a float64 array presented to a "
                      "float32-typed check, an integer array, a list of lists, a "
                      "frame — all of them content the real estimator converts and "
                      "then scores. It changes nothing about fitting and emits no "
                      "diagnostic, so it would PASS the FAIL_TO_PASS test, while "
                      "every PASS_TO_PASS body that fits and then scores content in "
                      "any presentation other than the one the check already "
                      "settled on raises instead of returning — a verify-not-resolve "
                      "break, and one measured on the real repository rather than "
                      "argued: with this rival's predicate in the patched entry "
                      "point the failing test still passes while a third of the "
                      "regression bodies that score converted content stop, and the "
                      "gold change leaves all of them passing.",
        "rationale": "REJECT from C7, and ONLY from C7 — on the part of C7's region "
                     "that a fixed-point antecedent would have removed. C5's "
                     "`refused` leg is one-directional, so refusing MORE is "
                     "invisible to it; C6 pins admissibility only at `xOrig`, where "
                     "this rival's extra predicate is false because fitting has "
                     "already re-presented that carrier's content; C1-C4 and C8 are "
                     "about the fit, which this rival leaves verbatim. C7 states the "
                     "behavior: a carrier whose content the check ACCEPTS is "
                     "admitted, whether or not the check rewrites it, so having to "
                     "convert content is never itself a ground for turning a carrier "
                     "away. The witness conditions on ONE hypothesis about ONE "
                     "payload — that the check does not hand that payload back as it "
                     "found it — which is the sub-domain where the rival is wrong, "
                     "and it is a measured property of the real callee "
                     "(axiom_check.py's handed-on leg presents a float64 column to "
                     "the float32-typed check and compares what comes back, with the "
                     "already-converted payload as the control that the disequality "
                     "is not universal). Nothing is assumed about WHAT the check "
                     "returns, and in particular the bundle's one axiom "
                     "(`checked_idem`) does not supply this hypothesis. Refuted at "
                     "`xOrig = {[4.5], 2, true}`, `contaminationAuto = false`, "
                     "`contamination = 0.42`, with a same-width unlabelled carrier "
                     "whose payload is an ordinary one.",
        "witness": _w_rewritten_content_admitted(
            "h : ([9.5] != checked [9.5]) = true",
            "[4.5]", "2", "true", "false", "0.42", "[9.5]"),
    },
    {
        "id": "later-scoring-admits-uninspectable",
        "kind": "uniqueness",
        "expect": "reject",
        # THE REJECT-LANE CONTROL FOR THE INSPECTABILITY LEG, and the rival the
        # ABSTRACTION-COLLAPSE reading licenses. If the model's `hasFeatureNames`
        # is read as total — every carrier has a feature-name status, so a carrier
        # whose labels the estimator cannot inspect is just another carrier — then
        # the fitted estimator may treat it as one: check its width, report the
        # name diagnostic, hand it on. The real estimator does not: the label
        # inspection RAISES first, so the carrier is turned away whatever its
        # width and whatever the estimator holds on record. Everything else about
        # this rival is the frozen value, so only C5's fifth leg can see it.
        "module": _swap(
            _BASE, _I_ENTRY_BODY,
            "  -- attack: treat a carrier whose labels the estimator cannot inspect as\n"
            "  -- an ordinary carrier — check its width, report the name diagnostic and\n"
            "  -- hand it on. Only the inspection ground is dropped from the refusal.\n"
            "  let v := validateInput z false ref Form.sparseByRow\n"
            "  { refused := (z.nFeatures != ref.nFeatures), warned := v.warned,\n"
            "    refAfter := v.refAfter, handedOn := v.carrier }"),
        "refinement": "a counterpart whose fitted estimator swallows the label "
                      "inspection's failure and carries on scores a table whose "
                      "column labels it could not read against a record it cannot "
                      "compare them to — the estimator's feature-name agreement is "
                      "silently not enforced for exactly the carriers where it "
                      "cannot be evaluated. It changes nothing about fitting, so it "
                      "would PASS the FAIL_TO_PASS test. The reason it does not "
                      "refine the patched code is measured rather than argued, and "
                      "the measurement is of the callee this model abstracts: "
                      "`_get_feature_names` — the step `hasFeatureNames` stands for "
                      "— RAISES `TypeError` on labels of mixed kinds, at fit time "
                      "and through the fitted estimator's public scoring path "
                      "alike, for an estimator fitted on a labelled frame and for "
                      "one fitted on a bare array (axiom_check.py leg L; "
                      "conformance_check.py asserts it against the patched "
                      "estimator on every draw). So the refusal is UNCONDITIONAL in "
                      "the real code, and a counterpart that returns a score there "
                      "is not a refinement of this tail at all — it has invented an "
                      "outcome the patched estimator does not produce.",
        "rationale": "REJECT from C5's FIFTH leg (`z.namesInspectable = false → "
                     "(result.scoreLater z).refused = true`), and ONLY from it. The "
                     "rival is definitionally the frozen impl in the diagnostic, "
                     "the record and the handed-on carrier, and its refusal agrees "
                     "with the frozen one on every carrier the estimator inspects — "
                     "so C1-C4, C6, C7 and C8 all hold, and C5's own width leg "
                     "holds too (a disagreeing width is still turned away). This is "
                     "the rival the ABSTRACTION-COLLAPSE reading admits, which is "
                     "why the inspectability distinction is carried as a field and "
                     "the requirement is stated POSITIVELY rather than left as "
                     "silence: withholding the claim would license exactly this "
                     "implementation. Transparent, so no hypothesis: the witness "
                     "instantiates C5 at a probe carrier of the TRAINING width "
                     "whose labels the estimator will not inspect — the training "
                     "width deliberately, so the width leg cannot be what refuses "
                     "it and the inspection ground is the only thing separating the "
                     "two impls — discharges the leg's guard by `decide` and decides "
                     "the boolean clash. Refuted at `xOrig = {[6.5], 5, true}`, "
                     "`contaminationAuto = false`, `contamination = 0.05` with the "
                     "probe carrier `z = ([5.5], 5, false, not inspectable)`.",
        "witness": _w_later(
            "inspect",
            "{ values := [5.5], nFeatures := 5, hasFeatureNames := false, form := Form.dense, namesInspectable := false, contentAdmissible := true }",
            "[6.5]", "5", "true", "false", "0.05"),
    },
    {
        "id": "later-scoring-admits-inadmissible-content",
        "kind": "uniqueness",
        "expect": "reject",
        # THE REJECT-LANE CONTROL FOR THE CONTENT LEG. If the model's carrier is
        # read as holding only content the check accepts, then the fitted
        # estimator's entry point may treat a carrier it does NOT accept as an
        # ordinary one: check its width, report the name diagnostic, hand it on.
        # The real entry point does not — the re-presentation raises, so the
        # carrier is turned away whatever its width and whatever the estimator
        # holds on record. Everything else about this rival is the frozen value, so
        # only C5's sixth leg can see it. Note what it deliberately KEEPS: the
        # label-inspection ground and the width ground are both still enforced, so
        # C5's own width leg and its fifth leg hold and the sixth leg is the only
        # thing separating the two impls.
        "module": _swap(
            _BASE, _I_ENTRY_BODY,
            "  -- attack: treat a carrier whose content the check does not accept as an\n"
            "  -- ordinary carrier — check its width, report the name diagnostic and hand\n"
            "  -- it on. Only the content ground is dropped from the refusal.\n"
            "  let v := validateInput z false ref Form.sparseByRow\n"
            "  { refused := (!z.namesInspectable || (z.nFeatures != ref.nFeatures)),\n"
            "    warned := v.warned, refAfter := v.refAfter,\n"
            "    handedOn := v.carrier }"),
        "refinement": "a counterpart whose fitted estimator swallows the "
                      "re-presentation's failure and carries on hands the fitted "
                      "ensemble content the estimator never accepted — an empty "
                      "batch, a batch of no width, or one holding a non-finite "
                      "value — so the trees are traversed over an object the "
                      "estimator's own admissibility check exists to keep out. It "
                      "changes nothing about fitting, so it would PASS the "
                      "FAIL_TO_PASS test. The reason it does not refine the patched "
                      "code is measured rather than argued, and the measurement is "
                      "of the callee this model abstracts: the score-time "
                      "`_validate_data(..., reset=False)` call RAISES on each of "
                      "those three contents, for an estimator fitted on a labelled "
                      "frame and for one fitted on a bare array alike, at every "
                      "width tried (axiom_check.py leg D's score-time legs; "
                      "conformance_check.py asserts it against the patched "
                      "estimator on every draw). So the refusal is UNCONDITIONAL in "
                      "the real code, and a counterpart that returns a score there "
                      "has invented an outcome the patched estimator does not "
                      "produce.",
        "rationale": "REJECT from C5's SIXTH leg (`z.contentAdmissible = false → "
                     "(result.scoreLater z).refused = true`), and ONLY from it. The "
                     "rival is definitionally the frozen impl in the diagnostic, "
                     "the record and the handed-on carrier, and its refusal agrees "
                     "with the frozen one on every carrier whose content the check "
                     "accepts — so C1-C4, C6, C7 and C8 all hold, and C5's width "
                     "and inspection legs hold too. This is the rival that "
                     "withholding the claim would license: C5's `refused` leg is "
                     "one-directional and C6 pins admissibility only at `xOrig`, "
                     "whose content fitting already re-presented, so nothing else "
                     "in the description can reach an entry point that drops this "
                     "ground. Transparent, so no hypothesis: the witness "
                     "instantiates C5 at a probe carrier of the TRAINING width, "
                     "whose labels the estimator WILL inspect and whose content it "
                     "will NOT accept — the training width and the inspectable "
                     "labels deliberately, so neither of the other two grounds can "
                     "be what refuses it — discharges the leg's guard by `decide` "
                     "and decides the boolean clash. Refuted at `xOrig = {[7.25], "
                     "3, false}`, `contaminationAuto = true`, `contamination = "
                     "0.15` with the probe carrier `z = ([2.75], 3, false, "
                     "inspectable, content not accepted)`.",
        "witness": _w_later(
            "content",
            "{ values := [2.75], nFeatures := 3, hasFeatureNames := false, form := Form.dense, namesInspectable := true, contentAdmissible := false }",
            "[7.25]", "3", "false", "true", "0.15"),
    },
    {
        "id": "prenormalization-payload-scored",
        "kind": "uniqueness",
        "expect": "reject",
        # Traverse the CALLER'S OWN payload rather than the payload the
        # admissibility check handed on. One traversal either way, at the right
        # rank, over the right sample — the only error is the PRESENTATION of the
        # content scored. This is the nagini `raw-matrix-out-of-domain` rival,
        # which two earlier audits carried as DROPPED-vacuous on the (then true)
        # grounds that the modeled validation step changed only the metadata flag
        # and carried `values` through untouched. The deep model no longer does
        # that: validation RE-PRESENTS the payload (`carrier.values = checked
        # x.values`, validated against the real `check_array` by G-AX), so the
        # distinction is kept on this carrier and the rival is refutable.
        "module": _swap(
            _BASE, _I_TRAVERSE,
            "    -- attack: traverse the caller's own payload instead of the payload\n"
            "    -- the admissibility check handed on. Same sample, same rank, one\n"
            "    -- traversal either way — but not the same presentation of the\n"
            "    -- content, so the scores are taken over the wrong object.\n"
            "    Fitting.traverse xOrig.values fun scores =>"),
        "refinement": "a counterpart that hands the fitted ensemble the caller's "
                      "own object rather than the array `_validate_data` returned "
                      "scores un-converted content — which is precisely what the "
                      "`check_array` call at the top of `fit` exists to prevent: a "
                      "sparse carrier arrives in the wrong sparse format for the "
                      "scoring path, a frame arrives as a frame, and a float64 "
                      "array is scored at a different precision than the trees "
                      "were fitted at. The threshold then sits at the configured "
                      "rank of a DIFFERENT score sample than the fitted model "
                      "produces. It emits no diagnostic and records the right "
                      "description, so it would pass the FAIL_TO_PASS test — a "
                      "verify-not-resolve break if C3 named the caller's payload "
                      "instead of the checked one (`test_iforest_sparse` is the "
                      "PASS_TO_PASS body that observes the format leg).",
        "rationale": "REJECT from C3, and independently from C8: the spec pins "
                     "`percentile (sc (checked xOrig.values)) …` and pins "
                     "the traversed payload to `checked xOrig.values`, while the "
                     "rival computes and traverses `xOrig.values`. Nothing is "
                     "assumed about what `checked` returns, nor about the "
                     "interpretation of the scoring effect — in "
                     "particular NOT that `checked` is the identity, which is "
                     "exactly the claim this rival needs and the bundle's only "
                     "axiom (`checked_idem`) does not supply. The witness "
                     "conditions only on the two applications differing at the "
                     "probed input. Refuted at `xOrig = {[3.25, 4.75], 2, true}`, "
                     "`contaminationAuto = false`, `contamination = 0.28` — a fresh "
                     "payload, and the only witness at that rank, so the point is "
                     "distinct from every other in the battery. C1, C2, C4, C5, C6 "
                     "and C7 all hold.",
        "witness": _w_offset(
            "h : percentile ([3.25, 4.75]) (100.0 * 0.28)\n"
            "      ≠ percentile (checked [3.25, 4.75]) (100.0 * 0.28)",
            "[3.25, 4.75]", "2", "true", "false", "0.28", "configured"),
    },

    # =====================================================================
    # SCORE-TIME WORK (attacks C5's seventh leg). The four rivals below move
    # WORK at the fitted estimator's public scoring entry point rather than
    # values, which is the other end of the tail the fit-side work rivals
    # (`traversal-hoisted-above-branch`, `extra-discarded-traversal`) cover.
    # Every clause over what the call REPORTS is blind to all four: each one
    # returns the same `ScoreOutcome` as the frozen entry point on every
    # carrier, so C5's first six legs, C6 and C7 hold exactly, and the fit
    # itself is untouched so C1-C4 and C8 hold exactly. The traversals are read
    # off the score-time program's STRUCTURE, which is what makes them
    # refutable at all: there is no field for such a rival to report a number
    # into that differs from the number it performs.
    #
    # WHY THE REAL REPOSITORY DISTINGUISHES THEM. Presenting one carrier to a
    # fitted estimator through its public scoring entry point enters the
    # chunked scoring path exactly once for a carrier it accepts, and not at
    # all for a carrier it turns away (the entry point raises out of the
    # consistency re-check, before any scoring). The PASS_TO_PASS bodies that
    # count how many times the chunk-sizing helper is consulted assert the
    # TOTAL over a fit followed by a fixed number of scoring calls, so a rival
    # that spends a second pass per call, spends one before deciding, spends one
    # on a carrier it refuses, or spends none on one it accepts, observes a
    # different total and fails them — while computing every value correctly and
    # so still passing the FAIL_TO_PASS test.
    # =====================================================================

    # ---- a warm-up pass at score time (attacks C5 leg 7, accepting lane) ----
    {
        "id": "score-warmup-traversal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_ENTRY_PROGRAM,
            "def scoreEntry (ref : Reference) (z : InputData) : Scored :=\n"
            "  let r := scoreReport ref z\n"
            "  -- attack: score the accepted carrier once as a warm-up, discard what\n"
            "  -- that pass yields, then score it again and report on that. Every\n"
            "  -- value this call reports is the frozen one; only the cost differs.\n"
            "  bif r.refused then Scored.done r\n"
            "    else Scored.traverse r.handedOn.values (fun _ =>\n"
            "           Scored.traverse r.handedOn.values (fun _ => Scored.done r))"),
        "refinement": "a counterpart whose public scoring entry point scores the "
                      "carrier once as a warm-up and throws the result away, then "
                      "scores it again, reports exactly the values the real entry "
                      "point reports: same decision on whether to turn the carrier "
                      "away, same feature-name diagnostic, same record afterwards, "
                      "same content handed to the fitted model, same anomaly scores "
                      "returned. It therefore PASSES the FAIL_TO_PASS test. What it "
                      "changes is what one such call COSTS: the chunked scoring path "
                      "is entered twice per accepted carrier instead of once, so the "
                      "PASS_TO_PASS bodies that assert how many times the chunk-sizing "
                      "helper is consulted across a fit plus a fixed number of scoring "
                      "calls observe more consultations than they expect and fail. "
                      "This is the shape a previous audit measured on the real "
                      "repository at this instance: FAIL_TO_PASS 1/1 passes and four "
                      "PASS_TO_PASS chunking bodies fail, so it does NOT resolve.",
        "rationale": "REJECT from C5's seventh leg, and from that leg ALONE. The "
                     "rival is definitionally the frozen entry point in every field "
                     "any clause over the REPORT mentions — legs 1 through 6, C6 and "
                     "C7 all hold exactly, and the fit is verbatim so C1-C4 and C8 "
                     "hold exactly. It is the score-side counterpart of "
                     "`extra-discarded-traversal`: the same 'spend a pass and throw "
                     "it away' error, at the other end of the same tail, and the "
                     "reason the entry point is modeled as a PROGRAM rather than as a "
                     "plain function to a report. Against a description in which the "
                     "entry point returns only a report, this rival is not merely "
                     "admitted, it is the SAME Lean term as the frozen one — which is "
                     "what makes reading the cost off the program's structure the "
                     "only available refutation and not one spelling among several. "
                     "Refuted on the ACCEPTING lane, where the leg pins exactly one "
                     "traversal, by projecting the LENGTH out of the leg's list "
                     "equation, so nothing is assumed about the re-presentation "
                     "callee's value. Witnessed at `xOrig = {[5.5], 3, false}`, "
                     "`contaminationAuto = false`, `contamination = 0.22`, probed "
                     "with a same-width nameless carrier the entry point accepts.",
        "witness": _w_score_traversals("[5.5]", "3", "false", "false", "0.22"),
    },

    # ---- scoring before deciding whether to refuse (C5 leg 7, refusing lane) ----
    {
        "id": "score-before-deciding",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_ENTRY_PROGRAM,
            "def scoreEntry (ref : Reference) (z : InputData) : Scored :=\n"
            "  -- attack: score the carrier FIRST and only then consult the\n"
            "  -- consistency re-check about whether to turn it away. The report is\n"
            "  -- the frozen one on every carrier; what changes is that a carrier the\n"
            "  -- entry point turns away has already been scored by then.\n"
            "  Scored.traverse (checked z.values) (fun _ =>\n"
            "    Scored.done (scoreReport ref z))"),
        "refinement": "a counterpart that scores the carrier before deciding whether "
                      "to turn it away reports exactly what the real entry point "
                      "reports on every carrier — it still refuses the ones the "
                      "consistency re-check refuses, still warns where it warns, "
                      "still hands on the same content — so it PASSES the "
                      "FAIL_TO_PASS test. What it changes is that a REFUSED "
                      "presentation now costs a pass through the chunked scoring "
                      "path, where the real entry point raises out of the re-check "
                      "before any scoring happens. Every PASS_TO_PASS body that "
                      "presents a carrier the estimator rejects and then counts how "
                      "many times the chunk-sizing helper was consulted observes one "
                      "more than it expects; so does any body that measures the cost "
                      "of a rejected call. It does NOT resolve.",
        "rationale": "REJECT from C5's seventh leg on its REFUSING lane, which is "
                     "the lane `score-warmup-traversal` cannot reach: that rival is "
                     "exactly right wherever the entry point turns a carrier away, "
                     "and this one is exactly right wherever it accepts. Two "
                     "distinct wrong entry points refuted by one leg on its two "
                     "lanes, so the leg is not a restatement of either rival's "
                     "spelling. It is also what makes the leg's `bif` on the "
                     "report load-bearing rather than decorative: a leg that pinned "
                     "one traversal unconditionally would be OVER-STRENGTH (the "
                     "real entry point scores nothing for a carrier it rejects) and "
                     "a leg that pinned a count without reference to the report "
                     "could not see this rival at all. Legs 1-6, C6, C7 and C1-C4, "
                     "C8 all hold exactly. Refuted by projecting the LENGTH out of "
                     "the leg's list equation at a probe whose width DISAGREES with "
                     "the recorded one, so the entry point turns it away and the leg "
                     "pins no traversal; nothing is assumed about the "
                     "re-presentation callee. Witnessed at `xOrig = {[6.25], 2, "
                     "false}`, `contaminationAuto = true`, probed at width 5.",
        "witness": _w_score_traversals("[6.25]", "2", "false", "true", "0.5",
                                       probe_width="5"),
    },

    # ---- no pass at all for an accepted carrier (C5 leg 7, undercount) ----
    {
        "id": "score-spends-nothing",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_ENTRY_PROGRAM,
            "def scoreEntry (ref : Reference) (z : InputData) : Scored :=\n"
            "  -- attack: report on the carrier and stop. The entry point never\n"
            "  -- forwards it to the fitted model at all, which no clause over the\n"
            "  -- report can see: the report is the frozen one.\n"
            "  Scored.done (scoreReport ref z)"),
        "refinement": "a counterpart whose public scoring entry point validates the "
                      "carrier and then returns without ever forwarding it to the "
                      "fitted model reports the same decision, the same diagnostic "
                      "and the same record as the real one, so nothing about the fit "
                      "or about a rejected presentation changes and it PASSES the "
                      "FAIL_TO_PASS test. What it changes is that an ACCEPTED "
                      "presentation costs nothing: the chunked scoring path is never "
                      "entered, so the PASS_TO_PASS bodies that count consultations "
                      "of the chunk-sizing helper across a fit plus a fixed number of "
                      "scoring calls observe fewer than they expect and fail, and any "
                      "body reading anomaly scores off such a call gets nothing. It "
                      "does NOT resolve.",
        "rationale": "REJECT from C5's seventh leg in the UNDERCOUNT direction. The "
                     "two rivals above spend MORE work than one presentation costs; "
                     "this one spends LESS, which is the direction a leg stated as an "
                     "upper bound would miss. Together the three fix the count from "
                     "both sides and on both lanes, so the leg is an equation about "
                     "the behavior rather than a bound fitted to one rival. Legs 1-6, "
                     "C6, C7 and C1-C4, C8 all hold exactly — this rival's report is "
                     "the frozen report on every carrier. Refuted by projecting the "
                     "LENGTH out of the leg's list equation on the ACCEPTING lane, "
                     "where the leg pins one traversal and the rival performs none; "
                     "nothing is assumed about the re-presentation callee. Witnessed "
                     "at `xOrig = {[8.75], 4, true}`, `contaminationAuto = false`, "
                     "`contamination = 0.18`, probed with a same-width nameless "
                     "carrier.",
        "witness": _w_score_traversals("[8.75]", "4", "true", "false", "0.18"),
    },

    # ---- right count, wrong payload scored (C5 leg 7, payload) ----
    {
        "id": "score-forwards-caller-payload-to-model",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_ENTRY_PROGRAM,
            "def scoreEntry (ref : Reference) (z : InputData) : Scored :=\n"
            "  let r := scoreReport ref z\n"
            "  -- attack: spend exactly the one pass the contract asks for, but spend\n"
            "  -- it over the CALLER's own object rather than over the content the\n"
            "  -- re-check handed on. The report still describes the checked content,\n"
            "  -- so every clause about what the call reports is satisfied.\n"
            "  bif r.refused then Scored.done r\n"
            "    else Scored.traverse z.values (fun _ => Scored.done r)"),
        "refinement": "a counterpart that forwards the caller's own object to the "
                      "fitted model while still reporting the checked content enters "
                      "the chunked scoring path exactly once per accepted carrier, so "
                      "every count of how many times the chunk-sizing helper is "
                      "consulted comes out right, and it reports the same decision, "
                      "diagnostic and record, so it PASSES the FAIL_TO_PASS test. "
                      "What it changes is WHAT the fitted trees traverse: a sparse "
                      "carrier reaches them in the wrong sparse layout, a frame "
                      "reaches them as a frame, and a float64 array is traversed at a "
                      "different precision than the trees were built at, so the "
                      "anomaly scores — and the decisions read off them — are taken "
                      "over the wrong object. The PASS_TO_PASS bodies that fit and "
                      "then score content in any presentation other than the one the "
                      "check settles on raise or return the wrong scores, and it does "
                      "NOT resolve.",
        "rationale": "REJECT from C5's seventh leg on its PAYLOAD rather than its "
                     "count, which is what makes the leg an equation about which "
                     "content crosses and not merely a tally. The count is exactly "
                     "right here, so a leg that pinned only the NUMBER of passes "
                     "would admit this rival; and the report is exactly the frozen "
                     "one, so leg 4 — which pins the content the call HANDS ON — "
                     "cannot see it either, because handing on the checked content "
                     "and forwarding the unchecked content to the model are "
                     "different acts. It is the score-side counterpart of "
                     "`prenormalization-payload-scored` on the fit side. Legs 1-6, "
                     "C6, C7 and C1-C4, C8 all hold exactly. The witness takes the "
                     "wrong-payload route: both sides of the leg are about the "
                     "OPAQUE re-presentation callee's value, so — like the two "
                     "offset witnesses and the handed-on one — it conditions on a "
                     "single hypothesis naming the one probed payload where the "
                     "rival is wrong, and `axiom_check.py`'s handed-on leg is where "
                     "that disequality is measured against the real callee rather "
                     "than assumed. In particular the bundle's only axiom "
                     "(`checked_idem`) does not supply it. Witnessed at `xOrig = "
                     "{[1.75], 3, false}`, `contaminationAuto = false`, "
                     "`contamination = 0.32`, probed with payload `[4.25]`.",
        "witness": _w_score_traversals(
            "[1.75]", "3", "false", "false", "0.32", probe_values="[4.25]",
            hyp="h : ¬ ([4.25] = checked [4.25])"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting (audited six times; 2 rivals added by the first
# audit, 1 by the second, 5 by the third, 2 rivals plus a soundness positive
# by the fourth, 1 rival plus a soundness positive by the fifth, and 2 rivals plus
# a soundness positive by the sixth; a SEVENTH round, prompted by the
# mutation-sensitivity measurement rather than by an audit, added 1 rival. The last
# four
# rounds each raised the FAITHFULNESS of the input carrier rather than the
# strength of a clause — the fourth by splitting the storage form off the payload,
# the fifth by splitting "the estimator cannot answer the feature-name question
# about this carrier at all" off "it answers no", the sixth by splitting "the
# admissibility check declines this content outright" off "it re-presents it", and
# the seventh by splitting the estimator's OWN PRESENTATION of a carrier off the
# content that presentation carries: what crosses into the fitted model is a whole
# carrier that describes itself, so the handed-on leg became one record equation
# over all six fields and `later-scoring-hands-on-caller-description` is the rival
# the payload equation admitted —
# see "WHERE THE DESCRIPTION
# STOPS", the two "WHERE THE DESCRIPTION IS NOT ASKED AT ALL" sections and "AND WHY
# THAT CARRIER IS A WHOLE CARRIER AND NOT A PAYLOAD" in the
# module
# header. The sixth round also REMOVED an antecedent rather than adding one: C7's
# admission region was pinned to the re-presentation callee's fixed points, which
# left every carrier the check merely CONVERTS outside it, and
# `content-rewrite-treated-as-inadmissibility` is the rival that verified under
# that reading. An EIGHTH round made the storage form THREE-valued, splitting the
# two sparse layouts the estimator recognises apart, because the layout an
# admissibility check hands content back in is the property the fitted model's
# scoring path turns on -- `later-scoring-hands-on-unscorable-layout` is the rival
# a sparseness bit admitted. A NINTH round added the PARAMETER-DOMAIN precondition
# on the configured threshold level -- the estimator validates that parameter
# before it looks at a carrier at all, so a level it refuses ends the run before
# any clause has anything to describe -- with `pos-declines-refused-level` as its
# soundness control. A TENTH round, prompted by an audit of the score-time cost
# clause rather than of the values, added the four `score-*` rivals that move WORK
# at the scoring end of the tail -- a warm-up pass, a pass spent before the carrier
# is judged, no pass at all on an accepted carrier, and the right number of passes
# over the wrong payload -- which is what made C5's seventh leg load-bearing.
# Total here: 41 cases, 31 uniqueness rivals + 9 soundness
# positives + 1 admissibility.) The sibling battery has 10 SPEC cases
# (8 uniqueness rivals, 1 soundness positive, 1 admissibility) plus 4
# AXIOM_TESTS, ALL attached to a single contracted procedure whose contract
# bundles a side-effect advisory tally, two unforgeable provenance tokens, a
# fractionally-permitted read-only input, and a flag/biconditional pair. This
# bundle models the threshold-selection tail as one total function whose result
# carries five observables. Several sibling rivals collapse onto the same clause
# here; one is not expressible at all. Every sibling case is accounted for below.
#
#   sibling case                          -> here                          disp
#   -------------------------------------------------------------------------
#   3. validating-path-prepatch-bug       -> second-consistency-pass       PORTED
#   2. control-flow-unconditional-scorer  -> unconditional-derivation      PORTED
#   5. forge-offset-token                 -> forged-constant-offset        RE-AIMED
#   7. fabricated-matrix-wrong-data       -> foreign-batch-scored          RE-AIMED
#   4. skip-scorer-no-offset              -> forged-constant-offset        SUBSUMED
#   9. pos-control-record-labels-last     -> pos-derive-before-select      PORTED
#  10. admissibility-public-scorer        -> admiss-f2p-shaped-input       RE-AIMED
#   8. skip-record-fit-labels             -> second-pass-redescribes-      PORTED
#                                            record (+ 2 width/record rivals)
#   6. raw-matrix-out-of-domain           -> prenormalization-payload-      PORTED
#                                            scored                        LATE
#   1. frame-mutation-write-readonly      -> (referential transparency)    VACUOUS
#   AXIOM_TESTS (4)                       -> (G-AX / axiom_check.py)       DROPPED
#
# RE-AIMED, in each case because a nagini PROVENANCE TOKEN becomes a value
# equation here:
#   * forge-offset-token: nagini rejects it because the unforgeable scoring token
#     is never granted. This carrier has no token; what a threshold that was
#     never derived from the data violates is C3's value equation, so the rival
#     asserts the constant instead of deriving it. Same argument (the threshold
#     must be PRODUCED by scoring the training data), different mechanism.
#   * fabricated-matrix-wrong-data: nagini rejects it on the callee precondition
#     demanding the scored matrix carry this fit's own provenance token. Here C3
#     names the training carrier's payload directly, so scoring a fabricated
#     batch violates the value equation itself.
#   * admissibility: the frozen obligation carries exactly ONE precondition
#     hypothesis (`xOrig.namesInspectable = true`, the carriers the estimator can
#     answer the feature-name question about at all), so the sibling's
#     precondition-admission probe DOES have a counterpart: this case discharges
#     the spec at an F2P-shaped point whose precondition holds, which is the
#     PRECOND-TOO-STRONG probe — a precondition drawn so as to exclude the input
#     the change is about would fail here. It carries the residual risk on the
#     rest of the domain at the same time: that the modeled behavior is
#     unsatisfiable at the interesting point.
#
# PORTED LATE, and the most consequential entry in this table:
# skip-record-fit-labels. This case was carried as DROPPED across two audits on
#   the argument that the recorded description is "an internal binding whose only
#   use is the initial validation call", so a rival recording the wrong value
#   would be bit-identical on every input. That argument was FALSE OF THE MODELED
#   BEHAVIOR, and the third audit demonstrated it: the description an estimator
#   holds is not internal at all, it is what the estimator enforces against every
#   carrier handed to it from then on, so it is observable through the estimator's
#   own public entry point. The surface now carries it (C4: the description comes
#   from the training carrier alone; C5: it is enforced afterwards and a later
#   call never re-describes it) and the sibling rival is expressible — indeed
#   THREE rivals of that family are, one per component:
#     - second-pass-redescribes-record  (the description's metadata status)
#     - record-width-from-foreign-batch (the description's width)
#     - later-scoring-redescribes-record (the description's durability)
#   plus two enforcement rivals (later-scoring-accepts-any-width,
#   later-scoring-silent-on-names) that hold the description right and drop the
#   check. Recorded here in full rather than silently reclassified, because the
#   reason the earlier accounting got it wrong is itself the load-bearing fact:
#   the modeled validation step's `reset` argument governs TWO observables, not
#   one — whether a consistency diagnostic is raised, AND whether the call
#   DESCRIBES the admissible input from the carrier it is handed or CHECKS that
#   carrier against the description already held. A surface that observes only
#   the first admits a rival that satisfies the diagnostic clause HONESTLY, by
#   re-describing instead of checking, and destroys the second. That rival was
#   built and measured on the real repository: it passes the FAIL_TO_PASS test and
#   fails a PASS_TO_PASS test, i.e. it verifies and does not resolve. C4 and C5
#   exist to refute it, and both were validated against the real behavior before
#   being written — 120 fits with 0 mismatches for C4's equation across metadata
#   status x threshold configuration x five levels x six shapes, and 128
#   observations with 0 mismatches for C5's three components across fit metadata
#   x threshold configuration x later metadata x four fit widths x four later
#   widths.
#
# SUBSUMED (skip-scorer-no-offset): nagini's "never derive the offset" rival is
#   rejected there by an offset-set FLAG that this carrier does not have (the
#   modeled function always returns a threshold; there is no not-yet-set state).
#   Its observable content — the returned threshold was not produced by scoring
#   the training data — is exactly what forged-constant-offset attacks, at the
#   same clause and with the same refinement argument, so it is not a separate
#   rival here rather than a silently dropped one.
#
# VACUOUS (frame-mutation-write-readonly): the sibling's mandatory frame probe
#   overwrites an input field held at a fractional permission and is rejected by
#   the permission system. Lean is referentially transparent — no heap, no
#   aliasing, no fractional permission, `xOrig` is an immutable value with no
#   writable cell — so no discriminating witness could exist. No substitute is
#   fabricated. Note this is now the ONLY genuinely unmodelable sibling case
#   about state: the durable-description observable that the sibling reaches
#   through estimator state is modeled here functionally, as what the returned
#   fitted estimator does when a further carrier is handed to it (C5's
#   `scoreLater`), so it needs no heap. (The divergence lane is likewise vacuous
#   here, and for the lean-family reason: `implementation_fit` is a total `def`,
#   so a diverging rival cannot be written. The sibling carries no divergence
#   case.)
#
# PORTED LATE (2): raw-matrix-out-of-domain -> prenormalization-payload-scored.
#   Nagini rejects scoring the RAW (possibly name-carrying) table because the
#   non-validating scorer's precondition demands an already-normalized argument.
#   Two earlier audits carried this case as DROPPED-VACUOUS, and the argument they
#   gave was TRUE OF THE MODEL AS IT THEN STOOD: the validation step was modeled
#   as changing only the metadata flag, carrying `values` through untouched, so a
#   rival scoring the pre-normalization carrier computed literally the same term as
#   the frozen impl. It was machine-checked twice: the rival was built,
#   `∀ x a c, implementation_fit x a c = goldImpl x a c` closed by
#   `cases a <;> rfl`, the variant verified with the frozen script, and every
#   then-shipped witness failed against it — i.e. it was a CORRECT impl on that
#   carrier, and no witness could exist.
#   THAT IS NO LONGER THE MODEL. Establishing admissibility is not a pure
#   inspection: the check RE-PRESENTS the payload in the uniform numeric form the
#   fitted model operates in (`carrier.values = checked x.values`), which is the
#   behaviour of the real `check_array`/`_validate_data` and is validated against
#   it by G-AX (leg I / the payload-identity leg of axiom_check.py). So the
#   distinction the nagini rival exploits IS kept here, C3 and C8 both name
#   `checked xOrig.values`, and the rival is refutable — shipped above, with a
#   witness that conditions only on the two applications differing and a
#   consistency probe confirming the hypothesis is satisfiable. Recorded in full
#   rather than silently reclassified, because the reason the earlier accounting
#   was right and is now wrong is itself load-bearing: a shallow validation model
#   ("only the metadata flag changes") erases a real refusal ground and a real
#   data-presentation obligation at the same time.
#   * AXIOM_TESTS (4). The axiom lane is G-AX's job and this gate ignores
#     AXIOM_TESTS; the sibling's four probes (validation-callee soundness, scorer
#     + token soundness, offset provenance, scorer-domain containment) are the
#     obligations this bundle's axiom_check.py / G-AX already discharge for
#     `percentile` / `checked` / the deep-modeled validation step.
#
# ADDED beyond the ported set, all attacking load-bearing parts of the SAME
# modeled spec rather than fabricated for an unmodeled behavior:
#   * rank-unscaled — the sibling's value abstraction drops the offset VALUE
#     entirely (only provenance tokens separate its rivals), so it has no rival
#     for the rank arithmetic that C3 pins here. This is the near-miss that is
#     correct in data, computation and branch, and wrong only in the rank.
#   * pos-negated-branch / pos-single-expression — two further reshapes beyond
#     the ported positive, so the obligation is defended against branch-polarity
#     and single-exit reshapes, not only statement order.
#   * recheck-against-fixed-names / auto-constant-sign-flipped — ADDED BY THE
#     FIRST AUDIT to close two measured gaps in clause coverage, both of which the
#     original battery left one-sided:
#       - C1 was attacked only by a rival that is wrong exclusively on a
#         name-carrying carrier (`second-consistency-pass` compares the re-check
#         against the record, so at `hasFeatureNames = false` it AGREES with the
#         frozen impl and no witness at that point could refute it). C1 is now
#         attacked at BOTH values of the metadata binder.
#       - C2 was attacked only by a rival that DELETES the unconfigured branch,
#         i.e. only whether the branch is reached; nothing pinned the constant it
#         returns. A sign-flipped constant is now refuted too.
#   * auto-branch-diagnostic — ADDED BY A SECOND, INDEPENDENT AUDIT, which
#     re-measured the clause coverage above and found it still one-sided in a
#     direction the first pass did not check. C1 was attacked at both values of
#     the METADATA binder but both of its rivals edit the CONFIGURED tail, so both
#     are correct wherever `contaminationAuto = true` (measured: each rival's own
#     witness re-stated on the unconfigured branch FAILS against it, exit 1). C1
#     is a top-level clause with no branch guard, so it must hold on both
#     branches; nothing pinned it on the unconfigured one. This rival keeps the
#     configured tail frozen verbatim and reports the diagnostic on the
#     unconfigured branch instead. Built before adding: variant scope clean,
#     variant rejected (exit 1), witness rival exit 0 / gold exit 1, no
#     consistency probe needed (binds nothing). The gold-side failure is semantic
#     — an unsolved goal carrying the diagnostic hypothesis at the frozen value —
#     and its FORGERY pair confirms the exit code tracks the claim rather than the
#     file: the opposite claim (that the impl SATISFIES the spec at that same
#     point) builds against gold (exit 0) and fails against the rival (exit 1),
#     the exact inverse of the witness.
#   * pos-record-from-normalized-carrier — ADDED WITH C4/C5 as their soundness
#     control. An added clause needs a positive that would fail if the clause
#     pinned the PROVENANCE of the description rather than its CONTENT; this impl
#     spells the description out from the training carrier's own fields instead of
#     taking the validation step's returned description, which is the same value
#     on every input, and it must verify.
#   * the five record/enforcement rivals — ADDED BY A THIRD, INDEPENDENT AUDIT.
#     See PORTED LATE above for why they are ports of a case wrongly carried as
#     DROPPED rather than inventions. Each was built and measured before being
#     added: variant scope clean, variant rejected, witness rival exit 0 / gold
#     exit 1. Their witnesses are the four newly reachable clause components
#     (C4-metadata, C4-width, C5-refused, C5-warned); the durability rival shares
#     C5-refused with the enforcement rival by DESIGN, since the two are distinct
#     wrong implementations refuted at the same component, which is what shows the
#     component is a property of the behavior and not a restatement of one impl's
#     spelling.
#   * pos-sparse-declines-threshold / sparse-guard-inverted /
#     sparse-abort-emits-diagnostic — ADDED WITH THE STORAGE-FORM LIMIT on C3 and
#     C8 (module header, "WHERE THE DESCRIPTION STOPS"). A NARROWED clause needs
#     all three: the positive that the narrowing was for (declining a threshold
#     where the real code aborts MUST verify, or the clause was over-strength), a
#     rival that reads the narrowing as licence where the clause still applies
#     (refuted by C8 on a dense carrier), and a rival that reads it as licence in
#     the clauses that never carried it (refuted by C1 on a sparse carrier). The
#     limit itself is measured against the real callees rather than argued —
#     axiom_check.py's leg S at both storage forms with the dense leg as its
#     control, and conformance_check.py asserting the abort boundary in both
#     directions on the patched estimator — because a domain limit no control can
#     refute is indistinguishable from a hole. Each was built before being added:
#     variant scope clean, the two rivals rejected, their witnesses exit 0 against
#     the rival and exit 1 against the frozen solution, the positive verified.
#   * pos-uninspectable-fit-declines / later-scoring-admits-uninspectable —
#     ADDED WITH THE LABEL-INSPECTABILITY PRECONDITION (module header, "WHERE THE
#     DESCRIPTION IS NOT ASKED AT ALL"). A precondition is the one kind of spec
#     edit that can only WEAKEN, so it needs both lanes and it needs them in
#     opposite directions: the positive is the shape the precondition was drawn
#     for (an impl that declines to produce a fitted description at all where the
#     real estimator raises before recording anything MUST verify, or the
#     obligation was over-strength there), and the rival is the collapsed reading
#     of the same distinction — it treats "labels the estimator cannot inspect" as
#     "labels it inspects and finds absent", so it admits an uninspectable later
#     carrier at the training width, which C5's fifth leg refutes. That fifth leg
#     is why the precondition does not buy the weakening back on the side where
#     the distinction is observable. Neither the precondition nor the leg is
#     argued: axiom_check.py leg L presents mixed-kind labels at three widths, at
#     fit time and through the fitted estimator's public scoring path, with the
#     homogeneously labelled carrier of the same payload at the same width as its
#     negative control, and conformance_check.py tier B asserts the fit-time abort
#     leaves neither attribute behind (dense control per abort) and that every
#     uninspectable probe is turned away by the label inspection at the training
#     width (same-width homogeneous control per probe), with four abuse mutations
#     — a precondition that ignores the inspection, one that also excludes merely
#     unlabelled carriers, and two later-scoring readings that admit or merely
#     warn about an uninspectable carrier — all caught. Each case was built before
#     being added: variant scope clean, the rival rejected, its witness exit 0
#     against the rival and exit 1 against the frozen solution, the positive
#     verified.
#   * pos-inadmissible-content-fit-declines /
#     later-scoring-admits-inadmissible-content /
#     content-rewrite-treated-as-inadmissibility — ADDED WITH THE
#     CONTENT-ADMISSIBILITY PRECONDITION and with the REMOVAL of C7's fixed-point
#     antecedent (module header, "WHERE THE DESCRIPTION IS NOT ASKED AT ALL (the
#     content-admissibility precondition...)"). Same three-sided shape as the
#     label-inspectability round, plus a third case the earlier round did not need:
#     the positive is the shape the precondition was drawn for (an impl that
#     declines to produce a fitted description where the real check raises MUST
#     verify), the first rival is the collapsed reading of the distinction (it
#     treats content the check DECLINES as content it merely re-presents, so it
#     admits an inadmissible later carrier at the training width, which C5's sixth
#     leg refutes), and the second rival is the CONVERSE error, which is what the
#     dropped antecedent had been hiding: it treats content the check merely
#     REWRITES as content the check declines, refusing every ordinary caller's
#     carrier. Under the old antecedent (`z.values = checked z.values`) that rival
#     verified, because every carrier it refused sat outside C7's region; with the
#     region stated as `z.contentAdmissible = true` it is refuted. So the round
#     removed an antecedent as well as adding one, and the removal is the part with
#     a real refutation behind it. Neither direction is argued: axiom_check.py leg
#     D presents the three declined contents at three widths, at fit time and
#     through the fitted estimator's public scoring path, each asserted still
#     label-inspectable (which is what makes the field irreducible to
#     `namesInspectable`), with the ordinary content of the same width as its
#     negative control; conformance_check.py tier B reads off the estimator WHICH
#     step declined, asserts the fit-time abort leaves neither attribute behind,
#     and turns every declined content away at the training width with the ordinary
#     content of that width accepted, with four abuse mutations — a precondition
#     that ignores the check, one that also excludes content the check merely
#     converts, a later-scoring reading that admits declined content on a width
#     check, and one that escalates a re-presentation into a refusal — all caught.
#     Each case was built before being added: variant scope clean, the two rivals
#     rejected, their witnesses exit 0 against the rival and exit 1 against the
#     frozen solution, the positive verified. The second rival's witness needed a
#     route of its own, because its refusal predicate names the opaque
#     re-presentation callee and `decide` is stuck on it: it ascribes the shape the
#     rival gives the refusal and lets the defeq check reduce, and the FORGERY
#     ascribing the opposite value fails against the rival, which is what shows the
#     elaboration reports the rival's behaviour rather than merely typechecking.
#
# POINT SPREAD. The thirty-one reject witnesses probe thirty-one DISTINCT
# input points (pts=31); (xOrig.values, xOrig.nFeatures, xOrig.hasFeatureNames,
# contaminationAuto, contamination) — plus, where it is what separates the point,
# xOrig.form — and, for the C5/C6/C7 rivals, the probe carrier (whose own
# namesInspectable is what separates the last row):
#   ([1.0],       3, true,  false, 0.05)  second-consistency-pass      C1 (names present)
#   ([7.0,8.0],   2, false, false, 0.3 )  recheck-against-fixed-names  C1 (names absent)
#   ([2.5,3.5],   2, false, true,  0.6 )  auto-branch-diagnostic       C1 (unconfigured branch)
#   ([3.0],       1, false, false, 0.1 )  forged-constant-offset       C3 (value)
#   ([4.0,5.0],   2, false, false, 0.2 )  foreign-batch-scored         C3 (carrier)
#   ([6.0],       1, true,  false, 0.5 )  rank-unscaled                C3 (rank)
#   ([3.25,4.75], 2, true,  false, 0.28)  prenormalization-payload-    C3 (presentation)
#                                           scored                     + C8
#   ([2.0],       1, false, true,  0.25)  unconditional-derivation     C2 (branch reached)
#   ([9.0],       1, true,  true,  0.75)  auto-constant-sign-flipped   C2 (branch value)
#   ([1.5],       4, true,  false, 0.15)  second-pass-redescribes-     C4 (metadata)
#                                           record
#   ([2.75],      2, false, false, 0.35)  record-width-from-foreign-   C4 (width)
#                                           batch
#   ([1.25],      5, false, true,  0.45)  later-scoring-accepts-any-   C5 (refused)
#                                           width        probe z = ([1.25], 1, false)
#   ([8.5],       3, true,  false, 0.22)  later-scoring-redescribes-   C5 (refAfter)
#                                           record       probe z = ([8.5],  1, true)
#   ([0.5],       6, false, true,  0.65)  later-scoring-silent-on-     C5 (warned)
#                                           names        probe z = ([0.5],  6, true)
#   ([2.5],       4, false, false, 0.4 )  later-scoring-refuses-       C6 (admission at
#                                           everything                 xOrig itself)
#   ([1.0],       2, true,  false, 0.3 )  names-treated-as-            C7 (admission of a
#                                           inadmissibility            nameless carrier)
#                                          probe z = ([9.5], 2, false)
#   ([1.25],      2, false, true,  0.35)  traversal-hoisted-above-     C8 (work on the
#                                           branch                     constant branch)
#   ([7.5],       3, true,  false, 0.3 )  extra-discarded-traversal    C8 (work on the
#                                                                      configured branch)
#   ([2.5,6.5],   2, false, false, 0.35)  uncounted-work-off-          C3 (scores the
#                                           structure                  traversal yielded,
#                                                                      at a NON-identity
#                                                                      interpretation)
#   ([0.1],       1, false, true,  0.25)  later-scoring-forwards-      C5 (handedOn:
#                                           caller-payload  probe z = ([4.5], 1, false)
#                                                                      the CONTENT half)
#   ([0.35],      4, false, false, 0.45)  later-scoring-hands-on-      C5 (handedOn: the
#                                           caller-description         SELF-DESCRIPTION
#                                          probe z = ([6.25], 4, true)  half -- content
#                                                                      converted, worn
#                                                                      under the caller's
#                                                                      account of itself)
#   ([3.5,1.5],   4, false, false, 0.4 )  sparse-guard-inverted        C8 (work on the
#                                          DENSE carrier               dense branch)
#   ([3.5,1.5],   4, false, false, 0.4 )  sparse-abort-emits-          C1 (on the carrier
#                                          SPARSE carrier                diagnostic
#                                                                      where fitting
#                                                                      aborts)
#   ([6.5],       5, true,  false, 0.05)  later-scoring-admits-        C5 (fifth leg: a
#                                           uninspectable              probe whose labels
#                                          probe z = ([5.5], 5, false, cannot be inspected
#                                                     namesInspectable := false)  at all)
#   ([7.25],      3, false, true,  0.15)  later-scoring-admits-        C5 (sixth leg: a
#                                           inadmissible-content       probe whose content
#                                          probe z = ([2.75], 3, false,  the check declines
#                                                     contentAdmissible := false) outright)
#   ([0.75],      2, false, true,  0.2 )  later-scoring-hands-on-      C5 (handedOn: the
#                                           unscorable-layout          STORAGE-FORM half
#                                          probe z = ([3.5], 2, false,  -- content
#                                                     form := sparseByRow)  converted and
#                                                                      correctly described,
#                                                                      handed on in the
#                                                                      sparse layout the
#                                                                      scoring path refuses)
#   ([4.5],       2, true,  false, 0.42)  content-rewrite-treated-     C7 (admission of an
#                                           as-inadmissibility         ORDINARY carrier,
#                                          probe z = ([9.5], 2, false)  i.e. content the
#                                                                      check accepts AND
#                                                                      rewrites)
#   ([5.5],       3, false, false, 0.22)  score-warmup-traversal       C5 (seventh leg:
#                                          probe z = ([9.5], 3, false)  a warm-up pass at
#                                                                      score time --
#                                                                      ACCEPTING lane,
#                                                                      overcount)
#   ([6.25],      2, false, true,  0.5 )  score-before-deciding        C5 (seventh leg:
#                                          probe z = ([9.5], 5, false)  a pass spent
#                                                                      BEFORE the refusal
#                                                                      decision --
#                                                                      REFUSING lane,
#                                                                      where the leg pins
#                                                                      no traversal)
#   ([8.75],      4, true,  false, 0.18)  score-spends-nothing         C5 (seventh leg:
#                                          probe z = ([9.5], 4, false)  NO pass at all on
#                                                                      an accepted
#                                                                      carrier --
#                                                                      undercount)
#   ([1.75],      3, false, false, 0.32)  score-forwards-caller-       C5 (seventh leg on
#                                           payload-to-model           its PAYLOAD: right
#                                          probe z = ([4.25], 3, false)  count, the
#                                                                      caller's own object
#                                                                      traversed)
# Every input binder MOVES across them: `contaminationAuto` in {false, true},
# `hasFeatureNames` in {false, true}, `form` over all three layouts, `nFeatures`
# takes six distinct widths
# (1, 2, 3, 4, 5, 6), `values` TWENTY-EIGHT distinct payloads (including six
# two-element ones), `contamination` EIGHTEEN distinct levels (0.05-0.75, every
# CONFIGURED one inside the interval the estimator declares). The two
# binders that do NOT move are `xOrig.namesInspectable` and
# `xOrig.contentAdmissible`: they are two of the obligation's three
# preconditions, so a rival is only refutable where they hold, and `= true` is what
# each of the thirty-one witnesses discharges by `decide`. Both move on the PROBE
# carrier instead, which is where the model asks a positive question about them.
# The third precondition -- that the estimator's parameter validation admits the
# configured level -- is not a field and moves differently: the LEVEL itself takes
# fourteen distinct configured values across the rivals, each witness assuming the
# validation admits its own (a fact G-AX's parameter-domain leg measures at every
# one of them), while the refused side of that precondition is where no clause
# claims anything and `pos-declines-refused-level` is the control. All
# eight
# clauses are attacked from independent directions: C1 at both metadata points AND
# on both branches AND on both storage forms (four rivals), C2 on branch-existence
# and on branch-value, C3
# by five rivals differing in WHICH part of it they break (value, carrier, rank,
# presentation of the payload, and the interpretation of the scoring effect),
# C4 on both components of the description it pins
# (metadata status and width), C5 on EACH of its seven legs and on ALL THREE
# separable halves of the fourth (one at the
# foreign-width refusal, one at `warned`, one at `refAfter`, three at `handedOn` --
# the content it carries, the description it wears, and the storage layout it
# crosses in --
# one at the uninspectable-probe refusal, one at the declined-content refusal, and
# FOUR at the seventh, the score-time traversal record: a warm-up pass and a pass
# spent before the refusal decision (the two lanes of the leg), a pass withheld on
# an accepted carrier (the undercount direction, which a leg stated as an upper
# bound would miss), and the right count spent over the caller's own object rather
# than the checked content (the leg's PAYLOAD rather than its tally)), C6
# and C7 on the
# two directions of admission the real code actually guarantees — C7 from both
# sides of the content question, a rival that refuses content the check would
# merely rewrite and one that admits content the check declines — and C8 on BOTH
# branches (a traversal added where the spec allows none, and a second added where
# it allows one) AND at its storage-form boundary (the work withheld on the dense
# branch, where the clause still applies), with C1 carrying the other side of that
# boundary (a claim withheld on the sparse carrier, where C1 never withheld one).
# The probe carriers also spread: one narrower and
# metadata-agreeing, one narrower and metadata-carrying, one of the training width
# and metadata-disagreeing, one of the training width presented in the ROW-INDEXED
# SPARSE layout (C5's handed-on leg on its storage-form half, the only probe that
# is not dense, and the only region where that half has content at all), one
# nameless and ORDINARY — content the check accepts
# and rewrites, which is C7's region now that no antecedent pins it to the
# re-presentation's fixed points, so the probe says nothing about the callee at all
# — one of the training width whose own labels cannot be inspected
# at all (C5's fifth leg, the only probe carrying `namesInspectable := false`), one
# of the training width whose content the check declines outright (C5's sixth leg,
# the only probe carrying `contentAdmissible := false`), one of a DISAGREEING width
# for the seventh leg's refusing lane (where the leg pins no traversal at all, which
# is the lane the accepting-lane rivals are exactly right on), one of the training
# width carrying a payload the re-presentation moves (the seventh leg's PAYLOAD
# half),
# and for C6 the training carrier itself, so the conjuncts are
# separated rather than co-triggered. The obligation is defended by nine
# positives (including `pos-name-identity-refusal`,
# `pos-sparse-declines-threshold`, `pos-declines-refused-level`,
# `pos-uninspectable-fit-declines` and
# `pos-inadmissible-content-fit-declines`, the
# soundness controls for the guards on C6/C7, on C3/C8, and for each of the three
# preconditions) plus the admissibility witness.
#
# WHY THE PER-CLAUSE SPREAD IS NOT DECORATIVE. Every rival that edits ONE branch
# is correct on the other, so a witness on the wrong branch cannot refute it and
# the point choice is forced, not cosmetic. Measured for each C1 rival by
# re-stating its own witness at its agreement point and building it against the
# rival: `second-consistency-pass` at `hasFeatureNames = false` -> exit 1, and
# both configured-tail C1 rivals at `contaminationAuto = true` -> exit 1. That
# residual is exactly what `auto-branch-diagnostic` covers. The same forcing
# applies to the record rivals and is why their points are not interchangeable:
# `second-pass-redescribes-record` re-describes from the training data itself, so
# its recorded WIDTH is correct and only the metadata component can refute it —
# which also means it is correct at `hasFeatureNames = false`, so its witness must
# carry metadata. `record-width-from-foreign-batch` is the mirror image: the
# recorded metadata status is right and only the width component refutes it, and
# it is stated at `hasFeatureNames = false` precisely to show C4 is enforced
# independently of the metadata flag. For C5, the two `refused` rivals are both
# refutable only at a probe carrier of a DIFFERENT width (at the training width
# they refuse nothing, correctly), while `later-scoring-silent-on-names` is
# refutable only at a probe carrier whose metadata status DISAGREES — and it is
# stated at the training width so the width check cannot be what refutes it.
#
# AXIOM_TESTS: dropped (see above). Kept as an empty list so the manifest's shape
# matches the sibling's.
AXIOM_TESTS = []
