# properties.py — PBT falsification battery for django__django-15103. NOT a Nagini
# module; a record of adversarially-reasoned cases the runner (swebench_nagini.pbt)
# executes and stamps RESULT onto. Spec cases are FULL model.py variants that share
# the FROZEN spec byte-for-byte (region surgery: ONLY the text strictly between the
# function's `# impl-start` / `# impl-end` — which INCLUDES the nested invariants
# region — is edited; the spec view is never touched), checked by Nagini verify +
# markers.same_spec. The axiom case re-runs the A-reference soundness check
# (axiom_check.py) in the instance Docker image (real post-patch Django callee).
#
# Defended surface (read from model.py / refinement.md / mapping.md / instance.json):
#   build_json_script(payload: List[int], element_id: Optional[List[int]]) -> List[int]
#   Models the gold change to django.utils.html.json_script: make the element_id
#   optional. Wrap an already-serialized JSON payload in a <script ...> element of
#   media type application/json. The id attribute is OPTIONAL:
#     * present id (non-None, non-empty): opening tag carries the id, then the
#       media-type attribute -> prefix_with_id(element_id) + payload + tag_close();
#     * absent/empty id (None, or empty token): opening tag carries ONLY the
#       media-type attribute (id attribute ABSENT entirely) -> tag_open_no_id() +
#       payload + tag_close().
#   The F2P tests (test_without_id, test_json_script_without_id) call json_script
#   with NO id and assert the output is exactly '<script type="application/json">'
#   + payload + '</script>' (no id="..."). The pre-patch code ALWAYS emitted the
#   id-bearing template; model_prepatch.py reproduces that and FAILS the absent
#   branch postcondition (G-DIFF).
#
#   PRECONDITION (three clauses: two read-only frame grants + one obligation):
#     (P1) Requires(Acc(list_pred(payload), 1/2))                  # HALF perm => READ-ONLY
#     (P2) Requires(Implies(element_id is not None,
#                           Acc(list_pred(element_id), 1/2)))       # HALF perm => READ-ONLY
#     (P3) Requires(MustTerminate(2))                               # TOTAL correctness:
#            every loop must consume the obligation with a strictly decreasing
#            measure; a diverging impl (vacuous value postconditions) is rejected
#            by the obligation system ("Obligation leak check failed").
#   POSTCONDITION (five clauses; three framing/permission + two LOAD-BEARING):
#     (Q1) Ensures(Acc(list_pred(payload), 1/2))                   # returns payload read perm
#     (Q2) Ensures(Implies(element_id is not None,
#                          Acc(list_pred(element_id), 1/2)))         # returns id read perm
#     (Q3) Ensures(Acc(list_pred(Result())))                       # full perm on the result
#     (Q4) Ensures(Implies(element_id is not None and len(element_id) > 0,
#            ToSeq(Result()) == prefix_with_id(element_id) + ToSeq(payload) + tag_close()))
#            -- PRESENT branch: the id-bearing wrapping is pinned exactly.
#     (Q5) Ensures(Implies(element_id is None or len(element_id) == 0,
#            ToSeq(Result()) == tag_open_no_id() + ToSeq(payload) + tag_close()))
#            -- ABSENT/EMPTY branch: the id-FREE wrapping is pinned exactly (no id attr).
#   Q4 and Q5 together PIN the output on the WHOLE domain in BOTH directions: every
#   present-id input MUST get the id-bearing tag, every absent/empty-id input MUST
#   get the id-free tag. The presence predicate `element_id is not None and
#   len(element_id) > 0` is the R-refinement of Python truthiness `if element_id:`
#   (empty token == falsy == absent). There is no slack — a rival that misbuilds the
#   output on EITHER branch (or misclassifies the empty-token boundary) fails Q4/Q5.
#
# FRAME-MUTATION lane is MANDATORY: BOTH inputs are read-only.
#   * payload : Acc(list_pred(payload), 1/2)  (P1)
#   * element_id : Acc(list_pred(element_id), 1/2) when present  (P2)
#   A rival that WRITES either input must be REJECTED for INSUFFICIENT PERMISSION.
#   Byte-fuzzers never think to mutate the input; this is the project's #1 weakness
#   class. The real json_script only READS element_id (interpolated by format_html)
#   and the serialized payload string; a str/SafeString is immutable, so any write
#   to the carrier would be unfaithful to the gold and could corrupt a caller's
#   live argument. Two frame-mutation rivals are included (one per read-only input);
#   each keeps the gold body verbatim so the rejection is attributable to the write.
#
# UNGROUNDED-ORACLE-ECHO: N/A as a *wrong* echo. Q4/Q5 are pinned to the @Pure
#   helpers prefix_with_id / tag_open_no_id / tag_close, which are GROUNDED entirely
#   in the input (the constant code-point literals + ToSeq(element_id) / ToSeq(payload),
#   fully unfolded — prefix_with_id(ident) == tag_open_with_id() + ToSeq(ident) +
#   attr_close_and_type()). There is NO @ContractOnly axiom and NO opaque answer-key:
#   the pure region COMPUTES the markup from the arguments, it does not assert an
#   answer. So no value an echo could carry satisfies Q4/Q5 yet is wrong — echoing
#   prefix_with_id(element_id) IS doing the work (it is the literal id-bearing
#   assembly the impl must materialize element-by-element). The honest control is the
#   cheapest faithful impl that builds that grounded output (the positive control
#   below), not a wrong echo. See 'assessment'.
#
# CONTROL-FLOW-EFFECT lane: N/A. build_json_script never raises and has no side
#   effect beyond returning the assembled list; both branches are pure value
#   constructions returned the same way. There is no raise/return fork the value
#   abstraction could miss (unlike a guard function). The branch SELECTION is fully
#   captured by Q4/Q5 (each governs one branch of the presence predicate), so the
#   branch-swap rival below is already a value-level discriminator — no capability
#   token is needed. Omitted as N/A (justified here per directive).
#
# PARTIAL-DOMAIN lane: heavily exercised — the whole behavioural change lives on a
#   sub-domain (the absent/empty-id slice). Rivals:
#     - weak-absent-emits-id   : correct on the PRESENT slice but in the absent
#                                branch emits the id-bearing empty-id tag
#                                '<script id="" type=...>' (the PRE-PATCH behaviour).
#                                Diverges on EXACTLY the F2P (no-id) input. Q5.
#     - weak-present-on-empty  : presence test drops `len>0` (uses `is not None`),
#                                so an EMPTY token ([]) is misclassified as present
#                                and gets '<script id="" type=...>'. Diverges on the
#                                empty-token boundary. Q5 (empty-id falls in absent).
#     - weak-swap-branches     : full inversion (id-free in the present branch,
#                                id-bearing in the absent branch). Q4 and Q5.
#
# AXIOM lane: meta.axioms == [] (NO consumed @ContractOnly axiom). deep_model_references
#   has ONE A-reference: build_json_script itself is the deep model of the real
#   post-patch django.utils.html.json_script (its conditional wrapping + the unchanged
#   wrapper callees format_html / mark_safe). Per PBT_PLAN §2.4 an A-reference deep
#   model is validated == the real callee on every caller-reachable input. The real
#   callee lives only in the instance image, so this probe runs in Docker with the
#   GOLD PATCH APPLIED (apply_gold=True). It re-executes axiom_check.py's logic
#   (embedded verbatim from the HOST at load time, per pilot pitfall #6 — the runner
#   mounts only the probe at /work) — running the REAL json_script and asserting the
#   model's structural assembly matches it character-for-character on boundary +
#   4000 fuzz cases (absent / empty / present id; JSON-script escape payloads). This
#   is the soundness side of the refinement (format_html positional interpolation +
#   mark_safe identity preserve the assembled character structure). A containment
#   probe confirms every caller-reachable id (the tested HTML-special-free tokens +
#   None + empty) lies in the domain where format_html's conditional-escape of the id
#   is the identity, matching the model's literal-id assembly.
from pathlib import Path

