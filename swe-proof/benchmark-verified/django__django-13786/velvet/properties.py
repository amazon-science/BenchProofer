"""properties.py — G-PBT falsification battery for django__django-13786 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct combineTrackedSettings`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: it must elaborate against the rival and FAIL, by a
DECIDED verdict rather than a stuck reduction, against the witness subject — here
the ``witness_reference`` rather than the frozen solution, for the reason set out
under WITNESS MECHANICS below).

DEFENDED SURFACE (one contracted method):

  combineTrackedSettings
      (baseMap : SettingMap) (newMap : SettingMap) (trackedKeys : List String)
      return (out : SettingMap)
    ensures out = pruneFold newMap trackedKeys (mergeMaps baseMap newMap)

The method combines two settings maps under a managed-key discipline. A settings
map is an association list of key→value pairs (``SettingMap``), compared as a set
of pairs. The result is the override-merge of the base map by the overriding map,
FURTHER restricted so that every managed (tracked) key the overriding map does
NOT mention is cleared. Three input binders, all free; the post-image must hold
for every value of each:
  * ``baseMap``     — the existing settings map;
  * ``newMap``      — the overriding map (its bindings win on shared keys);
  * ``trackedKeys`` — the prescribed set of managed keys.

The single equality post-image composes three independently-attackable
behaviours, all grounded in the input binders (the ``axioms`` region is empty;
``mergeMaps``/``pruneFold``/``eraseKey``/``keyPresent`` are concrete ``def``s in
the ``pure`` region — there is no opaque answer-key to echo, so the unique
satisfier IS the grounded combination):
  (M) OVERRIDE-MERGE (``mergeMaps baseMap newMap``): the union of both maps'
      keys, with the overriding map winning on a shared key AND every base-only
      key (managed or not) carried through.
  (P-clear) PRUNE-CLEAR: a managed key the overriding map OMITS is dropped from
      the merged map — THE bug→fix delta behaviour.
  (P-keep) PRUNE-KEEP (the guard ``if keyPresent k newMap then rest else
      eraseKey k rest``): a managed key the overriding map PROVIDES is NOT
      dropped — the overriding value survives.

ADVERSARIAL READ of the sibling's classes:
  * FRAME-MUTATION — VACUOUS on this backend. The sibling's mandatory
    frame-mutation rival writes back into a read-only mapping input that carries
    only a fractional heap permission (``Acc(dict_pred(operation_options),1/2)``)
    and is rejected for INSUFFICIENT PERMISSION. Lean and Velvet are
    referentially transparent: ``baseMap`` / ``newMap`` / ``trackedKeys`` are
    immutable values, this bundle declares no ``mut`` parameter, there is no heap
    and no aliasing. There is no read-only input to overwrite and no permission
    system to trip, so the class is vacuous. No substitute is fabricated (per the
    porting map, this class is legitimately dropped rather than replaced).
  * ADMISSIBILITY — RE-AIMED and PORTED (``admiss-postimage-nondegenerate``).
    The sibling's control confirms two half-permission preconditions admit a
    normal F2P-shaped input; this bundle's method has NO precondition (the
    pre-conditions region is empty; the contract is total over the three
    carriers), so that literal probe is vacuous. But "the frozen obligation has
    no precondition" is NOT a reason to drop the lane, and an earlier revision of
    this file dropped it for exactly that reason — which was wrong. The analogue
    on a total carrier is the obligation being UNSATISFIABLE or DEGENERATE at an
    F2P-shaped input, because a post-image no impl can meet reads exactly like a
    post-image every impl meets. Nor do the other two lanes cover it: a soundness
    positive shows SOME impl satisfies the spec, a reject witness shows some impl
    VIOLATES it, and neither pins the post-image's VALUE at the point the fix is
    about. The ported case discharges that value by EVALUATION as an in-region
    ``assert`` at a concrete F2P-shaped input, then closes the frozen obligation
    verbatim; it is live in both directions (a false claim about the same point
    fails, and the frozen script alone does not absorb the assert — both
    measured).
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is pinned to a concrete pure
    computation of the method's own inputs; there is no answer-key term a wrong
    impl could echo. The cheapest correct impls compute it, which the positive
    controls cover honestly.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface: a rival can get the merge
    right yet mishandle the prune on a sub-domain (a managed key on the base map
    omitted by the overriding map), over-prune a provided managed key, drop a
    base-only non-managed key, or invert the override precedence.

WITNESS MECHANICS ON THIS BUNDLE — why every reject case carries a
``witness_reference``. The frozen impl keeps a backward ``while`` loop under
``loom.semantics.choice "demonic"``, so its fixpoint elaborates through
``Classical.choice``, which the kernel cannot unfold. The frozen tester
therefore does NOT reduce under ``decide`` for ANY claim, true or false: every
gold-side build fails with

    reduction got stuck at the `Decidable` instance
      match combineTrackedSettingsTester [("k", "v")] [] ["k"], false with ...

That is a stuck reduction, NOT a refutation, so the frozen side's exit code
carries no information and cannot serve as the "fails on gold" half — a forged
witness asserting a rival is CORRECT would clear it just as well. (This is the
``witness-undecided`` outcome; the reduction goes through the loop no matter
which projection of the result is stated, since the loop IS the frozen impl, so
route 1 — a computable projection — is not available here.)

The repair is ``witness_reference``: each reject case is refuted against
``_REFERENCE``, a loop-free impl of the SAME frozen spec that does reduce. The
gate independently checks that the reference shares the frozen spec and
VERIFIES before trusting it (an impl that failed everything would refute every
witness), and ``_REFERENCE`` is additionally shipped as the ``pos-control-direct``
``expect="verify"`` case, so the battery itself records that loop-freeness is
not what any rival is rejected for.

Both halves were checked out-of-band with ``scripts/lean_verify.sh``: every
witness ELABORATES against its rival (exit 0) and, against ``_REFERENCE``, fails
by genuine refutation — ``Tactic `decide` proved that the proposition
combineTrackedSettingsTester ... = false is false`` (exit 1, a decided verdict,
no stuck reduction). So each rejection is attributable to the spec and not to
mechanical tactic breakage. Witnesses use only concrete ``String`` literals and
``decide``; no opaque term appears and no witness head binds anything, so no
carrier conditioning (and hence no joint-satisfiability hazard) is involved.

AXIOM lane: EMPTY. ``meta.json`` declares no consumed ``axiom``; the one deep
model reference (``trackedKeys`` ↔ the managed-key constant) is an A-reference
validated by ``axiom_check.py`` (G-AX). Nothing in the proof rests on an axiom,
and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-13786"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the entire frozen backward-prune loop body. Lies
# ---- wholly inside the single `-- impl-start`/`-- impl-end` region and is
# ---- unique in Solution.lean (both facts asserted at load by _swap).
_IMPL = (
    "    let mut result : SettingMap := mergeMaps baseMap newMap\n"
    "    let mut i := trackedKeys.length\n"
    "    while i > 0\n"
    "      invariant 0 ≤ i ∧ i ≤ trackedKeys.length\n"
    "      invariant result = pruneFold newMap (trackedKeys.drop i) (mergeMaps baseMap newMap)\n"
    "      done_with i = 0\n"
    "      decreasing i\n"
    "    do\n"
    "      let c := trackedKeys[i - 1]!\n"
    "      result := if keyPresent c newMap then result else eraseKey c result\n"
    "      i := i - 1\n"
    "    return result"
)

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"

# ---- proof-body anchor. The frozen tactic script is tuned to the frozen
# ---- backward-prune loop (it discharges the loop-body goal via the drop-step
# ---- lemma). A positive control that reshapes the impl away from that loop must
# ---- retune the tactic body; both the impl region and the `prove_correct` body
# ---- are elided from the spec view, so same_spec still holds and the
# ---- `prove_correct combineTrackedSettings` obligation survives with an
# ---- identical statement. Unique in the file.
_PROOF = (
    "prove_correct combineTrackedSettings by\n"
    "  loom_solve\n"
    "  rw [pruneFold_drop_step newMap trackedKeys (mergeMaps baseMap newMap) i (by omega) (by omega)]\n"
    "  simp_all"
)

assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"

# A reshaped straight-line impl (no loop) leaves `loom_solve` a goal that closes
# without the loop-body drop-step lemma; retune to the bare tactic.
_PROOF_STRAIGHT = "prove_correct combineTrackedSettings by\n  loom_solve"

# The frozen tactic script wrapped in an alternation with a `decide` arm, for the
# admissibility case: its in-region `assert` leaves ONE extra ground goal that
# `loom_solve` does not close on its own (measured — the bare frozen script exits
# 1 with `unsolved goals case «admiss_1: ...»`), while the loop-body goal still
# needs the drop-step lemma. `all_goals first | <frozen> | decide` closes both
# without weakening either. The tactic body is elided from the spec view, so
# same_spec and the `prove_correct combineTrackedSettings` header are untouched.
_PROOF_ASSERT = (
    "prove_correct combineTrackedSettings by\n"
    "  loom_solve\n"
    "  all_goals first\n"
    "    | (rw [pruneFold_drop_step newMap trackedKeys (mergeMaps baseMap newMap)"
    " i (by omega) (by omega)];\n"
    "       simp_all)\n"
    "    | decide")


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl region body replaced
    (frozen tactic script kept — used for reject rivals, which are expected NOT
    to verify)."""
    return _swap(_BASE, _IMPL, new_body)


