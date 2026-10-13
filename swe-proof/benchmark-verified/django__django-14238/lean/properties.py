# properties.py — G-PBT falsification battery for django__django-14238 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, for a positive that reproves, the proof body — is edited),
# checked by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   subclassCheck (isSub : Cls → Cls → Bool) (superCheck : Cls → Bool)
#                 (subclass : Cls) (subclasses : List Cls) : Bool
#   ONE obligation, `theorem correct_subclassCheck`, with NO precondition
#   hypothesis. The single postcondition clause pins the boolean result to
#
#       (subclasses.any (fun d => isSub subclass d)) || superCheck subclass
#
#   i.e. a disjunction of two INDEPENDENT legs, each grounded in the actual inputs:
#     (L1) the designated-member leg: SOME element of the actual member list stands
#          in the given relation to the actual candidate — note the relation is
#          applied with the CANDIDATE first and the MEMBER second, and the
#          quantification is over the WHOLE list;
#     (L2) the inherited-check leg: the given check applied to the actual candidate.
#
# CARRIER NOTE — what changes from nagini, and what that costs.
#   The nagini sibling carried a concrete `Cls` record (`cid : int`, `anc : PSet[int]`)
#   behind fractional read permission, a grounded `@Pure` membership helper, and a
#   FIXED pair of designated members passed as two separate parameters (`base_one`,
#   `base_two`) plus a third `owner` leg. This backend abstracts further and in a way
#   that is strictly stronger for the spec: `Cls` is an opaque `Type`, the membership
#   relation and the inherited check are UNIVERSALLY QUANTIFIED function parameters,
#   and the designated members are a `List Cls` of arbitrary length. So the result is
#   pinned for EVERY relation and EVERY member list, not just for one record layout.
#   Consequences for the port:
#     * nagini's two fixed-base rivals (drop one base / consult one base twice)
#       become rivals about the TRAVERSAL of the member list and about the ARGUMENTS
#       the relation is applied to — there is no second named base to drop. The
#       "consult one leg twice and never the other" shape DOES port, onto the two
#       legs the carrier has rather than onto two named bases: see
#       riv-dup-inherited-leg, the mirror of riv-drop-inherited.
#     * `Cls` carries no DecidableEq in the frozen signature, so nagini's identity-
#       membership rival cannot be spelled `subclass = d`. Its faithful re-expression
#       is the ANTISYMMETRIC closure of the given relation, `isSub subclass d &&
#       isSub d subclass` — "identical as far as the subclass order can tell", which
#       is exactly identity membership stated in the vocabulary this carrier has.
#     * every witness instantiates the abstract carrier at `Nat` with a concrete
#       relation and check, so the whole postcondition COMPUTES and `decide` closes
#       it at a literal input. No conditioning on an opaque term is needed here.
#
# LANES THAT DO NOT PORT (see 'assessment' in the submitted payload):
#   * FRAME-MUTATION — nagini's #1 class, and it shipped TWO of them
#     (frame-write-cid, frame-write-anc: a rival writing a field of a parameter held
#     at Acc(.,1/4)). Lean is referentially transparent — no aliasing, no fractional
#     permission, parameters are values — so a "store into a read-only input" rival
#     is not expressible at all. The class is genuinely VACUOUS here, not a hole.
#   * ADMISSIBILITY — nagini's admiss-unfold defended the fractional-permission
#     precondition by asserting the @Pure helper unfolds from the held share. That
#     specific content (a @Pure body unfolding from a 1/4 share) presupposes a
#     permission logic this carrier does not have. But the LANE is NOT vacuous, and
#     "the frozen obligation has no precondition hypothesis" is NOT a reason to drop
#     it: the analogue of PRECOND-TOO-STRONG on a total carrier is the obligation
#     being UNSATISFIABLE at exactly an F2P-shaped input, which a positive that
#     discharges the obligation at that concrete input — by evaluation, as a `have`,
#     before closing the frozen obligation verbatim — tests directly. Ported below as
#     adm-ground-derived-member.
#   * DIVERGENCE / NON-TERMINATION — the nagini sibling carries none, and on this
#     backend the class is vacuous regardless: `implementation_subclassCheck` is a
#     total Lean `def` over a `List`, so a diverging implementation cannot be
#     written. (Contrast velvet under partial termination semantics, where this
#     would be a KNOWN SPEC HOLE — the corpus-wide termination-semantics finding — not a vacuity.)
#   * AXIOM_TESTS — dropped. The axiom lane is G-AX's job and this gate ignores it;
#     there is no consumed axiom here anyway (both callees are plain parameters).
from pathlib import Path