INSTANCE = "django__django-15103"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


def _indent(block, n=4):
    """Indent every non-empty line of `block` by n spaces (to nest a top-level
    impl block under a new `if ...:` guard without re-typing it)."""
    pad = " " * n
    return "\n".join((pad + ln) if ln.strip() else ln for ln in block.splitlines())


# The frozen FUNCTION impl region body, verbatim (everything strictly BETWEEN the
# function's `# impl-start` / `# impl-end`, INCLUDING the two nested invariants
# regions). Every spec variant _swap()s ONLY this block, so the edit never touches
# the spec (axioms/pure/pre-/post-conditions regions + the function signature).
# same_spec is computed over the spec_view, which elides every impl region (and the
# nested invariants), so swapping inside here is GUARANTEED same_spec.
_IMPL = """\
    if element_id is not None and len(element_id) > 0:
        # opening tag carrying the identifier, then the media-type attribute
        result = [60, 115, 99, 114, 105, 112, 116, 32, 105, 100, 61, 34]  # type: List[int]
        Assert(ToSeq(result) == tag_open_with_id())
        i = 0
        while i < len(element_id):
            # invariants-start
            Invariant(Acc(list_pred(element_id), 1 / 2))
            Invariant(len(element_id) > 0)
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= i and i <= len(element_id))
            Invariant(ToSeq(result) == tag_open_with_id() + ToSeq(element_id).take(i))
            # the copy loop consumes the caller's termination obligation with a
            # strictly decreasing measure (len(element_id) - i), discharging
            # MustTerminate(2) from the precondition.
            Invariant(MustTerminate(len(element_id) - i + 1))
            # invariants-end
            result.append(element_id[i])
            i = i + 1
        Assert(ToSeq(element_id).take(len(element_id)) == ToSeq(element_id))
        Assert(ToSeq(result) == tag_open_with_id() + ToSeq(element_id))
        result = result + [34, 32, 116, 121, 112, 101, 61, 34, 97, 112, 112,
                           108, 105, 99, 97, 116, 105, 111, 110, 47, 106, 115,
                           111, 110, 34, 62]
        Assert(ToSeq(result) == prefix_with_id(element_id))
        prefix_a = prefix_with_id(element_id)  # type: PSeq[int]
        # append the payload, then the closing tag
        j = 0
        while j < len(payload):
            # invariants-start
            Invariant(Acc(list_pred(payload), 1 / 2))
            Invariant(Acc(list_pred(element_id), 1 / 2))
            Invariant(len(element_id) > 0)
            Invariant(prefix_a == prefix_with_id(element_id))
            Invariant(Acc(list_pred(result)))
            Invariant(0 <= j and j <= len(payload))
            Invariant(ToSeq(result) == prefix_a + ToSeq(payload).take(j))
            # payload copy loop: strictly decreasing measure (len(payload) - j)
            # discharges MustTerminate(2) from the precondition.
            Invariant(MustTerminate(len(payload) - j + 1))
            # invariants-end
            result.append(payload[j])
            j = j + 1
        Assert(ToSeq(payload).take(len(payload)) == ToSeq(payload))
        Assert(ToSeq(result) == prefix_a + ToSeq(payload))
        result = result + [60, 47, 115, 99, 114, 105, 112, 116, 62]
        Assert(ToSeq(result) == prefix_a + ToSeq(payload) + tag_close())
        Assert(ToSeq(result) == prefix_with_id(element_id) + ToSeq(payload) + tag_close())
        return result
    # opening tag carrying ONLY the media-type attribute (no id attribute)
    result = [60, 115, 99, 114, 105, 112, 116, 32, 116, 121, 112, 101,
              61, 34, 97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
              47, 106, 115, 111, 110, 34, 62]
    Assert(ToSeq(result) == tag_open_no_id())
    prefix_b = tag_open_no_id()  # type: PSeq[int]
    # append the payload, then the closing tag
    k = 0
    while k < len(payload):
        # invariants-start
        Invariant(Acc(list_pred(payload), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= k and k <= len(payload))
        Invariant(ToSeq(result) == prefix_b + ToSeq(payload).take(k))
        # payload copy loop: strictly decreasing measure (len(payload) - k)
        # discharges MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(payload) - k + 1))
        # invariants-end
        result.append(payload[k])
        k = k + 1
    Assert(ToSeq(payload).take(len(payload)) == ToSeq(payload))
    result = result + [60, 47, 115, 99, 114, 105, 112, 116, 62]
    Assert(ToSeq(result) == prefix_b + ToSeq(payload) + tag_close())
    Assert(ToSeq(result) == tag_open_no_id() + ToSeq(payload) + tag_close())
    return result"""

