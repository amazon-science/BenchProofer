# properties.py — PBT falsification battery for django__django-13516.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions regions untouched) and swaps ONLY text inside
# the # impl-start/# impl-end region; the runner checks each with Nagini verify +
# markers.same_spec. AXIOM_TESTS are real-callee probes run in Docker.
#
# Defended surface (read from model.py + refinement.md / mapping.md + instance.json):
#
#   drain_buffer(stream: OutputStream) -> None        [models OutputWrapper.flush]
#     Requires:
#       Acc(stream.out, 1/2)              -- the wrapped-stream REFERENCE is READ-ONLY
#       Acc(stream.out_can_drain, 1/2)    -- the capability BIT is READ-ONLY
#       stream.out.drain_count_pred()     -- FULL predicate (the invocation count IS advanced)
#       MustTerminate(2)                  -- bounded work: a non-returning body is REJECTED
#                                            (no vacuous discharge of the postconditions)
#     Ensures (frame):  Acc(stream.out,1/2), Acc(stream.out_can_drain,1/2),
#                       stream.out.drain_count_pred()
#     Ensures (wrapper unchanged, load-bearing):
#       stream.out is Old(stream.out)
#       stream.out_can_drain == Old(stream.out_can_drain)
#     Ensures (forward, the DISCRIMINATING clause — what the F2P observes):
#       (4) Implies(stream.out_can_drain,
#                   stream.out.get_drained() == Old(stream.out.get_drained()) + 1)
#       (5) Implies(not stream.out_can_drain,
#                   stream.out.get_drained() == Old(stream.out.get_drained()))
#
#   The invocation count is held behind @Predicate drain_count_pred and read ONLY
#   via @Pure get_drained (directive-8 echo hardening), so clause (4) is
#   dischargeable ONLY by RUNNING the drain primitive Sink.do_drain
#   (Unfold/+1/Fold) — a bare field write `stream.out.drained = ...` has no
#   permission (the field is folded inside the predicate) and is rejected. There
#   is no opaque answer-key oracle: get_drained() == Old(get_drained())+1 is a
#   GROUNDED count of work actually performed (see 'assessment').
#
# F2P: test_outputwrapper_flush — wraps a StringIO (flushable => out_can_drain==True),
#      mocks its flush, runs a command that calls self.stdout.flush(), asserts
#      mocked_flush.called is True (the underlying flush WAS invoked — count 0->1).
# The bug (model_prepatch): OutputWrapper inherits TextIOBase.flush (a no-op) and
# never forwards, so on a flushable stream the count stays at 0 — fails clause (4).
#
# REGION-SURGERY: every spec variant is built by _swap on _BASE editing ONLY the
# impl region (the whole body is `if stream.out_can_drain: stream.out.do_drain()`).
# The frozen spec is never touched; same_spec is GUARANTEED.

from pathlib import Path

