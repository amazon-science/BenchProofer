# properties.py — PBT falsification battery for sympy__sympy-16766.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by region-surgery: ONLY text
# strictly inside the `# impl-start` / `# impl-end` region of print_indexed is
# edited (the frozen spec — pre/post-conditions, the @Pure helpers join_sep /
# render_indexed / sep / empty_seq, the signature — is never touched), so
# same_spec is guaranteed. Spec cases are checked by Nagini verify + same_spec.
#
# Defended surface (from model.py / refinement.md / mapping.md):
#   print_indexed(name: List[int], index_renderings: List[PSeq[int]]) -> PSeq[int]
#   Requires Acc(list_pred(name), 1/2)            <-- READ-ONLY input
#   Requires Acc(list_pred(index_renderings), 1/2)<-- READ-ONLY input
#   Requires len(index_renderings) >= 1
#   Ensures  Acc(list_pred(name), 1/2)
#   Ensures  Acc(list_pred(index_renderings), 1/2)
#   Ensures  Result() == render_indexed(ToSeq(name), ToSeq(index_renderings))
#
# LOAD-BEARING clause: Result() == render_indexed(ToSeq(name), ToSeq(index)).
# render_indexed = name + '[' + join_sep(idx) + ']' and join_sep = the ', '-joined
# (U+002C U+0020) concatenation, none before the first / after the last index.
# This is a GROUNDED oracle: render_indexed / join_sep are fully-unfolded @Pure
# functions of the actual inputs (not an opaque answer-key), so there is no
# "wrong echo" — the cheapest honest impl literally returns the oracle and is
# CORRECT (pos-control-oracle-direct). See 'assessment' in the structured return.
#
# F2P ground truth: test_PythonCodePrinter asserts prntr.doprint(p[0, 1]) ==
# 'p[0, 1]' (carrier 'p', two indices '0' and '1', ', ' separator, '[' ']'
# brackets, NO surrounding text). The discriminators are exactly: the ', '
# separator, the '[' ']' brackets, and the absence of surrounding text — each is
# attacked below with a rival whose faithful real patch would NOT resolve the F2P.

from pathlib import Path

INSTANCE = "sympy__sympy-16766"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()

# The exact impl region of the frozen model (gold backward-loop materialization
# of the front-recursive join_sep). All swaps target text strictly inside it.
_GOLD_IMPL = (
    "    # impl-start\n"
    "    nm = ToSeq(name)                  # type: PSeq[int]\n"
    "    idx = ToSeq(index_renderings)     # type: PSeq[PSeq[int]]\n"
    "    n = len(index_renderings)\n"
    "    joined = empty_seq()              # type: PSeq[int]\n"
    "    i = n\n"
    "    while i > 0:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(name), 1 / 2))\n"
    "        Invariant(Acc(list_pred(index_renderings), 1 / 2))\n"
    "        Invariant(nm == ToSeq(name))\n"
    "        Invariant(idx == ToSeq(index_renderings))\n"
    "        Invariant(n == len(index_renderings))\n"
    "        Invariant(n >= 1)\n"
    "        Invariant(0 <= i and i <= n)\n"
    "        Invariant(joined == join_sep(idx.drop(i)))\n"
    "        Invariant(MustTerminate(i + 1))\n"
    "        # invariants-end\n"
    "        e = idx[i - 1]\n"
    "        Assert(idx.drop(i - 1)[0] == e)\n"
    "        Assert(idx.drop(i - 1).drop(1) == idx.drop(i))\n"
    "        if i == n:\n"
    "            joined = e\n"
    "        else:\n"
    "            joined = e + sep() + joined\n"
    "        i = i - 1\n"
    "    return nm + PSeq(91) + joined + PSeq(93)\n"
    "    # impl-end"
)

assert _GOLD_IMPL in _BASE, "impl region drift vs model.py (update _GOLD_IMPL)"
assert _BASE.count(_GOLD_IMPL) == 1, "impl region not unique in model.py"


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _impl(new_impl_region):
    """Replace the whole gold impl region with `new_impl_region` (must keep the
    `# impl-start` / `# impl-end` markers)."""
    return _swap(_BASE, _GOLD_IMPL, new_impl_region)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness / admissibility) — MUST verify.
# ---------------------------------------------------------------------------

