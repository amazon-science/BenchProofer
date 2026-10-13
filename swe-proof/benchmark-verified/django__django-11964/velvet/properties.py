"""properties.py — G-PBT falsification battery for django__django-11964 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is
changed — both of which the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct memberToStr`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is judged
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates — the witness must ELABORATE against the rival and
FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method over the modeled payload of an
enumerated member). The member's payload is either a numeric value
(``MemberValue.intVal n``) or a textual value (``MemberValue.strVal s``); the
method renders the member as text:

    memberToStr (member : Member) return (out : List Char)
      (P1) ensures out = renderValue member.value
      (P2) ensures ∀ n : Int, member.value = MemberValue.intVal n
                     → out = (toString n).toList
      (P3) ensures ∀ s : List Char, member.value = MemberValue.strVal s
                     → out = s

``renderValue`` is a fully unfolded ``def`` in the ``pure`` region: a numeric
payload becomes its decimal text form, a textual payload is exactly its own code
points. There is NO opaque answer key to echo — the load-bearing oracle is a
total function of the member's OWN input field, so a faithful element-for-element
render IS the correct impl and any DIFFERENT returned content (the member's
generic default token, a truncation, the empty text) fails the postcondition.
The three ``ensures`` clauses carry two independent per-constructor behaviours
over the sole input binder ``member.value``: the decimal render on the numeric
arm (P2) and the identity render on the textual arm (P3), both also pinned by
the top-level P1. Both arms are exercised, and the reject witnesses vary
``member.value`` across BOTH constructors so neither arm is left pinned.

GROUNDED-ORACLE NOTE (why there is no wrong echo to build). The post-image is
grounded in the member's own payload, not an ungrounded oracle, so the reject
lane targets returning content that DIVERGES from that payload on a
discriminating sub-domain: the member's generic default token (the pre-fix
rendering — the qualified ``Owner.NAME`` object token the problem statement
shows), a truncation, the empty text, and a token substituted on ONLY the
textual arm. Each is exactly a behaviour the desired render replaces.

CARRIER NOTE (decisive for the witness route). Every carrier here is
TRANSPARENT: ``MemberValue`` has ``DecidableEq`` and ``renderValue`` is a
concrete ``def``, so a rival's violation reduces to a decidable equality of
concrete values. HOWEVER, the two quantified clauses (P2 over ``Int``, P3 over
``List Char``) make ``prove_postcondition_decidable_for`` fail — the tester
route (``derive_tester_for`` → ``…Tester args = false``) is UNAVAILABLE here
(measured: the two ``∀`` clauses leave unsolved ``Decidable`` goals). So each
witness instead refutes the method's Hoare triple DIRECTLY at a concrete member:
``¬ triple True (memberToStr m) (fun out => P1 ∧ P2 ∧ P3)`` closed by
``unfold; simp [triple, pure] <;> decide``. Every witness was SEEN to
discriminate — it ELABORATES against the rival (EXIT 0) and FAILS against the
frozen solution (EXIT 1) — with two real builds per case. The witness heads bind
nothing (they state the refutation at literal inputs), so there is no
consistency obligation to satisfy.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling carries this as
    MANDATORY because its input holds a fractional heap permission
    (``Acc(self.value_text, 1/2)``) an impl can illegally WRITE (normalize the
    read-only input to satisfy the postcondition vacuously). Lean and Velvet are
    referentially transparent: ``member`` is an immutable value, this bundle
    declares no ``mut`` binder, there is no heap and no aliasing — so there is no
    read-only input to overwrite and no substitute probe to build. Not
    fabricated (per the porting map: this class is vacuous on Lean/Velvet).
  * SOUNDNESS / positive controls — APPLY. A structurally different but faithful
    render must still verify, else SPEC-TOO-STRONG.
  * ADMISSIBILITY — the nagini self-call establishes the precondition ADMITS a
    normal F2P-shaped member. This bundle carries NO ``require`` clause (the
    render is total), so the precondition-admission probe is degenerate; the
    case is RE-AIMED at the residual admissibility risk on a transparent carrier
    — that the post-image is DEGENERATE (does not actually demand the decimal /
    identity render on each arm, distinct from the generic default token). An
    in-region assert pins BOTH arms at F2P-shaped points; the impl is kept
    verbatim so the method's own obligation still discharges.
  * PARTIAL-DOMAIN / VALUE rivals — APPLY: the pre-fix default token, a
    truncation, the empty text, and a token substituted on only the textual arm.

AXIOM lane: EMPTY. The ``axioms`` region declares no ``axiom`` (the render is
modeled DEEPLY as ``renderValue``); the nagini file's single A-reference
(the ``str(value)`` coercion) is G-AX's job, and this gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-11964"
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

# The WHOLE executable body of the method: render the payload and return it.
_IMPL = (
    "    let result : List Char := renderValue member.value\n"
    "    return result"
)
assert _BASE.count(_IMPL) == 1, "impl region drifted from expected text"

# The first executable line of the impl region; an in-region assert prepended
# here is discharged by the (retuned) proof without disturbing the obligation.
_IMPL_TOP = "    let result : List Char := renderValue member.value"
assert _BASE.count(_IMPL_TOP) == 1, "impl top-line drifted from expected text"

# The FULL frozen proof body. A case that adds an in-region assert retunes this
# to also close the ground assert goal; the tactic body is elided from the spec
# view, so this is a proof reshape, not a spec change.
_PROOF = "prove_correct memberToStr by\n  loom_solve"
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, new_impl)


# ---- WITNESSES. The spec is a `method` CONTRACT with two quantified `ensures`
# ---- clauses, so `prove_postcondition_decidable_for` fails and the tester
# ---- route is unavailable (measured). Each witness instead refutes the
# ---- method's Hoare triple DIRECTLY at one concrete member, checked in a file
# ---- whose `prove_correct` block has been stripped so no tactic script can
# ---- mask the verdict. `triple`/`pure` come from the frozen `Velvet.Std`
# ---- import; the head binds nothing (literal input), so there is no
# ---- consistency obligation.
def _witness(member_lit: str, value_lit: str) -> str:
    return (
        f"example : ¬ triple (l := Prop) (True)\n"
        f"    (memberToStr {member_lit})\n"
        f"    (fun out => out = renderValue ({value_lit})\n"
        f"      ∧ (∀ n : Int, ({value_lit}) = MemberValue.intVal n → out = (toString n).toList)\n"
        f"      ∧ (∀ s : List Char, ({value_lit}) = MemberValue.strVal s → out = s)) := by\n"
        f"  unfold memberToStr\n"
        f"  simp [triple, pure] <;> decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the three `ensures` obligations and
    # only reshapes the executable surface.
    # =====================================================================
    {
        "id": "pos-bind-local",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the payload to a typed local before rendering it. Same
        # value flow; the frozen `loom_solve` still closes the (byte-identical)
        # obligation. Ports the nagini pos-control-reshape ARGUMENT (read the
        # datum into a temp, then produce it) onto this carrier.
        "module": _with_impl(
            "    let v : MemberValue := member.value\n"
            "    let result : List Char := renderValue v\n"
            "    return result"),
        "rationale": "PASS SOURCE = P1/P2/P3. Binding the payload to a typed local "
                     "before rendering leaves the returned value identical, so "
                     "`out = renderValue member.value` and both per-constructor "
                     "clauses still discharge; a structurally-different faithful "
                     "reshape MUST verify, else the postcondition is over-fit to the "
                     "exact impl FORM => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-match",
        "kind": "soundness",
        "expect": "verify",
        # A second honest correct shape: split the render into an explicit match
        # on the payload constructor, spelling out each arm exactly as the
        # post-image names it. A maximally different control-flow shape (no call
        # to renderValue at all) computing the same result — confirms the spec is
        # not over-fit to delegating to the pure helper. Ports the nagini
        # pos-control-copy ARGUMENT (a distinct honest render is the correct impl;
        # there is no wrong echo to build).
        "module": _with_impl(
            "    let result : List Char :=\n"
            "      match member.value with\n"
            "      | MemberValue.intVal n => (toString n).toList\n"
            "      | MemberValue.strVal s => s\n"
            "    return result"),
        "rationale": "PASS SOURCE = P1/P2/P3. Rendering via an explicit match on the "
                     "payload constructor (decimal text on the numeric arm, identity "
                     "on the textual arm) reproduces `renderValue member.value` on "
                     "both constructors without calling the helper, so all three "
                     "clauses discharge. The load-bearing oracle is grounded in the "
                     "input, so a faithful element-for-element render IS the correct "
                     "impl; a second honest shape verifying confirms the spec is not "
                     "echo-vulnerable and not over-fit. Else SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED. The nagini sibling self-calls on a freshly
    # constructed member to show the (fractional-permission) precondition
    # ADMITS a normal input. This bundle carries NO `require` clause (the render
    # is total), so that probe is degenerate. Re-aimed at the residual
    # admissibility risk on a transparent carrier: that the post-image is
    # DEGENERATE — that it does not actually demand the decimal render on the
    # numeric arm and the identity render on the textual arm, each distinct from
    # the member's generic default token. An in-region assert pins BOTH arms at
    # F2P-shaped points AND that the numeric render differs from a default token;
    # the impl is kept verbatim so the method's own obligation still discharges;
    # the proof gains a `decide` arm to close the ground assert. The assert is
    # LIVE — a false claim (e.g. the numeric render = "6") leaves an unsolved
    # `decide` goal (verified out of band).
    # =====================================================================
    {
        "id": "admiss-grounded",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _swap(
                _BASE, _IMPL_TOP,
                "    assert (with_name_prefix `admiss\n"
                "      (renderValue (MemberValue.intVal 5) = \"5\".toList\n"
                "       ∧ renderValue (MemberValue.strVal \"first\".toList) = \"first\".toList\n"
                "       ∧ renderValue (MemberValue.intVal 5) ≠ \"C.M\".toList))\n"
                + _IMPL_TOP),
            _PROOF,
            "prove_correct memberToStr by\n  loom_solve <;> decide"),
        "rationale": "PASS SOURCE = the post-image is non-degenerate at F2P-shaped "
                     "points. The in-region assert pins the numeric arm to its "
                     "decimal text ('5'), the textual arm to its own code points "
                     "('first'), AND the numeric render to something OTHER than a "
                     "generic default token ('C.M') — so the spec genuinely demands "
                     "the value's text, not the default object token. The assert must "
                     "discharge (else the obligation is degenerate / unsatisfiable) "
                     "and the frozen body keeps `out = renderValue member.value` "
                     "intact, so the module verifies. Since the render is total, "
                     "there is no precondition to over-strengthen; this defends "
                     "against a hollow/degenerate post-image instead.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete member (both constructors exercised), and the refinement argument
    # that its faithful real counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-default-token",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-fix behaviour: return the member's generic default token
        # instead of its value text. This is the qualified `Owner.NAME` object
        # token the problem statement shows ('MyChoice.FIRST_CHOICE'), carried
        # here as `member.defaultLabel`.
        "module": _with_impl(
            "    let result : List Char := member.defaultLabel\n"
            "    return result"),
        "refinement": "returning the member's generic default token is EXACTLY the "
                      "pre-fix behaviour the problem statement reports: a member cast "
                      "to text renders the qualified object token "
                      "('MyChoice.FIRST_CHOICE') instead of its underlying value "
                      "('first'). A faithful real patch that left the render at that "
                      "token still shows the object token for every member whose "
                      "token differs from its value, so it FAILS the failing test "
                      "(which asserts the cast-to-text equals the value text) — it is "
                      "the unfixed bug, the definition of verify-not-resolve.",
        "rationale": "REJECT from P1 (`out = renderValue member.value`): the impl "
                     "returns the default token, which differs from the value's text "
                     "on every member whose token differs from its value. Refuted at "
                     "a numeric member (intVal 5): its render is '5', the token 'C.M'; "
                     "P2 (`out = toString 5`) is also violated there. If it verified "
                     "=> SPEC-TOO-WEAK (the value-vs-token discriminator — the whole "
                     "point of the fix — would be hollow).",
        "witness": _witness(
            '{ value := MemberValue.intVal 5, defaultLabel := "C.M".toList }',
            "MemberValue.intVal 5"),
    },
    {
        "id": "weak-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # Cheapest wrong render: return the empty text regardless of the payload.
        # Correct only on an empty textual payload; wrong on every non-empty
        # value. Refuted on the TEXTUAL arm (a distinct constructor from the
        # numeric arms the other rivals probe).
        "module": _with_impl(
            "    let result : List Char := []\n"
            "    return result"),
        "refinement": "a real render that returned the empty text for every member "
                      "shows '' instead of 'first' / '1', so the cast-to-text differs "
                      "from the value text for every non-empty value and it FAILS the "
                      "failing test — verify-not-resolve (this is the cheapest wrong "
                      "render).",
        "rationale": "REJECT from P1 and P3: the impl returns the empty text, so at a "
                     "textual member with a non-empty payload the post-image demands "
                     "the payload's own code points while the impl returns []. "
                     "Refuted at a textual member (strVal 'first') — exercising the "
                     "strVal arm (P3), a distinct constructor from the numeric rivals. "
                     "If it verified => SPEC-TOO-WEAK.",
        "witness": _witness(
            '{ value := MemberValue.strVal "first".toList, defaultLabel := "C.M".toList }',
            'MemberValue.strVal "first".toList'),
    },
    {
        "id": "weak-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        # Truncating render: drop the LAST code point of the value's text.
        # Correct only on empty/one-char values; diverges on every longer value.
        # Attacks whether the post-image pins the EXACT rendered text, not merely
        # that a related text is produced. Refuted on the NUMERIC arm.
        "module": _with_impl(
            "    let result : List Char := (renderValue member.value).dropLast\n"
            "    return result"),
        "refinement": "a real render that dropped the last character would show "
                      "'firs' for the value 'first' and '4' for the value '42'. It "
                      "diverges from the value text on every value longer than one "
                      "character, so the cast-to-text differs from the value text and "
                      "it FAILS the failing test — verify-not-resolve on the entire "
                      "multi-character sub-domain.",
        "rationale": "REJECT from P1 and P2: the impl returns the value's text with "
                     "its last code point dropped, so at a numeric member whose "
                     "decimal text has length >= 2 the post-image demands the full "
                     "decimal text while the impl returns a proper prefix. Refuted at "
                     "a numeric member (intVal 42 -> render '42', impl '4'), pinning "
                     "the EXACT rendered text. If it verified => SPEC-TOO-WEAK (the "
                     "spec would accept a truncating render).",
        "witness": _witness(
            '{ value := MemberValue.intVal 42, defaultLabel := "C.M".toList }',
            "MemberValue.intVal 42"),
    },
    {
        "id": "weak-text-arm-token",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain over the CONSTRUCTOR split: render the numeric arm
        # correctly but substitute the generic default token on the TEXTUAL arm.
        # Correct on every numeric member; wrong on every textual member whose
        # token differs from its value. This clause exists because the carrier
        # distinguishes intVal / strVal — it demonstrates the post-image pins the
        # two arms INDEPENDENTLY (P3 is not subsumed by P2), a distinction the
        # nagini single-`value_text`-list carrier cannot express.
        "module": _with_impl(
            "    let result : List Char :=\n"
            "      match member.value with\n"
            "      | MemberValue.intVal n => (toString n).toList\n"
            "      | MemberValue.strVal _ => member.defaultLabel\n"
            "    return result"),
        "refinement": "a real render that handled numeric values but fell back to the "
                      "generic default token for TEXTUAL values still shows "
                      "'MyChoice.FIRST_CHOICE' instead of 'first' for a TextChoices "
                      "member, so the cast-to-text differs from the value text on the "
                      "textual sub-domain and it FAILS the failing test (which covers "
                      "both integer and text choices) — verify-not-resolve on the "
                      "textual sub-domain.",
        "rationale": "REJECT from P1 and P3: on a textual member the post-image "
                     "demands the payload's own code points while the impl returns the "
                     "default token; they differ whenever the token differs from the "
                     "value. Refuted at a textual member (strVal 'sec', token 'C.M') — "
                     "the strVal arm this rival mishandles while agreeing with gold on "
                     "every numeric member (there it renders correctly). If it "
                     "verified => SPEC-TOO-WEAK (P3 would be subsumed by P2 and the "
                     "textual arm left undefended).",
        "witness": _witness(
            '{ value := MemberValue.strVal "sec".toList, defaultLabel := "C.M".toList }',
            'MemberValue.strVal "sec".toList'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 7 SPEC cases (2
# soundness positives, 1 admissibility, 4 uniqueness rivals — one of which is
# the mandatory frame-mutation probe) plus 1 AXIOM_TESTS entry. The sibling
# contracts one method, `render_to_text`, over a member held at a fractional
# heap permission with a `ToSeq(Result()) == ToSeq(self.value_text)`
# discriminator; this bundle contracts one method, `memberToStr`, over the
# member's modeled payload with a deep `renderValue` and no axioms. The two
# surfaces model the SAME behaviour (render a member as its own value's text),
# so the port is near-1:1 with two carrier consequences: the frame-mutation
# rival is vacuous here, and the intVal/strVal constructor split ADDS a
# per-constructor clause the single-list sibling cannot express.
#
#   sibling case                 kind          -> here                   disposition
#   ---------------------------------------------------------------------------
#   pos-control-reshape          soundness     -> pos-bind-local         PORTED
#   pos-control-copy             soundness     -> pos-match              PORTED
#   admiss-selfcall              admissibility -> admiss-grounded        RE-AIMED
#   frame-mutate-value-text      uniqueness    -> (none)                 VACUOUS
#   weak-qualified-label         uniqueness    -> weak-default-token     PORTED
#   weak-drop-last               uniqueness    -> weak-drop-last         PORTED
#   weak-empty                   uniqueness    -> weak-empty             PORTED
#   (—)                          uniqueness    -> weak-text-arm-token    ADDED
#   ax-ref-render-equals-str-value axiom       -> (none)                 G-AX
#
# 5 ported, 1 re-aimed, 1 added, 1 vacuous = 7 velvet cases (3 verify, 4 reject).
#
# PORTED (pos-control-reshape -> pos-bind-local): the sibling reads the code
#   point into a temp before appending; here the payload is bound to a typed
#   local before rendering. Same argument (a faithful reshape must verify),
#   verified to build.
# PORTED (pos-control-copy -> pos-match): the sibling's second honest correct
#   shape (typed-local copy) becomes an explicit match spelling out each arm,
#   confirming the grounded oracle is not echo-vulnerable. Verified to build.
# RE-AIMED (admiss-selfcall -> admiss-grounded): the sibling self-calls to show
#   the fractional-permission precondition admits a normal member. This bundle
#   has NO `require` clause (the render is total), so that probe is degenerate.
#   Re-aimed at the residual risk on a transparent carrier — a DEGENERATE
#   post-image — via a live in-region assert pinning BOTH arms and that the
#   numeric render differs from a default token. Verified to build; the assert
#   is live (a false claim leaves an unsolved `decide` goal, verified out of band).
# VACUOUS (frame-mutate-value-text): the sibling carries this as MANDATORY
#   because `self.value_text` is held at Acc(...,1/2) an impl can illegally
#   write. This backend is referentially transparent and this bundle declares no
#   `mut` binder, so `member` is an immutable value with no heap footprint —
#   there is no read-only input to overwrite and no substitute probe to build.
#   Not fabricated (per the porting map: this class is vacuous on Lean/Velvet).
# PORTED (the three value rivals): weak-qualified-label ports to
#   weak-default-token (return the generic default token — the pre-fix
#   `Owner.NAME` object rendering — refuted on a numeric member where token !=
#   value). weak-drop-last ports directly (truncate the render — refuted on a
#   numeric member whose decimal text has length >= 2, pinning the exact text).
#   weak-empty ports directly (return the empty text — refuted on a textual
#   member with a non-empty payload). Each carries a machine-checked witness
#   that ELABORATES against the rival and FAILS against the frozen solution
#   (verified with two real builds per case).
# ADDED (weak-text-arm-token): the intVal/strVal constructor split gives the
#   post-image two independent per-constructor clauses (P2 over the numeric arm,
#   P3 over the textual arm) that the sibling's single `value_text` list has no
#   analogue for. This rival renders the numeric arm correctly but substitutes
#   the default token on the textual arm, so it is refutable ONLY on a textual
#   member — closing P3 as an independent clause and demonstrating it is not
#   subsumed by P2.
# AXIOM_TESTS (1): dropped. The axiom lane is G-AX's job (axiom_check.py); this
#   bundle declares no axiom (the render is modeled deeply as `renderValue`, an
#   A-reference), and this gate ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The obligation has one input binder,
#   `member`, whose observed content is `member.value : MemberValue`
#   (`intVal n` | `strVal s`); `member.defaultLabel` is not observed by the spec
#   (it is deliberately ignored by the render — a wrong impl that returns it is
#   caught by weak-default-token / weak-text-arm-token). The four reject
#   witnesses probe four DISTINCT input points (pts=4): intVal 5, strVal 'first',
#   intVal 42, strVal 'sec' — so `member.value` ranges over BOTH constructors and
#   several literals, none held fixed. Clause coverage: P1 (`out = renderValue
#   member.value`) is attacked by all four rivals; P2 (numeric arm) is attacked
#   by weak-default-token and weak-drop-last (both at numeric members where the
#   impl's output differs from the decimal text); P3 (textual arm) is attacked by
#   weak-empty and weak-text-arm-token (both at textual members where the impl's
#   output differs from the payload's own code points). No rival is refuted at
#   the same point as another, and the two per-constructor clauses are each
#   attacked independently.
AXIOM_TESTS = []
