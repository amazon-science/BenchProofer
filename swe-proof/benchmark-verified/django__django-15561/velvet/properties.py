"""properties.py — G-PBT falsification battery for django__django-15561 (velvet).

NOT a Velvet module; a manifest the G-PBT gate executes and stamps with a
verdict. Each SPEC case is a full ``Solution.lean`` variant that shares the
FROZEN spec byte-for-byte (region surgery: only text inside the ``-- impl-start``
/ ``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body — the
two regions the consumer spec view elides — is changed, so ``markers.same_spec``
holds and the ``prove_correct decideSchemaAlteration`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation, checked by the
real verifier. ``expect="verify"`` passes iff (in scope AND verifies);
``expect="reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method, two read-only input binders):

  decideSchemaAlteration (a b : FieldDef) return (out : Bool)
    ensures out = schemaAlterationNeeded a b            [clause A, the whole pin]

  ``FieldDef`` observes a field definition through three components — its quoted
  column name (``quotedColumn``), its schema-relevant identity (``schemaIdentity``),
  and its presentation-only enumerated choices (``choices``). ``schemaAlterationNeeded``
  is a TRANSPARENT total function of the two inputs:

    schemaAlterationNeeded a b =
      decide (a.quotedColumn ≠ b.quotedColumn) || decide (a.schemaIdentity ≠ b.schemaIdentity)

  A rewrite is required EXACTLY when the quoted column name differs or the
  schema-relevant identity differs; a difference confined to the presentation-only
  ``choices`` component NEVER requires a rewrite, so ``choices`` is observable but
  not consulted. The post-image is grounded entirely in the inputs (a plain
  ``def`` over two ``FieldDef`` records that derive ``DecidableEq``; the ``axioms``
  region is empty), so a wrong impl cannot verify by echoing an opaque answer-key —
  it must reproduce the decision.

  THE BEHAVIOURAL DISCRIMINATOR. A field replacement that changes only the
  presentation-only ``choices`` component must be treated as requiring no column
  rewrite; a change to the quoted column name or the schema-relevant identity must
  still require one. The pre-change decision consulted the presentation-only
  component as though it were schema-relevant, so a ``choices``-only difference
  wrongly forced a column rewrite. The failing test keys on exactly this
  observable (a ``choices``-only field replacement performs no schema work). Clause
  A senses it: ``out = schemaAlterationNeeded a b`` at every input, and
  ``schemaAlterationNeeded`` does not read ``choices``.

CARRIER NARROWING (this bundle vs the nagini sibling). The nagini sibling
contracts TWO functions and pins several facts: (SET) a 12-element schema-irrelevant
attribute set stated by EXACT set equality (with the presentation-only attribute
now a pinned member), and (DEC) a rebuild decision computed by scanning the two
kwargs bags, ignoring the schema-irrelevant attributes and comparing the rest plus
a structural (non-kwargs) difference flag. This bundle models ONLY the purely
functional core the fix's behavioural delta turns on — the rebuild DECISION — over
a projected ``FieldDef`` whose ``schemaIdentity`` component has ALREADY had the
schema-irrelevant attributes stripped by the unchanged projection callee
(mapping.md §2.1), and whose presentation-only ``choices`` component is carried
separately and NOT consulted. The gold patch's behavioural delta is exactly that a
``choices``-only difference no longer requires a rewrite, and that is the entire
modeled surface here.

Consequently the nagini rivals attached to the STRUCTURE of the attribute set
(dropping a legacy attribute, or over-populating the set) have no direct
counterpart: the set-construction is folded into the unchanged projection callee
(exercised by G-CONF, not modeled here), and the loop-index off-by-one rivals have
no counterpart because the decision is a flat disjunction over two aggregate
components, not an indexed scan. What the two carriers SHARE is the load-bearing
delta — whether the presentation-only component is (wrongly) consulted — plus the
two schema-relevant components each being genuinely consulted. Every nagini case is
accounted for in the footer.

ADVERSARIAL READ of the nagini classes on this carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling's mandatory
    ``frame-mut-non_db-write-perm`` rival demands FULL (write) permission on the
    read-only ``Acc(set_pred(non_db),1/2)`` input and is rejected for INSUFFICIENT
    PERMISSION. Lean and Velvet are referentially transparent: both inputs are
    immutable values (no ``mut`` binder), there is no heap, no aliasing and no
    fractional-permission system to subvert. There is no read-only input to
    over-claim, so the class is vacuous; no substitute probe is fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A as an attack. Clause A's post-image is
    ``schemaAlterationNeeded a b``, a transparent total function of the method's own
    arguments; there is no answer-key to echo. The nagini file makes the same
    observation (``disagrees_relevant`` is a fully-unfolded existential over the
    args, not an opaque oracle). The cheapest CORRECT impl is carried as a positive
    control instead.
  * ADMISSIBILITY — the method carries NO ``require`` clause (precondition ≡ True),
    so the nagini admissibility probe's "a normal / F2P-shaped input satisfies the
    precondition" half is vacuous. Re-aimed at the residual total-domain risk: that
    the one-clause post-image is SATISFIABLE by a gold-shaped computation (else
    SPEC-UNSATISFIABLE) — witnessed by the frozen impl discharging clause A.

CARRIER NOTE — why this port refutes at CONCRETE literals (no conditioning). The
carrier is fully transparent: ``FieldDef`` is a three-``String``-field structure
deriving ``DecidableEq``, and clause A's post-image ``schemaAlterationNeeded`` is a
plain ``def`` over it. So every reject witness reaches the method's contract through
Velvet's own tester machinery (``decideSchemaAlterationTester a b``) at concrete
``FieldDef`` literals and closes by ``decide`` — no hypothesis about an opaque term
is needed, so no witness binds anything and the gate's consistency probe has nothing
to check. The frozen solution is STRAIGHT-LINE and also reduces under ``decide``;
each witness fails against gold purely because gold SATISFIES the spec at that input
(the tester returns ``true``, so ``... = false`` is provably false), which is the
required discriminator. Checked in a file whose ``prove_correct`` block is stripped,
so no tactic script can mask the verdict. Every reject witness below was run against
both the rival (elaborates) and the frozen solution (fails) with two real builds.

DIVERGENCE LANE - the class is INAPPLICABLE to this impl and CLOSED BY THE
SEMANTICS against any rival that manufactures it. The frozen impl is LOOP-FREE
(straight-line a single ``return`` over immutable values, no loop and no
recursion), so there is no control flow here to make diverge: a diverging rival
cannot be obtained by mutating this body, it has to bring a loop of its own.
When it does, the semantics refuse it. This bundle sets
``loom.semantics.termination "total"`` AND carries ``open TotalCorrectness``,
and the ``open`` is the line that actually selects the semantics: both
namespaces define ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and
the ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
two lines have to move together and they do here. Under the total scope a
postcondition is claimed of ALL runs and not only of terminating ones, so a
spliced loop owes a descent obligation ``measure b' < measure b``. Re-measured
on this bundle with a real build: a ``while spin > 0 do spin := spin`` prefix
carrying ``decreasing spin`` is REJECTED on the measure's own goal (``case
«decreasing_1: spin» ... ⊢ spin < spin``). Dropping the clause rather than
faking it is refused even earlier, by the elaborator's own check (``Decreasing
annotations are required in total correctness semantics``). So divergence
neither applies to this impl nor discharges the ``ensures`` clauses vacuously
if a rival introduces it.

AXIOM lane: dropped. ``AXIOM_TESTS = []``. This bundle has NO consumed axiom (the
projection callees are unchanged and run live by G-CONF, not axiomatized); the
nagini file's ``AXIOM_TESTS`` is likewise empty. The G-PBT gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-15561"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the whole frozen impl body (text strictly between
# ---- -- impl-start and -- impl-end). Lies wholly inside the single impl region
# ---- and is unique in Solution.lean (both facts asserted at load by _swap), so
# ---- every variant's edit is confined to the elided impl region and same_spec
# ---- holds by construction.
_GOLD_IMPL = (
    "    return (decide (a.quotedColumn ≠ b.quotedColumn) ||\n"
    "      decide (a.schemaIdentity ≠ b.schemaIdentity))"
)

assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted; update _GOLD_IMPL"

# ---- the frozen proof, verbatim. Reject rivals KEEP it unchanged — their
# ---- rejection is carried by the witness, not by whether the frozen tactic
# ---- happens to break on the reshape. A correct reshape whose residual goal the
# ---- frozen tactic no longer closes (the disjunct reorder) retunes ONLY the
# ---- elided tactic body (the spec view is untouched, the obligation statement
# ---- byte-identical).
_PROOF = (
    "prove_correct decideSchemaAlteration by\n"
    "  loom_solve\n"
    "  simp_all [schemaAlterationNeeded]"
)

assert _BASE.count(_PROOF) == 1, "frozen proof region drifted; update _PROOF"


def _impl(body):
    """Full Solution.lean variant with only the impl body replaced (spec view and
    frozen proof untouched)."""
    return _swap(_BASE, _GOLD_IMPL, body)


def _impl_reproved(body, new_proof):
    """Impl body replaced AND the (elided) proof tactic body retuned — for a
    correct reshape whose residual goal the frozen script no longer closes. The
    obligation STATEMENT is byte-identical; only the tactic body differs."""
    return _swap(_impl(body), _PROOF, new_proof)


# ---- witness builder. Reaches the method contract through Velvet's tester
# ---- machinery: `decideSchemaAlterationTester a b = false` says the extracted
# ---- program's result violates clause A at the concrete inputs a, b. Checked in
# ---- a file whose `prove_correct` block is stripped; closes by `decide` on the
# ---- transparent carrier. Binds nothing (literal inputs), so the gate's
# ---- consistency probe is a no-op.
def _fd(qc, si, ch):
    return (f'{{ quotedColumn := "{qc}", schemaIdentity := "{si}", '
            f'choices := "{ch}" }}')


def _witness(a_lit, b_lit):
    return (
        "extract_program_for decideSchemaAlteration\n"
        "prove_precondition_decidable_for decideSchemaAlteration\n"
        "prove_postcondition_decidable_for decideSchemaAlteration\n"
        "derive_tester_for decideSchemaAlteration\n\n"
        f"example : decideSchemaAlterationTester\n"
        f"    ({a_lit})\n"
        f"    ({b_lit}) = false := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else clause A is SPEC-TOO-STRONG. Each keeps the
    # byte-identical obligation statement; only the executable surface (and, where
    # the frozen tactic no longer closes the reshaped residual goal, the elided
    # tactic body) is changed. Both verified out-of-band with real builds.
    # =====================================================================
    {
        "id": "pos-control-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: report the decision as the SAME two-component disjunction with
        # the two disjuncts in the opposite order. `||` is commutative, so the
        # value is unchanged and clause A still discharges; the residual goal is a
        # `Bool` commutation the frozen `simp_all` does not close on its own, so the
        # elided tactic body is retuned with `ac_rfl` (obligation statement kept
        # byte-identical). Ports the nagini pos-sia-reorder (same members, reversed
        # literal order): a correct order-insensitive reshape must verify.
        "module": _impl_reproved(
            "    return (decide (a.schemaIdentity ≠ b.schemaIdentity) ||\n"
            "      decide (a.quotedColumn ≠ b.quotedColumn))",
            "prove_correct decideSchemaAlteration by\n"
            "  loom_solve\n"
            "  simp_all [schemaAlterationNeeded]\n"
            "  ac_rfl"),
        "rationale": (
            "structurally different CORRECT reshape: the same two-component "
            "disjunction with the disjuncts commuted. `||` is commutative so the "
            "value equals `schemaAlterationNeeded a b`, and clause A discharges "
            "after an `ac_rfl` on the `Bool` commutation the frozen `simp_all` "
            "leaves. Must verify, else clause A is SPEC-TOO-STRONG (over-fit to the "
            "disjunct order). Ports the nagini pos-sia-reorder (same members, "
            "reversed literal order — set/disjunction is order-insensitive)."
        ),
    },
    {
        "id": "pos-control-argswap",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: compare each component in the OPPOSITE argument order.
        # Disequality is symmetric, so the value is unchanged; the frozen
        # `simp_all` does not close the residual symmetry goal, so the elided
        # tactic body is retuned with `ne_comm` (obligation statement kept
        # byte-identical). Added by audit: the pre-existing positives both keep
        # the (a, b) comparison direction, so nothing in the battery showed the
        # spec is insensitive to which side of each comparison a binder sits on.
        "module": _impl_reproved(
            "    return (decide (b.quotedColumn ≠ a.quotedColumn) ||\n"
            "      decide (b.schemaIdentity ≠ a.schemaIdentity))",
            "prove_correct decideSchemaAlteration by\n"
            "  loom_solve\n"
            "  simp_all [schemaAlterationNeeded, ne_comm]"),
        "rationale": (
            "third correct shape, on an axis the other two positives leave "
            "untested: each component is compared in the opposite argument "
            "order. Disequality is symmetric, so the value equals "
            "`schemaAlterationNeeded a b` and clause A discharges after "
            "`ne_comm` rewrites the residual symmetry goal the frozen "
            "`simp_all` leaves. Must verify, else clause A is SPEC-TOO-STRONG "
            "(over-fit to the comparison direction rather than to the "
            "component-wise disagreement it means to pin)."
        ),
    },
    {
        "id": "pos-control-local-stage",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: stage each component's change flag through a typed local before
        # combining them. Same value flow, different control shape; the frozen
        # proof closes unchanged. Ports the nagini pos-fan-conj (a cheapest correct
        # re-shape of the decision keeping identical value flow).
        "module": _impl(
            "    let colChanged := decide (a.quotedColumn ≠ b.quotedColumn)\n"
            "    let idChanged := decide (a.schemaIdentity ≠ b.schemaIdentity)\n"
            "    return (colChanged || idChanged)"),
        "rationale": (
            "second correct shape: stage each component's change flag through a "
            "typed local before combining them. The value flow is unchanged "
            "(`colChanged = decide (a.quotedColumn ≠ b.quotedColumn)`, likewise "
            "`idChanged`), so clause A discharges and the frozen `prove_correct` "
            "body closes as-is. Proves the spec is not over-fitted to the inline "
            "spelling. Must verify, else SPEC-TOO-STRONG. Ports the nagini "
            "pos-fan-conj (cheapest correct decision re-shape)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the nagini admiss-sia / admiss-fan. Those cases
    # asserted the load-bearing membership / decision-defining facts are reachable
    # under a read-only fractional-permission precondition. This method carries NO
    # `require` clause (precondition ≡ True) and no heap permission, so that half
    # is vacuous. Re-aimed at the residual total-domain risk: that clause A's
    # post-image is SATISFIABLE by a gold-shaped computation. The frozen impl
    # discharging clause A IS that witness. MUST verify, else SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # frozen impl; same_spec trivially, must verify
        "rationale": (
            "the inputs carry no `require`, so the decision is total over every "
            "pair of field definitions; the gold impl discharging clause A is the "
            "admissibility witness that the post-image `out = schemaAlterationNeeded "
            "a b` is satisfiable by a real computation, not vacuously. Near-trivial "
            "precisely because the precondition is empty. Re-aimed from the nagini "
            "admiss-sia / admiss-fan, whose read-only-precondition half has no "
            "counterpart on this referentially-transparent carrier with no require "
            "clause. Else SPEC-UNSATISFIABLE."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each with a machine-checked refutation witness at concrete
    # inputs and the refinement argument for why its faithful real counterpart
    # would NOT resolve the failing test. All attack clause A; the witnesses vary
    # each of the three observable components of the input binders across FOUR
    # distinct points (pts=4), so no component is held fixed by every witness. The
    # first three attack a whole component (consulted when it must not be, or
    # dropped when it must be); the fourth is a NARROW partial-domain rival that
    # consults the right component but compares it too coarsely.
    # =====================================================================
    {
        "id": "weak-consult-choices",
        "kind": "uniqueness",
        "expect": "reject",
        # THE central rival = the pre-change behaviour: the decision consults the
        # presentation-only `choices` component as though it were schema-relevant,
        # so a difference confined to `choices` wrongly forces a rewrite. Correct on
        # every pair that agrees on `choices`; WRONG on a choices-only difference.
        "module": _impl(
            "    return (decide (a.quotedColumn ≠ b.quotedColumn) ||\n"
            "      decide (a.schemaIdentity ≠ b.schemaIdentity) ||\n"
            "      decide (a.choices ≠ b.choices))"),
        "refinement": (
            "this is the pre-change decision: the presentation-only component is "
            "consulted as though it affected the stored column, so a replacement "
            "that changes only that component is treated as requiring a rewrite. "
            "The failing test asserts such a replacement performs no schema work; a "
            "decision that consults the presentation-only component still reports a "
            "rewrite is required, so the faithful real patch FAILS the F2P and does "
            "NOT resolve. This is the exact defect the fix corrects."
        ),
        "rationale": (
            "REJECT from clause A (`out = schemaAlterationNeeded a b`): "
            "`schemaAlterationNeeded` never reads `choices`, so for a pair differing "
            "only in `choices` the spec forces `false` while this impl returns "
            "`true`. Refuted at a choices-only difference (equal columns, equal "
            "schema identity, differing choices). Verifying => SPEC-TOO-WEAK "
            "(admits the bug). Ports the nagini weak-drop-choices (the pre-patch "
            "behaviour where the presentation-only attribute is not ignored)."
        ),
        "witness": _witness(_fd("c", "s", "x"), _fd("c", "s", "y")),
    },
    {
        "id": "weak-ignore-column",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the quoted-column disjunct: the decision ignores a change to the
        # quoted column name. Correct on every pair whose column name agrees; WRONG
        # when the sole difference is the quoted column name.
        "module": _impl(
            "    return (decide (a.schemaIdentity ≠ b.schemaIdentity))"),
        "refinement": (
            "a faithful counterpart that stopped comparing the quoted column name "
            "would treat a replacement that renames the stored column (with the "
            "schema-relevant identity unchanged) as requiring no rewrite, so a "
            "required column rename is silently skipped. The P2P tests that rename "
            "a column pin a rewrite there, which this impl does not produce, so the "
            "faithful real patch FAILS and does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause A: `schemaAlterationNeeded` requires a rewrite when "
            "the quoted column name differs, so for a pair differing only in "
            "`quotedColumn` the spec forces `true` while this impl returns `false`. "
            "Refuted at a column-only difference (differing columns, equal schema "
            "identity, equal choices) — a DISTINCT point from weak-consult-choices, "
            "varying the `quotedColumn` component. Verifying => SPEC-TOO-WEAK. "
            "Ports the nagini weak-superset-extra-attr / partial-domain family (a "
            "schema-relevant difference wrongly ignored)."
        ),
        "witness": _witness(_fd("c1", "s", "x"), _fd("c2", "s", "x")),
    },
    {
        "id": "weak-ignore-schema-identity",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the schema-identity disjunct: the decision ignores a change to the
        # schema-relevant identity. Correct on every pair whose identity agrees;
        # WRONG when the sole difference is the schema-relevant identity.
        "module": _impl(
            "    return (decide (a.quotedColumn ≠ b.quotedColumn))"),
        "refinement": (
            "a faithful counterpart that stopped comparing the schema-relevant "
            "identity would treat a replacement that changes a schema-relevant "
            "attribute (e.g. one that alters the column's type/length, with the "
            "column name unchanged) as requiring no rewrite, so a REQUIRED column "
            "rebuild is silently skipped. The P2P alter tests that change a "
            "schema-relevant attribute pin a rewrite there, which this impl does "
            "not produce, so the faithful real patch FAILS and does NOT resolve."
        ),
        "rationale": (
            "REJECT from clause A: `schemaAlterationNeeded` requires a rewrite when "
            "the schema-relevant identity differs, so for a pair differing only in "
            "`schemaIdentity` the spec forces `true` while this impl returns "
            "`false`. Refuted at a schema-identity-only difference (equal columns, "
            "differing schema identity, equal choices) — a DISTINCT point from both "
            "other rivals, varying the `schemaIdentity` component. Verifying => "
            "SPEC-TOO-WEAK. Ports the nagini partial-domain rivals (a schema-relevant "
            "disagreement wrongly treated as a no-op)."
        ),
        "witness": _witness(_fd("c", "s1", "x"), _fd("c", "s2", "x")),
    },
    {
        "id": "weak-identity-coarse-compare",
        "kind": "uniqueness",
        "expect": "reject",
        # NARROW PARTIAL-DOMAIN rival, added by audit. The three rivals above are
        # all TOTAL-component failures (a whole component consulted or dropped).
        # This one CONSULTS the schema-relevant identity but compares it only
        # COARSELY — by length instead of by value. Correct on every pair whose
        # identities differ in length (and on every pair that agrees), WRONG
        # exactly on the sub-domain where the two identities differ but happen to
        # have the same length. That is the genuine flat-carrier counterpart of
        # the nagini partial-domain (loop off-by-one) rivals: a rival that agrees
        # with gold almost everywhere and diverges only on a narrow sub-domain,
        # which the three total-component rivals do not exercise.
        "module": _impl(
            "    return (decide (a.quotedColumn ≠ b.quotedColumn) ||\n"
            "      decide (a.schemaIdentity.length ≠ b.schemaIdentity.length))"),
        "refinement": (
            "a faithful counterpart would compare the two reconstructed "
            "schema-relevant identities by SIZE rather than by content, so a "
            "replacement that changes a schema-relevant attribute to a "
            "different value of the same serialized width is wrongly treated as "
            "requiring no rewrite and a REQUIRED column rebuild is silently "
            "skipped. Same-width schema-relevant edits are ordinary (swapping "
            "one enumerated database type for another of equal name length, or "
            "changing a fixed-width numeric bound), so the P2P alter tests that "
            "pin a rewrite on a schema-relevant change FAIL. It does NOT "
            "resolve, and it is strictly harder to catch than the total-drop "
            "rivals because it agrees with gold on the whole rest of the domain."
        ),
        "rationale": (
            "REJECT from clause A (`out = schemaAlterationNeeded a b`): the "
            "post-image compares the schema-relevant identity by VALUE, so at a "
            "pair whose identities differ but share a length the spec forces "
            "`true` while this impl returns `false`. Refuted at a FOURTH "
            "distinct input point (equal columns, identities `abc` vs `abd` — "
            "same length, different value, equal choices), which no other "
            "witness in this battery visits. Verifying => SPEC-TOO-WEAK (the "
            "spec would pin only the WIDTH of the schema-relevant identity "
            "rather than its content). This is the partial-domain class the "
            "footer previously recorded as having no counterpart on this "
            "carrier; the audit found it IS expressible here and landed it."
        ),
        "witness": _witness(_fd("q", "abc", "z"), _fd("q", "abd", "z")),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING. The sibling battery has 9 SPEC cases (2 soundness
# positives, 2 admissibility, 5 uniqueness — 1 frame-mutation, 2 partial-domain,
# 3 structural-weakness) plus an empty AXIOM lane, over TWO modeled functions: a
# 12-element schema-irrelevant attribute SET (exact-set-equality postcondition,
# with the presentation-only attribute now a pinned member) and a rebuild DECISION
# computed by an indexed scan over the two kwargs bags. THIS bundle models only the
# purely-functional core the fix's behavioural delta turns on — the rebuild
# DECISION — as a single method `decideSchemaAlteration (a b : FieldDef) -> Bool`
# whose post-image is `out = schemaAlterationNeeded a b`, a flat two-component
# disjunction over the quoted column name and the schema-relevant identity, with the
# presentation-only `choices` component observable but NOT consulted. The
# schema-irrelevant SET construction is folded into the unchanged projection callee
# that forms `schemaIdentity` (mapping.md §2.1), exercised by G-CONF, not modeled
# here. Every nagini case is accounted for below.
#
#   nagini case                     -> here
#   -----------------------------------------------------------------------
#   pos-sia-reorder                 -> pos-control-reorder            RE-EXPRESSED
#   pos-fan-conj                    -> pos-control-local-stage        RE-EXPRESSED
#   admiss-sia                      -> admiss-gold-total              RE-AIMED (merged)
#   admiss-fan                      -> admiss-gold-total              RE-AIMED (merged)
#   frame-mut-non_db-write-perm     -> (none)                        VACUOUS
#   partial-skip-first              -> weak-identity-coarse-compare    RE-EXPRESSED (audit)
#   partial-drop-last               -> weak-identity-coarse-compare    RE-EXPRESSED (audit)
#   weak-drop-choices               -> weak-consult-choices           PORTED (central, THE delta)
#   weak-drop-verbose               -> (none)                         NO COUNTERPART (folded)
#   weak-superset-extra-attr        -> weak-ignore-schema-identity    RE-EXPRESSED
#   AXIOM_TESTS (empty)             -> (none)                         empty both sides
#
# 8 velvet SPEC cases: 3 soundness, 1 admissibility, 4 uniqueness. This is a
# CORRECTLY-NARROWED port (case-count parity with nagini is not the target): the
# Lean-family bundle models one function where nagini models two, so the cases
# attached to the attribute-set STRUCTURE have no counterpart on the flat
# two-component decision carrier. The DECISION's partial-domain class DOES have
# one and is now carried (weak-identity-coarse-compare).
#
# RE-EXPRESSED (pos-sia-reorder -> pos-control-reorder): the nagini positive builds
#   the schema-irrelevant set from the same 12 members in reversed literal order
#   (set equality is order-insensitive). On this carrier the order-insensitive
#   structure is the two-component `||`; the reshape commutes its disjuncts and
#   verifies after an `ac_rfl` on the residual `Bool` commutation.
# RE-EXPRESSED (pos-fan-conj -> pos-control-local-stage): the nagini positive
#   collapses two nested `if`s into one short-circuiting decision keeping identical
#   value flow. On this carrier the decision is already a flat disjunction; the
#   value-preserving reshape stages each component's change flag through a typed
#   local before combining them. The frozen proof closes unchanged.
# RE-AIMED / MERGED (admiss-sia + admiss-fan -> admiss-gold-total): both nagini
#   admissibility cases assert a load-bearing fact is reachable under a read-only
#   fractional-permission precondition. This method has no `require` clause and no
#   heap permission, so that half is vacuous; re-aimed at the residual total-domain
#   risk (post-image satisfiability), witnessed by the frozen impl discharging
#   clause A. The two nagini cases (one per function) merge into one here because
#   this bundle models one function.
# PORTED (weak-drop-choices -> weak-consult-choices): THE central rival and the
#   exact pre-change behaviour. Nagini drops the presentation-only attribute from
#   the schema-irrelevant SET, so the decision keeps treating a choices-only change
#   as a rebuild-forcing disagreement; here the equivalent is the decision
#   CONSULTING the presentation-only `choices` component. Same behavioural delta,
#   same refinement argument (the F2P asserts a choices-only replacement performs no
#   schema work; consulting the component fails it), now backed by a machine-checked
#   witness at a choices-only difference.
# RE-EXPRESSED (weak-superset-extra-attr -> weak-ignore-schema-identity): the nagini
#   superset rival smuggles a schema-RELEVANT attribute into the schema-irrelevant
#   set, so a change to that attribute is wrongly stripped before comparison and
#   treated as a no-op. On this carrier the schema-relevant attributes are folded
#   into the single `schemaIdentity` component; a rival that fails to consult that
#   component is the flat-carrier expression of "a schema-relevant difference is
#   wrongly ignored". Refuted at a schema-identity-only difference.
# RE-EXPRESSED (partial-skip-first, partial-drop-last -> weak-identity-coarse-compare):
#   the nagini rivals are loop off-by-ones (skip the first / drop the last scanned
#   attribute), correct unless the sole schema-relevant disagreement is at that
#   index. There is indeed no first/last INDEX on this carrier's flat aggregate
#   decision — but the load-bearing property of that nagini class is not the index,
#   it is being correct almost everywhere and diverging only on a NARROW sub-domain.
#   An earlier revision of this footer recorded the whole class as having no
#   counterpart here; the audit re-derived it and found that wrong. Comparing the
#   schema-relevant identity COARSELY (by length rather than by value) reproduces
#   exactly that shape: it consults the component, agrees with gold on every pair
#   whose identities differ in width, and is WRONG only on the same-width sub-domain.
#   Landed with a machine-checked witness at a fourth distinct input point. The
#   total-component rivals weak-ignore-column / weak-ignore-schema-identity do NOT
#   cover this: each drops a component outright and so is wrong on a whole half-space,
#   which is a strictly easier target than a narrow sub-domain.
# NO COUNTERPART (weak-drop-verbose): the nagini rival omits a LEGACY
#   schema-irrelevant attribute from the set, so a change to that attribute wrongly
#   forces a rebuild. On this carrier those legacy attributes are stripped by the
#   unchanged projection callee that forms `schemaIdentity` (mapping.md §2.1); they
#   are not modeled as separate observable components, so there is no per-attribute
#   membership to drop. Omitted because the modeled surface does not include the
#   set structure (carrier narrowing), NOT because it was hard to prove.
# FRAME-MUTATION (frame-mut-non_db-write-perm): VACUOUS. The nagini rival demands
#   FULL write permission on the read-only Acc(set_pred(non_db),1/2) input.
#   Referentially-transparent backend: both inputs are immutable values, no `mut`
#   binder, no heap, no aliasing, no permission system. No read-only input to
#   over-claim; no substitute fabricated.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. The frozen impl is
#   LOOP-FREE (straight-line a single ``return`` over immutable values, no loop
#   and no recursion), so there is no control flow here to make diverge: a
#   diverging rival cannot be obtained by mutating this body, it has to bring a
#   loop of its own. When it does, the semantics refuse it. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
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
# AXIOM lane: empty on BOTH sides. No consumed axiom in this bundle (the projection
#   callees are unchanged and run live by G-CONF, not axiomatized). The G-PBT gate
#   ignores AXIOM_TESTS regardless.
#
# BINDER / CLAUSE / POINT COVERAGE. Two input binders (a, b : FieldDef), each with
#   three observable components. The single load-bearing clause A
#   (`out = schemaAlterationNeeded a b`) is attacked on all three: the
#   presentation-only `choices` component that MUST NOT be consulted
#   (weak-consult-choices), and the two schema-relevant components that MUST each be
#   consulted — the quoted column name (weak-ignore-column) and the schema-relevant
#   identity (weak-ignore-schema-identity) — plus the STRENGTH of the identity
#   comparison, which must be by value and not merely by width
#   (weak-identity-coarse-compare). The four reject witnesses probe four DISTINCT
#   input points (pts=4): a choices-only difference, a column-only difference, a
#   schema-identity-only difference at differing widths, and a schema-identity
#   difference at EQUAL width — so every observable component is varied by some
#   witness, none is held fixed across the battery, and the identity component is
#   probed at two points that a width-only comparison distinguishes. Clause A is
#   defended by the three soundness positives (inline, staged-local, and
#   argument-swapped shapes) and the admissibility case.
#
# ATTACK SURFACE MEASURED BY AUDIT (all with real builds, none shipped as a case
#   because each behaved as the spec requires). WRONG impls the spec REJECTED:
#   conjunction instead of disjunction; the presentation-only component substituted
#   for the schema-relevant identity; the whole decision negated; the constant
#   `true`; a decision reading only binder `a`; the quoted column compared by length;
#   the identity compared by first character. CORRECT reshapes the spec ACCEPTED:
#   a De Morgan spelling over `&&`; a `decide` over a `Prop`-level disjunction; a
#   single comparison of the two components as a PAIR; a redundant
#   presentation-only conjunct that cannot change the value; a branch on column
#   equality (accepted once the elided tactic body is retuned, statement
#   byte-identical). So clause A is neither too weak nor too strong on any axis
#   probed: it pins the decision by VALUE at every input over both binders.
#
# CARRIER NOTE. The carrier is fully transparent (`FieldDef` a three-String-field
#   structure deriving `DecidableEq`; `schemaAlterationNeeded` a plain `def`), so
#   every witness refutes at concrete literals via the tester machinery and closes by
#   `decide` — no conditioning on an opaque term, hence no witness binds anything and
#   the consistency probe is a no-op. Each witness was SEEN to discriminate with two
#   real builds: it ELABORATES against the rival and FAILS against the frozen
#   (straight-line, `decide`-reducible) solution, whose tester returns `true` because
#   gold satisfies clause A at that input.
AXIOM_TESTS = []
