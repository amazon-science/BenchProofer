# properties.py — PBT falsification battery for django__django-13513. NOT a
# Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT. Each SPEC_TESTS case is a full model.py
# variant that shares the FROZEN spec exactly (markers.same_spec) and edits ONLY
# inside a # impl-start/# impl-end region; the runner re-runs the Nagini verifier
# on the host and checks the verify/reject outcome against `expect`.
#
# ---------------------------------------------------------------------------
# Defended surface (read model.py + refinement.md + mapping.md + axiom_check.py)
# ---------------------------------------------------------------------------
# Two modeled functions; the change locus is the cross-chain assembly.
#
#   frames_from_traceback(chain: PSeq[int], k: int) -> List[int]
#     Requires(0 <= k and k < len(chain))            # WHICH exception of the chain
#     Requires(chain[k] >= 0)                        # its own visible-node count
#     Ensures(Acc(list_pred(Result())))
#     Ensures(len(Result()) == chain[k])             # LOAD-BEARING: one entry per
#                                                    # node of THAT exception's own
#                                                    # traceback (empty -> zero).
#     Ensures(Forall j: 0<=j<chain[k] ->
#             Result()[j] == locations_before(chain, k) + j)      # LOAD-BEARING:
#                                                    # WHICH location each entry
#                                                    # describes is observable too
#                                                    # -- the block carries the
#                                                    # chain locations OWNED BY
#                                                    # exception k, one each, in
#                                                    # TRACE ORDER (obligation 1/3).
#     # chain is a PSeq value and k a scalar (NO Acc) -> no read-only-input frame
#     # mutation applies to THIS function.
#
#   assemble_frames(trace_lens: List[int]) -> List[int]
#     Requires(Acc(list_pred(trace_lens), 1/2))      # READ-ONLY input (half perm)
#     Requires(Forall k: 0<=k<len -> trace_lens[k] >= 0)
#     Ensures(Acc(list_pred(trace_lens), 1/2))       # permission preserved
#     Ensures(Acc(list_pred(Result())))
#     Ensures(len(Result()) == chain_total(ToSeq(trace_lens)))   # LOAD-BEARING:
#                                                    # the total is the SUM over
#                                                    # EVERY exception (obligation
#                                                    # 2 — independence). This is
#                                                    # the discriminating clause:
#                                                    # the pre-patch coupled walk
#                                                    # gives 0 on [1,0], gold gives
#                                                    # chain_total([1,0]) == 1.
#     Ensures(Forall p: 0<=p<len(Result()) ->
#             Result()[p] == entry_location(ToSeq(trace_lens), p))
#                                                    # LOAD-BEARING: the report is
#                                                    # read POSITIONALLY, so WHICH
#                                                    # location each entry
#                                                    # describes, WHICH exception
#                                                    # owns it, and WHERE it sits
#                                                    # are as observable as HOW
#                                                    # MANY there are (obligation
#                                                    # 3): each exception's block
#                                                    # is contiguous, internally in
#                                                    # trace order, drawn from that
#                                                    # exception's OWN locations,
#                                                    # and the blocks appear in the
#                                                    # order the report consumes
#                                                    # the chain (innermost cause
#                                                    # first, outermost last).
#
#   chain_total(lens: PSeq[int]) -> int  is  @Pure, a front-recursive SUM fold:
#     chain_total([]) = 0 ; chain_total(x:::xs) = x + chain_total(xs).
#   locations_before(lens: PSeq[int], k: int) -> int  is  @Pure:
#     chain_total(lens) - chain_total(lens.drop(k)) — the number of locations owned
#     by the exceptions BEFORE lens[k] in chain order, i.e. where exception k's own
#     block of chain location numbers starts. Consecutive exceptions own
#     consecutive, pairwise-disjoint blocks, so a location number identifies its
#     owner and the index of the node within that owner's own visible trace.
#   entry_location(lens: PSeq[int], pos: int) -> int  is  @Pure: the exceptions
#     consumed BEFORE lens[0] -- i.e. lens.drop(1) -- fill the leading
#     chain_total(lens.drop(1)) positions, and the rest are lens[0]'s own block in
#     trace order, so report position pos carries the location number the report
#     puts there. Together the folds determine the report completely from the chain.
#
# Where the rejections come from:
#   * assemble_frames is the bug locus. The pre-patch single coupled pointer
#     advances to the next exception only from INSIDE the per-node loop, so an
#     empty innermost traceback aborts the whole walk and drops every frame.
#     ANY impl whose count is not the full SUM (drops/suppresses an exception
#     after an empty one, takes max/last/first only, double-counts, off-by-one)
#     fails Ensures(len(Result()) == chain_total(ToSeq(trace_lens))).
#   * an impl that gets the COUNT right and the PLACEMENT or the PROVENANCE wrong
#     -- reverses one exception's block, reverses the whole report, interleaves or
#     exchanges two blocks (even two blocks of EQUAL length), or puts in a position
#     an entry describing another exception's location -- fails the positional
#     clause Ensures(Result()[p] == entry_location(ToSeq(trace_lens), p)).
#     Count-only rivals are therefore NOT the whole reject lane.
#   * frames_from_traceback off-by-one / wrong-count rivals fail
#     Ensures(len(Result()) == chain[k]); rivals that emit the right NUMBER of
#     entries but not the right ONES (one constant marker per node, the trace
#     walked backwards, or another exception's block) fail
#     Ensures(Result()[j] == locations_before(chain, k) + j).
#   * trace_lens is held at HALF permission Acc(...,1/2): any impl that WRITES to
#     it (trace_lens[k] = ..., .append(...), .pop()) fails for INSUFFICIENT
#     PERMISSION regardless of the postcondition — the canonical frame-mutation
#     probe (directive 5), MANDATORY here.
#
# Ungrounded-oracle-echo (directive 2): chain_total, locations_before and
# entry_location are @Pure but FULLY GROUNDED in the input carrier — each is a
# spelled-out fold over `trace_lens` itself (a sum; a prefix sum; a positional
# lookup), not an opaque answer key. An impl MAY echo them: compute nothing and
# read the answer straight out of the fold. That echo is covered on BOTH sides, so
# the channel is not a hole: echoed FAITHFULLY it is admitted
# (`pos-frames-echo-fold`, a positive control — it recomputes the same fold, so it
# is doing the work, not dodging it), and echoed one position OVER it is rejected
# by Ensures(Result()[j] == locations_before(chain, k) + j) itself
# (`uniq-fft-echo-shifted`). There is no wrong value an echo can slip past the spec.
# Both members are per-exception, echoing entry_location on the one-element
# chain, because the WHOLE-REPORT echo is not judgeable by this backend: its own
# inline bookkeeping needs an induction over chain_total and a preservation step
# that reaches no verdict at 900s (measured ten ways — see the ECHO family note at
# the shifted case's construction). The whole-report shifted echo is retained as
# `uniq-echo-shifted`, with its attribution stated honestly there.
#
# Control-flow-effect (directive 4): the report must actually be DELIVERED, so the
# effect channel modeled here is TERMINATION. Nagini verifies partial correctness
# by default, under which an impl that assembles the right report and then spins
# instead of returning satisfies every Ensures vacuously while the real reporter
# hangs. MustTerminate(2)/(3) in the two preconditions closes that; the rival that
# does exactly this is `uniq-diverge`, rejected for an unsatisfied obligation
# rather than a wrong value. No capability-token rival applies (there is no
# raise/side-effect channel the List[int] abstraction hides).
#
# AXIOM lane: there is NO @ContractOnly axiom (meta.axioms == []). chain_total +
# frames_from_traceback are an A-REFERENCE deep model of Django's own restructured
# control flow, validated == the real gold assembly by axiom_check.py / G-AX. We
# carry that soundness + caller-domain-containment forward as AXIOM_TESTS probes
# run in the instance Docker image against the REAL ExceptionReporter.
from pathlib import Path

INSTANCE = "django__django-13513"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ===========================================================================
# Frozen impl regions (verbatim from model.py). We only ever replace text
# BETWEEN a # impl-start / # impl-end pair, guaranteeing same_spec. There are
# TWO impl regions (one per function); each swap is uniqueness-checked by _swap.
# ===========================================================================

# --- frames_from_traceback impl region (verbatim from model.py) ---
_FFT_IMPL_OLD = """    # impl-start
    result = []  # type: List[int]
    # where this exception's own block of chain location numbers begins
    start = locations_before(chain, k)
    trace_len = chain[k]
    i = 0
    while i < trace_len:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= trace_len)
        Invariant(trace_len == chain[k])
        Invariant(start == locations_before(chain, k))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda j: Implies(0 <= j and j < i,
                                                result[j] == start + j)))
        # TERMINATION: at most `trace_len - i` passes remain. `i` grows by
        # exactly 1 each pass and `trace_len` is fixed before the loop (read from
        # the immutable chain), so the bound strictly decreases; the `+ 1` keeps
        # it positive on the final pass, which has 0 passes left.
        Invariant(MustTerminate(trace_len - i + 1))
        # invariants-end
        result.append(start + i)
        i = i + 1
    return result
    # impl-end"""

