"""properties.py — G-PBT falsification battery for astropy__astropy-13033 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside an ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves, inside a
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the single ``theorem correct_<name>`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery (see
``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models TWO helper functions with fractional-permission contracts
(``render_name_run`` at site A, ``compose_leading_run_report`` at site B); this
Lean bundle models the SINGLE purely-functional core — one total function over
the observable inputs (the toggles, the configured names, the present names, the
class name) returning an ``Except``-carried outcome. Most nagini cases therefore
carry over as attacks on ONE clause of the one modeled obligation. Each nagini
case is mapped to its Lean counterpart, or to a stated reason for omission, in
the per-case comments below and in the OMISSION LEDGER at the end of this
docstring. (An earlier revision pointed here to "the module ``assessment``";
no such module exists in this bundle or the repository, so that pointer was
dangling and the mapping now lives in this file, where it can be checked.)

DEFENDED SURFACE (one modeled behavior). The re-check produces exactly the
outcome dictated by the rule: the right no-op / error decision, and on a
mismatch a message naming the FULL expected and found column collections
(adaptively rendered — a single name as one quoted name, several names as the
whole bracketed list), with the word "column" pluralised exactly when more than
one column is required. The postcondition pins ``result`` to a single grounded
computation over the inputs, so it has these independent top-level clauses,
selected by the input:

  * the check-disabled no-op (returns the relax flag unchanged);
  * the no-configured-names no-op (returns the relax flag unchanged);
  * the relaxed truncation of the configured list to the number present;
  * the no-present-columns report (keeps its single-head wording);
  * the leading-columns-mismatch report (the CHANGED clause: full adaptive
    rendering of both the expected and the found collection + pluralisation);
  * the relaxed-regime toggle once the leading columns match.

The BEHAVIOURAL DISCRIMINATOR (the fix): on a mismatch, render the WHOLE
required collection and the WHOLE present leading slice — every name, adaptively
— and pluralise, instead of naming only the first required name and the first
present name. The pre-fix message named one pair that need not even differ; the
partial-domain rivals below ARE that pre-fix behavior.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS, and demonstrated so rather than
    asserted. Lean is referentially transparent: an input carries no heap
    permission, there is no read-only half-permission to overwrite and no
    aliasing to exploit. What the nagini rival tests is WHO HOLDS WRITE
    PERMISSION, and that is not an observable of a total function over values —
    the spec quantifies over the input list itself, and the carrier offers no
    reference through which a caller's copy could be disturbed. Confirmed by
    construction on this carrier: the only expressible analogue of "write the
    same value back into the input" is rebinding a LOCAL to a value-neutral
    expression, which leaves ``result`` equal on every input, so any such variant
    is a POSITIVE (a correct reshape), never a rival — it cannot be made to fail
    for a spec reason. There is therefore no rival instance to land, and no
    substitute is fabricated. (nagini case 3.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned equal to a term built only from the inputs. There is no opaque
    answer key an implementation could echo. (One leaf of the rendering, the
    per-element quoting of a name inside a multi-name list, is left ``opaque``
    because it is an unchanged platform builtin whose escaping tables the fix
    never touches — NOT an oracle for the modeled decision; the impl still has to
    select the branch and assemble the message.) In its place the battery carries
    honest cheapest-implementation POSITIVE CONTROLS that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where the fix bites: rendering only the first name of each
    collection; dropping the leading name of each rendered collection; forcing
    the whole-list form even for a ONE-name collection (the other arm of the
    adaptive renderer); dropping the plural marker; ignoring the relaxed
    truncation; hardcoding the class name; and the unchanged-but-load-bearing
    no-op / toggle clauses.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``rfl`` is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet stating the spec predicate directly at one
concrete input and refuting it. Each was checked to HOLD of its rival and to FAIL
on the frozen solution, so it discriminates rather than asserting a tautology.

A subtlety of this carrier drives the witness tactics. The multi-name list
rendering routes through the ``opaque`` per-element quoting, so a message built
in that branch is not fully ``decide``-able. But the THREE rivals that attack the
adaptive-rendering clause (first-name-only, drop-leading-name, always-list-form)
each make the two forms disagree at the VERY FIRST character of the rendered
collection — the single-name form begins ``'`` where the whole-list form begins
``[`` — which is BEFORE any opaque element text, in BOTH directions (two rivals
emit ``'`` where the spec emits ``[``; the third emits ``[`` where the spec emits
``'``). Their witnesses cancel the concrete common prefix and expose that one
character (``'[' ≠ '\''``), which is decidable. The offset is measured, not
assumed: the message prefix ``"<Class> object is invalid - expected "`` is
exactly 40 characters for a 10-character class name, so the discriminating
character is ``(msg.data)[40]`` and the witnesses project exactly there. The
clauses whose divergence is entirely concrete (plural marker in the no-columns
branch, the two no-op decisions, the relaxed truncation, the toggle, the
class-name prefix) are refuted by plain evaluation.

That first-character projection does NOT reach the INTERIOR of a rendered
multi-name collection — the separator between the rendered elements, and the
per-element rendering itself — because both sit past the opaque element text. The
opacity is not, however, a reason no witness can be built there, and the two
INTERIOR rivals below demonstrate it: their witnesses state the refutation at a
point described by HYPOTHESIS (``pyReprStr "a" = "'a'"``, i.e. what the platform's
canonical rendering yields for the names at hand) rather than by computing the
opaque leaf. Nothing has to PROVE those hypotheses; they must only be
SATISFIABLE, since a refutation resting on contradictory assumptions describes no
real input and would attest to nothing. That is the one genuine hazard of this
technique, so it is established POSITIVELY rather than by the absence of a
complaint: for each of the two interior witnesses a concrete witnessing function
was exhibited and checked by the verifier (``∃ f, f "a" = "'a'" ∧ …``, closed by
``decide``), so the assumed rendering really is realisable and the counterexample
input really exists. The gate's consistency probe agrees (it derives no
``False``), but note that probe is deliberately incomplete in the safe direction,
so its silence alone is weaker evidence than the exhibited models. It is NOT the
case that an opaque term is immune to refutation — a probe over genuinely
contradictory hypotheses about the same leaf (``pyReprStr "z"`` equal to two
different strings) DOES close, measured — which is precisely why the models are
exhibited. With the leaf pinned by a satisfiable hypothesis the remaining message
is concrete and the disagreement decidable.

BINDER / POINT SPREAD. The reject witnesses move every input binder of the spec
rather than fixing them at one convenient point: ``className`` varies
(``"TimeSeries"``, ``"QTable"``); ``requiredColumnsEnabled`` takes both settings;
``requiredColumns`` takes ``none``, ``some []`` and ``some`` of length 1 and
length ≥2; ``requiredColumnsRelax`` takes both settings (including the
relaxed-truncation, the relaxed no-columns point and the toggle point); and
``colnames`` ranges over empty, matching, mismatching, shorter-than and
longer-than the requirement. No two rivals share a refutation point unless they
fail there for the same reason — the eighteen reject witnesses probe eighteen
distinct inputs (verified by extracting each witness's argument tuple: eighteen
tuples, no duplicates).

AXIOM lane: EMPTY here. The bundle declares one ``opaque`` leaf (the unchanged
platform per-element quoting) validated executably by G-AX (an A-reference), and
consumes no ``axiom``. The axiom lane belongs to G-AX; this gate ignores it, and
the nagini ``AXIOM_TESTS`` (also empty there) are dropped.

AUDIT RECORD (independent adversarial re-derivation of this ported battery; every
line below is a machine-checked exit code from the real verifier, not an
argument).

  * STATEMENT INTEGRITY — the ``theorem correct_checkRequiredColumns`` statement
    and the whole spec view were extracted from every case module and diffed
    against the frozen solution: byte-identical in all of them. No obligation is
    weakened, restated or narrowed.

  * WITNESS DISCRIMINATION — every ``expect="reject"`` witness was rebuilt twice,
    by hand, outside the gate: against its rival (elaborates, exit 0) and against
    the FROZEN solution (fails, exit 1), reproducing the recorded
    ``gold_signature`` in each case. No witness passes vacuously and none would
    elaborate against the frozen impl.

  * FORGERY TEST — for every reject case whose gold failure is not a plain
    evaluation, the claim was flipped (the ``\u00ac`` dropped) and rebuilt: gold's
    error CHANGED to ``No goals to be solved`` — i.e. the frozen impl PROVES the
    positive equation the rival refutes — while the same file against the rival
    left a concrete residual inequation. Gold's failure therefore tracks the
    CLAIM, not the tactic shape; no case is refuted by a missing identifier, a
    type error, an unfolding failure or a timeout.

  * ARE THE RIVALS WRONG, OR MERELY DIFFERENT? — each rival was simulated against
    the modeled behavior over a 1600-input cross-product of the five binders. Every
    one differs OBSERVABLY on a non-empty set of inputs (the two multi-name
    rendering rivals on 278 and 390 inputs respectively). No rival is a
    definitionally-equal reshape, so no rejection here attests only to a tactic
    mismatch.

  * SPEC-TOO-WEAK PROBE — thirteen NEW wrong implementations, not shipped here,
    were written against the frozen spec, including four aimed at the leaf that
    routes through the ``opaque`` per-element quoting. ALL thirteen were rejected.
    No spec hole was found.

  * SPEC-TOO-STRONG PROBE — five NEW correct implementations were written and
    PROVEN against the frozen obligation, four of them not definitionally the
    frozen term. The spec admits genuinely reshaped correct implementations.

  * ADMISSIBILITY — the ground instance in ``admiss-ground-report-instance`` was
    shown load-bearing rather than decorative: the same ``have \u2026 := rfl`` FAILS
    (type mismatch) when placed against a wrong implementation, so it is a real
    discharge of the obligation at the F2P-shaped input, not a tautology.

  * REPAIR — the audit found ONE genuine gap and closed it. Both shipped
    rendering rivals attacked the MULTI-name arm of the adaptive renderer; the
    ONE-name arm (the wording the fix deliberately PRESERVES, and the arm the
    single-column scenarios assert) had no rival, so an implementation that
    dropped the adaptivity entirely would have been rejected with nothing
    attributing that rejection to the spec. ``weak-always-list-form`` was added
    and verified to discriminate in both builds.

SECOND-PASS AUDIT (independent adversarial re-derivation by a different auditor;
every claim below is an exit code from the real verifier).

  * The first-pass findings above were RE-CHECKED, not taken on trust, and all
    held. Statement integrity: the ``theorem correct_checkRequiredColumns``
    header and the whole ``spec_view`` were extracted from all case modules and
    compared to the frozen file — byte-identical in every one. Witness
    discrimination: all nine shipped reject witnesses rebuilt by hand, rival
    EXIT 0 and frozen EXIT 1 in every case, reproducing each recorded
    ``gold_signature``. Forgery test (attack B'): for each of the nine, the claim
    was flipped (``¬`` dropped) and rebuilt on both sides — against the frozen
    solution the error CHANGED to ``No goals to be solved`` (the frozen impl
    PROVES the equation the witness refutes) while against the rival the flipped
    claim still failed on a concrete residual. Gold's exit code therefore tracks
    the CLAIM, not the tactic shape, in all nine.

  * The three "load-bearing" prose claims were each verified by the build they
    assert. ``pos-enabled-guard-as-match``: the frozen ``rfl`` alone was rebuilt
    against that reshape and FAILED, so the case genuinely re-proves rather than
    re-spelling the frozen term. ``admiss-ground-report-instance``: the same
    ``have … := rfl`` was placed against a WRONG impl and failed with a type
    mismatch, so the ground discharge is a real evaluation at the reporting
    input and not a tautology. The FRAME-MUTATION vacuity claim was confirmed by
    construction rather than argument: the only expressible analogue on this
    carrier (rebinding the present-columns local to a value-equal expression)
    was built and VERIFIED (EXIT 0), i.e. it is a positive and cannot be made a
    rival, exactly as recorded.

  * ARE THE RIVALS WRONG? — re-simulated independently over a 39936-input
    cross-product of the five binders. Every shipped rival differs observably
    from the modeled behavior (31 to 17330 inputs); none is a
    definitionally-equal reshape.

  * SPEC-TOO-WEAK — nine FURTHER wrong implementations were written, three of
    them aimed squarely at the ``opaque`` per-element leaf (hand-rolled list
    rendering substituting the non-escaping single-quoter for the platform
    rendering; separator without its space; adaptive threshold shifted to
    ``≤ 1``). ALL nine were rejected. No spec hole; in particular the opaque leaf
    is not usable as an answer key.

  * SPEC-TOO-STRONG — three further correct reshapes were written and PROVEN
    (EXIT 0): a combined no-op guard, the relaxed truncation rewritten as a
    ``match`` on the Bool, and the no-columns guard with its ``&&`` commuted (the
    last needed a three-way case split, which is proof engineering, not a spec
    relaxation). The spec admits genuinely reshaped correct impls.

  * REPAIR (this pass) — one further genuine gap, of the same shape as the first
    pass's but on the other half of the changed clause. The clause both RENDERS
    adaptively and TRUNCATES the found side to the required length; every rival
    attacked the rendering, none the truncation. ``weak-found-side-untruncated``
    closes it: measured to differ from the modeled behavior on 14400 of the
    39936 inputs while AGREEING at the multi-name reporting point — so no
    existing witness could see it — and verified to discriminate in both builds
    (rival EXIT 0, frozen EXIT 1 with the claim-tracking ``rewrite`` signature,
    flipped claim on gold EXIT 1 with ``No goals to be solved``). It is also the
    only reject case whose present-column list is LONGER than the requirement,
    which is a binder point no other witness reached.

THIRD-PASS AUDIT (independent adversarial re-derivation by a third auditor; every
claim below is an exit code from the real verifier, run outside the gate).

  * RE-CHECKED, not trusted. Statement integrity: the ``theorem
    correct_checkRequiredColumns`` statement and the whole non-impl / non-proof
    view were extracted from every case module and diffed against the frozen file
    — byte-identical in all of them. Witness discrimination: every shipped reject
    witness rebuilt by hand, rival EXIT 0 and frozen EXIT 1 in each, reproducing
    the recorded ``gold_signature``. Forgery test (attack B′) on each: with the
    ``¬`` dropped, gold's error CHANGES to ``No goals to be solved`` — the frozen
    impl PROVES the equation the witness refutes — while the same flipped claim
    against the rival leaves a concrete residual disagreement (``introN failed``
    on a goal showing both messages, or ``decide`` reporting the two concrete
    strings). Gold's exit code tracks the CLAIM, not the tactic shape.

  * OBSERVABILITY re-derived independently over a 1456-input cross-product of the
    five binders: every shipped rival differs from the modeled behavior on 13 to
    474 inputs. None is a definitionally-equal reshape.

  * SPEC-TOO-WEAK — twelve further wrong implementations were written and ALL
    twelve were rejected: fields swapped; expected side rendering the
    untruncated configured list; plural counted from the untruncated list; the
    no-columns branch naming the present head; the toggle comparing against the
    whole present list; the no-columns branch ignoring the relaxed regime; the
    plural marker on a one-name requirement; the relaxed truncation applied to
    the wrong list; the mismatch guard comparing whole lists; the adaptive
    threshold shifted to two; and two aimed at the collection INTERIOR. No spec
    hole. In particular the ``opaque`` leaf is not usable as an answer key.

  * SPEC-TOO-STRONG — reshapes written and PROVEN (EXIT 0): the present-columns
    write-back analogue, the emptiness test by ``isEmpty``, the toggle as a
    ``match``, and the plural marker decided by matching the required list's SHAPE
    instead of its length. One reshape (found side sliced by the CONFIGURED length
    rather than the truncated one — observably equal, since the two lengths differ
    only where the present list is the shorter) was NOT closed: after four
    attempts the residual was the ``Id.run`` monadic wrapper over two
    syntactically identical terms, so this is recorded as an unclosed PROOF, not a
    spec hole.

  * REPAIR (this pass) — the audit found the collection INTERIOR entirely
    unpinned and closed it with two rivals. Every rendering witness in the
    battery, including the two earlier repairs, refutes by projecting ONE
    character at a measured offset that PRECEDES the opaque per-element text, so
    the whole-list arm was pinned only at its opening bracket: an impl emitting
    the right form with the wrong interior was rejected with nothing attributing
    that rejection to the spec. ``weak-list-separator-tight`` (elements joined
    without the space) and ``weak-naive-element-quoting`` (per-element rendering
    replaced by the verbatim single-value quoting, refuted at a quote-bearing
    name) close it. Both were landed AGAINST the opaque leaf, which the earlier
    passes had treated as unattackable there: the witness states its refutation at
    a point where the leaf's value is given by HYPOTHESIS rather than computed,
    and the gate's consistency probe confirms those hypotheses are jointly
    satisfiable. Both discriminate in both builds (rival EXIT 0, frozen EXIT 1)
    and both pass the forgery test (flipped claim on gold: ``No goals to be
    solved``; on the rival: a concrete residual).

  * ADMISSIBILITY strengthened. The ground ``have … := rfl`` is load-bearing (it
    fails against a wrong impl) but it does not show WHICH branch the F2P input
    reaches, because the spec pins ``result`` to a term over the same inputs — the
    same ``rfl`` would read identically for a no-op outcome. A second ``have`` now
    evaluates the outcome at that input to a concrete reported message; it was
    measured to VERIFY on the frozen impl (EXIT 0) and to FAIL against a rival
    (EXIT 1), so the admission is pinned to the reporting branch itself.

FOURTH-PASS AUDIT (independent adversarial re-derivation by a fourth auditor;
every claim is an exit code from the real verifier, run outside the gate).

  * SCOPE OF THIS PASS. The two INTERIOR, hypothesis-bearing witnesses added by
    the third pass were singled out for re-derivation, because among all shapes in
    this battery they are the one that can pass the gate while attesting to
    nothing: a witness whose ASSUMPTIONS are contradictory proves its refutation
    from absurdity, describes no real input, and — measured by the gate's own
    authors — still elaborates against the rival and still fails on gold, so it
    survives both halves of the discrimination check.

  * STATEMENT INTEGRITY across all sixteen current cases: the ``theorem
    correct_checkRequiredColumns`` statement and the whole post-conditions view
    were extracted per module and compared to the frozen file — byte-identical in
    every one (16/16). No obligation is weakened or restated.

  * THE THIRD PASS'S SATISFIABILITY ARGUMENT WAS TOO WEAK, AND ITS STATED REASON
    WAS FALSE. It rested on the gate's consistency probe finding no
    contradiction, justified by the claim that no tactic can derive ``False`` from
    an equation about an opaque term. That claim is refuted by build: a probe over
    two contradictory hypotheses about the SAME leaf (``pyReprStr "z"`` equal to
    two different strings) CLOSES (EXIT 0). The probe is therefore live for this
    exact shape — good news for the gate, but it means the probe's silence is
    ordinary incomplete-check evidence, not the impossibility result claimed. The
    prose above has been corrected accordingly.

  * SATISFIABILITY RE-ESTABLISHED POSITIVELY, which is what the earlier claim
    should have been. For each interior witness a concrete witnessing function was
    exhibited and checked: ``∃ f, f "a" = "'a'" ∧ f "b" = "'b'" ∧ f "c" = "'c'"``
    and ``∃ f, f "a'b" = "\"a'b\"" ∧ f "z" = "'z'"``, both closed by ``decide``
    (EXIT 0). The assumed inputs therefore exist and the refutations are about
    real points. Further, the assumed values are FAITHFUL to the platform, not
    merely consistent: the real builtin renders ``a'b`` in the double-quoted form
    and ``z`` in the single-quoted one, matching the hypotheses exactly.

  * DISCRIMINATION AND FORGERY, re-run for the three newest rivals. Each rival
    module alone fails (EXIT 1, correctly rejected); each witness elaborates
    against its rival (EXIT 0) and fails on the frozen solution (EXIT 1) with
    gold's goal REDUCED TO ``False`` — the frozen impl satisfies the equation the
    rival violates. With the ``¬`` dropped, gold reports ``No goals to be solved``
    while the rival is left holding a concrete residual inequation between the two
    messages. Gold's failure tracks the CLAIM, not the tactic shape.

  * THE RIVALS ARE WRONG OUTSIDE LEAN TOO, checked against the real platform
    rather than the model: ``str(["a'b", "z"])`` renders ``["a'b", 'z']`` where
    naive verbatim quoting yields the unescaped ``['a'b', 'z']``, and
    ``['a', 'b']`` where the tight separator yields ``['a','b']``. Neither is a
    reshape.

  * POINT SPREAD re-counted mechanically: twelve reject cases, twelve DISTINCT
    argument tuples, no duplicates. A stale "nine reject witnesses" count left by
    an earlier pass has been corrected — a shipped file must not miscount its own
    contents.

FIFTH-PASS AUDIT (independent adversarial re-derivation by a fifth auditor; every
claim is an exit code from the real verifier, run outside the gate).

  * RE-CHECKED, not trusted. Statement integrity across all sixteen then-current
    cases: the ``theorem correct_checkRequiredColumns`` statement and the whole
    spec view extracted per module and diffed against the frozen file —
    byte-identical 16/16, and ``variant_scope.variant_problems`` clean on all
    sixteen. Witness discrimination: all twelve then-shipped reject witnesses
    rebuilt by hand, rival EXIT 0 and frozen EXIT 1 in every one, reproducing
    each recorded ``gold_signature``. Forgery test (attack B′) on all twelve:
    with the ``¬`` dropped, gold's error CHANGES to ``No goals to be solved``
    while the same flipped claim against the rival leaves a concrete residual.
    Gold's exit code tracks the CLAIM, not the tactic shape, in all twelve.

  * OBSERVABILITY re-derived over a 195936-input cross-product of the five
    binders (requirement lengths up to 3, name pool including a quote-bearing
    name): every shipped rival differs from the modeled behavior on 312 to 93830
    inputs, and all seventeen behaviors — sixteen rivals plus the modeled one —
    are pairwise DISTINCT. No rival is a definitionally-equal reshape.

  * SPEC-TOO-WEAK — seventeen FURTHER wrong implementations were written against
    the frozen spec and ALL seventeen were rejected, including the no-columns
    branch rendering the whole collection, the empty collection rendered blank,
    the one-name arm routed through the platform per-element rendering, the
    toggle clearing unconditionally, and the mismatch report emitted as ``.ok``.
    No spec hole. The ``opaque`` leaf is again not usable as an answer key.

  * SPEC-TOO-STRONG — four NEW correct reshapes were written and PROVEN (EXIT 0):
    the relaxed truncation restated as a match, a combined no-op guard, the
    emptiness test by ``isEmpty`` (closed by a case split on the present list),
    and the present-columns write-back rebound through ``id`` (frozen ``rfl``
    retained). THREE further reshapes were NOT closed: after repeated attempts
    the residual was the ``Id.run`` monadic wrapper or a mis-shaped case split.
    Those are recorded as unclosed PROOFS and explicitly NOT as spec holes.

  * DIVERGENCE / TERMINATION lane, judged against the semantics this bundle
    actually sets. It sets NO ``set_option loom.semantics.termination`` at all
    (grepped: zero occurrences), so this is plain Lean and the elaborator
    enforces totality on every ``def``. Measured, three ways: (a) a self-recursive
    impl with no decreasing measure does not elaborate at all ("fail to show
    termination"), and its WITNESS FILE fails with the same termination error, so
    no witness can hold of it; (b) the same written ``partial def`` compiles in
    the witness file, but then BOTH the rival and the gold build fail with
    ``failed to synthesize`` — the gate's own stuck-instance screen shape — so
    gold's exit code would carry no information and the case is unshippable as
    ``witness-undecided``; (c) a non-progressing ``while`` whose result is
    DISCARDED verifies (EXIT 0), but that is not an observable divergence: the
    unreduced loop term is thrown away by ``Id``'s bind, and when the loop's
    result is actually USED both the claim and its flipped control fail. The
    absence of a divergence rival is therefore a carrier fact, not a convenience.

  * REPAIR (this pass) — FOUR genuine gaps found and closed, all four ports of
    nagini cases this port had dropped, each measured to discriminate in every
    build before being landed (rival module alone EXIT 1; witness against rival
    EXIT 0; witness against frozen EXIT 1; flipped claim on frozen EXIT 1 ``No
    goals to be solved``; flipped claim on rival EXIT 1 with a concrete
    residual):

      - ``weak-echo-found-side`` — the found SLOT was never pinned as an
        independent observable. An impl echoing the requirement into both slots
        emitted a perfectly-shaped message and was rejected for nothing the
        battery could attribute to the spec. Differs on 93830/195936.
      - ``weak-plural-token-swap`` — the pluralisation RULE had a rival
        (``weak-plural-drop``) but the emitted MARKER did not. Differs on
        90450/195936, with a behavior distinct from the rule rival's.
      - ``weak-bracket-token-swap`` — the offset projection pins that the
        whole-list form opens with a bracket, never WHICH bracket sits at each
        end; the interior rivals leave both ends untouched. Differs on
        90150/195936.
      - ``weak-adaptive-threshold-at-two`` — the renderer's THRESHOLD. Both
        existing arm-rivals delete an arm and so differ at every arity; this one
        keeps both arms and moves the switch, agreeing at arity 1 and at every
        arity ≥3. Differs on 26900/195936 and from ``weak-first-name-only`` on
        69500. NOTE, because it nearly went the other way: measured on a domain
        capped at requirement length 2 this rival looks EXTENSIONALLY EQUAL to
        ``weak-first-name-only`` and would have been discarded as vacuous. That
        was an artifact of the measuring domain, not a property of the rival;
        the two separate as soon as a three-name requirement is in the domain.
        A vacuity finding is only as good as the domain it was measured on.

  * PROSE CORRECTED, twice over. Two shipped witness comments still asserted that
    "no tactic can derive ``False`` from an equation about an opaque term" — the
    very claim the FOURTH pass had already retracted in this docstring after
    refuting it by build. Re-measured here three ways, on the exact leaves those
    two witnesses assume (``pyReprStr "a"`` and ``pyReprStr "a'b"`` each pinned to
    two different strings): the probe CLOSES in all three (EXIT 0). The claim is
    false, and a shipped file must not contradict its own audit record. Both
    comments now rest the satisfiability on the POSITIVELY exhibited models and
    say plainly that the probe's silence is an incomplete check. This changes no
    verdict — those two witnesses remain sound, and the probe being live for this
    shape is good news for the gate — but the stated reason was wrong.

  * A DANGLING POINTER was removed. The PORT NOTE directed the reader to "the
    module ``assessment``" for the per-case omission mapping; no such module
    exists in this bundle or anywhere in the repository, so the omission
    rationale the port claimed to document was absent from the artifact. The
    mapping is now the OMISSION LEDGER below, in the file the gate reads.

SIXTH-PASS AUDIT (independent adversarial re-derivation by a sixth auditor; every
claim is an exit code from the real verifier, run outside the gate, ~120 builds).

  * RE-CHECKED, not trusted. Statement integrity across all twenty then-current
    cases: the ``theorem correct_checkRequiredColumns`` statement AND the whole
    impl/proof-elided spec view extracted per module and diffed against the frozen
    file — byte-identical 20/20, ``variant_problems`` clean on all twenty. Witness
    discrimination: all sixteen shipped reject witnesses rebuilt by hand through
    the gate's own ``witness_file``, rival EXIT 0 and frozen EXIT 1 in every one
    (16/16), reproducing each recorded ``gold_signature``. Forgery test (attack
    B′) on all sixteen: with the ``¬`` dropped, gold's error CHANGES to ``No goals
    to be solved`` while the same flipped claim against the rival still fails on a
    concrete residual (``introN failed`` over a goal printing both messages, or
    ``decide`` reporting the two concrete strings). Gold's exit code tracks the
    CLAIM, not the tactic shape, in all sixteen. Both consistency probes rebuilt:
    EXIT 1 (``simp_all made no progress``), i.e. no forgery.

  * OBSERVABILITY re-derived independently over a 38936-input cross-product of the
    five binders (name pool including a quote-bearing name and the empty name,
    requirement lengths to 3): every shipped rival differs from the modeled
    behavior on 62 to 17830 inputs, and all seventeen behaviors — sixteen rivals
    plus the modeled one — are pairwise DISTINCT. No rival is a
    definitionally-equal reshape; no case is vacuous.

  * SPEC-TOO-WEAK — eighteen FURTHER wrong impls written against the frozen spec,
    ALL eighteen REJECTED (EXIT 1). Aimed at what the shipped rivals leave
    unattacked: the no-columns guard ignoring the relaxed regime; that guard's
    trailing noun; the mismatch guard comparing whole lists; the toggle comparing
    the whole present list, clearing unconditionally, and SETTING instead of
    clearing; the plural counted from the untruncated list; the relaxed truncation
    by ``drop`` and applied unconditionally; the no-columns branch rendering the
    whole collection or the PRESENT head; the adaptive threshold at ``≤ 1``; the
    empty collection rendered blank; a mismatch emitted as ``.ok``; the two
    rendered fields swapped; and four aimed at the ``opaque`` leaf (one-name arm
    routed through the platform per-element rendering, separator by semicolon).
    No spec hole. The opaque leaf is again not usable as an answer key.

  * SPEC-TOO-STRONG — reshapes written and PROVEN (EXIT 0): emptiness by
    ``isEmpty``; the relaxed truncation as a ``match``; the toggle as a ``match``;
    the no-columns guard with its ``&&`` commuted; a combined no-op guard. TWO
    reshapes a PRIOR pass had recorded as unclosed proofs were CLOSED here, so
    that record is corrected: the plural marker decided by the required list's
    SHAPE (closed after hoisting the arity equality to a ``have`` and rewriting,
    once the ``none`` arm is split off first), and the found side sliced by the
    CONFIGURED length (closed by pinning ``take (take …).length`` with
    ``Nat.min_eq_left/right`` and ``List.take_of_length_le``). ONE reshape remains
    unclosed after five attempts — the toggle deciding by a LENGTH comparison,
    which is observably equal to the frozen toggle (measured: 0 differences over
    the 853 toggle-reachable inputs) but whose proof needs the list-equality ↔
    length-inequality bridge. Recorded as an unclosed PROOF and explicitly NOT a
    spec hole.

  * THE THREE LOAD-BEARING PROSE CLAIMS re-measured, all three hold.
    ``pos-enabled-guard-as-match``: the frozen ``rfl`` alone rebuilt against that
    reshape FAILS (EXIT 1, ``rfl failed … not definitionally equal``), so it
    genuinely re-proves. ``admiss-ground-report-instance``: the whole admissibility
    proof body spliced against a WRONG impl FAILS (EXIT 1) and the FIRST error is
    on the ground ``have`` itself (``Type mismatch: rfl … but is expected to have
    type problem_spec_… ["time","b"]``), so the discharge is a real evaluation at
    the F2P-shaped input and not a tautology. The FRAME-MUTATION vacuity claim:
    the write-back analogue (present-columns local rebound through ``id``) was
    built and VERIFIES (EXIT 0), so it is a positive and cannot be made a rival.

  * SATISFIABILITY of the two hypothesis-bearing witnesses re-established
    POSITIVELY rather than from the probes' silence, by exhibiting the witnessing
    functions inside the frozen file: ``∃ f, f "a" = "'a'" ∧ f "b" = "'b'" ∧ f "c"
    = "'c'"`` (EXIT 0, at ``pyStrRepr``) and ``∃ f, f "a'b" = "\"a'b\"" ∧ f "z" =
    "'z'"`` (EXIT 0). The assumed values are also FAITHFUL to the platform,
    checked against it directly: it renders ``a'b`` double-quoted and ``z``
    single-quoted, matching the hypotheses. And the FOURTH pass's retraction is
    confirmed: ``False`` IS derivable from two contradictory hypotheses about the
    same leaf (EXIT 0), so the probe is live for this shape and its silence is an
    ordinary incomplete check.

  * DIVERGENCE / TERMINATION re-judged against the semantics the bundle actually
    sets — it sets NO ``set_option loom.semantics.termination`` (grepped: 0
    occurrences), so neither prompt branch applies verbatim and plain Lean's
    totality checker governs. Re-measured: a self-recursive impl with no
    decreasing measure does not elaborate at all (``fail to show termination``),
    and written as a ``partial def`` the witness file fails on BOTH sides — on the
    rival with ``unfold failed to unfold`` and on gold with ``unsolved goals`` —
    so gold's exit code would carry no information and the case is unshippable as
    ``witness-undecided``. The absence of a divergence rival is a carrier fact.

  * REPAIR (this pass) — ONE genuine gap, and it is an OMISSION recorded as
    inexpressible that is not. ``pos-internal-failure-handled`` ports nagini's
    ``internal-signal-caught-admitted``, which the ledger below had dismissed
    because "the error is a VALUE in the result, not a control transfer". That
    reason conflates the CHANNEL with the CASE: the nagini case is a POSITIVE
    asserting that an impl which fails internally, HANDLES it, and still delivers
    the gold outcome must be ACCEPTED — an obligation about the delivered value,
    which this carrier states directly with an internal ``Except`` failure raised
    and consumed in an intermediate step. Built EXIT 0, and the frozen ``rfl``
    alone FAILS on it (EXIT 1), so it re-proves genuinely rather than re-spelling
    the frozen term. Before it the battery had no positive pinning that an
    internally-failing-but-delivering impl is admitted, which is the direction
    the four ``nondelivery-*`` entries are the mirror of. Two further nagini
    entries were probed and NOT landed, with the build reason recorded at their
    ledger lines: the ``recursive-descent`` port (a recursive helper ``def`` is
    admissible, but its bridge to ``String.intercalate`` did not close), and the
    four control-flow ``nondelivery-*`` rivals, whose nagini vacuity has no
    analogue in a pinned equality over a total function.

SEVENTH-PASS AUDIT (independent adversarial re-derivation by a seventh auditor;
every claim is an exit code from the real verifier, run outside the gate, 143
builds, no build timed out so every exit code is a real verdict).

  * RE-CHECKED, not trusted. Statement integrity across all twenty-one
    then-current cases: the ``theorem correct_checkRequiredColumns`` statement
    AND the whole impl/proof-elided spec view extracted per module and diffed
    against the frozen file — byte-identical 21/21, ``variant_problems`` clean on
    all twenty-one. Witness discrimination: all sixteen then-shipped reject
    witnesses rebuilt by hand through the gate's own ``witness_file``, rival EXIT
    0 and frozen EXIT 1 in every one (16/16), reproducing each recorded
    ``gold_signature``. Both consistency probes rebuilt: EXIT 1 (``simp_all made
    no progress``), so no witness proves its refutation from a contradiction.

  * FORGERY (attack B′) on all sixteen: with the ``¬`` dropped, gold's error
    CHANGES to ``No goals to be solved`` — the frozen impl PROVES the equation
    the witness refutes — while the same flipped claim against the rival still
    fails on a concrete residual (``introN failed`` on a goal printing both
    messages, ``decide`` reporting the two concrete strings, or the
    ``noConfusion`` type mismatch showing the rival's ``.error`` where gold has
    ``.ok``). Gold's exit code tracks the CLAIM, not the tactic shape, 16/16.

  * REVEAL-THE-TYPE, added because a ``rewrite``-pattern signature is the one
    class where "it looks semantic" is weakest evidence: for both
    hypothesis-bearing witnesses and for ``weak-first-name-only`` the final
    ``exact absurd`` was replaced by a deliberate type error on ``h``, so Lean
    prints the hypothesis's REAL type on each side. On gold the goal is already
    ``⊢ False`` with the assumed leaf equations intact — i.e. the preceding
    tactics DISCHARGED the equation for the frozen impl — while on the rival
    ``h`` is a concrete residual inequation between the two whole messages
    (``",".intercalate ["'a'","'b'"]`` against ``", ".intercalate …``; the naive
    verbatim quoting against ``["\"a'b\"", "'z'"]``). That pair is a genuine
    refutation, not a tactic mismatch, and it is the strongest gold-side evidence
    available on this carrier.

  * OBSERVABILITY re-derived independently over a 58480-input cross-product of
    the five binders, from a Python transliteration written from the spec text
    rather than from the Lean rivals, and with the opaque per-element rendering
    modeled as an ABSTRACT symbol rather than identified with the verbatim
    quoter (conflating the two would make ``weak-naive-element-quoting`` read as
    a reshape). Every shipped rival differs from the modeled behavior on 85 to
    27024 inputs, and all seventeen behaviors are pairwise DISTINCT. No rival is
    a definitionally-equal reshape; no case is vacuous.

  * SPEC-TOO-WEAK — twenty-three FURTHER wrong impls written against the frozen
    spec, ALL twenty-three REJECTED (EXIT 1): the toggle comparing the truncated
    requirement, the whole present list, clearing unconditionally, and SETTING
    instead of clearing; the plural counted from the configured list and emitted
    at arity one; the relaxed truncation by ``drop``, applied unconditionally,
    and applied to the wrong list; the no-columns branch naming the present head,
    rendering the whole collection, and with its trailing noun altered; the
    mismatch emitted as ``.ok``; the two rendered fields transposed; the adaptive
    threshold at ``≤ 1``; the empty collection rendered blank; the separator's
    space moved ahead of its comma; the collection's element order reversed; and
    three aimed at the ``opaque`` leaf (the one-name arm routed through the
    platform per-element rendering, the one-name arm double-quoted); plus the two
    GUARD-CONDITION probes described under REPAIR below, which were rejected here
    like the rest and then, unlike the rest, PROMOTED into the battery because no
    shipped case attributed their rejection to the spec. No spec hole; the opaque
    leaf is again not usable as an answer key. A rejection alone is what a probe
    buys; the promotion is what makes it evidence.

  * SPEC-TOO-STRONG — reshapes written and PROVEN (EXIT 0): the no-columns
    emptiness test by ``isEmpty``; the no-columns head read from the CONFIGURED
    list rather than the truncated one; the relaxed truncation as a ``match``; a
    combined no-op guard. The two reshapes the sixth pass reported closing were
    INDEPENDENTLY re-closed here from scratch, by different tactics than that
    pass recorded, which is the point of re-deriving rather than trusting: the
    found side sliced by the CONFIGURED length (closed by ``List.take_take`` +
    ``Nat.min_self`` then ``rfl``, where the prior pass used
    ``Nat.min_eq_left/right`` and ``List.take_of_length_le``) and the plural
    marker decided by the required list's SHAPE (closed by hoisting the
    arity/length bridge to a ``have`` over a UNIVERSALLY QUANTIFIED list and
    rewriting with it). The spec admits genuinely reshaped correct impls. The one
    reshape the sixth pass left unclosed — the toggle deciding by a LENGTH
    comparison — was NOT re-attempted here, so that record stands as it is: an
    unclosed PROOF, explicitly not a spec hole.

  * THE THREE LOAD-BEARING PROSE CLAIMS re-measured, all three hold.
    ``pos-enabled-guard-as-match`` and ``pos-internal-failure-handled``: the
    frozen ``rfl`` alone rebuilt against each FAILS (EXIT 1), so both genuinely
    re-prove rather than re-spelling the frozen term.
    ``admiss-ground-report-instance``: the whole admissibility body spliced
    against a WRONG impl FAILS, and — measured separately — the ground ``have``
    ALONE fails there with ``Type mismatch: rfl … but is expected to have type
    problem_spec_… ["time","b"]`` while the second ``have`` ALONE fails with a
    goal printing the transposed message, so BOTH halves of the admission are
    load-bearing, not just the pair. The FRAME-MUTATION vacuity claim: the
    write-back analogue was built and VERIFIES (EXIT 0), so it is a positive and
    cannot be made a rival.

  * SATISFIABILITY of the two hypothesis-bearing witnesses re-established
    POSITIVELY, not from the probes' silence: the witnessing functions were
    exhibited and checked (``∃ f, f "a" = "'a'" ∧ f "b" = "'b'" ∧ f "c" = "'c'"``
    and ``∃ f, f "a'b" = "\"a'b\"" ∧ f "z" = "'z'"``, both EXIT 0). The assumed
    values are FAITHFUL to the platform, checked against it directly. And the
    probe-liveness control is confirmed: ``False`` IS derivable from two
    contradictory hypotheses about the same leaf (EXIT 0), so the probe is live
    for this shape and its silence is an ordinary incomplete check.

  * DIVERGENCE / TERMINATION re-judged against the semantics this bundle
    actually sets — it sets NO ``set_option`` at all (grepped: zero), so plain
    Lean's totality checker governs and neither prompt branch applies verbatim.
    Re-measured three ways: a self-recursive impl with no decreasing measure does
    not elaborate (``fail to show termination``); written as a ``partial def``
    the witness file fails on BOTH sides — on the rival with ``unfold failed to
    unfold``, on gold with ``decide proved that False is false`` — so gold's exit
    code carries no information about the claim and the case is unshippable as
    ``witness-undecided``; and a non-progressing ``while`` whose result is USED
    fails to close the obligation without being refutable. The absence of a
    divergence rival is a carrier fact, not a convenience.

  * REPAIR (this pass) — TWO genuine gaps, and they are the same shape as each
    other: the battery attacked both report-emitting branches' CONTENT
    exhaustively while leaving each branch's own GUARD CONDITION unpinned. Every
    rival before this pass reached its branch by the frozen guard and then
    changed what the branch emits; an impl that emitted each message correctly
    but entered the branch on the WRONG CONDITION was rejected with nothing in
    the battery attributing that rejection to the spec. Both were measured
    behaviorally NEW (extensionally distinct from all sixteen shipped rivals and
    from the modeled behavior) and both diverge at the ``.ok``/``.error``
    CONSTRUCTOR, which is a coarser and more consequential observable than any
    message-content divergence in the battery:

      - ``weak-mismatch-guard-whole-list`` — the mismatch guard compares the
        WHOLE present list to the requirement instead of its leading slice, so a
        table holding its required columns FOLLOWED BY OTHERS is reported as
        invalid. Differs on 912/58480, all 912 at the constructor.
      - ``weak-nocols-guard-ignores-relax`` — the no-columns guard drops its
        relaxed-regime conjunct, so a relaxed table that legitimately has no
        columns yet is reported instead of passing. Differs on 170/58480, all 170
        at the constructor, and it is the only rival whose refutation point is a
        RELAXED table with no columns.

    Both discriminate in every build (rival module alone EXIT 1; witness against
    rival EXIT 0; witness against frozen EXIT 1 with the claim-tracking
    ``noConfusion`` signature; flipped claim on frozen EXIT 1 ``No goals to be
    solved``; flipped claim on rival EXIT 1 holding a concrete ``.error``
    residual). Neither binds anything, so neither needs a consistency probe.

OMISSION LEDGER — every nagini case not ported, with the reason. "Inexpressible"
means the carrier cannot state the attack; "covered" means a shipped Lean case
already discriminates at the same observable. Four entries previously in this
ledger were found EXPRESSIBLE by the fifth pass and are now shipped cases
(echo-demanded-into-found, boundary-plural-token-swap, boundary-bracket-token-swap,
partial-domain-len2-guard); they are listed at their new ids above.

  * ``internal-signal-caught-admitted`` — was recorded here as INEXPRESSIBLE and
    is NOT; it is now shipped as ``pos-internal-failure-handled``. See that case
    and the SIXTH-PASS record above. The reason previously stated ("the error is
    a VALUE in the result, not a control transfer, so there is no handler and no
    raise to misplace") conflated the CHANNEL with the CASE. This nagini case is
    a POSITIVE, and what it tests is that an impl which fails INTERNALLY, HANDLES
    the failure, and still delivers the gold outcome is ACCEPTED — not that a
    raise reaching the caller is rejected, which is the ``nondelivery-*`` lane
    below. An internal ``Except`` failure raised and consumed in an intermediate
    step is exactly this carrier's internal-failure channel, so the case ports
    directly: built EXIT 0, and the frozen ``rfl`` alone FAILS on it, so it
    genuinely re-proves rather than re-spelling the frozen term.
  * ``nondelivery-signalled-away-report``,
    ``nondelivery-signalled-away-render``, ``nondelivery-reraise-from-handler``,
    ``nondelivery-late-after-build`` — INEXPRESSIBLE as RIVALS, on a narrower and
    checkable ground than the entry above used. These four leave BY an exceptional
    exit reaching the caller, and they verified on nagini because an ``Ensures``
    clause is silent on such an exit, so every clause held vacuously. Here the
    obligation is a pinned EQUALITY on the returned value of a total function:
    there is no exit the postcondition is silent about, hence no vacuity to
    exploit. The value-level analogue — leaving by the wrong constructor — is
    covered, and since the seventh pass it is covered by SHIPPED cases rather
    than only by a rejected probe: ``weak-mismatch-guard-whole-list`` and
    ``weak-nocols-guard-ignores-relax`` both answer ``.error`` where the spec
    answers ``.ok``, and each is refuted by ``Except.noConfusion`` at the
    constructor. (A mismatch reported as ``.ok`` — the opposite direction — was
    also one of the spec-too-weak probes, rejected.)
  * ``nondelivery-true-contract-override`` — INEXPRESSIBLE as a rival. It
    overrides a contract to ``True``. Here the obligation is a pinned equality in
    the FROZEN spec region, which region surgery cannot touch; a case that
    weakened it would fail ``same_spec`` rather than test anything.
  * ``nondelivery-partial-multiname``, ``non-completion-render-multiname``,
    ``non-completion-report-assembly``, ``non-completion-render-loop-no-step`` —
    INEXPRESSIBLE on this carrier, and demonstrated so rather than asserted: see
    the DIVERGENCE lane above. Non-completion is not an observable of a total
    function here — the elaborator rejects a non-terminating ``def`` outright, and
    the ``partial def`` route makes BOTH sides of the discrimination check fail on
    a stuck instance, so gold's exit code would carry no information.
  * ``recursive-descent-admitted`` — INEXPRESSIBLE. It admits a recursive helper's
    contract to itself. The modeled core is non-recursive and no case may add a
    declaration, so there is no contract to admit; the assumption tokens that
    would express it are banned by scope.
  * ``aliased-input-rewritten``, ``frame-mutation-write-run`` — VACUOUS, shown by
    construction (see the FRAME / PERMISSION MUTATION note above). Lean is
    referentially transparent; the only expressible analogue of writing to an
    input VERIFIES, so it is a positive and cannot be made a rival.
  * ``pos-control-reorder-locals`` — COVERED by ``pos-fields-bound-to-locals``.
  * ``admissibility-three-readonly-inputs`` — COVERED by
    ``admiss-ground-report-instance``, whose ground discharge was measured
    load-bearing (it fails against a wrong impl).
  * ``partial-domain-first-name-only``, ``partial-domain-drop-first-name-helper``,
    ``plural-marker-drop``, ``overapprox-always-bracketed`` — COVERED by
    ``weak-first-name-only``, ``weak-drop-leading-name``, ``weak-plural-drop`` and
    ``weak-always-list-form`` respectively.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-13033"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Every anchor lies ENTIRELY inside the impl region (or, for the positive that
# re-proves, the proof region) so same_spec stays byte-identical.

# The whole CHANGED (adaptive-rendering) mismatch branch of the impl.
_I_MISMATCH = (
    "    else if colnames.take required.length != required then\n"
    "      return .error (className ++ \" object is invalid - expected \" ++\n"
    "        renderNames required ++ \" as the first column\" ++ plural ++\n"
    "        \" but found \" ++ renderNames (colnames.take required.length))"
)

# The plural line of the impl (+ the following guard line, to make it unique
# against the identically-worded spec-helper line at a different indentation).
_I_PLURAL = (
    "\n    let plural := if required.length > 1 then \"s\" else \"\"\n"
    "    if !requiredColumnsRelax && colnames.length == 0 then"
)

# The check-disabled no-op branch of the impl (+ following line for uniqueness).
_I_DISABLED = (
    "  if !requiredColumnsEnabled then\n"
    "    return .ok requiredColumnsRelax\n"
    "  match requiredColumns with"
)

# The no-configured-names no-op arm of the impl.
_I_NONE = "  | none => return .ok requiredColumnsRelax"

# The relaxed-truncation `required` binding (+ plural line for uniqueness).
_I_REQUIRED = (
    "    let required := if requiredColumnsRelax then reqCols.take colnames.length else reqCols\n"
    "    let plural := if required.length > 1 then \"s\" else \"\""
)

# The relaxed-regime toggle of the impl.
_I_TOGGLE = (
    "    let newRelax := if requiredColumnsRelax && reqCols == colnames.take reqCols.length then\n"
    "                      false else requiredColumnsRelax\n"
    "    return .ok newRelax"
)

# The no-present-columns report branch of the impl (its class-name prefix).
_I_NOCOLS = (
    "    if !requiredColumnsRelax && colnames.length == 0 then\n"
    "      return .error (className ++ \" object is invalid - expected '\" ++ required.headD \"\" ++\n"
    "        \"' as the first column\" ++ plural ++ \" but time series has no columns\")"
)

# The check-disabled guard of the impl, as a Bool `if` (+ following lines for
# uniqueness) — reshaped by the control-flow positive into a `match`.
_I_ENABLED_IF = (
    "  if !requiredColumnsEnabled then\n"
    "    return .ok requiredColumnsRelax\n"
    "  match requiredColumns with"
)

# The frozen proof body (proof region).
_P_FROZEN = (
    "  intro className requiredColumnsEnabled requiredColumns requiredColumnsRelax colnames\n"
    "  rfl"
)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation the spec is SPEC-TOO-STRONG. Each
    # keeps the theorem statement byte-identical; the first two reshapes below
    # preserve the definitional form so the frozen `rfl` still closes, and the
    # third (added by audit) changes the branch structure and therefore RE-PROVES
    # by a Bool case split (no helper lemma, no axiom, no assumption token
    # introduced in any of them).
    #
    # AUDIT NOTE on the strength of the first two. Both reshape only by binding
    # or inlining a `let`, so they zeta-reduce back to the frozen term; the
    # frozen `rfl` closes them for that reason, and their passing therefore does
    # NOT by itself show the spec tolerates a genuinely different SHAPE — a
    # definitionally-equal reshape verifies while testing little. They are kept
    # (they are the faithful ports of nagini's reorder/swap-locals positive, and
    # they do pin the two rendered fields and the toggle payload), but the
    # control-flow positive is what carries the SPEC-TOO-STRONG evidence.
    #
    # Ports nagini case 1 (pos-control-reorder-locals): the nagini positive
    # reordered the local assignments and swapped the two field renders of site
    # B. Here the analogous structural reshape binds the two rendered fields to
    # locals before assembling the message.
    # =====================================================================
    {
        "id": "pos-fields-bound-to-locals",
        "kind": "soundness",
        "expect": "verify",
        # Bind the found and expected rendered collections to locals (found
        # first) before assembling the message. Same value flow into the report,
        # so the result is unchanged on every input and the frozen `rfl` closes
        # after the locals zeta-reduce.
        "module": _swap(
            _BASE, _I_MISMATCH,
            "    else if colnames.take required.length != required then\n"
            "      let foundField := renderNames (colnames.take required.length)\n"
            "      let expectedField := renderNames required\n"
            "      return .error (className ++ \" object is invalid - expected \" ++\n"
            "        expectedField ++ \" as the first column\" ++ plural ++\n"
            "        \" but found \" ++ foundField)",
        ),
        "rationale": "the CHANGED clause is reshaped by binding the two rendered "
                     "collections to locals (found bound first) before assembling "
                     "the message; the assembled value is identical on every "
                     "input, so `result = checkRequiredColumns …` still holds. "
                     "Must verify, else the adaptive-rendering clause is "
                     "SPEC-TOO-STRONG. Proof: the frozen tactic body is retained "
                     "(the locals zeta-reduce, `rfl` closes). Ports nagini's "
                     "reorder/swap-locals positive to the single modeled site.",
    },
    {
        "id": "pos-toggle-inlined",
        "kind": "soundness",
        "expect": "verify",
        # Inline the `newRelax` local into the returned value. Same result on
        # every input; the frozen `rfl` closes.
        "module": _swap(
            _BASE, _I_TOGGLE,
            "    return .ok (if requiredColumnsRelax && reqCols == colnames.take reqCols.length then\n"
            "                  false else requiredColumnsRelax)",
        ),
        "rationale": "the relaxed-toggle clause is reshaped by inlining the "
                     "`newRelax` local into the `.ok` payload; the returned flag "
                     "is identical on every input, so `result = "
                     "checkRequiredColumns …` still holds. Must verify. Proof: "
                     "frozen tactic body retained (the local zeta-reduces, `rfl` "
                     "closes). Defends the toggle clause with a second correct "
                     "reshape on a different region than the rendering positive.",
    },
    # A CONTROL-FLOW positive, added by audit. The two positives above reshape
    # only by binding/inlining a local, so they zeta-reduce back to the frozen
    # term and the frozen `rfl` closes them unchanged — which means neither can
    # distinguish "the spec accepts a genuinely differently-shaped correct impl"
    # from "the reshape was definitionally the frozen impl". This one changes the
    # branch STRUCTURE of the no-op guard (a `Bool` scrutinee `match` in place of
    # the `if !…`), which is NOT zeta-equal: measured, the frozen `rfl` FAILS on
    # it, so it must genuinely re-prove (a one-line `cases` split, still inside
    # the proof region, no lemma/axiom/assumption token added). That makes it the
    # only positive here whose verification is evidence the spec admits a
    # reshaped correct impl rather than a re-spelling of the frozen one.
    {
        "id": "pos-enabled-guard-as-match",
        "kind": "soundness",
        "expect": "verify",
        # Decide the check-disabled no-op by matching on the Bool toggle instead
        # of testing its negation. Same outcome on every input, but the branch
        # structure differs, so the obligation is re-proven by a case split.
        "module": _swap(
            _swap(
                _BASE, _I_ENABLED_IF,
                "  match requiredColumnsEnabled with\n"
                "  | false => return .ok requiredColumnsRelax\n"
                "  | true =>\n"
                "  match requiredColumns with",
            ),
            _P_FROZEN,
            "  intro className requiredColumnsEnabled requiredColumns requiredColumnsRelax colnames\n"
            "  cases requiredColumnsEnabled <;> rfl",
        ),
        "rationale": "the check-disabled no-op clause is reshaped from a negated "
                     "`if` guard into a `match` on the Bool toggle; the returned "
                     "outcome is identical on every input, so `result = "
                     "checkRequiredColumns …` still holds. Must verify, else the "
                     "no-op clause is SPEC-TOO-STRONG about the FORM of the "
                     "branch rather than the value. Unlike the two positives "
                     "above this reshape is NOT definitionally the frozen term "
                     "(the frozen `rfl` alone does not close it — measured), so "
                     "the obligation is genuinely re-proven, by splitting the "
                     "Bool and closing each branch by `rfl`. No lemma, axiom or "
                     "assumption token is introduced and the theorem statement "
                     "is byte-identical.",
    },
    # An INTERNAL-FAILURE-HANDLING positive, added by the sixth-pass audit. This
    # is the port of nagini case 1 (`internal-signal-caught-admitted`), which the
    # OMISSION LEDGER had recorded as INEXPRESSIBLE on the ground that "the error
    # is a VALUE in the result, not a control transfer, and there is no handler
    # and no raise to misplace". Measured: that reason confuses the CHANNEL with
    # the CASE. The nagini case does not test a raise reaching the caller — the
    # `nondelivery-*` rivals do that, and their value-level analogue (a mismatch
    # returned as `.ok`) is indeed shipped as a rejected probe. What it tests is
    # the mirror obligation: an impl that fails INTERNALLY, HANDLES it, and still
    # delivers the gold outcome must be ACCEPTED, else the spec constrains the
    # internal shape rather than the delivered value. That is expressible here,
    # because an internal `Except` failure raised and consumed in an intermediate
    # step IS this carrier's internal-failure channel. Built: EXIT 0. It is a
    # genuine re-proof, not a re-spelling — the frozen `rfl` alone FAILS on it
    # (measured: `rfl failed ... not definitionally equal`), because the consumed
    # probe branches on the relax flag, so the obligation is closed by a Bool
    # split. Without it the battery had no positive at all pinning that an
    # internally-failing-but-delivering impl is admitted.
    {
        "id": "pos-internal-failure-handled",
        "kind": "soundness",
        "expect": "verify",
        # Raise an internal Except-carried failure, CONSUME it in place (both
        # arms continue), and then deliver the frozen outcome unchanged.
        "module": _swap(
            _swap(
                _BASE, _I_DISABLED,
                "  if !requiredColumnsEnabled then\n"
                "    return .ok requiredColumnsRelax\n"
                "  let probe : Except String Unit :=\n"
                "    if requiredColumnsRelax then .error \"internal\" else .ok ()\n"
                "  match probe with\n"
                "  | .error _ => pure ()\n"
                "  | .ok _ => pure ()\n"
                "  match requiredColumns with",
            ),
            _P_FROZEN,
            "  intro className requiredColumnsEnabled requiredColumns requiredColumnsRelax colnames\n"
            "  cases requiredColumnsRelax <;> rfl",
        ),
        "rationale": "an internal failure is raised and HANDLED before the "
                     "outcome is delivered: the impl builds an internal "
                     "`Except`-carried failure (on the relaxed regime), consumes "
                     "it in place — both arms continue — and then returns exactly "
                     "the frozen outcome, so `result = checkRequiredColumns …` "
                     "holds on every input. Must verify, else the spec would "
                     "constrain HOW an implementation fails internally rather "
                     "than WHAT it delivers, i.e. it would reject a correct "
                     "implementation shape (internal failure handling) => "
                     "SPEC-TOO-STRONG. Together with the shipped value-level "
                     "non-delivery probe (a mismatch returned as `.ok`, which is "
                     "rejected) this pins the obligation to the DELIVERED "
                     "outcome, not to the absence of an internal failure. "
                     "Measured NOT definitionally the frozen term: the frozen "
                     "`rfl` alone fails on it, so the obligation is genuinely "
                     "re-proven by splitting the Bool the consumed probe reads. "
                     "No lemma, axiom or assumption token is introduced and the "
                     "theorem statement is byte-identical. Ports nagini case "
                     "`internal-signal-caught-admitted`, which an earlier "
                     "revision of the ledger below had recorded as "
                     "inexpressible.",
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is
    # SATISFIABLE (non-vacuous) at the normal, F2P-shaped reporting input rather
    # than only in the abstract. The frozen theorem carries NO precondition
    # hypothesis (the modeled behavior is total, so `∀` is unguarded), so the
    # nagini precondition-admission probe (case 2) has no binder to attack here;
    # the honest analogue is to discharge the spec predicate by evaluation at a
    # ground mismatch-reporting input (the multi-name F2P scenario) alongside the
    # frozen obligation. Ports nagini case 2 (admissibility-three-readonly-inputs).
    # =====================================================================
    {
        "id": "admiss-ground-report-instance",
        "kind": "admissibility",
        "expect": "verify",
        # Discharge the obligation at the F2P-shaped multi-name mismatch input by
        # `rfl` (a `have`), then close the frozen obligation verbatim. Nothing is
        # assumed: no new declaration, statement byte-identical.
        "module": _swap(
            _BASE, _P_FROZEN,
            "  have _ground : problem_spec_checkRequiredColumns \"TimeSeries\" true "
            "(some [\"time\", \"a\"]) false [\"time\", \"b\"]\n"
            "      (implementation_checkRequiredColumns \"TimeSeries\" true "
            "(some [\"time\", \"a\"]) false [\"time\", \"b\"]) := rfl\n"
            # Strengthened by a later audit pass. The `have` above discharges the
            # obligation at the F2P-shaped input, but the spec pins `result` to a
            # term over the same inputs, so `rfl` closes it without ever showing
            # WHICH outcome that input produces — it would read the same if the
            # input landed in a no-op branch. This second `have` EVALUATES the
            # modeled behavior at that input down to a concrete reported message,
            # so the admission is pinned to the reporting branch the F2P actually
            # exercises: the whole required collection and the whole present
            # leading slice both rendered in the multi-name form, and the noun
            # pluralised. Measured load-bearing: it FAILS against a wrong impl.
            "  have _report : implementation_checkRequiredColumns \"TimeSeries\" true "
            "(some [\"time\", \"a\"]) false [\"time\", \"b\"]\n"
            "      = .error (\"TimeSeries\" ++ \" object is invalid - expected \" ++ "
            "pyListRepr [\"time\", \"a\"] ++\n"
            "          \" as the first column\" ++ \"s\" ++ \" but found \" ++ "
            "pyListRepr [\"time\", \"b\"]) := by\n"
            "    unfold implementation_checkRequiredColumns\n"
            "    simp only [Id.run, pure, bind]\n"
            "    norm_num [renderNames, List.take, List.headD]\n"
            "    intro h\n"
            "    exact absurd h (by decide)\n"
            + _P_FROZEN,
        ),
        "rationale": "the obligation is discharged at a ground multi-name "
                     "mismatch-reporting input (the F2P scenario: a two-name "
                     "requirement, a present leading slice that differs) by "
                     "`rfl`, then the frozen obligation is closed verbatim. "
                     "Verifies (else the modeled behavior is unsatisfiable at "
                     "exactly the input the F2P exercises — the analogue of "
                     "PRECOND-TOO-STRONG). Nothing is assumed: no new "
                     "declaration, the theorem statement is byte-identical, and "
                     "the ground instance is a `have` inside the existing tactic "
                     "body. A second `have` EVALUATES the outcome at that input "
                     "to a concrete reported message, which pins the admission to "
                     "the reporting branch rather than to an unspecified one: the "
                     "`rfl` discharge alone would read identically if the input "
                     "landed in a no-op branch, since the spec pins `result` to a "
                     "term over the same inputs. Ports nagini's "
                     "three-readonly-inputs admissibility "
                     "probe.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve the F2P, so a
    # verifying rival would be a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at one
    # concrete input.
    # =====================================================================

    # ---- the fix itself: render only the FIRST name (nagini case 4) ----
    {
        "id": "weak-first-name-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix behavior: on a mismatch, name only the first required name and
        # the first present name (each as one quoted name), regardless of how
        # many columns are required.
        "module": _swap(
            _BASE, _I_MISMATCH,
            "    else if colnames.take required.length != required then\n"
            "      return .error (className ++ \" object is invalid - expected '\" ++ required.headD \"\" ++\n"
            "        \"' as the first column\" ++ plural ++ \" but found '\" ++ colnames.headD \"\" ++ \"'\")",
        ),
        "refinement": "this IS the pre-fix behavior: naming only the first "
                      "required name and the first present name regardless of how "
                      "many columns are required. For the reported scenario (a "
                      "two-name requirement with a present leading slice that "
                      "differs only after the first name) it emits a message "
                      "naming a single pair whose two heads coincide — the "
                      "misleading report the issue is about — instead of the full "
                      "expected and found collections. The F2P test asserts the "
                      "full-collection message verbatim, so the faithful real "
                      "patch would NOT resolve.",
        "rationale": "REJECT from the adaptive-rendering clause: on a multi-name "
                     "mismatch the spec renders the WHOLE collection (the "
                     "bracketed list form, beginning `[`) while the rival renders "
                     "the single quoted first name (beginning `'`), so the "
                     "reported message — hence `result` — differs. Binder spread: "
                     "className=\"TimeSeries\", enabled, a two-name requirement, "
                     "strict, mismatching present columns.",
        "witness": (
            "-- Refuted at the reported multi-name scenario. The expected-side\n"
            "-- render diverges at its very first character: the whole-list form\n"
            "-- begins '[' where the rival's single-quote form begins '\\''. That\n"
            "-- character sits at a fixed offset past the concrete common prefix,\n"
            "-- BEFORE any opaque per-element text, so it is decidable.\n"
            "example : ¬ problem_spec_checkRequiredColumns \"TimeSeries\" true (some [\"time\",\"a\"]) false [\"time\",\"b\"]\n"
            "    (implementation_checkRequiredColumns \"TimeSeries\" true (some [\"time\",\"a\"]) false [\"time\",\"b\"]) := by\n"
            "  unfold problem_spec_checkRequiredColumns implementation_checkRequiredColumns checkRequiredColumns\n"
            "  simp only [Id.run, bind, pure]\n"
            "  norm_num [renderNames, pyListRepr, pyStrRepr, List.take, List.headD]\n"
            "  rw [if_neg (by decide : ¬ ((\"b\":String) = \"a\"))]\n"
            "  rw [if_neg (by decide : ¬ ((\"b\":String) = \"a\"))]\n"
            "  intro h\n"
            "  rw [Except.error.injEq] at h\n"
            "  have hd := congrArg (fun t => (t.data)[40]?) h\n"
            "  simp only [String.data_append] at hd\n"
            "  exact absurd hd (by decide)\n"
        ),
    },

    # ---- drop the LEADING name of each rendered collection (nagini case 6) ----
    {
        "id": "weak-drop-leading-name",
        "kind": "uniqueness",
        "expect": "reject",
        # A partial-domain miss on the rendering: render the collections with
        # their FIRST name dropped, so a multi-name report omits the leading
        # required/present column. (Ports nagini's site-A drop-first-name loop
        # onto the single modeled rendering site.)
        "module": _swap(
            _BASE, _I_MISMATCH,
            "    else if colnames.take required.length != required then\n"
            "      return .error (className ++ \" object is invalid - expected \" ++\n"
            "        renderNames (required.drop 1) ++ \" as the first column\" ++ plural ++\n"
            "        \" but found \" ++ renderNames ((colnames.take required.length).drop 1))",
        ),
        "refinement": "a faithful real patch that rendered the collections with "
                      "their leading name dropped would omit the first required "
                      "column from the reported message (e.g. show only the "
                      "trailing name instead of the whole list). The F2P test "
                      "asserts the FULL collection including its leading name, so "
                      "the faithful patch would NOT resolve.",
        "rationale": "REJECT from the adaptive-rendering clause: dropping the "
                     "leading name turns a two-name collection into a one-name "
                     "collection, which the adaptive renderer shows as a single "
                     "quoted name (beginning `'`) where the spec shows the whole "
                     "list (beginning `[`), so `result` differs. Refuted at an "
                     "input DISTINCT from the first-name-only rival "
                     "(className=\"TimeSeries\", a two-name requirement [x,y], "
                     "present [x,z]) so the two rivals probe their own points.",
        "witness": (
            "-- Refuted at a distinct two-name mismatch. Same first-character\n"
            "-- discriminator ('[' vs '\\'') at the concrete offset; decidable.\n"
            "example : ¬ problem_spec_checkRequiredColumns \"TimeSeries\" true (some [\"x\", \"y\"]) false [\"x\", \"z\"]\n"
            "    (implementation_checkRequiredColumns \"TimeSeries\" true (some [\"x\", \"y\"]) false [\"x\", \"z\"]) := by\n"
            "  unfold problem_spec_checkRequiredColumns implementation_checkRequiredColumns checkRequiredColumns\n"
            "  simp only [Id.run, bind, pure]\n"
            "  norm_num [renderNames, pyListRepr, pyStrRepr, List.take, List.drop, List.headD]\n"
            "  rw [if_neg (by decide : ¬ ((\"z\":String) = \"y\"))]\n"
            "  rw [if_neg (by decide : ¬ ((\"z\":String) = \"y\"))]\n"
            "  intro h\n"
            "  rw [Except.error.injEq] at h\n"
            "  have hd := congrArg (fun t => (t.data)[40]?) h\n"
            "  simp only [String.data_append] at hd\n"
            "  exact absurd hd (by decide)\n"
        ),
    },

    # ---- force the WHOLE-LIST form even for a ONE-name collection ----
    # Added by audit. Both rendering rivals above attack the MULTI-name arm of the
    # adaptive renderer (`| _ => pyListRepr xs`) by making it emit the single-name
    # form. Nothing shipped attacked the OTHER arm (`| [x] => pyStrRepr x`) — the
    # arm every single-column scenario asserts on — so half of the changed clause
    # was unpinned: an impl that dropped the adaptivity and always rendered the
    # bracketed list would have been rejected only by tactic mismatch, with no
    # witness attributing that rejection to the spec. This rival closes that gap
    # from the opposite direction.
    {
        "id": "weak-always-list-form",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the adaptivity: always render the whole bracketed list, so a
        # ONE-name collection is reported as `['time']` instead of `'time'`.
        "module": _swap(
            _BASE, _I_MISMATCH,
            "    else if colnames.take required.length != required then\n"
            "      return .error (className ++ \" object is invalid - expected \" ++\n"
            "        pyListRepr required ++ \" as the first column\" ++ plural ++\n"
            "        \" but found \" ++ pyListRepr (colnames.take required.length))",
        ),
        "refinement": "a faithful real patch that rendered both collections with "
                      "the whole-list form unconditionally — dropping the "
                      "single-element adaptation — would report a one-column "
                      "requirement as a bracketed one-element list rather than the "
                      "one quoted name. The suite asserts the PRESERVED "
                      "single-column wording (one quoted name) verbatim alongside "
                      "the new full-collection wording, so the single-column "
                      "assertions would break: the faithful patch would NOT "
                      "resolve. It is a partial-domain miss that is CORRECT on "
                      "every multi-name requirement and wrong exactly on the "
                      "one-name requirements, i.e. the mirror image of the two "
                      "rivals above.",
        "rationale": "REJECT from the OTHER arm of the adaptive-rendering clause: "
                     "for a one-name collection the spec renders the single quoted "
                     "name (beginning `'`) while the rival renders the bracketed "
                     "list (beginning `[`), so the reported message — hence "
                     "`result` — differs. The discriminating character is the same "
                     "measured offset, taken in the opposite direction, and it "
                     "still precedes any opaque element text, so it stays "
                     "decidable. Binder spread: a ONE-name requirement with a "
                     "mismatching single present column (a point no other witness "
                     "uses).",
        "witness": (
            "-- Refuted at a ONE-name requirement with a mismatching present column.\n"
            "-- Here the SPEC emits the single-quote form and the RIVAL emits the\n"
            "-- bracketed list, so the discriminator runs the other way ('[' where\n"
            "-- the spec has '\\''), again at offset 40 and again before any opaque\n"
            "-- per-element text.\n"
            "example : \u00ac problem_spec_checkRequiredColumns \"TimeSeries\" true (some [\"time\"]) false [\"q\"]\n"
            "    (implementation_checkRequiredColumns \"TimeSeries\" true (some [\"time\"]) false [\"q\"]) := by\n"
            "  unfold problem_spec_checkRequiredColumns implementation_checkRequiredColumns checkRequiredColumns\n"
            "  simp only [Id.run, bind, pure]\n"
            "  norm_num [renderNames, pyListRepr, pyStrRepr, List.take, List.headD]\n"
            "  rw [if_neg (by decide : \u00ac ((\"q\":String) = \"time\"))]\n"
            "  rw [if_neg (by decide : \u00ac ((\"q\":String) = \"time\"))]\n"
            "  intro h\n"
            "  rw [Except.error.injEq] at h\n"
            "  have hd := congrArg (fun t => (t.data)[40]?) h\n"
            "  simp only [String.data_append] at hd\n"
            "  exact absurd hd (by decide)\n"
        ),
    },

    # ---- render the found side WITHOUT truncating it to the required length ----
    # Added by audit (second pass). The changed clause does TWO things: it renders
    # both collections adaptively, AND it takes the found side to the length of the
    # required list rather than naming a single present column. Every rival above
    # attacks the RENDERING half; nothing attacked the TRUNCATION half, so an impl
    # that rendered the whole present column list — correct at the multi-name
    # scenario the new assertion exercises, and correct whenever the table has
    # exactly as many columns as are required — would have been rejected only by
    # tactic mismatch, with no witness attributing that rejection to the spec.
    # Measured over a 39936-input cross-product of the five binders: this impl
    # differs from the modeled behavior on 14400 inputs yet agrees at the
    # multi-name reporting point, so it is a partial-domain miss the existing
    # witnesses provably cannot see (it is not extensionally equal to any rival
    # above). Refuted at a ONE-name requirement with two present columns.
    {
        "id": "weak-found-side-untruncated",
        "kind": "uniqueness",
        "expect": "reject",
        # Render the WHOLE present column list on the found side instead of its
        # leading slice taken to the required length.
        "module": _swap(
            _BASE, _I_MISMATCH,
            "    else if colnames.take required.length != required then\n"
            "      return .error (className ++ \" object is invalid - expected \" ++\n"
            "        renderNames required ++ \" as the first column\" ++ plural ++\n"
            "        \" but found \" ++ renderNames colnames)",
        ),
        "refinement": "a faithful real patch that rendered the ENTIRE present "
                      "column collection on the found side — rather than its "
                      "leading slice taken to the number of required columns — "
                      "would report every column the table currently has, however "
                      "many, in place of just the leading ones the requirement "
                      "speaks about. On a table requiring ONE column but holding "
                      "several it reports a bracketed multi-element list where the "
                      "preserved single-column wording is one quoted name, so the "
                      "single-column assertions the suite keeps asserting verbatim "
                      "break. It is a partial-domain miss that is CORRECT exactly "
                      "when the table has no more columns than are required "
                      "(including the multi-name reporting scenario), and wrong "
                      "whenever it has more, so the faithful patch would NOT "
                      "resolve.",
        "rationale": "REJECT from the TRUNCATION sub-term of the mismatch report "
                     "clause: the spec renders `colnames.take required.length` on "
                     "the found side while the rival renders all of `colnames`, so "
                     "with a one-name requirement and two present columns the spec "
                     "emits the single quoted name (beginning `'`) and the rival "
                     "the bracketed list (beginning `[`), and `result` differs. "
                     "This is the ONLY rival attacking the found-side truncation "
                     "rather than the rendering; the discriminating character sits "
                     "past the (concrete) expected-side render, at the measured "
                     "offset 77, still BEFORE any opaque per-element text, so it "
                     "stays decidable. Binder spread: a ONE-name requirement with "
                     "a present list LONGER than it — a point no other witness "
                     "uses (every other reject witness holds colnames no longer "
                     "than the requirement).",
        "witness": (
            "-- Refuted at a one-name requirement with TWO present columns. The\n"
            "-- found-side render diverges at its first character: the spec's\n"
            "-- single-name form begins '\\'' where the rival's whole-list form\n"
            "-- begins '['. The offset is measured, not assumed: the prefix\n"
            "-- \"TimeSeries object is invalid - expected \" is 40 characters, the\n"
            "-- expected-side render \"'time'\" is 6, \" as the first column\" is 20\n"
            "-- with an empty plural marker, and \" but found \" is 11 — so the\n"
            "-- discriminating character is at index 77, BEFORE any opaque\n"
            "-- per-element text, hence decidable.\n"
            "example : ¬ problem_spec_checkRequiredColumns \"TimeSeries\" true (some [\"time\"]) false [\"q\", \"z\"]\n"
            "    (implementation_checkRequiredColumns \"TimeSeries\" true (some [\"time\"]) false [\"q\", \"z\"]) := by\n"
            "  unfold problem_spec_checkRequiredColumns implementation_checkRequiredColumns checkRequiredColumns\n"
            "  simp only [Id.run, bind, pure]\n"
            "  norm_num [renderNames, pyListRepr, pyStrRepr, List.take, List.headD]\n"
            "  rw [if_neg (by decide : ¬ ((\"q\":String) = \"time\"))]\n"
            "  rw [if_neg (by decide : ¬ ((\"q\":String) = \"time\"))]\n"
            "  intro h\n"
            "  rw [Except.error.injEq] at h\n"
            "  have hd := congrArg (fun t => (t.data)[77]?) h\n"
            "  simp only [String.data_append] at hd\n"
            "  exact absurd hd (by decide)\n"
        ),
    },

    # ---- the INTERIOR of a rendered multi-name collection: the separator ----
    # Added by audit. Every rendering rival above (including the found-side one)
    # is refuted by projecting ONE character at a measured offset that precedes
    # the opaque per-element text. That projection structurally cannot see the
    # INTERIOR of the bracketed list — the separator between rendered elements,
    # and the per-element rendering itself — so the whole-list arm was pinned only
    # at its opening bracket: an impl that emitted the right FORM with the wrong
    # interior was rejected with nothing attributing that rejection to the spec.
    # The port recorded this region as unattackable because the leaf is `opaque`.
    # Measured otherwise: nothing has to PROVE the opaque leaf. This witness
    # states the refutation at a point described by HYPOTHESIS (what the
    # platform's canonical rendering yields for the two names at hand), which
    # makes the remaining message concrete and the disagreement decidable.
    # Satisfiability of those hypotheses is established POSITIVELY (a concrete
    # witnessing function is exhibited and checked; see the docstring) and NOT by
    # the consistency probe's silence: the probe is live for exactly this shape —
    # over two contradictory hypotheses about the SAME leaf it closes (measured,
    # EXIT 0) — so it is an ordinary incomplete check here, not an impossibility
    # result. Verified to discriminate in both builds.
    {
        "id": "weak-list-separator-tight",
        "kind": "uniqueness",
        "expect": "reject",
        # Join the rendered elements of a multi-name collection with "," instead
        # of the platform's ", " — right form, wrong interior.
        "module": _swap(
            _BASE, _I_MISMATCH,
            "    else if colnames.take required.length != required then\n"
            "      let tight : List String → String := fun xs =>\n"
            "        match xs with\n"
            "        | [x] => pyStrRepr x\n"
            "        | _ => \"[\" ++ String.intercalate \",\" (xs.map pyReprStr) ++ \"]\"\n"
            "      return .error (className ++ \" object is invalid - expected \" ++\n"
            "        tight required ++ \" as the first column\" ++ plural ++\n"
            "        \" but found \" ++ tight (colnames.take required.length))",
        ),
        "refinement": "a faithful real patch that rendered a multi-name collection "
                      "by joining the per-element renderings with a bare comma — "
                      "rather than the comma-and-space the platform's own "
                      "collection rendering uses — would emit "
                      "\"['time','a']\" where the suite asserts \"['time', 'a']\". "
                      "The F2P test compares the reported message verbatim, so it "
                      "would NOT resolve. It is correct on every one-name "
                      "requirement and on both no-op clauses, and it even opens "
                      "the collection with the right bracket, so it is a "
                      "partial-domain miss strictly INSIDE the rendered list.",
        "rationale": "REJECT from the whole-list arm of the adaptive-rendering "
                     "clause, at a place no other witness reaches: the spec joins "
                     "the rendered names with \", \" and the rival with \",\", so "
                     "the reported message — hence `result` — differs, while the "
                     "message's opening bracket and every character before it "
                     "AGREE. Binder spread: a two-name requirement whose leading "
                     "name matches and whose second differs, strict regime.",
        "witness": (
            "-- Refuted INSIDE the rendered collection. The two messages agree on\n"
            "-- the whole prefix and on the opening bracket, so the fixed-offset\n"
            "-- projection the other rendering witnesses use cannot see this; the\n"
            "-- divergence is the separator, which sits past the opaque per-element\n"
            "-- text. The opacity is not a barrier: the refutation is stated at a\n"
            "-- point where the platform's canonical per-element rendering is\n"
            "-- described by HYPOTHESIS rather than computed, which leaves the rest\n"
            "-- of the message concrete and the inequation decidable. These\n"
            "-- hypotheses are satisfiable, established by EXHIBITING a witnessing\n"
            "-- function (`∃ f, f \"a\" = \"'a'\" ∧ …`, closed by `decide`) rather\n"
            "-- than by the consistency probe's silence — that probe DOES close\n"
            "-- over contradictory hypotheses about this same leaf, so its silence\n"
            "-- is an incomplete check, not a proof of consistency.\n"
            "example (hra : pyReprStr \"a\" = \"'a'\") (hrb : pyReprStr \"b\" = \"'b'\")\n"
            "    (hrc : pyReprStr \"c\" = \"'c'\") :\n"
            "    ¬ problem_spec_checkRequiredColumns \"TimeSeries\" true (some [\"a\",\"b\"]) false [\"a\",\"c\"]\n"
            "      (implementation_checkRequiredColumns \"TimeSeries\" true (some [\"a\",\"b\"]) false [\"a\",\"c\"]) := by\n"
            "  unfold problem_spec_checkRequiredColumns implementation_checkRequiredColumns checkRequiredColumns\n"
            "  simp only [Id.run, bind, pure]\n"
            "  norm_num [renderNames, pyListRepr, pyStrRepr, List.take, List.headD]\n"
            "  rw [if_neg (by decide : ¬ ((\"c\":String) = \"b\"))]\n"
            "  rw [if_neg (by decide : ¬ ((\"c\":String) = \"b\"))]\n"
            "  rw [hra, hrb, hrc]\n"
            "  intro h\n"
            "  rw [Except.error.injEq] at h\n"
            "  exact absurd h (by decide)\n"
        ),
    },

    # ---- the per-element rendering used inside a multi-name collection ----
    # Added by audit, same lane as the separator rival and the deepest point in
    # the changed clause. The whole-list arm renders each name with the PLATFORM's
    # canonical value rendering; a plausible wrong patch renders each name with
    # the SINGLE-value quoting instead (the same verbatim-apostrophe wrapper the
    # one-name arm legitimately uses). The two agree on every name that needs no
    # escaping, so this is invisible to every other witness in the battery and is
    # refutable only at a name the platform's rendering treats specially. Landed
    # against an opaque leaf by the same hypothesis technique as above.
    {
        "id": "weak-naive-element-quoting",
        "kind": "uniqueness",
        "expect": "reject",
        # Inside the whole-list form, render each name with the single-value
        # verbatim quoting instead of the platform's canonical rendering.
        "module": _swap(
            _BASE, _I_MISMATCH,
            "    else if colnames.take required.length != required then\n"
            "      let naive : List String → String := fun xs =>\n"
            "        match xs with\n"
            "        | [x] => pyStrRepr x\n"
            "        | _ => \"[\" ++ String.intercalate \", \" (xs.map pyStrRepr) ++ \"]\"\n"
            "      return .error (className ++ \" object is invalid - expected \" ++\n"
            "        naive required ++ \" as the first column\" ++ plural ++\n"
            "        \" but found \" ++ naive (colnames.take required.length))",
        ),
        "refinement": "a faithful real patch that built the multi-name form by "
                      "wrapping each name in apostrophes itself — instead of "
                      "deferring to the platform's canonical value rendering, "
                      "which the collection rendering applies per element — would "
                      "agree on ordinary column names and diverge on any name the "
                      "platform renders specially (a name embedding an apostrophe "
                      "switches the surrounding quotes; backslashes and control "
                      "characters are escaped). The reported message would then "
                      "not be the collection rendering the suite compares against, "
                      "so it would NOT resolve. A partial-domain miss on exactly "
                      "the names that need escaping.",
        "rationale": "REJECT from the per-element rendering inside the whole-list "
                     "arm — the deepest sub-term of the changed clause, and the "
                     "one place the battery otherwise left entirely unpinned. The "
                     "spec renders each element with the platform's canonical "
                     "rendering; the rival substitutes the verbatim single-value "
                     "quoting, so on a name that embeds an apostrophe the reported "
                     "message — hence `result` — differs. Binder spread: a "
                     "two-name requirement whose leading name is quote-bearing, a "
                     "point no other witness visits.",
        "witness": (
            "-- Refuted at a QUOTE-BEARING column name, where the platform's\n"
            "-- canonical rendering of a name differs from the verbatim\n"
            "-- apostrophe-wrapping the rival substitutes for it. That rendering is\n"
            "-- the bundle's one opaque leaf, so its value at the two names in play\n"
            "-- is supplied by HYPOTHESIS rather than computed — which is what makes\n"
            "-- the leaf attackable at all. The hypotheses are satisfiable, shown by\n"
            "-- EXHIBITING a witnessing function (`∃ f, f \"a'b\" = \"\\\"a'b\\\"\" ∧\n"
            "-- f \"z\" = \"'z'\"`, closed by `decide`), and the assumed values are\n"
            "-- faithful to the real platform. This is NOT inferred from the\n"
            "-- consistency probe finding nothing: that probe closes over\n"
            "-- contradictory hypotheses about this very leaf, so it is an\n"
            "-- incomplete check. With the leaf pinned the rest of the message is\n"
            "-- concrete and the inequation decidable.\n"
            "example (h1 : pyReprStr \"a'b\" = \"\\\"a'b\\\"\") (h2 : pyReprStr \"z\" = \"'z'\") :\n"
            "    ¬ problem_spec_checkRequiredColumns \"TimeSeries\" true (some [\"a'b\",\"z\"]) false [\"a'b\",\"w\"]\n"
            "      (implementation_checkRequiredColumns \"TimeSeries\" true (some [\"a'b\",\"z\"]) false [\"a'b\",\"w\"]) := by\n"
            "  unfold problem_spec_checkRequiredColumns implementation_checkRequiredColumns checkRequiredColumns\n"
            "  simp only [Id.run, bind, pure]\n"
            "  norm_num [renderNames, pyListRepr, pyStrRepr, List.take, List.headD]\n"
            "  rw [if_neg (by decide : ¬ ((\"w\":String) = \"z\"))]\n"
            "  rw [if_neg (by decide : ¬ ((\"w\":String) = \"z\"))]\n"
            "  rw [h1, h2]\n"
            "  intro h\n"
            "  rw [Except.error.injEq] at h\n"
            "  exact absurd h (by decide)\n"
        ),
    },

    # ---- drop the plural marker (nagini case 5) ----
    {
        "id": "weak-plural-drop",
        "kind": "uniqueness",
        "expect": "reject",
        # Always emit the empty plural marker, never pluralise "column".
        "module": _swap(
            _BASE, _I_PLURAL,
            "\n    let plural := \"\"\n"
            "    if !requiredColumnsRelax && colnames.length == 0 then",
        ),
        "refinement": "a faithful real patch that hard-coded the plural marker to "
                      "empty (dropped the more-than-one-required test) would emit "
                      "\"… as the first column …\" for a multi-column requirement. "
                      "The F2P test asserts the pluralised \"… as the first "
                      "columns …\", so the message mismatches and the faithful "
                      "patch would NOT resolve; the single-column scenarios still "
                      "pass, so it is a partial-domain miss on exactly the "
                      "multi-column path.",
        "rationale": "REJECT from the plural sub-term of the report clause: with a "
                     "two-name requirement the spec pins the marker to \"s\" and "
                     "the rival emits \"\", so `result` differs. Refuted in the "
                     "NO-columns branch (empty present columns) — fully concrete, "
                     "decidable — which pins the plural marker independently of "
                     "the opaque list rendering, and moves the colnames binder to "
                     "the empty list.",
        "witness": (
            "example : ¬ problem_spec_checkRequiredColumns \"TimeSeries\" true (some [\"time\", \"a\"]) false []\n"
            "    (implementation_checkRequiredColumns \"TimeSeries\" true (some [\"time\", \"a\"]) false []) := by\n"
            "  unfold problem_spec_checkRequiredColumns implementation_checkRequiredColumns checkRequiredColumns\n"
            "  simp only [Id.run, bind, pure]\n"
            "  norm_num\n"
            "  decide\n"
        ),
    },

    # ---- the check-disabled no-op clause (unchanged but load-bearing) ----
    {
        "id": "weak-disabled-wrong-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # When checking is switched off, return the WRONG relax flag (`true`)
        # instead of the unchanged input flag.
        "module": _swap(
            _BASE, _I_DISABLED,
            "  if !requiredColumnsEnabled then\n"
            "    return .ok true\n"
            "  match requiredColumns with",
        ),
        "refinement": "a faithful real patch that flipped the relaxed-regime flag "
                      "to true when checking is disabled would silently relax a "
                      "table the caller had left strict, corrupting the state the "
                      "subsequent P2P re-checks rely on; the disabled path is "
                      "meant to be a pure no-op. It would NOT resolve.",
        "rationale": "REJECT from the check-disabled no-op clause: the spec "
                     "returns the relax flag UNCHANGED and the rival returns "
                     "`true`, so at a strict (relax=false) disabled input "
                     "`result` differs. Fully concrete, decidable. Moves the "
                     "enabled binder to false — the only rival that does.",
        "witness": (
            "example : ¬ problem_spec_checkRequiredColumns \"TimeSeries\" false (some [\"time\"]) false [\"time\"]\n"
            "    (implementation_checkRequiredColumns \"TimeSeries\" false (some [\"time\"]) false [\"time\"]) := by\n"
            "  unfold problem_spec_checkRequiredColumns implementation_checkRequiredColumns checkRequiredColumns\n"
            "  simp only [Id.run, bind, pure]\n"
            "  norm_num\n"
        ),
    },

    # ---- the no-configured-names no-op clause (unchanged but load-bearing) ----
    {
        "id": "weak-none-wrong-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # When no columns are configured, return the WRONG relax flag.
        "module": _swap(_BASE, _I_NONE, "  | none => return .ok true"),
        "refinement": "a faithful real patch that flipped the relaxed-regime flag "
                      "to true when no required columns are configured would "
                      "relax a table that has no requirement to satisfy, "
                      "corrupting state the P2P suite depends on; that path must "
                      "be a pure no-op. It would NOT resolve.",
        "rationale": "REJECT from the no-configured-names no-op clause: the spec "
                     "returns the relax flag UNCHANGED and the rival returns "
                     "`true`, so at a strict input with no configured columns "
                     "`result` differs. Fully concrete, decidable. The only rival "
                     "probing requiredColumns=none.",
        "witness": (
            "example : ¬ problem_spec_checkRequiredColumns \"TimeSeries\" true none false [\"time\"]\n"
            "    (implementation_checkRequiredColumns \"TimeSeries\" true none false [\"time\"]) := by\n"
            "  unfold problem_spec_checkRequiredColumns implementation_checkRequiredColumns checkRequiredColumns\n"
            "  simp only [Id.run, bind, pure]\n"
            "  norm_num\n"
        ),
    },

    # ---- the relaxed-regime toggle clause ----
    {
        "id": "weak-toggle-never-clears",
        "kind": "uniqueness",
        "expect": "reject",
        # Never clear the relaxed regime: keep the input flag even once the
        # leading columns have matched the full requirement.
        "module": _swap(
            _BASE, _I_TOGGLE,
            "    let newRelax := requiredColumnsRelax\n"
            "    return .ok newRelax",
        ),
        "refinement": "a faithful real patch that never cleared the relaxed "
                      "regime once the table acquired its required leading "
                      "columns would leave the table permanently relaxed, so a "
                      "later genuine violation would be silently accepted; the "
                      "P2P behavior that a satisfied table returns to strict "
                      "checking breaks. It would NOT resolve.",
        "rationale": "REJECT from the toggle clause: with the regime relaxed and "
                     "the present leading columns equal to the full requirement "
                     "the spec clears the flag to `false`, while the rival keeps "
                     "`true`, so `result` differs. Fully concrete, decidable. "
                     "Moves relax to true at the toggle point (requirement met).",
        "witness": (
            "example : ¬ problem_spec_checkRequiredColumns \"TimeSeries\" true (some [\"time\"]) true [\"time\"]\n"
            "    (implementation_checkRequiredColumns \"TimeSeries\" true (some [\"time\"]) true [\"time\"]) := by\n"
            "  unfold problem_spec_checkRequiredColumns implementation_checkRequiredColumns checkRequiredColumns\n"
            "  simp only [Id.run, bind, pure]\n"
            "  norm_num\n"
        ),
    },

    # ---- the relaxed truncation of the required list ----
    {
        "id": "weak-ignore-relax-truncation",
        "kind": "uniqueness",
        "expect": "reject",
        # Ignore the relaxed regime when computing `required`: always use the
        # full configured list instead of truncating it to the number present.
        "module": _swap(
            _BASE, _I_REQUIRED,
            "    let required := reqCols\n"
            "    let plural := if required.length > 1 then \"s\" else \"\"",
        ),
        "refinement": "a faithful real patch that ignored the relaxed regime and "
                      "compared against the full configured list (rather than its "
                      "truncation to the number of present columns) would report a "
                      "mismatch — and raise — for a relaxed table that is still "
                      "being assembled and legitimately has fewer columns so far. "
                      "The relaxed regime exists precisely to permit that, so the "
                      "faithful patch would NOT resolve.",
        "rationale": "REJECT from the relaxed-truncation clause: with the regime "
                     "relaxed, a two-name requirement, and one present column, the "
                     "spec truncates `required` to length one (leading column "
                     "matches → no error, `.ok`) while the rival keeps the "
                     "two-name list (mismatch → `.error`), so the outcome "
                     "constructor itself differs. Refuted on the `.ok`/`.error` "
                     "split; moves relax to true with a length-mismatched present "
                     "slice.",
        "witness": (
            "example : ¬ problem_spec_checkRequiredColumns \"TimeSeries\" true (some [\"time\", \"a\"]) true [\"time\"]\n"
            "    (implementation_checkRequiredColumns \"TimeSeries\" true (some [\"time\", \"a\"]) true [\"time\"]) := by\n"
            "  unfold problem_spec_checkRequiredColumns implementation_checkRequiredColumns checkRequiredColumns\n"
            "  simp only [Id.run, bind, pure]\n"
            "  norm_num\n"
            "  exact fun h => Except.noConfusion h\n"
        ),
    },

    # ---- the class-name prefix of the reported message ----
    {
        "id": "weak-hardcoded-classname",
        "kind": "uniqueness",
        "expect": "reject",
        # Hardcode the class-name prefix of the report instead of echoing the
        # actual class name. Refuted in the (concrete) no-columns branch.
        "module": _swap(
            _BASE, _I_NOCOLS,
            "    if !requiredColumnsRelax && colnames.length == 0 then\n"
            "      return .error (\"TimeSeries\" ++ \" object is invalid - expected '\" ++ required.headD \"\" ++\n"
            "        \"' as the first column\" ++ plural ++ \" but time series has no columns\")",
        ),
        "refinement": "a faithful real patch that hard-coded the class name in "
                      "the message (rather than reading the actual class) would "
                      "mislabel the reported object for every subclass; the "
                      "message the tests assert is prefixed with the ACTUAL class "
                      "name, so on any other class the message mismatches and the "
                      "faithful patch would NOT resolve.",
        "rationale": "REJECT from the class-name prefix of the report clause: the "
                     "spec prefixes the message with the `className` input and the "
                     "rival hard-codes \"TimeSeries\", so on a different class the "
                     "message — hence `result` — differs. Fully concrete, "
                     "decidable. The ONLY rival moving the className binder "
                     "(\"QTable\"), so that input is demonstrated live rather than "
                     "held fixed by every witness.",
        "witness": (
            "example : ¬ problem_spec_checkRequiredColumns \"QTable\" true (some [\"x\"]) false []\n"
            "    (implementation_checkRequiredColumns \"QTable\" true (some [\"x\"]) false []) := by\n"
            "  unfold problem_spec_checkRequiredColumns implementation_checkRequiredColumns checkRequiredColumns\n"
            "  simp only [Id.run, bind, pure]\n"
            "  norm_num\n"
            "  decide\n"
        ),
    },

    # ---- the found slot ECHOES the required collection (nagini
    # ---- echo-demanded-into-found) ----
    # Added by the fifth-pass audit. Ports a nagini case the port had dropped.
    # Every rival above attacks HOW a collection is rendered, or WHICH slice is
    # rendered; none pins that the two slots hold DIFFERENT collections. An impl
    # that rendered the required collection into BOTH slots would emit a message
    # of exactly the right shape, with the right brackets, separator, per-element
    # rendering and plural marker — and would still be rejected, with nothing in
    # the battery attributing that rejection to the spec. This case makes the
    # found side an INDEPENDENT observable rather than a restatement of the
    # expected side.
    {
        "id": "weak-echo-found-side",
        "kind": "uniqueness",
        "expect": "reject",
        # Render the REQUIRED collection into the found slot as well, so the
        # message reports the requirement twice and never the present columns.
        "module": _swap(
            _BASE, _I_MISMATCH,
            "    else if colnames.take required.length != required then\n"
            "      return .error (className ++ \" object is invalid - expected \" ++\n"
            "        renderNames required ++ \" as the first column\" ++ plural ++\n"
            "        \" but found \" ++ renderNames required)",
        ),
        "refinement": "a faithful real patch that filled the found slot from the "
                      "required collection — rather than from the columns actually "
                      "present — would report the requirement twice, telling the "
                      "user the table holds exactly what it was faulted for not "
                      "holding. Since the branch is only reached when the two "
                      "collections DIFFER, the found half of every reported message "
                      "would be wrong on the whole branch, and the message the "
                      "suite compares verbatim names the present columns, so the "
                      "faithful patch would NOT resolve. It is correct on both "
                      "no-op clauses, on the no-columns report and on the toggle, "
                      "so it is a partial-domain miss confined to the found slot of "
                      "the changed clause.",
        "rationale": "REJECT from the found SLOT of the mismatch report clause, an "
                     "observable no other rival pins: the spec renders "
                     "`colnames.take required.length` there and the rival renders "
                     "`required`, so at a one-name requirement whose single present "
                     "column differs the spec reports the present name and the "
                     "rival repeats the required one, and `result` differs. This is "
                     "orthogonal to the rendering rivals (the FORM is untouched — "
                     "same brackets, separator, per-element rendering, plural) and "
                     "to `weak-found-side-untruncated` (which renders the present "
                     "columns, merely unsliced); measured to differ from the "
                     "modeled behavior on 93830 of 195936 inputs with a behavior "
                     "distinct from every other rival's. Fully concrete at the "
                     "one-name point, hence decidable without touching the opaque "
                     "leaf. Binder spread: a fresh one-name requirement and a "
                     "fresh one-name present list, a tuple no other witness uses.",
        "witness": (
            "-- Refuted at a one-name requirement with ONE differing present\n"
            "-- column. Both sides take the single-name arm of the renderer, so the\n"
            "-- messages agree on form and diverge only in the found NAME: the spec\n"
            "-- reports the present column, the rival repeats the required one.\n"
            "-- Both names are concrete and neither routes through the opaque\n"
            "-- per-element rendering (that leaf is only reached by the whole-list\n"
            "-- arm), so the inequation is decidable outright.\n"
            "example : ¬ problem_spec_checkRequiredColumns \"TimeSeries\" true (some [\"u\"]) false [\"v\"]\n"
            "    (implementation_checkRequiredColumns \"TimeSeries\" true (some [\"u\"]) false [\"v\"]) := by\n"
            "  unfold problem_spec_checkRequiredColumns implementation_checkRequiredColumns checkRequiredColumns\n"
            "  simp only [Id.run, bind, pure]\n"
            "  norm_num [renderNames, pyListRepr, pyStrRepr, List.take, List.headD]\n"
            "  rw [if_neg (by decide : ¬ ((\"v\":String) = \"u\"))]\n"
            "  rw [if_neg (by decide : ¬ ((\"v\":String) = \"u\"))]\n"
            "  intro h\n"
            "  rw [Except.error.injEq] at h\n"
            "  exact absurd h (by decide)\n"
        ),
    },

    # ---- the plural marker's TOKEN, not its rule (nagini
    # ---- boundary-plural-token-swap) ----
    # Added by the fifth-pass audit. Ports a nagini case the port had dropped.
    # `weak-plural-drop` attacks the pluralisation RULE (never pluralise). It
    # cannot see a rival that keeps the rule exactly right — pluralise iff more
    # than one column is required — while emitting the WRONG marker. The word the
    # suite compares is spelled out in the asserted message, so the token itself
    # is part of the defended surface and needs its own rival.
    {
        "id": "weak-plural-token-swap",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep the pluralisation RULE byte-for-byte; move only the marker's code
        # point from "s" to "t".
        "module": _swap(
            _BASE, _I_PLURAL,
            "\n    let plural := if required.length > 1 then \"t\" else \"\"\n"
            "    if !requiredColumnsRelax && colnames.length == 0 then",
        ),
        "refinement": "a faithful real patch that pluralised on exactly the right "
                      "condition but appended the wrong letter would emit "
                      "\"as the first columnt\" where the suite asserts "
                      "\"as the first columns\". The reported message is compared "
                      "verbatim, so it would NOT resolve, even though the decision "
                      "of WHETHER to pluralise is entirely correct on every input. "
                      "It is correct on every one-name requirement (where the "
                      "marker is empty) and on both no-op clauses — a partial-domain "
                      "miss confined to the marker's spelling.",
        "rationale": "REJECT from the plural marker's TOKEN, which no other rival "
                     "pins: `weak-plural-drop` moves the RULE (it emits the empty "
                     "marker unconditionally) and therefore agrees with this rival "
                     "wherever the requirement holds one name, while this rival "
                     "keeps the rule and changes the emitted character. Measured to "
                     "differ from the modeled behavior on 90450 of 195936 inputs, "
                     "with a behavior distinct from `weak-plural-drop`'s and from "
                     "every other rival's. Refuted in the no-columns branch, which "
                     "is fully concrete, so plain evaluation decides it. Binder "
                     "spread: a two-name requirement with an EMPTY present list "
                     "under the strict regime, and the \"QTable\" class name.",
        "witness": (
            "-- Refuted in the no-present-columns branch at a TWO-name requirement,\n"
            "-- where the spec pluralises and the rival emits its wrong marker. That\n"
            "-- branch renders only the required head verbatim and never enters the\n"
            "-- whole-list arm, so no opaque per-element rendering is involved and\n"
            "-- the whole message is concrete: `decide` settles the inequation.\n"
            "example : ¬ problem_spec_checkRequiredColumns \"QTable\" true (some [\"time\", \"a\"]) false []\n"
            "    (implementation_checkRequiredColumns \"QTable\" true (some [\"time\", \"a\"]) false []) := by\n"
            "  unfold problem_spec_checkRequiredColumns implementation_checkRequiredColumns checkRequiredColumns\n"
            "  simp only [Id.run, bind, pure]\n"
            "  norm_num\n"
            "  decide\n"
        ),
    },

    # ---- the collection's DELIMITERS (nagini boundary-bracket-token-swap) ----
    # Added by the fifth-pass audit. Ports a nagini case the port had dropped.
    # The rendering witnesses project ONE character at the collection's opening
    # position, so they pin THAT the whole-list form opens with a bracket rather
    # than a quote. They do not pin WHICH bracket sits at each end. A rival that
    # transposes the two delimiters keeps every name, order, separator and
    # per-element rendering byte-identical and still opens with a bracket-class
    # character, so it is invisible to the separator and quoting rivals too.
    {
        "id": "weak-bracket-token-swap",
        "kind": "uniqueness",
        "expect": "reject",
        # Transpose the collection's two delimiters; everything inside is
        # byte-identical to the spec's rendering.
        "module": _swap(
            _BASE, _I_MISMATCH,
            "    else if colnames.take required.length != required then\n"
            "      let swapped : List String → String := fun xs =>\n"
            "        match xs with\n"
            "        | [x] => pyStrRepr x\n"
            "        | _ => \"]\" ++ String.intercalate \", \" (xs.map pyReprStr) ++ \"[\"\n"
            "      return .error (className ++ \" object is invalid - expected \" ++\n"
            "        swapped required ++ \" as the first column\" ++ plural ++\n"
            "        \" but found \" ++ swapped (colnames.take required.length))",
        ),
        "refinement": "a faithful real patch that assembled the multi-name form "
                      "with its two delimiters transposed would emit "
                      "\"]'time', 'a'[\" where the suite asserts "
                      "\"['time', 'a']\". The collection rendering the message is "
                      "compared against is the platform's own, so the reported "
                      "message would not match and the patch would NOT resolve — "
                      "even though every name, their order, the separator and each "
                      "per-element rendering are exactly right. Correct on every "
                      "one-name requirement and on both no-op clauses: a "
                      "partial-domain miss at the collection's two ends.",
        "rationale": "REJECT from the DELIMITERS of the whole-list arm. The other "
                     "rendering witnesses project one character at the collection's "
                     "opening offset and so pin only that the multi-name form opens "
                     "with a bracket rather than a quote — not which of the two "
                     "brackets it is; the interior rivals (separator, per-element "
                     "quoting) leave both ends untouched. Measured to differ from "
                     "the modeled behavior on 90150 of 195936 inputs with a "
                     "behavior distinct from every other rival's. The divergence is "
                     "at the collection's first character, BEFORE any opaque "
                     "per-element text, so it is decidable by the same measured "
                     "offset-40 projection. Binder spread: a two-name requirement "
                     "whose leading name matches and whose second differs, at names "
                     "no other witness uses.",
        "witness": (
            "-- Refuted at a two-name requirement whose second name differs. The\n"
            "-- messages agree on the whole 40-character prefix and then diverge at\n"
            "-- the collection's opening delimiter: the spec emits '[' where the\n"
            "-- rival emits ']'. That character precedes all opaque per-element\n"
            "-- text, so the projection is decidable. The offset is measured, not\n"
            "-- assumed: \"TimeSeries object is invalid - expected \" is exactly 40\n"
            "-- characters for this 10-character class name.\n"
            "example : ¬ problem_spec_checkRequiredColumns \"TimeSeries\" true (some [\"b\",\"c\"]) false [\"b\",\"d\"]\n"
            "    (implementation_checkRequiredColumns \"TimeSeries\" true (some [\"b\",\"c\"]) false [\"b\",\"d\"]) := by\n"
            "  unfold problem_spec_checkRequiredColumns implementation_checkRequiredColumns checkRequiredColumns\n"
            "  simp only [Id.run, bind, pure]\n"
            "  norm_num [renderNames, pyListRepr, pyStrRepr, List.take, List.headD]\n"
            "  rw [if_neg (by decide : ¬ ((\"d\":String) = \"c\"))]\n"
            "  rw [if_neg (by decide : ¬ ((\"d\":String) = \"c\"))]\n"
            "  intro h\n"
            "  rw [Except.error.injEq] at h\n"
            "  have hd := congrArg (fun t => (t.data)[40]?) h\n"
            "  simp only [String.data_append] at hd\n"
            "  exact absurd hd (by decide)\n"
        ),
    },

    # ---- adaptivity keyed to the WRONG length (nagini
    # ---- partial-domain-len2-guard) ----
    # Added by the fifth-pass audit. Ports a nagini case the port had dropped.
    # The adaptive renderer switches to the single-quoted form at exactly ONE
    # required name. `weak-always-list-form` attacks the switch by removing it
    # (always bracket); `weak-first-name-only` attacks it by always taking the
    # single-name arm. Neither pins the THRESHOLD: a rival that keeps both arms
    # and takes the single-name arm at the wrong ARITY renders correctly on
    # one-name and three-or-more-name collections and diverges only at exactly
    # two, which is the boundary the fix's own scenarios sit closest to.
    {
        "id": "weak-adaptive-threshold-at-two",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep BOTH arms of the adaptive renderer; take the single-quoted arm at
        # a collection of exactly TWO names instead of exactly one.
        "module": _swap(
            _BASE, _I_MISMATCH,
            "    else if colnames.take required.length != required then\n"
            "      let g : List String → String := fun xs =>\n"
            "        if xs.length == 2 then pyStrRepr (xs.headD \"\") else renderNames xs\n"
            "      return .error (className ++ \" object is invalid - expected \" ++\n"
            "        g required ++ \" as the first column\" ++ plural ++\n"
            "        \" but found \" ++ g (colnames.take required.length))",
        ),
        "refinement": "a faithful real patch that keyed the adaptive rendering to "
                      "the wrong arity — collapsing a TWO-name collection to its "
                      "first name in quotes, while correctly bracketing collections "
                      "of three or more and correctly quoting a lone name — would "
                      "emit \"'time'\" where the suite asserts "
                      "\"['time', 'a']\" for a two-column requirement. The "
                      "two-column requirement is the smallest case the fix was "
                      "written for and the one the added scenarios assert, so it "
                      "would NOT resolve, even though the renderer is right "
                      "everywhere else in the domain.",
        "rationale": "REJECT from the THRESHOLD of the adaptive renderer, which no "
                     "other rival pins: `weak-always-list-form` deletes the "
                     "single-name arm and `weak-first-name-only` deletes the "
                     "whole-list arm, so both differ from the spec on collections "
                     "of every arity, while this rival agrees with the spec at arity "
                     "1 and at every arity ≥3 and diverges at exactly 2. Measured "
                     "to differ from the modeled behavior on 26900 of 195936 "
                     "inputs, and — checked over a domain reaching requirement "
                     "length 3 — to differ from `weak-first-name-only` on 69500 of "
                     "them, with a behavior distinct from every other rival's. (On "
                     "a domain capped at requirement length 2 the two coincide, "
                     "which is a measurement artifact and not a fact about the "
                     "rival.) Refuted at the collection's first character, before "
                     "any opaque text. Binder spread: a two-name requirement under "
                     "the strict regime with a differing second present column. "
                     "The refutation ARITY is forced to 2 (that is the only arity "
                     "where this rival diverges at all), so it necessarily shares "
                     "an arity with `weak-first-name-only`; the NAMES are chosen "
                     "fresh so the argument tuple stays distinct from every other "
                     "witness's.",
        "witness": (
            "-- Refuted at a requirement of exactly TWO names, the one arity where\n"
            "-- this rival's threshold bites: the spec takes the whole-list arm and\n"
            "-- opens with '[', the rival takes the single-quoted arm and opens with\n"
            "-- '\\''. That character sits at the measured offset 40 (the prefix\n"
            "-- \"TimeSeries object is invalid - expected \" is 40 characters for a\n"
            "-- 10-character class name), BEFORE any opaque per-element text, so the\n"
            "-- projection is decidable.\n"
            "example : ¬ problem_spec_checkRequiredColumns \"TimeSeries\" true (some [\"u\",\"v\"]) false [\"u\",\"w\"]\n"
            "    (implementation_checkRequiredColumns \"TimeSeries\" true (some [\"u\",\"v\"]) false [\"u\",\"w\"]) := by\n"
            "  unfold problem_spec_checkRequiredColumns implementation_checkRequiredColumns checkRequiredColumns\n"
            "  simp only [Id.run, bind, pure]\n"
            "  norm_num [renderNames, pyListRepr, pyStrRepr, List.take, List.headD]\n"
            "  rw [if_neg (by decide : ¬ ((\"w\":String) = \"v\"))]\n"
            "  rw [if_neg (by decide : ¬ ((\"w\":String) = \"v\"))]\n"
            "  intro h\n"
            "  rw [Except.error.injEq] at h\n"
            "  have hd := congrArg (fun t => (t.data)[40]?) h\n"
            "  simp only [String.data_append] at hd\n"
            "  exact absurd hd (by decide)\n"
        ),
    },

    # ---- the mismatch guard's CONDITION, not its report ----
    # Added by the seventh-pass audit, which found that every rival above
    # attacks what a report branch EMITS while reaching that branch by the
    # frozen guard, so no case attributed a rejection to either guard's own
    # CONDITION. This rival emits both reports exactly as the spec does and
    # differs only in WHEN the mismatch branch is entered, so it diverges at
    # the `.ok`/`.error` CONSTRUCTOR rather than inside a message — a coarser
    # observable than any other reject case here reaches.
    {
        "id": "weak-mismatch-guard-whole-list",
        "kind": "uniqueness",
        "expect": "reject",
        # The guard compares the WHOLE present list against the requirement
        # instead of its leading slice; the report itself is untouched.
        "module": _swap(
            _BASE, _I_MISMATCH,
            "    else if colnames != required then\n"
            "      return .error (className ++ \" object is invalid - expected \" ++\n"
            "        renderNames required ++ \" as the first column\" ++ plural ++\n"
            "        \" but found \" ++ renderNames (colnames.take required.length))",
        ),
        "refinement": "a faithful real patch that rewrote the leading-slice "
                      "comparison as an equality against the whole present "
                      "collection would render every message exactly as the "
                      "suite asserts, and would still accept a collection that "
                      "is exactly the requirement, but would report a table "
                      "holding its required columns FOLLOWED BY OTHERS as "
                      "invalid — which is the ordinary case for a table with "
                      "any additional column. It would not resolve, and the "
                      "failure it produced would be an unexpected report on an "
                      "input the suite expects to pass rather than a wrong "
                      "string on an input it expects to fail.",
        "rationale": "REJECT from the mismatch guard's CONDITION, which no other "
                     "rival pins: every rival above reaches this branch through "
                     "the frozen guard and changes what it emits, so a rival "
                     "that emits both reports correctly and enters the branch on "
                     "the wrong condition was previously rejected with nothing "
                     "in the battery attributing that rejection to the spec. "
                     "Measured over a 58480-input cross-product of the five "
                     "binders to differ from the modeled behavior on 912 inputs, "
                     "with all 912 differing at the `Except` CONSTRUCTOR "
                     "(`.error` where the spec answers `.ok`), and with a "
                     "behavior distinct from all sixteen rivals above and from "
                     "the modeled behavior. Because the divergence is at the "
                     "constructor, the refutation needs no string projection and "
                     "no assumption about the opaque per-element rendering at "
                     "all: `Except.noConfusion` closes it. Binder spread: the "
                     "relaxed regime with a one-name requirement and a present "
                     "collection that CONTAINS it and is longer — a "
                     "longer-than-required collection at a one-name "
                     "requirement, an argument tuple no other witness uses.",
        "witness": (
            "-- Refuted where the present collection begins with the whole\n"
            "-- requirement and continues past it: the spec compares only the\n"
            "-- leading slice and answers `.ok`, this rival compares the whole\n"
            "-- collection and answers `.error`. The divergence is at the\n"
            "-- CONSTRUCTOR, so the refutation is `Except.noConfusion` and never\n"
            "-- touches the opaque per-element rendering.\n"
            "example : ¬ problem_spec_checkRequiredColumns \"TimeSeries\" true (some [\"time\"]) true [\"time\", \"a\"]\n"
            "    (implementation_checkRequiredColumns \"TimeSeries\" true (some [\"time\"]) true [\"time\", \"a\"]) := by\n"
            "  unfold problem_spec_checkRequiredColumns implementation_checkRequiredColumns checkRequiredColumns\n"
            "  simp only [Id.run, bind, pure]\n"
            "  norm_num\n"
            "  exact fun h => Except.noConfusion h\n"
        ),
    },

    # ---- the no-columns guard's CONDITION, not its report ----
    # Added by the seventh-pass audit alongside the case above, for the same
    # reason: the report's CONTENT is attacked from four directions
    # (`weak-hardcoded-classname`, `weak-plural-drop`, `weak-plural-token-swap`
    # and the head/noun probes explored during the audit) while the guard that
    # decides whether that report is emitted at all was unpinned.
    {
        "id": "weak-nocols-guard-ignores-relax",
        "kind": "uniqueness",
        "expect": "reject",
        # The guard drops its relaxed-regime conjunct; the report is untouched.
        "module": _swap(
            _BASE, _I_NOCOLS,
            "    if colnames.length == 0 then\n"
            "      return .error (className ++ \" object is invalid - expected '\" ++ required.headD \"\" ++\n"
            "        \"' as the first column\" ++ plural ++ \" but time series has no columns\")",
        ),
        "refinement": "a faithful real patch that tested only for an empty "
                      "collection, dropping the regime conjunct that confines "
                      "that report to the strict regime, would emit the "
                      "no-columns report verbatim as the suite asserts it in "
                      "the strict regime, and would be right on every "
                      "non-empty collection under either regime — but it would "
                      "report a relaxed table that legitimately has no columns "
                      "yet, which is exactly the state the relaxed regime "
                      "exists to permit. It would not resolve.",
        "rationale": "REJECT from the no-columns guard's CONDITION. This is the "
                     "only rival whose refutation point is a RELAXED collection "
                     "with no columns, and the only one besides "
                     "`weak-mismatch-guard-whole-list` that turns an accepting "
                     "answer into a report rather than altering a report's text. "
                     "Measured over the same 58480-input cross-product to differ "
                     "from the modeled behavior on 170 inputs, all 170 at the "
                     "`Except` CONSTRUCTOR, with a behavior distinct from every "
                     "other case's. It is NOT subsumed by "
                     "`weak-ignore-relax-truncation`: that rival keeps this "
                     "guard intact and changes the truncation feeding the "
                     "report, so it agrees with the spec on every empty "
                     "collection under the relaxed regime, which is the whole "
                     "of this rival's divergence. Refuted by "
                     "`Except.noConfusion`, with no dependence on the opaque "
                     "per-element rendering. Binder spread: the relaxed regime "
                     "with a one-name requirement and an EMPTY present "
                     "collection — the empty-collection point under the relaxed "
                     "regime, which no other witness visits.",
        "witness": (
            "-- Refuted at a RELAXED table with no columns: the spec's guard is\n"
            "-- confined to the strict regime and answers `.ok`, this rival drops\n"
            "-- that conjunct and answers `.error`. Constructor-level, so the\n"
            "-- refutation is `Except.noConfusion` and assumes nothing about the\n"
            "-- opaque per-element rendering.\n"
            "example : ¬ problem_spec_checkRequiredColumns \"TimeSeries\" true (some [\"time\"]) true []\n"
            "    (implementation_checkRequiredColumns \"TimeSeries\" true (some [\"time\"]) true []) := by\n"
            "  unfold problem_spec_checkRequiredColumns implementation_checkRequiredColumns checkRequiredColumns\n"
            "  simp only [Id.run, bind, pure]\n"
            "  norm_num\n"
            "  exact fun h => Except.noConfusion h\n"
        ),
    },
]

# No AXIOM lane here: the bundle consumes no `axiom` (one `opaque` leaf, the
# unchanged platform per-element quoting, is an A-reference validated by G-AX,
# not a consumed contract). The nagini AXIOM_TESTS were also empty; dropped.
AXIOM_TESTS = []
