"""properties.py — G-PBT falsification battery for django__django-12663 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both of which the consumer spec view elides, so ``markers.same_spec`` holds
and the ``prove_correct outputFieldIdentity`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

This battery is a PORT of the nagini sibling
(``../nagini/properties.py``); the sibling's adversarial reasoning is carried
over and re-expressed against this backend's carrier.

DEFENDED SURFACE (one contracted method):

  outputFieldIdentity (sel : Selection) return (r : Int)
    require sel.field ≠ 0
    ensures (sel.source ≠ 0 → r = sel.source) ∧ (sel.source = 0 → r = sel.field)

  The method reports ONE field identity for a selected item that carries two
  integer field identities: a *source* identity ``sel.source`` (sentinel ``0`` ≡
  "no usable source identity present"; any nonzero value ≡ a usable, distinct
  identity) and a *resolved* identity ``sel.field`` (always usable, pinned
  nonzero by the ``require``). The single ``ensures`` has TWO independent
  top-level clauses:

    * (S1) ``sel.source ≠ 0 → r = sel.source`` — PREFER the source identity when
      it is usable. This is the DISCRIMINATING clause: on an item whose source
      is nonzero and DIFFERS from the resolved identity, the reported identity
      MUST be the source, never the resolved one.
    * (S2) ``sel.source = 0 → r = sel.field`` — else fall back to the resolved
      identity.

  ONE INPUT BINDER, ``sel``, exposing two load-bearing fields: ``sel.source``
  selects the branch (nonzero vs the sentinel) and, on the nonzero branch, IS the
  answer; ``sel.field`` is the answer on the sentinel branch. Both are varied by
  the reject witnesses (``sel.source`` over {5, 0, 3, -5}, ``sel.field`` over
  {7, 9}) and both clauses are attacked (S1 by three rivals, S2 by one), at FOUR
  distinct input points (pts = 4). The negative source point is what separates
  the ``≠ 0`` S1 actually quantifies over from the narrower ``> 0`` a
  sign-restricted guard would substitute.

ORACLE GROUNDEDNESS: the postcondition is grounded entirely in the argument
(``sel.source``, ``sel.field``, ``r``); the ``axioms`` region is empty — there is
no opaque answer-key term a wrong impl could echo. The cheapest correct impl
computes the choice honestly, which the positive controls cover; the
"ungrounded-oracle echo" class is therefore N/A (see the footer).

CARRIER NOTE — THE DECIDABLE BOUNDARY. A witness reaches the post-image through
Velvet's tester machinery (``outputFieldIdentityTester sel = false`` says the
extracted program's result violates the postcondition at that concrete input) and
closes by ``decide``, checked in a file whose ``prove_correct`` block has been
stripped so no tactic script can mask the verdict. Both the frozen impl and every
reject rival are LOOP-FREE (a two-branch integer chooser), so their extracted
testers ``decide`` over concrete ``Int`` literals — no opaque term stalls the
kernel. The FAIL-on-gold half is therefore genuine value divergence, not a stuck
reduction: at each witnessed input the frozen chooser reports the OTHER identity,
so its tester reduces to ``true`` (postcondition holds) while the rival's reduces
to ``false``. Every witness was checked with ``scripts/lean_verify.sh`` against
both the rival (elaborates green) and the frozen solution (fails).

FORGERY CHECK. Because a gold-side exit code is evidence only if it TRACKS the
claim, each witness was additionally built against the frozen solution with its
claim FLIPPED (``= true`` for ``= false``, i.e. asserting the frozen chooser is
CORRECT at that input). All four flipped builds ELABORATE against gold (exit 0)
and FAIL against their rival (exit 1) — the exact inverse of the witnesses'
own pattern. So gold's exit code here carries real information about the claim,
and the rejections are refutations rather than tactic mismatches.
"""
from pathlib import Path

INSTANCE = "django__django-12663"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- the WHOLE gold impl block (between and INCLUDING the markers): a single
# ---- anchor lying wholly inside the impl region and unique in the file (both
# ---- facts asserted at load). Every variant swaps on this block.
_IMPL = (
    "    -- impl-start\n"
    "    let source := sel.source\n"
    "    if source ≠ 0 then\n"
    "      return source\n"
    "    else\n"
    "      return sel.field\n"
    "    -- impl-end"
)
assert _BASE.count(_IMPL) == 1, "impl-block anchor drift — re-sync _IMPL"

