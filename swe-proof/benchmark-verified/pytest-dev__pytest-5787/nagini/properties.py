# properties.py — PBT falsification battery for pytest-dev__pytest-5787.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses: each
# SPEC_TESTS entry is a full model.py variant that shares the FROZEN spec
# (axioms/pure/pre/post-conditions/invariants regions untouched at the
# spec-view level) and swaps ONLY text inside the # impl-start/# impl-end region
# (spec_view elides the impl region — markers + nested invariants inclusive — so
# editing anything strictly between # impl-start and # impl-end preserves
# same_spec). The runner checks each with Nagini verify + markers.same_spec.
#
# Defended surface (read from model.py + refinement.md + mapping.md + meta.json):
#   serialize_chain(chain: List[int]) -> List[int]
#   deserialize_chain(transport: List[int]) -> List[int]
#   Two symmetric, cooperating sites. Each:
#     * input is READ-ONLY: Requires(Acc(list_pred(X), 1/2)) — half permission.
#     * Requires(len(X) >= 1)   (a chain is >= 1 link; the degenerate case)
#     * Ensures(Acc(list_pred(X), 1/2))            (input still readable)
#     * Ensures(Acc(list_pred(Result())))          (fresh output owned)
#     * LOAD-BEARING: Ensures(len(Result()) == len(X))           (count survives)
#     * LOAD-BEARING: Ensures(Forall k in [0,len(X)):
#                         ToSeq(Result())[k] == copy_link(ToSeq(X)[k]))  (order +
#                         per-link content survive)
#   copy_link is the @Pure IDENTITY (copy_link(t)==t), grounded in the input —
#   NOT an opaque answer-key oracle. See 'assessment' re ungrounded-oracle echo.
#
# The single behaviour under test is that the WHOLE chain (count + order +
# per-link content) survives the round trip; a multi-stage failure must not
# collapse to a single stage. The two model_prepatch*.py skeletons each emit/
# rebuild only the outermost link and FAIL len(Result())==len(X) for len>=2.
#
# F2P: testing/test_reports.py::TestReportSerialization::test_chained_exceptions
#      [TestReport] and [CollectReport] — both assert the reconstructed
#      ExceptionChainRepr.chain has the SAME length (>= 2) and per-link content
#      as the original (the whole multi-stage failure round-trips).

from pathlib import Path

INSTANCE = "pytest-dev__pytest-5787"
FLOAT_ENCODING = None  # meta.json float_encoding == null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The two full impl blocks (everything strictly between # impl-start and
# # impl-end), extracted verbatim from model.py. Every rival edits ONLY one of
# these blocks, so the frozen spec is provably untouched (same_spec).
# ---------------------------------------------------------------------------
_SER_IMPL = """    out = []  # type: List[int]
    i = 0
    while i < len(chain):
        # invariants-start
        Invariant(Acc(list_pred(chain), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(chain))
        Invariant(len(out) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                  ToSeq(out)[k] == copy_link(ToSeq(chain)[k])),
                  [[ToSeq(out)[k]]])))
        Invariant(MustTerminate(len(chain) - i + 1))
        # invariants-end
        old = out  # type: List[int]
        out = out + [chain[i]]
        Assert(ToSeq(out) == ToSeq(old) + PSeq(chain[i]))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(old),
               ToSeq(out)[k] == ToSeq(old)[k]), [[ToSeq(out)[k]]])))
        Assert(ToSeq(out)[i] == chain[i])
        i = i + 1
    return out
"""

_DES_IMPL = """    out = []  # type: List[int]
    i = 0
    while i < len(transport):
        # invariants-start
        Invariant(Acc(list_pred(transport), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(transport))
        Invariant(len(out) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                  ToSeq(out)[k] == copy_link(ToSeq(transport)[k])),
                  [[ToSeq(out)[k]]])))
        Invariant(MustTerminate(len(transport) - i + 1))
        # invariants-end
        old = out  # type: List[int]
        out = out + [transport[i]]
        Assert(ToSeq(out) == ToSeq(old) + PSeq(transport[i]))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(old),
               ToSeq(out)[k] == ToSeq(old)[k]), [[ToSeq(out)[k]]])))
        Assert(ToSeq(out)[i] == transport[i])
        i = i + 1
    return out
"""