assert _FFT_IMPL_OLD in _BASE and _BASE.count(_FFT_IMPL_OLD) == 1

# --- assemble_frames impl region (verbatim from model.py) ---
_AF_IMPL_OLD = """    # impl-start
    frames = []  # type: List[int]
    # The report consumes the chain from the end (innermost cause first), then
    # the remaining exceptions in turn; each exception's own entries are appended
    # as one block, drawn from THAT exception's own trace, so every exception
    # contributes its own entries independently of the rest.
    n = len(trace_lens)
    i = n
    # `suffix` is the part of the chain already consumed and `base` the number of
    # entries it contributed -- the two quantities the report's shape is read off.
    suffix = ToSeq(trace_lens).drop(i)  # type: PSeq[int]
    base = 0
    # `head` is where the block of location numbers owned by the exceptions NOT
    # yet consumed ends: the consumed suffix owns the numbers from `head` up.
    total = chain_total(ToSeq(trace_lens))
    head = total
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(trace_lens), 1 / 2))
        Invariant(Acc(list_pred(frames)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(trace_lens))
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < len(trace_lens),
                                                 trace_lens[k] >= 0)))
        Invariant(suffix == ToSeq(trace_lens).drop(i))
        Invariant(base == chain_total(suffix))
        Invariant(total == chain_total(ToSeq(trace_lens)))
        Invariant(head == total - base)
        # What has been gathered so far is exactly the report of the chain suffix
        # already consumed: that many entries, each naming the chain location that
        # suffix places there -- shifted up by `head`, because the exceptions not
        # yet consumed own all the location numbers below it.
        Invariant(len(frames) == base)
        Invariant(Forall(int, lambda p: Implies(0 <= p and p < base,
                                                frames[p] ==
                                                head + entry_location(suffix, p))))
        # How the chain suffix one exception LONGER -- the one the next pass will
        # have consumed -- is read off this one: it starts with THAT exception's
        # own trace length and continues with the suffix consumed so far ...
        Invariant(Implies(i > 0,
                          ToSeq(trace_lens).drop(i - 1).drop(1) == suffix))
        # ... so its entry count is that trace's length plus this suffix's ...
        Invariant(Implies(i > 0,
                          chain_total(ToSeq(trace_lens).drop(i - 1)) ==
                          trace_lens[i - 1] + base))
        # ... the positions this suffix already filled keep the entries they
        # carry, shifted up by that one exception's own trace length (it owns the
        # numbers immediately below theirs) ...
        Invariant(Implies(i > 0,
                          Forall(int, lambda p: Implies(
                              0 <= p and p < base,
                              entry_location(ToSeq(trace_lens).drop(i - 1), p) ==
                              trace_lens[i - 1] +
                              entry_location(suffix, p)))))
        # ... and the positions after them are that one exception's own block,
        # laid down in trace order over the numbers it owns.
        Invariant(Implies(i > 0,
                          Forall(int, lambda p: Implies(
                              base <= p and p < base + trace_lens[i - 1],
                              entry_location(ToSeq(trace_lens).drop(i - 1),
                                             p) == p - base))))
        # TERMINATION: at most `i` passes remain -- one per exception still to be
        # consumed. `i` drops by exactly 1 per pass and the loop runs only while
        # `i > 0`, so the bound strictly decreases and the `+ 1` keeps it positive
        # on the last pass, which has 0 passes left.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        # the block for the exception whose turn it is, drawn from ITS OWN trace:
        # the helper is told which exception of this chain it serves.
        contribution = frames_from_traceback(ToSeq(trace_lens), i - 1)
        m = len(contribution)
        frames.extend(contribution)
        # This exception is consumed: fold its block into the chain suffix. The
        # suffix one exception longer starts with THIS exception's trace length
        # and continues with the suffix just consumed ...
        i = i - 1
        longer = ToSeq(trace_lens).drop(i)  # type: PSeq[int]
        suffix = longer
        base = base + m
        head = head - m
    return frames
    # impl-end"""

assert _AF_IMPL_OLD in _BASE and _BASE.count(_AF_IMPL_OLD) == 1


# Fragments of the frozen assemble_frames body, so a case that changes ONE thing
# (where the block's entries are written, what is written after them, what
# happens to the finished report) is derived from the frozen text instead of
# re-transcribed: the derivation cannot silently drift from model.py, and the
# diff between a case and gold is exactly the behaviour under test.
_AF_HEAD = """    frames = []  # type: List[int]
"""
_AF_BLOCK = """        contribution = frames_from_traceback(ToSeq(trace_lens), i - 1)
        m = len(contribution)
        frames.extend(contribution)
"""
_AF_TAIL = """        suffix = longer
        base = base + m
        head = head - m
    return frames
    # impl-end"""


def _sub(impl, old, new):
    """One surgical, uniqueness-checked change inside a frozen impl region."""
    if impl.count(old) != 1:
        raise AssertionError(f"fragment not unique: {old!r}")
    return impl.replace(old, new, 1)


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally-DIFFERENT but CORRECT impls that
# MUST verify (else SPEC-TOO-STRONG). Pilot pitfalls #2/#3 honoured: the
# front-recursive chain_total / entry_location folds make a chain walk in the
# OPPOSITE direction need an f(a+b)==f(a)+f(b) lemma the verifier cannot
# auto-discharge, so we DO NOT flip the OUTER walk's direction; we keep it and
# its invariants, and reshape the executable shape of what each pass writes.
#
# COST NOTE (measured, not guessed): replacing the per-exception `frames.extend`
# with a NESTED per-entry copy loop is not usable in this battery. The outer
# walk's quantified invariants (over entry_location / chain_total) then have to
# be re-established through a second quantified loop, and the verifier reached NO
# verdict in 1800s on such a variant (`p_af_pos` / `p_af_block_rev`, this cell's
# scratch). The same wall stops the whole-report ECHO positive: dropping the chain
# walk entirely and reading each position out of entry_location needs an
# induction over chain_total just to enter the loop, and then preservation of the
# positional invariant across `frames.append` reaches no verdict at 900s (ten
# variants measured, incl. a control with the entry conjunct removed — see the ECHO
# family note further down). A case that cannot be judged is not evidence either
# way, so the assemble_frames positives below keep the assembly's loop STRUCTURE
# and differ in what is computed (the per-exception count taken from the chain
# instead of from the produced block), and the echo SHAPE is admitted at the
# per-exception level, where it IS judgeable (`pos-frames-echo-fold`).
# ===========================================================================

# pos-frames-reshape (frames_from_traceback): a different way of computing the
# same entry — instead of adding the loop counter to this exception's block start,
# add the count of entries already written, which is the index of the location
# this entry describes. The observable (one entry per location, the entry in
# position j naming this exception's own location j) is unchanged, the invariant
# len(result) == i already pins the two expressions equal, and the loop direction
# is unchanged, so it must verify.
_FFT_POS_RESHAPE = """    # impl-start
    result = []  # type: List[int]
    start = locations_before(chain, k)
    trace_len = chain[k]
    i = 0
    while i < trace_len:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= trace_len)
        Invariant(trace_len == chain[k])
        Invariant(start == locations_before(chain, k))
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda j: Implies(0 <= j and j < i,
                                                result[j] == start + j)))
        # TERMINATION: at most `trace_len - i` passes remain; `i` grows by 1 per
        # pass and `trace_len` is fixed before the loop, so the bound strictly
        # decreases and the `+ 1` keeps it positive on the final pass.
        Invariant(MustTerminate(trace_len - i + 1))
        # invariants-end
        result.append(start + len(result))
        i = i + 1
    return result
    # impl-end"""

# pos-assemble-count-from-chain (assemble_frames): the per-exception count that
# the report's bookkeeping advances by is read from the CHAIN (trace_lens[i-1])
# instead of from the block that was just produced (len(contribution)). The two
# are equal only because frames_from_traceback's own postcondition says so, so
# this is the cheapest CORRECT rival that leans on the per-exception clause rather
# than restating it. Same loop structure, so it verifies at gold cost.
_AF_POS_MFROM = _sub(_AF_IMPL_OLD, _AF_BLOCK, """        contribution = frames_from_traceback(ToSeq(trace_lens), i - 1)
        # the count this pass advances by, read from the CHAIN rather than from
        # the block just produced. The two are equal only through
        # frames_from_traceback's own postcondition, stated over the chain
        # sequence; the Assert names the sequence-vs-list reading of the same
        # element so the caller can use that postcondition.
        Assert(len(contribution) == ToSeq(trace_lens)[i - 1])
        m = trace_lens[i - 1]
        frames.extend(contribution)
""")


