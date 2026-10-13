"""properties.py — G-PBT falsification battery for django__django-15629 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes. Each
SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside one of the two ``-- impl-start``
/ ``-- impl-end`` regions, or inside a ``prove_correct`` tactic body, is changed
— the consumer spec view elides both, so ``markers.same_spec`` holds and both
``prove_correct`` headers survive intact) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness ELABORATES
against the rival and FAILS against the frozen solution).

DEFENDED SURFACE (two contracted methods, no ``require`` clause on either)

  M1  foreignReferenceColumnDesc (refType : String) (refCheck : Option String)
          (targetCollation : Option String) return (out : ColumnDesc)
        (C1) ensures out = referencingColumnDesc refType refCheck targetCollation
        (C2) ensures out.collation = targetCollation
        (C3) ensures out.sqlType   = refType
        (C4) ensures out.check     = refCheck

  M2  shouldReissueReferences (targetUnique : Bool)
          (oldType newType : String)
          (oldCollation newCollation : Option String) return (out : Bool)
        (D1) ensures out = referencesNeedReissue targetUnique oldType newType
                             oldCollation newCollation
        (D2) ensures out = true → (targetUnique = true ∧ ((oldType != newType) = true
                                     ∨ (oldCollation != newCollation) = true))
        (D3) ensures (targetUnique = true ∧ oldType = newType
                        ∧ oldCollation ≠ newCollation) → out = true

both stated over TRANSPARENT ``pure``-region ``def``s (directive 8 — there is no
opaque answer key anywhere in this bundle; the ``axioms`` region is empty):

  referencingColumnDesc refType refCheck targetCollation =
    { sqlType := refType, check := refCheck, collation := targetCollation }
  referencesNeedReissue targetUnique oldType newType oldCollation newCollation =
    targetUnique && ((oldType != newType) || (oldCollation != newCollation))

WHAT THE SPEC DEFENDS. M1 is the descriptor a *referencing* column reports: a
referencing column owns no independent collation, so it must adopt the collation
of the column it points at while keeping its own storage type and check. The
load-bearing content is C2 — the reported collation is EXACTLY the referenced
column's, in particular a PRESENT collation is carried across rather than
reported as absent. M2 is the decision whether references to an altered column
must be reissued: true exactly when the referenced column can be a reference
target AND something a referencing column mirrors changed. The load-bearing
content is that the collation is one of the mirrored characteristics — D3 pins
the collation-only sub-domain (equal storage type, differing collation) where the
narrower storage-type-only decision is wrong; D2 pins the converse direction (no
reissue without a real, target-eligible change).

BINDER STRUCTURE (read before judging binder coverage). Every input binder of
both predicates is varied by the reject witnesses; the per-binder tally is in the
footer.

  * M1 ``targetCollation`` — the whole point of the construction. Varied over
    ``some "utf8_bin"`` / ``some "nocase"`` / ``some "C"`` / ``some ""`` /
    ``none`` so both the present-collation sub-domain (the one the failing tests
    exercise) and the absent-collation sub-domain are probed. A rival correct
    only on the absent sub-domain is refuted on the present one and vice versa,
    and the empty NAME ``some ""`` is held distinct from absence (mapping.md §2),
    which is what refutes a rival that normalises the two together.
  * M1 ``refCheck`` — carried through unchanged (C4). Varied over ``none`` and
    ``some "chk_len"`` / ``some "len_chk"`` / ``some "gt_zero"`` / ``some "c"``,
    because a rival can both DROP it and confuse it with the collation (both
    ``Option String``), and because a rival can condition its collation handling
    ON it (the guarded-collation partial-domain rival below).
  * M1 ``refType`` — carried through unchanged (C3). Varied over five distinct
    storage types so a rival substituting a wrong type is refutable and no
    witness pins it at one spelling.
  * M2 ``targetUnique`` — the outer gate. Varied over ``true`` and ``false``, so
    a rival that ignores target eligibility entirely is refuted at ``false``
    while every other rival is refuted at ``true``.
  * M2 ``oldType`` / ``newType`` — the storage-type characteristic. Witnesses
    carry both the equal-type points (where the collation must decide alone) and
    the differing-type points (where the type must decide alone), and ``oldType``
    itself takes four distinct values (``varchar(10)`` / ``char(5)`` /
    ``varchar(30)`` / ``text``) so it is not pinned; ``newType`` takes two
    (``varchar(10)`` / ``varchar(20)``), which is what the equal-type and
    differing-type points require and no more.
  * M2 ``oldCollation`` / ``newCollation`` — the collation characteristic.
    Witnesses carry equal-and-absent, equal-and-present, differing-with-one-absent
    and differing-with-both-present points, so the collation comparison is probed
    at the ``none``/``some`` boundary as well as between two present names.

CARRIER NOTE — FULLY TRANSPARENT, NO CONDITIONING NEEDED. Both post-images
reduce, on concrete inputs, to equalities between ``ColumnDesc`` / ``Bool``
values that the kernel computes. A witness reaches the CONTRACT (not a bare
predicate — the spec is a ``method`` triple) through Velvet's own tester
machinery: ``<method>Tester <args> = false`` says the extracted program's result
violates the method's postcondition at that concrete input, and ``decide``
settles it. It is checked in a file whose ``prove_correct`` blocks have been
stripped, so no tactic script can mask the verdict, and neither method declares a
``require`` clause, so every input reaches the postcondition. No witness binds a
hypothesis (no opaque leaf forces conditioning on the carrier), so no witness
carries a joint-satisfiability obligation.

ADVERSARIAL READ of the nagini classes on this carrier:

  * FRAME / PERMISSION-MUTATION (nagini ``frame-mut-write-target``) — VACUOUS,
    and DEMONSTRATED so rather than asserted. The nagini sibling holds its
    referenced-column parameter at a fractional heap permission and its mandatory
    probe WRITES it, so the write must be rejected for insufficient permission.
    Velvet is referentially transparent: every input here is an immutable value,
    neither method declares a ``mut`` binder, and there is no heap, no aliasing
    and no permission system — there is no read-only input to overwrite. The
    mechanical check: the ONLY way to give a rival something to overwrite is to
    add a ``mut`` binder to a method signature, and the signature lives in the
    consumer spec view, so that edit is refused by ``variant_scope`` with
    ``spec view differs (same_spec failed)`` — measured, not argued. A write to
    an immutable binder is not expressible in the impl region either. So the
    class has no in-scope expression on this carrier; no substitute probe is
    fabricated (porting map: vacuous here).
  * UNGROUNDED-ORACLE ECHO — N/A, and for the same reason the nagini sibling
    gives: both post-images are spelled-out ``def``s over the method's own
    inputs, and the ``axioms`` region is empty. There is no answer key to echo,
    so the cheapest impl (return the helper directly) is CORRECT rather than a
    wrong echo, and it ships below as an honest positive control.
  * DIVERGENCE / NON-TERMINATION — nothing to port, but NOT vacuous: see the
    dedicated section below.
  * AXIOM lane (nagini's 3 ``AXIOM_TESTS`` probes) — DROPPED. That lane is
    G-AX's job and this gate ignores ``AXIOM_TESTS`` regardless; this bundle
    declares no axioms and no deep-model references at all (mapping.md §1).

DIVERGENCE LANE - the class is INAPPLICABLE to this impl and CLOSED BY THE
SEMANTICS against any rival that manufactures it. Every frozen impl region is
LOOP-FREE (straight-line a single ``return`` over immutable values, no loop and
no recursion), so there is no control flow here to make diverge: a diverging
rival cannot be obtained by mutating this body, it has to bring a loop of its
own. When it does, the semantics refuse it. This bundle sets
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

CASE COUNT vs NAGINI. The nagini sibling ships 13 SPEC cases over two modeled
functions; this bundle ships 19 over the same two behaviours. Both carriers model
the same pair, so this is not the usual narrowing — the extra cases come from
this backend's richer descriptor (a ``ColumnDesc`` with three independently
attackable fields, two of them ``Option String`` and therefore confusable with
each other) plus one binder nagini does not carry at all (``targetUnique``, the
target-eligibility gate that lives in the modeled decision here). Full
case-by-case accounting in the footer.
"""
from pathlib import Path

