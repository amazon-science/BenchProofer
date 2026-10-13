# properties.py — G-PBT falsification battery for sphinx-doc__sphinx-9367 (lean).
# Ported from the nagini sibling battery and re-expressed against THIS backend's
# carrier. NOT a Lean module — a record of adversarially-reasoned cases the
# spec-lane gate executes. Every case edits ONLY the impl region (and, for the
# positives, the proof tactic body) of the frozen Solution.lean, so
# `markers.same_spec` holds by construction and any rejection is attributable to
# the postcondition rather than to a tampered spec.
#
# Defended surface (this backend's model):
#   renderTuple (elts : List String) -> String
#     `elts` is the ordered, already-rendered text of a sequence's components;
#     the result is the rendered source text of the whole parenthesized sequence.
#     The obligation is `theorem correct_renderTuple : ∀ elts, spec elts (impl elts)`
#     — an unconditional ∀ with NO precondition hypothesis.
#
#   The postcondition is a total case split on the component count, with THREE
#   independent top-level clauses (one per match arm), each fully pinning the
#   output — no output component is left free:
#     (C0) no components      => the empty pair of parentheses
#     (C1) exactly one, `e`   => parentheses around `e` WITH a trailing comma
#                                <- THE LOAD-BEARING CLAUSE (the F2P behavior)
#     (C2) two or more        => parentheses around the components joined by ", "
#
# CARRIER: fully TRANSPARENT. There is no `opaque` callee and no axiom — the
# per-component rendering step is absorbed into the input, so the spec is pinned
# for every component renderer. Consequently every witness below is stated at
# CONCRETE literal inputs and closed by `decide`; no witness needs to condition
# on the carrier, so no witness binds anything and none can be inconsistent.
#
# BINDER COVERAGE: `elts` is the SOLE input binder, so "vary every binder" here
# means varying it across all three arity classes AND across component content —
# a battery whose witnesses all sat at one arity would say nothing about the
# spec's dependence on the count, which is the entire modeled behavior. The seven
# reject witnesses probe the points [], ["1"], ["a"], ["1","2"] (twice, against
# rivals that fail for unrelated reasons), ["a","b"], ["1","2","3"] — arity 0, 1,
# 1, 2, 2, 2, 3.
#
# A HONEST LIMIT ON WHAT THAT VARIATION PROVES (measured, not argued): except for
# multi-reversed-order, each rival differs from gold at EVERY input of the arity
# class it breaks, so within a class the specific component content is a coverage
# choice, not a discriminating one — either C1 witness input refutes either C1
# rival, and this was re-checked with real builds rather than assumed. The arity
# variation is what carries real weight, since arity is what selects the clause.
# multi-reversed-order is the one exception: it is correct on any palindromic
# component list (`["a","a"]` is a measured agreement point), so ITS witness
# input has to be non-palindromic to refute at all.
#
# CLAUSE COVERAGE: C0 attacked by empty-stray-comma; C1 by single-no-comma and
# single-comma-space; C2 by multi-missing-first-sep (separator placement, one
# dropped), multi-trailing-comma (separator placement, one added), multi-
# sep-no-space (separator CONTENT) and multi-reversed-order (component ORDER).
# The positives defend all three clauses at once; admiss-spec-pins-single attests
# to C0/C1/C2 satisfiability without reference to any impl.
#
# POSITIVE STRENGTH — the two structural positives (pos-spec-shape, pos-branch-
# reorder) are both DEFINITIONALLY equal to the frozen impl arm-for-arm, so the
# frozen tactic script closes them unchanged. They are honest but cheap: no proof
# step is redone, so they cannot detect a spec too strong for a reshape needing
# real rewriting. pos-conditional-suffix was added to carry that weight — it is
# correct, NOT definitionally equal, and the frozen script demonstrably fails on
# it, so closing it required the singleton-join reduction and String.append_assoc.
#
# VACUOUS / OMITTED LANES (stated, never fabricated) — see 'assessment':
#   * FRAME-MUTATION: the nagini sibling's MANDATORY frame rival writes back into
#     an input held at half permission. Lean is referentially transparent — no
#     aliasing, no fractional permission — so there is no "write to an input" a
#     rival could even express. Legitimately vacuous here.
#   * DIVERGENCE / vacuity: the nagini sibling's w-diverge rival spins forever so
#     that every postcondition holds vacuously under partial correctness. On lean
#     a non-terminating impl IS writable as `partial def` (the total-`def` claim
#     an earlier revision of this note made is wrong, and was corrected after
#     building it). It is nonetheless not shippable as a reject case: `partial`
#     is banned outright from a witness, and the rival is unfalsifiable anyway —
#     an opaque `partial` constant does not unfold, so measured with real builds
#     every witness against it fails to elaborate (`unfold` cannot unfold it;
#     `simp` leaves the goal), which the gate reads as witness-unproven, an
#     INCONCLUSIVE outcome rather than a rejection. The disposition is that there
#     is nothing to ship, and note this is NOT the velvet vacuity hole: there the
#     diverging impl VERIFIES, whereas here it fails the obligation outright
#     (measured: three tactic shapes, all exit 1). See the corpus-wide termination-semantics finding
#     for the velvet lane, which is settled and not re-derived here.
#   * ADMISSIBILITY: the sibling's admissibility case is PORTED rather than
#     dropped — see admiss-spec-pins-single. It is true that this obligation has
#     no precondition hypothesis, so there is nothing to admit an input TO; but
#     the other half of what the sibling checked (that the postcondition is
#     satisfiable and pins the one-component form, rather than being
#     contradictory) is expressible here and is now asserted.
#   * AXIOM_TESTS: the axiom lane is G-AX's job and this gate ignores it; the
#     model has no opaque callee and no consumed axiom regardless.
#
# WITNESSES: every reject case carries a Lean `example` proving the rival
# CONTRADICTS the spec at one concrete input. It is checked in a file with the
# proof obligation stripped (so no tactic script can mask the verdict) and must
# both (1) elaborate against the rival and (2) FAIL against the frozen solution,
# making it a real discriminator rather than a tautology. Each was built by hand
# both ways before shipping.
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9367"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen regions, verbatim. Every variant _swap()s inside these, so the spec
# view (which elides both) is byte-identical and same_spec is guaranteed.
# ---------------------------------------------------------------------------

