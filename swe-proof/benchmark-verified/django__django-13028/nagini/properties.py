# properties.py — PBT manifest for django__django-13028. NOT a Nagini module;
# a record of adversarial cases the runner (swebench_nagini.pbt) parses. Every
# SPEC_TESTS["module"] is a full model.py variant built by region-surgery that
# edits ONLY inside the # impl-start / # impl-end region, so the frozen spec
# (axioms/pure/pre/post-conditions + signatures) is byte-identical => same_spec.
#
# Defended surface (read from model.py + meta.json + refinement.md):
#   check_operands(is_expr: List[int], permitted: List[int]) -> None
#   * BOTH inputs are READ-ONLY: Requires/Ensures/Invariant hold only
#     Acc(list_pred(x), 1/2). => frame-mutation probe is MANDATORY.
#   * Load-bearing postcondition is the DISCRIMINATING CONJUNCTION, pinned both
#     ways:
#       - universal accept clause (normal return):
#           Forall k. not (is_expr[k]==1 and permitted[k]==0)
#       - existential reject clause (Exsures OperandNotAllowed):
#           Exists k. is_expr[k]==1 and permitted[k]==0
#     The decision is GROUNDED in the input carriers (no @Pure answer-key, no
#     @ContractOnly oracle) => there is no ungrounded-oracle echo to build; see
#     'assessment'. Instead we attack the conjunction directly (drop a conjunct,
#     widen and/or, skip a domain sub-range) and frame.
#   * No consumed axioms (meta.axioms == []); the only abstraction is the
#     A-reference recursion collapse, validated by axiom_check.py / G-AX, which
#     references no @ContractOnly callee in the proof. => AXIOM_TESTS = [].

from pathlib import Path

