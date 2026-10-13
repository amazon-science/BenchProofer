# properties.py — G-PBT falsification battery for pytest-dev__pytest-10356 (lean).
#
# NOT a Lean file; a record of adversarial cases the G-PBT gate executes and
# stamps. Each SPEC_TESTS case is a full `Solution.lean` variant that shares the
# FROZEN spec byte-for-byte: `_swap` only ever rewrites text lying inside the
# `-- impl-start` / `-- impl-end` region or (for a case that legitimately
# re-proves) inside `-- proof-start` / `-- proof-end`. So `markers.same_spec`
# holds by construction, the single `theorem correct_inheritedMarks` STATEMENT
# stays byte-identical, and any rejection is attributable to the postcondition
# rather than to a tampered spec.
#
# PORT NOTE. This is a PORT of the nagini falsification battery
# (`../nagini/properties.py`) onto this backend's carrier, not a translation of
# its text. The nagini sibling contracts the behavior over an immutable sequence
# of sequences with an explicit length precondition and a front-recursive `@Pure`
# fold as its oracle; this bundle models the same behavior as one total Lean
# function over `(hierarchy : List ClassMarks) (wholeHierarchy : Bool)` with NO
# precondition at all. Every nagini case's ARGUMENT carries over; its mechanics
# are re-expressed against this carrier. The per-case correspondence, and every
# principled omission, is in the `assessment` submitted with this battery.
#
# ---------------------------------------------------------------------------
# DEFENDED SURFACE (one obligation, `correct_inheritedMarks`)
# ---------------------------------------------------------------------------
# The postcondition is a single equality whose right-hand side branches on the
# mode selector, giving three independent things to attack:
#
#   (F) FULL-MODE arm — when `wholeHierarchy` is true the result is
#       `hierarchy.flatMap flattenClassMarks`: EVERY class in the chain
#       contributes, in resolution order, with duplicates kept. This is the
#       load-bearing clause: it is what distinguishes gathering the whole chain
#       from reading one resolved entry, and it pins order, multiplicity and
#       completeness simultaneously.
#   (R) RESTRICTED-MODE arm — when `wholeHierarchy` is false the result is
#       exactly `flattenClassMarks (hierarchy.headD (ClassMarks.many []))`: the
#       head entry's labels and nothing else.
#   (C) the per-entry CONTRIBUTION `flattenClassMarks`, shared by both arms: a
#       stored list passes through verbatim, a single bare stored label becomes a
#       one-element list. An entry stored in bare form contributes its label just
#       as a list-stored one does.
#
# The right-hand side is GROUNDED — a fold of the input `hierarchy` spelled out
# in the spec view, with no opaque callee anywhere in the bundle. So there is no
# answer-key for a rival to echo: an impl satisfies the equality only when the
# list it returns provably IS that fold. That is also why the cheapest honest
# impl (return the fold directly, `pure-branch-on-mode` below) is a POSITIVE
# control rather than a weak-echo rival.
#
# ---------------------------------------------------------------------------
# WHY EVERY REJECT CASE CARRIES A WITNESS
# ---------------------------------------------------------------------------
# On this backend "did not verify" does NOT mean "the spec refutes it". The
# frozen proof script is tuned to the frozen impl's syntactic form (it rewrites
# with `loop_helper`, whose statement mentions the frozen loop body verbatim), so
# reshaping the impl AT ALL breaks the script — a merely commuted-but-correct
# impl fails exactly as loudly as a wrong one. Every `expect="reject"` case
# therefore ships a `witness`: an `example` proving the rival CONTRADICTS the
# spec at one concrete input. Each was built both ways before shipping and SEEN
# to discriminate — it elaborates against the rival and FAILS against the frozen
# solution, and that gold-side failure was read to confirm it is a SEMANTIC
# refutation (`decide` reducing the claim to `False`) rather than an unknown
# identifier, a type error or a stuck reduction, which would discriminate
# nothing. The carrier is fully transparent (`Mark` derives `DecidableEq`,
# `ClassMarks` is a two-constructor inductive, both arms are computable), so
# every witness closes by `decide` at literal inputs; none needs to condition on
# a hypothesis, so none can be `witness-inconsistent`.
#
# BINDER / POINT COVERAGE. Two input binders, both moved by the reject
# witnesses. `wholeHierarchy` is probed at BOTH values (true by nine rivals,
# false by three) rather than held at its default. The twelve reject witnesses sit
# at twelve DISTINCT (`hierarchy`, `wholeHierarchy`) points, drawn from ten
# distinct `hierarchy` values — a three-class chain, a three-class chain mixing a
# bare-stored entry into a list-stored one, three different two-class chains, a
# lone class, a single bare-stored entry, a repeated-label pair, a single label
# carrying two arguments, and the empty chain. Two of those ten are each used
# twice, at OPPOSITE mode values, which is what pins the two arms against each
# other rather than a borrowed input. Chain lengths 0, 1, 2 and 3 all appear,
# which matters because several arms coincide on the short chains.
#
# ADMISSIBILITY. The battery also carries a `kind="admissibility"` positive. The
# frozen obligation has no precondition, but that is not what would make the lane
# vacuous on a total carrier: the analogue of PRECOND-TOO-STRONG is the obligation
# being UNSATISFIABLE at a behavior-shaped input, which the case probes by
# discharging the post image at that concrete input by evaluation — with a
# negative control showing the evaluation discriminates — before closing the
# frozen obligation verbatim. See the case for the full argument.
from pathlib import Path

