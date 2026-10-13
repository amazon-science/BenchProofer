# properties.py — PBT manifest for django__django-12155. NOT a Nagini module; a
# record of adversarial cases the runner (swebench_nagini.pbt) parses.
#
# Instance shape: ONE modeled function, a value-returning de-indentation
# transform with a READ-ONLY input (Acc(...,1/2)):
#
#   dedent_block(eff[Acc 1/2]) -> List[int]
#       eff is the per-line summary of a docstring: entry k is the leading-
#       whitespace count of line k (>= 0) or the blank marker -1. The result is
#       the PEP 257 / inspect.cleandoc de-indentation: first line flushed left
#       (blank kept blank), every subsequent line slid left by the COMMON margin
#       measured over the non-blank lines AFTER the first only.
#
# Load-bearing pre clause:
#   (R2) MustTerminate(2) — the method is specified to TERMINATE, so a rival that
#        diverges (or re-discharges the postconditions through a self-call at the
#        same obligation level) is no longer admitted vacuously. Every variant below
#        therefore also carries the loop measure Invariant(MustTerminate(i - 1 + 1)),
#        and the admissibility case asserts the precondition at its witness instead
#        of self-calling (a method under a termination obligation may not call itself
#        at the same level).
#
# Load-bearing post clauses:
#   (P1) len(Result()) == len(eff)                      (one output per line)
#   (P2) ToSeq(Result()) == dedented(ToSeq(eff))        (the EXACT transform —
#        a GROUNDED @Pure oracle fully unfolded as first_line / remove_margin /
#        clamp_margin / min_indent_from over the input; no opaque answer-key)
#   (P3) Implies(len(eff)>0 and eff[0]>=0, Result()[0]==0)   (non-blank first
#        line ends flush-left)
#
# The discriminating content (the FAIL_TO_PASS bug) is the MARGIN MEASUREMENT
# SCOPE: clamp_margin(min_indent_from(ToSeq(eff), 1)) — over lines[1:] — vs the
# pre-patch trim_docstring measurement over ALL lines (min_indent_from(..,0)).
# On "firstline\n\n    second line" the fixed scope gives margin 4 (body flushed)
# and the pre-patch scope gives margin 0 (body stays indented -> docutils
# "default-role: no content permitted" stderr -> F2P fails).
#
# Oracle groundedness: P2's oracle `dedented` is GROUNDED — it is a pure total
# function of the single arg eff, fully unfolded by the @Pure helpers (no
# @ContractOnly answer-key to echo). So the ungrounded-oracle-echo class does
# NOT apply (see assessment); the uniqueness attack is instead partial-domain
# rivals that get the margin scope / first-line flush / per-line removal wrong,
# led by the literal prepatch bug.
#
# A-reference: `dedented` is validated == real inspect.cleandoc (per-line indent
# profile) by axiom_check.py / G-AX. The AXIOM_TESTS below re-run the real stdlib
# callee for soundness + caller-domain containment.
from pathlib import Path

INSTANCE = "django__django-12155"
FLOAT_ENCODING = None  # meta.json float_encoding is null and unused

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- exact impl-region body (verbatim from model.py, between the markers) ----
# Every variant is produced by _swap on this body; the markers themselves and
# everything outside the impl region (signature, pre/post-conditions, @Pure
# helpers) are NEVER touched => same_spec is guaranteed. The nested invariants
# region lives INSIDE impl and is elided by spec_view, so changing it (e.g. the
# prepatch margin scope) keeps the spec signature identical.
_IMPL = (
    "    result = []  # type: List[int]\n"
    "    n = len(eff)\n"
    "    if n == 0:\n"
    "        Assert(len(ToSeq(eff)) == 0)\n"
    "        Assert(ToSeq(result) == dedented(ToSeq(eff)))\n"
    "        return result\n"
    "    margin = clamp_margin(min_indent_from(ToSeq(eff), 1))\n"
    "    i = n\n"
    "    while i > 1:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(eff), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(1 <= i and i <= n and n == len(eff) and n > 0)\n"
    "        Invariant(margin == clamp_margin(min_indent_from(ToSeq(eff), 1)))\n"
    "        Invariant(len(result) == n - i)\n"
    "        Invariant(ToSeq(result) == remove_margin(\n"
    "            ToSeq(eff).drop(i), clamp_margin(min_indent_from(ToSeq(eff), 1))))\n"
    "        Invariant(MustTerminate(i - 1 + 1))\n"
    "        # invariants-end\n"
    "        c = eff[i - 1]\n"
    "        Assert(ToSeq(eff).drop(i - 1)[0] == c)\n"
    "        Assert(ToSeq(eff).drop(i - 1).drop(1) == ToSeq(eff).drop(i))\n"
    "        if c < 0:\n"
    "            result = [-1] + result\n"
    "        else:\n"
    "            result = [c - margin] + result\n"
    "        i = i - 1\n"
    "    Assert(i == 1)\n"
    "    Assert(ToSeq(eff).drop(1) == ToSeq(eff).drop(i))\n"
    "    first = eff[0]\n"
    "    Assert(first == ToSeq(eff)[0])\n"
    "    if first < 0:\n"
    "        result = [-1] + result\n"
    "    else:\n"
    "        result = [0] + result\n"
    "    Assert(result[0] == first_line(first))\n"
    "    # Unfold `dedented` once on the non-empty input; the loop already produced\n"
    "    # the body via the identical `clamp_margin(min_indent_from(...))` argument,\n"
    "    # so no recursive-function congruence step is needed.\n"
    "    Assert(dedented(ToSeq(eff)) ==\n"
    "           PSeq(first_line(ToSeq(eff)[0])) + remove_margin(\n"
    "               ToSeq(eff).drop(1), clamp_margin(min_indent_from(ToSeq(eff), 1))))\n"
    "    Assert(ToSeq(result) == dedented(ToSeq(eff)))\n"
    "    return result"
)

