# properties.py — PBT falsification battery for sphinx-doc__sphinx-9258. NOT a Nagini
# module; a record of adversarially-reasoned cases the runner (swebench_nagini.pbt)
# executes and stamps RESULT onto. Spec cases are FULL model.py variants that share
# the FROZEN spec byte-for-byte (region surgery: ONLY the text strictly between the
# `split_render` function's `# impl-start` / `# impl-end` markers — which INCLUDES
# the nested invariants region — is edited; the axioms/pure/pre-/post-conditions
# regions and every OTHER function are never touched), checked by Nagini verify +
# markers.same_spec. Axiom cases probe the A-reference deep model `kinds` against the
# REAL stdlib `re.split` / `re.match` tokeniser (see AXIOM_TESTS at the bottom).
#
# Defended surface (read from model.py / refinement.md / mapping.md / instance.json):
#   split_render(target: List[int]) -> List[bool]
#   Models the gold change to PyXrefMixin.make_xrefs: the delimiter regex gained a
#   `\s*\|\s*` alternative, so a bar('|')-separated type spec is tokenised into one
#   cross-reference per named type, interleaved with literal separators. The output
#   is abstracted to its rendered-node KIND sequence: List[bool] with True=cross-
#   reference, False=literal separator. The F2P test_info_field_list_piped_type uses
#   `:type age: int | str` and asserts TWO separate pending_xref nodes ("int","str")
#   with a literal_emphasis " | " between them — i.e. kind sequence [True,False,True].
#
#   PRECONDITION (split_render):
#     (P1) Requires(Acc(list_pred(target), 1/2))         # HALF permission => READ-ONLY
#     (P2) Requires(MustTerminate(5))                     # must COMPLETE
#          -- and NOTHING else. There is NO domain clause: EVERY specification is
#          claimed, including the ones that mix the bar with a bracket, comma, `or`
#          or ellipsis separator, and the empty one. Whitespace throughout means the
#          FULL whitespace set (is_space), not just the ASCII space: an `or` padded by
#          TAB/NL/NBSP/IDEOGRAPHIC SPACE is a separator just as a space-padded one is.
#          A rival is therefore free to differ nowhere.
#   POSTCONDITION (split_render) — one framing pair + one LOAD-BEARING clause:
#     (Q1) Ensures(Acc(list_pred(target), 1/2))           # returns the read permission
#     (Q2) Ensures(Acc(list_pred(Result())))              # owns the produced list
#     (Q3) Ensures(ToSeq(Result()) == marks(ToSeq(target), 0))   # *** LOAD-BEARING ***
#   `marks` is the KIND PROJECTION of `rendered` (same case analysis over
#   `next_sep`/`sep_end`, kinds read and carried text ignored), so Q3 pins the ENTIRE
#   output: the NUMBER of nodes and the kind of each one, at every index, over every
#   specification. On a bar-only specification that is exactly True,False,True,...
#   (length 2*bars+1); on one that also uses a bracket, comma, `or` or ellipsis it is
#   the kind sequence of that tokenisation, and a leading separator makes the first
#   entry False. There is NO slack: any rival whose kind sequence differs at ANY
#   index, or in length, fails Q3 — on ANY input, not merely on a bar-only one.
#
# FRAME-MUTATION lane is MANDATORY: `target` is Acc(list_pred(target),1/2) (read-only,
#   P1/Q1). A rival that WRITES `target` must be REJECTED for INSUFFICIENT PERMISSION.
#   Byte-fuzzers never think to mutate the input; this is the project's #1 weakness
#   class. The real make_xrefs only READS `target` (it `re.split`s a str — strings are
#   immutable in Python and the function never rebinds/mutates the argument); any write
#   model would be infidelity, so the spec must forbid ANY store into `target`.
#
# UNGROUNDED-ORACLE-ECHO: N/A as a *wrong* echo. Q3 is pinned to
#   `marks(ToSeq(target), 0)` — GROUNDED entirely in the argument `target`. `marks` is
#   a @Pure front-recursive fold (over @Pure `next_sep`/`sep_end`) fully unfolded over
#   the separator structure of the input; there is NO @ContractOnly axiom, NO opaque
#   answer-key, NO exact marker the impl could echo. The pure region COMPUTES the kind
#   sequence from the input's separators, it does not assert an answer. So an impl that
#   "echoes the oracle" (`return materialize(marks(ToSeq(target),0))`) is the CORRECT impl
#   — there is no value an echo could carry that satisfies Q3 yet is wrong. The honest
#   substitute is the structurally-different positive control below, not a wrong echo.
#   See 'assessment'.
#
# VALUE-LEVEL DOUBLE-MASK / CONTROL-FLOW-EFFECT: there is NO hidden raise/return/
#   side-effect channel here — the function's only observable is its returned List[bool]
#   kind sequence, and Q3 pins that sequence index-by-index (no value proxy that could
#   drop a disagreeing index: equality of the WHOLE PSeq is required). The closest
#   analogue — mislabelling a separator node as a cross-reference (or vice-versa) —
#   is a VALUE divergence Q3 catches directly; it is exercised by the weak-all-xref
#   rival (every node emitted True, so the False separators are mislabelled). No
#   capability-token is needed because the kind itself is the discriminating value.
#
# PARTIAL-DOMAIN lane: heavily exercised. A rival can be correct on the no-bar
#   sub-domain (a single type name => [True]) yet diverge once a bar appears, and — now
#   that Q3 carries no domain clause — a rival can equally be correct on the bar-only
#   shape yet arbitrary on a specification that uses one of the other separators:
#     - weak-single-xref : never splits on the bar (the literal pre-patch behaviour,
#                          model_prepatch.py) => returns [True] for EVERY spec, wrong on
#                          any bar input incl. the F2P `int | str` (marks=[True,False,
#                          True]) and on the empty spec (marks is empty). Q3-rejected.
#     - weak-no-sep      : emits one True per stretch of text but NO False separators =>
#                          for `int | str` returns [True,True], length 2 (marks wants
#                          length 3, and entry[1] must be False). Q3-rejected.
#     - weak-all-xref    : emits the right NUMBER of nodes (2*bars+1 on a bar-only
#                          spec) but classifies the separators as cross-references too
#                          (all True) => for `int | str` returns [True,True,True];
#                          marks[1] is False. Q3-rejected (the value-double-mask
#                          analogue).
#     - weak-shape-guard : gold on the bar-only shape, arbitrary outside it — the
#                          sharpest rival against a kind-only obligation, since a
#                          bar-structure reading says nothing about a specification
#                          carrying a bracket, comma, `or` or ellipsis. It renders
#                          NOTHING there ([] instead of, for `list[int] | None`,
#                          marks=[True,False,True,False,False,True]). Q3-rejected
#                          BECAUSE Q3 carries no domain clause; under a bar-only
#                          obligation this rival would verify.
#   The same shape-guard family is exercised against the primary obligation as
#   atk-indomain-only (render_nodes).
#
#   SECOND DEFENDED SURFACE (the primary obligation):
#     render_nodes(target: List[int]) -> List[int]
#   Same modelled change, stated at full strength: the WHOLE rendered-node stream, not
#   just the node kinds. The result encodes the node list as, per node, that node's
#   carried code points followed by its kind marker (-1 cross-reference, -2 literal
#   separator), closed by -3; code points are non-negative, so no marker can be
#   confused with carried text and the encoding is injective.
#     PRECONDITION (render_nodes):
#       (R1) Requires(Acc(list_pred(target), 1/2))        # HALF permission => READ-ONLY
#       (R2) Requires(MustTerminate(5))                    # must COMPLETE
#       -- and NOTHING else. There is NO well_formed (or any other) domain clause: every
#          specification is claimed, including the ones that mix the bar with a bracket,
#          comma, `or` or ellipsis separator. A rival is therefore free to differ nowhere.
#     POSTCONDITION (render_nodes):
#       (S1) Ensures(Acc(list_pred(target), 1/2))
#       (S2) Ensures(Acc(list_pred(Result())))
#       (S3) Ensures(ToSeq(Result()) == rendered(ToSeq(target), 0))  # *** LOAD-BEARING ***
#   S3 pins the node COUNT, each node's KIND and each node's exact CARRIED TEXT — the
#   specification's own characters over that node's stretch, padding included, nothing
#   trimmed, re-padded, reordered, split or dropped. `rendered` is a @Pure front-
#   recursive fold over `next_sep`/`sep_end` (the separator vocabulary: padded bar,
#   bracket/comma with optional `or`, whitespace-bounded `or`, three-dot run), so there
#   is no opaque answer key: the obligation is COMPUTED from the argument.
#   The rivals below attack S3 in five distinct families — over-approximation (the node
#   text left unconstrained, or trimmed), partial-domain guard (correct only on the
#   bar-only shape), boundary token swap (a node's span off by one
#   token), oracle echo (the spec's own boundary oracle read at the wrong anchor), and
#   the freedom the encoding could have left (re-partitioning one node into two) — plus
#   the mandatory frame-mutation lane. Every one must be REJECTED.
#
# AXIOM lane: meta.axioms == [] (NO consumed @ContractOnly axiom). deep_model_references
#   has ONE A-reference: `kinds` models the real `re.split(delims)` + `filter(None,...)`
#   + per-piece `delims_re.match(...)` tokeniser with the gold patch's delimiter regex.
#   Per PBT_PLAN §2.4 / §4a an A-reference deep model is validated == the real callee on
#   every caller-reachable input. The real callee is the STDLIB `re` module (the exact
#   module the patched code calls) used with the patched pattern verbatim — so the
#   probes need NO repo import and run anywhere (Docker or host). The probes embed
#   faithful transcriptions of model.py's `kinds`/`first_bar`/`well_formed`/`no_other_sep`
#   folds (mirroring axiom_check.py / G-AX) and compare against the live re tokeniser:
#   axiom-soundness fuzzes kinds == real on the bar-only shape over the FULL
#   delimiter alphabet; axiom-containment confirms every specification of that shape
#   lands in the real tokeniser's domain and agrees. `kinds` is the bar-structure
#   reading; the folds the OBLIGATIONS are stated over — `rendered` and its kind
#   projection `marks`, both total — are validated against the real patched callee by
#   conformance_check.py / G-CONF, which drives the real function rather than the
#   stdlib tokeniser alone.
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-9258"
FLOAT_ENCODING = None  # meta.json float_encoding is null


