"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-9281 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside ``-- impl-start`` / ``-- impl-end`` — and, for a case
that legitimately re-proves, inside ``-- proof-start`` / ``-- proof-end`` — is
changed, so ``markers.same_spec`` holds and the single
``theorem correct_describeValue`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` HOLDS of the rival while FAILING on
the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models the display routine ``describe(value)`` over a ``PSeq[int]`` code-point
carrier with a five-way ``kind`` dispatch (collection kinds 0/1/2, enum kind 3,
generic fallback kind 4), pinning the enum arm against a GROUNDED pure deep model
(``enum_rendering(c, m) = c ++ '.' ++ m``). This Lean bundle models the SAME
purely-functional core at the granularity the fix distinguishes: a **plain
enumeration member** (carrying its class name and member name) versus **any other
value** (an opaque tag). The five nagini kinds collapse to TWO arms here — the
mapping bijection folds every non-enum kind (collection arms AND the generic
fallback) into the single ``other`` arm, whose display is the one the POST-PATCH
routine gives that value when it does not itself take the new enum arm (modeled
by the opaque carrier ``legacyDescription``; mapping.md pins that denotation and
the boundary it draws). So the nagini
kind-specific collection/fallback rivals have no separate counterpart; they are
subsumed by the single ``other``-arm attack (see accounting).

DEFENDED SURFACE (one modeled behavior; two independent top-level clauses).
``problem_spec_describeValue obj result`` matches on ``obj`` and pins EXACTLY:

  * (C-enum)  for a plain enumeration member, ``result = className ++ "." ++
    memberName`` — the qualified name: class name, a literal dot, member name.
    This is the LOAD-BEARING, discriminating clause: the behaviour the F2P test
    observes (an enumeration member renders as ``Class.Member``, NOT as the
    generic value-revealing fallback the pre-patch code produced). It is
    GROUNDED in the two input components — there is no opaque answer key to echo;
    the only way to satisfy it is to actually concatenate class, dot, member.
  * (C-other)  for any other value, ``result = legacyDescription obj`` — the
    result is pinned to the display the routine itself gives that value (the
    frame clause: such a value is not given the new treatment and must reproduce
    the routine's own output for it exactly, at the SAME value — a rival may
    neither substitute a constant nor call the carrier at a different value).

BINDER STRUCTURE. The spec predicate matches on the single input binder ``obj``.
For the ``enumMember`` arm that binder carries TWO components, ``className`` and
``memberName``, both load-bearing; for the ``other`` arm it carries the opaque
tag. The reject witnesses vary all three: rivals probe ``className``'s relevance
(class-name-only drops the member; member-only drops the class), the separator
between the two components, their ORDER (transposition — invisible to either drop
rival), the whole-arm substitution, the ``other`` arm (both replaced by a
constant and applied to the WRONG value, which is what varies the tag binder), and
the clause's UNIVERSAL force (an impl correct at exactly the observed member and
pre-patch at every other one). The eight reject witnesses probe eight DISTINCT
``obj`` values (see point-spread).

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. Nagini's mandatory attack writes into
    the read-only ``value.member_name`` 1/2 list to subvert the read-only
    precondition. On this referentially transparent carrier there is no heap, no
    fractional permission, no ``mut`` input binder, and no aliasable cell to
    overwrite — ``obj`` is an immutable value. The class is vacuous; the frame
    obligation instead lives in the C-other clause (the ``other`` arm's result is
    pinned to ``legacyDescription obj`` verbatim), which the ``other``-arm rival
    below attacks. No substitute mutation probe is fabricated (porting map).

  * DIVERGENCE / NON-TERMINATION — NOTHING TO SHIP, but not for the reason first
    recorded. Nagini's ``w-diverge`` rival is an endless loop that satisfies every
    ``Ensures`` vacuously under partial correctness, rejected there only by
    ``MustTerminate(2)``. The port originally claimed a diverging implementation
    "cannot be written at all" on this backend. AUDIT CORRECTION: it can — a
    ``partial def implementation_describeValue obj := implementation_describeValue
    obj`` is well-typed, passes ``variant_scope`` (no new axiom, statement
    byte-identical), and elaborates. What is genuinely unavailable is the SECOND
    half of a reject case: a diverging impl is an opaque constant with no
    reduction behaviour, so no witness can discriminate it from the frozen
    solution. Measured with three real builds: the natural conditioned witness
    (``implementation_describeValue v ≠ "Dv" ++ "." ++ "Rg"``) elaborates against
    the diverging rival AND against the frozen solution (both exit 0) — i.e. it is
    a TAUTOLOGY the gate would correctly record as ``witness-vacuous``, because
    the hypothesis is strong enough to refute the spec for any impl. So the
    disposition (nothing to port) stands on the witness half, NOT on
    inexpressibility of the rival. Note the rival is nonetheless REJECTED here on
    its own: the frozen proof cannot close for it (measured: ``Tactic `rfl`
    failed`` on both arms), because ``partial`` supplies no equation to reduce —
    unlike velvet's ``partial`` semantics, where such an impl verifies vacuously
    (a known spec hole recorded in ``the corpus-wide termination-semantics finding``, NOT re-reported
    here).

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The C-enum clause is GROUNDED: ``result`` is
    pinned by concatenation of the two input string components with a literal
    dot. There is no opaque answer key an implementation could echo — building
    ``className ++ "." ++ memberName`` IS doing the work. Nagini carries an
    ``echo-honest`` redundant-assert positive to demonstrate non-echo-vulnerability;
    on this carrier the honest cheapest-implementation positive controls below
    play that role (there is no separate oracle def to redundantly re-assert).

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where the fix bites: rendering the enum member as the generic
    fallback (the pre-patch bug); joining with the wrong separator; dropping the
    member name; dropping the class name; and replacing the ``other`` arm's
    result with a constant (attacks the frame clause C-other).

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof (``cases obj <;> rfl``) is tuned
to the frozen impl's syntactic form — so a rejection alone attributes nothing to
the spec. Every ``expect="reject"`` case therefore carries a Lean snippet that
states the spec predicate at one CONCRETE input and refutes it. The FOUR C-enum
rivals whose output is a concrete string literal (wrong separator, class-only,
member-only, transposed) are refuted by ``decide`` at a ground ``enumMember``
value. The FOUR rivals whose divergence is entangled with the OPAQUE
``legacyDescription`` (enum-as-fallback, f2p-point-overfit, other-arm-constant,
other-arm tag-collapse) cannot be refuted by computation — the carrier will not
reduce — so
their witnesses CONDITION on the carrier: ONE hypothesis naming the opaque term
(``legacyDescription v ≠ <the rival's substitute>``, where the substitute is the
pinned qualified name for the two enum-arm rivals, a literal for
other-arm-constant, and ``legacyDescription`` at a DIFFERENT argument for
the tag-collapse rival — two applications of one carrier, still no contradictory
pair), stating that WHENEVER the existing routine differs from the rival's
substitute, the rival contradicts the spec — exactly the sub-domain where the
rival is wrong. Note that conditioning must stay TIGHT: a hypothesis about
``implementation_describeValue`` itself rather than about the carrier would refute
the spec for ANY impl including the frozen one, which the gate records as
``witness-vacuous`` (measured — see the DIVERGENCE entry). Each witness was
checked with real ``lake env lean`` builds to HOLD of its rival (exit 0) and to
FAIL on the frozen solution (exit 1), and each conditioned witness additionally
had its hypotheses confirmed satisfiable by the gate's consistency probe, so it
discriminates rather than asserting a tautology.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues that its faithful real counterpart
renders an enumeration member wrong (as the ugly generic fallback, or with the
wrong separator, or missing a component) or corrupts the unchanged rendering of
other values, so ``test_object_description_enum`` — which pins the exact
``Class.Member`` text — would mismatch and the faithful patch would NOT resolve.

