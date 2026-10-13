"""properties.py — G-PBT falsification battery for django__django-13670 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_twoDigitYear`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the two-digit abbreviated-year rendering over an ``int``-scalar input and
a ``List[int]`` code-point output, pinning the answer to a GROUNDED closed-form
of the input (nagini's ``tens_digit``/``units_digit``, fully unfolded — there is
no opaque oracle). This Lean bundle models the SAME single purely-functional
core over a ``Nat`` input and a ``List Char`` output, with the SAME grounding:
the postcondition equates ``result`` to ``twoDigitYear year`` — a deep model
(reduce modulo one hundred, then emit the tens digit then the units digit as two
ASCII decimal characters). Every nagini case carries over either as a faithful
correct positive or as an attack on the single top-level postcondition clause;
the nagini frame/permission-mutation class is VACUOUS here (referential
transparency — see ``assessment``), as it already was on nagini's int-scalar
carrier.

DEFENDED SURFACE (one modeled behavior; one top-level clause).
``problem_spec_twoDigitYear year result`` pins EXACTLY:

  * (C0)  ``result = twoDigitYear year`` — the result is definitionally the
    two ASCII decimal digits of ``year % 100``, tens then units, with a leading
    zero when the reduced value is below ten.

Because the modeled surface is a single equation against a fully-computable deep
model, the nagini spec's several sub-clauses (``len(Result())==2``, the
digit-range pins ``48<=Result()[k]<=57``, the per-index ``Result()[0]==
tens_digit``/``Result()[1]==units_digit`` pins) are not independent top-level
conjuncts here — they are all consequences of the single equality ``result =
twoDigitYear year``. So a rival that violates ANY of them (wrong length, wrong
modulus, transposed digits, off-by-one digit, no leading-zero pad) violates the
one clause and is refutable by evaluation. Each nagini rival is therefore ported
as an attack on C0 at the concrete input where it diverges from the frozen model.

The BEHAVIOURAL DISCRIMINATOR (the fix): for years whose last two digits are
below ten, the output must be zero-padded to exactly two characters (year 4 ->
``['0','4']``), where the pre-fix behavior (slice the decimal rendering from the
third character) produced fewer than two characters. The ``weak-prepatch-slice``
and ``weak-partial-nopad`` rivals below attack exactly this seam.

BINDER STRUCTURE. The spec predicate has ONE input binder: ``year`` (a ``Nat``).
It is load-bearing and is VARIED across the reject witnesses: the seven rivals
are refuted at seven DISTINCT years — 42, 476, 91, 9, 4, 99, 100 — spanning the
sub-ten leading-zero regime (4, 9), ordinary two-digit years (42, 91, 99), a year
whose modulus-100 value differs from its modulus-1000 value (476), and a year
whose reduced value is 0 (100). So the single binder is exercised across every
regime the fix distinguishes (``pts=7``).

The variation is MEANINGFUL, not seven spellings of one point: each year was
checked to be a year at which the OTHER rivals are NOT refutable. Concretely,
``weak-mod1000`` and ``weak-partial-nopad`` both AGREE with the frozen model at
year 42 (``42 % 1000 = 42``; ``42 % 100 >= 10``), and ``weak-swap-digits`` agrees
at year 100 (the reduced value 0 is a palindrome), so each witness's year is
carrying its own case rather than restating a neighbour's.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling notes its input is
    an ``int`` scalar carrying no heap permission (no read-only list parameter),
    so its frame-mutation class is already vacuous THERE; on this referentially
    transparent carrier it is doubly so — ``year`` is an immutable ``Nat``, there
    is no ``mut`` input binder, no aliasing, no read-only cell to overwrite. No
    substitute probe is fabricated (porting map: vacuous here).

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    equals ``twoDigitYear year``, a closed-form arithmetic function of the input.
    There is no opaque answer key an implementation could echo — producing the
    two digits IS doing the work. In its place the battery carries honest
    cheapest-implementation POSITIVE CONTROLS that must verify (porting the
    nagini ``pos-control-*`` positives).

  * DEFINITIONAL-COLLAPSE OF A POSITIVE — APPLIES, and it is the reason this
    battery carries five positives rather than two. On this carrier a reshape of
    the impl can be DEFINITIONALLY the frozen body (zeta reduction, ``Id.run``
    reduction, ``++`` on literals), in which case the frozen ``rfl`` closes it
    unchanged and the positive tests only that the shape still compiles — it
    cannot witness SPEC-TOO-STRONG, because no spec that admits gold could
    reject a term gold is definitionally equal to. The nagini sibling had no such
    trap: Viper re-discharges the postcondition per rival, so ANY reshape there
    is a genuine re-proof. So the two ported positives are kept (as shape
    regression controls, with their scope stated) and three EXTENSIONAL positives
    are added, each provably not closable by ``rfl``.

  * CONTROL-FLOW EFFECT — VACUOUS. The nagini sibling notes the function is pure
    value computation with no raise/return/side-effect distinction the value
    abstraction misses; the Lean model is a total ``def`` with no such
    distinction either. No substitute probe.

  * DIVERGENCE / NON-TERMINATION — VACUOUS on lean. ``implementation_twoDigitYear``
    is a total Lean ``def``; a diverging implementation cannot be written at all,
    so there is no rival to port. (The nagini sibling carries no divergence case
    either.)

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where the fix bites: the pre-fix decimal slice, the no-leading-zero
    variant, plus wrong-modulus, transposed-digit, three-character, and
    off-by-one-digit rivals (both digit positions).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof is tuned to the frozen form — so
a rejection alone attributes nothing to the spec. Every ``expect="reject"`` case
therefore carries a Lean snippet that states the spec predicate at one concrete
``year`` and closes ``¬ problem_spec_twoDigitYear year (implementation ... year)``
by ``decide`` (the deep model and the rival are both fully computable, so
``decide`` reduces ``Char.ofNat`` and the modular arithmetic to a literal
inequality). Each witness binds NOTHING in its head (the year is a ground
literal), so there are no hypotheses whose consistency could be in question. Each
was checked with two real ``lake env lean`` builds to HOLD of its rival and to
FAIL on the frozen solution, so it discriminates rather than asserting a
tautology.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart is a
rendering that mis-computes the two-digit short form, so on the F2P inputs
(``476 -> '76'``, ``42 -> '42'``, ``4 -> '04'``) the rendered string mismatches
the expected value — so the faithful patch would NOT resolve.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the changed operation is modeled deeply); the axiom lane belongs to
G-AX, and the nagini ``AXIOM_TESTS`` (also empty there) are dropped.
"""
from pathlib import Path

