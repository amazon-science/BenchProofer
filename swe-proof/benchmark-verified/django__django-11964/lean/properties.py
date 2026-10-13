"""properties.py — G-PBT falsification battery for django__django-11964 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for a case that legitimately re-proves or adds a
ground instance, inside the ``-- proof-start`` / ``-- proof-end`` region — is
changed, so ``markers.same_spec`` holds and the ``theorem correct_memberStr``
STATEMENT stays byte-identical). ``expect:"verify"`` passes iff (in scope AND the
file elaborates with the obligation closed, no ``sorry``/``admit``/
``native_decide`` and no new ``axiom``/``theorem``); ``expect:"reject"`` passes
iff (in scope AND it does NOT verify AND the case's refutation ``witness`` holds
of the rival while FAILING on the frozen solution).

DEFENDED SURFACE (one total function over a single input binder):

  memberStr (m : EnumMember) (result : String) : Prop
    result = pyStr m.value          -- THE load-bearing (and only) clause

  ``m`` is an ``EnumMember`` with two observed fields — ``qualifiedName`` (a
  fully-qualified textual identifier of the member, e.g. "Owner.NAME") and
  ``value`` (the underlying value it carries, either a textual value or an
  integral one). ``pyStr`` renders that underlying value: a textual value renders
  as itself, an integral value renders as its decimal numeral. The pinned
  behaviour is that the member's textual rendering equals the rendering of its
  UNDERLYING VALUE — never the qualified identifier, never a truncation, never
  the empty string.

BINDER STRUCTURE (read before judging binder coverage). The postcondition depends
on EXACTLY ONE input component — ``m.value``. The other field is DELIBERATELY free:

  * ``m.qualifiedName`` — the member's owner-qualified identifier. It exists only
    so a rival can state the WRONG answer (render the identifier instead of the
    value), which is exactly the un-fixed behaviour. The correct result never
    mentions it. It is varied across the reject witnesses so the coverage tool
    does not flag it pinned, while the DISCRIMINATION always comes from
    ``m.value``.
  * ``m.value`` — the load-bearing binder. ``pyStr`` splits on its constructor
    (textual vs integral), so the reject witnesses vary BOTH constructors: a
    textual value (where the identifier / a truncation diverges) and an integral
    value (where the decimal rendering must be produced).

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling holds the member's
    fields at a half-permission (``Acc(.,1/2)``) and makes its MANDATORY
    frame-mutation rival WRITE through that read-only reference (``self.value_text
    [i] = 88``) to normalize the input and satisfy the postcondition vacuously.
    Lean is referentially transparent: ``m`` is an immutable value with no heap
    footprint, no ``mut`` binder and no aliasing — there is no read-only field to
    overwrite and no substitute probe. NOT fabricated (per the porting map, this
    class is vacuous here); see ``assessment``.

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: an equality
    against ``pyStr m.value``, a term built ONLY from the input's own value field
    and fully unfolded (``pyStr`` is a transparent pattern match, not an
    axiomatized oracle). The bundle declares no ``opaque``/``axiom`` (meta.json
    axioms == [], deep_model_references == []), so there is no answer key an impl
    could echo without doing the work. The honest analogue is the
    cheapest-correct POSITIVE CONTROL below (a faithful element-for-value copy IS
    the correct impl).

  * WRONG-VALUE / PARTIAL-DOMAIN / VALUE-MASK — APPLY, and carry the lane. The
    pre-patch rendered the qualified identifier; a truncation renders a proper
    prefix; the empty string renders nothing; a constructor-selective rival
    mishandles only the integral arm. Each violates the one clause on a distinct
    sub-domain and is refuted with a witness at a distinct input.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``intro m; … rfl`` is tuned to the
frozen ``return pyStr m.value`` form — so a rejection alone attributes nothing to
the spec. Every ``expect="reject"`` case therefore carries a Lean snippet stating
the spec predicate directly at a ``decide``-able ground ``EnumMember``. Each was
checked (two real ``lake env lean`` builds) to ELABORATE against its rival and to
FAIL against the frozen solution (so it discriminates rather than asserting a
tautology): against gold the same ``decide`` faces ``pyStr m.value = pyStr
m.value`` and fails. All literals are ground (concrete ``String``/``Int``), so no
opaque term blocks ``decide`` and no hypothesis conditioning is needed.

BINDER COVERAGE. ``m.value`` is varied across both constructors and four distinct
values — textual ("FR", "first") and integral (1, 5); ``m.qualifiedName`` is
varied across all four witnesses ("YearInSchool.FRESHMAN", "Suit.DIAMOND", "X.Y",
"Suit.DIAMOND"). ``pts`` = 4 distinct input points.

AXIOM lane: EMPTY. meta.json ``axioms == []`` and ``deep_model_references`` covers
only the transparent value rendering (an A-reference validated by G-AX, not a
consumed axiom); the modeled behavior is a total rendering of an input field, so
there is no axiom-soundness obligation for THIS gate to re-discharge (that lane is
G-AX's). ``AXIOM_TESTS`` is therefore empty.
"""
from pathlib import Path

