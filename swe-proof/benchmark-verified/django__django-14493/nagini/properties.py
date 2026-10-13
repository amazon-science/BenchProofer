# properties.py — PBT falsification battery for django__django-14493. NOT a Nagini
# module; a record of adversarially-reasoned cases the runner (swebench_nagini.pbt)
# executes and stamps RESULT onto. Spec cases are FULL model.py variants that share
# the FROZEN spec byte-for-byte (region surgery: ONLY the text strictly between the
# function's `# impl-start` / `# impl-end` — which INCLUDES the nested invariants
# region — is edited; the spec view / contracts / pure helpers / proof lemmas are
# never touched), checked by Nagini verify + markers.same_spec.
#
# Defended surface (read from model.py / refinement.md / mapping.md / instance.json):
#   run_passes(pass_changed: List[int], max_passes: int) -> bool
#   Models the gold one-line fix in HashedFilesMixin.post_process: initialise the
#   loop flag `substitutions = False` BEFORE the `for i in range(max_post_process_
#   passes)` loop, so the post-loop read `if substitutions:` is well defined even when
#   the loop body never runs (max_post_process_passes == 0). The bug: without the
#   pre-loop init the zero-pass path reads `substitutions` undefined -> UnboundLocal-
#   Error. The F2P (NoPostProcessReplacedPathStorage, max_post_process_passes = 0)
#   runs collectstatic and asserts it completes ('post-processed' in stdout) — i.e.
#   NO crash and NO spurious "Max post-process passes exceeded." on the zero-pass path.
#
#   PRECONDITION:
#     (P1) Requires(Acc(list_pred(pass_changed), 1/2))      # HALF permission => READ-ONLY
#     (P2) Requires(0 <= max_passes and max_passes <= len(pass_changed))
#   POSTCONDITION (three clauses; one framing/permission + two LOAD-BEARING):
#     (Q0) Ensures(Acc(list_pred(pass_changed), 1/2))       # returns the read permission
#     (Q1) Ensures(0 <= max_passes and max_passes <= len(pass_changed))  # frame on the int
#     (Q2) Ensures(Result() == (max_passes > 0 and all_changed(ToSeq(pass_changed), max_passes)))
#            -- the running flag value: at least one pass ran AND every pass that ran
#               reported a change (loop breaks at the first change-free pass).
#     (Q3) Ensures(Implies(max_passes == 0, Result() == False))
#            -- the ZERO-PASS BOUNDARY (the bug): with zero allowed passes the flag
#               reads as "no change to report" — a DEFINITE False, never absent.
#   Q2 pins the value on EVERY path including loop-exit; Q3 pins the zero-pass path to
#   a definite False. Together they require the function to RETURN on every path (the
#   prepatch, which reads the flag undefined on the zero-pass path, cannot verify) and
#   to return EXACTLY the grounded closed form. No slack.
#
# all_changed is a @Pure front-recursive fold over PSeq[int]: all_changed(flags, 0) is
#   True, all_changed(flags, n) = flags[n-1] != 0 and all_changed(flags, n-1). It is
#   GROUNDED entirely in the arguments (ToSeq(pass_changed), max_passes) and fully
#   unfolded — NOT a @ContractOnly axiom, NOT an opaque answer-key, NOT an exact marker.
#   lemma_unfold / lemma_change_free_kills are proof-only methods (module level, OUTSIDE
#   the impl region — frozen) the loop calls to discharge the forward-extend and the
#   change-free-kills-the-prefix inductive steps.
#
# FRAME-MUTATION lane is MANDATORY: `pass_changed` is Acc(list_pred(pass_changed),1/2)
#   (read-only, in AND out). A rival that WRITES it must be REJECTED for INSUFFICIENT
#   PERMISSION. Byte-fuzzers never think to mutate the input; this is the #1 weakness
#   class. The real loop only READS the per-pass outcomes; any write would corrupt the
#   per-pass change-tracking the post-loop decision depends on.
#
# UNGROUNDED-ORACLE-ECHO: N/A as a *wrong* echo. Q2 is pinned to
#   `max_passes > 0 and all_changed(ToSeq(pass_changed), max_passes)` — GROUNDED in the
#   arguments via the @Pure fully-unfolded fold all_changed. The pure region COMPUTES
#   the flag from the input; it does not assert an opaque answer. There is therefore no
#   value an echo could carry that satisfies Q2/Q3 yet is wrong — the unique satisfier
#   IS the grounded decision. So instead of a wrong echo we include the HONEST cheapest
#   faithful impl (pos-direct: return the closed form) as a positive control, which
#   MUST verify (it IS the postcondition, grounded in the args). See 'assessment'.
#
# CONTROL-FLOW-EFFECT lane: the ONLY behavioural effects are control-flow forks — the
#   early-stop `return False` and the post-loop `return substitutions`. The value
#   abstraction does NOT drop them: Q2 governs the loop-exit value and Q3 governs the
#   zero-pass path, so a return-value swap on either fork is observable to the spec.
#   weak-early-true (flip the early-stop return) and weak-zero-true (flip the zero-pass
#   return) are the discriminators; no separate capability token is needed because the
#   return value IS the observable.
#
# PARTIAL-DOMAIN lane: heavily exercised — the bug lives entirely in ONE sub-domain.
#   weak-zero-true is correct on every max_passes>0 input but diverges on EXACTLY the
#   zero-pass sub-domain (the F2P discriminator); weak-early-true is correct until the
#   first change-free pass and diverges on the change-free sub-domain.
#
# TOTALITY lane: the zero-pass divergence has TWO halves and each has its own rival.
#   weak-zero-true returns a WRONG VALUE there (rejected by Q3); weak-prepatch does not
#   return AT ALL there (rejected by the postcondition region declaring no Exsures, i.e.
#   'method raises no exceptions'). The second is what the pre-patch repo actually does —
#   `if substitutions:` on an unbound local — and the spec view demands the operation
#   "complete normally and return a definite boolean on every path", so the abrupt exit
#   is a spec-attributable rejection, NOT nagini's contract-independent definite-
#   assignment check (see the weak-prepatch note for why the literal unbound read is
#   both untranslatable and, once made translatable, uninformative).
#
# NON-VACUITY: ctl-zero-reachable puts `Assert(False)` on the zero-pass path and MUST be
#   rejected. Without it, both zero-pass rejections above would be consistent with a
#   dead branch: an infeasible guard refutes every rival while proving nothing.
#
# AXIOM lane: meta.axioms == [] AND deep_model_references has NO A-reference to a
#   library callee (all_changed is a DEEP model of the in-function loop itself, not an
#   abstraction of an external callee — refinement.md / mapping.md §3). There is no
#   @ContractOnly axiom and no library-callee to execute in Docker, so AXIOM_TESTS = [].
#   axiom_check.py performs the deep-model FAITHFULNESS check (G-AX analogue) on the
#   host; it is not re-encoded here as there is no callee-input domain to probe.
from pathlib import Path

