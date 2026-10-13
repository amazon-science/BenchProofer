# properties.py — PBT falsification battery for astropy__astropy-14539.
#
# NOT a Nagini module. A manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS entry is a full model.py variant built by region-surgery (a single
# _swap inside the # impl-start/# impl-end region) so the FROZEN spec
# (axioms/pure/pre-conditions/post-conditions) is never touched — same_spec is
# guaranteed.
#
# Defended surface (read from model.py + refinement.md + meta.json):
#   * count_differing_rows(fmt, close_mismatches, unequal_mismatches,
#     rows_hold_subarrays) — the modelled behaviour: the figure a column
#     contributes is the number of slots rejected by the verdict of the
#     comparator GOVERNING that column. WHICH comparator governs a column is
#     settled by HOW ITS ROWS ARE STORED — the observation `rows_hold_subarrays`
#     of the materialised pair of columns, pinned against the real storage test
#     by conformance_check.py (G-CONF) and axiom_check.py (G-AX) — and by nothing
#     else. A column whose rows hold sub-arrays of their own is governed by the
#     row-aware comparator, whose per-position CLOSENESS verdict is summarised in
#     close_mismatches; every other column is governed by the element-wise
#     comparator, whose plain INEQUALITY verdict is summarised, per leading-axis
#     slot of the block comparison it performs, in unequal_mismatches. The three
#     sequence arguments are READ-ONLY (Acc(., 1/2)).
#   * The routing observation is a DATA INPUT, not an opaque symbol. That is the
#     load-bearing change from the earlier revision of this bundle: when the
#     routing predicate was an unconstrained @ContractOnly axiom, an impl could
#     dispatch on the symbol itself and satisfy both clauses vacuously, then
#     instantiate the symbol as the pre-patch descriptor test in refinement. With
#     the routing keyed on an input, an impl that decides from the DESCRIPTOR
#     CARRIER instead of the storage observation reports the non-governing
#     verdict's figure on every column where the two disagree, and the
#     postcondition catches it. `route-by-descriptor-carrier` below is exactly
#     that rival, and it is the one the prepatch twin also fails on.
#   * BOTH clauses are unconditional on their side of the routing: no side
#     condition on framing, lengths, or the descriptor guards either one. The
#     element-wise comparator attributes every reported position to a
#     leading-axis slot of the block comparison whatever the two sides' framing,
#     so its figure is a slot count in every case and no column is left with an
#     unclaimed figure. `carve-out-when-frames-differ` below is the rival that
#     exploits such a carve-out; it MUST be rejected, and a future revision that
#     reintroduces a framing side condition would let it verify.
#   * The two summaries are indexed INDEPENDENTLY (each by its own comparator's
#     slots), so NO relation between their lengths is required, and they are
#     INCOMPARABLE in value: no ordering between them is required in EITHER
#     direction, because neither real per-position verdict refines the other (the
#     closeness verdict cannot separate neighbouring values of the 64-bit range,
#     and it rejects a position whose two values are the same
#     non-finite-component value, which the inequality test does not report).
#     They are two independent observations, so WHICH summary a column's figure
#     is taken from is observable IN THE FIGURE: sending a column to the wrong
#     comparator is a wrong VALUE, not an invisible internal choice. Every reject
#     case below exploits exactly that, which is why none needs a
#     comparator-applicability precondition to be caught — and why none may
#     ASSUME an ordering or a shared length to build its wrongness from.
#   * MustTerminate(2) — the figure must actually be delivered. A body that
#     diverges before returning satisfies a partial-correctness reading of the
#     postcondition while never producing the count, so non-termination is a
#     reject case in its own right.
#
# The postcondition oracle `row_granular_count` is GROUNDED: a @Pure
# front-recursive fold over the argument summaries, unfolded by the loop
# invariant total == row_granular_count(ToSeq(<summary>).drop(i)). It is a
# function of the arguments, not an opaque answer key — but with TWO summaries in
# scope an echo can still fold the WRONG one, so the ungrounded-oracle class is
# exercised here (echo-wrong-summary, sum-of-both-summaries) rather than N/A.
#
# There are NO consumed @ContractOnly axioms: the axioms region is EMPTY, which
# is the point. `row_granular_count`, `contains_cp` and each of the two
# per-position verdicts are A-references validated against the REAL callees.
# AXIOM_TESTS mirrors that soundness in-container — including the routing
# observation's own grounding (the storage test, NOT the descriptor spelling),
# the leading-axis grounding of the element-wise summary on columns whose two
# sides are framed differently, and the INCOMPARABILITY of the two summaries
# (each direction of a would-be ordering is refuted by a real column, so the spec
# may not assume either).
from pathlib import Path

INSTANCE = "astropy__astropy-14539"
FLOAT_ENCODING = None  # meta.json float_encoding is null (integer data, zero tolerances)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: %r" % (old,))
    if src.count(old) != 1:
        raise AssertionError("not unique: %r" % (old,))
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The gold impl of count_differing_rows, VERBATIM: the whole of its impl
# region. Every rival below replaces exactly this block, so the frozen spec
# regions are untouched and same_spec holds — and if model.py's impl text ever
# drifts, _swap raises at import instead of silently testing nothing.
# ---------------------------------------------------------------------------
_GOLD_IMPL = """    # How the column's rows are STORED selects the governing verdict, and the
    # column's figure is that verdict's summary folded row-granularly: a column
    # whose rows hold sub-arrays of their own counts the rows its closeness
    # summary rejects, every other column the leading-axis slots its
    # plain-inequality summary reports.
    total = 0
    if rows_hold_subarrays:
        i = len(close_mismatches)
        while i > 0:
            # invariants-start
            Invariant(Acc(list_pred(fmt), 1 / 2))
            Invariant(Acc(list_pred(close_mismatches), 1 / 2))
            Invariant(Acc(list_pred(unequal_mismatches), 1 / 2))
            Invariant(0 <= i and i <= len(close_mismatches))
            Invariant(total >= 0)
            Invariant(Forall(int, lambda k:
                (Implies(0 <= k and k < len(close_mismatches),
                         close_mismatches[k] >= 0),
                 [[close_mismatches[k]]])))
            Invariant(total ==
                      row_granular_count(ToSeq(close_mismatches).drop(i)))
            # The loop consumes the caller's termination obligation with the
            # strictly decreasing, bounded-below measure i, discharging
            # MustTerminate(2) from the precondition.
            Invariant(MustTerminate(i + 1))
            # invariants-end
            Assert(ToSeq(close_mismatches).drop(i - 1)[0] ==
                   close_mismatches[i - 1])
            Assert(ToSeq(close_mismatches).drop(i - 1).drop(1) ==
                   ToSeq(close_mismatches).drop(i))
            if close_mismatches[i - 1] > 0:
                total = total + 1
            i = i - 1
    else:
        j = len(unequal_mismatches)
        while j > 0:
            # invariants-start
            Invariant(Acc(list_pred(fmt), 1 / 2))
            Invariant(Acc(list_pred(close_mismatches), 1 / 2))
            Invariant(Acc(list_pred(unequal_mismatches), 1 / 2))
            Invariant(0 <= j and j <= len(unequal_mismatches))
            Invariant(total >= 0)
            Invariant(Forall(int, lambda k:
                (Implies(0 <= k and k < len(unequal_mismatches),
                         unequal_mismatches[k] >= 0),
                 [[unequal_mismatches[k]]])))
            Invariant(total ==
                      row_granular_count(ToSeq(unequal_mismatches).drop(j)))
            # Same decreasing measure on the other branch's fold.
            Invariant(MustTerminate(j + 1))
            # invariants-end
            Assert(ToSeq(unequal_mismatches).drop(j - 1)[0] ==
                   unequal_mismatches[j - 1])
            Assert(ToSeq(unequal_mismatches).drop(j - 1).drop(1) ==
                   ToSeq(unequal_mismatches).drop(j))
            if unequal_mismatches[j - 1] > 0:
                total = total + 1
            j = j - 1
    return total"""


