"""properties.py — PBT falsification manifest for sphinx-doc__sphinx-10323.

NOT a Nagini module: a record of adversarial cases the runner
(`swebench_nagini.pbt`) executes. See the battery-authoring brief (esp. §2 "four
falsification checks" and §4a "Adversarial, NOT mechanical").

This battery is reasoned from THIS spec's defended surface, not stamped out by a
corruption template. The function under spec is

    assemble(included: PSeq[PSeq[int]], lead: PSeq[int], trail: PSeq[int],
             n: int) -> PSeq[PSeq[int]]

i.e. the gold patch's filter-pipeline reorder in
`LiteralIncludeReader.read()` (move `dedent_filter` BEFORE
`prepend_filter`/`append_filter`), so the per-line left-margin trim reaches the
included text ONLY, and the author-supplied leading/trailing lines are emitted
VERBATIM. A "line" is its content `PSeq[int]` (the trailing newline is the
implicit separator); the per-line trim of width n is `PSeq.drop(n)`.

Load-bearing contract (frozen spec view):

    Requires(n >= 0)                                # the FULL trim-width domain
    Requires(MustTerminate(2))                      # total correctness: no vacuous
                                                    # proof by divergence
    # NOTHING is required of lead/trail: the empty (== absent) author line is
    # in-domain, and so is n == 0.
    Ensures(Result() == (emit(lead) + trim_block(included, n)) + emit(trail))  # THE pin
    Ensures(len(Result()) == len(emit(lead)) + len(included) + len(emit(trail)))
    Ensures(Implies(len(lead) == 0 and len(trail) == 0,
                    Result() == trim_block(included, n)))   # trim UNCONDITIONAL
    Ensures(Implies(len(lead) >= 1, Result()[0] == lead))          # lead VERBATIM
    Ensures(Implies(len(lead) >= 1 and n >= 1, Result()[0] != lead.drop(n)))
    Ensures(Implies(len(trail) >= 1, Result()[len(Result()) - 1] == trail))
    Ensures(Implies(len(lead) >= 1, Forall i: 0<=i<len(included)
                    -> Result()[i + 1] == included[i].drop(n)))
    Ensures(Implies(len(lead) == 0, Forall i: 0<=i<len(included)
                    -> Result()[i] == included[i].drop(n)))

where `trim_block` is a `@Pure` front-recursive fold (each line `.drop(n)`), with
the per-element lemma `trim_block_at`, and `emit` is the `@Pure` presence rule for
ONE author line (a one-line block when the line has content, NO line when it is
empty).

What the spec defends, and the attacks it must survive:

  * NO read-only `Acc(...,1/2)` / `list_pred` input. Every input is a pure,
    immutable `PSeq` passed by value (meta.json G-HYGIENE: "no full-permission
    read-only param (pure PSeq inputs, no list_pred/Acc)"). There is no heap
    state for an impl to write through, so the FRAME-MUTATION class is N/A for
    this instance — there is no `lines[i] = ...` store that could vacuously
    discharge the pin. (Documented in 'assessment'; has_readonly_input=False.)

  * The output pin is GROUNDED in the inputs, not pinned to an answer-key
    oracle. `trim_block(included, n)` is a fully-unfolded deterministic function
    of `included` and `n` (a `@Pure` fold), `emit` is a fully-unfolded
    deterministic function of one author line, and `lead`/`trail` enter the pin
    through it directly. There is no opaque marker to echo and no executable
    materialization that would let a WRONG impl reproduce the pin without doing
    the trim+assembly. So UNGROUNDED-ORACLE has no wrong-echo here; instead
    `echo-honest` is an honest positive control proving the cheapest correct
    impl (which equates its result to the grounded pin) verifies.

  * The DOMAIN IS TOTAL in every parameter the behaviour is about. `lead` and
    `trail` may be EMPTY (== no author line supplied) and `n` may be 0. This is
    load-bearing, not cosmetic: the earlier surface of this spec demanded
    `n >= 1`, `len(lead) >= 1`, `len(trail) >= 1`, which made every
    author-line-absent state PROVABLY UNREACHABLE inside the body — so an
    implementation was free to make the whole trim stage CONDITIONAL on an
    author line being present and still verify, while the real function trims
    the included text whether or not one is. `rival-trim-only-if-lead-present`,
    `rival-trim-only-if-both-present` and `rival-no-trim-when-no-author-line`
    are exactly those implementations, and `pos-live-no-author-line` /
    `pos-live-zero-width` are the LIVENESS controls proving those states are now
    reachable rather than merely mentioned (each asserts a property that only
    holds because the branch is entered; an infeasible guard would let anything
    through — cf. the `Assert(False)` deadness idiom).

  * The DISCRIMINATING content of the patch — leading/trailing author lines are
    emitted verbatim rather than left-margin-trimmed, while the included text is
    trimmed unconditionally — lives in the primary pin
    `Result() == (emit(lead) + trim_block(included, n)) + emit(trail)` and its
    derived clauses: `Result()[0] == lead` when a lead is supplied,
    `Result()[0] != lead.drop(n)` making that verbatim-ness observable,
    `Result()[len(Result()) - 1] == trail` when a trail is supplied, the
    UNCONDITIONAL-TRIM clause
    `len(lead) == 0 and len(trail) == 0 -> Result() == trim_block(included, n)`,
    and the per-included-line clauses in BOTH author-line regimes (offset 1 when
    a lead is supplied, offset 0 when it is not). The uniqueness rivals
    therefore attack WHERE the trim is applied, WHICH lines are verbatim, and
    WHETHER the trim runs at all: the actual pre-patch bug (trim the whole
    assembled block, == model_prepatch.py), trim only the lead, swap lead/trail,
    drop the trim on the included text, a partial-domain rival correct except on
    the first included line, and the three author-line-absence rivals above.

  * The assembled block carries NO CONTENT OF ITS OWN and INVENTS NO AUTHOR
    LINE. The pin fixes the output element for element and
    `len(Result()) == len(emit(lead)) + len(included) + len(emit(trail))` fixes
    its length as a function of which author lines were actually supplied, so an
    impl that inserts a line of its own — or that emits a blank line where an
    absent author line would have gone — must be rejected.
    `rival-nonempty-fold-base` is the first: the backward fold starts from a
    ONE-ELEMENT block, so a spurious empty line lands between the trimmed
    included text and the trailing line. `rival-blank-for-absent-author-line` is
    the second: it emits the empty author line as a real (blank) line instead of
    omitting it. `rival-nonempty-fold-base` is also the BEHAVIOUR of the only
    live mutant the superseded empty-block idiom
    `PSeq(PSeq(0).take(0)).take(0)` ever produced, preserved here because the
    base expression now carries no literal for the mutation operator to reach.
    The four mutants of that idiom which G-MUT reported as survivors mutate a
    subexpression strictly inside the outer `.take(0)` and so denote the SAME
    empty block -- equivalent programs, no spec hole;
    `pos-inert-empty-base-equivalence` has Viper PROVE that instead of
    asserting it in prose.

  * NO consumed `@ContractOnly` axiom and NO A-consumed deep model whose Ensures
    is read numerically: the per-line trim is an A-REFERENCE deep model
    (`trim_block`) validated == the real `dedent_lines` callee OUT OF BAND by
    axiom_check.py / G-AX (meta.json axioms == []). The proof never consumes a
    trim axiom (it unfolds `trim_block` + the lemma). `emit` is likewise a deep
    `@Pure` definition, not an axiom. Hence AXIOM_TESTS = [] (there is no
    in-proof axiom obligation to re-run in Docker; the deep-model soundness is
    already the G-AX gate's job, run by the orchestrator in-container).

Authoring mechanics: every spec variant is built by REGION-SURGERY (`_swap`)
that edits ONLY inside `# impl-start`/`# impl-end`, so `markers.same_spec` is
guaranteed and a rejection comes from the POSTCONDITION (never a tampered spec).
The positive controls keep EVERY gold proof obligation they still need (the two
backward-fold framing asserts, the lemma-discharge loop's invariants/asserts) so
they are not proof-gap cases; only the executable shape (a named intermediate)
changes. Each `expect:"reject"` rival carries the refinement argument that its
faithful real patch would NOT resolve — either the F2P
(`test_LiteralIncludeReader_dedent_and_append_and_prepend`) or, for the
author-line-absence rivals, the P2P lane that exercises a dedent with NEITHER
`prepend` nor `append` (`test_LiteralIncludeReader_dedent`,
`test_LiteralIncludeReader_tabwidth_dedent`).
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-10323"
FLOAT_ENCODING = None  # meta.json float_encoding is null

# --- base spec (frozen) ------------------------------------------------------
_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src: str, old: str, new: str) -> str:
    """Replace exactly one occurrence of an impl-region substring; assert it
    actually matched so silent drift (model.py edited) fails loudly at load."""
    if old not in src:
        raise AssertionError(f"properties.py drift: substring not found:\n{old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"properties.py: substring not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Region landmarks — all strictly INSIDE the impl region of model.py.
# ---------------------------------------------------------------------------

# The whole gold impl body (between # impl-start and # impl-end). Used as a
# single replaceable block for the rivals that restructure control flow so that
# no stale (now-false) gold assert survives to mask the postcondition rejection.
_GOLD_IMPL = (
    "    # impl-start\n"
    "    # Margin trim first — over the included text only, and unconditionally.\n"
    "    # Build the trimmed block by a backward fold matching `trim_block`.\n"
    "    trimmed = PSeq()  # type: PSeq[PSeq[int]]\n"
    "    i = len(included)\n"
    "    while i > 0:\n"
    "        # invariants-start\n"
    "        Invariant(0 <= i and i <= len(included))\n"
    "        Invariant(trimmed == trim_block(included.drop(i), n))\n"
    "        # The loop consumes the caller's termination obligation with the\n"
    "        # strictly decreasing, bounded-below measure i, discharging\n"
    "        # MustTerminate(2) from the precondition.\n"
    "        Invariant(MustTerminate(i + 1))\n"
    "        # invariants-end\n"
    "        Assert(included.drop(i - 1)[0] == included[i - 1])\n"
    "        Assert(included.drop(i - 1).drop(1) == included.drop(i))\n"
    "        trimmed = PSeq(included[i - 1].drop(n)) + trimmed\n"
    "        i = i - 1\n"
    "    Assert(trimmed == trim_block(included, n))\n"
    "    Assert(len(trimmed) == len(included))\n"
    "    # Then the leading and the trailing line, each emitted VERBATIM (untrimmed)\n"
    "    # and only when it has content.\n"
    "    result = (emit(lead) + trimmed) + emit(trail)  # type: PSeq[PSeq[int]]\n"
    "    # Discharge the per-included-line characterization of the trim via the\n"
    "    # lemma, index by index, in both author-line regimes.\n"
    "    j = 0\n"
    "    while j < len(included):\n"
    "        # invariants-start\n"
    "        Invariant(0 <= j and j <= len(included))\n"
    "        Invariant(result == (emit(lead) + trim_block(included, n)) + emit(trail))\n"
    "        Invariant(len(trim_block(included, n)) == len(included))\n"
    "        Invariant(Implies(len(lead) >= 1, Forall(int, lambda k: (\n"
    "            Implies(0 <= k and k < j, result[k + 1] == included[k].drop(n)),\n"
    "            [[result[k + 1]]]))))\n"
    "        Invariant(Implies(len(lead) == 0, Forall(int, lambda k: (\n"
    "            Implies(0 <= k and k < j, result[k] == included[k].drop(n)),\n"
    "            [[result[k]]]))))\n"
    "        # The loop consumes the caller's termination obligation with the\n"
    "        # strictly decreasing, bounded-below measure len(included) - j,\n"
    "        # discharging MustTerminate(2) from the precondition.\n"
    "        Invariant(MustTerminate(len(included) - j + 1))\n"
    "        # invariants-end\n"
    "        Assert(trim_block_at(included, n, j))\n"
    "        Assert(trim_block(included, n)[j] == included[j].drop(n))\n"
    "        Assert(len(emit(lead)) == 0 or len(emit(lead)) == 1)\n"
    "        Assert(result[len(emit(lead)) + j] == trim_block(included, n)[j])\n"
    "        j = j + 1\n"
    "    return result\n"
    "    # impl-end"
)

# sanity: the reconstructed gold impl block must be present, exactly once.
assert _BASE.count(_GOLD_IMPL) == 1, "gold impl block landmark drift"

# The first line INSIDE the impl region — the insertion point for the liveness
# controls and the guarded rivals.
_IMPL_HEAD = (
    "    # impl-start\n"
    "    # Margin trim first — over the included text only, and unconditionally.\n"
)
assert _BASE.count(_IMPL_HEAD) == 1, "impl head landmark drift"


def _guarded(prefix: str) -> str:
    """The gold impl with `prefix` (extra statements) spliced in right after
    # impl-start, i.e. BEFORE the gold body runs."""
    return _swap(_BASE, _IMPL_HEAD, _IMPL_HEAD.replace(
        "    # impl-start\n", "    # impl-start\n" + prefix, 1))