_IMPL = '''\
def implementation_renderTuple (elts : List String) : String := Id.run do
  -- Distinguish the tuple's rendered form by how many components it has.
  if elts.length == 0 then
    return "()"
  else if elts.length == 1 then
    -- a one-component tuple keeps its trailing comma
    return "(" ++ elts.headI ++ ",)"
  else
    return "(" ++ String.intercalate ", " elts ++ ")"'''

assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"

# The frozen proof tactic body (everything after `:= by`). ONLY the soundness
# positives touch this. Every reject rival leaves the frozen script untouched:
# its rejection is attested by its `witness`, never by the tactic breakage that
# reshaping an impl would cause anyway.
_PROOF = '''\
  intro elts
  unfold problem_spec_renderTuple implementation_renderTuple
  match elts with
  | [] => rfl
  | [e] => rfl
  | a :: b :: rest => rfl'''

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_impl):
    """Full Solution.lean with ONLY the impl-region def replaced."""
    return _swap(_BASE, _IMPL, new_impl)


def _impl_proof(new_impl, new_proof):
    """Full Solution.lean with the impl def AND the proof tactic body replaced.

    The `theorem correct_renderTuple : ...` STATEMENT stays byte-identical; only
    the tactics after `:= by` change, so the obligation survives intact.
    """
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, new_proof)


def _wit(elts):
    """A refutation `example`: the spec predicate is FALSE at this concrete input
    for the rival's impl.

    `elts` is a Python list of component strings. The carrier is transparent, so
    the arity match, the concatenations and the join all reduce on literals and
    `decide` closes the goal. The head binds NOTHING — there are no hypotheses,
    hence nothing that could be jointly unsatisfiable.
    """
    lit = "[" + ", ".join('"%s"' % e for e in elts) + "]"
    return (
        f'example : ¬ problem_spec_renderTuple {lit}\n'
        f'    (implementation_renderTuple {lit}) := by\n'
        f'  unfold problem_spec_renderTuple implementation_renderTuple\n'
        f'  decide'
    )


