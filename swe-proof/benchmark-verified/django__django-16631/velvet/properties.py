# properties.py — G-PBT falsification battery for django__django-16631 (velvet).
#
# NOT a Lean file; a manifest the G-PBT runner parses. Each SPEC_TESTS case is a
# FULL Solution.lean variant that shares the frozen spec byte-for-byte
# (markers.same_spec) and edits ONLY the impl region and, where a reshaped impl
# needs it, the elided `prove_correct` tactic body. The `prove_correct
# resolveSessionPrincipal` header survives in every case, and no case introduces
# an axiom / sorry / admit / native_decide / helper lemma — so a rejection is
# attributable to the postcondition, never to a neutered obligation.
#
# DEFENDED SURFACE (read Solution.lean)
#   resolveSessionPrincipal (storedCred : Option Cred) (currentCred : Cred)
#                           (priorCreds : List Cred) -> (out : SessionVerify)
#     no `require` clause: every input triple is admissible, so no witness can be
#       vacuously excluded by a false precondition.
#     one obligation, one clause:
#       ensures out = verifyDecision storedCred currentCred priorCreds
#     `verifyDecision` decides four independent legs, and the single equation
#     above pins BOTH observables (`principalKept : Bool` and
#     `action : SessionAction`) on each of them:
#       L1  storedCred = none                       -> (false, reject)
#       L2  some h, h = currentCred                 -> (true,  valid)
#       L3  some h, h != currentCred, h in prior    -> (true,  acceptedPrior)
#       L4  some h, h != currentCred, h not in prior-> (false, reject)
#     The leg PRIORITY is load-bearing: L2 is tested before L3, so a retained
#     credential matching the current secret is classified `valid` even when it
#     also occurs among the prior-secret credentials.
#     L3's membership is positional-agnostic: `contains` is a match at ANY index,
#     so the prior-secret search must be exhaustive, not head-only.
#
# WHAT THE `refinement` PROSE BELOW DOES AND DOES NOT CLAIM (audit lane)
#   Most of these rivals are NOT caught by the shipped test suite. Traced by hand
#   against the listed tests: the sole F2P drives two calls, whose prior lists are
#   (one prior secret, retained credential matching it) and (empty); the only
#   listed test that reaches the decision otherwise presents a retained
#   credential matching the current secret with no prior secrets configured; and
#   the listed no-credential case never LOCATES a principal, so the decision is
#   not entered on it at all. Consequently the `none` leg (L1), the unrecognised
#   leg (L4), the leg-priority overlap, the excluded value sub-domain, and any
#   non-head prior position are ALL test-unreachable. Each such refinement below
#   says so in a "Scope of the claim, stated exactly" sentence rather than
#   asserting a test failure it cannot demonstrate. That is the point of the
#   battery, not a weakness in it: the guarantee is verified => correct, so the
#   spec must pin behaviour on inputs the shipped assertions never present.
#
# Carrier note: `Cred := Nat` with decidable equality, `SessionVerify` and
# `SessionAction` both `deriving DecidableEq`. Nothing here is `opaque`, so every
# witness states its refutation at CONCRETE literal inputs and `decide` reduces
# it — no witness binds a hypothesis, hence none can be inconsistent.
#
# LANES. This battery carries all three directions the gate exists to test:
# soundness (a correct reshape must verify — else SPEC-TOO-STRONG), uniqueness (a
# wrong rival must be rejected, each with a witness seen to discriminate — else
# SPEC-TOO-WEAK), and admissibility (the obligation must be satisfiable and
# non-degenerate at an F2P-shaped input — else PRECOND-TOO-STRONG). The
# admissibility case is re-aimed rather than omitted: the frozen method has no
# `require` clause, so the literal "a normal input satisfies the precondition"
# probe is vacuous, and the meaningful analogue on a total carrier is
# satisfiability + non-degeneracy of the post-image at the concrete corners the
# fix turns on. See the ADMISSIBILITY block below.
from pathlib import Path

