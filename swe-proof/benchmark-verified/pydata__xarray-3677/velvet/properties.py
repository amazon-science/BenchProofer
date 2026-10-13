"""properties.py — G-PBT falsification battery for pydata__xarray-3677 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes and
stamps with a verdict. Each SPEC case is a full ``Solution.lean`` variant that
shares the FROZEN spec byte-for-byte (region surgery: only text inside the
``-- impl-start`` / ``-- impl-end`` region, or inside the ``prove_correct``
tactic body, is changed — both of which the consumer spec view elides, so
``markers.same_spec`` holds and the ``prove_correct combineKeyed`` obligation
survives with a byte-identical statement) and swaps in a candidate
implementation; it is judged by the real verifier. ``expect:"verify"`` passes
iff (in scope AND verifies); ``expect:"reject"`` passes iff (in scope AND does
NOT verify AND its refutation ``witness`` discriminates — the witness must
ELABORATE against the rival and FAIL against the frozen solution).

DEFENDED SURFACE (one contracted method: normalize-then-combine two collections):

    combineKeyed (base : KeyedMap) (other : Operand)
                 return (out : Except CombineErr KeyedMap)
      ensures out = combineSpec base other

``combineSpec base other`` is a total, fully-unfolded pure function of the two
inputs: normalize ``other`` into a key→value collection (a lone keyed value is
re-expressed as a one-entry collection; a collection passes through) and then
hand it to the core combine, which fuses the base entries with the operand's
entries (base first). It is spelled out in the spec-view ``pure`` region
(``combineSpec`` / ``coerceOperand`` / ``combineCore`` / ``combineEntries``): it
is NOT an opaque answer key — it computes over the actual input carrier. The
single load-bearing ``ensures`` clause pins the WHOLE result: that the combine
SUCCEEDS on both operand shapes (``.ok``, never ``.error``), that its entries are
the union ``base ++ es`` (base entries present, operand entries present, in that
order), and — the discriminating property of the fix — that a lone keyed value
(``.single``) is FIRST re-expressed so the combine reaches it at all instead of
failing.

The two inputs ``base`` and ``other`` are both FREE (no ``require`` clause), so
the ``ensures`` holds for EVERY value of each. The bundle runs under
``set_option loom.semantics.termination "total"``.

ADVERSARIAL READ of the nagini classes on this carrier:
  * SOUNDNESS / positive controls — APPLY. Structurally different but
    behaviourally identical impls (report the closed form the post-image names
    directly; call the normalizer ``coerceOperand`` by name instead of inlining
    its ``match``; reorder the two normalization arms) must still verify, else
    the spec is SPEC-TOO-STRONG on the shape of the impl.
  * ADMISSIBILITY — the nagini sibling's admissibility witness constructs the
    F2P-shaped operands and asserts the read-only FRACTIONAL-PERMISSION
    precondition holds for them. This method carries NO ``require`` clause and no
    heap permission, so the permission half of that probe has no counterpart.
    The lane is NOT vacuous for it: the analogue on a total carrier is the
    obligation being UNSATISFIABLE at exactly an F2P-shaped input, which a
    positive that DISCHARGES the obligation at that concrete input — by
    evaluation, as a ``have``, before closing the frozen obligation verbatim —
    tests directly. That is ``admiss-f2p-shaped-input``.
  * FRAME / PERMISSION-MUTATION — VACUOUS on this backend. The nagini sibling
    holds ``receiver`` and ``other`` at fractional heap permissions
    (``Acc(., 1/2)``) an impl can illegally overwrite, and ships two mandatory
    rivals that mutate a read-only input (``other.is_mapping = True`` /
    ``receiver.value = 0``), rejected for INSUFFICIENT PERMISSION. Lean and Velvet
    are referentially transparent: ``base`` and ``other`` are immutable values
    (neither declared ``mut``), there is no heap, aliasing, or permission system
    to subvert, so there is no read-only input to overwrite. No substitute probe
    is fabricated — reported as an omission in the footer.
  * DIVERGENCE / non-termination - the class is INAPPLICABLE to this impl and
    CLOSED BY THE SEMANTICS against any rival that manufactures it. The frozen
    impl is LOOP-FREE (straight-line ``let`` over immutable values, no loop and
    no recursion), so there is no control flow here to make diverge: a
    diverging rival cannot be obtained by mutating this body, it has to bring a
    loop of its own. When it does, the semantics refuse it. This bundle sets
    ``loom.semantics.termination "total"`` AND carries
    ``open TotalCorrectness``, and the ``open`` is the line that actually
    selects the semantics: both namespaces define
    ``WPGen.forWithInvariantLoop``, the later ``open`` wins, and the
    ``PartialCorrectness`` version takes a loop measure and DISCARDS it, so the
    two lines have to move together and they do here. Under the total scope a
    postcondition is claimed of ALL runs and not only of terminating ones, so a
    spliced loop owes a descent obligation ``measure b' < measure b``.
    Re-measured on this bundle with a real build: a
    ``while spin > 0 do spin := spin`` prefix carrying ``decreasing spin`` is
    REJECTED on the measure's own goal (``case «decreasing_1: spin» ... ⊢ spin
    < spin``). Dropping the clause rather than faking it is refused even
    earlier, by the elaborator's own check (``Decreasing annotations are
    required in total correctness semantics``). So divergence neither applies
    to this impl nor discharges the ``ensures`` clauses vacuously if a rival
    introduces it.
  * UNIQUENESS / SPEC-TOO-WEAK rivals — the heart of this port. Wrong impls that
    diverge from the desired normalize-then-combine on some sub-domain and MUST be
    rejected: the headline pre-patch bug (feed a lone keyed value to the combine
    UNNORMALIZED, so it fails), losing the base entries, losing the operand
    entries, normalizing a lone keyed value to an EMPTY collection (dropping its
    single entry), fusing the two collections in the REVERSED order, and fusing
    the operand's entries TWICE. The last two matter because they satisfy
    membership on both legs and break only the fused sequence's ORDER and
    MULTIPLICITY — without them the union clause would be probed only as a set.
    Each is a loop-free closed form whose extracted program ``combineKeyedExec``
    REDUCES under ``decide``, with a machine-checked refutation witness at a
    concrete input.

WITNESS MECHANICS (specific to this carrier). The spec is a ``method`` CONTRACT,
so a witness must reach the postcondition. The tester path
(``derive_tester_for`` → ``combineKeyedTester … = false := by decide``) is DEAD
here: ``prove_postcondition_decidable_for`` yields a ``Decidable (out =
combineSpec base other)`` instance that does NOT kernel-reduce (measured: the
tester ``decide`` gets stuck for BOTH a wrong rival and gold, discriminating
nothing). But the post-image ``combineSpec`` is fully TRANSPARENT, so every
witness instead extracts the executable program (``extract_program_for`` →
``combineKeyedExec``) and refutes the ``ensures`` directly: at one concrete
input, the rival's own output DIFFERS from ``combineSpec``. The result type
``Except CombineErr KeyedMap`` has no ``DecidableEq`` instance, so both sides are
projected through ``.toOption`` (``Option KeyedMap``, which does), and the
inequality is closed by ``decide``. Against the frozen solution the SAME
statement fails — gold satisfies the ``ensures`` at every input, so
``combineKeyedExec`` agrees with ``combineSpec`` and ``decide`` proves the
inequality FALSE — exactly the discrimination the gate requires. No witness binds
a hypothesis (every input is a concrete literal), so no consistency probe is
needed. No banned token (sorry/admit/native_decide/axiom/opaque). Each witness
was checked out of band with ``scripts/lean_verify.sh``: every one ELABORATES
against its rival (exit 0) and FAILS against gold (a ``decide`` error).

AXIOM lane: dropped. ``AXIOM_TESTS = []``. The nagini file carries axiom-
soundness / containment probes over the real conversion callee; that is G-AX's
job (axiom_check.py / mapping.md — here the core combine is modeled DEEPLY as an
A-reference, not consumed as an axiom) and the G-PBT gate ignores ``AXIOM_TESTS``
regardless.
"""
from pathlib import Path