assert _BASE.count(_IMPL) == 1, "function impl region drifted from expected text"


def _impl(new_body):
    """Full model.py variant with ONLY the function impl region body replaced."""
    return _swap(_BASE, _IMPL, new_body)


# The verbatim absent-branch tail (the second half of _IMPL: from the id-free tag
# allocation through the final return). Used to build the branch-reorder positive
# control and the branch-swap rival WITHOUT re-typing the long literal arrays.
_ABSENT_TAIL = """\
    # opening tag carrying ONLY the media-type attribute (no id attribute)
    result = [60, 115, 99, 114, 105, 112, 116, 32, 116, 121, 112, 101,
              61, 34, 97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,
              47, 106, 115, 111, 110, 34, 62]
    Assert(ToSeq(result) == tag_open_no_id())
    prefix_b = tag_open_no_id()  # type: PSeq[int]
    # append the payload, then the closing tag
    k = 0
    while k < len(payload):
        # invariants-start
        Invariant(Acc(list_pred(payload), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= k and k <= len(payload))
        Invariant(ToSeq(result) == prefix_b + ToSeq(payload).take(k))
        # payload copy loop: strictly decreasing measure (len(payload) - k)
        # discharges MustTerminate(2) from the precondition.
        Invariant(MustTerminate(len(payload) - k + 1))
        # invariants-end
        result.append(payload[k])
        k = k + 1
    Assert(ToSeq(payload).take(len(payload)) == ToSeq(payload))
    result = result + [60, 47, 115, 99, 114, 105, 112, 116, 62]
    Assert(ToSeq(result) == prefix_b + ToSeq(payload) + tag_close())
    Assert(ToSeq(result) == tag_open_no_id() + ToSeq(payload) + tag_close())
    return result"""

assert _IMPL.count(_ABSENT_TAIL) == 1, "absent-branch tail drifted"

# The verbatim PRESENT branch (the `if ...:` block of _IMPL, indented one level),
# everything up to and including its `return result`. Reused by the reorder control.
_PRESENT_BLOCK = _IMPL[: _IMPL.index("\n" + _ABSENT_TAIL.splitlines()[0])]
assert _PRESENT_BLOCK.startswith("    if element_id is not None and len(element_id) > 0:")
assert _PRESENT_BLOCK.rstrip().endswith("return result")


# ---------------------------------------------------------------------------
# POSITIVE CONTROL (soundness) — must VERIFY.
# ---------------------------------------------------------------------------

# pos-branch-reorder: structurally DIFFERENT but behaviourally identical. The gold
# tests the PRESENT predicate first (fall-through == absent); this reshape tests the
# ABSENT predicate FIRST with an explicit guard, returns the id-free wrapping, then
# runs the (verbatim) PRESENT block in the fall-through (where `element_id is not
# None and len(element_id) > 0` now holds by negation of the absent guard, exactly
# the entry condition the present block already assumes). It keeps EVERY gold proof
# obligation verbatim — both loops, all invariants (incl. the load-bearing
# ToSeq(result)==prefix_a+take(j) and tag_open_with_id()+take(i) ones), every drop/
# take framing assert, and both final-equality asserts. No dropped lemma, no loop-
# direction flip, no forward-append against a front-recursive fold (directive 2/3):
# only the textual order of two independent guarded branches changes. If it FAILS =>
# SPEC-TOO-STRONG (a faithful, structurally-different correct impl rejected).
_POS_REORDER = (
    "    if element_id is None or len(element_id) == 0:\n"
    + _indent(_ABSENT_TAIL, 4)   # nest the id-free build under the new absent guard
    + "\n"
    + _PRESENT_BLOCK             # already top-level-indented (`if element_id is not...`)
)

# Relocate the `# type: List[int]` annotation so it sits on the FIRST `result`
# declaration in this reordered body. In model.py the PRESENT branch (which carries
# the annotation) is textually FIRST, so mypy sees the annotated declaration before
# the un-annotated absent-branch one. Reordering puts the un-annotated absent-branch
# `result` first and the annotated present-branch `result` second; Nagini's mypy
# front-end then rejects the second `# type:` comment as re-annotating an
# already-defined name ("Name 'result' already defined"). This is a textual artifact
# of the reorder, NOT a spec obligation: move the single annotation to the first
# declaration (the no-id literal) and drop it from the second. Behaviour and spec_view
# are unchanged (the annotation lives wholly inside the impl region; both `result`s are
# List[int] either way), so this stays same_spec. Both edits are uniquely-anchored
# inside _POS_REORDER only (the shared _ABSENT_TAIL/_PRESENT_BLOCK constants are not
# touched, so no other case is affected).
_POS_REORDER = _swap(
    _POS_REORDER,
    "                  47, 106, 115, 111, 110, 34, 62]\n"
    "        Assert(ToSeq(result) == tag_open_no_id())",
    "                  47, 106, 115, 111, 110, 34, 62]  # type: List[int]\n"
    "        Assert(ToSeq(result) == tag_open_no_id())",
)
_POS_REORDER = _swap(
    _POS_REORDER,
    "        result = [60, 115, 99, 114, 105, 112, 116, 32, 105, 100, 61, 34]  # type: List[int]",
    "        result = [60, 115, 99, 114, 105, 112, 116, 32, 105, 100, 61, 34]",
)


