# properties.py — G-PBT falsification battery for django__django-15315 (lean lane).
#
# PORTED from the nagini sibling: the adversarial ARGUMENTS are carried over, the
# mechanics re-expressed against this backend's carrier. Each SPEC case is a FULL
# Solution.lean variant sharing the FROZEN spec byte-for-byte (only the impl region
# — and, where a positive reproves, the proof body — is edited), checked by
# variant_scope + the Lean verifier. Every expect="reject" case carries a
# refutation `witness`: a snippet that ELABORATES against the rival and FAILS on
# the frozen solution, so the rejection is attributable to the postcondition and
# not to a tactic script that merely stopped matching a reshaped impl.
#
# DEFENDED SURFACE (read from Solution.lean / mapping.md / instance.json):
#   object_hash : IdObject → Int, one obligation `theorem correct_object_hash`,
#   quantified over EVERY IdObject with NO precondition hypothesis.
#     input binder `o : IdObject`, two independent components:
#       o.serial : Int                      — the construction-time identity
#                                             token, ranging over ALL of Int
#                                             (negative tokens are real inputs)
#       o.owner  : Option (String × String) — the owner identity, `none` until
#                                             the object is attached to a
#                                             container, `some (label, name)`
#                                             afterwards
#     load-bearing postcondition (a single top-level clause):
#       result = int_hash o.serial
#     Two things are pinned at once, and each is attackable on its own:
#       (a) DEPENDENCE on o.serial — the result must be the standard integer hash
#           OF THE TOKEN, so an impl that ignores the token is refutable;
#       (b) INDEPENDENCE from o.owner — o.owner does not occur on the right-hand
#           side at all, so an impl whose result moves with the attachment state
#           or with the owner strings is refutable. This is the immutability the
#           issue demands: the value before and after attachment must agree.
#
# CARRIER NOTE: the nagini sibling abstracted the same decision behind fractional
# read permission over four flat int fields (`order`, `has_owner`, `owner_label`,
# `owner_name`), where the owner-derived fields were readable only under the
# attachment flag. This backend models the same object as a transparent structure
# whose owner component is an `Option`, and `int_hash` is a total, transparent
# function of the token (no opaque callee, no answer-key oracle). So every VALUE
# clause the nagini battery attacked has a direct counterpart here and each is
# refutable at a concrete literal input — witnesses need no conditioning on the
# carrier — but the nagini cases that rejected for PERMISSION reasons rather than
# for a value mismatch have no counterpart at all (see LANES THAT DO NOT PORT).
#
# LANES THAT DO NOT PORT:
#   * FRAME-MUTATION (nagini's mandatory class #1: two rivals that STORED into an
#     input field held at half permission). Lean is referentially transparent —
#     no aliasing, no fractional permission, and the input is an immutable
#     structure value — so "write into a read-only input" is not expressible and
#     the lane is VACUOUS here. No substitute is fabricated.
#   * DIVERGENCE / non-termination (nagini's diverge-loop, rejected there by
#     MustTerminate). NOT vacuous, and NOT a spec hole — UNSHIPPABLE under the
#     witness requirement, which is a third thing. Measured, because the earlier
#     claim here ("a diverging implementation cannot be written at all") is
#     false: a diverging impl IS writable in the impl region, two ways, and both
#     pass the mechanical scope check —
#       (i)  `let mut i := 0; while true do i := i + 1; return int_hash (o.serial + i)`
#       (ii) `partial def implementation_object_hash o := implementation_object_hash o`
#     and the frozen obligation REJECTS both (build exit 1,
#     "Tactic `rfl` failed: The left-hand side `o` is not definitionally equal to
#     the right-hand side `implementation_object_hash o`"), which is the correct
#     disposition for a carrier whose `def`s are total. So the spec is not weak
#     here. What blocks SHIPPING the case is witness attribution: the diverging
#     term does not reduce, so `decide` gets stuck on it for EVERY claim. Both
#     builds were run against rival (i): the refutation `¬ problem_spec ...` and
#     the FLIPPED claim `problem_spec ...` fail IDENTICALLY on the rival
#     (both exit 1, "Tactic `decide` failed for proposition ¬(have i := 0; do
#     let r ← forIn Lean.Loop.mk ...") — and the rival build is the half a
#     witness MUST pass. A witness whose exit code is the same whatever it claims
#     attributes nothing, so shipping this rival would record a rejection the
#     gate could not attribute, not a refutation. Hence no case: the rejection is
#     real but unattributable, deliberately left out rather than dropped as
#     vacuous. (Contrast velvet under partial termination semantics, where the
#     analogous rival VERIFIES and the class is a genuine KNOWN SPEC HOLE —
#     the corpus-wide termination-semantics finding. That does not apply to lean.)
#     Adjacent measurement worth recording, since it looks like a hole and is
#     not: `repeat pure ()` before the frozen return VERIFIES here. That is
#     correct, not a vacuous pass — the loop is a no-op, not a divergence.
#     `Id.run`'s bind discards the unforced loop value, so the impl reduces to
#     the frozen one; confirmed by negative control (`g2 5 = 7 := rfl` FAILS with
#     a type mismatch while `g2 5 = 6 := rfl` closes, so `rfl` really is
#     reducing the term rather than skipping it).
#   * UNGUARDED OWNER READ (nagini's `unguarded-owner-read-shadow`, an
#     expect="reject" case). Its nagini rejection came from the EXISTENCE
#     discipline — the owner-derived fields were readable only under the
#     attachment flag, mirroring an absent attribute on an unattached object —
#     not from the postcondition. Here the owner component is a total `Option`
#     field that is always present and always readable; an impl that inspects it
#     and still returns the token hash is CORRECT on this carrier, so there is no
#     discriminating witness and shipping it as a reject case would be a rival
#     that "rejects" for no reason the spec supplies. The argument is preserved on
#     the POSITIVE side instead, as `pos-owner-inspected` below.
#   * AXIOM_TESTS. The axiom lane is G-AX's job; this gate ignores them, and this
#     bundle consumes no axiom anyway (the integer hash is modeled concretely and
#     differential-tested by G-CONF).
#
# ADMISSIBILITY, which DOES port (this replaces an earlier note claiming the lane
# was N/A because `correct_object_hash` binds `∀ (o : IdObject)` with no
# precondition hypothesis). "No precondition" is not a reason: the analogue on a
# total carrier is the obligation being UNSATISFIABLE at an F2P-shaped input, and
# a positive that discharges it at that concrete input by EVALUATION — as a
# `have`, before closing the frozen obligation verbatim — tests exactly that.
# See `admiss-f2p-shape-satisfiable` below; it ports nagini's
# `admiss-call-and-stability`, including that case's stability assertion.
from pathlib import Path

