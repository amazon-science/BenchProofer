# properties.py — PBT manifest for sympy__sympy-19495. NOT a Nagini module; a
# record of adversarial falsification cases. The runner (swebench_nagini.pbt)
# parses SPEC_TESTS / AXIOM_TESTS, executes each, and stamps RESULT.
#
# Defended surface (read from model.py / refinement.md / mapping.md / instance):
#   The change is ConditionSet._eval_subs free-symbol branch (old != bound sym).
#   The buggy pre-patch code, when the substituted predicate collapsed to
#   S.true, did `return ConditionSet(new, Contains(new, base), base)` — i.e. it
#   rebuilt the set keyed on the REPLACEMENT value `new` (membership predicate
#   stays a non-trivial restriction => a ConditionSet on `new`), so the bound
#   variable `x` was effectively mistaken for `y`. The fix ALWAYS returns
#   `self.func(self.sym, cond, base)` — rebuilt on the ORIGINAL bound symbol.
#
#   model.py models this as two functions, BOTH PURE value producers over plain
#   `int` carriers (no reference-typed inputs => NO read-only Acc(...,1/2), so
#   there is NO frame to mutate; see 'assessment'):
#
#   * build(sym, cond, base, base_kind, listed_kind, listed_base, merged_sym,
#       merged_base) -> Result0
#       (A-reference deep model of ConditionSet.__new__'s reduction;
#       meta.axioms == [], NOT a consumed @ContractOnly axiom). The reduction
#       the real constructor performs depends on BOTH the predicate's truth
#       status and the SHAPE of the base domain, so base_kind is an observed
#       input, and it has FOUR values because the constructor dispatches on four
#       shapes (empty / explicit listing / itself a restricted object / plain).
#       LOAD-BEARING posts:
#         cond==COND_FALSE                      => kind==K_EMPTY
#         base_kind==BASE_EMPTY                 => kind==K_EMPTY
#         cond==COND_TRUE and base_kind!=EMPTY  => kind==K_BASE and base==base
#         cond==COND_OPEN and base_kind==PLAIN  => kind==K_SET and sym==sym
#                                                  and base==base
#                                                  and cond==COND_OPEN
#         cond==COND_OPEN and base_kind==LISTED => kind==listed_kind
#                                                  (base==listed_base when
#                                                   listed_kind!=K_EMPTY; and
#                                                   sym==sym, cond==COND_OPEN
#                                                   when listed_kind==K_SET)
#         cond==COND_OPEN and base_kind==MERGED => kind==K_SET and
#                                                  sym==merged_sym and
#                                                  base==merged_base
#             (the merge with a base domain that is itself a restricted object:
#              the ONE shape whose bound variable is not carried over, and the
#              one the constructor performs with no further reduction)
#
#   * replace_free_parameter(self_sym, new, cond_after, base_after, base_kind,
#       listed_kind, listed_base, merged_sym, merged_base) -> Result0
#       (A-reference deep model of the
#       patched free-symbol branch). LOAD-BEARING posts — these are the
#       discriminators G-DIFF/model_prepatch fail on:
#         cond_after==COND_FALSE  => kind==K_EMPTY
#         base_kind==BASE_EMPTY   => kind==K_EMPTY
#         cond_after==COND_TRUE and base_kind!=BASE_EMPTY
#                                 => kind==K_BASE and base==base_after   (<-- the
#             headline: a collapsed-to-true predicate yields the base domain
#             itself, NEVER a fresh restricted object keyed on `new`)
#         cond_after==COND_OPEN and base_kind==BASE_PLAIN
#                                 => kind==K_SET and sym==self_sym (NOT `new`)
#                                    and base==base_after and cond==COND_OPEN
#         cond_after==COND_OPEN and base_kind==BASE_LISTED
#                                 => kind==listed_kind (base==listed_base when
#                                    non-empty; and any surviving restricted
#                                    object is STILL keyed on self_sym)
#         cond_after==COND_OPEN and base_kind==BASE_MERGED
#                                 => kind==K_SET and sym==merged_sym and
#                                    base==merged_base  (<-- the merge: where the
#             replacement-applied base domain is itself a restricted object the
#             two restrictions are merged, the merged object stands over the
#             INNER base domain, and the bound variable is the one the merge
#             settles on -- the only shape not keyed on self_sym, and still never
#             `new` as such)
#
#   TOTALITY (the obligation both functions now carry): each is Requires-d to
#   DELIVER its reduced object — Requires(MustTerminate(_)) on Result0.__init__,
#   build and replace_free_parameter. Without it Nagini proves PARTIAL
#   correctness only: every Ensures above is claimed solely of runs that reach a
#   return, so an implementation that never gets there satisfies the entire
#   postcondition set vacuously and verifies while doing nothing. That is a
#   `verify`-does-not-imply-resolve break the value clauses cannot express, so it
#   lives in the precondition as an obligation and is exercised by the
#   NON-DELIVERY reject lane below.
#
# Attack map (only classes that APPLY — frame-mutation/ungrounded-oracle/
# control-flow-effect are N/A here, justified in 'assessment'):
#   * NON-DELIVERY (uniqueness) — rivals whose returned VALUE is gold wherever
#     they return at all, but which on some slice of the admitted domain never
#     deliver: an unguarded self-call on unchanged arguments, an endless loop
#     ahead of the gold return, a loop carrying a measure it does not keep, and
#     a partial-domain variant that is gold on the eagerly-returning paths and
#     non-delivering elsewhere. Every value clause holds vacuously of these, so
#     only the totality obligation rejects them. Each carries a refinement.
#   * PARTIAL-DOMAIN / value-double-mask (uniqueness) — rivals correct on most
#     of {FALSE,TRUE,OPEN} x {EMPTY,LISTED,PLAIN} but diverging on the
#     load-bearing sub-domain (the exact pre-patch bug: TRUE -> keyed-on-new;
#     OPEN -> keyed-on-new; TRUE -> empty; build OPEN keyed on a wrong
#     constant; the base-shape reductions dropped or mis-keyed, including the
#     merge keyed on the OUTER bound variable or left standing over the outer
#     base domain). Each carries a refinement.
#   * POSITIVE CONTROLS (soundness) — structurally-different but CORRECT impls
#     (branch reorder; inlined reduction instead of delegating to build) MUST
#     verify, else SPEC-TOO-STRONG. Reorders/inlines keep the gold proof valid
#     (no loop, no induction lemma — directives 2/3 N/A but still respected).
#   * ADMISSIBILITY — a self-call on the F2P-shaped collapsed-to-true input
#     asserting the base-domain result; the precondition must admit it.
#   * AXIOM lane — the two A-reference deep models are validated against the
#     REAL patched SymPy by axiom_check.py; persisted here as an axiom-soundness
#     probe (real-callee == model, gold applied, in Docker).
from pathlib import Path

