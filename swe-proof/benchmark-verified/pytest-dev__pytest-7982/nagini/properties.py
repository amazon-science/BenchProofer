# properties.py — PBT falsification battery for pytest-dev__pytest-7982.
#
# NOT a Nagini module: a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TEST is a full model.py variant built by region-surgery — _swap edits
# ONLY text physically inside the # impl-start / # impl-end span (the loop body
# AND the nested # invariants-start/-end, which spec_view elides wholesale), so
# the frozen spec (axioms/pure/pre-conditions/post-conditions) is provably
# untouched and markers.same_spec holds for every case.
#
# Defended surface (read adversarially, not mechanically):
#   descend_decisions(kinds: PSeq[int], selected: PSeq[bool]) -> PSeq[bool]
#     Requires:  len(kinds) == len(selected)
#     Ensures:   len(Result()) == len(kinds)
#                Forall i in [0,len): Result()[i] == should_descend(kinds[i], selected[i])
#     where should_descend(k, s) == resolves_to_dir(k) and s
#       and resolves_to_dir(k)   == (k == 1 or k == 2)
#
# The load-bearing clause is the per-element Forall pinning Result()[i] to a
# GROUNDED pure function of the inputs (it fully unfolds to
# (kinds[i]==1 or kinds[i]==2) and selected[i]). The discriminating row is
# code 2 (link-to-directory): the fix flips is_dir(follow_symlinks=False)
# (pre-patch, code 1 only) to is_dir() (post-patch, codes 1 and 2). The F2P
# test (test_collect_symlink_dir) requires a SELECTED link-to-directory to be
# descended into; the pre-patch no-follow classification fails it.
#
# Inputs are PSeq pure values: they carry NO heap permission, so there is NO
# Acc(x, 1/2) read-only parameter and NOTHING to mutate. The frame-mutation
# attack (overwrite a half-permission heap input) is therefore N/A here — see
# 'assessment'. We still include the standard reject-class attacks that DO apply
# to this value abstraction: partial-domain, oracle-grounding (a positive
# control rather than a wrong echo, because the oracle is grounded), and a
# predicate-dropping rival.

from pathlib import Path

INSTANCE = "pytest-dev__pytest-7982"
FLOAT_ENCODING = None  # meta.json float_encoding is null and unused

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchor strings — all strictly INSIDE the impl region (lines 83..107).
# ---------------------------------------------------------------------------

# The single line that computes the per-entry decision (loop body, impl region).
# 8-space indent: it lives inside the `while i < n:` block.
_DECISION = "        decision = resolves_to_dir(kinds[i]) and selected[i]  # type: bool"

# ===========================================================================
# POSITIVE CONTROLS (soundness) — a structurally / locally different but
# CORRECT impl MUST verify; else the postcondition is SPEC-TOO-STRONG.
# Each keeps the gold loop invariants and framing asserts verbatim (directive 5
# / pilot bug #2) and only reshapes the executable decision computation in a way
# provably equal to should_descend, so the gold proof stays valid.
# ===========================================================================

# pos-1: operand-swapped conjunction. `s and rtd(k)` == `rtd(k) and s` (both
# pure, no short-circuit observable difference at the value level). The per-entry
# Assert(decision == should_descend(...)) still discharges.
_pos_swap = _swap(
    _BASE, _DECISION,
    "        decision = selected[i] and resolves_to_dir(kinds[i])  # type: bool",
)

# pos-2: resolves_to_dir unfolded inline to its definition (k==1 or k==2). A
# different surface syntax that is definitionally equal; the Assert against
# should_descend still discharges because should_descend unfolds identically.
_pos_unfold = _swap(
    _BASE, _DECISION,
    "        decision = (kinds[i] == 1 or kinds[i] == 2) and selected[i]  # type: bool",
)