INSTANCE = "django__django-15315"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# --- anchors -----------------------------------------------------------------
# The frozen impl body: the single return, lying ENTIRELY inside
# impl-start/impl-end and unique in the file.
_IMPL = "  return int_hash o.serial"
assert _BASE.count(_IMPL) == 1, "impl anchor drifted"

# The frozen proof body (tactic lines only, inside proof-start/proof-end). Swapped
# ONLY by positives that reshape the impl enough that the frozen script no longer
# closes; the theorem STATEMENT is never touched, and no case adds an
# axiom/lemma/sorry.
_PROOF = "  intro o\n  rfl"
assert _BASE.count(_PROOF) == 1, "proof anchor drifted"


def _impl(body, proof=None):
    """Full Solution.lean with the impl body replaced (and optionally the proof
    body reproved). Edits only the impl (+ proof) region, so same_spec holds."""
    src = _swap(_BASE, _IMPL, body)
    return _swap(src, _PROOF, proof) if proof is not None else src


# A digest of the owner identity strings, reused by the rivals that fold the
# owner into the result. Expressed with the imperative idioms the impl region
# already uses; it is value-DEPENDENT, so it distinguishes different owners
# rather than merely flagging attachment.
_OWNER_DIGEST = (
    "  let mut d : Int := 0\n"
    "  if let some (label, name) := o.owner then\n"
    "    for c in label.toList do d := d + (c.toNat : Int)\n"
    "    for c in name.toList do d := d + (c.toNat : Int)\n"
)


