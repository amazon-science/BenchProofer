"""properties.py — G-PBT falsification battery for django__django-14373 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct fourDigitYear`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method):

  fourDigitYear (year : Nat) return (out : List Char)
    require year ≤ 9999
    ensures out = fourDigitString year

The method renders a calendar year (a count below ten thousand) as a
fixed-width four-character decimal, most-significant-first, with the high slots
filled on the left with zeros so a value below one thousand still occupies four
slots. The single load-bearing ``ensures`` pins ``out`` to the deep, fully
unfolded pure model ``fourDigitString year`` (the ``axioms`` region is empty —
no opaque answer key to echo). ``fourDigitString`` fixes FOUR independently
attackable facts about the result:

  * WIDTH — the result is exactly four characters, never fewer (a small year is
    NOT collapsed to its bare significant digits) and never more.
  * DIGIT — every slot is an ASCII decimal digit ``digitChar d`` (code point
    ``48 + d % 10``), never a space or other fill.
  * PLACE — slot k carries the correct place-value digit: thousands, hundreds,
    tens, ones, in that most-significant-first ORDER.
  * LEADING — the high slot is ``digitChar (year / 1000 % 10)`` and is NOT
    dropped for a sub-thousand year (the whole point of the change).

ONE INPUT BINDER: ``year : Nat``. It is load-bearing across the ENTIRE result —
every one of the four slots is a place-value function of it. The reject
witnesses drive ``year`` to SIX distinct input points spanning the low
sub-domain (leading-zero years 1 and 999), a boundary at each place, and
four-digit years (1999, 2020, 2345), so the manifest demonstrates the
post-image's dependence on the low-order digits, the high-order digit, the
ORDER of the two most significant slots, and the constant width — not on a
single pinned shape (pts = 6).

CARRIER NOTE — a FULLY TRANSPARENT carrier. Unlike the opaque-callee bundles,
``fourDigitYear`` is a pure function ``Nat → List Char`` computed entirely from
integer ``/`` and ``%``; there are no opaque terms. A witness therefore reaches
the post-image through Velvet's tester machinery (``fourDigitYearTester year =
false`` says the extracted program's result violates the postcondition at that
concrete year) and closes by ``decide`` over a concrete literal — no
conditioning on the carrier is needed. Each reject rival is a loop-free,
branch-only closed form so its extracted tester ``decide``s directly. Every
witness below was built two ways with ``scripts/lean_verify.sh``: it elaborates
green against its rival and FAILS (``decide proved … is false``) against the
frozen solution.

ADVERSARIAL READ of the sibling's classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. FOUR structurally different but
    behaviourally identical impls must verify, else the spec is SPEC-TOO-STRONG
    on the shape of the impl. Two are definitionally equal to the frozen impl
    (return the grounded model directly; bind the four digit characters to typed
    locals first) and so test only that the spec does not over-fit the literal
    write; two are NOT definitionally equal (truncate-then-divide place
    arithmetic; the redundant high-slot clamp dropped) and force a real
    arithmetic identity per slot — the audit additions, since a positive that
    reduces to gold's own goal exercises nothing.
  * ADMISSIBILITY — the sibling self-asserts that F2P-shaped sub-1000 years
    satisfy its fractional-permission precondition. This backend's only
    ``require`` is ``year ≤ 9999`` (met by every calendar year) and there is no
    permission surface, so that probe is degenerate; the residual risk is a
    DEGENERATE post-image. ``admiss-nondegenerate`` discharges an in-region
    ``assert`` pinning the model at the two F2P boundary years (1 → '0001',
    999 → '0999' — the leading-zero behaviour the fix adds) plus an ordinary
    four-digit year (1999 → '1999'); the impl is kept verbatim so the method's
    own obligation still discharges.
  * FRAME-MUTATION — VACUOUS on this backend. The sibling has no owned heap
    input either (``year`` is a value type), but even the general frame class is
    inapplicable: ``year`` is an immutable ``Nat`` declared read-only (not
    ``mut``), Lean/Velvet are referentially transparent, there is no heap and no
    aliasing. No read-only input to overwrite, no permission system to trip. NOT
    ported (fabricating a substitute would test nothing).
  * DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line a single ``return`` over immutable values,
    no loop and no recursion), so there is no control flow here to make
    diverge: a diverging rival cannot be obtained by mutating this body, it has
    to bring a loop of its own. When it does, the semantics refuse it. This
    bundle sets ``loom.semantics.termination "total"`` AND carries
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
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to ``fourDigitString
    year``, a fully-unfolded ``def`` over the method's own argument; there is no
    answer-key term a wrong impl could echo. The cheapest correct impl computes
    the digits honestly, which the positive controls cover.
  * PARTIAL-DOMAIN / VALUE — carries the reject lane: each rival gets most of
    the domain right yet diverges on one sub-domain (leading zero dropped, wrong
    fill character, transposed digits, a units off-by-one on a sub-domain, a
    fifth character on the high sub-domain).
  * AXIOM lane — the sibling's AXIOM_TESTS validates the deep model against the
    real ``'%04d'`` operation; on this backend that is G-AX / G-CONF's job
    (mapping.md §3: the changed op is modeled deeply, no axiom), and this gate
    ignores AXIOM_TESTS regardless. Empty here.
"""
from pathlib import Path