# ---- the frozen proof body (tactic script only; elided from the spec view). A
# ---- structurally-different correct impl keeps this bare `loom_solve`; a reject
# ---- rival keeps it too (a wrong impl leaves the obligation unclosed, which is
# ---- the intended non-verification — the witness, not the tactic script, is
# ---- what attributes the rejection to the spec).
_PROOF = "prove_correct outputFieldIdentity by\n  loom_solve"
assert _BASE.count(_PROOF) == 1, "proof anchor drift"


def _impl(body):
    """Wrap a new executable body in the impl markers (spec never touched)."""
    return "    -- impl-start\n" + body + "\n    -- impl-end"


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `outputFieldIdentityTester sel = false` says the extracted program's result
# ---- violates the method's postcondition at that concrete input. Checked in a
# ---- file whose `prove_correct` block has been stripped. Every argument is a
# ---- concrete `Int` literal so `decide` reduces the (loop-free) extracted rival.
def _tester(body):
    return ("\n"
            "extract_program_for outputFieldIdentity\n"
            "prove_precondition_decidable_for outputFieldIdentity\n"
            "prove_postcondition_decidable_for outputFieldIdentity\n"
            "derive_tester_for outputFieldIdentity\n\n" + body)


def _sel(source, field):
    """A concrete Selection literal for a witness input point."""
    return "{ source := %d, field := %d }" % (source, field)


def _witness(source, field):
    return _tester(
        f"example : outputFieldIdentityTester {_sel(source, field)} "
        "= false := by\n  decide\n")


def _admiss(claims, body):
    """An in-region `assert` (elided from the spec view) ahead of `body`.

    `with_name_prefix` names the goals the assert raises so the frozen tactic
    script's own goals stay distinguishable. The assert is discharged as an extra
    obligation of THIS variant; the method's frozen `ensures` still has to
    discharge from `body` afterwards.
    """
    return _impl("    assert (with_name_prefix `adm (\n" + claims + "))\n" + body)


# The gold body, reused verbatim by the admissibility case (which adds an
# in-region assert AHEAD of it and changes nothing else).
_GOLD_BODY = (
    "    let source := sel.source\n"
    "    if source ≠ 0 then\n"
    "      return source\n"
    "    else\n"
    "      return sel.field")