# ===========================================================================
# POSITIVE CONTROLS (soundness / admissibility) — expect "verify"
# ===========================================================================

# (5) Structurally-different but CORRECT. The executable shape is reshaped while
# keeping the EXACT backward fold (matching the front-recursive `trim_block`)
# and EVERY gold proof obligation (the two framing asserts inside loop 1, the
# lemma-discharge loop's invariants and asserts). The two reshapes:
#   * inside loop 1 the per-line trim is bound to a NAMED local `cur` before the
#     prepend (`trimmed = PSeq(cur) + trimmed`) — value-identical to
#     `PSeq(included[i-1].drop(n)) + trimmed`, so the invariant still holds;
#   * the assembly is split via a named intermediate `head = emit(lead) + trimmed`
#     then `result = head + emit(trail)` — the SAME concatenation structure
#     `(emit(lead)+trimmed)+emit(trail)`, just bound in two steps, so the
#     lemma-discharge loop invariant `result == (emit(lead)+trim_block(...))+
#     emit(trail)` is unchanged.
# This deliberately AVOIDS a loop-direction flip (a forward-append against the
# front-recursive fold would need an f(a+b) lemma the verifier won't
# auto-discharge — PBT_PLAN §5a.3) and AVOIDS dropping any framing assert
# (PBT_PLAN §5a.2). If this fails to verify, the postcondition is over-fit to one
# statement layout => SPEC-TOO-STRONG.
_POS_REORDER_IMPL = (
    "    # impl-start\n"
    "    # Margin trim first — over the included text only, unconditionally, by a\n"
    "    # backward fold matching `trim_block` (named per-line local).\n"
    "    trimmed = PSeq(PSeq(0).take(0)).take(0)  # type: PSeq[PSeq[int]]\n"
    "    i = len(included)\n"
    "    while i > 0:\n"
    "        # invariants-start\n"
    "        Invariant(0 <= i and i <= len(included))\n"
    "        Invariant(trimmed == trim_block(included.drop(i), n))\n"
    "        # The loop consumes the caller's termination obligation with the\n"
    "        # strictly decreasing, bounded-below measure i.\n"
    "        Invariant(MustTerminate(i + 1))\n"
    "        # invariants-end\n"
    "        Assert(included.drop(i - 1)[0] == included[i - 1])\n"
    "        Assert(included.drop(i - 1).drop(1) == included.drop(i))\n"
    "        cur = included[i - 1].drop(n)  # type: PSeq[int]\n"
    "        trimmed = PSeq(cur) + trimmed\n"
    "        i = i - 1\n"
    "    Assert(trimmed == trim_block(included, n))\n"
    "    Assert(len(trimmed) == len(included))\n"
    "    # Then the leading and the trailing line, each VERBATIM (untrimmed) and\n"
    "    # only when it has content, built via a named head intermediate (same\n"
    "    # concatenation structure).\n"
    "    head = emit(lead) + trimmed  # type: PSeq[PSeq[int]]\n"
    "    result = head + emit(trail)  # type: PSeq[PSeq[int]]\n"
    "    # Discharge the per-included-line characterization of the trim via the\n"
    "    # lemma, index by index, in both author-line regimes.\n"
    "    j = 0\n"
    "    while j < len(included):\n"
    "        # invariants-start\n"
    "        Invariant(0 <= j and j <= len(included))\n"
    "        Invariant(result == (emit(lead) + trim_block(included, n)) + emit(trail))\n"
    "        Invariant(len(trim_block(included, n)) == len(included))\n"
    "        Invariant(Implies(len(lead) >= 1, Forall(int, lambda k: (\n"
    "            Implies(0 <= k and k < j, result[k + 1] == included[k].drop(n)),\n"
    "            [[result[k + 1]]]))))\n"
    "        Invariant(Implies(len(lead) == 0, Forall(int, lambda k: (\n"
    "            Implies(0 <= k and k < j, result[k] == included[k].drop(n)),\n"
    "            [[result[k]]]))))\n"
    "        # The loop consumes the caller's termination obligation with the\n"
    "        # strictly decreasing, bounded-below measure len(included) - j.\n"
    "        Invariant(MustTerminate(len(included) - j + 1))\n"
    "        # invariants-end\n"
    "        Assert(trim_block_at(included, n, j))\n"
    "        Assert(trim_block(included, n)[j] == included[j].drop(n))\n"
    "        Assert(len(emit(lead)) == 0 or len(emit(lead)) == 1)\n"
    "        Assert(result[len(emit(lead)) + j] == trim_block(included, n)[j])\n"
    "        j = j + 1\n"
    "    return result\n"
    "    # impl-end"
)
_POS_REORDER = _swap(_BASE, _GOLD_IMPL, _POS_REORDER_IMPL)