def _witness(serial, owner):
    """A refutation witness: the frozen spec predicate is FALSE of the rival's
    own result at one concrete input. Carrier is fully transparent, so `decide`
    settles it; the head binds nothing, so there are no hypotheses that could be
    inconsistent."""
    obj = "{ serial := %s, owner := %s }" % (serial, owner)
    return (
        "example : ¬ problem_spec_object_hash\n"
        "    %s\n"
        "    (implementation_object_hash %s) := by\n"
        "  unfold problem_spec_object_hash implementation_object_hash\n"
        "  decide\n" % (obj, obj)
    )


# =============================================================================
# POSITIVE CONTROLS (soundness) — must VERIFY, else SPEC-TOO-STRONG.
# =============================================================================

# Reshape 1: bind the value to a local before returning it. No branch structure
# changes, so the frozen proof body still closes.
_POS_LOCAL = _impl("  let h : Int := int_hash o.serial\n  return h")

# Reshape 2: an explicit but VACUOUS split on the attachment state — both arms
# return the same token hash, so the function is unchanged on every input while
# the control shape is one a faithful patch could equally take. The frozen
# script no longer closes across the branch tree, so it is genuinely REPROVEN
# (statement byte-identical, no new axiom/lemma/sorry).
_POS_BRANCH = _impl(
    "  if o.owner.isSome then\n"
    "    return int_hash o.serial\n"
    "  else\n"
    "    return int_hash o.serial",
    "  intro o\n"
    "  unfold problem_spec_object_hash implementation_object_hash\n"
    "  by_cases h : o.owner.isSome <;> simp [h]",
)

# Reshape 3 (carries nagini's guarded-owner-read argument to the positive side):
# the impl INSPECTS the owner identity — destructures it and binds its strings —
# and still returns the token hash alone. Reading the owner is harmless; only
# LETTING IT REACH THE RESULT is the defect. The spec must admit this, else
# SPEC-TOO-STRONG.
_POS_INSPECT = _impl(
    "  match o.owner with\n"
    "  | some (label, name) =>\n"
    "    let _inspected : String := label ++ name\n"
    "    return int_hash o.serial\n"
    "  | none => return int_hash o.serial",
    "  intro o\n"
    "  unfold problem_spec_object_hash implementation_object_hash\n"
    "  cases o.owner <;> rfl",
)

# Reshape 4: explicitly DISCARD the owner component first (rebuild the object
# with no owner), then hash the token of that. Observationally identical because
# the result never depended on the owner; a different data-flow shape for the
# same immutability guarantee.
_POS_ERASE = _impl(
    "  let bare : IdObject := { o with owner := none }\n"
    "  return int_hash bare.serial"
)

# Reshape 5 (AUDIT ADDITION): the owner identity is genuinely CONSUMED by the
# arithmetic that produces the result — the same value-dependent digest the
# rivals fold in — and then cancelled back out again. Every other positive here
# keeps the owner strictly out of the returned expression, so each of them would
# still verify under a spec that had banned owner-derived terms syntactically
# rather than pinning the VALUE. This one would not: it is the only positive
# whose result expression mentions the owner. It must verify, because the spec
# constrains what the result IS, not which components were read on the way
# there; else SPEC-TOO-STRONG.
_POS_DIGEST_CANCELS = _impl(
    _OWNER_DIGEST + "  return int_hash (o.serial + d - d)",
    "  intro o\n"
    "  unfold problem_spec_object_hash implementation_object_hash\n"
    "  cases o.owner <;> simp",
)