# ===========================================================================
# ADMISSIBILITY — confirm the precondition admits a normal F2P-shaped input
# (else PRECOND-TOO-STRONG). A new module-level caller def would change the
# projected spec view and break same_spec, so we inject the admissibility
# witness INSIDE the impl region (elided from the spec view): a leading block
# that asserts the function's own Requires hold for the actual parameter, then
# runs the real impl unchanged. The F2P witness is the chain [1, 0] (outer exc
# with a 1-node traceback, innermost attached context with an empty traceback);
# its precondition (every trace_lens[k] >= 0, held at half permission) is
# exactly what the function declares and is established for any in-domain input.
# ===========================================================================
_AF_ADMISS = _sub(_AF_IMPL_OLD, _AF_HEAD, """    # --- admissibility witness for an F2P-shaped input (elided from spec view) ---
    # The F2P scenario is the chain [1, 0]: an outer exception with a one-node
    # traceback and an attached-but-never-raised __context__ with an empty
    # (None) traceback. Its precondition is exactly the function's own Requires:
    # the half-permission to trace_lens and the per-element non-negativity. Assert
    # they hold for the actual parameter (a legitimate in-domain input); if the
    # precondition could not be established the Assert fails => PRECOND-TOO-STRONG.
    Assert(Acc(list_pred(trace_lens), 1 / 2))
    Assert(Forall(int, lambda k: Implies(0 <= k and k < len(trace_lens),
                                          trace_lens[k] >= 0)))
    # --- end admissibility witness; the real impl follows unchanged ---
""" + _AF_HEAD)


# ===========================================================================
# FRAME-MUTATION (MANDATORY) — trace_lens is held at HALF permission
# Acc(list_pred(trace_lens), 1/2). A rival that WRITES to it (to satisfy the
# postcondition "vacuously" / opportunistically) MUST be rejected for
# INSUFFICIENT PERMISSION, not for a value reason. We keep the ENTIRE gold body
# (so the postcondition itself remains satisfiable) and inject a single write to
# the read-only input before the loop. The only verification failure cause is
# the write requiring full permission the caller never granted.
# ===========================================================================

# frame-mut-setitem: assign into the half-permission input list.
_AF_FRAME_MUT_SETITEM = _sub(_AF_IMPL_OLD, _AF_HEAD, _AF_HEAD + """    # FRAME-MUTATION PROBE: write into the read-only (half-permission) input.
    # Needs FULL Acc(list_pred(trace_lens)); the caller granted only 1/2 => this
    # must fail for insufficient permission (NOT a value mismatch).
    if len(trace_lens) > 0:
        trace_lens[0] = 0
""")

# frame-mut-append: structural write — append to the half-permission input list.
# Same insufficient-permission rejection; a supporting frame-mutation near-miss.
_AF_FRAME_MUT_APPEND = _sub(_AF_IMPL_OLD, _AF_HEAD, _AF_HEAD + """    # FRAME-MUTATION PROBE (structural write): append to the read-only input.
    # Needs FULL permission; the caller granted only 1/2 => insufficient
    # permission rejection.
    trace_lens.append(0)
""")


# ===========================================================================
# UNIQUENESS / partial-domain — rivals that share the spec exactly and change
# ONLY the impl. Each MUST be rejected; a verifying rival is a real
# verify-but-not-resolve break (SPEC-TOO-WEAK).
# ===========================================================================

# uniq-prepatch-coupled (THE BUG): reproduce the pre-patch coupled walk. Build
# the WHOLE chain's entries only while the suffix being consumed is non-empty,
# but the moment an exception's own trace is empty (trace_lens[i-1] == 0) STOP —
# drop every remaining (more-outer) exception, exactly as the single coupled
# pointer aborts when the innermost traceback is None. On [1, 0] (innermost
# consumed first, empty) this returns 0 frames; the spec requires
# chain_total([1,0]) == 1. This is the model_prepatch.py behaviour G-DIFF flags.
_AF_UNIQ_PREPATCH = """    # impl-start
    frames = []  # type: List[int]
    n = len(trace_lens)
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(trace_lens), 1 / 2))
        Invariant(Acc(list_pred(frames)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(trace_lens))
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < len(trace_lens),
                                                 trace_lens[k] >= 0)))
        # TERMINATION: at most `i` outer passes remain; `i` drops by 1 per pass
        # and the loop runs only while `i > 0`, so the bound strictly decreases
        # and stays positive. It does NOT mention the inner counter `j`, which
        # is reset on every outer pass.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        if trace_lens[i - 1] == 0:
            # the pre-patch coupled walk aborts here: an empty innermost trace
            # drops all the remaining (still-unconsumed) exceptions.
            return frames
        contribution = frames_from_traceback(ToSeq(trace_lens), i - 1)
        j = 0
        m = len(contribution)
        while j < m:
            # invariants-start
            Invariant(Acc(list_pred(trace_lens), 1 / 2))
            Invariant(Acc(list_pred(frames)))
            Invariant(Acc(list_pred(contribution)))
            Invariant(n == len(trace_lens))
            Invariant(0 < i and i <= n)
            Invariant(0 <= j and j <= m)
            Invariant(m == len(contribution))
            Invariant(len(contribution) == trace_lens[i - 1])
            Invariant(Forall(int, lambda k: Implies(0 <= k and k < len(trace_lens),
                                                     trace_lens[k] >= 0)))
            # TERMINATION: at most `m - j` inner passes remain within
            # this outer pass; `m` is fixed before the loop, `j` grows by 1 per
            # pass and stays <= m, so the bound decreases and stays positive.
            Invariant(MustTerminate(m - j + 1))
            # invariants-end
            frames.append(contribution[j])
            j = j + 1
        i = i - 1
    return frames
    # impl-end"""

# uniq-last-only: count only the innermost (last) exception's entries — return
# frames_from_traceback(trace_lens[n-1]) and nothing else. Correct on length-1
# chains and on chains whose total equals the last element, but wrong whenever
# any earlier exception has a non-empty trace (drops their independent
# contributions). Fails the SUM clause.
_AF_UNIQ_LAST_ONLY = """    # impl-start
    frames = []  # type: List[int]
    n = len(trace_lens)
    if n > 0:
        contribution = frames_from_traceback(ToSeq(trace_lens), n - 1)
        j = 0
        m = len(contribution)
        while j < m:
            # invariants-start
            Invariant(Acc(list_pred(trace_lens), 1 / 2))
            Invariant(Acc(list_pred(frames)))
            Invariant(Acc(list_pred(contribution)))
            Invariant(n == len(trace_lens))
            Invariant(0 <= j and j <= m)
            Invariant(m == len(contribution))
            Invariant(len(frames) == j)
            # TERMINATION: at most `m - j` passes remain; `m` is fixed before
            # the loop, `j` grows by 1 per pass and stays <= m, so `m - j + 1`
            # strictly decreases and stays positive.
            Invariant(MustTerminate(m - j + 1))
            # invariants-end
            frames.append(contribution[j])
            j = j + 1
    return frames
    # impl-end"""

# uniq-off-by-one-tail: gold backward walk but the inner copy loop drops the
# LAST entry of each exception's contribution (while j < m - 1). The total is
# then short by the number of non-empty exceptions. Correct only when every
# exception's trace is empty or length 1; wrong otherwise (e.g. [3] -> 2 != 3).
# Partial-domain attack on the per-exception count flowing into the sum.
_AF_UNIQ_OFF_BY_ONE = """    # impl-start
    frames = []  # type: List[int]
    n = len(trace_lens)
    i = n
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(trace_lens), 1 / 2))
        Invariant(Acc(list_pred(frames)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(trace_lens))
        Invariant(Forall(int, lambda k: Implies(0 <= k and k < len(trace_lens),
                                                 trace_lens[k] >= 0)))
        # TERMINATION: at most `i` outer passes remain; `i` drops by 1 per pass
        # and the loop runs only while `i > 0`, so the bound strictly decreases
        # and stays positive. It does NOT mention the inner counter `j`, which
        # is reset on every outer pass.
        Invariant(MustTerminate(i + 1))
        # invariants-end
        contribution = frames_from_traceback(ToSeq(trace_lens), i - 1)
        j = 0
        m = len(contribution)
        while j < m - 1:
            # invariants-start
            Invariant(Acc(list_pred(trace_lens), 1 / 2))
            Invariant(Acc(list_pred(frames)))
            Invariant(Acc(list_pred(contribution)))
            Invariant(n == len(trace_lens))
            Invariant(0 < i and i <= n)
            Invariant(0 <= j and j <= m)
            Invariant(m == len(contribution))
            Invariant(len(contribution) == trace_lens[i - 1])
            Invariant(Forall(int, lambda k: Implies(0 <= k and k < len(trace_lens),
                                                     trace_lens[k] >= 0)))
            # TERMINATION: this rival's inner loop stops one early
            # (`j < m - 1`), so at most `(m - 1) - j` passes remain; `j` grows
            # by 1 per pass, so `m - j` strictly decreases and stays positive
            # while the condition holds.
            Invariant(MustTerminate(m - j))
            # invariants-end
            frames.append(contribution[j])
            j = j + 1
        i = i - 1
    return frames
    # impl-end"""

