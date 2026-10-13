"""properties.py — G-PBT falsification battery for sphinx-doc__sphinx-8035 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region — which the consumer spec view elides — plus, where a
reshape needs it, the ``prove_correct`` tactic body, so ``markers.same_spec``
holds and the single ``prove_correct selectMembers`` obligation survives) and
swaps in a candidate implementation; it is checked by the real verifier.
``expect:"verify"`` passes iff (in scope AND verifies); ``expect:"reject"``
passes iff (in scope AND does NOT verify AND its refutation ``witness``
discriminates: the witness must ELABORATE against the rival and FAIL against the
refutation subject).

DEFENDED SURFACE. One contracted method,
``selectMembers (members : List Member) (sel : Sel) (showUndocumented : Bool)
return (out : List Member)``, which filters a collection down to the members
that should be surfaced, in input order. There is NO ``require`` clause: the
domain is total over every input triple. The postcondition is a SINGLE master
equality:

  (M) out = shownMembers sel showUndocumented members

where ``shownMembers`` is a fully-unfolded, front-recursive ``def`` over the
per-member keep-decision ``memberShown``:

  * a NON-restricted member is surfaced iff it is documented, or undocumented
    members are requested (``m.hasDoc || showUndocumented``);
  * a RESTRICTED member is surfaced iff it clears that same gate AND the
    tri-state selection ``sel`` surfaces its identifier — where ``selKeeps``
    gives ``false`` for the empty selection ``.none``, ``true`` for the blanket
    selection ``.all``, and ``names.contains name`` for a specific selection
    ``.only names``.

So (M) pins the observable exactly, and the load-bearing content — the whole
point of the modeled behaviour — is that a SPECIFIC selection distinguishes the
named restricted members rather than acting as a single all-or-nothing switch: a
verifying implementation cannot treat ``.only names`` as "surface every
restricted member". The equality also pins the tri-state at ``.none`` (surface
none), the gate on BOTH branches, the branch DISPATCH between them, and the
input ORDER of the result.

CARRIER NOTE — why every reject case names a ``witness_reference``, and why the
frozen solution CANNOT be the refutation subject here.

The whole spec is COMPUTABLE (``shownMembers`` / ``memberShown`` / ``selKeeps``
are concrete ``def``s over ``DecidableEq`` carriers), so a refutation runs
through Velvet's executable tester: ``selectMembersTester members sel su = false``
says the extracted program's result violates the postcondition at that concrete
input. But the FROZEN implementation is a backward ``while`` loop, and under
``loom.semantics.choice "demonic"`` its extracted program elaborates through
``Classical.choice``, which the kernel cannot unfold. ``decide`` against the
frozen impl is therefore STUCK for EVERY claim, true or false, so its exit code
carries NO information and cannot witness a refutation.

This was MEASURED here, not assumed — three builds against the frozen solution:

  * the real refutation             -> rc=1, ``did not reduce to `isTrue` or `isFalse` ``
  * a TRUE claim (``... = true`` at an agreement point) -> rc=1, the SAME stuck error
  * a straight-line reference impl  -> rc=0 on the true claim, rc=1 on the false one

Because a TRUE claim about gold fails exactly like a false one, "the witness
failed on gold" would attest to a refutation that was never performed, and a
FORGED witness asserting the rival is CORRECT would clear both halves. So gold
is not a usable second subject, and every reject case below names
``witness_reference = _LOOPFREE`` instead: a loop-free implementation of the same
frozen spec that REDUCES, and that the gate independently checks shares the
frozen spec and VERIFIES before refuting any witness against it. Verified
directly: the forgery ("the rival is correct here") is REFUTED against
``_LOOPFREE`` (rc=1, not stuck), and a true claim is confirmed (rc=0) — the
discrimination the frozen side cannot give. ``_LOOPFREE`` also ships as the
``pos-loopfree`` positive, so the battery itself records that loop-freeness is
not what any rival is being rejected for. No banned token (``sorry`` / ``admit``
/ ``native_decide`` / new ``axiom`` / ``opaque``).

ADVERSARIAL READ of the nagini classes (the sibling battery contracts TWO
functions — a per-member keep-decision [site A] and a selector-list merge
[site B] — over Nagini's fractional-permission carrier):

  * SITE B (the selector-list merge) — NOT MODELED here. This bundle models only
    the per-member keep-filter (mapping.md §1–2); the list-merge behaviour is a
    separate function with no counterpart in this carrier. Every site-B nagini
    case (its positive control, its frame-mutation reject, its drop-extra and
    no-op-dropped rejects) is legitimately omitted as carrier narrowing — see the
    ACCOUNTING footer.
  * FRAME-MUTATION (site A, ``write-names``) — VACUOUS. The nagini sibling
    MANDATES it because the name list is held at half permission (read-only) and
    an impl that WRITES to it must be rejected for insufficient permission.
    Lean/Velvet is referentially transparent: ``members`` / ``sel`` /
    ``showUndocumented`` are immutable values, no ``mut`` binder, no heap and no
    aliasing, so there is no read-only input to overwrite and no substitute probe
    to build. Not fabricated. (Footer.)
  * ASYMMETRY / inherited-member filter (site A, ``mode2-ignores-inherited``) —
    NOT ON THIS CARRIER. The inherited-member filter is constantly inactive in
    the modeled scenario (mapping.md §2: the modeled collection is a module, so
    the inherited-member test is identically ``false``), so it is not a field of
    ``Member`` and not a term in (M). A rival attacking it would have no
    counterpart clause to violate — DROPPED, not fabricated. (Footer.)
  * PARTIAL-DOMAIN / VALUE (site A, the boolean collapse) — APPLIES, and is the
    core of the battery. The pre-fix behaviour collapses the tri-state selection
    to a truthy flag (surface every documentable restricted member); that IS the
    ``collapse`` rival. This carrier makes the tri-state EXPLICIT, so the single
    master equality is additionally attacked at each ``Sel`` state
    (``.only``-as-blanket, ``.none``-as-blanket, ``.all``-as-drop), at the
    documentable gate on the restricted branch, at the branch DISPATCH, and at
    the result ORDER — each a distinct sub-domain of (M).
  * DIVERGENCE / non-termination - the class is CLOSED BY THE SEMANTICS here,
    and a diverging rival is REJECTED rather than admitted. This bundle sets
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
  * UNGROUNDED-ORACLE ECHO — N/A. ``shownMembers`` is a concrete ``def`` fully
    unfolded in the ``pure`` region and grounded entirely in the input triple;
    (M) equates the result to that fold, so there is no opaque answer-key to echo
    (materialising the filtered list IS the work).

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries two
axiom-soundness probes over the real upstream callees; that is G-AX's job
(axiom_check.py / mapping.md) and the G-PBT gate ignores ``AXIOM_TESTS``
regardless.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-8035"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- Anchors. All three lie wholly inside the regions a variant may edit (the
# ---- single method's `-- impl-start` / `-- impl-end` region, plus the
# ---- `prove_correct` tactic body) and each is unique in the file (asserted at
# ---- load, so the manifest breaks loudly if the frozen solution ever changes).
# ---- `_IMPL` is the WHOLE frozen loop body — every uniqueness rival replaces
# ---- exactly this text with a loop-free expression. `_STEP` is the two-line
# ---- loop-body core, edited by the in-loop positive control. `_PROOF` is the
# ---- frozen tactic script, retuned only by the loop-free positive (whose loop
# ---- invariant is gone with the loop).
_IMPL = (
    "    let mut result : List Member := []\n"
    "    let mut i := members.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ members.length\n"
    "      invariant result = shownMembers sel showUndocumented (members.drop i)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let m := members[i - 1]!\n"
    "      result := (if memberShown sel showUndocumented m then [m] else []) ++ result\n"
    "      i := i - 1\n"
    "    return result"
)

_STEP = (
    "      let m := members[i - 1]!\n"
    "      result := (if memberShown sel showUndocumented m then [m] else []) ++ result"
)

_PROOF = (
    "prove_correct selectMembers by\n"
    "  loom_solve\n"
    "  rw [shownMembers_drop_step members sel showUndocumented i (by omega) (by omega)]\n"
    "  simp_all"
)

for _a in (_IMPL, _STEP, _PROOF):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"


def _rival(body):
    """A uniqueness rival: the whole frozen loop replaced by a loop-free
    expression, so its extracted program REDUCES under `decide` and its witness
    can be checked. The frozen proof script is left as-is — a rival is not
    expected to prove anything, and retuning it would only mask the rejection."""
    return _swap(_BASE, _IMPL, body)


# ===========================================================================
# THE WITNESS REFERENCE. A loop-free, machine-checked-CORRECT implementation of
# the frozen spec, and the refutation subject for every reject case, because the
# FROZEN impl cannot serve as one (see the CARRIER NOTE: `decide` against its
# `Classical.choice` loop is stuck for every claim, so its exit code carries no
# information and the gate reports `witness-undecided`). This impl filters by the
# pure per-member decision directly, so it REDUCES: a witness that says "the spec
# is violated here" is genuinely refuted against it. Reproved by list induction —
# the loop invariant is gone with the loop, so the frozen script no longer
# applies; the `prove_correct selectMembers` obligation itself is untouched.
# Shipped as `pos-loopfree` below as well, so the battery records that
# loop-freeness is not what any rival is being rejected for.
# ===========================================================================
_LOOPFREE_PROOF = (
    "prove_correct selectMembers by\n"
    "  loom_solve\n"
    "  induction members with\n"
    "  | nil => simp [shownMembers]\n"
    "  | cons m ms ih =>\n"
    "    simp only [List.filter_cons, shownMembers_cons, ih]\n"
    "    split <;> simp_all"
)

_LOOPFREE = _swap(
    _rival("    return members.filter (fun m => memberShown sel showUndocumented m)"),
    _PROOF, _LOOPFREE_PROOF)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches the post-image through Velvet's own tester machinery:
# ---- `selectMembersTester members sel showUndocumented = false` says the
# ---- extracted program's result violates the postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped, so
# ---- no tactic script can mask the verdict. Every witness states its refutation
# ---- at CONCRETE literals (no opaque term, so nothing to condition on and no
# ---- hypothesis that could be inconsistent — `consistency_probe` finds no
# ---- binders to probe).
def _tester(call):
    return ("extract_program_for selectMembers\n"
            "prove_precondition_decidable_for selectMembers\n"
            "prove_postcondition_decidable_for selectMembers\n"
            "derive_tester_for selectMembers\n\n"
            f"example : {call} = false := by\n  decide\n")


# Concrete members reused across witnesses. A single member is enough to violate
# (M) at a per-member keep-decision; the order rival needs two.
_R_DOC = '[{name := "b", isRestricted := true, hasDoc := true}]'       # restricted, documented
_R_UNDOC = '[{name := "b", isRestricted := true, hasDoc := false}]'    # restricted, undocumented
_PUB_DOC = '[{name := "a", isRestricted := false, hasDoc := true}]'    # NON-restricted, documented
_TWO_PUBLIC = ('[{name := "a", isRestricted := false, hasDoc := true}, '
               '{name := "b", isRestricted := false, hasDoc := true}]')
# Two IDENTICAL members. Needed by the multiplicity rival: `Member` derives
# DecidableEq structurally, so a de-duplicating rival only differs from (M) when
# two surfaced entries are equal in every field — distinct names survive dedup.
_TWO_SAME = ('[{name := "a", isRestricted := false, hasDoc := true}, '
             '{name := "a", isRestricted := false, hasDoc := true}]')


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else SPEC-TOO-STRONG. Ports the nagini site-A
    # pos-control (a control-flow reshape computing the same keep-decision).
    # =====================================================================
    {
        "id": "pos-control-hoist-keep-local",
        "kind": "soundness",
        "expect": "verify",
        # Cheapest reshape: stage the per-member keep-decision through a named
        # local before the conditional cons. Every computed value is unchanged
        # and the loop invariant still holds verbatim, so the frozen loop-tuned
        # proof still discharges the byte-identical obligation.
        "module": _swap(
            _BASE, _STEP,
            "      let m := members[i - 1]!\n"
            "      let keep := memberShown sel showUndocumented m\n"
            "      result := (if keep then [m] else []) ++ result"),
        "rationale": "a correct reshape that stages the per-member keep-decision "
                     "through a named local before the conditional cons computes "
                     "the same result, so the master equality (M) "
                     "`out = shownMembers sel showUndocumented members` still "
                     "discharges under the frozen loop proof; must verify (else "
                     "SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-loopfree",
        "kind": "soundness",
        "expect": "verify",
        # The witness reference, shipped as a case in its own right. Reshape:
        # drop the backward loop entirely and filter by the pure per-member
        # decision. Behaviourally identical (same members, same input order),
        # reproved by list induction since the loop invariant is gone with the
        # loop. Recording it here is what makes its use as the reject lane's
        # refutation subject legible: the battery asserts, and the gate
        # independently re-checks, that this impl shares the frozen spec and
        # VERIFIES — so no rival is being rejected merely for being loop-free.
        "module": _LOOPFREE,
        "rationale": "filtering by the pure per-member keep-decision surfaces "
                     "exactly the members `shownMembers` keeps, in input order, "
                     "so (M) holds by list induction on the member list; a "
                     "correct loop-free reshape must verify, else "
                     "SPEC-TOO-STRONG. Also the `witness_reference` every reject "
                     "case is refuted against, so its verifying here is "
                     "load-bearing for the whole reject lane.",
    },
    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from the nagini site-A admissibility probe, which
    # re-establishes that the precondition admits a normal F2P-shaped input. This
    # method carries NO `require` (the pre-conditions region is empty), so nothing
    # could exclude a normal input and the classic "a normal input is admitted"
    # probe is vacuous. Re-aimed at the residual admissibility risk on a total
    # domain: that the master post-image is jointly SATISFIABLE by a gold-shaped
    # computation. The frozen impl verifying IS that witness. MUST verify, else
    # SPEC-UNSATISFIABLE.
    # =====================================================================
    {
        "id": "admiss-gold-total",
        "kind": "admissibility",
        "expect": "verify",
        "module": _BASE,  # frozen impl; same_spec trivially, must verify
        "rationale": "the input triple carries no `require`, so the filter is "
                     "total; the gold impl discharging (M) is the admissibility "
                     "witness that the post-image is jointly satisfiable — "
                     "near-trivial precisely because the precondition is empty. "
                     "Else SPEC-UNSATISFIABLE.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each carrying a tester `witness` that holds of the
    # rival and FAILS against `_LOOPFREE` (the refutation subject; gold cannot
    # decide — see the CARRIER NOTE), plus the refinement argument for why its
    # faithful real counterpart would NOT resolve the failing test.
    #
    # Verified during authoring, per rival: the rival MODULE fails to verify
    # (rc=1), the witness build against the rival exits 0, and the witness build
    # against `_LOOPFREE` exits 1 by REFUTATION (not by stuck reduction).
    # =====================================================================
    {
        "id": "partial-domain-boolean-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-fix bug: collapse the tri-state selection to the documentable
        # gate alone — surface every documentable member, restricted or not,
        # regardless of the selection. Correct on non-restricted members; wrong on
        # any documentable restricted member the selection does NOT name.
        "module": _rival(
            "    return members.filter (fun m => m.hasDoc || showUndocumented)"),
        "refinement": "this is the pre-fix behaviour: the selection is collapsed "
                      "to a truthy flag, so every documentable restricted member "
                      "is surfaced whenever the option is present. For the F2P "
                      "scenario (a specific selection naming one restricted "
                      "member) it surfaces the OTHER restricted member too, which "
                      "the failing test asserts must be dropped — this is the "
                      "exact regression the fix removes, so it would NOT resolve.",
        "rationale": "REJECT from (M): on a documentable restricted member whose "
                     "identifier is not in the specific selection, `shownMembers` "
                     "drops it (`selKeeps (.only …) name = false`) but the rival "
                     "keeps it, so `out ≠ shownMembers …`. If it verified ⇒ "
                     "SPEC-TOO-WEAK (the selection unenforced). Refuted at a "
                     "documented restricted member `\"b\"` with `.only [\"a\"]`.",
        "witness": _tester(f"selectMembersTester {_R_DOC} (Sel.only [\"a\"]) false"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "partial-domain-only-as-blanket",
        "kind": "uniqueness",
        "expect": "reject",
        # A subtler collapse: honour `.none` (drop) but treat a SPECIFIC selection
        # `.only names` as the blanket `.all` — surface every gated restricted
        # member regardless of whether its identifier is named. This is the
        # headline defect (a specific selection acting as an all-or-nothing
        # switch). A NEAR-MISS of the collapse rival: it agrees with gold over
        # strictly more of the domain (it is correct under `.none`), so it gets
        # its own witness at its own distinguishing input.
        "module": _rival(
            "    return members.filter (fun m =>\n"
            "      if m.isRestricted then\n"
            "        (m.hasDoc || showUndocumented) && "
            "(match sel with | .none => false | _ => true)\n"
            "      else (m.hasDoc || showUndocumented))"),
        "refinement": "a counterpart that routed a specific selection through the "
                      "blanket path (surface all gated restricted members whenever "
                      "any selection is given) would surface every documentable "
                      "restricted member for the F2P input, not only the named "
                      "one — the precise behaviour the feature is added to "
                      "prevent, so the specific-selection test would NOT resolve.",
        "rationale": "REJECT from (M) at the `.only` state: `selKeeps (.only "
                     "names) name` tests membership, but the rival returns `true` "
                     "for every gated restricted member under any non-empty "
                     "selection, diverging on a restricted member NOT in `names`. "
                     "Refuted at an UNDOCUMENTED restricted member `\"b\"` with "
                     "`.only [\"a\"]` and `showUndocumented = true` — the gate is "
                     "met via the undoc request, isolating the selection axis and "
                     "varying both `hasDoc` and `showUndocumented` away from the "
                     "collapse rival's point. If it verified ⇒ SPEC-TOO-WEAK.",
        "witness": _tester(f"selectMembersTester {_R_UNDOC} (Sel.only [\"a\"]) true"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "partial-domain-none-as-blanket",
        "kind": "uniqueness",
        "expect": "reject",
        # Mishandle the EMPTY selection: treat `.none` as `.all` (surface every
        # gated restricted member when NO selection is given). Attacks the `.none`
        # state of the tri-state — the sub-domain the `.only` rivals leave
        # correct.
        "module": _rival(
            "    return members.filter (fun m =>\n"
            "      if m.isRestricted then\n"
            "        (m.hasDoc || showUndocumented) && "
            "(match sel with | .none => true | .all => true | .only ns => ns.contains m.name)\n"
            "      else (m.hasDoc || showUndocumented))"),
        "refinement": "a counterpart that treated the absence of a selection as "
                      "\"surface all restricted members\" reintroduces the default "
                      "over-disclosure the tri-state is designed to prevent: with "
                      "no selection given, gated restricted members would be "
                      "surfaced where the default must drop them, failing the "
                      "no-selection test — it would NOT resolve.",
        "rationale": "REJECT from (M) at the `.none` state: `selKeeps .none _ = "
                     "false` (drop all), but the rival keeps every gated "
                     "restricted member. Refuted at a documented restricted "
                     "member with `Sel.none` — the tri-state state no membership "
                     "rival attacks. If it verified ⇒ SPEC-TOO-WEAK.",
        "witness": _tester(f"selectMembersTester {_R_DOC} Sel.none false"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "partial-domain-all-as-drop",
        "kind": "uniqueness",
        "expect": "reject",
        # Mishandle the BLANKET selection: treat `.all` as `.none` (drop every
        # restricted member even when the blanket selection is given). Attacks the
        # `.all` state — the remaining tri-state state.
        "module": _rival(
            "    return members.filter (fun m =>\n"
            "      if m.isRestricted then\n"
            "        (m.hasDoc || showUndocumented) && "
            "(match sel with | .none => false | .all => false | .only ns => ns.contains m.name)\n"
            "      else (m.hasDoc || showUndocumented))"),
        "refinement": "a counterpart that dropped every restricted member under "
                      "the blanket selection would fail to surface any restricted "
                      "member when the caller asks for all of them — the "
                      "blanket-selection test asserts they are surfaced, so it "
                      "would NOT resolve.",
        "rationale": "REJECT from (M) at the `.all` state: `selKeeps .all _ = "
                     "true` (surface all gated), but the rival drops them. Refuted "
                     "at a documented restricted member with `Sel.all` — the "
                     "third tri-state state, completing the `sel` binder coverage. "
                     "If it verified ⇒ SPEC-TOO-WEAK.",
        "witness": _tester(f"selectMembersTester {_R_DOC} Sel.all false"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "partial-domain-drop-doc-gate",
        "kind": "uniqueness",
        "expect": "reject",
        # Drop the documentable GATE on the restricted branch: surface a named
        # restricted member on the strength of the selection alone, even when it
        # is undocumented and undocumented members are NOT requested. Attacks the
        # `(hasDoc || showUndocumented)` conjunct on the restricted branch.
        "module": _rival(
            "    return members.filter (fun m =>\n"
            "      if m.isRestricted then selKeeps sel m.name\n"
            "      else (m.hasDoc || showUndocumented))"),
        "refinement": "a counterpart that surfaced a named restricted member "
                      "without also requiring it to be documented (or undocumented "
                      "members requested) would surface an undocumented restricted "
                      "member the default keep-decision drops, diverging from the "
                      "gated behaviour every test exercises — it would NOT resolve.",
        "rationale": "REJECT from (M): `memberShown` gates the restricted branch "
                     "on `(m.hasDoc || showUndocumented)` as well as the "
                     "selection, but the rival returns `selKeeps sel name` alone, "
                     "so it surfaces an undocumented named restricted member when "
                     "undocumented members are not requested. Refuted at an "
                     "undocumented restricted member `\"b\"` named in `.only "
                     "[\"b\"]` with `showUndocumented = false` — the only witness "
                     "whose selection NAMES the probed member, so it isolates the "
                     "gate rather than the selection. If it verified ⇒ "
                     "SPEC-TOO-WEAK (the gate unpinned on the restricted branch).",
        "witness": _tester(f"selectMembersTester {_R_UNDOC} (Sel.only [\"b\"]) false"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "partial-domain-selection-applies-to-all",
        "kind": "uniqueness",
        "expect": "reject",
        # Attack the BRANCH DISPATCH itself: apply the selection uniformly to
        # EVERY member instead of only to restricted ones, collapsing the
        # two-branch structure of `memberShown`. Correct on restricted members
        # (both conjuncts survive); wrong on NON-restricted members, which (M)
        # gates on documentation ALONE and never on the selection. The mirror
        # image of the collapse rival — that one drops the selection everywhere,
        # this one imposes it everywhere — and the only rival that varies
        # `isRestricted` on the single-member sub-domain.
        "module": _rival(
            "    return members.filter (fun m =>\n"
            "      (m.hasDoc || showUndocumented) && selKeeps sel m.name)"),
        "refinement": "a counterpart that consulted the restricted-member "
                      "selection for ordinary members too would stop surfacing "
                      "documented ordinary members whenever no selection (or a "
                      "selection not naming them) was given — the ordinary "
                      "members every documentation build emits by default would "
                      "vanish, so the tests asserting their presence would NOT "
                      "resolve.",
        "rationale": "REJECT from (M) at the NON-restricted branch: `memberShown` "
                     "gates an unrestricted member on `m.hasDoc || "
                     "showUndocumented` and never consults `sel`, but the rival "
                     "conjoins `selKeeps sel m.name` for every member. Refuted at "
                     "a documented NON-restricted member `\"a\"` with `Sel.none` "
                     "(which the rival drops and (M) keeps) — the branch-dispatch "
                     "clause, attacked by no other single-member rival. If it "
                     "verified ⇒ SPEC-TOO-WEAK (the branch structure unpinned).",
        "witness": _tester(f"selectMembersTester {_PUB_DOC} Sel.none false"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "structural-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct MEMBERSHIP, wrong ORDER: keep exactly the members `shownMembers`
        # keeps, but emit them reversed. Attacks the input-order clause of (M),
        # which no membership rival touches, over the multi-element sub-domain.
        "module": _rival(
            "    return (members.filter "
            "(fun m => memberShown sel showUndocumented m)).reverse"),
        "refinement": "a counterpart that surfaced the right members but in "
                      "reversed source order would emit the documentation entries "
                      "out of order; the failing test matches the generated output "
                      "as an ordered sequence, so a reversed collection of two or "
                      "more surfaced members would NOT resolve.",
        "rationale": "REJECT from (M), which pins the result in INPUT ORDER "
                     "(`shownMembers` is order-preserving): the rival reverses it, "
                     "so on any input with two distinct surfaced members `out ≠ "
                     "shownMembers …`. Refuted at TWO documented non-restricted "
                     "members — a distinct clause (order) and the only "
                     "multi-element witness in the battery, so it is also what "
                     "varies the member-list binder past length 1. If it verified "
                     "⇒ SPEC-TOO-WEAK.",
        "witness": _tester(f"selectMembersTester {_TWO_PUBLIC} Sel.none false"),
        "witness_reference": _LOOPFREE,
    },
    {
        "id": "structural-dedup-output",
        "kind": "uniqueness",
        "expect": "reject",
        # Correct membership AND correct order, wrong MULTIPLICITY: keep exactly
        # the members `shownMembers` keeps, in input order, but collapse equal
        # entries to one. Attacks the multiplicity clause of (M) — the only clause
        # left untouched by the six keep-decision rivals and by the order rival,
        # each of which is multiplicity-faithful.
        "module": _rival(
            "    return (members.filter "
            "(fun m => memberShown sel showUndocumented m)).eraseDups"),
        "refinement": "a counterpart that surfaced the right members in the right "
                      "order but silently merged entries that agree in every field "
                      "would emit one entry where the collection holds two, so a "
                      "check counting the surfaced entries would NOT resolve.",
        "rationale": "REJECT from (M), which pins `out` to `shownMembers …` as a "
                     "LIST and therefore preserves multiplicity: `shownMembers` "
                     "appends a singleton per kept member and never compares "
                     "members to each other, so two entries equal in every field "
                     "both survive. The rival's `eraseDups` keeps one. Refuted at "
                     "TWO IDENTICAL documented ordinary members, the input point "
                     "where dedup and (M) first disagree — distinct-name inputs "
                     "cannot expose it, which is why no other rival's witness "
                     "reaches this clause. If it verified ⇒ SPEC-TOO-WEAK (the "
                     "post-image pinned only up to set-of-members, leaving an impl "
                     "free to drop a genuine repeated entry).",
        "witness": _tester(f"selectMembersTester {_TWO_SAME} Sel.none false"),
        "witness_reference": _LOOPFREE,
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING. The sibling battery has 9 SPEC cases across TWO
# contracted functions: a per-member keep-decision [site A] and a selector-list
# merge [site B]. This bundle models ONLY the per-member keep-filter (site A;
# mapping.md §1–2), so every site-B case has no counterpart on this carrier.
#
#   nagini case (site)                          -> here
#   -----------------------------------------------------------------------
#   pos-control-A-nested-tree              (A)  -> pos-control-hoist-keep-local
#                                                                    RE-EXPRESSED
#   admissibility-A-readonly-names         (A)  -> admiss-gold-total  RE-AIMED
#   frame-mutation-A-write-names           (A)  -> (none)             VACUOUS
#   partial-domain-A-boolean-collapse      (A)  -> partial-domain-boolean-collapse
#                                                                        PORTED
#   asymmetry-A-mode2-ignores-inherited    (A)  -> (none)          NOT-ON-CARRIER
#   pos-control-B-merged-noop-loop         (B)  -> (none)          NOT-MODELED (B)
#   frame-mutation-B-write-members         (B)  -> (none)          NOT-MODELED (B)
#   partial-domain-B-drop-extra-names      (B)  -> (none)          NOT-MODELED (B)
#   partial-domain-B-noop-dropped          (B)  -> (none)          NOT-MODELED (B)
#   (no sibling)                                -> pos-loopfree                     ADDED
#   (no sibling)                                -> partial-domain-only-as-blanket   ADDED
#   (no sibling)                                -> partial-domain-none-as-blanket   ADDED
#   (no sibling)                                -> partial-domain-all-as-drop       ADDED
#   (no sibling)                                -> partial-domain-drop-doc-gate     ADDED
#   (no sibling)                                -> partial-domain-selection-applies-to-all
#                                                                                   ADDED
#   (no sibling)                                -> structural-reverse-order         ADDED
#   (no sibling)                                -> structural-dedup-output          ADDED
#
# Result: 11 velvet cases (2 soundness, 1 admissibility, 8 uniqueness).
#
# RE-EXPRESSED (positive control): the nagini site-A positive re-shapes a flat
#   early-return cascade into a nested if/elif tree. There is no cascade here (the
#   keep-decision is a single `memberShown` call inside the copy loop), so the
#   same "structurally different but correct" intent is re-expressed as hoisting
#   the per-member decision into a named local — the cheapest reshape that keeps
#   the frozen loop proof valid. Verified: builds green (rc=0).
# RE-AIMED (admissibility): the nagini site-A probe re-establishes the
#   half-permission + mode-bound precondition on an F2P-shaped input. This method
#   has NO `require`, so "a normal input is admitted" is vacuous — nothing could
#   exclude one. Re-aimed at the residual total-domain risk: that the master
#   post-image is jointly SATISFIABLE. The frozen impl discharging (M) is that
#   witness.
# VACUOUS (frame-mutation, site A): the sibling rejects an impl that WRITES to a
#   read-only half-permission name list. This backend is referentially
#   transparent and the method declares no `mut` binder, so there is no read-only
#   input to overwrite and no substitute probe. Not fabricated (per the porting
#   map: this class is vacuous on lean/velvet).
# NOT-ON-CARRIER (asymmetry / inherited-member filter, site A): the sibling
#   rejects an impl that drops the inherited-member filter in the specific-
#   selection state. That filter is constantly inactive in the modeled scenario
#   (mapping.md §2: the modeled collection is a module, so the inherited-member
#   test is identically false), so it is NOT a field of `Member` and NOT a term
#   in (M). A rival attacking it would have no clause to violate — DROPPED, not
#   fabricated. This is a genuine carrier narrowing (the modeled scenario is the
#   want-all module case), recorded here as a known gap, not omitted because it
#   was hard: if a later revision adds an inherited-member field to `Member`,
#   this is the case to add back.
# NOT-MODELED (all four site-B cases): the selector-list merge is a SEPARATE
#   contracted function in the sibling; this bundle models only the per-member
#   keep-filter, so the merge — its positive control, its frame-mutation reject,
#   its drop-extra-names reject, and its no-op-dropped reject — has no counterpart
#   in this carrier. Omitted as carrier narrowing (451/500 lean and 433/500
#   velvet bundles model only the functional core where the sibling contracts ≥5
#   functions); chasing parity would mean fabricating rivals for a behaviour this
#   bundle does not model. Note the sibling itself records that its merge
#   postcondition does not pin "no duplicates" — a genuine permissiveness on a
#   function absent here. The *class* of defect does carry over, though, even
#   though the site does not: (M) pins `out` as a LIST, so multiplicity IS
#   observable on this carrier, and `structural-dedup-output` attacks it here
#   rather than letting the clause go unprobed (audit finding; see ADDED below).
# ADDED (8): this carrier makes the tri-state selection EXPLICIT as `Sel`, so the
#   single master equality is attacked at each `Sel` state and at each structural
#   clause the sibling folds into its collapse rival:
#     * partial-domain-only-as-blanket  — `.only` mishandled as the blanket
#       switch (the headline "specific selection ≠ show-all" defect);
#     * partial-domain-none-as-blanket  — `.none` (empty selection) mishandled;
#     * partial-domain-all-as-drop      — `.all` (blanket selection) mishandled;
#     * partial-domain-drop-doc-gate    — the documentable gate on the restricted
#       branch dropped;
#     * partial-domain-selection-applies-to-all — the two-branch DISPATCH
#       collapsed (the selection imposed on ordinary members too);
#     * structural-reverse-order        — the input-order clause of (M);
#     * structural-dedup-output         — the MULTIPLICITY clause of (M): correct
#       membership and correct order, but equal entries collapsed;
#     * pos-loopfree                    — the witness reference, shipped as a
#       positive so the reject lane's subject is itself gate-checked.
#   None is a fabricated wrongness: each is a real regression with a
#   machine-checked witness that holds of the rival and fails on the reference.
#
# CLAUSE / BINDER COVERAGE. (M) is the single obligation; it is defended by two
#   positives + admissibility and attacked by all eight rivals. Coverage of (M)'s
#   independent structure: the restricted-branch selection conjunct (collapse,
#   only-as-blanket, none-as-blanket, all-as-drop), the restricted-branch
#   documentable gate (drop-doc-gate), the NON-restricted branch and the dispatch
#   between the two (selection-applies-to-all), the result order (reverse-order),
#   and the result multiplicity (dedup-output). The last two are the clauses a
#   keep-decision rival cannot reach: every one of the six is order- and
#   multiplicity-faithful, so without them an impl free to reorder or to merge
#   equal entries would satisfy every other case in this battery.
#   Binder variation across the reject witnesses:
#     sel              — .none (none-as-blanket, selection-applies-to-all,
#                        reverse-order), .all (all-as-drop), .only (collapse,
#                        only-as-blanket, drop-doc-gate) — all three states, and
#                        `.only` at both a NON-matching name (collapse,
#                        only-as-blanket) and a MATCHING one (drop-doc-gate);
#     showUndocumented — true (only-as-blanket), false (the other six);
#     Member.isRestricted — true (five rivals), false (selection-applies-to-all,
#                        reverse-order);
#     Member.hasDoc    — true (collapse, none-as-blanket, all-as-drop,
#                        selection-applies-to-all, reverse-order, dedup-output),
#                        false (only-as-blanket, drop-doc-gate);
#     members (length) — 1 (six rivals), 2 distinct (reverse-order), 2 EQUAL
#                        (dedup-output — a point no other witness can reach, since
#                        dedup is invisible on distinct members).
#   The distinct witness input points are eight, one per rival:
#     (.only["a"], b/restricted/doc,   su=false)   collapse
#     (.only["a"], b/restricted/undoc, su=true)    only-as-blanket
#     (.none,      b/restricted/doc,   su=false)   none-as-blanket
#     (.all,       b/restricted/doc,   su=false)   all-as-drop
#     (.only["b"], b/restricted/undoc, su=false)   drop-doc-gate
#     (.none,      a/ordinary/doc,     su=false)   selection-applies-to-all
#     (.none,      two ordinary/doc,   su=false)   reverse-order
#     (.none,      two IDENTICAL a/doc, su=false)  dedup-output
#   so no two rivals share a point and every input binder is moved by some
#   witness — the battery probes the spec's dependence on each binder rather than
#   asserting one shared point seven times. In particular the two near-misses of
#   the collapse rival (only-as-blanket, which is correct under `.none`, and
#   selection-applies-to-all, which is correct on restricted members) are each
#   refuted at the input that distinguishes THEM, not at the collapse's point.
#
# WITNESS MECHANICS — and the correction to the previous port of this cell.
#   The spec is COMPUTABLE (concrete `def`s over DecidableEq carriers), so
#   witnesses use Velvet's tester (`extract_program_for` … `derive_tester_for` …
#   `decide`) at concrete literals. The frozen impl is a backward `while` loop
#   whose extracted program elaborates through `Classical.choice` under demonic
#   choice; the kernel cannot unfold it, so `decide` against GOLD is stuck for
#   EVERY claim. An earlier battery for this cell read that stuck failure as
#   discrimination and shipped six rejects whose witnesses were never actually
#   decided; the gate recorded MALFORMED-TESTS (6x `witness-undecided`). That
#   reading was wrong, and measurably so: a TRUE claim about gold
#   (`… = true` at an agreement point) fails with the IDENTICAL
#   `did not reduce to `isTrue` or `isFalse``, so gold's exit code carried no
#   information and a forged witness asserting the rival CORRECT would have
#   cleared both halves.
#   The repair is `witness_reference = _LOOPFREE` on every reject case: a
#   loop-free impl of the same frozen spec, which the gate checks shares the spec
#   and VERIFIES before refuting any witness against it. Measured during
#   authoring, per rival: rival module rc=1 (does not verify); witness-vs-rival
#   rc=0; witness-vs-`_LOOPFREE` rc=1 by REFUTATION with no stuck-reduction
#   message. And on the subject itself: the forgery ("the rival is correct here")
#   is refuted against `_LOOPFREE` (rc=1, not stuck) while a true claim is
#   confirmed (rc=0) — so this subject decides both directions, which is exactly
#   what gold could not do. No witness binds a hypothesis (all inputs are
#   literals), so there is no `witness-inconsistent` risk: `consistency_probe`
#   finds no binders to probe.
#
# DIVERGENCE lane - the class is CLOSED BY THE SEMANTICS here, and a diverging
#   rival is REJECTED rather than admitted. This bundle sets
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
#
# AXIOM_TESTS: dropped. The nagini file's two axiom-soundness probes are G-AX's
#   job (axiom_check.py / mapping.md); the G-PBT gate ignores AXIOM_TESTS.
AXIOM_TESTS = []
