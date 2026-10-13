# properties.py — PBT falsification battery for django__django-11749. NOT a
# Nagini module; a record of adversarial cases the runner (swebench_nagini.pbt)
# executes and stamps with RESULT. Each SPEC_TESTS case is a full model.py
# variant that shares the FROZEN spec exactly (markers.same_spec) and edits ONLY
# inside the # impl-start/# impl-end region; the runner re-runs the Nagini
# verifier on the host and checks the verify/reject outcome against `expect`.
#
# Defended surface of this instance (read model.py + refinement.md + mapping.md):
#   select_forwarded(actions: List[int]) -> List[int]
#     Requires(Acc(list_pred(actions), 1 / 2))      # READ-ONLY input (half perm)
#     Requires(MustTerminate(len(actions) + 2))     # TOTAL correctness obligation

#     Ensures(Acc(list_pred(actions), 1 / 2))       # returns the borrowed half
#     Ensures(Acc(list_pred(Result())))             # full perm on the result
#     Ensures(ToSeq(Result()) == forwarded_seq(ToSeq(actions)))   # LOAD-BEARING
#   where (all @Pure, fully unfolded over the input — NOT opaque oracles):
#     supplied(a)        = (a % 2 == 1)             # bit0: caller supplied it
#     mandatory(a)       = ((a // 2) % 2 == 1)      # bit1: individually mandatory
#     in_mandated_set(a) = ((a // 4) % 2 == 1)      # bit2: in a mandated alt set
#     forward(a)         = supplied(a) and (mandatory(a) or in_mandated_set(a))
#     forwarded_seq(s)   = order-preserving sub-list of s under `forward`
#                          (front-recursive: one auto-unfold per declared option)
#
# What the spec defends (the single load-bearing clause):
#   ToSeq(Result()) == forwarded_seq(ToSeq(actions)) pins the output to the EXACT
#   order-preserving filter of the declared options under
#   forward = supplied AND (mandatory OR in_mandated_set). This is precisely the
#   post-patch comprehension predicate
#   `opt.dest in options and (opt.required or opt in mutually_exclusive_required_options)`
#   (refinement.md A5/A6). Any impl that forwards a different set, in a different
#   order, or whose filter predicate differs on any of the 8 bit-combinations of
#   (supplied, mandatory, in_mandated_set) cannot satisfy the loop invariant
#   ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i)) and is rejected.
#
# The DISCRIMINATING content of the gold change (refinement.md §A, G-DIFF): an
# option that is `supplied AND in_mandated_set AND NOT mandatory` MUST be
# forwarded. The pre-patch predicate `opt.required and opt.dest in options`
# (== model_prepatch.py's `mandatory(a) and supplied(a)`) DROPS exactly that
# case and FAILS the F2P test_mutually_exclusive_group_required_options
# (--foo-id/--foo-name in a required=True mutually-exclusive group; each member
# required=False). That is the headline partial-domain attack below.
#
# Permission: `actions` is held at HALF permission Acc(list_pred(actions), 1/2),
# i.e. READ-ONLY. The frame-mutation probe (writing to `actions`) is MANDATORY
# and is the #1 weakness class — see uniq-frame-mutate.
#
# Ungrounded-oracle echo (N/A here, see assessment): forwarded_seq is GROUNDED in
# the input — it is a @Pure function of `actions`, fully unfolded, with no opaque
# @ContractOnly answer key. "Echoing the oracle" therefore just computes the
# CORRECT answer (there is no WRONG value to echo). The honest cheapest grounded
# impl (the backward fold against forward(a)) is given as pos-control-helper.
#
# TERMINATION: the spec carries Requires(MustTerminate(len(actions) + 2)), so what
# the verifier proves is TOTAL correctness, not partial. Every accept-lane rival
# below must therefore discharge its own termination proof: each spliced loop
# carries Invariant(MustTerminate(<remaining iterations>)) as the last invariant in
# its region. The measure is the backward counter `i` (+1, since the final
# iteration has 0 remaining and MustTerminate(0) is unsatisfiable). The level is
# input-dependent rather than a constant because the admissibility witness
# SELF-CALLS select_forwarded: a constant level cannot be strictly greater than
# itself, so the callee would have no room beneath the caller. len(actions) + 2
# gives it that room under the witness's guard.
#
# No @ContractOnly axioms and no deep-model references (meta.axioms == []), so the
# axiom lane is vacuous: AXIOM_TESTS = [].  (refinement.md §B, mapping.md §3.)
from pathlib import Path

