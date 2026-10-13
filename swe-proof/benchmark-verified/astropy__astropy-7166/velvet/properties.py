"""properties.py — G-PBT falsification battery for astropy__astropy-7166 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the elided ``prove_correct`` tactic body, is
changed — both regions the consumer spec view elides, so ``markers.same_spec``
holds and the ``prove_correct resolveMemberDocstrings`` obligation survives with
a byte-identical statement) and swaps in a candidate implementation; it is
checked by the real verifier. ``expect:"verify"`` passes iff (in scope AND
verifies); ``expect:"reject"`` passes iff (in scope AND does NOT verify AND its
refutation ``witness`` discriminates: the witness must elaborate against the
rival and FAIL against the witness subject — here an explicit
``witness_reference``, since the frozen impl cannot decide anything (see WITNESS
MECHANICS below)).

DEFENDED SURFACE (one contracted method):

  resolveMemberDocstrings (members : List Member)
      return (out : List (Option (List Char)))
    ensures out = resolvedDocs members                    -- the WHOLE pin (C1)

The method walks a list of class members and reports, per member, the
documentation it resolves. A member takes the documentation resolved from its
base classes exactly when it is one of the two participating member kinds, is
publicly visible, and carries no documentation of its own; every other member
keeps its own documentation. The whole-list result is the pure front-recursive
fold ``resolvedDocs`` (``resolvedDocs (m :: ms) = finalDoc m :: resolvedDocs
ms``). ``resolvedDocs``, ``finalDoc`` and ``eligible`` are all TRANSPARENT
``def``s over the method's own input — there is NO opaque answer-key oracle in
the load-bearing clause, so pinning ``out = resolvedDocs members`` is grounded,
not an echo.

WHICH CLAUSE CONSTRAINS THE IMPL. There is exactly one ``ensures`` clause, C1
(``out = resolvedDocs members``), and it is the only impl-constraining clause: it
is a function of ``members`` and pins, at every list position, which
documentation each member resolves — the eligibility decision (the two-kind
disjunction, the visibility conjunct, the own-doc conjunct), the value it takes
when eligible vs not, and the traversal order/length. Every uniqueness rival
therefore targets C1, each at a DIFFERENT input binder of the per-member
predicate (``isCallable``, ``isProperty``, ``isPublic``, ``ownDoc``,
``inheritedDoc``) or the list structure.

ADVERSARIAL READ of the nagini classes on THIS carrier. The nagini sibling
contracts a SINGLE-member ``apply_inheritance(m) -> None`` over a heap object
``m`` whose ``doc`` field is mutated in place; five of its six fields are
read-only (fractional ``Acc(...,1/2)``). This velvet bundle models the WHOLE
per-member loop over a ``List Member`` and returns the resolved documentation as
a value; the eligibility booleans are the same four observations
(``isCallable``/``isProperty``/``isPublic``/``ownDoc.isNone``), and the resolved
base documentation is the input field ``inheritedDoc``.

  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling's mandatory
    ``frame-mut-inherited`` and ``frame-mut-public`` rivals WRITE a read-only
    (``Acc(...,1/2)``) field and are rejected for INSUFFICIENT PERMISSION. Lean
    and Velvet are referentially transparent: ``members`` is an immutable value,
    this bundle declares no ``mut`` parameter, and there is no heap, aliasing, or
    permission system to subvert. There is no read-only input to overwrite, so
    the class is vacuous. No substitute probe is fabricated.
  * DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging
    rival is REJECTED rather than admitted. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
    two lines have to move together, and they do here. Under the total scope a
    postcondition is claimed of ALL runs, not only of terminating ones, and the
    verifier emits a descent obligation ``measure b' < measure b`` for every
    loop in the impl (1 loop here, measure ``i``). A rival that loops without a
    measure is refused outright (``Decreasing annotations are required in total
    correctness semantics``), and a rival that supplies a CONSTANT measure to
    dodge that is refused on the measure's own goal (``case «decreasing_1:
    spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
    Divergence therefore does not discharge the ``ensures`` clauses vacuously.
    It is still not shipped as a G-PBT reject case, and the reason is the
    witness contract rather than a spec weakness. A reject case must carry a
    witness that ELABORATES against the rival, and the rival's module does not
    compile at all: the descent obligation fails at the ``method`` itself,
    ahead of any appended tester. Measured through the gate's own
    ``_check_witness``, even ``example : True := trivial`` comes back
    ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
    would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.
  * ELIGIBILITY / VALUE / TRAVERSAL — the whole reject surface, all against C1.
    The nagini partial-domain and value rivals port directly onto the per-member
    predicate; the list traversal is a velvet-only surface (nagini's single-
    member carrier has no list) and gets one ADDED rival.

WITNESS MECHANICS ON THIS BUNDLE. C1's post-image ``resolvedDocs`` is FULLY
TRANSPARENT over the input (no opaque axiom in the clause). Each rival is written
LOOP-FREE (a ``members.map``, or a ``match`` on the head), so its extracted
program ``resolveMemberDocstringsExec`` — the ``NonDetT``-run of the impl —
REDUCES fully under ``decide`` at a concrete input. Each witness states, at one
concrete input,

    (match resolveMemberDocstringsExec <input> with | DivM.res r => r | _ => [])
        ≠ resolvedDocs <input>

i.e. the rival's own output DIFFERS from the transparent post-image C1 demands —
a direct C1 violation the elaborator sees.

THE FROZEN IMPL CANNOT SERVE AS THE SECOND SUBJECT, and every reject case
therefore carries an explicit ``witness_reference``. Gold's body is the ``while``
loop, whose ``…Exec`` elaborates through machinery the kernel cannot unfold, so
``decide`` against gold does not DECIDE anything: it fails with

    `decide` failed ... its `Decidable` instance `instDecidableNot` did not
    reduce to `isTrue` or `isFalse` ... reduction got stuck at ... `.hasDecEq`

Measured on all six witnesses (``scripts/lean_verify.sh``, exit 1 each). That is
a STUCK REDUCTION, not a refutation: the same error appears for a TRUE claim
about gold, so gold's exit code carries no information and would attest to a
refutation never performed (the gate screens exactly this signature and calls it
``witness-undecided``). An earlier revision of this file mistook that stuck
failure for the required discrimination; it is not, and the claim is retracted
here.

So each reject case names ``witness_reference = _REFERENCE`` — the loop-free
``return (resolvedDocs members)`` impl, which shares the frozen spec byte-for-byte
and VERIFIES (it is also shipped as the ``pos-direct-fold`` positive, checked
independently). Being loop-free, its ``…Exec`` reduces, so ``decide`` reaches a
real verdict there. Refuting the witness against a VERIFYING impl of the same
spec is sound for the reason gold was: an impl the verifier accepts cannot
violate its own spec, so a genuine "the spec is violated at this input" claim
must fail against it.

Measured, per reject case, with ``scripts/lean_verify.sh``: the witness
ELABORATES against its rival (exit 0), and against the reference it FAILS with
``decide`` **proving the proposition false** (exit 1) — a semantic refutation of
the concrete claim, not a stuck reduction, not a missing identifier, not a type
error. Every input is a concrete ``Member`` literal with tiny ``List Char``
documentation values that ``decide`` reduces, so no witness binds a hypothesis
and none can be inconsistent; no consistency probe is needed. No banned token
(sorry/admit/native_decide/axiom/opaque).

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries none either
(``meta.axioms == []``); the ``isProperty``/``eligible`` deep model is an
A-reference validated by G-AX / axiom_check.py, not a consumed axiom, and the
G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "astropy__astropy-7166"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body (backward `while` fold),
# ---- everything strictly BETWEEN the method's `-- impl-start` / `-- impl-end`.
# ---- Every variant replaces exactly this text, so each edit lies wholly inside
# ---- the one -- impl-start .. -- impl-end region and same_spec holds by
# ---- construction (both facts asserted at load by _swap).
_IMPL = (
    "    let mut result : List (Option (List Char)) := []\n"
    "    let mut i := members.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ members.length\n"
    "      invariant result = resolvedDocs (members.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let m := members[i - 1]!\n"
    "      result := finalDoc m :: result\n"
    "      i := i - 1\n"
    "    return result"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# The frozen proof, verbatim. A loop-free reshape may retune THIS block (elided
# from the spec view); loop-keeping variants leave it as-is. Rivals leave it
# as-is too — the rejection is carried by the witness, not the tactic script.
_PROOF = (
    "prove_correct resolveMemberDocstrings by\n"
    "  loom_solve\n"
    "  rw [resolvedDocs_drop_step members i (by omega) (by omega)]\n"
    "  simp_all"
)

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_reproved(new_body, new_proof):
    """Impl body replaced AND the proof retuned (for reshapes whose residual
    goal no longer matches the frozen backward-fold tactic script)."""
    return _swap(_impl(new_body), _PROOF, new_proof)


# ---- A loop-free rival: resolve each member with a custom per-member map. Being
# ---- loop-free (`members.map`), its extracted `…Exec` reduces under `decide`, so
# ---- the witness reaches a real verdict against it.
def _map(mapexpr):
    return _impl(f"    return (members.map (fun m => {mapexpr}))")


# ---- THE WITNESS SUBJECT for every reject case (`witness_reference`).
# ---- The frozen impl's `while`-loop `…Exec` does not reduce, so `decide` against
# ---- gold is STUCK for every claim, true or false, and its exit code
# ---- discriminates nothing (the gate calls that `witness-undecided`). This
# ---- loop-free impl of the SAME frozen spec does reduce, and it VERIFIES — the
# ---- gate re-checks both properties before using it, and it is shipped
# ---- independently as the `pos-direct-fold` positive. Refuting a witness against
# ---- a VERIFYING impl is sound for the reason gold would have been: an impl the
# ---- verifier accepts cannot violate its own spec.
_REFERENCE = _impl_reproved(
    "    return (resolvedDocs members)",
    "prove_correct resolveMemberDocstrings by\n  loom_solve")


# ---- witness preamble + builder. C1's post-image `resolvedDocs` is TRANSPARENT
# ---- (no opaque axiom in the clause), so the executable program is extracted
# ---- and C1 refuted directly at a concrete input. Checked in a file whose
# ---- `prove_correct` block is stripped, so no tactic script can mask the
# ---- verdict.
_EXTRACT = "extract_program_for resolveMemberDocstrings\n\n"


def _witness(inp):
    return (
        _EXTRACT +
        "example :\n"
        f"    (match resolveMemberDocstringsExec ({inp}) with | DivM.res r => r | _ => [])"
        f" ≠ resolvedDocs ({inp}) := by\n"
        "  decide\n"
    )


# ---- Documentation-value helpers for `Option (List Char)` literals (avoid
# ---- backslashes inside f-strings). `NONE` is absent documentation; `DOC(c)`
# ---- is a present one-character documentation string.
NONE = "none"


def DOC(ch):
    return "some [" + repr(ch) + "]"


# ---- Member literal helper (keep witnesses readable). `ownDoc`/`inheritedDoc`
# ---- are `Option (List Char)`; pass `NONE` or e.g. `DOC('B')`.
def _M(is_callable, is_property, is_public, own_doc, inherited_doc):
    return (f"{{ isCallable := {is_callable}, isProperty := {is_property}, "
            f"isPublic := {is_public}, ownDoc := {own_doc}, "
            f"inheritedDoc := {inherited_doc} }}")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-direct-fold",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: report the whole-list result DIRECTLY via the transparent
        # fold, no per-member loop. C1 is literally `out = resolvedDocs members`,
        # so this is the cheapest HONEST correct impl — and, since `resolvedDocs
        # members` is GROUNDED in the argument (not an opaque answer key), it
        # doubles as proof the spec is not echo-vulnerable (any WRONG per-member
        # resolution fails `out = resolvedDocs members`). The loop is gone, so the
        # frozen proof's backward-fold step is unneeded and the residual goal
        # closes under `loom_solve` alone.
        "module": _REFERENCE,  # identical text to the witness subject

        "rationale": (
            "the post-image `resolvedDocs members` is GROUNDED in the input (a "
            "total front-recursive fold, no opaque answer key), so `return "
            "resolvedDocs members` is the honest cheapest CORRECT impl; C1 is "
            "literally `out = resolvedDocs members`, so it MUST verify, else C1 is "
            "SPEC-TOO-STRONG. Re-expresses the nagini pos-reorder-local (a "
            "structurally-different correct decision) on the whole-list carrier: "
            "the cheapest impl satisfying the grounded pin, showing the spec is "
            "not echo-vulnerable."
        ),
    },
    {
        "id": "pos-inline-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the backward `while` fold, but INLINE the per-member
        # resolution (the unfolded body of finalDoc/eligible) with the two-kind
        # disjunction operands REORDERED (isProperty first) instead of calling
        # `finalDoc`. Same value flow, different syntactic form; the frozen proof
        # is retuned by handing `finalDoc`/`eligible` to the closing `simp_all`
        # (the loop invariant and step lemma are unchanged).
        "module": _impl_reproved(
            "    let mut result : List (Option (List Char)) := []\n"
            "    let mut i := members.length\n"
            "    while i > 0\n"
            "      invariant 0 ≤ i ∧ i ≤ members.length\n"
            "      invariant result = resolvedDocs (members.drop i)\n"
            "      done_with i = 0\n"
            "      decreasing i\n"
            "    do\n"
            "      let m := members[i - 1]!\n"
            "      let d : Option (List Char) := "
            "if ((m.isProperty || m.isCallable) && m.isPublic && m.ownDoc.isNone) "
            "then m.inheritedDoc else m.ownDoc\n"
            "      result := d :: result\n"
            "      i := i - 1\n"
            "    return result",
            "prove_correct resolveMemberDocstrings by\n"
            "  loom_solve\n"
            "  rw [resolvedDocs_drop_step members i (by omega) (by omega)]\n"
            "  simp_all [finalDoc, eligible, Bool.or_comm]"),
        "rationale": (
            "a correct impl with a DIFFERENT syntactic shape (inline the "
            "finalDoc/eligible resolution — the reordered two-kind disjunction, "
            "the visibility conjunct, the own-doc conjunct — instead of calling "
            "`finalDoc`) must verify; the value flow is unchanged so C1 still "
            "discharges once the closing step unfolds `finalDoc`/`eligible`. Ports "
            "the nagini pos-reorder-local / pos-guard-clause reshapes (reorder "
            "operands + inline the eligibility decision). If it fails => "
            "SPEC-TOO-STRONG (over-fit to the `finalDoc`-call form)."
        ),
    },
    {
        "id": "pos-map-finalDoc",
        "kind": "soundness",
        "expect": "verify",
        # ADDED BY AUDIT (attack E). A THIRD correct shape, structurally between
        # the other two positives: the loop is gone (like pos-direct-fold) but the
        # result is built by mapping the per-member resolver over the list rather
        # than naming the whole-list fold, so C1 is discharged by INDUCTION on the
        # list rather than by `rfl` against `resolvedDocs`. That makes it the only
        # positive whose proof reasons about the traversal, so it is the positive
        # that would break if C1 were over-fit to the fold's own syntactic form.
        "module": _impl_reproved(
            "    return (members.map finalDoc)",
            "prove_correct resolveMemberDocstrings by\n"
            "  loom_solve\n"
            "  all_goals induction members with\n"
            "  | nil => rfl\n"
            "  | cons hd tl ih => simp [resolvedDocs_cons, ih]"),
        "rationale": (
            "a correct impl that computes the result as `members.map finalDoc` "
            "instead of naming `resolvedDocs members` must verify: the two are "
            "extensionally equal but NOT definitionally so, and the equality needs "
            "an induction on the list, so this positive exercises C1 against the "
            "TRAVERSAL rather than against the fold's syntactic form. Added by the "
            "audit (attack E, SPEC-TOO-STRONG probe): measured to verify with "
            "scripts/lean_verify.sh (exit 0). If it failed => SPEC-TOO-STRONG "
            "(C1 admits only impls shaped like the frozen fold)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from nagini admiss-property-self-call. That case
    # established the read-only fractional-permission precondition on an
    # F2P-shaped Member (a public undocumented property). This method carries NO
    # `require` clause (the pre-conditions region is empty), so nothing could
    # exclude a normal input and the classic "a normal input is admitted" probe is
    # vacuous. Re-aimed at the residual admissibility risk on a total domain: that
    # the post-image is jointly SATISFIABLE by a gold-shaped computation. The
    # frozen impl discharging the ensures IS that witness. MUST verify, else
    # SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # frozen impl; same_spec trivially, must verify
        "rationale": (
            "the input carries no `require`, so the resolver is total over every "
            "member list; the gold impl discharging `out = resolvedDocs members` "
            "is the admissibility witness that the post-image is satisfiable. "
            "Near-trivial precisely because the precondition is empty. Re-aimed "
            "from the nagini admiss-property-self-call, whose read-only fractional-"
            "permission half (Acc 1/2 on the five read-only fields, full Acc only "
            "on doc) has no counterpart on this referentially-transparent, "
            "unconditioned carrier. Else SPEC-UNSATISFIABLE."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the F2P. All attack C1 (`out = resolvedDocs
    # members`); the per-member binders (isCallable, isProperty, isPublic, ownDoc,
    # inheritedDoc) and the list structure are varied across the witnesses.
    # =====================================================================
    {
        "id": "rival-drop-descriptor",
        "kind": "uniqueness",
        "expect": "reject",
        # THE F2P-DISCRIMINATING BUG. Drop the SECOND member-kind disjunct from the
        # eligibility decision, so only the plain-function kind qualifies — the
        # exact pre-change guard. On a public undocumented member of the OTHER kind
        # (isCallable=false, isProperty=true) eligibility flips false, so the
        # member keeps its own (absent) documentation instead of inheriting.
        "module": _map(
            "if (m.isCallable && m.isPublic && m.ownDoc.isNone) "
            "then m.inheritedDoc else m.ownDoc"),
        "refinement": (
            "drops the second member-kind disjunct — the exact pre-change guard, "
            "which recognised only the plain-function kind. Its faithful real "
            "patch is the pre-change membership test, under which a public "
            "undocumented member of the OTHER participating kind is NOT recognised "
            "(the added kind-test is absent), so its documentation is never filled "
            "from the base; the F2P assertion that such a member inherits the "
            "base's documentation FAILS -> does not resolve. This is exactly the "
            "defect the fix corrects."
        ),
        "rationale": (
            "THE F2P-discriminating bug. REJECT from C1 (`out = resolvedDocs "
            "members`): `resolvedDocs` routes a member through `finalDoc`, which "
            "for an eligible member (either participating kind, public, no own "
            "doc) yields `inheritedDoc`; a rival recognising only the first kind "
            "diverges on a member of the second kind. Refuted at a public "
            "undocumented second-kind member with a non-empty inherited doc. Ports "
            "nagini rival-drop-descriptor. If it verified => SPEC-TOO-WEAK (admits "
            "the original bug)."
        ),
        "witness": _witness(f"[{_M('false', 'true', 'true', NONE, DOC('B'))}]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "rival-fill-always",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the WHOLE eligibility decision: unconditionally take the inherited
        # documentation for every member, including ineligible ones. Wrong on any
        # member the spec says keeps its own documentation (ineligible) whose own
        # doc differs from the inherited doc.
        "module": _map("m.inheritedDoc"),
        "refinement": (
            "drops the whole eligibility guard and fills every member from the "
            "base's documentation — including non-public members and members that "
            "already define their own documentation. A faithful real patch of this "
            "shape would overwrite documented and private members' documentation "
            "with the base's, breaking the own-documentation expectation the F2P "
            "and PASS_TO_PASS suites encode; plainly not the gold hunk -> does not "
            "resolve."
        ),
        "rationale": (
            "REJECT from C1 (`out = resolvedDocs members`): `finalDoc` keeps "
            "`ownDoc` on an INELIGIBLE member, so a rival always returning "
            "`inheritedDoc` diverges whenever an ineligible member's own doc "
            "differs from its inherited doc. Refuted at a non-public member "
            "(isPublic=false, otherwise ineligible) whose own doc differs from the "
            "inherited doc. Ports nagini rival-fill-always. If it verified => "
            "SPEC-TOO-WEAK (the eligibility decision is unpinned)."
        ),
        "witness": _witness(f"[{_M('true', 'false', 'false', DOC('A'), DOC('B'))}]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "rival-drop-public",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: drop the visibility conjunct. Correct on every public
        # member; diverges ONLY on the non-public sub-domain, filling a non-public
        # member's documentation the spec says must be left as its own.
        "module": _map(
            "if ((m.isCallable || m.isProperty) && m.ownDoc.isNone) "
            "then m.inheritedDoc else m.ownDoc"),
        "refinement": (
            "PARTIAL-DOMAIN: drops the visibility conjunct. Correct on every "
            "public member; diverges only on the NON-PUBLIC sub-domain, filling a "
            "non-public member's documentation. Its faithful real patch removes "
            "the visibility test from the guard, so leading-underscore (private) "
            "members get base documentation copied in — a behavioural regression "
            "vs the gold guard; not the gold hunk -> does not resolve faithfully."
        ),
        "rationale": (
            "PARTIAL-DOMAIN on the non-public sub-domain. REJECT from C1 (`out = "
            "resolvedDocs members`): `eligible` requires `isPublic`, so a rival "
            "dropping it diverges on a non-public otherwise-eligible member. "
            "Refuted at a non-public (isPublic=false) member that is otherwise "
            "eligible (a participating kind, no own doc) — a distinct binder "
            "(isPublic) exercised at false. Ports nagini rival-drop-public. If it "
            "verified => SPEC-TOO-WEAK (domain-incomplete)."
        ),
        "witness": _witness(f"[{_M('true', 'false', 'false', NONE, DOC('B'))}]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "rival-drop-owndoc",
        "kind": "uniqueness",
        "expect": "reject",
        # PARTIAL-DOMAIN: drop the own-documentation conjunct. Correct on every
        # member lacking its own documentation; diverges ONLY on the
        # already-documented sub-domain, OVERWRITING documentation a member already
        # defines with the base's.
        "module": _map(
            "if ((m.isCallable || m.isProperty) && m.isPublic) "
            "then m.inheritedDoc else m.ownDoc"),
        "refinement": (
            "PARTIAL-DOMAIN: drops the own-documentation conjunct. Correct on "
            "every member lacking its own documentation; diverges only on the "
            "already-documented sub-domain, OVERWRITING documentation a member "
            "already defines. Its faithful real patch removes the own-doc test "
            "from the guard, clobbering members' own documentation with the "
            "base's — the exact behaviour that test exists to prevent; not the "
            "gold hunk -> does not resolve faithfully."
        ),
        "rationale": (
            "PARTIAL-DOMAIN on the already-documented sub-domain. REJECT from C1 "
            "(`out = resolvedDocs members`): `eligible` requires `ownDoc.isNone`, "
            "so a rival dropping it diverges on a member that has its own doc but "
            "is otherwise eligible. Refuted at a public participating-kind member "
            "WITH its own documentation (ownDoc = some ..) differing from the "
            "inherited doc — exercises the ownDoc binder at `some`. Ports nagini "
            "rival-drop-owndoc. If it verified => SPEC-TOO-WEAK (domain-incomplete)."
        ),
        "witness": _witness(f"[{_M('true', 'false', 'true', DOC('A'), DOC('B'))}]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "rival-fill-wrong-value",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE divergence: the eligibility decision is GOLD, but when eligible the
        # rival assigns `none` ("no documentation") instead of the resolved
        # inherited documentation. Wrong on any eligible member whose resolved base
        # documentation is present.
        "module": _map(
            "if ((m.isCallable || m.isProperty) && m.isPublic && m.ownDoc.isNone) "
            "then (none : Option (List Char)) else m.ownDoc"),
        "refinement": (
            "the eligibility decision is GOLD, but when eligible the rival records "
            "NO documentation instead of the resolved base documentation. Its "
            "faithful real patch sets the member's documentation to `None` rather "
            "than the base member's documentation, so the inherited documentation "
            "is never copied and the F2P assertion that the member inherits the "
            "base's documentation FAILS (it would be None) -> does not resolve."
        ),
        "rationale": (
            "VALUE divergence on the assigned documentation. REJECT from C1 (`out "
            "= resolvedDocs members`): `finalDoc` assigns `inheritedDoc` on an "
            "eligible member, so a rival assigning `none` diverges whenever the "
            "resolved base documentation is present. Refuted at an eligible member "
            "(public, no own doc, a participating kind) whose inherited doc is "
            "`some ..` — exercises the inheritedDoc binder as the assigned value. "
            "Ports nagini rival-fill-wrong-value. If it verified => SPEC-TOO-WEAK "
            "(assigns wrong value)."
        ),
        "witness": _witness(f"[{_M('true', 'false', 'true', NONE, DOC('B'))}]"),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "rival-head-only",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED (velvet-only surface — nagini's single-Member carrier has no list).
        # Attack the LIST TRAVERSAL: resolve only the FIRST member, dropping the
        # rest of the list. Correct on any input of length <= 1 (and the empty
        # list); wrong on any list of length >= 2. Varies the list-length binder,
        # which every other witness holds at length 1.
        "module": _impl(
            "    match members with\n"
            "    | [] => return []\n"
            "    | m :: _ => return [finalDoc m]"),
        "refinement": (
            "resolves only the first member of the class body and discards every "
            "subsequent member. A faithful real patch that filled only the first "
            "member's documentation would leave the remaining members' "
            "documentation unresolved; essentially every multi-member class test "
            "(the bulk of the PASS_TO_PASS suite) would then FAIL -> does not "
            "resolve. No nagini counterpart: nagini contracts a single member, so "
            "the traversal is a velvet-only surface."
        ),
        "rationale": (
            "REJECT from C1 (`out = resolvedDocs members`): `resolvedDocs` maps "
            "EVERY member, so `out` must have the input's length; a rival "
            "returning a one-element list diverges on any input of length >= 2. "
            "Refuted at a TWO-member list — the only witness that varies the "
            "list-length binder (every other witness is length 1), so the "
            "traversal is defended, not just the per-member resolution. ADDED "
            "(no nagini sibling — single-member carrier). If it verified => "
            "SPEC-TOO-WEAK (the traversal/length is unpinned)."
        ),
        "witness": _witness(
            f"[{_M('true', 'false', 'true', NONE, DOC('A'))}, "
            f"{_M('true', 'false', 'true', NONE, DOC('B'))}]"),
        "witness_reference": _REFERENCE,
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
#   nagini case                  -> here
#   -----------------------------------------------------------------------
#   pos-reorder-local            -> pos-direct-fold + pos-inline-reorder   PORTED
#   pos-guard-clause             -> pos-inline-reorder                     PORTED
#   admiss-property-self-call    -> admiss-gold-total                      RE-AIMED
#   rival-drop-descriptor        -> rival-drop-descriptor                  PORTED
#   rival-fill-always            -> rival-fill-always                      PORTED
#   rival-drop-public            -> rival-drop-public                      PORTED
#   rival-drop-owndoc            -> rival-drop-owndoc                      PORTED
#   rival-fill-wrong-value       -> rival-fill-wrong-value                 PORTED
#   (no nagini sibling)          -> rival-head-only                        ADDED
#   (no nagini sibling)          -> pos-map-finalDoc                 ADDED (AUDIT)
#   frame-mut-inherited          -> (none)                                 VACUOUS
#   frame-mut-public             -> (none)                                 VACUOUS
#   (divergence — no nagini case)-> (none)                     SPEC-CLOSED
#   AXIOM_TESTS ([])             -> (none)                                 N/A
#
# AUDIT AMENDMENTS (independent adversarial re-derivation of this battery):
#   1. WITNESS SUBJECT CORRECTED. This file previously claimed the witnesses
#      discriminate because they FAIL against the frozen solution. Rebuilt all six
#      by hand: gold's exit code is indeed 1, but the error is
#      "`instDecidableNot` did not reduce to `isTrue` or `isFalse` ... stuck at
#      `.hasDecEq`" — a STUCK REDUCTION that appears for a true claim too, so it
#      discriminates nothing. Every reject case now carries an explicit
#      `witness_reference` (the loop-free verifying impl), against which each
#      witness fails with "`decide` proved that the proposition is false" — a real
#      semantic refutation. The false claim is retracted above.
#   2. RIVALS RE-CONFIRMED WRONG (attack C). Each witness was rebuilt against its
#      rival (exit 0, elaborates) and against the verifying reference (exit 1, by
#      semantic refutation), so all six rivals are OBSERVABLY wrong on this
#      carrier, not merely reshaped.
#   3. SPEC-TOO-WEAK probe (attack D) — 5 NEW wrong impls the battery did not
#      contain, all REJECTED (exit 1): both kinds ANDed instead of ORed; the
#      eligible/ineligible branches swapped; the list reversed; the first-kind
#      disjunct dropped (mirror of rival-drop-descriptor); the own-doc conjunct
#      inverted to `isSome`. No spec hole found.
#   4. SPEC-TOO-STRONG probe (attack E) — 2 NEW correct reshapes both VERIFY
#      (exit 0): `members.map finalDoc` (now shipped as pos-map-finalDoc) and an
#      `Option.orElse` reshape of the eligible branch. The spec is not over-fit.
#
# 10 velvet SPEC cases: 3 soundness + 1 admissibility + 6 uniqueness. The nagini
# file has 9 SPEC cases; the two frame-mutation rivals are vacuous here, one
# traversal rival is added, and the audit added a third positive — so the counts
# do not line up, and are not made to.
#
# PORTED (5 uniqueness + 2 positives): the eligibility/value rivals carry across
#   with only a carrier change (nagini single heap `Member` with a mutated `doc`
#   field -> velvet `List Member`, resolved documentation returned as a value).
#   rival-drop-descriptor is the F2P bug (recognise only the first member kind);
#   the two drop rivals and the fill/wrong-value rivals attack the visibility
#   conjunct, the own-doc conjunct, the whole decision, and the assigned value.
#   The positives split the nagini reorder+guard reshapes into a direct grounded-
#   fold return and an inline reordered-disjunction loop, each backed by a proof
#   that closes for the new shape.
# RE-AIMED (admiss-property-self-call -> admiss-gold-total): the nagini case
#   established the read-only fractional-permission precondition on an F2P-shaped
#   member. This method has no `require` and no heap permission, so that probe is
#   vacuous; re-aimed at the residual total-domain risk (post-image joint
#   satisfiability), witnessed by the frozen impl discharging the ensures.
# ADDED (rival-head-only): attacks the list TRAVERSAL, refuted at a length-2
#   list. The nagini single-member model has no list to traverse, so this C1
#   binder (the traversal/length) has no nagini rival; here it is a concrete
#   witnessable C1 divergence. A real divergence with a checked witness, not
#   fabricated wrongness.
# VACUOUS — frame-mut-inherited, frame-mut-public: Velvet is referentially
#   transparent, `members` is immutable, no `mut` binder, no heap/aliasing/
#   permission system. No read-only input to overwrite. No substitute fabricated.
# DIVERGENCE - the class is CLOSED BY THE SEMANTICS here, and a diverging rival
#   is REJECTED rather than admitted. This bundle sets
#   ``loom.semantics.termination "total"`` AND carries
#   ``open TotalCorrectness``, and the ``open`` is the line that actually
#   selects the semantics: both namespaces define
#   ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
#   ``PartialCorrectness`` version takes a loop measure and DISCARDS it. So the
#   two lines have to move together, and they do here. Under the total scope a
#   postcondition is claimed of ALL runs, not only of terminating ones, and the
#   verifier emits a descent obligation ``measure b' < measure b`` for every
#   loop in the impl (1 loop here, measure ``i``). A rival that loops without a
#   measure is refused outright (``Decreasing annotations are required in total
#   correctness semantics``), and a rival that supplies a CONSTANT measure to
#   dodge that is refused on the measure's own goal (``case «decreasing_1:
#   spin» ... ⊢ spin < spin``), re-measured on this bundle with a real build.
#   Divergence therefore does not discharge the ``ensures`` clauses vacuously.
#   It is still not shipped as a G-PBT reject case, and the reason is the
#   witness contract rather than a spec weakness. A reject case must carry a
#   witness that ELABORATES against the rival, and the rival's module does not
#   compile at all: the descent obligation fails at the ``method`` itself,
#   ahead of any appended tester. Measured through the gate's own
#   ``_check_witness``, even ``example : True := trivial`` comes back
#   ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome and
#   would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
# AXIOM_TESTS: the nagini file ships none (meta.axioms == []); the
#   isProperty/eligible deep model is an A-reference (G-AX / axiom_check.py),
#   not a consumed axiom, and G-PBT ignores AXIOM_TESTS anyway.
#
# CLAUSE / BINDER / POINT COVERAGE. The sole impl-constraining clause C1
#   (`out = resolvedDocs members`) is DEFENDED by both positives and the
#   admissibility case (all discharge on gold) and ATTACKED by six rivals across
#   its input binders:
#     * the two-kind disjunction (isCallable/isProperty) — rival-drop-descriptor
#       (isCallable=false, isProperty=true);
#     * the visibility conjunct (isPublic) — rival-drop-public (isPublic=false)
#       and rival-fill-always (isPublic=false);
#     * the own-doc conjunct (ownDoc.isNone) — rival-drop-owndoc (ownDoc=some);
#     * the assigned value (inheritedDoc vs none) — rival-fill-wrong-value;
#     * list length / traversal — rival-head-only (the only length-2 witness).
#   The six reject witnesses probe SIX distinct input points (pts=6): isCallable
#   takes both values, isProperty both, isPublic both, ownDoc both none/some,
#   inheritedDoc is present in all discriminating positions, and list length
#   takes 1 and 2. No binder is held fixed by every witness.
#
# WITNESS MECHANICS: C1's post-image `resolvedDocs` is TRANSPARENT (no opaque
#   axiom in the clause), so `decide` reduces the extracted program directly.
#   Every rival is loop-free so its `…Exec` reduces under `decide`.
#
#   GOLD IS NOT THE WITNESS SUBJECT. The frozen `while`-loop's `…Exec` does not
#   reduce, so `decide` against gold is STUCK for every claim regardless of truth
#   ("`instDecidableNot` did not reduce to `isTrue` or `isFalse` ... stuck at
#   `.hasDecEq`"). A failure the kernel never evaluated attests to nothing, so
#   every reject case carries `witness_reference = _REFERENCE`: the loop-free
#   `return (resolvedDocs members)` impl, which shares the frozen spec and
#   VERIFIES (the gate re-checks both before using it).
#
#   Measured per reject case with scripts/lean_verify.sh:
#     rival module build                exit 1  (the rival is rejected)
#     witness vs rival                  exit 0  (elaborates)
#     witness vs _REFERENCE             exit 1  ("`decide` proved that the
#                                                proposition is false" — a
#                                                SEMANTIC refutation, not a
#                                                stuck reduction)
#     witness vs gold (recorded only)   exit 1  by STUCK REDUCTION — which is why
#                                                gold cannot be the subject
#   No witness binds a hypothesis, so none can be inconsistent and no
#   consistency probe is needed.
AXIOM_TESTS = []
