# properties.py — PBT falsification battery for sphinx-doc__sphinx-7757.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions regions untouched, since spec_signature elides
# only the impl region) and swaps ONLY text inside the # impl-start/# impl-end
# region; the runner checks each with Nagini verify + markers.same_spec.
#
# Defended surface (read from model.py + refinement.md + mapping.md + instance):
#   resolve_positional_defaults(positionals: int, posonly: int,
#                               provided: List[int]) -> List[int]
#   aligns a single combined list of supplied defaults (`provided`) right-aligned
#   across ALL `positionals` positional parameters (positional-only prefix of
#   length `posonly` included). With m = len(provided) and pad = positionals - m,
#   the result at index p is EMPTY() (the no-default sentinel, -1) iff p < pad,
#   else render(provided[p-pad]) (a rendered source string, never EMPTY()).
#
#   `provided` is a READ-ONLY input: held at Acc(list_pred(provided), 1/2) in
#   both Requires and Ensures (and as a loop Invariant). => FRAME-MUTATION probe
#   is MANDATORY (a rival that WRITES to `provided` cannot get full permission
#   and must be rejected for INSUFFICIENT PERMISSION).
#
#   Load-bearing postcondition clauses (the spec's teeth):
#     C1  len(Result()) == positionals                       (one slot/parameter)
#     C2  Forall p in [0,positionals):
#             Result()[p] == resolved_default(p, positionals, m, provided)
#                                                            (the alignment pin)
#     C3  Forall p in [0,posonly) with p >= positionals - m:
#             Result()[p] != EMPTY()       (positional-only-prefix NOT exempt —
#                                           the exact bug the gold patch fixes)
#     C4  Acc(list_pred(provided), 1/2)  preserved           (frame / read-only)
#     C5  Forall j: renderable(provided[j])  preserved       (input unchanged)
#     C6  Requires(MustTerminate(2))                         (TOTAL correctness:
#                                           the resolver must ANSWER, so C1-C5
#                                           are claimed of every run and not only
#                                           of the runs that reach a return)
#
#   C6 makes the DIVERGENCE lane mandatory. Without it Nagini proves only partial
#   correctness and the cheapest rival of all -- one that never reaches the return
#   -- satisfies C1-C5 vacuously while computing nothing; refined into the real
#   signature_from_str it recurses or spins and resolves NOTHING. r6/r7 below are
#   the two shapes of that rival (unbounded self-delegation; a loop that writes
#   the obligation token with a constant level instead of a decreasing measure),
#   and r8 closes the other non-returning exit: the frozen contract declares no
#   Exsures, so leaving by RAISING is rejected too ("method raises no
#   exceptions"). A rival that loops must supply its own decreasing measure --
#   a proof burden, not a domain restriction: pos-reorder and admiss-f2p below
#   still verify, and so does an otherwise-gold impl whose loop is reshaped.
#
#   resolved_default is a @Pure helper but it is GROUNDED (fully unfolded from
#   (p, n, m, provided): EMPTY() when p<n-m else render(provided[p-(n-m)])), NOT
#   an opaque answer-key oracle — so there is no WRONG echo to build (echoing it
#   IS the correct answer). See 'assessment'; we use an honest positive control
#   in its place (directive 2).
#
# F2P: tests/test_util_inspect.py::test_signature_from_str_positionaly_only_args
#      ('(a, b=0, /, c=1)' -> a empty, b='0' POSONLY, c='1') — the headline case
#      where the positional-only `b` must KEEP its default (C3).
# Axioms: render (A-consumed, domain-restricted by `renderable`) + renderable
#         (domain predicate). axiom_check.py runs the real callee; the AXIOM_TESTS
#         probes below reuse/strengthen its logic (soundness + caller-containment).

from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7757"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


_IMPL_START = "    # impl-start\n"
_IMPL_END = "    # impl-end\n"


def _swap_impl(body):
    """model.py with the WHOLE impl-region body replaced by `body`.

    The divergence rivals (r6-r8) do not edit the decision block, they replace
    the computation outright, so anchoring them on a sub-expression of the gold
    loop is not possible. The impl region is exactly the region spec_view elides,
    so a whole-body swap is still same_spec by construction; the runner re-checks.
    """
    src = _BASE
    if src.count(_IMPL_START) != 1 or src.count(_IMPL_END) != 1:
        raise AssertionError("drift: impl markers not unique in model.py")
    i = src.index(_IMPL_START) + len(_IMPL_START)
    j = src.index(_IMPL_END)
    if not body.endswith("\n"):
        body += "\n"
    return src[:i] + body + src[j:]