# pos-3: a structurally different decision computation via an explicit local
# `is_dir` boolean, then conjoin. Keeps every gold invariant/assert; only the
# executable shape of computing `decision` changes (local-variable reshape, the
# safe positive-control pattern — NOT a loop-direction flip, directive 3).
_pos_local = _swap(
    _BASE, _DECISION,
    "        entry_is_dir = resolves_to_dir(kinds[i])  # type: bool\n"
    "        decision = entry_is_dir and selected[i]  # type: bool",
)


# ===========================================================================
# REJECT — uniqueness / completeness. Each shares the spec exactly (same_spec)
# and changes ONLY the impl decision; if any VERIFIES, the spec is SPEC-TOO-WEAK.
# Every reject case carries the refinement argument that its faithful real patch
# would NOT resolve the F2P/P2P.
# ===========================================================================

# reject-1: PRE-PATCH no-follow classification (the regression itself). Counts
# only a plain directory (code 1) as a directory, NOT a link-to-directory
# (code 2). This is model_prepatch.py verbatim in decision form. It diverges
# from should_descend exactly on code 2: should_descend(2, True) == True but
# this gives False. Must fail the per-entry Assert / Forall postcondition.
_rej_nofollow = _swap(
    _BASE, _DECISION,
    "        decision = (kinds[i] == 1) and selected[i]  # type: bool",
)

# reject-2: OVER-BROAD classification — treat a link-to-non-dir / broken link
# (code 3) as a directory too. Diverges from should_descend on code 3:
# should_descend(3, True) == False but this gives True.
_rej_code3 = _swap(
    _BASE, _DECISION,
    "        decision = (kinds[i] == 1 or kinds[i] == 2 or kinds[i] == 3) and selected[i]  # type: bool",
)

# reject-3: DROP the caller predicate — descend into every directory entry
# regardless of selected[i]. Diverges from should_descend on any entry where
# resolves_to_dir(k) is True but selected[i] is False.
_rej_drop_pred = _swap(
    _BASE, _DECISION,
    "        decision = resolves_to_dir(kinds[i])  # type: bool",
)

# reject-4: PARTIAL-DOMAIN on the FIRST index — correct on every entry except
# index 0, which is forced False. Pins all-but-one of the domain; the postcond
# Forall covers i == 0 too, so it must reject when should_descend(kinds[0],
# selected[0]) is True.
_rej_first = _swap(
    _BASE, _DECISION,
    "        decision = (i != 0) and (resolves_to_dir(kinds[i]) and selected[i])  # type: bool",
)

# reject-5 (cheap supporting near-miss): constant False. Trivially violates the
# Forall on any descendable selected entry. Carries a real refinement anyway.
_rej_const = _swap(
    _BASE, _DECISION,
    "        decision = False  # type: bool",
)