# ---------------------------------------------------------------------------
# The pieces every rival is built from. Each rival is given MAXIMAL proof power
# on purpose: a rejection that comes from a proof gap attributes nothing to the
# spec, so every rival gets the read permissions re-stated across its loop and
# the descriptor recognition carried across it (the descriptor is read-only, so
# this is always provable). What no rival may be granted is an ordering between
# the two summaries: the real per-position verdicts are incomparable, so a rival
# built on such an assumption would be refuted by real data rather than by the
# spec. What is left when the provable power is granted is the figure itself.
# ---------------------------------------------------------------------------
_PERMS = """            Invariant(Acc(list_pred(fmt), 1 / 2))
            Invariant(Acc(list_pred(close_mismatches), 1 / 2))
            Invariant(Acc(list_pred(unequal_mismatches), 1 / 2))
"""
_PIN = "            Invariant(vla == rows_hold_subarrays)\n"
# The two summaries are indexed independently, so the spec does NOT say their
# lengths agree. A rival that wants to read across them must therefore GUARD the
# read itself rather than carry an equality it is not given. _LENGUARD is that
# guard, carried as an invariant a rival establishes for itself by testing the
# two lengths in its own body — no unowned cross-summary fact is handed out.
_LENGUARD = "            Invariant(len(unequal_mismatches) > 0)\n"


def _nonneg(lst):
    return ("""            Invariant(Forall(int, lambda k:
                (Implies(0 <= k and k < len(%s),
                         %s[k] >= 0),
                 [[%s[k]]])))
""" % (lst, lst, lst))


def _fold(lst, idx, body=None, extra_inv="", keep_rel=True, stop=0):
    """A row-granular fold over `lst`, indexed from the back by `idx`."""
    body = body if body is not None else ("""            if %s[%s - 1] > 0:
                total = total + 1
""" % (lst, idx))
    rel = ""
    if keep_rel:
        rel = ("            Invariant(total == row_granular_count(ToSeq(%s)"
               ".drop(%s)))\n" % (lst, idx))
    return ("""        %s = len(%s)
        while %s > %d:
            # invariants-start
%s%s            Invariant(0 <= %s and %s <= len(%s))
            Invariant(total >= 0)
%s%s%s            Invariant(MustTerminate(%s + 1))
            # invariants-end
            Assert(ToSeq(%s).drop(%s - 1)[0] == %s[%s - 1])
            Assert(ToSeq(%s).drop(%s - 1).drop(1) == ToSeq(%s).drop(%s))
%s            %s = %s - 1
""" % (idx, lst, idx, stop, _PERMS, _PIN, idx, idx, lst, _nonneg(lst),
       extra_inv, rel, idx, lst, idx, lst, idx, lst, idx, lst, idx, body, idx,
       idx))


def _dedent(t):
    return "".join((ln[4:] if ln.startswith("    ") else ln) + "\n"
                   for ln in t.split("\n")[:-1])


def _pin_local(t, name, expr):
    """Re-phrase the carried recognition in terms of a rival's own local."""
    return t.replace("Invariant(vla == rows_hold_subarrays)",
                     "Invariant(%s == %s)" % (name, expr))


_HEAD = "    total = 0\n    vla = rows_hold_subarrays\n"


# === POSITIVE CONTROL (soundness) ==========================================
# Structurally different but CORRECT: test the descriptor once into a local and
# write the ORDINARY-column branch first, the variable-length branch second (the
# opposite of gold's order). Each kind of column still reports the figure of the
# verdict that governs it. MUST verify; if it cannot => SPEC-TOO-STRONG.
_POS_REORDER = (
    "    total = 0\n"
    "    ordinary = not rows_hold_subarrays\n"
    "    if ordinary:\n"
    + _pin_local(_fold("unequal_mismatches", "j"), "ordinary",
                 "(not rows_hold_subarrays)")
    + "    else:\n"
    + _pin_local(_fold("close_mismatches", "i"), "ordinary",
                 "(not rows_hold_subarrays)")
    + "    return total")

# === POSITIVE CONTROL 2 / ADMISSIBILITY ====================================
# The recognition bound to a local boolean, gold's branch order kept. Doubles as
# admissibility: the precondition must accept an ordinary F2P-shaped column (two
# independent summaries of the same rows) and return its figure. MUST verify.
_POS_LOCAL = (_HEAD
              + "    if vla:\n" + _fold("close_mismatches", "i")
              + "    else:\n" + _fold("unequal_mismatches", "j")
              + "    return total")

# === POSITIVE CONTROL 3 (soundness) ========================================
# A correct impl that reaches the same figure by a DIFFERENT route: fold BOTH
# summaries unconditionally into two separate accumulators, and only THEN consult
# the descriptor to decide which of the two figures to hand back. The routing
# therefore happens AFTER the work rather than selecting it, which is a shape the
# gold does not use — so this control checks the spec pins the FIGURE a column
# reports and not the order in which an impl decides and computes. MUST verify.
# (It replaces an earlier control that counted the rows BOTH verdicts reject.
# That one was correct only under an ordering between the two summaries, and the
# real per-position verdicts are incomparable — the closeness verdict rejects a
# same-valued non-finite-component position that the inequality test passes — so
# a rival of that shape is wrong on real columns and cannot serve as a control.)
def _fold_into(lst, idx, acc, other, carry=""):
    """gold's back-to-front fold, accumulating into a named local `acc`. Carries
    the OTHER summary's non-negativity across the loop as well, plus any `carry`
    fact: this rival runs the two folds in sequence, so every fact a later step
    needs must survive the earlier loop (neither a precondition fact nor an
    already-established result is automatically preserved across a loop that
    does not restate it)."""
    return (_fold(lst, idx,
                  extra_inv=_nonneg(other) + carry,
                  body=("            if %s[%s - 1] > 0:\n"
                        "                %s = %s + 1\n" % (lst, idx, acc, acc)))
            .replace("Invariant(total >= 0)", "Invariant(%s >= 0)" % acc)
            .replace("Invariant(%s == row_granular_count(ToSeq(%s).drop(%s)))"
                     % ("total", lst, idx),
                     "Invariant(%s == row_granular_count(ToSeq(%s).drop(%s)))"
                     % (acc, lst, idx)))


_POS_BOTH_THEN_SELECT = (
    "    total = 0\n"
    "    n_close = 0\n"
    "    n_unequal = 0\n"
    # Both folds run at the top level of the body, so each dedents by one step
    # and each takes its own MustTerminate measure directly under the caller's
    # MustTerminate(2). _PIN is dropped: there is no `vla` local to carry, since
    # the descriptor is not consulted until after both folds are done.
    + _dedent(_fold_into("close_mismatches", "i", "n_close",
                         "unequal_mismatches").replace(_PIN, ""))
    # The second loop must carry the FIRST fold's finished value, or the closeness
    # clause is unprovable at the return even though n_close was computed right.
    + _dedent(_fold_into(
        "unequal_mismatches", "j", "n_unequal", "close_mismatches",
        carry="            Invariant(n_close == "
              "row_granular_count(ToSeq(close_mismatches)))\n").replace(_PIN, ""))
    + "    if rows_hold_subarrays:\n"
    "        total = n_close\n"
    "    else:\n"
    "        total = n_unequal\n"
    "    return total")

# === POSITIVE CONTROL 4 (soundness) ========================================
# No loop at all: hand back the governing verdict's fold directly. A correct
# impl in a shape the gold does not use, so it checks that the spec pins the
# FIGURE rather than the gold's way of arriving at it. MUST verify.
_POS_ECHO_RIGHT = (
    "    if rows_hold_subarrays:\n"
    "        return row_granular_count(ToSeq(close_mismatches))\n"
    "    return row_granular_count(ToSeq(unequal_mismatches))")


# === MISROUTE: always the plain-inequality figure (uniqueness) ==============
# The maximally broken routing, and the shape a rival is reduced to once it can
# no longer fabricate a descriptor to test: fold the element-wise comparator's
# summary whatever the column is. A variable-length column then reports the
# figure of a verdict that does not govern it.
_ALWAYS_UNEQUAL = (_HEAD + _dedent(_fold("unequal_mismatches", "j"))
                   + "    return total")

# === MISROUTE: always the closeness figure (uniqueness) =====================
# The reverse misroute. Right on variable-length columns, wrong on every
# ordinary column whose two verdicts differ.
_ALWAYS_CLOSE = (_HEAD + _dedent(_fold("close_mismatches", "i"))
                 + "    return total")

# === RECOGNITION NARROWED TO THE 32-BIT DESIGNATOR (uniqueness) =============
# The pre-patch bug, made adversarial: recognise only code point 80, so a column
# carrying the OTHER variable-length designator reports the plain-inequality
# figure instead of the closeness figure that governs it.
_PONLY = (
    "    total = 0\n"
    "    vla = contains_cp(ToSeq(fmt), 80)\n"
    "    if vla:\n"
    + _pin_local(_fold("close_mismatches", "i"), "vla",
                 "contains_cp(ToSeq(fmt), 80)")
    + "    else:\n"
    + _pin_local(_fold("unequal_mismatches", "j"), "vla",
                 "contains_cp(ToSeq(fmt), 80)")
    + "    return total")