# ---------------------------------------------------------------------------
# The frozen per-iteration DECISION block (model.py lines 172-182): the if/else
# that chooses EMPTY() for the leading `pad` positions and render(provided[...])
# for the trailing block. Every value-rival edits ONLY this block. The loop
# invariant (lines 165-169) PINS ToSeq(result)[q] == resolved_default(q,...) for
# q < p and must be MAINTAINED each iteration, so a wrong value at index p fails
# invariant maintenance even if the helper Assert at line 188 is also kept — i.e.
# the rejection is attributable to the spec (C2), not just to a dropped hint.
# ---------------------------------------------------------------------------
_DECISION = """        if p < pad:
            Assert(resolved_default(p, positionals, m, ToSeq(provided))
                   == EMPTY())
            result = result + [EMPTY()]
        else:
            Assert(provided[p - pad] == ToSeq(provided)[p - pad])
            Assert(renderable(ToSeq(provided)[p - pad]))
            Assert(renderable(provided[p - pad]))
            Assert(resolved_default(p, positionals, m, ToSeq(provided))
                   == render(ToSeq(provided)[p - pad]))
            result = result + [render(provided[p - pad])]"""


# === POSITIVE CONTROL (soundness) =========================================
# Branch-REORDER: test the DEFAULTED (p >= pad) case first and fall through to
# the EMPTY case. Identical executable meaning; every gold framing Assert kept
# verbatim (directive-2 safe). It is a forward loop appending one element at the
# tail just like the gold (NOT a loop-direction flip), so no f(a+b) fold lemma is
# needed (directive-3 safe) — the front-recursive resolved_default is evaluated
# pointwise at index p, not folded over a reversed accumulation. MUST verify;
# else SPEC-TOO-STRONG (a faithful correct impl cannot satisfy the Ensures).
_DECISION_REORDER = """        if p >= pad:
            Assert(provided[p - pad] == ToSeq(provided)[p - pad])
            Assert(renderable(ToSeq(provided)[p - pad]))
            Assert(renderable(provided[p - pad]))
            Assert(resolved_default(p, positionals, m, ToSeq(provided))
                   == render(ToSeq(provided)[p - pad]))
            result = result + [render(provided[p - pad])]
        else:
            Assert(resolved_default(p, positionals, m, ToSeq(provided))
                   == EMPTY())
            result = result + [EMPTY()]"""

POS_REORDER = _swap(_BASE, _DECISION, _DECISION_REORDER)


# === ADMISSIBILITY ========================================================
# A separate top-level caller would break same_spec (spec_view elides only the
# impl region; a module-level addition enters the spec signature). So the
# admissibility probe lives INSIDE the impl region, inserted right after
# `# impl-start`, before any gold obligation (so every following obligation is
# preserved verbatim). It builds a concrete F2P-shaped `provided` and asserts the
# Requires can be established: list_pred holds, the count fits (<= positionals),
# and the renderable domain predicate can hold for each element. If this block
# cannot verify, the precondition rejects a normal input -> PRECOND-TOO-STRONG.
# (We Assume renderable on the concrete codes — the axiom is @ContractOnly with no
# body, so its truth on a literal cannot be derived; assuming it is exactly the
# in-domain shape the F2P signatures present and is the admissibility question.)
_ADMISS_BLOCK = """    # impl-start
    # ADMISSIBILITY PROBE: a representative F2P-shaped supplied-defaults list
    # ('(a, b=0, /, c=1)' -> positionals=3, posonly=2, provided=[code(0), code(1)]
    # i.e. two trailing defaults). The Requires must admit it.
    probe = [7, 8]  # type: List[int]
    Assert(list_pred(probe))
    Assert(len(probe) == 2)
    Assert(len(probe) <= 3)        # m <= positionals for the F2P case
    Assert(ToSeq(probe)[0] == 7)"""