# sanity: the body appears verbatim & uniquely in the frozen model.
assert _BASE.count(_IMPL) == 1, "IMPL anchor drift"


# ---------------------------- FRAME-MUTATION (MANDATORY) ----------------------
# eff is Acc(list_pred(eff), 1/2) — a half-permission READ-ONLY input. This rival
# WRITES to eff (eff[0] = 0) up front, intending to coerce the first-line-flush
# postcondition cheaply (after eff[0]:=0, first_line(eff[0])==0 trivially). A
# write to a half-permission list is forbidden, so this MUST REJECT for
# INSUFFICIENT PERMISSION — not for a value mismatch. The whole gold body
# (invariants + asserts + post) is kept verbatim so the rejection is attributable
# to the write alone.
_FRAME = "    eff[0] = 0\n" + _IMPL


# --------------------- PARTIAL-DOMAIN #1: the literal prepatch bug ------------
# == model_prepatch.py: measure the common margin over ALL lines (index 0) rather
# than the lines AFTER the first (index 1). On a first line at column 0 the
# all-lines minimum is 0, so the body is left INDENTED. This is exactly the
# pre-patch trim_docstring `min(... for line in lines if line.lstrip())`. The
# whole margin scope (compute + both invariants) is moved to index 0 and the
# closing dedented-unfold asserts (which pin the index-1 transform) are dropped,
# so the rejection lands on the postcondition P2.
_PREPATCH = (
    "    result = []  # type: List[int]\n"
    "    n = len(eff)\n"
    "    if n == 0:\n"
    "        Assert(len(ToSeq(eff)) == 0)\n"
    "        Assert(ToSeq(result) == dedented(ToSeq(eff)))\n"
    "        return result\n"
    "    margin = clamp_margin(min_indent_from(ToSeq(eff), 0))\n"
    "    i = n\n"
    "    while i > 1:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(eff), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(1 <= i and i <= n and n == len(eff) and n > 0)\n"
    "        Invariant(margin == clamp_margin(min_indent_from(ToSeq(eff), 0)))\n"
    "        Invariant(len(result) == n - i)\n"
    "        Invariant(ToSeq(result) == remove_margin(\n"
    "            ToSeq(eff).drop(i), clamp_margin(min_indent_from(ToSeq(eff), 0))))\n"
    "        Invariant(MustTerminate(i - 1 + 1))\n"
    "        # invariants-end\n"
    "        c = eff[i - 1]\n"
    "        Assert(ToSeq(eff).drop(i - 1)[0] == c)\n"
    "        Assert(ToSeq(eff).drop(i - 1).drop(1) == ToSeq(eff).drop(i))\n"
    "        if c < 0:\n"
    "            result = [-1] + result\n"
    "        else:\n"
    "            result = [c - margin] + result\n"
    "        i = i - 1\n"
    "    Assert(i == 1)\n"
    "    Assert(ToSeq(eff).drop(1) == ToSeq(eff).drop(i))\n"
    "    first = eff[0]\n"
    "    if first < 0:\n"
    "        result = [-1] + result\n"
    "    else:\n"
    "        result = [0] + result\n"
    "    return result"
)


# --------- PARTIAL-DOMAIN #2: first line NOT flushed (keep its indent) --------
# Correct margin scope and body removal, but the first line keeps its original
# indentation (result = [first] + result) instead of being moved flush-left
# (result = [0] + result). On a docstring whose first line is indented (Django's
# blank-first-line style keeps line 0 blank, but many docstrings begin with an
# indented sentence), parse_docstring's title would carry leading whitespace, so
# parse_rst renders a different title and the no-leading-line-feed F2P/P2P shape
# diverges. The now-false closing asserts (result[0]==first_line(first) and
# ToSeq(result)==dedented) are dropped so the rejection lands on P2/P3, not a
# stale assert; the two IN-LOOP framing asserts are kept verbatim from gold (they
# are true of this variant too — its loop body is gold's), so the loop invariant
# still discharges and the rejection is attributable to the first line rather than
# to a missing unfold. Measured: rejected at the postcondition
# `ToSeq(Result()) == dedented(ToSeq(eff))`.
_NOFLUSH = (
    "    result = []  # type: List[int]\n"
    "    n = len(eff)\n"
    "    if n == 0:\n"
    "        Assert(len(ToSeq(eff)) == 0)\n"
    "        Assert(ToSeq(result) == dedented(ToSeq(eff)))\n"
    "        return result\n"
    "    margin = clamp_margin(min_indent_from(ToSeq(eff), 1))\n"
    "    i = n\n"
    "    while i > 1:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(eff), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(1 <= i and i <= n and n == len(eff) and n > 0)\n"
    "        Invariant(margin == clamp_margin(min_indent_from(ToSeq(eff), 1)))\n"
    "        Invariant(len(result) == n - i)\n"
    "        Invariant(ToSeq(result) == remove_margin(\n"
    "            ToSeq(eff).drop(i), clamp_margin(min_indent_from(ToSeq(eff), 1))))\n"
    "        Invariant(MustTerminate(i - 1 + 1))\n"
    "        # invariants-end\n"
    "        c = eff[i - 1]\n"
    "        Assert(ToSeq(eff).drop(i - 1)[0] == c)\n"
    "        Assert(ToSeq(eff).drop(i - 1).drop(1) == ToSeq(eff).drop(i))\n"
    "        if c < 0:\n"
    "            result = [-1] + result\n"
    "        else:\n"
    "            result = [c - margin] + result\n"
    "        i = i - 1\n"
    "    first = eff[0]\n"
    "    if first < 0:\n"
    "        result = [-1] + result\n"
    "    else:\n"
    "        result = [first] + result\n"
    "    return result"
)


