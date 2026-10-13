"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-14710 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. This is
a PORT of the nagini sibling's battery to the lean carrier, re-expressing its
adversarial reasoning — not its text — against this bundle's model. Each SPEC
case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, where a case legitimately re-proves, inside the
``-- proof-start`` / ``-- proof-end`` region — is changed, so
``markers.same_spec`` holds and the ``theorem correct_scoreEarlyStop`` STATEMENT
stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

DEFENDED SURFACE (one total function over its input domain):

  scoreEarlyStop
      (scorer : Scorer) (shouldStop : List Score → Bool)
      (isClf useVal : Bool) (labels : Option (Array String))
      (xTrain : XData) (yTrain : Array Int)
      (xVal : Option XData) (yVal : Option (Array Int))
      (trScores vlScores : List Score) : Except EarlyStopError CheckResult

  where ``Scorer := XData → Targets → Except EarlyStopError Score``

  models the gold patch's two guarded re-encodings in the early-stopping scoring
  step. The behavioral delta the patch introduces: before handing a target array
  to the (opaque) scoring function, a CATEGORICAL estimator's integer-coded
  targets are mapped back through the class-label table to the original labels
  (``targetFor true (some ls) codes = (relabelTargets ls codes).map Sum.inr``); a
  non-categorical estimator forwards the raw codes (``Sum.inl codes``). This is
  applied INDEPENDENTLY on the training path and, when validation data is in use,
  on the validation path. The decode sits inside an ``Except`` because it is
  PARTIAL — see the fourth bullet below.

  BOTH OF THE PROCEDURE'S CONDITIONAL ARGUMENTS ARE OPTIONAL, and READING an
  absent one is an observable failure rather than a silent no-op:

    * the CLASS-LABEL TABLE exists only for a categorical estimator; reading it
      otherwise is ``Except.error EarlyStopError.absentClassLabels``. In the
      repository ``self.classes_`` is assigned only in
      ``HistGradientBoostingClassifier._encode_y`` (``gradient_boosting.py:1029``),
      so a regressor has no such attribute — and a regressor DOES reach this
      method, on every iteration, whenever ``scoring != 'loss'``
      (``gradient_boosting.py:254`` and ``:358``). Reading the table off the
      guarded branch therefore raises ``AttributeError:
      'HistGradientBoostingRegressor' object has no attribute 'classes_'``.
    * the VALIDATION ARGUMENTS (design matrix and target codes) are created only
      for an estimator that holds out a split; reading one otherwise is
      ``Except.error EarlyStopError.absentValidationData``.
      ``gradient_boosting.py`` sets ``X_val, y_val = None, None`` whenever
      ``validation_fraction is None`` and ``X_binned_val = None`` with it, so
      ``self.classes_[y_val.astype(int)]`` on that path raises
      ``AttributeError: 'NoneType' object has no attribute 'astype'``.
      The two are read in a FIXED ORDER, and the order is observable: the gold
      patch inserts ``y_val = self.classes_[y_val.astype(int)]`` immediately
      inside ``if self._use_validation_data:``, textually and dynamically BEFORE
      the ``self.scorer_(self, X_binned_val, y_val)`` call that is the method's
      only use of ``X_binned_val``. So the target codes are read, and decoded,
      first, and the design matrix is touched only after that. Where the two would
      report different failures the TARGET side answers first — measured on the
      gold-patched method with ``self.classes_`` a one-entry table:
      ``X_binned_val=None, y_val=[1]`` raises ``IndexError: index 1 is out of
      bounds for axis 0 with size 1`` (the DECODE's failure, not the absent design
      matrix's), while ``y_val=[0]`` decodes and reaches
      ``scorer_(self, None, y)``, and ``y_val=None`` raises the
      ``AttributeError`` on ``.astype`` before ``X_binned_val`` is looked at.

  AND TWO MORE OPERATIONS ARE PARTIAL, for the same kind of reason:

    * ``self.scorer_(self, X, y)`` compares ``y`` against predictions it derives
      from ``X`` (``_BaseScorer.__call__`` → ``_PredictScorer._score`` →
      ``metric(y_true, y_pred)`` → ``check_consistent_length``), so a design
      matrix and a target array that do not describe the same samples are a
      ``ValueError: Found input variables with inconsistent numbers of samples``,
      not a score. Modeled as ``Except.error EarlyStopError.scoringRefused``. This
      is what makes each scoring call's ARGUMENTS observable and not merely its
      recorded value; the bind site is the call site, so a term that is never
      bound is a call Python has not yet made.
    * THE DECODE ITSELF. ``self.classes_[codes.astype(int)]`` is an indexed
      gather, so it is defined on the codes the table has an entry for and on no
      others: numpy resolves a negative code from the END of the table
      (``size + c``) and RAISES ``IndexError: index N is out of bounds for axis 0
      with size M`` for a code landing outside ``[-size, size)`` on either side.
      Modeled as ``relabelTargets : Array String → Array Int →
      Except EarlyStopError (Array String)``, whose
      ``Except.error EarlyStopError.codeOutOfRange`` falls exactly where numpy
      raises: ``codeIndex`` resolves one code (wrapping a negative one rather than
      clamping it) and ``codesIndexLabels`` is the resulting domain. The
      correspondence is machine-checked against numpy in both directions and on
      both sides of zero by this bundle's ``axiom_check.py``. This partiality is
      what makes the DECODE's arguments observable and not merely the branch it
      took: a rival that decodes a stand-in pair assembled off the guard is
      answerable for what the gather says about that stand-in, exactly as a rival
      that scores a stand-in pair is answerable for the scorer's answer.

  All four were TOTAL in an earlier interface, and each was a measured,
  machine-checked hole in the contract — see the four lanes below. The decode's
  totality was the LAST of the four to be closed, and it was closed because it was
  exploited: a rival that hoisted the training decode above the ``isClf`` guard and
  fed it an ``Option.getD`` stand-in table verified against the total decode while
  its patch raised ``IndexError`` in the official image (G-EQ
  ``BROKEN (verify⇏correct)``; see ``weak-getd-train-decode-hoisted`` below, which
  is that rival).

  The load-bearing postcondition clauses. Since the decode is partial, the target
  array is itself an ``Except`` and the training answer is the decode BOUND to the
  scoring call; abbreviate the two of them as

    trTgt = targetFor isClf labels yTrain           -- Except EarlyStopError Targets
    trAns = trTgt.bind (fun t => scorer xTrain t)   -- Except EarlyStopError Score
    vlAns yv xv = (targetFor isClf labels yv).bind (fun t => scorer xv t)

  so that each clause is an equation over the scorer's ANSWER about the pair it
  names AND over the decode that produced that pair. (The spec text spells the
  categorical arms out in the equivalent unnested form
  ``(relabelTargets ls yTrain).bind (fun yT => (scorer xTrain (Sum.inr yT)).…)``,
  which is this ``trAns`` after one monad-law step. The step is a rewrite, not a
  definitional unfolding, when the decode is stuck on a symbolic table — which is
  exactly why several positives below must supply it as a ``have``; see PROOF
  REGION.)
    (C_lbl) isClf = true, labels = none →
              result = .error EarlyStopError.absentClassLabels
    (C_no)  labels present-if-needed, useVal = false →
              result = trAns.map (fun trScore =>
                          ⟨trScores ++ [trScore], vlScores,
                           shouldStop (trScores ++ [trScore])⟩)
    (C_val) labels present-if-needed, useVal = true,
            xVal = some xv, yVal = some yv →
              result = trAns.bind (fun trScore =>
                          (vlAns yv xv).map
                            (fun vlScore =>
                              ⟨trScores ++ [trScore], vlScores ++ [vlScore],
                               shouldStop (vlScores ++ [vlScore])⟩))
    (C_err) labels present-if-needed, useVal = true and a validation argument
            absent → the result is an error reached only after ``trAns``, and
            WHICH error it is follows the order in which the two validation
            arguments are taken — the target codes first, then (for a categorical
            estimator) their decode, and only then the design matrix:
              isClf = false →
                result = trAns.bind (fun _ =>
                           .error EarlyStopError.absentValidationData)
              isClf = true, labels = some ls →
                result = trAns.bind (fun _ =>
                           (readValCodes yVal).bind (fun codes =>
                             (relabelTargets ls codes).bind (fun _ =>
                               .error EarlyStopError.absentValidationData)))
            so absent codes are ``absentValidationData``; codes the class-label
            table has no entry for are the decode's own ``codeOutOfRange``,
            whatever the design matrix holds; and only codes that DO decode leave
            the absent design matrix to report ``absentValidationData``. On the
            non-categorical path there is no decode between the two reads, both
            absences report the same error, and the order is unobservable — which
            is why that arm is the short one.

  and the corollary the newest lane attacks, which is not a separate arm but a
  consequence of the three equations above (the training decode is the OUTERMOST
  bind in each):
    (C_dec) isClf = true, labels = some ls, relabelTargets ls yTrain = .error e →
              result = .error e, whatever the scorer would have answered about
              anything — so a rival that reports a success here, or that reports a
              ``codeOutOfRange`` the named pair does not produce, is refuted.

  (C_lbl) precedes the others because decoding the TRAINING targets is the first
  thing the procedure does, so an absent table is reported whatever the validation
  arguments hold; (C_dec) has that same standing one step further in, for the same
  reason. (C_err) is likewise an equation over ``trAns`` rather than a bare
  error, because the training pair is scored BEFORE the absence is discovered —
  which is what keeps the training call's arguments observable even on a path that
  ends in an error. Its categorical arm goes one step further and names the
  validation READ and the validation DECODE inside that error path, because the
  method performs both before it touches the design matrix; see IN WHICH ORDER
  THE VALIDATION ARGUMENTS ARE READ below, which is the audit that put them
  there. Every clause but (C_lbl) is an EQUATION on the whole result, so
  each of the three components, the ok/error disposition, and the ARGUMENTS of
  every scoring call are pinned at every input; the spec is a 7-arm match on
  ``isClf, labels, useVal, xVal, yVal`` and every arm is an equation, so the
  contract is TOTAL over its input domain — and it is quantified over EVERY
  partial scorer, of which the total ones are a special case, so the obligation is
  over strictly more inputs than the total-``scorer`` version it replaces.

  The DISCRIMINATOR of the patch is the argument passed to ``scorer``:
  ``targetFor`` chooses ``(relabelTargets ls …).map Sum.inr`` vs ``.ok (Sum.inl …)``
  by ``isClf``. Forwarding the raw codes on the classifier path is exactly the
  pre-patch behavior that makes the F2P scenario raise (integer y_true vs
  original-label y_pred). This is the behavior the F2P test
  ``test_string_target_early_stopping`` exercises.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION-MUTATION (nagini: MANDATORY) — the PERMISSION half is
    vacuous here (Lean is referentially transparent: every input is a plain
    immutable value, so there is no half-permission to violate and no aliasing
    to exploit), but the FRAME OBLIGATION the half-permission encodes is fully
    expressible and is attacked. Per spec_guide §0.5 the frame obligation
    translates on this carrier to "the spec pins the UNCHANGED output
    components"; here that is (C_no)'s ``valScores = vlScores``. A rival that
    extends the validation history when validation data is NOT in use changes a
    component the contract requires to be carried through unchanged — the
    value-level analogue of the input-overwrite, and the same "an unconstrained
    output component is the full-permission hole" argument. Ported as
    ``weak-val-frame-extended``.

  * PARTIAL-DOMAIN / PREPATCH (nagini ``prepatch-undecoded-index``) — APPLIES,
    and is the load-bearing rival. The classifier path forwards the raw codes
    (``Sum.inl``) instead of the decoded labels — the literal pre-patch — so
    (C_no)/(C_val) are violated whenever the scorer distinguishes the two
    arguments. Ported as ``weak-prepatch-undecoded``.

  * PASSTHROUGH-CLAUSE attack (nagini ``passthrough-regressor-decode``) —
    APPLIES. The rival decodes on the NON-classifier path too, violating the
    ``isClf = false`` selection of ``targetFor`` (raw codes). Ported as
    ``weak-regressor-decode``.

  * PARTIAL-DOMAIN / one-site-only (nagini ``partial-domain-first-undecoded``,
    which leaves ONE element undecoded) — ported TWICE, because the nagini case
    carries two independent arguments and the carrier expresses both:
      - as a ONE-PATH miss: the training path is decoded correctly but the
        VALIDATION path forwards raw codes. This attacks (C_val) and pins that
        the two scoring sites are re-encoded INDEPENDENTLY. Ported as
        ``weak-val-undecoded``.
      - as the literal ELEMENT-LEVEL sub-domain miss: every code is relabeled
        EXCEPT position 0, which keeps its raw code. This is the nagini argument
        verbatim ("correct on the whole domain except the first element") and it
        is what pins ``relabelTargets`` as an ELEMENT-WISE gather rather than
        merely "the ``Sum.inr`` branch was taken". The three whole-array rivals
        swap the ``Sum`` constructor wholesale, so without this case a rival that
        entered the right branch with a per-element defect was unattacked.
        Ported as ``weak-first-element-raw``.

  * GROUNDED-ORACLE positive control (nagini ``pos-grounded-oracle-decode-one``)
    + LOCAL-VARIABLE reshape (nagini ``pos-localvar-reshape``) — ported as the
    soundness positives: a helper-delegating reshape (``targetFor`` computed
    once into a ``let``), an inline ``if-then-else`` reshape, a ``match``-on-Bool
    reshape, and a record-direct reshape that abandons the mutable accumulators.
    All are structurally different but behaviorally identical CORRECT impls that
    must verify; else the spec is over-fit to the frozen impl's spelling =>
    SPEC-TOO-STRONG. THREE further positives belong to the lanes below, each
    paired with the rival it must be distinguished from:
    ``pos-option-map-precompute`` and ``pos-labels-map-precompute`` precompute
    under ``Option.map`` what their paired rivals precompute unguarded, so each
    pair pins its clause to READING an absent argument rather than to
    precomputation — note that both precompute the DECODE, not merely the
    ``Sum`` injection, so they are gathers on the table that exists;
    ``pos-unbound-consult`` NAMES a scoring application on an ``Option.getD``
    stand-in above the guard but binds it only inside, so its pair pins the
    clause to the BIND rather than to the mention. The last one is measured
    rather than argued: its faithful patch passes, in the official instance
    image, the three PASS_TO_PASS tests its paired rival's patch fails
    (``3 passed, 75 deselected, 1 warning in 399.63s``).

    A FOURTH such positive, ``pos-getd-decode-precompute``, used to sit here: it
    precomputed the ``Option.getD`` stand-in DECODE above the guard, on the
    argument that it read nothing absent and called the scorer on nothing. That
    argument was sound only while the decode was TOTAL. Against the partial
    decode it is false — performing a gather on a stand-in table is itself an
    observable act, and ``relabelTargets #[] #[12] = .error codeOutOfRange``
    where the pair the contract names answers ``.ok`` — and the construct's
    faithful patch does NOT pass the suite: the G-EQ role measured it at
    ``59 success / 4 FAILURE`` against gold's ``63/63`` (the four
    ``test_early_stopping_regression`` parametrizations, raising ``IndexError:
    index 12 is out of bounds for axis 0 with size 0``), which is why the total
    decode was recorded ``BROKEN (verify⇏correct)``. The case is therefore
    CONVERTED, not deleted: it ships as the two reject entries
    ``weak-getd-train-decode-hoisted`` (the train-site hoist, the G-EQ round's
    ``atk_6``) and ``weak-getd-val-decode-hoisted`` (the val-site hoist,
    ``atk_7``). Its old ``3 passed, 75 deselected`` oracle record is no
    contradiction: the 75 deselected tests include the four parametrizations the
    construct fails, so it was never certified where it breaks.

  * ADMISSIBILITY (nagini ``admiss-primary-selfcall``) — PRESENT, as
    ``admiss-ground-f2p``. On a TOTAL carrier the analogue of PRECOND-TOO-STRONG
    is the obligation being UNSATISFIABLE at exactly an F2P-shaped input — which
    a positive that discharges the obligation AT THAT CONCRETE INPUT, by
    evaluation, as a ``have``, before closing the frozen obligation verbatim,
    tests directly. The ported case does exactly that at the smallest F2P-shaped
    point: a categorical estimator with validation data in use and SUPPLIED, a
    two-entry class-label table, and both target arrays given as concrete codes,
    so ``relabelTargets`` is EVALUATED (``relabelTargets #["x","y"] #[0,1] =
    .ok #["x","y"]`` and ``relabelTargets #["x","y"] #[1,0] = .ok #["y","x"]``,
    both by ``rfl`` — ``decide`` is no longer available on the partial decode,
    since ``Except EarlyStopError (Array String)`` carries no ``DecidableEq``
    instance) and then REWRITTEN INTO the goal, rather than left symbolic.
    Evaluating to ``.ok`` of a named array, rather than merely to some value, is
    also what rules out the vacuous reading in which both sides are the same
    ``.error``. That rewrite is what makes the case
    load-bearing rather than decorative: it was measured to FAIL when grafted
    onto the ``weak-prepatch-undecoded`` and ``weak-first-element-raw`` rivals,
    so it pins the admission to the decoded branch the F2P scenario actually
    exercises rather than merely restating the obligation.

  * DIVERGENCE / NON-TERMINATION — a KNOWN HOLE in the frozen spec, NOT a vacuous
    class. The frozen solution sets no termination semantics option, and the
    variant scope check admits a ``partial def`` in the impl region, so an impl
    may introduce an unbounded recursion. Measured: an impl that adds
    ``partial def spin (n : Nat) : Nat := spin (n + 1)`` and evaluates it into a
    discarded binding, while computing the result exactly as gold, VERIFIES
    (build exit 0, scope check clean) — the discarded binding is erased before
    the obligation is reduced, so the frozen proof closes unchanged. No witness
    can refute it: its returned value is gold's at every input, so any claim true
    of it is true of gold and would be recorded ``witness-vacuous``. Nothing is
    therefore shippable in the reject lane, and no case is offered. (The
    neighbouring shape, where the diverging helper's result IS consumed, is a
    value-level rival rather than a divergence one — it is rejected, exit 1,
    because the recorded result is then not gold's — and adding it would test the
    clauses the existing rivals already pin, not termination.)

  * AXIOM lane (nagini ``AXIOM_TESTS``) — DROPPED. The axiom lane is G-AX's job;
    this gate ignores it. AXIOM_TESTS is empty.

  * STOP-DECISION clause — has NO nagini ancestor (the nagini surface returns
    only the re-encoded target list; the history/stop threading is modeled only
    here), so it is an ADDITION rather than a port. The spec's stop decision
    selects WHICH extended history the stopping rule is applied to, by
    ``useVal``; a rival that always consults the training history satisfies both
    history clauses and every ``targetFor`` selection while getting the decision
    wrong on the validation path (``weak-stop-uses-train``), and one that
    consults the training history as it stood ON ENTRY gets the no-validation
    decision wrong by one iteration (``weak-stop-no-val-unextended``).