# (2 / honest positive control for the GROUNDED pin) The pin is grounded in the
# inputs (trim_block is a @Pure fold of `included`,`n`; `emit` is a @Pure
# function of one author line), so there is no opaque oracle to echo. This
# control is the gold impl with an EXTRA assertion right before the return that
# the value it built equals the grounded spec pin. It is CORRECT
# (expect="verify"); its purpose is to demonstrate there is no wrong oracle-echo
# that verifies (the result must be PRODUCED by the modeled trim+assembly, not
# equated to an opaque marker). If you could echo a wrong answer and still
# verify, this would instead be a reject case; here no such echo exists.
_ECHO_RETURN = (
    "        Assert(result[len(emit(lead)) + j] == trim_block(included, n)[j])\n"
    "        j = j + 1\n"
    "    return result\n"
)
_ECHO_RETURN_NEW = (
    "        Assert(result[len(emit(lead)) + j] == trim_block(included, n)[j])\n"
    "        j = j + 1\n"
    "    Assert(result == (emit(lead) + trim_block(included, n)) + emit(trail))\n"
    "    return result\n"
)
_ECHO_HONEST = _swap(_BASE, _ECHO_RETURN, _ECHO_RETURN_NEW)

# (6) ADMISSIBILITY. An F2P-shaped probe input — the F2P scenario shape
# `included` = 3 content lines, `lead`/`trail` non-empty, n = 2 (dedent 2,
# prepend 'class Foo:', append '# comment') — modeled with opaque code-point
# identities, PLUS the complementary P2P-shaped probe (dedent with NEITHER
# author line: both empty, n = 2) and the zero-width probe. The locally-built
# PSeq inputs must be PROVEN to satisfy the input-shape precondition, which is
# now just `n >= 0` — so all three shapes are admissible. (The MustTerminate
# conjunct is an obligation any terminating caller supplies, not an input-shape
# constraint, so it is not part of the admissibility probe; a direct self-call is
# not usable as the probe because a self-call cannot carry a strictly smaller
# termination measure.) If the asserts fail for a normal F2P or P2P input =>
# PRECOND-TOO-STRONG.
_ADMISS_HEAD_NEW = (
    "    # impl-start\n"
    "    # Admissibility: the F2P-shaped probe (3 included lines, non-empty\n"
    "    # lead/trail, n=2), the P2P-shaped probe (a dedent with NEITHER author\n"
    "    # line: both empty) and the zero-width probe must all satisfy the\n"
    "    # input-shape precondition, which is just n >= 0.\n"
    "    inc_probe = PSeq(PSeq(32, 100), PSeq(32, 112), PSeq(0).take(0))  # type: PSeq[PSeq[int]]\n"
    "    lead_probe = PSeq(99, 108)  # type: PSeq[int]\n"
    "    trail_probe = PSeq(35)  # type: PSeq[int]\n"
    "    none_probe = PSeq(0).take(0)  # type: PSeq[int]\n"
    "    n_probe = 2\n"
    "    Assert(n_probe >= 0)\n"
    "    Assert(len(lead_probe) >= 1)\n"
    "    Assert(len(trail_probe) >= 1)\n"
    "    Assert(len(none_probe) == 0)\n"
    "    Assert(len(inc_probe) == 3)\n"
    "    Assert(0 >= 0)\n"
    "    # Margin trim first — over the included text only, and unconditionally.\n"
)
_ADMISS = _swap(_BASE, _IMPL_HEAD, _ADMISS_HEAD_NEW)