# --------- PARTIAL-DOMAIN #3: body NOT de-indented (margin forced to 0) --------
# Correct first-line flush, but every body line keeps its original indentation
# (margin pinned to 0 instead of the measured common amount). This is the
# behaviour an impl gets if it computes the margin but never subtracts it. On the
# F2P shape "firstline\n\n    second line" the body line stays at indent 4
# instead of 0 -> docutils "default-role" stderr -> F2P fails. The closing
# dedented-unfold asserts are dropped so the rejection lands on P2; the in-loop
# framing asserts are kept verbatim from gold, and the loop invariant is restated
# for THIS variant's margin (0), so the loop discharges and the rejection is
# attributable to the pinned margin. Measured: rejected at the postcondition
# `ToSeq(Result()) == dedented(ToSeq(eff))`.
_NODEDENT = (
    "    result = []  # type: List[int]\n"
    "    n = len(eff)\n"
    "    if n == 0:\n"
    "        Assert(len(ToSeq(eff)) == 0)\n"
    "        Assert(ToSeq(result) == dedented(ToSeq(eff)))\n"
    "        return result\n"
    "    margin = 0\n"
    "    i = n\n"
    "    while i > 1:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(eff), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(1 <= i and i <= n and n == len(eff) and n > 0)\n"
    "        Invariant(margin == 0)\n"
    "        Invariant(len(result) == n - i)\n"
    "        Invariant(ToSeq(result) == remove_margin(ToSeq(eff).drop(i), 0))\n"
    "        Invariant(MustTerminate(i - 1 + 1))\n"
    "        # invariants-end\n"
    "        c = eff[i - 1]\n"
    "        Assert(ToSeq(eff).drop(i - 1)[0] == c)\n"
    "        Assert(ToSeq(eff).drop(i - 1).drop(1) == ToSeq(eff).drop(i))\n"
    "        if c < 0:\n"
    "            result = [-1] + result\n"
    "        else:\n"
    "            result = [c - margin] + result\n"
    "        i = i - 1\n"
    "    first = eff[0]\n"
    "    if first < 0:\n"
    "        result = [-1] + result\n"
    "    else:\n"
    "        result = [0] + result\n"
    "    return result"
)


# ----- PARTIAL-DOMAIN #4: blank body lines turned non-blank (lose the marker) --
# Correct margin and first-line flush, but a blank body line is emitted as a
# non-blank zero-indent line (result = [0] + result on the c<0 branch) instead of
# kept blank (-1). cleandoc keeps blank lines blank; a faithful real patch that
# converted blank lines to empty-content non-blank lines would change the
# paragraph-splitting (re.split on \n{2,}) downstream -> wrong (title, body)
# split -> F2P/P2P diverge. Rejected by P2's content: the gold loop invariant
# (kept verbatim, framing asserts included) already says the accumulated tail IS
# `remove_margin(ToSeq(eff).drop(i), margin)`, and a body line emitted as 0 where
# that carries -1 violates it, so the verifier reports the invariant rather than
# the postcondition. Measured: `Loop invariant might not be preserved. Assertion
# (ToSeq(result) == remove_margin(ToSeq(eff).drop(i), clamp_margin(
# min_indent_from(ToSeq(eff), 1)))) might not hold.`
_BLANKWRONG = (
    "    result = []  # type: List[int]\n"
    "    n = len(eff)\n"
    "    if n == 0:\n"
    "        Assert(len(ToSeq(eff)) == 0)\n"
    "        Assert(ToSeq(result) == dedented(ToSeq(eff)))\n"
    "        return result\n"
    "    margin = clamp_margin(min_indent_from(ToSeq(eff), 1))\n"
    "    i = n\n"
    "    while i > 1:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(eff), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(1 <= i and i <= n and n == len(eff) and n > 0)\n"
    "        Invariant(margin == clamp_margin(min_indent_from(ToSeq(eff), 1)))\n"
    "        Invariant(len(result) == n - i)\n"
    "        Invariant(ToSeq(result) == remove_margin(\n"
    "            ToSeq(eff).drop(i), clamp_margin(min_indent_from(ToSeq(eff), 1))))\n"
    "        Invariant(MustTerminate(i - 1 + 1))\n"
    "        # invariants-end\n"
    "        c = eff[i - 1]\n"
    "        Assert(ToSeq(eff).drop(i - 1)[0] == c)\n"
    "        Assert(ToSeq(eff).drop(i - 1).drop(1) == ToSeq(eff).drop(i))\n"
    "        result = [0] + result\n"
    "        i = i - 1\n"
    "    first = eff[0]\n"
    "    if first < 0:\n"
    "        result = [-1] + result\n"
    "    else:\n"
    "        result = [0] + result\n"
    "    return result"
)


