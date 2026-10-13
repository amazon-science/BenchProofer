# properties.py — PBT manifest for django__django-11555. NOT a Nagini module; a
# record of adversarial cases the runner (swebench_nagini.pbt) parses.
#
# Instance shape: ONE modeled function, expand_default_ordering(kinds, ids, state),
# the related-model default-ordering expansion block of
# SQLCompiler.find_ordering_name. opts.ordering is abstracted to two index-aligned
# READ-ONLY List[int]:
#   kinds[k] in {0,1}  (1 = already-formed OrderBy expression, 0 = textual name)
#   ids[k]             (a stable identity tag for the item / produced expression)
# both at Acc(list_pred(.),1/2) => READ-ONLY (frame-mutation MANDATORY).
# A third carrier, `state`, is the SHARED resolution state the name-resolution
# machinery threads through its recursion (the already_seen / join bookkeeping).
# It is held as the ABSTRACT PREDICATE `machinery_state(state)` — a bodyless
# resource, NOT a boolean fact — because the machinery advances it and because a
# resolution state must be impossible to bring into existence (see U9 below).
# Output: List[int] of target identity tags.
#
# TWO load-bearing post clauses. The output clause pins the produced targets:
#   Ensures(ToSeq(Result()) == expanded(ToSeq(kinds), ToSeq(ids)))
# where the FROZEN @Pure helpers pin, per item:
#   contribution(1, id) == PSeq(id)            # OrderBy item: pass through VERBATIM
#   contribution(0, id) == resolve_name_seq(id) # textual name: name-resolution machinery
#   expanded(...) = front-to-back concat of each item's contribution.
# The invocation clause pins WHICH items the machinery is applied to, and how often:
#   Ensures(invocations(state)
#           == Old(invocations(state)) + name_items(ToSeq(kinds), ToSeq(ids)))
#   name_items(...) = the MULTISET of name-item identities: every kind-0 item
#                     exactly once, and NO kind-1 item.
# `invocations(state)` is the multiset of items the machinery has been applied to
# against that state; reading it REQUIRES the state resource, and the only thing
# that changes it is `resolve_name`, whose postcondition adds exactly the one item
# it was applied to.
# The second clause exists because the real machinery is PARTIAL (handed an
# already-formed OrderBy it subscripts it and raises TypeError) and STATE-CHANGING
# (each invocation mutates already_seen / accumulates joins). Constraining only the
# output left the callee's DOMAIN and MULTIPLICITY free, which admitted rivals that
# return the gold sequence while invoking the machinery out of domain (the reported
# crash) or twice per name (a P2P regression) — see U6-U9. A MULTISET rather than a
# sequence, so once-per-name is observable without pinning the iteration ORDER,
# which the real function does not guarantee (a correct impl may walk either way).
# WHY THE STATE IS A PREDICATE AND NOT A BOOLEAN. An earlier form of this spec
# guarded the callee with a @Pure @ContractOnly Ensures(True) boolean
# `is_machinery_state(state)`. An uninterpreted BOOLEAN cannot be refuted, so a
# rival could build its own carrier, pass the guard, and buy an invocation that the
# shared account never saw (U9) — the returned targets stayed gold-identical while
# the machinery was applied to the OrderBy item, reproducing the reported crash. An
# ABSTRACT PREDICATE is a resource rather than a fact: it has no body, so Fold is
# rejected outright (abstract.predicate.fold) and it cannot be assumed into
# existence, and `resolve_name` consumes and returns it. NOTE, because it decides how
# U10 is written: that Fold refusal is a FRONT-END fact -- nagini exits 1 with no
# Viper verdict -- so it is evidence about Nagini and not about this spec, and a case
# resting on it would prove nothing here. U10 therefore takes the resource BY FIAT in
# the one form that translates and reaches Viper (a loop Invariant naming it) and is
# refuted on the real obligation. Because the resource can be neither manufactured
# nor assumed, an impl holds exactly the one state it was given, every invocation it
# can reach lands in that state's account, and the invocation clause becomes
# inescapable rather than merely accounted-for.
#
# The oracle is GROUNDED in the args (kind,id): contribution/expanded/name_items are
# fully defined pure functions of the inputs, not an opaque answer-key. The ONLY
# opaque pieces are resolve_name_seq (Ensures(True)) for the UNCHANGED name
# machinery's content and the machinery_state resource / its invocations multiset —
# and precisely BECAUSE resolve_name_seq is opaque, an impl that routes a k==1 item
# through it CANNOT prove resolve_name_seq(d) == PSeq(d) (the axiom guarantees no
# such equality). The headline uniqueness attacks are partial-domain on the kind
# discriminant (the real bug: route the OrderBy item through the name machinery),
# the callee-domain / multiplicity family (U6-U9), plus the two mandatory
# frame-mutation probes on the read-only carriers.
from pathlib import Path

INSTANCE = "django__django-11555"
FLOAT_ENCODING = None  # meta.json float_encoding is null and unused

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---- exact impl-region body (verbatim from model.py, BETWEEN the markers) ----
# Every variant is produced by _swap on this single anchor. The markers
# (# impl-start / # impl-end) and everything outside the impl region (signature,
# pre/post-conditions, the @Pure helpers contribution/expanded, the axioms) are
# NEVER touched => same_spec is guaranteed for every spec case.
_IMPL = (
    '        k = kinds[i - 1]\n'
    '        d = ids[i - 1]\n'
    '        Assert(ToSeq(kinds).drop(i - 1)[0] == k)\n'
    '        Assert(ToSeq(ids).drop(i - 1)[0] == d)\n'
    '        Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))\n'
    '        Assert(ToSeq(ids).drop(i - 1).drop(1) == ToSeq(ids).drop(i))\n'
    '        if k == 1:\n'
    '            # An already-formed ordering expression: pass it through verbatim\n'
    '            # as a single target carrying its own identity. The name-resolution\n'
    '            # machinery is not invoked for it.\n'
    '            piece = [d]  # type: List[int]\n'
    '        else:\n'
    '            # A textual name: expand it through the name-resolution machinery,\n'
    '            # advancing the shared resolution state exactly once.\n'
    '            piece = resolve_name(state, d)\n'
    '        Assert(ToSeq(piece) == contribution(k, d))\n'
    '        result = piece + result\n'
    '        i = i - 1\n'
)

