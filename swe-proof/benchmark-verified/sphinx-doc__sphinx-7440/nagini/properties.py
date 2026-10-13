# properties.py — PBT falsification battery for sphinx-doc__sphinx-7440.
#
# NOT a Nagini module; a record of adversarial cases the runner
# (swebench_nagini.pbt) executes and stamps with RESULT. Spec cases are full
# model.py variants that SHARE the frozen spec exactly (same_spec) and edit ONLY
# the impl region (between `# impl-start` / `# impl-end`, which nests the loop
# invariants); each is checked by Nagini verify. Axiom cases are real-callee
# probes — but this bundle consumes NO axiom (meta.axioms == []), so AXIOM_TESTS
# is empty (see assessment).
#
# The defended surface (model.py register_term_name):
#   * Input `termtext: List[int]` is READ-ONLY — Requires/Ensures Acc(..,1/2).
#     => FRAME-MUTATION probe is MANDATORY (the project's #1 weakness class).
#   * The load-bearing postcondition pins the output VERBATIM to the input:
#       Ensures(ToSeq(Result()) == ToSeq(termtext))         # whole-sequence
#       Ensures(len(Result()) == len(termtext))             # length
#       Ensures(Forall k: 0<=k<len => Result()[k]==termtext[k])  # element-wise
#     The "key" is the term text ITSELF (case-preserving identity copy). The gold
#     fix removed a `termtext.lower()` case-fold; the F2P test (`test_glossary`)
#     feeds an upper-case term `TERM2` and asserts the stored key is `TERM2`
#     (not `term2`). So any rival that folds/rewrites even one upper-case ASCII
#     letter, or drops/duplicates a position, would store a wrong key and FAIL
#     test_glossary => verify must reject it.
#   * The postcondition's oracle is GROUNDED in the argument (`termtext`), fully
#     unfolded — it is not an opaque @Pure answer-key. `casefold`/`fold_cp` exist
#     only as the CONTRAST deep model and are NOT referenced by the postcondition,
#     so there is no wrong value an impl could echo. UNGROUNDED-ORACLE-ECHO is
#     therefore N/A; we substitute an honest cheapest-impl positive control.
from pathlib import Path

INSTANCE = "sphinx-doc__sphinx-7440"
FLOAT_ENCODING = None  # meta.json float_encoding is null

_BASE = (Path(__file__).parent / "model.py").read_text()


def _swap(src, old, new):
    if old not in src:
        raise AssertionError("drift: %r" % (old,))
    if src.count(old) != 1:
        raise AssertionError("not unique: %r" % (old,))
    return src.replace(old, new, 1)


# The exact gold impl-region body (between the markers; includes the nested
# invariants block). All swaps edit ONLY text inside this block, so same_spec
# holds for every variant.
_GOLD_IMPL = """    # Build the registration key character by character, copying each code point
    # of the term text unchanged. The loop invariant tracks that the prefix
    # emitted equals the prefix of the term text verbatim.
    result = []  # type: List[int]
    i = 0
    while i < len(termtext):
        # invariants-start
        Invariant(Acc(list_pred(termtext), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(termtext))
        Invariant(ToSeq(result) == ToSeq(termtext).take(i))
        Invariant(MustTerminate(len(termtext) - i + 1))
        # invariants-end
        c = termtext[i]
        Assert(ToSeq(termtext).take(i + 1) == ToSeq(termtext).take(i) + PSeq(c))
        result = result + [c]
        i = i + 1
    Assert(ToSeq(termtext).take(len(termtext)) == ToSeq(termtext))
    return result"""

assert _GOLD_IMPL in _BASE, "gold impl block drifted from model.py"


# ---------------------------------------------------------------------------
# 1) POSITIVE CONTROL (soundness). Structurally-different but CORRECT impl:
#    same forward copy, but the per-step body is reshaped — the appended code
#    point is read into a fresh local `cp`, the framing assert is rephrased with
#    an explicit `prev`/`next` prefix-length witness, and the prefix invariant
#    is expressed via `take(i)` exactly as gold (kept verbatim so the proof
#    obligation is preserved — directive AVOID-2/3). It MUST verify; if a
#    faithful correct copy can't verify => SPEC-TOO-STRONG.
# ---------------------------------------------------------------------------
_POS = """    # Forward copy with reshaped locals: read the code point into `cp`, append,
    # advance. Same verbatim-prefix invariant as gold (kept so the loop-invariant
    # proof obligation is preserved); only the executable surface is reshaped.
    result = []  # type: List[int]
    i = 0
    while i < len(termtext):
        # invariants-start
        Invariant(Acc(list_pred(termtext), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(termtext))
        Invariant(ToSeq(result) == ToSeq(termtext).take(i))
        Invariant(MustTerminate(len(termtext) - i + 1))
        # invariants-end
        cp = termtext[i]
        Assert(ToSeq(termtext).take(i + 1) == ToSeq(termtext).take(i) + PSeq(cp))
        appended = [cp]  # type: List[int]
        result = result + appended
        i = i + 1
    Assert(ToSeq(termtext).take(len(termtext)) == ToSeq(termtext))
    return result"""
