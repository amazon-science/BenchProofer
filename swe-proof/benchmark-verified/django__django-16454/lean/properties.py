"""properties.py — G-PBT falsification battery for django__django-16454 (lean).

NOT a Lean file; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — and, for the case that legitimately re-proves, inside
``-- proof-start`` / ``-- proof-end`` — is changed, so ``markers.same_spec``
holds and the single ``theorem correct_addSubparsers`` STATEMENT stays
byte-identical). ``expect:"verify"`` passes iff (in scope AND the file
elaborates with the obligation closed); ``expect:"reject"`` passes iff (in scope
AND it does NOT verify AND the case's refutation ``witness`` holds of the rival
while FAILING on the frozen solution).

PORT NOTE. This is a PORT of the nagini falsification battery
(``../nagini/properties.py``) onto this backend's carrier. The nagini bundle
models TWO functions with fractional-permission contracts — one that RECORDS the
propagation policy onto a mutable builder object, and one that CONSUMES that
recorded policy when materialising the nested parser. This Lean bundle collapses
both into the SINGLE purely-functional core: one total function over the two
observable inputs (the family test and the parent's flag) returning the flag the
constructed sub-parser ends up carrying. The record-then-consume split, and
every nagini case that attacks the seam between the two, therefore has no
counterpart here — the seam does not exist on this carrier. The per-case mapping
(ported / omitted, and why) is in the module ``assessment`` of the submission.

DEFENDED SURFACE (one modeled behavior, one obligation). The result is pinned to
the exact function of the two inputs, so the postcondition has two independent
top-level clauses selected by the family test:

  * SAME-FAMILY (``sameFamily = true``) — the outcome is ``some parentFlag``: a
    sub-parser is produced AND it carries EXACTLY the parent's flag value,
    verbatim, including the "unset" value. Two things are pinned here, and the
    rivals attack them separately: that a flag is carried at all (the OUTER
    ``some``), and WHICH value it is (the INNER payload).
  * FOREIGN (``sameFamily = false``) — the outcome is ``none``: the flag concept
    does not apply, and nothing whatsoever is carried.

The BEHAVIOURAL DISCRIMINATOR is that the carried value is the parent's ACTUAL
flag rather than any constant — in particular rather than the "unset" value a
freshly built sub-parser would otherwise hold. The partial-domain rivals below
are exactly that class of near-miss.

ADVERSARIAL READ of the case classes on this carrier:

  * FRAME / PERMISSION MUTATION — VACUOUS. The nagini battery devotes two cases
    to writes through a half-permission handle (a rival that overwrites the
    read-only parent field, and one that rewrites the builder's own recorded
    field). Lean is referentially transparent: inputs carry no heap permission,
    there is no read-only fraction to overwrite and no aliasing to exploit. Both
    cases have NO expressible instance here and no substitute is fabricated.

  * PLAIN-PATH GARBAGE WRITE — PORTED, but as a VALUE attack rather than a frame
    attack. Nagini needed two explicit frame clauses to stop a rival scribbling a
    style value on the path where no flag is injected. Here that hole cannot be
    left open by construction: the foreign arm is pinned to ``none``, a value, so
    "carried something anyway" is not a frame violation but a plain inequality.
    The two nagini garbage-write rivals port to ``weak-foreign-carries-unset``
    and ``weak-drop-family-guard``.

  * DIVERGENCE / NON-TERMINATION — genuinely VACUOUS here, and the nagini sibling
    carries no such case to port in any event (it has no ``diverge-*`` /
    ``nonterm-*`` / ``weak-diverge`` entry). On this backend
    ``implementation_addSubparsers`` is a total Lean ``def``, so a diverging
    implementation cannot be written at all. Note this disposition is NOT
    transferable to the velvet sibling, where under partial-correctness
    termination semantics a diverging rival satisfies every clause vacuously and
    the class is a KNOWN SPEC HOLE rather than a vacuous one (see
    ``the corpus-wide termination-semantics finding``).

  * UNGROUNDED-ORACLE ECHO — VACUOUS. The postcondition is fully GROUNDED: the
    result is pinned equal to a term built only from the two inputs. The bundle
    declares no ``opaque`` callee and consumes no ``axiom``, so there is no
    answer key an implementation could echo and no opaque term to condition a
    witness on. Every witness below is stated at literal inputs and closed by
    ``decide``; none binds a hypothesis, so none can be
    ``witness-inconsistent``.

  * PARTIAL-DOMAIN / VALUE — APPLIES, and carries all the adversarial pressure.
    Six rivals, each correct on part of the domain and wrong where the modeled
    behavior bites.

WITNESSES. On a tactic-proof backend "did not verify" is the DEFAULT outcome of
reshaping an implementation — the frozen ``cases … <;> rfl`` is tuned to the
frozen form — so a rejection alone attributes nothing to the spec. Every
``expect="reject"`` case therefore carries a Lean snippet stating the spec
predicate directly at one concrete input and refuting it. Each was checked by
real builds to HOLD of its rival and to FAIL on the frozen solution, and each
gold-side failure was read to confirm it is a genuine "the spec is satisfied
here" (``decide`` proving the negation false) rather than an unknown-name or
parse artifact.

BINDER / POINT SPREAD. The modeled input domain is FINITE and small: two
binders, ``sameFamily : Bool`` (2 values) and ``parentFlag : Option Bool``
(3 values) — six points in total. The six reject witnesses probe SIX DISTINCT
points, i.e. the ENTIRE domain, one rival per point:

  | witness point                  | rival                          |
  |--------------------------------|--------------------------------|
  | ``true``, ``some false``       | weak-carry-const-set           |
  | ``true``, ``some true``        | weak-carry-unset-default       |
  | ``true``, ``none``             | weak-collapse-unset-to-set     |
  | ``false``, ``none``            | weak-drop-family-guard         |
  | ``false``, ``some true``       | weak-foreign-carries-unset     |
  | ``false``, ``some false``      | weak-family-test-inverted      |

So no binder is held at a single value across the battery, and no rival is
refuted at a point another rival already used. Both halves of ``sameFamily`` and
all three values of ``parentFlag`` are exercised as refutation points, and each
of the two top-level clauses is attacked by three rivals. In particular the
``none`` ("unset") value of ``parentFlag`` is probed live rather than assumed
irrelevant: it is the value that most easily masks a wrong constant, so
``weak-collapse-unset-to-set`` exists specifically to occupy it.

AXIOM lane: EMPTY. The bundle declares no ``opaque`` callee and consumes no
``axiom`` (the family test is modeled DEEPLY as a boolean input, validated
against the real subclass relation by G-CONF, not axiomatized). The nagini
``AXIOM_TESTS`` was also empty; the axiom lane belongs to G-AX and this gate
ignores it, so it is dropped.
"""
from pathlib import Path