# === RECOGNITION NARROWED TO THE 64-BIT DESIGNATOR (uniqueness) =============
# The mirror image: recognise only code point 81, so a column carrying the
# 32-bit designator loses the row-aware treatment it already had.
_QONLY = (
    "    total = 0\n"
    "    vla = contains_cp(ToSeq(fmt), 81)\n"
    "    if vla:\n"
    + _pin_local(_fold("close_mismatches", "i"), "vla",
                 "contains_cp(ToSeq(fmt), 81)")
    + "    else:\n"
    + _pin_local(_fold("unequal_mismatches", "j"), "vla",
                 "contains_cp(ToSeq(fmt), 81)")
    + "    return total")

# === PARTIAL DOMAIN: one row judged by the other verdict (uniqueness) =======
# Routes correctly and folds the governing summary for every row EXCEPT row 0,
# whose verdict is taken from the other summary. Correct on every column whose
# first row's two verdicts agree — almost all of them — and wrong exactly where
# they differ. Given full proof power: the fold stops at 1, so the rival keeps
# the exact fold relation for every row it does handle honestly, and what it
# cannot prove is the one row it judged by the other verdict. It carries the two
# summaries' shared LENGTH (so its read of unequal_mismatches[0] is well-defined)
# but no ordering between them — there is none to carry.
_ROW0_OTHER = (
    _HEAD
    + "    if vla:\n"
    + _fold("close_mismatches", "i", extra_inv=_LENGUARD, stop=1)
    + """        if len(close_mismatches) > 0 and len(unequal_mismatches) > 0:
            Assert(ToSeq(close_mismatches).drop(1) ==
                   ToSeq(close_mismatches).drop(1))
            if unequal_mismatches[0] > 0:
                total = total + 1
"""
    + "    else:\n"
    + _fold("unequal_mismatches", "j")
    + "    return total")

# === BOUNDARY: the empty and single-row columns (uniqueness) ================
# Correct everywhere except at the fold's boundary: a column with no rows
# reports 1, and a one-row column always reports the plain-inequality verdict.
_BOUNDARY = (
    _HEAD
    + "    if len(close_mismatches) == 0:\n"
    "        return 1\n"
    "    if len(close_mismatches) == 1:\n"
    "        if unequal_mismatches[0] > 0:\n"
    "            return 1\n"
    "        return 0\n"
    "    if vla:\n" + _fold("close_mismatches", "i")
    + "    else:\n" + _fold("unequal_mismatches", "j")
    + "    return total")

# === FRAME MUTATION (uniqueness) — the inputs are read-only Acc(., 1/2) =====
# Right routing, wrong effect: zero a row's summary before folding it.
_FRAME_MUT = (
    _HEAD
    + "    if len(close_mismatches) > 0:\n"
    "        close_mismatches[0] = 0\n"
    "    if vla:\n" + _fold("close_mismatches", "i")
    + "    else:\n" + _fold("unequal_mismatches", "j")
    + "    return total")

# === NON-TERMINATION (uniqueness) ==========================================
# Right value, never delivered: spin forever, then compute the figure correctly.
# Only the caller's MustTerminate obligation catches this.
_DIVERGE = (
    _HEAD
    + "    spin = 0\n"
    "    while spin >= 0:\n"
    "        # invariants-start\n"
    + _PERMS.replace("            Invariant", "        Invariant")
    + "        Invariant(spin >= 0)\n"
    "        Invariant(total == 0)\n"
    "        Invariant(vla == rows_hold_subarrays)\n"
    "        # invariants-end\n"
    "        spin = spin + 1\n"
    "    if vla:\n" + _fold("close_mismatches", "i")
    + "    else:\n" + _fold("unequal_mismatches", "j")
    + "    return total")

# === GRANULARITY: positions instead of rows (uniqueness) ====================
# The row-granular discipline dropped on the variable-length branch: add each
# row's number of rejected POSITIONS instead of counting the row once.
_ELEMENT_SUM = (
    _HEAD
    + "    if vla:\n"
    + _fold("close_mismatches", "i", keep_rel=False,
            body="            total = total + close_mismatches[i - 1]\n")
    + "    else:\n" + _fold("unequal_mismatches", "j")
    + "    return total")

# === ROUTE INVERTED IN BOTH DIRECTIONS (uniqueness) =========================
# The recognition is computed correctly and used — just wired to the other
# summary on each branch. Distinct from the two "always X" misroutes: the
# descriptor still selects a branch, so a rival of this shape looks like it is
# routing and is wrong in both directions at once.
_INVERTED = (_HEAD
             + "    if vla:\n" + _fold("unequal_mismatches", "j")
             + "    else:\n" + _fold("close_mismatches", "i")
             + "    return total")

# === SATURATION: the right fold, then the figure adjusted (uniqueness) =======
# Routes correctly, folds the governing summary correctly, and then clamps the
# result below the number of rows. Correct on every column that does not have
# ALL of its rows differing, wrong exactly on the one that does.
_CLAMP = _GOLD_IMPL.replace(
    "    return total",
    "    if total >= len(close_mismatches) and total > 0:\n"
    "        total = total - 1\n"
    "    return total")

# === UNGROUNDED-ORACLE ECHO: the wrong summary (uniqueness) =================
# No work at all: echo the spec's own fold, applied to the summary of the
# verdict that does NOT govern the column.
_ECHO_WRONG = "    return row_granular_count(ToSeq(unequal_mismatches))"

# === UNGROUNDED-ORACLE ECHO: both summaries added (uniqueness) ==============
# The over-counting reading — "report everything that differs under either
# test" — as an echo of both folds on the variable-length branch.
_SUM_BOTH = (
    "    if rows_hold_subarrays:\n"
    "        return (row_granular_count(ToSeq(close_mismatches)) +\n"
    "                row_granular_count(ToSeq(unequal_mismatches)))\n"
    + _HEAD + _dedent(_fold("unequal_mismatches", "j")) + "    return total")



# === CARVE-OUT WHEN THE TWO SIDES ARE FRAMED DIFFERENTLY (uniqueness) ========
# THE rival this revision exists to reject. An earlier revision of this spec
# guarded the element-wise clause with a side condition — the figure was claimed
# only while the two sides framed their rows under one shared positional layout —
# and an impl was then free to do anything at all on a column whose sides are
# framed differently. This rival takes that freedom: it reports the CLOSENESS
# figure for any column whose sides are framed differently, and for boxed columns.
# The real element-wise comparator attributes every reported position to a
# leading-axis slot whatever the framing, so its figure IS claimed there, and
# this rival contradicts it. If this ever verifies again, the framing side
# condition has been reintroduced and the spec is TOO WEAK.
_CARVE_OUT = (
    "    if rows_hold_subarrays:\n"
    "        return row_granular_count(ToSeq(close_mismatches))\n"
    "    if len(unequal_mismatches) != len(close_mismatches):\n"
    "        return row_granular_count(ToSeq(close_mismatches))\n"
    "    return row_granular_count(ToSeq(unequal_mismatches))")

# === ROUTE OFF THE DESCRIPTOR CARRIER, BOTH DESIGNATORS (uniqueness) =========
# The shown attack's own family, in its strongest form: recognise BOTH
# designators in the carrier and route on that instead of on how the rows are
# actually stored. It agrees with the governing verdict on every column whose
# descriptor spelling happens to match its storage, and is wrong on every column
# where the two come apart — a column whose rows hold sub-arrays under a
# descriptor this test does not recognise, or a fixed-width column whose
# descriptor happens to contain a recognised code point. Routing must follow the
# STORAGE, so this must be rejected.
_CARRIER_BOTH = (
    "    total = 0\n"
    "    byname = contains_cp(ToSeq(fmt), 80) or contains_cp(ToSeq(fmt), 81)\n"
    "    if byname:\n"
    + _pin_local(_fold("close_mismatches", "i"), "byname",
                 "(contains_cp(ToSeq(fmt), 80) or contains_cp(ToSeq(fmt), 81))")
    + "    else:\n"
    + _pin_local(_fold("unequal_mismatches", "j"), "byname",
                 "(contains_cp(ToSeq(fmt), 80) or contains_cp(ToSeq(fmt), 81))")
    + "    return total")

