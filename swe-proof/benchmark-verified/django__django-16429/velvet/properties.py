"""properties.py — G-PBT falsification battery for django__django-16429 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct buildShiftedReference`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a read-only source instant):

  buildShiftedReference (base : Instant) (years : Nat) (months : Nat)
      return (out : Instant)
    require 1 ≤ base.mo ∧ base.mo ≤ 12
    require months ≤ 11
    require 0 < years ∨ 0 < months
    ensures out = shiftReference base years months

The method builds the reference instant that a later leftover-span measurement
is taken against, by shifting ``base`` forward by whole ``years`` and ``months``.
``Instant`` carries the touched calendar/clock components plus a ``zone : Option
Nat`` designation (``none`` a floating instant, ``some k`` an instant anchored to
designation ``k``). The sole ``ensures`` pins the whole output to the pure
``shiftReference``, whose value is a bundle of INDEPENDENT per-field decisions —
each a separate binder a rival can get wrong while getting the rest right:

  * (Y/M) the ADVANCE — the year/month are shifted forward by ``years``/
        ``months`` and the month is normalized back into 1..12, carrying into the
        year when ``base.mo + months`` overflows twelve. A rival that fails to
        advance, or skips the carry normalization, diverges here.
  * (D) the DAY CLAMP — the day-of-month is ``min (monthLen pm') base.d``, so an
        end-of-month source never names a non-existent day of the target month. A
        rival that drops the clamp keeps an out-of-range day.
  * (C) the CLOCK CARRY — hour/minute/second are carried across verbatim. A rival
        that zeroes them shifts the measured instant by up to ~24h.
  * (Z) the DESIGNATION CARRY — ``zone := base.zone``: the shifted reference must
        be expressed against the SAME designation as the source, so the two lie
        on a common timeline. This is the load-bearing clause the change repairs:
        an anchored source must yield an anchored reference, else a later
        difference between a floating reference and an anchored current instant is
        undefined (the crash the fix removes).

Input binders of the post-image the reject witnesses must vary: every component
of ``base`` (``y``, ``mo``, ``d``, ``h``, ``mi``, ``s``, ``zone``) plus the two
offsets ``years`` and ``months``. The precondition admits only ``1 ≤ base.mo ≤
12``, ``months ≤ 11``, and at least one non-zero offset, so each witness is
constructed inside that envelope (else the tester's precondition guard would
short it to a vacuous ``true``).

ADVERSARIAL READ of the nagini classes (see the footer for the case-by-case
accounting):
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling's two
    mandatory frame-mutation rivals keep the gold body then write back into the
    read-only source ``d`` (held at a fractional heap permission ``Acc(.,1/2)``)
    and are rejected for INSUFFICIENT PERMISSION. Lean and Velvet are
    referentially transparent: every parameter is an immutable value, this bundle
    declares no ``mut`` binder (``base`` is read-only by type), there is no heap
    and no aliasing. There is no read-only input to overwrite and no permission
    system to trip, so the class is vacuous. No substitute is fabricated.
  * CONTROL-FLOW-EFFECT (the discardable leftover-span call) — N/A here. The
    sibling's positive control DROPS the ``well_defined_diff(now, pivot)`` call
    whose only role was to sense the disposition. This backend models ONLY the
    pure reference-construction core (mapping.md §3): the subsequent difference is
    not part of the modeled expression, so there is no side-effecting call to
    drop and no counterpart rival. Reported as an omission, not faked.
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is ``shiftReference base years
    months`` and ``shiftReference`` / ``monthLen`` are concrete ``def``s in the
    ``pure`` region computing the reference from the method's own arguments (the
    ``axioms`` region declares nothing) — there is no opaque answer key to echo.
    The honest control is the cheapest faithful reshape (``pos-*``).
  * PARTIAL-DOMAIN / VALUE — heavily exercised: a rival can be correct on part of
    the domain yet diverge on a sub-domain (naive designation right for a floating
    source but wrong for an anchored one; un-advanced date right at a zero offset;
    zeroed clock right at midnight; un-clamped day right for an in-range day;
    un-normalized month right below the twelve boundary). Each is refuted at a
    concrete precondition-satisfying point on its own wrong sub-domain.

WITNESS MECHANICS. The frozen impl is STRAIGHT-LINE (no loop): its extracted
program reduces fully under ``decide``. Each reject rival carries a
machine-checked refutation ``witness`` — a Velvet tester statement
``buildShiftedReferenceTester <base> <years> <months> = false`` at ONE concrete,
precondition-satisfying input, checked in a file whose ``prove_correct`` block is
stripped so no tactic script can mask the verdict. ``Instant`` derives
``DecidableEq`` (and hence ``Option Nat`` and the return carrier do), so the
postcondition is decidable with no extra instance and every witness closes by
``decide``. Both halves were checked out-of-band with ``scripts/lean_verify.sh``:
each witness ELABORATES against its rival (the rival provably violates the
post-image at that input) and FAILS against the frozen solution (gold reduces the
tester to ``true`` there, so ``= false`` is disprovable) — a genuine spec
refutation, not mechanical tactic breakage.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom`` and no deep-model
reference; ``shiftReference`` / ``monthLen`` are deep models of language
constructs, refinement-checked by ``conformance_check.py`` (G-CONF), not
axiomatized. This gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-16429"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl region, verbatim — everything from `-- impl-start` through
# `-- impl-end` (marker lines included). Every rival and reshape edits ONLY this
# block (and, for reshapes/admissibility, the elided `prove_correct` tactic
# body), so the spec view is untouched and same_spec holds by construction. The
# whole block is unique in Solution.lean (asserted at load).
_IMPL = (
    "    -- impl-start\n"
    "    let py  := base.y + years\n"
    "    let pm  := base.mo + months\n"
    "    -- normalize the shifted month back into 1..12, carrying into the year\n"
    "    let py' := if pm > 12 then py + 1 else py\n"
    "    let pm' := if pm > 12 then pm - 12 else pm\n"
    "    let out : Instant :=\n"
    "      { y    := py',\n"
    "        mo   := pm',\n"
    "        d    := min (monthLen pm') base.d,\n"
    "        h    := base.h,\n"
    "        mi   := base.mi,\n"
    "        s    := base.s,\n"
    "        zone := base.zone }\n"
    "    return out\n"
    "    -- impl-end"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A reshape that changes the impl's syntactic form
# may retune THIS block (elided from the spec view); rivals leave it as-is (the
# rejection is carried by the witness, not the tactic script).
_PROOF = "prove_correct buildShiftedReference by\n  loom_solve"

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced (marker lines
    re-wrapped)."""
    return _swap(_BASE, _IMPL,
                 "    -- impl-start\n" + new_body + "\n    -- impl-end")


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes /
    admissibility asserts)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `buildShiftedReferenceTester <base> <years> <months> = false` says the
