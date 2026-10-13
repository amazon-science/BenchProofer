# properties.py — G-PBT falsification battery for django__django-13821 (lean lane).
# PORTED from the nagini sibling's battery: the adversarial ARGUMENTS are carried
# over, the mechanics re-expressed against this backend's carrier. Each SPEC case is
# a FULL Solution.lean variant that shares the FROZEN spec byte-for-byte (only the
# impl region — and, where a positive reproves, the proof body — is edited), checked
# by variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a self-contained snippet that ELABORATES against the rival
# and FAILS on the frozen solution, so the rejection is attributable to the spec and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# Defended surface (read from Solution.lean / mapping.md / instance.json):
#   ensureSupportedVersion : List Nat → List Char → Except (List Char) Unit
#   A runtime is described by two inputs: its numeric version components
#   (`versionInfo : List Nat`) and its version display string (`versionStr :
#   List Char`). The single postcondition `problem_spec_ensureSupportedVersion`
#   pins BOTH branches of a decision AND the payload on the reject branch:
#     (C1) DECISION: the result is the configuration error iff the version
#          components are strictly below the required minimum `requiredMin`
#          ([3,9,0]), under the lexicographic prefix order `versionLt`; otherwise
#          the result is the normal (ok) return. Both directions are pinned — no
#          slack: a rival that misclassifies ANY input on EITHER side fails C1.
#     (C2) MESSAGE PAYLOAD: on the reject branch the error carries exactly
#          `errorMessage versionStr` — the constant prefix/suffix with the
#          runtime's OWN version string substituted in. A rival that rejects the
#          right inputs but reports the wrong string fails C2.
#   versionLt and errorMessage are total, transparent folds over the input (no
#   opaque callee, no answer-key), so witnesses need no conditioning on the
#   carrier — `simp`+`decide` reduce them at any literal input.
#
# CARRIER NOTE / relation to the nagini sibling: nagini modeled ONLY the
# raise-vs-return control-flow fork behind fractional read permission (its
# lt_lex decision over a PSeq); it did not model the raised message text. This
# backend models the richer object directly — `Except (List Char) Unit`, whose
# error payload is `errorMessage versionStr`. So nagini's decision rivals
# (`weak-always-accept`, `weak-always-reject`, `weak-major-only`, `weak-prepatch`)
# port onto clause C1 here, and the extra structure (the version-string-bearing
# message) is ADDITIONALLY attackable via clause C2 — a binder (`versionStr`) the
# nagini carrier had no counterpart for. Every reject witness therefore probes a
# distinct (versionInfo, versionStr) point so both spec binders are exercised.
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's MANDATORY `_FRAME_MUT`: `version` was
#     Acc(list_pred(version),1/2) read-only and the rival wrote back into it).
#     Lean is referentially transparent — no aliasing, no fractional permission —
#     so a "store into a read-only input" rival is not expressible and the whole
#     lane is VACUOUS here. See 'assessment'.
#   * DIVERGENCE / NON-TERMINATION (nagini's `weak-diverge-reject`, rejected there
#     by MustTerminate(2)). On lean `implementation_ensureSupportedVersion` is a
#     total Lean `def`; a non-terminating implementation cannot be written at all,
#     so the class is genuinely VACUOUS here (NOT a known spec hole — that
#     disposition is the velvet-partial one). See 'assessment'.
#   * (ADMISSIBILITY DOES port — see `admiss-f2p-point` below. The lane was
#     originally dropped here on the ground that the lean obligation carries no
#     precondition hypothesis, so nothing could be PRECOND-TOO-STRONG. That
#     reason is wrong: the analogue on a TOTAL carrier is the obligation being
#     unsatisfiable at exactly an F2P-shaped input, which a positive that
#     discharges the obligation at that concrete input by EVALUATION — as a
#     `have`, before closing the frozen obligation verbatim — tests directly.)
#   * AXIOM_TESTS (nagini's `ax-sound-lt_lex` / `ax-cover-lt_lex`). The axiom lane
#     is G-AX's job; this gate ignores them. The ordering is modeled DEEPLY
#     (versionLt), so there is no consumed axiom here anyway.
from pathlib import Path