# (8) LIVENESS of the author-line-ABSENT states. This is the control for the
# repair that widened the domain: it is not enough that the spec MENTIONS
# `len(lead) == 0`; that state has to be REACHABLE inside the body, or a rival's
# guard on it is dead and unconstrained (an infeasible guard verifies while
# proving nothing). Under the OLD precondition (`len(lead) >= 1` and
# `len(trail) >= 1`) `if len(lead) == 0 and len(trail) == 0: Assert(False)`
# VERIFIED — which is precisely what let the author-line-absence rivals through.
# Here the branch asserts something that is TRUE but only in that state
# (`emit(lead)` and `emit(trail)` are both empty, so the whole assembled block is
# just the trimmed included text). If this case were REJECTED the state is not
# reachable after all and the widening did not take.
_POS_LIVE_NO_AUTHOR = _guarded(
    "    if len(lead) == 0 and len(trail) == 0:\n"
    "        Assert(len(emit(lead)) == 0)\n"
    "        Assert(len(emit(trail)) == 0)\n"
    "        Assert(emit(lead) + trim_block(included, n) == trim_block(included, n))\n"
)

# (9) LIVENESS of the zero-width trim state, same argument for `n`. Under the old
# precondition (`n >= 1`) `if n == 0: Assert(False)` VERIFIED, so an
# implementation could do anything at all for a zero-width trim. Here the branch
# asserts the true-only-there property that a zero-width trim is the identity on
# every line. If REJECTED, `n == 0` is still out of domain.
_POS_LIVE_ZERO_WIDTH = _guarded(
    "    if n == 0:\n"
    "        Assert(Forall(int, lambda q: (\n"
    "            Implies(0 <= q and q < len(included), included[q].drop(0) == included[q]),\n"
    "            [[included[q].drop(0)]])))\n"
)

# (7) INERT-BASE EQUIVALENCE — the machine-checked RECORD of G-MUT's four
# surviving mutants, so the finding is not carried by prose alone.
#
# History, measured (not inferred). Against the SUPERSEDED base expression
# `trimmed = PSeq(PSeq(0).take(0)).take(0)` on model.py line 117, G-MUT reported
#
#   G-MUT=fail :: killed 14/18 (78%); survivors: ["line 117: '0' -> '-1'",
#   "line 117: '0' -> '1'", "line 117: '0' -> '-1'", "line 117: '0' -> '1'"]
#
# Five of that line's mutants were sampled. FOUR of them mutate a subexpression
# strictly INSIDE the outer `.take(0)` — `PSeq(-1)`, `PSeq(1)`, `.take(-1)`,
# `.take(1)` on the inner sequence — and `X.take(0)` is the empty sequence for
# every `X`, so all four denote the SAME empty block as the gold expression: they
# are equivalent programs, not implementations the spec wrongly admits. Each was
# re-measured on its own and verifies (`Verification successful`, 16.1s / 17.2s /
# 17.4s / 17.6s, against the gold source's 22.5s in the same environment) — i.e.
# a real Viper verdict, not a front-end refusal.
#
# This case makes the equivalence a PROOF OBLIGATION instead of a claim: the five
# Asserts equate the gold expression and all four of its mutations to the empty
# base the impl now uses, and pin `len(trimmed) == 0`. It is otherwise the gold
# impl, so it must VERIFY. Non-vacuity control (measured out of band): the same
# module with one extra `Assert(False)` appended to the block is REJECTED —
#   model.py:124:12:124:17: error: Assert might fail. Assertion False might not
#   hold.
# — so the program point is reachable and the five equalities are really
# discharged rather than trivially true under an infeasible guard.
_INERT_BASE_LINE = "    trimmed = PSeq()  # type: PSeq[PSeq[int]]\n"
_INERT_EQUIV_NEW = _INERT_BASE_LINE + (
    "    Assert(PSeq(PSeq(0).take(0)).take(0) == trimmed)\n"
    "    Assert(PSeq(PSeq(-1).take(0)).take(0) == trimmed)\n"
    "    Assert(PSeq(PSeq(1).take(0)).take(0) == trimmed)\n"
    "    Assert(PSeq(PSeq(0).take(-1)).take(0) == trimmed)\n"
    "    Assert(PSeq(PSeq(0).take(1)).take(0) == trimmed)\n"
    "    Assert(len(trimmed) == 0)\n"
)
_POS_INERT_EQUIV = _swap(_BASE, _INERT_BASE_LINE, _INERT_EQUIV_NEW)


# ===========================================================================
# UNIQUENESS RIVALS (spec-too-weak probes) — expect "reject"
# ===========================================================================

# (1) PRE-PATCH BUG (== model_prepatch.py): assemble FIRST (lead + included +
# trail) and THEN trim the WHOLE assembled block, so the author-supplied
# leading/trailing lines are trimmed too. Result() becomes
# trim_block(emit(lead)+included+emit(trail), n), whose element 0 is lead.drop(n)
# != lead. Rejected by the primary pin AND the derived
# `len(lead) >= 1 -> Result()[0] == lead` / `Result()[0] != lead.drop(n)`.
_PREPATCH_IMPL = (
    "    # impl-start\n"
    "    # PRE-PATCH order: assemble FIRST, then trim the whole assembled block, so\n"
    "    # the author-supplied leading/trailing lines are trimmed too.\n"
    "    block = (emit(lead) + included) + emit(trail)  # type: PSeq[PSeq[int]]\n"
    "    result = PSeq(PSeq(0).take(0)).take(0)  # type: PSeq[PSeq[int]]\n"
    "    i = len(block)\n"
    "    while i > 0:\n"
    "        # invariants-start\n"
    "        Invariant(0 <= i and i <= len(block))\n"
    "        Invariant(len(block) == len(emit(lead)) + len(included) + len(emit(trail)))\n"
    "        Invariant(result == trim_block(block.drop(i), n))\n"
    "        # Terminating loop (measure i): the rejection must come from the\n"
    "        # postcondition, not an obligation leak.\n"
    "        Invariant(MustTerminate(i + 1))\n"
    "        # invariants-end\n"
    "        Assert(block.drop(i - 1)[0] == block[i - 1])\n"
    "        Assert(block.drop(i - 1).drop(1) == block.drop(i))\n"
    "        result = PSeq(block[i - 1].drop(n)) + result\n"
    "        i = i - 1\n"
    "    Assert(result == trim_block(block, n))\n"
    "    return result\n"
    "    # impl-end"
)
_RIVAL_PREPATCH = _swap(_BASE, _GOLD_IMPL, _PREPATCH_IMPL)