INSTANCE = "django__django-14238"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies ENTIRELY inside a single region and is unique in the file.
# ---------------------------------------------------------------------------

# The whole frozen impl body (inside impl-start / impl-end), comments included.
_IMPL = (
    "  -- Accept the candidate if it is a subclass of any designated member class\n"
    "  -- (reflexive-transitive subclass relation), or if the inherited check accepts.\n"
    "  let mut matched := false\n"
    "  for d in subclasses do\n"
    "    if isSub subclass d then\n"
    "      matched := true\n"
    "  return matched || superCheck subclass"
)
# The loop's guard alone (impl region) — for rivals that only change WHICH
# relation instance decides membership, leaving the traversal shape untouched.
_GUARD = "    if isSub subclass d then\n      matched := true\n"
# The final combination line (impl region) — for the drop-a-leg rival.
_RET = "  return matched || superCheck subclass"
for _a in (_IMPL, _GUARD, _RET):
    if _BASE.count(_a) != 1:
        raise AssertionError(f"impl anchor drifted: {_a!r}")

# The frozen proof body: everything strictly inside proof-start / proof-end after
# the `theorem correct_subclassCheck` statement. The STATEMENT itself is never
# touched by any case (variant_scope enforces byte-identity).
_PROOF_START = "  intro Cls isSub superCheck subclass subclasses\n"
if _BASE.count(_PROOF_START) != 1:
    raise AssertionError("proof anchor drifted")
_PROOF = _BASE[_BASE.index(_PROOF_START):_BASE.index("-- proof-end")].rstrip("\n")


def _impl(body):
    """Replace the frozen impl body; proof body left frozen (rival shape)."""
    return _swap(_BASE, _IMPL, body)


def _ground(have_block):
    """Prepend a ground `have` to the frozen tactic body, impl left FROZEN.

    Discharges the obligation at one concrete input before closing the frozen
    obligation verbatim: statement byte-identical, no new declaration, no
    axiom/sorry, and the frozen impl and proof script are otherwise untouched.
    """
    return _swap(_BASE, _PROOF_START, have_block + _PROOF_START)


def _reproved(body, tactics):
    """Replace the frozen impl body AND honestly re-close the SAME obligation.

    Only the tactic body moves: `theorem correct_subclassCheck`'s statement stays
    byte-identical, and no new axiom / lemma / sorry / native_decide is introduced.
    """
    return _swap(_swap(_BASE, _IMPL, body), _PROOF, tactics)


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-legs-as-locals: compute each of the two independent legs into a named local
# and combine once, dropping the accumulator loop in favour of the library
# traversal. Same total decision on every input, a shape a faithful patch could
# equally take. Reproved honestly (the frozen script is an induction tuned to the
# `forIn` accumulator, which this shape no longer has).
_POS_LOCALS = _reproved(
    "  let memberHit := subclasses.any (fun d => isSub subclass d)\n"
    "  let inherited := superCheck subclass\n"
    "  return memberHit || inherited",
    "  intro Cls isSub superCheck subclass subclasses\n"
    "  unfold problem_spec_subclassCheck implementation_subclassCheck\n"
    "  simp [Id.run, pure]",
)