# admiss-shape: an admissibility positive control. The precondition is the two
# half-permission grants (Acc(list_pred(payload),1/2) and the conditional
# Acc(list_pred(element_id),1/2)). This control keeps the gold impl VERBATIM but
# FIRST asserts, under those half-permissions, the reads a normal F2P-shaped input
# needs: the payload length is readable, the element_id may be None (the F2P no-id
# call), and when an id IS supplied its length/first element are readable. No write,
# so no extra permission demand. If the precondition could not admit a legitimate
# (payload, optional-id) input, this would fail => PRECOND-TOO-STRONG.
_ADMISS = (
    "    # Admissibility: a normal (payload, optional element_id) input is in-domain;\n"
    "    # the half-permissions admit reading the lengths and elements; element_id\n"
    "    # may be None (the F2P no-id call) or a present token.\n"
    "    Assert(len(payload) >= 0)   # payload read admitted under Acc(...,1/2)\n"
    "    if element_id is not None:\n"
    "        Assert(len(element_id) >= 0)   # id read admitted under Acc(...,1/2)\n"
    "        if len(element_id) > 0:\n"
    "            Assert(element_id[0] == element_id[0])\n"
    + _IMPL
)


# ---------------------------------------------------------------------------
# FRAME-MUTATION RIVALS (MANDATORY — both inputs are Acc(...,1/2) read-only).
# Must be REJECTED for INSUFFICIENT PERMISSION.
# ---------------------------------------------------------------------------

# frame-mut-payload: keeps the gold body VERBATIM (so the rejection is attributable
# SOLELY to the added write, not to a value mismatch), then APPENDS to the read-only
# input `payload` — a mutation demanding FULL write permission, granted only at 1/2.
# Placed FIRST so it is always reachable (no guard needed; append works on any list).
# The real json_script never mutates its serialized payload (a str/SafeString is
# immutable); any write to the carrier would be unfaithful and could corrupt a
# caller's live list. The verifier must reject for insufficient permission.
_FRAME_MUT_PAYLOAD = (
    "    # Frame violation: write into the read-only (Acc(...,1/2)) payload input.\n"
    "    payload.append(0)\n"
    + _IMPL
)

# frame-mut-element_id: the dual — keeps the gold body verbatim, then WRITES into the
# read-only `element_id` input (Acc(...,1/2) when present). Guarded by `is not None
# and len>0` so the store element_id[0]=element_id[0] is reachable on a present-id
# F2P input (e.g. 'test_id') yet only ever a no-op value; the point is it demands
# FULL write permission on element_id, which the caller granted only at 1/2. The real
# json_script only READS element_id (format_html interpolates it); any write would be
# unfaithful. The verifier must reject for insufficient permission.
_FRAME_MUT_EID = (
    "    if element_id is not None and len(element_id) > 0:\n"
    "        # Frame violation: write into the read-only (Acc(...,1/2)) element_id.\n"
    "        element_id[0] = element_id[0]\n"
    + _IMPL
)


# ---------------------------------------------------------------------------
# UNIQUENESS / PARTIAL-DOMAIN RIVALS — must be REJECTED (else SPEC-TOO-WEAK).
# Each shares the frozen spec exactly; only the impl changes.
# ---------------------------------------------------------------------------

# weak-absent-emits-id: PARTIAL-DOMAIN. The PRESENT branch is the gold block verbatim
# (correct on the present slice), but the ABSENT branch builds the id-BEARING tag
# with an EMPTY id value: '<script id="" type="application/json">' + payload +
# '</script>'. This is EXACTLY the pre-patch behaviour (model_prepatch.py always
# emits the id-bearing template). It diverges on precisely the F2P no-id input. The
# absent branch is assembled with the same forward-append loop shape but starting
# from tag_open_with_id() + attr_close_and_type() (id="" with nothing between the
# quotes), so it is a faithful, internally-consistent build — but its OUTPUT is the
# id-bearing empty-id tag, which violates Q5.
_WEAK_ABSENT_EMITS_ID = _swap(
    _IMPL,
    "    # opening tag carrying ONLY the media-type attribute (no id attribute)\n"
    "    result = [60, 115, 99, 114, 105, 112, 116, 32, 116, 121, 112, 101,\n"
    "              61, 34, 97, 112, 112, 108, 105, 99, 97, 116, 105, 111, 110,\n"
    "              47, 106, 115, 111, 110, 34, 62]\n"
    "    Assert(ToSeq(result) == tag_open_no_id())\n"
    "    prefix_b = tag_open_no_id()  # type: PSeq[int]\n",
    # id-bearing empty-id tag: '<script id="" type="application/json">' i.e.
    # tag_open_with_id() (...'<script id="') immediately followed by
    # attr_close_and_type() ('" type="application/json">') -- an empty id value.
    "    # PRE-PATCH bug: the absent branch ALSO emits the id-bearing tag, with an\n"
    "    # EMPTY id value ('<script id=\"\" type=\"application/json\">'). This violates\n"
    "    # Q5, which demands the id-FREE tag_open_no_id() when no id is supplied.\n"
    "    result = [60, 115, 99, 114, 105, 112, 116, 32, 105, 100, 61, 34,\n"
    "              34, 32, 116, 121, 112, 101, 61, 34, 97, 112, 112, 108,\n"
    "              105, 99, 97, 116, 105, 111, 110, 47, 106, 115, 111, 110, 34, 62]\n"
    "    prefix_b = tag_open_with_id() + attr_close_and_type()  # type: PSeq[int]\n"
    "    Assert(ToSeq(result) == prefix_b)\n",
)