# The whole loop body+tail, used by variants that also reshape the loop scaffold.
_LOOP = (
    '    inv0 = invocations(state)  # type: PMultiset[int]\n'
    '    result = []  # type: List[int]\n'
    '    i = len(kinds)\n'
    '    while i > 0:\n'
    '        # invariants-start\n'
    '        Invariant(Acc(list_pred(kinds), 1 / 2))\n'
    '        Invariant(Acc(list_pred(ids), 1 / 2))\n'
    '        Invariant(machinery_state(state))\n'
    '        Invariant(len(kinds) == len(ids))\n'
    '        Invariant(0 <= i and i <= len(kinds))\n'
    '        Invariant(Acc(list_pred(result)))\n'
    '        Invariant(ToSeq(result) == expanded(ToSeq(kinds).drop(i), ToSeq(ids).drop(i)))\n'
    '        Invariant(invocations(state)\n'
    '                  == inv0 + name_items(ToSeq(kinds).drop(i), ToSeq(ids).drop(i)))\n'
    '        Invariant(MustTerminate(i + 1))\n'
    '        # invariants-end\n'
    '        k = kinds[i - 1]\n'
    '        d = ids[i - 1]\n'
    '        Assert(ToSeq(kinds).drop(i - 1)[0] == k)\n'
    '        Assert(ToSeq(ids).drop(i - 1)[0] == d)\n'
    '        Assert(ToSeq(kinds).drop(i - 1).drop(1) == ToSeq(kinds).drop(i))\n'
    '        Assert(ToSeq(ids).drop(i - 1).drop(1) == ToSeq(ids).drop(i))\n'
    '        if k == 1:\n'
    '            # An already-formed ordering expression: pass it through verbatim\n'
    '            # as a single target carrying its own identity. The name-resolution\n'
    '            # machinery is not invoked for it.\n'
    '            piece = [d]  # type: List[int]\n'
    '        else:\n'
    '            # A textual name: expand it through the name-resolution machinery,\n'
    '            # advancing the shared resolution state exactly once.\n'
    '            piece = resolve_name(state, d)\n'
    '        Assert(ToSeq(piece) == contribution(k, d))\n'
    '        result = piece + result\n'
    '        i = i - 1\n'
    '    return result\n'
)

assert _BASE.count(_IMPL) == 1, "IMPL anchor drift"
assert _BASE.count(_LOOP) == 1, "LOOP anchor drift"


# ============================ FRAME-MUTATION (MANDATORY) ============================
# Both kinds and ids are Acc(list_pred(.),1/2) read-only inputs. A rival that WRITES
# to one of them must REJECT for INSUFFICIENT PERMISSION (.append needs full perm),
# NOT for a value mismatch — the gold post clauses are kept verbatim so the rejection
# is attributable to the write. A byte-fuzzer never thinks to mutate the input.

# --- F1: append to the read-only `ids` carrier ---
_F_IDS = (
    "    ids.append(0)\n"
    + _LOOP
)

# --- F2: append to the read-only `kinds` carrier ---
_F_KINDS = (
    "    kinds.append(1)\n"
    + _LOOP
)


# ============================ UNIQUENESS / PARTIAL-DOMAIN ============================

# --- U1: THE REAL BUG (== model_prepatch.py): route EVERY item through the name
#         machinery, with no separate handling for an already-formed OrderBy item. ---
# This is the literal pre-patch loop. On a k==1 item it produces resolve_name(state, d)
# (== resolve_name_seq(d)) where the spec requires contribution(1,d) == PSeq(d), and
# the axiom resolve_name_seq is OPAQUE (Ensures(True)) so resolve_name_seq(d)==PSeq(d)
# is NOT provable => rejected by the postcondition on the k==1 sub-domain.
_U_REALBUG = _swap(
    _IMPL,
    "        if k == 1:\n"
    "            # An already-formed ordering expression: pass it through verbatim\n"
    "            # as a single target carrying its own identity. The name-resolution\n"
    "            # machinery is not invoked for it.\n"
    "            piece = [d]  # type: List[int]\n"
    "        else:\n"
    "            # A textual name: expand it through the name-resolution machinery,\n"
    "            # advancing the shared resolution state exactly once.\n"
    "            piece = resolve_name(state, d)\n",
    "        # Pre-patch: every item handed to the name-resolution machinery,\n"
    "        # with NO separate pass-through for an already-formed expression.\n"
    "        piece = resolve_name(state, d)  # type: List[int]\n",
)

# --- U2: INVERTED kind discriminant: pass through textual names, route OrderBy
#         items through the name machinery (the discriminant is back-to-front). ---
# Correct nowhere the kinds differ: on k==1 produces resolve_name_seq(d) (need
# PSeq(d)); on k==0 produces PSeq(d) (need resolve_name_seq(d)). Faithful real patch:
# `if not isinstance(item, OrderBy): results.append((item, False)); continue` else
# recurse -> textual names appended raw (never resolved to columns) AND the OrderBy
# fed to get_order_dir -> the exact pre-patch crash. Rejected by the postcondition.
_U_INVERTED = _swap(
    _IMPL,
    "        if k == 1:\n"
    "            # An already-formed ordering expression: pass it through verbatim\n"
    "            # as a single target carrying its own identity. The name-resolution\n"
    "            # machinery is not invoked for it.\n"
    "            piece = [d]  # type: List[int]\n"
    "        else:\n"
    "            # A textual name: expand it through the name-resolution machinery,\n"
    "            # advancing the shared resolution state exactly once.\n"
    "            piece = resolve_name(state, d)\n",
    "        if k == 1:\n"
    "            # WRONG: hand the already-formed expression to the name machinery.\n"
    "            piece = resolve_name(state, d)  # type: List[int]\n"
    "        else:\n"
    "            # WRONG: pass a textual name straight through unresolved.\n"
    "            piece = [d]\n",
)

# --- U3: ALWAYS pass through (treat every item as already-formed). ---
# On a textual-name item (k==0) produces PSeq(d) where the spec requires
# resolve_name_seq(d). Faithful real patch: drop the isinstance guard's recursion
# fallthrough and append every item as (item, False) -> textual field-names are
# never expanded into concrete columns -> wrong/empty ordering -> P2P default-
# ordering tests fail. Rejected by the postcondition on the k==0 sub-domain.
_U_ALWAYS_PASS = _swap(
    _IMPL,
    "        if k == 1:\n"
    "            # An already-formed ordering expression: pass it through verbatim\n"
    "            # as a single target carrying its own identity. The name-resolution\n"
    "            # machinery is not invoked for it.\n"
    "            piece = [d]  # type: List[int]\n"
    "        else:\n"
    "            # A textual name: expand it through the name-resolution machinery,\n"
    "            # advancing the shared resolution state exactly once.\n"
    "            piece = resolve_name(state, d)\n",
    "        # WRONG: treat EVERY item as already-formed; never resolve names.\n"
    "        piece = [d]  # type: List[int]\n",
)

# --- U4: WRONG pass-through identity: contribute a DIFFERENT single target for a
#         k==1 item (d + 1 instead of d). ---
# The control flow / kinds are right but the OrderBy item's identity is corrupted:
# produces PSeq(d+1) where the spec requires PSeq(d). Faithful real patch: append a
# freshly-built / different OrderBy instead of `item` itself (e.g. append the wrong
# variable) -> the wrong expression flows to the output, identity NOT preserved ->
# the F2P (which orders by the very ptr expression) sorts wrong. Rejected by the
# postcondition's per-item content equality on the k==1 sub-domain.
_U_WRONG_ID = _swap(
    _IMPL,
    "            piece = [d]  # type: List[int]\n",
    "            piece = [d + 1]  # type: List[int]\n",
)