# =============================================================================
# ADMISSIBILITY (AUDIT ADDITION) — must VERIFY, else PRECOND-TOO-STRONG.
# =============================================================================
# The impl is the FROZEN one, untouched; the whole case lives in the proof
# region, which is what makes it an admissibility probe rather than another
# soundness reshape. Each `have` discharges the frozen postcondition at a
# CONCRETE F2P-shaped input BY EVALUATION (`decide`, so the obligation is
# actually computed at that point rather than restated), and only then is the
# frozen obligation closed by the frozen script verbatim. Three inputs, chosen
# to be the shapes the behavioural test actually builds:
#   * { serial := 7, owner := none }              — the object BEFORE attachment
#   * { serial := 7, owner := some ("m", "f") }   — the SAME object after it
#                                                   acquires an owner
#   * { serial := -1, owner := none }             — an auto-created object's
#                                                   token, which is also the
#                                                   reserved-output boundary of
#                                                   the hash law
# plus `h_stable`, the stability assertion nagini's admiss case carried: the
# result at the unattached shape EQUALS the result at the attached one, computed
# on both sides. If the obligation were unsatisfiable at any of these — the
# total-carrier analogue of PRECOND-TOO-STRONG — the corresponding `have` could
# not close by evaluation and this case would FAIL while every other positive
# still passed.
_ADM_F2P = _impl(
    _IMPL,
    "  have h_before : problem_spec_object_hash\n"
    "      { serial := 7, owner := none }\n"
    "      (implementation_object_hash { serial := 7, owner := none }) := by\n"
    "    unfold problem_spec_object_hash implementation_object_hash\n"
    "    decide\n"
    "  have h_after : problem_spec_object_hash\n"
    "      { serial := 7, owner := some (\"m\", \"f\") }\n"
    "      (implementation_object_hash { serial := 7, owner := some (\"m\", \"f\") }) := by\n"
    "    unfold problem_spec_object_hash implementation_object_hash\n"
    "    decide\n"
    "  have h_stable : implementation_object_hash { serial := 7, owner := none }\n"
    "      = implementation_object_hash { serial := 7, owner := some (\"m\", \"f\") } := by\n"
    "    unfold implementation_object_hash\n"
    "    decide\n"
    "  have h_before_auto : problem_spec_object_hash\n"
    "      { serial := -1, owner := none }\n"
    "      (implementation_object_hash { serial := -1, owner := none }) := by\n"
    "    unfold problem_spec_object_hash implementation_object_hash\n"
    "    decide\n"
    "  intro o\n"
    "  rfl",
)


# =============================================================================
# UNIQUENESS RIVALS — must be REJECTED, else SPEC-TOO-WEAK. Each shares the
# frozen spec exactly, edits only the impl region, keeps the frozen proof body,
# and carries a witness SEEN to elaborate against the rival and FAIL on gold.
# =============================================================================

# R1 — fold the owner digest into the hashed token: the result moves with the
# owner identity once one is available. Attacks clause (b), INDEPENDENCE.
_RIV_FOLDED = _impl(_OWNER_DIGEST + "  return int_hash (o.serial + d)")

# R2 — a bare attachment FLAG offset: +1 exactly when attached, ignoring the
# owner strings entirely. Attacks clause (b) through the Option's constructor
# alone, so it survives any rival-detector keyed on the owner strings.
_RIV_FLAG = _impl(
    "  if o.owner.isSome then\n"
    "    return int_hash o.serial + 1\n"
    "  else\n"
    "    return int_hash o.serial"
)

# R3 — hash the owner digest INSTEAD of the token: the result ignores the
# identity token altogether. Attacks clause (a), DEPENDENCE on o.serial — the
# only rival here whose witness needs an UNATTACHED input.
_RIV_OWNER_ONLY = _impl(_OWNER_DIGEST + "  return int_hash d")