# weak-present-on-empty: PARTIAL-DOMAIN on the empty-token boundary. The branch guard
# drops the `len > 0` test (uses only `is not None`), so an EMPTY token (element_id ==
# []) is misclassified as PRESENT and routed into the id-bearing branch, producing
# '<script id="" type=...>'. But under the frozen spec an empty token is ABSENT
# (Q5 governs `element_id is None or len(element_id) == 0`), which demands the id-FREE
# tag. The present-branch body is otherwise the gold block, but its first loop and the
# `Invariant(len(element_id) > 0)` no longer hold for an empty id — so the rival
# CANNOT even establish its own invariants on the empty-token input it now (wrongly)
# routes there; whichever way the verifier resolves it, Q5 is unmet for [].
_WEAK_PRESENT_ON_EMPTY = _swap(
    _IMPL,
    "    if element_id is not None and len(element_id) > 0:\n",
    "    if element_id is not None:\n",
)

# vac-nonterm: VACUOUS NON-TERMINATION — an impl that never returns. It spins
# forever (while cont with cont never cleared), so every value postcondition is
# satisfiable only vacuously: no execution reaches the return. This is the exact
# spec-too-weak class the G-PANEL-1 auditor exploited before the MustTerminate
# obligation was added (atk_8: an infinite `while cont:` loop appending 0 forever
# verified against the value-only spec, and its faithful real patch — json_script
# looping forever — hangs every F2P/P2P test). Under Requires(MustTerminate(2))
# the loop takes no termination obligation and has no decreasing measure, so
# Nagini's obligation system MUST reject it ("Obligation leak check failed").
# The invariants are relaxed to what the spinning loop maintains — the reject
# must come from the obligation system, not a broken proof of a correct impl.
_NONTERM = """\
    result = []  # type: List[int]
    cont = True
    while cont:
        # invariants-start
        Invariant(Acc(list_pred(result)))
        Invariant(cont)
        # invariants-end
        result.append(0)
    return result"""

# weak-swap-branches: full INVERSION via a single guard flip. The id-BEARING block
# (which builds prefix_with_id(element_id) + payload + tag_close()) is routed to the
# ABSENT predicate `element_id is None or len(element_id) == 0`, and the id-FREE
# fall-through then runs on the PRESENT inputs. So a present id gets the id-free tag
# and an absent/empty id gets the id-bearing tag — both wrong. Its faithful real patch
# is `if not element_id:` selecting the id-bearing template (the exact opposite of the
# gold `if element_id:`), so every F2P/P2P fails. A single _swap on the guard keeps the
# variant valid Python (the body is unchanged); it cannot verify because for an absent
# id the id-bearing block can neither build the id-bearing output Q5 forbids nor even
# establish its own `len(element_id) > 0` invariant.
_WEAK_SWAP = _swap(
    _IMPL,
    "    if element_id is not None and len(element_id) > 0:\n",
    "    if element_id is None or len(element_id) == 0:\n",
)