INSTANCE = "django__django-16454"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- region anchors (each unique inside Solution.lean; verified at load) ----
# Every anchor lies ENTIRELY inside the impl region, except _P_FROZEN which lies
# entirely inside the proof region, so same_spec stays byte-identical and the
# theorem STATEMENT is never touched.

# The whole impl body: default-then-conditionally-wire.
_I_BODY = (
    "  let mut carried : Option (Option Bool) := none\n"
    "  if sameFamily then\n"
    "    carried := some parentFlag\n"
    "  return carried"
)

# The family-test guard together with the wiring it governs.
_I_GUARD = (
    "  if sameFamily then\n"
    "    carried := some parentFlag"
)

# Just the wiring assignment (what value a same-family sub-parser receives).
_I_CARRY = "    carried := some parentFlag"

# The frozen proof body (proof region).
_P_FROZEN = (
    "  intro sameFamily parentFlag\n"
    "  unfold problem_spec_addSubparsers implementation_addSubparsers\n"
    "  cases sameFamily <;> rfl"
)


def _witness(same_family, parent_flag):
    """A refutation at one literal point of the (finite) input domain.

    States the spec predicate directly of the rival's own result and refutes it
    by evaluation. Binds nothing, so there are no hypotheses to be jointly
    unsatisfiable. Verified by real builds to elaborate against its rival and to
    FAIL on the frozen solution.
    """
    return (
        f"example : ¬ problem_spec_addSubparsers {same_family} {parent_flag}\n"
        f"    (implementation_addSubparsers {same_family} {parent_flag}) := by\n"
        "  unfold problem_spec_addSubparsers implementation_addSubparsers\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT
    # implementations that MUST verify. If a faithful correct implementation
    # cannot satisfy the frozen obligation, the spec is SPEC-TOO-STRONG. Each
    # keeps the theorem statement byte-identical and RE-PROVES honestly inside
    # the proof region where the reshape needs it; no case introduces a helper
    # lemma, an axiom, an assumption token, or a weakened obligation.
    #
    # Ports the two nagini positives (pos-open-branch-reorder,
    # pos-build-boolean-direct), whose reshapes were a branch reorder with an
    # unconditional default and a direct-from-boolean assignment. Both nagini
    # positives lived on the two SEPARATE functions; here they land as three
    # distinct reshapes of the one modeled core.
    # =====================================================================
    {
        "id": "pos-early-return",
        "kind": "soundness",
        "expect": "verify",
        # Drop the mutable accumulator entirely: answer each branch with a direct
        # early return. Same value on every input.
        "module": _swap(
            _BASE, _I_BODY,
            "  if sameFamily then\n"
            "    return some parentFlag\n"
            "  return none",
        ),
        "rationale": "a correct implementation that returns from each branch "
                     "directly, with no mutable accumulator, must still verify: "
                     "the postcondition pins the result BY VALUE, not by the "
                     "shape of the computation that produced it, and this "
                     "variant returns the same value at all six points of the "
                     "domain. Must verify, else SPEC-TOO-STRONG. The frozen "
                     "tactic body still closes it (the branch scrutinee is the "
                     "same, so `cases sameFamily <;> rfl` reduces both arms). "
                     "Ports nagini's branch-reorder positive.",
    },
    {
        "id": "pos-match-on-family",
        "kind": "soundness",
        "expect": "verify",
        # Functional shape: pattern-match the family test instead of an `if`.
        "module": _swap(
            _BASE, _I_BODY,
            "  match sameFamily with\n"
            "  | true  => return some parentFlag\n"
            "  | false => return none",
        ),
        "rationale": "a correct implementation that dispatches by pattern match "
                     "rather than by conditional must still verify — the "
                     "postcondition constrains the returned value, and the two "
                     "match arms deliver exactly the two clause values. Must "
                     "verify, else SPEC-TOO-STRONG. Defends the obligation with "
                     "a shape whose control flow differs from the frozen one "
                     "(match vs conditional) rather than only its value flow; "
                     "the frozen tactic body still closes it.",
    },
    {
        "id": "pos-inverted-default",
        "kind": "soundness",
        "expect": "verify",
        # Reverse the default/override polarity: seed the accumulator with the
        # same-family answer and overwrite it on the foreign path. This is the
        # mirror image of the frozen shape and the closest analogue of nagini's
        # unconditional-pre-set positive.
        "module": _swap(
            _BASE, _I_BODY,
            "  let mut carried : Option (Option Bool) := some parentFlag\n"
            "  if !sameFamily then\n"
            "    carried := none\n"
            "  return carried",
        ),
        "rationale": "a correct implementation that INVERTS the default/override "
                     "polarity — seeding the accumulator with the carrying "
                     "answer and clearing it on the non-applicable path — must "
                     "still verify; it agrees with the frozen result at all six "
                     "points. Must verify, else the spec is SPEC-TOO-STRONG "
                     "about which polarity the computation may use. This is the "
                     "strongest of the three positives: it moves the guard, the "
                     "seed AND the assignment at once, so it would catch a spec "
                     "that had accidentally been pinned to the frozen branch "
                     "structure. Ports nagini's unconditional-default reorder.",
    },

    # =====================================================================
    # ADMISSIBILITY — the frozen obligation carries NO precondition hypothesis
    # (the modeled behavior is TOTAL: `∀ sameFamily parentFlag`, unguarded), so
    # nagini's precondition-admission probe (admiss-open-self-call, which
    # established Requires from fresh constructors) has no binder to attack
    # here. The honest analogue is to show the obligation is SATISFIABLE — not
    # vacuously true — at the concrete recorded F2P-shaped input, by discharging
    # the spec predicate there by evaluation alongside the frozen obligation.
    # =====================================================================
    {
        "id": "admiss-ground-same-family-instance",
        "kind": "admissibility",
        "expect": "verify",
        # Discharge the spec predicate at the F2P-shaped point (a same-family
        # request under a set parent flag) by `rfl` as a `have`, then close the
        # frozen obligation verbatim. Nothing is assumed: no new declaration, no
        # assumption token, statement byte-identical, and the ground instance is
        # a `have` inside the existing tactic body.
        "module": _swap(
            _BASE, _P_FROZEN,
            "  have _ground : problem_spec_addSubparsers true (some true)\n"
            "      (implementation_addSubparsers true (some true)) := rfl\n"
            + _P_FROZEN,
        ),
        "rationale": "the obligation is discharged at the ground point the "
                     "recorded F2P scenario exercises — a same-family sub-parser "
                     "request under a parent whose flag is SET, which is the "
                     "configuration in which the concise-message behavior is "
                     "observable at all — and then the frozen obligation is "
                     "closed verbatim. Verifies, else the modeled behavior is "
                     "unsatisfiable at exactly the input the F2P exercises (the "
                     "analogue of PRECOND-TOO-STRONG on a spec whose ∀ is "
                     "unguarded). Nothing is assumed and the theorem statement "
                     "is byte-identical. Ports nagini's admissibility probe.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong implementations sharing the
    # frozen spec that MUST be rejected. Each carries (a) the refinement
    # argument that its faithful real patch would NOT resolve, so a verifying
    # rival would be a true verify-does-not-imply-resolve break rather than an
    # artifact, and (b) a refutation witness pinning the violation at one
    # concrete input, seen to discriminate by real builds.
    #
    # ---- ATTACKING CLAUSE 1: the same-family carried VALUE ----
    # Three rivals that produce a sub-parser carrying the WRONG value. Each
    # occupies its own value of parentFlag, because a constant is invisible at
    # the point where it happens to coincide with the parent's flag.
    # =====================================================================
    {
        "id": "weak-carry-const-set",
        "kind": "uniqueness",
        "expect": "reject",
        # Carry the constant "set" value instead of the parent's actual flag.
        # Correct exactly on the sub-domain where the parent's flag IS that
        # constant; wrong on the other two values.
        "module": _swap(_BASE, _I_CARRY, "    carried := some (some true)"),
        "refinement": "a faithful real patch that wired the constant 'set' value "
                      "into every same-family sub-parser, rather than the "
                      "parent's own value, would force the human-facing "
                      "reporting style onto sub-commands of a parent that was "
                      "invoked PROGRAMMATICALLY and had the flag unset or "
                      "cleared. In that regime the parent deliberately surfaces "
                      "an argument error as a raised exception so a caller can "
                      "catch it; the rival would instead print a usage message "
                      "and terminate, breaking the programmatic-invocation "
                      "behavior the recorded P2P scenarios rely on. It also "
                      "makes the sub-parser's behavior independent of the "
                      "parent, which is the opposite of the required "
                      "consistency at every nesting level. So the faithful "
                      "patch does NOT resolve.",
        "rationale": "REJECT from the same-family clause: the spec pins the "
                     "result to `some parentFlag`, and at a parent flag of "
                     "`some false` the rival yields `some (some true)`, so the "
                     "carried value — hence `result` — differs. Attacks the "
                     "INNER payload while leaving the outer branch correct, so "
                     "it is refutable only by a witness that moves parentFlag "
                     "off the rival's constant; the witness sits at "
                     "`some false`, the value no other rival is refuted at.",
        "witness": _witness("true", "(some false)"),
    },
    {
        "id": "weak-carry-unset-default",
        "kind": "uniqueness",
        "expect": "reject",
        # Produce a sub-parser, but carrying the "unset" default rather than the
        # parent's value: the pre-existing defect this instance is about.
        # Correct exactly when the parent's flag is itself unset.
        "module": _swap(_BASE, _I_CARRY, "    carried := some none"),
        "refinement": "this is precisely the pre-existing behavior the instance "
                      "targets: a same-family sub-parser is constructed without "
                      "the parent's flag being wired through, so it holds the "
                      "unset default. Under it an invalid argument to a nested "
                      "sub-command surfaces as a raised exception with a "
                      "traceback instead of the concise usage message, which is "
                      "the exact symptom the recorded F2P scenario asserts "
                      "against (it requires a two-line stderr whose second line "
                      "is the concise message). A faithful patch of this rival "
                      "changes nothing observable and does NOT resolve — it is "
                      "the unfixed state.",
        "rationale": "REJECT from the same-family clause: the spec pins the "
                     "result to `some parentFlag` and the rival yields "
                     "`some none` regardless, so at a parent flag of "
                     "`some true` the carried value differs. This is the "
                     "load-bearing rival of the battery — the one whose "
                     "verification would mean the spec admits the unfixed "
                     "behavior outright. Its witness sits at `some true`, "
                     "distinct from the other two value-clause rivals, because "
                     "a rival carrying the unset default is invisible at an "
                     "unset parent flag.",
        "witness": _witness("true", "(some true)"),
    },
    {
        "id": "weak-collapse-unset-to-set",
        "kind": "uniqueness",
        "expect": "reject",
        # The subtlest near-miss: propagate the parent's flag faithfully whenever
        # it is SET, but collapse the "unset" value to a concrete one. Wrong at
        # exactly ONE of the six domain points.
        "module": _swap(
            _BASE, _I_CARRY,
            "    carried := some (some (parentFlag.getD false))",
        ),
        "refinement": "a faithful real patch that normalised the parent's unset "
                      "flag to a concrete value before wiring it through would "
                      "replace 'no preference recorded' with an explicit "
                      "setting on every sub-parser. The distinction is "
                      "load-bearing downstream: the unset value is the default a "
                      "parser holds when nothing has declared how errors should "
                      "be reported, and the reporting branch tests the flag for "
                      "truthiness — so substituting a concrete value both "
                      "changes what a later reader of that attribute observes "
                      "and makes the sub-parser claim a policy its parent never "
                      "set. That is a spurious normalisation absent from the "
                      "real change, so the faithful patch does NOT resolve.",
        "rationale": "REJECT from the same-family clause, at the NARROWEST "
                     "sub-domain any rival here attacks: this rival agrees with "
                     "the spec at five of the six domain points and diverges "
                     "ONLY when the parent's flag is unset, where the spec "
                     "demands `some none` and the rival yields "
                     "`some (some false)`. It is deliberately a near-miss of "
                     "weak-carry-unset-default and weak-carry-const-set, so it "
                     "gets its OWN witness at the single point that "
                     "distinguishes it (`none`) rather than sharing theirs — "
                     "otherwise the sub-domain its rationale claims would never "
                     "be demonstrated. This is the rival that proves the battery "
                     "pins the unset value rather than merely pinning 'some "
                     "boolean gets carried'.",
        "witness": _witness("true", "none"),
    },

    # =====================================================================
    # ---- ATTACKING CLAUSE 2: the foreign branch (nothing is carried) ----
    # Three rivals that produce a carried flag for a request to which the flag
    # concept does not apply, or that decide applicability wrongly. These port
    # nagini's two plain-path garbage-write rivals and its decision-inversion
    # rivals; here the foreign arm is pinned to a VALUE, so the attack is an
    # inequality rather than a frame violation.
    # =====================================================================
    {
        "id": "weak-drop-family-guard",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the applicability test: carry the parent's flag unconditionally.
        # Correct exactly on the same-family sub-domain.
        "module": _swap(_BASE, _I_GUARD, "  carried := some parentFlag"),
        "refinement": "a faithful real patch that dropped the family test and "
                      "wired the flag into EVERY requested sub-parser would pass "
                      "the extra construction keyword to a foreign parser class "
                      "that does not accept it — a hard construction failure for "
                      "the foreign case rather than a wrong message. The "
                      "recorded regression scenario builds a sub-parser from a "
                      "foreign class precisely to guard that path and asserts it "
                      "still reports its own two-line error, so the faithful "
                      "patch does NOT resolve; it converts a working path into a "
                      "crashing one.",
        "rationale": "REJECT from the foreign clause: the spec pins the result to "
                     "`none` when the family test is false, and the rival yields "
                     "`some parentFlag` there, so at an unset parent flag it "
                     "yields `some none` where the spec demands `none`. Attacks "
                     "the OUTER branch decision (whether anything is carried at "
                     "all) rather than the payload. Witness at "
                     "`(false, none)` — the only rival refuted at that point, "
                     "and it demonstrates that the foreign arm is pinned even "
                     "when the parent has no flag value to leak.",
        "witness": _witness("false", "none"),
    },
    {
        "id": "weak-foreign-carries-unset",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep the same-family behavior exactly right, but have the foreign path
        # ALSO record something — the unset value. The garbage-write class:
        # wrong only on the foreign arm, and invisible to any witness that only
        # probes same-family inputs.
        "module": _swap(
            _BASE, _I_GUARD,
            "  if sameFamily then\n"
            "    carried := some parentFlag\n"
            "  else\n"
            "    carried := some none",
        ),
        "refinement": "a faithful real patch that additionally recorded an "
                      "'unset' flag against a foreign sub-parser would attach a "
                      "concept that does not belong to it — the foreign class "
                      "has no such attribute and the real change leaves that "
                      "path entirely untouched. Setting one anyway is a "
                      "spurious side-effect absent from the real change, and it "
                      "misrepresents the foreign path that the recorded "
                      "regression scenario checks. So the faithful patch does "
                      "NOT resolve.",
        "rationale": "REJECT from the foreign clause, and this is the rival the "
                     "clause EXISTS for: the same-family arm is left verbatim "
                     "correct, so the rival is indistinguishable from gold on "
                     "half the domain and is caught only because the spec pins "
                     "the foreign outcome to `none` instead of leaving it free. "
                     "It ports nagini's plain-path garbage-write rivals, which "
                     "there needed two explicit frame clauses to catch; here the "
                     "pinned value does the work. Witness at "
                     "`(false, some true)`, a point no other rival uses, chosen "
                     "so the parent DOES have a flag value — showing the foreign "
                     "arm is pinned independently of what the parent holds.",
        "witness": _witness("false", "(some true)"),
    },
    {
        "id": "weak-family-test-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # Invert the applicability decision: carry the flag exactly when it does
        # NOT apply. Wrong at every point of the domain, and refuted at the one
        # point no other rival occupies.
        "module": _swap(
            _BASE, _I_GUARD,
            "  if !sameFamily then\n"
            "    carried := some parentFlag",
        ),
        "refinement": "a faithful real patch that inverted the applicability "
                      "test would pass the extra construction keyword to exactly "
                      "the foreign classes that cannot accept it while withholding "
                      "it from the same-family sub-parsers that need it — "
                      "simultaneously crashing the path the recorded regression "
                      "scenario guards and leaving the reported defect unfixed on "
                      "the path the recorded F2P scenario asserts. It fails both "
                      "directions at once, so the faithful patch does NOT "
                      "resolve.",
        "rationale": "REJECT from BOTH top-level clauses: the rival's branch "
                     "decision is the complement of the spec's, so it is wrong "
                     "at every one of the six domain points. Included as the "
                     "decision-inversion port of nagini's always-inject rivals, "
                     "and refuted at `(false, some false)` — the sixth and final "
                     "domain point, which no other rival's witness occupies. "
                     "With this case the six reject witnesses together probe the "
                     "ENTIRE modeled input domain, so no binder value is left "
                     "undemonstrated.",
        "witness": _witness("false", "(some false)"),
    },
]

# No AXIOM lane here: the bundle declares no `opaque` callee and consumes no
# `axiom` (the family test is modeled deeply as a boolean input and validated
# against the real subclass relation by G-CONF). The nagini AXIOM_TESTS was also
# empty; dropped, since the axiom lane is G-AX's job and this gate ignores it.
AXIOM_TESTS = []
