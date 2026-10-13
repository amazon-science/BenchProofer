"""properties.py — G-PBT falsification battery for matplotlib__matplotlib-23299 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed —
both of which the consumer spec view elides, so ``markers.same_spec`` holds and
the ``prove_correct restoreSnapshot`` obligation survives with a byte-identical
header) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE. One contracted method that restores a previously-recorded
snapshot of a key→value mapping over its current (possibly modified) state, while
leaving ONE designated key ("backend") at its current value instead of reverting
it:

  restoreSnapshot (mut params : List (String × String))
      (saved : List (String × String))  return (u : Unit)
    ensures params = updateDict paramsOld (eraseKey saved "backend")

``params`` is the live mapping; it is genuinely mutated and its post-state is
pinned EXACTLY (directive 5) by the single ``ensures`` equation. ``saved`` is the
read-only entry snapshot (NOT a ``mut`` binder). There is no ``require`` clause,
so the admitted domain is total: the post-image must hold for every current
mapping and every snapshot. ``updateDict current saved`` overlays ``saved`` onto
``current`` (saved bindings win, current-only keys kept); ``eraseKey saved
"backend"`` drops the designated key from the snapshot before the overlay.

The single top-level clause folds THREE independent behaviours the change
demands, and each is attacked below:
  (S) SURVIVE — the designated key keeps its CURRENT value, not its snapshot
      value: because "backend" is dropped from the snapshot before the overlay,
      the current binding for "backend" is retained. This is the reported fix.
  (R) REVERT — every OTHER recorded key is put back to its snapshot value: the
      overlay reinstates the saved bindings over the current ones.
  (F) FRAME / NO-SPURIOUS — the restored mapping is EXACTLY the overlay: no key
      absent from both current and snapshot is introduced, and current-only keys
      keep their current value. This is the value-level analogue of the frame
      obligation on the one mutated binder.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME-MUTATION (half-permission read-only write) — VACUOUS here, exactly as
    the nagini sibling already reasoned: there is NO fractional-permission
    read-only input to overwrite. ``saved`` is an immutable value (not a ``mut``
    binder); Lean and Velvet are referentially transparent, with no heap and no
    aliasing. The nagini bundle itself noted its `params` is held at FULL
    permission and the frame analogue is its postcondition clause (4) — which is
    the FRAME/no-spurious behaviour (F) above, attacked by ``weak-corrupt-key``.
    So no half-permission substitute probe is fabricated (see footer).
  * UNGROUNDED-ORACLE ECHO — N/A. The post-image is a total, fully-unfolded
    function of the method's own two arguments (``updateDict``/``eraseKey``/
    ``lookupKey`` are concrete ``def``s and the ``axioms`` region declares
    nothing) — there is no opaque answer key to echo. Instead we carry two honest
    cheapest-reshape POSITIVE CONTROLS plus an admissibility positive.
  * PARTIAL-DOMAIN / VALUE — APPLIES: rivals right on part of the domain but
    diverging on a sub-domain (reverting the designated key too; not reverting
    ordinary keys; the current mapping winning over the snapshot; introducing a
    spurious key). Each is refuted at a concrete point that varies BOTH binders.

WITNESS PLACEMENT. The spec is a ``method`` CONTRACT, not a bare predicate, so
each reject rival reaches it through Velvet's own tester machinery:
``restoreSnapshotTester params saved = false`` says the extracted program's
observable (the mutated mapping's post-state) violates the method's
postcondition at that concrete input. It is checked in a file whose
``prove_correct`` block has been stripped, so no tactic script can mask the
verdict. The carrier ``List (String × String)`` has native ``DecidableEq``, so
every witness closes by ``decide``.

AXIOM lane: DROPPED. The ``axioms`` region declares no ``axiom`` (the overlay and
key-drop are modeled DEEPLY in the ``pure`` region — ``updateDict`` is an
A-reference validated == the real builtin overlay by axiom_check.py / G-AX, NOT
consumed as a contract). There is no axiom-soundness obligation to probe in this
spec-lane manifest, and the gate ignores ``AXIOM_TESTS`` regardless.
"""
from pathlib import Path