SPEC_TESTS = [
    {
        "id": "pos-branch-reorder",
        "kind": "soundness",
        "expect": "verify",
        "module": _impl(_POS_REORDER),
        "rationale": (
            "structurally-different but CORRECT impl: tests the ABSENT predicate "
            "first (`if element_id is None or len(element_id) == 0:`), returns the "
            "id-free wrapping, then runs the VERBATIM present block in the fall-through "
            "(where the present entry condition holds by negation of the absent guard). "
            "Both loops, every invariant (incl. ToSeq(result)==tag_open_with_id()+"
            "take(i) and ==prefix_a+take(j)), every drop/take framing assert, and both "
            "final-equality asserts are kept verbatim — no dropped lemma, no loop-"
            "direction flip, no forward-append against a front-recursive fold. Only the "
            "textual order of two independent guarded branches changes. If it FAILS => "
            "SPEC-TOO-STRONG (a faithful correct impl is rejected)."
        ),
    },
    {
        "id": "admiss-shape",
        "kind": "admissibility",
        "expect": "verify",
        "module": _impl(_ADMISS),
        "rationale": (
            "the precondition (Acc(list_pred(payload),1/2) + the conditional "
            "Acc(list_pred(element_id),1/2)) must admit a normal F2P-shaped input: the "
            "payload length is readable, element_id may be None (the F2P no-id call), "
            "and a supplied id's length/first element are readable under the half-"
            "permission. The gold impl is otherwise verbatim (only reads/asserts added "
            "inside the impl region, no write). If it FAILS => PRECOND-TOO-STRONG."
        ),
    },
    {
        "id": "frame-mut-payload",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT_PAYLOAD),
        "refinement": (
            "the gold json_script never mutates its serialized payload — json_str is a "
            "Python str (immutable), interpolated by format_html and wrapped by "
            "mark_safe (identity on content). A faithful real patch does not (and "
            "cannot) append to it; any write to the List[int] carrier would be "
            "unfaithful to the gold and could corrupt a caller's live argument. Such a "
            "rival is not the gold patch and would not faithfully resolve."
        ),
        "rationale": (
            "REJECTED by the PERMISSION SYSTEM: `payload` is granted at "
            "Acc(list_pred(payload),1/2) (P1); the store payload.append(0) demands FULL "
            "write permission, which is not available, so the verifier rejects for "
            "INSUFFICIENT PERMISSION. The gold body is kept verbatim so the rejection "
            "is attributable solely to the write. If it VERIFIES => the read-only frame "
            "on payload is hollow (frame-mutation, the #1 weakness class; a byte-fuzzer "
            "never thinks to mutate the input)."
        ),
    },
    {
        "id": "frame-mut-element_id",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_FRAME_MUT_EID),
        "refinement": (
            "the gold json_script only READS element_id (format_html interpolates it "
            "into the template); it never mutates it, and a str id is immutable anyway. "
            "A faithful real patch performs no write to element_id; a rival that did "
            "would diverge from the gold (and could corrupt a caller's argument), so it "
            "is not the gold patch and would not faithfully resolve."
        ),
        "rationale": (
            "REJECTED by the PERMISSION SYSTEM: `element_id` is granted at "
            "Acc(list_pred(element_id),1/2) when present (P2); the store "
            "element_id[0]=element_id[0] (guarded by is-not-None-and-len>0, reachable "
            "on a present-id F2P input) demands FULL write permission, not available, "
            "so the verifier rejects for INSUFFICIENT PERMISSION. The gold body is kept "
            "verbatim so the rejection is attributable solely to the write. If it "
            "VERIFIES => the read-only frame on element_id is hollow (frame-mutation, "
            "the #1 weakness class)."
        ),
    },
    {
        "id": "weak-absent-emits-id",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_ABSENT_EMITS_ID),
        "refinement": (
            "this IS the pre-patch behaviour (model_prepatch.py): the no-id case emits "
            "the id-bearing template with an empty id value, '<script id=\"\" "
            "type=\"application/json\">' + payload + '</script>'. Its faithful real "
            "patch is the UNCHANGED repo (always format_html('<script id=\"{}\" "
            "type=\"application/json\">{}</script>', element_id, ...)), which on the F2P "
            "no-id call renders '<script id=\"\" ...>' — not the id-free tag the F2P "
            "test_without_id / test_json_script_without_id assert. Does NOT resolve — "
            "exactly the change the spec senses (G-DIFF)."
        ),
        "rationale": (
            "REJECTED by Q5 (Ensures(Implies(element_id is None or len(element_id)==0, "
            "ToSeq(Result()) == tag_open_no_id() + ToSeq(payload) + tag_close()))): on "
            "the absent input the rival returns the id-BEARING empty-id tag "
            "(tag_open_with_id()+attr_close_and_type()+payload+tag_close()), whose "
            "prefix is tag_open_with_id()+attr_close_and_type() != tag_open_no_id() "
            "(the former still contains the ' id=\"\"' segment). Measured verbatim: "
            "`Assert might fail. Assertion (ToSeq(result) == ((tag_open_no_id() + "
            "ToSeq(payload)) + tag_close()))` at model.py:190, which is Q5's "
            "consequent restated inline in the absent-id branch of the impl, so the "
            "refutation is Q5's, reported at the hint that states it. "
            "PARTIAL-DOMAIN: correct "
            "on the present slice, wrong on the absent slice. If it VERIFIES => "
            "SPEC-TOO-WEAK (the id-omission is not enforced)."
        ),
    },
    {
        "id": "weak-present-on-empty",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_PRESENT_ON_EMPTY),
        "refinement": (
            "dropping the `len > 0` test (using only `element_id is not None`) is what "
            "a real patch keying on identity-not-truthiness (`if element_id is not "
            "None:` instead of the gold `if element_id:`) would do. On an empty token "
            "it would render '<script id=\"\" type=...>' rather than the id-free tag. "
            "While the headline F2P passes element_id=None (also routed correctly here), "
            "the gold's truthiness contract (empty == absent) is what the optionality "
            "fix promises; a patch that emits id=\"\" for the empty string is not the "
            "gold and breaks the documented 'optional id' behaviour on that boundary."
        ),
        "rationale": (
            "REJECTED by Q5 on the empty-token sub-domain: for element_id == [] the "
            "spec (element_id is None OR len==0) demands tag_open_no_id(), but the rival "
            "routes [] into the id-bearing branch. That branch also cannot establish its "
            "own Invariant(len(element_id) > 0) for an empty id, so the variant fails "
            "for an empty token regardless. PARTIAL-DOMAIN on the empty-token boundary. "
            "If it VERIFIES => SPEC-TOO-WEAK (the empty==absent refinement is unpinned)."
        ),
    },
    {
        "id": "vac-nonterm",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_NONTERM),
        "refinement": (
            "an impl that never returns is the G-PANEL-1 atk_8 rival: its faithful "
            "real patch replaces json_script's body with an infinite "
            "`while cont: result.append(0)` loop, so every F2P/P2P test that calls "
            "json_script hangs (the run_instance log shows exactly that patch "
            "failing to resolve). It satisfies the value postconditions only "
            "vacuously — no execution reaches the return — so it is not the gold "
            "patch and does not resolve."
        ),
        "rationale": (
            "REJECTED by the OBLIGATION SYSTEM: the precondition carries "
            "Requires(MustTerminate(2)), a total-correctness obligation every loop "
            "must consume with a strictly decreasing measure. The spinning "
            "`while cont:` loop declares no MustTerminate invariant and has no "
            "decreasing measure, so Nagini reports 'Obligation leak check failed. "
            "Loop might not take all unsatisfied obligations from the context.' "
            "(replayed locally: rejected in ~16s). If it VERIFIES => SPEC-TOO-WEAK "
            "(the vacuous non-termination hole is open again)."
        ),
    },
    {
        "id": "weak-swap-branches",
        "kind": "uniqueness",
        "expect": "reject",
        "module": _impl(_WEAK_SWAP),
        "refinement": (
            "inverting the predicate (`if not element_id:` selecting the id-bearing "
            "template, else the id-free one) is the exact opposite of the gold `if "
            "element_id:`. Every present-id call (e.g. the P2P test_json_script with "
            "'test_id') would render the id-FREE tag and every no-id F2P call would "
            "render the id-BEARING (empty-id) tag — both wrong. Fails every F2P and "
            "P2P. Does NOT resolve."
        ),
        "rationale": (
            "REJECTED by BOTH branches of the spec. The single guard flip routes the "
            "id-bearing block (which builds prefix_with_id(element_id)+payload+"
            "tag_close()) to the ABSENT predicate and the id-free fall-through to the "
            "PRESENT inputs. (a) A present id reaches the id-free fall-through "
            "returning tag_open_no_id()+payload+tag_close(), but Q4 demands "
            "prefix_with_id(element_id)+... (carries the id segment) — violated. (b) An "
            "absent/empty id reaches the id-bearing block, which cannot establish its "
            "Invariant(len(element_id) > 0) (element_id is None or len==0) and could "
            "not satisfy Q5's tag_open_no_id() anyway. A full value-level inversion. If "
            "it VERIFIES => SPEC-TOO-WEAK (the branch selection is unpinned)."
        ),
    },
]