# pos-legs-commuted: the SAME two legs, evaluated and combined in the OPPOSITE
# order. The postcondition's disjunction is commutative, so the verdict is
# identical on every input; only the order in which the legs are consulted
# changes. This is the case that would catch a postcondition over-fit to one leg
# order (e.g. one phrased as an if-then-else on the member leg).
_POS_COMMUTED = _reproved(
    "  let inherited := superCheck subclass\n"
    "  let memberHit := subclasses.any (fun d => isSub subclass d)\n"
    "  return inherited || memberHit",
    "  intro Cls isSub superCheck subclass subclasses\n"
    "  unfold problem_spec_subclassCheck implementation_subclassCheck\n"
    "  simp [Id.run, pure, Bool.or_comm]",
)

# pos-early-return: keeps the imperative traversal but SHORT-CIRCUITS — the first
# member that subsumes the candidate returns immediately, so the inherited check
# is never consulted on that path. Behaviourally identical (the inherited leg can
# only be reached when the member leg is false, and then it alone decides), but a
# genuinely different control-flow shape: the accumulator is gone and the loop
# exits early. Reproved by induction on the member list.
_POS_EARLY = _reproved(
    "  for d in subclasses do\n"
    "    if isSub subclass d then\n"
    "      return true\n"
    "  return superCheck subclass",
    "  intro Cls isSub superCheck subclass subclasses\n"
    "  unfold problem_spec_subclassCheck implementation_subclassCheck\n"
    "  induction subclasses with\n"
    "  | nil => rfl\n"
    "  | cons a as ih =>\n"
    "    rw [List.forIn_cons, List.any_cons]\n"
    "    by_cases h : isSub subclass a = true <;>\n"
    "      simp only [h, Id.run, bind, pure, Bool.true_or, Bool.false_or,\n"
    "        if_true, if_false] at ih ⊢ <;> simp_all [Id.run]",
)


# ===========================================================================
# ADMISSIBILITY — must VERIFY (else PRECOND-TOO-STRONG).
# ===========================================================================

