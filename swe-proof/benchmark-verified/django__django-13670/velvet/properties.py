"""properties.py — G-PBT falsification battery for django__django-13670 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct twoDigitYear`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation, checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must elaborate against the rival and FAIL against
the frozen solution).

DEFENDED SURFACE (one contracted method):

  twoDigitYear (year : Nat) return (out : List Char)
    require year ≤ 9999
    ensures out = twoDigitString (year % 100)          -- the WHOLE pin (C1)

The method renders the abbreviated (short) form of a calendar year as a
fixed-width two-character decimal: the part below one hundred, tens char then
ones char, so a value below ten still occupies two slots (a leading '0'). The
whole rendering is the pure, TRANSPARENT ``def twoDigitString``, itself built
from the transparent ``def digitChar``; both are total functions of the method's
own input ``year``. There is NO opaque answer-key oracle (the ``axioms`` region
is empty), so pinning ``out = twoDigitString (year % 100)`` is GROUNDED, not an
echo.

WHICH CLAUSE CONSTRAINS THE IMPL. C1 is the sole clause and it is a single
top-level equality of ``List Char``, so it simultaneously pins THREE
distinguishable obligations, each attacked by some rival below:
  * WIDTH — the output is exactly two characters (``List.length`` = 2). A rival
    that emits fewer (drop the high slot for small years) or more (a hundreds
    digit for large years, an extra duplicated char) violates it.
  * SLOT 0 — ``out[0] = digitChar ((year % 100) / 10 % 10)`` (the tens char).
    Attacked both at full width (``weak-tens-off-by-one``) and on the
    leading-zero sub-domain alone (``weak-trunc-sub-seam``).
  * SLOT 1 — ``out[1] = digitChar ((year % 100) % 10)`` (the ones char).
    Attacked IN ISOLATION by ``weak-ones-dup-tens`` (width 2 and slot 0 both
    correct, so only the slot-1 pin can reject it) as well as jointly by
    ``weak-swap-slots``.
Each obligation is additionally probed at the BOUNDARY of the admitted domain by
``weak-top-of-domain`` (wrong at year=9999 only), so C1 is shown to constrain the
edge of ``require year ≤ 9999`` and not merely the interior.
The load-bearing bug the gold fix corrects is the WIDTH obligation on the
sub-hundred / sub-ten regime (the F2P witness 4 -> "04"): the pre-fix skeleton
inherits the magnitude of the FULL year and loses the high-order slot(s) for
every year whose decimal width is not four.

CARRIER NOTE — the ``digitChar`` clamp and the nagini "wrong modulus" rival.
The nagini sibling's R2 reduces the year modulo 1000 instead of 100 and then
lays down two RAW code points (``48 + v//10``), which for year 476 reaches 95
(outside the decimal-digit range). On THIS carrier the per-digit renderer
``digitChar`` clamps by ``% 10`` and ``twoDigitString`` extracts exactly the last
two decimal digits, so a rival that reduces mod 1000 but renders the SAME two
``digitChar``-clamped slots is DEFINITIONALLY EQUAL to gold — the extra
high-order magnitude is discarded by the two ``% 10`` clamps, and the rival is
not wrong on this carrier. The FAITHFUL real counterpart it models — the same width-2 rendering applied
to the year reduced modulo one THOUSAND — does not collapse: for year 476 it
renders "476" — THREE characters. So R2 is ported as its true behaviour, a WIDTH violation for years
whose sub-thousand part is >= 100 (an extra hundreds char), refuted at 476.
(This is the "abstraction may collapse a distinction nagini kept" case, handled
by re-expressing the rival at the level where it genuinely diverges.)

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME/PERMISSION-MUTATION — VACUOUS. Lean and Velvet are referentially
    transparent: no heap, no aliasing, no fractional permission. ``year`` is an
    immutable ``Nat`` value and the method declares no ``mut`` binder, so there
    is no read-only input to overwrite. The nagini sibling ALSO records this
    class as N/A ("no full-permission read-only list param; year is an int
    scalar"). No substitute probe is fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A as an ATTACK. C1's post-image is the
    transparent ``twoDigitString (year % 100)``, a closed-form function of the
    input, not an opaque answer key. There is no wrong echo to build; the honest
    cheapest CORRECT impl (``return twoDigitString (year % 100)``) is carried as
    a POSITIVE control instead, doubling as proof the spec is not
    echo-vulnerable (any wrong per-digit computation fails the grounded pin).
  * CONTROL-FLOW EFFECT — N/A. The method is pure value computation; there is no
    raise / side-effect distinction the value model misses. (The nagini sibling
    reaches the same conclusion.)
  * WIDTH / SLOT / PARTIAL-DOMAIN — the whole reject surface, all against C1.

DIVERGENCE LANE - the class is INAPPLICABLE to this impl and CLOSED BY THE
SEMANTICS against any rival that manufactures it. The frozen impl is LOOP-FREE
(straight-line ``let`` over immutable values, no loop and no recursion), so
there is no control flow here to make diverge: a diverging rival cannot be
obtained by mutating this body, it has to bring a loop of its own. When it
does, the semantics refuse it. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
two lines have to move together and they do here. Under the total scope a
postcondition is claimed of ALL runs and not only of terminating ones, so a
spliced loop owes a descent obligation ``measure b' < measure b``. Re-measured
on this bundle with a real build: a ``while spin > 0 do spin := spin`` prefix
carrying ``decreasing spin`` is REJECTED on the measure's own goal (``case
«decreasing_1: spin» ... ⊢ spin < spin``). Dropping the clause rather than
faking it is refused even earlier, by the elaborator's own check (``Decreasing
annotations are required in total correctness semantics``). So divergence
neither applies to this impl nor discharges the ``ensures`` clauses vacuously
if a rival introduces it.

WITNESS MECHANICS. C1's post-image is fully TRANSPARENT and every rival is
loop-free (an if-ladder or a bare list literal over concrete ``Nat`` arithmetic),
so the tester+``decide`` path is live: ``extract_program_for`` /
``derive_tester_for`` yield a computable ``twoDigitYearTester : Nat -> Bool``,
and each witness asserts ``twoDigitYearTester <year> = false`` — the extracted
program's output violates C1 at that concrete year. Against the FROZEN solution
the same statement FAILS (gold satisfies C1, so the tester returns ``true`` and
``= false`` is not provable), exactly the discrimination the gate requires. Every
witness input is a concrete ``Nat`` literal satisfying the precondition
(``year ≤ 9999``); no witness binds a hypothesis, so no consistency probe is
needed. No banned token (sorry/admit/native_decide/axiom). Each witness was
checked out-of-band with ``scripts/lean_verify.sh``: it ELABORATES against its
rival (exit 0) and FAILS against gold (exit 1). The gold-side failure is a
SEMANTIC refutation in every case, not a missing identifier or an unfolding
failure — the error text is ``Tactic `decide` proved that the proposition
twoDigitYearTester <year> = false is false``, i.e. the tester returns ``true``
because gold SATISFIES C1 at that year. Both sides are stated in the shared
vocabulary (``twoDigitYearTester`` comes from the witness's own directives, which
are appended to both files), so no witness can pass by naming something only one
side has.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom`` (the rendering is
modeled deeply by ``twoDigitString`` / ``digitChar``); the nagini sibling's
``AXIOM_TESTS`` is likewise empty, and the gate ignores ``AXIOM_TESTS`` anyway.
"""
from pathlib import Path