# Sanity: both blocks are present exactly once.
assert _BASE.count(_SER_IMPL) == 1, "serialize impl block drifted"
assert _BASE.count(_DES_IMPL) == 1, "deserialize impl block drifted"


# === POSITIVE CONTROL (soundness) ==========================================
# Structurally-different but CORRECT serialize: hoist `n = len(chain)` into a
# local, loop `while i < n`, and bind the per-step appended element into a named
# local `link` instead of inlining `chain[i]`. This changes the executable shape
# (loop bound is a local; element bound to a name) while keeping the gold
# forward-append proof intact — every gold framing assert (prefix preservation,
# the per-element pin, the ToSeq concat) is kept VERBATIM, so no
# auto-undischargeable lemma is needed (directive-2/3 safe: NOT a loop-direction
# flip, NOT a forward-append-vs-front-recursive-fold mismatch). Must verify; if a
# faithful correct impl cannot verify => SPEC-TOO-STRONG.
# Termination: this loop counts against the HOISTED local `n`, not against
# len(chain), so its measure is `n - i + 1` -- the bound its own condition
# `i < n` names. (`n == len(chain)` is an invariant here, so the gold's measure
# would also be provable, but the measure has to belong to THIS loop.)
_POS_SER = """    out = []  # type: List[int]
    i = 0
    n = len(chain)  # type: int
    while i < n:
        # invariants-start
        Invariant(Acc(list_pred(chain), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(n == len(chain))
        Invariant(0 <= i and i <= len(chain))
        Invariant(len(out) == i)
        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,
                  ToSeq(out)[k] == copy_link(ToSeq(chain)[k])),
                  [[ToSeq(out)[k]]])))
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        old = out  # type: List[int]
        link = chain[i]  # type: int
        out = out + [link]
        Assert(ToSeq(out) == ToSeq(old) + PSeq(link))
        Assert(Forall(int, lambda k: (Implies(0 <= k and k < len(old),
               ToSeq(out)[k] == ToSeq(old)[k]), [[ToSeq(out)[k]]])))
        Assert(ToSeq(out)[i] == chain[i])
        i = i + 1
    return out
"""
POS_CONTROL = _swap(_BASE, _SER_IMPL, _POS_SER)


# === ADMISSIBILITY =========================================================
# Insert, right after `# impl-start` of serialize_chain (before any gold
# obligation), a probe that constructs a representative F2P-shaped MULTI-STAGE
# chain ([1, 2, 3], a length-3 chain — originating cause, intermediate, outer)
# and asserts the precondition predicate (list_pred) and the Requires shape
# (len >= 1) are establishable on it, plus the deep-model identity copy_link is
# usable. If this block cannot verify, a normal multi-stage input cannot satisfy
# the Requires => PRECOND-TOO-STRONG. The gold impl follows verbatim, so every
# postcondition obligation is still discharged.
_ADMISS_PROBE = (
    "    # ADMISSIBILITY PROBE: a normal multi-stage (length-3) chain shape\n"
    "    # establishes the Requires predicate and the len>=1 lower bound.\n"
    "    probe = [1, 2, 3]  # type: List[int]\n"
    "    Assert(list_pred(probe))\n"
    "    Assert(len(probe) >= 1)\n"
    "    Assert(len(probe) == 3)\n"
    "    Assert(copy_link(probe[0]) == probe[0])\n"
)
# Prepend the probe to the gold serialize impl block (gold follows verbatim, so
# every postcondition obligation is still discharged after the probe).
_ADMISS_SER = _ADMISS_PROBE + _SER_IMPL
ADMISS = _swap(_BASE, _SER_IMPL, _ADMISS_SER)