# --------------------------- POSITIVE CONTROL (soundness) ---------------------
# Structurally-different but CORRECT: the two value-producing branches are
# REORDERED to test the non-blank case first (if c >= 0 / else) for the body and
# (if first >= 0 / else) for the first line. The executable shape differs (branch
# order) but the produced content is identical, and EVERY gold framing assert and
# loop invariant is kept verbatim (per AVOID-bug #2), so the gold proof still
# discharges. Must verify; a failure here would be SPEC-TOO-STRONG. (A branch
# reorder is chosen over a loop-direction flip per AVOID-bug #3: the spec helpers
# are front-recursive folds, so a forward-append loop would need a congruence
# lemma the verifier cannot auto-discharge; the gold loop is backward-prepending
# and is preserved.)
_POS = (
    "    result = []  # type: List[int]\n"
    "    n = len(eff)\n"
    "    if n == 0:\n"
    "        Assert(len(ToSeq(eff)) == 0)\n"
    "        Assert(ToSeq(result) == dedented(ToSeq(eff)))\n"
    "        return result\n"
    "    margin = clamp_margin(min_indent_from(ToSeq(eff), 1))\n"
    "    i = n\n"
    "    while i > 1:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(eff), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(1 <= i and i <= n and n == len(eff) and n > 0)\n"
    "        Invariant(margin == clamp_margin(min_indent_from(ToSeq(eff), 1)))\n"
    "        Invariant(len(result) == n - i)\n"
    "        Invariant(ToSeq(result) == remove_margin(\n"
    "            ToSeq(eff).drop(i), clamp_margin(min_indent_from(ToSeq(eff), 1))))\n"
    "        Invariant(MustTerminate(i - 1 + 1))\n"
    "        # invariants-end\n"
    "        c = eff[i - 1]\n"
    "        Assert(ToSeq(eff).drop(i - 1)[0] == c)\n"
    "        Assert(ToSeq(eff).drop(i - 1).drop(1) == ToSeq(eff).drop(i))\n"
    "        if c >= 0:\n"
    "            result = [c - margin] + result\n"
    "        else:\n"
    "            result = [-1] + result\n"
    "        i = i - 1\n"
    "    Assert(i == 1)\n"
    "    Assert(ToSeq(eff).drop(1) == ToSeq(eff).drop(i))\n"
    "    first = eff[0]\n"
    "    Assert(first == ToSeq(eff)[0])\n"
    "    if first >= 0:\n"
    "        result = [0] + result\n"
    "    else:\n"
    "        result = [-1] + result\n"
    "    Assert(result[0] == first_line(first))\n"
    "    Assert(dedented(ToSeq(eff)) ==\n"
    "           PSeq(first_line(ToSeq(eff)[0])) + remove_margin(\n"
    "               ToSeq(eff).drop(1), clamp_margin(min_indent_from(ToSeq(eff), 1))))\n"
    "    Assert(ToSeq(result) == dedented(ToSeq(eff)))\n"
    "    return result"
)


# ------------------------------- ADMISSIBILITY --------------------------------
# The witness is a concrete in-domain summary for "firstline\n\n    second line" —
# eff = [0, -1, 4] (non-blank first line at indent 0, a blank line, a body line at
# indent 4). Two things are asserted AT it: the method's own precondition
# (`Acc(list_pred(sample), 1/2)`, i.e. a freshly built full-permission list can
# lend the half share the spec asks for), and the value the spec's measurement
# vocabulary takes there — the common amount over the lines AFTER the first is 4,
# and the fold's empty case at k = len reports "no line to measure". If the
# precondition rejected this normal input, or the measurement disagreed with the
# intended amount at it, the probe would fail -> PRECOND-TOO-STRONG. The
# measurement asserts are unfolded index by index because `min_indent_from` is
# front-recursive and the verifier unfolds a @Pure function a bounded number of
# times, not because any step is in doubt.
#
# The witness is asserted rather than passed to a self-call: `dedent_block` carries
# `Requires(MustTerminate(2))`, and a method under a termination obligation may not
# call itself at the same level (Nagini: "Obligation leak check failed"). Asserting
# the callee's own precondition clauses at the witness is the substitution used
# across this corpus for exactly that reason, and it keeps the domain claim while
# dropping only the device.
_ADMISS = (
    "    sample = [0, -1, 4]  # type: List[int]\n"
    "    Assert(Acc(list_pred(sample), 1 / 2))\n"
    "    Assert(len(sample) == 3)\n"
    "    Assert(len(ToSeq(sample)) == 3)\n"
    "    Assert(ToSeq(sample)[0] == 0)\n"
    "    Assert(ToSeq(sample)[1] == -1)\n"
    "    Assert(ToSeq(sample)[2] == 4)\n"
    "    Assert(min_indent_from(ToSeq(sample), 3) == NO_AMOUNT())\n"
    "    Assert(min_indent_from(ToSeq(sample), 2) == 4)\n"
    "    Assert(min_indent_from(ToSeq(sample), 1) == 4)\n"
    "    Assert(clamp_margin(min_indent_from(ToSeq(sample), 1)) == 4)\n"
) + _IMPL


