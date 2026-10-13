"""properties.py — G-PBT falsification battery for django__django-12325 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both regions the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct collectParentLinks`` obligation survives with a
byte-identical statement) and swaps in a candidate implementation; it is checked
by the real verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against a VERIFYING impl of the same spec — here an explicit
``witness_reference``, because the frozen ``while`` impl cannot decide anything;
see WHERE THE DISCRIMINATION ACTUALLY COMES FROM).

DEFENDED SURFACE (one contracted method):

  collectParentLinks (refs : List Ref) return (out : LinkMap)
    ensures ∀ k, out k = collectLinks refs k                       -- C1 (the pin)
    ensures ∀ k g, out k = some g → g.isLink = true                -- C2
    ensures ∀ k g, out k = some g → g.target = k ∧ g ∈ refs        -- C3

``Ref`` is one declared one-to-one reference a record makes to an ancestor:
``target`` is the ancestor's identity, ``isLink`` flags whether the reference is
explicitly the record's identity link to that ancestor, ``fid`` is the
reference's own identity (so two references to the same ancestor stay
distinguishable). ``LinkMap = Nat → Option Ref`` is the per-ancestor selection.
``selectRef``/``collectLinks`` are TRANSPARENT ``def``s over the method's own
input: ``selectRef`` folds one reference in — a non-link reference is dropped, an
explicit identity link is filed under its target, last-writer-wins — and
``collectLinks`` is the left-to-right fold of the whole list. There is NO opaque
answer-key oracle in any clause (the ``axioms`` region is empty), so pinning
``out k = collectLinks refs k`` is grounded in the argument, not an echo.

WHICH CLAUSE CONSTRAINS THE IMPL. C1 (``∀ k, out k = collectLinks refs k``) is
the whole functional pin: it fixes ``out`` at every key to the transparent fold,
so every selection decision (which references are dropped, which target each
kept reference is filed under, and which of several references to one ancestor
wins) is determined by it. C2 and C3 are CONSEQUENCES of C1 — they restate the
two structural facts ``collectLinks_props`` proves of the fold (a selected entry
is an explicit link; it is filed under exactly its target and is one of the
declared references). Because they follow from C1, a rival can only violate C2
or C3 by ALSO violating C1; every uniqueness rival is therefore a C1 divergence,
and each rival's rationale names in ADDITION the structural clause (C2 / C3) its
particular defect corresponds to, so all three top-level clauses are named by
some reject rationale.

ADVERSARIAL READ of the nagini classes on THIS carrier. The nagini sibling
models the same loop as a ``select_inheritance_links(is_parent_link, related_key)
-> Dict[int,int]`` over two parallel read-only lists; here the two lists are
fused into one ``List Ref`` (``is_parent_link[i] ↔ refs[i].isLink``,
``related_key[i] ↔ refs[i].target``, the dict key/value ↔ ``LinkMap``). The
nagini postcondition clauses map across as:
  * nagini clause (1) "every recorded position is a designated parent link
    targeting that key" ↔ C2 + C3 (``isLink = true`` and ``target = k``);
  * nagini clauses (3)+(4) "no parent link's key is lost, and the recorded
    position is the LAST parent-link position" ↔ C1 (the exact ``collectLinks``
    fold, which is last-writer-wins by construction).

  * FRAME/PERMISSION-MUTATION — VACUOUS. The nagini sibling carries TWO mandatory
    frame-mutation rivals (``frame-mutation-write-is_parent_link`` and
    ``frame-mutation-write-related_key``) that write through a read-only
    (``Acc(list_pred(.),1/2)``) reference to an input and are rejected for
    INSUFFICIENT PERMISSION. Lean and Velvet are referentially transparent:
    ``refs`` is an immutable value, this bundle declares NO ``mut`` parameter
    (the accumulator ``result`` is a fresh local), and there is no heap,
    aliasing, or permission system to subvert. There is no read-only input to
    overwrite, so the class is vacuous. No substitute probe is fabricated
    (reported in the footer, not faked).
  * UNGROUNDED-ORACLE ECHO — N/A as an attack. C1's post-image ``collectLinks
    refs`` is a transparent fold over the method's own argument; there is no
    answer key to echo. The honest cheapest CORRECT impl (``return collectLinks
    refs``) is carried as a POSITIVE control instead — it doubles as proof the
    spec is not echo-vulnerable, since any WRONG selection fails ``out k =
    collectLinks refs k`` at some key.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface, all against C1. A rival
    can be right on part of the domain and wrong on a sub-domain: record a
    non-link reference (wrong the instant a non-link reference exists — the
    pre-patch bug), record a non-link reference only when its target token is a
    fixed value (a value sub-domain a byte-fuzzer never reaches), skip the FIRST
    scanned reference (wrong only when the genuine link is declared first), keep
    the FIRST link per target instead of the LAST (wrong only when two links
    target one ancestor), or file a kept link under a fixed wrong key (a C3/key
    divergence).
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
    loop in the impl (1 loop here, measure ``refs.length - i``). A rival that
    loops without a measure is refused outright (``Decreasing annotations are
    required in total correctness semantics``), and a rival that supplies a
    CONSTANT measure to dodge that is refused on the measure's own goal (``case
    «decreasing_1: spin» ... ⊢ spin < spin``), re-measured on this bundle with
    a real build. Divergence therefore does not discharge the ``ensures``
    clauses vacuously. It is still not shipped as a G-PBT reject case, and the
    reason is the witness contract rather than a spec weakness. A reject case
    must carry a witness that ELABORATES against the rival, and neither diverging
    shape gets past that. With NO measure the descent obligation fails at the
    ``method`` itself, ahead of any appended tester, and the witness file retains
    the ``method`` (it strips only the ``prove_correct`` obligations), so the rival
    module does not compile at all. With a measure that does not decrease the
    refusal moves to the ``prove_correct`` site, which IS stripped, so that module
    does elaborate; but the rival's post-image is then an unreduced
    ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` / ``onDoneGadget`` /
    ``decreasingGadget``, which the kernel will not normalise to a value a
    concrete-input tester can decide. Either way the gate returns
    ``witness-unproven``, an inconclusive outcome. Measured through the
    gate's own ``_check_witness``, even ``example : True := trivial`` comes
    back ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome
    and would fail the whole battery rather than pass a case. That is the right
    behavior: a diverging impl has no output at any input, so there is no value
    for a witness to disagree with, and its rejection is a judgement of the
    termination obligation rather than a postcondition violation at a point.
    Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
    is neither a spec hole nor a battery gap.

WITNESS MECHANICS ON THIS BUNDLE. The output type ``LinkMap = Nat → Option Ref``
is a FUNCTION, and C1 is ``∀ k, out k = collectLinks refs k`` — a universal over
``Nat``, not a decidable proposition, so the Velvet tester path
(``prove_postcondition_decidable_for`` → ``derive_tester_for`` →
``collectParentLinksTester args = false := by decide``) is DEAD: the
postcondition's ``Decidable`` instance does not exist over a ``∀ (k : Nat)``.

But C1's carrier IS transparent, and it holds at EACH key. Each rival is written
LOOP-FREE, so its extracted program ``collectParentLinksExec`` — the
``NonDetT``-run of the impl — REDUCES fully under ``decide`` at a concrete input.
Each witness picks one concrete key ``k`` and, at one concrete ``refs``, states
the divergence with BOTH sides pinned BY VALUE:

    (match collectParentLinksExec <refs> with | DivM.res r => r k | _ => none)
        ≠ collectLinks <refs> k
    ∧ (match collectParentLinksExec <refs> with | DivM.res r => r k | _ => none)
        = <the rival's concrete selection at k>
    ∧ collectLinks <refs> k = <C1's concrete post-image at k>

i.e. the rival's own selection at key ``k`` DIFFERS from the transparent
post-image C1 demands there — a direct C1 violation the elaborator can see (C1
instantiated at that single ``k``, which suffices to refute the ``∀``).

WHERE THE DISCRIMINATION ACTUALLY COMES FROM: THE REFERENCE, NOT GOLD. Against
the FROZEN solution every one of these statements fails, and NOT for a semantic
reason — this must be stated precisely because the gate's own record is easy to
misread. Gold's body is the frozen ``while``; its extracted ``…Exec`` is the
loop's CCPO fixpoint, which the KERNEL cannot reduce at any input. Gold's build
fails with

    Tactic `decide` failed for proposition … because its `Decidable` instance
    instDecidableAnd did not reduce to `isTrue` or `isFalse`. After unfolding
    … reduction got stuck at the `Decidable` instance

i.e. a REDUCTION failure independent of what the statement says. Measured, not
argued: a claim that is TRUE of gold (``…Exec [] 0 = collectLinks [] 0``, zero
loop iterations) fails against gold with the same stuck-reduction error, exit 1.
So gold's exit code carries NO information about any claim, and a witness resting
on it alone would certify nothing.

That is exactly the condition ``gates/pbt.py::_STUCK_REDUCTION`` screens for, and
the gate does NOT accept the gold-side exit here: it detects the stuck reduction
and re-checks the witness against a VERIFYING impl of the same spec instead (its
``_check_witness`` fallback / an explicit ``witness_reference``). Each reject case
below therefore carries ``witness_reference = _REF_DIRECT``, the loop-free
``return collectLinks refs`` impl — spelled out rather than left to the fallback,
so the artifact says which impl the refutation was checked against instead of
requiring a reader to re-derive it. ``_REF_DIRECT`` is the same source as the
``pos-control-direct`` positive: it shares the frozen spec and independently
VERIFIES (measured exit 0), which is what makes refuting a witness against it
sound — an impl the verifier accepts cannot violate its own spec.

And on THAT subject the exit code tracks the claim, which is the property the
gold side lacks. Measured per reject case (attack B′, the forgery pair): the
shipped witness fails against the reference with

    Tactic `decide` proved that the proposition … is false

— a semantic refutation, the kernel having evaluated both sides — while the SAME
file with the claim FLIPPED (``≠`` replaced by ``=``, i.e. asserting the impl
AGREES with C1 at that key) ELABORATES against the reference, exit 0, no error.
Two different claims, two different exit codes: the channel carries information.
Against gold both the witness and its flipped form fail with the byte-identical
stuck-reduction error, which is the contrast that proves the gold channel dead
and the reference channel live.

WHY BOTH VALUES ARE PINNED. Naming ``rival_val`` and ``spec_val`` alongside the
disequality makes the statement FALSE of any impl agreeing with ``collectLinks``
at that key, so it can only elaborate where the rival genuinely diverges. This is
load-bearing independently of the subject question: the bare ``≠``-only shape
would let a point where the rival and the spec AGREE pass as a refutation. Under
the pinned shape such a point fails on the RIVAL side (measured: a bare ``≠`` at
key 99, where the rival and the post-image both give ``none``, is refuted against
the rival itself — ``decide`` proves it false, exit 1), and ``_witness``
additionally refuses at load time to build a witness whose two values agree.

Measured for all five rivals with ``scripts/lean_verify.sh``: witness vs rival
exit 0; witness vs reference exit 1 by evaluation; flipped claim vs reference
exit 0. No witness binds a hypothesis — every input is a concrete literal that
decides C1 at the chosen key — so no consistency probe is needed. No banned token
(sorry/admit/native_decide/axiom/opaque).

AXIOM lane: dropped. ``AXIOM_TESTS = []``. This bundle declares no ``axiom``
(mapping.md §3: no consumed axiom, no deep-model reference — the layout facts
the direct model rests on are validated executably by G-AX, not here), and the
G-PBT gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "django__django-12325"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors (each lies wholly inside the one -- impl-start ..
# ---- -- impl-end region and is unique in Solution.lean; both facts asserted at
# ---- load by _swap, so every edit keeps same_spec by construction) ----

# The single loop-body step: reshaped by the loop-preserving positive control.
_BODY = (
    "      let f := refs[i]!\n"
    "      result := selectRef result f\n"
    "      i := i + 1"
)

# The WHOLE executable body: the accumulator `while` loop that folds `selectRef`
# over the reference list. Reshaped wholesale by the uniqueness rivals and the
# direct positive, which are written STRAIGHT-LINE (see WITNESS MECHANICS): the
# frozen `while` elaborates to well-founded recursion the kernel does not reduce,
# so a rival that KEPT the loop would have an `…Exec` as stuck as the frozen one
# and no witness could `decide` it. A loop-free rival's `…Exec` reduces.
_IMPL = (
    "    let mut result : LinkMap := (fun _ => none)\n"
    "    let mut i := 0\n"
    "    while i < refs.length\n"
    "      invariant i ≤ refs.length\n"
    "      invariant result = (refs.take i).foldl selectRef (fun _ => none)\n"
    "      done_with i = refs.length\n"
    "      decreasing refs.length - i\n"
    "    do\n"
    "      let f := refs[i]!\n"
    "      result := selectRef result f\n"
    "      i := i + 1\n"
    "    return result"
)

# The frozen proof, verbatim. A loop-free reshape (the direct positive) retunes
# THIS block (elided from the spec view); loop-keeping variants leave it as-is.
# Rivals leave it as-is too — the rejection is carried by the witness, not the
# tactic script.
_PROOF = (
    "prove_correct collectParentLinks by\n"
    "  loom_solve\n"
    "  case «invariant_2: result = (refs.take i).foldl selectRef (fun _ => none)» =>\n"
    "    have hi : i < refs.length := by omega\n"
    "    rw [invariant_2, collectLinks_take_step refs i hi]\n"
    "  case «ensures_2: ∀ k g, out k = some g → g.isLink = true» =>\n"
    "    intro k g h\n"
    "    cases i_2\n"
    "    have hlen : i = refs.length := by omega\n"
    "    rw [invariant_2, hlen, List.take_length] at h\n"
    "    exact (collectLinks_props refs k g h).1\n"
    "  case «ensures_1: ∀ k g, out k = some g → g.target = k ∧ g ∈ refs» =>\n"
    "    intro k g h\n"
    "    cases i_2\n"
    "    have hlen : i = refs.length := by omega\n"
    "    rw [invariant_2, hlen, List.take_length] at h\n"
    "    exact (collectLinks_props refs k g h).2\n"
    "  all_goals simp_all [collectLinks]"
)

for _a in (_BODY, _IMPL, _PROOF):
    assert _BASE.count(_a) == 1, f"anchor drifted: {_a!r}"


def _rival(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced (loop-free)."""
    return _swap(_BASE, _IMPL, new_body)