# (3) TRIM-LEAD-ONLY — the SHARPEST discriminator for the verbatim clause.
# Everything correct except the leading line is emitted TRIMMED
# (emit(lead.drop(n))) instead of verbatim. Directly contradicts
# `len(lead) >= 1 -> Result()[0] == lead` AND `Result()[0] != lead.drop(n)`.
_TRIM_LEAD_IMPL = _swap(
    _GOLD_IMPL,
    "    result = (emit(lead) + trimmed) + emit(trail)  # type: PSeq[PSeq[int]]\n",
    "    result = (emit(lead.drop(n)) + trimmed) + emit(trail)  # type: PSeq[PSeq[int]]\n",
)
_RIVAL_TRIM_LEAD = _swap(_BASE, _GOLD_IMPL, _TRIM_LEAD_IMPL)

# (4) NO-TRIM-INCLUDED — emit the included lines VERBATIM (no .drop(n)). The
# lead/trail are correct, but the interior lines are untrimmed: result ==
# emit(lead) + included + emit(trail). Contradicts the pin AND both
# per-included-line clauses.
_NO_TRIM_IMPL = (
    "    # impl-start\n"
    "    # WRONG: do NOT trim the included text; emit it verbatim between the\n"
    "    # (correct) verbatim lead and trail.\n"
    "    result = (emit(lead) + included) + emit(trail)  # type: PSeq[PSeq[int]]\n"
    "    return result\n"
    "    # impl-end"
)
_RIVAL_NO_TRIM = _swap(_BASE, _GOLD_IMPL, _NO_TRIM_IMPL)

# (4b) SWAP-LEAD-TRAIL — trail prepended, lead appended (the prepend/append
# filters transposed). Interior trim correct, but Result()[0]==trail!=lead and
# the last element == lead != trail.
_SWAP_IMPL = _swap(
    _GOLD_IMPL,
    "    result = (emit(lead) + trimmed) + emit(trail)  # type: PSeq[PSeq[int]]\n",
    "    result = (emit(trail) + trimmed) + emit(lead)  # type: PSeq[PSeq[int]]\n",
)
_RIVAL_SWAP = _swap(_BASE, _GOLD_IMPL, _SWAP_IMPL)

# (5) PARTIAL-DOMAIN — correct on EVERY input except it leaves the FIRST included
# line untrimmed (included[0] verbatim, included[1:] trimmed). On any block with
# a non-empty first line this contradicts the per-included-line clauses and the
# pin. (The precondition admits a block whose first line is non-empty — the
# F2P's first included line is "    def baz():".) Built by restructuring the
# whole impl so no stale gold assert masks the rejection.
_PARTIAL_IMPL = (
    "    # impl-start\n"
    "    # WRONG (partial-domain): trim included[1:] but leave included[0] verbatim.\n"
    "    trimmed = PSeq(PSeq(0).take(0)).take(0)  # type: PSeq[PSeq[int]]\n"
    "    i = len(included)\n"
    "    while i > 1:\n"
    "        Invariant(1 <= i and i <= len(included))\n"
    "        # Terminating loop (measure i): the rejection must come from the\n"
    "        # postcondition, not an obligation leak.\n"
    "        Invariant(MustTerminate(i + 1))\n"
    "        trimmed = PSeq(included[i - 1].drop(n)) + trimmed\n"
    "        i = i - 1\n"
    "    interior = PSeq(PSeq(0).take(0)).take(0)  # type: PSeq[PSeq[int]]\n"
    "    if len(included) > 0:\n"
    "        interior = PSeq(included[0]) + trimmed\n"
    "    result = (emit(lead) + interior) + emit(trail)  # type: PSeq[PSeq[int]]\n"
    "    return result\n"
    "    # impl-end"
)
_RIVAL_PARTIAL = _swap(_BASE, _GOLD_IMPL, _PARTIAL_IMPL)


# (6) NON-EMPTY FOLD BASE — the only behaviourally LIVE mutant the empty-block
# base ever produced, kept here permanently now that the base carries no mutable
# literal for the mutation operator to land on.
#
# The fifth sampled mutant of the superseded base (`.take(0)` -> `.take(1)`, i.e.
# `PSeq(PSeq(0).take(0)).take(1)`) is the one that changes the VALUE: the backward
# fold starts from a ONE-ELEMENT block, so the assembled output carries a spurious
# empty line between the trimmed included text and the verbatim trailing line, and
# its length exceeds `len(emit(lead)) + len(included) + len(emit(trail))` by one.
# Measured verbatim (against the superseded spec surface), that mutant was
# rejected on the loop INVARIANT rather than on the postcondition:
#   model.py:122:19:122:61: error: Loop invariant might not hold on entry.
#   Assertion (trimmed == trim_block(included.drop(i), n)) might not hold.
# A rejection from an invariant that no longer fits the body is evidence about the
# proof, not about the spec, so this case REALIGNS the invariant to the mutant's
# own base (`trim_block(included.drop(i), n) + PSeq(PSeq(0).take(0)).take(1)`) and
# drops the lemma-discharge loop whose invariant the extra element falsifies. The
# fold proof then goes through and the rejection can only come from the
# POSTCONDITION.
_NONEMPTY_BASE_IMPL = (
    "    # impl-start\n"
    "    # WRONG: the fold base is a ONE-ELEMENT block (one empty line) instead of\n"
    "    # the empty block, so the assembled output carries a spurious empty line\n"
    "    # between the trimmed included text and the verbatim trailing line.\n"
    "    trimmed = PSeq(PSeq(0).take(0)).take(1)  # type: PSeq[PSeq[int]]\n"
    "    i = len(included)\n"
    "    while i > 0:\n"
    "        # invariants-start\n"
    "        Invariant(0 <= i and i <= len(included))\n"
    "        # Realigned to the rival's own base so the fold proof still goes\n"
    "        # through and the rejection comes from the POSTCONDITION.\n"
    "        Invariant(trimmed == trim_block(included.drop(i), n) + PSeq(PSeq(0).take(0)).take(1))\n"
    "        # Terminating loop (measure i): the rejection must come from the\n"
    "        # postcondition, not an obligation leak.\n"
    "        Invariant(MustTerminate(i + 1))\n"
    "        # invariants-end\n"
    "        Assert(included.drop(i - 1)[0] == included[i - 1])\n"
    "        Assert(included.drop(i - 1).drop(1) == included.drop(i))\n"
    "        trimmed = PSeq(included[i - 1].drop(n)) + trimmed\n"
    "        i = i - 1\n"
    "    result = (emit(lead) + trimmed) + emit(trail)  # type: PSeq[PSeq[int]]\n"
    "    return result\n"
    "    # impl-end"
)
_RIVAL_NONEMPTY_BASE = _swap(_BASE, _GOLD_IMPL, _NONEMPTY_BASE_IMPL)


# (10) TRIM ONLY IF A LEADING LINE IS PRESENT — the one-sided author-line-absence
# rival. Correct whenever a leading line is supplied; when it is absent the trim
# stage is SKIPPED entirely and the included text is emitted un-trimmed. Under
# the superseded precondition (`len(lead) >= 1`) that guard was PROVABLY DEAD and
# this verified.
_RIVAL_TRIM_IF_LEAD = _guarded(
    "    # WRONG: make the margin trim contingent on a leading line being present.\n"
    "    if len(lead) == 0:\n"
    "        return included + emit(trail)\n"
)