SPEC_TESTS = [
    {
        "id": "frame-mutation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _FRAME),
        "refinement": "Writes eff[0] = 0 to the half-permission read-only input. "
                      "Its faithful real patch would MUTATE the caller's docstring "
                      "representation in place to coerce the flush rather than "
                      "compute a fresh de-indented string — the gold patch calls "
                      "inspect.cleandoc(docstring), which returns a NEW string and "
                      "never mutates its argument. An in-place rewrite of the "
                      "shared docstring/list is not the gold fix and would not "
                      "faithfully resolve F2P.",
        "rationale": "Must reject for INSUFFICIENT PERMISSION: eff is "
                     "Acc(list_pred(eff), 1/2); eff[0] = 0 needs full write "
                     "permission. The rejection is attributable to the write — the "
                     "gold invariants, asserts and all three post clauses are kept "
                     "verbatim. This is the #1 weakness class and the input is "
                     "read-only, so the case is mandatory.",
    },
    {
        "id": "prepatch-all-lines-margin",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _PREPATCH),
        "refinement": "== model_prepatch.py: measures the common margin over ALL "
                      "lines (min_indent_from(.., 0)) instead of the lines AFTER "
                      "the first (min_indent_from(.., 1)). This is the literal "
                      "pre-patch trim_docstring "
                      "`min(len(line)-len(line.lstrip()) for line in lines if "
                      "line.lstrip())`. On the F2P docstring "
                      "'firstline\\n\\n    second line' the first line sits at "
                      "column 0, so the all-lines minimum is 0 and the body line "
                      "stays at indent 4 -> docutils emits the 'default-role: no "
                      "content permitted' error to stderr -> "
                      "test_parse_rst_with_docstring_no_leading_line_feed fails "
                      "(its captured_stderr is non-empty). The faithful real patch "
                      "is exactly the code the gold patch deletes.",
        "rationale": "Rejected by Ensures(ToSeq(Result()) == dedented(ToSeq(eff))) "
                     "(P2): dedented measures over lines[1:] (min_indent_from(s,1) "
                     "via clamp_margin), so a body de-indented by the all-lines "
                     "margin (0 on the F2P shape) cannot equal it. This is the "
                     "G-DIFF discriminator; the prepatch model fails on exactly "
                     "this clause.",
    },
    {
        "id": "first-line-not-flushed",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _NOFLUSH),
        "refinement": "Keeps the first line's original indentation (emits `first` "
                      "instead of 0 on the non-blank branch) rather than moving it "
                      "flush-left. cleandoc / PEP 257 always lstrip the first line; "
                      "a faithful real patch that skipped lines[0]=lines[0].lstrip() "
                      "would leave leading whitespace on the title, so "
                      "parse_docstring's title parses differently and the rst "
                      "rendering diverges from the gold output on any docstring "
                      "whose first line is indented (a P2P shape).",
        "rationale": "Rejected by Ensures(ToSeq(Result())==dedented(ToSeq(eff))) "
                     "(P2, since first_line(x)==0 for a non-blank x) and equally by "
                     "Ensures(Implies(eff[0]>=0, Result()[0]==0)) (P3): when eff[0] "
                     "is a non-blank indented line, Result()[0]==first != 0 "
                     "contradicts both clauses. Measured: the verifier reports P2.",
    },
    {
        "id": "body-not-dedented",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _NODEDENT),
        "refinement": "Computes nothing — pins the body margin to 0, so every body "
                      "line keeps its original indentation. A faithful real patch "
                      "that measured but never applied the margin "
                      "(omitting lines[i]=lines[i][margin:]) leaves the body "
                      "indented; on 'firstline\\n\\n    second line' the body stays "
                      "at indent 4 -> docutils 'default-role' stderr -> F2P fails. "
                      "Distinct from the prepatch rival (which mis-SCOPES the "
                      "margin); this one drops the removal entirely.",
        "rationale": "Rejected by Ensures(ToSeq(Result())==dedented(ToSeq(eff))) "
                     "(P2): remove_margin(s.drop(1), clamp_margin(min_indent_from("
                     "s,1))) subtracts the measured common amount from each body "
                     "line; a body left at margin 0 cannot equal it whenever the "
                     "common amount is > 0.",
    },
    {
        "id": "blank-body-line-emitted-nonblank",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _BLANKWRONG),
        "refinement": "Emits every body line as a non-blank zero-indent line "
                      "(result = [0] + result) instead of preserving the blank "
                      "marker -1 for empty/whitespace-only lines. cleandoc keeps "
                      "blank lines blank; converting them to empty non-blank lines "
                      "would change the downstream paragraph split "
                      "(re.split(r'\\n{2,}', docstring)) so parse_docstring returns "
                      "a different (title, body, metadata) -> F2P/P2P diverge.",
        "rationale": "Rejected by P2's content "
                     "(Ensures(ToSeq(Result())==dedented(ToSeq(eff)))): "
                     "remove_margin maps a blank entry (x<0) to -1, so on a "
                     "docstring containing any blank body line (the F2P shape has "
                     "one) the emitted 0 differs from -1. Reported at the loop "
                     "invariant that carries that clause per step "
                     "(ToSeq(result) == remove_margin(ToSeq(eff).drop(i), margin)) "
                     "rather than at the postcondition, because the gold invariant "
                     "and framing asserts are kept verbatim and the wrong entry "
                     "breaks them on the very first blank line.",
    },
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL, _POS),
        "rationale": "A structurally-different but CORRECT impl: both "
                     "value-producing if/else branches are reordered to test the "
                     "non-blank case first (if c>=0 / if first>=0), producing "
                     "identical content. Every gold loop invariant and framing "
                     "assert (the drop-congruence asserts, first==ToSeq(eff)[0], "
                     "result[0]==first_line(first), and the dedented-unfold) is "
                     "kept verbatim, so the gold proof still discharges. Must "
                     "verify; a failure would be SPEC-TOO-STRONG. Branch reorder is "
                     "deliberately chosen over a loop-direction flip because the "
                     "spec helpers are front-recursive folds (a forward-append "
                     "would need an f(a+b) congruence lemma the verifier cannot "
                     "auto-discharge — a proof gap, not a spec defect).",
    },
    {
        "id": "admissibility",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL, _ADMISS),
        "rationale": "An F2P-shaped in-domain witness — the summary [0, -1, 4] of "
                     "'firstline\\n\\n    second line' (non-blank first line at "
                     "indent 0, a blank line, a body line at indent 4) — with the "
                     "method's own precondition asserted at it: "
                     "Acc(list_pred(sample), 1/2), i.e. a freshly built list can "
                     "lend the half share the spec asks for. If the precondition "
                     "rejected this normal input the probe would fail -> "
                     "PRECOND-TOO-STRONG. Because that clause is the only "
                     "value-independent one, the probe also asserts what the spec's "
                     "measurement vocabulary yields AT the witness: the common "
                     "amount over the lines after the first is 4 (the F2P margin) "
                     "and the fold's empty case reports NO_AMOUNT() — asserts that "
                     "DO depend on the witness and would fail if the spec measured "
                     "it differently. Not a self-call: dedent_block carries "
                     "Requires(MustTerminate(2)), and a method under a termination "
                     "obligation may not call itself at the same level, so the "
                     "corpus substitution (assert the callee's Requires at the "
                     "witness) is used. The gold body follows verbatim, so the "
                     "case also re-confirms the gold proof discharges after it.",
    },
]