_MISROUTE_REFINEMENT = (
    "A faithful real patch of this shape sends a column to the comparator that "
    "does not govern it. On the F2P 64-bit variable-length column the "
    "element-wise path does not merely return a different figure: it raises on "
    "the object array of sub-arrays, so _diff crashes and BOTH F2P tests fail "
    "(test_identical_tables on the identical column, and "
    "test_different_table_data which needs diff_total 13 -> 15). Where the "
    "element-wise path does return, its plain-inequality verdict separates "
    "64-bit values the closeness verdict cannot, so the figure is wrong by row "
    "count. Faithful real patch does NOT resolve."
)


SPEC_TESTS = [
    {
        "id": "pos-control-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_REORDER),
        "rationale": (
            "Structurally different but correct: the descriptor tested once into "
            "a local, the ordinary-column branch written first and the "
            "variable-length branch second. Each column kind still reports the "
            "figure of the verdict that governs it, so every obligation the gold "
            "discharges is still discharged — only the branch order and the "
            "shape of the carried recognition change. Must verify, else "
            "SPEC-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-local-reshape-admiss",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_LOCAL),
        "rationale": (
            "Local-variable reshape (bind the recognition to a local bool, keep "
            "gold's branch order). Doubles as admissibility: the precondition "
            "must accept an ordinary F2P-shaped column — two independent "
            "summaries of the same rows, in no particular relation to each "
            "other — and let the figure be returned. Must verify, else "
            "PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "pos-control-fold-both-then-select",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_BOTH_THEN_SELECT),
        "rationale": (
            "A correct impl that reaches the governing figure by a different "
            "route: it folds BOTH summaries into two accumulators and only then "
            "consults the descriptor to choose which figure to return, so the "
            "routing happens after the work instead of selecting it. Each kind "
            "of column still reports the figure of the verdict that governs it. "
            "Must verify, else the spec pins the ORDER in which an impl decides "
            "and computes rather than the figure => SPEC-TOO-STRONG. (This "
            "replaces a control that counted the rows BOTH verdicts reject: "
            "that was correct only under an ordering between the two summaries, "
            "and the real per-position verdicts are incomparable, so it is wrong "
            "on real columns and cannot certify anything.)"
        ),
    },
    {
        "id": "pos-control-fold-without-loop",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _GOLD_IMPL, _POS_ECHO_RIGHT),
        "rationale": (
            "The governing verdict's figure handed back directly, with no loop "
            "at all: a correct impl in a shape gold does not use. Must verify, "
            "else the spec pins the gold's WAY of arriving at the figure rather "
            "than the figure => SPEC-TOO-STRONG (this is the control that "
            "caught Ensures(Result() >= 0) needing the count's non-negativity "
            "to be part of the model rather than a by-product of folding)."
        ),
    },
    {
        "id": "carve-out-when-frames-differ",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _CARVE_OUT),
        "refinement": (
            "A faithful real patch of this shape judges a fixed-width column by "
            "the row-aware closeness verdict whenever the two sides are framed "
            "differently. test_different_table_data compares tables holding a "
            "4I column declared with a 2x2 layout; the real element-wise "
            "comparator reports its differing slots and the expected diff_total "
            "counts them, while the closeness verdict at the comparison's "
            "tolerances is a different test over 16-bit integers and reports a "
            "different figure, so the expected diff_total is not produced and "
            "the test FAILS. Faithful real patch does NOT resolve."
        ),
        "rationale": (
            "THE rival this revision of the spec exists to reject. An earlier "
            "revision guarded the element-wise clause with a framing side "
            "condition, which left a column whose two sides are framed "
            "differently with NO claimed figure — and this impl, which verified "
            "against that revision, does whatever it likes there. The real "
            "comparator attributes every reported position to a leading-axis "
            "slot of the block comparison whatever the framing, so the figure is "
            "claimed unconditionally and this rival contradicts it. If it "
            "verifies, a framing carve-out has been reintroduced => "
            "SPEC-TOO-WEAK."
        ),
    },
    {
        "id": "route-by-descriptor-carrier-both",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _CARRIER_BOTH),
        "refinement": (
            "Routing off the descriptor spelling rather than the storage is the "
            "shape the earlier revision of this spec admitted: with the routing "
            "predicate an unconstrained axiom, an impl could dispatch on the "
            "symbol and instantiate it in refinement as any descriptor test at "
            "all, including the pre-patch one. A real patch that decides from "
            "the carrier reports the non-governing verdict's figure on every "
            "column whose spelling and storage come apart, so the identical-file "
            "comparison of the issue still reports a difference and both F2P "
            "tests fail. Faithful real patch does NOT resolve."
        ),
        "rationale": (
            "The routing observation is a DATA INPUT, so an impl that decides "
            "from the descriptor carrier instead cannot prove either clause "
            "wherever the carrier and the storage disagree — a boxed column "
            "under an unrecognised spelling, or a fixed-width column whose "
            "descriptor happens to contain a recognised code point. This is the "
            "shown attack's own family in its strongest form; rejection comes "
            "from the governing-verdict postcondition, the same clause the "
            "prepatch twin fails on."
        ),
    },
    {
        "id": "misroute-always-plain-inequality",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ALWAYS_UNEQUAL),
        "refinement": _MISROUTE_REFINEMENT,
        "rationale": (
            "The recognition is dropped and every column reports the "
            "plain-inequality figure. On a variable-length column the "
            "postcondition demands the closeness verdict's figure, and the two "
            "differ, so the rival cannot prove "
            "Implies(rows_hold_subarrays, Result() == "
            "row_granular_count(ToSeq(close_mismatches))). Rejection comes from "
            "the governing-verdict postcondition — a wrong VALUE, with full "
            "proof power granted."
        ),
    },
    {
        "id": "misroute-always-closeness",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ALWAYS_CLOSE),
        "refinement": (
            "The reverse misrouting: an ordinary fixed-width column would be "
            "judged by the row-aware comparator's closeness verdict at the "
            "comparison's tolerances instead of by plain inequality. On 64-bit "
            "integer columns above the closeness verdict's significand width "
            "that verdict cannot separate neighbouring values, so genuinely "
            "differing rows stop being counted and the pre-existing "
            "PASS_TO_PASS table-data comparisons under-report diff_total. "
            "Faithful real patch does NOT resolve."
        ),
        "rationale": (
            "Every column reports the closeness figure, so the rival cannot "
            "prove Implies(not rows_hold_subarrays, Result() == "
            "row_granular_count(ToSeq(unequal_mismatches))) wherever the two "
            "verdicts differ. Rejection from the governing-verdict "
            "postcondition."
        ),
    },
    {
        "id": "route-by-descriptor-carrier-32bit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _PONLY),
        "refinement": (
            "This IS the pre-patch bug: only the 32-bit variable-length "
            "designator is recognised. On the F2P column carrying the 64-bit "
            "designator the real element-wise path raises ValueError on the "
            "object array of 2-element sub-arrays, crashing _diff and failing "
            "BOTH F2P tests (test_identical_tables on the identical column, and "
            "test_different_table_data which needs diff_total 13 -> 15). "
            "Faithful real patch does NOT resolve."
        ),
        "rationale": (
            "A column carrying only the 64-bit designator satisfies "
            "the storage observation, yet this rival folds its plain-inequality "
            "summary, so the closeness clause of the postcondition fails. "
            "Rejection from the governing-verdict postcondition — the same "
            "clause the prepatch twin fails on."
        ),
    },
    {
        "id": "route-by-descriptor-carrier-64bit",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _QONLY),
        "refinement": (
            "The mirror image of the pre-patch bug: a column carrying the "
            "32-bit designator loses the row-aware treatment it already had, so "
            "its object array of sub-arrays reaches the element-wise path and "
            "raises. The pre-existing PASS_TO_PASS comparisons over 32-bit "
            "variable-length columns crash. Faithful real patch does NOT "
            "resolve."
        ),
        "rationale": (
            "Symmetric to the case above: a column carrying only the 32-bit "
            "designator has rows holding sub-arrays but is folded from the "
            "plain-inequality summary, so the closeness clause fails. Rejection "
            "from the governing-verdict postcondition."
        ),
    },
    {
        "id": "partial-domain-row0-other-verdict",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ROW0_OTHER),
        "refinement": (
            "A patch of this shape judges row 0 of a variable-length column by "
            "plain inequality while judging every other row by closeness. On "
            "the issue's own reproduction — a file compared to ITSELF — every "
            "row agrees under both verdicts and the bug is invisible; on a "
            "64-bit column whose row 0 holds neighbouring values the closeness "
            "verdict cannot separate, row 0 is reported as differing and "
            "FITSDiff again reports a difference where the row-aware comparator "
            "finds none, which is exactly the reported failure. Faithful real "
            "patch does NOT resolve."
        ),
        "rationale": (
            "Correct on the whole domain except row 0, so no clause about the "
            "column as a whole is violated unless the two verdicts differ THERE "
            "— the partial-domain class. The rival keeps the exact fold relation "
            "for rows 1..n-1 (its loop stops at 1) and is granted the two "
            "summaries' shared length, so what it cannot prove is only the row "
            "it judged by the wrong verdict. Rejection from the "
            "governing-verdict postcondition."
        ),
    },
    {
        "id": "boundary-empty-and-single-row",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _BOUNDARY),
        "refinement": (
            "A patch that special-cases the ends of the fold: a column with no "
            "rows is reported as having one differing row, and a one-row column "
            "is always judged by plain inequality. The first makes FITSDiff "
            "report a difference between two empty columns — a difference that "
            "does not exist, the reported failure again; the second is the "
            "single-row variable-length column of the issue's own reproduction, "
            "where a 64-bit pair the closeness verdict cannot separate is "
            "reported as differing. Faithful real patch does NOT resolve."
        ),
        "rationale": (
            "The boundary class: correct on every column of two or more rows, "
            "wrong at 0 and 1. row_granular_count of an empty summary is 0, so "
            "returning 1 breaks both clauses, and the one-row case breaks the "
            "closeness clause. Rejection from the governing-verdict "
            "postcondition."
        ),
    },
    {
        "id": "route-inverted-both-branches",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _INVERTED),
        "refinement": _MISROUTE_REFINEMENT,
        "rationale": (
            "The recognition is computed and used, but each branch folds the "
            "other branch's summary. Distinct from the two 'always X' misroutes: "
            "a rival of this shape looks like it is routing. Both clauses of the "
            "postcondition are violated wherever the two verdicts differ. "
            "Rejection from the governing-verdict postcondition."
        ),
    },
    {
        "id": "saturation-clamp-figure",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _CLAMP),
        "refinement": (
            "A patch that clamps the per-column figure below the number of rows "
            "under-reports exactly the worst column: one whose every row "
            "differs. test_different_table_data needs the new differing column "
            "to raise diff_total from 13 to 15; clamped it contributes one row "
            "too few and the test FAILS. Faithful real patch does NOT resolve."
        ),
        "rationale": (
            "Routes correctly and folds the governing summary correctly, then "
            "adjusts the answer — the shape a rival takes when the routing "
            "clauses alone are what the spec pins. It is correct on every column "
            "that does not have all of its rows differing, so only the exact "
            "figure catches it. Rejection from the governing-verdict "
            "postcondition."
        ),
    },
    {
        "id": "frame-mutation-write-readonly",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _FRAME_MUT),
        "refinement": (
            "A faithful real patch cannot zero a row's mismatch summary: it "
            "would silently drop a genuinely differing row from diff_total, so "
            "test_different_table_data (which requires diff_total 13 -> 15 from "
            "the new differing column) would under-count and FAIL. The write is "
            "behaviourally wrong, not just a permission artifact."
        ),
        "rationale": (
            "The summaries are read-only (Acc(list_pred(close_mismatches), "
            "1/2)), so the write close_mismatches[0] = 0 must be rejected for "
            "INSUFFICIENT PERMISSION. If it verified, an impl that edits its "
            "input until the postcondition holds would pass => SPEC-TOO-WEAK on "
            "framing. Rejection comes from the permission system."
        ),
    },
    {
        "id": "non-termination-before-the-figure",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _DIVERGE),
        "refinement": (
            "A per-column comparison that never returns delivers no figure at "
            "all: FITSDiff hangs and every test that compares table data, F2P "
            "and PASS_TO_PASS alike, fails by timeout rather than by a wrong "
            "count. The eventual value being right is worth nothing. Faithful "
            "real patch does NOT resolve."
        ),
        "rationale": (
            "The value this rival would return is exactly gold's, so no value "
            "clause discriminates it: under a partial-correctness reading it is "
            "admissible. Requires(MustTerminate(2)) is what rejects it — the "
            "added loop takes no measure, so the obligation cannot be "
            "discharged. Rejection from the termination obligation."
        ),
    },
    {
        "id": "granularity-positions-not-rows",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ELEMENT_SUM),
        "refinement": (
            "Adding each row's number of rejected positions instead of counting "
            "the row once over-reports: the real per-column accumulation is "
            "len(set(diffs[0])), a count of distinct ROWS. A variable-length "
            "column with one row differing in two positions would be reported "
            "as two differing rows, so test_different_table_data's expected "
            "diff_total is exceeded and the test FAILS. Faithful real patch "
            "does NOT resolve."
        ),
        "rationale": (
            "Row-granularity is the other half of the modelled behaviour: the "
            "figure counts rows that differ ANYWHERE, not positions. The rival "
            "cannot prove the closeness clause on any column with a row of two "
            "or more rejected positions. Rejection from the governing-verdict "
            "postcondition."
        ),
    },
    {
        "id": "echo-wrong-summary-no-work",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _ECHO_WRONG),
        "refinement": (
            "Identical in behaviour to dropping the recognition altogether — "
            "every column reports the plain-inequality figure — so it fails the "
            "F2P tests for the same reason: the 64-bit variable-length column "
            "reaches the element-wise path, which raises on its object array. "
            "Faithful real patch does NOT resolve."
        ),
        "rationale": (
            "The ungrounded-oracle class. The oracle is a @Pure fold over the "
            "arguments, so an impl CAN echo it without doing any work — but with "
            "two summaries in scope the echo has to pick one, and picking the "
            "non-governing one is exactly what the postcondition forbids. If "
            "this verified, the two clauses would be a tautology under the "
            "model. Rejection from the governing-verdict postcondition."
        ),
    },
    {
        "id": "echo-sum-of-both-summaries",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _GOLD_IMPL, _SUM_BOTH),
        "refinement": (
            "The over-counting reading, 'report every row that differs under "
            "either test', double-counts every row both verdicts reject: a "
            "variable-length column of two differing rows reports four. "
            "test_different_table_data's expected diff_total is exceeded and the "
            "test FAILS. Faithful real patch does NOT resolve."
        ),
        "rationale": (
            "A second ungrounded echo, this one combining both summaries rather "
            "than choosing the wrong one — the shape a rival takes when it tries "
            "to satisfy both clauses at once. It satisfies neither wherever "
            "either figure is non-zero. Rejection from the governing-verdict "
            "postcondition."
        ),
    },
]