_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# The frozen `split_render` impl region body, verbatim (everything strictly BETWEEN
# its `# impl-start` / `# impl-end` markers, INCLUDING the nested invariants region).
# Every spec variant _swap()s ONLY this block, so the edit never touches the spec
# (axioms/pure/pre-/post-conditions regions + the signatures + the OTHER functions
# next_sep_idx / sep_end_idx). same_spec is computed over the spec_view, which elides
# every impl region (and nested invariants), so swapping inside here is GUARANTEED
# same_spec.
_IMPL = """\
    result = []  # type: List[bool]
    n = len(target)
    i = 0
    while True:
        # invariants-start
        Invariant(Acc(list_pred(target), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(target))
        Invariant(n == len(ToSeq(target)))
        # telescoping fold: what is emitted, concatenated with the kinds of the
        # remaining suffix, is the whole kind sequence.
        Invariant(ToSeq(result) + marks(ToSeq(target), i) ==
                  marks(ToSeq(target), 0))
        # The condition is the constant `True`, so the bound comes from what the
        # break counts down: the loop leaves via `break` as soon as no separator
        # remains at or after i, and otherwise resumes at i = e, the end of a
        # separator that starts at j >= i and ends strictly after it (sep_end's
        # postcondition), so the scan index rises by at least one per pass and at
        # most n - i + 1 passes remain. It strictly decreases because only i
        # changes (n is a local fixed before the loop, pinned by
        # Invariant(n == len(target))), and it stays >= 1 because
        # Invariant(0 <= i and i <= n) holds on entry to every pass (so it never
        # reaches the unsatisfiable 0); the pass on which no separator remains is
        # the one that breaks.
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        # `+ 0` reads the boundary as the plain integer it is; see `sep_end`.
        j = next_sep_idx(target, i) + 0
        if j >= n:
            if i < n:
                Assert(marks(ToSeq(target), i) == PSeq(True))
                # the trailing text is one cross-reference.
                result.append(True)
            else:
                Assert(marks(ToSeq(target), i) == PSeq(True).drop(1))
            break
        e = sep_end_idx(target, j) + 0
        Assert(j < e and e <= n)
        if j > i:
            Assert(marks(ToSeq(target), i) ==
                   (PSeq(True) + PSeq(False)) + marks(ToSeq(target), e))
            # the text before the separator is one cross-reference.
            result.append(True)
        else:
            Assert(marks(ToSeq(target), i) ==
                   PSeq(False) + marks(ToSeq(target), e))
        # the separator itself is one literal node.
        result.append(False)
        i = e
    return result"""

assert _BASE.count(_IMPL) == 1, "split_render impl region drifted from expected text"