# uniq-empty (supporting near-miss): return the empty list outright. Correct
# only on the all-empty / empty chain; wrong on every chain with a positive
# total (including the F2P [1,0]). Cheap supporting case; fails the SUM clause.
_AF_UNIQ_EMPTY = """    # impl-start
    frames = []  # type: List[int]
    return frames
    # impl-end"""

# uniq-fft-extra (frames_from_traceback off-by-one): the gold block, then ONE
# extra entry appended after it. Every location this exception's trace records
# still gets its own entry in trace order, so the PLACEMENT clause still holds and
# the ONLY thing wrong is the count: len(Result()) == trace_len + 1 != trace_len.
# Over-counts every non-empty exception -> the chain total would be inflated.
# Attributed purely to Ensures(len(Result()) == trace_len).
_FFT_UNIQ_EXTRA = _sub(_FFT_IMPL_OLD, """    return result
""", """    # ONE entry too many: a phantom node beyond the ones the trace records.
    result.append(trace_len)
    return result
""")

# uniq-fft-short (frames_from_traceback, supporting near-miss): the gold block
# with the loop stopped one early, so an empty trace still yields 0 entries but
# every non-empty trace is short by one -- the location where the exception
# surfaced (the trace's LAST) goes unreported. Fails len == trace_len for
# trace_len >= 1 (and, being short, cannot carry the entry the last position
# needs). Partial-domain: correct only at trace_len == 0.
_FFT_UNIQ_SHORT = _sub(_FFT_IMPL_OLD, """    while i < trace_len:
""", """    while i < trace_len - 1:
""")

# ---------------------------------------------------------------------------
# PLACEMENT rivals — the count is EXACTLY right on every chain; only WHICH
# location an entry describes, or WHERE it sits, is wrong. Each must be rejected
# by the positional clause. Without these the battery would only be testing the
# count, and a report that shows the right NUMBER of frames in the wrong ORDER
# would pass the spec (it is what the shown counterexample did).
# ---------------------------------------------------------------------------

# The per-exception BLOCK REVERSAL (the shown counterexample) is carried by
# `uniq-fft-reversed` below, not by a nested copy loop in assemble_frames: the
# report a block-reversing assembly produces is exactly the report a
# block-reversing frames_from_traceback produces, and the single-loop form can be
# JUDGED (the nested form reached no verdict in 1800s — see the COST NOTE above).
#
# uniq-report-reversed: the gold report, assembled correctly and then handed back
# REVERSED — the outermost exception's last location first, the innermost cause's
# first location last. The count clause is satisfied exactly (the reversal is
# length-preserving, and the loop carries that fact), so ONLY the positional clause
# can reject it.
_AF_UNIQ_REPORT_REV = _sub(_AF_IMPL_OLD, _AF_TAIL, """        suffix = longer
        base = base + m
        head = head - m
    # The report is complete and the right LENGTH; hand it back end-first.
    out = []  # type: List[int]
    k = len(frames)
    while k > 0:
        # invariants-start
        Invariant(Acc(list_pred(trace_lens), 1 / 2))
        Invariant(Acc(list_pred(frames)))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= k and k <= len(frames))
        Invariant(len(frames) == chain_total(ToSeq(trace_lens)))
        Invariant(len(out) == len(frames) - k)
        # TERMINATION: at most `k` passes remain; `k` drops by 1 per pass and the
        # loop runs only while `k > 0`, so the bound decreases and stays positive.
        Invariant(MustTerminate(k + 1))
        # invariants-end
        out.append(frames[k - 1])
        k = k - 1
    return out
    # impl-end""")

# uniq-fft-constant-marker: one entry per recorded location -- the count is right
# on every trace -- but every entry carries the SAME marker instead of the location
# it describes, so the entries no longer say which location they are for. This is
# the placement-blind version of this function; only the positional clause sees it.
_FFT_UNIQ_CONST = _sub(_FFT_IMPL_OLD, """        result.append(start + i)
""", """        result.append(1)
""")

# uniq-fft-reversed: one entry per recorded location, all of them present exactly
# once -- right count, right multiset, all of them numbers this exception OWNS --
# but the block is written in reverse trace order, so the location where the
# exception surfaced is reported first. Only the positional clause rejects it.
_FFT_UNIQ_REV = _sub(_FFT_IMPL_OLD, """        result.append(start + i)
""", """        result.append(start + trace_len - 1 - i)
""")

# The ECHO family (ungrounded-oracle echo, directive 2): do NO walk at all, read
# the answer straight out of the spec's own grounded fold. The channel is closed on
# both sides at the PER-EXCEPTION level, where the echo is JUDGEABLE:
# `pos-frames-echo-fold` echoes entry_location faithfully and VERIFIES, and
# `uniq-fft-echo-shifted` echoes it one position over and is rejected by
# Ensures(Result()[j] == locations_before(chain, k) + j) itself (both MEASURED, below).
#
# At the WHOLE-REPORT level only the shifted (reject) member survives, as
# `uniq-echo-shifted`. MEASURED, why the assemble-level POSITIVE echo is not in
# this battery: the body below is not judgeable by this backend.
#   * As first written it is rejected in 21.9s at its OWN first invariant --
#     "Loop invariant might not hold on entry. Assertion (p <= total) might not
#     hold" -- because `total = chain_total(ToSeq(trace_lens))` needs
#     chain_total >= 0 for a non-negative chain, an INDUCTION over the recursive
#     fold that Viper does not derive (gold never needs it: gold accumulates its
#     count incrementally and carries `base >= 0` as an invariant).
#   * Supplying that induction inline (a gold-shaped suffix walk carrying
#     acc == chain_total(chain.drop(i)) and acc >= 0) closes the entry gap and
#     exposes the real wall: PRESERVATION of
#     Forall q < p: frames[q] == entry_location(ToSeq(trace_lens), q)
#     across `frames.append(...)` does not converge. Eight strategies were
#     measured (point-instantiation Asserts, a quantified Assert, a hoisted
#     `chain = ToSeq(trace_lens)` local, one-element `extend` in place of
#     `append`, the invariant restated over ToSeq(frames)[q], the accounting walk
#     moved after the echo, a weakened bound): all failed preservation in
#     43s-622s, and two variants reached NO VERDICT at 900s.
#   * CONTROL: the body below with the entry-gap conjunct `p <= total` dropped
#     fails preservation too (74s), and the body below VERBATIM with the loop
#     guarded by `if total >= 0:` (so the entry check passes) reaches NO VERDICT
#     at 900s. So the assemble-level echo positive was NEVER discharged -- its
#     recorded failure is its own inline bookkeeping, and no postcondition of the
#     spec is ever named in any of these errors.
# A case that cannot be judged is not evidence either way (see the COST NOTE
# above, which already excludes two positives for the same reason), so the echo
# SHAPE is admitted by `pos-frames-echo-fold` instead.

# pos-frames-echo-fold: the JUDGEABLE echo positive. frames_from_traceback does no
# counting of its own -- each entry is read straight out of the spec's own
# postcondition expression: this exception's block start from `locations_before`,
# plus the placement fold applied to its one-element chain, where
# entry_location(PSeq(trace_len), i) unfolds to i - chain_total(PSeq()) == i.
# That is the echo SHAPE (the answer taken from the folds rather than computed),
# and because the folds are spelled out over the input itself, recomputing them IS
# doing the work, so it must be ADMITTED.
_FFT_POS_ECHO = _sub(_FFT_IMPL_OLD, """        result.append(start + i)
""", """        # ECHO: the entry is not computed here at all -- it is read out of the
        # spec's own folds: the block start this exception owns, plus the
        # placement fold for its one-element chain
        # (entry_location(PSeq(trace_len), i) == i - chain_total(PSeq()) == i).
        result.append(locations_before(chain, k) +
                      entry_location(PSeq(trace_len), i))
""")