# ===========================================================================
# AXIOM lane — no consumed @ContractOnly axioms, but the deep models are
# A-references validated against the REAL callees. The probes execute the real
# numpy paths in the instance container (the same obligations axiom_check.py
# checks), fuzzing boundaries + sentinels + raise paths to try to make the real
# callee DISAGREE. Each probe is self-contained: imports only stdlib + numpy (a
# core astropy dependency present in the eval image), prints a diagnostic, exits
# 0 iff the obligation holds. (The runner mounts ONLY the probe; nothing from the
# bundle is in-container, so each probe is fully self-contained.)
# ===========================================================================

_PROBE_ROUTING = r'''
import sys
import numpy as np
from astropy.io import fits
# A-reference soundness for the ROUTING OBSERVATION `rows_hold_subarrays`.
#
# The spec routes on HOW A COLUMN'S ROWS ARE STORED, and says explicitly that
# this is NOT read off the descriptor spelling. This probe grounds that: it
# materialises real column pairs and checks that the observation deciding the
# route agrees with the real storage of each, never with its format text.
def build(fmt, arr, dim=None):
    kw = {'dim': dim} if dim else {}
    return fits.BinTableHDU.from_columns(
        [fits.Column(name='c', format=fmt, array=arr, **kw)]).data

def rows_hold_subarrays(arr):
    # read off the MATERIALISED column: each row is its own sub-array object
    return arr.dtype == object

bad = 0
n_boxed = 0
n_flat = 0
cases = []
for fmt in ['PJ', 'QJ', 'PD', 'QD', 'PI', 'QE']:
    cases.append((fmt, [[0], [0, 0]], None))
    cases.append((fmt, [[1, 2], [3, 4]], None))
for fmt in ['J', 'I', 'D', 'E', 'K', '2J', '4I', '2D', 'B']:
    w = 2 if fmt.startswith('2') else (4 if fmt.startswith('4') else 1)
    arr = [[1] * w, [2] * w] if w > 1 else [1, 2]
    cases.append((fmt, arr, None))
cases.append(('4I', [[0, 1, 2, 3], [4, 5, 6, 7]], '(2,2)'))
cases.append(('4I', [[0, 1, 2, 3], [4, 5, 6, 7]], '(4)'))
cases.append(('2J', [[1, 2], [3, 4]], '(2,1)'))

for fmt, arr, dim in cases:
    try:
        col = build(fmt, arr, dim)['c']
    except Exception as e:
        print('SKIP %r %r: %s' % (fmt, dim, e))
        continue
    obs = rows_hold_subarrays(col)
    if obs:
        n_boxed += 1
        # a boxed column must be a 1-D listing of one value per row, so its
        # leading axis IS the rows -- the fact the closeness clause rests on
        if col.ndim != 1 or col.shape[0] != len(arr):
            print('DISAGREE boxed %r %r: shape %r for %d rows'
                  % (fmt, dim, col.shape, len(arr)))
            bad += 1
    else:
        n_flat += 1
        if col.dtype == object:
            print('DISAGREE flat %r %r: dtype is object' % (fmt, dim))
            bad += 1
if n_boxed == 0 or n_flat == 0:
    print('FAIL: routing observation not exercised on both classes '
          '(boxed=%d flat=%d)' % (n_boxed, n_flat))
    bad += 1
# DECISIVE leg: the observation must follow the STORAGE, not the spelling. A
# boxed and a flat column of the same element type must be separated by it.
boxed = build('QJ', [[1, 2], [3, 4]])['c']
flat = build('2J', [[1, 2], [3, 4]])['c']
if not (rows_hold_subarrays(boxed) and not rows_hold_subarrays(flat)):
    print('DISAGREE: observation does not separate boxed from flat storage')
    bad += 1
if bad:
    print('FAIL: routing observation disagrees with real storage (%d cases)' % bad)
    sys.exit(1)
print('OK rows_hold_subarrays == real materialised storage on %d boxed + %d flat '
      'column pairs; separates boxed from flat at identical element type'
      % (n_boxed, n_flat))
sys.exit(0)
'''


