"""properties.py — G-PBT falsification battery for django__django-11133 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed,
both of which the consumer spec view elides — so ``markers.same_spec`` holds and
the ``prove_correct makeBytes`` obligation survives with a byte-identical
header) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must elaborate against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over three read-only inputs).

  makeBytes (encodeStr) (fallback) (value : Body)  return (out : List UInt8)
      ensures out = bodyBytes encodeStr fallback value                 -- master

A body value is turned into its output bytestring by DISPATCHING on its shape
(``value : Body``): a plain byte string yields its bytes; a read-only
byte-buffer view yields its underlying bytes (materialising it gives exactly the
same bytes as a plain byte string — the discriminating behaviour); a textual
value is encoded with the charset encoder ``encodeStr``; any other value yields
``fallback``, its rendered-then-encoded form. ``bodyBytes`` is a total, fully
unfolded ``def`` of the method's own three arguments; there is NO ``require``
clause and NO ``mut`` binder, which is what makes the per-arm rivals below
refutable at a concrete point.

WHICH CLAUSE CONSTRAINS THE IMPL. There is a single top-level clause,
``out = bodyBytes encodeStr fallback value``, and it is the WHOLE pin: it fixes
the output on every one of the four value shapes at once. ``encodeStr`` and
``fallback`` are FREE inputs (no property is claimed of either — the spec holds
for every value of them), so ``bodyBytes`` is GROUNDED in the method's own
arguments, not an opaque answer key. Every uniqueness rival therefore targets
this one clause, on a different arm of the dispatch.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME / PERMISSION-MUTATION — VACUOUS. The nagini sibling's MANDATORY
    ``frame-mutate-data`` / ``frame-mutate-kind`` rivals write through a
    half-permission (``Acc(.,1/2)``) reference to a field of the read-only input
    and are rejected for INSUFFICIENT PERMISSION. This backend is referentially
    transparent: the inputs are immutable values, this bundle declares no
    ``mut`` binder, and there is no heap, aliasing, or permission system to
    subvert. There is no read-only input to overwrite, so the class is vacuous;
    no substitute probe is fabricated (reported as an omission, not faked).
  * UNGROUNDED-ORACLE ECHO — N/A as an attack. The post-image ``bodyBytes`` is a
    total, fully unfolded ``def`` of the method's own arguments (the ``axioms``
    region declares NO ``axiom`` — there is no opaque answer key to echo). The
    only value that satisfies the master clause on the encode/fallback arms is
    the one ``bodyBytes`` names, which the gold impl returns, so there is no
    WRONG echo to build. The honest cheapest CORRECT impl (return ``bodyBytes``
    directly) is carried as a POSITIVE control instead — it doubles as proof the
    spec is not echo-vulnerable, since any wrong per-arm dispatch fails
    ``out = bodyBytes encodeStr fallback value``.
  * PARTIAL-DOMAIN / VALUE — the whole reject surface, all against the master
    clause. A rival can be right on three of the four value shapes and divert
    the fourth into the wrong bytestring (the pre-image bug on the buffer arm),
    or emit the RIGHT SHAPE with the WRONG value on the buffer arm (a byte list
    derived from the content but not the content itself), isolating exactly the
    verbatim-content requirement. A third axis, added by audit: the right
    OPERATION on the wrong ARGUMENT (the encoder applied to something other than
    the value's own characters), which is invisible to any witness that binds
    the encoder to a constant function.
  * DIVERGENCE - the class is INAPPLICABLE to this impl and CLOSED BY THE
    SEMANTICS against any rival that manufactures it. The frozen impl is
    LOOP-FREE (straight-line ``match`` over immutable values, no loop and no
    recursion), so there is no control flow here to make diverge: a diverging
    rival cannot be obtained by mutating this body, it has to bring a loop of
    its own. When it does, the semantics refuse it. This bundle sets
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

WITNESS MECHANICS. The spec is a ``method`` CONTRACT, not a bare predicate, so a
witness reaches the post-image through Velvet's own tester machinery
(``extract_program_for`` → ``prove_..._decidable_for`` → ``derive_tester_for``).
``makeBytesTester encodeStr fallback value = false`` says the extracted
program's result violates the method's postcondition at that concrete input. It
is checked in a file whose ``prove_correct`` block has been stripped by the gate
(so no frozen tactic script can mask the verdict) and each witness passes both
halves: it ELABORATES against its rival (``decide`` closes the ``= false``) and
FAILS against the frozen solution (``decide`` proves the tester is ``true``
there, so the ``= false`` goal is refuted). ``value`` is a concrete constructor
literal and ``encodeStr`` / ``fallback`` are concrete function/list literals, so
``decide`` reduces fully (``UInt8`` and ``List`` are decidable-eq). No witness
binds a hypothesis (every input is a concrete literal that decides the master
clause), so no consistency probe is needed and none of the banned tokens
(sorry/admit/native_decide/axiom/opaque) appears. Every witness was checked
out-of-band with ``scripts/lean_verify.sh``: each ELABORATES against its rival
(exit 0) and FAILS against gold (a ``decide`` error).

AXIOM lane: DROPPED. ``AXIOM_TESTS = []``. The axiom lane is G-AX's job
(axiom_check.py validates the one A-reference — that materialising a byte-buffer
view yields its underlying bytes — against the real builtin) and the G-PBT gate
ignores ``AXIOM_TESTS`` regardless. This bundle consumes no ``axiom``
(``meta.json`` axioms == []), so there is nothing in that lane for this
spec-lane manifest.
"""
from pathlib import Path