ADMISS = _swap(_BASE, "    # impl-start", _ADMISS_BLOCK)


# === UNIQUENESS / REJECT rivals ===========================================

# --- R1  PRE-PATCH SHAPE (partial-domain): exempt the positional-only prefix.
# For p < posonly emit EMPTY() unconditionally; only ordinary parameters
# (p >= posonly) get the aligned default. This is EXACTLY the pre-patch bug
# (positional-only parameters got no default). Correct on signatures with no
# defaulted positional-only parameter; DIVERGES on the F2P input where a
# positional-only `b` sits inside the trailing default block.
# refinement: the pre-patch repo constructed each positional-only Parameter with
# NO default= (always Parameter.empty); on '(a, b=0, /, c=1)' the real `b` comes
# out default==Parameter.empty, but the F2P test asserts
# sig.parameters['b'].default == '0'. The faithful patch FAILS the F2P -> does
# NOT resolve (it IS the bug). rejection source: C3 (positional-only-not-exempt:
# Result()[p] != EMPTY() for posonly p in the trailing block) AND C2 (alignment).
_R1 = """        if p < pad or p < posonly:
            Assert(resolved_default(p, positionals, m, ToSeq(provided))
                   == EMPTY())
            result = result + [EMPTY()]
        else:
            Assert(provided[p - pad] == ToSeq(provided)[p - pad])
            Assert(renderable(ToSeq(provided)[p - pad]))
            Assert(renderable(provided[p - pad]))
            Assert(resolved_default(p, positionals, m, ToSeq(provided))
                   == render(ToSeq(provided)[p - pad]))
            result = result + [render(provided[p - pad])]"""
R1_POSONLY_EXEMPT = _swap(_BASE, _DECISION, _R1)


# --- R2  OFF-BY-ONE ALIGNMENT (partial-domain): align over the ORDINARY count
# alone, as the pre-patch ordinary-loop did. Use a boundary of `pad + posonly`
# instead of `pad`: a parameter gets a default only once p crosses both the pad
# AND the positional-only prefix, and the offset is shifted accordingly. Wrong
# for any signature whose trailing default block reaches into the positional-only
# prefix (the F2P case), and also misaligns ordinary defaults.
# refinement: the pre-patch ordinary loop indexed args.defaults relative to the
# ordinary-parameter count (`-len(args.args) + i`), ignoring that posonly params
# also consume default slots; on '(a, b=0, /, c=1)' it renders the wrong slot for
# `c` and gives `b` none. The F2P test reads b='0', c='1' position-by-position and
# FAILS -> does NOT resolve. rejection source: C2 (Result()[p] != the aligned
# resolved_default at the shifted positions) AND C3.
_R2 = """        if p < pad + posonly:
            Assert(resolved_default(p, positionals, m, ToSeq(provided))
                   == EMPTY())
            result = result + [EMPTY()]
        else:
            result = result + [render(provided[p - pad - posonly])]"""
R2_OFFBY_POSONLY = _swap(_BASE, _DECISION, _R2)


# --- R3  ALL-EMPTY (partial-domain, degenerate): emit EMPTY() for every
# position, dropping every supplied default. Trivially satisfies C1 (length) and
# C4/C5 (frame, no write) and the C3-vacuous case (when m==0), but pins the wrong
# value wherever a default should appear.
# refinement: a real patch that never attached any default (e.g. forgot the
# defaults loop entirely) would render every positional parameter with
# default==Parameter.empty; the F2P test reads b='0', c='1' and FAILS -> does NOT
# resolve. rationale: the cheapest impl that satisfies the length/frame clauses
# but not the value pin — exactly the soundness-of-C2 control. rejection source:
# C2 (the alignment pin at every defaulted position).
_R3 = """        result = result + [EMPTY()]"""
R3_ALL_EMPTY = _swap(_BASE, _DECISION, _R3)