def _impl(new_body):
    """Full model.py variant with ONLY the split_render impl region body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-local-reshape: structurally DIFFERENT but behaviourally identical. The two
# constant booleans the loop appends are hoisted into named locals XREF=True and
# SEP=False and the separator end is bound to an extra alias the loop then resumes
# from — WITHOUT touching any proof obligation. EVERY gold Invariant is kept verbatim
# (the load-bearing telescoping
# `ToSeq(result)+marks(ToSeq(target),i)==marks(ToSeq(target),0)`, the four framing
# invariants), EVERY Assert is kept verbatim (the boundary assert and the three
# marks-unfold asserts), and the append order is unchanged. Only local-variable
# shapes change (directive 2/3: no dropped lemma/assert, no loop-direction flip, no
# forward-append against the front-recursive `marks` fold — the loop still
# front-consumes `i = e` exactly as gold). If it FAILS => SPEC-TOO-STRONG (a
# faithful, structurally-different correct impl is rejected).
_POS_RESHAPE = """\
    XREF = True
    SEP = False
    result = []  # type: List[bool]
    n = len(target)
    i = 0
    while True:
        # invariants-start
        Invariant(Acc(list_pred(target), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(target))
        Invariant(n == len(ToSeq(target)))
        # telescoping fold: what is emitted, concatenated with the kinds of the
        # remaining suffix, is the whole kind sequence.
        Invariant(ToSeq(result) + marks(ToSeq(target), i) ==
                  marks(ToSeq(target), 0))
        # The condition is the constant `True`, so the bound comes from what the
        # break counts down: the loop leaves via `break` as soon as no separator
        # remains at or after i, and otherwise resumes at i = e, the end of a
        # separator that starts at j >= i and ends strictly after it (sep_end's
        # postcondition), so the scan index rises by at least one per pass and at
        # most n - i + 1 passes remain. It strictly decreases because only i
        # changes (n is a local fixed before the loop, pinned by
        # Invariant(n == len(target))), and it stays >= 1 because
        # Invariant(0 <= i and i <= n) holds on entry to every pass (so it never
        # reaches the unsatisfiable 0); the pass on which no separator remains is
        # the one that breaks.
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        # `+ 0` reads the boundary as the plain integer it is; see `sep_end`.
        j = next_sep_idx(target, i) + 0
        if j >= n:
            if i < n:
                Assert(marks(ToSeq(target), i) == PSeq(True))
                # the trailing text is one cross-reference.
                result.append(XREF)
            else:
                Assert(marks(ToSeq(target), i) == PSeq(True).drop(1))
            break
        e = sep_end_idx(target, j) + 0
        end = e + 0
        Assert(j < end and end <= n)
        if j > i:
            Assert(marks(ToSeq(target), i) ==
                   (PSeq(True) + PSeq(False)) + marks(ToSeq(target), e))
            # the text before the separator is one cross-reference.
            result.append(XREF)
        else:
            Assert(marks(ToSeq(target), i) ==
                   PSeq(False) + marks(ToSeq(target), e))
        # the separator itself is one literal node.
        result.append(SEP)
        i = end
    return result"""
assert _POS_RESHAPE != _IMPL, "pos-local-reshape did not change the impl"


# admiss-reads: an admissibility positive control. The precondition is the
# half-permission Acc(list_pred(target),1/2) plus MustTerminate and NOTHING else, so
# EVERY specification is in-domain — the F2P `int | str`, the bracket/comma/`or`/
# ellipsis shapes, and the empty one. This control keeps the gold impl VERBATIM but
# FIRST asserts, under the half-permission alone and with no domain clause available
# to lean on, that the reads a renderer needs are admitted: the length always, and the
# first code point when non-empty. No write => no extra permission demand. If the
# precondition could not admit a legitimate union-type spec (e.g. the F2P `int | str`),
# this would fail => PRECOND-TOO-STRONG.
_ADMISS = (
    "    # Admissibility: no domain clause at all; the half-permission admits\n"
    "    # reading the length and the elements of ANY specification.\n"
    "    Assert(len(target) >= 0)\n"
    "    if len(target) > 0:\n"
    "        Assert(target[0] == target[0])   # read admitted under Acc(...,1/2)\n"
    + _IMPL
)


# ---------------------------------------------------------------------------
# FRAME-MUTATION RIVAL (MANDATORY — `target` is Acc(list_pred(target),1/2)).
# Must be REJECTED for INSUFFICIENT PERMISSION.
# ---------------------------------------------------------------------------

# frame-mut-write: keeps the gold body VERBATIM (so the rejection is attributable
# SOLELY to the added write, not to a value mismatch), then WRITES BACK into the
# read-only input: target[0] = target[0]. A no-op store, but a STORE — it demands
# FULL write permission on `target`, which the caller granted only at 1/2. The
# verifier must reject for insufficient permission. The store is placed FIRST, guarded
# by len>0 so it is reachable on the F2P input `int | str` (any non-empty spec takes
# the branch). (A real make_xrefs that mutated
# its `target` argument would be infidelity — the gold patch only `re.split`s an
# immutable str and never writes the argument; the spec must forbid ANY write.)
_FRAME_MUT = (
    "    if len(target) > 0:\n"
    "        # Frame violation: write back into the read-only (Acc(...,1/2)) input.\n"
    "        target[0] = target[0]\n"
    + _IMPL
)


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN / VALUE rivals — must be REJECTED
# (else SPEC-TOO-WEAK). Each shares the frozen spec exactly; only the impl changes.
# ---------------------------------------------------------------------------

# weak-single-xref: the literal PRE-PATCH behaviour (model_prepatch.py). It NEVER
# treats the bar as a split point, so it renders the whole spec as a SINGLE cross-
# reference and returns [True] for every input. The `single = [True]` is bound to a
# typed local first (directive 1: never `return []  # type:` on a bare literal).
_WEAK_SINGLE = """\
    single = [True]  # type: List[bool]
    return single"""

# weak-no-sep: emits one True per stretch of type-name text but OMITS the literal-
# separator nodes (never appends False). For `int | str` it returns [True,True]
# (length 2) where marks wants [True,False,True] (length 3). It keeps the gold scan
# and its framing invariants but carries no telescoping invariant, so the rejection
# lands on the postcondition: the omitted False makes the emitted sequence differ from
# `marks` at index 1 and in length.
_WEAK_NOSEP = """\
    result = []  # type: List[bool]
    n = len(target)
    i = 0
    while True:
        # invariants-start
        Invariant(Acc(list_pred(target), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(target))
        Invariant(n == len(ToSeq(target)))
        # this variant carries only the framing invariants and its own measure: at
        # most n - i + 1 passes remain, n is a local fixed before the loop, and the
        # scan index rises by at least one per pass (the separator starting at
        # j >= i ends strictly after it, and the loop resumes at that end), so the
        # bound strictly decreases; Invariant(0 <= i and i <= n) keeps it >= 1.
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        j = next_sep_idx(target, i) + 0
        if j >= n:
            if i < n:
                result.append(True)
            break
        e = sep_end_idx(target, j) + 0
        Assert(j < e and e <= n)
        if j > i:
            result.append(True)
        i = e
    return result"""

# weak-all-xref: VALUE-LEVEL double-mask. It emits the correct NUMBER of nodes
# (2*bars+1 on a bar-only spec) but classifies EVERY node — including the separators —
# as a cross-reference (all True). For `int | str` it returns [True,True,True] where
# marks is [True,False,True] (the separator at index 1 must be False). Length matches;
# the value at the separator indices is wrong.
_WEAK_ALLXREF = """\
    result = []  # type: List[bool]
    n = len(target)
    i = 0
    while True:
        # invariants-start
        Invariant(Acc(list_pred(target), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(target))
        Invariant(n == len(ToSeq(target)))
        # this variant carries only the framing invariants and its own measure: at
        # most n - i + 1 passes remain, n is a local fixed before the loop, and the
        # scan index rises by at least one per pass (the separator starting at
        # j >= i ends strictly after it, and the loop resumes at that end), so the
        # bound strictly decreases; Invariant(0 <= i and i <= n) keeps it >= 1.
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        j = next_sep_idx(target, i) + 0
        if j >= n:
            if i < n:
                result.append(True)
            break
        e = sep_end_idx(target, j) + 0
        Assert(j < e and e <= n)
        if j > i:
            result.append(True)
        result.append(True)
        i = e
    return result"""

# weak-shape-guard: the PARTIAL-DOMAIN rival stated against the kind sequence. The
# gold scan is kept VERBATIM, prefixed by a guard that returns the empty node list for
# every specification carrying one of the non-bar separator triggers (`no_other_sep`
# is False there: a bracket, comma, `or` or ellipsis). It is therefore gold on the
# bar-only shape and arbitrary on `list[int] | None`, `Dict[str, str]`, `str or int`,
# `Tuple[int, ...]` — the shapes a bar-structure reading has nothing to say about, and
# exactly the shapes the PASS_TO_PASS xref tests observe. Under a kind obligation
# restricted to the bar-only shape this rival VERIFIES while rendering nothing for most
# real type specifications; under the total `marks` clause it must be REJECTED.
_WEAK_SHAPEGUARD = (
    "    result = []  # type: List[bool]\n"
    "    n = len(target)\n"
    "    if not no_other_sep(ToSeq(target), 0):\n"
    "        # a specification carrying a bracket, comma, `or` or ellipsis: a\n"
    "        # bar-structure reading of the kinds says nothing here.\n"
    "        return result\n"
    + _IMPL.split("\n", 2)[2])


# ---------------------------------------------------------------------------
# The SECOND defended surface: `render_nodes` (the primary, full-strength
# obligation). Frozen impl region body, verbatim — everything strictly BETWEEN its
# `# impl-start` / `# impl-end` markers, INCLUDING the nested invariants region.
# Every variant below _swap()s ONLY inside this block, so the spec view (which
# elides every impl region and nested invariants region) is untouched and
# same_spec is GUARANTEED. The swap anchors are single lines, so each rival
# differs from gold in exactly the documented way and nothing else.
# ---------------------------------------------------------------------------

_RIMPL = """\
    out = []  # type: List[int]
    n = len(target)
    i = 0
    while True:
        # invariants-start
        Invariant(Acc(list_pred(target), 1 / 2))
        Invariant(Acc(list_pred(out)))
        Invariant(0 <= i and i <= n)
        Invariant(n == len(target))
        Invariant(n == len(ToSeq(target)))
        # telescoping fold: what has been emitted, concatenated with the node
        # stream of the remaining suffix, is the whole node stream.
        Invariant(ToSeq(out) + rendered(ToSeq(target), i) ==
                  rendered(ToSeq(target), 0))
        # The condition is the constant `True`, so the bound comes from what the
        # break counts down: the loop leaves via `break` as soon as no separator
        # remains at or after i, and otherwise resumes at i = e, the end of a
        # separator that starts at j >= i and ends strictly after it (sep_end's
        # postcondition), so the scan index rises by at least one per pass and at
        # most n - i + 1 passes remain. It strictly decreases because only i
        # changes (n is a local fixed before the loop, pinned by
        # Invariant(n == len(target))), and it stays >= 1 because
        # Invariant(0 <= i and i <= n) holds on entry to every pass (so it never
        # reaches the unsatisfiable 0); the pass on which no separator remains is
        # the one that breaks.
        Invariant(MustTerminate(n - i + 1))
        # invariants-end
        # `+ 0` reads the boundary as the plain integer it is; see `sep_end`.
        j = next_sep_idx(target, i) + 0
        if j >= n:
            if i < n:
                Assert(rendered(ToSeq(target), i) ==
                       (ToSeq(target).take(n).drop(i) + PSeq(-1)) + PSeq(-3))
                # the trailing text is one cross-reference carrying it verbatim.
                copy_span(out, target, i, n)
                out.append(-1)
            else:
                Assert(rendered(ToSeq(target), i) == PSeq(-3))
            out.append(-3)
            break
        e = sep_end_idx(target, j) + 0
        Assert(j < e and e <= n)
        if j > i:
            Assert(rendered(ToSeq(target), i) ==
                   ((ToSeq(target).take(j).drop(i) + PSeq(-1)) +
                    (ToSeq(target).take(e).drop(j) + PSeq(-2))) +
                   rendered(ToSeq(target), e))
            # the text before the separator is one cross-reference carrying
            # exactly the specification's characters over [i, j).
            copy_span(out, target, i, j)
            out.append(-1)
        else:
            Assert(rendered(ToSeq(target), i) ==
                   (ToSeq(target).take(e).drop(i) + PSeq(-2)) +
                   rendered(ToSeq(target), e))
        # the separator itself is one literal node carrying [j, e) verbatim.
        copy_span(out, target, j, e)
        out.append(-2)
        i = e
    return out"""

assert _BASE.count(_RIMPL) == 1, "render_nodes impl region drifted from expected text"


def _rimpl(new_body):
    """Full model.py variant with ONLY the render_nodes impl region body replaced."""
    return _swap(_BASE, _RIMPL, new_body)


# the three span-copy calls that put a node's carried text into the result, and
# the loop's start anchor. Each is a unique line inside _RIMPL.
_CP_TAIL = "                copy_span(out, target, i, n)\n"
_CP_TEXT = "            copy_span(out, target, i, j)\n"
_CP_SEP = "        copy_span(out, target, j, e)\n"
_START = "    i = 0\n"


# --- OVER-APPROXIMATION #1: the node text left out entirely -------------------
# atk-markers-only: keeps the gold loop, the gold boundaries, the gold node COUNT
# and the gold KIND markers, and drops ONLY the three copy_span calls that carry
# each node's text. The result is exactly the information the WEAKER obligation
# (`split_render`'s kind sequence, `marks`) pins — kinds and count, no text. If S3
# were an over-approximation of the node stream (kinds only, payload free), this rival
# would verify. It must be REJECTED.
_A_MARKERS = _swap(_swap(_swap(_RIMPL, _CP_TAIL, ""), _CP_TEXT, ""), _CP_SEP, "")

# --- OVER-APPROXIMATION #2: the node text trimmed ----------------------------
# atk-trim-payload: every node still exists, in the right order, with the right
# kind, but each cross-reference carries the WHITESPACE-TRIMMED segment instead of
# the specification's own characters — i.e. the node payload as the retained
# weaker model's `seg_text`/`slice_trim` computes it. This is the single most
# plausible wrong payload: it is what a tokeniser that strips each piece produces,
# and the real code does NOT strip (` int | str` renders a cross-reference
# carrying " int", padding included). Must be REJECTED.
_A_TRIM = _swap(
    _swap(_RIMPL, _CP_TAIL,
          "                a = strip_left_idx(target, i, n)\n"
          "                copy_span(out, target, a, n)\n"),
    _CP_TEXT,
    "            a = strip_left_idx(target, i, j)\n"
    "            copy_span(out, target, a, j)\n")

# --- PARTIAL-DOMAIN GUARD ----------------------------------------------------
# atk-indomain-only: gold on the bar-only shape, arbitrary outside it. The guard is a
# specification that opens with a bracket — the shape `no_other_sep` is False on, i.e.
# the one a bar-structure reading of the input has nothing to say about. The rival
# renders NOTHING (an empty node list) for those inputs. Must be REJECTED: `render_nodes`
# has no domain clause, so `rendered` states the stream for a bracket specification too
# (`[a` is a literal separator node "[" then a cross-reference "a"). Its sibling
# weak-shape-guard is the same rival against the kind sequence, which since `marks` is
# total is refuted for the same reason.
_A_INDOMAIN = (
    "    if len(target) > 0 and target[0] == 91:\n"
    "        # A specification opening with a bracket: the shape a bar-structure\n"
    "        # reading (`no_other_sep`) is silent about.\n"
    "        nothing = []  # type: List[int]\n"
    "        nothing.append(-3)\n"
    "        return nothing\n"
    + _RIMPL
)

# --- BOUNDARY TOKEN SWAP -----------------------------------------------------
# atk-tail-shift: one boundary token moved. The trailing cross-reference carries
# [i+1, n) instead of [i, n) — the node's start is one code point late, exactly
# the off-by-one a hand-written scanner makes when it treats the preceding
# separator as extending one character further. Node count, kinds and every other
# boundary are gold. Must be REJECTED.
#
# The same one-code-point shift applied to the MID-STREAM span
# (`copy_span(out, target, i + 1, j)` in the `j > i` branch) is a valid rival too,
# but Silicon reached no verdict on it inside 1200 s twice — and a case with no
# verdict measures nothing, so it would be recorded as INCONCLUSIVE rather than as
# evidence. The shift is applied on the break path instead, where the same
# obligation refutes it in ~60 s.
_A_TAILSHIFT = _swap(_RIMPL, _CP_TAIL,
                     "                copy_span(out, target, i + 1, n)\n")

# --- ORACLE ECHO -------------------------------------------------------------
# atk-echo-anchor: instead of scanning from the beginning, the rival ASKS THE
# SPECIFICATION'S OWN boundary oracle where to start (`next_sep_idx`, whose
# postcondition is the pure `next_sep`) and renders from there. Every node it does
# emit is gold; it simply takes the answer key's first separator as the origin, so
# a specification with leading text loses its first cross-reference. This is the
# echo family stated where it can actually bite: reading the obligation's own
# helper is not enough, the obligation is anchored at 0 and covers the WHOLE
# input. Must be REJECTED.
_A_ECHO = _swap(_RIMPL, _START, "    i = next_sep_idx(target, 0) + 0\n")

# --- THE FREEDOM THE ENCODING COULD HAVE LEFT --------------------------------
# atk-node-remerge: the trailing type name's characters are still emitted, in
# order, but WITHOUT a node marker of their own, so they are no longer a node —
# they run into the closing marker. Total carried characters, character order and
# the kind alphabet are all unchanged; only the PARTITION of those characters into
# nodes differs. That partition is the one thing a flat code-point carrier could
# have left free, and it is the difference the F2P turns on (one cross-reference
# per named type, not per string of characters). It must be REJECTED — i.e. the
# -1/-2 markers must genuinely DELIMIT nodes rather than merely accompany text.
#
# The mirror-image rival (the trailing text emitted as TWO cross-references whose
# texts concatenate to the gold node's text) is equally valid and was tried first;
# Silicon reached no verdict on it inside 1200 s twice, and a case with no verdict
# measures nothing, so the merge direction — refuted in ~33 s by the same
# obligation — is what ships.
_A_REMERGE = _swap(
    _RIMPL,
    _CP_TAIL + "                out.append(-1)\n",
    _CP_TAIL)

# --- FRAME MUTATION (mandatory; `target` is Acc(list_pred(target),1/2)) -------
# frame-mut-stream-write: gold body VERBATIM plus a write back into the read-only
# input, so the rejection is attributable solely to the store. Must be REJECTED
# for INSUFFICIENT PERMISSION.
_A_FRAME = (
    "    if len(target) > 0:\n"
    "        # Frame violation: write into the read-only (Acc(...,1/2)) input.\n"
    "        target[0] = target[0]\n"
    + _RIMPL
)

# --- POSITIVE CONTROL --------------------------------------------------------
# pos-stream-reshape: structurally different, behaviourally identical. The three
# marker constants are hoisted into named locals and the tail span end is aliased;
# EVERY Invariant and EVERY Assert is kept verbatim, the append order and the
# front-consuming `i = e` are unchanged. If it FAILS => SPEC-TOO-STRONG.
_POS_STREAM = _swap(_swap(_swap(_swap(_swap(_swap(
    _RIMPL,
    "    out = []  # type: List[int]\n",
    "    XREF = -1\n    SEP = -2\n    END = -3\n"
    "    out = []  # type: List[int]\n"),
    _CP_TAIL + "                out.append(-1)\n",
    "                tail = n\n"
    "                copy_span(out, target, i, tail)\n"
    "                out.append(XREF)\n"),
    "            out.append(-3)\n", "            out.append(END)\n"),
    _CP_TEXT + "            out.append(-1)\n",
    _CP_TEXT + "            out.append(XREF)\n"),
    "        out.append(-2)\n", "        out.append(SEP)\n"),
    "        i = e\n", "        i = e + 0\n")
assert _POS_STREAM != _RIMPL, "pos-stream-reshape did not change the impl"

# --- ADMISSIBILITY CONTROL ---------------------------------------------------
# admiss-stream-reads: the precondition is Acc(list_pred(target),1/2) + MustTerminate
# and NOTHING else, so EVERY specification is in-domain — including the empty one
# and the ones the retained weaker obligation excludes. This control keeps the gold
# impl verbatim and first asserts, under the half permission alone, that the reads a
# renderer needs are admitted (the length always; the first code point when
# non-empty) with no domain clause available to lean on. If it FAILS =>
# PRECOND-TOO-STRONG.
_ADMISS_STREAM = (
    "    # Admissibility: no domain clause at all; the half permission admits\n"
    "    # reading the length and the elements of ANY specification.\n"
    "    Assert(len(target) >= 0)\n"
    "    if len(target) > 0:\n"
    "        Assert(target[0] == target[0])   # read admitted under Acc(...,1/2)\n"
    + _RIMPL
)


SPEC_TESTS = [
    {
        "id": "pos-local-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_RESHAPE),
        "rationale": (
            "structurally-different but CORRECT impl: the two constant booleans the "
            "loop appends are hoisted into named locals XREF=True / SEP=False and the "
            "separator end is aliased (end = e + 0, resumed from), WITHOUT touching any "
            "proof obligation. EVERY gold Invariant is kept verbatim (incl. the "
            "load-bearing telescoping "
            "ToSeq(result)+marks(ToSeq(target),i)==marks(ToSeq(target),0)), EVERY Assert "
            "is kept verbatim (the boundary assert and the three marks-unfold asserts), "
            "and the append order / front-consuming `i=e` are "
            "unchanged (directive 2/3: no dropped lemma, no loop-direction flip, no "
            "forward-append against the front-recursive `marks` fold). If it FAILS => "
            "SPEC-TOO-STRONG (a faithful correct impl is rejected)."
        ),
    },
    {
        "id": "admiss-reads",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "the precondition (Acc(list_pred(target),1/2) half-permission + "
            "MustTerminate(5), no domain clause) must admit EVERY specification, the "
            "F2P `int | str` included: the length is readable and, when non-empty, the "
            "first code point is readable under the half-permission, with no shape "
            "assumption to lean on. The gold impl is otherwise "
            "verbatim (only reads/asserts added inside the impl region, no write). If it "
            "FAILS => PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mut-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT),
        "refinement": (
            "the gold make_xrefs only READS its `target` (a Python str — immutable — "
            "fed to re.split); it NEVER writes/rebinds the argument. A faithful real "
            "patch that mutated `target` would be infidelity to make_xrefs (and a str "
            "cannot be mutated in place anyway), so such a rival is not the gold patch "
            "and would not faithfully resolve the F2P. The store here is a no-op only by "
            "coincidence; the point is the spec must forbid ANY write to the read-only "
            "input."
        ),
        "rationale": (
            "REJECTED by the PERMISSION SYSTEM: `target` is granted at "
            "Acc(list_pred(target),1/2) (P1); the store target[0]=target[0] demands "
            "FULL write permission, which is not available, so the verifier rejects for "
            "INSUFFICIENT PERMISSION. The gold loop/return body is kept verbatim so the "
            "rejection is attributable solely to the write. If it VERIFIES => the read- "
            "only frame is hollow (frame-mutation, the #1 weakness class; a byte-fuzzer "
            "never thinks to mutate the input)."
        ),
    },
    {
        "id": "weak-single-xref",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_SINGLE),
        "refinement": (
            "returning [True] (one cross-reference for the whole spec) is EXACTLY the "
            "pre-patch behaviour (model_prepatch.py): the delimiter regex without the "
            "added `\\s*\\|\\s*` alternative never splits on the bar, so make_xrefs "
            "renders `int | str` as a single pending_xref with reftarget='int | str'. "
            "That fails the F2P test_info_field_list_piped_type, which asserts TWO "
            "separate pending_xref nodes ('int' and 'str') with a literal ' | ' between "
            "them. Does NOT resolve — this is precisely the change the spec senses "
            "(G-DIFF)."
        ),
        "rationale": (
            "REJECTED by Q3 (Ensures(ToSeq(Result()) == marks(ToSeq(target),0))): for "
            "any bar-containing spec (e.g. `int | str`) marks is "
            "[True,False,True] (length 2*bars+1 >= 3 on a bar-only spec) but "
            "the rival returns [True] (length 1); on the empty spec marks is empty and "
            "the rival still returns [True]. PARTIAL-DOMAIN: correct only on the "
            "single-name sub-domain, wrong on every input carrying a separator. If "
            "it VERIFIES => SPEC-TOO-WEAK (the split is not enforced)."
        ),
    },
    {
        "id": "weak-no-sep",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_NOSEP),
        "refinement": (
            "emitting one cross-reference per type but NO literal separator node is what "
            "a real patch that split on the bar yet then `filter`ed out / skipped the "
            "separator pieces would do. The F2P asserts the literal_emphasis ' | ' node "
            "BETWEEN the two xrefs (the separator is rendered, not dropped); a tree "
            "missing it is structurally different and fails the assert_node. Does NOT "
            "resolve."
        ),
        "rationale": (
            "REJECTED by Q3: for `int | str` the rival returns [True,True] (length 2) "
            "but marks is [True,False,True] (length 3) — both the LENGTH and entry[1] "
            "(which must be the separator False) disagree. The dropped False breaks the "
            "telescoping relation ToSeq(result)+marks==marks, so no proof of Q3 exists. "
            "If it VERIFIES => SPEC-TOO-WEAK (the "
            "literal separator is not pinned)."
        ),
    },
    {
        "id": "weak-all-xref",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ALLXREF),
        "refinement": (
            "classifying EVERY split piece — including the bar separators — as a cross- "
            "reference is what a real patch that dropped the `if delims_re.match(piece)` "
            "test (always taking the make_xref branch) would do. It would render the "
            "literal ' | ' separator as a pending_xref with reftarget='|' instead of an "
            "innernode/contnode literal, so the F2P (which asserts the ' | ' is a "
            "literal_emphasis, NOT a pending_xref) fails. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by Q3 (the VALUE-LEVEL double-mask analogue): for `int | str` the "
            "rival returns the right NUMBER of nodes [True,True,True] (length 3 == "
            "2*bars+1) but marks is [True,False,True] — entry[1] (the separator) must be "
            "False, not True. Q3 requires equality of the WHOLE PSeq, so the mislabelled "
            "separator index is caught; there is no value proxy that could drop it. If "
            "it VERIFIES => SPEC-TOO-WEAK (the separator/cross-reference distinction is "
            "unpinned)."
        ),
    },
    {
        "id": "weak-shape-guard",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_SHAPEGUARD),
        "refinement": (
            "rendering nothing for every specification that carries a bracket, comma, "
            "`or` or ellipsis is what a real patch that recognised ONLY the bar (and "
            "bailed out on anything else) would do. `Dict[str, str]`, `List[int]`, "
            "`Tuple[int, ...]`, `str or int` and `list[int] | None` are exactly what the "
            "PASS_TO_PASS tests tests/test_domain_py.py::test_domain_py_xrefs and "
            "::test_info_field_list observe, and a field that renders no nodes at all "
            "fails their assert_node outright. Does NOT resolve: it breaks the P2P suite "
            "while the gold change keeps it green."
        ),
        "rationale": (
            "REJECTED by Q3 BECAUSE Q3 CARRIES NO DOMAIN CLAUSE: for `list[int] | None` "
            "marks is [True,False,True,False,False,True] and for `a[b]` it is "
            "[True,False,True,False], but the guard returns []. This is the sharpest "
            "rival against a KIND-ONLY obligation — every specification with a non-bar "
            "separator is a shape a bar-structure reading is silent about — so if it "
            "VERIFIES => SPEC-TOO-WEAK (the kind sequence is pinned only on the bar-only "
            "shape and the behaviour on most real type specifications is free)."
        ),
    },
    {
        "id": "pos-stream-reshape",
        "kind": "soundness",
        "expect": "verify",
        "module": _rimpl(_POS_STREAM),
        "rationale": (
            "structurally-different but CORRECT impl of the PRIMARY obligation: the "
            "three kind markers the loop appends are hoisted into named locals "
            "XREF=-1 / SEP=-2 / END=-3, the tail span end is aliased (tail = n) and "
            "the resume index is read through `e + 0`, WITHOUT touching any proof "
            "obligation. EVERY gold Invariant is kept verbatim (incl. the "
            "load-bearing telescoping ToSeq(out)+rendered(ToSeq(target),i)== "
            "rendered(ToSeq(target),0) and the MustTerminate(n-i+1) measure), EVERY "
            "Assert is kept verbatim, and the append order / front-consuming `i = e` "
            "are unchanged (directive 2/3: no dropped lemma, no loop-direction flip, "
            "no forward-append against the front-recursive `rendered` fold). If it "
            "FAILS => SPEC-TOO-STRONG (a faithful correct impl is rejected)."
        ),
    },
    {
        "id": "admiss-stream-reads",
        "kind": "admissibility",
        "expect": "verify",
        "module": _rimpl(_ADMISS_STREAM),
        "rationale": (
            "the PRIMARY obligation's precondition is Acc(list_pred(target),1/2) + "
            "MustTerminate(5) and NOTHING else — no well_formed, no shape clause — so "
            "EVERY specification is in-domain, including the empty one and the ones "
            "the retained weaker obligation excludes. This control keeps the gold impl "
            "verbatim and first asserts, under the half permission with no domain "
            "clause to lean on, that the reads a renderer needs are admitted: the "
            "length always, and the first code point when non-empty. No write => no "
            "extra permission demand. If it FAILS => PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "atk-markers-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rimpl(_A_MARKERS),
        "refinement": (
            "a real patch that split on the bar and produced the right NUMBER of nodes "
            "of the right KINDS, but built each node from something other than its own "
            "stretch of the specification, would not resolve: the F2P "
            "test_info_field_list_piped_type asserts the two pending_xref nodes carry "
            "'int' and 'str' and the literal_emphasis between them carries ' | '. Node "
            "kinds alone do not say that. This rival is the exact shape of that patch "
            "at the model level: gold boundaries, gold count, gold kinds, no text."
        ),
        "rationale": (
            "REJECTED by S3 (Ensures(ToSeq(Result()) == rendered(ToSeq(target),0))): "
            "dropping the three copy_span calls leaves the marker skeleton "
            "[-1,-2,...,-3] where `rendered` requires each marker to be PRECEDED by "
            "that node's carried code points, so the telescoping loop invariant "
            "ToSeq(out)+rendered(ToSeq(target),i)==rendered(ToSeq(target),0) can no "
            "longer be re-established. OVER-APPROXIMATION lane: this rival satisfies "
            "the retained WEAKER obligation's information content exactly (`marks`: "
            "kinds and count), so if it VERIFIED the primary obligation would be pinning nothing "
            "the kind sequence did not already pin => SPEC-TOO-WEAK, and the node "
            "payload would be free."
        ),
    },
    {
        "id": "atk-trim-payload",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rimpl(_A_TRIM),
        "refinement": (
            "trimming each piece is the single most plausible wrong payload: it is what "
            "a tokeniser that strips whitespace off every split piece produces, and it "
            "is what the pure region's trimmed-segment helpers (seg_text / "
            "slice_trim) compute. The real code does NOT strip — it hands each "
            "re.split piece to make_xref verbatim, so ` int | str` yields a "
            "cross-reference whose target is ' int', padding included. A patch that "
            "stripped would change the reftarget of every padded piece."
        ),
        "rationale": (
            "REJECTED by S3: with the leading whitespace of a segment removed from the "
            "carried text, ToSeq(out) is missing those code points while "
            "rendered(ToSeq(target),i) still contains them (it is defined by the raw "
            "slices target[i:j] / target[j:e]), so the telescoping invariant fails on "
            "any specification with padding before a name. OVER-APPROXIMATION lane, "
            "second form: the node exists with the right kind at the right place, only "
            "its text differs. If it VERIFIES => SPEC-TOO-WEAK (the carried text is not "
            "pinned to the specification's own characters)."
        ),
    },
    {
        "id": "atk-indomain-only",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rimpl(_A_INDOMAIN),
        "refinement": (
            "a real patch whose new delimiter alternative is guarded to fire only on "
            "specifications it recognises — and which falls back to rendering nothing "
            "(or to the old whole-string behaviour) on anything containing a bracket, "
            "comma, `or` or ellipsis — is a plausible defensive patch. It does not "
            "resolve: PASS_TO_PASS cases in tests/test_domain_py.py render bracketed "
            "and comma-separated specifications (List[int], Dict[str, str], "
            "Tuple[str, ...]) and assert their node trees, so a patch that renders "
            "nothing there fails them."
        ),
        "rationale": (
            "REJECTED by S3. PARTIAL-DOMAIN-GUARD lane: the rival is gold on the "
            "bar-only shape and arbitrary outside it, keyed on a specification that "
            "opens with a bracket (code point 91) — the shape `no_other_sep` is False "
            "on, i.e. the one a bar-structure reading of the input is silent about. "
            "NEITHER obligation has a domain clause, so `rendered` still states the "
            "stream there ('[a' is a literal separator "
            "node '[' then a cross-reference 'a'), and returning [-3] contradicts it. "
            "If it VERIFIES => the behaviour on every specification carrying a non-bar "
            "separator is free => SPEC-TOO-WEAK. Its kind-level sibling is "
            "weak-shape-guard."
        ),
    },
    {
        "id": "atk-tail-shift",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rimpl(_A_TAILSHIFT),
        "refinement": (
            "a real patch that consumed one code point too many when closing the "
            "preceding separator — so the cross-reference after it starts one character "
            "late ('int | str' giving reftargets 'int' and 'tr') — is the classic "
            "off-by-one of a hand-written scanner. It fails the F2P, which asserts the "
            "second pending_xref carries exactly 'str'."
        ),
        "rationale": (
            "REJECTED by S3. BOUNDARY-TOKEN-SWAP lane: exactly one boundary moves — the "
            "trailing cross-reference carries [i+1, n) instead of [i, n) — while the node "
            "count, the kinds, the separator spans and every other boundary are gold. "
            "`rendered` fixes that node's text to target[i:n], so the postcondition fails "
            "on any specification whose last piece is a type name. If it VERIFIES => "
            "SPEC-TOO-WEAK (node spans would be pinned only up to a shift)."
        ),
    },
    {
        "id": "atk-echo-anchor",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rimpl(_A_ECHO),
        "refinement": (
            "a real patch that located the first delimiter with the new regex and "
            "started emitting nodes THERE — dropping the text before it — is what "
            "`re.split` misused as `re.search` + slice produces. It does not resolve: "
            "'int | str' would render only ' | ' and 'str', losing the first "
            "cross-reference the F2P asserts."
        ),
        "rationale": (
            "REJECTED by S3. ORACLE-ECHO lane, stated where it can bite: the rival does "
            "not compute its own starting point, it ASKS THE SPECIFICATION'S OWN "
            "boundary oracle (`next_sep_idx`, whose postcondition is the pure "
            "`next_sep`) and renders from there, so every node it emits is gold and its "
            "answer is read off the obligation's own helper. It is still rejected, "
            "because S3 is anchored at 0 and covers the WHOLE input: the loop invariant "
            "ToSeq(out)+rendered(ToSeq(target),i)==rendered(ToSeq(target),0) does not "
            "hold on ENTRY when i is the first separator and text precedes it. If it "
            "VERIFIES => SPEC-TOO-WEAK (the obligation would only pin some suffix, and "
            "echoing the oracle would buy correctness)."
        ),
    },
    {
        "id": "atk-node-remerge",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rimpl(_A_REMERGE),
        "refinement": (
            "a real patch that emitted the same characters but partitioned them into a "
            "different number of nodes — a trailing name folded into its neighbour, or "
            "one cross-reference per character — still carries every named type's text in "
            "order, yet it is not one link per named type. The F2P asserts exactly two "
            "pending_xref children for 'int | str'; a tree with one or three fails "
            "assert_node on the child count."
        ),
        "rationale": (
            "REJECTED by S3. This is the ONE freedom a flat code-point carrier could "
            "have left: the rival still emits the trailing type name's characters, in "
            "order, but with no node marker of their own, so the total carried "
            "characters, their order and the kind alphabet are unchanged and only the "
            "PARTITION of those characters into nodes differs. It is rejected because the "
            "-1/-2 markers genuinely DELIMIT nodes — `rendered` has a -1 where this "
            "stream runs the text into the closing marker — which is what makes the "
            "encoding injective (code points are non-negative, so no marker can be "
            "mistaken for text). If it VERIFIES => SPEC-TOO-WEAK (the carrier would pin "
            "the concatenated text but not the node boundaries, and 'one cross-reference "
            "per named type' would be unstated)."
        ),
    },
    {
        "id": "frame-mut-stream-write",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _rimpl(_A_FRAME),
        "refinement": (
            "the gold make_xrefs only READS its `target` (a Python str — immutable — fed "
            "to re.split); it NEVER writes or rebinds the argument. A real patch that "
            "mutated the specification in place would be infidelity to make_xrefs, so "
            "the primary obligation must forbid ANY write just as the retained one does."
        ),
        "rationale": (
            "REJECTED by the PERMISSION SYSTEM: `target` is granted at "
            "Acc(list_pred(target),1/2) (R1); the store target[0]=target[0] demands FULL "
            "write permission, which is not available, so the verifier rejects for "
            "INSUFFICIENT PERMISSION. The gold body is kept verbatim so the rejection is "
            "attributable solely to the write. If it VERIFIES => the read-only frame is "
            "hollow on the primary obligation (frame-mutation, the #1 weakness class)."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane — the A-reference deep model `kinds` vs the REAL stdlib re tokeniser.
# meta.axioms == [] (no consumed @ContractOnly axiom); deep_model_references has ONE
# A-reference: `kinds` models `re.split(delims)` + `filter(None,...)` + per-piece
# `delims_re.match(...)` with the gold patch's delimiter regex. The real callee is the
# STDLIB `re` module (the exact module the patched code calls), so the probes need NO
# repo import and run anywhere. The probes embed faithful transcriptions of model.py's
# kinds / first_bar / well_formed / no_other_sep folds (in lock-step with axiom_check.py
# / G-AX) and reproduce the patched delimiter regex VERBATIM, then compare the deep
# model against the live re tokeniser. axiom-soundness == the deep model equals the
# real callee on the well_formed domain (over the FULL delimiter alphabet, so the fuzz
# actually probes the domain boundary); axiom-containment == every caller-reachable
# input the model can pass (a well_formed spec) is in the real tokeniser's domain and
# the deep model agrees there.
# ---------------------------------------------------------------------------

# Shared reference encodings (kept in lock-step with model.py's @Pure folds and with
# axiom_check.py). Embedded into both probes; uses only the stdlib `re` module.
_REF_SRC = r'''
import re

# The delimiter regex EXACTLY as installed by the gold patch (sphinx/domains/python.py,
# make_xrefs). The change adds the `\s*\|\s*` alternative.
DELIMS = r'(\s*[\[\]\(\),](?:\s*or\s)?\s*|\s+or\s+|\s*\|\s*|\.\.\.)'
DELIMS_RE = re.compile(DELIMS)

BAR = ord('|')
SPACE = ord(' ')
DOT = ord('.')
O = ord('o')
R = ord('r')
BRACKETS = {ord('['), ord(']'), ord('('), ord(')'), ord(',')}


def is_space(c):
    """model.py `is_space`: a whitespace code point — the FULL whitespace set the
    real delimiter pattern's `\s` matches, not merely the ASCII space 32."""
    return ((9 <= c <= 13) or (28 <= c <= 32) or c == 133 or c == 160 or
            c == 5760 or (8192 <= c <= 8202) or c == 8232 or c == 8233 or
            c == 8239 or c == 8287 or c == 12288)


# Guard: the transcription above must be EXACTLY the regex engine's `\s` class,
# else these probes would validate a different model than model.py's.
_ws_bad = [c for c in range(0x110000) if bool(re.match(r'\s', chr(c))) != is_space(c)]
assert not _ws_bad, "is_space transcription != regex \\s class: %r" % (_ws_bad[:8],)


def first_bar(s, i):
    """model.py `first_bar`: index of the first '|' at/after i, clamped."""
    while i < len(s) and s[i] != BAR:
        i += 1
    return i


def model_kinds(codepoints, i=0):
    """model.py deep model `kinds(s, i)`: the strictly-alternating kind sequence
    (True = cross-reference, False = literal separator) for the raw-bar split."""
    out = []
    while True:
        p = first_bar(codepoints, i)
        out.append(True)
        if p >= len(codepoints):
            break
        out.append(False)
        i = p + 1
    return out


def seg_text_nonempty(codepoints, i, j):
    """True iff the trimmed segment codepoints[i:j] is non-empty (model.py
    `len(seg_text(...)) > 0`); trims ANY whitespace, per model.py `strip_*`."""
    a, b = i, j
    while a < b and is_space(codepoints[a]):
        a += 1
    while b > a and is_space(codepoints[b - 1]):
        b -= 1
    return b > a


def no_other_sep(codepoints, i=0):
    """model.py `no_other_sep(s, i)`: the suffix contains none of the non-bar
    separator triggers (no `[ ] ( ) ,`, no `...` run, no whitespace-bounded `or`
    — the `or` bounded by ANY whitespace, per model.py's `is_space` guard)."""
    n = len(codepoints)
    x = i
    while x < n:
        c = codepoints[x]
        if c in BRACKETS:
            return False
        if (c == DOT and x + 2 < n and codepoints[x + 1] == DOT and
                codepoints[x + 2] == DOT):
            return False
        if (is_space(c) and x + 3 < n and codepoints[x + 1] == O and
                codepoints[x + 2] == R and is_space(codepoints[x + 3])):
            return False
        x += 1
    return True


def well_formed(codepoints, i=0):
    """model.py `well_formed(s, i)`: (a) every bar-separated segment names a
    non-empty type, AND (b) no_other_sep (the bar is the only separator)."""
    if not no_other_sep(codepoints, i):
        return False
    while True:
        p = first_bar(codepoints, i)
        if not seg_text_nonempty(codepoints, i, p):
            return False
        if p >= len(codepoints):
            return True
        i = p + 1


def real_kinds(target):
    """The REAL rendered-node kind sequence the patched make_xrefs produces: split on
    the delimiter regex, drop empty pieces, each remaining piece is a literal separator
    iff it matches the delimiter regex, else a cross-reference."""
    pieces = [p for p in re.split(DELIMS, target) if p]
    return [not bool(DELIMS_RE.match(p)) for p in pieces]
'''


_AX_SOUND_PROBE = _REF_SRC + r'''
import random
import sys

fails = 0

def check_in_domain(target):
    """On the modelled (well_formed) domain, deep model must == the real callee."""
    global fails
    cps = [ord(ch) for ch in target]
    if not well_formed(cps):
        return False
    observed = real_kinds(target)
    expected = model_kinds(cps)
    if observed != expected:
        fails += 1
        print("UNSOUND kinds on %r: real=%r model=%r" % (target, observed, expected))
    return True

# --- in-domain boundary cases (bar-only well-formed specs, incl. the F2P) --------
boundary_in = [
    "int | str", "int|str", "bytes | str | None", "a | b | c | d", "int",
    "SomeClass", "a|b", "x | y", "foo |bar", "x| y",
    "List | Dict | Tuple | Set", "int   |   str", "mod.Class | other.Class",
    "colored | factor", "a or",
    # non-ASCII whitespace PADDING a bar is in-domain (it is consumed into the
    # separator exactly as a space is) as long as each segment still names a type,
    # and an `or` NOT bounded by whitespace on both sides is not a separator.
    "int\t|\tstr", "a\n|\nb", "x\xa0|\xa0y", "int　|　str", "a \t| \tb",
    "aorb | c", "ore\t| int",
]
checked = 0
for t in boundary_in:
    if not check_in_domain(t):
        fails += 1
        print("IN-DOMAIN BOUNDARY WRONGLY REJECTED by well_formed: %r" % (t,))
    else:
        checked += 1

# --- out-of-domain boundary cases (must be rejected by well_formed) --------------
# The second block is the non-ASCII-whitespace class: an `or` padded by TAB/NL/NBSP/
# IDEOGRAPHIC SPACE is just as much a separator as a space-padded one, and a segment
# made only of such whitespace names no type. Both must fall outside the domain, or
# the bar-only alternation would not be the real kind sequence there.
boundary_out = [
    "Tuple[str, ...]", "Dict[str, str]", "List[int]", "str or int", "word or other",
    ",", "...", "a, b", "Optional[int] | str", "abc...def",
    "a\tor\tb", "int\tor\tstr", "a\nor\nb", "x\xa0or\xa0y", "a\tor\tb\t|\tc",
    "a　or　b", "a\x0bor\ror b", "a|\t", "\t|a", "a|\t|b", "\xa0|a",
    "a|\xa0", "\x0b|ce\r", "　|a", "a| ", "int\t|\t", "\n|\n",
]
rejected = 0
for t in boundary_out:
    cps = [ord(ch) for ch in t]
    if well_formed(cps):
        fails += 1
        print("OUT-OF-DOMAIN WRONGLY ADMITTED (would be unsound): %r" % (t,))
    else:
        rejected += 1

# --- the discriminating F2P fact, explicitly -------------------------------------
if model_kinds([ord(c) for c in "int | str"]) != [True, False, True]:
    fails += 1
    print("FACT FAIL: kinds('int | str') must be [True,False,True]")
if real_kinds("int | str") != [True, False, True]:
    fails += 1
    print("FACT FAIL: real tokeniser on 'int | str' must be [True,False,True]")

# --- randomized fuzz over the FULL delimiter alphabet ----------------------------
rng = random.Random(9258)
# The alphabet includes every delimiter char AND the non-ASCII whitespace the real
# `\s` matches. Those code points are exactly where a space-only whitespace notion
# would part company with the real pattern (a TAB-padded `or` still separates; a
# segment of pure NBSP names no type), so omitting them would make this probe unable
# to fail — it would draw only from the subset on which any such model agrees.
_UWS = ["\t", "\n", "\x0b", "\x0c", "\r", "\x1c", "\x1d", "\x1e", "\x1f", "\x85",
        "\xa0", " ", " ", " ", " ", " ", " ",
        " ", " ", " ", " ", " ", "　"]
alphabet = (list("abcdeFGHIJ_0129")
            + [" ", " ", "|", "[", "]", "(", ")", ",", ".", "o", "r"] + _UWS)
fuzzed = 0
skipped = 0
attempts = 0
while fuzzed < 60000 and attempts < 4000000:
    attempts += 1
    n = rng.randint(0, 22)
    t = "".join(rng.choice(alphabet) for _ in range(n))
    if check_in_domain(t):
        fuzzed += 1
    else:
        skipped += 1

# --- structured fuzz over the full delimiter alphabet ----------------------------
names = ["int", "str", "bytes", "None", "List", "Dict", "X", "Foo_1", "T2",
         "List[int]", "Dict[str, str]", "Tuple[str, ...]", "a or b", "mod.Class",
         "Optional[int]", "a\tor\tb", "x\xa0or\xa0y", "a　or　b", "aorb"]
# pads straddle the domain boundary: "" and real whitespace of several kinds, so some
# draws are in-domain bar-padding and others make a segment pure whitespace.
pads = ["", " ", "  ", "\t", "\n", "\xa0", "　", " \t", " "]
structured = 0
structured_skipped = 0
for _ in range(60000):
    k = rng.randint(1, 5)
    parts = [rng.choice(names) for _ in range(k)]
    seps = [rng.choice(pads) + "|" + rng.choice(pads) for _ in range(k - 1)]
    t = parts[0]
    for idx in range(k - 1):
        t += seps[idx] + parts[idx + 1]
    if check_in_domain(t):
        structured += 1
    else:
        structured_skipped += 1

if fails:
    print("AXIOM-SOUNDNESS FAIL: %d disagreement(s) between deep `kinds` and the real "
          "re.split/re.match tokeniser" % fails)
    sys.exit(1)
print("AXIOM-SOUNDNESS OK: deep `kinds` == real re tokeniser on %d in-domain boundary "
      "+ %d out-of-domain boundary (correctly rejected) + %d fuzz (%d skipped) + %d "
      "structured (%d skipped) well-formed inputs over the FULL delimiter alphabet; "
      "F2P 'int | str' => [True,False,True]." %
      (checked, rejected, fuzzed, skipped, structured, structured_skipped))
sys.exit(0)
'''


_AX_COVER_PROBE = _REF_SRC + r'''
import random
import sys

# (axiom-containment) Which callee-inputs can the MODEL actually reach? `split_render`
# applies the deep model `kinds` to ToSeq(target) where the precondition requires
# well_formed(ToSeq(target), 0). So the ONLY callee-inputs the model can reach are
# well_formed specs (the bar is the only separator AND every bar-segment is non-empty).
# The real callee is the stdlib re tokeniser with the patched pattern; its domain is
# any Python str (re.split never raises on a str). Every reachable input is a str, so
# every caller-reachable input is INSIDE the real tokeniser's domain — and on that
# domain the deep model must AGREE with the real callee (containment + soundness on the
# reachable slice). Covering MORE (out-of-domain specs the regex splits differently)
# than the caller reaches would be sound, not a defect; we only need containment. We
# CONFIRM by sampling the reachable (well_formed) operand space heavily and asserting
# re.split raises nothing and the deep model == the real callee on every reachable input.
fails = 0
rng = random.Random(2024)

def reachable_specs():
    # well-formed union-type specs (the inputs split_render's precondition admits):
    # 1..6 bar-separated non-empty names, names from a bar-only alphabet (no other
    # delimiter), with assorted whitespace padding around the bars.
    yield "int | str"          # the F2P
    name_alpha = list("abcdeFGHIJ_0129")
    # padding around the bar spans the whole whitespace class the real pattern
    # consumes, not just the ASCII space, so the reachable slice that is sampled is
    # the one the repaired domain actually admits.
    pads = ["", " ", "  ", "   ", "\t", "\n", "\r", "\x0b", "\xa0", "　",
            " ", " ", " \t", "\t\xa0"]
    for _ in range(40000):
        k = rng.randint(1, 6)
        parts = []
        for _ in range(k):
            L = rng.randint(1, 6)
            # a non-empty name (the leading char is non-space so the segment trims
            # to a non-empty type) from the bar-only alphabet.
            nm = "".join(rng.choice(name_alpha) for _ in range(L))
            parts.append(nm)
        t = parts[0]
        for idx in range(1, k):
            t += rng.choice(pads) + "|" + rng.choice(pads) + parts[idx]
        yield t

reached = 0
for spec in reachable_specs():
    cps = [ord(ch) for ch in spec]
    if not well_formed(cps):
        # the generator should only emit well_formed specs; if not, skip (it is simply
        # not a reachable callee-input for split_render).
        continue
    try:
        observed = real_kinds(spec)      # the real callee on a reachable input
    except Exception as e:               # pragma: no cover
        fails += 1
        print("CONTAINMENT FAIL: real tokeniser raised on reachable %r: %s" % (spec, e))
        continue
    expected = model_kinds(cps)
    if observed != expected:
        fails += 1
        print("CONTAINMENT/SOUNDNESS FAIL on reachable %r: real=%r model=%r"
              % (spec, observed, expected))
    reached += 1

if fails:
    print("AXIOM-CONTAINMENT FAIL: %d reachable callee-input(s) outside the real "
          "tokeniser's domain or mismatched" % fails)
    sys.exit(1)
print("AXIOM-CONTAINMENT OK: every callee-input the model can reach (a well_formed "
      "union-type spec, the only inputs split_render's precondition admits) is a Python "
      "str INSIDE the real re tokeniser's domain (re.split never raises) and the deep "
      "model `kinds` agrees on all %d sampled reachable inputs." % reached)
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-kinds",
        "axiom": "kinds",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "`kinds` is an A-reference deep model of the real `re.split(delims)` + "
            "`filter(None,...)` + per-piece `delims_re.match(...)` tokeniser (no consumed "
            "@ContractOnly axiom in this bundle). AXIOM-SOUNDNESS: the deep fold must "
            "equal the REAL stdlib re tokeniser (with the patched delimiter regex "
            "reproduced verbatim) on the well_formed domain. The probe runs the live "
            "re.split/re.match on 15 in-domain boundary + 10 out-of-domain boundary "
            "(asserting well_formed correctly rejects each) + 60000 fuzz + 60000 "
            "structured inputs over the FULL delimiter alphabet, and asserts agreement; "
            "mirrors axiom_check.py / G-AX. If the real callee disagrees anywhere on the "
            "well_formed domain => AXIOM-UNSOUND."
        ),
    },
    {
        "id": "ax-cover-kinds",
        "axiom": "kinds",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": (
            "AXIOM-CONTAINMENT: split_render applies the deep model `kinds` to "
            "ToSeq(target) under the precondition well_formed(ToSeq(target),0), so the "
            "ONLY callee-inputs the model can reach are well_formed union-type specs. "
            "The real callee (the stdlib re tokeniser with the patched pattern) accepts "
            "any Python str (re.split never raises), so every reachable input is INSIDE "
            "its domain — and the deep model must agree there. The probe samples the "
            "reachable well_formed operand space heavily (the F2P + 40000 random 1..6 "
            "bar-separated non-empty-name specs over a bar-only alphabet) and asserts "
            "re.split raises nothing and the deep model == the real callee. A reachable "
            "input outside the domain or a mismatch => AXIOM-TOO-WEAK-FOR-CALLER (none "
            "expected: covering more than the caller reaches is sound, not a defect)."
        ),
    },
]
