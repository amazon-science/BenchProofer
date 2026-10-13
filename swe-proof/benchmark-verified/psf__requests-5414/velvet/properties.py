"""properties.py — G-PBT falsification battery for psf__requests-5414 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct validateAsciiHostLabel`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  validateAsciiHostLabel (host : List Char) return (out : Bool)
    require host.length > 0
    require isAsciiHost host = true
    ensures out = hostAccepted host

The method decides, along the all-ASCII handling path, whether a host is
accepted (return ``true``) or rejected (return ``false``). Both ``require``
clauses SCOPE the decision: the host reaching it is non-empty and entirely in
the 7-bit range — the code-point sub-domain this branch governs. The single
load-bearing ``ensures`` pins ``out`` to the fully-unfolded pure predicate
``hostAccepted host`` (the ``axioms`` region is empty — there is no opaque answer
key to echo):

    hostAccepted host = !(host.head? == some '*' || host.head? == some '.')

i.e. accept exactly when the host does NOT open with the wildcard (U+002A) or
the separator (U+002E); reject otherwise. This is a BICONDITIONAL over one input
feature — the leading code point — with three independently-attackable facets:
reject the wildcard head, reject the separator head, and accept every other
head.

SINGLE INPUT BINDER: ``host`` (``List Char``). Its behaviourally-relevant
feature is ``host.head?`` under the ``length > 0`` / ``isAsciiHost`` scope. The
reject witnesses drive ``host`` to FIVE distinct inputs — separator head,
wildcard head, ordinary head, an ordinary head with a separator in the BODY, and
an ordinary head with a WILDCARD in the body — so the manifest demonstrates the
post-image's dependence on the leading code point in BOTH directions of the
biconditional (reject-when-must-reject and accept-when-must-accept) AND that the
tested POSITION is load-bearing SEPARATELY FOR EACH of the two needle code
points, not on a single pinned shape (pts = 5). The first three are all length-1
hosts, on which a head test and a whole-host membership test coincide; the fourth
separates them for the separator needle and the fifth for the wildcard needle.
The fifth is not redundant: a rival that screens the head for one needle and the
whole host for the OTHER agrees with the spec at all four of the other points, so
it survives a battery that pins the two facets only jointly (measured — see
``weak-mixed-position``).

CARRIER NOTE — THE DECIDABLE BOUNDARY. The whole spec is transparent (``pure``
helpers over the method's own argument; no opaque callee), so a witness reaches
the post-image through Velvet's own tester machinery
(``validateAsciiHostLabelTester host = false`` says the extracted program's
result violates the postcondition at that concrete input) and closes by
``decide``, checked in a file whose ``prove_correct`` block has been stripped so
no tactic script can mask the verdict. Every argument is a concrete ``"…".toList``
literal that satisfies BOTH require clauses (non-empty, all-ASCII), so ``decide``
reduces the extracted rival program (a loop-free head-inspection) and the
concrete precondition/postcondition instances without getting stuck. Both halves
of every reject witness were confirmed out-of-band with
``scripts/lean_verify.sh``: each ELABORATES green against its rival (proof
stripped, exit 0) and FAILS against the frozen solution (exit 1, "``decide``
proved … is false"), so it is a real discriminator, not a tautology. The
gold-side failure is a PLAIN EVALUATION — the kernel reduced the tester and found
the claim false — and it carries information about the claim, confirmed by
building the FLIPPED claim on both sides: asserting ``… = true`` instead of ``…
= false`` inverts both exit codes (gold 0, rival 1) for all five cases, so no
gold-side exit code is a constant of the file. No witness binds a hypothesis
(every input is a concrete literal that decides the clause), so no consistency
probe is needed.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (return the grounded predicate directly; and a
    let-staged form that keeps the frozen proof) must verify, else the spec is
    SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — APPLIES with teeth here (unlike the referentially-transparent
    siblings with no ``require``). This method DOES carry a precondition; the
    residual admissibility risk is a DEGENERATE post-image (a spec every impl
    trivially meets reads like one no impl violates). ``admiss-nondegenerate``
    discharges an in-region ``assert`` pinning three genuinely distinct outcomes
    (accept an ordinary head, reject the wildcard head, reject the separator
    head); the surrounding impl is kept verbatim so the method's own obligation
    still discharges.
  * FRAME-MUTATION — VACUOUS on this backend. The sibling carries a MANDATORY
    frame-mutation rival because the host is held at a fractional heap permission
    (``Acc(.,1/2)``) an impl can illegally overwrite. Lean/Velvet are
    referentially transparent: ``host`` is an immutable ``List Char`` value
    declared read-only (not ``mut``), there is no heap, aliasing, ``Old``, or
    permission system. There is no read-only input to overwrite and no frame
    clause to violate, so the class has no carrier analogue; NOT ported
    (fabricating a substitute would test nothing).
  * DIVERGENCE / NON-TERMINATION — CLOSED BY THE SPEC on this bundle, and NOT a
    hole. This bundle runs under ``set_option loom.semantics.termination
    "total"``, so the divergence class the sibling closes with MustTerminate(2)
    is closed here by total-correctness semantics: both sibling rivals are
    REJECTED outright. Measured with real builds — a bare self-call
    (``let r ← validateAsciiHostLabel host; return r``) is rejected with "fail to
    show termination for validateAsciiHostLabel … no parameters suitable for
    structural recursion", and an unbounded ``while true do`` is rejected with
    "Decreasing annotations are required in total correctness semantics". Neither
    can be SHIPPED as a reject case, however, because the refutation witness must
    ELABORATE against the rival: the witness file retains the rival's impl, so the
    same termination error fires in the witness build (rival exit 1 for both), and
    a reject case whose witness does not hold of its rival is
    ``witness-unproven`` — inconclusive, which the gate scores as an error rather
    than a pass. So the class is genuinely unshippable HERE, but for a
    tooling/witness-shape reason and with the spec on the RIGHT side of the
    verdict. (An earlier version of this bullet placed the bundle in a ``total``
    cohort against a larger ``partial`` one, citing an internal findings doc for the
    opposite disposition. That census is withdrawn: all 500 velvet bundles set
    ``"total"``, and the ``set_option`` elaborator itself runs
    ``openScope `TotalCorrectness`` (``Loom/MonadAlgebras/WP/Options.lean``, lines
    169-186), so the option and the ``open`` cannot disagree and no cohort exists.)
  * UNGROUNDED-ORACLE ECHO — N/A. ``hostAccepted`` is a fully-unfolded ``def``
    over the method's own argument; there is no answer-key term a wrong impl
    could echo. The cheapest correct impl computes the membership test honestly,
    which the positive controls cover.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: the pre-patch shape
    (reject the wildcard only), its mirror (reject the separator only), and an
    over-rejection rival (reject an ordinary head too) — each right on most of
    the domain yet diverging on one leading-code-point sub-domain.
"""
from pathlib import Path