INSTANCE = "django__django-14373"
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
# ---- facts asserted at load). Every full-variant rival / positive swaps this
# ---- block for its own straight-line body.
_IMPL = """    -- impl-start
    return [digitChar (year / 1000 % 10), digitChar (year / 100 % 10),
            digitChar (year / 10 % 10), digitChar (year % 10)]
    -- impl-end"""
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the impl-start marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- the frozen proof body (tactic script only; elided from the spec view).
_PROOF_GOLD = """prove_correct fourDigitYear by
  loom_solve
  simp [fourDigitString]"""
assert _BASE.count(_PROOF_GOLD) == 1, "proof anchor drift"

# ---- a bare-loom_solve proof body: when the impl RETURNS the model directly
# ---- there is nothing left for `simp` to do (the equality is definitional
# ---- after loom_solve), so `simp [fourDigitString]` errors with "no goals".
# ---- The direct-return positive retunes to this shape. Reject rivals also
# ---- carry a proof body, but they are expected to FAIL to verify regardless of
# ---- the tactic shape — the rejection is attributed to the spec by the
# ---- machine-checked witness, never by the proof-script mismatch.
_PROOF_FLAT = "prove_correct fourDigitYear by\n  loom_solve"


def _rewrite_impl(new_block, proof=_PROOF_GOLD):
    """Full variant: whole impl block replaced; proof optionally retuned."""
    out = _swap(_BASE, _IMPL, new_block)
    if proof != _PROOF_GOLD:
        out = _swap(out, _PROOF_GOLD, proof)
    return out


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `fourDigitYearTester year = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete year. Checked in a
# ---- file whose `prove_correct` block has been stripped. The argument is a
# ---- concrete literal so `decide` reduces the (branch-only) extracted rival
# ---- program without getting stuck.
def _tester(body):
    return ("\n"
            "extract_program_for fourDigitYear\n"
            "prove_precondition_decidable_for fourDigitYear\n"
            "prove_postcondition_decidable_for fourDigitYear\n"
            "derive_tester_for fourDigitYear\n\n" + body)


def _witness(year):
    return _tester(
        f"example : fourDigitYearTester {year} = false := by\n  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct-model",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest honest correct impl: return the grounded pure model directly.
        # `out` IS `fourDigitString year`, so the ensures holds trivially; the
        # reproof is a bare `loom_solve` (the equality is definitional, so the
        # frozen `simp [fourDigitString]` arm would error with "no goals").
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return fourDigitString year\n"
            "    -- impl-end",
            proof=_PROOF_FLAT),
        "rationale": (
            "the cheapest honest correct impl returns the grounded model "
            "`fourDigitString year` directly. `out` IS that model, so the ensures "
            "holds on the whole domain; the reproof is `loom_solve`. If this fails "
            "to verify the spec is over-fit to the literal four-element expression "
            "shape (SPEC-TOO-STRONG). Also the honest no-ungrounded-echo control: "
            "the model IS the real work, so a direct return is correct, not a "
            "cheat. (Sibling: pos-cheapest-grounded, re-shaped to a direct return.)"),
    },
    {
        "id": "pos-control-locals",
        "kind": "soundness",
        "expect": "verify",
        # The four place-value digit characters are bound to typed locals FIRST
        # (a local-variable reshape), then written in the same most-significant-
        # first order. Observationally identical for every year; the frozen proof
        # script closes unchanged.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    let c3 := digitChar (year / 1000 % 10)\n"
            "    let c2 := digitChar (year / 100 % 10)\n"
            "    let c1 := digitChar (year / 10 % 10)\n"
            "    let c0 := digitChar (year % 10)\n"
            "    return [c3, c2, c1, c0]\n"
            "    -- impl-end"),
        "rationale": (
            "binding the four digit characters to typed locals before writing them "
            "in the same MS-first order produces the identical list for every "
            "year, so `out = fourDigitString year` still holds on the whole domain "
            "and the frozen proof (`loom_solve; simp [fourDigitString]`) closes "
            "unchanged. A correct local-variable reshape must verify, else the "
            "postcondition is SPEC-TOO-STRONG (rejects a faithful impl over the "
            "shape of the write). (Sibling: pos-control-locals, direct port.)"),
    },
    {
        "id": "pos-control-mod-first",
        "kind": "soundness",
        "expect": "verify",
        # AUDIT ADDITION. The two positives above are, after `loom_solve`, the
        # SAME goal gold faces: the direct-model return makes the ensures
        # definitional (the frozen `simp` arm then errors "no goals"), and the
        # `let`-bound locals zeta-reduce to gold's literal term (measured: under a
        # bare `loom_solve` that case leaves gold's own residual goal verbatim).
        # So neither positive forces ANY arithmetic — the SPEC-TOO-STRONG surface
        # was only probed at impls definitionally equal to the frozen one. This
        # rival shape truncates FIRST and divides second on every slot, which is
        # NOT definitionally equal to the frozen expression: the residual goal
        # needs a real place-value identity per slot (`omega`) before it closes.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return [digitChar (year % 10000 / 1000), digitChar (year % 1000 / 100),\n"
            "            digitChar (year % 100 / 10), digitChar (year % 10)]\n"
            "    -- impl-end",
            proof="prove_correct fourDigitYear by\n"
                  "  loom_solve\n"
                  "  have h1 : year % 10000 / 1000 = year / 1000 % 10 := by omega\n"
                  "  have h2 : year % 1000 / 100 = year / 100 % 10 := by omega\n"
                  "  have h3 : year % 100 / 10 = year / 10 % 10 := by omega\n"
                  "  simp [fourDigitString, h1, h2, h3]"),
        "rationale": (
            "a truncate-then-divide rendering (mask to the low k places, then take "
            "the leading digit of the mask) selects the SAME four place-value "
            "digits as the frozen divide-then-clamp form, but is not "
            "definitionally equal to it — the residual goal is a genuine "
            "arithmetic identity per slot. It must still verify, else the "
            "postcondition is over-fit to one spelling of the place arithmetic "
            "(SPEC-TOO-STRONG). This is the positive the battery lacked: the two "
            "shipped ones reduce to gold's own goal and so exercise no arithmetic "
            "at all. Measured: verifies (exit 0)."),
    },
    {
        "id": "pos-control-unclamped-high",
        "kind": "soundness",
        "expect": "verify",
        # AUDIT ADDITION. On the `require` domain the high slot's `% 10` clamp is
        # REDUNDANT (year ≤ 9999 => year / 1000 ≤ 9), so an impl may legitimately
        # omit it. That is a faithful correct impl whose term differs from the
        # frozen one, and whose equality with it is TRUE ONLY BECAUSE of the
        # precondition — so this positive also checks the spec lets the `require`
        # be USED, not merely carried.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return [digitChar (year / 1000), digitChar (year / 100 % 10),\n"
            "            digitChar (year / 10 % 10), digitChar (year % 10)]\n"
            "    -- impl-end",
            proof="prove_correct fourDigitYear by\n"
                  "  loom_solve\n"
                  "  simp only [fourDigitString, digitChar]\n"
                  "  congr 2\n"
                  "  omega"),
        "rationale": (
            "the high slot's `% 10` is redundant on the required domain "
            "(`year ≤ 9999` forces `year / 1000 ≤ 9`), so dropping it is a "
            "faithful correct impl — and one that is equal to the frozen form ONLY "
            "under the precondition, so the proof must actually consume `require`. "
            "It must verify, else the spec rejects a correct impl over a redundant "
            "clamp (SPEC-TOO-STRONG) or fails to make its own precondition "
            "available. Measured: verifies (exit 0)."),
    },

    # =====================================================================
    # ADMISSIBILITY — the method's only `require` (`year ≤ 9999`) is met by every
    # F2P-shaped input, so the sibling's "a normal sub-1000 year satisfies the
    # precondition" probe is degenerate here. The residual admissibility risk on
    # this domain is that the post-image is DEGENERATE at the interesting point.
    # This case discharges an in-region `assert`, at three fully concrete
    # F2P-shaped years, that the post-image is NON-DEGENERATE and matches the
    # intended rendering: year 1 → '0001' and year 999 → '0999' (the leading-zero
    # behaviour the fix adds), and an ordinary year 1999 → '1999'. The
    # surrounding impl is kept verbatim so the method's own obligation still
    # discharges; the proof gains a `decide` arm to clear the assert goal.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(_BASE, _IMPL_START,
                  _IMPL_START +
                  "    assert (with_name_prefix `admiss (\n"
                  "      fourDigitString 1 = ['0','0','0','1'] ∧\n"
                  "      fourDigitString 999 = ['0','9','9','9'] ∧\n"
                  "      fourDigitString 1999 = ['1','9','9','9']))\n"),
            _PROOF_GOLD,
            "prove_correct fourDigitYear by\n"
            "  loom_solve\n"
            "  all_goals first\n"
            "    | decide\n"
            "    | simp [fourDigitString]\n"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P-shaped "
            "years: year 1 must render '0001' and year 999 must render '0999' (the "
            "retained leading zeros — the sub-1000 behaviour the fix adds), while a "
            "four-digit year 1999 renders '1999'. The in-region assert must "
            "discharge (else the obligation is degenerate / the precondition too "
            "strong); the impl is kept verbatim so `out = fourDigitString year` "
            "still verifies. (Sibling: admiss-self-call, re-aimed from precondition "
            "admissibility to post-image non-degeneracy since this backend's only "
            "require is `year ≤ 9999` and there is no permission surface.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete year and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Each rival is a branch-only
    # closed form so its extracted tester `decide`s (see the CARRIER NOTE); the
    # frozen spec is untouched.
    # =====================================================================
    {
        "id": "weak-leading-zero-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        # Port of sibling weak-leading-zeros-dropped (the pre-patch skeleton):
        # when the high (thousands) digit is 0 the result drops it, yielding THREE
        # characters for a sub-1000 year. Correct on every four-digit year;
        # diverges on the low sub-domain — the whole point of the change.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    if year / 1000 % 10 = 0 then\n"
            "      return [digitChar (year / 100 % 10), digitChar (year / 10 % 10),\n"
            "              digitChar (year % 10)]\n"
            "    else\n"
            "      return [digitChar (year / 1000 % 10), digitChar (year / 100 % 10),\n"
            "              digitChar (year / 10 % 10), digitChar (year % 10)]\n"
            "    -- impl-end",
            proof=_PROOF_FLAT),
        "refinement": (
            "this is the pre-change behaviour: a year is rendered by its bare "
            "significant digits, dropping the leading zeros of a sub-thousand year, "
            "so the smallest calendar year renders as a single character and a "
            "three-digit year as three characters. The failing scenario asserts the "
            "fixed four-character forms '0001' and '0999' for those years — a "
            "three-character rendering does NOT match, so the faithful real patch "
            "does NOT resolve. Correct on every four-digit year (a true "
            "partial-domain break)."),
        "rationale": (
            "REJECT from `out = fourDigitString year` via the WIDTH and LEADING "
            "facts: the spec pins a four-element list whose high slot is "
            "`digitChar (year / 1000 % 10)`, but for a sub-1000 year this returns a "
            "three-element list dropping that slot. Verifying would be "
            "SPEC-TOO-WEAK (the constant width / retained leading zero unpinned). "
            "Refuted at year 1 (the smallest F2P witness). (Sibling: "
            "weak-leading-zeros-dropped.)"),
        "witness": _witness(1),
    },
    {
        "id": "weak-space-pad",
        "kind": "uniqueness",
        "expect": "reject",
        # Port of sibling weak-space-pad: pad to width four but fill the high slot
        # with an ASCII SPACE (code point 32) instead of the zero digit, on the
        # sub-1000 sub-domain. Width is right; the fill is not a decimal digit.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    if year / 1000 % 10 = 0 then\n"
            "      return [Char.ofNat 32, digitChar (year / 100 % 10),\n"
            "              digitChar (year / 10 % 10), digitChar (year % 10)]\n"
            "    else\n"
            "      return [digitChar (year / 1000 % 10), digitChar (year / 100 % 10),\n"
            "              digitChar (year / 10 % 10), digitChar (year % 10)]\n"
            "    -- impl-end",
            proof=_PROOF_FLAT),
        "refinement": (
            "this is the space-pad mistake instead of the zero-pad: a sub-thousand "
            "year is padded to width four with leading spaces rather than leading "
            "zeros. The failing scenario asserts literal zero characters ('0001' / "
            "'0999'); a space-padded rendering does NOT match, so the faithful real "
            "patch does NOT resolve. Correct on every four-digit year and on the "
            "width."),
        "rationale": (
            "REJECT from `out = fourDigitString year` via the DIGIT and LEADING "
            "facts: the high slot must be `digitChar (year / 1000 % 10)` (code "
            "point 48 for a sub-1000 year), but this returns code point 32 (a "
            "space), which is not an ASCII decimal digit. Verifying would be "
            "SPEC-TOO-WEAK (the each-slot-is-a-digit / leading-digit facts "
            "unpinned). Refuted at year 999 (sub-1000, exercises the space-pad "
            "branch at a different low year than the leading-zero-drop rival). "
            "(Sibling: weak-space-pad.)"),
        "witness": _witness(999),
    },
    {
        "id": "weak-transpose-tens-units",
        "kind": "uniqueness",
        "expect": "reject",
        # Port of sibling weak-transpose-tens-units: width four, every slot a
        # digit, but the tens and units slots are swapped. A proxy checking only
        # "width four, all digits" would miss it; the PLACE (order) fact catches
        # the transposition wherever tens ≠ units.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return [digitChar (year / 1000 % 10), digitChar (year / 100 % 10),\n"
            "            digitChar (year % 10), digitChar (year / 10 % 10)]\n"
            "    -- impl-end",
            proof=_PROOF_FLAT),
        "refinement": (
            "this transposes the tens and units slots (e.g. year 42 → '0024', year "
            "2021 → '2012'). The intended rendering never reorders digits; the "
            "pass-to-pass dateformat scenarios assert the exact rendered year "
            "string, so the faithful real patch does NOT resolve on any year whose "
            "tens and units differ. Correct on the width and on years ending in a "
            "repeated digit (a place-order break)."),
        "rationale": (
            "REJECT from `out = fourDigitString year` via the PLACE (order) fact: "
            "slot 2 must be the tens digit and slot 3 the ones digit, but this "
            "swaps them. Verifying would be SPEC-TOO-WEAK (the most-significant-"
            "first order unpinned). Refuted at year 42 (tens 4 ≠ units 2, so the "
            "swap is observable; also a low sub-domain year distinct from the other "
            "witnesses). (Sibling: weak-transpose-tens-units.)"),
        "witness": _witness(42),
    },
    {
        "id": "weak-units-plus-one-on-zero",
        "kind": "uniqueness",
        "expect": "reject",
        # Port of sibling weak-units-plus-one-on-zero: render correctly except set
        # the ones slot to '1' when the units digit is 0. Correct on every year
        # not ending in 0; wrong on multiples of ten — a near-miss.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    if year % 10 = 0 then\n"
            "      return [digitChar (year / 1000 % 10), digitChar (year / 100 % 10),\n"
            "              digitChar (year / 10 % 10), digitChar 1]\n"
            "    else\n"
            "      return [digitChar (year / 1000 % 10), digitChar (year / 100 % 10),\n"
            "              digitChar (year / 10 % 10), digitChar (year % 10)]\n"
            "    -- impl-end",
            proof=_PROOF_FLAT),
        "refinement": (
            "this corrupts the ones slot for years ending in zero (year 2020 → "
            "'2021', year 10 → '0011'). The intended rendering of a year ending in "
            "zero writes a '0' in the ones slot; the pass-to-pass dateformat "
            "scenarios assert the exact year string, so the faithful real patch "
            "does NOT resolve on any year ending in zero. Correct on every year "
            "whose ones digit is non-zero (a partial-domain break)."),
        "rationale": (
            "REJECT from `out = fourDigitString year` via the PLACE fact on the "
            "ones slot: it must be `digitChar (year % 10)` (code point 48 when the "
            "units digit is 0), but this returns `digitChar 1` (code point 49). "
            "Verifying would be SPEC-TOO-WEAK (the ones digit unpinned on the "
            "ends-in-zero sub-domain). Refuted at year 2020 (units 0, a four-digit "
            "year — exercises `year % 10 = 0`, which no other witness does). "
            "(Sibling: weak-units-plus-one-on-zero.)"),
        "witness": _witness(2020),
    },
    {
        "id": "weak-five-chars-high",
        "kind": "uniqueness",
        "expect": "reject",
        # Port of sibling weak-five-chars-high (the inverse of leading-zero-drop):
        # append a spurious trailing zero for a four-digit year, yielding FIVE
        # characters, while sub-1000 years stay four. Correct length only on the
        # low sub-domain.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    if year / 1000 % 10 = 0 then\n"
            "      return [digitChar (year / 1000 % 10), digitChar (year / 100 % 10),\n"
            "              digitChar (year / 10 % 10), digitChar (year % 10)]\n"
            "    else\n"
            "      return [digitChar (year / 1000 % 10), digitChar (year / 100 % 10),\n"
            "              digitChar (year / 10 % 10), digitChar (year % 10), digitChar 0]\n"
            "    -- impl-end",
            proof=_PROOF_FLAT),
        "refinement": (
            "this appends a spurious trailing '0' for four-digit years (year 1999 → "
            "'19990'). The intended rendering is exactly four characters; the "
            "pass-to-pass dateformat scenarios assert the four-character year, so "
            "the faithful real patch does NOT resolve on any four-digit year. "
            "Correct on every sub-1000 year (the inverse partial-domain of the "
            "leading-zero-drop rival)."),
        "rationale": (
            "REJECT from `out = fourDigitString year` via the WIDTH fact: the "
            "result must be exactly four characters, but for a four-digit year this "
            "returns five. Verifying would be SPEC-TOO-WEAK (the upper width bound "
            "unpinned). Refuted at year 1999 (four-digit, so the fifth character is "
            "emitted — the complementary sub-domain to weak-leading-zero-dropped, "
            "which the two therefore do not share). (Sibling: weak-five-chars-high.)"),
        "witness": _witness(1999),
    },
    {
        "id": "weak-transpose-thousands-hundreds",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT ADDITION. The shipped transpose rival swaps only the LOW pair
        # (tens/ones), so the PLACE fact was never attacked on the HIGH pair: no
        # existing rival reorders the two most significant slots, and none is
        # refuted at a year whose thousands and hundreds digits differ while its
        # tens and ones are ordinary. This swaps the thousands and hundreds slots
        # — width four, every slot a genuine digit of the year, the same multiset
        # — so only the most-significant-first ORDER separates it from the spec.
        "module": _rewrite_impl(
            "    -- impl-start\n"
            "    return [digitChar (year / 100 % 10), digitChar (year / 1000 % 10),\n"
            "            digitChar (year / 10 % 10), digitChar (year % 10)]\n"
            "    -- impl-end",
            proof=_PROOF_FLAT),
        "refinement": (
            "this transposes the two most significant slots (year 2345 → '3245', "
            "year 1999 → '9199'). The intended rendering never reorders digits; the "
            "pass-to-pass dateformat scenarios assert the exact rendered year "
            "string, so the faithful real patch does NOT resolve on any year whose "
            "thousands and hundreds digits differ. Correct on the width, on every "
            "slot being a digit, and on years whose leading two digits repeat."),
        "rationale": (
            "REJECT from `out = fourDigitString year` via the PLACE (order) fact on "
            "the HIGH pair: slot 0 must be `digitChar (year / 1000 % 10)` and slot "
            "1 `digitChar (year / 100 % 10)`, but this swaps them. Verifying would "
            "be SPEC-TOO-WEAK (the MS-first order unpinned at the top of the "
            "field, which the tens/ones transpose rival does not cover). Refuted at "
            "year 2345 — thousands 2 ≠ hundreds 3, and a year no other witness "
            "uses. Measured: witness elaborates against the rival (exit 0) and is "
            "refuted against the frozen solution (exit 1, `decide` proved the "
            "tester claim false)."),
        "witness": _witness(2345),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 8 SPEC cases (2
# soundness positives, 1 admissibility, 5 uniqueness rivals) plus a single-case
# AXIOM lane. The sibling contracts `render_year` over a plain `int` year and
# returns a `List[int]` of ASCII code points, pinning SIX postcondition facts.
# This backend models the SAME rendering DEEPLY and CONCRETELY (`fourDigitString`
# / `digitChar` over `Nat` / `List Char`), and the returned `List Char` observes
# exactly the same width / per-slot-digit / place-value / leading-digit content,
# so ALL of the sibling's SPEC cases have a faithful carrier analogue.
#
#   sibling case                  kind          -> here                        disposition
#   ---------------------------------------------------------------------------------------
#   pos-control-locals            soundness     -> pos-control-locals          PORTED
#   pos-cheapest-grounded         soundness     -> pos-control-direct-model    RE-SHAPED
#   admiss-self-call              admissibility -> admiss-nondegenerate        RE-AIMED
#   weak-leading-zeros-dropped    uniqueness    -> weak-leading-zero-dropped   PORTED
#   weak-space-pad                uniqueness    -> weak-space-pad              PORTED
#   weak-transpose-tens-units     uniqueness    -> weak-transpose-tens-units   PORTED
#   weak-units-plus-one-on-zero   uniqueness    -> weak-units-plus-one-on-zero PORTED
#   weak-five-chars-high          uniqueness    -> weak-five-chars-high        PORTED
#   AXIOM_TESTS (1 A-reference)   axiom         -> (none)                      N/A (G-AX/G-CONF)
#
# 5 uniqueness ported, 1 admissibility re-aimed, 1 soundness ported + 1 re-shaped;
# 0 vacuous; axiom lane dropped (this gate ignores AXIOM_TESTS; the deep-model
# validation is G-AX / G-CONF's job — mapping.md §3 records no axiom).
#
# AUDIT ADDITIONS (3 cases beyond the sibling's 8; independent adversarial pass).
#   pos-control-mod-first        soundness  NEW — truncate-then-divide place
#                                          arithmetic; verifies (exit 0)
#   pos-control-unclamped-high   soundness  NEW — the redundant high-slot clamp
#                                          dropped; verifies (exit 0)
#   weak-transpose-thousands-hundreds
#                                uniqueness NEW — the HIGH pair transposed;
#                                          rejected, witness at year 2345
#                                          (rival exit 0 / gold exit 1)
#
# WHY the two positives were added: both shipped positives, after `loom_solve`,
#   present gold's OWN residual goal or none at all. `pos-control-direct-model`
#   makes the ensures definitional (measured: the frozen `simp [fourDigitString]`
#   arm then errors `No goals to be solved`, which is why that case retunes to a
#   bare `loom_solve`), and `pos-control-locals`' `let`-bound locals zeta-reduce
#   to gold's literal term (measured: under a bare `loom_solve` it leaves gold's
#   residual goal verbatim, and it closes under the frozen script unchanged). Both
#   are therefore DEFINITIONALLY EQUAL to the frozen impl, so they honestly pass
#   while forcing no arithmetic: the SPEC-TOO-STRONG surface was untested against
#   any impl whose equality with the frozen one is a non-trivial fact. The two new
#   positives are not definitionally equal (each needs a per-slot `omega`
#   identity, and the unclamped one is equal ONLY under the `require`), so they
#   probe that surface for the first time — and the unclamped case additionally
#   checks the precondition is USABLE in the proof, not merely carried.
# WHY the high transpose was added: the ported PLACE-order attack swaps only the
#   tens/ones pair, leaving the two most significant slots' ORDER unattacked, and
#   no shipped witness sits at a year whose thousands and hundreds digits differ.
#
# AUDIT-MEASURED, NOT SHIPPED (attack D / E probes that behaved correctly, so
# there is nothing to add for them): a diverging `while` body is rejected under
# `total` with `Decreasing annotations are required in total correctness
# semantics` (so the divergence class really is closed here, as recorded); an
# infeasible `:|` choice (`junk = 0 ∧ junk = 1`) cannot discharge its own
# feasibility goal `∃ h, h = 0 ∧ h = 1`, so vacuity-by-empty-choice is closed; a
# wrong impl lying only at year 0, only at year 9999, or writing the ones digit
# into all four slots is rejected; an impl wrong only ABOVE the `require` domain
# verifies, which is correct (the real domain excludes it — mapping.md §2). An
# append-shaped correct reshape (`[a] ++ [b, c] ++ [d]`) verifies under the FROZEN
# proof script unchanged, so it is definitionally equal too and adds nothing the
# two new positives do not already cover.
#
# RE-SHAPED (pos-cheapest-grounded -> pos-control-direct-model): the sibling's
#   cheapest-honest positive inlines the place arithmetic and appends the digits.
#   On this carrier the maximally-different correct impl is a loop-free direct
#   return of the grounded model `fourDigitString year`; the sibling's OTHER
#   positive (pos-control-locals) ports directly as a typed-local reshape, so the
#   soundness surface is defended both from a direct model return AND from a
#   local-variable reshape that keeps the frozen proof.
# RE-AIMED (admiss-self-call -> admiss-nondegenerate): the sibling asserts that
#   F2P-shaped sub-1000 years satisfy its precondition and reads back post facts.
#   This backend's only `require` is `year ≤ 9999` (met by every calendar year)
#   and there is no permission surface, so that probe is degenerate; the sharper
#   residual risk is a DEGENERATE post-image, so the case is re-aimed to a live
#   in-region assert pinning the model at the two F2P boundary years (1 → '0001',
#   999 → '0999') plus a four-digit year (1999 → '1999').
# PORTED (the five value/width rivals): each maps directly to the same wrong
#   rendering expressed over `List Char`. weak-leading-zeros-dropped (pre-patch
#   skeleton) → three-element list on the low sub-domain (refuted at year 1);
#   weak-space-pad → space fill in the high slot (refuted at year 999);
#   weak-transpose-tens-units → swapped tens/ones slots (refuted at year 42);
#   weak-units-plus-one-on-zero → ones slot corrupted on multiples of ten
#   (refuted at year 2020); weak-five-chars-high → spurious fifth character on the
#   high sub-domain (refuted at year 1999).
#
# BINDER / CLAUSE COVERAGE. The sole `ensures` clause `out = fourDigitString
#   year` has ONE binder — `year : Nat` — which is load-bearing across the entire
#   result (all four slots are place-value functions of it). The five reject
#   witnesses probe five DISTINCT years (pts=5): 1, 999, 42, 2020, 1999 — spanning
#   the leading-zero sub-domain (1, 999), a tens/ones boundary (42), a
#   units-is-zero four-digit year (2020) and an ordinary four-digit year (1999).
#   (The audit added a sixth witness year, 2345, for the high-pair transpose.)
#   All four independent facts of `fourDigitString` are attacked: WIDTH (both
#   below — weak-leading-zero-dropped, three chars — and above —
#   weak-five-chars-high, five chars), DIGIT (weak-space-pad, a non-digit fill),
#   PLACE / ORDER (weak-transpose-tens-units and weak-units-plus-one-on-zero), and
#   LEADING (weak-leading-zero-dropped and weak-space-pad both attack the high
#   slot on the sub-1000 sub-domain, one by dropping it, one by mis-filling it).
#   No two rivals share a witness: the leading-zero-drop and five-chars rivals sit
#   on COMPLEMENTARY sub-domains (year < 1000 vs year ≥ 1000), and the units and
#   transpose rivals are separated at years that make their respective mistakes
#   observable.
#
# FRAME-MUTATION & DIVERGENCE: both VACUOUS here, not ported. Frame-mutation has
#   no owned read-only heap input to overwrite on a referentially-transparent
#   carrier (`year` is an immutable `Nat` value, not `mut`). Divergence is closed
#   by the VERIFIER under `set_option loom.semantics.termination "total"`: the
#   frozen impl is straight-line pure with no loop/recursion, so no divergence
#   rival is SHIPPED here, but a rival owns the whole impl region and CAN splice a
#   loop of its own, and it then owes a decreasing measure AND its descent.
#   Measured with the proof reduced to `loom_solve`: with the measure omitted the
#   refusal is at the `method` declaration ("Decreasing annotations are required in
#   total correctness semantics"); with a measure supplied that does not decrease
#   (`decreasing z`, body `z := z + 1`) the refusal is on the measure's own goal,
#   `case «decreasing_1: z»`, residual `z + 1 < z`. This is NOT a known spec hole;
#   vacuous verification is the `partial` disposition, and no velvet bundle sets
#   `partial`.
#
# AXIOM_TESTS: empty. The changed op is modeled deeply (mapping.md §3: no axiom;
#   the `'%04d'` correspondence is validated by G-CONF), so there is nothing for
#   the axiom lane, and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