INSTANCE = "django__django-13821"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------------
# The full frozen impl body, lying ENTIRELY inside impl-start/impl-end and unique in
# the file. Every rival (and the positives) swap THIS block.
_IMPL = (
    "def implementation_ensureSupportedVersion (versionInfo : List Nat) (versionStr : List Char) :\n"
    "    Except (List Char) Unit := Id.run do\n"
    "  if versionLt versionInfo requiredMin then\n"
    "    return Except.error (errorMessage versionStr)\n"
    "  return Except.ok ()"
)
assert _BASE.count(_IMPL) == 1, "impl anchor drifted from expected text"

# The frozen proof body (tactic lines inside proof-start/proof-end). Swapped only by
# the pure-if-expression positive, whose different impl shape needs an (equally cheap,
# honest) reproof of the byte-identical theorem statement.
_PROOF = (
    "  intro versionInfo versionStr\n"
    "  unfold problem_spec_ensureSupportedVersion implementation_ensureSupportedVersion\n"
    "  by_cases h : versionLt versionInfo requiredMin <;>\n"
    "    simp only [h, Id.run, if_true] <;> rfl"
)
assert _BASE.count(_PROOF) == 1, "proof anchor drifted from expected text"


# ===========================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY (else SPEC-TOO-STRONG).
# ===========================================================================

# pos-let-bound-decision: structurally-DIFFERENT but behaviourally identical. The
# decision is bound to a local `below` before the branch; the branch bodies and the
# result are otherwise unchanged, so the output equals the frozen impl's on every
# input. The frozen `theorem correct_ensureSupportedVersion` statement is kept
# byte-identical AND the frozen proof body still closes (the `let` binding is
# definitionally transparent). No reproof, no new axiom/lemma/sorry. If it FAILS =>
# SPEC-TOO-STRONG (postcondition over-fit to one syntactic impl shape).
_POS_LET = _swap(
    _BASE,
    _IMPL,
    "def implementation_ensureSupportedVersion (versionInfo : List Nat) (versionStr : List Char) :\n"
    "    Except (List Char) Unit := Id.run do\n"
    "  let below := versionLt versionInfo requiredMin\n"
    "  if below then\n"
    "    return Except.error (errorMessage versionStr)\n"
    "  return Except.ok ()",
)

# pos-pure-if-expression: a structurally different CORRECT impl written as a pure
# `if`-expression (no `Id.run do` monad, no early `return`), directly returning the
# `Except`. Semantics identical. The theorem STATEMENT is byte-identical; its proof is
# reproven honestly (`split <;> rfl`) inside proof-start/proof-end — no new
# axiom/lemma/sorry, just the cheapest tactic for the new shape. If it FAILS =>
# SPEC-TOO-STRONG (the postcondition is bound to the monadic impl shape).
_POS_PURE = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_ensureSupportedVersion (versionInfo : List Nat) (versionStr : List Char) :\n"
        "    Except (List Char) Unit :=\n"
        "  if versionLt versionInfo requiredMin then\n"
        "    Except.error (errorMessage versionStr)\n"
        "  else\n"
        "    Except.ok ()",
    ),
    _PROOF,
    "  intro versionInfo versionStr\n"
    "  unfold problem_spec_ensureSupportedVersion implementation_ensureSupportedVersion\n"
    "  split <;> rfl",
)