# adm-ground-derived-member: the obligation carries no precondition HYPOTHESIS,
# but that is not the same as the lane being vacuous. What can still go wrong on
# a total carrier is the obligation being UNSATISFIABLE at exactly an F2P-shaped
# input — a postcondition whose two legs cannot jointly take the values the
# reported scenario needs. So this case discharges the spec predicate at one
# concrete F2P-shaped point BY EVALUATION, as a `have`, and only then closes the
# frozen obligation verbatim. The point chosen is the shape the whole change is
# about: a candidate that lies STRICTLY BELOW a designated member under a
# reflexive-transitive relation (so it is not the member itself), with the
# inherited check REFUSING — i.e. the member leg alone must carry the
# acceptance. If the spec were unsatisfiable there, no `have` could close.
_ADM_ARGS = "(fun c d => decide (d <= c)) (fun _ => false) (3 : Nat) [1]"
_ADM_GROUND = _ground(
    f"  have _ground : problem_spec_subclassCheck {_ADM_ARGS}\n"
    f"      (implementation_subclassCheck {_ADM_ARGS}) := by\n"
    f"    unfold problem_spec_subclassCheck implementation_subclassCheck\n"
    f"    decide\n"
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly, edits only the impl region, and leaves the frozen proof
# body in place (that script will not close for the reshaped impl, but the gate
# does not read a rival's own build as evidence — it reads the witness, which is
# checked in a file with the obligation removed).
# ===========================================================================

# riv-identity-membership: the pre-change membership test. Requires the relation
# to hold in BOTH directions, i.e. candidate and member indistinguishable in the
# subclass order — identity membership, expressed in the only vocabulary this
# carrier has (`Cls` has no DecidableEq here). Accepts each designated member
# itself; rejects anything properly below one.
_RIV_IDENTITY = _impl(
    _IMPL.replace(
        _GUARD,
        "    if isSub subclass d && isSub d subclass then\n      matched := true\n",
    )
)

# riv-relation-reversed: applies the membership relation with the ARGUMENTS
# SWAPPED — it asks whether each designated member is a subclass of the candidate
# rather than the reverse. A near-miss: it agrees with the frozen verdict wherever
# the relation is symmetric or the inherited leg carries the decision, and
# diverges exactly on the ordered pairs, in BOTH directions.
_RIV_REVERSED = _impl(
    _IMPL.replace(_GUARD, "    if isSub d subclass then\n      matched := true\n")
)

# riv-first-member-only: consults only the FIRST designated member, ignoring the
# rest of the list. Correct whenever the head decides; wrong on a candidate
# subsumed only by a later member.
_RIV_FIRST = _impl(
    "  let mut matched := false\n"
    "  for d in subclasses.take 1 do\n"
    "    if isSub subclass d then\n"
    "      matched := true\n"
    "  return matched || superCheck subclass"
)

# riv-drop-inherited: keeps the member leg in full but DROPS the inherited-check
# leg from the combination.
_RIV_NO_INHERITED = _impl(_IMPL.replace(_RET, "  return matched"))

# riv-dup-inherited-leg: the faithful re-expression of nagini's "consult one leg
# TWICE and never the other" near-miss. There is no second named base here to
# duplicate, so the duplication lands on the two legs the carrier does have: the
# member-list guard is rewritten to consult the INHERITED check instead of the
# membership relation, so the impl reduces to the inherited leg alone and the
# designated-member list is never actually interrogated. Distinct from
# riv-drop-inherited (which keeps the member leg and drops the inherited one):
# this is the MIRROR attack, and it is the only rival under which a candidate
# that genuinely matches a designated member is refused.
_RIV_DUP_INHERITED = _impl(
    _IMPL.replace(_GUARD, "    if superCheck subclass then\n      matched := true\n")
)

# riv-inherited-on-members: the inherited check is applied to each designated
# MEMBER instead of to the candidate. Both legs are still present and the member
# list is still traversed in full, so the shape looks right; what is wrong is
# WHICH class the inherited check is asked about. Attacks the GROUNDING of L2 in
# the actual candidate, which no other rival touches (riv-drop-inherited removes
# L2 outright; riv-dup-inherited-leg keeps L2 grounded correctly).
_RIV_INHERITED_ON_MEMBERS = _impl(
    _IMPL.replace(_GUARD, "    if superCheck d then\n      matched := true\n")
)

# riv-xor-legs: combines the two legs with XOR instead of OR. It agrees with the
# frozen verdict everywhere EXCEPT where BOTH legs are true, and there it
# cancels them and refuses. That overlap sub-domain — a candidate that both
# matches a designated member AND is accepted by the inherited check — is
# reachable and is visited by no other witness in the battery.
_RIV_XOR = _impl(_IMPL.replace(_RET, "  return xor matched (superCheck subclass)"))

# riv-accept-all: the trivially over-permissive rival — accepts every candidate,
# consulting neither leg's content.
_RIV_ALL = _impl(
    "  let mut matched := true\n"
    "  for _d in subclasses do\n"
    "    matched := true\n"
    "  return matched"
)


# ---------------------------------------------------------------------------
# Witnesses. The carrier is abstract, so each witness INSTANTIATES it at `Nat`
# with a concrete relation and a concrete inherited check, at which point the
# whole postcondition computes and `decide` closes `¬ problem_spec … (impl …)`.
# Because the frozen obligation is universally quantified over the relation, the
# check, the candidate and the member list, any such instance is an admissible
# input point — and a rival that contradicts the spec at ONE of them contradicts
# it, full stop. Every witness states its refutation at literal inputs, so none
# binds a hypothesis and none can be inconsistent.
# ---------------------------------------------------------------------------

def _wit(is_sub, super_check, subclass, subclasses, note):
    args = f"({is_sub}) ({super_check}) ({subclass}) {subclasses}"
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_subclassCheck {args}\n"
        f"    (implementation_subclassCheck {args}) := by\n"
        f"  unfold problem_spec_subclassCheck implementation_subclassCheck\n"
        f"  decide"
    )


