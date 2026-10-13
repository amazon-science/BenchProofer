# properties.py — PBT falsification battery for sympy__sympy-15345.
#
# NOT a Nagini module; a record of adversarially-reasoned cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Each SPEC_TESTS case is
# a full model.py variant built by region-surgery: ONLY text inside the
# # impl-start / # impl-end region is swapped, so the frozen spec (axioms / pure /
# pre- / post-conditions, incl. the nested invariants markers' surrounding
# structure) is byte-for-byte preserved and `markers.same_spec` holds by
# construction. The runner checks each variant with the real Nagini verifier on
# the host: expect="verify" passes iff (same_spec AND verifies); expect="reject"
# passes iff (same_spec AND does NOT verify).
#
# Defended surface of this instance
# ---------------------------------
# print_lattice_call(name: PSeq[int], operands: PSeq[PSeq[int]]) -> PSeq[int]
#   Requires: len(operands) > 0; MustTerminate(2) — a total-correctness
#       obligation: a rival that diverges before returning (infinite loop)
#       would satisfy every value Ensures vacuously; the obligation system
#       rejects any loop lacking a decreasing termination measure. The gold
#       fold discharges it with Invariant(MustTerminate(i)).
#   Ensures (load-bearing): Result() == rendered(name, operands)
#       where rendered(name, ops) = name + '[' + joined(ops) + ']' and
#       joined is the front-recursive ", "-join (no trailing separator).
#   plus three pin clauses: len(Result()) > len(name);
#       Result()[len(name)] == lbracket() (== 91, '[');
#       Result()[len(Result())-1] == rbracket() (== 93, ']');
#       Result().take(len(name)) == name.
#
# Both inputs are PURE PSeq values (carry no heap permission, immutable in
# Nagini). There is therefore NO Acc(x,1/2) read-only heap input and the
# frame-mutation class is N/A — see 'assessment' in the returned verdict. The
# oracle `rendered` is GROUNDED (fully unfolded as a function of the inputs), not
# an opaque answer-key, so there is no WRONG ungrounded echo to build; the
# echo-equivalent is the honest cheapest-impl positive control `pos-cheapest`.
# No @ContractOnly axiom is consumed (axioms region empty), so AXIOM_TESTS = [].
from pathlib import Path

INSTANCE = "sympy__sympy-15345"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not in model.py")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen gold impl body (everything between the markers, exclusive). Used as
# the anchor for region-surgery: every variant replaces exactly this block.
_GOLD_IMPL = (
    "    # body := the \", \"-joined operand list (front-recursive fold, built back\n"
    "    # to front so each step unfolds `joined` once).\n"
    "    body = PSeq(0).take(0)  # type: PSeq[int]\n"
    "    i = len(operands)\n"
    "    while i > 0:\n"
    "        # invariants-start\n"
    "        Invariant(0 <= i and i <= len(operands))\n"
    "        Invariant(body == joined(operands.drop(i)))\n"
    "        # The loop consumes the termination obligation: i is the strictly\n"
    "        # decreasing, bounded-below measure.\n"
    "        Invariant(MustTerminate(i))\n"
    "        # invariants-end\n"
    "        # Bridge the front-recursive unfold of `joined` over `operands.drop(i-1)`:\n"
    "        # its head is operands[i-1] and its tail is operands.drop(i).\n"
    "        Assert(operands.drop(i - 1)[0] == operands[i - 1])\n"
    "        Assert(operands.drop(i - 1).drop(1) == operands.drop(i))\n"
    "        if i == len(operands):\n"
    "            # last operand: a single-element tail, no trailing separator.\n"
    "            Assert(len(operands.drop(i - 1)) == 1)\n"
    "            body = operands[i - 1]\n"
    "        else:\n"
    "            # at least two operands remain, so `joined` unfolds once.\n"
    "            Assert(len(operands.drop(i - 1)) >= 2)\n"
    "            body = operands[i - 1] + sep() + body\n"
    "        i = i - 1\n"
    "    result = name + PSeq(lbracket()) + body + PSeq(rbracket())  # type: PSeq[int]\n"
    "    return result\n"
)


