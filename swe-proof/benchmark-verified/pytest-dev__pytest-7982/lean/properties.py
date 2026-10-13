"""properties.py — G-PBT falsification battery for pytest-dev__pytest-7982 (lean).

NOT a Lean file; a manifest of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant built by region surgery: only text
physically inside an ``-- impl-start`` / ``-- impl-end`` region — and, for a case
that legitimately re-proves, inside ``-- proof-start`` / ``-- proof-end`` — is
changed. So ``markers.same_spec`` holds by construction, the single
``theorem correct_collect`` STATEMENT stays byte-identical, and any rejection is
attributable to the postcondition rather than to a tampered spec.
``expect="verify"`` passes iff (in scope AND the file elaborates with the
obligation closed); ``expect="reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier, not a translation of
its text. The nagini bundle models a FLATTENED per-entry decision: a function
``descend_decisions(kinds : PSeq[int], selected : PSeq[bool]) -> PSeq[bool]``
whose postcondition pins each output element to a grounded predicate of the two
inputs at that index, where an integer ``kind`` code enumerates the four entry
classifications. This Lean bundle models the WHOLE recursive walk instead: one
total function over a tree of entries, returning the emitted entry sequence, with
the classification carried structurally by an inductive node type rather than by
an integer code. Every nagini case therefore has to be re-expressed, and the
carrier change both loses cases (an integer code the type system now makes
unrepresentable) and gains them (clauses the flattened model could not state at
all). The case-by-case map, including every principled omission, is in the module
``assessment`` of the submitted payload and summarised per case below.

DEFENDED SURFACE (one modeled behavior, one obligation). The result is pinned
equal to a single grounded computation over the inputs: the in-order walk of the
input level. The postcondition is a single equation, but that equation is a
CONJUNCTION of independent observable commitments, each attackable on its own:

  * WHICH entries are descended into — an entry is descended into exactly when it
    resolves to a directory AND the caller's predicate selects it. This splits
    into two independent sub-commitments, since either conjunct can be attacked
    while the other is honoured;
  * the CLASSIFICATION that decides "resolves to a directory" — an entry whose
    resolved target is a directory counts as one whether or not the entry is
    itself a symbolic link. This is the BEHAVIOURAL DISCRIMINATOR (the fix);
  * the ORDER within a level — entries are emitted in name order;
  * the ORDER of a level against its descended subtrees — a level is emitted in
    full BEFORE any subtree it descends into;
  * the ORDER of SIBLING subtrees against each other — two subtrees of the same
    level follow in their parents' order. Independent of both orderings above: a
    rival can honour each of those and still permute these;
  * the TRANSITIVITY of the descent — the walk recurses to unbounded depth, not
    merely one level down. Invisible at any input whose child levels hold no
    directory, which is why it needs a depth-three witness of its own;
  * UNIFORMITY across the level — the rule applies to every entry of a level, not
    to a positional subset;
  * LEVEL COMPLETENESS — the level is emitted whole and exactly once, so no entry
    is dropped from the report and none is duplicated. Two independent halves,
    since a postcondition can be weak in one direction only.

ADVERSARIAL READ of the nagini case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Lean is referentially transparent: an
    input carries no heap permission, so there is no read-only half-permission to
    overwrite and no aliasing to exploit. The nagini sibling already recorded this
    class as N/A for its own value abstraction; here it is vacuous for the
    stronger reason that the carrier cannot express it. No substitute fabricated.

  * DIVERGENCE / NON-TERMINATION — VACUOUS on this backend, and vacuous for a
    reason specific to it rather than for the referential-transparency reason.
    ``implementation_collect`` is a total Lean ``def`` carrying a
    ``termination_by`` proof obligation the elaborator discharges, so a diverging
    implementation cannot be written at all: a variant that dropped the descent
    measure would fail to elaborate as a MALFORMED variant, not verify vacuously.
    (This is the lean disposition of the class; it is NOT the "spec admits the
    rival" hole that the partial-semantics backends carry. Nothing to port either
    way, but the reason differs and the two carry opposite information.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: the result
    is pinned equal to a term built only from the inputs, and the bundle declares
    no ``opaque`` callee and consumes no ``axiom``. There is no answer key an
    implementation could echo. In its place the battery carries honest positive
    controls that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and is where the port concentrates.

  * INTEGER-CODE OVER-BROADENING — NOT EXPRESSIBLE, and this is the one nagini
    case that genuinely has no counterpart. Nagini's ``kinds`` is a ``PSeq[int]``,
    so a rival can widen the classification to admit a code the rule excludes
    (its ``reject-overbroad-code3``: treat a link whose target is NOT a directory
    as descendable). Here the classification is a MATCH ON AN INDUCTIVE TYPE with
    exactly two constructors, one of which is the non-directory entry; an entry
    whose target is not a directory simply IS the non-directory constructor.

    The AUDIT measured what the over-broad rival actually does here rather than
    arguing it, because the answer is not the one the port originally recorded.
    Widening the classification to return ``true`` on the non-directory
    constructor is NOT a wrong implementation on this carrier: that constructor
    carries no children, so the descent's own match still emits nothing for it,
    and the walk is unchanged at every input. Built as a variant, it VERIFIES
    against the frozen spec unchanged apart from one Boolean normalisation step
    (exit 0). So it cannot be shipped as an ``expect="reject"`` case — it belongs
    to attack E (a correct reshape) and not to the uniqueness lane — and it is
    NOT, as an earlier draft of this note claimed, subsumed by some
    "descend into everything" rival carried below; no such rival exists in this
    battery, and one could not reject if it did. The distinction nagini's integer
    code kept is genuinely collapsed by the inductive carrier: the sub-domain the
    nagini rival is wrong ON is unrepresentable here. Recorded as inexpressible
    with that measurement as its evidence; see ``assessment``.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen script is tuned to the frozen form, as
both positive controls below demonstrate by needing a reproof despite being
CORRECT — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at one concrete input and refuting it. Each was checked by two
real builds to HOLD of its rival and to FAIL on the frozen solution, so it
discriminates rather than asserting a tautology.

And the gold-side FAILURE has to be a refutation, not merely an exit code — a
requirement this battery did not originally meet everywhere. The first audit
re-derived every witness and found that the level-ordering witness failed on the
frozen solution because the per-level ordering term never REDUCED, so its loop
never unfolded: the claim that is TRUE of the frozen implementation at that same
input failed there with the identical error, meaning the gold exit code was
reporting the shape of an unreduced term rather than the truth of the claim. The
repair is recorded at that witness. The invariant to hold each witness to is
therefore sharper than "gold exits nonzero": the gold-side error must exhibit two
CONCRETE lists that differ.

The SECOND audit re-derived all of them again from the manifest, and measured the
sensitivity directly rather than reading the errors: for each of the eight, the
value that is TRUE of the frozen implementation at that witness's own input was
claimed under that witness's OWN closing tactic and built against the frozen
solution. All eight built (exit 0) while the witnesses themselves failed there
(exit 1), so every gold-side exit code tracks the claim and not the term's shape.
Note that FLIPPING a witness's outer negation is NOT the sensitivity test on this
carrier: these witnesses fail on gold inside the `himpl` step, which sits above
the negation, so the flipped file fails with a byte-identical error for a reason
that has nothing to do with the forged claim. The claim that has to be varied is
the one inside `himpl`. Both new rivals below were held to the same standard, and
the depth witness needed its innermost level supplied as a `have` for exactly the
reason the ordering witness did — without it the frozen side failed by an
unfolding failure rather than by a refutation (measured, then repaired before
shipping).

A property of this carrier drives the witness tactics, and it is worth stating
because it is NOT the usual shape. Neither the specification walk nor the
implementation is ``decide``-able at ANY input: both are well-founded recursions
(so their equation lemmas do not reduce definitionally), the entry-node type
carries no decidable equality, and the per-level ordering bottoms out in a string
comparison whose ``Decidable`` instance is stuck (measured: ``decide`` on a
two-name ordering fails at ``String.decidableLE``). So no witness here can be a
bare ``decide``. Instead each witness EVALUATES both sides by hand — unfolding
the recursion one level at a time, discharging each child level as a local
``have``, and reducing the ordering to the ``List Char`` comparison that IS
decidable — and then refutes the resulting concrete list equation. Every witness
is stated at literal inputs, so no witness binds a hypothesis and the gate's
inconsistent-binder probe has nothing to check (there are no assumptions to be
jointly unsatisfiable).

BINDER / POINT SPREAD. The obligation binds two inputs, ``recurse`` (the caller's
selection predicate) and ``entries0`` (the input level), and the reject witnesses
move BOTH rather than fixing either at one convenient value. ``recurse`` takes
the always-select setting in nine witnesses and the never-select setting in the
one rival that attacks the selection conjunct — which is the only setting that can
expose it, since a rival that ignores the predicate agrees with the specification
everywhere the predicate is true. ``entries0`` ranges over: a symbolically-linked
directory holding a file; a plain directory holding a file (twice, at distinct
names); a two-entry level of two plain directories (twice — once refuted by an
omitted subtree and once by permuted ones); a two-entry flat level given out of
name order; a one-entry level holding only a NON-directory, which is the
descent-free point where level emission itself is the only thing under test; and a
depth-three chain of a directory inside a directory, the shallowest input at which
recursion is distinguishable from a single descent.
The ten reject witnesses probe eight distinct input points. Two points are shared,
each deliberately: the descent-free single-file level, used by the two
level-completeness rivals that attack it from opposite directions (too few
entries, too many) and so need the same input to be a matched pair; and the
two-directory level, where the uniformity rival is refuted by an ABSENT subtree
and the sibling-order rival by two PRESENT ones in the wrong order — the same
input separating two different clauses, which is why the second rival is not
redundant with the first.

AXIOM lane: EMPTY. The bundle declares no ``opaque`` callee and consumes no
``axiom`` — the walk, the per-level ordering and the classification are all
modeled deeply, and the selection predicate is a universally quantified function
parameter rather than an axiomatized callee. The nagini ``AXIOM_TESTS`` was also
empty; the axiom lane belongs to G-AX and this gate ignores it.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-7982"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region anchors. Each is verified unique at import, so the manifest breaks
# loudly if the frozen solution ever drifts. The IMPL anchors lie entirely
# inside the impl region; the PROOF anchors entirely inside the proof region
# (only the two positive controls, which legitimately re-prove, touch those).
# ---------------------------------------------------------------------------

# --- impl region ---

# The classification of an entry as a directory to descend into.
_I_CLASSIFY = ("def entryIsDir : FSNode → Bool\n"
               "  | .file => false\n"
               "  | .dir _ _ => true")

# The descent guard: resolves-to-a-directory AND the caller selects it.
_I_GUARD = "      if entryIsDir e.2 && recurse e then"

# The whole per-level loop (accumulator init through the return).
_I_LOOP = ("    let mut acc := entries\n"
           "    for h : e in entries do\n"
           "      if entryIsDir e.2 && recurse e then\n"
           "        match h2 : e.2 with\n"
           "        | .dir _ ch => acc := acc ++ implementation_collect recurse ch\n"
           "        | .file => pure ()\n"
           "    return acc")

# The per-level ordering step (+ the accumulator init, for uniqueness).
_I_ORDER = "    let entries := sortByName xs\n    let mut acc := entries"

# The append that places a descended subtree AFTER the level emitted so far.
_I_PLACE = ("        | .dir _ ch => acc := acc ++ implementation_collect recurse ch")

# The loop header that walks a level's entries in order.
_I_FOR = "    for h : e in entries do"

# Just the membership step of the impl's descent measure (the part that has to be
# rejustified when the loop no longer ranges over the level in its own order).
# (Trailing newline included: the SPEC walk's own measure differs from the
# impl's only by naming its membership hypothesis `he`, so without it this anchor
# would also match a prefix of that line and the swap would not be unique.)
_I_MEASURE_MEM = ("  have hmem : e ∈ xs :=\n"
                  "    ((List.mergeSort_perm xs (fun a b => a.1 ≤ b.1)).mem_iff).mp h\n")

# The impl's whole termination clause, dropped by a rival whose recursion is gone.
_I_TERMINATION = ("termination_by xs => sizeOf xs\n"
                  "decreasing_by\n"
                  "  simp_wf\n"
                  "  show sizeOf ch < sizeOf xs\n"
                  "  have hmem : e ∈ xs :=\n"
                  "    ((List.mergeSort_perm xs (fun a b => a.1 ≤ b.1)).mem_iff).mp h\n"
                  "  have h1 : sizeOf e ≤ sizeOf xs := le_of_lt (List.sizeOf_lt_of_mem hmem)\n"
                  "  have hh2 : sizeOf ch < sizeOf e.2 := by rw [h2]; simp\n"
                  "  have h3 : sizeOf e.2 < sizeOf e := by cases e; simp\n"
                  "  omega")

# The impl's own descent-measure justification (mirrors the spec walk's).
_I_MEASURE = ("  have hmem : e ∈ xs :=\n"
              "    ((List.mergeSort_perm xs (fun a b => a.1 ≤ b.1)).mem_iff).mp h\n"
              "  have h1 : sizeOf e ≤ sizeOf xs := le_of_lt (List.sizeOf_lt_of_mem hmem)\n"
              "  have hh2 : sizeOf ch < sizeOf e.2 := by rw [h2]; simp")

# --- proof region (touched only by the two soundness positives) ---

# The directory arm of the do-block unfolding lemma.
_P_UNFOLD_DIR = """      | dir s ch =>
        by_cases hr : recurse (nm, FSNode.dir s ch) = true
        · simp only [entryIsDir, Bool.true_and, hr, if_true]
          rfl
        · have hr' : (recurse (nm, FSNode.dir s ch) = true) = False := by simp [hr]
          simp only [entryIsDir, Bool.true_and, hr', if_false, List.append_nil]
          rfl]"""

# The non-directory arm of the do-block unfolding lemma.
_P_UNFOLD_FILE = """      | file =>
        simp only [entryIsDir, Bool.false_and, Bool.false_eq_true, if_false, List.append_nil]
        rfl"""

# The directory arm of the per-entry body-equality lemma.
_P_BODY_DIR = """  | dir b ch =>
    simp only [entryIsDir, Bool.true_and]
    rw [ih b ch rfl]"""

# The guard as it appears in the per-entry body-equality lemma's STATEMENT.
_P_BODY_STMT = """    (if entryIsDir e.2 && recurse e then
       (match e.2 with
        | .dir _ ch => implementation_collect recurse ch
        | .file => []) else []) ="""

# The frozen closing tactic body of the obligation.
_P_CLOSE = """theorem correct_collect : ∀ (recurse : DirEntry → Bool) (entries0 : List DirEntry),
    problem_spec_collect recurse entries0 (implementation_collect recurse entries0) := by
  intro recurse entries0
  show implementation_collect recurse entries0 = collectTree recurse entries0
  exact main_induction recurse entries0"""


# ===========================================================================
# POSITIVE CONTROLS (soundness). A structurally different but CORRECT
# implementation MUST verify; if a faithful correct implementation cannot
# satisfy the frozen obligation the spec is SPEC-TOO-STRONG.
#
# NOTE on the reproofs. Both positives are OBSERVATIONALLY EQUAL to the frozen
# implementation, and both nevertheless FAIL to build under the frozen tactic
# script (measured: `rfl` failed / `rewrite` found no occurrence of the guard's
# frozen form). That is precisely the phenomenon that makes a bare rejection
# uninformative on this backend, and it is why every reject case below carries a
# witness. Each positive is therefore re-proved: the tactic body is retuned to
# the reshaped form while the theorem STATEMENT stays byte-identical, no helper
# lemma is added, no `sorry`/`admit`/`native_decide` is used, and no new
# declaration appears. Both were confirmed to close by a real build.
#
# Ports nagini cases pos-1 (operand-swapped conjunction) and pos-2
# (classification unfolded to a definitionally equal surface syntax). Nagini's
# pos-3 (bind the classification to a local, then conjoin) is NOT ported as a
# third positive, and the AUDIT re-derived the reason with a real build rather
# than taking it on faith: the `let`-bound form
# `let isDir := entryIsDir e.2; if isDir && recurse e then …` zeta-reduces to the
# frozen guard, so it verifies under the frozen tactic script COMPLETELY
# UNCHANGED (measured, exit 0). A positive that needs no reproof at all is
# indistinguishable from re-running the frozen file, which is what makes it a
# duplicate rather than a case — unlike the two positives shipped here, both of
# which genuinely break the frozen script and must be re-proved. See
# `assessment`.
# ===========================================================================

_pos_classify_unfolded = _swap(
    _swap(
        _swap(
            _BASE, _I_CLASSIFY,
            "def entryIsDir : FSNode → Bool\n"
            "  | .file => false\n"
            "  | .dir _ _ => !false"),
        _P_UNFOLD_DIR,
        _P_UNFOLD_DIR
        .replace("simp only [entryIsDir, Bool.true_and, hr, if_true]",
                 "simp only [entryIsDir, Bool.not_false, Bool.true_and, hr, if_true]")
        .replace("simp only [entryIsDir, Bool.true_and, hr', if_false, List.append_nil]",
                 "simp only [entryIsDir, Bool.not_false, Bool.true_and, hr', "
                 "if_false, List.append_nil]")),
    _P_BODY_DIR,
    _P_BODY_DIR.replace("simp only [entryIsDir, Bool.true_and]",
                        "simp only [entryIsDir, Bool.not_false, Bool.true_and]"))

# Guard operands commuted: select-then-classify instead of classify-then-select.
# The guard's syntactic form is named in three places in the proof (the unfolding
# lemma's `show`, the loop-body abbreviation, and the body-equality lemma's
# statement), so the reproof mirrors the commutation into each and swaps the two
# Boolean normalisation lemmas for their commuted counterparts.
_pos_guard_commuted = _swap(
    _swap(
        _swap(
            _swap(_BASE, _I_GUARD, "      if recurse e && entryIsDir e.2 then")
            .replace("(entryIsDir a.2 && recurse a)", "(recurse a && entryIsDir a.2)")
            .replace("if entryIsDir p.1.2 && recurse p.1 then",
                     "if recurse p.1 && entryIsDir p.1.2 then"),
            _P_BODY_STMT,
            _P_BODY_STMT.replace("if entryIsDir e.2 && recurse e then",
                                 "if recurse e && entryIsDir e.2 then")),
        _P_BODY_DIR,
        """  | dir b ch =>
    simp only [entryIsDir, Bool.and_true]
    rw [ih b ch rfl]"""),
    _P_UNFOLD_DIR,
    """      | dir s ch =>
        by_cases hr : recurse (nm, FSNode.dir s ch) = true
        · simp only [entryIsDir, Bool.and_true, hr, if_true]
          rfl
        · have hr' : (recurse (nm, FSNode.dir s ch) = true) = False := by simp [hr]
          simp only [entryIsDir, Bool.and_true, hr', if_false, List.append_nil]
          rfl]""")
_pos_guard_commuted = _swap(
    _pos_guard_commuted, _P_UNFOLD_FILE,
    """      | file =>
        simp only [entryIsDir, Bool.and_false, Bool.false_eq_true, if_false, List.append_nil]
        rfl""")


# ===========================================================================
# ADMISSIBILITY. The frozen obligation carries NO precondition hypothesis (the
# modeled behavior is total, so the `∀` is unguarded), so nagini's
# precondition-admission probe has no binder to attack here. The honest analogue
# is to confirm the obligation is SATISFIABLE at the concrete, scenario-shaped
# input rather than only in the abstract: a selected entry that resolves to a
# directory THROUGH a symbolic link and holds a single file. Discharged as a
# `have` inside the existing tactic body — nothing new is declared and the
# statement is byte-identical — then the frozen obligation is closed verbatim.
# ===========================================================================

# AUDIT REPAIR. The ported form of this case discharged its ground `have` by
# `exact main_induction _ _` — i.e. it INSTANTIATED the very theorem being
# proven at the scenario input. Instantiating a `∀`-theorem at a point cannot
# fail, so that case could not fail for the reason its rationale claimed
# (satisfiability at the interesting sub-domain) and tested nothing while passing
# honestly. Repaired to pin the ground VALUE instead: the walk at the scenario
# input is computed to a literal two-entry list, and the spec predicate is then
# discharged OF THAT LITERAL. This can fail — it does if the modeled walk does
# not descend through an entry that resolves to a directory via a symbolic link,
# because the contained entry would then be absent from `hwalk`'s right-hand
# side. Confirmed to close by a real build (exit 0).
_admiss_ground = _swap(
    _BASE, _P_CLOSE,
    """theorem correct_collect : ∀ (recurse : DirEntry → Bool) (entries0 : List DirEntry),
    problem_spec_collect recurse entries0 (implementation_collect recurse entries0) := by
  have hchild : collectTree (fun _ => true) [("t", FSNode.file)] = [("t", FSNode.file)] := by
    rw [collectTree, sortByName, List.mergeSort_singleton]; simp
  have hwalk : collectTree (fun _ => true) [("d", FSNode.dir true [("t", FSNode.file)])]
      = [("d", FSNode.dir true [("t", FSNode.file)]), ("t", FSNode.file)] := by
    rw [collectTree, sortByName, List.mergeSort_singleton]; simp [hchild]
  have _ground : problem_spec_collect (fun _ => true)
      [("d", FSNode.dir true [("t", FSNode.file)])]
      [("d", FSNode.dir true [("t", FSNode.file)]), ("t", FSNode.file)] := by
    show [("d", FSNode.dir true [("t", FSNode.file)]), ("t", FSNode.file)]
      = collectTree (fun _ => true) [("d", FSNode.dir true [("t", FSNode.file)])]
    exact hwalk.symm
  intro recurse entries0
  show implementation_collect recurse entries0 = collectTree recurse entries0
  exact main_induction recurse entries0""")


# ===========================================================================
# UNIQUENESS / SPEC-TOO-WEAK rivals. Each shares the frozen spec exactly and
# changes ONLY the implementation; if any VERIFIES the spec is SPEC-TOO-WEAK.
# Each carries (a) the refinement argument that its faithful real patch would
# NOT resolve, so a verifying rival is a true verify-does-not-imply-resolve
# break rather than an artifact, and (b) a witness refuting it at one concrete
# input, checked to hold of the rival and to FAIL on the frozen solution.
# ===========================================================================

# The regression itself: an entry that is a symbolic link is not classified as a
# directory, so a linked directory is never descended into.
_rej_link_not_dir = _swap(
    _BASE, _I_CLASSIFY,
    "def entryIsDir : FSNode → Bool\n"
    "  | .file => false\n"
    "  | .dir isSymlink _ => !isSymlink")

# Drop the caller's selection predicate from the descent guard.
_rej_drop_predicate = _swap(_BASE, _I_GUARD, "      if entryIsDir e.2 then")

# Never descend at all.
_rej_never_descend = _swap(
    _BASE, _I_GUARD, "      if entryIsDir e.2 && recurse e && false then")

# Partial domain: apply the descent rule to every entry of a level EXCEPT the
# first, which is never descended into.
_rej_skip_first = _swap(
    _BASE, _I_LOOP,
    "    let mut acc := entries\n"
    "    let mut isFirst := true\n"
    "    for h : e in entries do\n"
    "      if entryIsDir e.2 && recurse e && !isFirst then\n"
    "        match h2 : e.2 with\n"
    "        | .dir _ ch => acc := acc ++ implementation_collect recurse ch\n"
    "        | .file => pure ()\n"
    "      isFirst := false\n"
    "    return acc")

# Emit each level in its incoming order instead of in name order. (The descent
# measure is rejustified from list membership directly, since the level is no
# longer permuted — otherwise the variant would not elaborate at all.)
_rej_unordered = _swap(
    _swap(_BASE, _I_ORDER, "    let entries := xs\n    let mut acc := entries"),
    _I_MEASURE,
    "  have hmem : e ∈ xs := h\n"
    "  have h1 : sizeOf e ≤ sizeOf xs := le_of_lt (List.sizeOf_lt_of_mem hmem)\n"
    "  have hh2 : sizeOf ch < sizeOf e.2 := by rw [h2]; simp")

# Emit a descended subtree BEFORE the level it was reached from.
_rej_subtree_first = _swap(
    _BASE, _I_PLACE,
    "        | .dir _ ch => acc := implementation_collect recurse ch ++ acc")

# AUDIT ADDITIONS. The ported battery attacked WHICH entries are descended into,
# the classification, and both orderings — but never the commitment that the
# level itself is emitted WHOLE AND ONCE. Every shipped rival changes only the
# descent, so all six leave the emitted level exactly `sortByName xs`; a spec
# that pinned the descent but let an impl drop or duplicate members of the level
# would pass the whole ported battery. Both rivals below attack that commitment
# from the two opposite sides, at the cheapest input that shows it (a level of a
# single non-directory entry, where no descent happens at all on either side, so
# nothing but level emission can be doing the work).

# Emit only the directory entries of a level, dropping non-directory entries from
# the output while still descending correctly.
_rej_level_incomplete = _swap(
    _BASE, _I_ORDER,
    "    let entries := sortByName xs\n"
    "    let mut acc := entries.filter (fun e => entryIsDir e.2)")

# Emit every entry of a level TWICE.
_rej_level_duplicated = _swap(
    _BASE, _I_ORDER,
    "    let entries := sortByName xs\n    let mut acc := entries ++ entries")

# SECOND-AUDIT ADDITIONS. Every rival above (including the two added by the first
# audit) is refuted at a tree of depth at most two whose child levels hold only
# non-directory entries, and at a level holding at most one directory. Two
# commitments of the walk are invisible at every one of those points, so a spec
# that dropped either would pass the whole battery:
#
#   * that the descent is TRANSITIVE — the walk continues into a directory found
#     inside a directory, to unbounded depth, rather than stopping one level down.
#     No existing witness has a grandchild directory, so a one-level-only descent
#     agrees with the spec at every input the battery visits.
#   * that SIBLING subtrees are concatenated in their parents' name order — the
#     level's own order is pinned by `reject-level-order-not-by-name`, but the
#     order in which two DESCENDED subtrees follow it is a separate commitment,
#     and the only multi-directory level in the battery
#     (`reject-first-entry-never-descended`) is refuted by an OMITTED subtree, so
#     a permutation of present subtrees is not something it can see.

# Descend exactly one level: a selected directory's own children are emitted, but
# the walk never recurses into a directory found among them. (Emitting the child
# level with the per-level ordering applied, so the rival is wrong ONLY about
# depth — it agrees with the spec on membership and on order at every level it
# does emit. With the recursive call gone the definition is structural, so the
# frozen termination clause is dropped rather than rejustified.)
_rej_depth_limited = _swap(
    _swap(_BASE, _I_PLACE,
          "        | .dir _ ch => acc := acc ++ sortByName ch"),
    _I_TERMINATION, "")

# Walk the level's entries in reverse, so the descended subtrees are appended in
# the opposite order to their parents'. The level itself is still emitted whole,
# in name order, and every subtree still appears exactly once: only the order of
# the subtrees among themselves is wrong. (The descent measure is rejustified
# through `List.mem_reverse`, since membership now comes from the reversed list.)
_rej_sibling_order = _swap(
    _swap(_BASE, _I_FOR, "    for h : e in entries.reverse do"),
    _I_MEASURE_MEM,
    "  have hmem : e ∈ xs :=\n"
    "    ((List.mergeSort_perm xs (fun a b => a.1 ≤ b.1)).mem_iff).mp\n"
    "      (List.mem_reverse.mp h)\n")


SPEC_TESTS = [
    # ---------------------------------------------------------------- positives
    {
        "id": "pos-classification-unfolded",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_classify_unfolded,
        "rationale": "the directory arm of the classification is written in a "
                     "definitionally equal surface syntax (the negation of the "
                     "opposite constant rather than the constant itself). The "
                     "classification agrees with the frozen one on every entry, so "
                     "the walk is unchanged on every input and `result = <the "
                     "in-order walk>` still holds. Must verify, else the "
                     "classification clause is SPEC-TOO-STRONG — pinned to one "
                     "syntactic form rather than to the behavior. Proof: the "
                     "reshape changes how the guard normalises, so the two "
                     "normalisation steps of the frozen script are given the extra "
                     "Boolean simp lemma; statement byte-identical, no helper "
                     "lemma, nothing assumed. Confirmed to close by a real build. "
                     "Ports nagini's pos-2 (classification unfolded inline).",
    },
    {
        "id": "pos-guard-operands-commuted",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_guard_commuted,
        "rationale": "the descent guard's two conjuncts are commuted: the caller's "
                     "selection is tested before the directory classification "
                     "instead of after. Both operands are pure Booleans, so the "
                     "guard has the same value on every entry, the walk is "
                     "unchanged, and `result = <the in-order walk>` still holds. "
                     "Must verify, else the descent-condition clause is "
                     "SPEC-TOO-STRONG on the ORDER of a conjunction it should not "
                     "observe. Proof: the guard's syntactic form is named in three "
                     "places in the frozen script, so the commutation is mirrored "
                     "into each and the two Boolean normalisation lemmas are "
                     "swapped for their commuted counterparts; statement "
                     "byte-identical, no helper lemma, nothing assumed. Confirmed "
                     "to close by a real build. Ports nagini's pos-1 "
                     "(operand-swapped conjunction). This case is also the direct "
                     "evidence for why every reject case below needs a witness: a "
                     "provably CORRECT reshape fails the frozen script, so "
                     "'did not verify' cannot by itself mean 'the spec refutes it'.",
    },
    {
        "id": "admiss-ground-linked-directory",
        "kind": "admissibility",
        "expect": "verify",
        "module": _admiss_ground,
        "rationale": "the obligation is discharged at the ground scenario-shaped "
                     "input — a selected entry that resolves to a directory THROUGH "
                     "a symbolic link and holds a single file — as a `have` inside "
                     "the existing tactic body, then the frozen obligation is "
                     "closed verbatim. Verifies, else the modeled behavior is "
                     "unsatisfiable at exactly the input the reported scenario "
                     "exercises (the analogue of PRECOND-TOO-STRONG: an obligation "
                     "that holds only vacuously or only away from the interesting "
                     "sub-domain). Nothing is assumed: no new declaration, no "
                     "helper lemma, the statement is byte-identical. Confirmed by a "
                     "real build. Ports nagini's admissibility probe; the frozen "
                     "obligation carries no precondition hypothesis here, so there "
                     "is no precondition binder to attack instead.",
    },

    # ------------------------------------------------------------------ rivals
    {
        "id": "reject-linked-directory-not-descended",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_link_not_dir,
        "refinement": "this is the regressed behavior itself: an entry that is "
                      "ITSELF a symbolic link is not classified as a directory, so "
                      "the walk never descends into it even when its target is a "
                      "directory and the caller selects it. Its faithful real patch "
                      "keeps the non-following classification, so a selected "
                      "linked directory is never entered and everything inside it "
                      "goes uncollected. The F2P test builds exactly that shape — a "
                      "directory holding a test file, plus a symbolic link to that "
                      "directory — and asserts BOTH copies are collected; under "
                      "this rival only the direct copy is, so the asserted outcome "
                      "count is short and the faithful patch does NOT resolve. "
                      "(This is the pre-patch classification the bundle's own "
                      "prepatch file carries, so G-DIFF independently confirms the "
                      "spec fails here.)",
        "rationale": "REJECT from the classification clause — the behavioural "
                     "discriminator. The spec's walk descends into every entry that "
                     "RESOLVES to a directory, symbolic link or not; this rival "
                     "descends only into non-link directories, so at a level whose "
                     "single selected entry is a linked directory holding one file "
                     "the spec emits two entries and the rival emits one. If it "
                     "verified => SPEC-TOO-WEAK: the spec would not sense the "
                     "regression at all. Binder spread: `recurse` at always-select, "
                     "`entries0` at a one-entry level whose entry is a LINKED "
                     "directory — the only witness that moves the link setting to "
                     "true, so this input is demonstrated live rather than held "
                     "fixed across the battery.",
        "witness": (
            "-- Refuted at the reported scenario: one selected entry resolving to a\n"
            "-- directory through a symbolic link, holding a single file. Neither\n"
            "-- side is `decide`-able (both are well-founded recursions and the\n"
            "-- entry-node type has no decidable equality), so both are evaluated by\n"
            "-- hand: the child level is discharged as a local `have`, then each\n"
            "-- recursion is unfolded once. The spec's walk emits the entry AND the\n"
            "-- file it contains; the rival emits only the entry.\n"
            "example : ¬ problem_spec_collect (fun _ => true)"
            " [(\"a\", FSNode.dir true [(\"b\", FSNode.file)])]\n"
            "    (implementation_collect (fun _ => true)"
            " [(\"a\", FSNode.dir true [(\"b\", FSNode.file)])]) := by\n"
            "  have hi : implementation_collect (fun _ => true) [(\"b\", FSNode.file)]"
            " = [(\"b\", FSNode.file)] := by\n"
            "    rw [implementation_collect]; simp [sortByName, entryIsDir, Id.run]; rfl\n"
            "  have hc : collectTree (fun _ => true) [(\"b\", FSNode.file)]"
            " = [(\"b\", FSNode.file)] := by\n"
            "    rw [collectTree, sortByName, List.mergeSort_singleton]; simp\n"
            "  have hgold : collectTree (fun _ => true)"
            " [(\"a\", FSNode.dir true [(\"b\", FSNode.file)])]\n"
            "      = [(\"a\", FSNode.dir true [(\"b\", FSNode.file)]), (\"b\", FSNode.file)] := by\n"
            "    rw [collectTree, sortByName, List.mergeSort_singleton]; simp [hc]\n"
            "  have himpl : implementation_collect (fun _ => true)"
            " [(\"a\", FSNode.dir true [(\"b\", FSNode.file)])]\n"
            "      = [(\"a\", FSNode.dir true [(\"b\", FSNode.file)])] := by\n"
            "    rw [implementation_collect]; simp [sortByName, entryIsDir, Id.run, hi]; rfl\n"
            "  unfold problem_spec_collect\n"
            "  rw [himpl, hgold]\n"
            "  simp\n"
        ),
    },
    {
        "id": "reject-selection-predicate-ignored",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_drop_predicate,
        "refinement": "drops the caller's selection predicate from the descent "
                      "guard, descending into every entry that resolves to a "
                      "directory regardless of whether the caller wants it walked. "
                      "Its faithful real patch removes the predicate conjunct from "
                      "the guard, so the collector would walk into directories the "
                      "caller's filter exists to exclude — the P2P suite pins that "
                      "filter's effect directly, asserting that certain "
                      "conventionally-excluded directories and detected virtual "
                      "environments are NOT walked into. Those tests would fail, so "
                      "the faithful patch does NOT resolve.",
        "rationale": "REJECT from the selection conjunct of the descent condition. "
                     "The spec descends into an entry only when the caller's "
                     "predicate selects it; this rival descends whenever the entry "
                     "resolves to a directory, so wherever the predicate is false "
                     "on a directory entry the rival emits that directory's "
                     "contents and the spec does not. If it verified => "
                     "SPEC-TOO-WEAK: the predicate conjunct would be entirely "
                     "unconstrained, and the spec would accept a collector that "
                     "ignores its caller's filter. Binder spread: this is the ONLY "
                     "witness that moves `recurse` to never-select, which is also "
                     "the only setting that can expose the rival — it agrees with "
                     "the spec at every point where the predicate is true — so "
                     "without this case that binder would be held at one value by "
                     "the whole battery.",
        "witness": (
            "-- Refuted where the caller selects NOTHING: the spec emits the level\n"
            "-- alone, the rival descends anyway and emits the contained file too.\n"
            "-- Evaluated by hand (neither side reduces by `decide`).\n"
            "example : ¬ problem_spec_collect (fun _ => false)"
            " [(\"a\", FSNode.dir false [(\"b\", FSNode.file)])]\n"
            "    (implementation_collect (fun _ => false)"
            " [(\"a\", FSNode.dir false [(\"b\", FSNode.file)])]) := by\n"
            "  have hi : implementation_collect (fun _ => false) [(\"b\", FSNode.file)]"
            " = [(\"b\", FSNode.file)] := by\n"
            "    rw [implementation_collect]; simp [sortByName, entryIsDir, Id.run]; rfl\n"
            "  have hgold : collectTree (fun _ => false)"
            " [(\"a\", FSNode.dir false [(\"b\", FSNode.file)])]\n"
            "      = [(\"a\", FSNode.dir false [(\"b\", FSNode.file)])] := by\n"
            "    rw [collectTree, sortByName, List.mergeSort_singleton]; simp\n"
            "  have himpl : implementation_collect (fun _ => false)"
            " [(\"a\", FSNode.dir false [(\"b\", FSNode.file)])]\n"
            "      = [(\"a\", FSNode.dir false [(\"b\", FSNode.file)]), (\"b\", FSNode.file)] := by\n"
            "    rw [implementation_collect]; simp [sortByName, entryIsDir, Id.run, hi]; rfl\n"
            "  unfold problem_spec_collect\n"
            "  rw [himpl, hgold]\n"
            "  simp\n"
        ),
    },
    {
        "id": "reject-never-descends",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_never_descend,
        "refinement": "never descends into anything: only the top level is ever "
                      "emitted. Its faithful real patch makes the descent guard "
                      "unsatisfiable, so nothing below the starting directory is "
                      "collected — the F2P test's own nested test file is not "
                      "reached, and essentially every collection test in the P2P "
                      "set that relies on walking into a subdirectory fails too. It "
                      "does NOT resolve. (A cheap supporting near-miss, but it "
                      "attacks a clause the other rivals do not: it is refuted on a "
                      "PLAIN directory, where the classification and the selection "
                      "predicate both agree with the spec, so what it isolates is "
                      "the existence of descent itself rather than either "
                      "condition on it.)",
        "rationale": "REJECT from the descent clause as a whole: the spec's walk "
                     "emits the contents of every selected directory entry, and "
                     "this rival emits none, so at a level holding one selected "
                     "plain directory with one file the spec emits two entries and "
                     "the rival one. Refuted at an input DISTINCT from every other "
                     "rival (a PLAIN directory, at its own names) so its "
                     "sub-domain claim is demonstrated rather than inherited: "
                     "unlike the classification rival it fails even where the entry "
                     "is not a link, and unlike the predicate rival it fails where "
                     "the predicate is true.",
        "witness": (
            "-- Refuted on a PLAIN (non-link) selected directory, so neither the\n"
            "-- classification nor the selection predicate is doing the work here.\n"
            "example : ¬ problem_spec_collect (fun _ => true)"
            " [(\"d\", FSNode.dir false [(\"f\", FSNode.file)])]\n"
            "    (implementation_collect (fun _ => true)"
            " [(\"d\", FSNode.dir false [(\"f\", FSNode.file)])]) := by\n"
            "  have hi : implementation_collect (fun _ => true) [(\"f\", FSNode.file)]"
            " = [(\"f\", FSNode.file)] := by\n"
            "    rw [implementation_collect]; simp [sortByName, entryIsDir, Id.run]; rfl\n"
            "  have hc : collectTree (fun _ => true) [(\"f\", FSNode.file)]"
            " = [(\"f\", FSNode.file)] := by\n"
            "    rw [collectTree, sortByName, List.mergeSort_singleton]; simp\n"
            "  have hgold : collectTree (fun _ => true)"
            " [(\"d\", FSNode.dir false [(\"f\", FSNode.file)])]\n"
            "      = [(\"d\", FSNode.dir false [(\"f\", FSNode.file)]), (\"f\", FSNode.file)] := by\n"
            "    rw [collectTree, sortByName, List.mergeSort_singleton]; simp [hc]\n"
            "  have himpl : implementation_collect (fun _ => true)"
            " [(\"d\", FSNode.dir false [(\"f\", FSNode.file)])]\n"
            "      = [(\"d\", FSNode.dir false [(\"f\", FSNode.file)])] := by\n"
            "    rw [implementation_collect]; simp [sortByName, entryIsDir, Id.run, hi]; rfl\n"
            "  unfold problem_spec_collect\n"
            "  rw [himpl, hgold]\n"
            "  simp\n"
        ),
    },
    {
        "id": "reject-first-entry-never-descended",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_skip_first,
        "refinement": "a partial-domain miss: the descent rule is applied "
                      "correctly to every entry of a level EXCEPT the first, which "
                      "is never descended into. Its faithful real patch "
                      "special-cases the first entry of each ordered level, so any "
                      "directory that happens to sort first within its parent is "
                      "silently not walked — and since the level is name-ordered, "
                      "WHICH directory that is depends only on naming. The F2P "
                      "test's own tree is vulnerable (its two collected "
                      "directories differ only by name, and the alphabetically "
                      "first one would be skipped), and collection would diverge "
                      "from the intended walk on essentially any real tree, so it "
                      "does NOT resolve.",
        "rationale": "REJECT from the UNIFORMITY commitment: the spec's walk "
                     "applies the same rule to every entry of a level, so a rival "
                     "that pins all-but-one position must still fail wherever the "
                     "excepted position holds a descendable entry. At a two-entry "
                     "level of two selected plain directories the spec emits both "
                     "subtrees and the rival omits the first's. If it verified => "
                     "SPEC-TOO-WEAK on the leading-position sub-domain — the spec "
                     "would constrain the walk only up to a positional exception. "
                     "Binder spread: the only witness whose `entries0` is a "
                     "MULTI-ENTRY level of directories, so position within a level "
                     "is exercised at all; the other rivals' single-entry levels "
                     "cannot distinguish a positional rule from a uniform one. "
                     "Ports nagini's partial-domain-on-the-first-index rival.",
        "witness": (
            "-- Refuted at a two-entry level of two selected plain directories, given\n"
            "-- in name order. The per-level ordering is reduced to the `List Char`\n"
            "-- comparison that IS decidable (the string comparison itself is not),\n"
            "-- then both walks are evaluated by hand: the spec emits both children,\n"
            "-- the rival omits the first entry's.\n"
            "example : ¬ problem_spec_collect (fun _ => true)\n"
            "      [(\"a\", FSNode.dir false [(\"x\", FSNode.file)]),"
            " (\"b\", FSNode.dir false [(\"y\", FSNode.file)])]\n"
            "    (implementation_collect (fun _ => true)\n"
            "      [(\"a\", FSNode.dir false [(\"x\", FSNode.file)]),"
            " (\"b\", FSNode.dir false [(\"y\", FSNode.file)])]) := by\n"
            "  have hix : implementation_collect (fun _ => true) [(\"x\", FSNode.file)]"
            " = [(\"x\", FSNode.file)] := by\n"
            "    rw [implementation_collect]; simp [sortByName, entryIsDir, Id.run]; rfl\n"
            "  have hiy : implementation_collect (fun _ => true) [(\"y\", FSNode.file)]"
            " = [(\"y\", FSNode.file)] := by\n"
            "    rw [implementation_collect]; simp [sortByName, entryIsDir, Id.run]; rfl\n"
            "  have hcx : collectTree (fun _ => true) [(\"x\", FSNode.file)]"
            " = [(\"x\", FSNode.file)] := by\n"
            "    rw [collectTree, sortByName, List.mergeSort_singleton]; simp\n"
            "  have hcy : collectTree (fun _ => true) [(\"y\", FSNode.file)]"
            " = [(\"y\", FSNode.file)] := by\n"
            "    rw [collectTree, sortByName, List.mergeSort_singleton]; simp\n"
            "  have hsort : sortByName [(\"a\", FSNode.dir false [(\"x\", FSNode.file)]),"
            " (\"b\", FSNode.dir false [(\"y\", FSNode.file)])]\n"
            "      = [(\"a\", FSNode.dir false [(\"x\", FSNode.file)]),"
            " (\"b\", FSNode.dir false [(\"y\", FSNode.file)])] := by\n"
            "    simp [sortByName, List.mergeSort, List.merge]\n"
            "    decide\n"
            "  have hgold : collectTree (fun _ => true)\n"
            "      [(\"a\", FSNode.dir false [(\"x\", FSNode.file)]),"
            " (\"b\", FSNode.dir false [(\"y\", FSNode.file)])]\n"
            "      = [(\"a\", FSNode.dir false [(\"x\", FSNode.file)]),"
            " (\"b\", FSNode.dir false [(\"y\", FSNode.file)]),\n"
            "         (\"x\", FSNode.file), (\"y\", FSNode.file)] := by\n"
            "    rw [collectTree, hsort]; simp [hcx, hcy]\n"
            "  have himpl : implementation_collect (fun _ => true)\n"
            "      [(\"a\", FSNode.dir false [(\"x\", FSNode.file)]),"
            " (\"b\", FSNode.dir false [(\"y\", FSNode.file)])]\n"
            "      = [(\"a\", FSNode.dir false [(\"x\", FSNode.file)]),"
            " (\"b\", FSNode.dir false [(\"y\", FSNode.file)]),\n"
            "         (\"y\", FSNode.file)] := by\n"
            "    rw [implementation_collect, hsort]; simp [entryIsDir, Id.run, hix, hiy]; rfl\n"
            "  unfold problem_spec_collect\n"
            "  rw [himpl, hgold]\n"
            "  simp\n"
        ),
    },
    {
        "id": "reject-level-order-not-by-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_unordered,
        "refinement": "emits each level in whatever order the platform enumerated "
                      "it rather than in name order. Its faithful real patch drops "
                      "the per-level ordering step, so collection order becomes "
                      "filesystem-dependent: the reported order of collected items "
                      "stops being deterministic across platforms and runs. The "
                      "collection-order behavior the suite pins would then hold "
                      "only accidentally — several P2P tests assert the ORDER in "
                      "which items are reported, and the F2P test's own assertion "
                      "is over a tree with more than one entry per level — so the "
                      "faithful patch does NOT resolve.",
        "rationale": "REJECT from the per-level ORDERING clause. The spec's walk "
                     "emits each level in name order; this rival emits it in "
                     "incoming order, so at a level given out of name order the two "
                     "results are permutations of each other and differ. If it "
                     "verified => SPEC-TOO-WEAK on ordering: the spec would pin "
                     "WHICH entries are emitted but not their order, and a "
                     "nondeterministically-ordered collector would satisfy it. This "
                     "clause is independent of every other rival's — none of them "
                     "perturbs order — and it is one the flattened nagini carrier "
                     "could not state at all, since its per-index postcondition "
                     "fixes the ordering by construction. Binder spread: the only "
                     "witness whose `entries0` is given OUT of name order.",
        "witness": (
            "-- Refuted at a flat two-entry level supplied out of name order. The\n"
            "-- ordering step is reduced to the `List Char` comparison that IS\n"
            "-- decidable, then both sides are evaluated: the spec reorders, the\n"
            "-- rival preserves the incoming order.\n"
            "example : ¬ problem_spec_collect (fun _ => true)"
            " [(\"b\", FSNode.file), (\"a\", FSNode.file)]\n"
            "    (implementation_collect (fun _ => true)"
            " [(\"b\", FSNode.file), (\"a\", FSNode.file)]) := by\n"
            "  have hsort : sortByName [(\"b\", FSNode.file), (\"a\", FSNode.file)]\n"
            "      = [(\"a\", FSNode.file), (\"b\", FSNode.file)] := by\n"
            "    simp [sortByName, List.mergeSort, List.merge]\n"
            "    decide\n"
            "  have hgold : collectTree (fun _ => true)"
            " [(\"b\", FSNode.file), (\"a\", FSNode.file)]\n"
            "      = [(\"a\", FSNode.file), (\"b\", FSNode.file)] := by\n"
            "    rw [collectTree, hsort]; simp\n"
            # AUDIT REPAIR: `hsort` must be in THIS simp set too. Without it the
            # per-level ordering term stays unreduced on the frozen solution, the
            # loop over it never unfolds, and the gold-side build failed by an
            # UNFOLDING failure rather than by refuting anything — measured: the
            # claim that is TRUE of the frozen impl at this input failed there
            # identically (same `rfl` error on the same unreduced `forIn'` term),
            # so the gold exit code tracked the shape of the term and not the
            # truth of the claim. With `hsort` supplied the ordering step rewrites
            # to a literal on both files, the loop reduces, and the gold-side
            # failure is a concrete value clash (`pure [a, b] = [b, a]`) while the
            # TRUE claim now builds. On the rival there is no ordering step, so
            # `hsort` is simply unused there.
            "  have himpl : implementation_collect (fun _ => true)"
            " [(\"b\", FSNode.file), (\"a\", FSNode.file)]\n"
            "      = [(\"b\", FSNode.file), (\"a\", FSNode.file)] := by\n"
            "    rw [implementation_collect]; simp [hsort, entryIsDir, Id.run]; rfl\n"
            "  unfold problem_spec_collect\n"
            "  rw [himpl, hgold]\n"
            "  simp\n"
        ),
    },
    {
        "id": "reject-subtree-emitted-before-level",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_subtree_first,
        "refinement": "emits a descended subtree BEFORE the level it was reached "
                      "from, inverting the walk's shape from level-first to "
                      "subtree-first. Its faithful real patch yields the recursive "
                      "walk ahead of the current level's own entries, so items are "
                      "reported deepest-first: a nested item appears before the "
                      "directory that contains it. The suite pins the reported "
                      "order of collected items, and the reversal shows up on any "
                      "tree with a walked subdirectory — including the F2P test's "
                      "own — so the faithful patch does NOT resolve.",
        "rationale": "REJECT from the LEVEL-BEFORE-SUBTREE commitment: the spec's "
                     "walk emits a level in full and only then the subtrees it "
                     "descends into, so at a level holding one selected directory "
                     "with one file the spec emits the directory then the file "
                     "while the rival emits the file then the directory. The two "
                     "results contain exactly the same entries, which is what makes "
                     "this clause independent: a spec pinning only membership, or "
                     "only per-level order, would accept the rival. If it verified "
                     "=> SPEC-TOO-WEAK on the traversal shape. Refuted at its own "
                     "input (a plain selected directory at names used by no other "
                     "witness) rather than sharing the never-descend rival's, "
                     "because the two fail for different reasons: that rival OMITS "
                     "entries, this one REORDERS them, and a witness that only "
                     "counted entries would miss this rival entirely. This clause "
                     "also has no nagini counterpart — the flattened per-index "
                     "carrier has no notion of a subtree's placement.",
        "witness": (
            "-- Refuted at a selected plain directory holding one file: same entries\n"
            "-- on both sides, opposite order. Evaluated by hand; the discriminator\n"
            "-- is the position of the contained entry, not the set of entries.\n"
            "example : ¬ problem_spec_collect (fun _ => true)"
            " [(\"p\", FSNode.dir false [(\"q\", FSNode.file)])]\n"
            "    (implementation_collect (fun _ => true)"
            " [(\"p\", FSNode.dir false [(\"q\", FSNode.file)])]) := by\n"
            "  have hi : implementation_collect (fun _ => true) [(\"q\", FSNode.file)]"
            " = [(\"q\", FSNode.file)] := by\n"
            "    rw [implementation_collect]; simp [sortByName, entryIsDir, Id.run]; rfl\n"
            "  have hc : collectTree (fun _ => true) [(\"q\", FSNode.file)]"
            " = [(\"q\", FSNode.file)] := by\n"
            "    rw [collectTree, sortByName, List.mergeSort_singleton]; simp\n"
            "  have hgold : collectTree (fun _ => true)"
            " [(\"p\", FSNode.dir false [(\"q\", FSNode.file)])]\n"
            "      = [(\"p\", FSNode.dir false [(\"q\", FSNode.file)]), (\"q\", FSNode.file)] := by\n"
            "    rw [collectTree, sortByName, List.mergeSort_singleton]; simp [hc]\n"
            "  have himpl : implementation_collect (fun _ => true)"
            " [(\"p\", FSNode.dir false [(\"q\", FSNode.file)])]\n"
            "      = [(\"q\", FSNode.file), (\"p\", FSNode.dir false [(\"q\", FSNode.file)])] := by\n"
            "    rw [implementation_collect]; simp [sortByName, entryIsDir, Id.run, hi]; rfl\n"
            "  unfold problem_spec_collect\n"
            "  rw [himpl, hgold]\n"
            "  simp\n"
        ),
    },
    {
        "id": "reject-level-not-emitted-whole",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_level_incomplete,
        "refinement": "emits only the directory entries of each level, dropping "
                      "every non-directory entry from the output while still "
                      "descending correctly. Its faithful real patch filters the "
                      "level before emitting it, so the collector reports only the "
                      "sub-directories it walks and never the ordinary files inside "
                      "them — no test file anywhere in the tree is reported. The "
                      "F2P assertion counts collected outcomes and would see none; "
                      "essentially the whole P2P collection set fails too, so the "
                      "faithful patch does NOT resolve.",
        "rationale": "REJECT from the LEVEL-COMPLETENESS commitment, which no "
                     "shipped rival attacked: all the others change only the "
                     "descent, so every one of them still emits the level as the "
                     "full name-ordered list, and a spec that pinned the descent "
                     "while leaving the level's own membership free would pass the "
                     "entire rest of this battery. The spec's walk emits every entry "
                     "of a level and then descends; this rival emits a proper subset "
                     "of it. If it verified => SPEC-TOO-WEAK: the spec would "
                     "constrain which subtrees are visited but not which entries are "
                     "actually reported. Refuted at a level of ONE non-directory "
                     "entry — an input at which no descent occurs on either side, so "
                     "the refutation isolates level emission and cannot be inherited "
                     "from any descent clause. This is also a point no other witness "
                     "in the battery visits: every other `entries0` holds at least "
                     "one directory.",
        "witness": (
            "-- Refuted at a level holding a single non-directory entry. Neither\n"
            "-- side descends anywhere here (there is no directory to descend\n"
            "-- into), so the only thing under test is whether the level itself is\n"
            "-- emitted whole: the spec emits the entry, the rival emits nothing.\n"
            "example : ¬ problem_spec_collect (fun _ => true) [(\"f\", FSNode.file)]\n"
            "    (implementation_collect (fun _ => true) [(\"f\", FSNode.file)]) := by\n"
            "  have hgold : collectTree (fun _ => true) [(\"f\", FSNode.file)]"
            " = [(\"f\", FSNode.file)] := by\n"
            "    rw [collectTree, sortByName, List.mergeSort_singleton]; simp\n"
            "  have himpl : implementation_collect (fun _ => true)"
            " [(\"f\", FSNode.file)] = [] := by\n"
            "    rw [implementation_collect]; simp [sortByName, entryIsDir, Id.run]; rfl\n"
            "  unfold problem_spec_collect\n"
            "  rw [himpl, hgold]\n"
            "  simp\n"
        ),
    },
    {
        "id": "reject-level-emitted-twice",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_level_duplicated,
        "refinement": "emits every entry of each level twice. Its faithful real "
                      "patch yields the level a second time before descending, so "
                      "every collected item is reported twice over — the F2P "
                      "assertion pins an exact outcome COUNT and would see double "
                      "it, and every P2P test that counts or lists reported items "
                      "fails the same way, so the faithful patch does NOT resolve.",
        "rationale": "REJECT from the MULTIPLICITY half of the same "
                     "level-completeness commitment, approached from the opposite "
                     "side to the rival above: that one emits too few entries, this "
                     "one too many. The pair matters because a spec can be weak in "
                     "just one direction — a postcondition stated as 'every entry of "
                     "the level appears in the result' would refute the dropping "
                     "rival and ACCEPT this one, and a set- or membership-based "
                     "postcondition would accept both. The frozen spec pins the "
                     "result to a LIST equality, so it must refute both. If it "
                     "verified => SPEC-TOO-WEAK on multiplicity. Refuted at the same "
                     "descent-free single-file level, where duplication is the only "
                     "possible difference.",
        "witness": (
            "-- Refuted at a level holding a single non-directory entry, where no\n"
            "-- descent happens on either side: the spec emits it once, the rival\n"
            "-- twice. The discriminator is multiplicity, not membership — a witness\n"
            "-- that only asked which entries occur would not separate these.\n"
            "example : ¬ problem_spec_collect (fun _ => true) [(\"f\", FSNode.file)]\n"
            "    (implementation_collect (fun _ => true) [(\"f\", FSNode.file)]) := by\n"
            "  have hgold : collectTree (fun _ => true) [(\"f\", FSNode.file)]"
            " = [(\"f\", FSNode.file)] := by\n"
            "    rw [collectTree, sortByName, List.mergeSort_singleton]; simp\n"
            "  have himpl : implementation_collect (fun _ => true) [(\"f\", FSNode.file)]\n"
            "      = [(\"f\", FSNode.file), (\"f\", FSNode.file)] := by\n"
            "    rw [implementation_collect]; simp [sortByName, entryIsDir, Id.run]; rfl\n"
            "  unfold problem_spec_collect\n"
            "  rw [himpl, hgold]\n"
            "  simp\n"
        ),
    },
    {
        "id": "reject-descent-not-transitive",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_depth_limited,
        "refinement": "descends exactly one level and then stops: a selected "
                      "directory's own children are reported, but a directory "
                      "found AMONG those children is never entered. Its faithful "
                      "real patch replaces the recursive call on a subdirectory "
                      "with a single non-recursive listing of it, so collection "
                      "reaches depth two and no further. Anything nested more "
                      "deeply than one directory below the starting point goes "
                      "uncollected — the P2P suite walks package trees several "
                      "levels deep, and the reported set would be truncated on "
                      "every one of them, so the faithful patch does NOT resolve.",
        "rationale": "REJECT from the TRANSITIVITY of the descent, a commitment no "
                     "other rival in this battery can see. The spec's walk is "
                     "defined recursively, so it descends to unbounded depth; this "
                     "rival descends once. Every other witness here is stated at a "
                     "tree whose child levels hold only non-directory entries, and "
                     "at every such input a one-level descent AGREES with the spec "
                     "exactly — so a spec that pinned the first level of descent "
                     "but not its recursion would pass the entire rest of the "
                     "battery. If it verified => SPEC-TOO-WEAK on depth. Binder "
                     "spread: the only witness whose `entries0` is a tree of depth "
                     "THREE (a directory holding a directory holding a file), which "
                     "is the shallowest input at which unbounded descent is "
                     "distinguishable from a bounded one at all. This clause has no "
                     "nagini counterpart: the flattened per-entry carrier has no "
                     "notion of a subtree, let alone of recursion into one.",
        "witness": (
            "-- Refuted at a tree of depth three: a selected plain directory `d`\n"
            "-- holding a selected plain directory `e`, which holds one file `g`.\n"
            "-- Both sides agree on `d` and on `e`; they differ on whether `g` is\n"
            "-- reached, which is exactly whether the descent recurses. Each level\n"
            "-- is discharged innermost-first as a local `have` (neither side is\n"
            "-- `decide`-able), so the two literal lists differ by one entry.\n"
            "example : ¬ problem_spec_collect (fun _ => true)\n"
            "      [(\"d\", FSNode.dir false [(\"e\", FSNode.dir false"
            " [(\"g\", FSNode.file)])])]\n"
            "    (implementation_collect (fun _ => true)\n"
            "      [(\"d\", FSNode.dir false [(\"e\", FSNode.dir false"
            " [(\"g\", FSNode.file)])])]) := by\n"
            # The INNERMOST level is supplied first and is true of BOTH impls (at a
            # level of one non-directory nothing descends either way). Without it
            # the frozen side's `hie` cannot reduce and the gold-side build fails by
            # an UNFOLDING failure instead of by refuting anything — measured, and
            # it is the same defect the first audit repaired on the ordering witness.
            "  have hig : implementation_collect (fun _ => true) [(\"g\", FSNode.file)]"
            " = [(\"g\", FSNode.file)] := by\n"
            "    rw [implementation_collect]; simp [sortByName, entryIsDir, Id.run]; rfl\n"
            "  have hie : implementation_collect (fun _ => true)"
            " [(\"e\", FSNode.dir false [(\"g\", FSNode.file)])]\n"
            "      = [(\"e\", FSNode.dir false [(\"g\", FSNode.file)]),"
            " (\"g\", FSNode.file)] := by\n"
            "    rw [implementation_collect]; simp [sortByName, entryIsDir, Id.run, hig]; rfl\n"
            "  have hcg : collectTree (fun _ => true) [(\"g\", FSNode.file)]"
            " = [(\"g\", FSNode.file)] := by\n"
            "    rw [collectTree, sortByName, List.mergeSort_singleton]; simp\n"
            "  have hce : collectTree (fun _ => true)"
            " [(\"e\", FSNode.dir false [(\"g\", FSNode.file)])]\n"
            "      = [(\"e\", FSNode.dir false [(\"g\", FSNode.file)]),"
            " (\"g\", FSNode.file)] := by\n"
            "    rw [collectTree, sortByName, List.mergeSort_singleton]; simp [hcg]\n"
            "  have hgold : collectTree (fun _ => true)\n"
            "      [(\"d\", FSNode.dir false [(\"e\", FSNode.dir false"
            " [(\"g\", FSNode.file)])])]\n"
            "      = [(\"d\", FSNode.dir false [(\"e\", FSNode.dir false"
            " [(\"g\", FSNode.file)])]),\n"
            "         (\"e\", FSNode.dir false [(\"g\", FSNode.file)]),"
            " (\"g\", FSNode.file)] := by\n"
            "    rw [collectTree, sortByName, List.mergeSort_singleton]; simp [hce]\n"
            "  have himpl : implementation_collect (fun _ => true)\n"
            "      [(\"d\", FSNode.dir false [(\"e\", FSNode.dir false"
            " [(\"g\", FSNode.file)])])]\n"
            "      = [(\"d\", FSNode.dir false [(\"e\", FSNode.dir false"
            " [(\"g\", FSNode.file)])]),\n"
            "         (\"e\", FSNode.dir false [(\"g\", FSNode.file)])] := by\n"
            "    rw [implementation_collect]; simp [sortByName, entryIsDir, Id.run, hie]; rfl\n"
            "  unfold problem_spec_collect\n"
            "  rw [himpl, hgold]\n"
            "  simp\n"
        ),
    },
    {
        "id": "reject-sibling-subtrees-out-of-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_sibling_order,
        "refinement": "reports the descended subtrees in the reverse of their "
                      "parents' order. Its faithful real patch iterates the ordered "
                      "level backwards when recursing, so the level itself is still "
                      "reported in name order and every item still appears exactly "
                      "once, but the blocks of nested items follow in the opposite "
                      "order to the directories they came from. The suite pins the "
                      "reported ORDER of collected items, and the inversion shows on "
                      "any parent holding two walked subdirectories, so the faithful "
                      "patch does NOT resolve.",
        "rationale": "REJECT from the ORDER OF SIBLING SUBTREES against each other "
                     "— a commitment distinct from both orderings already attacked. "
                     "`reject-level-order-not-by-name` pins the order WITHIN a "
                     "level and `reject-subtree-emitted-before-level` pins a level "
                     "against its own subtrees, but neither constrains how two "
                     "subtrees of the SAME level are ordered relative to one "
                     "another; this rival gets both of those right and only that "
                     "wrong. It is invisible to the rest of the battery: the one "
                     "other multi-directory witness "
                     "(`reject-first-entry-never-descended`) is refuted by a "
                     "MISSING subtree, so a rival that emits every subtree exactly "
                     "once in a permuted order defeats it. Both results here are "
                     "permutations of each other with identical multiplicities, so "
                     "a spec pinning membership, counts, or per-level order alone "
                     "would accept this rival. If it verified => SPEC-TOO-WEAK on "
                     "the walk's sibling order.",
        "witness": (
            "-- Refuted at a two-entry level of two selected plain directories given\n"
            "-- in name order, each holding one file. Both sides emit the level\n"
            "-- correctly and emit both children exactly once: the ONLY difference is\n"
            "-- that the spec appends `a`'s subtree before `b`'s and the rival\n"
            "-- reverses them. The per-level ordering is reduced to the `List Char`\n"
            "-- comparison that IS decidable, then both walks are evaluated by hand.\n"
            "example : ¬ problem_spec_collect (fun _ => true)\n"
            "      [(\"a\", FSNode.dir false [(\"x\", FSNode.file)]),"
            " (\"b\", FSNode.dir false [(\"y\", FSNode.file)])]\n"
            "    (implementation_collect (fun _ => true)\n"
            "      [(\"a\", FSNode.dir false [(\"x\", FSNode.file)]),"
            " (\"b\", FSNode.dir false [(\"y\", FSNode.file)])]) := by\n"
            "  have hix : implementation_collect (fun _ => true) [(\"x\", FSNode.file)]"
            " = [(\"x\", FSNode.file)] := by\n"
            "    rw [implementation_collect]; simp [sortByName, entryIsDir, Id.run]; rfl\n"
            "  have hiy : implementation_collect (fun _ => true) [(\"y\", FSNode.file)]"
            " = [(\"y\", FSNode.file)] := by\n"
            "    rw [implementation_collect]; simp [sortByName, entryIsDir, Id.run]; rfl\n"
            "  have hcx : collectTree (fun _ => true) [(\"x\", FSNode.file)]"
            " = [(\"x\", FSNode.file)] := by\n"
            "    rw [collectTree, sortByName, List.mergeSort_singleton]; simp\n"
            "  have hcy : collectTree (fun _ => true) [(\"y\", FSNode.file)]"
            " = [(\"y\", FSNode.file)] := by\n"
            "    rw [collectTree, sortByName, List.mergeSort_singleton]; simp\n"
            "  have hsort : sortByName [(\"a\", FSNode.dir false [(\"x\", FSNode.file)]),"
            " (\"b\", FSNode.dir false [(\"y\", FSNode.file)])]\n"
            "      = [(\"a\", FSNode.dir false [(\"x\", FSNode.file)]),"
            " (\"b\", FSNode.dir false [(\"y\", FSNode.file)])] := by\n"
            "    simp [sortByName, List.mergeSort, List.merge]\n"
            "    decide\n"
            "  have hgold : collectTree (fun _ => true)\n"
            "      [(\"a\", FSNode.dir false [(\"x\", FSNode.file)]),"
            " (\"b\", FSNode.dir false [(\"y\", FSNode.file)])]\n"
            "      = [(\"a\", FSNode.dir false [(\"x\", FSNode.file)]),"
            " (\"b\", FSNode.dir false [(\"y\", FSNode.file)]),\n"
            "         (\"x\", FSNode.file), (\"y\", FSNode.file)] := by\n"
            "    rw [collectTree, hsort]; simp [hcx, hcy]\n"
            "  have himpl : implementation_collect (fun _ => true)\n"
            "      [(\"a\", FSNode.dir false [(\"x\", FSNode.file)]),"
            " (\"b\", FSNode.dir false [(\"y\", FSNode.file)])]\n"
            "      = [(\"a\", FSNode.dir false [(\"x\", FSNode.file)]),"
            " (\"b\", FSNode.dir false [(\"y\", FSNode.file)]),\n"
            "         (\"y\", FSNode.file), (\"x\", FSNode.file)] := by\n"
            "    rw [implementation_collect, hsort]; simp [entryIsDir, Id.run, hix, hiy]; rfl\n"
            "  unfold problem_spec_collect\n"
            "  rw [himpl, hgold]\n"
            "  simp\n"
        ),
    },
]

# No AXIOM lane: the bundle declares no `opaque` callee and consumes no `axiom`
# (the walk, the per-level ordering and the classification are all modeled
# deeply; the selection predicate is a universally quantified function parameter).
# The nagini AXIOM_TESTS was also empty; dropped either way, since the axiom lane
# belongs to G-AX and this gate ignores it.
AXIOM_TESTS = []