# admiss-f2p-point: the ADMISSIBILITY positive. The frozen obligation carries no
# precondition hypothesis, so PRECOND-TOO-STRONG cannot arrive as a rejected
# `Requires`; on a total carrier the analogue is the obligation being UNSATISFIABLE
# at exactly an F2P-shaped input. This positive tests that directly: the impl is the
# frozen one, and the proof first discharges the obligation AT the F2P-shaped point
# ([3,8,11,1] with its matching display string) by pure evaluation, as a `have`, and
# only then closes the frozen obligation verbatim with the frozen tactic body. If the
# spec were unsatisfiable there — an over-strong demand at the very input the
# regression test pins — the `have` could not be discharged by evaluation and this
# case would FAIL while the plain positives still passed. No new axiom/lemma/sorry:
# the `have` is proved, and the frozen theorem statement is byte-identical.
_ADMISS_F2P = _swap(
    _BASE,
    _PROOF,
    "  have hF2P : problem_spec_ensureSupportedVersion [3, 8, 11, 1]\n"
    "      ['3', '.', '8', '.', '1', '1', '.', '1']\n"
    "      (implementation_ensureSupportedVersion [3, 8, 11, 1]\n"
    "        ['3', '.', '8', '.', '1', '1', '.', '1']) := by\n"
    "    unfold problem_spec_ensureSupportedVersion implementation_ensureSupportedVersion\n"
    "    simp [versionLt, requiredMin, errorMessage, Id.run, pure, bind, Id.instMonad]\n"
    + _PROOF,
)

# pos-negated-guard: a CORRECT reshape that inverts the guard and SWAPS the branch
# bodies (`if !below then ok else error`) — the accept case is now the taken branch.
# Behaviourally identical on every input, but neither the branch order nor the guard
# polarity matches the frozen impl, so it is the sharpest available check that the
# postcondition pins BEHAVIOUR and not the frozen impl's branch layout. Reproven with
# `cases h : … <;> simp [h, …]`; statement byte-identical. Found by attack E during the
# audit (a first attempt with the short simp set failed on a residual `pure` — a
# tactic gap, not a spec hole; retried with the monad lemmas and it closes).
_POS_NEG = _swap(
    _swap(
        _BASE,
        _IMPL,
        "def implementation_ensureSupportedVersion (versionInfo : List Nat) (versionStr : List Char) :\n"
        "    Except (List Char) Unit := Id.run do\n"
        "  if !(versionLt versionInfo requiredMin) then\n"
        "    return Except.ok ()\n"
        "  return Except.error (errorMessage versionStr)",
    ),
    _PROOF,
    "  intro versionInfo versionStr\n"
    "  unfold problem_spec_ensureSupportedVersion implementation_ensureSupportedVersion\n"
    "  cases h : versionLt versionInfo requiredMin <;>\n"
    "    simp [h, Id.run, pure, bind, Id.instMonad]",
)


# ===========================================================================
# UNIQUENESS RIVALS — must be REJECTED (else SPEC-TOO-WEAK). Each shares the
# frozen spec exactly and edits only the impl region; the frozen proof body is left
# in place (it will not close for the reshaped impl, but the gate reads the witness —
# checked in a file with the obligation removed — not the rival's own build).
# ===========================================================================

# weak-always-accept: never rejects — always takes the ok return (the control-flow
# fork is removed on the reject side). PARTIAL-DOMAIN / CONTROL-FLOW: correct on every
# at-or-above runtime, WRONG on every strictly-below one.
_RIV_ACCEPT = _swap(
    _BASE,
    _IMPL,
    "def implementation_ensureSupportedVersion (versionInfo : List Nat) (versionStr : List Char) :\n"
    "    Except (List Char) Unit := Id.run do\n"
    "  return Except.ok ()",
)

# weak-always-reject: always rejects — every runtime takes the error path (the dual;
# the ok fork is removed). It even carries the RIGHT message string, so only clause C1
# (the decision) refutes it, on an at-or-above runtime.
_RIV_REJECT = _swap(
    _BASE,
    _IMPL,
    "def implementation_ensureSupportedVersion (versionInfo : List Nat) (versionStr : List Char) :\n"
    "    Except (List Char) Unit := Id.run do\n"
    "  return Except.error (errorMessage versionStr)",
)

