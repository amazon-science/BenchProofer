"""properties.py — G-PBT falsification battery for django__django-11099 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is
changed — both of which the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct validateName`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is judged
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must elaborate against the rival and
FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over a candidate's code-point
sequence, parametric in the per-code-point class membership). The single
obligation is

    validateName (isAllowed : Char → Bool) (s : List Char) return (out : Bool)
      ensures out = validName isAllowed s

``validName isAllowed s`` is a total, fully-unfolded pure function: a sequence
names a valid identifier exactly when it is NON-EMPTY and every one of its code
points — from the first through the very LAST — lies in the allowed class
``isAllowed``. There is NO end-of-input tolerance: no code point is dropped or
exempted before the check, so a sequence whose final code point falls outside
the class (canonically a trailing line terminator, which no faithful class
admits) is rejected. The single load-bearing ``ensures`` clause pins the result
to ``validName isAllowed s`` and thereby to the WHOLE sequence.

``isAllowed : Char → Bool`` is a FREE input the spec quantifies over: the
``ensures`` holds for EVERY value of it, so the spec makes no claim about which
single code points are in the class. It is the abstraction of the two
validators' shared per-code-point class under each one's flags; because the
result is pinned for every ``isAllowed``, a rival that mishandled the anchoring
is refuted uniformly across all instantiations of the class.

ADVERSARIAL READ of the classes:
  * SOUNDNESS / positive controls — APPLY. A structurally different but
    behaviourally identical impl (the accumulating loop collapsed to the closed
    form the post-image names; the per-code-point conjunction commuted) must
    still verify, else the spec is SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — the method carries no ``require`` clause, so the precondition
    is trivially satisfiable and the "a normal input satisfies the precondition"
    probe is not where the risk sits. The residual risk on this surface is that
    the post-image is UNSATISFIABLE / DEGENERATE at the interesting point — that
    it does not actually demand acceptance of an all-in-class non-empty sequence
    while rejecting one whose last code point is out of class, and rejecting the
    empty sequence. ``admiss-grounded`` discharges an in-region assert pinning
    all three of those at concrete inputs; the impl is kept verbatim so the
    method's own obligation still discharges.
  * FRAME-MUTATION — VACUOUS on this backend. The sibling class exists because a
    read-only heap input may carry a fractional permission an impl overwrites.
    Lean and Velvet are referentially transparent: ``isAllowed`` and ``s`` are
    immutable values (neither declared ``mut``), there is no heap and no
    aliasing, so there is no read-only input to mutate and no substitute probe
    to build. Not fabricated — reported as an omission in the footer.
  * UNIQUENESS / SPEC-TOO-WEAK rivals — the heart of this port. Wrong impls that
    diverge from the desired behaviour on some sub-domain and MUST be rejected:
    the trailing-line-terminator tolerance (the literal pre-patch bug — the
    single discriminating delta of the gold patch), the last-code-point exemption
    (the end anchor generalised), and the inverted decision. Each is a loop-free
    closed form (so its tester kernel-reduces) with a machine-checked refutation
    witness.

WITNESS MECHANICS (specific to this carrier). The spec is a ``method``
CONTRACT, not a bare predicate, so a witness reaches it through Velvet's own
tester machinery: ``validateNameTester isAllowed s = false`` says the extracted
program's result violates the postcondition at that concrete input, checked in a
file whose ``prove_correct`` block has been stripped (no tactic script can mask
the verdict). The frozen program contains a ``while`` loop, whose fixpoint does
not reduce under the kernel's ``decide``; every reject rival is reshaped into a
LOOP-FREE closed form, so ITS tester ``decide``s while the SAME witness applied
to the loop-bearing frozen solution cannot reduce and so fails to elaborate. The
free class parameter ``isAllowed`` is instantiated at a concrete decidable
lambda in each witness, so the tester reduces to a ground boolean. The
discrimination is thus structural, not a tactic-tuning artifact. (Verified out
of band: each witness builds green against its rival and red against the frozen
solution.)

WITNESS PLACEMENT. The three rejects probe three DISTINCT input points, so both
input binders are genuinely varied rather than pinned: ``s`` ranges over a
sequence ending in the line terminator, one ending in an ordinary out-of-class
code point, and a single-code-point sequence; and ``isAllowed`` ranges over
three distinct class functions (an alphabetic class, a singleton class, the
all-true class). A rival that mishandled only a fixed class or a fixed input
shape would still be caught.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom``; the unchanged
per-code-point class is the free input ``isAllowed``, an A-reference the R/I
legs differential-test (G-CONF / G-AX's job), not a consumed contract. The gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11099"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside the impl region (between -- impl-start and
# -- impl-end) or inside the prove_correct tactic body, and each is unique in
# Solution.lean; both facts are asserted at load time by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct statement byte-
# identical (the spec view elides both regions).
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method: the backward accumulating loop over
# the code points. Reject rivals replace this with a loop-free closed form (so
# their tester reduces under `decide`); the loop-free positive control does too.
_IMPL = """    -- impl-start
    let mut acc : Bool := true
    let mut i := s.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ s.length
      invariant acc = allowedAll isAllowed (s.drop i)
      done_with i = 0
      decreasing i
    do
      let c := s[i - 1]!
      acc := isAllowed c && acc
      i := i - 1
    return !s.isEmpty && acc
    -- impl-end"""

# The three per-iteration loop lines; a positive control may reshape them while
# keeping the loop and the invariant, so the frozen proof still closes.
_LOOP_BODY = """      let c := s[i - 1]!
      acc := isAllowed c && acc
      i := i - 1"""

# The first executable line of the impl region; an in-region assert prepended
# here is discharged by the proof without disturbing the method's obligation.
_IMPL_TOP = "    let mut acc : Bool := true"

# The FULL frozen proof body (everything after the `prove_correct ... by`
# header). A positive control that collapses the loop to the closed form the
# post-image names retunes this; the tactic body is elided from the spec view,
# so this is a proof reshape, not a spec change.
_PROOF = """prove_correct validateName by
  loom_solve
  · rw [allowedAll_drop_step isAllowed s i (by omega) (by omega)]
    simp_all [Bool.and_comm]
  · simp_all [validName, List.drop_zero]"""


def _swap2(a_old, a_new, t_old, t_new):
    """Reshape the impl region AND retune the tactic body."""
    return _swap(_swap(_BASE, a_old, a_new), t_old, t_new)


# ---- witness preamble. Reach the method contract through Velvet's tester
# ---- machinery: `validateNameTester isAllowed s = false` says the extracted
# ---- program's result violates the postcondition at that concrete input.
def _tester(body):
    return ("extract_program_for validateName\n"
            "prove_precondition_decidable_for validateName\n"
            "prove_postcondition_decidable_for validateName\n"
            "derive_tester_for validateName\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the `ensures out = validName isAllowed
    # s` obligation and only reshapes the executable surface.
    # =====================================================================
    {
        "id": "pos-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Collapse the accumulating loop into the closed form the post-image
        # names directly. A completely different control-flow shape (no loop, no
        # accumulator) computing the same decision; the loop-specific proof is
        # retuned since the impl now matches the post-image syntactically.
        "module": _swap2(
            _IMPL,
            "    -- impl-start\n"
            "    return !s.isEmpty && allowedAll isAllowed s\n"
            "    -- impl-end",
            _PROOF,
            "prove_correct validateName by\n"
            "  loom_solve\n"
            "  simp_all [validName]"),
        "rationale": "a loop-free impl that returns the acceptance decision "
                     "directly must satisfy `out = validName isAllowed s`; a "
                     "correct reshape of the modeled behaviour verifying is exactly "
                     "what SPEC-TOO-STRONG would deny. Exercises the obligation from "
                     "a maximally different (loop-free) control-flow shape.",
    },
    {
        "id": "pos-commuted-and",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: commute the per-code-point conjunction in the loop body
        # (`acc := acc && isAllowed c` instead of `isAllowed c && acc`). Same
        # value flow; the loop and the front-recursive invariant are unchanged,
        # so the frozen proof (which already appeals to `Bool.and_comm`) still
        # closes untouched.
        "module": _swap(
            _BASE, _LOOP_BODY,
            "      let c := s[i - 1]!\n"
            "      acc := acc && isAllowed c\n"
            "      i := i - 1"),
        "rationale": "commuting the conjunction computes the same accumulator "
                     "value-for-value with the loop and invariant unchanged, so "
                     "`out = validName isAllowed s` still holds and the frozen "
                     "proof closes; a correct reshape must verify (else "
                     "SPEC-TOO-STRONG on the conjunction order). (Sibling: "
                     "pos-control-ascii-conjunctive.)",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries no `require` clause, so the "a normal
    # input satisfies the precondition" probe is not where the risk sits. The
    # residual risk on this surface is that the post-image is UNSATISFIABLE /
    # DEGENERATE at the interesting point (a spec no impl can meet reads like a
    # spec every impl meets). This case discharges an in-region assert at
    # concrete inputs, establishing that the post-image really does ACCEPT a
    # non-empty all-in-class sequence, REJECT a sequence whose last code point is
    # out of class (the discriminating trailing-terminator shape), and REJECT the
    # empty sequence. The surrounding impl is kept verbatim so the method's own
    # obligation still discharges; the assert is live (a false claim about the
    # same points leaves an unsolved goal), and the proof's alternation gains one
    # `decide` arm to close the ground assert.
    # =====================================================================
    {
        "id": "admiss-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap2(
            _IMPL_TOP,
            "    assert (with_name_prefix `assert\n"
            "      (validName (fun c => c == 'a') ['a'] = true ∧\n"
            "       validName (fun c => c == 'a') ['a', '\\n'] = false ∧\n"
            "       validName (fun c => c == 'a') [] = false))\n"
            "    let mut acc : Bool := true",
            _PROOF,
            "prove_correct validateName by\n"
            "  loom_solve <;>\n"
            "    first\n"
            "    | decide\n"
            "    | (rw [allowedAll_drop_step isAllowed s i (by omega) (by omega)];\n"
            "       simp_all [Bool.and_comm])\n"
            "    | simp_all [validName, List.drop_zero]"),
        "rationale": "the post-image is satisfiable AND non-degenerate at the "
                     "F2P-shaped points: it demands ACCEPT for a non-empty "
                     "all-in-class sequence, REJECT for one whose LAST code point "
                     "is out of class (the trailing-terminator shape the fix "
                     "targets), and REJECT for the empty sequence. The in-region "
                     "assert must discharge (else the obligation is unsatisfiable / "
                     "PRECOND-TOO-STRONG); the impl is kept verbatim so "
                     "`out = validName isAllowed s` still verifies. (Sibling: "
                     "admiss-ascii-read-input, re-aimed.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form (so its tester
    # kernel-reduces) with a machine-checked refutation witness at a concrete
    # input, and the refinement argument that its faithful real counterpart would
    # NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-trailing-terminator-tolerated",
        "kind": "uniqueness",
        "expect": "reject",
        # THE discriminating delta. Tolerate exactly one trailing line
        # terminator before the all-in-class check: if the sequence ends in the
        # terminator, check only the prefix. This is precisely the pre-patch
        # end-of-input tolerance the gold change removes. Correct on every
        # sequence that does not end in the terminator; diverges on the
        # trailing-terminator sub-domain, where the post-image demands the last
        # code point ALSO be in class (no faithful class admits the terminator).
        "module": _swap(
            _BASE, _IMPL,
            "    -- impl-start\n"
            "    let t : List Char := if s.getLast? = some '\\n' then s.dropLast else s\n"
            "    return !s.isEmpty && allowedAll isAllowed t\n"
            "    -- impl-end"),
        "refinement": "this is the literal pre-image behaviour: a single trailing "
                      "line terminator is tolerated before the in-class run. Its "
                      "faithful real counterpart is the UNCHANGED buggy end anchor, "
                      "which still accepts a candidate ending in that terminator — "
                      "exactly the failing case the issue adds — so it would NOT "
                      "resolve. (Sibling: partial-domain-ascii-trailing-lf-tolerated; "
                      "the Unicode mirror is subsumed — see footer.)",
        "rationale": "REJECT from `out = validName isAllowed s`: at a sequence whose "
                     "last code point is the line terminator over an else-in-class "
                     "prefix, `validName` folds the class over EVERY code point "
                     "including the last, so it demands reject while the rival drops "
                     "the terminator and accepts. Refuted on the trailing-terminator "
                     "sub-domain (`s.getLast? = some '\\n'`, prefix all in class), "
                     "the load-bearing behavior of the fix.",
        "witness": _tester(
            "example : validateNameTester (fun c => c.isAlpha) ['a', '\\n'] "
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-exempt-last-code-point",
        "kind": "uniqueness",
        "expect": "reject",
        # Exempt the LAST code point from the class check unconditionally (check
        # only the prefix). The end anchor generalised: correct on every sequence
        # whose only out-of-class code point is not the last, but accepts a
        # sequence whose final code point is out of class regardless of what it
        # is. Diverges on the last-code-point sub-domain.
        "module": _swap(
            _BASE, _IMPL,
            "    -- impl-start\n"
            "    return !s.isEmpty && allowedAll isAllowed s.dropLast\n"
            "    -- impl-end"),
        "refinement": "a counterpart that exempts one anchored code point (the last) "
                      "from the class check is the end-of-input tolerance "
                      "generalised: it admits a candidate with one un-checked "
                      "trailing position, so it accepts inputs the fixed end anchor "
                      "rejects (it no longer requires EVERY code point in class) and "
                      "would NOT resolve. (Sibling: partial-domain-ascii-skip-last.)",
        "rationale": "REJECT from `out = validName isAllowed s`: `validName` pins the "
                     "LAST code point inside the in-class run, so skipping it breaks "
                     "the equality on any sequence whose final code point is out of "
                     "class. Refuted at a sequence whose last code point is an "
                     "ordinary out-of-class code point (NOT the line terminator), so "
                     "this attacks the general last-anchor requirement, a strictly "
                     "different sub-domain from the trailing-terminator rival.",
        "witness": _tester(
            "example : validateNameTester (fun c => c == 'a') ['a', 'z'] "
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-inverted-decision",
        "kind": "uniqueness",
        "expect": "reject",
        # Supporting near-miss: return the NEGATION of the acceptance decision.
        # Accepts exactly the invalid candidates and rejects the valid ones — the
        # inverse of the validator. Confirms the post-image pins the polarity of
        # the result.
        "module": _swap(
            _BASE, _IMPL,
            "    -- impl-start\n"
            "    return !(!s.isEmpty && allowedAll isAllowed s)\n"
            "    -- impl-end"),
        "refinement": "returning the inverse decision accepts every invalid "
                      "candidate (including one with an out-of-class code point) and "
                      "rejects every valid one, the opposite of the validator — it "
                      "resolves nothing. (Sibling: support-ascii-inverted-decision.)",
        "rationale": "REJECT from `out = validName isAllowed s`: the negated decision "
                     "contradicts the pinned value on every input the spec accepts "
                     "(and every one it rejects). Verifying would be SPEC-TOO-WEAK on "
                     "the polarity of the result. Refuted at a single in-class code "
                     "point under the all-true class (a distinct input point and a "
                     "distinct class function from the other two rivals).",
        "witness": _tester(
            "example : validateNameTester (fun c => true) ['a'] "
            "= false := by\n  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 7 SPEC cases (1
# soundness positive, 1 admissibility, 1 frame-mutation rival, 4
# uniqueness/partial-domain rivals) plus 4 AXIOM_TESTS entries. The sibling
# contracts TWO functions, `accepts_ascii` and `accepts_unicode`, each over a
# `List[int]` carrying a fractional heap permission, with the per-code-point
# class an axiomatized membership oracle. This bundle contracts ONE method,
# `validateName`, over a `List Char`, PARAMETRIC in the per-code-point class
# `isAllowed : Char → Bool` — so the ASCII and Unicode validators collapse to a
# single obligation (they differ only in the instantiation of the free class,
# which the spec quantifies over) and the membership oracle becomes a free input
# rather than an axiom. The value surface carries across intact; the permission
# surface and the two-function split do not exist here.
#
#   sibling case                              kind          -> here                              disposition
#   -----------------------------------------------------------------------------------------------------------
#   pos-control-ascii-conjunctive             soundness     -> pos-commuted-and                  PORTED
#   (—)                                       soundness     -> pos-closed-form                   ADDED
#   admiss-ascii-read-input                   admissibility -> admiss-grounded                   RE-AIMED
#   frame-mutation-ascii-overwrite            uniqueness    -> (none)                            VACUOUS
#   partial-domain-ascii-trailing-lf-tolerated uniqueness   -> weak-trailing-terminator-tolerated PORTED
#   partial-domain-ascii-skip-last            uniqueness    -> weak-exempt-last-code-point       PORTED
#   partial-domain-unicode-trailing-lf-tolerated uniqueness -> weak-trailing-terminator-tolerated SUBSUMED
#   support-ascii-inverted-decision           uniqueness    -> weak-inverted-decision            PORTED
#   ax-sound-permitted-ascii                  axiom         -> (none)                            G-AX
#   ax-sound-permitted-unicode                axiom         -> (none)                            G-AX
#   ax-ref-deep-model-fixed                   axiom         -> (none)                            G-AX
#   ax-cover-membership-domain                axiom         -> (none)                            G-AX
#
# PORTED (pos-control-ascii-conjunctive -> pos-commuted-and): the sibling reshapes
#   the per-step branch into a conjunction; here the conjunction already exists in
#   the loop body, so the closest reshape is to COMMUTE it (`acc && isAllowed c`),
#   which keeps the loop and the front-recursive invariant so the frozen proof
#   closes unchanged. pos-closed-form is ADDED to defend the obligation from a
#   maximally different (loop-free) shape.
# RE-AIMED (admiss-ascii-read-input -> admiss-grounded): the sibling establishes
#   that the half-permission read-only grant is held and the length is readable —
#   a permission fact with no analogue on a referentially-transparent carrier with
#   no `require` clause. Re-aimed to the sharper residual risk here: a degenerate
#   post-image. The case discharges a live in-region assert pinning ACCEPT (non-
#   empty all-in-class), REJECT (last code point out of class), and REJECT (empty)
#   at concrete inputs.
# VACUOUS (frame-mutation-ascii-overwrite): the sibling's mandatory frame-mutation
#   rival overwrites the half-permission read-only input to force it all-permitted,
#   rejected for INSUFFICIENT PERMISSION. This backend is referentially transparent
#   and both parameters are read-only immutable values (no `mut`), so there is no
#   read-only input to overwrite and no permission system to trip. Omitted as
#   vacuous, NOT fabricated (per the porting map, this class is legitimately
#   dropped rather than replaced).
# PORTED (the two partial-domain ASCII rivals): trailing-lf-tolerated ports directly
#   to weak-trailing-terminator-tolerated (the literal pre-patch bug, refuted on the
#   trailing-terminator sub-domain — the single discriminating delta of the fix);
#   skip-last ports to weak-exempt-last-code-point (the last-anchor exemption
#   generalised, refuted on a last-code-point-out-of-class input that is NOT the
#   terminator).
# SUBSUMED (partial-domain-unicode-trailing-lf-tolerated): on the sibling this is a
#   SEPARATE rival because the ASCII and Unicode validators are two distinct
#   functions and a rival could fix one while leaving the other's end anchor buggy.
#   Here the two validators collapse to the SINGLE parametric method `validateName`,
#   which quantifies over `isAllowed`, so a trailing-terminator rival is refuted for
#   EVERY class instantiation at once — there is no separate Unicode surface to
#   attack. weak-trailing-terminator-tolerated already covers both. Its witness uses
#   the alphabetic class `Char.isAlpha`, which admits neither ASCII nor Unicode-only
#   distinctions of the terminator, so it is faithful to both validators.
# PORTED (support-ascii-inverted-decision -> weak-inverted-decision): the polarity
#   attack ports directly.
# AXIOM_TESTS (4): dropped. The axiom lane is G-AX's job. Here the per-code-point
#   class is not an axiomatized oracle but the FREE input `isAllowed` (an
#   A-reference the R/I legs differential-test), so there is no consumed contract to
#   probe in this lane, and the gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The obligation has two input binders,
#   `isAllowed : Char → Bool` and `s : List Char`, and one top-level clause,
#   `out = validName isAllowed s`, which internally conjoins non-emptiness with the
#   all-in-class fold over EVERY code point. The three reject witnesses probe three
#   DISTINCT input points (pts=3): a trailing-terminator sequence under the
#   alphabetic class, an ordinary out-of-class-last sequence under a singleton
#   class, and a single in-class code point under the all-true class. Thus `s`
#   ranges over ['a','\n'] / ['a','z'] / ['a'] and `isAllowed` over
#   Char.isAlpha / (· == 'a') / (fun _ => true) — neither binder held fixed. The
#   last-code-point requirement is attacked from two independent sub-domains (the
#   terminator specifically and an ordinary out-of-class code point), the non-empty
#   / all-in-class polarity is attacked by the inversion, and the admissibility case
#   pins the empty-sequence and accept branches — so no rival that mishandled only a
#   fixed class or a fixed input shape could slip through.
AXIOM_TESTS = []
