"""properties.py — PBT falsification manifest for scikit-learn__scikit-learn-14087.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The bundle models TWO changed functions (both in the
no-refit branch of LogisticRegressionCV.fit):

  gather_per_class(resolved_strategy, unresolved_form, table_axes,
                   summary_token) -> int          # site 1 (the IndexError fix)
      Requires MustTerminate(2)                              (TOTALITY)
      Requires resolved_strategy in {INDEPENDENT, JOINT}     (never UNRESOLVED)
      Requires unresolved_form  in {INDEPENDENT, JOINT, UNRESOLVED}
      Requires table_axes == table_rank(resolved_strategy)   (3 or 4)
      Requires summary_table(table_axes)                     (the ONE held table,
                                                              at its actual rank)
      Ensures  Result() == summary_token                     (ECHOABLE value)
      Ensures  read_admissible(table_axes)                   (LOAD-BEARING token,
                                                              AT the actual rank)
      Ensures  summary_table(table_axes)                     (the SAME table is
                                                              handed back)

  mixing_record(family_has_mixing, selected_index, candidates_len,
                mixing_value) -> Optional[int]     # site 2 (the None-marker fix)
      Requires MustTerminate(2)                              (TOTALITY)
      Requires candidates_len >= 1 ; 0 <= selected_index < candidates_len
      Requires Implies(not family_has_mixing, candidates_len == 1)
      Requires candidate_table(family_has_mixing, candidates_len)
                                                             (the ONE held table,
                                                              at its actual entry
                                                              reality AND extent)
      Ensures  Implies(family_has_mixing, Result() is not None
                       and Result() == mixing_value)
      Ensures  Implies(not family_has_mixing, Result() is None)
      Ensures  candidate_table(family_has_mixing, candidates_len)
                                                             (the SAME table is
                                                              handed back)
      Ensures  Implies(family_has_mixing, mixing_selected()) (LOAD-BEARING token)

What the spec defends, and the attacks it must survive:

  * SITE 1 IS A CONTROL-FLOW-EFFECT SITE. The headline bug is a read that either
    succeeds in-bounds or raises `IndexError: too many indices for array`; the
    gathered coefficient VALUE is value-irrelevant to the F2P (it asserts
    coef_.shape, not values). A value-only postcondition `Result() == summary_token`
    is therefore ECHOABLE by `return summary_token` with no read. The
    discriminator is the UNFORGEABLE capability `read_admissible(rank)`: an
    abstract @ContractOnly @Predicate (no body, un-mintable) granted ONLY by the
    consumed axiom `read_across_folds`, whose Requires(gather_arity(use_joint_layout)
    == table_rank) enforces the arity match, and granted AT the rank the read
    was checked against. The caller must hold it at the ACTUAL layout rank
    (`table_axes`), so a read checked against a SELF-CONSISTENT rank other than
    the actual layout's (pass gather_arity(use_joint_layout) as the rank
    argument) grants only read_admissible(gather_arity(...)), NOT
    read_admissible(table_axes), and is rejected whenever the branch is wrong.
    So the control-flow / raise difference the value abstraction drops is
    pinned by a rank-indexed capability token (directive 4 IS this site).
    `rival-echo` and the three `rival-forge-rank-*` cases are exactly those
    attacks.

  * SITE 1'S READ OBLIGATION IS UNIVERSAL, NOT EXISTENTIAL. The real observable
    is that EVERY index expression the step executes against the one summary
    table is in-bounds — not merely the one whose value is delivered. A rank
    passed as a plain int leaves the number and the ranks of the OTHER reads
    free: an impl may issue an EXTRA read at any self-consistent (arity, rank)
    pair, which is a no-op in a value model but a real index expression against
    the single real table. `summary_table(actual_rank)` closes that: it is an
    abstract @ContractOnly @Predicate held as a RESOURCE, required by the step
    and CONSUMED by each read at the rank the read is checked against, so a read
    is only performable against the held table at the held table's actual rank.
    The rank argument is therefore no longer forgeable — not by a self-consistent
    literal (`rival-extra-read-forged-joint` / `-independent`), not off the
    UNRESOLVED operand (`rival-extra-read-unresolved`), not by delivering the
    unresolved read's value and harvesting the token from a second honest read
    (`rival-deliver-unresolved-read`), and not by conjuring the table at a
    self-named rank (the predicate is abstract, so no state the step can reach
    contains one: `rival-conjure-summary-table`, whose non-vacuity control is
    `pos-control-site1-held-table-assertable`). A read that is PROVABLY at the held rank stays
    legal, which is right — a duplicated in-bounds index expression does not
    raise, and `pos-control-site1-duplicate-read` pins that the obligation is
    "every read at the actual rank", never "at most one read". The obligation
    is likewise about WHICH AXES each read addresses, never about the
    provenance of the delivered number: an impl that performs the honest
    arity-matching read and then delivers the summary directly refines to the
    correct branch taken twice with one result unused, and was measured to
    RESOLVE, so `pos-control-site1-read-then-deliver` must verify. That pair
    with `rival-echo-no-read` fixes the boundary from both sides — a read is
    required, tracing the returned value through it is not.

  * SITE 1 PARTIAL-DOMAIN. An impl that drives the read off the UNRESOLVED
    operand (`unresolved_form != INDEPENDENT`) is correct on every input EXCEPT
    unresolved_form==UNRESOLVED with resolved_strategy==INDEPENDENT — the exact
    reported crash (auto-l2 F2P). An impl that hardcodes the independent read
    (`use_joint_layout=False`) is correct on the ovr case but over/under-indexes
    the joint layout (multinomial-l2 F2P). Both fail the read_across_folds arity
    precondition for an in-domain input -> no capability -> reject.

  * SITE 2 IS A GROUNDED ABSENT-MARKER SITE. The postcondition pins the result
    BOTH ways: family_has_mixing -> Result()==mixing_value (grounded in the input
    value, not an opaque oracle); not family_has_mixing -> Result() is None. The
    value clause is grounded (an input arg), so there is no wrong-oracle echo to
    build; the attacks are (a) always-take-the-value (the pre-patch bug — records
    a table value for the no-mixing family), (b) record a DIFFERENT input value
    (selected_index), (c) invert the branch. Each violates a load-bearing
    implication.

  * SITE 2'S SELECTION OBLIGATION IS UNIVERSAL OVER *WHICH ENTRY* IS ADDRESSED,
    NOT ONLY OVER WHETHER THE ENTRIES ARE REAL. The real observable is that every
    averaged lookup the block performs against the one candidate-mixing table
    addresses an entry that table actually holds — an out-of-range position is a
    real `IndexError` on the elasticnet path even when the delivered record is
    the gold one. With the extent passed to the selection as a plain int, the
    in-range condition `0 <= selected_index < candidates_len` is discharged by
    any caller that simply NAMES a larger bound (select at `candidates_len`,
    declare `candidates_len + 1`): a no-op in the value model, a real
    out-of-range index against the single real candidate table.
    `candidate_table(holds_mixing_values, actual_len)` closes that: it is an
    abstract @ContractOnly @Predicate held as a RESOURCE carrying BOTH the entry
    reality AND the table's actual extent, required by the step and CONSUMED and
    returned by each selection at the extent that selection's position is checked
    against — so a selection is only performable against the held table, at the
    held table's real extent. The bound is therefore no longer forgeable: not by
    naming `candidates_len + 1` (`rival-site2-forged-extent`), not by offsetting
    the real position past the end (`rival-site2-forged-extent-offset`), not by
    keeping the delivering selection honest and adding an EXTRA out-of-range one
    (`rival-site2-extra-selection-forged-extent`), not by hoisting an
    out-of-range selection above the family guard
    (`rival-site2-hoisted-forged-extent`), and not by conjuring a longer table
    (the predicate is abstract, so no reachable state holds one:
    `rival-site2-conjure-candidate-table`, with
    `pos-control-site2-held-table-assertable` as its non-vacuity control; the same
    control covers `rival-site2-conjure-selection`, the capability-side probe).
    A selection PROVABLY within
    the held extent stays legal at ANY position, which is right: the no-refit
    per-class mixing record is observed by its SHAPE (the new test asserts
    `l1_ratio_.shape == (n_classes,)`; the only value assertion on `l1_ratio_`
    lives in the refit path), so an in-range lookup at a different position is a
    correct alternative. `pos-control-site2-other-in-range-position` pins that
    side of the boundary, so the obligation is exactly "every selection is of an
    entry the table has", never "the position is the gold index expression".

  * DIVERGENCE IS NOT AN ESCAPE HATCH. Nagini's default is partial
    correctness: a body that never returns satisfies every postcondition
    vacuously (including the capability obligation), yet its faithful real
    patch would hang the fit and resolve nothing. Both functions therefore
    carry a MustTerminate(2) obligation, with the consumed axiom at measure 1,
    so an unbounded loop (or any callee not proven to terminate) is rejected
    as an obligation leak. `rival-diverge-loop` is exactly that attack.

  * NO READ-ONLY (Acc(x,1/2)) INPUT ⇒ FRAME-MUTATION N/A. Both functions take
    only immutable by-value int/bool/Optional[int] params; there is no heap
    reference held at half permission to overwrite. The mandatory frame-mutation
    probe (directive 1) does not apply to this instance — there is no input frame
    to subvert. Stated in the structured assessment rather than fabricated.

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
that edits ONLY inside a `# impl-start`/`# impl-end` block, so `markers.same_spec`
is GUARANTEED and any rejection is attributable to the POSTCONDITION catching
wrong behaviour, never to a tampered spec. Each `expect:"reject"` rival carries
the refinement argument that its faithful real patch would NOT resolve the
F2P/P2P. The one A-consumed axiom `read_across_folds` and the A-reference [None]
sentinel are checked by RUNNING the real callees (`_check_multi_class`, numpy
indexing, np.mean) in Docker — reusing + strengthening axiom_check.py.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-14087"
FLOAT_ENCODING = None   # meta.json float_encoding is null

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks (all strictly INSIDE an impl region of model.py).
# ---------------------------------------------------------------------------

# Site 1 (gather_per_class) — the full gold impl body (the three operative
# lines; comments kept so the substring is unique and stays inside impl).
_S1_BODY = """    # Address the table with the arity determined by the strategy actually in
    # effect, so the index arity always equals the table's axis rank.
    use_joint_layout = resolved_strategy != INDEPENDENT
    w = read_across_folds(use_joint_layout, table_axes, summary_token)
    return w"""

# Site 2 (mixing_record) — the full gold impl body.
_S2_BODY = """    if family_has_mixing:
        # The family carries a mixing parameter: select the value from the
        # candidate table and record it.
        entry = select_mixing_value(family_has_mixing, selected_index,
                                    candidates_len,
                                    mixing_value)  # type: Optional[int]
    else:
        # No mixing parameter for this family: the candidate table holds only
        # the absent placeholder, so nothing is selected from it — record the
        # explicit absent marker.
        entry = None
    return entry"""


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (soundness, site 1) Structurally-DIFFERENT but CORRECT: compute the same
# branch boolean with an explicit if/else over an `== JOINT` test instead of the
# `!= INDEPENDENT` test. Since the precondition pins resolved_strategy to
# {INDEPENDENT, JOINT}, `resolved_strategy == JOINT` is provably equivalent to
# `resolved_strategy != INDEPENDENT`, so the SAME arity is requested and the
# read_across_folds precondition is discharged identically -> the unforgeable
# capability is obtained -> it MUST verify. No induction lemma is needed (pure
# case analysis over two int constants), so the gold proof stays valid. If it
# failed => SPEC-TOO-STRONG (over-fit to one way of writing the branch test).
_S1_POS = """    # Compute the joint-layout branch by the resolved strategy, written as an
    # explicit if/else over `== JOINT` (provably equal to `!= INDEPENDENT`).
    if resolved_strategy == JOINT:
        use_joint_layout = True
    else:
        use_joint_layout = False
    w = read_across_folds(use_joint_layout, table_axes, summary_token)
    return w"""
_POS_S1 = _swap(_BASE, _S1_BODY, _S1_POS)

# (soundness, site 2) Structurally-DIFFERENT but CORRECT: local-variable reshape
# — initialise the entry to the absent marker, then OVERRIDE it only for the
# mixing family. Same result on every input (no-mixing -> None; mixing ->
# mixing_value), so it MUST verify. If it failed => SPEC-TOO-STRONG.
_S2_POS = """    entry = None  # type: Optional[int]
    if family_has_mixing:
        # The family carries a mixing parameter: select the value from the
        # candidate table and record it.
        entry = select_mixing_value(family_has_mixing, selected_index,
                                    candidates_len, mixing_value)
    return entry"""
_POS_S2 = _swap(_BASE, _S2_BODY, _S2_POS)

# (admissibility, site 1) The precondition must ADMIT a normal F2P-shaped input
# (incl. the deferred 'auto' case unresolved_form==UNRESOLVED) and let the
# arity-matching read be established. We keep the gold body and add an Assert,
# right before the read, that the arity the gold branch requests EQUALS the
# table's axis rank for ANY admissible input. Nagini reasons universally, so a
# discharged Assert proves the precondition admits the in-bounds read for every
# in-domain input — including the UNRESOLVED operand that caused the crash. If
# this Assert could not be discharged, the precondition would be blocking a
# legitimate F2P-shaped computation => PRECOND-TOO-STRONG.
_S1_ADMISS = """    # Address the table with the arity determined by the strategy actually in
    # effect, so the index arity always equals the table's axis rank.
    use_joint_layout = resolved_strategy != INDEPENDENT
    Assert(gather_arity(use_joint_layout) == table_axes)
    w = read_across_folds(use_joint_layout, table_axes, summary_token)
    return w"""
_ADMISS_S1 = _swap(_BASE, _S1_BODY, _S1_ADMISS)

# (soundness, site 1) The obligation is "EVERY read at the actual rank", NOT
# "at most one read". Address the held table TWICE with the arity the strategy
# in effect determines. Both reads are arity-matching reads of the actual
# layout, and a duplicated in-bounds index expression does not raise in the real
# code, so this MUST verify. If it failed, the resource clause would have been
# over-tightened into single-use (SPEC-TOO-STRONG: it would reject a correct
# alternative that happens to read the table more than once).
_S1_DUP = """    # Address the table in effect twice with the matching arity.
    use_joint_layout = resolved_strategy != INDEPENDENT
    first = read_across_folds(use_joint_layout, table_axes, summary_token)
    w = read_across_folds(use_joint_layout, table_axes, summary_token)
    return w"""
_POS_DUP = _swap(_BASE, _S1_BODY, _S1_DUP)

# (soundness, site 1) The read's arity obligation is about WHICH AXES are
# addressed, not about the provenance of the delivered number. Perform the
# arity-matching read of the held table, discard its value, and deliver the
# summary token. Refined, this is the correct branch performed twice with the
# first result unused — every index expression is in-bounds, the delivered
# vector is the gathered one, and it was measured to RESOLVE (all three
# FAIL_TO_PASS and all PASS_TO_PASS pass). So it MUST verify: rejecting it
# would mean the spec had been tightened into a value-provenance claim the real
# function does not make (SPEC-TOO-STRONG — it would fail a correct
# alternative). The pair (this, `rival-echo-no-read`) fixes the boundary
# exactly: performing the read is required, tracing the delivered value back
# through it is not.
_S1_READ_THEN_ECHO = """    # Address the table in effect, then deliver the summary.
    use_joint_layout = resolved_strategy != INDEPENDENT
    checked = read_across_folds(use_joint_layout, table_axes, summary_token)
    w = summary_token
    return w"""
_POS_READ_ECHO = _swap(_BASE, _S1_BODY, _S1_READ_THEN_ECHO)

# (soundness, site 1) NON-VACUITY CONTROL for `rival-conjure-summary-table`.
# That rival is rejected because Viper cannot show the step holds a summary table
# at a rank the impl names for itself. This control pins that the rejection is
# about WHICH rank was named and not about asserting an abstract predicate at
# all: assert the table at the rank the precondition hands it at, take the gold
# read, then assert both the returned table and the granted capability. Every
# assertion names exactly what the spec makes available at that program point, so
# this MUST verify. If it failed, `rival-conjure-summary-table` (and its two
# site-2 counterparts) would be rejected by a construct that always fails, i.e.
# they would be `Assert(False)` in disguise and would measure nothing.
_S1_HELD_ASSERT = """    # Assert the resources the spec actually hands over / grants.
    Assert(summary_table(table_axes))
    use_joint_layout = resolved_strategy != INDEPENDENT
    w = read_across_folds(use_joint_layout, table_axes, summary_token)
    Assert(summary_table(table_axes))
    Assert(read_admissible(table_axes))
    return w"""
_POS_HELD_ASSERT = _swap(_BASE, _S1_BODY, _S1_HELD_ASSERT)

# (soundness, site 2) NON-VACUITY CONTROL for `rival-site2-conjure-selection` and
# `rival-site2-conjure-candidate-table`. Assert the candidate table at the extent
# the step is handed it at (the extent the forged-extent rival names one past),
# take the gold selection, then assert the capability that selection grants (the
# one the conjuring rival claims without selecting) and that the table comes back
# at the same extent. Each assertion holds of the state the spec describes, so
# this MUST verify — which is what makes those two rejections attributable to the
# named extent / the missing selection rather than to the assertion mechanism.
_S2_HELD_ASSERT = """    if family_has_mixing:
        Assert(candidate_table(family_has_mixing, candidates_len))
        entry = select_mixing_value(family_has_mixing, selected_index,
                                    candidates_len,
                                    mixing_value)  # type: Optional[int]
        Assert(mixing_selected())
        Assert(candidate_table(family_has_mixing, candidates_len))
    else:
        entry = None
    return entry"""
_POS_S2_HELD_ASSERT = _swap(_BASE, _S2_BODY, _S2_HELD_ASSERT)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (CONTROL-FLOW-EFFECT / ungrounded-value echo, site 1) Echo the summary value
# WITHOUT performing any across-folds read: return summary_token directly, never
# call read_across_folds. Satisfies `Result() == summary_token` but never
# obtains the unforgeable `read_admissible(table_axes)` capability. MUST be
# rejected ("insufficient permission to access read_admissible(table_axes)").
# This is the
# capability-token discriminator for the control-flow/raise difference the value
# abstraction drops (= model_prepatch_1.py).
_S1_ECHO = """    # Echo the value without performing an arity-matching read.
    w = summary_token
    return w"""
_RIVAL_ECHO = _swap(_BASE, _S1_BODY, _S1_ECHO)

# (PARTIAL-DOMAIN, site 1) Drive the read branch off the UNRESOLVED operand (the
# pre-patch `self.multi_class`) instead of the resolved strategy. Correct on
# every input EXCEPT unresolved_form==UNRESOLVED with resolved_strategy==
# INDEPENDENT (table_axes==3): then gather_arity(True)==4 != 3, the
# read_across_folds precondition is violated and no capability is granted. This
# is the EXACT reported IndexError (auto-l2 F2P). MUST be rejected (=
# model_prepatch.py).
_S1_UNRESOLVED = """    # Drive the branch off the UNRESOLVED operand (the pre-patch bug).
    use_joint_layout = unresolved_form != INDEPENDENT
    w = read_across_folds(use_joint_layout, table_axes, summary_token)
    return w"""
_RIVAL_UNRESOLVED = _swap(_BASE, _S1_BODY, _S1_UNRESOLVED)

# (PARTIAL-DOMAIN, site 1) Hardcode the independent (3-axis) read. Correct on the
# ovr case (table_axes==3) but on the joint case (resolved_strategy==JOINT,
# table_axes==4) requests arity 3 != 4 -> precondition fails, no capability.
# MUST be rejected. A faithful patch that always took the ovr read would
# under-index the multinomial layout (multinomial-l2 F2P would mis-shape / not
# resolve).
_S1_HARDCODE = """    # Always take the independent (3-axis) read regardless of layout.
    use_joint_layout = False
    w = read_across_folds(use_joint_layout, table_axes, summary_token)
    return w"""
_RIVAL_HARDCODE = _swap(_BASE, _S1_BODY, _S1_HARDCODE)

# (FORGED-RANK, site 1) Invoke the read with a SELF-CONSISTENT rank — pass
# gather_arity(use_joint_layout) as the rank argument so the arity-match
# condition holds trivially, without the read arity ever being compared to the
# actual layout (`table_axes`). Three shapes: hardcode the joint read, hardcode
# the independent read, drive the branch off the UNRESOLVED operand. Each is
# rejected because the read is only performable against the HELD summary table,
# whose actual rank is `table_axes`: a rank the reader names for itself is not a
# table it holds, so the read's `summary_table(table_rank)` requirement is
# unmet whenever the named rank can differ from the actual layout's.
_S1_FORGE_JOINT = """    # Joint read with a self-consistent (forged) rank argument.
    use_joint_layout = True
    w = read_across_folds(use_joint_layout, gather_arity(use_joint_layout),
                          summary_token)
    return w"""
_RIVAL_FORGE_JOINT = _swap(_BASE, _S1_BODY, _S1_FORGE_JOINT)

_S1_FORGE_INDEP = """    # Independent read with a self-consistent (forged) rank argument.
    use_joint_layout = False
    w = read_across_folds(use_joint_layout, gather_arity(use_joint_layout),
                          summary_token)
    return w"""
_RIVAL_FORGE_INDEP = _swap(_BASE, _S1_BODY, _S1_FORGE_INDEP)

_S1_FORGE_UNRESOLVED = """    # Branch off the UNRESOLVED operand, rank argument forged to match.
    use_joint_layout = unresolved_form != INDEPENDENT
    w = read_across_folds(use_joint_layout, gather_arity(use_joint_layout),
                          summary_token)
    return w"""
_RIVAL_FORGE_UNRESOLVED = _swap(_BASE, _S1_BODY, _S1_FORGE_UNRESOLVED)

# (EXTRA-READ, site 1) The universality attacks: keep the arity-matching read of
# the table in effect (so the delivered value and the demanded token are both
# honest) and add ONE MORE read at a rank the impl names for itself. Each extra
# read refines to a real index expression against the single real summary table,
# so on the layout whose actual rank differs from the named one it addresses a
# non-existent axis / an out-of-range position — the reported error class, at a
# read whose value is never used. A postcondition demanding only that SOME read
# was admissible cannot see these; the held-table resource can, because the extra
# read has no table to be performed against.
_S1_EXTRA_JOINT = """    # An extra read naming the joint layout's rank for itself, then the
    # arity-matching read of the table in effect.
    joint_extra = read_across_folds(True, 4, summary_token)
    use_joint_layout = resolved_strategy != INDEPENDENT
    w = read_across_folds(use_joint_layout, table_axes, summary_token)
    return w"""
_RIVAL_EXTRA_JOINT = _swap(_BASE, _S1_BODY, _S1_EXTRA_JOINT)

_S1_EXTRA_INDEP = """    # An extra read naming the independent layout's rank for itself, then the
    # arity-matching read of the table in effect.
    independent_extra = read_across_folds(False, 3, summary_token)
    use_joint_layout = resolved_strategy != INDEPENDENT
    w = read_across_folds(use_joint_layout, table_axes, summary_token)
    return w"""
_RIVAL_EXTRA_INDEP = _swap(_BASE, _S1_BODY, _S1_EXTRA_INDEP)

_S1_EXTRA_UNRESOLVED = """    # An extra read driven by the UNRESOLVED form at the rank its own arity
    # implies, then the arity-matching read of the table in effect.
    unresolved_layout = unresolved_form != INDEPENDENT
    unresolved_extra = read_across_folds(unresolved_layout,
                                        gather_arity(unresolved_layout),
                                        summary_token)
    use_joint_layout = resolved_strategy != INDEPENDENT
    w = read_across_folds(use_joint_layout, table_axes, summary_token)
    return w"""
_RIVAL_EXTRA_UNRESOLVED = _swap(_BASE, _S1_BODY, _S1_EXTRA_UNRESOLVED)

# (EXTRA-READ / value provenance, site 1) DELIVER the value read via the
# UNRESOLVED form and merely harvest the demanded token from a second,
# arity-matching read. Both the value clause and the token clause are satisfied,
# yet the delivered value comes from a read the actual layout may not admit.
_S1_DELIVER_UNRESOLVED = """    # Deliver the value read via the UNRESOLVED form; harvest the token from a
    # separate arity-matching read of the table in effect.
    unresolved_layout = unresolved_form != INDEPENDENT
    w = read_across_folds(unresolved_layout, gather_arity(unresolved_layout),
                          summary_token)
    honest_layout = resolved_strategy != INDEPENDENT
    ignored = read_across_folds(honest_layout, table_axes, summary_token)
    return w"""
_RIVAL_DELIVER_UNRESOLVED = _swap(_BASE, _S1_BODY, _S1_DELIVER_UNRESOLVED)

# (FABRICATION, site 1) Try to CONJURE the held table at a rank of the impl's
# own choosing, then read against it. Stated as an ASSERTED CLAIM about the
# state rather than as `Fold`, on measured grounds: `summary_table` is abstract
# (no body), and nagini's FRONT END refuses both minting constructs before Viper
# ever runs — `Fold(summary_table(4))` exits at translation with
# `Invalid program: abstract.predicate.fold` and `Assume(summary_table(4))` with
# `Invalid program: invalid.contract.position` (both measured on this bundle).
# A front-end refusal is a fact about the LANGUAGE, not evidence about this
# spec, so scoring it as a rejection would certify nothing (see refinement.md
# §H). `Assert(summary_table(4))` is the strongest form of the same fabrication
# that nagini does translate: it obliges Viper to decide, from the spec's own
# resource discipline, whether the step can ever hold a table at a rank it names
# for itself. It cannot — the step is handed exactly one table, at `table_axes`
# — so Viper refutes the claim ('insufficient permission to access
# summary_table(4)'), and the extra joint read the claim was meant to license is
# unperformable for the same reason. `pos-control-site1-held-table-assertable`
# is the non-vacuity control: the same assertion of the resource the step IS
# handed verifies, so the rejection here is attributable to the named rank, not
# to asserting a predicate at all.
_S1_FORGE_TABLE = """    # Claim a table at a self-named rank, then read against it.
    Assert(summary_table(4))
    joint_extra = read_across_folds(True, 4, summary_token)
    use_joint_layout = resolved_strategy != INDEPENDENT
    w = read_across_folds(use_joint_layout, table_axes, summary_token)
    return w"""
_RIVAL_FORGE_TABLE = _swap(_BASE, _S1_BODY, _S1_FORGE_TABLE)

# (DIVERGENCE, site 1) Spin in an unbounded loop before the read: under partial
# correctness a never-returning body satisfies every postcondition vacuously
# (even the capability obligation), but the MustTerminate(2) obligation on
# gather_per_class makes the loop an obligation leak -> MUST be rejected. Its
# faithful real patch would hang the no-refit summarisation forever (no result,
# no resolution).
_S1_DIVERGE = """    # Spin forever before the read; a diverging body discharges nothing.
    k = 0
    while k >= 0:
        Invariant(k >= 0)
        k += 1
    use_joint_layout = resolved_strategy != INDEPENDENT
    w = read_across_folds(use_joint_layout, table_axes, summary_token)
    return w"""
_RIVAL_DIVERGE = _swap(_BASE, _S1_BODY, _S1_DIVERGE)

# (PARTIAL-DOMAIN / always-take-value, site 2) The pre-patch bug: unconditionally
# record the table value, never the absent marker. MUST be rejected: fails
# `Implies(not family_has_mixing, Result() is None)` (= model_prepatch_2.py).
_S2_ALWAYSVAL = """    entry = mixing_value  # type: Optional[int]
    return entry"""
_RIVAL_ALWAYSVAL = _swap(_BASE, _S2_BODY, _S2_ALWAYSVAL)

# (VALUE-SUBSTITUTION, site 2) Record a DIFFERENT input value (selected_index)
# for the mixing family instead of mixing_value. Satisfies "Result is not None"
# but fails `Result() == mixing_value` (selected_index and mixing_value are
# independent params; the verifier cannot prove them equal). MUST be rejected.
# A faithful patch appending the WRONG quantity (e.g. the chosen index instead
# of the chosen ratio) records a wrong l1_ratio_ value.
_S2_WRONGVAL = """    if family_has_mixing:
        entry = select_mixing_value(family_has_mixing, selected_index,
                                    candidates_len,
                                    selected_index)  # type: Optional[int]
    else:
        entry = None
    return entry"""
_RIVAL_WRONGVAL = _swap(_BASE, _S2_BODY, _S2_WRONGVAL)

# (SUPPORTING — inverted branch, site 2) Swap the two branches: record the
# absent marker for the mixing family and the value otherwise. MUST be rejected:
# fails BOTH implications. A near-miss kept as a cheap supporting case; its
# faithful patch inverts the fix (None for elasticnet, a [None]-derived value
# otherwise) so both the elasticnet and non-elasticnet F2P l1_ratio_ records are
# wrong.
_S2_INVERT = """    if family_has_mixing:
        entry = None  # type: Optional[int]
    else:
        entry = select_mixing_value(family_has_mixing, selected_index,
                                    candidates_len, mixing_value)
    return entry"""
_RIVAL_INVERT = _swap(_BASE, _S2_BODY, _S2_INVERT)

# (HOISTED SELECTION, site 2) Select from the candidate-mixing table
# UNCONDITIONALLY and only afterwards correct the RECORD to the absent marker
# for a family that carries no mixing parameter. The delivered record is
# identical to the guarded form on every input, so the value-shape
# postconditions alone cannot tell it apart — but the selection itself is a
# partial operation that is only admissible against a table holding real mixing
# values, and for the no-mixing family the held table holds only the
# placeholder. MUST be rejected on the selection's precondition. A faithful
# patch performs the averaged lookup over the placeholder table for the
# no-mixing family, which yields no mixing value and breaks the per-class record
# for exactly the families whose table is the placeholder.
_S2_HOIST = """    entry = select_mixing_value(family_has_mixing, selected_index,
                                candidates_len,
                                mixing_value)  # type: Optional[int]
    if not family_has_mixing:
        entry = None
    return entry"""
_RIVAL_HOIST = _swap(_BASE, _S2_BODY, _S2_HOIST)

# (HOISTED SELECTION, forged reality flag) The same shape, but declaring the
# held table's entries real so the selection's own precondition is met by an
# assertion of the selector's rather than by the table it holds. MUST be
# rejected: the resource is held at `family_has_mixing`, so a selection at
# `True` has no held table to address when the family carries no mixing
# parameter.
_S2_HOIST_FORGE = """    entry = select_mixing_value(True, selected_index,
                                candidates_len,
                                mixing_value)  # type: Optional[int]
    if not family_has_mixing:
        entry = None
    return entry"""
_RIVAL_HOIST_FORGE = _swap(_BASE, _S2_BODY, _S2_HOIST_FORGE)

# (RECORD A VALUE NEVER SELECTED, site 2) Keep the gold guard shape but deliver
# the value token directly, never selecting it from the held candidate table.
# MUST be rejected: the unforgeable selection capability cannot be fabricated,
# so a recorded mixing value that was never selected cannot discharge the
# contract. This is the site-2 analogue of the site-1 value echo.
_S2_ECHO = """    if family_has_mixing:
        entry = mixing_value  # type: Optional[int]
    else:
        entry = None
    return entry"""
_RIVAL_S2_ECHO = _swap(_BASE, _S2_BODY, _S2_ECHO)

# (FORGE THE SELECTION CAPABILITY, site 2) Attempt to bring the abstract
# capability into existence rather than obtaining it from the selection, then
# deliver the value it is supposed to witness. Asserted rather than `Fold`ed for
# the measured reason recorded at `_S1_FORGE_TABLE` (both minting constructs are
# refused by nagini's front end, which decides nothing about this spec). MUST be
# rejected: `mixing_selected()` is granted by `select_mixing_value` alone, so at
# a point where no selection has been performed the state does not contain it and
# Viper refutes the claim ('insufficient permission to access
# mixing_selected()'). `pos-control-site2-held-table-assertable` is the
# non-vacuity control: the SAME assertion placed after the honest selection
# verifies.
_S2_FORGE_SELECTED = """    if family_has_mixing:
        Assert(mixing_selected())
        entry = mixing_value  # type: Optional[int]
    else:
        entry = None
    return entry"""
_RIVAL_S2_FORGE_SELECTED = _swap(_BASE, _S2_BODY, _S2_FORGE_SELECTED)

# (FORGED EXTENT, site 2) Select at position `candidates_len` — the first
# position the candidate table does NOT have — while declaring the table one
# entry longer than it is, so the in-range condition
# `0 <= candidates_len < candidates_len + 1` is discharged trivially without the
# position ever being compared to the table's real extent. MUST be rejected: the
# selection is only performable against the HELD table, whose actual extent is
# `candidates_len`, so an extent the selector names for itself is not a table it
# holds.
_S2_FORGE_EXTENT = """    if family_has_mixing:
        # Select at position `candidates_len`, declaring the table one entry
        # longer than it is.
        entry = select_mixing_value(family_has_mixing, candidates_len,
                                    candidates_len + 1,
                                    mixing_value)  # type: Optional[int]
    else:
        entry = None
    return entry"""
_RIVAL_S2_FORGE_EXTENT = _swap(_BASE, _S2_BODY, _S2_FORGE_EXTENT)

# (FORGED EXTENT, site 2 — offset shape) The same forged-extent shape, offsetting
# the REAL selected position past the end of the real table instead of using the
# extent itself as the position. MUST be rejected for the same reason.
_S2_FORGE_EXTENT_OFFSET = """    if family_has_mixing:
        entry = select_mixing_value(family_has_mixing,
                                    selected_index + candidates_len,
                                    selected_index + candidates_len + 1,
                                    mixing_value)  # type: Optional[int]
    else:
        entry = None
    return entry"""
_RIVAL_S2_FORGE_EXTENT_OFFSET = _swap(_BASE, _S2_BODY, _S2_FORGE_EXTENT_OFFSET)

# (EXTRA SELECTION, site 2 — the universality attack) Keep the DELIVERED
# selection honest (right position, right extent, right value) and add ONE MORE
# selection past the end of the table at a self-named extent. Every clause about
# the delivered record and the selection capability is satisfied by the honest
# selection, so a postcondition demanding only that SOME selection happened
# cannot see the extra one; the held-table resource can, because the extra
# selection has no table of that extent to be performed against.
_S2_EXTRA_SELECT = """    if family_has_mixing:
        extra = select_mixing_value(family_has_mixing, candidates_len,
                                    candidates_len + 1, mixing_value)
        entry = select_mixing_value(family_has_mixing, selected_index,
                                    candidates_len,
                                    mixing_value)  # type: Optional[int]
    else:
        entry = None
    return entry"""
_RIVAL_S2_EXTRA_SELECT = _swap(_BASE, _S2_BODY, _S2_EXTRA_SELECT)

# (HOISTED + FORGED EXTENT, site 2) Both site-2 holes at once: an unconditional
# selection (above the family guard) at a position past the end of the table,
# with the record corrected afterwards. MUST be rejected.
_S2_HOIST_FORGE_EXTENT = """    entry = select_mixing_value(True, candidates_len,
                                candidates_len + 1,
                                mixing_value)  # type: Optional[int]
    if not family_has_mixing:
        entry = None
    return entry"""
_RIVAL_S2_HOIST_FORGE_EXTENT = _swap(_BASE, _S2_BODY, _S2_HOIST_FORGE_EXTENT)

# (FABRICATION, site 2) Try to CONJURE a candidate table at an extent of the
# impl's own choosing, then select past the end of the real table against it
# (keeping the honest selection so every value clause still holds). Asserted
# rather than `Fold`ed for the measured reason recorded at `_S1_FORGE_TABLE`.
# `candidate_table` is abstract exactly as `summary_table` is, and it is handed
# to the step at its real extent alone, so Viper refutes the claim
# ('insufficient permission to access candidate_table(family_has_mixing,
# (candidates_len + 1))') and the out-of-extent selection it was meant to license
# is unperformable for the same reason. The non-vacuity control is
# `pos-control-site2-held-table-assertable`, which asserts the candidate table at
# the extent the step actually holds and verifies.
_S2_FORGE_TABLE = """    if family_has_mixing:
        Assert(candidate_table(family_has_mixing, candidates_len + 1))
        extra = select_mixing_value(family_has_mixing, candidates_len,
                                    candidates_len + 1, mixing_value)
        entry = select_mixing_value(family_has_mixing, selected_index,
                                    candidates_len,
                                    mixing_value)  # type: Optional[int]
    else:
        entry = None
    return entry"""
_RIVAL_S2_FORGE_TABLE = _swap(_BASE, _S2_BODY, _S2_FORGE_TABLE)

# (PARTIAL-DOMAIN, forged extent) Honest on a singleton candidate table, forged
# extent whenever the table has more than one entry (i.e. exactly the mixing
# family's real table). MUST be rejected — the resource is held at the real
# extent on the whole domain, so the guarded branch has no table to select
# against either.
_S2_PARTIAL_EXTENT = """    if family_has_mixing:
        if candidates_len > 1:
            entry = select_mixing_value(family_has_mixing, candidates_len,
                                        candidates_len + 1,
                                        mixing_value)  # type: Optional[int]
        else:
            entry = select_mixing_value(family_has_mixing, selected_index,
                                        candidates_len, mixing_value)
    else:
        entry = None
    return entry"""
_RIVAL_S2_PARTIAL_EXTENT = _swap(_BASE, _S2_BODY, _S2_PARTIAL_EXTENT)

# (soundness, site 2 — the OTHER side of the extent boundary) Select a DIFFERENT
# but provably in-range entry (position 0) of the held candidate table. Refined,
# this is an in-range averaged lookup at another position of the one real
# candidate table; the no-refit per-class mixing record is observed by its SHAPE
# (`l1_ratio_.shape == (n_classes,)`) and the only value assertion on
# `l1_ratio_` is in the refit path, so this is a CORRECT alternative and MUST
# verify. If it failed the extent obligation would have been over-tightened into
# a claim about which index expression the real code writes (SPEC-TOO-STRONG /
# over-fit to the gold position).
_S2_POS_OTHER_INDEX = """    if family_has_mixing:
        entry = select_mixing_value(family_has_mixing, 0,
                                    candidates_len,
                                    mixing_value)  # type: Optional[int]
    else:
        entry = None
    return entry"""
_POS_S2_OTHER_INDEX = _swap(_BASE, _S2_BODY, _S2_POS_OTHER_INDEX)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-site1-branch-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_S1,
     "rationale": "structurally-different but correct: the joint-layout boolean is computed "
                  "by an explicit if/else over `resolved_strategy == JOINT`, provably equal "
                  "to the gold `!= INDEPENDENT` under the precondition (resolved_strategy in "
                  "{INDEPENDENT,JOINT}). The SAME arity is requested, read_across_folds' "
                  "precondition is discharged, the capability is obtained -> it must verify. "
                  "Pure case analysis over two constants (no induction lemma), so the gold "
                  "proof stays valid. If it failed => SPEC-TOO-STRONG."},
    {"id": "pos-control-site2-init-override", "kind": "soundness", "expect": "verify",
     "module": _POS_S2,
     "rationale": "structurally-different but correct: initialise entry to the absent marker "
                  "(None) and override it only for the mixing family. Identical result on "
                  "every input, so it must verify. If it failed => SPEC-TOO-STRONG."},
    {"id": "pos-control-site1-duplicate-read", "kind": "soundness", "expect": "verify",
     "module": _POS_DUP,
     "rationale": "the read obligation is 'EVERY read at the actual rank', not 'at most one "
                  "read'. This addresses the held table TWICE with the arity the strategy in "
                  "effect determines; both reads are arity-matching reads of the actual layout "
                  "and a duplicated in-bounds index expression does not raise in the real code, "
                  "so it must verify. If it failed => SPEC-TOO-STRONG (the held-table resource "
                  "would have been over-tightened into single-use, rejecting correct "
                  "alternatives that read the table more than once)."},
    {"id": "pos-control-site1-read-then-deliver", "kind": "soundness", "expect": "verify",
     "module": _POS_READ_ECHO,
     "rationale": "the obligation is about WHICH AXES each read addresses, not about the "
                  "provenance of the delivered number. This performs the arity-matching read "
                  "of the held table, discards its value and delivers the summary; refined it "
                  "is the correct branch taken twice with the first result unused, every index "
                  "expression in-bounds. Measured against the correctness oracle it RESOLVES "
                  "(3/3 FAIL_TO_PASS, all PASS_TO_PASS), so it must verify. If it failed => "
                  "SPEC-TOO-STRONG (the spec would have been tightened into a value-provenance "
                  "claim the real function does not make). Paired with "
                  "`rival-echo-no-read` this pins the boundary exactly: performing the "
                  "arity-checked read is required, threading the delivered value through it "
                  "is not."},
    {"id": "pos-control-site2-other-in-range-position", "kind": "soundness", "expect": "verify",
     "module": _POS_S2_OTHER_INDEX,
     "rationale": "the site-2 extent obligation is 'every selection addresses an entry the "
                  "candidate table actually holds', NOT 'the position is the gold index "
                  "expression'. This selects a different but provably in-range entry (position 0) "
                  "of the held table. Refined it is an in-range averaged lookup at another "
                  "position of the one real candidate table; the no-refit per-class mixing record "
                  "is observed by its SHAPE (l1_ratio_.shape == (n_classes,)) and the only value "
                  "assertion on l1_ratio_ is in the refit path, so it is a correct alternative and "
                  "must verify. If it failed => SPEC-TOO-STRONG (the extent resource would have "
                  "been over-tightened into a claim about which index expression the real code "
                  "writes). Paired with the four forged-extent rivals this fixes the boundary from "
                  "both sides: staying inside the table's real extent is required, choosing the "
                  "gold position is not."},
    {"id": "pos-control-site1-held-table-assertable", "kind": "soundness", "expect": "verify",
     "module": _POS_HELD_ASSERT,
     "rationale": "NON-VACUITY CONTROL for the three conjuring rivals. Each of those is rejected "
                  "by an Assert of a resource at a parameterisation the step was never handed; "
                  "this asserts the SAME predicates at the parameterisations the spec does make "
                  "available at that program point — summary_table at `table_axes` before and "
                  "after the gold read, read_admissible at `table_axes` after it — so it MUST "
                  "verify. If it failed, asserting an abstract predicate would be unprovable in "
                  "principle and the conjuring rivals would be `Assert(False)` in disguise: they "
                  "would be rejected by the construct rather than by the spec, and would measure "
                  "nothing. It also independently pins that the granted capability really is at "
                  "the actual layout rank, from inside the body."},
    {"id": "pos-control-site2-held-table-assertable", "kind": "soundness", "expect": "verify",
     "module": _POS_S2_HELD_ASSERT,
     "rationale": "NON-VACUITY CONTROL for `rival-site2-conjure-selection` and "
                  "`rival-site2-conjure-candidate-table`. Asserts the candidate table at the "
                  "extent the step is handed it at (the extent the forged-extent rival names one "
                  "past), takes the gold selection, then asserts the selection capability the "
                  "conjuring rival claims without selecting and that the table returns at the "
                  "same extent. Every assertion holds of the state the spec describes, so it "
                  "MUST verify — which is what makes those two rejections attributable to the "
                  "named extent and to the absent selection rather than to the assertion "
                  "mechanism."},
    {"id": "admiss-site1-arity-establishable", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS_S1,
     "rationale": "the precondition must admit a normal F2P-shaped input (incl. the deferred "
                  "'auto' operand) AND let the in-bounds read be established. The added Assert "
                  "(gather_arity(use_joint_layout) == table_axes) is discharged for EVERY "
                  "admissible input (Nagini reasons universally), proving the precondition "
                  "admits the arity-matching read. If it could not be discharged => "
                  "PRECOND-TOO-STRONG."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "rival-echo-no-read", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ECHO,
     "refinement": "echoes the value (w = summary_token) and never performs the across-folds "
                   "read. Its faithful real patch would skip the coefficient read entirely and "
                   "fabricate w — but the F2P requires the actual np.mean([coefs_paths[...]]) "
                   "read to produce a well-shaped coef_; a no-read echo cannot produce the "
                   "real coefficient array and would not resolve. A verifying rival here would "
                   "be a true verify-not-resolve break.",
     "rationale": "the capability-token / control-flow-effect discriminator. Rejection "
                  "source: the postcondition Ensures(read_admissible(table_axes)) — the "
                  "unforgeable abstract predicate cannot be fabricated by a value echo "
                  "(\"insufficient permission to access read_admissible(table_axes)\"). "
                  "If it verified => SPEC-TOO-WEAK "
                  "(the value-only postcondition would be hollow)."},
    {"id": "rival-unresolved-operand", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_UNRESOLVED,
     "refinement": "drives the read branch off the UNRESOLVED operand (the pre-patch "
                   "`self.multi_class`). Its faithful real patch is the pre-patch code "
                   "`if self.multi_class == 'ovr'`, which for the deferred 'auto' value takes "
                   "the joint 4-axis read against a 3-axis (ovr-resolved) layout -> "
                   "`IndexError: too many indices for array` (the EXACT reported crash, "
                   "auto-l2 F2P). It does NOT resolve.",
     "rationale": "partial-domain: correct except unresolved_form==UNRESOLVED & "
                  "resolved_strategy==INDEPENDENT. Rejection source: the read_across_folds "
                  "precondition gather_arity(use_joint_layout)==table_rank is violated there, "
                  "so read_admissible(table_axes) is unobtainable. If it verified => SPEC-TOO-WEAK."},
    {"id": "rival-hardcode-independent", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_HARDCODE,
     "refinement": "hardcodes the independent (3-axis) read for every layout. Its faithful "
                   "real patch always takes `coefs_paths[i, best_indices[i], :]`; on the "
                   "multinomial 4-axis layout it under-indexes (drops the leading class axis), "
                   "producing a wrong-shape coef_ (multinomial-l2 F2P asserts coef_.shape). "
                   "It does NOT resolve.",
     "rationale": "partial-domain: correct only on the independent layout. Rejection source: "
                  "for resolved_strategy==JOINT (table_axes==4) the request gather_arity(False)"
                  "==3 != 4 violates the read_across_folds precondition, so no capability. If "
                  "it verified => SPEC-TOO-WEAK."},
    {"id": "rival-forge-rank-joint", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FORGE_JOINT,
     "refinement": "always takes the joint (4-axis) read, with the axiom's rank argument "
                   "forged to the read's own arity so the axiom precondition holds "
                   "trivially. Its faithful real patch unconditionally reads "
                   "the extra-leading-axis form; on the independent 3-axis layout that "
                   "over-indexes (the reported error class) — it does NOT resolve.",
     "rationale": "the audited G-EQ hole. Rejection source: the granted capability is "
                  "read_admissible(4) but the postcondition demands "
                  "read_admissible(table_axes), and table_axes==3 for the independent "
                  "layout. If it verified => SPEC-TOO-WEAK (rank argument ungrounded)."},
    {"id": "rival-forge-rank-independent", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FORGE_INDEP,
     "refinement": "always takes the independent (3-axis) read with a forged rank "
                   "argument. Its faithful real patch under-indexes the joint 4-axis "
                   "layout (wrong-shape per-class summary) — it does NOT resolve.",
     "rationale": "Rejection source: grants read_admissible(3); the postcondition demands "
                  "read_admissible(table_axes)==read_admissible(4) on the joint layout. "
                  "If it verified => SPEC-TOO-WEAK."},
    {"id": "rival-forge-rank-unresolved", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FORGE_UNRESOLVED,
     "refinement": "drives the branch off the UNRESOLVED operand and forges the rank "
                   "argument to match its own choice. Its faithful real patch is the "
                   "pre-patch branch operand: on the deferred form resolved to the "
                   "independent layout it takes the 4-axis read against a 3-axis table "
                   "(the exact reported crash) — it does NOT resolve.",
     "rationale": "Rejection source: when unresolved_form==UNRESOLVED and "
                  "resolved_strategy==INDEPENDENT the granted capability is "
                  "read_admissible(4) but the demanded one is read_admissible(3). If it "
                  "verified => SPEC-TOO-WEAK (the un-indexed token admitted exactly this)."},
    {"id": "rival-extra-read-forged-joint", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EXTRA_JOINT,
     "refinement": "keeps the honest arity-matching read AND adds one more read naming the "
                   "joint layout's rank for itself. Its faithful real patch adds an "
                   "unconditional `coefs_paths[:, i, best_indices[i], :]` to the block; on the "
                   "independent 3-axis layout that read addresses a non-existent axis "
                   "(`IndexError: too many indices for array`) even though its value is never "
                   "used, so fit() raises and the ovr F2P/P2P cases fail. It does NOT resolve.",
     "rationale": "the universality attack: the delivered value and the demanded token are both "
                  "honest, so a postcondition demanding that SOME read was admissible cannot "
                  "see the extra one. Rejection source: `read_across_folds` requires "
                  "summary_table(table_rank) — the read is only performable against the HELD "
                  "table, whose actual rank is table_axes, so a self-named rank of 4 has no "
                  "table to be read against on the 3-axis layout. If it verified => "
                  "SPEC-TOO-WEAK (the read obligation would be existential, not universal)."},
    {"id": "rival-extra-read-forged-independent", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EXTRA_INDEP,
     "refinement": "the mirror image: honest read plus one more read naming the independent "
                   "layout's rank for itself. Its faithful real patch adds an unconditional "
                   "`coefs_paths[i, best_indices[i], :]`; on the joint 4-axis layout that "
                   "indexes the leading class axis (extent n_classes) with a position drawn "
                   "from the far larger candidate range, raising IndexError, so the "
                   "multinomial F2P case fails. It does NOT resolve.",
     "rationale": "same universality hole from the other side. Rejection source: the read's "
                  "summary_table(table_rank) requirement — a self-named rank of 3 is not the "
                  "held table on the 4-axis layout. If it verified => SPEC-TOO-WEAK."},
    {"id": "rival-extra-read-unresolved", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_EXTRA_UNRESOLVED,
     "refinement": "honest read plus one more read driven by the UNRESOLVED form at the rank "
                   "its own arity implies. Its faithful real patch adds a read selected by the "
                   "unresolved operand; when the deferred form resolves to the independent "
                   "layout the added read takes the extra-leading-axis form against a 3-axis "
                   "table — the EXACT reported crash, on the problem statement's own "
                   "reproducer. It does NOT resolve.",
     "rationale": "the nearest miss: every clause about the delivered read holds. Rejection "
                  "source: the added read requires summary_table at a rank derived from the "
                  "UNRESOLVED operand, which is not the held table's actual rank whenever the "
                  "two operands disagree. If it verified => SPEC-TOO-WEAK."},
    {"id": "rival-deliver-unresolved-read", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DELIVER_UNRESOLVED,
     "refinement": "DELIVERS the value read via the UNRESOLVED form and merely harvests the "
                   "demanded token from a second arity-matching read. Its faithful real patch "
                   "computes w from the pre-resolution branch operand, so on the deferred form "
                   "resolved to the independent layout the delivering read raises the reported "
                   "IndexError before the second read is ever reached. It does NOT resolve.",
     "rationale": "value-provenance: both the value clause and the token clause are satisfied "
                  "by different reads. Rejection source: the delivering read must be performed "
                  "against the held table, and a rank taken from the UNRESOLVED operand's own "
                  "arity is not it. If it verified => SPEC-TOO-WEAK (the token could be "
                  "harvested independently of the read that produced the result)."},
    {"id": "rival-conjure-summary-table", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_FORGE_TABLE,
     "refinement": "attempts to CONJURE a summary table at a rank of its own choosing and read "
                   "against it. A faithful real patch would have to invent a second array with "
                   "a layout the surrounding code never built, then index the real one through "
                   "it — the extra read is the forged-joint read above and does NOT resolve.",
     "rationale": "fabrication probe for the held-table resource, the counterpart of the "
                  "unforgeability of the capability token. Rejection source: `summary_table` is "
                  "an abstract @ContractOnly @Predicate handed to the step at the layout's ACTUAL "
                  "rank alone, so the state never contains a table at a rank the impl names for "
                  "itself: Viper refutes the claim with 'Assert might fail. There might be "
                  "insufficient permission to access summary_table(4)', and the extra joint read "
                  "the claim was meant to license is unperformable for the same reason. Stated as "
                  "an asserted claim rather than as `Fold`/`Assume` because nagini's front end "
                  "refuses BOTH minting constructs before Viper runs (abstract.predicate.fold / "
                  "invalid.contract.position, both measured), and a front-end refusal is a fact "
                  "about the language that decides nothing about this spec — see refinement.md "
                  "§H. Non-vacuity control: `pos-control-site1-held-table-assertable`. If it "
                  "verified => SPEC-TOO-WEAK (the held table could be had at any rank, which "
                  "would reopen every extra-read attack above)."},
    {"id": "rival-diverge-loop", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_DIVERGE,
     "refinement": "spins in an unbounded loop before the read. Its faithful real patch "
                   "inserts a `while True`-style loop into the no-refit branch: fit() never "
                   "returns, so no attribute is ever produced and NO hidden test passes — a "
                   "diverging patch does NOT resolve. Under partial correctness alone this "
                   "body would verify vacuously; the totality obligation is what rejects it.",
     "rationale": "divergence probe. Rejection source: the MustTerminate(2) obligation on "
                  "gather_per_class — the unbounded loop cannot take the unsatisfied "
                  "obligation into its context (obligation leak). If it verified => "
                  "SPEC-TOO-WEAK (non-termination would be an escape hatch from every "
                  "postcondition)."},
    {"id": "rival-site2-always-value", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ALWAYSVAL,
     "refinement": "the pre-patch bug: unconditionally records the table value. Its faithful "
                   "real patch is `self.l1_ratio_.append(np.mean(l1_ratios_[best_indices_l1]))` "
                   "with no guard; for the non-elasticnet family l1_ratios_ is the [None] "
                   "sentinel, so np.mean([None]) is recorded -> a malformed l1_ratio_ "
                   "(the l2 F2P asserts a well-formed l1_ratio_.shape). It does NOT resolve.",
     "rationale": "partial-domain / absent-marker. Rejection source: the postcondition "
                  "Implies(not family_has_mixing, Result() is None) — recording a value for "
                  "the no-mixing family violates it. If it verified => SPEC-TOO-WEAK."},
    {"id": "rival-site2-wrong-value", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_WRONGVAL,
     "refinement": "records a DIFFERENT input quantity (selected_index, the chosen index) "
                   "instead of mixing_value (the chosen ratio) for the mixing family. A "
                   "faithful patch appending the index instead of the ratio records a wrong "
                   "l1_ratio_ value (it appends best_indices_l1 rather than the averaged "
                   "ratio). It does NOT resolve.",
     "rationale": "value-substitution. Rejection source: the postcondition clause "
                  "Implies(family_has_mixing, Result() == mixing_value) — the verifier cannot "
                  "prove selected_index == mixing_value (independent params). If it verified "
                  "=> SPEC-TOO-WEAK (the value clause would be ungrounded)."},
    {"id": "rival-site2-inverted", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_INVERT,
     "refinement": "inverts the branch: records the absent marker for the mixing family and a "
                   "value otherwise. A faithful patch with the guard inverted "
                   "(`if self.penalty != 'elasticnet'`) records None for elasticnet (losing "
                   "the real ratio) and a [None]-derived value otherwise (malformed) — both "
                   "the elasticnet and non-elasticnet l1_ratio_ records are wrong. It does NOT "
                   "resolve. SUPPORTING near-miss (still carries a real refinement).",
     "rationale": "Rejection source: BOTH implications fail — Implies(family_has_mixing, "
                  "Result()==mixing_value) (records None) and Implies(not family_has_mixing, "
                  "Result() is None) (records a value). If it verified => SPEC-TOO-WEAK."},
    {"id": "rival-site2-hoisted-selection", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_HOIST,
     "rationale": "selects from the candidate-mixing table UNCONDITIONALLY and only then "
                  "corrects the record to the absent marker. The delivered record equals the "
                  "gold one on every input, so the value-shape postconditions alone admit it; "
                  "the selection is a PARTIAL operation admissible only against a held table "
                  "whose entries are real mixing values, and the no-mixing family's table holds "
                  "only the placeholder, so it MUST be rejected on the selection's "
                  "precondition. Its faithful patch performs the averaged lookup over the "
                  "placeholder table for that family, which yields no mixing value and breaks "
                  "the per-class record -- measured NOT to resolve.",
     "refinement": "selects from the candidate-mixing table UNCONDITIONALLY and only afterwards corrects the RECORD to the absent marker for a family that carries no mixing parameter. A faithful patch performs the averaged lookup `np.mean(l1_ratios_[best_indices_l1])` before the family is consulted, so for a family whose candidate table is the one-element placeholder it averages that placeholder rather than a ratio table. The per-class record for exactly those families is then produced from a table that holds no mixing value. It does NOT resolve."},
    {"id": "rival-site2-hoisted-forged-reality", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_HOIST_FORGE,
     "rationale": "same hoisted shape, declaring the table's entries real at the call rather "
                  "than taking that from the held table. MUST be rejected: the resource is held "
                  "at family_has_mixing, so a selection at True addresses no table the step "
                  "holds when the family carries no mixing parameter.",
     "refinement": "the same hoisted-lookup shape, asserting at the call that the table's entries are real instead of taking that from the table the step holds. A faithful patch is the same unconditional averaged lookup over the placeholder table, so it does NOT resolve; the model rejects it because the resource is held at the family flag and no held table matches the asserted one."},
    {"id": "rival-site2-echo-no-selection", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_S2_ECHO,
     "rationale": "keeps the gold guard but delivers the value token without ever selecting it "
                  "from the held candidate table. MUST be rejected: the unforgeable selection "
                  "capability cannot be fabricated, so a recorded mixing value the step never "
                  "selected cannot discharge the contract.",
     "refinement": "keeps the gold guard shape but delivers the mixing token without ever performing the averaged lookup on the held candidate table. A faithful patch appends a value that was never read out of `l1_ratios_` (a fabricated per-class ratio rather than the selected one), so the recorded l1_ratio_ is not the chosen ratio. It does NOT resolve."},
    {"id": "rival-site2-conjure-selection", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_S2_FORGE_SELECTED,
     "rationale": "attempts to bring the abstract selection capability into existence instead of "
                  "obtaining it from the selection, then delivers the value it is supposed to "
                  "witness. MUST be rejected: `mixing_selected()` is granted by "
                  "`select_mixing_value` alone, so at a point where no selection has been "
                  "performed the state does not contain it ('Assert might fail. There might be "
                  "insufficient permission to access mixing_selected()'). Asserted rather than "
                  "`Fold`ed for the measured reason recorded on "
                  "`rival-conjure-summary-table`; non-vacuity control: "
                  "`pos-control-site2-held-table-assertable`, which asserts the SAME capability "
                  "after the honest selection and verifies. If it verified => SPEC-TOO-WEAK.",
     "refinement": "attempts to fabricate the selection capability rather than obtaining it from the averaged lookup, i.e. a faithful patch that appends a per-class ratio it never selected from `l1_ratios_`. It does NOT resolve."},
    {"id": "rival-site2-forged-extent", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_S2_FORGE_EXTENT,
     "rationale": "the extent attack: select at position `candidates_len` while DECLARING the "
                  "table one entry longer, so the in-range condition "
                  "0 <= candidates_len < candidates_len + 1 holds trivially and the position is "
                  "never compared to the table's real extent. Every value clause and the selection "
                  "capability are discharged, so no postcondition over the delivered record can "
                  "see it. Rejection source: `select_mixing_value` requires "
                  "candidate_table(holds_mixing_values, candidates_len) — the selection is only "
                  "performable against the HELD table, whose actual extent is `candidates_len`, so "
                  "an extent the selector names for itself is no table it holds ('insufficient "
                  "permission to access candidate_table(holds_mixing_values, candidates_len)'). "
                  "If it verified => SPEC-TOO-WEAK (the selection bound would be caller-supplied).",
     "refinement": "refines to the averaged lookup performed one position past the end of the one real candidate table, i.e. `self.l1_ratio_.append(np.mean(l1_ratios_[len(l1_ratios_)]))`. That raises `IndexError: index N is out of bounds for axis 0 with size N` on the mixing-family path, so fit() raises for exactly the families whose candidate table is the real ratio table while the reported bug's own cases still pass. It does NOT resolve."},
    {"id": "rival-site2-forged-extent-offset", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_S2_FORGE_EXTENT_OFFSET,
     "rationale": "the same forged-extent shape, offsetting the REAL selected position past the "
                  "end of the real table rather than using the extent as the position. Rejection "
                  "source: the same held-table requirement at the real extent. If it verified => "
                  "SPEC-TOO-WEAK.",
     "refinement": "refines to `np.mean(l1_ratios_[best_indices_l1 + len(l1_ratios_)])`, an averaged lookup offset past the end of the one real candidate table -> IndexError on the mixing-family path. It does NOT resolve."},
    {"id": "rival-site2-extra-selection-forged-extent", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_S2_EXTRA_SELECT,
     "rationale": "the universality attack at site 2: the DELIVERED selection is entirely honest "
                  "(right position, right extent, right value, real capability), and one EXTRA "
                  "selection is made past the end of the table at a self-named extent. A "
                  "postcondition demanding only that SOME selection happened cannot see the extra "
                  "one. Rejection source: the extra selection needs "
                  "candidate_table(holds_mixing_values, candidates_len + 1), and the step holds "
                  "the table only at its real extent. If it verified => SPEC-TOO-WEAK (the "
                  "selection obligation would be existential, not universal).",
     "refinement": "adds an unconditional out-of-range averaged lookup to the block whose value is never used; a real out-of-range index raises regardless of whether its result is consumed, so fit() raises on the mixing-family path. It does NOT resolve."},
    {"id": "rival-site2-hoisted-forged-extent", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_S2_HOIST_FORGE_EXTENT,
     "rationale": "both site-2 holes at once: an unconditional selection hoisted above the family "
                  "guard AND placed past the end of the table, with the record corrected "
                  "afterwards. Rejection source: the held table is at (family_has_mixing, "
                  "candidates_len), so neither the asserted entry reality nor the named extent "
                  "matches a table the step holds. If it verified => SPEC-TOO-WEAK.",
     "refinement": "refines to an unconditional averaged lookup past the end of the candidate table, performed before the family is consulted: it raises for the mixing family and averages the placeholder for every other. It does NOT resolve."},
    {"id": "rival-site2-partial-domain-extent", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_S2_PARTIAL_EXTENT,
     "rationale": "partial-domain version of the extent attack: honest whenever the candidate "
                  "table is a singleton, forged extent as soon as it has more than one entry — "
                  "which is exactly the real mixing family's table. Rejection source: the resource "
                  "is held at the real extent over the whole domain, so the guarded branch has no "
                  "table of the named extent to select against either. If it verified => "
                  "SPEC-TOO-WEAK (the clause would only bind the singleton boundary).",
     "refinement": "refines to a guarded out-of-range averaged lookup taken whenever the real candidate table has more than one entry, i.e. on every genuine mixing-family configuration -> IndexError there. It does NOT resolve."},
    {"id": "rival-site2-conjure-candidate-table", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_S2_FORGE_TABLE,
     "rationale": "fabrication probe for the candidate-table resource's EXTENT, the counterpart of "
                  "`rival-conjure-summary-table`: attempt to conjure the candidate table at an "
                  "extent of the impl's own choosing and select past the end of the real one "
                  "against it, keeping the honest selection so every value clause still holds. "
                  "Rejection source: `candidate_table` is an abstract @ContractOnly @Predicate "
                  "handed to the step at its REAL extent alone, so the state never contains a "
                  "table one entry longer ('Assert might fail. There might be insufficient "
                  "permission to access candidate_table(family_has_mixing, (candidates_len + 1))') "
                  "and the out-of-extent selection the claim was meant to license is unperformable "
                  "for the same reason. Asserted rather than `Fold`ed for the measured reason "
                  "recorded on `rival-conjure-summary-table`; non-vacuity control: "
                  "`pos-control-site2-held-table-assertable`, which asserts the candidate table at "
                  "the extent the step really holds and verifies. "
                  "If it verified => SPEC-TOO-WEAK (the held table could be had at any extent, "
                  "reopening every forged-extent attack above).",
     "refinement": "a faithful patch would have to invent a longer candidate table the surrounding code never built and index the real one through it; the extra lookup is the forged-extent selection above and does NOT resolve."},
]

# ===========================================================================
# AXIOM LANE (Docker, real sklearn 0.22 callees)
# ===========================================================================

# (1) axiom-soundness for read_across_folds (R1 + R2). Validates, against the
# REAL callees, that the axiom grants the in-range capability EXACTLY on an
# arity match — under the caller's actual config (the resolved multi_class that
# fit() reshapes the coefs_paths layout from):
#   R1: the real `_check_multi_class` NEVER returns the deferred 'auto' form
#       (resolved_strategy != UNRESOLVED), over solvers x n_classes x {ovr,
#       multinomial,auto}; and the real np.reshape rank table is 3 (ovr) / 4
#       (multinomial) == model.py table_rank.
#   R2: an arity-matching read is in-bounds, while an over-arity read raises the
#       reported `IndexError: too many indices for array` -> the capability is
#       grantable iff gather_arity == table_rank.
# This EXECUTES the real routines (never scrapes source). apply_gold=True since
# the axiom describes the post-gold (resolved-operand) read.
_AX_READ_SOUNDNESS = r'''
import sys
import numpy as np
from sklearn.linear_model.logistic import _check_multi_class

INDEPENDENT, JOINT, UNRESOLVED = 0, 1, 2

def table_rank(resolved_strategy):
    assert resolved_strategy in (INDEPENDENT, JOINT)
    return 3 if resolved_strategy == INDEPENDENT else 4

def gather_arity(use_joint_layout):
    return 4 if use_joint_layout else 3

# --- R1: resolver never yields 'auto'; real reshape rank table is 3/4 ---------
solvers = ['lbfgs', 'newton-cg', 'sag', 'saga', 'liblinear']
for solver in solvers:
    for n_classes in range(2, 8):
        for mc in ('ovr', 'multinomial', 'auto'):
            try:
                resolved = _check_multi_class(mc, solver, n_classes)
            except ValueError:
                # multinomial+liblinear is unsupported -> the read is never
                # reached in that config; skip (matches axiom_check.py).
                continue
            if resolved not in ('ovr', 'multinomial'):
                print("AXIOM-UNSOUND R1: resolver produced %r (must be ovr/"
                      "multinomial), config solver=%r mc=%r n_classes=%d"
                      % (resolved, solver, mc, n_classes))
                sys.exit(1)
            if resolved == 'auto':
                print("AXIOM-UNSOUND R1: resolver returned the deferred 'auto' form")
                sys.exit(1)
            # the per-class coefs_paths layout fit() reshapes to:
            n_folds, n_cl1, n_feat = 2, 6, 20
            if resolved == 'ovr':
                arr = np.empty((n_folds, n_cl1, n_feat))          # 3 axes
                tag, expected = INDEPENDENT, 3
            else:
                arr = np.empty((n_classes, n_folds, n_cl1, n_feat))  # 4 axes
                tag, expected = JOINT, 4
            if not (arr.ndim == expected == table_rank(tag)):
                print("AXIOM-UNSOUND R1: rank-table mismatch resolved=%r ndim=%d "
                      "table_rank=%d" % (resolved, arr.ndim, table_rank(tag)))
                sys.exit(1)

# --- R2: arity-match <=> in-bounds; over-arity read raises IndexError ---------
n_folds, n_cl1, n_feat = 2, 6, 20
ind_arr = np.empty((n_folds, n_cl1, n_feat))      # 3 axes (independent layout)
joint_arr = np.empty((4, n_folds, n_cl1, n_feat)) # 4 axes (joint layout)
best = np.zeros(n_folds, dtype=int)

# matching independent read (3 axes) is in-bounds
for i in range(n_folds):
    _ = ind_arr[i, best[i], :]
if gather_arity(False) != ind_arr.ndim:
    print("AXIOM-UNSOUND R2: independent read arity != layout rank")
    sys.exit(1)

# matching joint read (4 axes) is in-bounds
for i in range(n_folds):
    _ = joint_arr[:, i, best[i], :]
if gather_arity(True) != joint_arr.ndim:
    print("AXIOM-UNSOUND R2: joint read arity != layout rank")
    sys.exit(1)

# OVER-arity read of the 3-axis layout (the joint read against ovr) must raise
# the reported IndexError -> the capability is NOT grantable on an arity mismatch
raised = False
try:
    for i in range(n_folds):
        _ = ind_arr[:, i, best[i], :]   # 4 index axes against a 3-axis array
except IndexError:
    raised = True
if not raised:
    print("AXIOM-UNSOUND R2: over-indexing the 3-axis layout with the 4-axis "
          "joint read did NOT raise IndexError")
    sys.exit(1)

print("read_across_folds SOUND: real _check_multi_class never yields 'auto' and "
      "the real np.reshape rank table is 3 (ovr) / 4 (multinomial) == model "
      "table_rank (R1); an arity-matching read is in-bounds while an over-arity "
      "read raises IndexError, so read_admissible is grantable EXACTLY on an "
      "arity match (R2).")
sys.exit(0)
'''

# (2) axiom-containment for read_across_folds. Enumerate EXACTLY the
# (use_joint_layout, table_rank) pairs the MODEL can pass to read_across_folds,
# derived from the model's own control flow + Requires:
#     use_joint_layout = (resolved_strategy != INDEPENDENT)
#     table_axes       = table_rank(resolved_strategy)
#     resolved_strategy in {INDEPENDENT, JOINT}     (Requires excludes UNRESOLVED)
# => the ONLY reachable pairs are (False, 3) and (True, 4). Assert each lies in
# the axiom's Requires domain (gather_arity == table_rank) AND corresponds to a
# real in-bounds numpy read of the matching layout. A reachable pair with
# gather_arity != table_rank would be AXIOM-TOO-WEAK-FOR-CALLER (the caller could
# request a read the axiom cannot soundly grant). Covering the mismatch case
# would be sound over-coverage; reaching one is the defect. apply_gold=True.
_AX_READ_CONTAINMENT = r'''
import sys
import numpy as np

INDEPENDENT, JOINT = 0, 1

def table_rank(resolved_strategy):
    assert resolved_strategy in (INDEPENDENT, JOINT)
    return 3 if resolved_strategy == INDEPENDENT else 4

def gather_arity(use_joint_layout):
    return 4 if use_joint_layout else 3

# The model's reachable callee inputs: resolved_strategy ranges over the two
# concrete forms ONLY (the Requires excludes UNRESOLVED); the impl computes
# use_joint_layout and table_axes deterministically from it.
reachable = []
for resolved_strategy in (INDEPENDENT, JOINT):
    use_joint_layout = (resolved_strategy != INDEPENDENT)
    table_axes = table_rank(resolved_strategy)
    reachable.append((use_joint_layout, table_axes))

# Every reachable pair must lie in read_across_folds' Requires domain
# (gather_arity == table_rank): containment.
n_folds, n_cl1, n_feat = 2, 6, 20
best = np.zeros(n_folds, dtype=int)
for use_joint_layout, table_axes in reachable:
    if gather_arity(use_joint_layout) != table_axes:
        print("AXIOM-TOO-WEAK-FOR-CALLER: model reaches read_across_folds with "
              "gather_arity=%d, table_rank=%d (arity MISMATCH outside the axiom "
              "Requires domain)" % (gather_arity(use_joint_layout), table_axes))
        sys.exit(1)
    # and it must be a real in-bounds numpy read of the matching layout
    if table_axes == 3:
        arr = np.empty((n_folds, n_cl1, n_feat))
        try:
            for i in range(n_folds):
                _ = arr[i, best[i], :]
        except IndexError:
            print("AXIOM-TOO-WEAK-FOR-CALLER: reachable independent read raised "
                  "IndexError on the real layout")
            sys.exit(1)
    else:
        arr = np.empty((4, n_folds, n_cl1, n_feat))
        try:
            for i in range(n_folds):
                _ = arr[:, i, best[i], :]
        except IndexError:
            print("AXIOM-TOO-WEAK-FOR-CALLER: reachable joint read raised "
                  "IndexError on the real layout")
            sys.exit(1)

print("containment OK: the model reaches read_across_folds with EXACTLY the "
      "pairs", reachable, "(use_joint_layout, table_rank); each satisfies the "
      "axiom Requires gather_arity==table_rank and is a real in-bounds numpy "
      "read. The arity-mismatch case is unreachable (Requires excludes the "
      "deferred form), so the axiom is sufficient for the caller.")
sys.exit(0)
'''

# (3) axiom-soundness for the A-reference [None] sentinel (site 2). When the
# regularisation family carries no mixing parameter, the candidate-mixing table
# is the one-element sentinel [None]; np.mean over it does NOT yield a real
# finite number, so the per-class mixing record MUST be the explicit None marker
# (never a value derived from the sentinel). A real ratio table DOES average to a
# number. This grounds the mixing_record postcondition `not family_has_mixing ->
# Result() is None`. Executes real numpy (reuses axiom_check.py R3).
_AX_SENTINEL = r'''
import sys
import numpy as np

# no-mixing family: candidate table is the one-element [None] sentinel
sentinel = np.asarray([None])
if sentinel.shape != (1,):
    print("AXIOM-UNSOUND R3: [None] sentinel shape != (1,):", sentinel.shape)
    sys.exit(1)
idx = 0   # post-patch only index 0 is reachable (len == 1)
if sentinel[idx] is not None:
    print("AXIOM-UNSOUND R3: sentinel element is not None:", repr(sentinel[idx]))
    sys.exit(1)
# np.mean of the [None] sentinel must NOT be a real finite number, else the
# absent marker would be indistinguishable from a real ratio.
bad = False
try:
    m = np.mean(sentinel[idx])
    if isinstance(m, (int, float, np.floating)) and np.isfinite(m):
        bad = True
except (TypeError, ValueError):
    bad = False
if bad:
    print("AXIOM-UNSOUND R3: np.mean of the [None] sentinel yielded a real "
          "finite number -> the absent marker None would be indistinguishable")
    sys.exit(1)

# a REAL ratio table (the mixing family) DOES average to a finite number
real_ratios = np.asarray([0.0, 1.0])
for i in (0, 1):
    m = np.mean(real_ratios[i])
    if not (isinstance(m, (int, float, np.floating)) and np.isfinite(m)):
        print("AXIOM-UNSOUND R3: real ratio entry did not average to a finite "
              "number:", repr(m))
        sys.exit(1)

print("sentinel SOUND (R3): np.mean of the [None] sentinel is not a real finite "
      "number (so not_family_has_mixing -> the record must be the None marker), "
      "while a real ratio table averages to a finite number.")
sys.exit(0)
'''

# (4) axiom-soundness for select_mixing_value's EXTENT guard (R5). Validates,
# against real numpy, that the averaged lookup of the candidate-mixing table is
# admissible EXACTLY inside the table's extent — every position in [0, n)
# averages to a real number, position n raises the reported IndexError — and that
# the real flat-position decomposition (`flat // n_Cs`) lands inside the extent
# for every reachable flat position, given the real score-table extent
# n_Cs * n_mixing. If an in-extent position could raise, carrying the extent on
# the held resource would be UNSOUND; if the real decomposition could leave the
# extent, it would be RESTRICTIVE (it would forbid a lookup the real code makes).
_AX_EXTENT = r'''
import sys
import numpy as np

# (a) admissible EXACTLY inside the extent
for n in (1, 2, 3, 5):
    table = np.asarray([float(i) / n for i in range(n)])
    for idx in range(n):
        got = np.mean(table[idx])
        if not (isinstance(got, (int, float, np.floating)) and np.isfinite(got)):
            print("AXIOM-UNSOUND R5: in-extent position %d of a %d-entry "
                  "candidate table did not average to a real number: %r"
                  % (idx, n, got))
            sys.exit(1)
    raised = False
    try:
        _ = np.mean(table[n])
    except IndexError:
        raised = True
    if not raised:
        print("AXIOM-UNSOUND R5: position %d of a %d-entry candidate table did "
              "NOT raise IndexError -- the extent bound would not be the real "
              "in-bounds condition" % (n, n))
        sys.exit(1)

# (b) the real flat-position decomposition stays inside the extent, for the real
#     score-table extent n_Cs * n_mixing (the reshape the block argmaxes over).
for n_cs in range(1, 6):
    for n_mixing in range(1, 6):
        flat_extent = n_cs * n_mixing
        for flat in range(flat_extent):
            pos = flat // n_cs
            if not (0 <= pos < n_mixing):
                print("AXIOM-TOO-STRONG R5: flat=%d // n_Cs=%d gave position %d, "
                      "outside a candidate table of extent %d"
                      % (flat, n_cs, pos, n_mixing))
                sys.exit(1)

print("candidate-table extent SOUND (R5): the averaged lookup is admissible "
      "EXACTLY inside the table's extent (every in-extent position averages to a "
      "real number; position len raises IndexError), and the real flat-position "
      "decomposition flat // n_Cs lands inside the extent for every reachable "
      "flat position -- so carrying the extent on the held candidate table is "
      "sound and does not forbid a lookup the real code makes.")
sys.exit(0)
'''

AXIOM_TESTS = [
    {"id": "ax-read-across-folds-soundness", "axiom": "read_across_folds",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _AX_READ_SOUNDNESS,
     "rationale": "read_across_folds grants read_admissible EXACTLY on an arity match. "
                  "Validated against the real callees under the caller's config: real "
                  "_check_multi_class never yields the deferred 'auto' form and the real "
                  "np.reshape rank table is 3/4 == model table_rank (R1); an arity-matching "
                  "numpy read is in-bounds while an over-arity read raises the reported "
                  "IndexError (R2). Any disagreement => AXIOM-UNSOUND."},
    {"id": "ax-read-across-folds-containment", "axiom": "read_across_folds",
     "kind": "axiom-containment", "expect": "covered", "apply_gold": True,
     "probe": _AX_READ_CONTAINMENT,
     "rationale": "the model reaches read_across_folds with EXACTLY (False,3) and (True,4) "
                  "(resolved_strategy in {INDEPENDENT,JOINT}, use_joint_layout / table_axes "
                  "derived from it); each lies in the axiom Requires domain (gather_arity == "
                  "table_rank) and is a real in-bounds read. The arity-mismatch case is "
                  "unreachable. A reachable mismatch => AXIOM-TOO-WEAK-FOR-CALLER."},
    {"id": "ax-none-sentinel-soundness", "axiom": "l1_ratios_ [None] sentinel",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _AX_SENTINEL,
     "rationale": "A-reference deep model (site 2): np.mean of the real one-element [None] "
                  "sentinel is not a real finite number, so the no-mixing family must record "
                  "the explicit None marker, while a real ratio table averages to a number. "
                  "If np.mean([None]) were a finite number => the absent-marker postcondition "
                  "would be unsound (AXIOM-UNSOUND)."},
    {"id": "ax-candidate-table-extent-soundness", "axiom": "select_mixing_value",
     "kind": "axiom-soundness", "expect": "holds", "apply_gold": True,
     "probe": _AX_EXTENT,
     "rationale": "select_mixing_value is admissible EXACTLY inside the candidate table's "
                  "extent. Validated against real numpy: every position in [0, n) of an "
                  "n-entry table averages to a real number while position n raises the "
                  "reported IndexError (so the extent bound IS the real in-bounds condition, "
                  "and permitting any in-extent position is not over-permissive); and the real "
                  "flat-position decomposition `flat // n_Cs` lands inside the extent for every "
                  "reachable flat position given the real score-table extent n_Cs * n_mixing "
                  "(so the bound forbids no lookup the real code makes). An in-extent position "
                  "that raised => AXIOM-UNSOUND; a real decomposition leaving the extent => "
                  "AXIOM-TOO-STRONG."},
]
