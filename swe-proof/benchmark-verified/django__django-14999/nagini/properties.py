# properties.py — PBT falsification battery for django__django-14999.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TEST is a full model.py variant that shares the FROZEN spec exactly
# (region-surgery: only text strictly between `# impl-start` / `# impl-end` is
# ever changed, so spec_view — hence same_spec — is invariant) and swaps the
# impl. Nagini verify + same_spec decide each case.
#
# Defended surface (see model.py / refinement.md / mapping.md); nc is written for
# len(column_relations) and nl for len(link_relations):
#   rename_schema_schedule(before_table:int, after_table:int,
#                          column_relations:List[int],
#                          link_relations:List[int]) -> List[int]
#   Requires Acc(list_pred(column_relations), 1/2)   # both inputs READ-ONLY
#   Requires Acc(list_pred(link_relations), 1/2)
#   Requires MustTerminate(2)                        # must not diverge
#   Ensures  Acc(...) x2 back, Acc(list_pred(Result()))
#   Ensures  Implies(before==after, len(Result())==0)                  # (1) inert
#   Ensures  Implies(before!=after, len>0 and Result()[0]==MAIN_MOVE)  # (2) move first
#   Ensures  Forall i>=1. 0 <= Result()[i] < nc + 2*nl                 # (3) real requests
#   Ensures  Forall 1<=i<j. Result()[i] != Result()[j]                 # (4) never twice
#   Ensures  Implies(before!=after, len(Result()) == 1 + nc + 2*nl)    # (5) exact schedule
#   Ensures  Forall p,q>=1. Result()[p]>=nc and (Result()[p]-nc)%2==0
#            and Result()[q]==Result()[p]+1 ==> p < q                  # (6) move before
#                                                                      #     its own rewrite
#
# The observable is the SCHEDULE OF REQUESTED schema operations, pinned
# POSITIONALLY: each entry says WHAT the request operates on — the move of the
# renamed model's own table (`OP_MAIN_MOVE`), the rewrite of the column relation
# at position i (code i), the move of the link table of the link relation at
# position j (code nc+2*j), or the rewrite of the column INSIDE that same link
# table (code nc+2*j+1). A link relation therefore contributes TWO entries, and
# the schedule carries the order between them. That granularity is what this
# battery exercises, because every coarser reading admits a rival that is not a
# rename:
#   * one-entry-per-dependent -> a schedule that asks to rewrite the column
#                       inside a link table BEFORE that link table has been
#                       moved (`weak-link-pair-swapped`,
#                        `weak-all-rewrites-before-moves`,
#                        `weak-link-pair-swapped-when-two`)
#   * length-only    -> a schedule that never asks for the move of the model's
#                       own table, or never rewrites a dependent
#                       (`weak-drop-main-move-boundary-repaired`,
#                        `weak-drop-dependent-requests`)
#   * kinds-only     -> a schedule that asks for the move LAST, after requests
#                       that address the renamed table under a name it does not
#                       carry yet (`weak-main-move-last`)
#   * lower-bound    -> a schedule that rewrites every column relation twice
#                       (`weak-double-rewrite`)
#   * count-only     -> a schedule of the right length that issues one request
#                       twice and another not at all
#                       (`weak-duplicate-first-skip-last`,
#                        `weak-link-double-move`)
# Each of those is a genuinely wrong rename and each gets its own reject case;
# the soundness controls pin the other side, that the spec does NOT over-pin the
# freedom the real operation has: any order of the column relations
# (`pos-control-reverse-column-order`), any interleaving of the two dependent
# kinds (`pos-control-link-block-first`), no requirement that a link relation's
# two requests be ADJACENT (`pos-control-moves-then-inner-rewrites`), any order
# of the link relations among themselves (`pos-control-links-descending`), and
# any control-flow shape that emits the schedule (`pos-control-guard-inverted`).
#
# The oracle is GROUNDED in the args (equality of the two int identifiers, the
# positions of the two collections, and their lengths); there is no @Pure
# answer-key / marker in the contract, so the echo family has to reach for the
# spec itself, which `echo-selfcall` does. Both collections are half-permission
# read-only inputs, so a frame-mutation reject case is MANDATORY. No
# @ContractOnly axioms (meta.axioms == []; the deep model is A-reference,
# validated by axiom_check.py) => AXIOM_TESTS = [].
from pathlib import Path

