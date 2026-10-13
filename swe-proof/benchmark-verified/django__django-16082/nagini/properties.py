# properties.py — PBT falsification battery for django__django-16082.
#
# NOT a Nagini module; a manifest the runner (swebench_nagini.pbt) parses. Each
# SPEC_TESTS case is a full model.py variant built by REGION SURGERY: we _swap
# the single `# impl-start` .. `# impl-end` body of resolve_combined_type and
# leave the frozen spec (axioms / pure / pre / post-conditions / signatures)
# byte-identical. same_spec is therefore guaranteed for every case.
#
# Defended surface (read from model.py / refinement.md / mapping.md / instance.json):
#   resolve_combined_type(connector, lhs_type, rhs_type) -> int resolves a binary
#   combination of two operand field types under a connector to a result
#   field-type code, by scanning the rows the registry records for that
#   connector. The precondition admits EVERY connector code (registered or not)
#   and EVERY operand field-type code, so no in-repo call site is modelled away.
#
#   The load-bearing postcondition clauses pin, over that whole open domain:
#     (T)  the result is the unresolved sentinel or a RECORDED result type, and
#          it is a real type EXACTLY when some recorded row matches
#          (`has_permitted_combination == (Result() != T_NONE)`) — a totality
#          claim, so no (connector, lhs, rhs) point is left free;
#     (S)  same-type numeric -> that type, for the five arithmetic connectors
#          and exponentiation;
#     (M)  MIXED numeric -> the WIDER type, for EVERY arithmetic connector with
#          the remainder connector on the SAME footing (the discriminating
#          clauses: the pre-patch registry omits the remainder connector from
#          the mixed-type numeric rows);
#     (K)  the integer clauses are quantified over the OPEN family of field
#          types BELOW the integer type (`is_int_kind`, an unbounded band of
#          codes at or above T_INT_SUB), not over a finite list of integer
#          variants — matching is by SUBTYPING, so no finite normalization
#          table can discharge them;
#     (P)  exponentiation records the same-type numeric rows but NO mixed-type
#          numeric row;
#     (N)  the null-literal type combines only with the float type;
#     (B)  a bitwise connector resolves two integer-family operands to integer
#          and leaves every other operand pair unresolved;
#     (D)  the date/time rows under addition and under subtraction, including
#          their asymmetry (date-date is a duration under subtraction but
#          unresolved under addition; a duration on the left of a date operand
#          resolves under addition but not under subtraction);
#     (U)  an operand type below no recorded operand type, and a connector with
#          no recorded rows, resolve nothing.
#
#   The DISCRIMINATING clauses are (M): the gold change records the mixed-type
#   numeric rows for the remainder connector too, so mixed numeric operands
#   resolve to the WIDER type under it as they already did under the other four
#   arithmetic connectors. Those clauses are NOT parameterised away by
#   connector: they must hold for all five arithmetic connectors uniformly, so
#   any impl that resolves the mixed rows only for the non-remainder connectors
#   (the pre-patch state) fails them.
#
# Read-only inputs: NONE. All three params (connector, lhs_type, rhs_type) are
# immutable `int` value scalars — there is no object reference and therefore no
# Acc(x, 1/2) half-permission read-only input. The frame-mutation weakness class
# (overwrite a read-only input to satisfy the postcondition vacuously) is
# STRUCTURALLY INAPPLICABLE here: there is nothing to mutate (an int param cannot
# be aliased/written through to forge the Result). See 'assessment' in the
# structured return. has_readonly_input=False; frame_mutation_included=False.
#
# Oracle grounding: is_int_kind / is_date_kind / is_subtype / row /
# records_* / has_permitted_combination are @Pure helpers that are FULLY
# UNFOLDED grounded predicates (functions of the args; no @ContractOnly axiom,
# no opaque answer-key). There is no ungrounded oracle to echo. The
# echo-shaped rival is instead an impl that satisfies the clauses by TABLE
# LOOKUP over the finitely many named type codes while getting the open bands
# wrong; `weak-exact-match-normalize` and `weak-int-band-truncated` below are
# exactly that shape, and they must reject.
#
# Control-flow-effect: N/A. resolve_combined_type is a pure value function whose
# only observable is the returned int code; there is no raise / side-effect /
# capability difference invisible to the value abstraction. The clause set is
# TOTAL over the open domain (clause (T) plus the per-family clauses pin a
# unique result at every point), so a capability-token rival would add nothing.
# Omitted; see 'assessment'.
from pathlib import Path

INSTANCE = "django__django-16082"
FLOAT_ENCODING = None  # meta.json float_encoding is null (field-type / connector int codes only)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# The single whole-impl anchor: the exact gold cascade body, from the comment
# header through `return T_NONE`. The trailing `# impl-end` marker is kept OUT
# of the swap so the region boundary is never touched and same_spec holds.
# ---------------------------------------------------------------------------