def _impl_proof(new_body, new_proof):
    """Reshape the impl region AND retune the tactic body (soundness positives
    whose reshaped impl no longer matches the frozen loop-tuned script)."""
    return _swap(_swap(_BASE, _IMPL, new_body), _PROOF, new_proof)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's own tester machinery:
# ---- `combineTrackedSettingsTester <args> = false` says the extracted
# ---- program's result violates the method's postcondition at that concrete
# ---- input. Checked in a file whose `prove_correct` block has been stripped.
def _tester(body):
    return ("extract_program_for combineTrackedSettings\n"
            "prove_precondition_decidable_for combineTrackedSettings\n"
            "prove_postcondition_decidable_for combineTrackedSettings\n"
            "derive_tester_for combineTrackedSettings\n\n" + body)


def _witness(call):
    return _tester(f"example : {call} = false := by\n  decide\n")


# ---- The witness subject. The FROZEN impl cannot serve as one: its `while` loop
# ---- elaborates through `Classical.choice`, so `decide` against the frozen
# ---- tester is stuck for every claim and its exit code discriminates nothing
# ---- (`witness-undecided`). This is a loop-free impl of the SAME frozen spec —
# ---- it applies the pure combination directly, so the extracted program reduces
# ---- fully and a tester statement DECIDES against it. The gate checks it shares
# ---- the frozen spec and VERIFIES before refuting any witness against it, and it
# ---- is also shipped as the `pos-control-direct` expect="verify" case below so
# ---- the battery records that loop-freeness is not what any rival is rejected
# ---- for. Shared by the whole reject lane; the gate verifies it once.
_REFERENCE = _impl_proof(
    "    let out : SettingMap := pruneFold newMap trackedKeys (mergeMaps baseMap newMap)\n"
    "    return out",
    _PROOF_STRAIGHT)