# --- U5: DROP the pass-through (contribute nothing for a k==1 item). ---
# On a k==1 item produces the empty sequence where the spec requires PSeq(d).
# Faithful real patch: `if isinstance(item, OrderBy): continue` (the OrderBy guard
# is present so no crash, but the expression is NOT appended) -> the ordering
# expression is silently dropped from the output -> wrong ordering -> F2P fails.
# Rejected by the postcondition (empty != PSeq(d)).
_U_DROP_PASS = _swap(
    _IMPL,
    "            piece = [d]  # type: List[int]\n",
    "            piece = []  # type: List[int]\n",
)

# --- U6: OUT-OF-DOMAIN INVOCATION on the already-formed expression. ---
# The RETURNED SEQUENCE is gold-identical (the pass-through is correct and the
# probe's value is discarded), but the name-resolution machinery is invoked on the
# one item for which it is UNDEFINED. Faithful real patch: call
# self.find_ordering_name(item, ...) on the OrderBy item before/besides the
# pass-through and throw the value away -> get_order_dir subscripts the OrderBy ->
# TypeError: 'OrderBy' object is not subscriptable, i.e. the EXACT reported crash
# that the instance exists to fix. The F2P
# test_order_by_ptr_field_with_default_ordering_by_expression fails. This is the
# family the recorded G-EQ audit found VERIFYING against the pre-repair spec: the
# spec then constrained only the returned sequence and said nothing about which
# items the machinery is applied to.
_U_PROBE_ORDERBY = _swap(
    _IMPL,
    "            piece = [d]  # type: List[int]\n",
    "            # WRONG: invoke the name machinery on the already-formed\n"
    "            # expression (out of its domain) and discard the value.\n"
    "            junk = resolve_name(state, d)  # type: List[int]\n"
    "            piece = [d]  # type: List[int]\n",
)

# --- U7: UNCONDITIONAL out-of-domain invocation before the kind test. ---
# Same wrong route as U6 reached differently: the machinery is invoked for EVERY
# item, including the already-formed expression, and its value is used only for
# name items. Returned sequence again gold-identical. Faithful real patch: hoist
# the recursive call above the isinstance guard -> the OrderBy item is still fed to
# get_order_dir -> the same pre-patch TypeError -> F2P fails.
_U_PROBE_ALL = _swap(
    _IMPL,
    "        if k == 1:\n",
    "        # WRONG: invoke the name machinery on every item, including an\n"
    "        # already-formed expression, before discriminating on the kind.\n"
    "        probe = resolve_name(state, d)  # type: List[int]\n"
    "        if k == 1:\n",
)

# --- U8: MULTIPLICITY violation: the machinery is invoked TWICE for one name. ---
# Returned sequence gold-identical (the first result is discarded). Faithful real
# patch: recurse twice for a textual name and keep only the second list. The
# machinery is STATE-CHANGING -- each invocation mutates the shared already_seen /
# join bookkeeping -- so the duplicate recursion perturbs that state and regresses
# a PASS_TO_PASS test (test_related_ordering_duplicate_table_reference, the #24654
# regression), even though the targets come out equal. A distinct failure mode from
# U6/U7 and equally invisible to a spec that constrains only the output.
_U_DOUBLE_RESOLVE = _swap(
    _IMPL,
    "            piece = resolve_name(state, d)\n",
    "            # WRONG: invoke the name machinery twice for one name item,\n"
    "            # discarding the first result.\n"
    "            probe = resolve_name(state, d)  # type: List[int]\n"
    "            piece = resolve_name(state, d)\n",
)

# --- U9: FORGED resolution state: obtain the invocation on a state of the impl's
#         own making rather than the shared one it was given. ---
# This is the dodge a naive invocation-counting clause admits, and it is the
# witness that broke the previous form of this spec: invoke the machinery against a
# locally built carrier so the shared state records nothing, then pass the
# expression through. The returned sequence is gold-identical and the shared
# state's recorded invocations look right. Faithful real patch: run the recursion
# against a throwaway already_seen/join carrier -- but there IS no second carrier in
# the repository; the recursion threads the compiler's own query state, so a
# "private" invocation is still the real call on the real OrderBy item ->
# get_order_dir subscripts it -> the pre-patch TypeError, the EXACT reported crash
# (measured: F2P 0/1, P2P 26/26). Rejected because `machinery_state` is an ABSTRACT
# PREDICATE (a resource with no body), not a boolean fact: `resolve_name` needs that
# resource for its argument and the impl holds it only for the state it was given,
# so the call has INSUFFICIENT PERMISSION to access machinery_state(forged). This
# is the case an uninterpreted BOOLEAN guard could not reject -- an unrefutable
# `Ensures(True)` predicate is satisfied by any carrier the impl invents.
_U_FORGED_STATE = _swap(
    _IMPL,
    "            piece = [d]  # type: List[int]\n",
    "            # WRONG: invoke the machinery on a fabricated resolution state\n"
    "            # so the shared one records nothing.\n"
    "            forged = []  # type: List[int]\n"
    "            junk = resolve_name(forged, d)  # type: List[int]\n"
    "            piece = [d]  # type: List[int]\n",
)

# --- U10: FORGED state, taken BY FIAT: help ourselves to the resolution-state
#         RESOURCE for a carrier of our own making, then spend it. ---
# U9's route with the one extra step a rival reaches for once the state is a resource
# rather than a boolean: do not merely call the machinery on a private carrier -- first
# ACQUIRE machinery_state(forged) for it, then buy the same free out-of-domain
# invocation so the shared account records nothing. Returned sequence gold-identical.
# Same faithful real patch as U9 and the same reported crash (measured: F2P 0/1).
#
# WHY A LOOP INVARIANT AND NOT `Fold`. The direct manufacture, Fold(machinery_state(
# forged)), is NOT TRANSLATABLE: Nagini's front end rejects Fold / Unfold / Unfolding
# of an ABSTRACT (@ContractOnly) predicate before Viper ever runs. Measured on this
# bundle: `Invalid program: abstract.predicate.fold (model.py@216.12)`, nagini exit 1,
# NO Viper verdict, 19.3s. A front-end refusal is evidence about NAGINI, not about
# THIS SPEC -- the file never reaches the verifier, so it cannot show that any clause
# turns the rival down, and on a backend where a rejection's whole argument is "the
# verifier did not verify it" such a case is hollow. (`Assume(machinery_state(forged))`
# is not a third route either: rejected as invalid.contract.position, and a banned
# token for this backend besides -- a trusted assumption proves anything.) There are
# exactly two translatable ways to hold an abstract predicate instance: a callee's
# postcondition, or the enclosing method's precondition. So the fiat is expressed in
# the one form that DOES translate and DOES reach Viper: a loop INVARIANT, the single
# place a rival may NAME a predicate instance it has no producer for. Viper then makes
# it PAY, on loop entry. Measured on this case's exact bytes, 28.6s, ONE error:
#   Loop invariant might not hold on entry. There might be insufficient permission to
#   access machinery_state(forged).
# Carried as its own case because U9 makes no attempt to acquire the resource and is
# refuted at the CALL SITE, whereas this one attempts the acquisition and is refuted AT
# THE ACQUISITION: machinery_state has exactly ONE producer (resolve_name, which hands
# it back only for the carrier it was given) and the precondition grants it only for
# the shared `state`, so a second one cannot be had -- which is what makes the
# invocation clause inescapable rather than merely accounted-for.
_U_FIAT_STATE = _swap(
    _swap(
        _swap(
            _LOOP,
            "    inv0 = invocations(state)  # type: PMultiset[int]\n",
            "    inv0 = invocations(state)  # type: PMultiset[int]\n"
            "    # WRONG: a resolution state of the impl's own making, to hold the\n"
            "    # invocation the shared account must never see.\n"
            "    forged = []  # type: List[int]\n",
        ),
        "        # invariants-start\n",
        "        # invariants-start\n"
        "        # WRONG: help ourselves BY FIAT to the resource for that carrier.\n"
        "        Invariant(machinery_state(forged))\n",
    ),
    "            piece = [d]  # type: List[int]\n",
    "            # WRONG: spend the fiat resource on the already-formed expression,\n"
    "            # out of the machinery's domain and off the shared account's books.\n"
    "            junk = resolve_name(forged, d)  # type: List[int]\n"
    "            piece = [d]  # type: List[int]\n",
)