WHERE THE VALIDATION ARGUMENTS ARE READ — the lane this battery previously had
no case for, and the reason the contract's interface changed.

  The earlier contract typed the validation inputs TOTAL (``xVal : XData``,
  ``yVal : Array Int``) and constrained the validation score only under
  ``useVal = true``, while binding it in an UNCONDITIONAL ``let``. Because
  ``scorer`` and ``relabelTargets`` are total pure functions, WHEN the validation
  targets are decoded was then unobservable: an impl could HOIST the decode (and
  the scorer call) above the ``if useVal`` guard and stay provably equal to the
  spec, since on the no-validation branch the hoisted value is simply dead.

  In the repository it is not dead, it is a crash. ``gradient_boosting.py`` sets
  ``X_val, y_val = None, None`` when ``validation_fraction is None`` (and
  ``X_binned_val = None`` with it), so the hoisted
  ``self.classes_[y_val.astype(int)]`` runs on ``None``. Measured in the official
  instance image on 2026-08-16: the hoisted patch (the gold patch with the
  val-site decode lifted out of ``if self._use_validation_data:``) FAILS two
  PASS_TO_PASS tests that the gold patch PASSES —
  ``test_early_stopping_classification[accuracy-None-5-0.1-data0]`` and
  ``[…-data1]``, whose parameters are ``('accuracy', None, 5, 1e-1)``, a
  classifier with ``validation_fraction=None`` — with
  ``AttributeError: 'NoneType' object has no attribute 'astype'``. So a verifying
  impl was NOT correct: verify ⇏ correct.

  Strengthening the old clauses could not close it: hoisting a PURE computation
  is semantics-preserving, so no relation over a single total ``result`` can
  forbid it. The absence of the validation data had to enter the model. It now
  does, in two parts: the validation inputs are ``Option``, and READING an absent
  one is observable (``Except.error``). (``Option`` alone would not have been
  enough — an impl could hoist ``relabelTargets labels (yVal.getD #[])``, whose
  value is again dead on the no-validation branch. The error propagation is the
  part that does the work, and it is also the faithful model of what Python does:
  ``None.astype`` raises.) The two rivals in this lane are the machine-checked
  attacks that broke the old contract, re-encoded against the new one:
  ``weak-val-read-hoisted`` (hoists the read + decode) and
  ``weak-val-score-hoisted`` (hoists the scorer call with them).

  The complementary SPEC-TOO-STRONG probe matters just as much, because the new
  clause must forbid READING an absent argument and nothing more: an impl that
  precomputes the decoded validation targets UNDER ``Option.map`` — never
  touching an absent argument — is correct (its Python counterpart is a
  defensive ``y_val if y_val is not None else None``) and must still verify.
  Shipped as ``pos-option-map-precompute``.

IN WHICH ORDER THE VALIDATION ARGUMENTS ARE READ — the same lane's second half,
and a SPEC-TOO-STRONG defect the live G-PANEL audit found in it (agent_verdict
UNFAITHFUL against the contract that shipped ``| true, some ls, true, _, _ =>
… .bind (fun _ => .error absentValidationData)``).

  Making both reads observable settled WHETHER an absent argument may be touched.
  It left the ORDER of the two reads unstated, and the previous ``(C_err)`` arm
  quietly chose one: the design matrix first. That is the order the frozen impl
  had (``let xv ← readValData xVal`` above ``let codes ← readValCodes yVal``), so
  the contract and the impl agreed and every case in this battery passed — but it
  is NOT the method's order, and it is observable, because the two sides can
  report different failures.

  In the repository the gold patch puts the decode of the validation targets
  immediately inside ``if self._use_validation_data:``, above the only use of
  ``X_binned_val`` in the method. So with ``validation_fraction`` set but
  ``X_binned_val`` absent and a code the label table has no entry for, Python
  raises the gather's ``IndexError`` — never reaching the design matrix — where the
  old arm demanded ``absentValidationData``. The auditor rebuilt exactly that impl
  in Lean (codes read and decoded, then ``readValData xVal``) and PROVED the
  shipped spec refutes it: 13 disagreeing points over a 21600-point grid, every one
  of shape ``isClf=true, useVal=true, xVal=none, yVal=some <out-of-range code>``,
  real ``codeOutOfRange`` against modeled ``absentValidationData``. A faithful impl
  the contract refutes is SPEC-TOO-STRONG, and on this carrier it is the same
  defect class as an over-strong precondition: the contract was demanding a
  behavior the patched method does not have.

  Closed by stating the order the method has, in the arm that can see it: the
  categorical ``(C_err)`` arm now binds ``readValCodes yVal`` and then
  ``relabelTargets ls codes`` before it reports ``absentValidationData``, so the
  three sub-cases come out as Python does them — absent codes report the read,
  undecodable codes report the gather, and decodable codes reach the absent design
  matrix. Nothing else moved: the ``(C_val)`` arm (both arguments supplied) and
  every ``isClf = false`` arm are byte-identical, because with both arguments
  present the order is unobservable and with no decode between the two reads both
  absences report the same error. The frozen impl swaps its two validation reads to
  match, and the frozen tactic body still closes it unchanged.

  The rival for this half is ``weak-val-order-swapped``: gold with the two
  validation reads in the OLD order, which is the shape the audited contract
  demanded. Its witness is unconditional and lands on the newly constrained arm —
  it is the only reject case that does — so a regression to the design-matrix-first
  order is caught here rather than by the next audit. The too-strong side needs no
  new case: all seven soundness positives read the codes and decode them before the
  design matrix, so the faithful order is what the required-to-verify half of this
  battery is now built on.

WHERE THE CLASS-LABEL TABLE IS READ — the same defect on the other conditional
argument, closed the same way, and NOT a decoration: it is a second point at which
a verifying impl was incorrect.

  The earlier contract typed ``labels : Array String`` TOTAL. Reading the table is
  again a pure projection, so an impl could HOIST it above ``if isClf`` — keeping
  both decodes inside the guard, hence recording exactly gold's scores at every
  input — and be provably equal to the spec. On the non-categorical branch the
  hoisted table is simply dead.

  In the repository it is not dead. ``self.classes_`` is assigned only in
  ``HistGradientBoostingClassifier._encode_y`` (``gradient_boosting.py:1029``);
  ``HistGradientBoostingRegressor._encode_y`` returns the targets as float64 and
  defines no such attribute. And the regressor reaches
  ``_check_early_stopping_scorer``: ``fit`` dispatches
  ``if self.scoring == 'loss': … else: self._check_early_stopping_scorer(…)`` at
  ``gradient_boosting.py:232-255`` (first iteration) and ``:339-360`` (each later
  iteration), with no classifier guard. So the hoisted read raises
  ``AttributeError: 'HistGradientBoostingRegressor' object has no attribute
  'classes_'`` on the four scorer-driven ``test_early_stopping_regression``
  PASS_TO_PASS parametrizations — ``[neg_mean_squared_error-0.1-5-1e-07]``,
  ``[neg_mean_squared_error-None-5-0.1]``, ``[None-0.1-5-1e-07]``,
  ``[None-None-5-0.1]`` (the two ``[loss-…]`` ones take the
  ``_check_early_stopping_loss`` path and ``[None-None-None-None]`` does not early
  stop at all). Measured in the official instance image; see refinement.md,
  ``Reading an absent class-label table``. So here too a verifying impl was NOT
  correct: verify ⇏ correct.

  Closed identically: ``labels : Option (Array String)``, with ``readLabels`` /
  ``targetFor`` reporting ``absentClassLabels``. The rival is
  ``weak-labels-hoisted``; its SPEC-TOO-STRONG partner is
  ``pos-labels-map-precompute``, which performs the SAME precomputation under
  ``Option.map`` — never touching an absent table — and must still verify, so the
  clause forbids reading an absent table and not precomputing from a present one.

WHICH PAIR THE SCORING FUNCTION IS CONSULTED ABOUT — the third lane, and the one
that survived making both conditional arguments ``Option`` with observable reads.

  An impl does not have to READ an absent argument to consult the scorer about the
  wrong pair: it can build a stand-in out of ``Option.getD`` defaults. Measured on
  2026-08-16 by the live G-EQ reviewer against the Option-plus-error contract:
  ``atk_8.lean`` keeps BOTH guarded validation reads, computes
  ``hoistedTargets := if isClf then Sum.inr (relabelTargets (labels.getD #[]) (yVal.getD #[])) else Sum.inl (yVal.getD #[])``
  and ``hoistedScore := scorer (xVal.getD xTrain) hoistedTargets`` ABOVE the
  ``useVal`` guard, and inside the guard — where the defaults coincide with the
  real arguments — records the answer it already holds. It had ``same_spec=True``,
  ``verifies=True`` and axioms ``[propext]``. Every value it records is gold's at
  every input and it reads nothing absent, so no clause about reads or about
  recorded scores can see it: with a TOTAL ``scorer`` the hoisted call is a dead
  pure value on the no-validation path.

  In the repository it is not dead, it is a ``ValueError``. Its faithful patch
  hoists
  ``_hoisted_score = self.scorer_(self, X_binned_val if X_binned_val is not None else X_binned_small_train, _hoisted_targets)``
  above ``if self._use_validation_data:``. Measured in the official instance image
  (digest ``sha256:e68930db25c0…``) on 2026-08-16: **3 failed, 75 deselected,
  1 warning in 1.91s** —
  ``test_early_stopping_regression[neg_mean_squared_error-None-5-0.1]``,
  ``test_early_stopping_classification[accuracy-None-5-0.1-data0]`` and
  ``[…-data1]``, each with ``ValueError: Found input variables with inconsistent
  numbers of samples: [0, 50]`` (``[0, 30]`` for the two classification cases)
  from ``sklearn/utils/validation.py:206``, because the stand-in target array is
  EMPTY while the training design matrix it is paired with has 50 (resp. 30) rows.
  The gold control PASSES all three in the same image and session (``3 passed …
  248.03s``), and all three are PASS_TO_PASS, so that patch cannot resolve: a third
  verifying impl was NOT correct.

  Strengthening a clause about the recorded scores could not close it — the rival
  records exactly gold's scores. What had to enter the model is the scorer's own
  PARTIALITY: ``Scorer := XData → Targets → Except EarlyStopError Score``, with
  each call bound by ``←``, so every branch names its outcome as an
  ``Except.bind``/``Except.map`` over the answer about the pair THAT BRANCH NAMES
  and an impl that consults the scorer about any other pair is answerable for the
  answer it draws. The rival is ``weak-val-scorecall-hoisted``. (It ships RETYPED
  for the partial decode — the stand-in target array is now an ``Except``, so the
  hoisted consult binds through it — while the ``atk_8`` text quoted above is the
  original, typed for the total decode of that round. Its witness point is
  unchanged at ``isClf = false``, where no decode is taken at all, so the case is
  still attributable to the refused CALL rather than to a ``codeOutOfRange`` from
  the stand-in table.)

  The complementary SPEC-TOO-STRONG probe for this lane was, for one round, the
  fourteen-attack round's ``atk_6.lean``: the same ``getD`` stand-in precomputed,
  with both scoring calls left INSIDE the guard, shipped as required-to-verify
  (``pos-getd-decode-precompute``) on the strength of a three-test resolve
  measurement. The next G-EQ round refuted that blessing — it is the FOURTH LANE
  below, and the reason this battery no longer has such a positive. The probe's job
  in this lane is done instead by ``pos-unbound-consult``, which names the same
  stand-in pair above the guard without consulting the scorer about it and is
  measured correct on the resolve side, so the lane keeps its too-strong side while
  nothing in it permits performing the call.

  That bind-site argument is the one claim in this lane an adversary can attack
  directly, and one did. A live G-EQ reviewer, running against the contract as
  shipped, authored fourteen attacks; thirteen were rejected — including
  ``atk_13``, which is ``weak-val-scorecall-hoisted``'s shape reached
  independently, and ``atk_14``, which consults the scorer an extra time about
  the raw validation pair INSIDE the branch and discards the answer. The
  fourteenth, ``atk_12``, VERIFIES: it names ``scorer (xVal.getD xTrain)
  standInTargets`` above the guard in a ``let`` of type
  ``Except EarlyStopError Score`` and ``←``-binds it only inside. Its author then
  settled it with the oracle rather than with an argument, and settled it against
  itself: the faithful patch it shipped defers the call in a lambda invoked only
  under ``if self._use_validation_data:``, and that patch PASSES the three
  PASS_TO_PASS parametrizations (``3 passed, 75 deselected, 1 warning in
  399.63s``, official instance image). So ``atk_12`` is a correct echo and the
  contract is right to admit it; it is shipped here as ``pos-unbound-consult``,
  which is what puts the lane's boundary — bind, not mention — under a case of
  its own. An eager Python call in that position is not a refinement at all:
  under ``useVal = false`` this impl returns ``.ok``, and a raising call does not
  refine a normal return.

WHICH PAIR THE DECODE IS PERFORMED ON — the fourth lane, added by the most recent
repair, and the one the corpus recorded as an actual ``verify ⇏ correct`` break
rather than argued for in advance.

  The contract already made the scoring CALL's arguments observable, and both
  conditional READS. It did not make the DECODE's arguments observable: with
  ``relabelTargets : Array String → Array Int → Array String`` TOTAL, gathering from
  a stand-in table was as invisible as reading one had been before the ``Option``s
  arrived. Measured by the live G-EQ role against the shipped
  Option-plus-partial-scorer contract, and recorded in this bundle's verdict.md:

    * ``atk_6.lean`` — spec byte-for-byte, the TRAINING decode hoisted above the
      ``isClf`` guard and taken from a DEFAULTED table
      (``relabelTargets (labels.getD #[]) yTrain``), consumed only inside the
      guard, with the guarded ``readLabels`` left in place: ``rc=0 VERIFIES``,
      axioms ``[propext]``;
    * ``atk_7.lean`` — the same defect at the validation site, with BOTH
      conditional arguments defaulted
      (``relabelTargets (labels.getD #[]) (yVal.getD yTrain)`` hoisted above the
      ``useVal`` guard): ``rc=0 VERIFIES``, axioms ``[propext]``.

  In the repository neither is dead. The hoisted
  ``getattr(self, 'classes_', np.array([]))[y.astype(int)]`` is a fancy-index gather
  on an EMPTY table, and numpy answers it with ``IndexError: index 12 is out of
  bounds for axis 0 with size 0``. Measured in the official instance image:
  ``atk_6`` is ``resolved=False, completed=True, F2P 1/1, P2P 59 success /
  4 FAILURE, 253.1s`` and ``atk_7`` the identical four failures in ``70.3s``, both
  'consistent - not flaky', against a gold control of ``resolved=True, F2P 1/1,
  P2P 63/63, 231.7s``. The four are the scorer-driven
  ``test_early_stopping_regression`` parametrizations — the estimator that has no
  ``classes_`` at all — and both attacks still PASS the F2P, so the break is a P2P
  regression rather than a lost fix. G-EQ recorded the spec
  ``BROKEN (verify⇏correct)``.

  Why the three earlier lanes could not see it: nothing absent is READ (``getD``
  supplies a default), every recorded value is gold's (the hoisted decode is
  consumed only inside the guard, where the default coincides with the real table),
  and the scorer is consulted about nothing but the named pairs. What was left
  unmodeled is that the GATHER itself can fail.

  Closed by giving the decode exactly numpy's domain:
  ``relabelTargets : Array String → Array Int → Except EarlyStopError (Array
  String)``, with ``codeIndex`` resolving one code — a negative one from the END of
  the table (``size + c``), which is what numpy does, NOT clamped to zero — and
  ``codesIndexLabels`` deciding the resulting domain; outside it the result is
  ``.error codeOutOfRange``, which is numpy's raise. The correspondence is
  machine-checked against numpy in both directions and on both sides of zero by
  ``axiom_check.py``. Against that decode the defaulted (empty) table paired with
  real codes is a gather with no entry to return, off-guard, where the contract
  demands a success — so both attacks are refuted, and they ship as
  ``weak-getd-train-decode-hoisted`` (= ``atk_6``) and
  ``weak-getd-val-decode-hoisted`` (= ``atk_7``) with one unconditional shared
  witness.

  Not too strong, and this is the boundary the retired positive was defending
  badly: the clause forbids PERFORMING a gather on a table the caller did not
  supply, not precomputing a decode. ``pos-labels-map-precompute`` and
  ``pos-option-map-precompute`` precompute the DECODE itself under ``Option.map`` —
  the gather then runs on the table that exists, and its own ``codeOutOfRange``
  stays the impl's outcome wherever the contract says it is — and both must verify;
  ``pos-unbound-consult`` names a defaulted stand-in decode above the guard without
  performing it, and must verify. A decode an impl never binds is a gather numpy has
  not yet attempted, exactly as an unbound ``scorer x t`` is a call not yet made.

PROOF REGION. The repair did not cost gold its proof: the FROZEN tactic body
``cases isClf <;> cases labels <;> cases useVal <;> cases xVal <;> cases yVal <;>
rfl`` still closes ``correct_scoreEarlyStop`` for the frozen impl (measured,
``Solution.lean`` exit 0), because that impl binds the decode exactly where the
contract binds it and both sides reduce to the same ``Except.bind`` chain.
``admiss-ground-f2p`` and ``pos-labels-map-precompute`` also close with that body
verbatim — the admissibility case only PREPENDS its ground ``have``.

The other SIX positives cannot, and re-prove instead. That is admissible: G-PBT allows edits
inside the ``-- proof-start`` / ``-- proof-end`` region, the theorem STATEMENT stays
byte-identical, and no declaration, axiom or assumption token is added. What they
need is one MONAD-LAW step. The contract binds the decode and then injects
(``(relabelTargets ls yTrain).bind (fun yT => … (Sum.inr yT) …)``), while a reshape
that goes through ``targetFor`` — or spells it out — binds the injected decode
(``(relabelTargets ls yTrain).map Sum.inr``). Over a symbolic table the decode is
STUCK, so ``(x.map Sum.inr) >>= k`` and ``x >>= fun d => k (Sum.inr d)`` are equal
but not DEFINITIONALLY equal, and ``rfl`` cannot cross the gap; it closed
everything before the repair because a total decode left nothing stuck. Each such
case supplies the step in its own proof region as

    have hmap : ∀ {β : Type} (x : Except EarlyStopError (Array String))
        (k : Targets → Except EarlyStopError β),
        (Except.map (Sum.inr : Array String → Targets) x) >>= k
          = x >>= fun d => k (Sum.inr d) := by
      intro β x k; cases x <;> rfl

(plus ``htf``, which is ``targetFor true (some ls) cs`` unfolded by ``rfl``) and
finishes with ``simp only`` over those two and whatever ITS OWN spelling leaves in
the way — ``if_true`` for a ``let`` the elaborator guards with a literal ``True``,
``Option.map`` / ``readLabels`` / ``Except.bind`` for a precomputation performed
through one of those. ``pos-unbound-consult`` needs the same step across TWO binds
at once, because it names a stand-in ANSWER (``decode >>= scorer >>= …``) rather
than a stand-in target array; since the contract's order requires the stand-in
decode to be BOUND before the design-matrix read, that case binds it once on its
own and once inside the named answer, and adds the step that says binding the same
partial gather twice is binding it once (``hdup``, likewise ``cases x <;> rfl``). The sets differ per case rather than being unified:
each is the smallest one measured to close all 32 goals the five-fold ``cases``
leaves.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an impl (the frozen script is tuned to the frozen form), so a rejection
alone attributes nothing to the spec. Every ``expect="reject"`` case therefore
carries a Lean snippet stating the spec predicate at a described input; each was
built (against the rival) and rebuilt (against the frozen solution) to confirm it
HOLDS of its rival and FAILS on gold. Each witness first RESTATES the spec
predicate at that input as the explicit equation it definitionally is — a
``have h1 : <Except equation> := hspec``, which typechecks against the rival and
does NOT typecheck against gold — then projects the disagreeing component.

Every witness but one INSTANTIATES the scoring function as the total lift
``fun x t => .ok (scorer x t)`` of an opaque ``scorer : XData → Targets → Score``.
A total scorer is a legitimate member of ``Scorer`` — it is what the repository's
own well-formed call sites see — and the lift makes each clause's
``Except.map``/``Except.bind`` reduce to the plain ``Except.ok ⟨…⟩`` equation the
witness restates, so the refutations below are about the recorded values and the
error disposition, NOT about the scorer refusing anything. That keeps them
independent of the new partiality: they would still refute their rivals under the
previous total-``scorer`` interface. The single exception is
``weak-val-scorecall-hoisted``, whose whole point is the partiality: it
instantiates a scorer that refuses exactly one pair — the empty-target stand-in
the rival assembles — and answers every other pair with ``.ok (scorer x t)``.

Every witness that reaches a categorical path states its refutation at a LITERAL
class-label table (``#["x", "y"]``) and LITERAL codes (``#[0, 1]`` on the training
path, ``#[1, 0]`` on the validation path) rather than at a symbolic
``labels``/``yTrain``. The decode's PARTIALITY forces that, and it is what makes
these witnesses decide anything: the contract binds the training decode FIRST
(``(relabelTargets ls yTrain).bind …``), so over a symbolic table the clause is
stuck behind a decode that might be ``.error`` and the plain ``Except.ok ⟨…⟩``
equation a witness restates is not what the spec reduces to. At the literal table
the decode EVALUATES (``#[0,1] ↦ .ok #["x","y"]``, ``#[1,0] ↦ .ok #["y","x"]``),
the ``bind`` discharges, and the equation is again exactly the recorded triple. A
literal input is also strictly stronger evidence — the refutation names one input
rather than a family — and ``#["x","y"]`` with codes ``#[0,1]`` is the shape of
the F2P fixture (50 ``'x'`` + 50 ``'y'``). The two witnesses whose rivals never
decode (the scoring-call and class-label hoists, both refuted at
``isClf = false``) keep symbolic inputs.

Because the scorer/Score/XData carriers are OPAQUE (no literal input computes the
score), MOST witnesses CONDITION ON THE CARRIER: they assume only a single
disequality separating the two calls the rival confuses (e.g. ``scorer xTrain
(Sum.inl #[0, 1]) ≠ scorer xTrain (Sum.inr #["x", "y"])``) and show the rival's
returned result contradicts the spec's under that one assumption. One hypothesis
per witness, jointly satisfiable by construction: a single disequality on an opaque
function, which no other assumption constrains, so the gate's consistency probe
cannot derive ``False`` from it.

EIGHT witnesses need NO hypothesis at all:
  * ``weak-val-frame-extended`` violates a FRAME clause
    (``valScores = vlScores``), so the contradiction is purely structural — a
    list cannot equal itself extended by one element;
  * ``weak-val-read-hoisted``, ``weak-val-score-hoisted`` and
    ``weak-labels-hoisted`` violate the ok/error DISPOSITION: (C_no) demands a
    success and the rival returns ``Except.error``, and
    ``Except.error ≠ Except.ok`` needs no assumption;
  * ``weak-val-scorecall-hoisted`` violates the same disposition from the other
    direction — (C_no) demands the success built from the answer about the
    TRAINING pair, and the rival propagates the refusal it drew by consulting the
    scorer about a pair the contract does not name. The refusing scorer is
    supplied by the witness, so there is nothing to assume;
  * ``weak-val-order-swapped`` violates the DISPOSITION between two DIFFERENT
    error values: on the newly ordered ``(C_err)`` arm the contract demands the
    decode's ``codeOutOfRange`` and the rival, having read the design matrix
    first, returns ``absentValidationData``. Two distinct constructors of
    ``EarlyStopError``, so nothing about the carrier is assumed;
  * ``weak-getd-train-decode-hoisted`` and ``weak-getd-val-decode-hoisted``
    violate the disposition on the FOURTH error value: at ``isClf = false`` with
    no table and codes ``#[0]``, (C_no) demands the success built from the RAW
    training call, and each rival returns ``Except.error codeOutOfRange`` because
    the gather it performed above the guard ran on the empty ``getD`` stand-in
    table. ``Except.error ≠ Except.ok`` again needs no assumption — and that is
    the point of the case: the same rival under the previously TOTAL decode
    returned exactly the demanded success, so this witness did not exist and
    could not have.
Those eight assume NOTHING about the carrier, which is the strongest form an
attack can take on an opaque one. (They are still probed: ``consistency_probe``
builds ``example <binders> : False`` for every declaration that binds anything,
and these bind the opaque ``scorer``/``xTrain``/history arguments they are stated
over. Nothing follows from those types, so the probe fails as it must — measured,
exit 1, for all fourteen reject cases.)

Each gold-side failure was read, not just counted: every one reports that the
witness's own restatement of the spec equation does not typecheck against the
frozen impl's value, never an unknown identifier, a stuck unfolding, or a
timeout.

BINDER / CLAUSE COVERAGE. The reject witnesses vary the discriminating binders:
  * ``isClf`` — refuted at ``true`` (prepatch, val-undecoded, first-element-raw,
    val-frame, stop-uses-train, stop-no-val-unextended, both val hoists) AND at
    ``false`` (regressor-decode, labels-hoisted, val-scorecall-hoisted, both getd
    decode hoists), so the ``targetFor`` selector is pinned on both paths.
  * ``labels`` — refuted at ``some`` (ten cases) AND at ``none``
    (labels-hoisted, val-scorecall-hoisted and both getd decode hoists — the
    rivals whose witnesses need the table to be ABSENT), so the (C_lbl)
    disposition is pinned rather than assumed. The complementary direction is
    held by ``pos-labels-map-precompute``, which precomputes from a PRESENT table
    without reading an absent one and must verify.
  * ``useVal`` — refuted at ``false`` (prepatch, regressor-decode, val-frame,
    first-element-raw, stop-no-val-unextended, all three val hoists,
    labels-hoisted, both getd decode hoists)
    AND at ``true`` (val-undecoded, stop-uses-train, val-order-swapped),
    exercising the (C_no), the (C_val) AND the (C_err) branch. ``useVal=true`` is additionally exercised by the
    ADMISSIBILITY positive, which is the only case that reaches (C_val) at fully
    CONCRETE targets.
  * ``xVal`` / ``yVal`` — refuted at ``none, none`` (prepatch,
    first-element-raw, stop-no-val-unextended, val-read-hoisted,
    labels-hoisted, val-scorecall-hoisted, both getd decode hoists), at
    ``some, none`` (val-score-hoisted), at ``none, some``
    (val-order-swapped — the ONLY reject case on the arm where the two
    validation reads' order is observable) and at
    ``some, some`` (val-undecoded, val-frame, stop-uses-train), so the presence
    pattern is pinned at four distinct points rather than only where the
    arguments are supplied.
  * The scoring ARGUMENT (``Sum.inl`` vs ``Sum.inr`` of the decoded labels) is
    separated on the train site (prepatch, regressor) and the val site
    (val-undecoded); ``relabelTargets``'s per-element GATHER is separated
    independently of the branch by ``weak-first-element-raw``, which stays inside
    ``Sum.inr`` and differs at one position only.
  * The scoring function's PARTIALITY — an axis the binder point cannot show,
    because it lives in the ``scorer`` argument rather than in the flags. Thirteen
    of the fourteen reject witnesses instantiate a TOTAL scorer, so their
    refutations hold verbatim under the previous, total-``scorer`` interface;
    ``weak-val-scorecall-hoisted`` instantiates one that refuses a single pair,
    which is what separates WHICH pair the scorer is consulted about from WHICH
    score is recorded. Its binder point coincides with ``weak-labels-hoisted``'s,
    and that coincidence is the evidence that the new axis is independent of the
    five flags: same input point, different scorer, a rival that no flag-only
    clause can see. The axis is bounded from the other side by
    ``pos-unbound-consult``, which mentions the refusable application without
    binding it and must verify.
  * The DECODE's partiality — the same kind of axis, and likewise invisible to
    the flags. The two getd decode hoists are refuted with a TOTAL scorer, at an
    input where the contract asks for no decode at all (``isClf = false``,
    ``labels = none``): what refutes them is that they performed one anyway, on a
    stand-in table, and the gather's own failure is the result they return. Under
    the previously TOTAL decode both were VERIFYING rivals whose patches broke the
    suite, so this axis is the one the current repair adds. It is bounded from the
    other side by ``pos-unbound-consult`` (names the stand-in decode, performs
    none) and by ``pos-labels-map-precompute`` / ``pos-option-map-precompute``
    (perform the decode, but on the table the caller supplied).
  * ``result``'s components are each attacked: ``trainScores`` (prepatch,
    regressor, first-element-raw), ``valScores`` (val-undecoded, val-frame),
    ``stop`` on BOTH branches (stop-uses-train at useVal=true,
    stop-no-val-unextended at useVal=false) and the ok/error DISPOSITION on ALL
    FOUR error values (``absentValidationData``: the read and score hoists;
    ``absentClassLabels``: labels-hoisted; ``scoringRefused``:
    val-scorecall-hoisted; ``codeOutOfRange``: both getd decode hoists and
    val-order-swapped, which is the only case that separates TWO error values
    from each other rather than an error from a success), so no clause of the
    frozen contract is left without a rival.
``pts`` = 7 distinct ``(isClf, useVal, labels.isSome, xVal.isSome, yVal.isSome)``
reject points — ``(T,F,S,N,N)`` prepatch / first-element-raw /
stop-no-val-unextended / val-read-hoisted, ``(F,F,S,N,N)`` regressor-decode,
``(T,T,S,S,S)`` val-undecoded / stop-uses-train, ``(T,F,S,S,S)`` val-frame,
``(T,F,S,S,N)`` val-score-hoisted, ``(T,T,S,N,S)`` val-order-swapped,
``(F,F,N,N,N)`` labels-hoisted /
val-scorecall-hoisted / getd-train-decode-hoisted / getd-val-decode-hoisted —
and within ``(T,F,S,N,N)`` two distinct target-array shapes (whole-array vs
one-position-off), and within ``(F,F,N,N,N)`` three distinct MECHANISMS at one
input point (a total scorer refuting an absent-table read; a scorer that refuses
one pair, refuting a call on a stand-in; and a total scorer refuting a GATHER on
a stand-in, which is the fourth error value); the admissibility positive adds a
fully GROUND point (true/true at literal codes and a literal label table).

AXIOM lane: EMPTY. AXIOM_TESTS = [].
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-14710"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region interior (the guarded re-encodings, the guarded reads of
# the validation arguments, and the returns) and the FULL frozen tactic body, so
# every replacement lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "  let mut trainScores := trScores\n"
    "  let mut valScores := vlScores\n"
    "  -- Decode a categorical estimator's integer-coded training targets before\n"
    "  -- scoring; forward the raw targets otherwise. The class-label table is read\n"
    "  -- here and on the matching validation line, and nowhere else: those are the\n"
    "  -- only places on which the estimator is known to have one.\n"
    "  let mut yT : Targets := Sum.inl yTrain\n"
    "  if isClf then\n"
    "    let ls ← readLabels labels\n"
    "    -- The decode is performed here, on the table just read and these codes, and a\n"
    "    -- code that table has no entry for is reported rather than stood in for.\n"
    "    let decoded ← relabelTargets ls yTrain\n"
    "    yT := Sum.inr decoded\n"
    "  -- The scoring function is consulted here on the training pair, and on the\n"
    "  -- matching validation line on the validation pair, and nowhere else; a refusal\n"
    "  -- of either pair is reported.\n"
    "  let trScore ← scorer xTrain yT\n"
    "  trainScores := trainScores ++ [trScore]\n"
    "  if useVal then\n"
    "    -- The validation arguments are read here and nowhere else: this is the only\n"
    "    -- branch on which the caller created them. The target codes come first, and\n"
    "    -- are decoded, before the design matrix is touched: a code the class-label\n"
    "    -- table has no entry for is reported by the decode, whatever the design\n"
    "    -- matrix holds.\n"
    "    let codes ← readValCodes yVal\n"
    "    -- Likewise decode the validation targets for a categorical estimator.\n"
    "    let mut yV : Targets := Sum.inl codes\n"
    "    if isClf then\n"
    "      let ls ← readLabels labels\n"
    "      let decoded ← relabelTargets ls codes\n"
    "      yV := Sum.inr decoded\n"
    "    let xv ← readValData xVal\n"
    "    let vlScore ← scorer xv yV\n"
    "    valScores := valScores ++ [vlScore]\n"
    "    return { trainScores := trainScores, valScores := valScores,\n"
    "             stop := shouldStop valScores }\n"
    "  return { trainScores := trainScores, valScores := valScores,\n"
    "           stop := shouldStop trainScores }"
)

_PROOF_BODY = (
    "  intro scorer shouldStop isClf useVal labels xTrain yTrain xVal yVal trScores vlScores\n"
    "  unfold problem_spec_scoreEarlyStop implementation_scoreEarlyStop\n"
    "  cases isClf <;> cases labels <;> cases useVal <;> cases xVal <;> cases yVal <;> rfl"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"

# The frozen tactic body's first line, used as the insertion point for the
# admissibility case's ground `have` (which is PREPENDED, leaving the frozen
# obligation to be closed verbatim by the unchanged body below it).
_PROOF_INTRO = (
    "  intro scorer shouldStop isClf useVal labels xTrain yTrain xVal yVal trScores vlScores\n"
)
assert _BASE.count(_PROOF_INTRO) == 1, "proof intro drifted; update _PROOF_INTRO"


def _impl(body):
    """Full Solution.lean variant produced by replacing the gold impl body."""
    return _swap(_BASE, _IMPL_GOLD, body)


def _impl_proof(body, proof):
    """`_impl(body)` with the frozen tactic body replaced by `proof`.

    The proof region is editable for a positive — ``markers.same_spec`` elides it,
    and what must stay byte-identical is the theorem STATEMENT — and the PARTIAL
    decode makes that latitude necessary rather than cosmetic. The contract binds
    the decode ITSELF (`(relabelTargets ls yTrain).bind fun yT => …`), so a reshape
    that instead binds the decoded TARGET ARRAY (`targetFor …` or an inline
    equivalent, i.e. `(… .map Sum.inr) >>= k`) differs from the contract by one
    monad-law step — and on a decode that is STUCK under the opaque class-label
    table neither side reduces, so `rfl` cannot perform it. Each proof below
    supplies exactly that step as a `have` inside the existing tactic body: no new
    declaration, no axiom, no assumption token, and nothing case-specific about
    the goal it closes.
    """
    return _swap(_impl(body), _PROOF_BODY, proof)


# The monad-law step, plus the frozen body that uses it. `__SIMP__` is the
# `simp only` set: `htf`/`hmap` do the reassociation, and a case adds whatever
# reduction ITS OWN reshape leaves in the way (`if_true` for a `let` the
# elaborator guards with a literal `True`, `Option.map` / `readLabels` /
# `Except.bind` for a precomputation the case performs through one of those).
# Each set below is the one measured to close every one of the 32 goals the
# five-fold `cases` leaves; a smaller set leaves goals open, which is why they
# differ per case rather than being unified into one over-large set.
_PROOF_REASSOC_TEMPLATE = r'''  intro scorer shouldStop isClf useVal labels xTrain yTrain xVal yVal trScores vlScores
  -- This reshape binds the decoded TARGET ARRAY where the contract binds the
  -- DECODE itself, so the two sides differ by one monad-law step on a decode that
  -- is stuck under the opaque table: `(x.map Sum.inr) >>= k` against
  -- `x >>= (k ∘ Sum.inr)`. The step is supplied here, as a `have` inside the
  -- existing tactic body -- no declaration, axiom, or assumption token, and the
  -- theorem STATEMENT is byte-identical.
  have htf : ∀ (ls : Array String) (cs : Array Int),
      targetFor true (some ls) cs
        = (relabelTargets ls cs).map (Sum.inr : Array String → Targets) :=
    fun _ _ => rfl
  have hmap : ∀ {β : Type} (x : Except EarlyStopError (Array String))
      (k : Targets → Except EarlyStopError β),
      (Except.map (Sum.inr : Array String → Targets) x) >>= k
        = x >>= fun d => k (Sum.inr d) := by
    intro β x k; cases x <;> rfl
  unfold problem_spec_scoreEarlyStop implementation_scoreEarlyStop
  cases isClf <;> cases labels <;> cases useVal <;> cases xVal <;> cases yVal <;>
    (first
      | rfl
      | (simp only [__SIMP__]; rfl)
      | simp only [__SIMP__])'''


def _proof_reassoc(*extra):
    """The reassociating proof, with `extra` prepended to its `simp only` set."""
    return _PROOF_REASSOC_TEMPLATE.replace(
        "__SIMP__", ", ".join(tuple(extra) + ("htf", "hmap")))


# The same step one `bind` deeper, for the positive that names a stand-in ANSWER
# (`decode >>= scorer >>= …`) rather than a stand-in target array: there the
# reassociation has to move across two binds at once.
_PROOF_REASSOC_BIND = r'''  intro scorer shouldStop isClf useVal labels xTrain yTrain xVal yVal trScores vlScores
  -- The stand-in answer is a `bind` on the stand-in decode, and the contract
  -- binds the decode first, so where the two coincide they differ by one
  -- monad-law step on a decode stuck under the opaque table:
  -- `((x.map Sum.inr) >>= f) >>= g` against `x >>= fun d => f (Sum.inr d) >>= g`.
  -- Supplied here as a `have` inside the existing tactic body -- no declaration,
  -- axiom, or assumption token, and the theorem STATEMENT is byte-identical.
  have hb : ∀ {β γ : Type} (x : Except EarlyStopError (Array String))
      (f : Targets → Except EarlyStopError β) (g : β → Except EarlyStopError γ),
      ((Except.map (Sum.inr : Array String → Targets) x) >>= f) >>= g
        = x >>= fun d => (f (Sum.inr d) >>= g) := by
    intro β γ x f g; cases x <;> rfl
  have hdup : ∀ {β γ : Type} (x : Except EarlyStopError (Array String))
      (m : Except EarlyStopError β) (f : Array String → Except EarlyStopError γ),
      ((Except.map (Sum.inr : Array String → Targets) x) >>= fun _ => (m >>= fun _ => x >>= f))
        = x >>= fun d => (m >>= fun _ => f d) := by
    intro β γ x m f; cases x <;> rfl
  unfold problem_spec_scoreEarlyStop implementation_scoreEarlyStop
  cases isClf <;> cases labels <;> cases useVal <;> cases xVal <;> cases yVal <;>
    (first
      | rfl
      | (simp only [if_true, hb, hdup, readValCodes, readValData, Option.getD]; rfl)
      | simp only [if_true, hb, hdup, readValCodes, readValData, Option.getD])'''


# ---------------------------------------------------------------------------
# Rival impl bodies (each a full impl-region interior; only the impl changes, so
# the spec and the theorem STATEMENT stay byte-identical).
# ---------------------------------------------------------------------------

# PREPATCH (= the literal pre-fix bug): the classifier path forwards the RAW
# integer codes (`Sum.inl`) instead of the decoded labels — the guard that
# selects `relabelTargets` is dropped on BOTH sites. The validation arguments are
# still read only on the branch that has them, so this rival isolates the missing
# decode.
_IMPL_PREPATCH = (
    "  let mut trainScores := trScores\n"
    "  let mut valScores := vlScores\n"
    "  let trScore ← scorer xTrain (Sum.inl yTrain)\n"
    "  trainScores := trainScores ++ [trScore]\n"
    "  if useVal then\n"
    "    let xv ← readValData xVal\n"
    "    let codes ← readValCodes yVal\n"
    "    let vlScore ← scorer xv (Sum.inl codes)\n"
    "    valScores := valScores ++ [vlScore]\n"
    "    return { trainScores := trainScores, valScores := valScores,\n"
    "             stop := shouldStop valScores }\n"
    "  return { trainScores := trainScores, valScores := valScores,\n"
    "           stop := shouldStop trainScores }"
)

# REGRESSOR-DECODE (passthrough-clause attack): the re-encoding is applied
# UNCONDITIONALLY (the `isClf` guard is dropped), so the NON-classifier path
# decodes too, violating the raw-codes selection of `targetFor` when isClf=false.
_IMPL_REGRESSOR_DECODE = (
    "  let mut trainScores := trScores\n"
    "  let mut valScores := vlScores\n"
    "  let ls ← readLabels labels\n"
    "  let trScore ← scorer xTrain (Sum.inr (← relabelTargets ls yTrain))\n"
    "  trainScores := trainScores ++ [trScore]\n"
    "  if useVal then\n"
    "    let xv ← readValData xVal\n"
    "    let codes ← readValCodes yVal\n"
    "    let vlScore ← scorer xv (Sum.inr (← relabelTargets ls codes))\n"
    "    valScores := valScores ++ [vlScore]\n"
    "    return { trainScores := trainScores, valScores := valScores,\n"
    "             stop := shouldStop valScores }\n"
    "  return { trainScores := trainScores, valScores := valScores,\n"
    "           stop := shouldStop trainScores }"
)

# VAL-UNDECODED (one-site partial-domain): the TRAINING path decodes correctly
# but the VALIDATION path forwards raw codes — the two scoring sites are
# re-encoded independently, and this rival misses exactly one of them.
_IMPL_VAL_UNDECODED = (
    "  let mut trainScores := trScores\n"
    "  let mut valScores := vlScores\n"
    "  let mut yT : Targets := Sum.inl yTrain\n"
    "  if isClf then\n"
    "    let ls ← readLabels labels\n"
    "    yT := Sum.inr (← relabelTargets ls yTrain)\n"
    "  let trScore ← scorer xTrain yT\n"
    "  trainScores := trainScores ++ [trScore]\n"
    "  if useVal then\n"
    "    let xv ← readValData xVal\n"
    "    let codes ← readValCodes yVal\n"
    "    let vlScore ← scorer xv (Sum.inl codes)\n"
    "    valScores := valScores ++ [vlScore]\n"
    "    return { trainScores := trainScores, valScores := valScores,\n"
    "             stop := shouldStop valScores }\n"
    "  return { trainScores := trainScores, valScores := valScores,\n"
    "           stop := shouldStop trainScores }"
)

# FIRST-ELEMENT-RAW (element-level sub-domain miss): the classifier path DOES take
# the decoded branch, and relabels every code EXCEPT position 0, which keeps its
# raw code rendered as text. Attacks the per-element gather inside
# `relabelTargets` rather than the choice of `Sum` branch, which the three
# whole-array rivals already cover.
_IMPL_FIRST_ELEMENT_RAW = (
    "  let mut trainScores := trScores\n"
    "  let mut valScores := vlScores\n"
    "  let mut yT : Targets := Sum.inl yTrain\n"
    "  if isClf then\n"
    "    let ls ← readLabels labels\n"
    "    yT := Sum.inr ((← relabelTargets ls yTrain).set! 0 (toString (yTrain[0]!)))\n"
    "  let trScore ← scorer xTrain yT\n"
    "  trainScores := trainScores ++ [trScore]\n"
    "  if useVal then\n"
    "    let xv ← readValData xVal\n"
    "    let codes ← readValCodes yVal\n"
    "    let mut yV : Targets := Sum.inl codes\n"
    "    if isClf then\n"
    "      let ls ← readLabels labels\n"
    "      yV := Sum.inr (← relabelTargets ls codes)\n"
    "    let vlScore ← scorer xv yV\n"
    "    valScores := valScores ++ [vlScore]\n"
    "    return { trainScores := trainScores, valScores := valScores,\n"
    "             stop := shouldStop valScores }\n"
    "  return { trainScores := trainScores, valScores := valScores,\n"
    "           stop := shouldStop trainScores }"
)

# VAL-FRAME-EXTENDED (frame obligation, spec_guide §0.5): the validation history is
# extended UNCONDITIONALLY, so when validation data is NOT in use a component the
# contract requires to be carried through unchanged is changed anyway. Both
# `targetFor` selections and both history contents are otherwise gold. Its witness
# is taken at SUPPLIED validation arguments, where the ok/error disposition is not
# in play, so the refutation is attributable to the frame clause alone.
_IMPL_VAL_FRAME_EXTENDED = (
    "  let mut trainScores := trScores\n"
    "  let mut valScores := vlScores\n"
    "  let mut yT : Targets := Sum.inl yTrain\n"
    "  if isClf then\n"
    "    let ls ← readLabels labels\n"
    "    yT := Sum.inr (← relabelTargets ls yTrain)\n"
    "  let trScore ← scorer xTrain yT\n"
    "  trainScores := trainScores ++ [trScore]\n"
    "  let xv ← readValData xVal\n"
    "  let codes ← readValCodes yVal\n"
    "  let mut yV : Targets := Sum.inl codes\n"
    "  if isClf then\n"
    "    let ls ← readLabels labels\n"
    "    yV := Sum.inr (← relabelTargets ls codes)\n"
    "  let vlScore ← scorer xv yV\n"
    "  valScores := valScores ++ [vlScore]\n"
    "  if useVal then\n"
    "    return { trainScores := trainScores, valScores := valScores,\n"
    "             stop := shouldStop valScores }\n"
    "  return { trainScores := trainScores, valScores := valScores,\n"
    "           stop := shouldStop trainScores }"
)

# STOP-USES-TRAIN (stop-decision clause): every history is recorded exactly as
# gold, with both `targetFor` selections correct and the validation arguments read
# only where they exist, but the stop decision always consults the TRAINING
# history — so on the validation path the stopping rule is asked about the wrong
# history.
_IMPL_STOP_USES_TRAIN = (
    "  let mut trainScores := trScores\n"
    "  let mut valScores := vlScores\n"
    "  let mut yT : Targets := Sum.inl yTrain\n"
    "  if isClf then\n"
    "    let ls ← readLabels labels\n"
    "    yT := Sum.inr (← relabelTargets ls yTrain)\n"
    "  let trScore ← scorer xTrain yT\n"
    "  trainScores := trainScores ++ [trScore]\n"
    "  if useVal then\n"
    "    let xv ← readValData xVal\n"
    "    let codes ← readValCodes yVal\n"
    "    let mut yV : Targets := Sum.inl codes\n"
    "    if isClf then\n"
    "      let ls ← readLabels labels\n"
    "      yV := Sum.inr (← relabelTargets ls codes)\n"
    "    let vlScore ← scorer xv yV\n"
    "    valScores := valScores ++ [vlScore]\n"
    "    return { trainScores := trainScores, valScores := valScores,\n"
    "             stop := shouldStop trainScores }\n"
    "  return { trainScores := trainScores, valScores := valScores,\n"
    "           stop := shouldStop trainScores }"
)

# STOP-NO-VAL (the (C_no) stop conjunct): every history is recorded exactly as
# gold and both `targetFor` selections are correct, but on the NO-validation path
# the stopping rule is consulted on the training history as it was HANDED IN,
# before this call's own score was appended. Attacks the clause conjunct the other
# rivals leave untouched: `weak-stop-uses-train` pins WHICH history the decision
# reads at useVal=true, and this pins that at useVal=false it must be the EXTENDED
# one.
_IMPL_STOP_NO_VAL_UNEXTENDED = (
    "  let mut trainScores := trScores\n"
    "  let mut valScores := vlScores\n"
    "  let mut yT : Targets := Sum.inl yTrain\n"
    "  if isClf then\n"
    "    let ls ← readLabels labels\n"
    "    yT := Sum.inr (← relabelTargets ls yTrain)\n"
    "  let trScore ← scorer xTrain yT\n"
    "  trainScores := trainScores ++ [trScore]\n"
    "  if useVal then\n"
    "    let xv ← readValData xVal\n"
    "    let codes ← readValCodes yVal\n"
    "    let mut yV : Targets := Sum.inl codes\n"
    "    if isClf then\n"
    "      let ls ← readLabels labels\n"
    "      yV := Sum.inr (← relabelTargets ls codes)\n"
    "    let vlScore ← scorer xv yV\n"
    "    valScores := valScores ++ [vlScore]\n"
    "    return { trainScores := trainScores, valScores := valScores,\n"
    "             stop := shouldStop valScores }\n"
    "  return { trainScores := trainScores, valScores := valScores,\n"
    "           stop := shouldStop trScores }"
)

# VAL-READ-HOISTED — the machine-checked attack that broke the PREVIOUS contract
# (`atk_2.lean`, verified 2026-08-16), re-encoded against this one. The validation
# arguments are read and decoded BEFORE the branch that knows whether they exist;
# on the no-validation path they do not exist, so the read is a crash rather than
# a dead computation. Everything else is gold.
_IMPL_VAL_READ_HOISTED = (
    "  let mut trainScores := trScores\n"
    "  let mut valScores := vlScores\n"
    "  let mut yT : Targets := Sum.inl yTrain\n"
    "  if isClf then\n"
    "    let ls ← readLabels labels\n"
    "    yT := Sum.inr (← relabelTargets ls yTrain)\n"
    "  let xv ← readValData xVal\n"
    "  let codes ← readValCodes yVal\n"
    "  let mut yV : Targets := Sum.inl codes\n"
    "  if isClf then\n"
    "    let ls ← readLabels labels\n"
    "    yV := Sum.inr (← relabelTargets ls codes)\n"
    "  let trScore ← scorer xTrain yT\n"
    "  trainScores := trainScores ++ [trScore]\n"
    "  if useVal then\n"
    "    let vlScore ← scorer xv yV\n"
    "    valScores := valScores ++ [vlScore]\n"
    "    return { trainScores := trainScores, valScores := valScores,\n"
    "             stop := shouldStop valScores }\n"
    "  return { trainScores := trainScores, valScores := valScores,\n"
    "           stop := shouldStop trainScores }"
)

# VAL-SCORE-HOISTED — the same defect one step further (`atk_3.lean`): the
# validation SCORE itself is computed before the guard, so the scoring call joins
# the read above the branch. A repair has to reject both shapes.
_IMPL_VAL_SCORE_HOISTED = (
    "  let mut trainScores := trScores\n"
    "  let mut valScores := vlScores\n"
    "  let mut yT : Targets := Sum.inl yTrain\n"
    "  if isClf then\n"
    "    let ls ← readLabels labels\n"
    "    yT := Sum.inr (← relabelTargets ls yTrain)\n"
    "  let xv ← readValData xVal\n"
    "  let codes ← readValCodes yVal\n"
    "  let mut yV : Targets := Sum.inl codes\n"
    "  if isClf then\n"
    "    let ls ← readLabels labels\n"
    "    yV := Sum.inr (← relabelTargets ls codes)\n"
    "  let vlScore ← scorer xv yV\n"
    "  let trScore ← scorer xTrain yT\n"
    "  trainScores := trainScores ++ [trScore]\n"
    "  if useVal then\n"
    "    valScores := valScores ++ [vlScore]\n"
    "    return { trainScores := trainScores, valScores := valScores,\n"
    "             stop := shouldStop valScores }\n"
    "  return { trainScores := trainScores, valScores := valScores,\n"
    "           stop := shouldStop trainScores }"
)

# VAL-SCORECALL-HOISTED — the attack that broke the OPTION-plus-ERROR contract
# while both validation READS stayed inside the guard, machine-checked by the
# live G-EQ reviewer as `atk_8.lean` on 2026-08-16 (same_spec=True,
# verifies=True, axioms `[propext]`). Nothing absent is read: the rival assembles
# a STAND-IN pair out of `Option.getD` defaults (`xVal.getD xTrain`,
# `yVal.getD #[]`, `labels.getD #[]`), consults the scoring function about that
# pair ABOVE the guard, and inside the guard — where the stand-ins coincide with
# the real arguments — records the answer it already has. Every recorded value is
# gold's at every input, and both guarded reads are still performed, so no
# clause about reads or about recorded scores can see it. What sees it is the
# scoring function's PARTIALITY: the stand-in pair is a design matrix and a
# target array that need not describe the same samples, and the contract names
# the answer about the pair it names.
# Retyped for the PARTIAL decode: the stand-in target array is now an `Except`,
# so the hoisted consult binds through it. Its witness point is unchanged and
# keeps isClf=false, where the decode is not taken at all — so what refutes this
# rival is still the refused CALL, not a `codeOutOfRange` from the stand-in
# table, and the case stays attributable to the scoring clause alone.
_IMPL_VAL_SCORECALL_HOISTED = (
    "  let mut trainScores := trScores\n"
    "  let mut valScores := vlScores\n"
    "  let hoistedTargets : Except EarlyStopError Targets :=\n"
    "    if isClf then (relabelTargets (labels.getD #[]) (yVal.getD #[])).map Sum.inr\n"
    "    else Except.ok (Sum.inl (yVal.getD #[]))\n"
    "  let hoistedScore ← Except.bind hoistedTargets\n"
    "    (fun t => scorer (xVal.getD xTrain) t)\n"
    "  let mut yT : Targets := Sum.inl yTrain\n"
    "  if isClf then\n"
    "    let ls ← readLabels labels\n"
    "    yT := Sum.inr (← relabelTargets ls yTrain)\n"
    "  let trScore ← scorer xTrain yT\n"
    "  trainScores := trainScores ++ [trScore]\n"
    "  if useVal then\n"
    "    let _xv ← readValData xVal\n"
    "    let _codes ← readValCodes yVal\n"
    "    valScores := valScores ++ [hoistedScore]\n"
    "    return { trainScores := trainScores, valScores := valScores,\n"
    "             stop := shouldStop valScores }\n"
    "  return { trainScores := trainScores, valScores := valScores,\n"
    "           stop := shouldStop trainScores }"
)

# LABELS-HOISTED — the class-label table is read ABOVE the branch that knows the
# estimator is categorical. The two decodes are still guarded by `isClf`, so
# every recorded score is gold's whenever the table exists; the defect is that a
# non-categorical estimator, which has no table, is made to produce one. This is
# the class-label-table analogue of `weak-val-read-hoisted`, and it is the rival
# the earlier TOTAL `labels` interface could not express.
_IMPL_LABELS_HOISTED = (
    "  let mut trainScores := trScores\n"
    "  let mut valScores := vlScores\n"
    "  let ls ← readLabels labels\n"
    "  let mut yT : Targets := Sum.inl yTrain\n"
    "  if isClf then\n"
    "    yT := Sum.inr (← relabelTargets ls yTrain)\n"
    "  let trScore ← scorer xTrain yT\n"
    "  trainScores := trainScores ++ [trScore]\n"
    "  if useVal then\n"
    "    let xv ← readValData xVal\n"
    "    let codes ← readValCodes yVal\n"
    "    let mut yV : Targets := Sum.inl codes\n"
    "    if isClf then\n"
    "      yV := Sum.inr (← relabelTargets ls codes)\n"
    "    let vlScore ← scorer xv yV\n"
    "    valScores := valScores ++ [vlScore]\n"
    "    return { trainScores := trainScores, valScores := valScores,\n"
    "             stop := shouldStop valScores }\n"
    "  return { trainScores := trainScores, valScores := valScores,\n"
    "           stop := shouldStop trainScores }"
)

# VAL-ORDER-SWAPPED — the shape the live G-PANEL audit refuted the previous
# contract with, kept as the rival that pins the ORDER of the two validation
# reads. Everything is gold's except the two lines inside the `useVal` guard: the
# design matrix is read BEFORE the target codes are read and decoded, which is the
# order the previous `(C_err)` arm demanded and is NOT the order the method has.
# Its faithful real patch is the gold patch with
# `y_val = self.classes_[y_val.astype(int)]` moved BELOW the
# `self.scorer_(self, X_binned_val, y_val)` line's argument evaluation — i.e. the
# design matrix consulted first — which cannot resolve, because the F2P scenario
# needs the decoded labels to reach the scorer at all: moving the decode after the
# call that consumes it hands the scorer the raw integer codes, which is the
# pre-patch defect (`test_string_target_early_stopping`). The rival is therefore
# refuted where the ORDER is observable, not where the values are, and that is the
# point of the case: the arm `| true, some ls, true, _, yv` is the one the audit
# repaired, and this is the only rival that lands on it.
_IMPL_VAL_ORDER_SWAPPED = (
    "  let mut trainScores := trScores\n"
    "  let mut valScores := vlScores\n"
    "  let mut yT : Targets := Sum.inl yTrain\n"
    "  if isClf then\n"
    "    let ls \u2190 readLabels labels\n"
    "    let decoded \u2190 relabelTargets ls yTrain\n"
    "    yT := Sum.inr decoded\n"
    "  let trScore \u2190 scorer xTrain yT\n"
    "  trainScores := trainScores ++ [trScore]\n"
    "  if useVal then\n"
    "    let xv \u2190 readValData xVal\n"
    "    let codes \u2190 readValCodes yVal\n"
    "    let mut yV : Targets := Sum.inl codes\n"
    "    if isClf then\n"
    "      let ls \u2190 readLabels labels\n"
    "      let decoded \u2190 relabelTargets ls codes\n"
    "      yV := Sum.inr decoded\n"
    "    let vlScore \u2190 scorer xv yV\n"
    "    valScores := valScores ++ [vlScore]\n"
    "    return { trainScores := trainScores, valScores := valScores,\n"
    "             stop := shouldStop valScores }\n"
    "  return { trainScores := trainScores, valScores := valScores,\n"
    "           stop := shouldStop trainScores }"
)


# POSITIVE 1 (helper-delegating reshape): compute the scoring argument once via
# the `targetFor` helper into a `let`, dropping the mutable two-step guard.
_IMPL_POS_TARGETFOR = (
    "  let mut trainScores := trScores\n"
    "  let mut valScores := vlScores\n"
    "  let yT ← targetFor isClf labels yTrain\n"
    "  let trScore ← scorer xTrain yT\n"
    "  trainScores := trainScores ++ [trScore]\n"
    "  if useVal then\n"
    "    let codes ← readValCodes yVal\n"
    "    let yV ← targetFor isClf labels codes\n"
    "    let xv ← readValData xVal\n"
    "    let vlScore ← scorer xv yV\n"
    "    valScores := valScores ++ [vlScore]\n"
    "    return { trainScores := trainScores, valScores := valScores,\n"
    "             stop := shouldStop valScores }\n"
    "  return { trainScores := trainScores, valScores := valScores,\n"
    "           stop := shouldStop trainScores }"
)

# POSITIVE 2 (inline if-then-else reshape): the same selection expressed inline —
# read the table through the frozen reader, decode, and tag the RESULT with
# `Sum.inr` — which is definitionally the frozen `targetFor`. Because the decode is
# partial the tag lands under `.map` rather than on a bare array, so the reshape
# binds the decoded ARRAY where the contract binds the DECODE and its proof
# supplies the one monad-law step for that (see `_impl_proof`).
_IMPL_POS_INLINE = (
    "  let mut trainScores := trScores\n"
    "  let mut valScores := vlScores\n"
    "  let yT ←\n"
    "    if isClf then\n"
    "      Except.bind (readLabels labels) (fun ls => (relabelTargets ls yTrain).map Sum.inr)\n"
    "    else Except.ok (Sum.inl yTrain)\n"
    "  let trScore ← scorer xTrain yT\n"
    "  trainScores := trainScores ++ [trScore]\n"
    "  if useVal then\n"
    "    let codes ← readValCodes yVal\n"
    "    let yV ←\n"
    "      if isClf then\n"
    "        Except.bind (readLabels labels) (fun ls => (relabelTargets ls codes).map Sum.inr)\n"
    "      else Except.ok (Sum.inl codes)\n"
    "    let xv ← readValData xVal\n"
    "    let vlScore ← scorer xv yV\n"
    "    valScores := valScores ++ [vlScore]\n"
    "    return { trainScores := trainScores, valScores := valScores,\n"
    "             stop := shouldStop valScores }\n"
    "  return { trainScores := trainScores, valScores := valScores,\n"
    "           stop := shouldStop trainScores }"
)

# POSITIVE 3 (match-on-Bool reshape): the selection performed by `match isClf
# with` rather than by `if`, a DIFFERENT elimination form for the same Bool.
_IMPL_POS_MATCH = (
    "  let mut trainScores := trScores\n"
    "  let mut valScores := vlScores\n"
    "  let yT ←\n"
    "    match isClf, labels with\n"
    "    | true, some ls => (relabelTargets ls yTrain).map Sum.inr\n"
    "    | true, none => Except.error EarlyStopError.absentClassLabels\n"
    "    | false, _ => Except.ok (Sum.inl yTrain)\n"
    "  let trScore ← scorer xTrain yT\n"
    "  trainScores := trainScores ++ [trScore]\n"
    "  if useVal then\n"
    "    let codes ← readValCodes yVal\n"
    "    let yV ←\n"
    "      match isClf, labels with\n"
    "      | true, some ls => (relabelTargets ls codes).map Sum.inr\n"
    "      | true, none => Except.error EarlyStopError.absentClassLabels\n"
    "      | false, _ => Except.ok (Sum.inl codes)\n"
    "    let xv ← readValData xVal\n"
    "    let vlScore ← scorer xv yV\n"
    "    valScores := valScores ++ [vlScore]\n"
    "    return { trainScores := trainScores, valScores := valScores,\n"
    "             stop := shouldStop valScores }\n"
    "  return { trainScores := trainScores, valScores := valScores,\n"
    "           stop := shouldStop trainScores }"
)

# POSITIVE 4 (record-direct reshape): drop the mutable accumulators entirely and
# build each history as a single `let`-bound expression, naming it once and
# reusing it for the stop decision. The furthest reshape from the frozen `let mut`
# shape that is still a faithful skeleton.
_IMPL_POS_RECORD_DIRECT = (
    "  let yT ← targetFor isClf labels yTrain\n"
    "  let trScore ← scorer xTrain yT\n"
    "  let tr := trScores ++ [trScore]\n"
    "  if useVal then\n"
    "    let codes ← readValCodes yVal\n"
    "    let yV ← targetFor isClf labels codes\n"
    "    let xv ← readValData xVal\n"
    "    let vlScore ← scorer xv yV\n"
    "    let vl := vlScores ++ [vlScore]\n"
    "    return { trainScores := tr, valScores := vl, stop := shouldStop vl }\n"
    "  return { trainScores := tr, valScores := vlScores, stop := shouldStop tr }"
)

# POSITIVE 5 (defended precomputation): the decoded validation targets are
# computed BEFORE the branch, but UNDER `Option.map`, so an absent argument is
# never read — the Lean analogue of the defensive
# `y_val = self.classes_[y_val.astype(int)] if y_val is not None else None`.
# Correct, and must verify: the new clause forbids READING an absent validation
# argument, not precomputing from a present one.
_IMPL_POS_OPTION_MAP = (
    "  let mut trainScores := trScores\n"
    "  let mut valScores := vlScores\n"
    "  let mut yT : Targets := Sum.inl yTrain\n"
    "  if isClf then\n"
    "    let ls ← readLabels labels\n"
    "    yT := Sum.inr (← relabelTargets ls yTrain)\n"
    "  let yVpre : Option (Except EarlyStopError Targets) :=\n"
    "    yVal.map (fun codes => targetFor isClf labels codes)\n"
    "  let trScore ← scorer xTrain yT\n"
    "  trainScores := trainScores ++ [trScore]\n"
    "  if useVal then\n"
    "    let yV ← match yVpre with\n"
    "      | some t => t\n"
    "      | none => Except.error EarlyStopError.absentValidationData\n"
    "    let xv ← readValData xVal\n"
    "    let vlScore ← scorer xv yV\n"
    "    valScores := valScores ++ [vlScore]\n"
    "    return { trainScores := trainScores, valScores := valScores,\n"
    "             stop := shouldStop valScores }\n"
    "  return { trainScores := trainScores, valScores := valScores,\n"
    "           stop := shouldStop trainScores }"
)

# POSITIVE 6 (defended class-label precomputation): the TRAINING decode is
# computed before the `isClf` guard, but UNDER `Option.map` and on the table the
# caller actually supplied, so no absent table is read and no stand-in table is
# invented — the Lean analogue of a defensive
# `dec = self.classes_[y.astype(int)] if hasattr(self, "classes_") else None`.
# What is precomputed is the DECODE, `Option (Except … (Array String))`, so the
# decode's own `codeOutOfRange` is still the impl's outcome wherever the contract
# says it is; the case therefore probes the class-label clause without touching the
# decode's domain. Correct, and must verify: the clause forbids READING an absent
# table, not precomputing from the present one. Because the precomputed value is
# the decode rather than the decoded array, the FROZEN tactic body closes it
# verbatim — measured — which is also what distinguishes this reshape from the
# reassociating positives.
_IMPL_POS_LABELS_MAP = (
    "  let mut trainScores := trScores\n"
    "  let mut valScores := vlScores\n"
    "  let decT : Option (Except EarlyStopError (Array String)) :=\n"
    "    labels.map (fun ls => relabelTargets ls yTrain)\n"
    "  let mut yT : Targets := Sum.inl yTrain\n"
    "  if isClf then\n"
    "    let dec ← match decT with\n"
    "      | some d => d\n"
    "      | none => Except.error EarlyStopError.absentClassLabels\n"
    "    yT := Sum.inr dec\n"
    "  let trScore ← scorer xTrain yT\n"
    "  trainScores := trainScores ++ [trScore]\n"
    "  if useVal then\n"
    "    let codes ← readValCodes yVal\n"
    "    let mut yV : Targets := Sum.inl codes\n"
    "    if isClf then\n"
    "      let ls ← readLabels labels\n"
    "      yV := Sum.inr (← relabelTargets ls codes)\n"
    "    let xv ← readValData xVal\n"
    "    let vlScore ← scorer xv yV\n"
    "    valScores := valScores ++ [vlScore]\n"
    "    return { trainScores := trainScores, valScores := valScores,\n"
    "             stop := shouldStop valScores }\n"
    "  return { trainScores := trainScores, valScores := valScores,\n"
    "           stop := shouldStop trainScores }"
)

# GETD-TRAIN-DECODE-HOISTED — `atk_6.lean`, the attack that BROKE the previous
# contract on the fourth axis, machine-checked by the live G-EQ role and recorded
# in this bundle's verdict.md (verifies, axioms `[propext]`, and its faithful patch
# does NOT resolve: 4 PASS_TO_PASS failures). The TRAINING decode is hoisted above the
# `isClf` guard and taken from a DEFAULTED class-label table
# (`relabelTargets (labels.getD #[]) yTrain`), while the guarded `readLabels` stays
# where it is and the precomputed value is consumed only under the guard, where the
# default coincides with the real table. Nothing absent is read, every recorded
# value is gold's, and both scoring calls are the named ones — so none of the three
# earlier lanes can see it. What sees it is the decode's own DOMAIN: a defaulted
# (empty) table paired with real codes is a gather the class-label table has no
# entry for, which the repaired `relabelTargets` reports as
# `codeOutOfRange` — off-guard, where the contract demands a success.
# This is the attack the decode repair closes, and it is exactly the shape the
# previous total decode admitted: `relabelTargets #[] #[12,-3,480,0]` returned
# `#["","","",""]` there (the `Inhabited` default), where numpy raises.
_IMPL_GETD_TRAIN_DECODE_HOISTED = (
    "  let mut trainScores := trScores\n"
    "  let mut valScores := vlScores\n"
    "  let hoistedDecoded ← relabelTargets (labels.getD #[]) yTrain\n"
    "  let mut yT : Targets := Sum.inl yTrain\n"
    "  if isClf then\n"
    "    let _ls ← readLabels labels\n"
    "    yT := Sum.inr hoistedDecoded\n"
    "  let trScore ← scorer xTrain yT\n"
    "  trainScores := trainScores ++ [trScore]\n"
    "  if useVal then\n"
    "    let xv ← readValData xVal\n"
    "    let codes ← readValCodes yVal\n"
    "    let mut yV : Targets := Sum.inl codes\n"
    "    if isClf then\n"
    "      let ls ← readLabels labels\n"
    "      yV := Sum.inr (← relabelTargets ls codes)\n"
    "    let vlScore ← scorer xv yV\n"
    "    valScores := valScores ++ [vlScore]\n"
    "    return { trainScores := trainScores, valScores := valScores,\n"
    "             stop := shouldStop valScores }\n"
    "  return { trainScores := trainScores, valScores := valScores,\n"
    "           stop := shouldStop trainScores }"
)

# GETD-VAL-DECODE-HOISTED — `atk_7.lean`, the SECOND break of the same round and
# the same defect on the validation site, with BOTH conditional arguments
# defaulted: `relabelTargets (labels.getD #[]) (yVal.getD yTrain)` hoisted above
# the `useVal` guard. Verifies against the previous contract (axioms `[propext]`),
# and its faithful patch does not resolve either — the same 4 PASS_TO_PASS
# regressions. Shipped alongside the train-site shape because the repair has to
# reject BOTH shapes the live audit produced: the codes it defaults to are the
# TRAINING codes, so the defaulted table again meets a non-empty code array, and
# hoisting past `useVal` rather than past `isClf` puts the same off-guard decode at
# a different point in the procedure.
_IMPL_GETD_VAL_DECODE_HOISTED = (
    "  let mut trainScores := trScores\n"
    "  let mut valScores := vlScores\n"
    "  let mut yT : Targets := Sum.inl yTrain\n"
    "  if isClf then\n"
    "    let ls ← readLabels labels\n"
    "    yT := Sum.inr (← relabelTargets ls yTrain)\n"
    "  let trScore ← scorer xTrain yT\n"
    "  trainScores := trainScores ++ [trScore]\n"
    "  let hoistedDecoded ← relabelTargets (labels.getD #[]) (yVal.getD yTrain)\n"
    "  if useVal then\n"
    "    let xv ← readValData xVal\n"
    "    let codes ← readValCodes yVal\n"
    "    let mut yV : Targets := Sum.inl codes\n"
    "    if isClf then\n"
    "      yV := Sum.inr hoistedDecoded\n"
    "    let vlScore ← scorer xv yV\n"
    "    valScores := valScores ++ [vlScore]\n"
    "    return { trainScores := trainScores, valScores := valScores,\n"
    "             stop := shouldStop valScores }\n"
    "  return { trainScores := trainScores, valScores := valScores,\n"
    "           stop := shouldStop trainScores }"
)

# POSITIVE 8 (the unbound consult, measured correct): the boundary case of the
# scoring lane, and the one an independent reviewer went looking for. The stand-in
# pair is assembled above the guard AND the scorer application on it is NAMED
# there, in a `let` of type `Except EarlyStopError Score` — but it is not `←`-bound
# until INSIDE the guard, where the `getD` defaults coincide with the real
# arguments. This is `atk_12.lean` from the live G-EQ round of 2026-08-16, the one
# attack of that round's fourteen that VERIFIES. It is a correct echo, and its own
# author said so with the oracle: the faithful patch it shipped defers the call
# (`_hoisted_answer = lambda: self.scorer_(self, _stand_in_X, _stand_in_y)`,
# invoked only inside `if self._use_validation_data:`) and PASSES the three
# PASS_TO_PASS parametrizations that reach this method with
# `validation_fraction=None` (`3 passed, 75 deselected, 1 warning in 399.63s`,
# official instance image). Shipping it as a positive is what makes the reject
# lane's boundary the BIND, not the mention: `weak-val-scorecall-hoisted` and
# `atk_13` bind off-guard and are rejected; this one names the same application and
# must verify, because a named-but-unbound `Except` term is a Python call not yet
# made and the deferring refinement is the faithful one.
# Retyped for the PARTIAL decode: the stand-in target array is now an
# `Except EarlyStopError Targets`, so the stand-in answer binds through it. That
# makes this case carry a second boundary as well, and the one the repair turns on:
# the off-guard DECODE of the defaulted table is *named* here too and this must
# still verify, while the two `weak-getd-*-decode-hoisted` rivals — which `←`-bind
# exactly that decode off the guard — must not. Mentioning a stand-in decode is
# permitted; performing one is not.
_IMPL_POS_UNBOUND_CONSULT = (
    "  let mut trainScores := trScores\n"
    "  let mut valScores := vlScores\n"
    "  let mut yT : Targets := Sum.inl yTrain\n"
    "  if isClf then\n"
    "    let ls ← readLabels labels\n"
    "    yT := Sum.inr (← relabelTargets ls yTrain)\n"
    "  let trScore ← scorer xTrain yT\n"
    "  trainScores := trainScores ++ [trScore]\n"
    "  let standInTargets : Except EarlyStopError Targets :=\n"
    "    if isClf then (relabelTargets (labels.getD #[]) (yVal.getD #[])).map Sum.inr\n"
    "    else Except.ok (Sum.inl (yVal.getD #[]))\n"
    "  let unboundAnswer : Except EarlyStopError Score := do\n"
    "    let t ← standInTargets\n"
    "    scorer (xVal.getD xTrain) t\n"
    "  if useVal then\n"
    "    let _codes ← readValCodes yVal\n"
    "    let _t ← standInTargets\n"
    "    let _xv ← readValData xVal\n"
    "    let vlScore ← unboundAnswer\n"
    "    valScores := valScores ++ [vlScore]\n"
    "    return { trainScores := trainScores, valScores := valScores,\n"
    "             stop := shouldStop valScores }\n"
    "  return { trainScores := trainScores, valScores := valScores,\n"
    "           stop := shouldStop trainScores }"
)

# ADMISSIBILITY ground instance (prepended to the frozen tactic body, which then
# closes the frozen obligation verbatim). Discharges the obligation at the
# smallest F2P-shaped point — a CATEGORICAL estimator with validation data in use
# AND supplied, a two-entry class-label table, both target arrays concrete codes,
# both histories empty — by EVALUATION: the two `have`s reduce `relabelTargets` to
# a literal `Except.ok` array and are then rewritten into the goal, so the
# admission is pinned to the decoded branch the F2P scenario exercises rather than
# left symbolic. No new declaration, axiom, or assumption token; the theorem
# STATEMENT is untouched.
# Two things changed with the decode's partiality. The reductions are `by rfl`, not
# `by decide`: the decode's result type is `Except EarlyStopError (Array String)`,
# which carries no `Decidable` instance for equality, so `decide` fails to
# synthesize one where `rfl` evaluates both sides and closes the goal outright. And
# what is being reduced is now the DISPOSITION as well as the array — each `have`
# says the decode SUCCEEDS on this pair, `.ok` and not `codeOutOfRange`, which is
# the part of the contract a ground instance most needs to pin: the clause is
# `(relabelTargets ls yTrain).bind …`, so an inadmissible reading in which the
# decode always failed would make every categorical clause vacuously satisfiable by
# the error, and this `have` is what rules it out. The `show` therefore restates the
# goal in the contract's own `bind` shape before the rewrite; the rewrite discharges
# both binds and the equation is the recorded triple.
_ADMISS_GROUND = (
    "  have _ground : ∀ (scorer : XData → Targets → Score)\n"
    "      (shouldStop : List Score → Bool) (xT xV : XData),\n"
    "      problem_spec_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop\n"
    "        true true (some #[\"x\", \"y\"])\n"
    "        xT #[0, 1] (some xV) (some #[1, 0]) [] []\n"
    "        (implementation_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop\n"
    "          true true (some #[\"x\", \"y\"])\n"
    "          xT #[0, 1] (some xV) (some #[1, 0]) [] []) := by\n"
    "    intro scorer shouldStop xT xV\n"
    "    have hT : relabelTargets #[\"x\", \"y\"] #[0, 1] = Except.ok #[\"x\", \"y\"] := by rfl\n"
    "    have hV : relabelTargets #[\"x\", \"y\"] #[1, 0] = Except.ok #[\"y\", \"x\"] := by rfl\n"
    "    show implementation_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop\n"
    "        true true (some #[\"x\", \"y\"])\n"
    "        xT #[0, 1] (some xV) (some #[1, 0]) [] []\n"
    "      = (relabelTargets #[\"x\", \"y\"] #[0, 1]).bind (fun yT =>\n"
    "          (relabelTargets #[\"x\", \"y\"] #[1, 0]).bind (fun yV =>\n"
    "            Except.ok ⟨[scorer xT (Sum.inr yT)], [scorer xV (Sum.inr yV)],\n"
    "              shouldStop [scorer xV (Sum.inr yV)]⟩))\n"
    "    rw [hT, hV]\n"
    "    rfl\n"
)


# ---------------------------------------------------------------------------
# Refutation witnesses. Each first RESTATES the spec predicate at one concrete
# input as the explicit `Except` equation it definitionally is — a restatement
# that typechecks against the rival and NOT against gold — then projects the
# disagreeing component. Where the disagreement is a score, the witness
# conditions on the ONE disequality separating the two calls the rival confuses,
# so the assumption is trivially satisfiable (a single disequality on an opaque
# function). Where the disagreement is a frame clause or the ok/error
# disposition, no hypothesis is needed at all.
#
# Every witness that reaches a categorical path states its refutation at a
# LITERAL class-label table (`#["x", "y"]`) and LITERAL codes (`#[0, 1]` on the
# training path, `#[1, 0]` on the validation path), rather than at a symbolic
# `labels`/`yTrain`. That is forced by the decode's PARTIALITY and it is what
# makes these witnesses decide anything: the contract binds the training decode
# FIRST (`(relabelTargets ls yTrain).bind …`), so at a symbolic table the whole
# clause is stuck behind a decode that might be `.error`, and the restatement the
# witness needs — a plain `Except.ok ⟨…⟩` equation — is not what the spec reduces
# to. At the literal table the decode EVALUATES (`#[0,1] ↦ .ok #["x","y"]`,
# `#[1,0] ↦ .ok #["y","x"]`), the `bind` discharges, and the equation is again
# exactly the recorded triple. A literal input is also strictly stronger evidence:
# the refutation now names one input rather than a family, and `#["x", "y"]` with
# codes `#[0, 1]` is the shape of the F2P fixture (50 'x' + 50 'y').
# Two witnesses keep symbolic inputs because their rivals never decode: the
# scoring-call and class-label hoists are both refuted at isClf=false.
# These are written as triple-quoted raw strings rather than in the concatenated
# style used elsewhere in this file, because the literal tables contain the double
# quotes Lean needs and escaping them would obscure what is being asserted.
# ---------------------------------------------------------------------------

# Train-site witness (isClf=true, useVal=false, no validation arguments): the
# classifier's TRAIN history must record the DECODED call, but the rival recorded
# the raw one.
_WIT_PREPATCH = r'''example (scorer : XData → Targets → Score) (shouldStop : List Score → Bool)
    (xTrain : XData) (trScores vlScores : List Score)
    (h : scorer xTrain (Sum.inl #[0, 1])
        ≠ scorer xTrain (Sum.inr #["x", "y"])) :
    ¬ problem_spec_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop
        true false (some #["x", "y"])
        xTrain #[0, 1] none none trScores vlScores
        (implementation_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop
          true false (some #["x", "y"])
          xTrain #[0, 1] none none trScores vlScores) := by
  intro hspec
  have h1 : (Except.ok ⟨trScores ++ [scorer xTrain (Sum.inl #[0, 1])], vlScores,
      shouldStop (trScores ++ [scorer xTrain (Sum.inl #[0, 1])])⟩
        : Except EarlyStopError CheckResult)
      = Except.ok ⟨trScores ++ [scorer xTrain (Sum.inr #["x", "y"])], vlScores,
          shouldStop (trScores ++ [scorer xTrain (Sum.inr #["x", "y"])])⟩ :=
    hspec
  have h2 := congrArg CheckResult.trainScores (Except.ok.inj h1)
  exact h (by simpa using h2)'''

# Regressor-decode witness (isClf=false, useVal=false, no validation arguments):
# the non-classifier's TRAIN history must record the RAW call, but the rival
# decoded it.
_WIT_REGRESSOR = r'''example (scorer : XData → Targets → Score) (shouldStop : List Score → Bool)
    (xTrain : XData) (trScores vlScores : List Score)
    (h : scorer xTrain (Sum.inl #[0, 1])
        ≠ scorer xTrain (Sum.inr #["x", "y"])) :
    ¬ problem_spec_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop
        false false (some #["x", "y"])
        xTrain #[0, 1] none none trScores vlScores
        (implementation_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop
          false false (some #["x", "y"])
          xTrain #[0, 1] none none trScores vlScores) := by
  intro hspec
  have h1 : (Except.ok
      ⟨trScores ++ [scorer xTrain (Sum.inr #["x", "y"])], vlScores,
        shouldStop (trScores ++ [scorer xTrain (Sum.inr #["x", "y"])])⟩
        : Except EarlyStopError CheckResult)
      = Except.ok ⟨trScores ++ [scorer xTrain (Sum.inl #[0, 1])], vlScores,
          shouldStop (trScores ++ [scorer xTrain (Sum.inl #[0, 1])])⟩ :=
    hspec
  have h2 := congrArg CheckResult.trainScores (Except.ok.inj h1)
  exact h (by simpa using h2.symm)'''

# Val-site witness (isClf=true, useVal=true, both validation arguments supplied):
# the classifier's VALIDATION history must record the DECODED call, but the rival
# recorded the raw one on that site.
_WIT_VAL = r'''example (scorer : XData → Targets → Score) (shouldStop : List Score → Bool)
    (xTrain xv : XData) (trScores vlScores : List Score)
    (h : scorer xv (Sum.inl #[1, 0])
        ≠ scorer xv (Sum.inr #["y", "x"])) :
    ¬ problem_spec_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop
        true true (some #["x", "y"])
        xTrain #[0, 1] (some xv) (some #[1, 0]) trScores vlScores
        (implementation_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop
          true true (some #["x", "y"])
          xTrain #[0, 1] (some xv) (some #[1, 0]) trScores vlScores) := by
  intro hspec
  have h1 : (Except.ok
      ⟨trScores ++ [scorer xTrain (Sum.inr #["x", "y"])],
        vlScores ++ [scorer xv (Sum.inl #[1, 0])],
        shouldStop (vlScores ++ [scorer xv (Sum.inl #[1, 0])])⟩
        : Except EarlyStopError CheckResult)
      = Except.ok ⟨trScores ++ [scorer xTrain (Sum.inr #["x", "y"])],
          vlScores ++ [scorer xv (Sum.inr #["y", "x"])],
          shouldStop (vlScores ++ [scorer xv (Sum.inr #["y", "x"])])⟩ :=
    hspec
  have h2 := congrArg CheckResult.valScores (Except.ok.inj h1)
  exact h (by simpa using h2)'''

# Element-level witness (isClf=true, useVal=false, no validation arguments): the
# classifier's TRAIN history must record the call on the FULLY relabeled array,
# but the rival's array differs at position 0. Conditions on the scorer separating
# those two DECODED arrays, so it cannot be discharged by the `Sum` branch alone.
_WIT_FIRST_ELEMENT_RAW = r'''example (scorer : XData → Targets → Score) (shouldStop : List Score → Bool)
    (xTrain : XData) (trScores vlScores : List Score)
    (h : scorer xTrain
          (Sum.inr ((#["x", "y"] : Array String).set! 0
            (toString ((#[0, 1] : Array Int)[0]!))))
        ≠ scorer xTrain (Sum.inr #["x", "y"])) :
    ¬ problem_spec_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop
        true false (some #["x", "y"])
        xTrain #[0, 1] none none trScores vlScores
        (implementation_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop
          true false (some #["x", "y"])
          xTrain #[0, 1] none none trScores vlScores) := by
  intro hspec
  have h1 : (Except.ok
      ⟨trScores ++ [scorer xTrain
          (Sum.inr ((#["x", "y"] : Array String).set! 0
            (toString ((#[0, 1] : Array Int)[0]!))))],
        vlScores,
        shouldStop (trScores ++ [scorer xTrain
          (Sum.inr ((#["x", "y"] : Array String).set! 0
            (toString ((#[0, 1] : Array Int)[0]!))))])⟩
        : Except EarlyStopError CheckResult)
      = Except.ok ⟨trScores ++ [scorer xTrain (Sum.inr #["x", "y"])],
          vlScores,
          shouldStop (trScores ++ [scorer xTrain (Sum.inr #["x", "y"])])⟩ :=
    hspec
  have h2 := congrArg CheckResult.trainScores (Except.ok.inj h1)
  exact h (by simpa using h2)'''

# Frame witness (isClf=true, useVal=false, both validation arguments SUPPLIED):
# UNCONDITIONAL. (C_no) requires the validation history to come back unchanged,
# and the rival returns it extended by one element; a list cannot equal itself
# with an element appended, so no hypothesis about the opaque scorer is needed and
# there is no consistency probe to satisfy. Taken at supplied arguments so that
# the ok/error disposition is not what does the refuting.
_WIT_VAL_FRAME = r'''example (scorer : XData → Targets → Score) (shouldStop : List Score → Bool)
    (xTrain xv : XData) (trScores vlScores : List Score) :
    ¬ problem_spec_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop
        true false (some #["x", "y"])
        xTrain #[0, 1] (some xv) (some #[1, 0]) trScores vlScores
        (implementation_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop
          true false (some #["x", "y"])
          xTrain #[0, 1] (some xv) (some #[1, 0]) trScores vlScores) := by
  intro hspec
  have h1 : (Except.ok
      ⟨trScores ++ [scorer xTrain (Sum.inr #["x", "y"])],
        vlScores ++ [scorer xv (Sum.inr #["y", "x"])],
        shouldStop (trScores ++ [scorer xTrain (Sum.inr #["x", "y"])])⟩
        : Except EarlyStopError CheckResult)
      = Except.ok ⟨trScores ++ [scorer xTrain (Sum.inr #["x", "y"])],
          vlScores,
          shouldStop (trScores ++ [scorer xTrain (Sum.inr #["x", "y"])])⟩ :=
    hspec
  have h2 := congrArg CheckResult.valScores (Except.ok.inj h1)
  simpa using h2'''

# Stop-decision witness (isClf=true, useVal=true, both validation arguments
# supplied): (C_val) requires the decision to be the stopping rule applied to the
# extended VALIDATION history, but the rival applies it to the extended TRAINING
# history. Conditions on `shouldStop` distinguishing those two histories — the
# single disequality that separates the two calls, on the other opaque
# function-valued input.
_WIT_STOP_USES_TRAIN = r'''example (scorer : XData → Targets → Score) (shouldStop : List Score → Bool)
    (xTrain xv : XData) (trScores vlScores : List Score)
    (h : shouldStop (trScores ++ [scorer xTrain (Sum.inr #["x", "y"])])
        ≠ shouldStop (vlScores ++ [scorer xv (Sum.inr #["y", "x"])])) :
    ¬ problem_spec_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop
        true true (some #["x", "y"])
        xTrain #[0, 1] (some xv) (some #[1, 0]) trScores vlScores
        (implementation_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop
          true true (some #["x", "y"])
          xTrain #[0, 1] (some xv) (some #[1, 0]) trScores vlScores) := by
  intro hspec
  have h1 : (Except.ok
      ⟨trScores ++ [scorer xTrain (Sum.inr #["x", "y"])],
        vlScores ++ [scorer xv (Sum.inr #["y", "x"])],
        shouldStop (trScores ++ [scorer xTrain (Sum.inr #["x", "y"])])⟩
        : Except EarlyStopError CheckResult)
      = Except.ok ⟨trScores ++ [scorer xTrain (Sum.inr #["x", "y"])],
          vlScores ++ [scorer xv (Sum.inr #["y", "x"])],
          shouldStop (vlScores ++ [scorer xv (Sum.inr #["y", "x"])])⟩ :=
    hspec
  exact h (congrArg CheckResult.stop (Except.ok.inj h1))'''

# Stop-no-val witness (isClf=true, useVal=false, no validation arguments): (C_no)
# requires the decision to be the stopping rule applied to the EXTENDED training
# history, but the rival applies it to the history as handed in. Conditions on
# `shouldStop` separating those two lists — one disequality on the other opaque
# function-valued input.
_WIT_STOP_NO_VAL = r'''example (scorer : XData → Targets → Score) (shouldStop : List Score → Bool)
    (xTrain : XData) (trScores vlScores : List Score)
    (h : shouldStop trScores
        ≠ shouldStop (trScores ++ [scorer xTrain (Sum.inr #["x", "y"])])) :
    ¬ problem_spec_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop
        true false (some #["x", "y"])
        xTrain #[0, 1] none none trScores vlScores
        (implementation_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop
          true false (some #["x", "y"])
          xTrain #[0, 1] none none trScores vlScores) := by
  intro hspec
  have h1 : (Except.ok
      ⟨trScores ++ [scorer xTrain (Sum.inr #["x", "y"])], vlScores,
        shouldStop trScores⟩ : Except EarlyStopError CheckResult)
      = Except.ok ⟨trScores ++ [scorer xTrain (Sum.inr #["x", "y"])],
          vlScores,
          shouldStop (trScores ++ [scorer xTrain (Sum.inr #["x", "y"])])⟩ :=
    hspec
  exact h (congrArg CheckResult.stop (Except.ok.inj h1))'''

# Hoisted-read witness (isClf=true, useVal=false, BOTH validation arguments
# absent): UNCONDITIONAL. (C_no) requires a SUCCESS on the no-validation path, and
# the rival — having read the absent validation arguments before the branch —
# returns `Except.error`. `Except.error ≠ Except.ok`, so no assumption about the
# opaque carriers is needed. This is the input point the previous contract could
# not see.
_WIT_VAL_READ_HOISTED = r'''example (scorer : XData → Targets → Score) (shouldStop : List Score → Bool)
    (xTrain : XData) (trScores vlScores : List Score) :
    ¬ problem_spec_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop
        true false (some #["x", "y"])
        xTrain #[0, 1] none none trScores vlScores
        (implementation_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop
          true false (some #["x", "y"])
          xTrain #[0, 1] none none trScores vlScores) := by
  intro hspec
  have h1 : (Except.error EarlyStopError.absentValidationData
        : Except EarlyStopError CheckResult)
      = Except.ok ⟨trScores ++ [scorer xTrain (Sum.inr #["x", "y"])],
          vlScores,
          shouldStop (trScores ++ [scorer xTrain (Sum.inr #["x", "y"])])⟩ :=
    hspec
  exact Except.noConfusion h1'''

# Hoisted-score witness (isClf=true, useVal=false, the design matrix SUPPLIED and
# the targets absent): UNCONDITIONAL, and at a different presence pattern from the
# hoisted-read witness — the rival gets past the design-matrix read and fails on
# the target read, and (C_no) still demands a success.
_WIT_VAL_SCORE_HOISTED = r'''example (scorer : XData → Targets → Score) (shouldStop : List Score → Bool)
    (xTrain xv : XData) (trScores vlScores : List Score) :
    ¬ problem_spec_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop
        true false (some #["x", "y"])
        xTrain #[0, 1] (some xv) none trScores vlScores
        (implementation_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop
          true false (some #["x", "y"])
          xTrain #[0, 1] (some xv) none trScores vlScores) := by
  intro hspec
  have h1 : (Except.error EarlyStopError.absentValidationData
        : Except EarlyStopError CheckResult)
      = Except.ok ⟨trScores ++ [scorer xTrain (Sum.inr #["x", "y"])],
          vlScores,
          shouldStop (trScores ++ [scorer xTrain (Sum.inr #["x", "y"])])⟩ :=
    hspec
  exact Except.noConfusion h1'''


# Hoisted-scoring-call witness (isClf=false, NO class-label table, useVal=false,
# BOTH validation arguments absent, one training code): UNCONDITIONAL, and the
# only witness that instantiates the scoring function as a PARTIAL one. It
# refuses exactly one pair — the one whose target array is empty, which is the
# stand-in the rival assembles from the absent validation targets — and answers
# every other pair with the opaque score. (C_no) then demands the success built
# from the answer about the TRAINING pair `Sum.inl #[0]`, which is not the
# refused pair, while the rival propagates the refusal it provoked. This is the
# model of the measured `ValueError: Found input variables with inconsistent
# numbers of samples: [0, 50]`: a scoring function handed 50 rows of design
# matrix and 0 targets.
_WIT_VAL_SCORECALL_HOISTED = (
    "example (scorer : XData → Targets → Score) (shouldStop : List Score → Bool)\n"
    "    (xTrain : XData) (trScores vlScores : List Score) :\n"
    "    ¬ problem_spec_scoreEarlyStop\n"
    "        (fun x t => if t = (Sum.inl (#[] : Array Int) : Targets) then\n"
    "            Except.error EarlyStopError.scoringRefused else .ok (scorer x t))\n"
    "        shouldStop false false none xTrain #[0] none none trScores vlScores\n"
    "        (implementation_scoreEarlyStop\n"
    "          (fun x t => if t = (Sum.inl (#[] : Array Int) : Targets) then\n"
    "              Except.error EarlyStopError.scoringRefused else .ok (scorer x t))\n"
    "          shouldStop false false none xTrain #[0] none none trScores vlScores) := by\n"
    "  intro hspec\n"
    "  have h1 : (Except.error EarlyStopError.scoringRefused\n"
    "        : Except EarlyStopError CheckResult)\n"
    "      = Except.ok ⟨trScores ++ [scorer xTrain (Sum.inl #[0])], vlScores,\n"
    "          shouldStop (trScores ++ [scorer xTrain (Sum.inl #[0])])⟩ :=\n"
    "    hspec\n"
    "  exact Except.noConfusion h1"
)
# Hoisted-class-label witness (isClf=false, NO class-label table, useVal=false,
# no validation arguments): UNCONDITIONAL. A non-categorical estimator's call
# must SUCCEED and record the raw-code score, and the rival — having read the
# absent table before the branch — returns `Except.error`.
# `Except.error ≠ Except.ok`, so no assumption about the opaque carriers is
# needed. This is the input point the TOTAL-`labels` interface could not express.
_WIT_LABELS_HOISTED = (
    "example (scorer : XData → Targets → Score) (shouldStop : List Score → Bool)\n"
    "    (xTrain : XData) (yTrain : Array Int)\n"
    "    (trScores vlScores : List Score) :\n"
    "    ¬ problem_spec_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop\n"
    "        false false none\n"
    "        xTrain yTrain none none trScores vlScores\n"
    "        (implementation_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop\n"
    "          false false none\n"
    "          xTrain yTrain none none trScores vlScores) := by\n"
    "  intro hspec\n"
    "  have h1 : (Except.error EarlyStopError.absentClassLabels\n"
    "        : Except EarlyStopError CheckResult)\n"
    "      = Except.ok ⟨trScores ++ [scorer xTrain (Sum.inl yTrain)], vlScores,\n"
    "          shouldStop (trScores ++ [scorer xTrain (Sum.inl yTrain)])⟩ :=\n"
    "    hspec\n"
    "  exact Except.noConfusion h1"
)

# Hoisted-DECODE witness (isClf=false, NO class-label table, useVal=false, no
# validation arguments, one training code): UNCONDITIONAL, and the input point the
# TOTAL decode could not express at all. A non-categorical estimator's call must
# SUCCEED with the raw-code score; a rival that runs the decode off the branch —
# on the DEFAULTED empty table, which has an entry for no code whatsoever —
# provokes the decode's own `codeOutOfRange` and propagates it.
# `Except.error ≠ Except.ok`, so no assumption about the opaque carriers is needed.
# Under the previous TOTAL decode this same rival returned the very success the
# contract demands (the empty table simply gathered `#[""]`), which is exactly why
# it verified; the `codeOutOfRange` failure is what makes the off-branch decode
# observable. Serves both hoist sites: the training decode reaches the defaulted
# table before the guard, and the validation decode reaches it after the training
# score, so both arrive at this same error on this same input.
_WIT_GETD_DECODE_HOISTED = r'''example (scorer : XData → Targets → Score) (shouldStop : List Score → Bool)
    (xTrain : XData) (trScores vlScores : List Score) :
    ¬ problem_spec_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop
        false false none
        xTrain #[0] none none trScores vlScores
        (implementation_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop
          false false none
          xTrain #[0] none none trScores vlScores) := by
  intro hspec
  have h1 : (Except.error EarlyStopError.codeOutOfRange
        : Except EarlyStopError CheckResult)
      = Except.ok ⟨trScores ++ [scorer xTrain (Sum.inl #[0])], vlScores,
          shouldStop (trScores ++ [scorer xTrain (Sum.inl #[0])])⟩ :=
    hspec
  exact Except.noConfusion h1'''


# Order-swapped witness (isClf=true, a two-entry class-label table, useVal=true,
# the design matrix ABSENT and the target codes SUPPLIED but OUT OF RANGE):
# UNCONDITIONAL, and the only witness that separates two ERROR values from each
# other. On this input the repaired `(C_err)` arm reads the codes, decodes them,
# and reports the gather's own `codeOutOfRange` — the design matrix is never
# reached — while the rival, having read the design matrix first, reports
# `absentValidationData`. Two distinct constructors of `EarlyStopError`, so no
# assumption about the opaque carriers is needed. This is the exact point the live
# G-PANEL auditor's grid disagreed on (`isClf=true, useVal=true, xVal=none,
# yVal=some <out-of-range code>`), stated as one input: `#[7]` against the
# two-entry table `#["x", "y"]`, which numpy answers with `IndexError: index 7 is
# out of bounds for axis 0 with size 2`.
_WIT_VAL_ORDER_SWAPPED = r'''example (scorer : XData → Targets → Score) (shouldStop : List Score → Bool)
    (xTrain : XData) (trScores vlScores : List Score) :
    ¬ problem_spec_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop
        true true (some #["x", "y"])
        xTrain #[0, 1] none (some #[7]) trScores vlScores
        (implementation_scoreEarlyStop (fun x t => .ok (scorer x t)) shouldStop
          true true (some #["x", "y"])
          xTrain #[0, 1] none (some #[7]) trScores vlScores) := by
  intro hspec
  have h1 : (Except.error EarlyStopError.absentValidationData
        : Except EarlyStopError CheckResult)
      = Except.error EarlyStopError.codeOutOfRange :=
    hspec
  exact Except.noConfusion h1 (fun h => EarlyStopError.noConfusion h)'''


SPEC_TESTS = [
    # =====================================================================
    # ADMISSIBILITY (must VERIFY) — the obligation is SATISFIABLE at exactly an
    # F2P-shaped input, discharged there by evaluation as a `have` before the
    # frozen obligation is closed verbatim. The total-carrier analogue of
    # PRECOND-TOO-STRONG: if the modeled behavior could not be admitted at a
    # normal F2P-shaped point, the contract would be unsatisfiable where it most
    # matters.
    # =====================================================================
    {
        "id": "admiss-ground-f2p",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _PROOF_INTRO, _ADMISS_GROUND + _PROOF_INTRO),
        "rationale": (
            "the obligation is discharged at the smallest F2P-shaped input — a "
            "CATEGORICAL estimator (isClf=true) with validation data in use "
            "(useVal=true) and both validation arguments SUPPLIED "
            "(`some xV` / `some #[1, 0]`), a two-entry class-label table "
            "`#[\"x\", \"y\"]`, both target arrays given as concrete codes "
            "(`#[0, 1]` on the training path, `#[1, 0]` on the validation path) "
            "and both histories empty — by EVALUATION, as a `have`, after which "
            "the frozen obligation is closed by the unchanged frozen tactic body. "
            "The two `rfl` steps reduce the relabeling to `Except.ok` of a "
            "literal array (`relabelTargets #[\"x\",\"y\"] #[0,1] = "
            ".ok #[\"x\",\"y\"]`, `relabelTargets #[\"x\",\"y\"] #[1,0] = "
            ".ok #[\"y\",\"x\"]` — `decide` is unavailable on the partial decode, "
            "which carries no `DecidableEq`) and are "
            "REWRITTEN into the stated goal, so the admission is pinned to the "
            "decoded branch the F2P scenario exercises rather than restating the "
            "obligation symbolically — measured load-bearing: the same `have` "
            "FAILS (exit 1) when grafted onto the weak-prepatch-undecoded and "
            "weak-first-element-raw rivals, so it is not a decoration that would "
            "read the same against a wrong impl. Must verify; else the modeled "
            "behavior is unsatisfiable at exactly a normal F2P-shaped point, the "
            "total-carrier analogue of PRECOND-TOO-STRONG. Nothing is assumed: no "
            "new declaration, axiom or assumption token, the theorem STATEMENT is "
            "byte-identical, and the ground instance is a `have` prepended inside "
            "the existing tactic body."
        ),
    },

    # =====================================================================
    # SOUNDNESS positives (must VERIFY) — structurally different but CORRECT
    # impls. If a faithful correct impl cannot satisfy the frozen obligation the
    # spec is SPEC-TOO-STRONG. The theorem STATEMENT is byte-identical; only the
    # impl body changes. No helper lemma, axiom, or assumption token is
    # introduced.
    # =====================================================================
    {
        "id": "pos-targetfor-delegate",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_IMPL_POS_TARGETFOR, _proof_reassoc()),
        "rationale": (
            "a correct reshape that computes the scoring argument once through "
            "the frozen `targetFor` helper (dropping the mutable two-step guard) "
            "must satisfy (C_no)/(C_val)/(C_err); if it cannot, the spec is "
            "over-fit to the frozen impl's mutable-if spelling => "
            "SPEC-TOO-STRONG. The validation arguments are still read only inside "
            "the guard, so the disposition clauses are met. Because `targetFor` "
            "returns the DECODED ARRAY inside the same `Except` the decode "
            "produces, this reshape binds `(relabelTargets … ).map Sum.inr` where "
            "the contract binds `relabelTargets …` itself, and the two differ by "
            "one monad-law step that `rfl` cannot perform on a decode stuck under "
            "the opaque table; the step is supplied in the (editable) proof region "
            "as a `have`. No new declaration, axiom, or assumption token, and the "
            "theorem STATEMENT is byte-identical."
        ),
    },
    {
        "id": "pos-inline-ite",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(
            _IMPL_POS_INLINE,
            _proof_reassoc("if_true", "readLabels", "Except.bind")),
        "rationale": (
            "a correct reshape that inlines the selection as "
            "`if isClf then readLabels labels >>= fun ls => "
            "(relabelTargets ls yTrain).map Sum.inr else .ok (Sum.inl yTrain)` — "
            "definitionally the frozen `targetFor`, but written with the table read "
            "and the decode threaded by hand rather than delegated. Must verify; "
            "else the spec is over-fit to the helper-application spelling => "
            "SPEC-TOO-STRONG. Its proof needs the same monad-law step as the "
            "delegating positive plus the reductions its own spelling leaves in the "
            "way (the elaborated `let ←` guard, `readLabels`, `Except.bind`); all of "
            "that is inside the (editable) proof region. The theorem STATEMENT is "
            "byte-identical and no new declaration/axiom is introduced."
        ),
    },
    {
        "id": "pos-match-isclf",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_IMPL_POS_MATCH, _proof_reassoc()),
        "rationale": (
            "a correct reshape that performs the selection by "
            "`match isClf, labels with` rather than by `if`: the two other selector "
            "positives both keep an `if`-shaped selector (one behind the "
            "`targetFor` helper, one inline), so neither showed the spec accepts a "
            "DIFFERENT elimination form for the same Bool. `match` on a `Bool` "
            "reduces by the same `casesOn`, so only the one monad-law step the "
            "`.map Sum.inr` shape needs is left to supply, inside the (editable) "
            "proof region. Must verify; else the spec is over-fit to the `ite` "
            "spelling => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-record-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_IMPL_POS_RECORD_DIRECT, _proof_reassoc()),
        "rationale": (
            "a correct reshape that abandons the mutable accumulators altogether: "
            "each extended history is a single `let`-bound expression, named once "
            "and reused for the stop decision. The furthest reshape from the "
            "frozen `let mut` / imperative-`do` shape that is still a faithful "
            "skeleton — the selector positives all retain the mutable "
            "accumulators and only move the target selection, so none probed "
            "whether the spec tolerates a different STATE shape. Must verify; "
            "else the spec is over-fit to the mutable-accumulator spelling => "
            "SPEC-TOO-STRONG. It reaches the decode through `targetFor`, so its "
            "proof carries the same monad-law step as the delegating positive and "
            "nothing else."
        ),
    },
    {
        "id": "pos-option-map-precompute",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(
            _IMPL_POS_OPTION_MAP, _proof_reassoc("if_true", "Option.map")),
        "rationale": (
            "the SPEC-TOO-STRONG probe for the disposition clauses, and the one "
            "that fixes their scope. The decoded validation targets are computed "
            "BEFORE the `useVal` branch, but UNDER `Option.map`, so an ABSENT "
            "argument is never read — the Lean analogue of the defensive "
            "`y_val = self.classes_[y_val.astype(int)] if y_val is not None else "
            "None`, which is a correct implementation of the real method (it does "
            "not raise on the no-validation path, and it hands the scorer exactly "
            "the decoded labels when validation data is in use). Must verify. If "
            "it did not, (C_no) would be forbidding PRECOMPUTATION rather than "
            "forbidding READING AN ABSENT ARGUMENT, which is not what the "
            "repository requires => SPEC-TOO-STRONG. Paired with "
            "weak-val-read-hoisted, which is the same precomputation WITHOUT the "
            "`Option` guard: the two together pin the clause to exactly the "
            "distinction the repository draws. The precomputed value is now an "
            "`Except` (the decode is partial), and it stays under the `Option`, so "
            "on the no-validation path no decode is attempted at all — while on the "
            "path that scores, a decode failure is still the reported outcome."
        ),
    },

    {
        "id": "pos-labels-map-precompute",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_IMPL_POS_LABELS_MAP),
        "rationale": (
            "the SPEC-TOO-STRONG probe for the CLASS-LABEL-TABLE disposition "
            "clause, and the one that fixes its scope. The decoded training "
            "targets are computed BEFORE the `isClf` guard, but UNDER "
            "`Option.map`, so an ABSENT table is never read — the Lean analogue "
            "of a defensive `dec = self.classes_[y.astype(int)] if "
            "hasattr(self, 'classes_') else None`, which is a correct "
            "implementation of the real method (it does not raise on a "
            "non-categorical estimator, and it hands the scorer exactly the "
            "decoded labels for a categorical one). Must verify. If it did not, "
            "the first clause would be forbidding PRECOMPUTATION rather than "
            "forbidding READING AN ABSENT TABLE, which is not what the "
            "repository requires => SPEC-TOO-STRONG. Paired with "
            "weak-labels-hoisted, which is the same precomputation WITHOUT the "
            "`Option` guard: the two together pin the clause to exactly the "
            "distinction the repository draws. What is precomputed is the DECODE "
            "itself — an `Except` under the `Option`, i.e. the shape the contract "
            "binds — so this is the one positive whose proof region is the FROZEN "
            "tactic body verbatim, and the measurement that the frozen body is not "
            "brittle: a precomputing reshape can still close it unchanged."
        ),
    },

    {
        "id": "pos-unbound-consult",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_IMPL_POS_UNBOUND_CONSULT, _PROOF_REASSOC_BIND),
        "refinement": (
            "`atk_12.lean` from the fourteen-attack G-EQ round of 2026-08-16, and "
            "the ONE attack of that round that verifies. It NAMES the scorer application "
            "on the `getD` stand-in pair above the guard, in a `let` of type "
            "`Except EarlyStopError Score`, and `←`-binds it only inside the "
            "guard, where the defaults coincide with the real arguments. Its "
            "author shipped the faithful patch itself and it RESOLVES: "
            "`_hoisted_answer = lambda: self.scorer_(self, _stand_in_X, "
            "_stand_in_y)` called only under "
            "`if self._use_validation_data:` PASSES the three PASS_TO_PASS "
            "parametrizations that reach this method with "
            "`validation_fraction=None` (`3 passed, 75 deselected, 1 warning in "
            "399.63s`, official instance image, measured 2026-08-16 after the "
            "scoring clause landed). An eager Python call in that position is NOT "
            "a refinement of this Lean impl: under `useVal = false` the impl "
            "returns `.ok`, and a raising call does not refine a normal return."
        ),
        "rationale": (
            "The boundary control of the scoring lane, and the only one that "
            "distinguishes the CONSULT from the MENTION. The reject rivals "
            "`weak-val-scorecall-hoisted` (and the reviewer's `atk_13`, the same "
            "shape with the bind above the guard) are rejected because they "
            "`←`-bind the stand-in answer off-guard, so their outcome is that "
            "answer; this positive names the identical application and must "
            "verify. If it did NOT verify, the clause would be forbidding the "
            "mention of a term rather than the making of a call — "
            "SPEC-TOO-STRONG, and unfaithful, since Lean's `let` on a pure "
            "`Except` value has no Python counterpart that raises. Measured "
            "correct on the resolve side by the adversary that authored it, which "
            "is the strongest form this control can take. It is also the case that "
            "keeps the DECODE lane from overshooting: it names the defaulted "
            "off-guard gather that the two `weak-getd-*-decode-hoisted` rivals "
            "PERFORM, so the boundary the repaired contract draws is the "
            "performance of the stand-in decode, not its mention."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals (must be REJECTED). Each carries (a) the
    # refinement argument that its faithful real patch would NOT resolve the F2P,
    # so a verifying rival is a true verify-does-not-imply-resolve break rather
    # than an artifact, and (b) a refutation witness pinning the violation at one
    # described input.
    # =====================================================================
    {
        "id": "weak-getd-train-decode-hoisted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_GETD_TRAIN_DECODE_HOISTED),
        "refinement": (
            "`atk_6.lean`, the recorded G-EQ BREAK on this cell: the TRAINING "
            "decode is performed above the `isClf` guard on the DEFAULTED "
            "class-label table (`relabelTargets (labels.getD #[]) yTrain`), the "
            "guarded `readLabels` is kept, and the precomputed value is consumed "
            "only inside the guard where the default coincides with the real table. "
            "Its faithful patch hoists "
            "`getattr(self, 'classes_', np.array([], dtype=object))"
            "[y_small_train.astype(int)]` above `if is_classifier(self):` — the same "
            "`getattr` idiom the bundle's own cases use — and does NOT resolve: "
            "`resolved=False, completed=True, F2P 1/1, P2P 59 success / 4 FAILURE, "
            "253.1s`, 'patch did not resolve in 1 attempts (consistent - not "
            "flaky)', against the gold control's `resolved=True, F2P 1/1, P2P "
            "63/63, 231.7s` in the same image and session. The four failures are "
            "exactly the regressor parametrizations of "
            "`test_early_stopping_regression` that reach this method "
            "(`[neg_mean_squared_error-0.1-5-1e-07]`, "
            "`[neg_mean_squared_error-None-5-0.1]`, `[None-0.1-5-1e-07]`, "
            "`[None-None-5-0.1]`), all four in this instance's 63-entry "
            "PASS_TO_PASS list. MECHANISM: on a HistGradientBoostingRegressor "
            "`getattr(self, 'classes_', np.array([]))` is the EMPTY array while "
            "`y_small_train` holds real-valued targets, so `.astype(int)` gives "
            "e.g. `[12,-3,480,0]` and the gather indexes a size-0 axis — "
            "`IndexError: index 12 is out of bounds for axis 0 with size 0`."
        ),
        "rationale": (
            "This is the rival the repair closes, and the case that makes the "
            "decode's PARTIALITY load-bearing. Under the previous TOTAL decode this "
            "impl VERIFIED (axioms `[propext]`) while its patch crashed, because "
            "`relabelTargets #[] #[12,-3,480,0]` returned `#[\"\",\"\",\"\",\"\"]` "
            "where numpy raises: no clause about reads, recorded scores or scoring "
            "calls could see it, since it reads nothing absent and makes only the "
            "two named calls. With the gather's domain modeled, the same hoist is "
            "the reported `codeOutOfRange` on every input whose defaulted table "
            "cannot answer for the training codes, and the first clause's demand "
            "for a SUCCESS refutes it. Must be rejected; a verifying rival here is "
            "the recorded verify-does-not-imply-resolve break itself."
        ),
        "witness": _WIT_GETD_DECODE_HOISTED,
    },
    {
        "id": "weak-getd-val-decode-hoisted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_GETD_VAL_DECODE_HOISTED),
        "refinement": (
            "`atk_7.lean`, the second recorded break of the same round and the "
            "same gap at the other site, with BOTH conditional arguments defaulted: "
            "`relabelTargets (labels.getD #[]) (yVal.getD yTrain)` performed above "
            "the `useVal` guard and consumed only inside it. Its faithful patch "
            "does NOT resolve either: `resolved=False, completed=True, F2P 1/1, "
            "P2P 59 success / 4 FAILURE, 70.3s`, 'consistent - not flaky', the "
            "IDENTICAL four `test_early_stopping_regression` parametrizations, "
            "against the same gold control (`63/63, 231.7s`). Both attacks still "
            "PASS the FAIL_TO_PASS, so the break is a P2P regression on regressors "
            "rather than a lost fix. This case is the CONVERSION of the retired "
            "positive `pos-getd-decode-precompute`, which shipped this very "
            "construct with the stand-in codes defaulted to `#[]` instead of "
            "`yTrain`; that positive's oracle record (`3 passed, 75 deselected, "
            "1 warning in 250.70s`) was measured with 75 tests DESELECTED — among "
            "them the four regressor parametrizations that fail here — so it "
            "certified the construct only on the inputs where the defaulted table "
            "meets an EMPTY code array, which every table can answer for. The "
            "full-suite measurement of the same construct is this 59/4."
        ),
        "rationale": (
            "The site twin of weak-getd-train-decode-hoisted, kept as its own case "
            "because the two sites fail through different clauses — the training "
            "hoist is refuted by the first clause's decode, this one by the "
            "validation clause — and because the corpus measured them separately "
            "(253.1s and 70.3s runs, same four failures). It is also the case that "
            "records the decision on the retired positive: the previous contract "
            "PERMITTED this shape by argument ('the clause forbids reading an "
            "absent table, not precomputing from a present one'), and shipping it "
            "as required-to-verify is what made the break unreachable by the "
            "battery. The repaired contract rejects it while still admitting "
            "pos-unbound-consult, which names the identical defaulted gather "
            "without performing it, and pos-labels-map-precompute / "
            "pos-option-map-precompute, which precompute the decode under an "
            "`Option` so the gather is on the table that exists — so the too-strong "
            "side keeps three controls, two of them with their own oracle records."
        ),
        "witness": _WIT_GETD_DECODE_HOISTED,
    },
    {
        "id": "weak-prepatch-undecoded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_PREPATCH),
        "refinement": (
            "this is the pre-fix behavior: the classifier path forwards the raw "
            "integer codes to the scoring function instead of the decoded class "
            "labels. Its faithful real patch is the UNPATCHED early-stopping "
            "step, which hands integer-coded targets to a scorer whose "
            "predictions are original-domain class labels — exactly the type "
            "mismatch the issue reports ('<' not supported between 'str' and "
            "'float'). The F2P test_string_target_early_stopping then raises and "
            "FAILS; it does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause (C_no): at isClf=true the training history must "
            "record scorer applied to the DECODED targets — `Sum.inr` of the "
            "array `relabelTargets ls yTrain` gathers, which at the witness's "
            "literal table is `Sum.inr #[\"x\", \"y\"]` — but the rival records the "
            "raw `Sum.inl yTrain`. Whenever the scorer distinguishes the two "
            "arguments the recorded score differs from the spec's, so (C_no) "
            "fails. If it verified => SPEC-TOO-WEAK (the spec would not force "
            "decoding on the classifier path)."
        ),
        "witness": _WIT_PREPATCH,
    },
    {
        "id": "weak-regressor-decode",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_REGRESSOR_DECODE),
        "refinement": (
            "passthrough-clause attack: the re-encoding is applied "
            "UNCONDITIONALLY (the classifier guard is dropped), so a "
            "non-categorical estimator's raw targets are decoded too. Its "
            "faithful real patch drops the categorical guard and always gathers "
            "through the class-label table; a non-categorical estimator never "
            "builds that table, so the unguarded gather raises during early "
            "stopping and the non-categorical early-stopping regression tests "
            "FAIL. It does NOT resolve. (Those tests are P2P for this instance, "
            "so the break is observed by the harness.)"
        ),
        "rationale": (
            "REJECT from clause (C_no) at isClf=false: the training history must "
            "record scorer applied to the RAW codes `Sum.inl yTrain`, but the "
            "rival records the decoded `Sum.inr` of what `relabelTargets ls "
            "yTrain` gathers (`Sum.inr #[\"x\", \"y\"]` at the witness's table). "
            "Refuted with isClf=false — varying that binder off the `true` value "
            "the other train-site rivals use — so the spec pins BOTH selections "
            "of `targetFor`. If it verified => SPEC-TOO-WEAK."
        ),
        "witness": _WIT_REGRESSOR,
    },
    {
        "id": "weak-val-undecoded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_VAL_UNDECODED),
        "refinement": (
            "one-site partial-domain: the training path is decoded correctly but "
            "the validation path forwards raw codes. Its faithful real patch "
            "re-encodes only the training target and leaves the validation target "
            "integer-coded; when validation data is in use the validation score "
            "is then computed on integer y_true against original-label y_pred, so "
            "the same str-vs-float comparison raises on the validation split and "
            "test_string_target_early_stopping FAILS. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause (C_val) at isClf=true, useVal=true, both "
            "validation arguments supplied: the validation history must record "
            "scorer applied to the DECODED validation targets — `Sum.inr` of what "
            "`relabelTargets ls yv` gathers, `Sum.inr #[\"y\", \"x\"]` at the "
            "witness's table and codes — but the rival records the raw "
            "`Sum.inl yv`. Refuted at useVal=true with the arguments present (the "
            "train-site rivals use useVal=false), exercising the validation "
            "branch and confirming the two scoring sites are pinned "
            "INDEPENDENTLY. If it verified => SPEC-TOO-WEAK (the val site would "
            "be unconstrained)."
        ),
        "witness": _WIT_VAL,
    },
    {
        "id": "weak-first-element-raw",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_FIRST_ELEMENT_RAW),
        "refinement": (
            "element-level sub-domain miss (the literal nagini "
            "`partial-domain-first-undecoded` argument): the categorical path DOES "
            "re-encode, and every code is mapped back through the class-label "
            "table EXCEPT the one at position 0, which keeps its raw code. Its "
            "faithful real patch re-encodes a slice that omits the first sample "
            "and reassembles it (an off-by-one in the gather). The scored target's "
            "element 0 is then still an integer code while the estimator's own "
            "predictions for that sample are original-domain class values, so the "
            "same str-vs-float comparison the issue reports "
            "(\"'<' not supported between instances of 'str' and 'float'\") raises "
            "on that one sample and the early-stopping F2P FAILS. It does NOT "
            "resolve. (The issue's fixture is 50 'x' + 50 'y', so element 0 is a "
            "real string label and the divergence is observable.)"
        ),
        "rationale": (
            "REJECT from clause (C_no) at isClf=true: the training history must "
            "record scorer applied to `Sum.inr` of what `relabelTargets ls yTrain` "
            "gathers — the array in which EVERY position is the code's class-label-table "
            "entry — but the rival records the call on an array differing at "
            "position 0. This is the only rival that stays INSIDE the `Sum.inr` "
            "branch, so it is what pins `relabelTargets` as a genuine element-wise "
            "gather; the whole-array rivals swap the `Sum` constructor wholesale "
            "and would all be satisfied by any impl that merely took the right "
            "branch. If it verified => SPEC-TOO-WEAK (the spec would constrain "
            "which branch is taken but not what the branch computes)."
        ),
        "witness": _WIT_FIRST_ELEMENT_RAW,
    },
    {
        "id": "weak-val-frame-extended",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_VAL_FRAME_EXTENDED),
        "refinement": (
            "FRAME attack (spec_guide §0.5): the validation-score history is "
            "extended on EVERY call, including when validation data is not in use. "
            "Both re-encodings are correct and both histories hold the right "
            "values; the defect is that an output component the contract requires "
            "to be carried through UNCHANGED is changed. Its faithful real patch "
            "computes and appends the validation score outside the "
            "validation-data guard, so with no validation split the unguarded "
            "scoring call raises for every estimator configured to early-stop on "
            "training data — the early-stopping-on-training-data configurations of "
            "the regression and classification P2P tests FAIL. It does NOT "
            "resolve. This is the value-level analogue of nagini's MANDATORY "
            "input-overwrite attack: the carrier has no fractional permission, but "
            "the obligation the half-permission encodes (do not disturb what you "
            "were handed) is a real clause here and is otherwise undefended."
        ),
        "rationale": (
            "REJECT from clause (C_no) at useVal=false with BOTH validation "
            "arguments supplied: `valScores` must equal `vlScores` exactly, and "
            "the rival returns `vlScores ++ [score]`. The witness is taken at "
            "supplied arguments ON PURPOSE, so that the ok/error disposition is "
            "not what refutes it and the rejection is attributable to the frame "
            "clause alone. The refutation is STRUCTURAL, not conditional — a list "
            "cannot equal itself extended by one element — so the witness needs no "
            "hypothesis about the opaque scorer and has no consistency probe to "
            "clear. If it verified, `valScores` would be unconstrained on the "
            "no-validation path, which is exactly the unconstrained-output-"
            "component hole spec_guide §0.5 names => SPEC-TOO-WEAK."
        ),
        "witness": _WIT_VAL_FRAME,
    },
    {
        "id": "weak-stop-uses-train",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_STOP_USES_TRAIN),
        "refinement": (
            "stop-decision attack: both histories are recorded exactly as the "
            "contract demands and both re-encodings are correct, but the halt "
            "decision always consults the training history — so when validation "
            "data IS in use the stopping rule is asked about the wrong history. "
            "Its faithful real patch returns the training-history verdict from "
            "both arms of the validation-data branch. Early stopping then fires on "
            "training-score plateaus instead of validation-score plateaus, so the "
            "iteration count the early-stopping P2P tests assert "
            "(n_iter_no_change <= n_iter_ < max_iter, on a validation split) is no "
            "longer the quantity being controlled and those tests FAIL. It does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT from the `stop` component of clause (C_val) at useVal=true: "
            "`stop` must be `shouldStop (vlScores ++ [vlScore])`, but the rival "
            "returns `shouldStop (trScores ++ [trScore])`. Together with "
            "weak-stop-no-val-unextended this is what pins the halt decision; the "
            "history rivals all satisfy it. The witness conditions on "
            "`shouldStop`, the other opaque function-valued input, rather than on "
            "`scorer`. If it verified => SPEC-TOO-WEAK (the halt decision would be "
            "free to consult either history)."
        ),
        "witness": _WIT_STOP_USES_TRAIN,
    },
    {
        "id": "weak-stop-no-val-unextended",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_STOP_NO_VAL_UNEXTENDED),
        "refinement": (
            "off-by-one-in-time on the no-validation halt decision: both "
            "re-encodings are correct and both histories are recorded exactly as "
            "the contract demands, but when validation data is NOT in use the "
            "stopping rule is consulted on the training history as it stood on "
            "entry — this iteration's own score is appended, then ignored by the "
            "decision. Its faithful real patch reads the training-score history "
            "into a local before appending and hands the stale local to the "
            "stopping rule. Early stopping then decides one iteration behind, so "
            "the plateau length the early-stopping P2P tests assert "
            "(n_iter_no_change <= n_iter_ < max_iter, in the no-validation-split "
            "configurations of both the regression and the classification "
            "early-stopping families, which are P2P for this instance) is off by "
            "one and those tests FAIL. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the `stop` component of clause (C_no) at useVal=false: "
            "`stop` must be `shouldStop (trScores ++ [trScore])`, but the rival "
            "returns `shouldStop trScores`. weak-stop-uses-train pins WHICH "
            "history the decision reads on the validation path, and this pins that "
            "on the no-validation path it must be the EXTENDED one — the other "
            "rivals all satisfy that conjunct, so an impl that consulted a stale "
            "training history was otherwise unattested. The witness conditions on "
            "`shouldStop` separating the extended history from the one handed in. "
            "If it verified => SPEC-TOO-WEAK (the halt decision could ignore the "
            "score it just recorded)."
        ),
        "witness": _WIT_STOP_NO_VAL,
    },

    # ---- the lane the previous contract had no case for ----
    {
        "id": "weak-val-read-hoisted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_VAL_READ_HOISTED),
        "refinement": (
            "the machine-checked attack that BROKE the previous contract, "
            "re-encoded against this one (`atk_2.lean`, verified 2026-08-16: "
            "same_spec=True, verifies=True, `#print axioms` clean). The validation "
            "design matrix and targets are read and decoded BEFORE the branch that "
            "knows whether they exist; every recorded value is otherwise gold's. "
            "Its faithful real patch is the gold patch with the val-site decode "
            "lifted out of `if self._use_validation_data:`, and it was RUN in the "
            "official instance image: it FAILS two PASS_TO_PASS tests that the "
            "gold patch PASSES in the same image and session — "
            "test_early_stopping_classification[accuracy-None-5-0.1-data0] and "
            "[...-data1], parameters ('accuracy', None, 5, 1e-1), a classifier "
            "with validation_fraction=None — with `AttributeError: 'NoneType' "
            "object has no attribute 'astype'`, because "
            "gradient_boosting.py sets `X_val, y_val = None, None` on that path. "
            "A patch that fails a PASS_TO_PASS test cannot resolve, so it does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the DISPOSITION of clause (C_no) at useVal=false with "
            "both validation arguments absent: the result must be a SUCCESS, and "
            "the rival returns `Except.error EarlyStopError.absentValidationData` "
            "because it read arguments that hold nothing. This is the case the "
            "PREVIOUS contract could not express — it typed both validation "
            "inputs total, so hoisting a pure decode past the guard was "
            "provably semantics-preserving and this rival VERIFIED against it "
            "while its faithful patch failed the P2P tests above (verify ⇏ "
            "correct). The witness is unconditional: `Except.error` cannot equal "
            "`Except.ok`. If it verified again => SPEC-TOO-WEAK, and the same hole "
            "as before."
        ),
        "witness": _WIT_VAL_READ_HOISTED,
    },
    {
        "id": "weak-val-score-hoisted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_VAL_SCORE_HOISTED),
        "refinement": (
            "the same defect one step further (`atk_3.lean`, likewise verified "
            "against the previous contract on 2026-08-16 with same_spec=True and "
            "clean axioms): the validation SCORE itself is computed above the "
            "guard, so the scoring call is hoisted along with the reads. Its "
            "faithful real patch lifts both `y_val = self.classes_[...]` and "
            "`self.scorer_(self, X_binned_val, y_val)` out of "
            "`if self._use_validation_data:`; on the no-validation path both "
            "arguments are `None`, so it raises on the same line as the "
            "weak-val-read-hoisted patch and additionally calls the scorer on a "
            "`None` design matrix. It does NOT resolve, for the same measured "
            "reason (the two test_early_stopping_classification[accuracy-None-...] "
            "PASS_TO_PASS failures)."
        ),
        "rationale": (
            "REJECT from the DISPOSITION of clause (C_no), witnessed at a "
            "DIFFERENT presence pattern from weak-val-read-hoisted: useVal=false "
            "with the design matrix SUPPLIED and the targets absent, so the rival "
            "gets past the first read and fails on the second while (C_no) still "
            "demands a success. Shipped alongside weak-val-read-hoisted because "
            "the repaired contract has to reject BOTH shapes the live audit "
            "produced, not just the smaller one. Unconditional witness. If it "
            "verified => SPEC-TOO-WEAK."
        ),
        "witness": _WIT_VAL_SCORE_HOISTED,
    },
    {
        "id": "weak-val-order-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_VAL_ORDER_SWAPPED),
        "refinement": (
            "the shape the live G-PANEL audit refuted the PREVIOUS contract with, "
            "kept as a rival so the repaired one cannot drift back. It is gold "
            "with the two validation reads swapped: the design matrix is read "
            "before the target codes are read and decoded. Its faithful real "
            "patch is the gold patch with the validation decode moved BELOW the "
            "`self.scorer_(self, X_binned_val, y_val)` line, so the design matrix "
            "is consumed first. That patch cannot resolve: the F2P scenario "
            "(`test_string_target_early_stopping`) needs the DECODED labels to "
            "reach the scorer, and a decode performed after the call that "
            "consumes it hands the scorer the raw integer codes — the pre-patch "
            "defect, on the validation site. There is no ordering of those two "
            "Python statements that both consults the design matrix first and "
            "still decodes in time, which is exactly why the order is a fact "
            "about the method rather than a choice the contract may make."
        ),
        "rationale": (
            "REJECT from the ORDER of the two validation reads inside clause "
            "(C_err), at isClf=true with the design matrix ABSENT and the target "
            "codes SUPPLIED but out of range for the class-label table: the "
            "method reads and decodes the codes first, so the contract demands "
            "the decode's own `codeOutOfRange`, and the rival — reading the "
            "design matrix first — reports `absentValidationData`. This is the "
            "defect the audit found in the previous contract, in the opposite "
            "direction: there the SPEC held the design-matrix-first order and "
            "refuted the faithful impl (SPEC-TOO-STRONG, 13 disagreeing points "
            "over a 21600-point grid, all of this shape); here the repaired spec "
            "holds the method's order and refutes the design-matrix-first impl. "
            "Unconditional witness — two distinct `EarlyStopError` constructors, "
            "nothing assumed about the carrier. It is the only reject case on the "
            "arm the repair changed, so without it that arm's new content would "
            "be unattacked. If it verified => SPEC-TOO-WEAK, and the order would "
            "be back to unstated."
        ),
        "witness": _WIT_VAL_ORDER_SWAPPED,
    },
    {
        "id": "weak-val-scorecall-hoisted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_VAL_SCORECALL_HOISTED),
        "refinement": (
            "the attack that survived the Option-plus-error interface "
            "(`atk_8.lean`, verified against it on 2026-08-16 with "
            "same_spec=True and axioms `[propext]`). Both guarded READS are "
            "kept, so nothing absent is ever read; what moves above the guard is "
            "the SCORING CALL, on a stand-in pair built from `Option.getD` "
            "defaults. Its faithful real patch hoists "
            "`_hoisted_score = self.scorer_(self, X_binned_val if "
            "X_binned_val is not None else X_binned_small_train, _hoisted_targets)` "
            "above `if self._use_validation_data:` and records it inside. "
            "Measured in the official instance image (digest "
            "`sha256:e68930db25c0…`) on 2026-08-16: it FAILS THREE PASS_TO_PASS "
            "tests the gold patch passes — "
            "test_early_stopping_regression[neg_mean_squared_error-None-5-0.1] "
            "and test_early_stopping_classification[accuracy-None-5-0.1-data0] / "
            "[…-data1] — with `ValueError: Found input variables with "
            "inconsistent numbers of samples: [0, 50]` (and `[0, 30]`) raised "
            "from sklearn/utils/validation.py:206, because the stand-in targets "
            "are an EMPTY array while the training design matrix has 50 (resp. "
            "30) rows. It does NOT resolve."
        ),
        "rationale": (
            "REJECT from the ARGUMENTS of the scoring call rather than from the "
            "recorded score or the reads: the contract names the pair the "
            "scoring function is consulted about, and carries that answer with "
            "`Except.bind`/`Except.map`, so a call about any OTHER pair is "
            "answerable for the refusal it draws. This is the lane a TOTAL "
            "`scorer : XData → Targets → Score` could not express at all — with "
            "a total scoring function the hoisted call is a dead pure value on "
            "the no-validation path, which is precisely how this rival verified "
            "against the previous contract. Witnessed unconditionally at "
            "isClf=false with both validation arguments absent, with the scoring "
            "function refusing only the empty-target stand-in. If it verified => "
            "SPEC-TOO-WEAK, with a measured non-resolving patch to prove it."
        ),
        "witness": _WIT_VAL_SCORECALL_HOISTED,
    },
    {
        "id": "weak-labels-hoisted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_LABELS_HOISTED),
        "refinement": (
            "the class-label-table analogue of weak-val-read-hoisted, and the "
            "rival the earlier TOTAL `labels` interface could not express: the "
            "table is read ABOVE the `isClf` guard, while both decodes stay "
            "inside it, so every recorded score is gold's whenever the "
            "estimator has a table. Its faithful real patch hoists the gather "
            "out of `if is_classifier(self):` and selects it under the guard. "
            "`self.classes_` is set only by "
            "`HistGradientBoostingClassifier._encode_y` "
            "(gradient_boosting.py:1029); a regressor never defines it, and "
            "`_check_early_stopping_scorer` IS reached by a regressor whenever "
            "`scoring != 'loss'` (gradient_boosting.py:254 / :358). So the "
            "hoisted read raises `AttributeError: "
            "'HistGradientBoostingRegressor' object has no attribute "
            "'classes_'` on the four scorer-driven "
            "test_early_stopping_regression PASS_TO_PASS parametrizations "
            "([neg_mean_squared_error-0.1-5-1e-07], "
            "[neg_mean_squared_error-None-5-0.1], [None-0.1-5-1e-07], "
            "[None-None-5-0.1]; the two [loss-...] ones take the "
            "_check_early_stopping_loss path instead and the "
            "[None-None-None-None] one does not early-stop at all). Measured in "
            "the official instance image: 4 failed / 3 passed for this patch "
            "against 7 passed for the gold control, same image, same command, "
            "same session — see refinement.md, `Reading an absent class-label "
            "table`. A patch that fails a PASS_TO_PASS test cannot resolve, so "
            "it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the DISPOSITION of the non-categorical clause at "
            "isClf=false with NO class-label table: the result must be a "
            "SUCCESS recording the RAW-code score, and the rival returns "
            "`Except.error EarlyStopError.absentClassLabels` because it read a "
            "table that does not exist. This is the second lane the earlier "
            "interface could not express — it typed `labels` TOTAL, so hoisting "
            "the table read past the `isClf` guard was provably "
            "semantics-preserving and this rival VERIFIED against it while its "
            "faithful patch fails the P2P tests above (verify ⇏ correct). The "
            "witness is unconditional: `Except.error` cannot equal "
            "`Except.ok`. If it verified again => SPEC-TOO-WEAK."
        ),
        "witness": _WIT_LABELS_HOISTED,
    },
]


# Axiom lane is G-AX's job, not this gate's; the nagini AXIOM_TESTS are dropped.
AXIOM_TESTS = []
