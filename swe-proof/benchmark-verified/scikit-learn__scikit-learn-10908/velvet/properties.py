"""properties.py — G-PBT falsification battery for scikit-learn__scikit-learn-10908 (velvet).

NOT a Velvet module; a record of adversarially-reasoned cases the G-PBT gate
executes. Each SPEC case is a full ``Solution.lean`` variant that shares the
FROZEN spec byte-for-byte — region surgery touches ONLY text lying wholly inside
the single ``-- impl-start`` / ``-- impl-end`` region, or inside the
``prove_correct getFeatureInventory`` tactic body, both of which the consumer
spec view elides — so ``markers.same_spec`` holds by construction and the
``prove_correct getFeatureInventory`` obligation survives with a byte-identical
method statement. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: elaborates against the rival, FAILS against the frozen
solution).

DEFENDED SURFACE (one contracted operation over two binders, one of them ``mut``):

  getFeatureInventory (mut st : InvState) (supplied : Option (List String))
      return (out : Except InvErr (List String))
    require (match supplied with
              | none       => True
              | some terms => terms ≠ [] ∧ terms.Nodup)          -- (P)
    ensures (st, out) = featureNamesRun stOld supplied           -- (E)

The modeled behavior is reading back the feature inventory of an estimator: the
terms of the established term→position inventory in ascending position order. The
desired behavior is that this succeeds not only after a training run but also when
an inventory was supplied explicitly at construction and no training has happened
— the read-back must first run the establishment step when no inventory has yet
been established, and only then apply the readiness guard.

  Carrier (mapping.md §2):
    ``st.index    : Option (List (String × Nat))`` — the inventory, ``none``
      until established; ``some []`` is an established-but-EMPTY inventory.
    ``st.explicit : Option Bool``  — whether the established inventory was
      supplied explicitly rather than learned; ``none`` until the establishment
      step has run and recorded the fact. This slot is what the failing test's
      first post-rejection assertion observes.
    ``supplied    : Option (List String)`` — the read-only explicit inventory
      parameter (NOT ``mut``: the operation never writes it).

  The single ``ensures`` is one equation, but it pins a PAIR and is therefore
  three independent obligations, each separately attackable:
    (E-state) the post-state ``st``. Covers BOTH halves of the establishment
      step: whether it ran at all, and what it wrote to ``index`` and to
      ``explicit``. Also a FRAME obligation in the directive-5 sense: when
      nothing is established anew, ``featureNamesRun`` returns the entry state
      verbatim, so the post-state must equal it — a rival that re-establishes, or
      clobbers, an already-established inventory violates this.
    (E-result-guard) WHICH rejection, or admission, the readiness guard produces:
      not-ready when no inventory is established, empty-inventory when one is
      established but holds no terms, admission otherwise.
    (E-result-order) on admission, the returned terms and their ORDER — the
      ascending-position projection of the established inventory.

  ``featureNamesRun`` / ``materializeIndex`` / ``readinessGuard`` /
  ``featureList`` are fully-unfolded pure functions of the two binders (the
  ``axioms`` region is EMPTY — mapping.md §3), so pinning ``(st, out)`` to
  ``featureNamesRun`` is GROUNDED in the inputs, not an echo of an opaque
  answer-key: a rival cannot satisfy (E) by returning an oracle's answer, it has
  to compute the transition. Correspondingly, a positive that returns
  ``featureNamesRun`` directly is doing the work, not cheating (see pos-direct).

CARRIER NARROWING (this bundle vs the nagini sibling). The nagini sibling models
the operation as a MUTABLE OBJECT method over a five-field ``Vectoriser`` and
splits (E) into four separately-named clauses (E1 "ends usable", E2 "returns the
mapping", E3 the conditional "an unfitted object only became usable because a
list was supplied, and the names equal it", plus an exceptional clause X pinning
the rejection path). It also carries an explicit fractional-permission obligation
on the supplied list. This bundle models the same behavior as a PURE transition
on ``(state, result)``, so nagini's E1/E2/E3/X are not four clauses here — they
are the three facets of the single pair equation listed above, and every nagini
rival maps onto one of them:

    nagini R2 raise-without-recording-not-supplied  ->  uniq-skip-establish and
        uniq-establish-only-when-supplied (E-state, the ``explicit`` slot)
    nagini R3 fake-fit-empty-names-has-param        ->  uniq-establish-empty
        (E-state ``index`` + E-result-guard)
    nagini R4 swallow-failure-no-raise-on-unfitted  ->  uniq-admit-unready
        (E-result-guard)
    nagini R5 pos-control-flattened-guard           ->  pos-fold-match
    nagini R6 admissibility-f2p-custom-vocab        ->  admiss-explicit-inventory

Four rivals have no nagini counterpart and are added because this carrier makes
them expressible and the coverage rule demands the ``st`` binder be varied by the
witnesses: ``uniq-reestablish-always`` and ``uniq-clobber-established`` attack
(E-state) as a FRAME obligation on an ALREADY-established inventory — the
sub-domain where nagini's E3 is vacuous (its antecedent "was not already fitted"
is false) and so the sibling never probes it. ``uniq-reverse-order`` attacks
(E-result-order), which nagini folds into E3's sequence equality.
``uniq-empty-counts-unestablished`` attacks the established-but-empty BOUNDARY,
a distinction nagini's carrier does not separately name.

ADVERSARIAL READ of the nagini classes on THIS carrier:

  * FRAME-PERMISSION MUTATION (nagini R1, its mandatory directive-5 probe) —
    VACUOUS AS A PERMISSION PROBE. That rival mutates the CONTENTS of the
    supplied list in place, and is rejected by a fractional-permission check with
    no analogue here: Lean and Velvet are referentially transparent — no heap, no
    aliasing, no fractional permission — and ``supplied`` is a pass-by-value
    read-only binder that is not declared ``mut``, so writing to it is not
    expressible, let alone a rejectable act. No substitute probe is fabricated
    for the permission mechanism. What DOES survive of directive 5 is the
    value-level frame obligation on the one ``mut`` binder, and that is attacked
    directly: ``uniq-reestablish-always`` and ``uniq-clobber-established`` both
    write ``st`` where the spec pins it to the entry state.

  * UNGROUNDED-ORACLE ECHO — N/A. The ``axioms`` region declares no ``axiom``;
    every function (E) mentions is a fully-unfolded pure definition over the two
    binders (mapping.md §3 records ``materializeIndex`` / ``readinessGuard`` as
    A-REFERENCES validated equal to their real callees by G-AX, not as assumed
    oracles). There is no opaque term for a rival to echo, and none that blocks a
    witness: every reject witness below fires at literal inputs and needs no
    hypothesis, so no case conditions on the carrier and no consistency probe
    applies.

  * PARTIAL-DOMAIN / CONTROL-DECISION / VALUE-ORDER — APPLY, and are the whole
    reject surface below.

DIVERGENCE LANE — NO HOLE on this bundle; the class is CLOSED by the carrier's own
termination obligation, and no reject case is shippable for it. Corrected during
audit: an earlier revision of this docstring asserted this bundle runs under
``partial`` termination semantics and recorded the class as a live KNOWN HOLE.
That was simply WRONG about the artifact. Solution.lean line 4 reads
``set_option loom.semantics.termination "total"``, as it does in all 500 velvet
bundles, so the disposition inverts. The option cannot drift from the file's
``open TotalCorrectness`` either, because the ``set_option`` elaborator ITSELF
runs ``openScope `TotalCorrectness`` (``Loom/MonadAlgebras/WP/Options.lean``,
lines 169-186). A corpus census that same revision cited from an internal
findings doc, splitting a ``partial`` cohort against a ``total`` one, is
withdrawn with it: there is no split, and the doc no longer exists.

Re-measured directly rather than argued. A rival that prefixes the frozen body
with an unbounded ``while i = 0 do i := 0`` loop, everything else verbatim, is
REJECTED (exit 1) with

    error: Decreasing annotations are required in total correctness semantics
    error: Failed to prove assertion without names: WPGen (forIn Lean.Loop.mk …)

i.e. the verifier discharges a termination obligation this bundle's semantics
impose, and a loop with no decreasing measure fails it. So there is nothing for a
rival to exploit: divergence does NOT verify here, and the ``verify``-implies-
``resolve`` direction is intact on this axis.

It is nevertheless NOT shippable as an ``expect="reject"`` case, and the reason is
mechanical rather than a matter of effort. A reject case on this backend must carry
a witness that ELABORATES against the rival, and the rival's own build is what
fails: the missing decreasing annotation is a hard ``loom.linter.errors``
diagnostic, so every file containing that impl fails to elaborate no matter what is
appended to it. Measured — the witness file built against the diverging rival exits
1 on the rival half (``Decreasing annotations are required …`` plus an unsolved
goal over an unreduced ``forIn Lean.Loop.mk`` term), which the gate reads as
``witness-unproven``: an INCONCLUSIVE outcome that fails the battery rather than
passing it. Suppressing the diagnostic to make the file elaborate
(``set_option loom.linter.errors false``) is not available either: it changes the
solver-flag surface and ``variant_problems`` rejects the variant outright
(measured: ``spec view differs (same_spec failed)``). Recorded here as a closed
class with the exit codes that close it, not as a hole and not as an omission.

WITNESS MACHINERY. The spec is a ``method`` CONTRACT, not a bare predicate, so
each witness reaches it through Velvet's own tester machinery:
``getFeatureInventoryTester st supplied = false`` says the extracted program's
``(post-state, result)`` pair VIOLATES the method's postcondition at that concrete
input. Checked in a file whose ``prove_correct`` block has been stripped, so no
tactic script can mask the verdict. Two workspace facts were measured while
authoring and are handled in the preamble:

  1. the return type ``Except InvErr (List String)`` has no synthesizable
     ``DecidableEq`` in scope, and the ``require``'s ``match``-on-``Option`` shape
     defeats ``infer_instance`` for the precondition (measured: ``failed to
     synthesize Decidable (match supplied with …)``); the preamble supplies both
     explicitly, as COMPUTABLE structural definitions. They are the witness's OWN
     declarations, appended to the rival build and the gold build alike, so they
     exist on both sides by construction and reference only spec-region names
     (``InvErr``, ``InvState``, ``Except``).
  2. ``decide`` is unusable here, but the reason is sharper than an earlier
     revision of this note claimed and the correction matters, because the shape it
     misdescribed is exactly the one the gate refuses. Re-measured on the
     ``uniq-skip-establish`` point: ``decide`` DOES close the goal against the
     RIVAL (exit 0), so "it does not reduce the derived tester" is false as a flat
     statement. What it cannot do is decide anything against GOLD, where it fails

         Tactic `decide` failed … because its `Decidable` instance
           instDecidableEqBool (getFeatureInventoryTester …) false
         did not reduce to `isTrue` or `isFalse`.

     and — this is the part that disqualifies it — the ``= true`` claim at the same
     point fails on gold with the same stuck instance. Gold's exit code would
     therefore carry NO information about the claim, which is precisely the
     ``witness-undecided`` shape the gate screens for (``_STUCK_REDUCTION``); a
     ``decide`` witness here would have been hollow in the gate's own sense, not
     merely inconvenient. ``rfl`` is stuck likewise.

     Unfolding the tester, the program extraction and the pure transition for
     ``simp`` is what closes the goal honestly, and unlike ``decide`` it EVALUATES
     on both sides: every witness below uses that tactic, and all eight were
     rebuilt during audit against the rival (exit 0) and against gold (exit 1 with
     a real refuted goal, ``unsolved goals ⊢ False``) — never a stuck reduction.
     The gold-side exit code was additionally shown to track the CLAIM rather than
     the tactic, by rebuilding each witness with its claim flipped to ``= true``:
     all eight flip to exit 0 on gold and exit 1 on the rival, the exact inversion
     of the shipped pair. That is the forgery test, and it is what distinguishes
     these eight from a witness whose gold-side failure is an artifact.

Each of the eight reject witnesses fires at a DISTINCT concrete input, chosen so
the rival's transition disagrees with the frozen transition there, and jointly the
eight points vary EVERY input binder: ``st.index`` over ``none`` /
established-but-empty / established-non-empty, ``st.explicit`` over ``none`` /
``some false`` / ``some true``, and ``supplied`` over ``none`` / a one-term list
/ a two-term list / a three-term list. Both halves machine-checked per case
(elaborates against the rival, fails on gold by refutation).

AXIOM lane: dropped. The nagini sibling's ``AXIOM_TESTS`` re-run the real callees
in Docker; that is the G-AX lane's job (``axiom_check.py`` in this bundle, whose
pass meta.json records) and this gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-10908"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Frozen anchors (verbatim from Solution.lean). Each lies WHOLLY inside the
# region it names and is unique in the file — asserted at import, so the manifest
# breaks loudly if the frozen solution ever drifts.
# ---------------------------------------------------------------------------

# The establishment gate: the impl region's first statement, and the line the
# desired behavior turns on.
_GATE = "    st := if st.index = none then materializeIndex supplied st else st\n"

# The readiness guard + ordered read-back: the rest of the impl region.
_GUARD = """    let out : Except InvErr (List String) :=
      match readinessGuard st with
      | Except.error e => Except.error e
      | Except.ok _    => Except.ok (featureList (st.index.getD []))
    return out"""

# Gate + guard together, for variants that restructure the whole body.
_IMPL_BODY = _GATE + _GUARD

# The frozen proof obligation. A reshape may retune the tactic body; the
# `prove_correct getFeatureInventory by` HEADER and the method statement stay
# byte-identical, so the obligation survives.
_PROOF = """prove_correct getFeatureInventory by
  loom_solve
  simp_all only [featureNamesRun, materializeIndex, readinessGuard]"""

for _anchor, _label in ((_GATE, "gate"), (_GUARD, "guard"),
                        (_IMPL_BODY, "impl body"), (_PROOF, "proof")):
    if _anchor not in _BASE or _BASE.count(_anchor) != 1:
        raise AssertionError(f"drift: {_label} anchor not present exactly once")


def _gate(new):
    """Variant replacing ONLY the establishment gate (inside the impl region)."""
    return _swap(_BASE, _GATE, new)


def _guard(new):
    """Variant replacing ONLY the guard + read-back (inside the impl region)."""
    return _swap(_BASE, _GUARD, new)


def _body(new, newproof=None):
    """Variant replacing the whole impl-region body, optionally retuning the
    tactic body under the byte-identical `prove_correct` header."""
    src = _swap(_BASE, _IMPL_BODY, new)
    return src if newproof is None else _swap(src, _PROOF, newproof)


# ---------------------------------------------------------------------------
# Witness preamble + tactic. See "WITNESS MACHINERY" in the module docstring for
# the two measured workspace facts these work around. Nothing here assumes
# anything: the two instances are computable structural definitions, and the
# tactic unfolds rather than trusts.
# ---------------------------------------------------------------------------
_WITNESS_PREAMBLE = r"""instance instDecEqInvOut : DecidableEq (Except InvErr (List String)) := fun a b =>
  match a, b with
  | .ok x, .ok y => if h : x = y then isTrue (by rw [h]) else isFalse (by simp [h])
  | .error x, .error y => if h : x = y then isTrue (by rw [h]) else isFalse (by simp [h])
  | .ok _, .error _ => isFalse (by simp)
  | .error _, .ok _ => isFalse (by simp)