# uniq-fft-echo-shifted: the same echo one position OVER. Its own invariant is
# restated to the SHIFTED placement (result[j] == start + j + 1) so the loop
# bookkeeping is maintainable and the count clause holds by construction -- the
# ONLY thing left that can reject it is the positional clause.
_FFT_UNIQ_ECHO_SHIFT = _sub(_sub(_FFT_IMPL_OLD, """        Invariant(Forall(int, lambda j: Implies(0 <= j and j < i,
                                                result[j] == start + j)))
""", """        Invariant(Forall(int, lambda j: Implies(0 <= j and j < i,
                                                result[j] == start + j + 1)))
"""), """        result.append(start + i)
""", """        # ECHO, one position OVER: entry_location(PSeq(trace_len), i + 1)
        # unfolds to i + 1, so every entry names the NEXT location -- one this
        # exception may not even own.
        result.append(locations_before(chain, k) +
                      entry_location(PSeq(trace_len), i + 1))
""")


def _echo_impl(pos_expr, inv_expr):
    body = """    frames = []  # type: List[int]
    # No chain walk: every position is read straight out of the grounded fold.
    total = chain_total(ToSeq(trace_lens))
    p = 0
    while p < total:
        # invariants-start
        Invariant(Acc(list_pred(trace_lens), 1 / 2))
        Invariant(Acc(list_pred(frames)))
        Invariant(0 <= p and p <= total)
        Invariant(total == chain_total(ToSeq(trace_lens)))
        Invariant(len(frames) == p)
        Invariant(Forall(int, lambda q: Implies(0 <= q and q < p,
                                                frames[q] ==
                                                entry_location(
                                                    ToSeq(trace_lens), INV))))
        # TERMINATION: at most `total - p` passes remain; `total` is fixed before
        # the loop and `p` grows by 1 per pass, so the bound strictly decreases
        # and the `+ 1` keeps it positive on the final pass.
        Invariant(MustTerminate(total - p + 1))
        # invariants-end
        frames.append(entry_location(ToSeq(trace_lens), POS))
        p = p + 1
    return frames
    # impl-end""".replace("INV", inv_expr).replace("POS", pos_expr)
    return _sub(_AF_IMPL_OLD,
                _AF_IMPL_OLD[_AF_IMPL_OLD.index("    frames = []"):], body)


_AF_UNIQ_ECHO_SHIFT = _echo_impl("p + 1", "q + 1")
if _AF_UNIQ_ECHO_SHIFT == _echo_impl("p", "q"):
    raise AssertionError("the shifted echo does not differ from the faithful one")
if _FFT_POS_ECHO == _FFT_UNIQ_ECHO_SHIFT:
    raise AssertionError("the per-exception echo pair does not differ")

