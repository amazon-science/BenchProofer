"""properties.py — G-PBT falsification battery for django__django-13568 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct usernameUniquenessVerdict`` obligation survives
with a byte-identical statement) and swaps in a candidate implementation. It is
checked by the real verifier. ``expect:"verify"`` passes iff (in scope AND
verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates: the witness must elaborate against the
rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method):

  usernameUniquenessVerdict
      (fieldUnique : Bool) (constraints : List Constraint)
      (usernameField : String) (defaultBackendOnly : Bool) return (out : Verdict)
    ensures out =
      (if !fieldUnique && !coversField constraints usernameField then
         (if defaultBackendOnly then Verdict.error else Verdict.warning)
       else Verdict.ok)

The method decides what to report about the uniqueness of a login identity
field. Nothing is reported (``Verdict.ok``) exactly when the field is already
guaranteed unique — either its own column is declared unique (``fieldUnique``)
OR some declared constraint guarantees the single field is unique for every row
(``coversField``). Only when NEITHER holds is a verdict reported, and then the
severity depends on whether only the default authentication backend is
configured (``defaultBackendOnly``): a hard error there, a warning otherwise.

``coversField cs uf`` is a total, fully-unfolded pure function of the method's
own inputs: it asks whether some UNCONDITIONAL uniqueness constraint
(``totalUnique`` keeps ``c.fields`` iff ``c.isUnique && !c.conditional``) ranges
over EXACTLY the single field ``uf`` (``fs == [uf]``). The three interesting
sub-behaviors it composes — uniqueness-vs-not (``isUnique``), unconditional-vs-
conditional (``conditional``), single-field-exact-match (``fs == [uf]``) — are
each independently attackable.

The four INPUT binders are all free and the post-image must hold for EVERY value
of each:
  * ``fieldUnique``        — the field's own declared-unique flag;
  * ``constraints``        — the declared constraints (only ``totalUnique`` of
                             them, projected to single-field-exact-match, drives
                             the decision; per-constraint ``fields`` / ``isUnique``
                             / ``conditional`` all matter);
  * ``usernameField``      — the single identity field the cover must match;
  * ``defaultBackendOnly`` — selects the reported severity.

ADVERSARIAL READ of the classes (mirrors the nagini sibling; see the footer for
the case-by-case accounting):
  * FRAME/PERMISSION-MUTATION — VACUOUS on this backend. The sibling's mandatory
    frame-mutation rival writes back into a read-only sequence input that
    carries only a fractional heap permission (``Acc(list_pred(c_*),1/2)``) and
    is rejected for INSUFFICIENT PERMISSION. Lean and Velvet are referentially
    transparent: every parameter is an immutable value, this bundle declares no
    ``mut`` binder, there is no heap and no aliasing. There is no read-only input
    to overwrite and no permission system to trip, so the class is vacuous. No
    substitute is fabricated (per the porting map, this class is legitimately
    dropped here rather than replaced).
  * UNGROUNDED-ORACLE ECHO — N/A, exactly as the sibling records. The post-image
    is pinned to ``coversField constraints usernameField`` and the regime
    constant — both computed entirely from the method's own arguments by a
    concrete ``def`` in the ``pure`` region (the ``axioms`` region is empty; no
    opaque answer key). There is no value an echo could carry that satisfies the
    ensures yet is behaviourally wrong — the unique satisfier IS the grounded
    decision. The honest controls are the cheapest faithful impls that compute
    it (the ``pos-*`` reshapes).
  * CONTROL-FLOW-EFFECT — N/A. The method returns a pure three-valued verdict;
    there is no raise / return-vs-fallthrough / side-effect difference invisible
    to the value abstraction. The emit-vs-suppress and severity control points
    ARE the returned verdict, fully captured by the ensures.
  * PARTIAL-DOMAIN / VALUE — heavily exercised. The decision surface has several
    sub-domains a rival can get right on most inputs yet diverge on one: the
    regime severity, the field-unique-but-covered discriminator (the F2P
    scenario), and the never-suppress / always-suppress edges.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is STRAIGHT-LINE (no loop):
its extracted program reduces fully under ``decide``. Each reject rival carries
a machine-checked refutation ``witness`` — a Velvet tester statement
``usernameUniquenessVerdictTester <args> = false`` at ONE concrete input,
checked in a file whose ``prove_correct`` block has been stripped so no tactic
script can mask the verdict. Both halves were checked out-of-band with
``scripts/lean_verify.sh``: every witness ELABORATES against its rival and FAILS
(``decide`` proves the proposition false) against the frozen solution, so each
rejection is a genuine spec refutation and not mechanical tactic breakage.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom``; the one deep
model (``totalUnique``) is an A-reference validated ``== _meta.total_unique_
constraints`` by ``axiom_check.py`` (G-AX). Nothing in the proof rests on an
axiom, and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13568"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen impl body, verbatim — everything strictly BETWEEN the method's
# `-- impl-start` / `-- impl-end`. Every rival and reshape edits ONLY this block
# (and, for reshapes/admissibility, the elided `prove_correct` tactic body), so
# the spec view is untouched and same_spec holds by construction.
_IMPL = """    -- impl-start
    let covered := (totalUnique constraints).any (fun fs => fs == [usernameField])
    let out : Verdict :=
      if !fieldUnique && !covered then
        (if defaultBackendOnly then Verdict.error else Verdict.warning)
      else Verdict.ok
    return out
    -- impl-end"""

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A reshape that changes the impl's syntactic form
# retunes THIS block (elided from the spec view); rivals leave it as-is (the
# rejection is carried by the witness, not the tactic script).
_PROOF = """prove_correct usernameUniquenessVerdict by
  loom_solve
  simp_all [coversField]"""

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL,
                 "    -- impl-start\n" + new_body + "\n    -- impl-end")


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for correct reshapes)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery:
# ---- `usernameUniquenessVerdictTester <args> = false` says the extracted
# ---- program's result violates the postcondition at that concrete input.
# ---- Checked in a file whose `prove_correct` block is stripped.
_TESTER = ("extract_program_for usernameUniquenessVerdict\n"
           "prove_precondition_decidable_for usernameUniquenessVerdict\n"
           "prove_postcondition_decidable_for usernameUniquenessVerdict\n"
           "derive_tester_for usernameUniquenessVerdict\n\n")


def _witness(call):
    return _TESTER + f"example : {call} = false := by\n  decide\n"


# Constraint literal helper for readable witnesses.
def _c(fields, uniq, cond):
    fs = "[" + ", ".join(f'"{f}"' for f in fields) + "]"
    return (f"{{ fields := {fs}, isUnique := {str(uniq).lower()}, "
            f"conditional := {str(cond).lower()} }}")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the
    # spec is SPEC-TOO-STRONG. Each keeps the decision value identical and only
    # reshapes the executable surface, so the reproof stays a `loom_solve` away
    # from the frozen script.
    # =====================================================================
    {
        "id": "pos-negated-guard",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: name the cover via the pure `coversField` selector, negate the
        # suppress guard, and swap the two arms (ok first). Same decision value
        # on every input; proof retuned (the do-block changed shape — `loom_solve`
        # alone closes it because `covered` is now definitionally `coversField`).
        "module": _impl_reproved(
            "    let covered : Bool := coversField constraints usernameField\n"
            "    let out : Verdict :=\n"
            "      if fieldUnique || covered then Verdict.ok\n"
            "      else (if defaultBackendOnly then Verdict.error else Verdict.warning)\n"
            "    return out",
            "prove_correct usernameUniquenessVerdict by\n  loom_solve"),
        "rationale": "binding the cover through the pure `coversField` selector, "
                     "negating the suppress guard and swapping the arms computes "
                     "the SAME verdict on every input (`fieldUnique || covered` is "
                     "the De Morgan dual of `!fieldUnique && !covered`), so the "
                     "ensures still holds; a correct reshape must verify, else "
                     "SPEC-TOO-STRONG on branch order / cover-naming.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO precondition (the pre-conditions
    # region is empty), so the sibling's "a normal input satisfies the
    # precondition" probe is degenerate here (every input is in-domain). The
    # residual admissibility risk on a total-domain spec is that the post-image
    # is DEGENERATE at the interesting point — a spec no impl distinguishes reads
    # exactly like one every impl meets. This case discharges an in-region assert
    # pinning that `coversField` genuinely distinguishes the three sub-behaviors
    # it composes: an unconditional single-field uniqueness constraint COVERS;
    # the same constraint made conditional does NOT; a multi-field one does NOT.
    # The rest of the impl is kept verbatim so the method's own obligation still
    # discharges; the proof is retuned to also close the assert VC.
    # =====================================================================
    {
        "id": "admiss-cover-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_reproved(
            "    assert (with_name_prefix `assert\n"
            "      (coversField [{ fields := [\"u\"], isUnique := true, conditional := false }] \"u\" = true ∧\n"
            "       coversField [{ fields := [\"u\"], isUnique := true, conditional := true }] \"u\" = false ∧\n"
            "       coversField [{ fields := [\"u\", \"v\"], isUnique := true, conditional := false }] \"u\" = false))\n"
            "    let covered := (totalUnique constraints).any (fun fs => fs == [usernameField])\n"
            "    let out : Verdict :=\n"
            "      if !fieldUnique && !covered then\n"
            "        (if defaultBackendOnly then Verdict.error else Verdict.warning)\n"
            "      else Verdict.ok\n"
            "    return out",
            "prove_correct usernameUniquenessVerdict by\n"
            "  loom_solve <;> (try simp_all [coversField]) <;> decide"),
        "rationale": "the post-image is satisfiable AND non-degenerate: the cover "
                     "predicate really distinguishes its three sub-behaviors — an "
                     "unconditional single-field uniqueness constraint covers, the "
                     "same constraint made conditional does not, and a multi-field "
                     "one does not. The in-region assert must discharge (else the "
                     "cover would be constant / the obligation degenerate); the "
                     "impl is kept verbatim so the ensures still discharges too.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is straight-line (its witness reduces under
    # `decide`), refuted at a concrete input by a witness that FAILS on the
    # frozen solution, and carries the refinement argument that its faithful
    # real counterpart would NOT resolve the F2P.
    # =====================================================================
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch skeleton: the verdict is decided ONLY by the field's own
        # direct uniqueness; the declared constraints are never consulted.
        "module": _impl(
            "    let out : Verdict :=\n"
            "      if !fieldUnique then\n"
            "        (if defaultBackendOnly then Verdict.error else Verdict.warning)\n"
            "      else Verdict.ok\n"
            "    return out"),
        "refinement": "this IS the pre-patch behaviour: the identity-field "
                      "uniqueness check consults only the field's own declared-"
                      "unique flag and never the model's declared uniqueness "
                      "constraints. Its faithful real counterpart is the "
                      "unchanged repo, which still reports the hard error for a "
                      "model whose identity field is guaranteed unique ONLY by an "
                      "unconditional single-field uniqueness constraint — exactly "
                      "the failing test, which now asserts no error is reported. "
                      "It would NOT resolve.",
        "rationale": "REJECT from the ensures: on the discriminating sub-domain "
                     "`fieldUnique = false` AND a covering unconditional single-"
                     "field constraint exists (`coversField = true`), the "
                     "post-image demands `Verdict.ok` but the rival reports a "
                     "verdict. Verifying would be SPEC-TOO-WEAK (the constraint "
                     "search is unenforced). Refuted at that sub-domain.",
        "witness": _witness(
            f'usernameUniquenessVerdictTester false [{_c(["username"], True, False)}] '
            '"username" true'),
    },
    {
        "id": "weak-swap-regime",
        "kind": "uniqueness",
        "expect": "reject",
        # Keeps the full decision but INVERTS the severity: warning under the
        # default backend, error otherwise. Correct on every suppress input;
        # wrong on every reported-verdict input.
        "module": _impl(
            "    let covered := (totalUnique constraints).any (fun fs => fs == [usernameField])\n"
            "    let out : Verdict :=\n"
            "      if !fieldUnique && !covered then\n"
            "        (if defaultBackendOnly then Verdict.warning else Verdict.error)\n"
            "      else Verdict.ok\n"
            "    return out"),
        "refinement": "a real patch that swapped the two severity branches "
                      "reports a warning where the default-backend configuration "
                      "requires a hard error, and an error where a custom backend "
                      "should only warn — failing the tests that pin the exact "
                      "diagnostic severity under each backend configuration. It "
                      "would NOT resolve.",
        "rationale": "REJECT from the ensures' severity split: on a reported "
                     "verdict the post-image pins `error` under the default "
                     "backend and `warning` otherwise; the inverted rival "
                     "contradicts both. Refuted at a not-suppressed input under "
                     "`defaultBackendOnly = false` (so the severity binder is "
                     "varied against the other reject witnesses).",
        "witness": _witness(
            'usernameUniquenessVerdictTester false [] "u" false'),
    },
    {
        "id": "weak-always-suppress",
        "kind": "uniqueness",
        "expect": "reject",
        # Always `Verdict.ok`: never reports, ignoring the decision entirely.
        "module": _impl("    let out : Verdict := Verdict.ok\n    return out"),
        "refinement": "always suppressing is what a real patch that deleted the "
                      "report branch entirely would do — it never reports a "
                      "non-unique identity field. It fails every test that "
                      "asserts a verdict IS produced for an identity field that "
                      "is neither directly unique nor covered by an unconditional "
                      "single-field constraint. It would NOT resolve.",
        "rationale": "REJECT from the ensures: on a not-suppressed input "
                     "(`fieldUnique = false`, no cover) the post-image demands a "
                     "verdict but the rival returns `Verdict.ok`. Verifying would "
                     "be SPEC-TOO-WEAK (the report obligation is unpinned). "
                     "Refuted under `defaultBackendOnly = true` (the error arm), "
                     "the branch the swap-regime witness does not probe.",
        "witness": _witness(
            'usernameUniquenessVerdictTester false [] "y" true'),
    },
    {
        "id": "weak-always-report",
        "kind": "uniqueness",
        "expect": "reject",
        # The dual: always reports, ignoring whether the field is already unique.
        "module": _impl(
            "    let out : Verdict :=\n"
            "      if defaultBackendOnly then Verdict.error else Verdict.warning\n"
            "    return out"),
        "refinement": "always reporting is what a real patch that emitted the "
                      "diagnostic outside the uniqueness guard would do — it "
                      "reports even for a genuinely-unique identity field, "
                      "failing every test that asserts no diagnostic is produced "
                      "(including the case where the field's own column is "
                      "declared unique). It would NOT resolve.",
        "rationale": "REJECT from the ensures: on a suppress input "
                     "(`fieldUnique = true`) the post-image demands `Verdict.ok` "
                     "but the rival reports a verdict. Verifying would be "
                     "SPEC-TOO-WEAK (the suppression is unpinned). Refuted with "
                     "`fieldUnique = true` — the only reject witness that moves "
                     "the `fieldUnique` binder to `true`.",
        "witness": _witness(
            'usernameUniquenessVerdictTester true [] "x" false'),
    },
    {
        "id": "weak-cover-membership-not-exact",
        "kind": "uniqueness",
        "expect": "reject",
        # Binder-coverage rival for the single-field-EXACT-match sub-behavior of
        # the cover: treats a MULTI-field unique constraint that merely CONTAINS
        # the identity field as covering it. A multi-column uniqueness constraint
        # does not make either column unique on its own.
        "module": _impl(
            "    let covered := (totalUnique constraints).any (fun fs => fs.contains usernameField)\n"
            "    let out : Verdict :=\n"
            "      if !fieldUnique && !covered then\n"
            "        (if defaultBackendOnly then Verdict.error else Verdict.warning)\n"
            "      else Verdict.ok\n"
            "    return out"),
        "refinement": "a counterpart that treated any uniqueness constraint "
                      "MENTIONING the identity field as guaranteeing it unique "
                      "would wrongly suppress the diagnostic for a model whose "
                      "only relevant constraint is a MULTI-column uniqueness "
                      "constraint — which does not make either column unique on "
                      "its own. The identity field is not actually guaranteed "
                      "unique, so the check must still report; a real patch with "
                      "this bug would leave a genuinely non-unique field "
                      "unreported. It would NOT resolve.",
        "rationale": "REJECT from the ensures via `coversField`'s exact-match "
                     "clause (`fs == [uf]`, a single-element tuple): a rival that "
                     "accepts a multi-field constraint merely containing the field "
                     "suppresses where the post-image demands a verdict. Refuted "
                     "at a multi-field unconditional uniqueness constraint "
                     "containing the identity field (varying `constraints` shape "
                     "and `usernameField`).",
        "witness": _witness(
            f'usernameUniquenessVerdictTester false [{_c(["username", "email"], True, False)}] '
            '"username" true'),
    },
    {
        "id": "weak-cover-ignores-conditional",
        "kind": "uniqueness",
        "expect": "reject",
        # Binder-coverage rival for the `conditional` sub-behavior: counts a
        # CONDITIONAL (partial) single-field uniqueness constraint as covering.
        # A partial constraint applies to only a subset of rows, so it does NOT
        # guarantee uniqueness across all rows.
        "module": _impl(
            "    let covered := constraints.any (fun c => c.isUnique && c.fields == [usernameField])\n"
            "    let out : Verdict :=\n"
            "      if !fieldUnique && !covered then\n"
            "        (if defaultBackendOnly then Verdict.error else Verdict.warning)\n"
            "      else Verdict.ok\n"
            "    return out"),
        "refinement": "a counterpart that dropped the unconditional requirement "
                      "would count a PARTIAL (conditioned) single-field uniqueness "
                      "constraint as guaranteeing the field unique — but a partial "
                      "constraint applies to only a subset of rows and does NOT "
                      "guarantee uniqueness across all of them. It would wrongly "
                      "suppress the diagnostic for a model whose identity field is "
                      "covered only by a conditioned constraint — exactly the "
                      "partially-unique test, which asserts the diagnostic IS "
                      "reported. It would NOT resolve.",
        "rationale": "REJECT from the ensures via `totalUnique`'s unconditional "
                     "filter (`c.isUnique && !c.conditional`): a rival that omits "
                     "the `!conditional` guard treats a conditional constraint as "
                     "covering and suppresses where the post-image demands a "
                     "verdict. Refuted at a single-field CONDITIONAL uniqueness "
                     "constraint (varying the `conditional` attribute, which no "
                     "other reject witness sets to `true`).",
        "witness": _witness(
            f'usernameUniquenessVerdictTester false [{_c(["username"], True, True)}] '
            '"username" false'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 5 uniqueness — one of which is the mandatory frame-
# mutation rival). Every one is accounted for below. The sibling models the same
# decision but over THREE parallel READ-ONLY sequence inputs carrying fractional
# heap permissions, with the existential cover computed by a verified backward
# `while` loop (`any_covers`/`covers` over `ToSeq`); this backend models the same
# decision straight-line over a `List Constraint` with the cover as the pure
# `coversField`/`totalUnique`. The value surface carries across intact; the
# permission surface and the loop do not exist here.
#
#   sibling case            -> here                              disposition
#   -----------------------------------------------------------------------
#   pos-eager-loop          -> pos-negated-guard                 PORTED (reshaped
#                                                                 for straight-line)
#   admiss-reads            -> admiss-cover-nondegenerate         RE-AIMED
#   frame-mut-write         -> (none)                            VACUOUS
#   weak-prepatch           -> weak-prepatch                      PORTED
#   weak-swap-regime        -> weak-swap-regime                   PORTED
#   weak-always-error       -> weak-always-report                PORTED
#   weak-always-suppress    -> weak-always-suppress               PORTED
#   (no sibling)            -> weak-cover-membership-not-exact    ADDED (binder cov.)
#   (no sibling)            -> weak-cover-ignores-conditional     ADDED (binder cov.)
#
# 5 ported, 1 re-aimed, 1 vacuous; 2 binder-coverage rivals added.
#
# VACUOUS (frame-mut-write): the sibling's MANDATORY frame-mutation rival keeps
#   the gold body verbatim then writes back into a read-only sequence input
#   granted only at half permission, and must be rejected for INSUFFICIENT
#   PERMISSION. This backend is referentially transparent: every parameter is an
#   immutable value, the method declares no `mut` binder, there is no heap and no
#   aliasing. There is no read-only input to overwrite and no permission system
#   to trip, so the class is vacuous. No substitute is fabricated.
# RE-AIMED (admissibility): the sibling asserts the three half-permissions admit
#   reading a normal equal-length constraint list. This backend's method has NO
#   precondition and no permission surface, so that probe is degenerate (every
#   input is in-domain). It is re-aimed at the residual total-domain risk — that
#   the post-image is DEGENERATE at the interesting point — via an in-region
#   assert that `coversField` genuinely distinguishes its three sub-behaviors
#   (unconditional single-field covers; conditional does not; multi-field does
#   not).
# PORTED-RESHAPED (pos-eager-loop): the sibling's positive control runs the gold
#   backward loop UNCONDITIONALLY (eager search) then combines
#   `field_unique or found`, keeping every loop invariant / drop-framing assert.
#   This backend's frozen impl is straight-line (no loop), so the sibling's exact
#   loop-eagerness reshape does not exist. The reshape SPIRIT — "structurally
#   different, behaviourally identical, De Morgan-dual guard" — is carried by
#   pos-negated-guard: name the cover via `coversField`, negate the suppress
#   guard, swap the arms. Same verdict on every input; the reproof is `loom_solve`.
# ADDED (2): the sibling's `covers(sp,sg,tt,f) := tt==1 and sp==1 and sg==f`
#   folds single-field-exactness AND unconditionality into scalar flags of one
#   record, so a single rival could not vary them independently. This backend's
#   `coversField`/`totalUnique` expose them as two separable structural clauses
#   (`fs == [uf]` exact-match; `c.isUnique && !c.conditional` unconditional
#   filter), so each gets its own binder-coverage rival:
#     weak-cover-membership-not-exact — attacks the `fs == [uf]` exact-match
#       clause (a multi-field constraint containing the field must NOT cover);
#     weak-cover-ignores-conditional — attacks the `!conditional` filter (a
#       partial/conditioned single-field constraint must NOT cover). This is the
#       precise pairing the failing / partially-unique tests discriminate.
#
# BINDER / CLAUSE COVERAGE of the reject witnesses over the four input binders of
#   the sole ensures (pts = 6 distinct input points):
#     fieldUnique        — false (5 rivals), TRUE (weak-always-report): both.
#     constraints        — [] (swap-regime, always-suppress, always-report);
#                          [unconditional single-field] (prepatch);
#                          [unconditional MULTI-field] (membership-not-exact);
#                          [CONDITIONAL single-field] (ignores-conditional). The
#                          three per-constraint attributes fields/isUnique/
#                          conditional are each moved.
#     usernameField      — "username" / "u" / "x" / "y": varied (never held fixed).
#     defaultBackendOnly — true (prepatch, always-suppress, membership-not-exact),
#                          FALSE (swap-regime, always-report, ignores-conditional):
#                          both severity arms exercised.
#   Every independent top-level behavior of the post-image is attacked: the
#   suppress-vs-report guard (prepatch / always-suppress / always-report), the
#   severity split (swap-regime), and each cover sub-clause (membership-not-exact
#   / ignores-conditional).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; the one deep model
# (`totalUnique`) is an A-reference validated there, and this gate ignores
# AXIOM_TESTS regardless.
AXIOM_TESTS = []