INSTANCE = "django__django-11133"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchor: the WHOLE frozen impl body (the shape dispatch),
# ---- everything strictly BETWEEN the method's `-- impl-start` / `-- impl-end`.
# ---- The `bodyBytes` def in the `pure` region uses a different `| .case arg =>`
# ---- (no `match value with`, no `pure`), so this `match value with` /
# ---- `pure ...` block is unique in the file (both facts asserted at load by
# ---- _swap). Every variant replaces exactly this text, so each edit lies
# ---- wholly inside the one -- impl-start .. -- impl-end region and same_spec
# ---- holds by construction.
_IMPL = (
    "    match value with\n"
    "    | .bytes  b => pure b\n"
    "    | .buffer b => pure b\n"
    "    | .text   s => pure (encodeStr s)\n"
    "    | .other    => pure fallback"
)
assert _BASE.count(_IMPL) == 1, "makeBytes impl region drifted from expected text"

# ---- the frozen proof body (tactic script only; elided from the spec view).
# ---- Rivals leave it as-is — the rejection is carried by the witness, not the
# ---- tactic script. A positive reshape or the admissibility assert may retune
# ---- it, but none needs to: `loom_solve` closes every case here.
_PROOF = "prove_correct makeBytes by\n  loom_solve"
assert _BASE.count(_PROOF) == 1, "proof region drifted from expected text"


def _impl(new_body):
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---- witness preamble. Reaches the method's post-image through the tester
# ---- machinery; checked in a file whose `prove_correct` block is stripped.
_TESTER = (
    "extract_program_for makeBytes\n"
    "prove_precondition_decidable_for makeBytes\n"
    "prove_postcondition_decidable_for makeBytes\n"
    "derive_tester_for makeBytes\n\n"
)