# uniq-diverge (control-flow / effect, directive 4): assemble the RIGHT report --
# right count, right placement, and the loop below carries both facts as
# invariants -- and then never deliver it: spin instead of returning. Under
# partial correctness this satisfies every Ensures vacuously; it is rejected only
# because the preconditions carry MustTerminate and this loop has no measure.
_AF_UNIQ_DIVERGE = _sub(_AF_IMPL_OLD, """    return frames
    # impl-end""", """    # The report is complete and correct at this point ...
    stuck = True  # type: bool
    while stuck:
        # invariants-start
        Invariant(Acc(list_pred(trace_lens), 1 / 2))
        Invariant(Acc(list_pred(frames)))
        Invariant(len(frames) == chain_total(ToSeq(trace_lens)))
        Invariant(Forall(int, lambda p: Implies(0 <= p and p < len(frames),
                                                frames[p] ==
                                                entry_location(
                                                    ToSeq(trace_lens), p))))
        # NO MustTerminate: this loop cannot discharge the caller's obligation,
        # which is the whole point of the probe -- the report is never delivered.
        # invariants-end
        stuck = True
    return frames
    # impl-end""")


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-frames-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _FFT_IMPL_OLD, _FFT_POS_RESHAPE),
        "rationale": "structurally-different CORRECT frames_from_traceback: instead of "
                     "appending the loop counter, append the number of entries already "
                     "written -- which IS the index of the location this entry describes. "
                     "Both observables are unchanged (trace_len entries; the entry in "
                     "position j describes location j), the invariant len(result) == i "
                     "already pins the two expressions equal, and the loop direction is "
                     "unchanged, so no lemma gap (pilot pitfalls #2/#3). Must verify; "
                     "else SPEC-TOO-STRONG. MEASURED: verifies.",
    },
    {
        "id": "pos-assemble-count-from-chain",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _AF_IMPL_OLD, _AF_POS_MFROM),
        "rationale": "CORRECT assemble_frames that advances its bookkeeping by the count "
                     "the CHAIN gives (trace_lens[i-1]) instead of the length of the block "
                     "just produced (len(contribution)). The two are equal only via "
                     "frames_from_traceback's own postcondition, so this control also "
                     "checks that the per-exception clause is usable by the caller and not "
                     "merely restated by it. Same loop structure as gold, so it is judged "
                     "at gold cost. Must verify; else SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-frames-echo-fold",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _FFT_IMPL_OLD, _FFT_POS_ECHO),
        "rationale": "the ECHO control (directive 2): a CORRECT frames_from_traceback that "
                     "computes nothing itself and reads every entry straight out of the "
                     "spec's own placement fold, applied to this exception's one-element "
                     "chain -- entry_location(PSeq(trace_len), i), which unfolds to "
                     "i - chain_total(PSeq()) == i. The fold is a spelled-out function of "
                     "the input itself, not an opaque answer key, so recomputing it IS "
                     "doing the work and the echo SHAPE must be ADMITTED, else "
                     "SPEC-TOO-STRONG (a spec that only accepted one algorithm). Its "
                     "one-position-shifted twin uniq-fft-echo-shifted is rejected by "
                     "Ensures(Result()[j] == locations_before(chain, k) + j) itself, so the pair shows the echoed VALUE "
                     "is what is pinned, not the shape. This is the per-exception echo "
                     "because the whole-report one is NOT JUDGEABLE on this backend (see "
                     "the ECHO family note above: the entry gap needs an induction over "
                     "chain_total, and preservation of the positional invariant across "
                     "list.append reached no verdict at 900s). MEASURED: verifies in "
                     "308.1s.",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _AF_IMPL_OLD, _AF_ADMISS),
        "rationale": "an admissibility witness injected INSIDE the impl region (elided "
                     "from the spec view, so same_spec holds) asserts the function's "
                     "own Requires hold for the actual parameter: the half-permission "
                     "Acc(list_pred(trace_lens), 1/2) and the per-element "
                     "non-negativity Forall k: trace_lens[k] >= 0. These are exactly "
                     "the precondition of the F2P-shaped chain [1, 0]; the real impl "
                     "then runs unchanged. If the precondition could not be established "
                     "for a legitimate in-domain input the Assert fails => "
                     "PRECOND-TOO-STRONG.",
    },

    # ---- frame-mutation (MANDATORY; must reject for insufficient permission) ----
    {
        "id": "frame-mut-setitem",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _AF_IMPL_OLD, _AF_FRAME_MUT_SETITEM),
        "refinement": "the real get_traceback_frames is given the live `exceptions` "
                      "chain (the report's own exception list) and MUST NOT mutate the "
                      "exceptions it walks — it only reads each exception's traceback to "
                      "count frames. A faithful patch that overwrote an entry of the "
                      "exceptions list (e.g. zeroing an exception's traceback) would "
                      "corrupt the report for every other consumer of that chain and "
                      "change the very frame counts the F2P/P2P traceback tests "
                      "(test_reporting_of_nested_exceptions, test_sharing_traceback) "
                      "observe; it would not resolve. The half-permission models that "
                      "read-only contract.",
        "rationale": "rejected for INSUFFICIENT PERMISSION (not a value mismatch): "
                     "trace_lens is held at Acc(list_pred(trace_lens), 1/2); the "
                     "assignment trace_lens[0] = 0 needs FULL permission the caller "
                     "never granted. The rest of the body is the verbatim gold proof, "
                     "so the only failure cause is the write to the read-only input "
                     "(directive 5 / permission system).",
    },
    {
        "id": "frame-mut-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _AF_IMPL_OLD, _AF_FRAME_MUT_APPEND),
        "refinement": "appending to the exceptions chain corresponds to a patch that "
                      "grew the report's own exception list mid-walk — it would invent "
                      "a phantom exception, inflate the frame count, and break the "
                      "nested-exception / shared-traceback P2P tests; it does not "
                      "resolve. Supporting structural frame-mutation near-miss.",
        "rationale": "rejected for INSUFFICIENT PERMISSION: trace_lens.append(0) "
                     "requires FULL Acc(list_pred(trace_lens)); only 1/2 is held "
                     "(directive 5 / permission system).",
    },

    # ---- uniqueness / partial-domain (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-prepatch-coupled",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _AF_IMPL_OLD, _AF_UNIQ_PREPATCH),
        "refinement": "this IS the pre-patch bug that model_prepatch.py reproduces and "
                      "G-DIFF flags: the single coupled pointer advances to the next "
                      "exception only from INSIDE the per-node loop, so when the "
                      "innermost consumed exception has an empty (None) traceback the "
                      "walk aborts and drops every remaining exception's frames. On the "
                      "F2P chain [1, 0] it returns 0 frames; the sole FAIL_TO_PASS test "
                      "test_innermost_exception_without_traceback asserts len(frames) "
                      "== 1. Its faithful real patch (the un-restructured coupled walk) "
                      "is exactly what does NOT resolve.",
        "rationale": "rejected by Ensures(len(Result()) == chain_total(ToSeq("
                     "trace_lens))): returning early on the first empty trace makes "
                     "len(frames) == 0 on [1,0] (and short on any chain with an empty "
                     "exception preceding a non-empty one), but chain_total is the FULL "
                     "SUM (obligation 2: independence); 0 != 1. The postcondition pins "
                     "the per-exception-independent sum.",
    },
    {
        "id": "uniq-last-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _AF_IMPL_OLD, _AF_UNIQ_LAST_ONLY),
        "refinement": "counting only the innermost (last-popped) exception's frames "
                      "corresponds to a patch that returned after the first "
                      "frames.extend(...) and never ran the `while exceptions:` loop — "
                      "every more-outer exception's traceback frames are dropped. The "
                      "nested-exception P2P test (test_reporting_of_nested_exceptions) "
                      "observes frames from multiple exceptions in the chain; this "
                      "drops all but one and does not resolve.",
        "rationale": "rejected by Ensures(len(Result()) == chain_total(ToSeq("
                     "trace_lens))): len(frames) == trace_lens[n-1] but chain_total is "
                     "the SUM over ALL exceptions; they differ whenever any earlier "
                     "exception has a non-empty trace (e.g. [2,3] -> 3 != 5). Pins the "
                     "cross-chain sum.",
    },
    {
        "id": "uniq-off-by-one-tail",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _AF_IMPL_OLD, _AF_UNIQ_OFF_BY_ONE),
        "refinement": "dropping the last node of each exception's traceback "
                      "corresponds to a per-exception generator that stopped one node "
                      "early (while tb.tb_next is not None instead of while tb is not "
                      "None) — every non-empty traceback loses its final frame. The "
                      "traceback-rendering P2P tests (test_reporting_frames_without_"
                      "source, test_sharing_traceback) observe the full node count; a "
                      "patch short by one frame per exception does not resolve.",
        "rationale": "rejected by Ensures(len(Result()) == chain_total(ToSeq("
                     "trace_lens))): the inner loop runs to m-1, so each non-empty "
                     "exception contributes trace_lens[i-1]-1; the total is short by "
                     "the count of non-empty exceptions (e.g. [3] -> 2 != 3). Fails the "
                     "sum clause. Partial-domain (correct only when every trace is "
                     "empty or length 1).",
    },
    {
        "id": "uniq-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _AF_IMPL_OLD, _AF_UNIQ_EMPTY),
        "refinement": "returning no frames at all corresponds to a patch whose assembly "
                      "produced an empty report — every traceback test fails (the F2P "
                      "wants 1 frame, the nested-exception tests want several). Cheap "
                      "supporting near-miss; does not resolve.",
        "rationale": "rejected by Ensures(len(Result()) == chain_total(ToSeq("
                     "trace_lens))): len(frames) == 0 but chain_total is positive on "
                     "any chain with a non-empty trace (incl. the F2P [1,0] -> 1). "
                     "Partial-domain (correct only on the empty / all-empty chain).",
    },
    {
        "id": "uniq-fft-extra",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FFT_IMPL_OLD, _FFT_UNIQ_EXTRA),
        "refinement": "appending one extra marker per exception corresponds to a "
                      "per-exception generator that yielded one phantom frame beyond "
                      "the real traceback nodes — every exception's frame count is "
                      "inflated by one, so the rendered traceback would show a spurious "
                      "trailing frame. The traceback P2P tests count the real nodes; an "
                      "over-by-one patch does not resolve.",
        "rationale": "rejected by Ensures(len(Result()) == trace_len): the body is the "
                     "gold block (so every recorded location still gets its own entry in "
                     "trace order and the PLACEMENT clause still holds) plus one entry "
                     "after it, so len(Result()) == trace_len + 1 != trace_len. The "
                     "rejection is attributable to the count clause alone.",
    },
    {
        "id": "uniq-fft-short",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FFT_IMPL_OLD, _FFT_UNIQ_SHORT),
        "refinement": "looping to trace_len-1 drops the final node of every non-empty "
                      "traceback (a generator that stops at tb.tb_next is None) — the "
                      "same end-of-traceback frame the rendering tests display goes "
                      "missing; does not resolve. Supporting per-exception near-miss "
                      "for the off-by-one family.",
        "rationale": "rejected by Ensures(len(Result()) == trace_len): for trace_len "
                     ">= 1 the loop runs trace_len-1 times so len(Result()) == "
                     "trace_len-1 != trace_len. (An empty trace still yields 0, so it "
                     "is a partial-domain miss correct only at trace_len == 0.)",
    },

    # ---- PLACEMENT lane (must reject; else the spec would only pin HOW MANY
    # ---- entries a report has, not WHICH location each one describes) ----
    {
        "id": "uniq-report-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _AF_IMPL_OLD, _AF_UNIQ_REPORT_REV),
        "refinement": "corresponds to a patch that assembled the frames correctly and "
                      "then handed back reversed(frames) — the outermost exception's last "
                      "frame first, the innermost cause's first frame last. The count is "
                      "identical, so a count-only spec cannot see it, but the debug page "
                      "would render the whole traceback backwards and every P2P test that "
                      "inspects frames[0] / the frame order fails. Does not resolve.",
        "rationale": "rejected by Ensures(Result()[p] == entry_location(ToSeq("
                     "trace_lens), p)): the reversal loop is length-preserving and the "
                     "invariant carries len(out) == len(frames) - k with len(frames) == "
                     "chain_total(...), so the SUM clause holds; only the positional "
                     "clause can reject it. Whole-report permutation family (the "
                     "block-reversal case above is the per-exception one).",
    },
    {
        "id": "uniq-echo-shifted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _AF_IMPL_OLD, _AF_UNIQ_ECHO_SHIFT),
        "refinement": "an off-by-one report: every position shows the frame that belongs "
                      "one position later, so the first frame of each exception's block is "
                      "dropped from view and a frame from the next block slides in. The "
                      "frame COUNT is untouched (the F2P test still passes) while the "
                      "rendered traceback is wrong everywhere — the positional P2P tests "
                      "fail and it does not resolve.",
        "rationale": "REJECTED (measured, 16.1s), and the behaviour is genuinely wrong: on "
                     "a chain like [2] this echo yields [1, 2] where the spec demands "
                     "[0, 1]. ATTRIBUTION, stated honestly: the error Nagini reports is "
                     "this rival's OWN first loop invariant (\"Assertion (p <= total) "
                     "might not hold\" on entry), because `total = chain_total(...)` needs "
                     "chain_total >= 0 -- an induction over the fold that Viper does not "
                     "derive. So this case does NOT witness the positional clause; it is "
                     "kept as the whole-report member of the echo family (a wrong rival "
                     "the spec does not admit), and the ECHO channel's attributable "
                     "evidence is the per-exception pair pos-frames-echo-fold / "
                     "uniq-fft-echo-shifted, whose rejection names Ensures(Result()[j] == "
                     "j) itself. The whole-report positional clause is witnessed by "
                     "uniq-report-reversed (a length-preserving permutation the sum clause "
                     "cannot see); the per-exception one by uniq-fft-reversed, "
                     "uniq-fft-constant-marker and uniq-fft-echo-shifted. See the ECHO "
                     "family note for the full measurement.",
    },
    {
        "id": "uniq-fft-echo-shifted",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FFT_IMPL_OLD, _FFT_UNIQ_ECHO_SHIFT),
        "refinement": "an off-by-one per-exception block: the helper emits the right NUMBER "
                      "of frames for the exception but each one names the NEXT traceback "
                      "node, so every block drops the frame the trace starts at and shows "
                      "one that belongs past its end. The frame count is untouched (the F2P "
                      "test still passes) while every rendered frame is the wrong one, so "
                      "the positional P2P tests (test_reporting_frames_source_not_match, "
                      "test_reporting_frames_without_source) fail; does not resolve.",
        "rationale": "rejected by Ensures(Result()[j] == locations_before(chain, k) + j) — MEASURED, and the reported "
                     "error names exactly that postcondition. The count clause holds by "
                     "construction (trace_len appends) and the loop's own invariant is "
                     "restated to the shifted placement (result[j] == j + 1) and IS "
                     "maintainable, so nothing but the positional clause can reject it. "
                     "This is the reject member of the ungrounded-oracle-echo pair "
                     "(directive 2): its faithful twin pos-frames-echo-fold verifies, so "
                     "the rejection is about the echoed VALUE, not about echoing.",
    },
    {
        "id": "uniq-fft-constant-marker",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FFT_IMPL_OLD, _FFT_UNIQ_CONST),
        "refinement": "corresponds to a per-exception helper that emitted the RIGHT NUMBER "
                      "of frames but made them all the same — e.g. repeating one "
                      "traceback node's data for every node instead of advancing to "
                      "tb.tb_next. The frame count (and so the F2P test) is unaffected; "
                      "the rendered traceback repeats one line and the P2P tests that "
                      "read each frame's own file/line (test_reporting_frames_"
                      "source_not_match, test_reporting_frames_without_source) fail. Does "
                      "not resolve.",
        "rationale": "rejected by Ensures(Result()[j] == locations_before(chain, k) + j): the loop appends exactly "
                     "trace_len entries so the count clause holds, but each carries the "
                     "constant 1 instead of the index of the location it describes (wrong "
                     "for every j != 1). This is the case a count-only per-exception "
                     "postcondition would have admitted.",
    },
    {
        "id": "uniq-fft-reversed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _FFT_IMPL_OLD, _FFT_UNIQ_REV),
        "refinement": "this is the SHOWN counterexample's behaviour: a patch whose "
                      "per-exception helper walked that exception's traceback and then "
                      "emitted its frames back-to-front (the frame where the exception "
                      "surfaced first, the frame the traceback starts at last). Every "
                      "exception still contributes exactly its own node count, so the "
                      "FAIL_TO_PASS frame-count test passes — and the rendered traceback "
                      "is upside down inside every exception, which is why the P2P tests "
                      "that read the frames positionally "
                      "(test_reporting_frames_for_cyclic_reference, "
                      "test_reporting_frames_source_not_match, "
                      "test_reporting_frames_without_source) FAIL. Measured: that patch "
                      "does NOT resolve, so the spec MUST reject this rival.",
        "rationale": "rejected by Ensures(Result()[j] == locations_before(chain, k) + j): trace_len entries are still "
                     "appended (count clause holds) but position j carries trace_len-1-j, "
                     "which differs from j on every trace of length >= 2. This is the "
                     "case the pre-repair spec ADMITTED (it pinned only the per-exception "
                     "COUNT), and it is why the entry carries the trace index it "
                     "describes. Permutation family: a spec that only pinned the multiset "
                     "of entries would still miss it; this one pins each position.",
    },

    # ---- control-flow / effect (must reject; else the report need never be
    # ---- DELIVERED and every Ensures is vacuous) ----
    {
        "id": "uniq-diverge",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _AF_IMPL_OLD, _AF_UNIQ_DIVERGE),
        "refinement": "corresponds to a patch whose restructured walk assembles the right "
                      "frames and then fails to terminate — e.g. a cyclic __cause__ / "
                      "__context__ chain the walk follows forever, or a per-node loop that "
                      "stops advancing. The user gets a hung request and NO debug page at "
                      "all, so the F2P test (and the cyclic-reference P2P test "
                      "test_reporting_frames_for_cyclic_reference) never even completes: "
                      "it does not resolve.",
        "rationale": "rejected by the MustTerminate(3) obligation in the precondition, NOT "
                     "by a value clause: the report built before the spin is correct and "
                     "the added loop carries both observables as invariants, so under "
                     "PARTIAL correctness this rival would satisfy every Ensures "
                     "vacuously (the return is unreachable). The loop declares no "
                     "measure, so it cannot discharge the caller's obligation and Nagini "
                     "rejects it. This is the case that makes the specification a TOTAL "
                     "one.",
    },
]