INSTANCE = "django__django-13670"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the entire frozen impl body plus both markers, so the
# ---- swap lies wholly inside the single `-- impl-start`/`-- impl-end` region
# ---- and is unique in Solution.lean (both facts asserted at load by _swap).
_IMPL = (
    "    -- impl-start\n"
    "    let n := year % 100\n"
    "    return [digitChar (n / 10 % 10), digitChar (n % 10)]\n"
    "    -- impl-end"
)
assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"

# ---- proof anchor: the frozen `prove_correct` tactic body. Positive-control
# ---- reshapes may retune THIS block (it is elided from the spec view); reject
# ---- rivals leave it as-is (the rejection is carried by the witness, and the
# ---- proof fails to close against a wrong impl regardless).
_PROOF = (
    "prove_correct twoDigitYear by\n"
    "  loom_solve\n"
    "  simp [twoDigitString]"
)
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(body):
    """Full variant: only the impl body (between the markers) replaced."""
    return _swap(_BASE, _IMPL,
                 "    -- impl-start\n" + body + "\n    -- impl-end")


def _impl_reproved(body, proof):
    """Impl body replaced AND the proof retuned (for correct reshapes whose
    residual goal differs from the frozen one)."""
    return _swap(_impl(body), _PROOF, proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `twoDigitYearTester <year> = false` says the extracted program's result
# ---- violates C1 at that concrete year. Checked in a file whose `prove_correct`
# ---- block has been stripped, so no tactic script can mask the verdict. Every
# ---- input is a concrete Nat literal so `decide` reduces the loop-free
# ---- extracted program without getting stuck.
def _witness(year):
    return (
        "\n"
        "extract_program_for twoDigitYear\n"
        "prove_precondition_decidable_for twoDigitYear\n"
        "prove_postcondition_decidable_for twoDigitYear\n"
        "derive_tester_for twoDigitYear\n\n"
        f"example : twoDigitYearTester {year} = false := by\n  decide\n"
    )


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
        # Cheapest honest correct impl: return the grounded pure model directly,
        # no per-slot construction. `out` IS `twoDigitString (year % 100)`, so C1
        # holds trivially — and since that post-image is GROUNDED in the input
        # (not an opaque answer key), this doubles as proof the spec is not
        # echo-vulnerable. The reproof drops the frozen `simp [twoDigitString]`
        # step (the goal is `x = x` after `loom_solve`).
        "module": _impl_reproved(
            "    return twoDigitString (year % 100)",
            "prove_correct twoDigitYear by\n  loom_solve"),
        "rationale": (
            "the post-image `twoDigitString (year % 100)` is GROUNDED in the "
            "input (a transparent def, no opaque answer key), so `return "
            "twoDigitString (year % 100)` is the honest cheapest CORRECT impl; C1 "
            "is literally `out = twoDigitString (year % 100)`, so it MUST verify, "
            "else C1 is SPEC-TOO-STRONG. Ports the nagini honest cheapest-impl "
            "control (its @Pure helpers were fully unfolded; here the whole "
            "renderer is the transparent model)."
        ),
    },
    {
        "id": "pos-control-slot-locals",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: compute the two code points into typed locals in the REVERSE
        # order (ones char first, tens char second) and assemble the pair from
        # the locals. Same value flow, different construction order; the frozen
        # proof still closes (the assembled list is definitionally the gold one).
        "module": _impl(
            "    let n := year % 100\n"
            "    let ones := digitChar (n % 10)\n"
            "    let tens := digitChar (n / 10 % 10)\n"
            "    return [tens, ones]"),
        "rationale": (
            "a correct impl with a DIFFERENT construction shape (bind the ones "
            "char and tens char to typed locals in reverse order, then assemble "
            "the pair) must verify; the value flow is unchanged (`[tens, ones] = "
            "[digitChar (n/10%10), digitChar (n%10)]` definitionally) so C1 "
            "discharges and the frozen proof closes as-is. Ports the nagini "
            "pos-control-reorder (units computed first, tens second, into a "
            "local bound before return). If it fails => SPEC-TOO-STRONG (over-fit "
            "to the inline-literal code form)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — the nagini admiss-year4 established TWO things: that the
    # precondition is USABLE at a call site for a legitimate in-domain year, and
    # that the postcondition then discharges at the F2P-shaped point (4 -> "04").
    # An admissibility case whose module is the FROZEN FILE VERBATIM establishes
    # neither: it re-runs the artifact's own build (already G-VERIFY's job) and
    # is satisfied no matter how unusable the precondition is, because nothing in
    # it ever has to CONSUME `year ≤ 9999`. So the case is aimed at the two real
    # residual risks instead, both inside the elided regions:
    #   (a) the precondition must be ASSUMABLE — the impl's in-domain arm is
    #       guarded by `year ≤ 9999` itself, so the residual goal is closable
    #       ONLY by discharging the `else` arm from `require_1`. Measured: with
    #       the frozen `simp [twoDigitString]` this variant does NOT close
    #       (`unsolved goals`); it closes exactly when `require_1` is supplied.
    #       A vacuous or unsatisfiable precondition would fail here.
    #   (b) the post-image must be jointly SATISFIABLE and pin the F2P-shaped
    #       point, machine-checked by two `have`s decided in the proof body:
    #       `twoDigitString (4 % 100) = ['0','4']` (the sub-ten leading-zero
    #       point the change defends) and `twoDigitString (9999 % 100) =
    #       ['9','9']` (the top of the admitted domain). An unsatisfiable or
    #       mis-stated post-image cannot produce both.
    # MUST verify, else PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-precond-usable",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    let n := year % 100\n"
            "    let out : List Char :=\n"
            "      if year ≤ 9999 then [digitChar (n / 10 % 10), digitChar (n % 10)]\n"
            "      else []\n"
            "    return out",
            "prove_correct twoDigitYear by\n"
            "  loom_solve\n"
            "  have hF2P : twoDigitString (4 % 100) = ['0', '4'] := by decide\n"
            "  have hTop : twoDigitString (9999 % 100) = ['9', '9'] := by decide\n"
            "  simp [twoDigitString, require_1]"),
        "rationale": (
            "re-aims the nagini admiss-year4 at what is actually at risk here. "
            "The impl's in-domain arm is guarded by the precondition itself, so "
            "the `else []` arm is dischargeable ONLY from `require_1 : year ≤ "
            "9999` — the precondition must be ASSUMABLE, which is the carrier's "
            "counterpart of the nagini call site establishing `Requires`. "
            "Measured: the same variant with the frozen `simp [twoDigitString]` "
            "alone leaves `unsolved goals`, so the precondition is genuinely "
            "load-bearing in this case and not decoration. Two `have`s decided "
            "in the proof body additionally pin the post-image at the F2P-shaped "
            "sub-ten point (4 -> \"04\", the leading-zero seam) and at the top of "
            "the admitted domain (9999 -> \"99\"), so an unsatisfiable or "
            "mis-stated post-image fails. Deliberately NOT the frozen file "
            "verbatim: that module consumes the precondition nowhere and would "
            "verify however unusable `require` was, re-testing only the "
            "artifact's own build. Else PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete year and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. The sole binder `year` is varied
    # across nine distinct points (4, 476, 42, 13, 9, 25, 1970, 2005, 9999),
    # spanning the sub-ten, teens, tens, three-digit, four-digit and
    # domain-boundary regimes.
    # =====================================================================
    {
        "id": "weak-prepatch-slice",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch behaviour reproduced deeply (the `Solution_prepatch.lean`
        # skeleton): the short year inherits the magnitude of the FULL year — a
        # year below 100 loses everything (empty), a three-digit year keeps only
        # its final char, only a four-digit year keeps two. Violates the WIDTH
        # obligation of C1 for every year whose decimal width is not four.
        "module": _impl(
            "    let out : List Char :=\n"
            "      if year < 100 then []\n"
            "      else\n"
            "        if year < 1000 then [digitChar (year % 10)]\n"
            "        else [digitChar (year / 10 % 10), digitChar (year % 10)]\n"
            "    return out"),
        "refinement": (
            "this IS the pre-patch body (render the whole year in decimal, drop "
            "its first two characters). Its faithful real patch is the unpatched "
            "repo: the F2P expects 4 -> '04', 42 -> '42', 476 -> "
            "'76', but the drop-first-two-chars behaviour yields '' for 4 and 42 "
            "and a single char for 476, so it would NOT resolve. This is the "
            "exact defect the fix corrects."
        ),
        "rationale": (
            "REJECT from C1's WIDTH obligation: for year=4 (< 100) the result is "
            "the empty list, whose length is 0, not the two chars `['0','4']` the "
            "post-image `twoDigitString (4 % 100)` pins. Refuted at year=4. If it "
            "verified the fixed-width guarantee would go unsensed => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _witness(4),
    },
    {
        "id": "weak-mod1000-width",
        "kind": "uniqueness",
        "expect": "reject",
        # The nagini "wrong modulus" rival, re-expressed at the level where it
        # genuinely diverges on this carrier. Reducing mod 1000 and rendering the
        # same two `digitChar`-clamped slots would collapse to gold (the extra
        # magnitude is discarded by the two `% 10` clamps), so the FAITHFUL
        # behaviour of the mod-1000 counterpart is modeled: an extra hundreds char
        # whenever the sub-thousand part is >= 100. Violates the WIDTH obligation
        # for such years; correct for year < 100.
        "module": _impl(
            "    let v := year % 1000\n"
            "    let out : List Char :=\n"
            "      if v < 100 then [digitChar (v / 10 % 10), digitChar (v % 10)]\n"
            "      else [digitChar (v / 100 % 10), digitChar (v / 10 % 10), digitChar (v % 10)]\n"
            "    return out"),
        "refinement": (
            "the faithful real counterpart reduces the year modulo one THOUSAND "
            "before the width-2 rendering: for year 476 it renders '476' (three "
            "characters, not '76'); for 123 it renders '123' not '23'. The F2P "
            "pins 476 -> '76' and the reported example pins 123 -> '23', so this "
            "counterpart would NOT resolve."
        ),
        "rationale": (
            "REJECT from C1's WIDTH obligation: year=476 gives v=476 >= 100, so "
            "the result is three characters `['4','7','6']`, whose length is 3, "
            "not the two chars `twoDigitString (476 % 100)` = `['7','6']` pins. "
            "Refuted at year=476 (a three-digit point distinct from every other "
            "rival). On this carrier a mod-1000 rival rendering the same two "
            "clamped slots collapses to gold; modeled at its true divergence "
            "(the extra hundreds char). If it verified the modulus would be "
            "unconstrained => SPEC-TOO-WEAK."
        ),
        "witness": _witness(476),
    },
    {
        "id": "weak-swap-slots",
        "kind": "uniqueness",
        "expect": "reject",
        # Transposed slots: ones char first, tens char second. Violates SLOT 0
        # and SLOT 1 whenever the two digits differ.
        "module": _impl(
            "    let n := year % 100\n"
            "    return [digitChar (n % 10), digitChar (n / 10 % 10)]"),
        "refinement": (
            "faithful real patch that transposes the two characters (ones then "
            "tens) renders 42 -> '24', 476 -> '67', 4 -> '40'. None match the F2P "
            "expectations ('42', '76', '04'), so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from C1's SLOT obligations: slot 0 is pinned to `digitChar "
            "((year%100)/10%10)` (the tens char) and slot 1 to `digitChar "
            "((year%100)%10)` (the ones char); the transposition violates both "
            "whenever the two digits differ (year=42 -> `['2','4']` vs the pinned "
            "`['4','2']`). Refuted at year=42. A value-multiset proxy would MISS "
            "this — the spec pins per index. If it verified the ordering would be "
            "unconstrained => SPEC-TOO-WEAK."
        ),
        "witness": _witness(42),
    },
    {
        "id": "weak-len3-dup",
        "kind": "uniqueness",
        "expect": "reject",
        # Three characters (duplicate the ones char): a real off-by-one width
        # mistake (e.g. '%03d'). Violates the WIDTH obligation for every year.
        "module": _impl(
            "    let n := year % 100\n"
            "    return [digitChar (n / 10 % 10), digitChar (n % 10), digitChar (n % 10)]"),
        "refinement": (
            "a faithful patch emitting three characters (e.g. '%03d' % (year % "
            "100), or a duplicated final digit) renders 13 -> '013'/'133' etc.; "
            "the F2P pins exactly two characters, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from C1's WIDTH obligation: the result has length 3, not the "
            "two chars the post-image pins. Refuted at year=13 (a distinct point "
            "from the other width rivals). Distinct from weak-mod1000-width, "
            "which is correct for year < 100 whereas this over-emits for every "
            "year. If it verified the fixed width would be unconstrained => "
            "SPEC-TOO-WEAK."
        ),
        "witness": _witness(13),
    },
    {
        "id": "weak-partial-nopad",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain leading-zero drop: correct for year%100 >= 10, but for
        # the sub-ten tail it emits a single ones char (the conventional
        # non-padded abbreviation: no left-fill). This is the exact
        # seam the fix defends. Correct everywhere except the sub-ten sub-domain.
        "module": _impl(
            "    let n := year % 100\n"
            "    let out : List Char :=\n"
            "      if n < 10 then [digitChar (n % 10)]\n"
            "      else [digitChar (n / 10 % 10), digitChar (n % 10)]\n"
            "    return out"),
        "refinement": (
            "the faithful real counterpart renders the sub-hundred part with no "
            "zero-pad: correct for years whose last two digits are >= 10 (476 -> "
            "'76', 42 -> '42') but renders 4 -> '4' and 9 -> '9'. The F2P expects "
            "4 -> '04', so this counterpart would NOT resolve — precisely the "
            "leading-zero seam at issue."
        ),
        "rationale": (
            "REJECT from C1's WIDTH obligation on the sub-ten sub-domain "
            "(year%100 < 10): for year=9 the result is the single char `['9']`, "
            "length 1, not the two chars `twoDigitString (9)` = `['0','9']` pins. "
            "A rival correct on most of the domain but diverging on the "
            "leading-zero sub-domain must REJECT. Refuted at year=9 (a sub-ten "
            "point distinct from the year=4 prepatch witness: this rival returns "
            "a single char there, the prepatch returns none). If it verified the "
            "spec would miss the exact bug => SPEC-TOO-WEAK (partial-domain)."
        ),
        "witness": _witness(9),
    },
    {
        "id": "weak-tens-off-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Off-by-one on the tens slot only: the tens digit is mis-incremented,
        # the ones char correct. Wrong on SLOT 0 for every year with year%100 in
        # a range where the increment changes the rendered digit. A distinct seam
        # from the swap (a single mis-computed digit, not a transposition).
        "module": _impl(
            "    let n := year % 100\n"
            "    return [digitChar (n / 10 % 10 + 1), digitChar (n % 10)]"),
        "refinement": (
            "faithful real patch with the tens digit mis-incremented (e.g. "
            "(year // 10) % 10 + 1 in the high position): renders 25 -> '35', 42 "
            "-> '52', 476 -> '86'. The F2P expects '25'/'42'/'76', so it would "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT from C1's SLOT 0 obligation: slot 0 = `digitChar "
            "((year%100)/10%10 + 1)` != `digitChar ((year%100)/10%10)` whenever "
            "the increment changes the clamped digit (year=25 -> `['3','5']` vs "
            "the pinned `['2','5']`). Refuted at year=25. Distinct from "
            "weak-swap-slots (a single mis-incremented digit, not a "
            "transposition). If it verified a per-digit off-by-one would be "
            "admitted => SPEC-TOO-WEAK."
        ),
        "witness": _witness(25),
    },
    {
        "id": "weak-ones-dup-tens",
        "kind": "uniqueness",
        "expect": "reject",
        # SLOT 1 attacked IN ISOLATION: slot 0 is exactly the pinned tens char
        # and the WIDTH is exactly 2, so neither of those obligations can carry
        # the rejection — only the SLOT 1 pin can. The battery's other SLOT-1
        # attack (weak-swap-slots) also permutes slot 0, so a spec that pinned
        # slot 0 and only the MULTISET of characters would still reject it; this
        # rival isolates the residual.
        "module": _impl(
            "    let n := year % 100\n"
            "    return [digitChar (n / 10 % 10), digitChar (n / 10 % 10)]"),
        "refinement": (
            "faithful real patch that renders the high digit into BOTH slots "
            "(e.g. reusing the tens quotient for the low slot) renders 1970 -> "
            "'77', 476 -> '77', 42 -> '44', 4 -> '00'. The F2P pins 476 -> '76', "
            "42 -> '42', 4 -> '04', so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from C1's SLOT 1 obligation ALONE: width is 2 and slot 0 is "
            "the pinned tens char, so this rival is refuted only by the slot-1 "
            "pin `digitChar ((year%100)%10)` (year=1970 -> `['7','7']` vs the "
            "pinned `['7','0']`). Refuted at year=1970, a fresh four-digit point "
            "no other rival uses. Closes the gap left by weak-swap-slots, which "
            "disturbs BOTH slots at once and so would also be rejected by a spec "
            "that pinned only slot 0 plus the character multiset. If it verified "
            "the low slot would be unconstrained => SPEC-TOO-WEAK."
        ),
        "witness": _witness(1970),
    },
    {
        "id": "weak-trunc-sub-seam",
        "kind": "uniqueness",
        "expect": "reject",
        # The `Nat`-carrier trap, turned into an attack instead of a hazard:
        # `d - 1 + 1` is the identity on Nat for every d >= 1 but equals 1 at
        # d = 0, because truncated subtraction floors at zero. So this rival is
        # correct on 90% of the domain and wrong on EXACTLY the sub-ten tail
        # (tens digit 0) — the leading-zero regime the change defends — and it is
        # wrong there by emitting the WRONG CHARACTER at full width 2, not by
        # dropping a slot. weak-partial-nopad attacks the same sub-domain via
        # WIDTH; this one leaves width intact, so only the SLOT 0 pin can reject
        # it.
        "module": _impl(
            "    let n := year % 100\n"
            "    return [digitChar (n / 10 % 10 - 1 + 1), digitChar (n % 10)]"),
        "refinement": (
            "faithful real patch that decrements then re-increments the high "
            "digit with a clamped-at-zero integer op (a saturating/unsigned "
            "subtraction, as a C-style `unsigned` or a clamped helper would do) "
            "renders 2005 -> '15' and 4 -> '14' while leaving 476 -> '76' and 42 "
            "-> '42' correct. The F2P pins 4 -> '04', so it would "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT from C1's SLOT 0 obligation on the leading-zero sub-domain: "
            "on `Nat` the truncated `d - 1 + 1` is the identity for d >= 1 but "
            "yields 1 at d = 0, so the rival agrees with gold on 9000 of the "
            "10000 admitted years and diverges on exactly the 1000 whose tens "
            "digit is 0 (year=2005 -> `['1','5']` vs the pinned `['0','5']`). "
            "Refuted at year=2005, a fresh point. Distinct from "
            "weak-partial-nopad, which attacks that same sub-domain by dropping "
            "a slot (WIDTH); here width stays 2 and only the pinned high "
            "CHARACTER is wrong, so the truncation trap this carrier introduces "
            "is probed rather than assumed harmless. If it verified the "
            "leading-zero character would be unconstrained => SPEC-TOO-WEAK "
            "(partial-domain)."
        ),
        "witness": _witness(2005),
    },
    {
        "id": "weak-top-of-domain",
        "kind": "uniqueness",
        "expect": "reject",
        # The precondition's UPPER BOUND probed as a live edge: a rival correct
        # at 9999 of the 10000 admitted years and wrong at exactly the largest
        # one. If `require year ≤ 9999` were doing more work than the real domain
        # needs, or if the post-image degraded at the boundary, this is where a
        # single-point hole would hide — and a spec that admitted it would admit a
        # patch that is wrong on a stdlib-constructible date.
        "module": _impl(
            "    let n := year % 100\n"
            "    let out : List Char :=\n"
            "      if year = 9999 then [digitChar 0, digitChar 0]\n"
            "      else [digitChar (n / 10 % 10), digitChar (n % 10)]\n"
            "    return out"),
        "refinement": (
            "faithful real patch that special-cases the maximum representable "
            "year to '00' renders 9999 -> '00' where the modeled behaviour is "
            "'99'; every other year is unchanged. The abbreviated form of the "
            "largest constructible year is a real, reachable case, so this patch "
            "would render it wrongly."
        ),
        "rationale": (
            "REJECT from C1 at the TOP of the admitted domain: the post-image "
            "pins `twoDigitString (9999 % 100)` = `['9','9']` and the rival "
            "returns `['0','0']`. It is correct at all 9999 other admitted "
            "years, so it tests that C1 constrains the boundary point rather "
            "than only the interior — the single-point hole no width or slot "
            "rival above would sense. Refuted at year=9999, the exact upper "
            "bound of `require year ≤ 9999`. If it verified the boundary would be "
            "unconstrained => SPEC-TOO-WEAK (single-point)."
        ),
        "witness": _witness(9999),
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING.
#
# The nagini sibling has 9 SPEC cases (2 soundness positives, 1 admissibility,
# 6 uniqueness rivals; AXIOM_TESTS empty) over `abbreviated_year(year: int)`,
# whose postcondition has FOUR clauses (len==2, per-digit range, the tens pin,
# the units pin). THIS bundle folds those into the single equality C1 (`out =
# twoDigitString (year % 100)`), which pins the same three distinguishable
# obligations (width, slot 0, slot 1). Every nagini case is accounted for.
#
#   nagini case               -> here
#   -----------------------------------------------------------------------
#   pos-control-reorder       -> pos-control-slot-locals        PORTED (reshaped)
#   pos-control-append        -> pos-control-direct-model       RE-EXPRESSED
#   admiss-year4              -> admiss-precond-usable          RE-AIMED
#   weak-prepatch-slice (R1)  -> weak-prepatch-slice           PORTED
#   weak-mod1000 (R2)         -> weak-mod1000-width            RE-EXPRESSED
#   weak-swap-digits (R3)     -> weak-swap-slots               PORTED
#   weak-len3 (R4)            -> weak-len3-dup                 PORTED
#   weak-partial-nopad (R5)   -> weak-partial-nopad            PORTED
#   weak-tens-off-by-one (R6) -> weak-tens-off-by-one          PORTED
#   AXIOM_TESTS ([])          -> (none)                        N/A (empty)
#   (no nagini counterpart)   -> weak-ones-dup-tens            ADDED (audit)
#   (no nagini counterpart)   -> weak-trunc-sub-seam           ADDED (audit)
#   (no nagini counterpart)   -> weak-top-of-domain            ADDED (audit)
#
# 12 velvet SPEC cases: 2 soundness, 1 admissibility, 9 uniqueness — parity with
# nagini on the modeled surface (a single pure renderer) plus three rivals with
# no nagini counterpart, aimed at seams this CARRIER introduces or leaves
# unprobed. The four nagini postcondition clauses collapse into one List-Char
# equality that pins the same obligations (List[int] -> List Char).
#
# ADDED (3) — seams the ported set left unattacked, each with a machine-checked
#   witness at a point no other case uses:
#   * weak-ones-dup-tens (year=1970) isolates SLOT 1. The ported SLOT-1 attack
#     (weak-swap-slots) permutes BOTH slots, so it is also rejected by a spec
#     pinning only slot 0 plus the character multiset; this rival keeps width 2
#     and slot 0 correct, so only the slot-1 pin can reject it.
#   * weak-trunc-sub-seam (year=2005) probes the `Nat` TRUNCATED-SUBTRACTION trap
#     this carrier introduces and nagini's `int` does not: `d - 1 + 1` is the
#     identity for d >= 1 but yields 1 at d = 0, making the rival wrong on
#     exactly the 1000 leading-zero years and correct on the other 9000 — a
#     partial-domain SLOT 0 divergence at full width, where weak-partial-nopad
#     attacks the same sub-domain via WIDTH.
#   * weak-top-of-domain (year=9999) probes the BOUNDARY of `require year ≤
#     9999`: wrong at exactly one of the 10000 admitted years. No width or slot
#     rival senses a single-point hole at the edge of the precondition.
#
# PORTED (5): R1/R3/R4/R5/R6 carry across on the same argument — only the carrier
#   changes. R1 (weak-prepatch-slice) is the deep pre-patch skeleton (== the
#   frozen Solution_prepatch impl), refuted at year=4 on WIDTH. R3
#   (weak-swap-slots) transposes the two slots, refuted at year=42 on the SLOT
#   pins. R4 (weak-len3-dup) emits three characters, refuted at year=13 on WIDTH.
#   R5 (weak-partial-nopad) drops the leading zero on the sub-ten sub-domain,
#   refuted at year=9 on WIDTH. R6 (weak-tens-off-by-one) mis-increments the tens
#   slot, refuted at year=25 on SLOT 0. Each carries its nagini refinement
#   argument (the faithful real patch fails the same F2P assertion), now backed
#   by a machine-checked witness.
# RE-EXPRESSED (weak-mod1000 R2 -> weak-mod1000-width): the nagini R2 lays down
#   RAW code points `48 + v//10` (unclamped), reaching 95 for year 476 (out of
#   the digit range). On this carrier `digitChar` clamps by `% 10` and
#   `twoDigitString` reads exactly the last two decimal digits, so a mod-1000
#   rival rendering the SAME two clamped slots is DEFINITIONALLY EQUAL to gold
#   (the abstraction collapses the raw-code-point distinction). The rival is
#   therefore re-expressed at its TRUE divergence — the faithful Python patch
#   mod-1000 counterpart renders three characters for year 476 — a WIDTH
#   violation refuted at year=476. This is a genuine divergence with a checked
#   witness, not a fabricated one.
# RE-EXPRESSED (pos-control-append -> pos-control-direct-model): the nagini
#   append positive assembled the two code points into a fresh list by
#   .append(). On this carrier the honest cheapest correct impl is `return
#   twoDigitString (year % 100)` — the grounded model returned directly (C1 IS
#   that equality). Same argument (a correct impl with a different executable
#   shape must verify; the grounded pin is not echo-vulnerable), expressed
#   loop-free.
# PORTED-RESHAPED (pos-control-reorder -> pos-control-slot-locals): the nagini
#   reorder positive computes units first, tens second, into a typed local bound
#   before return. Carried over as computing the ones char and tens char into
#   reverse-order typed locals, then assembling the pair — same value flow,
#   different construction order.
# RE-AIMED (admiss-year4 -> admiss-precond-usable): the nagini admiss self-called
#   abbreviated_year(4) and asserted the post over the F2P witness, so BOTH the
#   usability of `Requires` and the discharge of the post at that point were
#   under test. This carrier has no fractional-permission precondition and no
#   self-call idiom, but both halves are still expressible INSIDE the elided
#   regions, and the case is aimed at them: the impl's in-domain arm is guarded
#   by `year ≤ 9999` itself, so the residual `else` arm is closable only from
#   `require_1` (measured: the frozen `simp [twoDigitString]` alone leaves
#   `unsolved goals` on this variant, so the precondition is load-bearing), and
#   two `decide`d `have`s pin the post-image at the F2P-shaped sub-ten point
#   (4 -> "04") and at the top of the domain (9999 -> "99"). NOT the frozen file
#   verbatim: a variant identical to the artifact consumes the precondition
#   nowhere, so it would verify however unusable `require` was and would only
#   re-run the artifact's own build (G-VERIFY's job), attesting nothing about
#   admissibility.
# FRAME-MUTATION: VACUOUS. Referentially-transparent backend, no `mut` binder, no
#   heap, no aliasing, no permission system; `year` is an immutable scalar. The
#   nagini sibling itself records this class as N/A. No substitute fabricated.
# CONTROL-FLOW EFFECT: N/A. Pure value computation, no raise/side-effect
#   distinction (the nagini sibling reaches the same conclusion).
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line ``let`` over immutable values, no loop and no
#   recursion), so there is no control flow here to make diverge: a diverging
#   rival cannot be obtained by mutating this body, it has to bring a loop of
#   its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
#   two lines have to move together and they do here. Under the total scope a
#   postcondition is claimed of ALL runs and not only of terminating ones, so a
#   spliced loop owes a descent obligation ``measure b' < measure b``.
#   Re-measured on this bundle with a real build: a
#   ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
#   REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
#   < spin``). Dropping the clause rather than faking it is refused even
#   earlier, by the elaborator's own check (``Decreasing annotations are
#   required in total correctness semantics``). So divergence neither applies
#   to this impl nor discharges the ``ensures`` clauses vacuously if a rival
#   introduces it.
# AXIOM_TESTS: the nagini file's AXIOM_TESTS is empty (no @ContractOnly axiom;
#   the @Pure helpers are part of the verified spec). This bundle likewise
#   declares no axiom (the renderer is modeled deeply); the gate ignores
#   AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE. The sole clause C1 pins three obligations,
#   each attacked, and each attacked at least once IN ISOLATION so no rejection
#   rests on a co-violated obligation:
#     WIDTH  — weak-prepatch-slice (year=4, empty), weak-mod1000-width (year=476,
#              three chars), weak-len3-dup (year=13, three chars),
#              weak-partial-nopad (year=9, one char).
#     SLOT 0 — weak-tens-off-by-one (year=25, full width, slot 1 correct) and
#              weak-trunc-sub-seam (year=2005, wrong only on the leading-zero
#              sub-domain); jointly by weak-swap-slots (year=42).
#     SLOT 1 — weak-ones-dup-tens (year=1970, width 2 and slot 0 correct, so the
#              slot-1 pin alone carries the rejection); jointly by
#              weak-swap-slots (year=42).
#     BOUNDARY — weak-top-of-domain (year=9999), wrong at exactly the largest
#              admitted year, so C1 is shown to constrain the edge of `require
#              year ≤ 9999` and not only the interior.
#   The sole input binder `year` is varied across NINE distinct points (4, 476,
#   42, 13, 9, 25, 1970, 2005, 9999) spanning the sub-ten, teens, tens,
#   three-digit, four-digit and domain-boundary regimes, so pts=9 and no binder
#   is held fixed by every witness. The variation is MEANINGFUL, not two
#   spellings of one point: each witness year is a value at which its own rival
#   diverges from the frozen renderer and at which every other rival's witness
#   would not refute it. Both positives and the admissibility case defend C1 over
#   the whole domain.
AXIOM_TESTS = []