# (1) Cheapest honest impl: directly return the grounded oracle. Because
# render_indexed is a fully-unfolded @Pure function of the inputs (not an opaque
# answer key), returning it is CORRECT, not a hollow echo. If this did NOT verify
# the spec would be SPEC-TOO-STRONG (its own postcondition unsatisfiable by the
# witness it names).
_IMPL_ORACLE_DIRECT = (
    "    # impl-start\n"
    "    return render_indexed(ToSeq(name), ToSeq(index_renderings))\n"
    "    # impl-end"
)

# (2) Structurally-different correct impl: backward loop preserved (so no
# forward-append-against-a-front-recursive-fold proof gap), but the per-step
# branch is REORDERED (the `i < n` general case first, the `i == n` base case in
# the else). Every gold invariant and framing Assert is KEPT verbatim, so the
# gold proof remains valid; only the executable branch shape differs. MUST verify
# (else SPEC-TOO-STRONG against a faithful different shape).
_IMPL_BRANCH_REORDER = _GOLD_IMPL.replace(
    "        if i == n:\n"
    "            joined = e\n"
    "        else:\n"
    "            joined = e + sep() + joined\n",
    "        if i < n:\n"
    "            joined = e + sep() + joined\n"
    "        else:\n"
    "            joined = e\n",
)
assert _IMPL_BRANCH_REORDER != _GOLD_IMPL

# (3) Admissibility: the gold impl verbatim plus a benign Assert that the
# in-domain shape (n >= 1, single-index base case reachable) is admitted by the
# precondition. Confirms Requires(len(index_renderings) >= 1) accepts a normal
# F2P-shaped input (an Indexed always has >= 1 index) — else PRECOND-TOO-STRONG.
_IMPL_ADMISS = _GOLD_IMPL.replace(
    "    n = len(index_renderings)\n",
    "    n = len(index_renderings)\n"
    "    Assert(n >= 1)            # precondition admits the in-domain n>=1 input\n",
)
assert _IMPL_ADMISS != _GOLD_IMPL


# ---------------------------------------------------------------------------
# REJECT cases (uniqueness + frame-mutation) — MUST NOT verify.
# ---------------------------------------------------------------------------

# (4) FRAME-MUTATION on `name` (MANDATORY: name is Acc(list_pred(name), 1/2),
# read-only). The rival WRITES to the read-only carrier-name list before
# assembling. Keeps every gold invariant/Assert and the gold return, so the
# rejection is attributable to the write needing FULL list_pred(name) permission
# we do not hold (we hold 1/2). expect=reject for INSUFFICIENT PERMISSION.
_IMPL_FRAME_MUT_NAME = _GOLD_IMPL.replace(
    "    nm = ToSeq(name)                  # type: PSeq[int]\n",
    "    nm = ToSeq(name)                  # type: PSeq[int]\n"
    "    name.append(91)                   # WRITE to read-only input (1/2 perm)\n",
)
assert _IMPL_FRAME_MUT_NAME != _GOLD_IMPL

# (5) FRAME-MUTATION on `index_renderings` (also Acc(..., 1/2), read-only). The
# rival appends to the read-only renderings list. Same gold proof obligations
# kept; rejection is the missing FULL list_pred(index_renderings) permission.
_IMPL_FRAME_MUT_INDEX = _GOLD_IMPL.replace(
    "    n = len(index_renderings)\n",
    "    n = len(index_renderings)\n"
    "    index_renderings.append(empty_seq())  # WRITE to read-only input (1/2 perm)\n",
)
assert _IMPL_FRAME_MUT_INDEX != _GOLD_IMPL

# (6) DISCRIMINATOR: wrong separator (',' without the U+0020 space). The loop
# builds `joined` with PSeq(44) instead of sep()==PSeq(44,32), so the in-loop
# invariant joined == join_sep(idx.drop(i)) becomes unprovable for n>=2 and the
# final equality fails. expect=reject (postcondition / separator discriminator).
_IMPL_WRONG_SEP = _GOLD_IMPL.replace(
    "            joined = e + sep() + joined\n",
    "            joined = e + PSeq(44) + joined\n",
)
assert _IMPL_WRONG_SEP != _GOLD_IMPL

