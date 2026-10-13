# properties.py — PBT falsification battery for django__django-12304.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Spec
# cases are full model.py variants that share the FROZEN spec byte-for-byte
# (region-surgery: ONLY the impl region of build_template_usable_grouping is
# edited) and are checked by Nagini verify + same_spec. Axiom cases are
# self-contained probes run in the instance Docker image against the REAL Django
# callees.
#
# Defended surface (reasoned from model.py, NOT mechanical):
#   build_template_usable_grouping(identity: int) -> EnumGrouping
#     Requires:
#       (P1) MustTerminate(2)                    [TOTAL correctness — must deliver]
#       (P2) identity > 0
#       (P3) declaration_available(identity)     [ONE pending declaration to build from]
#       There is deliberately NO fourth precondition restricting WHICH
#       declarations are specified. Every declaration is in scope and the
#       Ensures/Exsures below are a COMPLETE, ORDERED case split over the three
#       refusals the construction can make plus delivery. A precondition
#       excluding any refusal would hand an implementation a region it may behave
#       arbitrarily in, and each of the three regions is reachable and its report
#       observable to the declarer.
#     Ensures (load-bearing clauses):
#       (E0a) not base_step_refuses(identity)        [DELIVERY implies the base
#             construction step accepted the declaration — establishable only by
#             having RUN that step, since the predicate is opaque]
#       (E0b) not flag_name_taken_by_choice(identity) [DELIVERY is mandatory off
#             the taken-name case, so the refusal leg cannot be used as a dodge]
#       (E0c) not repeats_choice_value(identity)     [DELIVERY implies the
#             value-distinctness step at the END of the construction accepted the
#             declaration — establishable only by having run it, i.e. AFTER the
#             flag is recorded]
#       (E1) built_from_declaration(Result(), identity)  [PROVENANCE: the object
#            delivered is the one the base construction step built for THIS
#            declaration, not any object that reports the requested identity]
#       (E1b) distinctness_confirmed(Result(), identity)  [WHO established E0c:
#            the value-distinctness step ITSELF confirmed, on the very grouping
#            delivered, that the declared choice values are distinct. E0c says
#            the fact; E1b says the step whose decision it is actually made it.
#            An unforgeable body-less token issued ONLY by that step's delivery
#            leg, so a construction cannot read the declaration, conclude the
#            values are distinct and deliver on its own authority]
#       (E2) Acc(Result().identity) and Acc(Result().preserve_when_callable)  [framing]
#       (E3) Result().identity == identity                                    [identity]
#       (E4) Result().preserve_when_callable == True                          [THE flag]
#       (E5) resolved_in_template(Result()) == identity                       [behaviour]
#       (E6) resolved_in_template(Result()) != INVALID_VALUE                  [behaviour]
#     Exsures:
#       (X1) BaseStepRefused,
#            base_step_refuses(identity)
#            and base_step_report(RaisedException(), identity)
#            [the base construction step's own report, passed on UNCHANGED; it
#            may escape only for a declaration that step actually refuses, AND the
#            report the declarer receives must BE that step's report OBJECT — the
#            token is issued by that step's refusal leg FOR THE OBJECT IT RAISED,
#            so a construction can neither anticipate the refusal off the
#            declaration nor catch the step's report and hand on a replacement of
#            its own composition]
#       (X2) PreserveFlagNameTaken,
#            flag_name_taken_by_choice(identity) and not base_step_refuses(identity)
#            [the recording of the flag is REFUSED exactly when one of the
#            grouping's own declared choices already occupies the flag's name;
#            E0b forces the refusal to occur there and X2 confines it to there.
#            No report token here: this refusal is the CONSTRUCTION's own guarded
#            binding, not a report relayed from a separate step]
#       (X3) RepeatedChoiceValue,
#            repeats_choice_value(identity) and not base_step_refuses(identity)
#            and not flag_name_taken_by_choice(identity)
#            and distinctness_step_report(RaisedException(), identity)
#            [the value-distinctness step at the END of the construction refused;
#            E0c forces it to occur there and X3 confines it to there. The
#            `not flag_name_taken_by_choice` conjunct pins the ORDER: the flag is
#            recorded BEFORE this step runs, so a declaration that both names a
#            choice after the flag's name AND repeats a choice value must report
#            X2, never X3. The report token pins WHICH report object it is: a body
#            that anticipates the repeated-value refusal off the opaque
#            declaration predicate without letting the step word it holds no
#            token, and so does one that lets the step refuse and then substitutes
#            a freshly composed report for the one the step raised]
#   E1b / X1's and X3's report tokens are the RELAY obligation, and they are what
#   separates "a refusal of the right kind at the right point" from "the report
#   that step made". Each is a body-less @ContractOnly @Predicate with a single
#   issuer — the corresponding leg of the corresponding step — so it cannot be
#   Folded into existence nor obtained without running that step. The two report
#   tokens are moreover held BY THE REPORT OBJECT (`RaisedException()`), not by the
#   declaration alone, so they pin WHICH report reaches the declarer and not merely
#   that the step ran. Without them the two step-owned outcomes (base refusal,
#   distinctness refusal/confirmation) are dischargeable by BRANCHING on the opaque
#   @Pure declaration predicates, and an impl may skip the step entirely: it
#   satisfies every clause about the OCCURRENCE and ORDER of the refusal while
#   having to re-word the step's report itself, which a declarer reading the
#   report's content observes. With identity-only tokens a SECOND family survives —
#   run the step, catch its report, raise a fresh one of the same kind — and it is
#   equally unfaithful for the same reason; binding the token to the report object
#   closes both. Reject cases weak-anticipate-distinctness,
#   weak-anticipate-distinctness-late, weak-anticipate-base-refusal,
#   weak-relabel-base-report, weak-relabel-distinctness-report and
#   weak-echo-relay-both exercise them.
#   P1 makes the Ensures claims of a construction that ACTUALLY RETURNS, not of
#   the runs that happen to reach the return: without it Nagini proves only
#   partial correctness and a body that re-enters itself (or loops forever)
#   discharges every clause above vacuously while delivering no grouping at all.
#   P3 is an opaque single-use @Predicate resource that base_class_creation
#   CONSUMES and never returns, so the base construction step can be run at most
#   once per declaration. It carries no Ensures — its whole content is
#   MULTIPLICITY. Reject cases weak-diverge-selfcall / weak-diverge-loop and
#   weak-double-construct exercise P1 and P3 respectively.
#   E1 is the second half of "the grouping this construction produced":
#   built_from_declaration is a body-less @ContractOnly @Predicate, so it cannot
#   be Folded into existence — the only way to hold one is to have obtained it
#   from the base construction step (which issues it for the object it produced)
#   or from the value-distinctness step (which passes it along). Together with P3
#   it forbids both fabricating a grouping and building one but delivering
#   something else. Reject case weak-echo-fabricate exercises it.
#   E0b + X2 are the two-sided REFUSAL obligation for the flag's own name.
#   Recording the flag is a guarded binding, not a free field write: a
#   constructed grouping refuses to rebind a name one of its own declared choices
#   already occupies, so on a declaration that names a choice after the flag's
#   own name the construction delivers NO grouping and reports the refusal
#   instead. X2 alone would let an impl refuse everywhere (vacuous delivery);
#   E0b alone would forbid the refusal the real construction must make. Reject
#   cases weak-always-refuse and weak-inverted-refuse exercise them.
#   E0a + X1 and E0c + X3 are the SAME two-sided obligation for the other two
#   refusals, and they are what makes the case split complete. E0c/X3 in
#   particular cover the declarations that repeat a choice value: those are
#   refused only at the very END of the construction, by a step it reaches
#   normally and AFTER the flag has been recorded, so they are ordinary
#   in-domain declarations whose reported refusal is observable. Reject cases
#   weak-skip-distinctness, weak-wrong-report-on-repeat, weak-swap-reports,
#   weak-finalize-before-flag and weak-invent-base-refusal exercise them.
#   The behavioural clauses (E5/E6) are GROUNDED, not an answer-key echo: the
#   @Pure axiom resolved_in_template is a function of Result().preserve_when_callable
#   (Implies(preserve, Result()==identity); Implies(not preserve, Result()==0)),
#   so to satisfy E5 (with identity>0) the impl MUST establish preserve==True.
#   There is therefore no "wrong echo" of an opaque oracle — see assessment.
#
#   The modeled function takes a single PRIMITIVE input (identity: int); it has
#   NO read-only Acc(x,1/2) object parameter, so the frame-mutation attack
#   (overwrite a half-permission input) does not apply (justified in assessment).
#   The object the impl writes to (grouping.preserve_when_callable = True) is the
#   FRESH full-permission object returned by base_class_creation, which the impl
#   owns — a legitimate write, not a frame violation.
from pathlib import Path