# ===========================================================================
# SOUNDNESS POSITIVES — must VERIFY, else SPEC-TOO-STRONG.
# ===========================================================================

# pos-spec-shape: a structurally different CORRECT impl. It drops the imperative
# `Id.run do` + `if`-chain-on-length entirely and dispatches by PATTERN MATCHING
# on the component list, which is a different way of deciding the same three
# arities (destructuring the list vs. computing its length and comparing). All
# three clauses hold verbatim, so it must verify.
#
# NOTE ON PROOF STRENGTH: this reshape is DEFINITIONALLY equal to the frozen impl
# arm-for-arm, so the frozen tactic script closes it unchanged. That makes it a
# cheap positive: it confirms the spec does not depend on the imperative shell,
# but because no proof step had to be redone it cannot detect a spec that is too
# strong for a reshape needing real rewriting. `pos-conditional-suffix` below is
# the positive that carries that weight — its proof genuinely differs.
_POS_MATCH_IMPL = '''\
def implementation_renderTuple (elts : List String) : String :=
  -- Dispatch on the component list's own shape rather than on its length.
  match elts with
  | [] => "()"
  | [e] => "(" ++ e ++ ",)"
  | _ => "(" ++ String.intercalate ", " elts ++ ")"'''

_POS_MATCH_PROOF = '''\
  intro elts
  unfold problem_spec_renderTuple implementation_renderTuple
  match elts with
  | [] => rfl
  | [e] => rfl
  | a :: b :: rest => rfl'''

# pos-conditional-suffix: the LOAD-BEARING positive. Unlike the two reshapes
# above, this impl is NOT definitionally equal to the frozen one arm-for-arm: it
# collapses the three arities to a SINGLE join for every non-empty input and
# recovers the one-component trailing comma as a conditional SUFFIX appended
# after the join. So on the one-component arity it computes
# `"(" ++ intercalate ", " [e] ++ "," ++ ")"` where the spec demands
# `"(" ++ e ++ ",)"`, and on the multi arity it appends an empty suffix. Both are
# EQUAL but not by `rfl` — closing them needs the singleton-join reduction and
# `String.append_assoc` (measured: the frozen script fails on this impl at both
# non-empty arms, and `simp`/`norm_num`/`decide` alone do not close the arity-1
# goal `"(" ++ e ++ "," ++ ")" = "(" ++ e ++ ",)"` because String append is not
# associative by `rfl`). It is therefore the one positive whose verification
# attests that the spec admits a correct impl requiring REAL reproof, which is
# the SPEC-TOO-STRONG direction a definitionally-equal reshape cannot probe.
_POS_SUFFIX_IMPL = '''\
def implementation_renderTuple (elts : List String) : String :=
  -- One join for every non-empty arity; the one-component case is the only one
  -- that also carries a trailing separator, chosen by a conditional SUFFIX
  -- rather than by its own branch.
  if elts.isEmpty then "()"
  else "(" ++ String.intercalate ", " elts ++ (if elts.length == 1 then "," else "") ++ ")"'''

_POS_SUFFIX_PROOF = '''\
  intro elts
  unfold problem_spec_renderTuple implementation_renderTuple
  match elts with
  | [] => rfl
  | [e] =>
    show "(" ++ String.intercalate ", " [e] ++ "," ++ ")" = "(" ++ e ++ ",)"
    rw [show String.intercalate ", " [e] = e from rfl, String.append_assoc]
    rfl
  | a :: b :: rest =>
    show "(" ++ String.intercalate ", " (a :: b :: rest) ++ "" ++ ")"
      = "(" ++ String.intercalate ", " (a :: b :: rest) ++ ")"
    simp'''

