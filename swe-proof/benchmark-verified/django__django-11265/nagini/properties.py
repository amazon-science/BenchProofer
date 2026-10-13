# properties.py — PBT manifest for django__django-11265. NOT a Nagini module; a
# record of adversarial cases the runner (swebench_nagini.pbt) parses.
#
# Instance shape: TWO modeled functions in one model.py, both PURE value-returning
# list builders, each with a READ-ONLY input (Acc(...,1/2)):
#
#   propagate_relation_registry(outer_relations[Acc 1/2], referenced_alias)
#       -> List[int] with ToSeq(Result()) == ToSeq(outer_relations)
#       (site 1: the exclusion subquery inherits the outer query's filtered-
#        relation registry, so the referenced alias resolves — no FieldError)
#
#   subquery_retained_filters(join_type, is_filtered_relation, leading_filter,
#                             other_filters[Acc 1/2]) -> List[int]
#       (site 2: a left-outer OR filtered-relation leading join keeps its filter
#        condition; an inner non-filtered leading join may be collapsed)
#
# Load-bearing post clauses:
#   site 1: ToSeq(Result()) == ToSeq(outer_relations)   (exact value+order pin)
#           + referenced_alias in ToSeq(Result()) + Forall membership corollary
#   site 2: four Implies clauses pinning ToSeq(Result()) EXACTLY on each branch
#           (trim-allowed => other_filters ; else => [leading_filter]+other_filters
#            ; is_filtered_relation => keep ; join_type==LOUTER => keep)
#
# The site-2 oracle `may_trim_leading_join` is a @Pure helper but it is GROUNDED:
# it is fully unfolded as `join_type != LOUTER() and not is_filtered_relation`, a
# pure function of the two scalar args. There is no opaque answer-key to echo, so
# the ungrounded-oracle-echo class does NOT apply (see assessment); instead site 2
# is attacked via partial-domain rivals that get the trim decision wrong on a
# specific (join_type, is_filtered_relation) sub-domain (incl. the real bug).
from pathlib import Path

INSTANCE = "django__django-11265"
FLOAT_ENCODING = None  # meta.json float_encoding is null and unused

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- exact impl-region bodies (verbatim from model.py, between the markers) ----
# Every variant is produced by _swap on one of these; the markers themselves and
# everything outside the impl regions (signatures, pre/post-conditions, @Pure
# helpers) are NEVER touched => same_spec is guaranteed.

_IMPL1 = (
    "    result = []  # type: List[int]\n"
    "    i = 0\n"
    "    while i < len(outer_relations):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(outer_relations), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(outer_relations))\n"
    "        Invariant(referenced_alias in ToSeq(outer_relations))\n"
    "        Invariant(ToSeq(result) == ToSeq(outer_relations).take(i))\n"
    "        Invariant(MustTerminate(len(outer_relations) - i + 1))\n"
    "        # invariants-end\n"
    "        result = result + [outer_relations[i]]\n"
    "        i = i + 1\n"
    "    Assert(ToSeq(outer_relations).take(len(outer_relations)) == ToSeq(outer_relations))\n"
    "    Assert(ToSeq(result) == ToSeq(outer_relations))\n"
    "    Assert(referenced_alias in ToSeq(outer_relations))\n"
    "    return result\n"
)

_IMPL2 = (
    "    result = []  # type: List[int]\n"
    "    if not may_trim_leading_join(join_type, is_filtered_relation):\n"
    "        result = result + [leading_filter]\n"
    "    prefix = ToSeq(result)\n"
    "    i = 0\n"
    "    while i < len(other_filters):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(other_filters), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(other_filters))\n"
    "        Invariant(ToSeq(result) == prefix + ToSeq(other_filters).take(i))\n"
    "        Invariant(MustTerminate(len(other_filters) - i + 1))\n"
    "        # invariants-end\n"
    "        result = result + [other_filters[i]]\n"
    "        i = i + 1\n"
    "    Assert(ToSeq(other_filters).take(len(other_filters)) == ToSeq(other_filters))\n"
    "    return result\n"
)

# sanity: the two bodies appear verbatim & uniquely in the frozen model.
assert _BASE.count(_IMPL1) == 1, "IMPL1 anchor drift"
assert _BASE.count(_IMPL2) == 1, "IMPL2 anchor drift"


