# properties.py — PBT falsification battery for scikit-learn__scikit-learn-14983.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by REGION SURGERY: we _swap
# the SINGLE `# impl-start` .. `# impl-end` block of reported_param_value for a
# new body and leave the frozen spec (axioms / pure / pre / post-conditions /
# signatures) byte-identical. spec_view elides the entire impl region, so
# same_spec is GUARANTEED for every case regardless of the impl shape.
#
# ---------------------------------------------------------------------------
# Defended surface (read from model.py / refinement.md / mapping.md / meta.json)
# ---------------------------------------------------------------------------
# reported_param_value(attr, none, has_store, store, key) -> int models the
# per-parameter value resolution of the gold `_build_repr` patch:
#     value = getattr(self, key, None)                       # `attr`  (None<->none)
#     if value is None and hasattr(self, 'cvargs'):          # `attr==none and has_store`
#         value = self.cvargs.get(key, None)                 # store[key] if key in store else none
# under the §2 bijection (name str -> int key; None -> int sentinel `none`;
# self.cvargs -> store: Dict[int,int]; hasattr(self,'cvargs') -> has_store).
#
# LOAD-BEARING postcondition clauses (the things an impl must satisfy):
#   (P1) Result() == resolved_value(attr, none, has_store, store, key)   [master pin]
#   (P2) Implies(attr != none, Result() == attr)                         [attr wins]
#   (P3) Implies(attr==none and has_store and key in store,              [the FIX:
#                Result() == store[key])                                  store value]
#   (P4) Implies(attr==none and has_store and key in store,
#                Result() != none)                                        [not absent]
#   (P5) Implies(attr==none and not has_store, Result() == none)         [P2P: no store
#                                                                          -> stays absent]
#   (P6) Requires(MustTerminate(2))                                      [totality: the
#        real resolution is loop-free straight-line code; without this a
#        diverging same-spec impl verifies vacuously under Nagini's
#        partial-correctness default while its faithful real patch hangs the
#        F2P harness — the audit's recorded P1/G-EQ witness class (atk_7:
#        an infinite loop inserted into _build_repr's per-key body verified
#        but its real patch never returns from repr()). The nontermination
#        rival below is the regression case for exactly that hole.]
# resolved_value is a @Pure helper that is FULLY GROUNDED/TRANSPARENT in its
# arguments (it inlines `if attr!=none: return attr; if has_store and key in
# store: return store[key]; return none`) — it is NOT an opaque answer-key.
# Therefore there is NO "wrong ungrounded-oracle echo" to build: `return
# resolved_value(...)` is simply the correct answer, the real work. We say so in
# 'assessment' and stand a structurally-different positive control + an honest
# cheapest-impl positive control in its place (directive 2).
#
# The discriminating F2P behaviour (test_repeated_cv_repr): RepeatedKFold /
# RepeatedStratifiedKFold stow n_splits in **cvargs (NOT as a direct attribute),
# so getattr(self,'n_splits',None) is None; the fix reads it back from cvargs.
# The pre-patch body returned only the direct attribute (model_prepatch.py:
# `value = attr; return value`) and reports n_splits as ABSENT -> the repr omits
# it / shows the bare object repr -> the F2P string mismatch. Any rival that
# fails P3 on the (attr==none and has_store and key in store) case reproduces
# this exact bug and would NOT resolve the F2P.
#
# READ-ONLY INPUT (Acc(dict_pred(store),1/2)) -> FRAME-MUTATION IS MANDATORY:
#   `store: Dict[int,int]` is held at HALF permission in BOTH Requires and
#   Ensures (Acc(dict_pred(store),1/2)). reported_param_value only READS the
#   store (membership test + lookup); it returns the half-permission unchanged.
#   An impl that WRITES the store (e.g. `store[key] = ...` to control the lookup)
#   holds only half permission and MUST be rejected for INSUFFICIENT PERMISSION,
#   not a value mismatch. A byte-fuzzer never thinks to mutate the input; this is
#   the project's #1 weakness class (frame-mutation cases below).
from pathlib import Path