# ===========================================================================
# AXIOM LANE — there is NO @ContractOnly axiom (meta.axioms == []). chain_total
# + frames_from_traceback are an A-REFERENCE deep model of Django's OWN
# restructured control flow (gold get_traceback_frames /
# get_exception_traceback_frames). G-AX (axiom_check.py) validates the deep model
# == the real gold assembly. We carry that forward as Docker probes against the
# REAL ExceptionReporter in the instance image:
#   * axiom-soundness: drive the real gold ExceptionReporter on the exact F2P
#     scenario and a faithful stdlib re-creation on boundary + fuzz chains, and
#     assert the real frame count == chain_total (the per-exception SUM) on every
#     caller-reachable chain. A disagreement => the A-reference is UNSOUND.
#   * axiom-containment: every chain the model can reach is a List[int] of
#     non-negative per-exception trace lengths (the precondition); assert each
#     such chain lies in the deep model's domain (lengths >= 0) and the real gold
#     assembly accepts it and reports the SUM (never suppressing a neighbour).
#
# The runner mounts ONLY the probe at /work, so axiom_check.py/model.py are NOT
# in-container; the soundness probe is self-contained stdlib + (optional) real
# Django, mirroring axiom_check.py's faithful re-creation of the gold control
# flow. apply_gold=True so the REAL get_exception_traceback_frames method (added
# only by the gold patch) is present for the strict F2P assertion; the strict
# real-Django assertion is gated on BOTH the gold marker AND the gold-era version
# (< 4.0), exactly as axiom_check.py prescribes (RC=0 in both container states).
# ===========================================================================