_GOLD_IMPL = """    # Scan the rows recorded for this connector in registration order and
    # return the recorded result type of the first matching row, else the
    # unresolved sentinel. The rows are, per family:
    #   numeric same-type (five arithmetic connectors + exponentiation):
    #       (int,int)->int  (flt,flt)->flt  (dec,dec)->dec
    #   numeric mixed-type (every arithmetic connector, remainder included on
    #   the same footing; NOT exponentiation):
    #       (int,dec)->dec  (dec,int)->dec  (int,flt)->flt  (flt,int)->flt
    #   numeric with the null-literal type (same connectors as same-type):
    #       (flt,null)->flt  (null,flt)->flt
    #   bitwise (five bitwise connectors): (int,int)->int
    #   date/time under addition and under subtraction, as recorded.
    if records_same_type_numeric(connector):
        if row(T_INT, T_INT, lhs_type, rhs_type):
            return T_INT
        if row(T_FLT, T_FLT, lhs_type, rhs_type):
            return T_FLT
        if row(T_DEC, T_DEC, lhs_type, rhs_type):
            return T_DEC
    if records_mixed_numeric(connector):
        if row(T_INT, T_DEC, lhs_type, rhs_type):
            return T_DEC
        if row(T_DEC, T_INT, lhs_type, rhs_type):
            return T_DEC
        if row(T_INT, T_FLT, lhs_type, rhs_type):
            return T_FLT
        if row(T_FLT, T_INT, lhs_type, rhs_type):
            return T_FLT
    if records_same_type_numeric(connector):
        if row(T_FLT, T_NULL, lhs_type, rhs_type):
            return T_FLT
        if row(T_NULL, T_FLT, lhs_type, rhs_type):
            return T_FLT
    if records_bitwise_integer(connector):
        if row(T_INT, T_INT, lhs_type, rhs_type):
            return T_INT
    if connector == C_ADD:
        if row(T_DATE, T_DUR, lhs_type, rhs_type):
            return T_DTM
        if row(T_DUR, T_DATE, lhs_type, rhs_type):
            return T_DTM
        if row(T_DUR, T_DUR, lhs_type, rhs_type):
            return T_DUR
        if row(T_TIME, T_DUR, lhs_type, rhs_type):
            return T_TIME
        if row(T_DUR, T_TIME, lhs_type, rhs_type):
            return T_TIME
    if connector == C_SUB:
        if row(T_DATE, T_DUR, lhs_type, rhs_type):
            return T_DTM
        if row(T_DATE, T_DATE, lhs_type, rhs_type):
            return T_DUR
        if row(T_DUR, T_DUR, lhs_type, rhs_type):
            return T_DUR
        if row(T_TIME, T_DUR, lhs_type, rhs_type):
            return T_TIME
        if row(T_TIME, T_TIME, lhs_type, rhs_type):
            return T_DUR
    return T_NONE"""


def _impl(new_body: str) -> str:
    """Replace ONLY resolve_combined_type's impl body (between the comment
    header and `return T_NONE`). The `# impl-end` marker stays put."""
    return _swap(_BASE, _GOLD_IMPL, new_body)


