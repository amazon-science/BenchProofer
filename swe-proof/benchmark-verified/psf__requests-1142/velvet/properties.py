"""properties.py — G-PBT falsification battery for psf__requests-1142 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body — both
regions the consumer spec view elides, so ``markers.same_spec`` holds and the
``prove_correct contentLength`` obligation survives) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
elaborate against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method):

  contentLength (payload : Payload) (carriesBody : Bool) return (out : Option Nat)
    ensures out = announcedSize payload carriesBody

The method decides the announced payload size of a request from the shape of its
payload and one boolean property of the request method. The pure region pins the
whole outcome as a total function of the method's own two inputs:

  announcedSize payload carriesBody
    = match payload with
      | .seekable   n => some n          -- a positionable payload: announce its size n
      | .measurable n => some n          -- an in-memory payload:   announce its size n
      | .absent       => if carriesBody then some 0 else none

So the sole ensures is an EXACT equality pinning, across BOTH input binders:

  * (V) VALUE on a present payload — a ``seekable`` / ``measurable`` payload of
        size ``n`` announces exactly ``some n``. A rival that announces a
        different value (or nothing) for a present payload violates the ensures.
  * (D) the DISCRIMINATING DECISION on an absent payload — this is the changed
        behaviour. With no payload present the announcement forks on
        ``carriesBody``: a method that conventionally carries an entity body
        announces ``some 0``, a method that conventionally carries none announces
        ``none`` (NO size attached). The issue's F2P point is exactly the
        ``carriesBody = false`` arm: a body-less request whose method carries no
        body must announce NOTHING.

Both INPUT binders are free (the pre-conditions region is empty — no ``require``)
and the post-image must hold for EVERY value of each:
  * ``payload``     — the request payload shape; drives (V) and the absent split.
  * ``carriesBody`` — the method's body-carrying property; drives (D) in the
                      absent case (and is IGNORED for a present payload, which
                      the value rival exploits).

ADVERSARIAL READ of the nagini classes on THIS carrier (see the footer for the
case-by-case accounting):

  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling holds a mutable
    header map at full permission and its ``extra-header-smuggle`` rival writes an
    unrelated key into it, caught by a whole-map frame clause. This backend is
    referentially transparent: the method returns a single ``Option Nat`` (the
    announced size), declares no ``mut`` binder, has no heap and no aliasing.
    There is no map to smuggle a spurious key into and no permission system to
    trip, so the class is vacuous. No substitute is fabricated.
  * GET-vs-HEAD PARTIAL DOMAIN — VACUOUS by carrier narrowing. The sibling's
    ``partial-domain-head-only`` rival guards one concrete method token but not
    the other. This backend abstracts the whole ``method``-property distinction
    into the SINGLE boolean ``carriesBody`` (mapping.md §2.1), so there is no
    second token to mishandle independently; a rival that decided the fork from
    ``carriesBody`` alone but wrongly for one underlying method has no
    counterpart on this carrier. Reported as a carrier-collapsed omission.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is ``announcedSize payload carriesBody``, a concrete ``def`` in the ``pure``
    region computing the outcome from the method's own arguments (the ``axioms``
    region is empty; there is no opaque answer key). The unique satisfier IS the
    grounded decision, so there is no wrong echo to build; the honest controls
    are the cheapest faithful reshapes (the ``pos-*`` cases), and
    ``pos-two-stage-option`` re-routes the decision through an intermediate
    ``Option`` to make the point explicit with a shape that is demonstrably NOT
    definitionally the frozen body.
  * CONTROL-FLOW-EFFECT — captured by the value abstraction, not lost to it. The
    single observable effect (attach a size vs attach nothing) is exactly the
    ``Option Nat`` carrier: ``some n`` ↔ a ``Content-Length`` value, ``none`` ↔
    no header. So the announce/omit fork is fully observable to the ensures; the
    absent-case rivals are its discriminators.
  * VALUE / DECISION divergence — heavily exercised: the prepatch rival ignores
    ``carriesBody`` in the absent case (always announces a size), its dual
    over-corrects (never announces one), and the value rival drops the size of a
    present payload.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is a STRAIGHT-LINE ``match``
(no loop): its extracted program reduces fully under ``decide``. Each reject
rival carries a machine-checked refutation ``witness`` — a Velvet tester
statement ``contentLengthTester <payload> <carriesBody> = false`` at ONE concrete
input, checked in a file whose ``prove_correct`` block has been stripped so no
tactic script can mask the verdict. (``derive_tester_for`` needs a decidable
equality on the ``Payload`` return-side carrier; each witness first
``deriving instance DecidableEq for Payload`` — an instance, not an assumption:
no ``axiom`` / ``sorry`` / ``native_decide`` is involved, and the frozen solution
rejects the witnesses all the same.) Both halves were checked out-of-band with
``scripts/lean_verify.sh``: every witness ELABORATES against its rival (``decide``
proves the tester ``false``) and FAILS against the frozen solution, so each
rejection is a genuine spec refutation and not mechanical tactic breakage.

FORGERY-RESISTANCE OF THE GOLD SIDE (re-derived in audit, all four rivals). A
gold-side failure is evidence only if its exit code tracks WHAT THE WITNESS
CLAIMS; a failure that would occur for any claim discriminates nothing. Here the
gold side fails by PLAIN EVALUATION — ``Tactic `decide` proved that the
proposition contentLengthTester <input> = false is false`` — i.e. the kernel
fully reduced the tester at the concrete input and found it ``true`` (gold
satisfies its postcondition there), which is the strongest gold-side evidence
available. Confirmed by flipping each claim: the witness asserting the OPPOSITE
(``... = true``) BUILDS against the frozen solution (exit 0) and FAILS against
the rival (exit 1) with the mirror-image message. So both exit codes carry
information about the claim in both directions, and a forged witness asserting
gold is correct at an agreement point would have been recorded as unproven rather
than as a refutation. No case here rests on a stuck reduction, a missing
``Decidable`` instance, a unification failure, or an unknown identifier: the
carrier is a straight-line ``match`` over a small inductive with ``Nat`` sizes,
which the kernel reduces outright.

WHAT THE SHIPPED TESTS EXERCISE (honest scope of the reject lane). The only
behaviourally-discriminating shipped test on this instance keys on the
``carriesBody = false`` arm of the absent case (a body-less request whose method
carries no body must announce NOTHING); the ``prepatch`` rival is refuted exactly
there and is the true verify-does-not-imply-resolve discriminator. The other two
rivals attack sub-domains the gold contract PINS but the shipped F2P/P2P set does
not directly exercise (a present payload's announced value; the ``carriesBody =
true`` arm of the absent case). They are legitimate SPEC-TOO-WEAK probes — the
spec is faithful to gold on those sub-domains (G-CONF: 0 disagreements over
100011 real inputs), and admitting a rival that diverges from gold there would be
a spec-too-weak hole — and they are REQUIRED to vary the two input binders and
attack both independent behaviours (V) and (D) of the sole clause. Their
refinements say so plainly rather than overclaiming an F2P failure.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom`` and no deep-model
reference; ``announcedSize`` is an I-op modeled deeply and refutation-checked by
``conformance_check.py`` (G-CONF), not axiomatized. Nothing in the proof rests on
an axiom, and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "psf__requests-1142"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — the `let out : Option Nat := match ...` block
# strictly BETWEEN the method's `-- impl-start` / `-- impl-end`. Every rival and
# reshape edits ONLY this block (and, for the admissibility case, the elided
# `prove_correct` tactic body), so the spec view is untouched and same_spec holds
# by construction.
_GOLD_IMPL = (
    "    let out : Option Nat :=\n"
    "      match payload with\n"
    "      | .seekable   n => some n\n"
    "      | .measurable n => some n\n"
    "      | .absent       => if carriesBody then some 0 else none\n"
    "    return out"
)

assert _BASE.count(_GOLD_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. The admissibility case retunes THIS block (elided
# from the spec view) to also close its in-region assert VC; rivals and the two
# reshape positives leave it as-is.
_PROOF = ("prove_correct contentLength by\n"
          "  loom_solve\n"
          "  cases payload <;> simp_all [announcedSize]")

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for the admissibility assert)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's tester machinery:
# ---- `contentLengthTester <payload> <carriesBody> = false` says the extracted
# ---- program's result violates the postcondition at that concrete input.
# ---- Checked in a file whose `prove_correct` block is stripped. The `Payload`
# ---- return-side carrier needs a decidable-equality instance for the tester
# ---- derivation; it is DERIVED, not assumed.
_TESTER = (
    "deriving instance DecidableEq for Payload\n\n"
    "extract_program_for contentLength\n"
    "prove_precondition_decidable_for contentLength\n"
    "prove_postcondition_decidable_for contentLength\n"
    "derive_tester_for contentLength\n\n"
)


def _witness(call):
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the announced-value flow identical
    # and only reshapes the executable surface, so the frozen proof still
    # closes.
    # =====================================================================
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: reorder the match arms (absent first, then the two present
        # shapes). A `match` is defined by its arms, not their textual order, so
        # every input maps to the same announced value. The frozen proof
        # (`cases payload <;> simp_all`) closes regardless of arm order.
        "module": _impl(
            "    let out : Option Nat :=\n"
            "      match payload with\n"
            "      | .absent       => if carriesBody then some 0 else none\n"
            "      | .seekable   n => some n\n"
            "      | .measurable n => some n\n"
            "    return out"),
        "rationale": "reordering the match arms (absent case first) computes the "
                     "SAME announced value on every input — a match is its arm "
                     "set, not their order — so `out = announcedSize payload "
                     "carriesBody` still holds. A correct reshape must verify, "
                     "else SPEC-TOO-STRONG on arm order.",
    },
    {
        "id": "pos-two-stage-option",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: SPLIT the decision into two stages. First project the payload
        # to the size it carries, if any (`sized`), collapsing BOTH present
        # shapes and mapping `absent` to `none`; then recover the announcement
        # from that intermediate, consulting `carriesBody` only where no size was
        # found. Every input still maps to the same announced value, but the
        # control flow no longer mirrors the frozen `match`: the absent/present
        # split is now made by an `Option` scrutinee rather than by the `Payload`
        # constructor, and the two present arms have been merged and re-split.
        #
        # AUDIT NOTE (why this shape, and not a `let`-bound absent branch). The
        # case this replaces hoisted the absent-branch value into a typed local
        # and referenced it in the absent arm. That is a zeta-reduction of the
        # frozen body, so the two elaborate to the SAME term: checked directly at
        # the function level with `example : letShape = gOrder := rfl`, which
        # elaborates (exit 0). A positive that is definitionally the frozen impl
        # cannot witness SPEC-TOO-STRONG — `rfl` alone would close it whatever
        # the spec said. The same probe on THIS shape fails to close
        # (`Type mismatch ... twoStage = gOrder`, exit 1), so the two terms
        # genuinely differ and the frozen proof script has to do real work
        # (`cases payload <;> simp_all` must reduce the intermediate `match`).
        # Kept as the ECHO-HONEST control too: the post-image is grounded (a
        # concrete `def` over the method's own inputs, empty axioms region), so
        # there is no answer-key to echo and the honest control is a genuinely
        # reshaped correct impl.
        "module": _impl(
            "    let sized : Option Nat :=\n"
            "      match payload with\n"
            "      | .seekable   n => some n\n"
            "      | .measurable n => some n\n"
            "      | .absent       => none\n"
            "    let out : Option Nat :=\n"
            "      match sized with\n"
            "      | some n => some n\n"
            "      | none   => if carriesBody = true then some 0 else none\n"
            "    return out"),
        "rationale": "staging the decision — project the payload to the size it "
                     "carries (if any), then recover the announcement from that "
                     "intermediate, consulting `carriesBody` only when no size "
                     "was found — announces the same value on every input, so "
                     "`out = announcedSize payload carriesBody` still holds. The "
                     "control flow is NOT the frozen one: the absent/present "
                     "split is made by an `Option` scrutinee instead of the "
                     "`Payload` constructor, and the shape is verified NOT "
                     "definitionally equal to the frozen body (a function-level "
                     "`rfl` between them fails to elaborate), so the frozen proof "
                     "must genuinely re-derive the equality. A correct reshape "
                     "must verify, else SPEC-TOO-STRONG on decision staging.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO precondition (the pre-conditions
    # region is empty), so the sibling's literal probe ("a normal F2P-shaped
    # input satisfies the precondition") has no `require` to establish. The
    # analogue on a TOTAL-domain carrier is that the obligation must be
    # SATISFIABLE at exactly an F2P-shaped input: a spec whose post-image were
    # unreachable there would still be discharged by no impl at all, and the
    # gate would read the resulting universal rejection as a strong spec. So the
    # probe discharges the post-image AT the F2P-shaped point concretely, by
    # evaluation, as an in-region `assert`, BEFORE the frozen obligation closes
    # verbatim — that is the direction PRECOND-TOO-STRONG lives in here.
    #
    # AUDIT NOTE. The case this replaces asserted only non-degeneracy
    # (`announcedSize .absent true ≠ announcedSize .absent false`). That is a
    # real property, but it is a claim about the fork SEPARATING, not about the
    # F2P-shaped input being in-domain and satisfiable: a spec that demanded an
    # impossible announcement at the F2P point could still separate its two arms
    # and pass. The first conjunct below is the missing half — it pins the
    # announcement the F2P-shaped input actually requires (`absent` payload, a
    # method carrying no body ⇒ announce NOTHING) and so demonstrates that a
    # value satisfying the post-image EXISTS at that point. The non-degeneracy
    # conjunct is retained.
    #
    # The assert VC is LIVE, not decorative: replacing the first conjunct with
    # the false pin `announcedSize .absent false = some 0` leaves the file
    # failing (exit 1) with the assert's own goals unsolved
    # (`case «assert_1: ...».seekable ⊢ False`), so this positive would not have
    # verified had the claim been wrong.
    # =====================================================================
    {
        "id": "admiss-f2p-point-satisfiable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `assert\n"
            "      (announcedSize Payload.absent false = none ∧\n"
            "       announcedSize Payload.absent true ≠ announcedSize Payload.absent false))\n"
            "    let out : Option Nat :=\n"
            "      match payload with\n"
            "      | .seekable   n => some n\n"
            "      | .measurable n => some n\n"
            "      | .absent       => if carriesBody then some 0 else none\n"
            "    return out",
            "prove_correct contentLength by\n"
            "  loom_solve <;> (try cases payload) <;> simp_all [announcedSize]"),
        "rationale": "the obligation is SATISFIABLE at an F2P-shaped input, "
                     "discharged by evaluation before the frozen obligation "
                     "closes: at the F2P point (no payload present, a method that "
                     "conventionally carries no entity body) the post-image "
                     "demands `announcedSize .absent false = none` — announce "
                     "NOTHING — and that value is reachable, so no impl is asked "
                     "for the impossible there (else PRECOND-TOO-STRONG, which on "
                     "a total-domain carrier shows up as an unsatisfiable "
                     "obligation at exactly this input rather than as an "
                     "unestablishable `require`). The second conjunct adds that "
                     "the absent-case fork is non-degenerate: the two arms differ, "
                     "so the guard really separates its outcomes rather than "
                     "collapsing to one. Both in-region assert VCs must discharge, "
                     "and the impl is kept verbatim so the ensures discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is straight-line (its witness reduces under
    # `decide`), refuted at a concrete input by a witness that FAILS on the
    # frozen solution, and carries a refinement stated to the actual tested
    # surface.
    # =====================================================================
    {
        "id": "weak-prepatch-always-announce",
        "kind": "uniqueness",
        "expect": "reject",
        # THE discriminating bug (pre-patch): in the absent case, announce a zero
        # size UNCONDITIONALLY, ignoring `carriesBody`. This is the pre-gold
        # behaviour (a leading unconditional zero the present-payload branches
        # overwrote), collapsed onto this carrier.
        "module": _impl(
            "    let out : Option Nat :=\n"
            "      match payload with\n"
            "      | .seekable   n => some n\n"
            "      | .measurable n => some n\n"
            "      | .absent       => some 0\n"
            "    return out"),
        "refinement": "this IS the pre-patch behaviour: a body-less request always "
                      "announces a zero size, even for a method that "
                      "conventionally carries no entity body. Its faithful real "
                      "counterpart is the unchanged repo, which the F2P test — a "
                      "body-less request on a no-body method asserting NO size is "
                      "announced — refutes directly. It would NOT resolve; this is "
                      "the precise change the spec senses (G-DIFF).",
        "rationale": "REJECT from `out = announcedSize payload carriesBody` on the "
                     "decision (D): for an absent payload with `carriesBody = "
                     "false` the post-image demands `none` but the rival announces "
                     "`some 0`. Refuted at exactly that point — the F2P "
                     "discriminator — varying `carriesBody` to false against the "
                     "over-correction rival's true.",
        "witness": _witness("contentLengthTester .absent false"),
    },
    {
        "id": "weak-overcorrect-never-announce",
        "kind": "uniqueness",
        "expect": "reject",
        # The DUAL over-correction: in the absent case announce NOTHING
        # unconditionally, ignoring `carriesBody`. Correct on the F2P (no-body
        # method) arm, but wrong on the body-carrying arm, where the gold
        # contract pins a zero-size announcement.
        "module": _impl(
            "    let out : Option Nat :=\n"
            "      match payload with\n"
            "      | .seekable   n => some n\n"
            "      | .measurable n => some n\n"
            "      | .absent       => none\n"
            "    return out"),
        "refinement": "over-correction: a body-less request NEVER announces a "
                      "size, even for a method that conventionally carries an "
                      "entity body. The gold contract pins `some 0` on that arm "
                      "(`announcedSize .absent true`), so a faithful patch "
                      "dropping it produces observably different wire behaviour "
                      "from gold on a body-carrying method with no payload. The "
                      "shipped F2P set exercises only the no-body arm, so this is "
                      "not the F2P discriminator — it is a SPEC-TOO-WEAK probe "
                      "guarding the gold-pinned `carriesBody = true` sub-domain "
                      "and varying that binder; the spec (faithful to gold, "
                      "G-CONF) correctly rejects it.",
        "rationale": "REJECT from `out = announcedSize payload carriesBody` on the "
                     "decision (D, dual): for an absent payload with `carriesBody "
                     "= true` the post-image demands `some 0` but the rival "
                     "announces `none`. Refuted at that point, varying "
                     "`carriesBody` to true against the prepatch rival's false — "
                     "this rival carries its own separating input.",
        "witness": _witness("contentLengthTester .absent true"),
    },
    {
        "id": "weak-drop-present-size",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE rival (V): the absent-case decision is kept exactly right (frozen
        # arm verbatim), but a present, positionable payload announces NOTHING
        # instead of its measured size. Built to abuse `payload`, the binder the
        # decision rivals hold at `absent`.
        "module": _impl(
            "    let out : Option Nat :=\n"
            "      match payload with\n"
            "      | .seekable   n => none\n"
            "      | .measurable n => some n\n"
            "      | .absent       => if carriesBody then some 0 else none\n"
            "    return out"),
        "refinement": "a present, positionable payload announces NOTHING instead "
                      "of its measured size. The gold contract pins `some n` for "
                      "such a payload (`announcedSize (.seekable n) _`), so a "
                      "faithful patch that failed to attach the size drops the "
                      "Content-Length of a request that DOES carry a payload — "
                      "observably different from gold. The shipped tests do not "
                      "assert the announced VALUE, so this is not the F2P "
                      "discriminator; it is a SPEC-TOO-WEAK probe guarding the "
                      "present-payload value behaviour (V) and varying the "
                      "`payload` binder the decision rivals hold at `absent`. The "
                      "spec (faithful to gold, G-CONF) correctly rejects it.",
        "rationale": "REJECT from `out = announcedSize payload carriesBody` on the "
                     "value (V): for `payload = .seekable n` the post-image "
                     "demands `some n` but the rival announces `none`. Refuted at "
                     "`.seekable 3` with `carriesBody = true` — the sub-domain "
                     "where this rival is wrong and both absent-case rivals are "
                     "correct, and the only reject witness that moves `payload` "
                     "off `absent`.",
        "witness": _witness("contentLengthTester (.seekable 3) true"),
    },
    {
        "id": "weak-measurable-collapse-size",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE rival (V), second present shape. Added by audit: before this case
        # the `measurable` constructor was the ONE arm of `Payload` no rival
        # touched — the two decision rivals hold `payload` at `.absent` and the
        # value rival attacks `.seekable` only. A wrong impl confined to the
        # in-memory-payload arm would therefore have gone uncaught by the whole
        # battery, which is precisely the sub-domain gap attack D looks for. Here
        # a directly-measurable payload announces a ZERO size instead of its
        # measured size, so the defect is confined to that arm: both absent-case
        # rivals and the `.seekable` value rival are correct at this input, and
        # this rival is correct at all three of THEIR inputs.
        "module": _impl(
            "    let out : Option Nat :=\n"
            "      match payload with\n"
            "      | .seekable   n => some n\n"
            "      | .measurable n => some 0\n"
            "      | .absent       => if carriesBody then some 0 else none\n"
            "    return out"),
        "refinement": "a present, directly-measurable (in-memory) payload "
                      "announces a ZERO size instead of its measured size. The "
                      "gold contract pins `some n` for such a payload "
                      "(`announcedSize (.measurable n) _`), so a faithful patch of "
                      "this shape announces zero bytes for a request that does "
                      "carry a non-empty in-memory payload — observably different "
                      "from gold on the wire, and a truncated-body report to any "
                      "peer that trusts the announcement. The shipped tests do not "
                      "assert the announced VALUE on this arm, so this is not the "
                      "F2P discriminator; it is a SPEC-TOO-WEAK probe guarding the "
                      "in-memory-payload value behaviour, the one `Payload` "
                      "constructor no other rival varies. The spec (faithful to "
                      "gold, G-CONF) correctly rejects it.",
        "rationale": "REJECT from `out = announcedSize payload carriesBody` on the "
                     "value (V), second present shape: for `payload = .measurable "
                     "n` the post-image demands `some n` but the rival announces "
                     "`some 0`. Refuted at `.measurable 5` with `carriesBody = "
                     "true` — an input at which every other rival in this battery "
                     "is CORRECT, so the case is not a re-spelling of one of them. "
                     "The frozen obligation's residual goal for this rival is the "
                     "concrete value clash `0 = size✝`, i.e. the ensures caught the "
                     "announced number, not the impl's shape.",
        "witness": _witness("contentLengthTester (.measurable 5) true"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness) plus an empty AXIOM lane. The sibling
# models `announce_body_size` over a MUTABLE header dict at full permission, with
# `method` an immutable int and the GET/HEAD tokens as constant @Pure identity
# tokens, and a rich multi-clause postcondition (size pins per branch, a
# GET/HEAD-vs-other discriminator, a `headers[size]==0` clause, two whole-map
# frame clauses, and `method == Old(method)`). This backend models only the
# purely functional announcement DECISION: `contentLength (payload) (carriesBody)`
# returning `Option Nat`, with the whole outcome pinned by the single ensures
# `out = announcedSize payload carriesBody`. The decision surface carries across
# intact; the header MAP, the fractional permissions, the frame clauses, and the
# separate GET/HEAD tokens do not exist here (carrier narrowing).
#
#   sibling case                    -> here                               disposition
#   -------------------------------------------------------------------------------
#   pos-control-reordered           -> pos-branch-reorder                 PORTED (reshaped)
#   echo-honest                     -> pos-two-stage-option                RE-EXPRESSED
#   admiss-bodyless-get             -> admiss-f2p-point-satisfiable        RE-AIMED
#   rival-prepatch-unconditional    -> weak-prepatch-always-announce      PORTED (U1)
#   rival-drop-method-guard         -> (folds into weak-prepatch-...)     COLLAPSED
#   partial-domain-head-only        -> (none)                             VACUOUS (carrier)
#   rival-wrong-stream-value        -> weak-drop-present-size             PORTED (re-expr.)
#   rival-extra-header-smuggle      -> (none)                             VACUOUS (frame)
#   (no sibling)                    -> weak-overcorrect-never-announce    ADDED (binder cov.)
#   (no sibling)                    -> weak-measurable-collapse-size      ADDED (audit, arm cov.)
#
# 3 ported (1 collapsed into another), 1 re-expressed positive, 1 re-aimed
# admissibility, 2 vacuous; 2 coverage rivals added (1 binder, 1 audit-added arm).
#
# AUDIT REVISIONS (independent re-derivation of this port; all claims below were
# re-measured with real builds, not argued):
#   * `pos-let-binding` -> `pos-two-stage-option`. The old positive hoisted the
#     absent-branch value into a `let` and referenced it in the absent arm, which
#     is a zeta-reduction of the frozen body: a function-level `rfl` between the
#     two shapes ELABORATES (exit 0), so the variant was definitionally the
#     frozen impl and could not witness SPEC-TOO-STRONG. The replacement stages
#     the decision through an intermediate `Option`, and the same `rfl` probe
#     FAILS on it (exit 1) while the frozen proof script still closes it (exit 0)
#     — a positive that tests something.
#   * `admiss-absent-fork-nondegenerate` -> `admiss-f2p-point-satisfiable`. The
#     old case asserted only that the fork separates its arms, which is not the
#     direction PRECOND-TOO-STRONG lives in: it says nothing about the obligation
#     being SATISFIABLE at the F2P-shaped input. The replacement discharges the
#     post-image AT that input by evaluation (`announcedSize .absent false =
#     none`) and keeps the non-degeneracy conjunct. The assert VC is live: the
#     same case with a FALSE first conjunct fails (exit 1, `assert_1 ... ⊢ False`).
#   * `weak-measurable-collapse-size` ADDED. The `.measurable` arm was the one
#     `Payload` constructor no rival varied, so a wrong impl confined to it would
#     have gone uncaught. Rival exit 1 (residual goal `0 = size✝`), witness exit 0
#     on the rival / 1 on gold, flipped-claim forgery 0 on gold / 1 on the rival.
#
# COLLAPSED (rival-drop-method-guard): the sibling's U1 (leading unconditional
#   write) and U2 (announce zero via an unguarded else) are two distinct impl
#   SHAPES with the SAME observable defect — a body-less GET/HEAD carries
#   Content-Length==0. On this carrier the GET/HEAD distinction is the single
#   boolean `carriesBody` and the announcement is a single `Option Nat`, so both
#   shapes reduce to the ONE rival `absent => some 0` (ignore `carriesBody`).
#   Porting both would ship the identical variant twice; U2 is folded into
#   `weak-prepatch-always-announce`.
# VACUOUS (partial-domain-head-only): the sibling guards `method != GET` but
#   forgets HEAD, correct on GET yet wrong on HEAD. This backend abstracts the
#   entire method-property distinction into ONE boolean `carriesBody`
#   (mapping.md §2.1): there is no separate HEAD token to mishandle
#   independently, so a rival that decided the fork from `carriesBody` alone but
#   wrongly for one underlying method has no counterpart. Carrier narrowing, not
#   an evasion; no substitute is fabricated.
# VACUOUS (rival-extra-header-smuggle): the sibling injects an unrelated key into
#   the mutable header map, caught by a whole-map frame clause. This backend
#   returns a single `Option Nat` (the announced size), declares no `mut` binder,
#   and has no heap or aliasing — there is no map to smuggle a key into and no
#   frame clause to violate. Referentially transparent; the class is vacuous. The
#   sibling's absence of a read-only (Acc(.,1/2)) input and its
#   `method==Old(method)` clause are likewise permission/heap artifacts with no
#   counterpart here.
# RE-AIMED (admissibility): the sibling's admissibility probe self-calls on an
#   F2P-shaped input to check the precondition (dict_pred, size-header absent,
#   Implies(seekable, body_present)) is establishable. This backend's method has
#   no `require` to establish, but the lane is NOT vacuous: the analogue on a
#   total-domain carrier is the obligation being UNSATISFIABLE at exactly an
#   F2P-shaped input, since a post-image demanding the unreachable there would be
#   discharged by no impl at all and the resulting universal rejection would read
#   as a strong spec. So the probe discharges the post-image at that concrete
#   input by evaluation, as an in-region `assert`, before closing the frozen
#   obligation verbatim (`announcedSize .absent false = none` — the F2P point
#   demands that NOTHING be announced, and that is reachable), and additionally
#   keeps the non-degeneracy claim that the absent-case fork separates its two
#   outcomes (`announcedSize .absent true ≠ announcedSize .absent false`).
# RE-EXPRESSED (pos-two-stage-option): the sibling's `echo-honest` keeps the gold
#   impl and asserts the decision table holds, to show the spec is not
#   echo-vulnerable (the @Pure tokens are constants, not an answer key). This
#   backend's post-image is likewise grounded (a concrete `def` over the inputs,
#   empty axioms region), so there is no wrong echo either; the point is
#   re-expressed as a reshape positive that stages the decision through an
#   intermediate `Option` — a control-flow reshape axis (the absent/present split
#   moves from the `Payload` constructor to an `Option` scrutinee), and a second
#   correct impl shape that is verified NOT definitionally equal to the frozen
#   body, so the frozen proof has to re-derive the equality rather than close by
#   reflexivity.
# ADDED (weak-overcorrect-never-announce): the sibling's rivals all attack the
#   `carriesBody = false` (GET/HEAD) arm; none attacks the body-carrying arm,
#   where the sibling's clause (4) pins `headers[size]==0`. Here that arm is
#   `announcedSize .absent true = some 0`, an independent behaviour of the sole
#   clause with the free input `carriesBody` held at `true`. A battery whose every
#   reject rival held `carriesBody = false` would never demonstrate the spec's
#   dependence on it (a rival mishandling only the true arm would go uncaught), so
#   this rival drops the zero on the body-carrying arm — refuted at `.absent true`.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the two input binders of
#   the sole ensures (pts = 4 distinct input points):
#     payload     — `.absent` (prepatch), `.absent` (over-correct),
#                   `.seekable 3` (drop-present-size), `.measurable 5`
#                   (measurable-collapse): ALL THREE constructors of `Payload`
#                   reached — never held fixed, and no arm left unattacked.
#     carriesBody — false (prepatch), true (over-correct), true (drop-present),
#                   true (measurable-collapse): both arms of the boolean
#                   exercised — never held fixed.
#   Both independent behaviours of the post-image are attacked: the absent-case
#   DECISION in BOTH directions (prepatch announces when it must not / over-correct
#   omits when it must not) and the present-payload VALUE on BOTH present shapes
#   (drop-present-size on `.seekable`, measurable-collapse on `.measurable`).
#   The four points are mutually discriminating, not re-spellings: each rival is
#   CORRECT at the other three rivals' witness inputs, so no case's rejection is
#   implied by another's.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom and no deep-model reference (`announcedSize` is an I-op checked by
# G-CONF), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
