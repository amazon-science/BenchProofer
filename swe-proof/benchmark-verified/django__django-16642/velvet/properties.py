"""properties.py — G-PBT falsification battery for django__django-16642 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both are elided from the consumer spec view, so ``markers.same_spec`` holds
and the ``prove_correct resolveMediaType`` obligation survives with a
byte-identical header) and swaps in a candidate implementation; it is checked by
the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness elaborates against the rival and FAILS
against the frozen solution).

DEFENDED SURFACE. One contracted method over two optional media-type carriers:

  resolveMediaType (guessed encoding : Option String) return (out : String)
    ensures out = resolvedMediaType guessed encoding

with the single, fully-grounded post-image

  resolvedMediaType g e = (compressionMediaType e |>.orElse (fun _ => g)).getD
                            "application/octet-stream"
  compressionMediaType e = (a total match pinning each of five recognised
                            compression labels to its OWN dedicated media type,
                            and every other label / absence to `none`).

There is no ``require`` clause: the admitted input domain is total, and BOTH
binders are free — the post-image must hold for every value they take. The
oracle is a total, fully-unfolded function of the method's own arguments (no
``axiom`` region, no opaque callee), so there is no ungrounded answer-key to
echo: any value equal to ``resolvedMediaType g e`` IS the correct output. That
is what makes each partial-domain rival below refutable at a concrete point by
``decide`` — the carrier computes.

ADVERSARIAL READ of the classes:
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. It exists on the
    sibling because an input may carry a fractional heap permission an impl can
    overwrite. This backend is referentially transparent, both parameters are
    immutable values, this bundle declares no ``mut`` binder, and there is no
    heap or aliasing — so there is no read-only input to mutate and no substitute
    probe to build. Not fabricated. (See footer for the sibling's frame case.)
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * PARTIAL-DOMAIN / VALUE — APPLIES. The post-image has three observable
    sub-behaviours over the two binders — a recognised compression label wins and
    contributes its OWN dedicated media type; an unrecognised/absent label falls
    back to the guessed type; and when even that is absent the generic binary
    media type is announced. Each is attacked by a rival wrong only on its
    sub-domain, and the two NEW recognised labels (the discriminating fix) are
    attacked individually.
  * UNGROUNDED-ORACLE ECHO — N/A (the oracle is grounded, see above). Carried
    instead as honest cheapest-reshape POSITIVE CONTROLS (``pos-*``).

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches it through Velvet's own tester machinery: ``resolveMediaTypeTester
g e = false`` says the extracted program's result violates the post-image at that
concrete input. It is checked in a file whose ``prove_correct`` block is stripped,
so no tactic script can mask the verdict. Rivals do not share a refutation point:
each ``encoding`` value below hits a DISTINCT sub-domain of the post-image (a
different recognised label, an unrecognised label, or the absent marker), and
``guessed`` is moved across ``some`` / ``none`` so neither binder is held fixed.

AXIOM lane: EMPTY (``axioms`` region declares no ``axiom``; every input is a free
value owed no contract). The gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-16642"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. Lies wholly inside the single `-- impl-start` /
# ---- `-- impl-end` region and is unique in Solution.lean (both asserted at
# ---- load by _swap). Every rival/positive replaces exactly this text.
_IMPL = (
    "    let chosen := (compressionMediaType encoding).orElse (fun _ => guessed)\n"
    "    -- ... and to the generic binary media type when even that is absent.\n"
    '    return chosen.getD "application/octet-stream"'
)

# ---- proof-body anchor. A `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view (only the header is kept), so a positive control that
# ---- reshapes the impl may retune its tactic script without touching the spec
# ---- or dropping the obligation. Unique in the file.
_PROOF = "  loom_solve\n  simp [resolvedMediaType]"


def _impl(new_impl):
    """Reshape ONLY the impl region; keep the frozen proof body."""
    return _swap(_BASE, _IMPL, new_impl)


def _impl_proof(new_impl, new_proof):
    """Reshape the impl region AND retune the tactic body (for positives)."""
    return _swap(_swap(_BASE, _IMPL, new_impl), _PROOF, new_proof)


# ---- witness preamble. Reaches the method contract through Velvet's tester
# ---- machinery; appended to BOTH the rival file and the (proof-stripped) gold
# ---- file, so the tester names exist on both sides by construction.
_WIT = (
    "extract_program_for resolveMediaType\n"
    "prove_precondition_decidable_for resolveMediaType\n"
    "prove_postcondition_decidable_for resolveMediaType\n"
    "derive_tester_for resolveMediaType\n\n"
)


def _witness(guessed, encoding):
    return _WIT + (
        f"example : resolveMediaTypeTester {guessed} {encoding} = false := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot, the spec is
    # SPEC-TOO-STRONG. Each keeps the obligation header byte-identical and only
    # reshapes the executable surface + retunes the tactic body.
    # =====================================================================
    {
        "id": "pos-match-chosen",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: case-split on the recognised-label lookup instead of the
        # `orElse` combinator — present label returns its dedicated type, absence
        # falls to the guessed type (or the generic marker). Observationally
        # `resolvedMediaType guessed encoding` for every input.
        "module": _impl_proof(
            "    let out := match compressionMediaType encoding with\n"
            "      | some t => t\n"
            '      | none   => guessed.getD "application/octet-stream"\n'
            "    return out",
            "  loom_solve\n"
            "  cases h : compressionMediaType encoding <;> "
            "simp [resolvedMediaType, h]",
        ),
        "rationale": "a correct case-split reshape of the resolution must satisfy "
                     "`out = resolvedMediaType guessed encoding` on both arms of "
                     "the recognised-label lookup; else SPEC-TOO-STRONG on the "
                     "combinator form.",
    },
    {
        "id": "pos-inline-branches",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: inline every recognised label as an explicit branch returning
        # its dedicated media type directly (does not call the lookup at all),
        # with the guessed-type fallback on the default branch. Structurally the
        # cheapest branch-by-branch impl; confirms the spec ADMITS it.
        "module": _impl_proof(
            "    let out := match encoding with\n"
            '      | some "br"       => "application/x-brotli"\n'
            '      | some "bzip2"    => "application/x-bzip"\n'
            '      | some "compress" => "application/x-compress"\n'
            '      | some "gzip"     => "application/gzip"\n'
            '      | some "xz"       => "application/x-xz"\n'
            '      | _               => guessed.getD "application/octet-stream"\n'
            "    return out",
            "  loom_solve\n"
            "  cases encoding <;> "
            "simp [resolvedMediaType, compressionMediaType] <;> "
            "split <;> simp_all",
        ),
        "rationale": "inlining each recognised label to its dedicated media type "
                     "and defaulting to the guessed type reproduces "
                     "`resolvedMediaType guessed encoding` on every input; a "
                     "straightforward correct reshape must verify (else "
                     "SPEC-TOO-STRONG).",
    },

    # =====================================================================
    # ADMISSIBILITY — the method has NO `require` clause, so nothing could
    # exclude a normal input; the usual precondition probe is vacuous. Re-aimed
    # at the residual admissibility risk on a total domain: that the post-image
    # is UNSATISFIABLE / degenerate at the interesting points. This case
    # discharges an in-region assert pinning the oracle at three F2P-shaped
    # points — a recognised NEW label to its dedicated type, an unrecognised
    # label to the guessed type, and total absence to the generic marker — so
    # the verifier must establish the post-image really demands those values.
    # The surrounding impl is kept verbatim so the method's own obligation still
    # discharges. The assert is live: replacing any clause with a false value
    # leaves an unsolved `False` goal (checked by hand).
    # =====================================================================
    {
        "id": "admiss-resolution-points",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            "    assert (with_name_prefix `assert\n"
            '      (resolvedMediaType (some "application/x-tar") (some "br") = '
            '"application/x-brotli" ∧\n'
            '       resolvedMediaType (some "text/plain") none = "text/plain" ∧\n'
            "       resolvedMediaType none none = "
            '"application/octet-stream"))\n' + _IMPL,
            "  loom_solve <;> simp [resolvedMediaType, compressionMediaType]",
        ),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped points: it demands the dedicated media type for "
                     "a recognised compression label, the guessed type when the "
                     "label is unrecognised, and the generic binary type when "
                     "both are absent. The in-region assert must discharge (else "
                     "an unsatisfiable / degenerate obligation); the impl is kept "
                     "verbatim so `out = resolvedMediaType guessed encoding` "
                     "still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input the other rivals do not probe, plus the refinement argument
    # that its faithful real counterpart would NOT resolve the failing tests.
    # =====================================================================
    {
        "id": "drop-br-key",
        "kind": "uniqueness",
        "expect": "reject",
        # Removes the recognised-label branch for the first NEW label so that
        # label falls through to the guessed type — the pre-patch behaviour for
        # that scheme.
        "module": _impl(
            "    let chosen := (match encoding with\n"
            '      | some "bzip2"    => some "application/x-bzip"\n'
            '      | some "compress" => some "application/x-compress"\n'
            '      | some "gzip"     => some "application/gzip"\n'
            '      | some "xz"       => some "application/x-xz"\n'
            "      | _               => none).orElse (fun _ => guessed)\n"
            '    return chosen.getD "application/octet-stream"'),
        "refinement": "a counterpart that omits this recognised label is the "
                      "pre-patch behaviour for that scheme; the failing test that "
                      "pins that scheme's response to its OWN dedicated media type "
                      "still observes the wrapped (uncompressed) guessed type and "
                      "still fails. It would NOT resolve.",
        "rationale": "REJECT from `out = resolvedMediaType guessed encoding`: for "
                     "this recognised label the impl falls back to the guessed "
                     "type where the post-image demands the label's dedicated "
                     "type. Refuted with a present guessed type and this label.",
        "witness": _witness('(some "text/x-tar")', '(some "br")'),
    },
    {
        "id": "drop-compress-key",
        "kind": "uniqueness",
        "expect": "reject",
        # Removes the recognised-label branch for the second NEW label — the
        # other half of the pre-patch bug. Refuted at a DIFFERENT label and a
        # different guessed type than drop-br-key.
        "module": _impl(
            "    let chosen := (match encoding with\n"
            '      | some "br"       => some "application/x-brotli"\n'
            '      | some "bzip2"    => some "application/x-bzip"\n'
            '      | some "gzip"     => some "application/gzip"\n'
            '      | some "xz"       => some "application/x-xz"\n'
            "      | _               => none).orElse (fun _ => guessed)\n"
            '    return chosen.getD "application/octet-stream"'),
        "refinement": "omitting this recognised label is the other half of the "
                      "pre-patch bug; the failing test pinning that scheme's "
                      "response to its dedicated media type still observes the "
                      "guessed type and still fails. It would NOT resolve.",
        "rationale": "REJECT from `out = resolvedMediaType guessed encoding`: for "
                     "this recognised label the impl falls back to the guessed "
                     "type where the post-image demands the label's dedicated "
                     "type. Refuted at a distinct recognised label from "
                     "drop-br-key.",
        "witness": _witness('(some "text/html")', '(some "compress")'),
    },
    {
        "id": "swap-br-value",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-swap: maps the first NEW label to a DIFFERENT recognised
        # scheme's dedicated type. Wrong only on that label's sub-domain, and
        # refuted with an ABSENT guessed type — so the divergence is attributable
        # to the label mapping alone, not to any fallback.
        "module": _impl(
            "    let chosen := (match encoding with\n"
            '      | some "br"       => some "application/x-bzip"\n'
            '      | some "bzip2"    => some "application/x-bzip"\n'
            '      | some "compress" => some "application/x-compress"\n'
            '      | some "gzip"     => some "application/gzip"\n'
            '      | some "xz"       => some "application/x-xz"\n'
            "      | _               => none).orElse (fun _ => guessed)\n"
            '    return chosen.getD "application/octet-stream"'),
        "refinement": "a counterpart mapping this label to another scheme's media "
                      "type announces the wrong media type for the compressed "
                      "payload; the failing test pinning it to its OWN dedicated "
                      "type still fails. It would NOT resolve.",
        "rationale": "REJECT from `out = resolvedMediaType guessed encoding`: the "
                     "two dedicated media types differ, so at this label the impl "
                     "yields the wrong one. Refuted with `guessed = none`, so the "
                     "wrongness is in the label mapping, not the fallback.",
        "witness": _witness('none', '(some "br")'),
    },
    {
        "id": "passthrough-returns-encoding",
        "kind": "uniqueness",
        "expect": "reject",
        # For an unrecognised label, falls back to the LABEL itself instead of
        # the guessed type (the `orElse` default is `encoding`, not `guessed`).
        # Attacks the guessed-type-passthrough sub-behaviour; refuted at an
        # unrecognised label with a present, distinct guessed type.
        "module": _impl(
            "    let chosen := (compressionMediaType encoding).orElse "
            "(fun _ => encoding)\n"
            '    return chosen.getD "application/octet-stream"'),
        "refinement": "a counterpart that announces the raw compression label as "
                      "the media type for an unrecognised label returns a "
                      "non-media-type string for ordinary files; the passing "
                      "content-type tests (expecting the guessed type, e.g. "
                      "text/plain) would fail. It would NOT resolve.",
        "rationale": "REJECT from `out = resolvedMediaType guessed encoding`: on "
                     "the unrecognised-label branch the post-image demands the "
                     "GUESSED type; the impl returns the label. Refuted at an "
                     "unrecognised label with a present guessed type that differs "
                     "from it.",
        "witness": _witness('(some "text/plain")', '(some "foo")'),
    },
    {
        "id": "generic-fallback-wrong",
        "kind": "uniqueness",
        "expect": "reject",
        # Corrupts the FINAL generic fallback: when both label and guess are
        # absent, announces a non-standard generic marker instead of the generic
        # binary media type. Attacks the both-absent sub-behaviour, the only one
        # neither binder-value probe above reaches; refuted at `none, none`.
        "module": _impl(
            "    let chosen := (compressionMediaType encoding).orElse "
            "(fun _ => guessed)\n"
            '    return chosen.getD "application/x-unknown"'),
        "refinement": "a counterpart announcing a non-standard generic marker "
                      "when nothing is known changes the media type served for "
                      "every un-guessable file; the passing tests pinning that "
                      "fallback to the generic binary media type would fail. It "
                      "would NOT resolve.",
        "rationale": "REJECT from `out = resolvedMediaType guessed encoding`: with "
                     "both label and guess absent the post-image demands the "
                     "generic binary media type; the impl returns a different "
                     "marker. Refuted at `guessed = none`, `encoding = none` — the "
                     "both-absent sub-domain no other rival probes.",
        "witness": _witness('none', 'none'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals — one of which is the
# mandatory frame-mutation rival); every one is accounted for below. The sibling
# models a per-code-point `select_content_type(content_type, encoding)` over
# List[int] byte carriers WITH fractional heap permissions; this bundle models
# the value-level resolution `resolveMediaType (guessed encoding : Option String)`
# over immutable Option String carriers, so the byte-loop machinery and the
# permission frame have no counterpart, while the resolution ARGUMENT ports
# faithfully.
#
#   sibling case                       -> here
#   ---------------------------------------------------------------------
#   frame-mut-write-input              -> (none)                    VACUOUS
#   drop-br-key                        -> drop-br-key               PORTED
#   drop-compress-key                  -> drop-compress-key         PORTED
#   swap-br-value-to-bzip              -> swap-br-value             PORTED
#   passthrough-returns-encoding       -> passthrough-returns-encoding PORTED
#   pos-reorder-branches-reshape-loop  -> pos-inline-branches       RE-SHAPED
#   pos-echo-grounded-oracle           -> pos-match-chosen          RE-SHAPED
#   admiss-br-text-html                -> admiss-resolution-points  RE-AIMED
#
# 4 ported, 2 re-shaped positives, 1 re-aimed admissibility, 1 vacuous = 8.
#
# VACUOUS (frame-mutation): the sibling's MANDATORY frame rival writes to the
#   read-only half-permission `content_type` input. This backend is referentially
#   transparent, both inputs are immutable values, and this bundle declares no
#   `mut` binder — there is no heap, no aliasing, no read-only input to overwrite,
#   and no substitute probe to fabricate. Recorded, not faked.
# RE-SHAPED (the two positives): the sibling reshapes a byte-copy loop with its
#   prefix-preservation invariant; there is no loop here (the resolution is a
#   value-level combinator), so the two positives are re-expressed as the two
#   structurally-distinct correct impls this carrier admits — a case-split on the
#   recognised-label lookup (pos-match-chosen, the analogue of reorder-branches)
#   and a fully-inlined branch-by-branch impl that never calls the lookup
#   (pos-inline-branches, the analogue of the grounded cheapest-impl echo). The
#   ARGUMENT — a correct reshape must verify, else SPEC-TOO-STRONG — is unchanged.
# RE-AIMED (admissibility): the sibling establishes a precondition for an
#   F2P-shaped input. No method here has a `require` clause, so that probe is
#   vacuous — nothing could exclude a normal input. It is re-aimed at the residual
#   admissibility risk on a total domain: that the post-image is unsatisfiable /
#   degenerate at the interesting points. The case discharges an in-region assert
#   pinning the oracle at three F2P-shaped points (a recognised NEW label to its
#   dedicated type, an unrecognised label to the guessed type, and total absence
#   to the generic marker).
# ADDED (1, no sibling counterpart): generic-fallback-wrong. The sibling's List
#   carrier has no generic-binary fallback (its default branch copies
#   content_type); here the post-image has a distinct both-absent sub-behaviour
#   (`getD "application/octet-stream"`), and a battery that never probes it says
#   nothing about the spec's dependence on that arm. It is a real divergence with
#   a machine-checked witness at `none, none`.
#
# BINDER / CLAUSE COVERAGE. The single post-image clause has three observable
#   sub-behaviours over the two free binders; each reject rival attacks a
#   distinct one and the two binders are both moved across the battery:
#     `encoding` over {"br", "compress", "br", "foo"(unrecognised), none} — the
#       two NEW recognised labels, an unrecognised label, and the absent marker;
#     `guessed`  over {some "text/x-tar", some "text/html", none, some
#       "text/plain", none} — moved across present/absent so the passthrough and
#       the generic-fallback arms are both exercised.
#   No reject witness shares an input with another; `pts` = 5 distinct points.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom, so there is nothing there to probe.
AXIOM_TESTS = []
