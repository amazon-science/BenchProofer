"""properties.py — G-PBT falsification battery for astropy__astropy-7606 (lean).

NOT a Lean file; a manifest the G-PBT gate executes. Each SPEC case is a full
``Solution.lean`` variant that shares the FROZEN spec byte-for-byte (region
surgery: only text inside the ``-- impl-start`` / ``-- impl-end`` region — and,
for a case that legitimately re-proves, inside the ``-- proof-start`` /
``-- proof-end`` region — is changed, so ``markers.same_spec`` holds and the
single ``theorem correct_unrecognizedUnitEq`` STATEMENT stays byte-identical).
``expect:"verify"`` passes iff (in scope AND the file elaborates with the
obligation closed, no ``sorry``/``admit``/``native_decide`` and no new
``axiom``/``theorem``); ``expect:"reject"`` passes iff (in scope AND it does NOT
verify AND the case's refutation ``witness`` holds of the rival while FAILING on
the frozen solution).

PORT NOTE — carrier narrowing. The nagini sibling models TWO patched equality
dunders, abstracted to boolean observables and a three-valued integer tag:
``eq_unparsed_name`` (the F2P-discriminating hunk) and ``eq_unit`` (the companion
hunk on the base class). This Lean bundle models only the FIRST — the
purely-functional core of the F2P-discriminating comparison, ``selfName`` +
``ParseOutcome`` → ``Except UnitError EqResult`` — and mapping.md records that the
companion base-class edit is behaviour-PRESERVING for every F2P/P2P test and is
therefore NOT modeled as a separate triple here. So every nagini case attached to
``eq_unit`` (``rival-unit-defer-as-false``, ``rival-unit-notunit-as-false``, and
the ``eq_unit`` legs of the admissibility/positive cases) has NO counterpart on
this carrier and is legitimately omitted — this is carrier narrowing, not a
dropped attack; see the accounting block at the bottom. The three nagini cases
that DO attach to the modeled behavior port directly, and two finer-grained
rivals are added to cover both sub-binders of the ``.parsed`` decision (see
below).

DEFENDED SURFACE (one modeled behavior; two independent top-level branches of
the comparison rule). ``problem_spec_unrecognizedUnitEq selfName po result`` pins
``result = eqResult selfName po`` EXACTLY, i.e. for every input:

  * (RAISED branch)  ``po = .raised`` ⟹ ``result = .ok .notApplicable`` — an
    operand that cannot be interpreted as a unit yields the "not applicable"
    sentinel, NEVER an escaping error and never a definite decision. This is the
    F2P discriminator: the pre-patch code lets the interpretation failure escape
    (``.error``), so ``unit == None`` terminates with an error instead of a
    boolean.
  * (PARSED branch) ``po = .parsed isUnrecognized otherName`` ⟹ ``result =
    .ok (if isUnrecognized && selfName == otherName then .isTrue else .isFalse)``
    — a definite decision that is TRUE iff the operand parsed to an unrecognised
    unit (``isUnrecognized``) carrying a matching name (``selfName == otherName``),
    and FALSE otherwise.

BINDER STRUCTURE. The spec predicate has TWO input binders: ``selfName : String``
and ``po : ParseOutcome``, where ``po`` further carries the two sub-binders
``isUnrecognized : Bool`` and ``otherName : String`` in its ``.parsed``
constructor. All are load-bearing and all are varied across the reject witnesses
(see the point-spread block at the bottom): ``selfName`` takes six distinct
literals, ``po`` ranges over ``.raised`` and ``.parsed`` with ``isUnrecognized ∈
{true,false}`` and ``otherName`` both matching and non-matching. The seven reject
witnesses probe seven DISTINCT input tuples, and on the RESULT side both halves of
the ``Except UnitError EqResult`` carrier are refuted — six rivals inside
``.ok`` and one on the ``.error`` leg.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini sibling already notes its
    inputs are plain value-typed booleans carrying no heap permission, so its
    frame-mutation class is vacuous THERE; on this referentially transparent
    carrier it is doubly so — ``selfName``/``po`` are immutable values, there is
    no ``mut`` input binder, no aliasing, no read-only cell to overwrite. No
    substitute probe is fabricated (porting map: vacuous here).

  * DIVERGENCE / NON-TERMINATION — VACUOUS on lean. ``implementation_*`` is a
    total Lean ``def`` (a ``match`` on a finite inductive), so a diverging
    implementation cannot be written at all. (The nagini sibling carries no
    ``diverge-*``/``nonterm-*`` case either.)

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is GROUNDED: ``result``
    is pinned by ``eqResult``, a structural function of the two input binders
    (the branch on ``po`` and the ``isUnrecognized && selfName == otherName``
    decision). There is no opaque answer key an implementation could echo —
    producing the tag from ``po`` and the name comparison IS doing the work. In
    its place the battery carries honest cheapest-implementation POSITIVE
    CONTROLS that must verify.

  * PARTIAL-DOMAIN / VALUE — APPLIES. Rivals correct on part of the domain but
    diverging where the spec bites: the interpretation failure propagating as
    ``.error`` on ``.raised`` (the F2P bug proper) and the same branch decided as
    a definite ``.isFalse``; never reporting a definite equal on the parsed
    branch; deferring for every parsed operand; and dropping each of the two
    conjuncts of the parsed decision individually.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen proof (``cases po <;> rfl``) is tuned to
the frozen form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet that states the spec
predicate at ONE concrete ground input, unfolds it against the rival's impl, and
closes by ``simp`` (which reduces the ``Id.run do`` ``match`` and discharges the
resulting concrete inequality of ``Except`` values). Each witness binds NOTHING
in its head (all inputs are ground literals — a ``String`` and a ``ParseOutcome``
constructor application), so there are no hypotheses whose consistency could be
in question (the gate's consistency probe is correctly skipped: nothing binds).
Each was checked with two real ``lake env lean`` builds to HOLD of its rival and
to FAIL on the frozen solution, so it discriminates rather than asserting a
tautology.

Each gold-side failure is a PLAIN EVALUATION — ``unsolved goals ⊢ False``: the
witness's input is ground, so ``simp`` reduces the spec on both sides and the
residual goal is the decided (in)equality itself, never a stuck reduction, a
missing identifier or a type error. That the exit code tracks the CLAIM rather
than the file's shape is established per case by the flipped-claim experiment
(drop the ``¬``): the flipped witness VERIFIES against the frozen solution
(exit 0) and FAILS against the rival (exit 1) — the exact inverse of the
witness's own pair, so each build's verdict is carrying information about what
is being asserted at that input.

REFINEMENT (why a verifying rival would be a true verify-but-not-resolve break).
Each reject case's ``refinement`` argues its faithful real counterpart would NOT
resolve the F2P ``test_unknown_unit3`` (which asserts ``unit == "FOO"`` is True,
``unit != u.m`` is True, and ``unit != None`` / ``unit not in (None, u.m)`` — the
latter two only terminate at all once the interpretation failure is caught; the
test additionally carries, from before, ``unit == unit2`` for a same-named
unrecognised operand and ``unit != unit3`` for a differently-named one).

REACHABILITY CAVEAT (established by audit; keep it honest). A rival can violate
the spec on this carrier at an input the REAL system cannot present, because
``ParseOutcome`` is a free 2-constructor inductive while the real interpretation
step is a FUNCTION of the operand string. Such a rival is still a legitimate
spec-strength probe — the spec pins ``eqResult`` on all of ``ParseOutcome``, so
its rejection is genuinely attributable to the spec — but it must NOT claim its
faithful real counterpart would fail the F2P, because that counterpart is
observationally equivalent to gold on every reachable operand. Exactly one case
here is in that position (``rival-drop-kind-conjunct``: its divergence needs one
string to be interpretable and un-interpretable at once) and its ``refinement``
says so explicitly. Every OTHER reject case's refutation point is realizable, and
four of the six are literal F2P operand shapes.

AXIOM lane: EMPTY here. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the comparison rule is modeled deeply/structurally over
``ParseOutcome``); the axiom lane belongs to G-AX, and the nagini ``AXIOM_TESTS``
are dropped.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-7606"
BACKEND = "lean"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# The parsed-branch decision expression of the impl (the load-bearing conjunction
# that pins .isTrue/.isFalse). Unique in the file and wholly inside
# `-- impl-start`/`-- impl-end`.
_I_PARSED_DECIDE = (
    "      return .ok (if isUnrecognized && selfName == otherName "
    "then .isTrue else .isFalse)")
# The whole `.parsed` arm (constructor pattern + body), used when a rival needs
# to discard the field bindings.
_I_PARSED_ARM = (
    "  | .parsed isUnrecognized otherName =>\n"
    "      return .ok (if isUnrecognized && selfName == otherName "
    "then .isTrue else .isFalse)")
# The raised-branch body.
_I_RAISED = "  | .raised =>\n      return .ok .notApplicable"

# Frozen proof body — unique in the file, wholly inside `-- proof-start`/
# `-- proof-end` — so a re-proving positive can replace it without touching the
# spec view or the `correct_unrecognizedUnitEq` STATEMENT.
_P_BODY = "  cases po <;> rfl"
# The frozen proof's intro line, used by the admissibility positive to prepend a
# ground `have` while keeping the theorem statement byte-identical.
_P_INTRO = "  intro selfName po"


# ---------------------------------------------------------------------------
# witness scaffold. States the spec predicate at one ground input against the
# variant's impl, unfolds, and closes by `simp` (which reduces the `Id.run do`
# match and the concrete `Except` (in)equality). No hypotheses => nothing whose
# consistency could be in question.
# ---------------------------------------------------------------------------
def _w(args):
    return (
        f"example : ¬ problem_spec_unrecognizedUnitEq {args}\n"
        f"    (implementation_unrecognizedUnitEq {args}) := by\n"
        "  unfold problem_spec_unrecognizedUnitEq implementation_unrecognizedUnitEq eqResult\n"
        "  simp\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    # `theorem correct_unrecognizedUnitEq` statement byte-identical.
    # =====================================================================
    {
        "id": "pos-let-bound-decision",
        "kind": "soundness",
        "expect": "verify",
        # Correct reshape: bind the parsed-branch decision to a local before
        # returning it. Definitionally identical to the frozen body, so the frozen
        # proof (`cases po <;> rfl`) still closes — no proof authoring, no helper
        # lemma, no assumption token. (Verified: real build.)
        "module": _swap(
            _BASE, _I_PARSED_DECIDE,
            "      let namesMatch := isUnrecognized && selfName == otherName\n"
            "      return .ok (if namesMatch then .isTrue else .isFalse)"),
        "rationale": "correct reshape that binds the parsed-branch decision to a "
                     "local `namesMatch` before returning; it computes the SAME "
                     "result on every input, so both branches of the spec still "
                     "hold — else SPEC-TOO-STRONG. The impl is definitionally the "
                     "frozen body, so the frozen proof (`cases po <;> rfl`) still "
                     "closes; statement byte-identical, no new axiom/lemma. Ports "
                     "the nagini pos-unparsed-restructured positive (there: the "
                     "definite decision collapsed into a computed boolean local).",
    },
    {
        "id": "pos-nested-if",
        "kind": "soundness",
        "expect": "verify",
        # Structurally DIFFERENT correct reshape: the single flat conjunction is
        # split into a nested if/else (test isUnrecognized first, then the name
        # equality). Same values, different control-flow shape — the proof region
        # is re-proved (case split + `split`), statement byte-identical, no new
        # axiom/lemma. (Verified: real build.)
        "module": _swap(
            _swap(
                _BASE, _I_PARSED_DECIDE,
                "      if isUnrecognized then\n"
                "        if selfName == otherName then return .ok .isTrue "
                "else return .ok .isFalse\n"
                "      else\n"
                "        return .ok .isFalse"),
            _P_BODY,
            "  cases po with\n"
            "  | raised => rfl\n"
            "  | parsed isUnrecognized otherName =>\n"
            "      cases isUnrecognized <;> simp <;> split <;> simp_all"),
        "rationale": "correct control-flow reshape: the flat `isUnrecognized && "
                     "selfName == otherName` decision is split into a nested "
                     "if/else. Identical values, different shape — a faithful "
                     "reshape MUST verify, else SPEC-TOO-STRONG. Re-proved by "
                     "case-splitting `po` and `isUnrecognized` and discharging the "
                     "nested `if` with `split`; statement byte-identical, no new "
                     "axiom/lemma. Ports the nagini pos-unparsed-restructured "
                     "positive's spirit (a different control shape for the definite "
                     "decision).",
    },

    # =====================================================================
    # ADMISSIBILITY — confirm the obligation is SATISFIABLE (non-vacuous) at a
    # normal, F2P-shaped input. The frozen theorem carries no precondition, so the
    # nagini precondition-admission self-call re-expresses as: discharge the spec
    # predicate by evaluation at the concrete F2P-shaped input (a matching-name
    # unrecognised operand, the `unit == "FOO"` → isTrue case) as a `have`, then
    # close the frozen obligation verbatim. Nothing is assumed: no new declaration,
    # statement byte-identical, ground instance is a `have` prepended to the
    # existing tactic body. (Verified: real build.)
    # =====================================================================
    {
        "id": "admiss-ground-equal",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _P_INTRO,
            '  have _ground : problem_spec_unrecognizedUnitEq "FOO" '
            '(ParseOutcome.parsed true "FOO")\n'
            '      (implementation_unrecognizedUnitEq "FOO" '
            '(ParseOutcome.parsed true "FOO")) := by\n'
            "    unfold problem_spec_unrecognizedUnitEq "
            "implementation_unrecognizedUnitEq eqResult\n"
            "    rfl\n"
            # The obligation alone does not pin WHICH value satisfies it, so the
            # two `have`s below evaluate the two F2P-asserted results explicitly:
            # the definite equal on a matching-name unrecognised operand, and the
            # sentinel on an operand that cannot be interpreted as a unit (the
            # discriminating input — the one that must RETURN rather than fail).
            '  have _f2p_true : implementation_unrecognizedUnitEq "FOO" '
            '(ParseOutcome.parsed true "FOO") = .ok .isTrue := by\n'
            "    unfold implementation_unrecognizedUnitEq\n"
            "    rfl\n"
            '  have _f2p_sentinel : implementation_unrecognizedUnitEq "FOO" '
            "ParseOutcome.raised = .ok .notApplicable := by\n"
            "    unfold implementation_unrecognizedUnitEq\n"
            "    rfl\n"
            + _P_INTRO),
        "rationale": "the obligation is discharged at the F2P-shaped input "
                     "(a matching-name unrecognised operand — the `unit == \"FOO\"` "
                     "→ isTrue case the F2P test asserts) by evaluation as a `have`, "
                     "then the frozen obligation is closed verbatim. Two further "
                     "ground `have`s EVALUATE the two results the F2P test asserts — "
                     "the definite equal on the matching-name unrecognised operand, "
                     "and the not-applicable sentinel on an operand that cannot be "
                     "interpreted as a unit — so the case pins the VALUES and not "
                     "merely the satisfiability of the obligation. Verifies (else "
                     "the modeled behavior would be unsatisfiable at exactly a "
                     "normal F2P input — the analogue of PRECOND-TOO-STRONG). "
                     "Nothing is assumed: no new declaration, statement "
                     "byte-identical, ground instances are `have`s in the existing "
                     "tactic body. Ports nagini's admiss-defer-self-call (there: a "
                     "self-call establishing the precondition on an F2P input).",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries (a) the refinement argument that its
    # faithful real patch would NOT resolve the F2P, and (b) a witness pinning the
    # violation at one concrete input.
    # =====================================================================

    # ---- the F2P bug proper: the interpretation failure ESCAPES to the caller ----
    {
        "id": "rival-raised-escapes",
        "kind": "uniqueness",
        "expect": "reject",
        # The one rival whose result leaves the `.ok` half of the carrier: on an
        # uninterpretable operand the interpretation failure propagates as
        # `.error .parseError` instead of yielding the not-applicable sentinel.
        # This is the ACTUAL modeled defect (it is the impl the frozen
        # Solution_prepatch.lean carries, i.e. the shape G-DIFF uses as "the bug");
        # every other reject case in this battery stays inside `.ok` and therefore
        # never probes the `Except` error leg at all.
        "module": _swap(
            _BASE, _I_RAISED,
            "  | .raised =>\n      return .error .parseError"),
        "refinement": "lets the interpretation failure PROPAGATE to the caller "
                      "(`.error .parseError`) instead of yielding the "
                      "not-applicable sentinel. Its faithful real counterpart is "
                      "the comparison that consumes the interpretation step with no "
                      "handler at all, so comparing against an operand that cannot "
                      "be interpreted as a unit terminates with an escaping error "
                      "rather than a value; the F2P `test_unknown_unit3` asserts "
                      "such a comparison is True, which requires it to RETURN at "
                      "all, so the assertion does not merely fail — it errors out. "
                      "It would NOT resolve.",
        "rationale": "the F2P-discriminating bug in its true shape, and the only "
                     "case in this battery that exercises the ERROR leg of the "
                     "`Except UnitError EqResult` carrier. REJECT from the RAISED "
                     "branch: the spec pins `.raised ⟹ .ok .notApplicable`, i.e. "
                     "the sentinel and NOT an escaping error, but the rival emits "
                     "`.error .parseError`. If it verified => SPEC-TOO-WEAK (the "
                     "spec's \"never propagates the interpretation failure\" clause "
                     "would be unenforced, which is precisely the modeled defect). "
                     "Ports nagini's rival-unparsed-defer-as-false in the register "
                     "the Lean carrier actually gives it. Refuted at "
                     "selfName=\"N\", po=.raised.",
        "witness": _w('"N" ParseOutcome.raised'),
    },

    # ---- the interpretation failure decided as a definite False ----
    {
        "id": "rival-raised-as-false",
        "kind": "uniqueness",
        "expect": "reject",
        # Same branch, the OTHER way to get it wrong: stay inside `.ok` but emit a
        # definite decision where the spec pins the sentinel.
        "module": _swap(
            _BASE, _I_RAISED,
            "  | .raised =>\n      return .ok .isFalse"),
        "refinement": "returns a DEFINITE .isFalse on an operand that cannot be "
                      "interpreted as a unit, instead of the not-applicable "
                      "sentinel. Its faithful real counterpart catches the "
                      "interpretation failure but then decides the comparison "
                      "itself rather than declining to decide, so the comparison "
                      "never defers to the reflected/identity comparison. It "
                      "terminates, so it is a strictly nearer miss than the "
                      "escaping-error rival above, but it still hard-codes a "
                      "decision the spec reserves for the sentinel — a "
                      "behavioural regression against the modeled rule, so it "
                      "would NOT be the gold change.",
        "rationale": "near-miss on the RAISED branch, distinguishing the SENTINEL "
                     "from a definite decision (the escaping-error rival above "
                     "distinguishes it from an error). REJECT: the spec pins "
                     "`.raised ⟹ .ok .notApplicable` but the rival emits "
                     "`.ok .isFalse`. If it verified => SPEC-TOO-WEAK (admits a "
                     "definite decision on an uninterpretable operand). Refuted at "
                     "selfName=\"A\", po=.raised.",
        "witness": _w('"A" ParseOutcome.raised'),
    },

    # ---- never reports a definite equal on the parsed branch ----
    {
        "id": "rival-parsed-never-true",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct on .raised, but on EVERY parsed operand returns .isFalse — it
        # never reports a definite equal.
        "module": _swap(
            _BASE, _I_PARSED_ARM,
            "  | .parsed _isUnrecognized _otherName =>\n"
            "      return .ok .isFalse"),
        "refinement": "defers correctly on uninterpretable operands but reports a "
                      "definite .isFalse on EVERY parsed operand — it NEVER returns "
                      "a definite equal. Its faithful real counterpart drops the "
                      "name/kind decision and hard-returns a definite \"not equal\" "
                      "for any interpretable operand, so comparing the unit against "
                      "its own name string is false and the F2P assertion that it is "
                      "true FAILS — it would NOT resolve.",
        "rationale": "partial-domain on the definite-EQUAL sub-domain. REJECT from "
                     "the PARSED branch: the spec pins `.isTrue` when "
                     "`isUnrecognized && selfName == otherName`, but the rival emits "
                     "`.isFalse` there. If it verified => SPEC-TOO-WEAK (never "
                     "reports equal). Ports nagini's rival-unparsed-never-true. "
                     "Refuted at selfName=\"B\", po=.parsed true \"B\" (the "
                     "equal-name case).",
        "witness": _w('"B" (ParseOutcome.parsed true "B")'),
    },

    # ---- always defers, even for a parsed operand ----
    {
        "id": "rival-always-defer",
        "kind": "uniqueness",
        "expect": "reject",
        # Returns the not-applicable sentinel for EVERY operand — never decides a
        # parsed operand.
        "module": _swap(
            _BASE, _I_PARSED_ARM,
            "  | .parsed _isUnrecognized _otherName =>\n"
            "      return .ok .notApplicable"),
        "refinement": "returns the not-applicable sentinel for EVERY operand, never "
                      "deciding a parsed one. Its faithful real counterpart declines "
                      "to decide unconditionally, so comparing the unit against its "
                      "own name string defers to the reflected comparison and is "
                      "false — the F2P assertion that it is true FAILS — and it "
                      "would NOT resolve.",
        "rationale": "supporting near-miss with a real refinement: total but never "
                     "decides a parsed operand. REJECT from the PARSED branch: the "
                     "spec pins `.isTrue`/`.isFalse` (never `.notApplicable`) for a "
                     "parsed operand, but the rival emits `.notApplicable`. If it "
                     "verified => SPEC-TOO-WEAK (the parsed operand is never "
                     "decided). Ports nagini's rival-unparsed-always-defer. Refuted "
                     "at selfName=\"C\", po=.parsed false \"m\" (a recognised-unit "
                     "operand, the isFalse case).",
        "witness": _w('"C" (ParseOutcome.parsed false "m")'),
    },

    # ---- drop the isUnrecognized conjunct of the parsed decision ----
    {
        "id": "rival-drop-kind-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        # Decide on name equality ALONE, ignoring whether the parsed value is an
        # unrecognised unit. Correct on the whole domain except a recognised unit
        # whose name happens to equal selfName, where it wrongly reports equal.
        "module": _swap(
            _BASE, _I_PARSED_DECIDE,
            "      return .ok (if selfName == otherName then .isTrue else .isFalse)"),
        "refinement": "ignores whether the operand parsed to an unrecognised unit "
                      "and decides on name equality alone. HONEST SCOPE (corrected "
                      "by audit — do not restore the stronger claim): this rival's "
                      "divergence set is exactly `{(selfName, .parsed false "
                      "otherName) : selfName == otherName}`, and that set is "
                      "UNREACHABLE in the real system. Reaching it needs the same "
                      "string to be simultaneously un-interpretable (so that this "
                      "unit is an unrecognised one carrying it as its name) and "
                      "interpretable as a recognised unit (so that the operand "
                      "parses to a recognised unit carrying it as ITS name) — "
                      "contradictory, since the lenient interpretation step is a "
                      "function of the string. So its faithful real counterpart is "
                      "observationally EQUIVALENT to the gold comparison on every "
                      "reachable operand: it would resolve the F2P and regress no "
                      "P2P. This case is therefore a pure CARRIER-LEVEL "
                      "spec-strength probe on the `isUnrecognized` sub-binder, not "
                      "an F2P discriminator; the reachable attack on that same "
                      "binder is rival-parsed-always-true below, whose divergence "
                      "point IS a literal F2P operand.",
        "rationale": "partial-domain: attacks the `isUnrecognized` sub-binder of "
                     "the parsed decision. REJECT from the PARSED branch: the spec "
                     "pins `.isFalse` when `isUnrecognized = false` even if names "
                     "match, but the rival emits `.isTrue`. If it verified => "
                     "SPEC-TOO-WEAK (drops the kind check — the spec would not pin "
                     "the kind conjunct at all). Kept because the spec pins "
                     "`eqResult` on ALL of `ParseOutcome`, so this is a genuine "
                     "(machine-checked) violation and its rejection is "
                     "spec-attributable; but see the refinement — its divergence "
                     "point is not reachable in the real system, so it carries NO "
                     "F2P-resolution claim. Refuted at selfName=\"D\", "
                     "po=.parsed false \"D\" (the sole point where it diverges).",
        "witness": _w('"D" (ParseOutcome.parsed false "D")'),
    },

    # ---- drop the name-equality conjunct of the parsed decision ----
    {
        "id": "rival-drop-name-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        # Decide on isUnrecognized ALONE, ignoring the name comparison. Correct
        # except for an unrecognised unit whose name DIFFERS, where it wrongly
        # reports equal.
        "module": _swap(
            _BASE, _I_PARSED_DECIDE,
            "      return .ok (if isUnrecognized then .isTrue else .isFalse)"),
        "refinement": "ignores the name comparison and decides on the "
                      "unrecognised-kind alone. Its faithful real counterpart drops "
                      "the name-equality conjunct, so two DISTINCTLY-named "
                      "unrecognised units are wrongly reported equal — a behavioural "
                      "regression vs the gold comparison that would misreport the "
                      "name distinction the comparison suite pins. It would NOT "
                      "resolve.",
        "rationale": "partial-domain: attacks the `otherName` sub-binder of the "
                     "parsed decision. REJECT from the PARSED branch: the spec pins "
                     "`.isFalse` when `selfName != otherName` even if "
                     "`isUnrecognized`, but the rival emits `.isTrue`. If it "
                     "verified => SPEC-TOO-WEAK (drops the name check). Refuted at "
                     "selfName=\"E\", po=.parsed true \"Z\" (unrecognised unit, "
                     "non-matching name — the sub-domain this rival gets wrong).",
        "witness": _w('"E" (ParseOutcome.parsed true "Z")'),
    },

    # ---- reports a definite EQUAL for every parsed operand ----
    # ADDED BY AUDIT. The two conjunct-dropping rivals above each attack one
    # sub-binder of the parsed decision, but only one of them (the name conjunct)
    # diverges at an input the real system can actually present: the kind-conjunct
    # rival's divergence set requires one string to be both interpretable and
    # un-interpretable at once, so it is unreachable and carries no F2P claim.
    # That left the `isUnrecognized` conjunct with NO rival whose divergence point
    # is realizable — and therefore left the "a recognised operand compares FALSE"
    # half of the parsed branch attacked only vacuously. This rival closes that:
    # it drops the kind test in the direction that IS reachable (a recognised
    # operand wrongly reported equal), and its refutation point is the literal
    # F2P operand — comparing this unit against a recognised unit.
    {
        "id": "rival-parsed-always-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(
            _BASE, _I_PARSED_ARM,
            "  | .parsed _isUnrecognized _otherName =>\n"
            "      return .ok .isTrue"),
        "refinement": "reports a definite EQUAL for EVERY operand that interprets "
                      "as a unit, dropping both halves of the parsed decision. "
                      "Unlike the two conjunct-dropping rivals, its divergence set "
                      "is REACHABLE and contains a literal F2P operand: comparing "
                      "this unrecognised unit against a RECOGNISED unit (which "
                      "interprets fine, is not an unrecognised unit, and carries a "
                      "different name) must be FALSE, and the F2P test asserts "
                      "exactly that inequality. Its faithful real counterpart "
                      "reports that comparison as equal, so the F2P assertion that "
                      "the two differ FAILS. It also collapses the "
                      "different-name case, so the pre-existing base assertion that "
                      "two differently-named unrecognised units are unequal fails "
                      "too. It would NOT resolve.",
        "rationale": "partial-domain on the definite-FALSE sub-domain of the PARSED "
                     "branch — the reachable attack on the `isUnrecognized` "
                     "sub-binder. REJECT: the spec pins `.isFalse` for a parsed "
                     "operand that is not an unrecognised unit with a matching "
                     "name, but the rival emits `.isTrue`. If it verified => "
                     "SPEC-TOO-WEAK (the spec would not pin the definite-FALSE "
                     "half of the parsed decision at all, which is a clause the "
                     "F2P directly observes). Refuted at selfName=\"FOO\", "
                     "po=.parsed false \"m\" — the literal F2P operand shape "
                     "(a recognised unit), where the spec pins .isFalse.",
        "witness": _w('"FOO" (ParseOutcome.parsed false "m")'),
    },
]

# ---------------------------------------------------------------------------
# Nagini -> lean accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 5 uniqueness rivals — but 2 of those 5 rivals plus
# one positive and the admissibility self-call attach to the sibling's SECOND
# modeled function, the base-class comparison) plus a 2-probe AXIOM lane. This
# Lean bundle models only the FIRST behavior, so the second function's cases have
# no carrier here and are legitimately omitted (carrier narrowing; mapping.md
# records the base-class edit as behaviour-preserving and NOT separately
# modeled). Every sibling case is recorded below.
#
#   sibling case                    -> here
#   -----------------------------------------------------------------------
#   pos-unparsed-restructured       -> pos-let-bound-decision  RE-EXPRESSED
#                                      + pos-nested-if          (2nd shape ADDED)
#   pos-unit-restructured           -> (none)                  OMITTED (2nd fn
#                                                               not modeled)
#   admiss-defer-self-call          -> admiss-ground-equal     RE-EXPRESSED
#   rival-unparsed-defer-as-false   -> rival-raised-escapes    PORTED (the F2P bug,
#                                                               error leg)
#                                      + rival-raised-as-false  (near-miss ADDED)
#   rival-unparsed-never-true       -> rival-parsed-never-true PORTED
#   rival-unparsed-always-defer     -> rival-always-defer      PORTED
#   rival-unit-defer-as-false       -> (none)                  OMITTED (2nd fn)
#   rival-unit-notunit-as-false     -> (none)                  OMITTED (2nd fn)
#   (none)                          -> rival-drop-kind-conjunct ADDED (isUnrecognized,
#                                                               carrier-only: see caveat)
#   (none)                          -> rival-drop-name-conjunct ADDED (otherName)
#   (none)                          -> rival-parsed-always-true ADDED by audit
#                                                               (definite-FALSE half)
#   AXIOM_TESTS (2)                 -> (none)                  DROPPED (G-AX)
#
# AUDIT REPAIR (rival-raised-escapes). The sibling's F2P rival is a
# definite-decision-instead-of-sentinel rewrite, because on the sibling's carrier
# the interpretation failure is already abstracted to a boolean flag and cannot be
# represented as a result at all. On THIS carrier the result type is
# `Except UnitError EqResult`, so the failure-propagates-to-the-caller outcome IS
# expressible — it is the `.error .parseError` leg, and it is exactly the impl the
# frozen prepatch file carries. As originally ported the battery mapped the
# sibling rival to `.ok .isFalse` only, so no case anywhere in it left the `.ok`
# half of the carrier and the spec's "never propagates the interpretation failure"
# clause — the clause the module docstring calls out by name — was never attacked.
# The error-leg rival is added; the `.ok .isFalse` rival is KEPT as a genuine
# second near-miss on the same branch (sentinel-vs-definite-decision, as opposed
# to sentinel-vs-error) and its prose corrected, since it is not the prepatch
# shape and must not claim to be.
#
# OMITTED (second-function cases): the sibling's other modeled function abstracts
# the base-class comparison, whose gold edit mapping.md documents as
# behaviour-PRESERVING for every F2P/P2P test and therefore NOT modeled as a
# separate Lean triple. The frozen Solution.lean declares exactly one
# spec/impl/proof triple and one marker region of each kind, so a second modeled
# behavior cannot be introduced by impl-region surgery — expressing those cases
# would require editing the FROZEN spec, which is out of scope for a G-PBT case.
# Omitting them is carrier narrowing, NOT a dropped attack — the single modeled
# obligation is fully defended and attacked.
# ADDED (rival-drop-kind-conjunct, rival-drop-name-conjunct,
# rival-parsed-always-true): the nagini `eq_unparsed_name` rivals collapse the
# whole definite decision to False (rival-unparsed-never-true) but do not attack
# the two conjuncts of the parsed decision individually. This backend's coverage
# requires every input binder to be varied by the reject witnesses; the `.parsed`
# constructor carries two sub-binders (`isUnrecognized`, `otherName`), so one
# rival is added per conjunct to demonstrate the spec's dependence on each. They
# attack real, load-bearing clauses of the SAME modeled spec. Note the asymmetry
# the audit established: only the name-conjunct rival has a REALIZABLE divergence
# point, so rival-parsed-always-true is added to give the kind conjunct a rival
# whose refutation point the real system can actually present.
# VACUOUS (frame/permission mutation; divergence/non-termination): the sibling's
# frame class is already vacuous on its value-typed boolean carrier; on this
# referentially transparent carrier it is doubly vacuous (no `mut` input, no
# aliasing, no read-only cell). Divergence is vacuous on lean because
# `implementation_*` is a total `def` over a finite inductive — a diverging impl
# cannot be written. No substitute probe is fabricated for either.
#
# POINT SPREAD. The seven reject witnesses probe seven DISTINCT input tuples, and
# the two RAISED-branch witnesses differ in the WRONG VALUE they refute (an
# escaping error vs a definite decision), not merely in the input literal. The
# last column records whether the refutation point is REALIZABLE in the real
# system (see the REACHABILITY CAVEAT in the module docstring) — i.e. whether the
# case's refinement may carry an F2P-resolution claim at all:
#   (selfName, po)               case                      branch / refuted value   reachable?
#     ("N", .raised)             rival-raised-escapes      RAISED, .error           yes (F2P shape)
#     ("A", .raised)             rival-raised-as-false     RAISED, .ok .isFalse     yes (F2P shape)
#     ("B", .parsed true "B")    rival-parsed-never-true   PARSED (equal-name)      yes (F2P shape)
#     ("C", .parsed false "m")   rival-always-defer        PARSED (recognised)      yes (F2P shape)
#     ("D", .parsed false "D")   rival-drop-kind-conjunct  PARSED (isUnrecognized)  NO — carrier-only
#     ("E", .parsed true "Z")    rival-drop-name-conjunct  PARSED (otherName)       yes (F2P shape)
#     ("FOO", .parsed false "m") rival-parsed-always-true  PARSED (definite-FALSE)  yes (F2P shape)
#   Across them selfName takes six distinct literals; po ranges over .raised and
#   .parsed; isUnrecognized ∈ {true,false}; otherName both matches and differs
#   from selfName — so no input binder is pinned to a single value. On the RESULT
#   side both halves of the `Except` carrier are exercised: six rivals are
#   refuted inside `.ok` and one on the `.error` leg.
#
# AUDIT REPAIR 2 (rival-parsed-always-true ADDED; rival-drop-kind-conjunct prose
# corrected). The battery's two conjunct-dropping rivals were presented as a
# symmetric pair, each attacking one sub-binder of the parsed decision, and BOTH
# claimed their faithful real counterpart would fail the F2P. That is true of the
# name-conjunct rival and FALSE of the kind-conjunct one: the latter diverges from
# gold only where a parsed operand is a RECOGNISED unit whose name equals this
# unit's name, which requires one string to be simultaneously un-interpretable
# (making this unit unrecognised under that name) and interpretable as a
# recognised unit — impossible, since interpretation is a function of the string.
# Its faithful counterpart is therefore observationally equivalent to gold on
# every reachable operand and WOULD resolve. So the `isUnrecognized` conjunct had
# no rival with a realizable divergence point, leaving the definite-FALSE half of
# the parsed branch attacked only vacuously. rival-parsed-always-true closes it:
# it drops the kind test in the reachable direction (a recognised operand wrongly
# reported equal) and is refuted at the literal F2P operand shape. The
# kind-conjunct case is KEPT — it is a real, machine-checked spec violation and a
# valid carrier-level probe of that binder — with its F2P claim withdrawn.
#
# INDEPENDENT AUDIT (second pass, real builds). Attack C: every rival's value was
# EVALUATED against the frozen impl at all six witness points (`#eval reprStr`);
# each differs from gold at exactly its own claimed point, so none is a mere
# reshape and no case is vacuous. Attack D: eight further wrong impls beyond the
# battery's own — raised-as-isTrue, inverted parsed decision, `||` for `&&`, name
# compared by length, the parsed branch on the error leg, an empty-name alias, a
# case-insensitive name test, and isFalse replaced by the sentinel — were each
# built with a deliberately GENEROUS proof script (so a failure is not merely the
# frozen tactic being brittle) and all eight were REJECTED; no spec hole. Attack
# E: four correct reshapes VERIFY — a fully non-monadic pure `match` using `cond`
# (no `Id.run do` at all, the shape furthest from frozen), a commuted conjunction,
# a Prop-level decidable name equality, and an explicit `Bool` match — so the spec
# is not shape-fitted and admits faithful reimplementations. The admissibility
# case was strengthened here: as ported it discharged the obligation at the
# F2P-shaped input but pinned no VALUE, so the two evaluating `have`s were added.
#
# INDEPENDENT AUDIT (third pass, real builds — this pass). Attack A: all cases'
# theorem statements and spec views re-diffed byte-for-byte against frozen; clean.
# Attack B: all six pre-existing witnesses rebuilt (rival exit 0 / gold exit 1,
# gold error `unsolved goals ⊢ False`). Attack B′ (forgery): the flipped claim was
# built on BOTH sides for every reject case — flipped-vs-gold exit 0 (clean) and
# flipped-vs-rival exit 1, the exact inverse of each witness's own pair, so every
# exit code tracks the CLAIM and no case is hollow. Attack C: all seven rivals
# `#eval`-compared against gold over a 36-point enumerated domain; each differs at
# its own claimed point, no two rivals coincide, none is a mere reshape. Attack D:
# twelve NEW wrong impls (parsed branch on the error leg, raised-as-isTrue,
# true/false swapped, `||` for `&&`, name-by-length, name-by-prefix,
# case-insensitive name, each definite leg replaced by the sentinel, a parsed
# branch ignoring `po` entirely, and one TUNED to be correct at all six existing
# witness points) were each built with a deliberately generous multi-tactic proof
# script and ALL TWELVE were rejected — no spec hole. Attack E: seven correct
# reshapes were tried and all seven verify (a fully non-monadic `cond` match with
# no `Id.run do`, a commuted conjunction, a Prop-level decidable equality, a
# `decide`-routed test, a local lambda, an explicit Bool match, and a guard-style
# early-return chain), so the spec is not shape-fitted. The guard-style one needed
# a per-branch `split`/`simp_all` script rather than the generous fallback chain —
# recorded because a hasty read of that first exit 1 would misreport a tactic gap
# as a soundness hole. Admissibility non-vacuity: all three of its ground claims
# were independently falsified and each falsification FAILS to build (exit 1), so
# none is a vacuously-provable restatement.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (the comparison rule is modeled deeply/structurally over ParseOutcome),
# so there is nothing to probe and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