INSTANCE = "pytest-dev__pytest-10356"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen anchors. Each lies ENTIRELY inside the impl region (or, for the two
# proof anchors, inside the proof region) and is unique in the file, so the
# manifest breaks loudly if the frozen solution ever drifts.
# ---------------------------------------------------------------------------

# the mode selection: which entries of the chain are gathered at all.
_SELECT = """  let markLists := if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]
                   else hierarchy"""

# the bare-stored-entry arm of the per-entry contribution.
_ONE_ARM = "    | .one m   => markList := markList ++ [m]"

# the returned accumulator.
_RETURN = "  return markList"

# the whole implementation definition (used by the positives that reshape it).
_IMPL = """def implementation_inheritedMarks (hierarchy : List ClassMarks) (wholeHierarchy : Bool) :
    List Mark := Id.run do
  -- restricted mode: only the class's own stored entry; full mode: every class
  -- in the resolution chain.
  let markLists := if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]
                   else hierarchy
  let mut markList : List Mark := []
  for item in markLists do
    match item with
    | .many xs => markList := markList ++ xs
    | .one m   => markList := markList ++ [m]
  return markList"""

# the frozen tactic body of `correct_inheritedMarks` (the STATEMENT above it is
# never touched; only this body may differ, and only when a case re-proves).
_PROOF = """  intro hierarchy wholeHierarchy
  unfold problem_spec_inheritedMarks implementation_inheritedMarks
  rw [loop_helper]
  simp only [List.nil_append]
  cases wholeHierarchy with
  | true => simp
  | false =>
    simp only [Bool.not_false, if_true]
    cases h2 : hierarchy.headD (ClassMarks.many []) with
    | many xs => simp [flattenClassMarks]
    | one m => simp [flattenClassMarks]"""

for _a in (_SELECT, _ONE_ARM, _RETURN, _IMPL, _PROOF):
    assert _BASE.count(_a) == 1, _a[:60]

# The frozen `theorem correct_inheritedMarks` STATEMENT, verbatim, so a case that
# prepends steps to the tactic body re-emits the statement byte-for-byte instead
# of retyping it.
_THM_STMT = """theorem correct_inheritedMarks :
    ∀ (hierarchy : List ClassMarks) (wholeHierarchy : Bool),
      problem_spec_inheritedMarks hierarchy wholeHierarchy
        (implementation_inheritedMarks hierarchy wholeHierarchy) := by"""
assert _BASE.count(_THM_STMT) == 1


def _select(new):
    """Rewrite ONLY the mode-selection line pair inside the impl region."""
    return _swap(_BASE, _SELECT, "  let markLists := " + new)


# ---------------------------------------------------------------------------
# Witness helper. Every witness states the spec predicate directly at a
# concrete, fully decidable input and asserts the rival's output violates it.
# ---------------------------------------------------------------------------

def _witness(hierarchy, mode):
    return (
        "example : ¬ problem_spec_inheritedMarks\n"
        f"    {hierarchy} {mode}\n"
        "    (implementation_inheritedMarks\n"
        f"      {hierarchy} {mode}) := by\n"
        "  unfold problem_spec_inheritedMarks implementation_inheritedMarks\n"
        "  decide"
    )


# ===========================================================================
# UNIQUENESS (expect="reject") — rivals sharing the frozen spec exactly. A
# verifying rival here is a real verify-does-not-imply-resolve break
# (SPEC-TOO-WEAK).
# ===========================================================================

# (F) THE DEFECT ITSELF: gather only the head entry, in BOTH modes — i.e. one
# resolved entry stands in for the whole chain. Every ancestor's labels vanish.
_R_HEAD_ONLY = _swap(
    _BASE, _SELECT,
    "  let _ := wholeHierarchy\n"
    "  let markLists := [hierarchy.headD (ClassMarks.many [])]",
)

# (F) partial-domain: gather every ancestor but SKIP the class's own entry.
# Correct on the chain's tail, wrong on its head.
_R_SKIP_OWN = _select(
    "if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]\n"
    "                   else hierarchy.drop 1")

# (F) partial-domain, mirror image: gather every entry but the LAST, so the
# deepest class in the chain never contributes. Correct on the prefix.
_R_SKIP_DEEPEST = _select(
    "if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]\n"
    "                   else hierarchy.dropLast")

# (F) partial-domain in the chain's INTERIOR: gather the class's own entry and
# everything from the second ancestor on, skipping exactly the first ancestor.
# Both endpoints of the chain are correct — which is what the other two
# partial-domain rivals cut at — so only a chain of at least three classes, read
# at an interior position, refutes it.
_R_SKIP_INTERMEDIATE = _select(
    "if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]\n"
    "                   else hierarchy.take 1 ++ hierarchy.drop 2")

# (F) ORDERING attack: the same labels, in the wrong order — the ancestors'
# contributions first and the class's own appended last. Same multiset, so this
# defeats any membership/multiset proxy; only ORDERED equality refutes it.
_R_OWN_LAST = _select(
    "if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]\n"
    "                   else hierarchy.drop 1 ++ "
    "[hierarchy.headD (ClassMarks.many [])]")

# (F) partial-domain on the SMALLEST admissible chain: correct whenever the
# chain has more than one class, but a lone class yields nothing at all.
_R_LONE_EMPTY = _select(
    "if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]\n"
    "                   else if hierarchy.length ≤ 1 then [] else hierarchy")

# (F) MULTIPLICITY attack: collapse entries carrying the same label name, so
# only ONE contribution per name survives. Completeness-of-names is intact; only
# the duplicates-are-kept content of the equality refutes it. (`pwFilter` with
# this relation keeps the LAST contribution per name, not the first — checked at
# the witness point rather than assumed, since the direction is easy to get
# backwards and the rationale below states it.)
_R_COLLAPSE_NAMES = _swap(
    _BASE, _RETURN,
    "  return markList.pwFilter (fun x y => x.name ≠ y.name)")

# (C) the per-entry CONTRIBUTION: an entry stored in bare form contributes
# nothing instead of its one label. Both arms of the equality route through
# this, and both mode values expose it.
_R_BARE_DROPPED = _swap(
    _BASE, _ONE_ARM, "    | .one _   => markList := markList ++ []")

# (F)+(R) CONTROL-FLOW: the two modes are wired backwards. Refuted by either
# arm; the witness picks the restricted arm so this case moves the mode binder.
_R_MODES_SWAPPED = _select(
    "if !wholeHierarchy then hierarchy\n"
    "                   else [hierarchy.headD (ClassMarks.many [])]")

# (R) the restricted arm alone: it reaches one class too far up the chain.
# Indistinguishable from gold in full mode and on a lone class — a near-miss
# refuted only in restricted mode on a chain of at least two classes.
_R_RESTRICTED_OVERREACH = _select(
    "if !wholeHierarchy then hierarchy.take 2\n"
    "                   else hierarchy")

# (R) the DEFAULT the restricted arm falls back on when the chain is empty. Every
# other rival attacks which entries are gathered or what an entry contributes;
# none touches the fallback itself, which the spec pins to the empty contribution.
# This rival substitutes a bare-label default, so it agrees with gold on every
# NON-empty chain in both modes and diverges only at the empty chain.
_R_EMPTY_DEFAULT = _select(
    "if !wholeHierarchy then [hierarchy.headD (ClassMarks.one ⟨\"\", []⟩)]\n"
    "                   else hierarchy")

# (C) WITHIN a label rather than within the chain: every gathered label keeps its
# name and position, but its positional arguments come back reversed. All the
# other rivals move whole entries or whole labels around, so none of them
# observes the `args` component's own order — which the carrier's `Mark` equality
# does observe, and which mapping.md declares part of the observable.
_R_ARGS_REVERSED = _swap(
    _BASE, _RETURN,
    "  return markList.map (fun m => ⟨m.name, m.args.reverse⟩)")


# ===========================================================================
# SOUNDNESS (expect="verify") — structurally DIFFERENT but CORRECT impls that
# MUST verify (else SPEC-TOO-STRONG). On this backend each needs a proof that
# actually closes for the NEW impl shape; the `theorem correct_inheritedMarks`
# STATEMENT is byte-identical in every one, only the tactic body is re-authored,
# and none reaches for `sorry`/`admit`/`native_decide`, a new axiom or a new
# lemma. All three were built and confirmed to close.
# ===========================================================================

# The cheapest honest impl: drop the imperative scaffold entirely and branch on
# the mode with a pattern match, returning the fold directly. The right-hand
# side is grounded in the input, so this genuinely does the work. `loop_helper`
# is left verbatim (unused) so the frozen lemma set is unchanged.
_POS_PURE = _swap(
    _swap(_BASE, _IMPL,
          """def implementation_inheritedMarks (hierarchy : List ClassMarks) (wholeHierarchy : Bool) :
    List Mark :=
  -- full mode: every class in the resolution chain contributes; restricted
  -- mode: only the class's own stored entry.
  match wholeHierarchy with
  | true  => hierarchy.flatMap flattenClassMarks
  | false => flattenClassMarks (hierarchy.headD (ClassMarks.many []))"""),
    _PROOF,
    """  intro hierarchy wholeHierarchy
  unfold problem_spec_inheritedMarks implementation_inheritedMarks
  cases wholeHierarchy with
  | true => simp
  | false => simp""")

# Keep the gold accumulator loop verbatim and flip only the POLARITY of the
# mode test (positive test, branches exchanged) — behaviourally identical,
# syntactically different enough that the frozen `simp only [Bool.not_false,
# if_true]` step no longer applies and the branch collapse must be re-derived.
_POS_POLARITY = _swap(
    _swap(_BASE, _IMPL,
          _swap(_IMPL, _SELECT,
                "  let markLists := if wholeHierarchy then hierarchy\n"
                "                   else [hierarchy.headD (ClassMarks.many [])]")),
    _PROOF,
    """  intro hierarchy wholeHierarchy
  unfold problem_spec_inheritedMarks implementation_inheritedMarks
  rw [loop_helper]
  simp only [List.nil_append]
  cases wholeHierarchy with
  | true => simp
  | false =>
    simp only [if_false, Bool.false_eq_true]
    cases h2 : hierarchy.headD (ClassMarks.many []) with
    | many xs => simp [flattenClassMarks]
    | one m => simp [flattenClassMarks]""")

# Replace the imperative loop with a left fold over the selected entries,
# accumulating each entry's contribution through the shared per-entry helper
# instead of re-matching the two stored forms inline. `loop_helper` is re-stated
# for the fold shape — same lemma NAME, same role (the accumulator
# generalization), so the frozen lemma set is unchanged; only its body and
# statement shape follow the new impl. The obligation statement is untouched.
_POS_FOLD = _swap(
    _swap(_BASE, _IMPL,
          """def implementation_inheritedMarks (hierarchy : List ClassMarks) (wholeHierarchy : Bool) :
    List Mark :=
  -- restricted mode: only the class's own stored entry; full mode: every class
  -- in the resolution chain.
  let markLists := if !wholeHierarchy then [hierarchy.headD (ClassMarks.many [])]
                   else hierarchy
  markLists.foldl (fun acc item => acc ++ flattenClassMarks item) []"""),
    _BASE[_BASE.index("theorem loop_helper"):_BASE.index("-- proof-end")].rstrip(),
    """theorem loop_helper :
    ∀ (markLists : List ClassMarks) (init : List Mark),
      markLists.foldl (fun acc item => acc ++ flattenClassMarks item) init =
        init ++ markLists.flatMap flattenClassMarks := by
  intro markLists
  induction markLists with
  | nil => intro init; simp
  | cons a as ih =>
    intro init
    simp only [List.foldl_cons, ih, List.flatMap_cons, List.append_assoc]

theorem correct_inheritedMarks :
    ∀ (hierarchy : List ClassMarks) (wholeHierarchy : Bool),
      problem_spec_inheritedMarks hierarchy wholeHierarchy
        (implementation_inheritedMarks hierarchy wholeHierarchy) := by
  intro hierarchy wholeHierarchy
  unfold problem_spec_inheritedMarks implementation_inheritedMarks
  simp only [loop_helper, List.nil_append]
  cases wholeHierarchy with
  | true => simp
  | false => simp""")


# ===========================================================================
# ADMISSIBILITY (expect="verify") — the obligation is SATISFIABLE, and
# DISCRIMINATING, at the shape the modeled behavior exists for.
# ===========================================================================
# The frozen obligation is `∀ (hierarchy : List ClassMarks) (wholeHierarchy :
# Bool)` with no hypothesis arrow, so there is no precondition that could be too
# strong. On a TOTAL carrier that is not what makes this lane vacuous, and
# "there is no precondition" is the wrong test: the analogue of
# PRECOND-TOO-STRONG here is the obligation being UNSATISFIABLE at exactly a
# behavior-shaped input, which a case can probe directly by discharging the post
# image AT that concrete input, by evaluation, before closing the frozen
# obligation verbatim.
#
# The input is the shape the modeled behavior is pinned at: a four-entry chain
# whose first three entries each carry one label sharing a single NAME and
# differing only in arguments (so a name-collapsing or args-blind reading is
# visible here), and whose last entry contributes nothing. Both modes are
# discharged.
#
# The third `have` is what makes this a probe rather than a restatement: it
# evaluates the post image to FALSE at the output a single-entry gathering would
# produce at that same input. So the two positive `have`s are real evaluations of
# the postcondition, not steps that would close for any output at all — the
# obligation is satisfiable AND it discriminates there. If any of the three
# failed, the obligation would be unsatisfiable, or indifferent, at the one input
# the behavior exists for.
#
# Scope: the impl region is the FROZEN impl, untouched; `loop_helper` and the
# `theorem correct_inheritedMarks` STATEMENT are re-emitted byte-for-byte, the
# frozen tactic body follows the `have`s verbatim, and the `have`s are `clear`ed
# so they cannot participate in it. No new declaration, no new axiom, no `sorry`.
_ADM_INPUT = ('[ClassMarks.many [⟨"t", ["1"]⟩], ClassMarks.many [⟨"t", ["2"]⟩], '
              'ClassMarks.many [⟨"t", ["3"]⟩], ClassMarks.many []]')

_ADM_HAVES = f"""  -- Positive halves: the post image is satisfiable at that input, in BOTH modes.
  have adm_full : problem_spec_inheritedMarks
      {_ADM_INPUT} true
      (implementation_inheritedMarks
        {_ADM_INPUT} true) := by
    unfold problem_spec_inheritedMarks implementation_inheritedMarks
    decide
  have adm_restricted : problem_spec_inheritedMarks
      {_ADM_INPUT} false
      (implementation_inheritedMarks
        {_ADM_INPUT} false) := by
    unfold problem_spec_inheritedMarks implementation_inheritedMarks
    decide
  -- Informativeness control: at that same input the obligation evaluates to
  -- FALSE for the output a single-entry gathering would give, so the two halves
  -- above are genuine evaluations rather than steps that close for any output.
  have adm_discriminates : ¬ problem_spec_inheritedMarks
      {_ADM_INPUT} true
      [⟨"t", ["1"]⟩] := by
    unfold problem_spec_inheritedMarks
    decide
  clear adm_full adm_restricted adm_discriminates
"""

# The frozen tactic body must survive VERBATIM after the probes, so the
# obligation is reproven and not replaced. Asserted so a Solution.lean edit fails
# loudly instead of silently shipping an admissibility case closed some other way.
assert _PROOF in _BASE
_ADMISS = _swap(_BASE, _THM_STMT + "\n" + _PROOF,
                _THM_STMT + "\n" + _ADM_HAVES + _PROOF)
assert _PROOF in _ADMISS


SPEC_TESTS = [
    # ---- uniqueness (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "gather-head-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_HEAD_ONLY,
        "rationale": (
            "REJECT from the full-mode arm (F). The spec pins the result to "
            "`hierarchy.flatMap flattenClassMarks` — every class in the chain "
            "contributes — while this rival gathers only the head entry no "
            "matter what mode is selected. Refuted at a three-class chain in "
            "full mode: the spec's fold has all three labels, the rival returns "
            "one. This is the deepest attack in the battery, since the same "
            "input that refutes it is the one the modeled behavior exists for."
        ),
        "refinement": (
            "This IS the pre-fix behavior, and it is what `Solution_prepatch.lean` "
            "reproduces: the gathering consults a single resolved stored entry "
            "rather than each class's own entry along the whole chain, so a class "
            "descending from two independently labelled parents keeps only one "
            "source's labels. The sole F2P test builds exactly that shape — a "
            "class with two labelled parents, all three labelled — and asserts "
            "the gathered list is all three labels in resolution order; with "
            "head-only gathering it is a single label and the assertion fails. "
            "The faithful real patch is the UN-fixed single-resolved-entry read, "
            "which is by definition what does not resolve."
        ),
        "witness": _witness(
            '[ClassMarks.many [⟨"u", []⟩], ClassMarks.many [⟨"v", []⟩], '
            'ClassMarks.many [⟨"w", []⟩]]', "true"),
    },
    {
        "id": "gather-skips-own-entry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_SKIP_OWN,
        "rationale": (
            "REJECT from the full-mode arm (F), partial-domain: the rival "
            "gathers the chain's TAIL, so it agrees with the spec on every "
            "ancestor's contribution and in resolution order, but omits the "
            "class's own labels. Refuted at a two-class chain in full mode — a "
            "point distinct from every other rival's — where the spec's fold "
            "leads with the head entry's label and the rival's does not."
        ),
        "refinement": (
            "A faithful real patch that walked the resolution chain from the "
            "first ANCESTOR onward (skipping the class itself) would drop every "
            "directly-applied label. On the F2P shape the gathered list would be "
            "the two parents' labels and would omit the class's own, so the "
            "asserted three-label list mismatches at its leading position and "
            "the patch would NOT resolve. It would also silently break the "
            "accumulation path that records a newly applied label, since that "
            "path reads back the labels stored directly on the class."
        ),
        "witness": _witness(
            '[ClassMarks.many [⟨"u", []⟩], ClassMarks.many [⟨"v", []⟩]]',
            "true"),
    },
    {
        "id": "gather-skips-deepest",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_SKIP_DEEPEST,
        "rationale": (
            "REJECT from the full-mode arm (F), the mirror-image partial domain: "
            "the rival gathers a strict PREFIX of the chain, agreeing with the "
            "spec on the class's own labels and every intermediate ancestor but "
            "never letting the deepest class contribute. Refuted at its own "
            "two-class point in full mode (distinct from the skip-own rival's, "
            "so the two sub-domains are demonstrated separately rather than "
            "sharing an input)."
        ),
        "refinement": (
            "A faithful real patch that stopped one class short of the end of "
            "the resolution chain would lose the deepest entry's labels. Note "
            "the F2P shape does NOT expose this: there the deepest entry in "
            "resolution order is the unlabelled root every class descends from, "
            "so dropping it changes nothing and the F2P assertion still holds. "
            "What it breaks is the P2P suite, where a labelled base class is "
            "itself the last labelled entry of a subclass's chain and its label "
            "is asserted to reach the subclass's tests — a base whose label "
            "would silently vanish. The witness therefore refutes it on the "
            "carrier at a chain whose deepest entry does carry a label, which "
            "is the general shape rather than the F2P one; recorded that way "
            "because a refinement claiming the F2P input would be false."
        ),
        "witness": _witness(
            '[ClassMarks.many [⟨"u", []⟩], ClassMarks.many [⟨"w", []⟩]]',
            "true"),
    },
    {
        "id": "gather-skips-intermediate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_SKIP_INTERMEDIATE,
        "rationale": (
            "REJECT from the full-mode arm (F) in the chain's INTERIOR. The two "
            "other partial-domain rivals each cut at an ENDPOINT (the head, the "
            "deepest), so both are refuted by a two-class chain and neither "
            "tests that an entry strictly between the ends contributes at all. "
            "This rival keeps both endpoints and drops exactly the first "
            "ancestor, so it agrees with the spec on every two-class chain and "
            "on both endpoints of every longer one; only the `flatMap` covering "
            "the WHOLE chain refutes it. Refuted at its own three-class point in "
            "full mode, whose middle entry is stored in bare form — so it is "
            "also the only witness in the battery that mixes both stored forms "
            "in one chain, exercising clause (C) inside clause (F) rather than "
            "in isolation."
        ),
        "refinement": (
            "A faithful real patch that walked the resolution chain but skipped "
            "one intermediate class — the classic off-by-one in an index-stepped "
            "walk, or a filter that excluded a level it should not — would lose "
            "that level's labels while leaving both ends of the chain intact. "
            "This is the sub-domain most likely to survive the F2P test by "
            "accident: on the F2P shape the two labelled parents sit adjacent, "
            "so whether a given walk drops one of them depends on which index it "
            "misses. It does not resolve on the P2P behaviors that stack three "
            "levels of labelled classes and assert the middle level's label "
            "reaches the leaf's tests, where the skipped level's label simply "
            "disappears."
        ),
        "witness": _witness(
            '[ClassMarks.many [⟨"u", []⟩], ClassMarks.one ⟨"m", []⟩, '
            'ClassMarks.many [⟨"w", []⟩]]', "true"),
    },
    {
        "id": "own-entry-gathered-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_OWN_LAST,
        "rationale": (
            "REJECT from the ORDER content of the full-mode arm (F). The rival "
            "returns exactly the same labels with the same multiplicities — "
            "ancestors first, the class's own contribution appended last — so "
            "nothing about completeness or count refutes it; only the fact that "
            "the spec's fold is `flatMap` over the chain IN RESOLUTION ORDER "
            "does. Refuted at a two-class chain in full mode at its own point, "
            "which pins the spec's dependence on order alone and defeats any "
            "membership- or multiset-based reading of the equality."
        ),
        "refinement": (
            "A faithful real patch that appended the class's own labels after "
            "the inherited ones (rather than leading with them) would produce "
            "the right labels in the wrong order. The F2P test asserts an "
            "ordered list equality whose FIRST element is the class's own label, "
            "so the reordered list compares unequal even though every label is "
            "present, and the patch would NOT resolve. Ordering is also "
            "observable to the label-precedence behaviors the P2P suite pins, "
            "where the closest declaration is expected to come first."
        ),
        "witness": _witness(
            '[ClassMarks.many [⟨"p", []⟩], ClassMarks.many [⟨"q", []⟩]]',
            "true"),
    },
    {
        "id": "lone-class-yields-nothing",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_LONE_EMPTY,
        "rationale": (
            "REJECT from the full-mode arm (F) on the SMALLEST admissible input. "
            "The rival is correct for every chain of more than one class and "
            "returns nothing for a chain of exactly one, where the spec's fold "
            "is that lone class's own contribution. There is no precondition to "
            "exclude this input — the obligation is universally quantified over "
            "`hierarchy` — so the length-1 chain is a fully legitimate point, "
            "and it is the only witness in the battery at chain length 1."
        ),
        "refinement": (
            "A faithful real patch that short-circuited a length-1 resolution "
            "chain to the empty list would report NO labels for it. Recorded "
            "honestly: on the real carrier a CLASS's chain always has at least "
            "two entries (the class itself and the root every class descends "
            "from), so no class input reaches this rival's wrong branch and it "
            "is not a refinement of a resolve-breaking patch. Its value is "
            "purely spec-level, and that is why it is kept: the modeled "
            "obligation is universally quantified over `hierarchy` with NO "
            "precondition excluding the length-1 chain, so the spec is claimed "
            "to hold there and something must attack it. The near-miss it pins "
            "— correct on every longer chain, wrong on the smallest admissible "
            "one — is exactly the shape a length-guard would take, and it is "
            "the only witness in the battery at chain length 1."
        ),
        "witness": _witness('[ClassMarks.many [⟨"u", []⟩]]', "true"),
    },
    {
        "id": "repeated-names-collapsed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_COLLAPSE_NAMES,
        "rationale": (
            "REJECT from the MULTIPLICITY content of the full-mode arm (F): the "
            "rival keeps only ONE contribution per label NAME (the last one, "
            "under this relation). No name is lost, so only the fact that the "
            "spec's fold is a plain concatenation — duplicates kept — refutes "
            "it. Refuted at a two-class chain whose two entries share a label "
            "name but differ in their arguments, an input point no other rival "
            "uses and the only one exercising the `args` component of the "
            "carrier."
        ),
        "refinement": (
            "Collapsing repeated label names is a plausible-looking reading of "
            "the public report this instance comes from, which explicitly floats "
            "de-duplicating by label name as an option — so a faithful real "
            "patch could well have done it. It does not resolve: the F2P "
            "test's three labels ALL share a single name and differ only in "
            "their arguments, so name-collapsing gathering returns one label "
            "where three are asserted. It would also break the P2P behavior "
            "where the same label is applied at two levels with different "
            "arguments and both are expected to survive."
        ),
        "witness": _witness(
            '[ClassMarks.many [⟨"d", []⟩], ClassMarks.many [⟨"d", ["2"]⟩]]',
            "true"),
    },
    {
        "id": "bare-entry-contributes-nothing",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_BARE_DROPPED,
        "rationale": (
            "REJECT from the per-entry CONTRIBUTION clause (C). The spec routes "
            "every gathered entry through `flattenClassMarks`, under which an "
            "entry stored as a single bare label contributes that one label; the "
            "rival makes it contribute nothing. Both arms of the equality read "
            "through this clause, so it is genuinely independent of the mode "
            "selection. Refuted at the only witness point in the battery whose "
            "entry uses the bare-stored constructor rather than the list one — "
            "the sole rival exercising that half of the carrier."
        ),
        "refinement": (
            "A faithful real patch that only ever extended the gathered list "
            "with list-stored entries — and silently ignored an entry stored as "
            "a single bare label instead of appending it — would lose the labels "
            "of every class that stores its label in bare form. That form is "
            "explicitly supported and is exercised by the P2P suite (a class "
            "assigning a single label to the attribute directly rather than as a "
            "one-element list), whose tests assert the label reaches the class's "
            "tests. It would NOT resolve."
        ),
        "witness": _witness('[ClassMarks.one ⟨"z", []⟩]', "true"),
    },
    {
        "id": "modes-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_MODES_SWAPPED,
        "rationale": (
            "REJECT from BOTH arms — a control-flow attack rather than a value "
            "one: the mode selector is wired backwards, so full mode returns the "
            "head entry only and restricted mode returns the whole chain's fold. "
            "This is caught only because each arm is pinned separately; a spec "
            "constraining just one of them would admit it. The witness refutes "
            "it in RESTRICTED mode (`wholeHierarchy = false`), which also moves "
            "the mode binder off the value seven other rivals hold it at."
        ),
        "refinement": (
            "A faithful real patch that routed the mode flag backwards would "
            "invert both behaviors at once. In the default whole-chain mode the "
            "F2P test would see only the class's own label instead of all three "
            "(its first assertion fails), and in restricted mode it would see "
            "all three instead of the one it asserts (its second assertion "
            "fails). Worse, the accumulation path that records a newly applied "
            "label deliberately asks for the restricted reading; under this "
            "rival it would gather the entire chain each time and re-record "
            "every inherited label, duplicating labels on each application and "
            "breaking the P2P precedence and no-propagation-to-base behaviors. "
            "It would NOT resolve."
        ),
        "witness": _witness(
            '[ClassMarks.many [⟨"u", []⟩], ClassMarks.many [⟨"v", []⟩]]',
            "false"),
    },
    {
        "id": "restricted-mode-overreaches",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_RESTRICTED_OVERREACH,
        "rationale": (
            "REJECT from the restricted-mode arm (R) alone, and the tightest "
            "near-miss here: the rival is byte-for-byte gold in full mode and "
            "agrees with gold in restricted mode on any chain of a single class, "
            "diverging only by reaching ONE class too far up the chain. The spec "
            "pins the restricted result to the head entry's contribution and "
            "nothing else. Refuted in restricted mode at a three-class chain — "
            "its own point, and the only place its narrower sub-domain shows — "
            "which is why it does not share the mode-swap rival's witness."
        ),
        "refinement": (
            "A faithful real patch whose restricted reading included the "
            "immediate parent as well as the class itself would over-report by "
            "exactly one level. The F2P test asserts the restricted reading of a "
            "class with two labelled parents is precisely its own single label; "
            "this returns that label plus the first parent's and the assertion "
            "fails. It also corrupts the accumulation path, which uses the "
            "restricted reading specifically so that re-recording a class's "
            "labels does not absorb inherited ones: under this rival each "
            "application would copy the parent's labels onto the child, which is "
            "the P2P behavior asserting a label does not propagate in that "
            "direction. It would NOT resolve."
        ),
        "witness": _witness(
            '[ClassMarks.many [⟨"u", []⟩], ClassMarks.many [⟨"v", []⟩], '
            'ClassMarks.many [⟨"w", []⟩]]', "false"),
    },

    {
        "id": "empty-chain-default-differs",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_EMPTY_DEFAULT,
        "rationale": (
            "REJECT from the restricted-mode arm (R), aimed at the one thing no "
            "other rival in this battery touches: the DEFAULT the head lookup "
            "falls back on when the chain is empty. Every other rival changes "
            "which entries are gathered, in what order, or what an entry "
            "contributes; this one leaves all of that alone and substitutes a "
            "bare-label default for the empty one the spec pins. So it agrees "
            "with the spec on every NON-empty chain in both modes and diverges "
            "at exactly one point. Refuted at the empty chain in restricted "
            "mode — the only witness in the battery at chain length 0, and the "
            "boundary of the universally quantified domain."
        ),
        "refinement": (
            "A faithful real patch whose restricted reading fell back on a "
            "placeholder label rather than on nothing — the shape a defaulted "
            "lookup takes when the default is written as a bare value instead of "
            "an empty collection — would report a spurious label for a class "
            "whose chain yielded no entry. Recorded honestly, as with the "
            "length-1 case: a real class's resolution chain is never empty, so "
            "no class input reaches this point and it refines no resolve-breaking "
            "patch. Its value is spec-level and that is why it is kept — the "
            "obligation is universally quantified over `hierarchy` with no "
            "precondition excluding the empty chain, so the spec is claimed "
            "there and the fallback it claims must be attacked."
        ),
        "witness": _witness("([] : List ClassMarks)", "false"),
    },
    {
        "id": "label-args-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _R_ARGS_REVERSED,
        "rationale": (
            "REJECT from the per-entry CONTRIBUTION clause (C) at a granularity "
            "nothing else in the battery reaches: WITHIN a label rather than "
            "within the chain. Every gathered label keeps its name, its "
            "multiplicity and its position — so every ordering, completeness and "
            "multiplicity attack above passes straight through this rival — but "
            "each label's positional arguments come back reversed. The carrier's "
            "`Mark` equality observes `args`, and mapping.md declares `(name, "
            "args)` the observable, so the spec's equality genuinely pins it. "
            "Refuted at a one-entry chain whose single label carries two "
            "arguments, which is the smallest input where the reversal is "
            "visible at all (a label with 0 or 1 arguments is a fixed point)."
        ),
        "refinement": (
            "A faithful real patch that rebuilt each gathered label while "
            "reversing its positional arguments — the shape an accumulate-by-"
            "prepending pass takes when it is applied one level too deep, to a "
            "label's arguments rather than to the list of labels — would return "
            "the right labels with their arguments backwards. It does NOT "
            "resolve: the F2P test asserts equality against labels built with "
            "specific arguments, and a label whose arguments are reversed "
            "compares unequal, so the assertion fails for any label carrying two "
            "or more arguments. It also breaks the P2P behaviors that apply the "
            "same label at two levels with different arguments and assert both "
            "survive intact."
        ),
        "witness": _witness('[ClassMarks.many [⟨"t", ["1", "2"]⟩]]', "true"),
    },

    # ---- soundness (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pure-branch-on-mode",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PURE,
        "rationale": (
            "The cheapest honest impl: drop the imperative scaffold and the "
            "mutable accumulator entirely and branch on the mode with a pattern "
            "match, returning the selected fold directly. Because the "
            "postcondition's right-hand side is GROUNDED in the input — a fold "
            "of `hierarchy` spelled out in the spec view, with no opaque callee "
            "to echo — this is the honest minimal implementation of the modeled "
            "behavior, not a cheat: it satisfies the equality precisely because "
            "what it returns IS that fold. Structurally maximally distant from "
            "the frozen loop, so the frozen tactic script does not apply and the "
            "obligation is re-proved from the new shape (the `theorem "
            "correct_inheritedMarks` statement is byte-identical; the frozen "
            "lemma set is unchanged, `loop_helper` simply going unused). MUST "
            "verify, else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "mode-test-polarity-flipped",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_POLARITY,
        "rationale": (
            "Behaviourally identical reshape that keeps the gold accumulator "
            "loop verbatim and flips only the POLARITY of the mode test — a "
            "positive test with the two branches exchanged. Exactly the kind of "
            "correct-but-reshaped variant that breaks a form-tuned tactic script "
            "(the frozen `simp only [Bool.not_false, if_true]` step no longer "
            "applies), so it is the control proving that this battery's reject "
            "cases are not just detecting reshaping: the branch collapse is "
            "re-derived for the flipped test and the obligation closes. MUST "
            "verify, else SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "accumulate-by-fold",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_FOLD,
        "rationale": (
            "A third shape: replace the imperative loop with a left fold over "
            "the selected entries, and accumulate each entry's contribution "
            "through the shared per-entry helper instead of re-matching the two "
            "stored forms inline. Keeps the gold mode-selection line, so it "
            "varies a different axis than the two positives above. The "
            "accumulator-generalizing lemma keeps its frozen NAME and role and "
            "is re-proved for the fold shape by the same induction (no new "
            "lemma, no new axiom, no `sorry`); the obligation statement is "
            "untouched and closes. MUST verify, else SPEC-TOO-STRONG."
        ),
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-behavior-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": (
            "Landed by audit; the lane had been dropped on the ground that the "
            "frozen obligation has no precondition, which is the wrong test on a "
            "total carrier. The obligation IS an unconditional universal over "
            "`hierarchy` and `wholeHierarchy`, so no hypothesis can be "
            "over-strong — but the analogue of PRECOND-TOO-STRONG here is the "
            "obligation being UNSATISFIABLE at exactly a behavior-shaped input, "
            "and this case tests that directly. It discharges the post image BY "
            "EVALUATION, as `have`s, at a four-entry chain whose first three "
            "entries each carry one label sharing a single name and differing "
            "only in arguments and whose last contributes nothing — the shape the "
            "modeled behavior is pinned at — in BOTH modes, then closes the "
            "frozen obligation verbatim. A third `have` is the informativeness "
            "control: at that same input the post image evaluates to FALSE for "
            "the output a single-entry gathering would produce, so the positive "
            "halves are real evaluations of the postcondition rather than steps "
            "that would close for any output. Scope: the FROZEN impl is untouched, "
            "the obligation STATEMENT is byte-identical, the frozen tactic body "
            "follows verbatim and the `have`s are cleared before it, so nothing "
            "is assumed and no declaration is added. If this case fails, the "
            "obligation is unsatisfiable — or indifferent — at the one input the "
            "modeled behavior exists for."
        ),
    },
]

# AXIOM_TESTS is intentionally absent: this bundle consumes no callee axiom (the
# axioms region is empty and `opaque_callees` is []), and the axiom lane is
# G-AX's job in any case — this gate ignores it.