# --- NON-VACUITY probe for the kind-1 (pass-through) branch that U6, U9, U10 and the
#     wrong-identity / drop rivals all diverge on: the GOLD impl with Assert(False)
#     spliced in at the head of that branch. It must be REJECTED, on the Assert. ---
_NONVAC_PASSTHROUGH = _swap(
    _IMPL,
    "        if k == 1:\n",
    "        if k == 1:\n"
    "            Assert(False)\n",
)


# ============================ POSITIVE CONTROLS (soundness) ============================
# Structurally-different but CORRECT impls. They MUST verify (else SPEC-TOO-STRONG).
# CAUTION (PBT_PLAN AVOID #2/#3): the @Pure fold `expanded` is FRONT-recursive, so a
# forward-append loop would need an f(a+b) lemma the verifier won't auto-discharge.
# Both positive controls therefore KEEP the back-to-front prepend direction and ALL
# gold framing asserts/invariants; only the executable SHAPE inside a step changes.

# --- P1: hoist the per-item identity into an explicit local before branching;
#         compute `piece` via a temp. Same content, same direction, gold asserts kept. ---
_P_LOCAL = _swap(
    _IMPL,
    "        if k == 1:\n"
    "            # An already-formed ordering expression: pass it through verbatim\n"
    "            # as a single target carrying its own identity. The name-resolution\n"
    "            # machinery is not invoked for it.\n"
    "            piece = [d]  # type: List[int]\n"
    "        else:\n"
    "            # A textual name: expand it through the name-resolution machinery,\n"
    "            # advancing the shared resolution state exactly once.\n"
    "            piece = resolve_name(state, d)\n",
    "        # Structurally different but identical content: branch on the textual\n"
    "        # case first, build the single pass-through target via an explicit local.\n"
    "        if k != 1:\n"
    "            piece = resolve_name(state, d)  # type: List[int]\n"
    "        else:\n"
    "            single = d  # type: int\n"
    "            piece = [single]\n",
)

# --- P2: precompute the loop bound into a separate decrementing index, keeping the
#         back-to-front direction and every gold invariant/assert. ---
_P_BOUND = _swap(
    _LOOP,
    "    i = len(kinds)\n"
    "    while i > 0:\n",
    "    n = len(kinds)  # type: int\n"
    "    i = n\n"
    "    while i > 0:\n",
)


# ============================ ADMISSIBILITY ============================
# Confirms the precondition admits a normal F2P-shaped input: a default ordering
# that MIXES an already-formed OrderBy item (kind 1) and a textual name (kind 0) —
# exactly the axiom_check.py reproduction (Meta.ordering = (F("rank").asc(...),
# "name")). The sample lists are freshly owned (full perm) so BOTH Acc(.,1/2)
# Requires clauses are discharged as explicit Asserts, and len(sk)==len(sd) holds.
# If the precondition rejected a normal mixed input those Asserts would fail =>
# PRECOND-TOO-STRONG.
#
# WHY NOT A SELF-CALL. This probe previously called expand_default_ordering(sk, sd)
# to witness admissibility. Once the spec carries Requires(MustTerminate(6)) that
# call site can no longer verify, and the reason is STRUCTURAL rather than a missing
# measure: MustTerminate levels must strictly DECREASE from caller to callee, and a
# self-call's caller and callee are the same method, so their levels are necessarily
# EQUAL. Nagini reports `Obligation leak check failed. Callee
# expand_default_ordering might not take all unsatisfied obligations from the
# caller.` Measured, so the diagnosis is not a guess:
#   * self-call at level 6                     -> leak check failed
#   * self-call with the level raised to 7      -> leak check failed (raising the
#     method's own level moves BOTH sides of the comparison together, so no level
#     can ever work)
#   * self-call guarded by `if len(kinds) > 0`  -> leak check failed (the guard is
#     satisfiable, so it does not make the call vacuous; the obligation is what
#     rejects, not reachability)
# The spliced call is genuinely unbounded recursion — the arguments (sk, sd) are
# fixed literals, NOT a descending measure, so the recursion never approaches a base
# case. This is the obligation doing its job, not spec over-strength.
#
# The claim is PRESERVED, not weakened, and in fact strengthened. Admissibility asks
# whether the PRECONDITION admits a normal input; the self-call was only ever a
# vehicle for establishing the Requires clauses at a call site. Asserting each
# Requires conjunct directly witnesses the same thing without the recursion, and the
# probe additionally unfolds `expanded` on the concrete mixed input all the way down
# to a closed form (PSeq(7) + resolve_name_seq(9)) — pinning that a kind-1 item
# contributes its own identity VERBATIM while the kind-0 item routes to the name
# machinery. The old case never checked that; it compared the call's result against
# the same `expanded` term on both sides, which holds by the postcondition alone.
# The `resolve_name` probe keeps a real obligated-callee call in the case (level 2
# under the method's 6), so the level ordering is still exercised.
# Non-vacuity was CONTROLLED: appending Assert(False) to this block makes the build
# fail (`Assertion False might not hold`), so the block is reachable and the
# unfold chain is proving something rather than verifying under a dead path.
_ADMISS = (
    "    sk = [1, 0]  # type: List[int]\n"
    "    sd = [7, 9]  # type: List[int]\n"
    "    Assert(len(sk) == len(sd))\n"
    # the two half-permission Requires clauses are establishable for a normal input
    "    Assert(Acc(list_pred(sk), 1 / 2))\n"
    "    Assert(Acc(list_pred(sd), 1 / 2))\n"
    # unfold `expanded` on the concrete mixed ordering down to a closed form: the
    # kind-1 item contributes its own identity verbatim, the kind-0 item resolves.
    "    Assert(ToSeq(sk)[0] == 1 and ToSeq(sd)[0] == 7)\n"
    "    Assert(len(ToSeq(sk).drop(1)) == 1 and len(ToSeq(sd).drop(1)) == 1)\n"
    "    Assert(ToSeq(sk).drop(1)[0] == 0 and ToSeq(sd).drop(1)[0] == 9)\n"
    "    Assert(len(ToSeq(sk).drop(1).drop(1)) == 0)\n"
    "    Assert(expanded(ToSeq(sk).drop(1).drop(1), ToSeq(sd).drop(1).drop(1))\n"
    "           == PSeq(0).take(0))\n"
    "    Assert(expanded(ToSeq(sk).drop(1), ToSeq(sd).drop(1))\n"
    "           == resolve_name_seq(9))\n"
    "    Assert(expanded(ToSeq(sk), ToSeq(sd)) == PSeq(7) + resolve_name_seq(9))\n"
    # unfold `name_items` on the same input: only the kind-0 item is to be
    # resolved, so the invocation obligation's multiset is exactly PMultiset(9) --
    # the kind-1 item (identity 7) is absent. This pins that a normal mixed
    # ordering is admissible AND that the invocation clause is not vacuous on it.
    "    Assert(name_items(ToSeq(sk).drop(1).drop(1), ToSeq(sd).drop(1).drop(1))\n"
    "           == ToMS(PSeq(0).take(0)))\n"
    "    Assert(name_items(ToSeq(sk).drop(1), ToSeq(sd).drop(1)) == PMultiset(9))\n"
    "    Assert(name_items(ToSeq(sk), ToSeq(sd)) == PMultiset(9))\n"
    # The shared resolution-state RESOURCE is held on entry, so the machinery is
    # INVOKABLE on it and its invocation account is readable -- admissibility of the
    # state carrier, not just the two ordering carriers. (Reading `invocations`
    # itself requires the resource, so the second Assert would not even frame if the
    # precondition failed to hand the state over.)
    "    Assert(machinery_state(state))\n"
    "    Assert(invocations(state) == invocations(state))\n"
    # No standalone resolve_name probe here: an invocation records itself against
    # the shared state, and the method's own invocation obligation would then
    # (correctly) report it as a resolution the ordering does not call for. The
    # spliced loop below calls the obligated callee for every kind-0 item, so the
    # MustTerminate level ordering (callee 2 strictly below the method's 6) is
    # exercised by the case regardless.
    + _LOOP
)