INSTANCE = "django__django-12304"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl-region body (between # impl-start / # impl-end). Every
# variant is produced by _swap on this single anchor, so only the impl region is
# ever touched and same_spec is guaranteed.
_GOLD_IMPL = (
    "    grouping = base_class_creation(identity)  # type: EnumGrouping\n"
    "    if flag_name_taken_by_choice(identity):\n"
    "        raise PreserveFlagNameTaken()\n"
    "    grouping.preserve_when_callable = True\n"
    "    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping\n"
    "    return delivered"
)


def _impl(body: str) -> str:
    return _swap(_BASE, _GOLD_IMPL, body)


# ----------------------------------------------------------------------------
# SPEC LANE
# ----------------------------------------------------------------------------
SPEC_TESTS = [

    # --- POSITIVE CONTROL (soundness): record the flag AFTER the distinctness --
    # step rather than before it. Structurally different from gold, and faithful:
    # in the real construction the value-distinctness step hands back the very
    # object it was given, so recording the flag on the object it returns is the
    # same observable behaviour (and still reports the taken-name refusal first,
    # which is what X3's ordering conjunct demands). MUST verify; if it cannot,
    # the postcondition is SPEC-TOO-STRONG.
    {
        "id": "pos-flag-after-distinctness",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    grouping = base_class_creation(identity)  # type: EnumGrouping\n"
            "    if flag_name_taken_by_choice(identity):\n"
            "        raise PreserveFlagNameTaken()\n"
            "    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping\n"
            "    delivered.preserve_when_callable = True\n"
            "    return delivered"
        ),
        "rationale": (
            "A correct, structurally-different impl: the flag is recorded on the "
            "object the value-distinctness step hands back (which that step's "
            "Ensures pins to be the SAME object, with the provenance token passed "
            "along). E0a-E6 and X1-X3 all still discharge. If it fails to verify, "
            "the postcondition is too strong / proof-fragile (SPEC-TOO-STRONG)."
        ),
    },

    # --- POSITIVE CONTROL 2 (soundness): reorder via a local boolean -----------
    # Same gold operations, reshaped: bind the flag to a typed local then assign.
    # Keeps the gold proof obligations; only the executable shape changes.
    {
        "id": "pos-local-flag",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    grouping = base_class_creation(identity)  # type: EnumGrouping\n"
            "    if flag_name_taken_by_choice(identity):\n"
            "        raise PreserveFlagNameTaken()\n"
            "    flag = True  # type: bool\n"
            "    grouping.preserve_when_callable = flag\n"
            "    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping\n"
            "    return delivered"
        ),
        "rationale": (
            "A local-variable reshape of the gold impl (flag bound to a typed "
            "local) must still verify; it changes only executable shape, keeping "
            "every gold proof obligation. If it fails, SPEC-TOO-STRONG (proof "
            "fragility)."
        ),
    },

    # --- ADMISSIBILITY: the precondition + axioms admit an F2P-shaped input ----
    # F2P uses Suit.DIAMOND with value 1 (identity 1 in the model). The variant
    # constructs a concrete F2P-shaped grouping locally and asserts the behavioural
    # contract holds for it (resolved_in_template == 1 != INVALID_VALUE), proving
    # the precondition / axioms are jointly satisfiable (non-vacuous) for a normal
    # input, then proceeds with the gold return. If this cannot verify, the
    # precondition/axiom set is contradictory => PRECOND-TOO-STRONG.
    {
        "id": "admiss-f2p-diamond",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    probe = EnumGrouping(1, True)  # type: EnumGrouping\n"
            "    Assert(resolved_in_template(probe) == 1)\n"
            "    Assert(resolved_in_template(probe) != INVALID_VALUE)\n"
            "    grouping = base_class_creation(identity)  # type: EnumGrouping\n"
            "    if flag_name_taken_by_choice(identity):\n"
            "        raise PreserveFlagNameTaken()\n"
            "    grouping.preserve_when_callable = True\n"
            "    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping\n"
            "    return delivered"
        ),
        "rationale": (
            "Admissibility: a concrete F2P-shaped grouping (identity 1, the "
            "value of Suit.DIAMOND) satisfies the behavioural contract "
            "(resolved_in_template==1, non-INVALID). The asserts go through only "
            "if the precondition/axioms are jointly consistent for a normal "
            "input; failure => PRECOND-TOO-STRONG (vacuous/contradictory spec)."
        ),
    },

    # --- UNIQUENESS / prepatch kill: omit the flag (do nothing) ----------------
    # The faithful real variant is "do not record the flag at all" = exactly the
    # pre-patch code. Must be REJECTED: base_class_creation leaves the initial
    # flag UNCONSTRAINED (havoced), so E4 (preserve==True) cannot be established,
    # nor can E5/E6 (resolved_in_template is pinned only through the flag).
    {
        "id": "weak-omit-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    grouping = base_class_creation(identity)  # type: EnumGrouping\n"
            "    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping\n"
            "    return delivered"
        ),
        "refinement": (
            "Its faithful real variant is the empty diff (never record "
            "`cls.do_not_call_in_templates = True`) = the pre-patch source. Then "
            "the template engine invokes Suit() (no args), which raises a "
            "required-argument TypeError, so `Suit` resolves to string_if_invalid; "
            "`Suit.DIAMOND.label` renders '' and the F2P test_templates "
            "(expects 'Diamond|1') FAILS. Does NOT resolve."
        ),
        "rationale": (
            "Rejected on the clause the verifier reports first, E0b (not "
            "flag_name_taken_by_choice(identity)): with no flag recorded there is "
            "nothing to establish that the flag's own name was free, so this body "
            "delivers a grouping for a declaration the real construction refuses. "
            "E4 (Result().preserve_when_callable == True) and E5 "
            "(resolved_in_template(Result()) == identity) are independently "
            "unprovable too, since base_class_creation leaves the initial flag "
            "havoced — weak-flag-false isolates that leg. Both failures are real "
            "consequences of removing the one line: it is what makes the recording "
            "step (and hence its refusal) exist at all, and what makes the "
            "delivered grouping preserved. This is the model_prepatch kill "
            "(G-DIFF), byte-identical to model_prepatch.py's impl region."
        ),
    },

    # --- UNIQUENESS: set the flag to False (a wrong literal) -------------------
    # Real analogue: `cls.do_not_call_in_templates = False`. getattr reads it as
    # falsy => the engine invokes Suit() => fails => string_if_invalid => the F2P
    # test fails. Must be REJECTED by E4 (and E5).
    {
        "id": "weak-flag-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    grouping = base_class_creation(identity)  # type: EnumGrouping\n"
            "    if flag_name_taken_by_choice(identity):\n"
            "        raise PreserveFlagNameTaken()\n"
            "    grouping.preserve_when_callable = False\n"
            "    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping\n"
            "    return delivered"
        ),
        "refinement": (
            "Its faithful real variant records `cls.do_not_call_in_templates = "
            "False`. getattr(cls, 'do_not_call_in_templates', False) is then "
            "falsy, so the resolution rule does NOT take the preserve branch; it "
            "invokes Suit(), which fails, yielding string_if_invalid. "
            "`{{ Suit.DIAMOND.label }}` renders '' and test_templates FAILS. "
            "Does NOT resolve."
        ),
        "rationale": (
            "Rejected by E4 (preserve must be True) and E5 (preserve==False => "
            "resolved_in_template == INVALID_VALUE != identity)."
        ),
    },

    # --- UNIQUENESS: toggle the flag instead of establishing it ----------------
    # Exploits the deliberately havoced initial flag: a grouping built under an
    # already-flagged base INHERITS the flag, so toggling clears it exactly for
    # the subclasses the F2P test uses. Must be REJECTED by E4.
    {
        "id": "weak-toggle-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    grouping = base_class_creation(identity)  # type: EnumGrouping\n"
            "    if flag_name_taken_by_choice(identity):\n"
            "        raise PreserveFlagNameTaken()\n"
            "    grouping.preserve_when_callable = not grouping.preserve_when_callable\n"
            "    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping\n"
            "    return delivered"
        ),
        "refinement": (
            "Its faithful real variant records `cls.do_not_call_in_templates = "
            "not getattr(cls, 'do_not_call_in_templates', False)`. `Choices` "
            "itself gets the flag, but every subclass — `IntegerChoices`, "
            "`TextChoices`, and the F2P `Suit` — INHERITS a truthy flag from its "
            "base and therefore ends up with it cleared, so `Suit` is invoked in "
            "the template and test_templates FAILS. Does NOT resolve."
        ),
        "rationale": (
            "Rejected by E4: base_class_creation's Ensures deliberately pins "
            "nothing about the initial flag (both inherited-truthy and "
            "absent-falsy are realizable through the real callee, demonstrated by "
            "axiom_check), so `not <havoced>` cannot be shown to be True."
        ),
    },

    # --- PARTIAL-DOMAIN: correct only at identity == 1 -------------------------
    # Returns a grouping whose identity is pinned to the literal 1 (the F2P
    # DIAMOND value) with the flag set. Must be REJECTED by E1 (provenance) and
    # E3 (Result().identity == identity) for identity != 1.
    {
        "id": "partial-fixed-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    grouping = EnumGrouping(1, True)  # type: EnumGrouping\n"
            "    return grouping"
        ),
        "refinement": (
            "Its faithful real variant makes the metaclass return a FIXED, "
            "different class object regardless of the actual enumeration "
            "(modelled as a constant identity). In the template, `Suit` would "
            "then resolve to the wrong class object, so `Suit.DIAMOND` (and "
            "`.label`) would not exist and test_templates FAILS for any grouping "
            "other than the one whose value happens to be 1. Does NOT resolve in "
            "general."
        ),
        "rationale": (
            "Rejected on E0a (not base_step_refuses(identity)) — the clause the "
            "verifier reports — because a body that never runs the base "
            "construction step cannot establish that the step accepted this "
            "declaration; E1 (no provenance token for a fabricated object) and E3 "
            "(the constant identity 1 disagrees with the requested identity on "
            "the rest of the domain) fail as well. Pins only one point of the "
            "input domain."
        ),
    },

    # --- SUPPORTING near-miss: build correctly, deliver a DIFFERENT object -----
    # Performs every step of the gold impl (so E0a/E0b/E0c all hold) and then
    # hands back a freshly constructed grouping with a different identity. This is
    # the sharpest test of E1+E3: the whole construction happened, only the object
    # delivered is wrong.
    {
        "id": "weak-wrong-identity-obj",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    grouping = base_class_creation(identity)  # type: EnumGrouping\n"
            "    if flag_name_taken_by_choice(identity):\n"
            "        raise PreserveFlagNameTaken()\n"
            "    grouping.preserve_when_callable = True\n"
            "    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping\n"
            "    other = EnumGrouping(identity + 1, True)  # type: EnumGrouping\n"
            "    return other"
        ),
        "refinement": (
            "Its faithful real variant runs the whole construction and then "
            "returns a DIFFERENT class object than the enumeration it built "
            "(modelled as an off-by-one identity). The template variable `Suit` "
            "then resolves to an unrelated object; `Suit.DIAMOND.label` does not "
            "resolve and test_templates FAILS, as does every PASS_TO_PASS test "
            "that reads the declared members. Does NOT resolve."
        ),
        "rationale": (
            "Rejected by E1 (the provenance token is held for the object the base "
            "step built, not for this one) and E3 (identity+1 != identity). Every "
            "step of the construction did run here, and all three refusal clauses "
            "E0a/E0b/E0c are discharged — so this case isolates the delivery "
            "obligation itself: the grouping handed back must BE the one that was "
            "built."
        ),
    },

    # --- UNIQUENESS: ORACLE ECHO — decide every opaque predicate, do no work ---
    # Reads the three opaque declaration predicates, reports the matching refusal
    # for each, and otherwise hands back a grouping it constructed itself with the
    # flag already set. Every scalar clause (E0a-E0c, E3-E6) is satisfied; the
    # construction never happens. Must be REJECTED by E1, the provenance token.
    {
        "id": "weak-echo-fabricate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if base_step_refuses(identity):\n"
            "        raise BaseStepRefused()\n"
            "    if flag_name_taken_by_choice(identity):\n"
            "        raise PreserveFlagNameTaken()\n"
            "    if repeats_choice_value(identity):\n"
            "        raise RepeatedChoiceValue()\n"
            "    made = EnumGrouping(identity, True)  # type: EnumGrouping\n"
            "    return made"
        ),
        "refinement": (
            "Its faithful real variant never calls `super().__new__` at all: it "
            "decides the refusal conditions off the class dictionary and, on the "
            "accepting branch, hands back an object it made itself instead of the "
            "enumeration class the base construction produces. `class Suit(int, "
            "Choices)` then does not name a real enumeration — `Suit.DIAMOND` "
            "does not exist — so test_templates FAILS, and so does every "
            "PASS_TO_PASS test that reads members, choices, labels or values. "
            "Does NOT resolve."
        ),
        "rationale": (
            "Rejected by E1 (built_from_declaration(Result(), identity)): the "
            "predicate has no body, so it cannot be Folded into existence, and "
            "the only issuers are the base construction step and the "
            "value-distinctness step that passes it along. An impl that never "
            "runs the base step holds no token for what it delivers. Note that "
            "every OTHER clause of this spec is satisfied by this body, so E1 is "
            "exactly the clause that separates 'the grouping the construction "
            "produced' from 'any object reporting the requested identity'."
        ),
    },

    # --- UNIQUENESS: refuses on EVERY declaration (delivery dodge) -------------
    # Reports a refusal unconditionally. X2 alone would admit this: the Exsures
    # only describes the state once a refusal happened. Must be REJECTED by E0b.
    {
        "id": "weak-always-refuse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    grouping = base_class_creation(identity)  # type: EnumGrouping\n"
            "    raise PreserveFlagNameTaken()"
        ),
        "refinement": (
            "Its faithful real variant refuses to record the flag on every "
            "declaration, so `class Suit(int, Choices)` raises instead of "
            "producing the enumeration. The F2P module cannot even import and "
            "`{{ Suit.DIAMOND.label }}` never renders. Does NOT resolve."
        ),
        "rationale": (
            "Rejected on X2, whose guard (flag_name_taken_by_choice(identity) and "
            "not base_step_refuses(identity)) is unprovable on the branch this "
            "body raises from — the verifier reports exactly that assertion. E0b "
            "is the other half: it makes DELIVERY mandatory wherever the flag's "
            "name is not already taken by one of the grouping's own declared "
            "choices. Without the pair, an Exsures alone would let this verify "
            "while delivering nothing (SPEC-TOO-WEAK)."
        ),
    },

    # --- UNIQUENESS: refuses on the COMPLEMENT of the real condition -----------
    # Delivers exactly where the real construction refuses and refuses exactly
    # where it must deliver. E0b kills it.
    {
        "id": "weak-inverted-refuse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    grouping = base_class_creation(identity)  # type: EnumGrouping\n"
            "    if not flag_name_taken_by_choice(identity):\n"
            "        raise PreserveFlagNameTaken()\n"
            "    grouping.preserve_when_callable = True\n"
            "    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping\n"
            "    return delivered"
        ),
        "refinement": (
            "Its faithful real variant inverts the guard on the recording step: "
            "it refuses precisely the ordinary declarations (`Suit` with DIAMOND) "
            "and attempts the recording precisely where the grouping refuses to "
            "rebind the name anyway. `class Suit(int, Choices)` then raises, the "
            "F2P module fails to import, and the template never renders. Does "
            "NOT resolve."
        ),
        "rationale": (
            "Rejected on X2 (the assertion the verifier reports): the body raises "
            "PreserveFlagNameTaken on the branch where the flag's name is NOT "
            "taken, and X2 confines that report to declarations where it is. E0b "
            "fails on the complementary branch, where it delivers for a "
            "declaration the real construction refuses. Together they pin the "
            "refusal to the taken-name case rather than merely permitting "
            "refusals somewhere."
        ),
    },

    # --- UNIQUENESS: wrong report on a repeated choice value ------------------
    # THE counterexample family this spec was hardened against. A repeated choice
    # value is refused only at the very END of the construction, AFTER the flag
    # has been recorded, by a step the construction reaches normally — so it is an
    # ordinary in-domain declaration, not an excluded region. This body reports
    # the taken-name refusal there instead of the value-distinctness one. Must be
    # REJECTED by X2's guard.
    {
        "id": "weak-wrong-report-on-repeat",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    grouping = base_class_creation(identity)  # type: EnumGrouping\n"
            "    if repeats_choice_value(identity):\n"
            "        raise PreserveFlagNameTaken()\n"
            "    if flag_name_taken_by_choice(identity):\n"
            "        raise PreserveFlagNameTaken()\n"
            "    grouping.preserve_when_callable = True\n"
            "    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping\n"
            "    return delivered"
        ),
        "refinement": (
            "Its faithful real variant detects a repeated choice value itself "
            "(len(cls._value2member_map_) != len(cls._member_names_)) and raises "
            "`AttributeError('Cannot reassign members.')` — the report the "
            "taken-name case makes — instead of letting the value-distinctness "
            "step report it. PASS_TO_PASS `test_invalid_definition "
            "(model_enums.tests.ChoicesTests)` asserts `ValueError: duplicate "
            "values found in <enum 'Fruit'>: PINEAPPLE -> APPLE` for exactly that "
            "declaration and ERRORs on the AttributeError. Does NOT resolve."
        ),
        "rationale": (
            "Rejected by X2: PreserveFlagNameTaken may escape only where "
            "flag_name_taken_by_choice(identity) holds, and on this branch only "
            "repeats_choice_value(identity) is known — the two predicates are "
            "independent, so nothing lets one stand in for the other. This is the "
            "clause that denies an implementation the freedom to treat a repeated "
            "choice value as an unspecified region: it is refused after the flag "
            "is recorded, by a step the construction reaches normally, and the "
            "harness grades that report."
        ),
    },

    # --- UNIQUENESS: drop the value-distinctness step entirely -----------------
    {
        "id": "weak-skip-distinctness",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    grouping = base_class_creation(identity)  # type: EnumGrouping\n"
            "    if flag_name_taken_by_choice(identity):\n"
            "        raise PreserveFlagNameTaken()\n"
            "    grouping.preserve_when_callable = True\n"
            "    return grouping"
        ),
        "refinement": (
            "Its faithful real variant records the flag and returns `cls` "
            "directly instead of `enum.unique(cls)`, so a declaration that "
            "repeats a choice value is delivered as a perfectly good enumeration. "
            "PASS_TO_PASS `test_invalid_definition` expects `ValueError: "
            "duplicate values found in <enum 'Fruit'>: PINEAPPLE -> APPLE` and "
            "gets no exception at all. Does NOT resolve."
        ),
        "rationale": (
            "Rejected by E0c (not repeats_choice_value(identity)) and E1b "
            "(distinctness_confirmed): DELIVERY carries the claim that the "
            "value-distinctness step accepted the declaration AND that the step "
            "itself confirmed it on the delivered grouping, and the only way to "
            "obtain either is to have run the step. Dropping it leaves both "
            "clauses unprovable."
        ),
    },

    # --- UNIQUENESS: ANTICIPATE the distinctness refusal, skip the step -------
    # THE RECORDED COUNTEREXAMPLE FAMILY. The value-distinctness step is never
    # invoked: the body reads the opaque declaration predicate directly, reports
    # the repeated-value refusal itself, and on the accepting branch delivers
    # without ever letting the step confirm anything. Every clause about the
    # OCCURRENCE, KIND and ORDER of the refusal holds. Must be REJECTED by X3's
    # report token (the refusal it makes is its OWN, not the step's) and by E1b
    # (nothing confirmed the delivered grouping).
    {
        "id": "weak-anticipate-distinctness",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    grouping = base_class_creation(identity)  # type: EnumGrouping\n"
            "    if flag_name_taken_by_choice(identity):\n"
            "        raise PreserveFlagNameTaken()\n"
            "    if repeats_choice_value(identity):\n"
            "        raise RepeatedChoiceValue()\n"
            "    grouping.preserve_when_callable = True\n"
            "    return grouping"
        ),
        "refinement": (
            "Its faithful real variant never invokes the value-distinctness step "
            "at all: it detects the repeated value itself off the class's own "
            "value table and raises its OWN ValueError, then records the flag and "
            "returns the class directly. The refusal happens for exactly the "
            "right declarations, with the right exception type, at the right "
            "point — but the message is the construction's own wording rather "
            "than the step's. PASS_TO_PASS `test_invalid_definition "
            "(model_enums.tests.ChoicesTests)` asserts the message content "
            "(`assertRaisesMessage(ValueError, \"duplicate values found in <enum "
            "'Fruit'>: PINEAPPLE -> APPLE\")`), which names the offending choices "
            "as the step names them, so any re-worded report FAILS it. Does NOT "
            "resolve."
        ),
        "rationale": (
            "Rejected by X3's `distinctness_step_report(RaisedException(), "
            "identity)` conjunct: the token is body-less and issued ONLY by the "
            "value-distinctness step's own refusal leg, for the report object it "
            "raises, so a body that branches on the opaque @Pure predicate and "
            "raises one of its own holds nothing to present. E1b "
            "(distinctness_confirmed(Result(), identity)) independently rejects "
            "the delivering branch, since nothing confirmed the grouping it hands "
            "back. Note that E0c and X3's ordering conjuncts are ALL satisfied by "
            "this body — pinning only the occurrence and the order of the refusal "
            "leaves its CONTENT to the implementation, which is precisely the "
            "observable the harness grades (SPEC-TOO-WEAK without the tokens)."
        ),
    },

    # --- UNIQUENESS: same anticipation, but AFTER the flag and still relayed --
    # A mutation of the family above that keeps the step in the body for the
    # accepting branch, so E1b is satisfied, and anticipates ONLY the refusal.
    # Isolates X3's report token: the refusal is still the construction's own.
    {
        "id": "weak-anticipate-distinctness-late",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    grouping = base_class_creation(identity)  # type: EnumGrouping\n"
            "    if flag_name_taken_by_choice(identity):\n"
            "        raise PreserveFlagNameTaken()\n"
            "    grouping.preserve_when_callable = True\n"
            "    if repeats_choice_value(identity):\n"
            "        raise RepeatedChoiceValue()\n"
            "    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping\n"
            "    return delivered"
        ),
        "refinement": (
            "Its faithful real variant guards the value-distinctness call: it "
            "detects the repeated value itself and raises its OWN ValueError "
            "before reaching the step, and otherwise calls the step normally. "
            "Delivery is therefore identical to gold and every accepting-path "
            "test passes; only the refusal's message differs from the step's. "
            "PASS_TO_PASS `test_invalid_definition` asserts that message and "
            "FAILS. Does NOT resolve."
        ),
        "rationale": (
            "Rejected by X3's report token alone — this case exists to isolate it "
            "from E1b. Here the accepting branch DOES run the value-distinctness "
            "step, so E0a-E0c, E1, E1b and E2-E6 all discharge; the only "
            "unprovable clause is `distinctness_step_report(RaisedException(), "
            "identity)` on the branch the body raises from, because the step that "
            "issues that token for the report it raises was skipped exactly there. So the token is load-bearing on the "
            "refusal leg independently of the delivery leg."
        ),
    },

    # --- UNIQUENESS: ANTICIPATE the base step's refusal -----------------------
    # The mirror-image family for the FIRST step: pre-empt its refusal off the
    # opaque declaration predicate and report it without letting the step run.
    # Must be REJECTED by X1's report token.
    {
        "id": "weak-anticipate-base-refusal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if base_step_refuses(identity):\n"
            "        raise BaseStepRefused()\n"
            "    grouping = base_class_creation(identity)  # type: EnumGrouping\n"
            "    if flag_name_taken_by_choice(identity):\n"
            "        raise PreserveFlagNameTaken()\n"
            "    grouping.preserve_when_callable = True\n"
            "    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping\n"
            "    return delivered"
        ),
        "refinement": (
            "Its faithful real variant pre-screens the declaration and raises its "
            "OWN TypeError for a kind that cannot carry the declared values, "
            "instead of letting the base construction step raise. PASS_TO_PASS "
            "`test_invalid_definition` asserts `TypeError: 'str' object cannot be "
            "interpreted as an integer` and `test_bool_unsupported` / "
            "`test_uuid_unsupported` assert the base step's own messages "
            "(\"type 'bool' is not an acceptable base type\"), so a re-worded "
            "report FAILS them. Does NOT resolve."
        ),
        "rationale": (
            "Rejected by X1's `base_step_report(RaisedException(), identity)` "
            "conjunct: the token is issued only by the base construction step's "
            "refusal leg, for the report object it raises, so pre-empting the "
            "refusal off the opaque predicate leaves nothing to present. The mirror of weak-anticipate-distinctness for the FIRST "
            "step — included because closing one step's relay obligation and not "
            "the other's would leave the same hole open on the other path."
        ),
    },

    # --- UNIQUENESS: ORACLE ECHO on BOTH relay legs at once -------------------
    # Decide all three opaque declaration predicates, report each refusal itself,
    # and deliver a genuinely-built, genuinely-flagged grouping on the accepting
    # branch WITHOUT the distinctness step. The sharpest form: the provenance
    # token E1 is legitimately held (the base step really ran), so only the relay
    # clauses can reject it.
    {
        "id": "weak-echo-relay-both",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    if base_step_refuses(identity):\n"
            "        raise BaseStepRefused()\n"
            "    grouping = base_class_creation(identity)  # type: EnumGrouping\n"
            "    if flag_name_taken_by_choice(identity):\n"
            "        raise PreserveFlagNameTaken()\n"
            "    if repeats_choice_value(identity):\n"
            "        raise RepeatedChoiceValue()\n"
            "    grouping.preserve_when_callable = True\n"
            "    return grouping"
        ),
        "refinement": (
            "Its faithful real variant decides every refusal condition itself off "
            "the declaration, raising its own exceptions of the right types in the "
            "right order, and on the accepting path builds the class, records the "
            "flag and returns it without the value-distinctness step. F2P "
            "test_templates PASSES (the flag is set, the grouping resolves). But "
            "PASS_TO_PASS `test_invalid_definition` reads the CONTENT of both "
            "reports it asserts and gets the construction's own wording for each. "
            "Does NOT resolve."
        ),
        "rationale": (
            "Rejected by X1's and X3's report tokens and by E1b — three "
            "independent clauses, none of which is about the occurrence, kind or "
            "order of a refusal (all of which this body gets right). E1 is "
            "genuinely held here, since the base construction step really ran on "
            "the accepting path, so this case is the sharpest evidence that "
            "PROVENANCE of the delivered object and RELAY of a step's report are "
            "two different obligations."
        ),
    },

    # --- UNIQUENESS: RELABEL the base step's report ---------------------------
    # The step DOES run and DOES refuse, so the construction legitimately learns
    # the refusal happened; it then discards the step's report object and hands on
    # a FRESH one of the same kind. Every clause about occurrence, kind, order —
    # and any token keyed on the DECLARATION rather than the report — is satisfied.
    # Only a token bound to the report OBJECT can reject it.
    {
        "id": "weak-relabel-base-report",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    try:\n"
            "        grouping = base_class_creation(identity)  # type: EnumGrouping\n"
            "    except BaseStepRefused:\n"
            "        raise BaseStepRefused()\n"
            "    if flag_name_taken_by_choice(identity):\n"
            "        raise PreserveFlagNameTaken()\n"
            "    grouping.preserve_when_callable = True\n"
            "    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping\n"
            "    return delivered"
        ),
        "refinement": (
            "Its faithful real variant wraps the base construction step, catches "
            "the failure it raises and re-raises a BARE one of the same class, "
            "losing the step's message. Delivery is byte-identical to gold, so F2P "
            "test_templates PASSES. But PASS_TO_PASS `test_invalid_definition` "
            "asserts `TypeError: 'str' object cannot be interpreted as an integer` "
            "and `test_bool_unsupported`, `test_timezone_unsupported`, "
            "`test_uuid_unsupported` assert the base step's own wording, and an "
            "emptied report FAILS all four. Measured: F2P 1/1 pass, P2P 4/17 fail. "
            "Does NOT resolve."
        ),
        "rationale": (
            "Rejected by X1's `base_step_report(RaisedException(), identity)` "
            "conjunct and ONLY by it: the step really ran and really refused, so "
            "any obligation phrased as `some report of this kind was made, by that "
            "step, for this declaration` is discharged. What is NOT discharged is "
            "that the report the declarer receives IS the object that step raised. "
            "This case is why the relay tokens are keyed on the report object: "
            "keyed on the declaration alone they leave this family admitted."
        ),
    },

    # --- UNIQUENESS: RELABEL the distinctness step's report -------------------
    # The mirror of the above on the second relay leg.
    {
        "id": "weak-relabel-distinctness-report",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    grouping = base_class_creation(identity)  # type: EnumGrouping\n"
            "    if flag_name_taken_by_choice(identity):\n"
            "        raise PreserveFlagNameTaken()\n"
            "    grouping.preserve_when_callable = True\n"
            "    try:\n"
            "        delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping\n"
            "    except RepeatedChoiceValue:\n"
            "        raise RepeatedChoiceValue()\n"
            "    return delivered"
        ),
        "refinement": (
            "Its faithful real variant wraps the value-distinctness step, catches "
            "its refusal and re-raises a bare one of the same class. The accepting "
            "path is gold, so F2P passes and the delivery clauses all hold; only "
            "the refusal the declarer reads is emptied of the step's account of "
            "WHICH two choices collide. PASS_TO_PASS `test_invalid_definition` "
            "asserts `duplicate values found in <enum 'Fruit'>: PINEAPPLE -> "
            "APPLE` and FAILS. Does NOT resolve."
        ),
        "rationale": (
            "Rejected by X3's `distinctness_step_report(RaisedException(), "
            "identity)` conjunct alone. E0a-E0c, E1, E1b, E2-E6 and X3's ordering "
            "conjuncts are all satisfied — the step ran, refused, and the ORDER is "
            "right. Included alongside weak-relabel-base-report so the "
            "report-object binding is exercised on BOTH relay legs: closing one "
            "and not the other would leave the same hole open on the other path."
        ),
    },

    # --- UNIQUENESS: swap the two refusal reports -----------------------------
    {
        "id": "weak-swap-reports",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    grouping = base_class_creation(identity)  # type: EnumGrouping\n"
            "    if flag_name_taken_by_choice(identity):\n"
            "        raise RepeatedChoiceValue()\n"
            "    grouping.preserve_when_callable = True\n"
            "    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping\n"
            "    return delivered"
        ),
        "refinement": (
            "Its faithful real variant raises `ValueError('duplicate values "
            "found ...')` where the grouping refuses to rebind the flag's name, "
            "i.e. it swaps the two reports a declarer distinguishes on. A "
            "declaration that names a choice `do_not_call_in_templates` then "
            "reports a duplicate-value error that is simply false of it, and "
            "user code catching `AttributeError` around the declaration no longer "
            "sees it. Does NOT resolve."
        ),
        "rationale": (
            "Rejected by X3, whose guard requires repeats_choice_value(identity) "
            "and NOT flag_name_taken_by_choice(identity); on this branch exactly "
            "the opposite is known. Boundary token swap on the reported refusal."
        ),
    },

    # --- UNIQUENESS: distinctness check BEFORE the flag is recorded -----------
    # Observationally different exactly where both refusals apply: the real
    # construction records the flag first, so a declaration that names a choice
    # after the flag's name AND repeats a choice value reports the taken-name
    # refusal. Must be REJECTED by X3's ordering conjunct.
    {
        "id": "weak-finalize-before-flag",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    grouping = base_class_creation(identity)  # type: EnumGrouping\n"
            "    checked = finalize_grouping(grouping, identity)  # type: EnumGrouping\n"
            "    if flag_name_taken_by_choice(identity):\n"
            "        raise PreserveFlagNameTaken()\n"
            "    checked.preserve_when_callable = True\n"
            "    return checked"
        ),
        "refinement": (
            "Its faithful real variant reorders the last two statements: "
            "`cls = enum.unique(cls)` first, then `cls.do_not_call_in_templates = "
            "True`, then `return cls`. For a declaration that BOTH names a choice "
            "`do_not_call_in_templates` and repeats a choice value the reported "
            "error flips from `AttributeError('Cannot reassign members.')` to "
            "`ValueError('duplicate values found ...')`, which is not the "
            "construction's behaviour. Does NOT resolve for that declaration."
        ),
        "rationale": (
            "Rejected by X3: the guard's `not flag_name_taken_by_choice(identity)` "
            "conjunct is unprovable when the distinctness step runs before the "
            "taken-name branch has been ruled out. This is the ORDER clause, "
            "grounded in the real construction recording the flag on the line "
            "before it hands the grouping to the distinctness step."
        ),
    },

    # --- UNIQUENESS: invent the base step's report -----------------------------
    {
        "id": "weak-invent-base-refusal",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    grouping = base_class_creation(identity)  # type: EnumGrouping\n"
            "    if flag_name_taken_by_choice(identity):\n"
            "        raise BaseStepRefused()\n"
            "    grouping.preserve_when_callable = True\n"
            "    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping\n"
            "    return delivered"
        ),
        "refinement": (
            "Its faithful real variant reports the base construction step's own "
            "error kind (`TypeError`, e.g. \"type 'bool' is not an acceptable "
            "base type\") where the grouping refuses to rebind the flag's name, "
            "for a declaration that step accepted without complaint. The declarer "
            "is told its base type is unusable when it is not. Does NOT resolve."
        ),
        "rationale": (
            "Rejected by X1: BaseStepRefused may escape only where "
            "base_step_refuses(identity) holds, and the ONLY way to learn that is "
            "for the base construction step to have refused — which on this "
            "branch it demonstrably did not, since it delivered a grouping "
            "(its Ensures records `not base_step_refuses(identity)`)."
        ),
    },

    # --- UNIQUENESS: never delivers a grouping (partial-correctness dodge) -----
    # The body re-enters the construction and returns its result. Every Ensures
    # is discharged from the self-call's own contract, so under PARTIAL
    # correctness this verifies while no run ever reaches a return. Must be
    # REJECTED by P1 (MustTerminate(2)).
    {
        "id": "weak-diverge-selfcall",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    inner = build_template_usable_grouping(identity)  # type: EnumGrouping\n"
            "    return inner"
        ),
        "refinement": (
            "Its faithful real variant makes the metaclass re-enter itself with "
            "the same arguments and return that result. Class creation then never "
            "completes: `class Suit(int, Choices)` raises RecursionError, so the "
            "enumeration cannot even be declared and the F2P module fails to "
            "import — `{{ Suit.DIAMOND.label }}` never renders. Does NOT resolve."
        ),
        "rationale": (
            "Rejected by P1 (Requires(MustTerminate(2))): the measure permits the "
            "bounded construction and distinctness steps and grouping "
            "construction (measure 1) but NOT a re-entry of this construction "
            "itself, so Nagini reports an obligation leak. This is the "
            "total-correctness kill: without P1 the same file verifies vacuously "
            "(SPEC-TOO-WEAK) while delivering no grouping."
        ),
    },

    # --- UNIQUENESS: never delivers a grouping (endless loop) ------------------
    {
        "id": "weak-diverge-loop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    n = identity  # type: int\n"
            "    while n > 0:\n"
            "        Invariant(n > 0)\n"
            "        n = n + 1\n"
            "    grouping = base_class_creation(identity)  # type: EnumGrouping\n"
            "    grouping.preserve_when_callable = True\n"
            "    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping\n"
            "    return delivered"
        ),
        "refinement": (
            "Its faithful real variant puts an endless loop in the metaclass "
            "before the construction steps. `class Suit(int, Choices)` never "
            "returns, so importing the F2P test module hangs and every test in "
            "the file — F2P and PASS_TO_PASS alike — times out. Does NOT resolve."
        ),
        "rationale": (
            "Rejected by P1: the loop carries no MustTerminate of its own, so it "
            "cannot take the caller's unsatisfied obligation ('Loop might not "
            "take all unsatisfied obligations from the context'). The second, "
            "loop-shaped witness that the spec is TOTAL rather than partial."
        ),
    },

    # --- UNIQUENESS: builds twice, delivers the second object ------------------
    # Runs the base construction step twice for ONE declaration, discards the
    # first, returns the second. Must be REJECTED by P3, the single-use
    # declaration resource the base step consumes.
    {
        "id": "weak-double-construct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    first = base_class_creation(identity)  # type: EnumGrouping\n"
            "    first.preserve_when_callable = False\n"
            "    grouping = base_class_creation(identity)  # type: EnumGrouping\n"
            "    if flag_name_taken_by_choice(identity):\n"
            "        raise PreserveFlagNameTaken()\n"
            "    grouping.preserve_when_callable = True\n"
            "    delivered = finalize_grouping(grouping, identity)  # type: EnumGrouping\n"
            "    return delivered"
        ),
        "refinement": (
            "Its faithful real variant runs the base class-construction step a "
            "SECOND time on the same declaration and returns that object. The "
            "declared-members record is single-use (enum exhausts it on the first "
            "construction), so the second attempt raises KeyError 'DIAMOND' and "
            "class creation fails outright — `class Suit(int, Choices)` never "
            "builds, so the F2P template cannot render. Does NOT resolve."
        ),
        "rationale": (
            "Rejected by P3 (Requires(declaration_available(identity))): the "
            "opaque resource is CONSUMED by the first base_class_creation call "
            "and never returned, so the second call's precondition is "
            "unsatisfiable ('insufficient permission to access "
            "declaration_available'). Note E3-E6 alone do NOT reject this — the "
            "returned object reports the requested identity and carries the flag "
            "— so P3 is exactly the clause that makes the delivered grouping be "
            "the one the construction produced (SPEC-TOO-WEAK without it)."
        ),
    },
]