# (7) DISCRIMINATOR: parentheses instead of brackets. Loop + invariants kept
# valid (joined is built correctly); ONLY the final return uses PSeq(40)/PSeq(41)
# ('(' / ')') instead of PSeq(91)/PSeq(93) ('[' / ']'). The rejection is cleanly
# attributable to Ensures(Result() == render_indexed(...)) which pins '['/']'.
_IMPL_PAREN = _GOLD_IMPL.replace(
    "    return nm + PSeq(91) + joined + PSeq(93)\n",
    "    return nm + PSeq(40) + joined + PSeq(41)\n",
)
assert _IMPL_PAREN != _GOLD_IMPL

# (8) DISCRIMINATOR / prepatch-class: surrounding text. Loop + invariants kept
# valid; ONLY the final return PREPENDS PSeq(35) ('#') — the same shape as the
# pre-patch unsupported-node annotation fallback. Rejection is on the
# "no other surrounding text" clause of the postcondition.
_IMPL_PREFIX = _GOLD_IMPL.replace(
    "    return nm + PSeq(91) + joined + PSeq(93)\n",
    "    return PSeq(35) + nm + PSeq(91) + joined + PSeq(93)\n",
)
assert _IMPL_PREFIX != _GOLD_IMPL

# (9) PARTIAL-DOMAIN: correct on the multi-index F2P input (n>=2) but WRONG on
# the single-index sub-domain (n==1). The loop still builds the correct `joined`
# (invariant proof intact); only the final return special-cases n==1 to OMIT the
# brackets. For n==2 (the literal F2P value p[0,1]) it is identical to gold; for
# n==1 it returns name+idx0 with no brackets. expect=reject (the postcondition
# pins brackets for ALL n>=1, the spec's whole admitted domain).
_IMPL_PARTIAL_DOMAIN = _GOLD_IMPL.replace(
    "    return nm + PSeq(91) + joined + PSeq(93)\n",
    "    if n == 1:\n"
    "        return nm + joined          # single-index: brackets dropped (WRONG)\n"
    "    return nm + PSeq(91) + joined + PSeq(93)\n",
)
assert _IMPL_PARTIAL_DOMAIN != _GOLD_IMPL


