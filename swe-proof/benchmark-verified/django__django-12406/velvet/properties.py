"""properties.py — G-PBT falsification battery for django__django-12406 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside a ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and each ``prove_correct`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (two contracted methods, both pure boolean decisions passed by
value; NO heap, NO ``mut`` binder, NO opaque answer-key — the ``axioms`` region
is empty and each ``ensures`` is a closed boolean expression of the method's own
inputs, so there is nothing to echo):

  (B) relationBlankFlag (modelAllowsBlank : Bool) return (out : Bool)
        ensures out = modelAllowsBlank
      The relation hands the constructed choice field its own declared
      blank-allowed flag — exact identity forwarding, nothing added or dropped.
      One input binder.

  (A) blankChoiceOffered
          (required initialPresent widgetIsRadio blank : Bool) return (out : Bool)
        ensures out = !((required && initialPresent) || (widgetIsRadio && !blank))
      Whether the leading, unfilled "blank" option is presented. It is withheld
      in EITHER of two situations — the field is required and already carries an
      initial value, OR the field renders with a radio widget and a blank
      selection is not permitted — and otherwise offered. ``out`` is ``true``
      exactly when the option is offered. Four input binders.

  The postcondition of (A) is exhaustive: it pins ``out`` UNIQUELY on every one
  of the 2^4 reachable boolean combinations. The two top-level withholding
  disjuncts — (required && initialPresent) and (widgetIsRadio && !blank) — are
  independent clauses, and the second is itself a conjunction that must
  DISCRIMINATE a radio field that permits blank (option kept) from one that does
  not (option withheld). The live attack surface is therefore PARTIAL-DOMAIN /
  CONTROL-FLOW rivals that get one sub-domain wrong: a withholding disjunct
  dropped, or the radio disjunct that ignores the blank observation.

ADVERSARIAL READ of the nagini classes on THIS carrier (case-by-case accounting
in the footer):

  * FRAME / PERMISSION-MUTATION — VACUOUS. Lean and Velvet are referentially
    transparent: every parameter is an immutable value, this bundle declares no
    ``mut`` binder, there is no heap and no aliasing. The nagini sibling itself
    records this class as inapplicable (its scalar inputs are passed by value —
    no ``Acc(x,1/2)`` read-only object input to overwrite). No substitute is
    fabricated.
  * TERMINATION / NON-TERMINATION - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. Every
    frozen impl region is LOOP-FREE (straight-line a single ``return`` over
    immutable values, no loop and no recursion), so there is no control flow
    here to make diverge: a diverging rival cannot be obtained by mutating this
    body, it has to bring a loop of its own. When it does, the semantics refuse
    it. This bundle sets ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The
    ``axioms`` region is empty; each ``ensures`` is a closed boolean expression
    of the method's own inputs (a fully-unfolded decision, not an opaque
    answer-key). The unique satisfier IS the grounded decision, so there is no
    wrong echo to build; the honest controls are the cheapest faithful reshapes.
  * SECOND-POSTCONDITION / CARRIED-LABEL — NO COUNTERPART. The nagini sibling's
    second postcondition pins, when the option is offered, the EXACT label
    carried (``field.placeholder == placeholder_label``); its ``weak-wrong-label``
    rival offers under the right condition but with a different label. This
    carrier models only the observable BOOLEAN — whether the option is offered
    (``out : Bool``, the observer's ``empty_label is not None``) — not the label
    text it carries. There is no label binder to abuse; the clause is not
    modeled here (mapping.md). Reported as an omission in the footer, not faked.
  * PARTIAL-DOMAIN / CONTROL-FLOW — heavily exercised. This is the live reject
    surface for site (A): drop each withholding disjunct, drop the ``!blank``
    half of the radio disjunct so a blank-allowing radio field is wrongly
    withheld, and (added by audit) keep both disjuncts but make the radio one
    wrongly depend on ``initialPresent``, so a fresh blank-forbidding radio field
    is wrongly offered. Site (B) is an identity forwarding over a single ``Bool``
    binder, so its wrong-impl space is FINITE and is attacked exhaustively: all
    three non-identity functions of one ``Bool`` ship as rivals — invert, collapse
    to constant false (the pre-image skeleton), and (added by audit) collapse to
    constant true.

WITNESS MECHANICS ON THIS BUNDLE. Both frozen impls are STRAIGHT-LINE closed
boolean expressions: each extracted tester reduces fully under ``decide``. Each
reject rival carries a machine-checked refutation ``witness`` — a Velvet tester
statement ``<method>Tester <bools> = false`` at ONE concrete input, checked in a
file whose ``prove_correct`` block has been stripped so no tactic script can
mask the verdict. ``Bool`` has ``DecidableEq`` built in, so the tester
derivations add no instance and the witnesses introduce no ``axiom`` / ``sorry``
/ ``native_decide``. Every witness states its refutation at literal booleans, so
no witness binds a hypothesis and the consistency probe is vacuous for all of
them. Both halves were checked out-of-band with ``scripts/lean_verify.sh``:
every witness ELABORATES against its rival and FAILS (``decide`` proves the
proposition false) against the frozen solution.

FORGERY CONTROL (re-derived by audit, 14 extra builds). A gold-side failure is
admissible evidence only if its exit code TRACKS THE CLAIM. Every one of the
seven gold-side signatures here is a plain evaluation — ``Tactic `decide` proved
that the proposition <tester> <bools> = false is false`` — i.e. the kernel
reduced the tester to a literal, not a stuck reduction, a missing identifier or
a type error. That was then confirmed rather than read: for all seven witnesses
the claim was FLIPPED (``= false`` -> ``= true``) and rebuilt on both subjects,
and the exit codes INVERT exactly — flipped-on-gold elaborates (exit 0) while
flipped-on-rival fails (exit 1) with the symmetric ``decide`` evaluation. So
gold's exit code carries full information about the claim at every witness
point, and a witness asserting the frozen impl is CORRECT there could not have
been recorded as a refutation.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom`` and no deep-model
reference; both decisions are R-refinements of the real boolean observations,
validated by ``conformance_check.py`` (G-CONF), not axiomatized. This gate
ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-12406"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Impl-region anchors. Each lies ENTIRELY inside one `-- impl-start` /
# `-- impl-end` region and is unique in Solution.lean (both facts asserted at
# load), so every _swap keeps same_spec and leaves the `prove_correct`
# obligation statements byte-identical.
# ---------------------------------------------------------------------------

# Site B impl: the frozen identity forwarding.
_S_B = "    return modelAllowsBlank\n"

# Site A impl: the frozen closed boolean decision.
_S_A = "    return !((required && initialPresent) || (widgetIsRadio && !blank))\n"

assert _BASE.count(_S_B) == 1, "site B impl region drifted from expected text"
assert _BASE.count(_S_A) == 1, "site A impl region drifted from expected text"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery:
# ---- `<method>Tester <bools> = false` says the extracted program's result
# ---- violates the postcondition at that concrete input. Checked in a file
# ---- whose `prove_correct` blocks are stripped. `Bool` derives `DecidableEq`,
# ---- so no instance is added.
def _witness(method, call):
    return (
        f"extract_program_for {method}\n"
        f"prove_precondition_decidable_for {method}\n"
        f"prove_postcondition_decidable_for {method}\n"
        f"derive_tester_for {method}\n\n"
        f"example : {call} = false := by\n  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the boolean value identical on every
    # input; the reproof stays the frozen `loom_solve` (checked out-of-band), so
    # the proof body is left byte-identical.
    # =====================================================================
    {
        "id": "pos-control-demorgan-offered",
        "kind": "soundness",
        "expect": "verify",
        # Reshape (site A): compute the OFFERED flag as the CONJUNCTION of the
        # two situations NOT holding (De Morgan of the withholding disjunction:
        # !(X || Y) = !X && !Y). Same boolean value on every input.
        "module": _swap(
            _BASE, _S_A,
            "    return (!(required && initialPresent)) "
            "&& (!(widgetIsRadio && !blank))\n"),
        "rationale": "the offered flag spelled as the conjunction of the two "
                     "withholding situations NOT holding (!X && !Y) is "
                     "definitionally the negated disjunction !(X || Y) the "
                     "post-image pins, so `out = !((required && initialPresent) "
                     "|| (widgetIsRadio && !blank))` still discharges; a "
                     "structurally-different correct reshape must verify, else "
                     "SPEC-TOO-STRONG (over-fit to the negated-disjunction "
                     "spelling). Mirrors the nagini De Morgan positive control.",
    },
    {
        "id": "pos-control-forward-branch",
        "kind": "soundness",
        "expect": "verify",
        # Reshape (site B): forward the flag through an explicit branch instead
        # of a bare return; same value (modelAllowsBlank) on both arms.
        "module": _swap(
            _BASE, _S_B,
            "    if modelAllowsBlank then\n"
            "      return true\n"
            "    else\n"
            "      return false\n"),
        "rationale": "a branch-shaped forwarding (return true/false per "
                     "modelAllowsBlank) is value-equal to `return "
                     "modelAllowsBlank` on both arms, so `out = modelAllowsBlank` "
                     "still discharges; a correct reshape must verify, else "
                     "SPEC-TOO-STRONG. Mirrors the nagini site-2 forward-branch "
                     "positive control.",
    },

    # =====================================================================
    # ADMISSIBILITY — neither method carries a `require` clause (the
    # pre-conditions region is empty), so the nagini sibling's "the granted
    # permission admits a normal call" probe is degenerate here (every input is
    # in-domain). The residual admissibility risk on a total-domain spec is that
    # the decision is DEGENERATE at the interesting point — a decision that never
    # separated the F2P withhold-case from the neighbouring offer-case would read
    # like a live one. This case discharges an in-region assert pinning that the
    # modeled decision genuinely forks on the F2P boundary: a radio field that
    # forbids a blank selection WITHHOLDS the option (= false), while an
    # otherwise-identical non-radio field OFFERS it (= true). The rest of the
    # impl is kept verbatim so the method's own obligation still discharges; the
    # frozen `loom_solve` closes the assert VC too (checked out-of-band).
    # =====================================================================
    {
        "id": "admiss-radio-boundary-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _S_A,
            "    assert (with_name_prefix `assert\n"
            "      ((!((false && false) || (true && !false)) = false) ∧\n"
            "       (!((false && false) || (false && !false)) = true)))\n"
            "    return !((required && initialPresent) "
            "|| (widgetIsRadio && !blank))\n"),
        "rationale": "the decision is satisfiable AND non-degenerate at the F2P "
                     "boundary: a radio field that forbids a blank selection "
                     "WITHHOLDS the option (= false), yet an otherwise-identical "
                     "non-radio field OFFERS it (= true), so the radio "
                     "withholding rule really does fork on the widget observation "
                     "— exactly the F2P discriminating point. The in-region "
                     "assert must discharge (else the boundary would be "
                     "degenerate / the obligation vacuous); the impl is kept "
                     "verbatim so the ensures still discharges too. Re-aims the "
                     "nagini admissibility control (which asserted the granted "
                     "permission admits a normal call) at the total-domain "
                     "degeneracy risk this carrier has instead.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is straight-line (its witness reduces under
    # `decide`), refuted at a concrete input by a witness that ELABORATES against
    # the rival and FAILS on the frozen solution, and carries the refinement
    # argument that its faithful real counterpart would NOT resolve the F2P.
    # Site-A tester argument order:
    #   required  initialPresent  widgetIsRadio  blank
    # =====================================================================
    {
        "id": "weak-drop-radio-clause",
        "kind": "uniqueness",
        "expect": "reject",
        # THE site-A discriminating delta, dropped. Withhold ONLY for
        # required-with-initial; the radio/blank situation is not considered, so
        # a radio field that forbids a blank selection still OFFERS the option.
        # This is the site-A pre-image skeleton (Solution_prepatch.lean).
        "module": _swap(
            _BASE, _S_A,
            "    return !(required && initialPresent)\n"),
        "refinement": "this IS the pre-change site-A behaviour: the withholding "
                      "decision lacks the radio rule entirely. Its faithful real "
                      "counterpart is the unchanged repo, under which a radio "
                      "choice field that forbids a blank selection still presents "
                      "the leading blank option — exactly what the failing tests "
                      "for a non-blank radio foreign key and the radio-blank "
                      "subcase assert it must NOT. It would NOT resolve; the "
                      "precise change the spec senses (G-DIFF).",
        "rationale": "REJECT from the ensures on the F2P sub-domain "
                     "{not (required && initialPresent), widgetIsRadio, "
                     "not blank}: the post-image withholds (out = false) for a "
                     "radio field forbidding blank, but the rival offers "
                     "(out = true). Refuted at (required=F, initialPresent=F, "
                     "widgetIsRadio=T, blank=F) — the radio-no-blank cell the fix "
                     "adds.",
        "witness": _witness(
            "blankChoiceOffered",
            "blankChoiceOfferedTester false false true false"),
    },
    {
        "id": "weak-drop-required-clause",
        "kind": "uniqueness",
        "expect": "reject",
        # Mirror omission: keep ONLY the radio disjunct, drop required-with-
        # initial. Correct on radio inputs but wrong on a required, pre-filled,
        # non-radio field: rival offers where the spec withholds.
        "module": _swap(
            _BASE, _S_A,
            "    return !(widgetIsRadio && !blank)\n"),
        "refinement": "dropping the required-with-initial withholding re-offers "
                      "the empty option for a mandatory field that already "
                      "carries a pre-filled value — the long-standing behaviour "
                      "this branch has always guarded (present pre-patch too). A "
                      "faithful real patch would regress that required+initial "
                      "behaviour exercised across the broad valid-form P2P suite, "
                      "so it would NOT resolve / would break P2P.",
        "rationale": "REJECT from the ensures on the required+initial sub-domain "
                     "{required, initialPresent, not widgetIsRadio}: the "
                     "post-image withholds (out = false) but the rival offers "
                     "(out = true). Refuted at (required=T, initialPresent=T, "
                     "widgetIsRadio=F, blank=F) — varies required/initialPresent "
                     "true, the binders the radio-clause rivals hold false.",
        "witness": _witness(
            "blankChoiceOffered",
            "blankChoiceOfferedTester true true false false"),
    },
    {
        "id": "partial-domain-radio-ignores-blank",
        "kind": "uniqueness",
        "expect": "reject",
        # Subtle wrong sub-domain: withhold for ALL radio (use widgetIsRadio in
        # place of `widgetIsRadio && !blank`). Correct on radio-no-blank and on
        # every non-radio input, but WRONG on radio-with-blank: a blank-allowing
        # radio field must OFFER the option, this rival withholds it. Attacks
        # exactly the `!blank` half of the new disjunct.
        "module": _swap(
            _BASE, _S_A,
            "    return !((required && initialPresent) || widgetIsRadio)\n"),
        "refinement": "withholding the option for EVERY radio field (even one "
                      "whose model permits a blank selection) drops the blank "
                      "choice a blank-allowing radio foreign key must show — "
                      "exactly the blank-permitted radio subcase the failing "
                      "tests expect to present the leading blank option. A "
                      "faithful real patch would fail those, so it would NOT "
                      "resolve.",
        "rationale": "REJECT from the ensures on the radio-with-blank sub-domain "
                     "{not (required && initialPresent), widgetIsRadio, blank}: "
                     "the post-image offers (out = true) but the rival withholds "
                     "(out = false). Refuted at (required=F, initialPresent=F, "
                     "widgetIsRadio=T, blank=T) — varies blank true, the binder "
                     "the radio-no-blank rival holds false, isolating the "
                     "`!blank` half of the new disjunct.",
        "witness": _witness(
            "blankChoiceOffered",
            "blankChoiceOfferedTester false false true true"),
    },
    {
        "id": "weak-radio-conditioned-on-initial",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (attack D). The four ported site-A rivals all leave the
        # radio withholding rule's INDEPENDENCE from the other disjunct's binders
        # unattacked: each either drops a whole disjunct or drops the `!blank`
        # half. This rival keeps both disjuncts and the `!blank` half intact but
        # narrows the radio rule with an extra conjunct — it withholds for a
        # radio field forbidding blank ONLY when an initial value is also
        # present. Correct on all four points the ported witnesses use, wrong on
        # a radio, blank-forbidding field with NO initial value: the post-image
        # withholds, the rival offers.
        "module": _swap(
            _BASE, _S_A,
            "    return !((required && initialPresent) "
            "|| (widgetIsRadio && !blank && initialPresent))\n"),
        "refinement": "gating the radio withholding rule on an initial value "
                      "being present makes it fire only for pre-filled fields, "
                      "so a fresh (unfilled) radio choice field that forbids a "
                      "blank selection still presents the leading blank option. "
                      "That is precisely the shape the failing tests exercise — "
                      "they build a fresh form with no initial data and require "
                      "NO leading blank row for the blank-forbidding radio "
                      "relation — so a faithful real counterpart would NOT "
                      "resolve the F2P.",
        "rationale": "REJECT from the ensures on the sub-domain {widgetIsRadio, "
                     "not blank, not initialPresent}: the post-image withholds "
                     "(out = false) because the radio disjunct depends on NEITHER "
                     "of the first disjunct's binders, but the rival offers "
                     "(out = true). Refuted at (required=T, initialPresent=F, "
                     "widgetIsRadio=T, blank=F) — a fifth site-A point, and the "
                     "only one holding required true with initialPresent false, "
                     "which no ported witness reaches.",
        "witness": _witness(
            "blankChoiceOffered",
            "blankChoiceOfferedTester true false true false"),
    },
    {
        "id": "support-always-offer",
        "kind": "uniqueness",
        "expect": "reject",
        # Unconditional offer: never withhold. Re-introduces BOTH withholding
        # situations at once. Refuted on the required-with-initial sub-domain, at
        # a point that also varies `blank` true so no site-A witness holds every
        # binder fixed.
        "module": _swap(
            _BASE, _S_A,
            "    return true\n"),
        "refinement": "always offering the option ignores BOTH withholding "
                      "situations: a required pre-filled field and a non-blank "
                      "radio field would both wrongly present the empty option. "
                      "It fails the non-blank radio foreign-key test (which "
                      "expects NO leading blank) and the required+initial valid-"
                      "form P2P paths — resolves nothing.",
        "rationale": "REJECT from the ensures on any withholding sub-domain: on "
                     "(required=T, initialPresent=T, widgetIsRadio=F, blank=T) "
                     "the post-image withholds (out = false, the required+initial "
                     "situation) but the rival offers (out = true). Refuted at a "
                     "point that also holds blank true, so the four site-A "
                     "witnesses jointly vary all four binders.",
        "witness": _witness(
            "blankChoiceOffered",
            "blankChoiceOfferedTester true true false true"),
    },
    {
        "id": "weak-flip-blank",
        "kind": "uniqueness",
        "expect": "reject",
        # Site B: forward the NEGATION of the model's blank-allowed flag.
        "module": _swap(
            _BASE, _S_B,
            "    return !modelAllowsBlank\n"),
        "refinement": "inverting the forwarded blank flag flips the downstream "
                      "radio choice field's option presence: a blank-allowing "
                      "relation would LOSE the option and a non-blank one would "
                      "GAIN it — the exact inverse of the blank / non-blank "
                      "foreign-key-with-radio tests. A faithful real patch "
                      "resolves nothing.",
        "rationale": "REJECT from `out = modelAllowsBlank`: `!modelAllowsBlank` "
                     "contradicts the pinned identity on every input. Refuted at "
                     "modelAllowsBlank=F (post-image false, rival true) — varies "
                     "the binder false, distinct from the const-false rival's "
                     "true point.",
        "witness": _witness(
            "relationBlankFlag",
            "relationBlankFlagTester false"),
    },
    {
        "id": "weak-const-false",
        "kind": "uniqueness",
        "expect": "reject",
        # Site B pre-image skeleton (Solution_prepatch_2.lean): the relation did
        # NOT forward the flag, so the field always behaved as though a blank
        # selection were not permitted (constant false). Diverges when the model
        # DOES permit a blank.
        "module": _swap(
            _BASE, _S_B,
            "    return false\n"),
        "refinement": "this IS the pre-change site-B behaviour: the relation "
                      "does not forward the model's blank-allowed flag, so the "
                      "constructed choice field defaults to blank-not-permitted. "
                      "Its faithful real counterpart is the unchanged repo, which "
                      "withholds the option for a blank-allowing radio foreign "
                      "key — exactly what the blank foreign-key-with-radio test "
                      "asserts it must NOT — so it would NOT resolve the F2P.",
        "rationale": "REJECT from `out = modelAllowsBlank`: when modelAllowsBlank "
                     "is true the rival returns false — contradiction on the "
                     "blank-permitted subdomain (the discriminating F2P case). "
                     "Refuted at modelAllowsBlank=T, distinct from the flip "
                     "rival's false point.",
        "witness": _witness(
            "relationBlankFlag",
            "relationBlankFlagTester true"),
    },
    {
        "id": "weak-const-true",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT (attack D). Site B is a Bool -> Bool identity, so there
        # are exactly FOUR total functions of its one binder: the frozen identity,
        # the inversion (weak-flip-blank), constant false (weak-const-false) and
        # constant TRUE — which the port left unattacked. Completing the four makes
        # the site-B lane exhaustive by enumeration rather than by argument: with
        # all three non-frozen functions rejected, `out = modelAllowsBlank` pins
        # the forwarding uniquely over its whole domain.
        "module": _swap(
            _BASE, _S_B,
            "    return true\n"),
        "refinement": "hard-coding the forwarded flag to permitted makes every "
                      "relation look as though a blank selection were allowed, so "
                      "a relation that does NOT permit one still lets its choice "
                      "field present the leading blank option. That is the "
                      "opposite regression from the pre-change skeleton and breaks "
                      "the non-blank foreign-key-with-radio expectation (which "
                      "requires NO leading blank row), so a faithful real "
                      "counterpart would NOT resolve the F2P.",
        "rationale": "REJECT from `out = modelAllowsBlank`: when modelAllowsBlank "
                     "is false the rival returns true — contradiction on the "
                     "blank-forbidden subdomain. Refuted at modelAllowsBlank=F. "
                     "Together with weak-flip-blank and weak-const-false this "
                     "exhausts all three non-frozen Bool -> Bool functions, so the "
                     "site-B forwarding is pinned by enumeration.",
        "witness": _witness(
            "relationBlankFlag",
            "relationBlankFlagTester false"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The nagini sibling has 10 SPEC cases (2 soundness
# positives, 1 admissibility, 7 uniqueness rivals; AXIOM_TESTS is G-AX's job and
# dropped here) over TWO modeled functions:
#   * configure_placeholder(field, placeholder_label, required, initial_present,
#     is_radio, blank) -> None, mutating field.placeholder, with a TWO-clause
#     postcondition: (C1) present iff placeholder_offered(...), and (C2) when
#     offered, field.placeholder == placeholder_label (the carried label);
#   * derived_field_emptiness_flag(model_blank) -> bool, ensures Result ==
#     model_blank (identity forwarding).
# THIS bundle models the same two behaviours as two pure boolean methods —
# blankChoiceOffered (site A, the offered-iff decision, mapping.md observable
# `empty_label is not None`) and relationBlankFlag (site B, the identity
# forwarding) — but with NO carried-label output (site A returns only the
# observable Bool, not the label), so the nagini C2 clause has no counterpart.
# Every nagini case is accounted for below.
#
#   nagini case                       -> here                                  disposition
#   --------------------------------------------------------------------------------------
#   pos-control-demorgan-offered      -> pos-control-demorgan-offered          PORTED
#   pos-control-forward-branch        -> pos-control-forward-branch            PORTED
#   admiss-site1-read-field           -> admiss-radio-boundary-nondegenerate   RE-AIMED
#   weak-drop-radio-clause            -> weak-drop-radio-clause                PORTED
#   weak-drop-required-clause         -> weak-drop-required-clause            PORTED
#   partial-domain-radio-ignores-blank-> partial-domain-radio-ignores-blank    PORTED
#   weak-wrong-label                  -> (none)                                NO COUNTERPART (C2 unmodeled)
#   weak-flip-blank                   -> weak-flip-blank                       PORTED
#   weak-const-false                  -> weak-const-false                      PORTED
#   support-always-offer              -> support-always-offer                  PORTED
#   (no nagini counterpart)           -> weak-radio-conditioned-on-initial      ADDED BY AUDIT
#   (no nagini counterpart)           -> weak-const-true                        ADDED BY AUDIT
#
# 8 ported, 1 re-aimed, 1 no-counterpart, 2 added by audit.
#
# ADDED BY AUDIT (weak-const-true, attack D): site B is a Bool -> Bool identity,
#   so its binder admits exactly FOUR total functions — the frozen identity plus
#   three wrong ones. The port shipped two of the three (invert, constant false)
#   and left constant TRUE unattacked, which is a coverage gap that argument
#   cannot close but enumeration can. With the third landed, every non-frozen
#   function of the site-B domain is refuted, so `out = modelAllowsBlank` is
#   pinned exhaustively rather than merely "from both directions". Refuted at
#   modelAllowsBlank=F; witness rebuilt both ways (rival exit 0; gold exit 1,
#   `decide` proves `relationBlankFlagTester false = false` is false), and the
#   flipped claim inverts both exit codes.
#
# ADDED BY AUDIT (weak-radio-conditioned-on-initial, attack D): the four ported
#   site-A rivals each drop a whole withholding disjunct or the `!blank` half of
#   the radio one, so all four leave the radio rule's INDEPENDENCE from the
#   first disjunct's binders unprobed. The added rival keeps both disjuncts and
#   `!blank` intact and instead narrows the radio rule with an extra
#   `&& initialPresent` conjunct, refuted at (T,F,T,F) — a fifth site-A point,
#   and the only one holding required true with initialPresent false. Its
#   witness was rebuilt both ways during the audit: it elaborates against the
#   rival (exit 0) and fails on the frozen solution with a SEMANTIC refutation
#   (`decide` proves `blankChoiceOfferedTester true false true false = false`
#   is false; exit 1).
#
# PORTED (8): the site-A partial-domain rivals (drop-radio, drop-required,
#   radio-ignores-blank, always-offer), the site-B forwarding rivals (flip,
#   const-false), and both positive controls carry across intact. Only the
#   carrier changes: nagini mutated `field.placeholder` (present iff offered),
#   this bundle returns the offered Bool directly; nagini forwarded through an
#   Optional[int]-shaped None/label, this bundle forwards a Bool. Each carries
#   its nagini refinement argument (pre-image skeleton or partial-domain
#   divergence fails the same F2P). weak-drop-radio-clause and weak-const-false
#   are exactly Solution_prepatch.lean / Solution_prepatch_2.lean (G-DIFF).
# RE-AIMED (admiss-site1-read-field -> admiss-radio-boundary-nondegenerate): the
#   nagini admissibility control asserted the granted permission Acc(field.
#   placeholder) admits a normal call. This carrier has NO precondition (no
#   permission system, referentially transparent), so that probe is degenerate.
#   It is re-aimed at the residual total-domain risk — a DEGENERATE decision that
#   never forks on the F2P boundary — via an in-region assert that the radio
#   withholding rule genuinely forks (radio+no-blank withholds; the same field
#   non-radio offers).
# NO COUNTERPART (weak-wrong-label): the nagini rival offers under the right
#   condition but carries a DIFFERENT label (placeholder_label + 1), attacking
#   the second postcondition clause (offered => field.placeholder ==
#   placeholder_label). This carrier models only the observable BOOLEAN — whether
#   the leading blank option is offered (`out`, the observer's `empty_label is
#   not None`) — not the label text it carries (mapping.md §1: `out` of
#   blankChoiceOffered is `empty_label is not None`, a Bool). There is no label
#   binder to abuse and no C2 clause to violate. Omitted because the modeled
#   surface does not include the carried-label behaviour, NOT because it was hard
#   to prove.
# FRAME / PERMISSION-MUTATION: VACUOUS. Referentially-transparent backend, no
#   `mut` binder, no heap, no aliasing, no permission system. The nagini sibling
#   itself records this class as N/A (its scalar inputs are passed by value; no
#   Acc(x,1/2) read-only object). No substitute fabricated.
# DIVERGENCE / NON-TERMINATION - the class is INAPPLICABLE to this impl and
#   CLOSED BY THE SEMANTICS against any rival that manufactures it. Every
#   frozen impl region is LOOP-FREE (straight-line a single ``return`` over
#   immutable values, no loop and no recursion), so there is no control flow
#   here to make diverge: a diverging rival cannot be obtained by mutating this
#   body, it has to bring a loop of its own. When it does, the semantics refuse
#   it. This bundle sets ``loom.semantics.termination "total"`` AND carries
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
#
# BINDER / CLAUSE / POINT COVERAGE. pts = 7 distinct input points (five site-A,
#   two site-B; the site-B pair is reused by the third site-B rival, see below).
#   Site A blankChoiceOffered — four binders over the five reject witnesses
#   (drop-radio / drop-required / radio-ignores-blank / radio-conditioned-on-
#   initial / always-offer):
#     required        — F / T / F / T / T:                                 VARIED
#     initialPresent  — F / T / F / F / T:                                 VARIED
#     widgetIsRadio   — T / F / T / T / F:                                 VARIED
#     blank           — F / F / T / F / T:                                 VARIED
#   The variation is MEANINGFUL, not two spellings of one point, and the
#   machine-checked form of that is: the five points are pairwise DISTINCT cells
#   of the 2^4 post-image, and the five rivals' DISAGREEMENT SETS (the cells where
#   rival and post-image differ) are pairwise distinct too — {(F,F,T,F),(F,T,T,F),
#   (T,F,T,F)} / {(T,T,F,F),(T,T,F,T),(T,T,T,T)} / {(F,F,T,T),(F,T,T,T),(T,F,T,T)}
#   / {(F,F,T,F),(T,F,T,F)} / the 7 cells where the post-image withholds. So each
#   rival is refuted inside a region no other rival's witness inhabits.
#   (A stronger claim — that flipping ANY single binder at a witness point changes
#   the spec's verdict for that rival — was carried here and is FALSE, corrected by
#   audit: e.g. at drop-radio's (F,F,T,F), flipping `required` to (T,F,T,F) leaves
#   the post-image withholding and the rival still wrong, so that flip changes
#   nothing. 11 of the 20 (rival, binder) flips are counterexamples. Exhaustiveness
#   is established by the 16-cell probe below, not by single-binder sensitivity.)
#   POINTWISE EXHAUSTIVENESS, measured (audit): an impl that flips the frozen
#   decision at EXACTLY ONE of the 16 input cells — `xor <frozen decision>
#   (required == b0 && initialPresent == b1 && widgetIsRadio == b2 && blank == b3)`
#   — was built for all 16 cells and ALL 16 were REJECTED (exit 1). The site-A
#   ensures therefore pins `out` uniquely at every reachable input, so no wrong
#   sub-domain is left unsensed; site B has only 4 total Bool->Bool functions and
#   the three non-frozen ones (invert, const false, const true) are all rejected.
#   Both top-level withholding disjuncts are attacked: (required && initialPresent) by
#   drop-required and always-offer; (widgetIsRadio && !blank) by drop-radio
#   (drops it), radio-ignores-blank (drops its `!blank` half, the F2P
#   discriminator) and radio-conditioned-on-initial (keeps both halves but makes
#   the disjunct wrongly depend on initialPresent). Both positives and the
#   admissibility assert defend the clause.
#   Site B relationBlankFlag — one binder over the THREE reject witnesses:
#     modelAllowsBlank — F (flip) / T (const-false) / F (const-true):      VARIED,
#   and the sole ensures is attacked EXHAUSTIVELY: the binder admits four total
#   Bool -> Bool functions and all three non-frozen ones are shipped as rivals
#   (invert everywhere; collapse to constant false, wrong on the true subdomain;
#   collapse to constant true, wrong on the false subdomain). const-true reuses
#   the flip rival's refutation point, which costs nothing — with one binder there
#   are only two points, and what matters at site B is that the FUNCTION space is
#   exhausted, not that the point set grows.
#   Every witness states its refutation at literal booleans, so none binds a
#   hypothesis (consistency probe vacuous).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
# axiom and no deep-model reference (both decisions are R-refinements checked by
# G-CONF), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