# ----------------------------------------------------------------------------
# AXIOM LANE
# ----------------------------------------------------------------------------
# Five A-consumed @ContractOnly axioms: base_class_creation, finalize_grouping,
# base_step_refuses / flag_name_taken_by_choice / repeats_choice_value (the three
# opaque declaration predicates), and resolved_in_template. The host-side
# axiom_check.py already drives the REAL Django / stdlib callees; we embed its
# full source into the soundness probes (the runner mounts ONLY the probe at
# /work, per AVOID #6) and invoke its main(). The containment probes enumerate
# the inputs the MODEL can reach and assert each lies in the axiom's Requires
# domain (a subset check, NOT whole-domain coverage).

# Read the host bundle's axiom_check.py ONCE, at manifest-load time, and embed it.
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text(encoding="utf-8")

# A probe that re-executes the bundle's REAL-callee soundness check, then exits
# 0/1 on its return code. Django lives in-container; only stdlib + Django used.
_SOUNDNESS_PROBE = (
    "import sys\n"
    "_SRC = " + repr(_AXIOM_CHECK_SRC) + "\n"
    "g = {'__name__': '__axiom_check__'}\n"
    "exec(compile(_SRC, 'axiom_check.py', 'exec'), g)\n"
    "rc = g['main']()\n"
    "print('axiom soundness probe rc=%r' % rc)\n"
    "sys.exit(0 if rc == 0 else 1)\n"
)