# ============================ SITE 1 variants ============================

# --- S1 frame-mutation (MANDATORY: outer_relations is Acc(...,1/2) read-only) ---
# Rival APPENDS to the read-only input to satisfy the post 'cheaply' (after the
# append, outer_relations == result trivially in the attacker's intent). Writing
# to a half-permission list is forbidden, so this must REJECT for insufficient
# permission, NOT for a value mismatch — that is the whole point of the 1/2 perm.
_S1_FRAME = (
    "    outer_relations.append(referenced_alias)\n"
    "    result = []  # type: List[int]\n"
    "    i = 0\n"
    "    while i < len(outer_relations):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(outer_relations)))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(outer_relations))\n"
    "        Invariant(ToSeq(result) == ToSeq(outer_relations).take(i))\n"
    "        Invariant(MustTerminate(len(outer_relations) - i + 1))\n"
    "        # invariants-end\n"
    "        result = result + [outer_relations[i]]\n"
    "        i = i + 1\n"
    "    return result\n"
)

# --- S1 partial-domain: drop the LAST declared alias ---
# Copies the registry but stops one short (i < len-1). If the referenced alias is
# the last key in the dict, it is missing from the inner registry. Faithful real
# patch: a registry copy that omits the final key -> names_to_path raises
# FieldError for that alias -> F2P test_with_exclude still fails. Rejected by
# ToSeq(Result()) == ToSeq(outer_relations) (and by referenced_alias membership /
# the Forall corollary when the referenced alias is the dropped one).
_S1_DROP_LAST = (
    "    result = []  # type: List[int]\n"
    "    i = 0\n"
    "    while i + 1 < len(outer_relations):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(outer_relations), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(outer_relations))\n"
    "        Invariant(ToSeq(result) == ToSeq(outer_relations).take(i))\n"
    "        Invariant(MustTerminate(len(outer_relations) - i + 1))\n"
    "        # invariants-end\n"
    "        result = result + [outer_relations[i]]\n"
    "        i = i + 1\n"
    "    return result\n"
)

# --- S1 partial-domain: drop the FIRST declared alias ---
# Starts the copy at index 1, so the first-declared alias is lost. Faithful patch:
# `query._filtered_relations = dict(list(self._filtered_relations.items())[1:])`
# -> the first alias is unresolvable -> FieldError when the exclude references it.
# Rejected by the same exact-equality clause.
_S1_DROP_FIRST = (
    "    result = []  # type: List[int]\n"
    "    i = 1\n"
    "    while i < len(outer_relations):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(outer_relations), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(1 <= i and i <= len(outer_relations))\n"
    "        Invariant(ToSeq(result) == ToSeq(outer_relations).drop(1).take(i - 1))\n"
    # This rival counts from 1, not 0, but the REMAINING-iteration bound is the
    # same expression: the loop still runs while i < len(outer_relations) and i
    # still increases by one each pass, so len(outer_relations) - i + 1 strictly
    # decreases and stays positive. Added because the strengthened precondition
    # now obliges every spliced loop to prove termination too; the case still
    # REJECTS, and on its own stated ground (the exact-equality postcondition),
    # so the rejection remains attributable to the dropped head alias.
    "        Invariant(MustTerminate(len(outer_relations) - i + 1))\n"
    "        # invariants-end\n"
    "        result = result + [outer_relations[i]]\n"
    "        i = i + 1\n"
    "    return result\n"
)

# --- S1 empty-registry (the literal pre-patch / prepatch_1 behaviour) ---
# Returns the empty list (the freshly-created inner Query keeps its {} registry).
# This is the EXACT pre-patch bug: the referenced alias is absent so the exclude
# raises FieldError -> F2P fails. Must reject (referenced_alias in ToSeq(Result())
# and the exact-equality clause). A cheap supporting near-miss for the headline
# site-1 weakness; carries a real refinement (== prepatch_1, fails F2P).
_S1_EMPTY = (
    "    empty = []  # type: List[int]\n"
    "    return empty\n"
)

