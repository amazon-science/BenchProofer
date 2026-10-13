"""properties.py — G-PBT falsification battery for django__django-12741 (velvet).

NOT a Velvet module; a record of adversarial cases the G-PBT gate executes.
Each SPEC case is a full ``Solution.lean`` variant that shares the FROZEN spec
byte-for-byte (region surgery: only text inside the ``-- impl-start`` /
``-- impl-end`` region, or inside the ``prove_correct`` tactic body, is changed
— both regions the consumer spec view elides — so ``markers.same_spec`` holds
and the ``prove_correct runBatch`` obligation survives with a byte-identical
statement) and swaps in a candidate implementation; it is checked by the real
verifier. ``expect:"verify"`` passes iff (in scope AND verifies);
``expect:"reject"`` passes iff (in scope AND does NOT verify AND its refutation
``witness`` discriminates: the witness must ELABORATE against the rival and FAIL
against the frozen solution).

DEFENDED SURFACE (one contracted method over a connection-bound batch
operation). A connection carries its OWN identifier (``ownAlias``); the
operation is handed a separately-supplied identifier alongside the statement
list, and returns the pair of (identifier the scoped operation is opened under,
statements replayed, in order):

  runBatch (conn : Connection) (suppliedKey : List Char)
           (sqlList : List (List Char)) return (out : ...)
    ensures out = flushSpec conn sqlList
    ensures out.1 = conn.ownAlias
    ensures out.2 = sqlList

``flushSpec conn sqlList = (conn.ownAlias, sqlList)`` is a fully-unfolded ``def``
in the ``pure`` region — there is NO opaque answer key to echo; pinning
``out = flushSpec ...`` IS the work. Two INDEPENDENT top-level clauses carry the
whole behaviour:

  (1) the scoped operation is opened under the connection's OWN identifier and
      NOT under the separately-supplied key — ``out.1 = conn.ownAlias`` for every
      ``suppliedKey``. This is the independence-from-``suppliedKey`` property (the
      load-bearing fix): a supplied value must not reach the opened identifier.
  (2) the statement list is replayed unchanged and in order —
      ``out.2 = sqlList`` (element-wise, order included).

Every clause is attacked by a reject rival below, and the reject witnesses vary
all three input binders (``conn.ownAlias``, ``suppliedKey``, ``sqlList`` —
including the empty-``sqlList`` sub-domain and a length-2 order-sensitive list),
so no sub-behaviour is left pinned at one point.

ADVERSARIAL READ of the nagini classes on THIS carrier:
  * FRAME/PERMISSION-MUTATION and the CONNECTION-REBIND attack — VACUOUS here.
    The nagini sibling carries the frame-mutation class as MANDATORY because both
    read-only inputs hold a fractional heap permission (``Acc(..., 1/2)``) a rival
    could illegally demand at full strength, and the rebind attack exploits the
    absence of a ``self.connection is Old(self.connection)`` frame. Lean and
    Velvet are referentially transparent: the inputs are immutable values, this
    bundle declares no ``mut`` parameter, there is no heap, no aliasing, and no
    mutable ``self`` to rebind — so there is no read-only input to overwrite and
    no connection handle to swap. Not fabricated (per the porting map: this
    class is vacuous on Lean/Velvet).
  * SAVEPOINT clause — NOT MODELED on this carrier. The nagini sibling pins a
    third clause (the scoped operation's savepoint flag equals the connection's
    declared capability). This bundle's mapping.md records that flag as UNCHANGED
    by the fix and orthogonal to the modeled identifier-sourcing, so it is elided
    (identity) and there is no ``savepoint`` clause in this spec to attack. The
    sibling's savepoint-flip rival therefore has NO counterpart here — the toggled
    field simply does not exist in the modeled output. Documented, not fabricated.
  * UNGROUNDED-ORACLE ECHO — N/A as a distinct class, exactly as the sibling
    records: ``flushSpec`` is a concrete ``def`` in the ``pure`` region and the
    ``axioms`` region is empty, so there is no answer key to echo. The honest
    grounded controls (a correct reshape + an admissibility non-degeneracy
    assert) are the sibling's directive-2 substitute, carried here.
  * PARTIAL-DOMAIN / VALUE — the core attacks. Each rival is correct on part of
    the domain but diverges on a sub-domain: source the opened identifier from the
    supplied key (unconditionally, or only on the empty batch), or replay a WRONG
    statement list (drop the last, reverse the order). The two whole-value
    equalities are what reject each divergence.

WITNESS MECHANICS ON THIS BUNDLE. The frozen impl is straight-line (two ``let``s
and a ``return`` of a pair), so its extracted program reduces under ``decide``
and a reject rival written the same straight-line way does too. Each reject case
is refuted by a witness ``runBatchTester conn suppliedKey sqlList = false``
stated at concrete ``List Char`` literals; it ELABORATES against the (reducible)
rival and — because gold satisfies the spec at every input — FAILS against the
frozen solution under the identical ``decide``. Both halves were checked
out-of-band with ``scripts/lean_verify.sh`` (rival elaborates EXIT 0, gold fails
EXIT 1) for every reject case. No witness binds a hypothesis (every input is a
concrete literal that ``decide`` reduces), so there is no carrier-conditioning
and no consistency-probe obligation.

AXIOM lane: EMPTY (``meta.json`` declares no ``axiom`` and no A-reference deep
model; the two observables are modeled DEEPLY as ``flushSpec`` — the opened
identifier is the connection's own field and the replay is the identity on the
statement list, both I ops, not axiomatized callees). There is no
axiom-soundness / axiom-containment obligation to probe here, and the gate
ignores ``AXIOM_TESTS`` regardless. (The sibling's ``ax-recorded-effects-sound``
probe is a G-AX concern and is dropped per the porting map.)
"""
from pathlib import Path