AXIOM lane: DROPPED. The nagini ``AXIOM_TESTS`` probe the A-reference deep model
``enum_rendering``; the axiom lane belongs to G-AX. This bundle declares one
``opaque`` carrier (``legacyDescription``) but consumes NO ``axiom`` about it
(the enum rendering is modeled deeply as concatenation; the proof uses no
property of the opaque carrier), so there is nothing for this gate to probe and
the ``AXIOM_TESTS`` are dropped.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9281"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The enum-arm body line: the grounded concatenation the fix emits (impl region).
_ENUM_RET = '    return className ++ "." ++ memberName\n'
# The fall-through return for any other value (impl region); this is the frame
# clause's realization — the result equals the existing routine's output.
_OTHER_RET = "  return legacyDescription obj\n"
# The WHOLE impl body of the enum-branch conditional (for the structural
# reshapes and the enum-as-fallback rival).
_IMPL_BODY = (
    "  if let .enumMember className memberName := obj then\n"
    '    return className ++ "." ++ memberName\n'
    "  -- Any other value falls through to the existing display routine.\n"
    "  return legacyDescription obj"
)
# The frozen proof's `intro` line (proof region) — unique — so the admissibility
# positive can prepend a ground `have` without touching the theorem STATEMENT.
_P_INTRO = "  intro obj\n"
# The frozen proof's WHOLE tactic body (proof region). A positive whose reshape is
# NOT definitionally the frozen impl has to re-prove its enum arm, and only the
# tactic body may differ — the theorem STATEMENT stays byte-identical.
_P_BODY = (
    "  intro obj\n"
    "  cases obj with\n"
    "  | enumMember className memberName => rfl\n"
    "  | other tag => rfl\n"
)


# ---------------------------------------------------------------------------
# witness scaffolds.
# ---------------------------------------------------------------------------
def _w_enum_concrete(cls, mem):
    """Refute C-enum at a concrete enumeration member whose rival output is a
    ground string literal — reduced and refuted by `decide`."""
    return (
        f'example : ¬ problem_spec_describeValue (.enumMember "{cls}" "{mem}")\n'
        f'    (implementation_describeValue (.enumMember "{cls}" "{mem}")) := by\n'
        "  unfold problem_spec_describeValue implementation_describeValue\n"
        "  decide\n")


def _w_enum_conditioned(cls, mem):
    """Refute C-enum for a rival whose enum output is the OPAQUE
    `legacyDescription` (enum-as-fallback). Conditioned on the carrier: whenever
    the existing routine differs from the pinned qualified name, the rival's
    output differs from the spec's. One hypothesis, one opaque term."""
    v = f'(PyValue.enumMember "{cls}" "{mem}")'
    return (
        f'example (h : legacyDescription {v} ≠ "{cls}" ++ "." ++ "{mem}") :\n'
        f"    ¬ problem_spec_describeValue {v}\n"
        f"    (implementation_describeValue {v}) := by\n"
        "  unfold problem_spec_describeValue implementation_describeValue\n"
        "  simpa using h\n")