INSTANCE = "sympy__sympy-19495"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()

# The two impl-region bodies, verbatim from the frozen model.py. Region-surgery:
# we _swap ONLY these (everything between # impl-start/# impl-end) so same_spec
# is guaranteed — the frozen axioms/pure/pre/post-conditions are never touched.
_BUILD_IMPL = (
    "    if cond == COND_FALSE:\n"
    "        return Result0(K_EMPTY, sym, base, cond)\n"
    "    elif base_kind == BASE_EMPTY:\n"
    "        return Result0(K_EMPTY, sym, base, cond)\n"
    "    elif cond == COND_TRUE:\n"
    "        return Result0(K_BASE, sym, base, cond)\n"
    "    elif base_kind == BASE_LISTED:\n"
    "        return Result0(listed_kind, sym, listed_base, cond)\n"
    "    elif base_kind == BASE_MERGED:\n"
    "        if merged_sym == MERGE_REFUSED:\n"
    "            return Result0(K_REFUSED, merged_sym, merged_base, cond)\n"
    "        return Result0(K_SET, merged_sym, merged_base, cond)\n"
    "    else:\n"
    "        return Result0(K_SET, sym, base, cond)"
)
_RFP_IMPL = ("    return build(self_sym, cond_after, base_after, base_kind, "
             "listed_kind,\n                 listed_base, merged_sym, merged_base)")


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _build(impl):
    return _swap(_BASE, _BUILD_IMPL, impl)


def _rfp(impl):
    return _swap(_BASE, _RFP_IMPL, impl)