# --- R4  FRAME-MUTATION (MANDATORY: `provided` is Acc(.,1/2) read-only). Before
# the decision, WRITE to `provided` (overwrite the slot we are about to read).
# `provided` is held at half permission throughout (Requires + Invariant +
# Ensures), so a write needs full permission the impl does NOT hold => Nagini
# rejects this for INSUFFICIENT PERMISSION (a write to provided[...] requires
# Acc(list_pred(provided), 1) / full write access). The gold value invariants are
# kept verbatim so the rejection is attributable to the write, not to a value
# mismatch. This is the #1 weakness class a byte-fuzzer never finds.
# refinement: a faithful patch that mutated args.defaults in place (e.g.
# `args.defaults[i] = <rendered>`) would corrupt the shared AST `definition`
# object that signature_from_str parses once and reuses; subsequent reads (the
# ordinary-args loop reads the SAME padded `defaults`) would see clobbered nodes
# and render the wrong source for `c`. The F2P test reads b='0', c='1' off the
# (now-corrupted) defaults and would FAIL -> does NOT resolve. rejection source:
# the PERMISSION system — Acc(list_pred(provided), 1/2) forbids the write.
_R4 = """        provided[0] = EMPTY()   # FRAME-MUTATION: write a read-only (1/2-perm) input
        if p < pad:
            Assert(resolved_default(p, positionals, m, ToSeq(provided))
                   == EMPTY())
            result = result + [EMPTY()]
        else:
            Assert(provided[p - pad] == ToSeq(provided)[p - pad])
            Assert(renderable(ToSeq(provided)[p - pad]))
            Assert(renderable(provided[p - pad]))
            Assert(resolved_default(p, positionals, m, ToSeq(provided))
                   == render(ToSeq(provided)[p - pad]))
            result = result + [render(provided[p - pad])]"""
R4_FRAME_MUTATION = _swap(_BASE, _DECISION, _R4)


# --- R5  SHORT RESULT (partial-domain on length / first-vs-last): drop the LAST
# position by stopping the loop one short, then return. Correct on every position
# it does emit, but the result has positionals-1 slots.
# refinement: a real patch that ran the ordinary-args loop with an off-by-one
# range (`range(len(args.args) - 1)`) would omit the final positional parameter's
# Parameter entirely; the F2P test's list(sig.parameters.keys()) == ['a','b','c']
# would be missing 'c' and FAIL -> does NOT resolve. rejection source: C1
# (len(Result()) == positionals). We narrow the loop guard so the last position
# is never produced.
_R5 = """    while p < positionals - 1 or (positionals == 0 and p < positionals):"""
R5_SHORT = _swap(_BASE, "    while p < positionals:", _R5)


# --- R6  DIVERGENCE by unconditional SELF-DELEGATION (the C6 lane). The impl
# performs nothing: it hands its own arguments back to itself. Under PARTIAL
# correctness the callee's Ensures discharge the caller's and the whole contract
# holds of a computation that never happens. C6 (`Requires(MustTerminate(2))`)
# is what refuses it: an obligated caller may not call a callee at its own
# level, so Nagini reports an obligation leak.
# refinement: `return signature_from_str(signature)` as the first statement of
# the patched signature_from_str (sphinx/util/inspect.py:516), with the entire
# gold body -- left-pad and both absolute-index loops -- present and correct
# below it. Every call dies with RecursionError, so the F2P
# test_signature_from_str_positionaly_only_args fails and 5 P2P signature tests
# fail with it (the module still imports; the patch applies). This is the exact
# rival recorded as `atk_7.py` in verdict.md, measured by the official resolve
# harness as completed=True, resolved=False, 3/3 consistent attempts.
_R6 = """    # DIVERGENCE: unconditional self-delegation -- nothing is computed.
    return resolve_positional_defaults(positionals, posonly, provided)"""
R6_SELF_DELEGATION = _swap_impl(_R6)