# (11) TRIM ONLY IF BOTH AUTHOR LINES ARE PRESENT — the two-sided variant, the
# broadest form of the same wrongness.
_RIVAL_TRIM_IF_BOTH = _guarded(
    "    # WRONG: make the margin trim contingent on BOTH author lines being\n"
    "    # present.\n"
    "    if len(lead) == 0 or len(trail) == 0:\n"
    "        return (emit(lead) + included) + emit(trail)\n"
)

# (12) NO TRIM AT ALL WHEN NEITHER AUTHOR LINE IS PRESENT — the narrowest form,
# and the one the UNCONDITIONAL-TRIM clause exists for.
_RIVAL_NO_TRIM_NO_AUTHOR = _guarded(
    "    # WRONG: with no author line at all, skip the margin trim and return the\n"
    "    # included text as-is.\n"
    "    if len(lead) == 0 and len(trail) == 0:\n"
    "        return included\n"
)

# (13) BLANK LINE FOR AN ABSENT AUTHOR LINE — the presence rule attacked from the
# other side. The trim is correct and the author lines that ARE supplied are
# verbatim, but an ABSENT (empty) author line is emitted as a real blank line
# instead of contributing nothing.
_RIVAL_BLANK_FOR_ABSENT = _swap(
    _BASE, _GOLD_IMPL,
    _swap(
        _GOLD_IMPL,
        "    result = (emit(lead) + trimmed) + emit(trail)  # type: PSeq[PSeq[int]]\n",
        "    # WRONG: emit an absent (empty) author line as a real BLANK line rather\n"
        "    # than omitting it.\n"
        "    result = (PSeq(lead) + trimmed) + PSeq(trail)  # type: PSeq[PSeq[int]]\n",
    ),
)

# (14) ZERO-WIDTH SUBSTITUTION — a boundary rival on the newly-in-domain trim
# width. Correct for every positive width; for a zero width (which must leave
# every line unchanged) it trims by one instead. Under the superseded
# precondition (`n >= 1`) this guard was PROVABLY DEAD and this verified.
_RIVAL_ZERO_WIDTH = _guarded(
    "    # WRONG: substitute a width of 1 for the zero-width (identity) trim.\n"
    "    if n == 0:\n"
    "        return (emit(lead) + trim_block(included, 1)) + emit(trail)\n"
)