INSTANCE = "psf__requests-5414"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE gold impl block (between and INCLUDING the markers): a single
# ---- anchor lying wholly inside the impl region and unique in the file (both
# ---- facts asserted at load). Every reject rival and each positive swap on
# ---- this block, so each edit stays inside the one impl region and same_spec
# ---- holds by construction.
_IMPL = """    -- impl-start
    -- Reject iff the host opens with an invalid leading label, i.e. its first
    -- code point is the wildcard `*` or the separator `.`; accept otherwise.
    let startsBad : Bool := host.head? == some '*' || host.head? == some '.'
    return !startsBad
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the frozen proof body (tactic script only; elided from the spec view).
_PROOF_GOLD = "prove_correct validateAsciiHostLabel by\n  loom_solve"
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"


def _rewrite_impl(new_block, proof=_PROOF_GOLD):
    """Full variant: whole impl block replaced; proof left as the frozen script
    unless overridden (the reshaped correct impls all discharge under
    `loom_solve`)."""
    return _swap(_swap(_BASE, _IMPL, new_block), _PROOF_GOLD, proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `validateAsciiHostLabelTester host = false` says the extracted program's
# ---- result violates the method's postcondition at that concrete input.
# ---- Checked in a file whose `prove_correct` block is stripped. Every argument
# ---- is a concrete literal satisfying BOTH require clauses (non-empty,
# ---- all-ASCII), so `decide` reduces the (loop-free) extracted rival program
# ---- and the concrete pre/postcondition instances without getting stuck.
def _witness(call):
    return ("\n"
            "extract_program_for validateAsciiHostLabel\n"
            "prove_precondition_decidable_for validateAsciiHostLabel\n"
            "prove_postcondition_decidable_for validateAsciiHostLabel\n"
            "derive_tester_for validateAsciiHostLabel\n\n"
            f"example : {call} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Both discharge under the frozen `prove_correct … by
    # loom_solve` script.
    # =====================================================================
    {
        "id": "pos-control-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded pure predicate
        # directly, no intermediate `let` binding — maximally structurally
        # different from the gold two-step form. `out` IS `hostAccepted host`, so
        # the ensures holds trivially and the frozen `loom_solve` still closes it.
        # Doubles as the honest no-ungrounded-echo control: `hostAccepted` is a
        # fully-unfolded def over the argument, so returning it is the real work,
        # not a cheat — any WRONG head-decision fails `out = hostAccepted host`.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return hostAccepted host\n"
            "    -- impl-end"),
        "rationale": (
            "the cheapest honest correct impl returns the grounded predicate "
            "`hostAccepted host` directly. `out` IS that predicate, so the ensures "
            "holds on the whole scoped domain; the reproof is the frozen "
            "`loom_solve`. If this fails to verify the spec is over-fit to the "
            "two-step `let startsBad; return !startsBad` shape (SPEC-TOO-STRONG). "
            "Re-expresses the sibling's honest-inline-oracle positive: the helper "
            "is the real work, so a direct return is correct, not an echo."),
    },
    {
        "id": "pos-control-let-head",
        "kind": "soundness",
        "expect": "verify",
        # Stage the leading code point into a typed local `h` before the
        # membership test — same value flow (`h = host.head?`), different source
        # shape. Keeps the frozen proof (definitionally equal to gold).
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let h : Option Char := host.head?\n"
            "    let startsBad : Bool := h == some '*' || h == some '.'\n"
            "    return !startsBad\n"
            "    -- impl-end"),
        "rationale": (
            "a correct impl with a DIFFERENT source shape (bind the leading code "
            "point to a typed local before the membership test) must verify; the "
            "value flow is unchanged (`h = host.head?`) so `out = hostAccepted "
            "host` still discharges and the frozen `loom_solve` closes it. "
            "Re-shapes the sibling's branch-reorder positive to this carrier "
            "(the impl has no branch chain to reorder — the decision is a single "
            "disjunction). If it fails => SPEC-TOO-STRONG (over-fit to the inline "
            "code form)."),
    },

    # =====================================================================
    # ADMISSIBILITY — this method DOES carry a `require` (host non-empty AND
    # all-ASCII), so the precondition is not vacuous; the residual admissibility
    # risk is a DEGENERATE post-image — a spec no impl distinguishes reads like
    # one every impl meets. This case discharges an in-region `assert`, at three
    # fully concrete inputs, that the post-image is NON-DEGENERATE: an ordinary
    # head is accepted (`true`), the wildcard head is rejected (`false`), and the
    # separator head is rejected (`false`) — three distinct outcomes exercising
    # both directions of the biconditional. The surrounding impl is kept verbatim
    # so the method's own obligation still discharges; the proof gains a `decide`
    # arm to clear the assert goal.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    assert (with_name_prefix `admiss (\n"
            '      (".host.test".toList.length > 0 ∧ isAsciiHost ".host.test".toList = true\n'
            '        ∧ hostAccepted ".host.test".toList = false) ∧\n'
            '      ("*host.test".toList.length > 0 ∧ isAsciiHost "*host.test".toList = true\n'
            '        ∧ hostAccepted "*host.test".toList = false) ∧\n'
            '      ("host.test".toList.length > 0 ∧ isAsciiHost "host.test".toList = true\n'
            '        ∧ hostAccepted "host.test".toList = true)))\n'
            "    -- Reject iff the host opens with an invalid leading label, i.e. its first\n"
            "    -- code point is the wildcard `*` or the separator `.`; accept otherwise.\n"
            "    let startsBad : Bool := host.head? == some '*' || host.head? == some '.'\n"
            "    return !startsBad\n"
            "    -- impl-end",
            "prove_correct validateAsciiHostLabel by\n  loom_solve\n  all_goals decide"),
        "rationale": (
            "PRECOND-TOO-STRONG probe in the shape a total carrier admits: at each "
            "of three CONCRETE realistic multi-label hosts, discharge BOTH require "
            "clauses (`length > 0` AND `isAsciiHost … = true`) by evaluation AND the "
            "post-image value there, before closing the frozen obligation verbatim. "
            "So the precondition is satisfiable at exactly the input shapes this "
            "decision governs — not merely at a one-code-point host — and the "
            "post-image is non-degenerate on them: a separator-leading host is "
            "REJECTED, a wildcard-leading host is REJECTED, and an ordinary "
            "multi-label host is ACCEPTED. Three distinct outcomes, both directions "
            "of the biconditional. If the requires were jointly unsatisfiable at a "
            "realistic host, or the post-image constant, the assert would not "
            "discharge => PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE / degenerate. "
            "Re-aims the sibling's F2P-shaped-precondition admissibility (its "
            "fractional-permission half has no analogue here). Liveness measured: "
            "flipping any single conjunct — the accept outcome, or an `isAsciiHost` "
            "claim — makes this case FAIL to build, so the assert is load-bearing "
            "rather than decoration."),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-reject-wildcard-only",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-change behaviour: reject ONLY the wildcard head, letting a host
        # that opens with the separator through. Correct on every non-separator
        # head; diverges exactly on a separator-leading host — the F2P
        # discriminator.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let startsBad : Bool := host.head? == some '*'\n"
            "    return !startsBad\n"
            "    -- impl-end"),
        "refinement": (
            "this is the pre-change decision: reject only the wildcard-leading "
            "host, accept a separator-leading one. Its faithful real patch is the "
            "unpatched guard, which accepts a host that opens with the separator; "
            "the failing test drives exactly such a host and asserts it is "
            "rejected as an invalid URL, which this impl does not do, so it would "
            "NOT resolve. This is precisely the defect the widening fixes."),
        "rationale": (
            "REJECT from `out = hostAccepted host` via the separator facet: the "
            "spec requires reject (`out = false`) when the host opens with the "
            "separator, but this rival accepts it (`out = true`). Verifying would "
            "be SPEC-TOO-WEAK (admits the bug). Refuted at a separator-leading "
            "host (`\".\"`) — where the spec rejects and the rival accepts."),
        "witness": _witness('validateAsciiHostLabelTester ".".toList'),
    },
    {
        "id": "weak-reject-separator-only",
        "kind": "uniqueness",
        "expect": "reject",
        # The mirror miss: reject ONLY the separator head, letting a
        # wildcard-leading host through. Correct on every non-wildcard head;
        # diverges exactly on a wildcard-leading host — a P2P the fix must
        # preserve.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let startsBad : Bool := host.head? == some '.'\n"
            "    return !startsBad\n"
            "    -- impl-end"),
        "refinement": (
            "the mirror miss: reject only the separator-leading host, accept a "
            "wildcard-leading one. A faithful real patch of this shape would "
            "accept a host that opens with the wildcard and thus fail the "
            "pass-to-pass test that drives such a host and requires it be rejected "
            "as an invalid URL (and regress the legacy wildcard rejection), so it "
            "would NOT resolve."),
        "rationale": (
            "REJECT from `out = hostAccepted host` via the wildcard facet: the "
            "spec requires reject (`out = false`) when the host opens with the "
            "wildcard, but this rival accepts it (`out = true`). Verifying would "
            "be SPEC-TOO-WEAK. Refuted at a wildcard-leading host (`\"*\"`) — a "
            "DISTINCT input point from the wildcard-only rival (different leading "
            "code point), so the two do not collapse to one probed point and the "
            "battery varies the leading-code-point feature of `host`."),
        "witness": _witness('validateAsciiHostLabelTester "*".toList'),
    },
    {
        "id": "weak-over-reject",
        "kind": "uniqueness",
        "expect": "reject",
        # The over-rejection direction: reject EVERY host, including one whose
        # leading code point is ordinary and must be accepted. Correct on the two
        # invalid heads (wildcard, separator) — it rejects them, as required — but
        # wrong on every valid head. Attacks the ACCEPT branch of the
        # biconditional, which the two under-rejection rivals above leave untested.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return false\n"
            "    -- impl-end"),
        "refinement": (
            "rejecting every host means a faithful real patch would signal an "
            "invalid-URL condition on the all-ASCII branch for ordinary hosts "
            "too, so a request to an ordinary host (e.g. a plain domain) would "
            "raise instead of proceeding; every pass-to-pass test that prepares a "
            "valid ordinary URL would fail, so it would NOT resolve. Correct only "
            "on the two invalid-head sub-domains (a genuine partial-domain break "
            "in the accept direction)."),
        "rationale": (
            "REJECT from `out = hostAccepted host` via the ACCEPT facet: when the "
            "host opens with an ordinary code point the spec requires accept "
            "(`out = true`), but this rival returns `false`. Verifying would be "
            "SPEC-TOO-WEAK (the acceptance side of the biconditional left "
            "unpinned — the direction neither the wildcard-only nor "
            "separator-only rival exercises, since both are correct on ordinary "
            "heads). Refuted at an ordinary-leading host (`\"a\"`) — a third "
            "distinct leading code point, so pts=3 and no head-class is left "
            "unattacked."),
        "witness": _witness('validateAsciiHostLabelTester "a".toList'),
    },
    {
        "id": "weak-needle-anywhere",
        "kind": "uniqueness",
        "expect": "reject",
        # POSITIONAL confusion: reject when either needle code point occurs
        # ANYWHERE in the host, not just at its head. This rival agrees with the
        # spec on EVERY single-code-point host, so the three rivals above — whose
        # witnesses all drive length-1 hosts — leave it completely unattacked. It
        # is wrong on any host that merely CONTAINS a separator away from the head,
        # which is the overwhelmingly common shape of a real host. Refuted at a
        # multi-code-point host whose leading code point is ordinary but whose body
        # holds a separator: the spec accepts it, this rival rejects it. This is
        # what pins the decision to `head?` rather than to membership, i.e. it is
        # the case that makes the POSITION of the tested code point load-bearing.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return !(host.any (fun c => c == '*' || c == '.'))\n"
            "    -- impl-end"),
        "refinement": (
            "a faithful real patch of this shape screens the whole host for the "
            "two code points instead of screening its leading label. Every "
            "ordinary multi-label host contains a separator, so such a patch "
            "signals an invalid-URL condition for essentially every request; the "
            "pass-to-pass tests that prepare a valid multi-label URL and expect it "
            "to proceed would all fail, so it would NOT resolve. It happens to "
            "agree with the intended decision on the failing test's input and on "
            "the wildcard input, which is exactly why a battery that only probes "
            "one-code-point hosts cannot see it."),
        "rationale": (
            "REJECT from `out = hostAccepted host` via the POSITION of the tested "
            "code point: the spec reads `host.head?` only, so a host whose leading "
            "code point is ordinary must be ACCEPTED (`out = true`) however many "
            "separators its body contains; this rival returns `false` for it. "
            "Verifying would be SPEC-TOO-WEAK — it would mean the ensures pins "
            "only WHICH code points are invalid and not WHERE they must appear. "
            "Refuted at a host with an ordinary head and a separator in its body "
            "(`\"a.b\"`), a fourth distinct input point and the first with length "
            "> 1, so the reject set no longer pins host length to 1."),
        "witness": _witness('validateAsciiHostLabelTester "a.b".toList'),
    },
    {
        "id": "weak-mixed-position",
        "kind": "uniqueness",
        "expect": "reject",
        # SPLIT-POSITION confusion, and the one rival none of the four above can
        # see. It screens the HEAD for the separator (matching the spec on that
        # facet exactly) but the WHOLE host for the wildcard. So it agrees with
        # the spec at every one of the four preceding witness points — the three
        # length-1 hosts, and "a.b" (ordinary head, separator in the body, which
        # it ACCEPTS just as the spec does, because its separator test is a head
        # test). It diverges only on a host whose leading code point is ordinary
        # and whose BODY holds a wildcard: the spec accepts, this rival rejects.
        # It demonstrates that the POSITION facet must be pinned once PER NEEDLE
        # code point, not once jointly for both.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return !(host.head? == some '.' || host.any (fun c => c == '*'))\n"
            "    -- impl-end"),
        "refinement": (
            "a faithful real patch of this shape screens the leading label for "
            "the separator but the whole host for the wildcard. Any ordinary "
            "host that merely contains a wildcard anywhere would then be "
            "signalled as an invalid-URL condition instead of proceeding, so a "
            "pass-to-pass test that prepares such a URL and expects it to be "
            "prepared normally would fail; it would NOT resolve. It happens to "
            "agree with the intended decision on the failing test's input, on "
            "the wildcard-leading input, and on an ordinary multi-label host "
            "with a separator in its body — which is exactly why the four "
            "rivals above cannot see it."),
        "rationale": (
            "REJECT from `out = hostAccepted host` via the POSITION facet of the "
            "WILDCARD needle specifically: the spec reads `host.head?` for BOTH "
            "code points, so a host with an ordinary leading code point must be "
            "ACCEPTED (`out = true`) however many wildcards its body contains; "
            "this rival returns `false` for it. Verifying would be "
            "SPEC-TOO-WEAK — it would mean the ensures pins the tested position "
            "for the separator only and leaves it free for the wildcard, i.e. "
            "the two facets could be satisfied by two different positional "
            "readings. Refuted at a host with an ordinary head and a wildcard "
            "in its body (`\"a*b\"`), a FIFTH distinct input point: it is the "
            "first that the head-vs-membership rival `weak-needle-anywhere` "
            "does not already cover, because that rival is wrong at \"a.b\" "
            "while this one is right there."),
        "witness": _witness('validateAsciiHostLabelTester "a*b".toList'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 10 SPEC cases (2
# soundness positives, 1 admissibility, 7 uniqueness rivals — one a MANDATORY
# frame-mutation rival, two divergence rivals) plus an axiom lane. The sibling
# contracts `screen_host(host, host_is_ascii, encodable)` over the WHOLE
# leading-label screen: the ASCII branch (the changed decision), the non-ASCII
# IDNA-encoder branch (`encode_label`), read-only fractional-permission framing
# on `host`, and a MustTerminate(2) total-correctness obligation. This velvet
# bundle NARROWS the modeled slice to the discriminating core — the ASCII
# leading-label decision ONLY (`validateAsciiHostLabel` / `hostAccepted` /
# `startsWithInvalidLabel`) — scoped by `require isAsciiHost host`; the non-ASCII
# IDNA branch is UNCHANGED by the patch and abstracted away (mapping.md §3.1).
# That carrier narrowing removes the sibling cases attached to the non-ASCII
# encoder path outright and makes the frame class vacuous. It does NOT open a
# divergence hole: this bundle sets `loom.semantics.termination "total"`, so both
# sibling divergence rivals are REJECTED by the spec (measured — see SPEC-CLOSED
# below); they are merely unshippable as reject CASES, for a witness-shape reason.
#
#   sibling case                        kind          -> here                        disposition
#   ---------------------------------------------------------------------------------------------
#   pos-control-reorder                 soundness     -> pos-control-let-head        RE-SHAPED
#   pos-inline-oracle                   soundness     -> pos-control-direct-model    RE-EXPRESSED
#   admissibility-readonly-host         admissibility -> admiss-nondegenerate        RE-AIMED
#   frame-mutation-write-host           uniqueness    -> (none)                      VACUOUS
#   partial-star-only                   uniqueness    -> weak-reject-wildcard-only   PORTED
#   partial-dot-only                    uniqueness    -> weak-reject-separator-only  PORTED
#   control-flow-drop-encoder           uniqueness    -> (none)                      NOT MODELED
#   control-flow-always-raise-nonascii  uniqueness    -> (none)                      NOT MODELED
#   nonterm-self-recursion              uniqueness    -> (none)                      SPEC-CLOSED
#   nonterm-endless-loop                uniqueness    -> (none)                      SPEC-CLOSED
#   (no sibling)                        uniqueness    -> weak-over-reject            ADDED
#   (no sibling)                        uniqueness    -> weak-needle-anywhere        ADDED
#   (no sibling)                        uniqueness    -> weak-mixed-position         ADDED
#   AXIOM_TESTS (2)                     axiom         -> (none)                      N/A (G-AX)
#
# 8 velvet SPEC cases: 2 soundness, 1 admissibility, 5 uniqueness.
#
# RE-SHAPED (pos-control-reorder -> pos-control-let-head): the sibling reorders
#   the if/elif branch chain of `screen_host`. On this carrier the decision is a
#   single boolean disjunction, not a branch chain, so there is no branch order
#   to reorder; the structurally-different-but-correct control instead stages the
#   leading code point into a typed local before the membership test (same value
#   flow, different source shape), which keeps the frozen `loom_solve` proof.
# RE-EXPRESSED (pos-inline-oracle -> pos-control-direct-model): the sibling
#   inlines the @Pure `is_invalid_leading` as its unfolded disjunction. Here the
#   predicate IS the transparent `hostAccepted` and the ensures already IS `out =
#   hostAccepted host`, so the honest cheapest impl is `return hostAccepted host`
#   — the same argument (the grounded pin is satisfiable only by the real
#   head-decision; no wrong echo verifies) as a loop-free correct impl.
# RE-AIMED (admissibility-readonly-host -> admiss-nondegenerate): the sibling
#   re-derives that the half-permission `host` is readable and `len(host)>0` is
#   usable, reaching a normal return. This backend has a real `require` (host
#   non-empty AND all-ASCII) but no permission surface, so the readable-under-
#   half-permission half has no analogue; re-aimed at the residual risk of a
#   DEGENERATE post-image via a live in-region assert pinning three distinct
#   outcomes (accept ordinary head, reject wildcard head, reject separator head).
# PORTED (2): partial-star-only -> weak-reject-wildcard-only (the pre-patch
#   shape: reject only the wildcard head; refuted at a separator-leading host —
#   the F2P discriminator). partial-dot-only -> weak-reject-separator-only (the
#   mirror miss: reject only the separator head; refuted at a wildcard-leading
#   host — a distinct point, the P2P the fix must preserve). Each carries its
#   sibling refinement argument, now backed by a machine-checked witness.
# ADDED (weak-over-reject): the two ported rivals both attack the REJECT
#   direction of the biconditional (accept-when-must-reject) and are both correct
#   on ordinary heads. To attack the ACCEPT direction (reject-when-must-accept)
#   this rival rejects every host; refuted at an ordinary-leading host, a third
#   distinct leading code point. It re-aims the ADVERSARIAL INTENT of the
#   sibling's over-rejection rival (control-flow-always-raise-nonascii, which
#   over-rejects on the UNMODELED non-ASCII branch) onto the modeled ASCII
#   carrier — a real divergence with a machine-checked witness, not a fabricated
#   substitute for the vacuous non-ASCII rival itself.
# VACUOUS (frame-mutation-write-host): the sibling's MANDATORY frame-mutation
#   rival writes to the half-permission `host` (`host[0] = host[0]`) and is
#   rejected for INSUFFICIENT PERMISSION. This backend is referentially
#   transparent: `host` is an immutable `List Char` value declared read-only (not
#   `mut`), there is no heap, aliasing, `Old`, or permission system. There is no
#   read-only input to overwrite and no frame clause to violate, so the class has
#   no carrier analogue. Omitted as a genuine carrier fact, NOT fabricated.
# NOT MODELED (control-flow-drop-encoder, control-flow-always-raise-nonascii):
#   both attack the NON-ASCII IDNA-encoder branch (`encode_label`), which this
#   bundle scopes OUT via `require isAsciiHost host` — the patch does not change
#   that branch (mapping.md §3.1), so it is abstracted away and there is no
#   encoder clause in this bundle's spec for these rivals to violate. Carrier
#   narrowing (the Lean-family bundle models only the changed ASCII decision),
#   NOT an omission for difficulty: the modeled slice is defended and attacked in
#   full. The over-rejection INTENT of always-raise-nonascii is re-aimed onto the
#   ASCII carrier as weak-over-reject (see ADDED).
# SPEC-CLOSED (nonterm-self-recursion, nonterm-endless-loop): the sibling closes
#   the divergence class with a MustTerminate(2) obligation. This bundle sets
#   `set_option loom.semantics.termination "total"`, which closes the same class
#   by semantics: BOTH sibling rivals are REJECTED, measured with real builds.
#   The self-call fails with "fail to show termination for validateAsciiHostLabel
#   … no parameters suitable for structural recursion"; the unbounded loop fails
#   with "Decreasing annotations are required in total correctness semantics". So
#   the spec is on the right side of this verdict and there is no hole to report.
#   Neither is SHIPPABLE as a reject case, though: the witness file retains the
#   rival's impl, so the same termination error fires in the WITNESS build and the
#   rival half exits 1 (measured for both) — a reject case whose witness does not
#   hold of its rival records `witness-unproven`, which is inconclusive and scores
#   as a gate ERROR, not a pass. Unshippable for a witness-shape reason, not
#   because the spec admits the rival. (An earlier version of this entry cited an
#   internal findings doc scoped to a `partial` cohort; that cohort is withdrawn,
#   since all 500 velvet bundles set "total" and the `set_option` elaborator itself
#   runs `openScope `TotalCorrectness`.)
# N/A (AXIOM_TESTS): the sibling's axiom-soundness/containment probes over the
#   real IDNA encoder are G-AX's job (axiom_check.py / mapping.md); the G-PBT gate
#   ignores AXIOM_TESTS regardless. This bundle's `axioms` region is empty
#   (mapping.md §3.2) — the acceptance decision is modeled deeply and the only
#   deep-model reference `isAsciiHost` is a G-AX-checked A-reference.
#
# BINDER / CLAUSE / POINT COVERAGE. The sole `ensures` clause `out = hostAccepted
#   host` is a biconditional over one input feature — `host.head?` under the
#   `length > 0` / `isAsciiHost` scope. It has THREE independently-attackable
#   facets (reject wildcard head, reject separator head, accept ordinary head),
#   each attacked by one reject rival — plus a fourth facet, the POSITION at which
#   the code point is tested, which the first three cannot see, and which must be
#   pinned once PER NEEDLE code point rather than once jointly:
#     * weak-reject-wildcard-only    "."   (separator head — spec rejects, rival accepts)
#     * weak-reject-separator-only   "*"   (wildcard head  — spec rejects, rival accepts)
#     * weak-over-reject             "a"   (ordinary head  — spec accepts, rival rejects)
#     * weak-needle-anywhere         "a.b" (ordinary head, separator in the BODY —
#                                           spec accepts, rival rejects)
#     * weak-mixed-position          "a*b" (ordinary head, WILDCARD in the BODY —
#                                           spec accepts, rival rejects)
#   The sole binder `host` is driven to FIVE distinct input points (pts=5) over
#   three distinct leading code points AND two distinct lengths, covering BOTH
#   directions of the biconditional. The length variation is load-bearing, not
#   cosmetic: the first three witnesses are all length-1 hosts, on which a rival
#   that screens the WHOLE host for the two code points is indistinguishable from
#   the spec, so `head?`-vs-membership was unpinned until weak-needle-anywhere;
#   `host.any` was measured VERIFYING-adjacent (it fails the obligation, exit 1)
#   and its witness discriminates at "a.b". The fifth point is load-bearing for
#   the same reason one step down: with only the first four, a rival that reads
#   `head?` for the separator but the whole host for the WILDCARD agrees with the
#   spec at all four (it accepts "a.b", exactly as the spec does), so the
#   positional facet was pinned only for the separator needle. Measured: that
#   rival fails the obligation (exit 1) and its witness discriminates at "a*b"
#   (rival 0 / gold 1). Both positives and the admissibility case defend the
#   clause on all three outcomes, the latter at realistic multi-label hosts
#   rather than one-code-point ones.
AXIOM_TESTS = []