INSTANCE = "django__django-11964"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The FULL impl-region body and the FULL frozen tactic body, so every replacement
# lands entirely inside the region it means to edit.
_IMPL_GOLD = (
    "def implementation_memberStr (m : EnumMember) : String := Id.run do\n"
    "  return pyStr m.value\n"
)

_PROOF_BODY = (
    "  intro m\n"
    "  unfold problem_spec_memberStr implementation_memberStr\n"
    "  rfl\n"
)

assert _BASE.count(_IMPL_GOLD) == 1, "impl region drifted; update _IMPL_GOLD"
assert _BASE.count(_PROOF_BODY) == 1, "proof region drifted; update _PROOF_BODY"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl body."""
    return _swap(_BASE, _IMPL_GOLD, body)


# ---------------------------------------------------------------------------
# Rival impl bodies (each is a full impl region; only the impl changes, so the
# spec and the theorem STATEMENT stay byte-identical).
# ---------------------------------------------------------------------------

# WRONG-VALUE (= the pre-fix bug): render the fully-qualified identifier instead
# of the underlying value. This is exactly the inherited (un-fixed) behaviour.
_RIVAL_LABEL = (
    "def implementation_memberStr (m : EnumMember) : String := Id.run do\n"
    "  return m.qualifiedName\n"
)

# VALUE-MASK: render the empty string for every member — the cheapest wrong impl.
_RIVAL_EMPTY = (
    "def implementation_memberStr (m : EnumMember) : String := Id.run do\n"
    "  return \"\"\n"
)

# PARTIAL-DOMAIN: render the underlying value but drop its last character — a
# proper prefix, correct only on values that are already empty.
_RIVAL_TRUNCATE = (
    "def implementation_memberStr (m : EnumMember) : String := Id.run do\n"
    "  return (pyStr m.value).dropRight 1\n"
)

# CONSTRUCTOR-SELECTIVE: render textual values correctly but drop integral ones
# to the empty string. Correct on the textual arm, wrong on the integral arm —
# so it is refuted specifically at an integral value (this carrier splits the
# underlying value into textual/integral constructors; the nagini sibling's
# code-point list has no such split, so this rival is new coverage here).
_RIVAL_NUMDROP = (
    "def implementation_memberStr (m : EnumMember) : String := Id.run do\n"
    "  match m.value with\n"
    "  | .text s => return s\n"
    "  | .num _  => return \"\"\n"
)

# POSITIVE CONTROL (soundness) — a structurally different but CORRECT impl: drop
# the `Id.run do` scaffold and render the value directly. Definitionally the same
# value on every input, so the frozen `rfl` still closes (statement byte-identical).
_POS_DIRECT = (
    "def implementation_memberStr (m : EnumMember) : String :=\n"
    "  pyStr m.value\n"
)

# POSITIVE CONTROL (soundness) — a second, more different reshape: inline the
# rendering by matching on the value's constructor. The value equals the frozen
# one on both arms; the proof is retuned to close the collapsed match (verified
# with a real build). Only the impl and proof regions change; the theorem
# STATEMENT is byte-identical, and no helper lemma / axiom / assumption token is
# introduced.
_POS_MATCH = (
    "def implementation_memberStr (m : EnumMember) : String := Id.run do\n"
    "  match m.value with\n"
    "  | .text s => return s\n"
    "  | .num n  => return toString n\n"
)
_POS_MATCH_PROOF = (
    "  intro m\n"
    "  unfold problem_spec_memberStr implementation_memberStr\n"
    "  cases m.value <;> rfl\n"
)


def _witness(qname, value, comment):
    """A witness states the spec predicate directly at a ground EnumMember. It is
    checked in a file whose frozen obligation is elided by the gate, so no tactic
    script can mask the verdict; `EnumMember` fields are ground literals, so
    `decide` settles the `String` (in)equality after unfolding."""
    m = "{ qualifiedName := %s, value := %s }" % (qname, value)
    return (
        comment
        + "example : ¬ problem_spec_memberStr\n"
        f"    {m}\n"
        "    (implementation_memberStr\n"
        f"      {m}) := by\n"
        "  unfold problem_spec_memberStr implementation_memberStr\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_memberStr` statement byte-identical.
    # =====================================================================
    {
        "id": "pos-direct-render",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_DIRECT),
        "rationale": (
            "correct reshape of the mutable-`Id.run do` rendering into a direct "
            "return of `pyStr m.value`; it computes the same value on every input, "
            "so it must satisfy `result = pyStr m.value` — else SPEC-TOO-STRONG. "
            "Proof: the result is now definitionally `pyStr m.value`, so the frozen "
            "`intro m; unfold …; rfl` still closes. No new declaration, axiom, or "
            "assumption token; statement byte-identical."
        ),
    },
    {
        "id": "pos-match-constructor",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_impl(_POS_MATCH), _PROOF_BODY, _POS_MATCH_PROOF),
        "rationale": (
            "a more different CORRECT reshape: inline the value rendering by "
            "matching on the underlying value's constructor (textual → itself, "
            "integral → its decimal numeral), which is exactly what `pyStr` does, so "
            "`result = pyStr m.value` holds on both arms. A faithful reshape MUST "
            "verify, else the spec is over-fit to the exact rendering FORM => "
            "SPEC-TOO-STRONG. Proof: after `unfold`, `cases m.value <;> rfl` closes "
            "both collapsed arms; no new axiom/lemma, statement unchanged."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — a positive control confirming the obligation is SATISFIABLE
    # (non-vacuous) at the F2P-shaped input rather than only in the abstract. The
    # frozen theorem carries NO precondition hypothesis (the behavior is total, so
    # `∀` is unguarded), so nagini's precondition-admission probe has no binder to
    # attack; the honest analogue discharges the spec predicate at the concrete
    # F2P member (a textual member whose identifier differs from its value) inside
    # the proof region, alongside the frozen obligation.
    # =====================================================================
    {
        "id": "admiss-textchoice-ground",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _PROOF_BODY,
            "  have _ground : problem_spec_memberStr\n"
            "      { qualifiedName := \"MyChoice.FIRST_CHOICE\", value := .text \"first\" }\n"
            "      (implementation_memberStr\n"
            "        { qualifiedName := \"MyChoice.FIRST_CHOICE\", value := .text \"first\" }) := by\n"
            "    unfold problem_spec_memberStr implementation_memberStr\n"
            "    decide\n"
            + _PROOF_BODY,
        ),
        "rationale": (
            "the obligation is discharged at the concrete F2P member (a textual "
            "value \"first\" whose owner-qualified identifier \"MyChoice.FIRST_CHOICE\" "
            "differs from it) by `decide`, where the spec requires the rendering be "
            "the value \"first\" rather than the identifier; then the frozen "
            "obligation is closed verbatim. Verifies (else the modeled behavior is "
            "unsatisfiable at the normal input, the analogue of PRECOND-TOO-STRONG). "
            "Nothing is assumed: the theorem STATEMENT is byte-identical, the ground "
            "instance is a `have` inside the existing tactic body, and no new "
            "declaration/axiom/`sorry` is introduced."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing F2P tests.
    # =====================================================================
    {
        "id": "weak-qualified-identifier",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_LABEL),
        "refinement": (
            "this is EXACTLY the pre-fix behaviour: a member with no explicit "
            "textual conversion inherits the enumeration base's rendering, which "
            "returns the owner-qualified identifier ('YearInSchool.FRESHMAN', "
            "'Suit.DIAMOND') instead of the value ('FR', '1'). A faithful patch that "
            "kept that inherited rendering still renders the identifier and FAILS the "
            "F2P observable (the member's textual form must equal its value's textual "
            "form) — it is the unfixed bug, the definition of verify-does-not-resolve."
        ),
        "rationale": (
            "REJECT from `result = pyStr m.value`: the rival returns "
            "`m.qualifiedName`, which differs from `pyStr m.value` for every member "
            "whose identifier differs from its value. Refuted at a textual member "
            "(`value = .text \"FR\"`, `qualifiedName = \"YearInSchool.FRESHMAN\"`) — "
            "discrimination comes from the qualifiedName field being substituted for "
            "the value rendering."
        ),
        "witness": _witness(
            '"YearInSchool.FRESHMAN"', '.text "FR"',
            "-- Refuted at a textual member whose owner-qualified identifier differs\n"
            "-- from its value: the rendering must be the value, not the identifier.\n"),
    },
    {
        "id": "weak-empty-render",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_EMPTY),
        "refinement": (
            "rendering the empty string for every member returns nothing instead of "
            "the value's text; the F2P observable (the member's textual form equals "
            "its value's textual form) fails for every non-empty value. It is the "
            "cheapest wrong rendering — it does NOT resolve."
        ),
        "rationale": (
            "REJECT from `result = pyStr m.value`: the rival returns \"\" regardless "
            "of the input, differing from `pyStr m.value` for every non-empty value. "
            "Refuted at an INTEGRAL member (`value = .num 1`), where `pyStr` renders "
            "the decimal numeral \"1\" — varying the value binder onto its integral "
            "constructor (the other rivals refute on the textual arm)."
        ),
        "witness": _witness(
            '"Suit.DIAMOND"', '.num 1',
            "-- Refuted at an integral member: the rendering must be the decimal\n"
            "-- numeral \"1\", but an empty render surfaces nothing.\n"),
    },
    {
        "id": "weak-truncate-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_TRUNCATE),
        "refinement": (
            "rendering the value with its last character dropped returns a proper "
            "prefix ('firs' for 'first'); it diverges from the value text on every "
            "non-empty value, so the F2P observable (member text equals value text) "
            "fails on the entire non-empty sub-domain — it does NOT resolve."
        ),
        "rationale": (
            "REJECT from `result = pyStr m.value`: the rival returns `(pyStr "
            "m.value).dropRight 1`, a proper prefix that differs from `pyStr m.value` "
            "for every non-empty value. Refuted at a textual member "
            "(`value = .text \"first\"`), where the rival renders \"firs\" — a "
            "near-miss (right prefix, wrong tail) distinct from the empty and "
            "identifier rivals, so it carries its own distinguishing input."
        ),
        "witness": _witness(
            '"X.Y"', '.text "first"',
            "-- Refuted at a multi-character textual value: dropping the last\n"
            "-- character renders a proper prefix, not the full value text.\n"),
    },
    {
        "id": "weak-integral-arm-dropped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_RIVAL_NUMDROP),
        "refinement": (
            "rendering textual values faithfully but dropping integral values to the "
            "empty string is correct on the textual sub-domain yet wrong on every "
            "integral member; the F2P observable fails for integral members (their "
            "textual form must equal their decimal numeral) — it does NOT resolve."
        ),
        "rationale": (
            "REJECT from `result = pyStr m.value`: the rival matches the value's "
            "constructor and returns \"\" on the integral arm where the spec demands "
            "the decimal numeral. Refuted at an integral member (`value = .num 5`), "
            "where the rival renders \"\" but the spec demands \"5\" — exercising the "
            "integral constructor specifically, a distinction the split value carrier "
            "makes that the label/empty rivals do not isolate."
        ),
        "witness": _witness(
            '"Suit.DIAMOND"', '.num 5',
            "-- Refuted at an integral member: a constructor-selective impl that\n"
            "-- drops integral values renders \"\" where the decimal numeral \"5\" is\n"
            "-- required.\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 7 SPEC cases (2 soundness
# positives, 1 admissibility, 1 frame-mutation, 3 value/uniqueness rivals) plus a
# 1-case AXIOM lane. This bundle models a NARROWER surface: nagini contracts a
# permission-typed `render_to_text` over a per-code-point `List[int]`, whereas
# lean models the value-level string rendering `result = pyStr m.value` and folds
# the code-point copy into the transparent `pyStr`. Every sibling case is recorded
# below.
#
#   sibling case                    -> here
#   ---------------------------------------------------------------------
#   pos-control-reshape             -> pos-direct-render / pos-match  RE-EXPRESSED
#   pos-control-copy                -> pos-match-constructor          RE-EXPRESSED
#   admiss-selfcall                 -> admiss-textchoice-ground       RE-EXPRESSED
#   frame-mutate-value-text         -> (none)                        VACUOUS (no heap)
#   weak-qualified-label            -> weak-qualified-identifier      PORTED
#   weak-drop-last                  -> weak-truncate-last             PORTED
#   weak-empty                      -> weak-empty-render              PORTED
#   (new: split-carrier coverage)   -> weak-integral-arm-dropped      ADDED
#   AXIOM_TESTS (1)                 -> (none)                        DROPPED (G-AX)
#
# RE-EXPRESSED (positives): the nagini positives split the per-element append into
#   a temp read (pos-control-reshape) and a typed-local copy (pos-control-copy) to
#   show the take(i) loop invariant survives. This carrier has no loop — the copy
#   collapses to `pyStr m.value` — so the ARGUMENT ("a structurally different but
#   faithful impl must verify") is carried by two reshapes that ARE expressible on
#   the value-level rendering: dropping the `Id.run do` scaffold (pos-direct-render,
#   frozen `rfl` still closes) and inlining the rendering as a constructor match
#   (pos-match-constructor, proof retuned to `cases m.value <;> rfl`). Both build.
# RE-EXPRESSED (admissibility): the nagini self-call establishes render_to_text's
#   1/2 precondition for a freshly-built member. This bundle's `correct_memberStr`
#   carries NO precondition hypothesis (the `∀ m` is unguarded — the behavior is
#   total), so there is no precondition to admit; the honest analogue discharges the
#   spec at the concrete F2P member as a `have` ground instance, confirming the
#   obligation is non-vacuous at the normal input.
# VACUOUS (frame-mutation): the nagini sibling carries this MANDATORY because its
#   member fields are held at Acc(.,1/2) and a rival can illegally WRITE through the
#   read-only reference (`self.value_text[i] = 88`) to normalize the input. This
#   backend is referentially transparent and declares no `mut` binder over the
#   input — `m` is an immutable value with no heap footprint — so there is no
#   read-only field to overwrite and no substitute probe. Not fabricated (porting
#   map: vacuous here).
# PORTED / ADDED (value rivals): weak-qualified-label ports directly (render the
#   owner-qualified identifier — the pre-patch bug). weak-drop-last ports as
#   weak-truncate-last (a proper prefix). weak-empty ports as weak-empty-render.
#   weak-integral-arm-dropped is ADDED: this carrier splits the underlying value
#   into textual/integral constructors (nagini's code-point `List[int]` has no such
#   split), so a rival that mishandles ONLY the integral arm is a genuine coverage
#   addition, refuted specifically at an integral value. Each rival carries a
#   machine-checked witness that ELABORATES against the rival and FAILS against the
#   frozen solution.
#
#   The four witnesses probe four DISTINCT input tuples; across them m.value takes
#   {.text "FR", .num 1, .text "first", .num 5} (both constructors, four values)
#   and m.qualifiedName takes {"YearInSchool.FRESHMAN", "Suit.DIAMOND", "X.Y",
#   "Suit.DIAMOND"}. The load-bearing binder m.value is varied across both the
#   textual and integral arms. The free m.qualifiedName is varied too, though the
#   spec is genuinely independent of it (it exists only so the pre-patch rival can
#   state the wrong answer). pts = 4 distinct input points.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; the value rendering `pyStr`
# is a directive-7 deep-model reference (validated == real string conversion by
# G-AX), not a consumed axiom this gate re-discharges, so AXIOM_TESTS is empty and
# the gate ignores it regardless.
AXIOM_TESTS = []