# ============================== AXIOM LANE ===================================
# meta.json axioms=[] (no @ContractOnly axiom the proof CONSUMES), but there IS an
# A-reference deep model: `dedented` is validated == real inspect.cleandoc by
# axiom_check.py / G-AX. The PBT plan §4 checks A-reference deep models the same
# way as axioms — the deep model must equal the real callee on every
# caller-reachable input. `inspect` is the Python standard library (the very
# module the gold patch calls), so the probes are self-contained and run in any
# Python. apply_gold=True for convention; cleandoc is unchanged stdlib so the
# result is independent of the patch.

_AX_SOUNDNESS = r'''
import inspect, random, sys

NO_AMOUNT = -1

# --- the model.py deep-model encodings (lock-step with the pure region) ---
# The empty-fold marker is NEGATIVE, exactly as in model.py: a leading-whitespace
# amount is a count of characters, so it is never negative, whereas ANY large
# number is a reachable amount and a large marker would alias a real line.
def min_indent_from(eff, k):
    m = NO_AMOUNT
    for i in range(k, len(eff)):
        if eff[i] >= 0 and (m < 0 or eff[i] < m):
            m = eff[i]
    return m

def clamp_margin(m):
    return m if m >= 0 else 0

def dedent_reference_profile(eff):
    """The same transform with NO empty-fold marker of any kind: remove the
    minimum over the non-blank entries after the first, or nothing when there are
    none. Independent of how model.py (or cleandoc) says "no line to measure"."""
    if len(eff) == 0:
        return []
    body = [x for x in eff[1:] if x >= 0]
    margin = min(body) if body else 0
    return [first_line(eff[0])] + [(-1 if x < 0 else x - margin) for x in eff[1:]]

def remove_margin(eff, margin):
    return [(-1 if x < 0 else x - margin) for x in eff]

def first_line(x):
    return -1 if x < 0 else 0

def dedented(eff):
    if len(eff) == 0:
        return []
    margin = clamp_margin(min_indent_from(eff, 1))
    return [first_line(eff[0])] + remove_margin(eff[1:], margin)

def to_eff(docstring):
    lines = docstring.expandtabs().split('\n')
    eff = []
    for line in lines:
        content = len(line.lstrip())
        eff.append(-1 if content == 0 else len(line) - content)
    return eff

def cleandoc_indent_profile(docstring):
    """Real inspect.cleandoc indentation transform, BEFORE its leading/trailing
    blank-line stripping (an unchanged post-step orthogonal to the measurement
    under test). Mirrors cleandoc's own body so the comparison is at the exact
    per-line index level the model decides (no value-membership double-mask)."""
    lines = docstring.expandtabs().split('\n')
    margin = sys.maxsize
    for line in lines[1:]:
        content = len(line.lstrip())
        if content:
            margin = min(margin, len(line) - content)
    if lines:
        lines[0] = lines[0].lstrip()
    if margin < sys.maxsize:
        for i in range(1, len(lines)):
            lines[i] = lines[i][margin:]
    profile = []
    for line in lines:
        content = len(line.lstrip())
        profile.append(-1 if content == 0 else len(line) - content)
    return profile

def check(s):
    expected = dedented(to_eff(s))            # model.py deep model
    observed = cleandoc_indent_profile(s)     # real inspect.cleandoc
    assert observed == expected, (
        "deep model unsound on %r: cleandoc profile %r, model %r"
        % (s, observed, expected))
    real = inspect.cleandoc(s)                # exercise the actual callee
    assert isinstance(real, str)

# --- boundary cases (incl. the FAIL_TO_PASS shape + Django docstring style) ---
boundary = [
    "", "oneliner", "   leading spaces only line",
    "firstline\n\n    second line",
    "\n    First line empty.\n\n    Second.\n",
    "title\n\n    metadata: x", "a\n  b\n    c", "   a\n  b",
    "x\n\ty\n\t\tz", "no body\n", "\n\n\n",
    "head\n    indented body\nflush body", "\n    a\n      b\n    c\n",
]
for s in boundary:
    check(s)

# --- the FAIL_TO_PASS discriminator: fixed margin (lines[1:]) vs prepatch (all) ---
discriminator = "firstline\n\n    second line"
eff = to_eff(discriminator)
fixed_margin = clamp_margin(min_indent_from(eff, 1))   # over lines[1:]
buggy_margin = clamp_margin(min_indent_from(eff, 0))   # over all lines (pre-patch)
assert fixed_margin != buggy_margin, "discriminator does not separate the scopes"
assert fixed_margin == 4 and buggy_margin == 0, (
    "unexpected margins fixed=%r buggy=%r" % (fixed_margin, buggy_margin))
# real cleandoc flushes the body line (fixed behaviour)
assert inspect.cleandoc(discriminator).split('\n')[-1] == "second line"
check(discriminator)

# --- amount magnitude: the empty-fold marker must not alias a real amount ---
# An amount of leading whitespace is a count of characters, so the carrier (an
# unbounded int) admits amounts of ANY size. A marker that is merely a LARGE
# number is itself such an amount, and a body line sitting exactly there would be
# read as "no line to measure" -> nothing removed from a body that must move.
# The standard here is the marker-free reference, checked at and around every
# magnitude a marker might take. Above 1e9 the reference rather than cleandoc is
# the standard on purpose: cleandoc's own sys.maxsize marker is safe only because
# a str with that many leading spaces cannot exist (~9 EB), so above the
# physically reachable range the encodings part company and the claim is about the
# intended transform. Below it, the boundary/fuzz blocks compare against the
# actual stdlib callee. Checked at summary level (a 1e9-space line costs ~2 GB).
wide = [10 ** 9 - 1, 10 ** 9, 10 ** 9 + 1,
        sys.maxsize - 1, sys.maxsize, sys.maxsize + 1, 2 ** 70]
magnitude = []
for big in wide:
    magnitude += [[0, -1, big], [big, -1, big], [0, big, big + 3],
                  [-1, big], [big], [big, big], [0, -1, big, 3]]
prng = random.Random(121550)
amounts = [0, 1, 2, 7, 10, 10 ** 9 - 1, 10 ** 9, 10 ** 9 + 1, sys.maxsize, 2 ** 70]
for _ in range(20000):
    magnitude.append([-1 if prng.randint(0, 3) == 0 else prng.choice(amounts)
                      for _ in range(prng.randint(0, 7))])
for eff in magnitude:
    assert dedented(eff) == dedent_reference_profile(eff), (
        "deep model disagrees with the marker-free reference on %r: model %r, "
        "reference %r" % (eff, dedented(eff), dedent_reference_profile(eff)))

# --- randomized fuzz: many shapes incl. blanks / whitespace-only / tabs ---
rng = random.Random(12155)
snippets = ["x", "ab", "q w", "...", "metadata: y", ":model:`m`"]
for _ in range(40000):
    nlines = rng.randint(0, 7)
    lines = []
    for _ in range(nlines):
        kind = rng.randint(0, 2)
        if kind == 0:
            lines.append("")
        elif kind == 1:
            lines.append(" " * rng.randint(0, 10))
        else:
            lines.append(" " * rng.randint(0, 10) + rng.choice(snippets))
    check("\n".join(lines))

print("AX-SOUND OK: deep model `dedented` == real inspect.cleandoc per-line "
      "indent profile on %d boundary + 40000 fuzz docstrings; == the marker-free "
      "reference on %d summaries carrying amounts up to 2**70 (no empty-fold "
      "aliasing); FAIL_TO_PASS discriminator separates fixed (4) from pre-patch "
      "(0) margin." % (len(boundary), len(magnitude)))
sys.exit(0)
'''