# Relations used below, all decidable on Nat:
#   `fun c d => decide (d <= c)`  — a genuine partial order: reflexive and
#       transitive, so a faithful stand-in for a reflexive-transitive subclass
#       relation, and ANTISYMMETRIC-nontrivial (c below d is distinguishable from
#       d below c), which is what the direction-sensitive rivals need.
#   `fun c d => decide (c = d)`   — the degenerate relation that holds only on
#       identical arguments; useful where the rival must be separated on WHICH
#       member is consulted rather than on the relation's reach.
#   `fun _ _ => false`            — no member subsumes anything.
_LE = "fun c d => decide (d <= c)"
_EQ = "fun c d => decide (c = d)"
_NEVER = "fun _ _ => false"
_REJECTS = "fun _ => false"
_ACCEPTS = "fun _ => true"


SPEC_TESTS = [
    # ---------------- positive controls (must VERIFY) ----------------
    {
        "id": "pos-legs-as-locals",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LOCALS,
        "rationale": (
            "structurally-different but CORRECT impl: the two independent legs of "
            "the postcondition (the designated-member leg and the inherited-check "
            "leg) are each computed into a named local and combined once, replacing "
            "the accumulator traversal with the library traversal. Identical verdict "
            "on every input. The `theorem correct_subclassCheck` STATEMENT is kept "
            "byte-identical and the proof body is honestly re-closed with "
            "`simp [Id.run, pure]` (no new axiom/lemma/sorry — the frozen script is "
            "an induction over the `forIn` accumulator this shape no longer has). If "
            "it FAILS => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-legs-commuted",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_COMMUTED,
        "rationale": (
            "the SAME two legs consulted and combined in the OPPOSITE order. The "
            "postcondition's top-level disjunction is commutative, so the verdict is "
            "identical at every input; only which leg is evaluated first changes — a "
            "shape a faithful patch could equally take. Reproved with "
            "`Bool.or_comm`, statement byte-identical. This is the case that would "
            "catch a postcondition over-fit to one leg order (one phrased as a "
            "branch on the member leg, say). If it FAILS => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-early-return",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_EARLY,
        "rationale": (
            "a third CORRECT shape, and the one furthest from the frozen impl: the "
            "traversal SHORT-CIRCUITS on the first designated member that subsumes "
            "the candidate and never consults the inherited check on that path. "
            "Still identical on every input (the inherited leg is reachable only "
            "when the member leg is false, where it alone decides), but the "
            "accumulator is gone and the loop exits early, so the proof is a fresh "
            "induction on the member list. Also carries the ground the nagini "
            "admissibility lane covered — that a normally-shaped correct impl is "
            "admitted — since this obligation has no precondition to be too strong. "
            "If it FAILS => SPEC-TOO-STRONG."
        ),
    },

    # ---------------- admissibility (must VERIFY) ----------------
    {
        "id": "adm-ground-derived-member",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADM_GROUND,
        "rationale": (
            "the obligation must be SATISFIABLE at an F2P-shaped input, not merely "
            "provable in the abstract. The frozen obligation carries no precondition "
            "hypothesis, but the analogue of PRECOND-TOO-STRONG on a total carrier is "
            "the postcondition being unsatisfiable at exactly the input the reported "
            "scenario needs, so this case discharges "
            "`problem_spec_subclassCheck` at one CONCRETE such point by evaluation "
            "(`decide`), as a `have`, and only then closes the frozen obligation "
            "verbatim. The point is the shape the whole change is about: the candidate "
            "lies STRICTLY BELOW a designated member under a reflexive-transitive "
            "relation (`fun c d => decide (d <= c)` at candidate 3, members [1]) — so "
            "it is not the member itself — while the inherited check REFUSES, which "
            "forces the designated-member leg (L1) alone to carry the acceptance. "
            "Nothing is assumed: the impl and the frozen tactic script are untouched, "
            "the statement is byte-identical, and no new declaration/axiom/sorry is "
            "introduced. If it FAILS => PRECOND-TOO-STRONG (the modeled behavior "
            "would be unsatisfiable at exactly a normal in-domain input, which would "
            "make every positive above vacuously true)."
        ),
    },

    # ---------------- uniqueness rivals (must be REJECTED) ----------------
    {
        "id": "riv-identity-membership",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_IDENTITY,
        "refinement": (
            "this is the PRE-CHANGE membership test: a candidate is matched only "
            "when it is indistinguishable from a designated member, so a class "
            "properly derived from a designated member is not matched. Its faithful "
            "real counterpart is exactly the behavior the F2P tests were added to "
            "reject: a user class derived from a designated member is then not "
            "recognized as a subclass of the special base, so both the direct "
            "subclass assertion and the project-default primary-key configuration "
            "check still fail. It does NOT resolve, so a rival that VERIFIED here "
            "would be a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by the postcondition's designated-member leg (L1), which pins "
            "acceptance to `isSub subclass d` for some member d — a strictly weaker "
            "requirement than that relation holding in BOTH directions. Attacks L1 "
            "on the sub-domain where the candidate lies strictly below a member; "
            "varies the `isSub` and `subclass` binders. If it VERIFIES => "
            "SPEC-TOO-WEAK (the reflexive-transitive strengthening would be hollow)."
        ),
        # candidate 3 is strictly above member 1 under `d <= c`: L1 holds for gold,
        # while the two-directional test fails, and the inherited leg rejects.
        "witness": _wit(_LE, _REJECTS, "3 : Nat", "[1]",
                        "candidate strictly below a designated member in the order"),
    },
    {
        "id": "riv-relation-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REVERSED,
        "refinement": (
            "applying the membership relation with its arguments swapped asks "
            "whether each designated member derives from the candidate, rather than "
            "whether the candidate derives from a designated member. Its faithful "
            "real counterpart accepts an arbitrary ANCESTOR of a designated member "
            "(so unrelated broad classes become acceptable as the project-default "
            "primary-key class, breaking the guard the passing suite relies on) "
            "while still rejecting a user class derived FROM a designated member — "
            "the very case the F2P tests pin. It does NOT resolve."
        ),
        "rationale": (
            "REJECTED by L1, which pins the relation's ARGUMENT ORDER: the candidate "
            "is the first argument and the designated member the second. A near-miss "
            "— it agrees with the frozen verdict wherever the relation is symmetric "
            "or the inherited leg decides, so it needs its own witness at an ordered "
            "pair. Probed at the MIRROR point of riv-identity-membership (candidate "
            "below the member instead of above), which is where reversal, and only "
            "reversal, shows: varies `subclass` and `subclasses` against that case. "
            "If it VERIFIES => SPEC-TOO-WEAK (the spec would not fix the direction)."
        ),
        # candidate 1, member 3: gold's L1 is false and the inherited leg rejects,
        # so gold answers false; the reversed test finds 1 <= 3 and answers true.
        "witness": _wit(_LE, _REJECTS, "1 : Nat", "[3]",
                        "designated member strictly below the candidate in the order"),
    },
    {
        "id": "riv-first-member-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FIRST,
        "refinement": (
            "consulting only the first designated member is the partial fix: it "
            "recognizes derived classes of one designated member and silently leaves "
            "every other designated member on the pre-change behavior. Its faithful "
            "real counterpart therefore resolves only half of the F2P surface — the "
            "direct subclass assertion is added over derived classes of BOTH "
            "designated members, so the other half still fails. It does NOT resolve."
        ),
        "rationale": (
            "REJECTED by L1's quantification over the WHOLE member list "
            "(`subclasses.any`): for a candidate subsumed only by a LATER member the "
            "frozen disjunction is true while this impl consults only the head. "
            "Attacks the `subclasses` binder specifically — the only rival that "
            "moves the list to length > 1 with the deciding element off the head; "
            "also varies `isSub` (degenerate equality relation) and `subclass`. If "
            "it VERIFIES => SPEC-TOO-WEAK (a one-member spec would be indifferent to "
            "the rest of the list)."
        ),
        # members [1, 2], candidate 2 under the equality relation: only the SECOND
        # member decides. gold answers true; the head-only impl answers false.
        "witness": _wit(_EQ, _REJECTS, "2 : Nat", "[1, 2]",
                        "only a designated member past the head matches"),
    },
    {
        "id": "riv-drop-inherited",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NO_INHERITED,
        "refinement": (
            "dropping the inherited-check leg makes the special base reject every "
            "candidate the ordinary type machinery would have accepted on its own — "
            "including the base's own ordinary descendants. Its faithful real "
            "counterpart breaks the existing subclass and instance checks the "
            "passing suite pins (the ordinary-descendant cases), so the unchanged "
            "second leg is load-bearing and such a patch does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition's SECOND independent top-level clause "
            "arm, the inherited-check leg (L2): for a candidate no designated member "
            "subsumes but the inherited check accepts, the frozen disjunction is true "
            "while this impl returns the member leg alone. It is the case that isolates "
            "L2 at a point where L1 is false, so the inherited leg alone carries the "
            "acceptance; riv-xor-legs and riv-inherited-on-members also move the "
            "`superCheck` binder off `fun _ => false`, but at the overlap point and "
            "with a non-constant check respectively. Mirrored by "
            "riv-dup-inherited-leg, which drops L1 and keeps L2. If it VERIFIES => "
            "SPEC-TOO-WEAK (L2 would be "
            "unattacked and a spec omitting it would pass)."
        ),
        # candidate 5 matches no member ([7], equality relation) but the inherited
        # check accepts: gold answers true, the member-leg-only impl answers false.
        "witness": _wit(_EQ, _ACCEPTS, "5 : Nat", "[7]",
                        "no designated member matches; the inherited check accepts"),
    },
    {
        "id": "riv-dup-inherited-leg",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_DUP_INHERITED,
        "refinement": (
            "consulting the inherited check in the place where the designated-member "
            "relation belongs means the member list is never interrogated at all: the "
            "decision collapses onto the inherited leg. Its faithful real counterpart "
            "recognizes only what the ordinary type machinery already recognized, so "
            "neither a designated member nor any class derived from one is accepted — "
            "it leaves the ENTIRE reported failure in place while also breaking the "
            "existing member-class assertions the passing suite pins. It does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by the designated-member leg (L1), which pins acceptance to "
            "`isSub subclass d` for some member d — a leg this impl replaces with a "
            "second copy of L2 and therefore never evaluates. The MIRROR of "
            "riv-drop-inherited: that rival keeps L1 and drops L2, this one keeps L2 "
            "and drops L1, so between them each of the two independent legs is shown "
            "to be load-bearing on its own. What is specific to THIS rival is not that "
            "it refuses a genuine member match — riv-identity-membership and "
            "riv-first-member-only each do that too, at their own witness points, as "
            "machine-checked — but that it makes L1 wholly INERT: the member list is "
            "never interrogated at any input, so no member match whatsoever can be "
            "recognized, whereas those two still accept some matches and miss only a "
            "sub-domain. If it VERIFIES => SPEC-TOO-WEAK (L1 would be inert and a spec "
            "asserting only the inherited leg would pass)."
        ),
        # candidate 4 with member list [4] under the equality relation: L1 holds
        # (the member matches exactly) while the inherited check rejects, so gold
        # answers true and this inherited-leg-only impl answers false.
        "witness": _wit(_EQ, _REJECTS, "4 : Nat", "[4]",
                        "a designated member matches exactly; the inherited check rejects"),
    },
    {
        "id": "riv-inherited-on-members",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_INHERITED_ON_MEMBERS,
        "refinement": (
            "asking the ordinary inherited check about each DESIGNATED MEMBER rather "
            "than about the candidate is a plausible slip that leaves the overall "
            "shape intact. Its faithful real counterpart decides every candidate by a "
            "property of the member classes alone — a constant, since the member list "
            "is fixed — so it accepts or refuses ALL candidates uniformly on that leg: "
            "a class derived from a designated member is still not recognized (leaving "
            "the reported failure in place) while unrelated classes can be accepted "
            "wholesale. It does NOT resolve."
        ),
        "rationale": (
            "REJECTED by L2's GROUNDING: the postcondition applies the inherited check "
            "to `subclass`, the actual candidate, not to a member of the list. This is "
            "the only rival that keeps BOTH legs present and the whole list traversed "
            "while misdirecting an argument, so it is what pins that the second leg is "
            "about the candidate — riv-drop-inherited deletes L2 instead, and "
            "riv-dup-inherited-leg keeps L2 correctly grounded. Probed with a check "
            "that accepts a MEMBER but refuses the candidate, so the two groundings "
            "disagree; varies the `superCheck` binder to a non-constant function, "
            "which nothing else in the battery does. If it VERIFIES => SPEC-TOO-WEAK "
            "(L2 could read any class and the spec would not notice)."
        ),
        # members [7], candidate 5, inherited check accepts only 7: gold answers
        # false (no member matches, the check refuses the candidate) while this
        # impl finds `superCheck 7 = true` and answers true.
        "witness": _wit(_NEVER, "fun c => decide (c = 7)", "5 : Nat", "[7]",
                        "the inherited check accepts a MEMBER but not the candidate"),
    },
    {
        "id": "riv-xor-legs",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_XOR,
        "refinement": (
            "combining the two legs exclusively means a candidate accepted by BOTH "
            "routes is refused. Its faithful real counterpart refuses exactly the "
            "classes that are both a designated member's descendant and already "
            "acceptable to the ordinary machinery — so it breaks acceptances the "
            "passing suite pins while also refusing part of the surface the change is "
            "meant to fix. It does NOT resolve."
        ),
        "rationale": (
            "REJECTED by the postcondition's top-level CONNECTIVE, which is inclusive "
            "disjunction: the result must be true when either leg is true, including "
            "when both are. This is the only case that visits the OVERLAP sub-domain "
            "where L1 and L2 are simultaneously true — every other witness in the "
            "battery holds at most one leg true, so a spec that had accidentally "
            "pinned exclusive-or would satisfy all of them. Uses the order relation "
            "with an accepting inherited check, a binder combination no other case "
            "pairs. If it VERIFIES => SPEC-TOO-WEAK (the connective would be "
            "underdetermined on the overlap)."
        ),
        # candidate 3 over members [1] under `d <= c` with the check accepting:
        # BOTH legs are true, so gold answers true while xor cancels to false.
        "witness": _wit(_LE, _ACCEPTS, "3 : Nat", "[1]",
                        "both legs are true: inclusive or accepts, exclusive or cancels"),
    },
    {
        "id": "riv-accept-all",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ALL,
        "refinement": (
            "accepting every candidate unconditionally would make the special base "
            "report every class as one of its subclasses. Its faithful real "
            "counterpart makes the project-default primary-key guard admit arbitrary "
            "unrelated classes and inverts the negative assertions the passing suite "
            "makes about non-members, so it does NOT resolve — it trades the reported "
            "failure for a broader one."
        ),
        "rationale": (
            "REJECTED by the postcondition on the sub-domain where BOTH legs are "
            "false: the frozen disjunction is then false while this impl returns "
            "true. The complementary attack to riv-drop-inherited — it pins that the "
            "result is not merely IMPLIED BY but EQUAL to the disjunction. Probed at "
            "a third relation instance (nothing matches anything) and the longest "
            "member list in the battery, so it also varies `isSub`, `subclass` and "
            "`subclasses`. If it VERIFIES => SPEC-TOO-WEAK (the spec would only "
            "bound the result from one side)."
        ),
        # no member subsumes anything and the inherited check rejects: gold answers
        # false at candidate 0 over [1, 2, 3]; the constant impl answers true.
        "witness": _wit(_NEVER, _REJECTS, "0 : Nat", "[1, 2, 3]",
                        "neither leg accepts: the frozen verdict is false"),
    },
]


# No @ContractOnly axiom, no `opaque` callee: the membership relation and the
# inherited check are universally-quantified PARAMETERS of the obligation, so
# there is nothing for an axiom lane to fuzz here, and the axiom lane is G-AX's
# job regardless.
AXIOM_TESTS = []
