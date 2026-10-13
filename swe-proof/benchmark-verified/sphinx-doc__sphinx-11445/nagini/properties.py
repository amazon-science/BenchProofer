"""PBT falsification battery for sphinx-doc__sphinx-11445.

Parsed by swebench_nagini.pbt. Each SPEC_TESTS case is a full model.py variant
that shares the FROZEN spec (markers.same_spec) and differs only inside the
`# impl-start` / `# impl-end` region (region surgery via _swap GUARANTEES
same_spec — the axioms/pure/pre-conditions/post-conditions are never touched).

Defended surface (read model.py + refinement.md + mapping.md):

  count_leading_header_lines(content: PSeq[PSeq[int]]) -> int returns the length
  of the leading run of HEADER lines. A line is a header line iff it has the
  docutils field-marker shape (`is_header_line`, a deep model validated == the
  real `re.compile(Body.patterns['field_marker'])` by axiom_check.py / G-AX).
  The behavioural content of the gold fix: a ``:mod:`foo```-style role heading
  whose closing colon is followed by a back-quote is NOT a header line, so the
  prolog is inserted BEFORE it and the heading survives. The pre-patch
  recogniser `:\\w+:.*?` wrongly accepted it, eating the heading (the bug).

  Load-bearing postcondition: `Result() == leading_header_count(content)`, plus
  the prefix-all-header clause `Forall i<Result(): is_header_line(content[i])`
  and the stop clause `Implies(Result()<len(content),
  not is_header_line(content[Result()]))`.

NO read-only Acc(...,1/2) input: `content` is a PSeq (a pure mathematical
sequence; PSeq carries no permission — see the pre-conditions region). There is
no heap location to overwrite, so the FRAME-MUTATION class is N/A here; this is
justified in the agent's assessment. (Nagini PSeq is immutable-by-construction;
there is no Acc to drop to satisfy a postcondition vacuously.)

The postcondition oracle `leading_header_count(content)` is GROUNDED in the
input (a fully-unfolded @Pure function of `content`), NOT an opaque answer key —
so there is no "wrong echo": echoing it IS the correct answer. The
ungrounded-oracle class is therefore replaced by an honest cheapest-impl
positive control (oracle-echo, expect=verify).

There IS an A-reference deep model (`is_header_line`) but NO consumed
@ContractOnly axiom (the axioms region is empty). The axiom lane re-runs the
G-AX soundness check (deep model == real docutils recogniser) in-container.
"""
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-11445"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r} not found")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The exact gold impl block (text strictly inside # impl-start / # impl-end).
# Every variant below is built by _swap on _BASE, editing ONLY this block — the
# frozen spec is never touched, so same_spec is guaranteed.
_GOLD_IMPL = """    pos = 0
    while pos < len(content) and is_header_line(content[pos]):
        # invariants-start
        Invariant(0 <= pos and pos <= len(content))
        Invariant(Forall(int, lambda i: (
            Implies(0 <= i and i < pos, is_header_line(content[i])),
            [[content[i]]])))
        Invariant(leading_header_count(content) >= pos)
        # The loop consumes the caller's termination obligation with the
        # strictly decreasing, bounded-below measure len(content) - pos: `pos`
        # rises by exactly one per pass and the guard keeps pos < len(content),
        # so the remaining-iteration bound falls by one and stays >= 1 (the + 1
        # matters — the last pass has 0 iterations left and MustTerminate(0) is
        # unsatisfiable).
        Invariant(MustTerminate(len(content) - pos + 1))
        # invariants-end
        lfc_reaches(content, pos + 1)
        pos = pos + 1
    # On exit: the first `pos` lines all have the header-line shape (loop
    # invariant), and either pos == len(content) or content[pos] does not. The
    # postcondition of leading_header_count then pins it to exactly `pos`:
    # lhc >= pos by the lemma, and lhc <= pos because a larger lhc would force
    # content[pos] to have the header-line shape.
    Assert(leading_header_count(content) >= pos)
    lfc_all_markers(content)
    return pos"""


# ---- POSITIVE CONTROL 1 (soundness): the honest cheapest impl — return the
# grounded oracle directly. Structurally maximally different from the gold loop
# (no loop at all). Its postcondition clauses 2-4 follow from
# leading_header_count's own Ensures; clause 1 is trivial. MUST verify.
_POS_ORACLE = """    # Honest cheapest impl: the result is the grounded oracle itself.
    # Bind it to a concrete local `r` so the postcondition reasons over an `int`
    # rather than the recursive @Pure expression in Result()-position (which
    # otherwise sends Z3 chasing unbounded recursive unfoldings of
    # leading_header_count and times out — a proof-search artifact, not a spec
    # rejection). Clauses 2 & 4 then follow directly from leading_header_count's
    # own Ensures on `r`; clause 3 (prefix-all-header) is the lfc_all_markers
    # lemma. None of this changes the spec; it is in-region proof engineering.
    r = leading_header_count(content)
    Assert(0 <= r and r <= len(content))
    Assert(Implies(r < len(content), not is_header_line(content[r])))
    lfc_all_markers(content)
    return r"""

# ---- POSITIVE CONTROL 2 (soundness): a structurally-different but CORRECT loop
# that keeps EVERY gold proof obligation it still needs (the loop invariants,
# the lfc_reaches monotone-lower-bound call, the lfc_all_markers prefix lemma,
# and the final Assert). The only executable change: hoist the per-iteration
# guard into a local boolean `cont` and reshape the loop into a structurally
# distinct `while True / if not cont: break` — the proof obligations are
# identical, so this is a shape change, not a proof-gap change.
_POS_RESHAPE = """    pos = 0
    while pos < len(content):
        # invariants-start
        Invariant(0 <= pos and pos <= len(content))
        Invariant(Forall(int, lambda i: (
            Implies(0 <= i and i < pos, is_header_line(content[i])),
            [[content[i]]])))
        Invariant(leading_header_count(content) >= pos)
        # Same measure as gold: this reshape drops the header test out of the
        # guard, so the counter part `pos < len(content)` is the whole guard and
        # len(content) - pos still strictly falls per pass and stays >= 1. The
        # explicit `break` only exits sooner, which cannot break a bound on the
        # REMAINING iterations.
        Invariant(MustTerminate(len(content) - pos + 1))
        # invariants-end
        # Hoist the per-iteration header test into a local boolean and break
        # explicitly instead of folding it into the while-guard — a structurally
        # distinct forward loop that keeps EVERY gold proof obligation
        # (invariants, lfc_reaches lower bound, lfc_all_markers, final Assert).
        # NOTE: Nagini requires Invariant() to be the FIRST statements of a loop
        # body, so the guard local + break must come AFTER the invariants (a
        # `while True:` with the guard before the invariants is rejected at
        # translation time as invalid.contract.position — a Nagini structural
        # limitation, not a spec rejection).
        cont = is_header_line(content[pos])
        if not cont:
            break
        lfc_reaches(content, pos + 1)
        pos = pos + 1
    Assert(leading_header_count(content) >= pos)
    lfc_all_markers(content)
    return pos"""

# ---- ADMISSIBILITY (expect=verify): a self-call caller that constructs an
# F2P-shaped input (a header line ':a:' i.e. PSeq(58, 97, 58) then a body line)
# and calls count_leading_header_lines on it, asserting the precondition admits
# it. The precondition is trivially True (no Requires), so this must verify;
# if it could not, PRECOND-TOO-STRONG. We keep the gold impl verbatim and add
# the caller AFTER the return is unreachable? No — instead place the admissibility
# probe in the impl as a leading no-op self-call would recurse; safest is a
# separate top-level caller method appended OUTSIDE the modeled function but
# INSIDE the impl region is impossible. Use a dedicated caller variant: replace
# the impl with one that first exercises a concrete in-domain build, then runs
# the gold loop. The concrete PSeq build asserts the input is well-formed.
_ADMISS_IMPL = """    # Admissibility witness: an F2P-shaped header line ':a:' (code points
    # 58,97,58) is a header line, and a body line '-' (45) is not — so the
    # precondition (vacuously True; content is a pure PSeq) admits a normal
    # document. Build the 2-line witness with the proven empty-typed-local
    # idiom (no fragile nested PSeq literal) and SELF-CALL the modeled function
    # on it: the call site must establish the precondition (trivially True),
    # which is exactly the admissibility obligation.
    hdr = PSeq(58, 97, 58)          # ':a:'  -> a header line
    body = PSeq(45)                 # '-'    -> not a header line
    empty = PSeq(PSeq(0)).take(0)   # type: PSeq[PSeq[int]]
    doc = empty + PSeq(hdr) + PSeq(body)   # proven PSeq[PSeq[int]] extend idiom
    Assert(len(doc) == 2 and doc[0] == hdr and doc[1] == body)
    # Self-call: the call site must establish the precondition for this
    # F2P-shaped input — exactly the admissibility obligation. The ONLY
    # precondition is the termination level MustTerminate(len(content) + 2), and
    # Nagini demands a callee level strictly BELOW the caller's, so the self-call
    # is admissible exactly when the witness is shorter than this call's own
    # document: len(doc) + 2 < len(content) + 2. Guarding on `len(doc) <
    # len(content)` is therefore not a dodge — it IS the admissibility statement
    # for a self-call on a strictly smaller document, and it is what forbids the
    # unguarded self-recursion that would discharge every Ensures vacuously. We
    # do NOT assert the recursive oracle's exact value (that would need a manual
    # unfold the verifier need not auto-discharge — AVOID-2); the bound result is
    # constrained only by the callee's postcondition.
    if len(doc) < len(content):
        n = count_leading_header_lines(doc)
        Assert(0 <= n and n <= len(doc))   # from the callee's own postcondition
    # then compute the real answer with the gold loop (kept verbatim).
    pos = 0
    while pos < len(content) and is_header_line(content[pos]):
        # invariants-start
        Invariant(0 <= pos and pos <= len(content))
        Invariant(Forall(int, lambda i: (
            Implies(0 <= i and i < pos, is_header_line(content[i])),
            [[content[i]]])))
        Invariant(leading_header_count(content) >= pos)
        # Gold's measure, kept verbatim: len(content) - pos strictly falls per
        # pass (pos rises by one) and stays >= 1 under the counter guard.
        Invariant(MustTerminate(len(content) - pos + 1))
        # invariants-end
        lfc_reaches(content, pos + 1)
        pos = pos + 1
    Assert(leading_header_count(content) >= pos)
    lfc_all_markers(content)
    return pos"""


# ---- REJECT 1 (uniqueness / partial-domain, OFF-BY-ONE-OVER): count one extra
# line past the header run when the document is longer than the run. Concretely:
# when the loop stops early (pos < len) the counter is advanced once more, so the
# returned value is pos + 1 there and pos otherwise. On the F2P input
# [:title:, :author:, "", :mod:`foo`, ...] the gold count is 2; this returns 3,
# placing the prolog AFTER the empty line — i.e. it would still mis-scan past a
# real boundary in the general case. It breaks clause 1
# (Result != leading_header_count) and the prefix-all-header clause
# `Forall i<Result(): is_header_line(content[i])`, because Result() - 1 indexes
# the first line the scan found NOT to have the header-line shape; and on the
# same path the stop clause `not is_header_line(content[Result()])` is no longer
# established either, Result() now naming the line AFTER that boundary.
#
# WHY THE COUNTER IS ADVANCED IN PLACE (measured, not guessed). The identical
# off-by-one written with a SECOND EXIT —
#
#     if pos < len(content):
#         return pos + 1
#     return pos
#
# — returns the same value for every input, carries the same obligation and
# breaks the same clauses, but the prover does not converge on it: it reached NO
# VERDICT at the 1500s cap this battery was first gated at and again at 5400s,
# while all six of its sibling cases (three positives, three rivals) reach a
# verdict in 42-48s. Advancing the counter and leaving by gold's single exit is
# rejected in 22.6s on clause 1. That is a proof-search shape inside the impl
# region, not a weaker test — and two controls pin the attribution:
#
#   * SHAPE control: the same guard and the same `pos = pos + 1` carrying gold's
#     VALUE (a following `pos = pos - 1`) VERIFIES in 21.3s. So neither the
#     branch nor the increment is what the verifier turns down — the off-by-one
#     value is.
#   * NON-VACUITY control: `Assert(False)` placed INSIDE the
#     `if pos < len(content)` branch FAILS in 18.9s ("Assert might fail.
#     Assertion False might not hold"). The branch is therefore reachable, so
#     this rejection is not the hollow kind an infeasible guard produces.
#   * SAME-OBLIGATION control: silicon reports ONE error per member, so under the
#     full postcondition it names clause 1 and stops, saying nothing about the
#     stop clause the two-exit case also targeted. A probe carrying only the
#     bounds clause and the stop clause answers that separately, and the stop
#     clause breaks too, in 20.6s: "Postcondition of
#     count_leading_header_lines might not hold. Assertion
#     Implies((Result() < len(content)),
#     (not is_header_line(content[Result()]))) might not hold". (The bounds
#     clause has to stay in that probe: without it `content[Result()]` loses its
#     index precondition and the error is about well-formedness rather than
#     about the clause.) So both clauses the two-exit case named are still
#     broken here — this case is not the weaker of the two.
_REJECT_OVER = """    pos = 0
    while pos < len(content) and is_header_line(content[pos]):
        # invariants-start
        Invariant(0 <= pos and pos <= len(content))
        Invariant(Forall(int, lambda i: (
            Implies(0 <= i and i < pos, is_header_line(content[i])),
            [[content[i]]])))
        Invariant(leading_header_count(content) >= pos)
        # Gold's measure, kept verbatim: len(content) - pos strictly falls per
        # pass (pos rises by one) and stays >= 1 under the counter guard.
        Invariant(MustTerminate(len(content) - pos + 1))
        # invariants-end
        lfc_reaches(content, pos + 1)
        pos = pos + 1
    Assert(leading_header_count(content) >= pos)
    lfc_all_markers(content)
    # Swallow one extra line whenever a body follows the header run, and leave
    # by the SINGLE exit gold uses: advance the counter in place rather than
    # returning from a second exit point.
    if pos < len(content):
        pos = pos + 1
    return pos"""

# ---- REJECT 2 (uniqueness / partial-domain, STOP-ONE-EARLY): correct on most
# inputs but caps the count at 1 (counts at most one leading header line). On
# the F2P input with TWO field lines [:title:, :author:, ...] the gold count is
# 2; this returns 1, inserting the prolog between the two field lines. It breaks
# clause 1 (Result != leading_header_count when the run is longer than 1).
_REJECT_CAP1 = """    pos = 0
    while pos < len(content) and is_header_line(content[pos]):
        # invariants-start
        Invariant(0 <= pos and pos <= len(content))
        Invariant(Forall(int, lambda i: (
            Implies(0 <= i and i < pos, is_header_line(content[i])),
            [[content[i]]])))
        Invariant(leading_header_count(content) >= pos)
        # Gold's measure, kept verbatim: len(content) - pos strictly falls per
        # pass (pos rises by one) and stays >= 1 under the counter guard.
        Invariant(MustTerminate(len(content) - pos + 1))
        # invariants-end
        lfc_reaches(content, pos + 1)
        pos = pos + 1
    Assert(leading_header_count(content) >= pos)
    lfc_all_markers(content)
    if pos > 1:
        return 1
    return pos"""

# ---- REJECT 3 (uniqueness / WRONG-PREDICATE = the pre-patch bug): scan using
# an inline ':name:'-prefix recogniser that accepts a line as a header as long
# as it starts with a colon, a non-colon non-space name code point, and contains
# ANY later colon — REGARDLESS of what follows the closing colon. This is
# exactly the pre-patch `docinfo_re = re.compile(':\\w+:.*?')` behaviour: it
# WRONGLY accepts `:mod:`foo`` (closing colon followed by a back-quote). On the
# F2P input it counts the `:mod:`foo`` heading as a header line and over-counts,
# so the prolog is inserted AFTER the heading — eating it, the original bug.
# It cannot prove Result()==leading_header_count(content) (clause 1) nor the
# prefix-all-header clause, because is_header_line REJECTS `:mod:`foo``.
_REJECT_PREPATCH = """    # Inline pre-patch recogniser: a line is accepted iff it begins with a
    # colon, a non-colon non-space name code point, and contains any LATER
    # colon (what follows that colon is ignored) — `:\\w+:.*?`. This accepts
    # `:mod:`foo`` (the discriminator the gold fix rejects).
    #
    # This rival's loops count differently from gold's, so each carries its OWN
    # measure (a nested pair: the two must not share a counter). The document
    # and line lengths are hoisted into int locals `n` / `m` so each measure is
    # a plain linear term over locals — the loops read `content` but never write
    # it, so the hoists are exact, and Z3 discharges the two measure checks in
    # seconds instead of re-deriving len() through the sequence theory on every
    # pass.
    pos = 0
    n = len(content)
    while pos < n:
        # invariants-start
        Invariant(0 <= pos and pos <= n and n == len(content))
        # OUTER measure: `pos` rises by exactly one per pass under the guard
        # pos < n, so n - pos strictly falls and stays >= 1. It must NOT mention
        # the inner counter `j`, which is reset to 2 on every outer pass.
        Invariant(MustTerminate(n - pos + 1))
        # invariants-end
        line = content[pos]
        accept = False
        if len(line) >= 3 and line[0] == COLON and line[1] != COLON and line[1] != SPACE:
            j = 2
            m = len(line)
            while j < m:
                # invariants-start
                Invariant(2 <= j and j <= m and m == len(line))
                # INNER measure, decreasing WITHIN one outer pass: `m` is the
                # current line's fixed length (bound before this loop, never
                # written in it), and `j` either rises by one or jumps to `m` on
                # the early exit, so m - j strictly falls and stays >= 1. It is
                # independent of the outer counter: this loop's bound is the
                # line's length, not a function of how far the outer scan got.
                Invariant(MustTerminate(m - j + 1))
                # invariants-end
                if line[j] == COLON:
                    accept = True
                    j = m
                else:
                    j = j + 1
        if not accept:
            break
        pos = pos + 1
    return pos"""

# ---- REJECT 4 (uniqueness / CONSTANT, cheap supporting near-miss): return a
# constant 0. Correct ONLY when the document has no leading header lines; on the
# F2P input (1+ leading field lines) it is wrong. Breaks clause 1 whenever the
# leading header run is non-empty. (Supporting mechanical case; carries the same
# refinement — a real patch that never counts field lines never advances the
# prolog past them, so docinfo documents regress.)
_REJECT_ZERO = """    # Always return 0 (never count any leading header line).
    return 0"""


SPEC_TESTS = [
    {
        "id": "pos-oracle-echo",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_ORACLE),
        "rationale": "the grounded oracle is the correct answer; the honest "
        "cheapest impl `return leading_header_count(content)` must verify "
        "(clause 1 trivial; clauses 2-4 from leading_header_count's Ensures). "
        "If it cannot, SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-loop-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_RESHAPE),
        "rationale": "a structurally-different forward loop (while-True / "
        "hoisted guard / explicit break) that KEEPS every gold proof obligation "
        "(invariants, lfc_reaches, lfc_all_markers, final Assert). A correct "
        "shape variant must verify; else SPEC-TOO-STRONG. Forward direction "
        "preserved to avoid a front-recursion induction gap (AVOID-3).",
    },
    {
        "id": "admiss-f2p-shaped",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _ADMISS_IMPL),
        "rationale": "the precondition (the termination level "
        "MustTerminate(len(content) + 2); content is a pure PSeq, so there is no "
        "permission or domain clause) must admit an F2P-shaped input: a ':a:' "
        "header line then a '-' body line, with leading_header_count == 1. The "
        "self-call establishes it at the strictly lower level len(doc) + 2 "
        "(guarded by len(doc) < len(content), which is exactly what Nagini's "
        "callee-below-caller rule demands and what forbids the unguarded "
        "self-recursion that would satisfy every Ensures vacuously). If the "
        "witness build / classify fails to verify, PRECOND-TOO-STRONG. Gold loop "
        "kept verbatim after.",
    },
    {
        "id": "reject-off-by-one-over",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJECT_OVER),
        "refinement": "its faithful real patch returns pos+1 whenever the run "
        "stops early, inserting the prolog one line PAST the true boundary — on "
        "any docinfo document it splits the body, so test_prepend_prolog / "
        "test_prepend_prolog_with_roles_in_sections fail (wrong xitems layout). "
        "Does NOT resolve.",
        "rationale": "rejected on postcondition clause 1, verbatim from the "
        "verifier: 'Postcondition of count_leading_header_lines might not hold. "
        "Assertion (Result() == leading_header_count(content)) might not hold' "
        "(model.py:185, 22.6s). The prefix-all-header clause "
        "`Forall i<Result(): is_header_line(content[i])` is broken on the same "
        "path — Result() - 1 indexes the first line the scan found NOT to have "
        "the header-line shape — and the stop clause "
        "`Implies(Result()<len(content), not is_header_line(content[Result()]))` "
        "is no longer established either; silicon reports one error per member, "
        "so clause 1 is the one it names — a probe carrying only the bounds and "
        "stop clauses shows the stop clause breaks as well (20.6s), so both "
        "clauses the original two-exit case named are still broken here. The "
        "off-by-one advances the counter in "
        "place and leaves by gold's single exit BECAUSE the second-exit form "
        "(`return pos + 1`) carries the same obligation and the same returned "
        "value yet reached no verdict at 1500s or at 5400s; see the measurements "
        "and the two attribution controls above _REJECT_OVER.",
    },
    {
        "id": "reject-cap-at-one",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJECT_CAP1),
        "refinement": "its faithful real patch counts at most one leading field "
        "line, so on a two-field-line docinfo block [:title:, :author:, ...] "
        "(exactly test_prepend_prolog_with_roles_in_sections) it inserts the "
        "prolog BETWEEN the two field lines — the xitems layout is wrong. Does "
        "NOT resolve.",
        "rationale": "rejected on postcondition clause 1 "
        "`Result()==leading_header_count(content)`: when the true run length is "
        ">1, capping at 1 cannot equal the oracle.",
    },
    {
        "id": "reject-prepatch-predicate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJECT_PREPATCH),
        "refinement": "this IS the pre-patch recogniser `:\\w+:.*?` (inlined): "
        "it accepts `:mod:`foo`` as a header line because it ignores what "
        "follows the closing colon. On the F2P input it counts the role heading "
        "as a header and inserts the prolog AFTER it — the heading is eaten, "
        "which is the ORIGINAL BUG. test_prepend_prolog_with_roles_in_sections* "
        "fail. Does NOT resolve (this is exactly what model_prepatch.py models, "
        "G-DIFF).",
        "rationale": "rejected on clause 1 + the prefix-all-header clause "
        "`Forall i<Result(): is_header_line(content[i])`: is_header_line "
        "REJECTS `:mod:`foo`` (closing colon followed by a back-quote, not a "
        "space), so a scan that accepts it cannot equal leading_header_count "
        "nor satisfy the prefix clause. This is the load-bearing discriminator "
        "of the whole instance. Its two nested loops each carry their OWN "
        "measure (outer n - pos, inner m - j; neither mentions the other's "
        "counter), so the rejection is attributable to the WRONG PREDICATE and "
        "not to a missing termination proof.",
    },
    {
        "id": "reject-constant-zero",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _REJECT_ZERO),
        "refinement": "its faithful real patch never counts any leading field "
        "line, so the prolog is always inserted at the very top — on a docinfo "
        "document (e.g. test_prepend_prolog) the prolog lands BEFORE :title: / "
        ":author: rather than after, wrong xitems layout. Does NOT resolve. "
        "(Cheap supporting near-miss; carries a real refinement.)",
        "rationale": "rejected on clause 1 whenever the leading header run is "
        "non-empty: 0 != leading_header_count(content).",
    },
]