INSTANCE = "django__django-15629"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Impl-region anchors. Each is the COMPLETE frozen impl body of one method plus
# its closing `-- impl-end` marker, so every surgery lies wholly inside that
# method's elided `-- impl-start`/`-- impl-end` region and is unique in the file
# (both facts asserted at load by `_swap`). Anchoring on the closing marker as
# well is what keeps a body that also appears in the `pure` region — the two
# helpers spell out the same expressions — from ever being matched there.
# ---------------------------------------------------------------------------
_IMPL1 = ("    return { sqlType := refType, check := refCheck, "
          "collation := targetCollation }\n    -- impl-end")
_IMPL2 = ("    return targetUnique && ((oldType != newType) || "
          "(oldCollation != newCollation))\n    -- impl-end")

assert _BASE.count(_IMPL1) == 1, "M1 impl region drifted from expected text"
assert _BASE.count(_IMPL2) == 1, "M2 impl region drifted from expected text"

# Frozen proof scripts. A variant may retune the tactic body (the spec view
# elides it and `variant_scope` allows a genuine REPROOF), but never the
# `prove_correct` header and never by assuming anything.
_PROOF1 = ("prove_correct foreignReferenceColumnDesc by\n  loom_solve\n"
           "  simp_all [referencingColumnDesc]")
_PROOF2 = ("prove_correct shouldReissueReferences by\n  loom_solve\n"
           "  simp_all [referencesNeedReissue]")

assert _BASE.count(_PROOF1) == 1 and _BASE.count(_PROOF2) == 1


def _impl1(body, src=None):
    """Solution.lean with ONLY M1's impl body replaced."""
    return _swap(src or _BASE, _IMPL1, body + "\n    -- impl-end")


def _impl2(body, src=None):
    """Solution.lean with ONLY M2's impl body replaced."""
    return _swap(src or _BASE, _IMPL2, body + "\n    -- impl-end")


def _reproof(src, frozen_proof, tactics):
    """Retune one `prove_correct` TACTIC BODY, header byte-identical.

    Needed only by the positives whose reshaped impl the frozen script no longer
    closes. Nothing is assumed: no `sorry`/`admit`/`native_decide`, no new
    `axiom`, and no helper lemma — each retuned script is the frozen `loom_solve`
    followed by `simp`/`simp_all` over the same transparent helper the frozen
    script already unfolds.
    """
    header = frozen_proof.split("\n")[0]
    return _swap(src, frozen_proof, header + "\n  loom_solve\n" + tactics)


# ---------------------------------------------------------------------------
# Witness machinery. The spec is a `method` CONTRACT, not a bare predicate, so a
# witness reaches it through Velvet's own tester: `<method>Tester <args> = false`
# says the extracted program's result violates that method's postcondition at
# that concrete input. Every name the witness uses is brought into scope by the
# directives inside the witness itself, so it exists in BOTH the rival build and
# the gold build by construction. No witness binds a hypothesis — the carrier is
# fully transparent, so no conditioning (and no joint-satisfiability obligation)
# is needed.
# ---------------------------------------------------------------------------
def _witness(method, call):
    return (f"extract_program_for {method}\n"
            f"prove_precondition_decidable_for {method}\n"
            f"prove_postcondition_decidable_for {method}\n"
            f"derive_tester_for {method}\n\n"
            f"example : {call} = false := by\n  decide\n")


def _w1(args):
    return _witness("foreignReferenceColumnDesc",
                    f"foreignReferenceColumnDescTester {args}")