# The loop-free proof the direct return needs: with the `while` gone there is no
# `invariant_2` case tag, and C1 closes per key by `rfl`.
_PROOF_DIRECT = (
    "prove_correct collectParentLinks by\n"
    "  loom_solve\n"
    "  case «ensures_2: ∀ k g, out k = some g → g.isLink = true» =>\n"
    "    intro k g h\n"
    "    exact (collectLinks_props refs k g h).1\n"
    "  case «ensures_1: ∀ k g, out k = some g → g.target = k ∧ g ∈ refs» =>\n"
    "    intro k g h\n"
    "    exact (collectLinks_props refs k g h).2\n"
    "  all_goals (intro k; rfl)")

# ---- THE WITNESS SUBJECT (`witness_reference` on every reject case).
#
# `return collectLinks refs` — a CORRECT, spec-sharing, loop-free impl. Two
# properties make it the right subject for the gold-side half of the
# discrimination check, and both are machine-checked rather than assumed:
#
#   * it VERIFIES against the frozen spec (measured exit 0; the gate re-checks
#     this itself via `_reference_ok` and rejects the case if it ever stops
#     holding), so it cannot violate its own spec and a genuine "the spec is
#     violated at this input" claim MUST fail against it;
#   * its `…Exec` REDUCES in the kernel, so `decide` reaches a verdict and the
#     exit code tracks what the statement says — which gold's, being the `while`'s
#     unreducible CCPO fixpoint, does not.
#
# Same source as the `pos-control-direct` positive, deliberately: that case's
# independent `expect="verify"` outcome is the artifact's own record that this
# subject satisfies the spec.
_REF_DIRECT = _swap(_rival("    return (collectLinks refs)"), _PROOF, _PROOF_DIRECT)