INSTANCE = "django__django-14493"
FLOAT_ENCODING = None  # meta.json float_encoding is null


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen FUNCTION impl region body, verbatim — everything strictly BETWEEN the
# function's `# impl-start` / `# impl-end` (INCLUDING the nested invariants region).
# Every spec variant _swap()s ONLY this block, so the edit never touches the spec
# (axioms/pure/pre-/post-conditions regions, the function signature, and the proof
# lemmas lemma_unfold / lemma_change_free_kills, which live OUTSIDE the impl region).
# same_spec is computed over the spec_view, which elides every impl region (and the
# nested invariants), so swapping inside here is GUARANTEED same_spec.
_IMPL = """\
    # Initialise the flag BEFORE the loop so it is defined even when the loop
    # body never runs (max_passes == 0). This is the whole behaviour.
    substitutions = False
    i = 0
    while i < max_passes:
        # invariants-start
        Invariant(Acc(list_pred(pass_changed), 1 / 2))
        Invariant(0 <= i and i <= max_passes and max_passes <= len(pass_changed))
        # Before each iteration the flag reflects the passes run so far: True
        # iff at least one pass ran (i > 0) and all of the first i passes changed.
        Invariant(substitutions == (i > 0 and
                                    all_changed(ToSeq(pass_changed), i)))
        # The loop is only re-entered after a change-reporting pass, so reaching
        # i > 0 means the flag is set and the first i passes all changed.
        Invariant(i == 0 or substitutions)
        # invariants-end
        substitutions = pass_changed[i] != 0
        Assert(ToSeq(pass_changed)[i] == pass_changed[i])
        if not substitutions:
            # Early stop: pass i reported no change. Then the full count of
            # passes is not all-changed, so the closed form is False regardless
            # of the remaining allowance.
            lemma_change_free_kills(ToSeq(pass_changed), i, max_passes)
            return False
        # pass i changed: extend the all-changed prefix from i to i+1.
        lemma_unfold(ToSeq(pass_changed), i + 1)
        i = i + 1
    # Normal completion: i == max_passes, so the running flag already equals the
    # full-range closed form (congruence over the single count argument).
    return substitutions
"""

assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"


def _impl(new_body):
    """Full model.py variant with ONLY the function impl region body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness / admissibility) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-reshape: structurally DIFFERENT but behaviourally identical. Two source
# reshapes that keep EVERY gold proof obligation verbatim (the loop bound, all four
# invariants incl. the load-bearing substitutions==(i>0 and all_changed(...)) one, the
# `Assert(ToSeq(pass_changed)[i] == pass_changed[i])` framing pin, BOTH lemma calls,
# the early-stop, and the post-loop return):
#   (a) the two pre-loop assignments `substitutions = False` / `i = 0` are reordered
#       (independent — neither reads the other), and
#   (b) the per-pass `substitutions = pass_changed[i] != 0` is rewritten as an explicit
#       guarded assignment with the SAME value (if pass_changed[i] != 0: True else False).
# No loop-direction flip, no dropped lemma, no forward-append against the front-
# recursive fold (directives 2/3 respected). If it FAILS => SPEC-TOO-STRONG.
_POS_RESHAPE = """\
    # Reordered pre-loop init (independent assignments) + explicit per-pass guard.
    i = 0
    substitutions = False
    while i < max_passes:
        # invariants-start
        Invariant(Acc(list_pred(pass_changed), 1 / 2))
        Invariant(0 <= i and i <= max_passes and max_passes <= len(pass_changed))
        Invariant(substitutions == (i > 0 and
                                    all_changed(ToSeq(pass_changed), i)))
        Invariant(i == 0 or substitutions)
        # invariants-end
        if pass_changed[i] != 0:
            substitutions = True
        else:
            substitutions = False
        Assert(ToSeq(pass_changed)[i] == pass_changed[i])
        if not substitutions:
            lemma_change_free_kills(ToSeq(pass_changed), i, max_passes)
            return False
        lemma_unfold(ToSeq(pass_changed), i + 1)
        i = i + 1
    return substitutions
"""
assert _POS_RESHAPE != _IMPL, "pos-reshape did not rewrite"


# pos-direct: the HONEST cheapest faithful impl (the grounded-oracle positive control,
# standing in for the absent wrong-echo). Because Q2 pins Result() to the @Pure fold
# all_changed — which is GROUNDED in the arguments and fully unfolded — the unique
# satisfier IS that closed form, and returning it directly is CORRECT, not a cheat.
# It must VERIFY (the postcondition is literally `Result() == <this expression>` and
# Q3 follows: max_passes==0 makes the first conjunct False). No loop, no lemma needed.
# If a GROUNDED oracle could be echoed to a WRONG-yet-verifying answer this control
# would have a wrong twin; it does not (see 'assessment'). If it FAILS => SPEC-TOO-
# STRONG (the spec rejects the very value it pins).
_POS_DIRECT = """\
    # The postcondition pins Result() to this grounded closed form; return it.
    result = max_passes > 0 and all_changed(ToSeq(pass_changed), max_passes)
    return result