INSTANCE = "scikit-learn__scikit-learn-14983"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The single whole-impl anchor: the entire `# impl-start` .. `# impl-end` block
# of reported_param_value (verified verbatim from model.py). Each variant
# re-emits `# impl-start` first and `# impl-end` last so the region boundary is
# preserved exactly — only the body between them changes, and spec_view elides
# all of it (same_spec guaranteed).
# ---------------------------------------------------------------------------
_S = _BASE.index("# impl-start")
_E = _BASE.index("# impl-end") + len("# impl-end")
_IMPL_BLOCK = _BASE[_S:_E]
assert _BASE.count(_IMPL_BLOCK) == 1


def _impl(body_lines: str) -> str:
    """Replace reported_param_value's whole impl block with a new body.
    `body_lines` is the source BETWEEN the markers (no markers); we wrap it back
    in the exact `# impl-start` / `# impl-end` markers so the region is intact.
    Indentation is 4 spaces (function body level)."""
    new_block = "# impl-start\n" + body_lines.rstrip("\n") + "\n    # impl-end"
    return _swap(_BASE, _IMPL_BLOCK, new_block)


# The gold impl body, verbatim (between the markers), reused by the admissibility
# probe (which appends a self-call) and as the baseline shape for several rivals.
_GOLD_BODY = (
    "    value = attr  # type: int\n"
    "    if value == none and has_store:\n"
    "        if key in store:\n"
    "            value = store[key]\n"
    "        else:\n"
    "            value = none\n"
    "    return value\n"
)