# weak-major-only: PARTIAL-DOMAIN. Decides from the MAJOR component alone (reject iff
# empty, or first component < 3). Correct on the major-version sub-domain — a 2.x
# runtime rejected, a 4.x accepted — but ALWAYS accepts any 3.x runtime, so it is
# WRONG on the minor/patch boundary the fix introduces.
_RIV_MAJOR = _swap(
    _BASE,
    _IMPL,
    "def implementation_ensureSupportedVersion (versionInfo : List Nat) (versionStr : List Char) :\n"
    "    Except (List Char) Unit := Id.run do\n"
    "  match versionInfo with\n"
    "  | [] => return Except.error (errorMessage versionStr)\n"
    "  | h :: _ =>\n"
    "      if h < 3 then\n"
    "        return Except.error (errorMessage versionStr)\n"
    "      return Except.ok ()",
)

# weak-prepatch: the EXACT pre-patch threshold — compares against the OLD minimum
# [3,8,3] instead of requiredMin [3,9,0]. This is the literal pre-patch behaviour; it
# accepts runtimes in the [3.8.3, 3.9.0) band the fix now rejects.
_RIV_PREPATCH = _swap(
    _BASE,
    _IMPL,
    "def implementation_ensureSupportedVersion (versionInfo : List Nat) (versionStr : List Char) :\n"
    "    Except (List Char) Unit := Id.run do\n"
    "  if versionLt versionInfo [3, 8, 3] then\n"
    "    return Except.error (errorMessage versionStr)\n"
    "  return Except.ok ()",
)

# weak-wrong-message: makes the RIGHT decision on every input (clause C1 holds) but on
# the reject branch reports the constant message with an EMPTY version string instead
# of substituting the runtime's own `versionStr`. Attacks clause C2 (the payload) —
# the binder the nagini carrier never modeled.
_RIV_MSG = _swap(
    _BASE,
    _IMPL,
    "def implementation_ensureSupportedVersion (versionInfo : List Nat) (versionStr : List Char) :\n"
    "    Except (List Char) Unit := Id.run do\n"
    "  if versionLt versionInfo requiredMin then\n"
    "    return Except.error (errorMessage [])\n"
    "  return Except.ok ()",
)


# weak-prefix-pad: attacks the PREFIX RULE of the lexicographic order, the one part of
# clause C1 no other rival here touches. It zero-pads the version components before
# comparing, so a SHORT tuple that is a strict prefix of the minimum (e.g. two
# components `3.9`) compares as `3.9.0.0.0`-ish and is judged at-or-above, where the
# spec's order makes a strict prefix strictly SMALLER than its extension and demands
# the error. Correct on every full-length tuple; wrong exactly on the short ones.
# Added by the audit: attack D wrote it as a NEW wrong impl, confirmed the frozen spec
# does reject it, and kept it as a rival because the sub-domain was unprobed.
_RIV_PREFIX = _swap(
    _BASE,
    _IMPL,
    "def implementation_ensureSupportedVersion (versionInfo : List Nat) (versionStr : List Char) :\n"
    "    Except (List Char) Unit := Id.run do\n"
    "  if versionLt (versionInfo ++ [0, 0, 0]) requiredMin then\n"
    "    return Except.error (errorMessage versionStr)\n"
    "  return Except.ok ()",
)