INSTANCE = "django__django-11749"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Exact frozen impl region (verbatim from model.py). We only ever replace text
# BETWEEN # impl-start / # impl-end, guaranteeing same_spec. The `invariants`
# region is NESTED inside the impl region (markers.spec_view elides it), so the
# loop, invariants, asserts, and filter predicate are all free to reshape while
# the frozen spec (pure/pre/post) is never touched.
# ---------------------------------------------------------------------------
_IMPL_OLD = """    # impl-start
    result = []  # type: List[int]
    i = len(actions)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(actions), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(actions))
        Invariant(ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        a = actions[i - 1]
        Assert(ToSeq(actions).drop(i - 1)[0] == a)
        Assert(ToSeq(actions).drop(i - 1).drop(1) == ToSeq(actions).drop(i))
        if supplied(a) and (mandatory(a) or in_mandated_set(a)):
            result = [a] + result
        i = i - 1
    return result
    # impl-end"""

assert _IMPL_OLD in _BASE and _BASE.count(_IMPL_OLD) == 1


# ===========================================================================
# POSITIVE CONTROLS (soundness) — structurally-DIFFERENT but CORRECT impls that
# MUST verify (else SPEC-TOO-STRONG). Both keep the gold backward fold direction
# (front-recursive forwarded_seq is built over s[0] + forwarded_seq(s.drop(1)),
# so a forward-append control would need an f(a+b)==f(a)+f(b) lemma the verifier
# cannot auto-discharge — pilot pitfall #3 — and is deliberately avoided). They
# keep the two framing asserts verbatim (pilot pitfall #2) and reshape only the
# filter expression / a local-variable binding.
# ===========================================================================

# pos-control-helper: replace the INLINED disjunction `supplied(a) and (mandatory
# (a) or in_mandated_set(a))` with the @Pure helper `forward(a)`, whose body is
# literally that same expression (model.py forward()). This is the honest cheapest
# grounded impl: it consults the spec's own forwarding predicate. Same fold, same
# asserts, same invariants. Must verify (else SPEC-TOO-STRONG, and also the
# grounded-oracle positive control standing in for the N/A ungrounded-echo class).
_POS_HELPER = """    # impl-start
    result = []  # type: List[int]
    i = len(actions)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(actions), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(actions))
        Invariant(ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        a = actions[i - 1]
        Assert(ToSeq(actions).drop(i - 1)[0] == a)
        Assert(ToSeq(actions).drop(i - 1).drop(1) == ToSeq(actions).drop(i))
        if forward(a):
            result = [a] + result
        i = i - 1
    return result
    # impl-end"""

# pos-control-local: a local-variable reshape — bind the per-action value `a` and
# the forwarding decision into a named boolean local `keep` before the prepend,
# and bind the prepended sequence into a typed local. Same backward fold, same
# framing asserts, same invariants; only the executable shape (extra locals)
# changes. Must verify (else SPEC-TOO-STRONG).
_POS_LOCAL = """    # impl-start
    result = []  # type: List[int]
    i = len(actions)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(actions), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(actions))
        Invariant(ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        a = actions[i - 1]
        Assert(ToSeq(actions).drop(i - 1)[0] == a)
        Assert(ToSeq(actions).drop(i - 1).drop(1) == ToSeq(actions).drop(i))
        keep = supplied(a) and (mandatory(a) or in_mandated_set(a))  # type: bool
        if keep:
            prepended = [a] + result  # type: List[int]
            result = prepended
        i = i - 1
    return result
    # impl-end"""