# ---- ADMISSIBILITY probe, prefixed to the frozen impl (inside the impl region,
# ---- so `same_spec` holds and the frozen obligation survives verbatim).
#
# Discharges the three-clause post-image BY EVALUATION at concrete F2P-shaped
# inputs, as a `have`, BEFORE the frozen obligation is closed unchanged. See the
# `admiss-f2p-nondegenerate` case for what each conjunct buys.
_ADMISS_HAVE = (
    "    have hadm :\n"
    "        collectLinks [{ target := 0, isLink := false, fid := 0 },\n"
    "                      { target := 0, isLink := true, fid := 1 }] 0\n"
    "            = some { target := 0, isLink := true, fid := 1 }\n"
    "          ∧ collectLinks [{ target := 0, isLink := true, fid := 1 },\n"
    "                          { target := 0, isLink := false, fid := 0 }] 0\n"
    "            = some { target := 0, isLink := true, fid := 1 }\n"
    "          ∧ collectLinks [{ target := 0, isLink := false, fid := 0 }] 0"
    " = none := by\n"
    "      decide\n")


# ---- witness preamble + builder. C1 is `∀ k, out k = collectLinks refs k`, not
# ---- decidable (the output is a FUNCTION), so the tester+`decide` path is dead;
# ---- instead extract the executable program and refute C1 at ONE concrete key
# ---- against the TRANSPARENT `collectLinks`. Checked in a file whose
# ---- `prove_correct` block is stripped, so no tactic script can mask the
# ---- verdict.
#
# TWO INDEPENDENT THINGS MAKE THESE WITNESSES DISCRIMINATE. Both were measured;
# see the docstring section "WHERE THE DISCRIMINATION ACTUALLY COMES FROM".
#
# (1) THE SUBJECT. The bare shape
#
#     (match collectParentLinksExec <refs> with | DivM.res r => r k | _ => none)
#         ≠ collectLinks <refs> k
#
# cannot be judged against GOLD at all. Gold's `…Exec` is the frozen `while`'s
# CCPO fixpoint, which the kernel cannot reduce at ANY input, so gold's build
# fails with `Tactic `decide` failed … reduction got stuck at the `Decidable`
# instance` no matter what the statement says. Measured: a claim TRUE of gold
# (`…Exec [] 0 = collectLinks [] 0`, zero iterations) fails identically, exit 1.
# `gates/pbt.py::_STUCK_REDUCTION` screens precisely this and refuses to read
# gold's exit code as a refutation; each reject case therefore names
# `witness_reference = _REF_DIRECT`, a loop-free VERIFYING impl of the same spec
# whose `…Exec` does reduce. Against that subject the exit code tracks the claim:
# the witness is refuted by evaluation (`decide` proved the proposition false)
# while the same file with the claim FLIPPED elaborates, exit 0.
#
# (2) THE PINNED VALUES. Independently of the subject, the bare `≠`-only shape
# would let a point where the rival AGREES with the spec read as a refutation. So
# the refutation names the two CONCRETE values — `rival_val` (what the rival's own
# `…Exec` returns at that key) and `spec_val` (what C1's transparent post-image
# demands there) — alongside the disequality. The statement is then FALSE of any
# impl agreeing with `collectLinks` at that key, so it can only elaborate where
# the rival genuinely diverges: measured, a bare `≠` at key 99 (rival and
# post-image both `none`, no clause violated) is refuted against the RIVAL
# itself, exit 1. `_witness` also refuses at load time to build a witness whose
# two values agree, so a future edit cannot silently reintroduce such a point.
_EXTRACT = "extract_program_for collectParentLinks\n\n"