SPEC_TESTS = [
    {
        "id": "pos-control-oracle-direct",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_IMPL_ORACLE_DIRECT),
        "rationale": (
            "Cheapest honest impl: directly return the grounded oracle "
            "render_indexed(ToSeq(name), ToSeq(index_renderings)). The oracle is a "
            "fully-unfolded @Pure function of the inputs (not an opaque answer key), "
            "so this is CORRECT, not a hollow echo. If it failed to verify the spec "
            "would be SPEC-TOO-STRONG (unsatisfiable by the witness it names)."
        ),
    },
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_IMPL_BRANCH_REORDER),
        "rationale": (
            "Structurally-different but correct: same backward loop matched to the "
            "front-recursive join_sep, every gold invariant + framing Assert kept "
            "verbatim, only the per-step branch order swapped (i<n general case "
            "first). Avoids the forward-append-vs-front-recursive-fold proof gap. "
            "Must verify, else SPEC-TOO-STRONG against a faithful different shape."
        ),
    },
    {
        "id": "admiss-in-domain",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_IMPL_ADMISS),
        "rationale": (
            "Gold impl plus Assert(n >= 1): confirms Requires(len(index_renderings) "
            ">= 1) admits a normal F2P-shaped input (an Indexed always carries >= 1 "
            "index). Must verify, else PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mut-name-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_FRAME_MUT_NAME),
        "refinement": (
            "The gold patch _print_Indexed only READS str(base); it never mutates "
            "the carrier name. A faithful real patch that wrote into the printer's "
            "input would corrupt printer/AST state and is not the gold behaviour — it "
            "would not resolve the F2P (and would break P2P printer tests). The "
            "abstraction here is a list write that the value postcondition cannot "
            "even see; only the permission system catches it."
        ),
        "rationale": (
            "name is Acc(list_pred(name), 1/2) (read-only). The inserted "
            "name.append(91) needs FULL list_pred(name) permission, which the "
            "function does not hold. Rejected for INSUFFICIENT PERMISSION (the "
            "frame condition), NOT a value mismatch — gold invariants/return kept "
            "verbatim so the rejection is attributable to the write."
        ),
    },
    {
        "id": "frame-mut-index-append",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_FRAME_MUT_INDEX),
        "refinement": (
            "The gold patch reads [self._print(ind) for ind in index] and joins it; "
            "it never appends to that list. A real patch mutating the renderings list "
            "would change the rendered index set, diverging from 'p[0, 1]' and not "
            "resolving the F2P. The value abstraction cannot observe the append; only "
            "the half-permission frame condition rejects it."
        ),
        "rationale": (
            "index_renderings is Acc(list_pred(index_renderings), 1/2) (read-only). "
            "The inserted index_renderings.append(empty_seq()) needs FULL permission. "
            "Rejected for INSUFFICIENT PERMISSION (frame condition)."
        ),
    },
    {
        "id": "rival-wrong-separator",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_WRONG_SEP),
        "refinement": (
            "This is the canonical wrong real patch: ',' .join(...) (PSeq(44), no "
            "U+0020 space) instead of ', '.join(...). It renders p[0,1] not "
            "'p[0, 1]', so the F2P assertion prntr.doprint(p[0, 1]) == 'p[0, 1]' "
            "FAILS — it would not resolve."
        ),
        "rationale": (
            "Building joined with PSeq(44) instead of sep()==PSeq(44,32) breaks the "
            "loop invariant joined == join_sep(idx.drop(i)) for n>=2 and the final "
            "Result() == render_indexed(...) equality. Rejected on the join_sep "
            "(', ' separator) clause of the postcondition."
        ),
    },
    {
        "id": "rival-paren-not-bracket",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_PAREN),
        "refinement": (
            "A real patch using '{}({})'.format(...) (parentheses) renders p(0, 1) "
            "not 'p[0, 1]'. The F2P assertion fails — it would not resolve."
        ),
        "rationale": (
            "Loop + invariants build joined correctly; only the final return uses "
            "PSeq(40)/PSeq(41) ('('/')') instead of PSeq(91)/PSeq(93) ('['/']'). "
            "Rejected cleanly on Ensures(Result() == render_indexed(...)) which pins "
            "the '['/']' brackets."
        ),
    },
    {
        "id": "rival-surrounding-prefix",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_PREFIX),
        "refinement": (
            "Prepending text is exactly the PRE-PATCH unsupported-node fallback "
            "behaviour (model_prepatch.py prepends '  # Not supported in Python:\\n  "
            "# Indexed\\n'). Any leading content makes doprint(p[0, 1]) != 'p[0, 1]' "
            "— the pre-patch state the gold repairs; it would not resolve."
        ),
        "rationale": (
            "Loop + invariants intact; the final return PREPENDS PSeq(35) ('#'). "
            "Rejected on the postcondition's 'no other surrounding text' guarantee "
            "(Result() must equal render_indexed exactly, which has no prefix)."
        ),
    },
    {
        "id": "rival-partial-domain-single-index",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_IMPL_PARTIAL_DOMAIN),
        "refinement": (
            "Correct on the literal F2P value p[0,1] (n=2: identical to gold) but on "
            "the single-index sub-domain (n==1) it OMITS the brackets, rendering p0 "
            "for p[0] instead of 'p[0]'. A real patch that special-cased single "
            "indices this way passes the one F2P value but produces wrong source for "
            "any single-index Indexed, contradicting the printer contract the spec "
            "fixes for ALL n>=1; it is not the gold and would regress single-index "
            "rendering."
        ),
        "rationale": (
            "The loop builds joined correctly (invariant proof intact); only the "
            "final return special-cases n==1 to drop PSeq(91)/PSeq(93). The "
            "postcondition pins render_indexed = name + '[' + join + ']' for the "
            "WHOLE admitted domain (len >= 1), so the n==1 path fails the equality. "
            "Rejected on the brackets clause over the precondition's full domain."
        ),
    },
]

# No @ContractOnly axioms and no A-reference deep models in this bundle (meta.json
# axioms == [], deep_model_references == [], G-AX vacuous, axiom_check.py absent).
# The only callees str(base) and self._print(ind) are UNCHANGED by the gold patch
# and abstracted as the input carriers name / index_renderings, so there is no
# real callee to execute in-container. Axiom lane is N/A.
AXIOM_TESTS = []