# === FRAME-MUTATION (mandatory: read-only input) ===========================
# `chain` is held at HALF permission (Requires(Acc(list_pred(chain), 1/2))). A
# rival that WRITES to it (chain.append(...)) to influence the output must be
# rejected for INSUFFICIENT PERMISSION — a mutating write needs full permission,
# only 1/2 is held. The gold loop is kept VERBATIM after the write, so the
# rejection is attributable solely to the illegal mutation of the read-only
# input, not to any postcondition.
# refinement: a faithful real patch whose serialize step mutated rep.longrepr
# (e.g. appending to / rewriting rep.longrepr.chain in place while serializing)
# would corrupt the live failure report object that pytest still holds and later
# renders to the terminal; the F2P round-trip + every report-display P2P
# (test_reprtraceback_*, terminal output) would observe a mutated original and
# diverge — it would NOT resolve.
# rejection source: the PERMISSION SYSTEM — Acc(list_pred(chain), 1/2) does not
# admit a write to `chain`.
_FRAME_SER = "    chain.append(chain[len(chain) - 1])\n" + _SER_IMPL
FRAME_SER_WRITE = _swap(_BASE, _SER_IMPL, _FRAME_SER)

# Mirror frame-mutation on the deserialize site (transport is also read-only).
_FRAME_DES = "    transport.append(transport[len(transport) - 1])\n" + _DES_IMPL
FRAME_DES_WRITE = _swap(_BASE, _DES_IMPL, _FRAME_DES)


# === UNIQUENESS / REJECT rivals (chain-collapse weakness class) ============

# --- (a) Outermost-only (the literal pre-patch shape, serialize site): emit
# only chain[len(chain)-1]. Output length is 1; for len(chain)>=2 this breaks the
# load-bearing Ensures(len(Result()) == len(chain)). This is exactly
# model_prepatch.py.
# refinement: this IS the pre-patch bug — the old disassembled_report serialized
# only rep.longrepr.reprtraceback/reprcrash (the outermost link chain[-1]); the
# F2P test_chained_exceptions asserts the reconstructed chain has length >= 2 and
# per-link content, so a chained failure collapses to one stage — it does NOT
# resolve (it is the very bug the patch fixes).
# rejection source: Ensures(len(Result()) == len(chain)).
_OUTER_ONLY_SER = """    out = []  # type: List[int]
    out = out + [chain[len(chain) - 1]]
    return out
"""
OUTER_ONLY = _swap(_BASE, _SER_IMPL, _OUTER_ONLY_SER)


# --- (b) Drop-first-link (partial-domain, serialize site): emit links 1..len-1
# (skip index 0, the ORIGINATING cause). Correct on a length-1 chain (degenerate
# single-stage failure: loop is empty so result is empty -> still breaks len==1,
# so it is wrong even there) but the point is it diverges on every multi-stage
# chain: length is len-1 and the per-index content is shifted.
# refinement: a faithful patch serializing rep.longrepr.chain[1:] would drop the
# originating exception (the root cause) from the transport form; F2P
# test_chained_exceptions asserts the FULL chain (the [TestReport]/[CollectReport]
# cases build a 2-link chain and check both links) — the dropped root cause fails
# the length and per-link-content assertions — it would NOT resolve.
# rejection source: Ensures(len(Result()) == len(chain)) AND the per-index Forall
# (ToSeq(Result())[0] would equal chain[1], not copy_link(chain[0])).
# Termination: same `while i < len(chain)` bound as the gold, so the same
# `len(chain) - i + 1` measure applies -- starting at i=1 rather than i=0 only
# means the loop enters with a measure one SMALLER, which is still positive and
# still drops by one per pass (this variant's divergence is the dropped index 0,
# not a different counting).
_DROP_FIRST_SER = """    out = []  # type: List[int]
    i = 1
    while i < len(chain):
        # invariants-start
        Invariant(Acc(list_pred(chain), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(1 <= i and i <= len(chain))
        Invariant(len(out) == i - 1)
        Invariant(MustTerminate(len(chain) - i + 1))
        # invariants-end
        out = out + [chain[i]]
        i = i + 1
    return out
"""
DROP_FIRST = _swap(_BASE, _SER_IMPL, _DROP_FIRST_SER)