def _w_other_conditioned(tag, const):
    """Refute C-other for a rival that replaces the existing routine's output
    with the constant `const`. Conditioned on the carrier: whenever the existing
    routine differs from that constant, the rival contradicts the frame clause.
    The spec states `result = legacyDescription obj`, i.e. `const = legacy`, so
    the hypothesis `legacy ≠ const` refutes it via `.symm`."""
    v = f"(PyValue.other {tag})"
    return (
        f'example (h : legacyDescription {v} ≠ "{const}") :\n'
        f"    ¬ problem_spec_describeValue {v}\n"
        f"    (implementation_describeValue {v}) := by\n"
        "  unfold problem_spec_describeValue implementation_describeValue\n"
        "  intro heq\n"
        "  exact h heq.symm\n")


def _w_other_tag_collapse(bad, pinned):
    """Refute C-other for a rival that renders EVERY other value as the existing
    routine's output for ONE fixed value (`.other pinned`) instead of for the
    value it was given. Conditioned on the carrier at `.other bad`: whenever the
    existing routine distinguishes those two values — which it must, since they
    are distinct values with distinct displays — the rival contradicts the frame
    clause. Two applications of ONE opaque carrier at two distinct arguments, so
    the hypothesis is satisfiable by construction (nothing can derive `False`
    from `legacyDescription x ≠ legacyDescription y` for `x ≠ y`)."""
    v = f"(PyValue.other {bad})"
    return (
        f"example (h : legacyDescription {v}\n"
        f"    ≠ legacyDescription (PyValue.other {pinned})) :\n"
        f"    ¬ problem_spec_describeValue {v}\n"
        f"    (implementation_describeValue {v}) := by\n"
        "  unfold problem_spec_describeValue implementation_describeValue\n"
        "  intro heq\n"
        "  exact h heq.symm\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_describeValue` statement byte-identical and re-uses the
    # frozen proof body (`cases obj <;> rfl`), which closes for these reshapes
    # because they are definitionally the frozen impl.
    # =====================================================================
    {
        "id": "pos-match-form",
        "kind": "soundness",
        "expect": "verify",
        # Reshape the `if let … then … ; return …` into an explicit two-arm
        # `match`. Identical values on every input; the frozen `cases obj <;> rfl`
        # still closes (each arm reduces by `rfl`). No proof authoring, no helper
        # lemma, no assumption token. (Verified: real build.)
        "module": _swap(
            _BASE, _IMPL_BODY,
            "  match obj with\n"
            '  | .enumMember className memberName => return className ++ "." ++ memberName\n'
            "  | .other _ => return legacyDescription obj"),
        "rationale": "structurally-different but CORRECT reshape: the `if let` guard "
                     "is rewritten as an explicit two-arm `match` on `obj`. It "
                     "computes the SAME result on every input, so C-enum and C-other "
                     "both still hold — else SPEC-TOO-STRONG. Definitionally the "
                     "frozen impl, so the frozen proof (`cases obj <;> rfl`) still "
                     "closes; statement byte-identical, no new axiom/lemma. Ports "
                     "nagini's pos-control-disj-reorder (there: reorder the "
                     "collection-arm disjunction; here that dispatch collapses to two "
                     "arms, so the analogous correct reshape is the match form).",
    },
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Branch-REORDER positive control: test the `other` arm FIRST, the enum
        # arm second. Same values, different control-flow order. The frozen proof
        # `cases obj <;> rfl` is order-independent (it discharges both arms), so it
        # still closes. Statement byte-identical; no new axiom/lemma.
        # (Verified: real build.)
        "module": _swap(
            _BASE, _IMPL_BODY,
            "  match obj with\n"
            "  | .other _ => return legacyDescription obj\n"
            '  | .enumMember className memberName => return className ++ "." ++ memberName'),
        "rationale": "branch-REORDER positive control: the two match arms are written "
                     "in the opposite order (other first, enum second) — identical "
                     "values, different control flow. A faithful reshape MUST verify, "
                     "else SPEC-TOO-STRONG. The frozen `cases obj <;> rfl` discharges "
                     "both arms regardless of textual order, so it still closes "
                     "(statement byte-identical, no new axiom/lemma). Ports nagini's "
                     "pos-control-disj-reorder shape (order-independent dispatch).",
    },

    {
        "id": "pos-append-right-assoc",
        "kind": "soundness",
        "expect": "verify",
        # AUDIT ADDITION. The two reshapes above are DEFINITIONALLY the frozen
        # impl, so `cases obj <;> rfl` closes them unchanged — which means neither
        # tests whether the spec accepts a correct impl that is NOT defeq to the
        # frozen one. This one is: `++` is left-associative, so the frozen enum arm
        # parses as `(className ++ ".") ++ memberName`, whereas this impl appends
        # the dot to the MEMBER name first — `className ++ ("." ++ memberName)`.
        # Equal by associativity of string append, but NOT by `rfl`: measured, the
        # frozen proof body leaves `className.append (".".append memberName) =
        # className ++ "." ++ memberName` open. So the enum arm is re-proven inside
        # the proof region (permitted: only the tactic body differs, the theorem
        # STATEMENT stays byte-identical) via `String.append_assoc`. No new
        # axiom/lemma/`sorry`. If this could NOT be proven, the spec would be
        # over-fit to one parse of `++` => SPEC-TOO-STRONG. (Verified: real build,
        # exit 0.)
        "module": _swap(
            _swap(
                _BASE, _IMPL_BODY,
                "  match obj with\n"
                "  | .enumMember className memberName =>\n"
                '    return String.append className (String.append "." memberName)\n'
                "  | .other _ => return legacyDescription obj"),
            _P_BODY,
            "  intro obj\n"
            "  cases obj with\n"
            "  | enumMember className memberName =>\n"
            '    show className ++ ("." ++ memberName) = className ++ "." ++ memberName\n'
            '    exact (String.append_assoc className "." memberName).symm\n'
            "  | other tag => rfl\n"),
        "rationale": "NON-DEFEQ correct reshape — the positive control the other two "
                     "cannot be. `++` is left-associative, so the frozen enum arm "
                     "parses as `(className ++ \".\") ++ memberName`; this impl builds "
                     "`className ++ (\".\" ++ memberName)` instead. Same string on "
                     "every input (associativity of append), but NOT definitionally "
                     "equal: measured, the frozen `cases obj <;> rfl` leaves the enum "
                     "arm open, so this case genuinely re-proves it (tactic body only; "
                     "statement byte-identical, no new axiom/lemma). A faithful "
                     "correct impl the spec REJECTED would be SPEC-TOO-STRONG — the "
                     "spec must pin the STRING, not one parse of the concatenation. "
                     "The pos-match-form / pos-branch-reorder reshapes are both "
                     "definitionally the frozen impl, so neither exercises this.",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at a
    # normal, F2P-shaped input. Discharge the spec predicate by evaluation at the
    # F2P member `MyEnum.FOO` (rendering the exact `"MyEnum.FOO"` the F2P test
    # observes) as a `have`, then close the frozen obligation verbatim. Nothing is
    # assumed: no new declaration, statement byte-identical, ground instance is a
    # `have` prepended to the existing tactic body. (Verified: real build.)
    # =====================================================================
    {
        "id": "admiss-f2p-member",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            '  have _f2p : problem_spec_describeValue (.enumMember "MyEnum" "FOO")\n'
            '      (implementation_describeValue (.enumMember "MyEnum" "FOO")) := by\n'
            "    unfold problem_spec_describeValue implementation_describeValue\n"
            "    rfl\n"
            + _P_INTRO),
        "rationale": "the obligation is discharged at the exact F2P input — a plain "
                     "enumeration member with class name `MyEnum` and member name "
                     "`FOO`, whose modeled display is `MyEnum.FOO`, the text the F2P "
                     "test observes — by evaluation as a `have`, then the frozen "
                     "obligation is closed verbatim. Verifies (else the modeled "
                     "behavior would be unsatisfiable at a normal F2P input — the "
                     "analogue of PRECOND-TOO-STRONG / SPEC-UNUSABLE). Nothing is "
                     "assumed: no new declaration, statement byte-identical, ground "
                     "instance is a `have` in the existing tactic body. Ports "
                     "nagini's admiss-enum-shaped.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a witness pinning the
    # violation at one concrete input.
    # =====================================================================

    # ---- the discriminating bug: render the enum member as the fallback ----
    {
        "id": "rival-enum-as-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-patch behaviour: no dedicated enum treatment, so a plain enumeration
        # member falls through to the existing routine (the generic
        # value-revealing fallback). Drop the enum branch entirely.
        "module": _swap(
            _BASE, _IMPL_BODY, "  return legacyDescription obj"),
        "refinement": "this IS the pre-patch behaviour: with no dedicated enum arm, a "
                      "plain enumeration member falls through to the existing routine, "
                      "which renders it as the generic value-revealing form (the ugly "
                      "`<Class.Member: value>`) rather than the qualified name. Its "
                      "faithful real patch is the pre-patch code, which FAILS "
                      "test_object_description_enum (it observes `Class.Member`, not "
                      "the fallback) — it would NOT resolve.",
        "rationale": "REJECT from C-enum: the spec pins `className ++ \".\" ++ "
                     "memberName` for an enumeration member, but the rival returns "
                     "`legacyDescription obj` (the existing routine's output). "
                     "Refuted by CONDITIONING on the opaque carrier at `MyEnum.FOO`: "
                     "whenever the existing routine differs from `MyEnum.FOO`, the "
                     "rival contradicts the spec. If it verified => SPEC-TOO-WEAK "
                     "(admits the pre-patch fall-through bug).",
        "witness": _w_enum_conditioned("MyEnum", "FOO"),
    },

    # ---- wrong separator ----
    {
        "id": "rival-wrong-separator",
        "kind": "uniqueness",
        "expect": "reject",
        # Join the class name and member name with '/' instead of '.'.
        "module": _swap(
            _BASE, _ENUM_RET, '    return className ++ "/" ++ memberName\n'),
        "refinement": "joins the class and member names with `/` instead of `.`. A "
                      "faithful real patch emitting `\"%s/%s\"` would render "
                      "`MyEnum/FOO` and FAIL test_object_description_enum (which pins "
                      "`MyEnum.FOO`) — it would NOT resolve.",
        "rationale": "REJECT from C-enum: the spec pins the literal `.` separator "
                     "(`className ++ \".\" ++ memberName`) but the rival emits `/`. "
                     "Refuted at the concrete member `.enumMember \"A\" \"B\"`, whose "
                     "rival output `\"A/B\"` is a ground literal `decide` refutes "
                     "against the pinned `\"A.B\"`. If it verified => SPEC-TOO-WEAK "
                     "(separator not pinned).",
        "witness": _w_enum_concrete("A", "B"),
    },

    # ---- class-name only (member dropped) ----
    {
        "id": "rival-class-name-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit only `class name .` — drop the member name.
        "module": _swap(
            _BASE, _ENUM_RET, '    return className ++ "."\n'),
        "refinement": "drops the member name, rendering just `class name .`. A "
                      "faithful real patch emitting `\"%s.\" % cls.__name__` would "
                      "render `MyEnum.` and FAIL test_object_description_enum (which "
                      "pins `MyEnum.FOO`) — it would NOT resolve.",
        "rationale": "REJECT from C-enum: the spec pins `className ++ \".\" ++ "
                     "memberName` but the rival drops the member component, emitting "
                     "`className ++ \".\"`. Refuted at `.enumMember \"Cls\" \"Mem\"`, "
                     "whose rival output `\"Cls.\"` (a ground literal) `decide` "
                     "refutes against the pinned `\"Cls.Mem\"`. If it verified => "
                     "SPEC-TOO-WEAK (member name not pinned).",
        "witness": _w_enum_concrete("Cls", "Mem"),
    },

    # ---- member-name only (class dropped) ----
    {
        "id": "rival-member-name-only",
        "kind": "uniqueness",
        "expect": "reject",
        # Emit only `. member name` — drop the class name. The dual of the
        # class-name-only rival; it varies the OTHER enum component so the
        # className binder is exercised too.
        "module": _swap(
            _BASE, _ENUM_RET, '    return "." ++ memberName\n'),
        "refinement": "drops the class name, rendering just `. member name`. A "
                      "faithful real patch emitting `\".%s\" % member.name` would "
                      "render `.FOO` and FAIL test_object_description_enum (which "
                      "pins `MyEnum.FOO`) — it would NOT resolve.",
        "rationale": "REJECT from C-enum, exercising the OTHER enum component: the "
                     "spec pins `className ++ \".\" ++ memberName` but the rival drops "
                     "the class component, emitting `\".\" ++ memberName`. Refuted at "
                     "`.enumMember \"Klass\" \"Nom\"`, whose rival output `\".Nom\"` (a "
                     "ground literal) `decide` refutes against the pinned "
                     "`\"Klass.Nom\"`. If it verified => SPEC-TOO-WEAK (class name not "
                     "pinned). No nagini counterpart — nagini's carrier copies the "
                     "class name in a loop it never neutered; added so both enum "
                     "components are attacked.",
        "witness": _w_enum_concrete("Klass", "Nom"),
    },

    # ---- components TRANSPOSED (both present, wrong order) ----
    {
        "id": "rival-components-transposed",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT ADDITION. Emit `memberName ++ "." ++ className` — both components
        # present, both separated by the correct literal dot, only the ORDER wrong.
        # The three drop/separator rivals above are all refuted by a witness that
        # would also refute an impl merely missing a component; none of them pins
        # the ORDER of the two components, which the class-name-only and
        # member-name-only pair cannot detect (each drops one component, so neither
        # observes a transposition). Distinct point: `.enumMember "Ecls" "Emem"`.
        "module": _swap(
            _BASE, _ENUM_RET, '    return memberName ++ "." ++ className\n'),
        "refinement": "renders the two components in the wrong order — member name "
                      "first, then the class name. A faithful real patch emitting "
                      "`\"%s.%s\"` with the two substitutions swapped would render "
                      "`FOO.MyEnum` and FAIL test_object_description_enum (which pins "
                      "`MyEnum.FOO`) — it would NOT resolve. This is a plausible real "
                      "slip precisely because both components ARE read and the dot IS "
                      "emitted; the display is simply inverted.",
        "rationale": "REJECT from C-enum: the spec pins `className ++ \".\" ++ "
                     "memberName` — an ORDERED concatenation — but the rival emits "
                     "`memberName ++ \".\" ++ className`. Neither the class-name-only "
                     "nor the member-name-only rival can catch this: each DROPS a "
                     "component, so a transposition is invisible to both. Refuted at "
                     "`.enumMember \"Ecls\" \"Emem\"`, whose rival output `\"Emem.Ecls\"` "
                     "is a ground literal `decide` refutes against the pinned "
                     "`\"Ecls.Emem\"`. If it verified => SPEC-TOO-WEAK (the spec would "
                     "pin the multiset of components rather than their order).",
        "witness": _w_enum_concrete("Ecls", "Emem"),
    },

    # ---- correct at the OBSERVED point, wrong everywhere else ----
    {
        "id": "rival-f2p-point-overfit",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT ADDITION (second audit). Every other C-enum rival is wrong at the
        # observed point itself, so each of them would still be rejected by a spec
        # that pinned the enum arm only AT that one member. This rival is the
        # complement: it emits the correct qualified name for exactly ONE member
        # (class `MyEnum`, member `FOO`) and hands every other enumeration member
        # to the existing routine — i.e. it keeps the pre-patch display for the
        # whole rest of the enum arm. It is the "hardcode the answer you were
        # measured on" attack, and it is the only rival in the battery that
        # separates the modeled clause from the single observation: the clause is
        # UNIVERSALLY quantified over `obj`, so satisfying it at one member is not
        # satisfying it. Distinct point: `.enumMember "Other" "BAR"` — a member no
        # other case uses, and the only point in the battery chosen because the
        # rival is RIGHT elsewhere rather than wrong there.
        "module": _swap(
            _BASE, _IMPL_BODY,
            "  if let .enumMember className memberName := obj then\n"
            '    if className == "MyEnum" && memberName == "FOO" then\n'
            '      return "MyEnum.FOO"\n'
            "    return legacyDescription obj\n"
            "  return legacyDescription obj"),
        "refinement": "unlike the other rivals this one DOES satisfy the single "
                      "assertion the F2P test makes — it special-cases exactly that "
                      "member — so its refinement is not \"the test would fail\" but "
                      "\"the test is not the behaviour\": the described display rule "
                      "is stated for a plain enumeration member generally, and a "
                      "faithful patch of this shape would leave EVERY other "
                      "enumeration member rendered by the existing routine, i.e. "
                      "still showing the value-revealing form the report complains "
                      "about. It resolves the observation and not the issue, which "
                      "is precisely the verify-but-not-resolve artifact this lane "
                      "exists to exclude; the spec must reject it on the strength of "
                      "the clause, not of the test.",
        "rationale": "REJECT from C-enum, attacking the clause's UNIVERSAL force: the "
                     "spec pins `result = className ++ \".\" ++ memberName` for every "
                     "plain enumeration member, and this rival satisfies that at one "
                     "hardcoded member while returning `legacyDescription obj` for all "
                     "the others. No other reject case can catch this — each of them "
                     "is wrong AT the observed member too, so every one of them would "
                     "still be rejected by a spec that pinned the enum arm only at "
                     "that single point; this rival is rejected only because the "
                     "clause quantifies. Refuted by CONDITIONING on the opaque carrier "
                     "at a DIFFERENT member, `.enumMember \"Other\" \"BAR\"`: whenever "
                     "the existing routine differs from `Other.BAR`, the rival "
                     "contradicts the spec there. If it verified => SPEC-TOO-WEAK (the "
                     "spec would pin only the one member the observation names, which "
                     "is the weakest thing a spec can do and still look green).",
        "witness": _w_enum_conditioned("Other", "BAR"),
    },

    # ---- other-arm corruption (attacks the frame clause C-other) ----
    {
        "id": "rival-other-arm-constant",
        "kind": "uniqueness",
        "expect": "reject",
        # Corrupt the unchanged rendering of a non-enum value: return the empty
        # string instead of deferring to the existing routine. Attacks C-other,
        # the frame clause (the analogue of nagini's read-only frame protection).
        "module": _swap(_BASE, _OTHER_RET, '  return ""\n'),
        "refinement": "corrupts the unchanged rendering of a non-enumeration value "
                      "(and of container-mixin enum members captured by an earlier "
                      "branch), returning the empty string instead of deferring to "
                      "the existing routine. A faithful real patch that blanked those "
                      "values' display would break every PASS_TO_PASS case that reads "
                      "back a non-enum default value's rendering — it would NOT "
                      "resolve (and would regress the unchanged behaviour the fix "
                      "must preserve).",
        "rationale": "REJECT from C-other (the frame clause): the spec pins `result = "
                     "legacyDescription obj` for any other value, but the rival "
                     "returns the constant `\"\"`. Refuted by CONDITIONING on the "
                     "opaque carrier at `.other 0`: whenever the existing routine's "
                     "output is non-empty, the rival contradicts the frame clause. "
                     "This is the referentially-transparent analogue of nagini's "
                     "frame-mutate-member probe (the read-only non-enum rendering "
                     "must be reproduced, not overwritten). If it verified => "
                     "SPEC-TOO-WEAK (frame clause hollow).",
        "witness": _w_other_conditioned(0, ""),
    },

    # ---- other-arm tag collapse (the `other` binder must be USED) ----
    {
        "id": "rival-other-arm-tag-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        # AUDIT ADDITION. Render every other value as the existing routine's output
        # for ONE fixed value, ignoring the value actually passed. The
        # other-arm-constant rival above replaces the whole arm with a literal, so
        # it is refuted by a witness that only needs `legacyDescription v ≠ ""`;
        # it does NOT establish that the arm must be applied to the value it was
        # GIVEN. This rival still calls the existing routine — it simply calls it
        # on the wrong argument — so it probes the `other` arm's tag binder, the
        # one binder no other case varies. Distinct point: `.other 1`.
        "module": _swap(
            _BASE, _OTHER_RET, "  return legacyDescription (PyValue.other 0)\n"),
        "refinement": "renders every non-enumeration value using the existing "
                      "routine's output for one FIXED value rather than for the value "
                      "it was handed — e.g. every default value's display becomes the "
                      "display of some other, unrelated value. A faithful real patch "
                      "that passed a fixed stand-in to the existing rendering instead "
                      "of the actual argument would report the wrong text for every "
                      "non-enumeration value, breaking the PASS_TO_PASS cases that "
                      "read back a container's or a plain value's rendering — it "
                      "would NOT resolve.",
        "rationale": "REJECT from C-other (the frame clause), attacking the `other` "
                     "arm's TAG binder: the spec pins `result = legacyDescription obj` "
                     "— the existing routine applied to THE VALUE GIVEN — but the "
                     "rival applies it to a fixed value instead. The "
                     "other-arm-constant rival cannot catch this: its witness only "
                     "needs the routine's output to differ from a literal, which says "
                     "nothing about WHICH value the routine is applied to. Refuted by "
                     "CONDITIONING at `.other 1`: whenever the existing routine "
                     "distinguishes `.other 1` from `.other 0` (it must — they are "
                     "distinct values), the rival contradicts the frame clause. Two "
                     "applications of ONE opaque carrier, jointly satisfiable. If it "
                     "verified => SPEC-TOO-WEAK (the frame clause would not pin the "
                     "argument, only the routine).",
        "witness": _w_other_tag_collapse(1, 0),
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 8 SPEC cases (3 soundness/
# admissibility positives, 4 uniqueness rivals, 1 divergence rival) plus a
# 2-case AXIOM lane. This bundle models the SAME purely-functional core but at a
# TWO-arm granularity (plain enum member vs any other value) where nagini used a
# five-way kind dispatch, so several nagini cases collapse or become vacuous.
#
#   sibling case              -> here                          disposition
#   -----------------------------------------------------------------------
#   pos-control-disj-reorder  -> pos-match-form,               RE-EXPRESSED
#                                pos-branch-reorder,            (+1 reorder shape,
#                                pos-append-right-assoc          +1 NON-DEFEQ, audit)
#   echo-honest               -> (subsumed by positives)       RE-EXPRESSED
#   admiss-enum-shaped        -> admiss-f2p-member             PORTED
#   frame-mutate-member       -> rival-other-arm-constant      RE-EXPRESSED
#   rival-enum-as-fallback    -> rival-enum-as-fallback        PORTED
#   rival-wrong-separator     -> rival-wrong-separator         PORTED
#   rival-class-name-only     -> rival-class-name-only         PORTED
#   (none)                    -> rival-member-name-only        ADDED (2nd component)
#   (none)                    -> rival-components-transposed   ADDED (audit: order)
#   (none)                    -> rival-other-arm-tag-collapse  ADDED (audit: tag)
#   (none)                    -> rival-f2p-point-overfit       ADDED (audit 2: the
#                                                               clause's universal
#                                                               force vs the one
#                                                               observed point)
#   w-diverge                 -> (none)                        NO WITNESS POSSIBLE
#   AXIOM_TESTS (2)           -> (none)                        DROPPED (G-AX)
#
# RE-EXPRESSED (pos-match-form / pos-branch-reorder): nagini's structurally-
#   different positive reorders the collection-arm membership disjunction
#   (kind ∈ {0,1,2}). That five-way dispatch collapses here to a two-arm match,
#   so the analogous "correct reshape" is (a) the explicit match form and (b) the
#   two arms in reversed order. Both are definitionally the frozen impl, so the
#   frozen proof `cases obj <;> rfl` closes for each (verified with real builds).
# RE-EXPRESSED (echo-honest): nagini re-asserts the grounded pin redundantly to
#   show the spec is not echo-vulnerable. This carrier has no separate oracle def
#   to re-assert (the enum rendering is inlined concatenation); the honest
#   cheapest-impl positive controls above play the same non-echo-vulnerability
#   role. The spec is grounded in the two input string components — there is no
#   opaque answer key to echo — so there is no reject case to author here.
# RE-EXPRESSED (frame-mutate-member -> rival-other-arm-constant): nagini's
#   mandatory frame attack writes into the read-only member-name list. This
#   carrier is referentially transparent — no heap, no fractional permission, no
#   mutable input — so the mutation class is VACUOUS. The frame OBLIGATION it
#   defended (read-only inputs are reproduced, not corrupted) survives as the
#   C-other clause: the non-enum branch's result is pinned to the existing
#   routine's output verbatim. The other-arm-constant rival attacks exactly that
#   clause, so the frame protection is still tested — via the value relation, not
#   a permission check.
# ADDED (rival-member-name-only): nagini refutes dropping the member name
#   (rival-class-name-only) but never drops the CLASS name — its carrier copies
#   the class name in a loop it did not neuter. To exercise both components of the
#   enum arm (both are load-bearing binders of C-enum), this rival drops the class
#   name instead. It attacks the SAME modeled clause, not an unmodeled behavior.
# NO WITNESS POSSIBLE (w-diverge): nagini's endless-loop vacuity rival is rejected
#   there only by MustTerminate(2). The RIVAL is expressible here — see the
#   DIVERGENCE entry in the module docstring — so the class is NOT vacuous, and the
#   sentence that used to stand here ("a diverging implementation cannot be
#   written") was false. What is unavailable is the second half of a reject case.
#   Re-measured in the second audit with real builds: the `partial def` self-call
#   passes variant_scope and is REJECTED on its own (exit 1, ``Tactic `rfl` failed``
#   on both arms, so this backend does not admit the vacuous proof at all), but the
#   only witness one can state about it elaborates against the frozen solution TOO
#   (both exit 0) — a `partial` self-call is an opaque constant with no reduction
#   behaviour and no carrier term to condition on, so there is nothing to
#   discriminate at. The gate would record `witness-vacuous`. Hence: nothing to
#   ship, on the WITNESS half. Not a spec hole either (the rival does not verify),
#   so nothing to escalate.
# DROPPED (AXIOM_TESTS): nagini's two probes validate the A-reference deep model
#   `enum_rendering` against the real enum rendering. The axiom lane is G-AX's
#   job; this bundle consumes NO axiom (the enum rendering is modeled deeply as
#   concatenation, and the opaque `legacyDescription` carries no `_prop` the proof
#   uses), so there is nothing to probe and the gate ignores AXIOM_TESTS.
#
# POINT SPREAD. The eight reject witnesses probe eight DISTINCT `obj` values:
#   obj =
#     .enumMember "MyEnum" "FOO"   rival-enum-as-fallback     C-enum (conditioned)
#     .enumMember "A" "B"          rival-wrong-separator      C-enum (decide)
#     .enumMember "Cls" "Mem"      rival-class-name-only      C-enum (decide)
#     .enumMember "Klass" "Nom"    rival-member-name-only     C-enum (decide)
#     .enumMember "Ecls" "Emem"    rival-components-transposed  C-enum (decide)
#     .enumMember "Other" "BAR"    rival-f2p-point-overfit    C-enum (conditioned)
#     .other 0                     rival-other-arm-constant   C-other (conditioned)
#     .other 1                     rival-other-arm-tag-collapse C-other (conditioned)
#   Across them BOTH arms of the match (enumMember, other) are attacked; BOTH enum
#   components (className, memberName) are varied and independently refuted; their
#   ORDER is pinned separately from their presence; the `other` arm's TAG binder is
#   varied (two distinct tags, refuted against each other); and one point is chosen
#   for the opposite reason to all the others — because the rival is RIGHT at the
#   observed member and wrong away from it, which is what tests that the clause
#   quantifies rather than naming the one member the F2P test asserts. So no input
#   binder is pinned to a single value across the battery, and no case's rejection
#   would survive weakening C-enum to that single observed point.
#
# AUDIT ADDITIONS (independent audit of the recorded SOUND; three gaps closed):
#   pos-append-right-assoc       both shipped positives were DEFINITIONALLY the
#                                frozen impl (the frozen `cases obj <;> rfl` closes
#                                them untouched), so neither tested whether the
#                                spec accepts a correct impl that is NOT defeq to
#                                gold. This one is not defeq — it re-proves the
#                                enum arm via `String.append_assoc` — so it is the
#                                battery's first real SPEC-TOO-STRONG probe.
#   rival-components-transposed  no case pinned the ORDER of the two enum
#                                components. The class-name-only / member-name-only
#                                pair each DROP a component, so a transposition is
#                                invisible to both.
#   rival-other-arm-tag-collapse no case varied the `other` arm's tag binder. The
#                                other-arm-constant rival's witness only needs the
#                                routine's output to differ from a literal, which
#                                does not establish that the routine must be
#                                applied to the value it was GIVEN.
#   Also corrected: the divergence-class prose claimed a diverging impl "cannot be
#   written at all" on this backend. It can (a `partial def` self-call elaborates
#   and passes variant_scope); what actually fails is the WITNESS half, measured
#   with real builds. See the DIVERGENCE entry in the module docstring. The
#   disposition (nothing to ship) is unchanged.
#
# SECOND AUDIT (independent re-audit of the re-recorded SOUND). Attacks A/B/B'/C
# on the eight then-shipped cases found no hollow case: every statement is
# byte-identical to the frozen one and all text outside the impl/proof regions is
# too; each reject witness rebuilt to rival 0 / gold 1; each conditioned witness's
# consistency probe failed (exit 1 = hypotheses satisfiable, the safe direction);
# and the FORGERY pair was run for all four non-`decide` signature classes — the
# flipped claim (asserting the spec HOLDS at the same point) elaborates against the
# FROZEN solution (0) and fails against the RIVAL (1), the exact inversion of the
# witness, so gold's exit code carries information about the claim rather than
# about a tactic mismatch. Two defects were found and fixed:
#   rival-f2p-point-overfit  every reject case was wrong AT the observed member as
#                            well as away from it, so the battery never separated
#                            "the clause holds for every plain enumeration member"
#                            from "the display is right for the one member the F2P
#                            test asserts". A spec pinning only that single point
#                            would have rejected all eight rivals and passed the
#                            battery. This rival is correct exactly there and
#                            pre-patch everywhere else, so only the clause's
#                            universal force rejects it. Measured before shipping:
#                            rejected under the frozen proof AND under a
#                            strengthened `simp_all` body (exit 1, goal left open at
#                            the guarded `if`), witness rival 0 / gold 1, probe 1,
#                            forgery flip gold 0 / rival 1.
#   w-diverge accounting     the table below still recorded the class "VACUOUS on
#                            lean" and repeated the "cannot be written" claim that
#                            the previous audit had already retracted in the
#                            docstring — so the file asserted both. Corrected to the
#                            measured disposition; see that entry.
# Attacks D and E found no hole in the FROZEN spec. Three further wrong impls (the
# overfit above, wrong only on the empty-member-name sub-domain, and the `other` arm
# wrong at one tag) were all REJECTED; four further correct reshapes (`s!` string
# interpolation, `String.intercalate "." [c, m]`, the `other` arm reconstructing its
# value from the tag binder, and appending `""` to the `other` arm's result — the
# last non-defeq, needing `simp`) were all ACCEPTED.
AXIOM_TESTS = []