# --- R7  DIVERGENCE by DECORATIVE MEASURE. C6's measure lives in the impl
# region, which spec_view elides, so a rival writes its own -- and this one
# writes the token without the substance: an unbounded loop carrying a CONSTANT
# `Invariant(MustTerminate(1))` instead of a decreasing one, ahead of an
# otherwise-gold computation. If a non-decreasing level satisfied the obligation
# then C6 would be satisfiable by spelling and R6's hole would reopen one line
# lower; Nagini instead reports that the loop might not keep its promise.
# refinement: a `while True: pass` spin inserted ahead of the added block at
# sphinx/util/inspect.py:521. signature_from_str never returns, so the F2P test
# and every P2P signature test hang rather than pass -- it resolves nothing.
_R7 = """    # DIVERGENCE: an unbounded loop that claims termination with a
    # CONSTANT level instead of a decreasing measure.
    result = []  # type: List[int]
    spin = 0
    while spin >= 0:
        # invariants-start
        Invariant(Acc(list_pred(provided), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= spin)
        Invariant(MustTerminate(1))
        # invariants-end
        spin = spin + 1
    m = len(provided)
    pad = positionals - m
    p = 0
    while p < positionals:
        # invariants-start
        Invariant(Acc(list_pred(provided), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(len(provided) == m and positionals - m == pad)
        Invariant(0 <= pad and pad <= positionals)
        Invariant(0 <= p and p <= positionals)
        Invariant(len(result) == p)
        Invariant(Forall(int, lambda j: (
            Implies(0 <= j and j < m, renderable(ToSeq(provided)[j])),
            [[ToSeq(provided)[j]]])))
        Invariant(Forall(int, lambda q: (
            Implies(0 <= q and q < p,
                    ToSeq(result)[q] == resolved_default(
                        q, positionals, m, ToSeq(provided))),
            [[ToSeq(result)[q]]])))
        Invariant(MustTerminate(positionals - p + 1))
        # invariants-end
        old_seq = ToSeq(result)  # type: PSeq[int]
        if p < pad:
            Assert(resolved_default(p, positionals, m, ToSeq(provided))
                   == EMPTY())
            result = result + [EMPTY()]
        else:
            Assert(provided[p - pad] == ToSeq(provided)[p - pad])
            Assert(renderable(ToSeq(provided)[p - pad]))
            Assert(renderable(provided[p - pad]))
            Assert(resolved_default(p, positionals, m, ToSeq(provided))
                   == render(ToSeq(provided)[p - pad]))
            result = result + [render(provided[p - pad])]
        Assert(len(ToSeq(result)) == p + 1)
        Assert(Forall(int, lambda q: (
            Implies(0 <= q and q < p, ToSeq(result)[q] == old_seq[q]),
            [[ToSeq(result)[q]], [old_seq[q]]])))
        p = p + 1
    return result"""
R7_DECORATIVE_MEASURE = _swap_impl(_R7)


# --- R8  NON-RETURNING EXIT by RAISING. C6 obliges the resolver to STOP; the
# other way to stop without answering is to leave by an exception. The gold
# computation, the gold invariants and the gold measure are kept VERBATIM and the
# finished list is simply never handed back. The frozen contract declares no
# Exsures at all, so the postcondition region promises a Result on every
# admitted input and admits no exceptional exit: Nagini rejects with
# `Exhale might fail. Assertion "method raises no exceptions" might not hold.`
# refinement: `raise RuntimeError` appended to the added block at
# sphinx/util/inspect.py:552, after the two absolute-index loops have built the
# right params. signature_from_str raises on every input, so the F2P test and
# every P2P signature test error out -- it resolves nothing.
_R8 = _BASE[_BASE.index(_IMPL_START) + len(_IMPL_START):
            _BASE.index(_IMPL_END)].replace(
    "    return result\n",
    "    # NON-RETURNING EXIT: the right answer is computed and then discarded.\n"
    "    raise Exception()\n")
if "raise Exception()" not in _R8:
    raise AssertionError("drift: gold impl no longer ends in `return result`")
R8_RAISE_EXIT = _swap_impl(_R8)