# --- (c) Reversed order (partial-domain / order, serialize site): emit every
# link but in REVERSE order. Length is correct; per-index content is wrong for
# every chain whose links are not palindromic, i.e. every genuine multi-stage
# failure. Correct only on the degenerate length-1 chain.
# refinement: a faithful patch iterating reversed(rep.longrepr.chain) would
# serialize the stages newest-first; on deserialize the rebuilt ExceptionChainRepr
# would present the outermost failure as the root cause. F2P test_chained_exceptions
# asserts per-index traceback text equality (loaded.longrepr.chain[k] == original
# .longrepr.chain[k] for each k) — reversed order fails per index — it would NOT
# resolve.
# rejection source: the per-index Ensures Forall
# (ToSeq(Result())[k] == copy_link(ToSeq(chain)[k]) requires SAME order).
# Termination: the REVERSAL is in where each link is PREPENDED, not in how the
# loop counts -- the cursor is still `i` going up to len(chain) -- so the gold's
# `len(chain) - i + 1` is the right measure here too.
_REVERSE_SER = """    out = []  # type: List[int]
    i = 0
    while i < len(chain):
        # invariants-start
        Invariant(Acc(list_pred(chain), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(chain))
        Invariant(len(out) == i)
        Invariant(MustTerminate(len(chain) - i + 1))
        # invariants-end
        out = [chain[i]] + out
        i = i + 1
    return out
"""
REVERSE = _swap(_BASE, _SER_IMPL, _REVERSE_SER)


# --- (d) Constant-link / first-link-duplicated (value-level, serialize site):
# emit a list of the CORRECT length but with every position carrying the FIRST
# link (chain[0]) instead of chain[k]. Length is correct; per-index content is
# wrong for every k>=1 on any chain whose links differ.
# refinement: a faithful patch that copied rep.longrepr.chain[0] into every
# transport slot (e.g. a serialize loop that read the wrong index) would duplicate
# the originating cause across all stages; F2P test_chained_exceptions asserts each
# reconstructed link's traceback text matches the original at that index — the
# duplicated content fails for the later stage(s) — it would NOT resolve.
# rejection source: the per-index Ensures Forall
# (ToSeq(Result())[k] == copy_link(ToSeq(chain)[k]); k=1.. would carry chain[0]).
# Termination: only the READ index is wrong (always 0); the loop still counts `i`
# up to len(chain), so the gold's `len(chain) - i + 1` is this loop's measure.
_CONST_SER = """    out = []  # type: List[int]
    i = 0
    while i < len(chain):
        # invariants-start
        Invariant(Acc(list_pred(chain), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= len(chain))
        Invariant(len(out) == i)
        Invariant(MustTerminate(len(chain) - i + 1))
        # invariants-end
        out = out + [chain[0]]
        i = i + 1
    return out
"""
CONST_LINK = _swap(_BASE, _SER_IMPL, _CONST_SER)


# --- (e) Deserialize-site collapse (the literal model_prepatch_2.py shape):
# rebuild a single link from the outermost transport entry. Mirrors (a) on the
# deserialize site to pin BOTH cooperating functions, not just serialize.
# refinement: this IS the pre-patch _from_json, which always rebuilt one
# ReprExceptionInfo from the outermost entry; even given a full transport form,
# deserialization collapses the chain to length 1. F2P test_chained_exceptions
# reads loaded_report.longrepr.chain back and asserts length >= 2 — it would NOT
# resolve.
# rejection source: Ensures(len(Result()) == len(transport)) of deserialize_chain.
_DES_COLLAPSE = """    out = []  # type: List[int]
    out = out + [transport[len(transport) - 1]]
    return out
"""
DES_COLLAPSE = _swap(_BASE, _DES_IMPL, _DES_COLLAPSE)


