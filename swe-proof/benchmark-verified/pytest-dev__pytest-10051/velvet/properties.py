"""properties.py — G-PBT falsification battery for pytest-dev__pytest-10051 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct clearCapture`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation; it is checked by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates: the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE. One contracted method that empties, in place, the record
sequence a capture buffer holds for the current phase:

  clearCapture (mut c : Capture) return (u : Unit)
    require  c.callId = c.live.ident
    ensures  c.live.ident  = cOld.live.ident        -- (E1) identity frame
    ensures  c.callId      = cOld.callId            -- (E2) call-ref frame
    ensures  c.callSnap    = cOld.callSnap          -- (E3) snapshot frame
    ensures  liveRecords c = []                     -- (E4) live emptied
    ensures  callRecords c = []                     -- (E5) call-ref sees empty

``Capture`` carries the live buffer (``live : Buffer`` = an identity token
``ident`` plus its ``contents``), the identity the per-phase "call" reference was
bound to at phase preparation (``callId``), and the sequence that reference would
expose were it detached from the live buffer (``callSnap``). ``liveRecords`` is
the live contents; ``callRecords`` is ``live.contents`` while the call reference
still denotes the live buffer (``callId = live.ident``) and ``callSnap`` once the
two have diverged. The ``require`` pins the F2P entry state: on phase setup the
call reference and the live reference denote the SAME buffer object.

FIVE load-bearing top-level ``ensures`` clauses over the single ``mut`` binder
``c`` (whose sub-fields ``live.ident`` / ``live.contents`` / ``callId`` /
``callSnap`` are the sub-inputs the reject witnesses vary). FOUR of them are
logically independent; E5 is a DERIVED consequence, not an independent
constraint — see the note under E5:
  * (E1) ``c.live.ident = cOld.live.ident`` — THE fix. The live buffer must be
    emptied IN PLACE, keeping the SAME buffer object; a body that replaces it
    with a fresh object (a rebind) fails here. This is the discriminating clause:
    emptiness alone (E4) is satisfiable by the buggy rebind, but the fresh object
    breaks the identity frame.
  * (E2) ``c.callId = cOld.callId`` — the call reference's bound identity is
    read-only; the clear must not perturb it.
  * (E3) ``c.callSnap = cOld.callSnap`` — the detached snapshot is read-only; the
    clear must not perturb it either.
  * (E4) ``liveRecords c = []`` — the live sequence becomes empty (the emptiness
    the P2P/F2P observe after clear).
  * (E5) ``callRecords c = []`` — BECAUSE identity is preserved (E1) and the
    precondition pins ``callId = live.ident``, the call reference still denotes
    the live buffer and therefore also observes the empty sequence. A rebind
    orphans the call reference (its bound identity no longer matches the fresh
    buffer's), so it keeps observing the stale ``callSnap`` and E5 fails.
    NOT INDEPENDENT, and the battery does not claim it is: E5 is ENTAILED by
    ``require`` + E1 + E2 + E4. Machine-checked (audit, real build, exit 0)::

        theorem e5_implied (cOld c : Capture)
            (req : cOld.callId = cOld.live.ident)
            (e1 : c.live.ident = cOld.live.ident)
            (e2 : c.callId = cOld.callId)
            (e4 : liveRecords c = []) : callRecords c = [] := by
          unfold callRecords; rw [e2, e1, req]; simpa using e4

    So E5 adds no strength; it is a READABILITY clause that spells out the
    consequence the F2P actually observes. It follows that no reject case can
    fail E5 ALONE, and none claims to — every rival that breaks E5 breaks one of
    E1/E2/E4 first, which is why each reject rationale names that clause as the
    primary one.
Everything is grounded in the method's own input state (``cOld`` and the pinned
alias); the ``axioms`` region is empty, so there is no opaque answer key to echo
(directive 8).

SPEC COMPLETENESS (why the reject lane is bounded, and can be). ``Capture`` has
exactly three fields and ``Buffer`` exactly two, and E1/E2/E3 pin three of them
to ``cOld`` while E4 pins the fourth to ``[]``. The post-state is therefore
UNIQUELY determined by the contract — machine-checked (audit, real build,
exit 0)::

    theorem post_state_unique (cOld c c' : Capture)
        (h1 : c.live.ident = cOld.live.ident) (h1' : c'.live.ident = cOld.live.ident)
        (h2 : c.callId = cOld.callId)         (h2' : c'.callId = cOld.callId)
        (h3 : c.callSnap = cOld.callSnap)     (h3' : c'.callSnap = cOld.callSnap)
        (h4 : liveRecords c = [])             (h4' : liveRecords c' = []) :
        c = c' := by
      obtain ⟨⟨i, xs⟩, k, s⟩ := c; obtain ⟨⟨i', xs'⟩, k', s'⟩ := c'
      simp_all [liveRecords]

That is the strongest statement this lane can make: the spec admits exactly ONE
post-state per admissible input, so there is NO room for a wrong impl to verify
and SPEC-TOO-WEAK is unreachable by construction rather than merely unobserved.
Correspondingly, a correct reshape can only fail for a TACTIC reason, which is
what the two positive controls guard.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * SOUNDNESS positives — APPLY. Structurally different but CORRECT impls (empty
    through a local binding of the emptied buffer; name the preserved identity
    token explicitly) that MUST verify, else SPEC-TOO-STRONG. Each keeps the
    in-place-empty / identity-preserving shape so the frozen ``loom_solve`` script
    still closes.
  * ADMISSIBILITY — APPLIES (this method HAS a precondition). ``admiss-f2p-shape``
    discharges an in-region ``assert`` that the F2P-shaped input (the call
    reference aliasing the live buffer, ``callId = live.ident``, with a genuinely
    NON-EMPTY live sequence so the clear is a real transition) satisfies the alias
    invariant and is non-degenerate — so a normal ``caplog.clear()`` after logging
    is admitted (else PRECOND-TOO-STRONG). The impl and frozen proof are kept
    verbatim so E1–E5 still discharge; the proof gains a ``decide`` arm.
  * FRAME / PERMISSION-MUTATION (the nagini MANDATORY note) — the permission
    MECHANISM is vacuous here. The nagini sibling holds the single shared list at
    a FULL heap permission and notes there is NO half-permission ``Acc(x,1/2)``
    read-only input (``view`` carries only the aliasing constraint, no independent
    permission), so the classic frame-mutation probe does not apply on EITHER
    backend. Velvet is referentially transparent: ``c`` is a ``mut`` VALUE binder
    with no heap and no aliasing. But the BEHAVIOUR the sibling calls the "instance
    -specific analogue of a frame attack" — the REBIND that the permission system
    allows but the identity postcondition must reject — is NOT lost: it is
    captured directly by the value-level identity frame E1 and attacked by
    ``rebind-orphans`` / ``clear-then-rebind`` below, and the read-only-frame
    behaviour on the other fields is captured by E2/E3 and attacked by
    ``mutate-callid`` / ``mutate-callsnap``. So the mechanism is vacuous; the
    behaviour is fully expressible and exercised (see footer).
  * DIVERGENCE / NON-TERMINATION — VACUOUS on this cell. The nagini sibling
    carries two divergence rivals (``recursion-discard`` / ``empty-then-recurse``)
    guarded by ``Requires(MustTerminate(2))``. This bundle sets
    ``loom.semantics.termination "total"``, under which a postcondition is claimed of
    ALL runs, not only terminating ones, and the verifier demands a decreasing
    measure on every loop. (An earlier version of this bullet called the cell "one of
    the 99 total-semantics velvet bundles" against "the 401 ``partial`` bundles where
    it is a known spec hole", citing an internal findings doc. That census is
    withdrawn: all 500 velvet bundles set ``"total"`` and open ``TotalCorrectness``,
    so there is no ``partial`` cohort and no such hole on file.) A diverging
    body IS writable here — ``while true do ...`` spliced into the impl region
    elaborates as a term — but it is REFUSED, which is the point: measured by the
    audit with a real build (exit 1) on exactly that splice,
    ``error: Decreasing annotations are required in total correctness semantics``,
    and the sharper shape is refused too, which matters because it cannot be
    dismissed as merely missing the annotation: a loop CARRYING a measure that does
    not decrease (``while q > 0 / invariant 0 ≤ q / done_with q = 0 /
    decreasing q``, body ``q := q``) is REJECTED on the measure's own goal -
    ``case «decreasing_1: q»``, residual ``⊢ q < q``. So the divergence rivals have
    nothing to attack on this cell and are correctly not ported; NOT a known hole.
    See footer.

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so
each reject rival reaches it through Velvet's own tester machinery:
``clearCaptureTester c = false`` says the extracted program's observable
post-state (the mutated ``c``) violates the method's postcondition at that
concrete input. Checked in a file whose ``prove_correct`` block has been
stripped, so no tactic script can mask the verdict. The tester is VACUOUSLY
``true`` on any precondition-violating input (confirmed out-of-band: a witness
with ``callId ≠ live.ident`` does NOT discriminate), so every witness pins
``callId = live.ident`` — the F2P entry state. ``Capture`` fields are ``Nat`` /
``List Nat`` with decidable equality, so every witness closes by ``decide``. Each
reject witness below was run against BOTH the rival (exit 0) and the frozen
solution (exit 1) with two real builds and was SEEN to discriminate. No witness
binds a hypothesis (the carrier is fully transparent — all fields are concrete
literals), so there is no joint-satisfiability obligation.

AXIOM lane: EMPTY. ``meta.json`` declares no axioms and no deep-model references
(mapping.md §3: the clear calls no unchanged external operation; the in-place
empty is modeled deeply as ``{ c.live with contents := [] }`` — every step is R
or I). Nothing in the proof rests on an axiom, and this gate ignores
``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "pytest-dev__pytest-10051"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor. The ENTIRE frozen impl body (marker lines and inline
# ---- comments included); lies wholly inside the single `-- impl-start` /
# ---- `-- impl-end` region and is unique in Solution.lean (both facts asserted
# ---- at load by _swap).
_GOLD_IMPL = (
    "    -- impl-start\n"
    "    -- Empty the live buffer in place: keep the same buffer object (its identity\n"
    "    -- token is left untouched) and set its contents to the empty sequence. Any\n"
    "    -- reference aliasing this buffer therefore observes the empty sequence.\n"
    "    c := { c with live := { c.live with contents := [] } }\n"
    "    return\n"
    "    -- impl-end"
)
assert _BASE.count(_GOLD_IMPL) == 1, "frozen impl region drifted from expected text"

# ---- the `-- impl-start` marker line (unique); the admissibility case inserts an
# ---- in-region `assert` immediately after it, keeping the whole gold body.
_IMPL_START = "    -- impl-start\n"
assert _BASE.count(_IMPL_START) == 1, "impl-start anchor drift"

# ---- proof-body anchor. The frozen tactic script is elided from the consumer
# ---- spec view (only the obligation header is kept), so a case may retune the
# ---- tactic body without touching the spec statement or dropping the
# ---- obligation. Unique in the file.
_GOLD_PROOF = "prove_correct clearCapture by\n  loom_solve"
assert _BASE.count(_GOLD_PROOF) == 1, "frozen proof body drifted from expected text"


def _impl(body):
    """Full Solution.lean variant with the gold impl body replaced."""
    return _swap(_BASE, _GOLD_IMPL, body)


# A proof that ALSO clears an in-region `assert` VC (decidable), keeping the
# frozen `loom_solve` arm for the five method obligations. Used by admissibility.
_PROOF_WITH_DECIDE = (
    "prove_correct clearCapture by\n"
    "  loom_solve <;> first | decide | skip"
)


def _impl_assert(assert_block):
    """Insert an in-region assert right after `-- impl-start`, keep the gold body,
    and retune the proof so the extra decidable VC discharges."""
    src = _swap(_BASE, _IMPL_START, _IMPL_START + assert_block)
    return _swap(src, _GOLD_PROOF, _PROOF_WITH_DECIDE)


# ---- witness preamble. Reaches the method contract through Velvet's tester
# ---- machinery; checked in a file whose `prove_correct` block is stripped by
# ---- the gate. `clearCaptureTester c = false` says the extracted program's
# ---- observable post-state violates the postcondition at that input. No
# ---- `axiom`/`sorry`/`native_decide`; the frozen solution rejects each witness.
# ---- `Capture` is written as `⟨⟨ident, contents⟩, callId, callSnap⟩`; every
# ---- witness pins `callId = ident` (the precondition — else the tester is
# ---- vacuously true and does not discriminate).
def _tester(body):
    return (
        "extract_program_for clearCapture\n"
        "prove_precondition_decidable_for clearCapture\n"
        "prove_postcondition_decidable_for clearCapture\n"
        "derive_tester_for clearCapture\n\n" + body)


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify, else the post-image is SPEC-TOO-STRONG. Each keeps the
    # byte-identical five-clause obligation and only reshapes the executable
    # surface; the frozen `loom_solve` script still discharges all five. Both
    # verified out-of-band with real builds.
    # =====================================================================
    {
        "id": "pos-control-local-emptied",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: bind the emptied buffer to a local first, then store it. The
        # buffer object is never replaced (its `ident` rides through the `with`),
        # so identity is preserved and the contents become empty — E1..E5 all hold.
        "module": _impl(
            "    -- impl-start\n"
            "    let emptied := { c.live with contents := [] }\n"
            "    c := { c with live := emptied }\n"
            "    return\n"
            "    -- impl-end"),
        "rationale": "a correct reshape of the gold body: empty the live buffer "
                     "through a LOCAL binding of the emptied buffer rather than "
                     "inline. The `with` keeps the same `ident`, so identity is "
                     "preserved (E1), the contents become empty (E4), and because "
                     "the precondition pins `callId = live.ident` the call "
                     "reference still observes the empty sequence (E5); the frames "
                     "E2/E3 are untouched. All five clauses discharge under the "
                     "frozen script; if it failed to verify the spec would be "
                     "SPEC-TOO-STRONG on impl shape. (Sibling: pos-control-discard.)",
    },
    {
        "id": "pos-control-explicit-ident",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: name the preserved identity token EXPLICITLY in the new buffer
        # literal (`ident := c.live.ident`) rather than riding it through `with`.
        # Observationally identical: same token, empty contents.
        "module": _impl(
            "    -- impl-start\n"
            "    c := { c with live := { ident := c.live.ident, contents := [] } }\n"
            "    return\n"
            "    -- impl-end"),
        "rationale": "a correct reshape that constructs the new buffer literal "
                     "explicitly, carrying the SAME identity token "
                     "(`ident := c.live.ident`) and empty contents. Identity is "
                     "preserved by construction (E1), the sequence is empty (E4/E5), "
                     "and the frames hold (E2/E3), so all five clauses discharge "
                     "under the frozen script. A faithful reshape MUST verify, else "
                     "the identity clause is over-fit to the `with`-record FORM => "
                     "SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — this method HAS a precondition (`callId = live.ident`), so
    # the sibling's "a normal input satisfies the precondition" probe ports
    # directly, re-aimed to also show non-degeneracy on a total domain. This case
    # discharges an in-region `assert` that the F2P-shaped input (the call
    # reference ALIASING the live buffer, with a genuinely NON-EMPTY live sequence
    # so the clear is a real transition, not a no-op) satisfies the alias invariant
    # and is non-degenerate. The surrounding impl and the byte-identical five
    # clauses are kept verbatim so the method's own obligation still discharges;
    # the assert is LIVE (a false claim leaves an unsolved goal — confirmed
    # out-of-band).
    # =====================================================================
    {
        "id": "admiss-f2p-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_assert(
            "    assert (with_name_prefix `adm\n"
            "      (({ live := ⟨7, [3, 4]⟩, callId := 7, callSnap := [] } : Capture).callId\n"
            "         = ({ live := ⟨7, [3, 4]⟩, callId := 7, callSnap := [] } : Capture).live.ident\n"
            "       ∧ ({ live := ⟨7, [3, 4]⟩, callId := 7, callSnap := [] } : Capture).live.contents ≠ []))\n"),
        "rationale": "the precondition admits the F2P-shaped input and it is "
                     "non-degenerate: the per-phase call reference ALIASES the live "
                     "buffer (`callId = live.ident`, the post-setup invariant) and "
                     "the live sequence is genuinely NON-EMPTY ([3,4] ≠ []), so the "
                     "clear is a real state transition (not a vacuous no-op on an "
                     "already-empty buffer). The in-region assert must discharge "
                     "(else the interesting input is excluded / PRECOND-TOO-STRONG "
                     "at the point that matters); the impl and five clauses are kept "
                     "verbatim so E1..E5 still discharge too. (Sibling: "
                     "pos-control-discard's embedded admissibility Assert.)",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Witnesses vary the sub-fields
    # of the single `mut` binder `c` (see footer BINDER / CLAUSE COVERAGE).
    # =====================================================================
    {
        "id": "rebind-orphans-discard",
        "kind": "uniqueness",
        "expect": "reject",
        # THE BUG. Empty by REPLACING the live buffer with a fresh object (a new
        # identity token) instead of emptying in place. Emptiness (E4) holds, but
        # the fresh object breaks the identity frame (E1) and, because the call
        # reference's bound identity no longer matches the fresh buffer's, the call
        # reference is orphaned and observes the stale snapshot (E5).
        "module": _impl(
            "    -- impl-start\n"
            "    c := { c with live := { ident := c.live.ident + 1, contents := [] } }\n"
            "    return\n"
            "    -- impl-end"),
        "refinement": "this IS the pre-patch behaviour: the record-buffer clear "
                      "REBINDS the list to a fresh one rather than emptying it in "
                      "place, so the per-phase 'call' reference stored at phase "
                      "preparation is orphaned — it keeps pointing at the OLD "
                      "detached list. The failing test logs a record, clears, then "
                      "asserts the per-phase 'call' observation is empty AND that a "
                      "record logged after the clear is visible through it; with the "
                      "rebind the orphaned reference still shows the pre-clear "
                      "records and never sees the post-clear record, so the test "
                      "FAILS. Its faithful real patch (the un-patched rebinding "
                      "clear) is exactly what does NOT resolve.",
        "rationale": "REJECT from E1 (`c.live.ident = cOld.live.ident`) and, "
                     "consequently, E5 (`callRecords c = []`): the fresh buffer has "
                     "a DIFFERENT identity token, breaking the identity frame; and "
                     "because `callId` still names the OLD identity, `callRecords` "
                     "falls through to the stale `callSnap` and is non-empty. "
                     "Emptiness alone (E4) is satisfied, so E1/E5 are the "
                     "discriminating clauses. If this verified the spec would admit "
                     "the pre-patch bug => SPEC-TOO-WEAK. Refuted at a buffer whose "
                     "snapshot is non-empty ([7]) so the orphaned call reference is "
                     "observably wrong.",
        "witness": _tester(
            "example : clearCaptureTester ⟨⟨0, [1]⟩, 0, [7]⟩ = false := by\n"
            "  decide\n"),
    },
    {
        "id": "clear-then-rebind-discard",
        "kind": "uniqueness",
        "expect": "reject",
        # Do the real work (empty in place) but THEN throw away identity by
        # rebinding to a fresh empty buffer. Observationally identical to the plain
        # rebind: the live field ends up naming a NEW object. A "looks like it did
        # the work" variant of the rebind bug.
        "module": _impl(
            "    -- impl-start\n"
            "    c := { c with live := { c.live with contents := [] } }\n"
            "    c := { c with live := { ident := c.live.ident + 1, contents := [] } }\n"
            "    return\n"
            "    -- impl-end"),
        "refinement": "empties in place (the real work) but then rebinds to a fresh "
                      "buffer, so the live field points at a NEW object and the "
                      "previously-handed-out per-phase reference is orphaned exactly "
                      "as in rebind-orphans. The failing test never sees the "
                      "post-clear record through the stale reference; doing the work "
                      "and then discarding identity does NOT resolve.",
        "rationale": "REJECT from E1 (`c.live.ident = cOld.live.ident`) and E5: the "
                     "FINAL live buffer is a fresh object distinct from "
                     "`cOld.live.ident`, so the identity frame fails and the call "
                     "reference is orphaned (E5 falls through to the stale "
                     "snapshot). Refuted at a DIFFERENT input point from "
                     "rebind-orphans (ident 5, a length-3 live sequence, snapshot "
                     "[9]) so it does not merely reuse the other rival's point.",
        "witness": _tester(
            "example : clearCaptureTester ⟨⟨5, [1, 2, 3]⟩, 5, [9]⟩ = false := by\n"
            "  decide\n"),
    },
    {
        "id": "noop-discard",
        "kind": "uniqueness",
        "expect": "reject",
        # Leave the buffer untouched. Identity is trivially preserved (E1/E2/E3
        # hold, and E5 holds when the buffer is already empty) but emptiness fails
        # whenever the buffer held >= 1 record on entry (the F2P clears a non-empty
        # sequence).
        "module": _impl(
            "    -- impl-start\n"
            "    return\n"
            "    -- impl-end"),
        "refinement": "a clear that does nothing keeps identity (so it passes the "
                      "identity frame) but leaves the captured records in place. The "
                      "failing/related tests log a record before clear and assert "
                      "the observation is empty AFTER clear; a no-op clear leaves the "
                      "pre-existing records visible, so those assertions FAIL. A "
                      "no-op patch does not resolve.",
        "rationale": "REJECT from E4 (`liveRecords c = []`) and E5 on the NON-EMPTY "
                     "sub-domain the F2P exercises: doing nothing leaves the "
                     "pre-existing records in the sequence. The identity frames hold, "
                     "so E4/E5 are the sole failing clauses. Refuted at a non-empty "
                     "live sequence ([3,4]) with an empty snapshot so `callRecords` "
                     "reads the live (non-empty) contents.",
        "witness": _tester(
            "example : clearCaptureTester ⟨⟨2, [3, 4]⟩, 2, []⟩ = false := by\n"
            "  decide\n"),
    },
    {
        "id": "rebind-only-when-already-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # ADDED BY AUDIT. A sub-domain-selective rebind: empty in place on the
        # NON-EMPTY branch (so every other reject witness's input point, all of
        # which have a non-empty live sequence, is handled CORRECTLY here), and
        # rebind to a fresh object only when the live sequence is already empty.
        # Every pre-existing rival is wrong on the non-empty sub-domain, so none
        # of them constrains the already-empty one; this one does.
        "module": _impl(
            "    -- impl-start\n"
            "    if c.live.contents = [] then\n"
            "      c := { c with live := { ident := c.live.ident + 1, contents := [] } }\n"
            "    else\n"
            "      c := { c with live := { c.live with contents := [] } }\n"
            "    return\n"
            "    -- impl-end"),
        "refinement": "a clear that only rebinds when the record sequence is "
                      "ALREADY empty still orphans the per-phase reference — just on "
                      "a narrower entry state. Clearing twice in a row, or clearing "
                      "before anything has been logged, is an ordinary thing for a "
                      "test to do, and after it the per-phase observation is detached "
                      "from the live sequence, so a record logged afterwards is never "
                      "visible through it and the assertion that the two agree FAILS. "
                      "Being correct on the non-empty entry state does not resolve.",
        "rationale": "REJECT from E1 (`c.live.ident = cOld.live.ident`) and E5, on "
                     "the ALREADY-EMPTY sub-domain that no other rival reaches: this "
                     "impl is deliberately CORRECT wherever `live.contents ≠ []`, so "
                     "every other reject witness point (all non-empty) verifies "
                     "against it and only an empty-sequence input refutes it. That "
                     "makes it the sole attacker of the empty sub-domain — the "
                     "boundary the F2P's repeated `verify_consistency()` calls sit on "
                     "before anything is logged. Refuted at ⟨⟨8,[]⟩, 8, [5]⟩: empty "
                     "live sequence (taking the buggy branch) with a NON-EMPTY "
                     "snapshot [5], so the orphaned call reference is observably "
                     "non-empty and E5 fails alongside E1.",
        "witness": _tester(
            "example : clearCaptureTester ⟨⟨8, []⟩, 8, [5]⟩ = false := by\n"
            "  decide\n"),
    },
    {
        "id": "mutate-callid-frame",
        "kind": "uniqueness",
        "expect": "reject",
        # Empty correctly (E1/E4 hold) but perturb the read-only call-reference
        # identity `callId`. This desynchronises the alias: after the write
        # `callId ≠ live.ident`, so the call reference falls through to the stale
        # `callSnap` (E5) AND the frame E2 fails.
        "module": _impl(
            "    -- impl-start\n"
            "    c := { c with live := { c.live with contents := [] }, callId := c.callId + 1 }\n"
            "    return\n"
            "    -- impl-end"),
        "refinement": "a faithful patch that re-pointed the per-phase 'call' "
                      "reference to a DIFFERENT buffer while clearing would break the "
                      "aliasing the test depends on: the observation would no longer "
                      "track the live buffer, so a record logged after the clear is "
                      "never seen through the per-phase reference and the test FAILS. "
                      "Re-binding the read-only reference does not resolve.",
        "rationale": "REJECT from E2 (`c.callId = cOld.callId`): the read-only "
                     "call-reference identity is a frame the clear must not perturb; "
                     "bumping it violates E2, and as a knock-on `callRecords` falls "
                     "through to the stale `callSnap`, so E5 fails TOO whenever that "
                     "snapshot is non-empty. E1/E3/E4 are kept correct, so E2 and E5 "
                     "are the failing clauses. Verifying would be SPEC-TOO-WEAK on "
                     "the call-reference frame. Refuted at a NON-EMPTY snapshot "
                     "([8]): with an empty snapshot the desynchronised alias would "
                     "still read `[]` and E5 would hold vacuously, leaving E2 as the "
                     "sole failing clause — machine-checked clause vectors "
                     "[E1..E5] at this rival are [T,F,T,T,F] at snapshot [8] versus "
                     "[T,F,T,T,T] at snapshot [], so the non-empty snapshot is what "
                     "makes the knock-on this rationale claims actually observable.",
        "witness": _tester(
            "example : clearCaptureTester ⟨⟨3, [1]⟩, 3, [8]⟩ = false := by\n"
            "  decide\n"),
    },
    {
        "id": "mutate-callsnap-frame",
        "kind": "uniqueness",
        "expect": "reject",
        # Empty correctly (E1/E4/E5 hold on entry) but perturb the read-only
        # detached snapshot `callSnap`. Isolates E3: the snapshot frame is the only
        # failing clause.
        "module": _impl(
            "    -- impl-start\n"
            "    c := { c with live := { c.live with contents := [] }, callSnap := 99 :: c.callSnap }\n"
            "    return\n"
            "    -- impl-end"),
        "refinement": "the detached snapshot is a read-only aspect of the capture "
                      "state; a faithful patch that mutated it during the clear would "
                      "corrupt what a DETACHED per-phase reference would expose for an "
                      "earlier phase, so any test reading a prior phase's records "
                      "would observe a fabricated entry and FAIL. Perturbing the "
                      "read-only snapshot does not resolve.",
        "rationale": "REJECT from E3 (`c.callSnap = cOld.callSnap`): the read-only "
                     "snapshot is a frame the clear must leave unchanged; prepending "
                     "an element violates E3. E1/E2/E4/E5 are kept correct (the live "
                     "buffer is emptied in place and, since `callId = live.ident`, "
                     "`callRecords` reads the emptied live contents regardless of the "
                     "snapshot), so E3 is the SOLE failing clause — a clean isolation "
                     "of the snapshot frame no other rival attacks.",
        "witness": _tester(
            "example : clearCaptureTester ⟨⟨6, [1]⟩, 6, []⟩ = false := by\n"
            "  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 9 SPEC cases (2 soundness
# positives, 5 uniqueness rivals, 2 of which are divergence rivals) plus a 2-case
# AXIOM lane, contracting TWO functions (`discard_captured` and
# `append_then_visible`) over a permission-bearing shared list aliased by an
# observer reference `view`. This bundle models the NARROWER purely-functional
# core — the clear path alone (`clearCapture`), over a `Capture` structure whose
# `Buffer.ident` makes object identity an OBSERVABLE VALUE — and folds the
# observer-aliasing into `callId`/`callSnap`. The value/identity surface carries
# across; the permission surface and the second (append) function do not exist on
# this cell. Every sibling case is accounted for below.
#
#   sibling case (nagini)          -> here                              disposition
#   ---------------------------------------------------------------------------
#   pos-control-discard            -> pos-control-local-emptied         PORTED
#   (structural 2nd shape)         -> pos-control-explicit-ident        ADDED
#   (embedded admissibility Assert)-> admiss-f2p-shape                  RE-AIMED
#   rebind-orphans-discard         -> rebind-orphans-discard            PORTED (central)
#   clear-then-rebind-discard      -> clear-then-rebind-discard         PORTED
#   noop-discard                   -> noop-discard                      PORTED
#   recursion-discard              -> (none)                            VACUOUS (total sem.)
#   empty-then-recurse-discard     -> (none)                            VACUOUS (total sem.)
#   pos-control-append             -> (none)                            NOT MODELED (append fn)
#   wrongval-append                -> (none)                            NOT MODELED (append fn)
#   rebind-append                  -> (none)                            NOT MODELED (append fn)
#   AXIOM_TESTS (2)                -> (none)                            DROPPED (G-AX)
#   + mutate-callid-frame / mutate-callsnap-frame                       ADDED (E2/E3)
#   + rebind-only-when-already-empty                                    ADDED (audit)
#
# PORTED (pos-control-local-emptied): the sibling empties the list through a local
#   alias of the field; the analogue here empties through a LOCAL binding of the
#   emptied buffer (`with` preserves `ident`). ADDED (pos-control-explicit-ident):
#   a second correct shape that names the preserved identity token explicitly in
#   the new buffer literal — guards against the identity clause being over-fit to
#   the `with`-record form. Both verified with real builds under the frozen proof.
# RE-AIMED (admiss-f2p-shape): the sibling embeds `Assert(view is buf.items)` as an
#   admissibility witness inside its positive control. Here it is a first-class
#   admissibility case: an in-region `assert` that the F2P-shaped input satisfies
#   the alias precondition (`callId = live.ident`) AND is non-degenerate (a genuinely
#   NON-EMPTY live sequence, so the clear is a real transition). loom_solve + a
#   `decide` arm discharges the VC; the impl and five clauses are kept verbatim.
# PORTED (rebind-orphans-discard): the central prepatch bug (rebind to a fresh
#   object, orphaning the observer reference) ports directly and is the headline
#   reject, refuted by the identity frame E1 (which nagini spells as
#   `buf.items is Old(buf.items)`) and its knock-on E5. PORTED
#   (clear-then-rebind-discard, noop-discard): the "do the work then discard
#   identity" and the no-op both port directly; on this carrier they are refuted by
#   E1/E5 and E4/E5 respectively, with witnesses that `decide` outright.
# ADDED (mutate-callid-frame, mutate-callsnap-frame): the sibling's frame concern
#   is stated in prose ("view carries the aliasing constraint; there is no
#   half-permission read-only input"). On this carrier the read-only aspects are
#   FIRST-CLASS spec clauses — E2 (`callId`) and E3 (`callSnap`) — so two rivals
#   attack them directly (bump the call-reference identity; prepend to the detached
#   snapshot). These give E2 and E3 the dedicated attackers the coverage tool
#   demands; mutate-callsnap-frame isolates E3 as the SOLE failing clause.
# VACUOUS (recursion-discard, empty-then-recurse-discard): the sibling's two
#   divergence rivals are guarded by `Requires(MustTerminate(2))`. This bundle sets
#   `loom.semantics.termination "total"`, under which a postcondition is claimed of
#   ALL runs and every loop must carry a decreasing measure. (The earlier version of
#   this note called the cell one of "the 99 total-semantics velvet bundles" against
#   "the 401 `partial` bundles where divergence is a known spec hole", citing an
#   internal findings doc; that census is withdrawn, since all 500 velvet bundles now
#   read "total".) A diverging body is refused by the decreasing obligation -- an
#   unmeasured loop at elaboration, and a loop carrying a NON-decreasing measure on
#   the measure's own goal (`case «decreasing_1: q»`, residual `q < q`). The frozen
#   body here is straight-line, so no divergence rival is SHIPPED; the further
#   claim that "a non-terminating body cannot even be written" is withdrawn, since
#   a rival owns the whole impl region and the two measurements just quoted were
#   taken on exactly such a spliced loop. So there is nothing to port and NO known
#   hole to record on this cell. (The `partial` counterfactual is dropped: no
#   velvet bundle sets `partial`, so the vacuous-admission disposition has no
#   referent in this corpus.)
# NOT MODELED (pos-control-append, wrongval-append, rebind-append): the sibling's
#   second contracted function `append_then_visible` — a subsequently captured item
#   is visible through the still-aliased view — is NOT part of this bundle's modeled
#   carrier. The Lean-family bundle models only the CLEAR path (`clearCapture`);
#   there is one `method`/one `prove_correct`, and the append behaviour has no
#   counterpart here. This is carrier narrowing (the porting map's "most nagini
#   cases attached to an unmodeled behaviour have no counterpart"), NOT an omission
#   for difficulty: fabricating an append rival would require a second method this
#   bundle does not contract.
# DROPPED (AXIOM_TESTS): the two axiom-lane cases validate the sibling's
#   `empty_in_place` A-consumed axiom (== real `list.clear()`) against the real
#   builtin. This bundle declares NO axioms and NO deep-model references
#   (mapping.md §3: the clear is modeled deeply as `{ c.live with contents := [] }`;
#   every step is R or I), so there is nothing to probe — and this gate ignores
#   AXIOM_TESTS regardless.
#
# BINDER / CLAUSE COVERAGE. The obligation has ONE `mut` input binder `c`, whose
#   sub-fields the reject witnesses vary, and FIVE independent clauses. Every
#   clause is DEFENDED (the two positive controls + admissibility all verify) and
#   ATTACKED:
#   * E1 (`c.live.ident = cOld.live.ident`) by rebind-orphans and clear-then-rebind
#                                            (non-empty entry) and
#                                            rebind-only-when-already-empty (the
#                                            EMPTY entry sub-domain);
#   * E2 (`c.callId = cOld.callId`)          by mutate-callid-frame;
#   * E3 (`c.callSnap = cOld.callSnap`)      by mutate-callsnap-frame (sole failing
#                                            clause — a clean isolation);
#   * E4 (`liveRecords c = []`)              by noop-discard;
#   * E5 (`callRecords c = []`)              never ALONE — it is entailed by
#                                            require+E1+E2+E4 (see header), so it
#                                            co-fails with E1 (rebind-orphans,
#                                            clear-then-rebind,
#                                            rebind-only-when-already-empty), with
#                                            E4 (noop-discard), or with E2
#                                            (mutate-callid-frame).
#   The six reject witnesses probe SIX DISTINCT input points (pts=6):
#     ⟨⟨0,[1]⟩, 0, [7]⟩        rebind-orphans        (E1/E5; non-empty snapshot)
#     ⟨⟨5,[1,2,3]⟩, 5, [9]⟩    clear-then-rebind     (E1/E5; ident 5, len-3 live)
#     ⟨⟨2,[3,4]⟩, 2, []⟩       noop-discard          (E4/E5; non-empty live)
#     ⟨⟨8,[]⟩, 8, [5]⟩         rebind-only-when-...  (E1/E5; EMPTY live — the only
#                                                     witness on that sub-domain)
#     ⟨⟨3,[1]⟩, 3, [8]⟩        mutate-callid-frame   (E2/E5; non-empty snapshot, so
#                                                     the knock-on is observable)
#     ⟨⟨6,[1]⟩, 6, []⟩         mutate-callsnap-frame (E3; ident 6)
#   `live.ident`/`callId` are varied over {0,5,2,8,3,6} (always equal — the pinned
#   precondition alias, so the tester is not vacuous), `live.contents` over
#   {[1],[1,2,3],[3,4],[],[1],[1]} (non-empty where the clear must be a real
#   transition, and EMPTY at the one point that probes the boundary sub-domain), and
#   `callSnap` over {[7],[9],[],[5],[8],[]} (non-empty at every point where a rival
#   orphans or desynchronises the reference, which is what makes E5 observably wrong
#   rather than vacuously true there). No two rivals share an input tuple.
#   VARIATION IS MEANINGFUL, not two spellings of one point: the machine-checked
#   clause vectors [E1..E5] at each rival's own witness differ —
#   [F,T,T,T,F] (rebind-orphans), [F,T,T,T,F] at a different ident/length
#   (clear-then-rebind), [T,T,T,F,F] (noop), [F,T,T,T,F] on the empty sub-domain
#   where the other three rivals are CORRECT (rebind-only-when-already-empty),
#   [T,F,T,T,F] (mutate-callid), [T,T,F,T,T] (mutate-callsnap).
#   Each witness was SEEN to discriminate: it ELABORATES against the rival (exit 0)
#   and FAILS against the frozen solution (exit 1), confirmed with two real builds
#   each, and the gold-side failure is in every case a SEMANTIC refutation —
#   `decide` fully reduces the tester on gold and reports "proved that the
#   proposition ... = false is false", not a stuck reduction, unknown identifier, or
#   type error. No witness binds a hypothesis (the carrier is fully transparent —
#   all fields are concrete `Nat`/`List Nat` literals), so there is no
#   joint-satisfiability obligation. No `sorry`/`admit`/`native_decide`/`axiom`
#   appears in any witness.
#
# AUDIT PROBES that found no hole (recorded so the next reader need not redo them).
#   Wrong impls beyond the shipped rivals, each built against the frozen spec and
#   each REJECTED (exit 1): drop only the first record instead of emptying
#   (`contents.drop 1`); overwrite the snapshot with the pre-clear contents;
#   erase the snapshot; rebind the buffer AND re-point `callId` at the fresh object
#   (the "repair the alias too" cheat, which keeps E5 true and still fails E1/E2).
#   Correct reshapes beyond the shipped positives, each VERIFYING (exit 0):
#   `Buffer.mk c.live.ident []`; a guard that returns early when the sequence is
#   already empty (genuinely different control flow); destructure-and-rebuild
#   through a named `ident` local. Consistent with post_state_unique above: the
#   contract pins every field, so no wrong impl can verify and no faithful reshape
#   is refused. The admissibility assert is LIVE, not decorative: the same case
#   with `contents = []` substituted for `contents ≠ []` FAILS (exit 1,
#   `unsolved goals ... ⊢ [3, 4] = []`), so `decide` is discharging a real claim.
#   The docstring's vacuity note is also confirmed: `clearCaptureTester` is TRUE at
#   a precondition-VIOLATING input (`⟨⟨0,[1]⟩, 99, [7]⟩`) against BOTH gold and the
#   rebind rival (exit 0 both), so such a witness would discriminate nothing —
#   which is why every witness pins `callId = live.ident`.
AXIOM_TESTS = []
