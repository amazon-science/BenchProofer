"""properties.py — G-PBT falsification battery for django__django-12304 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct`` obligation survives with a byte-identical statement) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
frozen solution).

DEFENDED SURFACE (one contracted method over a two-observation class carrier).
The final publishing step of building an enumerated-choices class produces the
published class from the already-assembled one:

  publishChoicesClass (built : ChoicesClass) return (out : ChoicesClass)
    ensures out.doNotCallInTemplates = true          -- (C1) THE patch clause
    ensures out.valueToLabel = built.valueToLabel     -- (C2) frame/preservation

There is NO opaque answer key to echo (directive 8): (C2) grounds the rest of
the published state in an actual method input, and (C1) pins the one boolean the
template engine reads to decide whether a callable class is auto-invoked during
variable resolution. The two clauses together pin the whole behaviour the issue
demands — the flag is set so the class is usable as a plain value, AND the rest
of the construction (the value→label association behind member-attribute reads)
survives unchanged, so a class that set the flag but clobbered the map would
still fail the read-back tests.

BINDER STRUCTURE (read this before judging binder coverage). The method has ONE
input binder, ``built``, a record with two observed fields:

  * ``built.valueToLabel`` — the value→label association. (C2) is a function of
    exactly this field: the published map must equal it. A rival that alters the
    map (drops it, reorders it, substitutes it) is caught by (C2) whenever the
    input map is non-empty / non-palindromic.
  * ``built.doNotCallInTemplates`` — the flag the class ARRIVES with. (C1) is a
    CONSTANT (``= true``) and so does not name any input; but a pass-through
    rival that returns the flag it arrived with (rather than forcing ``true``)
    is correct exactly when ``built.doNotCallInTemplates`` already happens to be
    ``true`` and wrong otherwise, so a discriminating witness for it must hold
    that field at ``false``. This is why the witness set varies that field too
    (the ``omit-flag`` rival is a partial-domain rival keyed on it).

ADVERSARIAL READ of the nagini classes on this carrier:
  * DEFINITIONAL-EQUALITY TRAP (why the positives are shaped as they are). On a
    two-field record the obvious "different shape" reshapes are not different
    terms at all: a from-scratch construction, a record update, and a
    `let`-bound flag literal all reduce to the SAME term, and the equation
    between each of them and the frozen body closes by `with_reducible rfl`
    (measured with real builds). A positive of that family verifies whatever the
    obligation says, so it cannot detect SPEC-TOO-STRONG. The load-bearing
    positive here is therefore `pos-branch-on-arriving-flag`, which branches on
    the flag the class arrives with — NOT definitionally equal to the frozen
    body (`rfl` fails on that equation, measured), so the proof must actually
    perform the case analysis. The cheap from-scratch reshape is kept beside it
    as a control, labelled as such rather than as an independent test.
  * FRAME-MUTATION (permission overwrite) — VACUOUS. The nagini sibling carries
    this because its inputs are held at a fractional heap permission
    (``Acc(.,1/2)``) an impl can illegally overwrite. Lean/Velvet are
    referentially transparent: ``built`` is an immutable value, there is no
    ``mut`` binder, no heap and no aliasing — so there is no read-only field to
    mutate and no substitute probe to build. Per the porting map this class is
    vacuous here; NOT fabricated. Note the preservation clause (C2) is the Lean
    analogue of directive 5's frame obligation (the publish step reads ``built``
    without disturbing it), and IS attacked below by value rivals.
  * UNGROUNDED-ORACLE ECHO — N/A. The bundle declares NO ``axiom`` (the publish
    step's effect is modeled directly); the post-image of (C2) is a method
    input, not an axiomatized oracle.

WITNESS PLACEMENT. Each reject rival is refuted at a concrete ``built`` chosen so
the five points together move ``built.valueToLabel`` across the empty boundary,
two distinct singletons, a two-element list (where order matters), and a
singleton keyed away from a rival's hardcoded constant, and move
``built.doNotCallInTemplates`` across ``{false, true}``. No two rivals are
refuted at the same input.

WITNESS DISCRIMINATION IS BY EVALUATION, and that is what makes the gold-side
exit code informative here. This carrier is a plain record over ``Bool`` and
``List (Int × List Char)`` and the frozen impl is a single loop-free record
update, so the extracted tester REDUCES: each witness fails on the frozen
solution with ``Tactic `decide` proved that the proposition … = false is
false``, i.e. the kernel evaluated the tester to ``true`` there. Re-derived
under audit: for all five reject cases the FLIPPED claim (``= true`` instead of
``= false``, asserting gold is correct at that point) BUILDS against the frozen
solution (exit 0) and FAILS against the rival (exit 1) — the exact mirror of the
shipped witness. So the gold-side verdict tracks the claim rather than being a
fixed tactic failure, and none of these cases is of the hollow
stuck-reduction/forgery family. Each witness reaches the ``method`` contract through
Velvet's own tester machinery (``publishChoicesClassTester built = false`` says
the extracted program's result violates the postcondition at that input) and is
checked in a file whose ``prove_correct`` block has been stripped, so no tactic
script can mask the verdict. There are no ``require`` clauses, so every input
reaches the postcondition. Each witness was verified out-of-band with two real
builds: it ELABORATES against the rival and FAILS against the frozen solution.

AXIOM lane: EMPTY (the bundle declares no ``axiom``; the publish step is modeled
directly, not delegated to an oracle). The gate ignores ``AXIOM_TESTS``
regardless. Nagini→velvet accounting is at the bottom of the file.
"""
from pathlib import Path