INSTANCE = "django__django-14999"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen gold impl region body (verbatim from model.py, strictly inside the
# # impl-start / # impl-end markers). All variants are produced by _swap-ing
# this exact block, so nothing outside the impl region is ever touched.
_GOLD_IMPL = """    result = []  # type: List[int]
    # An unchanged table identifier means there is nothing to do at all.
    if before_table == after_table:
        return result
    # The rename proceeds: ask for the move of the model's own table first.
    result = [OP_MAIN_MOVE]
    nc = len(column_relations)
    nl = len(link_relations)
    # Then one rewrite for each column relation reaching this model.
    i = 0
    while i < nc:
        # invariants-start
        Invariant(Acc(list_pred(column_relations), 1 / 2))
        Invariant(Acc(list_pred(link_relations), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(nc == len(column_relations) and nl == len(link_relations))
        Invariant(0 <= i and i <= nc)
        Invariant(len(result) == 1 + i)
        Invariant(result[0] == OP_MAIN_MOVE)
        Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
                  result[t] == t - 1)))
        Invariant(MustTerminate(nc - i + 1))
        # invariants-end
        result.append(i)
        i = i + 1
    # Then the requests the link relations need, each link relation served in
    # turn: its two codes are nc + 2*j (move that link table) and nc + 2*j + 1
    # (rewrite the column inside that same link table), so walking the codes
    # upward from nc issues, for one link relation after another, that link
    # table's move and then immediately that link table's own column rewrite.
    m = 0
    while m < 2 * nl:
        # invariants-start
        Invariant(Acc(list_pred(column_relations), 1 / 2))
        Invariant(Acc(list_pred(link_relations), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(nc == len(column_relations) and nl == len(link_relations))
        Invariant(0 <= m and len(result) <= 1 + nc + 2 * nl)
        Invariant(len(result) == 1 + nc + m)
        Invariant(result[0] == OP_MAIN_MOVE)
        Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
                  result[t] == t - 1)))
        Invariant(MustTerminate(2 * nl - m + 1))
        # invariants-end
        result.append(nc + m)
        m = m + 1
    # Proof step, not behaviour: these three facts are what the loop invariants
    # above have just established, so they hold wherever control reaches here
    # and they change no schedule. They are what makes the proof converge, as
    # is the second loop's bound being carried by len(result) rather than by m;
    # the G-VERIFY note in meta.json records the measurements behind both.
    Assert(len(result) == 1 + nc + 2 * nl)
    Assert(result[0] == OP_MAIN_MOVE)
    Assert(Forall(int, lambda t: Implies(1 <= t and t < len(result),
           result[t] == t - 1)))
    return result"""

assert _GOLD_IMPL in _BASE, "gold impl block drifted from model.py"


def _impl(body: str) -> str:
    """Build a full module that keeps the frozen spec and swaps only the impl
    region body (the text between # impl-start and # impl-end)."""
    return _swap(_BASE, _GOLD_IMPL, body)


# --- shared impl fragments -------------------------------------------------
# Reused verbatim by the variants whose defect is elsewhere, so that a variant
# differs from gold ONLY in the part its rationale names.

_PREAMBLE = """    result = []  # type: List[int]
    if before_table == after_table:
        return result
    result = [OP_MAIN_MOVE]
    nc = len(column_relations)
    nl = len(link_relations)
"""

# one rewrite per column relation, positions ascending (gold's first loop)
_COLS_ASC = """    i = 0
    while i < nc:
        # invariants-start
        Invariant(Acc(list_pred(column_relations), 1 / 2))
        Invariant(Acc(list_pred(link_relations), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(nc == len(column_relations) and nl == len(link_relations))
        Invariant(0 <= i and i <= nc)
        Invariant(len(result) == 1 + i)
        Invariant(result[0] == OP_MAIN_MOVE)
        Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
                  result[t] == t - 1)))
        Invariant(MustTerminate(nc - i + 1))
        # invariants-end
        result.append(i)
        i = i + 1
"""

# per link relation: the move of its link table, then the rewrite of the column
# inside that same link table (gold's second loop)
_LINKS_ASC = """    m = 0
    while m < 2 * nl:
        # invariants-start
        Invariant(Acc(list_pred(column_relations), 1 / 2))
        Invariant(Acc(list_pred(link_relations), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(nc == len(column_relations) and nl == len(link_relations))
        Invariant(0 <= m and m <= 2 * nl)
        Invariant(len(result) == 1 + nc + m)
        Invariant(result[0] == OP_MAIN_MOVE)
        Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
                  result[t] == t - 1)))
        Invariant(MustTerminate(2 * nl - m + 1))
        # invariants-end
        result.append(nc + m)
        m = m + 1
"""

# gold's link loop, carried after a column block whose entries are only known to
# be positions of column_relations (used by the variants whose column block is
# the defective part)
_LINKS_ASC_AFTER_UNKNOWN_COLS = """    m = 0
    while m < 2 * nl:
        # invariants-start
        Invariant(Acc(list_pred(column_relations), 1 / 2))
        Invariant(Acc(list_pred(link_relations), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(nc == len(column_relations) and nl == len(link_relations))
        Invariant(0 <= m and m <= 2 * nl)
        Invariant(len(result) == 1 + nc + m)
        Invariant(result[0] == OP_MAIN_MOVE)
        Invariant(Forall(int, lambda t: Implies(1 <= t and t < 1 + nc,
                  0 <= result[t] and result[t] < nc)))
        Invariant(Forall(int, lambda t: Implies(
            1 + nc <= t and t < len(result), result[t] == t - 1)))
        Invariant(MustTerminate(2 * nl - m + 1))
        # invariants-end
        result.append(nc + m)
        m = m + 1
"""

_RETURN = "    return result"


# --- shape-guarded concrete schedules --------------------------------------
# A variant that emits a schedule the gold loops cannot produce pays for it in
# PROOF cost, not in expressiveness. Gold's `result[t] == t - 1` closed form is
# what makes its loop invariants cheap; a permuted, truncated or doubled-up link
# block needs a shifted / slope-2 / mod-2 closed form instead, and clause (6)'s
# nested quantifier with the `% 2` parity guard then has to be discharged
# against it. Six such variants (three controls and three rejects) were measured
# at the 900s verifier cap, and for G-PBT a cap hit is not a slow pass but a
# TIMED-OUT gate: the case is judged neither way and it takes the whole battery
# with it (src/swebench_unified/gates/pbt.py). They are written the other way
# round here — the interesting schedule is a CONCRETE list on ONE dependent
# shape, and every other input takes the gold path, so the verifier decides the
# interesting branch by evaluating a 3-to-5 element sequence rather than by
# reasoning about a general closed form. Measured cost of the six: 20s, 26s,
# 50s, 69s, 98s, 103s (rejects) and 207s / 427s (controls), against 900s+ before.
# Nothing is conceded by the narrowing: a rival that is gold everywhere except
# on one dependent shape is a HARDER impl for a spec to reject than one that is
# wrong everywhere (it is the partial-domain family), and the reject cases below
# use the same two shape guards, so their rejection is the standing proof that
# such a branch is REACHABLE and that its postcondition really is evaluated
# there — a positive control here cannot pass by being unreachable.
_HEAD = """    result = []  # type: List[int]
    if before_table == after_table:
        return result
    nc = len(column_relations)
    nl = len(link_relations)
"""

_GOLD_TAIL = "    result = [OP_MAIN_MOVE]\n" + _COLS_ASC + _LINKS_ASC + _RETURN


def _shaped(guard: str, comment: str, entries: str, facts=()) -> str:
    """Gold on every input EXCEPT the dependent shape `guard` names, where the
    schedule is exactly the concrete list `entries`. `facts` are Assert lines
    naming those entries, which keeps the nested clause-(4)/(6) quantifiers from
    having to dig the values back out of the constructed sequence."""
    body = _HEAD + "    if %s:\n%s" % (guard, comment)
    body += "        alt = [%s]  # type: List[int]\n" % entries
    for fact in facts:
        body += "        Assert(%s)\n" % fact
    return body + "        return alt\n" + _GOLD_TAIL


# ---------------------------------------------------------------------------
# POSITIVE CONTROLS (soundness / admissibility) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-control-reverse-column-order: structurally different but CORRECT. The move
# of the model's own table is still requested FIRST, every dependent request is
# still issued exactly once, and each link table is still moved before the
# column inside it is rewritten — but the column relations are taken from the
# LAST position to the first. Confirms the spec does NOT pin the order the
# column relations are taken in among themselves: each of their rewrites is
# addressed to the renamed model's table after that table has already moved, so
# any order of them is a correct rename.
_POS_REVERSE_COLUMNS = _PREAMBLE + """    i = nc
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(column_relations), 1 / 2))
        Invariant(Acc(list_pred(link_relations), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(nc == len(column_relations) and nl == len(link_relations))
        Invariant(0 <= i and i <= nc)
        Invariant(len(result) == 1 + (nc - i))
        Invariant(result[0] == OP_MAIN_MOVE)
        Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
                  result[t] == nc - t)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        result.append(i - 1)
        i = i - 1
    m = 0
    while m < 2 * nl:
        # invariants-start
        Invariant(Acc(list_pred(column_relations), 1 / 2))
        Invariant(Acc(list_pred(link_relations), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(nc == len(column_relations) and nl == len(link_relations))
        Invariant(0 <= m and m <= 2 * nl)
        Invariant(len(result) == 1 + nc + m)
        Invariant(result[0] == OP_MAIN_MOVE)
        Invariant(Forall(int, lambda t: Implies(1 <= t and t < 1 + nc,
                  result[t] == nc - t)))
        Invariant(Forall(int, lambda t: Implies(
            1 + nc <= t and t < len(result), result[t] == t - 1)))
        Invariant(MustTerminate(2 * nl - m + 1))
        # invariants-end
        result.append(nc + m)
        m = m + 1
""" + _RETURN

# pos-control-link-block-first: the two dependent kinds INTERLEAVED the other
# way round — the link relations' requests issued first, the column relations'
# rewrites last, on EVERY dependent shape. Still move-of-own-table first, still
# each request exactly once, still every link table moved before its own column
# is rewritten. Confirms the spec does not pin WHICH dependent kind is served
# first.
#
# This is the one variant that is NOT written as a shape-guarded concrete
# schedule, and the reason is measured rather than stylistic. Its shape-guarded
# form verified in 427s while the module docstring was 20 lines shorter, and
# reached no verdict at the 3600s cap once the SCOPE paragraph landed. The cost
# is not in the guarded branch — evaluating its four-element sequence takes 21s
# on its own — but in the GOLD path underneath it, which is entered under the
# guard's negation `nc != 1 or nl != 1`: pinning gold under exactly that
# disequality takes it from 39s to no verdict at 400s. Two closed forms
# discharged at the end of a single unguarded path (below) cost 40s, so this
# case is carried that way. The five shape-guarded variants that remain are
# each measured green as they stand.
_LINKS_FIRST = """    # The link relations' requests come FIRST -- for one link relation after
    # another, that link table's move (code nc + 2*j) and then the rewrite of
    # the column inside it (code nc + 2*j + 1) -- and only then the column
    # relations' own rewrites.
    m = 0
    while m < 2 * nl:
        # invariants-start
        Invariant(Acc(list_pred(column_relations), 1 / 2))
        Invariant(Acc(list_pred(link_relations), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(nc == len(column_relations) and nl == len(link_relations))
        Invariant(0 <= m and m <= 2 * nl)
        Invariant(len(result) == 1 + m)
        Invariant(result[0] == OP_MAIN_MOVE)
        Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
                  result[t] == nc + t - 1)))
        Invariant(MustTerminate(2 * nl - m + 1))
        # invariants-end
        result.append(nc + m)
        m = m + 1
"""

_COLS_AFTER_LINKS = """    i = 0
    while i < nc:
        # invariants-start
        Invariant(Acc(list_pred(column_relations), 1 / 2))
        Invariant(Acc(list_pred(link_relations), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(nc == len(column_relations) and nl == len(link_relations))
        Invariant(0 <= i and i <= nc)
        Invariant(len(result) == 1 + 2 * nl + i)
        Invariant(result[0] == OP_MAIN_MOVE)
        Invariant(Forall(int, lambda t: Implies(1 <= t and t < 1 + 2 * nl,
                  result[t] == nc + t - 1)))
        Invariant(Forall(int, lambda t: Implies(
            1 + 2 * nl <= t and t < len(result),
            result[t] == t - 1 - 2 * nl)))
        Invariant(MustTerminate(nc - i + 1))
        # invariants-end
        result.append(i)
        i = i + 1
"""

# The two closed forms the loops above have just established, pinned once for
# the nested clause-(4)/(6) quantifiers exactly as model.py's impl region pins
# gold's single one. True on every input that reaches here, so no rival can be
# rejected because of them.
_LINKS_FIRST_FACTS = """    Assert(len(result) == 1 + nc + 2 * nl)
    Assert(result[0] == OP_MAIN_MOVE)
    Assert(Forall(int, lambda t: Implies(1 <= t and t < 1 + 2 * nl,
           result[t] == nc + t - 1)))
    Assert(Forall(int, lambda t: Implies(1 + 2 * nl <= t and t < len(result),
           result[t] == t - 1 - 2 * nl)))
"""

_POS_LINK_BLOCK_FIRST = (_PREAMBLE + _LINKS_FIRST + _COLS_AFTER_LINKS
                         + _LINKS_FIRST_FACTS + _RETURN)

# pos-control-moves-then-inner-rewrites: every link table moved first (all of
# them), and only then the column inside each of them rewritten. On the (no
# column relations, two link relations) shape that is [main move, move link
# table 0 (code 0), move link table 1 (code 2), rewrite the column inside link
# table 0 (code 1), rewrite the column inside link table 1 (code 3)]. Each link
# relation's move still precedes ITS OWN column rewrite, which is all clause (6)
# asks — the two requests of one link relation are NOT required to be adjacent,
# and here they sit two apart. Confirms clause (6) pins an ORDER, not a
# batching: a real operation that moved all the link tables in one pass and
# rewrote their columns in a second pass would still be a correct rename, and
# the spec must admit it. Measured: verifies, 89s.
_POS_MOVES_THEN_REWRITES = _shaped(
    "nc == 0 and nl == 2",
    "        # both link tables moved, and only then the column inside each of\n"
    "        # them rewritten: precedence without adjacency\n",
    "OP_MAIN_MOVE, 0, 2, 1, 3",
    ("len(alt) == 5",
     "alt[0] == OP_MAIN_MOVE and alt[1] == 0 and alt[2] == 2",
     "alt[3] == 1 and alt[4] == 3"))

# pos-control-links-descending: the link relations served from the LAST
# position to the first, each still contributing its link-table move immediately
# followed by that link table's own column rewrite. On the (no column relations,
# two link relations) shape that is [main move, move link table 1 (code 2),
# rewrite the column inside link table 1 (code 3), move link table 0 (code 0),
# rewrite the column inside link table 0 (code 1)]. Confirms clause (6) leaves
# WHICH link relation is served first entirely free, and in particular that its
# parity guard is not accidentally pinning the link order. Measured: verifies,
# 207s even without the Assert lines.
_POS_LINKS_DESCENDING = _shaped(
    "nc == 0 and nl == 2",
    "        # link relation 1's pair, then link relation 0's pair, each with\n"
    "        # its own move ahead of its own rewrite\n",
    "OP_MAIN_MOVE, 2, 3, 0, 1",
    ("len(alt) == 5",
     "alt[0] == OP_MAIN_MOVE and alt[1] == 2 and alt[2] == 3",
     "alt[3] == 0 and alt[4] == 1"))

# pos-control-guard-inverted: the same schedule reached by the opposite
# control-flow shape — no early return at all; the whole proceeding branch sits
# inside `if before_table != after_table:` and the single exit returns whatever
# was built. Behaviourally identical to gold on every input. Confirms the spec
# constrains the SCHEDULE, not the shape of the code that emits it.
_POS_GUARD_INVERTED = """    result = []  # type: List[int]
    nc = len(column_relations)
    nl = len(link_relations)
    if before_table != after_table:
        result = [OP_MAIN_MOVE]
        i = 0
        while i < nc:
            # invariants-start
            Invariant(Acc(list_pred(column_relations), 1 / 2))
            Invariant(Acc(list_pred(link_relations), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(nc == len(column_relations) and nl == len(link_relations))
            Invariant(0 <= i and i <= nc)
            Invariant(len(result) == 1 + i)
            Invariant(result[0] == OP_MAIN_MOVE)
            Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
                      result[t] == t - 1)))
            Invariant(MustTerminate(nc - i + 1))
            # invariants-end
            result.append(i)
            i = i + 1
        m = 0
        while m < 2 * nl:
            # invariants-start
            Invariant(Acc(list_pred(column_relations), 1 / 2))
            Invariant(Acc(list_pred(link_relations), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(nc == len(column_relations) and nl == len(link_relations))
            Invariant(0 <= m and m <= 2 * nl)
            Invariant(len(result) == 1 + nc + m)
            Invariant(result[0] == OP_MAIN_MOVE)
            Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
                      result[t] == t - 1)))
            Invariant(MustTerminate(2 * nl - m + 1))
            # invariants-end
            result.append(nc + m)
            m = m + 1
    return result"""

# admiss: a positive-control body that proves the precondition admits a normal
# F2P-shaped input (equal tables, one column relation AND one link relation —
# the Pony.rider / Pony.stables noop scenario) and that the noop clause is
# satisfiable on it. The asserted facts come straight from the postcondition.
_ADMISS = """    cols = [7]  # type: List[int]
    links = [3]  # type: List[int]
    Assert(Acc(list_pred(cols), 1 / 2))
    Assert(Acc(list_pred(links), 1 / 2))
    Assert(len(cols) == 1 and len(links) == 1)
    # equal identifiers => the postcondition forces an empty schedule (clause 1)
    # even though a column relation AND a link relation are present, and a normal
    # F2P input was admissible at the call site (Requires held).
""" + _PREAMBLE + _COLS_ASC + _LINKS_ASC + _RETURN


# ---------------------------------------------------------------------------
# UNIQUENESS / falsification (SPEC-TOO-WEAK probes) — must be REJECTED.
# ---------------------------------------------------------------------------

# weak-prepatch-bug: the ACTUAL pre-patch defect, on the WHOLE input domain.
# It issues every dependent request unconditionally and only gates the move of
# the model's own table on equality, so on equal tables WITH a dependent present
# it returns a non-empty schedule. This is the defect the issue reports (Postgres
# drops/recreates the FK; sqlite recreates the table). Rejected by clause (1).
# The inert branch emits its dependents with the ascending closed form
# result[t] == t — the same shape gold's loops carry, so it costs the verifier
# nothing; the earlier revision shared ONE loop between the two branches and had
# to carry `result[t] == t - n_moves` for a symbolic n_moves, which is what put
# this case over the cap.
_WEAK_PREPATCH = """    result = []  # type: List[int]
    nc = len(column_relations)
    nl = len(link_relations)
    if before_table == after_table:
        # PRE-PATCH: no top-level table-identity guard, so every dependent
        # request is issued anyway. Only the move of the model's own table is
        # inert here, and only because alter_db_table short-circuits internally.
        k = 0
        while k < nc + 2 * nl:
            # invariants-start
            Invariant(Acc(list_pred(column_relations), 1 / 2))
            Invariant(Acc(list_pred(link_relations), 1 / 2))
            Invariant(Acc(list_pred(result)))
            Invariant(nc == len(column_relations) and nl == len(link_relations))
            Invariant(0 <= k and k <= nc + 2 * nl)
            Invariant(len(result) == k)
            Invariant(Forall(int, lambda t: Implies(0 <= t and t < len(result),
                      result[t] == t)))
            Invariant(MustTerminate(nc + 2 * nl - k + 1))
            # invariants-end
            result.append(k)
            k = k + 1
        return result
""" + _GOLD_TAIL

# weak-link-pair-swapped: THE REFUTATION THE OLD SPEC ADMITTED, reconstructed
# on the request-level carrier. Everything is right — noop guard, move of the
# model's own table first, every dependent request issued exactly once, exact
# length — EXCEPT that on the (one column relation, one link relation) shape the
# rewrite of the column inside the link table (code 2) is asked for BEFORE that
# link table has been moved (code 1). That is atk_9's schedule on the smallest
# shape that exhibits it, and it is the shape the F2P/P2P fixtures actually
# build. On the old one-entry-per-dependent carrier the two requests collapsed
# into a single schedule entry, so this rival was schedule-identical to gold and
# the spec could not see it at all. Rejected by clause (6). Measured: 69s.
_WEAK_PAIR_SWAPPED = _shaped(
    "nc == 1 and nl == 1",
    "        # the column INSIDE link table 0 rewritten (code 2) BEFORE link\n"
    "        # table 0 has been moved (code 1)\n",
    "OP_MAIN_MOVE, 0, 2, 1")

# weak-all-rewrites-before-moves: uses the freedom the spec DOES grant as
# cover. The schedule is a legitimate-looking reordering — the move of the
# model's own table first, then the rewrite of the column inside EVERY link
# table, and only then the link-table moves ([main move, 1, 3, 0, 2] on the two-
# link-relation shape). Every request appears exactly once and the length is
# exact, so only an ORDER clause can see it; and the order it breaks is
# precisely the one clause (6) pins, one level below the main move. Unlike
# weak-link-pair-swapped this violates (6) at a DISTANCE — code 0's move sits
# two entries after its own rewrite, not one — so it also rules out a clause
# that only compared adjacent entries. Rejected by clause (6). Measured: 98s.
_WEAK_REWRITES_FIRST = _shaped(
    "nc == 0 and nl == 2",
    "        # every inner column rewrite (codes 1, 3) before every link-table\n"
    "        # move (codes 0, 2)\n",
    "OP_MAIN_MOVE, 1, 3, 0, 2")

# weak-link-pair-swapped-when-two: the PARTIAL-DOMAIN version of the same
# defect, and the narrowest rival in the battery. Link relation 0 is served
# CORRECTLY (its move, code 0, then its own column rewrite, code 1) and only
# link relation 1's pair is inverted (code 3 before code 2), on the shape that
# has two link relations and nothing else. A fuzzer that only ever builds one
# m2m never sees it, and one that builds two and only checks the first pair
# still does not. Rejected by clause (6). Measured: 103s.
_WEAK_PAIR_SWAPPED_WHEN_TWO = _shaped(
    "nc == 0 and nl == 2",
    "        # link relation 0 served correctly (0 then 1), link relation 1\n"
    "        # inverted (3 before 2)\n",
    "OP_MAIN_MOVE, 0, 1, 3, 2")

# weak-link-double-move: the OVER-APPROXIMATION rival. Every entry is a
# legitimate request, the move of the model's own table is first, the length is
# EXACTLY 1 + nc + 2*nl, and no link table's column rewrite is ever issued
# before its move — clause (6) is satisfied, vacuously for link table 0, whose
# rewrite is not issued at all. It asks for link table 0's move TWICE instead of
# once plus its column rewrite, and serves link relation 1 correctly so that
# only the repeated entry is anomalous. Rejected by clause (4). Measured: 50s.
_WEAK_LINK_DOUBLE_MOVE = _shaped(
    "nc == 0 and nl == 2",
    "        # link table 0 moved TWICE (code 0 twice) and the column inside it\n"
    "        # never rewritten; link relation 1 served correctly\n",
    "OP_MAIN_MOVE, 0, 0, 2, 3")

# weak-link-drop-inner-rewrite: each link table is MOVED but the column inside
# it is never rewritten, so that column keeps naming the renamed model's old
# table. One request per link relation instead of two — which is exactly what a
# spec that gave a link relation a single schedule entry could not distinguish
# from gold. Rejected by clause (5). Measured: 26s.
_WEAK_LINK_DROP_REWRITE = _shaped(
    "nc == 0 and nl == 2",
    "        # both link tables moved (codes 0, 2), neither inner column ever\n"
    "        # rewritten\n",
    "OP_MAIN_MOVE, 0, 2")

# weak-always-emit: drops the noop guard entirely and always requests the move.
# On equal tables it returns [OP_MAIN_MOVE] — violating clause (1). Faithful
# real patch: a database_forwards with NO top-level table-identity guard would
# request the move (and every dependent request) even when the stored table name
# is unchanged => the F2P assertNumQueries(0) fails => does NOT resolve.
_WEAK_ALWAYS = """    result = [OP_MAIN_MOVE]  # type: List[int]
    return result"""

# weak-always-empty: never requests anything. Satisfies clause (1) but violates
# (2) and (5) — a genuinely-renamed table would get NO schema work, so the
# rename never reaches the DB. Faithful real patch: an unconditional early
# return makes every rename a silent noop => the P2P rename-actually-moves-the-
# table expectations fail => does NOT resolve.
_WEAK_EMPTY = """    result = []  # type: List[int]
    return result"""

# weak-partial-domain: correct on every input EXCEPT one sub-domain — it returns
# the empty schedule when before==after OR when after == before + 1, i.e. it
# treats one genuinely-changed pair as a noop. Violates (2)/(5) on that slice.
# Faithful real patch: a guard that mis-classifies one pair of distinct
# db_table identities as "unchanged" skips the real rename for that pair.
_WEAK_PARTIAL = """    result = []  # type: List[int]
    if before_table == after_table:
        return result
    if after_table == before_table + 1:
        # mis-classify this one genuinely-changed pair as a noop (the defect).
        return result
    result = [OP_MAIN_MOVE]
    nc = len(column_relations)
    nl = len(link_relations)
""" + _COLS_ASC + _LINKS_ASC + _RETURN

# weak-main-move-last: THE SHAPE A KINDS-AND-COUNT-ONLY SPEC ADMITS. Keeps the
# noop guard, issues every dependent request exactly once, asks for the move of
# the model's own table exactly once — and asks for it LAST. Every entry is a
# legitimate request and the multiset of requests is exactly gold's; only the
# ORDER differs. Measured on the real tree: the same six SQL statements as gold,
# reordered, with the model's own ALTER TABLE ... RENAME TO moved from first to
# last; the dependent request then addresses the renamed model's table under a
# name nothing carries yet, and run_resolve gives RESOLVED=False with the
# PASS_TO_PASS failure "Tests the RenameModel operation on model with self
# referential FK." => does NOT resolve. Rejected by clause (2).
_WEAK_MOVE_LAST = """    result = []  # type: List[int]
    if before_table == after_table:
        return result
    nc = len(column_relations)
    nl = len(link_relations)
    i = 0
    while i < nc:
        # invariants-start
        Invariant(Acc(list_pred(column_relations), 1 / 2))
        Invariant(Acc(list_pred(link_relations), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(nc == len(column_relations) and nl == len(link_relations))
        Invariant(0 <= i and i <= nc)
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda t: Implies(0 <= t and t < len(result),
                  result[t] == t)))
        Invariant(MustTerminate(nc - i + 1))
        # invariants-end
        result.append(i)
        i = i + 1
    m = 0
    while m < 2 * nl:
        # invariants-start
        Invariant(Acc(list_pred(column_relations), 1 / 2))
        Invariant(Acc(list_pred(link_relations), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(nc == len(column_relations) and nl == len(link_relations))
        Invariant(0 <= m and m <= 2 * nl)
        Invariant(len(result) == nc + m)
        Invariant(Forall(int, lambda t: Implies(0 <= t and t < len(result),
                  result[t] == t)))
        Invariant(MustTerminate(2 * nl - m + 1))
        # invariants-end
        result.append(nc + m)
        m = m + 1
    result.append(OP_MAIN_MOVE)
    return result"""

# weak-double-rewrite: requests the move first, then rewrites EVERY column
# relation TWICE (link relations served as gold). This is what a schedule pinned
# only from BELOW admits (a `len(Result()) >= 1 + nc + 2*nl` bound). Re-issuing a
# rewrite is not harmless repetition: the second one is applied to a table the
# first already rebuilt. Measured on the real tree: run_resolve RESOLVED=False
# with the PASS_TO_PASS failures test_rename_m2m_target_model and
# test_rename_model_with_self_referential_m2m => does NOT resolve. Rejected by
# clause (4) and by clause (5).
_WEAK_DOUBLE_REWRITE = _PREAMBLE + """    i = 0
    while i < nc:
        # invariants-start
        Invariant(Acc(list_pred(column_relations), 1 / 2))
        Invariant(Acc(list_pred(link_relations), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(nc == len(column_relations) and nl == len(link_relations))
        Invariant(0 <= i and i <= nc)
        Invariant(len(result) == 1 + 2 * i)
        Invariant(result[0] == OP_MAIN_MOVE)
        Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
                  0 <= result[t] and result[t] < nc)))
        Invariant(MustTerminate(nc - i + 1))
        # invariants-end
        result.append(i)
        result.append(i)
        i = i + 1
""" + _RETURN

# weak-duplicate-first-skip-last: THE SHAPE A COUNT-ONLY SPEC ADMITS. The move
# is first, every entry after it names a real request, and the schedule has
# exactly the right length — but when there are two or more column relations the
# FIRST is rewritten twice and the LAST is never rewritten at all. So one column
# keeps pointing at the old table while another is rewritten twice. Correct for
# 0 or 1 column relations, which is what makes it a partial-domain rival rather
# than an obviously-broken one. Rejected by clause (4).
_WEAK_DUP_SKIP = _PREAMBLE + """    i = 0
    while i < nc:
        # invariants-start
        Invariant(Acc(list_pred(column_relations), 1 / 2))
        Invariant(Acc(list_pred(link_relations), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(nc == len(column_relations) and nl == len(link_relations))
        Invariant(0 <= i and i <= nc)
        Invariant(len(result) == 1 + i)
        Invariant(result[0] == OP_MAIN_MOVE)
        Invariant(Forall(int, lambda t: Implies(1 <= t and t < len(result),
                  0 <= result[t] and result[t] < nc)))
        Invariant(MustTerminate(nc - i + 1))
        # invariants-end
        if i + 1 == nc and nc > 1:
            # rewrite the first column relation a second time, not the last one
            result.append(0)
        else:
            result.append(i)
        i = i + 1
""" + _LINKS_ASC_AFTER_UNKNOWN_COLS + _RETURN

# weak-drop-main-move-boundary-repaired: keeps the noop guard, issues every
# dependent request, and asks for the move of the model's own table ONLY when
# there are no dependents at all (so the schedule is still non-empty on every
# proceeding input — the boundary "repair" that defeats a bare len>0 clause).
# The refined real code therefore NEVER moves the renamed model's own table
# whenever any dependent exists: the table keeps its old name while migration
# state says otherwise. Measured on the real tree: 25 PASS_TO_PASS failures
# including "Tests the RenameModel operation." => does NOT resolve. Rejected by
# clause (2).
_WEAK_NO_MAIN = """    result = []  # type: List[int]
    if before_table == after_table:
        return result
    nc = len(column_relations)
    nl = len(link_relations)
    i = 0
    while i < nc:
        # invariants-start
        Invariant(Acc(list_pred(column_relations), 1 / 2))
        Invariant(Acc(list_pred(link_relations), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(nc == len(column_relations) and nl == len(link_relations))
        Invariant(0 <= i and i <= nc)
        Invariant(len(result) == i)
        Invariant(Forall(int, lambda t: Implies(0 <= t and t < len(result),
                  result[t] == t)))
        Invariant(MustTerminate(nc - i + 1))
        # invariants-end
        result.append(i)
        i = i + 1
    m = 0
    while m < 2 * nl:
        # invariants-start
        Invariant(Acc(list_pred(column_relations), 1 / 2))
        Invariant(Acc(list_pred(link_relations), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(nc == len(column_relations) and nl == len(link_relations))
        Invariant(0 <= m and m <= 2 * nl)
        Invariant(len(result) == nc + m)
        Invariant(Forall(int, lambda t: Implies(0 <= t and t < len(result),
                  result[t] == t)))
        Invariant(MustTerminate(2 * nl - m + 1))
        # invariants-end
        result.append(nc + m)
        m = m + 1
    if nc + nl == 0:
        result.append(OP_MAIN_MOVE)
    return result"""

# weak-drop-dependent-requests: the mirror-image hole. Keeps the noop guard and
# requests the move of the model's own table, but issues NO dependent request at
# all. Non-empty on every proceeding input, so a length-only spec admits it too.
# Measured on the real tree (main move kept, both dependent loops skipped):
# RESOLVED=False with 4 PASS_TO_PASS failures — "RenameModel renames a
# many-to-many column after a RenameField.", test_rename_m2m_target_model,
# test_rename_model_with_m2m, test_rename_model_with_self_referential_m2m —
# because the auto-created link tables and the FKs pointing at the model keep
# referring to the old table. Rejected by clause (5).
_WEAK_NO_DEPENDENTS = """    result = []  # type: List[int]
    if before_table == after_table:
        return result
    result = [OP_MAIN_MOVE]
    return result"""

# weak-move-as-filler: satisfies the move-first clause and the exact length by
# PADDING with repeated requests to move the model's own table instead of doing
# any dependent work — the move is used as an interchangeable length filler. A
# real rename relocates the model's own table once; asking for it 1 + nc + 2*nl
# times while never touching a dependent both leaves the dependents stale and
# issues moves whose source table no longer exists after the first. Rejected by
# clause (3).
_WEAK_MOVE_FILLER = _PREAMBLE + """    m = 0
    while m < nc + 2 * nl:
        # invariants-start
        Invariant(Acc(list_pred(column_relations), 1 / 2))
        Invariant(Acc(list_pred(link_relations), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(nc == len(column_relations) and nl == len(link_relations))
        Invariant(0 <= m and m <= nc + 2 * nl)
        Invariant(len(result) == 1 + m)
        Invariant(Forall(int, lambda t: Implies(0 <= t and t < len(result),
                  result[t] == OP_MAIN_MOVE)))
        Invariant(MustTerminate(nc + 2 * nl - m + 1))
        # invariants-end
        result.append(OP_MAIN_MOVE)
        m = m + 1
""" + _RETURN

# weak-junk-entries: pads the schedule to the required length with entries that
# name no request at all (a code past the end of the scheme), so the length is
# met without any dependent work being requested. A schedule entry that names
# nothing corresponds to no request the real method can make. Rejected by clause
# (3).
_WEAK_JUNK = _PREAMBLE + """    m = 0
    while m < nc + 2 * nl:
        # invariants-start
        Invariant(Acc(list_pred(column_relations), 1 / 2))
        Invariant(Acc(list_pred(link_relations), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(nc == len(column_relations) and nl == len(link_relations))
        Invariant(0 <= m and m <= nc + 2 * nl)
        Invariant(len(result) == 1 + m)
        Invariant(result[0] == OP_MAIN_MOVE)
        Invariant(MustTerminate(nc + 2 * nl - m + 1))
        # invariants-end
        result.append(nc + 2 * nl + 7)
        m = m + 1
""" + _RETURN

# weak-diverge-on-noop: right schedule on the proceeding branch, but the inert
# branch never returns. Partial correctness alone cannot see this, so the
# MustTerminate(2) obligation in the precondition is what must reject it. A real
# database_forwards that spins on the unchanged-table input wedges the migration
# instead of being a noop (measured: the harness cannot even complete a run).
_WEAK_DIVERGE = """    result = []  # type: List[int]
    nc = len(column_relations)
    nl = len(link_relations)
    if before_table == after_table:
        while True:
            # invariants-start
            Invariant(Acc(list_pred(column_relations), 1 / 2))
            Invariant(Acc(list_pred(link_relations), 1 / 2))
            Invariant(Acc(list_pred(result)))
            # invariants-end
            result = result
    result = [OP_MAIN_MOVE]
""" + _COLS_ASC + _LINKS_ASC + _RETURN

# echo-selfcall: the ECHO family. Instead of computing the schedule it hands the
# question back to the specified function itself, so the postcondition would be
# "established" by assuming it. The contract is grounded (no @Pure answer key to
# read), so this is the only echo available — and the termination obligation is
# what closes it: the callee demands MustTerminate(2), which is not smaller than
# the caller's own measure, so the recursion is not proved to bottom out.
_ECHO_SELFCALL = """    return rename_schema_schedule(before_table, after_table,
                                  column_relations, link_relations)"""

# frame-mutation: MANDATORY (both inputs are Acc(list_pred(...), 1/2),
# read-only). This rival WRITES to a read-only input to "do work" before
# emitting. With only half permission the append cannot verify — it must be
# rejected for INSUFFICIENT PERMISSION, not for a value mismatch (the gold
# invariants/contracts are kept verbatim; only the impl body writes). A
# byte-fuzzer never constructs this. Faithful real patch: a database_forwards
# that MUTATES old_model._meta.related_objects (the dependent collection it is
# only meant to read) is not what the gold does and would corrupt migration
# state => does NOT resolve.
_FRAME_MUT = """    link_relations.append(0)  # WRITE to a read-only (1/2-perm) input
    result = []  # type: List[int]
    if before_table == after_table:
        return result
    result = [OP_MAIN_MOVE]
    return result"""


SPEC_TESTS = [
    {
        "id": "pos-control-reverse-column-order",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REVERSE_COLUMNS),
        "rationale": (
            "a structurally-different but CORRECT impl: the move of the model's "
            "own table is still requested first, each link table is still moved "
            "before the column inside it is rewritten, and every dependent "
            "request is still issued exactly once — but the column relations are "
            "taken from the last position to the first. Must verify: the spec "
            "pins the move-first discipline and the within-link-relation order, "
            "NOT the order the column relations are taken in among themselves. "
            "If it cannot verify the spec has over-pinned that order => "
            "SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-control-link-block-first",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_LINK_BLOCK_FIRST),
        "rationale": (
            "the two dependent KINDS served in the opposite order, on every "
            "shape: the link relations' pairs of requests come first (each link "
            "table's move still immediately ahead of the rewrite of the column "
            "inside it) and the column relations' rewrites come last. Still "
            "correct — every request is addressed to a table that has already "
            "moved — so it must verify; a rejection would mean the spec is "
            "pinning which dependent kind is served first => SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-control-moves-then-inner-rewrites",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_MOVES_THEN_REWRITES),
        "rationale": (
            "all link tables moved in one pass, then the column inside each of "
            "them rewritten in a second pass: on the (no column relations, two "
            "link relations) shape that is [main move, 0, 2, 1, 3]. Every link "
            "relation's move still precedes ITS OWN column rewrite, two entries "
            "away, which is all clause (6) asks, so this must verify. A "
            "rejection would mean clause (6) had accidentally demanded that a "
            "link relation's two requests be ADJACENT — a batching, not an "
            "order => SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-control-links-descending",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_LINKS_DESCENDING),
        "rationale": (
            "the link relations served from the last position to the first, each "
            "still contributing its link-table move immediately followed by that "
            "link table's own column rewrite: on the (no column relations, two "
            "link relations) shape that is [main move, 2, 3, 0, 1]. Must verify: "
            "WHICH link relation is served first is free. A rejection would mean "
            "clause (6)'s parity guard was reading as a constraint on the link "
            "ORDER rather than on the order inside one link relation => "
            "SPEC-TOO-STRONG."),
    },
    {
        "id": "pos-control-guard-inverted",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_GUARD_INVERTED),
        "rationale": (
            "the same schedule with the opposite control-flow shape: no early "
            "return, the whole proceeding branch nested under `before_table != "
            "after_table`, one exit. Behaviourally identical to gold on every "
            "input, so it must verify; a rejection would mean the spec is "
            "pinning the SHAPE of the code rather than the schedule => "
            "SPEC-TOO-STRONG."),
    },
    {
        "id": "admiss-noop-fk-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "an F2P-shaped input (equal table ids, one column relation AND one "
            "link relation = the Pony.rider / Pony.stables noop scenario) is "
            "constructed and shown to satisfy the Requires framing, and the "
            "postcondition then forces len(out)==0 on it. If the Requires "
            "cannot be met for this normal input => PRECOND-TOO-STRONG."),
    },
    {
        "id": "weak-prepatch-bug",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PREPATCH),
        "refinement": (
            "this IS the pre-patch defect: issue every dependent request "
            "unconditionally, gate only the move of the model's own table on "
            "equality. On equal tables with a dependent present it requests "
            "nc + 2*nl schema operations — exactly the Postgres FK "
            "drop/recreate the issue reports. Its faithful real patch (no "
            "top-level guard) FAILS the F2P assertNumQueries(0) => does NOT "
            "resolve. model_prepatch.py reproduces this verbatim."),
        "rationale": (
            "rejected by clause (1) Implies(before==after, len(Result())==0): "
            "with a dependent present the impl returns a non-empty schedule on "
            "the equal branch."),
    },
    {
        "id": "weak-link-pair-swapped",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PAIR_SWAPPED),
        "refinement": (
            "THE RIVAL THE ONE-ENTRY-PER-DEPENDENT SPEC ADMITTED. Noop guard, "
            "move of the model's own table first, every dependent request "
            "exactly once, exact length — but on the (one column relation, one "
            "link relation) shape, which is the shape the F2P/P2P fixtures "
            "actually build, the rewrite of the column in the link table (code "
            "2) is asked for BEFORE that link table has been moved (code 1): "
            "[main move, 0, 2, 1]. Faithful real patch: swap the "
            "alter_db_table(new_m2m_model, ...) at "
            "django/db/migrations/operations/models.py:358-362 with the "
            "alter_field(new_m2m_model, ...) at :365-369. The alter_field is "
            "addressed to the link table under its NEW name, so it runs against "
            "a table that does not exist yet => does NOT resolve. On the old "
            "carrier, where a link relation had a single schedule entry, this "
            "rival was schedule-identical to gold."),
        "rationale": (
            "rejected by clause (6): the entry carrying the link table's move "
            "(code nc+2*j = 1, an EVEN offset from nc=1) sits at index 3, a "
            "LATER index than the entry carrying code nc+2*j+1 = 2 at index 2, "
            "so the required p < q fails."),
    },
    {
        "id": "weak-all-rewrites-before-moves",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_REWRITES_FIRST),
        "refinement": (
            "uses the reordering freedom the spec deliberately GRANTS as cover: "
            "move of the model's own table, then the rewrite of the column "
            "inside every link table, and only then the link-table moves — on "
            "the (no column relations, two link relations) shape, [main move, 1, "
            "3, 0, 2]. The multiset of requests is exactly gold's and every "
            "request appears once, so nothing but an order clause can see it, "
            "and the violation is at a DISTANCE of two rather than between "
            "neighbours. Faithful real patch: hoist the alter_field of "
            "models.py:365-369 out of the per-m2m loop into a pass that runs "
            "before the alter_db_table of :358-362; every link table's column is "
            "then rewritten against a name the table does not carry yet => does "
            "NOT resolve."),
        "rationale": (
            "rejected by clause (6): each link relation's move (code nc+2*j, "
            "i.e. 0 and 2) is emitted in the SECOND pass, at a strictly later "
            "index than its own column rewrite (code nc+2*j+1, i.e. 1 and 3) "
            "emitted in the first — code 0 at index 3 against code 1 at index 1, "
            "and code 2 at index 4 against code 3 at index 2."),
    },
    {
        "id": "weak-link-pair-swapped-when-two",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PAIR_SWAPPED_WHEN_TWO),
        "refinement": (
            "the PARTIAL-DOMAIN guard version of the same defect, and the "
            "narrowest rival in the battery: gold everywhere except on the "
            "exactly-two-link-relations-and-nothing-else shape, where link "
            "relation 0 is served CORRECTLY (its move, code 0, then its own "
            "column rewrite, code 1) and only link relation 1's pair is inverted "
            "— [main move, 0, 1, 3, 2]. Faithful real patch: a per-m2m branch "
            "that only reverses the alter_db_table/alter_field pair of "
            "models.py:358-369 for the m2m relations after the first. Most "
            "fixtures carry a single m2m and a checker that looks only at the "
            "first pair sees nothing, so the slice where it is wrong is a real "
            "but narrow one => does NOT resolve on the multi-m2m tests."),
        "rationale": (
            "rejected by clause (6) on that shape: the entry carrying code nc+2 "
            "(link relation 1's link-table move, offset 2, even) sits at index 4, "
            "one AFTER the entry carrying nc+3 at index 3. The correctly-served "
            "link relation 0 satisfies the clause, so only the second pair "
            "witnesses the violation."),
    },
    {
        "id": "weak-link-double-move",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_LINK_DOUBLE_MOVE),
        "refinement": (
            "the OVER-APPROXIMATION rival: every entry is a legitimate request, "
            "the move is first, the length is EXACTLY 1 + nc + 2*nl, and clause "
            "(6) is satisfied — genuinely for link relation 1, and vacuously for "
            "link relation 0, whose column rewrite is never issued at all. On the "
            "(no column relations, two link relations) shape it asks for link "
            "table 0's move TWICE instead of once plus its column rewrite: [main "
            "move, 0, 0, 2, 3]. Faithful real patch: "
            "replace the alter_field of models.py:365-369 with a second "
            "alter_db_table(new_m2m_model, ...) call; the second rename targets "
            "a table the first already moved and the link column keeps naming "
            "the renamed model's old table => does NOT resolve."),
        "rationale": (
            "rejected by clause (4) Forall 1<=i<j. Result()[i]!=Result()[j]: "
            "indices 1 and 2 both carry code nc+2*0 = 0, so the schedule asks "
            "for one link table's move twice."),
    },
    {
        "id": "weak-link-drop-inner-rewrite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_LINK_DROP_REWRITE),
        "refinement": (
            "each link table is MOVED but the column inside it is never "
            "rewritten — one request per link relation instead of two, which is "
            "precisely what a spec giving a link relation a single schedule "
            "entry cannot tell from gold. On the (no column relations, two link "
            "relations) shape that is [main move, 0, 2]. Faithful real patch: "
            "delete the "
            "alter_field(new_m2m_model, ...) call at "
            "django/db/migrations/operations/models.py:365-369 and keep the "
            "alter_db_table at :358-362. The link table moves, its column keeps "
            "naming the renamed model's old table => the m2m PASS_TO_PASS tests "
            "fail => does NOT resolve."),
        "rationale": (
            "rejected by clause (5) Implies(before!=after, len(Result()) == "
            "1 + nc + 2*nl): the schedule has length 1 + nc + nl = 3 against the "
            "required 5, short by exactly the missing inner rewrites."),
    },
    {
        "id": "weak-main-move-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_MOVE_LAST),
        "refinement": (
            "the ORDER-INVERSION rival one level UP: same noop guard, same "
            "requests, same multiset — one move of the model's own table and "
            "every dependent request once — but the model's own move is "
            "requested LAST. Probed on the real tree with a self-referential FK: "
            "the emitted SQL is gold's six statements reordered, the model's own "
            "ALTER TABLE ... RENAME TO moved from first to last, so the "
            "dependent rewrite rebuilds a table under a name that does not exist "
            "yet and the move then lands on an occupied name; run_resolve "
            "RESOLVED=False, PASS_TO_PASS failure 'Tests the RenameModel "
            "operation on model with self referential FK.' => does NOT resolve."),
        "rationale": (
            "rejected by clause (2) Implies(before!=after, len(Result())>0 and "
            "Result()[0]==OP_MAIN_MOVE): with nc + nl >= 1 the first entry is a "
            "dependent request, not the move (and the trailing move violates "
            "clause (3) as well)."),
    },
    {
        "id": "weak-double-rewrite",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DOUBLE_REWRITE),
        "refinement": (
            "the LOWER-BOUND rival: move first, then every column relation "
            "rewritten TWICE (and, since it stops there, the link relations left "
            "alone). Admitted by any spec that bounds the schedule only from "
            "below. Measured on the real tree: run_resolve RESOLVED=False with "
            "PASS_TO_PASS failures test_rename_m2m_target_model and "
            "test_rename_model_with_self_referential_m2m — a second rewrite is "
            "applied to a table the first one already rebuilt => does NOT "
            "resolve."),
        "rationale": (
            "rejected by clause (4) (the two entries emitted for one column "
            "relation carry the same code) and by clause (5) (length "
            "1 + 2*nc != 1 + nc + 2*nl)."),
    },
    {
        "id": "weak-duplicate-first-skip-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DUP_SKIP),
        "refinement": (
            "the COUNT-ONLY rival: right length, right kinds, move first, link "
            "relations served exactly as gold — but with two or more column "
            "relations it rewrites the FIRST twice and the LAST never. The "
            "refined real code rewrites one FK column twice and leaves another "
            "pointing at the renamed model's old table, which is the union of "
            "the weak-double-rewrite and weak-drop-dependent-requests failure "
            "modes => does NOT resolve. Correct for 0 or 1 column relations, so "
            "only a spec that names WHICH dependent each request operates on "
            "can see it."),
        "rationale": (
            "rejected by clause (4) Forall 1<=i<j. Result()[i]!=Result()[j]: on "
            "nc >= 2 the code 0 appears at index 1 and again at index nc."),
    },
    {
        "id": "weak-always-emit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ALWAYS),
        "refinement": (
            "no noop guard at all — always requests the move. A real "
            "database_forwards without the top-level table-identity guard "
            "requests schema work even on an unchanged table => F2P "
            "assertNumQueries(0) fails => does NOT resolve."),
        "rationale": (
            "rejected by clause (1): on before==after it returns a length-1 "
            "schedule (and by clause (5) once a dependent exists)."),
    },
    {
        "id": "weak-always-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_EMPTY),
        "refinement": (
            "always a noop — never requests schema work even on a genuine "
            "rename. A real database_forwards that unconditionally returns "
            "early would make EVERY rename a silent noop => the table is never "
            "actually moved => the P2P rename tests fail => does NOT resolve."),
        "rationale": (
            "rejected by clause (2) (on the proceeding branch len(Result()) is "
            "0, so there is no first entry holding the move) and by clause (5)."),
    },
    {
        "id": "weak-partial-domain",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PARTIAL),
        "refinement": (
            "correct on the whole input domain EXCEPT one slice (after==before+1), "
            "where it mis-treats a genuinely-changed table as a noop and requests "
            "nothing. A real guard that aliased one distinct pair of db_table "
            "identities to 'unchanged' would skip the real rename for that pair => "
            "the F2P/P2P for that genuine rename fail => does NOT resolve."),
        "rationale": (
            "rejected by clauses (2)/(5): on before_table=0, after_table=1 "
            "(before!=after) it returns the empty schedule, so there is no "
            "leading move entry and the length is wrong."),
    },
    {
        "id": "weak-drop-main-move-boundary-repaired",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NO_MAIN),
        "refinement": (
            "keeps the noop guard, issues every dependent request, but asks for "
            "the move of the renamed model's OWN table only when there are no "
            "dependents — so the schedule is non-empty on every proceeding input "
            "while the model's table is never actually moved whenever any "
            "dependent exists. Probed on the real tree: the rename emits SQL but "
            "not the ALTER TABLE ... RENAME TO of the model's own table; "
            "run_resolve gives RESOLVED=False with 25 PASS_TO_PASS failures "
            "including 'Tests the RenameModel operation.' => does NOT resolve. "
            "This is precisely the rival a length-only clause admits, which is "
            "why the move is pinned positionally."),
        "rationale": (
            "rejected by clause (2): with nc + nl >= 1 the first entry is a "
            "dependent request and no entry is OP_MAIN_MOVE at all, so no move "
            "is requested."),
    },
    {
        "id": "weak-drop-dependent-requests",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NO_DEPENDENTS),
        "refinement": (
            "the mirror-image rival: keeps the noop guard and requests the move "
            "of the model's own table, but issues no dependent request at all. "
            "Non-empty on every proceeding input, so a length-only clause admits "
            "it. Measured on the real tree (main move kept, both dependent loops "
            "skipped): RESOLVED=False, 4 PASS_TO_PASS failures — 'RenameModel "
            "renames a many-to-many column after a RenameField.', "
            "test_rename_m2m_target_model, test_rename_model_with_m2m, "
            "test_rename_model_with_self_referential_m2m — because the "
            "auto-created link tables and the FKs pointing at the model keep "
            "referring to the old table => does NOT resolve."),
        "rationale": (
            "rejected by clause (5) Implies(before!=after, len(Result()) == "
            "1 + nc + 2*nl): on nc + nl >= 1 the schedule has length 1."),
    },
    {
        "id": "weak-move-as-filler",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_MOVE_FILLER),
        "refinement": (
            "satisfies the move-first clause and the exact length by REPEATING "
            "the request to move the model's own table instead of doing any "
            "dependent work. A real rename relocates that one table once; "
            "repeating it while never touching a dependent leaves every "
            "dependent stale (the weak-drop-dependent-requests failure mode) and "
            "additionally issues moves whose source table no longer exists after "
            "the first => does NOT resolve."),
        "rationale": (
            "rejected by clause (3) Forall i>=1. 0 <= Result()[i] < nc + 2*nl: "
            "every padding entry is OP_MAIN_MOVE, which is negative and so names "
            "no dependent request."),
    },
    {
        "id": "weak-junk-entries",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_JUNK),
        "refinement": (
            "pads the schedule to the required length with entries that name no "
            "request (a code past the end of the scheme), so the length is met "
            "without any dependent work being requested. A schedule entry naming "
            "nothing corresponds to no request the real method can make of the "
            "schema layer; the dependents are left stale exactly as in "
            "weak-drop-dependent-requests => does NOT resolve."),
        "rationale": (
            "rejected by clause (3): the padding entry is nc + 2*nl + 7, which "
            "is not a code of the scheme."),
    },
    {
        "id": "weak-diverge-on-noop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_DIVERGE),
        "refinement": (
            "right requests on the proceeding branch, but the inert branch "
            "never returns. A real database_forwards that spins on the "
            "unchanged-table input wedges the migration rather than being a "
            "noop; the F2P assertNumQueries(0) never completes => does NOT "
            "resolve. Partial correctness alone cannot see this, so this case "
            "is what makes the MustTerminate(2) precondition load-bearing."),
        "rationale": (
            "rejected by the TERMINATION obligation: Requires(MustTerminate(2)) "
            "must be discharged, and the unguarded `while True` on the inert "
            "branch carries no decreasing measure."),
    },
    {
        "id": "echo-selfcall",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_ECHO_SELFCALL),
        "refinement": (
            "the ECHO rival: it computes nothing and hands the question back to "
            "the specified function, so the postcondition would be discharged by "
            "assuming it. Refined into the real tree this is "
            "database_forwards delegating to itself — a method that issues no "
            "schema operation and does not return => does NOT resolve. The "
            "contract is grounded in the arguments (no @Pure answer key sits in "
            "it), so this is the only echo the surface offers."),
        "rationale": (
            "rejected by the TERMINATION obligation: the self-call demands "
            "MustTerminate(2), which is not smaller than the caller's own "
            "measure, so the recursion is not proved to bottom out and the "
            "obligation cannot be discharged."),
    },
    {
        "id": "frame-mutation-write-link-relations",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT),
        "refinement": (
            "writes to the read-only `link_relations` input (Acc(...,1/2)) to "
            "'do work'. A real database_forwards that mutates the dependent "
            "collection (old_model._meta.related_objects / the m2m field list) "
            "it is only meant to read would corrupt migration state and is not "
            "what the gold does => does NOT resolve. A byte-fuzzer never "
            "constructs an input-mutating rival."),
        "rationale": (
            "rejected by the PERMISSION SYSTEM: link_relations.append needs full "
            "list_pred(link_relations) write permission, but Requires grants "
            "only Acc(list_pred(link_relations), 1/2) — INSUFFICIENT PERMISSION "
            "(and the Ensures Acc(list_pred(link_relations),1/2) framing is kept "
            "verbatim, so the rejection is attributable to the write, not a "
            "value mismatch)."),
    },
]


# No @ContractOnly axioms and no consumed axiom (meta.axioms == []). The deep
# model is A-reference, validated by axiom_check.py / G-AX against the real
# RenameModel.database_forwards/backwards at the granularity of the schema
# operations REQUESTED of the schema layer — one entry per request, so a link
# relation's link-table move and the rewrite of the column inside it are two
# separate entries whose order the schedule carries. There is no axiom
# obligation for PBT to probe.
AXIOM_TESTS = []