def _w2(args):
    return _witness("shouldReissueReferences",
                    f"shouldReissueReferencesTester {args}")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Each was confirmed with a real
    # build against the frozen spec. Where the frozen tactic script no longer
    # closes the reshaped impl, the script is retuned inside the elided proof
    # body only — the `prove_correct` header is byte-identical and nothing is
    # assumed.
    # =====================================================================
    {
        "id": "pos-fn1-field-order",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: stage the descriptor in a typed local and list its fields in a
        # different order (storage type, collation, check). Structure literals are
        # field-name-keyed, so the constructed value is definitionally identical;
        # the frozen script still closes. Ports the nagini dict-key-order positive.
        "module": _impl1(
            "    let d : ColumnDesc :=\n"
            "      { sqlType := refType, collation := targetCollation, "
            "check := refCheck }\n"
            "    return d"),
        "rationale": (
            "structurally-different CORRECT impl of M1: the descriptor is staged "
            "in a typed local and its fields are listed in a different order "
            "(type, collation, check rather than type, check, collation). Field "
            "order in a structure literal is not semantic, so the returned value "
            "is definitionally the frozen one and all four clauses C1-C4 still "
            "discharge under the frozen tactic script. Ports the nagini "
            "pos-fn1-reorder / pos-fn1-temp shapes (build the reported descriptor "
            "in a different order, via a local). If it cannot verify the spec is "
            "over-fit to one spelling => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-fn1-via-helper",
        "kind": "soundness",
        "expect": "verify",
        # The cheapest impl satisfying C1: return the transparent helper directly.
        # This is the honest no-echo control — the helper is a spelled-out `def`
        # over M1's own three inputs, not an opaque answer key, so returning it
        # still performs the real construction. The frozen script closes C1 but
        # leaves C2/C3 needing the helper unfolded, so the proof body is retuned.
        "module": _reproof(
            _impl1("    return referencingColumnDesc refType refCheck "
                   "targetCollation"),
            _PROOF1, "  all_goals simp [referencingColumnDesc]"),
        "rationale": (
            "the cheapest impl satisfying C1 returns the transparent helper "
            "directly. Because the post-image is a spelled-out function of M1's "
            "own three inputs — NOT an axiomatized answer key (the axioms region "
            "is empty) — this still does the real construction, so it must "
            "verify; it demonstrates the spec is not echo-vulnerable (a wrong "
            "echo would have to be a reject case, and none exists). Re-expresses "
            "the nagini grounded-@Pure-reference control. The tactic body is "
            "retuned (frozen `loom_solve` + `simp` over the SAME transparent "
            "helper the frozen script already unfolds) because the reshaped impl "
            "leaves C2/C3 needing that unfolding; the `prove_correct` header is "
            "byte-identical and nothing is assumed. If it cannot verify => "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-fn2-nested-if",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: an explicit two-level branch over the eligibility gate and the
        # storage-type characteristic instead of the single guarded disjunction.
        # Returns exactly the same Bool on every input. Ports nagini's
        # pos-fn2-branch (if/return over the two characteristics).
        "module": _reproof(
            _impl2(
                "    if targetUnique then\n"
                "      if oldType != newType then\n"
                "        return true\n"
                "      else\n"
                "        return oldCollation != newCollation\n"
                "    else\n"
                "      return false"),
            _PROOF2, "  all_goals simp_all [referencesNeedReissue]"),
        "rationale": (
            "structurally-different CORRECT impl of M2: an explicit nested "
            "branch over the eligibility gate and then the storage-type "
            "characteristic, falling through to the collation comparison, "
            "instead of the single guarded disjunction. It returns true exactly "
            "when the target is eligible and either characteristic differs, and "
            "false otherwise, so D1/D2/D3 all still hold. Ports the nagini "
            "pos-fn2-branch if/return shape. The tactic body is retuned "
            "(`loom_solve` + `simp_all` over the same transparent helper) to "
            "discharge the extra branch goals; header byte-identical, nothing "
            "assumed. If it cannot verify => SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-fn2-disjunct-order",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: test the collation characteristic BEFORE the storage-type one.
        # Boolean `||` is commutative, so the decision is unchanged; this is the
        # canonical "reshaped but correct" case the witness requirement exists
        # for, and it is shipped as a POSITIVE precisely so a merely-commuted impl
        # is never mistaken for a wrong one.
        "module": _reproof(
            _impl2("    return targetUnique && ((oldCollation != newCollation) "
                   "|| (oldType != newType))"),
            _PROOF2,
            "  all_goals simp_all [referencesNeedReissue, Bool.or_comm]"),
        "rationale": (
            "structurally-different CORRECT impl of M2: the collation "
            "characteristic is tested before the storage-type one. Boolean "
            "disjunction is commutative so the decision is pointwise identical "
            "and D1/D2/D3 hold. This is deliberately the commuted-operand shape "
            "that breaks a frozen tactic script WITHOUT being wrong — shipping it "
            "as an expect=verify control is what keeps the battery from reading "
            "tactic breakage as spec strength. The tactic body is retuned "
            "(`loom_solve` + `simp_all` over the same helper plus commutativity "
            "of `||`); header byte-identical, nothing assumed. If it cannot "
            "verify => SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — neither method declares a `require` clause, so the usual
    # "a normal input satisfies the precondition" probe is vacuous. The residual
    # admissibility risk on a total domain is that the post-image is
    # UNSATISFIABLE or DEGENERATE: a spec no impl can meet, or one that pins the
    # same answer everywhere, reads exactly like a spec every impl meets. Each
    # case below discharges a LIVE in-region assert that the post-image takes
    # DIFFERENT values on the two sub-domains the failing tests straddle, at
    # concrete test-shaped inputs. The real impl is kept unchanged so the
    # method's own obligation still discharges too. This is the nagini
    # admiss-fn1-f2p-shaped case re-aimed at the risk this carrier actually has.
    # =====================================================================
    {
        "id": "admiss-fn1-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _reproof(
            _impl1(
                "    assert (with_name_prefix `adm\n"
                "      ((referencingColumnDesc \"varchar(10)\" none "
                "(some \"utf8_bin\")).collation = some \"utf8_bin\"\n"
                "       ∧ (referencingColumnDesc \"varchar(10)\" none "
                "none).collation = none))\n"
                "    return { sqlType := refType, check := refCheck, "
                "collation := targetCollation }"),
            _PROOF1, "  all_goals simp [referencingColumnDesc]"),
        "rationale": (
            "M1 declares no `require`, so precondition admissibility is vacuous; "
            "this discharges the residual risk that M1's post-image is "
            "unsatisfiable or DEGENERATE. The live in-region assert establishes "
            "that at a test-shaped referenced-column collation the reported "
            "collation is that PRESENT collation, while with no referenced "
            "collation it is absent — i.e. the post-image genuinely distinguishes "
            "the two sub-domains the failing tests straddle and is jointly "
            "satisfiable at both. The real impl is kept so C1-C4 still discharge, "
            "and the assert is live (it is inside the elided impl region, so no "
            "new declaration and same_spec holds). Re-aims the nagini "
            "admiss-fn1-f2p-shaped control, whose fractional-permission half has "
            "no counterpart on this carrier. If the assert cannot discharge the "
            "post-image is degenerate/unsatisfiable => PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "admiss-fn2-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _reproof(
            _impl2(
                "    assert (with_name_prefix `adm\n"
                "      (referencesNeedReissue true \"varchar(10)\" "
                "\"varchar(10)\" none (some \"utf8_bin\") = true\n"
                "       ∧ referencesNeedReissue true \"varchar(10)\" "
                "\"varchar(10)\" none none = false))\n"
                "    return targetUnique && ((oldType != newType) || "
                "(oldCollation != newCollation))"),
            _PROOF2, "  all_goals simp [referencesNeedReissue]"),
        "rationale": (
            "M2 declares no `require`, so precondition admissibility is vacuous; "
            "this discharges the residual risk that M2's post-image is "
            "unsatisfiable or DEGENERATE. The live in-region assert establishes "
            "the decision is TRUE on the collation-only-change point (eligible "
            "target, equal storage type, collation appearing) and FALSE on the "
            "nothing-changed point at the same storage type — so the decision is "
            "not constant and both truth values are reachable at test-shaped "
            "inputs. The real impl is kept so D1-D3 still discharge. If the "
            "assert cannot discharge => PRECOND-TOO-STRONG."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Every one carries a machine-checked refutation
    # witness at a concrete input: it ELABORATES against the rival and FAILS
    # against the frozen solution (both halves confirmed with real builds, 13
    # rivals x 4 builds counting the flipped-claim forgery control, whose exit
    # codes invert on both sides). Each also carries the refinement argument
    # for why its faithful real counterpart would NOT resolve the failing tests,
    # so a rival that verified would be a true verify-does-not-imply-resolve
    # break rather than an artifact.
    # ---- M1 rivals: the reported descriptor of a referencing column ----
    # =====================================================================
    {
        "id": "fn1-drop-collation",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-change behaviour (Solution_prepatch.lean): the referencing
        # column reports no collation of its own and ignores the referenced
        # column's. Correct on the absent-collation sub-domain, wrong on exactly
        # the present-collation sub-domain the failing tests exercise.
        "module": _impl1("    return { sqlType := refType, check := refCheck, "
                         "collation := none }"),
        "refinement": (
            "This is the pre-change behaviour, and it is the load-bearing half "
            "of the fix. Its faithful real counterpart is the unpatched "
            "descriptor: a referencing column reports only its storage type and "
            "check, so every consumer that reads the reported collation sees "
            "nothing and the referencing column is emitted with no collation "
            "clause. Both failing tests observe a referencing column carrying "
            "the referenced column's collation — one on creation of the "
            "referencing model, one after the referenced column's collation is "
            "altered — and neither can pass while the reported collation is "
            "absent. The reported behaviour in the issue is exactly this: the "
            "reference-constraint statements fail because the referencing "
            "column's collation was never emitted. So this rival's faithful "
            "patch would NOT resolve."
        ),
        "rationale": (
            "REJECT from C2 (out.collation = targetCollation), and equally from "
            "C1: at a referenced collation of `some \"utf8_bin\"` the "
            "post-image's collation is `some \"utf8_bin\"` but this impl reports "
            "`none`, so the descriptors differ. Correct on the whole "
            "absent-collation sub-domain, wrong on exactly the present-collation "
            "sub-domain. Refuted at refType=\"varchar(10)\", refCheck=none, "
            "targetCollation=some \"utf8_bin\" — the present-collation point. If "
            "it verified => SPEC-TOO-WEAK (the entire regression would go "
            "unnoticed). Ports nagini uniq-fn1-drop-collation."
        ),
        "witness": _w1('"varchar(10)" none (some "utf8_bin")'),
    },
    {
        "id": "fn1-empty-collation",
        "kind": "uniqueness",
        "expect": "reject",
        # Reports a PRESENT but content-free collation regardless of the
        # referenced column's. A strictly harder near-miss than
        # fn1-drop-collation: it clears any weaker "reports some collation"
        # reading of the clause and fails only on the VALUE.
        "module": _impl1("    return { sqlType := refType, check := refCheck, "
                         "collation := some \"\" }"),
        "refinement": (
            "Its faithful real counterpart reports a present-but-empty collation "
            "for the referencing column no matter what the referenced column "
            "declares. The referencing column would be emitted naming an empty "
            "collation (or, on backends that treat empty as absent, none at "
            "all), which does not agree with the referenced column; the failing "
            "tests read back the referencing column's collation and compare it "
            "to the referenced column's non-default collation, so an empty value "
            "does not match and would NOT resolve. It is also wrong in the other "
            "direction: when the referenced column declares NO collation this "
            "rival still reports one, which would emit a spurious collation "
            "clause on a column that should have none."
        ),
        "rationale": (
            "REJECT from C2 (and C1): the reported collation is a fixed present "
            "value independent of `targetCollation`, so at any referenced "
            "collation other than the empty string the descriptors differ. This "
            "is the VALUE-level attack on C2 — distinct from "
            "fn1-drop-collation, which attacks presence — so a reading of the "
            "clause satisfied by reporting merely SOME collation is refuted too. "
            "Refuted at refType=\"char(8)\", refCheck=none, targetCollation=some "
            "\"nocase\" (a different storage type and a different collation name "
            "from every other witness). Ports nagini uniq-fn1-empty-collation."
        ),
        "witness": _w1('"char(8)" none (some "nocase")'),
    },
    {
        "id": "fn1-guarded-collation",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: adopt the referenced collation only when the
        # referencing column imposes no check of its own; otherwise report none.
        # A strict near-miss that agrees with gold over the whole no-check
        # sub-domain, so it needs — and gets — a witness on the with-check side.
        "module": _impl1(
            "    match refCheck with\n"
            "    | none   => return { sqlType := refType, check := none, "
            "collation := targetCollation }\n"
            "    | some c => return { sqlType := refType, check := some c, "
            "collation := none }"),
        "refinement": (
            "Its faithful real counterpart adopts the referenced column's "
            "collation only for referencing columns that impose no check of "
            "their own, and silently drops it for the rest. Nothing about the "
            "behaviour at issue depends on whether the referencing column "
            "carries a check — a reference-constraint between columns of "
            "mismatched collation is rejected either way — so this half-fix "
            "leaves every checked referencing column with the pre-change defect. "
            "It is a plausible-looking patch (it 'adds the collation' and passes "
            "on the simplest models) that still fails the reported scenario for "
            "any referencing column with a check, so it would NOT resolve in "
            "general; it is the partial-domain shape a spec must forbid rather "
            "than a wholesale reversion."
        ),
        "rationale": (
            "REJECT from C2 (and C1): on the with-check sub-domain the "
            "post-image's collation is `targetCollation` but this impl reports "
            "`none`. The rival agrees with the frozen solution on the ENTIRE "
            "no-check sub-domain, so it is a genuine near-miss and is refuted at "
            "the point that distinguishes it — refType=\"text\", refCheck=some "
            "\"len_chk\", targetCollation=some \"C\" — rather than at any point "
            "shared with fn1-drop-collation. Demonstrates the spec's dependence "
            "on `refCheck` NOT influencing the reported collation."
        ),
        "witness": _w1('"text" (some "len_chk") (some "C")'),
    },
    {
        "id": "fn1-swap-check-collation",
        "kind": "uniqueness",
        "expect": "reject",
        # Confuses the two `Option String` fields: reports the referenced
        # collation as the check and the own check as the collation. Attacks C2
        # and C4 simultaneously and is refutable only where the two differ.
        "module": _impl1("    return { sqlType := refType, check := "
                         "targetCollation, collation := refCheck }"),
        "refinement": (
            "Its faithful real counterpart populates the two optional "
            "descriptor entries from each other's source — the referencing "
            "column's check expression is emitted as its collation and the "
            "referenced column's collation is emitted as a check constraint. "
            "The referencing column then both carries the wrong collation "
            "(failing the collation read-back the failing tests perform) and "
            "acquires a nonsensical check, so it would NOT resolve and would "
            "additionally corrupt column emission for referencing columns that "
            "have a check. This is the field-confusion failure mode that a "
            "carrier with two same-typed optional entries makes available and a "
            "descriptor-shape clause must forbid."
        ),
        "rationale": (
            "REJECT from C2 and C4 jointly (and C1): with refCheck=some "
            "\"chk_len\" and targetCollation=some \"utf8_bin\" the post-image "
            "wants check=some \"chk_len\", collation=some \"utf8_bin\" but this "
            "impl returns them exchanged. Refutable ONLY where the two optionals "
            "differ, which is why the witness carries a distinct present value "
            "in each — refType=\"varchar(22)\", refCheck=some \"chk_len\", "
            "targetCollation=some \"utf8_bin\". The only rival attacking C4 and "
            "C2 together."
        ),
        "witness": _w1('"varchar(22)" (some "chk_len") (some "utf8_bin")'),
    },
    {
        "id": "fn1-drop-check",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks C4 ALONE: the referenced collation is carried correctly, but
        # the referencing column's own check is dropped. The pass-through clause
        # the fix must not regress while adding the collation.
        "module": _impl1("    return { sqlType := refType, check := none, "
                         "collation := targetCollation }"),
        "refinement": (
            "Its faithful real counterpart adds the collation entry but stops "
            "reporting the referencing column's own check expression. That is a "
            "regression of behaviour the change is required to LEAVE ALONE: "
            "referencing columns that impose a check would be emitted without "
            "it, so constraints present before the change silently disappear "
            "and the previously-passing column-emission tests break. A patch "
            "that resolves the collation scenario by rewriting the reported "
            "descriptor wholesale, rather than adding one entry to it, is "
            "exactly this shape — it does not resolve, because resolution "
            "requires the failing tests to pass WITHOUT breaking the passing "
            "ones."
        ),
        "rationale": (
            "REJECT from C4 (out.check = refCheck) alone — the collation and "
            "type clauses C2/C3 hold, so this isolates the check pass-through "
            "clause, which no other rival attacks on its own. Refuted at "
            "refType=\"varchar(64)\", refCheck=some \"gt_zero\", "
            "targetCollation=none: note the ABSENT referenced collation, which "
            "also demonstrates the battery attacks M1 on the no-collation "
            "sub-domain and not only where a collation is present."
        ),
        "witness": _w1('"varchar(64)" (some "gt_zero") none'),
    },
    {
        "id": "fn1-target-type",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks C3 ALONE: collation and check are carried correctly, but the
        # referencing column's own storage type is replaced by a fixed value.
        "module": _impl1("    return { sqlType := \"\", check := refCheck, "
                         "collation := targetCollation }"),
        "refinement": (
            "Its faithful real counterpart reports a content-free storage type "
            "for the referencing column while getting the collation right. A "
            "referencing column emitted with no storage type is not valid column "
            "definition at all, so the referencing table cannot be created or "
            "remade; both failing tests create or remake the referencing table "
            "before reading its collation back, so this would NOT resolve, and "
            "it would break every previously-passing test that builds a "
            "referencing column. The storage type is the entry the change must "
            "preserve verbatim while adding the collation."
        ),
        "rationale": (
            "REJECT from C3 (out.sqlType = refType) alone — C2 and C4 hold, so "
            "this isolates the storage-type pass-through clause, which no other "
            "rival attacks on its own. Refuted at refType=\"varchar(10)\", "
            "refCheck=some \"c\", targetCollation=none — a fifth distinct "
            "refType/refCheck pairing, and a second probe of the "
            "absent-collation sub-domain."
        ),
        "witness": _w1('"varchar(10)" (some "c") none'),
    },

    {
        "id": "fn1-normalize-empty-collation",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN, added by audit. Carries the referenced collation
        # faithfully EXCEPT when it is the empty name `some ""`, which it folds to
        # `none`. Agrees with the frozen solution on every other input in the whole
        # domain — a strictly harder near-miss than fn1-drop-collation and
        # fn1-empty-collation, both of which are wrong on a whole sub-domain — so
        # it is refuted only at the one point the collapse happens.
        "module": _impl1(
            "    match targetCollation with\n"
            "    | some \"\" => return { sqlType := refType, check := refCheck, "
            "collation := none }\n"
            "    | c       => return { sqlType := refType, check := refCheck, "
            "collation := c }"),
        "refinement": (
            "Its faithful real counterpart adopts the referenced column's "
            "collation but treats a declared empty collation name as no collation "
            "at all, normalising it away. The mapping table for this carrier "
            "records the empty string as a DISTINCT present value from an absent "
            "collation, so this rival reports absence where the referenced column "
            "declares a present (if degenerate) name, and the referencing column "
            "would be emitted with no collation clause while its target has one — "
            "reinstating exactly the mismatch at issue on that sub-domain. It is "
            "the 'normalise the input before comparing' shape a spec pinning an "
            "EXACT carry-across must forbid: plausible-looking, correct almost "
            "everywhere, and silently lossy at one point, so it would NOT resolve "
            "in general."
        ),
        "rationale": (
            "REJECT from C2 (out.collation = targetCollation) and C1: at "
            "targetCollation=some \"\" the post-image's collation is some \"\" "
            "but this impl reports none. Added by audit: every other M1 rival is "
            "wrong on a whole sub-domain, so none of their witnesses reaches the "
            "empty-collation-name point, and no prior witness bound "
            "targetCollation to `some \"\"` at all. Refuted at "
            "refType=\"varchar(22)\", refCheck=some \"chk\", "
            "targetCollation=some \"\" — the ONLY input where this rival and the "
            "frozen solution differ, which is what makes it the tightest "
            "near-miss in the battery. Confirmed with real builds: the witness "
            "elaborates against the rival (exit 0) and gold refutes it by kernel "
            "evaluation (exit 1, `decide` proved the tester equation false)."
        ),
        "witness": _w1('"varchar(22)" (some "chk") (some "")'),
    },

    # ---- M2 rivals: the reissue decision for references to an altered column
    {
        "id": "fn2-type-only",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-change behaviour (Solution_prepatch_2.lean): reissue only on a
        # storage-type difference, ignoring the collation. Correct everywhere the
        # type changes; wrong on exactly the collation-only sub-domain.
        "module": _impl2("    return targetUnique && (oldType != newType)"),
        "refinement": (
            "This is the pre-change decision, and it is the second load-bearing "
            "half of the fix. Its faithful real counterpart reissues the columns "
            "that reference an altered column only when the altered column's "
            "storage type differs, so an alteration that changes ONLY the "
            "collation never reaches the referencing columns and they keep the "
            "old collation. The failing test that alters a referenced column's "
            "collation does exactly that — the storage type is unchanged, only "
            "the collation appears — and then asserts the referencing columns "
            "carry the new collation. Under this decision they are never "
            "reissued, so it does NOT resolve. Reproduced independently as the "
            "second frozen pre-image."
        ),
        "rationale": (
            "REJECT from D3 (an eligible target with equal storage type and "
            "differing collation must reissue), and equally from D1: at "
            "targetUnique=true, oldType=newType=\"varchar(10)\", "
            "oldCollation=none, newCollation=some \"utf8_bin\" the spec demands "
            "true but the storage-type-only decision yields false. Correct on "
            "the entire type-change sub-domain; wrong on exactly the "
            "collation-only sub-domain. If it verified => SPEC-TOO-WEAK (the "
            "alter regression would go unnoticed). Ports nagini "
            "uniq-fn2-type-only."
        ),
        "witness": _w2('true "varchar(10)" "varchar(10)" none (some "utf8_bin")'),
    },
    {
        "id": "fn2-collation-only",
        "kind": "uniqueness",
        "expect": "reject",
        # The symmetric partial-domain rival: the collation disjunct REPLACES the
        # storage-type one instead of joining it.
        "module": _impl2("    return targetUnique && (oldCollation != "
                         "newCollation)"),
        "refinement": (
            "Its faithful real counterpart adds the collation condition but "
            "DROPS the pre-existing storage-type condition, so an alteration "
            "that widens or retypes a referenced column no longer reissues the "
            "columns that reference it. That regresses behaviour the tests "
            "already relied on before the change — the previously-passing alter "
            "tests observe referencing columns being reissued on a "
            "referenced-column type change — so it would NOT resolve even though "
            "it fixes the new collation scenario. The symmetric half-fix to "
            "fn2-type-only."
        ),
        "rationale": (
            "REJECT from D1 (out = referencesNeedReissue …): at "
            "targetUnique=true, oldType=\"varchar(10)\", newType=\"varchar(20)\" "
            "with oldCollation=newCollation=some \"nocase\" the post-image is "
            "true but this decision yields false. Note the witness holds the "
            "collation EQUAL AND PRESENT — a point no other witness carries, so "
            "it also probes the collation comparison between two identical "
            "present names rather than at the none/some boundary. Ports nagini "
            "uniq-fn2-collation-only."
        ),
        "witness": _w2('true "varchar(10)" "varchar(20)" (some "nocase") '
                       '(some "nocase")'),
    },
    {
        "id": "fn2-both-required",
        "kind": "uniqueness",
        "expect": "reject",
        # Conjunction instead of disjunction: reissue only when BOTH
        # characteristics differ. Wrong on both single-change sub-domains.
        "module": _impl2("    return targetUnique && ((oldType != newType) && "
                         "(oldCollation != newCollation))"),
        "refinement": (
            "Its faithful real counterpart joins the two conditions with 'and' "
            "rather than 'or', so neither a storage-type-only nor a "
            "collation-only alteration reissues the referencing columns. It "
            "fails the new collation scenario AND regresses the pre-existing "
            "type-change behaviour — strictly worse than either single-condition "
            "rival — so it would NOT resolve. A plausible transcription slip "
            "when a second condition is added to an existing guard."
        ),
        "rationale": (
            "REJECT from D3 and from D1: the conjunction is false on either "
            "single-change sub-domain while the post-image is true there. "
            "Refuted at targetUnique=true, oldType=\"char(5)\", "
            "newType=\"varchar(20)\", oldCollation=newCollation=none — the "
            "type-changes-alone point with both collations ABSENT, so this "
            "witness probes a sub-domain distinct from both single-condition "
            "rivals and carries an oldType (\"char(5)\") no other witness uses. "
            "Ports nagini uniq-fn2-and."
        ),
        "witness": _w2('true "char(5)" "varchar(20)" none none'),
    },
    {
        "id": "fn2-ignore-unique",
        "kind": "uniqueness",
        "expect": "reject",
        # Drops the target-eligibility gate: reissues on any characteristic
        # change even for a column nothing can reference. This is the binder
        # nagini's carrier does not model at all, so the rival is new work.
        "module": _impl2("    return (oldType != newType) || (oldCollation != "
                         "newCollation)"),
        "refinement": (
            "Its faithful real counterpart reissues referencing columns whenever "
            "an altered column's type or collation changes, without first "
            "checking that the altered column can even be a reference target. "
            "Every ordinary column alteration would then trigger the "
            "reference-reissue path — remaking unrelated tables and emitting "
            "reference-rebuild statements where none is warranted — which breaks "
            "the previously-passing alteration tests that assert no such churn. "
            "It would therefore NOT resolve, since resolution requires the "
            "passing tests to keep passing. This over-trigger rival attacks a "
            "gate the nagini carrier does not model, so it has no sibling case."
        ),
        "rationale": (
            "REJECT from D2 (out = true implies the target is eligible), and "
            "equally from D1: at targetUnique=false with a differing storage "
            "type the post-image is false but this impl yields true. THE ONLY "
            "rival refuted at targetUnique=false, so it is what keeps that "
            "binder from being pinned at true across the battery — a rival "
            "mishandling only the ineligible-target sub-domain would otherwise "
            "verify unnoticed. Refuted at targetUnique=false, "
            "oldType=\"varchar(30)\", newType=\"varchar(20)\", oldCollation=some "
            "\"C\", newCollation=none (also the only witness with a present-to-"
            "absent collation transition)."
        ),
        "witness": _w2('false "varchar(30)" "varchar(20)" (some "C") none'),
    },
    {
        "id": "fn2-always",
        "kind": "uniqueness",
        "expect": "reject",
        # Constant true: always reissue. The over-trigger extreme, refuted on the
        # nothing-changed point.
        "module": _impl2("    return true"),
        "refinement": (
            "Its faithful real counterpart drops the guard entirely and reissues "
            "the columns that reference an altered column on every alteration. "
            "It would emit reference-rebuild statements for alterations that "
            "change nothing a referencing column mirrors, breaking the "
            "previously-passing alter tests that assert no reference churn on an "
            "unrelated alteration, and would remake tables unnecessarily. It "
            "does NOT resolve. Ports nagini uniq-fn2-const-true."
        ),
        "rationale": (
            "REJECT from D2 (and D1): with an eligible target but equal storage "
            "type and equal absent collation, nothing a referencing column "
            "mirrors changed, so the post-image is false while this impl yields "
            "true. Refuted at targetUnique=true, "
            "oldType=newType=\"varchar(10)\", oldCollation=newCollation=none — "
            "the nothing-changed point, which only this rival probes."
        ),
        "witness": _w2('true "varchar(10)" "varchar(10)" none none'),
    },
    {
        "id": "fn2-never",
        "kind": "uniqueness",
        "expect": "reject",
        # Constant false: never reissue. The under-trigger extreme; a supporting
        # near-miss refuted where BOTH characteristics change.
        "module": _impl2("    return false"),
        "refinement": (
            "Its faithful real counterpart removes the reference-reissue path "
            "altogether, so referencing columns are never reissued — the new "
            "collation scenario fails and the pre-existing type-change behaviour "
            "regresses. It does NOT resolve. Supporting near-miss at the "
            "opposite extreme from fn2-always, so the decision is pinned from "
            "both directions. Ports nagini uniq-fn2-const-false."
        ),
        "rationale": (
            "REJECT from D3 and D1: on any real change to an eligible target the "
            "post-image is true while this impl yields false. Refuted at "
            "targetUnique=true, oldType=\"text\", newType=\"varchar(20)\", "
            "oldCollation=some \"nocase\", newCollation=some \"utf8_bin\" — the "
            "only witness where BOTH characteristics change and both collations "
            "are present-and-distinct, so it probes the collation comparison "
            "between two different present names."
        ),
        "witness": _w2('true "text" "varchar(20)" (some "nocase") '
                       '(some "utf8_bin")'),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery ships 13 SPEC cases (3
# soundness positives, 1 admissibility, 1 frame-mutation, 8 uniqueness rivals)
# plus a 3-case AXIOM lane. Both carriers model the SAME two behaviours — the
# descriptor a referencing column reports, and the reissue decision for
# references to an altered column — so this is not the usual carrier narrowing:
# every sibling SPEC case except the permission probe has a counterpart here.
#
#   sibling case                -> here                          disposition
#   ---------------------------------------------------------------------------
#   pos-fn1-reorder             -> pos-fn1-field-order            PORTED (merged)
#   pos-fn1-temp                -> pos-fn1-field-order            PORTED (merged)
#   pos-fn2-branch              -> pos-fn2-nested-if              PORTED
#   admiss-fn1-f2p-shaped       -> admiss-fn1-nondegenerate       RE-AIMED
#                                  + admiss-fn2-nondegenerate     RE-AIMED (new)
#   frame-mut-write-target      -> (none)                         VACUOUS
#   uniq-fn1-drop-collation     -> fn1-drop-collation             PORTED
#   uniq-fn1-wrong-collation    -> fn1-swap-check-collation       RE-EXPRESSED
#   uniq-fn1-empty-collation    -> fn1-empty-collation            PORTED
#   uniq-fn1-spurious-entry     -> (none)                         NO COUNTERPART
#   uniq-fn2-type-only          -> fn2-type-only                  PORTED
#   uniq-fn2-collation-only     -> fn2-collation-only             PORTED
#   uniq-fn2-and                -> fn2-both-required              PORTED
#   uniq-fn2-const-true         -> fn2-always                     PORTED
#   uniq-fn2-const-false        -> fn2-never                      PORTED
#   AXIOM_TESTS (3)             -> (none)                         DROPPED (G-AX)
#                                  + pos-fn1-via-helper           ADDED
#                                  + pos-fn2-disjunct-order       ADDED
#                                  + fn1-guarded-collation        ADDED
#                                  + fn1-drop-check               ADDED
#                                  + fn1-target-type              ADDED
#                                  + fn2-ignore-unique            ADDED
#                                  + fn1-normalize-empty-collation ADDED (audit)
#
# 8 ported, 1 re-expressed, 1 re-aimed (into 2), 2 merged into 1, 1 vacuous,
# 1 no-counterpart, 3 dropped; 7 cases added for clause/binder coverage this
# carrier requires and nagini's does not have.
#
# PORTED (8): the collation-adoption rivals and the reissue-decision rivals carry
#   across intact; only the carrier changes, from a params dict keyed by three
#   opaque int tokens to a `ColumnDesc` structure with named fields, and from
#   `differs(a, b)` over int identities to Lean `!=` over `String` /
#   `Option String`. Each keeps its sibling's refinement argument, re-grounded in
#   the actual failing-test behaviour.
# MERGED (pos-fn1-reorder + pos-fn1-temp -> pos-fn1-field-order): the sibling
#   needs two positives because a dict is built by successive key WRITES, so
#   "different write order" and "stage the value in a temporary" are different
#   reshapes. Here the descriptor is a single structure literal, so both collapse
#   into one shape — a typed local staging the literal with its fields in a
#   different order. Reordering fields alone is not even semantic on this carrier
#   (structure literals are field-name-keyed), so a second case would be a
#   duplicate rather than added coverage.
# RE-EXPRESSED (uniq-fn1-wrong-collation -> fn1-swap-check-collation): the
#   sibling reports the referencing column's own type identity as its collation,
#   which is natural there because all three dict values inhabit one int carrier.
#   The same attack is EXPRESSIBLE here — `collation := some refType` typechecks
#   and is rejected by the frozen spec (audit built it) — but it is a value-level
#   C2 attack of the kind fn1-empty-collation already carries, differing only in
#   that the wrong value is derived from an input rather than constant. The
#   re-expression chosen instead is the confusion this carrier uniquely admits:
#   the two same-typed optional entries reported in each other's slot, which
#   attacks C2 and C4 JOINTLY and so covers strictly more clause surface than the
#   direct transliteration would. Same attack class (a present collation with the
#   wrong value), aimed at this carrier's own failure mode.
# RE-AIMED (admiss-fn1-f2p-shaped -> admiss-fn1/fn2-nondegenerate): the sibling's
#   admissibility case asserts a freshly-built input satisfies a precondition
#   that demands a fractional heap permission and a key's presence. Neither
#   method here declares a `require` clause at all, so that probe is vacuous;
#   it is re-aimed at the residual risk a total domain does have — an
#   UNSATISFIABLE or DEGENERATE post-image, which reads exactly like a spec every
#   impl meets. Each of the two methods gets one, since each has its own
#   post-image; both discharge a live in-region assert that the post-image takes
#   DIFFERENT values across the two sub-domains the failing tests straddle.
# VACUOUS (frame-mut-write-target): the sibling's mandatory permission probe
#   writes a read-only input held at half permission and must be rejected for
#   insufficient permission. This backend is referentially transparent — every
#   input is an immutable value, neither method declares a `mut` binder, and
#   there is no heap, no aliasing and no permission system — so there is no
#   read-only input to overwrite and the class collapses. No substitute is
#   fabricated.
# NO COUNTERPART (uniq-fn1-spurious-entry): the sibling reports a fourth,
#   spurious key alongside the three real ones, refuted by its no-spurious-keys
#   quantifier. The descriptor here is a `structure` with exactly three fields,
#   so a spurious entry is not expressible — the type system forbids what that
#   quantifier has to forbid by contract, and the corresponding clause therefore
#   does not exist in the frozen spec. A carrier fact, not an omission for
#   difficulty.
# DROPPED (AXIOM_TESTS x3): the axiom lane is G-AX's job and this gate ignores
#   AXIOM_TESTS regardless. This bundle additionally declares NO axioms and NO
#   deep-model references (mapping.md §1) — both operations are pure data-flow
#   over their declared inputs — so there is no axiom-soundness or containment
#   obligation here to probe in the first place.
# ADDED (6): four are clause coverage this carrier's richer descriptor requires.
#   The sibling's dict carries its three values in one int carrier with a
#   no-spurious-keys quantifier; here the spec instead has three separate
#   field-level clauses (C2/C3/C4) plus the whole-descriptor C1, and a rival can
#   attack each field independently — so fn1-drop-check isolates C4 and
#   fn1-target-type isolates C3, neither of which any ported rival attacks alone.
#   fn1-guarded-collation is the partial-domain rival this carrier makes
#   available: it conditions the collation adoption on `refCheck`, agreeing with
#   the frozen solution over the whole no-check sub-domain, so it is a strict
#   near-miss refuted only at a with-check point. fn2-ignore-unique attacks
#   `targetUnique`, the target-eligibility gate the nagini carrier does not model
#   at all (its FN-2 has four binders, this M2 has five), and it is the only
#   rival refuted at targetUnique=false. Two positives are added: pos-fn1-via-
#   helper is the honest no-echo control (the post-image is a transparent def
#   over the method's own inputs, so returning it directly is CORRECT — there is
#   no answer key to echo), and pos-fn2-disjunct-order is deliberately the
#   commuted-operand shape that breaks a frozen tactic script WITHOUT being
#   wrong, shipped as an expect=verify control so the battery cannot read tactic
#   breakage as spec strength.
# DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
#   SEMANTICS against any rival that manufactures it. Every frozen impl region
#   is LOOP-FREE (straight-line a single ``return`` over immutable values, no
#   loop and no recursion), so there is no control flow here to make diverge: a
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
#
# WITNESS COVERAGE. The 13 reject witnesses probe 13 DISTINCT input points —
# seven for M1 and six for M2, none shared between two rivals, so no rival's
# claimed sub-domain goes undemonstrated and every near-miss is refuted at the
# point that distinguishes it rather than at a point it shares with a coarser
# rival.
#
#   M1 (refType, refCheck, targetCollation)
#     fn1-drop-collation        ("varchar(10)", none,             some "utf8_bin")
#     fn1-empty-collation       ("char(8)",     none,             some "nocase")
#     fn1-guarded-collation     ("text",        some "len_chk",   some "C")
#     fn1-swap-check-collation  ("varchar(22)", some "chk_len",   some "utf8_bin")
#     fn1-drop-check            ("varchar(64)", some "gt_zero",   none)
#     fn1-target-type           ("varchar(10)", some "c",         none)
#     fn1-normalize-empty-collation ("varchar(22)", some "chk",   some "")
#   M2 (targetUnique, oldType, newType, oldCollation, newCollation)
#     fn2-type-only        (true,  "varchar(10)", "varchar(10)", none,           some "utf8_bin")
#     fn2-collation-only   (true,  "varchar(10)", "varchar(20)", some "nocase",  some "nocase")
#     fn2-both-required    (true,  "char(5)",     "varchar(20)", none,           none)
#     fn2-ignore-unique    (false, "varchar(30)", "varchar(20)", some "C",       none)
#     fn2-always           (true,  "varchar(10)", "varchar(10)", none,           none)
#     fn2-never            (true,  "text",        "varchar(20)", some "nocase",  some "utf8_bin")
#
#   Per binder, across the witness set: refType takes 5 distinct storage types;
#   refCheck takes none and 5 distinct present checks; targetCollation takes none
#   and 4 distinct present collations (incl. the empty name `some ""`), so both
#   the present- and absent-collation sub-domains are probed. targetUnique takes
#   both true and false; oldType takes 4 distinct values and newType 2 (the
#   equal-type and differing-type points need no more); the
#   (oldCollation, newCollation) pair covers
#   equal-and-absent, equal-and-present, absent-to-present, present-to-absent and
#   present-to-different-present. No binder of either predicate is held at a
#   single value.
#
#   Per clause: C1 is attacked by every M1 rival; C2 by fn1-drop-collation
#   (presence), fn1-empty-collation (value), fn1-guarded-collation (partial
#   domain over refCheck), fn1-normalize-empty-collation (partial domain over the
#   empty collation NAME) and fn1-swap-check-collation; C3 alone by
#   fn1-target-type; C4 alone by fn1-drop-check and jointly by
#   fn1-swap-check-collation. D1 is attacked by every M2 rival; D2 by
#   fn2-ignore-unique and fn2-always; D3 by fn2-type-only, fn2-both-required and
#   fn2-never. Every independent top-level clause of both postconditions is
#   attacked, and each obligation is both defended (2 verifying cases each) and
#   attacked (7 rivals for M1, 6 for M2).
#
#   Every case in this file was confirmed with real builds: the 6 expect=verify
#   cases each elaborate against the frozen spec, and each reject case was
#   checked three ways — the rival fails to verify, its witness ELABORATES
#   against the rival, and its witness FAILS against the frozen solution. No
#   witness binds a hypothesis, so none carries a joint-satisfiability obligation
#   (`consistency_probe` returns None for all 13, checked mechanically).
#
# INDEPENDENT AUDIT (re-derived, not inherited). Every claim above was re-run by
# an auditor who did not write the port:
#   * Statement integrity: the projected spec view of all 19 case modules is
#     byte-identical to the frozen file's. No case reformats a statement.
#   * Witness discrimination: all 13 rival builds exit 0 and all 13 gold builds
#     exit 1, and every gold-side failure is a KERNEL EVALUATION refutation
#     ("Tactic `decide` proved that the proposition …Tester <args> = false is
#     false") — the strongest signature class, not a missing identifier, type
#     error, unfolding failure or timeout.
#   * FORGERY test (B'), run on all 13 even though a plain evaluation does not
#     require it: flipping the claim to `= true` makes gold ACCEPT (exit 0) and
#     the rival REJECT (exit 1) — exactly inverting both exit codes. Gold's exit
#     therefore tracks the claim rather than the file, so no case is hollow.
#   * Admissibility liveness: negating each of the two in-region asserts makes
#     its case FAIL (exit 1) with an unsolved `adm_1` goal `⊢ False`. The asserts
#     are load-bearing, not decoration.
#   * SPEC-TOO-WEAK probe: 5 further wrong impls not in this battery (empty-name
#     normalisation on M1, collation back-filled into the check slot, a narrow
#     notch in M2's guard, none/empty collation normalisation on M2, and the
#     referencing column's own type reported as its collation — the direct nagini
#     uniq-fn1-wrong-collation shape) were each REJECTED by the frozen spec. The
#     first is now shipped above as fn1-normalize-empty-collation, since it was
#     the one live gap: it is wrong at exactly one input and no prior witness
#     bound targetCollation to `some ""`. No spec hole found.
#   * SPEC-TOO-STRONG probe: 3 further correct reshapes (M1 rebuilding the option
#     through a match, M2 as a nested decidable if-chain, M2 as a De Morgan
#     negated conjunction) were each PROVEN against the frozen spec. The De
#     Morgan shape needs `bne` in the simp set; with it, it closes. No soundness
#     hole found.
#   Two false prose tallies were found and corrected: oldType takes 4 distinct
#   values (not 5) and newType 2 (not 3). The claims were wrong; the coverage
#   they described is adequate and the corrected numbers are stated above.
AXIOM_TESTS = []