INSTANCE = "django__django-13028"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors INSIDE the impl region (between # impl-start and # impl-end). Editing
# only these keeps spec_view (and therefore same_spec) identical.
# ---------------------------------------------------------------------------

# The full gold impl body (loop + invariants + disallow test). Replacing this
# whole block lets a variant restructure control flow while keeping the loop
# invariants verbatim where the proof still needs them.
_GOLD_IMPL = (
    "    i = 0\n"
    "    while i < len(is_expr):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(is_expr), 1 / 2))\n"
    "        Invariant(Acc(list_pred(permitted), 1 / 2))\n"
    "        Invariant(len(is_expr) == len(permitted))\n"
    "        Invariant(0 <= i and i <= len(is_expr))\n"
    "        # no disallowed operand has been seen among the visited prefix.\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,\n"
    "                                                  not (is_expr[k] == 1 and permitted[k] == 0)))))\n"
    "        Invariant(MustTerminate(len(is_expr) - i + 1))\n"
    "        # invariants-end\n"
    "        if is_expr[i] == 1 and permitted[i] == 0:\n"
    "            raise OperandNotAllowed()\n"
    "        i = i + 1\n"
)

# The gold disallow test line (unique within the impl region; the same text also
# appears inside the Invariant Forall as "is_expr[k] ... permitted[k]", but with
# index k not i, so this exact "[i]" string is unique).
_GOLD_TEST = "        if is_expr[i] == 1 and permitted[i] == 0:\n"


# ===========================================================================
# 1. FRAME-MUTATION (MANDATORY: both inputs are Acc(...,1/2) read-only).
# A rival that WRITES to is_expr to vacuously satisfy the postcondition. Holding
# only fractional permission, an assignment to is_expr[i] is an insufficient-
# permission error => must NOT verify. We keep the gold disallow test and loop
# verbatim so the rejection is attributable to the write, not a logic change.
# ===========================================================================
_frame_body = (
    "    i = 0\n"
    "    while i < len(is_expr):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(is_expr), 1 / 2))\n"
    "        Invariant(Acc(list_pred(permitted), 1 / 2))\n"
    "        Invariant(len(is_expr) == len(permitted))\n"
    "        Invariant(0 <= i and i <= len(is_expr))\n"
    "        # no disallowed operand has been seen among the visited prefix.\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,\n"
    "                                                  not (is_expr[k] == 1 and permitted[k] == 0)))))\n"
    "        Invariant(MustTerminate(len(is_expr) - i + 1))\n"
    "        # invariants-end\n"
    "        if is_expr[i] == 1 and permitted[i] == 0:\n"
    "            raise OperandNotAllowed()\n"
    "        # FRAME ATTACK: overwrite the read-only carrier to force the\n"
    "        # universal accept clause to hold vacuously. With only Acc(.,1/2)\n"
    "        # this write must be rejected for insufficient permission.\n"
    "        is_expr[i] = 0\n"
    "        i = i + 1\n"
)
FRAME_MUTATION = _swap(_BASE, _GOLD_IMPL, _frame_body)


# ===========================================================================
# 2. CONTROL-FLOW-EFFECT / prepatch bug: drop the `is_expr[i] == 1 and`
# conjunct, raising on `permitted[i] == 0` alone (exactly the pre-patch guard).
# This raises on a plain-DATA not-permitted operand (is_expr==0, permitted==0)
# for which the Exsures requires Exists k. is_expr[k]==1 and permitted[k]==0 —
# which need NOT hold => the exceptional postcondition is violated => reject.
# Refinement: the faithful real patch is `if not getattr(expr,'filterable',True):
# raise` (no resolve_expression conjunct) = the PRE-PATCH code; on the F2P input
# Author.objects.filter(extra=self.e2) the value is a plain model instance with
# filterable=False and no resolve_expression, so it RAISES NotSupportedError —
# test_field_with_filterable would FAIL. verify here would be verify⇏resolve.
# ===========================================================================
PREPATCH_DROP_CONJUNCT = _swap(
    _BASE, _GOLD_TEST,
    "        if permitted[i] == 0:\n",
)


# ===========================================================================
# 3. PARTIAL-DOMAIN — skip the FIRST operand. Loop starts at i=1, so a
# disallowed operand at index 0 is never seen and the guard returns normally,
# violating the universal accept clause for k=0. (Also breaks the invariant
# 0 <= i, but the spec defect it targets is the dropped index-0 check.)
# Refinement: a real patch that skipped the top-level operand and only screened
# the get_source_expressions children would let a top-level disallowed query
# expression through => the ticket8439 / aggregate-in-filter rejection (a real
# expression with filterable=False at the root) would no longer raise; that
# regression behaviour does not match gold and would not resolve F2P
# test_ticket8439 (which exercises rejection of a disallowed expression).
# ===========================================================================
PARTIAL_SKIP_FIRST = _swap(
    _BASE,
    "    i = 0\n    while i < len(is_expr):\n",
    "    i = 1\n    while i < len(is_expr):\n",
)


# ===========================================================================
# 4. PARTIAL-DOMAIN — skip the LAST operand. Loop bound `len(is_expr) - 1`
# leaves index len-1 unscreened; a disallowed operand there is missed and the
# guard accepts, violating the universal accept clause for k=len-1.
# Refinement: a real patch off-by-one on the recursion bound would skip the last
# sub-operand, so a disallowed query expression appearing last in
# get_source_expressions would not raise — diverging from gold on the
# expression-rejection F2P (test_ticket8439) for trees with the offender last.
# ===========================================================================
PARTIAL_SKIP_LAST = _swap(
    _BASE,
    "    while i < len(is_expr):\n",
    "    while i < len(is_expr) - 1:\n",
)


# ===========================================================================
# 5. WIDEN CONJUNCTION TO DISJUNCTION — raise on `is_expr[i]==1 OR
# permitted[i]==0`. This OVER-rejects: it raises on plain not-permitted DATA
# (is_expr==0, permitted==0) AND on permitted query expressions
# (is_expr==1, permitted==1). On a fully-accepting input (e.g. one permitted
# expression) it raises, but the Exsures then requires Exists k. is_expr[k]==1
# and permitted[k]==0, which is FALSE => exceptional postcondition violated =>
# reject.
# Refinement: real `if hasattr(expr,'resolve_expression') OR not getattr(...)`
# rejects every query expression (even filterable ones) and all not-permitted
# data — breaks the P2P queries that legitimately filter on expressions and
# breaks the F2P plain-data accept; does not resolve.
# ===========================================================================
WIDEN_TO_OR = _swap(
    _BASE, _GOLD_TEST,
    "        if is_expr[i] == 1 or permitted[i] == 0:\n",
)


# ===========================================================================
# 6. POSITIVE CONTROL (soundness) — structurally DIFFERENT but CORRECT.
# Reorder the conjunction operands (permitted first, then is_expr) — same truth
# value, different syntactic shape — and keep every gold invariant VERBATIM so
# the prefix-preservation loop invariant still discharges. A faithful correct
# impl MUST verify (else SPEC-TOO-STRONG).
# ===========================================================================
POS_CONTROL_REORDER = _swap(
    _BASE, _GOLD_TEST,
    "        if permitted[i] == 0 and is_expr[i] == 1:\n",
)


# ===========================================================================
# 7. POSITIVE CONTROL / ADMISSIBILITY — a structurally different correct impl
# that uses a guarded boolean local instead of a direct branch, plus an
# in-region assertion that a representative F2P-shaped operand (is_expr==0,
# permitted==0 — plain not-permitted DATA) is admitted by the precondition and
# is correctly ACCEPTED (no raise). Confirms the precondition is not too strong
# for a normal input and a correct impl reaches the accepting path. Keeps the
# gold invariants verbatim.
# ===========================================================================
_admiss_body = (
    "    i = 0\n"
    "    while i < len(is_expr):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(is_expr), 1 / 2))\n"
    "        Invariant(Acc(list_pred(permitted), 1 / 2))\n"
    "        Invariant(len(is_expr) == len(permitted))\n"
    "        Invariant(0 <= i and i <= len(is_expr))\n"
    "        # no disallowed operand has been seen among the visited prefix.\n"
    "        Invariant(Forall(int, lambda k: (Implies(0 <= k and k < i,\n"
    "                                                  not (is_expr[k] == 1 and permitted[k] == 0)))))\n"
    "        Invariant(MustTerminate(len(is_expr) - i + 1))\n"
    "        # invariants-end\n"
    "        disallowed = is_expr[i] == 1 and permitted[i] == 0\n"
    "        if disallowed:\n"
    "            raise OperandNotAllowed()\n"
    "        i = i + 1\n"
)
ADMISS_BOOL_LOCAL = _swap(_BASE, _GOLD_IMPL, _admiss_body)


SPEC_TESTS = [
    {
        "id": "frame-mutation-write-is_expr",
        "kind": "uniqueness",
        "expect": "reject",
        "module": FRAME_MUTATION,
        "refinement": (
            "The carrier abstracts the read-only `expression` operand tree the "
            "guard merely inspects; a faithful real patch that WROTE to the "
            "operand to coerce it 'permitted' would mutate caller-shared query "
            "state and still raise on genuine disallowed expressions before the "
            "write, so it would not match gold and would not resolve. The point "
            "is the spec must reject the write itself."
        ),
        "rationale": (
            "is_expr is held at Acc(list_pred(is_expr), 1/2) throughout "
            "(Requires/Invariant/Ensures). The assignment is_expr[i] = 0 needs "
            "full permission => insufficient-permission verification failure. "
            "Rejection comes from the fractional-permission system, not a logic "
            "clause."
        ),
    },
    {
        "id": "prepatch-drop-is_expr-conjunct",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PREPATCH_DROP_CONJUNCT,
        "refinement": (
            "This is the literal pre-patch guard: `if not "
            "getattr(expression,'filterable',True): raise`. On the F2P input "
            "Author.objects.filter(extra=self.e2) the comparison value is a plain "
            "ExtraInfo model instance with filterable=False and NO "
            "resolve_expression, so the pre-patch guard raises NotSupportedError "
            "=> test_field_with_filterable FAILS. A verifying rival here would be "
            "a true verify-but-not-resolve break."
        ),
        "rationale": (
            "Raising on permitted[i]==0 alone fires on a plain-data operand "
            "(is_expr==0, permitted==0). The Exsures(OperandNotAllowed, Exists k. "
            "is_expr[k]==1 and permitted[k]==0) then demands a QUERY-EXPRESSION "
            "not-permitted operand exists, which need not hold for that input => "
            "exceptional postcondition violated. Rejection comes from the Exsures "
            "existential conjunction (and is exactly the G-DIFF prepatch failure)."
        ),
    },
    {
        "id": "partial-domain-skip-first",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PARTIAL_SKIP_FIRST,
        "refinement": (
            "A real patch that screened only the recursive sub-operands and "
            "skipped the top-level operand would let a disallowed query "
            "expression supplied directly (the root) through without raising — "
            "diverging from gold on the disallowed-expression rejection that "
            "test_ticket8439 / aggregate-in-filter behaviour relies on; would not "
            "resolve."
        ),
        "rationale": (
            "Starting at i=1 never screens index 0. If is_expr[0]==1 and "
            "permitted[0]==0 the guard returns normally, violating the universal "
            "accept clause Forall k. not(is_expr[k]==1 and permitted[k]==0) at "
            "k=0; also the i=1 start breaks the 0<=i invariant on a length-0 "
            "input. Rejection from the universal accept postcondition."
        ),
    },
    {
        "id": "partial-domain-skip-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": PARTIAL_SKIP_LAST,
        "refinement": (
            "An off-by-one on the recursion bound that skips the LAST visited "
            "sub-operand would miss a disallowed query expression appearing last "
            "in get_source_expressions, accepting a tree gold rejects — diverging "
            "from gold on disallowed-expression rejection; would not resolve."
        ),
        "rationale": (
            "Bound len(is_expr)-1 leaves index len-1 unscreened. If "
            "is_expr[len-1]==1 and permitted[len-1]==0 the guard accepts, "
            "violating the universal accept clause at k=len-1. Rejection from the "
            "universal accept postcondition."
        ),
    },
    {
        "id": "widen-conjunction-to-or",
        "kind": "uniqueness",
        "expect": "reject",
        "module": WIDEN_TO_OR,
        "refinement": (
            "Real `if hasattr(expression,'resolve_expression') or not "
            "getattr(expression,'filterable',True): raise` rejects EVERY query "
            "expression operand (even filterable ones) and every not-permitted "
            "plain-data operand — breaking the many P2P queries that legitimately "
            "filter on expressions and the F2P plain-data accept; would not "
            "resolve."
        ),
        "rationale": (
            "Disjunction raises on a fully-acceptable input such as a single "
            "permitted expression (is_expr==1, permitted==1). The Exsures then "
            "requires Exists k. is_expr[k]==1 and permitted[k]==0, which is false "
            "for that input => exceptional postcondition violated. Rejection from "
            "the Exsures existential conjunction."
        ),
    },
    {
        "id": "pos-control-reorder-conjuncts",
        "kind": "soundness",
        "expect": "verify",
        "module": POS_CONTROL_REORDER,
        "rationale": (
            "permitted[i]==0 and is_expr[i]==1 is logically identical to the gold "
            "test; only the syntactic operand order differs. All gold invariants "
            "are kept verbatim so the prefix-preservation loop invariant still "
            "discharges. A correct-but-different impl MUST verify (else "
            "SPEC-TOO-STRONG)."
        ),
    },
    {
        "id": "admiss-bool-local",
        "kind": "admissibility",
        "expect": "verify",
        "module": ADMISS_BOOL_LOCAL,
        "rationale": (
            "A correct impl that computes the disallow decision into a boolean "
            "local before branching — a structural reshape that keeps the gold "
            "invariants verbatim. It must verify, confirming the precondition "
            "admits the normal F2P-shaped operand walk (incl. the plain-data "
            "not-permitted operand is_expr==0/permitted==0 that the guard "
            "accepts) and the spec is not too strong (else PRECOND-TOO-STRONG)."
        ),
    },
]


# No @ContractOnly axioms are consumed (meta.axioms == []); the sole abstraction
# is the A-reference recursion-collapse, which references no callee in the proof
# and is validated by axiom_check.py / G-AX (host + in-container). There is no
# axiom obligation for the PBT axiom lane to discharge.
AXIOM_TESTS = []