# R4 — a NEAR-MISS restricted to a sub-domain of the token: owner-folding fires
# only for non-negative tokens, so on every negative token this rival agrees
# with gold exactly (checked: the spec predicate HOLDS of it at
# serial := -5, owner := some ("a", "b")). It therefore gets its own witness at a
# non-negative token rather than sharing R1's.
_RIV_SUBDOMAIN = _impl(
    "  if 0 ≤ o.serial then\n"
    "    let mut d : Int := 0\n"
    "    if let some (label, name) := o.owner then\n"
    "      for c in label.toList do d := d + (c.toNat : Int)\n"
    "      for c in name.toList do d := d + (c.toNat : Int)\n"
    "    return int_hash o.serial + d\n"
    "  else\n"
    "    return int_hash o.serial"
)

# R5 / R6 (AUDIT ADDITIONS) — attack the postcondition's RIGHT-HAND SIDE, which
# every rival above leaves untouched: R1-R4 all return `int_hash <something>`,
# so each of them concedes the token-hash LAW and attacks only which value is
# fed to it. A spec that pinned merely "the result is int_hash of SOME
# owner-independent function of the token" would reject all four and still be
# too weak. These two inline the law and get it wrong, so the token maps to the
# wrong hash while remaining perfectly owner-independent — which also makes them
# the only rivals here whose defect is invisible to any amount of owner
# variation.

# R5 — the law's magnitude reduction and sign re-application are kept, but the
# RESERVED-OUTPUT remap (`-1` is never returned; it becomes `-2`) is dropped.
# The narrowest near-miss in the battery: it agrees with gold on every token
# whose reduced value is not `-1` (checked: the spec predicate HOLDS of it at
# serial := -5 / 9 / 0), and diverges exactly on the tokens that reduce to the
# reserved output — serial := -1 among them.
_RIV_NO_RESERVED = _impl(
    "  let m : Int := 2 ^ 61 - 1\n"
    "  let r : Int := if 0 ≤ o.serial then o.serial % m else -((-o.serial) % m)\n"
    "  return r"
)

# R6 — the sign of the token is never re-applied: the magnitude reduction is
# taken on the signed token directly, so a negative token maps into the POSITIVE
# residue class instead of the negative one. Agrees with gold on the whole
# non-negative half of the token domain (checked: the predicate HOLDS at
# serial := 9 and serial := 0) and is wrong on the negative half — the
# auto-created serials, which are real inputs here.
_RIV_UNSIGNED = _impl("  return o.serial % (2 ^ 61 - 1)")


# The shared refinement core: the F2P test places the object in a hash-based
# container's terms BEFORE attachment, attaches it, and asserts the hash is
# UNCHANGED. Any faithful patch whose hash moves with attachment fails it.
_REF_IMMUTABLE = (
    "The faithful real patch keeps the hash dependent on the owner identity that "
    "only becomes available on attachment, so the value observed before "
    "attachment and the value observed after it differ. The F2P test hashes the "
    "object, attaches it to an owning container, and asserts the hash is "
    "unchanged; a hash that moves across attachment fails that assertion. So "
    "this rival's faithful patch does NOT resolve, and a verifying rival would "
    "be a true verify-does-not-imply-resolve break."
)