INSTANCE = "django__django-12741"
BACKEND = "velvet"

_BASE = (Path(__file__).parent / "Solution.lean").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- impl-region anchors. Each lies wholly inside the single impl region and
# ---- is unique in Solution.lean (both facts asserted at load by _swap). ----

# The whole frozen impl BODY (the two `let`s and the `return`, excluding the
# comment lines). Rivals replace it with a straight-line computable impl so their
# extracted program reduces under `decide`.
_IMPL = (
    "    let openedUnder : List Char := conn.ownAlias\n"
    "    let replayed : List (List Char) := sqlList\n"
    "    return (openedUnder, replayed)\n"
)

# The two `let`-binding lines only (for the positive control, which keeps the
# `return` and only reorders the two independent bindings).
_LETS = (
    "    let openedUnder : List Char := conn.ownAlias\n"
    "    let replayed : List (List Char) := sqlList\n"
)

# The first line of the impl body (an anchor for the admissibility assert, which
# is inserted ahead of the verbatim body).
_OPEN_LINE = "    let openedUnder : List Char := conn.ownAlias\n"

# ---- proof-body anchor. The `prove_correct` TACTIC BODY is elided from the
# ---- consumer spec view (only the header/statement survives), so a variant may
# ---- retune the tactic script without touching the spec or dropping the
# ---- obligation. The body below is the frozen script, unique in the file. ----
_PROOF = "prove_correct runBatch by\n  loom_solve"
assert _BASE.count(_PROOF) == 1, "prove_correct body drifted from expected text"