# ---- The admissibility case's in-region `assert`: a ground, fully concrete
# ---- claim about the post-image's own pure computation at an F2P-shaped input.
# ---- Prepended to the frozen impl, which is then re-appended VERBATIM so the
# ---- method's own obligation still discharges on its own terms.
#
# The point is the one the whole reject lane leaves untouched: a base map
# carrying TWO tracked keys — one the overriding map rebinds, one it omits —
# plus a non-tracked key. Three conjuncts pin the post-image there and pin it
# AWAY from both degenerate collapses:
#   (1) the image is exactly [("t2","new"), ("u","keep")]  — the rebound tracked
#       key takes the overriding value, the omitted tracked key is cleared, the
#       non-tracked key survives, all at once;
#   (2) it is NOT the plain override-merge (so the clear direction is live —
#       a post-image that pruned nothing would satisfy neither the spec nor this);
#   (3) it is NOT the clear-every-tracked-key image (so the keep direction is
#       live — a post-image that over-pruned would fail this).
_ASSERT_ADMISS = (
    "    assert (with_name_prefix `admiss\n"
    "      (pruneFold [(\"t2\", \"new\")] [\"t1\", \"t2\"]\n"
    "           (mergeMaps [(\"t1\", \"old\"), (\"t2\", \"stale\"), (\"u\", \"keep\")]"
    " [(\"t2\", \"new\")])\n"
    "         = [(\"t2\", \"new\"), (\"u\", \"keep\")]\n"
    "       ∧ pruneFold [(\"t2\", \"new\")] [\"t1\", \"t2\"]\n"
    "           (mergeMaps [(\"t1\", \"old\"), (\"t2\", \"stale\"), (\"u\", \"keep\")]"
    " [(\"t2\", \"new\")])\n"
    "         ≠ mergeMaps [(\"t1\", \"old\"), (\"t2\", \"stale\"), (\"u\", \"keep\")]"
    " [(\"t2\", \"new\")]\n"
    "       ∧ pruneFold [(\"t2\", \"new\")] [\"t1\", \"t2\"]\n"
    "           (mergeMaps [(\"t1\", \"old\"), (\"t2\", \"stale\"), (\"u\", \"keep\")]"
    " [(\"t2\", \"new\")])\n"
    "         ≠ [(\"u\", \"keep\")]))\n")


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT
    # impls that MUST verify. If a faithful correct impl cannot verify, the spec
    # is SPEC-TOO-STRONG. Each replaces the frozen backward-prune loop with a
    # straight-line application of the pure combination and retunes the tactic
    # body to `loom_solve` (the loop-body drop-step lemma is no longer needed).
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: apply the pure combination directly, no per-key loop.
        # Trivially equal to the post-image on every input. This is the SAME
        # source the reject lane uses as its `witness_reference`, shipped as a
        # case in its own right so the battery records that loop-freeness is not
        # what any rival is rejected for.
        "module": _REFERENCE,
        "rationale": (
            "a straight-line application of the pure combination is the simplest "
            "correct impl and reduces the post-image to a reflexive equality, so "
            "it must verify. If it fails the spec is SPEC-TOO-STRONG (a faithful "
            "correct impl rejected because the frozen loop shape was over-fit). "
            "It is also the reject lane's `witness_reference`: the gate requires "
            "the witness subject to VERIFY, and this case is that requirement "
            "recorded as a case."
        ),
    },
    {
        "id": "pos-control-let-merged",
        "kind": "soundness",
        "expect": "verify",
        # A second, structurally-different correct reshape: name the merge in a
        # local, then prune. Same value on every input; distinct executable
        # surface from pos-control-direct.
        "module": _impl_proof(
            "    let merged : SettingMap := mergeMaps baseMap newMap\n"
            "    let out : SettingMap := pruneFold newMap trackedKeys merged\n"
            "    return out",
            _PROOF_STRAIGHT),
        "rationale": (
            "binding the override-merge in a local before pruning computes the "
            "SAME value on every input (a `let`-inlining of pos-control-direct), "
            "so the post-image still holds; a second structurally-different "
            "correct reshape defends the soundness surface. If it fails => "
            "SPEC-TOO-STRONG."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — re-aimed, and NOT vacuous. This method has no `require`
    # clause, so the sibling's literal probe ("a normal input satisfies the
    # precondition") has nothing to test: no input is excluded. But "the frozen
    # obligation has no precondition" is not a reason to drop the lane — the
    # analogue on a total carrier is the obligation being UNSATISFIABLE or
    # DEGENERATE at exactly an F2P-shaped input, because a post-image no impl can
    # meet reads exactly like a post-image every impl meets, and neither the
    # soundness positives nor the reject witnesses test it: a positive shows SOME
    # impl satisfies the spec somewhere, and a reject witness shows some impl
    # VIOLATES it — neither pins the post-image's VALUE at the point the fix is
    # about.
    #
    # So this case discharges the value BY EVALUATION, as an in-region `assert` at
    # a fully concrete F2P-shaped input, and only then closes the frozen
    # obligation with the frozen impl kept verbatim. The tactic body gains one
    # `decide` arm for the extra ground goal (elided from the spec view).
    #
    # LIVE, not decoration: the identical case with the FIRST conjunct changed to
    # the unpruned image leaves the assert unprovable — measured, exit 1,
    # `Tactic `decide` proved that the proposition ... is false`. And the frozen
    # tactic script alone does NOT absorb the assert — also measured, exit 1,
    # `unsolved goals case «admiss_1: ...»` — so the `decide` arm is doing real
    # work rather than papering over a goal `loom_solve` had already closed.
    # =====================================================================
    {
        "id": "admiss-postimage-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(_ASSERT_ADMISS + _IMPL, _PROOF_ASSERT),
        "rationale": (
            "PRECOND-TOO-STRONG probe, re-aimed at what that direction IS on a "
            "total carrier: the post-image must be SATISFIABLE and non-degenerate "
            "at an F2P-shaped input, since an obligation nothing can meet is "
            "indistinguishable from one everything meets. Discharged by EVALUATION "
            "as an in-region `assert` at base=[(\"t1\",\"old\"),(\"t2\",\"stale\"),"
            "(\"u\",\"keep\")], new=[(\"t2\",\"new\")], tracked=[\"t1\",\"t2\"] — a "
            "base map carrying two tracked keys, one REBOUND by the overriding map "
            "and one OMITTED, plus a non-tracked key — before the frozen "
            "obligation is closed verbatim. The assert pins the image to exactly "
            "[(\"t2\",\"new\"),(\"u\",\"keep\")] and pins it AWAY from both "
            "degenerate collapses (the plain override-merge, which prunes nothing; "
            "and [(\"u\",\"keep\")], which prunes every tracked key). This is also "
            "the only case in the battery at the rebind-one-clear-another point: "
            "every reject witness varies at most one tracked key at a time. "
            "(Sibling: admiss-f2p-shaped, whose half-permission Requires probe is "
            "vacuous here — but the lane is not.)"
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # DISTINCT concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test.
    # =====================================================================
    {
        "id": "weak-bare-merge-no-prune",
        "kind": "uniqueness",
        "expect": "reject",
        # The pre-patch skeleton: the override-merge with NO pruning. A managed
        # key on the base map that the overriding map omits survives.
        "module": _impl(
            "    let out : SettingMap := mergeMaps baseMap newMap\n"
            "    return out"),
        "refinement": (
            "this IS the pre-patch behaviour: the combination is the plain "
            "override-merge with no logic to clear managed keys the overriding "
            "map does not supply. Its faithful counterpart is the unchanged repo, "
            "which on the failing scenario (a base map carrying a managed setting, "
            "an overriding map that omits it) emits the combined operation with "
            "that managed setting still present, where the failing test now "
            "asserts it is cleared. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from the (P-clear) behaviour of the post-image: on a base map "
            "carrying a tracked key omitted by the overriding map, "
            "`pruneFold ... (mergeMaps ...)` drops that key but the plain merge "
            "keeps it, so the results differ. Verifying would be SPEC-TOO-WEAK "
            "(the managed-key clearing unenforced). Refuted at "
            "base=[(\"k\",\"v\")], new=[], tracked=[\"k\"] — a base-only tracked "
            "key omitted by the overriding map."
        ),
        "witness": _witness(
            'combineTrackedSettingsTester [("k", "v")] [] ["k"]'),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-prune-only-head",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: prunes ONLY the first tracked key, forgetting the rest.
        # Correct whenever at most the head tracked key needs clearing; diverges
        # when a later tracked key is on the base map and omitted by the override.
        "module": _impl(
            "    let merged : SettingMap := mergeMaps baseMap newMap\n"
            "    let out : SettingMap := match trackedKeys with\n"
            "      | [] => merged\n"
            "      | k :: _ => if keyPresent k newMap then merged else eraseKey k merged\n"
            "    return out"),
        "refinement": (
            "a counterpart that cleared only the first managed key in the "
            "prescribed set would leave every OTHER managed key the overriding "
            "map omits still present on the combined operation. On the failing "
            "scenario where a non-first managed setting must be cleared, it emits "
            "that setting, where the test asserts it is gone. It would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from (P-clear) over the FULL tracked list: `pruneFold` clears "
            "every omitted tracked key, but the rival clears at most the head. "
            "Refuted at base=[(\"b\",\"v\")], new=[], tracked=[\"a\",\"b\"] — a "
            "SECOND tracked key on the base map omitted by the override (varying "
            "the `trackedKeys` list length and probing a non-head element, which "
            "no other reject witness does)."
        ),
        "witness": _witness(
            'combineTrackedSettingsTester [("b", "v")] [] ["a", "b"]'),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-overclear-provided-key",
        "kind": "uniqueness",
        "expect": "reject",
        # Over-clear: drop EVERY tracked key unconditionally, even one the
        # overriding map PROVIDES. Correct only when the overriding map supplies
        # none of the tracked keys; diverges when it provides one.
        "module": _impl(
            "    let merged : SettingMap := mergeMaps baseMap newMap\n"
            "    let out : SettingMap := trackedKeys.foldl (fun m k => eraseKey k m) merged\n"
            "    return out"),
        "refinement": (
            "a counterpart that cleared each managed key UNCONDITIONALLY (without "
            "checking whether the overriding map supplies it) would drop a managed "
            "setting the overriding operation explicitly sets. The combined "
            "operation would lose a setting the override provides, where the test "
            "asserts the provided value survives. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from the (P-keep) guard of the post-image "
            "(`if keyPresent k newMap then rest else eraseKey k rest`): a tracked "
            "key the overriding map provides must be KEPT, but the "
            "unconditional-erase rival drops it. Refuted at base=[], "
            "new=[(\"a\",\"x\")], tracked=[\"a\"] — the overriding map PROVIDES a "
            "tracked key (this is the only reject witness where a tracked key is "
            "present in `newMap`, exercising the keep-guard binder)."
        ),
        "witness": _witness(
            'combineTrackedSettingsTester [] [("a", "x")] ["a"]'),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-drop-base-only-key",
        "kind": "uniqueness",
        "expect": "reject",
        # Keep ONLY the overriding map: every base-only key (managed OR not) is
        # dropped. Satisfies the clear behaviour vacuously but violates the
        # merge's base-inclusion for a NON-managed base-only key.
        "module": _impl(
            "    let out : SettingMap := newMap\n"
            "    return out"),
        "refinement": (
            "a counterpart that emitted only the overriding map's settings would "
            "drop every setting the base operation alone carried — including "
            "NON-managed ones outside the prescribed key set, which the pruning "
            "must never touch. The combined operation would lose a base-only "
            "non-managed setting the correct reduction keeps. It would NOT "
            "resolve."
        ),
        "rationale": (
            "REJECT from the (M) override-merge behaviour: `mergeMaps baseMap "
            "newMap` carries every base-only key through, and `pruneFold` only "
            "clears TRACKED keys — so a NON-tracked base-only key must survive, "
            "but the rival drops it. Refuted at base=[(\"o\",\"v\")], new=[], "
            "tracked=[\"a\"] — a non-tracked base-only key with an unrelated "
            "tracked list (attacks the base-inclusion clause the prune rivals do "
            "not)."
        ),
        "witness": _witness(
            'combineTrackedSettingsTester [("o", "v")] [] ["a"]'),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-override-precedence-inverted",
        "kind": "uniqueness",
        "expect": "reject",
        # Merge-precedence rival: build the merge with the arguments SWAPPED, so
        # the base map wins on a shared key instead of the overriding map.
        # Correct on every input with no shared key; diverges only on a shared
        # key with differing values.
        "module": _impl(
            "    let out : SettingMap := pruneFold newMap trackedKeys (mergeMaps newMap baseMap)\n"
            "    return out"),
        "refinement": (
            "a counterpart that merged with the precedence reversed (the base "
            "map's value winning on a shared setting) would emit the OLD value "
            "for any setting BOTH operations specify, where the test asserts the "
            "overriding operation's value. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from the (M) override-precedence behaviour: on a shared key "
            "`mergeMaps baseMap newMap` takes the overriding value, but the "
            "arg-swapped merge takes the base value. Refuted at "
            "base=[(\"a\",\"old\")], new=[(\"a\",\"new\")], tracked=[] — the two "
            "maps share a key with DIFFERENT values (the only witness with a "
            "value collision, isolating the precedence direction; tracked=[] so "
            "the prune is a no-op and the divergence is attributable to the "
            "merge)."
        ),
        "witness": _witness(
            'combineTrackedSettingsTester [("a", "old")] [("a", "new")] []'),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-guard-on-wrong-map",
        "kind": "uniqueness",
        "expect": "reject",
        # The guard's ARGUMENT, not its shape: prune with the keep-guard consulting
        # the BASE map instead of the overriding one. Structurally identical to the
        # post-image — same fold, same guard, same erase — so it is the closest
        # near-miss in the battery, and the only rival that gets the fold's SHAPE
        # right and its subject wrong. Diverges wherever a tracked key's presence
        # differs between the two maps.
        "module": _impl(
            "    let out : SettingMap := pruneFold baseMap trackedKeys"
            " (mergeMaps baseMap newMap)\n"
            "    return out"),
        "refinement": (
            "a counterpart that decided whether to clear each managed setting by "
            "asking the EXISTING settings rather than the overriding ones would "
            "clear precisely the wrong set: a managed setting the base carries is "
            "kept even when the override omits it (the very persistence the fix "
            "removes), and a managed setting only the override supplies is cleared. "
            "On the failing scenario it emits the stale managed setting, where the "
            "test asserts it is gone. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from the SUBJECT of the (P-keep) guard: the post-image's guard "
            "is `keyPresent k newMap` — presence in the OVERRIDING map — and a "
            "guard on `baseMap` satisfies neither (P-clear) nor (P-keep). Refuted "
            "at base=[(\"a\",\"v\"),(\"b\",\"w\")], new=[], tracked=[\"a\"] — a "
            "tracked key present in the base map and omitted by the override, "
            "where the base-guard KEEPS it and the post-image clears it. Closes "
            "the gap the other rivals leave: each of those changes the fold's "
            "SHAPE (drop it, truncate it, unconditionalise it), so none of them "
            "tests that the guard reads the right map."
        ),
        "witness": _witness(
            'combineTrackedSettingsTester [("a", "v"), ("b", "w")] [] ["a"]'),
        "witness_reference": _REFERENCE,
    },
    {
        "id": "weak-empty-result",
        "kind": "uniqueness",
        "expect": "reject",
        # The trivial too-weak baseline: always return the empty map. Meets the
        # post-image only when the correct combination is itself empty.
        "module": _impl(
            "    let out : SettingMap := []\n"
            "    return out"),
        "refinement": (
            "always emitting an empty settings map is what a counterpart that "
            "never populated the combined operation would do; it drops every "
            "setting for any non-empty combination, failing every test that "
            "asserts a surviving setting. It would NOT resolve. A cheap "
            "supporting near-miss with a genuine refinement."
        ),
        "rationale": (
            "REJECT from the (M) merge behaviour: for an input whose correct "
            "combination is non-empty the post-image demands those pairs, but the "
            "rival returns []. Verifying would be SPEC-TOO-WEAK. Refuted at "
            "base=[], new=[(\"a\",\"x\")], tracked=[] — a non-empty overriding map "
            "whose value must survive (tracked=[] so no pruning could excuse the "
            "loss)."
        ),
        "witness": _witness(
            'combineTrackedSettingsTester [] [("a", "x")] []'),
        "witness_reference": _REFERENCE,
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 7 SPEC cases (1 soundness
# positive, 1 admissibility, 5 uniqueness — one of which is the mandatory frame-
# mutation rival) plus 3 AXIOM_TESTS (dropped: axiom lane is G-AX's job). This
# bundle models only the purely-functional core — a single method
# `combineTrackedSettings` — where the sibling contracts one function
# `reduced_create_options` over TWO read-only mapping inputs carrying fractional
# heap permissions, with the clearing done by two guarded branches over a fixed
# two-element managed family {key_managed_a, key_managed_b}. This backend models
# the same combination DEEPLY over `List (String x String)` with the clearing as
# a backward per-key prune fold over a FREE `trackedKeys` list. The value surface
# carries across intact; the permission surface does not exist here, and the
# fixed two-key family generalises to a free tracked list.
#
#   sibling case                        -> here                          disposition
#   ---------------------------------------------------------------------------------
#   pos-control-reorder-clears          -> pos-control-direct            RE-SHAPED
#                                          (+ pos-control-let-merged ADDED)
#   admiss-f2p-shaped                   -> admiss-postimage-nondegenerate RE-AIMED
#   frame-mutation-write-op             -> (none)                        VACUOUS
#   weak-bare-merge-no-clear            -> weak-bare-merge-no-prune       PORTED
#   weak-forget-managed-b               -> weak-prune-only-head           PORTED
#   weak-overclear-provided-managed-a   -> weak-overclear-provided-key    PORTED
#   weak-clear-nonmanaged-other         -> weak-drop-base-only-key        PORTED
#   weak-empty-result                   -> weak-empty-result              PORTED
#   (no sibling)                        -> weak-override-precedence-inverted  ADDED
#   (no sibling)                        -> weak-guard-on-wrong-map        ADDED
#
# 5 ported, 1 re-shaped, 1 re-aimed, 1 vacuous; 1 positive control + 2 rivals
# added (merge-precedence, guard-subject).
#
# VACUOUS (frame-mutation-write-op): the sibling's MANDATORY frame-mutation rival
#   keeps the gold body verbatim then writes back into a read-only mapping input
#   granted only at half permission, and must be rejected for INSUFFICIENT
#   PERMISSION. This backend is referentially transparent: every parameter is an
#   immutable value, the method declares no `mut` binder, there is no heap and no
#   aliasing. There is no read-only input to overwrite and no permission system
#   to trip, so the class is vacuous. No substitute is fabricated.
# RE-AIMED (admiss-f2p-shaped -> admiss-postimage-nondegenerate): the sibling
#   confirms two half-permission preconditions admit an F2P-shaped input via a
#   self-call. This bundle's method has NO precondition, so that exact probe is
#   vacuous — but the LANE is not, and an earlier revision of this file dropped it
#   on precisely that reasoning, which was the wrong call. PRECOND-TOO-STRONG on a
#   total carrier means the obligation is unsatisfiable or degenerate at an
#   F2P-shaped input; that is one of the three directions this gate exists to
#   test, and neither of the other two lanes reaches it (a positive shows some
#   impl satisfies the spec, a reject witness shows some impl violates it, and
#   neither pins the post-image's VALUE where the fix lives). The re-aimed case
#   discharges that value by evaluation at a concrete F2P-shaped input as an
#   in-region assert, keeps the frozen impl verbatim, and adds only a `decide` arm
#   to the elided tactic body. Liveness measured both ways: a false first conjunct
#   fails (exit 1, `decide` proved the proposition false), and the frozen script
#   without the `decide` arm also fails (exit 1, unsolved `admiss_1` goal), so the
#   assert is neither unprovable-by-luck nor already-closed-by-loom_solve.
# RE-SHAPED (pos-control-reorder-clears -> pos-control-direct): the sibling's
#   positive control reorders the two commuting clearing branches. This backend's
#   frozen impl is a single loop over a free tracked list, so the sibling's exact
#   two-branch reorder does not exist. The reshape SPIRIT — "structurally
#   different, behaviourally identical" — is carried by pos-control-direct (drop
#   the loop, apply the pure combination) and pos-control-let-merged (name the
#   merge in a local first); both retune the elided tactic body to `loom_solve`.
# ADDED (weak-override-precedence-inverted): the sibling's merge soundness lives
#   in AXIOM_TESTS (dropped here), but the override-precedence behaviour is a
#   genuine independent clause of the modeled combination (`mergeMaps baseMap
#   newMap` takes the overriding value on a shared key). A rival that swaps the
#   merge arguments attacks exactly that clause; it is refuted at the only witness
#   with a shared-key value collision, which no ported rival exercises.
#
# DIVERGENCE / NON-TERMINATION - the class is CLOSED BY THE SEMANTICS here, and
#   a diverging rival is REJECTED rather than admitted. This bundle sets
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
#   NO reject case is shipped for it, and that is deliberate rather than a gap in
#   effort: a reject case must carry a witness that REFUTES the rival, and no
#   witness can exist for a rival the frozen spec SATISFIES. Shipping one would
#   require either a forged witness or a case that "rejects" for a tactic reason,
#   both of which are worse than the recorded hole. The defect is in the spec's
#   termination semantics, not in this battery, and it is not fixable inside the
#   G-PBT lane — hence recorded here and escalated there.
#
# ADDED (weak-guard-on-wrong-map): the six original rivals all attack the prune's
#   SHAPE — drop the fold, truncate it to the head, unconditionalise it, replace
#   the whole result — so none of them tests which map the keep-guard CONSULTS. A
#   rival that keeps the fold, the guard and the erase exactly as the post-image
#   has them and only swaps the guard's subject (`keyPresent k baseMap` for
#   `keyPresent k newMap`) is the closest near-miss available on this carrier, and
#   it is observably wrong: it keeps a stale tracked setting the override omits and
#   clears one only the override supplies. Refuted at a base-present /
#   override-omitted tracked key.
#
# BINDER / CLAUSE COVERAGE of the seven reject witnesses over the three input
#   binders of the sole ensures (pts = 7 distinct input points), plus the
#   admissibility positive's evaluated point:
#     baseMap      — nonempty (bare-merge, prune-only-head, drop-base-only,
#                    override-precedence, guard-on-wrong-map [TWO pairs]);
#                    empty (overclear, empty-result).
#     newMap       — empty (bare-merge, prune-only-head, drop-base-only,
#                    guard-on-wrong-map); nonempty (overclear [provides a tracked
#                    key], override-precedence [shares a key], empty-result).
#     trackedKeys  — ["k"] (bare-merge); ["a","b"] TWO keys, non-head probed
#                    (prune-only-head); ["a"] (overclear, drop-base-only,
#                    guard-on-wrong-map); [] (override-precedence, empty-result).
#                    Length and element position both varied.
#   Every independent behaviour of the post-image is attacked: the override-merge
#   base-inclusion (drop-base-only, empty-result), the override precedence
#   (override-precedence-inverted), the managed-key clear over the FULL list
#   (bare-merge, prune-only-head), the provided-key keep-guard (overclear), and
#   the guard's SUBJECT (guard-on-wrong-map). The admissibility case adds the one
#   point no rejection reaches: a tracked key REBOUND and another CLEARED in the
#   same call, with a non-tracked key surviving alongside.
#
# WITNESS SUBJECT (no sibling counterpart — this is the part of the port with no
#   nagini analogue). Nagini's reject cases need no witness: Viper discharges the
#   postcondition itself, so "did not verify" already means the contract fails.
#   On this tactic-proof backend that inference is invalid, and the frozen impl
#   additionally cannot serve as the witness's discriminating subject: its `while`
#   loop elaborates through `Classical.choice`, so `decide` against the frozen
#   tester is stuck for EVERY claim and the gold-side exit code carries no
#   information (`witness-undecided`). Because the loop IS the frozen impl, no
#   projection of the result avoids it. So all seven reject cases name a shared
#   `witness_reference` (_REFERENCE, also shipped as `pos-control-direct`): a
#   loop-free impl of the same frozen spec that the gate independently checks
#   shares the spec and VERIFIES. Each witness was confirmed out-of-band to
#   ELABORATE against its rival and to fail against _REFERENCE by a DECIDED
#   verdict (`Tactic `decide` proved that the proposition ... is false`), not by
#   stuck reduction — so every rejection is attributable to the spec.
#
# AXIOM_TESTS: dropped. The sibling's three probes (merge soundness, without_key
#   soundness, callee-domain containment) are the axiom lane's job (G-AX); this
#   bundle has no consumed axiom (the one deep-model reference `trackedKeys` is
#   validated by axiom_check.py), and this gate ignores AXIOM_TESTS regardless.
AXIOM_TESTS = []