SPEC_TESTS = [

    # ===================================================================== #
    # POSITIVE CONTROLS (soundness) — a structurally-DIFFERENT but CORRECT
    # impl MUST verify, else SPEC-TOO-STRONG. The only structural freedom is
    # branch-reorder / inlining of a straight-line match; no loop, no
    # @Pure fold, no induction lemma (directives 2/3 do not bite). Each keeps
    # every gold proof obligation intact.
    # ===================================================================== #
    {
        "id": "pos-build-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _build(
            "    # structurally different: test the empty base domain FIRST, then the\n"
            "    # false predicate, then TRUE, then the listed base. Both of the first\n"
            "    # two cases yield the empty domain, so swapping them is behaviour-\n"
            "    # preserving; same reduction, branches reordered.\n"
            "    if base_kind == BASE_EMPTY:\n"
            "        return Result0(K_EMPTY, sym, base, cond)\n"
            "    elif cond == COND_FALSE:\n"
            "        return Result0(K_EMPTY, sym, base, cond)\n"
            "    elif cond == COND_TRUE:\n"
            "        return Result0(K_BASE, sym, base, cond)\n"
            "    elif base_kind == BASE_LISTED:\n"
            "        return Result0(listed_kind, sym, listed_base, cond)\n"
            "    elif base_kind == BASE_MERGED:\n"
            "        if merged_sym == MERGE_REFUSED:\n"
            "            return Result0(K_REFUSED, merged_sym, merged_base, cond)\n"
            "        return Result0(K_SET, merged_sym, merged_base, cond)\n"
            "    else:\n"
            "        return Result0(K_SET, sym, base, cond)"
        ),
        "rationale": "a correct build with the two empty-domain branches swapped must "
                     "still verify: both yield K_EMPTY, and the preconditions pin cond "
                     "and base_kind to exactly one tag each, so every Ensures clause "
                     "still holds. If it rejects => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-rfp-inline",
        "kind": "soundness",
        "expect": "verify",
        "module": _rfp(
            "    # structurally different: inline the reduction here instead of\n"
            "    # delegating to build(). Keyed on the ORIGINAL self_sym; the TRUE\n"
            "    # case yields the base domain (base_after), never a set on `new`.\n"
            "    if cond_after == COND_FALSE:\n"
            "        return Result0(K_EMPTY, self_sym, base_after, cond_after)\n"
            "    elif base_kind == BASE_EMPTY:\n"
            "        return Result0(K_EMPTY, self_sym, base_after, cond_after)\n"
            "    elif cond_after == COND_TRUE:\n"
            "        return Result0(K_BASE, self_sym, base_after, cond_after)\n"
            "    elif base_kind == BASE_LISTED:\n"
            "        return Result0(listed_kind, self_sym, listed_base, cond_after)\n"
            "    elif base_kind == BASE_MERGED:\n"
            "        if merged_sym == MERGE_REFUSED:\n"
            "            return Result0(K_REFUSED, merged_sym, merged_base, cond_after)\n"
            "        return Result0(K_SET, merged_sym, merged_base, cond_after)\n"
            "    else:\n"
            "        return Result0(K_SET, self_sym, base_after, cond_after)"
        ),
        "rationale": "a faithful replace_free_parameter that inlines the reduction "
                     "(rather than calling build) must verify: the TRUE case returns "
                     "K_BASE with base==base_after, the open/PLAIN case returns K_SET "
                     "keyed on self_sym, the listed case returns the folded outcome — "
                     "exactly the postcondition. If it rejects => SPEC-TOO-STRONG.",
    },

    # ===================================================================== #
    # ADMISSIBILITY — the preconditions (cond_after in {FALSE,TRUE,OPEN},
    # base_kind in {EMPTY,LISTED,PLAIN}, listed_kind a kind) must admit a
    # normal F2P-shaped input. The impl computes the result and asserts, for
    # the collapsed-to-true F2P shape over a non-empty base domain, that it is
    # the base domain keyed on self_sym (never `new`) — the precondition is
    # satisfiable, not vacuous. expect=verify; reject => PRECOND-TOO-STRONG.
    # ===================================================================== #
    {
        "id": "admiss-rfp-true",
        "kind": "admissibility",
        "expect": "verify",
        "module": _rfp(
            "    result = build(self_sym, cond_after, base_after, base_kind,\n"
            "                   listed_kind, listed_base, merged_sym,\n"
            "                   merged_base)  # type: Result0\n"
            "    # admissibility: the F2P collapsed-to-true input (cond_after==COND_TRUE\n"
            "    # over a non-empty base domain, e.g. ConditionSet(n, n<x, [-oo,0])\n"
            "    # .subs(x, p)) is admitted; the result is the base domain (K_BASE /\n"
            "    # base_after), NOT a set keyed on `new`.\n"
            "    Assert(Implies(cond_after == COND_TRUE and base_kind != BASE_EMPTY,\n"
            "                   result.kind == K_BASE and result.base == base_after))\n"
            "    Assert(Implies(cond_after == COND_OPEN and base_kind == BASE_PLAIN,\n"
            "                   result.sym == self_sym))\n"
            "    return result"
        ),
        "rationale": "the precondition admits a normal collapsed-to-true / open input "
                     "over an ordinary (non-empty, non-listed) base domain; the Asserts "
                     "are discharged from build's Ensures. If it rejects => "
                     "PRECOND-TOO-STRONG (the precondition would exclude the F2P input).",
    },

    # ===================================================================== #
    # NON-DELIVERY (uniqueness) — the returned VALUE is gold wherever these
    # return at all, so EVERY value clause above holds of them; what they omit
    # is delivering a result. Only the totality obligation
    # (Requires(MustTerminate(_))) rejects them. If any VERIFIES, the spec is
    # SPEC-TOO-WEAK in the way a value postcondition structurally cannot see:
    # partial correctness claims each Ensures solely of runs reaching a return.
    # ===================================================================== #
    {
        # Unguarded self-call on its own unchanged arguments: the whole
        # postcondition set is satisfied vacuously because no run reaches a
        # return. Nothing about the returned VALUE is wrong — there is no value.
        "id": "weak-rfp-never-delivers-selfcall",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rfp(
            "    # NON-DELIVERY: re-enter the same replacement on the same unchanged\n"
            "    # arguments, so the reduced object is never handed back.\n"
            "    return replace_free_parameter(self_sym, new, cond_after, base_after,\n"
            "                                  base_kind, listed_kind, listed_base,\n"
            "                                  merged_sym, merged_base)"
        ),
        "refinement": "the faithful real patch replaces the branch's tail with a "
                      "re-entry of the same substitution on the same arguments "
                      "(`return self._eval_subs(old, new)`), which recurses without "
                      "bound. It applies cleanly, but the F2P test_subs_CondSet never "
                      "returns a value to compare: the substitution raises a recursion "
                      "error instead of yielding the base domain, so the F2P assertion "
                      "fails while the untouched P2P tests still pass => it would NOT "
                      "resolve.",
        "rationale": "REJECT comes from the totality obligation "
                     "`Requires(MustTerminate(3))` on replace_free_parameter: the "
                     "self-call cannot discharge a strictly smaller measure, so the "
                     "obligation leaks. Every VALUE clause holds vacuously, so if this "
                     "verified => SPEC-TOO-WEAK (the spec would claim only partial "
                     "correctness and admit an implementation that answers nothing).",
    },
    {
        # Endless loop ahead of an otherwise-gold return: same vacuity, reached
        # by iteration rather than recursion.
        "id": "weak-rfp-never-delivers-loop",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rfp(
            "    # NON-DELIVERY: spin without end before the (otherwise gold) return,\n"
            "    # so no admitted input ever receives its reduced object.\n"
            "    i = 0\n"
            "    while i >= 0:\n"
            "        i = i + 1\n"
            "    return build(self_sym, cond_after, base_after, base_kind, listed_kind,\n"
            "                 listed_base, merged_sym, merged_base)"
        ),
        "refinement": "the faithful real patch keeps the gold tail but prefixes it with "
                      "an unbounded loop. The substitution then never returns, so the "
                      "F2P assertion on the collapsed-to-true result is never reached "
                      "and the suite hangs rather than resolving => it would NOT "
                      "resolve.",
        "rationale": "REJECT comes from the same totality obligation: an unbounded loop "
                     "inside a MustTerminate context cannot take the obligation from "
                     "its caller. If it verified => SPEC-TOO-WEAK (divergence by "
                     "iteration would satisfy every clause).",
    },
    {
        # A loop that CLAIMS a measure it does not keep — the obligation must be
        # checked, not merely asserted, or the reject above is bought back.
        "id": "weak-rfp-measure-not-kept",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rfp(
            "    # NON-DELIVERY: spin without end while ASSERTING a termination\n"
            "    # measure, to confirm the obligation is checked and not taken on trust.\n"
            "    i = 0\n"
            "    while i >= 0:\n"
            "        Invariant(MustTerminate(1))\n"
            "        Invariant(i >= 0)\n"
            "        i = i + 1\n"
            "    return build(self_sym, cond_after, base_after, base_kind, listed_kind,\n"
            "                 listed_base, merged_sym, merged_base)"
        ),
        "refinement": "same non-delivering real patch as the loop case above; the "
                      "asserted measure is a claim about the model, not about the repo "
                      "code, and the substitution still never returns => it would NOT "
                      "resolve.",
        "rationale": "REJECT comes from the measure being VERIFIED rather than assumed: "
                     "the loop does not keep its promise to terminate. If it verified "
                     "=> the obligation would be discharge-on-assertion and the two "
                     "rejects above would be recoverable, i.e. SPEC-TOO-WEAK.",
    },
    {
        # PARTIAL non-delivery: gold on the two eagerly-returning paths the value
        # clauses pin hardest, non-delivering on the rest of the admitted domain.
        "id": "weak-rfp-partial-then-never-delivers",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rfp(
            "    # PARTIAL-DOMAIN + NON-DELIVERY: gold on the collapsed-to-true and the\n"
            "    # open/non-enumerated paths, never delivering anywhere else.\n"
            "    if cond_after == COND_TRUE and base_kind != BASE_EMPTY:\n"
            "        return Result0(K_BASE, self_sym, base_after, cond_after)\n"
            "    if cond_after == COND_OPEN and base_kind == BASE_PLAIN:\n"
            "        return Result0(K_SET, self_sym, base_after, COND_OPEN)\n"
            "    return replace_free_parameter(self_sym, new, cond_after, base_after,\n"
            "                                  base_kind, listed_kind, listed_base,\n"
            "                                  merged_sym, merged_base)"
        ),
        "refinement": "the faithful real patch answers normally when the substituted "
                      "predicate collapsed to true or stayed open over a non-enumerated "
                      "domain, and re-enters itself otherwise — so the empty-domain and "
                      "explicit-listing inputs of the F2P/P2P suite never return => it "
                      "would NOT resolve.",
        "rationale": "REJECT comes from the totality obligation holding on the WHOLE "
                     "admitted domain, not just the slice the value clauses pin "
                     "eagerly. If it verified => SPEC-TOO-WEAK (a rival could deliver "
                     "only where the spec looks hardest).",
    },
    {
        # The construction itself must deliver: divergence inside `build` is the
        # same hole one level down, and the rebuild's caller depends on it.
        "id": "weak-build-never-delivers",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _build(
            "    # NON-DELIVERY inside the construction: spin without end before the\n"
            "    # (otherwise gold) reduction, so no object is ever produced.\n"
            "    i = 0\n"
            "    while i >= 0:\n"
            "        i = i + 1\n"
            "    if cond == COND_FALSE:\n"
            "        return Result0(K_EMPTY, sym, base, cond)\n"
            "    elif base_kind == BASE_EMPTY:\n"
            "        return Result0(K_EMPTY, sym, base, cond)\n"
            "    elif cond == COND_TRUE:\n"
            "        return Result0(K_BASE, sym, base, cond)\n"
            "    elif base_kind == BASE_LISTED:\n"
            "        return Result0(listed_kind, sym, listed_base, cond)\n"
            "    elif base_kind == BASE_MERGED:\n"
            "        if merged_sym == MERGE_REFUSED:\n"
            "            return Result0(K_REFUSED, merged_sym, merged_base, cond)\n"
            "        return Result0(K_SET, merged_sym, merged_base, cond)\n"
            "    else:\n"
            "        return Result0(K_SET, sym, base, cond)"
        ),
        "refinement": "build models the real constructor's reduction, which every "
                      "caller — including the rebuilt free-parameter substitution — "
                      "waits on. A real constructor that never returned would hang the "
                      "whole suite, not just the F2P case => it would NOT resolve.",
        "rationale": "REJECT comes from `Requires(MustTerminate(2))` on build. If it "
                     "verified => SPEC-TOO-WEAK: the deep reduction model could be "
                     "satisfied without ever producing the object it claims to build.",
    },

    # ===================================================================== #
    # PARTIAL-DOMAIN / value-double-mask (uniqueness) — rivals correct on most
    # of the domain but diverging on a LOAD-BEARING sub-domain. If any
    # VERIFIES the frozen spec, it is SPEC-TOO-WEAK. Each carries the
    # refinement that its faithful real patch would NOT resolve.
    # ===================================================================== #
    {
        # THE HEADLINE BUG (model_prepatch.py verbatim shape): when the predicate
        # collapsed to true, rebuild keyed on `new` with the membership predicate
        # staying a non-trivial restriction (COND_OPEN) => a K_SET keyed on `new`,
        # not the base domain. Correct on FALSE/OPEN; wrong exactly on TRUE.
        "id": "weak-rfp-true-keyed-on-new",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rfp(
            "    # PARTIAL-DOMAIN (the pre-patch bug): on TRUE, rebuild keyed on `new`\n"
            "    # wrapped in a membership predicate that stays a non-trivial restriction\n"
            "    # (COND_OPEN) => K_SET on `new`, instead of the base domain.\n"
            "    if cond_after == COND_TRUE:\n"
            "        return build(new, COND_OPEN, base_after, base_kind, listed_kind,\n"
            "                     listed_base, merged_sym, merged_base)\n"
            "    return build(self_sym, cond_after, base_after, base_kind, listed_kind,\n"
            "                 listed_base, merged_sym, merged_base)"
        ),
        "refinement": "this IS the pre-patch code: `if cond is S.true: return "
                      "ConditionSet(new, Contains(new, base), base)`. On the F2P input "
                      "ConditionSet(x, Contains(y,[-1,1]), imageset(...asin(y)...)).subs"
                      "(y,1/3) it returns ConditionSet(1/3, Contains(1/3,base), base) "
                      "(Out[75]) which does NOT .dummy_eq(imageset(...asin(1/3)...)); and "
                      "ConditionSet(n,n<x,[-oo,0]).subs(x,p) would not equal Interval"
                      "(-oo,0). The added F2P test_subs_CondSet asserts exactly those => "
                      "it would NOT resolve.",
        "rationale": "REJECT comes from postcondition `cond_after==COND_TRUE and "
                     "base_kind!=BASE_EMPTY => kind==K_BASE and base==base_after`: this "
                     "returns kind==K_SET keyed on `new`. If it verified => "
                     "SPEC-TOO-WEAK (the discriminating clause hollow).",
    },
    {
        # OPEN case adopts `new` as the bound symbol (the same family of bug, on
        # the open sub-domain): the restricted object is keyed on `new` instead of
        # self_sym. Correct on FALSE/TRUE; wrong sym exactly on OPEN.
        "id": "weak-rfp-open-keyed-on-new",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rfp(
            "    # PARTIAL-DOMAIN: the OPEN restricted object is keyed on `new`\n"
            "    # (the replacement value) instead of the ORIGINAL self_sym.\n"
            "    if cond_after == COND_OPEN:\n"
            "        return build(new, cond_after, base_after, base_kind, listed_kind,\n"
            "                     listed_base, merged_sym, merged_base)\n"
            "    return build(self_sym, cond_after, base_after, base_kind, listed_kind,\n"
            "                 listed_base, merged_sym, merged_base)"
        ),
        "refinement": "a faithful real patch that, on the open branch, returned "
                      "self.func(new, cond, base) would rebuild the set on the "
                      "replacement value instead of self.sym. P2P test_subs_CondSet "
                      "checks e.g. ConditionSet(f(x), f(x)<1, {w,z}).subs(f(x), y) == "
                      "ConditionSet(y, y<1, {w,z}) and the open-stays-open cases keyed on "
                      "the original symbol => keying on `new` would produce the wrong "
                      "bound symbol and NOT resolve.",
        "rationale": "REJECT comes from postcondition `cond_after==COND_OPEN and "
                     "base_kind==BASE_PLAIN => kind==K_SET and sym==self_sym`: this "
                     "returns sym==new (!=self_sym for the discriminating input). If it "
                     "verified => SPEC-TOO-WEAK.",
    },
    {
        # TRUE case collapses to the EMPTY domain instead of the base domain — a
        # different wrong reduction on the load-bearing sub-domain. Correct on
        # FALSE/OPEN; wrong exactly on TRUE.
        "id": "weak-rfp-true-to-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rfp(
            "    # PARTIAL-DOMAIN: on TRUE collapse to the EMPTY domain instead of the\n"
            "    # base domain (drops everyone in base who trivially qualifies).\n"
            "    if cond_after == COND_TRUE:\n"
            "        return build(self_sym, COND_FALSE, base_after, base_kind,\n"
            "                     listed_kind, listed_base, merged_sym,\n"
            "                     merged_base)\n"
            "    return build(self_sym, cond_after, base_after, base_kind, listed_kind,\n"
            "                 listed_base, merged_sym, merged_base)"
        ),
        "refinement": "a faithful real patch that returned S.EmptySet when the predicate "
                      "collapsed to true would drop every member of the base domain. The "
                      "F2P ConditionSet(n,n<x,[-oo,0]).subs(x,p) must equal Interval"
                      "(-oo,0) (the whole base), not EmptySet; and the issue-17341 case "
                      "must dummy_eq the imageset, not the empty set => it would NOT "
                      "resolve.",
        "rationale": "REJECT comes from postcondition `cond_after==COND_TRUE and "
                     "base_kind!=BASE_EMPTY => kind==K_BASE`: this returns kind==K_EMPTY. "
                     "If it verified => SPEC-TOO-WEAK.",
    },
    {
        # build's OPEN/PLAIN case keyed on a fixed wrong constant (0) instead of
        # `sym`: correct only on the sub-domain sym==0. This attacks the build deep
        # model directly (the constructor's bound-symbol propagation).
        "id": "weak-build-open-wrong-sym",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _build(
            "    if cond == COND_FALSE:\n"
            "        return Result0(K_EMPTY, sym, base, cond)\n"
            "    elif base_kind == BASE_EMPTY:\n"
            "        return Result0(K_EMPTY, sym, base, cond)\n"
            "    elif cond == COND_TRUE:\n"
            "        return Result0(K_BASE, sym, base, cond)\n"
            "    elif base_kind == BASE_LISTED:\n"
            "        return Result0(listed_kind, sym, listed_base, cond)\n"
            "    elif base_kind == BASE_MERGED:\n"
            "        if merged_sym == MERGE_REFUSED:\n"
            "            return Result0(K_REFUSED, merged_sym, merged_base, cond)\n"
            "        return Result0(K_SET, merged_sym, merged_base, cond)\n"
            "    else:\n"
            "        # PARTIAL-DOMAIN: key the restricted object on a fixed constant 0\n"
            "        # rather than the given bound variable sym (correct only if sym==0).\n"
            "        return Result0(K_SET, 0, base, cond)"
        ),
        "refinement": "build models ConditionSet.__new__'s reduction; a real constructor "
                      "that minted the open ConditionSet on a fixed wrong symbol (not the "
                      "passed sym) would break every open-case caller — including the "
                      "patched _eval_subs, which relies on the rebuilt set being keyed on "
                      "self.sym. P2P test_CondSet / test_subs_CondSet construct open "
                      "ConditionSets on distinct symbols and check the bound symbol => it "
                      "would NOT resolve.",
        "rationale": "REJECT comes from postcondition `cond==COND_OPEN and "
                     "base_kind==BASE_PLAIN => sym==sym`: this returns sym==0 != sym for "
                     "any sym!=0. If it verified => SPEC-TOO-WEAK (build's bound-symbol "
                     "propagation unpinned).",
    },
    {
        # build's TRUE case returns a DIFFERENT base (drops base==base): mints the
        # base domain on a fixed constant 0 base id. Correct only if base==0.
        "id": "weak-build-true-wrong-base",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _build(
            "    if cond == COND_FALSE:\n"
            "        return Result0(K_EMPTY, sym, base, cond)\n"
            "    elif base_kind == BASE_EMPTY:\n"
            "        return Result0(K_EMPTY, sym, base, cond)\n"
            "    elif cond == COND_TRUE:\n"
            "        # PARTIAL-DOMAIN: return the base domain on a fixed wrong base id 0\n"
            "        # (drops base==base; correct only if base==0).\n"
            "        return Result0(K_BASE, sym, 0, cond)\n"
            "    elif base_kind == BASE_LISTED:\n"
            "        return Result0(listed_kind, sym, listed_base, cond)\n"
            "    elif base_kind == BASE_MERGED:\n"
            "        if merged_sym == MERGE_REFUSED:\n"
            "            return Result0(K_REFUSED, merged_sym, merged_base, cond)\n"
            "        return Result0(K_SET, merged_sym, merged_base, cond)\n"
            "    else:\n"
            "        return Result0(K_SET, sym, base, cond)"
        ),
        "refinement": "build models the constructor reduction `condition is S.true -> "
                      "base_set`: a real reduction that returned a DIFFERENT base set "
                      "would change which domain passes through. The F2P requires the "
                      "collapsed-to-true result to be the actual (replacement-applied) "
                      "base domain (Interval(-oo,0) / imageset(...asin(1/3)...)); a "
                      "different base would NOT resolve.",
        "rationale": "REJECT comes from postcondition `cond==COND_TRUE and "
                     "base_kind!=BASE_EMPTY => base==base`: this returns base==0 != base "
                     "for any base!=0. If it verified => SPEC-TOO-WEAK (the keyed-base "
                     "clause hollow).",
    },
    {
        # The empty-base-domain collapse dropped: an already-empty base domain
        # would yield a non-empty result. Correct on every non-empty base domain;
        # wrong exactly when the (replacement-applied) base domain is empty.
        "id": "weak-build-drop-empty-base",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _build(
            "    # PARTIAL-DOMAIN: the empty-base-domain collapse is dropped, so an\n"
            "    # already-empty base domain is treated like any other and yields the\n"
            "    # base domain / a restricted object instead of the empty domain.\n"
            "    if cond == COND_FALSE:\n"
            "        return Result0(K_EMPTY, sym, base, cond)\n"
            "    elif cond == COND_TRUE:\n"
            "        return Result0(K_BASE, sym, base, cond)\n"
            "    elif base_kind == BASE_LISTED:\n"
            "        return Result0(listed_kind, sym, listed_base, cond)\n"
            "    elif base_kind == BASE_MERGED:\n"
            "        if merged_sym == MERGE_REFUSED:\n"
            "            return Result0(K_REFUSED, merged_sym, merged_base, cond)\n"
            "        return Result0(K_SET, merged_sym, merged_base, cond)\n"
            "    else:\n"
            "        return Result0(K_SET, sym, base, cond)"
        ),
        "refinement": "the real constructor collapses an empty base domain to the empty "
                      "domain before any other reduction, and that branch is reachable by "
                      "an ordinary free-parameter replacement: "
                      "ConditionSet(x, x<y, Interval(0,y)).subs(y,-1) has the base domain "
                      "collapse to the empty domain while the predicate stays open, and "
                      "the real result is the empty domain. A real reduction lacking that "
                      "collapse would hand back a restricted object over an empty domain, "
                      "contradicting the constructor P2P tests => it would NOT resolve.",
        "rationale": "REJECT comes from postcondition `base_kind==BASE_EMPTY => "
                     "kind==K_EMPTY`: on an empty base domain with an open predicate this "
                     "returns K_SET. If it verified => SPEC-TOO-WEAK (the empty-base "
                     "collapse unpinned).",
    },
    {
        # The member-by-member decision over an explicitly listed base domain is
        # ignored: every listed base domain yields a restricted object over the
        # whole listing. Correct only when the folded outcome happens to be K_SET
        # over the full listing.
        "id": "weak-build-listed-ignore-members",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _build(
            "    if cond == COND_FALSE:\n"
            "        return Result0(K_EMPTY, sym, base, cond)\n"
            "    elif base_kind == BASE_EMPTY:\n"
            "        return Result0(K_EMPTY, sym, base, cond)\n"
            "    elif cond == COND_TRUE:\n"
            "        return Result0(K_BASE, sym, base, cond)\n"
            "    elif base_kind == BASE_MERGED:\n"
            "        if merged_sym == MERGE_REFUSED:\n"
            "            return Result0(K_REFUSED, merged_sym, merged_base, cond)\n"
            "        return Result0(K_SET, merged_sym, merged_base, cond)\n"
            "    else:\n"
            "        # PARTIAL-DOMAIN: ignore the member-by-member decision and keep the\n"
            "        # whole listing as a restricted object.\n"
            "        return Result0(K_SET, sym, base, cond)"
        ),
        "refinement": "over an explicit finite listing the real constructor decides the "
                      "predicate member by member: ConditionSet(x, Eq(x,y), {1,2,3})"
                      ".subs(y,2) really yields {2}, and ConditionSet(x, x<y, {1,2,3})"
                      ".subs(y,-1) really yields the empty domain. A real reduction that "
                      "kept the whole listing wrapped in a restricted object instead "
                      "would contradict the FiniteSet P2P tests => it would NOT resolve.",
        "rationale": "REJECT comes from postcondition `cond==COND_OPEN and "
                     "base_kind==BASE_LISTED => kind==listed_kind` (and base==listed_base "
                     "when non-empty): this returns K_SET over the full listing "
                     "regardless of the folded outcome. If it verified => SPEC-TOO-WEAK "
                     "(the member-by-member reduction unpinned).",
    },
    {
        # The MERGE keyed on the OUTER bound variable: the shape in which the
        # real constructor does NOT carry the bound variable over. Correct on
        # every other base-domain shape; wrong exactly on the merge.
        "id": "weak-build-merged-keeps-outer-sym",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _build(
            "    if cond == COND_FALSE:\n"
            "        return Result0(K_EMPTY, sym, base, cond)\n"
            "    elif base_kind == BASE_EMPTY:\n"
            "        return Result0(K_EMPTY, sym, base, cond)\n"
            "    elif cond == COND_TRUE:\n"
            "        return Result0(K_BASE, sym, base, cond)\n"
            "    elif base_kind == BASE_LISTED:\n"
            "        return Result0(listed_kind, sym, listed_base, cond)\n"
            "    elif base_kind == BASE_MERGED:\n"
            "        if merged_sym == MERGE_REFUSED:\n"
            "            return Result0(K_REFUSED, merged_sym, merged_base, cond)\n"
            "        # PARTIAL-DOMAIN: keep the OUTER bound variable across the merge\n"
            "        # (correct only when the merge happens to settle on it).\n"
            "        return Result0(K_SET, sym, merged_base, cond)\n"
            "    else:\n"
            "        return Result0(K_SET, sym, base, cond)"
        ),
        "refinement": "the real constructor, handed a base domain that is itself a "
                      "restricted object, unpacks it and may adopt the inner bound "
                      "variable or mint a fresh internal name; it keeps the outer one "
                      "only when the two predicates leave it free. A real reduction that "
                      "always kept the outer variable would rename nothing and would "
                      "return a set whose members are indexed by the wrong variable: "
                      "ConditionSet(x, x<5, Union(Interval(0,y), ConditionSet(z, x+z>0, "
                      "Reals))).subs(y,-1) really yields ConditionSet(z, (z<5) & (x+z>0), "
                      "Reals), keyed on z, and the constructor P2P tests on nested "
                      "ConditionSets check exactly that => it would NOT resolve.",
        "rationale": "REJECT comes from postcondition `cond==COND_OPEN and "
                     "base_kind==BASE_MERGED => sym==merged_sym`: this returns sym==sym, "
                     "which differs whenever the merge settles on the inner variable or "
                     "a fresh name. If it verified => SPEC-TOO-WEAK (the one shape in "
                     "which the bound variable legitimately changes would be unpinned, "
                     "and a rival could rename it arbitrarily).",
    },
    {
        # The MERGE left standing over the OUTER base domain instead of the inner
        # one: the merged object must range over the inner restricted object's
        # own base domain.
        "id": "weak-build-merged-keeps-outer-base",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _build(
            "    if cond == COND_FALSE:\n"
            "        return Result0(K_EMPTY, sym, base, cond)\n"
            "    elif base_kind == BASE_EMPTY:\n"
            "        return Result0(K_EMPTY, sym, base, cond)\n"
            "    elif cond == COND_TRUE:\n"
            "        return Result0(K_BASE, sym, base, cond)\n"
            "    elif base_kind == BASE_LISTED:\n"
            "        return Result0(listed_kind, sym, listed_base, cond)\n"
            "    elif base_kind == BASE_MERGED:\n"
            "        if merged_sym == MERGE_REFUSED:\n"
            "            return Result0(K_REFUSED, merged_sym, merged_base, cond)\n"
            "        # PARTIAL-DOMAIN: merge the bound variable but leave the object\n"
            "        # standing over the OUTER base domain (the restricted object\n"
            "        # itself) instead of the INNER base domain it unpacks to.\n"
            "        return Result0(K_SET, merged_sym, base, cond)\n"
            "    else:\n"
            "        return Result0(K_SET, sym, base, cond)"
        ),
        "refinement": "the real constructor unpacks the inner restricted object into "
                      "(inner variable, inner predicate, INNER base domain) and builds "
                      "the merged object over that inner base domain; keeping the outer "
                      "one would nest a restricted object inside its own base domain and "
                      "never flatten, so ConditionSet(x, x<5, Union(Interval(0,y), "
                      "ConditionSet(z, x+z>0, Reals))).subs(y,-1) would not equal "
                      "ConditionSet(z, (z<5) & (x+z>0), Reals) => it would NOT resolve.",
        "rationale": "REJECT comes from postcondition `cond==COND_OPEN and "
                     "base_kind==BASE_MERGED => base==merged_base`: this returns "
                     "base==base (the un-unpacked restricted object). If it verified => "
                     "SPEC-TOO-WEAK (the merge could leave the object standing over the "
                     "wrong domain).",
    },
    {
        # The restricted object surviving a listed base domain's member-by-member
        # decision is keyed on a fixed wrong constant instead of the bound
        # variable — the same bound-variable-capture family as the headline bug,
        # on the listed sub-domain.
        "id": "weak-build-listed-wrong-sym",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _build(
            "    if cond == COND_FALSE:\n"
            "        return Result0(K_EMPTY, sym, base, cond)\n"
            "    elif base_kind == BASE_EMPTY:\n"
            "        return Result0(K_EMPTY, sym, base, cond)\n"
            "    elif cond == COND_TRUE:\n"
            "        return Result0(K_BASE, sym, base, cond)\n"
            "    elif base_kind == BASE_LISTED:\n"
            "        # PARTIAL-DOMAIN: the surviving restricted object is keyed on a\n"
            "        # fixed constant 0 rather than the given bound variable.\n"
            "        return Result0(listed_kind, 0, listed_base, cond)\n"
            "    else:\n"
            "        return Result0(K_SET, sym, base, cond)"
        ),
        "refinement": "the real constructor gathers the undecided members of a listing "
                      "into a restricted object keyed on the SAME bound variable: "
                      "ConditionSet(x, x<y, {1,2,z}).subs(y,-1) really yields "
                      "ConditionSet(x, x<-1, {z}) — bound variable still x. A real "
                      "reduction keying that object on something else would reintroduce "
                      "exactly the bound-variable capture the issue reports, on the "
                      "finite-base path => it would NOT resolve.",
        "rationale": "REJECT comes from postcondition `cond==COND_OPEN and "
                     "base_kind==BASE_LISTED and listed_kind==K_SET => sym==sym`: this "
                     "returns sym==0 != sym for any sym!=0. If it verified => "
                     "SPEC-TOO-WEAK (bound-variable propagation unpinned on the listed "
                     "sub-domain).",
    },
]