SPEC_TESTS = [
    # ------------------------------------------------------------------ positives
    {
        "id": "pos-local-bind",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_LOCAL,
        "rationale": "A correct token-only impl in a different syntactic shape "
                     "(local-variable reshape of the returned value). The single "
                     "postcondition clause `result = int_hash o.serial` is "
                     "discharged at every `o` exactly as before, so it MUST "
                     "verify; if it cannot, SPEC-TOO-STRONG. Ported from "
                     "nagini's pos-control-local-bind.",
    },
    {
        "id": "pos-attach-branch",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_BRANCH,
        "rationale": "An explicit split on the attachment state whose two arms "
                     "return the SAME token hash: correct on both arms, and a "
                     "control shape a faithful patch could take. Reproved with "
                     "`by_cases` + `simp` because the frozen script is tuned to "
                     "the unbranched form — the theorem STATEMENT is unchanged "
                     "and no assumption is added. Exercises the o.owner binder "
                     "on the verify side (both constructors). If it fails, "
                     "SPEC-TOO-STRONG (a postcondition over-fit to one branch "
                     "shape). Ported from nagini's pos-control-branch-reorder.",
    },
    {
        "id": "pos-owner-inspected",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_INSPECT,
        "rationale": "The impl destructures the owner identity and binds its "
                     "strings, then returns the token hash alone. Inspecting the "
                     "owner is not the defect — letting it reach the RESULT is — "
                     "so the spec must admit this; else SPEC-TOO-STRONG. This is "
                     "where nagini's guarded-owner-read argument lands on this "
                     "carrier: nagini could REJECT the unguarded form because its "
                     "owner fields were readable only under the attachment flag, "
                     "whereas here the owner is a total Option that is always "
                     "readable, so the same shape is simply correct.",
    },
    {
        "id": "pos-owner-erased",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_ERASE,
        "rationale": "A different DATA-FLOW shape for the same guarantee: "
                     "discard the owner component outright, then hash the token "
                     "of the owner-free object. Observationally identical since "
                     "the result never depended on the owner, so it must verify; "
                     "else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-owner-digest-cancels",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_DIGEST_CANCELS,
        "rationale": "The ONLY positive whose RESULT EXPRESSION mentions the "
                     "owner: the same value-dependent owner digest the rivals "
                     "fold in is folded in here too, and then cancelled back "
                     "out, so the returned value is gold's at every input. The "
                     "other three positives keep the owner out of the returned "
                     "expression entirely, so all of them would still verify "
                     "against a spec that banned owner-derived TERMS "
                     "syntactically instead of pinning the VALUE; this one "
                     "would not. It must verify, because the postcondition "
                     "constrains what the result IS, not which components were "
                     "read or arithmetically touched on the way to it; else "
                     "SPEC-TOO-STRONG. Reproved (`cases` + `simp`) because the "
                     "frozen `rfl` is tuned to the unbranched form; statement "
                     "byte-identical, no assumption added.",
    },

    # ------------------------------------------------------- admissibility
    {
        "id": "admiss-f2p-shape-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADM_F2P,
        "rationale": "PRECOND-TOO-STRONG on a total carrier: the obligation "
                     "binds every `o : IdObject` with no precondition "
                     "hypothesis, so what could go wrong is not an unmeetable "
                     "guard but the obligation being UNSATISFIABLE at an "
                     "F2P-shaped input. This case discharges it, by EVALUATION "
                     "(`decide`, so the postcondition is computed rather than "
                     "restated), at the three concrete inputs the behavioural "
                     "test actually builds — the object before attachment "
                     "({ serial := 7, owner := none }), the SAME object after it "
                     "acquires an owner ({ serial := 7, owner := some "
                     "(\"m\", \"f\") }), and an auto-created object's negative "
                     "token ({ serial := -1, owner := none }), which is also the "
                     "reserved-output boundary of the hash law — and additionally "
                     "asserts h_stable, that the result at the unattached shape "
                     "EQUALS the result at the attached one, computed on both "
                     "sides. That equality is the immutability-across-attachment "
                     "property the F2P test checks, established here at a "
                     "concrete input rather than argued in prose. The impl is the "
                     "FROZEN one byte-for-byte and the frozen obligation is "
                     "closed by the frozen script verbatim after the `have`s, so "
                     "nothing but satisfiability is being tested; the statement "
                     "is untouched and no axiom/lemma/sorry is added. If any "
                     "`have` could not close by evaluation, the obligation would "
                     "be vacuous or unsatisfiable at a real input => "
                     "PRECOND-TOO-STRONG. Ports nagini's "
                     "admiss-call-and-stability, whose conditional "
                     "half-permission footprint has no counterpart here but "
                     "whose stability assertion does.",
    },

    # ------------------------------------------------------------------ rivals
    {
        "id": "riv-owner-folded",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FOLDED,
        "rationale": "Attacks the INDEPENDENCE half of "
                     "`result = int_hash o.serial`: a value-dependent digest of "
                     "the owner identity is folded into the hashed token, so the "
                     "result varies with o.owner, which does not occur in the "
                     "postcondition at all. Refuted at an ATTACHED input with "
                     "non-empty owner strings (serial := 5). This is the "
                     "owner-folding shape nagini attacked as "
                     "wrong-arg-order-plus-owner / partial-domain-attached.",
        "refinement": _REF_IMMUTABLE,
        "witness": _witness("5", 'some ("a", "b")'),
    },
    {
        "id": "riv-attach-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_FLAG,
        "rationale": "Attacks INDEPENDENCE through the ATTACHMENT STATE ALONE: a "
                     "constant offset applied exactly when an owner is present, "
                     "with the owner strings never consulted. A battery that only "
                     "probed owner-string sensitivity would miss it. Refuted at "
                     "an attached input whose owner strings are EMPTY "
                     "(so any digest-shaped rival would agree with gold there) "
                     "and whose token is the reserved-output boundary "
                     "serial := -1, which also exercises the negative branch of "
                     "int_hash. Ported from nagini's partial-domain-attached.",
        "refinement": _REF_IMMUTABLE,
        "witness": _witness("-1", 'some ("", "")'),
    },
    {
        "id": "riv-owner-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_OWNER_ONLY,
        "rationale": "Attacks the DEPENDENCE half: the result is the hash of the "
                     "owner digest INSTEAD of the identity token, so o.serial "
                     "never reaches it. Refuted at an UNATTACHED input "
                     "(owner := none, serial := 7) — the only witness here on "
                     "the none constructor, where the rival collapses to a "
                     "constant while the spec still demands the token's hash. "
                     "This is nagini's wrong-arg-owner-label: the same oracle "
                     "called on the wrong argument.",
        "refinement": "The faithful real patch derives the hash from the owner "
                      "identity rather than from the construction-time token. "
                      "Before attachment there is no owner identity to read, so "
                      "the value is drawn from a different source than after "
                      "attachment; the F2P test hashes the object, attaches it, "
                      "and asserts equality, which such a hash cannot satisfy. "
                      "It also stops distinguishing objects that share an owner "
                      "but differ in token. So its faithful patch does NOT "
                      "resolve.",
        "witness": _witness("7", "none"),
    },
    {
        "id": "riv-token-subdomain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_SUBDOMAIN,
        "rationale": "A NEAR-MISS on a sub-domain of the token binder: the "
                     "owner-folding fires only for NON-NEGATIVE tokens, so on "
                     "every negative token this rival satisfies the "
                     "postcondition exactly (verified: the spec predicate HOLDS "
                     "of it at serial := -5, owner := some (\"a\", \"b\"), where "
                     "riv-owner-folded already fails). It therefore carries its "
                     "OWN witness, at a non-negative token (serial := 3), rather "
                     "than sharing another rival's — otherwise its rationale "
                     "would claim a sub-domain the manifest never demonstrates. "
                     "Ported from nagini's partial-domain-order-zero, widened "
                     "from one token value to the sign split so it survives on a "
                     "carrier where every token is a real input.",
        "refinement": _REF_IMMUTABLE + " Restricting the defect to a sub-range "
                      "of the identity token does not help: ordinary objects "
                      "receive non-negative tokens, so the object the F2P test "
                      "builds lands squarely inside the broken sub-domain.",
        "witness": _witness("3", 'some ("m", "")'),
    },
    {
        "id": "riv-no-reserved-remap",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_NO_RESERVED,
        "rationale": "Attacks the postcondition's RIGHT-HAND SIDE — the "
                     "token-hash LAW itself — which every rival above concedes: "
                     "riv-owner-folded / riv-attach-flag / riv-owner-only / "
                     "riv-token-subdomain all return `int_hash <something>` and "
                     "argue only about the argument, so a spec pinning merely "
                     "\"int_hash of some owner-independent function of the "
                     "token\" would reject all four and still be too weak. Here "
                     "the law is inlined with the RESERVED-OUTPUT remap dropped: "
                     "the reduction and the sign re-application are exact, so "
                     "the rival agrees with gold on every token whose reduced "
                     "value is not the reserved one (verified: the spec "
                     "predicate HOLDS of it at serial := -5, at serial := 9 and "
                     "at serial := 0) and is wrong precisely on the tokens that "
                     "reduce to it. The narrowest near-miss in the battery, and "
                     "OWNER-INDEPENDENT — no amount of owner variation exposes "
                     "it, so it survives every discriminator the four rivals "
                     "above rely on. Refuted at serial := -1, the boundary the "
                     "remap exists for.",
        "refinement": "The faithful real patch derives the hash from the "
                      "construction-time token alone — so it IS immutable "
                      "across attachment and the F2P assertion passes — but "
                      "reproduces the standard integer hash incorrectly at the "
                      "reserved output, returning the one value the platform "
                      "reserves as its error sentinel instead of the value the "
                      "standard hash of that token actually is. An auto-created "
                      "object receives exactly that token, so such a patch hands "
                      "the reserved sentinel back to every hash-based container "
                      "that stores one, and it disagrees with the standard hash "
                      "of an equal integer key, breaking lookups that mix the "
                      "two. So its faithful patch does NOT resolve, and a "
                      "verifying rival here would be a true "
                      "verify-does-not-imply-resolve break.",
        "witness": _witness("-1", 'some ("a", "b")'),
    },
    {
        "id": "riv-unsigned-reduction",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIV_UNSIGNED,
        "rationale": "The second attack on the LAW rather than on its argument, "
                     "and a sub-domain near-miss on the SIGN of the token: the "
                     "magnitude reduction is taken on the signed token directly, "
                     "so the sign is never re-applied and a negative token lands "
                     "in the positive residue class. It agrees with gold across "
                     "the entire NON-NEGATIVE half of the token domain "
                     "(verified: the spec predicate HOLDS of it at serial := 9 "
                     "with an owner attached, and at serial := 0) and is wrong "
                     "on the whole negative half, which is a real part of this "
                     "domain — the theorem carries no precondition, and "
                     "auto-created objects take their serials from a counter "
                     "running downwards. Also owner-independent, so the owner "
                     "binder cannot expose it. Refuted at serial := -5, a "
                     "negative token whose reduced value is NOT the reserved "
                     "one, so this case's refutation point is disjoint from "
                     "riv-no-reserved-remap's IN ONE DIRECTION ONLY, which is "
                     "what the two witnesses were built and measured to "
                     "establish: serial := -5 refutes THIS rival while "
                     "riv-no-reserved-remap SATISFIES the postcondition there "
                     "(verified, exit 0), so -5 separates the two defects. The "
                     "converse does not hold and is not claimed: "
                     "riv-no-reserved-remap's point serial := -1 also refutes "
                     "this rival (verified, exit 0 on the ¬-claim), since "
                     "dropping the sign re-application already maps -1 to the "
                     "positive residue. The two rivals are therefore distinct "
                     "defects with distinct witnesses, not defects with "
                     "mutually exclusive refutation sets.",
        "refinement": "The faithful real patch is again immutable across "
                      "attachment, so the F2P assertion itself passes, but it "
                      "computes the standard integer hash wrongly for every "
                      "object whose identity token is negative: the value it "
                      "returns is the positive residue rather than the negative "
                      "one the platform's hash of that integer produces. Every "
                      "auto-created object has a negative token, so such an "
                      "object no longer hashes equal to the plain integer key "
                      "equal to its token, and the standing behavioural tests "
                      "that exercise hashing and equality of auto-created "
                      "objects break. So its faithful patch does NOT resolve.",
        "witness": _witness("-5", "none"),
    },
]