# ===========================================================================
# ADMISSIBILITY (verify) — confirm the Requires admits a normal F2P-shaped input
# (else PRECOND-TOO-STRONG). We CANNOT add a separate top-level caller (a new
# module-level def changes the projected spec view and breaks same_spec). Instead
# we inject the admissibility witness INSIDE the impl region (elided from the spec
# view): construct a concrete F2P-shaped declared-options list — encoding a
# `supplied AND in_mandated_set AND NOT mandatory` option (value 5 = bits 101:
# supplied=1, mandatory=0, in_mandated_set=1), exactly the
# test_mutually_exclusive_group_required_options configuration — and SELF-CALL
# select_forwarded on it (its Requires Acc(list_pred(_,1/2)) is establishable from
# the fresh list's full list_pred). Then run the gold body unchanged. If the
# precondition could not be established for this legitimate input the self-call
# would fail => PRECOND-TOO-STRONG.
# ===========================================================================
_ADMISS = """    # impl-start
    # --- admissibility witness for an F2P-shaped input (elided from spec view) ---
    # The self-call is GUARDED on len(actions) >= 2 so the recursion is
    # well-founded under the termination obligation: the callee's level is
    # len(sample) + 2 == 3, and the guard forces the caller's level
    # len(actions) + 2 >= 4 > 3, giving the callee the room it needs. An
    # UNGUARDED self-call is unbounded recursion (level len(actions) + 2 calling
    # itself at the same level) and is correctly rejected for an obligation leak
    # — that is a defect in the witness, not a too-strong precondition. The guard
    # is feasible (Assert(False) inside it fails), so the witness still bites.
    if len(actions) >= 2:
        sample = [5]  # type: List[int]
        # value 5 = bits 101: supplied=1, mandatory=0, in_mandated_set=1 — the
        # required-mutually-exclusive-group member the F2P exercises. The
        # function's Requires Acc(list_pred(sample), 1/2) is establishable from
        # the fresh list's full list_pred, so the self-call is well-formed.
        echoed = select_forwarded(sample)
        # this option IS forwarded, so the result echoes it back:
        Assert(ToSeq(echoed) == forwarded_seq(ToSeq(sample)))
    # --- end admissibility witness; the real impl follows unchanged ---
    result = []  # type: List[int]
    i = len(actions)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(actions), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(actions))
        Invariant(ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        a = actions[i - 1]
        Assert(ToSeq(actions).drop(i - 1)[0] == a)
        Assert(ToSeq(actions).drop(i - 1).drop(1) == ToSeq(actions).drop(i))
        if supplied(a) and (mandatory(a) or in_mandated_set(a)):
            result = [a] + result
        i = i - 1
    return result
    # impl-end"""


# ===========================================================================
# FRAME-MUTATION (uniqueness / reject) — MANDATORY: `actions` is read-only
# Acc(list_pred(actions), 1/2). A rival WRITES to the half-permission input. The
# write needs FULL list_pred(actions); only 1/2 is granted by Requires, so this
# must REJECT for INSUFFICIENT PERMISSION (not a value mismatch) — that is the
# whole point of the 1/2 perm. The gold value invariants/asserts are kept
# verbatim so the rejection is attributable solely to the write. (The invariant's
# Acc is bumped to FULL to expose that the attacker would need write permission
# the caller never granted; the rejection lands at the `actions.append` for
# insufficient permission against the 1/2-perm Requires.)
# ===========================================================================
_FRAME_MUTATE = """    # impl-start
    actions.append(0)
    result = []  # type: List[int]
    i = len(actions)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(actions)))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(actions))
        Invariant(ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        a = actions[i - 1]
        if supplied(a) and (mandatory(a) or in_mandated_set(a)):
            result = [a] + result
        i = i - 1
    return result
    # impl-end"""