def _witness(refs, key, rival_val, spec_val):
    """Refutation at ONE concrete key, pinning BOTH sides by value.

    `rival_val` is the rival's selection at `key`; `spec_val` is C1's post-image
    (`collectLinks refs key`) there. They MUST differ — that difference is the
    C1 violation — and naming them is what stops a stuck-reduction pass on gold
    from certifying a statement that discriminates nothing.
    """
    if rival_val == spec_val:
        raise AssertionError(
            f"witness does not discriminate at key {key}: rival and spec agree "
            f"({rival_val!r}) — no C1 divergence to refute")
    exec_at = (f"(match collectParentLinksExec ({refs}) with "
               f"| DivM.res r => r {key} | _ => none)")
    return (
        _EXTRACT +
        "example :\n"
        f"    {exec_at}\n"
        f"      ≠ collectLinks ({refs}) {key}\n"
        f"    ∧ {exec_at}\n"
        f"        = {rival_val}\n"
        f"    ∧ collectLinks ({refs}) {key} = {spec_val} := by\n"
        "  decide\n"
    )


# A single `Ref` literal, spelled inline in each witness/rival.
def _ref(target, is_link, fid):
    return ("{ target := %d, isLink := %s, fid := %d }"
            % (target, "true" if is_link else "false", fid))


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-control-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: report the whole selection DIRECTLY via the transparent fold,
        # no per-reference loop. C1 is literally `out k = collectLinks refs k`,
        # so this is the cheapest HONEST correct impl — and, since `collectLinks
        # refs` is GROUNDED in the argument (not an opaque answer key), it doubles
        # as proof the spec is not echo-vulnerable (any WRONG selection fails
        # `out k = collectLinks refs k` at some key). The loop is gone, so the
        # frozen proof's invariant/step case no longer applies; the residual
        # `∀ k, out k = collectLinks refs k` closes by `rfl` per key and C2/C3
        # close from `collectLinks_props` exactly as in the frozen proof.
        # Same source as `_REF_DIRECT`, the subject every reject case refutes its
        # witness against — so this case's independent verify outcome IS the
        # artifact's record that that subject satisfies the frozen spec.
        "module": _REF_DIRECT,
        "rationale": (
            "the post-image `collectLinks refs` is GROUNDED in the input (a total "
            "left-fold over the argument, no opaque answer key), so `return "
            "collectLinks refs` is the honest cheapest CORRECT impl; C1 is "
            "literally `out k = collectLinks refs k`, so it MUST verify, else C1 "
            "is SPEC-TOO-STRONG. Re-expresses the nagini positive controls' "
            "argument (a structurally-different correct impl records exactly the "
            "designated links) as a loop-free direct return, and doubles as the "
            "echo-non-vulnerability control (any wrong selection fails C1)."
        ),
    },
    {
        "id": "pos-control-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: keep the frozen backward-`while` fold but bind the stepped
        # selection to a typed local before assigning it. Same value flow
        # (`stepped = selectRef result f`), different control shape; the frozen
        # proof still closes unchanged (the loop invariant and step lemma are
        # untouched). Ports the nagini pos-control-local-reshape (read the flag/key
        # into a local before recording).
        "module": _swap(
            _BASE, _BODY,
            "      let f := refs[i]!\n"
            "      let stepped := selectRef result f\n"
            "      result := stepped\n"
            "      i := i + 1"),
        "rationale": (
            "a correct impl with a DIFFERENT control shape (bind the stepped "
            "per-reference selection to a typed local before assigning it) must "
            "verify; the value flow is unchanged (`stepped = selectRef result f`) "
            "so the loop invariant `result = (refs.take i).foldl selectRef …` and "
            "C1/C2/C3 still discharge and the frozen loop proof closes as-is. "
            "Ports nagini pos-control-local-reshape: if it fails => "
            "SPEC-TOO-STRONG (over-fit to the inline-assign code form)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from nagini admiss-selfcall. That case established
    # the read-only fractional-permission precondition `Acc(.,1/2)` on an
    # F2P-shaped input (a designated parent link + an ordinary reference to the
    # same ancestor). This method carries NO `require` clause (the pre-conditions
    # region is empty), so nothing can exclude a normal input and the classic
    # "a normal input is admitted" probe has no content.
    #
    # The analogue on a TOTAL carrier is the obligation being unsatisfiable — or,
    # worse, DEGENERATE — at exactly an F2P-shaped input, which a positive that
    # discharges the obligation AT that concrete input tests directly. So the
    # probe is an in-region `have`, closed BY EVALUATION at concrete inputs,
    # before the frozen obligation is closed verbatim.
    #
    # (An earlier revision of this battery filled this lane with `module = _BASE`
    # — the frozen file, byte-identical. That case is a no-op: it re-runs the
    # frozen bundle and can only fail if the frozen bundle itself fails, so it
    # probes nothing about the post-image at any particular input. Replaced.)
    # =====================================================================
    {
        "id": "admiss-f2p-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        # Frozen impl and frozen proof BOTH verbatim; the `have` is prefixed
        # inside the impl region, so the obligation is reproven unchanged and the
        # probe is pure addition.
        "module": _swap(_BASE, _IMPL, _ADMISS_HAVE + _IMPL),
        "rationale": (
            "PRECOND-TOO-STRONG lane, re-aimed for a carrier with no `require`: "
            "the post-image must be SATISFIABLE and NON-DEGENERATE at the "
            "F2P-shaped input — an ancestor referenced BOTH by an explicit "
            "identity link and by an ordinary one-to-one reference. The three "
            "conjuncts are discharged by evaluation in-region before the frozen "
            "obligation is closed verbatim: (a) with the ordinary reference "
            "declared FIRST, C1's post-image at that ancestor is the identity "
            "link, not the ordinary reference; (b) with the two declared in the "
            "OPPOSITE order it is still the identity link — so the clause pins the "
            "explicit link regardless of declaration order, which is the property "
            "the failing scenario turns on and is NOT implied by (a) alone; (c) at "
            "the ordinary reference ALONE the post-image is `none`, so the clause "
            "is not degenerately satisfied by selecting everything. If any "
            "conjunct failed to evaluate, or the case failed to verify, the "
            "obligation would be unsatisfiable or vacuous exactly where it must "
            "bite. Re-aimed from nagini admiss-selfcall, whose read-only "
            "fractional-permission half has no counterpart on this "
            "referentially-transparent carrier."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real patch
    # would NOT resolve the F2P. All attack C1 (`out k = collectLinks refs k`);
    # the input binder `refs` is varied across the reject witnesses (a non-link
    # reference, a value sub-domain, a leading link, two links to one ancestor,
    # a mis-keyed link), and the two structural clauses C2/C3 are each named.
    # =====================================================================
    {
        "id": "weak-no-filter-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        # The PRE-PATCH behaviour: fold EVERY reference into the selection with no
        # `isLink` filter, last-writer-wins. An ordinary (non-link) reference to
        # an ancestor is then recorded as that ancestor's identity link.
        "module": _rival(
            "    return (refs.foldl (fun m f =>\n"
            "        (fun k => if k = f.target then some f else m k))"
            " (fun _ => none))"),
        "refinement": (
            "this is the pre-change behaviour verbatim: every scanned one-to-one "
            "reference is filed under its ancestor with no identity-link filter, "
            "last-writer-wins. An ordinary reference that targets an ancestor then "
            "displaces / stands in for the genuine identity link, so the "
            "downstream selection promotes a non-link field and the record raises "
            "the misconfiguration error the fix removes — the exact defect. Its "
            "faithful real patch is the unpatched repo, which does NOT resolve the "
            "F2P (test_onetoone_with_parent_model asserts an ordinary reference to "
            "the ancestor is NOT treated as the identity link)."
        ),
        "rationale": (
            "REJECT from C1 (`out k = collectLinks refs k`): `collectLinks` drops "
            "non-link references (`selectRef` ignores `isLink = false`), so at the "
            "key of a recorded non-link reference the rival returns `some f` where "
            "C1 demands `none`. This ALSO violates C2 (`isLink = true` for every "
            "selected entry). Refuted at `refs = [Ref 3 false 0]`, key 3, where "
            "the rival selects the non-link reference and gold selects nothing. "
            "If it verified => SPEC-TOO-WEAK (admits the pre-patch bug)."
        ),
        "witness": _witness("[" + _ref(3, False, 0) + "]", "3",
                            "some " + _ref(3, False, 0), "none"),
        "witness_reference": _REF_DIRECT,
    },
    {
        "id": "weak-record-nonlink-on-target0",
        "kind": "uniqueness",
        "expect": "reject",
        # Value-partial-domain: filter correctly (keep only links) EXCEPT that a
        # non-link reference is ALSO recorded whenever its target token is 0. On
        # that sub-domain a non-link reference is selected as the identity link.
        "module": _rival(
            "    return (refs.foldl (fun m f =>\n"
            "        if f.isLink || f.target = 0 then\n"
            "          (fun k => if k = f.target then some f else m k)\n"
            "        else m) (fun _ => none))"),
        "refinement": (
            "records an ordinary (non-link) reference whenever it targets one "
            "particular ancestor (target token 0). For that ancestor the "
            "downstream selection promotes a non-link field and the record raises "
            "the misconfiguration error; the F2P assertion that ordinary "
            "references to that ancestor are not promoted fails on that "
            "sub-domain. A faithful patch of this shape (special-casing one target "
            "identity) would NOT resolve. A value-partial-domain break — correct "
            "on every non-zero target, invisible to a byte-fuzzer."
        ),
        "rationale": (
            "REJECT from C1 (`out k = collectLinks refs k`): on the value "
            "sub-domain `target = 0` the rival selects a non-link reference where "
            "`collectLinks` selects nothing, so C1 fails at key 0. Also violates "
            "C2 (the selected entry has `isLink = false`). Refuted at `refs = "
            "[Ref 0 false 0]`, key 0 — a DISTINCT point from weak-no-filter "
            "(target 0 vs 3), so the `refs` binder is varied. If it verified => "
            "SPEC-TOO-WEAK (value-partial-domain)."
        ),
        "witness": _witness("[" + _ref(0, False, 0) + "]", "0",
                            "some " + _ref(0, False, 0), "none"),
        "witness_reference": _REF_DIRECT,
    },
    {
        "id": "weak-skip-first-reference",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: apply the identity-link filter correctly to every
        # reference EXCEPT the first scanned one, which is never folded in. When a
        # genuine identity link is declared first, its ancestor gets no entry.
        "module": _rival(
            "    match refs with\n"
            "    | [] => return (fun _ => none)\n"
            "    | _ :: rest => return (rest.foldl selectRef (fun _ => none))"),
        "refinement": (
            "never records the FIRST scanned reference (correct filter on the "
            "rest). When the genuine identity link is the first declared reference "
            "— the ordering the issue reports as the failing one — its ancestor "
            "has no selected link, the downstream selection synthesizes an "
            "auto-created link instead of reusing the declared one, and pk setup "
            "for the record diverges from the patched repo. A faithful patch that "
            "skipped the first scanned field would NOT resolve (the shipped F2P "
            "scenarios declare the explicit link as a scanned field that can be "
            "first)."
        ),
        "rationale": (
            "REJECT from C1 (`out k = collectLinks refs k`): C1 pins the WHOLE "
            "fold including index 0, so dropping the first reference loses its "
            "selection — at the key of a leading identity link the rival returns "
            "`none` where `collectLinks` returns `some f`. Refuted at `refs = "
            "[Ref 0 true 5]`, key 0 (a single leading link), a DISTINCT point "
            "(a link, not a non-link) from the two rivals above. If it verified "
            "=> SPEC-TOO-WEAK (domain-incomplete on the first element)."
        ),
        "witness": _witness("[" + _ref(0, True, 5) + "]", "0",
                            "none", "some " + _ref(0, True, 5)),
        "witness_reference": _REF_DIRECT,
    },
    {
        "id": "weak-first-writer-wins",
        "kind": "uniqueness",
        "expect": "reject",
        # First-writer-wins: record an identity link only if its target is not
        # already selected, so the FIRST link per ancestor wins instead of the
        # LAST. C2 and C3 still hold (every selected entry is a link filed under
        # its own target), so this slipped past a weaker spec; C1's last-writer-
        # wins fold is violated when two links target the same ancestor.
        "module": _rival(
            "    return (refs.foldl (fun m f =>\n"
            "        if f.isLink && (m f.target).isNone then\n"
            "          (fun k => if k = f.target then some f else m k)\n"
            "        else m) (fun _ => none))"),
        "refinement": (
            "keeps the FIRST identity link per ancestor and ignores later ones, "
            "instead of the repo's last-assignment-wins dict semantics. When two "
            "identity links target the same ancestor, the downstream selection "
            "holds a DIFFERENT field object than the patched repo does (the first, "
            "not the last), so pk promotion / field identity downstream diverges "
            "from the gold patch and the record is set up against the wrong field. "
            "Does not refine the patched behaviour — a verify-not-resolve break."
        ),
        "rationale": (
            "REJECT from C1 (`out k = collectLinks refs k`): `collectLinks` is the "
            "left-fold whose `selectRef` OVERWRITES on a repeated target "
            "(last-writer-wins), so at an ancestor with two links C1 demands the "
            "LATER reference; the rival returns the earlier one. C2 and C3 still "
            "hold for this rival (it is exactly the weakness class a pin lacking "
            "the last-writer-wins fold would admit), so ONLY C1 refutes it. "
            "Refuted at `refs = [Ref 0 true 0, Ref 0 true 1]`, key 0 — a "
            "two-reference input no other witness uses, varying `refs`. If it "
            "verified => SPEC-TOO-WEAK (tie-breaking / which-reference pinning)."
        ),
        "witness": _witness(
            "[" + _ref(0, True, 0) + ", " + _ref(0, True, 1) + "]", "0",
            "some " + _ref(0, True, 0), "some " + _ref(0, True, 1)),
        "witness_reference": _REF_DIRECT,
    },
    {
        "id": "weak-wrong-key",
        "kind": "uniqueness",
        "expect": "reject",
        # File every kept identity link under the fixed key 0 regardless of its
        # target. Keeps the filter (only links recorded) but breaks the per-target
        # keying: a link to a non-zero ancestor is recorded under key 0.
        # Directly attacks C3's `g.target = k` (filed under exactly its target).
        "module": _rival(
            "    return (refs.foldl (fun m f =>\n"
            "        if f.isLink then\n"
            "          (fun k => if k = 0 then some f else m k)\n"
            "        else m) (fun _ => none))"),
        "refinement": (
            "files every identity link under one fixed ancestor identity instead "
            "of the ancestor it actually references. The downstream selection "
            "keys the record's parents by the real referenced ancestor, so a link "
            "filed under the wrong identity is looked up under the right one and "
            "found absent — the identity link is effectively lost and an "
            "auto-created link is synthesized instead. A faithful patch keying by "
            "a bogus constant identity would NOT resolve."
        ),
        "rationale": (
            "REJECT from C1 (`out k = collectLinks refs k`): `collectLinks` files "
            "each link under its own `target`, so for a link to ancestor 7 the "
            "rival returns `none` at key 7 (it filed the link under 0) where C1 "
            "demands `some f`. This is precisely a C3 violation (`g.target = k` — "
            "filed under exactly its target). Refuted at `refs = [Ref 7 true 0]`, "
            "key 0, where the rival wrongly returns `some f` and gold returns "
            "`none` — a key-divergence point distinct from every other witness. "
            "If it verified => SPEC-TOO-WEAK (per-target keying)."
        ),
        "witness": _witness("[" + _ref(7, True, 0) + "]", "0",
                            "some " + _ref(7, True, 0), "none"),
        "witness_reference": _REF_DIRECT,
    },
]


# ===========================================================================
# NAGINI → VELVET ACCOUNTING.
#
#   nagini case                        -> here
#   -----------------------------------------------------------------------
#   pos-control-local-reshape          -> pos-control-local-reshape   PORTED
#   pos-control-branch-reorder         -> pos-control-direct          RE-EXPRESSED
#   admiss-selfcall                    -> admiss-f2p-nondegenerate    RE-AIMED
#   frame-mutation-write-is_parent_link-> (none)                      VACUOUS
#   frame-mutation-write-related_key   -> (none)                      VACUOUS
#   weak-no-filter-prepatch            -> weak-no-filter-prepatch     PORTED
#   weak-record-nonparent-on-key0      -> weak-record-nonlink-on-target0  PORTED
#   weak-skip-first-relation           -> weak-skip-first-reference   PORTED
#   weak-first-writer-wins             -> weak-first-writer-wins      PORTED
#   (no sibling)                       -> weak-wrong-key              ADDED
#   AXIOM_TESTS ([])                   -> (none)                      DROPPED (G-AX lane)
#
# 8 velvet SPEC cases: 2 soundness, 1 admissibility, 5 uniqueness. Every nagini
# uniqueness rival that attacks a modeled clause is ported; one rival is added to
# complete C3 (per-target keying) coverage.
#
# PORTED (5): pos-control-local-reshape (read the stepped value into a local
#   before assigning — the nagini local-variable reshape), and the four
#   uniqueness rivals. Each nagini rival's ARGUMENT is carried over verbatim in
#   spirit; the mechanics are re-expressed over this carrier (one `List Ref` and
#   the `selectRef`/`collectLinks` fold) rather than the sibling's two parallel
#   `List[bool]`/`List[int]` lists, and each reject case gains a machine-checked
#   refutation witness with no sibling counterpart (Viper discharges the nagini
#   postcondition; a tactic-proof backend needs the witness to attribute the
#   rejection to the spec, not to frozen-tactic breakage).
#     * weak-no-filter-prepatch: the pre-patch no-filter loop (nagini clause (1)
#       ↔ C2/C1).
#     * weak-record-nonlink-on-target0: nagini weak-record-nonparent-on-key0, the
#       value-partial-domain rival that records a non-link reference on the target
#       sub-domain (nagini related_key == 0 ↔ Ref.target = 0).
#     * weak-skip-first-reference: nagini weak-skip-first-relation, the leading-
#       element partial-domain rival (nagini clause (3) ↔ C1 at index 0).
#     * weak-first-writer-wins: nagini weak-first-writer-wins, the tie-break rival
#       that keeps the first link per ancestor instead of the last (nagini clause
#       (4) ↔ C1's last-writer-wins fold). C2/C3 still hold for it, so only C1
#       refutes it — exactly the G-PANEL-1 weakness class the nagini file flags.
# RE-EXPRESSED (pos-control-branch-reorder -> pos-control-direct): the nagini
#   branch-reorder positive negates the eligibility test and records in the else.
#   On this carrier the per-reference eligibility is the pure `selectRef` filter
#   (a `def`, not an inline if/else in the impl region), so there is no impl-region
#   branch to reorder; the structurally-different correct control here is the
#   loop-free direct return `return collectLinks refs`, which also serves as the
#   echo-non-vulnerability control (C1's post-image is grounded, so no wrong echo
#   verifies).
# RE-AIMED (admiss-selfcall -> admiss-f2p-nondegenerate): the nagini case
#   established the read-only fractional-permission precondition on an F2P-shaped
#   self-call. This method has no `require` and no heap permission, so that probe
#   is vacuous; re-aimed at the total-carrier analogue — the obligation being
#   unsatisfiable or DEGENERATE at exactly an F2P-shaped input. The case discharges
#   the post-image by EVALUATION at that input (an ancestor referenced both by an
#   explicit identity link and by an ordinary reference, in BOTH declaration
#   orders, plus the ordinary reference alone giving `none`) as an in-region
#   `have`, before closing the frozen obligation verbatim.
#     AUDIT NOTE: this lane previously held `admiss-gold-total`, whose `module` was
#     `_BASE` — the frozen file byte-identical. That is a no-op: it re-runs the
#     frozen bundle, so it can only fail if the frozen bundle fails, and it probes
#     nothing about the post-image at any input. Replaced with the evaluated probe
#     above, which fails if the clause is unsatisfiable or degenerate there.
# ADDED (1): weak-wrong-key files every kept link under a fixed key 0 regardless
#   of its target, a direct C3 (`g.target = k`) divergence. The nagini file's
#   clause (1) "targeting that key" is defended implicitly by its dict semantics;
#   here it is a concrete witnessable C1/C3 divergence at `[Ref 7 true 0]`, key 0,
#   completing coverage of the per-target keying dimension. A real divergence with
#   a machine-checked witness, not fabricated wrongness.
# VACUOUS (2): the nagini sibling's TWO mandatory frame-mutation rivals
#   (write is_parent_link, write related_key) overwrite a read-only input through
#   a fractional heap permission and are rejected for INSUFFICIENT PERMISSION.
#   This backend is referentially transparent, this bundle declares no `mut`
#   binder on any input (the accumulator is a fresh local), and there is no heap
#   or aliasing — so there is no read-only input to overwrite and no substitute
#   probe. Reported, not fabricated.
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
#   loop in the impl (1 loop here, measure ``refs.length - i``). A rival that
#   loops without a measure is refused outright (``Decreasing annotations are
#   required in total correctness semantics``), and a rival that supplies a
#   CONSTANT measure to dodge that is refused on the measure's own goal (``case
#   «decreasing_1: spin» ... ⊢ spin < spin``), re-measured on this bundle with
#   a real build. Divergence therefore does not discharge the ``ensures``
#   clauses vacuously. It is still not shipped as a G-PBT reject case, and the
#   reason is the witness contract rather than a spec weakness. A reject case
#   must carry a witness that ELABORATES against the rival, and neither diverging
#   shape gets past that. With NO measure the descent obligation fails at the
#   ``method`` itself, ahead of any appended tester, and the witness file retains
#   the ``method`` (it strips only the ``prove_correct`` obligations), so the rival
#   module does not compile at all. With a measure that does not decrease the
#   refusal moves to the ``prove_correct`` site, which IS stripped, so that module
#   does elaborate; but the rival's post-image is then an unreduced
#   ``forIn Lean.Loop.mk`` term carrying ``invariantGadget`` / ``onDoneGadget`` /
#   ``decreasingGadget``, which the kernel will not normalise to a value a
#   concrete-input tester can decide. Either way the gate returns
#   ``witness-unproven``, an inconclusive outcome. Measured through the
#   gate's own ``_check_witness``, even ``example : True := trivial`` comes
#   back ``witness-unproven`` on this rival, which is an INCONCLUSIVE outcome
#   and would fail the whole battery rather than pass a case. That is the right
#   behavior: a diverging impl has no output at any input, so there is no value
#   for a witness to disagree with, and its rejection is a judgement of the
#   termination obligation rather than a postcondition violation at a point.
#   Recorded as REJECTED-BY-SPEC and not expressible as a witnessed case, which
#   is neither a spec hole nor a battery gap.
# INDEPENDENT AUDIT PROBES (run against the frozen spec, none shipped as a case;
#   recorded so the next reader need not re-spend the builds). Exit codes are from
#   scripts/lean_verify.sh on this bundle.
#   SPEC-TOO-WEAK probes — NEW wrong impls the battery does not contain, each aimed
#   where the shipped rivals leave off. ALL were REJECTED (exit 1), so no spec hole
#   was found in this direction:
#     * strip a kept link's own identity (`{ f with fid := 0 }`) — attacks `g ∈ refs`
#       in C3, a dimension no shipped rival touches (every shipped rival keeps or
#       drops whole `Ref`s, never forges one). Failure is SEMANTIC: `unsolved goals`
#       on the `ensures_1` (`g.target = k ∧ g ∈ refs`) case;
#     * a correct fold PLUS a spurious entry at an unreferenced key (999) — attacks
#       C3's `g ∈ refs` from the other side, an entry with no declaring reference.
#       Also `unsolved goals` on `ensures_1`;
#     * file each kept link one key ABOVE its target (`f.target + 1`) — a keying
#       divergence distinct from the shipped fixed-key rival;
#     * drop a link on a per-reference sub-domain (`f.fid != 1`) — a fid-valued
#       sub-domain no shipped witness point reaches;
#     * skip the LAST scanned reference (mirror of the shipped skip-first rival).
#   SPEC-TOO-STRONG probes — NEW correct reshapes:
#     * filter to the explicit links FIRST, then fold unconditionally, bridged to
#       `selectRef` by a list induction stated as a `have` INSIDE the prove_correct
#       body (so it stays in variant scope: no new top-level theorem). VERIFIES
#       (exit 0) => the spec is NOT over-fit to the frozen fold's shape. This is the
#       load-bearing soundness evidence in this direction.
#     * a reverse-fold first-writer-wins impl (observationally equal to the frozen
#       last-writer-wins fold) and a `match f.isLink with` reshape: both exit 1
#       under the proof scripts tried, in each case failing on `unsolved goals` /
#       `rfl` for the residual bridge rather than on a spec clause. NOT reported as
#       spec holes: an unclosed proof of a correct impl is UNCERTAIN — the bridging
#       lemma (that reversing the list and keeping the first link equals keeping the
#       last) is a real obligation this auditor did not discharge, not a
#       demonstrated over-strength. Recorded so the next reader knows the state.
# DROPPED (AXIOM_TESTS): the nagini file already carries AXIOM_TESTS = [] (no
#   @ContractOnly callee); this bundle likewise declares no axiom (mapping.md §3).
#   The G-PBT gate ignores AXIOM_TESTS regardless.
#
# CLAUSE / BINDER / POINT COVERAGE. Three clauses. C1 (`∀ k, out k = collectLinks
#   refs k`) is the impl-constraining pin and is attacked by ALL FIVE rivals
#   (drop-filter, value sub-domain, leading element, tie-break, wrong key). C2
#   (`isLink = true`) and C3 (`target = k ∧ g ∈ refs`) are CONSEQUENCES of C1, so
#   no rival can violate them without violating C1; they are named as the
#   structural clause each rival ALSO corresponds to — C2 by weak-no-filter and
#   weak-record-nonlink-on-target0 (both select a non-link entry), C3 by
#   weak-wrong-key (files under the wrong target). Both positives and the
#   admissibility case defend all three clauses (gold discharges C1/C2/C3). The
#   sole input binder `refs` is varied across FIVE distinct points — [Ref 3 f 0],
#   [Ref 0 f 0], [Ref 0 t 5], [Ref 0 t 0; Ref 0 t 1], [Ref 7 t 0] — exercising
#   every `Ref` field: `isLink` at both false (no-filter, value-domain) and true
#   (skip-first, first-wins, wrong-key); `target` at 0, 3, 7 and repeated across
#   two references (first-wins); list length 1 and 2. So pts=5 and no binder /
#   field is held fixed by every witness.
#
# WITNESS MECHANICS: the tester+`decide` path is DEAD (the output is a FUNCTION
#   `LinkMap = Nat → Option Ref` and C1 is `∀ (k : Nat), …`, so no Decidable
#   instance exists). Every witness instead extracts the executable program and
#   refutes C1 at ONE concrete key against the TRANSPARENT `collectLinks`, pinning
#   the rival's selection AND C1's post-image there BY VALUE. Each rival is
#   loop-free so its `…Exec` reduces under `decide`.
#   THE SUBJECT IS NOT GOLD. Gold's `while`-loop `…Exec` is the CCPO fixpoint,
#   which the kernel never reduces at ANY input, so gold's exit code is
#   claim-independent — measured: a claim TRUE of gold (`…Exec [] 0 =
#   collectLinks [] 0`) fails against gold with the same stuck-reduction error,
#   exit 1. `gates/pbt.py::_STUCK_REDUCTION` screens this and will not read gold's
#   exit as a refutation, so every reject case names `witness_reference =
#   _REF_DIRECT` (the loop-free `return collectLinks refs`, which shares the spec
#   and VERIFIES). Against that subject the exit code tracks the claim, which is
#   the whole substance of the attestation. Measured per rival with
#   scripts/lean_verify.sh: witness vs rival exit 0; witness vs `_REF_DIRECT`
#   exit 1 with `Tactic `decide` proved that the proposition … is false` (a
#   semantic refutation by evaluation); the SAME file with the claim FLIPPED
#   (`≠` -> `=`) vs `_REF_DIRECT` exit 0. Two claims, two exit codes.
#   Naming both values is load-bearing separately: a bare `≠` at a key where the
#   rival and the post-image AGREE (key 99, both `none`) is refuted against the
#   RIVAL itself, exit 1, so it cannot be shipped as a witness. No witness binds a
#   hypothesis, so no consistency probe is needed.
AXIOM_TESTS = []