SPEC_TESTS = [
    # ---------------- FRAME-MUTATION (mandatory; read-only carriers) ----------------
    {
        "id": "frame-mutate-ids",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _LOOP, _F_IDS),
        "refinement": "Appends to `ids` (Acc(list_pred(ids),1/2) read-only). Its "
                      "faithful real patch would MUTATE opts.ordering (the related "
                      "model's shared Meta.ordering tuple/list) in place while "
                      "expanding it — corrupting class-level model metadata across "
                      "every later query, which the gold patch (a pure read of "
                      "opts.ordering into a fresh `results` list) never does. Not "
                      "the gold fix; would not faithfully resolve.",
        "rationale": "Must reject for INSUFFICIENT PERMISSION: ids is held at half "
                     "permission; .append needs full permission. Attributable to "
                     "the write (the gold postcondition clauses are kept verbatim, "
                     "so this is a permission failure, not a value mismatch).",
    },
    {
        "id": "frame-mutate-kinds",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _LOOP, _F_KINDS),
        "refinement": "Appends to `kinds` (Acc(list_pred(kinds),1/2) read-only). "
                      "Its faithful real patch would write to the shared "
                      "opts.ordering carrier of the related model's _meta — "
                      "mutating shared metadata the gold pure read never touches. "
                      "Not the gold fix.",
        "rationale": "Must reject for INSUFFICIENT PERMISSION: kinds is held at "
                     "half permission; .append needs full permission. The write is "
                     "the cause, not a value mismatch.",
    },

    # ---------------- UNIQUENESS / PARTIAL-DOMAIN ----------------
    {
        "id": "real-bug-route-orderby-through-name-machinery",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _U_REALBUG),
        "refinement": "The literal PRE-PATCH loop (== model_prepatch.py): every "
                      "opts.ordering item — including an already-formed OrderBy "
                      "expression — is handed to self.find_ordering_name(item,...), "
                      "whose get_order_dir subscripts its argument and raises "
                      "TypeError: 'OrderBy' object is not subscriptable. This is "
                      "the EXACT reported crash; the F2P "
                      "test_order_by_ptr_field_with_default_ordering_by_expression "
                      "fails (errors) pre-patch. This is the headline weakness.",
        "rationale": "Rejected by Ensures(ToSeq(Result()) == expanded(...)) on the "
                     "k==1 sub-domain: this rival produces resolve_name(state, d) == "
                     "resolve_name_seq(d) but the frozen contribution(1,d) == "
                     "PSeq(d); resolve_name_seq is @ContractOnly Ensures(True) "
                     "(opaque) so resolve_name_seq(d) == PSeq(d) is NOT provable.",
    },
    {
        "id": "inverted-kind-discriminant",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _U_INVERTED),
        "refinement": "Back-to-front discriminant: passes textual names through "
                      "raw and routes OrderBy items into the name machinery. "
                      "Faithful real patch: `if not isinstance(item, OrderBy): "
                      "results.append((item, False)); continue` else recurse — "
                      "textual field-names are appended unresolved (no concrete "
                      "columns) AND the OrderBy is fed to get_order_dir -> the "
                      "pre-patch TypeError. Wrong on BOTH F2P and the default-"
                      "ordering P2P tests.",
        "rationale": "Rejected by the postcondition: on k==1 it yields "
                     "resolve_name_seq(d) where contribution(1,d)==PSeq(d) is "
                     "required, and on k==0 it yields PSeq(d) where "
                     "contribution(0,d)==resolve_name_seq(d) is required — neither "
                     "equality is provable (opaque resolve_name_seq).",
    },
    {
        "id": "always-passthrough-never-resolve",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _U_ALWAYS_PASS),
        "refinement": "Treats EVERY item as already-formed (piece = [d]); never "
                      "calls the name machinery. Faithful real patch: append every "
                      "opts.ordering item as (item, False) and drop the recursion "
                      "-> a textual field-name in Meta.ordering is emitted raw "
                      "instead of resolved to its concrete column targets -> "
                      "default-ordering P2P tests (e.g. test_default_ordering) "
                      "break. Cheap supporting near-miss with a real refinement.",
        "rationale": "Rejected by Ensures(ToSeq(Result()) == expanded(...)) on the "
                     "k==0 sub-domain: it produces PSeq(d) where "
                     "contribution(0,d) == resolve_name_seq(d) is required; the "
                     "opaque resolve_name_seq blocks the equality.",
    },
    {
        "id": "wrong-passthrough-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _U_WRONG_ID),
        "refinement": "Right control flow but corrupts the OrderBy item's "
                      "identity: contributes PSeq(d+1) instead of PSeq(d). "
                      "Faithful real patch: append a different / freshly-built "
                      "OrderBy rather than `item` itself (identity NOT preserved) "
                      "-> the query orders by the wrong expression -> the F2P, "
                      "which sorts by the very passed-through ptr expression, "
                      "sorts on the wrong column.",
        "rationale": "Rejected by the postcondition's per-item content equality on "
                     "k==1: contribution(1,d) == PSeq(d) but the rival yields "
                     "PSeq(d+1); d+1 != d so the sequences differ.",
    },
    {
        "id": "drop-passthrough",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _U_DROP_PASS),
        "refinement": "Has the OrderBy guard (so no crash) but contributes NOTHING "
                      "for a k==1 item (piece = []). Faithful real patch: `if "
                      "isinstance(item, OrderBy): continue` WITHOUT the "
                      "results.append((item, False)) -> the ordering expression is "
                      "silently dropped from the output -> the query is missing the "
                      "expression it must order by -> F2P fails (wrong/short "
                      "ordering). Subtler than the crash but still wrong.",
        "rationale": "Rejected by the postcondition on k==1: it yields the empty "
                     "sequence where contribution(1,d) == PSeq(d) (a singleton) is "
                     "required.",
    },

    # ---------------- UNIQUENESS / CALLEE DOMAIN + MULTIPLICITY ----------------
    # The name-resolution machinery is PARTIAL (defined for textual names only) and
    # STATE-CHANGING. These four rivals all return the gold sequence and differ only
    # in WHICH items they invoke it on and HOW OFTEN, which is why a spec that
    # constrained the output alone admitted them (the recorded G-EQ finding).
    {
        "id": "out-of-domain-invocation-on-orderby",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _U_PROBE_ORDERBY),
        "refinement": "Correct pass-through, but the name machinery is ALSO "
                      "invoked on the already-formed OrderBy item and the value "
                      "discarded. Faithful real patch: an extra "
                      "self.find_ordering_name(item, ...) on the OrderBy item -> "
                      "get_order_dir subscripts it -> TypeError: 'OrderBy' object "
                      "is not subscriptable, the EXACT reported crash. F2P "
                      "test_order_by_ptr_field_with_default_ordering_by_expression "
                      "fails while the returned targets are gold-identical. This "
                      "is the sharpest witness the recorded audit found verifying.",
        "rationale": "Rejected by the invocation obligation Ensures(ToMS(ToSeq("
                     "state)) == Old(...) + name_items(...)): name_items omits "
                     "every kind-1 item, so an invocation recorded against the "
                     "OrderBy item's identity makes the recorded multiset strictly "
                     "larger than required. Not a value mismatch on Result().",
    },
    {
        "id": "unconditional-out-of-domain-invocation",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _U_PROBE_ALL),
        "refinement": "The machinery is invoked for EVERY item before the kind is "
                      "tested; the value is used only for name items. Faithful "
                      "real patch: hoist the recursive call above the isinstance "
                      "guard -> the OrderBy is still fed to get_order_dir -> the "
                      "same pre-patch TypeError -> F2P fails. Returned sequence "
                      "gold-identical.",
        "rationale": "Rejected by the invocation obligation: the kind-1 item's "
                     "identity is recorded against the shared resolution state but "
                     "name_items contains no kind-1 item, so the multisets differ.",
    },
    {
        "id": "duplicate-invocation-for-one-name",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _U_DOUBLE_RESOLVE),
        "refinement": "The machinery is invoked TWICE for a single textual name, "
                      "the first result discarded; the returned targets are "
                      "gold-identical. Faithful real patch: recurse twice per name "
                      "item. Because the recursion MUTATES the shared already_seen "
                      "/ join bookkeeping, the duplicate perturbs that state and "
                      "regresses the PASS_TO_PASS "
                      "test_related_ordering_duplicate_table_reference (the #24654 "
                      "regression) -- a preservation failure, not an F2P failure.",
        "rationale": "Rejected by the invocation obligation's MULTIPLICITY content: "
                     "name_items is a MULTISET containing each name item exactly "
                     "once, so resolving one name twice records that identity twice "
                     "and the multisets differ. (A set-valued obligation would miss "
                     "this; a multiset is what makes once-per-name observable.)",
    },
    {
        "id": "forged-resolution-state",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL, _U_FORGED_STATE),
        "refinement": "The dodge a naive invocation count would admit: invoke the "
                      "machinery against a locally fabricated carrier so the SHARED "
                      "state records nothing, then pass the expression through. "
                      "Returned sequence and recorded invocations both look gold. "
                      "Faithful real patch: there IS no second carrier in the "
                      "repository -- the recursion threads the compiler's own query "
                      "state -- so a 'private' invocation is still the real call on "
                      "the real OrderBy item -> get_order_dir subscripts it -> the "
                      "pre-patch TypeError -> F2P fails.",
        "rationale": "Rejected at the CALL SITE, not by a postcondition: "
                     "resolve_name Requires(machinery_state(state)), an ABSTRACT "
                     "PREDICATE (a resource, not a boolean fact), and the impl holds "
                     "that resource only for the state it was handed -- so the call "
                     "fails with INSUFFICIENT PERMISSION to access "
                     "machinery_state(forged). The invocation is unavailable, which "
                     "is what prevents the invocation obligation from being "
                     "escapable. An uninterpreted BOOLEAN guard could NOT reject "
                     "this: Ensures(True) is unrefutable, so any invented carrier "
                     "satisfies it -- that is the hole this case now covers.",
    },
    {
        "id": "forged-resolution-state-by-fiat",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _LOOP, _U_FIAT_STATE),
        "refinement": "U9's route plus the one extra step a rival reaches for when "
                      "the state is a resource: ACQUIRE the resolution-state resource "
                      "for a carrier of its own making -- here by FIAT, naming it in a "
                      "loop invariant, the only translatable way to help yourself to a "
                      "predicate instance you have no producer for -- then buy the "
                      "same free out-of-domain invocation and pass the expression "
                      "through. Same faithful real patch as the forged-state case -- "
                      "a 'private' invocation is still the real recursion applied to "
                      "the real OrderBy item -> get_order_dir subscripts it -> the "
                      "pre-patch TypeError -> F2P fails.",
        "rationale": "Rejected AT THE ACQUISITION, by the RESOURCE-ness of "
                     "machinery_state: an abstract predicate instance cannot be named "
                     "for free, so the fiat is charged on loop entry. Measured, "
                     "28.6s, the ONLY error reported: 'Loop invariant might not hold "
                     "on entry. There might be insufficient permission to access "
                     "machinery_state(forged).' The resource has exactly ONE producer "
                     "-- resolve_name, which returns it only for the carrier it was "
                     "given -- and the method's precondition grants it only for the "
                     "shared `state`, so no route to a second one exists. Distinct "
                     "from the plain forged-state case, which attempts no acquisition "
                     "and is refuted at the CALL SITE instead. Deliberately NOT "
                     "carried as Fold(machinery_state(forged)): that is a FRONT-END "
                     "refusal ('Invalid program: abstract.predicate.fold', nagini exit "
                     "1, no Viper verdict, 19.3s), i.e. evidence about Nagini rather "
                     "than about this spec -- the file never reaches the verifier, so "
                     "no clause can be shown to turn it down. Non-vacuous: the k == 1 "
                     "branch the private invocation sits on is reachable, pinned by "
                     "`nonvacuity-passthrough-branch-reachable` below.",
    },
    {
        "id": "nonvacuity-passthrough-branch-reachable",
        "kind": "admissibility",
        "expect": "reject",
        # NON-VACUITY CONTROL for every reject case that diverges inside the kind-1
        # pass-through branch (the real-bug route, the out-of-domain invocation, the
        # wrong pass-through identity, the dropped pass-through, and both forged-state
        # cases). Each of those claims something about that branch, and every such
        # claim is EMPTY if the branch is not reachable: a divergence under an
        # infeasible guard VERIFIES while proving nothing. The fiat case needs the
        # control most, because its error is reported at LOOP ENTRY -- that error
        # would fire even if the branch below it were dead.
        #
        # The probe is the frozen-correct impl with `Assert(False)` spliced in as the
        # first statement of the branch. It must be REJECTED, and rejected on the
        # Assert: a failing `Assert(False)` is exactly the statement "the verifier
        # cannot rule this program point out", i.e. k == 1 is satisfiable there under
        # the frozen Requires. If this case ever flips to `verified`, the pass-through
        # branch has gone dead and every sibling rejection stops being evidence about
        # the pass-through.
        #
        # Spliced into the CORRECT impl, not into a rival, so the failing Assert is
        # the only obligation that can break and the reject is unambiguously
        # attributable to reachability. `kind` is "admissibility" (=> PRECOND-TOO-
        # STRONG) because a dead pass-through branch would mean the precondition
        # admits no input carrying an already-formed ordering expression -- the very
        # in-domain input this instance exists for.
        "module": _swap(_BASE, _IMPL, _NONVAC_PASSTHROUGH),
        "refinement": "not a candidate implementation and not a refinement claim: an "
                      "instrumentation probe. `Assert(False)` is not something a real "
                      "patch could contain, so there is nothing to resolve -- it "
                      "exists to keep the kind-1-branch reject cases honest.",
        "rationale": "REJECT on the ASSERT, which is the non-vacuity signal: measured, "
                     "28.4s, the ONLY error reported: 'Assert might fail. Assertion "
                     "False might not hold.' at the spliced line. That the verifier "
                     "cannot discharge False at the head of the pass-through branch is "
                     "precisely the fact that k == 1 is satisfiable there, so the "
                     "branch every out-of-domain-invocation and pass-through rival "
                     "diverges on is LIVE. A `verified` outcome here would mean the "
                     "branch is infeasible and those rejections are vacuous.",
    },

    # ---------------- POSITIVE CONTROLS (soundness) ----------------
    {
        "id": "pos-control-explicit-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL, _P_LOCAL),
        "rationale": "A structurally-different but CORRECT impl: the textual-name "
                     "branch is tested first (k != 1) and the single pass-through "
                     "target is built via an explicit local `single`. Identical "
                     "content and the SAME back-to-front direction; every gold "
                     "framing assert (the four drop-equalities and "
                     "Assert(ToSeq(piece)==contribution(k,d))) is kept verbatim, so "
                     "the proof discharges. Must verify; a failure would be "
                     "SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-precomputed-bound",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _LOOP, _P_BOUND),
        "rationale": "A structurally-different but CORRECT impl: the loop bound is "
                     "hoisted into a separate local `n` and the index decrements "
                     "from it. Back-to-front direction, gold invariants, and gold "
                     "asserts all unchanged; identical content. Must verify; a "
                     "failure would be SPEC-TOO-STRONG. (Stays back-to-front to "
                     "avoid the front-recursive-fold proof gap, PBT_PLAN AVOID #3.)",
    },

    # ---------------- ADMISSIBILITY ----------------
    {
        "id": "admissibility-mixed-ordering",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _LOOP, _ADMISS),
        "rationale": "An F2P-shaped in-domain input: a 2-item default ordering "
                     "MIXING an OrderBy item (kind 1) and a textual name (kind 0) "
                     "— exactly the axiom_check.py reproduction. Every Requires "
                     "conjunct is discharged directly: the freshly-owned sample "
                     "lists establish both Acc(.,1/2) clauses and len(sk)==len(sd) "
                     "holds. If the precondition rejected a normal mixed input "
                     "those Asserts would fail => PRECOND-TOO-STRONG. The probe "
                     "also unfolds `expanded` on that input to the closed form "
                     "PSeq(7) + resolve_name_seq(9), pinning the kind-1 verbatim "
                     "pass-through against the kind-0 name resolution, and calls "
                     "the obligated `resolve_name` (level 2 < the method's 6) so "
                     "the level ordering stays exercised. Deliberately NOT a "
                     "self-call: with Requires(MustTerminate(6)) in the spec a "
                     "self-call can never verify, because caller and callee levels "
                     "are then necessarily equal rather than strictly decreasing "
                     "(measured at level 6, at a raised level 7, and under a "
                     "satisfiable guard — all three fail the obligation leak "
                     "check). The spliced call passed fixed literals, so it was "
                     "unbounded recursion; asserting the precondition directly "
                     "witnesses admissibility without it. See the _ADMISS comment.",
    },
]