# admiss-spec-pins-single: the port of the nagini sibling's admissibility case,
# re-expressed for a carrier with no precondition. There is no precondition to
# admit an input to, so the obligation this case discharges is the OTHER half of
# what the nagini case checked: that the postcondition is SATISFIABLE at each
# arity and actually PINS the one-component form. The four `example`s are stated
# over `problem_spec_renderTuple` ALONE — none mentions the impl — so they attest
# to the postcondition rather than to any implementation of it. Added inside the
# impl region so `same_spec` still holds; the returned value and the frozen proof
# script are untouched.
#
# These are not tautologies: re-measured against a spec whose C1 clause was
# weakened to the parenthesised-only form, the 1st and 2nd `example`s FAIL (the
# `decide` proves the opposite), so they discriminate the clause they name.
_ADMISS_IMPL = _IMPL + '''

-- Spec-level admissibility, independent of ANY implementation: the
-- postcondition is SATISFIABLE at each arity, and at the one-component arity it
-- pins the rendered form to the trailing-comma shape while REFUTING the
-- merely-parenthesised shape.
example : problem_spec_renderTuple ["1"] "(1,)" := by
  unfold problem_spec_renderTuple
  decide

example : ¬ problem_spec_renderTuple ["1"] "(1)" := by
  unfold problem_spec_renderTuple
  decide

example : problem_spec_renderTuple [] "()" := by
  unfold problem_spec_renderTuple
  decide

example : problem_spec_renderTuple ["1", "2"] "(1, 2)" := by
  unfold problem_spec_renderTuple
  decide'''

# pos-branch-reorder: the port of the nagini sibling's branch-reorder positive.
# The two short-circuit arities are tested in the OPPOSITE order (one component
# before none); the multi-component branch is kept verbatim. Behaviorally
# identical because the two guards are mutually exclusive, so it must verify.
_POS_REORDER_IMPL = '''\
def implementation_renderTuple (elts : List String) : String := Id.run do
  -- Same three arities, the two short-circuit guards tested in the other order.
  if elts.length == 1 then
    -- a one-component tuple keeps its trailing comma
    return "(" ++ elts.headI ++ ",)"
  else if elts.length == 0 then
    return "()"
  else
    return "(" ++ String.intercalate ", " elts ++ ")"'''

_POS_REORDER_PROOF = '''\
  intro elts
  unfold problem_spec_renderTuple implementation_renderTuple
  match elts with
  | [] => rfl
  | [e] => rfl
  | a :: b :: rest => rfl'''


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED, else SPEC-TOO-WEAK.
# Each edits ONLY the impl region; the frozen proof body is left intact.
# ===========================================================================

# --- Clause C1 (exactly one component) — the load-bearing clause ---

# single-no-comma: collapses the three-way split back to a TWO-way split on
# emptiness, so a one-component sequence falls into the joining branch and loses
# its trailing comma. This is the pre-patch behavior verbatim (the join of a
# one-element list is that element, so the result is the component merely
# parenthesized). Correct on C0 and C2; wrong on exactly C1.
_U_SINGLE_NO_COMMA = '''\
def implementation_renderTuple (elts : List String) : String := Id.run do
  -- Only a two-way split: any non-empty sequence goes through the join.
  if elts.length == 0 then
    return "()"
  else
    return "(" ++ String.intercalate ", " elts ++ ")"'''

# single-comma-space: keeps a trailing separator for the one-component case but
# uses the full inter-component separator (comma AND space) instead of a bare
# comma, so the rendered text carries a stray space before the closing paren.
# A near-miss: it agrees with the pre-patch rival nowhere and with gold on C0/C2.
_U_SINGLE_COMMA_SPACE = '''\
def implementation_renderTuple (elts : List String) : String := Id.run do
  -- Distinguish the tuple's rendered form by how many components it has.
  if elts.length == 0 then
    return "()"
  else if elts.length == 1 then
    -- trailing separator spelled as the full inter-component separator
    return "(" ++ elts.headI ++ ", )"
  else
    return "(" ++ String.intercalate ", " elts ++ ")"'''