"""
assert _POS_DIRECT != _IMPL, "pos-direct did not rewrite"


# admiss-reads: an admissibility positive control. The precondition is
# Acc(list_pred(pass_changed),1/2) (P1) + 0<=max_passes<=len(pass_changed) (P2). This
# control keeps the gold impl VERBATIM but FIRST asserts, under that half-permission,
# that the reads a normal F2P-shaped input needs are admitted: the length is readable,
# the int bound holds, and — when the list is non-empty — the first per-pass outcome is
# readable. No write, so no extra permission demand. If the precondition could not
# admit a legitimate input (including the zero-pass F2P shape max_passes==0), this would
# fail => PRECOND-TOO-STRONG.
_ADMISS = (
    "    # Admissibility: a normal F2P-shaped input (incl. the zero-pass case\n"
    "    # max_passes==0) is in-domain; the half-permission admits reading the\n"
    "    # length and the per-pass outcomes.\n"
    "    Assert(len(pass_changed) >= 0)\n"
    "    Assert(0 <= max_passes and max_passes <= len(pass_changed))\n"
    "    if len(pass_changed) > 0:\n"
    "        Assert(pass_changed[0] == pass_changed[0])  # read admitted under Acc(...,1/2)\n"
    + _IMPL
)
assert _ADMISS != _IMPL, "admiss did not rewrite"


# ---------------------------------------------------------------------------
# FRAME-MUTATION RIVAL (MANDATORY — `pass_changed` is Acc(list_pred(pass_changed),1/2)).
# Must be REJECTED for INSUFFICIENT PERMISSION.
# ---------------------------------------------------------------------------

# frame-mut-write: keeps the gold body VERBATIM (so the rejection is attributable
# SOLELY to the added write, not to a value mismatch), then WRITES BACK into the
# read-only input: pass_changed[0] = pass_changed[0]. A no-op store, but a STORE — it
# demands FULL write permission on `pass_changed`, which the caller granted only at 1/2.
# The verifier must reject for insufficient permission. The store is guarded by len>0 so
# it is reachable on a normal non-empty input. A real impl that mutated the per-pass
# outcomes would corrupt the change-tracking the post-loop `if substitutions:` decision
# reads, diverging from the gold (which only READS the aggregate) — it would not be the
# gold patch and would not faithfully resolve.
_FRAME_MUT = (
    "    if len(pass_changed) > 0:\n"
    "        # Frame violation: write back into the read-only (Acc(...,1/2)) input.\n"
    "        pass_changed[0] = pass_changed[0]\n"
    + _IMPL
)
assert _FRAME_MUT != _IMPL, "frame-mut did not rewrite"


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN / CONTROL-FLOW RIVALS — must be REJECTED
# (else SPEC-TOO-WEAK). Each shares the frozen spec exactly; only the impl changes.
# ---------------------------------------------------------------------------

# weak-zero-true: PARTIAL-DOMAIN on the ZERO-PASS sub-domain — the exact F2P
# discriminator. Keeps the gold loop and pre-loop init VERBATIM (so every invariant
# still holds), but changes ONLY the post-loop return to `substitutions or max_passes ==
# 0`. On every max_passes>0 input this equals `substitutions` (the gold value); on the
# zero-pass path the loop never runs, substitutions stays False, and the rival returns
# True. That is precisely the SPURIOUS "bound reached" the gold fix forbids on zero
# passes.
_WEAK_ZERO_TRUE = _IMPL.replace(
    "    return substitutions\n",
    "    # Wrong on the zero-pass sub-domain: returns a spurious True when no pass ran.\n"
    "    return substitutions or max_passes == 0\n",
)
assert _WEAK_ZERO_TRUE != _IMPL, "weak-zero-true did not rewrite"

# weak-early-true: CONTROL-FLOW / PARTIAL-DOMAIN on the change-free sub-domain. Keeps
# everything VERBATIM except the early-stop return: it returns True (not False) when a
# pass reports no change. On any input whose first change-free pass is at index k <
# max_passes the rival returns True, but all_changed(flags, max_passes) is False there
# (lemma_change_free_kills proves it), so the closed form is False. This is a real patch
# that reported "bound reached" even after the loop broke on a settled pass.
_WEAK_EARLY_TRUE = _IMPL.replace(
    "            lemma_change_free_kills(ToSeq(pass_changed), i, max_passes)\n"
    "            return False\n",
    "            lemma_change_free_kills(ToSeq(pass_changed), i, max_passes)\n"
    "            # Wrong: returns True on a change-free pass (the closed form is False).\n"
    "            return True\n",
)
assert _WEAK_EARLY_TRUE != _IMPL, "weak-early-true did not rewrite"

# weak-prepatch: the pre-patch behaviour of the unchanged repo (model_prepatch.py) on
# the ZERO-PASS sub-domain. Upstream the line the gold ADDS is the pre-loop
# `substitutions = False`; without it, `max_post_process_passes == 0` runs no pass and
# the post-loop `if substitutions:` READS AN UNBOUND LOCAL, so the operation does not
# hand back the definite False the contract demands — it exits ABRUPTLY
# (UnboundLocalError). This rival writes that observable EFFECT: an abrupt,
# non-returning exit on exactly the zero-pass path. The MECHANISM (the unbound read
# itself) is deliberately NOT what is shipped, for two measured reasons:
#   (a) Delete the pre-loop assignment and `substitutions` has no binding on entry.
#       mypy cannot type a name that has none, so the first Invariant reading it gives
#       'Cannot determine type of "substitutions"' and nagini aborts in the FRONT END
#       (`Translation failed`) without ever reaching Viper. nagini is outside
#       pbt.WITNESS_REQUIRED, so "did not verify" is the WHOLE rejection argument on
#       this backend: a front-end abort would record a rejection nothing witnessed.
#   (b) Drop the two invariants that read the flag and the literal unbound read DOES
#       translate; Viper then rejects it with 'Local variable may not have been
#       defined'. But that obligation is emitted at EVERY local read independently of
#       the contract: the same shape is still rejected with the postcondition weakened
#       to `Ensures(True)` (measured, 13.5s). A rival that no specification can admit
#       cannot report SPEC-TOO-WEAK, so it is not a uniqueness rival at all.
# The abrupt exit is rejected BECAUSE OF the frozen postcondition region: it declares
# no Exsures, i.e. it demands normal completion with a definite bool on EVERY path (the
# spec view says so in as many words). Add `Exsures(Exception, True)` to that region and
# this same rival VERIFIES (measured, 22.5s) — so the rejection is attributable to the
# spec and the case stays capable of reporting SPEC-TOO-WEAK.
# Two honesty notes. The pre-loop `substitutions = False` is RETAINED here only so mypy
# can type the flag; it is dead on the zero-pass path (the abrupt exit precedes any
# read), so the rival's observable behaviour is the pre-patch's: abrupt exit iff zero
# passes, the gold value otherwise. And the exception carrier is the base `Exception`
# because Nagini's builtin class table has no NameError/UnboundLocalError — what the
# spec must forbid is the abrupt exit, not the class name.
_WEAK_PREPATCH = _IMPL.replace(
    "    # Normal completion: i == max_passes, so the running flag already equals the\n"
    "    # full-range closed form (congruence over the single count argument).\n"
    "    return substitutions\n",
    "    if max_passes == 0:\n"
    "        # PRE-PATCH: with no pre-loop init the post-loop read of the flag is an\n"
    "        # UNBOUND read on exactly this path, so the operation exits ABRUPTLY here\n"
    "        # instead of returning the definite False the contract demands.\n"
    "        raise Exception('unbound local: substitutions (zero passes)')\n"
    "    # Normal completion: i == max_passes, so the running flag already equals the\n"
    "    # full-range closed form (congruence over the single count argument).\n"
    "    return substitutions\n",
)
assert _WEAK_PREPATCH != _IMPL, "weak-prepatch did not rewrite"

# ctl-zero-reachable: NON-VACUITY control for the zero-pass sub-domain that both
# zero-pass rivals above diverge on. Gold body VERBATIM plus `Assert(False)` on the
# zero-pass path, and it MUST be rejected. If it VERIFIED, the zero-pass path would be
# unreachable under P1/P2 — every zero-pass rejection in this battery would then be an
# artefact of an infeasible guard rather than evidence about the spec, and the
# precondition would be excluding the very F2P configuration
# (NoPostProcessReplacedPathStorage, max_post_process_passes=0) the task is about.
_CTL_ZERO_REACHABLE = _IMPL.replace(
    "    # Normal completion: i == max_passes, so the running flag already equals the\n"
    "    # full-range closed form (congruence over the single count argument).\n"
    "    return substitutions\n",
    "    if max_passes == 0:\n"
    "        # Reachability probe: this must FAIL, proving the zero-pass path is live.\n"
    "        Assert(False)\n"
    "    # Normal completion: i == max_passes, so the running flag already equals the\n"
    "    # full-range closed form (congruence over the single count argument).\n"
    "    return substitutions\n",
)
assert _CTL_ZERO_REACHABLE != _IMPL, "ctl-zero-reachable did not rewrite"


SPEC_TESTS = [
    {
        "id": "pos-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_RESHAPE),
        "rationale": (
            "structurally-different but CORRECT impl: the two independent pre-loop "
            "assignments are reordered and the per-pass `substitutions = pass_changed[i] "
            "!= 0` is rewritten as an explicit guarded assignment with the SAME value. "
            "EVERY gold proof obligation is kept verbatim — same loop bound, all four "
            "invariants (incl. substitutions==(i>0 and all_changed(...))), the "
            "Assert(ToSeq(pass_changed)[i]==pass_changed[i]) framing pin, BOTH lemma "
            "calls (lemma_change_free_kills, lemma_unfold), the early-stop, and the "
            "post-loop return. No loop-direction flip / dropped lemma. If it FAILS => "
            "SPEC-TOO-STRONG (a faithful structurally-different correct impl rejected)."
        ),
    },
    {
        "id": "pos-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_DIRECT),
        "rationale": (
            "the HONEST cheapest faithful impl (grounded-oracle positive control, "
            "standing in for the absent wrong-echo). Q2 pins Result() to the @Pure "
            "fully-unfolded fold all_changed, GROUNDED in the args, so returning the "
            "closed form `max_passes > 0 and all_changed(ToSeq(pass_changed), "
            "max_passes)` directly is CORRECT and satisfies Q2 and Q3 (max_passes==0 "
            "makes the first conjunct False). No loop/lemma needed. If it FAILS => "
            "SPEC-TOO-STRONG (the spec rejects the very value it pins). Demonstrates the "
            "oracle is grounded — there is no wrong value an echo could carry."
        ),
    },
    {
        "id": "admiss-reads",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "the precondition (Acc(list_pred(pass_changed),1/2) + 0<=max_passes<="
            "len(pass_changed)) must admit a normal F2P-shaped input, INCLUDING the "
            "zero-pass case max_passes==0: the length is readable, the int bound holds, "
            "and a non-empty list's first per-pass outcome is readable under the half-"
            "permission. The gold impl is otherwise verbatim (only reads/asserts added "
            "inside the impl region, no write). If it FAILS => PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mut-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT),
        "refinement": (
            "the gold loop only READS the per-pass outcomes (the inner generator's "
            "`subst`, aggregated by `substitutions = substitutions or subst`); it NEVER "
            "writes them back. A faithful real patch that mutated the per-pass change "
            "outcomes would corrupt the change-tracking the post-loop `if substitutions:` "
            "decision depends on — it would not be the gold patch and would not "
            "faithfully resolve. The store here is a no-op only by coincidence; the "
            "point is the spec must forbid ANY write to the read-only input."
        ),
        "rationale": (
            "REJECTED by the PERMISSION SYSTEM: `pass_changed` is granted at "
            "Acc(list_pred(pass_changed),1/2) (P1); the store pass_changed[0]="
            "pass_changed[0] demands FULL write permission, which is not available, so "
            "the verifier rejects for INSUFFICIENT PERMISSION. The gold body is kept "
            "verbatim so the rejection is attributable solely to the write. If it "
            "VERIFIES => the read-only frame is hollow (frame-mutation, the #1 weakness "
            "class; a byte-fuzzer never thinks to mutate the input)."
        ),
    },
    {
        "id": "weak-zero-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ZERO_TRUE),
        "refinement": (
            "returning a spurious True on the zero-pass path is EXACTLY the defect class "
            "the gold fix forbids: in the repo it would make `if substitutions:` raise "
            "RuntimeError('Max post-process passes exceeded.') even though zero passes "
            "were configured. It fails the F2P (NoPostProcessReplacedPathStorage, "
            "max_post_process_passes=0), which runs collectstatic and asserts it "
            "completes ('post-processed' in stdout) with NO spurious 'exceeded' error. "
            "Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q3 (Ensures(Implies(max_passes == 0, Result() == False))): on "
            "the zero-pass path the loop never runs, substitutions stays False, and "
            "`substitutions or max_passes == 0` evaluates to True, but Q3 demands a "
            "definite False. PARTIAL-DOMAIN: correct on every max_passes>0 input, wrong "
            "on EXACTLY the zero-pass sub-domain (the F2P discriminator). If it VERIFIES "
            "=> SPEC-TOO-WEAK (the zero-pass boundary, the whole bug, is unpinned)."
        ),
    },
    {
        "id": "weak-early-true",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_EARLY_TRUE),
        "refinement": (
            "returning True on a change-free pass is what a real patch that reported "
            "'bound reached' even after the loop broke on a settled (no-substitution) "
            "pass would do — it emits the spurious RuntimeError whenever post-processing "
            "settles early, breaking the normal multi-pass P2P paths (post_processing "
            "behaves correctly, the manifest/aggregating tests) that settle before the "
            "pass cap. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q2 (Ensures(Result() == (max_passes > 0 and all_changed("
            "ToSeq(pass_changed), max_passes)))): on a change-free pass at index i < "
            "max_passes, lemma_change_free_kills proves all_changed(flags, max_passes) "
            "is False, so the closed form is False, but the rival returns True. "
            "CONTROL-FLOW / PARTIAL-DOMAIN: the early-stop return value is flipped on the "
            "change-free sub-domain. If it VERIFIES => SPEC-TOO-WEAK (the early-stop "
            "value is unpinned)."
        ),
    },
    {
        "id": "weak-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PREPATCH),
        "refinement": (
            "this is the pre-patch behaviour of the unchanged repo (model_prepatch.py) "
            "on the zero-pass sub-domain: without the pre-loop `substitutions = False`, "
            "max_post_process_passes==0 runs no pass and `if substitutions:` reads the "
            "flag UNBOUND, so post_process does not hand back a definite False — it "
            "exits abruptly with UnboundLocalError, the exact crash reported in the "
            "issue. The rival writes that observable exit on exactly the zero-pass "
            "path and is otherwise the gold body verbatim. It fails the F2P (the "
            "zero-pass storage must complete collectstatic). Does NOT resolve — the "
            "precise change the spec senses (G-DIFF)."
        ),
        "rationale": (
            "REJECTED by the frozen postcondition region, which declares NO Exsures and "
            "so demands normal completion with a definite bool on every path: "
            "'Exhale might fail. Assertion \"method raises no exceptions\" might not "
            "hold.' (19.5s). Attribution is exact — every invariant, both lemma calls, "
            "the early stop and the post-loop return are verbatim; the ONLY edit is the "
            "zero-pass exit. Spec-attributable, not language-level: adding "
            "`Exsures(Exception, True)` to that region makes this same rival VERIFY "
            "(22.5s), so the case can still report SPEC-TOO-WEAK. The LITERAL unbound "
            "read is not what is shipped because it is not expressible as a translatable "
            "rival: with no binding on entry mypy gives 'Cannot determine type of "
            "\"substitutions\"' at the first Invariant that reads it and nagini aborts "
            "in the front end (Translation failed) without reaching Viper — and on a "
            "backend outside pbt.WITNESS_REQUIRED, where 'did not verify' is the whole "
            "rejection argument, that would vouch for a rejection nothing witnessed. "
            "Dropping the two invariants that read the flag does make it translate and "
            "Viper then reports 'Local variable may not have been defined', but that "
            "obligation fires at every local read regardless of the contract (it still "
            "fires with the postcondition weakened to Ensures(True), 13.5s), so it "
            "could never report spec weakness. If this rival VERIFIES => SPEC-TOO-WEAK "
            "(the spec would admit an operation that does not complete on the zero-pass "
            "path — the well-definedness the whole task is about). Paired with "
            "ctl-zero-reachable, which proves that path is live."
        ),
    },
    {
        "id": "ctl-zero-reachable",
        "kind": "admissibility",
        "expect": "reject",
        "module": _impl(_CTL_ZERO_REACHABLE),
        "refinement": (
            "not a candidate patch: a reachability probe. `Assert(False)` on the "
            "zero-pass path is the control for every zero-pass rejection in this "
            "battery (weak-prepatch, weak-zero-true)."
        ),
        "rationale": (
            "NON-VACUITY CONTROL: must be REJECTED — 'Assert might fail. Assertion "
            "False might not hold.' (22.7s) — which is what shows the zero-pass path is "
            "REACHABLE under P1/P2 and that the two zero-pass rivals are refuted on a "
            "live path, not behind an infeasible guard. If it VERIFIES => "
            "PRECOND-TOO-STRONG: the precondition would make max_passes==0 infeasible, "
            "excluding the very F2P configuration (NoPostProcessReplacedPathStorage, "
            "max_post_process_passes=0) the task is about, and every zero-pass "
            "rejection recorded here would be vacuous."
        ),
    },
]


# meta.axioms == [] and there is NO A-reference to a library callee (all_changed is a
# DEEP model of the in-function loop, not an abstraction of an external callee — see
# refinement.md / mapping.md §3). There is no @ContractOnly axiom and no callee to
# execute in Docker, hence no axiom-soundness / containment probe to run.
AXIOM_TESTS = []