_AX_CONTAINMENT = r'''
import inspect, random, sys

# The model's dedent_block(eff) feeds the deep model `dedented` (and through it
# min_indent_from(s, k) and remove_margin). The A-reference callee is
# inspect.cleandoc(doc: str). Containment obligation: every callee-input the
# MODEL can reach must lie in the callee's Requires domain.
#
# The model's only precondition is Acc(list_pred(eff), 1/2): eff is ANY List[int]
# under the carrier mapping (entry = leading-whitespace count >= 0, or the blank
# marker -1). min_indent_from is called only with k in {0, 1, ..} (its own
# Requires is 0 <= k; the impl passes k=1 and recurses upward) — always in domain.
#
# inspect.cleandoc has NO domain restriction: it accepts ANY str (single arg, no
# flags; meta.json flag_dependency = none). So EVERY reachable docstring is a
# valid cleandoc input. We confirm: for every per-line summary shape the carrier
# can produce, a witnessing real str exists that cleandoc accepts and whose
# round-tripped summary matches the shape — i.e. the carrier never produces a
# summary outside what a real (expandtabs+split) docstring yields.

NO_AMOUNT = -1   # the empty-fold marker, negative as in model.py

def min_indent_from(eff, k):
    m = NO_AMOUNT
    for i in range(k, len(eff)):
        if eff[i] >= 0 and (m < 0 or eff[i] < m):
            m = eff[i]
    return m

def to_eff(docstring):
    lines = docstring.expandtabs().split('\n')
    eff = []
    for line in lines:
        content = len(line.lstrip())
        eff.append(-1 if content == 0 else len(line) - content)
    return eff

def witness(summary):
    """Build a real docstring whose per-line summary is exactly `summary`:
    a blank marker -1 -> an empty line; a count c>=0 -> c spaces + 'x'."""
    lines = []
    for c in summary:
        if c < 0:
            lines.append("")
        else:
            lines.append(" " * c + "x")
    return "\n".join(lines)

rng = random.Random(2155)
checked = 0
# The carrier to_eff(s) = s.expandtabs().split('\n') summarised entry-wise; a
# split on '\n' ALWAYS yields >= 1 element, so a reachable summary has length
# >= 1 (the empty docstring "" yields [-1], not []). Sample 1..7 lines.
for _ in range(20000):
    nlines = rng.randint(1, 7)
    summary = []
    for _ in range(nlines):
        if rng.random() < 0.3:
            summary.append(-1)                 # blank marker
        else:
            summary.append(rng.randint(0, 12)) # leading-whitespace count
    s = witness(summary)
    # the witnessing string round-trips to the same summary (carrier is realizable)
    assert to_eff(s) == summary, "carrier summary not realizable: %r" % (summary,)
    # cleandoc accepts it without error (callee Requires domain = any str)
    out = inspect.cleandoc(s)
    assert isinstance(out, str), "cleandoc rejected an in-carrier input"
    # min_indent_from is only ever asked for k in {0,1}; both satisfy its 0<=k
    _ = min_indent_from(summary, 1)
    _ = min_indent_from(summary, 0)
    checked += 1

print("AX-CONTAIN OK: every caller-reachable per-line summary (%d sampled) "
      "corresponds to a real docstring that inspect.cleandoc accepts; "
      "min_indent_from only ever called with k in {0,1} (in its 0<=k domain). "
      "No reachable input lies outside the A-reference callee's domain." % checked)
sys.exit(0)
'''