INSTANCE = "pydata__xarray-3677"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors. Each lies wholly inside the impl region (between -- impl-start and
# -- impl-end) or is the prove_correct tactic body, and each is unique in
# Solution.lean; both facts are asserted at load time by _swap. Editing only
# these keeps markers.same_spec True and the prove_correct statement byte-
# identical (the spec view elides both regions).
# ---------------------------------------------------------------------------

# The WHOLE executable body of the method: the inline normalize-then-combine.
# Every variant replaces exactly this text.
_IMPL = (
    "    -- An operand that is a lone keyed value, not a key→value collection, is\n"
    "    -- first re-expressed as a one-entry collection so the core combine — which\n"
    "    -- consumes key/value pairs — can process it; a collection passes through.\n"
    "    let other' : Operand :=\n"
    "      match other with\n"
    "      | .single k v => Operand.keyed (asKeyed k v)\n"
    "      | .keyed es   => Operand.keyed es\n"
    "    let out := combineCore base other'\n"
    "    return out"
)

# The frozen proof body, verbatim. Loop-free reshapes whose residual goal no
# longer closes under `loom_solve` alone retune THIS block (elided from the spec
# view). Reject rivals leave it as-is — the rejection is carried by the witness,
# not the tactic script.
_PROOF = "prove_correct combineKeyed by\n  loom_solve\n"

assert _BASE.count(_IMPL) == 1, "method impl region drifted from expected text"
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(body: str) -> str:
    """Solution.lean with ONLY the impl body replaced (spec view untouched)."""
    return _swap(_BASE, _IMPL, body)


def _impl_reproved(body: str, proof: str) -> str:
    """Impl body replaced AND the proof retuned (for reshapes whose residual
    goal no longer closes under the frozen tactic alone)."""
    return _swap(_impl(body), _PROOF, proof)


# ---- witness preamble + builder. The tester+`decide` path is dead here (the
# ---- postcondition's Decidable instance does not kernel-reduce), so extract the
# ---- executable program and refute the ensures directly against the TRANSPARENT
# ---- `combineSpec`. `Except CombineErr KeyedMap` has no DecidableEq, so both
# ---- sides are projected through `.toOption`. Checked in a file whose
# ---- `prove_correct` block is stripped, so no tactic script can mask the verdict.
def _witness(base_v: str, other_v: str) -> str:
    return (
        "extract_program_for combineKeyed\n\n"
        "example :\n"
        f"    (match combineKeyedExec ({base_v}) ({other_v}) with\n"
        "     | DivM.res r => r.toOption | _ => none)\n"
        f"      ≠ (combineSpec ({base_v}) ({other_v})).toOption := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Each keeps the `ensures out = combineSpec base other`
    # obligation and only reshapes the executable surface.
    # =====================================================================
    {
        "id": "pos-closed-form",
        "kind": "soundness",
        "expect": "verify",
        # Report the closed form the post-image names DIRECTLY: no inline
        # normalization match, just `combineSpec base other`. A maximally
        # different (fully collapsed) impl computing the same result. Because
        # `combineSpec` is GROUNDED in the inputs (fully unfolded in the spec
        # view), returning it directly is the cheapest CORRECT impl, not a wrong
        # echo of an opaque oracle — any impl that mishandled the normalization or
        # the union would fail `out = combineSpec base other`. The frozen proof
        # closes it as-is (the impl now matches the post-image syntactically).
        "module": _impl(
            "    let out := combineSpec base other\n"
            "    return out"),
        "rationale": (
            "the post-image `combineSpec base other` is GROUNDED in the inputs (a "
            "total pure function, fully unfolded in the spec view, no opaque answer "
            "key), so returning it directly is the honest cheapest CORRECT impl; "
            "the single ensures is literally `out = combineSpec base other`, so it "
            "MUST verify, else SPEC-TOO-STRONG. Doubles as proof the spec is not "
            "echo-vulnerable: any impl that mishandled the normalization or the "
            "union fails `out = combineSpec base other`. Re-expresses the nagini "
            "pos-control-ifelse (a behaviourally-identical restructure of the "
            "second-operand selection)."
        ),
    },
    {
        "id": "pos-coerce-named",
        "kind": "soundness",
        "expect": "verify",
        # Call the normalizer `coerceOperand` by NAME instead of inlining its
        # `match` on `other`, then hand the result to the core combine. Same value
        # flow (`coerceOperand other` is definitionally the inlined match), a
        # different impl shape (delegated vs inlined). The residual goal
        # `combineCore base (coerceOperand other) = combineSpec base other` closes
        # by `rfl` (combineSpec IS that composition), so the proof gains one `rfl`.
        "module": _impl_reproved(
            "    let out := combineCore base (coerceOperand other)\n"
            "    return out",
            "prove_correct combineKeyed by\n  loom_solve\n  rfl\n"),
        "rationale": (
            "a correct impl with a DIFFERENT shape — delegate to the named "
            "normalizer `coerceOperand` rather than inline its match — computes the "
            "same combine, so `out = combineSpec base other` still holds; the "
            "residual goal closes by `rfl` (combineSpec is that composition). Ports "
            "the nagini pos-control-listfirst (a data-shape reshape of the same "
            "selection). If it fails => SPEC-TOO-STRONG (over-fit to the inlined "
            "match form)."
        ),
    },
    {
        "id": "pos-arm-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reorder the two normalization match arms (`.keyed` first, `.single`
        # second). Same value flow, a different branch order; the frozen proof
        # closes it unchanged.
        "module": _impl(
            "    let other' : Operand :=\n"
            "      match other with\n"
            "      | .keyed es   => Operand.keyed es\n"
            "      | .single k v => Operand.keyed (asKeyed k v)\n"
            "    let out := combineCore base other'\n"
            "    return out"),
        "rationale": (
            "reorder the normalization match arms (collection branch first). A "
            "structurally-different control shape computing the identical "
            "normalize-then-combine, so `out = combineSpec base other` still holds "
            "and the frozen proof closes as-is. A correct reshape must verify (else "
            "SPEC-TOO-STRONG on the branch order)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — PORTED from the nagini admiss-f2p-shaped-input, re-aimed at
    # the analogue this total carrier has. The nagini case injects the F2P-shaped
    # operands INSIDE the impl region (elided from the spec view) and asserts the
    # function's Requires is establishable for them. This method has no `require`
    # and no heap permission, so the permission half has no counterpart — but the
    # lane is NOT thereby vacuous. The analogue on a total carrier is the
    # obligation being UNSATISFIABLE at exactly an F2P-shaped input: the case
    # below discharges the post-image at that concrete input BY EVALUATION, as a
    # `have` inside the impl region, and only then closes the frozen obligation
    # verbatim. If the post-image demanded something unreachable there — a
    # `.error`, or a union missing an entry — the `have` fails to reduce and the
    # case fails => PRECOND-TOO-STRONG / SPEC-UNSATISFIABLE at the very input the
    # change exists to serve.
    # =====================================================================
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        # The F2P-shaped input: a one-entry base collection combined with a LONE
        # KEYED VALUE under a distinct key. `have` pins the post-image's value
        # there CONCRETELY — success (`.ok`, not `.error`) carrying BOTH entries in
        # base-first order — discharged by `rfl`, i.e. by evaluation, not by a
        # restatement of the ensures. The gold body then runs unchanged over the
        # actual params and closes the frozen obligation under the frozen tactic.
        "module": _impl(
            "    -- Admissibility at an F2P-shaped input, discharged by evaluation:\n"
            "    -- a one-entry base collection combined with a LONE KEYED VALUE under\n"
            "    -- a distinct key. The post-image demands SUCCESS there (never\n"
            "    -- `.error`) carrying BOTH entries, base first. If it demanded\n"
            "    -- anything unreachable, this `have` would not reduce.\n"
            "    have _adm : combineSpec [(0, 0)] (Operand.single 1 1)\n"
            "        = Except.ok [(0, 0), (1, 1)] := by rfl\n"
            "    let other' : Operand :=\n"
            "      match other with\n"
            "      | .single k v => Operand.keyed (asKeyed k v)\n"
            "      | .keyed es   => Operand.keyed es\n"
            "    let out := combineCore base other'\n"
            "    return out"),
        "rationale": (
            "PRECOND-TOO-STRONG probe, re-aimed for a total carrier with an empty "
            "precondition: the residual risk is not an unsatisfiable `require` but "
            "an obligation that cannot be MET at an F2P-shaped input. The `have` "
            "discharges the post-image at that concrete input by EVALUATION — "
            "`combineSpec [(0,0)] (.single 1 1) = .ok [(0,0),(1,1)]` — so it pins "
            "three things the ensures must actually deliver there: the combine "
            "SUCCEEDS on a lone keyed value (`.ok`, not `.error`), the base entry "
            "survives, and the operand's entry is present, base first. It is not a "
            "restatement of the ensures (that would be `rfl` against itself); it is "
            "a computed value the spec is checked against. The frozen obligation is "
            "then closed verbatim over the free params. If the `have` failed to "
            "reduce, or the obligation could not be closed alongside it, the spec "
            "would be unsatisfiable at exactly the input the change serves."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each a loop-free closed form (so its `…Exec` reduces
    # under `decide`) with a machine-checked refutation witness at a concrete
    # input, and the refinement argument that its faithful real counterpart would
    # NOT resolve the F2P.
    # =====================================================================
    {
        "id": "rival-drop-conversion",
        "kind": "uniqueness",
        "expect": "reject",
        # THE headline pre-patch bug. Never normalize — hand `other` straight to
        # the core combine. On a lone keyed value (`.single`) the combine has no
        # key/value pairs to consume and FAILS (`.error .notKeyed`), where the
        # spec demands the SUCCESSFUL union of the re-expressed entry.
        "module": _impl(
            "    let out := combineCore base other\n"
            "    return out"),
        "refinement": (
            "this IS the pre-change behaviour: the operand is fed to the core "
            "combine unnormalized. Its faithful real counterpart is the unpatched "
            "repo, where a lone keyed value reaches the combine's key/value "
            "iteration with nothing to iterate and raises — exactly the reported "
            "crash. The failing test merges a receiver collection with a lone keyed "
            "value and asserts the union is produced; the unnormalized operand "
            "makes the combine fail instead, so it would NOT resolve. This is the "
            "exact defect the fix corrects (nagini uniq-drop-conversion)."
        ),
        "rationale": (
            "REJECT from `out = combineSpec base other`: on a `.single` operand "
            "`combineSpec` normalizes it and yields `.ok (base ++ [(k,v)])`, while "
            "the rival hands the raw `.single` to `combineCore` and yields `.error "
            ".notKeyed`. Refuted at base=[], other=.single 0 0. If it verified => "
            "SPEC-TOO-WEAK (admits the bug)."
        ),
        "witness": _witness("[] : List (Nat × Int)", "Operand.single 0 0"),
    },
    {
        "id": "rival-lose-base",
        "kind": "uniqueness",
        "expect": "reject",
        # Normalize correctly, but return ONLY the operand's entries — drop the
        # base entries from the union. Correct on an EMPTY base; diverges whenever
        # the base carries an entry (the receiver's own variables vanish).
        "module": _impl(
            "    let other' : Operand :=\n"
            "      match other with\n"
            "      | .single k v => Operand.keyed (asKeyed k v)\n"
            "      | .keyed es   => Operand.keyed es\n"
            "    let out : Except CombineErr KeyedMap :=\n"
            "      match other' with\n"
            "      | .keyed es   => Except.ok es\n"
            "      | .single _ _ => Except.error .notKeyed\n"
            "    return out"),
        "refinement": (
            "returns only the operand's entries, dropping the base collection's "
            "own entries from the union. A faithful real patch of this shape would "
            "discard the receiver's existing variables on merge; the failing test "
            "asserts the merged result contains BOTH the receiver's and the "
            "operand's entries, so with the base dropped it is missing the "
            "receiver's and would NOT resolve. A genuine partial-domain break — "
            "correct only when the base is empty."
        ),
        "rationale": (
            "REJECT from `out = combineSpec base other`: `combineSpec` fuses "
            "`base ++ es` (base first), so on a non-empty base the rival's "
            "base-omitting result diverges. Refuted at base=[(1,1)], "
            "other=.single 0 0 — a DISTINCT point from rival-drop-conversion "
            "(non-empty base, so this rival diverges while drop-conversion at this "
            "point would still fail the combine), varying the `base` binder. If it "
            "verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness("[(1,1)] : List (Nat × Int)", "Operand.single 0 0"),
    },
    {
        "id": "rival-lose-operand",
        "kind": "uniqueness",
        "expect": "reject",
        # Return ONLY the base entries — never combine in the operand at all.
        # Correct on an operand that contributes nothing; diverges whenever the
        # operand carries an entry (the merged-in value never appears).
        "module": _impl(
            "    let out : Except CombineErr KeyedMap := Except.ok base\n"
            "    return out"),
        "refinement": (
            "returns the base unchanged, never merging in the operand's entries. A "
            "faithful real patch of this shape would leave the receiver untouched "
            "on merge; the failing test asserts the merged result gains the "
            "operand's entry, so with the operand dropped it is missing that entry "
            "and would NOT resolve."
        ),
        "rationale": (
            "REJECT from `out = combineSpec base other`: `combineSpec` includes the "
            "operand's entries in the union, so on an operand carrying an entry the "
            "rival's base-only result diverges. Refuted at base=[], "
            "other=.keyed [(2,3)] — a distinct input point that also varies the "
            "`other` binder to a `.keyed` (collection) shape, so a rival "
            "mishandling only lone keyed values would be caught here. If it "
            "verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness("[] : List (Nat × Int)", "Operand.keyed [(2,3)]"),
    },
    {
        "id": "rival-coerce-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # Normalize a lone keyed value to an EMPTY collection instead of a
        # one-entry one, dropping its single (key, value). The combine SUCCEEDS
        # (so this is NOT the drop-conversion crash) but loses the operand's data.
        # A near-miss for drop-conversion: it agrees that a `.single` must be
        # re-expressed, but re-expresses it lossily.
        "module": _impl(
            "    let other' : Operand :=\n"
            "      match other with\n"
            "      | .single _ _ => Operand.keyed []\n"
            "      | .keyed es   => Operand.keyed es\n"
            "    let out := combineCore base other'\n"
            "    return out"),
        "refinement": (
            "re-expresses a lone keyed value as an EMPTY collection, so the combine "
            "succeeds but the operand's single entry is silently lost. A faithful "
            "real patch of this shape would convert the operand to a collection "
            "carrying no variables; the failing test asserts the merged result "
            "gains the operand's named entry, so with that entry dropped it would "
            "NOT resolve. A lossy-normalization near-miss for the headline bug "
            "(nagini uniq-rebuild-noop, the lossy-rebuild cheat): the combine "
            "reaches success but on the wrong entries."
        ),
        "rationale": (
            "REJECT from `out = combineSpec base other`: `combineSpec` re-expresses "
            "`.single k v` as the one-entry `[(k,v)]` and includes it in the union, "
            "so on a `.single` the rival's empty re-expression drops that entry and "
            "diverges. Refuted at base=[(1,1)], other=.single 5 7 — a fourth "
            "distinct input point (non-empty base, a `.single` with distinct "
            "key/value), so the `.single` re-expression is attacked at both the "
            "crash level (drop-conversion) and the data-loss level here. If it "
            "verified => SPEC-TOO-WEAK."
        ),
        "witness": _witness("[(1,1)] : List (Nat × Int)", "Operand.single 5 7"),
    },
    {
        "id": "rival-swap-order",
        "kind": "uniqueness",
        "expect": "reject",
        # Normalize correctly and keep BOTH sides' entries, but fuse them in the
        # WRONG ORDER — operand entries first, base second. The union clause pins
        # the order (`base ++ es`), which is what fixes precedence between the two
        # collections; this rival inverts it. Membership-only rivals miss this, so
        # it is the leg neither lose-base nor lose-operand reaches.
        "module": _impl(
            "    let other' : Operand :=\n"
            "      match other with\n"
            "      | .single k v => Operand.keyed (asKeyed k v)\n"
            "      | .keyed es   => Operand.keyed es\n"
            "    let out : Except CombineErr KeyedMap :=\n"
            "      match other' with\n"
            "      | .keyed es   => Except.ok (combineEntries es base)\n"
            "      | .single _ _ => Except.error .notKeyed\n"
            "    return out"),
        "refinement": (
            "fuses the two collections in the reversed order. Both sides' entries "
            "are present, so any membership-only reading of the union is satisfied; "
            "what breaks is PRECEDENCE between the receiver's own entries and the "
            "operand's. The failing test compares the merged result against the "
            "receiver-first combine of the same two operands, so a result assembled "
            "operand-first does not match it and would NOT resolve. Ports the "
            "nagini uniq-swap-order, whose operand-ordering attack the port had "
            "recorded as unmodeled on this carrier — it is expressible here, "
            "against the union clause's ORDER rather than a list position."
        ),
        "rationale": (
            "REJECT from `out = combineSpec base other`: `combineSpec` fuses "
            "`combineEntries base es = base ++ es`, base FIRST, so a rival "
            "returning `es ++ base` diverges wherever both sides are non-empty. "
            "Refuted at base=[(1,1)], other=.keyed [(2,3)] — both legs non-empty, "
            "which is exactly the regime the two membership rivals leave "
            "unattacked. If it verified => SPEC-TOO-WEAK on the union's order."
        ),
        "witness": _witness("[(1,1)] : List (Nat × Int)", "Operand.keyed [(2,3)]"),
    },
    {
        "id": "rival-dup-operand",
        "kind": "uniqueness",
        "expect": "reject",
        # Fuse the operand's entries TWICE. Every entry the union demands is
        # present (so membership passes) and the order is right; the multiplicity
        # is wrong. The near-miss for the union clause read as a set.
        "module": _impl(
            "    let other' : Operand :=\n"
            "      match other with\n"
            "      | .single k v => Operand.keyed (asKeyed k v)\n"
            "      | .keyed es   => Operand.keyed es\n"
            "    let out : Except CombineErr KeyedMap :=\n"
            "      match other' with\n"
            "      | .keyed es   => Except.ok (combineEntries (combineEntries base es) es)\n"
            "      | .single _ _ => Except.error .notKeyed\n"
            "    return out"),
        "refinement": (
            "fuses the operand's entries into the result a second time. A faithful "
            "real patch of this shape would hand the operand to the combine twice — "
            "at best a redundant duplicate, at worst a self-conflict between an "
            "entry and itself — and the merged result never matches the two-operand "
            "combine the failing test compares against, so it would NOT resolve. "
            "Ports the nagini uniq-pad-list (the padded-operand near-miss), which "
            "the port had recorded as unmodeled: the duplicate reappears here as "
            "duplicated ENTRIES rather than a third list slot."
        ),
        "rationale": (
            "REJECT from `out = combineSpec base other`: `combineSpec` fuses the "
            "operand's entries EXACTLY ONCE, so duplicating them diverges wherever "
            "the operand contributes anything. Membership and order are both "
            "satisfied here — only multiplicity breaks — so this pins that the "
            "union clause is read as a sequence and not as a set. Refuted at "
            "base=[(4,4)], other=.keyed [(2,3)], a fifth distinct input point. If "
            "it verified => SPEC-TOO-WEAK (the clause would admit a duplicating "
            "combine)."
        ),
        "witness": _witness("[(4,4)] : List (Nat × Int)", "Operand.keyed [(2,3)]"),
    },
]


# ===========================================================================
# NAGINI -> VELVET ACCOUNTING.
#
# The nagini sibling contracts `merge_method(receiver, other) -> List[Operand]`,
# whose postcondition pins the RETURNED 2-LIST: its length (P1), receiver
# pass-through by object identity (P2), both operands mapping-shaped (P3a/P3b),
# name/value preservation (P4), and identity on the no-op branch (P5). This
# velvet bundle models a NARROWER, downstream slice: `combineKeyed(base, other)`,
# the normalize-then-CORE-COMBINE tail, whose single ensures pins the fused
# result `out = combineSpec base other`. The nagini list-shape/identity clauses
# (P1/P2/P5) are about the intermediate 2-list the core is HANDED and have no
# counterpart in a model that returns the combine's OUTPUT directly; the
# load-bearing behaviour — that a lone keyed value is re-expressed so the combine
# reaches it (P3b) and that the union is produced (P4) — is exactly what
# `combineSpec` pins. This is carrier narrowing (the lean-family bundles model
# the purely functional core), not a thinner attack surface: every rival still
# targets the one clause the modeled surface has.
#
#   nagini case                  kind          -> here                     disposition
#   ------------------------------------------------------------------------------------------
#   pos-control-ifelse           soundness     -> pos-closed-form          RE-EXPRESSED
#   pos-control-listfirst        soundness     -> pos-coerce-named         RE-EXPRESSED
#   (no sibling)                 soundness     -> pos-arm-reorder          ADDED
#   admiss-f2p-shaped-input      admissibility -> admiss-f2p-shaped-input  PORTED (re-aimed)
#   uniq-drop-conversion         uniqueness    -> rival-drop-conversion    PORTED (headline)
#   uniq-rebuild-noop            uniqueness    -> rival-coerce-empty       RE-EXPRESSED
#   uniq-swap-order              uniqueness    -> rival-swap-order         PORTED (union order)
#   uniq-pad-list                uniqueness    -> rival-dup-operand        RE-EXPRESSED (multiplicity)
#   uniq-drop-second             uniqueness    -> rival-lose-operand       RE-EXPRESSED (operand leg)
#   uniq-frame-mutation          uniqueness    -> (none)                   VACUOUS (no heap)
#   uniq-frame-mutation-recv     uniqueness    -> (none)                   VACUOUS (no heap)
#   (no sibling)                 uniqueness    -> rival-lose-base          ADDED (union, base leg)
#   AXIOM_TESTS (2)              axiom         -> (none)                   DROPPED (G-AX lane)
#
# 10 velvet SPEC cases: 3 soundness, 1 admissibility, 6 uniqueness.
#
# RE-EXPRESSED (pos-control-ifelse -> pos-closed-form; pos-control-listfirst ->
#   pos-coerce-named): the two nagini positives restructure the second-operand
#   selection (single if/else; build-then-append). On this carrier the selection
#   is the pure `coerceOperand`, so the honest reshapes are: return the grounded
#   post-image `combineSpec base other` directly (pos-closed-form), and delegate
#   to the named `coerceOperand` rather than inline its match (pos-coerce-named).
#   Both verify (pos-coerce-named with a one-`rfl` proof retune).
# ADDED (pos-arm-reorder): a third correct reshape — reorder the normalization
#   match arms — with no direct nagini sibling; confirms the spec is not over-fit
#   to the branch order. Verifies under the frozen proof unchanged.
# PORTED, RE-AIMED (admiss-f2p-shaped-input -> admiss-f2p-shaped-input): the
#   nagini case injects the F2P shapes inside the impl region and asserts the
#   read-only fractional-permission precondition holds for them. This method has
#   no `require` and no heap permission, so the PERMISSION half has no
#   counterpart — but the lane is not thereby vacuous, and a case whose module is
#   just the frozen file would test nothing while passing honestly. The analogue
#   on a total carrier is the obligation being UNSATISFIABLE at exactly an
#   F2P-shaped input, so the case discharges the post-image AT that concrete input
#   by evaluation (`have … := by rfl`, a computed value the spec is checked
#   against, not a restatement of the ensures) and only then closes the frozen
#   obligation verbatim over the free params.
# PORTED (uniq-drop-conversion -> rival-drop-conversion): the headline pre-patch
#   bug carries across intact — feed the operand to the core combine unnormalized,
#   so a lone keyed value makes the combine FAIL. Same refinement argument (the
#   unpatched repo hits the key/value iteration on an operand with nothing to
#   iterate and raises), now backed by a machine-checked witness.
# RE-EXPRESSED (uniq-rebuild-noop -> rival-coerce-empty): the nagini lossy-rebuild
#   cheat rebuilds a fresh mapping-shaped operand, dropping data beyond the first
#   variable and failing the object-IDENTITY clause P5. This carrier has no object
#   identity (values, not references), so the identity attack has no counterpart;
#   the DATA-LOSS the rebuild causes DOES — re-expressed as normalizing a lone
#   keyed value to an EMPTY collection, which drops its single entry. Same failure
#   mode (a lossy normalization the union clause catches), refuted where the entry
#   goes missing.
# ADDED (rival-lose-base): attacks the base leg of the union clause (base entries
#   present) — the combine's OUTPUT structure the nagini list-shape clauses do not
#   reach on this carrier. A genuine partial-domain break (correct on an empty
#   base) with a machine-checked witness.
# RE-EXPRESSED (uniq-drop-second -> rival-lose-operand; uniq-swap-order ->
#   rival-swap-order; uniq-pad-list -> rival-dup-operand): the three nagini rivals
#   that attack the intermediate 2-LIST's length (len == 2) and position identity
#   (Result()[0] is receiver). The 2-list itself is upstream of the modeled slice,
#   so there is no list slot to drop, swap, or pad — but each rival's OBSERVABLE
#   consequence survives the narrowing and lands on the union clause, which pins
#   the fused sequence `base ++ es` and therefore its membership, its ORDER, and
#   its MULTIPLICITY:
#     * dropping the second operand => the operand's entries never appear
#       (rival-lose-operand);
#     * swapping the two operands => the entries appear in the reversed order,
#       inverting precedence between the two collections (rival-swap-order);
#     * padding the operand list => the operand's entries appear TWICE
#       (rival-dup-operand).
#   All three are rejected with witnesses that elaborate against the rival and
#   fail on gold, so they are expressible here after all; an earlier revision of
#   this file recorded them as UNMODELED, which was wrong.
# VACUOUS (uniq-frame-mutation, uniq-frame-mutation-recv): the nagini frame
#   attacks overwrite a read-only input held at Acc(., 1/2) (other.is_mapping /
#   receiver.value) and are rejected for INSUFFICIENT PERMISSION. This backend is
#   referentially transparent and declares no `mut` parameter — `base` and `other`
#   are immutable values with no heap footprint — so there is no read-only field
#   to overwrite and no permission system to trip. Omitted as vacuous, NOT
#   fabricated (per the porting map, this class is legitimately dropped).
# DROPPED (AXIOM_TESTS): the nagini file's axiom-soundness/containment probes over
#   the real conversion callee are G-AX's job (axiom_check.py / mapping.md — here
#   the core combine is an A-reference modeled deeply, validated == the real
#   callee by G-AX, not a consumed axiom); the G-PBT gate ignores AXIOM_TESTS
#   regardless.
#
# DIVERGENCE lane: CLOSED BY THE SEMANTICS on this bundle. CORRECTED: an earlier
#   version of this entry scoped a corpus-wide vacuous-verification hole to a
#   cohort of bundles and placed this one outside it, citing an internal findings
#   doc. There is no cohort: all 500 velvet bundles carry
#   `set_option loom.semantics.termination "total"`, and the option cannot drift
#   from the file's `open TotalCorrectness` because the `set_option` elaborator
#   itself runs `openScope `TotalCorrectness`
#   (`Loom/MonadAlgebras/WP/Options.lean:169-186`). Under `total` a postcondition
#   is claimed of ALL runs and every loop owes a strictly decreasing measure, so
#   the diverging probe is REJECTED with `error: Decreasing annotations are
#   required in total correctness semantics`, confirmed here by building a
#   `while true` prefix ahead of an otherwise-gold body. So there is no hole to
#   record and nothing to ship: a
#   reject case for a rival the frozen proof already refuses would attest to the
#   termination checker, not to the spec. (An earlier revision of this file
#   asserted `"partial"` throughout and booked the hole against this cell; that was
#   a misreading of the frozen `set_option`.) The nagini sibling carries no
#   diverge-*/nonterm-*/weak-diverge case either, so nothing was dropped.
#
# BINDER / CLAUSE COVERAGE. The obligation has two input binders — `base` and
#   `other` — and one top-level clause, `out = combineSpec base other`, which
#   internally conjoins (i) the operand is normalized so the combine SUCCEEDS
#   (never .error), (ii) the base entries are present in the union, (iii) the
#   operand entries are present, (iv) in that ORDER (base first), and (v) each
#   exactly ONCE. The six reject witnesses probe six DISTINCT input points
#   (pts=6): base over {[], [(1,1)], [], [(1,1)], [(1,1)], [(4,4)]} and other over
#   {.single 0 0, .single 0 0, .keyed [(2,3)], .single 5 7, .keyed [(2,3)],
#   .keyed [(2,3)]} — both binders varied (base over empty/non-empty and over
#   distinct non-empty values; other over both the `.single` and `.keyed`
#   constructors), so no binder is held fixed by every witness and a rival
#   mishandling only one operand shape or only an empty base would be caught.
#   Clause (i) is attacked by rival-drop-conversion (the .error crash); clause
#   (ii) by rival-lose-base; clause (iii) by rival-lose-operand and
#   rival-coerce-empty (the lossy-normalization data loss); clause (iv) by
#   rival-swap-order and clause (v) by rival-dup-operand — the two rivals that
#   satisfy MEMBERSHIP on both legs and break only the sequence structure, which
#   is what pins the union as a sequence rather than a set. The three positives
#   defend the whole clause on gold-shaped computations, and the admissibility
#   case pins it at an F2P-shaped input by evaluation.
#
# WITNESS MECHANICS: the tester+`decide` path is DEAD (the postcondition's
#   Decidable instance for `out = combineSpec base other` does not kernel-reduce;
#   measured: both a wrong rival and gold get stuck identically). Every witness
#   instead extracts the executable program `combineKeyedExec` and refutes the
#   ensures directly against the TRANSPARENT `combineSpec`, projecting both sides
#   through `.toOption` (the result type `Except CombineErr KeyedMap` has no
#   DecidableEq). Each rival is loop-free so its `…Exec` reduces under `decide`;
#   gold's `…Exec` agrees with `combineSpec` at every input, so the SAME witness
#   proves the inequality FALSE on gold and fails to elaborate. No witness binds a
#   hypothesis, so no consistency probe is needed. All six checked with
#   scripts/lean_verify.sh: rival exit 0, gold build fails (a `decide` error).
#   The gold-side error is a PLAIN EVALUATION verdict ("Tactic `decide` proved that
#   the proposition … is false"), so it is not one of the signature classes that
#   need a forgery check to be read — but each was forgery-tested anyway, by
#   building the flipped claim (`=` for `≠`) on both sides: the flip ELABORATES on
#   gold (exit 0) and FAILS on the rival with the mirror-image `decide` error. The
#   exit codes therefore invert exactly with the claim, so gold's exit carries
#   information about what the witness asserts and no case is hollow.
AXIOM_TESTS = []