SPEC_TESTS = [
    {
        "id": "pos-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_REORDER,
        "rationale": "structurally-different CORRECT impl (defaulted branch tested "
        "first, EMPTY branch second) keeping every gold framing Assert verbatim — "
        "must verify, else SPEC-TOO-STRONG. Branch reorder only (directive-2/3 "
        "safe: forward tail-append, pointwise resolved_default, no fold lemma).",
    },
    {
        "id": "admiss-f2p",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "a probe inside the impl builds the F2P-shaped supplied "
        "defaults (positionals=3, posonly=2, provided len 2) and asserts "
        "list_pred + count fit can be established — the Requires must admit a "
        "normal input, else PRECOND-TOO-STRONG.",
    },
    {
        "id": "r1-posonly-exempt",
        "kind": "uniqueness",
        "expect": "reject",
        "module": R1_POSONLY_EXEMPT,
        "refinement": "this is the PRE-PATCH bug: positional-only parameters were "
        "constructed with no default= (always Parameter.empty). On '(a, b=0, /, "
        "c=1)' the real `b` comes out default==Parameter.empty, but the F2P test "
        "asserts sig.parameters['b'].default == '0' — the faithful patch FAILS the "
        "F2P and does NOT resolve (it IS the bug being fixed; cf. model_prepatch).",
        "rationale": "rejected by C3 (positional-only-not-exempt: Result()[p] != "
        "EMPTY() for a posonly p in the trailing default block) AND C2 (the "
        "alignment pin) — the loop invariant maintenance at the posonly default "
        "position cannot be re-established with EMPTY().",
    },
    {
        "id": "r2-offby-posonly",
        "kind": "uniqueness",
        "expect": "reject",
        "module": R2_OFFBY_POSONLY,
        "refinement": "this is the pre-patch ordinary-loop alignment: defaults "
        "indexed relative to the ordinary-parameter count alone (boundary "
        "pad+posonly, offset p-pad-posonly), ignoring that posonly params also "
        "consume default slots. On '(a, b=0, /, c=1)' it gives `b` none and "
        "renders the wrong slot for `c`; the F2P test reads b='0', c='1' "
        "position-by-position and FAILS -> does NOT resolve.",
        "rationale": "rejected by C2 (Result()[p] != resolved_default at the "
        "shifted boundary/offset) AND C3 — invariant maintenance fails at the "
        "first mis-aligned position.",
    },
    {
        "id": "r3-all-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": R3_ALL_EMPTY,
        "refinement": "a real patch that never attached any default (omitted the "
        "defaults loop) renders every positional parameter with "
        "default==Parameter.empty; the F2P test reads b='0', c='1' and FAILS -> "
        "does NOT resolve. The cheapest impl that satisfies the length/frame "
        "clauses but not the value pin — the soundness control for C2.",
        "rationale": "rejected by C2 (the alignment pin at every defaulted "
        "position): for p >= pad the invariant requires render(provided[p-pad]) "
        "(!= EMPTY() by the render axiom), which EMPTY() cannot satisfy.",
    },
    {
        "id": "r4-frame-mutation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": R4_FRAME_MUTATION,
        "refinement": "a faithful patch mutating args.defaults in place "
        "(args.defaults[i] = <rendered>) corrupts the shared AST `definition` the "
        "ordinary-args loop re-reads from the SAME padded `defaults`; subsequent "
        "reads see clobbered nodes and render the wrong source for `c`. The F2P "
        "test reads b='0', c='1' off the corrupted defaults and FAILS -> does NOT "
        "resolve.",
        "rationale": "MANDATORY frame-mutation probe. `provided` is held at "
        "Acc(list_pred(provided), 1/2) in Requires + Invariant + Ensures; the "
        "write `provided[0] = EMPTY()` needs full write permission the impl does "
        "NOT hold => rejected for INSUFFICIENT PERMISSION (the permission system, "
        "not a value clause). Gold value invariants kept verbatim so the rejection "
        "is attributable to the write.",
    },
    {
        "id": "r5-short-result",
        "kind": "uniqueness",
        "expect": "reject",
        "module": R5_SHORT,
        "refinement": "a real patch with an off-by-one loop range "
        "(range(len(args.args)-1)) omits the final positional parameter entirely; "
        "the F2P test's list(sig.parameters.keys()) == ['a','b','c'] is missing "
        "'c' and FAILS -> does NOT resolve.",
        "rationale": "rejected by C1 (len(Result()) == positionals): the narrowed "
        "loop guard exits with len(result) == positionals-1 (for positionals>0), "
        "so the postcondition length clause cannot be proven. Supporting "
        "partial-domain/last-element case.",
    },
    {
        "id": "r6-self-delegation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": R6_SELF_DELEGATION,
        "refinement": "`return signature_from_str(signature)` as the first "
        "statement of the patched signature_from_str "
        "(sphinx/util/inspect.py:516), the entire gold body (left-pad + both "
        "absolute-index loops) present and correct below it. Every call dies with "
        "RecursionError: the F2P test_signature_from_str_positionaly_only_args "
        "fails and 5 of 33 P2P signature tests fail with it, while the module "
        "still imports and 28 P2P still pass -- a wrong result, not a collection "
        "failure. Measured by the official resolve harness as completed=True, "
        "resolved=False, 3/3 consistent attempts.",
        "rationale": "the DIVERGENCE lane. Rejected by C6 "
        "(Requires(MustTerminate(2))): an obligated caller may not delegate to a "
        "callee at its own level, so Nagini reports `Obligation leak check "
        "failed. Callee resolve_positional_defaults might not take all "
        "unsatisfied obligations from the caller.` Without C6 this rival VERIFIES "
        "-- it satisfies C1-C5 vacuously, since under partial correctness they "
        "are claimed only of runs that reach the return, and this one never does.",
    },
    {
        "id": "r7-decorative-measure",
        "kind": "uniqueness",
        "expect": "reject",
        "module": R7_DECORATIVE_MEASURE,
        "refinement": "a `while True: pass` spin inserted ahead of the added "
        "block at sphinx/util/inspect.py:521, gold body intact below. "
        "signature_from_str never returns, so the F2P test and every P2P "
        "signature test hang rather than pass -- the patch resolves nothing.",
        "rationale": "the DIVERGENCE lane, second shape: the obligation must not "
        "be satisfiable by SPELLING. C6's measure lives in the impl region, which "
        "spec_view elides, so a rival writes its own; this one writes a CONSTANT "
        "Invariant(MustTerminate(1)) on an unbounded loop. Rejected with "
        "`Obligation leak check failed. Loop might not keep promise to "
        "terminate.` -- the level has to strictly decrease, not merely appear.",
    },
    {
        "id": "r8-raise-exit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": R8_RAISE_EXIT,
        "refinement": "`raise RuntimeError` appended to the added block at "
        "sphinx/util/inspect.py:552, after the two absolute-index loops have "
        "built the right params. signature_from_str raises on every input, so the "
        "F2P test and every P2P signature test error out -- it resolves nothing.",
        "rationale": "the other non-returning EXIT. The gold computation, "
        "invariants and measure are kept verbatim and the finished list is never "
        "handed back, so C6 alone does not refuse it (the method does stop). The "
        "frozen contract declares NO Exsures, so the post-conditions region "
        "promises a Result on every admitted input and admits no exceptional "
        "exit: rejected with `Exhale might fail. Assertion \"method raises no "
        "exceptions\" might not hold.`",
    },
]