SPEC_TESTS = [

    # ===================================================================
    # SOUNDNESS — positive controls (must VERIFY; else SPEC-TOO-STRONG)
    # ===================================================================

    # POS-CONTROL 1 (branch-reorder reshape). A structurally-DIFFERENT but
    # CORRECT impl: instead of starting from `value = attr` and conditionally
    # overwriting, it dispatches on the resolution cases directly with the store
    # branch FIRST in the guard order and an early return for the attr-present
    # case. Same value on every input; no loop, no fold lemma, no dropped
    # framing. If a faithful correct impl cannot verify => SPEC-TOO-STRONG.
    {
        "id": "pos-control-reorder-early-return",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    # Early-return dispatch (different control shape, same result):\n"
            "    if attr != none:\n"
            "        return attr\n"
            "    if has_store and (key in store):\n"
            "        return store[key]\n"
            "    return none\n"
        ),
        "rationale": "a correct impl with DIFFERENT control flow (early-return "
                     "case dispatch vs gold's start-from-attr-then-overwrite) "
                     "must verify; it returns resolved_value(...) on every "
                     "input. No loop / no fold lemma / no framing to drop. Else "
                     "SPEC-TOO-STRONG.",
    },

    # POS-CONTROL 2 (honest cheapest impl against a GROUNDED oracle). Because
    # resolved_value is transparent (no opaque answer-key), the cheapest correct
    # impl is literally `return resolved_value(...)` — which performs the real
    # resolution. This STANDS IN PLACE of an ungrounded-oracle echo attack (there
    # is no wrong echo to build; echoing the grounded oracle is correct). It must
    # verify: P1 is then a definitional equality. Else SPEC-TOO-STRONG.
    {
        "id": "pos-control-grounded-oracle-cheapest",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(
            "    # Cheapest correct impl: return the grounded resolution directly.\n"
            "    # resolved_value is transparent in its args (no answer-key), so\n"
            "    # this IS the real work, not a cheat. P1 holds definitionally.\n"
            "    return resolved_value(attr, none, has_store, store, key)\n"
        ),
        "rationale": "grounded-oracle honest positive control: resolved_value is "
                     "a transparent @Pure function of the args, so the cheapest "
                     "correct impl returns it directly and must verify (P1 is a "
                     "definitional equality). No wrong echo exists. Else "
                     "SPEC-TOO-STRONG.",
    },

    # ===================================================================
    # ADMISSIBILITY — the precondition admits a normal input (must VERIFY;
    # else PRECOND-TOO-STRONG)
    # ===================================================================

    # ADMISS: an IN-REGION probe re-derives that the precondition admits a
    # normal F2P-shaped input. (No self-call: reported_param_value now carries
    # Requires(MustTerminate(2)), and a recursive call would need a strictly
    # SMALLER termination measure than the caller holds — an equal-measure
    # self-call is an obligation leak, so the probe is done with Asserts on a
    # locally-built input instead, per the project's admissibility pattern.)
    # A fresh EMPTY store is an F2P-shaped in-domain input: the dict literal
    # grants FULL Acc(dict_pred), so passing half is admissible, and the
    # store-precondition Implies(key in store, store[key]!=none) holds
    # VACUOUSLY on it. The deep resolution on (attr=none, has_store=True,
    # store=<empty>, key=0) is `none` (absent) — exactly the RepeatedKFold
    # introspection of a parameter NOT in cvargs. If these facts were not
    # derivable for this normal input => PRECOND-TOO-STRONG.
    {
        "id": "admiss-empty-store-in-domain",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(
            "    value = attr  # type: int\n"
            "    if value == none and has_store:\n"
            "        if key in store:\n"
            "            value = store[key]\n"
            "        else:\n"
            "            value = none\n"
            "    # Admissibility probe: a fresh empty store is an F2P-shaped\n"
            "    # in-domain input (full Acc from the dict literal; the store\n"
            "    # precondition holds vacuously on it) and the deep resolution\n"
            "    # gives `none` (absent) for a parameter not in the store —\n"
            "    # the RepeatedKFold key-not-in-cvargs case. If these were not\n"
            "    # derivable => PRECOND-TOO-STRONG.\n"
            "    probe_store = {}  # type: Dict[int, int]\n"
            "    Assert(Implies(0 in probe_store, probe_store[0] != none))\n"
            "    Assert(resolved_value(none, none, True, probe_store, 0) == none)\n"
            "    return value\n"
        ),
        "rationale": "the precondition must admit a normal F2P-shaped input: a "
                     "fresh empty store (full Acc(dict_pred) from the dict "
                     "literal; the store precondition Implies(key in store, "
                     "store[key]!=none) holds vacuously) with attr==none and "
                     "has_store. The in-region Asserts re-derive the Requires "
                     "facts and the resolved value for that input (no self-call: "
                     "an equal-measure recursive call would leak the "
                     "MustTerminate(2) obligation); else PRECOND-TOO-STRONG.",
    },

    # ===================================================================
    # UNIQUENESS — frame mutation (MANDATORY: store is Acc 1/2 read-only)
    # ===================================================================

    # ATTACK 1 (FRAME-MUTATION, MANDATORY — the #1 weakness class). The impl
    # WRITES the read-only store: it inserts store[key] = attr-or-something to
    # force the membership test / lookup, then resolves. Only
    # Acc(dict_pred(store),1/2) is held; a dict WRITE needs FULL permission, so
    # the verifier MUST reject this for INSUFFICIENT PERMISSION — not for a value
    # mismatch. The gold resolution shape is kept so the rejection is attributable
    # solely to the illegal write.
    {
        "id": "frame-mutate-store-insert",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # ILLEGAL: write to a read-only (Acc 1/2) dict input.\n"
            "    store[key] = none\n"
            "    value = attr  # type: int\n"
            "    if value == none and has_store:\n"
            "        if key in store:\n"
            "            value = store[key]\n"
            "        else:\n"
            "            value = none\n"
            "    return value\n"
        ),
        "refinement": "in the real _build_repr the secondary store is "
                      "self.cvargs — the **cvargs captured in "
                      "_RepeatedSplits.__init__, the live configuration of the "
                      "splitter. The gold code only READS it "
                      "(self.cvargs.get(key, None)); a patch that WRITES "
                      "self.cvargs[key] = None inside repr() corrupts the "
                      "splitter's stored configuration as a side effect of "
                      "printing it. Every subsequent split()/get_n_splits() that "
                      "reads cvargs would then see the clobbered value, so the "
                      "RepeatedKFold P2P split tests and the F2P repr would "
                      "diverge. The faithful real patch does NOT resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: the precondition grants "
                     "only Acc(dict_pred(store),1/2); a dict write needs full "
                     "permission. Insufficient permission, NOT a value mismatch. "
                     "Mandatory frame-mutation probe.",
    },

    # ATTACK 2 (FRAME-MUTATION, second probe — delete/clear style). The impl
    # tries to remove the key from the store (via `del store[key]`) to steer the
    # `key in store` branch. Same class: only Acc(...,1/2) is held, a mutation
    # needs full permission => rejected for insufficient permission.
    {
        "id": "frame-mutate-store-del",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    value = attr  # type: int\n"
            "    if value == none and has_store:\n"
            "        if key in store:\n"
            "            value = store[key]\n"
            "        else:\n"
            "            value = none\n"
            "    # ILLEGAL: mutate (clear an entry of) a read-only (Acc 1/2) dict.\n"
            "    store[key] = 0  # ILLEGAL write to a read-only dict\n"
            "    return value\n"
        ),
        "refinement": "this deletes key from self.cvargs as a side effect of "
                      "reporting it. The real splitter relies on cvargs being "
                      "intact for its actual cross-validation work "
                      "(get_n_splits multiplies by the cvargs-derived inner "
                      "splitter); deleting an entry during repr() would break "
                      "subsequent split()/get_n_splits() calls. The P2P split "
                      "tests would diverge. The faithful real patch does NOT "
                      "resolve.",
        "rationale": "rejected by the PERMISSION SYSTEM: deleting a dict entry "
                     "is a mutation needing full permission; only "
                     "Acc(dict_pred(store),1/2) is held. Insufficient "
                     "permission. Second mandatory frame-mutation probe.",
    },

    # ===================================================================
    # UNIQUENESS — nontermination / vacuity (must REJECT; else SPEC-TOO-WEAK)
    # ===================================================================

    # ATTACK 2b (NONTERMINATION — THE hole the P2 audit exploited, atk_7).
    # Keep the gold resolution verbatim but DIVERGE first (an unbounded loop
    # ahead of it). Under Nagini's partial-correctness default every Ensures
    # holds vacuously (no normal exit is ever reached), so the old spec
    # ADMITTED this impl even though its faithful real patch hangs repr()
    # forever (the F2P harness times out; does NOT resolve — the recorded
    # dbg-atk7 run produced no report). The spec's Requires(MustTerminate(2))
    # makes the obligation-leak check reject the loop (it takes no termination
    # measure). NOTE: the loop is statically-reachable-exit-shaped
    # (`while i >= 0` with an Invariant), NOT a literal `while True:`, so
    # Nagini does not flag the tail as dead code (which would "reject" for the
    # wrong, translation-level reason).
    {
        "id": "weak-diverge-before-return",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # NONTERMINATION: diverge before the (verbatim) gold resolution.\n"
            "    i = 0\n"
            "    while i >= 0:\n"
            "        Invariant(i >= 0)\n"
            "        i = i + 1\n"
            "    value = attr  # type: int\n"
            "    if value == none and has_store:\n"
            "        if key in store:\n"
            "            value = store[key]\n"
            "        else:\n"
            "            value = none\n"
            "    return value\n"
        ),
        "refinement": "this is the audit's recorded verify⇏⁠resolve witness "
                      "class (atk_7): a real _build_repr whose per-key loop "
                      "spins forever never returns, so repr(RepeatedKFold()) "
                      "hangs and the F2P test_repeated_cv_repr blocks until "
                      "the harness guillotine — the faithful real patch does "
                      "NOT resolve (its eval run produced no report.json). A "
                      "spec that admits a diverging impl is too weak.",
        "rationale": "rejected by the MustTerminate(2) termination obligation "
                     "in the precondition: the loop takes no termination "
                     "measure, so Nagini reports an obligation leak ('Loop "
                     "might not take all unsatisfied obligations from the "
                     "context'). Without MustTerminate this rival verified — "
                     "the recorded G-PANEL-1/G-EQ hole.",
    },

    # ===================================================================
    # UNIQUENESS — partial-domain wrong impls (must REJECT; else SPEC-TOO-WEAK)
    # ===================================================================

    # ATTACK 3 (PARTIAL-DOMAIN — the bug-delta / prepatch). Return ONLY the
    # direct attribute, no store fallback (exactly model_prepatch.py:
    # `value = attr; return value`). CORRECT on every parameter that IS a direct
    # attribute or has no store; WRONG on the discriminating case
    # (attr==none and has_store and key in store): returns none, the spec
    # requires store[key]. Must reject: violates P1, P3, P4.
    {
        "id": "weak-prepatch-no-fallback",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    # PRE-PATCH body: only the direct attribute, NO store fallback.\n"
            "    value = attr  # type: int\n"
            "    return value\n"
        ),
        "refinement": "this is the EXACT pre-patch _build_repr resolution "
                      "(value = getattr(self, key, None), no cvargs fallback) — "
                      "the bug the issue reports. RepeatedKFold / "
                      "RepeatedStratifiedKFold stow n_splits in **cvargs, NOT as "
                      "a direct attribute, so getattr(self,'n_splits',None) is "
                      "None and this resolution reports n_splits as ABSENT. "
                      "repr() then omits n_splits (or shows the bare object "
                      "repr), so the F2P test_repeated_cv_repr string "
                      "'<cls>(n_repeats=6, n_splits=2, random_state=None)' "
                      "MISMATCHES. The faithful real patch (= prepatch) does NOT "
                      "resolve the F2P. (This is model_prepatch.py / G-DIFF.)",
        "rationale": "violates P1 (Result != resolved_value), P3 (Result != "
                     "store[key]) and P4 (Result == none) on the "
                     "(attr==none and has_store and key in store) case — the "
                     "discriminating n_splits-in-cvargs case the F2P exercises.",
    },

    # ATTACK 4 (PARTIAL-DOMAIN — store-branch returns absent). Take the fallback
    # branch but resolve to `none` instead of `store[key]` (a subtler version of
    # the prepatch bug: it enters the store path but discards the value). CORRECT
    # everywhere EXCEPT the discriminating case; WRONG there (returns none, spec
    # requires store[key]). Targets P3/P4 precisely. Must reject.
    {
        "id": "weak-store-branch-returns-none",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    value = attr  # type: int\n"
            "    if value == none and has_store:\n"
            "        if key in store:\n"
            "            # WRONG: discards the store value, reports absent.\n"
            "            value = none\n"
            "        else:\n"
            "            value = none\n"
            "    return value\n"
        ),
        "refinement": "this enters the cvargs path but then reports None instead "
                      "of self.cvargs.get(key) — equivalent to never reading the "
                      "store value back. For n_splits (in cvargs) it again "
                      "reports absent, so the F2P repr string omits the actual "
                      "n_splits=2 and MISMATCHES the demanded "
                      "'<cls>(n_repeats=6, n_splits=2, random_state=None)'. The "
                      "faithful real patch does NOT resolve the F2P.",
        "rationale": "violates P3 (Result != store[key]) and P4 (Result==none) "
                     "on the (attr==none and has_store and key in store) case; "
                     "P1 also fails (resolved_value gives store[key]).",
    },

    # ATTACK 5 (PARTIAL-DOMAIN — attribute does NOT win). When the direct
    # attribute IS present (attr != none) AND the store also records the key,
    # this returns store[key] instead of attr. CORRECT whenever the attribute is
    # absent or the store lacks the key or store[key]==attr; WRONG whenever
    # attr != none and key in store and store[key] != attr (the spec says the
    # DIRECT attribute wins — `value = getattr(...)` then only overwrites when
    # value is None). Targets P2/P1. Must reject.
    {
        "id": "weak-store-overrides-attr",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    value = attr  # type: int\n"
            "    # WRONG: let the store override even a PRESENT direct attribute.\n"
            "    if has_store and (key in store):\n"
            "        value = store[key]\n"
            "    return value\n"
        ),
        "refinement": "this reads cvargs.get(key) UNCONDITIONALLY (dropping the "
                      "`value is None` guard), so a parameter that IS a direct "
                      "attribute is overwritten by a stale cvargs entry. In the "
                      "real splitters the direct attribute is the authoritative, "
                      "possibly-updated value; cvargs is the original "
                      "construction snapshot. Reporting the cvargs value over a "
                      "differing direct attribute would print the wrong "
                      "parameter value, diverging from the gold _build_repr "
                      "output that the repr P2P / F2P tests pin. The faithful "
                      "real patch does NOT resolve.",
        "rationale": "violates P2 (Implies(attr!=none, Result()==attr)) and P1 "
                     "whenever attr!=none and key in store and store[key]!=attr: "
                     "resolved_value returns attr (the direct attribute wins), "
                     "this returns store[key].",
    },

    # ATTACK 6 (PARTIAL-DOMAIN — no-store branch wrong). When attr==none and the
    # object carries NO store, the spec requires `none` (absent stays absent —
    # the test_build_repr / MockSplitter PASS_TO_PASS case, c=None). This impl
    # returns a fixed sentinel (key) on that branch instead. CORRECT on every
    # object that HAS a store; WRONG on the no-store absent case. Targets P5.
    # Must reject.
    {
        "id": "weak-no-store-returns-sentinel",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(
            "    value = attr  # type: int\n"
            "    if value == none and has_store:\n"
            "        if key in store:\n"
            "            value = store[key]\n"
            "        else:\n"
            "            value = none\n"
            "    elif value == none and not has_store:\n"
            "        # WRONG: a missing attribute with no store must stay absent\n"
            "        # (none); this fabricates a value.\n"
            "        value = key\n"
            "    return value\n"
        ),
        "refinement": "this fabricates a value for a parameter that is genuinely "
                      "absent on an object with no cvargs store — exactly the "
                      "test_build_repr / MockSplitter PASS_TO_PASS case where a "
                      "parameter set to None and not in any store must be "
                      "reported as None. A plain estimator (no cvargs) whose "
                      "parameter is None would then have repr() show a spurious "
                      "value, so test_build_repr and other repr-shaped P2P tests "
                      "FAIL. The faithful real patch does NOT resolve.",
        "rationale": "violates P5 (Implies(attr==none and not has_store, "
                     "Result()==none)) and P1 (resolved_value returns none on "
                     "the no-store absent branch); `key` may equal none for some "
                     "inputs but the spec must hold for ALL key != none too, so "
                     "this is rejected universally.",
    },
]