# --- S1 POSITIVE CONTROL: structurally-different but CORRECT (forward index by a
#     decrement counter, building the same content) ---
# Different executable shape (a separate `n` bound + an explicit appended local)
# but the SAME content equality and the SAME gold framing asserts kept verbatim,
# so the gold proof obligations still discharge. Must verify (else SPEC-TOO-STRONG).
_S1_POS = (
    "    result = []  # type: List[int]\n"
    "    n = len(outer_relations)\n"
    "    i = 0\n"
    "    while i < n:\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(outer_relations), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(n == len(outer_relations))\n"
    "        Invariant(0 <= i and i <= len(outer_relations))\n"
    "        Invariant(referenced_alias in ToSeq(outer_relations))\n"
    "        Invariant(ToSeq(result) == ToSeq(outer_relations).take(i))\n"
    "        Invariant(MustTerminate(len(outer_relations) - i + 1))\n"
    "        # invariants-end\n"
    "        nxt = outer_relations[i]\n"
    "        result = result + [nxt]\n"
    "        i = i + 1\n"
    "    Assert(ToSeq(outer_relations).take(len(outer_relations)) == ToSeq(outer_relations))\n"
    "    Assert(ToSeq(result) == ToSeq(outer_relations))\n"
    "    Assert(referenced_alias in ToSeq(outer_relations))\n"
    "    return result\n"
)

# --- S1 ADMISSIBILITY: a self-call confirming the Requires admits an F2P-shaped
#     input (a one-element registry whose sole alias is the referenced one) ---
# The helper caller establishes Acc + membership for a concrete in-domain input
# and invokes the modeled function, then keeps the gold body. If the precondition
# rejected a normal input the call site would fail (PRECOND-TOO-STRONG).
#
# TERMINATION: the precondition now carries MustTerminate(len(outer_relations)+2),
# so this self-call must prove the callee's level is STRICTLY below the caller's.
# The level is argument-dependent for exactly this reason: the probe calls itself
# on a ONE-element `sample`, so the callee's level is len(sample)+2 == 3 while the
# caller's is len(outer_relations)+2, and 3 < len(outer_relations)+2 holds as soon
# as len(outer_relations) >= 2. The `if` supplies that fact; it does NOT narrow the
# specification (the shared Requires region is untouched) and it does not weaken
# what the case claims — the probe still invokes the modeled function on a genuine
# in-domain input and still asserts the full result equality. A constant level
# could not work here at ANY value: an unguarded self-call needs level > itself.
# The guard is FEASIBLE, not vacuously true: replacing the body with Assert(False)
# under the same guard is REJECTED ("Assertion False might not hold"), so Nagini
# really does reach the call site and really does discharge the measure there.
_S1_ADMISS = (
    "    if len(outer_relations) >= 2:\n"
    "        sample = [referenced_alias]  # type: List[int]\n"
    "        Assert(referenced_alias in ToSeq(sample))\n"
    "        echoed = propagate_relation_registry(sample, referenced_alias)\n"
    "        Assert(ToSeq(echoed) == ToSeq(sample))\n"
    "    result = []  # type: List[int]\n"
    "    i = 0\n"
    "    while i < len(outer_relations):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(outer_relations), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(outer_relations))\n"
    "        Invariant(referenced_alias in ToSeq(outer_relations))\n"
    "        Invariant(ToSeq(result) == ToSeq(outer_relations).take(i))\n"
    "        Invariant(MustTerminate(len(outer_relations) - i + 1))\n"
    "        # invariants-end\n"
    "        result = result + [outer_relations[i]]\n"
    "        i = i + 1\n"
    "    Assert(ToSeq(result) == ToSeq(outer_relations))\n"
    "    Assert(referenced_alias in ToSeq(outer_relations))\n"
    "    return result\n"
)


# ============================ SITE 2 variants ============================

# --- S2 frame-mutation (MANDATORY: other_filters is Acc(...,1/2) read-only) ---
# Rival WRITES to the read-only downstream-conditions list. Forbidden at half
# permission -> must REJECT for insufficient permission, not a value mismatch.
_S2_FRAME = (
    "    other_filters.append(leading_filter)\n"
    "    result = []  # type: List[int]\n"
    "    if not may_trim_leading_join(join_type, is_filtered_relation):\n"
    "        result = result + [leading_filter]\n"
    "    prefix = ToSeq(result)\n"
    "    i = 0\n"
    "    while i < len(other_filters):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(other_filters)))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(other_filters))\n"
    "        Invariant(ToSeq(result) == prefix + ToSeq(other_filters).take(i))\n"
    "        Invariant(MustTerminate(len(other_filters) - i + 1))\n"
    "        # invariants-end\n"
    "        result = result + [other_filters[i]]\n"
    "        i = i + 1\n"
    "    return result\n"
)