def _impl(new_body: str) -> str:
    """Full Solution.lean variant with ONLY the impl body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---- witness preamble. The spec is a `method` CONTRACT, not a bare predicate,
# ---- so a witness reaches it through Velvet's tester machinery:
# ---- `runBatchTester conn suppliedKey sqlList = false` says the extracted
# ---- program's result violates the postcondition at that concrete input.
# ---- Checked in a file whose `prove_correct` block is stripped, so no tactic
# ---- script can mask the verdict. The method has no `require` clause, so every
# ---- input reaches the postcondition rather than vacuously passing.
_TESTER = (
    "extract_program_for runBatch\n"
    "prove_precondition_decidable_for runBatch\n"
    "prove_postcondition_decidable_for runBatch\n"
    "derive_tester_for runBatch\n\n"
)


def _witness(call: str) -> str:
    return _TESTER + f"example : {call} = false := by\n  decide\n"


SPEC_TESTS = [
    # =====================================================================
    # POSITIVE CONTROL (soundness) — a structurally different but CORRECT
    # impl that MUST verify. If a faithful correct impl cannot verify the
    # spec is SPEC-TOO-STRONG. The two INDEPENDENT bindings (opened identifier /
    # replayed statements) are REORDERED; the returned pair is byte-identical, so
    # both `ensures` clauses still hold and the frozen `loom_solve` proof closes
    # unchanged.
    # =====================================================================
    {
        "id": "pos-reorder-binds",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(
            _BASE, _LETS,
            "    let replayed : List (List Char) := sqlList\n"
            "    let openedUnder : List Char := conn.ownAlias\n"),
        "rationale": "reordering the two independent bindings (bind `replayed` "
                     "first, then `openedUnder`) leaves the returned pair "
                     "identical, so `out = flushSpec conn sqlList`, "
                     "`out.1 = conn.ownAlias` and `out.2 = sqlList` all still "
                     "hold; the frozen `loom_solve` proof closes unchanged. A "
                     "faithful correct reshape that could NOT verify would mean "
                     "SPEC-TOO-STRONG.",
    },

    # =====================================================================
    # ADMISSIBILITY — the method carries NO `require` clause, so no input is
    # excluded and the usual "a normal input satisfies the precondition" probe
    # is vacuous. The residual admissibility risk on a total domain is that the
    # post-image is UNSATISFIABLE / DEGENERATE — a spec no impl can meet reads
    # exactly like a spec every impl meets. So the assert has TWO jobs.
    #
    # (a) JOINT SATISFIABILITY AT AN F2P-SHAPED POINT (the total-carrier analogue
    #     of "a normal input satisfies the precondition"). A concrete output pair
    #     `(['x'], [['s']])` is exhibited and shown to discharge ALL THREE
    #     `ensures` clauses SIMULTANEOUSLY at the F2P-shaped input
    #     (ownAlias=['x'], suppliedKey=['y'] ≠ ownAlias, sqlList=[['s']]) — the
    #     very point where the independence-from-`suppliedKey` property bites and
    #     where every clause-(1) rival below is refuted. Per-clause consistency
    #     does not imply the conjunction is inhabited there; exhibiting the
    #     witness pair by evaluation, as a `have`-style assert BEFORE the frozen
    #     obligation closes, is what rules out a jointly-unsatisfiable post-image.
    # (b) NON-DEGENERACY: the opened identifier tracks the connection's own alias
    #     (['a'] vs ['b'] give two different opened identifiers, so clause (1) is
    #     not a constant) and the replay tracks the statement list ([['s']] vs []
    #     give different replays, so clause (2) is not a constant).
    #
    # The impl is kept verbatim so the method's own `ensures` still discharges;
    # `loom_solve` alone also clears the assert VC, so NO proof retune is needed.
    # LIVENESS is machine-checked, not asserted: flipping the (a) conjunct to
    # claim the opened identifier is the SUPPLIED key `['y']` leaves
    # `unsolved goals case admiss_1` (EXIT 1), so the assert is a real VC.
    # =====================================================================
    {
        "id": "admiss-nondegenerate",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(
            _BASE, _OPEN_LINE,
            "    assert (with_name_prefix `admiss\n"
            # (a) all three clauses jointly inhabited at the F2P-shaped point,
            #     where suppliedKey (['y']) differs from ownAlias (['x']).
            "      (((['x'], [['s']]) : (List Char) × (List (List Char)))\n"
            "           = flushSpec { ownAlias := ['x'] } [['s']] ∧\n"
            "       (((['x'], [['s']]) : (List Char) × (List (List Char))).1 "
            "= ['x']) ∧\n"
            "       (((['x'], [['s']]) : (List Char) × (List (List Char))).2 "
            "= [['s']]) ∧\n"
            # (b) neither clause is a constant function of its input.
            "       (flushSpec { ownAlias := ['a'] } [['s']]).1 = ['a'] ∧\n"
            "       (flushSpec { ownAlias := ['b'] } [['s']]).1 = ['b'] ∧\n"
            "       (flushSpec { ownAlias := ['a'] } [['s']]).2 = [['s']] ∧\n"
            "       (flushSpec { ownAlias := ['a'] } ([] : List (List Char))).2 "
            "= ([] : List (List Char))))\n"
            + _OPEN_LINE),
        "rationale": "the post-image is JOINTLY SATISFIABLE at an F2P-shaped "
                     "input AND non-degenerate. (a) At (ownAlias=['x'], "
                     "suppliedKey=['y'] ≠ ownAlias, sqlList=[['s']]) — the point "
                     "where independence-from-suppliedKey bites — the concrete "
                     "pair (['x'], [['s']]) is exhibited by evaluation and "
                     "discharges all three `ensures` clauses AT ONCE, so the "
                     "conjunction is inhabited there and no clause is "
                     "individually satisfiable only at the cost of another. This "
                     "is the total-carrier analogue of the precondition-admits-a-"
                     "normal-input probe: an obligation unsatisfiable at exactly "
                     "an F2P-shaped input would otherwise read as trivially met. "
                     "(b) Both clauses genuinely vary with their inputs (['a'] vs "
                     "['b'] give different opened identifiers; [['s']] vs [] give "
                     "different replays), so neither is a constant. The impl body "
                     "is kept verbatim so `out = flushSpec ...` and both "
                     "subsidiary clauses discharge too, and `loom_solve` alone "
                     "clears the assert (no proof retune). Liveness is "
                     "machine-checked: flipping the (a) conjunct to claim the "
                     "opened identifier is the supplied key ['y'] leaves "
                     "`unsolved goals case admiss_1`.",
    },

    # =====================================================================
    # UNIQUENESS / SPEC-TOO-WEAK rivals — wrong impls sharing the frozen spec
    # that MUST be rejected. Each is a straight-line COMPUTABLE impl (so its
    # witness reduces under `decide`), refuted at a concrete input by a witness
    # that fails on the frozen solution, and each carries the refinement argument
    # that its faithful real counterpart would NOT resolve the F2P.
    # =====================================================================
    {
        "id": "weak-open-under-supplied",
        "kind": "uniqueness",
        "expect": "reject",
        # Sources the opened identifier from the SEPARATELY-SUPPLIED key instead
        # of the connection's own alias — the exact pre-fix behaviour. Correct on
        # every input where the supplied key happens to equal the connection's own
        # alias, wrong precisely when they differ.
        "module": _impl(
            "    let openedUnder : List Char := suppliedKey\n"
            "    let replayed : List (List Char) := sqlList\n"
            "    return (openedUnder, replayed)\n"),
        "refinement": "opening the scope under the separately-supplied identifier "
                      "is the pre-fix behaviour. A faithful patch that kept it "
                      "would open the batch's scoped operation under a "
                      "caller-threaded value rather than the connection's own "
                      "identifier; the F2P calls the operation with NO supplied "
                      "identifier and asserts the connection's OWN store was "
                      "emptied, so a scope taken from the supplied value does NOT "
                      "resolve.",
        "rationale": "REJECT from `out.1 = conn.ownAlias`: this rival returns "
                     "`suppliedKey`. On an input where the supplied key differs "
                     "from the connection's own alias (ownAlias=['x'], "
                     "suppliedKey=['y']) the opened identifier is ['y'] but the "
                     "spec demands ['x'], so clause (1) fails. Refuted with "
                     "suppliedKey ≠ ownAlias — the sub-domain the "
                     "independence-from-suppliedKey property pins.",
        "witness": _witness("runBatchTester { ownAlias := ['x'] } ['y'] [['s']]"),
    },
    {
        "id": "weak-open-supplied-on-empty",
        "kind": "uniqueness",
        "expect": "reject",
        # Partial-domain: opens under the connection's own alias on any NON-empty
        # batch (clause (1) holds there) but under the supplied key on the EMPTY
        # batch. Correct everywhere except the legal empty-batch sub-domain.
        "module": _impl(
            "    let openedUnder : List Char :=\n"
            "      if sqlList.isEmpty then suppliedKey else conn.ownAlias\n"
            "    let replayed : List (List Char) := sqlList\n"
            "    return (openedUnder, replayed)\n"),
        "refinement": "a patch that only sources the identifier correctly when at "
                      "least one statement is present still mis-sources the (legal) "
                      "empty batch — the scope of an empty flush is opened under a "
                      "caller-threaded value rather than the connection's own "
                      "identifier. The empty statement list is an in-domain input "
                      "the operation is still called on, and its scope must still "
                      "open on the connection itself, so the faithful patch does "
                      "NOT resolve.",
        "rationale": "REJECT from `out.1 = conn.ownAlias`: on the empty-batch "
                     "sub-domain this rival returns `suppliedKey`. On "
                     "(ownAlias=['a'], suppliedKey=['b'], sqlList=[]) the opened "
                     "identifier is ['b'] but the spec demands ['a'], so clause "
                     "(1) fails. Refuted with sqlList at its EMPTY value — the "
                     "only witness that probes the empty-batch sub-domain.",
        "witness": _witness("runBatchTester { ownAlias := ['a'] } ['b'] []"),
    },
    {
        "id": "weak-open-under-alias-plus-supplied",
        "kind": "uniqueness",
        "expect": "reject",
        # NEAR-MISS on clause (1). Every other clause-(1) rival REPLACES the
        # connection's own identifier with the supplied key, so a spec that merely
        # demanded "the own identifier appears somewhere in the opened identifier"
        # (a prefix/containment check rather than EQUALITY) would still reject them.
        # This rival keeps `conn.ownAlias` as a genuine PREFIX and only APPENDS the
        # supplied key, so it passes any such weakened containment reading and is
        # rejected only by the exact equality the frozen clause states. It also
        # pins that the supplied key must not reach the opened identifier even
        # PARTIALLY — leaking it by concatenation is still a leak. Correct exactly
        # when suppliedKey is empty, wrong on every non-empty supplied key.
        "module": _impl(
            "    let openedUnder : List Char := conn.ownAlias ++ suppliedKey\n"
            "    let replayed : List (List Char) := sqlList\n"
            "    return (openedUnder, replayed)\n"),
        "refinement": "concatenating the supplied identifier onto the connection's "
                      "own one still lets a caller-threaded value determine the "
                      "identifier the scope is opened under — the resulting "
                      "identifier names no configured connection at all, so the "
                      "scoped operation is opened under a bogus key rather than the "
                      "connection's own. The F2P calls the operation with NO "
                      "supplied identifier and asserts the connection's OWN store "
                      "was emptied; an identifier contaminated by a supplied value "
                      "does NOT resolve.",
        "rationale": "REJECT from `out.1 = conn.ownAlias`: this rival returns "
                     "`conn.ownAlias ++ suppliedKey`. On (ownAlias=['x'], "
                     "suppliedKey=['y'], sqlList=[['s']]) the opened identifier is "
                     "['x','y'] but the spec demands ['x'], so clause (1) fails. "
                     "This is the sharpest clause-(1) near-miss: the own identifier "
                     "is still a PREFIX of the result, so the case attests that the "
                     "clause is an EQUALITY and not a containment/prefix test, and "
                     "that a supplied value must not reach the opened identifier "
                     "even partially.",
        "witness": _witness("runBatchTester { ownAlias := ['x'] } ['y'] [['s']]"),
    },
    {
        "id": "weak-drop-last-statement",
        "kind": "uniqueness",
        "expect": "reject",
        # Replays sqlList.dropLast: correct on the opened identifier and on the
        # in-order prefix, but stops one short so the LAST supplied statement is
        # never replayed. Clause (2) fails on any non-empty batch.
        "module": _impl(
            "    let openedUnder : List Char := conn.ownAlias\n"
            "    let replayed : List (List Char) := sqlList.dropLast\n"
            "    return (openedUnder, replayed)\n"),
        "refinement": "silently dropping the final statement leaves the store not "
                      "fully flushed — the last flush statement is never replayed "
                      "through the connection. The F2P asserts the tables are "
                      "actually empty after the call, which a truncated replay "
                      "cannot achieve, so the faithful patch does NOT resolve.",
        "rationale": "REJECT from `out.2 = sqlList`: dropping the last element "
                     "replays sqlList.dropLast, not sqlList. On a non-empty batch "
                     "(ownAlias=['c'], suppliedKey=['c'], sqlList=[['s']]) the "
                     "replay is [] but the spec demands [['s']], so clause (2) "
                     "fails. Refuted on a non-empty batch where the dropped last "
                     "element is the qualifying one.",
        "witness": _witness("runBatchTester { ownAlias := ['c'] } ['c'] [['s']]"),
    },
    {
        "id": "weak-reverse-statements",
        "kind": "uniqueness",
        "expect": "reject",
        # Replays sqlList.reverse: the right MULTISET of statements but in the
        # wrong ORDER. Correct on the opened identifier and on any palindromic /
        # length-≤1 batch, but reorders any batch of length ≥ 2.
        "module": _impl(
            "    let openedUnder : List Char := conn.ownAlias\n"
            "    let replayed : List (List Char) := sqlList.reverse\n"
            "    return (openedUnder, replayed)\n"),
        "refinement": "replaying the statements in reverse issues the same SQL but "
                      "in the wrong order; flush statements have ordering "
                      "dependencies (a reset must follow the delete it depends on), "
                      "so a reversed replay can fail or leave the store in a wrong "
                      "state. The F2P exercises a real ordered batch and asserts a "
                      "clean flush, so the faithful patch does NOT resolve.",
        "rationale": "REJECT from `out.2 = sqlList`: `sqlList.reverse` equals "
                     "`sqlList` only on length-≤1 or palindromic batches. On a "
                     "length-2 batch with distinct elements (ownAlias=['d'], "
                     "suppliedKey=['d'], sqlList=[['x'], ['y']]) the replay is "
                     "[['y'], ['x']] but the spec demands [['x'], ['y']], so "
                     "clause (2) fails. Refuted over a length-2 ordered list, "
                     "exercising list length and order.",
        "witness": _witness(
            "runBatchTester { ownAlias := ['d'] } ['d'] [['x'], ['y']]"),
    },
]


# ---------------------------------------------------------------------------
# Nagini -> velvet accounting. The sibling battery has 8 SPEC cases (1 soundness
# positive, 1 admissibility, 3 frame/rebind-mutation rivals, 3 partial-domain
# rivals — including a savepoint-flip) plus 1 AXIOM_TEST. This bundle models a
# NARROWED carrier: the connection is a `Connection` structure with only the
# touched field `ownAlias`, the batch is `List (List Char)`, and the observable
# output is the pair (opened identifier, replayed statements). The savepoint flag
# is UNCHANGED by the fix and elided (identity) — so the whole savepoint clause,
# and the sibling's savepoint-flip rival, have no counterpart here. The
# fractional-permission frame class and the connection-rebind attack are vacuous
# on a referentially-transparent carrier with no heap, no aliasing, and no
# mutable `self`.
#
#   sibling case                 -> here                       disposition
#   -----------------------------------------------------------------------------
#   pos-control-reorder          -> pos-reorder-binds           PORTED
#   admiss-fshaped               -> admiss-nondegenerate        RE-AIMED
#   frame-mut-alias              -> (none)                      VACUOUS
#   frame-mut-sqllist            -> (none)                      VACUOUS
#   rebind-connection            -> (none)                      VACUOUS
#   partial-domain-empty         -> weak-open-supplied-on-empty PORTED
#   partial-domain-drop-last     -> weak-drop-last-statement    PORTED
#   savepoint-flip               -> (none)                      NOT MODELED
#   (no sibling)                 -> weak-open-under-supplied     ADDED
#   (no sibling)                 -> weak-reverse-statements      ADDED
#   (no sibling)                 -> weak-open-under-alias-plus-supplied  ADDED (audit)
#   ax-recorded-effects-sound    -> (none)                      DROPPED
#
# 3 ported, 1 re-aimed, 3 vacuous, 1 not-modeled, 3 added, 1 dropped.
#
# PORTED (positive control): the sibling reorders the two independent recorder
#   writes and keeps the loop invariant verbatim. Here the two independent
#   bindings (opened identifier / replayed statements) are reordered; the returned
#   pair is byte-identical so the frozen `loom_solve` proof closes unchanged.
#   Verified to build (EXIT 0).
# RE-AIMED (admissibility): the sibling asserts F2P-shaped facts (len>=0; the
#   connection's own alias readable) hold at entry. This backend has no `require`
#   clause, so that probe is vacuous. It is re-aimed at the residual total-domain
#   risk — a DEGENERATE/unsatisfiable post-image — via an in-region assert that
#   both clauses genuinely vary with their inputs (the opened identifier tracks
#   two different connection aliases; the replay tracks a non-empty vs empty
#   batch). The impl is kept verbatim so the ensures still discharges; `loom_solve`
#   alone also clears the assert (no retune). Verified: the true assert builds
#   (EXIT 0) and a falsified assert leaves an unsolved goal (EXIT 1), so the assert
#   is live.
# VACUOUS (frame-mut-alias, frame-mut-sqllist, rebind-connection): the sibling
#   carries these because each read-only input holds a fractional heap permission
#   a rival could demand at full strength (write the connection's own alias, or
#   retro-extend the caller's statement list), and because `self.connection` can be
#   rebound to a throwaway object without an identity frame. Lean and Velvet are
#   referentially transparent, have no heap/aliasing, declare no `mut` parameter,
#   and have no mutable `self` — the inputs are immutable values and there is no
#   connection handle to swap. No substitute fabricated (per the porting map: this
#   class is vacuous here).
# NOT MODELED (savepoint-flip): the sibling's third clause pins the scoped
#   operation's savepoint flag to the connection's declared capability. mapping.md
#   records that flag as UNCHANGED by the fix and orthogonal to the modeled
#   identifier-sourcing, so it is elided (identity) and there is no savepoint field
#   in this bundle's modeled output. The toggled value the sibling's rival negates
#   simply does not exist here, so the rival has no counterpart. This is carrier
#   narrowing, not an omitted attack.
# PORTED (partial-domain-empty, partial-domain-drop-last): the empty-batch
#   mis-scope becomes weak-open-supplied-on-empty (sources the opened identifier
#   from the supplied key only on the empty batch); the drop-last-statement rival
#   becomes weak-drop-last-statement (replays sqlList.dropLast). Each carries a
#   machine-checked witness that ELABORATES against its straight-line rival (EXIT 0)
#   and FAILS against the frozen solution (EXIT 1).
# ADDED (3, no sibling counterpart): weak-open-under-supplied attacks clause (1)
#   over the WHOLE domain (source the opened identifier from the supplied key
#   unconditionally — the pre-fix behaviour, the sharpest attack on the
#   independence-from-suppliedKey property, refuted wherever suppliedKey ≠
#   ownAlias). weak-reverse-statements attacks clause (2)'s ORDER dimension
#   specifically (right multiset, wrong order — refuted only on a length-≥2 batch),
#   which the drop-last rival (a length attack) does not exercise.
#   weak-open-under-alias-plus-supplied (added during the independent audit) is the
#   clause-(1) NEAR-MISS: it keeps conn.ownAlias as a genuine PREFIX and only
#   appends the supplied key, so unlike the two replace-the-identifier rivals it
#   survives any weakened containment/prefix reading of clause (1) and is rejected
#   only by the exact equality — attesting that a supplied value must not reach the
#   opened identifier even PARTIALLY. Witness rebuilt out-of-band: rival EXIT 0,
#   gold EXIT 1 (`decide` proved the tester true at that input); the flipped-claim
#   forgery inverts (gold EXIT 0, rival EXIT 1), so gold's exit code tracks the
#   claim rather than a syntactic artifact.
# DROPPED (ax-recorded-effects-sound): the sibling's axiom lane re-runs the
#   real-callee recorded-effect soundness check. That is a G-AX concern; this
#   bundle declares no axiom and no A-reference deep model (the two observables are
#   modeled deeply as `flushSpec`, both I ops), so there is nothing for the axiom
#   lane to probe and the gate ignores AXIOM_TESTS regardless.
#
# BINDER / DOMAIN COVERAGE of the four reject witnesses over the three input
#   binders and the two clauses:
#     conn.ownAlias — ['x'], ['a'], ['c'], ['d']: varied across witnesses (never
#                     pinned at one value), so a rival mishandling only a specific
#                     alias could not hide.
#     suppliedKey   — ['y'] (≠ ownAlias, the clause-(1) attack), ['b'] (≠ ownAlias
#                     on the empty batch), ['c']/['d'] (= ownAlias, so the replay
#                     rivals are refuted while suppliedKey is INNOCENT — proving the
#                     replay clause does not secretly depend on the key).
#     sqlList       — [['s']] (non-empty), [] (EMPTY, only witness in that
#                     sub-domain), [['s']] (non-empty for drop-last), [['x'],['y']]
#                     (length 2, order-sensitive): varied in length and content.
#   CLAUSES: `out.1 = conn.ownAlias` attacked by weak-open-under-supplied and
#     weak-open-supplied-on-empty; `out.2 = sqlList` attacked by
#     weak-drop-last-statement (length) and weak-reverse-statements (order). The
#     conjunct clause `out = flushSpec conn sqlList` is entailed by the two
#     projections and is violated by every rival. All four reject witnesses probe
#     DISTINCT input points (pts=4).
#
# AXIOM_TESTS: dropped. The axiom lane is G-AX's job and this bundle declares no
# axiom and no A-reference deep model, so there is nothing there to probe.
AXIOM_TESTS = []