INSTANCE = "django__django-12304"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. Lies wholly inside the single impl region and is
# ---- unique in Solution.lean (both facts asserted at load by _swap). ----
_IMPL = "    return { built with doNotCallInTemplates := true }"


_PROOF = "prove_correct publishChoicesClass by\n  loom_solve"


def _with_impl(new_impl: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched).

    Positive reshapes keep the frozen `prove_correct publishChoicesClass by
    loom_solve` script verbatim (verified out-of-band with real builds); each
    reject rival is judged by its witness, not by whether the frozen script
    happens to break on the reshaped impl.
    """
    return _swap(_BASE, _IMPL, new_impl)


def _with_impl_reproved(new_impl: str, new_proof: str) -> str:
    """Impl body replaced AND the `prove_correct` tactic body retuned.

    Both regions are elided from the consumer spec view, so `markers.same_spec`
    still holds and the obligation statement stays byte-identical. Used only by
    the admissibility case, whose in-region `assert` adds a goal the frozen
    one-line script does not discharge.
    """
    return _swap(_with_impl(new_impl), _PROOF, new_proof)


# ---- ADMISSIBILITY point. A concrete arriving class whose flag is FALSE (the
# ---- state an arbitrary callable class arrives in) carrying a one-entry
# ---- value->label association. Used by the admissibility case below to show the
# ---- obligation is satisfiable AT that point rather than only in general.
_ADM_MAP = "[(1, ['L', 'b', 'l'])]"
_ADM_IN = ("{ doNotCallInTemplates := false, valueToLabel := " + _ADM_MAP + " }")
_ADM_OUT = ("({ (" + _ADM_IN + " : ChoicesClass) with doNotCallInTemplates := true })")


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery. ChoicesClass is
# ---- a concrete record (a Bool and a List (Int × List Char)), so `decide`
# ---- settles every equality at a concrete input. ----
_TESTER = (
    "extract_program_for publishChoicesClass\n"
    "prove_precondition_decidable_for publishChoicesClass\n"
    "prove_postcondition_decidable_for publishChoicesClass\n"
    "derive_tester_for publishChoicesClass\n\n"
)


def _witness(call: str) -> str:
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — a structurally different but CORRECT
    # impl that MUST verify, else SPEC-TOO-STRONG. Instead of a record update
    # on `built`, construct the published class DIRECTLY with the flag literal
    # and the preserved map. Both clauses hold by construction; the frozen
    # `loom_solve` script closes the byte-identical obligation (verified with a
    # real build).
    # =====================================================================
    {
        "id": "pos-direct-construct",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(
            "    return { doNotCallInTemplates := true, valueToLabel := built.valueToLabel }"),
        "rationale": "CONTROL positive (cheap by construction, kept as such): "
                     "build the published record from scratch with the flag set to "
                     "the literal `true` and `valueToLabel` copied from the input, "
                     "rather than a record update. (C1) holds (flag literal) and "
                     "(C2) holds (map copied), so it MUST verify. Note this reshape "
                     "is definitionally EQUAL to the frozen body on a two-field "
                     "record — the equation closes by `with_reducible rfl` "
                     "(measured) — so it cannot by itself detect SPEC-TOO-STRONG; "
                     "the load-bearing soundness probe is "
                     "`pos-branch-on-arriving-flag`, which is not defeq.",
    },

    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — a reshape that is NOT definitionally
    # equal to the frozen impl, so `loom_solve` has to do real work on it rather
    # than close a syntactically-different spelling of the same term.
    #
    # The two record-shaped reshapes above and below are cheap by construction:
    # `{ built with doNotCallInTemplates := true }`, the from-scratch
    # construction, and a `let`-bound flag all reduce to the SAME term
    # (`with_reducible rfl` closes both equations — measured), so a positive of
    # that family passes even if the obligation were far weaker. This one
    # branches on the flag the class ARRIVES with and returns `built` untouched
    # on the true branch, which is a genuinely different term on that branch
    # (`rfl` does NOT close it against the frozen body — measured); (C1) then
    # holds only because the branch guard says the arriving flag was already
    # true, and (C2) holds because neither branch touches the map. So this
    # positive exercises case analysis in the proof, and a spec/proof too
    # fragile to follow the guard would reject it => SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-branch-on-arriving-flag",
        "kind": "soundness",
        "expect": "verify",
        "module": _with_impl(
            "    if built.doNotCallInTemplates then\n"
            "      return built\n"
            "    else\n"
            "      return { built with doNotCallInTemplates := true }"),
        "rationale": "CORRECT reshape that is NOT definitionally equal to the "
                     "frozen impl: it branches on the flag the class arrives with "
                     "and republishes `built` unchanged when that flag is already "
                     "true, forcing the flag only on the other branch. Both "
                     "clauses still hold at every input — (C1) because the true "
                     "branch is guarded by the flag already being true and the "
                     "false branch sets it, (C2) because neither branch touches "
                     "the map — but the equation to the frozen body does NOT hold "
                     "by `rfl` (measured), so `loom_solve` must do the case "
                     "analysis. MUST verify, else SPEC-TOO-STRONG (proof "
                     "fragility). This is the positive that would catch a "
                     "one-shape-only proof; the from-scratch reshape below is "
                     "kept as the cheap control alongside it.",
    },

    # =====================================================================
    # ADMISSIBILITY (PRECOND-TOO-STRONG lane). The method declares no `require`,
    # so the analogue of "the precondition admits a normal input" on this total
    # carrier is: the OBLIGATION is jointly satisfiable at a concrete
    # F2P-SHAPED point, not merely in general. The residual risk the other
    # lanes cannot reach is a pair of clauses that is unsatisfiable exactly
    # where it matters — (C1) demanding one flag value while (C2) forces a state
    # that fixes it to the other — which would make every positive above verify
    # vacuously and no reject case notice.
    #
    # The in-region `assert` discharges both clauses AT the concrete point where
    # the fix has to bite: a class ARRIVING with the flag false (the state an
    # arbitrary callable class is in) that already carries a non-empty
    # value->label association. It checks, by evaluation, that (a) the arriving
    # flag really is false there — so the point is one where the step must
    # CHANGE something, not one where the postcondition holds already; (b) (C1)
    # holds of the published class at that point; and (c) (C2) holds there, with
    # the arriving association reproduced entry-for-entry. The impl is kept
    # verbatim so the method's own obligation still discharges; only the elided
    # tactic body gains `all_goals decide` to clear the extra assert goal.
    #
    # The assert is LIVE, not decoration: the same case with the flag claim
    # flipped to `false` fails (`decide` proved `true = false` is false), and
    # with the map claim weakened to `[]` it fails too (`decide` proved
    # `[(1, ['L','b','l'])] = []` is false) — both measured with real builds.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-point",
        "kind": "admissibility",
        "expect": "verify",
        "module": _with_impl_reproved(
            "    assert (with_name_prefix `admiss\n"
            f"      ((({_ADM_IN} : ChoicesClass).doNotCallInTemplates = false) ∧\n"
            f"       ({_ADM_OUT}.doNotCallInTemplates = true) ∧\n"
            f"       ({_ADM_OUT}.valueToLabel = {_ADM_MAP})))\n"
            + _IMPL,
            "prove_correct publishChoicesClass by\n"
            "  loom_solve\n"
            "  all_goals decide"),
        "rationale": "ADMISSIBILITY: both clauses are jointly satisfiable at a "
                     "concrete F2P-shaped point — a class arriving with the flag "
                     "FALSE (asserted, so the point is one where the step must "
                     "actually change the flag rather than one where (C1) already "
                     "holds) and carrying a non-empty value->label association. "
                     "The assert discharges (C1) and (C2) there by evaluation "
                     "before the frozen obligation closes, so the obligation is "
                     "neither unsatisfiable at the input that matters nor a "
                     "degenerate collapse. If this cannot verify the clause pair "
                     "is contradictory exactly where the behaviour is demanded => "
                     "PRECOND-TOO-STRONG, and every soundness positive above "
                     "would have been passing vacuously.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at
    # a concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "omit-flag",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch behaviour: publish `built` unchanged, never forcing the
        # flag. Correct iff the class already arrived with the flag true; wrong
        # otherwise. Attacks (C1).
        "module": _with_impl("    return built"),
        "refinement": "its faithful real patch is the empty diff — do not add the "
                      "line that sets the flag on the published class = the "
                      "pre-patch source. An arbitrary callable class then carries "
                      "no such flag (the getattr default is falsey), so the "
                      "template engine auto-invokes the class with no arguments; "
                      "that call fails its required argument and the variable "
                      "resolves to the invalid-value string. The F2P template "
                      "renders the empty string instead of the expected "
                      "label|value and the test FAILS — it would NOT resolve.",
        "rationale": "REJECT from (C1) `out.doNotCallInTemplates = true`: the rival "
                     "passes the input flag straight through, so it violates (C1) "
                     "whenever `built.doNotCallInTemplates` is false. Refuted at "
                     "`built.doNotCallInTemplates = false` (with an empty map). A "
                     "partial-domain rival keyed on the input flag field — its "
                     "witness MUST hold that field at false, which the others do "
                     "not.",
        "witness": _witness(
            "publishChoicesClassTester { doNotCallInTemplates := false, valueToLabel := [] }"),
    },
    {
        "id": "flag-false",
        "kind": "uniqueness",
        "expect": "reject",
        # Force the flag to the WRONG literal. Attacks (C1) unconditionally.
        "module": _with_impl(
            "    return { built with doNotCallInTemplates := false }"),
        "refinement": "its faithful real patch sets the published class's flag to "
                      "the wrong literal (false). The engine reads it as falsey and "
                      "auto-invokes the callable class, whose no-argument call "
                      "fails, so the variable resolves to the invalid-value string; "
                      "the F2P template renders the empty string and the test "
                      "FAILS — it would NOT resolve.",
        "rationale": "REJECT from (C1): the rival publishes the flag as `false`, "
                     "which contradicts `out.doNotCallInTemplates = true` at every "
                     "input. Refuted at a non-empty singleton map with the input "
                     "flag already true — showing the violation is in (C1) and not "
                     "a coincidence of the map or the arriving flag.",
        "witness": _witness(
            "publishChoicesClassTester { doNotCallInTemplates := true, valueToLabel := [(1, ['A'])] }"),
    },
    {
        "id": "clobber-map",
        "kind": "uniqueness",
        "expect": "reject",
        # Sets the flag correctly but DISCARDS the value→label association.
        # Attacks (C2), the preservation/frame clause. Correct on (C1).
        "module": _with_impl(
            "    return { doNotCallInTemplates := true, valueToLabel := [] }"),
        "refinement": "its faithful real patch sets the flag but overwrites the "
                      "already-assembled value→label association with an empty one. "
                      "The template engine no longer auto-calls the class, but "
                      "member-attribute reads (`.label`, `.value`) that depend on "
                      "that association now find nothing, so the F2P template "
                      "renders the wrong text and the test FAILS — it would NOT "
                      "resolve. (This is the directive-5 frame violation: setting "
                      "the flag while disturbing the rest of the construction.)",
        "rationale": "REJECT from (C2) `out.valueToLabel = built.valueToLabel`: the "
                     "rival publishes an empty map regardless of the input, "
                     "differing from `built.valueToLabel` whenever the input map is "
                     "non-empty. Refuted at a non-empty singleton map (flag already "
                     "true, so only (C2) fires). Discrimination comes from "
                     "`built.valueToLabel` being non-empty.",
        "witness": _witness(
            "publishChoicesClassTester { doNotCallInTemplates := true, valueToLabel := [(7, ['Z'])] }"),
    },
    {
        "id": "reorder-map",
        "kind": "uniqueness",
        "expect": "reject",
        # Near-miss: right elements, wrong ORDER. Reverses the association while
        # forcing the flag to the CORRECT literal, so the only clause it can
        # violate is (C2). Attacks (C2) with a rival the clobber-map rival (wrong
        # CONTENT) does not subsume.
        #
        # The flag is written explicitly here rather than left to `built with`:
        # a `{ built with valueToLabel := ... }` body inherits the ARRIVING flag
        # and so also violates (C1) wherever that flag is false, which makes the
        # rival wrong for two reasons at once and lets its witness be satisfied
        # by the (C1) failure the omit-flag rival already covers. Forcing
        # `doNotCallInTemplates := true` makes (C2) the sole possible cause, and
        # the witness point below holds the arriving flag at true so (C1) is
        # satisfied there by either spelling — the refutation is order alone.
        "module": _with_impl(
            "    return { doNotCallInTemplates := true, "
            "valueToLabel := built.valueToLabel.reverse }"),
        "refinement": "its faithful real patch sets the flag but publishes the "
                      "value→label association in a DIFFERENT order than assembled. "
                      "The association is order-significant (it backs member "
                      "iteration and label lookup), so downstream reads that depend "
                      "on the assembled order observe the wrong pairing and the F2P "
                      "read-back FAILS — it would NOT resolve.",
        "rationale": "REJECT from (C2): the rival reverses `built.valueToLabel`, "
                     "which equals the original only when the list is a palindrome "
                     "(e.g. empty or singleton). Refuted at a two-element map where "
                     "the reverse differs — a near-miss (right content, wrong "
                     "order) that the clobber-map rival (wrong content) does not "
                     "subsume, exercising the ORDER dependence of (C2).",
        "witness": _witness(
            "publishChoicesClassTester { doNotCallInTemplates := true, "
            "valueToLabel := [(1, ['A']), (2, ['B'])] }"),
    },
    {
        "id": "partial-fixed-map",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN rival, the class the four rivals above leave
        # unattacked. Every one of them is wrong on a WHOLE clause at (nearly)
        # every input; this one is CORRECT at one concrete point and wrong
        # everywhere else, which is the shape a spec that only pins behaviour at
        # the demonstrated input would admit. It sets the flag correctly and
        # publishes a HARDCODED one-entry association instead of the one the
        # class arrived with, so it satisfies (C1) always and (C2) exactly when
        # the arriving map happens to be that literal.
        #
        # Confirmed partial rather than uniformly wrong with a real build: the
        # tester evaluates to TRUE at the hardcoded point (so the rival really
        # does satisfy the whole obligation somewhere — it is not just another
        # clobber-map) and to FALSE at the witness point below.
        "module": _with_impl(
            "    return { doNotCallInTemplates := true, "
            f"valueToLabel := {_ADM_MAP} }}"),
        "refinement": "its faithful real patch sets the flag but replaces the "
                      "already-assembled value->label association with a fixed "
                      "literal one belonging to some other enumeration. The engine "
                      "no longer auto-calls the class, so the flag half of the "
                      "behaviour looks fixed, but every member-attribute read "
                      "(`.label`) now resolves against an association that does "
                      "not describe THIS class: any enumeration whose members "
                      "differ from that literal renders the wrong label and the "
                      "F2P read-back FAILS — it would NOT resolve. It would pass "
                      "only for the single enumeration whose association happens "
                      "to be the hardcoded one.",
        "rationale": "REJECT from (C2), as a PARTIAL-DOMAIN rival rather than a "
                     "whole-clause violation: the published map is a constant, so "
                     "(C2) holds at exactly the inputs whose arriving map IS that "
                     "constant and fails at every other. This is the class none of "
                     "the four rivals above covers — they are wrong almost "
                     "everywhere, so a spec that pinned the behaviour only at a "
                     "demonstrated point would still reject them while admitting "
                     "this one. Refuted at a two-key-away arriving map (flag "
                     "already true, so only (C2) can fire) at a FIFTH distinct "
                     "witness point.",
        "witness": _witness(
            "publishChoicesClassTester { doNotCallInTemplates := false, "
            "valueToLabel := [(2, ['O', 't', 'h'])] }"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 6 SPEC cases (2 soundness
# positives, 1 admissibility, 3 uniqueness rivals) plus a 4-case AXIOM lane.
# This bundle models a NARROWER surface: nagini contracts one function over a
# PRIMITIVE `identity: int` with an @Pure axiom oracle `resolved_in_template` and
# a construction axiom `base_class_creation`, whereas velvet models the publish
# step DIRECTLY over the two-observation class carrier (`ChoicesClass`) with NO
# axiom. The behavioural clauses E4/E5 (resolved_in_template == identity) and the
# identity clause E2 (Result().identity == identity) have no counterpart here:
# identity is not a modeled observation (the mapping folds the "class object" to
# just its flag and its value→label map, §2), and there is no oracle to satisfy.
# What velvet DOES model is (C1) the flag and (C2) the preservation of the rest
# of the construction.
#
#   sibling case                 -> here
#   ---------------------------------------------------------------------
#   pos-direct-construct         -> pos-direct-construct        PORTED (control)
#   pos-local-flag               -> pos-branch-on-arriving-flag REPLACED (defeq)
#   admiss-f2p-diamond           -> admiss-f2p-shaped-point     PORTED
#   weak-omit-flag               -> omit-flag                   PORTED
#   weak-flag-false              -> flag-false                  PORTED
#   partial-fixed-identity       -> partial-fixed-map           PORTED (re-aimed)
#   weak-wrong-identity-obj      -> (none)                      NO CARRIER (identity)
#   (no sibling)                 -> clobber-map / reorder-map   NEW (C2 attacks)
#   AXIOM_TESTS (4)              -> (none)                      DROPPED (G-AX)
#
# PORTED (positives): direct-construct builds the published record from scratch.
#   It verifies under the frozen `loom_solve`, but it is definitionally EQUAL to
#   the frozen body on this two-field record (`with_reducible rfl` closes the
#   equation — measured), so it is retained as a control and not counted as an
#   independent SPEC-TOO-STRONG probe.
# REPLACED (positive 2): the sibling's `pos-local-flag` ports mechanically, and a
#   `let flag : Bool := true` reshape does verify — but it reduces to the frozen
#   term as well (`with_reducible rfl` closes it, measured), so the battery's two
#   positives were the same test twice and neither could fail. It is replaced by
#   `pos-branch-on-arriving-flag`, a correct reshape that is NOT defeq to the
#   frozen body (`rfl` fails on the equation, measured) and so makes the proof do
#   real case analysis. Verified with a real build under the frozen script.
# PORTED (E3/flag rivals): weak-omit-flag ports as `omit-flag` (publish `built`
#   unchanged — the pre-patch skeleton) and weak-flag-false ports as `flag-false`
#   (force the wrong literal). Both attack (C1).
# PORTED (admissibility) — the earlier accounting recorded this lane VACUOUS on
#   the ground that the bundle declares no `require`, so "there is no
#   precondition to admit". That reason does not hold: on a total carrier the
#   analogue is the OBLIGATION being unsatisfiable at an F2P-shaped input, which
#   an absent `require` does nothing to rule out — a clause pair can conflict
#   exactly where the behaviour is demanded, and if it did, every positive would
#   verify vacuously and no reject case would notice. The claim that such a
#   positive could only assert a triviality was also wrong: `admiss-f2p-shaped-
#   point` discharges (C1) AND (C2) by evaluation at a concrete class arriving
#   with the flag FALSE and a non-empty association — asserting the arriving flag
#   is false is what makes the point one where the step must change something —
#   before closing the frozen obligation verbatim. It is live in both halves:
#   flipping the (C1) claim to `false` fails, and weakening the (C2) claim to `[]`
#   fails (both measured with real builds).
# PORTED, re-aimed (partial-domain rival): partial-fixed-identity attacks the
#   nagini identity clause E2 by pinning the result to a CONSTANT that is right at
#   one point of the domain and wrong elsewhere. E2 itself has no counterpart here
#   (see below), but the rival CLASS — correct on a sub-domain, wrong off it — is
#   expressible against (C2) and was missing: all four original rivals violate a
#   whole clause almost everywhere. `partial-fixed-map` ports it: publish a
#   hardcoded constant association, so (C2) holds at exactly the inputs whose
#   arriving map is that constant. Confirmed genuinely partial with real builds
#   (its tester evaluates to TRUE at the constant's own point and FALSE at the
#   witness point), so it is not a re-spelling of clobber-map.
# NO CARRIER (identity rival): weak-wrong-identity-obj attacks the nagini identity
#   clause E2 (Result().identity == identity) by returning an off-by-one identity.
#   The velvet mapping does NOT model class identity as an observation (the class
#   object abstracts to its flag + value→label map only, mapping.md §2), so E2 has
#   no counterpart here and there is no clause for that rival to violate — the
#   distinction it abuses (a wrong `identity`) is collapsed by this carrier.
#   Dropped, not fabricated. Its partial-domain SIBLING is ported anyway (above),
#   re-aimed at (C2), so the dropped clause costs the battery no attack CLASS.
# NEW (C2 attacks): velvet has a preservation/frame clause (C2) with no direct
#   nagini reject (nagini's E1 is a framing-permission clause, not a behavioural
#   one). Two rivals attack it: `clobber-map` (drop the map — wrong content) and
#   its near-miss `reorder-map` (right content, wrong order), so (C2)'s dependence
#   on `built.valueToLabel`'s content AND order is both exercised. This is the
#   directive-5 frame obligation the mapping calls out (a wrong impl that set the
#   flag but clobbered the map would fail the F2P `.label`/`.value` read).
#   `reorder-map` writes the flag literal explicitly: as originally ported it used
#   `{ built with valueToLabel := ... }`, which inherits the ARRIVING flag and so
#   ALSO violates (C1) wherever that flag is false — two faults at once, letting
#   the witness be satisfied by the (C1) failure omit-flag already covers. With
#   the flag forced true, (C2) is the sole possible cause and the refutation is
#   order alone. Both spellings are rejected and both witnesses discriminate
#   (measured); the change is about what the rejection ATTRIBUTES, not whether it
#   happens.
#
# CLAUSE COVERAGE: (C1) attacked by omit-flag + flag-false; (C2) attacked by
#   clobber-map (content), reorder-map (order) and partial-fixed-map
#   (sub-domain). Both independent top-level clauses attacked, and (C2) is
#   attacked by all three of the whole-clause, near-miss and partial-domain
#   classes.
# BINDER COVERAGE: the one input binder `built` is varied across both fields —
#   `doNotCallInTemplates` ∈ {false, true} and `valueToLabel` ∈ {[], [(1,A)],
#   [(7,Z)], [(1,A),(2,B)], [(2,Oth)]} — over five DISTINCT reject witness points
#   (pts=5), plus the admissibility point [(1,Lbl)] with the flag arriving false.
#   The variation is verdict-CHANGING, not two spellings of one point: the empty
#   map is the only point at which clobber-map is correct, the singletons are the
#   only points at which reorder-map is correct, and the flag values separate the
#   inputs where omit-flag is correct from those where it is not.
#
# SPEC-HOLE PROBES run under audit and NOT landed (they found nothing, so there is
#   nothing to ship, but they bound what was tried). Wrong impls checked against
#   the frozen spec, all correctly REJECTED with the clause named in the unsolved
#   goal: flag derived from the map's emptiness (`(!built.valueToLabel.isEmpty) =
#   true` unsolved, (C1)); map truncated to its first entry (`List.take 1 … = …`
#   unsolved, (C2)); every label overwritten with a placeholder while keys are
#   kept (`List.map (fun p => (p.1, ['?'])) … = …` unsolved, (C2)). Correct
#   reshapes checked to verify: `.reverse.reverse` and `++ []` round-trips on the
#   map both verify under the frozen script; a `.map id` round-trip needs
#   `all_goals simp` in the elided tactic body and then verifies, which is proof
#   retuning rather than a spec hole. No wrong impl verified and no faithful
#   correct impl was rejected.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom (the publish step is modeled directly, not delegated to an oracle), so
# there is nothing to probe and the gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
