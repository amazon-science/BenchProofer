# properties.py — PBT manifest for django__django-12262. NOT a Nagini module; a
# record of adversarial, instance-specific falsification cases. The runner
# (swebench_nagini.pbt) writes each `module` to a temp file, runs the Nagini
# verifier on the host, and checks markers.same_spec against the frozen model.py.
#
# Defended surface (read from model.py + meta.json + refinement.md):
#   bind_keywords(supplied: List[int],          # READ-ONLY  Acc(list_pred,1/2)
#                 positional: PSeq[int],
#                 keyword_only: PSeq[int],
#                 keyword_only_with_default: PSeq[int],
#                 catch_all: bool) -> int
#   Load-bearing postcondition (line 137):
#       Result() == outcome(ToSeq(supplied), PSeq(0).take(0),
#                           positional, keyword_only, catch_all)
#   plus the frame postcondition  Ensures(Acc(list_pred(supplied), 1/2))
#   and the totality obligation   Requires(MustTerminate(2))  (line 127),
#   discharged in the loop by Invariant(MustTerminate(len(supplied) - i + 1)):
#   the binder must actually ANSWER (Nagini is partial-correctness by default,
#   so without it a diverging impl satisfies the postcondition vacuously).
#   `outcome` is a @Pure front-recursive fold FULLY GROUNDED in the args (no
#   @ContractOnly axiom) -> there is no "wrong echo": echoing the oracle IS the
#   correct answer. So the ungrounded-oracle-echo class does NOT apply; instead
#   we ship an honest cheapest-impl positive control (pos-control-baseline) and
#   attack the semantics directly.
#
# Discriminating behaviour the spec pins:
#   * code 1 UNEXPECTED iff the first problematic keyword names NO declared param
#     (positional OR keyword-only, DEFAULT-INDEPENDENT) and there is no catch-all;
#   * code 2 DUPLICATE iff the first problematic keyword repeats an already-bound
#     name; UNEXPECTED is checked before DUPLICATE but on the FIRST problematic
#     keyword the two are mutually exclusive (an unacceptable name is never bound);
#   * code 0 OK otherwise.
#   The gold fix tests membership in the FULL keyword_only set, NOT the required
#   subset that excludes defaulted keyword-only names (keyword_only_with_default).
#
# Region-surgery discipline: every variant is built by _swap() on the frozen
# model.py text, editing ONLY inside the # impl-start / # impl-end region (lines
# 140-171, invariants nested at 144-159). The spec_view elides that whole span,
# so same_spec is GUARANTEED for every spec case.
from pathlib import Path

INSTANCE = "django__django-12262"
FLOAT_ENCODING = None  # meta.json float_encoding is null (unused)

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError(f"drift: {old!r}")
    if src.count(old) != 1:
        raise AssertionError(f"not unique: {old!r}")
    return src.replace(old, new, 1)


# ---------------------------------------------------------------------------
# Anchors that live INSIDE the impl region (verified unique below).
# ---------------------------------------------------------------------------
_LOOP_HEADER = "    i = 0\n    while i < len(supplied):"
_GUARD_UNEXPECTED = (
    "        if not acceptable(positional, keyword_only, catch_all, name):\n"
    "            return 1\n")
_GUARD_DUPLICATE = (
    "        if contains(seen, name):\n"
    "            return 2\n")


# ===========================================================================
# 1. FRAME-MUTATION (MANDATORY: `supplied` is read-only, Acc(list_pred,1/2)).
#    A rival that WRITES to `supplied` to do its work. With only 1/2 permission
#    a write (append) is impossible; Nagini must reject for INSUFFICIENT
#    PERMISSION. All gold guards/invariants/asserts are kept verbatim so the
#    rejection is attributable solely to the write, not to a logic change.
# ===========================================================================
_frame_mut = _swap(
    _BASE, _LOOP_HEADER,
    "    i = 0\n"
    "    supplied.append(0)  # frame-mutation: needs FULL list_pred, only 1/2 held\n"
    "    while i < len(supplied):")