# ---------------------------------------------------------------------------
# AXIOM lane — the A-reference deep model build_json_script vs the REAL post-patch
# django.utils.html.json_script. meta.axioms == [] (NO consumed @ContractOnly axiom);
# deep_model_references has ONE A-reference (build_json_script models json_script's
# conditional wrapping + the unchanged format_html / mark_safe callees). Per
# PBT_PLAN §2.4 / §4a an A-reference deep model is validated == the real callee on
# every caller-reachable input. The real callee lives ONLY in the instance image, so
# these probes run in Docker with the GOLD PATCH APPLIED (apply_gold=True). They embed
# axiom_check.py's reference encodings + assembly (read from the HOST at load time per
# pilot pitfall #6 — the runner mounts only the probe at /work) and EXECUTE the real
# json_script (pitfall #4: call the callee, never scrape source). Files would be read
# with encoding utf-8 if any were opened (pitfall #5) — none are.
# ---------------------------------------------------------------------------

# Shared Django setup + model reference assembly + real_payload, transcribed from
# axiom_check.py (kept in lock-step with model.py's @Pure encodings).
_AX_PREAMBLE = '''
import json
import random
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(USE_I18N=False)
django.setup()

from django.core.serializers.json import DjangoJSONEncoder
from django.utils.html import _json_script_escapes, json_script

# --- model.py reference encodings (in lock-step with the spec @Pure helpers) ---
_TAG_OPEN_WITH_ID = [ord(c) for c in '<script id="']
_ATTR_CLOSE_AND_TYPE = [ord(c) for c in '" type="application/json">']
_TAG_OPEN_NO_ID = [ord(c) for c in '<script type="application/json">']
_TAG_CLOSE = [ord(c) for c in '</script>']


def build_json_script(payload, element_id):
    """Reference of model.py build_json_script as a list of code points; element_id
    may be None (absent). Present iff non-None and non-empty (empty == absent)."""
    present = element_id is not None and len(element_id) > 0
    if present:
        prefix = _TAG_OPEN_WITH_ID + list(element_id) + _ATTR_CLOSE_AND_TYPE
    else:
        prefix = list(_TAG_OPEN_NO_ID)
    return prefix + list(payload) + _TAG_CLOSE


def real_payload(value):
    return json.dumps(value, cls=DjangoJSONEncoder).translate(_json_script_escapes)
'''

_AX_SOUND_PROBE = _AX_PREAMBLE + '''

def check_one(value, element_id_str):
    payload = [ord(c) for c in real_payload(value)]
    eid = None if element_id_str is None else [ord(c) for c in element_id_str]
    expected = build_json_script(payload, eid)                     # model
    if element_id_str is None:
        observed_str = json_script(value)                          # REAL callee, no id
    else:
        observed_str = json_script(value, element_id_str)          # REAL callee, with id
    observed = [ord(c) for c in str(observed_str)]
    return observed == expected, observed_str, expected


# HTML-special-free id tokens (the tested usage): format_html's conditional_escape of
# such an id is the identity, matching the model's literal-id assembly.
id_alphabet = ("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")

values = [
    {}, [], "", "x", 0, 1, True, False, None,
    {"key": "value"},
    {"a": "<script>test&ing</script>"},
    "&<>",
    "a<b>&",
    {"a": "testing\\r\\njson 'string\\" <b>escaping</b>"},
    ["<", ">", "&", "plain"],
    {"nested": {"u": "  "}},
    "quotes \\" and ' apostrophe",
]

fails = 0
n = 0
# boundary: absent id (None), empty id (""), present ids
boundary_ids = [None, "", "test_id", "x", "a", "ID-42", "_priv"]
for v in values:
    for eid in boundary_ids:
        ok, obs, exp = check_one(v, eid)
        n += 1
        if not ok:
            fails += 1
            print("AXIOM-UNSOUND value=%r id=%r: real=%r model=%r"
                  % (v, eid, str(obs), "".join(chr(c) for c in exp)))

# randomized fuzz
rng = random.Random(15103)
for _ in range(4000):
    v = rng.choice(values)
    choice = rng.randint(0, 2)
    if choice == 0:
        eid = None
    elif choice == 1:
        eid = ""               # empty token -> treated as absent
    else:
        m = rng.randint(1, 12)
        eid = "".join(rng.choice(id_alphabet) for _ in range(m))
    ok, obs, exp = check_one(v, eid)
    n += 1
    if not ok:
        fails += 1
        print("AXIOM-UNSOUND fuzz value=%r id=%r: real=%r model=%r"
              % (v, eid, str(obs), "".join(chr(c) for c in exp)))

# the discriminating F2P facts, explicitly
no_id = str(json_script({}))
if no_id != '<script type="application/json">{}</script>':
    fails += 1
    print("FACT FAIL: json_script({}) no-id =>", repr(no_id))
with_id = str(json_script({"key": "value"}, "test_id"))
if with_id != '<script id="test_id" type="application/json">{"key": "value"}</script>':
    fails += 1
    print("FACT FAIL: json_script with id =>", repr(with_id))

if fails:
    print("AXIOM-SOUNDNESS FAIL: %d disagreement(s) between deep build_json_script "
          "and real django.utils.html.json_script" % fails)
    sys.exit(1)
print("AXIOM-SOUNDNESS OK: deep build_json_script == real post-patch json_script on "
      "%d boundary + fuzz cases (absent / empty / present id; JSON-script escape "
      "payloads); F2P no-id => id-free tag, present id => id-bearing tag." % n)
sys.exit(0)
'''