SPEC_TESTS = [
    {
        "id": "pos-control-localreshape",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_CONTROL,
        "rationale": "structurally-different CORRECT serialize (loop bound hoisted "
        "into local `n`, appended element bound to local `link`) keeping every gold "
        "forward-append framing assert verbatim — must verify, else SPEC-TOO-STRONG. "
        "Local-variable reshape only (directive-2/3 safe: no loop-direction flip, no "
        "front-recursive-fold mismatch). This also IS the honest cheapest-impl "
        "positive control for the (grounded, identity) copy_link oracle — see "
        "'assessment'.",
    },
    {
        "id": "admiss-multistage",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS,
        "rationale": "a probe constructs an F2P-shaped multi-stage chain [1,2,3] and "
        "asserts list_pred(probe) + len(probe)>=1 + copy_link identity — the "
        "Requires(Acc(list_pred(chain),1/2)) and Requires(len(chain)>=1) must admit a "
        "normal multi-stage input, else PRECOND-TOO-STRONG. Gold impl follows "
        "verbatim so all postconditions still discharge.",
    },
    {
        "id": "frame-serialize-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_SER_WRITE,
        "refinement": "a faithful real patch whose serialize step mutated rep.longrepr "
        "(appending to / rewriting rep.longrepr.chain in place) would corrupt the live "
        "failure report pytest still holds and later renders; the F2P round trip and "
        "report-display P2P would observe a mutated original and diverge — it would NOT "
        "resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: chain is held at "
        "Acc(list_pred(chain),1/2) (read-only half permission), so the in-place "
        "chain.append(...) write cannot verify (insufficient permission). MANDATORY "
        "frame-mutation probe for the read-only input; the gold loop is kept verbatim "
        "so the rejection is attributable to the write alone.",
    },
    {
        "id": "frame-deserialize-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_DES_WRITE,
        "refinement": "a faithful real patch whose deserialize step mutated its input "
        "transport list (reportdict['longrepr']['chain']) in place would corrupt the "
        "decoded report dict that other reconstruction steps read; the rebuilt report "
        "would carry the wrong links and the F2P round trip would diverge — it would "
        "NOT resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: transport is held at "
        "Acc(list_pred(transport),1/2), so the in-place transport.append(...) write "
        "cannot verify (insufficient permission). Mirrors the mandatory frame probe on "
        "the deserialize site.",
    },
    {
        "id": "outermost-only-serialize",
        "kind": "uniqueness",
        "expect": "reject",
        "module": OUTER_ONLY,
        "refinement": "this IS the pre-patch bug — disassembled_report serialized only "
        "rep.longrepr.reprtraceback/reprcrash (the outermost link chain[-1]); F2P "
        "test_chained_exceptions[TestReport]/[CollectReport] assert the reconstructed "
        "chain has length >= 2 and per-link content, so the chained failure collapses "
        "to one stage — it does NOT resolve (the very bug the patch fixes).",
        "rationale": "rejected by the load-bearing Ensures(len(Result()) == len(chain)) "
        "(== model_prepatch.py / G-DIFF). Partial-domain: correct only on a degenerate "
        "length-1 chain, collapses every multi-stage chain.",
    },
    {
        "id": "deserialize-collapse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": DES_COLLAPSE,
        "refinement": "this IS the pre-patch _from_json, which always rebuilt one "
        "ReprExceptionInfo from the outermost entry; even given a full transport form, "
        "deserialization collapses the chain to length 1. F2P test_chained_exceptions "
        "reads loaded_report.longrepr.chain and asserts length >= 2 — it would NOT "
        "resolve (== model_prepatch_2.py / G-DIFF).",
        "rationale": "rejected by Ensures(len(Result()) == len(transport)) of "
        "deserialize_chain. Pins the SECOND cooperating site, not just serialize.",
    },
    {
        "id": "drop-first-link-serialize",
        "kind": "uniqueness",
        "expect": "reject",
        "module": DROP_FIRST,
        "refinement": "a faithful patch serializing rep.longrepr.chain[1:] would drop "
        "the originating exception (root cause) from the transport form; F2P "
        "test_chained_exceptions builds a 2-link chain and checks BOTH links, so the "
        "dropped root cause fails the length and per-link-content assertions — it would "
        "NOT resolve.",
        "rationale": "rejected by Ensures(len(Result()) == len(chain)) and the per-index "
        "Forall (ToSeq(Result())[0] would carry chain[1], not copy_link(chain[0])). "
        "Partial-domain: diverges on the originating-cause sub-domain (index 0).",
    },
    {
        "id": "reverse-order-serialize",
        "kind": "uniqueness",
        "expect": "reject",
        "module": REVERSE,
        "refinement": "a faithful patch iterating reversed(rep.longrepr.chain) would "
        "serialize the stages newest-first; the rebuilt ExceptionChainRepr would present "
        "the outermost failure as the root cause. F2P test_chained_exceptions asserts "
        "per-index traceback text equality, so reversed order fails per index — it would "
        "NOT resolve.",
        "rationale": "rejected by the per-index Ensures Forall "
        "(ToSeq(Result())[k] == copy_link(ToSeq(chain)[k]) demands SAME order). Length "
        "is preserved, so ONLY the order clause catches it — a fuzzer dropping a branch "
        "never builds this.",
    },
    {
        "id": "const-first-link-serialize",
        "kind": "uniqueness",
        "expect": "reject",
        "module": CONST_LINK,
        "refinement": "a faithful patch that copied rep.longrepr.chain[0] into every "
        "transport slot would duplicate the originating cause across all stages; F2P "
        "test_chained_exceptions asserts each reconstructed link's traceback text "
        "matches the original at that index — the duplicated content fails for the "
        "later stage(s) — it would NOT resolve.",
        "rationale": "rejected by the per-index Ensures Forall "
        "(ToSeq(Result())[k] == copy_link(ToSeq(chain)[k]); positions k>=1 would carry "
        "chain[0], not chain[k]). Length is preserved, so ONLY the per-link-content "
        "clause catches it (value-level).",
    },
]