# ===========================================================================
# 2. PARTIAL-DOMAIN — pre-patch default-acceptance bug (the actual reverted edit).
#    Tests acceptability against the REQUIRED keyword-only subset (kwonly minus
#    defaulted names minus already-bound names = the live `unhandled_kwargs`)
#    instead of the FULL keyword_only set. A defaulted keyword-only name supplied
#    once is then classified UNEXPECTED (code 1) instead of OK (code 0).
#    Refinement: this IS model_prepatch.py's decision (the pre-patch condition
#    `param not in unhandled_kwargs`); its faithful real patch raises
#    "unexpected keyword argument" for `{% simple_keyword_only_default kwarg=37 %}`
#    -> FAILS F2P test_simple_tags / test_inclusion_tags. Witness: supplied=[1],
#    positional=[], keyword_only=[1], keyword_only_with_default=[1], catch_all=F
#    -> spec/outcome=0, rival=1.
# ===========================================================================
_prepatch_default = _swap(
    _BASE, _GUARD_UNEXPECTED,
    "        still_required = (contains(keyword_only, name)\n"
    "                          and not contains(keyword_only_with_default, name)\n"
    "                          and not contains(seen, name))\n"
    "        if not (catch_all or contains(positional, name) or still_required):\n"
    "            return 1\n")


# ===========================================================================
# 3. CONTROL-FLOW / VALUE — DUPLICATE collapsed into UNEXPECTED.
#    Returns code 1 for the repeated-acceptable-keyword case instead of code 2.
#    Refinement: a real patch that raised the "unexpected keyword argument"
#    message (or any non-"multiple values" outcome) for a doubly-supplied
#    keyword-only param FAILS the F2P assertions that pin the
#    "received multiple values for keyword argument 'kwarg'" message
#    (test_simple_tag_errors / test_inclusion_tag_errors). Witness:
#    supplied=[1,1], keyword_only=[1], catch_all=F -> spec=2, rival=1.
# ===========================================================================
_dup_as_unexpected = _swap(
    _BASE, _GUARD_DUPLICATE,
    "        if contains(seen, name):\n"
    "            return 1\n")


# ===========================================================================
# 4. PARTIAL-DOMAIN — catch-all ignored.
#    Drops the `catch_all` disjunct from the acceptability test, so a callable
#    with a **kwargs catch-all that receives an extra/unknown keyword is wrongly
#    classified UNEXPECTED (code 1) instead of OK (code 0).
#    Refinement: the real patch would raise on a custom tag declaring **kwargs
#    that legitimately accepts arbitrary keywords -> breaks the
#    `simple_unlimited_args_kwargs` family in PASS_TO_PASS (which relies on a
#    catch-all accepting extra keyword arguments). Witness: supplied=[9],
#    keyword_only=[], positional=[], catch_all=T -> spec=0, rival=1.
# ===========================================================================
_ignore_catchall = _swap(
    _BASE, _GUARD_UNEXPECTED,
    "        if not (contains(positional, name) or contains(keyword_only, name)):\n"
    "            return 1\n")


# ===========================================================================
# 5. MECHANICAL SUPPORTING near-miss — always-OK (never raises).
#    Removes both early-return guards: every input returns code 0.
#    Refinement: a real patch that never raises would let every malformed tag
#    invocation through -> all error F2P (test_simple_tag_errors,
#    test_inclusion_tag_errors) and the UNEXPECTED P2P checks fail. Witness:
#    supplied=[9], catch_all=F -> spec=1, rival=0.  (Cheap supporting case; the
#    reasoned attacks above are the primary battery.)
# ===========================================================================
_always_ok = _swap(
    _swap(_BASE, _GUARD_UNEXPECTED, ""),
    _GUARD_DUPLICATE, "")


# ===========================================================================
# 5b. NON-TERMINATION — diverges instead of answering (the audit's P1 attack).
#    Keeps the loop, the frame, and every value invariant verbatim, but never
#    advances `i` (and never returns from inside the loop): on any nonempty
#    `supplied` the loop spins forever, so every value postcondition holds only
#    vacuously. Nagini is a partial-correctness verifier by default; before the
#    spec carried MustTerminate this variant VERIFIED (the G-PANEL-1 finding).
#    Now the termination obligation Requires(MustTerminate(2)) must be
#    discharged by a strictly decreasing loop measure, which this variant
#    cannot supply -> "Loop might not keep promise to terminate".
#    Refinement: its faithful real patch inserts an endless loop into
#    parse_bits' keyword scan; template compilation for `{% simple_one_default
#    one=1 %}` (any tag with a kwarg) hangs, so every F2P/P2P custom-tag test
#    times out. It does not resolve.
# ===========================================================================
_IMPL_REGION_OLD = _BASE[_BASE.index("    # impl-start"):
                         _BASE.index("    # impl-end") + len("    # impl-end")]