INSTANCE = "django__django-13670"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The frozen impl body (the four lines between `-- impl-start`/`-- impl-end`,
# after the `def` header). Every impl reshape replaces exactly this block, so the
# spec view and the `correct_twoDigitYear` STATEMENT are untouched.
_IMPL_BODY = (
    "  let r := year % 100\n"
    "  let tens := r / 10\n"
    "  let ones := r % 10\n"
    "  return [digitChar tens, digitChar ones]")

# The frozen proof's `intro` line (proof region) — unique in the file — so the
# admissibility positive can prepend a ground `have` without touching the
# theorem STATEMENT or the spec view.
_P_INTRO = "  intro year"

# The FROZEN proof body verbatim (the whole tactic block after the `:= by`).
# A positive control whose impl is only DEFINITIONALLY the frozen one can reuse
# this untouched; a positive whose impl is merely EXTENSIONALLY equal cannot, and
# must re-prove inside the proof region (which `variant_scope` permits — only the
# theorem STATEMENT is frozen, the tactic body may differ).
_PROOF_BODY = (
    "  intro year\n"
    "  unfold problem_spec_twoDigitYear implementation_twoDigitYear twoDigitYear\n"
    "  rfl")

# The goal the frozen `unfold` leaves, written out so an extensional reshape can
# `show` its own reduced form and then rewrite the arithmetic. Stating it is what
# lets `rw`/`split` see past the `Id.run do` `have`-bindings, which otherwise
# block both tactics (measured: `rw` reports "did not find an occurrence" and
# `split` reports "could not split an `if`" against the un-reduced `Id.run` term).
_GOAL_RHS = "[digitChar (year % 100 / 10), digitChar (year % 100 % 10)]"


def _reproof(tactics):
    """A variant that re-proves the SAME obligation with its own tactic body.

    Only the text inside `-- proof-start`/`-- proof-end` after the theorem's
    `:= by` changes, so the `correct_twoDigitYear` STATEMENT stays byte-identical
    and `variant_scope` still admits the case (no new theorem, no new axiom, no
    assumption token).
    """
    return lambda src: _swap(src, _PROOF_BODY, tactics)


# ---------------------------------------------------------------------------
# witness scaffold. States the spec predicate at one concrete year and closes
# the negation by `decide` (the deep model and the rival are both computable).
# ---------------------------------------------------------------------------
def _w(year):
    return (
        f"example : ¬ problem_spec_twoDigitYear {year} "
        f"(implementation_twoDigitYear {year}) := by\n"
        "  unfold problem_spec_twoDigitYear implementation_twoDigitYear "
        "twoDigitYear\n"
        "  decide\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — CORRECT impls that MUST verify, else
    # SPEC-TOO-STRONG. Each keeps the `theorem correct_twoDigitYear` statement
    # byte-identical.
    #
    # THEY COME IN TWO STRENGTHS, and the distinction is the whole point of the
    # lane. The first two (`reorder`, `append`) are only DEFINITIONALLY the
    # frozen body: they reduce to the frozen impl by zeta/`Id.run` reduction, so
    # the frozen `rfl` closes them UNCHANGED. That makes them cheap regression
    # controls for the executable SHAPE — but it also caps what they can detect.
    # A spec that had been over-tightened to the frozen syntactic form would
    # still admit them, because `rfl` cannot tell them apart from gold. Measured
    # directly: both bodies close `= implementation_twoDigitYear year` by a bare
    # `rfl`, so neither can ever witness SPEC-TOO-STRONG.
    #
    # So the lane also carries EXTENSIONAL positives (`no-mod100`,
    # `units-via-sub`, `pad-literal-zero`) whose impls are equal to gold only as
    # FUNCTIONS, never definitionally: `rfl` provably fails on each, and closing
    # them needs real arithmetic (`omega`) about `%`/`/`. Those are the ones that
    # actually test whether the spec pins the two-digit VALUE rather than the
    # frozen impl's syntax. They re-prove inside the proof region, which
    # `variant_scope` permits (only the STATEMENT is frozen); no helper lemma, no
    # new declaration, no assumption token. All five verified with real builds.
    # =====================================================================
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Compute the units digit binding BEFORE the tens digit binding (reversed
        # `let` order), then assemble in the SAME tens-then-units order. Same
        # values, different local-binding order — definitionally the frozen body,
        # so the frozen `rfl` proof still closes.
        "module": _swap(
            _BASE, _IMPL_BODY,
            "  let r := year % 100\n"
            "  let ones := r % 10\n"
            "  let tens := r / 10\n"
            "  return [digitChar tens, digitChar ones]"),
        "rationale": "structurally-different CORRECT impl (the units-digit local "
                     "is computed first, the tens-digit local second, then the two "
                     "code points are assembled in the same tens-then-units order). "
                     "C0 still holds on every input. SCOPE OF THIS CONTROL: the "
                     "reshape is only the local-binding ORDER, which zeta-reduces "
                     "away, so this impl is DEFINITIONALLY the frozen body and the "
                     "frozen `rfl` closes it unchanged. It is therefore a "
                     "regression control on the executable shape, and NOT evidence "
                     "against SPEC-TOO-STRONG — a spec over-tightened to the frozen "
                     "syntactic form would admit it too. The extensional positives "
                     "(pos-control-no-mod100, pos-control-units-via-sub, "
                     "pos-control-pad-literal-zero) carry that burden. Ports "
                     "nagini's pos-control-reorder (there: units computed first, "
                     "tens second, into a typed local bound before return; on the "
                     "SMT carrier the reorder is a genuine re-discharge, here it is "
                     "definitional — the carrier collapses the distinction).",
    },
    {
        "id": "pos-control-append",
        "kind": "soundness",
        "expect": "verify",
        # CORRECT impl assembled by appending tens then units to a fresh mutable
        # list (different executable shape from the literal list constructor; still
        # no loop). Definitionally the frozen body, so the frozen `rfl` closes.
        "module": _swap(
            _BASE, _IMPL_BODY,
            "  let r := year % 100\n"
            "  let mut out : List Char := []\n"
            "  out := out ++ [digitChar (r / 10)]\n"
            "  out := out ++ [digitChar (r % 10)]\n"
            "  return out"),
        "rationale": "CORRECT impl assembled by appending the tens char then the "
                     "units char to a fresh mutable list (different executable "
                     "shape from the literal list constructor; still no loop). "
                     "C0 holds. SCOPE OF THIS CONTROL: `++` on two-element list "
                     "literals and the `mut` accumulator both reduce, so this impl "
                     "is DEFINITIONALLY the frozen body and the frozen `rfl` closes "
                     "it unchanged — a regression control on the executable shape, "
                     "NOT evidence against SPEC-TOO-STRONG (see "
                     "pos-control-reorder). Ports nagini's pos-control-append "
                     "(append to a fresh typed list).",
    },

    # ---- EXTENSIONAL positive: never forms `year % 100` at all ----
    {
        "id": "pos-control-no-mod100",
        "kind": "soundness",
        "expect": "verify",
        # Takes the tens digit as (year / 10) % 10 and the units digit as
        # year % 10 — the reduction modulo one hundred is never formed. Equal to
        # the frozen result as a FUNCTION, but NOT definitionally: `rfl` fails,
        # and closing it needs `omega` to relate the two digit extractions.
        "module": _reproof(
            "  intro year\n"
            "  unfold problem_spec_twoDigitYear implementation_twoDigitYear "
            "twoDigitYear\n"
            "  show [digitChar (year / 10 % 10), digitChar (year % 10)] = "
            + _GOAL_RHS + "\n"
            "  have ht : year / 10 % 10 = year % 100 / 10 := by omega\n"
            "  have hu : year % 10 = year % 100 % 10 := by omega\n"
            "  rw [ht, hu]")(_swap(
                _BASE, _IMPL_BODY,
                "  return [digitChar (year / 10 % 10), digitChar (year % 10)]")),
        "rationale": "CORRECT impl that never forms the modulo-one-hundred "
                     "reduction: the tens digit is taken as `year / 10 % 10` and "
                     "the units digit as `year % 10`. This is the STRONG form of "
                     "the soundness control, because it is equal to the frozen "
                     "result only EXTENSIONALLY — `rfl` provably does NOT close it "
                     "(the two digit extractions are not definitionally equal), so "
                     "the case re-proves with `omega`-justified rewrites of the "
                     "arithmetic. It therefore tests what the definitional "
                     "positives cannot: that C0 pins the two-digit VALUE rather "
                     "than the frozen impl's syntactic form. If the spec rejected "
                     "it, the spec would be SPEC-TOO-STRONG (it would demand a "
                     "particular way of extracting the digits, not the right "
                     "answer). Statement byte-identical; only the tactic body "
                     "differs, which variant_scope permits. Strengthens nagini's "
                     "pos-control lane, which on the SMT carrier got this for free "
                     "(Viper re-discharges linear //,% arithmetic per rival) while "
                     "here it must be earned.",
    },

    # ---- EXTENSIONAL positive: units digit by subtraction, not `%` ----
    {
        "id": "pos-control-units-via-sub",
        "kind": "soundness",
        "expect": "verify",
        # Units digit as r - 10 * (r / 10) instead of r % 10. Extensionally the
        # frozen result; `rfl` fails (Nat subtraction is not definitionally the
        # remainder), so the case re-proves via `omega`.
        "module": _reproof(
            "  intro year\n"
            "  unfold problem_spec_twoDigitYear implementation_twoDigitYear "
            "twoDigitYear\n"
            "  show [digitChar (year % 100 / 10), "
            "digitChar (year % 100 - 10 * (year % 100 / 10))] = "
            + _GOAL_RHS + "\n"
            "  have h : year % 100 - 10 * (year % 100 / 10) = year % 100 % 10 := "
            "by omega\n"
            "  rw [h]")(_swap(
                _BASE, _IMPL_BODY,
                "  let r := year % 100\n"
                "  let tens := r / 10\n"
                "  return [digitChar tens, digitChar (r - 10 * tens)]")),
        "rationale": "CORRECT impl that recovers the units digit by SUBTRACTION "
                     "(`r - 10 * (r / 10)`) rather than by the remainder operator. "
                     "Extensionally the frozen result, but not definitionally — "
                     "`rfl` fails — so this is a second STRONG soundness control, "
                     "re-proved by an `omega` rewrite. It probes the same clause C0 "
                     "from the units side, where pos-control-no-mod100 probes it "
                     "from the tens side. If the spec rejected it, C0 would be "
                     "pinning the operator rather than the digit value => "
                     "SPEC-TOO-STRONG.",
    },

    # ---- EXTENSIONAL positive: the CORRECT sibling of weak-partial-nopad ----
    {
        "id": "pos-control-pad-literal-zero",
        "kind": "soundness",
        "expect": "verify",
        # Same case split as weak-partial-nopad, but the sub-ten branch emits a
        # LITERAL '0' pad followed by the digit — i.e. it pads correctly. This is
        # the near-miss control for the leading-zero seam: it must VERIFY where
        # weak-partial-nopad must REJECT, which is what shows the spec bites on
        # the pad itself and not merely on the presence of a case split.
        "module": _reproof(
            "  intro year\n"
            "  unfold problem_spec_twoDigitYear implementation_twoDigitYear "
            "twoDigitYear\n"
            "  show (if year % 100 < 10 then "
            "['0', digitChar (year % 100)] else " + _GOAL_RHS + ") = "
            + _GOAL_RHS + "\n"
            "  split\n"
            "  · next h =>\n"
            "      have h0 : year % 100 / 10 = 0 := by omega\n"
            "      have h1 : year % 100 % 10 = year % 100 := by omega\n"
            "      rw [h0, h1]\n"
            "      rfl\n"
            "  · rfl")(_swap(
                _BASE, _IMPL_BODY,
                "  let r := year % 100\n"
                "  if r < 10 then\n"
                "    return ['0', digitChar r]\n"
                "  return [digitChar (r / 10), digitChar (r % 10)]")),
        "rationale": "the CORRECT NEAR-MISS SIBLING of weak-partial-nopad: the "
                     "identical branch structure on `year % 100 < 10`, but the "
                     "sub-ten branch emits a literal '0' followed by the digit — "
                     "i.e. it pads properly instead of dropping the pad. This "
                     "pairing is the load-bearing evidence for the seam the change "
                     "defends: the two cases differ ONLY in whether the leading "
                     "zero is supplied, and the spec must verify this one while "
                     "rejecting that one. Without this positive, "
                     "weak-partial-nopad's rejection is consistent with the spec "
                     "merely disliking a case split; with it, the rejection is "
                     "attributable to the missing pad specifically. Extensional, "
                     "not definitional (the literal '0' is not syntactically "
                     "`digitChar (r / 10)`), so `rfl` fails and the case re-proves "
                     "by `omega` on the branch hypothesis. If it were rejected, the "
                     "spec would be SPEC-TOO-STRONG on exactly the sub-domain the "
                     "change is about.",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at a
    # normal, F2P-shaped input. The frozen theorem carries no precondition
    # (`Nat` makes 1<=year<=9999 vacuous — see mapping.md), so the nagini
    # precondition-admission self-call re-expresses as: discharge the spec
    # predicate by evaluation at the F2P sub-ten leading-zero witness (year 4 ->
    # ['0','4']) as a ground `have`, then close the frozen obligation verbatim.
    # Nothing is assumed: no new declaration, statement byte-identical, ground
    # instance is a `have` prepended to the existing tactic body. (Verified: real
    # build.)
    # =====================================================================
    {
        "id": "admiss-year4",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            "  have _ground : problem_spec_twoDigitYear 4 "
            "(implementation_twoDigitYear 4) := by\n"
            "    unfold problem_spec_twoDigitYear implementation_twoDigitYear "
            "twoDigitYear\n"
            "    decide\n"
            + _P_INTRO),
        "rationale": "the obligation is discharged at the F2P sub-ten leading-zero "
                     "witness (year 4, which renders the two-char padded form "
                     "['0','4']) by evaluation as a `have`, then the frozen "
                     "obligation is closed verbatim. Verifies (else the modeled "
                     "behavior would be unsatisfiable at exactly a normal F2P input "
                     "— the analogue of PRECOND-TOO-STRONG). Nothing is assumed: no "
                     "new declaration, statement byte-identical, ground instance is "
                     "a `have` in the existing tactic body. Ports nagini's "
                     "admiss-year4.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a witness pinning the
    # violation at one concrete year.
    # =====================================================================

    # ---- the pre-fix behavior: slice the decimal rendering from char 3 ----
    {
        "id": "weak-prepatch-slice",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-fix shape: render the year's full decimal expansion and drop the
        # first two characters. For years < 100 this yields fewer than two chars.
        "module": _swap(
            _BASE, _IMPL_BODY,
            "  return (toString year).toList.drop 2"),
        "refinement": "this IS the pre-fix behavior reproduced deeply: render the "
                      "full decimal expansion and keep everything from the third "
                      "character on. As the removed line, its faithful real patch "
                      "does NOT resolve: for year 42 it yields '' and for year 4 it "
                      "yields '', whereas the F2P demands '42' and '04'.",
        "rationale": "REJECT from C0: for any year < 100 the deep slice yields "
                     "fewer than two characters, so `result = twoDigitYear year` "
                     "cannot hold. Refuted at year 42, where the slice is [] but "
                     "the frozen model is ['4','2']. If it verified, the spec would "
                     "not sense the fixed-width change => SPEC-TOO-WEAK.",
        "witness": _w(42),
    },

    # ---- wrong modulus: reduce modulo 1000 instead of 100 ----
    {
        "id": "weak-mod1000",
        "kind": "uniqueness",
        "expect": "reject",
        # Reduce modulo 1000, then emit two digits. For a three-digit year the
        # tens position becomes a non-digit code point and disagrees with the model.
        "module": _swap(
            _BASE, _IMPL_BODY,
            "  let r := year % 1000\n"
            "  return [digitChar (r / 10), digitChar (r % 10)]"),
        "refinement": "faithful real patch reducing modulo one thousand instead of "
                      "one hundred: for year 476 it renders a three-digit-derived "
                      "form, not '76', and for year 123 it renders '12x' not '23'. "
                      "The F2P demands 476 -> '76', so this patch does NOT resolve.",
        "rationale": "REJECT from C0: for year 476, `year % 1000 = 476` so the "
                     "tens position is `digitChar (476/10)` (a non-decimal-digit "
                     "code point) and the whole list differs from "
                     "`twoDigitYear 476 = ['7','6']`. Refuted at year 476. If it "
                     "verified the modulus would be unconstrained => SPEC-TOO-WEAK.",
        "witness": _w(476),
    },

    # ---- transposed digits: units then tens ----
    {
        "id": "weak-swap-digits",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit the units digit first, then the tens digit.
        "module": _swap(
            _BASE, _IMPL_BODY,
            "  let r := year % 100\n"
            "  return [digitChar (r % 10), digitChar (r / 10)]"),
        "refinement": "faithful real patch that transposes the two characters "
                      "(units then tens) renders 42 -> '24', 91 -> '19', 4 -> '40'. "
                      "None match the F2P expectations ('42','04'), so it does NOT "
                      "resolve.",
        "rationale": "REJECT from C0: the model pins tens then units, but the rival "
                     "emits units then tens; these differ whenever the two digits "
                     "differ. Refuted at year 91, where the rival is ['1','9'] but "
                     "`twoDigitYear 91 = ['9','1']`. If it verified the per-index "
                     "ordering would be unconstrained => SPEC-TOO-WEAK (a "
                     "value-multiset proxy would miss this — the model pins the "
                     "exact sequence).",
        "witness": _w(91),
    },

    # ---- off-by-one on the UNITS digit only (the mirror of the tens probe) ----
    {
        "id": "weak-units-off-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Units digit computed as (year%100)%10 + 1, correct tens. ADDED BY AUDIT:
        # the shipped battery attacked the tens position (weak-tens-off-by-one) and
        # the ORDER of the two positions (weak-swap-digits), but no rival perturbed
        # the units position while leaving the tens position correct — so a spec
        # that pinned only the tens character and the length would have passed the
        # whole battery. Refuted at year 100, whose reduced value is 0: the units
        # position is where the two disagree, and the tens position agrees, so the
        # witness isolates the units clause specifically.
        "module": _swap(
            _BASE, _IMPL_BODY,
            "  let r := year % 100\n"
            "  return [digitChar (r / 10), digitChar (r % 10 + 1)]"),
        "refinement": "faithful real patch whose units digit is mis-incremented "
                      "renders 42 -> '43', 4 -> '05', 100 -> '01'. The F2P demands "
                      "42 -> '42' and 4 -> '04', so this patch does NOT resolve.",
        "rationale": "REJECT from C0: the units character is "
                     "`digitChar ((year%100)%10 + 1)`, which differs from "
                     "`digitChar ((year%100)%10)` at every input, while the tens "
                     "character is correct. Refuted at year 100, where the rival is "
                     "['0','1'] but `twoDigitYear 100 = ['0','0']` — a year whose "
                     "reduced value is 0, so the ONLY disagreement is at the units "
                     "position and the refutation cannot be explained by the tens "
                     "position or the length. This closes the gap the shipped "
                     "rivals left: they perturbed the tens digit and the digit "
                     "ORDER, but never the units digit alone, so C0's units "
                     "conjunct was defended by no rival. If it verified, a "
                     "per-digit off-by-one in the units place would be admitted => "
                     "SPEC-TOO-WEAK.",
        "witness": _w(100),
    },

    # ---- three characters instead of two ----
    {
        "id": "weak-len3",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit a third (duplicated units) character.
        "module": _swap(
            _BASE, _IMPL_BODY,
            "  let r := year % 100\n"
            "  return [digitChar (r / 10), digitChar (r % 10), "
            "digitChar (r % 10)]"),
        "refinement": "a faithful patch emitting three characters (e.g. a "
                      "'%03d'-style render, or a duplicated final digit) renders "
                      "9 -> '009'/'099' etc.; the F2P demands exactly two "
                      "characters, so it does NOT resolve.",
        "rationale": "REJECT from C0: the result has length 3, so it cannot equal "
                     "the length-2 `twoDigitYear year`. Refuted at year 9, where "
                     "the rival is ['0','9','9'] but the model is ['0','9']. If it "
                     "verified the fixed width would be unconstrained => "
                     "SPEC-TOO-WEAK.",
        "witness": _w(9),
    },

    # ---- partial-domain: no leading-zero pad for the sub-ten tail ----
    {
        "id": "weak-partial-nopad",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct for year%100 >= 10, but for the sub-ten tail emit a single
        # (non-padded) character — the exact leading-zero seam the fix defends.
        "module": _swap(
            _BASE, _IMPL_BODY,
            "  let r := year % 100\n"
            "  if r < 10 then\n"
            "    return [digitChar r]\n"
            "  return [digitChar (r / 10), digitChar (r % 10)]"),
        "refinement": "faithful real patch that renders without zero-padding "
                      "(a plain decimal render of year % 100): correct for years "
                      "whose last two digits are >= 10 (476 -> '76', 42 -> '42') but "
                      "renders 4 -> '4' and 9 -> '9'. The F2P demands 4 -> '04', so "
                      "this patch does NOT resolve — this is precisely the "
                      "leading-zero seam the gold patch fixes.",
        "rationale": "REJECT from C0: for the sub-ten sub-domain (year%100 < 10) "
                     "the result is a single character, so it cannot equal the "
                     "length-2 model. Refuted at year 4, where the rival is ['4'] "
                     "but `twoDigitYear 4 = ['0','4']`. A rival correct on most of "
                     "the domain but diverging on the leading-zero sub-domain must "
                     "REJECT; if it verified the spec would miss the exact bug => "
                     "SPEC-TOO-WEAK (partial-domain).",
        "witness": _w(4),
    },

    # ---- off-by-one on the tens digit only ----
    {
        "id": "weak-tens-off-by-one",
        "kind": "uniqueness",
        "expect": "reject",
        # Tens digit computed as (year%100)/10 + 1, correct units.
        "module": _swap(
            _BASE, _IMPL_BODY,
            "  let r := year % 100\n"
            "  return [digitChar (r / 10 + 1), digitChar (r % 10)]"),
        "refinement": "faithful real patch with the tens digit mis-incremented "
                      "renders 42 -> '52', 99 -> ':9' (a non-digit high char). The "
                      "F2P demands '42', so it does NOT resolve.",
        "rationale": "REJECT from C0: the tens character is `digitChar ((year%100)"
                     "/10 + 1)`, which differs from `digitChar ((year%100)/10)` for "
                     "every input (and for year%100 in 90..99 reaches the non-digit "
                     "code point ':'). Refuted at year 99, where the rival's tens "
                     "char is `digitChar 10` (':') but the model is ['9','9']. If it "
                     "verified a per-digit off-by-one would be admitted => "
                     "SPEC-TOO-WEAK.",
        "witness": _w(99),
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 1 admissibility, 6 uniqueness/partial-domain rivals) plus an EMPTY
# AXIOM lane. This bundle models the SAME single purely-functional core (the
# two-digit abbreviated-year rendering) and re-expresses every sibling case; no
# case is dropped. FOUR cases are ADDED by a later independent audit (see the
# AUDIT ADDITIONS note below). Every sibling case is recorded here.
#
#   sibling case               -> here
#   -----------------------------------------------------------------------
#   pos-control-reorder        -> pos-control-reorder      PORTED (definitional)
#   pos-control-append         -> pos-control-append       PORTED (definitional)
#   admiss-year4               -> admiss-year4             RE-EXPRESSED
#   weak-prepatch-slice        -> weak-prepatch-slice      PORTED
#   weak-mod1000               -> weak-mod1000             PORTED
#   weak-swap-digits           -> weak-swap-digits         PORTED
#   weak-len3                  -> weak-len3                PORTED
#   weak-partial-nopad         -> weak-partial-nopad       PORTED
#   weak-tens-off-by-one       -> weak-tens-off-by-one     PORTED
#   AXIOM_TESTS (0)            -> (none)                   DROPPED (G-AX)
#   (no sibling)               -> pos-control-no-mod100          ADDED (audit)
#   (no sibling)               -> pos-control-units-via-sub      ADDED (audit)
#   (no sibling)               -> pos-control-pad-literal-zero   ADDED (audit)
#   (no sibling)               -> weak-units-off-by-one          ADDED (audit)
#
# AUDIT ADDITIONS — why the ported set was not sufficient on THIS carrier:
#
#   (1) BOTH ported positives are DEFINITIONALLY the frozen impl. Measured: each
#       of their bodies closes `= implementation_twoDigitYear year` by a bare
#       `rfl`, because the `let` reorder zeta-reduces and the `++`/`mut`
#       accumulator reduces on two-element literals. A positive that is
#       definitionally gold cannot witness SPEC-TOO-STRONG — no spec admitting
#       gold can reject a term definitionally equal to it — so the soundness lane
#       as ported was passing honestly while testing nothing about spec strength.
#       That is a carrier-specific trap with no analogue in the sibling, where
#       Viper re-discharges the postcondition for every rival and so any reshape
#       is a real re-proof. Three EXTENSIONAL positives were added, each equal to
#       gold only as a function and each provably NOT closable by `rfl`
#       (`no-mod100`: tens via `year / 10 % 10`, never forming `% 100`;
#       `units-via-sub`: units via `r - 10 * (r / 10)`; `pad-literal-zero`: the
#       correct-pad sibling of weak-partial-nopad). Each re-proves in the proof
#       region with `omega`-justified rewrites — statement byte-identical, no new
#       declaration, no assumption token.
#
#   (2) The UNITS position was attacked by no rival. The ported set perturbed the
#       tens digit (weak-tens-off-by-one), the ORDER of the two digits
#       (weak-swap-digits) and the LENGTH (weak-len3, weak-prepatch-slice,
#       weak-partial-nopad), but nothing perturbed the units digit while leaving
#       the tens digit and the length correct. A spec pinning only the tens
#       character and the length would have passed the entire ported battery.
#       weak-units-off-by-one closes that, refuted at year 100 — whose reduced
#       value is 0, so the tens character AGREES with gold and the refutation is
#       attributable to the units clause alone.
#
#   (3) weak-partial-nopad's rejection was unpaired. On its own, that rejection is
#       equally consistent with the spec disliking the branch structure as with it
#       demanding the pad. pos-control-pad-literal-zero is the same case split with
#       the pad supplied and MUST verify, so the pair isolates the pad itself —
#       which is the behaviour the change is actually about.
#
# RE-EXPRESSED (admiss-year4): the nagini admissibility case adds a caller that
#   self-calls abbreviated_year(4) and asserts its postcondition (len 2, '0' then
#   '4') to confirm the precondition 1<=year<=9999 admits a normal in-domain year.
#   On this carrier the input is a `Nat` and the frozen theorem carries no
#   precondition (the bound is vacuous over `Nat` — see mapping.md), so there is
#   no precondition to attack. The honest analogue is to discharge the
#   POSTCONDITION at the same F2P input (year 4 -> ['0','4']) as a ground `have`,
#   proving the modeled behavior is satisfiable at exactly that input, then close
#   the frozen obligation verbatim.
#
# CLAUSE COVERAGE. The nagini spec spells out several conjuncts (len==2, the
#   digit-range pins, the per-index tens/units pins). On this carrier they are NOT
#   independent top-level clauses: they all follow from the single equality
#   `result = twoDigitYear year`. The seven rivals each violate that one clause at
#   a different sub-behavior — length (weak-len3, weak-prepatch-slice), modulus
#   (weak-mod1000), per-index order (weak-swap-digits), per-digit value in the
#   TENS place (weak-tens-off-by-one) and in the UNITS place
#   (weak-units-off-by-one), and the leading-zero pad (weak-partial-nopad) — so
#   the single top-level clause is attacked from every angle the nagini
#   sub-clauses named, with each nagini sub-clause now having at least one rival
#   that violates it AND NOTHING ELSE. Every top-level clause of the spec is
#   attacked (there is one), and >=1 verify case defends it.
#
# DEEP-MODEL FIDELITY (audit, machine-checked). `twoDigitYear` was evaluated
#   against the two-digit zero-padded rendering over the ENTIRE real input domain:
#   for all y in 0..9999 it is exactly `[digitChar (y%100/10), digitChar (y%100%10)]`,
#   has length 2, and both characters lie in '0'..'9' — all three `#eval`s
#   returned `true`. The F2P triple was confirmed pointwise (476 -> ['7','6'],
#   42 -> ['4','2'], 4 -> ['0','4']). The pre-fix rendering disagrees with the
#   model on exactly 1000 of those 10000 years (precisely the y with y%100 < 10),
#   which is the sub-domain the change is about — so the modeled clause is the one
#   the behaviour change lives in, not a restatement of the frozen impl.
#
# VACUOUS classes (no substitute fabricated): FRAME/PERMISSION MUTATION (nagini
#   itself notes the input is an int scalar with no read-only list param; on this
#   referentially transparent carrier there is no `mut` input, no aliasing);
#   UNGROUNDED-ORACLE ECHO (the postcondition is grounded in a closed-form deep
#   model, no opaque answer key to echo — replaced by the positive controls);
#   CONTROL-FLOW EFFECT (pure value computation, no raise/return distinction);
#   DIVERGENCE / NON-TERMINATION (`implementation_twoDigitYear` is a total Lean
#   `def` — a diverging impl cannot be written, so the class is genuinely vacuous
#   on lean; the nagini sibling carries no divergence case either).
#
# POINT SPREAD. The seven reject witnesses probe seven DISTINCT years (pts=7):
#     year 42   weak-prepatch-slice      C0 (length: slice -> [])
#     year 476  weak-mod1000             C0 (wrong modulus)
#     year 91   weak-swap-digits         C0 (per-index order)
#     year 9    weak-len3                C0 (length: 3 chars)
#     year 4    weak-partial-nopad       C0 (leading-zero pad)
#     year 99   weak-tens-off-by-one     C0 (tens digit value; non-digit char)
#     year 100  weak-units-off-by-one    C0 (units digit value, tens correct)
#   The single input binder `year` is exercised across the sub-ten leading-zero
#   regime (4, 9), ordinary two-digit years (42, 91, 99), a three-digit year whose
#   mod-100 and mod-1000 reductions differ (476), and a year whose reduced value
#   is 0 (100), so the binder is not pinned to one value. The years are also
#   mutually DISCRIMINATING rather than respellings: weak-mod1000 and
#   weak-partial-nopad both agree with the frozen model at year 42, and
#   weak-swap-digits agrees at year 100, so no witness's year would serve for its
#   neighbours (each checked with a real build).
#
# SPEC-TOO-WEAK PROBES that found NOTHING (audit; recorded so the next reader does
#   not repeat them). Four NEW wrong impls beyond the shipped rivals were built
#   and all four were REJECTED by the frozen spec, each also refutable by a
#   concrete-year witness: units-digit off-by-one (kept above as a case); tens
#   digit hard-wired to zero (`r / 100`); an impl correct on all of 1..9999 but
#   returning `[]` at year >= 10000 (probing whether the spec's quantification
#   over all of `Nat` is load-bearing — it is: the rival is rejected and refuted
#   at 10000); and an impl correct everywhere EXCEPT the single year 9999. The
#   last two matter because the carrier's `Nat` is wider than the real domain
#   `1..9999`: the spec constrains the whole of `Nat`, so it does not go slack
#   outside the datetime range, and it bites on wrongness as sparse as one point.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (the rendering is modeled deeply), so there is nothing to probe and the
# gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