# ===========================================================================
# PARTIAL-DOMAIN (uniqueness / reject) — rivals correct on most of the input
# domain but diverging on a specific sub-domain. Each MUST be rejected; a
# verifying rival is a real verify-but-not-resolve break (SPEC-TOO-WEAK).
# ===========================================================================

# uniq-prepatch-predicate: THE BUG. Filter on `mandatory(a) and supplied(a)`,
# DROPPING the `or in_mandated_set` disjunct — this is model_prepatch.py / the
# pre-patch predicate `opt.required and opt.dest in options` verbatim. It diverges
# exactly on the sub-domain `supplied AND in_mandated_set AND NOT mandatory`
# (option encoding 5). Must be rejected by the loop invariant
# ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i)) (forwarded_seq forwards
# that option; the impl does not).
_UNIQ_PREPATCH = """    # impl-start
    result = []  # type: List[int]
    i = len(actions)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(actions), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(actions))
        Invariant(ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        a = actions[i - 1]
        Assert(ToSeq(actions).drop(i - 1)[0] == a)
        Assert(ToSeq(actions).drop(i - 1).drop(1) == ToSeq(actions).drop(i))
        if mandatory(a) and supplied(a):
            result = [a] + result
        i = i - 1
    return result
    # impl-end"""

# uniq-over-forward: forward EVERY supplied option (drop the obligation conjunct
# entirely; filter on `supplied(a)` alone). Over-forwards on the sub-domain
# `supplied AND NOT mandatory AND NOT in_mandated_set` (option encoding 1) — an
# optional caller-supplied argument that argparse does NOT require. Must be
# rejected by the loop invariant (forwarded_seq does NOT include such an option;
# the impl appends it).
_UNIQ_OVERFORWARD = """    # impl-start
    result = []  # type: List[int]
    i = len(actions)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(actions), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(actions))
        Invariant(ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        a = actions[i - 1]
        Assert(ToSeq(actions).drop(i - 1)[0] == a)
        Assert(ToSeq(actions).drop(i - 1).drop(1) == ToSeq(actions).drop(i))
        if supplied(a):
            result = [a] + result
        i = i - 1
    return result
    # impl-end"""

# uniq-drop-supplied: forward on obligation WITHOUT requiring the caller supplied
# it (filter on `mandatory(a) or in_mandated_set(a)`, dropping `supplied(a)`).
# Diverges on the sub-domain `(mandatory OR in_mandated_set) AND NOT supplied`
# (e.g. option encoding 2 = mandatory, not supplied): the gold predicate never
# forwards an unsupplied option (arg_options[opt.dest] would KeyError; the
# pre-patch and post-patch code both gate on `opt.dest in options`). Must be
# rejected by the loop invariant.
_UNIQ_DROP_SUPPLIED = """    # impl-start
    result = []  # type: List[int]
    i = len(actions)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(actions), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(actions))
        Invariant(ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        a = actions[i - 1]
        Assert(ToSeq(actions).drop(i - 1)[0] == a)
        Assert(ToSeq(actions).drop(i - 1).drop(1) == ToSeq(actions).drop(i))
        if mandatory(a) or in_mandated_set(a):
            result = [a] + result
        i = i - 1
    return result
    # impl-end"""

# uniq-drop-last: build the forwarded set over all options EXCEPT the last
# declared one (stop the backward fold at i == 1, never consider actions[0]).
# Diverges precisely when the FIRST-declared option is forwardable: that option
# is dropped from the result. Faithful real patch: a comprehension `for opt in
# parser_actions[1:]` that skips the first declared action — if that action is a
# required mutually-exclusive member the caller supplied, its value is never
# threaded through and the F2P fails. Rejected by the loop invariant at i == 0
# (the invariant ToSeq(result) == forwarded_seq(ToSeq(actions).drop(0)) cannot be
# re-established when actions[0] is forwardable but skipped).
_UNIQ_DROP_LAST = """    # impl-start
    result = []  # type: List[int]
    i = len(actions)
    while i > 1:
        # invariants-start
        Invariant(Acc(list_pred(actions), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(1 <= i and i <= len(actions))
        Invariant(ToSeq(result) == forwarded_seq(ToSeq(actions).drop(i)))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        a = actions[i - 1]
        Assert(ToSeq(actions).drop(i - 1)[0] == a)
        Assert(ToSeq(actions).drop(i - 1).drop(1) == ToSeq(actions).drop(i))
        if supplied(a) and (mandatory(a) or in_mandated_set(a)):
            result = [a] + result
        i = i - 1
    return result
    # impl-end"""