# --- S2 the REAL bug (== prepatch_2): trim guard ignores filtered_relation ---
# Keeps leading_filter ONLY when join_type==LOUTER (the pre-patch guard `!= LOUTER`
# decides trimming, ignoring `not first_join.filtered_relation`). On an INNER
# filtered-relation leading join (is_filtered_relation=True, join_type==INNER) it
# DROPS leading_filter. Faithful real patch = the PRE-PATCH code -> the ON-clause
# filter of the filtered relation is silently dropped -> wrong rows -> F2P
# test_with_exclude fails. Must reject via
# Implies(is_filtered_relation, ToSeq(Result()) == PSeq(leading_filter)+...).
_S2_REALBUG = (
    "    result = []  # type: List[int]\n"
    "    if join_type == LOUTER():\n"
    "        result = result + [leading_filter]\n"
    "    prefix = ToSeq(result)\n"
    "    i = 0\n"
    "    while i < len(other_filters):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(other_filters), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(other_filters))\n"
    "        Invariant(ToSeq(result) == prefix + ToSeq(other_filters).take(i))\n"
    "        Invariant(MustTerminate(len(other_filters) - i + 1))\n"
    "        # invariants-end\n"
    "        result = result + [other_filters[i]]\n"
    "        i = i + 1\n"
    "    return result\n"
)

# --- S2 partial-domain: never trim (always keep leading_filter) ---
# Over-retains: keeps the leading condition even on a plain inner non-filtered
# join that the gold patch collapses. Faithful real patch: drop the
# `first_join.join_type != LOUTER` half of the guard so the leading join is never
# trimmed -> a join that should be collapsed stays, diverging from gold (and from
# the pre-existing PASS_TO_PASS trim behaviour, e.g. test_with_join). Must reject
# via Implies(may_trim_leading_join(...), ToSeq(Result()) == ToSeq(other_filters)).
_S2_NEVERTRIM = (
    "    result = []  # type: List[int]\n"
    "    result = result + [leading_filter]\n"
    "    prefix = ToSeq(result)\n"
    "    i = 0\n"
    "    while i < len(other_filters):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(other_filters), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(other_filters))\n"
    "        Invariant(ToSeq(result) == prefix + ToSeq(other_filters).take(i))\n"
    "        Invariant(MustTerminate(len(other_filters) - i + 1))\n"
    "        # invariants-end\n"
    "        result = result + [other_filters[i]]\n"
    "        i = i + 1\n"
    "    return result\n"
)

# --- S2 partial-domain: inverted filter handling (trim a filtered relation, keep
#     a plain inner join) ---
# Uses the WRONG conjunct polarity: trims iff `join_type != LOUTER and
# is_filtered_relation` (keep iff NOT filtered). Correct on the LOUTER sub-domain
# but inverted on the filtered/non-filtered split. Faithful real patch: the guard
# `... and first_join.filtered_relation` (dropped the `not`) -> collapses exactly
# the filtered-relation join that must be kept while keeping plain inner joins the
# gold patch collapses -> F2P fails (filter dropped) AND P2P trim cases diverge.
# Rejected by the is_filtered_relation clause (filtered+inner now trims, dropping
# leading_filter when it must be kept).
_S2_INVERTED = (
    "    result = []  # type: List[int]\n"
    "    if not (join_type != LOUTER() and is_filtered_relation):\n"
    "        result = result + [leading_filter]\n"
    "    prefix = ToSeq(result)\n"
    "    i = 0\n"
    "    while i < len(other_filters):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(other_filters), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(other_filters))\n"
    "        Invariant(ToSeq(result) == prefix + ToSeq(other_filters).take(i))\n"
    "        Invariant(MustTerminate(len(other_filters) - i + 1))\n"
    "        # invariants-end\n"
    "        result = result + [other_filters[i]]\n"
    "        i = i + 1\n"
    "    return result\n"
)