pos_control = _swap(_BASE, _GOLD_IMPL, _POS)


# ---------------------------------------------------------------------------
# 2) ADMISSIBILITY. A self-call caller proves the Requires admits a normal
#    F2P-shaped input: build a concrete term-text list `[84,69,82,77,50]`
#    ("TERM2", the exact F2P upper-case term), hand its half-permission to
#    register_term_name, and assert the returned key equals it verbatim — the
#    precondition must accept this legitimate input. If the Requires cannot be
#    established for an F2P input => PRECOND-TOO-STRONG. (Still a same_spec edit:
#    we only add executable code inside the impl region, after the verbatim
#    copy, calling the function on a fresh list — the contract is untouched.)
#    NOTE: building the demo list and the self-call all live INSIDE impl.
# ---------------------------------------------------------------------------
_ADMISS = """    # Build the registration key verbatim (gold body), then exercise
    # admissibility: construct the exact F2P upper-case term "TERM2" as code
    # points and confirm register_term_name accepts it (Requires holds for a
    # normal input) and returns it unchanged.
    result = []  # type: List[int]
    i = 0
    while i < len(termtext):
        # invariants-start
        Invariant(Acc(list_pred(termtext), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(termtext))
        Invariant(ToSeq(result) == ToSeq(termtext).take(i))
        Invariant(MustTerminate(len(termtext) - i + 1))
        # invariants-end
        c = termtext[i]
        Assert(ToSeq(termtext).take(i + 1) == ToSeq(termtext).take(i) + PSeq(c))
        result = result + [c]
        i = i + 1
    Assert(ToSeq(termtext).take(len(termtext)) == ToSeq(termtext))
    return result


def _admiss_caller() -> None:
    # "TERM2" as Unicode code points: T=84 E=69 R=82 M=77 2=50.
    demo = [84, 69, 82, 77, 50]  # type: List[int]
    key = register_term_name(demo)
    # The precondition admitted a normal F2P input and the key is verbatim.
    Assert(ToSeq(key) == ToSeq(demo))
    Assert(key[0] == 84)"""
admiss = _swap(_BASE, _GOLD_IMPL, _ADMISS)


# ---------------------------------------------------------------------------
# 3) FRAME-MUTATION (MANDATORY: input is read-only Acc(..,1/2)). Rival that
#    WRITES to the read-only `termtext` to try to satisfy the postcondition
#    vacuously. It mutates termtext[0] then copies; with only 1/2 permission the
#    write `termtext[0] = ...` is illegal => must REJECT for INSUFFICIENT
#    PERMISSION (not a value mismatch). Gold invariants/asserts kept verbatim so
#    the rejection is attributable to the write, not a proof gap.
#    refinement: a faithful real patch that mutates `term.astext()`'s backing
#    text in place would corrupt the source term node (or be impossible — astext
#    returns a fresh string), so it would not be the gold one-line `.lower()`
#    removal and would not resolve test_glossary cleanly.
# ---------------------------------------------------------------------------
_FRAME = """    # FRAME-MUTATION rival: attempt to write to the read-only input before
    # copying. With only Acc(list_pred(termtext), 1/2) this write is illegal.
    if len(termtext) > 0:
        termtext[0] = termtext[0]
    result = []  # type: List[int]
    i = 0
    while i < len(termtext):
        # invariants-start
        Invariant(Acc(list_pred(termtext), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(termtext))
        Invariant(ToSeq(result) == ToSeq(termtext).take(i))
        Invariant(MustTerminate(len(termtext) - i + 1))
        # invariants-end
        c = termtext[i]
        Assert(ToSeq(termtext).take(i + 1) == ToSeq(termtext).take(i) + PSeq(c))
        result = result + [c]
        i = i + 1
    Assert(ToSeq(termtext).take(len(termtext)) == ToSeq(termtext))
    return result"""