# --- Clause C0 (no components) ---

# empty-stray-comma: emits a comma inside the otherwise empty parentheses — the
# shape an off-by-one that always appends a trailing separator would produce.
# Correct on C1 and C2; wrong on exactly C0.
_U_EMPTY_STRAY_COMMA = '''\
def implementation_renderTuple (elts : List String) : String := Id.run do
  -- Distinguish the tuple's rendered form by how many components it has.
  if elts.length == 0 then
    return "(,)"
  else if elts.length == 1 then
    -- a one-component tuple keeps its trailing comma
    return "(" ++ elts.headI ++ ",)"
  else
    return "(" ++ String.intercalate ", " elts ++ ")"'''

# --- Clause C2 (two or more components) ---

# multi-missing-first-sep: the port of the nagini sibling's dropped-separator
# rival. The first component is concatenated onto the join of the REST with no
# separator between them, so the first two components run together while every
# later adjacency stays separated. Correct on C0 and C1; wrong on exactly C2.
_U_MULTI_MISSING_SEP = '''\
def implementation_renderTuple (elts : List String) : String := Id.run do
  -- Distinguish the tuple's rendered form by how many components it has.
  if elts.length == 0 then
    return "()"
  else if elts.length == 1 then
    -- a one-component tuple keeps its trailing comma
    return "(" ++ elts.headI ++ ",)"
  else
    return "(" ++ elts.headI ++ String.intercalate ", " elts.tail ++ ")"'''

# multi-trailing-comma: OVER-generalizes the one-component trailing comma to
# every arity, so a multi-component sequence also gains a trailing comma. The
# natural over-correction of the modeled change. Correct on C0 and C1; wrong on
# exactly C2.
_U_MULTI_TRAILING_COMMA = '''\
def implementation_renderTuple (elts : List String) : String := Id.run do
  -- Distinguish the tuple's rendered form by how many components it has.
  if elts.length == 0 then
    return "()"
  else if elts.length == 1 then
    -- a one-component tuple keeps its trailing comma
    return "(" ++ elts.headI ++ ",)"
  else
    return "(" ++ String.intercalate ", " elts ++ ",)"'''

# multi-sep-no-space: uses a bare comma as the INTER-component separator instead
# of comma-and-space, so a multi-component sequence renders with its components
# jammed together after each comma. Added by audit: the three C2 rivals present
# attacked the separator's PLACEMENT (one dropped, one added at the end) and the
# component ORDER, but none attacked the separator's own CONTENT — a spec that
# pinned only "some single separator between adjacent components" would admit
# this. Correct on C0 and C1; wrong on exactly C2.
_U_MULTI_SEP_NO_SPACE = '''\
def implementation_renderTuple (elts : List String) : String := Id.run do
  -- Distinguish the tuple's rendered form by how many components it has.
  if elts.length == 0 then
    return "()"
  else if elts.length == 1 then
    -- a one-component tuple keeps its trailing comma
    return "(" ++ elts.headI ++ ",)"
  else
    return "(" ++ String.intercalate "," elts ++ ")"'''

# multi-reversed-order: joins the components in REVERSE order. Attacks the
# ordering C2 fixes (the spec joins `elts` itself, so component order is pinned),
# a dimension none of the arity rivals touch. Correct on C0 and C1 (and on any
# palindromic component list); wrong on C2 whenever the order is observable.
_U_MULTI_REVERSED = '''\
def implementation_renderTuple (elts : List String) : String := Id.run do
  -- Distinguish the tuple's rendered form by how many components it has.
  if elts.length == 0 then
    return "()"
  else if elts.length == 1 then
    -- a one-component tuple keeps its trailing comma
    return "(" ++ elts.headI ++ ",)"
  else
    return "(" ++ String.intercalate ", " elts.reverse ++ ")"'''