SPEC_TESTS = [

    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the
    # postcondition over-constrains the impl SHAPE (SPEC-TOO-STRONG). A
    # two-branch chooser needs no loop or lemma, so a branch reorder / ternary
    # keeps every obligation discharged by the frozen `loom_solve`.
    # =====================================================================
    {
        "id": "pos-reorder-source-zero-first",
        "kind": "soundness",
        "expect": "verify",
        # Branch-reorder: test the fallback (source == 0) FIRST and report the
        # resolved identity there, otherwise report the source. Same value choice,
        # mirror control-flow shape.
        "module": _swap(
            _BASE, _IMPL,
            _impl(
                "    let source := sel.source\n"
                "    if source = 0 then\n"
                "      return sel.field\n"
                "    else\n"
                "      return source")),
        "rationale": (
            "reporting the resolved identity when source = 0 and the source "
            "otherwise is exactly the gold choice with the two branches reordered. "
            "It satisfies S1 (source ≠ 0 → r = source) and S2 (source = 0 → r = "
            "field) on the whole domain, so `loom_solve` still closes. If a "
            "faithful correct impl cannot verify, the postcondition is "
            "SPEC-TOO-STRONG (over-fit to the gold branch order). (Sibling: "
            "pos-reorder-source-zero-first.)"),
    },
    {
        "id": "pos-ternary-local",
        "kind": "soundness",
        "expect": "verify",
        # Local-variable reshape: bind both candidate identities to locals and
        # pick with an if-expression in the return. Cheapest honest chooser,
        # grounded entirely in the inputs (no oracle to echo); maximally different
        # from the branch-and-return gold shape.
        "module": _swap(
            _BASE, _IMPL,
            _impl(
                "    let s := sel.source\n"
                "    let f := sel.field\n"
                "    return (if s ≠ 0 then s else f)")),
        "rationale": (
            "an if-expression over locals bound from the two fields is the cheapest "
            "correct chooser and is grounded entirely in the input (no answer-key "
            "to echo). It reports `s` when `s ≠ 0` and `f` otherwise, so S1/S2 hold "
            "and `loom_solve` closes; a failure would be SPEC-TOO-STRONG. Doubles "
            "as the honest positive control standing in for the N/A "
            "ungrounded-oracle class. (Sibling: pos-ternary-local.)"),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED, and NOT omitted. The sibling probes whether a
    # fractional-permission Requires is establishable for a fresh Selection; this
    # backend has no permission surface, so that exact probe has no analogue. But
    # the LANE is not vacuous: the analogue on a total carrier is that the frozen
    # obligation is SATISFIABLE — and, at an F2P-shaped input, satisfiable ONLY by
    # the gold answer. A spec no impl can meet at the discriminating input reads
    # exactly like a spec every impl meets, and neither the positives (which
    # discharge the obligation over the WHOLE domain, so they never exhibit any
    # single input) nor the reject witnesses (which run in a file whose
    # `prove_correct` is STRIPPED, so they never touch this obligation at all)
    # exhibit it at a concrete point.
    #
    # So this case discharges the obligation BY EVALUATION at two concrete
    # F2P-shaped inputs, as an in-region `assert` ahead of the unchanged gold
    # body, and pins non-degeneracy in BOTH directions at each: the postcondition
    # HOLDS of the gold answer and FAILS of the rival answer. That second half is
    # what makes the assert load-bearing rather than a tautology — checked by
    # building the same case with the negated claim asserted instead, which FAILS
    # (`unsolved goals`, case `adm_1`), so the assert is genuinely proved here and
    # not discharged vacuously.
    # =====================================================================
    {
        "id": "admiss-obligation-satisfiable-at-f2p",
        "kind": "admissibility",
        "expect": "verify",
        # Point 1 (the DISCRIMINATING shape: usable source differing from the
        # resolved identity) — the postcondition holds of r = 5 (the source) and
        # FAILS of r = 7 (the resolved identity the pre-change shape reports).
        # Point 2 (the SENTINEL shape) — it holds of r = 7 (the resolved identity)
        # and FAILS of r = 0 (the sentinel the fallback-dropping shape reports).
        # The require (`field ≠ 0`) is met at both, so both are admissible inputs.
        "module": _swap(
            _BASE, _IMPL,
            _admiss(
                "      (((5:Int) ≠ 0 → (5:Int) = 5) ∧ ((5:Int) = 0 → (5:Int) = 7)) ∧\n"
                "      ¬ (((5:Int) ≠ 0 → (7:Int) = 5) ∧ ((5:Int) = 0 → (7:Int) = 7)) ∧\n"
                "      (((0:Int) ≠ 0 → (7:Int) = 0) ∧ ((0:Int) = 0 → (7:Int) = 7)) ∧\n"
                "      ¬ (((0:Int) ≠ 0 → (0:Int) = 0) ∧ ((0:Int) = 0 → (0:Int) = 7))",
                _GOLD_BODY)),
        "rationale": (
            "the frozen obligation is SATISFIABLE at F2P-shaped inputs, and "
            "uniquely so: at (source = 5, field = 7) — a usable source differing "
            "from the resolved identity, the discriminating shape — the "
            "postcondition holds of r = 5 and is FALSE of r = 7; at (source = 0, "
            "field = 7) — the sentinel shape — it holds of r = 7 and is FALSE of "
            "r = 0. Both inputs meet the `require` (field ≠ 0), so neither is "
            "excluded. If the assert could not discharge, the obligation would be "
            "unsatisfiable or degenerate at exactly the input the behaviour is "
            "observable at (PRECOND-TOO-STRONG). The gold body and the frozen "
            "`loom_solve` are kept verbatim, so the method's own `ensures` still "
            "discharges alongside. The negated form of this assert does NOT "
            "discharge, so the claim is proved here rather than held vacuously. "
            "(Sibling: admiss-fresh-selection, re-aimed from permission "
            "establishability — no analogue on this carrier — to obligation "
            "satisfiability + non-degeneracy at the concrete F2P input.)"),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec that
    # MUST be rejected, each a loop-free closed form (so its extracted tester
    # `decide`s) with a machine-checked refutation witness at a DISTINCT concrete
    # input, plus the refinement argument that its faithful real counterpart would
    # NOT resolve the failing test. The frozen spec is untouched; the proof stays
    # `loom_solve` (a wrong impl leaves it unclosed — the intended
    # non-verification).
    # =====================================================================
    {
        "id": "weak-always-field-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # Pre-change behaviour: always report the resolved identity, ignoring a
        # usable source. Correct only on the source == 0 sub-domain.
        "module": _swap(_BASE, _IMPL, _impl("    return sel.field")),
        "refinement": (
            "this is the literal pre-change shape — report the resolved identity "
            "unconditionally. On a selected item with an explicit resolved identity "
            "differing from its source (the nested-subquery case in the issue), it "
            "reports the relation-unaware resolved identity, so a deferred "
            "stand-in on the comparison side cannot be coerced via the related "
            "field. The failing scenario that this fix targets would still fail — "
            "it would NOT resolve. Correct on every item whose source is the "
            "sentinel (a true partial-domain break)."),
        "rationale": (
            "REJECT via S1 (sel.source ≠ 0 → r = sel.source): for a selection with "
            "source ≠ 0 and source ≠ field it reports field ≠ source. Correct on "
            "the source = 0 sub-domain (S2) but wrong on the discriminating "
            "sub-domain S1 pins. Verifying would be SPEC-TOO-WEAK. Refuted at "
            "source = 5, field = 7 (source ≠ 0, source ≠ field): gold reports 5, "
            "the rival 7. (Sibling: weak-always-field-prepatch.)"),
        "witness": _witness(5, 7),
    },
    {
        "id": "weak-always-source",
        "kind": "uniqueness",
        "expect": "reject",
        # Always report the source identity, even when it is the unusable sentinel
        # 0 (no `or`-fallback to the resolved identity). Correct on the source != 0
        # sub-domain only.
        "module": _swap(_BASE, _IMPL, _impl("    return sel.source")),
        "refinement": (
            "reporting the source identity even when there is no usable source "
            "(dropping the fallback to the resolved identity) reports the sentinel "
            "for a selection whose source is absent/falsy; downstream the reported "
            "identity is then a non-usable field, breaking single-selection "
            "behaviour whose item carries no usable source. The fallback is "
            "load-bearing, so such a patch would regress the always-green suite — "
            "it would NOT resolve. Correct on every item with a usable source."),
        "rationale": (
            "REJECT via S2 (sel.source = 0 → r = sel.field): for source = 0 it "
            "reports 0, but the resolved identity is nonzero (the `require`), so "
            "r = field is violated. Verifying would be SPEC-TOO-WEAK (the fallback "
            "unenforced). Refuted at source = 0, field = 7 — the sentinel "
            "sub-domain the always-field rival agrees with gold on, so the two do "
            "NOT share a witness. (Sibling: weak-always-source.)"),
        "witness": _witness(0, 7),
    },
    {
        "id": "weak-equal-only-pin",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-proxy: report the source only when it ALREADY equals the resolved
        # identity; otherwise fall back to the resolved identity. On this integer
        # carrier this collapses to `return sel.field` (in the one branch that
        # returns source, source = field), so it is a disguised always-field — but
        # a DISTINCT executable shape whose rejection at the discriminating input
        # is worth pinning: a no-op disguised as a fix, correct on the coinciding
        # sub-domain (source == field) but reverting to the bug when they differ.
        "module": _swap(
            _BASE, _IMPL,
            _impl(
                "    let source := sel.source\n"
                "    if source ≠ 0 ∧ source = sel.field then\n"
                "      return source\n"
                "    else\n"
                "      return sel.field")),
        "refinement": (
            "reporting the source only when it already equals the resolved "
            "identity is a no-op disguised as a fix: it preserves the gold answer "
            "exactly on the coinciding case (item built without an explicit "
            "resolved identity, where the two coincide) but reverts to the "
            "pre-change bug on the discriminating case where they differ — the "
            "deferred stand-in still hits the resolved identity, so the failing "
            "scenario would NOT resolve. Correct on the coinciding and sentinel "
            "sub-domains."),
        "rationale": (
            "REJECT via S1 (sel.source ≠ 0 → r = sel.source): on the discriminating "
            "input source ≠ 0 and source ≠ field, the impl reports field ≠ source. "
            "This is the value-proxy that drops exactly the disagreeing sub-domain "
            "S1 pins. Verifying would be SPEC-TOO-WEAK. Refuted at a DISTINCT point "
            "from the always-field rival (source = 3, field = 9) so the manifest "
            "demonstrates the claimed source ≠ field sub-domain and widens the "
            "binder coverage (source over {5,0,3}, field over {7,9}). (Sibling: "
            "weak-equal-only-pin.)"),
        "witness": _witness(3, 9),
    },
    {
        "id": "weak-positive-source-only",
        "kind": "uniqueness",
        "expect": "reject",
        # SIGN-RESTRICTED guard: treat only a POSITIVE source identity as usable
        # (`> 0` in place of `≠ 0`), falling back to the resolved identity
        # otherwise. Correct on the entire sub-domain the other three rivals are
        # witnessed at (source ∈ {5, 3, 0}) and wrong only where source is a
        # NEGATIVE identity — a region no other case in this battery reaches.
        "module": _swap(
            _BASE, _IMPL,
            _impl(
                "    if sel.source > 0 then\n"
                "      return sel.source\n"
                "    else\n"
                "      return sel.field")),
        "refinement": (
            "this is the usability test narrowed from 'is there a source identity "
            "at all' to 'is it one of a privileged subset': it keeps the fallback "
            "and keeps preferring the source on the common shape, so the "
            "always-green suite stays green and the coinciding case is unaffected. "
            "But a selected item whose source identity falls outside the privileged "
            "subset is routed to the resolved, relation-unaware identity, so the "
            "deferred stand-in on the comparison side cannot be coerced there and "
            "the failing scenario would NOT resolve for such an item. A "
            "sub-domain break that is invisible to every other rival here, since "
            "each of those is witnessed only at a source in the privileged subset "
            "or at the sentinel."),
        "rationale": (
            "REJECT via S1 (sel.source ≠ 0 → r = sel.source): the guard `source > "
            "0` is STRICTLY STRONGER than the `source ≠ 0` the clause quantifies "
            "over, so at a source that is nonzero but outside the guard the impl "
            "reports field ≠ source. Verifying would be SPEC-TOO-WEAK — it would "
            "mean S1 pins only part of the nonzero domain it names, i.e. the "
            "sentinel test could be narrowed silently. Refuted at source = -5, "
            "field = 7: gold reports -5, the rival 7. This is the ONLY case that "
            "moves `sel.source` off the {5, 3, 0} region the other three rivals "
            "share, so it is what distinguishes 'nonzero' from 'positive' in the "
            "manifest. (NEW at audit: no sibling analogue — the nagini battery "
            "pins no negative source identity either, so this closes a gap the "
            "design document itself leaves open.)"),
        "witness": _witness(-5, 7),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 8 SPEC cases (2
# soundness positives, 1 admissibility, 5 uniqueness rivals — two of which are
# mandatory frame-mutation rivals) plus an EMPTY AXIOM lane (AXIOM_TESTS = []).
# The sibling contracts `output_field_identity` over a fractional-permission,
# read-only `Selection` with two int field identities. This backend models the
# SAME two-branch chooser over a referentially-transparent `Selection` value; the
# frame class collapses and the admissibility probe degenerates, but every
# value-level rival ports.
#
#   sibling case                 kind          -> here                            disposition
#   ---------------------------------------------------------------------------------------------
#   pos-reorder-source-zero-first soundness    -> pos-reorder-source-zero-first   PORTED
#   pos-ternary-local             soundness    -> pos-ternary-local               PORTED
#   admiss-fresh-selection        admissibility -> admiss-obligation-satisfiable-at-f2p  RE-AIMED (see below)
#   frame-mutate-source-to-field  uniqueness    -> (none)                         VACUOUS (carrier)
#   frame-mutate-field-to-source  uniqueness    -> (none)                         VACUOUS (carrier)
#   weak-always-field-prepatch    uniqueness    -> weak-always-field-prepatch     PORTED
#   weak-always-source            uniqueness    -> weak-always-source             PORTED
#   weak-equal-only-pin           uniqueness    -> weak-equal-only-pin            PORTED
#   (no sibling analogue)         uniqueness    -> weak-positive-source-only      NEW (audit)
#   AXIOM_TESTS (none)            axiom         -> (none)                          N/A (G-AX)
#
# 3 uniqueness ported + 1 NEW, 2 soundness ported, 1 admissibility RE-AIMED; 2
# frame rivals vacuous; axiom lane empty (nothing to port). NO divergence
# lane in the sibling (0 diverge-*/nonterm-* cases), so there is no port to
# account for on that lane. Independently of the port: this bundle sets
# `loom.semantics.termination "total"`, under which a postcondition is claimed of
# ALL runs and not only of terminating ones, and the verifier emits a descent
# obligation `measure b' < measure b` for every loop. A diverging rival is
# therefore REJECTED, so there is no hole on this lane either.
#
# VACUOUS (frame-mutate-source-to-field, frame-mutate-field-to-source): the
#   sibling's two MANDATORY frame-mutation rivals overwrite a read-only field
#   held at a fractional heap permission (`Acc(.,1/2)`) to satisfy a clause
#   vacuously, and are rejected for INSUFFICIENT-PERMISSION / a frame-clause
#   violation. This backend is referentially transparent: `sel` is an immutable
#   `Selection` value declared read-only (not `mut`), there is no heap, no
#   aliasing, no `Old`, and no permission system — and the spec carries no frame
#   clause (nothing to violate, because nothing can be written). The class has no
#   carrier analogue; OMITTED as a genuine carrier fact, NOT fabricated (porting
#   map: this class is vacuous on a referentially-transparent backend).
# RE-AIMED (admiss-fresh-selection -> admiss-obligation-satisfiable-at-f2p): the
#   sibling constructs a fresh Selection and asserts its fractional-permission
#   Requires (`Acc(.,1/2)` + field != 0) is establishable — a probe about
#   permission machinery, which has no analogue here (no heap, no permissions).
#   The LANE, however, is NOT vacuous, and an earlier revision of this file
#   omitted it on the reasoning that the `ensures` names no pure model helper, so
#   an in-region assert restating it "would be a tautology". That reasoning is
#   wrong, and was measured wrong: the assert this case now ships states the
#   obligation at CONCRETE inputs in BOTH directions — the postcondition holds of
#   the gold answer AND is FALSE of the rival answer — and the same case built
#   with the negated claim asserted instead does NOT elaborate (`unsolved goals`,
#   case `adm_1`). A tautology would discharge either way, so the assert is
#   load-bearing. It is also the only case in the battery that exhibits the
#   frozen obligation at a single named input: the positives discharge it over
#   the whole domain (never exhibiting any one point) and the reject witnesses
#   run in a file whose `prove_correct` is STRIPPED, so they never touch this
#   obligation at all. The analogue of PRECOND-TOO-STRONG on a total carrier is
#   the obligation being unsatisfiable or degenerate at exactly an F2P-shaped
#   input, and that is what this case tests.
#
# BINDER / CLAUSE COVERAGE. The sole `ensures` has TWO independent clauses over
#   ONE binder `sel` (fields `source`, `field`). Both clauses are attacked:
#     * S1 (source ≠ 0 → r = source): weak-always-field-prepatch (source 5,
#       field 7), weak-equal-only-pin (source 3, field 9) and
#       weak-positive-source-only (source -5, field 7).
#     * S2 (source = 0 → r = field): weak-always-source (source 0, field 7).
#   FOUR distinct input points (pts = 4): `sel.source` ranges over {5, 0, 3, -5}
#   and `sel.field` over {7, 9}. The four source values are meaningfully
#   distinct, not spellings of one point: 0 is the sentinel (S2's whole domain),
#   5 and 3 are usable identities differing from the resolved one (S1, at two
#   distinct field values), and -5 additionally separates "nonzero" — which is
#   what S1 actually quantifies over — from "positive", the narrower guard
#   weak-positive-source-only substitutes. Before that rival was added, EVERY
#   witnessed source was in {5, 3, 0}, so a spec pinning only a positive source
#   would have passed this battery unremarked.
#   No binder field is pinned at a single value across the reject set, so
#   a rival mishandling only `source` OR only `field` is caught. The always-field
#   and equal-only-pin rivals are behaviourally identical on this Int carrier
#   (equal-only-pin's guard forces its returned value to equal `field`), so they
#   attack S1 the same way; equal-only-pin is retained as a DISTINCT executable
#   shape at a DISTINCT input to widen coverage, and its `refinement` names the
#   coinciding sub-domain it is correct on. always-source attacks the disjoint
#   S2 sub-domain (the sentinel), so it does not share a witness with either.
#
# AXIOM_TESTS: empty. The bundle declares no axiom (mapping.md §3: the changed op
#   is modeled deeply and concretely, validated by G-CONF/G-AX, so there is no
#   consumed axiom); the sibling's AXIOM_TESTS is likewise empty. This gate
#   ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