frame_mutation = _swap(_BASE, _GOLD_IMPL, _FRAME)


# ---------------------------------------------------------------------------
# 4) PARTIAL-DOMAIN — case-fold the FIRST character only, copy the rest. This is
#    correct on every all-lowercase / non-letter-first term (term1, term3,
#    term4, mysql) but WRONG on an upper-case-first term. The F2P term `TERM2`
#    (T=84) folds to t=116 at position 0, so the stored key would be `tERM2` !=
#    `TERM2` => test_glossary FAILS. Must REJECT: the postcondition
#    Result()[0]==termtext[0] (and the whole-sequence eq) is violated on the
#    upper-case-first sub-domain the F2P exercises.
#    refinement: the faithful real patch (lower-case only the first char of the
#    note_object key) would store "tERM2", so get_objects re-emits "tERM2" and
#    the F2P assertion ("TERM2","TERM2",...) fails — does NOT resolve.
# ---------------------------------------------------------------------------
_PARTIAL_FIRST = """    # PARTIAL-DOMAIN rival: case-fold the FIRST code point (ASCII A-Z -> +32),
    # copy every other position verbatim. Correct on lowercase-first terms,
    # wrong on the upper-case-first F2P term "TERM2".
    result = []  # type: List[int]
    i = 0
    while i < len(termtext):
        # invariants-start
        Invariant(Acc(list_pred(termtext), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(termtext))
        Invariant(len(result) == i)
        # invariants-end
        c = termtext[i]
        if i == 0 and 65 <= c and c <= 90:
            result = result + [c + 32]
        else:
            result = result + [c]
        i = i + 1
    return result"""
partial_first = _swap(_BASE, _GOLD_IMPL, _PARTIAL_FIRST)


# ---------------------------------------------------------------------------
# 5) PARTIAL-DOMAIN (whole-string fold) — the PRE-PATCH behaviour: ASCII
#    case-fold EVERY character. Equal to gold on all-lowercase terms (term1,
#    term3, term4) but folds "TERM2"->"term2". This is exactly the bug the gold
#    patch removed; it must REJECT on the verbatim postcondition. (Strong
#    supporting case — it is the differential witness G-DIFF already uses, recast
#    as a uniqueness probe.) Uses a forward loop with the casefold invariant.
#    refinement: this IS the pre-patch `termtext.lower()`; it stores "term2" and
#    test_glossary asserts "TERM2" => does NOT resolve (that is the original bug).
# ---------------------------------------------------------------------------
_PARTIAL_ALL = """    # PARTIAL-DOMAIN rival = the pre-patch case fold: lower-case every ASCII
    # A-Z code point. Agrees with gold on all-lowercase terms, folds "TERM2".
    result = []  # type: List[int]
    i = 0
    while i < len(termtext):
        # invariants-start
        Invariant(Acc(list_pred(termtext), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(termtext))
        Invariant(len(result) == i)
        # invariants-end
        c = termtext[i]
        if 65 <= c and c <= 90:
            result = result + [c + 32]
        else:
            result = result + [c]
        i = i + 1
    return result"""
partial_all = _swap(_BASE, _GOLD_IMPL, _PARTIAL_ALL)


# ---------------------------------------------------------------------------
# 6) PARTIAL-DOMAIN (drop the LAST element) — copy positions 0..len-2, omit the
#    final code point. Correct on length-0 terms only; wrong on every non-empty
#    term (off-by-one). Violates len(Result())==len(termtext). Must REJECT.
#    refinement: a real patch that truncates the last char of the key stores
#    "TERM" instead of "TERM2", and get_objects re-emits "TERM" => the F2P
#    assertion fails => does NOT resolve.
# ---------------------------------------------------------------------------
_DROP_LAST = """    # PARTIAL-DOMAIN rival: copy all but the LAST code point (off-by-one).
    result = []  # type: List[int]
    i = 0
    bound = len(termtext) - 1
    while i < bound:
        # invariants-start
        Invariant(Acc(list_pred(termtext), 1 / 2))
        Invariant(Acc(list_pred(result)))
        Invariant(0 <= i and i <= len(termtext))
        Invariant(len(result) == i)
        # invariants-end
        c = termtext[i]
        result = result + [c]
        i = i + 1
    return result"""