# --- S2 partial-domain: drop the last downstream condition ---
# Correct on the leading-join decision but loses the final downstream filter
# (i+1 < len). Faithful real patch: a trim path that forgets one of the
# downstream where-conditions -> a subquery missing a filter -> wrong rows.
# Rejected because the result is no longer prefix + ToSeq(other_filters) exactly.
_S2_DROP_DOWNSTREAM = (
    "    result = []  # type: List[int]\n"
    "    if not may_trim_leading_join(join_type, is_filtered_relation):\n"
    "        result = result + [leading_filter]\n"
    "    prefix = ToSeq(result)\n"
    "    i = 0\n"
    "    while i + 1 < len(other_filters):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(other_filters), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(other_filters))\n"
    "        Invariant(ToSeq(result) == prefix + ToSeq(other_filters).take(i))\n"
    "        Invariant(MustTerminate(len(other_filters) - i + 1))\n"
    "        # invariants-end\n"
    "        result = result + [other_filters[i]]\n"
    "        i = i + 1\n"
    "    return result\n"
)

# --- S2 POSITIVE CONTROL: structurally-different but CORRECT (branch reorder via
#     an explicit `keep` boolean local; same content, gold framing kept) ---
# Reorders the decision into an explicit boolean and an if/else over may_trim,
# but produces the identical result content. Keeps the gold prefix-framing
# invariant and the closing take-len assert. Must verify (else SPEC-TOO-STRONG).
_S2_POS = (
    "    keep = not may_trim_leading_join(join_type, is_filtered_relation)\n"
    "    result = []  # type: List[int]\n"
    "    if keep:\n"
    "        result = result + [leading_filter]\n"
    "    else:\n"
    "        Assert(not keep)  # leading condition collapsed away\n"
    "    prefix = ToSeq(result)\n"
    "    i = 0\n"
    "    while i < len(other_filters):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(other_filters), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(other_filters))\n"
    "        Invariant(ToSeq(result) == prefix + ToSeq(other_filters).take(i))\n"
    "        Invariant(MustTerminate(len(other_filters) - i + 1))\n"
    "        # invariants-end\n"
    "        result = result + [other_filters[i]]\n"
    "        i = i + 1\n"
    "    Assert(ToSeq(other_filters).take(len(other_filters)) == ToSeq(other_filters))\n"
    "    return result\n"
)

# --- S2 ADMISSIBILITY: a self-call on an F2P-shaped input (an INNER filtered
#     relation leading join with one downstream condition) ---
# Establishes Acc on a concrete in-domain other_filters and invokes the modeled
# function with is_filtered_relation=True, join_type=INNER(); asserts the kept
# result. If Requires rejected a normal input the call would fail -> PRECOND-TOO-
# STRONG. Keeps the gold body afterwards.
# TERMINATION: same shape as the site-1 probe. The precondition now carries
# MustTerminate(len(other_filters)+6), so this self-call must prove a strictly
# lower callee level. It calls itself on an EMPTY `sample`, so the callee's level
# is 0+6 == 6 and the caller's is len(other_filters)+6; 6 < len(other_filters)+6
# holds as soon as len(other_filters) >= 1, which the guard supplies. The Requires
# region is untouched and the asserted result equality is unchanged. The guard is
# FEASIBLE: the same body with Assert(False) under it is REJECTED, so the call site
# is genuinely reachable and the measure is genuinely discharged there.
_S2_ADMISS = (
    "    if len(other_filters) >= 1:\n"
    "        sample = []  # type: List[int]\n"
    "        echoed = subquery_retained_filters(INNER(), True, leading_filter, sample)\n"
    "        Assert(ToSeq(echoed) == PSeq(leading_filter) + ToSeq(sample))\n"
    "    result = []  # type: List[int]\n"
    "    if not may_trim_leading_join(join_type, is_filtered_relation):\n"
    "        result = result + [leading_filter]\n"
    "    prefix = ToSeq(result)\n"
    "    i = 0\n"
    "    while i < len(other_filters):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(other_filters), 1 / 2))\n"
    "        Invariant(Acc(list_pred(result)))\n"
    "        Invariant(0 <= i and i <= len(other_filters))\n"
    "        Invariant(ToSeq(result) == prefix + ToSeq(other_filters).take(i))\n"
    "        Invariant(MustTerminate(len(other_filters) - i + 1))\n"
    "        # invariants-end\n"
    "        result = result + [other_filters[i]]\n"
    "        i = i + 1\n"
    "    Assert(ToSeq(other_filters).take(len(other_filters)) == ToSeq(other_filters))\n"
    "    return result\n"
)