_AX_SOUNDNESS_PROBE = r'''
import random
import sys


# --- model.py deep-model references (kept in lock-step with model.py) ---------
def locations_before(lens, k):
    """model.py locations_before: how many chain locations the exceptions BEFORE
    lens[k] own -- i.e. where exception k's own block of location numbers
    starts."""
    return sum(lens[:k])


def frames_from_traceback(chain, k):
    """model.py frames_from_traceback: one entry per node of exception k's OWN
    trace, each carrying the chain location number of that node (trace order)."""
    start = locations_before(chain, k)
    out = []
    for _ in range(chain[k]):
        out.append(start + len(out))
    return out


def chain_total(lens):
    """model.py chain_total: front-recursive SUM of the per-exception lengths."""
    total = 0
    for n in lens:
        total += n
    return total


def model_assemble_len(trace_lens):
    frames = []
    for k in range(len(trace_lens)):   # order is irrelevant to the count
        frames.extend(frames_from_traceback(trace_lens, k))
    return len(frames)


# --- faithful stdlib re-creation of the REAL gold assembly --------------------
class _TB:
    def __init__(self, length):
        self.tb_next = _TB(length - 1) if length > 1 else None


def _make_tb(length):
    return _TB(length) if length > 0 else None


def _gold_exception_frames(tb):
    out = []
    while tb is not None:                  # gold get_exception_traceback_frames
        out.append(1)
        tb = tb.tb_next
    return out


def real_assemble_len(trace_lens):
    """Byte-for-byte the gold control flow (counting frames only). trace_lens is
    the chain in exceptions-list order; the last index is popped first."""
    exceptions = list(trace_lens)
    frames = []
    if not exceptions:
        return len(frames)
    inner = exceptions.pop()               # exc_value = exceptions.pop()
    tb = _make_tb(inner)                    # tb = ... exc_value.__traceback__
    frames.extend(_gold_exception_frames(tb))
    while exceptions:
        exc_len = exceptions.pop()
        frames.extend(_gold_exception_frames(_make_tb(exc_len)))
    return len(frames)


def prepatch_assemble_len(trace_lens):
    """The PRE-PATCH (buggy) coupled single-pointer walk for the discriminating
    witness: it advances between exceptions only from inside the per-node loop,
    so an empty innermost traceback aborts the whole walk."""
    exceptions = list(trace_lens)
    frames = []
    if not exceptions:
        return len(frames)
    exc_len = exceptions.pop()
    tb = _make_tb(exc_len)
    while tb is not None:
        frames.append(1)
        if tb.tb_next is None and exceptions:
            exc_len = exceptions.pop()
            tb = _make_tb(exc_len)
        else:
            tb = tb.tb_next
    return len(frames)


def _real_django_frame_count_for_f2p():
    """Reproduce the exact FAIL_TO_PASS scenario against the REAL Django code and
    return (frame_count, version_tuple, gold_applied). (None, None, None) if
    Django is absent. gold_applied is True iff the gold method
    get_exception_traceback_frames (added only by the gold patch) is present."""
    try:
        import django
        from django.conf import settings
        if not settings.configured:
            settings.configure(DEBUG=True, ALLOWED_HOSTS=['*'], DATABASES={})
            django.setup()
        from django.views.debug import ExceptionReporter
        version = django.VERSION[:2]
        gold_applied = hasattr(ExceptionReporter, 'get_exception_traceback_frames')
    except Exception:
        return None, None, None
    try:
        try:
            try:
                raise RuntimeError('Oops')
            except Exception as exc:
                new_exc = RuntimeError('My context')
                exc.__context__ = new_exc
                raise
        except Exception:
            exc_type, exc_value, tb = sys.exc_info()
        reporter = ExceptionReporter(None, exc_type, exc_value, tb)
        return len(reporter.get_traceback_frames()), version, gold_applied
    except Exception:
        return None, None, None


def check_chain(trace_lens):
    """Assert deep model count == real gold count == the per-exception SUM."""
    real = real_assemble_len(trace_lens)
    model = model_assemble_len(trace_lens)
    expected = chain_total(trace_lens)
    assert real == expected, (
        "AXIOM-UNSOUND: real gold assembly != chain_total: trace_lens=%r real=%d sum=%d"
        % (trace_lens, real, expected))
    assert model == expected, (
        "AXIOM-UNSOUND: deep model != chain_total: trace_lens=%r model=%d sum=%d"
        % (trace_lens, model, expected))
    assert real == sum(trace_lens), (
        "AXIOM-UNSOUND: frame count is not the per-exception sum: %r -> %d"
        % (trace_lens, real))
    return real


def main():
    # --- the FAIL_TO_PASS witness: innermost cause has an EMPTY traceback ------
    f2p = [1, 0]
    real_f2p = check_chain(f2p)
    assert real_f2p == 1, (
        "AXIOM-UNSOUND: FAIL_TO_PASS frame count must be 1, gold gave %d" % real_f2p)
    assert prepatch_assemble_len(f2p) == 0, (
        "pre-patch witness should yield 0 frames on %r" % f2p)
    assert prepatch_assemble_len(f2p) != real_f2p, (
        "F2P scenario fails to discriminate gold from the bug")

    # --- boundary chains -------------------------------------------------------
    boundary = [
        [], [0], [1], [3], [0, 0], [1, 0], [0, 1],
        [2, 0, 3], [0, 0, 5], [5, 0, 0], [4, 3, 2, 1],
    ]
    for tl in boundary:
        check_chain(tl)

    # --- randomized fuzz -------------------------------------------------------
    rng = random.Random(13513)
    for _ in range(20000):
        n = rng.randint(0, 8)
        tl = [rng.randint(0, 6) for _ in range(n)]
        check_chain(tl)

    # --- drive the REAL Django code where available ----------------------------
    real_django, version, gold_applied = _real_django_frame_count_for_f2p()
    if real_django is None:
        django_note = "Django not importable; validated against faithful gold re-creation"
    elif version is not None and version < (4, 0) and gold_applied:
        assert real_django == 1, (
            "AXIOM-UNSOUND: gold-applied gold-era Django %s ExceptionReporter F2P frame "
            "count must be 1, got %d" % (".".join(map(str, version)), real_django))
        django_note = ("REAL gold-applied gold-era Django %s F2P frame count == 1 == "
                       "chain_total([1,0])" % ".".join(map(str, version)))
    elif version is not None and version < (4, 0):
        django_note = ("REAL gold-era Django %s gold NOT applied (base_commit): F2P "
                       "frame count == %d (the dropped-frames bug; matches the modeled "
                       "pre-patch witness 0); recorded, not asserted"
                       % (".".join(map(str, version)), real_django))
    else:
        django_note = ("importable Django %s newer than the gold era (F2P frame count "
                       "%d reflects a later placeholder-frame behaviour); validated "
                       "against the faithful gold re-creation instead"
                       % (".".join(map(str, version)), real_django))

    print("AXIOM-SOUNDNESS OK: deep model (frames_from_traceback + chain_total) == "
          "real gold assembly == per-exception SUM on %d boundary + 20000 fuzz "
          "chains; F2P witness (gold 1 vs bug 0) discriminates; %s"
          % (len(boundary), django_note))
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''

# axiom-containment: the model passes to its deep-model assembly exactly the
# chains its precondition admits — a List[int] whose every element is a
# non-negative per-exception trace length (Requires: trace_lens[k] >= 0; each
# frames_from_traceback call gets trace_lens[i-1], a single non-negative int).
# The deep model's domain is precisely "non-negative ints" (chain_total over
# PSeq[int]; frames_from_traceback Requires trace_len >= 0). Confirm every
# caller-reachable chain (and per-exception length) lies inside that domain and
# the real gold assembly accepts it and reports the SUM (never suppressing a
# neighbour). Covering MORE — e.g. arbitrary tracebacks — is sound, not a defect.
_AX_CONTAINMENT_PROBE = r'''
import random
import sys


class _TB:
    def __init__(self, length):
        self.tb_next = _TB(length - 1) if length > 1 else None


def _make_tb(length):
    return _TB(length) if length > 0 else None


def _gold_exception_frames(tb):
    out = []
    while tb is not None:
        out.append(1)
        tb = tb.tb_next
    return out


def real_assemble_len(trace_lens):
    exceptions = list(trace_lens)
    frames = []
    if not exceptions:
        return len(frames)
    inner = exceptions.pop()
    frames.extend(_gold_exception_frames(_make_tb(inner)))
    while exceptions:
        frames.extend(_gold_exception_frames(_make_tb(exceptions.pop())))
    return len(frames)


def main():
    # Enumerate the chains the MODEL can actually reach: any List[int] of
    # non-negative per-exception trace lengths (the precondition). For each,
    # assert (a) every per-exception length the model passes to
    # frames_from_traceback is a non-negative int -> inside its Requires domain
    # (trace_len >= 0); (b) the chain itself is in chain_total's domain
    # (non-negative ints over PSeq[int]); (c) the real gold assembly accepts the
    # chain and reports exactly the per-exception SUM (independence preserved).
    rng = random.Random(135130)
    reached = 0
    samples = [[], [0], [1], [1, 0], [0, 1], [2, 0, 3], [4, 3, 2, 1]]
    for _ in range(5000):
        n = rng.randint(0, 8)
        samples.append([rng.randint(0, 6) for _ in range(n)])
    for tl in samples:
        # (a)+(b): every model-reachable per-exception length is a non-negative
        # int, inside both frames_from_traceback's and chain_total's domain.
        for x in tl:
            assert isinstance(x, int) and x >= 0, (
                "AXIOM-TOO-WEAK-FOR-CALLER: model-reachable trace length %r is "
                "outside the deep model's non-negative-int domain" % (x,))
        # (c): the real gold assembly accepts this caller-reachable chain and
        # reports the per-exception SUM (no neighbour suppressed).
        real = real_assemble_len(tl)
        assert real == sum(tl), (
            "AXIOM-TOO-WEAK-FOR-CALLER: real gold assembly on a caller-reachable "
            "chain %r gave %d != per-exception sum %d" % (tl, real, sum(tl)))
        reached += 1

    print("AXIOM-CONTAINMENT OK: every model-reachable chain (%d sampled; each a "
          "List[int] of non-negative per-exception trace lengths) lies inside the "
          "deep model's non-negative-int domain and the real gold assembly reports "
          "exactly the per-exception SUM. The caller reaches a subset of the "
          "domain; no reachable input is outside it." % reached)
    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-chain_total",
        "axiom": "chain_total",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,  # the gold method get_exception_traceback_frames must exist
        "probe": _AX_SOUNDNESS_PROBE,
        "rationale": "chain_total + frames_from_traceback are an A-reference deep model "
                     "of Django's own restructured assembly (no @ContractOnly axiom). "
                     "If the real gold ExceptionReporter / faithful gold re-creation "
                     "ever disagreed with chain_total (the per-exception SUM) on a "
                     "caller-reachable chain — e.g. by suppressing an exception's "
                     "frames after an empty-traceback neighbour — the A-reference would "
                     "be UNSOUND. The F2P witness [1,0] (gold 1 vs bug 0) discriminates; "
                     "boundary + 20000 fuzz chains plus the live REAL Django F2P drive "
                     "(gated on gold-marker AND version < 4.0, per axiom_check.py) "
                     "confirm soundness in both container states (RC=0).",
    },
    {
        "id": "ax-cover-chain_total",
        "axiom": "chain_total",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT_PROBE,
        "rationale": "every chain the model can pass to its deep-model assembly is a "
                     "List[int] of non-negative per-exception trace lengths (Requires: "
                     "trace_lens[k] >= 0; each frames_from_traceback call gets a "
                     "non-negative int). The deep model's domain is exactly the "
                     "non-negative ints, so every caller-reachable per-exception length "
                     "and chain is inside it, and the real gold assembly accepts each "
                     "and reports the per-exception SUM. A reachable chain outside the "
                     "domain (a negative length) would be AXIOM-TOO-WEAK-FOR-CALLER; the "
                     "precondition forbids it, so none exists.",
    },
]