# ---- extracted program's result violates the postcondition at that concrete
# ---- (precondition-satisfying) input. Checked in a file whose `prove_correct`
# ---- block is stripped. The `Instant` return carrier already has DecidableEq
# ---- (derived on the structure), so no extra instance is needed.
_TESTER = (
    "extract_program_for buildShiftedReference\n"
    "prove_precondition_decidable_for buildShiftedReference\n"
    "prove_postcondition_decidable_for buildShiftedReference\n"
    "derive_tester_for buildShiftedReference\n\n"
)


def _wit(call):
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # impl that MUST verify; else the post-image is SPEC-TOO-STRONG on impl
    # shape. The obligation statement is preserved; only the executable surface
    # is reshaped.
    # =====================================================================
    {
        "id": "pos-inline-advance",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: drop the `py`/`pm` intermediate bindings and inline the
        # advanced year/normalized month directly into the two `if` expressions,
        # then construct from those. Definitionally the same value on every
        # input (`base.y + years + 1` = `(base.y + years) + 1`, etc.), so the
        # single equality clause still holds; the proof stays a `loom_solve`
        # away, with a `simp_all` fallback for the reshaped do-block.
        "module": _impl_reproved(
            "    let py' := if base.mo + months > 12 then base.y + years + 1 else base.y + years\n"
            "    let pm' := if base.mo + months > 12 then base.mo + months - 12 else base.mo + months\n"
            "    let out : Instant :=\n"
            "      { y    := py',\n"
            "        mo   := pm',\n"
            "        d    := min (monthLen pm') base.d,\n"
            "        h    := base.h,\n"
            "        mi   := base.mi,\n"
            "        s    := base.s,\n"
            "        zone := base.zone }\n"
            "    return out",
            "prove_correct buildShiftedReference by\n  loom_solve <;> simp_all [shiftReference]"),
        "rationale": "inlining the advanced year and normalized month into the "
                     "constructor (removing the `py`/`pm` intermediates) computes "
                     "the IDENTICAL `Instant` on every in-domain input — each "
                     "field maps to the same value definitionally — so "
                     "`out = shiftReference base years months` still discharges; "
                     "a correct reshape must verify, else SPEC-TOO-STRONG on the "
                     "binding shape.",
    },

    # =====================================================================
    # ADMISSIBILITY — the sibling establishes that a normal F2P-shaped input
    # satisfies the precondition. Here that probe is REAL (three `require`
    # clauses). The case keeps the gold impl VERBATIM and discharges an
    # in-region assert that (a) the F2P-shaped input — an anchored source shifted
    # forward by a whole year — lies in the precondition envelope, and (b) the
    # post-image is SATISFIABLE and NON-DEGENERATE there: the reference carries
    # the source's designation (`.zone = some 1`), distinct from a floating one
    # (`≠ none`). The assert is live: a false claim leaves an unsolved goal.
    # =====================================================================
    {
        "id": "admiss-anchored-f2p-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `assert\n"
            "      (((1 ≤ (8 : Nat) ∧ (8 : Nat) ≤ 12) ∧ (0 : Nat) ≤ 11 ∧ (0 < (1 : Nat) ∨ 0 < (0 : Nat))) ∧\n"
            "       (shiftReference ({ y := 2007, mo := 8, d := 14, h := 13, mi := 46, s := 0, zone := some 1 } : Instant) 1 0).zone = some 1 ∧\n"
            "       (shiftReference ({ y := 2007, mo := 8, d := 14, h := 13, mi := 46, s := 0, zone := some 1 } : Instant) 1 0).zone ≠ none))\n"
            "    let py  := base.y + years\n"
            "    let pm  := base.mo + months\n"
            "    let py' := if pm > 12 then py + 1 else py\n"
            "    let pm' := if pm > 12 then pm - 12 else pm\n"
            "    let out : Instant :=\n"
            "      { y    := py',\n"
            "        mo   := pm',\n"
            "        d    := min (monthLen pm') base.d,\n"
            "        h    := base.h,\n"
            "        mi   := base.mi,\n"
            "        s    := base.s,\n"
            "        zone := base.zone }\n"
            "    return out",
            "prove_correct buildShiftedReference by\n  loom_solve <;> decide"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P corner: an anchored source (`zone = some 1`) shifted "
                     "forward by a whole year lies in the precondition envelope "
                     "(`1 ≤ 8 ≤ 12`, `0 ≤ 11`, `0 < 1`), and the built reference "
                     "carries that designation (`.zone = some 1`, distinct from a "
                     "floating `none`). The in-region assert must discharge (else "
                     "the obligation would be unsatisfiable / PRECOND-TOO-STRONG); "
                     "the impl is kept verbatim so the ensures clause still "
                     "discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete precondition-satisfying input and the refinement argument for why
    # its faithful real counterpart would still leave the F2P failing.
    # =====================================================================
    {
        "id": "weak-naive-designation",
        "kind": "uniqueness",
        "expect": "reject",
        # THE bug. The reference is built without the source's designation
        # (`zone := none`): an anchored source yields a floating reference. This
        # is the literal pre-patch construction. Correct only for a floating
        # source; wrong for every anchored one.
        "module": _impl(
            "    let py  := base.y + years\n"
            "    let pm  := base.mo + months\n"
            "    let py' := if pm > 12 then py + 1 else py\n"
            "    let pm' := if pm > 12 then pm - 12 else pm\n"
            "    let out : Instant :=\n"
            "      { y    := py',\n"
            "        mo   := pm',\n"
            "        d    := min (monthLen pm') base.d,\n"
            "        h    := base.h,\n"
            "        mi   := base.mi,\n"
            "        s    := base.s,\n"
            "        zone := none }\n"
            "    return out"),
        "refinement": "this IS the pre-patch construction: the reference is built "
                      "dropping the source's designation. Its faithful real "
                      "counterpart is the unchanged repo, where an anchored source "
                      "yields a floating reference, so the later leftover-span "
                      "difference between an anchored current instant and the "
                      "floating reference is UNDEFINED and raises — exactly the "
                      "crash the F2P tests (an anchored source more than one "
                      "whole unit in the past) assert is gone. It would NOT "
                      "resolve — the precise change the spec senses (G-DIFF).",
        "rationale": "REJECT from the designation-carry clause (Z) of "
                     "`out = shiftReference base years months`: the post-image "
                     "sets `zone := base.zone`, so for an anchored source "
                     "(`zone = some 1`) it demands `some 1` but the rival emits "
                     "`none`. Refuted at an anchored source shifted by a whole "
                     "year — the sub-domain where it is wrong (a floating source "
                     "would agree).",
        "witness": _wit(
            "buildShiftedReferenceTester "
            "({ y := 2007, mo := 8, d := 14, h := 13, mi := 46, s := 0, zone := some 1 } : Instant) 1 0"),
    },
    {
        "id": "weak-unadvanced-date",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: keep the source calendar date instead of advancing it
        # (year/month taken from `base`, not shifted). Correct only at a zero
        # offset; wrong whenever a whole unit elapsed.
        "module": _impl(
            "    let out : Instant :=\n"
            "      { y    := base.y,\n"
            "        mo   := base.mo,\n"
            "        d    := min (monthLen base.mo) base.d,\n"
            "        h    := base.h,\n"
            "        mi   := base.mi,\n"
            "        s    := base.s,\n"
            "        zone := base.zone }\n"
            "    return out"),
        "refinement": "a reference pinned to the UN-advanced source date measures "
                      "the whole elapsed span instead of the leftover span beyond "
                      "the accounted whole years/months. The rendered residual is "
                      "then wrong (e.g. the thousand-years-ago case renders the "
                      "residual beyond 1000 advanced years, ~0, not the expected "
                      "figure), so the F2P tests that assert the rendered string "
                      "still fail. It would NOT resolve.",
        "rationale": "REJECT from the advance clause (Y/M): the post-image sets "
                     "`y := base.y + years` (etc.), so with `years = 1` it demands "
                     "`base.y + 1` but the rival keeps `base.y`. Refuted at a "
                     "one-year offset — the sub-domain where the un-advanced date "
                     "diverges (a zero offset would agree).",
        "witness": _wit(
            "buildShiftedReferenceTester "
            "({ y := 2007, mo := 8, d := 14, h := 13, mi := 46, s := 0, zone := none } : Instant) 1 0"),
    },
    {
        "id": "weak-zeroed-clock",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: zero the carried clock components. Correct only for a
        # midnight source; wrong whenever the source clock is non-zero (shifts
        # the measured instant by up to ~24h).
        "module": _impl(
            "    let py  := base.y + years\n"
            "    let pm  := base.mo + months\n"
            "    let py' := if pm > 12 then py + 1 else py\n"
            "    let pm' := if pm > 12 then pm - 12 else pm\n"
            "    let out : Instant :=\n"
            "      { y    := py',\n"
            "        mo   := pm',\n"
            "        d    := min (monthLen pm') base.d,\n"
            "        h    := 0,\n"
            "        mi   := 0,\n"
            "        s    := 0,\n"
            "        zone := base.zone }\n"
            "    return out"),
        "refinement": "zeroing the reference clock drops the source hour/minute/"
                      "second, shifting the reference by up to ~24h and so the "
                      "measured leftover span. Any source whose clock is not "
                      "midnight renders different sub-day residual components (the "
                      "depth/units tests observe them), so it does NOT resolve; "
                      "correct only on the midnight sub-domain.",
        "rationale": "REJECT from the clock-carry clause (C): the post-image sets "
                     "`h := base.h` (and `mi`, `s`), so for `base.h = 13` it "
                     "demands `13` but the rival emits `0`. Refuted at a source "
                     "with a non-midnight clock (`h = 13`, `mi = 46`, `s = 30`) — "
                     "varying the clock binders against the other witnesses.",
        "witness": _wit(
            "buildShiftedReferenceTester "
            "({ y := 2007, mo := 8, d := 14, h := 13, mi := 46, s := 30, zone := none } : Instant) 1 0"),
    },
    {
        "id": "weak-unclamped-day",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: carry the source day verbatim, dropping the clamp to
        # the target month's length. Correct only when the source day already
        # fits the target month; wrong for an end-of-month source shifted onto a
        # shorter month.
        "module": _impl(
            "    let py  := base.y + years\n"
            "    let pm  := base.mo + months\n"
            "    let py' := if pm > 12 then py + 1 else py\n"
            "    let pm' := if pm > 12 then pm - 12 else pm\n"
            "    let out : Instant :=\n"
            "      { y    := py',\n"
            "        mo   := pm',\n"
            "        d    := base.d,\n"
            "        h    := base.h,\n"
            "        mi   := base.mi,\n"
            "        s    := base.s,\n"
            "        zone := base.zone }\n"
            "    return out"),
        "refinement": "carrying the source day without clamping it to the target "
                      "month's length names a non-existent day when an "
                      "end-of-month source is shifted onto a shorter month (e.g. "
                      "day 31 onto a 28-day month). The reference is then an "
                      "invalid instant and the rendered span is wrong for such "
                      "sources, so it does NOT resolve; correct only when the day "
                      "already fits.",
        "rationale": "REJECT from the day-clamp clause (D): the post-image sets "
                     "`d := min (monthLen pm') base.d`, so for a day-31 source "
                     "shifted onto a 28-day month it demands `28` but the rival "
                     "emits `31`. Refuted at `base.mo = 1`, `base.d = 31`, "
                     "`months = 1` (target month February) — the sub-domain where "
                     "the clamp bites; and this witness moves `months` off zero, "
                     "varying that binder.",
        "witness": _wit(
            "buildShiftedReferenceTester "
            "({ y := 2007, mo := 1, d := 31, h := 0, mi := 0, s := 0, zone := none } : Instant) 0 1"),
    },
    {
        "id": "weak-unnormalized-month",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: skip the month carry normalization — take the shifted
        # month/year raw, never folding an overflowing month back into 1..12.
        # Correct only when `base.mo + months ≤ 12`; wrong when it overflows.
        "module": _impl(
            "    let py  := base.y + years\n"
            "    let pm  := base.mo + months\n"
            "    let out : Instant :=\n"
            "      { y    := py,\n"
            "        mo   := pm,\n"
            "        d    := min (monthLen pm) base.d,\n"
            "        h    := base.h,\n"
            "        mi   := base.mi,\n"
            "        s    := base.s,\n"
            "        zone := base.zone }\n"
            "    return out"),
        "refinement": "skipping the carry leaves an out-of-range month (e.g. "
                      "month 13) and the wrong year whenever the shifted month "
                      "overflows twelve, so the reference names a nonsense "
                      "calendar position and the rendered span is wrong for such "
                      "sources. It does NOT resolve; correct only below the "
                      "twelve boundary.",
        "rationale": "REJECT from the advance/normalization clause (Y/M): the "
                     "post-image folds `pm = base.mo + months > 12` back via "
                     "`pm' := pm - 12`, `py' := py + 1`, so for `base.mo = 12`, "
                     "`months = 1` it demands `mo = 1` (and `y = base.y + 1`) but "
                     "the rival emits `mo = 13`. Refuted at the month-overflow "
                     "boundary (`base.mo = 12`, `months = 1`) — the complementary "
                     "sub-domain to weak-unadvanced-date's zero-carry point.",
        "witness": _wit(
            "buildShiftedReferenceTester "
            "({ y := 2007, mo := 12, d := 14, h := 0, mi := 0, s := 0, zone := none } : Instant) 0 1"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness — two of which are the mandatory
# frame-mutation rivals). The sibling contracts `pivot_remaining(d, now,
# pivot_year, pivot_month, pivot_day)`, which builds the reference instant AND
# calls the deep `well_defined_diff(now, pivot)` guard for the subsequent
# difference. This backend models ONLY the pure reference-construction core
# (mapping.md §3): `buildShiftedReference (base) (years) (months)` returning the
# shifted `Instant`. The reference-construction surface carries across intact;
# the permission surface and the leftover-span difference call do not exist here.
#
#   sibling case                 -> here                              disposition
#   -----------------------------------------------------------------------------
#   frame-mut-write-d-clock      -> (none)                            VACUOUS
#   frame-mut-write-d-tz         -> (none)                            VACUOUS
#   partial-naive-pivot          -> weak-naive-designation            PORTED
#   partial-unadvanced-pivot     -> weak-unadvanced-date              PORTED
#   partial-zeroed-clock         -> weak-zeroed-clock                 PORTED
#   posctl-drop-diff-call        -> (none)                            N/A (unmodeled)
#   posctl-local-reshape         -> pos-inline-advance                PORTED (reshaped)
#   admiss-disposition-witness   -> admiss-anchored-f2p-nondegenerate RE-AIMED
#   (no sibling)                 -> weak-unclamped-day                ADDED (D clause)
#   (no sibling)                 -> weak-unnormalized-month           ADDED (carry)
#
# 4 ported, 1 re-aimed, 2 vacuous, 1 dropped-as-unmodeled; 2 binder-coverage
# rivals added.
#
# VACUOUS (frame-mut-write-d-clock, frame-mut-write-d-tz): the sibling's two
#   MANDATORY frame-mutation rivals keep the gold body then write back into the
#   read-only source `d`, held at half heap permission, and must be rejected for
#   INSUFFICIENT PERMISSION. This backend is referentially transparent: every
#   parameter is an immutable value, the method declares no `mut` binder (`base`
#   is read-only by type), there is no heap and no aliasing. There is no
#   read-only input to overwrite and no permission system to trip, so the class
#   is vacuous. No substitute is fabricated.
# N/A-UNMODELED (posctl-drop-diff-call): the sibling's second positive control
#   drops the value-discarded `well_defined_diff(now, pivot)` call and shows the
#   constructed pivot still verifies. This backend models only the pure
#   reference-construction core; the subsequent difference and its guard call are
#   NOT part of the modeled expression (mapping.md §3), so there is no
#   side-effecting call to drop and no counterpart rival on this carrier. Its
#   soundness point — that the reference alone carries the designation — is
#   already the load-bearing content of the (Z) clause, defended positively by
#   pos-inline-advance and admiss-anchored-f2p-nondegenerate and attacked by
#   weak-naive-designation. Omitted, not faked.
# RE-AIMED (admissibility): the sibling asserts an aware and a naive F2P witness
#   each satisfy the disposition precondition. This backend's precondition is
#   three real `require` clauses (`1 ≤ base.mo ≤ 12`, `months ≤ 11`, a non-zero
#   offset), so the "a normal input is admitted" probe is REAL. The case keeps
#   the gold impl verbatim and asserts an anchored F2P-shaped input lies in that
#   envelope AND the built reference carries the source designation (non-
#   degenerate: `.zone = some 1 ≠ none`) — the precise property the naive-
#   construction bug violated.
# PORTED-RESHAPED (pos-inline-advance): the sibling's positive control names each
#   constructor argument into a typed local first. This backend's frozen impl
#   already uses `py`/`pm` intermediates, so the reshape is the DUAL — inline the
#   advanced year / normalized month directly into the constructor, removing the
#   intermediates. Behaviourally identical (definitional equality per field), so
#   the reproof is `loom_solve <;> simp_all [shiftReference]`.
# ADDED (weak-unclamped-day): the sibling has no day-clamp rival — its pivot
#   construction takes `min(MONTHS_DAYS[..], d.day)` but the sibling battery
#   attacks the disposition, calendar-position and clock clauses only. This
#   backend's (D) clause is an independent per-field decision with its own binders
#   (`base.mo`, `base.d`); a battery that never abused an end-of-month source onto
#   a shorter month would never demonstrate the clamp is load-bearing, so this
#   rival drops the clamp and is refuted at day 31 shifted onto February.
# ADDED (weak-unnormalized-month): likewise the sibling has no month-carry rival.
#   The (Y/M) clause folds an overflowing shifted month back into 1..12; a rival
#   that skips the carry is correct below the twelve boundary and wrong above it,
#   refuted at `base.mo = 12`, `months = 1` — the overflow sub-domain
#   complementary to weak-unadvanced-date's zero-offset point, and the witness
#   that moves `months` and `base.mo` to their boundary values.
#
# BINDER / CLAUSE COVERAGE of the five reject witnesses over the post-image's
#   input binders (pts = 5 distinct input points):
#     base.zone : some 1 (naive-designation) vs none (all others) — varied; the
#                 designation-carry clause (Z) is attacked exactly where it bites.
#     base.y/mo advance : years = 1 (unadvanced) drives the year advance; months
#                 = 1 with base.mo = 12 (unnormalized-month) drives the carry.
#     base.mo   : 8, 1, 12 across the witnesses — varied over the 1..12 envelope.
#     base.d    : 14 vs 31 (unclamped-day) — the day-clamp clause (D) is attacked
#                 exactly at the end-of-month source.
#     base.h/mi/s : 13/46/30 (zeroed-clock) vs 0/0/0 (others) — the clock-carry
#                 clause (C) is attacked with a non-midnight source.
#     years     : 1 (naive-designation, unadvanced-date, zeroed-clock) vs 0
#                 (unclamped-day, unnormalized-month) — varied.
#     months    : 0 (first three) vs 1 (unclamped-day, unnormalized-month) —
#                 varied over the 0..11 envelope.
#   Every independent top-level clause of the post-image is attacked: designation
#   carry (Z), year/month advance and carry (Y/M, two rivals on complementary
#   sub-domains), day clamp (D), and clock carry (C); and defended by the positive
#   control and the admissibility case. No binder is pinned across the battery.
#
# AXIOM_TESTS: dropped. The sibling's axiom lane validates `well_defined_diff` as
#   a deep model of datetime subtraction definedness; this bundle models no callee
#   (`meta.json axioms = []`, `deep_model_references = []`) — the reference is
#   built field-by-field from concrete data — so there is nothing to probe, and
#   this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