_diverge = _BASE.replace(
    _IMPL_REGION_OLD,
    "    # impl-start\n"
    "    seen = PSeq(0).take(0)  # type: PSeq[int]\n"
    "    i = 0\n"
    "    while i < len(supplied):\n"
    "        # invariants-start\n"
    "        Invariant(Acc(list_pred(supplied), 1 / 2))\n"
    "        Invariant(0 <= i and i <= len(supplied))\n"
    "        Invariant(seen == ToSeq(supplied).take(i))\n"
    "        Invariant(outcome(ToSeq(supplied), PSeq(0).take(0),\n"
    "                          positional, keyword_only, catch_all) ==\n"
    "                  outcome(ToSeq(supplied).drop(i), seen,\n"
    "                          positional, keyword_only, catch_all))\n"
    "        Invariant(MustTerminate(len(supplied) - i + 1))\n"
    "        # invariants-end\n"
    "        i = i + 0  # never advances: diverges on any nonempty run\n"
    "    return 0\n"
    "    # impl-end", 1)
if _diverge == _BASE:
    raise AssertionError("drift: impl region anchor")


# ===========================================================================
# 6. POSITIVE CONTROL (soundness) — structurally different but CORRECT.
#    Hoists each guard condition into a typed boolean local before branching,
#    keeping the SAME forward loop, the SAME guard order (acceptability before
#    duplicate), and EVERY gold framing assert + loop invariant verbatim. This
#    is a genuine structural reshape (not a guard reorder, which would need an
#    "everything in seen is acceptable" lemma the verifier won't auto-discharge,
#    and not a loop-direction flip against the front-recursive fold). It MUST
#    verify; if it cannot, the postcondition is SPEC-TOO-STRONG.
# ===========================================================================
_pos_control = _swap(
    _BASE,
    _GUARD_UNEXPECTED + _GUARD_DUPLICATE,
    "        unacceptable = not acceptable(positional, keyword_only, catch_all, name)  # type: bool\n"
    "        if unacceptable:\n"
    "            return 1\n"
    "        duplicate = contains(seen, name)  # type: bool\n"
    "        if duplicate:\n"
    "            return 2\n")


# ===========================================================================
# 7. ADMISSIBILITY (precondition non-vacuous) — the gold impl unchanged.
#    The frozen impl already establishes both the value postcondition and the
#    1/2-permission frame postcondition under the stated Requires on an F2P-
#    shaped input. Shipping it verbatim confirms the precondition ADMITS a
#    normal binding run (else PRECOND-TOO-STRONG). Distinct from the positive
#    control, which proves a *different* shape also verifies.
# ===========================================================================
_admiss = _BASE