_PROBE_ROWGRAN = r'''
import random, sys
import numpy as np
# A-reference soundness for row_granular_count == the real per-column
# accumulation len(set(diffs[0])), on BOTH comparators, each folded over ITS OWN
# per-position verdict's summary. Then (2c) the ORDERING fact the spec's
# precondition states between the two summaries, and its NON-VACUITY: the two
# verdicts must genuinely differ somewhere, or the spec's two carriers would be
# one carrier used twice and a misrouting would be unobservable.
def model_count(row_mismatches):
    return sum(1 for m in row_mismatches if m > 0)
def row_mismatches_of(rows_a, rows_b):
    # Ground the summary in the ROW-AWARE comparator's OWN per-position verdict,
    # under the SAME positional alignment that comparator uses (numpy's own), NOT
    # a hand-rolled length penalty and NOT an idealised exact-equality test: the
    # comparator folds a per-position closeness verdict over the row, so the
    # summary counts exactly the positions THAT verdict rejects. Unequal lengths
    # that still align contribute per aligned position, and a pair that cannot
    # align at all raises here exactly as it does in the real comparator (that
    # row is outside the comparison's domain, so it has no summary).
    out = []
    for ra, rb in zip(rows_a, rows_b):
        a = np.asarray(ra); b = np.asarray(rb)
        out.append(int(np.count_nonzero(~np.isclose(a, b, rtol=0, atol=0))))
    return out
def row_mismatches_of_ew(rows_a, rows_b):
    # The ELEMENT-WISE comparator's own per-position verdict is a different test
    # (a plain inequality over the regular ndarray), so its branch is grounded
    # separately. Collapsing the two branches onto one per-position test is what
    # makes a summary diverge from the real figure on one branch or the other.
    out = []
    for ra, rb in zip(rows_a, rows_b):
        a = np.asarray(ra); b = np.asarray(rb)
        out.append(int(np.count_nonzero(a != b)))
    return out
def ew_summary_leading_axis(arra, arrb):
    # The element-wise comparator compares the two sides as whole blocks and
    # attributes each reported position to a slot of the LEADING AXIS of that
    # comparison. This is the grounding the spec's element-wise clause uses, and
    # it is the one that stays correct when the two sides are framed
    # DIFFERENTLY: a per-row zip of the two sides is NOT what the real code
    # does, and diverges from the real figure exactly on that class.
    ne = np.asarray(arra != arrb)
    if ne.ndim == 0:
        ne = ne.reshape(1)
    return [int(np.count_nonzero(ne[i])) for i in range(ne.shape[0])]
def _obj(rows):
    arr = np.empty(len(rows), dtype=object)
    for i, r in enumerate(rows):
        arr[i] = np.asarray(r)
    return arr
def real_vla(rows_a, rows_b):  # row-aware np.allclose path
    arra = _obj(rows_a); arrb = _obj(rows_b)
    diffs = ([idx for idx in range(len(arra))
              if not np.allclose(arra[idx], arrb[idx], rtol=0, atol=0)],)
    return len(set(diffs[0]))
def real_ew(arra, arrb):  # element-wise np.where path
    diffs = np.where(arra != arrb)
    return len(set(diffs[0]))

bad = 0
# --- 2a: row-aware path == row_granular_count. F2P + boundary + fuzz. ---
vla_boundary = [
    ([[0,1],[2,3]], [[0,1],[2,3]], 0),   # F2P identical QJ(2)
    ([[0,1],[2,3]], [[1,2],[3,4]], 2),   # F2P both differ
    ([[0],[0,0]],   [[0],[0,0]],   0),   # issue ragged QD identical
    ([[5],[6],[7]], [[5],[9],[7]], 1),   # one differs
    ([[1,2,3],[4,5,6]], [[1,9,3],[4,5,6]], 1),  # partial-row diff counts ONCE
    ([[1,2,3],[9,9,9]], [[1,0,3],[9,0,9]], 2),
    # Rows whose two stored values have UNEQUAL lengths but still align
    # positionally: the real comparator judges them by that alignment, so a
    # length difference alone is NOT a difference. Expected values below are
    # the REAL callee's (TableDataDiff.diff_total on real Q-columns).
    ([[0]],         [[0,0]],       0),   # aligns, all positions agree -> 0
    ([[0]],         [[0,1]],       1),   # aligns, a position disagrees -> 1
    ([[0]],         [[1,1]],       1),   # row-granular: still ONE row
    ([[0,0]],       [[0]],         0),   # opposite orientation -> 0
    ([[5]],         [[5,5,5]],     0),   # width 1 vs 3 aligns -> 0
    ([[1],[2,2]],   [[1,1],[2]],   0),   # both rows align, both agree -> 0
    ([[3],[0,1]],   [[3,3,3],[0,1]], 0),
    # 64-bit magnitudes. The row comparator's per-position verdict is computed
    # in a fixed-precision arithmetic whose significand is narrower than the
    # 64-bit integer range, so above 2**53 it is strictly COARSER than an
    # idealised exact comparison: neighbouring 64-bit values it cannot separate
    # are judged equivalent, and the real figure counts no differing row. These
    # expected values are the REAL callee's (TableDataDiff.diff_total on real
    # 64-bit columns), NOT what an exact-equality reading would predict.
    ([[9007199254740992]], [[9007199254740993]], 0),   # 2**53, +1: unresolved
    ([[9007199254740992]], [[9007199254740994]], 1),   # 2**53, +2: resolved
    ([[9007199254740991]], [[9007199254740992]], 1),   # below the boundary
    ([[0, 9007199254740992]], [[0, 9007199254740993]], 0),
    ([[9007199254740992],[3]], [[9007199254740993],[4]], 1),  # only row 1 counts
    ([[4611686018427387904]], [[4611686018427387905]], 0),
    ([[9007199254740992]], [[9007199254740992, 9007199254740992]], 0),
]
for ra, rb, want in vla_boundary:
    got_model = model_count(row_mismatches_of(ra, rb))
    got_real = real_vla(ra, rb)
    if not (got_model == got_real == want):
        print("DISAGREE vla %r/%r: model=%r real=%r want=%r" % (ra, rb, got_model, got_real, want))
        bad += 1
rng = random.Random(14539)
# The fuzz deliberately INCLUDES rows whose two stored values have unequal
# lengths (the alignment-dependent class). Where the alignment does not exist
# the real comparator raises; the grounded summary raises identically, so such a
# draw is counted as an out-of-domain row rather than skipped silently, and the
# run FAILS below if the alignment-dependent class was never exercised.
n_ragged_aligned = 0; n_outside_domain = 0
# Magnitudes are drawn across the FULL declared 64-bit range, not just small
# values: the per-position verdict's significand is narrower than that range, so
# a generator confined to tiny magnitudes cannot reach the region where the
# verdict stops separating neighbouring values, and would report agreement it
# never tested. `n_wide` below counts draws in that region and the run FAILS if
# the class was never exercised.
def _int_val(rng):
    r = rng.random()
    if r < 0.45:
        return rng.randint(-3, 3)                       # small values
    if r < 0.70:
        return rng.getrandbits(62)                      # full-range magnitudes
    if r < 0.90:
        return (1 << 53) + rng.randint(-2, 6)           # straddle the boundary
    return rng.choice([1 << 53, (1 << 53) + 1, (1 << 62), (1 << 62) + 1])
WIDE = 1 << 53
n_wide = 0
for _ in range(20000):
    nrows = rng.randint(0, 6); rows_a=[]; rows_b=[]; ragged = False
    for _r in range(nrows):
        w = rng.randint(0, 5)
        a = [_int_val(rng) for _ in range(w)]
        if rng.random() < 0.4:
            wb = rng.randint(0, 5)
            b = [_int_val(rng) for _ in range(wb)]
            if wb != w:
                ragged = True
        else:
            b = list(a)
            for k in range(w):
                if rng.random() < 0.3:
                    # Perturb by a SMALL delta so the pair lands on either side
                    # of the verdict's resolution limit depending on magnitude.
                    b[k] = a[k] + rng.choice([0, 1, -1, 2, -2])
        if any(abs(v) >= WIDE for v in a) or any(abs(v) >= WIDE for v in b):
            n_wide += 1
        rows_a.append(a); rows_b.append(b)
    try:
        got_real = real_vla(rows_a, rows_b)
    except ValueError:
        # no positional alignment -> outside the comparison's domain. The
        # grounded summary must be undefined here too, not silently numeric.
        try:
            row_mismatches_of(rows_a, rows_b)
            print("DISAGREE domain %r/%r: real raised, summary did not"
                  % (rows_a, rows_b)); bad += 1
        except ValueError:
            n_outside_domain += 1
        continue
    if model_count(row_mismatches_of(rows_a, rows_b)) != got_real:
        print("DISAGREE vla fuzz %r/%r" % (rows_a, rows_b)); bad += 1
    elif ragged:
        n_ragged_aligned += 1
if n_ragged_aligned == 0:
    print("FAIL: fuzz never exercised an unequal-length but ALIGNING row "
          "(the alignment-dependent class went untested)")
    bad += 1
if n_wide == 0:
    print("FAIL: fuzz never drew a magnitude at or beyond the per-position "
          "verdict's resolution limit (the wide-magnitude class went untested, "
          "so agreement there was asserted and never checked)")
    bad += 1

# --- 2b: element-wise path == row_granular_count, incl. multi-element
#     fixed-width where a NAIVE element sum would diverge from the row count
#     (non-vacuous: require sum>row_count seen at least once). ---
distinguishing = 0
def ew_check(arra, arrb):
    rows_a = [np.asarray(arra[i]) for i in range(len(arra))]
    rows_b = [np.asarray(arrb[i]) for i in range(len(arrb))]
    m = row_mismatches_of_ew(rows_a, rows_b)
    return model_count(m), real_ew(arra, arrb), sum(m)
for arra, arrb in [
    (np.array([1,2]), np.array([1,3])),
    (np.array([[0],[0]]), np.array([[0],[1]])),
    (np.array([[1,2],[3,4]]), np.array([[1,9],[8,8]])),
]:
    gm, gr, s = ew_check(arra, arrb)
    if gm != gr:
        print("DISAGREE ew %r/%r: model=%r real=%r" % (arra.tolist(), arrb.tolist(), gm, gr)); bad += 1
    if s > gr:
        distinguishing += 1
for _ in range(20000):
    nrows = rng.randint(0, 6); width = rng.randint(1, 4)
    if rng.random() < 0.5:
        a = np.array([[rng.randint(-3,3) for _ in range(width)] for _ in range(nrows)]).reshape(nrows, width)
        b = a.copy()
        for i in range(nrows):
            for j in range(width):
                if rng.random() < 0.25:
                    b[i, j] = rng.randint(-3,3)
    else:
        a = np.array([rng.randint(-3,3) for _ in range(nrows)])
        b = a.copy()
        for i in range(nrows):
            if rng.random() < 0.3:
                b[i] = rng.randint(-3,3)
    gm, gr, s = ew_check(a, b)
    if gm != gr:
        print("DISAGREE ew fuzz"); bad += 1
    if s > gr:
        distinguishing += 1
if distinguishing == 0:
    print("FAIL: element-wise check never exercised a partial-row diff (vacuous)")
    bad += 1

# --- 2c: the two summaries are INCOMPARABLE, which is why the precondition
#     states NO relation between them. This leg does not assert an ordering; it
#     asserts that BOTH directions of a would-be ordering are refuted by a real
#     per-position verdict pair, so a spec assuming either direction would
#     exclude columns the real comparison compares. Both witnesses must be found
#     or this leg FAILS: the spec's silence has to be earned, not assumed.
#       direction 1  close > unequal : the closeness verdict is not reflexive on
#         a value with a non-finite component (it scales its operands before
#         comparing, which destroys such a value), so a position holding the SAME
#         complex value twice is rejected by closeness and passed by inequality.
#       direction 2  close < unequal : the closeness verdict is computed in a
#         fixed-precision arithmetic whose significand is narrower than the
#         64-bit integer range, so it cannot separate neighbouring values there
#         that the inequality test separates.
n_pairs = 0; n_close_gt = 0; n_close_lt = 0; n_nan = 0
# direction 2 witnesses: integer magnitudes across the full 64-bit range.
for _ in range(20000):
    nrows = rng.randint(1, 5); rows_a = []; rows_b = []
    for _r in range(nrows):
        w = rng.randint(1, 4)
        a = [_int_val(rng) for _ in range(w)]
        b = list(a)
        for k in range(w):
            if rng.random() < 0.35:
                b[k] = a[k] + rng.choice([1, -1, 2, -2, 1 << 40])
        rows_a.append(a); rows_b.append(b)
    close = row_mismatches_of(rows_a, rows_b)
    uneq = row_mismatches_of_ew(rows_a, rows_b)
    for c, u in zip(close, uneq):
        n_pairs += 1
        if c > u: n_close_gt += 1
        elif c < u: n_close_lt += 1
# direction 1 witnesses: complex values with a non-finite component, compared to
# THEMSELVES. These are the pairs an ordering close <= unequal would forbid.
INF = float("inf"); NAN = float("nan")
cpx = [complex(INF, 2.0), complex(INF, 0.0), complex(2.0, INF), complex(0.0, INF),
       complex(INF, INF), complex(-INF, 3.0), complex(NAN, 2.0), complex(1.0, 2.0)]
n_selfpair_close_rejects = 0
for v in cpx:
    c = row_mismatches_of([[v]], [[v]])[0]
    u = row_mismatches_of_ew([[v]], [[v]])[0]
    n_pairs += 1
    if c > u:
        n_close_gt += 1
        n_selfpair_close_rejects += 1
    elif c < u:
        n_close_lt += 1
# Float rows: NaN is not close to NaN and is also unequal to itself.
for _ in range(4000):
    w = rng.randint(1, 4)
    a = [rng.choice([0.0, -0.0, 1.5, NAN, INF, -INF]) for _ in range(w)]
    b = [rng.choice([0.0, -0.0, 1.5, NAN, INF, -INF]) for _ in range(w)]
    if any(v != v for v in a + b):
        n_nan += 1
    c = row_mismatches_of([a], [b])[0]
    u = row_mismatches_of_ew([a], [b])[0]
    n_pairs += 1
    if c > u: n_close_gt += 1
    elif c < u: n_close_lt += 1
if n_close_lt == 0:
    print("FAIL: no per-row pair with close < unequal, so 'unequal <= close' was "
          "never refuted and the spec could have assumed that direction")
    bad += 1
if n_close_gt == 0 or n_selfpair_close_rejects == 0:
    print("FAIL: no per-row pair with close > unequal (self-compared "
          "non-finite-component complex rejected by closeness: %d), so "
          "'close <= unequal' was never refuted and the spec's omission of that "
          "ordering is unjustified" % n_selfpair_close_rejects)
    bad += 1

# --- 2e: the element-wise clause is claimed for EVERY non-boxed column, so its
#     grounding must hold even when the two sides frame their rows DIFFERENTLY.
#     An earlier revision of this spec carved that class out; this leg is what
#     earns the unconditional clause. The grounding is the LEADING AXIS of the
#     block comparison the real code performs -- not a per-row zip of the two
#     sides, which diverges from the real figure precisely here. Both a
#     same-framing and a different-framing class must be exercised, and the
#     different-framing class must contain a case where a per-row zip would have
#     given the WRONG figure, or the leg proves nothing.
from astropy.io import fits as _fits
def _build(fmt, arr, dim=None):
    kw = {'dim': dim} if dim else {}
    return _fits.BinTableHDU.from_columns(
        [_fits.Column(name='c', format=fmt, array=arr, **kw)]).data
n_same = 0; n_diff = 0; n_zip_would_be_wrong = 0
DIMS = [None, '(2)', '(1,2)', '(2,1)', '(2,2)', '(4)', '(4,1)', '(1,4)']
for w, fmt in ((2, '2J'), (4, '4I')):
    for dima in DIMS:
        for dimb in DIMS:
            for trial in range(6):
                nrows = rng.randint(1, 4)
                A = [[rng.randint(0, 3) for _ in range(w)] for _ in range(nrows)]
                B = [[rng.randint(0, 3) for _ in range(w)] for _ in range(nrows)]
                try:
                    arra = _build(fmt, A, dima)['c']
                    arrb = _build(fmt, B, dimb)['c']
                    real = real_ew(arra, arrb)
                except Exception:
                    continue
                got = model_count(ew_summary_leading_axis(arra, arrb))
                if got != real:
                    print("DISAGREE ew leading-axis %r %r/%r shapes %r/%r: "
                          "model=%r real=%r"
                          % (fmt, dima, dimb, arra.shape, arrb.shape, got, real))
                    bad += 1
                if arra.shape == arrb.shape:
                    n_same += 1
                else:
                    n_diff += 1
                    try:
                        zip_fig = model_count(row_mismatches_of_ew(
                            [np.asarray(arra[k]) for k in range(len(arra))],
                            [np.asarray(arrb[k]) for k in range(len(arrb))]))
                        if zip_fig != real:
                            n_zip_would_be_wrong += 1
                    except Exception:
                        n_zip_would_be_wrong += 1
if n_same == 0 or n_diff == 0:
    print("FAIL: leading-axis grounding not exercised on both framing classes "
          "(same=%d differing=%d)" % (n_same, n_diff))
    bad += 1
if n_zip_would_be_wrong == 0:
    print("FAIL: no differently-framed column where a per-row zip grounding "
          "would give the wrong figure, so the leading-axis grounding was never "
          "actually distinguished from the naive one")
    bad += 1

if bad:
    print("FAIL: row_granular_count disagrees with real diff_total (%d cases)" % bad)
    sys.exit(1)
print("OK element-wise leading-axis grounding == real figure on %d same-framed + "
      "%d differently-framed column pairs (%d of which a per-row zip would have "
      "got wrong), so the element-wise clause needs no framing side condition"
      % (n_same, n_diff, n_zip_would_be_wrong))
print("OK row_granular_count == real row-aware AND element-wise paths; %d distinguishing partial-row diffs; %d unequal-length-but-aligning rows agreed, %d outside the alignment domain (real and summary raise together); %d wide-magnitude draws at/beyond the per-position verdict's resolution limit agreed" % (distinguishing, n_ragged_aligned, n_outside_domain, n_wide))
print("OK the two per-position verdicts are INCOMPARABLE over %d per-row pairs: close>unequal on %d (incl. %d self-compared non-finite-component complex positions closeness rejects and inequality passes), close<unequal on %d (64-bit neighbours closeness cannot separate), %d NaN-bearing float rows -- so neither ordering may be assumed" % (n_pairs, n_close_gt, n_selfpair_close_rejects, n_close_lt, n_nan))
sys.exit(0)
'''