SPEC_TESTS = [
    {
        "id": 'pos-reorder-families',
        "kind": 'soundness',
        "expect": 'verify',
        "module": _impl(
            '    # A correct cascade with the ROW FAMILIES emitted in a different\n'
            '    # order: the date/time rows first, then bitwise, then the numeric\n'
            '    # rows. No query can match rows from two different families under\n'
            '    # one connector (the connector guards for the date/time, bitwise and\n'
            '    # numeric families are mutually exclusive except that addition and\n'
            '    # subtraction record both numeric and date/time rows, and those two\n'
            "    # families' operand types are disjoint), so the order is\n"
            '    # unobservable and this must verify.\n'
            '    if connector == C_ADD:\n'
            '        if row(T_DATE, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DATE, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_TIME, T_DUR, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '        if row(T_DUR, T_TIME, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '    if connector == C_SUB:\n'
            '        if row(T_DATE, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DATE, T_DATE, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_DUR, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_TIME, T_DUR, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '        if row(T_TIME, T_TIME, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '    if records_bitwise_integer(connector):\n'
            '        if row(T_INT, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '    if records_same_type_numeric(connector):\n'
            '        if row(T_INT, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '        if row(T_FLT, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_DEC, T_DEC, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '    if records_mixed_numeric(connector):\n'
            '        if row(T_INT, T_DEC, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '        if row(T_DEC, T_INT, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '        if row(T_INT, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_FLT, T_INT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '    if records_same_type_numeric(connector):\n'
            '        if row(T_FLT, T_NULL, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_NULL, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '    return T_NONE'
        ),
        "rationale": 'a correct cascade with the row families reordered (date/time and bitwise before numeric) must verify: no query matches rows from two families, so family order is unobservable. Else SPEC-TOO-STRONG.',
    },

    {
        "id": 'pos-subtype-dispatch',
        "kind": 'soundness',
        "expect": 'verify',
        "module": _impl(
            '    # A genuinely different SHAPE: instead of testing the recorded rows\n'
            '    # one by one, first map each queried operand type to the RECORDED\n'
            '    # operand type it lies below (the integer family collapses to the\n'
            '    # integer type, the date-time type to the date type, everything else\n'
            '    # is its own recorded type or nothing), then dispatch on that pair.\n'
            '    # This is the same relation computed the other way round, so it must\n'
            '    # verify.\n'
            '    a = T_INT if is_int_kind(lhs_type) else lhs_type  # type: int\n'
            '    b = T_INT if is_int_kind(rhs_type) else rhs_type  # type: int\n'
            '    da = T_DATE if is_date_kind(lhs_type) else lhs_type  # type: int\n'
            '    db = T_DATE if is_date_kind(rhs_type) else rhs_type  # type: int\n'
            '    if records_same_type_numeric(connector):\n'
            '        if a == T_INT and b == T_INT:\n'
            '            return T_INT\n'
            '        if a == T_FLT and b == T_FLT:\n'
            '            return T_FLT\n'
            '        if a == T_DEC and b == T_DEC:\n'
            '            return T_DEC\n'
            '        if a == T_FLT and b == T_NULL:\n'
            '            return T_FLT\n'
            '        if a == T_NULL and b == T_FLT:\n'
            '            return T_FLT\n'
            '    if records_mixed_numeric(connector):\n'
            '        if a == T_INT and b == T_DEC:\n'
            '            return T_DEC\n'
            '        if a == T_DEC and b == T_INT:\n'
            '            return T_DEC\n'
            '        if a == T_INT and b == T_FLT:\n'
            '            return T_FLT\n'
            '        if a == T_FLT and b == T_INT:\n'
            '            return T_FLT\n'
            '    if records_bitwise_integer(connector):\n'
            '        if a == T_INT and b == T_INT:\n'
            '            return T_INT\n'
            '    if connector == C_ADD:\n'
            '        if da == T_DATE and db == T_DUR:\n'
            '            return T_DTM\n'
            '        if da == T_DUR and db == T_DATE:\n'
            '            return T_DTM\n'
            '        if da == T_DUR and db == T_DUR:\n'
            '            return T_DUR\n'
            '        if da == T_TIME and db == T_DUR:\n'
            '            return T_TIME\n'
            '        if da == T_DUR and db == T_TIME:\n'
            '            return T_TIME\n'
            '    if connector == C_SUB:\n'
            '        if da == T_DATE and db == T_DUR:\n'
            '            return T_DTM\n'
            '        if da == T_DATE and db == T_DATE:\n'
            '            return T_DUR\n'
            '        if da == T_DUR and db == T_DUR:\n'
            '            return T_DUR\n'
            '        if da == T_TIME and db == T_DUR:\n'
            '            return T_TIME\n'
            '        if da == T_TIME and db == T_TIME:\n'
            '            return T_DUR\n'
            '    return T_NONE'
        ),
        "rationale": 'a structurally different but correct impl — collapse each queried operand type to the recorded type it lies below, then dispatch on codes — must verify. It normalizes by the OPEN band predicate (is_int_kind / is_date_kind), not by a finite table, so it is behaviourally equal to the row cascade over the whole open domain. Else SPEC-TOO-STRONG.',
    },

    {
        "id": 'admiss-probe-mod-mixed-and-open-band',
        "kind": 'admissibility',
        "expect": 'verify',
        "module": _impl(
            '    if records_same_type_numeric(connector):\n'
            '        if row(T_INT, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '        if row(T_FLT, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_DEC, T_DEC, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '    if records_mixed_numeric(connector):\n'
            '        if row(T_INT, T_DEC, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '        if row(T_DEC, T_INT, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '        if row(T_INT, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_FLT, T_INT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '    if records_same_type_numeric(connector):\n'
            '        if row(T_FLT, T_NULL, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_NULL, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '    if records_bitwise_integer(connector):\n'
            '        if row(T_INT, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '    if connector == C_ADD:\n'
            '        if row(T_DATE, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DATE, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_TIME, T_DUR, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '        if row(T_DUR, T_TIME, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '    if connector == C_SUB:\n'
            '        if row(T_DATE, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DATE, T_DATE, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_DUR, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_TIME, T_DUR, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '        if row(T_TIME, T_TIME, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '    return T_NONE\n'
            '\n'
            '\n'
            'def _admissibility_probe() -> int:\n'
            '    # admissibility probe: the remainder connector over mixed\n'
            '    # integer/decimal operands (the exact issue input), the same query\n'
            '    # with an operand drawn from the OPEN family below the integer type,\n'
            '    # a bitwise query, a date/time query, and an unregistered connector\n'
            '    # each satisfy the precondition and the pinned post consequence is\n'
            "    # derivable. Called from level 3, strictly above the callee's\n"
            '    # MustTerminate(2), so the termination obligation transfers and the\n'
            '    # only thing under test is the precondition.\n'
            '    Requires(MustTerminate(3))\n'
            '    Ensures(Result() == T_DEC)\n'
            '    r1 = resolve_combined_type(C_MOD, T_INT, T_DEC)  # type: int\n'
            '    Assert(r1 == T_DEC)\n'
            '    r2 = resolve_combined_type(C_MOD, T_AUTO, T_DEC)  # type: int\n'
            '    Assert(r2 == T_DEC)\n'
            '    r3 = resolve_combined_type(C_MOD, T_INT_SUB + 7, T_FLT)  # type: int\n'
            '    Assert(r3 == T_FLT)\n'
            '    r4 = resolve_combined_type(C_BITOR, T_INT, T_INT_SUB + 3)  # type: int\n'
            '    Assert(r4 == T_INT)\n'
            '    r5 = resolve_combined_type(C_SUB, T_DTM, T_DATE)  # type: int\n'
            '    Assert(r5 == T_DUR)\n'
            '    r6 = resolve_combined_type(C_POW, T_INT, T_DEC)  # type: int\n'
            '    Assert(r6 == T_NONE)\n'
            '    r7 = resolve_combined_type(C_BITXOR + 5, T_INT, T_INT)  # type: int\n'
            '    Assert(r7 == T_NONE)\n'
            '    r8 = resolve_combined_type(C_ADD, T_UNREL_TOP - 4, T_INT)  # type: int\n'
            '    Assert(r8 == T_NONE)\n'
            '    return r1'
        ),
        "rationale": "the precondition must admit the issue-shaped input (the remainder connector over mixed numeric operands), the same query with an operand from the OPEN integer family, a bitwise query, a date/time query, an exponentiation query, an unregistered connector and an operand below no recorded type; else PRECOND-TOO-STRONG. The asserts confirm the pinned consequences are reachable. The probe is a separate method at MustTerminate(3) — strictly above the callee's level 2 — because a same-level self-call fails the obligation leak check for a reason about the call site's level, not the precondition.",
    },

    {
        "id": 'weak-mod-gated-prepatch',
        "kind": 'uniqueness',
        "expect": 'reject',
        "module": _impl(
            '    if records_same_type_numeric(connector):\n'
            '        if row(T_INT, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '        if row(T_FLT, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_DEC, T_DEC, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '    # Pre-patch: the mixed-type numeric rows are recorded only for the\n'
            '    # addition/subtraction/multiplication/division connectors — the\n'
            '    # remainder connector is absent from that family.\n'
            '    if records_mixed_numeric(connector) and connector != C_MOD:\n'
            '        if row(T_INT, T_DEC, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '        if row(T_DEC, T_INT, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '        if row(T_INT, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_FLT, T_INT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '    if records_same_type_numeric(connector):\n'
            '        if row(T_FLT, T_NULL, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_NULL, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '    if records_bitwise_integer(connector):\n'
            '        if row(T_INT, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '    if connector == C_ADD:\n'
            '        if row(T_DATE, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DATE, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_TIME, T_DUR, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '        if row(T_DUR, T_TIME, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '    if connector == C_SUB:\n'
            '        if row(T_DATE, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DATE, T_DATE, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_DUR, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_TIME, T_DUR, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '        if row(T_TIME, T_TIME, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '    return T_NONE'
        ),
        "refinement": "this IS the pre-patch registry: the mixed-type numeric rows are recorded only for addition/subtraction/multiplication/division. The F2P test_resolve_output_field_number iterates the remainder connector over (Integer, Decimal) and asserts the combined output field is DecimalField; the real resolver would find no row and return None -> 'Cannot infer type of' FieldError. The faithful real patch FAILS the F2P; it does NOT resolve.",
        "rationale": 'violates the mixed-numeric clauses for connector == C_MOD (and the totality clause): mixed operands under the remainder connector yield the sentinel instead of the wider type.',
    },

    {
        "id": 'weak-exact-match-normalize',
        "kind": 'uniqueness',
        "expect": 'reject',
        "module": _impl(
            '    # Matching by EXACT recorded-type equality after normalizing only the\n'
            '    # finitely many NAMED narrower codes (the auto-increment integer type\n'
            '    # and the date-time type) up to their recorded supertype. Extensionally\n'
            '    # correct on every named code, but WRONG for the rest of the open\n'
            '    # families below the integer and date types: matching is by subtyping,\n'
            '    # which no finite normalization table can reproduce.\n'
            '    a = T_INT if lhs_type == T_AUTO else lhs_type  # type: int\n'
            '    b = T_INT if rhs_type == T_AUTO else rhs_type  # type: int\n'
            '    da = T_DATE if lhs_type == T_DTM else a  # type: int\n'
            '    db = T_DATE if rhs_type == T_DTM else b  # type: int\n'
            '    if records_same_type_numeric(connector):\n'
            '        if a == T_INT and b == T_INT:\n'
            '            return T_INT\n'
            '        if a == T_FLT and b == T_FLT:\n'
            '            return T_FLT\n'
            '        if a == T_DEC and b == T_DEC:\n'
            '            return T_DEC\n'
            '        if a == T_FLT and b == T_NULL:\n'
            '            return T_FLT\n'
            '        if a == T_NULL and b == T_FLT:\n'
            '            return T_FLT\n'
            '    if records_mixed_numeric(connector):\n'
            '        if a == T_INT and b == T_DEC:\n'
            '            return T_DEC\n'
            '        if a == T_DEC and b == T_INT:\n'
            '            return T_DEC\n'
            '        if a == T_INT and b == T_FLT:\n'
            '            return T_FLT\n'
            '        if a == T_FLT and b == T_INT:\n'
            '            return T_FLT\n'
            '    if records_bitwise_integer(connector):\n'
            '        if a == T_INT and b == T_INT:\n'
            '            return T_INT\n'
            '    if connector == C_ADD:\n'
            '        if da == T_DATE and db == T_DUR:\n'
            '            return T_DTM\n'
            '        if da == T_DUR and db == T_DATE:\n'
            '            return T_DTM\n'
            '        if da == T_DUR and db == T_DUR:\n'
            '            return T_DUR\n'
            '        if da == T_TIME and db == T_DUR:\n'
            '            return T_TIME\n'
            '        if da == T_DUR and db == T_TIME:\n'
            '            return T_TIME\n'
            '    if connector == C_SUB:\n'
            '        if da == T_DATE and db == T_DUR:\n'
            '            return T_DTM\n'
            '        if da == T_DATE and db == T_DATE:\n'
            '            return T_DUR\n'
            '        if da == T_DUR and db == T_DUR:\n'
            '            return T_DUR\n'
            '        if da == T_TIME and db == T_DUR:\n'
            '            return T_TIME\n'
            '        if da == T_TIME and db == T_TIME:\n'
            '            return T_DUR\n'
            '    return T_NONE'
        ),
        "refinement": 'this refines the row test as exact recorded-type matching plus a hard-coded list of the narrower types it happens to know about. Its faithful realization replaces the subtype test in the scan with an equality-plus-known-aliases helper, so an operand whose field type merely lies below a recorded one — e.g. a non-negative or wide integer field, the overwhelmingly common case in real models — matches no row and resolves to None -> FieldError, where the real resolver yields the integer type. The faithful real patch breaks combinations over such fields; it does NOT resolve.',
        "rationale": 'violates the same-type integer clause and the totality clause for any member of the open family below the integer type other than the one named auto-increment code: matching is quantified over the whole band by is_int_kind, so a finite normalization table cannot discharge it.',
    },

    {
        "id": 'weak-int-band-truncated',
        "kind": 'uniqueness',
        "expect": 'reject',
        "module": _impl(
            '    # Treat only a BOUNDED prefix of the family below the integer type as\n'
            '    # integer-matching; anything further down the hierarchy matches no\n'
            '    # row. The family is open, so truncating it is wrong.\n'
            '    if lhs_type > T_INT_SUB + 3 or rhs_type > T_INT_SUB + 3:\n'
            '        return T_NONE\n'
            '    if records_same_type_numeric(connector):\n'
            '        if row(T_INT, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '        if row(T_FLT, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_DEC, T_DEC, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '    if records_mixed_numeric(connector):\n'
            '        if row(T_INT, T_DEC, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '        if row(T_DEC, T_INT, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '        if row(T_INT, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_FLT, T_INT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '    if records_same_type_numeric(connector):\n'
            '        if row(T_FLT, T_NULL, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_NULL, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '    if records_bitwise_integer(connector):\n'
            '        if row(T_INT, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '    if connector == C_ADD:\n'
            '        if row(T_DATE, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DATE, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_TIME, T_DUR, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '        if row(T_DUR, T_TIME, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '    if connector == C_SUB:\n'
            '        if row(T_DATE, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DATE, T_DATE, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_DUR, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_TIME, T_DUR, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '        if row(T_TIME, T_TIME, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '    return T_NONE'
        ),
        "refinement": 'this realizes the subtype test as membership in a fixed, finite list of integer field classes rather than as a subclass test, so any integer field type outside that list resolves to None -> FieldError where the real resolver yields the integer type. The faithful real patch breaks combinations over integer fields it does not enumerate; it does NOT resolve.',
        "rationale": 'violates the same-type / mixed integer clauses and the totality clause for members of the open integer family above the truncation point: they must resolve exactly as the integer type does.',
    },

    {
        "id": 'weak-arith-only-connector-guard',
        "kind": 'uniqueness',
        "expect": 'reject',
        "module": _impl(
            '    # Resolve nothing unless the connector is one of the five arithmetic\n'
            '    # connectors: the bitwise, exponentiation and date/time row families\n'
            '    # are dropped.\n'
            '    if not records_mixed_numeric(connector):\n'
            '        return T_NONE\n'
            '    if records_same_type_numeric(connector):\n'
            '        if row(T_INT, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '        if row(T_FLT, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_DEC, T_DEC, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '    if records_mixed_numeric(connector):\n'
            '        if row(T_INT, T_DEC, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '        if row(T_DEC, T_INT, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '        if row(T_INT, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_FLT, T_INT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '    if records_same_type_numeric(connector):\n'
            '        if row(T_FLT, T_NULL, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_NULL, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '    if records_bitwise_integer(connector):\n'
            '        if row(T_INT, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '    if connector == C_ADD:\n'
            '        if row(T_DATE, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DATE, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_TIME, T_DUR, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '        if row(T_DUR, T_TIME, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '    if connector == C_SUB:\n'
            '        if row(T_DATE, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DATE, T_DATE, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_DUR, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_TIME, T_DUR, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '        if row(T_TIME, T_TIME, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '    return T_NONE'
        ),
        "refinement": 'this makes the resolver answer only for the five arithmetic connectors. The real resolver is also driven with the bitwise connectors, exponentiation and the date/time connectors, so a bitwise combination of two integer fields, an exponentiation of two float fields, and a date-plus-duration combination all become None -> FieldError. The faithful real patch breaks those; it does NOT resolve.',
        "rationale": 'violates the bitwise integer clause, the exponentiation same-type clauses, the date/time clauses and the totality clause: those connectors have recorded rows and must resolve.',
    },

    {
        "id": 'weak-mixed-narrower',
        "kind": 'uniqueness',
        "expect": 'reject',
        "module": _impl(
            '    if records_same_type_numeric(connector):\n'
            '        if row(T_INT, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '        if row(T_FLT, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_DEC, T_DEC, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '    # WRONG: mixed integer/decimal resolves to the NARROWER integer type\n'
            '    # instead of the wider decimal — the precise defect the issue names.\n'
            '    if records_mixed_numeric(connector):\n'
            '        if row(T_INT, T_DEC, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '        if row(T_DEC, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '        if row(T_INT, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_FLT, T_INT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '    if records_same_type_numeric(connector):\n'
            '        if row(T_FLT, T_NULL, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_NULL, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '    if records_bitwise_integer(connector):\n'
            '        if row(T_INT, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '    if connector == C_ADD:\n'
            '        if row(T_DATE, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DATE, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_TIME, T_DUR, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '        if row(T_DUR, T_TIME, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '    if connector == C_SUB:\n'
            '        if row(T_DATE, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DATE, T_DATE, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_DUR, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_TIME, T_DUR, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '        if row(T_TIME, T_TIME, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '    return T_NONE'
        ),
        "refinement": 'this records the mixed integer/decimal rows with the WRONG result type (the integer type instead of the decimal type) — the defect the issue describes. test_resolve_output_field_number asserts the combined field is DecimalField; the real resolver would yield IntegerField. The faithful real patch FAILS the F2P; it does NOT resolve.',
        "rationale": 'violates the mixed-numeric decimal clauses: the result is the narrower integer type, not the wider decimal type.',
    },

    {
        "id": 'weak-pow-gets-mixed-rows',
        "kind": 'uniqueness',
        "expect": 'reject',
        "module": _impl(
            '    if records_same_type_numeric(connector):\n'
            '        if row(T_INT, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '        if row(T_FLT, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_DEC, T_DEC, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '    if records_same_type_numeric(connector):\n'
            '        if row(T_INT, T_DEC, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '        if row(T_DEC, T_INT, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '        if row(T_INT, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_FLT, T_INT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '    if records_same_type_numeric(connector):\n'
            '        if row(T_FLT, T_NULL, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_NULL, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '    if records_bitwise_integer(connector):\n'
            '        if row(T_INT, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '    if connector == C_ADD:\n'
            '        if row(T_DATE, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DATE, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_TIME, T_DUR, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '        if row(T_DUR, T_TIME, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '    if connector == C_SUB:\n'
            '        if row(T_DATE, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DATE, T_DATE, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_DUR, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_TIME, T_DUR, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '        if row(T_TIME, T_TIME, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '    return T_NONE'
        ),
        "refinement": 'this records the mixed-type numeric rows for exponentiation as well as for the arithmetic connectors. The real registry records them for the arithmetic connectors only, so exponentiation over mixed numeric operands must stay unresolved; test_resolve_output_field_dates and the with-null/failure assertions observe that unresolved outcome. The faithful real patch resolves a combination the registry does not permit; it does NOT match the real callee.',
        "rationale": 'violates the exponentiation clause: a mixed numeric query under the exponentiation connector must yield the sentinel, not a widened type.',
    },

    {
        "id": 'weak-date-add-sub-symmetric',
        "kind": 'uniqueness',
        "expect": 'reject',
        "module": _impl(
            '    if records_same_type_numeric(connector):\n'
            '        if row(T_INT, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '        if row(T_FLT, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_DEC, T_DEC, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '    if records_mixed_numeric(connector):\n'
            '        if row(T_INT, T_DEC, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '        if row(T_DEC, T_INT, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '        if row(T_INT, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_FLT, T_INT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '    if records_same_type_numeric(connector):\n'
            '        if row(T_FLT, T_NULL, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_NULL, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '    if records_bitwise_integer(connector):\n'
            '        if row(T_INT, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '    if connector == C_ADD:\n'
            '        if row(T_DATE, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DATE, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_TIME, T_DUR, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '        if row(T_DUR, T_TIME, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '    if connector == C_SUB:\n'
            '        if row(T_DATE, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DATE, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_TIME, T_DUR, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '        if row(T_TIME, T_TIME, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '    return T_NONE'
        ),
        "refinement": "this makes subtraction record the same date/duration rows as addition — a duration on the LEFT of a date operand resolves — and drops subtraction's date-minus-date row. The real registry is asymmetric: subtracting two date operands yields a duration, while a duration minus a date is not permitted. test_resolve_output_field_dates asserts both. The faithful real patch contradicts the real callee; it does NOT resolve.",
        "rationale": 'violates the subtraction date-minus-date clause (must be a duration) and the duration-minus-date clause (must be the sentinel).',
    },

    {
        "id": 'weak-null-widened-to-all-numeric',
        "kind": 'uniqueness',
        "expect": 'reject',
        "module": _impl(
            '    if records_same_type_numeric(connector):\n'
            '        if row(T_INT, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '        if row(T_FLT, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_DEC, T_DEC, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '    if records_mixed_numeric(connector):\n'
            '        if row(T_INT, T_DEC, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '        if row(T_DEC, T_INT, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '        if row(T_INT, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_FLT, T_INT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '    if records_same_type_numeric(connector):\n'
            '        # WRONG: the null-literal type is treated as combining with every\n'
            '        # numeric type, not with the float type alone.\n'
            '        if rhs_type == T_NULL and (is_int_kind(lhs_type)\n'
            '                                   or lhs_type == T_DEC\n'
            '                                   or lhs_type == T_FLT):\n'
            '            return lhs_type if lhs_type == T_FLT else T_INT\n'
            '        if lhs_type == T_NULL and (is_int_kind(rhs_type)\n'
            '                                   or rhs_type == T_DEC\n'
            '                                   or rhs_type == T_FLT):\n'
            '            return rhs_type if rhs_type == T_FLT else T_INT\n'
            '    if records_bitwise_integer(connector):\n'
            '        if row(T_INT, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '    if connector == C_ADD:\n'
            '        if row(T_DATE, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DATE, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_TIME, T_DUR, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '        if row(T_DUR, T_TIME, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '    if connector == C_SUB:\n'
            '        if row(T_DATE, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DATE, T_DATE, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_DUR, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_TIME, T_DUR, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '        if row(T_TIME, T_TIME, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '    return T_NONE'
        ),
        "refinement": 'this records a row against the null-literal type for the integer and decimal types as well as the float type. The real registry records the null-literal rows only for the float type, so an integer or decimal operand combined with a null literal must raise FieldError — which is exactly what test_resolve_output_field_with_null asserts. The faithful real patch resolves combinations the registry forbids and turns those expected FieldErrors into silent results; it does NOT resolve.',
        "rationale": 'violates the clause pinning integer/null, decimal/null and null/null to the sentinel.',
    },

    {
        "id": 'weak-result-echoes-operand',
        "kind": 'uniqueness',
        "expect": 'reject',
        "module": _impl(
            "    # Ungrounded echo: return the queried operand's OWN type code when the\n"
            '    # two operands are both integer-family, instead of the recorded\n'
            '    # integer result type. Agrees with the recorded result whenever the\n'
            '    # operand IS the integer type, so it satisfies every clause that only\n'
            '    # mentions the named integer code — but the recorded result type is\n'
            '    # the integer type for EVERY member of the family below it.\n'
            '    if records_same_type_numeric(connector) or records_bitwise_integer(connector):\n'
            '        if is_int_kind(lhs_type) and is_int_kind(rhs_type):\n'
            '            return lhs_type\n'
            '    if records_same_type_numeric(connector):\n'
            '        if row(T_INT, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '        if row(T_FLT, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_DEC, T_DEC, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '    if records_mixed_numeric(connector):\n'
            '        if row(T_INT, T_DEC, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '        if row(T_DEC, T_INT, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '        if row(T_INT, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_FLT, T_INT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '    if records_same_type_numeric(connector):\n'
            '        if row(T_FLT, T_NULL, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_NULL, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '    if records_bitwise_integer(connector):\n'
            '        if row(T_INT, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '    if connector == C_ADD:\n'
            '        if row(T_DATE, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DATE, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_TIME, T_DUR, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '        if row(T_DUR, T_TIME, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '    if connector == C_SUB:\n'
            '        if row(T_DATE, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DATE, T_DATE, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_DUR, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_TIME, T_DUR, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '        if row(T_TIME, T_TIME, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '    return T_NONE'
        ),
        "refinement": "this returns the operand's own field class as the combined type instead of the class the registry records. For two integer fields of a narrower kind the real resolver yields IntegerField, while this yields that narrower class, so the combined expression's output field has the wrong type (and the resolver may return a class the registry never records as a result). The faithful real patch diverges from the real callee on every combination of narrower integer fields; it does NOT resolve.",
        "rationale": 'violates the same-type integer clause (the result must be the recorded integer type, not the queried operand type) and the is_result_type clause.',
    },

    {
        "id": 'weak-unrelated-operand-resolves',
        "kind": 'uniqueness',
        "expect": 'reject',
        "module": _impl(
            '    # WRONG: an operand type that lies below no recorded operand type is\n'
            '    # treated as if it matched the integer rows.\n'
            '    if lhs_type <= T_UNREL_TOP or rhs_type <= T_UNREL_TOP:\n'
            '        if records_same_type_numeric(connector):\n'
            '            return T_INT\n'
            '    if records_same_type_numeric(connector):\n'
            '        if row(T_INT, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '        if row(T_FLT, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_DEC, T_DEC, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '    if records_mixed_numeric(connector):\n'
            '        if row(T_INT, T_DEC, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '        if row(T_DEC, T_INT, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '        if row(T_INT, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_FLT, T_INT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '    if records_same_type_numeric(connector):\n'
            '        if row(T_FLT, T_NULL, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_NULL, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '    if records_bitwise_integer(connector):\n'
            '        if row(T_INT, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '    if connector == C_ADD:\n'
            '        if row(T_DATE, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DATE, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_TIME, T_DUR, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '        if row(T_DUR, T_TIME, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '    if connector == C_SUB:\n'
            '        if row(T_DATE, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DATE, T_DATE, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_DUR, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_TIME, T_DUR, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '        if row(T_TIME, T_TIME, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '    return T_NONE'
        ),
        "refinement": 'this makes an operand whose field type lies below no recorded operand type — a character, boolean or uuid field — match the integer rows. The real resolver finds no row for such an operand and returns None, so the combination raises FieldError; test_mixed_char_date_with_annotate and the failure assertions observe that. The faithful real patch silently resolves combinations the registry forbids; it does NOT resolve.',
        "rationale": 'violates the clause pinning an operand below no recorded operand type to the sentinel.',
    },

    {
        "id": 'weak-divergent-loop',
        "kind": 'uniqueness',
        "expect": 'reject',
        "module": _impl(
            '    # Control-flow / termination probe: diverge before scanning the rows.\n'
            '    # The result value would be correct if it were ever produced.\n'
            '    #\n'
            '    # The spin is an UNBOUNDED counter loop whose exit test is\n'
            '    # statically satisfiable, not a literal `while True:`. Nagini\n'
            "    # types the module with mypy first, and mypy's reachability\n"
            '    # analysis flags every statement after a `while True:` with no\n'
            '    # break as dead code, which makes the FRONT END refuse the file\n'
            '    # ("Translation failed / Type error: dead.code") before Viper is\n'
            '    # ever started. That refusal is not a rejection: nothing about\n'
            '    # this spec would have been judged. `spin` starts at 1 and only\n'
            '    # grows, so `spin != 0` never becomes false at run time (Nagini\n'
            '    # ints are unbounded) and the loop truly diverges, while the\n'
            '    # invariant `spin >= 0` is CONSISTENT with the exit test, so the\n'
            '    # post-loop state is feasible and the row cascade below still has\n'
            '    # to discharge every value clause on its own. The loop carries no\n'
            '    # Invariant(MustTerminate(...)) and no decreasing measure, so it\n'
            "    # cannot take the caller's termination obligation.\n"
            '    spin = 1\n'
            '    while spin != 0:\n'
            '        Invariant(spin >= 0)\n'
            '        spin = spin + 1\n'
            '    if records_same_type_numeric(connector):\n'
            '        if row(T_INT, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '        if row(T_FLT, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_DEC, T_DEC, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '    if records_mixed_numeric(connector):\n'
            '        if row(T_INT, T_DEC, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '        if row(T_DEC, T_INT, lhs_type, rhs_type):\n'
            '            return T_DEC\n'
            '        if row(T_INT, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_FLT, T_INT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '    if records_same_type_numeric(connector):\n'
            '        if row(T_FLT, T_NULL, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '        if row(T_NULL, T_FLT, lhs_type, rhs_type):\n'
            '            return T_FLT\n'
            '    if records_bitwise_integer(connector):\n'
            '        if row(T_INT, T_INT, lhs_type, rhs_type):\n'
            '            return T_INT\n'
            '    if connector == C_ADD:\n'
            '        if row(T_DATE, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DATE, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DUR, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_TIME, T_DUR, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '        if row(T_DUR, T_TIME, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '    if connector == C_SUB:\n'
            '        if row(T_DATE, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DTM\n'
            '        if row(T_DATE, T_DATE, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_DUR, T_DUR, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '        if row(T_TIME, T_DUR, lhs_type, rhs_type):\n'
            '            return T_TIME\n'
            '        if row(T_TIME, T_TIME, lhs_type, rhs_type):\n'
            '            return T_DUR\n'
            '    return T_NONE'
        ),
        "refinement": 'a resolver that does not terminate never yields an output field at all: every combined expression using it hangs. The faithful real patch makes the scan diverge; it does NOT resolve.',
        "rationale": 'must reject on the method-level MustTerminate(2) obligation: '
                     'partial correctness alone must not satisfy this spec. '
                     'MEASURED (17.9s, a real Viper verdict — Nagini exits 1 after '
                     '"Verification failed", not a front-end refusal): the SINGLE '
                     'error is "Obligation leak check failed. Loop might not take '
                     'all unsatisfied obligations from the context." reported at '
                     'the spin loop, i.e. exactly the obligation this case claims, '
                     'and NO value clause is reported — the row cascade after the '
                     'loop proves the whole postcondition, so termination is the '
                     'only thing wrong with this rival. ATTRIBUTED by ablation: '
                     'with Requires(MustTerminate(2)) deleted from the spec (in a '
                     'throwaway scratch file, never landed) this identical rival '
                     'VERIFIES in 24.3s, so the rejection comes from that clause '
                     'and from nothing else. NON-VACUOUS: on that same ablated '
                     'scratch file an Assert(False) placed immediately after the '
                     'loop FAILS ("Assertion False might not hold"), so the '
                     'post-loop program point the value clauses are discharged at '
                     'is reachable and the postcondition proof there is not '
                     'vacuous.',
    },

]


# ---------------------------------------------------------------------------
# AXIOM lane — A-reference soundness + caller-domain containment.
# ---------------------------------------------------------------------------
# model.py consumes NO @ContractOnly axiom. The deep model rests on two UNCHANGED
# primitives, validated == the real callee out-of-band by the bundle's G-AX
# oracle (axiom_check.py):
#   (1) is_subtype  <->  Python issubclass, over EVERY field class the registry
#       mentions as a recorded operand type AND every field class that lies
#       below one of them (the whole open family below the integer type and the
#       date-time type below the date type) plus representatives that lie below
#       none of them;
#   (2) the deep row cascade  <->  Django's real _connector_combinators scanned
#       by _resolve_combined_type, over EVERY connector the registry is keyed by
#       (the five arithmetic connectors, exponentiation, the five bitwise
#       connectors) plus unregistered connector codes, crossed with that whole
#       field-class domain, POST-PATCH.
# We re-run that exact host-validated oracle IN-CONTAINER (apply_gold=True so the
# post-patch source is present) as a single soundness + containment probe so the
# axiom lane is grounded in the REAL callee, not a regex over source. The runner
# mounts ONLY this probe script at /work, so axiom_check.py is read on the HOST at
# manifest-load time and embedded verbatim. The probe imports stdlib + the repo's
# own django only; it does not read any file (no utf-8 codec concern), and it
# EXECUTES the real issubclass and real _resolve_combined_type (never scrapes
# inspect.getsource).
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-issubclass-and-registry-cascade",
        "axiom": "is_subtype (issubclass); resolve cascade (_connector_combinators)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        # Embedded bundle G-AX oracle. Drives:
        #   - real issubclass over every (queried class, recorded class) pair vs
        #     is_subtype, including every real subclass of the integer field type
        #     and the date-time/date pair, so the OPEN band predicates are
        #     validated against the real hierarchy rather than assumed;
        #   - real _resolve_combined_type over every registered connector plus
        #     unregistered connector codes, crossed with that whole field-class
        #     domain, vs the deep cascade; and
        #   - the boundary cases: the remainder connector over mixed numeric
        #     operands resolves to the wider type, including when the integer
        #     operand is a narrower integer field class.
        # Exits 0 iff every observation matches the deep model (=> A-references
        # sound) AND every real result lies in the modeled type set (containment:
        # the real callee never returns an out-of-model field type anywhere in the
        # caller-reachable domain).
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "axiom-soundness + containment in one real-callee probe: the "
                     "deep cascade and is_subtype must equal the real "
                     "_resolve_combined_type / issubclass on every input the model "
                     "can reach. The precondition admits every connector code and "
                     "every operand field-type code, so the caller-reachable set is "
                     "the whole registry domain; the probe enumerates every "
                     "registered connector, unregistered connector codes, every "
                     "recorded operand class, every real class below one of them "
                     "(the whole integer family, the date-time type) and classes "
                     "below none of them. A real result outside the model type set "
                     "or disagreeing with the cascade => AXIOM-UNSOUND / "
                     "AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