_AX_COVER_PROBE = _AX_PREAMBLE + '''

# (axiom-containment) Which callee-inputs can the MODEL actually reach?
# build_json_script applies the wrapper assumption (format_html positional
# interpolation + mark_safe identity) to:
#   * element_id : None (absent), or a non-empty token. In the tested usage the id is
#                  an HTML-special-free token, for which format_html's
#                  conditional_escape is the IDENTITY (matching the model's literal-id
#                  assembly). The model never produces an id containing HTML-special
#                  chars (the tests use only such tokens; the optionality fix does not
#                  introduce special-char ids).
#   * payload    : the already-serialized + JSON-script-escaped string, which by
#                  construction (str.translate(_json_script_escapes)) contains NO raw
#                  HTML-special < > & (they are pre-escaped to \\u003C etc.), so
#                  format_html's interpolation of mark_safe(json_str) is the identity.
# CONTAINMENT holds iff for every reachable (payload, id) the real callee's escaping
# is the identity on both operands (so the literal assembly == the real output). We
# CONFIRM by running the REAL callee on a heavy sample of the reachable id/payload
# space and asserting the model agrees AND that the id appears verbatim in the output
# whenever present (no escaping applied). Covering MORE (e.g. special-char ids the
# model never reaches) than the caller reaches would be sound, not a defect.
fails = 0
n = 0

id_alphabet = ("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_")
values = [
    {}, [], "", "x", 0, 1, True, False, None,
    {"key": "value"}, {"a": "<script>test&ing</script>"}, "&<>", "a<b>&",
    {"a": "testing\\r\\njson 'string\\" <b>escaping</b>"},
    ["<", ">", "&", "plain"], {"nested": {"u": "  "}}, "quotes \\" and ' apostrophe",
]

rng = random.Random(2024)


def reachable_ids():
    yield None
    yield ""
    for _ in range(2000):
        m = rng.randint(1, 16)
        yield "".join(rng.choice(id_alphabet) for _ in range(m))


for eid in reachable_ids():
    for v in values:
        payload = [ord(c) for c in real_payload(v)]
        e = None if eid is None else [ord(c) for c in eid]
        expected = build_json_script(payload, e)
        observed = [ord(c) for c in str(json_script(v) if eid is None
                                        else json_script(v, eid))]
        n += 1
        if observed != expected:
            fails += 1
            print("CONTAINMENT FAIL: reachable id=%r value=%r outside identity domain "
                  "(model != real)" % (eid, v))
            continue
        # when present, the id must appear VERBATIM (escaping was the identity)
        if eid:
            out = str(json_script(v, eid))
            if ('id="%s"' % eid) not in out:
                fails += 1
                print("CONTAINMENT FAIL: id %r not verbatim in output %r" % (eid, out))

if fails:
    print("AXIOM-CONTAINMENT FAIL: %d reachable callee-input(s) where the wrapper "
          "escaping is NOT the identity (model != real)" % fails)
    sys.exit(1)
print("AXIOM-CONTAINMENT OK: every caller-reachable (payload, id) — None / empty / "
      "HTML-special-free token id, pre-escaped JSON payload — lies in the domain where "
      "format_html+mark_safe escaping is the identity; the deep model matches the real "
      "json_script and the id is emitted verbatim on %d cases." % n)
sys.exit(0)
'''


AXIOM_TESTS = [
    {
        "id": "ax-sound-build_json_script",
        "axiom": "build_json_script",
        "kind": "axiom-soundness",
        "expect": "holds",
        "apply_gold": True,
        "probe": _AX_SOUND_PROBE,
        "rationale": (
            "build_json_script is an A-reference deep model of the real post-patch "
            "django.utils.html.json_script (no consumed @ContractOnly axiom in this "
            "bundle). AXIOM-SOUNDNESS: the deep model's structural assembly must equal "
            "the REAL callee character-for-character on every caller-reachable input. "
            "The probe (apply_gold=True) executes the live json_script on boundary "
            "(absent/empty/present id; JSON-script escape payloads > < &) + 4000 fuzz "
            "cases and asserts agreement, plus the explicit F2P facts (no-id => id-free "
            "tag; present id => id-bearing tag). Mirrors axiom_check.py / G-AX. If the "
            "real callee disagrees anywhere => AXIOM-UNSOUND (the format_html/mark_safe "
            "structure-preservation refinement is false)."
        ),
    },
    {
        "id": "ax-cover-build_json_script",
        "axiom": "build_json_script",
        "kind": "axiom-containment",
        "expect": "covered",
        "apply_gold": True,
        "probe": _AX_COVER_PROBE,
        "rationale": (
            "AXIOM-CONTAINMENT: build_json_script's wrapper assumption (format_html "
            "positional interpolation + mark_safe identity) is sound only where the "
            "real callee's conditional-escape is the IDENTITY on both operands. The "
            "model reaches only: ids that are None / empty / HTML-special-free tokens "
            "(the tested usage), and payloads that are already JSON-script-escaped "
            "(str.translate pre-escapes < > & to \\u003C..., so no raw special chars). "
            "The probe samples that reachable space heavily and asserts the real "
            "json_script's output equals the literal assembly AND the present id "
            "appears verbatim (escaping == identity). A reachable input where escaping "
            "is NOT the identity => AXIOM-TOO-WEAK-FOR-CALLER (none expected; covering "
            "special-char ids the model never reaches would be sound, not a defect)."
        ),
    },
]