INSTANCE = "django__django-13516"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_DIR = Path(__file__).parent
_BASE = (_DIR / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Stable anchors inside the impl region (each present exactly once in _BASE).
# ---------------------------------------------------------------------------
_IMPL = "    if stream.out_can_drain:\n        stream.out.do_drain()"
_GUARD = "    if stream.out_can_drain:\n"
assert _BASE.count(_IMPL) == 1, "impl body anchor drifted"
assert _BASE.count("    # impl-start\n") == 1, "impl-start anchor drifted"


# ===========================================================================
# POSITIVE CONTROLS / ADMISSIBILITY  (expect "verify")
# ===========================================================================

# (5a) POSITIVE CONTROL — guard inversion + early return. Semantically identical
# to the gold `if out_can_drain: do_drain()`: on the not-flushable path it
# returns early (count untouched => clause 5, clause 4 vacuous); on the flushable
# path it runs the drain primitive exactly once (count +1 => clause 4). No write
# to any field, so the wrapper-unchanged and frame clauses still hold. This is a
# branch-reorder/early-return reshape (directive-3 safe — no loop-direction flip,
# no fold lemma) and keeps every gold obligation the proof needs.
_POS_EARLY_RETURN = _swap(
    _BASE, _IMPL,
    "    if not stream.out_can_drain:\n"
    "        return\n"
    "    stream.out.do_drain()",
)

# (5b) POSITIVE CONTROL — the honest INLINE drain (the literal Sink.do_drain
# body: Unfold/+1/Fold on drain_count_pred). drain_buffer holds the predicate at
# FULL, so unfolding, incrementing the count, and refolding is the REAL increment
# work — NOT an echo (an echo would skip the predicate dance and write the raw
# field, which is rejected; see weak-echo-fieldwrite). Must verify; it shows
# clause (4) is dischargeable by doing the work directly, so the spec is not
# over-fit to calling do_drain by name => not SPEC-TOO-STRONG.
_POS_INLINE = _swap(
    _BASE, _IMPL,
    "    if stream.out_can_drain:\n"
    "        Unfold(stream.out.drain_count_pred())\n"
    "        stream.out.drained = stream.out.drained + 1\n"
    "        Fold(stream.out.drain_count_pred())",
)

# (6) ADMISSIBILITY — construct a fresh, F2P-shaped wrapper (a flushable Sink,
# out_can_drain==True, the StringIO case) entirely inside the impl region and
# assert drain_buffer's FULL precondition is establishable on it: full
# drain_count_pred(), the read-only out / out_can_drain accesses, and the
# capability bit True. (A self-recursive drain_buffer(probe) call would need a
# Decreases measure the spec does not carry — that is a PROOF gap, not a spec
# defect, so we exercise the Requires-establishability directly, per the 10554
# pattern.) After the probe block the gold body runs verbatim on the real
# `stream`. If this cannot verify, the precondition rejects a normal F2P-shaped
# input => PRECOND-TOO-STRONG.
_ADMISS = _swap(
    _BASE, "    # impl-start\n",
    "    # impl-start\n"
    "    # ADMISSIBILITY PROBE: a fresh F2P-shaped flushable wrapper establishes\n"
    "    # the full drain_buffer precondition.\n"
    "    probe_sink = Sink()\n"
    "    probe = OutputStream(probe_sink, True)  # type: OutputStream\n"
    "    Assert(probe.out.drain_count_pred())\n"
    "    Assert(probe.out_can_drain)\n"
    "    Assert(probe.out is probe_sink)\n"
    "    Assert(probe.out.get_drained() == 0)\n",
)


# ===========================================================================
# UNIQUENESS RIVALS  (spec-too-weak probes — expect "reject")
# ===========================================================================

# (1) FRAME MUTATION — MANDATORY (#1 weakness class). stream.out_can_drain is
# READ-ONLY at Acc(.,1/2). This rival WRITES the capability bit before the gold
# body. A store needs FULL permission, so it MUST be rejected for INSUFFICIENT
# PERMISSION (not a value mismatch). The gold body is kept verbatim after the
# write so the rejection is attributable solely to the write.
_RIVAL_FRAME_BIT = _swap(
    _BASE, _IMPL,
    "    stream.out_can_drain = stream.out_can_drain\n"
    "    if stream.out_can_drain:\n"
    "        stream.out.do_drain()",
)

# (1b) FRAME MUTATION (supporting) — write the read-only wrapped-stream REFERENCE
# (Acc(stream.out, 1/2)). Same insufficient-permission rejection; targets the
# other 1/2 read-only field. Gold body kept verbatim after the write.
_RIVAL_FRAME_OUT = _swap(
    _BASE, _IMPL,
    "    stream.out = stream.out\n"
    "    if stream.out_can_drain:\n"
    "        stream.out.do_drain()",
)

# (2) ECHO / directive-8 — try to discharge clause (4) by writing the raw
# invocation count directly, WITHOUT running the drain primitive (no
# Unfold/Fold). The count `drained` is folded inside @Predicate drain_count_pred,
# so a bare field write has no permission and MUST be rejected ("insufficient
# permission to access stream.out.drained"). The guard and structure are
# otherwise the gold shape, so the rejection is attributable to the echo write.
_RIVAL_ECHO = _swap(
    _BASE, _IMPL,
    "    if stream.out_can_drain:\n"
    "        stream.out.drained = stream.out.get_drained() + 1",
)

# (3a) PARTIAL-DOMAIN — drop the capability guard: drain UNCONDITIONALLY. Correct
# on the flushable sub-domain (count +1 => clause 4), but on the NOT-flushable
# sub-domain it advances the count => violates clause (5)
# Implies(not out_can_drain, get_drained()==Old(get_drained())).
_RIVAL_UNCOND = _swap(_BASE, _IMPL, "    stream.out.do_drain()")

# (3b) PARTIAL-DOMAIN / prepatch shape — never drain (a no-op). This is exactly
# the pre-patch inherited TextIOBase.flush behaviour (== model_prepatch.py).
# Correct on the not-flushable sub-domain (clause 5), but on the FLUSHABLE
# sub-domain the count stays at Old => violates clause (4). Supporting case.
_RIVAL_NOOP = _swap(_BASE, _IMPL, "    pass")


SPEC_TESTS = [
    # ---- positive controls / admissibility (must VERIFY) ----
    {
        "id": "pos-early-return",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_EARLY_RETURN,
        "rationale": "structurally-different CORRECT impl (guard inverted + early "
        "return, then unconditional do_drain) — semantically identical to the gold "
        "if/do_drain: not-flushable returns early (count untouched => clause 5), "
        "flushable runs the primitive once (=> clause 4); no field write so the "
        "wrapper-unchanged/frame clauses hold. Branch reshape only (directive-3 "
        "safe). Must verify, else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-inline-drain",
        "kind": "soundness",
        "expect": "verify",
        "module": _POS_INLINE,
        "rationale": "the honest INLINE drain (the literal do_drain body: "
        "Unfold/+1/Fold on drain_count_pred, which drain_buffer holds at FULL). "
        "This is the REAL increment work, not an echo; it must verify, showing "
        "clause (4) is dischargeable by performing the increment directly and the "
        "spec is not over-fit to invoking do_drain by name. Else SPEC-TOO-STRONG.",
    },
    {
        "id": "admiss-fresh-wrapper",
        "kind": "admissibility",
        "expect": "verify",
        "module": _ADMISS,
        "rationale": "construct a fresh F2P-shaped flushable wrapper (Sink + "
        "OutputStream(.,True), the StringIO case) and assert drain_buffer's FULL "
        "precondition is establishable on it (full drain_count_pred(), the "
        "read-only accesses, out_can_drain True, count 0). If the precondition "
        "rejects a normal input => PRECOND-TOO-STRONG. (Self-recursion avoided: it "
        "would need a Decreases measure the spec lacks — a proof gap, not a defect.)",
    },

    # ---- uniqueness rivals (must be REJECTED) ----
    {
        "id": "frame-mutate-capability-bit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_FRAME_BIT,
        "refinement": "no faithful real patch corresponds to this: OutputWrapper.flush "
        "never reassigns its own capability — hasattr(self._out,'flush') is a read-only "
        "probe and the wrapper's fields are not rewritten by flush. The rival exists "
        "solely to test whether the read-only (1/2) capability-bit precondition can be "
        "subverted by overwriting it. There is no resolving patch that writes its own "
        "drain-capability bit, so a verifying rival would be a pure verify-not-resolve "
        "artifact (vacuous satisfaction of the wrapper-unchanged clause).",
        "rationale": "MANDATORY frame-mutation probe. The store "
        "`stream.out_can_drain = ...` writes through a 1/2 (read-only) reference and "
        "MUST fail for INSUFFICIENT PERMISSION (a store needs full Acc(stream.out_can_drain)), "
        "NOT a value mismatch; the gold body is kept verbatim so the rejection is "
        "attributable to the write. Rejection source: the PERMISSION SYSTEM (directive 5). "
        "If it verified => SPEC-TOO-WEAK (frame protection hollow).",
    },
    {
        "id": "frame-mutate-out-ref",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_FRAME_OUT,
        "refinement": "OutputWrapper.flush never reassigns self._out (the wrapped stream "
        "reference is set once in __init__ and only read thereafter). A patch that "
        "rebound self._out inside flush would change which stream subsequent writes go "
        "to — diverging from gold and breaking the surrounding command output P2P tests. "
        "No resolving patch rewrites the wrapped-stream reference; a verifying rival is a "
        "verify-not-resolve artifact.",
        "rationale": "supporting frame-mutation probe on the OTHER read-only field. "
        "`stream.out = ...` writes through Acc(stream.out,1/2) and MUST fail for "
        "INSUFFICIENT PERMISSION. Rejection source: the PERMISSION SYSTEM (directive 5).",
    },
    {
        "id": "weak-echo-fieldwrite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_ECHO,
        "refinement": "there is no faithful patch that fabricates the underlying stream's "
        "flush-invocation count without actually calling flush. The only way to make the "
        "F2P observe `mocked_flush.called is True` (count 0->1) is to INVOKE the underlying "
        "flush; a patch that 'pretended' it flushed (set a counter, or did nothing) would "
        "leave mocked_flush.called False and FAIL test_outputwrapper_flush — verify-not-resolve.",
        "rationale": "directive-8 echo probe. The clause-(4) observable get_drained() is "
        "folded inside @Predicate drain_count_pred; a bare field write "
        "`stream.out.drained = stream.out.get_drained() + 1` (no Unfold/Fold) has NO "
        "permission and MUST be rejected ('insufficient permission to access "
        "stream.out.drained'). Rejection source: the abstraction PREDICATE + PERMISSION "
        "SYSTEM — the count can advance ONLY by running the drain primitive. If it "
        "verified => SPEC-TOO-WEAK (the observable could be echoed without doing the work).",
    },
    {
        "id": "weak-drop-guard-unconditional",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_UNCOND,
        "refinement": "dropping the hasattr guard — `self._out.flush()` unconditionally — "
        "raises AttributeError on a wrapped stream that has NO flush attribute (exactly "
        "the case the guard exists for). On the non-flushable sub-domain the gold is a "
        "harmless no-op; an unguarded forward diverges (raises) and is not a faithful "
        "resolving patch — the deep model (G-AX) checks the no-raise no-op on a "
        "NoFlushStream. A patch that crashes flush() on a non-flushable wrapped stream "
        "would break management-command output and not resolve.",
        "rationale": "partial-domain probe. Correct on the flushable sub-domain (count "
        "+1 => clause 4), but on `not out_can_drain` it advances the count and violates "
        "clause (5) Implies(not out_can_drain, get_drained()==Old(get_drained())). "
        "Rejection source: postcondition clause (5). If it verified => SPEC-TOO-WEAK.",
    },
    {
        "id": "weak-noop-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _RIVAL_NOOP,
        "refinement": "this is the PRE-PATCH behaviour (== model_prepatch.py): the "
        "inherited TextIOBase.flush no-op never forwards to the underlying stream. On the "
        "flushable F2P case (StringIO) the underlying flush is never invoked, so "
        "mocked_flush.called is False and test_outputwrapper_flush FAILS — it does NOT "
        "resolve (it is the exact bug the patch fixes).",
        "rationale": "supporting partial-domain probe. Correct on the not-flushable "
        "sub-domain (clause 5), but on the FLUSHABLE sub-domain the count stays at Old "
        "and violates clause (4) Implies(out_can_drain, get_drained()==Old(get_drained())+1). "
        "Rejection source: postcondition clause (4) — the discriminating clause G-DIFF "
        "fails on. If it verified => SPEC-TOO-WEAK.",
    },
]


# ===========================================================================
# AXIOM LANE — there is NO consumed @ContractOnly axiom (meta.json axioms == []).
# The changed forwarding is an A-reference deep model: Sink.do_drain's count bump
# + the out_can_drain guard model the real OutputWrapper.flush. We re-run that
# real-callee equivalence (axiom_check.py's logic, read on the HOST and embedded
# into a self-contained probe — the runner mounts only the probe at /work) as an
# axiom-soundness check, with apply_gold=True (the deep model describes the
# POST-PATCH behaviour; the eval image sits at base_commit, so the gold patch must
# be applied for OutputWrapper.flush to forward). If the REAL post-patch
# OutputWrapper.flush ever disagrees with the deep model — invoked exactly once
# iff flushable, harmless no-op (no raise) otherwise, wrapper unchanged — the
# A-reference is UNSOUND.
#
# A containment probe is included: the model can reach OutputWrapper.flush in
# exactly two configurations of the wrapped stream — flushable (out_can_drain
# True, the StringIO/CountingStream case) and non-flushable (out_can_drain False,
# the NoFlushStream case). axiom_check.py exercises BOTH (and repeated calls), so
# every caller-reachable configuration lies inside the validated domain; there is
# no caller-reachable input outside it => no AXIOM-TOO-WEAK-FOR-CALLER.
# ===========================================================================

_AXIOM_CHECK_SRC = (_DIR / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-ref-flush-forward-equals-deep-model",
        "axiom": "Sink.do_drain (the out_can_drain-guarded forward)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "the A-reference deep model (Sink.do_drain count bump + the "
        "out_can_drain guard) must equal the REAL post-patch OutputWrapper.flush. This "
        "probe (axiom_check.py verbatim, stdlib + Django only) runs the real wrapper "
        "over 299 observations: a mocked StringIO (the F2P case) asserting exactly one "
        "underlying flush, an explicit flush-counting stream (one wrapper.flush() => "
        "exactly one underlying flush; a second => exactly one more), and a NoFlushStream "
        "asserting a harmless no-op (no touch, no raise), wrapper unchanged. Exit 0 iff "
        "every observation matches the deep model; any disagreement (under-/over-flush, "
        "a raise on the non-flushable path, or a no-op on the flushable path) => the "
        "A-reference is UNSOUND. apply_gold=True because the image is at base_commit and "
        "the forward only exists post-patch (without it the probe correctly fails "
        "'expected exactly 1 underlying flush, got 0' — the bug).",
    },
    {
        "id": "ax-cover-caller-reaches-both-capabilities",
        "axiom": "Sink.do_drain (the out_can_drain-guarded forward)",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "containment: the model reaches OutputWrapper.flush in exactly two "
        "wrapped-stream configurations — flushable (out_can_drain True) and non-flushable "
        "(out_can_drain False). axiom_check.py exercises BOTH (StringIO + CountingStream "
        "for True; NoFlushStream for False) plus repeated calls, so every "
        "caller-reachable configuration lies inside the validated domain. There is no "
        "caller-reachable wrapped-stream the deep model does not cover, so no "
        "AXIOM-TOO-WEAK-FOR-CALLER. The behaviour is flag-independent (a plain hasattr "
        "guard regardless of configuration). Exit 0 confirms both configurations hold.",
    },
]