# ============================ AXIOM LANE ============================
# This bundle has one A-consumed axiom (resolve_name / resolve_name_seq, the
# UNCHANGED recursive name machinery) and one A-reference deep model
# (contribution(1,id) == PSeq(id), the OrderBy pass-through). Both are validated
# against the REAL Django callee, in-container, by axiom_check.py (G-AX). The probes
# below re-derive that logic self-contained (the runner mounts only the probe; see
# PBT_PLAN AVOID #6) and EXECUTE the real find_ordering_name / get_order_dir (never
# scrape source; AVOID #4). apply_gold=True so the post-patch OrderBy guard is present.

# --- A-reference soundness: the OrderBy pass-through deep model == the real callee.
_AX_PASSTHROUGH_PROBE = r'''
import os, sys

def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    try:
        _configure_django()
    except Exception as exc:
        print("AXIOM-SOUNDNESS FAIL: Django not configurable: %r" % (exc,))
        return 1

    from django.db import connection, models
    from django.db.models import F
    from django.db.models.expressions import OrderBy

    # Parent whose default ordering MIXES an already-formed OrderBy expression and a
    # textual name; child via multi-table inheritance (the reported reproduction).
    class Parent(models.Model):
        name = models.CharField(max_length=20)
        rank = models.IntegerField()
        class Meta:
            app_label = "axcheck"
            ordering = (F("rank").asc(nulls_first=True), "name")

    class Child(Parent):
        class Meta:
            app_label = "axcheck"

    with connection.schema_editor() as editor:
        editor.create_model(Parent)
        editor.create_model(Child)

    qs = Child.objects.order_by("parent_ptr")
    compiler = qs.query.get_compiler(using="default")
    opts = Parent._meta

    # The REAL post-patch callee. Pre-patch this raises TypeError on the OrderBy item.
    results = compiler.find_ordering_name("parent_ptr", Child._meta, default_order="ASC")
    assert isinstance(results, list) and len(results) >= 1, (
        "find_ordering_name produced %r" % (results,))
    for entry in results:
        assert isinstance(entry, tuple) and len(entry) == 2, (
            "expected (expr, is_ref) pairs, got %r" % (entry,))
        expr, is_ref = entry
        assert isinstance(expr, OrderBy), (
            "every produced target must be an OrderBy, got %r" % (expr,))

    # contribution(1, id) == PSeq(id): the already-formed expression appears VERBATIM
    # as a SINGLE (OrderBy, False) target (identity preserved), in its position.
    meta_orderby = opts.ordering[0]
    assert isinstance(meta_orderby, OrderBy), "Meta.ordering[0] must be an OrderBy"
    passthrough = [e for e in results if e[0] is meta_orderby]
    assert len(passthrough) == 1, (
        "AXIOM-UNSOUND: the Meta.ordering OrderBy must be passed through verbatim "
        "exactly once (identity preserved); got %d matches in %r"
        % (len(passthrough), results))
    assert passthrough[0][1] is False, (
        "AXIOM-UNSOUND: the passed-through expression must carry is_ref == False")
    idx = next(i for i, e in enumerate(results) if e[0] is meta_orderby)
    assert idx == 0, (
        "AXIOM-UNSOUND: the OrderBy is Meta.ordering[0]; its contribution must come "
        "first, got index %d" % (idx,))

    # The guard is LOAD-BEARING: get_order_dir subscripts its argument, so handing it
    # an OrderBy crashes (the exact pre-patch TypeError) — i.e. the deep model is the
    # difference between resolve (crash) and pass-through (correct).
    from django.db.models.sql.query import get_order_dir
    raised = False
    try:
        get_order_dir(meta_orderby, "ASC")
    except TypeError:
        raised = True
    assert raised, (
        "AXIOM-UNSOUND: get_order_dir must subscript its argument so an OrderBy "
        "crashes; otherwise the isinstance guard is not load-bearing")

    print("AXIOM-SOUNDNESS OK: contribution(1,id)==PSeq(id) matches the real "
          "find_ordering_name (single (OrderBy,False) verbatim pass-through, in "
          "position); get_order_dir subscripts so the guard is load-bearing.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''

# --- A-consumed soundness + containment: the UNCHANGED name machinery resolves a
#     textual name to >=1 freshly-built OrderBy target (never the Meta OrderBy
#     identity), and is applied to textual names only.  Containment: resolve_name's
#     Requires domain is the whole `int` (no precondition beyond item_id:int), and
#     the model only ever passes d = ids[i-1] (an int) to it, so EVERY caller-
#     reachable input is inside the axiom domain — no reachable input is outside it.
_AX_RESOLVE_PROBE = r'''
import os, sys