# ===================================================================== #
# AXIOM LANE — no @ContractOnly axiom is consumed (meta.axioms == []); the
# canonical reduction (build) and the patched free-symbol branch
# (replace_free_parameter) are A-REFERENCE deep models. We persist the G-AX
# real-callee soundness check (axiom_check.py) as an axiom-soundness probe: run
# the REAL patched SymPy ConditionSet.__new__ / _eval_subs in-container (gold
# applied) and assert every observed (kind, bound symbol, base) matches the
# model's claims — the A-reference == real-callee obligation (PBT_PLAN §2.4 /
# §4 A-reference deep models). The probe embeds axiom_check.py's source (the
# runner mounts ONLY the probe at /work; axiom_check.py is NOT in-container) and
# imports only sympy + stdlib.
# ===================================================================== #

# Read the bundle's audited oracle on the HOST at load time and embed its source.
_AXIOM_CHECK_SRC = (Path(__file__).parent / "axiom_check.py").read_text()

AXIOM_TESTS = [
    {
        "id": "ax-ref-build-evalsubs-soundness",
        "axiom": "build / replace_free_parameter (A-reference deep models)",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,  # the A-reference describes POST-gold behaviour
        "probe": _AXIOM_CHECK_SRC,
        "rationale": "the deep models claim build(sym,cond,base,base_kind,...) == "
                     "ConditionSet.__new__'s reduction (false->empty, empty base->empty, "
                     "true->base, listed base->the member-by-member outcome, otherwise a "
                     "set keyed on sym) and replace_free_parameter == the patched "
                     "_eval_subs free-symbol branch (rebuilt on the ORIGINAL self.sym; a "
                     "collapsed-to-true predicate yields the base domain, never a set on "
                     "`new`). This runs the REAL patched ConditionSet over every base-"
                     "domain shape x {false,true,open} (§1) — including a base domain "
                     "that collapses to empty and explicitly listed base domains that "
                     "sift — and the _eval_subs cases incl. the issue-17341 imageset/asin "
                     "input and the F2P n<x->true regression (§2), asserting "
                     "kind/bound-symbol/base agree and the headline .dummy_eq. Exit 0 iff "
                     "every observation meets the model's claims; any divergence is "
                     "AXIOM-UNSOUND for the A-reference.",
    },
]