SPEC_TESTS = [
    # ---------------- SITE 1: registry propagation ----------------
    {
        "id": "s1-frame-mutation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL1, _S1_FRAME),
        "refinement": "Appends to outer_relations (a half-permission read-only "
                      "input). Its faithful real patch would MUTATE "
                      "self._filtered_relations (the shared OUTER query's dict) "
                      "instead of copying it into the inner query — corrupting "
                      "the outer query's registry across the split_exclude "
                      "rewrite. That is not the gold fix (which assigns the dict "
                      "into the fresh inner Query) and would not faithfully "
                      "resolve F2P.",
        "rationale": "Must reject for INSUFFICIENT PERMISSION: outer_relations is "
                     "Acc(list_pred(outer_relations),1/2); .append needs full "
                     "permission. Rejection is attributable to the write, not a "
                     "value mismatch (the gold post clauses are kept verbatim).",
    },
    {
        "id": "s1-drop-last-alias",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL1, _S1_DROP_LAST),
        "refinement": "Copies all but the last declared alias. Faithful real "
                      "patch: query._filtered_relations = a copy of the outer "
                      "dict missing its final key. If the exclude references that "
                      "dropped alias, names_to_path raises FieldError -> "
                      "test_with_exclude still fails (the exact pre-patch "
                      "symptom).",
        "rationale": "Rejected by Ensures(ToSeq(Result()) == ToSeq("
                     "outer_relations)) (exact value+order pin) and, when the "
                     "dropped alias is the referenced one, by referenced_alias "
                     "in ToSeq(Result()) and the Forall membership corollary.",
    },
    {
        "id": "s1-drop-first-alias",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL1, _S1_DROP_FIRST),
        "refinement": "Copies the registry starting at index 1, dropping the "
                      "first-declared alias. Faithful real patch: assigning a "
                      "registry that omits the first key -> that alias is "
                      "unresolvable -> FieldError when the exclude references it. "
                      "Not the gold whole-dict propagation.",
        "rationale": "Rejected by the exact-equality clause ToSeq(Result()) == "
                     "ToSeq(outer_relations); a registry missing the head can "
                     "never equal the full outer sequence.",
    },
    {
        "id": "s1-empty-registry",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL1, _S1_EMPTY),
        "refinement": "Returns the empty registry — EXACTLY the pre-patch / "
                      "prepatch_1 behaviour (the fresh inner Query keeps its "
                      "{} _filtered_relations; the added gold line is absent). "
                      "The referenced alias is absent -> FieldError -> F2P "
                      "test_with_exclude fails. Cheap supporting near-miss with a "
                      "real refinement.",
        "rationale": "Rejected by referenced_alias in ToSeq(Result()) (empty "
                     "result fails membership) and by ToSeq(Result()) == ToSeq("
                     "outer_relations) whenever the outer registry is non-empty "
                     "(it is: it contains referenced_alias by the precondition).",
    },
    {
        "id": "s1-pos-control",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL1, _S1_POS),
        "rationale": "A structurally-different but CORRECT impl (separate length "
                     "bound `n`, an explicit appended local `nxt`) producing the "
                     "identical content. Keeps the gold prefix-framing invariant "
                     "and the three closing asserts so the proof still "
                     "discharges. Must verify; a failure here would be "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "s1-admissibility",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL1, _S1_ADMISS),
        "rationale": "Self-call on an F2P-shaped in-domain input (a one-element "
                     "registry [referenced_alias] satisfying both Requires "
                     "clauses) verifies, confirming the precondition admits a "
                     "normal input. A failure would be PRECOND-TOO-STRONG.",
    },

    # ---------------- SITE 2: leading-join filter retention ----------------
    {
        "id": "s2-frame-mutation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL2, _S2_FRAME),
        "refinement": "Appends to other_filters (a half-permission read-only "
                      "input). Its faithful real patch would mutate the shared "
                      "downstream where-condition list of the query, not build a "
                      "fresh retained-conditions set — corrupting state the gold "
                      "trim_start never writes. Not the gold fix.",
        "rationale": "Must reject for INSUFFICIENT PERMISSION: other_filters is "
                     "Acc(list_pred(other_filters),1/2); .append needs full "
                     "permission. Attributable to the write — gold post clauses "
                     "kept verbatim.",
    },
    {
        "id": "s2-real-bug",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL2, _S2_REALBUG),
        "refinement": "The literal PRE-PATCH guard (== prepatch_2): trim iff NOT "
                      "left-outer, ignoring filtered_relation. On an INNER "
                      "filtered-relation leading join it DROPS leading_filter — "
                      "the ON-clause filter of the filtered relation is silently "
                      "lost -> wrong rows -> F2P test_with_exclude fails. This is "
                      "the headline site-2 weakness; its faithful patch is the "
                      "exact code the gold patch replaces.",
        "rationale": "Rejected by Ensures(Implies(is_filtered_relation, "
                     "ToSeq(Result()) == PSeq(leading_filter) + ToSeq("
                     "other_filters))): with is_filtered_relation=True and "
                     "join_type==INNER, may_trim is True so this rival omits "
                     "leading_filter, contradicting the clause.",
    },
    {
        "id": "s2-never-trim",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL2, _S2_NEVERTRIM),
        "refinement": "Always keeps leading_filter (never trims). Faithful real "
                      "patch: drop the `first_join.join_type != LOUTER` half of "
                      "the guard so a plain inner non-filtered leading join is "
                      "never collapsed — diverging from gold (which DOES collapse "
                      "it) and from pre-existing PASS_TO_PASS trim behaviour "
                      "(e.g. test_with_join). Over-retention is still wrong.",
        "rationale": "Rejected by Ensures(Implies(may_trim_leading_join(...), "
                     "ToSeq(Result()) == ToSeq(other_filters))): on an inner "
                     "non-filtered join may_trim is True yet this rival prepends "
                     "leading_filter.",
    },
    {
        "id": "s2-inverted-filter",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL2, _S2_INVERTED),
        "refinement": "Inverts the filtered-relation polarity: trims iff inner "
                      "AND filtered (keeps iff NOT filtered). Faithful real "
                      "patch: the guard with `... and first_join.filtered_"
                      "relation` (the `not` dropped) -> collapses exactly the "
                      "filtered-relation join that must be kept while keeping "
                      "plain inner joins gold collapses -> F2P fails (filter "
                      "dropped) and P2P trim cases diverge.",
        "rationale": "Rejected by Ensures(Implies(is_filtered_relation, "
                     "ToSeq(Result()) == PSeq(leading_filter) + ToSeq("
                     "other_filters))): with is_filtered_relation=True and "
                     "join_type==INNER this rival trims, omitting leading_filter.",
    },
    {
        "id": "s2-drop-downstream",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL2, _S2_DROP_DOWNSTREAM),
        "refinement": "Correct leading-join decision but loses the final "
                      "downstream condition (i+1 < len). Faithful real patch: a "
                      "trim path that forgets one downstream where-condition -> a "
                      "subquery missing a filter -> wrong rows on any F2P/P2P "
                      "case with >=1 downstream condition.",
        "rationale": "Rejected on both branches: the result is no longer "
                     "prefix + ToSeq(other_filters) exactly, contradicting both "
                     "the may_trim and the not-may_trim Implies clauses.",
    },
    {
        "id": "s2-pos-control",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL2, _S2_POS),
        "rationale": "A structurally-different but CORRECT impl: the trim "
                     "decision is hoisted into an explicit `keep` boolean with an "
                     "if/else, producing identical content. Keeps the gold "
                     "prefix-framing invariant and the closing take-len assert. "
                     "Must verify; a failure would be SPEC-TOO-STRONG.",
    },
    {
        "id": "s2-admissibility",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL2, _S2_ADMISS),
        "rationale": "Self-call on an F2P-shaped in-domain input (INNER filtered "
                     "relation leading join, empty downstream list) verifies, "
                     "confirming the precondition (Acc on other_filters only) "
                     "admits a normal input. A failure would be PRECOND-TOO-"
                     "STRONG.",
    },
]


# No @ContractOnly axioms and no A-reference deep models in this bundle (meta.json
# axioms=[], deep_model_references=[]; G-AX vacuous). Both behaviours are modeled
# deeply as Django-internal data-flow/control-flow over abstract tokens — there is
# no external real callee to fuzz for soundness or to check for caller-domain
# containment. The axiom lane is therefore empty.
AXIOM_TESTS = []  # type: list