def _configure_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=["django.contrib.contenttypes", "django.contrib.auth"],
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
        )
    django.setup()

def main():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "")
    try:
        _configure_django()
    except Exception as exc:
        print("AXIOM-SOUNDNESS FAIL: Django not configurable: %r" % (exc,))
        return 1

    from django.db import connection, models
    from django.db.models import F
    from django.db.models.expressions import OrderBy

    class Parent(models.Model):
        name = models.CharField(max_length=20)
        rank = models.IntegerField()
        class Meta:
            app_label = "axcheck"
            ordering = (F("rank").asc(nulls_first=True), "name")

    class Child(Parent):
        class Meta:
            app_label = "axcheck"

    with connection.schema_editor() as editor:
        editor.create_model(Parent)
        editor.create_model(Child)

    qs = Child.objects.order_by("parent_ptr")
    compiler = qs.query.get_compiler(using="default")
    opts = Parent._meta
    meta_orderby = opts.ordering[0]

    # resolve_name(textual name) -> a freshly produced owned list of >=1 OrderBy
    # targets; resolve_name_seq is the (uninterpreted, Ensures(True)) sequence it is
    # pinned to, so the binding ToSeq(Result()) == resolve_name_seq(id) over-claims
    # NOTHING about content. Operative consequence: textual names resolve to >=1
    # freshly-built OrderBy (NOT the Meta OrderBy identity), confirming the machinery
    # is applied to textual names only.
    name_targets = compiler.find_ordering_name("name", opts, default_order="ASC")
    assert isinstance(name_targets, list) and len(name_targets) >= 1, (
        "AXIOM-UNSOUND: a textual name must resolve to >= 1 target, got %r"
        % (name_targets,))
    for expr, is_ref in name_targets:
        assert isinstance(expr, OrderBy), (
            "AXIOM-UNSOUND: a textual name must resolve to OrderBy targets, got %r"
            % (expr,))
        assert expr is not meta_orderby, (
            "AXIOM-UNSOUND: a textual name must resolve to a FRESHLY built OrderBy, "
            "not the Meta.ordering expression's identity")

    # Caller-domain CONTAINMENT: the model passes only int identity tags (d=ids[i-1])
    # to resolve_name, and resolve_name's Requires domain is `int` with no further
    # precondition. Every caller-reachable input is therefore inside the axiom domain
    # (the entire int domain); none lies outside it. Confirm the real callee accepts
    # the in-domain textual-name path used by the model (already exercised above).
    assert isinstance(name_targets[0][0], OrderBy)

    print("AXIOM-SOUNDNESS OK: the unchanged name machinery resolves a textual name "
          "to >=1 freshly-built OrderBy target (never the Meta OrderBy identity); the "
          "resolve_name/resolve_name_seq binding is tautological (Ensures(True)). "
          "CONTAINMENT OK: the model passes only int ids to resolve_name, all inside "
          "the axiom's int Requires domain.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-orderby-passthrough",
        "axiom": "contribution(1, id) == PSeq(id)  (OrderBy pass-through, A-reference)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,  # the OrderBy guard is the post-patch behaviour
        "probe": _AX_PASSTHROUGH_PROBE,
        "rationale": "If the real post-patch find_ordering_name ever fails to pass "
                     "the Meta.ordering OrderBy through verbatim as a single "
                     "(OrderBy, False) target in position — or if get_order_dir did "
                     "NOT subscript its argument (guard not load-bearing) — the "
                     "deep model contribution(1,id)==PSeq(id) would be AXIOM-UNSOUND. "
                     "Drives the real callee; reuses/strengthens axiom_check.py.",
    },
    {
        "id": "ax-sound-cover-resolve-name",
        "axiom": "resolve_name / resolve_name_seq (unchanged name machinery, A-consumed)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,  # callee is UNCHANGED by the patch; apply_gold is harmless
        "probe": _AX_RESOLVE_PROBE,
        "rationale": "The resolve_name binding is a definitional tautology "
                     "(resolve_name_seq is Ensures(True), opaque), so it over-claims "
                     "nothing; the operative consequence is that the machinery is "
                     "applied to textual names only and resolves them to >=1 "
                     "freshly-built OrderBy target. CONTAINMENT: the model passes "
                     "only int ids (d=ids[i-1]) to resolve_name and the axiom domain "
                     "is the whole int — every reachable input is inside it, so it is "
                     "not AXIOM-TOO-WEAK-FOR-CALLER.",
    },
]