# uniq-empty: the trivial cheapest wrong impl — always return the empty list.
# Forwards NOTHING, so on any input with a forwardable option the result diverges
# from forwarded_seq. Faithful patch: deleting the comprehension entirely (no
# required option ever threaded through) — the F2P (and pre-existing required-arg
# behaviour, P2P) fails. Supporting near-miss; rejected by the postcondition
# ToSeq(Result()) == forwarded_seq(ToSeq(actions)) whenever forwarded_seq is
# non-empty. Uses a typed local then `return empty` (pilot pitfall #1: never a
# bare typed `return []`).
_UNIQ_EMPTY = """    # impl-start
    empty = []  # type: List[int]
    return empty
    # impl-end"""

# uniq-identity: return the WHOLE declared list unfiltered (no selection at all).
# Diverges on any input containing a non-forwardable option. Faithful patch: drop
# the `if <pred>` guard and forward every declared option's value — argparse would
# receive values for unsupplied/optional options (KeyError on arg_options[dest] /
# spurious required-arg threading), breaking the command-call P2P tests. Rejected
# by the postcondition (the identity copy is not the forwarded_seq filter unless
# every option happens to be forwardable). Supporting near-miss carrying a
# real refinement. Keeps the per-element framing asserts so the rejection is a
# value mismatch, not a proof-trigger gap.
_UNIQ_IDENTITY = """    # impl-start
    result = []  # type: List[int]
    i = len(actions)
    while i > 0:
        # invariants-start
        Invariant(Acc(list_pred(actions), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(actions))
        Invariant(ToSeq(result) == ToSeq(actions).drop(i))
        Invariant(MustTerminate(i + 1))
        # invariants-end
        a = actions[i - 1]
        Assert(ToSeq(actions).drop(i - 1)[0] == a)
        Assert(ToSeq(actions).drop(i - 1).drop(1) == ToSeq(actions).drop(i))
        result = [a] + result
        i = i - 1
    return result
    # impl-end"""