drop_last = _swap(_BASE, _GOLD_IMPL, _DROP_LAST)


SPEC_TESTS = [
    {
        "id": "pos-control-reshaped-copy",
        "kind": "soundness",
        "expect": "verify",
        "module": pos_control,
        "rationale": "a structurally-reshaped but correct verbatim copy (fresh "
                     "local `cp`, `appended` list) keeps the gold take(i) prefix "
                     "invariant and per-step framing assert, so it must verify; "
                     "if it cannot => SPEC-TOO-STRONG.",
    },
    {
        "id": "admissibility-F2P-TERM2",
        "kind": "admissibility",
        "expect": "verify",
        "module": admiss,
        "rationale": "a caller builds the exact F2P upper-case term 'TERM2' "
                     "([84,69,82,77,50]) and calls register_term_name on it; the "
                     "Requires(Acc(..,1/2)) must admit this normal input and the "
                     "returned key is verbatim. If the precondition rejects it "
                     "=> PRECOND-TOO-STRONG.",
    },
    {
        "id": "frame-mutation-write-input",
        "kind": "uniqueness",
        "expect": "reject",
        "module": frame_mutation,
        "refinement": "writing to the read-only term text in place has no faithful "
                      "real counterpart: term.astext() yields a fresh string and "
                      "the gold fix is the one-line removal of `.lower()`, never an "
                      "in-place mutation of the source term node; such a patch would "
                      "not be the gold edit and would not resolve test_glossary.",
        "rationale": "REJECT comes from the permission system: `termtext[0] = ...` "
                     "needs full Acc(list_pred(termtext)) but only Acc(..,1/2) is "
                     "held (Requires AND Ensures), so the write is insufficient-"
                     "permission. Gold invariants/asserts kept verbatim so the "
                     "rejection is attributable to the write, not a proof gap.",
    },
    {
        "id": "partial-fold-first-char",
        "kind": "uniqueness",
        "expect": "reject",
        "module": partial_first,
        "refinement": "folding only the first character stores 'tERM2' for the F2P "
                      "term 'TERM2'; get_objects re-emits 'tERM2', so the F2P "
                      "assertion (\"TERM2\",\"TERM2\",...) fails => does NOT resolve. "
                      "It is correct on every lowercase-first term (term1/3/4, "
                      "mysql) so a value abstraction that only sampled those would "
                      "miss it.",
        "rationale": "REJECT comes from postcondition Result()[0]==termtext[0] and "
                     "ToSeq(Result())==ToSeq(termtext): position 0 of an upper-case-"
                     "first term diverges (84->116), violating the element-wise pin.",
    },
    {
        "id": "partial-fold-all-prepatch",
        "kind": "uniqueness",
        "expect": "reject",
        "module": partial_all,
        "refinement": "this is exactly the pre-patch `termtext.lower()` the gold "
                      "patch removed: it stores 'term2' for 'TERM2', so "
                      "test_glossary's ('TERM2',...) assertion fails => does NOT "
                      "resolve (the original bug). Agrees with gold on all-lowercase "
                      "terms.",
        "rationale": "REJECT comes from the verbatim postcondition "
                     "ToSeq(Result())==ToSeq(termtext): any upper-case ASCII letter "
                     "is shifted +32, so Result() differs from termtext. This is the "
                     "G-DIFF differential witness recast as a uniqueness probe.",
    },
    {
        "id": "partial-drop-last",
        "kind": "uniqueness",
        "expect": "reject",
        "module": drop_last,
        "refinement": "omitting the final code point stores 'TERM' instead of "
                      "'TERM2'; get_objects re-emits 'TERM' so the F2P assertion "
                      "fails => does NOT resolve. Correct only on the empty term.",
        "rationale": "REJECT comes from postcondition len(Result())==len(termtext): "
                     "the result is one shorter than the input on every non-empty "
                     "term (and ToSeq equality also fails).",
    },
]

# No @ContractOnly axioms are consumed (meta.json axioms == []). The single
# kind-A obligation is the A-reference deep model `casefold == ASCII str.lower`,
# already validated out-of-band by axiom_check.py (G-AX) over the full 128-point
# ASCII domain + 20000 fuzz inputs. `casefold` is NOT referenced by any
# postcondition the spec discharges, so there is no caller-reachable callee input
# to contain and no axiom Ensures for a real callee to violate within THIS
# bundle's proof. Hence the axiom lane is vacuous here.
AXIOM_TESTS = []