def _impl(new_body: str) -> str:
    """Build a full model.py variant by replacing ONLY the gold impl block."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness / admissibility) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-cheapest: the honest grounded-oracle impl. `rendered` is a function of the
# inputs (not an opaque answer-key); returning it directly IS doing the work, so
# this is the cheapest correct implementation, not an ungrounded echo. If it
# fails to verify the spec is SPEC-TOO-STRONG (rejects a correct output).
_POS_CHEAPEST = (
    "    # Cheapest correct impl: return the grounded oracle directly. `rendered`\n"
    "    # is fully a function of the inputs, so this does the work, not an echo.\n"
    "    out = rendered(name, operands)  # type: PSeq[int]\n"
    "    return out\n"
)

# pos-branch-reorder: a STRUCTURALLY-DIFFERENT but correct impl. Keeps the gold
# back-to-front fold AND every framing assert/invariant the proof needs (so it
# does NOT introduce a forward-append-against-front-recursive-fold proof gap,
# per PBT_PLAN §5a.3). The only change is reordering the two branches: test the
# `i < len(operands)` (separator) case first via an early `if`, and fold the
# single-element tail in the `else`. Same values produced, gold proof intact.
_POS_REORDER = (
    "    # Structurally different (branches reordered) but identical values; keeps\n"
    "    # the gold back-to-front fold and every framing assert/invariant.\n"
    "    body = PSeq(0).take(0)  # type: PSeq[int]\n"
    "    i = len(operands)\n"
    "    while i > 0:\n"
    "        # invariants-start\n"
    "        Invariant(0 <= i and i <= len(operands))\n"
    "        Invariant(body == joined(operands.drop(i)))\n"
    "        # The loop consumes the termination obligation: i is the strictly\n"
    "        # decreasing, bounded-below measure.\n"
    "        Invariant(MustTerminate(i))\n"
    "        # invariants-end\n"
    "        Assert(operands.drop(i - 1)[0] == operands[i - 1])\n"
    "        Assert(operands.drop(i - 1).drop(1) == operands.drop(i))\n"
    "        if i < len(operands):\n"
    "            # at least two operands remain, so `joined` unfolds once.\n"
    "            Assert(len(operands.drop(i - 1)) >= 2)\n"
    "            body = operands[i - 1] + sep() + body\n"
    "        else:\n"
    "            # last operand: a single-element tail, no trailing separator.\n"
    "            Assert(len(operands.drop(i - 1)) == 1)\n"
    "            body = operands[i - 1]\n"
    "        i = i - 1\n"
    "    result = name + PSeq(lbracket()) + body + PSeq(rbracket())  # type: PSeq[int]\n"
    "    return result\n"
)

# admiss: an admissibility positive control. Keeps the gold impl verbatim but
# leads with an Assert re-deriving the precondition for the body's first step
# (the loop relies on `len(operands) > 0` to make `operands[i-1]` well-defined at
# i == len(operands)). If a normal in-domain input could not establish the
# Requires, this would fail => PRECOND-TOO-STRONG. It verifies => the precond
# admits an F2P-shaped (>= 1 operand) input.
_ADMISS = (
    "    # Admissibility: the precondition (>= 1 operand) must admit a normal\n"
    "    # F2P-shaped input. Re-derive it here; the gold fold then proceeds.\n"
    "    Assert(len(operands) > 0)\n"
    "    Assert(len(operands.drop(0)) == len(operands))\n"
    + _GOLD_IMPL
)


# ---------------------------------------------------------------------------
# UNIQUENESS RIVALS (wrong impl sharing the spec) — must REJECT.
# Each carries the refinement argument that its FAITHFUL real patch would NOT
# resolve the F2P (test_Function asserts mcode(Max(x,y,z)*Min(y,z)) ==
# "Max[x, y, z]*Min[y, z]"; the issue demands Max[...] not Max(...)).
# ---------------------------------------------------------------------------

# weak-round-parens: the canonical discriminating delta (== model_prepatch.py).
# Wraps the SAME ", "-joined body in ROUND parens. This is exactly the pre-fix
# behaviour the gold patch changes.
_WEAK_ROUND = _GOLD_IMPL.replace(
    "    result = name + PSeq(lbracket()) + body + PSeq(rbracket())  # type: PSeq[int]\n",
    "    result = name + PSeq(40) + body + PSeq(41)  # type: PSeq[int]\n",
)

# weak-trailing-sep: emit a trailing ", " after the last operand (seed `body`
# with a separator before the back-to-front fold). Wrong: a trailing separator.
_WEAK_TRAILING = _GOLD_IMPL.replace(
    "    body = PSeq(0).take(0)  # type: PSeq[int]\n",
    "    body = sep()  # type: PSeq[int]\n",
).replace(
    "        Invariant(body == joined(operands.drop(i)))\n",
    "        Invariant(body == joined(operands.drop(i)) + sep())\n",
)

# weak-comma-only: use a bare comma (44) as the separator instead of ", "
# (44, 32). Produces "Max[x,y,z]" (no spaces).
_WEAK_COMMA = _GOLD_IMPL.replace(
    "            body = operands[i - 1] + sep() + body\n",
    "            body = operands[i - 1] + PSeq(44) + body\n",
)

# weak-drop-first: drop the first operand entirely. Correct only when there is
# exactly one operand IS WRONG too (body becomes empty); for >= 2 operands it
# omits operands[0]. A partial-domain attack: most-but-not-all inputs diverge.
_WEAK_DROP_FIRST = _GOLD_IMPL.replace(
    "    i = len(operands)\n",
    "    i = len(operands)\n"
    "    # partial-domain rival: skip the very first operand entirely.\n",
).replace(
    "    while i > 0:\n",
    "    while i > 1:\n",
)

# weak-reverse: build the body in REVERSED operand order (front-to-back append
# while iterating front, but appending each operand after the running body),
# producing joined of the reversed operand list. Order is observable.
_WEAK_REVERSE = (
    "    # Reversed operand order: appends operands as encountered front-to-back\n"
    "    # but to the END, yielding the reversed join. Order is observable.\n"
    "    body = PSeq(0).take(0)  # type: PSeq[int]\n"
    "    i = 0\n"
    "    while i < len(operands):\n"
    "        # invariants-start\n"
    "        Invariant(0 <= i and i <= len(operands))\n"
    "        # Discharge the termination obligation identically to gold, so the\n"
    "        # reject stays on the SPEC (the value clause), not an obligation leak.\n"
    "        Invariant(MustTerminate(len(operands) - i + 1))\n"
    "        # invariants-end\n"
    "        if i == 0:\n"
    "            body = operands[i]\n"
    "        else:\n"
    "            body = operands[i] + sep() + body\n"
    "        i = i + 1\n"
    "    result = name + PSeq(lbracket()) + body + PSeq(rbracket())  # type: PSeq[int]\n"
    "    return result\n"
)

# weak-nonterminating: an impl that never returns. It spins forever (while
# 0 <= i with i increasing), so every value postcondition is satisfiable only
# vacuously: no execution reaches the return. This is the exact spec-too-weak
# class the G-PANEL-1 auditor exploited before the MustTerminate obligation was
# added (an echo/diverging same-spec impl that verified against the value-only
# spec). Under Requires(MustTerminate(2)) the loop takes no termination
# obligation and has no decreasing measure, so Nagini's obligation system MUST
# reject it. The invariants are relaxed to what the spinning loop maintains —
# the reject must come from the obligation system, not a broken proof.
_WEAK_NONTERM = (
    "    # Vacuous non-termination: spin forever, never deliver the text.\n"
    "    body = PSeq(0).take(0)  # type: PSeq[int]\n"
    "    i = 0\n"
    "    while 0 <= i:\n"
    "        # invariants-start\n"
    "        Invariant(0 <= i)\n"
    "        # invariants-end\n"
    "        i = i + 1\n"
    "    result = name + PSeq(lbracket()) + body + PSeq(rbracket())  # type: PSeq[int]\n"
    "    return result\n"
)


SPEC_TESTS = [
    {
        "id": "pos-cheapest",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_CHEAPEST),
        "rationale": "Honest grounded-oracle cheapest impl: returns rendered(name, "
                     "operands) directly. rendered is a function of the inputs (not "
                     "an opaque answer-key), so this DOES the work. Must verify, "
                     "else the postcondition Result()==rendered is SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": "Structurally different (the two fold branches are reordered: "
                     "the separator/unfold case is tested first via `i < "
                     "len(operands)`) yet produces identical values and keeps every "
                     "gold framing Assert/Invariant. A faithful correct impl must "
                     "verify, else SPEC-TOO-STRONG. Avoids the forward-append-vs-"
                     "front-recursive-fold proof gap (PBT_PLAN 5a.3) by retaining "
                     "the back-to-front fold.",
    },
    {
        "id": "admiss-ge1-operand",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": "Re-derives the precondition (len(operands) > 0) at entry and "
                     "confirms drop(0) is the identity before the gold fold. "
                     "Verifies => the precondition admits a normal F2P-shaped input "
                     "(>= 1 operand, e.g. Max(x,y,z)); else PRECOND-TOO-STRONG.",
    },
    {
        "id": "weak-round-parens",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ROUND),
        "refinement": "This is the pre-fix behaviour verbatim (== model_prepatch.py): "
                      "wraps the body in ROUND parens, so mcode(Max(x,y,z)) prints "
                      "'Max(x, y, z)'. The F2P test_Function asserts "
                      "mcode(Max(x,y,z)*Min(y,z)) == 'Max[x, y, z]*Min[y, z]' and the "
                      "issue demands 'Max[...]'; round parens are exactly the bug, so "
                      "the faithful real patch would NOT resolve.",
        "rationale": "Rejected by the postcondition Result()==rendered(name,operands) "
                     "(uses '[' = 91 / ']' = 93) AND by the pin clauses "
                     "Result()[len(name)]==lbracket() ('(' = 40 != 91) and "
                     "Result()[-1]==rbracket() (')' = 41 != 93).",
    },
    {
        "id": "weak-trailing-sep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_TRAILING),
        "refinement": "Seeds the body with a separator, so a trailing ', ' is emitted "
                      "after the last operand: mcode(Max(x,y,z)) prints 'Max[x, y, z, ]'. "
                      "The F2P asserts the exact 'Max[x, y, z]' with NO trailing "
                      "separator, so a faithful real patch with this behaviour would "
                      "NOT resolve.",
        "rationale": "Rejected by Result()==rendered(name,operands): rendered/joined "
                     "place exactly one sep() between adjacent pairs and none after "
                     "the last operand; the extra trailing sep() makes Result longer "
                     "than rendered.",
    },
    {
        "id": "weak-comma-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_COMMA),
        "refinement": "Uses a bare comma (44) as the separator instead of ', ' "
                      "(44, 32), so mcode(Max(x,y,z)) prints 'Max[x,y,z]' with no "
                      "spaces. The F2P asserts the exact 'Max[x, y, z]' WITH spaces "
                      "(== Python's ', '.join), so this faithful patch would NOT "
                      "resolve. (Note the issue text's 'Max[x,2]' is illustrative; "
                      "the gold/F2P oracle is the ', '-spaced form.)",
        "rationale": "Rejected by Result()==rendered(name,operands): joined uses "
                     "sep()==PSeq(44,32); a comma-only separator drops the 32 (space) "
                     "code point between adjacent operands, so Result != rendered.",
    },
    {
        "id": "weak-drop-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DROP_FIRST),
        "refinement": "Partial-domain: the loop guard `i > 1` skips folding the very "
                      "first operand, so mcode(Max(x,y,z)) prints 'Max[y, z]' (drops "
                      "x). The F2P asserts 'Max[x, y, z]' (all operands, in order), so "
                      "a faithful patch dropping the first operand would NOT resolve.",
        "rationale": "Rejected by Result()==rendered(name,operands) AND by the loop "
                     "invariant body==joined(operands.drop(i)) which cannot be "
                     "re-established at i==1 when the first operand is never folded "
                     "in; the omitted operands[0] makes Result != rendered.",
    },
    {
        "id": "weak-nonterminating",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NONTERM),
        "refinement": "The rival never returns: it spins in an unbounded loop, so "
                      "every value postcondition holds only vacuously and no rendered "
                      "text is ever delivered. Its faithful real patch is a printer "
                      "method that hangs — mathematica_code(Max(x,y,z)) would never "
                      "return, every F2P test times out/fails, so it does NOT resolve. "
                      "This is the attack class the G-PANEL-1 auditor exploited before "
                      "the MustTerminate obligation was added.",
        "rationale": "MUST reject via the OBLIGATION system: the renderer's "
                     "Requires(MustTerminate(2)) forces every loop on the path to the "
                     "return to carry a decreasing termination measure; the spinning "
                     "loop has none, so Nagini rejects it (obligation leak). "
                     "Rejection source: the termination obligation, not a value "
                     "clause — demonstrating the spec no longer admits vacuous "
                     "divergence.",
    },
    {
        "id": "weak-reverse",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_REVERSE),
        "refinement": "Builds the body in REVERSED operand order, so mcode(Max(x,y,z)) "
                      "prints 'Max[z, y, x]'. The operand order is fixed by expr.args "
                      "(canonicalised upstream, identical pre/post-fix) and the F2P "
                      "asserts 'Max[x, y, z]' in that order; a faithful patch that "
                      "reorders operands would NOT resolve.",
        "rationale": "Rejected by Result()==rendered(name,operands): rendered/joined "
                     "concatenate operands left-to-right in their given order; the "
                     "reversed join != joined(operands) for len >= 2.",
    },
]


# No @ContractOnly axiom is consumed (the axioms region is empty) and the only
# A-reference deep model (joined/rendered == Python's ", ".join / "%s[%s]"
# formatting) involves NO repo-specific callee — it is plain Python, already
# exhaustively validated on the host by axiom_check.py (G-AX: 12 boundary lists x
# 5 names + 3 F2P witnesses + 20000 fuzz, 0 mismatch). There is no Docker
# real-callee obligation to discharge, so the axiom lane is vacuous.
AXIOM_TESTS = []