SPEC_TESTS = [
    # ---- positive controls (must VERIFY) ----
    {"id": "pos-control-reshape", "kind": "soundness", "expect": "verify",
     "module": _POS_REORDER,
     "rationale": "structurally-different but CORRECT: the per-line trim is bound to a "
                  "named local `cur` inside the (identical, backward) fold, and the "
                  "assembly is split via a named `head` intermediate keeping the SAME "
                  "concatenation structure (emit(lead)+trimmed)+emit(trail). Every gold "
                  "proof obligation (the two loop-1 framing asserts, the lemma-discharge "
                  "loop invariants/asserts) is preserved, so it is not a proof-gap case "
                  "(PBT_PLAN §5a.2/5a.3). If it fails to verify the postcondition is "
                  "over-fit to one statement layout => SPEC-TOO-STRONG."},
    {"id": "echo-honest", "kind": "soundness", "expect": "verify",
     "module": _ECHO_HONEST,
     "rationale": "the output pin is GROUNDED in the inputs (trim_block is a @Pure fold of "
                  "included,n; emit is a @Pure function of one author line, and lead/trail "
                  "enter the pin through it), so there is no opaque oracle to echo. The gold "
                  "impl plus an extra assertion that the built result equals the grounded pin "
                  "must verify; it demonstrates the spec is NOT echo-vulnerable (no wrong "
                  "oracle-echo verifies — else this would be a reject case)."},
    {"id": "admiss-f2p-and-p2p-shapes", "kind": "admissibility", "expect": "verify",
     "module": _ADMISS,
     "rationale": "three probe inputs are PROVEN (Asserts on locally-built constants) to "
                  "satisfy the input-shape precondition, which is now just n >= 0: the F2P "
                  "shape (3 included content lines, non-empty lead/trail, n=2 — the dedent 2 "
                  "/ prepend 'class Foo:' / append '# comment' scenario), the complementary "
                  "P2P shape (a dedent with NEITHER author line — both empty), and the "
                  "zero-width shape. The MustTerminate conjunct is a caller obligation, not "
                  "an input-shape constraint. If any assert failed, PRECOND-TOO-STRONG — and "
                  "the P2P shape failing is exactly the narrowing that let the "
                  "author-line-absence rivals verify before."},
    {"id": "pos-live-no-author-line", "kind": "soundness", "expect": "verify",
     "module": _POS_LIVE_NO_AUTHOR,
     "rationale": "LIVENESS control for the author-line-ABSENT state, and the control that "
                  "makes rival-trim-only-if-lead-present / -if-both-present / "
                  "rival-no-trim-when-no-author-line meaningful. Guarded by "
                  "`len(lead) == 0 and len(trail) == 0`, the branch asserts properties that "
                  "are TRUE but hold only in that state (both emit(...) contributions are "
                  "empty, so the assembled block reduces to the trimmed included text). "
                  "Under the superseded precondition (len(lead) >= 1 and len(trail) >= 1) "
                  "the same guard was PROVABLY DEAD — `Assert(False)` inside it verified — "
                  "which is exactly why an implementation could make the trim contingent on "
                  "an author line and still pass. If this case is REJECTED the state is "
                  "still unreachable and the domain widening did not take, so the "
                  "author-line-absence rivals would be dead-branch cases proving nothing."},
    {"id": "pos-live-zero-width", "kind": "soundness", "expect": "verify",
     "module": _POS_LIVE_ZERO_WIDTH,
     "rationale": "LIVENESS control for the zero-width trim state, the same argument for `n` "
                  "and the control that makes rival-zero-width-substitution meaningful. The "
                  "`n == 0` branch asserts the true-only-there property that a zero-width "
                  "trim is the identity on every included line. Under the superseded "
                  "precondition (n >= 1) `if n == 0: Assert(False)` VERIFIED, so an "
                  "implementation was free to do anything at all for a zero-width trim. If "
                  "REJECTED, n == 0 is still out of domain."},
    {"id": "pos-inert-empty-base-equivalence", "kind": "soundness",
     "expect": "verify", "module": _POS_INERT_EQUIV,
     "rationale": "the machine-checked RECORD of G-MUT's four survivors on the superseded "
                  "base expression PSeq(PSeq(0).take(0)).take(0) (gate report verbatim: "
                  "\"killed 14/18 (78%); survivors: [\'line 117: \\'0\\' -> \\'-1\\'\', "
                  "\'line 117: \\'0\\' -> \\'1\\'\', \'line 117: \\'0\\' -> \\'-1\\'\', "
                  "\'line 117: \\'0\\' -> \\'1\\'\']\"). All four mutate a subexpression INSIDE the "
                  "outer .take(0), and X.take(0) is empty for every X, so all four denote the "
                  "SAME empty block: they are equivalent programs (each re-measured on its own: "
                  "\"Verification successful\" in 16.1s/17.2s/17.4s/17.6s, gold 22.5s), NOT "
                  "implementations the spec wrongly admits. This case turns that equivalence "
                  "into a proof obligation — five Asserts equating the gold expression and its "
                  "four mutations to the empty base the impl now uses, plus len(trimmed)==0 — "
                  "and is otherwise the gold impl, so it must verify. Non-vacuity: the same "
                  "module plus a trailing Assert(False) is rejected (\"error: Assert might "
                  "fail. Assertion False might not hold.\"), so the equalities are really "
                  "discharged. If this case were REJECTED the equivalence claim is false: the "
                  "four survivors would be behaviourally distinct rivals the spec admits, and "
                  "the remedy would be a strengthened postcondition, not an empty base "
                  "expression without an inert literal."},

    # ---- uniqueness rivals (must be REJECTED) ----
    {"id": "rival-prepatch-trim-all", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PREPATCH,
     "refinement": "this is the actual PRE-PATCH behaviour (== model_prepatch.py): the "
                   "per-line trim is the LAST pipeline stage, so it trims the whole "
                   "assembled block AFTER the leading/trailing lines were inserted. Its "
                   "faithful real patch is precisely the UN-patched read() pipeline, which "
                   "FAILS the F2P test_LiteralIncludeReader_dedent_and_append_and_prepend "
                   "(it emits the trimmed 'ass Foo:' / 'comment' instead of the verbatim "
                   "'class Foo:' / '# comment'). So it would NOT resolve.",
     "rationale": "the discriminating bug the patch fixes. Rejection source: the primary "
                  "pin Result() == (emit(lead)+trim_block(included,n))+emit(trail) and the "
                  "derived len(lead)>=1 -> Result()[0]==lead / Result()[0]!=lead.drop(n) — "
                  "the pre-patch order makes Result()[0]==lead.drop(n)!=lead. If it verified "
                  "=> SPEC-TOO-WEAK (admits the un-patched code)."},
    {"id": "rival-trim-lead-only", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_TRIM_LEAD,
     "refinement": "the SHARPEST discriminator: every line correct except the leading line "
                   "is emitted TRIMMED (lead.drop(n)). A faithful real patch that moves only "
                   "the append stage ahead of the trim but leaves the trim reaching the "
                   "prepended line would emit 'ass Foo:' instead of 'class Foo:' and FAIL the "
                   "F2P (expected first line 'class Foo:'). So it would NOT resolve.",
     "rationale": "Rejection source: the derived clauses len(lead)>=1 -> Result()[0]==lead "
                  "AND (len(lead)>=1 and n>=1) -> Result()[0]!=lead.drop(n) directly "
                  "contradict result[0]==lead.drop(n) on the F2P's regime; also the primary "
                  "pin. If it verified => SPEC-TOO-WEAK (verbatim-lead clause hollow)."},
    {"id": "rival-no-trim-included", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NO_TRIM,
     "refinement": "emits the included lines VERBATIM (no .drop(n)); lead/trail correct. A "
                   "faithful real patch that drops the trim stage from the pipeline "
                   "entirely would leave the included text un-dedented, emitting "
                   "'    def baz():' instead of the dedented '  def baz():' and FAIL the F2P "
                   "(which expects the dedented body). So it would NOT resolve.",
     "rationale": "Rejection source: the per-included-line clauses (offset 1 with a lead, "
                  "offset 0 without) and the primary pin (trim_block(included,n) != included "
                  "whenever some included line is non-empty and n>=1). If it verified => "
                  "SPEC-TOO-WEAK (interior trim unpinned)."},
    {"id": "rival-swap-lead-trail", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_SWAP,
     "refinement": "transposes the prepend/append author lines: trail first, lead last "
                   "(interior trim correct). A faithful real patch swapping the two author-"
                   "line stages would emit '# comment' as the first line and "
                   "'class Foo:' as the last, FAILING the F2P (expected first line "
                   "'class Foo:', last content line '# comment'). So it would NOT resolve.",
     "rationale": "Rejection source: the derived clauses len(lead)>=1 -> Result()[0]==lead "
                  "and len(trail)>=1 -> Result()[len(Result())-1]==trail (and the primary "
                  "pin) — the rival has Result()[0]==trail!=lead. If it verified => "
                  "SPEC-TOO-WEAK (line order unpinned)."},
    {"id": "rival-partial-first-line", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_PARTIAL,
     "refinement": "correct on every block whose first included line is empty, but leaves the "
                   "FIRST included line untrimmed (included[0] verbatim) while trimming the "
                   "rest. A faithful real patch with an off-by-one in the trim loop (start "
                   "at the second line) would emit '    def baz():' (untrimmed) for the F2P's "
                   "first included line instead of '  def baz():' and FAIL the F2P. So it "
                   "would NOT resolve.",
     "rationale": "partial-domain: pins only included[1:]. Rejection source: the "
                  "per-included-line clauses (Result()[1]==included[0].drop(n) with a lead) "
                  "and the primary pin — the rival has Result()[1]==included[0], which "
                  "differs from included[0].drop(n) on any non-empty first line (the F2P's is "
                  "'    def baz():'). If it verified => SPEC-TOO-WEAK (first-line sub-domain "
                  "unpinned)."},
    {"id": "rival-nonempty-fold-base", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NONEMPTY_BASE,
     "refinement": "the trim and both author lines are correct, but the assembled block "
                   "carries one line MORE than lead + included + trail: a spurious empty line "
                   "between the trimmed included text and the verbatim trailing line. A "
                   "faithful real patch whose append stage leaves an extra element behind "
                   "(e.g. `lines.append(\'\\n\' + append + \'\\n\')`, or an append stage that "
                   "keeps the blank the reorder was supposed to consume) emits "
                   "\'class Foo:\\n  def baz():\\n      pass\\n\\n\\n# comment\\n\' where the F2P "
                   "test_LiteralIncludeReader_dedent_and_append_and_prepend asserts "
                   "\'class Foo:\\n  def baz():\\n      pass\\n\\n# comment\\n\'. So it would NOT "
                   "resolve.",
     "rationale": "the ONE behaviourally live mutant of the fold base (the superseded "
                  "PSeq(PSeq(0).take(0)).take(0) idiom, mutated .take(0) -> .take(1)), kept as "
                  "a battery case because the base now carries no literal for the mutation "
                  "operator to reach. As a raw mutant it died on the loop invariant "
                  "(\"error: Loop invariant might not hold on entry. Assertion (trimmed == "
                  "trim_block(included.drop(i), n)) might not hold.\"), which is evidence "
                  "about the proof, not the spec; here the invariant is realigned to the "
                  "rival's own base so the fold proof goes through and the rejection can only "
                  "come from the POSTCONDITION: the primary pin, plus len(Result()) == "
                  "len(emit(lead)) + len(included) + len(emit(trail)) and the last-element "
                  "clause len(trail)>=1 -> Result()[len(Result())-1]==trail. If it VERIFIED "
                  "=> SPEC-TOO-WEAK: the spec would admit an implementation that inserts "
                  "content of its own into the assembled block, so the primary pin and the "
                  "length clause would both be hollow and G-MUT's only live kill on the fold "
                  "base was a proof artifact."},
    {"id": "rival-trim-only-if-lead-present", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_TRIM_IF_LEAD,
     "refinement": "makes the margin trim CONTINGENT on a leading line being supplied: with a "
                   "leading line it is the gold behaviour, without one the trim stage is "
                   "skipped and the included text is emitted un-trimmed. Its faithful real "
                   "patch keeps the fixed pipeline order only when the prepend option is "
                   "truthy and otherwise drops the trim stage. It PASSES the F2P (which "
                   "supplies both author lines) yet FAILS the P2P lane that dedents with "
                   "NEITHER author line: test_LiteralIncludeReader_dedent (lines 9-11, "
                   "dedent 2) expects '  def baz():\\n      pass\\n\\n' and would get the "
                   "un-trimmed '    def baz():\\n        pass\\n\\n', and "
                   "test_LiteralIncludeReader_tabwidth_dedent (tab-width 4, dedent 4) fails "
                   "the same way. So it would NOT resolve.",
     "rationale": "the author-line-ABSENCE hole, one-sided. Rejection source: the "
                  "UNCONDITIONAL-TRIM clause len(lead)==0 and len(trail)==0 -> Result() == "
                  "trim_block(included,n), the offset-0 per-included-line clause "
                  "len(lead)==0 -> Result()[i]==included[i].drop(n), and the primary pin — "
                  "each of which is now evaluated in a REACHABLE state (see "
                  "pos-live-no-author-line). If it verified => SPEC-TOO-WEAK: the trim's "
                  "unconditional presence would be unpinned and an implementation could make "
                  "the whole trim stage conditional on an author line."},
    {"id": "rival-trim-only-if-both-present", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_TRIM_IF_BOTH,
     "refinement": "the two-sided variant: the trim runs only when BOTH author lines are "
                   "supplied. Its faithful real patch keeps the fixed pipeline order only "
                   "when both the prepend and the append option are truthy and otherwise "
                   "drops the trim stage. Same verdict as the one-sided rival: F2P passes, "
                   "test_LiteralIncludeReader_dedent and "
                   "test_LiteralIncludeReader_tabwidth_dedent fail (un-trimmed included "
                   "text). So it would NOT resolve.",
     "rationale": "the broadest form of the author-line-absence hole. Rejection source: the "
                  "UNCONDITIONAL-TRIM clause and both per-included-line clauses (the rival is "
                  "also wrong in the one-author-line regimes, where the offset clause for the "
                  "supplied side still demands the trim). If it verified => SPEC-TOO-WEAK."},
    {"id": "rival-no-trim-when-no-author-line", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_NO_TRIM_NO_AUTHOR,
     "refinement": "the narrowest form: correct unless NEITHER author line is supplied, in "
                   "which case the included text is returned with no trim at all. Its "
                   "faithful real patch drops the trim stage exactly when neither option is "
                   "truthy. F2P passes; test_LiteralIncludeReader_dedent and "
                   "test_LiteralIncludeReader_tabwidth_dedent — the two P2P tests that set "
                   "dedent and set NEITHER prepend NOR append — fail. So it would NOT "
                   "resolve.",
     "rationale": "the exact sub-domain the UNCONDITIONAL-TRIM clause exists for. Rejection "
                  "source: len(lead)==0 and len(trail)==0 -> Result() == "
                  "trim_block(included,n). If it verified => SPEC-TOO-WEAK: the spec would "
                  "say nothing about whether the trim runs at all in the regime the oracle's "
                  "P2P lane exercises, which is the whole point of modelling this function."},
    {"id": "rival-blank-for-absent-author-line", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_BLANK_FOR_ABSENT,
     "refinement": "the presence rule attacked from the other side: the trim is correct and a "
                   "supplied author line is verbatim, but an ABSENT (empty) author line is "
                   "emitted as a real BLANK line instead of contributing nothing. Its "
                   "faithful real patch inserts the prepend/append line unconditionally "
                   "instead of only when the option is truthy. F2P passes; every P2P test "
                   "that omits prepend/append gains a spurious leading and/or trailing blank "
                   "line — test_LiteralIncludeReader_dedent would get "
                   "'\\n  def baz():\\n      pass\\n\\n\\n' against its expected "
                   "'  def baz():\\n      pass\\n\\n', and test_LiteralIncludeReader, "
                   "test_LiteralIncludeReader_lines1 and the rest fail the same way. So it "
                   "would NOT resolve.",
     "rationale": "pins the presence rule, not just the ordering. Rejection source: the "
                  "length clause len(Result()) == len(emit(lead)) + len(included) + "
                  "len(emit(trail)) (the rival's length is len(included)+2 regardless), the "
                  "UNCONDITIONAL-TRIM clause (the rival returns two extra blank lines in that "
                  "state) and the primary pin. If it verified => SPEC-TOO-WEAK: an "
                  "implementation could invent an author line that was never supplied."},
    {"id": "rival-zero-width-substitution", "kind": "uniqueness", "expect": "reject",
     "module": _RIVAL_ZERO_WIDTH,
     "refinement": "a boundary rival on the newly-in-domain trim width: correct for every "
                   "positive width, but for a zero width (which must leave every line "
                   "unchanged) it trims by one instead. Its faithful real patch maps a trim "
                   "width of 0 to 1 in the trim stage, so a zero-width trim eats the first "
                   "code point of every included line — visibly wrong behaviour for the "
                   "documented option, and rejected here rather than left to a dead branch.",
     "rationale": "under the superseded precondition (n >= 1) this guard was PROVABLY DEAD — "
                  "`if n == 0: Assert(False)` verified — so the spec said nothing about a "
                  "zero-width trim and this rival passed. Rejection source now: the primary "
                  "pin and the per-included-line clauses at n == 0, evaluated in a REACHABLE "
                  "state (see pos-live-zero-width). If it verified => SPEC-TOO-WEAK (the "
                  "zero-width boundary of the trim is unpinned)."},
]

# ===========================================================================
# AXIOM LANE — none. meta.json axioms == [] : there is NO consumed @ContractOnly
# axiom and NO A-consumed deep model whose Ensures is read numerically in the
# proof. The per-line trim is an A-REFERENCE deep model (`trim_block`) validated
# == the real `dedent_lines` callee OUT OF BAND by axiom_check.py / G-AX (run
# in-container by the orchestrator); `emit` is a deep @Pure definition of the
# author-line presence rule, likewise not an axiom. There is no in-proof axiom
# obligation for the PBT axiom lane to re-run, so AXIOM_TESTS is empty.
# ===========================================================================
AXIOM_TESTS = []