# ===========================================================================
# AXIOM lane — render (A-consumed, domain-restricted) + the A-reference deep
# alignment model. Both are validated by axiom_check.py against the REAL callee
# in the instance image; the probes below reuse/strengthen that logic. We embed
# axiom_check.py's source on the HOST (the runner mounts ONLY the probe script at
# /work — model.py / axiom_check.py are NOT in-container; directive-6) and call
# the REAL routines (no source-scraping; directive-4). Files opened utf-8
# (directive-5). apply_gold=True: the axioms describe POST-gold behaviour (the
# deep alignment model == the post-patch signature_from_str).
# ===========================================================================

# ax-sound-render: AXIOM-SOUNDNESS for the render axiom (and the deep alignment
# A-reference). Runs axiom_check.main() — the real signature_from_str on 3900
# signatures + the real ast.unparse on-domain (non-sentinel string, deterministic)
# and off-domain (raises NotImplementedError). If the real callee disagrees with
# the axiom Ensures anywhere, axiom_check exits non-zero -> AXIOM-UNSOUND.
_AX_SOUND_PROBE = (
    "import sys\n"
    "AXIOM_CHECK_SRC = r'''" + _AXIOM_CHECK_SRC.replace("'''", "''' \"'''\" r'''") + "'''\n"
    + r'''
g = {"__name__": "__axiom_check__", "__file__": "/work/axiom_check_embedded.py"}
try:
    exec(compile(AXIOM_CHECK_SRC, "axiom_check_embedded.py", "exec"), g)
    rc = g["main"]()
except SystemExit as e:
    rc = e.code if isinstance(e.code, int) else (0 if e.code in (None, "") else 1)
except Exception:
    import traceback
    traceback.print_exc()
    rc = 1
print("AX-SOUND render+alignment rc=%r" % (rc,))
sys.exit(0 if rc == 0 else 1)
'''
)