# ---------------- AXIOM LANE (A-reference deep model, no consumed axiom) ----
# There is NO @ContractOnly axiom (axioms region empty). But there IS an
# A-reference deep model `is_header_line` validated by axiom_check.py / G-AX.
# The axiom-soundness probe re-runs that check IN-CONTAINER against the REAL
# docutils recogniser the gold patch installs
# (`re.compile(Body.patterns['field_marker'])`), executing the callee (NOT
# scraping source — AVOID-4), reading files only as needed with utf-8
# (AVOID-5), and self-contained (imports only stdlib + docutils, the lib the
# gold patch itself imports — NOT the bundle's axiom_check.py, which is not
# mounted in-container, AVOID-6). apply_gold=True so the post-gold library +
# the field_marker pattern are present.

# Embed the deep model + boundary corpus inline (transcribed in lock-step from
# model.py's pure region, identical to axiom_check.py). The probe builds the
# real recogniser and asserts is_header_line == bool(FIELD_NAME_RE.match) on the
# boundary corpus + a randomized fuzz over the back-slash-free, newline-free
# modelled domain. This is BOTH the soundness check (deep model never weaker
# than the real callee) AND the containment check (the model only reaches lines
# in this domain — every checked line is asserted in-domain).
_AX_PROBE = r'''
import random
import re
import sys

try:
    from docutils.parsers.rst.states import Body
except Exception as e:  # pragma: no cover
    print("FATAL: could not import docutils Body:", e)
    sys.exit(2)

# The exact recogniser the gold patch constructs and calls.
FIELD_NAME_RE = re.compile(Body.patterns['field_marker'])

COLON = 58      # ':'
SPACE = 32      # ' '
BACKTICK = 96   # '`'
BACKSLASH = 92  # '\' -- excluded from the modelled domain
NEWLINE = 10    # excluded
CR = 13         # excluded


def first_boundary(line, k):
    n = len(line)
    if k >= n:
        return n
    if line[k] == COLON and (k == n - 1
                             or line[k + 1] == SPACE
                             or line[k + 1] == BACKTICK):
        return k
    return first_boundary(line, k + 1)


def is_header_line(line):
    if len(line) < 2:
        return False
    if line[0] != COLON:
        return False
    if line[1] == COLON or line[1] == SPACE:
        return False
    b = first_boundary(line, 2)
    if b >= len(line):
        return False
    if line[b - 1] == SPACE:
        return False
    return b == len(line) - 1 or line[b + 1] == SPACE


def real_match(s):
    return bool(FIELD_NAME_RE.match(s))


def check_line(s):
    cps = [ord(ch) for ch in s]
    assert BACKSLASH not in cps and NEWLINE not in cps and CR not in cps, (
        "check_line outside modelled domain on %r" % (s,))
    model = is_header_line(cps)
    real = real_match(s)
    assert model == real, (
        "is_header_line deep model UNSOUND on %r: real field_marker gives %r, "
        "deep model gives %r" % (s, real, model))


def main():
    corpus = [
        # F2P / P2P test lines
        ":title: test of SphinxFileInput",
        ":author: Sphinx team",
        ":mod:`foo`",
        ":mod:`mypackage2`",
        "----------",
        "",
        "hello",
        "hello Sphinx world",
        "Sphinx is a document generator",
        # grammar corners
        ":a:", ":a: ", ":a: x", ":a:x", ": bad:", "::bad:",
        ":x::y: z", ":x:`y`: z", ":= : x:", ":name with spaces: value",
        ":ref:`x` and more", "not a field line at all", ":", "::", ":a",
    ]
    for s in corpus:
        check_line(s)

    alphabet = list(" :`\tabxyz_-09.\"'!#=()/@[]~{}|+,;")
    assert "\\" not in alphabet
    assert "\n" not in alphabet and "\r" not in alphabet
    rng = random.Random(11445)
    n_fuzz = 200000
    for _ in range(n_fuzz):
        length = rng.randint(0, 16)
        s = "".join(rng.choice(alphabet) for _ in range(length))
        check_line(s)

    print("G-PBT axiom-soundness OK: is_header_line == docutils field_marker "
          "on %d boundary + %d fuzz inputs (back-slash/newline-free domain); "
          "pattern=%r" % (len(corpus), n_fuzz, Body.patterns['field_marker']))
    sys.exit(0)


if __name__ == "__main__":
    main()
'''


AXIOM_TESTS = [
    {
        "id": "ax-isheaderline-soundness",
        "axiom": "is_header_line",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_PROBE,
        "rationale": "the A-reference deep model is_header_line must EQUAL the "
        "real recogniser the gold patch installs "
        "(re.compile(Body.patterns['field_marker']).match) on every input in "
        "the modelled (back-slash-free, newline-free) domain. The probe EXECUTES "
        "the real callee (not source-scrape), fuzzes the grammar boundaries + "
        "the bug discriminator `:mod:`foo``, and ALSO asserts every checked line "
        "stays in the modelled domain (containment). A mismatch => AXIOM-UNSOUND "
        "(the deep model the proof relies on diverges from the real recogniser). "
        "Mirrors axiom_check.py / G-AX; runs post-gold (apply_gold) so the "
        "field_marker pattern is present.",
    },
]