SPEC_TESTS = [
    # ---- positive controls (must verify; else SPEC-TOO-STRONG) ----
    {
        "id": "pos-control-helper",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_HELPER),
        "rationale": "structurally-different CORRECT impl that replaces the inlined "
                     "disjunction `supplied(a) and (mandatory(a) or in_mandated_set("
                     "a))` with the @Pure helper `forward(a)` whose body is literally "
                     "that same expression. Same backward fold, same invariants, same "
                     "framing asserts — no new lemma (pilot pitfalls #2/#3 avoided). "
                     "Also the honest grounded-oracle positive control: forwarded_seq "
                     "is a @Pure fn of the input (not an opaque answer key), so "
                     "consulting forward(a) computes the CORRECT answer. If a faithful "
                     "correct impl cannot verify => SPEC-TOO-STRONG.",
    },
    {
        "id": "pos-control-local",
        "kind": "soundness",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _POS_LOCAL),
        "rationale": "local-variable reshape: bind the forwarding decision into a "
                     "named boolean local `keep` and the prepended sequence into a "
                     "typed local before assigning. Same backward fold direction, same "
                     "invariants and framing asserts; only the executable shape changes. "
                     "If it cannot verify => SPEC-TOO-STRONG.",
    },

    # ---- admissibility (must verify; else PRECOND-TOO-STRONG) ----
    {
        "id": "admiss-f2p-shaped-input",
        "kind": "admissibility",
        "expect": "verify",
        "module": _swap(_BASE, _IMPL_OLD, _ADMISS),
        "rationale": "an admissibility witness injected INSIDE the impl region (elided "
                     "from the spec view, so same_spec holds) builds the concrete "
                     "F2P-shaped declared-options list [5] (bits 101: supplied=1, "
                     "mandatory=0, in_mandated_set=1 — the required-mutually-exclusive "
                     "group member the F2P test constructs) and SELF-CALLS "
                     "select_forwarded on it; its Requires Acc(list_pred(_,1/2)) is "
                     "establishable from the fresh list's full list_pred. The real impl "
                     "then runs unchanged. If the precondition could not be established "
                     "for this legitimate input the self-call fails => PRECOND-TOO-STRONG.",
    },

    # ---- frame-mutation (MANDATORY: actions is Acc(...,1/2) read-only) ----
    {
        "id": "uniq-frame-mutate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _FRAME_MUTATE),
        "refinement": "writing to the declared-options list (`actions.append(0)`) "
                      "corresponds to a patch that MUTATES parser_actions (the parser's "
                      "live action list) while computing the forwarded set — a destructive "
                      "side effect on the shared parser the gold patch never performs "
                      "(the comprehension only READS parser_actions). Such a patch would "
                      "corrupt the parser's declared options before parser.parse_args, "
                      "breaking the F2P/P2P command-call tests. The model exposes the "
                      "illegitimacy structurally: actions is borrowed at 1/2 permission, "
                      "so a write is forbidden.",
        "rationale": "rejected for INSUFFICIENT PERMISSION: actions is held at "
                     "Acc(list_pred(actions), 1/2) (read-only); appending requires FULL "
                     "list_pred(actions), which the Requires never grants. The rejection "
                     "is attributable to the write (the gold value invariants are kept), "
                     "NOT to a value mismatch — this is the #1 weakness class a byte "
                     "fuzzer never finds.",
    },

    # ---- partial-domain (must reject; else SPEC-TOO-WEAK) ----
    {
        "id": "uniq-prepatch-predicate",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_PREPATCH),
        "refinement": "this IS the pre-patch predicate `opt.required and opt.dest in "
                      "options` (== model_prepatch.py: filter on `mandatory(a) and "
                      "supplied(a)`, dropping the `or in_mandated_set` disjunct). It "
                      "fails to forward an option that is supplied AND in a required "
                      "mutually-exclusive group AND not itself individually required — "
                      "exactly the configuration the sole F2P "
                      "test_mutually_exclusive_group_required_options constructs "
                      "(--foo-id/--foo-name in add_mutually_exclusive_group(required="
                      "True), each member required=False). Its faithful real patch is "
                      "the un-patched code, which does NOT resolve the F2P (G-DIFF).",
        "rationale": "rejected by the loop invariant ToSeq(result) == forwarded_seq("
                     "ToSeq(actions).drop(i)): forwarded_seq forwards an option with "
                     "supplied AND in_mandated_set AND NOT mandatory (encoding 5); this "
                     "impl never appends it, so result diverges from forwarded_seq and "
                     "the invariant cannot be re-established.",
    },
    {
        "id": "uniq-over-forward",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_OVERFORWARD),
        "refinement": "forwarding EVERY supplied option (filter on `opt.dest in "
                      "options` alone, dropping `(opt.required or opt in mutually_"
                      "exclusive_required_options)`) over-threads optional caller-"
                      "supplied arguments that argparse does not require. The faithful "
                      "patch would push values for non-required options into "
                      "parse_args, changing what parser.parse_args sees and the computed "
                      "defaults — regressing the command-call P2P tests that pass "
                      "optional kwargs (e.g. test_call_command_option_parsing). It does "
                      "NOT match the gold forwarded set.",
        "rationale": "rejected by the loop invariant: forwarded_seq excludes an option "
                     "with supplied AND NOT mandatory AND NOT in_mandated_set (encoding "
                     "1); this impl appends it, so result has an extra element vs "
                     "forwarded_seq and the invariant fails.",
    },
    {
        "id": "uniq-drop-supplied",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DROP_SUPPLIED),
        "refinement": "forwarding on obligation WITHOUT the `opt.dest in options` guard "
                      "(filter on `opt.required or opt in mutually_exclusive_required_"
                      "options`) forwards a mandatory/required-group option the caller "
                      "did NOT supply. The faithful patch would evaluate "
                      "arg_options[opt.dest] for a dest absent from options -> KeyError "
                      "at call_command time, crashing legitimate calls (the gold code "
                      "gates on `opt.dest in options` precisely to avoid this). It does "
                      "NOT match the gold forwarded set.",
        "rationale": "rejected by the loop invariant: forwarded_seq excludes an option "
                     "with (mandatory OR in_mandated_set) AND NOT supplied (e.g. "
                     "encoding 2); this impl appends it, so result diverges from "
                     "forwarded_seq.",
    },
    {
        "id": "uniq-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_DROP_LAST),
        "refinement": "stopping the backward fold at i == 1 (never considering "
                      "actions[0]) corresponds to a comprehension `for opt in "
                      "parser_actions[1:]` that skips the FIRST declared action. If that "
                      "first action is a supplied required option, its value is never "
                      "threaded through and parser.parse_args raises 'required ... not "
                      "provided' — the F2P fails when --foo-id is the first declared "
                      "option. It does NOT match the gold forwarded set.",
        "rationale": "rejected by the loop invariant at i == 0: the final obligation "
                     "ToSeq(result) == forwarded_seq(ToSeq(actions).drop(0)) cannot be "
                     "re-established when actions[0] is forwardable but the loop never "
                     "prepended it.",
    },

    # ---- supporting mechanical near-misses (cheap; each carries a real refinement) ----
    {
        "id": "uniq-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_EMPTY),
        "refinement": "always returning the empty list corresponds to deleting the "
                      "`parse_args += [...]` comprehension entirely: NO required/"
                      "required-group option is ever threaded through, so "
                      "parser.parse_args raises for any missing required argument — both "
                      "the F2P and the pre-existing required-argument P2P tests fail. "
                      "Supporting near-miss for the headline selection weakness.",
        "rationale": "rejected by the postcondition ToSeq(Result()) == forwarded_seq("
                     "ToSeq(actions)): for any input with a forwardable option "
                     "forwarded_seq is non-empty, so the empty result cannot satisfy "
                     "the equality.",
    },
    {
        "id": "uniq-identity",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _swap(_BASE, _IMPL_OLD, _UNIQ_IDENTITY),
        "refinement": "returning the whole declared list unfiltered corresponds to "
                      "dropping the `if <pred>` guard and forwarding every option's "
                      "value: argparse receives values for unsupplied / optional options "
                      "(KeyError on arg_options[opt.dest] or spurious required-arg "
                      "threading), breaking the command-call P2P tests. It is the "
                      "forwarded_seq filter only if every option is forwardable, which "
                      "is not generally true. Supporting near-miss.",
        "rationale": "rejected by the postcondition: the identity copy equals "
                     "forwarded_seq(ToSeq(actions)) only when every option satisfies "
                     "`forward`; on an input with a non-forwardable option the result "
                     "has extra elements and the equality fails.",
    },
]


# ===========================================================================
# AXIOM LANE — vacuous. meta.json axioms == [] and deep_model_references == []:
# the change is pure selection logic over the declared options, modeled deeply
# (the spelled-out @Pure `forward` + `forwarded_seq` fold). There is NO
# @ContractOnly axiom and no A-reference deep model (refinement.md §B, mapping.md
# §3), so there is no real-callee soundness/containment obligation. AXIOM_TESTS
# is empty; the spec lane carries the entire battery.
# ===========================================================================
AXIOM_TESTS = []