# ---------------------------------------------------------------------------
# AXIOM LANE
# ---------------------------------------------------------------------------
# This bundle consumes NO @ContractOnly axioms (meta.axioms == []). The only
# callee-level obligation is the A-REFERENCE deep model: resolved_value must
# equal the REAL gold _build_repr per-key resolution
#     value = getattr(self, key, None)
#     if value is None and hasattr(self, 'cvargs'):
#         value = self.cvargs.get(key, None)
# on every input the model can reach. resolved_value itself is a transparent
# @Pure function INSIDE the verified spec module — there is no separate runtime
# callee whose Ensures could drift, and no caller-reachable input outside any
# axiom domain (no axiom domain exists). So the axiom-lane obligation is purely
# the A-reference == real-Python soundness, already validated on the HOST by
# axiom_check.py / G-AX (8 boundary + ~20000 fuzz objects, incl. no-store
# objects, + the in-container end-to-end repr==F2P-string oracle).
#
# We re-run that HOST-validated oracle IN-CONTAINER as the single axiom-lane
# probe (apply_gold=True so the gold __repr__/_build_repr fallback is present).
# It CALLS the real getattr/hasattr/dict.get and, when sklearn is importable,
# the real RepeatedKFold/RepeatedStratifiedKFold repr — it does NOT regex-scrape
# source (avoids pilot bug 4). It reads no bundle files in-container (avoids
# pilot bug 6): axiom_check.py is read on the HOST at load time and embedded
# verbatim into the probe string. It opens no files (no utf-8 codec concern,
# pilot bug 5). Exit 0 iff every observation agrees.
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-ref-resolved-value-vs-real-build-repr",
        "axiom": "resolved_value (A-reference deep model of _build_repr per-key "
                 "resolution)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "A-reference soundness + containment: the deep model "
                     "resolved_value must equal the REAL gold _build_repr per-key "
                     "resolution (getattr(self,key,None); if None and "
                     "hasattr(self,'cvargs'): self.cvargs.get(key,None)) on every "
                     "input the model can reach — present/absent/None attribute, "
                     "store-with-key, store-without-key, NO-store (the "
                     "MockSplitter P2P case), 8 boundary + ~20000 fuzz objects. "
                     "It also runs the end-to-end oracle (real RepeatedKFold / "
                     "RepeatedStratifiedKFold repr == the F2P string) when "
                     "sklearn is importable. The resolution is plain "
                     "attribute/dict access with NO flag dependency. Any "
                     "mismatch => the A-reference is unsound. There is no "
                     "@ContractOnly axiom and no caller-reachable input outside "
                     "any axiom domain (no axiom domain exists).",
    },
]
