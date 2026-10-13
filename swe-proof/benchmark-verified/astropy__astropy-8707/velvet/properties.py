"""properties.py — G-PBT falsification battery for astropy__astropy-8707 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides — so ``markers.same_spec`` holds
and the ``prove_correct`` obligation survives) and swaps in a candidate
implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must elaborate against the rival and FAIL against the
frozen solution).

This bundle is a CARRIER-NARROWED port. The nagini sibling contracts several
functions over an octet-list carrier with fractional-permission framing and a
text-only downstream padding step guarded by a runtime predicate. This backend
models only the purely functional core the graded behavior turns on: ONE method

  buildImage (src)   require (raw octets are all < 256)   ensures out = imageSpec src

over a construction-source carrier that is EITHER a character image already in
hand (``Source.text : List Char``) or a raw octet sequence
(``Source.raw : List Nat``). ``imageSpec`` is the single load-bearing
post-image, total and fully unfolded:

  * a character source is accepted unchanged — its image is the source itself;
  * a raw octet source is ALSO accepted — its image is the per-octet code-point
    interpretation (``codepointsOf``: each octet 0–255 → the character whose
    code point equals that octet, byte-for-byte, no re-encoding).

The only free INPUT BINDER of the post-image is ``src``, which ranges over BOTH
constructors; inside the raw arm the octet list ``b`` is a second axis. The
reject witnesses below vary ``src`` across text AND raw, and vary ``b`` across a
single low octet, a two-octet sequence, and a high (>127) octet — so no rival is
refuted at an input another rival already pins, and every arm of the post-image
is attacked.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * CONTROL-FLOW / raw-acceptance — the load-bearing discriminator. The sibling
    hands a raw octet source to a text-only step that refuses it; here the
    faithful model of that refusal is the raw arm returning the refusal marker
    instead of the decoded image. Attacked by ``weak-raw-refused`` (this IS the
    pre-patch behavior).
  * PARTIAL-DOMAIN / VALUE — the sibling's drop-first-byte and ascii-mask rivals
    both attack the raw arm's VALUE on a sub-domain. Ported as
    ``weak-raw-drops-head`` (right on the empty raw source, one character short
    on any non-empty one) and ``weak-raw-ascii-mask`` (identical to the image on
    octets 0–127, wrong on 128–255 — refuted at a high octet).
  * TEXT-ARM PRESERVATION — a BINDER-COVERAGE addition with no direct sibling
    counterpart on this partition: the post-image's other arm requires a
    character source to pass through UNCHANGED. Every raw-arm rival holds ``src``
    at a ``raw`` value, so none attests that the text arm is constrained.
    ``weak-text-emptied`` abuses the text arm at ``src = Source.text [...]`` so
    that binder constructor is exercised too.
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The sibling's class
    exists because an input may carry a fractional heap permission an impl can
    overwrite. Lean and Velvet are referentially transparent; ``src`` is an
    immutable value (no ``mut`` binder anywhere in this bundle), there is no heap
    and no aliasing, so there is no read-only input to mutate and no substitute
    probe to build. Reported as N/A, not fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image ``imageSpec`` is a total, fully
    unfolded ``def`` of the method's own argument (``codepointsOf`` is a concrete
    front-recursive ``def``; the ``axioms`` region is empty). There is no opaque
    answer key to echo, so no wrong echo to build. Replaced by honest
    cheapest-reshape POSITIVE CONTROLS and one admissibility positive.

WITNESS mechanics. The spec here is a ``method`` contract, not a bare predicate,
so a witness reaches it through Velvet's own tester machinery:
``buildImageTester args = false`` says the extracted program's result violates
the postcondition at that concrete input. It is checked in a file whose
``prove_correct`` block has been stripped, so no tactic script can mask the
verdict. ``prove_precondition_decidable_for`` needs the guard decided per
constructor (``cases src``) and ``prove_postcondition_decidable_for`` needs
``DecidableEq (Except …)``; the preamble supplies both as INSTANCES — no
``axiom``, ``sorry``, ``admit`` or ``native_decide`` is involved, and the frozen
solution rejects every witness all the same.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom`` (the octet→char
interpretation is modeled deeply as an A-reference, validated == the real callee
by G-AX / axiom_check.py, NOT consumed as a contract). There is no
axiom-soundness / axiom-containment obligation to probe here, and the gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-8707"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors (each lies wholly inside the single impl region and
# ---- is unique inside Solution.lean; both facts asserted at load by _swap) ---
# The raw-source arm of the executable: the code-point interpretation of a raw
# octet sequence. This is the load-bearing decision the fix turns on.
_A_RAW = "      | Source.raw  b => Except.ok (codepointsOf b)"
# The character-source arm: a character image already in hand, used unchanged.
_A_TEXT = "      | Source.text s => Except.ok s"
# The whole two-arm decision inside the executable `let`.
_A_MATCH = (
    "      match src with\n"
    "      | Source.text s => Except.ok s\n"
    "      | Source.raw  b => Except.ok (codepointsOf b)"
)
# The whole executable body (used by the inline-return reshape).
_A_BODY = (
    "    let image : Except ImageErr (List Char) :=\n"
    "      match src with\n"
    "      | Source.text s => Except.ok s\n"
    "      | Source.raw  b => Except.ok (codepointsOf b)\n"
    "    return image"
)
# Anchor for inserting an in-region admissibility assert.
_A_LETHEAD = "    let image : Except ImageErr (List Char) :="

# ---- proof-body anchor. A `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view (only the header is kept), so a positive control that
# ---- reshapes the impl may retune its tactic script without touching the spec
# ---- or dropping the obligation.
_T_GOLD = "  loom_solve\n  simp [imageSpec]"
# A total case-split reproof that closes for any arm-reshaped correct impl.
_T_CASES = "  loom_solve\n  cases src <;> simp [imageSpec]"
# A `<;>`-form that discharges the frozen impl PLUS an extra in-region assert.
_T_SEQ = "  loom_solve <;> simp [imageSpec]"


def _swap2(a_old, a_new, t_old, t_new):
    """Reshape the impl region AND retune the tactic body."""
    return _swap(_swap(_BASE, a_old, a_new), t_old, t_new)


# ---- witness preamble. Reaches the method contract through Velvet's tester
# ---- machinery. `DecidableEq (Except …)` and the per-constructor guard
# ---- decision are supplied as INSTANCES (no assumption); the frozen solution
# ---- rejects these witnesses all the same.
_WIT_PRE = (
    "deriving instance DecidableEq for Except\n\n"
    "extract_program_for buildImage\n"
    "prove_precondition_decidable_for buildImage by\n"
    "  all_goals (cases src <;> infer_instance)\n"
    "prove_postcondition_decidable_for buildImage\n"
    "derive_tester_for buildImage\n\n"
)


def _witness(inp):
    return _WIT_PRE + f"example : buildImageTester {inp} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the obligation and only reshapes the
    # executable surface; the post-image is point-wise over an immutable value,
    # so each reproof stays one `cases src` away from the frozen script.
    # =====================================================================
    {
        "id": "pos-arms-reordered",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: the same two-arm decision written raw-source-first. The image
        # produced on each arm is unchanged; only the branch order differs.
        "module": _swap2(
            _A_MATCH,
            "      match src with\n"
            "      | Source.raw  b => Except.ok (codepointsOf b)\n"
            "      | Source.text s => Except.ok s",
            _T_GOLD, _T_CASES,
        ),
        "rationale": "reordering the two arms of the source decision yields the "
                     "same image on both arms, so `out = imageSpec src` still "
                     "holds pointwise; a correct reshape must verify (else "
                     "SPEC-TOO-STRONG on branch order).",
    },
    {
        "id": "pos-inline-return",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the intermediate binding and return the decision
        # directly. Same value flow on both arms.
        "module": _swap2(
            _A_BODY,
            "    return (match src with\n"
            "            | Source.text s => Except.ok s\n"
            "            | Source.raw  b => Except.ok (codepointsOf b))",
            _T_GOLD, _T_CASES,
        ),
        "rationale": "returning the source decision directly instead of through "
                     "an intermediate binding leaves the image on each arm "
                     "unchanged, so `out = imageSpec src` is preserved; must "
                     "verify.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method DOES carry a `require` (raw octets < 256), so
    # the sibling's "a normal input satisfies the precondition" probe is
    # meaningful AND the total-domain residual risk (an UNSATISFIABLE post-image
    # at the interesting point) applies. This case discharges an in-region
    # assert that (a) the guard admits a normal raw source, and (b) the
    # post-image is satisfiable AND non-degenerate at both an F2P-shaped raw
    # source and a character source — the raw octets decode to their code-point
    # image and a character image passes through unchanged. The assert is live:
    # replacing either conjunct with a false claim about the same point leaves an
    # unsolved goal (verified). The surrounding impl is kept verbatim so the
    # method's own obligation still discharges.
    # =====================================================================
    {
        "id": "admiss-image-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap2(
            _A_LETHEAD,
            "    assert (with_name_prefix `assert\n"
            "      ((∀ x ∈ [65, 66, 67], x < 256) ∧\n"
            "       imageSpec (Source.raw [65, 66, 67]) "
            "= Except.ok (codepointsOf [65, 66, 67]) ∧\n"
            "       imageSpec (Source.text ['A']) = Except.ok ['A']))\n"
            + _A_LETHEAD,
            _T_GOLD, _T_SEQ,
        ),
        "rationale": "the admitted domain covers a normal input AND the "
                     "post-image is satisfiable and non-degenerate there: the "
                     "guard admits a normal raw source, a raw source decodes to "
                     "its code-point image, and a character source passes "
                     "through unchanged. The in-region assert must discharge "
                     "(else PRECOND-TOO-STRONG / an unsatisfiable obligation); "
                     "the impl is kept verbatim so `out = imageSpec src` still "
                     "discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful counterpart
    # would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-raw-refused",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch behavior: a raw octet source is REFUSED rather than
        # decoded. The load-bearing discriminator this bundle exists to defend.
        "module": _swap(
            _BASE, _A_RAW,
            "      | Source.raw  _ => Except.error ImageErr.rawNotAccepted"),
        "refinement": "a counterpart that refuses a raw octet source instead of "
                      "accepting it never produces a character image for such a "
                      "source at all, so the failing test that constructs from a "
                      "raw octet source and reads back its parsed fields still "
                      "observes the refusal (the very pre-patch failure) and "
                      "still fails. It would NOT resolve.",
        "rationale": "REJECT from `out = imageSpec src`: on the raw arm the "
                     "post-image demands the decoded code-point image, and the "
                     "impl yields the refusal marker. Refuted at a present "
                     "single-octet raw source.",
        "witness": _witness("(Source.raw [65])"),
    },
    {
        "id": "weak-raw-drops-head",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: decodes every octet BUT the first — the image is one
        # character short on any non-empty raw source (right on the empty one).
        "module": _swap(
            _BASE, _A_RAW,
            "      | Source.raw  b => Except.ok (codepointsOf (b.drop 1))"),
        "refinement": "a counterpart that drops the first octet of a raw source "
                      "decodes a source shifted by one character, so the failing "
                      "test that reads the parsed fields off a raw octet source "
                      "observes the wrong leading content and still fails. It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = imageSpec src`: on a non-empty raw arm "
                     "the post-image demands the full code-point image and the "
                     "impl yields the image of the tail, one character short. "
                     "Refuted at a two-octet raw source (a length/content axis "
                     "the single-octet rivals do not probe).",
        "witness": _witness("(Source.raw [65, 66])"),
    },
    {
        "id": "weak-raw-ascii-mask",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-mask: masks each octet to 7 bits — identical to the code-point
        # image on octets 0..127, wrong on 128..255 (the sub-domain the raw
        # carrier admits and the byte-for-byte interpretation deliberately
        # retains).
        "module": _swap(
            _BASE, _A_RAW,
            "      | Source.raw  b => Except.ok (codepointsOf (b.map (· % 128)))"),
        "refinement": "a counterpart that masks each octet to seven bits agrees "
                      "with the byte-for-byte image on octets 0..127 but corrupts "
                      "any octet 128..255, so a raw source carrying a high octet "
                      "is decoded to the wrong character and the assertions that "
                      "pin the parsed content still fail on that sub-domain. It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = imageSpec src`: the post-image maps each "
                     "octet to its own code point, so at an octet >= 128 the "
                     "masked impl yields a different character. Refuted at a high "
                     "octet (200), the sub-domain no other rival probes.",
        "witness": _witness("(Source.raw [200])"),
    },
    {
        "id": "weak-text-emptied",
        "kind": "uniqueness",
        "expect": "reject",
        # Binder-coverage: corrupts the OTHER arm of the post-image. Every rival
        # above holds `src` at a raw source; this one abuses the character arm so
        # the `Source.text` constructor of the input binder is exercised.
        "module": _swap(_BASE, _A_TEXT, "      | Source.text _ => Except.ok []"),
        "refinement": "a counterpart that empties a character source discards a "
                      "character image already in hand, breaking every unchanged "
                      "path that constructs from a normal character source — the "
                      "pre-existing character-source assertions that pin the "
                      "parsed content regress. It would NOT resolve (and would "
                      "break behavior the fix leaves untouched).",
        "rationale": "REJECT from `out = imageSpec src`: on the character arm the "
                     "post-image demands the source passed through unchanged, and "
                     "the impl yields the empty image. Refuted at a character "
                     "source — the input-binder constructor no raw-arm rival "
                     "exercises, so `src` is varied across both arms.",
        "witness": _witness("(Source.text ['A'])"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (1 soundness
# positive, 1 admissibility, 4 uniqueness rivals — 2 of them permission-frame /
# control-flow specific). Every one is accounted for below.
#
#   sibling case                    -> here
#   ---------------------------------------------------------------------
#   pos-control-reshaped-loop       -> pos-arms-reordered / pos-inline-return
#                                         PORTED (split into two cheap reshapes)
#   admissibility-indomain          -> admiss-image-nondegenerate       PORTED
#   frame-mutation-write-raw        -> (none)                           VACUOUS
#   control-flow-prepatch-bug       -> weak-raw-refused                 PORTED
#   partial-domain-drop-first-byte  -> weak-raw-drops-head              PORTED
#   value-mask-ascii-7bit           -> weak-raw-ascii-mask              PORTED
#
# 5 ported (across 6 velvet cases), 1 vacuous.
#
# CARRIER NARROWING. The sibling carries the whole octet-list + text-only-pad
# pipeline (a backward-loop reinterpret, a runtime is_text-guarded pad step, and
# fractional-permission framing on the read-only input). This backend models only
# the purely functional core the graded behavior (test_card_from_bytes) turns on:
# the single decision "accept a raw octet source, interpreting each octet as its
# code point, exactly as a character source is accepted". So the sibling's
# in-loop unfold Asserts, its pad-precondition control-flow lane, and its
# permission framing have no counterpart to attack — the pad step is an unchanged
# downstream helper excluded from the model (mapping.md §3.2), and there is no
# heap. What survives is one obligation over one binder, and every reject rival
# attacks it.
#
# SIBLING pos-control-reshaped-loop -> SPLIT. The sibling reshapes a backward
#   loop (local hoisting + Assert reordering). This carrier has no loop — the
#   image is a direct case split — so the "cheapest correct reshape" is a branch
#   reorder or an intermediate-binding removal. Both are shipped
#   (pos-arms-reordered, pos-inline-return) so the reshape argument is defended
#   on both the decision structure and the value-flow structure.
#
# ADMISSIBILITY re-expressed, not re-aimed. Unlike the django sibling this
#   method DOES have a `require` (raw octets < 256), so the sibling's
#   "a normal input satisfies the precondition" probe ports directly: the assert
#   discharges the guard at a normal raw source. It ALSO covers the total-domain
#   residual (post-image unsatisfiable at the interesting point) by asserting the
#   image is exactly the decoded code points on the raw arm and the source itself
#   on the text arm. The assert is live (a false conjunct leaves an unsolved
#   goal — verified against gold).
#
# FRAME/PERMISSION-MUTATION: VACUOUS. The sibling's frame-mutation-write-raw
#   attacks a fractional-permission write to the read-only input. This backend is
#   referentially transparent and this bundle declares no `mut` binder, so there
#   is no read-only input to overwrite and no substitute probe to build. Not
#   fabricated.
#
# ADDED (1, no sibling counterpart): weak-text-emptied. The sibling's rivals all
#   attack the raw path (the modeled bug). On this carrier the post-image has a
#   SECOND arm — a character source must pass through unchanged — and every
#   raw-arm rival holds the input binder `src` at a raw value, so none attests
#   that the text arm is constrained. weak-text-emptied abuses the text arm at
#   `src = Source.text [...]` (a genuine divergence with a machine-checked
#   witness), so the input binder is varied across BOTH constructors rather than
#   pinned to `raw`, and both arms of the load-bearing post-image are attacked.
#
# WITNESS DISTINCTNESS / BINDER COVERAGE. The four reject witnesses probe four
#   distinct inputs: Source.raw [65] (a present single octet), Source.raw [65,66]
#   (a two-octet sequence, exercising the octet-list length/content axis),
#   Source.raw [200] (a high octet > 127), and Source.text ['A'] (the character
#   arm). No two rivals share a refutation point; `src` ranges over both
#   constructors and the raw octet content varies across low/multi/high. Each
#   witness was built against its rival (elaborates) and against the frozen
#   solution (fails) before shipping.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# consumed axiom (the octet->char interpretation is a deep A-reference validated
# by axiom_check.py), so there is nothing here to probe and the gate ignores it.
AXIOM_TESTS = []