SPEC_TESTS = [

    # --- POSITIVES -------------------------------------------------------
    {
        "id": "pos-spec-shape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_POS_MATCH_IMPL, _POS_MATCH_PROOF),
        "rationale": (
            "a structurally different CORRECT impl: it dispatches by pattern "
            "matching on the component list's shape instead of computing the "
            "length and comparing it against 0 and 1, and drops the imperative "
            "`Id.run do` / early-`return` shell for a pure functional "
            "expression. All three clauses (C0 empty, C1 single-with-trailing-"
            "comma, C2 joined) hold verbatim, so it must verify; if it fails => "
            "SPEC-TOO-STRONG (a faithful correct impl rejected). Reproven for "
            "the new shape; the theorem STATEMENT is byte-identical, only the "
            "tactic body changed."
        ),
    },
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_POS_REORDER_IMPL, _POS_REORDER_PROOF),
        "rationale": (
            "the port of the nagini sibling's branch-reorder positive: the two "
            "short-circuit arity guards are tested in the OPPOSITE order (one "
            "component before none) while the multi-component branch is kept "
            "verbatim. The guards are mutually exclusive so the impl is "
            "behaviorally identical and must verify, else SPEC-TOO-STRONG. This "
            "is the cheap structural positive — it confirms the spec constrains "
            "the OUTPUT, not the order in which the arities are decided. Like "
            "pos-spec-shape it is definitionally equal to the frozen impl at "
            "every arity, so the frozen tactic script closes it unchanged; "
            "pos-conditional-suffix is the positive that needed real reproof."
        ),
    },
    {
        "id": "pos-conditional-suffix",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl_proof(_POS_SUFFIX_IMPL, _POS_SUFFIX_PROOF),
        "rationale": (
            "the LOAD-BEARING positive, added by audit because the two "
            "reshapes above are both definitionally equal to the frozen impl "
            "arm-for-arm and so verify under the frozen tactic script "
            "UNCHANGED — passing honestly while reproving nothing. This impl "
            "collapses the arity split to a single join for every non-empty "
            "input and recovers the one-component trailing comma as a "
            "conditional SUFFIX after the join. It is correct but NOT "
            "definitionally equal: the arity-1 goal is "
            "`\"(\" ++ e ++ \",\" ++ \")\" = \"(\" ++ e ++ \",)\"`, which "
            "`rfl` does not close because String append is not associative by "
            "reduction. Measured: the frozen script FAILS on this impl at both "
            "non-empty arms, and closing it needs the singleton-join reduction "
            "plus `String.append_assoc`. So its verification is real evidence "
            "the spec admits a faithful correct impl requiring genuine "
            "rewriting — the SPEC-TOO-STRONG direction a definitionally-equal "
            "reshape cannot reach. If it fails => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-spec-pins-single",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS_IMPL),
        "rationale": (
            "the port of the nagini sibling's admissibility case, re-expressed "
            "for a carrier with NO precondition. Nothing here needs admitting "
            "to a precondition, so this checks the other half of what the "
            "sibling checked: that the postcondition is SATISFIABLE at each "
            "arity and genuinely PINS the one-component form rather than being "
            "contradictory or unusable. All four `example`s are stated over "
            "`problem_spec_renderTuple` alone — none mentions any impl — so "
            "they attest to the postcondition itself. They are not "
            "tautologies: re-measured against a spec whose one-component "
            "clause was weakened to the parenthesised-only form, the first two "
            "FAIL (`decide` proves the opposite), so they discriminate exactly "
            "the clause they name. If this fails => PRECOND-TOO-STRONG (here: "
            "an unsatisfiable postcondition)."
        ),
    },

    # --- C1: the load-bearing clause -------------------------------------
    {
        "id": "single-no-comma",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_U_SINGLE_NO_COMMA),
        "refinement": (
            "this is the pre-patch behavior verbatim: a single two-way split on "
            "emptiness, so every non-empty sequence is rendered through the "
            "joining branch. Joining a one-element list yields that element "
            "alone, so a one-component sequence renders as the component merely "
            "wrapped in parentheses, with NO trailing comma — which reads as a "
            "parenthesized expression rather than a one-element sequence. That "
            "is exactly the string the FAIL_TO_PASS case rejects: it asserts the "
            "rendered form WITH the trailing comma. Correct on the empty and "
            "multi-component forms (the PASS_TO_PASS cases), so a true "
            "partial-domain break rather than a blanket wrong impl. Its "
            "faithful real patch is the unpatched code path, which is precisely "
            "what currently FAILS the F2P — it does NOT resolve."
        ),
        "rationale": (
            "REJECTED by C1: at a one-component input the spec demands "
            "parentheses around the component followed by a comma, while the "
            "rival omits the comma. Witness at arity 1 (`[\"1\"]`) — the "
            "sub-domain the modeled change exists to fix, and the only arity at "
            "which this rival differs from gold."
        ),
        "witness": _wit(["1"]),
    },
    {
        "id": "single-comma-space",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_U_SINGLE_COMMA_SPACE),
        "refinement": (
            "a NEAR-MISS that does remember the one-component case needs a "
            "trailing separator, but reuses the full inter-component separator "
            "(comma followed by a space) instead of a bare comma, so the "
            "rendered text carries a stray space before the closing "
            "parenthesis. The F2P case asserts an exact string, so the extra "
            "space fails it just as the missing comma does — it does NOT "
            "resolve. Distinct from single-no-comma: it agrees with gold on "
            "strictly different outputs, so it gets its own witness input "
            "rather than sharing one."
        ),
        "rationale": (
            "REJECTED by C1: the spec pins the one-component form to the "
            "component followed by a bare comma and the closing parenthesis; "
            "the rival inserts a space between them. Witness at arity 1 with "
            "DIFFERENT component content (`[\"a\"]`, vs `[\"1\"]` for "
            "single-no-comma), so the two C1 rivals are refuted at distinct "
            "POINTS. Note these two points are not INDEPENDENT: both rivals "
            "differ from gold at every arity-1 input, so either witness input "
            "would refute either rival (re-measured: this rival's witness "
            "input under single-no-comma's impl, and vice versa, both "
            "elaborate). The distinct content is a coverage choice — it varies "
            "the component payload as well as the arity — not evidence that "
            "the two rivals fail on disjoint sub-domains."
        ),
        "witness": _wit(["a"]),
    },

    # --- C0 --------------------------------------------------------------
    {
        "id": "empty-stray-comma",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_U_EMPTY_STRAY_COMMA),
        "refinement": (
            "a patch that always appended a trailing separator (an off-by-one "
            "in the arity handling) would put a comma inside the otherwise "
            "empty parentheses. A PASS_TO_PASS case asserts the empty sequence "
            "renders as the bare empty pair of parentheses, so this regresses a "
            "currently-passing test — it does NOT resolve. Correct on the one- "
            "and multi-component forms, so a partial-domain break confined to "
            "the empty input."
        ),
        "rationale": (
            "REJECTED by C0: at the empty input the spec demands the empty pair "
            "of parentheses and the rival emits a comma between them. Witness "
            "at arity 0 (`[]`) — the boundary no other rival's witness probes, "
            "and the only arity at which this rival differs from gold."
        ),
        "witness": _wit([]),
    },

    # --- C2 --------------------------------------------------------------
    {
        "id": "multi-missing-first-sep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_U_MULTI_MISSING_SEP),
        "refinement": (
            "the port of the nagini sibling's dropped-separator rival: the "
            "first component is concatenated directly onto the join of the "
            "remaining ones, so the first two components run together while "
            "every later adjacency stays correctly separated (a three-component "
            "sequence renders with only one separator instead of two). The "
            "PASS_TO_PASS multi-component cases assert the fully separated "
            "form, so this regresses them — it does NOT resolve. Correct on the "
            "empty and one-component forms."
        ),
        "rationale": (
            "REJECTED by C2: the spec pins the multi-component form to the "
            "components joined by the separator, and the rival omits the first "
            "separator. Witness at arity 3 (`[\"1\",\"2\",\"3\"]`) — the only "
            "witness at arity >2, and the arity that distinguishes 'dropped ONE "
            "separator' from 'dropped every separator', since at arity 2 the "
            "two are indistinguishable."
        ),
        "witness": _wit(["1", "2", "3"]),
    },
    {
        "id": "multi-trailing-comma",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_U_MULTI_TRAILING_COMMA),
        "refinement": (
            "the natural OVER-correction of the modeled change: having learned "
            "that a one-component sequence keeps a trailing comma, this impl "
            "appends one at every arity, so a multi-component sequence also "
            "gains a trailing comma before its closing parenthesis. It PASSES "
            "the F2P one-component case, which makes it the most dangerous "
            "shape here — but the PASS_TO_PASS multi-component cases assert no "
            "trailing comma, so it regresses them and does NOT resolve. This is "
            "the rival that distinguishes 'the trailing comma is required at "
            "arity 1' from 'the trailing comma is always allowed'."
        ),
        "rationale": (
            "REJECTED by C2: the spec pins the multi-component form to the "
            "joined components followed immediately by the closing parenthesis; "
            "the rival inserts a comma. Witness at arity 2 (`[\"1\",\"2\"]`), "
            "the smallest input in C2's sub-domain."
        ),
        "witness": _wit(["1", "2"]),
    },
    {
        "id": "multi-sep-no-space",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_U_MULTI_SEP_NO_SPACE),
        "refinement": (
            "an impl that separated the components with a bare comma instead "
            "of a comma followed by a space would render a multi-component "
            "sequence with its components jammed up against each comma. The "
            "PASS_TO_PASS multi-component cases assert the spaced form, so "
            "this regresses them — it does NOT resolve. Added by audit: the "
            "three C2 rivals already present attack the separator's PLACEMENT "
            "(one dropped before the first adjacency, one added after the "
            "last) and the component ORDER, but none attacks the separator's "
            "own CONTENT, so a spec that pinned only 'adjacent components are "
            "divided by some single separator' would admit this rival and the "
            "battery would not notice."
        ),
        "rationale": (
            "REJECTED by C2: the spec pins the separator to a comma FOLLOWED "
            "BY A SPACE, and the rival drops the space. Witness at arity 2 "
            "(`[\"1\",\"2\"]`), the smallest input at which any separator is "
            "emitted at all — at arity 0 and 1 no inter-component separator "
            "exists, so this rival agrees with gold there."
        ),
        "witness": _wit(["1", "2"]),
    },
    {
        "id": "multi-reversed-order",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_U_MULTI_REVERSED),
        "refinement": (
            "an impl that joined the components in reverse order would render a "
            "multi-component sequence with its components transposed. The "
            "PASS_TO_PASS multi-component cases assert the components in source "
            "order, so it regresses them — it does NOT resolve. Included "
            "because ORDER is a dimension of C2 that none of the arity rivals "
            "touch: a spec that pinned only the multiset of components (or only "
            "the separator count) would admit this rival, and the battery would "
            "never notice."
        ),
        "rationale": (
            "REJECTED by C2: the spec joins `elts` itself, pinning component "
            "ORDER, and the rival joins the reversal. Witness at arity 2 with "
            "content chosen so the order is OBSERVABLE (`[\"a\",\"b\"]`): "
            "unlike the other rivals this one is correct on any palindromic "
            "component list, so the witness input has to be non-palindromic or "
            "it would not refute at all. `[\"a\",\"a\"]` is a measured "
            "agreement point. The input differs from multi-trailing-comma's "
            "`[\"1\",\"2\"]` for content coverage; it is NOT the case that "
            "neither witness would refute the other rival — both rivals differ "
            "from gold at both of those inputs, and each witness was re-built "
            "against the other's impl and elaborated."
        ),
        "witness": _wit(["a", "b"]),
    },
]


# ===========================================================================
# AXIOM_TESTS — none. The axiom lane is G-AX's job and this gate ignores it;
# this model has no `opaque` callee and no consumed axiom in any case, because
# the per-component rendering step is absorbed into the input carrier.
# ===========================================================================
AXIOM_TESTS = []