extract_program_for getFeatureInventory
prove_precondition_decidable_for getFeatureInventory by
  exact (match supplied with
         | none => isTrue trivial
         | some terms => inferInstanceAs (Decidable (terms ≠ [] ∧ terms.Nodup)))
prove_postcondition_decidable_for getFeatureInventory
derive_tester_for getFeatureInventory
"""

# `decide` leaves the derived tester's Decidable instance stuck in this workspace
# (measured), which would land every case on `witness-undecided`; unfolding the
# tester, the extraction and the pure transition closes the goal for real.
_WITNESS_TACTIC = (
    "  simp [getFeatureInventoryTester, getFeatureInventoryExec, NonDetT.run,\n"
    "        getFeatureInventory, featureNamesRun, materializeIndex,\n"
    "        readinessGuard, featureList]\n")


def _witness(state, supplied):
    """A refutation witness firing at one concrete `(st, supplied)` input: the
    extracted program's (post-state, result) pair VIOLATES the postcondition
    there."""
    return (_WITNESS_PREAMBLE
            + f"\nexample : getFeatureInventoryTester {state} {supplied}"
            + " = false := by\n" + _WITNESS_TACTIC)


_UNESTABLISHED = "{ index := none, explicit := none }"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally DIFFERENT but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG (over-fit to the frozen spelling rather than to the
    # behavior). Both reshapes are point-wise (no loop, no fold), so neither
    # needs an induction or a helper lemma; each keeps the `prove_correct` header
    # byte-identical and only retunes the tactic body, which is necessary because
    # the frozen script is tuned to the frozen statement shape.
    # =====================================================================
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        # Delegate the whole transition to the grounded pure transition in one
        # step: post-state from its first component, result from its second.
        # `featureNamesRun` is a fully-unfolded total function of the two binders
        # (mapping.md §3 — not an opaque oracle), so this COMPUTES the answer
        # rather than echoing one; any wrong state or result would still fail (E).
        # The retuned proof DROPS the frozen `simp_all only` line, which now has
        # no goals left to work on.
        "module": _body(
            "    let r := featureNamesRun st supplied\n"
            "    st := r.1\n"
            "    return r.2",
            "prove_correct getFeatureInventory by\n  loom_solve"),
        "rationale": "(E) pins the pair `(st, out)` to the grounded total "
                     "function `featureNamesRun` of both binders, so computing "
                     "that transition in one step and projecting its two "
                     "components is a fully-correct reshape and MUST verify. If "
                     "it could not, the spec would be over-fit to the frozen "
                     "two-statement spelling (gate, then guard) rather than to "
                     "the behavior — SPEC-TOO-STRONG. It also confirms the "
                     "obligation is discharged by the transition itself and not "
                     "by an artifact of the frozen statement order. Maps the "
                     "sibling's flattened-guard positive (collapse the "
                     "control-flow cascade into one equivalent step).",
    },
    {
        "id": "pos-fold-match",
        "kind": "soundness",
        "expect": "verify",
        # Reshape BOTH halves: test the inventory slot by `match` on the Option
        # instead of by equality with the unestablished marker, and inline the
        # readiness guard as a direct three-way match on the slot (its three cases
        # are exactly the guard's three outcomes) so the admitted branch reads the
        # terms straight out of the match binding rather than through `getD`.
        # Semantically identical on every input; structurally quite different.
        "module": _body(
            "    st := match st.index with\n"
            "          | none   => materializeIndex supplied st\n"
            "          | some _ => st\n"
            "    let out : Except InvErr (List String) :=\n"
            "      match st.index with\n"
            "      | none      => Except.error InvErr.notReady\n"
            "      | some []   => Except.error InvErr.emptyIndex\n"
            "      | some m    => Except.ok (featureList m)\n"
            "    return out",
            "prove_correct getFeatureInventory by\n"
            "  loom_solve\n"
            "  simp_all only [featureNamesRun, materializeIndex, readinessGuard]\n"
            "  rcases hst : stOld.index with _ | m <;> rcases hs : supplied with _ | terms <;>\n"
            "    simp_all <;> cases m <;> simp_all"),
        "rationale": "matching the inventory slot is definitionally the same test "
                     "as comparing it to the unestablished marker, and the "
                     "readiness guard's three outcomes are exactly the three "
                     "cases of that slot, so inlining it changes no input's "
                     "answer — a structurally-different correct impl that MUST "
                     "verify (else SPEC-TOO-STRONG, over-fit to the guard being "
                     "reached through a named helper and to the defaulted spelling "
                     "of the read-back). The retuned tactic body only case-splits "
                     "the two binders (and the inventory's own list) to match the "
                     "reshaped statement; the `prove_correct` header and the "
                     "method statement are byte-identical, so the obligation is "
                     "unchanged. Maps the sibling's helper/branch-reorder "
                     "positive.",
    },

    # =====================================================================
    # ADMISSIBILITY — the precondition (P) is non-trivial here (a supplied list
    # must be non-empty and repetition-free), so PRECOND-TOO-STRONG is a real
    # risk: a precondition that excluded the very configuration the desired
    # behavior is about would make the whole spec vacuous on the interesting
    # sub-domain. This case discharges an in-region `assert` pinning BOTH modeled
    # outcomes at the two configurations the failing test exercises, from a
    # completely unestablished state:
    #   * an explicitly-supplied two-term inventory -> the inventory IS
    #     established (recorded as explicit) and read back in supplied order;
    #   * nothing supplied                          -> still rejected as
    #     not-ready, but the establishment step has by then recorded the (absent)
    #     inventory as NON-explicit.
    # The assert is LIVE, re-measured during audit by mutating the CLAIM alone and
    # rebuilding: each of the three flips below leaves an unsolved goal (exit 1),
    # naming the flipped conjunct in the goal state, so the assert pins all three
    # facets rather than being a tautology `simp` would close whatever it said:
    #   * the returned ORDER   (["beer","burger"] -> ["burger","beer"])   exit 1
    #   * the rejection KIND   (notReady -> emptyIndex)                   exit 1
    #   * the `explicit` SLOT  (some false -> none, on the reject path)   exit 1
    # The frozen body follows it verbatim, so (E) still discharges for the method
    # itself (the unmutated case verifies, exit 0).
    # =====================================================================
    {
        "id": "admiss-explicit-inventory",
        "kind": "admissibility",
        "expect": "verify",
        "module": _body(
            "    assert (with_name_prefix `admiss (\n"
            "      featureNamesRun { index := none, explicit := none } (some [\"beer\", \"burger\"])\n"
            "        = ({ index := some [(\"beer\", 0), (\"burger\", 1)], explicit := some true },\n"
            "           Except.ok [\"beer\", \"burger\"]) ∧\n"
            "      featureNamesRun { index := none, explicit := none } none\n"
            "        = ({ index := none, explicit := some false }, Except.error InvErr.notReady)))\n"
            + _IMPL_BODY,
            "prove_correct getFeatureInventory by\n"
            "  loom_solve\n"
            "  all_goals simp_all [featureNamesRun, materializeIndex, readinessGuard,\n"
            "                      featureList, List.mergeSort]"),
        "rationale": "the two configurations the failing test exercises are both "
                     "ADMITTED by the precondition (P) and both classify to a "
                     "definite, non-degenerate outcome: from a completely "
                     "unestablished state, an explicitly-supplied "
                     "repetition-free inventory is established, recorded as "
                     "explicit, and read back in the supplied order; with nothing "
                     "supplied the request is still rejected as not-ready, yet "
                     "the establishment step has recorded the absent inventory as "
                     "NON-explicit — the exact post-rejection fact the test's "
                     "first assertion observes. The in-region assert is live (a "
                     "wrong claimed outcome leaves an unsolved goal, checked "
                     "out-of-band) and the frozen body follows verbatim so (E) is "
                     "unchanged, so this witnesses that the spec ADMITS the "
                     "modeled behavior at the interesting inputs rather than "
                     "being vacuous or over-strong there. Maps the sibling's "
                     "admissibility probe on the supplied-inventory input.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each carries a machine-checked refutation witness at
    # a DISTINCT concrete input (both halves seen to discriminate: elaborates
    # against the rival, fails on gold BY REFUTATION rather than stuck reduction)
    # and a `refinement` argument that its faithful real counterpart would NOT
    # resolve the failing test.
    # =====================================================================
    {
        "id": "uniq-skip-establish",
        "kind": "uniqueness",
        "expect": "reject",
        # THE DEFECT ITSELF. Drop the establishment gate entirely: go straight to
        # the readiness guard. An explicitly-supplied inventory is therefore never
        # established, so the read-back is rejected as not-ready, and the
        # explicit/non-explicit fact is never recorded either.
        "module": _gate(""),
        "refinement": "this is the pre-change behavior: the read-back applies the "
                      "readiness guard without first running the establishment "
                      "step. Its faithful real counterpart is the unpatched "
                      "source, under which reading back the inventory of an "
                      "estimator that was handed an explicit inventory and never "
                      "trained is rejected as not-yet-ready — the exact complaint "
                      "the public issue reports. The failing test asserts that "
                      "read-back returns the nine supplied terms in order, and "
                      "also that after the earlier rejection the "
                      "explicit/non-explicit fact HAS been recorded (its first "
                      "post-rejection assertion); both fail here, the first with "
                      "the rejection and the second because the fact is never "
                      "written. It does NOT resolve — it is the defect under fix.",
        "rationale": "REJECT from all three facets of (E) at once. With an "
                     "explicitly-supplied inventory and nothing established, the "
                     "frozen transition establishes the inventory (E-state), "
                     "admits the request (E-result-guard) and returns the terms in "
                     "position order (E-result-order); the rival establishes "
                     "nothing, leaves the explicit slot unwritten, and rejects. If "
                     "this verified => SPEC-TOO-WEAK, and the reported defect "
                     "would pass unnoticed. Maps the sibling's raise-path rival.",
        "witness": _witness(_UNESTABLISHED, '(some ["beer", "burger"])'),
    },
    {
        "id": "uniq-establish-only-when-supplied",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on E-state. Runs the establishment step ONLY when a list was
        # actually supplied — correct on the whole supplied sub-domain, which is
        # exactly why it needs its own witness rather than sharing
        # uniq-skip-establish's. When nothing was supplied it skips the step, so
        # the (absent) inventory is never RECORDED as non-explicit: the request is
        # still rejected as not-ready and the outcome LOOKS right, but the
        # post-state is wrong.
        "module": _gate(
            "    st := if st.index = none then\n"
            "            (match supplied with\n"
            "             | none       => st\n"
            "             | some _     => materializeIndex supplied st)\n"
            "          else st\n"),
        "refinement": "its faithful real counterpart guards the establishment "
                      "step on an explicit inventory having been supplied, "
                      "skipping it otherwise — so on an estimator with no "
                      "explicit inventory the read-back is rejected without the "
                      "establishment step ever having run, and the "
                      "explicit/non-explicit fact is left unset. The failing "
                      "test's FIRST post-rejection assertion reads exactly that "
                      "fact off the estimator, and on an unset attribute that "
                      "assertion errors out rather than passing. So the test fails "
                      "at its first assertion and the instance does NOT resolve — "
                      "even though every later assertion, about the "
                      "supplied-inventory case, would pass.",
        "rationale": "REJECT from (E-state) on the nothing-supplied sub-domain: "
                     "the frozen transition runs the establishment step whenever "
                     "no inventory is established, which with nothing supplied "
                     "records the inventory as NON-explicit while leaving the "
                     "inventory slot unestablished; the rival leaves the explicit "
                     "slot unwritten. The RESULT component agrees with gold at "
                     "EVERY input — machine-checked, not asserted: enumerated over "
                     "6 entry states x 4 supplied values, the result halves are "
                     "equal in all 24 and the pair differs in exactly the 2 whose "
                     "entry inventory is unestablished with nothing supplied. So "
                     "the result half of (E) alone would NOT catch this — the "
                     "post-state half is what rejects it, which is the "
                     "point of pinning the pair. A near-miss of "
                     "uniq-skip-establish, refuted at its own distinguishing "
                     "input (nothing supplied) rather than sharing that rival's. "
                     "Maps the sibling's raise-path side-effect-omission rival.",
        "witness": _witness(_UNESTABLISHED, "none"),
    },
    {
        "id": "uniq-establish-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # E-state on the inventory slot + E-result-guard. Records the establishment
        # as explicit (so the explicit slot is RIGHT) but establishes an EMPTY
        # inventory instead of building it from the supplied terms — a broken
        # establishment step. The readiness guard then rejects the request as
        # empty-inventory rather than admitting it.
        "module": _gate(
            "    st := if st.index = none then\n"
            "            (match supplied with\n"
            "             | none       => materializeIndex supplied st\n"
            "             | some _     => { index := some [], explicit := some true })\n"
            "          else st\n"),
        "refinement": "its faithful real counterpart marks the inventory as "
                      "established-and-explicit without iterating the supplied "
                      "terms, leaving an empty inventory. The failing test asserts "
                      "the read-back returns the nine supplied terms in order; "
                      "here the read-back is instead rejected as an empty "
                      "inventory, so that assertion fails and the instance does "
                      "NOT resolve. It also breaks unrelated already-passing "
                      "behavior, since every explicitly-supplied inventory would "
                      "come out empty.",
        "rationale": "REJECT from (E-state) on the inventory slot and "
                     "(E-result-guard): the frozen transition establishes the "
                     "inventory AS the supplied terms bound to their positions and "
                     "then admits the request, whereas the rival establishes an "
                     "empty inventory and is rejected by the guard. Note the "
                     "explicit slot is written CORRECTLY, so a spec pinning only "
                     "that fact would miss this — the inventory CONTENT half of "
                     "(E-state) is what rejects it. Refuted at a one-term supplied "
                     "list: minimal, and a value of `supplied` no other rival "
                     "probes. Maps the sibling's fake-fit-empty-names rival.",
        "witness": _witness(_UNESTABLISHED, '(some ["pizza"])'),
    },
    {
        "id": "uniq-reverse-order",
        "kind": "uniqueness",
        "expect": "reject",
        # E-result-order. Establishes the inventory from the supplied terms but
        # binds them to positions in REVERSE, so the read-back returns the terms in
        # the wrong order. Correct on every one-term list (and on any symmetric
        # one), so this is a genuine partial-domain rival needing a longer input.
        "module": _gate(
            "    st := if st.index = none then\n"
            "            (match supplied with\n"
            "             | none       => materializeIndex supplied st\n"
            "             | some terms => { index := some terms.reverse.zipIdx,\n"
            "                               explicit := some true })\n"
            "          else st\n"),
        "refinement": "its faithful real counterpart establishes the inventory "
                      "from the supplied terms but assigns positions in the "
                      "opposite order. The failing test asserts the read-back "
                      "equals the nine supplied terms IN THE SUPPLIED ORDER, and "
                      "separately that each returned term's recorded position "
                      "equals its index in the returned sequence; the reversed "
                      "assignment fails the first of those on any list of two or "
                      "more distinct terms, so the instance does NOT resolve.",
        "rationale": "REJECT from (E-result-order): the frozen transition binds "
                     "each supplied term to ITS OWN position in the supplied "
                     "sequence, and the read-back is the ascending-position "
                     "projection, so the returned order is the supplied order; the "
                     "rival returns it reversed (and stores a different "
                     "post-state, so E-state fails too). It agrees with gold on "
                     "every single-term inventory (and on nothing-supplied), which "
                     "is why it needs a supplied list of length >= 2; enumerated, "
                     "the pair agrees at `none` and at a one-term list and differs "
                     "at both a two-term and a three-term list. Refuted here at a "
                     "THREE-term list, which is a FREE choice among the "
                     "distinguishing inputs rather than a forced one — the point of "
                     "the length is that it is >= 2, and the three-term list "
                     "additionally keeps this witness's `supplied` value distinct "
                     "from every other case's, so no two witnesses share a point. "
                     "Maps the ordering half of the sibling's "
                     "names-equal-the-supplied-list clause.",
        "witness": _witness(_UNESTABLISHED, '(some ["salad", "coke", "water"])'),
    },
    {
        "id": "uniq-admit-unready",
        "kind": "uniqueness",
        "expect": "reject",
        # E-result-guard, the mirror image of the defect: drop the readiness guard
        # and admit unconditionally, reading whatever the inventory slot holds
        # (nothing, for an unestablished or empty one). Swallows the rejection and
        # returns an empty term list instead.
        "module": _guard(
            "    let out : Except InvErr (List String) :=\n"
            "      Except.ok (featureList (st.index.getD []))\n"
            "    return out"),
        "refinement": "its faithful real counterpart drops the readiness check and "
                      "returns an empty term sequence instead of rejecting. The "
                      "failing test's first act is to assert that the read-back IS "
                      "rejected on an estimator that is neither trained nor given "
                      "an explicit inventory; with no rejection raised that "
                      "assertion fails immediately, so the instance does NOT "
                      "resolve. It also breaks the separate already-passing "
                      "behavior that an empty inventory is rejected rather than "
                      "read back as nothing.",
        "rationale": "REJECT from (E-result-guard): the frozen transition applies "
                     "the readiness guard, which rejects an established-but-empty "
                     "inventory as empty-inventory (and an unestablished one as "
                     "not-ready), whereas the rival admits every input. Refuted on "
                     "an established-but-EMPTY inventory with nothing supplied — a "
                     "point that exercises the empty-inventory rejection "
                     "specifically, and one no other rival probes: this is the "
                     "only witness holding the inventory at established-empty with "
                     "nothing supplied. Maps the sibling's swallow-the-failure "
                     "rival.",
        "witness": _witness("{ index := some [], explicit := some true }", "none"),
    },
    {
        "id": "uniq-reestablish-always",
        "kind": "uniqueness",
        "expect": "reject",
        # FRAME on (E-state), with no nagini counterpart: the sibling's conditional
        # clause is vacuous on this sub-domain (its antecedent is "was not already
        # established"), so it never probes here. Run the establishment step
        # UNCONDITIONALLY, discarding an already-established inventory and
        # overwriting the explicit fact.
        "module": _gate("    st := materializeIndex supplied st\n"),
        "refinement": "its faithful real counterpart runs the establishment step "
                      "on every read-back rather than only when no inventory has "
                      "been established yet. On an estimator that HAS been trained "
                      "and was also handed an explicit inventory, the learned "
                      "inventory is thrown away and replaced by the supplied one, "
                      "and the explicit/non-explicit fact is rewritten — so a "
                      "trained estimator's read-back no longer reports what it "
                      "learned. The failing test reads back a trained estimator's "
                      "inventory and asserts both the terms and each term's "
                      "recorded position, and other already-passing behavior "
                      "asserts a trained estimator reports its inventory as "
                      "NON-explicit; both break, so the instance does NOT resolve.",
        "rationale": "REJECT from (E-state) as a FRAME obligation on the one `mut` "
                     "binder: when an inventory is already established the frozen "
                     "transition returns the ENTRY state verbatim, so the "
                     "post-state must equal it; the rival overwrites both the "
                     "inventory and the explicit fact. This is the directive-5 "
                     "value-level frame check that survives on this carrier (the "
                     "sibling's fractional-permission probe does not — there is no "
                     "heap here), and it attacks the sub-domain the sibling's "
                     "conditional clause leaves vacuous. Refuted at an "
                     "ALREADY-ESTABLISHED non-empty inventory with a supplied list "
                     "present, so that the establishment step actually changes "
                     "something — the only witness at that combination.",
        "witness": _witness(
            '{ index := some [("water", 0)], explicit := some false }',
            '(some ["beer"])'),
    },
    {
        "id": "uniq-clobber-established",
        "kind": "uniqueness",
        "expect": "reject",
        # FRAME on (E-state), near-miss of uniq-reestablish-always: it agrees with
        # gold on the whole UNESTABLISHED sub-domain (the establishment step runs
        # exactly as frozen) and goes wrong only when an inventory was already
        # established, which it empties. So it needs its own witness: the
        # sub-domain its rationale claims — established inventories with NOTHING
        # supplied — is only demonstrated at this point, where
        # uniq-reestablish-always would be harmless.
        "module": _gate(
            "    st := if st.index = none then materializeIndex supplied st\n"
            "          else { st with index := some [] }\n"),
        "refinement": "its faithful real counterpart empties the inventory of an "
                      "estimator that already had one — a read-back that destroys "
                      "what it was meant to report. The failing test reads back a "
                      "trained estimator's inventory and asserts its terms and "
                      "their recorded positions; here that read-back is instead "
                      "rejected as an empty inventory, so the instance does NOT "
                      "resolve. Every other read-back of a trained estimator "
                      "breaks the same way.",
        "rationale": "REJECT from (E-state) as a FRAME obligation: with an "
                     "inventory already established the frozen transition returns "
                     "the entry state verbatim and admits the request, whereas the "
                     "rival empties the inventory and is then rejected by the "
                     "guard. It agrees with gold on the ENTIRE unestablished "
                     "sub-domain, so it is a near-miss of uniq-reestablish-always "
                     "and is refuted at its own distinguishing input — an "
                     "already-established non-empty inventory with NOTHING "
                     "supplied, where uniq-reestablish-always is harmless (its "
                     "establishment step would leave the inventory in place) but "
                     "this rival still clobbers. The only witness holding the "
                     "explicit slot at recorded-non-explicit with nothing "
                     "supplied.",
        "witness": _witness(
            '{ index := some [("beer", 0)], explicit := some false }', "none"),
    },
    {
        "id": "uniq-empty-counts-unestablished",
        "kind": "uniqueness",
        "expect": "reject",
        # E-state BOUNDARY: conflate "no inventory established" with "an
        # established inventory holding no terms", re-running the establishment
        # step for both. Correct on every unestablished and every non-empty state;
        # wrong exactly at the established-but-EMPTY boundary, where it silently
        # replaces the empty inventory instead of letting the guard reject it.
        "module": _gate(
            "    st := if st.index = none ∨ st.index = some [] then\n"
            "            materializeIndex supplied st\n"
            "          else st\n"),
        "refinement": "its faithful real counterpart treats an established but "
                      "term-less inventory as though none had been established, "
                      "re-running the establishment step on it. An estimator whose "
                      "inventory legitimately came out empty would then silently "
                      "have it replaced by the explicitly-supplied one and its "
                      "explicit/non-explicit fact rewritten, instead of the "
                      "read-back being rejected as empty. That contradicts the "
                      "already-passing behavior that an empty inventory is "
                      "rejected, so the instance does NOT resolve.",
        "rationale": "REJECT from (E-state) at the established-but-empty BOUNDARY: "
                     "the frozen transition runs the establishment step only when "
                     "NO inventory has been established, so an established empty "
                     "one is left untouched and the guard rejects it as "
                     "empty-inventory; the rival replaces it and admits. It agrees "
                     "with gold on both the unestablished and the non-empty "
                     "sub-domains, so only this boundary input distinguishes it — "
                     "an established EMPTY inventory recorded as explicit, WITH a "
                     "supplied list present. The only witness at that combination "
                     "(uniq-admit-unready shares the state but holds `supplied` at "
                     "nothing-supplied, where this rival is harmless).",
        "witness": _witness(
            "{ index := some [], explicit := some true }", '(some ["beer"])'),
    },
]


# ---------------------------------------------------------------------------
# NAGINI -> VELVET ACCOUNTING. The sibling ships 6 SPEC cases + 2 AXIOM_TESTS;
# this battery ships 11 SPEC cases (3 verify + 8 reject). Every sibling case is
# accounted for below.
#
#   sibling case (nagini)                    kind          -> here
#   ------------------------------------------------------------------------
#   R5 pos-control-flattened-guard           soundness     -> pos-fold-match     PORTED
#                                                             (+ pos-direct     ADDED)
#   R6 admissibility-f2p-custom-vocab        admissibility -> admiss-explicit-inventory  RE-AIMED
#   R2 raise-without-recording-not-supplied  uniqueness    -> uniq-skip-establish +
#                                                             uniq-establish-only-when-supplied  PORTED (split)
#   R3 fake-fit-empty-names-has-param        uniqueness    -> uniq-establish-empty  PORTED
#   R4 swallow-failure-no-raise-on-unfitted  uniqueness    -> uniq-admit-unready    PORTED
#   R1 frame-mutation-write-readonly-param   uniqueness    -> (none)               VACUOUS
#   ax-sound-validate-vocabulary             axiom         -> (none)               G-AX's lane
#   ax-contain-validate-vocabulary-domain    axiom         -> (none)               G-AX's lane
#
# OMITTED, with reasons:
#   * R1 (the sibling's MANDATORY frame/permission probe) — VACUOUS as a
#     permission probe on this carrier, and deliberately not substituted. It
#     appends to the supplied list's contents and is rejected for insufficient
#     fractional permission; this backend is referentially transparent (no heap,
#     no aliasing, no fractional permission) and the supplied inventory is an
#     immutable pass-by-value binder, so the write is not even expressible. What
#     survives of directive 5 is the VALUE-level frame obligation on the one `mut`
#     binder, and that is attacked by two rivals the sibling does not have
#     (uniq-reestablish-always, uniq-clobber-established), so the frame SURFACE is
#     covered even though the permission MECHANISM has no analogue.
#   * both AXIOM_TESTS — dropped by design: the axiom lane belongs to G-AX
#     (axiom_check.py validates `materializeIndex` and `readinessGuard` as
#     A-references against their real callees) and this gate ignores AXIOM_TESTS.
#   * NO soundness positive was dropped for want of a closing proof. Both
#     positives here were reproven honestly under the byte-identical
#     `prove_correct` header (pos-direct by DELETING a now-redundant simp line,
#     pos-fold-match by case-splitting the two binders); neither adds a lemma and
#     neither reaches for sorry/admit/native_decide/an axiom.
#
# NO KNOWN HOLE on the DIVERGENCE lane — corrected during audit. This bundle runs
#   under `loom.semantics.termination "total"` (Solution.lean line 4), NOT
#   "partial" as an earlier revision of this file claimed, so the disposition is
#   the opposite of the one recorded there: a diverging impl does NOT verify. A
#   rival prefixing the frozen body with `while i = 0 do i := 0` is REJECTED
#   (exit 1, `Decreasing annotations are required in total correctness
#   semantics`), so the carrier's termination obligation closes the class. It is
#   still not shippable as a reject case: that hard diagnostic makes the rival's
#   own witness build fail to elaborate (measured exit 1 => `witness-unproven`,
#   inconclusive), and suppressing it breaks same_spec. See the DIVERGENCE LANE
#   paragraph in the module docstring for the exit codes.
#
# COVERAGE OF WHAT IS MODELED.
#   Obligation: the sole `prove_correct getFeatureInventory` is DEFENDED (3
#     expect="verify" cases) and ATTACKED (8 expect="reject" rivals).
#   Clauses: all three facets of (E) are attacked independently —
#     (E-state) inventory slot: uniq-establish-empty, uniq-clobber-established,
#               uniq-empty-counts-unestablished, uniq-reestablish-always
#     (E-state) explicit slot:  uniq-establish-only-when-supplied,
#               uniq-reestablish-always
#     (E-result-guard):         uniq-admit-unready, uniq-skip-establish,
#               uniq-establish-empty
#     (E-result-order):         uniq-reverse-order
#   Binders: 8 DISTINCT witness points, varying every input binder —
#     st.index    : none (4 points) / established-empty (2) / established-non-empty (2)
#     st.explicit : none (4) / recorded-non-explicit (2) / recorded-explicit (2)
#     supplied    : nothing-supplied (3) / one-term (3) / two-term (1) / three-term (1)
#   No binder is held at a single value across the witnesses, so no rival that
#   mishandled only one input could slip through unprobed. Every near-miss pair is
#   split onto its own distinguishing point rather than sharing: the two frame
#   rivals differ on the nothing-supplied entry, the two establishment-gate rivals
#   differ on whether anything was supplied, and the two empty-inventory rivals
#   differ on whether a list is present at the boundary.
#
# INDEPENDENT AUDIT PROBES (not shipped as cases; recorded so the next reader knows
# what was already tried and need not re-measure it). Eight NEW impls the battery
# above does not contain were built against the frozen spec, aimed at what the
# shipped rivals leave unattacked. None found a hole in either direction.
#
#   SPEC-TOO-WEAK probes (new WRONG impls; a verify here would be a spec hole):
#     gate on the `explicit` slot instead of the inventory slot     rejected (1)
#     project the inventory WITHOUT the ascending-position sort     rejected (1)
#     swap the two rejection kinds (notReady <-> emptyIndex)        rejected (1)
#     descending-position projection (order attack via .reverse)    rejected (1)
#     rewrite ONLY the `explicit` slot on the already-established
#       path — the finest frame near-miss, leaves `index` intact    rejected (1)
#     establish the right inventory but record explicit := false    rejected (1)
#     on nothing-supplied record explicit := some true              rejected (1)
#   So (E) is tight on every facet probed, including two the shipped rivals only
#   reach in combination with an `index` change.
#
#   OUT-OF-DOMAIN LICENCE probe (expected to verify, and does): an impl that
#     misbehaves ONLY on a supplied list with a repeated term VERIFIES (exit 0).
#     That is the precondition (P) doing its job, not a hole — `terms.Nodup`
#     excludes the input, and the real callee raises there too (mapping.md §3.1),
#     so no in-domain input distinguishes this impl from the frozen one. Recorded
#     because it is the one direction where a "verifying wrong impl" is CORRECT.
#
#   SPEC-TOO-STRONG probes (new CORRECT reshapes; a reject here would be a
#   soundness hole in the spec). All three VERIFY (exit 0):
#     bind the post-establishment state, read the guard off it, assign `st` last
#     test the slot with `Option.isNone` instead of equality with `none`
#     build the result with `Except.map` instead of the match cascade
#   So the spec is not over-fit to the frozen spelling of the gate, the slot test,
#   or the result cascade.
AXIOM_TESTS = []