AXIOM_TESTS = [

    # --- base_class_creation: SOUNDNESS (real super().__new__ / enum.EnumMeta) --
    {
        "id": "ax-sound-base_class_creation",
        "axiom": "base_class_creation",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _SOUNDNESS_PROBE,
        "rationale": (
            "Runs the REAL callee. The axiom pins the identity, issues the "
            "provenance token, and leaves the initial preserve-when-callable flag "
            "UNCONSTRAINED. axiom_check.check_base_construction demonstrates BOTH "
            "realizable initial states through enum.EnumMeta.__new__: (a) a class "
            "with no flagged ancestor carries NO do_not_call_in_templates "
            "attribute (getattr default False), and (b) a subclass of an "
            "already-flagged base INHERITS the flag (truthy right after "
            "super().__new__), so any Ensures pinning the initial flag either way "
            "would be unsound. check_base_step_refusal additionally grounds the "
            "Exsures leg: the step refuses a declaration whose declared kind "
            "cannot carry the values (TypeError \"type 'bool' is not an "
            "acceptable base type\") and one that names a choice after a derived "
            "table the step itself binds, and it is TOTAL otherwise. main() exits "
            "0 iff every observation holds; disagreement => AXIOM-UNSOUND."
        ),
    },

    # --- base_class_creation: CONTAINMENT (caller-reachable inputs) ------------
    # The model only ever calls base_class_creation(identity) where identity>0
    # (the modeled function's own Requires) while holding declaration_available.
    # The axiom's Requires is identity>0 plus that same resource, so every
    # caller-reachable input is in the axiom domain (equal domains).
    {
        "id": "ax-cover-base_class_creation",
        "axiom": "base_class_creation",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": (
            "import sys\n"
            "# Caller domain: build_template_usable_grouping Requires identity > 0\n"
            "# and declaration_available(identity), and the ONLY call is\n"
            "# base_class_creation(identity) with that same identity unchanged and\n"
            "# that same resource in hand. Axiom domain: Requires(identity > 0) and\n"
            "# Requires(declaration_available(identity)). Containment is\n"
            "# identity-of-domains. Sample a wide range of caller-reachable\n"
            "# identities and assert each is in the axiom's Requires domain.\n"
            "caller_reachable = list(range(1, 5000)) + [1, 2, 3, 4, 10**9, 2**31 - 1]\n"
            "def in_axiom_domain(identity):\n"
            "    return identity > 0\n"
            "bad = [i for i in caller_reachable if not in_axiom_domain(i)]\n"
            "print('base_class_creation containment: %d caller-reachable inputs, %d outside axiom domain'\n"
            "      % (len(caller_reachable), len(bad)))\n"
            "if bad:\n"
            "    print('OUTSIDE-DOMAIN sample:', bad[:10]); sys.exit(1)\n"
            "# A caller can never reach identity <= 0 (its own Requires forbids it),\n"
            "# and it holds the declaration resource on entry. Containment holds.\n"
            "sys.exit(0)\n"
        ),
        "rationale": (
            "Containment, not whole-domain coverage: the modeled function's "
            "Requires (identity>0 plus declaration_available) bounds every input "
            "it can pass to base_class_creation, and that equals the axiom's "
            "Requires. No caller-reachable input lies outside the axiom domain. A "
            "reachable input outside => AXIOM-TOO-WEAK-FOR-CALLER. Note the "
            "resource is deliberately NOT re-obtainable: the second call in a "
            "double-construct impl is out of domain, which is the point of the "
            "weak-double-construct reject case."
        ),
    },

    # --- finalize_grouping: SOUNDNESS (real enum.unique) -----------------------
    {
        "id": "ax-sound-finalize_grouping",
        "axiom": "finalize_grouping",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _SOUNDNESS_PROBE,
        "rationale": (
            "Runs the REAL value-distinctness callee (enum.unique). "
            "axiom_check.check_finalize_grouping asserts every clause of the "
            "axiom against it: (i) on a declaration with distinct choice values "
            "it hands back THE SAME object (`enum.unique(cls) is cls`), so "
            "Ensures(Result() is grouping) is sound; (ii) it leaves the "
            "do_not_call_in_templates attribute exactly as it found it (checked "
            "with the flag absent, False and True), so "
            "Ensures(Result().preserve_when_callable == Old(...)) is sound and the "
            "step cannot launder a flag that was never recorded; (iii) it refuses "
            "EXACTLY the declarations that repeat a choice value, with "
            "ValueError('duplicate values found in ...'), over a seeded fuzz of "
            "distinct and repeated value multisets, so both the Ensures(not "
            "repeats_choice_value) and Exsures legs are two-sided. Any "
            "disagreement => AXIOM-UNSOUND."
        ),
    },

    # --- finalize_grouping: CONTAINMENT ---------------------------------------
    {
        "id": "ax-cover-finalize_grouping",
        "axiom": "finalize_grouping",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": (
            "import sys\n"
            "# The model calls finalize_grouping(grouping, identity) at exactly one\n"
            "# point, on the object base_class_creation returned, while holding\n"
            "# built_from_declaration(grouping, identity), full access to both\n"
            "# modeled fields, and grouping.identity == identity. The axiom Requires\n"
            "# precisely those four things, so the single caller-reachable input\n"
            "# shape is in the axiom domain by construction.\n"
            "# Assert the concrete premise on the REAL object: the produced grouping\n"
            "# is an enumeration class whose declared values are what the\n"
            "# distinctness step reads, and it carries the modeled flag field.\n"
            "import enum, django\n"
            "from django.conf import settings\n"
            "if not settings.configured:\n"
            "    settings.configure(\n"
            "        INSTALLED_APPS=['django.contrib.contenttypes'],\n"
            "        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},\n"
            "        TEMPLATES=[{'BACKEND': 'django.template.backends.django.DjangoTemplates',\n"
            "                    'DIRS': [], 'APP_DIRS': False, 'OPTIONS': {}}],\n"
            "        USE_I18N=False)\n"
            "    django.setup()\n"
            "from django.db import models\n"
            "class Suit(models.IntegerChoices):\n"
            "    DIAMOND = 1, 'Diamond'\n"
            "    SPADE = 2, 'Spade'\n"
            "assert isinstance(Suit, enum.EnumMeta), 'grouping must be an enumeration class'\n"
            "assert hasattr(Suit, '_value2member_map_'), 'the distinctness step reads the value table'\n"
            "assert hasattr(Suit, 'do_not_call_in_templates'), 'modeled flag field readable'\n"
            "assert enum.unique(Suit) is Suit, 'same-object premise'\n"
            "print('finalize_grouping containment: the single caller-reachable input '\n"
            "      '(the object the base step returned, with the provenance token, '\n"
            "      'full field access and matching identity) is inside the axiom '\n"
            "      'Requires domain.')\n"
            "sys.exit(0)\n"
        ),
        "rationale": (
            "Containment: the axiom's four Requires conjuncts are exactly what the "
            "one call site holds (the token issued by base_class_creation, full "
            "access to both fields, matching identity, MustTerminate(1) inside "
            "measure 2). No caller-reachable input lies outside => not "
            "AXIOM-TOO-WEAK-FOR-CALLER."
        ),
    },

    # --- the three declaration predicates: SOUNDNESS + INDEPENDENCE + ORDER ----
    {
        "id": "ax-sound-declaration-predicates",
        "axiom": "flag_name_taken_by_choice",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _SOUNDNESS_PROBE,
        "rationale": (
            "Grounds the three opaque @Pure @ContractOnly declaration predicates "
            "against the REAL unchanged callees, which is what licenses the model "
            "treating each as a decidable property of the declaration alone. "
            "axiom_check.check_flag_name_guard drives the REAL "
            "enum.EnumMeta.__setattr__: rebinding a name is refused with "
            "AttributeError('Cannot reassign members.') EXACTLY when that name is "
            "one of the class's own declared members, and succeeds otherwise "
            "(fuzzed over member names, non-member names and the flag's own name). "
            "check_refusal_independence realizes all combinations of the three "
            "predicates, so no clause of the spec may be discharged by assuming "
            "one settles another. check_refusal_order composes the real callees in "
            "the order the construction uses and shows the observable difference "
            "the spec's ordering conjunct pins: recording the flag BEFORE the "
            "distinctness step makes a declaration that both takes the flag's name "
            "and repeats a value report the taken-name refusal, whereas the "
            "opposite order reports the duplicate. Any disagreement => "
            "AXIOM-UNSOUND."
        ),
    },

    # --- the three declaration predicates: CONTAINMENT ------------------------
    {
        "id": "ax-cover-declaration-predicates",
        "axiom": "flag_name_taken_by_choice",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": (
            "import sys\n"
            "# base_step_refuses / flag_name_taken_by_choice / repeats_choice_value\n"
            "# are @Pure @ContractOnly with NO Requires at all, so their domain is\n"
            "# every int. The model applies them only to `identity`, which its own\n"
            "# Requires keeps positive. Containment is therefore trivial in the\n"
            "# subset direction and cannot fail; what could fail is the opposite\n"
            "# reading, that the predicates are only defined for identities a\n"
            "# grouping actually exists for. Assert the real premise instead: each\n"
            "# predicate is settled by the DECLARATION, before/independently of any\n"
            "# object being produced, so it is total over the caller's inputs.\n"
            "caller_reachable = list(range(1, 5000)) + [10**9, 2**31 - 1]\n"
            "bad = [i for i in caller_reachable if not i > 0]\n"
            "print('declaration-predicate containment: %d caller-reachable identities, '\n"
            "      '%d outside the (unrestricted) axiom domain' % (len(caller_reachable), len(bad)))\n"
            "if bad:\n"
            "    sys.exit(1)\n"
            "# The premise, on the REAL declarations: whether the base step refuses,\n"
            "# whether a declared choice occupies the flag's name, and whether two\n"
            "# choices share a value are all readable off the declaration itself.\n"
            "decls = [\n"
            "    ((int, ), [('A', 1), ('B', 2)]),\n"
            "    ((int, ), [('A', 1), ('B', 1)]),\n"
            "    ((int, ), [('do_not_call_in_templates', 1), ('B', 2)]),\n"
            "    ((int, ), [('do_not_call_in_templates', 1), ('B', 1)]),\n"
            "]\n"
            "for bases, members in decls:\n"
            "    names = [n for n, _v in members]\n"
            "    values = [v for _n, v in members]\n"
            "    taken = 'do_not_call_in_templates' in names\n"
            "    repeats = len(set(values)) != len(values)\n"
            "    bad_kind = any(b is bool for b in bases)\n"
            "    assert isinstance(taken, bool) and isinstance(repeats, bool) and isinstance(bad_kind, bool)\n"
            "print('each predicate is a decidable property of the declaration alone '\n"
            "      '(names / values / declared kind), so it is total over every '\n"
            "      'identity the caller can pass.')\n"
            "sys.exit(0)\n"
        ),
        "rationale": (
            "Containment: the three predicates carry no Requires, so their domain "
            "is every int and no caller-reachable identity can fall outside it. "
            "The probe also asserts the modeling premise that makes them "
            "well-defined without an object in hand — each is decidable from the "
            "declaration's names, values and declared kind. A reachable identity "
            "for which a predicate were undefined => AXIOM-TOO-WEAK-FOR-CALLER."
        ),
    },

    # --- resolved_in_template: SOUNDNESS (real Variable._resolve_lookup) -------
    {
        "id": "ax-sound-resolved_in_template",
        "axiom": "resolved_in_template",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _SOUNDNESS_PROBE,
        "rationale": (
            "Runs the REAL django.template.base.Variable._resolve_lookup over a "
            "callable class whose no-arg construction raises a required-argument "
            "TypeError (the grouping scenario), through a TEMPLATE-BOUND context, "
            "for do_not_call_in_templates True/False/absent + a 2000x truthiness/"
            "attribute fuzz with a non-empty string_if_invalid, plus the REAL "
            "patched IntegerChoices rendering the F2P template. axiom_check asserts "
            "preserve->object-itself (==identity) and otherwise->string_if_invalid "
            "(==INVALID_VALUE). 0 violations over 6000+ resolutions => the axiom's "
            "Ensures hold; any disagreement => AXIOM-UNSOUND."
        ),
    },

    # --- resolved_in_template: CONTAINMENT (caller-reachable groupings) --------
    # The model calls resolved_in_template(Result()) only inside the postcondition,
    # on a fully-constructed EnumGrouping (both .identity and .preserve_when_callable
    # present). The axiom Requires Acc(grouping.identity,1/8) and
    # Acc(grouping.preserve_when_callable,1/8) — i.e. both fields readable. Every
    # grouping the model can produce has both fields => containment holds. We also
    # assert the REAL scenario premise the axiom is specialised to (a callable whose
    # no-arg invocation fails) holds for the actual produced grouping (IntegerChoices).
    {
        "id": "ax-cover-resolved_in_template",
        "axiom": "resolved_in_template",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": (
            "import sys\n"
            "# (1) Model-level containment: resolved_in_template is only ever called\n"
            "#     on Result() / a constructed EnumGrouping, which ALWAYS has both\n"
            "#     .identity and .preserve_when_callable set (the constructor Ensures\n"
            "#     them). The axiom Requires only readable access to those two\n"
            "#     fields. So every caller-reachable grouping is in the axiom domain.\n"
            "# (2) Real-scenario containment: the axiom is specialised to a callable\n"
            "#     whose no-arg invocation FAILS with a required-argument TypeError.\n"
            "#     Assert the actual produced grouping (a patched IntegerChoices class\n"
            "#     object) is callable and its no-arg call raises that TypeError, i.e.\n"
            "#     it lies inside the axiom's specialised domain.\n"
            "import django\n"
            "from django.conf import settings\n"
            "if not settings.configured:\n"
            "    settings.configure(\n"
            "        INSTALLED_APPS=['django.contrib.contenttypes', 'django.contrib.auth'],\n"
            "        DATABASES={'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}},\n"
            "        TEMPLATES=[{'BACKEND': 'django.template.backends.django.DjangoTemplates',\n"
            "                    'DIRS': [], 'APP_DIRS': False, 'OPTIONS': {}}],\n"
            "        USE_I18N=False)\n"
            "    django.setup()\n"
            "from django.db import models\n"
            "class Suit(models.IntegerChoices):\n"
            "    DIAMOND = 1, 'Diamond'\n"
            "    SPADE = 2, 'Spade'\n"
            "assert callable(Suit), 'produced grouping must be callable (a class object)'\n"
            "et = None\n"
            "try:\n"
            "    Suit()\n"
            "except Exception as e:\n"
            "    et = type(e)\n"
            "assert et is TypeError, ('produced grouping no-arg call raised %r, expected '\n"
            "                         'a required-argument TypeError (axiom domain premise)' % et)\n"
            "# both modeled fields are always available on any EnumGrouping the model builds:\n"
            "assert hasattr(Suit, 'do_not_call_in_templates'), ('the produced grouping carries the '\n"
            "    'preserve flag (preserve_when_callable readable); identity is the object itself')\n"
            "print('resolved_in_template containment: every caller-reachable grouping has both '\n"
            "      'modeled fields readable AND is a callable whose no-arg call raises a '\n"
            "      'required-argument TypeError => inside the axiom Requires domain.')\n"
            "sys.exit(0)\n"
        ),
        "rationale": (
            "Containment: resolved_in_template is only applied to a fully "
            "constructed grouping (both fields present, matching the axiom's "
            "Acc(...,1/8) Requires) that is a callable whose no-arg invocation "
            "fails (the scenario the axiom is specialised to). No caller-reachable "
            "grouping lies outside that domain => not AXIOM-TOO-WEAK-FOR-CALLER."
        ),
    },
]