SPEC_TESTS = [
    {"id": "frame-mutation-append", "kind": "uniqueness", "expect": "reject",
     "module": _frame_mut,
     "refinement": "Writing to `supplied` (a read-only Acc(list_pred,1/2) input "
                   "modelling the immutable supplied-keyword run / `bits`) has no "
                   "faithful real counterpart: parse_bits never mutates the token "
                   "run while deciding the keyword outcome. A patch that did would "
                   "inject a phantom keyword and corrupt the binding, failing the "
                   "F2P/P2P custom-tag assertions.",
     "rationale": "rejected by the PERMISSION SYSTEM: append needs full list_pred "
                  "but only Acc(list_pred(supplied),1/2) is held. The #1 weakness "
                  "class; a byte-fuzzer never mutates the input."},

    {"id": "prepatch-default-unexpected", "kind": "uniqueness", "expect": "reject",
     "module": _prepatch_default,
     "refinement": "This is exactly model_prepatch.py's reverted decision (the "
                   "pre-patch `param not in unhandled_kwargs` condition). Its "
                   "faithful real patch raises 'unexpected keyword argument' for "
                   "`{% simple_keyword_only_default kwarg=37 %}`, so it FAILS the "
                   "F2P test_simple_tags / test_inclusion_tags expectations "
                   "(result 37, not an error). It does not resolve.",
     "rationale": "rejected by the postcondition Result()==outcome(...): outcome "
                  "tests membership in the FULL keyword_only set "
                  "(acceptable = catch_all or in positional or in keyword_only), "
                  "default-independent. Witness supplied=[1], keyword_only=[1], "
                  "keyword_only_with_default=[1]: outcome=0, rival=1."},

    {"id": "duplicate-as-unexpected", "kind": "uniqueness", "expect": "reject",
     "module": _dup_as_unexpected,
     "refinement": "Returns UNEXPECTED (1) for a repeated acceptable keyword. A "
                   "faithful real patch raises the 'unexpected keyword argument' "
                   "message instead of 'received multiple values for keyword "
                   "argument', failing the F2P test_simple_tag_errors / "
                   "test_inclusion_tag_errors message assertions for "
                   "`kwarg=42 kwarg=37`.",
     "rationale": "rejected by the postcondition: outcome returns 2 (DUPLICATE) "
                  "when contains(seen,name); the spec pins DUPLICATE != UNEXPECTED. "
                  "Witness supplied=[1,1], keyword_only=[1]: outcome=2, rival=1."},

    {"id": "ignore-catch-all", "kind": "uniqueness", "expect": "reject",
     "module": _ignore_catchall,
     "refinement": "Drops the catch_all disjunct from acceptability, so a tag "
                   "with **kwargs that legitimately accepts an extra keyword is "
                   "wrongly rejected. A faithful real patch raises on such a tag, "
                   "breaking the `simple_unlimited_args_kwargs` PASS_TO_PASS "
                   "family that relies on a catch-all accepting arbitrary "
                   "keywords.",
     "rationale": "rejected by the postcondition: acceptable = catch_all or ... ; "
                  "the catch_all disjunct is load-bearing. Witness supplied=[9], "
                  "positional=[], keyword_only=[], catch_all=True: outcome=0, "
                  "rival=1."},

    {"id": "always-ok-supporting", "kind": "uniqueness", "expect": "reject",
     "module": _always_ok,
     "refinement": "Never raises (always OK). A real patch that never raised "
                   "would accept every malformed tag invocation, failing every "
                   "error F2P (test_simple_tag_errors / test_inclusion_tag_errors) "
                   "and the UNEXPECTED assertions. Cheap supporting near-miss.",
     "rationale": "rejected by the postcondition: outcome=1 on an unknown keyword "
                  "with no catch-all (supplied=[9], catch_all=False), but the "
                  "rival returns 0."},

    {"id": "diverge-before-answer", "kind": "uniqueness", "expect": "reject",
     "module": _diverge,
     "refinement": "Never answers: the loop spins without advancing, so every "
                   "value postcondition holds only vacuously. Its faithful real "
                   "patch inserts an endless loop into parse_bits' keyword scan; "
                   "compiling any custom tag with a kwarg hangs, so every "
                   "F2P/P2P custom-tag test times out. It does not resolve. This "
                   "is the audit's P1 attack class (same-spec impl the old, "
                   "MustTerminate-free spec admitted).",
     "rationale": "rejected by the termination obligation: Requires("
                  "MustTerminate(2)) must be discharged by a strictly "
                  "decreasing loop measure; with `i` frozen the measure "
                  "len(supplied)-i+1 does not decrease -> 'Loop might not keep "
                  "promise to terminate'."},

    {"id": "pos-control-hoisted-guards", "kind": "soundness", "expect": "verify",
     "module": _pos_control,
     "rationale": "a structurally-different but CORRECT impl (each guard "
                  "condition hoisted into a typed boolean local; same loop, same "
                  "guard order, every gold framing assert + loop invariant kept "
                  "verbatim) MUST verify, else SPEC-TOO-STRONG."},

    {"id": "admiss-gold-baseline", "kind": "admissibility", "expect": "verify",
     "module": _admiss,
     "rationale": "the frozen gold impl establishes the value postcondition AND "
                  "the 1/2-permission frame postcondition under the stated "
                  "Requires on an F2P-shaped binding run, so the precondition "
                  "ADMITS a normal input (else PRECOND-TOO-STRONG)."},
]


# No @ContractOnly axioms and no A-reference library callee in this bundle: the
# keyword-binding decision is membership/duplication logic over the binder's own
# inputs, modelled deeply by the `outcome` fold (meta.json axioms=[]; the
# `outcome` deep model is validated == the real fixed parse_bits branch by
# axiom_check.py / G-AX, which is a fidelity check, not a consumed axiom). The
# Nagini proof depends on NO axiom, so the axiom lane is vacuous here.
AXIOM_TESTS = []
