"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-25232 (lean).

NOT a Lean module: a record of adversarial cases the G-PBT gate executes over the
frozen ``Solution.lean``. This is a PORT of the nagini sibling's battery to the
lean carrier — re-expressing its adversarial reasoning, not its text. Each case
is a full ``Solution.lean`` variant produced by region surgery: only the text
strictly inside the ``-- impl-start`` / ``-- impl-end`` region (and, for the two
non-defeq soundness positives, the ``-- proof-start`` / ``-- proof-end`` body) is
changed,
so ``variant_scope.same_spec`` holds by construction and the
``theorem correct_initial_fill`` STATEMENT stays byte-identical. Every rejection
is therefore attributable to the postcondition, never to a tampered spec.

AUDIT REVISION
--------------
Independently re-audited after the port recorded SOUND. Every case was rebuilt
through the gate's own surgery (``pbt_witness.witness_file``) and every
``expect="reject"`` witness was additionally subjected to the FORGERY test: the
same witness with its claim FLIPPED (``¬ problem_spec …`` -> ``problem_spec …``)
was built against both sides. All twelve flipped claims ELABORATE against the frozen
solution (exit 0) and FAIL against their own rival (exit 1) with
``Tactic `decide` proved that the proposition … is false`` — the exact mirror of
the unflipped pair. So each gold-side exit code demonstrably TRACKS the claim
rather than reporting a stuck kernel, and no ported case is hollow. The audit
changed four things:

  * the DIVERGENCE class was recorded as VACUOUS on an argument that is measurably
    false; it is a known HOLE, and the builds that establish that are written out
    under PORTING MAP below;
  * (X2)'s outer row binder was pinned at exactly one point — every reject witness
    used a single-row matrix — and its column INDEX was never attacked at all, so
    ``weak-xfilled-row-partial`` and ``weak-xfilled-shift-col`` were added;
  * the positive lane's only non-defeq control reshaped the ``statistics`` field
    only, leaving the whole matrix half of the spec with no shape control at all;
    ``pos-map-functional`` was added and is the second SPEC-TOO-STRONG control;
  * one prose claim that overstated what had been measured (the CARRIER note's
    "every rival is refutable by evaluating the spec predicate at a concrete
    input") was corrected in place.

DEFENDED SURFACE (one total function over its whole input domain)
----------------------------------------------------------------
    initial_fill
        (X : Array (Array Rat)) (missingValues : Rat) (fillValue : Option Rat)
        : InitialFillResult    -- { statistics : Array Rat, xFilled : Array (Array Rat) }

models the first-round constant initialization. The effective constant is
``effFill fillValue = fillValue.getD 0`` (a user value when present, else the
neutral numerical default). The load-bearing postcondition has FOUR independent
top-level clauses, and this carrier is RICHER than the nagini sibling's — nagini
modeled only the per-feature statistic vector, whereas the lean model ALSO models
the returned filled matrix, so there is a whole extra family of clauses to attack:

  (S1) statistics.size = nFeatures X                     -- one statistic per feature
  (S2) ∀ j < nFeatures X, statistics[j]! = effFill fillValue
                                                         -- THE discriminating clause
                                                            nagini's F2P observes
  (X1) xFilled.size = X.size ∧ per-row: xFilled[i]!.size = X[i]!.size
                                                         -- shape of the filled matrix
  (X2) ∀ i j, xFilled[i]![j]! = (if X[i]![j]! = missingValues
                                   then effFill fillValue else X[i]![j]!)
                                                         -- sentinel replaced by the
                                                            constant; every other entry
                                                            pinned to its input (frame)

The nagini F2P observation ``statistics_ == fill_value`` maps to clause (S2); the
pre-patch omission (build the inner imputer without the user constant, so every
feature defaults to 0) violates (S2) whenever ``fillValue`` is a non-zero value.

CARRIER
-------
Fully transparent: ``Rat`` / ``Array`` / ``Option``, NO opaque callee is consumed
as an axiom (the round-zero fill and the sentinel replacement are modeled deeply).
So every rival SHIPPED HERE is refutable by evaluating the spec predicate at a
concrete input — no carrier conditioning is needed and no witness binds a
hypothesis (nothing to be inconsistent; the consistency probe never fires, which
was confirmed: ``consistency_probe`` returns ``None`` for all twelve witnesses).

Transparency is a property of the impls this battery ships, NOT of the carrier as
such, and the distinction is load-bearing: a rival may make the SUBJECT of the
refutation opaque, and then evaluation refutes nothing. The measured instance is
the divergence class below — a ``partial def`` is compiled to a constant with no
equation lemmas, so ``decide``/``unfold``/``simp``/``rw`` are all stuck on it.
Two consequences worth keeping straight: kernel-reducibility here is earned by
each rival keeping a bounded ``for`` over literal arrays, and it is why the
statistics rivals must pre-reduce the do-block (see the witness note below) rather
than relying on the carrier being "fully transparent".

Every witness — including the six that attack only the statistics clauses
(S1)/(S2) — hands the do-block reduction lemmas
(``Array.forIn_yield_eq_foldl`` / ``Std.Range.forIn_eq_forIn_range'`` /
``List.forIn_yield_eq_foldl``) to ``simp only`` BEFORE ``decide``. For a
statistics rival a bare ``unfold … ; decide`` is enough to prove the negation —
the false ``statistics`` conjunct short-circuits the outer ``And`` — but the same
script run against the FROZEN solution must then evaluate the matrix conjunct,
whose ``Id.run``/``forIn`` do-block ``decide`` cannot reduce. The gold-side build
fails with ``failed to reduce to isTrue or isFalse`` instead of refuting
anything, which makes the exit code attest to a refutation that never happened
(``witness-undecided``). Pre-reducing the do-block turns the matrix conjunct into
a ``foldl`` over literal arrays, which ``decide`` does reduce, so the gold-side
failure is a genuine refutation.

Every witness below was built BOTH ways through the gate's own file surgery
(``pbt_witness.witness_file``): it ELABORATES against its rival (exit 0) and
FAILS against the frozen solution (exit 1) with
``Tactic 'decide' proved that the proposition … is false`` and no stuck reduction
anywhere in the gold-side log.

PORTING MAP (which nagini cases port, which are omitted)
--------------------------------------------------------
  * nagini ``weak-default-zero`` (the pre-patch omission verbatim: pass the neutral
    default instead of the requested value) -> ``weak-default-zero``. Attacks (S2).
  * added ``weak-wrong-default`` — varies the ``fillValue`` binder to ``none`` and
    mishandles the DEFAULT arm of ``effFill`` (uses 100 instead of 0). The only
    rival that moves ``fillValue`` off ``some _``; without it a rival that gets the
    supplied value right but the default wrong would slip by. Attacks (S2).
  * nagini ``weak-partial-first`` -> ``weak-partial-first``. Attacks (S2) at j=0.
  * nagini ``weak-partial-last`` -> ``weak-partial-last``. Attacks (S2) at j=n-1.
  * nagini ``weak-len-long`` -> ``weak-stats-len-long``. Attacks (S1).
  * nagini ``weak-empty`` -> ``weak-stats-empty``. Attacks (S1) — but it does NOT
    isolate it: (S2) also fails, because (S2) quantifies over ``j < nFeatures X``
    (the INPUT's feature count), so the empty vector's out-of-bounds ``#[][j]!``
    is the ``Rat`` default 0, not a vacuous ∀. ``weak-stats-len-long`` is the rival
    that isolates (S1). See the case rationale for the machine-checked exit codes.
  * added (NO nagini counterpart — this carrier models the filled matrix, nagini
    did not):
      - ``weak-xfilled-no-replace`` — a sentinel entry is NOT replaced by the
        constant. Attacks (X2).
      - ``weak-xfilled-clobber`` — a NON-sentinel entry is overwritten by the
        constant, violating the frame half of (X2).
      - ``weak-xfilled-extra-row`` — the filled matrix has one row too many.
        Attacks (X1) row count.
      - ``weak-xfilled-row-long`` — each filled row is one entry too long. Attacks
        (X1) per-row size.
      - ``weak-xfilled-row-partial`` — replaces sentinels in the FIRST row only,
        forwarding later rows untouched. Attacks (X2) at ``i=1``: the only rival
        whose witness point has more than one row, so it is the only one that
        moves (X2)'s OUTER binder off ``i=0``. Without it every xFilled rival is
        refuted on a single-row matrix and the per-row quantifier is pinned at
        exactly one point.
      - ``weak-xfilled-shift-col`` — reads ``row[j+1]!`` instead of ``row[j]!``,
        so each filled row is a correct-looking shift of the input row. Attacks
        (X2)'s INDEX IDENTITY: every entry of the rival's row is a legitimate
        entry of the input row and the sentinel test is applied correctly, so
        this passes any clause that only checks membership or multiset content —
        it is refutable only because (X2) pins entry ``j`` to INPUT entry ``j``.
        No other rival attacks the column index.
  * nagini ``pos-local-reshape`` (carry the value through an intermediate local)
    -> ``pos-local-reshape`` (carry ``fillValue`` through a local) and the added
    ``pos-inline-eff`` (inline ``effFill`` at both use sites). Both keep the frozen
    tactic body verbatim, and BOTH ARE DEFINITIONALLY EQUAL to the frozen impl:
    ``example : @implementation_alt = @implementation_initial_fill := rfl``
    elaborates (exit 0) for each. They are therefore honest but WEAK positives —
    a defeq reshape cannot detect a spec over-fit to the frozen impl's spelling,
    because there is no spelling difference the kernel can see. They are kept
    (they cost little and do pin that the obligation is satisfiable) but they are
    NOT the SPEC-TOO-STRONG control; ``pos-explicit-loop`` below is.
  * nagini ``pos-explicit-loop`` (build via an explicit forward-append loop) ->
    ``pos-explicit-loop``. Builds ``statistics`` by pushing the constant once per
    feature instead of ``Array.replicate``, so it is NOT definitionally equal to
    the frozen impl (the same ``rfl`` probe FAILS, exit 1) and the frozen tactic
    body does NOT close it: the ``statistics`` field is now a ``forIn`` over
    ``[0:nFeatures X]`` rather than a ``replicate``, and gold's ``unfold_fields``
    fails with ``rewrite ... did not find an occurrence of the pattern forIn``.
    Reproving it needs a genuine induction relating the append loop's closed form
    to ``Array.replicate``, supplied inline as a ``have`` inside ``unfold_fields``
    (a top-level lemma would trip ``variant_scope``'s no-new-theorem rule). This
    is a load-bearing SPEC-TOO-STRONG control: a faithful correct impl whose
    SHAPE the spec must still accept. It covers the ``statistics`` half only; see
    ``pos-map-functional`` for the matrix half.
  * added ``pos-map-functional`` (NO nagini counterpart) — the SECOND
    SPEC-TOO-STRONG control, covering the half of the spec ``pos-explicit-loop``
    leaves untested. ``pos-explicit-loop`` reshapes only the ``statistics`` field;
    the matrix clauses (X1)/(X2) are the larger half of this postcondition and had
    NO shape control at all, because every positive built ``xFilled`` with the
    frozen impl's own nested ``for``/``push`` accumulation. So nothing tested
    whether (X1)/(X2) accept a differently-SHAPED matrix computation, which is
    exactly the over-fit a soundness positive exists to detect. This positive drops
    both loops and builds the matrix functionally —
    ``X.map (fun row => row.map (fun v => if v = missingValues then fill else v))``
    — with no accumulator, no index arithmetic, and no ``forIn`` anywhere. Measured
    NOT definitionally equal to the frozen impl (the ``rfl`` probe FAILS, exit 1)
    and the frozen tactic body does NOT close it (``rewrite ... did not find an
    occurrence of the pattern forIn`` inside ``unfold_fields``). Re-proved by an
    inline ``have`` identifying ``Array.map`` on a row with ``mapRow``'s ``foldl``
    closed form (an ``Array.ext'`` / ``List.ext_getElem`` argument over the row's
    indices, plus the ``getElem!_pos`` bridge — a real proof, not a restatement),
    after which the frozen ``inner_*``/``outer_*`` lemmas and
    ``correct_initial_fill`` itself close UNCHANGED.
  * nagini ``admiss-nonvacuous`` -> ``admiss-ground-matrix``. An earlier revision
    of this file recorded the lane as VACUOUS, reasoning that the obligation's
    rectangularity precondition (``∀ i, i < X.size → (X[i]!).size = nFeatures X``)
    is establishable for every F2P-shaped input and is never consumed by the proof,
    so no precondition CLAUSE is left for a probe to attack. That reasoning was
    wrong about what the lane detects: on a total carrier PRECOND-TOO-STRONG is the
    obligation being UNSATISFIABLE at a normal input (hypothesis holds, conclusion
    does not), and totality does not make that impossible. The ported case
    discharges the hypothesis AND the whole spec predicate at a concrete F2P-shaped
    input by evaluation, with the impl and every theorem statement untouched.
  * nagini frame / permission-mutation class — VACUOUS on lean (referential
    transparency: no half-permission input, no aliasing). It is not fabricated as a
    substitute. NOTE: the frame OBLIGATION itself is not vacuous — it is discharged
    STRUCTURALLY by clause (X2)'s ``else X[i]![j]!`` arm, which pins every
    non-sentinel entry to its input value, and ``weak-xfilled-clobber`` attacks
    exactly that pin.
  * DIVERGENCE / non-termination class — a KNOWN HOLE, not a vacuous class. An
    earlier revision of this file recorded it as VACUOUS on the argument that
    ``implementation_*`` is a total Lean ``def`` so "a diverging impl cannot be
    written at all". That argument is FALSE and was measured false. This bundle
    sets no ``loom.semantics.termination`` option — it is plain Lean 4 — so the
    relevant question is what Lean's own termination obligation blocks, and it
    blocks only the UNANNOTATED forms:

      - a self-recursive plain ``def`` with no decreasing measure is refused
        (``error: fail to show termination for implementation_initial_fill``), and
      - ``partial def`` alone is refused for THIS return type
        (``failed to compile 'partial' definition ..., could not prove that the
        type ... is nonempty``) because ``InitialFillResult`` has no ``Inhabited``
        instance in the frozen file,

    but supplying that instance inside the impl region lifts both objections. The
    diverging rival

        instance : Inhabited InitialFillResult := ⟨{ statistics := #[], xFilled := #[] }⟩
        partial def implementation_initial_fill
            (X : Array (Array Rat)) (missingValues : Rat) (fillValue : Option Rat) :
            InitialFillResult :=
          implementation_initial_fill X missingValues fillValue

    ELABORATES, and it is an admissible variant: ``same_spec`` holds and
    ``variant_scope.variant_problems`` returns ``[]`` (an ``instance`` is not a
    new theorem/axiom and ``partial`` is not an assumption token). It is also
    genuinely REJECTED — the frozen tactic body fails on it — so it looks
    shippable to the reject lane.

    It is NOT shippable, and the reason is the witness half, which was measured
    rather than assumed. A ``partial def`` is compiled to an opaque constant with
    NO equation lemmas, so nothing can reduce it and nothing can refute it:

      - ``unfold implementation_initial_fill`` -> ``failed to unfold``;
      - ``decide`` and ``decide +kernel`` -> ``Tactic 'decide' failed for
        proposition ...`` (stuck on the ``Decidable`` instance);
      - ``simp [implementation_initial_fill]`` -> ``unsolved goals``;
      - ``rw [implementation_initial_fill]`` -> ``Invalid rewrite argument``.

    The hypothesis-conditioned shape that works on an opaque CALLEE does not
    rescue it either, and this is the decisive measurement: a witness of the form
    ``example (h : (impl …).statistics = #[]) : ¬ problem_spec … := by …``
    elaborates against the diverging rival (exit 0) AND against the FROZEN
    solution (exit 0), because the hypothesis is false-but-irrefutable of gold
    too, so the gate records ``witness-vacuous``. The asymmetry an opaque callee
    provides is absent here: the opacity is in the SUBJECT of the refutation, not
    in a term both impls share.

    So the honest disposition is a HOLE in the spec, stated plainly: the frozen
    postcondition is a pure ``Prop`` about the returned record and says nothing
    about termination, so a non-terminating impl that is opaque to the kernel can
    be neither verified nor refuted on this carrier. Recording it as "vacuous"
    would assert the battery is complete; recording it as a hole says the spec is
    not. No case is fabricated for it, because a case whose witness is vacuous is
    worse than an admitted gap.
  * nagini ``AXIOM_TESTS`` — DROPPED. The axiom lane is G-AX's job; this gate
    ignores it. AXIOM_TESTS is empty.

BINDER / CLAUSE / POINT COVERAGE
--------------------------------
  * ``fillValue`` — refuted at ``some 100`` (most rivals) AND at ``none``
    (``weak-wrong-default``), so BOTH arms of ``effFill fillValue = fillValue.getD 0``
    are pinned.
  * ``missingValues`` — refuted at ``0`` (the statistics rivals, where no entry is a
    sentinel) AND at ``7`` (the xFilled rivals, where the sentinel is present), so
    the sentinel test in clause (X2) is exercised on both sides.
  * ``X`` — 1x1, 1x2, 2x1, and matrices whose entries are / are not sentinels, so
    the shape clauses (S1)/(X1) and the pointwise clauses (S2)/(X2) are all moved.
  * All four top-level clauses (S1),(S2),(X1),(X2) are attacked by some rival.
  * (X2) is a NESTED quantifier and both of its binders are now moved. The row
    binder ``i``: every reject witness but one uses a single-row matrix, so
    ``weak-xfilled-row-partial`` (a 2x1 whose SECOND row is left unfilled) is the
    case that refutes at ``i=1`` rather than ``i=0``. The column binder ``j`` is
    attacked as an INDEX rather than as a value by ``weak-xfilled-shift-col``,
    whose row is a shift of the input row: every entry it emits IS an entry of the
    input row and the sentinel test is applied faithfully, so only (X2)'s pinning
    of entry ``j`` to INPUT entry ``j`` refutes it.
  * Distinct witness input points (``pts``): (#[#[5]],0,some 100),
    (#[#[5,6]],0,some 100), (#[#[5]],0,none), (#[#[7]],7,some 100),
    (#[#[5]],7,some 100), (#[#[7],#[7]],7,some 100) — six distinct points, so no
    rival's refutation is parasitic on a single input.

WHICH RIVAL ISOLATES WHICH CLAUSE (machine-checked, not asserted)
----------------------------------------------------------------
Each of the five clause conjuncts was evaluated by ``decide`` at each rival's own
witness point, against BOTH the rival and the frozen solution. Against gold all
five hold at all five points (exit 0). Against the rivals:

  * ``weak-stats-len-long`` genuinely ISOLATES (S1): (S2),(X1),(X2) all decide
    TRUE and only the size conjunct fails.
  * ``weak-stats-empty`` fails (S1) AND (S2) — it does NOT isolate the size
    clause, because (S2) quantifies over ``j < nFeatures X`` (the INPUT's feature
    count), not over the returned vector's own indices, so ``j=0`` stays in range
    and the empty vector's out-of-bounds ``#[][0]!`` is the ``Rat`` default 0.
    An earlier revision of this file claimed that ∀ was "vacuously true over the
    empty vector"; that claim was false and is corrected in the case rationale.
  * every other rival fails exactly the clause its rationale names, with the
    remaining conjuncts deciding TRUE.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-25232"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The FULL gold impl-region interior (everything strictly between the
# `-- impl-start` / `-- impl-end` markers, minus the doc-comment + signature that
# sit outside the mutable body). Unique in the file — the near-identical spec line
# `let fill := effFill fillValue` also appears in problem_spec, so a per-LINE swap
# would not be unique; swapping this whole block edits ONLY the impl body.
_GOLD = (
    "  let fill := effFill fillValue\n"
    "  let statistics := Array.replicate (nFeatures X) fill\n"
    "  let mut xFilled : Array (Array Rat) := #[]\n"
    "  for row in X do\n"
    "    let mut newRow : Array Rat := #[]\n"
    "    for j in [0:row.size] do\n"
    "      let v := row[j]!\n"
    "      if v = missingValues then\n"
    "        newRow := newRow.push fill\n"
    "      else\n"
    "        newRow := newRow.push v\n"
    "    xFilled := xFilled.push newRow\n"
    "  return { statistics := statistics, xFilled := xFilled }"
)
assert _BASE.count(_GOLD) == 1, "impl region drifted; update _GOLD"

# The two DEFEQ positives keep the frozen proof body verbatim (their reshapes are
# definitionally equal to gold), so they need no proof-region surgery.
# `pos-explicit-loop` is NOT defeq and does need it: the gold `unfold_fields`
# script assumes the `statistics` field is already an `Array.replicate`, so it has
# to be re-proved for an append loop. This is the ONLY fragment of the frozen
# proof that changes; every downstream lemma and `correct_initial_fill` itself are
# untouched, which keeps the reproof honest (the obligation is re-established, not
# restated).
_GOLD_UNFOLD_TAIL = (
    "  simp only [implementation_initial_fill, Id.run, bind, pure]\n"
    "  congr 1\n"
    "  rw [Array.forIn_yield_eq_foldl]\n"
    "  congr 1\n"
    "  funext acc row\n"
    "  congr 1\n"
    "  -- inner per-row loop equals `mapRow`\n"
    "  rw [mapRow]\n"
    "  rw [Std.Range.forIn_eq_forIn_range']\n"
    "  simp only [← apply_ite ForInStep.yield]\n"
    "  rw [List.forIn_yield_eq_foldl]\n"
    "  rw [List.range_eq_range']\n"
    "  have hs : [:row.size].size = row.size := by simp [Std.Range.size]\n"
    "  rw [hs]\n"
    "  congr 1\n"
    "  funext nr j\n"
    "  split <;> rfl\n"
)
assert _BASE.count(_GOLD_UNFOLD_TAIL) == 1, "proof region drifted; update tail"

# The same script, plus (a) an inline induction identifying the append loop's
# closed form with `Array.replicate` -- inline as a `have`, since a top-level
# lemma would trip variant_scope's no-new-theorem rule -- and (b) a split of the
# now-two `congr 1` goals (statistics loop / xFilled loop) that gold did not need.
_MAPFUN_UNFOLD_TAIL = (
    "  have rowmap : ∀ (r : Array Rat),\n"
    "      r.map (fun v => if v = missingValues then effFill fillValue else v)\n"
    "        = mapRow missingValues (effFill fillValue) r := by\n"
    "    intro r\n"
    "    apply Array.ext'\n"
    "    have hl : (mapRow missingValues (effFill fillValue) r).toList\n"
    "        = (List.range r.size).map"
    " (fun j => if r[j]! = missingValues then effFill fillValue else r[j]!) := by\n"
    "      have key : ∀ (n : Nat) (g : Nat → Rat) (init : Array Rat),\n"
    "          ((List.range n).foldl (fun nr j => nr.push (g j)) init).toList\n"
    "            = init.toList ++ (List.range n).map g := by\n"
    "        intro n\n"
    "        induction n with\n"
    "        | zero => intro g init; simp\n"
    "        | succ m ih =>\n"
    "            intro g init\n"
    "            rw [List.range_succ, List.foldl_append, List.map_append]\n"
    "            simp [ih]\n"
    "      unfold mapRow; rw [key]; simp\n"
    "    rw [hl]\n"
    "    simp only [Array.toList_map]\n"
    "    apply List.ext_getElem (by simp)\n"
    "    intro n h1 h2\n"
    "    have hb : n < r.size := by simpa using h1\n"
    "    simp only [List.getElem_map, List.getElem_range]\n"
    "    rw [getElem!_pos r n hb]\n"
    "    congr 1\n"
    "  simp only [implementation_initial_fill, Id.run, bind, pure]\n"
    "  congr 1\n"
    "  rw [← Array.map_eq_foldl]\n"
    "  apply Array.map_congr_left\n"
    "  intro r _\n"
    "  exact rowmap r\n"
)

_RESHAPED_UNFOLD_TAIL = (
    "  have statsLoop_eq_replicate : ∀ (n : Nat) (fill : Rat),\n"
    "      (List.range n).foldl (fun acc _ => acc.push fill) #[]"
    " = Array.replicate n fill := by\n"
    "    intro n fill\n"
    "    induction n with\n"
    "    | zero => simp\n"
    "    | succ m ih =>\n"
    "        rw [List.range_succ, List.foldl_append]\n"
    "        simp only [List.foldl_cons, List.foldl_nil, ih]\n"
    "        apply Array.ext'\n"
    "        simp [Array.replicate_succ, Array.toList_replicate,"
    " List.replicate_succ']\n"
    "  simp only [implementation_initial_fill, Id.run, bind, pure]\n"
    "  congr 1\n"
    "  · -- the statistics append loop builds exactly `Array.replicate`\n"
    "    rw [← statsLoop_eq_replicate (nFeatures X) (effFill fillValue)]\n"
    "    rw [Std.Range.forIn_eq_forIn_range']\n"
    "    rw [List.forIn_yield_eq_foldl]\n"
    "    rw [List.range_eq_range']\n"
    "    have hs : [:nFeatures X].size = nFeatures X := by simp [Std.Range.size]\n"
    "    rw [hs]\n"
    "  · rw [Array.forIn_yield_eq_foldl]\n"
    "    congr 1\n"
    "    funext acc row\n"
    "    congr 1\n"
    "    -- inner per-row loop equals `mapRow` (unchanged from the frozen script)\n"
    "    rw [mapRow]\n"
    "    rw [Std.Range.forIn_eq_forIn_range']\n"
    "    simp only [← apply_ite ForInStep.yield]\n"
    "    rw [List.forIn_yield_eq_foldl]\n"
    "    rw [List.range_eq_range']\n"
    "    have hs : [:row.size].size = row.size := by simp [Std.Range.size]\n"
    "    rw [hs]\n"
    "    congr 1\n"
    "    funext nr j\n"
    "    split <;> rfl\n"
)


def _module(body, proof_tail=None):
    """Full Solution.lean variant with the gold impl body replaced by `body`.

    `proof_tail` optionally re-proves the `unfold_fields` step for an impl the
    frozen script does not close. Only the tactic BODY moves; every theorem
    STATEMENT (and `correct_initial_fill` in particular) stays byte-identical, so
    variant_scope's obligation-preservation rule holds.
    """
    src = _swap(_BASE, _GOLD, body)
    if proof_tail is not None:
        src = _swap(src, _GOLD_UNFOLD_TAIL, proof_tail)
    return src


# The single `intro` line of the frozen obligation's tactic body. The
# admissibility case prepends a ground `have` here: nothing about the impl or the
# obligation STATEMENT moves, so the only thing the case can fail on is the
# ground instance itself being unsatisfiable.
_P_INTRO = "  intro X missingValues fillValue _huniform\n"
assert _BASE.count(_P_INTRO) == 1, "obligation intro drifted; update _P_INTRO"

# The F2P-shaped ground input for the admissibility case: a rectangular 2x3
# matrix over `Rat` with the sentinel PRESENT in both rows (so the replacement
# arm of (X2) is exercised, not just the frame arm), a non-zero sentinel, and a
# supplied constant distinct from every entry.
_ADMISS_X = "#[#[(1:Rat), 7, 3], #[(7:Rat), 5, 6]]"
_ADMISS_GROUND = (
    f"  have _ground : (∀ i, i < ({_ADMISS_X} : Array (Array Rat)).size →\n"
    f"        (({_ADMISS_X} : Array (Array Rat))[i]!).size "
    f"= nFeatures ({_ADMISS_X} : Array (Array Rat))) ∧\n"
    f"      problem_spec_initial_fill ({_ADMISS_X} : Array (Array Rat)) 7 (some 100)\n"
    f"        (implementation_initial_fill ({_ADMISS_X} : Array (Array Rat)) 7 "
    "(some 100)) := by\n"
    "    refine ⟨by decide, ?_⟩\n"
    "    simp only [problem_spec_initial_fill, implementation_initial_fill, Id.run,\n"
    "      bind, pure, Array.forIn_yield_eq_foldl, Std.Range.forIn_eq_forIn_range',\n"
    "      List.forIn_yield_eq_foldl]\n"
    "    decide\n")


# ---------------------------------------------------------------------------
# Rival impl bodies (each a full impl-region interior). Only the impl changes.
# ---------------------------------------------------------------------------

# (weak-default-zero) THE pre-patch omission: the effective constant is forced to
# the neutral default 0, ignoring `fillValue`. Every feature statistic and every
# sentinel replacement uses 0. Violates (S2) whenever fillValue is non-zero.
_R_DEFAULT_ZERO = _GOLD.replace(
    "  let fill := effFill fillValue\n", "  let fill : Rat := 0\n", 1)

# (weak-wrong-default) Mishandle the DEFAULT arm of effFill: when no value is
# supplied use 100 instead of 0. Correct when a value is supplied, wrong on
# fillValue=none. The only rival that moves the `fillValue` binder off `some _`.
_R_WRONG_DEFAULT = _GOLD.replace(
    "  let fill := effFill fillValue\n", "  let fill := fillValue.getD 100\n", 1)

# (weak-partial-first) Fill the statistics vector correctly, then corrupt feature
# 0 to a fixed wrong constant (0). Violates (S2) at j=0 when the constant != 0.
_R_PARTIAL_FIRST = _GOLD.replace(
    "  let statistics := Array.replicate (nFeatures X) fill\n",
    "  let statistics := (Array.replicate (nFeatures X) fill).set! 0 0\n", 1)

# (weak-partial-last) Same, but corrupt the LAST feature. Violates (S2) at j=n-1.
_R_PARTIAL_LAST = _GOLD.replace(
    "  let statistics := Array.replicate (nFeatures X) fill\n",
    "  let statistics := (Array.replicate (nFeatures X) fill).set! (nFeatures X - 1) 0\n",
    1)

# (weak-stats-len-long) Every statistic is the right value but there is ONE TOO
# MANY feature. (S2) holds; (S1) statistics.size = nFeatures X fails.
_R_LEN_LONG = _GOLD.replace(
    "Array.replicate (nFeatures X) fill",
    "Array.replicate (nFeatures X + 1) fill", 1)

# (weak-stats-empty) Return an empty statistics vector. Violates (S1)
# statistics.size = nFeatures X for nFeatures X > 0. NOTE: (S2) is NOT vacuous
# here — its ∀ ranges over `j < nFeatures X` (the INPUT's feature count), not over
# the returned vector's indices, so j=0 is still in range and `#[][0]!` is the
# `Rat` default 0, not the required constant. Both (S1) and (S2) therefore fail;
# see the case rationale.
_R_EMPTY = _GOLD.replace(
    "  let statistics := Array.replicate (nFeatures X) fill\n",
    "  let statistics : Array Rat := #[]\n", 1)

# (weak-xfilled-no-replace) The per-row loop forwards every entry UNCHANGED,
# never replacing a sentinel by the constant. Violates (X2) at a sentinel entry.
_R_NO_REPLACE = _GOLD.replace(
    "      if v = missingValues then\n"
    "        newRow := newRow.push fill\n"
    "      else\n"
    "        newRow := newRow.push v\n",
    "      newRow := newRow.push v\n", 1)

# (weak-xfilled-clobber) The per-row loop overwrites EVERY entry with the constant
# — even a non-sentinel one — violating the frame half of (X2) (the `else X[i]![j]!`
# arm that pins non-sentinel entries to their input value).
_R_CLOBBER = _GOLD.replace(
    "      if v = missingValues then\n"
    "        newRow := newRow.push fill\n"
    "      else\n"
    "        newRow := newRow.push v\n",
    "      newRow := newRow.push fill\n", 1)

# (weak-xfilled-extra-row) Append one spurious empty row to the filled matrix.
# (X1) xFilled.size = X.size fails.
_R_EXTRA_ROW = _GOLD.replace(
    "  return { statistics := statistics, xFilled := xFilled }",
    "  return { statistics := statistics, xFilled := xFilled.push #[] }", 1)

# (weak-xfilled-row-long) Each filled row gets one extra trailing entry, so the
# per-row size half of (X1) fails.
_R_ROW_LONG = _GOLD.replace(
    "    xFilled := xFilled.push newRow\n",
    "    xFilled := xFilled.push (newRow.push 0)\n", 1)

# (weak-xfilled-row-partial) Replace sentinels in the FIRST row only: the guard
# additionally requires the output to still be empty, which is true only while the
# first row is being built. Later rows are forwarded untouched, so (X2) fails at
# i=1 while HOLDING at i=0. This is the only rival whose refutation point has more
# than one row, i.e. the only one that moves (X2)'s OUTER binder off i=0.
_R_ROW_PARTIAL = _GOLD.replace(
    "      if v = missingValues then\n",
    "      if v = missingValues ∧ xFilled.size = 0 then\n", 1)

# (weak-xfilled-shift-col) Read row[j+1]! where the spec pins entry j to INPUT
# entry j: each filled row is a SHIFT of the input row. Every emitted entry is a
# legitimate entry of the same input row and the sentinel test is applied
# faithfully to it, so nothing about membership, multiset content, or the
# replacement rule is violated — only (X2)'s index identity is. Attacks the
# COLUMN binder as an index, which no other rival does.
_R_SHIFT_COL = _GOLD.replace(
    "      let v := row[j]!\n", "      let v := row[j+1]!\n", 1)


# ---------------------------------------------------------------------------
# Soundness positives (must VERIFY) — CORRECT impls of a different shape. The
# theorem STATEMENT is byte-identical in all three.
#
# Two tiers, and the difference matters for what the SOUND actually certifies:
#   * `pos-local-reshape` / `pos-inline-eff` are DEFINITIONALLY EQUAL to the
#     frozen impl (measured: `example : @implementation_alt =
#     @implementation_initial_fill := rfl` elaborates for each). They verify with
#     the frozen tactic body precisely because the kernel cannot see a difference,
#     so they cannot detect a spec over-fit to the frozen impl's spelling. Honest,
#     cheap, and weak.
#   * `pos-explicit-loop` is NOT defeq (the same `rfl` probe fails) and the frozen
#     script does NOT close it. It is the real SPEC-TOO-STRONG control.
# ---------------------------------------------------------------------------

# (pos-local-reshape) Carry `fillValue` through an intermediate local before
# resolving the effective constant. Same computation, different shape; the frozen
# proof closes verbatim (`fv` is definitionally `fillValue`).
_P_RESHAPE = _GOLD.replace(
    "  let fill := effFill fillValue\n",
    "  let fv := fillValue\n  let fill := effFill fv\n", 1)

# (pos-inline-eff) Drop the `fill` binding and inline `effFill fillValue` at both
# use sites. Definitionally identical, so the frozen proof closes verbatim.
_P_INLINE = (
    "  let statistics := Array.replicate (nFeatures X) (effFill fillValue)\n"
    "  let mut xFilled : Array (Array Rat) := #[]\n"
    "  for row in X do\n"
    "    let mut newRow : Array Rat := #[]\n"
    "    for j in [0:row.size] do\n"
    "      let v := row[j]!\n"
    "      if v = missingValues then\n"
    "        newRow := newRow.push (effFill fillValue)\n"
    "      else\n"
    "        newRow := newRow.push v\n"
    "    xFilled := xFilled.push newRow\n"
    "  return { statistics := statistics, xFilled := xFilled }"
)

# (pos-explicit-loop) Build the per-feature statistic vector with an explicit
# forward-append loop — push the constant once per feature — instead of the
# bulk `Array.replicate`. Behaviorally identical (same size, same entries) but
# NOT definitionally equal: the field is a `forIn` over `[0:nFeatures X]`, so the
# frozen `unfold_fields` script fails with `rewrite ... did not find an occurrence
# of the pattern forIn`. Re-proved via `_RESHAPED_UNFOLD_TAIL`. This is the
# positive that actually tests whether the spec accepts a different SHAPE rather
# than a different spelling of the same term.
_P_EXPLICIT_LOOP = (
    "  let fill := effFill fillValue\n"
    "  let mut statistics : Array Rat := #[]\n"
    "  for _j in [0:nFeatures X] do\n"
    "    statistics := statistics.push fill\n"
    "  let mut xFilled : Array (Array Rat) := #[]\n"
    "  for row in X do\n"
    "    let mut newRow : Array Rat := #[]\n"
    "    for j in [0:row.size] do\n"
    "      let v := row[j]!\n"
    "      if v = missingValues then\n"
    "        newRow := newRow.push fill\n"
    "      else\n"
    "        newRow := newRow.push v\n"
    "    xFilled := xFilled.push newRow\n"
    "  return { statistics := statistics, xFilled := xFilled }"
)

# (pos-map-functional) Build the filled matrix FUNCTIONALLY: a nested
# `Array.map`, no accumulator, no index arithmetic, no `forIn` anywhere. This is
# the SPEC-TOO-STRONG control for the MATRIX half of the postcondition
# ((X1)/(X2)), which `pos-explicit-loop` does not touch — it reshapes only the
# `statistics` field. NOT definitionally equal to the frozen impl (the `rfl` probe
# fails) and the frozen script does not close it, so it is re-proved via
# `_MAPFUN_UNFOLD_TAIL`.
_P_MAP_FUNCTIONAL = (
    "  let fill := effFill fillValue\n"
    "  let statistics := Array.replicate (nFeatures X) fill\n"
    "  let xFilled := X.map"
    " (fun row => row.map (fun v => if v = missingValues then fill else v))\n"
    "  return { statistics := statistics, xFilled := xFilled }"
)


# ---------------------------------------------------------------------------
# Refutation witnesses. The carrier is transparent (Rat / Array / Option, no
# opaque callee), so each witness negates the spec predicate at a CONCRETE input
# and closes by evaluation. No witness binds a hypothesis, so there is nothing
# that could be jointly unsatisfiable and the gate's consistency probe never
# fires.
#
# ONE tactic shape is used for every witness, including those that attack only
# the statistics clauses (S1)/(S2). That is deliberate and load-bearing. A bare
# `unfold …; decide` is enough to prove the negation for a statistics rival —
# the false `statistics` conjunct short-circuits the outer `And` before the
# matrix conjunct is ever evaluated — but against the FROZEN solution the same
# script must evaluate the matrix conjunct, whose `Id.run`/`forIn` do-block
# `decide` cannot reduce. The gold-side build then fails with
# `failed to reduce to isTrue or isFalse` rather than by refuting anything, so
# its exit code attests to a refutation that never happened (the gate reports
# this as `witness-undecided`, and it is what an earlier revision of this file
# tripped on for all six statistics rivals).
#
# Handing the do-block reduction lemmas to `simp only` FIRST turns the matrix
# conjunct into a `foldl` over literal arrays, which `decide` does reduce. Every
# witness below therefore fails against gold by genuine refutation — verified as
# `Tactic 'decide' proved that the proposition … is false`, with no stuck
# reduction in the gold-side log — and elaborates against its own rival.
# Confirmed by building BOTH halves of all TWELVE pairs through the gate's own
# file surgery (pbt_witness.witness_file): rival exit 0, gold exit 1. Each pair
# was additionally FORGERY-tested — the same witness with its claim flipped
# (`¬ problem_spec …` -> `problem_spec …`) elaborates against gold (exit 0) and
# FAILS against its own rival (exit 1) with `decide` proving the flipped
# proposition false. So the gold-side exit code tracks the CLAIM, which is what
# distinguishes a refutation from a stuck kernel that would report exit 1 for a
# witness asserting gold is CORRECT there.
# ---------------------------------------------------------------------------

def _wit(x, mv, fv):
    """Negate the spec at a literal input, pre-reducing the impl's do-block."""
    args = f"({x} : Array (Array Rat)) {mv} {fv}"
    return (
        "example : ¬ problem_spec_initial_fill\n"
        f"    {args}\n"
        f"    (implementation_initial_fill {args}) := by\n"
        "  simp only [problem_spec_initial_fill, implementation_initial_fill, Id.run,\n"
        "    bind, pure, Array.forIn_yield_eq_foldl, Std.Range.forIn_eq_forIn_range',\n"
        "    List.forIn_yield_eq_foldl]\n"
        "  decide"
    )


# gold statistics = [100]; default-zero = [0]. Violates (S2) at j=0.
_WIT_DEFAULT_ZERO = _wit("#[#[(5:Rat)]]", "0", "(some 100)")
# fillValue=none: gold statistics = [0]; wrong-default = [100]. Violates (S2),
# varying the `fillValue` binder to none.
_WIT_WRONG_DEFAULT = _wit("#[#[(5:Rat)]]", "0", "none")
# 2-col so feature 1 stays correct: gold [100,100]; partial-first [0,100]. (S2) at j=0.
_WIT_PARTIAL_FIRST = _wit("#[#[(5:Rat), (6:Rat)]]", "0", "(some 100)")
# 2-col: gold [100,100]; partial-last [100,0]. (S2) at j=1.
_WIT_PARTIAL_LAST = _wit("#[#[(5:Rat), (6:Rat)]]", "0", "(some 100)")
# nFeatures = 1: gold statistics.size 1; len-long size 2. Violates (S1).
_WIT_LEN_LONG = _wit("#[#[(5:Rat)]]", "0", "(some 100)")
# nFeatures = 1: gold statistics.size 1; empty size 0. Violates (S1).
_WIT_EMPTY = _wit("#[#[(5:Rat)]]", "0", "(some 100)")
# sentinel present (mv=7): gold replaces 7 -> 100; no-replace keeps 7. (X2).
_WIT_NO_REPLACE = _wit("#[#[(7:Rat)]]", "7", "(some 100)")
# non-sentinel entry 5 (mv=7): gold keeps 5; clobber overwrites -> 100. Frame of (X2).
_WIT_CLOBBER = _wit("#[#[(5:Rat)]]", "7", "(some 100)")
# gold xFilled.size = 1; extra-row size 2. Violates (X1) row count.
_WIT_EXTRA_ROW = _wit("#[#[(5:Rat)]]", "0", "(some 100)")
# gold row size 1; row-long size 2. Violates (X1) per-row size.
_WIT_ROW_LONG = _wit("#[#[(5:Rat)]]", "0", "(some 100)")
# TWO rows, both a bare sentinel (mv=7): gold fills both -> [[100],[100]]; the
# rival fills row 0 only -> [[100],[7]]. So (X2) HOLDS at i=0 and fails at i=1 —
# the only witness point in this battery with more than one row.
_WIT_ROW_PARTIAL = _wit("#[#[(7:Rat)], #[(7:Rat)]]", "7", "(some 100)")
# 2-col, no sentinel present (mv=0): gold keeps [5,6]; the shifted rival emits
# [6, <out-of-range>] where row[2]! is the Rat default 0, so xFilled[0] = [6,0].
# Refuted at j=0, where 6 ≠ 5: both entries are drawn from the same input row, so
# only (X2)'s index identity is violated.
_WIT_SHIFT_COL = _wit("#[#[(5:Rat), (6:Rat)]]", "0", "(some 100)")


SPEC_TESTS = [
    # ---- soundness positives (must VERIFY; frozen proof body) ----
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _module(_P_RESHAPE),
        "rationale": (
            "a correct local-variable reshape: carry `fillValue` through an "
            "intermediate local before resolving the effective constant, same "
            "computation different shape. `fv` is definitionally `fillValue`, so "
            "the frozen proof closes verbatim and every clause (S1)/(S2)/(X1)/(X2) "
            "holds. WEAK positive, honestly labelled: this impl is DEFINITIONALLY "
            "EQUAL to the frozen one (`@implementation_alt = "
            "@implementation_initial_fill := rfl` elaborates), so it cannot detect "
            "a spec over-fit to the frozen spelling — there is no difference for "
            "the kernel to see. It pins only that the obligation is satisfiable. "
            "`pos-explicit-loop` is the load-bearing SPEC-TOO-STRONG control. No "
            "new declaration, axiom, or assumption token; the theorem STATEMENT is "
            "byte-identical."
        ),
    },
    {
        "id": "pos-inline-eff",
        "kind": "soundness",
        "expect": "verify",
        "module": _module(_P_INLINE),
        "rationale": (
            "a correct reshape that drops the `fill` binding and inlines "
            "`effFill fillValue` at both use sites — definitionally identical, so "
            "the frozen proof body closes verbatim. Same WEAK tier as "
            "`pos-local-reshape` and labelled the same way: the `rfl` defeq probe "
            "against the frozen impl elaborates, so passing here tests that the "
            "obligation is satisfiable, NOT that the spec tolerates a different "
            "shape. The theorem STATEMENT is byte-identical and no new "
            "declaration/axiom is introduced."
        ),
    },
    {
        "id": "pos-explicit-loop",
        "kind": "soundness",
        "expect": "verify",
        "module": _module(_P_EXPLICIT_LOOP, _RESHAPED_UNFOLD_TAIL),
        "rationale": (
            "THE SPEC-TOO-STRONG control, and the only positive here that is not "
            "definitionally equal to the frozen impl. Builds the per-feature "
            "statistic vector by an explicit forward-append loop (push the constant "
            "once per feature) instead of the bulk `Array.replicate`: same size, "
            "same entries, genuinely different term. Measured: the `rfl` defeq probe "
            "against the frozen impl FAILS, and the FROZEN tactic body does not "
            "close it either (`rewrite ... did not find an occurrence of the "
            "pattern forIn` inside `unfold_fields`) — which is exactly the "
            "confound this battery's witnesses exist to separate, since a correct "
            "reshape breaking the frozen script looks identical to a wrong impl "
            "doing so. Re-proved by supplying the missing induction (the append "
            "loop's closed form equals `Array.replicate`) INLINE as a `have`, so no "
            "new top-level theorem is declared; every other lemma and "
            "`correct_initial_fill` itself keep the frozen script, and every "
            "theorem STATEMENT is byte-identical. Must verify: a faithful correct "
            "impl the spec REJECTED on shape alone would be a soundness hole in "
            "the spec => SPEC-TOO-STRONG."
        ),
    },

    {
        "id": "pos-map-functional",
        "kind": "soundness",
        "expect": "verify",
        "module": _module(_P_MAP_FUNCTIONAL, _MAPFUN_UNFOLD_TAIL),
        "rationale": (
            "the SECOND SPEC-TOO-STRONG control, and the one that covers the half "
            "of the spec `pos-explicit-loop` leaves untested. `pos-explicit-loop` "
            "reshapes only the `statistics` field; the matrix clauses (X1)/(X2) are "
            "the larger half of this postcondition, and before this case every "
            "positive built `xFilled` with the frozen impl's own nested "
            "`for`/`push` accumulation — so nothing tested whether (X1)/(X2) accept "
            "a differently-SHAPED matrix computation, which is precisely the "
            "over-fit a soundness positive exists to detect. This impl drops both "
            "loops and computes the matrix functionally as `X.map (fun row => "
            "row.map (fun v => if v = missingValues then fill else v))`: no "
            "accumulator, no index arithmetic, no `forIn`. Measured: the `rfl` defeq "
            "probe against the frozen impl FAILS (exit 1), so this is a genuinely "
            "different term and not a spelling variant; and the FROZEN tactic body "
            "does not close it either (`rewrite ... did not find an occurrence of "
            "the pattern forIn` inside `unfold_fields`) — the same confound the "
            "witnesses exist to separate, since a correct reshape breaking the "
            "frozen script is indistinguishable from a wrong impl doing so. "
            "Re-proved by supplying INLINE as a `have` the identification of "
            "`Array.map` on a row with `mapRow`'s `foldl` closed form (an "
            "`Array.ext'` / `List.ext_getElem` argument over the row's indices with "
            "the `getElem!_pos` bridge — a real proof, not a restatement of the "
            "goal), so no new top-level theorem is declared; every downstream lemma "
            "and `correct_initial_fill` itself keep the frozen script, and every "
            "theorem STATEMENT is byte-identical. Must verify: a faithful correct "
            "impl the spec REJECTED because it computes the matrix without a loop "
            "would be a soundness hole => SPEC-TOO-STRONG."
        ),
    },

    # ---- admissibility (must VERIFY; the PRECOND-TOO-STRONG lane) ----
    {
        "id": "admiss-ground-matrix",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _P_INTRO, _ADMISS_GROUND + _P_INTRO),
        "rationale": (
            "the PRECOND-TOO-STRONG lane. An earlier revision of this file recorded "
            "this lane as VACUOUS on lean, on the argument that the obligation's "
            "rectangularity hypothesis is establishable for every F2P-shaped input "
            "and the proof never consumes it, so there is no precondition clause a "
            "normal input fails. That argument confuses the hypothesis with the "
            "lane: on a total carrier the analogue of PRECOND-TOO-STRONG is the "
            "obligation being UNSATISFIABLE at a normal input — the hypothesis "
            "holding but the conclusion not — and nothing about a total carrier "
            "makes that automatic. It is expressible here and is now tested. The "
            "impl is the frozen one byte-for-byte; the case prepends a ground "
            "`have` at the F2P-shaped input (a rectangular 2x3 `Rat` matrix, "
            "sentinel 7 PRESENT in both rows so the replacement arm of (X2) fires "
            "rather than only the frame arm, supplied constant 100 distinct from "
            "every entry) discharging BOTH the rectangularity hypothesis (`by "
            "decide`) AND the full spec predicate at that input, by evaluation. "
            "Nothing is assumed: no new declaration, no axiom, no `sorry`, the "
            "obligation STATEMENT is byte-identical and the frozen tactic body "
            "follows the `have` unchanged. Must verify: a rejection would say the "
            "modeled behavior cannot satisfy its own spec at exactly a normal "
            "input, which is the PRECOND-TOO-STRONG finding. Measured: verifies "
            "(exit 0), `variant_scope` clean."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED; each carries a witness) ----
    {
        "id": "weak-default-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _module(_R_DEFAULT_ZERO),
        "refinement": (
            "this is the pre-fix behavior verbatim: the first-round inner imputer "
            "is built WITHOUT the user's chosen constant, so the per-feature fill "
            "statistic defaults to the neutral numerical 0 for every feature. With "
            "the F2P's supplied value of 100 the observed statistics would be all "
            "zeros while the test asserts they equal 100, so the F2P FAILS and it "
            "does NOT resolve. A verifying rival here is a true "
            "verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECT from clause (S2): for a supplied value (some 100) every feature "
            "statistic must equal effFill fillValue = 100, but the rival installs 0. "
            "Witness at X=#[#[5]], missingValues=0, fillValue=some 100: gold "
            "statistics = [100], rival = [0], so (S2) is violated at j=0. Built both "
            "ways (rival exit 0, gold exit 1)."
        ),
        "witness": _WIT_DEFAULT_ZERO,
    },
    {
        "id": "weak-wrong-default",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _module(_R_WRONG_DEFAULT),
        "refinement": (
            "a faithful patch that forwards a supplied constant but resolves the "
            "MISSING (None) case to the wrong numerical default (100 instead of 0) "
            "produces the wrong statistics on every default-constant fit; the "
            "regression / default-fill tests observe statistics_ == 0 for numerical "
            "data with no fill_value and would FAIL — it does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause (S2) on the DEFAULT arm of effFill: at "
            "fillValue=none the statistic must be effFill none = 0, but the rival "
            "installs 100. The ONLY rival that varies the `fillValue` binder off "
            "`some _`, so the spec pins BOTH arms of `fillValue.getD 0`. Witness at "
            "X=#[#[5]], missingValues=0, fillValue=none: gold statistics = [0], "
            "rival = [100]. Built both ways (rival exit 0, gold exit 1)."
        ),
        "witness": _WIT_WRONG_DEFAULT,
    },
    {
        "id": "weak-partial-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _module(_R_PARTIAL_FIRST),
        "refinement": (
            "a faithful patch that special-cases the first feature (forces its "
            "statistic to 0 / skips index 0 while propagating) leaves the first "
            "per-feature fill at 0 while the rest are correct; assert_array_equal "
            "compares every entry, so the F2P FAILS on the first feature — it does "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT from clause (S2) at j=0: after corrupting feature 0 the "
            "statistic is 0, but the spec requires effFill fillValue (100). Witness "
            "at a 2-column matrix (feature 1 stays correct, isolating j=0): gold "
            "statistics = [100,100], rival = [0,100]. Built both ways (rival exit 0, "
            "gold exit 1)."
        ),
        "witness": _WIT_PARTIAL_FIRST,
    },
    {
        "id": "weak-partial-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _module(_R_PARTIAL_LAST),
        "refinement": (
            "a faithful patch with an off-by-one that stops one feature short "
            "leaves the final per-feature statistic at the default 0; the F2P's "
            "multi-feature array is compared entry-by-entry and FAILS on the last "
            "feature — it does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause (S2) at j=nFeatures-1: the corrupting write sets the "
            "last statistic to 0, but the spec requires effFill fillValue (100). "
            "Witness at a 2-column matrix: gold statistics = [100,100], rival = "
            "[100,0]. Varies the corrupted index off `weak-partial-first`'s j=0, "
            "pinning (S2) at both ends of the range. Built both ways (rival exit 0, "
            "gold exit 1)."
        ),
        "witness": _WIT_PARTIAL_LAST,
    },
    {
        "id": "weak-stats-len-long",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _module(_R_LEN_LONG),
        "refinement": (
            "a faithful patch that over-allocates the per-feature statistic array "
            "by one (off-by-one) yields a statistics_ of shape (n+1,) while the data "
            "has n features; assert_array_equal against the data shape and the "
            "downstream fit_transform require shape (n,) and FAIL on the mismatch — "
            "it does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause (S1): statistics.size must equal nFeatures X, but "
            "the rival has nFeatures X + 1 entries. Clause (S2) holds (every entry "
            "is the right value), isolating the length clause. Witness at X=#[#[5]] "
            "(nFeatures 1): gold statistics.size = 1, rival = 2. Built both ways "
            "(rival exit 0, gold exit 1)."
        ),
        "witness": _WIT_LEN_LONG,
    },
    {
        "id": "weak-stats-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _module(_R_EMPTY),
        "refinement": (
            "a faithful patch that returns an empty / unpopulated statistics_ "
            "installs no per-feature constant at all; the F2P reads the statistic "
            "vector and assert_array_equal against the fill value FAILS on the empty "
            "array (and fit_transform breaks) — it does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause (S1): statistics.size must equal nFeatures X, but "
            "the rival is empty. (S2) fails TOO, and the earlier claim that it is "
            "'vacuously true over the empty vector' was WRONG — machine-checked: "
            "(S2) quantifies over `j < nFeatures X`, the INPUT's feature count, "
            "which is 1 here, so j=0 is in range and the rival's out-of-bounds "
            "`#[][0]!` is the Rat default 0 ≠ 100. `¬(S2)` is provable by decide "
            "against this rival (exit 0) and `(S2)` is NOT (exit 1). So this case "
            "does not isolate the size clause; `weak-stats-len-long` is the rival "
            "that does (there (S2) genuinely holds — verified by decide — and only "
            "(S1) fails). Kept as an independent (S1) attack at a different point "
            "of the size clause (0 vs n+1). Witness at X=#[#[5]] (nFeatures 1): "
            "gold statistics.size = 1, rival = 0. Built both ways (rival exit 0, "
            "gold exit 1)."
        ),
        "witness": _WIT_EMPTY,
    },
    {
        "id": "weak-xfilled-no-replace",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _module(_R_NO_REPLACE),
        "refinement": (
            "a faithful patch that forwards the input matrix untouched (never "
            "substituting the per-feature constant for a missing entry) leaves the "
            "sentinel-valued cells in the round-zero output; the imputed matrix then "
            "still contains the missing marker and the transform / end-to-end tests "
            "that read back the filled values FAIL — it does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause (X2): a sentinel-valued entry must be replaced by "
            "effFill fillValue, but the rival forwards it unchanged. Witness at "
            "X=#[#[7]], missingValues=7, fillValue=some 100 (the single entry IS the "
            "sentinel): gold xFilled = [[100]], rival = [[7]]. Varies the "
            "`missingValues` binder to 7 (present in the data). Built both ways "
            "(rival exit 0, gold exit 1)."
        ),
        "witness": _WIT_NO_REPLACE,
    },
    {
        "id": "weak-xfilled-clobber",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _module(_R_CLOBBER),
        "refinement": (
            "a faithful patch that overwrites EVERY entry with the fill constant "
            "(not just the missing ones) destroys the observed non-missing data; the "
            "end-to-end imputation tests read back originally-present values and FAIL "
            "when they have been clobbered by the constant — it does NOT resolve."
        ),
        "rationale": (
            "REJECT from the FRAME half of clause (X2): a NON-sentinel entry must be "
            "left equal to its input value (the `else X[i]![j]!` arm), but the rival "
            "overwrites it with the constant. This is the frame obligation, "
            "discharged structurally here rather than via permissions. Witness at "
            "X=#[#[5]], missingValues=7, fillValue=some 100 (entry 5 is NOT the "
            "sentinel): gold xFilled = [[5]], rival = [[100]]. Built both ways "
            "(rival exit 0, gold exit 1)."
        ),
        "witness": _WIT_CLOBBER,
    },
    {
        "id": "weak-xfilled-extra-row",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _module(_R_EXTRA_ROW),
        "refinement": (
            "a faithful patch that emits one extra sample row in the filled matrix "
            "yields an X_filled of shape (n_samples+1, …) mismatching the input; the "
            "downstream iterative fit and the shape-checking tests FAIL — it does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from clause (X1): xFilled.size must equal X.size, but the rival "
            "appends a spurious row. Witness at X=#[#[5]] (X.size 1): gold "
            "xFilled.size = 1, rival = 2. Built both ways (rival exit 0, gold "
            "exit 1)."
        ),
        "witness": _WIT_EXTRA_ROW,
    },
    {
        "id": "weak-xfilled-row-long",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _module(_R_ROW_LONG),
        "refinement": (
            "a faithful patch that appends a spurious column to every filled row "
            "yields an X_filled with one extra feature per sample; the shape no "
            "longer matches the input and the downstream fit / shape tests FAIL — it "
            "does NOT resolve."
        ),
        "rationale": (
            "REJECT from the per-row half of clause (X1): each filled row's size "
            "must equal the input row's size, but the rival makes each row one entry "
            "longer. Witness at X=#[#[5]] (row size 1): gold xFilled[0].size = 1, "
            "rival = 2. Built both ways (rival exit 0, gold exit 1)."
        ),
        "witness": _WIT_ROW_LONG,
    },
    {
        "id": "weak-xfilled-row-partial",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _module(_R_ROW_PARTIAL),
        "refinement": (
            "a faithful patch that substitutes the per-feature constant while "
            "building the first sample row but forwards the remaining rows "
            "unchanged (an accumulator guard that only fires on the first "
            "iteration) leaves the missing marker in every sample after the first; "
            "the round-zero matrix handed to the iterative fit still contains "
            "sentinels below row 0, and the end-to-end tests that read back the "
            "filled values FAIL on those rows — it does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause (X2) at i=1, the OUTER binder. Every other reject "
            "case in this battery is refuted on a single-row matrix, so (X2)'s row "
            "quantifier was pinned at exactly one point (i=0) and a rival correct on "
            "the first row only would have slipped by. Witness at "
            "X=#[#[7],#[7]], missingValues=7, fillValue=some 100 (two rows, each a "
            "bare sentinel): gold xFilled = [[100],[100]], rival = [[100],[7]], so "
            "(X2) HOLDS at i=0 and fails at i=1 — the discrimination is genuinely "
            "about the row index and not about the replacement rule. Built both "
            "ways (rival exit 0, gold exit 1) and the flipped claim reverses both "
            "exit codes."
        ),
        "witness": _WIT_ROW_PARTIAL,
    },
    {
        "id": "weak-xfilled-shift-col",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _module(_R_SHIFT_COL),
        "refinement": (
            "a faithful patch with an off-by-one in the column index reads each "
            "row one feature over, so every filled row is a shift of the input row "
            "(its last feature falling off the end and reading as the neutral "
            "default). The values are all real values from the same sample, so "
            "nothing about the fill rule looks wrong, but each feature's column is "
            "displaced; the shape-preserving equality checks on the imputed matrix "
            "compare per-column and FAIL — it does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause (X2)'s INDEX IDENTITY, the inner binder read as an "
            "index rather than as a value. This is the subtlest rival here and it is "
            "the one that shows (X2) is doing more than the other xFilled cases "
            "test: every entry the rival emits IS a genuine entry of the SAME input "
            "row, and the sentinel test is applied to it faithfully, so the rival "
            "violates nothing about membership, multiset content, or the replacement "
            "rule — only the pinning of output entry j to INPUT entry j. Witness at "
            "X=#[#[5,6]], missingValues=0, fillValue=some 100 (no sentinel present, "
            "isolating the frame arm): gold xFilled = [[5,6]], rival = [[6,0]] (the "
            "shifted read of row[2]! is the Rat default), refuted at j=0 where "
            "6 ≠ 5. No other rival moves the column index. Built both ways (rival "
            "exit 0, gold exit 1) and the flipped claim reverses both exit codes."
        ),
        "witness": _WIT_SHIFT_COL,
    },
]


# Axiom lane is G-AX's job, not this gate's; the nagini AXIOM_TESTS are dropped.
AXIOM_TESTS = []