INSTANCE = "matplotlib__matplotlib-23299"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor (lies wholly inside the single impl region and is
# ---- unique in Solution.lean; both facts asserted at load by _swap). It spans
# ---- the gold impl's leading comment and its three code lines, so a variant
# ---- replaces the entire behaviour (comment included) with no stale narration.
_GOLD_IMPL = (
    "    -- Drop the designated key from the snapshot before overlaying it, so the\n"
    "    -- designated key is NOT reverted to its saved value.\n"
    "    let restoreSrc := eraseKey saved \"backend\"\n"
    "    params := updateDict params restoreSrc\n"
    "    return"
)

assert _GOLD_IMPL in _BASE, "frozen impl region drifted; update _GOLD_IMPL"

# ---- proof-body anchor. A `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view (only the header is kept), so a case that adds an
# ---- in-region `assert` may retune its tactic script without touching the spec
# ---- statement or dropping the obligation. Unique in the file.
_GOLD_PROOF = "prove_correct restoreSnapshot by\n  loom_solve"

assert _GOLD_PROOF in _BASE, "frozen proof body drifted; update _GOLD_PROOF"


def _impl(body):
    """Build a full Solution.lean variant by replacing the gold impl block."""
    return _swap(_BASE, _GOLD_IMPL, body)


def _impl_proof(body, proof):
    """Reshape the impl block AND retune the `prove_correct` tactic body."""
    return _swap(_swap(_BASE, _GOLD_IMPL, body), _GOLD_PROOF, proof)


# ---- witness preamble. Reaches the method contract through Velvet's tester
# ---- machinery; checked in a file whose `prove_correct` block is stripped. The
# ---- carrier `List (String × String)` has native `DecidableEq`, so no instance
# ---- needs deriving, no assumption is introduced (`axiom`/`sorry`/
# ---- `native_decide` are absent), and the frozen solution rejects these
# ---- witnesses all the same.
def _tester(body):
    return (
        "extract_program_for restoreSnapshot\n"
        "prove_precondition_decidable_for restoreSnapshot\n"
        "prove_postcondition_decidable_for restoreSnapshot\n"
        "derive_tester_for restoreSnapshot\n\n" + body
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL 1 (soundness) — a structurally different but CORRECT
    # impl that MUST verify; else the post-image is SPEC-TOO-STRONG. The gold
    # body binds the key-dropped snapshot to a `let` and overlays it; this
    # reshape inlines that binding into the overlay. Observationally identical
    # final mapping on every input, no new proof obligation, so the frozen
    # `loom_solve` still discharges the single clause.
    # =====================================================================
    {
        "id": "pos-inline-overlay",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    -- Inline the key-dropped snapshot directly into the overlay.\n"
            "    params := updateDict params (eraseKey saved \"backend\")\n"
            "    return"),
        "rationale": (
            "a correct reshape (the key-dropped snapshot inlined into the overlay "
            "instead of bound to an intermediate `let`) yields an identical "
            "post-state on every input and adds no new proof obligation, so the "
            "single clause `params = updateDict paramsOld (eraseKey saved "
            "\"backend\")` still discharges under the frozen `loom_solve`; if it "
            "failed to verify the spec would be SPEC-TOO-STRONG on impl shape."
        ),
    },

    # =====================================================================
    # POSITIVE CONTROL 2 (soundness) — a second structurally different CORRECT
    # impl: rebind the snapshot to a fresh local before dropping the designated
    # key from it, and overlay from that local. Same data flow, different local
    # structure. Must verify; else SPEC-TOO-STRONG.
    # =====================================================================
    {
        "id": "pos-local-rebind",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    -- Rebind the snapshot to a local before dropping the designated key.\n"
            "    let src := saved\n"
            "    let restoreSrc := eraseKey src \"backend\"\n"
            "    params := updateDict params restoreSrc\n"
            "    return"),
        "rationale": (
            "a correct reshape (the snapshot rebound to a fresh local `src` before "
            "the designated key is dropped from it, then overlaid) has identical "
            "data flow — `eraseKey src \"backend\"` = `eraseKey saved \"backend\"` "
            "— so it computes the same post-state on every input and the frozen "
            "`loom_solve` still discharges the clause; else SPEC-TOO-STRONG on "
            "impl shape."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — no `require` clause exists, so the nagini "a normal input
    # satisfies the precondition" probe is vacuous (nothing could exclude the
    # F2P-shaped input). Re-aimed at the residual total-domain risk: that the
    # post-image is UNSATISFIABLE / degenerate at the interesting point. This
    # case discharges an in-region `assert` pinning the post-image at the F2P
    # corner — the designated key overridden inside the scope while one ordinary
    # key was also changed — where it must demand the designated key KEEPS its
    # current (body) value AND the ordinary key is REVERTED to its snapshot
    # value. The impl is kept verbatim so the method's own obligation still
    # discharges; the assert is live (a false claim about the same point leaves
    # an unsolved goal), and the tactic body is retuned to also close it.
    # =====================================================================
    {
        "id": "admiss-f2p-survive-and-revert",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl_proof(
            "    assert (with_name_prefix `assert\n"
            "      (updateDict [(\"backend\", \"new\"), (\"k\", \"body\")]\n"
            "          (eraseKey [(\"backend\", \"old\"), (\"k\", \"entry\")] \"backend\")\n"
            "        = [(\"k\", \"entry\"), (\"backend\", \"new\")]))\n"
            + _GOLD_IMPL,
            "prove_correct restoreSnapshot by\n  loom_solve <;> decide"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at the F2P corner: "
            "with the designated key overridden inside the scope (current "
            "\"new\") over its snapshot value (\"old\") and one ordinary key also "
            "changed (current \"body\" over snapshot \"entry\"), the restored "
            "mapping must KEEP the designated key at \"new\" and REVERT the "
            "ordinary key to \"entry\". The in-region assert must discharge (else "
            "the obligation is unsatisfiable / PRECOND-TOO-STRONG); the impl is "
            "verbatim so the equality clause still discharges too."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument that its faithful real
    # counterpart would NOT resolve the failing test. Witnesses vary BOTH
    # binders (`params` and `saved`) in length and content.
    # =====================================================================
    {
        "id": "weak-revert-designated",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-fix bug. Overlay the FULL entry snapshot without dropping the
        # designated key, so the designated key is reverted to its snapshot
        # value instead of keeping its current one. Attacks behaviour (S).
        "module": _impl(
            "    -- Overlay the full entry snapshot, without dropping any key.\n"
            "    params := updateDict params saved\n"
            "    return"),
        "refinement": (
            "this is the pre-change behaviour: the full entry snapshot is overlaid "
            "unchanged, so the designated key is reverted to its stale snapshot "
            "value on scope exit. A faithful real counterpart that reverts the "
            "designated key together with the rest re-clobbers a value assigned to "
            "it inside the scope. The failing test drives exactly that path — it "
            "assigns the designated key inside the scope and asserts the assigned "
            "value SURVIVES the exit — and still observes it reverted, so it still "
            "fails. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from behaviour (S) of the clause: the post-image is "
            "`updateDict paramsOld (eraseKey saved \"backend\")` (designated key "
            "kept at its current value), but overlaying the full snapshot reverts "
            "the designated key to its snapshot value. These differ whenever the "
            "current and snapshot values for the designated key differ — the F2P "
            "scenario. Refuted at `params = [(\"backend\", \"B2\")]`, "
            "`saved = [(\"backend\", \"B1\")]`."
        ),
        "witness": _tester(
            "example : restoreSnapshotTester [(\"backend\", \"B2\")] "
            "[(\"backend\", \"B1\")] = false := by\n  decide\n"),
    },
    {
        "id": "weak-no-revert",
        "kind": "uniqueness",
        "expect": "reject",
        # Never revert anything: return the current mapping unchanged, so
        # recorded ordinary keys keep their in-scope (changed) values. Attacks
        # behaviour (R).
        "module": _impl(
            "    -- Return the mapping unchanged: no key is reverted.\n"
            "    return"),
        "refinement": (
            "a faithful counterpart that skips the restore entirely leaves every "
            "recorded ordinary setting permanently at whatever value it was given "
            "inside the scope. The existing test that requires the ordinary "
            "settings to be restored to their entry values on scope exit still "
            "observes them mutated, so it still fails. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from behaviour (R) of the clause: the post-image reinstates "
            "each recorded ordinary key's snapshot value, but returning the "
            "current mapping unchanged leaves it at the in-scope value. These "
            "differ whenever a recorded ordinary key's current and snapshot values "
            "differ. Refuted at `params = [(\"k\", \"cur\")]`, "
            "`saved = [(\"k\", \"sav\")]` (an ordinary key, no designated key "
            "present — a distinct input shape from the survive rival's)."
        ),
        "witness": _tester(
            "example : restoreSnapshotTester [(\"k\", \"cur\")] "
            "[(\"k\", \"sav\")] = false := by\n  decide\n"),
    },
    {
        "id": "weak-current-wins",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS of the no-revert rival. Overlay with the arguments swapped so
        # the CURRENT mapping wins over the snapshot: the designated key is kept
        # correctly AND snapshot-only keys are added correctly, but a key present
        # in BOTH keeps its current (in-scope) value instead of being reverted.
        # Correct over more of the domain than weak-no-revert, so it carries its
        # own separating witness at an input with a designated key and a
        # snapshot-only key present.
        "module": _impl(
            "    let restoreSrc := eraseKey saved \"backend\"\n"
            "    params := updateDict restoreSrc params\n"
            "    return"),
        "refinement": (
            "a faithful counterpart that lets the in-scope mapping take precedence "
            "over the recorded snapshot reverts nothing for any setting that was "
            "actually changed inside the scope — it merely re-adds settings that "
            "were never touched. The existing test requiring changed ordinary "
            "settings to be restored to their entry values still observes them at "
            "their in-scope values, so it still fails. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from behaviour (R): the post-image reinstates the SNAPSHOT "
            "value for each recorded key present in both, but with the overlay "
            "arguments swapped the current value wins, so a key changed inside the "
            "scope is not reverted. This rival keeps the designated key and adds "
            "snapshot-only keys correctly, so it agrees with the frozen solution "
            "where the no-revert rival does not; it is refuted at a NON-designated "
            "shared key whose current and snapshot values differ, with a "
            "snapshot-only key and the designated key also present: "
            "`params = [(\"backend\", \"cb\"), (\"k\", \"ck\")]`, "
            "`saved = [(\"backend\", \"sb\"), (\"k\", \"sk\"), (\"z\", \"sz\")]` "
            "(gold reverts k to \"sk\"; the rival keeps \"ck\")."
        ),
        "witness": _tester(
            "example : restoreSnapshotTester "
            "[(\"backend\", \"cb\"), (\"k\", \"ck\")] "
            "[(\"backend\", \"sb\"), (\"k\", \"sk\"), (\"z\", \"sz\")] "
            "= false := by\n  decide\n"),
    },
    {
        "id": "weak-corrupt-key",
        "kind": "uniqueness",
        "expect": "reject",
        # The gold overlay PLUS an appended binding for a key present in neither
        # the current mapping nor the snapshot. Attacks behaviour (F): the frame
        # / no-spurious analogue of the nagini corrupt-third-key rival.
        "module": _impl(
            "    let restoreSrc := eraseKey saved \"backend\"\n"
            "    params := updateDict params restoreSrc ++ [(\"spurious\", \"1\")]\n"
            "    return"),
        "refinement": (
            "a faithful counterpart whose restore introduces a setting present in "
            "neither the current mapping nor the recorded snapshot leaves that "
            "setting at a garbage value after the scope exits. The existing test "
            "requiring the FULL set of ordinary settings to be restored to its "
            "entry state (no setting spuriously introduced or corrupted) still "
            "observes the extra setting, so it still fails. It would NOT resolve."
        ),
        "rationale": (
            "REJECT from behaviour (F) of the clause: the post-image is EXACTLY "
            "the overlay, but the rival appends a binding for a key absent from "
            "both inputs, so the restored mapping carries a spurious entry the "
            "post-image does not. Refuted at `params = [(\"backend\", \"b\"), "
            "(\"k\", \"v\")]`, `saved = [(\"k\", \"v\")]` (the overlay is otherwise "
            "correct there, so the ONLY divergence is the spurious key)."
        ),
        "witness": _tester(
            "example : restoreSnapshotTester "
            "[(\"backend\", \"b\"), (\"k\", \"v\")] [(\"k\", \"v\")] "
            "= false := by\n  decide\n"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (2 soundness
# positives, 1 admissibility, 4 uniqueness rivals — with one of those framed as
# the FRAME-condition analogue) and a 1-case AXIOM lane (an A-reference deep-model
# probe). The sibling contracts one function
# (`restore_after_temporary_overrides`) over a `Dict[int,int]` held at FULL
# permission, with four load-bearing postcondition clauses (SURVIVE / REVERT /
# NO-SPURIOUS / FRAME-full-revert). This bundle models the same restore over the
# purely-functional carrier `List (String × String)` and FOLDS those four clauses
# into one exact equation `params = updateDict paramsOld (eraseKey saved
# "backend")` — the designated key "backend" (nagini `key_resolved()`), a
# representative ordinary key (nagini `key_other()`), and third keys are all
# ordinary bindings of that carrier. Every sibling SPEC case is accounted for.
#
#   nagini case                    -> here
#   ---------------------------------------------------------------------
#   pos-reorder-writes              -> pos-inline-overlay          PORTED (re-expressed)
#   pos-local-rename                -> pos-local-rebind            PORTED
#   admiss-requires-facts           -> admiss-f2p-survive-and-revert  RE-AIMED
#   weak-revert-distinguished       -> weak-revert-designated      PORTED (= prepatch)
#   weak-no-revert-ordinary         -> weak-no-revert              PORTED
#   weak-revert-wrong-value         -> weak-current-wins           PORTED (re-expressed)
#   weak-corrupt-third-key          -> weak-corrupt-key            PORTED
#
# 6 ported/re-expressed, 1 re-aimed. AXIOM lane dropped (G-AX's job).
#
# RE-EXPRESSED (pos-inline-overlay): the nagini positive reorders two body
#   writes. This carrier has a single overlay assignment, not two writes to
#   reorder, so the cheapest structurally-different CORRECT reshape is inlining
#   the key-dropped snapshot into the overlay (dropping the intermediate `let`).
#   Same net post-state; the frozen proof still closes.
# RE-AIMED (admissibility): the nagini case Asserts the Requires-derived facts for
#   a normal input. There is NO `require` clause here, so the "admits a normal
#   input" reading is vacuous; the case is re-aimed at proving the post-image is
#   satisfiable AND non-degenerate at the F2P corner (designated key kept at its
#   in-scope value, ordinary key reverted to its snapshot value). The in-region
#   assert is discharged symbolically against concrete literals.
# RE-EXPRESSED (weak-current-wins): the nagini rival reverts the ordinary key to
#   the WRONG value (the distinguished body value). Over the value-carrying dict
#   that is a bespoke value swap; over this list carrier the natural expression of
#   "the wrong value survives on the ordinary key" is swapping the overlay
#   arguments so the CURRENT mapping wins — a key changed inside the scope keeps
#   its in-scope value rather than being reverted. It is a genuine near-miss of
#   weak-no-revert (it handles the designated key and snapshot-only keys
#   correctly), so it carries its own separating witness at a shared non-designated
#   key, per the manifest's near-miss rule.
# FRAME-MUTATION (half-permission read-only write): VACUOUS here, exactly as the
#   nagini docstring itself reasoned — there is NO `Acc(x,1/2)` read-only input to
#   overwrite. `saved` is an immutable value (not a `mut` binder); this backend is
#   referentially transparent, with no heap, no aliasing, and no permission system.
#   The nagini bundle's own FRAME analogue for its full-permission mutated mapping
#   is postcondition clause (4) (the full-revert / no-spurious Forall), which here
#   is behaviour (F) of the single equation and IS attacked by weak-corrupt-key.
#   So the frame surface is defended; only the half-permission variant is vacuous,
#   and no substitute probe is fabricated.
#
# CLAUSE / BINDER COVERAGE. The single top-level equation folds three independent
#   behaviours, each attacked: (S) SURVIVE by weak-revert-designated, (R) REVERT
#   by weak-no-revert and weak-current-wins (two angles), (F) FRAME/no-spurious by
#   weak-corrupt-key. All three are defended by the two positive controls and the
#   admissibility case. The four reject witnesses probe four DISTINCT inputs
#   (pts=4):
#     params=[(backend,B2)],            saved=[(backend,B1)]                    weak-revert-designated
#     params=[(k,cur)],                 saved=[(k,sav)]                         weak-no-revert
#     params=[(backend,cb),(k,ck)],     saved=[(backend,sb),(k,sk),(z,sz)]      weak-current-wins
#     params=[(backend,b),(k,v)],       saved=[(k,v)]                           weak-corrupt-key
#   so BOTH binders (`params`, `saved`) are varied over lengths 1/1/2/2 and
#   1/1/3/1 respectively and over distinct contents (with/without the designated
#   key, with/without a snapshot-only key, matching/differing values). Neither
#   binder is pinned across the battery, and the designated-key sub-domain (S) is
#   probed at differing designated-key values while other rivals omit it.
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job; this bundle declares no
#   consumed axiom (`updateDict` is a deep A-reference validated == the real
#   builtin overlay by axiom_check.py), so there is nothing here to probe and the
#   gate ignores it.
AXIOM_TESTS = []