AXIOM_TESTS = [
    {
        "id": "ax-sound-dedented",
        "axiom": "dedented",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUNDNESS,
        "rationale": "The A-reference deep model `dedented` must equal the REAL "
                     "inspect.cleandoc per-line indentation transform on every "
                     "caller-reachable input. The probe runs the actual stdlib "
                     "cleandoc on 13 boundary docstrings (empty, single line, the "
                     "FAIL_TO_PASS shape, Django blank-first-line style, tabs, "
                     "all-blank, mixed) plus 40000 randomized fuzz docstrings and "
                     "asserts the profiles match; it also pins the FAIL_TO_PASS "
                     "discriminator (fixed margin 4 over lines[1:] vs pre-patch 0 "
                     "over all lines). Any disagreement is AXIOM-UNSOUND. Mirrors "
                     "axiom_check.py (G-AX), which exits 0 on host.",
    },
    {
        "id": "ax-contain-dedented",
        "axiom": "dedented",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_CONTAINMENT,
        "rationale": "Containment: every callee-input the model can reach lies in "
                     "the A-reference callee's Requires domain. inspect.cleandoc "
                     "accepts ANY str (single arg, no flags — meta flag_dependency "
                     "none), and min_indent_from's only caller-supplied index is k "
                     "in {0,1} (its Requires is 0<=k). The probe samples 20000 "
                     "per-line summaries the carrier can produce, builds a "
                     "witnessing real docstring for each, confirms it round-trips "
                     "to that summary and that cleandoc accepts it. A reachable "
                     "input outside the callee domain would be "
                     "AXIOM-TOO-WEAK-FOR-CALLER; none exists here.",
    },
]