def _wit(vi, vs, note):
    """A refutation witness: `¬ problem_spec … (implementation …)` at a concrete
    literal (versionInfo, versionStr). The simp set reduces versionLt/errorMessage
    AND the `Id` monad scaffolding all the way down, so the goal becomes a decidable
    equation between closed `Except (List Char) Unit` values, which simp then closes.

    `bind, Id.instMonad` are load-bearing, NOT decoration. Without them a rival
    whose impl body is a bare `return e` leaves the residual do-block
    `(do PUnit.unit; Except.ok ()) = Except.ok ()` unreduced on the GOLD side, and
    that build then fails for a reason that has nothing to do with what the witness
    claims: the FLIPPED claim (asserting gold is CORRECT at that point) fails with
    the byte-identical unreduced term, so gold's exit code carries no information
    and the case is hollow. Measured with four real builds on the at-boundary point
    [3,9,0]: with the short simp set, witness-on-gold exit 1 and flipped-on-gold
    exit 1 (same `⊢ ¬(do PUnit.unit; Except.ok ()) = Except.ok ()`); with `bind,
    Id.instMonad` added, witness-on-gold exit 1 with `⊢ False` and flipped-on-gold
    exit 0. Only the second pair is a refutation that TRACKS the claim.

    Verified for every point below: elaborates against the rival (exit 0), fails on
    gold with `⊢ False` (exit 1), and the flipped claim BUILDS on gold (exit 0)."""
    return (
        f"-- {note}\n"
        f"example : ¬ problem_spec_ensureSupportedVersion {vi} {vs}\n"
        f"    (implementation_ensureSupportedVersion {vi} {vs}) := by\n"
        f"  unfold problem_spec_ensureSupportedVersion implementation_ensureSupportedVersion\n"
        f"  simp [versionLt, requiredMin, errorMessage, Id.run, pure, bind, Id.instMonad]"
    )


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {
        "id": "pos-let-bound-decision",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LET,
        "rationale": (
            "structurally-different but CORRECT impl: the decision is bound to a local "
            "`below` before the branch, keeping both branch bodies and the result, so the "
            "output equals the frozen impl's on every input. The theorem statement is "
            "byte-identical and the FROZEN proof body still closes (the let binding is "
            "definitionally transparent) — a faithful restructure with no reproof and no "
            "new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG (postcondition over-fit "
            "to one syntactic impl shape)."
        ),
    },
    {
        "id": "pos-pure-if-expression",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_PURE,
        "rationale": (
            "a structurally different CORRECT impl written as a pure `if`-expression (no "
            "`Id.run do`, no early return), directly returning the Except. Semantics "
            "identical on every input. The theorem STATEMENT is byte-identical; its proof "
            "is reproven honestly with `split <;> rfl` — no new axiom/lemma/sorry, just "
            "the cheapest tactic for the new shape. If it FAILS => SPEC-TOO-STRONG (the "
            "postcondition is bound to the monadic impl shape rather than the behaviour)."
        ),
    },

    {
        "id": "pos-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_NEG,
        "rationale": (
            "a CORRECT reshape that inverts the guard polarity AND swaps the branch "
            "bodies (`if !below then ok else error`), so the accept case becomes the taken "
            "branch — behaviourally identical on every input while matching neither the "
            "branch order nor the guard polarity of the frozen impl. This is the sharpest "
            "check here that the postcondition pins BEHAVIOUR rather than the frozen impl's "
            "branch layout. Statement byte-identical; reproven with `cases h : … <;> simp "
            "[h, …]`, no new axiom/lemma/sorry. If it FAILS => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-f2p-point",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS_F2P,
        "rationale": (
            "ADMISSIBILITY on a total carrier. The frozen obligation has no precondition "
            "hypothesis, so PRECOND-TOO-STRONG cannot show up as a rejected `Requires`; "
            "the analogue is the obligation being UNSATISFIABLE at exactly an F2P-shaped "
            "input. This case tests that directly: the impl is the frozen one, and the "
            "proof first discharges the obligation AT the F2P-shaped point — the "
            "below-minimum runtime the regression test pins, with its matching display "
            "string — by pure EVALUATION as a `have`, then closes the frozen obligation "
            "verbatim with the frozen tactic body. If the spec demanded something "
            "unsatisfiable at that concrete input, the `have` could not be discharged by "
            "evaluation and this case would FAIL while the plain positives still passed. "
            "If it FAILS => PRECOND-TOO-STRONG / the pinned input is not admissible."
        ),
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "weak-always-accept",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_ACCEPT,
        "refinement": (
            "always returning the ok result is what a real patch that DELETED the guard "
            "(or its raise) would do — it never rejects any runtime, so an embedded engine "
            "older than the required minimum passes start-up. It fails the F2P test, which "
            "pins a below-minimum runtime ((3,8,11,1)) and asserts the configuration error "
            "IS raised. A faithful patch of this shape does NOT resolve; a verifying rival "
            "is a true verify-does-not-imply-resolve break."
        ),
        "rationale": (
            "REJECTED by clause C1 (the decision). On a strictly-below runtime the spec "
            "demands the error result, but the rival returns ok. Witness probes the "
            "below-minimum sub-domain (versionInfo below requiredMin). If it VERIFIES => "
            "SPEC-TOO-WEAK (the reject direction is unpinned)."
        ),
        # [3,8,11,1] is below [3,9,0]: gold -> error; rival -> ok.
        "witness": _wit("[3, 8, 11, 1]", "['3', '.', '8', '.', '1', '1', '.', '1']",
                        "below-minimum runtime: gold rejects, rival accepts"),
    },
    {
        "id": "weak-always-reject",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_REJECT,
        "refinement": (
            "always rejecting is what a real patch that hard-coded the guard true (or "
            "compared against an impossibly-high minimum) would do — it rejects EVERY "
            "runtime, including the modern engines the project supports, so every "
            "start-up path that must return normally on an in-spec runtime breaks. It "
            "carries the correct message string, so the defect is purely the decision. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1 (the decision, dual direction). On an at-or-above "
            "runtime the spec demands the ok result, but the rival returns the error. "
            "Witness probes the AT-BOUNDARY sub-domain (versionInfo == requiredMin), the "
            "exact accept edge. If it VERIFIES => SPEC-TOO-WEAK (the accept direction is "
            "unpinned)."
        ),
        # [3,9,0] == requiredMin, not below: gold -> ok; rival -> error.
        "witness": _wit("[3, 9, 0]", "['3', '.', '9', '.', '0']",
                        "at-boundary runtime: gold accepts, rival rejects"),
    },
    {
        "id": "weak-major-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_MAJOR,
        "refinement": (
            "comparing only the MAJOR component to 3 is what a real patch that wrote "
            "`if version_info[0] < 3:` would do. It is correct on the major-version "
            "sub-domain (a 2.x runtime rejected, a 4.x accepted) but ALWAYS accepts any "
            "3.x runtime, so it does NOT reject a below-minimum 3.x runtime — the exact "
            "F2P discriminator. It fails the F2P test; a genuine PARTIAL-DOMAIN break on "
            "the minor-version boundary. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1. For a 3.x runtime below requiredMin the rival returns "
            "ok (major==3, not <3) but the spec demands the error. Witness probes the "
            "minor/patch sub-domain the major-only decision drops (versionInfo shares the "
            "major component with requiredMin but is below it). If it VERIFIES => "
            "SPEC-TOO-WEAK on the minor-version sub-domain."
        ),
        # [3,8,7]: major 3 (rival accepts) but below [3,9,0] (gold rejects).
        "witness": _wit("[3, 8, 7]", "['3', '.', '8', '.', '7']",
                        "below-minimum 3.x runtime: gold rejects, major-only rival accepts"),
    },
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PREPATCH,
        "refinement": (
            "this IS the pre-patch behaviour: the original guard compares against the OLD "
            "minimum [3,8,3] instead of [3,9,0]. Its faithful real patch is the UNCHANGED "
            "repo, which ACCEPTS a runtime in the [old-min, new-min) band (>= 3.8.3 — "
            "exactly the bug the fix corrects) and so does NOT reject it. It fails the F2P "
            "test (now asserts the rejection). Does NOT resolve — the precise threshold "
            "bump the spec senses. Supporting near-miss carrying the strongest refinement "
            "(it is the literal pre-patch), probed at a point below the new minimum but "
            "above the old one where it and gold DISAGREE."
        ),
        "rationale": (
            "REJECTED by clause C1. For a runtime in [ [3,8,3], [3,9,0] ) the rival's "
            "decision reflects 'below [3,8,3]' (false -> ok), but the spec demands the "
            "error (it IS below [3,9,0]). Witness sits strictly inside that band, "
            "distinguishing this near-miss from the other decision rivals. If it VERIFIES "
            "=> SPEC-TOO-WEAK (the threshold bump is not enforced)."
        ),
        # [3,8,4]: >= [3,8,3] so rival accepts, but < [3,9,0] so gold rejects.
        "witness": _wit("[3, 8, 4]", "['3', '.', '8', '.', '4']",
                        "in [old-min, new-min) band: gold rejects, pre-patch rival accepts"),
    },
    {
        "id": "weak-wrong-message",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_MSG,
        "refinement": (
            "makes the RIGHT reject/accept decision on every input but reports the "
            "configuration error with an EMPTY version string instead of substituting the "
            "runtime's own display string. Its faithful real patch raises the error with "
            "the wrong (or missing) `found %s` value, so the F2P assertion on the exact "
            "message text (which names the actual runtime version) fails. Does NOT "
            "resolve — a decision-correct impl that still breaks the pinned message."
        ),
        "rationale": (
            "REJECTED by clause C2 (the message payload). On the reject branch the spec "
            "demands `errorMessage versionStr` — the runtime's OWN version string "
            "substituted — but the rival emits `errorMessage []`. Witness varies the "
            "versionStr BINDER at a below-minimum runtime with a NON-EMPTY string, so the "
            "two messages differ. This binder has no nagini counterpart (that carrier did "
            "not model the message). If it VERIFIES => SPEC-TOO-WEAK (the payload is "
            "unpinned)."
        ),
        # [3,8] below min with versionStr ['3','.','8']: gold error carries "3.8",
        # rival carries the empty string -> messages differ.
        "witness": _wit("[3, 8]", "['3', '.', '8']",
                        "below-minimum runtime, non-empty version string: gold substitutes "
                        "it into the message, rival drops it"),
    },
    {
        "id": "weak-prefix-pad",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_PREFIX,
        "refinement": (
            "zero-padding the version components before the comparison is what a real "
            "patch that normalised the tuple to a fixed width would do. It is correct on "
            "every full-length tuple, so it passes the ordinary cases, but it mis-orders "
            "the SHORT ones: a runtime reporting only two components that is a strict "
            "prefix of the minimum is judged at-or-above and accepted, where the spec's "
            "order makes a strict prefix strictly smaller and demands the error. A "
            "faithful patch of this shape lets a short-version runtime through start-up. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by clause C1, specifically the PREFIX RULE of the lexicographic "
            "order — the one part of the decision no other rival here attacks (the others "
            "all vary the threshold or the component compared, never the length rule). "
            "Witness probes a strict-prefix runtime: the spec orders it below the minimum "
            "and demands the error, the padded rival accepts. If it VERIFIES => "
            "SPEC-TOO-WEAK on the short-tuple sub-domain."
        ),
        # [3,9] is a strict prefix of [3,9,0] so it IS below it: gold -> error;
        # padded rival compares [3,9,0,0,0] -> not below -> ok.
        "witness": _wit("[3, 9]", "['3', '.', '9']",
                        "strict-prefix runtime: gold rejects (prefix is smaller), "
                        "zero-padding rival accepts"),
    },
]


# No @ContractOnly axioms and no opaque callees: the lexicographic decision (versionLt)
# and the message formatting (errorMessage) are modeled DEEPLY over transparent
# carriers, so the axiom lane is vacuous here and belongs to G-AX regardless.
AXIOM_TESTS = []