_PROBE_APPLIC = r'''
import sys
import numpy as np
# A-reference (applicability / control-flow effect): the element-wise np.where
# path is NOT applicable to a genuine VLA column. It RAISES on an object array
# of multi-element sub-arrays. This grounds the spec's statement that a column
# whose rows hold variable-length sub-arrays is never compared by the
# element-wise comparator -- i.e. that the closeness verdict is the one
# GOVERNING such a column, which is what the postcondition's first clause says.
def _obj(rows):
    arr = np.empty(len(rows), dtype=object)
    for i, r in enumerate(rows):
        arr[i] = np.asarray(r)
    return arr
def real_ew(arra, arrb):
    diffs = np.where(arra != arrb)
    return len(set(diffs[0]))
# F2P QJ(2) (differing + identical) and the issue ragged QD: each is a
# multi-element VLA object-array column; the element-wise path must RAISE.
vla_cases = [
    ([[0,1],[2,3]], [[1,2],[3,4]]),  # F2P QJ(2) differing
    ([[0,1],[2,3]], [[0,1],[2,3]]),  # F2P QJ(2) identical
    ([[0],[0,0]],   [[0],[0,0]]),    # issue ragged QD
    ([[1,2,3],[4,5,6]], [[1,2,3],[4,5,9]]),
]
bad = 0
for ra, rb in vla_cases:
    arra = _obj(ra); arrb = _obj(rb)
    try:
        v = real_ew(arra, arrb)
        print("DISAGREE: element-wise path did NOT raise on VLA %r/%r -> %r" % (ra, rb, v))
        bad += 1
    except ValueError:
        pass  # expected: not applicable -> raise
if bad:
    print("FAIL: element-wise path did not raise on %d VLA columns" % bad)
    sys.exit(1)
print("OK element-wise np.where path RAISES on %d multi-element VLA columns (the governing-comparator claim grounded)" % len(vla_cases))
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-ref1-routing-observation-soundness",
        "axiom": "rows_hold_subarrays",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_ROUTING,
        "rationale": (
            "The routing observation `rows_hold_subarrays` is a DATA INPUT of "
            "the model, not an opaque symbol, so what must hold is that it "
            "really is the property of the MATERIALISED pair of columns that "
            "decides which comparator the real code applies. This probe builds "
            "real column pairs -- both variable-length designators with and "
            "without a declared layout, fixed-width numeric columns of several "
            "widths, and columns declaring a multi-axis layout -- and checks the "
            "observation against the real storage of each, requiring BOTH "
            "classes to be exercised (non-vacuity). Its decisive leg checks that "
            "the observation follows the STORAGE and not the descriptor "
            "spelling, which is the fact the routing clause rests on and the one "
            "an earlier revision left unpinned: when the routing predicate was "
            "an opaque axiom, this lane pinned only the bundle\'s own "
            "transcription of a descriptor test and so could not tell a "
            "storage-routed impl from a spelling-routed one. It also records that "
            "a boxed column is a 1-D listing of one value per row, which is why "
            "the closeness clause needs no framing side condition. If the real "
            "callee disagrees => AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-ref2-row-granular-count-soundness",
        "axiom": "row_granular_count",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_ROWGRAN,
        "rationale": (
            "A-reference 2a/2b/2c: the row-granular fold must equal the REAL "
            "per-column accumulation len(set(diffs[0])) on BOTH comparators, "
            "each folded over ITS OWN per-position verdict's summary (row-aware "
            "closeness, element-wise plain inequality), including multi-element "
            "fixed-width columns where a naive element sum diverges from the row "
            "count (non-vacuous). 2c then checks that the two summaries are "
            "INCOMPARABLE — the justification for the precondition stating NO "
            "relation between them — and requires a real witness for EACH "
            "direction: a position where closeness rejects and inequality does "
            "not (a self-compared non-finite-component complex value, which the "
            "closeness verdict is not reflexive on) and one where inequality "
            "reports and closeness does not (64-bit neighbours the closeness "
            "verdict cannot separate). Both witnesses are required, so the "
            "spec's silence about the relation is earned rather than assumed; "
            "their existence also makes the two carriers genuinely distinct, "
            "without which a misrouting would be unobservable. Any disagreement "
            "on a reachable column => AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-ref2d-elementwise-not-applicable-to-vla",
        "axiom": "governing comparator",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _PROBE_APPLIC,
        "rationale": (
            "A-reference 2d (control-flow effect): grounds the spec's statement "
            "that the element-wise comparator is not applicable to a column "
            "whose rows hold variable-length sub-arrays, so the closeness "
            "verdict is the one GOVERNING such a column. The real element-wise "
            "path RAISES ValueError on a genuine multi-element VLA object-array "
            "column (F2P QJ(2) + the issue's QD). If it did NOT raise — if the "
            "element-wise comparator were silently applicable there — the "
            "postcondition's first clause would be picking a governing verdict "
            "the real code does not pick. The raise confirms it does."
        ),
    },
]