# ax-cover-render: AXIOM-CONTAINMENT. The model applies `render` ONLY at indices
# p >= pad to provided[p-pad], and the function-under-spec REQUIRES every supplied
# default to be renderable (Forall j: renderable(provided[j])). So every callee
# input the model can reach is, by precondition, in render's Requires domain
# (`renderable`). The containment question is whether the F2P/P2P signatures the
# patch must resolve actually present only renderable default expressions (else
# the caller could reach an input outside the covered domain on a resolving
# signature -> AXIOM-TOO-WEAK-FOR-CALLER). We confirm: every default expression
# the F2P/P2P tests pass to the real renderer renders WITHOUT raising (is in
# `renderable`), so the domain restriction never excludes a caller-reachable
# resolving input. We also confirm the renderer is observably PARTIAL (some
# grammar-valid default raises) so `renderable` is non-vacuous (covering its true
# domain, not everything).
_AX_COVER_PROBE = r'''
import ast
import sys

from sphinx.pycode.ast import unparse as ast_unparse

# Default expressions the F2P/P2P signature tests actually present to the renderer
# (literal/constant/name/attribute/collection/op defaults — the renderable shape).
# These are exactly the value codes the caller (signature_from_str) reaches under
# the gold patch on the resolving signatures; each must lie INSIDE `renderable`
# (the real renderer returns, never raising) so the domain restriction does not
# drop a caller-reachable resolving input.
caller_reachable = ["0", "1", "None", "True", "False", "'x'", "3.14",
                    "(1, 2)", "[1]", "{1: 2}", "{1, 2}", "foo.BAR",
                    "-1", "1 + 2", "lambda x: x", "...", "b'b'"]
for e in caller_reachable:
    node = ast.parse(e, mode="eval").body
    try:
        out = ast_unparse(node)
    except Exception as ex:
        print("CONTAINMENT VIOLATION: caller-reachable default %r is OUTSIDE "
              "renderable (real renderer raised %r) -> AXIOM-TOO-WEAK-FOR-CALLER"
              % (e, ex))
        sys.exit(1)
    assert isinstance(out, str) and out != "", \
        "renderer returned non-string/empty for caller-reachable %r: %r" % (e, out)

# Non-vacuity: `renderable` must NOT be the whole universe (else it would be a
# meaningless guard). Confirm the real renderer is observably partial — at least
# one grammar-valid default raises (it is genuinely outside the covered domain).
off_domain = ["1 if x else 2", "x == y", "f'{x}'", "z[1:2]", "{**w}",
              "[i for i in r]", "(yield x)"]
raised = 0
for e in off_domain:
    node = ast.parse(e, mode="eval").body
    try:
        ast_unparse(node)
    except Exception:
        raised += 1
assert raised >= 1, (
    "expected the partial renderer to raise on at least one unsupported default "
    "(renderable would be vacuous otherwise); none of %r raised" % (off_domain,))

print("AX-COVER OK: all %d caller-reachable F2P/P2P default exprs are inside "
      "renderable (renderer returns); renderer observably partial (%d/%d "
      "off-domain raise) so renderable is non-vacuous"
      % (len(caller_reachable), raised, len(off_domain)))
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-render",
        "axiom": "render",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": "runs the bundle's own axiom_check.main() (embedded from the "
        "HOST; the runner mounts only the probe) against the REAL post-gold "
        "signature_from_str (3900 signatures) and the REAL ast.unparse on-domain "
        "(non-sentinel string, deterministic) and off-domain (raises "
        "NotImplementedError). If the real callee violates the render Ensures "
        "(Result() != EMPTY()) or the deep alignment model anywhere -> "
        "AXIOM-UNSOUND.",
    },
    {
        "id": "ax-cover-render",
        "axiom": "render",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": "containment: every default expression the caller "
        "(signature_from_str) reaches on the F2P/P2P resolving signatures is "
        "INSIDE render's Requires domain (`renderable` — the real renderer "
        "returns, never raising), so the domain restriction never excludes a "
        "caller-reachable resolving input. Also confirms `renderable` is "
        "non-vacuous (the renderer is observably partial). A caller-reachable "
        "default OUTSIDE the covered domain would be AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