# === AXIOM LANE (A-reference deep model: copy_link + the (de)serialize loops) =
# meta.json axioms == [] (no @ContractOnly axiom the proof consumes). The bundle
# DOES carry one A-reference deep model: the per-link content-preserving copy
# (copy_link = identity) and the whole-chain-preserving serialize/deserialize
# loops, validated == the real pytest callees (_report_to_json /
# _report_kwargs_from_json) by axiom_check.py / G-AX. Per PBT_PLAN §2.4 + §4a,
# an A-reference is checked the same way as an axiom: the deep model must equal
# the real callee on every caller-reachable input. We re-run that exact check as
# a persisted probe.
#
# The probe EMBEDS the bundle's axiom_check.py source verbatim (read on the HOST
# at load time — directive #6: the runner mounts ONLY the probe at /work, so
# axiom_check.py is NOT in-container). It runs with apply_gold=True: the runner
# git-applies the gold patch to /testbed (now PATCHED) and mounts the patch at
# /gold.patch. axiom_check.py's _build_both_trees detects the patched live tree
# via reverse dry-run, reverse-applies a copy to recover the UNPATCHED tree, and
# drives the real pytest report round trip on both — requiring the whole chain
# (len >= 2 + per-index traceback text + description + sections, and renders) to
# SURVIVE on the patched tree and COLLAPSE on the unpatched (base_commit) tree.
# A genuine two-state differential: exit 0 iff the A-reference deep model matches
# the real callee on every F2P-relevant input (TestReport/CollectReport x
# chained with/without `from`).
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()


AXIOM_TESTS = [
    {
        "id": "ax-ref-roundtrip",
        "axiom": "copy_link / serialize_chain+deserialize_chain (A-reference deep model)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "the A-reference deep model (copy_link = identity; the verified "
        "per-link loops emit/reproduce every link in order) must equal the real pytest "
        "callees on every caller-reachable input. The embedded axiom_check.py drives "
        "the REAL report._to_json()/_from_json() round trip in-container on the four "
        "F2P-relevant chained reports and asserts the whole chain (count >= 2 + order + "
        "per-link traceback text + description + sections, renders) SURVIVES on the "
        "PATCHED tree and COLLAPSES on the UNPATCHED (base_commit) tree. If the deep "
        "model disagreed with reality (e.g. the real round trip dropped or reordered a "
        "link), this would exit non-zero => AXIOM-UNSOUND. Caller-domain containment is "
        "automatic: every caller-reachable chain (len >= 1, in particular the >= 2 "
        "multi-stage failures the F2P builds) is exactly what the four enumerated cases "
        "exercise.",
    },
]