INSTANCE = "django__django-16631"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen anchors. `_IMPL` is the whole text strictly between `-- impl-start` and
# `-- impl-end`; `_PROOF` is the whole `prove_correct` block. Both lie WHOLLY
# inside a region the consumer spec view elides, and both are unique in _BASE
# (asserted by _swap at import), so every variant below edits only those regions
# and the manifest breaks loudly if the frozen solution ever drifts.
# ---------------------------------------------------------------------------
_IMPL = """    match storedCred with
    | none   => return { principalKept := false, action := SessionAction.reject }
    | some h =>
      if h = currentCred then
        return { principalKept := true, action := SessionAction.valid }
      else
        if priorCreds.contains h then
          return { principalKept := true, action := SessionAction.acceptedPrior }
        else
          return { principalKept := false, action := SessionAction.reject }"""

_PROOF = """prove_correct resolveSessionPrincipal by
  loom_solve <;> simp_all [verifyDecision]"""


def _impl(body):
    """Full Solution.lean variant, ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, body)


def _impl_proof(body, proof):
    """Impl body replaced AND the tactic body retuned. The `prove_correct
    resolveSessionPrincipal` header is preserved verbatim, so the obligation
    survives with an identical statement; only the elided proof body differs."""
    return _swap(_impl(body), _PROOF, proof)


# ---------------------------------------------------------------------------
# Witness preamble. The spec is a `method` CONTRACT, not a bare predicate, so a
# witness reaches the post-image through Velvet's own tester machinery:
# `resolveSessionPrincipalTester storedCred currentCred priorCreds = false` says
# the extracted program's observable VIOLATES the method's postcondition at that
# concrete input. Checked in a file whose `prove_correct` block has been
# stripped, so no tactic script can mask the verdict.
#
# Each witness below was run BOTH ways before shipping: it elaborates against
# its rival (exit 0) and fails against the frozen solution with
# `Tactic 'decide' proved that the proposition ... is false` — i.e. gold
# satisfies the postcondition at that point, which is the discrimination the two
# halves are supposed to demonstrate.
# ---------------------------------------------------------------------------
def _witness(stored, current, priors):
    return ("extract_program_for resolveSessionPrincipal\n"
            "prove_precondition_decidable_for resolveSessionPrincipal\n"
            "prove_postcondition_decidable_for resolveSessionPrincipal\n"
            "derive_tester_for resolveSessionPrincipal\n\n"
            f"example : resolveSessionPrincipalTester {stored} {current} "
            f"{priors} = false := by\n  decide\n")


# ===========================================================================
# ADMISSIBILITY — the frozen method carries NO `require` clause, so the nagini
# sibling's probe ("a normal F2P-shaped input satisfies the precondition") is
# vacuous as stated: nothing could exclude an in-domain input. That is NOT a
# reason to drop the lane, because the analogue on a TOTAL carrier is the
# residual risk the lane actually exists to catch — that the obligation is
# UNSATISFIABLE, or satisfied only degenerately, at exactly an F2P-shaped input.
# This case discharges that by EVALUATION, as a live in-region `assert`, at the
# two concrete corners the fix turns on, before closing the frozen obligation
# verbatim:
#   * the prior-secret corner (a retained credential mismatching the current
#     secret but present among the priors) really does reach
#     (principalKept = true, action = acceptedPrior) — the post-image is
#     inhabited at the interesting point, not empty there;
#   * the current-secret corner with NO prior secrets configured really does
#     reach (true, valid);
#   * and the third conjunct pins NON-DEGENERACY: the two calls that differ only
#     in whether the prior list contains the retained credential land on
#     DIFFERENT outcomes, so the prior-secret input genuinely participates in
#     the decision rather than being ignored by a spec that could be satisfied
#     without reading it.
# The impl and the frozen tactic body are kept verbatim, so `out =
# verifyDecision ...` still discharges on its own; the assert only adds goals.
# The assert is LIVE, confirmed out-of-band rather than assumed: replacing the
# first conjunct's outcome with the wrong one, and separately flipping the
# non-degeneracy `≠` to `=`, each leave `unsolved goals` at the assert (exit 1).
# So this case cannot pass by the assert being ignored.
# ===========================================================================
_ADMISS = """    assert (with_name_prefix `adm
      (verifyDecision (some 7) 1 [7]
          = { principalKept := true, action := SessionAction.acceptedPrior }
       ∧ verifyDecision (some 6) 6 []
          = { principalKept := true, action := SessionAction.valid }
       ∧ verifyDecision (some 7) 1 [7] ≠ verifyDecision (some 7) 1 []))
""" + _IMPL


# ===========================================================================
# SOUNDNESS POSITIVES — structurally different CORRECT impls (must verify).
# If any of these were rejected the spec would be TOO STRONG: it would be
# pinning an incidental shape of the frozen impl rather than its behaviour.
# ===========================================================================

# Reorders the decision so the prior-secret leg is tested FIRST, made correct by
# carrying the `h != currentCred` side condition explicitly into its guard. Same
# four-way function, opposite branch order. Closes under the frozen tactic body.
_POS_GUARDED = """    match storedCred with
    | none   => return { principalKept := false, action := SessionAction.reject }
    | some h =>
      if h != currentCred && priorCreds.contains h then
        return { principalKept := true, action := SessionAction.acceptedPrior }
      else
        if h = currentCred then
          return { principalKept := true, action := SessionAction.valid }
        else
          return { principalKept := false, action := SessionAction.reject }"""

# Computes the classification into a local FIRST, then DERIVES the survival
# observable from it (`act != reject`) instead of writing the two fields
# independently on each leg. This reshapes the data flow rather than the control
# flow, and it needs a real case split, so the elided tactic body is retuned
# (`split_ifs`) with the obligation statement untouched.
_POS_DERIVED = """    match storedCred with
    | none   => return { principalKept := false, action := SessionAction.reject }
    | some h =>
      let act := if h = currentCred then SessionAction.valid
                 else if priorCreds.contains h then SessionAction.acceptedPrior
                 else SessionAction.reject
      return { principalKept := act != SessionAction.reject, action := act }"""

_POS_DERIVED_PROOF = ("prove_correct resolveSessionPrincipal by\n"
                      "  loom_solve <;> simp_all [verifyDecision] "
                      "<;> split_ifs <;> simp_all")

# Replaces the membership test with an explicit existential search over the
# prior-secret credentials — a different traversal of the same list input,
# reaching the same predicate. Closes under the frozen tactic body.
_POS_ELEM = """    match storedCred with
    | none   => return { principalKept := false, action := SessionAction.reject }
    | some h =>
      if h = currentCred then
        return { principalKept := true, action := SessionAction.valid }
      else
        if priorCreds.any (fun p => p = h) then
          return { principalKept := true, action := SessionAction.acceptedPrior }
        else
          return { principalKept := false, action := SessionAction.reject }"""


# ===========================================================================
# UNIQUENESS RIVALS — reasoned WRONG impls (must reject), each with a witness
# seen to discriminate.
# ===========================================================================

# L3 deleted outright: a retained credential that does not match the current
# secret drops the principal, whatever the prior secrets say.
_NO_PRIOR = """    match storedCred with
    | none   => return { principalKept := false, action := SessionAction.reject }
    | some h =>
      if h = currentCred then
        return { principalKept := true, action := SessionAction.valid }
      else
        return { principalKept := false, action := SessionAction.reject }"""

# Leg PRIORITY inverted with NO compensating side condition: the prior-secret
# leg is tested before the current-secret one, so a credential valid under the
# current secret that ALSO occurs among the prior ones is classified
# `acceptedPrior` where the spec demands `valid`. Attacks L2 only — it agrees
# with gold on L1/L3/L4 — so it gets its own witness at the overlap point.
_PRIOR_FIRST = """    match storedCred with
    | none   => return { principalKept := false, action := SessionAction.reject }
    | some h =>
      if priorCreds.contains h then
        return { principalKept := true, action := SessionAction.acceptedPrior }
      else
        if h = currentCred then
          return { principalKept := true, action := SessionAction.valid }
        else
          return { principalKept := false, action := SessionAction.reject }"""

# L3 restricted to a value SUB-DOMAIN of the credential carrier: the
# prior-secret path is refused for one particular retained-credential value,
# which falls through to `reject`. A near-miss that agrees with gold everywhere
# else, so its witness sits exactly on the excluded value.
_PARTIAL_PRIOR = """    match storedCred with
    | none   => return { principalKept := false, action := SessionAction.reject }
    | some h =>
      if h = currentCred then
        return { principalKept := true, action := SessionAction.valid }
      else
        if h != 0 && priorCreds.contains h then
          return { principalKept := true, action := SessionAction.acceptedPrior }
        else
          return { principalKept := false, action := SessionAction.reject }"""

# Keeps the principal on L3 (so `principalKept` is right) but mis-CLASSIFIES the
# credential as `valid` rather than `acceptedPrior`. Attacks the `action`
# component of L3 in isolation, holding `principalKept` at gold's value — the
# rival a battery that only ever checked survival would miss.
_TAGGED_VALID = """    match storedCred with
    | none   => return { principalKept := false, action := SessionAction.reject }
    | some h =>
      if h = currentCred then
        return { principalKept := true, action := SessionAction.valid }
      else
        if priorCreds.contains h then
          return { principalKept := true, action := SessionAction.valid }
        else
          return { principalKept := false, action := SessionAction.reject }"""

# L1 flipped: an ABSENT retained credential keeps the principal and reports it
# verified. The only rival that moves `storedCred` off `some`, which is what
# makes that binder discriminated rather than merely present.
_NONE_KEPT = """    match storedCred with
    | none   => return { principalKept := true, action := SessionAction.valid }
    | some h =>
      if h = currentCred then
        return { principalKept := true, action := SessionAction.valid }
      else
        if priorCreds.contains h then
          return { principalKept := true, action := SessionAction.acceptedPrior }
        else
          return { principalKept := false, action := SessionAction.reject }"""

# The current-secret leg deleted instead: classification consults ONLY the
# prior-secret credentials, so a credential matching the current secret is
# `acceptedPrior` when it happens to appear among the priors and `reject`
# otherwise. Its witness has an EMPTY prior list, so the refutation cannot be
# blamed on the overlap that _PRIOR_FIRST exploits.
_IGNORE_CURRENT = """    match storedCred with
    | none   => return { principalKept := false, action := SessionAction.reject }
    | some h =>
      if priorCreds.contains h then
        return { principalKept := true, action := SessionAction.acceptedPrior }
      else
        return { principalKept := false, action := SessionAction.reject }"""

# L3 restricted to the FIRST prior-secret credential: the retained credential is
# compared only against the head of the prior list, so a match at any later
# position falls through to `reject`. Attacks the list binder POSITIONALLY —
# every other rival either consults the whole list or none of it, so none of them
# forces the traversal to be exhaustive. Added by the audit lane (attack D):
# rival module exit 1; witness exit 0 against the rival and exit 1 against the
# frozen solution with `Tactic 'decide' proved that the proposition
# resolveSessionPrincipalTester (some 3) 8 [1, 2, 3] = false is false`.
_HEAD_PRIOR_ONLY = """    match storedCred with
    | none   => return { principalKept := false, action := SessionAction.reject }
    | some h =>
      if h = currentCred then
        return { principalKept := true, action := SessionAction.valid }
      else
        if priorCreds.head? = some h then
          return { principalKept := true, action := SessionAction.acceptedPrior }
        else
          return { principalKept := false, action := SessionAction.reject }"""

# L4 collapsed into L3: any present credential that does not match the current
# secret is accepted as a prior-secret one WITHOUT consulting the prior-secret
# list at all. The permissive dual of _NO_PRIOR, and the only rival attacking
# the `not in prior` leg.
_ACCEPT_UNKNOWN = """    match storedCred with
    | none   => return { principalKept := false, action := SessionAction.reject }
    | some h =>
      if h = currentCred then
        return { principalKept := true, action := SessionAction.valid }
      else
        return { principalKept := true, action := SessionAction.acceptedPrior }"""


SPEC_TESTS = [
    # ---- admissibility (must verify) ----
    {"id": "admiss-f2p-corners-nondegenerate", "kind": "admissibility",
     "expect": "verify",
     "module": _impl(_ADMISS),
     "rationale": "the obligation is SATISFIABLE and non-degenerate at the two "
                  "F2P-shaped corners, discharged by evaluation as a live "
                  "in-region assert before the frozen obligation closes "
                  "verbatim. The frozen method has no `require` clause, so the "
                  "sibling's literal precondition probe is vacuous; the analogue "
                  "on a total carrier is that the obligation could be "
                  "unsatisfiable — or satisfiable only trivially — at exactly "
                  "the input the fix turns on. Pins that the prior-secret corner "
                  "(retained credential mismatching the current secret, present "
                  "among the priors) genuinely reaches (true, acceptedPrior); "
                  "that the current-secret corner with an EMPTY prior list "
                  "genuinely reaches (true, valid); and — the non-degeneracy "
                  "conjunct — that two calls differing ONLY in whether the prior "
                  "list contains the retained credential land on DIFFERENT "
                  "outcomes, so the prior-secret input really participates in "
                  "the decision. The assert is live: falsifying the first "
                  "conjunct's outcome, or flipping the non-degeneracy `≠` to "
                  "`=`, each leaves an unsolved goal (checked out-of-band). Impl "
                  "and frozen tactic body kept verbatim."},

    # ---- soundness (must verify) ----
    {"id": "pos-branch-reorder", "kind": "soundness", "expect": "verify",
     "module": _impl(_POS_GUARDED),
     "rationale": "structurally different but behaviourally identical: the "
                  "prior-secret leg is tested FIRST, kept correct by carrying "
                  "the current-secret mismatch into its guard explicitly. The "
                  "same four-way classification with the opposite branch order "
                  "must satisfy `out = verifyDecision storedCred currentCred "
                  "priorCreds`, else the spec is pinning an incidental shape of "
                  "the frozen impl rather than the behaviour (SPEC-TOO-STRONG). "
                  "Frozen tactic body untouched."},
    {"id": "pos-derived-survival", "kind": "soundness", "expect": "verify",
     "module": _impl_proof(_POS_DERIVED, _POS_DERIVED_PROOF),
     "rationale": "reshapes the DATA flow rather than the control flow: the "
                  "classification is computed into a local and the survival "
                  "observable is derived from it, instead of both fields being "
                  "written independently on each leg. Exercises that the single "
                  "`out = verifyDecision ...` equation is satisfiable by an impl "
                  "that does not construct the two components separately. Needs "
                  "a genuine case split, so the ELIDED tactic body is retuned "
                  "with `split_ifs`; the `prove_correct resolveSessionPrincipal` "
                  "header and the obligation statement are byte-identical and no "
                  "helper lemma or assumption is added."},
    {"id": "pos-any-search", "kind": "soundness", "expect": "verify",
     "module": _impl(_POS_ELEM),
     "rationale": "a different TRAVERSAL of the prior-secret list input — an "
                  "explicit existential search rather than the membership test — "
                  "reaching the same predicate. Must verify, else the spec "
                  "constrains how the list is walked instead of what it decides."},

    # ---- uniqueness (must reject; witness seen to discriminate) ----
    {"id": "reject-no-prior-path", "kind": "uniqueness", "expect": "reject",
     "module": _impl(_NO_PRIOR),
     "witness": _witness("(some 7)", "1", "[7]"),
     "refinement": "this is the pre-image behaviour: with no prior-secret "
                   "acceptance path at all, a session established before a "
                   "secret change is dropped and the principal replaced by an "
                   "anonymous one. That is exactly the defect the issue "
                   "reports, so a faithful real patch of this shape leaves the "
                   "single F2P assertion — that the principal survives a secret "
                   "rotation — failing, and does NOT resolve.",
     "rationale": "attacks L3: for a retained credential that mismatches the "
                  "current secret but occurs among the prior-secret "
                  "credentials, the spec demands (principalKept = true, action "
                  "= acceptedPrior) and this returns (false, reject). Witness "
                  "at storedCred = some 7, currentCred = 1, priorCreds = [7]."},
    {"id": "reject-prior-priority", "kind": "uniqueness", "expect": "reject",
     "module": _impl(_PRIOR_FIRST),
     "witness": _witness("(some 5)", "5", "[5]"),
     "refinement": "a NEAR-MISS: it accepts every session the frozen policy "
                   "accepts and keeps every principal it keeps, differing only "
                   "in how it CLASSIFIES a credential that BOTH secrets "
                   "recognise. Under the refinement's fixed effect glue "
                   "(mapping.md 2a) the two classifications drive different "
                   "session state changes, so a faithful patch of this shape "
                   "performs the prior-secret re-establishment on a request "
                   "that needed no change at all. Scope of the claim, stated "
                   "exactly: the overlap point this rival mishandles is reached "
                   "by NO listed test — each F2P call presents either a prior "
                   "list not containing the retained credential or an EMPTY "
                   "one, and the P2P request has no prior secrets configured, "
                   "so on every test-reachable input this rival agrees with the "
                   "frozen policy and the shipped suite would not catch it. "
                   "That is precisely why the SPEC has to pin leg priority: the "
                   "guarantee is verified => correct (the policy the issue "
                   "demands), not verified => passes the shipped assertions.",
     "rationale": "attacks L2 and the leg PRIORITY specifically: inverting the "
                  "branch order with no compensating side condition classifies "
                  "a credential valid under the CURRENT secret as "
                  "acceptedPrior whenever it also appears among the priors. "
                  "Witness at the overlap point storedCred = some 5, "
                  "currentCred = 5, priorCreds = [5] — the only input where "
                  "this rival and gold disagree, so it gets its own witness "
                  "rather than sharing reject-no-prior-path's."},
    {"id": "reject-partial-prior", "kind": "uniqueness", "expect": "reject",
     "module": _impl(_PARTIAL_PRIOR),
     "witness": _witness("(some 0)", "3", "[0]"),
     "refinement": "prior-secret acceptance must be TOTAL over present "
                   "mismatching credentials, not conditional on the credential "
                   "value. A faithful patch that consulted the prior secrets "
                   "for only some retained-credential shapes would drop the "
                   "rotated principal whenever the real token landed on an "
                   "excluded shape. Scope of the claim, stated exactly: the F2P "
                   "credential is whatever the unchanged token machinery "
                   "produces on its fixture, so whether that one run lands in "
                   "the excluded sub-domain is not something this battery "
                   "establishes either way — the honest reading is that such a "
                   "patch is FLAKY against the F2P, not that it "
                   "deterministically fails it. The spec is what refuses it "
                   "outright, by demanding the leg hold at EVERY credential "
                   "value including the excluded one.",
     "rationale": "attacks L3 on a value SUB-DOMAIN of the credential carrier: "
                  "for the one excluded retained-credential value the "
                  "prior-secret path is refused and the leg falls through to "
                  "reject, contradicting (true, acceptedPrior). A near-miss "
                  "agreeing with gold on every other input, so the witness sits "
                  "exactly on the excluded value: storedCred = some 0, "
                  "currentCred = 3, priorCreds = [0]."},
    {"id": "reject-prior-misclassified", "kind": "uniqueness", "expect": "reject",
     "module": _impl(_TAGGED_VALID),
     "witness": _witness("(some 9)", "4", "[2, 9]"),
     "refinement": "the principal survives here, so the rival satisfies the "
                   "survival half of the fix; what it gets wrong is WHICH "
                   "classification the credential receives. The refinement "
                   "fixes distinct session effects to the two classifications "
                   "(mapping.md 2a), and the F2P asserts the effect belonging "
                   "to the prior-secret classification is observable on the "
                   "first call. Reporting the credential as current-secret-"
                   "verified attaches the no-op glue instead, so the assertion "
                   "on that observable fails and the rival does NOT resolve.",
     "rationale": "attacks the `action` component of L3 in ISOLATION, holding "
                  "principalKept at gold's value — the rival that a battery "
                  "checking only survival would miss. The single `out = "
                  "verifyDecision ...` equation pins both components, so "
                  "(true, valid) contradicts the required (true, "
                  "acceptedPrior). Witness at storedCred = some 9, currentCred "
                  "= 4, priorCreds = [2, 9] — a multi-element prior list whose "
                  "match is not at the head."},
    {"id": "reject-absent-kept", "kind": "uniqueness", "expect": "reject",
     "module": _impl(_NONE_KEPT),
     "witness": _witness("none", "3", "[4]"),
     "refinement": "an ABSENT retained credential carries no evidence "
                   "whatsoever about the principal, so treating it as verified "
                   "keeps a principal for a session that was never "
                   "authenticated — a security regression, not the requested "
                   "feature. Scope of the claim, stated exactly: no listed test "
                   "reaches this leg. The one P2P case with nothing retained "
                   "never LOCATES a principal, so the decision under spec is "
                   "not entered at all on it, and both F2P calls present a "
                   "retained credential. So this rival passes the shipped suite; "
                   "it is the spec, and only the spec, that refuses it. Left in "
                   "the battery deliberately: `storedCred = none` is a binder "
                   "value the obligation must pin whether or not a shipped "
                   "assertion happens to observe it, and this is the only rival "
                   "that moves that binder off `some`.",
     "rationale": "attacks L1, the `none` leg: the spec demands (false, "
                  "reject) for storedCred = none and this returns (true, "
                  "valid). The only rival that moves `storedCred` off the "
                  "`some` constructor, which is what makes that binder "
                  "discriminated rather than merely bound. Witness at "
                  "storedCred = none, currentCred = 3, priorCreds = [4]."},
    {"id": "reject-current-ignored", "kind": "uniqueness", "expect": "reject",
     "module": _impl(_IGNORE_CURRENT),
     "witness": _witness("(some 6)", "6", "[]"),
     "refinement": "the mirror error of dropping the prior-secret path: this "
                   "drops the CURRENT-secret one, so an ordinary session with "
                   "nothing rotated is no longer recognised. The PASS_TO_PASS "
                   "suite exercises that path on every request, so a faithful "
                   "patch of this shape logs out every user with no prior "
                   "secrets configured and does NOT resolve.",
     "rationale": "attacks L2 with the prior-secret list held EMPTY, so the "
                  "refutation cannot be blamed on the current/prior overlap "
                  "that reject-prior-priority exploits: with priorCreds = [] "
                  "the spec demands (true, valid) for a credential matching the "
                  "current secret and this returns (false, reject). This is the "
                  "witness point that varies priorCreds to the empty list, "
                  "discriminating that binder's length. Witness at storedCred = "
                  "some 6, currentCred = 6, priorCreds = []."},
    {"id": "reject-head-prior-only", "kind": "uniqueness", "expect": "reject",
     "module": _impl(_HEAD_PRIOR_ONLY),
     "witness": _witness("(some 3)", "8", "[1, 2, 3]"),
     "refinement": "prior-secret acceptance must be EXHAUSTIVE over the "
                   "configured prior secrets, not limited to the most recent "
                   "one. A faithful patch of this shape keeps a principal only "
                   "when the session was established under the single newest "
                   "prior secret, and drops it for any older one — so a "
                   "deployment rotating through more than one retained secret "
                   "logs out exactly the users the requested behaviour is meant "
                   "to keep. Scope of the claim, stated exactly: both F2P calls "
                   "configure at most ONE prior secret, so this rival agrees "
                   "with the frozen policy on every listed test and the shipped "
                   "suite cannot see it; the spec is the only thing that "
                   "separates them.",
     "rationale": "attacks the priorCreds binder POSITIONALLY — the dimension no "
                  "other rival probes. Every other rival consults either the "
                  "whole list or none of it, so none of them forces the search "
                  "to be exhaustive rather than head-only. The spec's "
                  "`priorCreds.contains h` is membership at ANY index, so a "
                  "match at a non-head position must still yield (true, "
                  "acceptedPrior) where this returns (false, reject). Witness at "
                  "storedCred = some 3, currentCred = 8, priorCreds = [1, 2, 3] "
                  "— the match sits at the LAST index, so the refutation is "
                  "attributable to position and not to membership."},
    {"id": "reject-accept-unknown", "kind": "uniqueness", "expect": "reject",
     "module": _impl(_ACCEPT_UNKNOWN),
     "witness": _witness("(some 8)", "2", "[5]"),
     "refinement": "the permissive dual of reject-no-prior-path: it never "
                   "consults the prior-secret credentials at all and accepts "
                   "ANY present credential that fails the current secret. That "
                   "authenticates a principal on a credential no configured "
                   "secret produced — the opposite of the requested behaviour, "
                   "and a strictly worse security posture than the pre-image, "
                   "which at least dropped the principal. Scope of the claim, "
                   "stated exactly: no listed test presents an unrecognised "
                   "retained credential, so this rival passes the shipped suite "
                   "AND makes the F2P pass for the wrong reason — accepting the "
                   "rotated session without the prior-secret list ever being "
                   "read. Only the spec separates it from the frozen policy, "
                   "which is exactly what an F2P-shaped oracle cannot do and "
                   "why L4 needs a rival of its own.",
     "rationale": "attacks L4, the leg no other rival touches: for a present "
                  "credential recognised by neither the current nor any prior "
                  "secret the spec demands (false, reject) and this returns "
                  "(true, acceptedPrior). Because it ignores priorCreds "
                  "entirely, the witness holds a NON-matching prior list, "
                  "distinguishing it from reject-accept-everything shapes: "
                  "storedCred = some 8, currentCred = 2, priorCreds = [5]."},
]