def _witness(encode, fallback, value):
    return (
        _TESTER +
        f"example : makeBytesTester ({encode}) ({fallback}) ({value}) = false := by\n"
        "  decide\n"
    )


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROLS (soundness) — structurally different but CORRECT impls
    # that MUST verify. If a faithful correct impl cannot verify, the spec is
    # SPEC-TOO-STRONG. Each keeps the obligation and the frozen proof script
    # (`loom_solve` closes the point-wise equality regardless of the executable
    # dispatch's shape).
    # =====================================================================
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: report the output DIRECTLY via the transparent dispatch
        # function, no per-shape match in the executable body. The master clause
        # is literally `out = bodyBytes encodeStr fallback value`, so this is the
        # cheapest HONEST correct impl — and, since `bodyBytes …` is GROUNDED in
        # the arguments (not an opaque answer key), it doubles as proof the spec
        # is not echo-vulnerable (any wrong per-arm dispatch fails the clause).
        "module": _impl("    pure (bodyBytes encodeStr fallback value)"),
        "rationale": (
            "the post-image `bodyBytes encodeStr fallback value` is GROUNDED in "
            "the inputs (a total, fully unfolded dispatch, no opaque answer "
            "key), so returning it directly is the honest cheapest CORRECT impl; "
            "the master clause is literally that equality, so it MUST verify, "
            "else the clause is SPEC-TOO-STRONG. Ports the nagini "
            "pos-oracle-grounded / echo-attempt-honest control: the cheapest "
            "impl satisfying the grounded pin, showing the spec is not "
            "echo-vulnerable."
        ),
    },
    {
        "id": "pos-arm-reorder",
        "kind": "soundness",
        "expect": "verify",
        # Reshape: permute the match arms (the two encode/fallback arms first,
        # the two verbatim-content arms last). A `match` is order-independent on
        # disjoint constructors, so the returned value is unchanged on every
        # shape and the master clause still discharges under the frozen proof.
        "module": _impl(
            "    match value with\n"
            "    | .text   s => pure (encodeStr s)\n"
            "    | .other    => pure fallback\n"
            "    | .bytes  b => pure b\n"
            "    | .buffer b => pure b"),
        "rationale": (
            "permuting the match arms over disjoint constructors leaves the "
            "output of every shape unchanged, so `out = bodyBytes encodeStr "
            "fallback value` still holds and the frozen `loom_solve` proof "
            "closes as-is; a correct reshape must verify. Ports the nagini "
            "pos-helper-reorder (branch-reorder, behaviourally identical). If it "
            "fails => SPEC-TOO-STRONG (over-fit to the frozen arm order)."
        ),
    },

    # =====================================================================
    # ADMISSIBILITY — RE-AIMED from nagini admiss-shape. That case established
    # that a normal F2P/P2P-shaped input satisfies the read-only precondition
    # (`Acc(.,1/2)` domain facts) and asserts the four representation tags
    # dispatch as specified. This method carries NO `require` clause (the
    # pre-conditions region is empty), so nothing could exclude an F2P-shaped
    # input and the precondition half is vacuous. Re-aimed at the residual
    # admissibility risk on a total domain: that the post-image is
    # UNSATISFIABLE / DEGENERATE at the interesting point (a spec no impl can
    # meet reads exactly like a spec every impl meets). An in-region `assert`,
    # at concrete F2P/P2P-shaped points, states the dispatch is NON-DEGENERATE:
    # a byte-buffer view yields its CONTENT (and, crucially, NOT the fallback
    # rendering), and a plain byte string yields its bytes. The gold impl is kept
    # verbatim so the method's own obligation still discharges; `loom_solve`
    # clears the extra assert goal too. The assert is LIVE, not decoration: a
    # false claim about the same points leaves an unsolved goal (checked).
    # =====================================================================
    {
        "id": "admiss-dispatch-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    assert (with_name_prefix `admiss\n"
            "      (bodyBytes (fun _ => []) [(7 : UInt8)] (.buffer [(1 : UInt8)]) = [(1 : UInt8)]\n"
            "        ∧ bodyBytes (fun _ => []) [(7 : UInt8)] (.buffer [(1 : UInt8)]) ≠ [(7 : UInt8)]\n"
            "        ∧ bodyBytes (fun _ => [(9 : UInt8)]) [(7 : UInt8)] (.bytes [(1 : UInt8)]) = [(1 : UInt8)]))\n"
            "    match value with\n"
            "    | .bytes  b => pure b\n"
            "    | .buffer b => pure b\n"
            "    | .text   s => pure (encodeStr s)\n"
            "    | .other    => pure fallback"),
        "rationale": (
            "the post-image is satisfiable AND non-degenerate at concrete "
            "F2P/P2P-shaped points: a byte-buffer view classifies to its "
            "underlying CONTENT (and is NOT diverted to the fallback rendering), "
            "and a plain byte string classifies to its bytes — the discriminating "
            "behaviours the failing/passing tests demand. The in-region assert "
            "must discharge (else the obligation is unsatisfiable/degenerate at "
            "the interesting point); the impl is kept verbatim so `out = "
            "bodyBytes encodeStr fallback value` discharges too. Re-aimed from "
            "the nagini admiss-shape, whose read-only-precondition half has no "
            "counterpart on this referentially-transparent, precondition-free "
            "carrier. If it fails => the spec is UNSATISFIABLE/DEGENERATE."
        ),
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected, each with a machine-checked refutation witness at a
    # concrete input and the refinement argument for why its faithful real
    # counterpart would NOT resolve the failing/passing tests. All attack the
    # master clause `out = bodyBytes encodeStr fallback value`; between them the
    # `value` binder is moved across all FOUR shapes (bytes / buffer / text /
    # other) and the `encodeStr` / `fallback` binders are moved off any fixed
    # value.
    # =====================================================================
    {
        "id": "weak-prepatch-view",
        "kind": "uniqueness",
        "expect": "reject",
        # THE pre-image bug: a byte-buffer view is NOT recognised as binary and
        # falls through to the fallback (rendered-then-encoded) branch instead of
        # yielding its underlying bytes. Exactly the behaviour the F2P observes.
        "module": _impl(
            "    match value with\n"
            "    | .bytes  b => pure b\n"
            "    | .buffer _ => pure fallback\n"
            "    | .text   s => pure (encodeStr s)\n"
            "    | .other    => pure fallback"),
        "refinement": (
            "this is the pre-image behaviour: a byte-buffer view is not treated "
            "as a binary value, so it yields its textual rendering rather than "
            "its content. A faithful real counterpart is the unpatched repo, "
            "where a response built from such a view renders the view's repr "
            "instead of its bytes; the failing test asserts the content equals "
            "the view's underlying bytes, which the repr rendering does not "
            "produce, so it would NOT resolve. This is the exact defect the fix "
            "corrects."
        ),
        "rationale": (
            "REJECT from the master clause `out = bodyBytes encodeStr fallback "
            "value`: `bodyBytes` pins the buffer arm to its underlying bytes "
            "(`.buffer b => b`), so a rival returning `fallback` there diverges "
            "at every byte-buffer view. Refuted at a byte-buffer view whose "
            "content [1] differs from `fallback` [2]. If it verified => "
            "SPEC-TOO-WEAK (the fix would be unobserved)."
        ),
        "witness": _witness("fun _ => []", "[(2 : UInt8)]", ".buffer [(1 : UInt8)]"),
    },
    {
        "id": "weak-buffer-valuemask",
        "kind": "uniqueness",
        "expect": "reject",
        # VALUE-MASK near-miss: on the buffer arm, return a byte list DERIVED
        # from the content (a spurious leading 0 prepended) instead of the
        # content verbatim. Same SHAPE (a byte list built from the view), wrong
        # VALUE. Catches a spec that pinned only "some byte list from the buffer"
        # rather than the underlying bytes exactly.
        "module": _impl(
            "    match value with\n"
            "    | .bytes  b => pure b\n"
            "    | .buffer b => pure (0 :: b)\n"
            "    | .text   s => pure (encodeStr s)\n"
            "    | .other    => pure fallback"),
        "refinement": (
            "transforms the buffer's bytes rather than carrying them verbatim (a "
            "spurious byte prepended). A faithful real counterpart that "
            "materialises a byte-buffer view into anything other than its "
            "underlying bytes changes the response content, and the failing test "
            "asserts the content equals the view's bytes EXACTLY, so any "
            "byte-for-byte deviation fails it. It does NOT resolve."
        ),
        "rationale": (
            "VALUE-MASK near-miss: same shape (a byte list derived from the "
            "buffer), wrong value. The master clause requires the buffer arm to "
            "equal its content EXACTLY (`.buffer b => b`), not a transform of it. "
            "Refuted at a byte-buffer view [1] (rival returns [0,1]) — a DISTINCT "
            "point from weak-prepatch-view (same value shape but `fallback` [] "
            "here vs [2] there, and the rival's wrong output is content-derived "
            "rather than the fallback), so the battery varies the `fallback` "
            "binder. Ports the nagini weak-encode-buffer. If it verified => "
            "SPEC-TOO-WEAK (buffer arm pinned only 'a function of the buffer')."
        ),
        "witness": _witness("fun _ => []", "[]", ".buffer [(1 : UInt8)]"),
    },
    {
        "id": "weak-bytes-to-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the .bytes arm / the other binary shape: a plain byte string is
        # (wrongly) routed to the fallback rendering instead of yielding its
        # bytes. The complement of weak-prepatch-view over the second binary
        # shape.
        "module": _impl(
            "    match value with\n"
            "    | .bytes  _ => pure fallback\n"
            "    | .buffer b => pure b\n"
            "    | .text   s => pure (encodeStr s)\n"
            "    | .other    => pure fallback"),
        "refinement": (
            "routes a plain byte string to the textual-rendering branch instead "
            "of yielding its bytes. A faithful real counterpart that renders a "
            "byte string as its repr breaks the long-standing behaviour that a "
            "byte-string body is emitted verbatim (the pass-to-pass byte-content "
            "cases), so it would NOT resolve those tests."
        ),
        "rationale": (
            "REJECT from the master clause: `bodyBytes` pins the bytes arm to its "
            "content (`.bytes b => b`), so a rival returning `fallback` there "
            "diverges at every plain byte string. Refuted at a plain byte string "
            "whose content [1] differs from `fallback` [2] — the only rival that "
            "moves the `value` binder to the `.bytes` shape. If it verified => "
            "SPEC-TOO-WEAK (bytes arm unconstrained)."
        ),
        "witness": _witness("fun _ => []", "[(2 : UInt8)]", ".bytes [(1 : UInt8)]"),
    },
    {
        "id": "weak-text-to-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the .text arm / the encodeStr binder: a textual value is
        # (wrongly) routed to the fallback rendering instead of the charset
        # encoding of its characters.
        "module": _impl(
            "    match value with\n"
            "    | .bytes  b => pure b\n"
            "    | .buffer b => pure b\n"
            "    | .text   _ => pure fallback\n"
            "    | .other    => pure fallback"),
        "refinement": (
            "routes a textual value to the object-fallback rendering instead of "
            "the charset encoding of its characters. A faithful real counterpart "
            "that renders a string via the fallback path emits the wrong bytes "
            "for string bodies, so the pass-to-pass string-content cases would "
            "NOT resolve."
        ),
        "rationale": (
            "REJECT from the master clause: `bodyBytes` pins the text arm to "
            "`encodeStr s`, so a rival returning `fallback` there diverges "
            "whenever the encoder's output differs from `fallback`. Refuted at a "
            "textual value with `encodeStr = fun _ => [1]` and `fallback = [2]` — "
            "the only rival that moves `value` to the `.text` shape and that "
            "moves the `encodeStr` binder off `fun _ => []`, exercising the "
            "encoder's role directly. If it verified => SPEC-TOO-WEAK (text arm "
            "unconstrained)."
        ),
        "witness": _witness("fun _ => [(1 : UInt8)]", "[(2 : UInt8)]", ".text ['a']"),
    },
    {
        "id": "weak-text-wrong-argument",
        "kind": "uniqueness",
        "expect": "reject",
        # ARGUMENT-MASK near-miss: the text arm DOES call the charset encoder (so
        # it is right about WHICH operation to perform, unlike
        # weak-text-to-fallback) but feeds it the WRONG argument — the empty
        # character list instead of the value's own characters. Isolates the
        # requirement that the encoder is applied to `s`, which no other rival
        # touches: every other witness pins `encodeStr` to a CONSTANT function,
        # under which "encoder of the wrong argument" is indistinguishable from
        # "encoder of the right argument". The witness therefore moves the
        # `encodeStr` binder to an argument-DEPENDENT function.
        "module": _impl(
            "    match value with\n"
            "    | .bytes  b => pure b\n"
            "    | .buffer b => pure b\n"
            "    | .text   _ => pure (encodeStr [])\n"
            "    | .other    => pure fallback"),
        "refinement": (
            "encodes a fixed empty character sequence rather than the textual "
            "value's own characters. A faithful real counterpart emits the "
            "encoding of the empty string for every textual body, so a response "
            "built from a non-empty string has empty content; the pass-to-pass "
            "string-content cases assert the content is the encoding of the "
            "string itself, so it would NOT resolve."
        ),
        "rationale": (
            "REJECT from the master clause: `bodyBytes` pins the text arm to "
            "`encodeStr s` — the encoder applied to THIS value's characters — not "
            "to the encoder applied to anything. Refuted at `.text ['a']` with an "
            "argument-dependent `encodeStr = fun s => s.map (fun _ => 3)`, where "
            "the spec demands [3] and the rival yields []. Verified out-of-band "
            "that none of the other reject witnesses discriminates this rival "
            "(all five fail against it), so this is the only case pinning the "
            "encoder's ARGUMENT. If it verified => SPEC-TOO-WEAK (text arm pinned "
            "only 'some output of the encoder')."
        ),
        "witness": _witness(
            "fun s => List.map (fun _ => (3 : UInt8)) s", "[]", ".text ['a']"),
    },
    {
        "id": "weak-buffer-encodes",
        "kind": "uniqueness",
        "expect": "reject",
        # The nagini weak-view-encodes analog, at the VALUE level the fallback
        # rivals cannot reach: the byte-buffer arm is diverted through the CHARSET
        # ENCODER rather than to `fallback`. Distinct from weak-prepatch-view
        # (which diverts that arm to `fallback`) and from weak-buffer-valuemask
        # (whose wrong value is content-derived): here the wrong value comes from
        # the encoder, the one operation the binary arms must never reach.
        "module": _impl(
            "    match value with\n"
            "    | .bytes  b => pure b\n"
            "    | .buffer _ => pure (encodeStr [])\n"
            "    | .text   s => pure (encodeStr s)\n"
            "    | .other    => pure fallback"),
        "refinement": (
            "pushes a byte-buffer view through the charset encoder instead of "
            "carrying its underlying bytes. A faithful real counterpart emits "
            "encoder output where the buffer's own bytes are required, so a "
            "response built from such a view does not have the view's bytes as "
            "its content; the failing test asserts exactly that equality, so it "
            "would NOT resolve."
        ),
        "rationale": (
            "REJECT from the master clause: `bodyBytes` pins the buffer arm to "
            "its content (`.buffer b => b`), and in particular the binary arms "
            "never route through the encoder. Refuted at a byte-buffer view with "
            "content [1] under `encodeStr = fun _ => [6]` and `fallback = []` — a "
            "point where BOTH the fallback rivals' wrong value ([]) and the "
            "content ([1]) differ from the rival's output ([6]), so no other "
            "witness in this battery covers it. Ports the nagini "
            "weak-view-encodes, which the earlier accounting wrongly recorded as "
            "collapsed. If it verified => SPEC-TOO-WEAK (buffer arm reachable by "
            "the encoder)."
        ),
        "witness": _witness("fun _ => [(6 : UInt8)]", "[]", ".buffer [(1 : UInt8)]"),
    },
    {
        "id": "weak-other-to-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # Attacks the .other arm / the fallback binder: an arbitrary non-binary,
        # non-text value yields the empty bytestring instead of its
        # rendered-then-encoded form.
        "module": _impl(
            "    match value with\n"
            "    | .bytes  b => pure b\n"
            "    | .buffer b => pure b\n"
            "    | .text   s => pure (encodeStr s)\n"
            "    | .other    => pure []"),
        "refinement": (
            "yields the empty bytestring for an arbitrary value instead of its "
            "rendered-then-encoded form. A faithful real counterpart that drops "
            "the rendered content emits an empty body where a non-empty encoded "
            "rendering is required (the pass-to-pass non-string-content cases), "
            "so it would NOT resolve those tests."
        ),
        "rationale": (
            "REJECT from the master clause: `bodyBytes` pins the other arm to "
            "`fallback`, so a rival returning `[]` there diverges whenever "
            "`fallback` is non-empty. Refuted at `.other` with `fallback = [1]` — "
            "the only rival that moves `value` to the `.other` shape and that "
            "isolates the `fallback` binder's role. If it verified => "
            "SPEC-TOO-WEAK (other arm unconstrained)."
        ),
        "witness": _witness("fun _ => []", "[(1 : UInt8)]", ".other"),
    },
]