SPEC_TESTS = [
    {
        "id": "pos-operand-swap",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_swap,
        "rationale": "selected[i] and resolves_to_dir(kinds[i]) is value-equal to "
                     "resolves_to_dir(kinds[i]) and selected[i]; the per-entry "
                     "Assert(decision == should_descend(...)) still discharges, so a "
                     "correct reorder MUST verify (else SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-unfold-resolves",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_unfold,
        "rationale": "(kinds[i]==1 or kinds[i]==2) and selected[i] is the definitional "
                     "unfolding of should_descend; a different surface syntax of the "
                     "same value must verify (else SPEC-TOO-STRONG).",
    },
    {
        "id": "pos-local-isdir",
        "kind": "soundness",
        "expect": "verify",
        "module": _pos_local,
        "rationale": "local-variable reshape: bind is_dir = resolves_to_dir(kinds[i]) "
                     "then conjoin with selected[i]. Keeps every gold invariant/assert; "
                     "only the executable shape changes, so the gold proof stays valid "
                     "(safe positive control per directive 3 / pilot bug #2).",
    },
    {
        "id": "reject-nofollow-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_nofollow,
        "refinement": "This is the pre-patch no-follow classification "
                      "entry.is_dir(follow_symlinks=False) (decision = kinds[i]==1 and "
                      "selected[i]). Its faithful real patch keeps follow_symlinks=False, "
                      "so a SELECTED link-to-directory (code 2) is never descended into — "
                      "exactly the regression. The F2P test test_collect_symlink_dir "
                      "(a symlinked directory must be collected) would FAIL, so this "
                      "rival does NOT resolve.",
        "rationale": "Rejected by the per-entry obligation Assert(decision == "
                     "should_descend(kinds[i], selected[i])) and the Forall "
                     "postcondition: should_descend(2, True) == True but this gives "
                     "False. If it verified => SPEC-TOO-WEAK (the spec would not sense "
                     "the regression). G-DIFF confirms model_prepatch.py fails here.",
    },
    {
        "id": "reject-overbroad-code3",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_code3,
        "refinement": "Treats a link-to-non-dir / broken link (code 3) as a directory. "
                      "Its faithful real patch would classify a broken/non-dir symlink as "
                      "descendable (e.g. entry.is_symlink() instead of entry.is_dir()), "
                      "descending into a non-directory. The walk would attempt to scandir "
                      "a non-directory target and over-collect, breaking the unchanged "
                      "P2P collection behaviour (no extra outcomes), so it does NOT resolve.",
        "rationale": "Rejected by the Forall postcondition on code 3: "
                     "should_descend(3, True) == False but this gives True. If it "
                     "verified => SPEC-TOO-WEAK on the over-descend sub-domain.",
    },
    {
        "id": "reject-drop-predicate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_drop_pred,
        "refinement": "Drops the caller recursion predicate (recurse(entry)), descending "
                      "into every directory entry regardless of selection. Its faithful "
                      "real patch removes `and recurse(entry)` from the guard, so pytest "
                      "would descend into directories the recursion predicate excludes "
                      "(e.g. ignored / virtualenv directories). The P2P tests "
                      "test_ignored_certain_directories / test_ignored_virtualenvs would "
                      "FAIL, so it does NOT resolve.",
        "rationale": "Rejected by the Forall postcondition wherever resolves_to_dir(k) "
                     "is True but selected[i] is False: should_descend gives False, this "
                     "gives True. If it verified => SPEC-TOO-WEAK (the predicate conjunct "
                     "would be unconstrained).",
    },
    {
        "id": "reject-partial-domain-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_first,
        "refinement": "Correct on every entry except index 0, which is forced to a "
                      "non-descend. A faithful real patch that special-cases the first "
                      "sorted entry would skip a selected directory that happens to sort "
                      "first, mis-collecting on any tree whose first sorted entry is a "
                      "descendable directory — diverging from the gold walk, so it does "
                      "NOT resolve in general.",
        "rationale": "Rejected by the Forall postcondition at i == 0: when "
                     "should_descend(kinds[0], selected[0]) is True this gives False. A "
                     "partial-domain rival that pins all-but-the-first index must reject "
                     "(else SPEC-TOO-WEAK on the index-0 sub-domain).",
    },
    {
        "id": "reject-constant-false",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rej_const,
        "refinement": "Never descends. Its faithful real patch is `if False:` — pytest "
                      "would never recurse into ANY subdirectory, collecting nothing past "
                      "the top level; essentially every collection test (incl. the F2P) "
                      "would FAIL, so it does NOT resolve. (Cheap supporting near-miss; "
                      "still carries a real refinement.)",
        "rationale": "Rejected by the Forall postcondition on any descendable selected "
                     "entry: should_descend == True but this gives False.",
    },
]


# No @ContractOnly axioms in this bundle (axioms: [] in meta.json). The
# "resolves to a directory" classification is an A-reference deep model
# (resolves_to_dir), validated == the real os.DirEntry.is_dir() out-of-band by
# axiom_check.py / G-AX, NOT consumed as an axiom in the proof. The PBT axiom
# lane (which re-runs a @ContractOnly callee in Docker against an Ensures) does
# not apply: there is no consumed axiom Ensures to re-check, and the A-reference
# soundness is already the dedicated G-AX gate. See 'assessment'.
AXIOM_TESTS = []