AXIOM_TESTS = []


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 12 SPEC cases (2
# soundness positives, 1 admissibility, 2 frame-mutation rivals, 7 uniqueness
# rivals) over a Value carrier with an integer `kind` tag in {OCTETS, VIEW,
# TEXT, OTHER}. This bundle models the SAME dispatch as ONE method `makeBytes`
# whose `value : Body` is the faithful carrier of the sibling's `kind` reduced
# to the four disjoint shapes the routine reacts to (bytes / buffer / text /
# other), with the two encode/fallback branches abstracted as the FREE inputs
# `encodeStr` / `fallback` (mapping.md §1–2).
#
#   sibling case                  -> here
#   -----------------------------------------------------------------------
#   pos-helper-reorder            -> pos-arm-reorder            PORTED
#   pos-oracle-grounded           -> pos-direct                 PORTED
#   admiss-shape                  -> admiss-dispatch-nondeg…    RE-AIMED
#   frame-mutate-data             -> (none)                     OMITTED (vacuous)
#   frame-mutate-kind             -> (none)                     OMITTED (vacuous)
#   weak-prepatch-view            -> weak-prepatch-view         PORTED
#   weak-view-encodes             -> weak-buffer-encodes        PORTED
#   weak-encode-buffer            -> weak-buffer-valuemask      PORTED
#   weak-always-encode            -> weak-bytes-to-fallback     PORTED (re-aimed)
#                                    + weak-prepatch-view       (buffer half)
#   weak-always-buf               -> weak-text-to-fallback      PORTED (re-aimed)
#                                    + weak-other-to-empty      (other half)
#   weak-swap-arms                -> (none)                     OMITTED (redundant)
#
# OMITTED — frame-mutate-data / frame-mutate-kind (2). VACUOUS on this backend.
#   Both nagini rivals write through a half-permission reference to a field of
#   the read-only input and are rejected for INSUFFICIENT PERMISSION. This
#   backend is referentially transparent: the inputs are immutable values, this
#   bundle declares no `mut` binder, and there is no heap/aliasing/permission
#   system. There is no read-only input to overwrite, so the class is vacuous;
#   no substitute probe fabricated.
#
# PORTED (was wrongly recorded COLLAPSED; corrected by audit) —
#   weak-view-encodes -> weak-buffer-encodes. The earlier accounting claimed this
#   sibling collapsed into weak-prepatch-view because both attack the single
#   `.buffer` constructor, and that its value-level distinctness was "covered by
#   weak-buffer-valuemask". Both halves of that claim are FALSE, measured:
#   weak-prepatch-view diverts the buffer arm to `fallback` while the sibling
#   diverts it through the ENCODER, and weak-buffer-valuemask's wrong value is
#   CONTENT-DERIVED (`0 :: b`), so neither pins the encoder out of the binary
#   arms. Which arm is wrong is not the only axis a rival varies — WHICH WRONG
#   VALUE it substitutes is a second one, and an arm-identity argument cannot
#   discharge it. The case is now carried as weak-buffer-encodes, refuted at a
#   point ([1] content, [] fallback, encoder -> [6]) that no other witness here
#   reaches. Not a carrier collapse: the distinction is expressible and now
#   expressed.
#
# ADDED by audit — weak-text-wrong-argument. Not a nagini port; it closes a gap
#   the ported set left open. Every reject witness above binds `encodeStr` to a
#   CONSTANT function, under which an impl that applies the encoder to the WRONG
#   ARGUMENT is indistinguishable from one that applies it correctly. Measured:
#   an impl returning `encodeStr []` on the text arm is refuted by NONE of the
#   five original witnesses (all five fail against it), yet the spec does reject
#   it once the witness moves `encodeStr` to an argument-dependent function. The
#   master clause pins `encodeStr s` — the encoder applied to THIS value's
#   characters — and that was the one part of the clause no case tested.
#
# RE-AIMED — weak-always-encode / weak-always-buf. Nagini's "always encode" and
#   "always carry buf" rivals each violate a WHOLE branch class (both buffer
#   kinds, or both non-buffer kinds) at once. On this four-constructor carrier
#   the same violations are expressed per-arm and split into independent rivals
#   so the `value` binder is moved across all four shapes: the buffer/bytes arms
#   (weak-prepatch-view + weak-bytes-to-fallback) and the text/other arms
#   (weak-text-to-fallback + weak-other-to-empty). Each per-arm rival is a
#   strictly finer probe than the sibling's all-or-nothing rival.
#
# OMITTED — weak-swap-arms (1). Redundant on this carrier. The sibling inverts
#   the entire dispatch (buffers encode, non-buffers carry buf), violating both
#   branch classes at once. Here every one of the four arms is already attacked
#   independently by a dedicated per-arm rival, each with its own discriminating
#   witness; a combined arm-swap would add no clause or binder coverage the
#   per-arm rivals do not already provide. Omitted as strictly redundant, not
#   for difficulty; no substitute fabricated.
#
# COVERAGE. There is ONE independent top-level clause (the master equality
#   `out = bodyBytes encodeStr fallback value`); it is DEFENDED by two soundness
#   positives + one admissibility case and ATTACKED by seven rivals. The `value`
#   binder is moved across ALL FOUR shapes (buffer: weak-prepatch-view,
#   weak-buffer-valuemask & weak-buffer-encodes; bytes: weak-bytes-to-fallback;
#   text: weak-text-to-fallback & weak-text-wrong-argument; other:
#   weak-other-to-empty). The `fallback` binder takes [2], [], [2], [], [1], []
#   across the reject witnesses. The `encodeStr` binder is moved off `fun _ => []`
#   three ways, and the third is the one that matters: to a CONSTANT non-empty
#   function (`fun _ => [1]` / `fun _ => [6]`, exercising the encoder's role as a
#   source of output) and — only by weak-text-wrong-argument — to an
#   ARGUMENT-DEPENDENT function (`fun s => s.map (fun _ => 3)`), which is what
#   pins the encoder's ARGUMENT rather than merely its output. Under a constant
#   encoder those two are the same point spelled twice, which is exactly the
#   variation the coverage reporter cannot see; it is why that case exists.
#   Seven DISTINCT input points, so no rival is refuted at the same point as
#   another.
#
# AXIOM lane: DROPPED (AXIOM_TESTS = []). The sibling carries axiom-soundness /
#   containment probes over the real stdlib callees; that is G-AX's job
#   (axiom_check.py / mapping.md) and the G-PBT gate ignores AXIOM_TESTS
#   regardless.
